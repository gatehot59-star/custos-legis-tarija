#!/usr/bin/env python3
"""Prueba que el benchmark discrimina medido de no medido."""
from __future__ import annotations

import sys

from benchmark_busqueda import (CorpusEngine, QueryCase, UnavailableEngine, run)


class Provider:
    def search(self, query: str, *, limit: int = 10) -> dict:
        return {"resultados": [{"uid": "ley-439"}]}


queries = (QueryCase("artículo 90", ("ley-439",)),)
result = run([
    CorpusEngine(Provider()),
    UnavailableEngine("vectorial", "Qdrant no conectado: NO MEDIDO"),
], queries)

assert result["engines"]["bm25"]["status"] == "MEASURED"
assert result["engines"]["bm25"]["mean_recall_at_k"] == 1.0
assert result["engines"]["vectorial"]["status"] == "NO_MEDIDO"
assert result["engines"]["vectorial"]["rows"][0]["recall_at_k"] is None
print("VERDE benchmark: medido y no medido se distinguen")
