#!/usr/bin/env python3
"""Cuanto corpus deja publico la compuerta de Custos Legis. Solo stdlib.

--------------------------------------------------------------------------------
POR QUE ESTE INSTRUMENTO EXISTE
--------------------------------------------------------------------------------
La compuerta (`anonimizador.py`) reparte por NATURALEZA: normativo publico,
jurisprudencial retenido. Su docstring afirmaba que eso "conserva el valor del
corpus (las normas, que son la MAYORIA y las que se citan)".

**Esa afirmacion era MIA y no la habia medido.** Este instrumento la mide contra
la composicion real del corpus, y da el numero que decide si el diseno es
aceptable o si hay que rehacerlo. **Resultado: refutada.**

--------------------------------------------------------------------------------
DOS MODOS, y el offline no es un consuelo
--------------------------------------------------------------------------------
  --vivo    consulta /estado del corpus. Requiere que el acceso este ABIERTO.
  (default) usa el SNAPSHOT commiteado abajo, con su procedencia y fecha.

El acceso publico esta CERRADO desde el 2026-09-10 06:29 UTC por orden de
Abraham (ver `corpus-legal-tarija/CIERRE-PUBLICO-2026-09-10.md`), y el cierre se
verifico a las 06:31 con `falsador_cierre_publico.py`: 12 rutas, 12 veces 503,
con control positivo por SSH de que la VM seguia viva.

PRECISION SOBRE ESE 503, porque la categoria importa: el 503 lo midio el
falsador desde un lugar CON RED. Desde el taller donde se escribio este archivo
NO HAY RED, asi que aca `--vivo` falla con `Temporary failure in name
resolution`, que es un error del TALLER y no del corpus. Son dos cosas
distintas y confundirlas seria declarar "esta cerrado" cuando lo unico medido es
"no llegue". El modo vivo queda para el dia que se reabra, corrido desde un lugar
con red, y sirve para detectar que el snapshot quedo viejo.

--------------------------------------------------------------------------------
QUE ES NO MEDIDO, declarado
--------------------------------------------------------------------------------
  1. EL REPARTO POR PASAJE. El corpus declara 78.930 pasajes y NO publica su
     desglose por fuente. Todo lo de aca es POR DOCUMENTO. Un Auto Supremo es
     mucho mas largo que una resolucion de la Asamblea, asi que por pasaje el
     porcentaje retenido es probablemente PEOR, no mejor. No lo afirmo: no lo
     tengo.
  2. Que la compuerta clasifique bien esos 6.079 en la practica. Aca se asume
     que fuente == clase (GENESIS es jurisprudencia, Gaceta y LexiVox son
     normativa). Es una asuncion razonable y NO verificada documento por
     documento. Es tambien el PUNTO UNICO DE FALLA de todo el diseno: si el
     mapeo dijera que GENESIS es normativo, los 5.030 Autos Supremos saldrian
     publicos con nombres de partes. Hay un contra-test que lo demuestra.
  3. Cuantos de los 5.030 Autos Supremos caen en RESERVA_LEGAL (NNA, violencia)
     y por lo tanto no se publican ni con matricula. `q=Violacion de Nino, Nina
     o Adolescente` daba 484 pasajes, pero pasajes no son documentos.
"""
from __future__ import annotations

import json
import sys
import urllib.request

BASE = "https://150448fcc6.abacusai.cloud"

# ---------------------------------------------------------------------------
# SNAPSHOT COMMITEADO. Cada numero con su procedencia, porque un numero sin
# fuente es el dato que despues nadie puede verificar.
# ---------------------------------------------------------------------------
SNAPSHOT = {
    "fecha": "2026-09-09T17:58Z",
    "procedencia": "corpus-legal-tarija/REPORTE-PARA-FABLE-2026-09-09.md, "
                   "seccion 1, tomado de /estado en vivo",
    "documentos": 6079,
    "pasajes": 78930,
    "fuentes": {
        "GENESIS": 5030,
        "Gaceta Tarija": 1034,
        "LexiVox": 15,
    },
}

# Mapeo fuente -> clase de la compuerta. ASUNCION declarada, no medida doc a doc.
CLASE_DE_FUENTE = {
    "GENESIS": "jurisprudencial",       # Autos Supremos del TSJ: tienen partes
    "Gaceta Tarija": "normativo",       # normativa departamental: sin partes
    "LexiVox": "normativo",             # normativa nacional: sin partes
}


