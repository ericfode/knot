#!/usr/bin/env python3
"""Round-10 regressions: a `+` or `-` marker and a return arrow read glued to what follows; a gap makes an operator or a malformed result."""
import datetime
import json
from pathlib import Path

import check as gate
import review

HERE = Path(__file__).resolve().parent
BUILD = gate.ROOT / '.local/compiler-nest/round10'
RECEIPT = HERE / 'receipts/round10.json'
ACCEPTED = {'exit': 0}


def invalid(code):
    return {'exit': 2, 'diagnostic': f'Invalid\tparse\t{code}\t'}


TAIL = 'Bool.or(scrutinee(tokens),promotes(tokens))'
FIRST = 'Bool.or(first,S.marks(h,second))'
ARROW = 'Bool.and(S.touches(dash,arrow),S.identifier(typ))'
# The first two ignore the row gap (the finding, then the later-column site alone; Arms
# tests the same predicate as RowTail, which re-tests it, so a lax Arms cannot be
# observed). The third accepts a marker before a line break; the fourth touches a
# leading promotion, which the seed allows apart. The next three do the same for a
# let marker, and the last two for the return arrow: ignore the gap, and demand more
# than the seed. The stopgaps for whitespace the seed accepts follow: each site reports its
# error again (argument whitespace, a repeated promotion, a line break before a marker's
# name, before `=` at both its sites, and before a value), then the two that would answer
# Unsupported where the seed rejects (a promotion as a call argument, a line break with
# no name or `=` after it).
MUTANTS = [
    {'name': 'ignore-plus-gap', 'file': 'parse.bend',
     'old': 'Bool.and(S.matches(plus,"+"),S.marks(plus,next))', 'new': 'S.matches(plus,"+")',
     'witness': 'rowplus-second-spaced', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'ignore-plus-gap-later-column', 'file': 'parse.bend',
     'old': TAIL, 'new': 'Bool.or(scrutinee(tokens),starts(tokens,"+"))',
     'witness': 'rowplus-three-cols-last', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'mark-a-line-break', 'file': 'syntax.bend',
     'old': 'Bool.and(touches(t,next),identifier(next))', 'new': 'touches(t,next)',
     'witness': 'marker-plus-newline', 'phase': 'check',
     'wrong': {'exit': 3, 'diagnostic': 'Unsupported\tparse\tline-break\t'}},
    {'name': 'touch-leading-promotion', 'file': 'parse.bend',
     'old': 'Bool.and(pattern,S.matches(name,"+"))',
     'new': 'Bool.and(pattern,Bool.and(S.matches(name,"+"),S.marks(name,open)))',
     'witness': 'rowplus-first-spaced', 'phase': 'check',
     'wrong': {'exit': 3, 'diagnostic': 'Unsupported\tparse\tterm-form\t'}},
    {'name': 'ignore-marker-gap', 'file': 'parse.bend',
     'old': FIRST, 'new': 'True{}',
     'witness': 'marker-repro', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'every-statement-first', 'file': 'parse.bend',
     'old': 'run(n,BodyAt{column,False{}},S.skip_lines(body))', 'new': 'run(n,BodyAt{column,True{}},S.skip_lines(body))',
     'witness': 'marker-third-statement', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'touch-first-marker', 'file': 'parse.bend',
     'old': FIRST, 'new': 'S.marks(h,second)',
     'witness': 'marker-first-plus-spaced-typed', 'phase': 'check', 'wrong': invalid('detached-marker')},
    {'name': 'ignore-arrow-gap', 'file': 'parse.bend',
     'old': ARROW, 'new': 'S.identifier(typ)',
     'witness': 'arrow-repro', 'phase': 'check', 'wrong': ACCEPTED},
    {'name': 'touch-arrow-type', 'file': 'parse.bend',
     'old': ARROW, 'new': 'Bool.and(S.touches(dash,arrow),Bool.and(S.touches(arrow,typ),S.identifier(typ)))',
     'witness': 'arrow-glued', 'phase': 'check', 'wrong': invalid('function-result')},
    {'name': 'argument-whitespace-invalid', 'file': 'parse.bend',
     'old': 'Bool.and(Bool.not(parameters),Bool.or(scrutinee(tokens),Bool.and(pattern,promotes(tokens))))', 'new': 'False{}',
     'witness': 'argspace-call-flat', 'phase': 'check', 'wrong': invalid('argument-separator')},
    {'name': 'repeated-promotion-invalid', 'file': 'parse.bend',
     'old': 'Bool.and(promoted,S.matches(name,"+"))', 'new': 'False{}',
     'witness': 'plusplus-flat', 'phase': 'check', 'wrong': invalid('pattern-binder')},
    {'name': 'marker-line-break-invalid', 'file': 'parse.bend',
     'old': 'broken(ts),u => unsupported(ts,"line-break"),u =>\n    invalid(ts,code)',
     'new': 'False{},u => unsupported(ts,"line-break"),u =>\n    invalid(ts,code)',
     'witness': 'letsplit-marker-flat', 'phase': 'check', 'wrong': invalid('binding-name')},
    {'name': 'value-line-break-invalid', 'file': 'parse.bend',
     'old': 'broken(rhs),u =>', 'new': 'False{},u =>',
     'witness': 'letsplit-after-eq-flat', 'phase': 'check', 'wrong': invalid('expected-term')},
    {'name': 'equals-line-break-invalid', 'file': 'parse.bend',
     'old': 'Bool.and(starts(ts,"\\n"),starts(S.skip_lines(ts),"="))', 'new': 'False{}',
     'witness': 'letsplit-before-eq-flat', 'phase': 'check', 'wrong': invalid('expected-=')},
    {'name': 'typed-equals-line-break-invalid', 'file': 'parse.bend',
     'old': 'assign(tail)', 'new': 'expect(tail,"=")',
     'witness': 'letsplit-before-eq-flat', 'phase': 'check', 'wrong': invalid('expected-=')},
    {'name': 'marker-equals-line-break-invalid', 'file': 'parse.bend',
     'old': 'assign(Con{separator,tail})', 'new': 'expect(Con{separator,tail},"=")',
     'witness': 'letsplit-before-eq-marker', 'phase': 'check', 'wrong': invalid('expected-=')},
    {'name': 'promoted-call-argument', 'file': 'parse.bend',
     'old': 'Bool.and(pattern,promotes(tokens))', 'new': 'promotes(tokens)',
     'witness': 'argspace-promoted-call', 'phase': 'check',
     'wrong': {'exit': 3, 'diagnostic': 'Unsupported\tparse\targument-whitespace\t'}},
    {'name': 'line-break-before-any-name', 'file': 'parse.bend',
     'old': 'Bool.and(starts(ts,"\\n"),scrutinee(S.skip_lines(ts)))', 'new': 'starts(ts,"\\n")',
     'witness': 'letsplit-after-eq-junk', 'phase': 'check',
     'wrong': {'exit': 3, 'diagnostic': 'Unsupported\tparse\tline-break\t'}},
    {'name': 'line-break-before-any-token', 'file': 'parse.bend',
     'old': 'Bool.and(starts(ts,"\\n"),starts(S.skip_lines(ts),"="))', 'new': 'starts(ts,"\\n")',
     'witness': 'letsplit-before-eq-junk', 'phase': 'check',
     'wrong': {'exit': 3, 'diagnostic': 'Unsupported\tparse\tline-break\t'}},
    {'name': 'erased-repeated-promotion', 'file': 'parse.bend',
     'old': 'Bool.and(promoted,S.matches(name,"+"))', 'new': 'S.matches(name,"+")',
     'witness': 'plusplus-erased-let', 'phase': 'check',
     'wrong': {'exit': 3, 'diagnostic': 'Unsupported\tparse\trepeated-promotion\t'}},
    {'name': 'arm-body-layout-invalid', 'file': 'parse.bend',
     'old': 'Bool.and(U32.is_gt(parent,0),S.identifier(h))', 'new': 'False{}',
     'witness': 'bodycol-arm-flat', 'phase': 'check', 'wrong': invalid('body-indentation')},
    {'name': 'body-layout-any-token', 'file': 'parse.bend',
     'old': 'Bool.and(U32.is_gt(parent,0),S.identifier(h))', 'new': 'U32.is_gt(parent,0)',
     'witness': 'bodycol-empty-arm', 'phase': 'check',
     'wrong': {'exit': 3, 'diagnostic': 'Unsupported\tparse\tbody-indentation\t'}},
]


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    gate.BUILD = review.BUILD = BUILD
    manifest = json.loads((HERE / 'round10-expectations.json').read_text())
    paths = [*sorted((gate.ROOT / 'src').glob('*.bend')), *sorted(HERE.glob('*.py')),
             HERE / 'round10-expectations.json', *sorted((HERE / 'round10-fixtures').glob('*.bend'))]
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
              'inputs': {str(p.relative_to(gate.ROOT)): gate.digest(p) for p in paths},
              'builds': [], 'fixtures': [], 'mutants': []}
    try:
        record['oracle'] = gate.successful(['python3', HERE / 'round10_seed.py'])
        record['proofs'] = {}
        for entry in sorted((gate.ROOT / 'src').glob('*PROOF.bend')):
            proof = gate.successful([*gate.SEED, entry])
            gate.require(proof['stdout'].strip() == 'All terms check.', proof)
            record['proofs'][entry.name] = proof
        lanes = gate.build_lanes(record)
        review.fixtures(record, manifest, lanes)
        gate.MUTANTS = MUTANTS
        gate.mutants(record, manifest, {'fixtures': {}})
        gate.require(all(gate.digest(gate.ROOT / p) == h for p, h in record['inputs'].items()), 'Round-10 inputs changed')
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
    print('Nest round 10 passed: ' + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
