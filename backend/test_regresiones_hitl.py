"""Regresiones de los cuatro defectos, con fases invocables por supervisor.

La integración recibe fixtures explícitos; no llama al cierre por su cuenta.
El supervisor observa plazos, integración y cierre por separado. El main local
conserva su try/finally para uso directo. No se modifica la lógica de producto.
Corpus remoto sustituido por doble declarado. PostgreSQL real para integración.
"""
import contextlib
import datetime as _dt
import io
import json
import os
import sys
import threading
import urllib.error
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import almacen as al
import api
import plazos

SALIDA = sys.stdout
VERDES = 0
ROJOS = 0
NO_MEDIDO: list[str] = []
CONSERVADO: list[str] = []
CANARIO = "CANARIO_REGRESION_" + uuid.uuid4().hex[:8]
PASSWORD = "regresion-only-" + uuid.uuid4().hex[:8]


def di(texto: str) -> None:
    print(texto, file=SALIDA, flush=True)


def ok(etiqueta: str, actual, esperado) -> bool:
    global VERDES, ROJOS
    paso = actual == esperado
    if paso:
        VERDES += 1
        di(f"  OK   {etiqueta}: {actual!r}")
    else:
        ROJOS += 1
        di(f"  ROJO {etiqueta}: obtenido {actual!r}, esperado {esperado!r}")
    return paso


class CorpusDoble:
    def buscar(self, q, limit=10):
        return {"total_pasajes": 0, "resultados": []}


def pedir(port, metodo, ruta, cuerpo=None, token=None):
    data = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(f"http://127.0.0.1:{port}{ruta}", method=metodo, data=data)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


@contextlib.contextmanager
def servidor(app):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        srv = api.servir(app, "127.0.0.1", 0)
        hilo = threading.Thread(target=srv.serve_forever, daemon=True)
        hilo.start()
        try:
            yield srv.server_address[1], buf
        finally:
            srv.shutdown()
            srv.server_close()


def regresion_plazo_penal():
    di("\n=== D4. Arranque del plazo cautelar penal (art. 130 CPP) ===")
    cal = plazos.CalendarioJudicial()
    cal.declarar_cubierto(2026)
    cal.declarar_cubierto(2027)
    c = plazos.computo_detallado(_dt.date(2026, 9, 11), 3, plazos.Materia.PENAL,
                                 medida_cautelar=True, calendario=cal)
    ok("viernes + 3 dias cautelares vence el lunes 14", c.vencimiento.date().isoformat(), "2026-09-14")
    ok("el dia 1 es el sabado 12, no el lunes",
       [d["fecha"].isoformat() for d in c.detalle if d["n"] == 1], ["2026-09-12"])
    ok("modo corridos", c.modo, "corridos")
    civ = plazos.computo_detallado(_dt.date(2026, 9, 11), 3, plazos.Materia.CIVIL, calendario=cal)
    ok("civil corto sigue arrancando el dia siguiente HABIL (lunes 14 = dia 1)",
       [d["fecha"].isoformat() for d in civ.detalle if d["n"] == 1], ["2026-09-14"])
    ok("civil corto vence el miercoles 16", civ.vencimiento.date().isoformat(), "2026-09-16")
    civ16 = plazos.computo_detallado(_dt.date(2026, 9, 11), 16, plazos.Materia.CIVIL, calendario=cal)
    ok("civil de 16 dias es CORRIDO pero arranca el lunes 14, no el sabado",
       [d["fecha"].isoformat() for d in civ16.detalle if d["n"] == 1], ["2026-09-14"])
    ok("civil de 16 dias corridos vence el 29-sep", civ16.vencimiento.date().isoformat(), "2026-09-29")
    ok("y su modo es corridos (o sea que el control discrimina de verdad)", civ16.modo, "corridos")
    borde = plazos.computo_detallado(_dt.date(2026, 9, 10), 2, plazos.Materia.PENAL,
                                     medida_cautelar=True, calendario=cal)
    ok("ultimo dia inhabil NO se declara confirmado", borde.confiable, False)
    ok("y dice por que", any("NO CONFIRMADO" in a for a in borde.advertencias), True)
    def arranque_viejo(base):
        cur = base
        for _ in range(40):
            cur += _dt.timedelta(days=1)
            if plazos.es_habil(cur, calendario=cal):
                return cur
        raise AssertionError("sin habil")
    viejo = arranque_viejo(_dt.date(2026, 9, 11))
    ok("FALSADOR: la regla vieja da lunes 14 como dia 1 (por eso fallaba)", viejo.isoformat(), "2026-09-14")
    ok("FALSADOR: vieja y nueva DIFIEREN, el test discrimina", viejo != _dt.date(2026, 9, 12), True)


