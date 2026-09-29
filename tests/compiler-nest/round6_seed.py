#!/usr/bin/env python3
"""Replay round-6 seed observations. --write is only for the pre-fix freeze.

Knot outcomes are literal review, keyed by fixture; the seed decides only
acceptance. A constructor's fields open at a brace touching its name: a space,
comment or line break between them is a seed rejection in patterns and bodies
alike, while a type declaration, a call's parenthesis and the inside of the
braces admit spaces. A tab is lexed before parsing and stays Unsupported.
"""
import argparse
import json
from pathlib import Path

import regen as oracle
import review_seed

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'round6-expectations.json'
FIXTURES = HERE / 'round6-fixtures'
DETACHED = {'exit': 2, 'diagnostic': 'Invalid\tparse\tdetached-brace\t'}


# Group -> fixture -> reviewed Knot outcome for a seed rejection.
REJECTED = {
    # A line break or comment: the header join newly bridged the gap.
    'joined-line': {name: DETACHED for name in (
        'w2-flat-newline', 'k1-header-newline-brace', 'k2-comment-between-name-brace',
        'gap-nested-newline', 'gap-multi-comment-nested')},
    # A space in nested or multi-scrutinee rows, which main did not accept.
    'new-row': {name: DETACHED for name in (
        'w3-nested-space', 'w4-multi-space', 'y8-space-in-braces', 'z2-nested-space',
        'z4-nullary-space-multi', 'z7-multi-ctor-space', 'z8-single-nullary-space-default')},
    # A space in flat, outer, body, argument and let positions, accepted on main too.
    'main-era': {name: DETACHED for name in (
        'w1-flat-space', 'w5-body-space', 'w6-outer-space', 'w7-main-space', 'z1-flat-space',
        'z3-nullary-space-single', 'z5-body-space', 'z6-flat-space-two', 'gap-argument', 'gap-let',
        'gap-constructor-argument')},
    'tab': {'k3-tab-before-brace': {'exit': 3, 'diagnostic': 'Unsupported\tlex\twhitespace\t'}},
}
ACCEPTED = {
    'control': ('touch-declaration-space', 'touch-pattern-inner-space', 'touch-body-inner-space',
                'touch-inner-newline', 'touch-brace-newline', 'touch-inner-space-row', 'touch-multi-next-line',
                'v1-call-space', 'v2-promo-space', 'v3-call-space-in-row', 'y6-comment-in-row'),
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
    result = {'basis': 'Reviewer repros verbatim, further gap positions and seed-accepted spacing controls, '
                       'frozen with the pinned seed before the repair.',
              'seed': oracle.environment()[0],
              'fixtures': [observe(p, *table[p.stem]) for p in files]}
    if write:
        MANIFEST.write_text(json.dumps(result, indent=2) + '\n')
    else:
        assert result == json.loads(MANIFEST.read_text()), 'round-6 seed observations changed'
    print(f"Round-6 seed: {len(result['fixtures'])} fixtures, "
          f"{sum(len(c['calls']) for c in result['fixtures'])} calls; no differences")


if __name__ == '__main__':
    main()
