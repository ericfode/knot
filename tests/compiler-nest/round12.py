#!/usr/bin/env python3
"""Round-12 regressions: the first row of a split marks its fields, term suffixes are unsupported, and gates share no half-written file.

`round12.py` replays the 161 seed-frozen fixtures in both compiler lanes, kills the first-row-marks and
term-suffix mutants, checks that a published wrapper is never seen half written, and runs the 3,000-program
differential generator of `fuzz12.py`.
"""
import datetime
import json
import os
from pathlib import Path
import tempfile

import check as gate
import fuzz12
import regen
import review

HERE = Path(__file__).resolve().parent
BUILD = gate.ROOT / '.local/compiler-nest/round12'
RECEIPT = HERE / 'receipts/round12.json'
ACCEPTED = {'exit': 0}


def invalid(phase, code):
    return {'exit': 2, 'diagnostic': f'Invalid\t{phase}\t{code}\t'}


def unsupported(code):
    return {'exit': 3, 'diagnostic': f'Unsupported\tparse\t{code}\t'}


LEADING = 'case Con{S.Arm{arm,S.Sequence{Con{S.Constructor{token,args},rest}},body},tail}: args'
MARKED = 'case Con{S.Variable{name},rest} Con{S.Promotion{binder},more}: Con{S.Promotion{name},marked(rest,more)}'
REPLY = 'S.choose(Result<S.Error,Parsed>,suffix(ts),u => unsupported(ts,"term-form"),u => terminated(value,ts))'
LINE_END = 'S.choose(Result<S.Error,List<&2,S.Token>>,suffix(ts),u =>'
BINDING = 'Bool.or(continues(tokens),Bool.and(U32.is_eq(quantity,2),starts(S.skip_lines(tokens),"(")))'
BINDING_BREAK = 'Bool.and(U32.is_eq(quantity,2),Bool.and(starts(tokens,"\\n"),starts(S.skip_lines(tokens),"+")))'
VALUE_BREAK = 'Bool.and(starts(rhs,"\\n"),Bool.and(Bool.not(scrutinee(S.skip_lines(rhs))),term_start(S.skip_lines(rhs))))'
ARGUMENT = 'Bool.and(Bool.not(Bool.or(parameters,pattern)),Bool.or(suffix(tokens),lambda(head,tokens)))'
# Each mutant is one replacement in a copy of `src/`, killed in both lanes on the named witness. The matrix
# mutants drop the first row's marks, take them from another row or promote too many fields; the parser
# mutants read each term suffix as invalid again, one site at a time, and widen each rule to what the seed rejects.
MUTANTS = [
    {'name': 'split-ignores-first-row-marks', 'file': 'matrix.bend', 'old': 'S.Constructor{ctor,marked(fields,leading(rows))}',
     'new': 'S.Constructor{ctor,fields}', 'witness': 'plusfirst-pair', 'phase': 'check', 'wrong': invalid('check', 'affine-reuse')},
    {'name': 'leading-takes-second-row', 'file': 'matrix.bend', 'old': LEADING,
     'new': LEADING.replace(': args', ': leading(tail)'), 'witness': 'plusfirst-pair', 'phase': 'check',
     'wrong': invalid('check', 'affine-reuse')},
    {'name': 'leading-takes-last-row', 'file': 'matrix.bend', 'old': LEADING,
     'new': LEADING.replace(',tail}: args', ',+tail}: S.choose(List<&2,S.Node>,List.is_empty(&2,S.Node,leading(tail)),u => args,u => leading(tail))'),
     'witness': 'plusfirst-pair', 'phase': 'check', 'wrong': invalid('check', 'affine-reuse')},
    {'name': 'marked-promotes-every-field', 'file': 'matrix.bend', 'old': MARKED,
     'new': MARKED.replace('Con{S.Promotion{binder},more}', 'Con{binder,more}'), 'witness': 'plusfirst-ctl-no-plus',
     'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'marked-ignores-later-fields', 'file': 'matrix.bend', 'old': MARKED,
     'new': MARKED.replace('Con{S.Promotion{name},marked(rest,more)}', 'Con{S.Promotion{name},rest}'),
     'witness': 'plusfirst-trip-two-marks', 'phase': 'check', 'wrong': invalid('check', 'affine-reuse')},
    {'name': 'body-suffix-invalid', 'file': 'parse.bend', 'old': REPLY, 'new': 'terminated(value,ts)',
     'witness': 'suffix-or-dead', 'phase': 'check', 'wrong': invalid('parse', 'end-of-body')},
    {'name': 'let-suffix-invalid', 'file': 'parse.bend', 'old': LINE_END,
     'new': LINE_END.replace('suffix(ts)', 'False{}'), 'witness': 'suffix-or-dead-let', 'phase': 'check',
     'wrong': {'exit': 2, 'diagnostic': 'Invalid\tparse\texpected-\n'}},
    {'name': 'argument-suffix-invalid', 'file': 'parse.bend', 'old': ARGUMENT,
     'new': ARGUMENT.replace('Bool.or(suffix(tokens),lambda(head,tokens))', 'lambda(head,tokens)'),
     'witness': 'suffix-or-dead-arg', 'phase': 'check', 'wrong': invalid('parse', 'argument-separator')},
    {'name': 'argument-lambda-invalid', 'file': 'parse.bend', 'old': ARGUMENT,
     'new': ARGUMENT.replace('Bool.or(suffix(tokens),lambda(head,tokens))', 'suffix(tokens)'),
     'witness': 'suffix-lam-dead-arg', 'phase': 'check', 'wrong': invalid('parse', 'argument-separator')},
    {'name': 'let-lambda-invalid', 'file': 'parse.bend', 'old': 'S.choose(Result<S.Error,Parsed>,lambda(value,tokens),u => unsupported(tokens,"term-form"),u =>',
     'new': 'S.choose(Result<S.Error,Parsed>,False{},u => unsupported(tokens,"term-form"),u =>',
     'witness': 'suffix-lam-dead-let', 'phase': 'check', 'wrong': {'exit': 2, 'diagnostic': 'Invalid\tparse\texpected-\n'}},
    {'name': 'promoted-term-invalid', 'file': 'parse.bend', 'old': 'S.choose(Result<S.Error,Parsed>,promoted_term(quantity,Con{separator,tail}),u =>',
     'new': 'S.choose(Result<S.Error,Parsed>,False{},u =>', 'witness': 'suffix-plus0-dead', 'phase': 'check',
     'wrong': invalid('parse', 'expected-=')},
    {'name': 'erased-term-unsupported', 'file': 'parse.bend', 'old': 'Bool.and(U32.is_eq(quantity,2),Bool.or(Bool.and(',
     'new': 'Bool.and(U32.is_ne(quantity,1),Bool.or(Bool.and(', 'witness': 'suffix-ctl-minus0', 'phase': 'check',
     'wrong': unsupported('term-form')},
    {'name': 'every-token-a-suffix', 'file': 'parse.bend', 'old': 'Bool.or(Bool.or(S.matches(h,"("),S.matches(h,"[")),Bool.or(bang(Con{h,t}),operator(Con{h,t})))',
     'new': 'True{}', 'witness': 'suffix-ctl-eqeq', 'phase': 'check', 'wrong': unsupported('term-form')},
    {'name': 'marker-an-operator', 'file': 'parse.bend', 'old': 'Bool.not(marker(Con{h,t}))', 'new': 'True{}',
     'witness': 'suffix-ctl-marker-plus', 'phase': 'check', 'wrong': unsupported('term-form')},
    {'name': 'dot-an-operator', 'file': 'parse.bend', 'old': 'u => Bool.or(starts(t,"|"),Bool.or(starts(t,"^"),starts(t,"&"))),u =>',
     'new': 'u => True{},u =>', 'witness': 'suffix-ctl-dot', 'phase': 'check', 'wrong': unsupported('term-form')},
    {'name': 'bang-without-paren', 'file': 'parse.bend', 'old': 'Bool.and(S.matches(h,"!"),starts(t,"("))', 'new': 'S.matches(h,"!")',
     'witness': 'suffix-ctl-bang', 'phase': 'check', 'wrong': unsupported('term-form')},
    {'name': 'margin-operator-invalid', 'file': 'parse.bend',
     'old': 'S.choose(Result<S.Error,Parsed>,continues(Con{keyword,Con{name,tokens}}),u =>',
     'new': 'S.choose(Result<S.Error,Parsed>,False{},u =>', 'witness': 'suffix-cont-margin', 'phase': 'check',
     'wrong': invalid('parse', 'declaration-name')},
    {'name': 'left-operator-invalid', 'file': 'parse.bend',
     'old': 'S.choose(Result<S.Error,Parsed>,continues(tokens),u =>\n            unsupported(tokens,"term-form"),u => invalid(tokens,"top-level-indentation"))',
     'new': 'S.choose(Result<S.Error,Parsed>,False{},u =>\n            unsupported(tokens,"term-form"),u => invalid(tokens,"top-level-indentation"))',
     'witness': 'suffix-cont-left', 'phase': 'check', 'wrong': invalid('parse', 'top-level-indentation')},
    {'name': 'let-operator-invalid', 'file': 'parse.bend',
     'old': 'S.choose(Result<S.Error,Parsed>,continues(tokens),u =>\n            unsupported(tokens,"term-form"),u => invalid(tokens,"body-indentation"))',
     'new': 'S.choose(Result<S.Error,Parsed>,False{},u =>\n            unsupported(tokens,"term-form"),u => invalid(tokens,"body-indentation"))',
     'witness': 'suffix-cont-let-margin', 'phase': 'check', 'wrong': invalid('parse', 'body-indentation')},
    {'name': 'binding-operator-invalid', 'file': 'parse.bend', 'old': BINDING, 'new': BINDING.replace('continues(tokens)', 'False{}'),
     'witness': 'suffix-cont-let-le', 'phase': 'check', 'wrong': invalid('parse', 'binding-name')},
    {'name': 'binding-paren-invalid', 'file': 'parse.bend', 'old': BINDING,
     'new': BINDING.replace('Bool.and(U32.is_eq(quantity,2),starts(S.skip_lines(tokens),"("))', 'False{}'),
     'witness': 'suffix-plus0-paren-dead', 'phase': 'check', 'wrong': invalid('parse', 'binding-name')},
    {'name': 'binding-paren-needs-no-break', 'file': 'parse.bend', 'old': BINDING,
     'new': BINDING.replace('starts(S.skip_lines(tokens),"(")', 'starts(tokens,"(")'),
     'witness': 'suffix-plus-break-paren', 'phase': 'check', 'wrong': invalid('parse', 'binding-name')},
    {'name': 'binding-repeated-break-invalid', 'file': 'parse.bend', 'old': BINDING_BREAK, 'new': 'False{}',
     'witness': 'suffix-plus-break-plus', 'phase': 'check', 'wrong': invalid('parse', 'binding-name')},
    {'name': 'value-break-term-invalid', 'file': 'parse.bend', 'old': VALUE_BREAK,
     'new': 'False{}', 'witness': 'suffix-let-break-paren', 'phase': 'check', 'wrong': invalid('parse', 'expected-term')},
    {'name': 'value-break-any-token', 'file': 'parse.bend', 'old': VALUE_BREAK,
     'new': 'starts(rhs,"\\n")', 'witness': 'suffix-ctl-let-break-closer', 'phase': 'check',
     'wrong': {'exit': 3, 'diagnostic': 'Unsupported\tparse\tline-break\t'}},
    {'name': 'continuation-needs-no-bang', 'file': 'parse.bend', 'old': 'Bool.or(operator(ts),Bool.or(bang(ts),arrow(ts)))',
     'new': 'Bool.or(operator(ts),arrow(ts))', 'witness': 'suffix-cont-bang-margin', 'phase': 'check',
     'wrong': invalid('parse', 'declaration-name')},
]


