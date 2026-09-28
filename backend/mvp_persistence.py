#!/usr/bin/env python3
"""Persistencia PostgreSQL del vertical MVP con contratos tipados y transacciones."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable

from mvp_contract import Citation, Draft, NumericValidation, SearchSnapshot, Workflow


class MVPPersistenceError(RuntimeError):
    """Error de persistencia que detiene el flujo y no degrada a memoria."""


_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


class MVPRepository:
    """Repositorio PostgreSQL del MVP, siempre dentro del tenant solicitado."""

    def __init__(self, dsn: str) -> None:
        if not isinstance(dsn, str) or not dsn.strip():
            raise ValueError("DATABASE_URL_APP es obligatorio para persistencia")
        self.dsn = dsn

    def _connect(self, tenant_id: str):
        """Abre una conexión transaccional con RLS fijado al tenant."""
        if not tenant_id or not isinstance(tenant_id, str):
            raise MVPPersistenceError("tenant_id obligatorio para persistir el MVP")
        connection = None
        try:
            import psycopg
            from psycopg.rows import dict_row
            connection = psycopg.connect(self.dsn, row_factory=dict_row)
            with connection.cursor() as cursor:
                cursor.execute("SELECT app.set_tenant(%s)", (tenant_id,))
            return connection
        except Exception as exc:  # noqa: BLE001
            if connection is not None:
                connection.close()
            raise MVPPersistenceError(
                f"no se pudo abrir persistencia MVP: {type(exc).__name__}: {exc}") from exc

    @staticmethod
    def _audit_args(event: dict[str, Any]) -> tuple[Any, ...]:
        """Convierte un evento en parámetros para el ledger SQL."""
        return (event["event_id"], event["tenant_id"], event.get("case_id"),
                event["event"], _json(event), event["created_at"])

    def _execute(self, tenant_id: str, sql: str, args: tuple[Any, ...] = ()) -> None:
        """Ejecuta una escritura y confirma solo si PostgreSQL la acepta."""
        connection = self._connect(tenant_id)
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, args)
            connection.commit()
        except Exception as exc:  # noqa: BLE001
            connection.rollback()
            raise MVPPersistenceError(
                f"falló escritura de persistencia MVP: {type(exc).__name__}: {exc}") from exc
        finally:
            connection.close()

    def _execute_with_audit(self, tenant_id: str, sql: str,
                            args: tuple[Any, ...], event: dict[str, Any]) -> None:
        """Confirma negocio y auditoría en la misma transacción PostgreSQL."""
        connection = self._connect(tenant_id)
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, args)
                cursor.execute(
                    """INSERT INTO public.cl_mvp_audit_events
                       (id, tenant_id, case_id, event, payload, created_at)
                       VALUES (%s, %s, %s, %s, %s::jsonb, %s::timestamptz)""",
                    self._audit_args(event),
                )
            connection.commit()
        except Exception as exc:  # noqa: BLE001
            connection.rollback()
            raise MVPPersistenceError(
                f"falló transacción MVP negocio+auditoría: {type(exc).__name__}: {exc}") from exc
        finally:
            connection.close()

    def _fetchone(self, tenant_id: str, sql: str,
                  args: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        """Lee una fila bajo RLS o devuelve None si no pertenece al tenant."""
        connection = self._connect(tenant_id)
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, args)
                row = cursor.fetchone()
            connection.commit()
            return dict(row) if row else None
        except Exception as exc:  # noqa: BLE001
            connection.rollback()
            raise MVPPersistenceError(
                f"falló lectura de persistencia MVP: {type(exc).__name__}: {exc}") from exc
        finally:
            connection.close()

    def _fetchall(self, tenant_id: str, sql: str,
                  args: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        """Lee filas bajo RLS y conserva un resultado explícito vacío."""
        connection = self._connect(tenant_id)
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, args)
                rows = cursor.fetchall()
            connection.commit()
            return [dict(row) for row in rows]
        except Exception as exc:  # noqa: BLE001
            connection.rollback()
            raise MVPPersistenceError(
                f"falló lectura de persistencia MVP: {type(exc).__name__}: {exc}") from exc
        finally:
            connection.close()

    @staticmethod
    def _validate_draft(draft: Draft) -> None:
        """Rechaza un borrador cuyo hash no sea el hash de su contenido real."""
        actual = hashlib.sha256(draft.content.encode("utf-8")).hexdigest()
        if draft.content_sha256 != actual:
            raise MVPPersistenceError("hash de borrador no coincide con el contenido")
        if not _HASH_RE.fullmatch(draft.content_sha256):
            raise MVPPersistenceError("content_sha256 de borrador inválido")

    @staticmethod
    def _validate_decision(decision: dict[str, Any]) -> None:
        """Rechaza decisiones sin campos tipados mínimos o con valores inválidos."""
        required = ("decision_id", "tenant_id", "case_id", "draft_id",
                    "content_sha256", "user_id", "role", "decision", "created_at")
        missing = [key for key in required if not str(decision.get(key) or "").strip()]
        if missing:
            raise MVPPersistenceError(f"decisión inválida: faltan {', '.join(missing)}")
        if not _HASH_RE.fullmatch(str(decision["content_sha256"])):
            raise MVPPersistenceError("content_sha256 de decisión inválido")
        if decision["decision"] not in {"aprobado", "rechazado", "correccion"}:
            raise MVPPersistenceError("decisión inválida")
        if decision["decision"] == "aprobado" and (
            decision["role"] not in {"socio", "asociado"}
            or not str(decision.get("matricula") or "").strip()
        ):
            raise MVPPersistenceError("aprobación sin rol o matrícula válida")

    def save_document(self, tenant_id: str, document: Any,
                      content_sha256: str) -> None:
        """Persiste los metadatos y el hash del documento recibido."""
        self._execute(
            tenant_id,
            """INSERT INTO public.cl_mvp_documents
               (id, tenant_id, case_id, content_sha256, payload)
               VALUES (%s, %s, %s, %s, %s::jsonb)
               ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload,
                 content_sha256 = EXCLUDED.content_sha256""",
            (document.document_id, tenant_id, document.case_id, content_sha256,
             _json(document.as_dict())),
        )

    def save_document_with_audit(self, tenant_id: str, document: Any,
                                 content_sha256: str, event: dict[str, Any]) -> None:
        """Persiste documento y auditoría en una única transacción."""
        self._execute_with_audit(tenant_id,
            """INSERT INTO public.cl_mvp_documents
               (id, tenant_id, case_id, content_sha256, payload)
               VALUES (%s, %s, %s, %s, %s::jsonb)
               ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload,
                 content_sha256 = EXCLUDED.content_sha256""",
            (document.document_id, tenant_id, document.case_id, content_sha256,
             _json(document.as_dict())), event)

    def save_search(self, tenant_id: str, search_id: str, case_id: str,
                    snapshot: SearchSnapshot) -> None:
        """Persiste una investigación citada y su alcance de retrieval."""
        self._execute(tenant_id,
            """INSERT INTO public.cl_mvp_searches
               (id, tenant_id, case_id, payload)
               VALUES (%s, %s, %s, %s::jsonb)
               ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload""",
            (search_id, tenant_id, case_id, _json(snapshot.as_dict())))

    def save_search_with_audit(self, tenant_id: str, search_id: str,
                               case_id: str, snapshot: SearchSnapshot,
                               event: dict[str, Any]) -> None:
        """Persiste investigación y auditoría en una única transacción."""
        self._execute_with_audit(tenant_id,
            """INSERT INTO public.cl_mvp_searches
               (id, tenant_id, case_id, payload)
               VALUES (%s, %s, %s, %s::jsonb)
               ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload""",
            (search_id, tenant_id, case_id, _json(snapshot.as_dict())), event)

    def save_draft(self, tenant_id: str, draft: Draft) -> None:
        """Persiste el borrador y valida el hash contra su contenido."""
        self._validate_draft(draft)
        self._execute(tenant_id,
            """INSERT INTO public.cl_mvp_drafts
               (id, tenant_id, case_id, payload, content, content_sha256)
               VALUES (%s, %s, %s, %s::jsonb, %s, %s)
               ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload,
                 content = EXCLUDED.content, content_sha256 = EXCLUDED.content_sha256,
                 actualizado_en = now()""",
            (draft.draft_id, tenant_id, draft.case_id, _json(draft.as_dict()),
             draft.content, draft.content_sha256))

    def save_draft_with_audit(self, tenant_id: str, draft: Draft,
                              event: dict[str, Any]) -> None:
        """Persiste borrador y auditoría en una única transacción."""
        self._validate_draft(draft)
        self._execute_with_audit(tenant_id,
            """INSERT INTO public.cl_mvp_drafts
               (id, tenant_id, case_id, payload, content, content_sha256)
               VALUES (%s, %s, %s, %s::jsonb, %s, %s)
               ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload,
                 content = EXCLUDED.content, content_sha256 = EXCLUDED.content_sha256,
                 actualizado_en = now()""",
            (draft.draft_id, tenant_id, draft.case_id, _json(draft.as_dict()),
             draft.content, draft.content_sha256), event)

    def save_decision(self, tenant_id: str, decision: dict[str, Any]) -> None:
        """Persiste una decisión tipada e inmutable para el hash exacto."""
        self._validate_decision(decision)
        self._execute(tenant_id, self._decision_sql(), self._decision_args(decision))

    def save_decision_with_audit(self, tenant_id: str, decision: dict[str, Any],
                                 event: dict[str, Any]) -> None:
        """Persiste decisión y auditoría en una única transacción."""
        self._validate_decision(decision)
        self._execute_with_audit(tenant_id, self._decision_sql(),
                                 self._decision_args(decision), event)

    @staticmethod
    def _decision_sql() -> str:
        """Devuelve el INSERT tipado de decisiones humanas."""
        return """INSERT INTO public.cl_mvp_decisions
          (id, tenant_id, case_id, draft_id, content_sha256, actor_user_id,
           actor_role, matricula, decision, fundamento, payload)
          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)"""

    @staticmethod
    def _decision_args(decision: dict[str, Any]) -> tuple[Any, ...]:
        """Alinea el payload histórico con las columnas tipadas."""
        return (decision["decision_id"], decision["tenant_id"], decision["case_id"],
                decision["draft_id"], decision["content_sha256"], decision["user_id"],
                decision["role"], decision.get("matricula"), decision["decision"],
                decision.get("fundamento", ""), _json(decision))

    def save_audit(self, tenant_id: str, event: dict[str, Any]) -> None:
        """Persiste un evento de auditoría inmutable."""
        self._execute(tenant_id,
            """INSERT INTO public.cl_mvp_audit_events
               (id, tenant_id, case_id, event, payload, created_at)
               VALUES (%s, %s, %s, %s, %s::jsonb, %s::timestamptz)""",
            self._audit_args(event))

    def load_search(self, tenant_id: str, search_id: str) -> tuple[str, SearchSnapshot] | None:
        """Recupera una investigación del tenant y reconstruye su contrato."""
        row = self._fetchone(tenant_id,
            "SELECT case_id, payload FROM public.cl_mvp_searches WHERE id = %s",
            (search_id,))
        if not row:
            return None
        return str(row["case_id"]), search_from_dict(row["payload"])

    def load_draft(self, tenant_id: str, draft_id: str) -> Draft | None:
        """Recupera un borrador y vuelve a comprobar su hash real."""
        row = self._fetchone(tenant_id,
            "SELECT payload, content, content_sha256 FROM public.cl_mvp_drafts WHERE id = %s",
            (draft_id,))
        if not row:
            return None
        draft = draft_from_dict(row["payload"])
        if row["content"] != draft.content or row["content_sha256"] != draft.content_sha256:
            raise MVPPersistenceError("columnas tipadas y payload de borrador divergen")
        return draft

    def load_decisions(self, tenant_id: str, case_id: str,
                       draft_id: str) -> list[dict[str, Any]]:
        """Recupera decisiones del borrador bajo RLS y orden estable."""
        rows = self._fetchall(tenant_id,
            """SELECT payload FROM public.cl_mvp_decisions
               WHERE case_id = %s AND draft_id = %s
               ORDER BY creado_en DESC, id DESC""",
            (case_id, draft_id))
        return [dict(row["payload"]) for row in rows]


def _json(value: Any) -> str:
    """Serializa JSON preservando UTF-8 y sin objetos no contractuales."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def citation_from_dict(raw: dict[str, Any]) -> Citation:
    """Reconstruye una cita persistida."""
    numeric = raw.get("numeric_validation") or {}
    return Citation(
        uid=str(raw.get("uid") or ""), statement=str(raw.get("statement") or ""),
        source_url=raw.get("source_url"), fragment=str(raw.get("fragment") or ""),
        source_sha256=raw.get("source_sha256"),
        vigencia=str(raw.get("vigencia") or "NO_MEDIDO"),
        numeric_validation=NumericValidation(
            status=str(numeric.get("status") or "not_measured"),
            expected=numeric.get("expected"), observed=numeric.get("observed"),
            method=numeric.get("method")), page_or_location=raw.get("page_or_location"))


