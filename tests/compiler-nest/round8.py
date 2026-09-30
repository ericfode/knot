#!/usr/bin/env python3
"""Round-8 regressions: a `+` binder's kind is judged where the frontier binds it."""
import datetime
import json
from pathlib import Path

import check as gate
import review
import typekind

HERE = Path(__file__).resolve().parent
BUILD = gate.ROOT / '.local/compiler-nest/round8'
RECEIPT = HERE / 'receipts/round8.json'
GENERATED = HERE / 'receipts/round8-typekind.json'
ACCEPTED = {'exit': 0}
KIND = {'exit': 2, 'diagnostic': 'Invalid\tcheck\treusable-type\t'}

# The first two restore the finding: the kind judged where `+` raises a binder
# (the alias) or a field (its binding). The last three drop one binding site:
# a leaf body, a split ahead of the binder, and a match with no rows.
KINDED = '''def kinded(result: Result<S.Error,E.Scope>, +level: U32, +types: List<&2,C.Datatype>) -> Result<S.Error,E.Scope>:
  match result:
    case Fail{error}: Fail{error}
    case Done{E.Scope{+bindings,next,open,live,smaller}}:
      S.bind(Unit,E.Scope,P.bound([level],bindings,types),u => Done{E.Scope{bindings,next,open,live,smaller}})

'''
FIELD = '''      binder(node,+token => +mark =>
        S.bind(Unit,Fields,G.binder(types,token,U32.is_eq(mark,2)),u =>
          add(scope,token,quantity(q,parent,mark),type_id,bound => binding => term =>
            S.bind(Fields,Fields,fields(tail,rest,parent,types,bound,origin),remaining => Done{prepend(binding,term,remaining)}))))'''
FIELD_KINDED = '''      binder(node,+token => +mark =>
        S.bind(Unit,Fields,G.binder(types,token,U32.is_eq(mark,2)),u =>
          S.bind(C.Datatype,Fields,G.type_at(types,type_id),definition =>
            S.bind(Unit,Fields,G.quantity(token,quantity(q,parent,mark),definition),u =>
              add(scope,token,quantity(q,parent,mark),type_id,bound => binding => term =>
                S.bind(Fields,Fields,fields(tail,rest,parent,types,bound,origin),remaining => Done{prepend(binding,term,remaining)}))))))'''
MUTANTS = [
    {'name': 'judge-kind-at-promotion', 'file': 'matrix.bend',
     'old': 'S.bind(E.Scope,Expansion,alias(scope,token,level,mark),bound =>',
     'new': 'S.bind(E.Scope,Expansion,kinded(alias(scope,token,level,mark),level,types),bound =>',
     'prefix': KINDED, 'witness': 'k1-param-promote-destructure', 'phase': 'check', 'wrong': KIND},
    {'name': 'judge-field-kind-at-binding', 'file': 'patterns.bend', 'old': FIELD, 'new': FIELD_KINDED,
     'witness': 'k6-field-promote-destructure', 'phase': 'check', 'wrong': KIND},
    {'name': 'skip-leaf-binding', 'file': 'patterns.bend',
     'old': 'S.bind(Unit,E.Scope,bound(open,bindings,types),u =>', 'new': 'S.bind(Unit,E.Scope,Done{Unit{}},u =>',
     'witness': 'c2-promote-no-match', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'skip-split-binding', 'file': 'patterns.bend',
     'old': 'S.bind(Unit,Fields,advance(scope,level,types),u =>', 'new': 'S.bind(Unit,Fields,Done{Unit{}},u =>',
     'witness': 'n6-promote-column-then-split', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'skip-empty-match-binding', 'file': 'check.bend',
     'old': 'S.bind(Unit,C.Checked,P.advance(scope,level,types),u =>', 'new': 'S.bind(Unit,C.Checked,Done{Unit{}},u =>',
     'witness': 'n5-promote-then-empty-match-later', 'phase': 'check', 'wrong': ACCEPTED},
]


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    gate.BUILD = review.BUILD = BUILD
    manifest = json.loads((HERE / 'round8-expectations.json').read_text())
    paths = [*sorted((gate.ROOT / 'src').glob('*.bend')), *sorted(HERE.glob('*.py')),
             HERE / 'round8-expectations.json', *sorted((HERE / 'round8-fixtures').glob('*.bend'))]
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
              'inputs': {str(p.relative_to(gate.ROOT)): gate.digest(p) for p in paths},
              'builds': [], 'fixtures': [], 'mutants': []}
    try:
        record['oracle'] = gate.successful(['python3', HERE / 'round8_seed.py'])
        record['proofs'] = {}
        for entry in ('matrix-PROOF.bend', 'lowering-PROOF.bend'):
            proof = gate.successful([*gate.SEED, gate.ROOT / 'src' / entry])
            gate.require(proof['stdout'].strip() == 'All terms check.', proof)
            record['proofs'][entry] = proof
        lanes = gate.build_lanes(record)
        review.fixtures(record, manifest, lanes)
        gate.MUTANTS = MUTANTS
        gate.mutants(record, manifest, {'fixtures': {}})
        generated = typekind.check(lanes['native']['check'], BUILD / 'typekind', lanes['native']['eval'])
        GENERATED.write_text(json.dumps(generated, indent=2) + '\n')
        record['typekind'] = generated
        gate.require(generated['programs'] == 3000 and generated['false_acceptances'] == 0
                     and generated['false_invalid'] == 0 and generated['evaluator_values'] > 0, generated)
        gate.require(all(gate.digest(gate.ROOT / p) == h for p, h in record['inputs'].items()), 'Round-8 inputs changed')
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
                            'generated_knot_outcomes': generated['knot_outcomes'],
                            'generated_promotes_type': generated['promotes_type'],
                            'generated_false_acceptances': generated['false_acceptances'],
                            'generated_false_invalid': generated['false_invalid'],
                            'generated_evaluator_values': generated['evaluator_values']}
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print('Nest round 8 passed: ' + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
