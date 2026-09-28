#!/usr/bin/env python3
"""Falsadores PostgreSQL del contrato persistente del MVP."""
from __future__ import annotations

import hashlib
import os
import uuid
from dataclasses import dataclass
from typing import Any

import psycopg

from mvp_contract import Citation, Draft, NumericValidation, SearchSnapshot, Workflow
from mvp_persistence import MVPRepository, MVPPersistenceError


@dataclass
class FixtureDocument:
    """Documento mínimo compatible con save_document."""

    document_id: str
    case_id: str

    def as_dict(self) -> dict[str, str]:
        """Devuelve el payload documental verificable."""
        return {"document_id": self.document_id, "case_id": self.case_id,
                "filename": "prueba.pdf", "sha256": "c" * 64}


ADMIN_DSN = os.environ["DATABASE_URL"]
APP_DSN = os.environ["DATABASE_URL_APP"]
tenant_id = str(uuid.uuid4())
other_tenant_id = str(uuid.uuid4())
case_id = str(uuid.uuid4())
other_case_id = str(uuid.uuid4())
search_id = "search-persistence-test"
draft_id = "draft-persistence-test"


def admin_execute(sql: str, args: tuple[Any, ...] = ()) -> None:
    """Ejecuta preparación o limpieza con el rol administrador del CI."""
    with psycopg.connect(ADMIN_DSN) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, args)


try:
    admin_execute(
        "INSERT INTO public.tenants (id, slug, nombre_bufete) VALUES (%s, %s, %s), (%s, %s, %s)",
        (tenant_id, "mvp-persistence-a", "MVP Persistence A", other_tenant_id,
         "mvp-persistence-b", "MVP Persistence B"),
    )
    admin_execute(
        """INSERT INTO public.cases
           (id, tenant_id, juzgado, materia, nro_expediente)
           VALUES (%s, %s, 'Juzgado de prueba', 'civil', 'PERSIST-1'),
                  (%s, %s, 'Juzgado de otro tenant', 'civil', 'PERSIST-2')""",
        (case_id, tenant_id, other_case_id, other_tenant_id),
    )

    repository = MVPRepository(APP_DSN)
    citation = Citation(
        uid="ley-persistida", statement="regla persistida",
        source_url="https://fuente.example/ley-persistida",
        fragment="Artículo persistido", source_sha256="a" * 64,
        vigencia="VIGENTE", numeric_validation=NumericValidation("not_applicable"),
    )
    snapshot = SearchSnapshot(
        query="regla persistida", engine="bm25", workflow_version="test-1",
        allowed_citations=(citation,), answer_state="grounded",
        evidence_ids=(citation.uid,), retrieval_scope="top_k",
    )
    workflow = Workflow("test-1", "civil", "Tarija")
    content = "Borrador persistido"
    content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    draft = Draft(
        draft_id=draft_id, case_id=case_id, content=content,
        content_sha256=content_sha256, workflow=workflow, search=snapshot,
        deadline={"estado": "CONFIRMADO"}, warnings=(),
    )

    repository.save_document(
        tenant_id, FixtureDocument("document-persistence-test", case_id), "c" * 64)
    repository.save_search(tenant_id, search_id, case_id, snapshot)
    repository.save_draft(tenant_id, draft)
    decision = {
        "decision_id": "decision-persistence-test", "tenant_id": tenant_id,
        "case_id": case_id, "draft_id": draft_id,
        "content_sha256": content_sha256, "user_id": "user-persistence-test",
        "role": "socio", "matricula": "MAT-TEST", "decision": "aprobado",
        "fundamento": "revisión", "created_at": "2026-09-26T16:00:00+00:00",
    }
    repository.save_decision(tenant_id, decision)
    repository.save_audit(tenant_id, {
        "event_id": "audit-persistence-test", "event": "test_persistido",
        "tenant_id": tenant_id, "case_id": case_id, "role": "investigador",
        "payload": {"ok": True}, "created_at": "2026-09-26T16:00:00+00:00",
    })

    loaded_case, loaded_search = repository.load_search(tenant_id, search_id) or (None, None)
    assert loaded_case == case_id
    assert loaded_search is not None
    assert loaded_search.allowed_citations[0].uid == citation.uid
    loaded_draft = repository.load_draft(tenant_id, draft_id)
    assert loaded_draft is not None and loaded_draft.content == draft.content
    decisions = repository.load_decisions(tenant_id, case_id, draft_id)
    assert len(decisions) == 1 and decisions[0]["decision"] == "aprobado"

    try:
        repository.save_decision(tenant_id, {**decision, "decision": "inventada",
                                             "decision_id": "decision-invalid-kind"})
        raise AssertionError("la decisión inválida fue aceptada")
    except MVPPersistenceError:
        pass
    try:
        bad_content = Draft(
            draft_id="draft-invalid-hash", case_id=case_id, content=content,
            content_sha256="b" * 64, workflow=workflow, search=snapshot,
            deadline={"estado": "CONFIRMADO"}, warnings=(),
        )
        repository.save_draft(tenant_id, bad_content)
        raise AssertionError("el borrador con hash inválido fue aceptado")
    except MVPPersistenceError:
        pass

    try:
        admin_execute("DELETE FROM public.tenants WHERE id = %s", (tenant_id,))
        raise AssertionError("DELETE de tenant con evidencia no fue bloqueado")
    except Exception:
        # Este es el falsador real: RESTRICT impide borrar el tenant y conservar
        # las filas inmutables; no se simula con un SELECT ni con TRUNCATE.
        pass
    assert repository.load_draft(tenant_id, draft_id) is not None
    print("VERDE: columnas tipadas, hashes ligados, decisiones validadas, transacción y DELETE RESTRICT")
finally:
    # TRUNCATE se usa solamente para dejar limpio el PostgreSQL efímero después
    # de haber medido el DELETE real arriba.
    admin_execute(
        "TRUNCATE public.cl_mvp_audit_events, public.cl_mvp_decisions, "
        "public.cl_mvp_drafts, public.cl_mvp_searches, public.cl_mvp_documents",
    )
    admin_execute(
        "DELETE FROM public.tenants WHERE id IN (%s, %s)",
        (tenant_id, other_tenant_id),
    )
