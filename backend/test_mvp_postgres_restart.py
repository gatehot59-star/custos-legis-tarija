#!/usr/bin/env python3
"""Mide el flujo MVP HTTP cuando PostgreSQL cae y vuelve.

La prueba no usa SQLite ni sesiones inyectadas. Levanta el servidor HTTP real
con PostgresAlmacen, detiene el contenedor de PostgreSQL entre pasos, observa
la respuesta del flujo y luego lo vuelve a arrancar y reintenta.
"""
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
PASSWORD = "restart-only-" + uuid.uuid4().hex[:10]
TENANT_ID = str(uuid.uuid4())
USER_ID = str(uuid.uuid4())
SLUG = "restart-" + uuid.uuid4().hex[:10]
EMAIL = "restart@example.invalid"

failures: list[str] = []
checks = 0
stopped = False


class CorpusFixture:
    """Fuente legal sintética válida para no depender del Corpus cerrado."""

    def buscar(self, query: str, limit: int = 10, offset: int = 0) -> dict:
        """Devuelve una cita vigente con validación numérica explícita."""
        return {"total_pasajes": 1, "resultados": [{
            "uid": "restart-ley-439",
            "afirmacion": "El plazo es de 10 días.",
            "pasaje": "Artículo 90: el plazo es de 10 días.",
            "fuente_url": "https://fuente.example/restart-ley-439",
            "sha256": "a" * 64,
            "vigencia": "VIGENTE",
            "validacion_numerica": {"status": "validated", "expected": "10",
                                    "observed": "10", "method": "fixture"},
        }]}


def check(name: str, actual, expected) -> None:
    """Registra una medición y conserva la salida completa para CI."""
    global checks
    checks += 1
    if actual == expected:
        print(f"OK   {name}: {actual!r}", flush=True)
    else:
        failures.append(f"{name}: obtenido {actual!r}, esperado {expected!r}")
        print(f"ROJO {name}: obtenido {actual!r}, esperado {expected!r}", flush=True)


def request(port: int, method: str, path: str, body: object | None = None,
            token: str | None = None) -> tuple[int, dict]:
    """Hace una petición HTTP real y devuelve status y JSON de error o éxito."""
    raw = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}",
                                 data=raw, method=method)
    if raw is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        try:
            return error.code, json.loads(error.read())
        except Exception:
            return error.code, {}
    except Exception as error:  # pragma: no cover - la suite lo hace visible
        return 599, {"error": f"cliente HTTP: {type(error).__name__}: {error}"}


def admin_execute(sql: str, args: tuple = ()) -> None:
    """Ejecuta una instrucción con el administrador del CI."""
    with psycopg.connect(ADMIN_DSN, autocommit=True) as connection:
        connection.execute(sql, args)


def wait_for_postgres() -> None:
    """Espera hasta que PostgreSQL acepte conexiones después del arranque."""
    last_error = ""
    for _ in range(40):
        try:
            with psycopg.connect(ADMIN_DSN, connect_timeout=1) as connection:
                connection.execute("SELECT 1")
            return
        except Exception as error:  # noqa: BLE001
            last_error = f"{type(error).__name__}: {error}"
            time.sleep(0.25)
    raise RuntimeError(f"PostgreSQL no volvió a aceptar conexiones: {last_error}")


def stop_postgres() -> None:
    """Interrumpe deliberadamente la base antes de una petición HTTP."""
    global stopped
    subprocess.run(["docker", "stop", PG_CONTAINER_ID], check=True,
                   capture_output=True, text=True)
    stopped = True
    print("EVENTO PostgreSQL detenido antes de la petición", flush=True)


def start_postgres() -> None:
    """Arranca la misma instancia y espera disponibilidad real."""
    global stopped
    subprocess.run(["docker", "start", PG_CONTAINER_ID], check=True,
                   capture_output=True, text=True)
    wait_for_postgres()
    stopped = False
    print("EVENTO PostgreSQL reiniciado y aceptando conexiones", flush=True)


def seed() -> None:
    """Crea un tenant y abogado sintéticos con el rol de aplicación."""
    admin_execute(
        "INSERT INTO public.tenants(id, slug, nombre_bufete) VALUES (%s,%s,%s)",
        (TENANT_ID, SLUG, "Estudio PostgreSQL Restart"),
    )
    admin_execute(
        "INSERT INTO public.users(id, tenant_id, email, password_hash, "
        "nombre_completo, rol, matricula_cab) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (USER_ID, TENANT_ID, EMAIL, AL.hash_password(PASSWORD),
         "Abogado de prueba", "socio", "MAT-RESTART"),
    )


