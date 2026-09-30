#!/usr/bin/env python3
"""Reproduce BS1's seed observations; never invoke or inspect Knot outputs."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPECTATIONS = HERE / 'expectations.json'
WORK = ROOT / '.local/baseslice/enum/seed'
SEED_DIR = '.toolchain/bend-2.0.29-574b6d3/bend2/'
SEED = ['bun', SEED_DIR + 'main.ts']
TIMEOUT = 180 * float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def run(argv):
    # A timeout, signal or tool failure is a harness failure, never a verdict.
    p = subprocess.run([str(x) for x in argv], cwd=ROOT, capture_output=True,
                       text=True, stdin=subprocess.DEVNULL, timeout=TIMEOUT,
                       env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
    return {'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


def native(source, output):
    output.unlink(missing_ok=True)
    for _ in range(3):
        obs = run([*SEED, source, '-o', relative(output)])
        if not (obs['exit'] != 0 and 'bend needs clang' in obs['stderr']):
            break
    require(obs['exit'] == 0 and output.is_file(), ('seed native build', source, obs))
    return run(['./' + relative(output)])


def result(observation, constructors):
    require(observation['exit'] == 0 and observation['stderr'] == '', observation)
    match = re.fullmatch(r'(?:[^\s{}]+\.)?([A-Za-z_]\w*)\{\}\n', observation['stdout'])
    require(match and match[1] in constructors, ('seed enum observation', observation))
    return {'constructor': match[1], 'tag': constructors.index(match[1])}


def pinned(document):
    base = (ROOT / (SEED_DIR + 'base.bend')).read_bytes()
    require(sha(base) == document['base_sha256'], 'pinned Base changed')
    lines = base.decode('ascii').splitlines(keepends=True)
    parts = []
    for d in document['declarations']:
        first, last = d['lines']
        text = ''.join(lines[first - 1:last])
        require(sha(text.encode()) == d['sha256'], ('Base span changed', d['name']))
        parts.append(text)
    return '\n'.join(parts) + '\n'


def observe_case(case, document, prefix):
    source = HERE / 'fixtures' / (case['name'] + '.bend')
    text = source.read_text()
    if case['require'] != 'deferred':
        full_prefix = (
            '# Qualification book: the seven pinned Base declarations below are verbatim.\n'
            '# This is source-body qualification; the import loader is gated separately.\n\n'
            + prefix)
        require(text.startswith(full_prefix), ('qualification prefix changed', case['name']))
        # The seed's native builder requires Base and reserves its names globally.
        # Its oracle loads the unmodified Base, then the identical consumer body.
        oracle_text = 'import Base\n\n' + text[len(full_prefix):]
    else:
        oracle_text = text
    work = WORK / case['name']
    work.mkdir(parents=True, exist_ok=True)
    oracle = work / 'program.bend'
    oracle.write_text(oracle_text)
    check = run([*SEED, relative(oracle), '--check-only'])
    row = {'case': case['name'], 'source_sha256': sha(source.read_bytes()),
           'seed_source': oracle_text, 'check': check}
    if case['require'] == 'reject':
        require(check['exit'] != 0 and case['seed_reason'] in check['stderr'],
                ('seed must reject for the reviewed reason', case['name'], check))
        direct = run([*SEED, relative(oracle)])
        require(direct['exit'] != 0 and case['seed_reason'] in direct['stderr'], direct)
        row['interpreter'] = direct
        # Native compilation checks before emission; a seed rejection has no binary.
        out = work / 'rejected'
        out.unlink(missing_ok=True)
        rejected = run([*SEED, relative(oracle), '-o', relative(out)])
        require(rejected['exit'] != 0 and case['seed_reason'] in rejected['stderr']
                and not out.exists(), ('seed native rejection', rejected))
        row['native_check'] = rejected
        return row
    require(check == {'exit': 0, 'stdout': 'All terms check.\n', 'stderr': ''}, check)
    row['calls'] = []
    for i, call in enumerate(case['calls']):
        wrapper = work / f'call-{i}.bend'
        args = ','.join(name + '{}' for name in call['arguments'])
        result_type = ('F.' if case['require'] == 'deferred' else '') + call['result_type']
        wrapper_text = ('import Base\nimport ./program.bend as F\n\n'
                        f'def main() -> {result_type}:\n'
                        f'  F.{call["entry"]}({args})\n')
        wrapper.write_text(wrapper_text)
        interpreter = run([*SEED, relative(wrapper)])
        compiled = native(relative(wrapper), work / f'call-{i}')
        constructors = document['constructors'][call['result_type']]
        answer = result(interpreter, constructors)
        require(result(compiled, constructors) == answer,
                ('seed lanes disagree', case['name'], call, interpreter, compiled))
        row['calls'].append({'entry': call['entry'], 'arguments': call['arguments'],
                             'ordinals': call['ordinals'], 'wrapper': wrapper_text,
                             'interpreter': interpreter, 'native': compiled, 'result': answer})
    return row


def observations(document):
    require(os.environ.get('BEND_NO_TELEMETRY') == '1', 'export BEND_NO_TELEMETRY=1')
    require(document['seed'] == json.loads((ROOT / 'src/CONTRACT.json').read_text())['seed'],
            'seed identity differs from the compiler contract')
    prefix = pinned(document)
    paths = [SEED_DIR + f for f in ('main.ts', 'bend.ts', 'comp.ts', 'base.bend')]
    seed = {name: sha((ROOT / name).read_bytes()) for name in paths}
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(lambda c: observe_case(c, document, prefix), document['cases']))
    return {'seed_files': seed, 'fixtures': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='freeze observations before gate implementation')
    args = parser.parse_args()
    document = json.loads(EXPECTATIONS.read_text())
    seen = observations(document)
    if args.write:
        require(seen == observations(document), 'two independent seed freezes disagree')
        document['observations'] = seen
        EXPECTATIONS.write_text(json.dumps(document, indent=2) + '\n')
    else:
        require(seen == document.get('observations'), 'seed observations differ from the frozen oracle')
    calls = sum(len(f.get('calls', [])) for f in seen['fixtures'])
    print(f'base-enum seed: {len(seen["fixtures"])} fixtures, {calls} calls on both seed lanes')


if __name__ == '__main__':
    main()
