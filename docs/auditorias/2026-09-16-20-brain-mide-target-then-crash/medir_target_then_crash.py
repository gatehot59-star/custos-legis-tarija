"""Mide el falso positivo NUEVO que reporto Sol contra MAIN: target-then-crash.

SU HALLAZGO: la suite emite la etiqueta objetivo y DESPUES revienta con una
excepcion. Una excepcion Python sale con codigo 1 y no imprime otra linea ROJO,
asi que mis DOS guards la dejan pasar:

  - exit 1 exacto       -> si, una excepcion da exactamente 1
  - exactamente un rojo -> si, el crash no suma rojos

O sea que el sabotaje se declara exitoso aunque la suite MURIO a mitad de camino
y los checks posteriores nunca corrieron. Entre ellos el CONTROL POSITIVO ("con
el caso correcto sigue autorizando"), que es justo el que garantiza que el
sabotaje no rompio el camino legitimo. Un falsador que acepta una corrida
incompleta no prueba que el defecto vuelva a ser detectado: prueba que la suite
llego hasta la primera asercion.

QUE MIDE, con el bloque REAL del workflow extraido de main:

  A. solo el objetivo                  -> tiene que ACEPTAR (control positivo)
  B. objetivo y DESPUES un crash       -> DEBERIA RECHAZAR. Si acepta, HUECO.
  C. objetivo y DESPUES exit 0         -> deberia RECHAZAR (retorno incoherente)
  D. crash SIN el objetivo             -> tiene que RECHAZAR (ya cubierto)

El escenario A existe para que un "todo rechaza" no se lea como exito: si el paso
rechazara TODO, B/C/D pasarian y el instrumento no mediria nada.

Los codigos de salida se leen con subprocess.returncode. El `$?` del shell de mi
gateway devuelve 0 SIEMPRE (control medido: `bash -c 'exit 7'` reportaba 0), asi
que no se usa como testigo.

Uso: python3 medir_target_then_crash.py [ruta-al-clon-de-main]
"""
from __future__ import annotations

import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/workspace/mainv")
WF = ROOT / ".github/workflows/api-e2e.yml"
EXPECTED = "CASO una accion SIN caso NO hereda la aprobacion del caso 1"


def read_step() -> str:
    """Extrae el bloque FALSADOR 2 real. Si el formato derivo, falla cerrado."""
    text = WF.read_text(encoding="utf-8")
    sec = re.split(r"^      - name: ", text, flags=re.MULTILINE)
    m = [s for s in sec if s.startswith("FALSADOR 2 - ")]
    assert len(m) == 1, f"esperaba un solo FALSADOR 2, hay {len(m)}"
    marker = "        run: |\n"
    assert m[0].count(marker) == 1, "el bloque run no es unico"
    body = textwrap.dedent(m[0].split(marker, 1)[1]).rstrip() + "\n"
    assert "${{" not in body, "expresion de GitHub no ejecutable"
    return body


def inject(original: str, statement: str) -> str:
    """Conserva imports y helpers reales; reemplaza solo el main guard final."""
    tree = ast.parse(original)
    last = tree.body[-1]
    assert isinstance(last, ast.If), "la suite tiene que terminar en su main guard"
    assert EXPECTED in original, "falta la etiqueta objetivo en la suite"
    return "\n".join(original.splitlines()[: last.lineno - 1]) + "\n" + statement


def correr(nombre: str, statement: str, espera_aceptar: bool) -> bool:
    step = read_step()
    with tempfile.TemporaryDirectory(prefix="brain-target-crash-") as tmp:
        f = Path(tmp)
        back = f / "backend"
        back.mkdir()
        for s in (ROOT / "backend").glob("*.py"):
            shutil.copyfile(s, back / s.name)
        suite = back / "test_regresiones_hitl.py"
        suite.write_text(inject(suite.read_text(encoding="utf-8"), statement),
                         encoding="utf-8")
        antes = (back / "api.py").read_bytes()
        step = step.replace("/tmp/api.py.bak2", str(f / "api.bak2"))
        step = step.replace("/tmp/f2.log", str(f / "f2.log"))
        sh = f / "step.sh"
        sh.write_text(step, encoding="utf-8")
        env = {k: v for k, v in os.environ.items()
               if k not in ("DATABASE_URL", "DATABASE_URL_APP", "PYTHONPATH",
                            "BASH_ENV", "ENV")}
        r = subprocess.run(["bash", "--noprofile", "--norc", "-e", "-o",
                            "pipefail", str(sh)], cwd=f, env=env,
                           capture_output=True, text=True, timeout=60)
        acepto = r.returncode == 0
        restaurado = (back / "api.py").read_bytes() == antes
    ok = acepto == espera_aceptar
    print(f"\n--- {nombre}")
    print(f"    exit del paso: {r.returncode}  (acepta={acepto}, "
          f"esperado acepta={espera_aceptar})  api.py restaurada={restaurado}")
    print(f"    {'OK' if ok else 'ROJO -> HUECO CONFIRMADO'}")
    for l in r.stdout.strip().splitlines()[-3:]:
        print("      |", l[:115])
    return ok


def main() -> int:
    control = subprocess.run(["bash", "-c", "exit 7"]).returncode
    print(f"CONTROL DEL MEDIDOR: bash -c 'exit 7' -> {control} (debe ser 7)")
    if control != 7:
        print("NO MEDIDO: el transporte no propaga codigos de salida.")
        return 2
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                         capture_output=True, text=True).stdout.strip()
    print("arbol auditado:", sha or "(sin git)")

    res = [
        ("A solo el objetivo (control positivo)", correr(
            "A. solo el objetivo",
            f"ok({EXPECTED!r}, 200, 403)\nraise SystemExit(1)\n", True)),
        ("B objetivo + CRASH posterior (el hallazgo de Sol)", correr(
            "B. objetivo, despues crash",
            f"ok({EXPECTED!r}, 200, 403)\n"
            "raise RuntimeError('la suite murio despues del check objetivo')\n",
            False)),
        ("C objetivo + exit 0 posterior (retorno incoherente)", correr(
            "C. objetivo, despues exit 0",
            f"ok({EXPECTED!r}, 200, 403)\nraise SystemExit(0)\n", False)),
        ("D crash SIN el objetivo", correr(
            "D. crash sin objetivo",
            "raise RuntimeError('crash ajeno')\n", False)),
    ]

    print("\n" + "=" * 62)
    for n, ok in res:
        print(("OK   " if ok else "HUECO") + "  " + n)
    huecos = [n for n, ok in res if not ok]
    print("\nVEREDICTO:", "el arbol aguanta los cuatro" if not huecos
          else f"HUECOS CONFIRMADOS: {huecos}")
    return 1 if huecos else 0


if __name__ == "__main__":
    raise SystemExit(main())
