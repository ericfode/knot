#!/usr/bin/env python3
"""Images whose validation reaches deep into the VM's scope tables, for gate vm-core (SPEC sections 3 and 4).

The validator holds each slot's type and use mark at an absolute scope index: a function's slots start at 0 and a
Closure's at the enclosing unit's base plus its depth at the Closure (vm.wat `$check`), so a slot sits at the sum of
the depths of the Closures around it. A Branch binds every field of its constructor, and one constructor record
serves every Case that matches it, so a few hundred words of image reach depths of thousands, and Closures nested
one in another add them up. The tables hold W + 4200 indices at first (W the image's words) and double when an
index passes them (CORE.md choice 16); these images put indices at, just past and far past those sizes.

Every builder is deterministic and returns a plan of vm/SPEC.md's record form. This module runs nothing:
check-core.py encodes each plan, and the reference codec and the VM must judge it alike.

- `chain`: one function whose body is m nested Cases, each binding the nf fields of one shared constructor `K`, then
  `lets` Lets, then a Construct of the slots `refs` name, each at a declared type;
- `nest`: L erased Closures nested one in another, each a unit of m nested Cases over `K` that captures the last slot
  it bound and hands it to the next;
- `excess`: a unit deeper than its `slots` with a defect after that depth, where the reference codec reports the defect;
- `need`: how many indices a plan's validation holds, from the plan alone; `tuned` puts it at a table size; `scratch`
  says how many bytes of scratch the doubling of the tables takes at least (a valid image can need more than 4 GiB);
- `corpus`: a seeded corpus of `chain` and `nest`, most with one small change the reference codec then judges.
"""
from __future__ import annotations

BIG, FLAG, REC, A, B, C = 0, 1, 2, 3, 4, 5  # type indices: K's type, the answer, the Construct's record, three more field types
ARROW = REC  # `nest` has no record: its third type is the erased arrow
CAPACITY = 4200  # vm.wat `$validate`: the tables begin at W + this many indices
CYCLE = [BIG, A, B, C]  # the field types of a typed `K`, repeated


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def data(name: str, *constructors) -> dict:
    return {'kind': 'data', 'name': name, 'constructors': [{'name': n, 'fields': f} for n, f in constructors]}


def main_fn() -> dict:
    return {'name': 'main', 'parameters': [], 'result': FLAG, 'slots': 0, 'body': ['value', FLAG, 1]}


def extras(typed: bool, pad: int | None) -> list:
    """The types after the first three: A, B and C when `K`'s fields use them, then an unused constructor of `pad` fields,
    whose words move W by exactly `pad` and change nothing else."""
    return [data(n, (f'{n}0', [])) for n in 'ABC'] * typed + ([data('Pad', ('Q', [FLAG] * pad))] if pad is not None else [])


def slot_type(nf: int, m: int, typed: bool, slot: int) -> int:
    """The type of a `chain` slot: the parameter is a `K`, binding k of the Cases holds field j's type at 1 + k * nf + j
    (`K` for every field, or CYCLE repeated when typed), and every slot past those is a Let's Flag."""
    if slot == 0:
        return BIG
    return (CYCLE[(slot - 1) % nf % 4] if typed else BIG) if slot <= m * nf else FLAG


def chain(nf: int, m: int, refs: list, typed: bool = False, pad: int | None = None, lets: int = 0) -> dict:
    """f(x: K) -> Pair. m nested Cases: Case 0 on x, Case k on field 0 of Case k - 1's binding (field 0 is a `K` in every
    `K`). Then `lets` Lets of Off, then a Construct of `refs`, pairs (slot, declared type). The slots are 0, 1 + k * nf + j
    (k < m, j < nf) and the Lets', so `slots` is 1 + m * nf + lets. Typed, K's field j has type CYCLE[j % 4], else `K`.
    `pad` adds an unused type (see `extras`)."""
    fields = [CYCLE[j % 4] if typed else BIG for j in range(nf)]
    first = [1 + k * nf for k in range(m)]
    scrutinee = [0] + first[:-1]
    body = ['con', REC, 0, [['ref', t, s] for s, t in refs]]
    for i in reversed(range(lets)):
        body = ['let', REC, 1 + m * nf + i, ['value', FLAG, 0], body]
    for k in reversed(range(m)):
        body = ['case', REC, scrutinee[k], BIG, 'tags', [['branch', 0, first[k], nf, body]], None]
    types = [data('Big', ('K', fields)), data('Flag', ('Off', []), ('On', [])), data('Pair', ('P', [t for _, t in refs])),
             *extras(typed, pad)]
    f = {'name': 'f', 'parameters': [BIG], 'result': REC, 'slots': 1 + m * nf + lets, 'body': body}
    return {'entry': 'book', 'types': types, 'functions': [f, main_fn()]}


