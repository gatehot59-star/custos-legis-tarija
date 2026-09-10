#!/usr/bin/env python3
"""Aislamiento entre bufetes. **El test mas importante del sistema.**

Si este test falla, un bufete puede leer los expedientes de otro. Eso no es un
bug: es el fin del producto.

CORRE CONTRA POSTGRESQL REAL. RLS es una funcion del planificador del motor:
un mock no ejecuta el planificador, asi que un test de RLS sobre un mock da
verde siempre y no prueba nada.

--------------------------------------------------------------------------------
DEFECTO PROPIO CORREGIDO EN LA v2, y es el mas instructivo del archivo:

  La v1 sembraba bufetes con UUID nuevos en CADA corrida y no limpiaba. El paso
  de sabotaje del CI corria el test una segunda vez, habia 4 casos en la tabla,
  y mi contra-test "el superusuario ve los 2 casos" fallaba POR EL CONTEO.

  Resultado: el sabotaje imprimio "OK: la fuga de checkpoints fue detectada" y
  NO habia detectado ninguna fuga. El test fallaba por otra razon.
  **Un control que da el veredicto correcto por la razon equivocada no es un
  control.** Ya me habia pasado con el N3 de un falsador de proot.

  Y de paso mordio el otro clasico: `grep 'ROJO ' archivo` sin match sale con
  codigo 1, y con `bash -e` eso mato el paso. Un grep vacio no es un error.

  Dos arreglos:
   1. El test LIMPIA sus propios bufetes al entrar y al salir, y sus asserts
      cuentan SOLO sus filas (por los UUID que el mismo creo), no la tabla.
   2. Cada rojo lleva una ETIQUETA estable (`[FUGA-CKPT]`, `[CONTRA-TEST]`...)
      para que el sabotaje del CI pueda exigir el rojo ESPERADO y no cualquiera.
--------------------------------------------------------------------------------

Uso:
  DATABASE_URL=postgresql://superuser...  DATABASE_URL_APP=postgresql://app...
  python3 test_rls.py
"""
import os
import sys
import uuid

import psycopg

URL_APP = os.environ["DATABASE_URL_APP"]   # rol custos_app, SIN bypassrls
URL_SUPER = os.environ["DATABASE_URL"]     # superusuario, solo para sembrar

fallos: list[tuple[str, str]] = []
verdes = 0


def chk(etiqueta, nombre, obtenido, esperado):
    """etiqueta = identificador estable del rojo, para que el CI lo exija."""
    global verdes
    if obtenido == esperado:
        verdes += 1
        print(f"  OK   {nombre}")
    else:
        fallos.append((etiqueta, nombre))
        print(f"  ROJO {etiqueta} {nombre}: obtuve {obtenido!r}, esperaba {esperado!r}")


A = str(uuid.uuid4())
B = str(uuid.uuid4())
CASE_A = str(uuid.uuid4())
CASE_B = str(uuid.uuid4())
SECRETO_A = "MEMORIAL SECRETO DEL BUFETE A " + A[:8]
SECRETO_B = "MEMORIAL SECRETO DEL BUFETE B " + B[:8]


def limpiar(cur):
    """Borra SOLO lo que este test creo. El resto de la tabla no se toca."""
    cur.execute("DELETE FROM tenants WHERE id = ANY(%s)", ([A, B],))


