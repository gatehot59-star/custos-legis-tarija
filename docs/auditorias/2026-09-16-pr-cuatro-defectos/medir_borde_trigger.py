"""Mide el borde del trigger de inmutabilidad ANTES de decidir que hacer.

Se commitea antes de correrlo. La pregunta no es "molesta la limpieza": es
QUIEN puede borrar QUE, porque `public.tenants` es la unica tabla de inquilino
que NO tiene RLS ("la administra el servicio, no un inquilino", dice el
esquema) y el rol de la aplicacion recibe
`GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES`.

Cluster de prueba desechable. NO produccion. No se desactiva ningun trigger.
"""
import json
import os
import pathlib
import subprocess
import sys
import uuid

ROOT = pathlib.Path('/workspace/custos-integration-20260916-0314')
REPO = ROOT / 'repo'
BACK = REPO / 'backend'
PG = ROOT / 'pgroot/usr/lib/postgresql/17/bin'
ENV = dict(os.environ, LD_LIBRARY_PATH=str(ROOT / 'pgroot/usr/lib/x86_64-linux-gnu'))
SOCK = ROOT / 'socket'
DATA = ROOT / 'pgdata'
A = f'host={SOCK} dbname=postgres user=audit_admin'
P = f'host={SOCK} dbname=postgres user=custos_app'
sys.path.insert(0, str(BACK))
out = {}

subprocess.run([str(PG / 'pg_ctl'), '-D', str(DATA), '-l', str(ROOT / 'pg-mide.log'),
                '-w', 'start'], env=ENV, capture_output=True, timeout=90)
try:
    import psycopg

    import almacen as al
    t1, t2, u1 = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    with psycopg.connect(A, autocommit=True) as c:
        c.execute((REPO / 'infra/init.sql').read_text(), prepare=False)
        for tid, n in ((t1, 'MIDE-1'), (t2, 'MIDE-2')):
            c.execute('INSERT INTO tenants(id,slug,nombre_bufete) VALUES(%s,%s,%s)',
                      (tid, 'mide-' + tid[:8], n))
        c.execute('INSERT INTO users(id,tenant_id,email,password_hash,'
                  'nombre_completo,rol,matricula_cab) VALUES(%s,%s,%s,%s,%s,%s,%s)',
                  (u1, t1, 'm@mide.invalid', al.hash_password('x'), 'MIDE',
                   'socio', 'M-1'))
        c.execute('INSERT INTO cases(id,tenant_id,nro_expediente,juzgado,materia)'
                  " VALUES(gen_random_uuid(),%s,'M-1','J','civil')", (t1,))
        cid = c.execute('SELECT id FROM cases WHERE tenant_id=%s', (t1,)).fetchone()[0]
        c.execute('INSERT INTO aprobaciones(tenant_id,case_id,usuario_id,matricula,'
                  "tipo,sha256_entrada,decision) VALUES(%s,%s,%s,'M-1',"
                  "'presentar_escrito',%s,'aprobado')", (t1, cid, u1, 'a' * 64))

    def prueba(dsn, sql, args=()):
        try:
            with psycopg.connect(dsn, autocommit=True) as c:
                c.execute(sql, args)
            return 'PASO'
        except Exception as e:  # noqa: BLE001
            return type(e).__name__ + ': ' + str(e).splitlines()[0][:110]

    # El tenant SIN aprobaciones es el control positivo: si tampoco se puede
    # borrar, el resultado del otro no dice nada sobre el trigger.
    out['app_borra_tenant_SIN_aprobaciones'] = prueba(
        P, 'DELETE FROM tenants WHERE id=%s', (t2,))
    out['app_borra_tenant_CON_aprobaciones'] = prueba(
        P, 'DELETE FROM tenants WHERE id=%s', (t1,))
    out['admin_borra_tenant_CON_aprobaciones'] = prueba(
        A, 'DELETE FROM tenants WHERE id=%s', (t1,))
    out['app_borra_aprobacion_directo'] = prueba(
        P, 'DELETE FROM aprobaciones WHERE tenant_id=%s', (t1,))
    out['app_update_aprobacion'] = prueba(
        P, "UPDATE aprobaciones SET decision='rechazado' WHERE tenant_id=%s", (t1,))

    with psycopg.connect(A, autocommit=True) as c:
        out['tenants_rls'] = c.execute(
            "SELECT relrowsecurity, relforcerowsecurity FROM pg_class"
            " WHERE relname='tenants'").fetchone()
        out['grants_app_tenants'] = c.execute(
            "SELECT privilege_type FROM information_schema.role_table_grants"
            " WHERE grantee='custos_app' AND table_name='tenants' ORDER BY 1"
        ).fetchall()
        out['fk_aprob_tenant'] = c.execute(
            "SELECT conname, confdeltype FROM pg_constraint"
            " WHERE conrelid='public.aprobaciones'::regclass"
            " AND confrelid='public.tenants'::regclass").fetchall()
        out['tenants_vivos'] = c.execute(
            'SELECT count(*) FROM tenants WHERE id=ANY(%s::uuid[])',
            ([t1, t2],)).fetchone()[0]
finally:
    subprocess.run([str(PG / 'pg_ctl'), '-D', str(DATA), '-m', 'fast', '-w', 'stop'],
                   env=ENV, capture_output=True)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
