#!/usr/bin/env python3
"""Mide rollback de negocio+auditoría cuando muere el backend SQL."""
from __future__ import annotations

import hashlib
import os
import sys
import threading
import time
import uuid

import psycopg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mvp_contract import Citation, Draft, NumericValidation, SearchSnapshot, Workflow
from mvp_persistence import MVPRepository, MVPPersistenceError

ADMIN_DSN = os.environ["DATABASE_URL"]
APP_DSN = os.environ["DATABASE_URL_APP"]
TENANT_ID = str(uuid.uuid4())
CASE_ID = str(uuid.uuid4())
DRAFT_ID = "txn-abort-draft"
DECISION_ID = "txn-abort-decision"
errors: list[Exception] = []


def admin(sql: str, args: tuple = ()) -> None:
    """Ejecuta una sentencia con el administrador de PostgreSQL."""
    with psycopg.connect(ADMIN_DSN, autocommit=True) as connection:
        connection.execute(sql, args)


def count(table: str) -> int:
    """Cuenta evidencia de la fixture."""
    with psycopg.connect(ADMIN_DSN) as connection:
        return connection.execute(f"SELECT count(*) FROM public.{table} WHERE tenant_id = %s",
                                  (TENANT_ID,)).fetchone()[0]


def install_pause() -> None:
    """Pausa el INSERT de decisiones sólo durante esta prueba efímera."""
    admin("""CREATE OR REPLACE FUNCTION public.test_hold_mvp_decision()
              RETURNS trigger LANGUAGE plpgsql AS $$
              BEGIN PERFORM pg_sleep(30); RETURN NEW; END $$""")
    admin("DROP TRIGGER IF EXISTS test_hold_mvp_decision ON public.cl_mvp_decisions")
    admin("""CREATE TRIGGER test_hold_mvp_decision
              AFTER INSERT ON public.cl_mvp_decisions
              FOR EACH ROW EXECUTE FUNCTION public.test_hold_mvp_decision()""")


def remove_pause() -> None:
    """Retira la inyección experimental."""
    admin("DROP TRIGGER IF EXISTS test_hold_mvp_decision ON public.cl_mvp_decisions")
    admin("DROP FUNCTION IF EXISTS public.test_hold_mvp_decision()")


def active_pid() -> int:
    """Encuentra el backend que está ejecutando el INSERT real."""
    for _ in range(120):
        with psycopg.connect(ADMIN_DSN) as connection:
            row = connection.execute(
                """SELECT pid FROM pg_stat_activity
                   WHERE datname = current_database() AND state = 'active'
                     AND query ILIKE '%cl_mvp_decisions%'
                     AND pid <> pg_backend_pid() LIMIT 1""").fetchone()
        if row:
            print(f"EVENTO backend SQL activo: {row[0]}", flush=True)
            return int(row[0])
        time.sleep(.25)
    raise RuntimeError("no se observó el INSERT persistente activo")


def make_draft() -> Draft:
    """Construye un borrador válido para el contrato persistente."""
    citation = Citation("txn-law", "regla", "https://fuente.example/txn", "Artículo 90",
                        "a" * 64, "VIGENTE", NumericValidation("not_applicable"))
    snapshot = SearchSnapshot("regla", "bm25", "txn-test-1",
                              allowed_citations=(citation,), answer_state="grounded",
                              evidence_ids=(citation.uid,))
    content = "Borrador persistente de prueba"
    return Draft(DRAFT_ID, CASE_ID, content, hashlib.sha256(content.encode()).hexdigest(),
                 Workflow("txn-test-1", "civil", "Tarija"), snapshot,
                 {"estado": "CONFIRMADO"}, ())


def main() -> int:
    """Corta una transacción real y comprueba rollback y reintento."""
    repo = MVPRepository(APP_DSN)
    draft = make_draft()
    decision = {
        "decision_id": DECISION_ID, "tenant_id": TENANT_ID, "case_id": CASE_ID,
        "draft_id": DRAFT_ID, "content_sha256": draft.content_sha256,
        "user_id": "txn-user", "role": "socio", "matricula": "MAT-TXN",
        "decision": "aprobado", "fundamento": "medición",
        "created_at": "2026-09-28T00:00:00+00:00",
    }
    event = {"event_id": "txn-abort-audit", "event": "decision_humana",
             "tenant_id": TENANT_ID, "case_id": CASE_ID, "role": "verificador",
             "payload": decision, "created_at": "2026-09-28T00:00:00+00:00"}
    try:
        admin("INSERT INTO public.tenants(id, slug, nombre_bufete) VALUES (%s,%s,%s)",
              (TENANT_ID, "txn-abort-" + TENANT_ID[:8], "Txn Abort"))
        admin("INSERT INTO public.cases(id, tenant_id, juzgado, materia, nro_expediente) VALUES (%s,%s,'J','civil','TXN-ABORT')",
              (CASE_ID, TENANT_ID))
        repo.save_draft(TENANT_ID, draft)
        install_pause()
        worker = threading.Thread(target=lambda: _save(repo, TENANT_ID, decision, event), daemon=True)
        worker.start()
        pid = active_pid()
        admin("SELECT pg_terminate_backend(%s)", (pid,))
        print(f"EVENTO backend SQL terminado: {pid}", flush=True)
        worker.join(timeout=35)
        print(f"ERROR CAPTURADO: {type(errors[0]).__name__}" if errors else "ERROR NO CAPTURADO", flush=True)
        ok = [0]
        ok[0] += int(bool(errors) and isinstance(errors[0], MVPPersistenceError))
        print(f"OK rollback transaccional: {ok[0] == 1}", flush=True)
        ok[0] += int(count("cl_mvp_decisions") == 0)
        print(f"OK sin decisión fantasma: {count('cl_mvp_decisions') == 0}", flush=True)
        ok[0] += int(count("cl_mvp_audit_events") == 0)
        print(f"OK sin auditoría fantasma: {count('cl_mvp_audit_events') == 0}", flush=True)
        remove_pause()
        repo.save_decision_with_audit(TENANT_ID, decision, event)
        ok[0] += int(count("cl_mvp_decisions") == 1 and count("cl_mvp_audit_events") == 1)
        print(f"OK reintento negocio+auditoría: {count('cl_mvp_decisions') == 1 and count('cl_mvp_audit_events') == 1}", flush=True)
        print(f"verdes: {ok[0]} | rojos: {4 - ok[0]}", flush=True)
        return 0 if ok[0] == 4 else 1
    finally:
        remove_pause()
        for table in ("cl_mvp_audit_events", "cl_mvp_decisions", "cl_mvp_drafts", "cases"):
            admin(f"DELETE FROM public.{table} WHERE tenant_id = %s", (TENANT_ID,))
        admin("DELETE FROM public.tenants WHERE id = %s", (TENANT_ID,))


def _save(repo: MVPRepository, tenant_id: str, decision: dict, event: dict) -> None:
    """Ejecuta el commit real y captura el fallo esperado del backend terminado."""
    try:
        repo.save_decision_with_audit(tenant_id, decision, event)
    except Exception as error:  # noqa: BLE001
        errors.append(error)


if __name__ == "__main__":
    raise SystemExit(main())
