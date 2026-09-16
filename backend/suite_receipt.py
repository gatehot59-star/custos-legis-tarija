# In-process phase supervisor, not a malicious-code security boundary.
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import traceback
SUITE=Path(__file__).with_name("test_regresiones_hitl.py")
POLICY=Path(__file__).with_name("required_checks.json")
PHASES=("regresion_plazo_penal","regresiones_con_postgres","cerrar_fixtures")
def required_phases():
    data=json.loads(POLICY.read_text())
    if data.get("schema")!=1 or type(data.get("version")) is not int or data["version"]<1:
        raise ValueError("invalid policy version")
    phases=data.get("phases")
    if not isinstance(phases,dict) or set(phases)!=set(PHASES):
        raise ValueError("missing required phases")
    seen=set()
    for phase in PHASES:
        ids=phases[phase]
        if not isinstance(ids,list) or not ids: raise ValueError("empty required phase")
        for ident in ids:
            if not isinstance(ident,str) or not ident.strip() or ident in seen:
                raise ValueError("invalid or duplicate identity")
            seen.add(ident)
    return {p:sorted(phases[p]) for p in PHASES}
def expected_checks():
    return sorted(x for ids in required_phases().values() for x in ids)
def source_hash(): return hashlib.sha256(SUITE.read_bytes()).hexdigest()
def policy_hash(): return hashlib.sha256(POLICY.read_bytes()).hexdigest()
def atomic_write(path,data):
    fd,tmp=tempfile.mkstemp(prefix=".receipt-",dir=path.parent)
    try:
        with os.fdopen(fd,"w") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def run_suite(receipt,run_id):
    if receipt.exists() or not run_id: raise ValueError("fresh path and run id required")
    required=required_phases()
    rows=[]
    phases=[dict(id=p,entered=False,returned=False,error=None) for p in PHASES]
    data=dict(schema=2,run_id=run_id,suite_sha256=source_hash(),policy_sha256=policy_hash(),required_phases=required,checks=rows,phases=phases,events=[],errors=[],skipped=[],setup_completed=False,completed=False,cleanup_returned=False,process_exit=2)
    active=None
    module=None
    def observe(label,actual,expected):
        if active is None: raise RuntimeError("check outside supervised phase")
        passed=bool(actual==expected)
        rows.append(dict(id=label,phase=active,passed=passed))
        original_ok(label,actual,expected)
        return passed
    def invoke(index,function,*args):
        nonlocal active
        phase=phases[index]
        phase["entered"]=True
        active=phase["id"]
        data["events"].append(dict(phase=active,event="enter"))
        try: function(*args)
        except BaseException as exc:
            phase["error"]=type(exc).__name__+": "+str(exc)
            data["errors"].append(dict(phase=active,error=phase["error"]))
            data["events"].append(dict(phase=active,event="error"))
            traceback.print_exc()
            return False
        else:
            phase["returned"]=True
            data["events"].append(dict(phase=active,event="return"))
            return True
        finally: active=None
    try:
        spec=importlib.util.spec_from_file_location("custos_supervised_suite",SUITE)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        functions=tuple(getattr(module,p) for p in PHASES)
        original_ok=module.ok
        module.ok=observe
        if invoke(0,functions[0]):
            admin=os.environ.get("DATABASE_URL")
            app=os.environ.get("DATABASE_URL_APP")
            if not admin or not app: data["skipped"].append("PostgreSQL credentials absent")
            else:
                fixtures=module.sembrar_postgres(admin)
                if not isinstance(fixtures,tuple) or len(fixtures)!=2: raise ValueError("invalid fixture handle")
                data["setup_completed"]=True
                try: invoke(1,functions[1],admin,app,fixtures)
                finally: invoke(2,functions[2],admin,*fixtures)
    except BaseException as exc:
        data["errors"].append(dict(phase="setup/import",error=type(exc).__name__+": "+str(exc)))
        traceback.print_exc()
    finally:
        if module is not None: data["skipped"].extend(list(getattr(module,"NO_MEDIDO",[])))
        covered=all(sorted(x["id"] for x in rows if x["phase"]==p)==required[p] for p in PHASES)
        data["cleanup_returned"]=phases[2]["returned"]
        data["completed"]=data["setup_completed"] and all(p["returned"] for p in phases) and covered and not data["errors"] and not data["skipped"]
        code=int(any(not x["passed"] for x in rows)) if data["completed"] else 2
        data["process_exit"]=code
        atomic_write(receipt,data)
    return code
def validate(receipt,run_id,process_exit,expected_failure):
    data=json.loads(receipt.read_text())
    required=required_phases()
    if data.get("schema")!=2 or data.get("run_id")!=run_id: raise ValueError("receipt identity mismatch")
    if data.get("suite_sha256")!=source_hash() or data.get("policy_sha256")!=policy_hash(): raise ValueError("source or policy hash mismatch")
    if data.get("required_phases")!=required: raise ValueError("phase policy mismatch")
    if any(data.get(k) is not True for k in ("completed","cleanup_returned","setup_completed")) or data.get("errors")!=[] or data.get("skipped")!=[]: raise ValueError("suite phases did not complete")
    wanted=[dict(id=p,entered=True,returned=True,error=None) for p in PHASES]
    events=[e for p in PHASES for e in (dict(phase=p,event="enter"),dict(phase=p,event="return"))]
    if data.get("phases")!=wanted or data.get("events")!=events: raise ValueError("missing phase entry or return")
    rows=data.get("checks")
    if not isinstance(rows,list) or any(not isinstance(x,dict) or type(x.get("passed")) is not bool or x.get("phase") not in PHASES or not isinstance(x.get("id"),str) for x in rows): raise ValueError("invalid check records")
    for phase in PHASES:
        if sorted(x["id"] for x in rows if x["phase"]==phase)!=required[phase]: raise ValueError("missing duplicate or misplaced phase checks")
    failures=sorted(x["id"] for x in rows if not x["passed"])
    if failures!=([] if expected_failure is None else [expected_failure]): raise ValueError("unexpected failures: "+repr(failures))
    wanted_exit=int(expected_failure is not None)
    if process_exit!=wanted_exit or data.get("process_exit")!=wanted_exit: raise ValueError("exit inconsistent with completion")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=["run","validate"])
    p.add_argument("--receipt",type=Path,required=True)
    p.add_argument("--run-id",required=True)
    p.add_argument("--exit-code",type=int)
    p.add_argument("--expect")
    a=p.parse_args()
    try:
        if a.mode=="run": return run_suite(a.receipt,a.run_id)
        if a.exit_code is None: raise ValueError("observed exit required")
        validate(a.receipt,a.run_id,a.exit_code,a.expect)
        print("RECEIPT VERIFIED: required phases entered and returned with exact checks")
        return 0
    except Exception as exc:
        print("RECEIPT REJECTED: "+str(exc),file=sys.stderr)
        return 2
if __name__=="__main__": raise SystemExit(main())
