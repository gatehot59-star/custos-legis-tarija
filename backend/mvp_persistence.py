#!/usr/bin/env python3
"""backend/mvp_persistence.py: persistencia PostgreSQL del vertical MVP.

Guarda documentos, investigaciones, borradores, decisiones humanas y eventos
 de auditoría con tenant_id explícito. El aislamiento no lo hace el filtro de
Python: cada operación fija app.tenant_id y depende de RLS.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from mvp_contract import (Citation, Draft, NumericValidation, SearchSnapshot,
                          Workflow)


class MVPPersistenceError(RuntimeError):
    """Error de persistencia que debe detener el flujo, no degradarlo a memoria."""


class MVPRepository:
    """Repositorio PostgreSQL del MVP, siempre dentro del tenant solicitado."""

    def __init__(self, dsn: str) -> None:
        if not isinstance(dsn, str) or not dsn.strip():
            raise ValueError("DATABASE_URL_APP es obligatorio para persistencia")
        self.dsn = dsn

    def _connect(self, tenant_id: str):
        """Abre una transacción con RLS fijado al tenant de la operación."""
        if not tenant_id or not isinstance(tenant_id, str):
            raise MVPPersistenceError("tenant_id obligatorio para persistir el MVP")
        try:
            import psycopg
            from psycopg.rows import dict_row
            connection = psycopg.connect(self.dsn, row_factory=dict_row)
            with connection.cursor() as cursor:
                cursor.execute("SELECT app.set_tenant(%s)", (tenant_id,))
            return connection
        except Exception as exc:  # noqa: BLE001
            raise MVPPersistenceError(
                f"no se pudo abrir persistencia MVP: {type(exc).__name__}: {exc}") from exc

    def _execute(self, tenant_id: str, sql: str, args: tuple[Any, ...] = ()) -> None:
        """Ejecuta una escritura y confirma solo si PostgreSQL la acepta."""
        try:
            connection = self._connect(tenant_id)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(sql, args)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()
        except MVPPersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise MVPPersistenceError(
                f"falló escritura de persistencia MVP: {type(exc).__name__}: {exc}") from exc

    def _fetchone(self, tenant_id: str, sql: str,
                  args: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        """Lee una fila bajo RLS o devuelve None si no pertenece al tenant."""
        try:
            connection = self._connect(tenant_id)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(sql, args)
                    row = cursor.fetchone()
                connection.commit()
                return dict(row) if row else None
            finally:
                connection.close()
        except MVPPersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise MVPPersistenceError(
                f"falló lectura de persistencia MVP: {type(exc).__name__}: {exc}") from exc

    def _fetchall(self, tenant_id: str, sql: str,
                  args: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        """Lee filas bajo RLS y conserva un resultado explícito vacío."""
        try:
            connection = self._connect(tenant_id)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(sql, args)
                    rows = cursor.fetchall()
                connection.commit()
                return [dict(row) for row in rows]
            finally:
                connection.close()
        except MVPPersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise MVPPersistenceError(
                f"falló lectura de persistencia MVP: {type(exc).__name__}: {exc}") from exc

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

    def save_search(self, tenant_id: str, search_id: str, case_id: str,
                    snapshot: SearchSnapshot) -> None:
        """Persiste una investigación citada y su alcance de retrieval."""
        self._execute(
            tenant_id,
            """INSERT INTO public.cl_mvp_searches
               (id, tenant_id, case_id, payload)
               VALUES (%s, %s, %s, %s::jsonb)
               ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload""",
            (search_id, tenant_id, case_id, _json(snapshot.as_dict())),
        )

    def save_draft(self, tenant_id: str, draft: Draft) -> None:
        """Persiste el borrador completo antes de devolverlo al cliente."""
        self._execute(
            tenant_id,
            """INSERT INTO public.cl_mvp_drafts
               (id, tenant_id, case_id, payload)
               VALUES (%s, %s, %s, %s::jsonb)
               ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload""",
            (draft.draft_id, tenant_id, draft.case_id, _json(draft.as_dict())),
        )

    def save_decision(self, tenant_id: str, decision: dict[str, Any]) -> None:
        """Persiste una decisión humana inmutable para el hash exacto."""
        self._execute(
            tenant_id,
            """INSERT INTO public.cl_mvp_decisions
               (id, tenant_id, case_id, draft_id, payload)
               VALUES (%s, %s, %s, %s, %s::jsonb)""",
            (decision["decision_id"], tenant_id, decision["case_id"],
             decision["draft_id"], _json(decision)),
        )

    def save_audit(self, tenant_id: str, event: dict[str, Any]) -> None:
        """Persiste un evento de auditoría sin permitir actualización posterior."""
        self._execute(
            tenant_id,
            """INSERT INTO public.cl_mvp_audit_events
               (id, tenant_id, case_id, event, payload, created_at)
               VALUES (%s, %s, %s, %s, %s::jsonb, %s::timestamptz)""",
            (event["event_id"], tenant_id, event.get("case_id"), event["event"],
             _json(event), event["created_at"]),
        )

    def load_search(self, tenant_id: str, search_id: str
                    ) -> tuple[str, SearchSnapshot] | None:
        """Recupera una investigación del tenant y reconstruye su contrato."""
        row = self._fetchone(
            tenant_id,
            "SELECT case_id, payload FROM public.cl_mvp_searches WHERE id = %s",
            (search_id,),
        )
        if not row:
            return None
        return str(row["case_id"]), search_from_dict(row["payload"])

    def load_draft(self, tenant_id: str, draft_id: str) -> Draft | None:
        """Recupera un borrador del tenant y reconstruye sus objetos tipados."""
        row = self._fetchone(
            tenant_id,
            "SELECT payload FROM public.cl_mvp_drafts WHERE id = %s",
            (draft_id,),
        )
        return draft_from_dict(row["payload"]) if row else None

    def load_decisions(self, tenant_id: str, case_id: str,
                       draft_id: str) -> list[dict[str, Any]]:
        """Recupera todas las decisiones del borrador para el gate de hash."""
        rows = self._fetchall(
            tenant_id,
            """SELECT payload FROM public.cl_mvp_decisions
               WHERE case_id = %s AND draft_id = %s ORDER BY creado_en DESC, id DESC""",
            (case_id, draft_id),
        )
        return [dict(row["payload"]) for row in rows]


def _json(value: Any) -> str:
    """Serializa JSON preservando UTF-8 y evitando objetos no contractuales."""
    import json
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def citation_from_dict(raw: dict[str, Any]) -> Citation:
    """Reconstruye una cita persistida."""
    numeric = raw.get("numeric_validation") or {}
    return Citation(
        uid=str(raw.get("uid") or ""), statement=str(raw.get("statement") or ""),
        source_url=raw.get("source_url"), fragment=str(raw.get("fragment") or ""),
        source_sha256=raw.get("source_sha256"), vigencia=str(raw.get("vigencia") or "NO_MEDIDO"),
        numeric_validation=NumericValidation(
            status=str(numeric.get("status") or "not_measured"),
            expected=numeric.get("expected"), observed=numeric.get("observed"),
            method=numeric.get("method")),
        page_or_location=raw.get("page_or_location"),
    )


def search_from_dict(raw: dict[str, Any]) -> SearchSnapshot:
    """Reconstruye una investigación persistida sin reconsultar el Corpus."""
    return SearchSnapshot(
        query=str(raw.get("query") or ""), engine=str(raw.get("engine") or "bm25"),
        workflow_version=str(raw.get("workflow_version") or ""),
        allowed_citations=tuple(citation_from_dict(item)
                                for item in raw.get("allowed_citations", [])),
        unread_candidates=tuple(raw.get("unread_candidates", [])),
        invalidated_precedents=tuple(raw.get("invalidated_precedents", [])),
        answer_state=str(raw.get("answer_state") or "abstain"),
        evidence_ids=tuple(str(item) for item in raw.get("evidence_ids", [])),
        graph_context=tuple(str(item) for item in raw.get("graph_context", [])),
        retrieval_scope=str(raw.get("retrieval_scope") or "top_k"),
    )


def draft_from_dict(raw: dict[str, Any]) -> Draft:
    """Reconstruye un borrador persistido listo para verificar/exportar."""
    workflow_raw = raw.get("workflow") or {}
    workflow = Workflow(
        version=str(workflow_raw.get("version") or ""),
        materia=str(workflow_raw.get("materia") or ""),
        jurisdiccion=str(workflow_raw.get("jurisdiccion") or ""),
        roles=tuple(workflow_raw.get("roles", ())),
        pack_id=workflow_raw.get("pack_id"),
        steps=tuple(workflow_raw.get("steps", ())),
    )
    return Draft(
        draft_id=str(raw.get("draft_id") or ""), case_id=str(raw.get("case_id") or ""),
        content=str(raw.get("content") or ""),
        content_sha256=str(raw.get("content_sha256") or ""), workflow=workflow,
        search=search_from_dict(raw.get("search") or {}), deadline=raw.get("deadline"),
        warnings=tuple(str(item) for item in raw.get("warnings", [])),
    )
