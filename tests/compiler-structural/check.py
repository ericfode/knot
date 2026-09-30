#!/usr/bin/env python3
"""Invoke Bend and compare fixed observations. No source-language semantics."""
from __future__ import annotations
import datetime
import hashlib
import json
from pathlib import Path
import sys
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/compiler-structural/gate'
SEED = ROOT / 'scripts/bend-reference'
SEED_GUARD = ROOT / 'scripts/gates/seed_build.py'
sys.path.insert(0, str(SEED_GUARD.parent))
from seed_build import guard_seed_builds
RECEIPT = HERE / 'receipts/catalog.json'


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@guard_seed_builds(SEED)
def run(argv, timeout=45):
    try:
        p = subprocess.run([str(x) for x in argv], cwd=ROOT, text=True,
                           capture_output=True, timeout=timeout)
        return {'argv': [str(x) for x in argv], 'exit': p.returncode,
                'stdout': p.stdout, 'stderr': p.stderr}
    except subprocess.TimeoutExpired:
        return {'argv': [str(x) for x in argv], 'exit': None,
                'outcome': 'Exhausted', 'budget_seconds': timeout,
                'stdout': '', 'stderr': ''}


def successful(argv):
    r = run(argv)
    require(r['exit'] == 0, r)
    return r


def observe(result, expected):
    require(result['exit'] == expected['exit'], result)
    if 'stdout' in expected:
        require(result['stdout'].strip() == expected['stdout'], result)
    if 'diagnostic' in expected:
        require(expected['diagnostic'] in result['stderr'], result)
        require(result['stdout'] == '', result)


# Each witness and expected observation is frozen in cases.json or the boundary
# contract below. Mutants are never allowed to update either oracle.
MUTANTS = [
    ('allow-owned-data-field', 'catalog.bend', 'Bool.not(data),Bool.or(U32.is_eq(q,0),child)',
     'True{},Bool.or(U32.is_eq(q,0),child)', 'data-owns-type', 'catalog'),
    ('discard-fields', 'catalog.bend', 'C.Constructor{token,ps}',
     'C.Constructor{token,Nil{}}', 'field-quantities', 'catalog'),
    ('reverse-fields', 'catalog.bend',
     'fields(tail,types,data,Con{name,seen},U32.add(count,1)),rest =>\n                Done{Con{head,rest}}',
     'fields(tail,types,data,Con{name,seen},U32.add(count,1)),rest =>\n                Done{List.append(&2,C.Parameter,rest,[head])}',
     'field-quantities', 'catalog'),
    ('wrong-field-type', 'catalog.bend',
     'Done{C.Parameter{token,q,index}},u => C.invalid(C.Parameter,"data-field-kind",token)',
     'Done{C.Parameter{token,q,0}},u => C.invalid(C.Parameter,"data-field-kind",token)',
     'forward-field-type', 'catalog'),
    ('duplicate-field-accepted', 'catalog.bend',
     'S.choose(Result<S.Error,List<&2,C.Parameter>>,named(seen,name),u =>',
     'S.choose(Result<S.Error,List<&2,C.Parameter>>,False{},u =>',
     'duplicate-field', 'catalog'),
    ('field-bound-off-by-one', 'catalog.bend',
     'U32.is_eq(count,256),u => C.exhausted(List<&2,C.Parameter>,name),u =>\n        S.choose',
     'U32.is_eq(count,257),u => C.exhausted(List<&2,C.Parameter>,name),u =>\n        S.choose',
     'fields-257', 'catalog'),
    ('field-capability-accepted', 'check.bend',
     'C.unsupported(Unit,"constructor-fields",token)', 'Done{Unit{}}',
     'plain-field', 'compiler'),
]


def boundary_source(count):
    # Test-data generation only: an explicit vector of distinct source fields.
    fields = ', '.join(f'f{i}: Flag' for i in range(count))
    return ('type Flag is Data:\n  Off{}\ntype Box is Data:\n'
            f'  Box{{{fields}}}\ndef main() -> Flag:\n  Off{{}}\n')


