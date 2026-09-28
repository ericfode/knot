#!/usr/bin/env python3
"""Build Bend, invoke independent lanes, compare frozen observations; no semantics."""
from __future__ import annotations
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
TIMEOUT_SCALE = float(__import__('os').environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))  # harness hang guard only; gates set it under load

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
HOST_CHECKS = json.loads((ROOT / 'tests/compiler-modules/host-check-expectations.json').read_text())['entries']
BUILD = ROOT / '.local/compiler-fields/gate'
SEED = ROOT / 'scripts/bend-reference'
RECEIPT = HERE / 'receipts/fields.json'


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, timeout=45*TIMEOUT_SCALE):
    try:
        p = subprocess.run([str(x) for x in argv], cwd=ROOT, text=True,
                           capture_output=True, timeout=timeout)
        return {'argv': [str(x) for x in argv], 'exit': p.returncode,
                'stdout': p.stdout, 'stderr': p.stderr}
    except subprocess.TimeoutExpired:
        return {'argv': [str(x) for x in argv], 'exit': None,
                'outcome': 'harness-timeout', 'stdout': '', 'stderr': ''}


def successful(argv):
    result = run(argv)
    require(result['exit'] == 0, result)
    return result


def observe(result, expected):
    require(result['exit'] == expected['exit'], (expected, result))
    if 'stdout' in expected:
        require(result['stdout'].strip() == expected['stdout'], (expected, result))
    if 'contains' in expected:
        require(expected['contains'] in result['stdout'], (expected, result))
    if 'diagnostic' in expected:
        require(expected['diagnostic'] in result['stderr'] and not result['stdout'], (expected, result))


