"""Regression for the actual FALSADOR 2 shell step, not a duplicate predicate.

Run: python3 backend/test_falsador_caso.py
Only stdlib and bash. Each scenario uses a temporary backend copy, preserves
its real assertion helper, and replaces the suite entrypoint with a controlled
outcome. No database, network, credentials or production writes are required.
The historical broad 'ROJO CASO' predicate must fail this regression.

WHAT EACH FALSIFIER GENERATION FIXED, because every condition earned its place:

  v1  any nonzero exit counted as success (a traceback proved nothing).
  v2  broad prefix `ROJO CASO`: matched four checks, only one was the target, and
      one of the others was the POSITIVE CONTROL, so breaking the legitimate path
      counted as a working sabotage.
  v3  exact line + exit 1 + exactly one red: closed the CONTAMINATED experiment.
  v4  the suite must TERMINATE. Sol found target-then-crash: emit the target red,
      then raise. A Python exception exits 1 and adds no red line, so all of v3's
      conditions held with the suite DEAD halfway and the positive control never
      executed.

WHY THIS HARNESS CHANGED IN v4, and it is a defect of the harness and not of the
guard: it replaced the suite's main guard with a bare assertion, so NO scenario
printed the closing line `verdes: N | rojos: M`. A real run always prints it.
When the workflow started requiring it, two of these tests failed, INCLUDING the
positive control. An instrument that does not represent a real run produces
failures that are not defects. Each scenario now declares whether it simulates a
COMPLETE run (and closes like the suite does) or a DEAD one (and does not).
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

# The suite's own closing lines, copied from its main(). Kept here so a scenario
# can simulate a COMPLETE run instead of dying at its first assertion.
CERRAR = ('di(f"verdes: {VERDES} | rojos: {ROJOS}")\n'
          'di("VERDE" if ROJOS == 0 else "ROJO")\n'
          'raise SystemExit(1 if ROJOS else 0)\n')


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
    # The closing helper must still match the suite's real ending, otherwise a
    # COMPLETE run would be simulated with a format the workflow does not accept.
    if 'di(f"verdes: {VERDES} | rojos: {ROJOS}")' not in original:
        raise ValueError('suite closing line changed: update CERRAR')
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

    # -- COMPLETE runs: they close like the suite does -----------------------

    def test_expected_assertion_with_complete_run_is_accepted(self):
        """Positive control: never replace the falsifier by always-fail.

        This is the ONLY scenario that must be accepted. If it ever fails, the
        falsifier has become an always-red step and its greens mean nothing.
        """
        result = self.run_scenario(f'ok({EXPECTED!r}, 200, 403)\n' + CERRAR)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fixture_failure_is_not_a_detected_regression(self):
        """Historical false positive: setup assertion alone must reject."""
        result = self.run_scenario(f'ok({FIXTURE!r}, False, True)\n' + CERRAR)
        self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_contaminated_experiment_is_rejected(self):
        """Target red plus a fixture red must NOT count as a clean detection.

        MEASURED GAP of the exact-line predicate: the grep matched and the step
        exited 0, so a broken experiment was reported as a working guard. With a
        null case_id the other-case check sends the same payload as the target,
        so the red is no longer attributable to the sabotage. This run CLOSES
        normally (two reds), so it exercises the count guard and not termination.
        """
        result = self.run_scenario(
            f'ok({FIXTURE!r}, False, True)\n'
            f'ok({EXPECTED!r}, 200, 403)\n' + CERRAR)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('CONTAMINADO', result.stdout, result.stdout)

    def test_broken_positive_control_is_rejected(self):
        """Breaking the legitimate path is the opposite of a working sabotage.

        Measured: the exact-line predicate ALREADY rejects this, so it is not a
        gap of that fix. It was a gap of the original broad prefix, which
        celebrated the sabotage precisely when it had destroyed the path that
        must keep working. Kept as a regression against any family-wide predicate.
        """
        result = self.run_scenario(f'ok({POSITIVE!r}, 403, 200)\n' + CERRAR)
        self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_successful_suite_is_rejected(self):
        """If the sabotaged suite passes, the falsifier must fail."""
        result = self.run_scenario(CERRAR)
        self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_incoherent_receipt_is_rejected(self):
        """The suite must not contradict itself: declared reds == printed reds.

        Two reds printed, a closing line claiming one. Every count-based guard
        would be satisfied by the claim; only comparing both catches it.
        """
        result = self.run_scenario(
            f'ok({FIXTURE!r}, False, True)\n'
            f'ok({EXPECTED!r}, 200, 403)\n'
            'di("verdes: 44 | rojos: 1")\n'
            'di("ROJO")\n'
            'raise SystemExit(1)\n')
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('INCOHERENTE', result.stdout, result.stdout)

    # -- DEAD runs: no closing line, on purpose -----------------------------

    def test_target_then_crash_is_rejected(self):
        """Sol's finding: the target red followed by a crash must NOT be accepted.

        MEASURED against main before the fix: the step exited 0 and announced
        success. An exception exits 1 and adds no red line, so exit-code and
        red-count guards were both satisfied while the suite died halfway and the
        positive control never ran.
        """
        result = self.run_scenario(
            f'ok({EXPECTED!r}, 200, 403)\n'
            'raise RuntimeError("suite died after the target check")\n')
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('INCOMPLETA', result.stdout, result.stdout)

    def test_unrelated_traceback_is_rejected(self):
        """An import/setup-style crash cannot validate the mutation."""
        result = self.run_scenario('raise RuntimeError("controlled unrelated crash")\n')
        self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_expected_label_with_abnormal_exit_is_rejected(self):
        """A label cannot excuse an abnormal suite termination."""
        result = self.run_scenario(f'ok({EXPECTED!r}, 200, 403)\nraise SystemExit(2)\n')
        self.assertNotEqual(result.returncode, 0, result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