print("=== 0. Sembrando dos bufetes (idempotente) ===")
with psycopg.connect(URL_SUPER, autocommit=True) as cx:
    with cx.cursor() as cur:
        limpiar(cur)
        cur.execute(
            "INSERT INTO tenants (id, slug, nombre_bufete) VALUES (%s,%s,%s),(%s,%s,%s)",
            (A, "t-" + A[:8], "Bufete Garcia", B, "t-" + B[:8], "Estudio Mamani"))
        for tid, cid, jz, mat, sec in (
                (A, CASE_A, "Juzgado Civil 1 Tarija", "civil", SECRETO_A),
                (B, CASE_B, "Juzgado Penal 2 Tarija", "penal", SECRETO_B)):
            cur.execute(
                "INSERT INTO cases (id, tenant_id, juzgado, materia, nro_expediente)"
                " VALUES (%s,%s,%s,%s,%s)", (cid, tid, jz, mat, "100/2026"))
            # El checkpoint guarda el estado del grafo: memorial + docs privados.
            # Es lo mas sensible del sistema entero.
            cur.execute(
                "INSERT INTO cl_checkpoints"
                " (tenant_id, case_id, thread_id, checkpoint_id, estado)"
                " VALUES (%s,%s,%s,%s,%s::jsonb)",
                (tid, cid, f"{tid}:{cid}", "ckpt-1",
                 psycopg.types.json.Json(
                     {"borrador_memorial": sec,
                      "contexto_caso_privado": "prueba documental confidencial"}
                 ).obj and __import__("json").dumps(
                     {"borrador_memorial": sec,
                      "contexto_caso_privado": "prueba documental confidencial"})))
            cur.execute(
                "INSERT INTO documents"
                " (tenant_id, case_id, tipo_documento, nombre_archivo, sha256, texto_crudo)"
                " VALUES (%s,%s,'prueba_documental','p.pdf',%s,'texto crudo privado')",
                (tid, cid, "h" + tid[:20]))
print("  sembrado (y limpiado lo de corridas anteriores)")


def como(tenant, sql, params=()):
    """Ejecuta como el rol de la app, con el tenant fijado en la transaccion."""
    with psycopg.connect(URL_APP) as cx:
        with cx.cursor() as cur:
            cur.execute("SELECT app.set_tenant(%s)", (tenant,))
            cur.execute(sql, params)
            return cur.fetchall()


print("\n=== 1. POSITIVA: cada bufete ve lo suyo ===")
chk("POS", "A ve su caso",
    [str(r[0]) for r in como(A, "SELECT id FROM cases WHERE id=%s", (CASE_A,))],
    [CASE_A])
chk("POS", "B ve su caso",
    [str(r[0]) for r in como(B, "SELECT id FROM cases WHERE id=%s", (CASE_B,))],
    [CASE_B])

print("\n=== 2. NEGATIVA en cases ===")
chk("FUGA-CASES", "A NO ve el caso de B",
    len(como(A, "SELECT id FROM cases WHERE id=%s", (CASE_B,))), 0)
vis = {str(r[0]) for r in como(A, "SELECT tenant_id FROM cases")}
chk("FUGA-CASES", "el tenant de B no aparece para A", B in vis, False)

print("\n=== 3. NEGATIVA en documents ===")
chk("FUGA-DOCS", "A no ve documentos de B",
    len(como(A, "SELECT id FROM documents WHERE tenant_id=%s", (B,))), 0)

print("\n=== 4. EL D3 DE FABLE: los CHECKPOINTS del grafo ===")
# En el diseno original esta tabla no tenia tenant_id ni RLS, asi que el bufete
# B podia leer el borrador de A aunque `cases` estuviera perfectamente aislado.
# El assert se hace por el CONTENIDO del secreto, no por conteos: un conteo
# puede dar 0 por RLS o por tabla vacia, y son cosas distintas.
todos_b = " ".join(str(r[0]) for r in como(B, "SELECT estado FROM cl_checkpoints"))
chk("FUGA-CKPT", "B NO ve el memorial secreto de A", SECRETO_A in todos_b, False)
chk("FUGA-CKPT", "B SI ve el suyo (el RLS no lo dejo ciego)", SECRETO_B in todos_b, True)
chk("FUGA-CKPT", "consulta dirigida al checkpoint de A da vacio",
    len(como(B, "SELECT id FROM cl_checkpoints WHERE tenant_id=%s", (A,))), 0)

print("\n=== 5. WITH CHECK: escribir con tenant ajeno se rechaza ===")
try:
    como(A, "INSERT INTO cases (tenant_id, juzgado, materia)"
            " VALUES (%s,'Juzgado Falso','civil') RETURNING id", (B,))
    chk("WITH-CHECK", "insercion cross-tenant bloqueada", "NO bloqueo", "bloqueada")
except Exception as e:
    m = str(e).lower()
    chk("WITH-CHECK", "insercion cross-tenant bloqueada",
        ("policy" in m or "row-level" in m or "permission" in m), True)

