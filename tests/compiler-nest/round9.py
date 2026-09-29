#!/usr/bin/env python3
"""Round-9 regressions: a let of a refined binder needs an annotation; a dotted binder, a line break in arguments and a same-line arm are unsupported."""
import datetime
import json
from pathlib import Path

import check as gate
import review

HERE = Path(__file__).resolve().parent
BUILD = gate.ROOT / '.local/compiler-nest/round9'
RECEIPT = HERE / 'receipts/round9.json'
ACCEPTED = {'exit': 0}
INFER = {'exit': 2, 'diagnostic': 'Invalid\tcheck\tannotation-required\t'}


def invalid(code):
    return {'exit': 2, 'diagnostic': f'Invalid\tparse\t{code}\t'}


# The rule lives in two rows of `expected`: an unannotated let rejects a checked
# Value (a binder refined to a nullary constructor) and a checked Construct.
VALUE = '''    case None{} C.Checked{C.Value{origin,typ,tag},ignored,uses}: C.invalid(C.Checked,"annotation-required",token)
'''
CONSTRUCT = '''    case None{} C.Checked{C.Construct{origin,typ,tag,params,args},ignored,uses}: C.invalid(C.Checked,"annotation-required",token)
'''
# The first three ignore the refinement, wholly or by constructor form. The next
# three over-reject: an annotated let, a residual binder and a field never split.
# The next three report a dotted binder as Invalid at one binder site each; the
# last three report a line break in arguments, or a same-line arm, as Invalid again.
MUTANTS = [
    {'name': 'ignore-refinement', 'file': 'check.bend', 'old': VALUE + CONSTRUCT, 'new': '',
     'witness': 'letm-multi', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'ignore-refined-value', 'file': 'check.bend', 'old': VALUE, 'new': '',
     'witness': 'letm-flat', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'ignore-refined-constructor', 'file': 'check.bend', 'old': CONSTRUCT, 'new': '',
     'witness': 'letm-flatfield', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'infer-annotated-let', 'file': 'check.bend',
     'old': '    case None{} C.Checked{C.Value{origin,typ,tag},ignored,uses}: C.invalid(',
     'new': '    case _ C.Checked{C.Value{origin,typ,tag},ignored,uses}: C.invalid(',
     'witness': 'letx-flat-param-annot', 'phase': 'check', 'wrong': INFER},
    {'name': 'refine-residual-binder', 'file': 'scope.bend',
     'old': 'u => C.Reference{token,level,type_id})),', 'new': 'u => C.Value{token,type_id,0})),',
     'witness': 'letm-wildrow', 'phase': 'check', 'wrong': INFER},
    {'name': 'refine-unsplit-field', 'file': 'patterns.bend',
     'old': '+binding : C.Binding = C.Binding{token,level,q,type_id,True{},None{}}',
     'new': '+binding : C.Binding = C.Binding{token,level,q,type_id,True{},Some{C.Value{token,type_id,0}}}',
     'witness': 'twin-field-unsplit', 'phase': 'check', 'wrong': INFER},
    {'name': 'rebound-pattern-invalid', 'file': 'parse.bend',
     'old': 'u => binder_failure(tokens,name,"pattern-binder",True{})))),u =>',
     'new': 'u => invalid(tokens,"pattern-binder")))),u =>',
     'witness': 'rebound-field', 'phase': 'check', 'wrong': invalid('pattern-binder')},
    {'name': 'rebound-promotion-invalid', 'file': 'parse.bend',
     'old': 'u => binder_failure(tokens,open,"pattern-binder",True{})),u =>',
     'new': 'u => invalid(tokens,"pattern-binder")),u =>',
     'witness': 'rebound-promotion', 'phase': 'check', 'wrong': invalid('pattern-binder')},
    {'name': 'rebound-let-invalid', 'file': 'parse.bend',
     'old': '            binder_failure(tokens,name,"binding-name",U32.is_ne(quantity,0)))',
     'new': '            invalid(tokens,"binding-name"))',
     'witness': 'rebound-let', 'phase': 'check', 'wrong': invalid('binding-name')},
    {'name': 'list-break-invalid-in-arguments', 'file': 'parse.bend',
     'old': 'u => unsupported(tokens,"line-break"),u =>\n            then(run(n,Term{pattern},tokens)',
     'new': 'u => invalid(tokens,"expected-term"),u =>\n            then(run(n,Term{pattern},tokens)',
     'witness': 'hd-b2-body-open-brace-newline', 'phase': 'check', 'wrong': invalid('expected-term')},
    {'name': 'list-break-invalid-after-element', 'file': 'parse.bend',
     'old': 'u => unsupported(tokens,"line-break"),u =>\n              invalid(tokens,"argument-separator")',
     'new': 'u => invalid(tokens,"argument-separator"),u =>\n              invalid(tokens,"argument-separator")',
     'witness': 'hd-b5-call-args-newline', 'phase': 'check', 'wrong': invalid('argument-separator')},
    {'name': 'same-line-arm-invalid', 'file': 'parse.bend',
     'old': 'u => unsupported(ts,"same-line-arm"),u =>', 'new': 'u => invalid(ts,"end-of-body"),u =>',
     'witness': 'hd-h25-two-cases-one-line', 'phase': 'check', 'wrong': invalid('end-of-body')},
]


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    gate.BUILD = review.BUILD = BUILD
    manifest = json.loads((HERE / 'round9-expectations.json').read_text())
    paths = [*sorted((gate.ROOT / 'src').glob('*.bend')), *sorted(HERE.glob('*.py')),
             HERE / 'round9-expectations.json', *sorted((HERE / 'round9-fixtures').glob('*.bend'))]
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
              'inputs': {str(p.relative_to(gate.ROOT)): gate.digest(p) for p in paths},
              'builds': [], 'fixtures': [], 'mutants': []}
    try:
        record['oracle'] = gate.successful(['python3', HERE / 'round9_seed.py'])
        record['proofs'] = {}
        for entry in ('matrix-PROOF.bend', 'lowering-PROOF.bend'):
            proof = gate.successful([*gate.SEED, gate.ROOT / 'src' / entry])
            gate.require(proof['stdout'].strip() == 'All terms check.', proof)
            record['proofs'][entry] = proof
        lanes = gate.build_lanes(record)
        review.fixtures(record, manifest, lanes)
        gate.MUTANTS = MUTANTS
        gate.mutants(record, manifest, {'fixtures': {}})
        gate.require(all(gate.digest(gate.ROOT / p) == h for p, h in record['inputs'].items()), 'Round-9 inputs changed')
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
    print('Nest round 9 passed: ' + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