MUTANTS = [
    ('promote-erased-field', 'patterns.bend',
     'Bool.or(U32.is_eq(field,0),U32.is_eq(parent,0))', 'U32.is_eq(parent,0)',
     'erased-field-promote', 'check'),
    ('discard-parent-demand', 'check.bend',
     'run(n,Rebuild{head},catalog,current,E.live_scope(scope,q))',
     'run(n,Rebuild{head},catalog,current,E.live_scope(scope,0))',
     'parent-twice', 'check'),
    ('refine-by-spelling', 'check.bend',
     'S.bind(C.Binding,C.Checked,E.find_level(bindings,level),binding =>',
     'S.bind(C.Binding,C.Checked,E.lookup(scope,token),binding =>',
     'reconstruction-shadow', 'eval'),
    ('fields-after-parameters', 'patterns.bend',
     'List.append(&2,U32,E.levels(introduced),open)',
     'List.append(&2,U32,open,E.levels(introduced))',
     'field-before-parameter', 'check'),
    ('reverse-live-fields', 'eval.bend',
     'Object{type_id,tag,List.reverse(&2,Value,values)}',
     'Object{type_id,tag,values}', 'mixed-live-order', 'eval'),
    ('forget-reusable-field', 'patterns.bend',
     'Bool.or(U32.is_eq(field,2),Bool.or(U32.is_eq(parent,2),U32.is_eq(mark,2)))',
     'Bool.or(U32.is_eq(parent,2),U32.is_eq(mark,2))',
     'reusable-field', 'check'),
    ('execute-erased-field', 'eval.bend',
     'U32.is_eq(q,0),u => Done{Fields{type_id,tag,params,args,env,values,frames}}',
     'False{},u => Done{Fields{type_id,tag,params,args,env,values,frames}}',
     'erased-forward', 'fuel'),
    ('ignore-inspection-capacity', 'eval.bend',
     'Nat.is_le(size,capacity)', 'True{}', 'inspection-capacity', 'bounds'),
    ('allow-level-overflow', 'patterns.bend',
     'U32.is_ge(level,4096)', 'U32.is_gt(level,4096)', 'levels', 'bounds'),
]


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((HERE / 'cases.json').read_text())
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'incomplete', 'seed_revision': manifest['seed_revision'],
              'scope': 'Structural checking and live-field tree evaluator. Owned heap and Wasm field lowering remain unimplemented.'}
    try:
        fixtures = sorted((HERE / 'fixtures').glob('*.bend'))
        require({str(p.relative_to(HERE)) for p in fixtures} ==
                {c['file'] for c in manifest['cases']}, 'Fixture manifest mismatch')
        paths = sorted((ROOT / 'src').glob('*.bend')) + fixtures + [Path(__file__), HERE / 'cases.json', HERE / 'bounds.bend',
                ROOT / 'src/SPEC.md', ROOT / 'src/CONTRACT.json', ROOT / 'research/compiler-fields/SPEC.md']
        record['inputs'] = {str(p.relative_to(ROOT)): digest(p) for p in paths}
        record['tools'] = {t: successful([t, '--version'])['stdout'].strip() for t in ('bun', 'node', 'python3')}
        record['proof'] = successful([SEED, ROOT / 'src/fields-PROOF.bend'])
        require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
        record['builds'], lanes = [], {}
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
            lanes[lane] = {}
            for phase in ('check', 'eval', 'compile'):
                output = BUILD / (phase + suffix)
                result = successful([SEED, ROOT / f'src/{phase}-cli.bend', '-o', output])
                record['builds'].append({'lane': lane, 'phase': phase, 'result': result, 'sha256': digest(output)})
                lanes[lane][phase] = [*runtime, output]
        record['fixtures'] = []
        for case in manifest['cases']:
            path = HERE / case['file']
            reference = run([SEED, path, *case.get('reference_args', [])]); observe(reference, case['reference'])
            item = {'case': case['name'], 'reference': reference, 'lanes': {}}
            for lane, commands in lanes.items():
                checked = run([*commands['check'], path]); observe(checked, case['check'])
                evaluated = run([*commands['eval'], path, 'main', 4096]); observe(evaluated, case['eval'])
                output = BUILD / (case['name'] + '-' + lane + '.wasm')
                marker = b'existing artifact: rejected compilation must preserve it\n'
                output.write_bytes(marker)
                compiled = run([*commands['compile'], path, output]); observe(compiled, case['compile'])
                require(output.read_bytes() == marker, ('artifact changed', compiled))
                item['lanes'][lane] = {'check': checked, 'eval': evaluated, 'compile': compiled, 'artifact_preserved': True}
            record['fixtures'].append(item)
        record['budgets'] = []
        cases = {c['name']: c for c in manifest['cases']}
        for lane, commands in lanes.items():
            for name, depth, transitions in [('open', 5, 14), ('erased-forward', 6, 16), ('nested-reconstruction', 14, 30)]:
                case = cases[name]; path = HERE / case['file']
                for budget in (0, depth - 1, depth):
                    result = run([*commands['check'], path, 65536, budget])
                    observe(result, case['check'] if budget == depth else {'exit': 4, 'diagnostic': 'Exhausted\tcheck\tbudget\t'})
                    record['budgets'].append({'lane': lane, 'phase': 'check', 'case': name, 'budget': budget, 'result': result})
                for budget in (0, transitions - 1, transitions):
                    result = run([*commands['eval'], path, 'main', budget])
                    observe(result, case['eval'] if budget == transitions else {'exit': 4, 'diagnostic': 'Exhausted\teval\tbudget\t'})
                    record['budgets'].append({'lane': lane, 'phase': 'eval', 'case': name, 'budget': budget, 'result': result})
        record['host_boundaries'] = []
        for lane, commands in lanes.items():
            for args, code in [(['open', 4096, 0], 'structured-argument'), (['open', 4096, 1], 'argument-range'), (['main', 4096, 0], 'argument-arity')]:
                result = run([*commands['eval'], HERE / 'fixtures/open.bend', *args])
                observe(result, {'exit': 5, 'diagnostic': 'HostFailure\tinvoke\t' + code})
                record['host_boundaries'].append({'lane': lane, 'result': result})
        expected_bounds = 'Next 4096\nExhausted\tcheck\tbudget\t0:0:1:0\nExhausted\tinspect\tbudget\t0:0:0:0\nOff{}\nExhausted\tinspect\tbudget\t0:0:0:0\nx'
        record['bounds'] = []
        for suffix, runtime in [('', []), ('.js', ['bun'])]:
            output = BUILD / ('bounds' + suffix)
            compiled = successful([SEED, HERE / 'bounds.bend', '-o', output])
            result = run([*runtime, output]); observe(result, {'exit': 0, 'stdout': expected_bounds})
            record['bounds'].append({'build': compiled, 'result': result, 'sha256': digest(output)})
        record['mutants'] = []
        for name, file, old, new, witness, phase in MUTANTS:
            directory = BUILD / name; directory.mkdir(exist_ok=True)
            for source in (ROOT / 'src').glob('*.bend'): shutil.copy2(source, directory / source.name)
            shutil.copytree(ROOT / 'src/host', directory / 'host', dirs_exist_ok=True)
            target = directory / file; source = target.read_text()
            require(source.count(old) == 1, (name, 'mutation must be unique'))
            target.write_text(source.replace(old, new))
            if phase == 'bounds':
                entry = directory / 'bounds.bend'
                entry.write_text((HERE / 'bounds.bend').read_text().replace('../../src/', './'))
                args = []; expected = {'exit': 0, 'stdout': expected_bounds}
            else:
                entry = directory / ('check-cli.bend' if phase == 'check' else 'eval-cli.bend')
                case = cases[witness]; args = [HERE / case['file']]
                if phase != 'check': args += ['main', 16 if phase == 'fuel' else 4096]
                expected = case['check' if phase == 'check' else 'eval']
            typecheck = successful([SEED, entry, '--check-only'])
            require(typecheck['stdout'].strip() == HOST_CHECKS.get(entry.name, {'stdout': 'All terms check.'})['stdout'].strip(), typecheck)
            output = directory / 'mutant.js'; compiled = successful([SEED, entry, '-o', output])
            actual = run(['bun', output, *args])
            require(actual['exit'] in (0, 2, 3, 4), ('not a semantic observation', actual))
            try: observe(actual, expected)
            except AssertionError: killed = True
            else: killed = False
            require(killed, (name, 'survived'))
            record['mutants'].append({'name': name, 'file': file, 'old': old, 'new': new,
                'sha256': digest(target), 'typecheck': typecheck, 'build': compiled,
                'witness': witness, 'phase': phase, 'expected': expected, 'actual': actual, 'outcome': 'semantic-kill'})
        require(all(digest(ROOT / p) == h for p, h in record['inputs'].items()), 'Inputs changed during gate')
        record['status'] = 'passed'
    except Exception as e:
        record['failure'] = repr(e)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print(f"Fields gate passed: {len(record['fixtures'])} seed fixtures, {6*len(record['fixtures'])} native/Bun phase observations, {len(record['budgets'])} budget probes, 6 host probes, 12 level/inspection observations, {len(record['mutants'])} semantic mutants; {RECEIPT}")


if __name__ == '__main__':
    main()
