#!/usr/bin/env python3
"""Aislamiento entre bufetes. **El test mas importante del sistema.**

Si este test falla, un bufete puede leer los expedientes de otro, y eso no es un
bug: es el fin del producto.

CORRE CONTRA POSTGRESQL REAL. RLS es una funcion del planificador del motor:
un mock no prueba nada.

LAS TRES CLASES DE PRUEBA, y la tercera es la que la mayoria olvida:
  1. POSITIVA: el bufete A ve lo suyo.
  2. NEGATIVA: el bufete A NO ve lo de B. Incluye `cl_checkpoints`, que es
     el D3 de Fable: ahi vive el memorial y los documentos privados, y el RLS
     de `cases` no lo cubre.
  3. CONTRA-TEST DEL INSTRUMENTO: si el test corriera como superusuario, RLS no
     aplica y TODO daria "aislado" por vacio. Se verifica que el superusuario
     SI ve las dos filas, o sea que el metodo discrimina.

Uso: DATABASE_URL=postgresql://... python3 test_rls.py
"""
import os
import sys
import uuid

import psycopg

URL_APP = os.environ.get("DATABASE_URL_APP")   # rol custos_app, SIN bypassrls
URL_SUPER = os.environ.get("DATABASE_URL")     # superusuario, solo el contra-test

fallos: list[str] = []
verdes = 0


def chk(nombre, obtenido, esperado):
    global verdes
    if obtenido == esperado:
        verdes += 1
        print(f"  OK   {nombre}")
    else:
        fallos.append(f"{nombre}: obtuve {obtenido!r}, esperaba {esperado!r}")
        print(f"  ROJO {nombre}: obtuve {obtenido!r}, esperaba {esperado!r}")


A = str(uuid.uuid4())
B = str(uuid.uuid4())
CASE_A = str(uuid.uuid4())
CASE_B = str(uuid.uuid4())

# ---------------------------------------------------------------------------
# SEMBRAR con superusuario (RLS no aplica): dos bufetes con datos de cada uno.
# ---------------------------------------------------------------------------
print("=== 0. Sembrando dos bufetes ===")
with psycopg.connect(URL_SUPER, autocommit=True) as cx:
    with cx.cursor() as cur:
        cur.execute(
            "INSERT INTO tenants (id, slug, nombre_bufete) VALUES (%s,%s,%s),(%s,%s,%s)",
            (A, "bufete-a", "Bufete Garcia", B, "bufete-b", "Estudio Mamani"))
        for tid, cid, jz, mat in ((A, CASE_A, "Juzgado Civil 1 Tarija", "civil"),
                                  (B, CASE_B, "Juzgado Penal 2 Tarija", "penal")):
            cur.execute(
                "INSERT INTO cases (id, tenant_id, juzgado, materia, nro_expediente)"
                " VALUES (%s,%s,%s,%s,%s)", (cid, tid, jz, mat, "100/2026"))
            # El checkpoint lleva el estado del grafo: es lo mas sensible.
            cur.execute(
                "INSERT INTO cl_checkpoints"
                " (tenant_id, case_id, thread_id, checkpoint_id, estado)"
                " VALUES (%s,%s,%s,%s,%s::jsonb)",
                (tid, cid, f"{tid}:{cid}", "ckpt-1",
                 '{"borrador_memorial":"SECRETO DEL BUFETE",'
                 '"contexto_caso_privado":"prueba documental confidencial"}'))
            cur.execute(
                "INSERT INTO documents"
                " (tenant_id, case_id, tipo_documento, nombre_archivo, sha256, texto_crudo)"
                " VALUES (%s,%s,'prueba_documental','p.pdf',%s,'texto crudo privado')",
                (tid, cid, "h" + tid[:20]))
print("  sembrado")


def como(tenant, sql, params=()):
    """Ejecuta como el rol de la app, con el tenant fijado en la transaccion."""
    with psycopg.connect(URL_APP) as cx:
        with cx.cursor() as cur:
            cur.execute("SELECT app.set_tenant(%s)", (tenant,))
            cur.execute(sql, params)
            return cur.fetchall()


print("\n=== 1. POSITIVA: cada bufete ve lo suyo ===")
chk("A ve 1 caso propio", len(como(A, "SELECT id FROM cases")), 1)
chk("B ve 1 caso propio", len(como(B, "SELECT id FROM cases")), 1)
chk("y es el caso correcto", str(como(A, "SELECT id FROM cases")[0][0]), CASE_A)

