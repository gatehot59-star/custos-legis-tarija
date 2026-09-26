#!/usr/bin/env python3
"""Patrones reutilizables de Custos Legis.

La implementación toma ideas concretas de Judicex, Mike y LegalGraphRAG, pero
las mantiene en stdlib y detrás de contratos pequeños:

* evidencia legal y memoria operativa no comparten el canal de citas;
* el answer contract solo acepta citas de evidencia legal registrada;
* los workflows son datos versionados, no ifs repartidos por el código;
* el retrieval gráfico es determinista, acotado y medible;
* las revisiones producen diff y hashes antes de la aprobación humana.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import Enum
from typing import Any, Iterable, Mapping


class EvidenceLayer(str, Enum):
    """Capas de memoria: solo LEGAL puede sostener una cita jurídica."""

    LEGAL = "legal"
    OPERATIONAL = "operational"


class AnswerState(str, Enum):
    """Estados públicos del contrato de respuesta, nunca una confianza inventada."""

    GROUNDED = "grounded"
    LIMITED = "limited"
    ABSTAIN = "abstain"
    CHAT = "chat"


@dataclass(frozen=True)
class EvidenceItem:
    """Unidad de evidencia con procedencia explícita."""

    evidence_id: str
    layer: EvidenceLayer
    text: str
    source_url: str | None = None
    source_sha256: str | None = None
    metadata: Mapping[str, Any] | None = None

    @property
    def citation_allowed(self) -> bool:
        """La memoria operativa jamás se convierte en autoridad jurídica."""
        return (
            self.layer is EvidenceLayer.LEGAL
            and bool(self.text.strip())
            and bool(self.source_url)
            and self.source_url.startswith(("http://", "https://"))
            and bool(self.source_sha256)
        )


@dataclass(frozen=True)
class Claim:
    """Afirmación que debe declarar qué evidencia la sostiene."""

    claim_id: str
    text: str
    citation_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnswerAssessment:
    """Resultado verificable del answer contract."""

    state: AnswerState
    accepted_citation_ids: tuple[str, ...]
    rejected_citation_ids: tuple[str, ...]
    unsupported_claim_ids: tuple[str, ...]
    errors: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "accepted_citation_ids": list(self.accepted_citation_ids),
            "rejected_citation_ids": list(self.rejected_citation_ids),
            "unsupported_claim_ids": list(self.unsupported_claim_ids),
            "errors": list(self.errors),
        }


class EvidenceRegistry:
    """Registro en memoria de una corrida, con dos canales sin contaminación."""

    def __init__(self) -> None:
        self._items: dict[str, EvidenceItem] = {}

    def add_legal(self, item: EvidenceItem) -> None:
        if item.layer is not EvidenceLayer.LEGAL:
            raise ValueError("add_legal exige evidencia de capa legal")
        self._items[item.evidence_id] = item

    def add_operational(self, item: EvidenceItem) -> None:
        if item.layer is not EvidenceLayer.OPERATIONAL:
            raise ValueError("add_operational exige memoria operativa")
        self._items[item.evidence_id] = item

    def get(self, evidence_id: str) -> EvidenceItem | None:
        return self._items.get(evidence_id)

    def legal_ids(self) -> tuple[str, ...]:
        return tuple(sorted(
            item.evidence_id for item in self._items.values()
            if item.layer is EvidenceLayer.LEGAL
        ))

    def assess(self, claims: Iterable[Claim], chat_only: bool = False) -> AnswerAssessment:
        """Valida claims contra evidencia legal registrada y permitida."""
        claims_list = tuple(claims)
        if chat_only and not claims_list:
            return AnswerAssessment(AnswerState.CHAT, (), (), ())
        accepted: list[str] = []
        rejected: list[str] = []
        unsupported: list[str] = []
        errors: list[str] = []
        for claim in claims_list:
            valid_for_claim = False
            for citation_id in claim.citation_ids:
                item = self._items.get(citation_id)
                if item is not None and item.citation_allowed:
                    accepted.append(citation_id)
                    valid_for_claim = True
                else:
                    rejected.append(citation_id)
            if not valid_for_claim:
                unsupported.append(claim.claim_id)
        accepted_unique = tuple(dict.fromkeys(accepted))
        rejected_unique = tuple(dict.fromkeys(rejected))
        if not claims_list:
            errors.append("no hay afirmaciones para evaluar")
            state = AnswerState.ABSTAIN
        elif len(unsupported) == 0:
            state = AnswerState.GROUNDED
        elif len(accepted_unique) > 0:
            state = AnswerState.LIMITED
        else:
            state = AnswerState.ABSTAIN
        if rejected_unique:
            errors.append("hay citas fuera de la evidencia legal permitida")
        return AnswerAssessment(
            state, accepted_unique, rejected_unique, tuple(unsupported), tuple(errors)
        )


@dataclass(frozen=True)
class WorkflowPack:
    """Workflow versionado como dato, inspirado en Mike/Judicex."""

    pack_id: str
    version: str
    jurisdiction: str
    materia: str
    roles: tuple[str, ...]
    steps: tuple[str, ...]
    required_inputs: tuple[str, ...]

    def validate(self) -> None:
        if not self.pack_id or not self.version:
            raise ValueError("workflow pack sin identidad/version")
        if not self.jurisdiction or not self.materia:
            raise ValueError("workflow pack sin jurisdicción/materia")
        if not self.roles or not self.steps:
            raise ValueError("workflow pack sin roles/steps")
        if len(set(self.steps)) != len(self.steps):
            raise ValueError("workflow pack con steps duplicados")

    def as_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "version": self.version,
            "jurisdiction": self.jurisdiction,
            "materia": self.materia,
            "roles": list(self.roles),
            "steps": list(self.steps),
            "required_inputs": list(self.required_inputs),
        }


# Datos versionados: agregar una materia no exige esconder reglas en el orquestador.
_WORKFLOW_PACK_DATA: tuple[dict[str, Any], ...] = (
    {
        "pack_id": "tarija-civil",
        "version": "tarija-civil-1.0",
        "jurisdiction": "Tarija",
        "materia": "civil",
        "roles": ("extractor", "investigador", "redactor", "verificador"),
        "steps": ("documento", "investigacion", "plazo", "borrador", "verificacion", "hitl", "exportacion"),
        "required_inputs": ("case_id", "materia", "jurisdiction", "deadline"),
    },
    {
        "pack_id": "tarija-penal",
        "version": "tarija-penal-1.0",
        "jurisdiction": "Tarija",
        "materia": "penal",
        "roles": ("extractor", "investigador", "redactor", "verificador"),
        "steps": ("documento", "investigacion", "plazo", "borrador", "verificacion", "hitl", "exportacion"),
        "required_inputs": ("case_id", "materia", "jurisdiction", "deadline"),
    },
)


def workflow_pack(materia: str, jurisdiction: str = "Tarija") -> WorkflowPack | None:
    """Devuelve un pack validado o None: lo no modelado no se disfraza."""
    wanted_materia = materia.strip().lower()
    wanted_jurisdiction = jurisdiction.strip().lower()
    for raw in _WORKFLOW_PACK_DATA:
        if (raw["materia"].lower() == wanted_materia
                and raw["jurisdiction"].lower() == wanted_jurisdiction):
            pack = WorkflowPack(**raw)
            pack.validate()
            return pack
    return None


@dataclass
class _GraphNode:
    record: dict[str, Any]
    neighbors: set[str]


class LegalGraph:
    """Índice gráfico pequeño: relaciones explícitas, hops acotados y ranking estable."""

    def __init__(self) -> None:
        self.nodes: dict[str, _GraphNode] = {}

    @staticmethod
    def _uid(record: Mapping[str, Any]) -> str:
        return str(record.get("uid") or "")

    @staticmethod
    def _relations(record: Mapping[str, Any]) -> set[str]:
        related: set[str] = set()
        for key in ("cites", "cita_a", "related_uids", "precedente_de"):
            value = record.get(key, ())
            if isinstance(value, str):
                value = (value,)
            if isinstance(value, (list, tuple, set)):
                related.update(str(item) for item in value if item)
        for edge in record.get("graph_edges", ()) or ():
            if isinstance(edge, Mapping):
                for key in ("to", "target", "uid"):
                    if edge.get(key):
                        related.add(str(edge[key]))
        return related

    def ingest(self, records: Iterable[Mapping[str, Any]]) -> None:
        """Construye el grafo sin inventar relaciones no presentes en el corpus."""
        materialized = [dict(record) for record in records]
        for record in materialized:
            uid = self._uid(record)
            if uid:
                self.nodes.setdefault(uid, _GraphNode(record, set()))
        for record in materialized:
            uid = self._uid(record)
            if not uid:
                continue
            for target in self._relations(record):
                if target in self.nodes:
                    self.nodes[uid].neighbors.add(target)
                    self.nodes[target].neighbors.add(uid)

    @staticmethod
    def _tokens(query: str) -> set[str]:
        return {token for token in re.findall(r"[\wáéíóúñ]+", query.lower()) if len(token) > 2}

    def search(self, query: str, limit: int = 10, max_hops: int = 2) -> list[dict[str, Any]]:
        """Expande semillas por relaciones y devuelve trazabilidad del camino."""
        if limit < 1:
            return []
        tokens = self._tokens(query)
        scored: list[tuple[float, str, int, tuple[str, ...]]] = []
        for uid, node in self.nodes.items():
            text = " ".join(str(node.record.get(key, "")) for key in ("uid", "afirmacion", "pasaje", "article"))
            overlap = len(tokens.intersection(self._tokens(text)))
            if overlap:
                scored.append((float(overlap), uid, 0, (uid,)))
        if not scored and self.nodes:
            scored = [(0.0, uid, 0, (uid,)) for uid in sorted(self.nodes)[:limit]]
        best: dict[str, tuple[float, int, tuple[str, ...]]] = {
            uid: (score, hop, path) for score, uid, hop, path in scored
        }
        frontier = list(best)
        for hop in range(1, max(0, max_hops) + 1):
            next_frontier: list[str] = []
            for source in frontier:
                source_score, _, source_path = best[source]
                for target in sorted(self.nodes[source].neighbors):
                    if target in best and best[target][1] <= hop:
                        continue
                    candidate = (source_score * 0.65, hop, source_path + (target,))
                    best[target] = candidate
                    next_frontier.append(target)
            frontier = next_frontier
        rows: list[dict[str, Any]] = []
        for uid, (score, hop, path) in sorted(
            best.items(), key=lambda item: (-item[1][0], item[1][1], item[0])
        )[:limit]:
            record = dict(self.nodes[uid].record)
            if str(record.get("vigencia", "VIGENTE")) == "DEROGADA" or record.get("anulado"):
                continue
            record["graph_score"] = round(score, 6)
            record["graph_hop"] = hop
            record["graph_path"] = list(path)
            rows.append(record)
        return rows


def draft_diff(before: str, after: str) -> dict[str, Any]:
    """Diff auditable para revisión tipo Mike: propuesta primero, aprobación después."""
    matcher = SequenceMatcher(a=before.splitlines(), b=after.splitlines())
    operations: list[dict[str, Any]] = []
    additions = deletions = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old_lines = before.splitlines()[i1:i2]
        new_lines = after.splitlines()[j1:j2]
        additions += len(new_lines)
        deletions += len(old_lines)
        operations.append({"op": tag, "before": old_lines, "after": new_lines})
    return {
        "changed": before != after,
        "before_sha256": hashlib.sha256(before.encode()).hexdigest(),
        "after_sha256": hashlib.sha256(after.encode()).hexdigest(),
        "additions": additions,
        "deletions": deletions,
        "operations": operations,
    }