def nest(nf: int, m: int, L: int, caps: int = 1, pad: int | None = None) -> dict:
    """f(x: K) -> K, and inside it L - 1 erased Closures, each inside the last. A unit is m nested Cases over `K` from
    depth `start` (1 in f, `caps` in a Closure). Its Closure captures the last slot the unit's last Case bound and, when
    caps is 2, the first slot its first Case bound; the next unit is that Closure's body. The innermost unit returns its
    last slot. A second capture is used by nothing."""
    types = [data('Big', ('K', [BIG] * nf)), data('Flag', ('Off', []), ('On', [])),
             {'kind': 'erased-arrow', 'domain': None, 'result': BIG}, *extras(False, pad)]
    inner = None
    for level in reversed(range(L)):
        start = 1 if level == 0 else caps
        first = [start + k * nf for k in range(m)]
        scrutinee = [0] + first[:-1]
        if level == L - 1:
            body = ['ref', BIG, start + m * nf - 1]
        else:
            captured = ([first[0]] if caps == 2 else []) + [first[-1]]
            body = ['invoke', BIG, ['closure', ARROW, 0, caps + m * nf, captured, inner], []]
        for k in reversed(range(m)):
            body = ['case', BIG, scrutinee[k], BIG, 'tags', [['branch', 0, first[k], nf, body]], None]
        inner = body
    f = {'name': 'f', 'parameters': [BIG], 'result': BIG, 'slots': 1 + m * nf, 'body': inner}
    return {'entry': 'book', 'types': types, 'functions': [f, main_fn()]}


def excess(kind: str) -> dict:
    """A unit of `slots` 0 that reaches depth 1, and a Reference to slot 5, beyond that depth. The reference codec checks the
    body before the unit's `slots`, so it reports `slot 5 beyond depth 1` and not the slots; a validator that refused at the
    first depth beyond `slots` would report the slots. `function`: f's own body (a Let, then the Reference); `closure`: the
    same in the body of an erased Closure that f invokes."""
    body = ['let', FLAG, 0, ['value', FLAG, 0], ['ref', FLAG, 5]]
    types = [data('Big', ('K', [])), data('Flag', ('Off', []), ('On', [])), {'kind': 'erased-arrow', 'domain': None, 'result': FLAG}]
    if kind == 'closure':
        body = ['invoke', FLAG, ['closure', ARROW, 0, 0, [], body], []]
    return {'entry': 'book', 'types': types,
            'functions': [{'name': 'f', 'parameters': [], 'result': FLAG, 'slots': 0, 'body': body}, main_fn()]}


BUILDERS = {'chain': chain, 'nest': nest, 'excess': excess}


def build(row: dict) -> dict:
    """The plan a frozen row names: {'family': 'chain' | 'nest', 'args': {...}} (refs as [slot, type] pairs)."""
    return BUILDERS[row['family']](**row['args'])


def need(plan: dict) -> int:
    """How many scope indices validation holds for `plan`: the most, over its nodes, of a unit's base plus its depth
    there (vm.wat `$check`; the tables cover the indices below it). From the plan alone, and iterative, for the plans
    nest tens of thousands of Closures deep."""
    most = 0
    for f in plan['functions']:
        work = [(f['body'], len(f['parameters']), 0)]
        while work:
            node, depth, base = work.pop()
            most = max(most, base + depth)
            op = node[0]
            if op in ('con', 'call', 'prim', 'foreign'):
                work += [(k, depth, base) for k in node[3]]
            elif op == 'let':
                work += [(node[3], depth, base), (node[4], depth + 1, base)]
            elif op == 'case':
                work += [(r[4], depth + r[3], base) for r in node[5] if r is not None]
                work += [(node[6][1], depth, base)] if node[6] is not None else []
            elif op == 'closure':
                _, _, live, _, captures, body = node
                work.append((body, len(captures) + live, base + depth))
            elif op == 'invoke':
                work += [(node[2], depth, base), *((a, depth, base) for a in node[3])]
    return most


def scratch(need: int, words: int) -> int:
    """The bytes of boot scratch the tables take at the least while they double from W + 4200 indices to `need`: a table of
    4-byte types and one of use bytes at each size, each 8-byte aligned, the earlier sizes kept (scratch has no free). The
    loader's other tables come on top, so an image whose `scratch` passes what 4 GiB holds cannot be validated."""
    total, cap = 0, words + CAPACITY
    while True:
        total += (4 * cap + 7 & -8) + (cap + 7 & -8)
        if cap >= need:
            return total
        cap = max(2 * cap, cap + 1)


def tuned(nf: int, m: int, tables: int, edge: int, words, typed: bool = False, nrefs: int = 1) -> tuple[int, int]:
    """(pad, lets) that put a `chain`'s `need` `edge` past the tables' size after `tables` doublings, (W + 4200) * 2**tables:
    `lets` moves need by one each and `pad` moves W by one each. `words(plan)` is a plan's W; `nrefs` how many references the
    chain will make, which each add words."""
    depth = 1 + m * nf
    for lets in range(1 << tables):
        top = depth + lets - edge  # (W + 4200) * 2**tables
        base = words(chain(nf, m, [(0, BIG)] * nrefs, typed, 0, lets))
        if top % (1 << tables) == 0 and (top >> tables) - CAPACITY - base >= 0:
            return (top >> tables) - CAPACITY - base, lets
    raise AssertionError(f'chain({nf}, {m}) is too shallow for its tables to double {tables} times, {edge} short')


