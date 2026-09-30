#!/usr/bin/env python3
"""Freeze refresh controls from the pinned seed; never invoke Knot."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/compiler-descent/refresh-seed'
MANIFEST = HERE / 'refresh-expectations.json'
REFERENCE = HERE / 'receipts/refresh-reference.json'
SEED_DIR = ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2'
SEED = ['bun', str((SEED_DIR / 'main.ts').relative_to(ROOT))]


def hashes(paths):
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(set(paths))}


def cases():
    manifest = json.loads(MANIFEST.read_text())
    fixtures = manifest['fixtures']
    assert len(fixtures) >= 20 and len({case['name'] for case in fixtures}) == len(fixtures)
    assert {str(path.relative_to(ROOT)) for path in (HERE / 'refresh-fixtures').glob('*.bend')} == {
        case['file'] for case in fixtures}, 'Refresh fixture manifest mismatch'
    return manifest, fixtures


def observe(command):
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60,
                            env={**os.environ, 'BEND_NO_TELEMETRY': '1',
                                 'BEND_HUB': 'offline://disabled', 'BEND_ORIGIN': 'offline://disabled'})
    return {'argv': command, 'exit': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr}


def expected(actual, fixed, name):
    assert actual['exit'] == fixed['exit'], (name, fixed, actual)
    if fixed['exit'] == 0:
        assert actual['stdout'].strip() == fixed['stdout'] and not actual['stderr'], (name, actual)
    else:
        assert not actual['stdout'] and fixed['diagnostic'] in actual['stderr'], (name, actual)


def observations(fixtures):
    BUILD.mkdir(parents=True, exist_ok=True)
    rows = []
    for case in fixtures:
        source = ROOT / case['file']
        row = {'name': case['name'], 'book': observe([*SEED, case['file']]), 'lanes': {}}
        expected(row['book'], case['seed'], case['name'])
        # The seed requires Base for executable output. Its wrapper adds only this
        # import, preserving the source body; Knot receives the original fixture.
        wrapper = BUILD / (case['name'] + '.bend')
        wrapper.write_text('import Base\n' + source.read_text())
        row['wrapper_sha256'] = hashlib.sha256(wrapper.read_bytes()).hexdigest()
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
            output = BUILD / (case['name'] + suffix)
            output.unlink(missing_ok=True)
            command = [*SEED, str(wrapper.relative_to(ROOT)), '-o', str(output.relative_to(ROOT))]
            built = observe(command)
            actual = row['lanes'][lane] = {'build': built}
            if case['seed']['exit'] == 0:
                assert built['exit'] == 0 and not built['stdout'] and not built['stderr'], (case['name'], built)
                assert output.is_file() and output.stat().st_size > 0, (case['name'], lane)
                actual['execution'] = observe([*runtime, str(output.relative_to(ROOT))])
                expected(actual['execution'], case['seed'], (case['name'], lane))
            else:
                expected(built, case['seed'], (case['name'], lane))
                assert not output.exists(), (case['name'], lane, 'rejected seed build emitted an artifact')
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        assert not REFERENCE.exists(), 'The refresh seed freeze is immutable'
    manifest, fixtures = cases()
    paths = [MANIFEST, Path(__file__).resolve(), *(ROOT / case['file'] for case in fixtures)]
    inputs = hashes(paths)
    seed = hashes([*SEED_DIR.glob('*.ts'), SEED_DIR / 'base.bend'])
    baseline = hashes((ROOT / 'src').glob('*.bend'))
    rows = observations(fixtures)
    assert hashes(paths) == inputs and hashes([*SEED_DIR.glob('*.ts'), SEED_DIR / 'base.bend']) == seed
    assert hashes((ROOT / 'src').glob('*.bend')) == baseline, 'Implementation changed during seed freeze'
    if args.write:
        record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'passed',
                  'seed_revision': manifest['seed_revision'], 'inputs': inputs, 'seed': seed,
                  'observations': rows, 'baseline_implementation': baseline}
        with REFERENCE.open('x') as output:
            output.write(json.dumps(record, indent=2) + '\n')
        print(f'Frozen {len(fixtures)} refresh seed observations in book/native/bun lanes')
    else:
        record = json.loads(REFERENCE.read_text())
        assert record['status'] == 'passed' and record['seed_revision'] == manifest['seed_revision']
        for key, actual in [('inputs', inputs), ('seed', seed), ('observations', rows)]:
            assert record[key] == actual, ('refresh seed freeze changed', key)
        print(f'Verified {len(fixtures)} refresh seed observations in book/native/bun lanes; no differences')


if __name__ == '__main__':
    main()