def sembrar_postgres(dsn_admin):
    import psycopg
    ids = {k: str(uuid.uuid4()) for k in ("A", "B", "UA", "UB")}
    slugs = {"A": "regr-a-" + ids["A"][:8], "B": "regr-b-" + ids["B"][:8]}
    with psycopg.connect(dsn_admin, autocommit=True) as c:
        for etq in ("A", "B"):
            c.execute("INSERT INTO tenants(id,slug,nombre_bufete) VALUES (%s,%s,%s)",
                      (ids[etq], slugs[etq], "REGRESION " + etq))
            c.execute("INSERT INTO users(id,tenant_id,email,password_hash,nombre_completo,rol,matricula_cab) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                      (ids["U" + etq], ids[etq], "mismo@regresion.invalid", al.hash_password(PASSWORD),
                       "REGRESION " + etq, "socio", "REGR-" + etq))
    return ids, slugs


def cerrar_fixtures(dsn_admin, ids, slugs):
    """Observe the intentional retention barrier; do not disable it for cleanup."""
    import psycopg
    bloqueado = False
    barrera = "NINGUNA"
    mensaje = ""
    try:
        with psycopg.connect(dsn_admin, autocommit=True) as c:
            c.execute("DELETE FROM tenants WHERE id = ANY(%s::uuid[])", ([ids["A"], ids["B"]],))
    except psycopg.errors.ForeignKeyViolation as e:
        bloqueado, barrera = True, "FK RESTRICT"
        mensaje = str(e).splitlines()[0]
    except psycopg.errors.RaiseException as e:
        bloqueado, barrera = True, "trigger de inmutabilidad"
        mensaje = str(e).splitlines()[0]
    ok("GUARD: borrar un bufete con aprobaciones queda BLOQUEADO", bloqueado, True)
    di("       barrera que actuo: " + barrera)
    if bloqueado:
        di("       verbatim: " + mensaje)
        CONSERVADO.append("bufetes sinteticos " + ", ".join(slugs.values()) +
                          " quedan en la base: tienen aprobaciones y por decision no se borran. "
                          "Cada corrida usa UUID y slug nuevos; purgado deliberado en "
                          "infra/2026-09-16-cierra-el-borrado-de-un-bufete.sql")


