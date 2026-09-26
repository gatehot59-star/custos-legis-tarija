#!/usr/bin/env python3
"""Retrieval completo sobre el contrato HTTP público del Corpus.

No abre SQLite ni inventa una base local. Repite GET /buscar con offset hasta
consumir todos los pasajes que la consulta devuelve, respetando el tope público
del Corpus y fallando cerrado si no puede demostrar completitud.
"""
from __future__ import annotations

import inspect
import json
import urllib.parse
import urllib.request
from typing import Any


CORPUS_OFFSET_MAX = 10_000
DEFAULT_PAGE_SIZE = 100


class CompleteRetrievalError(RuntimeError):
    """La recuperación completa no pudo probarse."""


def _page_from_http(corpus: Any, query: str, limit: int, offset: int) -> dict[str, Any]:
    """Consulta una página usando solo el contrato público del Corpus."""
    base = getattr(corpus, "base", None)
    if not isinstance(base, str) or not base:
        raise CompleteRetrievalError(
            "el proveedor no expone buscar(..., offset=...) ni una base HTTP "
            "para paginar el Corpus completo")
    url = base + "/buscar?" + urllib.parse.urlencode({
        "q": query, "limit": limit, "offset": offset,
    })
    request = urllib.request.Request(url, headers={
        "User-Agent": "custos-legis-tarija/0.1",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise CompleteRetrievalError(
                    f"/buscar devolvió HTTP {response.status} en offset {offset}")
            payload = json.loads(response.read().decode("utf-8"))
    except CompleteRetrievalError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise CompleteRetrievalError(
            f"no se pudo leer /buscar en offset {offset}: {type(exc).__name__}: {exc}") from exc
    if not isinstance(payload, dict):
        raise CompleteRetrievalError("/buscar no devolvió un objeto JSON")
    return payload


def fetch_page(corpus: Any, query: str, *, limit: int, offset: int) -> dict[str, Any]:
    """Obtiene una página con offset explícito, sin degradar a top-k silencioso."""
    buscar = getattr(corpus, "buscar", None)
    if not callable(buscar):
        return _page_from_http(corpus, query, limit, offset)
    try:
        parameters = inspect.signature(buscar).parameters
    except (TypeError, ValueError):
        parameters = {}
    if "offset" in parameters:
        page = buscar(query, limit=limit, offset=offset)
    elif offset == 0:
        # Una página inicial sirve para el camino BM25, pero no certifica
        # completitud. Para la segunda página se exige el contrato paginado.
        page = buscar(query, limit=limit)
    else:
        page = _page_from_http(corpus, query, limit, offset)
    if not isinstance(page, dict):
        raise CompleteRetrievalError("el proveedor devolvió una página no JSON")
    return page


def search_complete(corpus: Any, query: str, *, page_size: int = DEFAULT_PAGE_SIZE,
                    max_results: int = CORPUS_OFFSET_MAX) -> dict[str, Any]:
    """Recupera todas las páginas de una consulta del Corpus.

    `limit` de la investigación sigue siendo el tamaño de salida final; acá no
    se usa para recortar las semillas del grafo. El límite solo protege contra
    un endpoint que no respete el contrato y nunca se transforma en éxito.
    """
    if not query.strip():
        raise CompleteRetrievalError("la consulta no puede estar vacía")
    if page_size < 1 or page_size > CORPUS_OFFSET_MAX:
        raise CompleteRetrievalError("page_size fuera del límite del Corpus")
    if max_results < 1 or max_results > CORPUS_OFFSET_MAX:
        raise CompleteRetrievalError("max_results fuera del límite del Corpus")

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    offset = 0
    declared_total: int | None = None
    metadata: dict[str, Any] = {}

    while True:
        if offset > CORPUS_OFFSET_MAX:
            raise CompleteRetrievalError("el offset supera el tope público del Corpus")
        page = fetch_page(corpus, query, limit=page_size, offset=offset)
        raw_rows = page.get("resultados", [])
        if not isinstance(raw_rows, list):
            raise CompleteRetrievalError("/buscar.resultados no es una lista")
        if declared_total is None and page.get("total_pasajes") is not None:
            try:
                declared_total = int(page["total_pasajes"])
            except (TypeError, ValueError) as exc:
                raise CompleteRetrievalError("total_pasajes no es entero") from exc
            if declared_total > max_results:
                raise CompleteRetrievalError(
                    f"la consulta tiene {declared_total} pasajes y el límite seguro es "
                    f"{max_results}; completitud NO MEDIDA")
        metadata.update({k: v for k, v in page.items() if k != "resultados"})

        for index, raw in enumerate(raw_rows):
            if not isinstance(raw, dict):
                raise CompleteRetrievalError("/buscar contiene un resultado no objeto")
            uid = str(raw.get("uid") or "")
            key = (uid, offset + index) if not uid else (uid, -1)
            if key not in seen:
                seen.add(key)
                rows.append(raw)
        next_offset = offset + len(raw_rows)
        if len(rows) > max_results:
            raise CompleteRetrievalError(
                f"la consulta superó {max_results} resultados; completitud NO MEDIDA")
        if not raw_rows:
            break
        if declared_total is not None and next_offset >= declared_total:
            break
        if len(raw_rows) < page_size:
            # Una página corta es el único cierre válido si el servidor no
            # publica total_pasajes. No seguimos inventando offsets.
            break
        if next_offset <= offset:
            raise CompleteRetrievalError("el Corpus no avanzó el offset")
        offset = next_offset

    if declared_total is not None and len(rows) < declared_total:
        raise CompleteRetrievalError(
            f"se recuperaron {len(rows)} de {declared_total}; completitud NO MEDIDA")
    metadata.update({
        "resultados": rows,
        "retrieval_scope": "complete_query",
        "retrieval_pages": (offset // page_size) + (1 if rows or offset == 0 else 0),
        "retrieval_total": len(rows),
    })
    return metadata
