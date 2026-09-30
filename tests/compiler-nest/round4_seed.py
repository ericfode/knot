#!/usr/bin/env python3
"""Replay round-4 seed observations. --write is only for the pre-fix freeze.

Knot outcomes are literal review, keyed by fixture; the seed decides only
acceptance. The seed's decreasing-call rule is not implemented in full, so a
seed-rejected recursion stays Unsupported, never Invalid (D4).
"""
import argparse
import json
from pathlib import Path

import regen as oracle
import review_seed

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'round4-expectations.json'
FIXTURES = HERE / 'round4-fixtures'


def unsupported(phase, code):
    return {'exit': 3, 'diagnostic': f'Unsupported\t{phase}\t{code}\t'}


# Finding -> fixture -> reviewed Knot outcome for a seed rejection.
REJECTED = {
    'rebuilt-descent': {name: unsupported('check', 'recursive-call') for name in (
        'rebuilt-root', 'rebuilt-root-source', 'rebuilt-swapped-fields', 'rebuilt-retyped-constant',
        'rebuilt-partial', 'rebuilt-unrefined-constant')},
}
ACCEPTED = {
    'rebuilt-descent': ('rebuilt-field-default', 'rebuilt-field-default-type', 'rebuilt-list-default',
                        'rebuilt-tree-default', 'rebuilt-refined-variable', 'rebuilt-source-constructor',
                        'rebuilt-source-constant', 'rebuilt-nested-constant'),
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
    result = {'basis': 'Reviewer repros and seed-derived controls, frozen with the pinned seed before the repair.',
              'seed': oracle.environment()[0],
              'fixtures': [observe(p, *table[p.stem]) for p in files]}
    if write:
        MANIFEST.write_text(json.dumps(result, indent=2) + '\n')
    else:
        assert result == json.loads(MANIFEST.read_text()), 'round-4 seed observations changed'
    print(f"Round-4 seed: {len(result['fixtures'])} fixtures, "
          f"{sum(len(c['calls']) for c in result['fixtures'])} calls; no differences")


if __name__ == '__main__':
    main()
