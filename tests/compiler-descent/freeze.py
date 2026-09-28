#!/usr/bin/env python3
"""Freeze or verify seed observations; never invoke Knot or infer expectations."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SEED = '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts'
RECEIPT = HERE / 'receipts/reference.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observe(case):
    args = ['bun', SEED, case['file'], *case.get('seed_args', [])]
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=60,
                            env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
    actual = {'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    expected = case['seed']
    assert actual['exit'] == expected['exit'], (case['name'], actual)
    if 'stdout' in expected:
        assert actual['stdout'].strip() == expected['stdout'] and not actual['stderr'], (case['name'], actual)
    if 'diagnostic' in expected:
        assert expected['diagnostic'] in actual['stderr'] and not actual['stdout'], (case['name'], actual)
    return {'name': case['name'], 'command': args, **actual}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((HERE / 'expectations.json').read_text())
    cases = manifest['fixtures'] + manifest['legacy']
    inputs = {str(path.relative_to(ROOT)): digest(path) for path in
              [HERE / 'expectations.json', *(ROOT / case['file'] for case in cases)]}
    seed = {str(path.relative_to(ROOT)): digest(path) for path in
            sorted((ROOT / Path(SEED).parent).glob('*.ts'))}
    observations = [observe(case) for case in cases]
    if args.write:
        assert not RECEIPT.exists(), 'The preimplementation freeze is immutable'
        record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'passed',
                  'inputs': inputs, 'seed': seed, 'observations': observations,
                  'baseline_implementation': {str(path.relative_to(ROOT)): digest(path)
                      for path in sorted((ROOT / 'src').glob('*.bend'))}}
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
        print(f'Frozen {len(cases)} seed observations before implementation')
    else:
        record = json.loads(RECEIPT.read_text())
        assert record['status'] == 'passed'
        for key, actual in [('inputs', inputs), ('seed', seed), ('observations', observations)]:
            assert record[key] == actual, ('freeze changed', key)
        print(f'Verified {len(cases)} frozen seed observations; no differences')


if __name__ == '__main__':
    main()
