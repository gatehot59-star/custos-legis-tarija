"""Custos integration audit. Synthetic fixtures, unchanged product source.
Run inside dedicated brain-env directory only. PostgreSQL has private Unix socket,
no TCP listener. API binds loopback ephemeral port. No live corpus calls.
"""
import contextlib, datetime, hashlib, json, os, pathlib, subprocess, sys, threading, time, urllib.request, urllib.error, uuid
ROOT=pathlib.Path('/workspace/custos-integration-20260916-0314')
REPO=ROOT/'repo'; BACK=REPO/'backend'
PG=ROOT/'pgroot/usr/lib/postgresql/17/bin'
ENV=dict(os.environ,LD_LIBRARY_PATH=str(ROOT/'pgroot/usr/lib/x86_64-linux-gnu'))
ENV.pop('DATABASE_URL',None); ENV.pop('DATABASE_URL_APP',None)
SOCK=ROOT/'socket'; DATA=ROOT/'pgdata'
DSN_ADMIN=f'host={SOCK} dbname=postgres user=audit_admin'
DSN_APP=f'host={SOCK} dbname=postgres user=custos_app'
assert ROOT.is_dir() and DATA.is_dir() and SOCK.stat().st_mode & 0o777 == 0o700
sys.path.insert(0,str(BACK))
import psycopg
import api, almacen, plazos
results=[]; baseline=[]; servers=[]; threads=[]
def check(name, actual, expected, scope):
    results.append(dict(name=name,actual=actual,expected=expected,passed=actual==expected,scope=scope))
def run(cmd, log, env=ENV, cwd=BACK):
    with (ROOT/log).open('w') as out:
        cp=subprocess.run([str(x) for x in cmd],stdout=out,stderr=subprocess.STDOUT,env=env,cwd=cwd,timeout=90)
    return cp.returncode
class SyntheticCorpus:
    def buscar(self,q,limit=10):
        return {'total_pasajes':0,'resultados':[]}
def request(port,method,path,body=None,token=None):
    data=json.dumps(body).encode() if body is not None else None
    req=urllib.request.Request(f'http://127.0.0.1:{port}{path}',method=method,data=data)
    if data is not None: req.add_header('Content-Type','application/json')
    if token: req.add_header('Authorization','Bearer '+token)
    try:
        with urllib.request.urlopen(req,timeout=10) as r: return r.status,json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code,json.loads(e.read())
