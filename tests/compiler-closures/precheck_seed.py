#!/usr/bin/env python3
"""Freeze and replay seed evidence for the closure pre-review regressions."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'prechecks.json'
BUILD = ROOT / '.local/compiler-closures/precheck-seed'
SEED = ['bun', '--no-env-file', '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observe(argv):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                            timeout=120, env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
    return {'argv': argv, 'exit': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr}


def replay(write=False):
    frozen = json.loads(MANIFEST.read_text())
    original = json.loads((HERE / 'expectations.json').read_text())
    require(frozen['seed'] == original['seed'], 'precheck seed identity differs')
    require(frozen['seed_files'] == original['observations']['seed_files'], 'seed files differ')
    for name, expected in frozen['seed_files'].items():
        require(digest(ROOT / name) == expected, ('seed drift', name))
    BUILD.mkdir(parents=True, exist_ok=True)
    parser = BUILD / 'parse.ts'
    parser.write_text('import * as fs from "node:fs";\n'
        'const B = await import(process.argv[2]);\n'
        'try { B.parse_book(B.book_nil(), "/probe/", fs.readFileSync(process.argv[3], "utf8"), "probe", Object.create(null));\n'
        '  console.log(JSON.stringify({ok:true}));\n'
        '} catch (e) { console.log(JSON.stringify({ok:false,expected:e.exp,begin:e.spn?.beg})); }\n')
    counts = {'programs': len(frozen['cases']), 'seed_parses': 0,
              'seed_checks': 0, 'seed_builds': 0, 'accepted': 0, 'rejected': 0}
    require(len({c['name'] for c in frozen['cases']}) == len(frozen['cases']), 'duplicate prechecks')
    require(sorted(c['file'] for c in frozen['cases']) ==
            sorted('prechecks/' + p.name for p in (HERE / 'prechecks').glob('*.bend')),
            'precheck manifest and sources differ')
    for case in frozen['cases']:
        path = HERE / case['file']
        require(digest(path) == case['source_sha256'], ('precheck source drift', case['name']))
        source = path.relative_to(ROOT).as_posix()
        parsed = observe(['bun', '--no-env-file', parser.relative_to(ROOT).as_posix(),
                          '../../../.toolchain/bend-2.0.29-574b6d3/bend2/bend.ts', source])
        require(parsed['exit'] == 0 and parsed['stderr'] == '', parsed)
        syntax = json.loads(parsed['stdout'])
        require(syntax['ok'] == (case['parse'] != 'Invalid'), (case['name'], syntax))
        checked = observe([*SEED, source, '--check-only'])
        require(checked['exit'] in (0, 1), checked)
        require((checked['exit'] == 0 and checked['stdout'] == 'All terms check.\n' and not checked['stderr'])
                or (checked['exit'] == 1 and not checked['stdout'] and checked['stderr'].startswith('Error:\n')),
                checked)
        observations = {'parse': syntax, 'check': checked, 'builds': {}}
        build_source = source
        if checked['exit'] == 0:
            wrapper = BUILD / (case['name'] + '-build.bend')
            wrapper_source = (f'import Base\nimport ../../../{source} as F\n\n'
                              'def main() -> IO(Unit):\n  IO.print("checked")\n')
            wrapper.write_text(wrapper_source)
            build_source = wrapper.relative_to(ROOT).as_posix()
            observations['wrapper_source'] = wrapper_source
            if 'def main()' in path.read_text():
                observations['run'] = observe([*SEED, source])
                require(observations['run']['exit'] == 0 and not observations['run']['stderr'],
                        observations['run'])
        for lane, suffix in [('native', ''), ('bun', '.js')]:
            output = BUILD / (case['name'] + suffix)
            built = observe([*SEED, build_source, '-o', output.relative_to(ROOT).as_posix()])
            require(built['exit'] == checked['exit'], (case['name'], lane, built))
            require((built['exit'] == 0 and output.is_file() and not built['stdout'] and not built['stderr'])
                    or (built['exit'] == 1 and built['stderr'] == checked['stderr']), built)
            observations['builds'][lane] = built
            counts['seed_builds'] += 1
        counts['seed_parses'] += 1
        counts['seed_checks'] += 1
        counts['accepted' if checked['exit'] == 0 else 'rejected'] += 1
        if write:
            case['seed'] = observations
        else:
            require(case['seed'] == observations, ('precheck seed drift', case['name'], observations))
    if write:
        MANIFEST.write_text(json.dumps(frozen, indent=2) + '\n')
    return counts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='freeze seed observations only')
    args = parser.parse_args()
    print(json.dumps(replay(args.write), sort_keys=True))
