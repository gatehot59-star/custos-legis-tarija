"""Completion receipts for the Custos regression suite (stdlib only).

Runner emits an atomic receipt after main and its cleanup return. Exceptions,
skips, missing/duplicate checks, stale run ids and abnormal exits fail closed.
This detects accidental incomplete runs, not a malicious suite forging evidence.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import traceback

SUITE = Path(__file__).with_name('test_regresiones_hitl.py')
FUNCTIONS = ('regresion_plazo_penal', 'regresiones_con_postgres', 'cerrar_fixtures')


def expected_checks(path: Path = SUITE) -> list[str]:
    """Read all literal assertion identities from the three suite phases."""
    tree = ast.parse(path.read_text(encoding='utf-8'))
    found = []
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    for name in FUNCTIONS:
        if name not in functions:
            raise ValueError('missing suite phase: ' + name)
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'ok':
                if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
                    raise ValueError('check identities must be literal strings')
                found.append(node.args[0].value)
    if not found or len(set(found)) != len(found):
        raise ValueError('empty or duplicate check manifest')
    return sorted(found)


def source_hash() -> str:
    """Bind the receipt to the regression suite version, not the mutated API."""
    return hashlib.sha256(SUITE.read_bytes()).hexdigest()


def run_suite(receipt: Path, run_id: str) -> int:
    """Run the unmodified suite and publish completion only after normal return."""
    if receipt.exists():
        raise FileExistsError('refusing to overwrite an existing receipt')
    if not run_id:
        raise ValueError('empty run id')
    records = []
    result = {'schema': 1, 'run_id': run_id, 'suite_sha256': source_hash(),
              'expected_checks': expected_checks(), 'checks': records,
              'completed': False, 'cleanup_returned': False,
              'skipped': [], 'error': None, 'suite_exit': 2}
    code = 2
    try:
        spec = importlib.util.spec_from_file_location('custos_receipt_suite', SUITE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = module.ok
        def record(label, actual, expected):
            passed = original(label, actual, expected)
            records.append({'id': label, 'passed': bool(passed)})
            return passed
        module.ok = record
        code = module.main()
        if type(code) is not int or code not in (0, 1):
            raise ValueError('unexpected suite return value')
        result['skipped'] = list(module.NO_MEDIDO)
        result['suite_exit'] = code
        identities = [x['id'] for x in records]
        complete = sorted(identities) == result['expected_checks'] and not result['skipped']
        result['completed'] = complete
        # main returned past the PostgreSQL function's finally/fixture cleanup.
        result['cleanup_returned'] = complete
        if not complete:
            result['error'] = 'incomplete check manifest or skipped PostgreSQL phase'
            code = 2
    except BaseException as exc:
        result['error'] = type(exc).__name__ + ': ' + str(exc)
        result['suite_exit'] = 2
        traceback.print_exc()
        code = 2
    finally:
        result['process_exit'] = code
        fd, name = tempfile.mkstemp(prefix='.receipt-', dir=receipt.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(name, receipt)
        finally:
            if os.path.exists(name):
                os.unlink(name)
    return code


def validate(receipt: Path, run_id: str, process_exit: int, expected_failure: str | None) -> None:
    """Require completed phases, exact identity set and only the intended failure."""
    data = json.loads(receipt.read_text(encoding='utf-8'))
    manifest = expected_checks()
    if data.get('schema') != 1 or data.get('run_id') != run_id or data.get('suite_sha256') != source_hash():
        raise ValueError('receipt identity/version mismatch')
    if data.get('completed') is not True or data.get('cleanup_returned') is not True or data.get('error') is not None or data.get('skipped') != []:
        raise ValueError('suite did not finish all checks and cleanup')
    rows = data.get('checks')
    if not isinstance(rows, list) or any(not isinstance(x, dict) or type(x.get('passed')) is not bool for x in rows):
        raise ValueError('invalid check records')
    if sorted(x.get('id', '') for x in rows) != manifest or data.get('expected_checks') != manifest:
        raise ValueError('missing, duplicate or unexpected checks')
    failures = sorted(x['id'] for x in rows if not x['passed'])
    required = [] if expected_failure is None else [expected_failure]
    if failures != required:
        raise ValueError('unexpected failures: ' + repr(failures))
    wanted_exit = 0 if expected_failure is None else 1
    if process_exit != wanted_exit or data.get('process_exit') != wanted_exit or data.get('suite_exit') != wanted_exit:
        raise ValueError('exit code inconsistent with completed receipt')


def main() -> int:
    """CLI for run and validation, with explicit paths and per-execution ids."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['run', 'validate'])
    parser.add_argument('--receipt', required=True, type=Path)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--exit-code', type=int)
    parser.add_argument('--expect')
    args = parser.parse_args()
    try:
        if args.mode == 'run':
            return run_suite(args.receipt, args.run_id)
        if args.exit_code is None:
            raise ValueError('validation requires observed exit code')
        validate(args.receipt, args.run_id, args.exit_code, args.expect)
        print('RECEIPT VERIFIED: complete suite and exact expected failures')
        return 0
    except Exception as exc:
        print('RECEIPT REJECTED: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
