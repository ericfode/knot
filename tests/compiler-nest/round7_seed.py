#!/usr/bin/env python3
"""Replay round-7 seed observations. --write is only for the pre-fix freeze.

Knot outcomes are literal review, keyed by fixture; the seed decides only
acceptance. A `+` row re-quantifies only a lambda-case binder (a parameter or
field). A let binder, and every alias of it, keeps its declared quantity, so
a second use of a `+` alias of an affine let is `consumed more than once`, and
a `+` row on a let of a `Type`-kind value is not a reusable-type request.
"""
import argparse
import json
from pathlib import Path

import regen as oracle
import review_seed

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'round7-expectations.json'
FIXTURES = HERE / 'round7-fixtures'
REUSE = {'exit': 2, 'diagnostic': 'Invalid\tcheck\taffine-reuse\t'}


# Group -> fixture -> reviewed Knot outcome for a seed rejection.
REJECTED = {
    # The finding: a `+` alias of an affine let used twice.
    'let-promotion': {name: REUSE for name in (
        'l7-var-match-latest-promote-row', 'm2-let-call-promote-row', 'm4-let-annot-promote-row',
        'm5-let-ctor-promote-row', 'm9-let-promote-row-multi', 'm13-let-of-let-promote',
        'y1-let-alias-nested-promote', 'y2-let-of-reusable-param-promote', 'y3-let-promote-row-shadowing-let',
        'z2-let-promote-alias-and-let', 'z3-let-of-field-promote', 'own1-color-let-call-promote')},
    # Without a `+` row, an alias of an affine parameter stays affine.
    'parameter-alias': {name: REUSE for name in ('p1-param-alias-reuse', 'p2-param-alias-and-param')},
    # A `+` row on a parameter still asks for a reusable (`Data`) type.
    'parameter-kind': {'t2-type-param-promote-row': {'exit': 2, 'diagnostic': 'Invalid\tcheck\treusable-type\t'}},
}
ACCEPTED = {
    # A `+` row on a let of a `Type`-kind value; HEAD reported reusable-type.
    'let-kind': ('t1-type-let-promote-row',),
    'control': ('m1-let-promote-row-single', 'm3-reusable-let-promote-row', 'm6-field-var-match-promote',
                'm11-nested-alias-promote', 'z1-param-promote-alias-and-param', 'z4-param-promote-alias-multi-and-param',
                'l5-var-match-latest-let-promote', 'l8-var-match-erased-let', 'l9-var-match-let-shadow-param',
                'x3-erased-let-alias-erased-use', 'x6-let-promote-alias-then-erased-use', 'x7-let-alias-use-and-erased',
                'm7-type-field-var-match-promote', 'm8-param-after-use-promote', 'm12-field-nested-alias-promote',
                'z5-promote-alias-then-rebuilt-parent', 'own2-control-single',
                't3-let-promote-row-unused', 't4-erased-let-promote-row'),
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
    if knot == REUSE:
        assert 'consumed more than once' in case['seed']['stderr'], (path.name, 'seed rejects for another reason')
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
    result = {'basis': 'Reviewer let/alias repros verbatim, parameter-alias and datatype-kind companions and '
                       'seed-accepted promotion controls, frozen with the pinned seed before the repair.',
              'seed': oracle.environment()[0],
              'fixtures': [observe(p, *table[p.stem]) for p in files]}
    if write:
        MANIFEST.write_text(json.dumps(result, indent=2) + '\n')
    else:
        assert result == json.loads(MANIFEST.read_text()), 'round-7 seed observations changed'
    print(f"Round-7 seed: {len(result['fixtures'])} fixtures, "
          f"{sum(len(c['calls']) for c in result['fixtures'])} calls; no differences")


if __name__ == '__main__':
    main()
