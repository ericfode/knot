#!/usr/bin/env python3
"""Record and verify closure evidence; never implement source-language semantics."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RECEIPTS = HERE / 'receipts'
sys.path.insert(0, str(ROOT / 'scripts/gates'))
from normalize import Normalizer, json_bytes


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def portable(value):
    """Replace path volatility only; preserve dates, times, hashes and outcomes."""
    normalizer = Normalizer(ROOT, (ROOT / '.toolchain').resolve(), Path.home() / '.bend/lib')
    scratch = r'(?<![\w/.-])(?:' + re.escape(str(ROOT)) + r'/|\$ROOT/)?[.]local/gates/run-[A-Za-z0-9_-]+'

    def text(value):
        value = re.sub(scratch, '$GATE_RUN', value)
        return normalizer.text(value, normalizer.aliases)

    def walk(value):
        if isinstance(value, dict):
            return {text(key): walk(child) for key, child in value.items()}
        if isinstance(value, list):
            return [walk(child) for child in value]
        return text(value) if isinstance(value, str) else value

    return walk(value)


def verify_inputs(receipt):
    assert receipt['status'] == 'passed', 'closure gate did not pass'
    assert receipt['inputs'], 'missing input coverage'
    for name, expected in receipt['inputs'].items():
        path = ROOT / name.removeprefix('$ROOT/')
        assert path.resolve().is_relative_to(ROOT), ('external input', name)
        assert sha256(path) == expected, ('stale input', name)


def verify():
    closure_path = RECEIPTS / 'closures.json'
    closure = json.loads(closure_path.read_bytes())
    verify_inputs(closure)
    gates = json.loads((RECEIPTS / 'gates.json').read_bytes())
    assert gates['status'] == 'passed', 'whole gate run did not pass'
    assert all(g['status'] == 'passed' and g['exit_code'] == 0 for g in gates['gates'])
    assert gates['closure_receipt'] == {'file': 'tests/compiler-closures/receipts/closures.json',
                                        'sha256': sha256(closure_path)}, 'closure receipt changed'
    observed = next(g for g in gates['gates'] if g['name'] == 'closures')
    assert all(observed['counts'][key] == value for key, value in closure['counts'].items())
    print(json.dumps({'status': 'passed', 'inputs': len(closure['inputs']),
                      'gates': len(gates['gates'])}, sort_keys=True))


def record(run_dir: Path):
    run_dir = run_dir.resolve()
    assert run_dir.is_relative_to(ROOT / '.local'), 'run must belong to this worktree'
    summary = json.loads((run_dir / 'summary.json').read_bytes())
    assert summary['normalized']['status'] == 'passed', 'refuse unsuccessful run'
    rows = summary['normalized']['gates']
    assert all(g['status'] == 'passed' and g['exit_code'] == 0 for g in rows)
    from run import GATES
    assert [g['name'] for g in rows] == [g.name for g in GATES], 'incomplete gate coverage'
    source = run_dir / 'normalized/tests/compiler-closures/receipts/closures.json'
    closure = json.loads(source.read_bytes())
    verify_inputs(closure)
    snapshot = json.loads((run_dir / 'snapshot.json').read_bytes())
    for name, expected in closure['inputs'].items():
        assert snapshot[name]['sha256'] == expected, ('input differs from exported snapshot', name)
    closure_path = RECEIPTS / 'closures.json'
    closure_path.write_bytes(json_bytes(portable(closure)))
    gates = {
        'schema': 1,
        'source_commit': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
        'command': ['npm', 'run', '-s', 'gates', '--', '--jobs', str(summary['run']['jobs']),
                    '--timeout', str(summary['run']['timeout_seconds']), '--keep-scratch'],
        'environment': {'BEND_NO_TELEMETRY': '1'},
        'status': 'passed',
        'gates': portable(rows),
        'receipt_counts': summary['normalized']['receipt_counts'],
        'closure_receipt': {'file': 'tests/compiler-closures/receipts/closures.json',
                            'sha256': sha256(closure_path)},
        'limits': 'Other increments own shared receipt refresh; blocked prerequisites are not passes.'
    }
    (RECEIPTS / 'gates.json').write_bytes(json_bytes(gates))
    verify()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', type=Path, help='accepted run directory under this worktree .local/')
    args = parser.parse_args()
    record(args.record) if args.record else verify()
