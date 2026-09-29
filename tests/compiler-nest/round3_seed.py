#!/usr/bin/env python3
"""Replay round-3 seed observations. --write is only for the pre-fix freezes.

Knot outcomes are literal review, keyed by fixture; the seed decides only
acceptance. A seed-rejected fixture must name its Knot diagnostic, and a
seed-accepted fixture can never be Invalid (D4).

Amended in review round 9: the seed accepts a dotted binder that rebinds a name
in scope, and the parser did not resolve scopes yet, so every dotted binder
(a pattern, a `+` promotion, a let, a typed let) was Unsupported parse
dotted-binder, never Invalid (D4). The seed observations are unchanged.

Amended in the integration of the literals line (review round 1): the parser scopes a
dotted binder to the names in scope (parameters and the lets above it), so a rebinding is
accepted, as the seed accepts it, and a dotted binder that binds nothing is Invalid, as the
seed rejects it: `pattern-binder` in a pattern, `binding-name` in a let. The ten fixtures
below are all seed-rejected; only their reviewed Knot outcome changes.
"""
import argparse
import json
from pathlib import Path

import regen as oracle
import review_seed

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'round3-expectations.json'
FIXTURES = HERE / 'round3-fixtures'


def invalid(phase, code):
    return {'exit': 2, 'diagnostic': f'Invalid\t{phase}\t{code}\t'}


def unsupported(phase, code):
    return {'exit': 3, 'diagnostic': f'Unsupported\t{phase}\t{code}\t'}


# Finding -> fixture -> reviewed Knot outcome for a seed rejection.
REJECTED = {
    'dotted-binder': {
        **{name: invalid('parse', 'pattern-binder') for name in (
            'dot-multi-column', 'dot-variable-row', 'dot-nested-field', 'dot-flat-field',
            'dot-promotion', 'dot-anonymous', 'dot-constructor-name')},
        **{name: invalid('parse', 'binding-name') for name in ('dot-let', 'dot-let-reusable', 'dot-let-typed')},
        **{name: invalid('lex', 'name') for name in (
            'name-trailing-dot', 'name-double-dot', 'name-digit-segment',
            'name-type-double-dot', 'name-field-double-dot')},
    },
    'empty-binding': {name: invalid('check', 'missing-arm') for name in (
        'empty-after-multi', 'empty-after-control', 'empty-after-flat', 'empty-erased-control',
        'empty-field-after', 'empty-field-after-flat', 'empty-field-after-nested', 'empty-field-erased',
        'empty-param-after-field', 'empty-param-after-nested', 'empty-alias-erased')},
    'line-broken-header': {
        'line-missing-colon': invalid('parse', 'expected-:'),
        'line-scrutinee-missing-colon': invalid('parse', 'expected-:'),
        'line-trailing-comma': invalid('parse', 'expected-term'),
    },
}
ACCEPTED = {
    'dotted-binder': ('dot-parameter', 'dot-erased-let', 'dot-field-declaration', 'dot-definition', 'name-comment'),
    'empty-binding': ('empty-multi', 'empty-multi-alias', 'empty-multi-first', 'empty-multi-middle', 'empty-multi-skip',
                      'empty-flat', 'empty-flat-zero-row', 'empty-field-nested', 'empty-field-flat', 'empty-field-binder',
                      'empty-param-before-field', 'empty-param-before-nested', 'empty-field-before-nested', 'empty-data'),
    'line-broken-header': ('line-row', 'line-row-comma', 'line-scrutinee', 'line-pattern-braces', 'line-scrutinee-comma',
                           'line-case', 'line-match', 'line-case-single', 'line-colon', 'line-row-last',
                           'line-row-last-comma', 'line-promotion', 'line-comment'),
}


def reviewed():
    table = {}
    for finding, cases in REJECTED.items():
        for name, knot in cases.items():
            table[name] = (finding, knot)
    for finding, names in ACCEPTED.items():
        for name in names:
            table[name] = (finding, {'exit': 0, 'outcome': 'Accepted'})
    return table


def observe(path, finding, knot):
    case = review_seed.observe(path)
    case['finding'] = finding
    accepted = case['seed']['exit'] == 0
    assert accepted == (knot['exit'] == 0), (path.name, 'seed and reviewed Knot acceptance differ')
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
    result = {'basis': 'Reviewer repros and seed-derived controls, frozen with the pinned seed before each repair.',
              'seed': oracle.environment()[0],
              'fixtures': [observe(p, *table[p.stem]) for p in files]}
    if write:
        MANIFEST.write_text(json.dumps(result, indent=2) + '\n')
    else:
        assert result == json.loads(MANIFEST.read_text()), 'round-3 seed observations changed'
    print(f"Round-3 seed: {len(result['fixtures'])} fixtures, "
          f"{sum(len(c['calls']) for c in result['fixtures'])} calls; no differences")


if __name__ == '__main__':
    main()
