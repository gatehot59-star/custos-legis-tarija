"""FALSADOR del rojo del login: separa 'password mal sembrada' de 'RLS bloquea el SELECT'.

Se commitea ANTES de correrlo, con su criterio adentro, para no poder acomodarlo al
resultado. Cluster de prueba desechable dentro de brain-env. NO toca el producto ni
produccion: al final se verifica git diff y sha256 del backend.

BYPASSRLS se concede y se REVOCA dentro de esta corrida. Es el BRAZO del experimento,
no un arreglo: si con bypass el login pasa a 200, la causa del 401 es la politica RLS
y no la password ni el hash.

Criterio declarado por adelantado:
  el_401_lo_causa_RLS = (control da 401)  Y  (con bypass da 200)
  el check 'wrong password rejected' del instrumento DISCRIMINA solo si, con el login
    roto, la password incorrecta devuelve algo DISTINTO de la correcta.
  reversion_ok = (tras revocar vuelve a 401)  Y  (rolbypassrls es False)
"""
import contextlib, datetime, json, pathlib, subprocess, sys, threading, urllib.request, urllib.error, uuid, hashlib, os
ROOT = pathlib.Path('/workspace/custos-integration-20260916-0314')
REPO = ROOT/'repo'; BACK = REPO/'backend'
PG = ROOT/'pgroot/usr/lib/postgresql/17/bin'
ENV = dict(os.environ, LD_LIBRARY_PATH=str(ROOT/'pgroot/usr/lib/x86_64-linux-gnu'))
ENV.pop('DATABASE_URL', None); ENV.pop('DATABASE_URL_APP', None)
SOCK = ROOT/'socket'; DATA = ROOT/'pgdata'
DSN_ADMIN = f'host={SOCK} dbname=postgres user=audit_admin'
DSN_APP = f'host={SOCK} dbname=postgres user=custos_app'
sys.path.insert(0, str(BACK))
import psycopg
import api, almacen

out = {'instrumento': 'falsador propio del rojo del login', 'root': str(ROOT),
       'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'brazos': []}


def request(port, path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', method='POST', data=data)
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


started = False
try:
    rc = subprocess.run([str(PG/'pg_ctl'), '-D', str(DATA), '-l', str(ROOT/'postgres-falsador.log'), '-w', 'start'],
                        env=ENV, capture_output=True, text=True, timeout=90)
    out['pg_start_rc'] = rc.returncode
    if rc.returncode:
        raise RuntimeError('pg start fallo: ' + rc.stdout + rc.stderr)
    started = True
    tid, uid = str(uuid.uuid4()), str(uuid.uuid4())
    password = 'falsador-only-793-password'
    with psycopg.connect(DSN_ADMIN, autocommit=True) as c:
        c.execute((REPO/'infra/init.sql').read_text(), prepare=False)
        c.execute('insert into tenants(id,slug,nombre_bufete) values (%s,%s,%s)', (tid, 'fals-'+tid, 'FALSADOR'))
        c.execute('insert into users(id,tenant_id,email,password_hash,nombre_completo,rol,matricula_cab)'
                  ' values(%s,%s,%s,%s,%s,%s,%s)',
                  (uid, tid, 'f@falsador.invalid', almacen.hash_password(password), 'FALSADOR', 'socio', 'FALS-1'))
        out['rol_antes'] = c.execute("select rolname,rolsuper,rolbypassrls from pg_roles where rolname='custos_app'").fetchone()

    def medir(etiqueta):
        store = almacen.PostgresAlmacen(DSN_APP)
        corpus = type('C', (), {'buscar': lambda self, q, limit=10: {'total_pasajes': 0, 'resultados': []}})()
        app = api.App(almacen=store, corpus=corpus)
        with (ROOT/('http-falsador-%s.log' % etiqueta)).open('w', buffering=1) as f, contextlib.redirect_stdout(f):
            srv = api.servir(app, '127.0.0.1', 0)
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            port = srv.server_address[1]
            r = {'brazo': etiqueta,
                 'password_correcta': request(port, '/sesion', {'email': 'f@falsador.invalid', 'password': password}),
                 'password_incorrecta': request(port, '/sesion', {'email': 'f@falsador.invalid', 'password': 'no-es'}),
                 'email_inexistente': request(port, '/sesion', {'email': 'nadie@falsador.invalid', 'password': password})}
            srv.shutdown(); srv.server_close()
        with psycopg.connect(DSN_APP) as c:
            r['bypassrls_efectivo'] = c.execute("select rolbypassrls from pg_roles where rolname=current_user").fetchone()[0]
        out['brazos'].append(r)
        return r

    a = medir('control-rol-real')
    with psycopg.connect(DSN_ADMIN, autocommit=True) as c:
        c.execute('alter role custos_app bypassrls')
    b = medir('sabotaje-bypassrls')
    with psycopg.connect(DSN_ADMIN, autocommit=True) as c:
        c.execute('alter role custos_app nobypassrls')
        out['rol_revertido'] = c.execute("select rolname,rolsuper,rolbypassrls from pg_roles where rolname='custos_app'").fetchone()
    c_ = medir('control-tras-revertir')

    out['veredicto'] = {
        'el_401_lo_causa_RLS': a['password_correcta'] == 401 and b['password_correcta'] == 200,
        'el_check_password_incorrecta_discrimina_con_login_roto': a['password_incorrecta'] != a['password_correcta'],
        'reversion_ok': c_['password_correcta'] == 401 and out['rol_revertido'][2] is False,
    }
    with psycopg.connect(DSN_ADMIN, autocommit=True) as c:
        c.execute('delete from users where id=%s', (uid,))
        c.execute('delete from tenants where id=%s', (tid,))
finally:
    if started:
        s = subprocess.run([str(PG/'pg_ctl'), '-D', str(DATA), '-m', 'fast', '-w', 'stop'], env=ENV, capture_output=True, text=True)
        out['pg_stop_rc'] = s.returncode
        st = subprocess.run([str(PG/'pg_ctl'), '-D', str(DATA), 'status'], env=ENV, capture_output=True, text=True)
        out['pg_status_after_stop_rc'] = st.returncode
    out['git_diff_producto'] = subprocess.run(['git', 'diff', '--name-only'], cwd=REPO, capture_output=True, text=True).stdout.strip()
    out['sha256_producto'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(BACK.glob('*.py'))}
    out['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (ROOT/'falsador-login-results.json').write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str))
    claves = ('brazos', 'rol_antes', 'rol_revertido', 'veredicto', 'pg_stop_rc', 'pg_status_after_stop_rc', 'git_diff_producto')
    print(json.dumps({k: out[k] for k in claves if k in out}, ensure_ascii=False, indent=2))
