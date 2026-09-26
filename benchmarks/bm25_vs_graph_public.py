#!/usr/bin/env python3
"""Comparación pública y acotada: BM25 léxico vs grafo de abrogaciones.

Fuente única de datos: EXP-VIG-001 del corpus-legal-tarija, que publica las
cadenas 07 -> 129 -> 500 -> 520 y 094 -> 517, además de 432 -> 500.
No usa el SQLite privado ni inventa aristas.
"""
from __future__ import annotations

import math
import re
from collections import Counter

DOCS = [
    {"uid": "LD-129", "text": "Se abroga la Ley Departamental N° 07 Transitoria de Atribuciones y Funciones de los Ejecutivos Seccionales."},
    {"uid": "LD-500", "text": "Se abroga la Ley Departamental N° 129 y la Ley Departamental N° 432."},
    {"uid": "LD-520", "text": "Se abroga la Ley Departamental W 500."},
    {"uid": "LD-517", "text": "Se abroga la Ley Departamental N' 094 Departamentalización de Carreteras."},
]
EDGES = {
    "LD-007": ("LD-129",),
    "LD-129": ("LD-500",),
    "LD-432": ("LD-500",),
    "LD-500": ("LD-520",),
    "LD-094": ("LD-517",),
}
QUERIES = [
    {"id": "q-007", "query": "7", "seed": "LD-007", "relevant": {"LD-129", "LD-500"}},
    {"id": "q-129", "query": "129", "seed": "LD-129", "relevant": {"LD-500", "LD-520"}},
    {"id": "q-432", "query": "432", "seed": "LD-432", "relevant": {"LD-500", "LD-520"}},
    {"id": "q-500", "query": "500", "seed": "LD-500", "relevant": {"LD-520"}},
    {"id": "q-094", "query": "94", "seed": "LD-094", "relevant": {"LD-517"}},
]


def tokens(text: str) -> list[str]:
    raw = re.findall(r"[a-záéíóúñ]+|\d+", text.lower())
    out = []
    for token in raw:
        if token.isdigit():
            token = str(int(token))
        if len(token) >= 2 or token.isdigit():
            out.append(token)
    return out


def bm25(query: str, k: int = 2) -> list[str]:
    q = tokens(query)
    corpus = [tokens(doc["text"]) for doc in DOCS]
    avgdl = sum(map(len, corpus)) / len(corpus)
    df = Counter(term for terms in corpus for term in set(terms))
    scores = []
    k1, b = 1.2, 0.75
    for doc, terms in zip(DOCS, corpus):
        counts = Counter(terms)
        score = 0.0
        for term in q:
            if term not in counts:
                continue
            idf = math.log(1 + (len(corpus) - df[term] + 0.5) / (df[term] + 0.5))
            tf = counts[term]
            score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * len(terms) / avgdl))
        if score > 0:
            scores.append((score, doc["uid"]))
    return [uid for _, uid in sorted(scores, key=lambda x: (-x[0], x[1]))[:k]]


def graph(query: str, max_hops: int = 2, k: int = 2) -> list[str]:
    match = re.findall(r"\d+", query)
    if not match:
        return []
    seed = f"LD-{int(match[-1]):03d}"
    found: list[str] = []
    frontier = [seed]
    seen = {seed}
    for _ in range(max_hops):
        next_frontier = []
        for node in frontier:
            for target in EDGES.get(node, ()):
                if target not in seen:
                    seen.add(target)
                    found.append(target)
                    next_frontier.append(target)
        frontier = next_frontier
    return found[:k]


def metrics(pred: list[str], relevant: set[str], k: int = 2) -> tuple[float, float, float]:
    top = pred[:k]
    hits = [uid for uid in top if uid in relevant]
    precision = len(hits) / len(top) if top else 0.0
    recall = len(hits) / len(relevant) if relevant else 0.0
    rr = next((1 / (i + 1) for i, uid in enumerate(top) if uid in relevant), 0.0)
    return precision, recall, rr


rows = []
for item in QUERIES:
    bm = bm25(item["query"])
    gr = graph(item["query"])
    rows.append({
        "id": item["id"], "query": item["query"], "relevant": sorted(item["relevant"]),
        "bm25": bm, "graph": gr,
        "bm25_metrics": metrics(bm, item["relevant"]),
        "graph_metrics": metrics(gr, item["relevant"]),
    })

summary = {}
for engine in ("bm25", "graph"):
    values = [row[f"{engine}_metrics"] for row in rows]
    summary[engine] = {
        "precision_at_2": round(sum(v[0] for v in values) / len(values), 4),
        "recall_at_2": round(sum(v[1] for v in values) / len(values), 4),
        "mrr_at_2": round(sum(v[2] for v in values) / len(values), 4),
    }

print({"dataset": {"documents": len(DOCS), "queries": len(QUERIES), "edges": sum(map(len, EDGES.values()))}, "rows": rows, "summary": summary})
