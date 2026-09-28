#!/usr/bin/env python3
"""Mide rollback real al terminar el backend durante un commit MVP.

No usa SQLite ni mocks del repositorio. Un trigger efímero pausa el INSERT de
la decisión, la sesión administradora identifica el backend SQL activo y lo
termina con pg_terminate_backend. Después se verifica que negocio y auditoría
no dejaron filas, y que el reintento completo funciona.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid

import psycopg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import almacen as AL  # noqa: E402
import api as API  # noqa: E402
import mvp_server as SERVER  # noqa: E402

ADMIN_DSN = os.environ["DATABASE_URL"]
APP_DSN = os.environ["DATABASE_URL_APP"]
TENANT_ID = str(uuid.uuid4())
SLUG = "txn-abort-" + uuid.uuid4().hex[:10]
EMAIL = "txn-abort@example.invalid"
PASSWORD = "txn-abort-" + uuid.uuid4().hex[:10]
failures: list[str] = []
checks = 0


class CorpusFixture:
    """Fuente legal sintética válida."""

    def buscar(self, query: str, limit: int = 10, offset: int = 0) -> dict:
        """Devuelve una cita vigente y numéricamente validada."""
        return {"total_pasajes": 1, "resultados": [{
            "uid": "txn-abort-ley-439", "afirmacion": "El plazo es de 10 días.",
            "pasaje": "Artículo 90: el plazo es de 10 días.",
            "fuente_url": "https://fuente.example/txn-abort-ley-439",
            "sha256": "a" * 64, "vigencia": "VIGENTE",
            "validacion_numerica": {"status": "validated", "expected": "10",
                                    "observed": "10", "method": "fixture"},
        }]}


def check(name: str, actual, expected) -> None:
    """Registra cada resultado del instrumento."""
    global checks
    checks += 1
    if actual == expected:
        print(f"OK   {name}: {actual!r}", flush=True)
    else:
        failures.append(f"{name}: obtenido {actual!r}, esperado {expected!r}")
        print(f"ROJO {name}: obtenido {actual!r}, esperado {expected!r}", flush=True)


def admin(sql: str, args: tuple = ()) -> None:
    """Ejecuta una sentencia con la sesión administradora."""
    with psycopg.connect(ADMIN_DSN, autocommit=True) as connection:
        connection.execute(sql, args)


def request(port: int, method: str, path: str, body=None, token=None):
    """Hace una petición HTTP real."""
    raw = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=raw, method=method)
    if raw is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        try:
            return error.code, json.loads(error.read())
        except Exception:
            return error.code, {}
    except Exception as error:  # pragma: no cover
        return 599, {"error": f"cliente HTTP: {type(error).__name__}: {error}"}


def install_pause() -> None:
    """Pausa el INSERT sólo en esta base efímera."""
    admin("""CREATE OR REPLACE FUNCTION public.test_hold_mvp_decision()
              RETURNS trigger LANGUAGE plpgsql AS $$
              BEGIN PERFORM pg_sleep(30); RETURN NEW; END $$""")
    admin("DROP TRIGGER IF EXISTS test_hold_mvp_decision ON public.cl_mvp_decisions")
    admin("""CREATE TRIGGER test_hold_mvp_decision
              AFTER INSERT ON public.cl_mvp_decisions
              FOR EACH ROW EXECUTE FUNCTION public.test_hold_mvp_decision()""")


def remove_pause() -> None:
    """Retira el trigger efímero."""
    admin("DROP TRIGGER IF EXISTS test_hold_mvp_decision ON public.cl_mvp_decisions")
    admin("DROP FUNCTION IF EXISTS public.test_hold_mvp_decision()")


def active_decision_backend() -> int:
    """Encuentra el backend que ejecuta el INSERT pausado."""
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
    raise RuntimeError("no se observó el backend SQL de la decisión")


def count(table: str) -> int:
    """Cuenta filas de la fixture en PostgreSQL real."""
    with psycopg.connect(ADMIN_DSN) as connection:
        return connection.execute(f"SELECT count(*) FROM public.{table} WHERE tenant_id = %s",
                                  (TENANT_ID,)).fetchone()[0]


def cleanup() -> None:
    """Limpia exclusivamente el tenant sintético."""
    remove_pause()
    for table in ("cl_mvp_audit_events", "cl_mvp_decisions", "cl_mvp_drafts",
                  "cl_mvp_searches", "cl_mvp_documents", "cases", "users"):
        admin(f"DELETE FROM public.{table} WHERE tenant_id = %s", (TENANT_ID,))
    admin("DELETE FROM public.tenants WHERE id = %s", (TENANT_ID,))


def main() -> int:
    """Corre flujo HTTP, aborta la transacción y comprueba recuperación."""
    server = None
    worker = None
    try:
        admin("INSERT INTO public.tenants(id, slug, nombre_bufete) VALUES (%s,%s,%s)",
              (TENANT_ID, SLUG, "Estudio Txn Abort"))
        admin("""INSERT INTO public.users(id, tenant_id, email, password_hash,
                   nombre_completo, rol, matricula_cab) VALUES (%s,%s,%s,%s,%s,%s,%s)""",
              (str(uuid.uuid4()), TENANT_ID, EMAIL, AL.hash_password(PASSWORD),
               "Abogado de prueba", "socio", "MAT-TXN-ABORT"))
        app = API.App(almacen=AL.PostgresAlmacen(APP_DSN), corpus=CorpusFixture())
        server = SERVER.servir_con_mvp(app, "127.0.0.1", 0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_address[1]
        status, login = request(port, "POST", "/sesion",
                                {"bufete": SLUG, "email": EMAIL, "password": PASSWORD})
        check("login", status, 200)
        token = login.get("token")
        status, case = request(port, "POST", "/casos", {
            "nro_expediente": "TXN-ABORT-001/2026", "juzgado": "Juzgado de prueba",
            "materia": "civil"}, token=token)
        check("caso", status, 201)
        case_id = case.get("id")
        document = {"case_id": case_id, "filename": "notificacion.pdf",
                    "contenido_base64": base64.b64encode(b"notificacion sintetica").decode()}
        check("documento", request(port, "POST", "/mvp/documentos", document, token)[0], 201)
        status, research = request(port, "POST", "/mvp/investigaciones",
                                   {"case_id": case_id, "query": "artículo 90"}, token)
        check("investigación", status, 201)
        status, draft = request(port, "POST", "/mvp/borradores", {
            "case_id": case_id, "search_id": research.get("search_id"), "materia": "civil",
            "deadline": {"estado": "CONFIRMADO"}}, token)
        check("borrador", status, 201)
        draft_id = draft.get("borrador", {}).get("draft_id")
        status, verified = request(port, "POST", f"/mvp/borradores/{draft_id}/verificar",
                                   {"case_id": case_id}, token)
        check("verificación", status, 200)
        check("borrador válido", verified.get("verificacion", {}).get("ok"), True)

        install_pause()
        result = []
        worker = threading.Thread(target=lambda: result.append(request(
            port, "POST", f"/mvp/borradores/{draft_id}/decision",
            {"case_id": case_id, "decision": "aprobado"}, token))
        worker.start()
        pid = active_decision_backend()
        terminated = admin("SELECT pg_terminate_backend(%s)", (pid,))
        print(f"EVENTO backend SQL terminado: {pid}", flush=True)
        worker.join(timeout=35)
        check("backend terminado dentro del commit devuelve 503", result[0][0] if result else None, 503)
        check("pg_terminate_backend confirmó la interrupción", terminated, None)
        check("rollback sin decisión fantasma", count("cl_mvp_decisions"), 0)
        check("rollback sin auditoría fantasma", count("cl_mvp_audit_events"), 0)
        remove_pause()
        status, decision = request(port, "POST", f"/mvp/borradores/{draft_id}/decision", {
            "case_id": case_id, "decision": "aprobado", "fundamento": "reintento después del rollback"}, token)
        check("reintento de aprobación", status, 201)
        check("hash exacto", len(decision.get("decision", {}).get("content_sha256", "")), 64)
        status, exported = request(port, "POST", f"/mvp/borradores/{draft_id}/exportar",
                                   {"case_id": case_id}, token)
        check("exportación después del rollback", status, 200)
        raw = base64.b64decode(exported.get("content_base64", ""))
        check("hash del DOCX", exported.get("content_sha256"), hashlib.sha256(raw).hexdigest())
        print("RESULTADO: backend SQL terminado durante la transacción, rollback "
              "completo y reintento OK", flush=True)
    except Exception as error:  # pragma: no cover
        failures.append(f"excepción del instrumento: {type(error).__name__}: {error}")
        print("TRACEBACK DEL INSTRUMENTO", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        if worker is not None:
            worker.join(timeout=2)
        if server is not None:
            server.shutdown()
        try:
            cleanup()
        except Exception as error:  # pragma: no cover
            failures.append(f"limpieza: {type(error).__name__}: {error}")
            print(f"ROJO limpieza: {failures[-1]}", flush=True)
    print(f"verdes: {checks} | rojos: {len(failures)}", flush=True)
    for failure in failures:
        print("  ROJO: " + failure, flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
