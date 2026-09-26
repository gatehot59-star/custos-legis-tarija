#!/usr/bin/env python3
"""Contratos del vertical MVP de Custos Legis.

Solo usa la biblioteca estándar para que el contrato pueda probarse en el mismo
entorno que ya ejecuta el backend. Las etapas son lógicas: no son agentes y no
pueden saltarse la revisión humana.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


Role = Literal["extractor", "investigador", "redactor", "verificador"]
Decision = Literal["aprobado", "rechazado", "correccion"]
AnswerState = Literal["grounded", "limited", "abstain", "chat"]
RetrievalScope = Literal["top_k", "complete_query"]


class SearchProvider(Protocol):
    """Puerto mínimo para BM25, vectorial o grafo."""

    def search(self, query: str, *, limit: int = 10) -> dict[str, Any]:
        """Devuelve resultados normalizados o la forma documentada del corpus."""


@dataclass(frozen=True)
class NumericValidation:
    """Resultado explícito de validar números de una afirmación."""

    status: Literal["validated", "not_applicable", "not_measured"]
    expected: str | None = None
    observed: str | None = None
    method: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "expected": self.expected,
            "observed": self.observed,
            "method": self.method,
        }


@dataclass(frozen=True)
class Citation:
    """Afirmación exportable: fuente, fragmento, vigencia y control numérico."""

    uid: str
    statement: str
    source_url: str | None
    fragment: str
    source_sha256: str | None
    vigencia: str
    numeric_validation: NumericValidation
    page_or_location: str | None = None

    @property
    def exportable(self) -> bool:
        return bool(
            self.uid
            and self.statement.strip()
            and self.source_url
            and self.source_url.startswith(("http://", "https://"))
            and self.fragment.strip()
            and self.source_sha256
            and self.vigencia == "VIGENTE"
            and self.numeric_validation.status in {"validated", "not_applicable"}
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "statement": self.statement,
            "source_url": self.source_url,
            "fragment": self.fragment,
            "source_sha256": self.source_sha256,
            "vigencia": self.vigencia,
            "numeric_validation": self.numeric_validation.as_dict(),
            "page_or_location": self.page_or_location,
            "exportable": self.exportable,
        }


@dataclass(frozen=True)
class DocumentRecord:
    """Documento recibido sin reescribir el original."""

    document_id: str
    case_id: str
    filename: str
    sha256: str
    media_type: str
    received_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "case_id": self.case_id,
            "filename": self.filename,
            "sha256": self.sha256,
            "media_type": self.media_type,
            "received_at": self.received_at,
        }


@dataclass(frozen=True)
class SearchSnapshot:
    """Salida del investigador, con candidatos que no deben pasar en silencio."""

    query: str
    engine: str
    workflow_version: str
    allowed_citations: tuple[Citation, ...] = ()
    unread_candidates: tuple[dict[str, Any], ...] = ()
    invalidated_precedents: tuple[dict[str, Any], ...] = ()
    answer_state: AnswerState = "abstain"
    evidence_ids: tuple[str, ...] = ()
    graph_context: tuple[str, ...] = ()
    retrieval_scope: RetrievalScope = "top_k"

    def as_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "engine": self.engine,
            "workflow_version": self.workflow_version,
            "answer_state": self.answer_state,
            "evidence_ids": list(self.evidence_ids),
            "graph_context": list(self.graph_context),
            "retrieval_scope": self.retrieval_scope,
            "allowed_citations": [c.as_dict() for c in self.allowed_citations],
            "unread_candidates": list(self.unread_candidates),
            "invalidated_precedents": list(self.invalidated_precedents),
        }


@dataclass(frozen=True)
class Workflow:
    """Workflow versionado por materia y jurisdicción."""

    version: str
    materia: str
    jurisdiccion: str
    roles: tuple[Role, ...] = (
        "extractor", "investigador", "redactor", "verificador"
    )
    pack_id: str | None = None
    steps: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "materia": self.materia,
            "jurisdiccion": self.jurisdiccion,
            "roles": list(self.roles),
            "pack_id": self.pack_id,
            "steps": list(self.steps),
        }


@dataclass(frozen=True)
class Draft:
    """Borrador reproducible, todavía no aprobado."""

    draft_id: str
    case_id: str
    content: str
    content_sha256: str
    workflow: Workflow
    search: SearchSnapshot
    deadline: dict[str, Any] | None
    warnings: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "case_id": self.case_id,
            "content": self.content,
            "content_sha256": self.content_sha256,
            "workflow": self.workflow.as_dict(),
            "search": self.search.as_dict(),
            "deadline": self.deadline,
            "warnings": list(self.warnings),
        }


@dataclass
class AuditEvent:
    """Evento inmutable de una etapa del flujo."""

    event_id: str
    event: str
    tenant_id: str
    case_id: str | None
    role: Role | None
    payload: dict[str, Any]
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event": self.event,
            "tenant_id": self.tenant_id,
            "case_id": self.case_id,
            "role": self.role,
            "payload": self.payload,
            "created_at": self.created_at,
        }


@dataclass
class AuditLedger:
    """Contrato de auditoría; la implementación puede ser JSONL o SQL."""

    append: Any
    events: list[AuditEvent] = field(default_factory=list)

    def record(self, event: AuditEvent) -> None:
        self.events.append(event)
        self.append(event.as_dict())
