#!/usr/bin/env python3
"""Mide rollback de un commit SQL negocio+auditoría sin HTTP.

La transacción de aplicación se abre con el rol `custos_app`, se pausa en un
trigger efímero durante el INSERT de la decisión y el administrador termina el
backend SQL. El resultado válido exige error, cero filas parciales y reintento
completo posterior.
"""
from __future__ import annotations

import hashlib
import os
import threading
import time
import uuid

import psycopg

ADMIN_DSN = os.environ["DATABASE_URL"]
APP_DSN = os.environ["DATABASE_URL_APP"]
TENANT_ID = str(uuid.uuid4())
CASE_ID = str(uuid.uuid4())
DRAFT_ID = "txn-direct-draft"
DECISION_ID = "txn-direct-decision"
AUDIT_ID = "txn-direct-audit"
errors: list[BaseException] = []


def admin(sql: str, args: tuple = ()) -> None:
    """Ejecuta una sentencia con la conexión administradora."""
    with psycopg.connect(ADMIN_DSN, autocommit=True) as connection:
        connection.execute(sql, args)


def count(table: str) -> int:
    """Cuenta filas de la fixture sintética."""
    with psycopg.connect(ADMIN_DSN) as connection:
        return connection.execute(
            f"SELECT count(*) FROM public.{table} WHERE tenant_id = %s",
            (TENANT_ID,)).fetchone()[0]


def install_pause() -> None:
    """Pausa el INSERT de decisión en la base efímera."""
    admin("""CREATE OR REPLACE FUNCTION public.test_hold_txn_direct()
              RETURNS trigger LANGUAGE plpgsql AS $$
              BEGIN PERFORM pg_sleep(30); RETURN NEW; END $$""")
    admin("DROP TRIGGER IF EXISTS test_hold_txn_direct ON public.cl_mvp_decisions")
    admin("""CREATE TRIGGER test_hold_txn_direct
              AFTER INSERT ON public.cl_mvp_decisions
              FOR EACH ROW EXECUTE FUNCTION public.test_hold_txn_direct()""")


def remove_pause() -> None:
    """Retira el trigger efímero."""
    admin("DROP TRIGGER IF EXISTS test_hold_txn_direct ON public.cl_mvp_decisions")
    admin("DROP FUNCTION IF EXISTS public.test_hold_txn_direct()")


def active_pid() -> int:
    """Encuentra el backend de la transacción SQL pausada."""
    for _ in range(120):
        with psycopg.connect(ADMIN_DSN) as connection:
            rows = connection.execute(
                """SELECT pid, query FROM pg_stat_activity
                   WHERE datname = current_database()
                     AND state = 'active'
                     AND pid <> pg_backend_pid()
                     AND query ILIKE '%cl_mvp_decisions%'
                     AND query NOT ILIKE '%pg_stat_activity%'
                   ORDER BY query_start DESC""").fetchall()
        if rows:
            print(f"EVENTO backend SQL activo: {rows[0][0]}", flush=True)
            print(f"EVENTO consulta observada: {rows[0][1][:120]}", flush=True)
            return int(rows[0][0])
        time.sleep(.25)
    raise RuntimeError("no se observó el backend SQL pausado")


def app_transaction(decision: dict, audit: dict) -> None:
    """Ejecuta exactamente el commit negocio+auditoría y captura su caída."""
    try:
        with psycopg.connect(APP_DSN) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT app.set_tenant(%s)", (TENANT_ID,))
                cursor.execute(
                    """INSERT INTO public.cl_mvp_decisions
                       (id, tenant_id, case_id, draft_id, content_sha256,
                        actor_user_id, actor_role, matricula, decision,
                        fundamento, payload)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)""",
                    (decision["decision_id"], decision["tenant_id"],
                     decision["case_id"], decision["draft_id"],
                     decision["content_sha256"], decision["user_id"],
                     decision["role"], decision["matricula"],
                     decision["decision"], decision["fundamento"],
                     json_payload(decision)),
                )
                cursor.execute(
                    """INSERT INTO public.cl_mvp_audit_events
                       (id, tenant_id, case_id, event, payload, created_at)
                       VALUES (%s,%s,%s,%s,%s::jsonb,%s::timestamptz)""",
                    (audit["event_id"], audit["tenant_id"], audit["case_id"],
                     audit["event"], json_payload(audit), audit["created_at"]),
                )
    except BaseException as error:  # noqa: BLE001
        errors.append(error)