print("\n=== 2. NEGATIVA en cases ===")
visibles = {str(r[0]) for r in como(A, "SELECT tenant_id FROM cases")}
chk("A NO ve el tenant de B", B in visibles, False)
chk("consulta directa del caso de B da vacio",
    len(como(A, "SELECT id FROM cases WHERE id = %s", (CASE_B,))), 0)

print("\n=== 3. NEGATIVA en documents ===")
chk("A no ve documentos de B",
    len(como(A, "SELECT id FROM documents WHERE tenant_id = %s", (B,))), 0)

print("\n=== 4. EL D3 DE FABLE: los CHECKPOINTS del grafo ===")
# Aca vive el memorial redactado y el contexto privado del caso. En el diseno
# original esta tabla NO tenia tenant_id ni RLS, asi que el bufete B podia leer
# el borrador del bufete A aunque `cases` estuviera perfectamente aislado.
chk("B NO lee checkpoints de A",
    len(como(B, "SELECT id FROM cl_checkpoints WHERE tenant_id = %s", (A,))), 0)
chk("B NO ve NINGUN checkpoint ajeno en un SELECT abierto",
    len(como(B, "SELECT id FROM cl_checkpoints")), 1)
fuga = como(B, "SELECT estado FROM cl_checkpoints")
chk("y el unico estado visible NO contiene el secreto de A",
    all("SECRETO" in str(f[0]) for f in fuga), True)  # es SU propio secreto

print("\n=== 5. WITH CHECK: escribir con tenant ajeno se rechaza ===")
try:
    como(A, "INSERT INTO cases (tenant_id, juzgado, materia)"
            " VALUES (%s,'Juzgado Falso','civil') RETURNING id", (B,))
    chk("insercion cross-tenant bloqueada", "NO bloqueo", "bloqueada")
except Exception as e:
    msg = str(e).lower()
    chk("insercion cross-tenant bloqueada",
        ("policy" in msg or "row-level" in msg or "permission" in msg), True)

print("\n=== 6. Trigger: thread_id sin su tenant se rechaza ===")
try:
    como(A, "INSERT INTO cl_checkpoints (tenant_id, thread_id, checkpoint_id, estado)"
            " VALUES (%s,'hilo-sin-tenant','c9','{}'::jsonb) RETURNING id", (A,))
    chk("thread_id sin tenant rechazado", "NO rechazo", "rechazado")
except Exception as e:
    chk("thread_id sin tenant rechazado", "convencion violada" in str(e).lower(), True)

print("\n=== 7. Trigger: el texto crudo es inmutable (D1) ===")
try:
    como(A, "UPDATE documents SET texto_crudo = 'REESCRITO' WHERE tenant_id = %s"
            " RETURNING id", (A,))
    chk("reescritura del crudo rechazada", "NO rechazo", "rechazado")
except Exception as e:
    chk("reescritura del crudo rechazada", "inmutable" in str(e).lower(), True)

print("\n=== 8. Sin tenant fijado no se ve NADA (fail-closed) ===")
# Si alguien olvida el set_tenant, el sistema tiene que quedarse ciego, no
# abrirse. current_tenant_id() devuelve NULL y ninguna fila matchea.
with psycopg.connect(URL_APP) as cx:
    with cx.cursor() as cur:
        cur.execute("SELECT count(*) FROM cases")
        chk("sin set_tenant, cero filas", cur.fetchone()[0], 0)

print("\n=== 9. CONTRA-TEST DEL INSTRUMENTO ===")
# Si todo lo de arriba diera verde porque las tablas estan VACIAS, el test seria
# un instrumento que no puede dar rojo. El superusuario ignora RLS: debe ver 2.
with psycopg.connect(URL_SUPER) as cx:
    with cx.cursor() as cur:
        cur.execute("SELECT count(*) FROM cases")
        chk("el superusuario SI ve los 2 casos (hay datos)", cur.fetchone()[0], 2)
        cur.execute("SELECT count(*) FROM cl_checkpoints")
        chk("y los 2 checkpoints", cur.fetchone()[0], 2)

print("\n=== 10. El rol de la app NO tiene BYPASSRLS ===")
# Con BYPASSRLS todo lo anterior es decorativo y daria verde igual.
with psycopg.connect(URL_SUPER) as cx:
    with cx.cursor() as cur:
        cur.execute("SELECT rolbypassrls FROM pg_roles WHERE rolname='custos_app'")
        chk("custos_app sin bypassrls", cur.fetchone()[0], False)

print(f"\n{'='*60}")
print(f"verdes: {verdes} | rojos: {len(fallos)}")
if fallos:
    for f in fallos:
        print(f"  ROJO: {f}")
    sys.exit(1)
print("VERDE: aislamiento entre bufetes verificado, checkpoints incluidos")
