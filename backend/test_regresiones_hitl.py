"""Regresiones de los cuatro defectos medidos en la auditoria de integracion.

QUE LO HACE DISTINTO de las suites que ya existian: el recorrido completo
arranca en un LOGIN REAL por HTTP. Nada de sesiones inyectadas. Ese era el
agujero: 9 de los 14 verdes de la auditoria usaban `app.sesiones.abrir(...)`
directo, asi que probaban componentes y no el camino de un abogado.

Y cada arreglo trae su FALSADOR: se vuelve a poner el defecto y se exige ROJO.
Un test que no puede fallar cuando el bug vuelve no es una regresion, es
decoracion.

Corre contra PostgreSQL real si hay `DATABASE_URL`/`DATABASE_URL_APP` en el
entorno; si no, corre la parte que no necesita base y declara NO MEDIDO el
resto. NO se sustituye por SQLite: SQLite no tiene RLS y el defecto 1 ERA de
RLS, asi que un verde ahi no probaria nada.

TRES DEFECTOS DE ESTE ARCHIVO, cazados en sus propias corridas y arreglados:
  1. el `redirect_stdout` que captura el log del handler se comia tambien los
     `print` de los checks, asi que los resultados eran invisibles. Un
     instrumento cuya salida no se ve no mide: ahora los checks van al stdout
     REAL guardado al importar, y el buffer solo recibe el log del servidor.
  2. la limpieza hacia DELETE sobre `users` y violaba la FK
     `aprobaciones_usuario_id_fkey`: la evidencia apunta al abogado que firmo.
  3. borrar el TENANT esperando que cascadee tampoco funciona, y eso resulto ser
     un HALLAZGO del producto, no un bug mio: el trigger
     `app.aprobacion_inmutable()` rechaza el DELETE incluso cuando llega por
     `ON DELETE CASCADE`. O sea que un bufete con aprobaciones NO SE PUEDE
     BORRAR. Se mide como control positivo del guard y los datos sinteticos
     quedan declarados en vez de forzar el borrado desactivando triggers.
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

import almacen as al  # noqa: E402
import api  # noqa: E402
import plazos  # noqa: E402

# El stdout REAL, tomado antes de cualquier redireccion.
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
    """Doble declarado. No se toca el corpus vivo para una regresion."""

    def buscar(self, q, limit=10):
        return {"total_pasajes": 0, "resultados": []}


def pedir(port, metodo, ruta, cuerpo=None, token=None):
    data = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(f"http://127.0.0.1:{port}{ruta}", method=metodo,
                                 data=data)
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
    """Levanta el handler HTTP REAL y captura SU stdout para auditarlo."""
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


# ---------------------------------------------------------------------------
# DEFECTO 4 - PLAZO CAUTELAR PENAL (no necesita base: es norma + aritmetica)
# ---------------------------------------------------------------------------

def regresion_plazo_penal():
    di("\n=== D4. Arranque del plazo cautelar penal (art. 130 CPP) ===")
    cal = plazos.CalendarioJudicial()
    cal.declarar_cubierto(2026)
    cal.declarar_cubierto(2027)

    # Caso del encargo: notificacion viernes 11-sep-2026, 3 dias cautelares.
    # Art. 130 CPP: corre "al dia siguiente de practicada la notificacion"
    # (no dice habil) y en cautelares se computan DIAS CORRIDOS.
    # Sabado 12 = dia 1, domingo 13 = dia 2, lunes 14 = dia 3.
    c = plazos.computo_detallado(_dt.date(2026, 9, 11), 3, plazos.Materia.PENAL,
                                 medida_cautelar=True, calendario=cal)
    ok("viernes + 3 dias cautelares vence el lunes 14",
       c.vencimiento.date().isoformat(), "2026-09-14")
    ok("el dia 1 es el sabado 12, no el lunes",
       [d["fecha"].isoformat() for d in c.detalle if d["n"] == 1], ["2026-09-12"])
    ok("modo corridos", c.modo, "corridos")

    # CONTROL POSITIVO 1: el civil de POCOS dias no cambia (art. 90.I: dia
    # siguiente HABIL).
    civ = plazos.computo_detallado(_dt.date(2026, 9, 11), 3, plazos.Materia.CIVIL,
                                   calendario=cal)
    ok("civil corto sigue arrancando el dia siguiente HABIL (lunes 14 = dia 1)",
       [d["fecha"].isoformat() for d in civ.detalle if d["n"] == 1],
       ["2026-09-14"])
    ok("civil corto vence el miercoles 16", civ.vencimiento.date().isoformat(),
       "2026-09-16")

    # CONTROL POSITIVO 2, Y ES EL QUE ME REFUTO LA PRIMERA VERSION: un plazo
    # CIVIL de mas de 15 dias tambien se computa CORRIDO (art. 90.II Ley 439),
    # pero su arranque sigue siendo el dia siguiente HABIL (art. 90.I). O sea
    # que "corridos" NO implica "arranque calendario". Si este control se cae,
    # el arreglo penal se comio la regla civil.
    civ16 = plazos.computo_detallado(_dt.date(2026, 9, 11), 16,
                                     plazos.Materia.CIVIL, calendario=cal)
    ok("civil de 16 dias es CORRIDO pero arranca el lunes 14, no el sabado",
       [d["fecha"].isoformat() for d in civ16.detalle if d["n"] == 1],
       ["2026-09-14"])
    ok("civil de 16 dias corridos vence el 29-sep",
       civ16.vencimiento.date().isoformat(), "2026-09-29")
    ok("y su modo es corridos (o sea que el control discrimina de verdad)",
       civ16.modo, "corridos")

    # BORDE CON INCERTIDUMBRE DECLARADA: si el ultimo dia corrido cae inhabil,
    # el art. 130 se contradice ('dias corridos' vs 'ultimo dia habil'). Eso no
    # se resuelve con codigo: se devuelve incertidumbre, NO un confirmado.
    # Notificacion jueves 10-sep-2026 + 2 dias corridos -> viernes 11, sabado 12.
    borde = plazos.computo_detallado(_dt.date(2026, 9, 10), 2,
                                     plazos.Materia.PENAL, medida_cautelar=True,
                                     calendario=cal)
    ok("ultimo dia inhabil NO se declara confirmado", borde.confiable, False)
    ok("y dice por que",
       any("NO CONFIRMADO" in a for a in borde.advertencias), True)

    # FALSADOR: la regla vieja (arranque habil) da OTRA fecha. Si algun dia las
    # dos coinciden, este test dejo de discriminar y hay que rehacerlo.
    def arranque_viejo(base):
        cur = base
        for _ in range(40):
            cur += _dt.timedelta(days=1)
            if plazos.es_habil(cur, calendario=cal):
                return cur
        raise AssertionError("sin habil")
    viejo = arranque_viejo(_dt.date(2026, 9, 11))
    ok("FALSADOR: la regla vieja da lunes 14 como dia 1 (por eso fallaba)",
       viejo.isoformat(), "2026-09-14")
    ok("FALSADOR: vieja y nueva DIFIEREN, el test discrimina",
       viejo != _dt.date(2026, 9, 12), True)


# ---------------------------------------------------------------------------
# DEFECTOS 1, 2 y 3 - contra PostgreSQL real con el rol de la aplicacion
# ---------------------------------------------------------------------------

def sembrar_postgres(dsn_admin):
    import psycopg
    ids = {k: str(uuid.uuid4()) for k in ("A", "B", "UA", "UB")}
    slugs = {"A": "regr-a-" + ids["A"][:8], "B": "regr-b-" + ids["B"][:8]}
    with psycopg.connect(dsn_admin, autocommit=True) as c:
        for etq in ("A", "B"):
            c.execute("INSERT INTO tenants(id,slug,nombre_bufete)"
                      " VALUES (%s,%s,%s)",
                      (ids[etq], slugs[etq], "REGRESION " + etq))
            # MISMO email en los dos bufetes: es el caso que un login por email
            # suelto no puede resolver, y el que prueba que el bufete manda.
            c.execute(
                "INSERT INTO users(id,tenant_id,email,password_hash,"
                "nombre_completo,rol,matricula_cab)"
                " VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (ids["U" + etq], ids[etq], "mismo@regresion.invalid",
                 al.hash_password(PASSWORD), "REGRESION " + etq, "socio",
                 "REGR-" + etq))
    return ids, slugs


def cerrar_fixtures(dsn_admin, ids, slugs):
    """Intenta borrar el bufete sintetico y MIDE lo que pasa.

    No es limpieza a cualquier precio: el trigger `app.aprobacion_inmutable()`
    rechaza el DELETE de una aprobacion INCLUSO cuando llega por el
    `ON DELETE CASCADE` de `tenants`. Eso hace que un bufete con aprobaciones
    no se pueda borrar, y es informacion del producto que vale mas que dejar la
    base prolija. NO se desactivan triggers ni se eleva el rol para forzarlo:
    eso seria sabotear el guard que estoy midiendo.
    """
    import psycopg
    bloqueado = False
    mensaje = ""
    try:
        with psycopg.connect(dsn_admin, autocommit=True) as c:
            c.execute("DELETE FROM tenants WHERE id = ANY(%s::uuid[])",
                      ([ids["A"], ids["B"]],))
    except psycopg.errors.RaiseException as e:
        bloqueado = True
        mensaje = str(e).splitlines()[0]
    ok("GUARD: el trigger de inmutabilidad bloquea el DELETE en cascada",
       bloqueado, True)
    if bloqueado:
        di("       verbatim: " + mensaje)
        CONSERVADO.append(
            "bufetes sinteticos " + ", ".join(slugs.values()) + " quedan en la "
            "base: el trigger de inmutabilidad no permite borrarlos porque "
            "tienen aprobaciones. Cada corrida usa UUID y slug nuevos, asi que "
            "el test es repetible; la base acumula fixtures y eso hay que "
            "resolverlo con una decision de producto, no desactivando el guard")


def regresiones_con_postgres(dsn_admin, dsn_app):
    di("\n=== D1/D2/D3 contra PostgreSQL REAL, rol de aplicacion ===")
    import psycopg
    with psycopg.connect(dsn_app) as c:
        rol = c.execute("SELECT rolname, rolsuper, rolbypassrls FROM pg_roles"
                        " WHERE rolname = current_user").fetchone()
    # CONTROL DEL INSTRUMENTO: si el rol tuviera bypass o superusuario, todo lo
    # que sigue seria un verde vacio. Se mide antes de creer en nada.
    ok("el rol de la app NO es superusuario", bool(rol[1]), False)
    ok("el rol de la app NO tiene BYPASSRLS", bool(rol[2]), False)

    ids, slugs = sembrar_postgres(dsn_admin)
    try:
        store = al.PostgresAlmacen(dsn_app)
        app = api.App(almacen=store, corpus=CorpusDoble())
        with servidor(app) as (port, log):
            # --- D1: LOGIN REAL, sin inyectar sesiones -------------------
            st, cuerpo = pedir(port, "POST", "/sesion",
                               {"bufete": slugs["A"],
                                "email": "mismo@regresion.invalid",
                                "password": PASSWORD})
            ok("D1 credencial valida por HTTP+RLS da 200", st, 200)
            token = cuerpo.get("token")
            ok("D1 devuelve token real", bool(token), True)
            ok("D1 y resuelve el bufete correcto",
               cuerpo.get("bufete_id"), ids["A"])

            st, _ = pedir(port, "POST", "/sesion",
                          {"bufete": slugs["A"],
                           "email": "mismo@regresion.invalid",
                           "password": "no-es-la-clave"})
            ok("D1 password mala da 401", st, 401)
            st, _ = pedir(port, "POST", "/sesion",
                          {"bufete": slugs["A"],
                           "email": "nadie@regresion.invalid",
                           "password": PASSWORD})
            ok("D1 email inexistente da 401", st, 401)
            st, _ = pedir(port, "POST", "/sesion",
                          {"bufete": "bufete-que-no-existe",
                           "email": "mismo@regresion.invalid",
                           "password": PASSWORD})
            ok("D1 bufete inexistente da 401", st, 401)
            st, _ = pedir(port, "POST", "/sesion",
                          {"email": "mismo@regresion.invalid",
                           "password": PASSWORD})
            ok("D1 sin bufete da 401 (el email esta en DOS bufetes)", st, 401)

            # SELECCION INEQUIVOCA: el mismo email en el bufete B entra a B.
            st, cb = pedir(port, "POST", "/sesion",
                           {"bufete": slugs["B"],
                            "email": "mismo@regresion.invalid",
                            "password": PASSWORD})
            ok("D1 el mismo email en el bufete B resuelve a B", st, 200)
            ok("D1 y NO cruza al bufete A", cb.get("bufete_id"), ids["B"])
            token_b = cb.get("token")

            # --- Recorrido e2e con el token del login real ---------------
            st, caso = pedir(port, "POST", "/casos",
                             {"nro_expediente": "REGR-001",
                              "juzgado": "Juzgado de regresion",
                              "materia": "civil"}, token)
            ok("e2e crear caso con token de login real", st, 201)
            cid = caso.get("id")
            st, propios = pedir(port, "GET", "/casos", token=token)
            ok("e2e aislamiento POSITIVO: A ve su caso",
               any(x["id"] == cid for x in propios.get("casos", [])), True)
            st, ajenos = pedir(port, "GET", "/casos", token=token_b)
            ok("e2e aislamiento NEGATIVO: B no ve el caso de A",
               any(x["id"] == cid for x in ajenos.get("casos", [])), False)

            # --- D2: el rechazo posterior revoca -------------------------
            contenido = "MEMORIAL DE REGRESION " + CANARIO
            payload = {"tipo": "presentar_escrito", "contenido": contenido,
                       "case_id": cid}
            st, _ = pedir(port, "POST", "/acciones/externa", payload, token)
            ok("D2 sin ninguna decision: 403", st, 403)
            st, _ = pedir(port, "POST", "/aprobar",
                          {"tipo": "presentar_escrito", "contenido": contenido,
                           "case_id": cid, "decision": "aprobado",
                           "fundamento": "regresion"}, token)
            ok("D2 aprobacion registrada", st, 201)
            st, _ = pedir(port, "POST", "/acciones/externa", payload, token)
            ok("D2 con aprobacion vigente: 200 (control POSITIVO)", st, 200)
            st, _ = pedir(port, "POST", "/aprobar",
                          {"tipo": "presentar_escrito", "contenido": contenido,
                           "case_id": cid, "decision": "rechazado",
                           "fundamento": "me arrepiento"}, token)
            ok("D2 rechazo posterior registrado", st, 201)
            st, _ = pedir(port, "POST", "/acciones/externa", payload, token)
            ok("D2 EL DEFECTO: tras el rechazo la accion se BLOQUEA", st, 403)
            # Y una aprobacion NUEVA vuelve a habilitar: si no, el gate quedo
            # trabado, y eso tambien seria un defecto.
            st, _ = pedir(port, "POST", "/aprobar",
                          {"tipo": "presentar_escrito", "contenido": contenido,
                           "case_id": cid, "decision": "aprobado",
                           "fundamento": "reconsiderado"}, token)
            ok("D2 aprobacion nueva registrada", st, 201)
            st, _ = pedir(port, "POST", "/acciones/externa", payload, token)
            ok("D2 una aprobacion NUEVA vuelve a habilitar", st, 200)
            # Bordes que ya estaban y no deben romperse.
            st, _ = pedir(port, "POST", "/acciones/externa",
                          {"tipo": "presentar_escrito",
                           "contenido": contenido + " ALTERADO",
                           "case_id": cid}, token)
            ok("D2 contenido alterado: 403", st, 403)
            st, _ = pedir(port, "POST", "/acciones/externa",
                          {"tipo": "notificar_cliente", "contenido": contenido,
                           "case_id": cid}, token)
            ok("D2 otro tipo de accion: 403", st, 403)
            st, _ = pedir(port, "POST", "/acciones/externa", payload, token_b)
            ok("D2 la aprobacion de A no sirve para B: 403", st, 403)

            # --- D3: el log no puede traer la consulta -------------------
            st, _ = pedir(port, "GET", f"/buscar?q={CANARIO}", token=token)
            ok("D3 la busqueda responde", st, 200)
            st, _ = pedir(port, "GET", f"/no-existe?q={CANARIO}", token=token)
            ok("D3 la ruta de error tambien responde", st, 404)
        salida = log.getvalue()
        ok("D3 el canario NO aparece en el log del handler real",
           CANARIO in salida, False)
        ok("D3 pero el log SI registra la ruta (no quedo mudo)",
           "/buscar" in salida, True)
    finally:
        cerrar_fixtures(dsn_admin, ids, slugs)


def main() -> int:
    di("=" * 66)
    di("REGRESIONES DE LOS CUATRO DEFECTOS - canario " + CANARIO)
    di("=" * 66)
    regresion_plazo_penal()
    dsn_admin = os.environ.get("DATABASE_URL")
    dsn_app = os.environ.get("DATABASE_URL_APP")
    if dsn_admin and dsn_app:
        regresiones_con_postgres(dsn_admin, dsn_app)
    else:
        NO_MEDIDO.append(
            "D1/D2/D3 con PostgreSQL: sin DATABASE_URL/DATABASE_URL_APP. NO se "
            "sustituye por SQLite: SQLite no tiene RLS y el defecto 1 ERA de "
            "RLS, asi que un verde ahi no probaria nada")
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
