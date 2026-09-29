#!/usr/bin/env python3
"""Round-2 regressions, enum whitelist, semantic mutants and differential fuzz."""
import datetime
import importlib.util
import json
from pathlib import Path
import shutil

import check as gate
import fuzz

HERE = Path(__file__).resolve().parent
BUILD = gate.ROOT / '.local/compiler-nest/review'
RECEIPT = HERE / 'receipts/review.json'
spec = importlib.util.spec_from_file_location('enum_gate', gate.ROOT / 'tests/compiler-wasm/check.py')
enum_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(enum_gate)


def fixtures(record, manifest, lanes):
    for case in manifest['fixtures']:
        source = gate.ROOT / case['file']
        gate.require(gate.digest(source) == case['sha256'], ('review fixture hash', case['name']))
        item = {'name': case['name'], 'lanes': {}}
        hashes = []
        for lane, commands in lanes.items():
            observed = {'check': gate.run([*commands['check'], source])}
            output = BUILD / f'{case["name"]}-{lane}.wasm'
            if case['knot']['exit'] == 0:
                gate.checked(observed['check'])
                observed['compile'] = gate.compiled(commands['fields' if case['fields'] else 'enum'], source, output)
                if observed['compile'].get('outcome') == 'Exhausted (host)':
                    # The Bun lane's own limit: the native lane holds the module, the evaluator still answers here.
                    observed['calls'] = []
                    for call in case['calls']:
                        value = gate.run([*commands['eval'], source, call['export'], 65536, *call['ordinals']])
                        gate.evaluated(value, call)
                        observed['calls'].append({'export': call['export'], 'arguments': call['ordinals'], 'eval': value, 'wasm': None})
                    item['lanes'][lane] = observed
                    continue
                hashes.append(gate.digest(output))
                wat = gate.successful(['wasm2wat', output])['stdout']
                observed['module_sha256'] = gate.digest(output)
                if not case['fields']:
                    observed['instructions'] = enum_gate.mvp_instructions(wat)
                observed['calls'] = []
                for call in case['calls']:
                    value = gate.run([*commands['eval'], source, call['export'], 65536, *call['ordinals']])
                    gate.evaluated(value, call)
                    wasm = gate.executed(output, call, case['fields'])
                    observed['calls'].append({'export': call['export'], 'arguments': call['ordinals'], 'eval': value, 'wasm': wasm})
            else:
                gate.diagnostic(observed['check'], case['knot'])
                observed['eval'] = gate.run([*commands['eval'], source, 'main', 65536])
                gate.diagnostic(observed['eval'], case['knot'])
                # Both public profiles must reject before opening an artifact.
                for profile in ('enum', 'fields'):
                    output.write_bytes(b'preserve rejected artifact\n')
                    result = gate.run([*commands[profile], source, output])
                    gate.diagnostic(result, case['knot'])
                    gate.require(output.read_bytes() == b'preserve rejected artifact\n', result)
                    observed[profile] = result
            item['lanes'][lane] = observed
        if hashes:
            gate.require(len(set(hashes)) == 1, ('review native/Bun module equality', hashes))
        record['fixtures'].append(item)


MUTANTS = [
    {'name': 'refine-default-to-constant', 'file': 'scope.bend',
     'old': 'u => C.Reference{token,level,type_id})),', 'new': 'u => C.Value{token,type_id,0})),',
     'witness': 'default-alias-reuse', 'phase': 'check', 'wrong': {'exit': 0}},
    {'name': 'skip-empty-default-body', 'file': 'check.bend',
     'old': 'run(n,Expression{no,wanted},catalog,current,E.residual(scope,binding,List.is_empty(&2,S.Token,tags)))',
     'new': 'S.choose(Result<S.Error,C.Checked>,List.is_empty(&2,S.Token,tags),u => Done{C.Checked{C.Case{token,level,0,Nil{}},0,Nil{}}},u => run(n,Expression{no,wanted},catalog,current,E.residual(scope,binding,List.is_empty(&2,S.Token,tags))))',
     'witness': 'trailing-wild-free-name', 'phase': 'check', 'wrong': {'exit': 0}},
    {'name': 'reference-anonymous-binder', 'file': 'scope.bend',
     'old': 'S.matches(name,"_"),u => C.invalid', 'new': 'False{},u => C.invalid',
     'witness': 'underscore-use', 'phase': 'check', 'wrong': {'exit': 0}},
    {'name': 'partition-expansion-budget', 'file': 'matrix.bend',
     'old': 'expand(n,yes,types,opened(fields),work)', 'new': 'expand(n,yes,types,opened(fields),U32.div(work,2))',
     'witness': 'deep-13', 'phase': 'check', 'wrong': {'exit': 4, 'diagnostic': 'Exhausted\tcheck\tbudget\t'}},
    {'name': 'reject-comma-scrutinees', 'file': 'parse.bend',
     'old': 'MatchTail{+token,+value,+column}:\n      S.choose(Result<S.Error,Parsed>,starts(tokens,","),',
     'new': 'MatchTail{+token,+value,+column}:\n      S.choose(Result<S.Error,Parsed>,False{},',
     'witness': 'comma-c1', 'phase': 'check', 'wrong': {'exit': 2, 'diagnostic': 'Invalid\tparse\t'}},
    {'name': 'reject-variable-let-column', 'file': 'matrix.bend',
     'old': 'u => U32.is_eq(U32.add(level,1),next)', 'new': 'u => False{}',
     'witness': 'let-var-match', 'phase': 'check', 'wrong': {'exit': 2, 'diagnostic': 'Invalid\tcheck\tunmatchable-binder\t'}},
]


