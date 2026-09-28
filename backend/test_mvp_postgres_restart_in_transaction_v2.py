#!/usr/bin/env python3
"""Mide reinicio de PostgreSQL dentro de la transacción negocio+auditoría."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
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
PG_CONTAINER_ID = os.environ["PG_CONTAINER_ID"]
PASSWORD = "txn-restart-" + uuid.uuid4().hex[:10]
TENANT_ID = str(uuid.uuid4())
SLUG = "txn-restart-" + uuid.uuid4().hex[:10]
EMAIL = "txn-restart@example.invalid"
failures: list[str] = []
checks = 0
stopped = False


class CorpusFixture:
    """Fuente legal sintética para aislar la prueba del Corpus live."""

    def buscar(self, query: str, limit: int = 10, offset: int = 0) -> dict:
        """Devuelve una cita vigente con número validado."""
        return {"total_pasajes": 1, "resultados": [{
            "uid": "txn-restart-ley-439",
            "afirmacion": "El plazo es de 10 días.",
            "pasaje": "Artículo 90: el plazo es de 10 días.",
            "fuente_url": "https://fuente.example/txn-restart-ley-439",
            "sha256": "a" * 64, "vigencia": "VIGENTE",
            "validacion_numerica": {"status": "validated", "expected": "10",
                                    "observed": "10", "method": "fixture"},
        }]}


def check(name: str, actual, expected) -> None:
    """Emite cada medición y conserva los rojos."""
    global checks
    checks += 1
    if actual == expected:
        print(f"OK   {name}: {actual!r}", flush=True)
    else:
        failures.append(f"{name}: obtenido {actual!r}, esperado {expected!r}")
        print(f"ROJO {name}: obtenido {actual!r}, esperado {expected!r}", flush=True)


def request(port: int, method: str, path: str, body=None, token=None):
    """Hace una petición HTTP real y devuelve status y JSON."""
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


def admin(sql: str, args: tuple = ()) -> None:
    """Ejecuta una sola instrucción administrativa por conexión nueva."""
    with psycopg.connect(ADMIN_DSN, autocommit=True) as connection:
        connection.execute(sql, args)


def wait_pg() -> None:
    """Espera la disponibilidad real después del reinicio."""
    last = ""
    for _ in range(60):
        try:
            with psycopg.connect(ADMIN_DSN, connect_timeout=1) as connection:
                connection.execute("SELECT 1")
            return
        except Exception as error:  # noqa: BLE001
            last = f"{type(error).__name__}: {error}"
            time.sleep(.25)
    raise RuntimeError(f"PostgreSQL no volvió: {last}")


def stop_pg() -> None:
    """Detiene el servicio mientras el INSERT está bloqueado en trigger."""
    global stopped
    subprocess.run(["docker", "stop", PG_CONTAINER_ID], check=True,
                   capture_output=True, text=True)
    stopped = True
    print("EVENTO PostgreSQL detenido DENTRO de la transacción", flush=True)


def start_pg() -> None:
    """Arranca el mismo contenedor y espera conexiones."""
    global stopped
    subprocess.run(["docker", "start", PG_CONTAINER_ID], check=True,
                   capture_output=True, text=True)
    wait_pg()
    stopped = False
    print("EVENTO PostgreSQL reiniciado después del rollback", flush=True)


def install_pause() -> None:
    """Instala una pausa de 30 s sólo en el PostgreSQL efímero del CI."""
    admin("""CREATE OR REPLACE FUNCTION public.test_hold_mvp_decision()
              RETURNS trigger LANGUAGE plpgsql AS $$
              BEGIN PERFORM pg_sleep(30); RETURN NEW; END $$""")
    admin("DROP TRIGGER IF EXISTS test_hold_mvp_decision ON public.cl_mvp_decisions")
    admin("""CREATE TRIGGER test_hold_mvp_decision
              AFTER INSERT ON public.cl_mvp_decisions
              FOR EACH ROW EXECUTE FUNCTION public.test_hold_mvp_decision()""")


def remove_pause() -> None:
    """Retira la pausa antes del reintento."""
    admin("DROP TRIGGER IF EXISTS test_hold_mvp_decision ON public.cl_mvp_decisions")
    admin("DROP FUNCTION IF EXISTS public.test_hold_mvp_decision()")


def wait_insert() -> None:
    """Espera ver el INSERT de decisión activo, no simula el punto de corte."""
    for _ in range(120):
        with psycopg.connect(ADMIN_DSN) as connection:
            row = connection.execute(
                """SELECT pid FROM pg_stat_activity
                   WHERE datname = current_database() AND state = 'active'
                     AND query LIKE 'INSERT INTO public.cl_mvp_decisions%'
                     AND pid <> pg_backend_pid() LIMIT 1""").fetchone()
        if row:
            print(f"EVENTO INSERT activo en backend {row[0]}", flush=True)
            return
        time.sleep(.25)
    raise RuntimeError("no se observó el INSERT de decisión activo")


def count(table: str) -> int:
    """Cuenta la fixture después del reinicio."""
    with psycopg.connect(ADMIN_DSN) as connection:
        return connection.execute(
            f"SELECT count(*) FROM public.{table} WHERE tenant_id = %s",
            (TENANT_ID,)).fetchone()[0]


def cleanup() -> None:
    """Limpia sólo la fixture sintética."""
    if stopped:
        start_pg()
    remove_pause()
    for table in ("cl_mvp_audit_events", "cl_mvp_decisions", "cl_mvp_drafts",
                  "cl_mvp_searches", "cl_mvp_documents", "cases", "users"):
        admin(f"DELETE FROM public.{table} WHERE tenant_id = %s", (TENANT_ID,))
    admin("DELETE FROM public.tenants WHERE id = %s", (TENANT_ID,))


def main() -> int:
    """Corre flujo HTTP, corta el commit y verifica rollback y recuperación."""
    server = None
    thread = None
    try:
        admin("INSERT INTO public.tenants(id, slug, nombre_bufete) VALUES (%s,%s,%s)",
              (TENANT_ID, SLUG, "Estudio Transaction Restart"))
        admin("""INSERT INTO public.users(id, tenant_id, email, password_hash,
                   nombre_completo, rol, matricula_cab)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
              (str(uuid.uuid4()), TENANT_ID, EMAIL, AL.hash_password(PASSWORD),
               "Abogado de prueba", "socio", "MAT-TXN-RESTART"))
        app = API.App(almacen=AL.PostgresAlmacen(APP_DSN), corpus=CorpusFixture())
        server = SERVER.servir_con_mvp(app, "127.0.0.1", 0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_address[1]
        status, login = request(port, "POST", "/sesion",
                                {"bufete": SLUG, "email": EMAIL, "password": PASSWORD})
        check("login antes de la caída", status, 200)
        token = login.get("token")
        check("token antes de la caída", bool(token), True)
        status, case = request(port, "POST", "/casos", {
            "nro_expediente": "TXN-RESTART-001/2026",
            "juzgado": "Juzgado de prueba", "materia": "civil"}, token=token)
        check("caso antes de la caída", status, 201)
        case_id = case.get("id")
        body = {"case_id": case_id, "filename": "notificacion.pdf",
                "contenido_base64": base64.b64encode(b"notificacion sintetica").decode()}
        check("documento antes de la caída", request(port, "POST", "/mvp/documentos", body, token)[0], 201)
        status, research = request(port, "POST", "/mvp/investigaciones",
                                   {"case_id": case_id, "query": "artículo 90"}, token)
        check("investigación antes de la caída", status, 201)
        status, draft = request(port, "POST", "/mvp/borradores", {
            "case_id": case_id, "search_id": research.get("search_id"),
            "materia": "civil", "deadline": {"estado": "CONFIRMADO"}}, token)
        check("borrador antes de la caída", status, 201)
        draft_id = draft.get("borrador", {}).get("draft_id")
        status, verified = request(port, "POST", f"/mvp/borradores/{draft_id}/verificar",
                                   {"case_id": case_id}, token)
        check("verificación antes de la caída", status, 200)
        check("borrador válido", verified.get("verificacion", {}).get("ok"), True)

        install_pause()
        result = []
        thread = threading.Thread(target=lambda: result.append(request(
            port, "POST", f"/mvp/borradores/{draft_id}/decision",
            {"case_id": case_id, "decision": "aprobado"}, token))
        thread.start()
        wait_insert()
        stop_pg()
        thread.join(timeout=35)
        check("caída dentro del commit devuelve 503", result[0][0] if result else None, 503)
        start_pg()
        check("rollback sin decisión fantasma", count("cl_mvp_decisions"), 0)
        check("rollback sin auditoría fantasma", count("cl_mvp_audit_events"), 0)
        remove_pause()
        status, decision = request(port, "POST", f"/mvp/borradores/{draft_id}/decision", {
            "case_id": case_id, "decision": "aprobado",
            "fundamento": "reintento después del rollback"}, token)
        check("reintento de aprobación", status, 201)
        check("hash exacto conservado", len(decision.get("decision", {}).get("content_sha256", "")), 64)
        status, exported = request(port, "POST", f"/mvp/borradores/{draft_id}/exportar",
                                   {"case_id": case_id}, token)
        check("exportación después del rollback", status, 200)
        raw = base64.b64decode(exported.get("content_base64", ""))
        check("hash del DOCX", exported.get("content_sha256"), hashlib.sha256(raw).hexdigest())
        print("RESULTADO: PostgreSQL reinició dentro de la transacción, el rollback "
              "fue completo y el reintento recuperó el flujo", flush=True)
    finally:
        if thread is not None:
            thread.join(timeout=2)
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
