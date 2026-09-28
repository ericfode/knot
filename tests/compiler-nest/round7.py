#!/usr/bin/env python3
"""Round-7 regressions: a `+` row never raises a let binder's quantity."""
import datetime
import json
from pathlib import Path

import check as gate
import letalias
import review

HERE = Path(__file__).resolve().parent
BUILD = gate.ROOT / '.local/compiler-nest/round7'
RECEIPT = HERE / 'receipts/round7.json'
GENERATED = HERE / 'receipts/round7-letalias.json'
ACCEPTED = {'exit': 0}

# The first restores the finding at the quantity site. The second promotes
# every variable column at the promote site: the quantity site keeps every let
# affine under it, but it raises an affine parameter without a `+` row. The
# third over-corrects, withholding a `+` row's mark from parameters too.
MUTANTS = [
    {'name': 'promote-let-alias', 'file': 'matrix.bend',
     'old': 'u => row,u => 1)', 'new': 'u => row,u => row)',
     'witness': 'l7-var-match-latest-promote-row', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'promote-every-variable-column', 'file': 'matrix.bend',
     'old': 'promote(name,level,mark(rows),S.Matrix', 'new': 'promote(name,level,2,S.Matrix',
     'witness': 'p1-param-alias-reuse', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'never-promote', 'file': 'matrix.bend',
     'old': 'u => row,u => 1)', 'new': 'u => 1,u => 1)',
     'witness': 'z1-param-promote-alias-and-param', 'phase': 'check',
     'wrong': {'exit': 2, 'diagnostic': 'Invalid\tcheck\taffine-reuse\t'}},
]


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    gate.BUILD = review.BUILD = BUILD
    manifest = json.loads((HERE / 'round7-expectations.json').read_text())
    paths = [*sorted((gate.ROOT / 'src').glob('*.bend')), *sorted(HERE.glob('*.py')),
             HERE / 'round7-expectations.json', *sorted((HERE / 'round7-fixtures').glob('*.bend'))]
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
              'inputs': {str(p.relative_to(gate.ROOT)): gate.digest(p) for p in paths},
              'builds': [], 'fixtures': [], 'mutants': []}
    try:
        record['oracle'] = gate.successful(['python3', HERE / 'round7_seed.py'])
        proof = gate.successful([*gate.SEED, gate.ROOT / 'src/matrix-PROOF.bend'])
        gate.require(proof['stdout'].strip() == 'All terms check.', proof)
        record['proofs'] = {'matrix-PROOF.bend': proof}
        lanes = gate.build_lanes(record)
        review.fixtures(record, manifest, lanes)
        gate.MUTANTS = MUTANTS
        gate.mutants(record, manifest, {'fixtures': {}})
        generated = letalias.check(lanes['native']['check'], BUILD / 'letalias', lanes['native']['eval'])
        GENERATED.write_text(json.dumps(generated, indent=2) + '\n')
        record['letalias'] = generated
        gate.require(generated['programs'] == 1500 and generated['false_acceptances'] == 0
                     and generated['false_invalid'] == 0 and generated['evaluator_values'] > 0, generated)
        gate.require(all(gate.digest(gate.ROOT / p) == h for p, h in record['inputs'].items()), 'Round-7 inputs changed')
        cases = manifest['fixtures']
        accepted = sum(c['knot']['exit'] == 0 for c in cases)
        calls = sum(len(c['calls']) for c in cases if c['knot']['exit'] == 0)
        record['counts'] = {'seed_fixtures': len(cases), 'seed_calls': sum(len(c['calls']) for c in cases),
                            'accepted_books': accepted, 'check_observations': 2 * len(cases),
                            'evaluator_values': 2 * calls, 'wasm_values': 2 * calls,
                            'rejected_phase_observations': 8 * (len(cases) - accepted),
                            'findings': {f: sum(c['finding'] == f for c in cases) for f in sorted({c['finding'] for c in cases})},
                            'mutants': len(record['mutants']), 'semantic_kills': 2 * len(record['mutants']),
                            'generated_programs': generated['programs'], 'generated_seed_outcomes': generated['seed_outcomes'],
                            'generated_false_acceptances': generated['false_acceptances'],
                            'generated_false_invalid': generated['false_invalid'],
                            'generated_evaluator_values': generated['evaluator_values']}
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print('Nest round 7 passed: ' + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
