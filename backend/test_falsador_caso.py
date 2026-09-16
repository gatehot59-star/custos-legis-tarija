"""Regression for the actual FALSADOR 2 shell step, not a duplicate predicate.

Run: python3 backend/test_falsador_caso.py
Only stdlib and bash. Each scenario uses a temporary backend copy, preserves
its real assertion helper, and replaces the suite entrypoint with a controlled
outcome. No database, network, credentials or production writes are required.
The historical broad 'ROJO CASO' predicate must fail this regression.

SCOPE ADDED AFTER MEASUREMENT (Brain, on top of Sol's five scenarios):
Sol's version rejected a lone fixture failure, which was the false positive he
proved. Two gaps survived that fix and both were measured against the real step:

  * CONTAMINATED EXPERIMENT: when the suite emits the target red AND the fixture
    red, the exact-line grep still matches and the step exits 0. That is not
    hypothetical: with a null case_id the "other case" check sends the very same
    payload as the target one, so the red stops being attributable to the
    sabotage. A falsifier that claims one defect must observe exactly one red.
  * POSITIVE CONTROL AS SUCCESS: under the old broad prefix, breaking the
    legitimate path ("con el caso correcto sigue autorizando") was accepted as
    proof that the sabotage worked, which is backwards.

The expected red count is 1 because it was measured, not assumed: each sabotage
yields 44 greens and 1 red against real PostgreSQL in brain-env.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/api-e2e.yml'
EXPECTED = 'CASO una accion SIN caso NO hereda la aprobacion del caso 1'
FIXTURE = 'CASO el segundo expediente se creo (si no, no se puede medir)'
POSITIVE = 'CASO con el caso correcto sigue autorizando (control positivo)'


def read_step(workflow: Path) -> str:
    """Extract exactly one FALSADOR 2 block; format drift fails closed."""
    text = workflow.read_text(encoding='utf-8')
    sections = re.split(r'^      - name: ', text, flags=re.MULTILINE)
    matches = [s for s in sections if s.startswith('FALSADOR 2 - ')]
    if len(matches) != 1:
        raise ValueError('expected exactly one FALSADOR 2 workflow step')
    marker = '        run: |\n'
    if matches[0].count(marker) != 1:
        raise ValueError('FALSADOR 2 must have one inline run block')
    body = textwrap.dedent(matches[0].split(marker, 1)[1]).rstrip() + '\n'
    if '${{' in body:
        raise ValueError('unsupported GitHub expression in executable step')
    for path in ('/tmp/api.py.bak2', '/tmp/f2.log'):
        if path not in body:
            raise ValueError('temporary path contract changed: ' + path)
    return body


def inject_entrypoint(original: str, statement: str) -> str:
    """Keep real imports/helpers and replace only the final main guard."""
    tree = ast.parse(original)
    last = tree.body[-1]
    if not isinstance(last, ast.If) or ast.unparse(last.test) != "__name__ == '__main__'":
        raise ValueError('suite must end with its main guard')
    for label in (EXPECTED, FIXTURE, POSITIVE):
        if label not in original:
            raise ValueError('suite assertion label missing: ' + label)
    prefix = '\n'.join(original.splitlines()[:last.lineno - 1]) + '\n'
    return prefix + statement


class FalsadorCasoRegression(unittest.TestCase):
    """Exercise the workflow's subprocess/exit-code/log consumer end to end."""

    def run_scenario(self, statement: str) -> subprocess.CompletedProcess[str]:
        """Run the actual step in isolation and verify mutation restoration."""
        self.assertIsNotNone(shutil.which('bash'), 'bash is required, never skip')
        step = read_step(WORKFLOW)
        with tempfile.TemporaryDirectory(prefix='custos-falsador-test-') as tmp:
            folder = Path(tmp)
            backend = folder / 'backend'
            backend.mkdir()
            for source in (ROOT / 'backend').glob('*.py'):
                shutil.copyfile(source, backend / source.name)
            suite = backend / 'test_regresiones_hitl.py'
            suite.write_text(inject_entrypoint(suite.read_text(encoding='utf-8'), statement), encoding='utf-8')
            original_api = (backend / 'api.py').read_bytes()
            step = step.replace('/tmp/api.py.bak2', str(folder / 'api.py.bak2'))
            step = step.replace('/tmp/f2.log', str(folder / 'f2.log'))
            script = folder / 'step.sh'
            script.write_text(step, encoding='utf-8')
            env = dict(os.environ)
            for key in ('DATABASE_URL', 'DATABASE_URL_APP', 'PYTHONPATH', 'BASH_ENV', 'ENV'):
                env.pop(key, None)
            result = subprocess.run(
                ['bash', '--noprofile', '--norc', '-e', '-o', 'pipefail', str(script)],
                cwd=folder, env=env, capture_output=True, text=True, timeout=30,
            )
            self.assertIn('sabotaje 2 aplicado', result.stdout, result.stdout + result.stderr)
            self.assertEqual((backend / 'api.py').read_bytes(), original_api, 'step did not restore api.py')
            return result

    def test_fixture_failure_is_not_a_detected_regression(self):
        """Historical false positive: setup assertion alone must reject."""
        result = self.run_scenario(f'ok({FIXTURE!r}, False, True)\nraise SystemExit(1)\n')
        self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_unrelated_traceback_is_rejected(self):
        """An import/setup-style crash cannot validate the mutation."""
        result = self.run_scenario('raise RuntimeError("controlled unrelated crash")\n')
        self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_successful_suite_is_rejected(self):
        """If the sabotaged suite passes, the falsifier must fail."""
        result = self.run_scenario('raise SystemExit(0)\n')
        self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_expected_assertion_with_exit_one_is_accepted(self):
        """Positive control: never replace the falsifier by always-fail."""
        result = self.run_scenario(f'ok({EXPECTED!r}, 200, 403)\nraise SystemExit(1)\n')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_expected_label_with_abnormal_exit_is_rejected(self):
        """A label cannot excuse an abnormal suite termination."""
        result = self.run_scenario(f'ok({EXPECTED!r}, 200, 403)\nraise SystemExit(2)\n')
        self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_contaminated_experiment_is_rejected(self):
        """Target red plus a fixture red must NOT count as a clean detection.

        Measured gap: the exact-line grep matched and the step exited 0, so a
        broken experiment was reported as a working guard. With a null case_id
        the other-case check sends the same payload as the target, so the red is
        no longer attributable to the sabotage.
        """
        result = self.run_scenario(
            f'ok({FIXTURE!r}, False, True)\n'
            f'ok({EXPECTED!r}, 200, 403)\n'
            'raise SystemExit(1)\n')
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('CONTAMINADO', result.stdout, result.stdout)

    def test_broken_positive_control_is_rejected(self):
        """Breaking the legitimate path is the opposite of a working sabotage.

        Under the old broad 'ROJO CASO' prefix this was accepted as success: the
        guard celebrated the sabotage precisely when it had destroyed the path
        that must keep working.
        """
        result = self.run_scenario(f'ok({POSITIVE!r}, 403, 200)\nraise SystemExit(1)\n')
        self.assertNotEqual(result.returncode, 0, result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