def cleanup() -> None:
    """Borra sólo las filas sintéticas después de conservar el resultado."""
    if stopped:
        start_postgres()
    for table in (
        "cl_mvp_audit_events", "cl_mvp_decisions", "cl_mvp_drafts",
        "cl_mvp_searches", "cl_mvp_documents", "cases", "users",
    ):
        admin_execute(f"DELETE FROM public.{table} WHERE tenant_id = %s",
                      (TENANT_ID,))
    admin_execute("DELETE FROM public.tenants WHERE id = %s", (TENANT_ID,))


def main() -> int:
    """Corre el flujo y mide caída, respuesta y recuperación."""
    server = None
    try:
        seed()
        app = API.App(almacen=AL.PostgresAlmacen(APP_DSN), corpus=CorpusFixture())
        server = SERVER.servir_con_mvp(app, "127.0.0.1", 0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_address[1]

        status, login = request(port, "POST", "/sesion",
                                {"bufete": SLUG, "email": EMAIL,
                                 "password": PASSWORD})
        check("login antes de la caída", status, 200)
        token = login.get("token")
        check("token real antes de la caída", bool(token), True)

        status, case = request(port, "POST", "/casos", {
            "nro_expediente": "RESTART-001/2026",
            "juzgado": "Juzgado de prueba", "materia": "civil",
        }, token=token)
        check("caso antes de la caída", status, 201)
        case_id = case.get("id")

        encoded = base64.b64encode(b"notificacion sintetica").decode()
        status, document = request(port, "POST", "/mvp/documentos", {
            "case_id": case_id, "filename": "notificacion.pdf",
            "contenido_base64": encoded,
        }, token=token)
        check("documento HTTP persistido antes de la caída", status, 201)
        check("hash del documento", len(document.get("documento", {}).get("sha256", "")), 64)

        status, research = request(port, "POST", "/mvp/investigaciones", {
            "case_id": case_id, "query": "artículo 90",
        }, token=token)
        check("investigación HTTP persistida antes de la caída", status, 201)
        search_id = research.get("search_id")

        status, draft = request(port, "POST", "/mvp/borradores", {
            "case_id": case_id, "search_id": search_id, "materia": "civil",
            "deadline": {"estado": "CONFIRMADO"},
        }, token=token)
        check("borrador HTTP persistido antes de la caída", status, 201)
        draft_id = draft.get("borrador", {}).get("draft_id")

        status, verification = request(port, "POST",
                                       f"/mvp/borradores/{draft_id}/verificar",
                                       {"case_id": case_id}, token=token)
        check("verificación antes de la caída", status, 200)
        check("borrador válido antes de la caída",
              verification.get("verificacion", {}).get("ok"), True)

        stop_postgres()
        status, failed_decision = request(
            port, "POST", f"/mvp/borradores/{draft_id}/decision",
            {"case_id": case_id, "decision": "aprobado"}, token=token)
        check("decisión durante PostgreSQL detenido devuelve 503", status, 503)
        check("la caída se informa como persistencia no disponible",
              "persistencia MVP no disponible" in failed_decision.get("error", ""), True)

        start_postgres()
        status, decision = request(
            port, "POST", f"/mvp/borradores/{draft_id}/decision",
            {"case_id": case_id, "decision": "aprobado",
             "fundamento": "revisado después del reinicio"}, token=token)
        check("decisión reintentada después del reinicio", status, 201)
        decision_hash = decision.get("decision", {}).get("content_sha256")
        check("decisión conserva hash exacto", len(decision_hash or ""), 64)

        stop_postgres()
        status, failed_export = request(
            port, "POST", f"/mvp/borradores/{draft_id}/exportar",
            {"case_id": case_id}, token=token)
        check("exportación durante PostgreSQL detenido devuelve 503", status, 503)
        check("exportación caída conserva error controlado",
              "persistencia MVP no disponible" in failed_export.get("error", ""), True)

        start_postgres()
        status, exported = request(
            port, "POST", f"/mvp/borradores/{draft_id}/exportar",
            {"case_id": case_id}, token=token)
        check("DOCX reintentado después del reinicio", status, 200)
        raw_docx = base64.b64decode(exported.get("content_base64", ""))
        check("DOCX conserva hash de descarga", exported.get("content_sha256"),
              hashlib.sha256(raw_docx).hexdigest())
        print("RESULTADO PostgreSQL: caída controlada en 2 puntos, 503 explícito "
              "y recuperación por reintento; no se perdió el expediente", flush=True)
    finally:
        if server is not None:
            server.shutdown()
        try:
            cleanup()
        except Exception as error:  # pragma: no cover - queda visible como rojo
            failures.append(f"limpieza: {type(error).__name__}: {error}")
            print(f"ROJO limpieza: {failures[-1]}", flush=True)

    print(f"verdes: {checks} | rojos: {len(failures)}", flush=True)
    for failure in failures:
        print("  ROJO: " + failure, flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