def regresiones_con_postgres(dsn_admin, dsn_app, fixtures):
    """Run integration only; caller owns fixtures and cleanup invocation."""
    di("\n=== D1/D2/D3 contra PostgreSQL REAL, rol de aplicacion ===")
    import psycopg
    with psycopg.connect(dsn_app) as c:
        rol = c.execute("SELECT rolname, rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user").fetchone()
    ok("el rol de la app NO es superusuario", bool(rol[1]), False)
    ok("el rol de la app NO tiene BYPASSRLS", bool(rol[2]), False)
    ids, slugs = fixtures
    store = al.PostgresAlmacen(dsn_app)
    app = api.App(almacen=store, corpus=CorpusDoble())
    with servidor(app) as (port, log):
        st, cuerpo = pedir(port, "POST", "/sesion", {"bufete": slugs["A"], "email": "mismo@regresion.invalid", "password": PASSWORD})
        ok("D1 credencial valida por HTTP+RLS da 200", st, 200)
        token = cuerpo.get("token")
        ok("D1 devuelve token real", bool(token), True)
        ok("D1 y resuelve el bufete correcto", cuerpo.get("bufete_id"), ids["A"])
        st, _ = pedir(port, "POST", "/sesion", {"bufete": slugs["A"], "email": "mismo@regresion.invalid", "password": "no-es-la-clave"})
        ok("D1 password mala da 401", st, 401)
        st, _ = pedir(port, "POST", "/sesion", {"bufete": slugs["A"], "email": "nadie@regresion.invalid", "password": PASSWORD})
        ok("D1 email inexistente da 401", st, 401)
        st, _ = pedir(port, "POST", "/sesion", {"bufete": "bufete-que-no-existe", "email": "mismo@regresion.invalid", "password": PASSWORD})
        ok("D1 bufete inexistente da 401", st, 401)
        st, _ = pedir(port, "POST", "/sesion", {"email": "mismo@regresion.invalid", "password": PASSWORD})
        ok("D1 sin bufete da 401 (el email esta en DOS bufetes)", st, 401)
        st, cb = pedir(port, "POST", "/sesion", {"bufete": slugs["B"], "email": "mismo@regresion.invalid", "password": PASSWORD})
        ok("D1 el mismo email en el bufete B resuelve a B", st, 200)
        ok("D1 y NO cruza al bufete A", cb.get("bufete_id"), ids["B"])
        token_b = cb.get("token")
        st, caso = pedir(port, "POST", "/casos", {"nro_expediente": "REGR-001", "juzgado": "Juzgado de regresion", "materia": "civil"}, token)
        ok("e2e crear caso con token de login real", st, 201)
        cid = caso.get("id")
        st, propios = pedir(port, "GET", "/casos", token=token)
        ok("e2e aislamiento POSITIVO: A ve su caso", any(x["id"] == cid for x in propios.get("casos", [])), True)
        st, ajenos = pedir(port, "GET", "/casos", token=token_b)
        ok("e2e aislamiento NEGATIVO: B no ve el caso de A", any(x["id"] == cid for x in ajenos.get("casos", [])), False)
        contenido = "MEMORIAL DE REGRESION " + CANARIO
        payload = {"tipo": "presentar_escrito", "contenido": contenido, "case_id": cid}
        st, _ = pedir(port, "POST", "/acciones/externa", payload, token)
        ok("D2 sin ninguna decision: 403", st, 403)
        st, _ = pedir(port, "POST", "/aprobar", {"tipo": "presentar_escrito", "contenido": contenido, "case_id": cid, "decision": "aprobado", "fundamento": "regresion"}, token)
        ok("D2 aprobacion registrada", st, 201)
        st, _ = pedir(port, "POST", "/acciones/externa", payload, token)
        ok("D2 con aprobacion vigente: 200 (control POSITIVO)", st, 200)
        st, _ = pedir(port, "POST", "/aprobar", {"tipo": "presentar_escrito", "contenido": contenido, "case_id": cid, "decision": "rechazado", "fundamento": "me arrepiento"}, token)
        ok("D2 rechazo posterior registrado", st, 201)
        st, _ = pedir(port, "POST", "/acciones/externa", payload, token)
        ok("D2 EL DEFECTO: tras el rechazo la accion se BLOQUEA", st, 403)
        st, _ = pedir(port, "POST", "/aprobar", {"tipo": "presentar_escrito", "contenido": contenido, "case_id": cid, "decision": "aprobado", "fundamento": "reconsiderado"}, token)
        ok("D2 aprobacion nueva registrada", st, 201)
        st, _ = pedir(port, "POST", "/acciones/externa", payload, token)
        ok("D2 una aprobacion NUEVA vuelve a habilitar", st, 200)
        st, _ = pedir(port, "POST", "/acciones/externa", {"tipo": "presentar_escrito", "contenido": contenido + " ALTERADO", "case_id": cid}, token)
        ok("D2 contenido alterado: 403", st, 403)
        st, _ = pedir(port, "POST", "/acciones/externa", {"tipo": "notificar_cliente", "contenido": contenido, "case_id": cid}, token)
        ok("D2 otro tipo de accion: 403", st, 403)
        st, _ = pedir(port, "POST", "/acciones/externa", payload, token_b)
        ok("D2 la aprobacion de A no sirve para B: 403", st, 403)
        st, otro = pedir(port, "POST", "/casos", {"nro_expediente": "REGR-002", "juzgado": "Juzgado de regresion", "materia": "civil"}, token)
        cid2 = otro.get("id")
        ok("CASO el segundo expediente se creo (si no, no se puede medir)", bool(cid2 and cid2 != cid), True)
        st, _ = pedir(port, "POST", "/acciones/externa", {"tipo": "presentar_escrito", "contenido": contenido, "case_id": cid2}, token)
        ok("CASO la aprobacion del caso 1 NO sirve para el caso 2", st, 403)
        st, _ = pedir(port, "POST", "/acciones/externa", {"tipo": "presentar_escrito", "contenido": contenido}, token)
        ok("CASO una accion SIN caso NO hereda la aprobacion del caso 1", st, 403)
        st, _ = pedir(port, "POST", "/acciones/externa", payload, token)
        ok("CASO con el caso correcto sigue autorizando (control positivo)", st, 200)
        st, _ = pedir(port, "GET", f"/buscar?q={CANARIO}", token=token)
        ok("D3 la busqueda responde", st, 200)
        st, _ = pedir(port, "GET", f"/no-existe?q={CANARIO}", token=token)
        ok("D3 la ruta de error tambien responde", st, 404)
    salida = log.getvalue()
    ok("D3 el canario NO aparece en el log del handler real", CANARIO in salida, False)
    ok("D3 pero el log SI registra la ruta (no quedo mudo)", "/buscar" in salida, True)


def main() -> int:
    di("=" * 66)
    di("REGRESIONES DE LOS CUATRO DEFECTOS - canario " + CANARIO)
    di("=" * 66)
    regresion_plazo_penal()
    dsn_admin = os.environ.get("DATABASE_URL")
    dsn_app = os.environ.get("DATABASE_URL_APP")
    if dsn_admin and dsn_app:
        fixtures = sembrar_postgres(dsn_admin)
        try:
            regresiones_con_postgres(dsn_admin, dsn_app, fixtures)
        finally:
            cerrar_fixtures(dsn_admin, *fixtures)
    else:
        NO_MEDIDO.append("D1/D2/D3 con PostgreSQL: sin DATABASE_URL/DATABASE_URL_APP. NO se sustituye por SQLite")
    di("\n" + "=" * 66)
    for m in NO_MEDIDO:
        di("NO MEDIDO: " + m)
    for m in CONSERVADO:
        di("CONSERVADO: " + m)
    di(f"verdes: {VERDES} | rojos: {ROJOS}")
    di("VERDE" if ROJOS == 0 else "ROJO")
    return 1 if ROJOS else 0


if __name__ == "__main__":
    raise SystemExit(main())
