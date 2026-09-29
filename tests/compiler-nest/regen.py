#!/usr/bin/env python3
"""Re-run the pinned Bend seed over the frozen nest fixtures; diff against expectations.json.

Default (check): every recorded seed observation is reproduced from scratch and
compared exactly (exit, stdout, stderr, decoded result). Any difference, missing
or extra fixture, changed fixture hash, changed seed source hash or changed Bun
version fails with exit status 1.

--write: after a deliberate, reviewed fixture change, refreeze only the seed
observation fields (`seed`, `tools`, and each fixture's `sha256`/`observed`).
Hand-reviewed fields (feature, kind, requires, summary, types, entries, control,
seed_rule and the whole `knot` block) are never generated, modified or dropped.
Knot is never run: expectations come from the seed or from literal review.

Run from anywhere; seed commands execute in the repository root.
"""
from __future__ import annotations

import argparse
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
MANIFEST = HERE / 'expectations.json'
FIXTURES = HERE / 'fixtures'
SEED_DIR = '.toolchain/bend-2.0.29-574b6d3'
SEED = SEED_DIR + '/bend2/main.ts'
SEED_SOURCES = ('bend2/main.ts', 'bend2/bend.ts', 'bend2/comp.ts')
CALLS = '.local/compiler-nest/calls'
ENV = {'BEND_NO_TELEMETRY': '1'}
TIMEOUT = 60*float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))  # harness hang guard only; gates set it under load