def json_payload(value: dict) -> str:
    """Serializa el payload sin perder el contrato tipado."""
    import json
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def cleanup() -> None:
    """Elimina sólo la fixture después de la medición."""
    remove_pause()
    for table in ("cl_mvp_audit_events", "cl_mvp_decisions", "cl_mvp_drafts", "cases"):
        admin(f"DELETE FROM public.{table} WHERE tenant_id = %s", (TENANT_ID,))
    admin("DELETE FROM public.tenants WHERE id = %s", (TENANT_ID,))


def main() -> int:
    """Prepara, interrumpe, verifica rollback y reintenta el commit."""
    content = "Borrador de transacción SQL directa"
    digest = hashlib.sha256(content.encode()).hexdigest()
    decision = {
        "decision_id": DECISION_ID, "tenant_id": TENANT_ID, "case_id": CASE_ID,
        "draft_id": DRAFT_ID, "content_sha256": digest, "user_id": "txn-user",
        "role": "socio", "matricula": "MAT-TXN", "decision": "aprobado",
        "fundamento": "medición directa",
    }
    audit = {"event_id": AUDIT_ID, "tenant_id": TENANT_ID, "case_id": CASE_ID,
             "event": "decision_humana", "payload": decision,
             "created_at": "2026-09-28T00:00:00+00:00"}
    try:
        admin("INSERT INTO public.tenants(id, slug, nombre_bufete) VALUES (%s,%s,%s)",
              (TENANT_ID, "txn-direct-" + TENANT_ID[:8], "Txn Direct"))
        admin("""INSERT INTO public.cases(id, tenant_id, juzgado, materia, nro_expediente)
                   VALUES (%s,%s,'J','civil','TXN-DIRECT')""", (CASE_ID, TENANT_ID))
        admin("""INSERT INTO public.cl_mvp_drafts
                   (id, tenant_id, case_id, payload, content, content_sha256)
                   VALUES (%s,%s,%s,%s::jsonb,%s,%s)""",
              (DRAFT_ID, TENANT_ID, CASE_ID, json_payload({
                  "draft_id": DRAFT_ID, "case_id": CASE_ID, "content": content,
                  "content_sha256": digest}), content, digest))
        install_pause()
        worker = threading.Thread(target=app_transaction, args=(decision, audit), daemon=True)
        worker.start()
        pid = active_pid()
        terminated = admin("SELECT pg_terminate_backend(%s)", (pid,))
        print(f"EVENTO backend SQL terminado: {pid}", flush=True)
        worker.join(timeout=35)
        failed_as_expected = bool(errors) and isinstance(errors[0], psycopg.Error)
        print(f"RESULTADO interrupción capturada: {failed_as_expected}", flush=True)
        print(f"RESULTADO pg_terminate_backend: {terminated}", flush=True)
        print(f"RESULTADO decisiones tras rollback: {count('cl_mvp_decisions')}", flush=True)
        print(f"RESULTADO auditorías tras rollback: {count('cl_mvp_audit_events')}", flush=True)
        checks = [
            failed_as_expected,
            count("cl_mvp_decisions") == 0,
            count("cl_mvp_audit_events") == 0,
        ]
        remove_pause()
        with psycopg.connect(APP_DSN) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT app.set_tenant(%s)", (TENANT_ID,))
                cursor.execute(
                    """INSERT INTO public.cl_mvp_decisions
                       (id, tenant_id, case_id, draft_id, content_sha256,
                        actor_user_id, actor_role, matricula, decision,
                        fundamento, payload)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)""",
                    (decision["decision_id"], decision["tenant_id"], decision["case_id"],
                     decision["draft_id"], decision["content_sha256"], decision["user_id"],
                     decision["role"], decision["matricula"], decision["decision"],
                     decision["fundamento"], json_payload(decision)),
                )
                cursor.execute(
                    """INSERT INTO public.cl_mvp_audit_events
                       (id, tenant_id, case_id, event, payload, created_at)
                       VALUES (%s,%s,%s,%s,%s::jsonb,%s::timestamptz)""",
                    (audit["event_id"], audit["tenant_id"], audit["case_id"],
                     audit["event"], json_payload(audit), audit["created_at"]),
                )
        checks.extend([count("cl_mvp_decisions") == 1, count("cl_mvp_audit_events") == 1])
        print(f"CHECKS: {sum(checks)}/{len(checks)}", flush=True)
        return 0 if all(checks) else 1
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
