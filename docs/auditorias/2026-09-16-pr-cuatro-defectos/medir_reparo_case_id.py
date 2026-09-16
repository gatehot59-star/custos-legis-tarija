"""Mide el reparo 1 de Sol contra el gate REAL, no leyendo el codigo.

Su hallazgo estatico: `aprobaciones(tenant_id, case_id)` filtra por caso solo si
el argumento es truthy, y `exigir_aprobacion()` no vuelve a exigir igualdad de
`case_id`. Entonces una peticion SIN caso podria heredar una aprobacion atada a
un caso concreto.

Tres preguntas, y cada una tiene que dar distinto para que el instrumento sirva:
  A. misma aprobacion, MISMO caso        -> 200 (control positivo)
  B. misma aprobacion, OTRO caso         -> deberia 403
  C. misma aprobacion, SIN caso          -> deberia 403

Si las tres dieran 200 con `case_id` nulo en todas, el instrumento NO
discriminaria: por eso VERIFICA que los dos casos se crearon antes de concluir.
Ese chequeo esta porque el primer intento de este medidor se corrio por un
transporte que se comio el campo `nro_expediente`, los casos salieron None y las
tres respuestas dieron 200 por la razon equivocada. Un 200 con el sujeto vacio no
mide un gate, mide un payload roto.

Cluster de prueba desechable. No produccion.
"""
import contextlib
import io
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
                    else '/workspace/custos-integration-20260916-0314')
REPO = ROOT / 'repo'
BACK = REPO / 'backend'
PG = ROOT / 'pgroot/usr/lib/postgresql/17/bin'
ENV = dict(os.environ,
           LD_LIBRARY_PATH=str(ROOT / 'pgroot/usr/lib/x86_64-linux-gnu'))
SOCK = ROOT / 'socket'
DATA = ROOT / 'pgdata'
A = f'host={SOCK} dbname=postgres user=audit_admin'
P = f'host={SOCK} dbname=postgres user=custos_app'
sys.path.insert(0, str(BACK))
SAL = sys.stdout
out = {}


def di(t):
    print(t, file=SAL, flush=True)


subprocess.run([str(PG / 'pg_ctl'), '-D', str(DATA), '-l',
                str(ROOT / 'pg-reparo.log'), '-w', 'start'],
               env=ENV, capture_output=True, timeout=90)
try:
    import psycopg

    import almacen as al
    import api
    t1, u1 = str(uuid.uuid4()), str(uuid.uuid4())
    slug = 'rep-' + t1[:8]
    pw = 'reparo-' + uuid.uuid4().hex[:8]
    with psycopg.connect(A, autocommit=True) as c:
        c.execute((REPO / 'infra/init.sql').read_text(), prepare=False)
        c.execute('INSERT INTO tenants(id,slug,nombre_bufete) VALUES(%s,%s,%s)',
                  (t1, slug, 'REPARO'))
        c.execute('INSERT INTO users(id,tenant_id,email,password_hash,'
                  'nombre_completo,rol,matricula_cab)'
                  ' VALUES(%s,%s,%s,%s,%s,%s,%s)',
                  (u1, t1, 'rep@x.invalid', al.hash_password(pw), 'REPARO',
                   'socio', 'REP-1'))

    store = al.PostgresAlmacen(P)
    corpus = type('C', (), {'buscar': lambda s, q, limit=10: {
        'total_pasajes': 0, 'resultados': []}})()
    app = api.App(almacen=store, corpus=corpus)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        srv = api.servir(app, '127.0.0.1', 0)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        port = srv.server_address[1]

        def pedir(m, ruta, cuerpo=None, tok=None):
            d = json.dumps(cuerpo).encode() if cuerpo is not None else None
            r = urllib.request.Request(f'http://127.0.0.1:{port}{ruta}',
                                       method=m, data=d)
            if d is not None:
                r.add_header('Content-Type', 'application/json')
            if tok:
                r.add_header('Authorization', 'Bearer ' + tok)
            try:
                with urllib.request.urlopen(r, timeout=15) as x:
                    return x.status, json.loads(x.read())
            except urllib.error.HTTPError as e:
                try:
                    return e.code, json.loads(e.read())
                except Exception:
                    return e.code, {}

        st, cu = pedir('POST', '/sesion', {'bufete': slug,
                                           'email': 'rep@x.invalid',
                                           'password': pw})
        out['login'] = st
        tok = cu.get('token')
        st1, caso1 = pedir('POST', '/casos', {'nro_expediente': 'REP-C1',
                                              'juzgado': 'Juzgado',
                                              'materia': 'civil'}, tok)
        st2, caso2 = pedir('POST', '/casos', {'nro_expediente': 'REP-C2',
                                              'juzgado': 'Juzgado',
                                              'materia': 'civil'}, tok)
        c1, c2 = caso1.get('id'), caso2.get('id')
        out['casos_creados'] = [st1, st2]
        out['case_ids'] = [c1, c2]
        # GUARD DEL INSTRUMENTO: sin dos casos distintos y no nulos, las tres
        # preguntas de abajo no se pueden distinguir y no se concluye nada.
        out['instrumento_valido'] = bool(c1 and c2 and c1 != c2)

        cont = 'MEMORIAL REPARO ' + uuid.uuid4().hex[:6]
        st, _ = pedir('POST', '/aprobar',
                      {'tipo': 'presentar_escrito', 'contenido': cont,
                       'case_id': c1, 'decision': 'aprobado',
                       'fundamento': 'reparo'}, tok)
        out['aprobacion_atada_al_caso1'] = st

        st, _ = pedir('POST', '/acciones/externa',
                      {'tipo': 'presentar_escrito', 'contenido': cont,
                       'case_id': c1}, tok)
        out['A_mismo_caso'] = {'obtenido': st, 'esperado': 200}
        st, _ = pedir('POST', '/acciones/externa',
                      {'tipo': 'presentar_escrito', 'contenido': cont,
                       'case_id': c2}, tok)
        out['B_OTRO_caso'] = {'obtenido': st, 'esperado': 403}
        st, _ = pedir('POST', '/acciones/externa',
                      {'tipo': 'presentar_escrito', 'contenido': cont}, tok)
        out['C_SIN_caso'] = {'obtenido': st, 'esperado': 403}
        srv.shutdown()
        srv.server_close()

    if out['instrumento_valido']:
        out['veredicto'] = {
            'reparo_de_sol_confirmado':
                out['B_OTRO_caso']['obtenido'] == 200
                or out['C_SIN_caso']['obtenido'] == 200,
            'hereda_de_otro_caso': out['B_OTRO_caso']['obtenido'] == 200,
            'hereda_sin_caso': out['C_SIN_caso']['obtenido'] == 200,
        }
    else:
        out['veredicto'] = 'NO MEDIDO: los casos no se crearon, el instrumento ' \
                           'no discrimina'
finally:
    subprocess.run([str(PG / 'pg_ctl'), '-D', str(DATA), '-m', 'fast', '-w',
                    'stop'], env=ENV, capture_output=True)
    di(json.dumps(out, ensure_ascii=False, indent=2, default=str))
