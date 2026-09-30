#!/usr/bin/env python3
"""Replay independently frozen closure edges on the pinned seed in both lanes."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'refresh.json'
BUILD = ROOT / '.local/compiler-closures/refresh-seed'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observe(command):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            timeout=120, env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
    return {'argv': command, 'exit': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr}


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def replay(write=False):
    frozen = json.loads(MANIFEST.read_text())
    original = json.loads((HERE / 'expectations.json').read_text())
    require(frozen['seed'] == original['seed'], 'refresh seed identity differs')
    require(frozen['seed_files'] == original['observations']['seed_files'],
            'refresh seed file identities differ')
    for file, expected in frozen['seed_files'].items():
        require(digest(ROOT / file) == expected, ('seed source drift', file))
    cases = frozen['cases']
    require(len(cases) >= 20 and len({c['name'] for c in cases}) == len(cases),
            'refresh needs at least twenty distinct edge programs')
    require(sorted(c['file'] for c in cases) ==
            sorted('refresh/' + p.name for p in (HERE / 'refresh').glob('*.bend')),
            'refresh sources and manifest differ')
    BUILD.mkdir(parents=True, exist_ok=True)
    counts = {'programs': len(cases), 'accepted': 0, 'rejected': 0,
              'seed_checks': 0, 'seed_builds': 0, 'seed_runs': 0}
    for case in cases:
        source = 'tests/compiler-closures/' + case['file']
        source_hash = digest(ROOT / source)
        if not write:
            require(source_hash == case['source_sha256'], ('refresh source drift', case['name']))
        seed = ['bun', frozen['seed']['entry']]
        accepted = case['knot']['require'] == 'agree'
        require(accepted or case['knot']['require'] == 'reject', 'unknown refresh requirement')
        require(len(case['calls']) == int(accepted), 'refresh calls must be accepted main entries')
        checked = observe([*seed, source, '--check-only'])
        counts['seed_checks'] += 1
        if accepted:
            call = case['calls'][0]
            require(call['entry'] == 'main' and call['ordinals'] == [], 'refresh host signature')
            require(call['result']['type'] == 'Flag'
                    and call['result']['tag'] == {'Off': 0, 'On': 1}[call['result']['constructor']],
                    'refresh enum contract')
            require(checked['exit'] == 0 and checked['stdout'] == 'All terms check.\n'
                    and checked['stderr'] == '', (case['name'], checked))
        else:
            require(checked['exit'] == 1 and checked['stdout'] == ''
                    and checked['stderr'].startswith('Error:\n'), (case['name'], checked))
        observations = {'check_only': checked, 'lanes': {}}
        build_source = source
        if accepted:
            wrapper = BUILD / (case['name'] + '.bend')
            wrapper_source = ('import Base\n'
                f'import ../../../{source} as F\n\n'
                'def show(x: F.Flag) -> IO(Unit):\n'
                '  match x:\n'
                '    case F.Off{}: IO.print("Off{}")\n'
                '    case F.On{}: IO.print("On{}")\n\n'
                'def main() -> IO(Unit):\n'
                '  show(F.main())\n')
            wrapper.write_text(wrapper_source)
            build_source = wrapper.relative_to(ROOT).as_posix()
            observations['wrapper'] = {'file': build_source, 'source': wrapper_source}
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
            output = BUILD / (case['name'] + suffix)
            command = [*seed, build_source, '-o', output.relative_to(ROOT).as_posix()]
            built = observe(command)
            counts['seed_builds'] += 1
            row = {'build': built}
            if accepted:
                require(built['exit'] == 0 and built['stdout'] == '' and built['stderr'] == ''
                        and output.is_file(), (case['name'], lane, built))
                ran = observe([*runtime, output.relative_to(ROOT).as_posix()])
                counts['seed_runs'] += 1
                require(ran['exit'] == 0 and ran['stderr'] == ''
                        and ran['stdout'] == call['result']['constructor'] + '{}\n',
                        (case['name'], lane, ran))
                row['run'] = ran
            else:
                require(built['exit'] == checked['exit'] and built['stdout'] == checked['stdout']
                        and built['stderr'] == checked['stderr'], (case['name'], lane, built))
            observations['lanes'][lane] = row
        counts['accepted' if accepted else 'rejected'] += 1
        if write:
            case['source_sha256'] = source_hash
            case['seed'] = observations
        else:
            require(observations == case['seed'], ('refresh seed observation drift', case['name'], observations))
    if write:
        MANIFEST.write_text(json.dumps(frozen, indent=2) + '\n')
    return counts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='freeze seed observations only')
    args = parser.parse_args()
    print(json.dumps(replay(args.write), sort_keys=True))