print("\n=== 6. Trigger: thread_id sin su tenant se rechaza ===")
try:
    como(A, "INSERT INTO cl_checkpoints (tenant_id, thread_id, checkpoint_id, estado)"
            " VALUES (%s,'hilo-sin-tenant','c9','{}'::jsonb) RETURNING id", (A,))
    chk("TRIGGER-THREAD", "thread_id sin tenant rechazado", "NO rechazo", "rechazado")
except Exception as e:
    chk("TRIGGER-THREAD", "thread_id sin tenant rechazado",
        "convencion violada" in str(e).lower(), True)

print("\n=== 7. Trigger: el texto crudo es inmutable (D1) ===")
try:
    como(A, "UPDATE documents SET texto_crudo='REESCRITO' WHERE tenant_id=%s"
            " RETURNING id", (A,))
    chk("TRIGGER-CRUDO", "reescritura del crudo rechazada", "NO rechazo", "rechazado")
except Exception as e:
    chk("TRIGGER-CRUDO", "reescritura del crudo rechazada",
        "inmutable" in str(e).lower(), True)

print("\n=== 8. Sin tenant fijado no se ve NADA (fail-closed) ===")
# Si alguien olvida el set_tenant, el sistema tiene que quedarse ciego, no
# abrirse. current_tenant_id() da NULL y ninguna fila matchea.
with psycopg.connect(URL_APP) as cx:
    with cx.cursor() as cur:
        cur.execute("SELECT count(*) FROM cases WHERE id = ANY(%s)", ([CASE_A, CASE_B],))
        chk("FAIL-CLOSED", "sin set_tenant, cero filas", cur.fetchone()[0], 0)

print("\n=== 9. CONTRA-TEST DEL INSTRUMENTO ===")
# Si todo lo de arriba diera verde porque las tablas estan VACIAS, este test
# seria un instrumento incapaz de dar rojo. El superusuario ignora RLS: tiene
# que ver las 2 filas que sembre. Cuenta SOLO las mias (por UUID), asi que no
# se rompe si la tabla tiene datos de otras corridas.
with psycopg.connect(URL_SUPER) as cx:
    with cx.cursor() as cur:
        cur.execute("SELECT count(*) FROM cases WHERE id = ANY(%s)", ([CASE_A, CASE_B],))
        chk("CONTRA-TEST", "el superusuario SI ve mis 2 casos", cur.fetchone()[0], 2)
        cur.execute("SELECT count(*) FROM cl_checkpoints WHERE tenant_id = ANY(%s)",
                    ([A, B],))
        chk("CONTRA-TEST", "y mis 2 checkpoints", cur.fetchone()[0], 2)
        cur.execute("SELECT count(*) FROM cl_checkpoints"
                    " WHERE tenant_id=%s AND estado::text LIKE %s", (A, f"%{SECRETO_A}%"))
        chk("CONTRA-TEST", "el secreto de A existe de verdad en la tabla",
            cur.fetchone()[0], 1)

print("\n=== 10. El rol de la app NO tiene BYPASSRLS ===")
# Con BYPASSRLS todo lo anterior es decorativo y daria verde igual.
with psycopg.connect(URL_SUPER) as cx:
    with cx.cursor() as cur:
        cur.execute("SELECT rolbypassrls FROM pg_roles WHERE rolname='custos_app'")
        chk("BYPASSRLS", "custos_app sin bypassrls", cur.fetchone()[0], False)

print("\n=== 11. Limpieza ===")
with psycopg.connect(URL_SUPER, autocommit=True) as cx:
    with cx.cursor() as cur:
        limpiar(cur)
print("  borrados los bufetes de prueba")

print(f"\n{'='*64}")
print(f"verdes: {verdes} | rojos: {len(fallos)}")
if fallos:
    # Las etiquetas van en una linea propia para que el CI pueda exigir
    # el rojo ESPERADO y no conformarse con cualquiera.
    print("ETIQUETAS_ROJAS: " + ",".join(sorted({e for e, _ in fallos})))
    for e, n in fallos:
        print(f"  ROJO {e} {n}")
    sys.exit(1)
print("VERDE: aislamiento entre bufetes verificado, checkpoints incluidos")