TYPE = re.compile(r'^type\s+(\w+)(<[^>]*>)?\s+is\s+(Type|Data)\s*:\s*$')
CTOR = re.compile(r'^\s+(\w+)\{(.*)\}\s*$')
DEF = re.compile(r'^def\s+(\w+)\((.*)\)\s*->\s*(.+?)\s*:\s*$')
PARAM = re.compile(r'^([+-]?)(\w+)\s*:\s*(.+)$')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(argv):
    try:
        p = subprocess.run(argv, cwd=ROOT, env={**os.environ, **ENV}, text=True,
                           capture_output=True, timeout=TIMEOUT)
        return {'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except subprocess.TimeoutExpired:
        return {'exit': None, 'stdout': '', 'stderr': 'harness-timeout'}


def declarations(source):
    """Datatypes in declaration order (name, type parameters, constructors) and signatures.

    Metadata only: this reads declaration headers to find the host boundary. It
    implements no Bend semantics.
    """
    types, defs, current = [], {}, None
    for line in source.splitlines():
        t, c, d = TYPE.match(line), CTOR.match(line), DEF.match(line)
        if t:
            current = (t.group(1), t.group(2), [])
            types.append(current)
        elif c and current is not None:
            current[2].append((c.group(1), c.group(2).strip() == ''))
        else:
            if line and not line[0].isspace():
                current = None
            if d:
                raw = d.group(2).strip()
                params = [PARAM.match(p.strip()) for p in raw.split(',')] if raw else []
                defs[d.group(1)] = {'parameters': params, 'result': d.group(3)}
    return types, defs


def boundary(source):
    """Nullary enums declared in the file and the enum-only functions a host can call."""
    types, defs = declarations(source)
    enums = {name: [k for k, _ in ctors] for name, params, ctors in types
             if params is None and all(nullary for _, nullary in ctors)}
    entries = {}
    for name, sig in defs.items():
        ps = sig['parameters']
        if sig['result'] in enums and all(
                p is not None and p.group(1) != '-' and p.group(3) in enums for p in ps):
            entries[name] = {'parameters': [p.group(3) for p in ps], 'result': sig['result']}
    type_ids = {name: i for i, (name, _, _) in enumerate(types)}
    return enums, entries, type_ids


def decode(stdout, prefix, constructors):
    """`<prefix>Name{}\\n` -> Name when Name is a declared constructor, else None."""
    if not stdout.endswith('{}\n') or not stdout.startswith(prefix):
        return None
    name = stdout[len(prefix):-3]
    return name if name in constructors else None


def wrapper(fixture, export, arguments, result):
    """A seed program that imports the unmodified fixture and calls one entry."""
    stem = '-'.join([export, *arguments])
    path = f'{CALLS}/{fixture["name"]}/{stem}.bend'
    imported = os.path.relpath(ROOT / fixture['file'], (ROOT / path).parent)
    call = f'F.{export}(' + ', '.join(f'F.{a}{{}}' for a in arguments) + ')'
    source = f'import {imported} as F\n\ndef main() -> F.{result}:\n  {call}\n'
    return path, source, call, imported.removesuffix('.bend') + '.'


def observe(fixture):
    """Run the seed on the fixture itself, then on every entry over its whole domain."""
    path = ROOT / fixture['file']
    source = path.read_text()
    enums, entries, type_ids = boundary(source)
    argv = ['bun', SEED, fixture['file']]
    main = {'command': argv, **run(argv)}
    result = entries.get('main', {}).get('result')
    if main['exit'] == 0 and result is not None:
        name = decode(main['stdout'], '', enums[result])
        main.update({'result_type': result, 'type_id': type_ids[result], 'result': name,
                     'tag': enums[result].index(name) if name else None})
    calls = []
    if main['exit'] == 0:
        for export, sig in entries.items():
            if export == 'main':
                continue
            for arguments in itertools.product(*(enums[t] for t in sig['parameters'])):
                wpath, wsource, call, prefix = wrapper(fixture, export, list(arguments), sig['result'])
                (ROOT / wpath).parent.mkdir(parents=True, exist_ok=True)
                (ROOT / wpath).write_text(wsource)
                argv = ['bun', SEED, wpath]
                obs = run(argv)
                name = decode(obs['stdout'], prefix, enums[sig['result']]) if obs['exit'] == 0 else None
                calls.append({
                    'export': export, 'arguments': list(arguments),
                    'ordinals': [enums[t].index(a) for t, a in zip(sig['parameters'], arguments)],
                    'result_type': sig['result'], 'type_id': type_ids[sig['result']],
                    'result': name, 'tag': enums[sig['result']].index(name) if name else None,
                    'seed_call': call, 'wrapper': wpath, 'wrapper_source': wsource,
                    'command': argv, **obs})
    return ({'sha256': sha256(path), 'observed': {'main': main, 'calls': calls}},
            enums, entries, source)


def environment():
    bun = run(['bun', '--version'])
    seed = {'entry': SEED, 'version': '2.0.29',
            'revision': '574b6d39a235b539eb19a5c532993a0abb3d11ad',
            'sha256': {s: sha256(ROOT / SEED_DIR / s) for s in SEED_SOURCES}}
    return seed, {'bun': bun['stdout'].strip()}


def review(fixture, enums, entries, source, by_name):
    """Consistency of the hand-reviewed fields with the fixture and its seed outcome."""
    problems, name, obs = [], fixture['name'], fixture['observed']
    first = source.splitlines()[0] if source else ''
    if first != '# ' + fixture.get('summary', ''):
        problems.append(f'{name}: summary differs from the fixture comment line {first!r}')
    main, knot = obs['main'], fixture.get('knot')
    if not isinstance(knot, dict) or knot.get('outcome') not in ('Accepted', 'Invalid', 'Unsupported'):
        problems.append(f'{name}: missing reviewed knot outcome')
        knot = {}
    if knot.get('source') == 'knot_expected' and not knot.get('justification'):
        problems.append(f'{name}: knot_expected needs a justification')
    if fixture['kind'] == 'negative':
        if main['exit'] in (0, None) or fixture.get('seed_rule', '\0') not in main['stderr']:
            problems.append(f'{name}: seed must reject with rule {fixture.get("seed_rule")!r}')
        control = by_name.get(fixture.get('control'))
        if control is None or control['kind'] == 'negative':
            problems.append(f'{name}: control must name a seed-accepted fixture')
        if knot.get('outcome') == 'Accepted':
            problems.append(f'{name}: a seed-rejected fixture cannot be Accepted by Knot')
        return problems
    if fixture.get('entries') != entries:
        problems.append(f'{name}: entries differ from the enum-only signatures {entries}')
    used = {t for e in entries.values() for t in [*e['parameters'], e['result']]}
    if fixture.get('types') != {t: enums[t] for t in sorted(used)}:
        problems.append(f'{name}: types must be exactly the boundary enums {sorted(used)}')
    if main['exit'] != 0 or main['stderr'] or main.get('result') is None:
        problems.append(f'{name}: seed must accept and print a declared constructor')
    for call in obs['calls']:
        if call['exit'] != 0 or call['stderr'] or call['result'] is None:
            problems.append(f'{name}: call {call["seed_call"]} did not decode')
    if knot.get('outcome') == 'Invalid':
        problems.append(f'{name}: a seed-accepted fixture can never be Invalid (D4)')
    return problems


def dump(value, depth=0):
    """JSON with one line per field; arrays of scalars stay on one line."""
    pad, inner = '  ' * depth, '  ' * (depth + 1)
    if isinstance(value, dict) and value:
        rows = [f'{inner}{json.dumps(k)}: {dump(v, depth + 1)}' for k, v in value.items()]
        return '{\n' + ',\n'.join(rows) + '\n' + pad + '}'
    if isinstance(value, list) and any(isinstance(v, (dict, list)) for v in value):
        return '[\n' + ',\n'.join(inner + dump(v, depth + 1) for v in value) + '\n' + pad + ']'
    return json.dumps(value, ensure_ascii=False)


def diff(label, want, got, out):
    if want == got:
        return
    if isinstance(want, dict) and isinstance(got, dict):
        for k in sorted(set(want) | set(got)):
            diff(f'{label}.{k}', want.get(k), got.get(k), out)
    elif isinstance(want, list) and isinstance(got, list) and len(want) == len(got):
        for i, (w, g) in enumerate(zip(want, got)):
            diff(f'{label}[{i}]', w, g, out)
    else:
        out.append(f'{label}:\n  expected {json.dumps(want)}\n  observed {json.dumps(got)}')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--write', action='store_true', help='refreeze seed observations only')
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    fixtures = manifest['fixtures']
    by_name = {f['name']: f for f in fixtures}
    problems = []
    on_disk = sorted(p.name for p in FIXTURES.glob('*.bend'))
    listed = sorted(Path(f['file']).name for f in fixtures)
    if on_disk != listed or len(by_name) != len(fixtures):
        problems.append(f'fixture set mismatch: unlisted {sorted(set(on_disk) - set(listed))}, '
                        f'missing {sorted(set(listed) - set(on_disk))}, duplicates {len(fixtures) - len(by_name)}')
    for f in fixtures:
        if f['file'] != f'tests/compiler-nest/fixtures/{f["name"]}.bend':
            problems.append(f'{f["name"]}: file must be tests/compiler-nest/fixtures/<name>.bend')
    if sorted(manifest.get('knot_expected', [])) != sorted(
            f['name'] for f in fixtures if f.get('knot', {}).get('source') == 'knot_expected'):
        problems.append('top-level knot_expected list differs from the marked fixtures')

    seed, tools = environment()
    if not args.write:
        diff('seed', manifest.get('seed'), seed, problems)
        diff('tools', manifest.get('tools'), tools, problems)
    fresh = {f['name']: observe(f) for f in fixtures if (ROOT / f['file']).exists()}

    if args.write:
        manifest['seed'], manifest['tools'] = seed, tools
        for fixture in fixtures:
            if fixture['name'] in fresh:
                fixture.update(fresh[fixture['name']][0])
        MANIFEST.write_text(dump(manifest) + '\n')
    else:
        for fixture in fixtures:
            if fixture['name'] in fresh:
                for key, value in fresh[fixture['name']][0].items():
                    diff(f'{fixture["name"]}.{key}', fixture.get(key), value, problems)

    for fixture in fixtures:
        if fixture['name'] in fresh:
            observed, enums, entries, source = fresh[fixture['name']]
            problems += review({**fixture, **observed}, enums, entries, source, by_name)

    calls = sum(len(f[0]['observed']['calls']) for f in fresh.values())
    if problems:
        print('\n'.join(problems))
        print(f'FAILED: {len(problems)} difference(s) against {MANIFEST.relative_to(ROOT)}')
        sys.exit(1)
    verb = 'Refroze' if args.write else 'Reproduced'
    print(f'{verb} {len(fixtures)} fixtures and {calls} entry calls with the pinned seed '
          f'(bend {seed["version"]}, bun {tools["bun"]}); no differences.')


if __name__ == '__main__':
    main()
