#!/usr/bin/env python3
"""Re-run the pinned seed over the frozen baseslice fixtures; fail on any difference.

    python3 tests/compiler-baseslice/regen.py            # verify (default)
    python3 tests/compiler-baseslice/regen.py --write    # rewrite "observations" only
    python3 tests/compiler-baseslice/regen.py --census   # compare base_slice with the live census

Verify mode recomputes every seed observation and every source-derived coverage
fact, and compares them with the "observations" section of expectations.json
exactly. `--write` rewrites only that section, after two identical passes. The
hand-reviewed sections (forms, base_slice, cases) are never changed here; they
are only validated. `--census` reports drift between the frozen base_slice and
docs/compiler-campaign/inventory/base-closure.json without touching anything.

Everything runs from the repository root with relative paths, so recorded
commands and outputs are identical in every checkout. Nothing here runs or
reads Knot.
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
BASE = TOOLCHAIN + 'base.bend'
SEED_FILES = [TOOLCHAIN + name for name in ('main.ts', 'bend.ts', 'comp.ts', 'base.bend')]
WRAPPERS = '.local/compiler-baseslice/wrappers'
FIXTURES = 'tests/compiler-baseslice/fixtures'
CENSUS = 'docs/compiler-campaign/inventory/base-closure.json'
ENV = {**os.environ, 'BEND_NO_TELEMETRY': '1'}
TIMEOUT = 120
REQUIRES = {'agree', 'agree-or-unsupported', 'unsupported', 'reject'}
CLASSES = {'positive', 'edge', 'boundary', 'negative'}
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
        p = subprocess.run(argv, cwd=ROOT, env=ENV, text=True, capture_output=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        raise Mismatch(('a seed timeout is exhaustion, not an observation', argv))
    return {'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


# ---- Reading sources (syntactic only) ------------------------------------------

def base_catalog():
    """Base's top-level names and each constructor's owning type, from the pinned file."""
    names, owner, current = set(), {}, None
    for line in (ROOT / BASE).read_text().split('\n'):
        header = re.match(r'(def|law|type) ([\w.]+)', line)
        if header:
            names.add(header.group(2))
            current = header.group(2) if header.group(1) == 'type' else None
            continue
        ctor = re.match(r'  ([A-Z]\w*)\{', line)
        if ctor and current:
            owner.setdefault(ctor.group(1), current)
        elif line and not line.startswith(' '):
            current = None
    return names, owner


def enums(source: str):
    """Nullary enum declarations in constructor order."""
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


def local_names(source: str):
    names = set(re.findall(r'^(?:type|def) (\w+)', source, re.M))
    names |= set(re.findall(r'^  ([A-Z]\w*)\{', source, re.M))
    return names


def signature(source: str, name: str):
    match = re.search(rf'^def {name}\((.*)\) -> (\w+):$', source, re.M)
    require(match, (name, 'entry signature not found on one line'))
    params = [p.split(':')[1].strip() for p in match.group(1).split(', ')] if match.group(1) else []
    return params, match.group(2)


def code_only(source: str) -> str:
    """Source with character and string literal contents and comments removed."""
    code = re.sub(r"'(?:\\u\{\w*\}|\\.|[^\\'])'", "''", source)
    code = re.sub(r'"(?:\\.|[^"\\])*"', '""', code)
    return re.sub(r'#.*$', '', code, flags=re.M)


def spelled(source: str, names, owner, local):
    """Base names a fixture reaches by spelling or by literal sugar."""
    code = code_only(source)
    found = set()
    for token in set(re.findall(r'[A-Za-z_][\w.]*', code)) - local:
        if token in names:
            found.add(token)
        elif token in owner:
            found.add(owner[token])
    plain = re.sub(r'&\d+', '', code)
    sugar = {
        'String': '""' in code,
        'Char': "''" in code,
        'U32': re.search(r'(?<![\w.])\d+(?![\dn\w])', plain),
        'Nat': re.search(r'(?<![\w.])\d+n\b', plain),
        'List': '[' in code or '<>' in code,
        'Pair': re.search(r' & |(?<![\w>\]\)])\(', code),
        'IO.bind': re.search(r'\bdo IO<', code),
    }
    return sorted(found | {name for name, hit in sugar.items() if hit})


# ---- The frozen Base slice -------------------------------------------------------

def slice_index(document):
    entries = {e['key']: e for e in document['base_slice']['entries']}
    forms = document['forms']
    for key, e in entries.items():
        require(all(d in entries for d in e['dependencies']), (key, 'dependency outside the slice'))
        require(all(f in forms for f in e['forms']), (key, 'unknown form', e['forms']))
    return entries


def closure(names, entries):
    seen, todo = set(), list(names)
    while todo:
        key = todo.pop()
        if key not in seen:
            seen.add(key)
            todo.extend(entries[key]['dependencies'])
    return sorted(seen)


def census_projection():
    census = json.loads((ROOT / CENSUS).read_text())
    def base(root, lane):
        return {e['key']: e for e in census['roots'][root][lane]['entries'] if e['file'] == 'Base'}
    front, js, native = base('frontend', 'js'), base('compiler', 'js'), base('compiler', 'native')
    return {key: {'roots': ['frontend', 'compiler'] if key in front else ['compiler'],
                  'boundary': {'js': js[key]['boundary'], 'native': native[key]['boundary']},
                  'dependencies': sorted(d for d in js[key]['dependencies'] if d in js)}
            for key in js}


# ---- Hand-reviewed sections ------------------------------------------------------

def validate_case(case, cases, capabilities):
    knot, name = case['knot'], case['name']
    require(case['class'] in CLASSES, (name, 'unknown class'))
    require(knot['require'] in REQUIRES, (name, 'unknown requirement', knot))
    require(knot.get('justification'), (name, 'every Knot requirement carries a justification'))
    require(('exit' in knot) == bool(knot.get('knot_expected')), (name, 'a pinned outcome is a knot_expected literal'))
    require(set(case['requires']) <= set(capabilities), (name, 'unknown capability', case['requires']))
    if 'diagnostic' in knot:
        require(re.fullmatch(r'(Invalid|Unsupported)\t[a-z]+\t[a-z-]+\t', knot['diagnostic']), (name, knot))
        require({'Invalid': 2, 'Unsupported': 3}[knot['diagnostic'].split('\t')[0]] == knot.get('exit'), (name, knot))
    if knot['require'] == 'unsupported':
        require(knot.get('exit') == 3 and 'diagnostic' in knot, (name, 'Unsupported pins its phase and code'))
    if knot['require'] == 'reject':
        require(case['class'] == 'negative' and knot.get('exit') == 2, (name, 'a Base misuse is Invalid'))
        require(isinstance(case.get('seed_reason'), list) and case['seed_reason'], (name, 'reviewed seed reason'))
        twin = next((c for c in cases if c['name'] == case['twin']), None)
        require(twin and twin['knot']['require'] == 'agree', (name, 'a negative names an agree twin'))
    else:
        require(case['class'] != 'negative' and 'seed_reason' not in case, (name, 'accepted fixtures carry no rejection'))
    if knot['require'] in ('agree', 'agree-or-unsupported'):
        require('exit' not in knot, (name, 'agreement is fixed by the seed, not by a literal'))


def single_fault(case, cases):
    """A negative is its twin with exactly one line changed."""
    twin = next(c for c in cases if c['name'] == case['twin'])
    a = (HERE / twin['file']).read_text().split('\n')
    b = (HERE / case['file']).read_text().split('\n')
    changed = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    require(len(a) == len(b) and len(changed) == 1, (case['name'], 'must differ from its twin in one line'))
    return {'twin': twin['name'], 'line': changed[0] + 1, 'twin_text': a[changed[0]], 'text': b[changed[0]]}


# ---- Seed observations -----------------------------------------------------------

def value(stdout: str, prefix: str, constructors):
    match = re.fullmatch(re.escape(prefix) + r'(\w+)\{\}\n', stdout)
    require(match and match.group(1) in constructors, ('not a nullary constructor of the entry result', prefix, stdout))
    return match.group(1)


def result(type_name, constructor, constructors):
    return {'type': type_name, 'constructor': constructor, 'tag': constructors.index(constructor)}


def observe_case(case, cases, catalog, entries, forms):
    name = case['name']
    rel = f'{FIXTURES}/{name}.bend'
    require(case['file'] == f'fixtures/{name}.bend', (name, 'file must be named after the case'))
    source = (ROOT / rel).read_text()
    require(source.isascii() and '\t' not in source and '\r' not in source,
            (name, 'fixtures are ASCII with LF line endings and no tabs'))
    require(source.startswith('import Base\n\n'), (name, 'every fixture imports Base first'))
    names, owner = catalog
    local = local_names(source)
    clash = sorted(n for n in local if n in owner or n in {b.split('.')[0] for b in names})
    require(not clash, (name, 'local names reuse Base names', clash))
    types = enums(source)
    base = spelled(source, names, owner, local)
    outside = [b for b in base if b not in entries]
    require(not outside, (name, 'spells Base names outside the reached slice', outside))
    reached = closure(base, entries)
    reached_forms = sorted({f for key in reached for f in entries[key]['forms']})
    needs = sorted({n for f in reached_forms for n in forms[f]['needs']})
    missing = sorted(set(needs) - set(case['requires']))
    require(not missing, (name, 'requires omits what its Base slice needs', missing))
    check = run(['bun', SEED, rel, '--check-only'])
    direct = run(['bun', SEED, rel])
    item = {'case': name, 'source_sha256': digest(ROOT / rel), 'enums': types,
            'base_spelled': base, 'base_reached': reached, 'base_forms': reached_forms,
            'check_only': check, 'run': direct, 'calls': []}
    if case['knot']['require'] == 'reject':
        item['single_fault'] = single_fault(case, cases)
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
    require([e['name'] for e in case['entries']].count('main') == 1, (name, 'main is an entry'))
    for entry in case['entries']:
        out = entry['result']
        require(signature(source, entry['name']) == (entry['params'], out), (name, 'entry signature drifted', entry))
        require(out in types and all(p in types for p in entry['params']),
                (name, 'entries cross the host boundary with nullary enums only', entry))
        if entry['name'] == 'main':
            require(entry['params'] == [], (name, 'main takes no arguments'))
            item['calls'].append({'entry': 'main', 'arguments': [], 'ordinals': [], 'wrapper': None,
                                  'wrapper_source': None, **direct,
                                  'result': result(out, value(direct['stdout'], '', types[out]), types[out])})
            continue
        for args in itertools.product(*[types[p] for p in entry['params']]):
            wrapper = f"{WRAPPERS}/{name}--{entry['name']}--{'-'.join(args)}.bend"
            imported = os.path.relpath(ROOT / rel, (ROOT / wrapper).parent)
            call = ', '.join(f'F.{a}{{}}' for a in args)
            text = f"import {imported} as F\n\ndef main() -> F.{out}:\n  F.{entry['name']}({call})\n"
            (ROOT / wrapper).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / wrapper).write_text(text)
            observed = run(['bun', SEED, wrapper])
            require(observed['exit'] == 0 and observed['stderr'] == '', (name, 'wrapper call failed', observed))
            ctor = value(observed['stdout'], imported.removesuffix('.bend') + '.', types[out])
            item['calls'].append({'entry': entry['name'], 'arguments': list(args),
                                  'ordinals': [types[p].index(a) for p, a in zip(entry['params'], args)],
                                  'wrapper': wrapper, 'wrapper_source': text, **observed,
                                  'result': result(out, ctor, types[out])})
    if case['knot']['require'] in ('agree', 'agree-or-unsupported'):
        require(len({c['result']['constructor'] for c in item['calls']}) > 1,
                (name, 'every call returns one constructor; a constant answer would pass'))
    return item


def coverage(cases, fixtures, entries):
    """Which accepted fixtures spell or reach each slice entry, by Knot requirement."""
    requirement = {c['name']: c['knot']['require'] for c in cases}
    table = {}
    for key, e in sorted(entries.items()):
        accepted = [f for f in fixtures if requirement[f['case']] != 'reject']
        row = {'spelled': [f['case'] for f in accepted if key in f['base_spelled']]}
        for kind in ('agree', 'agree-or-unsupported', 'unsupported'):
            row[kind] = [f['case'] for f in accepted if key in f['base_reached'] and requirement[f['case']] == kind]
        host = bool({'foreign', 'bodiless'} & set(e['forms']))
        require(row['agree'] or host, (key, 'no agree fixture reaches this entry'))
        require(row['unsupported'] or not host, (key, 'no host-effect fixture reaches this host entry'))
        require(not (host and row['agree']), (key, 'an agree fixture reaches a host entry'))
        table[key] = row
    return table


def observe(document):
    cases, forms = document['cases'], document['forms']
    entries = slice_index(document)
    catalog = base_catalog()
    fixtures = [observe_case(c, cases, catalog, entries, forms) for c in cases]
    return {'seed_files': {f: digest(ROOT / f) for f in SEED_FILES},
            'fixtures': fixtures,
            'coverage': coverage(cases, fixtures, entries)}


def census_drift(document):
    frozen = {e['key']: {k: e[k] for k in ('roots', 'boundary', 'dependencies')}
              for e in document['base_slice']['entries']}
    live = census_projection()
    drift = [f'only frozen: {k}' for k in sorted(set(frozen) - set(live))]
    drift += [f'only in census: {k}' for k in sorted(set(live) - set(frozen))]
    drift += [f'changed: {k}' for k in sorted(set(frozen) & set(live)) if frozen[k] != live[k]]
    return drift


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--write', action='store_true', help='rewrite the observations section')
    parser.add_argument('--census', action='store_true', help='compare base_slice with the live census')
    args = parser.parse_args()
    document = json.loads(EXPECTATIONS.read_text())
    if args.census:
        drift = census_drift(document)
        print('\n'.join(drift) or 'regen: base_slice matches the live census projection')
        return 1 if drift else 0
    cases = document['cases']
    try:
        contract = json.loads((ROOT / 'src/CONTRACT.json').read_text())['seed']
        require(document['seed'] == {'version': contract['version'], 'revision': contract['commit'], 'entry': SEED},
                ('seed identity differs from src/CONTRACT.json', document['seed']))
        names = [c['name'] for c in cases]
        require(len(names) == len(set(names)), 'duplicate case names')
        on_disk = sorted(p.name for p in (HERE / 'fixtures').glob('*.bend'))
        require(on_disk == sorted(c['file'].removeprefix('fixtures/') for c in cases),
                ('fixture files and cases differ', on_disk))
        capabilities = document['capabilities']
        require(all(set(f['needs']) <= set(capabilities) for f in document['forms'].values()),
                'a form needs an unknown capability')
        for case in cases:
            validate_case(case, cases, capabilities)
        version = run(['bun', SEED, 'version'])
        require(version['stdout'] == f"bend {contract['version']}\n", ('unexpected seed version', version))
        observations = observe(document)
        if args.write:
            require(observe(document) == observations, 'two seed passes disagree; nothing written')
        text = json.dumps(observations)
        leaked = [leak for leak in LEAKS if leak in text]
        require(not leaked, ('checkout-specific paths in observations', leaked))
    except Mismatch as e:
        print('regen: FAIL', e, file=sys.stderr)
        return 1
    fixtures = observations['fixtures']
    calls = sum(len(o['calls']) for o in fixtures)
    rejected = sum(o['run']['exit'] != 0 for o in fixtures)
    summary = (f'{len(cases)} fixtures ({len(cases) - rejected} seed-valid, {rejected} seed-invalid), '
               f'{calls} entry calls, {len(observations["coverage"])} Base slice entries covered')
    if args.write:
        document['observations'] = observations
        EXPECTATIONS.write_text(json.dumps(document, indent=2) + '\n')
        print(f'regen: wrote {summary}')
        return 0
    stored = document.get('observations')
    if stored != observations:
        before = json.dumps(stored, indent=2).splitlines()
        after = json.dumps(observations, indent=2).splitlines()
        sys.stdout.writelines(line + '\n' for line in itertools.islice(difflib.unified_diff(
            before, after, 'expectations.json', 'seed', lineterm='', n=2), 200))
        print('regen: FAIL seed observations differ from expectations.json', file=sys.stderr)
        return 1
    print(f'regen: PASS {summary}, identical to expectations.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
