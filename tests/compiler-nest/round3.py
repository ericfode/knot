#!/usr/bin/env python3
"""Round-3 regressions: binder grammar, dead contexts and line-broken headers."""
import datetime
import json
from pathlib import Path

import check as gate
import review

HERE = Path(__file__).resolve().parent
BUILD = gate.ROOT / '.local/compiler-nest/round3'
RECEIPT = HERE / 'receipts/round3.json'

MUTANTS = [
    {'name': 'dotted-pattern-binder', 'file': 'parse.bend',
     'old': 'Bool.or(Bool.not(pattern),S.binder(name))', 'new': 'Bool.or(Bool.not(pattern),S.identifier(name))',
     'witness': 'dot-multi-column', 'phase': 'check', 'wrong': {'exit': 0}},
    {'name': 'dotted-live-let', 'file': 'parse.bend',
     'old': 'Bool.or(U32.is_eq(quantity,0),S.binder(name))', 'new': 'Bool.or(U32.is_eq(quantity,0),S.identifier(name))',
     'witness': 'dot-let', 'phase': 'check', 'wrong': {'exit': 0}},
    {'name': 'erased-let-as-pattern', 'file': 'parse.bend',
     'old': 'Bool.or(U32.is_eq(quantity,0),S.binder(name))', 'new': 'Bool.or(False{},S.binder(name))',
     'witness': 'dot-erased-let', 'phase': 'check', 'wrong': {'exit': 2, 'diagnostic': 'Invalid\tparse\tbinding-name\t'}},
    {'name': 'accept-malformed-name', 'file': 'lex.bend',
     'old': 'S.malformed(text),u => Fail', 'new': 'False{},u => Fail',
     'witness': 'name-double-dot', 'phase': 'check', 'wrong': {'exit': 0}},
    {'name': 'unordered-empty-context', 'file': 'scope.bend',
     'old': 'witnessed(bindings,types,Con{level,after(open,level)})', 'new': 'witnessed(bindings,types,Nil{})',
     'witness': 'empty-after-multi', 'phase': 'check', 'wrong': {'exit': 0}},
    {'name': 'fields-after-parameters', 'file': 'patterns.bend',
     'old': 'List.append(&2,U32,E.levels(introduced),open)', 'new': 'List.append(&2,U32,open,E.levels(introduced))',
     'witness': 'empty-param-after-field', 'phase': 'check', 'wrong': {'exit': 0}},
    {'name': 'ignore-empty-datatype', 'file': 'scope.bend',
     'old': 'case _: uninhabited(types,type_id)', 'new': 'case _: False{}',
     'witness': 'empty-multi', 'phase': 'check', 'wrong': {'exit': 2, 'diagnostic': 'Invalid\tcheck\tmissing-arm\t'}},
    {'name': 'erased-empty-witness', 'file': 'scope.bend',
     'old': 'Bool.and(U32.is_ne(q,0),empty(known,types,type_id))', 'new': 'empty(known,types,type_id)',
     'witness': 'empty-erased-control', 'phase': 'check', 'wrong': {'exit': 0}},
    {'name': 'case-header-layout', 'file': 'parse.bend',
     'old': 'run(n,Term{True{}},header(tail))', 'new': 'run(n,Term{True{}},tail)',
     'witness': 'line-case', 'phase': 'check', 'wrong': {'exit': 2, 'diagnostic': 'Invalid\tparse\texpected-term\t'}},
    {'name': 'match-header-layout', 'file': 'parse.bend',
     'old': 'header(Con{second,tail})', 'new': 'Con{second,tail}',
     'witness': 'line-match', 'phase': 'check', 'wrong': {'exit': 2, 'diagnostic': 'Invalid\tparse\texpected-term\t'}},
    {'name': 'header-past-colon', 'file': 'parse.bend',
     'old': 'S.matches(h,":"),u => Con{h,t}', 'new': 'False{},u => Con{h,t}',
     'witness': 'line-row', 'phase': 'check', 'wrong': {'exit': 2, 'diagnostic': 'Invalid\tparse\tend-of-body\t'}},
]


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    gate.BUILD = review.BUILD = BUILD
    manifest = json.loads((HERE / 'round3-expectations.json').read_text())
    paths = [*sorted((gate.ROOT / 'src').glob('*.bend')), *sorted(HERE.glob('*.py')),
             HERE / 'round3-expectations.json', *sorted((HERE / 'round3-fixtures').glob('*.bend'))]
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
              'inputs': {str(p.relative_to(gate.ROOT)): gate.digest(p) for p in paths},
              'builds': [], 'fixtures': [], 'mutants': []}
    try:
        record['oracle'] = gate.successful(['python3', HERE / 'round3_seed.py'])
        record['proof'] = gate.successful([*gate.SEED, gate.ROOT / 'src/matrix-PROOF.bend'])
        gate.require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
        lanes = gate.build_lanes(record)
        review.fixtures(record, manifest, lanes)
        gate.MUTANTS = MUTANTS
        gate.mutants(record, manifest, {'fixtures': {}})
        gate.require(all(gate.digest(gate.ROOT / p) == h for p, h in record['inputs'].items()), 'Round-3 inputs changed')
        cases = manifest['fixtures']
        accepted = sum(c['knot']['exit'] == 0 for c in cases)
        calls = sum(len(c['calls']) for c in cases if c['knot']['exit'] == 0)
        record['counts'] = {'seed_fixtures': len(cases), 'seed_calls': sum(len(c['calls']) for c in cases),
                            'accepted_books': accepted, 'check_observations': 2 * len(cases),
                            'evaluator_values': 2 * calls, 'wasm_values': 2 * calls,
                            'rejected_phase_observations': 8 * (len(cases) - accepted),
                            'findings': {f: sum(c['finding'] == f for c in cases) for f in sorted({c['finding'] for c in cases})},
                            'mutants': len(record['mutants']), 'semantic_kills': 2 * len(record['mutants'])}
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print('Nest round 3 passed: ' + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
