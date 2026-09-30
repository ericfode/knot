#!/usr/bin/env python3
"""Law falsification: each mutation is one replacement in a copy of `src/`; the named proof entry is checked with the
pinned seed and must fail. Each implementation first passes syntax/type checking without the laws; only a failed
proof in the named law file counts. The seed stops at the first failing law (`Location:`). Round 12's historical
receipt predates the operator vocabulary ruling; its let-suffix mutant now falsifies `call_ends_a_let`. Both rounds
can be replayed on the current sources:

    python3 tests/compiler-nest/falsify.py [--write] [round12|round13]
"""
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SEED = ['bun', str(ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts')]
SCRATCH = ROOT / '.local/compiler-nest/falsify'
TIMEOUT = 120 * float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))

MARKED = 'case Con{S.Variable{name},rest} Con{S.Promotion{binder},more}: Con{S.Promotion{name},marked(rest,more)}'
FORM = 'Bool.pick(String,operator(ts),"operator","term-form")'
GAP = 'gap(S.skip_lines(Con{second,tail}))'
PROMOTED = 'Bool.and(Bool.not(pattern),promotes(rest))'
GLUE = 'Bool.pick(String,abuts(t,h,rest),"operator","term-form")'
HOLE = 'Bool.and(Bool.not(Bool.or(parameters,pattern)),S.matches(h,"?"))'
OPENERS = 'Bool.or(matches(t,"("),Bool.or(matches(t,"["),Bool.or(numeral(text(t)),matches(t,"?"))))'
START = 'Bool.and(U32.is_gt(parent,0),S.body_start(h))'
SAME_LINE = 'S.choose(Result<S.Error,List<&2,S.Token>>,operator(ts),u =>'
LINE_END = 'S.choose(Result<S.Error,List<&2,S.Token>>,suffix(ts),u =>'

# (name, file, old, new, proof entry, the law the mutation must falsify)
ROUND12 = [
    ('marked-promotes-every-field', 'matrix.bend', MARKED, MARKED.replace('Con{S.Promotion{binder},more}', 'Con{binder,more}'),
     'matrix-PROOF.bend', 'matrix-LAWS.unmarked_first_row_witness'),
    ('marked-never-promotes', 'matrix.bend', MARKED, MARKED.replace('Con{S.Promotion{name},marked(rest,more)}', 'Con{S.Variable{name},marked(rest,more)}'),
     'matrix-PROOF.bend', 'matrix-LAWS.first_row_marks_witness'),
    ('bang-without-paren', 'parse.bend', 'Bool.and(S.matches(h,"!"),starts(t,"("))', 'S.matches(h,"!")', 'PROOF.bend', 'LAWS.suffix_witness'),
    ('continuation-needs-no-bang', 'parse.bend', 'Bool.or(operator(ts),Bool.or(bang(ts),arrow(ts)))', 'Bool.or(operator(ts),arrow(ts))',
     'PROOF.bend', 'LAWS.continues_witness'),
    ('every-name-a-lambda', 'parse.bend', '    case S.Variable{token}: True{}\n    case _: False{}', '    case S.Variable{token}: True{}\n    case _: True{}',
     'PROOF.bend', 'LAWS.lambda_witness'),
    ('erased-term-unsupported', 'parse.bend', 'Bool.and(U32.is_eq(quantity,2),Bool.or(Bool.and(', 'Bool.and(U32.is_ne(quantity,1),Bool.or(Bool.and(',
     'PROOF.bend', 'LAWS.promoted_term_witness'),
    ('body-suffix-invalid', 'parse.bend', 'S.choose(Result<S.Error,Parsed>,suffix(ts),u => unsupported(ts,form(ts)),u => terminated(value,ts))',
     'terminated(value,ts)', 'PROOF.bend', 'LAWS.suffix_ends_a_body'),
    ('marker-an-operator', 'parse.bend', 'Bool.not(marker(Con{h,t}))', 'True{}', 'PROOF.bend', 'LAWS.marker_ends_no_body'),
    ('let-suffix-invalid', 'parse.bend', LINE_END, 'S.choose(Result<S.Error,List<&2,S.Token>>,False{},u =>', 'PROOF.bend', 'LAWS.call_ends_a_let'),
    ('promoted-term-invalid', 'parse.bend', 'S.choose(Result<S.Error,Parsed>,promoted_term(quantity,Con{separator,tail}),u =>',
     'S.choose(Result<S.Error,Parsed>,False{},u =>', 'PROOF.bend', 'LAWS.promoted_term_is_unsupported'),
]
ROUND13 = [
    ('marker-gap-dropped', 'parse.bend', GAP, 'False{}', 'PROOF.bend', 'LAWS.detached_marker'),
    ('marker-gap-widened', 'parse.bend', GAP, 'True{}', 'PROOF.bend', 'LAWS.spaced_operator_after_a_let'),
    ('operator-code-term-form', 'parse.bend', FORM, '"term-form"', 'PROOF.bend', 'LAWS.suffix_ends_a_body'),
    ('every-suffix-an-operator', 'parse.bend', FORM, '"operator"', 'PROOF.bend', 'LAWS.call_ends_a_body'),
    ('same-line-operator-statement', 'parse.bend', SAME_LINE, 'S.choose(Result<S.Error,List<&2,S.Token>>,False{},u =>', 'PROOF.bend', 'LAWS.suffix_ends_a_let'),
    ('let-call-invalid', 'parse.bend', LINE_END, 'S.choose(Result<S.Error,List<&2,S.Token>>,False{},u =>', 'PROOF.bend', 'LAWS.call_ends_a_let'),
    ('argument-promotion-invalid', 'parse.bend', PROMOTED, 'False{}', 'PROOF.bend', 'LAWS.argument_promotion_is_unsupported'),
    ('argument-glue-lost', 'parse.bend', GLUE, '"term-form"', 'PROOF.bend', 'LAWS.glued_argument_operator_is_unsupported'),
    ('argument-hole-invalid', 'parse.bend', HOLE, 'False{}', 'PROOF.bend', 'LAWS.argument_hole_is_unsupported'),
    ('argument-at-unsupported', 'parse.bend', HOLE, 'Bool.and(Bool.not(Bool.or(parameters,pattern)),Bool.or(S.matches(h,"?"),S.matches(h,"@")))',
     'PROOF.bend', 'LAWS.argument_at_is_invalid'),
    ('body-start-without-paren', 'syntax.bend', OPENERS, OPENERS.replace('matches(t,"(")', 'False{}'), 'PROOF.bend', 'LAWS.body_start_witness'),
    ('arm-body-statement-only', 'parse.bend', START, START.replace('S.body_start(h)', 'S.statement(h)'), 'PROOF.bend', 'LAWS.arm_body_may_start_with_a_term'),
    ('every-token-starts-a-body', 'parse.bend', START, 'U32.is_gt(parent,0)', 'PROOF.bend', 'LAWS.closer_starts_no_body'),
    ('weight-counts-no-arms', 'check.bend', 'case C.Case{token,level,type_id,arms}: arms', 'case C.Case{token,level,type_id,arms}: Nil{}',
     'check-PROOF.bend', 'check-LAWS.weight_counts_every_node'),
    ('weight-never-stops', 'check.bend', 'S.choose(U32,U32.is_eq(budget,0),u => 0,u =>\n        weight(', 'S.choose(U32,False{},u => 0,u =>\n        weight(',
     'check-PROOF.bend', 'check-LAWS.weight_stops_when_spent'),
]
TABLES = {'round12': ROUND12, 'round13': ROUND13}


