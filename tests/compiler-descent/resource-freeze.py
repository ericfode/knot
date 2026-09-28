#!/usr/bin/env python3
"""Freeze seed observations before the descent resource repair; never run Knot."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SEED_DIR = ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2'
RECEIPT = HERE / 'receipts/resources-reference.json'


def hashes(paths):
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(set(paths))}


def observe(case):
    command = ['bun', str((SEED_DIR / 'main.ts').relative_to(ROOT)),
               case['file'], *case.get('seed_args', [])]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=30,
                            env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
    actual = {'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    expected = case['seed']
    assert actual['exit'] == expected['exit'], (case['name'], actual)
    if 'stdout' in expected:
        assert actual['stdout'] in (expected['stdout'], expected['stdout'] + '\n')
        assert not actual['stderr'], (case['name'], actual)
    if 'diagnostic' in expected:
        assert expected['diagnostic'] in actual['stderr'] and not actual['stdout'], (case['name'], actual)
    return {'name': case['name'], 'command': command, **actual}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        assert not RECEIPT.exists(), 'The resource expectation freeze is immutable'
    manifest = json.loads((HERE / 'resources.json').read_text())
    cases = manifest['cases']
    assert len({case['name'] for case in cases}) == len(cases), 'Duplicate resource cases'
    assert {str(path.relative_to(ROOT)) for path in (HERE / 'resources').glob('*.bend')} == {
        case['file'] for case in cases}, 'Resource fixture manifest mismatch'
    paths = [HERE / 'resources.json', Path(__file__).resolve(),
             *(ROOT / case['file'] for case in cases)]
    inputs = hashes(paths)
    seed = hashes([*SEED_DIR.glob('*.ts'), SEED_DIR / 'base.bend'])
    baseline = hashes((ROOT / 'src').glob('*.bend')) if args.write else None
    observations = [observe(case) for case in cases]
    assert hashes(paths) == inputs, 'Resource inputs changed during freeze'
    assert hashes([*SEED_DIR.glob('*.ts'), SEED_DIR / 'base.bend']) == seed, 'Seed changed during freeze'
    if args.write:
        assert hashes((ROOT / 'src').glob('*.bend')) == baseline, 'Implementation changed during freeze'
        record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'passed',
                  'seed_revision': manifest['seed_revision'], 'inputs': inputs, 'seed': seed,
                  'observations': observations, 'baseline_implementation': baseline}
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        with RECEIPT.open('x') as output:
            output.write(json.dumps(record, indent=2) + '\n')
        print(f'Frozen {len(cases)} resource seed observations before implementation')
    else:
        record = json.loads(RECEIPT.read_text())
        assert record['status'] == 'passed'
        for key, actual in [('inputs', inputs), ('seed', seed), ('observations', observations)]:
            assert record[key] == actual, ('resource freeze changed', key)
        print(f'Verified {len(cases)} frozen resource seed observations; no differences')


if __name__ == '__main__':
    main()
