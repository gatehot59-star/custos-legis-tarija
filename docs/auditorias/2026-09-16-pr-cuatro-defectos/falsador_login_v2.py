"""Falsador del login. Tercera version: ahora el guard de restauracion puede
DAR ROJO, que es lo unico que lo vuelve un guard.

EL DEFECTO DE LA v1, confirmado: el `ALTER ROLE ... NOBYPASSRLS` vivia en el
camino normal. El `finally` detenia el cluster pero NO garantizaba revocar el
privilegio si algo explotaba entre elevar y revocar. La corrida registrada si
revirtio, y eso es una OBSERVACION, no una garantia. La distincion es de Sol y
es correcta.

EL DEFECTO DE LA v2, y tambien es de Sol: la revocacion paso al `finally`, pero
envuelta en `contextlib.suppress(Exception)`. O sea que si el `ALTER` fallaba,
NADIE se enteraba: el rol quedaba con BYPASSRLS puesto y el script imprimia
"rojos: 0". **Un guard que se calla cuando falla es peor que no tenerlo, porque
reparte tranquilidad falsa.** Sol lo dijo como "suprime errores de restauracion
en bloque exterior" y tiene razon entera.

Y UN DEFECTO MIO QUE APARECIO AL LEERLO PARA ARREGLAR EL DE SOL: la v2 no tenia
NINGUN `sys.exit`. Contaba rojos, los imprimia, y salia con codigo 0. Cualquier
script o CI que lo llamara lo habria visto verde con rojos adentro. Es
exactamente el patron que vengo cazando en los guards del workflow, esta vez
dentro de mi propio instrumento.

QUE HAY AHORA:
  1. La revocacion vive en el `finally` y **su error se captura, se escribe en
     el JSON y cuenta como ROJO**. Nada de suppress.
  2. El veredicto de restauracion NO se cree del `ALTER`: se lee de `pg_roles`
     despues. Si el rol quedo con bypass, es ROJO aunque el ALTER no haya
     levantado nada.
  3. Brazo con EXCEPCION INYECTADA justo despues de elevar: tiene que restaurar
     el rol, detener el cluster y CONSERVAR el error original.
  4. Chequeo de ESTADO HEREDADO al arrancar: si una corrida anterior murio por
     SIGKILL con el privilegio puesto, este arranque lo tiene que ver y decirlo.
     `finally` no corre con SIGKILL, y eso queda declarado como limite en vez de
     asumido como cubierto.
  5. MODO SABOTAJE (`FALSADOR_V2_SABOTEAR_REVOCACION=1`): hace que `revocar()`
     levante. Existe para FALSAR el guard nuevo, porque un guard que nunca se
     probo contra su propio fallo es una anecdota. Con el sabotaje puesto este
     script tiene que: reportar ROJO, decir que el rol pudo quedar elevado, y
     SALIR CON CODIGO 1. Y la corrida siguiente, sin sabotaje, tiene que cazar
     el bypass HEREDADO en el paso 0. Esa cadena es la prueba de que las dos
     defensas discriminan.

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
# Sabotaje del propio guard. Apagado salvo que se pida a proposito.
SABOTAJE = os.environ.get("FALSADOR_V2_SABOTEAR_REVOCACION") == "1"
sys.path.insert(0, str(BACK))

import psycopg  # noqa: E402
import almacen  # noqa: E402
import api  # noqa: E402

SELLO = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
out = {"instrumento": "falsador del login v2 (revocacion en finally, con su "
                      "error medido)",
       "root": str(ROOT), "sello": SELLO,
       "sabotaje_de_la_revocacion": SABOTAJE,
       "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "brazos": [], "verdes": 0, "rojos": 0}


def chk(etiqueta, actual, esperado):
    paso = actual == esperado
    out["verdes" if paso else "rojos"] += 1
    print(f"  {'OK  ' if paso else 'ROJO'} {etiqueta}: {actual!r}"
          + ("" if paso else f" (esperaba {esperado!r})"))
    return paso


def rojo(etiqueta, detalle):
    """ROJO sin comparacion: para los fallos del propio instrumento."""
    out["rojos"] += 1
    print(f"  ROJO {etiqueta}: {detalle}")


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
    if SABOTAJE:
        raise RuntimeError(
            "revocacion SABOTEADA a proposito "
            "(FALSADOR_V2_SABOTEAR_REVOCACION=1). Si este script termina en "
            "verde o con codigo 0, el guard de restauracion no sirve")
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
    # Si una corrida anterior murio por SIGKILL despues de elevar, o si su
    # revocacion FALLO, el privilegio quedo puesto. `finally` no corre con
    # SIGKILL: la unica defensa es mirarlo al arrancar. Este chequeo tiene que
    # dar ROJO tras una corrida con FALSADOR_V2_SABOTEAR_REVOCACION=1, y eso es
    # medible en dos corridas seguidas.
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
    # REVOCACION EN EL finally, que era el reparo anterior de Sol, PERO ahora sin
    # tragarse su propio error, que era el reparo nuevo. La v2 tenia:
    #     with contextlib.suppress(Exception):
    #         revocar()
    # y con eso un ALTER fallido quedaba invisible: rol elevado y "rojos: 0".
    if started:
        try:
            revocar()
            out["revocacion_final"] = "OK"
        except Exception as e:  # noqa: BLE001
            out["revocacion_final"] = f"FALLO: {type(e).__name__}: {e}"
            rojo("la revocacion final FALLO", out["revocacion_final"])
            print("       EL ROL PUEDE HABER QUEDADO CON BYPASSRLS PUESTO.")
            print("       Revisar a mano: ALTER ROLE custos_app NOBYPASSRLS")
        try:
            out["rol_final"] = estado_rol()
        except Exception as e:  # noqa: BLE001
            out["rol_final"] = f"NO MEDIDO: {type(e).__name__}: {e}"
            rojo("no pude LEER el rol final", out["rol_final"])
        # EL VEREDICTO SE LEE DEL CATALOGO, no del ALTER. Un ALTER que no levanta
        # no prueba que el privilegio se fue.
        rf = out.get("rol_final")
        if isinstance(rf, (list, tuple)):
            if bool(rf[2]):
                rojo("EL ROL QUEDO CON BYPASSRLS", repr(rf))
            else:
                out["verdes"] += 1
                print("  OK   el rol final NO tiene bypassrls (leido de "
                      f"pg_roles): {rf!r}")
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
    print("revocacion final:", out.get("revocacion_final"))
    print("evidencia:", destino.name)
    print("VERDE" if out["rojos"] == 0 else "ROJO")
    # LA v2 NO TENIA ESTO y es un defecto mio, no de Sol: contaba rojos, los
    # imprimia, y salia con codigo 0. Cualquier script que lo llamara lo veia
    # verde. Si hay una excepcion en vuelo NO se llama exit: dejarla propagar
    # conserva el traceback, y su codigo ya es distinto de cero.
    if error_conservado is None and out["rojos"]:
        sys.exit(1)
