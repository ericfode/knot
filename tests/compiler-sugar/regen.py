#!/usr/bin/env python3
"""Re-run the pinned seed over the frozen sugar fixtures; fail on any difference.

Check mode (the default) recomputes every seed observation and compares it with
the "observations" section of expectations.json exactly. `--write` rewrites
only that section, and only after two complete seed passes agree. The
hand-reviewed "cases" section (entries, twins, needs, Base reasons, Knot
requirements and knot_expected literals) is never changed by this script; it is
only validated against the fixtures and the seed's classification.

Everything runs from the repository root with relative paths, so recorded
commands and outputs are identical in every checkout. No Knot code is run.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXPECTATIONS = HERE / 'expectations.json'
TOOLCHAIN = '.toolchain/bend-2.0.29-574b6d3/bend2/'
SEED = TOOLCHAIN + 'main.ts'
SEED_FILES = [TOOLCHAIN + name for name in ('main.ts', 'bend.ts', 'comp.ts', 'base.bend')]
WRAPPERS = '.local/compiler-sugar/wrappers'
FIXTURES = 'tests/compiler-sugar/fixtures'
ENV = {**os.environ, 'BEND_NO_TELEMETRY': '1'}
TIMEOUT = 60
CLASSES = {'positive': 'agree', 'edge': 'agree', 'boundary': 'unsupported', 'negative': 'reject'}
NEEDS = {'base', 'generics', 'fields', 'recursion', 'nested-patterns', 'closures', 'literals',
         'type-level-definition'}
LEAKS = ('/Users/', '/home/', '/private/', '/tmp/', '.claude/worktrees', str(ROOT))


class Mismatch(Exception):
    pass


def require(condition, detail):
    if not condition:
        raise Mismatch(detail)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv):
    try:
        p = subprocess.run(argv, cwd=ROOT, env=ENV, text=True,
                           capture_output=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        raise Mismatch(('a seed timeout is exhaustion, not an observation', argv))
    return {'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


def base_names():
    """Every top-level name the pinned Base declares (defs, laws, types, constructors)."""
    text = (ROOT / TOOLCHAIN / 'base.bend').read_text()
    names = set(re.findall(r'^(?:def|law) ([\w.]+)', text, re.M))
    names |= set(re.findall(r'^type ([\w.]+)', text, re.M))
    names |= set(re.findall(r'^  ([A-Z]\w*)\{', text, re.M))
    return {n.split('.')[0] for n in names} | names


def local_names(source: str):
    names = set(re.findall(r'^(?:def|type) (\w+)', source, re.M))
    names |= set(re.findall(r'^  ([A-Z]\w*)\{', source, re.M))
    return names


def enums(source: str):
    """Nullary enum declarations in constructor order: a syntactic reading only."""
    found, lines = {}, source.split('\n')
    for i, line in enumerate(lines):
        header = re.fullmatch(r'type (\w+) is (?:Data|Type):', line)
        if not header:
            continue
        body = list(itertools.takewhile(lambda l: l.startswith('  '), lines[i + 1:]))
        arms = [re.fullmatch(r'  (\w+)\{\}', l) for l in body]
        if body and all(arms):
            found[header.group(1)] = [m.group(1) for m in arms]
    return found


def value(stdout: str, prefix: str, constructors):
    match = re.fullmatch(re.escape(prefix) + r'(\w+)\{\}\n', stdout)
    require(match and match.group(1) in constructors,
            ('not a nullary constructor of the entry result', prefix, stdout))
    return match.group(1)


def result(type_name, constructor, constructors):
    return {'type': type_name, 'constructor': constructor, 'tag': constructors.index(constructor)}


def validate_source(case, source, base):
    name = case['name']
    require(source.isascii() and '\t' not in source and '\r' not in source,
            (name, 'fixtures are ASCII with LF line endings and no tabs'))
    require(source.split('\n', 1)[0] == '# ' + case['summary'],
            (name, 'line 1 is the reviewed summary'))
    imports = re.findall(r'^import .*$', source, re.M)
    require(imports in ([], ['import Base']), (name, 'the only import is Base', imports))
    uses_base = imports == ['import Base']
    require(uses_base == (case['base'] is not None) == ('base' in case['requires']),
            (name, 'import Base, a Base reason and the base need go together'))
    if uses_base:
        clash = sorted(local_names(source) & base)
        require(not clash, (name, 'a fixture that imports Base reuses a Base name', clash))


def observe_case(case, base):
    name = case['name']
    rel = f'{FIXTURES}/{name}.bend'
    require(case['file'] == f'fixtures/{name}.bend', (name, 'file must be named after the case'))
    source = (ROOT / rel).read_text()
    validate_source(case, source, base)
    types = enums(source)
    check = run(['bun', SEED, rel, '--check-only'])
    direct = run(['bun', SEED, rel])
    item = {'case': name, 'source_sha256': digest(ROOT / rel), 'enums': types,
            'check_only': check, 'run': direct, 'calls': []}
    if case['knot']['require'] == 'reject':
        require(check['exit'] == 1 and direct['exit'] == 1, (name, 'the seed must reject', check, direct))
        require(check['stdout'] == '' and direct['stdout'] == '', (name, 'a rejection prints to stderr only'))
        require(direct['stderr'].startswith('Error:\n') and check['stderr'] == direct['stderr'],
                (name, 'check-only and run report the same rejection'))
        require(all(reason in direct['stderr'] for reason in case['seed_reason']),
                (name, 'the seed rejected for another reason', direct['stderr']))
        require(case['entries'] == [], (name, 'a seed-invalid fixture has no entry calls'))
        return item
    require(check['exit'] == 0 and check['stdout'] == 'All terms check.\n' and check['stderr'] == '',
            (name, 'the seed must check', check))
    require(direct['exit'] == 0 and direct['stderr'] == '', (name, 'the seed must run main', direct))
    require('seed_reason' not in case, (name, 'accepted fixtures carry no rejection reason'))
    require([e['name'] for e in case['entries']].count('main') == 1, (name, 'main is an entry'))
    for entry in case['entries']:
        out = entry['result']
        require(out in types and all(p in types for p in entry['params']),
                (name, 'entries cross the host boundary with nullary enums only', entry))
        require(re.search(rf'^def {entry["name"]}\(', source, re.M), (name, 'entry is declared', entry))
        if entry['name'] == 'main':
            require(entry['params'] == [], (name, 'main takes no arguments'))
            item['calls'].append({
                'entry': 'main', 'arguments': [], 'ordinals': [], 'wrapper': None,
                'wrapper_source': None, **direct,
                'result': result(out, value(direct['stdout'], '', types[out]), types[out])})
            continue
        for args in itertools.product(*[types[p] for p in entry['params']]):
            wrapper = f"{WRAPPERS}/{name}--{entry['name']}--{'-'.join(args)}.bend"
            imported = os.path.relpath(ROOT / rel, (ROOT / wrapper).parent)
            call = ','.join(f'F.{a}{{}}' for a in args)
            text = (f'import {imported} as F\n\n'
                    f"def main() -> F.{out}:\n  F.{entry['name']}({call})\n")
            (ROOT / wrapper).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / wrapper).write_text(text)
            observed = run(['bun', SEED, wrapper])
            require(observed['exit'] == 0 and observed['stderr'] == '', (name, 'wrapper call failed', observed))
            ctor = value(observed['stdout'], imported.removesuffix('.bend') + '.', types[out])
            item['calls'].append({
                'entry': entry['name'], 'arguments': list(args),
                'ordinals': [types[p].index(a) for p, a in zip(entry['params'], args)],
                'wrapper': wrapper, 'wrapper_source': text, **observed,
                'result': result(out, ctor, types[out])})
    if case['knot']['require'] == 'agree':
        require(len({c['result']['constructor'] for c in item['calls']}) > 1,
                (name, 'an agree fixture needs two distinct results, so a constant cannot pass'))
    return item


def validate_case(case, by_name):
    """Hand-written Knot requirements must be well formed and consistent (D4)."""
    knot, name = case['knot'], case['name']
    require(case['class'] in CLASSES, (name, 'unknown class', case['class']))
    require(knot['require'] == CLASSES[case['class']], (name, 'class and requirement disagree', knot))
    require(knot.get('justification'), (name, 'every Knot requirement carries a justification'))
    require(set(case['requires']) <= NEEDS and case['requires'] == sorted(set(case['requires'])),
            (name, 'needs are known, sorted and unique', case['requires']))
    require(case['census'] and all(re.fullmatch(r'[a-z-]+(\.[a-z-]+)?', c) for c in case['census']),
            (name, 'census classes are named', case['census']))
    require(('exit' in knot) == bool(knot.get('knot_expected')),
            (name, 'a pinned Knot outcome is a knot_expected literal'))
    if 'diagnostic' in knot:
        require(re.fullmatch(r'(Invalid|Unsupported)\t[a-z]+\t[a-z-]+\t', knot['diagnostic']), (name, knot))
        require({'Invalid': 2, 'Unsupported': 3}[knot['diagnostic'].split('\t')[0]] == knot.get('exit'), (name, knot))
    if knot['require'] == 'unsupported':
        require(knot.get('exit') == 3 and 'diagnostic' in knot, (name, 'Unsupported pins its phase and code'))
    if knot['require'] == 'reject':
        require(knot.get('exit') == 2, (name, 'a seed rejection is Invalid (exit 2)'))
        require(isinstance(case.get('seed_reason'), list) and case['seed_reason'], (name, 'reviewed seed reason'))
        twin = case.get('twin')
        require(twin in by_name and by_name[twin]['knot']['require'] == 'agree',
                (name, 'a negative names a seed-valid twin', twin))
    else:
        require(case.get('twin') is None, (name, 'only negatives name a twin'))
    if knot['require'] == 'agree':
        require('exit' not in knot, (name, 'agreement is fixed by the seed, not by a literal'))


def observe(cases, contract, base):
    version = run(['bun', SEED, 'version'])
    require(version['stdout'] == f"bend {contract['version']}\n", ('unexpected seed version', version))
    bun = run(['bun', '--version'])
    require(bun['exit'] == 0, ('bun --version failed', bun))
    observations = {'seed_files': {f: digest(ROOT / f) for f in SEED_FILES},
                    'bun': bun['stdout'].strip(),
                    'fixtures': [observe_case(c, base) for c in cases]}
    text = json.dumps(observations)
    leaked = [leak for leak in LEAKS if leak in text]
    require(not leaked, ('checkout-specific paths in observations', leaked))
    return observations


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--write', action='store_true', help='rewrite the observations section')
    args = parser.parse_args()
    document = json.loads(EXPECTATIONS.read_text())
    cases = document['cases']
    try:
        contract = json.loads((ROOT / 'src/CONTRACT.json').read_text())['seed']
        require(document['seed'] == {'version': contract['version'], 'revision': contract['commit'], 'entry': SEED},
                ('seed identity differs from src/CONTRACT.json', document['seed']))
        names = [c['name'] for c in cases]
        require(len(names) == len(set(names)), 'duplicate case names')
        by_name = {c['name']: c for c in cases}
        on_disk = sorted(p.name for p in (HERE / 'fixtures').glob('*.bend'))
        require(on_disk == sorted(c['file'].removeprefix('fixtures/') for c in cases),
                ('fixture files and cases differ', on_disk))
        for case in cases:
            validate_case(case, by_name)
        base = base_names()
        observations = observe(cases, contract, base)
        if args.write:
            require(observe(cases, contract, base) == observations,
                    'two seed passes disagree; nothing written')
    except Mismatch as e:
        print('regen: FAIL', e, file=sys.stderr)
        return 1
    calls = sum(len(o['calls']) for o in observations['fixtures'])
    rejected = sum(o['run']['exit'] != 0 for o in observations['fixtures'])
    summary = (f'{len(cases)} fixtures ({len(cases) - rejected} seed-valid, {rejected} seed-invalid), '
               f'{calls} entry calls')
    if args.write:
        document['observations'] = observations
        EXPECTATIONS.write_text(json.dumps(document, indent=2) + '\n')
        print(f'regen: wrote {summary}')
        return 0
    stored = document.get('observations')
    if stored != observations:
        before = json.dumps(stored, indent=2).splitlines()
        after = json.dumps(observations, indent=2).splitlines()
        sys.stdout.writelines(line + '\n' for line in difflib.unified_diff(
            before, after, 'expectations.json', 'seed', lineterm='', n=2))
        print('regen: FAIL seed observations differ from expectations.json', file=sys.stderr)
        return 1
    print(f'regen: PASS {summary}, identical to expectations.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
