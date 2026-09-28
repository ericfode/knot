#!/usr/bin/env python3
"""Round-6 regressions: a constructor's brace must touch its name."""
import datetime
import json
from pathlib import Path

import check as gate
import review

HERE = Path(__file__).resolve().parent
BUILD = gate.ROOT / '.local/compiler-nest/round6'
RECEIPT = HERE / 'receipts/round6.json'
ACCEPTED = {'exit': 0}

# The first restores the finding; the others move the rule to lines, shift the
# offset, confine it to patterns or extend it to a call's parenthesis.
MUTANTS = [
    {'name': 'ignore-detached-brace', 'file': 'parse.bend',
     'old': 'S.touches(name,open),u =>', 'new': 'True{},u =>',
     'witness': 'w2-flat-newline', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'touch-by-line', 'file': 'syntax.bend',
     'old': 'U32.is_eq(b,c)', 'new': 'U32.is_eq(i,k)',
     'witness': 'w1-flat-space', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'touch-past-one', 'file': 'syntax.bend',
     'old': 'U32.is_eq(b,c)', 'new': 'U32.is_eq(U32.add(b,1),c)',
     'witness': 'touch-pattern-inner-space', 'phase': 'check',
     'wrong': {'exit': 2, 'diagnostic': 'Invalid\tparse\tdetached-brace\t'}},
    {'name': 'touch-patterns-only', 'file': 'parse.bend',
     'old': 'S.touches(name,open),u =>', 'new': 'Bool.or(Bool.not(pattern),S.touches(name,open)),u =>',
     'witness': 'w5-body-space', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'touch-call-parenthesis', 'file': 'parse.bend',
     'old': 'S.matches(open,"("),u =>', 'new': 'Bool.and(S.matches(open,"("),S.touches(name,open)),u =>',
     'witness': 'v1-call-space', 'phase': 'check',
     'wrong': {'exit': 2, 'diagnostic': 'Invalid\tparse\tend-of-body\t'}},
]


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    gate.BUILD = review.BUILD = BUILD
    manifest = json.loads((HERE / 'round6-expectations.json').read_text())
    paths = [*sorted((gate.ROOT / 'src').glob('*.bend')), *sorted(HERE.glob('*.py')),
             HERE / 'round6-expectations.json', *sorted((HERE / 'round6-fixtures').glob('*.bend'))]
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
              'inputs': {str(p.relative_to(gate.ROOT)): gate.digest(p) for p in paths},
              'builds': [], 'fixtures': [], 'mutants': []}
    try:
        record['oracle'] = gate.successful(['python3', HERE / 'round6_seed.py'])
        record['proofs'] = {}
        for entry in ('PROOF.bend', 'matrix-PROOF.bend'):
            proof = gate.successful([*gate.SEED, gate.ROOT / 'src' / entry])
            gate.require(proof['stdout'].strip() == 'All terms check.', proof)
            record['proofs'][entry] = proof
        lanes = gate.build_lanes(record)
        review.fixtures(record, manifest, lanes)
        gate.MUTANTS = MUTANTS
        gate.mutants(record, manifest, {'fixtures': {}})
        gate.require(all(gate.digest(gate.ROOT / p) == h for p, h in record['inputs'].items()), 'Round-6 inputs changed')
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
    print('Nest round 6 passed: ' + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
