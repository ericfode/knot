#!/usr/bin/env python3
"""Round-4 regressions: recursion through a rebuilt strict descendant."""
import datetime
import json
from pathlib import Path

import check as gate
import review

HERE = Path(__file__).resolve().parent
BUILD = gate.ROOT / '.local/compiler-nest/round4'
RECEIPT = HERE / 'receipts/round4.json'
UNSUPPORTED = {'exit': 3, 'diagnostic': 'Unsupported\tcheck\trecursive-call\t'}

# Disabling the recognizer restores the reconstruction-only rule of the
# finding; the other three each drop one condition of the recognizer.
MUTANTS = [
    {'name': 'ignore-rebuilt-descent', 'file': 'check.bend',
     'old': 'Bool.not(E.rebuilt(items,bindings,smaller))', 'new': 'True{}',
     'witness': 'rebuilt-field-default', 'phase': 'check', 'wrong': UNSUPPORTED},
    {'name': 'any-rebuilt-level', 'file': 'scope.bend',
     'old': 'Bool.and(contains(smaller,level),denotes(', 'new': 'Bool.and(True{},denotes(',
     'witness': 'rebuilt-root', 'phase': 'check', 'wrong': {'exit': 0}},
    {'name': 'untyped-rebuilt-constant', 'file': 'scope.bend',
     'old': 'Bool.and(Bool.and(U32.is_eq(type_id,typ),U32.is_eq(tag,t)),denotes(tail,rest,bindings))',
     'new': 'Bool.and(U32.is_eq(tag,t),denotes(tail,rest,bindings))',
     'witness': 'rebuilt-retyped-constant', 'phase': 'check', 'wrong': {'exit': 0}},
    {'name': 'ignore-rebuilt-fields', 'file': 'scope.bend',
     'old': 'denotes(args,unfolded(refs,bindings),bindings)', 'new': 'True{}',
     'witness': 'rebuilt-swapped-fields', 'phase': 'check', 'wrong': {'exit': 0}},
]


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    gate.BUILD = review.BUILD = BUILD
    manifest = json.loads((HERE / 'round4-expectations.json').read_text())
    paths = [*sorted((gate.ROOT / 'src').glob('*.bend')), *sorted(HERE.glob('*.py')),
             HERE / 'round4-expectations.json', *sorted((HERE / 'round4-fixtures').glob('*.bend'))]
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
              'inputs': {str(p.relative_to(gate.ROOT)): gate.digest(p) for p in paths},
              'builds': [], 'fixtures': [], 'mutants': []}
    try:
        record['oracle'] = gate.successful(['python3', HERE / 'round4_seed.py'])
        record['proofs'] = {}
        for entry in ('matrix-PROOF.bend', 'recursion-PROOF.bend'):
            proof = gate.successful([*gate.SEED, gate.ROOT / 'src' / entry])
            gate.require(proof['stdout'].strip() == 'All terms check.', proof)
            record['proofs'][entry] = proof
        lanes = gate.build_lanes(record)
        review.fixtures(record, manifest, lanes)
        gate.MUTANTS = MUTANTS
        gate.mutants(record, manifest, {'fixtures': {}})
        gate.require(all(gate.digest(gate.ROOT / p) == h for p, h in record['inputs'].items()), 'Round-4 inputs changed')
        cases = manifest['fixtures']
        accepted = sum(c['knot']['exit'] == 0 for c in cases)
        calls = sum(len(c['calls']) for c in cases if c['knot']['exit'] == 0)
        record['counts'] = {'seed_fixtures': len(cases), 'seed_calls': sum(len(c['calls']) for c in cases),
                            'accepted_books': accepted, 'check_observations': 2 * len(cases),
                            'evaluator_values': 2 * calls, 'wasm_values': 2 * calls,
                            'rejected_phase_observations': 8 * (len(cases) - accepted),
                            'mutants': len(record['mutants']), 'semantic_kills': 2 * len(record['mutants'])}
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print('Nest round 4 passed: ' + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