def one(mutation):
    name, file, old, new, entry, law = mutation
    directory = SCRATCH / name
    shutil.rmtree(directory, ignore_errors=True)
    directory.mkdir(parents=True)
    for source in (ROOT / 'src').glob('*.bend'):
        shutil.copy2(source, directory / source.name)
    text = (directory / file).read_text()
    if text.count(old) != 1:
        return f'{name}  ANCHOR  {text.count(old)} occurrences'
    (directory / file).write_text(text.replace(old, new))
    env = {**os.environ, 'BEND_NO_TELEMETRY': '1'}
    checked = subprocess.run([*SEED, str(directory / 'check-cli.bend'), '--check-only'],
                             capture_output=True, text=True, cwd=ROOT, env=env, timeout=TIMEOUT)
    if checked.returncode != 0 or checked.stdout.strip() != 'All terms check.' or checked.stderr:
        return f'{name} NOT FALSIFIED: implementation failed syntax/type checking'
    result = subprocess.run([*SEED, str(directory / entry)], capture_output=True, text=True, cwd=ROOT,
                            env=env, timeout=TIMEOUT)
    output = result.stdout + result.stderr
    where = re.search(r'Location: (\S+)', output)
    if result.returncode != 1 or not where or where.group(1).rsplit('.', 1)[0] != law.rsplit('.', 1)[0]:
        return f'{name:34s} {entry:18s} law {law:52s} NOT FALSIFIED: {output.strip()[:60]}'
    note = '' if where.group(1) == law else '  (another law of the file fails first)'
    return f'{name:34s} {entry:18s} law {law:52s} first failing law: {where.group(1)}{note}'


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    names = args or list(TABLES)
    lines = []
    for table in names:
        with ThreadPoolExecutor(max_workers=5) as pool:
            lines.append((table, list(pool.map(one, TABLES[table]))))
    for table, rows in lines:
        report = (f'# {table.capitalize()} witness laws: each mutation is one replacement in a copy of src/; the named proof entry is checked with the pinned seed\n'
                  '# and must fail. `first failing law` is where the seed stops; it is the named law unless another law of the same file fails first.\n\n'
                  + '\n'.join(rows) + '\n')
        if '--write' in sys.argv:
            (HERE / f'receipts/{table}-falsification.txt').write_text(report)
        print(report)
    bad = [r for _, rows in lines for r in rows if 'NOT FALSIFIED' in r or 'ANCHOR' in r]
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
