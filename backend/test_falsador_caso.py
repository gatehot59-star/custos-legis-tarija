"""Permanent receipt regressions against the actual FALSADOR 2 shell step.
Controlled suite main replaces only execution, not its real manifest/helper.
No PostgreSQL or network. Run: python3 backend/test_falsador_caso.py.
"""
import ast
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest
import suite_receipt as receipt

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'CASO una accion SIN caso NO hereda la aprobacion del caso 1'
FIXTURE = 'CASO el segundo expediente se creo (si no, no se puede medir)'


def complete(failures, tail=''):
    """Generate a synthetic normal return with all real check identities."""
    return (f'for label in {receipt.expected_checks()!r}:\n'
            f'    ok(label, 200 if label in {failures!r} else 403, 403)\n'
            + tail + f'return {int(bool(failures))}\n')


class CompletionRegression(unittest.TestCase):
    """Reject incomplete, stale and contaminated evidence; accept valid control."""

    def scenario(self, body, fault=None):
        """Exercise the real step in a fresh temporary source copy."""
        text = (ROOT/'.github/workflows/api-e2e.yml').read_text()
        blocks = [b for b in re.split(r'^      - name: ', text, flags=re.M)
                  if b.startswith('FALSADOR 2 - ')]
        self.assertEqual(len(blocks), 1)
        step = textwrap.dedent(blocks[0].split('        run: |\n', 1)[1])
        with tempfile.TemporaryDirectory(prefix='custos-receipt-') as tmp:
            p = Path(tmp)
            shutil.copytree(ROOT/'backend', p/'backend', ignore=shutil.ignore_patterns('__pycache__'))
            suite = p/'backend/test_regresiones_hitl.py'
            source = suite.read_text(); lines = source.splitlines(keepends=True)
            main = next(n for n in ast.parse(source).body
                        if isinstance(n, ast.FunctionDef) and n.name == 'main')
            suite.write_text(''.join(lines[:main.lineno-1]) + 'def main():\n'
                             + textwrap.indent(body, '    ') + '\n'
                             + ''.join(lines[main.end_lineno:]))
            before = (p/'backend/api.py').read_bytes()
            step = step.replace('/tmp/api.py.bak2',str(p/'backup')).replace('/tmp/f2.log',str(p/'log'))
            if fault:
                ops={'missing':'rm -f "$RECEIPT"', 'stale':'RUN_ID="other-run"',
                     'malformed':"printf '{broken' > \"$RECEIPT\""}
                needle='python3 backend/suite_receipt.py validate'
                self.assertIn(needle,step)
                step=step.replace(needle,ops[fault]+'\n'+needle,1)
            (p/'step.sh').write_text(step)
            env=dict(os.environ,TMPDIR=tmp)
            for k in ['DATABASE_URL','DATABASE_URL_APP','PYTHONPATH','BASH_ENV','ENV']:
                env.pop(k,None)
            r=subprocess.run(['bash','--noprofile','--norc','-e','-o','pipefail',str(p/'step.sh')],
                             cwd=p,env=env,text=True,capture_output=True,timeout=30)
            self.assertIn('sabotaje 2 aplicado',r.stdout,r.stdout+r.stderr)
            self.assertEqual((p/'backend/api.py').read_bytes(),before)
            return r

    def test_receipt_contract(self):
        """Fifteen outcomes discriminate completion from matching log output."""
        scenarios=[
            ('complete_target',complete([TARGET]),None,True),
            ('target_then_crash',f'ok({TARGET!r},200,403)\nraise RuntimeError("after target")\n',None,False),
            ('cleanup_crash',complete([TARGET],'raise RuntimeError("cleanup")\n'),None,False),
            ('partial_return',f'ok({TARGET!r},200,403)\nreturn 1\n',None,False),
            ('fixture_only',complete([FIXTURE]),None,False),
            ('contaminated',complete([TARGET,FIXTURE]),None,False),
            ('positive_broken',complete(['CASO con el caso correcto sigue autorizando (control positivo)']),None,False),
            ('traceback','raise RuntimeError("setup")\n',None,False),
            ('no_failure',complete([]),None,False),
            ('abnormal_exit',complete([TARGET],'raise SystemExit(2)\n'),None,False),
            ('missing',complete([TARGET]),'missing',False),
            ('stale',complete([TARGET]),'stale',False),
            ('malformed',complete([TARGET]),'malformed',False),
            ('duplicate',complete([TARGET],f'ok({TARGET!r},200,403)\n'),None,False),
            ('skipped',complete([TARGET],'NO_MEDIDO.append("database unavailable")\n'),None,False),
        ]
        for name,body,fault,accepted in scenarios:
            with self.subTest(name=name):
                r=self.scenario(body,fault)
                print(f'{name}: step_exit={r.returncode}, expected_accept={accepted}')
                self.assertEqual(r.returncode==0,accepted,r.stdout+r.stderr)


