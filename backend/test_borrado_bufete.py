"""Regresion de la decision sobre el trigger de inmutabilidad.

QUE PRUEBA, y por que cada cosa:

  1. CONTROL POSITIVO DEL DEFECTO. Antes de la migracion, `custos_app` borraba
     un bufete SIN aprobaciones: 1 fila. Ese caso tiene que pasar a rechazado.
     Si no lo probara ANTES y DESPUES, el verde no distinguiria "lo cerre" de
     "nunca estuvo abierto".
  2. La evidencia sigue inmutable: un bufete CON aprobaciones no se borra ni con
     el rol administrativo.
  3. EL CONTROL QUE PUEDE DAR ROJO Y ROMPER EL LOGIN: la migracion revoca
     DELETE/UPDATE/INSERT sobre `tenants` pero DEBE conservar SELECT, porque el
     login corregido resuelve el bufete leyendo esa tabla. Si el SELECT se va
     de mas, el login vuelve a 401 y este test lo caza.

Corre solo con `DATABASE_URL` y `DATABASE_URL_APP`. Sin PostgreSQL declara
NO MEDIDO: esto es una prueba de privilegios y RLS, y SQLite no tiene ninguno
de los dos.

DEFECTO DE MI PROPIO INSTRUMENTO, cazado en la medicion previa y arreglado aca:
la v1 reportaba "PASO" cuando un DELETE afectaba CERO filas. Un DELETE que no
toca nada NO es un DELETE exitoso, y confundirlos me habria hecho reportar como
agujero algo que era RLS trabajando. Ahora todo informa `rowcount`.
"""
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import almacen as al  # noqa: E402

VERDES = 0
ROJOS = 0


def ok(etiqueta, actual, esperado):
    global VERDES, ROJOS
    if actual == esperado:
        VERDES += 1
        print(f"  OK   {etiqueta}: {actual!r}")
    else:
        ROJOS += 1
        print(f"  ROJO {etiqueta}: obtenido {actual!r}, esperado {esperado!r}")