def publish_holds(publish, directory):
    """A reader holding the published file open keeps a whole snapshot while it is published again, and nothing is left behind."""
    target = directory / 'wrapper.bend'
    old = 'import old\n' * 200
    publish(target, old)
    with target.open() as held:
        publish(target, 'import new\n')
        snapshot = held.read()
    return snapshot == old and target.read_text() == 'import new\n' and [p.name for p in directory.iterdir()] == ['wrapper.bend']


def publishing(record):
    """The oracle's wrapper writer publishes by rename. A truncating writer must fail the same check."""
    with tempfile.TemporaryDirectory(dir=gate.ROOT / '.local') as scratch:
        directory = Path(scratch)
        gate.require(publish_holds(regen.publish, directory), 'regen.publish must publish by rename')
        (directory / 'wrapper.bend').unlink()
        gate.require(not publish_holds(lambda target, text: target.write_text(text), directory), 'the check must catch an in-place write')
    record['publish'] = {'atomic': True, 'in_place_writer_rejected': True}


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    (gate.ROOT / '.local').mkdir(exist_ok=True)
    gate.BUILD = review.BUILD = BUILD
    manifest = json.loads((HERE / 'round12-expectations.json').read_text())
    paths = [*sorted((gate.ROOT / 'src').glob('*.bend')), *sorted(HERE.glob('*.py')),
             HERE / 'round12-expectations.json', *sorted((HERE / 'round12-fixtures').glob('*.bend'))]
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
              'inputs': {str(p.relative_to(gate.ROOT)): gate.digest(p) for p in paths},
              'builds': [], 'fixtures': [], 'mutants': []}
    try:
        record['oracle'] = gate.successful(['python3', HERE / 'round12_seed.py'])
        publishing(record)
        record['proofs'] = {}
        for entry in sorted((gate.ROOT / 'src').glob('*PROOF.bend')):
            proof = gate.successful([*gate.SEED, entry])
            gate.require(proof['stdout'].strip() == 'All terms check.', proof)
            record['proofs'][entry.name] = proof
        lanes = gate.build_lanes(record)
        cases = manifest['fixtures']
        review.fixtures(record, manifest, lanes)
        gate.MUTANTS = MUTANTS
        gate.mutants(record, manifest, {'fixtures': {}})
        record['sweep'] = fuzz12.check(lanes, BUILD / 'sweep')
        gate.require(record['sweep']['programs'] == fuzz12.COUNT, 'fixed sweep coverage')
        for family, cell in record['sweep']['families'].items():
            # each family needs programs both sides accept and both sides reject
            gate.require(cell.get('seed-Accepted', 0) >= 50 and cell.get('seed-Invalid', 0) >= 50, (family, cell))
        gate.require(all(gate.digest(gate.ROOT / p) == h for p, h in record['inputs'].items()), 'Round-12 inputs changed')
        accepted = sum(c['knot']['exit'] == 0 for c in cases)
        calls = sum(len(c['calls']) for c in cases if c['knot']['exit'] == 0)
        sweep = record['sweep']
        record['counts'] = {'mutants': len(record['mutants']), 'semantic_kills': 2 * len(record['mutants']),
                            'seed_fixtures': len(cases), 'seed_calls': sum(len(c['calls']) for c in cases),
                            'accepted_books': accepted, 'check_observations': 2 * len(cases), 'evaluator_values': 2 * calls,
                            'wasm_values': 2 * calls, 'rejected_phase_observations': 8 * (len(cases) - accepted),
                            'programs': sweep['programs'], 'seed_outcomes': sweep['seed_outcomes'],
                            'knot_outcomes': sweep['knot_outcomes'], 'false_acceptances': sweep['false_acceptances'],
                            'false_invalid': sweep['false_invalid'], 'sweep_evaluator_values': sweep['evaluator_values'],
                            'findings': {f: sum(c['finding'].startswith(f) for c in cases) for f in ('plusfirst', 'suffix')}}
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print('Nest round 12 passed: ' + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
