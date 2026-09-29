#!/usr/bin/env python3
"""Round-11 regressions: every row is audited, one binder name rule, a binder hides its datatype, and the layouts the parser does not model.

`round11.py` replays the 293 seed-frozen fixtures in both compiler lanes with the audit, name-rule and
shadowing mutants; `round11.py --sweep` runs the parser mutants and the 5,400-program differential generator.
"""
import datetime
import json
import sys
from pathlib import Path

import check as gate
import fuzz11
import review

HERE = Path(__file__).resolve().parent
SWEEP = '--sweep' in sys.argv[1:]
BUILD = gate.ROOT / ('.local/compiler-nest/round11-sweep' if SWEEP else '.local/compiler-nest/round11')
RECEIPT = HERE / ('receipts/round11-sweep.json' if SWEEP else 'receipts/round11.json')
ACCEPTED = {'exit': 0}


def invalid(phase, code):
    return {'exit': 2, 'diagnostic': f'Invalid\t{phase}\t{code}\t'}


def unsupported(code):
    return {'exit': 3, 'diagnostic': f'Unsupported\tparse\t{code}\t'}


AUDIT_BODY = 'S.bind(Unit,Unit,audit(n,body,width,types),u => audit(n,S.Sequence{tail},width,types))'
LET_PROMOTION = 'S.bind(Unit,Unit,G.promotion(types,token,U32.is_eq(q,2)),u => audit(n,body,width,types))'
HIDES = 'G.visible(types,name,E.names(bindings))'
TELESCOPE = 'hidden(List<&2,S.Token>,seen,type_name,u => telescope(tail,Con{name,seen}))'
# Each mutant is one replacement in a copy of `src/`, killed in both lanes on the named witness. The first
# group breaks the audit (a body, a let, a nested match, the rows after the first), the width and constructor
# arity checks of finding 6 (which no gate saw fail before), the pattern forms and the binder rule; the
# second the promoted-datatype rule at every site and its source order; the third the hidden type name at
# every site that writes a type, and the over-rejecting twins that hide a parameter's own type.
MATRIX = [
    {'name': 'audit-skips-bodies', 'file': 'matrix.bend', 'old': AUDIT_BODY, 'new': 'audit(n,S.Sequence{tail},width,types)',
     'witness': 'dead-single-unknown', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'audit-skips-nested-matches', 'file': 'matrix.bend',
     'old': 'audit(n,S.Sequence{arms},List.length(&2,S.Node,items(value)),types)', 'new': 'Done{Unit{}}',
     'witness': 'dead-multi-unknown', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'audit-skips-let-bodies', 'file': 'matrix.bend', 'old': LET_PROMOTION,
     'new': 'S.bind(Unit,Unit,G.promotion(types,token,U32.is_eq(q,2)),u => Done{Unit{}})',
     'witness': 'dead-let-unknown', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'audit-skips-let-promotion', 'file': 'matrix.bend', 'old': LET_PROMOTION, 'new': 'audit(n,body,width,types)',
     'witness': 'dead-let-plus-flag', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'audit-first-row-only', 'file': 'matrix.bend', 'old': AUDIT_BODY, 'new': 'audit(n,body,width,types)',
     'witness': 'dead-outer-bare', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'audit-drops-row-width', 'file': 'matrix.bend', 'old': 'Nat.is_eq(List.length(&2,S.Node,items(pattern)),width)',
     'new': 'True{}', 'witness': 'arity-short-live', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'audit-drops-dead-row-width', 'file': 'matrix.bend', 'old': 'Nat.is_eq(List.length(&2,S.Node,items(pattern)),width)',
     'new': 'True{}', 'witness': 'dead-wide-long', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'validate-drops-constructor-arity', 'file': 'matrix.bend',
     'old': 'Nat.is_eq(List.length(&2,S.Node,args),List.length(&2,C.Parameter,params))', 'new': 'True{}',
     'witness': 'arity-ctor-less-dead', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'validate-drops-nested-arity', 'file': 'matrix.bend',
     'old': 'Nat.is_eq(List.length(&2,S.Node,args),List.length(&2,C.Parameter,params))', 'new': 'True{}',
     'witness': 'arity-field-more-live', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'validate-accepts-calls', 'file': 'matrix.bend', 'old': 'case 1n+n S.Call{token,args}: C.invalid(Unit,"pattern-form",token)',
     'new': 'case 1n+n S.Call{token,args}: Done{Unit{}}', 'witness': 'dead-single-call', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'binder-accepts-constructors', 'file': 'catalog.bend',
     'old': 'S.choose(Result<S.Error,Unit>,constructor_before(types,token),u =>\n    C.invalid(Unit,"constructor-pattern-binder",token),u => promotion(types,token,promoted))',
     'new': 'promotion(types,token,promoted)', 'witness': 'dead-single-bare', 'phase': 'check', 'wrong': ACCEPTED},
    # finding 2
    {'name': 'promotion-ignores-datatypes', 'file': 'catalog.bend', 'old': 'Bool.and(promoted,prior_datatype(types,token))',
     'new': 'False{}', 'witness': 'plusd-row-flag', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'row-promotion-unmarked', 'file': 'matrix.bend', 'old': 'case 1n+n S.Promotion{token}: G.binder(types,token,True{})',
     'new': 'case 1n+n S.Promotion{token}: G.binder(types,token,False{})', 'witness': 'plusd-row2-first-flag', 'phase': 'check',
     'wrong': ACCEPTED},
    {'name': 'field-promotion-unmarked', 'file': 'patterns.bend', 'old': 'G.binder(types,token,U32.is_eq(mark,2))',
     'new': 'G.binder(types,token,False{})', 'witness': 'plusd-field-flag', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'let-promotion-unchecked', 'file': 'check.bend',
     'old': 'S.bind(Unit,C.Checked,G.promotion(types,token,U32.is_eq(q,2)),u =>', 'new': 'S.bind(Unit,C.Checked,Done{Unit{}},u =>',
     'witness': 'plusd-let-flag', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'datatype-order-ignored', 'file': 'catalog.bend',
     'old': 'Bool.and(String.eq(S.text(token),S.text(name)),U32.is_le(start(token),start(name))),prior_datatype(tail,name))',
     'new': 'Bool.and(String.eq(S.text(token),S.text(name)),True{}),prior_datatype(tail,name))',
     'witness': 'plusd-order-before', 'phase': 'check', 'wrong': invalid('check', 'datatype-pattern-binder')},
    {'name': 'bare-binder-promoted', 'file': 'matrix.bend', 'old': 'case 1n+n S.Variable{token}: G.binder(types,token,False{})',
     'new': 'case 1n+n S.Variable{token}: G.binder(types,token,True{})', 'witness': 'plusd-ctl-bare-datatype', 'phase': 'check',
     'wrong': invalid('check', 'datatype-pattern-binder')},
    # finding 3
    {'name': 'annotation-ignores-binders', 'file': 'check.bend', 'old': HIDES, 'new': 'G.find_type(types,name,0)',
     'witness': 'shadow-row', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'every-type-hidden', 'file': 'catalog.bend',
     'old': 'S.choose(Result<S.Error,A>,named(seen,name),u => C.invalid(A,"type-shadowed",name),next)',
     'new': 'S.choose(Result<S.Error,A>,True{},u => C.invalid(A,"type-shadowed",name),next)',
     'witness': 'shadow-ctl-plain-binder', 'phase': 'check', 'wrong': invalid('check', 'type-shadowed')},
    {'name': 'parameter-type-ignores-earlier', 'file': 'catalog.bend', 'old': TELESCOPE, 'new': 'telescope(tail,Con{name,seen})',
     'witness': 'shadow-param-type', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'parameter-type-hides-itself', 'file': 'catalog.bend', 'old': TELESCOPE,
     'new': TELESCOPE.replace('hidden(List<&2,S.Token>,seen,', 'hidden(List<&2,S.Token>,Con{name,seen},'),
     'witness': 'shadow-ctl-param-own-type', 'phase': 'check', 'wrong': invalid('check', 'type-shadowed')},
    {'name': 'result-type-ignores-parameters', 'file': 'catalog.bend', 'old': 'visible(types,result,names)', 'new': 'find_type(types,result,0)',
     'witness': 'shadow-param-result', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'field-type-ignores-earlier', 'file': 'catalog.bend', 'old': 'visible(types,type_name,seen)',
     'new': 'find_type(types,type_name,0)',
     'witness': 'shadow-field-type', 'phase': 'check', 'wrong': ACCEPTED},
]
# The parser: a numeral column, and each layout the seed reads that the parser answers Unsupported.
PARSE = [
    {'name': 'row-ignores-numerals', 'file': 'parse.bend', 'old': 'Bool.or(scrutinee(ts),Bool.or(numeral(ts),promotes(ts)))',
     'new': 'Bool.or(scrutinee(ts),promotes(ts))', 'witness': 'nat-wild-space-zero', 'phase': 'check',
     'wrong': invalid('parse', 'expected-:')},
    {'name': 'declaration-case-invalid', 'file': 'parse.bend', 'old': 'S.choose(Result<S.Error,Parsed>,S.matches(head,"case"),u =>',
     'new': 'S.choose(Result<S.Error,Parsed>,False{},u =>', 'witness': 'layout-case-at-match-multi', 'phase': 'check',
     'wrong': invalid('parse', 'top-level-indentation')},
    {'name': 'declaration-indent-invalid', 'file': 'parse.bend', 'old': 'Bool.or(S.matches(head,"def"),S.matches(head,"type"))',
     'new': 'False{}', 'witness': 'layout-def-indent-2', 'phase': 'check', 'wrong': invalid('parse', 'top-level-indentation')},
    {'name': 'body-end-declaration-invalid', 'file': 'parse.bend', 'old': 'Bool.or(S.matches(h,"def"),S.matches(h,"type"))',
     'new': 'False{}', 'witness': 'layout-def-glued-arm', 'phase': 'check', 'wrong': invalid('parse', 'end-of-body')},
    {'name': 'later-statement-invalid', 'file': 'parse.bend', 'old': 'S.choose(Result<S.Error,Parsed>,S.statement(h),u =>',
     'new': 'S.choose(Result<S.Error,Parsed>,False{},u =>', 'witness': 'layout-later-deeper-single', 'phase': 'check',
     'wrong': invalid('parse', 'body-indentation')},
    {'name': 'marked-body-invalid', 'file': 'parse.bend', 'old': 'Bool.and(U32.is_gt(parent,0),S.statement(h))',
     'new': 'Bool.and(U32.is_gt(parent,0),S.identifier(h))', 'witness': 'layout-plus-body-single', 'phase': 'check',
     'wrong': invalid('parse', 'body-indentation')},
    {'name': 'every-token-a-statement', 'file': 'syntax.bend',
     'old': 'Bool.or(identifier(t),Bool.or(matches(t,"match"),Bool.or(matches(t,"+"),matches(t,"-"))))', 'new': 'True{}',
     'witness': 'layout-ctl-case-after-let', 'phase': 'check', 'wrong': unsupported('same-line-statement')},
    {'name': 'colon-split-invalid', 'file': 'parse.bend', 'old': 'starts(S.skip_lines(ts),":")', 'new': 'False{}',
     'witness': 'layout-split-colon-plus-single', 'phase': 'check', 'wrong': invalid('parse', 'expected-=')},
    {'name': 'plain-split-invalid', 'file': 'parse.bend', 'old': 'Bool.and(S.identifier(h),split(Con{second,tail}))',
     'new': 'False{}', 'witness': 'layout-plain-split-colon-margin-single', 'phase': 'check',
     'wrong': invalid('parse', 'top-level-indentation')},
    {'name': 'same-line-statement-invalid', 'file': 'parse.bend',
     'old': 'S.choose(Result<S.Error,List<&2,S.Token>>,S.statement(h),u =>', 'new': 'S.choose(Result<S.Error,List<&2,S.Token>>,False{},u =>',
     'witness': 'layout-same-line-glued-single', 'phase': 'check', 'wrong': {'exit': 2, 'diagnostic': 'Invalid\tparse\texpected-\n'}},
]
MUTANTS = PARSE if SWEEP else MATRIX


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    gate.BUILD = review.BUILD = BUILD
    manifest = json.loads((HERE / 'round11-expectations.json').read_text())
    paths = [*sorted((gate.ROOT / 'src').glob('*.bend')), *sorted(HERE.glob('*.py')),
             HERE / 'round11-expectations.json', *sorted((HERE / 'round11-fixtures').glob('*.bend'))]
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
              'inputs': {str(p.relative_to(gate.ROOT)): gate.digest(p) for p in paths},
              'builds': [], 'fixtures': [], 'mutants': []}
    try:
        record['oracle'] = gate.successful(['python3', HERE / 'round11_seed.py'])
        record['proofs'] = {}
        for entry in sorted((gate.ROOT / 'src').glob('*PROOF.bend')):
            proof = gate.successful([*gate.SEED, entry])
            gate.require(proof['stdout'].strip() == 'All terms check.', proof)
            record['proofs'][entry.name] = proof
        lanes = gate.build_lanes(record)
        cases = manifest['fixtures']
        if not SWEEP:
            review.fixtures(record, manifest, lanes)
        gate.MUTANTS = MUTANTS
        gate.mutants(record, manifest, {'fixtures': {}})
        if SWEEP:
            record['sweep'] = fuzz11.check(lanes, BUILD / 'sweep')
            gate.require(record['sweep']['programs'] == fuzz11.COUNT, 'fixed sweep coverage')
            for family, cell in record['sweep']['families'].items():
                # each family needs programs both sides accept and both sides reject
                gate.require(cell.get('seed-Accepted', 0) >= 50 and cell.get('seed-Invalid', 0) >= 50, (family, cell))
        gate.require(all(gate.digest(gate.ROOT / p) == h for p, h in record['inputs'].items()), 'Round-11 inputs changed')
        accepted = sum(c['knot']['exit'] == 0 for c in cases)
        calls = sum(len(c['calls']) for c in cases if c['knot']['exit'] == 0)
        counts = {'mutants': len(record['mutants']), 'semantic_kills': 2 * len(record['mutants'])}
        if SWEEP:
            sweep = record['sweep']
            counts.update({'programs': sweep['programs'], 'seed_outcomes': sweep['seed_outcomes'],
                           'knot_outcomes': sweep['knot_outcomes'], 'false_acceptances': sweep['false_acceptances'],
                           'false_invalid': sweep['false_invalid'], 'evaluator_values': sweep['evaluator_values']})
        else:
            counts.update({'seed_fixtures': len(cases), 'seed_calls': sum(len(c['calls']) for c in cases),
                           'accepted_books': accepted, 'check_observations': 2 * len(cases),
                           'evaluator_values': 2 * calls, 'wasm_values': 2 * calls,
                           'rejected_phase_observations': 8 * (len(cases) - accepted),
                           'findings': {f: sum(c['finding'] == f for c in cases) for f in sorted({c['finding'] for c in cases})}})
        record['counts'] = counts
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print(('Nest round 11 sweep passed: ' if SWEEP else 'Nest round 11 passed: ') + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
