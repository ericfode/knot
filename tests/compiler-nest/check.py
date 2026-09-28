#!/usr/bin/env python3
"""Drive independent seed, Bend and Wasm lanes; contains no language semantics."""
from __future__ import annotations

import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/compiler-nest/gate'
RECEIPT = HERE / 'receipts/nest.json'
SEED = ['bun', ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']
HOST = ROOT / 'scripts/run-wasm.mjs'
FIELDS = '--profile=knot-fields-wasm-1'
_enum_spec = importlib.util.spec_from_file_location('enum_contract', ROOT / 'tests/compiler-wasm/check.py')
_enum_contract = importlib.util.module_from_spec(_enum_spec)
_enum_spec.loader.exec_module(_enum_contract)
# Explicitly authorized conservative outcomes; these NEVER count as conformance.
UNMET = {'rec-swapped-args', 'rec-alias'}


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, timeout=120):
    try:
        p = subprocess.run([str(x) for x in argv], cwd=ROOT, text=True,
                           capture_output=True, timeout=timeout,
                           env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
        return {'argv': [str(x) for x in argv], 'exit': p.returncode,
                'stdout': p.stdout, 'stderr': p.stderr}
    except subprocess.TimeoutExpired:
        return {'argv': [str(x) for x in argv], 'exit': None,
                'outcome': 'harness-timeout', 'stdout': '', 'stderr': ''}


def successful(argv):
    result = run(argv)
    require(result['exit'] == 0 and not result['stderr'], result)
    return result


def diagnostic(result, expected):
    require(result['exit'] == expected['exit'] and not result['stdout']
            and result['stderr'].startswith(expected['diagnostic']), (expected, result))


def checked(result):
    require(result['exit'] == 0 and result['stdout'].startswith('Checked\n')
            and not result['stderr'], result)


def evaluated(result, call):
    expected = f"Evaluated\t{call['type_id']}\t{call['tag']}\t{call['result']}{{}}"
    require(result['exit'] == 0 and result['stdout'].strip() == expected
            and not result['stderr'], (expected, result))


def compiled(command, source, output):
    output.unlink(missing_ok=True)
    result = successful([*command, source, output])
    require(output.exists() and result['stdout'].strip() == f'Built\t{output.stat().st_size}', result)
    return result


def executed(module, call, fields):
    result = successful(['node', HOST, *([FIELDS] if fields else []), module,
                         call['export'], *call['ordinals']])
    observation = json.loads(result['stdout'])
    require(observation['validated'] is True and observation['result'] == call['tag']
            and observation['export'] == call['export']
            and observation['arguments'] == call['ordinals'], (call, result))
    return result


def calls(case):
    return [dict(case['observed']['main'], export='main', ordinals=[]), *case['observed']['calls']]


def build_lanes(record):
    lanes = {}
    for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
        lanes[lane] = {}
        entries = {'check': ROOT / 'src/check-cli.bend', 'eval': ROOT / 'src/eval-cli.bend',
                   'enum': ROOT / 'src/compile-cli.bend', 'fields': ROOT / 'tests/compiler-fields-wasm/compile.bend'}
        for phase, entry in entries.items():
            output = BUILD / (phase + suffix)
            result = successful([*SEED, entry, '-o', output])
            record['builds'].append({'lane': lane, 'phase': phase, 'result': result, 'sha256': digest(output)})
            lanes[lane][phase] = [*runtime, output]
    return lanes


def fixtures(record, manifest, lanes):
    for case in manifest['fixtures']:
        require(digest(ROOT / case['file']) == case['sha256'], ('fixture hash', case['name']))
        fields = 'fields' in case['requires']
        item = {'name': case['name'], 'file': case['file'], 'sha256': case['sha256'],
                'expected': case['knot'], 'profile': 'knot-fields-wasm-1' if fields else 'knot-enum-1', 'lanes': {}}
        accepted = case['knot']['outcome'] == 'Accepted'
        pending = case['name'] in UNMET
        expected = {'exit': 3, 'diagnostic': 'Unsupported\tcheck\trecursive-call\t'} if pending else case['knot']
        module_hashes = []
        for lane, commands in lanes.items():
            source = ROOT / case['file']
            check = run([*commands['check'], source])
            item['lanes'][lane] = {'check': check}
            output = BUILD / f"{case['name']}-{lane}.wasm"
            if accepted:
                checked(check)
                compile_result = compiled(commands['fields' if fields else 'enum'], source, output)
                module_hashes.append(digest(output))
                decoder = successful(['wasm2wat', output])
                item['lanes'][lane].update(compile=compile_result, module_sha256=digest(output),
                                           wat_sha256=hashlib.sha256(decoder['stdout'].encode()).hexdigest(), calls=[])
                if not fields:
                    item['lanes'][lane]['instructions'] = _enum_contract.mvp_instructions(decoder['stdout'])
                for call in calls(case):
                    evaluation = run([*commands['eval'], source, call['export'], 65536, *call['ordinals']])
                    evaluated(evaluation, call)
                    execution = executed(output, call, fields)
                    item['lanes'][lane]['calls'].append({'export': call['export'], 'ordinals': call['ordinals'],
                        'type_id': call['type_id'], 'tag': call['tag'], 'eval': evaluation, 'wasm': execution})
            else:
                diagnostic(check, expected)
                evaluation = run([*commands['eval'], source, 'main', 65536])
                diagnostic(evaluation, expected)
                marker = b'existing artifact: rejection must preserve this\n'
                output.write_bytes(marker)
                compile_result = run([*commands['fields' if fields else 'enum'], source, output])
                diagnostic(compile_result, expected)
                require(output.read_bytes() == marker, ('output changed', compile_result))
                item['lanes'][lane].update(eval=evaluation, compile=compile_result, artifact_preserved=True)
        if accepted:
            require(len(set(module_hashes)) == 1, ('native/Bun bytes', case['name'], module_hashes))
        if pending:
            item['disposition'] = 'unmet: seed rejects; complete decreasing-call rule is not implemented'
            record['unmet'].append(item)
        else:
            record['fixtures'].append(item)


def controls(record, fixed, lanes):
    wrapper = ROOT / '.local/nest/tree-shallow.bend'
    wrapper.parent.mkdir(parents=True, exist_ok=True)
    wrapper.write_text('import ../../tests/compiler-nest/controls/tree-arena.bend as F\n\ndef main() -> F.Flag:\n  F.shallow()\n')
    for name, case in fixed['fixtures'].items():
        source = ROOT / case['file']
        require(digest(source) == case['sha256'], ('control changed', name))
        ref = run(case['seed']['command'])
        require(all(ref[k] == case['seed'][k] for k in ('exit', 'stdout', 'stderr')), (case['seed'], ref))
        if name == 'tree-arena':
            shallow = run(case['shallow_seed']['command'])
            require(all(shallow[k] == case['shallow_seed'][k] for k in ('exit', 'stdout', 'stderr')), shallow)
        for lane, commands in lanes.items():
            if name == 'tree-arena':
                check = run([*commands['check'], source]); checked(check)
                output = BUILD / f'tree-arena-{lane}.wasm'
                compile_result = compiled(commands['fields'], source, output)
                record['boundaries'].append({'name': name, 'lane': lane, 'phase': 'check', 'result': check})
                record['boundaries'].append({'name': name, 'lane': lane, 'phase': 'compile', 'result': compile_result,
                                             'module_sha256': digest(output)})
                for entry, expected in case['expectations'].items():
                    evaluation = successful([*commands['eval'], source, entry, 1048576])
                    require(evaluation['stdout'].strip() == expected['eval'], evaluation)
                    execution = run(['node', HOST, FIELDS, output, entry])
                    if 'wasm_exit' in expected:
                        diagnostic(execution, {'exit': expected['wasm_exit'], 'diagnostic': expected['wasm_diagnostic']})
                    else:
                        require(execution['exit'] == 0 and not execution['stderr']
                                and json.loads(execution['stdout'])['result'] == expected['wasm'], execution)
                    record['boundaries'].append({'name': name, 'lane': lane, 'export': entry, 'phase': 'eval', 'result': evaluation})
                    record['boundaries'].append({'name': name, 'lane': lane, 'export': entry, 'phase': 'wasm', 'result': execution})
            else:
                for phase in ('check', 'eval', 'fields'):
                    output = BUILD / f'{name}-{lane}-rejected.wasm'
                    marker = b'control artifact must survive\n'
                    args = [source]
                    if phase == 'eval':
                        args += ['main', 65536]
                    elif phase == 'fields':
                        output.write_bytes(marker); args += [output]
                    actual = run([*commands[phase], *args]); diagnostic(actual, case['expectations'])
                    if phase == 'fields':
                        require(output.read_bytes() == marker, ('control output changed', actual))
                    record['boundaries'].append({'name': name, 'lane': lane, 'phase': phase, 'result': actual})


SPECIFICITY = '''def specificity(fuel: Nat, node: S.Node) -> U32:
  match fuel node:
    case 0n _: 0
    case 1n+ +n S.Arm{arm,pattern,body}: specificity(n,pattern)
    case 1n+ +n S.Constructor{token,args}: U32.add(1,specificity(n,S.Sequence{args}))
    case 1n+ +n S.Sequence{Con{head,tail}}: U32.add(specificity(n,head),specificity(n,S.Sequence{tail}))
    case _ _: 0

def more_specific(a: S.Node, b: S.Node) -> Bool:
  U32.is_ge(specificity(512n,a),specificity(512n,b))

'''

# Each mutation changes a checked compiler, not the frozen source fixtures.
MUTANTS = [
    {'name': 'last-row-wins', 'file': 'matrix.bend',
     'old': 'prepare(fuel,rows,List.length', 'new': 'prepare(fuel,List.reverse(&2,S.Node,rows),List.length',
     'witness': 'first-match-multi', 'phase': 'eval', 'export': 'rank', 'args': [1, 1], 'wrong_tag': 2},
    {'name': 'most-specific-row-wins', 'file': 'matrix.bend',
     'old': 'prepare(fuel,rows,List.length', 'new': 'prepare(fuel,List.sort(~S.Node,~more_specific,rows),List.length',
     'prefix': SPECIFICITY, 'witness': 'first-match-nested', 'phase': 'eval', 'export': 'probe', 'args': [1, 1, 0, 1], 'wrong_tag': 2},
    {'name': 'drop-default-matrix', 'file': 'matrix.bend',
     'old': 'without(rows,ctor),work}', 'new': 'Nil{},work}',
     'witness': 'wildcard-default', 'phase': 'check',
     'wrong': {'exit': 2, 'diagnostic': 'Invalid\tcheck\tmissing-arm\t'}},
    {'name': 'accept-nonexhaustive-matrix', 'file': 'check.bend',
     'old': 'Nat.is_eq(List.length(&2,C.Constructor,tokens),List.length(&2,U32,seen))', 'new': 'True{}',
     'witness': 'multi-missing', 'phase': 'check', 'wrong': {'exit': 0}},
    {'name': 'bind-erased-nested-field-live', 'file': 'matrix.bend',
     'old': '+actual = P.quantity(q,1,mark)',
     'new': '+actual = P.quantity(unerase(q),1,mark)',
     'prefix': 'def unerase(+q: U32) -> U32:\n  S.choose(U32,U32.is_eq(q,0),u => 1,u => q)\n\n',
     'witness': 'erased-nested-live-use', 'phase': 'check', 'wrong': {'exit': 0}},
    {'name': 'reuse-affine-through-nested-alias', 'file': 'scope.bend',
     'old': 'contains(ys,h),u => C.invalid', 'new': 'False{},u => C.invalid',
     'witness': 'nested-alias-affine', 'phase': 'check', 'wrong': {'exit': 0}},
]


def mutants(record, manifest, fixed):
    cases = {c['name']: c for c in manifest['fixtures']}
    for mutation in MUTANTS:
        directory = BUILD / mutation['name']; directory.mkdir(exist_ok=True)
        for source in (ROOT / 'src').glob('*.bend'):
            shutil.copy2(source, directory / source.name)
        target = directory / mutation['file']; text = target.read_text()
        require(text.count(mutation['old']) == 1, ('mutation anchor', mutation['name']))
        text = text.replace(mutation['old'], mutation['new'])
        if mutation.get('prefix'):
            text = text.replace('def start(', mutation['prefix'] + 'def start(', 1)
        target.write_text(text)
        phase = mutation['phase']
        entry = directory / f'{phase}-cli.bend'
        proof = successful([*SEED, entry, '--check-only'])
        require(proof['stdout'].strip() == 'All terms check.', proof)
        case = cases.get(mutation['witness']) or fixed['fixtures'][mutation['witness']]
        expected = case.get('knot') or case['expectations']
        item = {'name': mutation['name'], 'file': mutation['file'], 'old': mutation['old'], 'new': mutation['new'],
                'prefix': mutation.get('prefix'), 'mutated_sha256': digest(target), 'typecheck': proof,
                'witness': mutation['witness'], 'expected': expected, 'lanes': {}}
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
            output = directory / ('mutant' + suffix)
            build = successful([*SEED, entry, '-o', output])
            args = [ROOT / case['file']]
            if phase == 'eval':
                call = next(c for c in case['observed']['calls'] if c['export'] == mutation['export'] and c['ordinals'] == mutation['args'])
                args += [call['export'], 65536, *call['ordinals']]
                actual = run([*runtime, output, *args])
                wrong = {**call, 'tag': mutation['wrong_tag']}
                require(actual['exit'] == 0 and not actual['stderr']
                        and actual['stdout'].startswith(f"Evaluated\t{wrong['type_id']}\t{wrong['tag']}\t"), actual)
                require(wrong['tag'] != call['tag'], ('equivalent mutant', mutation['name']))
                try:
                    evaluated(actual, call)
                except AssertionError:
                    killed = True
                else:
                    killed = False
            else:
                actual = run([*runtime, output, *args])
                if mutation['wrong']['exit'] == 0:
                    checked(actual)
                else:
                    diagnostic(actual, mutation['wrong'])
                try:
                    checked(actual) if expected['exit'] == 0 else diagnostic(actual, expected)
                except AssertionError:
                    killed = True
                else:
                    killed = False
            require(killed, ('mutant survived', mutation['name'], actual))
            item['lanes'][lane] = {'build': build, 'actual': actual, 'outcome': 'semantic-kill'}
        record['mutants'].append(item)


def enum_bytes(record, lanes):
    baseline = json.loads((ROOT / 'tests/compiler-fields-wasm/enum-baseline.json').read_text())
    require(len(baseline) == 25, 'frozen enum module count')
    for source, expected in baseline.items():
        for lane, commands in lanes.items():
            for profile in ('enum', 'fields'):
                output = BUILD / f'enum-{Path(source).stem}-{lane}-{profile}.wasm'
                build = compiled(commands[profile], ROOT / source, output)
                require(digest(output) == expected, (source, lane, profile, expected, digest(output)))
                record['enum_preservation'].append({'file': source, 'lane': lane, 'profile': profile,
                                                   'sha256': digest(output), 'build': build})


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((HERE / 'expectations.json').read_text())
    fixed = json.loads((HERE / 'control-expectations.json').read_text())
    paths = [*sorted((ROOT / 'src').glob('*.bend')), ROOT / 'src/SPEC.md', ROOT / 'src/CONTRACT.json',
             *sorted(HERE.glob('*.py')), *sorted(HERE.glob('*.json')), *sorted(HERE.glob('*.md')),
             *sorted((HERE / 'fixtures').glob('*.bend')), *sorted((HERE / 'controls').glob('*.bend')),
             ROOT / 'tests/compiler-fields-wasm/compile.bend', ROOT / 'tests/compiler-fields-wasm/enum-baseline.json', HOST]
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
              'inputs': {str(p.relative_to(ROOT)): digest(p) for p in paths},
              'seed': manifest['seed'], 'frozen_tools': manifest['tools'],
              'builds': [], 'fixtures': [], 'unmet': [], 'mutants': [], 'boundaries': [], 'enum_preservation': []}
    try:
        record['oracle'] = successful(['python3', HERE / 'regen.py'])
        require('no differences' in record['oracle']['stdout'], record['oracle'])
        record['tools'] = {tool: successful([tool, '--version'])['stdout'].strip()
                           for tool in ('bun', 'node', 'python3', 'wasm2wat')}
        require(record['tools']['node'] == 'v22.22.3' and record['tools']['bun'] == '1.3.14', record['tools'])
        record['proof'] = successful([*SEED, ROOT / 'src/matrix-PROOF.bend'])
        require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
        lanes = build_lanes(record)
        fixtures(record, manifest, lanes)
        controls(record, fixed, lanes)
        enum_bytes(record, lanes)
        mutants(record, manifest, fixed)
        require(all(digest(ROOT / p) == h for p, h in record['inputs'].items()), 'Inputs changed during gate')
        record['counts'] = {
            'seed_fixtures': len(manifest['fixtures']),
            'seed_entry_calls': sum(len(c['observed']['calls']) for c in manifest['fixtures']),
            'matched_frozen_outcomes': len(record['fixtures']), 'unmet_frozen_outcomes': len(record['unmet']),
            'check_observations': 2 * len(record['fixtures']),
            'unmet_phase_observations': 6 * len(record['unmet']),
            'accepted_books': sum(c['expected']['exit'] == 0 for c in record['fixtures']),
            'evaluation_values': sum(len(lane.get('calls', [])) for c in record['fixtures'] for lane in c['lanes'].values()),
            'wasm_values': sum(len(lane.get('calls', [])) for c in record['fixtures'] for lane in c['lanes'].values()),
            'rejected_phase_observations': sum(3 * len(c['lanes']) for c in record['fixtures'] if c['expected']['exit'] != 0),
            'boundary_observations': len(record['boundaries']), 'enum_hash_checks': len(record['enum_preservation']),
            'mutants': len(record['mutants']), 'semantic_kills': sum(len(c['lanes']) for c in record['mutants'])}
        record['qualification'] = {'complete': not record['unmet'],
            'limits': 'The gate monitors two authorized conservative recursion outcomes; neither is counted as frozen conformance.'}
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    c = record['counts']
    print(f"Nest gate passed within stated scope: {c['seed_fixtures']} seed fixtures, {c['seed_entry_calls']} seed calls; "
          f"{c['matched_frozen_outcomes']}/40 frozen outcomes, {c['unmet_frozen_outcomes']} UNMET; "
          f"{c['evaluation_values']} evaluator values, {c['wasm_values']} Wasm values, "
          f"{c['boundary_observations']} boundary observations, {c['enum_hash_checks']} enum hashes, "
          f"{c['mutants']} mutants / {c['semantic_kills']} semantic kills")


if __name__ == '__main__':
    main()