def main() -> int:
    admin = os.environ.get("DATABASE_URL")
    app_dsn = os.environ.get("DATABASE_URL_APP")
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    migracion = os.path.join(
        raiz, "infra", "2026-09-16-cierra-el-borrado-de-un-bufete.sql")
    if not (admin and app_dsn):
        print("NO MEDIDO: falta DATABASE_URL/DATABASE_URL_APP. Esta suite prueba "
              "privilegios y RLS; SQLite no tiene ninguno de los dos, asi que un "
              "verde ahi no probaria nada.")
        return 0

    import psycopg

    ids = {k: str(uuid.uuid4()) for k in ("CON", "SIN", "U", "CTRL")}

    def probar(dsn, sql, args=()):
        """Devuelve (clase, filas). `filas` distingue 'no toco nada' de 'lo hizo'."""
        try:
            with psycopg.connect(dsn, autocommit=True) as c:
                cur = c.execute(sql, args)
                return ("sin error", cur.rowcount)
        except Exception as e:  # noqa: BLE001
            return (type(e).__name__, None)

    def sembrar():
        with psycopg.connect(admin, autocommit=True) as c:
            for k, nombre in (("CON", "BORRADO-CON"), ("SIN", "BORRADO-SIN"),
                              ("CTRL", "BORRADO-CTRL")):
                c.execute("INSERT INTO tenants(id,slug,nombre_bufete)"
                          " VALUES(%s,%s,%s)",
                          (ids[k], "borr-" + ids[k][:8], nombre))
            c.execute("INSERT INTO users(id,tenant_id,email,password_hash,"
                      "nombre_completo,rol,matricula_cab)"
                      " VALUES(%s,%s,%s,%s,%s,%s,%s)",
                      (ids["U"], ids["CON"], "b@borrado.invalid",
                       al.hash_password("borrado-only-x"), "BORRADO", "socio",
                       "B-1"))
            c.execute("INSERT INTO cases(id,tenant_id,nro_expediente,juzgado,"
                      "materia) VALUES(gen_random_uuid(),%s,'B-1','J','civil')",
                      (ids["CON"],))
            cid = c.execute("SELECT id FROM cases WHERE tenant_id=%s",
                            (ids["CON"],)).fetchone()[0]
            c.execute("INSERT INTO aprobaciones(tenant_id,case_id,usuario_id,"
                      "matricula,tipo,sha256_entrada,decision) VALUES"
                      "(%s,%s,%s,'B-1','presentar_escrito',%s,'aprobado')",
                      (ids["CON"], cid, ids["U"], "b" * 64))

    print("=" * 66)
    print("DECISION DEL TRIGGER: la evidencia se queda, el borrado se cierra")
    print("=" * 66)

    print("\n=== 1. ANTES de la migracion: el defecto EXISTE (control positivo)")
    sembrar()
    clase, filas = probar(app_dsn, "DELETE FROM tenants WHERE id=%s",
                          (ids["CTRL"],))
    ok("el rol de la app BORRABA un bufete sin aprobaciones", (clase, filas),
       ("sin error", 1))
    clase, _ = probar(app_dsn, "DELETE FROM tenants WHERE id=%s", (ids["CON"],))
    ok("y uno CON aprobaciones ya estaba frenado por el trigger", clase,
       "RaiseException")

    print("\n=== 2. Aplico la migracion")
    with psycopg.connect(admin, autocommit=True) as c:
        with open(migracion, encoding="utf-8") as f:
            c.execute(f.read(), prepare=False)
    with psycopg.connect(admin, autocommit=True) as c:
        privs = [r[0] for r in c.execute(
            "SELECT privilege_type FROM information_schema.role_table_grants"
            " WHERE grantee='custos_app' AND table_name='tenants' ORDER BY 1"
        ).fetchall()]
        fk = c.execute(
            "SELECT confdeltype FROM pg_constraint"
            " WHERE conname='aprobaciones_tenant_id_fkey'").fetchone()[0]
    ok("custos_app sobre tenants queda con SELECT y nada mas", privs,
       ["SELECT"])
    ok("la FK de aprobaciones pasa a RESTRICT", fk, "r")

    print("\n=== 3. DESPUES: el defecto esta CERRADO")
    clase, filas = probar(app_dsn, "DELETE FROM tenants WHERE id=%s",
                          (ids["SIN"],))
    ok("el rol de la app YA NO puede borrar un bufete sin aprobaciones",
       clase, "InsufficientPrivilege")
    clase, _ = probar(app_dsn, "UPDATE tenants SET nombre_bufete='x'"
                      " WHERE id=%s", (ids["SIN"],))
    ok("ni renombrarlo", clase, "InsufficientPrivilege")
    clase, _ = probar(app_dsn, "INSERT INTO tenants(id,slug,nombre_bufete)"
                      " VALUES(gen_random_uuid(),'colado','COLADO')")
    ok("ni crear uno nuevo", clase, "InsufficientPrivilege")

    print("\n=== 4. La evidencia sigue inmutable, ni para el rol admin")
    clase, _ = probar(admin, "DELETE FROM tenants WHERE id=%s", (ids["CON"],))
    ok("un bufete CON aprobaciones no se borra ni con el rol admin", clase,
       "ForeignKeyViolation")
    with psycopg.connect(admin, autocommit=True) as c:
        n = c.execute("SELECT count(*) FROM aprobaciones WHERE tenant_id=%s",
                      (ids["CON"],)).fetchone()[0]
    ok("y la aprobacion sigue ahi (el rechazo no fue una tabla vacia)", n, 1)

    print("\n=== 5. EL CONTROL QUE PUEDE ROMPER EL LOGIN")
    # La migracion revoca escritura sobre tenants pero CONSERVA el SELECT. Si se
    # fuera de mas, el login corregido no puede resolver el bufete y vuelve al
    # 401 que este PR arreglo. Se prueba por el adaptador REAL, no por SQL.
    store = al.PostgresAlmacen(app_dsn)
    slug_con = "borr-" + ids["CON"][:8]
    par = store.usuario_por_email("b@borrado.invalid", slug_con)
    ok("el adaptador todavia resuelve el bufete por slug", par is not None, True)
    if par:
        ok("y devuelve el usuario del tenant correcto", par[0].tenant_id,
           ids["CON"])
        ok("con su hash verificable",
           al.verificar_password("borrado-only-x", par[1]), True)

    print("\n=== 6. Limpieza de lo que SE PUEDE limpiar")
    # El bufete SIN aprobaciones se borra con el rol admin. El que TIENE
    # aprobaciones queda, a proposito: es la decision de este PR.
    with psycopg.connect(admin, autocommit=True) as c:
        c.execute("DELETE FROM tenants WHERE id=%s", (ids["SIN"],))
    print("  CONSERVADO: el bufete " + slug_con + " queda en la base porque "
          "tiene aprobaciones. Es la decision, no un descuido.")

    print("\n" + "=" * 66)
    print(json.dumps({"verdes": VERDES, "rojos": ROJOS}))
    print("VERDE" if ROJOS == 0 else "ROJO")
    return 1 if ROJOS else 0


if __name__ == "__main__":
    raise SystemExit(main())
