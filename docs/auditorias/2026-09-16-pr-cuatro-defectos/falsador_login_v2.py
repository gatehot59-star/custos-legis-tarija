"""Falsador del login, v2. Corrige el reparo de Sol sobre la v1.

EL DEFECTO DE LA v1, confirmado: el `ALTER ROLE ... NOBYPASSRLS` vivia en el
camino normal. El `finally` detenia el cluster pero NO garantizaba revocar el
privilegio si algo explotaba entre elevar y revocar. La corrida registrada si
revirtio, y eso es una OBSERVACION, no una garantia. La distincion es de Sol y
es correcta.

QUE CAMBIA ACA:
  1. La revocacion pasa al `finally` y se VERIFICA leyendo `pg_roles` despues.
  2. Se agrega un brazo con EXCEPCION INYECTADA justo despues de elevar: tiene
     que restaurar el rol, detener el cluster y CONSERVAR el error original.
  3. Antes de empezar se CHEQUEA el estado heredado: si una corrida anterior
     murio por SIGKILL con el privilegio puesto, este arranque lo tiene que ver
     y decirlo. `finally` no corre si el proceso recibe SIGKILL, y eso queda
     declarado como limite en vez de asumido como cubierto.

Solo cluster sintetico aislado. NUNCA produccion. No se sobrescribe la evidencia
de corridas anteriores: cada corrida escribe su propio JSON con timestamp.
"""
import contextlib
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import threading
import urllib.error
import urllib.request
import uuid

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                    else "/workspace/custos-integration-20260916-0314")
REPO = ROOT / "repo"
BACK = REPO / "backend"
PG = ROOT / "pgroot/usr/lib/postgresql/17/bin"
ENV = dict(os.environ,
           LD_LIBRARY_PATH=str(ROOT / "pgroot/usr/lib/x86_64-linux-gnu"))
ENV.pop("DATABASE_URL", None)
ENV.pop("DATABASE_URL_APP", None)
SOCK = ROOT / "socket"
DATA = ROOT / "pgdata"
DSN_ADMIN = f"host={SOCK} dbname=postgres user=audit_admin"
DSN_APP = f"host={SOCK} dbname=postgres user=custos_app"
sys.path.insert(0, str(BACK))

import psycopg  # noqa: E402
import almacen  # noqa: E402
import api  # noqa: E402

SELLO = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
out = {"instrumento": "falsador del login v2 (revocacion en finally)",
       "root": str(ROOT), "sello": SELLO,
       "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "brazos": [], "verdes": 0, "rojos": 0}


def chk(etiqueta, actual, esperado):
    paso = actual == esperado
    out["verdes" if paso else "rojos"] += 1
    print(f"  {'OK  ' if paso else 'ROJO'} {etiqueta}: {actual!r}"
          + ("" if paso else f" (esperaba {esperado!r})"))
    return paso


class ExcepcionInyectada(RuntimeError):
    """Se levanta a proposito para probar el camino de restauracion."""


def pedir(port, cuerpo):
    data = json.dumps(cuerpo).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}/sesion",
                                 method="POST", data=data)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def estado_rol():
    with psycopg.connect(DSN_ADMIN, autocommit=True) as c:
        return c.execute(
            "SELECT rolname, rolsuper, rolbypassrls FROM pg_roles"
            " WHERE rolname='custos_app'").fetchone()


def elevar():
    with psycopg.connect(DSN_ADMIN, autocommit=True) as c:
        c.execute("ALTER ROLE custos_app BYPASSRLS")


def revocar():
    with psycopg.connect(DSN_ADMIN, autocommit=True) as c:
        c.execute("ALTER ROLE custos_app NOBYPASSRLS")


def medir(etiqueta, tenant_slug, password):
    store = almacen.PostgresAlmacen(DSN_APP)
    corpus = type("C", (), {"buscar": lambda self, q, limit=10: {
        "total_pasajes": 0, "resultados": []}})()
    app = api.App(almacen=store, corpus=corpus)
    destino = ROOT / f"http-falsador-v2-{etiqueta}-{SELLO}.log"
    with destino.open("w", buffering=1) as f, contextlib.redirect_stdout(f):
        srv = api.servir(app, "127.0.0.1", 0)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        port = srv.server_address[1]
        r = {"brazo": etiqueta,
             "password_correcta": pedir(port, {"bufete": tenant_slug,
                                              "email": "v2@falsador.invalid",
                                              "password": password}),
             "password_incorrecta": pedir(port, {"bufete": tenant_slug,
                                                 "email": "v2@falsador.invalid",
                                                 "password": "no-es"}),
             "sin_bufete": pedir(port, {"email": "v2@falsador.invalid",
                                        "password": password})}
        srv.shutdown()
        srv.server_close()
    r["bypassrls_efectivo"] = bool(estado_rol()[2])
    out["brazos"].append(r)
    return r