def leer_vivo(timeout: int = 20) -> dict:
    """Consulta /estado. Devuelve el dict o levanta con el motivo real."""
    req = urllib.request.Request(
        BASE + "/estado",
        headers={"User-Agent": "impacto-compuerta/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def repartir(fuentes: dict[str, int]) -> dict:
    """Cuenta documentos por clase de la compuerta.

    Una fuente que NO esta en el mapeo cae en `sin_clasificar`, y la compuerta
    la RETIENE. Fail-closed hasta en el contador: si manana entra una fuente
    nueva del TCP, no se publica sola por omision.
    """
    por_clase: dict[str, int] = {"normativo": 0, "jurisprudencial": 0,
                                 "sin_clasificar": 0}
    desconocidas = []
    for nombre, n in fuentes.items():
        clase = CLASE_DE_FUENTE.get(nombre)
        if clase is None:
            por_clase["sin_clasificar"] += n
            desconocidas.append(nombre)
        else:
            por_clase[clase] += n
    total = sum(por_clase.values())
    return {"por_clase": por_clase, "total": total, "desconocidas": desconocidas}


def informe(fuentes: dict[str, int], etiqueta: str) -> float:
    """Imprime el reparto. Devuelve el % publicable."""
    r = repartir(fuentes)
    total = r["total"]
    pub = r["por_clase"]["normativo"]
    ret = r["por_clase"]["jurisprudencial"]
    sinc = r["por_clase"]["sin_clasificar"]

    print(f"\n=== IMPACTO DE LA COMPUERTA · {etiqueta} ===")
    print(f"  total de documentos: {total}")
    print(f"  PUBLICO   (normativo, sin partes por naturaleza): "
          f"{pub:5d}  {pub/total*100:5.1f}%")
    print(f"  RETENIDO  (jurisprudencial, con partes):          "
          f"{ret:5d}  {ret/total*100:5.1f}%")
    if sinc:
        print(f"  SIN CLASIFICAR (fuente nueva, la compuerta RETIENE):  "
              f"{sinc:5d}  {sinc/total*100:5.1f}%")
        print(f"    fuentes no mapeadas: {', '.join(r['desconocidas'])}")
    return round(pub / total * 100, 1)


def main() -> int:
    vivo = "--vivo" in sys.argv
    fuentes = None
    etiqueta = ""

    if vivo:
        try:
            est = leer_vivo()
            fuentes = est.get("fuentes") or {}
            etiqueta = "MEDIDO EN VIVO"
            print("acceso ABIERTO: /estado respondio")
        except Exception as e:
            print(f"/estado NO respondio: {type(e).__name__}: {e}")
            print("OJO con la categoria del error: si dice 'name resolution' es")
            print("que NO HAY RED donde corrio esto, y eso NO prueba nada sobre")
            print("el corpus. Si da 503, ese si es el cierre funcionando.")
            print("Cayendo al snapshot commiteado.")
    if not fuentes:
        fuentes = dict(SNAPSHOT["fuentes"])
        etiqueta = f"SNAPSHOT {SNAPSHOT['fecha']}"

    pct = informe(fuentes, etiqueta)

    print(f"\n  procedencia del snapshot: {SNAPSHOT['procedencia']}")
    print("\n=== LA AFIRMACION QUE VINE A MEDIR ===")
    print('  docstring de anonimizador.py v1: "las normas, que son la MAYORIA"')
    print(f"  medido: las normas son el {pct}% de los documentos.")
    if pct > 50:
        print("  -> la afirmacion SE SOSTIENE")
    else:
        print("  -> **REFUTADA**. Son minoria, y por bastante.")
        print(f"     La compuerta cierra el {round(100 - pct, 1)}% del corpus.")
        print("     Eso NO invalida la compuerta: invalida el argumento con que")
        print("     la justifique. La via de la matricula no es la excepcion,")
        print("     es el camino principal para 5 de cada 6 documentos.")

    print("\n=== NO MEDIDO ===")
    print(f"  reparto por PASAJE: el corpus declara {SNAPSHOT['pasajes']} pasajes")
    print("  y no publica su desglose por fuente. Un Auto Supremo es mas largo")
    print("  que una resolucion, asi que por pasaje el % retenido es")
    print("  probablemente PEOR. No lo afirmo: no lo tengo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