def edge_refs(nf: int, m: int, typed: bool, size: int, edge: int, tables: int, wrong: int | None = None) -> list:
    """Slots of a `chain` whose need is `size`, `edge` past the table size after `tables` doublings, each at its true type:
    the parameter, the first slots, the last two, and the slots below, at and above each table size. The `wrong`th of
    them is declared as a Flag (or, if it is one, a K) instead."""
    top = size - edge
    slots = {0, 1, 2, 3, size - 1, size - 2} | {(top >> (tables - j)) + d for j in range(tables + 1) for d in (-1, 0, 1)}
    refs = [(s, slot_type(nf, m, typed, s)) for s in sorted(slots) if 0 <= s < size]
    if wrong is not None:
        s, t = refs[wrong]
        refs[wrong] = (s, FLAG if t != FLAG else BIG)
    return refs


# ---------------------------------------------------------------------------- the corpus
def poke(plan: dict, rng) -> str:
    """One small change to a random node of `plan` for the validator to judge. A kind is drawn first, so that the many Cases
    of a deep plan do not crowd out the rest: a Reference's slot or declared type, a Case's slot, a Branch's first slot or
    field count, a Closure's `slots` or a capture, or a function's `slots`. Returns what changed."""
    spots = {'reference': [], 'case': [], 'branch': [], 'closure': [], 'function': []}
    for fn in plan['functions']:
        spots['function'].append((fn, 'slots', 'function slots'))
        work = [fn['body']]
        while work:
            node = work.pop()
            op = node[0]
            if op == 'ref':
                spots['reference'] += [(node, 2, 'slot'), (node, 1, 'type')]
            elif op == 'case':
                spots['case'].append((node, 2, 'case slot'))
                for r in node[5]:
                    if r is not None:
                        spots['branch'] += [(r, 2, 'first slot'), (r, 3, 'fields')]
                        work.append(r[4])
                work += [node[6][1]] if node[6] is not None else []
            elif op == 'closure':
                spots['closure'] += [(node, 3, 'closure slots'), *((node[4], i, 'capture') for i in range(len(node[4])))]
                work.append(node[5])
            elif op in ('con', 'call', 'prim', 'foreign'):
                work += node[3]
            elif op == 'let':
                work += [node[3], node[4]]
            elif op == 'invoke':
                work += [node[2], *node[3]]
    target, key, what = rng.choice(rng.choice([spots[k] for k in spots if spots[k]]))
    old = target[key]
    target[key] = rng.choice([t for t in (BIG, FLAG, REC) if t != old]) if what == 'type' else max(0, old + rng.choice([-2, -1, 1, 2]))
    return f'{what} {old}->{target[key]}'


def corpus(seed: int, count: int, words, Rng) -> list:
    """`count` rows (name, plan, change), deterministic in `seed`. A `chain` has its `need` at, just short of or just past a
    table size after 0 to 3 doublings, one to six references at the edges of those sizes (one in five at another type, one in
    seven past the depth) and K's fields typed or not; a `nest` has 2 to 6 units, one or two captures and a random `pad`.
    Two rows in three then get one small change (`poke`); the reference codec judges them all. `words(plan)` is a
    plan's W and `Rng` is vm/lane.py's generator."""
    rows = []
    for i in range(count):
        rng = Rng(seed, i + 1)
        if rng.random() < 0.6:
            nf = rng.choice([20, 40, 60, 100, 200, 500])
            m = rng.choice([m for m in (20, 40, 60, 80, 120, 130, 320) if 1 + m * nf <= 65536])
            tables, edge, nrefs = rng.choice([0, 1, 2, 3]), rng.choice([-2, -1, 0, 1, 2, 3]), rng.randrange(1, 7)
            typed = rng.random() < 0.7
            try:
                pad, lets = tuned(nf, m, tables, edge, words, typed, nrefs)
            except AssertionError:
                pad, lets, tables = None, 0, 0
            size = 1 + m * nf + lets
            slots = edge_refs(nf, m, typed, size, edge, tables)
            refs = [rng.choice(slots) for _ in range(nrefs)]
            if rng.random() < 1 / 7:
                refs[0] = (size + rng.choice([0, 3]), BIG)
            elif rng.random() < 0.2:
                refs[0] = (refs[0][0], rng.choice([t for t in (BIG, FLAG) if t != refs[0][1]]))
            plan, name = chain(nf, m, refs, typed, pad, lets), f'chain-{i:03d}-{nf}-{m}-{tables}{edge:+d}'
        else:
            nf, m, L = rng.choice([40, 60, 100, 150]), rng.choice([5, 10, 20, 30]), rng.choice([2, 3, 4, 6])
            plan = nest(nf, m, L, rng.choice([1, 1, 2]), rng.randrange(400) if rng.random() < 0.7 else None)
            name = f'nest-{i:03d}-{nf}-{m}-{L}'
        change = poke(plan, rng) if rng.random() < 2 / 3 else 'none'
        rows.append((name, plan, change))
    return rows