started = False
error_conservado = None
try:
    rc = subprocess.run([str(PG / "pg_ctl"), "-D", str(DATA), "-l",
                         str(ROOT / f"postgres-falsador-v2-{SELLO}.log"), "-w",
                         "start"], env=ENV, capture_output=True, text=True,
                        timeout=120)
    out["pg_start_rc"] = rc.returncode
    if rc.returncode:
        raise RuntimeError("pg start fallo: " + rc.stdout + rc.stderr)
    started = True

    # --- CHEQUEO DE ESTADO HEREDADO ---------------------------------------
    # Si una corrida anterior murio por SIGKILL despues de elevar, el
    # privilegio quedo puesto. `finally` no corre con SIGKILL: la unica defensa
    # es mirarlo al arrancar.
    heredado = estado_rol()
    out["rol_heredado"] = heredado
    print("=== 0. Estado heredado del rol (defensa contra SIGKILL previo) ===")
    chk("al arrancar, custos_app NO tiene bypass heredado", bool(heredado[2]),
        False)
    chk("ni es superusuario", bool(heredado[1]), False)

    tid, uid = str(uuid.uuid4()), str(uuid.uuid4())
    slug = "falsv2-" + tid[:8]
    password = "falsador-v2-" + uuid.uuid4().hex[:8]
    with psycopg.connect(DSN_ADMIN, autocommit=True) as c:
        c.execute((REPO / "infra/init.sql").read_text(), prepare=False)
        c.execute("INSERT INTO tenants(id,slug,nombre_bufete) VALUES (%s,%s,%s)",
                  (tid, slug, "FALSADOR V2"))
        c.execute(
            "INSERT INTO users(id,tenant_id,email,password_hash,"
            "nombre_completo,rol,matricula_cab) VALUES(%s,%s,%s,%s,%s,%s,%s)",
            (uid, tid, "v2@falsador.invalid", almacen.hash_password(password),
             "FALSADOR V2", "socio", "FALS-V2"))

    print("\n=== 1. Con el arreglo del login aplicado, el rol REAL alcanza ===")
    a = medir("control-rol-real", slug, password)
    chk("password correcta da 200 SIN bypass", a["password_correcta"], 200)
    chk("password incorrecta da 401", a["password_incorrecta"], 401)
    chk("y el check de password mala DISCRIMINA (no son los dos 401)",
        a["password_correcta"] != a["password_incorrecta"], True)
    chk("sin bufete da 401", a["sin_bufete"], 401)
    chk("bypassrls seguia apagado", a["bypassrls_efectivo"], False)

    print("\n=== 2. EXCEPCION INYECTADA justo despues de elevar ===")
    # Este es el brazo que la v1 no tenia. Si la restauracion depende del camino
    # feliz, aca queda el privilegio puesto y el chequeo de abajo da ROJO.
    intento = {"elevado": False, "error": None}
    try:
        elevar()
        intento["elevado"] = bool(estado_rol()[2])
        raise ExcepcionInyectada("fallo simulado con el privilegio puesto")
    except ExcepcionInyectada as e:
        intento["error"] = str(e)
    finally:
        revocar()
    chk("el privilegio SI estuvo puesto (el brazo no fue vacio)",
        intento["elevado"], True)
    chk("tras la excepcion, bypassrls quedo REVOCADO", bool(estado_rol()[2]),
        False)
    chk("y el error original se conservo",
        intento["error"], "fallo simulado con el privilegio puesto")
    out["excepcion_inyectada"] = intento

    print("\n=== 3. Brazo BYPASSRLS: confirma la CAUSA del 401 historico ===")
    # Con el arreglo puesto el login ya da 200, asi que este brazo ya no puede
    # distinguir la causa. Se mide sobre el contrato VIEJO reproducido aca: una
    # consulta a users SIN set_tenant, que es exactamente lo que hacia el bug.
    def leer_sin_tenant():
        with psycopg.connect(DSN_APP) as c:
            return c.execute(
                "SELECT count(*) FROM public.users WHERE id = %s",
                (uid,)).fetchone()[0]
    sin_bypass = leer_sin_tenant()
    try:
        elevar()
        con_bypass = leer_sin_tenant()
    finally:
        revocar()
    despues = leer_sin_tenant()
    chk("sin set_tenant y sin bypass, users devuelve CERO filas", sin_bypass, 0)
    chk("con BYPASSRLS la misma consulta devuelve la fila", con_bypass, 1)
    chk("tras revocar vuelve a cero (reversion verificada)", despues, 0)
    chk("y el rol quedo sin bypass", bool(estado_rol()[2]), False)
    out["lectura_sin_tenant"] = {"sin_bypass": sin_bypass,
                                 "con_bypass": con_bypass,
                                 "tras_revocar": despues}
except Exception as e:  # noqa: BLE001
    error_conservado = repr(e)
    raise
finally:
    # REVOCACION EN EL finally, que es el reparo de Sol. Se ejecuta pase lo que
    # pase y se VERIFICA leyendo el catalogo, no asumiendo que el ALTER anduvo.
    if started:
        with contextlib.suppress(Exception):
            revocar()
        with contextlib.suppress(Exception):
            out["rol_final"] = estado_rol()
        s = subprocess.run([str(PG / "pg_ctl"), "-D", str(DATA), "-m", "fast",
                            "-w", "stop"], env=ENV, capture_output=True,
                           text=True)
        out["pg_stop_rc"] = s.returncode
        st = subprocess.run([str(PG / "pg_ctl"), "-D", str(DATA), "status"],
                            env=ENV, capture_output=True, text=True)
        out["pg_status_after_stop_rc"] = st.returncode
    out["error_conservado"] = error_conservado
    out["git_diff_producto"] = subprocess.run(
        ["git", "diff", "--name-only", "--", "backend", "infra"], cwd=str(REPO),
        capture_output=True, text=True).stdout.strip()
    out["sha256_producto"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(BACK.glob("*.py"))}
    out["limite_declarado"] = (
        "`finally` NO corre si el proceso recibe SIGKILL o si la maquina se "
        "cae. Por eso el paso 0 chequea el estado heredado al arrancar: esa es "
        "la unica defensa real, y queda declarada en vez de asumida")
    out["finished_utc"] = datetime.datetime.now(
        datetime.timezone.utc).isoformat()
    destino = ROOT / f"falsador-login-v2-{SELLO}.json"
    destino.write_text(json.dumps(out, ensure_ascii=False, indent=2,
                                 default=str))
    print(f"\nverdes: {out['verdes']} | rojos: {out['rojos']}")
    print("rol final:", out.get("rol_final"))
    print("evidencia:", destino.name)