def enum_control(record, lanes):
    source = HERE / 'fixtures/empty-type.bend'
    for lane, commands in lanes.items():
        output = BUILD / f'empty-{lane}.wasm'
        result = gate.compiled(commands['enum'], source, output)
        wat = gate.successful(['wasm2wat', output])['stdout']
        ops = enum_gate.mvp_instructions(wat)
        gate.require('unreachable' not in ops and 'i32.const' in ops, ops)
        record['enum_whitelist'].append({'lane': lane, 'compile': result, 'instructions': ops,
                                         'sha256': gate.digest(output)})
    directory = BUILD / 'empty-unreachable'
    directory.mkdir(exist_ok=True)
    for source_file in (gate.ROOT / 'src').glob('*.bend'):
        shutil.copy2(source_file, directory / source_file.name)
    target = directory / 'wasm.bend'
    text = target.read_text()
    old = 'Branches{Nil{},index,pointer}: code(W.bytes(cap,[65,0]),next)'
    gate.require(text.count(old) == 1, 'empty encoding mutation anchor')
    target.write_text(text.replace(old, 'Branches{Nil{},index,pointer}: code(W.bytes(cap,[0]),next)'))
    proof = gate.successful([*gate.SEED, directory / 'compile-cli.bend', '--check-only'])
    gate.require(proof['stdout'].strip() == 'All terms check.', proof)
    item = {'name': 'empty-unreachable', 'typecheck': proof, 'lanes': {}}
    for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
        binary = directory / ('compile' + suffix)
        gate.successful([*gate.SEED, directory / 'compile-cli.bend', '-o', binary])
        output = directory / f'{lane}.wasm'
        gate.compiled([*runtime, binary], source, output)
        wat = gate.successful(['wasm2wat', output])['stdout']
        # The mutant is a valid executable module; only the declared whitelist kills it.
        gate.executed(output, {'export': 'main', 'ordinals': [], 'tag': 1}, False)
        try:
            enum_gate.mvp_instructions(wat)
        except AssertionError as error:
            gate.require('unreachable' in str(error), error)
            item['lanes'][lane] = {'outcome': 'semantic-kill', 'assertion': str(error)}
        else:
            raise AssertionError('empty-unreachable survived')
    record['mutants'].append(item)


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    gate.BUILD = BUILD
    manifest = json.loads((HERE / 'review-expectations.json').read_text())
    paths = [*sorted((gate.ROOT / 'src').glob('*.bend')), *sorted(HERE.glob('*.py')),
             HERE / 'review-expectations.json', *sorted((HERE / 'review-fixtures').glob('*.bend'))]
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
              'inputs': {str(p.relative_to(gate.ROOT)): gate.digest(p) for p in paths},
              'builds': [], 'fixtures': [], 'mutants': [], 'enum_whitelist': []}
    try:
        record['oracle'] = gate.successful(['python3', HERE / 'review_seed.py'])
        lanes = gate.build_lanes(record)
        fixtures(record, manifest, lanes)
        enum_control(record, lanes)
        gate.MUTANTS = MUTANTS
        gate.mutants(record, manifest, {'fixtures': {}})
        record['fuzz'] = fuzz.check(lanes, BUILD / 'fuzz')
        gate.require(record['fuzz']['programs'] == 3000, 'fixed fuzz coverage')
        gate.require(all(gate.digest(gate.ROOT / p) == h for p, h in record['inputs'].items()), 'Review inputs changed')
        accepted = sum(c['knot']['exit'] == 0 for c in manifest['fixtures'])
        record['counts'] = {'seed_fixtures': len(manifest['fixtures']), 'seed_calls': sum(len(c['calls']) for c in manifest['fixtures']),
                            'check_observations': 2 * len(manifest['fixtures']), 'accepted_books': accepted,
                            'evaluator_values': 2 * sum(len(c['calls']) for c in manifest['fixtures']),
                            'wasm_values': 2 * sum(len(c['calls']) for c in manifest['fixtures']),
                            'rejected_phase_observations': 8 * (len(manifest['fixtures']) - accepted),
                            'mutants': len(record['mutants']), 'semantic_kills': 2 * len(record['mutants']),
                            'fuzz_programs': record['fuzz']['programs'], 'fuzz_false_acceptances': record['fuzz']['false_acceptances'],
                            'fuzz_false_invalid': record['fuzz']['false_invalid'], 'fuzz_evaluator_values': record['fuzz']['evaluator_values']}
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print('Nest review passed: ' + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
