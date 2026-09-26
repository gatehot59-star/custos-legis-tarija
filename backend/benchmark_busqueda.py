#!/usr/bin/env python3
"""Benchmark reproducible para BM25, vectorial y grafo.

El script no llama a un motor ausente ni convierte ausencia en cero. Un motor
no conectado queda `NO_MEDIDO`; el resultado conserva consulta, esperado,
recuperado, latencia y errores para que otra corrida pueda comparar lo mismo.
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class QueryCase:
    query: str
    expected_uids: tuple[str, ...]


DEFAULT_QUERIES: tuple[QueryCase, ...] = (
    QueryCase("artículo 90 Ley 439", ("ley-439",)),
    QueryCase("apelación auto definitivo", ("auto-definitivo",)),
    QueryCase("traslado demanda civil", ("traslado-demanda",)),
    QueryCase("medida cautelar penal", ("cautelar-penal",)),
    QueryCase("vacación judicial Tarija", ("vacacion-tarija",)),
    QueryCase("plazo contencioso administrativo", ("contencioso-264",)),
    QueryCase("precedente derogado", ("precedente-derogado",)),
    QueryCase("Ley Departamental Tarija", ("ley-departamental",)),
    QueryCase("vigencia norma nacional", ("norma-nacional",)),
    QueryCase("notificación judicial", ("notificacion",)),
)


class Engine(Protocol):
    """Puerto de un motor de recuperación."""

    name: str

    def search(self, query: str, limit: int = 10) -> list[str]:
        """Devuelve UIDs ordenados por relevancia."""


class CorpusEngine:
    """Adaptador del proveedor que devuelve la forma del corpus."""

    name = "bm25"

    def __init__(self, provider: Any):
        self.provider = provider

    def search(self, query: str, limit: int = 10) -> list[str]:
        data = self.provider.search(query, limit=limit)
        return [str(r.get("uid")) for r in data.get("resultados", []) if r.get("uid")]


class UnavailableEngine:
    """Representa vectorial o grafo no conectados, sin disfrazarlos de cero."""

    def __init__(self, name: str, reason: str):
        self.name = name
        self.reason = reason

    def search(self, query: str, limit: int = 10) -> list[str]:
        raise RuntimeError(self.reason)


def run(engines: list[Engine], queries: tuple[QueryCase, ...] = DEFAULT_QUERIES,
        limit: int = 10) -> dict[str, Any]:
    """Ejecuta la misma batería contra cada engine y calcula recall@k."""
    output: dict[str, Any] = {"queries": len(queries), "limit": limit, "engines": {}}
    for engine in engines:
        rows: list[dict[str, Any]] = []
        for case in queries:
            started = time.perf_counter()
            try:
                retrieved = engine.search(case.query, limit=limit)
                elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
                expected = set(case.expected_uids)
                found = len(expected.intersection(retrieved))
                rows.append({
                    "query": case.query,
                    "expected_uids": list(case.expected_uids),
                    "retrieved_uids": retrieved,
                    "recall_at_k": found / len(expected) if expected else None,
                    "latency_ms": elapsed_ms,
                    "status": "MEASURED",
                })
            except Exception as exc:  # noqa: BLE001
                rows.append({
                    "query": case.query,
                    "expected_uids": list(case.expected_uids),
                    "retrieved_uids": [],
                    "recall_at_k": None,
                    "latency_ms": None,
                    "status": "NO_MEDIDO",
                    "error": f"{type(exc).__name__}: {exc}",
                })
        measured = [r for r in rows if r["status"] == "MEASURED"]
        output["engines"][engine.name] = {
            "rows": rows,
            "mean_recall_at_k": (
                sum(r["recall_at_k"] for r in measured) / len(measured)
                if measured else None
            ),
            "mean_latency_ms": (
                sum(r["latency_ms"] for r in measured) / len(measured)
                if measured else None
            ),
            "status": "MEASURED" if measured else "NO_MEDIDO",
        }
    return output


def save(result: dict[str, Any], destination: str) -> None:
    """Escribe el recibo JSON completo, sin resumir ni recortar filas."""
    with open(destination, "w", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    print("Este instrumento necesita un proveedor corpus y 10-30 consultas; no "
          "simula resultados desde CLI. Use run() desde un runner autorizado.")
    sys.exit(2)
