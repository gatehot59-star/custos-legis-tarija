# Independent HTTP verifier. Stdlib only; no imports from candidate or its tests.
import json,sys,urllib.request,urllib.error,uuid
base=sys.argv[1]
rows=[]
def check(name,actual,expected):
    rows.append(dict(name=name,actual=actual,expected=expected,passed=actual==expected))
def req(method,path,body=None,token=None):
    data=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(base+path,data=data,method=method)
    if data is not None:r.add_header("Content-Type","application/json")
    if token:r.add_header("Authorization","Bearer "+token)
    try:
        with urllib.request.urlopen(r,timeout=5) as x:return x.status,json.loads(x.read())
    except urllib.error.HTTPError as x:return x.code,json.loads(x.read())
try:
    s,b=req("GET","/casos");check("unauthenticated",s,401)
    s,b=req("POST","/sesion",dict(bufete="audit-a",email="same@audit.invalid",password="WRONG"));check("bad_password",s,401)
    s,a=req("POST","/sesion",dict(bufete="audit-a",email="same@audit.invalid",password="SYNTHETIC-ONLY-HTTP-20260916"));check("valid_login_a",s,200)
    ta=a.get("token");check("token_a_present",isinstance(ta,str) and len(ta)>20,True)
    s,b=req("POST","/sesion",dict(bufete="audit-b",email="same@audit.invalid",password="SYNTHETIC-ONLY-HTTP-20260916"));check("valid_login_b",s,200)
    tb=b.get("token");check("tenant_selection",a.get("bufete_id") is not None and a.get("bufete_id")!=b.get("bufete_id"),True)
    if not ta or not tb:raise RuntimeError("no real login tokens; downstream tests not attempted")
    s,c=req("POST","/casos",dict(nro_expediente="PINNED-"+uuid.uuid4().hex,juzgado="Synthetic Court",materia="civil"),ta);check("create_case",s,201)
    cid=c.get("id")
    if not cid:raise RuntimeError("no case id")
    s,c=req("GET","/casos",token=ta);check("own_case_visible",s==200 and any(x.get("id")==cid for x in c.get("casos",[])),True)
    s,c=req("GET","/casos",token=tb);check("other_tenant_hidden",s==200 and all(x.get("id")!=cid for x in c.get("casos",[])),True)
    payload=dict(tipo="presentar_escrito",contenido="SYNTHETIC PINNED CONTENT",case_id=cid)
    s,b=req("POST","/acciones/externa",payload,ta);check("unapproved_blocked",s,403)
    s,b=req("POST","/aprobar",payload,ta);check("approve",s,201)
    s,b=req("POST","/acciones/externa",payload,ta);check("approved_authorized",s,200);check("not_executed",b.get("estado"),"AUTORIZADA_PERO_NO_EJECUTADA")
    omitted=dict(payload);omitted.pop("case_id")
    s,b=req("POST","/acciones/externa",omitted,ta);check("omitted_case_blocked",s,403)
    s,b=req("POST","/acciones/externa",dict(payload,contenido="DIFFERENT"),ta);check("changed_content_blocked",s,403)
    s,b=req("POST","/acciones/externa",payload,tb);check("other_tenant_approval_blocked",s,403)
    s,b=req("POST","/aprobar",dict(payload,decision="rechazado"),ta);check("reject_recorded",s,201)
    s,b=req("POST","/acciones/externa",payload,ta);check("rejection_revokes",s,403)
    s,b=req("GET","/plazo?notificacion=2026-09-11&dias=3&materia=penal&cautelar=true",token=ta)
    check("deadline_http",s,200);check("deadline_date",str(b.get("vencimiento", ""))[:10],"2026-09-14");check("unknown_calendar_not_trusted",b.get("confiable"),False)
    s,b=req("GET","/no-existe?q=PINNED_LOG_CANARY_20260916",token=ta);check("error_path",s,404)
    s,b=req("DELETE","/sesion",token=ta);check("logout",s,200)
    s,b=req("GET","/casos",token=ta);check("closed_session_rejected",s,401)
    error=None
except Exception as exc:error=type(exc).__name__+": "+str(exc)
result=dict(verifier="independent-pinned-http-v1",checks=rows,error=error,completed=error is None,passed=sum(x["passed"] for x in rows),failed=sum(not x["passed"] for x in rows))
print(json.dumps(result,indent=2))
sys.exit(0 if error is None and result["failed"]==0 else 1)
