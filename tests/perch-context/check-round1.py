#!/usr/bin/env python3
"""Additive perch-cap review controls; the original context gate stays frozen."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EXPECT = json.loads((HERE / 'round1-expectations.json').read_text())
TESTS = ('tests/perch-context-round1.test.mjs', 'tests/perch-context-round1-mutants.test.mjs')


def main():
    result = subprocess.run(['node', '--test', *TESTS], cwd=ROOT,
                            env={**os.environ, 'BEND_NO_TELEMETRY': '1'},
                            text=True, capture_output=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    names = re.findall(r'^# Subtest: (.+)$', result.stdout, re.M)
    mutants = [name.removeprefix('semantic mutant killed: ') for name in names
               if name.startswith('semantic mutant killed: ')]
    fixtures = [name for name in names if not name.startswith('semantic mutant killed: ')]
    assert fixtures == EXPECT['controls'], fixtures
    assert mutants == EXPECT['mutants'], mutants
    assert re.search(r'^# fail 0$', result.stdout, re.M), result.stdout
    assert re.search(rf'^# pass {len(names)}$', result.stdout, re.M), result.stdout
    inputs = (*TESTS, 'tests/perch-context/check-round1.py', 'tests/perch-context/round1-expectations.json',
              'scripts/perch-style.mjs', 'scripts/perch-bend-context.mjs', 'scripts/perch-context-interfaces.mjs',
              'scripts/perch-bend.mjs', 'vendor/bend-parser/bend.mts', 'perch-style.json')
    record = {'status': 'pass', 'fixtures': fixtures, 'mutants': mutants, 'tests': len(names),
              'provider_requests': 0,
              'inputs': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in inputs}}
    path = HERE / 'receipts/round1.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + '\n')
    print(f'PASS: {len(fixtures)} additive perch-cap controls; {len(mutants)} semantic mutants killed; '
          f'{len(names)} tests; 0 provider requests')


if __name__ == '__main__':
    main()