class RequiredPolicyRegression(unittest.TestCase):
    """Requirements cannot shrink when executable checks disappear."""

    def test_policy_has_reviewed_phase_inventory(self):
        policy = __import__('json').loads(receipt.POLICY.read_text())
        self.assertEqual({k: len(v) for k, v in policy['phases'].items()},
                         {'regresion_plazo_penal': 12, 'regresiones_con_postgres': 32, 'cerrar_fixtures': 1})
        self.assertEqual(len(receipt.expected_checks()), 45)

    def test_suite_reduction_cannot_reduce_required_checks(self):
        with tempfile.TemporaryDirectory(prefix='custos-policy-') as tmp:
            p = Path(tmp)
            shutil.copytree(ROOT/'backend', p/'backend', ignore=shutil.ignore_patterns('__pycache__'))
            source = "NO_MEDIDO=[]\ndef ok(label,a,b): return a==b\ndef regresion_plazo_penal(): ok('surviving check',True,True)\ndef regresiones_con_postgres(a,b): pass\ndef cerrar_fixtures(a,b,c): pass\ndef main():\n    regresion_plazo_penal()\n    return 0\n"
            (p/'backend/test_regresiones_hitl.py').write_text(source)
            result = p/'result.json'
            run = subprocess.run(['python3',str(p/'backend/suite_receipt.py'),'run','--receipt',str(result),'--run-id','reduced'],capture_output=True,text=True)
            data = __import__('json').loads(result.read_text())
            self.assertEqual(run.returncode, 2, run.stderr)
            self.assertEqual(len(data['expected_checks']), 45)
            self.assertFalse(data['completed'])
            self.assertFalse(data['cleanup_returned'])
            # Even manually declaring completion with the shrunken list fails.
            data.update(completed=True, cleanup_returned=True, error=None,
                        expected_checks=['surviving check'], suite_exit=0, process_exit=0)
            result.write_text(__import__('json').dumps(data))
            checked = subprocess.run(['python3',str(p/'backend/suite_receipt.py'),'validate','--receipt',str(result),'--run-id','reduced','--exit-code','0'],capture_output=True,text=True)
            self.assertEqual(checked.returncode, 2)
            self.assertIn('missing, duplicate or unexpected checks', checked.stderr)

    def test_invalid_policy_fails_closed(self):
        from unittest.mock import patch
        import json
        base = json.loads(receipt.POLICY.read_text())
        with tempfile.TemporaryDirectory(prefix='custos-bad-policy-') as tmp:
            path = Path(tmp)/'policy.json'
            with patch.object(receipt, 'POLICY', path):
                with self.assertRaises(FileNotFoundError): receipt.expected_checks()
                path.write_text('{invalid')
                with self.assertRaises(json.JSONDecodeError): receipt.expected_checks()
                for name in receipt.PHASES:
                    policy = json.loads(json.dumps(base)); policy['phases'][name] = []
                    path.write_text(json.dumps(policy))
                    with self.assertRaises(ValueError): receipt.expected_checks()
                policy = json.loads(json.dumps(base))
                policy['phases']['cerrar_fixtures'] = [policy['phases']['regresion_plazo_penal'][0]]
                path.write_text(json.dumps(policy))
                with self.assertRaises(ValueError): receipt.expected_checks()


if __name__=='__main__':
    unittest.main(verbosity=2)
