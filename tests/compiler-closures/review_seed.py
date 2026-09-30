#!/usr/bin/env python3
"""Replay expectation-first round-one controls on the pinned seed."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'review-r1.json'
BUILD = ROOT / '.local/compiler-closures/review-r1-seed'
SEED = ['bun', '--no-env-file', '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observe(argv):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                            timeout=120, env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
    return {'argv': argv, 'exit': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr}


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def replay(freeze=None):
    frozen = json.loads((freeze or MANIFEST).read_text())
    original = json.loads((HERE / 'expectations.json').read_text())
    require(frozen['seed'] == original['seed'] and
            frozen['seed_files'] == original['observations']['seed_files'], 'seed identity drift')
    for path, expected in frozen['seed_files'].items():
        require(digest(ROOT / path) == expected, ('seed file drift', path))
    require(len({c['name'] for c in frozen['cases']}) == len(frozen['cases']), 'duplicate controls')
    require(sorted(c['file'] for c in frozen['cases']) ==
            sorted('review-r1/' + p.name for p in (HERE / 'review-r1').glob('*.bend')),
            'review sources and manifest differ')
    BUILD.mkdir(parents=True, exist_ok=True)
    counts = dict(programs=len(frozen['cases']), accepted=0, rejected=0,
                  seed_checks=0, seed_builds=0, seed_runs=0)
    for case in frozen['cases']:
        source = 'tests/compiler-closures/' + case['file']
        source_hash = digest(ROOT / source)
        if not freeze:
            require(case['source_sha256'] == source_hash, ('source drift', case['name']))
        accepted = case['knot']['require'] == 'agree'
        checked = observe([*SEED, source, '--check-only'])
        require(checked['exit'] == (0 if accepted else 1), (case['name'], checked))
        require((accepted and checked['stdout'] == 'All terms check.\n' and not checked['stderr'])
                or (not accepted and not checked['stdout'] and checked['stderr'].startswith('Error:\n')),
                (case['name'], checked))
        observations = {'check': checked, 'lanes': {}}
        counts['seed_checks'] += 1
        build_source = source
        if accepted:
            wrapper = BUILD / (case['name'] + '.bend')
            wrapper_source = ('import Base\n'
                f'import ../../../{source} as F\n\n'
                'def show(x: F.T) -> IO(Unit):\n'
                '  match x:\n'
                '    case F.K{}: IO.print("K{}")\n\n'
                'def main() -> IO(Unit):\n  show(F.main())\n')
            wrapper.write_text(wrapper_source)
            build_source = wrapper.relative_to(ROOT).as_posix()
            observations['wrapper'] = {'file': build_source, 'source': wrapper_source}
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun', '--no-env-file'])]:
            output = BUILD / (case['name'] + suffix)
            built = observe([*SEED, build_source, '-o', output.relative_to(ROOT).as_posix()])
            counts['seed_builds'] += 1
            row = {'build': built}
            if accepted:
                require(built['exit'] == 0 and not built['stdout'] and not built['stderr']
                        and output.is_file(), (case['name'], lane, built))
                ran = observe([*runtime, output.relative_to(ROOT).as_posix()])
                require(ran['exit'] == 0 and ran['stdout'] == 'K{}\n' and not ran['stderr'],
                        (case['name'], lane, ran))
                row['run'] = ran
                counts['seed_runs'] += 1
            else:
                require(built['exit'] == checked['exit'] and built['stdout'] == checked['stdout']
                        and built['stderr'] == checked['stderr'], (case['name'], lane, built))
            observations['lanes'][lane] = row
        counts['accepted' if accepted else 'rejected'] += 1
        if freeze:
            case['source_sha256'] = source_hash
            case['seed'] = observations
        else:
            require(case['seed'] == observations, ('seed observation drift', case['name'], observations))
    if freeze:
        require(not MANIFEST.exists(), 'frozen expectations must not be overwritten')
        MANIFEST.write_text(json.dumps(frozen, indent=2) + '\n')
    return counts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze', type=Path, help='new draft only; refuses an existing manifest')
    args = parser.parse_args()
    print(json.dumps(replay(args.freeze), sort_keys=True))
