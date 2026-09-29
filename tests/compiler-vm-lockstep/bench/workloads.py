"""Bump-sized variants of vm/bench's frozen workloads, as knot-vm-1 plans and as seed sources.

vm/bench freezes six workloads and says (README, "The workloads need reclamation") that three of them
allocate beyond a bump arena of 4 GiB, so that vm-lockstep's ratio gate cannot run on the whole set
before vm-rc. The VM has no reclamation yet (vm/CORE.md choice 1), and no image encoder exists
(`src/image.bend`, increment `image`), so a plan here is hand-lowered from the frozen source with the
same functions, the same order of evaluation and the same operations. Frozen sources never change,
and a new size is a new workload: each variant below keeps its frozen source's text except the
constants that size it, and carries its own independent guard.

    peano-b, deep-recursion-b, list-fold-b   the frozen source at a smaller size
    string-scan                              the frozen source, unchanged: it fits (about 2 GiB of cells)
    cps-choose, sha256-64k                   no image: closure churn over generic `choose` is not lowered here,
                                             and SHA-256 needs U32.or and U32.xor, which the registry reserves
                                             (ids 39 and 40) until vm-prims
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FROZEN = ROOT / 'vm/bench'

BOOL = {'kind': 'data', 'name': 'Bool', 'constructors': [{'name': 'False', 'fields': []}, {'name': 'True', 'fields': []}]}
U32 = {'kind': 'opaque', 'name': 'U32'}
NAT = {'kind': 'data', 'name': 'Nat', 'constructors': [{'name': 'Zero', 'fields': []}, {'name': 'Succ', 'fields': [0]}]}


def prim(name: str, id: int, params: list, result: int) -> dict:
    return {'name': name, 'parameters': params, 'result': result, 'slots': len(params),
            'body': ['prim', result, id, [['ref', t, i] for i, t in enumerate(params)]]}


def nat_case(want: int, zero: list, succ: list, first: int) -> list:
    """A Case on slot 0 (a Nat): Zero binds nothing, Succ binds the predecessor at `first`."""
    return ['case', want, 0, 0, 'tags', [['branch', 0, first, 0, zero], ['branch', 1, first, 1, succ]], None]


def tags_case(want: int, slot: int, scrutinee: int, rows: list) -> list:
    return ['case', want, slot, scrutinee, 'tags', rows, None]


def deep_recursion(rounds: int, depth: int = 250000) -> dict:
    nat, u32, boolean = 0, 1, 2
    functions = [
        prim('U32.add', 0, [u32, u32], u32), prim('U32.is_eq', 8, [u32, u32], boolean),
        {'name': 'depth', 'parameters': [nat], 'result': u32, 'slots': 2,
         'body': nat_case(u32, ['lit', u32, 'U32', 0], ['call', u32, 0, [['call', u32, 2, [['ref', nat, 1]]], ['lit', u32, 'U32', 1]]], 1)},
        {'name': 'rounds', 'parameters': [nat, u32], 'result': u32, 'slots': 3,
         'body': nat_case(u32, ['ref', u32, 1],
                          ['call', u32, 3, [['ref', nat, 2], ['call', u32, 0, [['ref', u32, 1], ['call', u32, 2, [['lit', nat, 'Nat', depth]]]]]]], 2)},
        {'name': 'main', 'parameters': [], 'result': boolean, 'slots': 0,
         'body': ['call', boolean, 1, [['call', u32, 3, [['lit', nat, 'Nat', rounds], ['lit', u32, 'U32', 0]]], ['lit', u32, 'U32', rounds * depth]]]},
    ]
    return {'entry': 'book', 'representation': {'Nat': nat, 'U32': u32, 'Bool': boolean}, 'types': [NAT, U32, BOOL], 'functions': functions}


def peano(rounds: int, size: int = 1000) -> dict:
    nat, u32, boolean, pea = 0, 1, 2, 3
    peano_type = {'kind': 'data', 'name': 'Peano', 'constructors': [{'name': 'Z', 'fields': []}, {'name': 'S', 'fields': [pea]}]}
    functions = [
        prim('U32.add', 0, [u32, u32], u32), prim('U32.is_eq', 8, [u32, u32], boolean),
        {'name': 'add', 'parameters': [pea, pea], 'result': pea, 'slots': 3,
         'body': tags_case(pea, 0, pea, [['branch', 0, 2, 0, ['ref', pea, 1]],
                                        ['branch', 1, 2, 1, ['con', pea, 1, [['call', pea, 2, [['ref', pea, 2], ['ref', pea, 1]]]]]]])},
        {'name': 'mul', 'parameters': [pea, pea], 'result': pea, 'slots': 3,
         'body': tags_case(pea, 0, pea, [['branch', 0, 2, 0, ['value', pea, 0]],
                                        ['branch', 1, 2, 1, ['call', pea, 2, [['ref', pea, 1], ['call', pea, 3, [['ref', pea, 2], ['ref', pea, 1]]]]]]])},
        {'name': 'peano', 'parameters': [nat], 'result': pea, 'slots': 2,
         'body': nat_case(pea, ['value', pea, 0], ['con', pea, 1, [['call', pea, 4, [['ref', nat, 1]]]]], 1)},
        {'name': 'count', 'parameters': [pea, u32], 'result': u32, 'slots': 3,
         'body': tags_case(u32, 0, pea, [['branch', 0, 2, 0, ['ref', u32, 1]],
                                        ['branch', 1, 2, 1, ['call', u32, 5, [['ref', pea, 2], ['call', u32, 0, [['ref', u32, 1], ['lit', u32, 'U32', 1]]]]]]])},
        {'name': 'rounds', 'parameters': [nat, u32], 'result': u32, 'slots': 3,
         'body': nat_case(u32, ['ref', u32, 1],
                          ['call', u32, 6, [['ref', nat, 2], ['call', u32, 0, [['ref', u32, 1], ['call', u32, 5, [
                              ['call', pea, 3, [['call', pea, 4, [['lit', nat, 'Nat', size]]], ['call', pea, 4, [['lit', nat, 'Nat', size]]]]],
                              ['lit', u32, 'U32', 0]]]]]]], 2)},
        {'name': 'main', 'parameters': [], 'result': boolean, 'slots': 0,
         'body': ['call', boolean, 1, [['call', u32, 6, [['lit', nat, 'Nat', rounds], ['lit', u32, 'U32', 0]]], ['lit', u32, 'U32', rounds * size * size]]]},
    ]
    return {'entry': 'book', 'representation': {'Nat': nat, 'U32': u32, 'Bool': boolean}, 'types': [NAT, U32, BOOL, peano_type], 'functions': functions}


def list_fold(rounds: int, length: int = 1_000_000) -> dict:
    nat, u32, boolean, lst = 0, 1, 2, 3
    list_type = {'kind': 'data', 'name': 'List', 'constructors': [{'name': 'Nil', 'fields': []}, {'name': 'Con', 'fields': [u32, lst]}]}
    per_round = sum(range(1, length + 1)) % 2 ** 32
    functions = [
        prim('U32.add', 0, [u32, u32], u32), prim('U32.is_eq', 8, [u32, u32], boolean),
        {'name': 'build', 'parameters': [nat, u32, lst], 'result': lst, 'slots': 4,
         'body': nat_case(lst, ['ref', lst, 2],
                          ['call', lst, 2, [['ref', nat, 3], ['call', u32, 0, [['ref', u32, 1], ['lit', u32, 'U32', 1]]],
                                            ['con', lst, 1, [['ref', u32, 1], ['ref', lst, 2]]]]], 3)},
        {'name': 'fold', 'parameters': [lst, u32], 'result': u32, 'slots': 4,
         'body': tags_case(u32, 0, lst, [['branch', 0, 2, 0, ['ref', u32, 1]],
                                        ['branch', 1, 2, 2, ['call', u32, 3, [['ref', lst, 3], ['call', u32, 0, [['ref', u32, 1], ['ref', u32, 2]]]]]]])},
        {'name': 'rounds', 'parameters': [nat, u32], 'result': u32, 'slots': 3,
         'body': nat_case(u32, ['ref', u32, 1],
                          ['call', u32, 4, [['ref', nat, 2], ['call', u32, 0, [['ref', u32, 1], ['call', u32, 3, [
                              ['call', lst, 2, [['lit', nat, 'Nat', length], ['lit', u32, 'U32', 1], ['value', lst, 0]]], ['lit', u32, 'U32', 0]]]]]]], 2)},
        {'name': 'main', 'parameters': [], 'result': boolean, 'slots': 0,
         'body': ['call', boolean, 1, [['call', u32, 4, [['lit', nat, 'Nat', rounds], ['lit', u32, 'U32', 0]]],
                                       ['lit', u32, 'U32', rounds * per_round % 2 ** 32]]]},
    ]
    return {'entry': 'book', 'representation': {'Nat': nat, 'U32': u32, 'Bool': boolean}, 'types': [NAT, U32, BOOL, list_type], 'functions': functions}


def string_scan(rounds: int = 900, length: int = 10000) -> dict:
    nat, u32, char, string, boolean = 0, 1, 2, 3, 4
    types = [NAT, U32, {'kind': 'data', 'name': 'Char', 'constructors': [{'name': 'Chr', 'fields': [u32]}]},
             {'kind': 'data', 'name': 'String', 'constructors': [{'name': 'SNil', 'fields': []}, {'name': 'SCon', 'fields': [char, string]}]}, BOOL]
    functions = [
        prim('U32.add', 0, [u32, u32], u32), prim('U32.mod', 4, [u32, u32], u32), prim('Char.from_u32', 18, [u32], char),
        prim('String.eq', 34, [string, string], boolean), prim('U32.is_eq', 8, [u32, u32], boolean),
        {'name': 'hit', 'parameters': [boolean], 'result': u32, 'slots': 1,
         'body': tags_case(u32, 0, boolean, [['branch', 0, 1, 0, ['lit', u32, 'U32', 0]], ['branch', 1, 1, 0, ['lit', u32, 'U32', 1]]])},
        {'name': 'letter', 'parameters': [u32], 'result': char, 'slots': 1,
         'body': ['call', char, 2, [['call', u32, 0, [['lit', u32, 'U32', 97], ['call', u32, 1, [['ref', u32, 0], ['lit', u32, 'U32', 26]]]]]]]},
        {'name': 'build', 'parameters': [nat, u32, string], 'result': string, 'slots': 4,
         'body': nat_case(string, ['ref', string, 2],
                          ['call', string, 7, [['ref', nat, 3], ['call', u32, 0, [['ref', u32, 1], ['lit', u32, 'U32', 1]]],
                                               ['con', string, 1, [['call', char, 6, [['ref', u32, 1]]], ['ref', string, 2]]]]], 3)},
        {'name': 'rounds', 'parameters': [nat, string, u32], 'result': u32, 'slots': 4,
         'body': ['case', u32, 0, nat, 'tags', [
             ['branch', 0, 3, 0, ['ref', u32, 2]],
             ['branch', 1, 3, 1, ['call', u32, 8, [['ref', nat, 3], ['ref', string, 1], ['call', u32, 0, [['ref', u32, 2], ['call', u32, 5, [
                 ['call', boolean, 3, [['call', string, 7, [['lit', nat, 'Nat', length], ['lit', u32, 'U32', 0], ['value', string, 0]]], ['ref', string, 1]]]]]]]]]]], None]},
        {'name': 'main', 'parameters': [], 'result': boolean, 'slots': 0,
         'body': ['call', boolean, 4, [['call', u32, 8, [['lit', nat, 'Nat', rounds],
                                                        ['call', string, 7, [['lit', nat, 'Nat', length], ['lit', u32, 'U32', 0], ['value', string, 0]]],
                                                        ['lit', u32, 'U32', 0]]], ['lit', u32, 'U32', rounds]]]},
    ]
    return {'entry': 'book', 'representation': {'Nat': nat, 'U32': u32, 'Char': char, 'String': string, 'Bool': boolean},
            'types': types, 'functions': functions}


def null_book() -> dict:
    return {'entry': 'book', 'representation': {}, 'types': [BOOL], 'functions': [
        {'name': 'main', 'parameters': [], 'result': 0, 'slots': 0, 'body': ['value', 0, 1]}]}


# ---------------------------------------------------------------- seed sources

def frozen_source(name: str) -> str:
    return (FROZEN / f'{name}.bend').read_text()


def resized(name: str, edits: list) -> str:
    """The frozen source with only the constants that size it replaced; each edit applies once."""
    text = frozen_source(name)
    for old, new in edits:
        assert text.count(old) == 1, (name, old)
        text = text.replace(old, new)
    return text


def variants() -> dict:
    """name -> {source: seed source, plan: knot-vm-1 plan, frozen: the frozen workload it sizes down, work: units}"""
    per_round = sum(range(1, 1_000_001)) % 2 ** 32
    d_rounds, p_rounds, l_rounds = 120, 12, 12
    return {
        'deep-recursion-b': {
            'frozen': 'deep-recursion', 'plan': deep_recursion(d_rounds), 'work': {'levels': d_rounds * 250000},
            'source': resized('deep-recursion', [('rounds(4000n,0),1000000000)', f'rounds({d_rounds}n,0),{d_rounds * 250000})')])},
        'peano-b': {
            'frozen': 'peano', 'plan': peano(p_rounds), 'work': {'product_cells': p_rounds * 1_000_000},
            'source': resized('peano', [('rounds(200n,0),200000000)', f'rounds({p_rounds}n,0),{p_rounds * 1_000_000})')])},
        'list-fold-b': {
            'frozen': 'list-fold', 'plan': list_fold(l_rounds), 'work': {'list_cells': l_rounds * 1_000_000},
            'source': resized('list-fold', [('rounds(240n,0),3028717056)', f'rounds({l_rounds}n,0),{l_rounds * per_round % 2 ** 32})')])},
        'string-scan': {
            'frozen': 'string-scan', 'plan': string_scan(), 'work': {'characters': 900 * 10000},
            'source': frozen_source('string-scan')},
    }
