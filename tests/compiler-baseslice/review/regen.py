#!/usr/bin/env python3
"""Freeze review regressions from the pinned seed, before changing Knot."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORK = ROOT / '.local/baseslice/review/seed'
SEED_DIR = '.toolchain/bend-2.0.29-574b6d3/bend2/'
SEED = ['bun', SEED_DIR + 'main.ts']
EXPECTATIONS = HERE / 'expectations.json'


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def run(argv):
    require(os.environ.get('BEND_NO_TELEMETRY') == '1', 'export BEND_NO_TELEMETRY=1')
    p = subprocess.run([str(x) for x in argv], cwd=ROOT, capture_output=True,
                       text=True, stdin=subprocess.DEVNULL, timeout=180)
    return {'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


def observations(document):
    WORK.mkdir(parents=True, exist_ok=True)
    paths = [SEED_DIR + f for f in ('main.ts', 'bend.ts', 'comp.ts', 'base.bend')]
    rows = []
    for case in document['cases']:
        source = HERE / 'fixtures' / (case['name'] + '.bend')
        check = run([*SEED, relative(source), '--check-only'])
        row = {'name': case['name'], 'source_sha256': sha(source.read_bytes()), 'check': check}
        if case['require'] == 'reject':
            require(check['exit'] == 1 and case['seed_reason'] in check['stderr'], (case, check))
            direct = run([*SEED, relative(source)])
            require(direct['exit'] == 1 and case['seed_reason'] in direct['stderr'], direct)
            row['interpreter'] = direct
            output = WORK / (case['name'] + '-rejected')
            output.unlink(missing_ok=True)
            native = run([*SEED, relative(source), '-o', relative(output)])
            require(native['exit'] == 1 and case['seed_reason'] in native['stderr']
                    and not output.exists(), native)
            row['native_check'] = native
        else:
            require(check == {'exit': 0, 'stdout': 'All terms check.\n', 'stderr': ''}, check)
            row['interpreter'] = run([*SEED, relative(source)])
            require(row['interpreter'] == {'exit': 0, 'stdout': case['seed_value'] + '\n',
                                           'stderr': ''}, (case, row['interpreter']))
            wrapper = WORK / (case['name'] + '.bend')
            wrapper.write_text('import Base\nimport ' + os.path.relpath(source, WORK)
                               + ' as F\n\n'
                               + 'def main() -> F.' + case['result_type'] + ':\n  F.main()\n')
            output = WORK / case['name']
            output.unlink(missing_ok=True)
            built = run([*SEED, relative(wrapper), '-o', relative(output)])
            require(built['exit'] == 0 and output.is_file(), (case, built))
            row['native'] = run(['./' + relative(output)])
            require(row['native']['exit'] == 0 and row['native']['stderr'] == ''
                    and re.fullmatch(r'(?:[^\s{}]+\.)?' + re.escape(case['seed_value']) + r'\n',
                                     row['native']['stdout']), (case, row['native']))
        rows.append(row)
    return {'seed_files': {name: sha((ROOT / name).read_bytes()) for name in paths}, 'cases': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    document = json.loads(EXPECTATIONS.read_text())
    seen = observations(document)
    if args.write:
        require(seen == observations(document), 'independent seed freezes disagree')
        document['observations'] = seen
        EXPECTATIONS.write_text(json.dumps(document, indent=2) + '\n')
    else:
        require(seen == document['observations'], 'frozen review seed observations changed')
    print('baseslice review seed: ' + str(len(seen['cases'])) + ' fixtures')


if __name__ == '__main__':
    main()
