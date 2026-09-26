#!/usr/bin/env python3
"""backend/mvp_http.py: rutas HTTP del vertical MVP, detrás de la sesión existente.

Este módulo no crea autenticación paralela. Recibe la sesión ya validada por
`api.py`, comprueba que el caso pertenece al bufete y expone las etapas del
vertical como transiciones explícitas. El estado del orquestador es de piloto,
conservado en memoria; la auditoría puede persistirse en JSONL mediante
`CUSTOS_MVP_AUDIT_PATH`.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import os
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mvp import (ApprovalRequired, MVPError, MVPService, ValidationBlocked,
                 sha256_bytes)
from mvp_contract import DocumentRecord, SearchSnapshot

MAX_DOCUMENT_BYTES = 10 * 1024 * 1024


class MVPHTTPError(MVPError):
    """Error del adaptador con estado HTTP determinista."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class SearchContext:
    """Propiedad de una búsqueda guardada en el orquestador del piloto."""

    tenant_id: str
    case_id: str
    snapshot: SearchSnapshot


@dataclass(frozen=True)
class DraftContext:
    """Propiedad de un borrador para impedir cruces entre bufetes."""

    tenant_id: str
    case_id: str


@dataclass
class CorpusProvider:
    """Adapta el `buscar` existente al puerto `SearchProvider` del MVP."""

    corpus: Any

    def search(self, query: str, *, limit: int = 10) -> dict[str, Any]:
        """Consulta el cliente de corpus existente sin leer su almacenamiento."""
        return self.corpus.buscar(query, limit=limit)


