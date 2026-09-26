#!/usr/bin/env python3
"""Falsadores del contrato dirigido de LegalGraph."""
from __future__ import annotations

from patterns import LegalGraph


records = [
    {
        "uid": "norma-origen",
        "afirmacion": "La norma origen cita a la norma destino.",
        "pasaje": "cita expresa",
        "cites": ["norma-destino"],
        "vigencia": "VIGENTE",
    },
    {
        "uid": "norma-destino",
        "afirmacion": "La norma destino contiene la regla aplicable.",
        "pasaje": "regla aplicable",
        "vigencia": "VIGENTE",
    },
]

graph = LegalGraph()
graph.ingest(records)

forward = graph.search("cita expresa", limit=10, max_hops=1)
forward_ids = [row["uid"] for row in forward]
assert "norma-origen" in forward_ids
assert "norma-destino" in forward_ids

reverse = graph.search("regla aplicable", limit=10, max_hops=1)
reverse_ids = [row["uid"] for row in reverse]
assert "norma-destino" in reverse_ids
assert "norma-origen" not in reverse_ids

print("VERDE: LegalGraph conserva aristas dirigidas y rechaza la inversión")
