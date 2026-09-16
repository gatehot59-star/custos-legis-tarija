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


if __name__=='__main__':
    unittest.main(verbosity=2)