def compile_observe(command, path, expected, output):
    marker = b'existing artifact must survive rejected compilation\n'
    output.write_bytes(marker)
    result = run([*command, path, output, 65536, 4096, 512, 4096, 65536])
    observe(result, expected)
    require(output.read_bytes() == marker, ('rejected compilation replaced output', result))
    return result


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((HERE / 'cases.json').read_text())
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'incomplete', 'seed_revision': manifest['seed_revision'],
              'scope': 'Structural declaration catalog only; field execution is Unsupported'}
    try:
        fixtures = sorted((HERE / 'fixtures').glob('*.bend'))
        require({str(p.relative_to(HERE)) for p in fixtures} ==
                {c['file'] for c in manifest['cases']}, 'fixture manifest mismatch')
        sources = sorted((ROOT / 'src').glob('*.bend'))
        paths = sources + fixtures + [Path(__file__), HERE / 'cases.json', HERE / 'observe.bend',
                ROOT / 'src/SPEC.md', ROOT / 'src/CONTRACT.json',
                ROOT / 'research/compiler-structural/SPEC.md']
        record['inputs'] = {str(p.relative_to(ROOT)): digest(p) for p in [*paths, SEED_GUARD]}
        record['tools'] = {t: successful([t, '--version'])['stdout'].strip()
                           for t in ('bun', 'node', 'python3')}
        record['proof'] = successful([SEED, ROOT / 'src/catalog-PROOF.bend'])
        require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
        record['builds'], lanes = [], {}
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
            commands = {}
            for name, entry in [('catalog', HERE / 'observe.bend'),
                                ('compiler', ROOT / 'src/compile-cli.bend')]:
                output = BUILD / (name + suffix)
                result = successful([SEED, entry, '-o', output])
                record['builds'].append({'lane': lane, 'target': name, 'result': result,
                                         'sha256': digest(output)})
                commands[name] = [*runtime, output]
            lanes[lane] = commands
        record['fixtures'] = []
        for case in manifest['cases']:
            path = HERE / case['file']
            reference = run([SEED, path])
            observe(reference, case['reference'])
            row = {'file': case['file'], 'reference': reference, 'lanes': {}}
            for lane, commands in lanes.items():
                catalog = run([*commands['catalog'], path]); observe(catalog, case['catalog'])
                compiled = compile_observe(commands['compiler'], path, case['compiler'], BUILD / f'{lane}-guard.wasm')
                row['lanes'][lane] = {'catalog': catalog, 'compiler': compiled}
            record['fixtures'].append(row)

        record['bounds'] = []
        for count in (256, 257):
            path = BUILD / f'fields-{count}.bend'
            path.write_text(boundary_source(count))
            reference = run([SEED, path]); observe(reference, {'exit': 0, 'stdout': 'Off{}'})
            for lane, commands in lanes.items():
                catalog = run([*commands['catalog'], path])
                if count == 256:
                    require(catalog['exit'] == 0 and catalog['stdout'].startswith('Catalogued\n'), catalog)
                    # Every ordered name/quantity/type and span has an explicit
                    # expectation; offsets follow this single generated source line.
                    offset = len('type Flag is Data:\n  Off{}\ntype Box is Data:\n  Box{')
                    expected_fields = []
                    for i in range(count):
                        name = f'f{i}'
                        column = offset - len('type Flag is Data:\n  Off{}\ntype Box is Data:\n')
                        expected_fields.append(f'{name}@{offset}:{offset+len(name)}:4:{column}=1:0;')
                        offset += len(name) + len(': Flag, ')
                    expected = 'Catalogued\n0 Flag Data{0 Off[];}\n1 Box Data{0 Box[' + ''.join(expected_fields) + '];}'
                    observe(catalog, {'exit': 0, 'stdout': expected})
                    cap = {'exit': 3, 'diagnostic': 'Unsupported\tcheck\tconstructor-fields\t'}
                else:
                    cap = {'exit': 4, 'diagnostic': 'Exhausted\tcheck\tbudget\t'}
                    observe(catalog, cap)
                compiled = compile_observe(commands['compiler'], path, cap, BUILD / f'{lane}-bound.wasm')
                record['bounds'].append({'count': count, 'lane': lane, 'reference': reference,
                                         'catalog': catalog, 'compiler': compiled})

        record['mutants'] = []
        for name, file, before, after, witness, target in MUTANTS:
            directory = BUILD / name
            directory.mkdir(exist_ok=True)
            for source in sources:
                shutil.copy2(source, directory / source.name)
            changed = directory / file
            text = changed.read_text()
            require(text.count(before) == 1, (name, 'mutation must be unique'))
            changed.write_text(text.replace(before, after))
            observer = directory / 'observe.bend'
            observer.write_text((HERE / 'observe.bend').read_text().replace('../../src/', './'))
            entry = observer if target == 'catalog' else directory / 'compile-cli.bend'
            typecheck = successful([SEED, entry, '--check-only'])
            require(typecheck['stdout'].strip() == 'All terms check.', typecheck)
            output = directory / 'mutant.js'
            build = successful([SEED, entry, '-o', output])
            if witness == 'fields-257':
                path = BUILD / 'fields-257.bend'
                expected = {'exit': 4, 'diagnostic': 'Exhausted\tcheck\tbudget\t'}
            else:
                case = next(c for c in manifest['cases'] if Path(c['file']).stem == witness)
                path, expected = HERE / case['file'], case[target]
            argv = ['bun', output, path]
            if target == 'compiler':
                artifact = directory / 'mutant.wasm'
                artifact.unlink(missing_ok=True)
                argv.append(artifact)
            actual = run(argv)
            require(actual['exit'] in (0, 2, 3, 4), actual)
            try:
                observe(actual, expected)
            except AssertionError:
                killed = True
            else:
                killed = False
            require(killed, (name, 'survived'))
            record['mutants'].append({'name': name, 'before': before, 'after': after,
                'source_sha256': digest(changed), 'typecheck': typecheck, 'build': build,
                'witness': str(path.relative_to(ROOT)), 'expected': expected,
                'actual': actual, 'outcome': 'semantic-kill'})
        record['status'] = 'passed'
    except Exception as e:
        record['failure'] = repr(e)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print(f'Structural catalog gate passed: {len(record["fixtures"])} seed fixtures, '
          f'{len(record["bounds"])} boundary pairs, {len(record["mutants"])} semantic mutants; {RECEIPT}')


if __name__ == '__main__':
    main()