started=False
report={'machine':'brain-env through MUDH build.run','root':str(ROOT),'python':sys.version,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':results,'baselines':baseline,'scope':'real PostgreSQL and real HTTP; synthetic corpus; no external actions executed'}
try:
    with (DATA/'postgresql.conf').open('a') as f:
        f.write("\nlisten_addresses = ''\nunix_socket_directories = '"+str(SOCK)+"'\nunix_socket_permissions = 0700\nshared_buffers = '32MB'\nmax_connections = 20\n")
    rc=run([PG/'pg_ctl','-D',DATA,'-l',ROOT/'postgres.log','-w','start'],'pg_start.log')
    if rc: raise RuntimeError('postgres startup failed; see pg_start.log')
    started=True
    with psycopg.connect(DSN_ADMIN,autocommit=True) as c:
        report['postgres']=c.execute('select version()').fetchone()[0]
        report['listen_addresses']=c.execute('show listen_addresses').fetchone()[0]
        report['socket_directory']=c.execute('show unix_socket_directories').fetchone()[0]
        c.execute((REPO/'infra/init.sql').read_text(),prepare=False)
        report['app_role']=c.execute("select rolname,rolsuper,rolbypassrls from pg_roles where rolname='custos_app'").fetchone()
        report['rls_tables']=c.execute("select relname,relrowsecurity,relforcerowsecurity from pg_class join pg_namespace n on n.oid=relnamespace where n.nspname='public' and relkind='r' order by relname").fetchall()
    report['source_revision']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    report['source_sha256']={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(BACK.glob('*.py'))}
    report['source_sha256']['infra/init.sql']=hashlib.sha256((REPO/'infra/init.sql').read_bytes()).hexdigest()
    ev=dict(ENV,DATABASE_URL=DSN_ADMIN,DATABASE_URL_APP=DSN_APP)
    for name in ['test_api.py','guard_esquema.py','test_rls.py','test_plazos.py']:
        rc=run([sys.executable,BACK/name],name+'.log',env=ev)
        baseline.append({'suite':name,'exit_code':rc,'log':name+'.log','tail':(ROOT/(name+'.log')).read_text()[-1500:]})
    ids={k:str(uuid.uuid4()) for k in ['A','B','UA','UB']}
    password='fixture-only-793-password'
    with psycopg.connect(DSN_ADMIN,autocommit=True) as c:
        for label in ['A','B']:
            c.execute('insert into tenants(id,slug,nombre_bufete) values (%s,%s,%s)',(ids[label],'audit-'+ids[label], 'SYNTHETIC '+label))
            c.execute('insert into users(id,tenant_id,email,password_hash,nombre_completo,rol,matricula_cab) values(%s,%s,%s,%s,%s,%s,%s)',(ids['U'+label],ids[label],label.lower()+'@audit.invalid',almacen.hash_password(password),'SYNTHETIC '+label,'socio','TEST-'+label))
        report['seeded_active_users']=c.execute('select count(*) from users where id=any(%s::uuid[])',([ids['UA'],ids['UB']],)).fetchone()[0]
    store=almacen.PostgresAlmacen(DSN_APP)
    app=api.App(almacen=store,corpus=SyntheticCorpus())
    # Positive direct SQL controls prove data/password correct without weakening RLS.
    with psycopg.connect(DSN_APP) as c:
        report['current_user']=c.execute('select current_user').fetchone()[0]
        report['users_without_tenant']=c.execute('select count(*) from users').fetchone()[0]
        c.execute('select app.set_tenant(%s)',(ids['A'],))
        row=c.execute('select password_hash from users where id=%s',(ids['UA'],)).fetchone()
        check('fixture password is valid inside its tenant',almacen.verificar_password(password,row[0]),True,'PostgreSQL fixture control')
    with (ROOT/'http.log').open('w',buffering=1) as httpout,contextlib.redirect_stdout(httpout):
        srv=api.servir(app,'127.0.0.1',0); servers.append(srv)
        t=threading.Thread(target=srv.serve_forever,daemon=True); t.start(); threads.append(t)
        port=srv.server_address[1]; report['http_port']=port
        status,body=request(port,'POST','/sesion',{'email':'a@audit.invalid','password':password})
        check('valid login via HTTP and PostgresAlmacen',status,200,'full login path')
        report['valid_login_response']={'status':status,'body':body}
        status,_=request(port,'POST','/sesion',{'email':'a@audit.invalid','password':'bad'})
        check('wrong password rejected',status,401,'full login path')
        status,_=request(port,'GET','/casos')
        check('unauthenticated cases blocked',status,401,'full HTTP path')
        # Login is NOT fixed or bypassed in DB. Inject sessions only for downstream tests.
        # These are component integration tests, not successful end-to-end login.
        sessions={label:app.sesiones.abrir(almacen.Usuario(ids['U'+label],ids[label],label.lower()+'@audit.invalid','Synthetic '+label,'socio','TEST-'+label)) for label in ['A','B']}
        token=sessions['A'].token
        status,case=request(port,'POST','/casos',{'nro_expediente':'AUDIT-793','juzgado':'Juzgado sintetico','materia':'civil'},token)
        check('create case through HTTP and PostgreSQL',status,201,'downstream with injected synthetic session')
        cid=case.get('id')
        if not cid: raise RuntimeError('case creation failed: '+str(case))
        status,cases=request(port,'GET','/casos',token=token)
        check('tenant A sees own case',any(x['id']==cid for x in cases.get('casos',[])),True,'HTTP + PostgreSQL with synthetic session')
        status,cases=request(port,'GET','/casos',token=sessions['B'].token)
        check('tenant B does not see A case',any(x['id']==cid for x in cases.get('casos',[])),False,'HTTP + PostgreSQL with synthetic session')
        content='SYNTHETIC MEMORIAL 793'
        payload={'tipo':'presentar_escrito','contenido':content,'case_id':cid}
        status,_=request(port,'POST','/acciones/externa',payload,token)
        check('no approval blocks external authorization',status,403,'HTTP + PostgreSQL with synthetic session')
        status,_=request(port,'POST','/aprobar',payload,token)
        check('approval persists in PostgreSQL',status,201,'HTTP + PostgreSQL with synthetic session')
        status,body=request(port,'POST','/acciones/externa',payload,token)
        check('approved content authorized but not executed',body.get('estado'),'AUTORIZADA_PERO_NO_EJECUTADA','HTTP + PostgreSQL with synthetic session')
        status,_=request(port,'POST','/acciones/externa',dict(payload,contenido=content+' CHANGED'),token)
        check('modified content blocked',status,403,'HTTP + PostgreSQL with synthetic session')
        status,_=request(port,'POST','/acciones/externa',payload,sessions['B'].token)
        check('other tenant cannot reuse approval',status,403,'HTTP + PostgreSQL with synthetic session')
        time.sleep(.02)
        status,_=request(port,'POST','/aprobar',dict(payload,decision='rechazado'),token)
        check('later rejection persists',status,201,'HTTP + PostgreSQL with synthetic session')
        status,body=request(port,'POST','/acciones/externa',payload,token)
        check('later rejection revokes old authorization',status,403,'HTTP + PostgreSQL with synthetic session')
        report['after_rejection_response']={'status':status,'body':body}
        with psycopg.connect(DSN_ADMIN) as c:
            report['approval_order']=c.execute('select decision,creado_en from aprobaciones where tenant_id=%s order by creado_en desc',(ids['A'],)).fetchall()
        status,_=request(port,'GET','/buscar?q=CANARIO_AUDITORIA_793',token=token)
        check('search path responds with synthetic corpus',status,200,'real HTTP/store, fake corpus')
        srv.shutdown(); srv.server_close(); t.join(timeout=3)
        servers.clear(); threads.clear()
    log=(ROOT/'http.log').read_text()
    check('search text absent from HTTP log','CANARIO_AUDITORIA_793' in log,False,'actual product HTTP handler')
    report['query_log_lines']=[x for x in log.splitlines() if 'CANARIO_AUDITORIA_793' in x]
    cal=plazos.CalendarioJudicial(); cal.declarar_cubierto(2026); cal.declarar_cubierto(2027)
    x=plazos.computo_detallado(datetime.date(2026,9,11),3,plazos.Materia.PENAL,medida_cautelar=True,calendario=cal)
    check('penal cautelar starts next calendar day, declared contract',x.vencimiento.date().isoformat(),'2026-09-14','actual engine; synthetic calendar, not legal validation')
    report['penal_actual_trace']=[{**d,'fecha':d['fecha'].isoformat()} for d in x.detalle]
    check('tracked product source unchanged',subprocess.run(['git','diff','--exit-code','HEAD','--','backend','infra'],cwd=REPO,capture_output=True).returncode,0,'git diff')
except Exception as e:
    import traceback
    report['harness_error']=traceback.format_exc()
finally:
    for srv in servers: srv.shutdown(); srv.server_close()
    for t in threads: t.join(timeout=3)
    if started:
        report['pg_stop_rc']=run([PG/'pg_ctl','-D',DATA,'-m','fast','-w','stop'],'pg_stop.log')
        report['pg_status_after_stop_rc']=run([PG/'pg_ctl','-D',DATA,'status'],'pg_status.log')
    report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    report['summary']={'passed':sum(x['passed'] for x in results),'failed':sum(not x['passed'] for x in results),'completed_without_harness_error':'harness_error' not in report}
    (ROOT/'integration-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str))
    print(json.dumps(report,ensure_ascii=False,indent=2,default=str))
sys.exit(2 if 'harness_error' in report else (1 if report['summary']['failed'] else 0))
