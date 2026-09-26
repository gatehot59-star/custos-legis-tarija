#!/usr/bin/env python3
"""Flujo vertical MVP de Custos Legis.

Une las piezas existentes sin convertirlas en agentes autónomos:
registro de documento, búsqueda citada, cálculo de plazo, borrador,
verificación, aprobación humana y exportación DOCX controlada.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import secrets
import zipfile
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any

try:
    from mvp_contract import (AuditEvent, AuditLedger, Citation, DocumentRecord,
                              Draft, NumericValidation, SearchProvider,
                              SearchSnapshot, Workflow)
except ImportError:  # pragma: no cover
    from .mvp_contract import (AuditEvent, AuditLedger, Citation, DocumentRecord,
                               Draft, NumericValidation, SearchProvider,
                               SearchSnapshot, Workflow)


WORKFLOW_VERSION = "mvp-vertical-1.0"
APPROVER_ROLES = frozenset({"socio", "asociado"})


class MVPError(RuntimeError):
    """Error de contrato del flujo, no un 500 opaco."""


class ApprovalRequired(MVPError):
    """Se intentó liberar o exportar sin aprobación válida."""


class ValidationBlocked(MVPError):
    """El verificador encontró evidencia insuficiente."""


def utc_now() -> str:
    """Devuelve un timestamp ISO-8601 con zona explícita."""
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    """Calcula el hash estable de un contenido textual."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    """Calcula el hash estable de un documento recibido."""
    return hashlib.sha256(value).hexdigest()


def _jsonl_append(path: str | Path):
    """Construye un sink JSONL que crea el directorio de auditoría."""
    target = Path(path)

    def append(event: dict[str, Any]) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True))
            stream.write("\n")

    return append


def ledger_for(path: str | Path | None = None) -> AuditLedger:
    """Crea una bitácora persistente o una bitácora en memoria para tests."""
    records: list[dict[str, Any]] = []
    return AuditLedger(_jsonl_append(path) if path else records.append)


def _numeric_validation(result: dict[str, Any], fragment: str) -> NumericValidation:
    """Normaliza la prueba numérica sin inventar que fue ejecutada."""
    raw = result.get("validacion_numerica")
    if isinstance(raw, dict):
        status = raw.get("status", "not_measured")
        if status in {"validated", "not_applicable", "not_measured"}:
            return NumericValidation(status=status,
                                     expected=raw.get("expected"),
                                     observed=raw.get("observed"),
                                     method=raw.get("method"))
    if not re.search(r"\d", fragment):
        return NumericValidation(status="not_applicable", method="sin cifras")
    return NumericValidation(status="not_measured", method="no se recibió recibo")


def citation_from_result(result: dict[str, Any]) -> Citation:
    """Convierte una fila del corpus en una cita auditable."""
    fragment = str(result.get("pasaje") or result.get("fragmento") or "")
    statement = str(result.get("afirmacion") or fragment).strip()
    return Citation(
        uid=str(result.get("uid") or ""),
        statement=statement,
        source_url=result.get("fuente_url") or result.get("source_url"),
        fragment=fragment,
        source_sha256=result.get("sha256") or result.get("source_sha256"),
        vigencia=str(result.get("vigencia") or "NO_MEDIDO"),
        numeric_validation=_numeric_validation(result, fragment),
        page_or_location=result.get("pagina") or result.get("ubicacion"),
    )


def _candidate(result: dict[str, Any], citation: Citation) -> dict[str, Any]:
    """Conserva un candidato no leído sin publicar texto innecesariamente."""
    return {
        "uid": citation.uid,
        "vigencia": citation.vigencia,
        "source_url": citation.source_url,
        "reason": "; ".join(filter(None, [
            "fuente ausente" if not citation.source_url else None,
            "fragmento ausente" if not citation.fragment.strip() else None,
            "hash de fuente ausente" if not citation.source_sha256 else None,
            f"vigencia={citation.vigencia}" if citation.vigencia != "VIGENTE" else None,
            f"validacion_numerica={citation.numeric_validation.status}"
            if citation.numeric_validation.status == "not_measured" else None,
        ])) or "no cumple el contrato de cita",
    }


def _docx_xml(text: str) -> str:
    """Genera un párrafo WordprocessingML sin dependencias externas."""
    return "<w:p><w:r><w:t xml:space=\"preserve\">" + escape(text) + \
        "</w:t></w:r></w:p>"


def build_docx(title: str, paragraphs: list[str]) -> bytes:
    """Construye un DOCX mínimo válido usando solo ZIP y XML de la stdlib."""
    content = "".join(_docx_xml(p) for p in [title, *paragraphs])
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{content}<w:sectPr/></w:body></w:document>"
    )
    types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>'
    )
    output = __import__("io").BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document)
    return output.getvalue()


@dataclass
class MVPService:
    """Orquestador determinista del MVP, con cuatro roles lógicos."""

    provider: SearchProvider
    ledger: AuditLedger
    documents: dict[str, DocumentRecord]
    drafts: dict[str, Draft]
    decisions: list[dict[str, Any]]

    @classmethod
    def create(cls, provider: SearchProvider, audit_path: str | Path | None = None) -> "MVPService":
        """Construye un servicio nuevo con almacenamiento de piloto."""
        return cls(provider=provider, ledger=ledger_for(audit_path),
                   documents={}, drafts={}, decisions=[])

    def _record(self, event: str, tenant_id: str, case_id: str | None,
                role: str | None, payload: dict[str, Any]) -> None:
        """Registra una transición antes de devolver su resultado."""
        self.ledger.record(AuditEvent(
            event_id=secrets.token_hex(12), event=event, tenant_id=tenant_id,
            case_id=case_id, role=role, payload=payload, created_at=utc_now()))

    def ingest_document(self, tenant_id: str, case_id: str, filename: str,
                        content: bytes, media_type: str = "application/pdf") -> DocumentRecord:
        """Registra metadatos y hash, conservando el original fuera de la bitácora."""
        if not tenant_id or not case_id or not filename or not content:
            raise MVPError("tenant, caso, nombre y contenido son obligatorios")
        document = DocumentRecord(
            document_id=secrets.token_urlsafe(12), case_id=case_id,
            filename=filename, sha256=sha256_bytes(content),
            media_type=media_type, received_at=utc_now())
        self.documents[document.document_id] = document
        self._record("documento_recibido", tenant_id, case_id, "extractor",
                     document.as_dict())
        return document

    def research(self, tenant_id: str, case_id: str, query: str,
                 limit: int = 10, engine: str = "bm25") -> SearchSnapshot:
        """Investiga y separa evidencia permitida de candidatos no leídos."""
        if not query.strip():
            raise MVPError("la consulta no puede estar vacía")
        raw = self.provider.search(query, limit=min(max(limit, 1), 50))
        allowed: list[Citation] = []
        unread: list[dict[str, Any]] = []
        invalidated: list[dict[str, Any]] = []
        for result in raw.get("resultados", []):
            citation = citation_from_result(result)
            if citation.vigencia == "DEROGADA" or result.get("anulado"):
                invalidated.append({"uid": citation.uid, "source_url": citation.source_url,
                                    "reason": "precedente o norma invalidada/derogada"})
            elif citation.exportable:
                allowed.append(citation)
            else:
                unread.append(_candidate(result, citation))
        snapshot = SearchSnapshot(query=query, engine=engine,
                                  workflow_version=WORKFLOW_VERSION,
                                  allowed_citations=tuple(allowed),
                                  unread_candidates=tuple(unread),
                                  invalidated_precedents=tuple(invalidated))
        self._record("investigacion_completada", tenant_id, case_id, "investigador",
                     snapshot.as_dict())
        return snapshot

    def draft(self, tenant_id: str, case_id: str, search: SearchSnapshot,
              deadline: dict[str, Any] | None, materia: str,
              jurisdiction: str = "Tarija") -> Draft:
        """Crea un borrador que solo afirma lo que tiene una cita permitida."""
        lines = [f"Borrador MVP, materia {materia}, jurisdicción {jurisdiction}."]
        warnings: list[str] = []
        for citation in search.allowed_citations:
            lines.append(f"Afirmación: {citation.statement}")
            lines.append(f"Cita: {citation.uid} · {citation.source_url}")
        if not search.allowed_citations:
            warnings.append("no hay afirmaciones exportables con cita completa")
            lines.append("No se formula una afirmación jurídica: falta evidencia exportable.")
        if search.unread_candidates:
            warnings.append(f"{len(search.unread_candidates)} candidatos no leídos")
        if search.invalidated_precedents:
            warnings.append(f"{len(search.invalidated_precedents)} precedentes invalidados excluidos")
        if deadline is None:
            warnings.append("no hay cálculo de plazo asociado")
        elif deadline.get("estado") != "CONFIRMADO":
            warnings.append("el plazo no está confirmado por el calendario y la regla")
        content = "\n".join(lines)
        draft = Draft(
            draft_id=secrets.token_urlsafe(12), case_id=case_id, content=content,
            content_sha256=sha256_text(content),
            workflow=Workflow(WORKFLOW_VERSION, materia, jurisdiction),
            search=search, deadline=deadline, warnings=tuple(warnings))
        self.drafts[draft.draft_id] = draft
        self._record("borrador_creado", tenant_id, case_id, "redactor", draft.as_dict())
        return draft

    def verify(self, draft_id: str) -> dict[str, Any]:
        """Aplica el gate de citas, vigencia, hash y plazo antes del HITL."""
        draft = self.drafts.get(draft_id)
        if draft is None:
            raise MVPError("borrador inexistente")
        errors: list[str] = []
        if not draft.search.allowed_citations:
            errors.append("no hay citas permitidas")
        if any(not c.exportable for c in draft.search.allowed_citations):
            errors.append("existe una cita que no cumple el contrato")
        if draft.deadline is None:
            errors.append("falta cálculo de plazo")
        elif draft.deadline.get("estado") != "CONFIRMADO":
            errors.append("el cálculo de plazo no está CONFIRMADO")
        result = {"ok": not errors, "draft_id": draft_id, "errors": errors,
                  "content_sha256": draft.content_sha256}
        return result

    def decide(self, tenant_id: str, case_id: str, draft_id: str,
               user_id: str, role: str, matricula: str | None,
               decision: str, fundamento: str = "") -> dict[str, Any]:
        """Registra aprobación, rechazo o pedido de corrección."""
        if decision not in {"aprobado", "rechazado", "correccion"}:
            raise MVPError("decisión inválida")
        draft = self.drafts.get(draft_id)
        if draft is None or draft.case_id != case_id:
            raise MVPError("borrador y caso no coinciden")
        if decision == "aprobado":
            if role not in APPROVER_ROLES or not matricula:
                raise ApprovalRequired("aprobar exige rol socio/asociado y matrícula")
            verification = self.verify(draft_id)
            if not verification["ok"]:
                raise ValidationBlocked("; ".join(verification["errors"]))
        record = {
            "decision_id": secrets.token_hex(12), "tenant_id": tenant_id,
            "case_id": case_id, "draft_id": draft_id,
            "content_sha256": draft.content_sha256, "user_id": user_id,
            "role": role, "matricula": matricula, "decision": decision,
            "fundamento": fundamento, "created_at": utc_now(),
        }
        self.decisions.append(record)
        self._record("decision_humana", tenant_id, case_id, "verificador", record)
        return record

    def export_docx(self, tenant_id: str, case_id: str, draft_id: str,
                    destination: str | Path) -> Path:
        """Exporta solo el borrador cuyo hash tiene aprobación vigente."""
        draft = self.drafts.get(draft_id)
        if draft is None or draft.case_id != case_id:
            raise MVPError("borrador y caso no coinciden")
        matching = [d for d in self.decisions
                    if d["tenant_id"] == tenant_id and d["case_id"] == case_id
                    and d["draft_id"] == draft_id
                    and d["content_sha256"] == draft.content_sha256]
        matching.sort(key=lambda d: (d["created_at"], d["decision_id"]), reverse=True)
        if not matching or matching[0]["decision"] != "aprobado":
            raise ApprovalRequired("DOCX bloqueado: falta aprobación vigente del hash exacto")
        paragraphs = draft.content.splitlines()
        paragraphs.append("\nCITAS Y CADENA DE CUSTODIA")
        paragraphs.extend(f"{c.uid}: {c.source_url} · sha256={c.source_sha256}"
                         for c in draft.search.allowed_citations)
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(build_docx(f"Custos Legis · {case_id}", paragraphs))
        self._record("exportacion_docx", tenant_id, case_id, "verificador",
                     {"draft_id": draft_id, "content_sha256": draft.content_sha256,
                      "path": str(target)})
        return target
