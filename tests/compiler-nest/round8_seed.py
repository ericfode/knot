#!/usr/bin/env python3
"""Replay round-8 seed observations. --write is only for the pre-fix freeze.

Knot outcomes are literal review, keyed by fixture; the seed decides only
acceptance. A `+` mark raises a frontier binder's quantity at any kind. The
seed forms the binder, and asks its type to be `Data`, only where the binder
leaves the match frontier undestructured: ahead of a later matched binder, or
at a body that is not a match (a let included). A binder destructured first is
never formed; its fields inherit the mark. Knot does not yet match a default
region's scrutinee, so a seed-accepted destructuring there stays Unsupported.
"""
import argparse
import json
from pathlib import Path

import regen as oracle
import review_seed

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'round8-expectations.json'
FIXTURES = HERE / 'round8-fixtures'
KIND = {'exit': 2, 'diagnostic': 'Invalid\tcheck\treusable-type\t'}
DEFAULT = {'exit': 3, 'diagnostic': 'Unsupported\tcheck\tdefault-scrutinee\t'}
ACCEPTED = {'exit': 0, 'outcome': 'Accepted'}

# Group -> fixture -> reviewed Knot outcome.
REVIEWED = {
    # The finding: a promoted binder destructured before the frontier binds it.
    'destructured-promotion': {name: ACCEPTED for name in (
        'k1-param-promote-destructure', 'k2-promote-destructure-field-reuse', 'k3-promote-destructure-rebuild-twice',
        'k4-multi-promote-destructure', 'k5-promote-nested-destructure', 'k6-field-promote-destructure',
        'k7-generated-a02852', 'k8-promote-destructure-both-names', 'k9-promote-destructure-param-name',
        'k10-promote-nested-rows', 'k11-promote-rebuild-reuse', 'k12-promote-field-binder-rebuild',
        'k13-generated-a01432', 'k14-generated-a02809', 'k15-generated-a02883',
        'k16-inherited-field-destructure', 'x1-empty-type-promote-empty-match')},
    # Destructured in a default region: accepted by the seed, Unsupported here.
    'default-scrutinee': {name: DEFAULT for name in (
        'y1-promote-residual-destructure-type', 'y2-promote-residual-destructure-data')},
    # The frontier binds a promoted `Type` binder: at a leaf, a let, a default
    # row, or ahead of a later match (flat, empty or a matrix split).
    'kind-at-binding': {name: KIND for name in (
        'c1-promote-default-row', 'c2-promote-no-match', 'c3-ctor-then-promote-row', 'c4-promote-direct-reuse',
        'c5-ctor-then-promote-use', 'c6-field-promote-direct', 'c7-promote-wildcard-row',
        'c8-empty-type-promote-leaf', 'n1-promote-then-let', 'n2-inherited-field-reused',
        'n3-inherited-field-bound', 'n4-promote-then-match-later', 'n5-promote-then-empty-match-later',
        'n6-promote-column-then-split')},
    # The same shapes at a `Data` kind.
    'data-control': {name: ACCEPTED for name in (
        'd1-data-promote-destructure', 'd4-data-promote-direct-reuse', 'd7-data-ctor-then-promote-row',
        'd8-data-ctor-then-promote-use')},
}


def reviewed():
    return {name: (finding, knot) for finding, cases in REVIEWED.items() for name, knot in cases.items()}


def observe(path, finding, knot):
    case = review_seed.observe(path)
    case['finding'] = finding
    accepted = case['seed']['exit'] == 0
    assert accepted == (knot['exit'] != 2), (path.name, 'seed acceptance and reviewed Knot outcome differ')
    if knot == KIND:
        stderr = case['seed']['stderr']
        assert '- expected : Data' in stderr and '- observed : Type' in stderr, (path.name, 'seed rejects for another reason')
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
    result = {'basis': 'Reviewer Type-kind promotion repros verbatim (host entries over Sel appended where a '
                       'parameter is fielded), reviewer generator hits, frontier-binding negatives and Data '
                       'controls, frozen with the pinned seed before the repair.',
              'seed': oracle.environment()[0],
              'fixtures': [observe(p, *table[p.stem]) for p in files]}
    if write:
        MANIFEST.write_text(json.dumps(result, indent=2) + '\n')
    else:
        assert result == json.loads(MANIFEST.read_text()), 'round-8 seed observations changed'
    print(f"Round-8 seed: {len(result['fixtures'])} fixtures, "
          f"{sum(len(c['calls']) for c in result['fixtures'])} calls; no differences")


if __name__ == '__main__':
    main()
