#!/usr/bin/env python3
"""Replay round-10 seed observations. --write is only for the pre-fix freeze.

Knot outcomes are literal review, keyed by fixture; the seed decides only
acceptance. The seed's operator loop (`parse_term_ops`, bend.ts) reads a `+` or
`-` as an infix operator unless a name starts right after it. Three
consequences, each frozen here from the reviewer's probes:

- After a term in a pattern row, `a + b`, `a+ b` and a `+ b` on the next line
  are one operator term, so the row has too few patterns and is rejected; `a +b`
  and `a+b` open the next column. A `+` that starts a row or follows a comma is
  not after a term, and stays a promotion spaced or not.
- The same loop reads a let's value. A spaced marker on the next line (`+ u : F
  = ..`) continues that value, and the next statement would start at the `:` or
  `=`; a marker first in a body follows no value and may be spaced.
- A return arrow is the literal `->`; `- >` is rejected.

The seed also reads arguments separated by whitespace alone (`two(a b)`, `Pr{a b}`),
a promotion of a promotion (`++y`, `+ +y`, `++u = x`) and a let split across lines
(a marker, then its name, then `=`, then the value) as ordinary. Knot ends a term at
a line break and reads one `+` promotion, so these seed-accepted programs are
Unsupported, never Invalid (D4). Only a term can follow an argument as another one
(a name, or a `+` marker in a pattern), so `two(a = b)` and `two(a + b)` stay Invalid.
An arm body on the line after its `case`, at the case's column or below it, is
seed-accepted layout (an empty arm and a `def` after it are seed-rejected and stay
Invalid). A def body at column 0 is seed-accepted too, but the frontend gate pins it
Invalid, and an untyped `w` then `= x` reaches `top-level-indentation`: both stay open D4
gaps and are no fixtures.

Amended in the integration of the literals line (review round 1): the parser reads an arm
body wherever it stands and a line break after a let's `=` as whitespace, so the seven body
books and the three after-`=` books are accepted, as the seed accepts them; a line break
before `=` or between a marker and its name stays Unsupported. A bare `+` after an argument
is an operator, which Knot does not check: the seed rejects `two(a + b)` for want of the
annotation an operator demands ("write (a + b : Nat)"), a rule of operator sugar that Knot
does not model, and the same operator with its annotation is valid, so the fixture is
Unsupported, never Invalid (D4). Only the reviewed Knot outcomes change; the seed
observations come from the seed.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import regen as oracle
import review_seed

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'round10-expectations.json'
FIXTURES = HERE / 'round10-fixtures'
ACCEPTED = {'exit': 0, 'outcome': 'Accepted'}


def invalid(code):
    return {'exit': 2, 'diagnostic': f'Invalid\tparse\t{code}\t'}


COLON, MARKER, RESULT = invalid('expected-:'), invalid('detached-marker'), invalid('function-result')


def unsupported(code):
    return {'exit': 3, 'diagnostic': f'Unsupported\tparse\t{code}\t'}


ARGUMENTS, PROMOTION, BREAK = (unsupported('argument-whitespace'), unsupported('repeated-promotion'),
                               unsupported('line-break'))
# What the seed says about each rejected group, so a fixture cannot be rejected for another reason.
REASON = {'plus-row-gap': 'patterns (one per scrutinee)', 'marker-gap': '- expected : a term',
          'arrow-gap': "- expected : '->'"}
GRID = [f'rowtok-{sep}-{left}-{right}' for sep in ('spaced', 'after', 'newline')
        for left in ('a', 'wild', 'ctor', 'promo', 'a1') for right in ('b', 'wild')]

# Group -> fixture -> reviewed Knot outcome.
REVIEWED = {
    # The finding: a `+` detached from its binder between row columns. The row-token
    # grid (three separators, five left and two right patterns) and the reviewer's
    # plus grid, with the two- and three-column repros and the fielded variant.
    'plus-row-gap': {name: COLON for name in (
        *GRID, 'rowplus-second-spaced', 'rowplus-second-plus-space-after', 'rowplus-ctor-spaced',
        'rowplus-nl-spaced', 'rowplus-wild-spaced', 'rowplus-three-cols-mid', 'rowplus-three-cols-last',
        'rowplus-three-cols-both', 'rowplus-plus-wild-spaced', 'rowplus-plus-plus',
        'rowplus-repro-column', 'rowplus-repro-column-fields', 'rowplus-comment-newline',
        'rowplus-comment-glued-newline', 'rowplus-comment-space-newline')},
    # Seed-accepted, and must stay accepted: a `+` glued to its binder, and a
    # promotion that starts a row, follows a comma or sits inside fields.
    'plus-row-control': {name: ACCEPTED for name in (
        'rowplus-comma-glued', 'rowplus-comma-nospace', 'rowplus-comma-nospace-spaced-plus',
        'rowplus-comma-spaced', 'rowplus-ctor-glued', 'rowplus-ctor-tight', 'rowplus-field-spaced-plus',
        'rowplus-field-spaced-then-column', 'rowplus-first-column-spaced-flat', 'rowplus-first-glued',
        'rowplus-first-promo-then-ctor', 'rowplus-first-spaced', 'rowplus-first-spaced-wild',
        'rowplus-nl-glued', 'rowplus-plus-wild', 'rowplus-repro-glued-column',
        'rowplus-repro-glued-column-fields', 'rowplus-second-glued', 'rowplus-second-tight',
        'rowplus-three-cols-mid-glued', 'rowplus-var-then-two', 'rowplus-wild-tight')},
    # The finding: a `+` or `-` let marker apart from its name after another statement.
    'marker-gap': {name: MARKER for name in (
        'marker-repro', 'marker-plus-spaced-typed', 'marker-plus-spaced-after-untyped',
        'marker-plus-spaced-untyped', 'marker-minus-spaced-typed', 'marker-minus-spaced-untyped',
        'marker-plus-newline', 'marker-arm-later', 'marker-third-statement',
        'marker-erased-then-plus-spaced', 'marker-after-call-value', 'marker-after-constructor-value')},
    # Seed-accepted: a spaced marker first in a body (typed and untyped, `+` and `-`,
    # in an arm too) and in a parameter list, and a glued marker after a let.
    'marker-control': {name: ACCEPTED for name in (
        'marker-repro-glued', 'marker-after-let-glued-plus', 'marker-after-let-glued-minus',
        'marker-arm-first', 'marker-arm-later-glued', 'marker-third-statement-glued',
        'marker-first-plus-spaced-typed', 'marker-first-plus-double-space',
        'marker-first-plus-spaced-tight-colon', 'marker-first-minus-spaced-typed',
        'marker-first-plus-spaced-untyped', 'marker-first-minus-spaced-untyped',
        'marker-first-plus-glued', 'marker-first-minus-glued', 'marker-param-spaced-plus',
        'marker-param-spaced-erased', 'marker-typed-param-spaced')},
    # The finding: a return arrow split into `-` and `>`.
    'arrow-gap': {name: RESULT for name in (
        'arrow-repro', 'arrow-two-spaces', 'arrow-three-spaces', 'arrow-split-main',
        'arrow-empty-params', 'arrow-type-application')},
    'arrow-control': {name: ACCEPTED for name in (
        'arrow-glued', 'arrow-tight-before', 'arrow-tight-after', 'arrow-tight-both')},
    # Seed-accepted, Unsupported here: arguments (a call's, a pattern's fields) separated
    # by whitespace, in a flat match and a multi-scrutinee one.
    'argument-whitespace': {name: ARGUMENTS for name in (
        'argspace-call-flat', 'argspace-call-multi', 'argspace-fields-flat', 'argspace-fields-multi',
        'argspace-repro-call', 'argspace-repro-fields', 'argspace-nested-call', 'argspace-promoted-fields')},
    # Seed-rejected: what follows the argument is no term, or an operator; a promotion is no
    # argument of a call.
    'argument-control': {'argspace-equals-call': invalid('argument-separator'),
                         'argspace-operator-call': unsupported('operator'),
                         'argspace-operator-fields': invalid('argument-separator'),
                         'argspace-promoted-call': invalid('argument-separator')},
    'repeated-promotion': {name: PROMOTION for name in (
        'plusplus-flat', 'plusplus-multi', 'plusplus-repro', 'plusplus-spaced-flat', 'plusplus-triple-flat',
        'plusplus-let', 'plusplus-spaced-let')},
    # Seed-rejected: an erased marker wants a name, so `-+u` is no promotion of a promotion.
    'repeated-promotion-control': {'plusplus-erased-let': invalid('binding-name')},
    # Seed-accepted: an arm body on the line after its `case`, at the case's column or below it
    # (a def body at column 0 is the frontend gate's pinned Invalid).
    'body-layout': {name: ACCEPTED for name in (
        'bodycol-arm-flat', 'bodycol-arm-multi', 'bodycol-last-arm', 'bodycol-multi-var', 'bodycol-let',
        'bodycol-below-flat', 'bodycol-below-col0')},
    # Seed-rejected: no body at all (the next `case`, or a `def`, follows the colon).
    'body-layout-control': {'bodycol-empty-arm': invalid('body-indentation'),
                            'bodycol-empty-arm-dedent': invalid('body-indentation')},
    'let-break': {**{name: BREAK for name in (
        'letsplit-before-eq-flat', 'letsplit-before-eq-multi', 'letsplit-before-eq-marker',
        'letsplit-marker-flat', 'letsplit-marker-multi', 'letsplit-marker-arm', 'letsplit-erased-marker')},
        **{name: ACCEPTED for name in (
            'letsplit-after-eq-flat', 'letsplit-after-eq-multi', 'letsplit-after-eq-untyped')}},
    # Seed-rejected: nothing that can continue the let follows the line break.
    'let-break-control': {'letsplit-before-eq-junk': invalid('expected-='),
                          'letsplit-after-eq-junk': invalid('expected-term'),
                          'letsplit-marker-junk': invalid('binding-name')},
    # Seed-accepted forms the parser already reports as unsupported, in a multi-scrutinee row.
    'unsupported-control': {'oos-destructuring-let-flat': unsupported('destructuring-binding'),
                            'oos-destructuring-let-multi': unsupported('destructuring-binding'),
                            'oos-generic-param-multi': unsupported('generic-datatype'),
                            'oos-tilde-header': unsupported('template-binder'),
                            'bodycol-nested': unsupported('pattern-or-indentation')},
}


def reviewed():
    return {name: (finding, knot) for finding, cases in REVIEWED.items() for name, knot in cases.items()}


def observe(path, finding, knot):
    case = review_seed.observe(path)
    case['finding'] = finding
    accepted = case['seed']['exit'] == 0
    # Seed-accepted: never Invalid. Seed-rejected: never accepted, and Unsupported only for an operator.
    assert accepted == (knot['exit'] != 2) or (knot == unsupported('operator') and not accepted), (
        path.name, 'seed acceptance and reviewed Knot outcome differ')
    if finding in REASON:
        assert REASON[finding] in case['seed']['stderr'], (path.name, 'seed rejects for another reason')
    case['knot'] = knot
    return case


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--write', action='store_true')
    write = args.parse_args().write
    table = reviewed()
    files = sorted(FIXTURES.glob('*.bend'))
    assert sorted(p.stem for p in files) == sorted(table), ('unreviewed or missing fixtures',
        sorted(set(p.stem for p in files) ^ set(table)))
    with ThreadPoolExecutor(6) as pool:
        cases = list(pool.map(lambda p: observe(p, *table[p.stem]), files))
    result = {'basis': 'Reviewer probes verbatim (the row-token grid, the plus grid with its two- and '
                       'three-column and fielded repros, the let-marker probes and the split-arrow repro, the '
                       'whitespace-argument, repeated-promotion and split-let probes) and their controls, '
                       'frozen with the pinned seed before the repairs.',
              'seed': oracle.environment()[0], 'fixtures': cases}
    if write:
        MANIFEST.write_text(json.dumps(result, indent=2) + '\n')
    else:
        assert result == json.loads(MANIFEST.read_text()), 'round-10 seed observations changed'
    print(f"Round-10 seed: {len(result['fixtures'])} fixtures, "
          f"{sum(len(c['calls']) for c in result['fixtures'])} calls; no differences")


if __name__ == '__main__':
    main()
