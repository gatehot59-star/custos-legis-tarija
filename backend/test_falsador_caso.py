# Supervisor regressions: synthetic phases, real supervisor and workflow consumer.
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest
import suite_receipt as sr
ROOT=Path(__file__).resolve().parents[1]
TARGET="CASO una accion SIN caso NO hereda la aprobacion del caso 1"
FIXTURE="CASO el segundo expediente se creo (si no, no se puede medir)"

def synthetic_suite(required,failures,change=None):
    source="NO_MEDIDO=[]\ndef ok(label,a,b): return a==b\ndef sembrar_postgres(admin): return ({}, {})\ndef main(): raise RuntimeError(\"MAIN MUST NOT RUN\")\n"
    signatures={sr.PHASES[0]:"",sr.PHASES[1]:"admin, app, fixtures",sr.PHASES[2]:"admin, ids, slugs"}
    for name in sr.PHASES:
        labels=list(required[name])
        if change=="missing" and name==sr.PHASES[1]: labels=labels[:-1]
        if change=="duplicate" and name==sr.PHASES[1]: labels+=labels[:1]
        if change=="misplaced" and name==sr.PHASES[0]: labels+=required[sr.PHASES[1]]
        if change=="misplaced" and name==sr.PHASES[1]: labels=[]
        body="for label in "+repr(labels)+":\n    ok(label, label not in "+repr(failures)+", True)\n"
        if change=="empty" and name==sr.PHASES[1]: body="pass\n"
        if change=="trap_first" and name==sr.PHASES[0]: body="raise RuntimeError(\"PHASE_TRAP\")\n"
        if change=="crash_integration" and name==sr.PHASES[1]: body+="raise RuntimeError(\"integration crash\")\n"
        if change=="crash_cleanup" and name==sr.PHASES[2]: body+="raise RuntimeError(\"cleanup crash\")\n"
        if change=="system_exit" and name==sr.PHASES[1]: body+="raise SystemExit(1)\n"
        if change=="skip" and name==sr.PHASES[1]: body+="NO_MEDIDO.append(\"skipped\")\n"
        source+="def "+name+"("+signatures[name]+"):\n"+textwrap.indent(body,"    ")
    if change=="main_replay":
        source+="def main():\n    for label in "+repr(sr.expected_checks())+":\n        ok(label,True,True)\n    return 0\n"
        source+="def regresion_plazo_penal(): raise RuntimeError(\"PHASE_TRAP\")\n"
    return source

class SupervisorRegression(unittest.TestCase):
    def test_phase_contract(self):
        required=sr.required_phases()
        scenarios=[("valid",[],None,True),("expected_failure",[TARGET],None,True),
                   ("fixture_failure",[FIXTURE],None,False),("contaminated",[TARGET,FIXTURE],None,False),
                   ("main_replay",[],"main_replay",False),("empty",[],"empty",False),
                   ("missing",[],"missing",False),("duplicate",[],"duplicate",False),
                   ("misplaced",[],"misplaced",False),("first_error",[],"trap_first",False),
                   ("integration_error",[TARGET],"crash_integration",False),
                   ("cleanup_error",[TARGET],"crash_cleanup",False),
                   ("system_exit",[TARGET],"system_exit",False),("skip",[],"skip",False)]
        for name,failures,change,accepted in scenarios:
            with self.subTest(name=name),tempfile.TemporaryDirectory(prefix="custos-phases-") as tmp:
                p=Path(tmp)
                shutil.copytree(ROOT/"backend",p/"backend",ignore=shutil.ignore_patterns("__pycache__"))
                (p/"backend/test_regresiones_hitl.py").write_text(synthetic_suite(required,failures,change))
                env=dict(os.environ,DATABASE_URL="SYNTHETIC_NOT_USED",DATABASE_URL_APP="SYNTHETIC_NOT_USED")
                receipt=p/"result.json"
                run=subprocess.run(["python3",str(p/"backend/suite_receipt.py"),"run","--receipt",str(receipt),"--run-id",name],env=env,capture_output=True,text=True,timeout=15)
                data=json.loads(receipt.read_text())
                cmd=["python3",str(p/"backend/suite_receipt.py"),"validate","--receipt",str(receipt),"--run-id",name,"--exit-code",str(run.returncode)]
                if failures: cmd += ["--expect",TARGET]
                val=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=15)
                print(name,"run",run.returncode,"validate",val.returncode,"events",data["events"])
                self.assertEqual(val.returncode==0,accepted,val.stdout+val.stderr)
                if change in ("crash_integration","system_exit"):
                    self.assertTrue(data["cleanup_returned"])
                    self.assertFalse(data["completed"])
                if change=="crash_cleanup": self.assertFalse(data["cleanup_returned"])
                if accepted:
                    self.assertEqual(len(data["checks"]),45)
                    for fault in ("stale","missing_return","wrong_phase","wrong_hash"):
                        bad=json.loads(json.dumps(data))
                        if fault=="stale": bad["run_id"]="older-run"
                        if fault=="missing_return": bad["events"].pop()
                        if fault=="wrong_phase": bad["checks"][0]["phase"]=sr.PHASES[1]
                        if fault=="wrong_hash": bad["policy_sha256"]="0"*64
                        receipt.write_text(json.dumps(bad))
                        rejected=subprocess.run(cmd,env=env,capture_output=True,text=True)
                        self.assertNotEqual(rejected.returncode,0,fault)

    def test_real_workflow_step(self):
        text=(ROOT/".github/workflows/api-e2e.yml").read_text()
        block=next(b for b in re.split(r"^      - name: ",text,flags=re.M) if b.startswith("FALSADOR 2 - "))
        step=textwrap.dedent(block.split("        run: |\n",1)[1])
        for change,accepted in ((None,True),("crash_integration",False),("main_replay",False)):
            with self.subTest(change=change),tempfile.TemporaryDirectory(prefix="custos-step-") as tmp:
                p=Path(tmp)
                shutil.copytree(ROOT/"backend",p/"backend",ignore=shutil.ignore_patterns("__pycache__"))
                (p/"backend/test_regresiones_hitl.py").write_text(synthetic_suite(sr.required_phases(),[TARGET],change))
                before=(p/"backend/api.py").read_bytes()
                script=p/"step.sh";script.write_text(step)
                env=dict(os.environ,DATABASE_URL="SYNTHETIC_NOT_USED",DATABASE_URL_APP="SYNTHETIC_NOT_USED",TMPDIR=tmp)
                for k in ("PYTHONPATH","BASH_ENV","ENV"): env.pop(k,None)
                run=subprocess.run(["bash","-e","-o","pipefail",str(script)],cwd=p,env=env,capture_output=True,text=True,timeout=20)
                self.assertEqual(run.returncode==0,accepted,run.stdout+run.stderr)
                self.assertEqual((p/"backend/api.py").read_bytes(),before)

    def test_policy_rejects_malformed_missing_empty(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"policy.json"
            with patch.object(sr,"POLICY",p):
                with self.assertRaises(FileNotFoundError): sr.required_phases()
                p.write_text("{bad")
                with self.assertRaises(json.JSONDecodeError): sr.required_phases()
                p.write_text(json.dumps(dict(schema=1,version=1,phases={x:[] for x in sr.PHASES})))
                with self.assertRaises(ValueError): sr.required_phases()

if __name__=="__main__": unittest.main(verbosity=2)