@dataclass
class MVPHTTPState:
    """Estado HTTP del vertical y sus índices de propiedad por tenant."""

    service: MVPService
    searches: dict[str, SearchContext] = field(default_factory=dict)
    drafts: dict[str, DraftContext] = field(default_factory=dict)
    documents: dict[str, str] = field(default_factory=dict)
    lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    @classmethod
    def create(cls, corpus: Any) -> "MVPHTTPState":
        """Crea el adaptador usando el corpus inyectado por `App`."""
        audit_path = os.environ.get("CUSTOS_MVP_AUDIT_PATH") or None
        return cls(MVPService.create(CorpusProvider(corpus), audit_path=audit_path))

    @staticmethod
    def _require_case(almacen: Any, session: Any, case_id: str) -> None:
        """Comprueba que el caso existe en el tenant de la sesión."""
        if not isinstance(case_id, str) or not case_id.strip():
            raise MVPHTTPError(400, "case_id es obligatorio")
        if almacen.caso(session.usuario.tenant_id, case_id) is None:
            raise MVPHTTPError(404, "caso inexistente en este bufete")

    @staticmethod
    def _required_string(body: dict[str, Any], name: str) -> str:
        """Lee un campo textual obligatorio del JSON."""
        value = body.get(name)
        if not isinstance(value, str) or not value.strip():
            raise MVPHTTPError(400, f"{name} es obligatorio")
        return value.strip()

    @staticmethod
    def _decode_content(body: dict[str, Any]) -> bytes:
        """Decodifica contenido base64 y aplica un límite de tamaño del piloto."""
        encoded = body.get("contenido_base64")
        if not isinstance(encoded, str) or not encoded:
            raise MVPHTTPError(400, "contenido_base64 es obligatorio")
        try:
            content = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise MVPHTTPError(400, "contenido_base64 inválido") from exc
        if not content:
            raise MVPHTTPError(400, "el documento no puede estar vacío")
        if len(content) > MAX_DOCUMENT_BYTES:
            raise MVPHTTPError(413, "el documento supera el límite de 10 MiB")
        return content

    @staticmethod
    def _json_hash(value: bytes) -> str:
        """Devuelve el hash usado para verificar la descarga del DOCX."""
        return hashlib.sha256(value).hexdigest()

    def _owned_search(self, session: Any, search_id: str) -> SearchSnapshot:
        """Obtiene una búsqueda y verifica su tenant y caso."""
        context = self.searches.get(search_id)
        if context is None:
            raise MVPHTTPError(404, "investigación inexistente")
        if context.tenant_id != session.usuario.tenant_id:
            raise MVPHTTPError(404, "investigación inexistente en este bufete")
        return context.snapshot

    def _owned_draft(self, session: Any, draft_id: str) -> DraftContext:
        """Obtiene un borrador y verifica su tenant."""
        context = self.drafts.get(draft_id)
        if context is None:
            raise MVPHTTPError(404, "borrador inexistente")
        if context.tenant_id != session.usuario.tenant_id:
            raise MVPHTTPError(404, "borrador inexistente en este bufete")
        return context

    def handle(self, method: str, path: str, body: dict[str, Any],
               session: Any, almacen: Any) -> tuple[int, dict[str, Any]]:
        """Despacha una ruta `/mvp/*` ya autenticada."""
        with self.lock:
            tenant_id = session.usuario.tenant_id
            if method == "POST" and path == "/mvp/documentos":
                case_id = self._required_string(body, "case_id")
                self._require_case(almacen, session, case_id)
                filename = self._required_string(body, "filename")
                content = self._decode_content(body)
                media_type = body.get("media_type", "application/pdf")
                if not isinstance(media_type, str) or not media_type.strip():
                    raise MVPHTTPError(400, "media_type inválido")
                document = self.service.ingest_document(
                    tenant_id, case_id, filename, content, media_type.strip())
                self.documents[document.document_id] = tenant_id
                return 201, {"documento": document.as_dict(),
                             "contenido_sha256": sha256_bytes(content)}

            if method == "POST" and path == "/mvp/investigaciones":
                case_id = self._required_string(body, "case_id")
                self._require_case(almacen, session, case_id)
                query = self._required_string(body, "query")
                limit = body.get("limit", 10)
                if not isinstance(limit, int) or isinstance(limit, bool):
                    raise MVPHTTPError(400, "limit debe ser entero")
                engine = body.get("engine", "bm25")
                if not isinstance(engine, str) or not engine.strip():
                    raise MVPHTTPError(400, "engine inválido")
                snapshot = self.service.research(
                    tenant_id, case_id, query, limit=limit, engine=engine.strip())
                search_id = hashlib.sha256(
                    f"{tenant_id}:{case_id}:{snapshot.query}:{snapshot.workflow_version}".encode()
                ).hexdigest()[:24]
                self.searches[search_id] = SearchContext(tenant_id, case_id, snapshot)
                return 201, {"search_id": search_id, "case_id": case_id,
                             "investigacion": snapshot.as_dict()}

            if method == "POST" and path == "/mvp/borradores":
                case_id = self._required_string(body, "case_id")
                self._require_case(almacen, session, case_id)
                search_id = self._required_string(body, "search_id")
                search_context = self.searches.get(search_id)
                snapshot = self._owned_search(session, search_id)
                if search_context is None or search_context.case_id != case_id:
                    raise MVPHTTPError(409, "la investigación no pertenece a este caso")
                deadline = body.get("deadline")
                if deadline is not None and not isinstance(deadline, dict):
                    raise MVPHTTPError(400, "deadline debe ser objeto o null")
                materia = self._required_string(body, "materia")
                jurisdiction = body.get("jurisdiction", "Tarija")
                if not isinstance(jurisdiction, str) or not jurisdiction.strip():
                    raise MVPHTTPError(400, "jurisdiction inválida")
                draft = self.service.draft(
                    tenant_id, case_id, snapshot, deadline, materia,
                    jurisdiction.strip())
                self.drafts[draft.draft_id] = DraftContext(tenant_id, case_id)
                return 201, {"borrador": draft.as_dict()}

            if method == "POST" and path.startswith("/mvp/borradores/"):
                suffix = path[len("/mvp/borradores/"):]
                parts = suffix.split("/")
                draft_id = parts[0] if parts else ""
                context = self._owned_draft(session, draft_id)
                draft = self.service.drafts[draft_id]
                if context.case_id != self._required_string(body, "case_id"):
                    raise MVPHTTPError(409, "el borrador no pertenece a este caso")
                if len(parts) == 2 and parts[1] == "verificar":
                    return 200, {"verificacion": self.service.verify(draft_id)}
                if len(parts) == 2 and parts[1] == "decision":
                    decision = self._required_string(body, "decision")
                    fundamento = body.get("fundamento", "")
                    if not isinstance(fundamento, str):
                        raise MVPHTTPError(400, "fundamento inválido")
                    try:
                        record = self.service.decide(
                            session.usuario.tenant_id, context.case_id, draft_id,
                            session.usuario.id, session.usuario.rol,
                            session.usuario.matricula, decision, fundamento)
                    except ApprovalRequired as exc:
                        raise MVPHTTPError(403, str(exc)) from exc
                    except ValidationBlocked as exc:
                        raise MVPHTTPError(422, str(exc)) from exc
                    return 201, {"decision": record}
                if len(parts) == 2 and parts[1] == "exportar":
                    if body.get("case_id") != context.case_id:
                        raise MVPHTTPError(409, "el borrador no pertenece a este caso")
                    with tempfile.TemporaryDirectory(prefix="custos-mvp-") as temp:
                        target = Path(temp) / f"{draft_id}.docx"
                        self.service.export_docx(
                            session.usuario.tenant_id, context.case_id, draft_id, target)
                        content = target.read_bytes()
                    return 200, {
                        "filename": f"custos-legis-{context.case_id}.docx",
                        "media_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "content_base64": base64.b64encode(content).decode("ascii"),
                        "content_sha256": self._json_hash(content),
                    }
                raise MVPHTTPError(404, "ruta de borrador inexistente")

            raise MVPHTTPError(404, f"no existe {method} {path}")