def search_from_dict(raw: dict[str, Any]) -> SearchSnapshot:
    """Reconstruye una investigación persistida sin reconsultar el Corpus."""
    return SearchSnapshot(
        query=str(raw.get("query") or ""), engine=str(raw.get("engine") or "bm25"),
        workflow_version=str(raw.get("workflow_version") or ""),
        allowed_citations=tuple(citation_from_dict(item) for item in raw.get("allowed_citations", [])),
        unread_candidates=tuple(raw.get("unread_candidates", [])),
        invalidated_precedents=tuple(raw.get("invalidated_precedents", [])),
        answer_state=str(raw.get("answer_state") or "abstain"),
        evidence_ids=tuple(str(item) for item in raw.get("evidence_ids", [])),
        graph_context=tuple(str(item) for item in raw.get("graph_context", [])),
        retrieval_scope=str(raw.get("retrieval_scope") or "top_k"))


def draft_from_dict(raw: dict[str, Any]) -> Draft:
    """Reconstruye un borrador y rechaza hash inconsistente."""
    workflow_raw = raw.get("workflow") or {}
    workflow = Workflow(
        version=str(workflow_raw.get("version") or ""),
        materia=str(workflow_raw.get("materia") or ""),
        jurisdiccion=str(workflow_raw.get("jurisdiccion") or ""),
        roles=tuple(workflow_raw.get("roles", ())), pack_id=workflow_raw.get("pack_id"),
        steps=tuple(workflow_raw.get("steps", ())),)
    draft = Draft(
        draft_id=str(raw.get("draft_id") or ""), case_id=str(raw.get("case_id") or ""),
        content=str(raw.get("content") or ""),
        content_sha256=str(raw.get("content_sha256") or ""), workflow=workflow,
        search=search_from_dict(raw.get("search") or {}), deadline=raw.get("deadline"),
        warnings=tuple(str(item) for item in raw.get("warnings", [])))
    actual = hashlib.sha256(draft.content.encode("utf-8")).hexdigest()
    if draft.content_sha256 != actual:
        raise MVPPersistenceError("hash de borrador persistido no coincide con contenido")
    return draft
