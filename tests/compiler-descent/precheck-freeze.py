#!/usr/bin/env python3
"""Immutable independent seed observations for the executor precheck repairs."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/descent-2/precheck-seed'
REFERENCE = HERE / 'receipts/precheck-reference.json'
SEED_DIR = ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2'
SEED = ['bun', str(SEED_DIR / 'main.ts')]
REVISION = '574b6d39a235b539eb19a5c532993a0abb3d11ad'


def hashes(paths):
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def run(args):
    env = {k: os.environ[k] for k in ('PATH', 'HOME', 'CC', 'SDKROOT', 'DEVELOPER_DIR') if k in os.environ}
    env.update(BEND_NO_TELEMETRY='1', BEND_HUB='offline://disabled', BEND_ORIGIN='offline://disabled')
    p = subprocess.run([str(a) for a in args], cwd=BUILD, env=env, text=True, capture_output=True, timeout=120)
    return {'argv': [str(a) for a in args], 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


def observe():
    BUILD.mkdir(parents=True, exist_ok=True)
    files = sorted((HERE / 'precheck-fixtures').glob('*.bend'))
    parsed = run(['bun', HERE / 'precheck-parse.ts', SEED_DIR / 'bend.ts', *files])
    assert parsed['exit'] == 0 and not parsed['stderr'], parsed
    syntax = {Path(r['file']).stem: {k: v for k, v in r.items() if k != 'file'} for r in json.loads(parsed['stdout'])}
    rows = []
    for source in files:
        row = {'name': source.stem, 'file': str(source.relative_to(ROOT)), 'parse': syntax[source.stem],
               'book': run([*SEED, source]), 'lanes': {}}
        assert row['book']['exit'] in (0, 1), row
        wrapper = BUILD / source.name
        wrapper.write_text('import Base\n' + source.read_text())
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
            output = BUILD / (source.stem + suffix)
            output.unlink(missing_ok=True)
            built = run([*SEED, wrapper, '-o', output])
            item = row['lanes'][lane] = {'build': built}
            assert built['exit'] == row['book']['exit'], row
            if built['exit'] == 0:
                assert output.is_file() and not built['stderr'], built
                item['execution'] = run([*runtime, output])
                assert item['execution']['exit'] == 0 and not item['execution']['stderr'], item
                assert item['execution']['stdout'].strip() == row['book']['stdout'].strip(), row
            else:
                assert not output.exists() and not built['stdout'], built
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    assert not (args.write and REFERENCE.exists()), 'Seed freeze is immutable'
    sources = [Path(__file__).resolve(), HERE / 'precheck-parse.ts', *sorted((HERE / 'precheck-fixtures').glob('*.bend'))]
    inputs = hashes(sources)
    seed = hashes([*SEED_DIR.glob('*.ts'), SEED_DIR / 'base.bend'])
    baseline = hashes((ROOT / 'src').glob('*.bend'))
    observations = observe()
    assert hashes(sources) == inputs and hashes((ROOT / 'src').glob('*.bend')) == baseline
    record = {'seed_revision': REVISION, 'status': 'passed', 'inputs': inputs, 'seed': seed,
              'observations': observations}
    if args.write:
        record['implementation_at_freeze'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        record['baseline_implementation'] = baseline
        with REFERENCE.open('x') as f:
            f.write(json.dumps(record, indent=2) + '\n')
    else:
        frozen = json.loads(REFERENCE.read_text())
        for key, value in record.items():
            assert frozen[key] == value, ('Seed freeze differs', key)
    print(f"{'Frozen' if args.write else 'Verified'} {len(observations)} seed controls in parse/book/native/Bun lanes")


if __name__ == '__main__':
    main()
