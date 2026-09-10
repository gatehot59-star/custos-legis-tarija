#!/usr/bin/env python3
"""Cliente del corpus legal. Solo stdlib.

RESPETA EL ADR-001: el corpus es un PRODUCTO INDEPENDIENTE y se consume por su
contrato HTTP publico. No se lee su SQLite, no se copia su base, no se le pide
multi-tenancy. Si el corpus cambia su esquema interno, esto no se rompe.

--------------------------------------------------------------------------------
ARREGLA EL D2 DE FABLE, que es el defecto mas peligroso del diseno original:

  El diseno ponia `estado_vigencia="vigente"` HARDCODEADO en todo el catalogo, y
  el Agente Investigador filtraba por `estado_vigencia == "vigente"`.

  Con la medicion real del corpus (13 de 527 leyes con estado, 2,47 %) ese filtro
  tiene dos salidas y las dos son malas:
    a) si el filtro se respeta -> se descarta el 97,5 % del corpus
    b) si el campo se rellena con "vigente" por defecto -> el sistema DECLARA
       vigente lo que nadie midio, y un memorial cita una ley abrogada

  La (b) es peor y es la que el diseno elegia. Un memorial que cita una norma
  abrogada es un memorial perdido, y el abogado no lo va a notar.

LA SALIDA: tres estados, nunca dos. `VIGENTE`, `DEROGADA`, `NO_MEDIDO`. Y el
cliente devuelve una `advertencia` obligatoria cuando la vigencia no esta medida,
que la UI TIENE que mostrar. La ausencia de dato es un dato.
--------------------------------------------------------------------------------
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

BASE = "https://150448fcc6.abacusai.cloud"
UA = "custos-legis-tarija/0.1 (+github.com/gatehot59-star/custos-legis-tarija)"

# Limites que el propio corpus declara en /estado. Se respetan; no se fuerzan.
TOPE_OFFSET = 10_000
MUESTRA_FACETAS = 400


class CorpusError(RuntimeError):
    pass


def _get(ruta: str, params: dict | None = None, timeout: int = 30) -> Any:
    url = BASE + ruta
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                              "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status != 200:
                raise CorpusError(f"{ruta} devolvio {r.status}")
            return json.loads(r.read().decode("utf-8"))
    except CorpusError:
        raise
    except Exception as e:
        raise CorpusError(f"{ruta}: {type(e).__name__}: {e}") from e


def estado() -> dict:
    """Conteos y limites declarados del corpus."""
    return _get("/estado")


def cobertura_vigencia() -> dict:
    """Cuanta vigencia hay medida DE VERDAD, leida del corpus en vivo.

    Se consulta y NO se cachea a proposito: si el corpus mejora su vigencia, el
    agente tiene que enterarse sin redeploy. Y si empeora, tambien.

    Publica LOS DOS denominadores, que es el A7 de Fable: el corpus publica dos
    y citar uno solo es elegir el que conviene.
    """
    v = estado().get("vigencia", {})
    return {
        "medidas": v.get("con_estado_medido"),
        "universo_amplio": v.get("normas_con_vigencia_aplicable"),
        "universo_estricto": v.get("solo_leyes_y_nacionales"),
        "pct_amplio": v.get("cobertura_por_ciento"),
        "pct_estricto": v.get("cobertura_solo_leyes_por_ciento"),
        "nota": v.get("nota"),
    }


def _vigencia_de(r: dict) -> tuple[str, str | None]:
    """Los TRES estados. `None` NO significa vigente: significa no medido."""
    vig = r.get("vigente")
    der = r.get("derogada_por")
    if vig == 0 or vig is False:
        return "DEROGADA", der
    if vig == 1 or vig is True:
        return "VIGENTE", None
    return "NO_MEDIDO", der


def buscar(q: str, *, limit: int = 10, offset: int = 0,
           materia: str | None = None, tipo: str | None = None) -> dict:
    """Busqueda literal sobre el corpus.

    La busqueda del corpus es LEXICA (BM25/FTS5), no semantica: el propio
    /estado lo declara. Para "Art. 252 CPC" o "AS/0122/2026" eso es una VENTAJA,
    porque la similitud semantica traeria un fallo parecido en vez del que lleva
    ese numero. Para "casos como este" NO alcanza, y eso va declarado en
    `limites` para que el agente que lo consuma no concluya de mas.
    """
    if offset > TOPE_OFFSET:
        raise CorpusError(
            f"offset {offset} supera el tope declarado del corpus ({TOPE_OFFSET})")
    params: dict[str, Any] = {"q": q, "limit": limit, "offset": offset}
    if materia:
        params["materia"] = materia
    if tipo:
        params["tipo"] = tipo
    d = _get("/buscar", params)

    salida = []
    sin_medir = 0
    for r in d.get("resultados", []):
        est, der = _vigencia_de(r)
        if est == "NO_MEDIDO":
            sin_medir += 1
        salida.append({
            "uid": r.get("uid"),
            "nro": r.get("nro"),
            "pasaje": r.get("pasaje"),
            "tipo_norma": r.get("tipo_norma"),
            "numero": r.get("numero"),
            "anio": r.get("anio"),
            "fecha": r.get("fecha"),
            "materia": r.get("materia"),
            "organo": r.get("organo"),
            # La cadena de custodia viaja SIEMPRE con la cita. Sin esto un
            # memorial cita algo que nadie puede verificar.
            "fuente_url": r.get("fuente_url"),
            "sha256": r.get("sha256"),
            "via_texto": r.get("via_texto"),
            "confianza_texto": r.get("confianza"),
            # Los tres estados, explicitos
            "vigencia": est,
            "derogada_por": der,
            "advertencia": (
                None if est == "VIGENTE" else
                f"DEROGADA por {der}: NO citar como vigente" if est == "DEROGADA"
                else "VIGENCIA NO VERIFICADA: confirmar antes de citar"),
        })

    return {
        "consulta": d.get("consulta"),
        "total_pasajes": d.get("total_pasajes"),
        "ms": d.get("ms"),
        "resultados": salida,
        "facetas": d.get("facetas"),
        "limites": {
            "busqueda": "literal (BM25/FTS5): sin expansion semantica",
            "facetas": f"contadas sobre una muestra de {MUESTRA_FACETAS} pasajes",
            "offset_max": TOPE_OFFSET,
            "resultados_sin_vigencia_medida": sin_medir,
            "advertencia_global": (
                f"{sin_medir} de {len(salida)} resultados NO tienen vigencia"
                " verificada. El agente NO debe presentarlos como derecho"
                " vigente." if sin_medir else None),
        },
    }


def texto(uid: str, nro: int = 1) -> dict:
    """Texto continuo del documento, para leer el articulo completo."""
    return _get("/texto", {"uid": uid, "nro": nro})


def cita_formal(r: dict) -> str:
    """Cita lista para un memorial, CON su advertencia si corresponde.

    Regla heredada del corpus: la advertencia viaja DENTRO de la cita. Si la cita
    se copia a un escrito judicial, la advertencia se copia con ella.
    """
    partes = [p for p in (r.get("tipo_norma"), r.get("numero")) if p]
    base = " ".join(partes) or r.get("uid", "documento sin identificar")
    if r.get("fecha"):
        base += f" de {r['fecha']}"
    if r.get("organo"):
        base += f" ({r['organo']})"
    if r.get("vigencia") == "DEROGADA":
        base += f" [DEROGADA por {r.get('derogada_por')}]"
    elif r.get("vigencia") == "NO_MEDIDO":
        base += " [vigencia no verificada]"
    if r.get("fuente_url"):
        base += f" · {r['fuente_url']}"
    return base


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "asistencia familiar"
    d = buscar(q, limit=3)
    print(f"consulta: {d['consulta']!r}")
    print(f"total: {d['total_pasajes']} pasajes en {d['ms']} ms")
    print(f"limites: {json.dumps(d['limites'], ensure_ascii=False, indent=1)}")
    for r in d["resultados"]:
        print(f"\n  {cita_formal(r)}")
        print(f"    vigencia: {r['vigencia']}")
        if r["advertencia"]:
            print(f"    AVISO: {r['advertencia']}")
