#!/usr/bin/env python3
"""Replay round-9 seed observations. --write is only for the pre-fix freeze.

Knot outcomes are literal review, keyed by fixture; the seed decides only
acceptance. The seed infers an unannotated let's value and cannot infer a
constructor. A matched binder is its constructor in a positive branch, so
`v = z` is rejected there ("an annotated term (cannot infer)"), through an
alias, a nested field level or an enclosing match. A binder the match never
refined stays inferable: a residual or default row (the seed types it
`C3<> - A{}`), a field that was never split, a call, a later parameter, and an
annotated let.

The seed also accepts a dotted binder that rebinds a name in scope, which Knot
does not resolve yet: every dotted binder, in a let, a typed let or a pattern,
is Unsupported (coordinator decision, round 9), never Invalid (D4).

The seed reads a line break inside call or constructor arguments as whitespace,
and a second arm on the line of an arm's body as the next arm. Knot ends a term
at a line break, so these seed-accepted programs are Unsupported, never Invalid.
A def header's parameters and a type's fields have the same gap; it stays open
(it is the selfhost suite's `layout` need).
"""
import argparse
import json
from pathlib import Path

import regen as oracle
import review_seed

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'round9-expectations.json'
FIXTURES = HERE / 'round9-fixtures'
INFER = {'exit': 2, 'diagnostic': 'Invalid\tcheck\tannotation-required\t'}
ACCEPTED = {'exit': 0, 'outcome': 'Accepted'}
DOTTED = {'exit': 3, 'diagnostic': 'Unsupported\tparse\tdotted-binder\t'}
BREAK = {'exit': 3, 'diagnostic': 'Unsupported\tparse\tline-break\t'}
ARM = {'exit': 3, 'diagnostic': 'Unsupported\tparse\tsame-line-arm\t'}
SITES = ('default-col', 'default-resid', 'flat-param', 'inline', 'inline-outer', 'multi-col1',
         'multi-col2', 'nested-field', 'nested-inner', 'nested-sub', 'var-row-alias')
LETS = ('plain', 'erased', 'promo')


def letx(forms):
    return [f'letx-{site}-{form}' for site in SITES for form in forms]


# Group -> fixture -> reviewed Knot outcome.
REVIEWED = {
    # The finding: an unannotated let of a binder refined to a constructor at
    # that leaf, in every let form (`v =`, `+v =`, `-v =`) and at every site.
    'let-of-refined-binder': {name: INFER for name in (
        *letx(LETS),
        'letm-default', 'letm-flat', 'letm-flatfield', 'letm-flatunused', 'letm-multi', 'letm-nested',
        *(f'fuzz-q{i}' for i in (1040, 1062, 1208, 1600, 1671, 1815, 2411, 2495)))},
    # Already Invalid: a literal constructor has always needed an annotation.
    'literal-control': {'letm-literal': INFER},
    # The seed accepts these, and so must Knot: an annotated let, a residual
    # binder, and binders the match never refined.
    'inferable-control': {name: ACCEPTED for name in (
        *letx(('annot',)), 'letm-annotated', 'letm-wildrow',
        'twin-call-rebuilt', 'twin-field-unsplit', 'twin-later-param', 'twin-nested-field-binder')},
    # A rebound dotted binder is accepted by the seed: the modules review's three
    # probes (a let, a typed let, a field) and the other binder sites. Unsupported
    # is non-accepting. An erased let's dotted name is a name and stays accepted.
    'dotted-binder-stopgap': {**{name: DOTTED for name in (
        'rebound-let', 'rebound-typed-let', 'rebound-field', 'rebound-promotion',
        'rebound-row', 'rebound-multi', 'rebound-nested')}, 'rebound-erased-let': ACCEPTED},
    # The reviewer's seven main-era probes (sem-r7-probes/hd).
    'layout-stopgap': {**{name: BREAK for name in (
        'hd-b1-body-empty-brace-newline', 'hd-b2-body-open-brace-newline', 'hd-b3-body-comma-newline',
        'hd-b4-body-top-level-ctor-newline', 'hd-b5-call-args-newline', 'hd-h15-ctr-body-newline')},
        'hd-h25-two-cases-one-line': ARM},
}


def reviewed():
    return {name: (finding, knot) for finding, cases in REVIEWED.items() for name, knot in cases.items()}


def observe(path, finding, knot):
    case = review_seed.observe(path)
    case['finding'] = finding
    accepted = case['seed']['exit'] == 0
    assert accepted == (knot['exit'] != 2), (path.name, 'seed acceptance and reviewed Knot outcome differ')
    if knot == INFER:
        assert '- expected : an annotated term (cannot infer)' in case['seed']['stderr'], (path.name, 'seed rejects for another reason')
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
    result = {'basis': 'Reviewer let-of-binder repros verbatim (11 sites in four let forms, the multi-scrutinee, '
                       'default, nested and flat programs, the twins and eight fuzz hits), rebound dotted-binder '
                       'probes (the modules review\'s three verbatim) and line-break probes (the reviewer\'s seven '
                       'verbatim), frozen with the pinned seed before the repairs.',
              'seed': oracle.environment()[0],
              'fixtures': [observe(p, *table[p.stem]) for p in files]}
    if write:
        MANIFEST.write_text(json.dumps(result, indent=2) + '\n')
    else:
        assert result == json.loads(MANIFEST.read_text()), 'round-9 seed observations changed'
    print(f"Round-9 seed: {len(result['fixtures'])} fixtures, "
          f"{sum(len(c['calls']) for c in result['fixtures'])} calls; no differences")


if __name__ == '__main__':
    main()
