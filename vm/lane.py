#!/usr/bin/env python3
"""Corpora for gate vm-core's differential lane (D7: seed <=> reference evaluation <=> Wasm).

Every builder is deterministic. It returns items (dicts) that hold a plan of vm/SPEC.md's record
form, the words after IMAGE that run it, and, where the same program exists in Bend, its source. This
module runs nothing: check-core.py encodes each plan, runs it through vm.wasm and vm/evaluate.py, and
compares; the seed's native lane runs the items that carry a source and are frozen in vm/core/.

Families:
- `program`: random well-typed Books over small data types, closures, Nat recursion, U32 key Cases and
  every U32 and Nat prim, emitted twice (Bend source and plan). Every second one is laundered: its
  values pass through `none`-typed identities (SPEC section 3), so a Case scrutinizes a word whose
  type only the run can check;
- `sweep`: every prim over boundary operands, as Books whose result lists the answers;
- `print`, `halt`, `digits`, `nat`: Programs and Books that reach the VM's decimal, UTF-8 and text
  writers at their byte and digit boundaries;
- the seeded rows of vm/core/seeded.json (key Cases, wide constructors, tag Defaults) and the
  ill-typed boundary rows of section 6.1.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REGISTRY = json.loads((HERE / 'registry.json').read_text())
PRIM = {p['name']: p for p in REGISTRY['prims'] if p.get('status') != 'reserved'}
FUEL = 1_000_000
M32 = 0xFFFFFFFF
M64 = (1 << 64) - 1


class Rng:
    """SplitMix64 over integers only, so a corpus and its frozen sample never depend on the Python version."""

    def __init__(self, seed: int, index: int = 0):
        self.state = self.mix(seed * 1_000_003 + index)

    @staticmethod
    def mix(x: int) -> int:
        z = (x + 0x9E3779B97F4A7C15) & M64
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & M64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & M64
        return z ^ (z >> 31)

    def next(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & M64
        return self.mix(self.state - 0x9E3779B97F4A7C15)

    def random(self) -> float:
        return (self.next() >> 11) / (1 << 53)

    def randrange(self, first: int, last: int | None = None) -> int:
        first, last = (0, first) if last is None else (first, last)
        return first + self.next() % (last - first)

    def choice(self, items):
        return items[self.randrange(len(items))]

    def sample(self, items, count: int) -> list:
        pool, out = list(items), []
        for _ in range(count):
            out.append(pool.pop(self.randrange(len(pool))))
        return out

    def weighted(self, items, weights):
        point = self.random() * sum(weights)
        for item_, weight in zip(items, weights):
            point -= weight
            if point < 0:
                return item_
        return items[-1]


def item(name: str, family: str, plan: dict, source: str | None = None, argv: list | None = None, **more) -> dict:
    """A corpus row: a Book runs `main` (argv `main FUEL`), a Program `FUEL --`."""
    argv = argv or (['main', str(FUEL)] if plan['entry'] == 'book' else [str(FUEL), '--'])
    return {'name': name, 'family': family, 'plan': plan, 'argv': argv, 'source': source, **more}


# ---------------------------------------------------------------------------- generated programs
DATA = {
    'Flag': [('Off', []), ('On', [])],
    'Tri': [('A', []), ('B', []), ('C', [])],
    'Duo': [('Duo', ['Flag', 'Tri'])],
    'Box': [('Box', ['Duo', 'Flag'])],
    'Opt': [('None0', []), ('Some0', ['Box'])],
    'Two': [('Lo', ['Flag']), ('Hi', ['Tri'])],
    'Bool': [('False', []), ('True', [])],
}
PREDECLARED = {'Bool'}
KEYS = [0, 1, 2, 3, 5, 7, 100, 2 ** 31 - 1, 2 ** 31, 2 ** 31 + 1, 2 ** 32 - 2, 2 ** 32 - 1]
VALUES = KEYS + [4, 6, 8, 65535, 65536, 12345678, 2 ** 16 * 3]
U32_BINARY = ['U32.add', 'U32.sub', 'U32.mul', 'U32.and', 'U32.div', 'U32.mod']
U32_COMPARE = ['U32.is_eq', 'U32.is_ne', 'U32.is_lt', 'U32.is_le', 'U32.is_gt', 'U32.is_ge']
U32_SHIFT = ['U32.shln', 'U32.shrn']
NAT_COMPARE = ['Nat.is_lt', 'Nat.is_eq', 'Nat.is_ne', 'Nat.is_le', 'Nat.is_gt', 'Nat.is_ge']
SIGNATURE = {n: (['U32', 'U32'], 'U32') for n in U32_BINARY}
SIGNATURE.update({n: (['U32', 'U32'], 'Bool') for n in U32_COMPARE})
SIGNATURE.update({n: (['U32', 'Nat'], 'U32') for n in U32_SHIFT})
SIGNATURE.update({n: (['Nat', 'Nat'], 'Bool') for n in NAT_COMPARE})
SIGNATURE.update({'U32.not': (['U32'], 'U32'), 'Nat.sub': (['Nat', 'Nat'], 'Nat'),
                  'U32.to_nat': (['U32'], 'Nat'), 'U32.from_nat': (['Nat'], 'U32')})
DATA_ORDER = list(DATA)
NULLARY = {t for t, cs in DATA.items() if all(not f for _, f in cs)}


def arrow(domain, result):
    return ('->', domain, result)


def is_arrow(t) -> bool:
    return isinstance(t, tuple)


def bend_type(t, top=True) -> str:
    if not is_arrow(t):
        return t
    domain = bend_type(t[1], False)
    return f'({domain}) -> {bend_type(t[2], False)}' if is_arrow(t[1]) else f'{domain} -> {bend_type(t[2], False)}'


class Generator:
    """Random programs: first-order data plus closures. Every binder is unrestricted (`+`) except a
    lambda's parameter, which reaches its helper exactly once. A `match` only opens a definition body
    or an arm (the seed refuses one after a let), and scrutinizes a parameter or a field."""

    def __init__(self, rng: Rng, depth=3):
        self.rng, self.depth = rng, depth
        self.funcs, self.n, self.current = [], 0, None

    def fresh(self, prefix='v'):
        self.n += 1
        return f'{prefix}{self.n}'

    def data(self):
        return self.rng.choice(DATA_ORDER)

    def arrow_type(self, depth=0):
        result = self.arrow_type(depth + 1) if depth < 1 and self.rng.random() < 0.25 else self.data()
        return arrow(self.data(), result)

    def any_type(self):
        return self.arrow_type() if self.rng.random() < 0.25 else self.data()

    def scalar_or_data(self):
        return 'U32' if self.rng.random() < 0.25 else self.data()

    def canonical(self, t):
        """A closed expression of type t that recurses on nothing but the type's own shape."""
        if is_arrow(t):
            return self.lam(t, {}, 0)
        ci = min(range(len(DATA[t])), key=lambda i: len(DATA[t][i][1]))
        return ('ctor', t, ci, [self.canonical(f) for f in DATA[t][ci][1]])

    def lam(self, t, scope, depth):
        """x => h(x, captures...) with a generated helper h(+x: A, +c...) -> R."""
        _, a, r = t
        x = self.fresh('x')
        caps = [(n, ty) for n, ty in scope.items() if self.rng.random() < 0.4][:3]
        helper, hx = self.fresh('h'), self.fresh('p')
        params = [(hx, a)] + [(self.fresh('q'), ty) for _, ty in caps]
        body = self.body(r, dict(params), {n for n, _ in params}, max(depth - 1, 0))
        self.funcs.append({'name': helper, 'params': params, 'ret': r, 'body': body})
        return ('lam', x, a, r, helper, [('var', x)] + [('var', n) for n, _ in caps])

    def simple(self, t, scope, depth):
        rng = self.rng
        if t == 'U32':
            names = [n for n, ty in scope.items() if ty == 'U32']
            r = rng.random()
            if names and r < 0.3:
                return ('var', rng.choice(names))
            if depth > 0 and r < 0.12:
                return ('prim', 'U32.from_nat', [self.simple('Nat', scope, depth - 1)])
            if depth > 0 and r < 0.75:
                name = rng.choice(U32_BINARY + U32_SHIFT + ['U32.not'])
                return ('prim', name, [self.simple(i, scope, depth - 1) for i in SIGNATURE[name][0]])
            calls = [f for f in self.funcs if f['ret'] == 'U32']
            if calls and depth > 0 and r < 0.9:
                f = rng.choice(calls)
                return ('call', f['name'], [self.simple(pt, scope, depth - 1) for _, pt in f['params']])
            return ('u32', rng.choice(VALUES))
        if t == 'Bool' and depth > 0 and rng.random() < 0.6:
            name = rng.choice(U32_COMPARE + NAT_COMPARE)
            return ('prim', name, [self.simple(i, scope, depth - 1) for i in SIGNATURE[name][0]])
        if t == 'Nat':
            names = [n for n, ty in scope.items() if ty == 'Nat']
            r = rng.random()
            if names and r < 0.35:
                return ('var', rng.choice(names))
            if depth > 0 and r < 0.6:
                return ('prim', 'U32.to_nat', [self.simple('U32', scope, depth - 1)])
            if depth > 0 and r < 0.75:
                return ('prim', 'Nat.sub', [self.simple('Nat', scope, depth - 1), self.simple('Nat', scope, depth - 1)])
            return ('nat', rng.randrange(0, 9))
        options = []
        names = [n for n, ty in scope.items() if ty == t]
        if names:
            options.append(('var', 4))
        options.append(('lam', 3) if is_arrow(t) else ('ctor', 3))
        calls = [f for f in self.funcs if f['ret'] == t]
        if self.current is not None and self.current['ret'] == t and depth > 0:
            calls.append(self.current)
        if calls and depth > 0:
            options.append(('call', 4))
        applied = [f for f in self.funcs if is_arrow(f['ret']) and f['ret'][2] == t]  # f(..)(argument)
        if applied and depth > 0:
            options.append(('app', 3))
        kinds, weights = zip(*options)
        kind = rng.weighted(kinds, weights)
        if depth <= 0 and kind in ('call', 'app'):
            kind = 'var' if names else ('lam' if is_arrow(t) else 'ctor')
        if kind == 'var':
            return ('var', rng.choice(names))
        if kind == 'lam':
            return self.lam(t, scope, depth)
        if kind == 'ctor':
            if depth <= 0:
                return self.canonical(t)
            ci = rng.randrange(len(DATA[t]))
            return ('ctor', t, ci, [self.simple(f, scope, depth - 1) for f in DATA[t][ci][1]])
        if kind == 'app':
            f = rng.choice(applied)
            function = ('call', f['name'], [self.simple(pt, scope, depth - 1) for _, pt in f['params']])
            return ('app', function, self.simple(f['ret'][1], scope, depth - 1), t)
        f = rng.choice(calls)
        if f is self.current:  # structural recursion: the Nat argument is the predecessor field
            args = [('var', self.current['pred']) if pt == 'Nat' else self.simple(pt, scope, depth - 1) for _, pt in f['params']]
        elif f.get('rec'):
            args = [('nat', rng.randrange(0, 9)) if pt == 'Nat' else self.simple(pt, scope, depth - 1) for _, pt in f['params']]
        else:
            args = [self.simple(pt, scope, depth - 1) for _, pt in f['params']]
        return ('call', f['name'], args)

    def body(self, t, scope, matchable, depth, linear=None):
        """`matchable`: parameters (at the root) or fields; `linear`: an arrow parameter each leaf applies once."""
        rng = self.rng
        scalars = sorted(n for n in matchable if scope[n] == 'U32')
        if depth > 0 and scalars and rng.random() < 0.6:
            v = rng.choice(scalars)
            keys = sorted(rng.sample(KEYS, rng.randrange(1, 5)))
            arms = [(k, self.body(t, dict(scope), set(), depth - 1, linear)) for k in keys]
            return ('keys', v, arms, self.body(t, dict(scope), set(), depth - 1, linear))
        algebraic = sorted(n for n in matchable if scope[n] not in ('Nat', 'U32'))
        if depth > 0 and algebraic and rng.random() < 0.55:
            v = rng.choice(algebraic)
            d = scope[v]
            constructors = DATA[d]
            defaulted = d in NULLARY and len(constructors) > 1 and rng.random() < 0.4
            listed = list(range(len(constructors)))
            if defaulted:
                listed = sorted(rng.sample(listed, rng.randrange(1, len(constructors))))
            arms = {}
            for ci in listed:
                fields = [(self.fresh('f'), ft) for ft in constructors[ci][1]]
                inner = dict(scope)
                inner.update(fields)
                arms[ci] = (fields, self.body(t, inner, {n for n, _ in fields}, depth - 1, linear))
            default = self.body(t, scope, set(), depth - 1, linear) if defaulted else None
            return ('match', v, d, arms, default)
        lets, inner = [], dict(scope)
        for _ in range(rng.choice([0, 0, 1, 1, 2])):
            ty = self.scalar_or_data()
            e = self.simple(ty, inner, max(depth - 1, 0))
            x = self.fresh('l')
            lets.append((x, ty, e))
            inner[x] = ty
        if linear is not None:
            name, arrow_ty = linear
            leaf = ('app', ('var', name), self.simple(arrow_ty[1], inner, max(depth - 1, 0)), arrow_ty[2])
        else:
            leaf = self.simple(t, inner, max(depth, 0))
        return ('lets', lets, leaf)

    def nat_function(self):
        """A Nat matcher (its successor arm only compares the predecessor) or a structural recursion."""
        rng = self.rng
        recursive = rng.random() < 0.5
        name = self.fresh('r' if recursive else 'm')
        others = [(self.fresh('a'), self.data() if recursive else self.scalar_or_data()) for _ in range(rng.choice([0, 1, 2]))]
        n = self.fresh('n')
        params, ret = [(n, 'Nat')] + others, self.data()
        data = dict(others)
        zero_body = self.body(ret, dict(data), set(), self.depth - 1)
        p = self.fresh('p')
        scope = dict(data)
        scope[p] = 'Nat'
        if not recursive:
            succ_body = self.body(ret, scope, set(), self.depth - 1)
            desc = {'name': name, 'params': params, 'ret': ret}
        else:
            desc = {'name': name, 'params': params, 'ret': ret, 'pred': p}
            self.current = desc
            lets = []
            for _ in range(rng.choice([0, 1])):
                ty = self.data()
                x = self.fresh('l')
                lets.append((x, ty, self.simple(ty, scope, 1)))
                scope[x] = ty
            call = ('call', name, [('var', p) if pt == 'Nat' else self.simple(pt, scope, 1) for _, pt in params])
            leaf = call if rng.random() < 0.5 else self.through_identity(ret, call)
            self.current = None
            succ_body = ('lets', lets, leaf)
            desc['rec'] = True
        desc['body'] = ('match', n, 'Nat', {0: ([], zero_body), 1: ([(p, 'Nat')], succ_body)}, None)
        self.funcs.append(desc)

    def through_identity(self, ret, inner):
        """A non-tail recursive call: the result passes through an earlier one-parameter function of its type."""
        same = [f for f in self.funcs if len(f['params']) == 1 and f['params'][0][1] == ret and f['ret'] == ret]
        return ('call', self.rng.choice(same)['name'], [inner]) if same else inner

    def function(self):
        rng = self.rng
        if rng.random() < 0.3:
            return self.nat_function()
        name = self.fresh('f')
        params = [(self.fresh('a'), self.scalar_or_data()) for _ in range(rng.choice([0, 1, 1, 2, 3]))]
        linear, ret = None, None
        if rng.random() < 0.3:
            arrow_ty, pn = self.arrow_type(), self.fresh('k')
            params.insert(rng.randrange(len(params) + 1), (pn, arrow_ty))
            linear, ret = (pn, arrow_ty), arrow_ty[2]
        ret = ret or self.any_type()
        data = {n: t for n, t in params if not is_arrow(t)}
        body = self.body(ret, dict(data), set(data), self.depth, linear)
        self.funcs.append({'name': name, 'params': params, 'ret': ret, 'body': body})

    def program(self, count):
        for _ in range(count):
            self.function()
        main_type = self.data()
        self.funcs.append({'name': 'main', 'params': [], 'ret': main_type, 'body': self.body(main_type, {}, set(), self.depth)})
        return main_type


def emit_simple(e) -> str:
    k = e[0]
    if k == 'var':
        return e[1]
    if k == 'nat':
        return f'{e[1]}n'
    if k == 'u32':
        return str(e[1])
    if k == 'prim':
        return f"{e[1]}({','.join(emit_simple(a) for a in e[2])})"
    if k == 'ctor':
        return f"{DATA[e[1]][e[2]][0]}{{{','.join(emit_simple(a) for a in e[3])}}}"
    if k == 'call':
        return f"{e[1]}({','.join(emit_simple(a) for a in e[2])})"
    if k == 'app':
        return f'{emit_simple(e[1])}({emit_simple(e[2])})'
    _, x, _, _, helper, args = e  # a lambda
    return f"({x} => {helper}({','.join(emit_simple(a) for a in args)}))"


def emit_body(b, indent) -> list:
    pad = ' ' * indent
    if b[0] == 'lets':
        return [f'{pad}+{x} : {bend_type(ty)} = {emit_simple(e)}' for x, ty, e in b[1]] + [f'{pad}{emit_simple(b[2])}']
    if b[0] == 'keys':
        _, v, arms, default = b
        out = [f'{pad}match {v}:']
        for key, sub in arms:
            out += [f'{pad}  case {key}:', *emit_body(sub, indent + 4)]
        return out + [f'{pad}  case _:', *emit_body(default, indent + 4)]
    _, v, d, arms, default = b
    out = [f'{pad}match {v}:']
    if d == 'Nat':
        return out + [f'{pad}  case 0n:', *emit_body(arms[0][1], indent + 4),
                      f'{pad}  case 1n+{arms[1][0][0][0]}:', *emit_body(arms[1][1], indent + 4)]
    for ci, (fields, sub) in arms.items():
        binders = ','.join(f'+{n}' for n, _ in fields)
        out += [f'{pad}  case {DATA[d][ci][0]}{{{binders}}}:', *emit_body(sub, indent + 4)]
    if default is not None:
        out += [f'{pad}  case _:', *emit_body(default, indent + 4)]
    return out


def emit_program(funcs) -> str:
    lines = ['import Base', '']
    for d, cs in DATA.items():
        if d not in PREDECLARED:
            lines.append(f'type {d} is Data:')
            lines += [f"  {c}{{{', '.join(f'f{i}: {ft}' for i, ft in enumerate(fs))}}}" for c, fs in cs]
            lines.append('')
    for f in funcs:
        params = ', '.join(f'{n}: {bend_type(t)}' if is_arrow(t) else f'+{n}: {bend_type(t)}' for n, t in f['params'])
        lines += [f"def {f['name']}({params}) -> {bend_type(f['ret'])}:", *emit_body(f['body'], 2), '']
    return '\n'.join(lines)


class Lowering:
    """The plan of a generated program: types in a fixed order, one function per prim it calls, then its own."""

    def __init__(self, funcs):
        self.funcs, self.types, self.index = funcs, [], {}
        for d in DATA_ORDER:
            self.index[d] = len(self.types)
            self.types.append(None)
        for d in DATA_ORDER:
            self.types[self.index[d]] = {'kind': 'data', 'name': d, 'constructors': [
                {'name': c, 'fields': [self.type_index(f) for f in fs]} for c, fs in DATA[d]]}
        self.prims = sorted(prims_of(funcs))
        self.fidx = {n: i for i, n in enumerate(self.prims)}
        for i, f in enumerate(funcs):
            self.fidx[f['name']] = len(self.prims) + i
        self.flat = {f['name']: f for f in funcs}
        self.max_depth = 0

    def type_index(self, t):
        if t in self.index:
            return self.index[t]
        if t == 'U32':
            self.index[t] = len(self.types)
            self.types.append({'kind': 'opaque', 'name': 'U32'})
        elif t == 'Nat':
            self.index[t] = len(self.types)
            self.types.append({'kind': 'data', 'name': 'Nat', 'constructors': [
                {'name': 'Zero', 'fields': []}, {'name': 'Succ', 'fields': [self.index['Nat']]}]})
        else:
            _, a, r = t
            ai, ri = self.type_index(a), self.type_index(r)
            self.index[t] = len(self.types)
            self.types.append({'kind': 'arrow', 'domain': ai, 'result': ri})
        return self.index[t]

    def wrappers(self):
        out = []
        for name in self.prims:
            ins, result = SIGNATURE[name]
            ip, o = [self.type_index(x) for x in ins], self.type_index(result)
            out.append({'name': name, 'parameters': ip, 'result': o, 'slots': len(ip),
                        'body': ['prim', o, PRIM[name]['id'], [['ref', t, i] for i, t in enumerate(ip)]]})
        return out

    def build(self):
        fns = self.wrappers()
        for f in self.funcs:
            self.max_depth = len(f['params'])
            body = self.body(f['body'], {n: (i, t) for i, (n, t) in enumerate(f['params'])}, len(f['params']), f['ret'])
            fns.append({'name': f['name'], 'parameters': [self.type_index(t) for _, t in f['params']],
                        'result': self.type_index(f['ret']), 'slots': self.max_depth, 'body': body})
        plan = {'entry': 'book', 'types': self.types, 'functions': fns}
        rep = {n: self.index[n] for n in ('Nat', 'U32', 'Bool') if n in self.index}
        if 'Nat' in rep or 'U32' in rep:
            rep['Bool'] = self.type_index('Bool')
        if rep:
            plan['representation'] = rep
        return plan

    def body(self, b, scope, depth, T):
        self.max_depth = max(self.max_depth, depth)
        if b[0] == 'lets':
            return self.lets(b[1], b[2], scope, depth, T)
        if b[0] == 'keys':
            _, v, arms, default = b
            rows = [['branch', k, depth, 0, self.body(sub, scope, depth, T)] for k, sub in arms]
            return ['case', self.type_index(T), scope[v][0], self.type_index('U32'), 'keys', rows,
                    ['default', self.body(default, scope, depth, T)]]
        _, v, d, arms, default = b
        slot = scope[v][0]
        if d == 'Nat':
            (_, zero_body), (fields, succ_body) = arms[0], arms[1]
            inner = dict(scope)
            inner[fields[0][0]] = (depth, 'Nat')
            rows = [['branch', 0, depth, 0, self.body(zero_body, scope, depth, T)],
                    ['branch', 1, depth, 1, self.body(succ_body, inner, depth + 1, T)]]
            return ['case', self.type_index(T), slot, self.type_index('Nat'), 'tags', rows, None]
        rows = [None] * len(DATA[d])
        for ci, (fields, sub) in arms.items():
            inner = dict(scope)
            for k, (n, ft) in enumerate(fields):
                inner[n] = (depth + k, ft)
            rows[ci] = ['branch', ci, depth, len(fields), self.body(sub, inner, depth + len(fields), T)]
        fallback = None if default is None else ['default', self.body(default, scope, depth, T)]
        return ['case', self.type_index(T), slot, self.index[d], 'tags', rows, fallback]

    def lets(self, lets, leaf, scope, depth, T):
        self.max_depth = max(self.max_depth, depth)
        if not lets:
            return self.simple(leaf, scope, T)
        (x, ty, e), rest = lets[0], lets[1:]
        value = self.simple(e, scope, ty)
        inner = dict(scope)
        inner[x] = (depth, ty)
        body = self.lets(rest, leaf, inner, depth + 1, T)
        self.max_depth = max(self.max_depth, depth + 1)
        return ['let', self.type_index(T), depth, value, body]

    def simple(self, e, scope, T):
        k = e[0]
        if k == 'nat':
            return ['lit', self.type_index('Nat'), 'Nat', e[1]]
        if k == 'u32':
            return ['lit', self.type_index('U32'), 'U32', e[1]]
        if k == 'prim':
            ins, result = SIGNATURE[e[1]]
            return ['call', self.type_index(result), self.fidx[e[1]], [self.simple(a, scope, i) for a, i in zip(e[2], ins)]]
        if k == 'var':
            slot, t = scope[e[1]]
            assert t == T, (e, t, T)
            return ['ref', self.type_index(t), slot]
        if k == 'ctor':
            _, tn, ci, args = e
            if not args:
                return ['value', self.type_index(tn), ci]
            return ['con', self.type_index(tn), ci, [self.simple(a, scope, ft) for a, ft in zip(args, DATA[tn][ci][1])]]
        if k == 'call':
            f = self.flat[e[1]]
            return ['call', self.type_index(f['ret']), self.fidx[e[1]],
                    [self.simple(a, scope, pt) for a, (_, pt) in zip(e[2], f['params'])]]
        if k == 'app':
            _, fe, arg, R = e
            fty = self.type_of(fe, scope)
            return ['invoke', self.type_index(R), self.simple(fe, scope, fty), [self.simple(arg, scope, fty[1])]]
        _, x, a, r, helper, args = e  # a lambda: its captures in ascending slot order, then its argument
        used = []
        for arg in args[1:]:
            if arg[1] not in used:
                used.append(arg[1])
        caps = sorted(used, key=lambda n: scope[n][0])
        inner = {n: (i, scope[n][1]) for i, n in enumerate(caps)}
        inner[x] = (len(caps), a)
        hf = self.flat[helper]
        call = ['call', self.type_index(r), self.fidx[helper], [self.simple(arg, inner, pt) for arg, (_, pt) in zip(args, hf['params'])]]
        return ['closure', self.type_index(arrow(a, r)), 1, len(caps) + 1, [scope[n][0] for n in caps], call]

    def type_of(self, e, scope):
        return scope[e[1]][1] if e[0] == 'var' else self.flat[e[1]]['ret']


def prims_of(funcs) -> set:
    found = set()

    def walk(x):
        if isinstance(x, (tuple, list)):
            if isinstance(x, tuple) and x and x[0] == 'prim' and x[1] in SIGNATURE:
                found.add(x[1])
            for y in x:
                walk(y)
        elif isinstance(x, dict):
            for y in x.values():
                walk(y)
    for f in funcs:
        walk(f['body'])
    return found


def launder(plan: dict, rng: Rng, p_let=0.5, p_param=0.4) -> dict:
    """Metamorphic `none` laundering, meaning-preserving: a Let's value goes through `__id(x: none) -> none`,
    some parameters are declared `none`, and every Reference to a `none`-typed slot goes through
    `__castT(x: none) -> T`. A Case may still scrutinize such a slot, so the run inspects its word."""
    plan = copy.deepcopy(plan)
    types, fns = plan['types'], plan['functions']
    fns.append({'name': '__id', 'parameters': [None], 'result': None, 'slots': 1, 'body': ['ref', None, 0]})
    identity, casts = len(fns) - 1, {}

    def cast(t):
        if t not in casts:
            fns.append({'name': f'__cast{len(casts)}', 'parameters': [None], 'result': t, 'slots': 1, 'body': ['ref', None, 0]})
            casts[t] = len(fns) - 1
        return casts[t]

    def walk(node, scope):
        op = node[0]
        if op in ('lit', 'value'):
            return node
        if op == 'ref':
            _, t, slot = node
            return ['call', t, cast(t), [['ref', None, slot]]] if scope[slot] is None and t is not None else node
        if op in ('prim', 'con', 'call', 'foreign'):
            return [op, node[1], node[2], [walk(k, scope) for k in node[3]]]
        if op == 'let':
            _, t, slot, value, body = node
            v, vt = walk(value, scope), value[1]
            if rng.random() < p_let:
                v, vt = ['call', None, identity, [v]], None
            return ['let', t, slot, v, walk(body, scope + [vt])]
        if op == 'case':
            _, t, slot, scrutinee, mode, rows, default = node
            out = []
            for r in rows:
                if r is None:
                    out.append(None)
                    continue
                _, key, first, fields, body = r
                fts = list(types[scrutinee]['constructors'][key]['fields']) if mode == 'tags' else []
                out.append(['branch', key, first, fields, walk(body, scope + fts)])
            fallback = None if default is None else ['default', walk(default[1], scope)]
            return ['case', t, slot, scrutinee, mode, out, fallback]
        if op == 'closure':
            _, t, live, slots, caps, body = node
            return ['closure', t, live, slots, caps, walk(body, [scope[c] for c in caps] + ([types[t]['domain']] if live else []))]
        _, t, function, arguments = node  # invoke
        return ['invoke', t, walk(function, scope), [walk(a, scope) for a in arguments]]

    for f in fns[:-1]:
        if f['name'].startswith('__'):
            continue
        params = [None if p is not None and rng.random() < p_param else p for p in f['parameters']]
        f['body'], f['parameters'] = walk(f['body'], list(params)), params
    return plan


def program(index: int, seed: int, depth=3, functions=7) -> dict:
    """Program `index` of the corpus: generated from `seed + index`, laundered when `index` is odd."""
    rng = Rng(seed, index)
    generator = Generator(rng, depth)
    generator.program(rng.randrange(2, functions + 1))
    source, plan = emit_program(generator.funcs), Lowering(generator.funcs).build()
    if index % 2:
        plan = launder(plan, Rng(seed + 1, index))
    return item(f'program-{index}', 'program', plan, source)


# ---------------------------------------------------------------------------- prim sweeps
# Each Book's result is a chain of answers: `Ok{Bool, ..}` or `COk{Cmp, ..}`. A value prim is checked
# against its expected word (the answer is True), a comparison shows its own answer.
T = dict(Bool=0, U32=1, Nat=2, Char=3, String=4, Cmp=5, Bs=6, Cs=7)
ANSWERS = {'b': ('Ok', 'End{}', 'Bs', ('False', 'True')), 'c': ('COk', 'CEnd{}', 'Cs', ('LT', 'EQ', 'GT'))}
U = [0, 1, 2, 3, 31, 32, 33, 255, 256, 65535, 65536, 65537, 0x7fffffff, 0x80000000, 0x80000001,
     0xfffffffe, 0xffffffff, 0x55555555, 0xaaaaaaaa, 12345678, 4000000000]
N = [0, 1, 2, 3, 255, 65535, 65536, 65537, 0x7fffffff, 0x80000000, 0x80000001, 0xfffffffe, 0xffffffff]
SHIFT_SEED = [0, 1, 2, 7, 31, 32, 33, 40, 64]
SHIFT_ALL = SHIFT_SEED + [0x7fffffff, 0x80000000, 0xffffffff, 100000]
CHARS = [0, 9, 10, 13, 14, 31, 32, 33, 65, 0xD7FF, 0xD800, 0xDFFF, 0xE000, 0x10FFFF, 0x110000, 0x7fffffff, 0x80000000,
         0xffffffff, 8, 12]
STRINGS = [[], [97], [97, 98], [0x1F600], [0x7fffffff], [0x80000000, 97], [0, 0xffffffff],
           [65, 66, 67, 68, 69, 70, 71, 72, 73, 74], [0xD800], [97, 0xD800, 98]]
CHUNK = 200


def scalar(code: int) -> bool:
    return code < 0xD800 or 0xDFFF < code <= 0x10FFFF


def sweep_types() -> list:
    def data(name, *constructors):
        return {'kind': 'data', 'name': name, 'constructors': [{'name': n, 'fields': f} for n, f in constructors]}
    return [data('Bool', ('False', []), ('True', [])), {'kind': 'opaque', 'name': 'U32'},
            data('Nat', ('Zero', []), ('Succ', [2])), data('Char', ('Chr', [1])),
            data('String', ('SNil', []), ('SCon', [3, 4])), data('Cmp', ('LT', []), ('EQ', []), ('GT', [])),
            data('Bs', ('End', []), ('Ok', [0, 6])), data('Cs', ('CEnd', []), ('COk', [5, 7]))]


class Term:
    """An expression of one prim type with its Bend text and its plan node; prim functions are named
    in the plan until `sweep_program` numbers them."""

    def __init__(self, ty, bend, plan):
        self.ty, self.bend, self.plan = ty, bend, plan


def u32(v):
    return Term('U32', str(v), ['lit', T['U32'], 'U32', v])


def nat(v):
    return Term('Nat', f'{v}n', ['lit', T['Nat'], 'Nat', v])


def char(v):
    return Term('Char', f'Chr{{{v}}}', ['con', T['Char'], 0, [['lit', T['U32'], 'U32', v]]])


def string(codes):
    """An ASCII-safe literal when possible, else the SCon chain."""
    if all(0x20 <= c < 0x7f and c not in (0x22, 0x5c) for c in codes):
        return Term('String', '"' + ''.join(map(chr, codes)) + '"', ['lit', T['String'], 'String', list(codes)])
    bend, plan = 'SNil{}', ['value', T['String'], 0]
    for c in reversed(codes):
        bend = f'SCon{{Chr{{{c}}},{bend}}}'
        plan = ['con', T['String'], 1, [char(c).plan, plan]]
    return Term('String', bend, plan)


def prim(name, *args):
    p = PRIM[name]
    return Term(p['output'], f"{name}({','.join(a.bend for a in args)})",
                ['call', T[p['output']], ('prim', name), [a.plan for a in args]])


def check(term: Term, expected) -> tuple:
    """The Bool `term == expected`, which a correct VM answers True."""
    equal = {'U32': 'U32.is_eq', 'Nat': 'Nat.is_eq', 'Char': 'Char.is_eq', 'String': 'String.eq'}[term.ty]
    return prim(equal, term, {'U32': u32, 'Nat': nat, 'Char': char, 'String': string}[term.ty](expected)), True


def shows(term: Term, expected) -> tuple:
    return term, expected


def sweep_program(entries: list, kind: str) -> tuple[dict, str, str]:
    """(plan, Bend source, expected tree) of a Book whose result chains `entries` [(Term, answer)]."""
    cons, nil, chain, names = ANSWERS[kind]
    bend, plan, tree = nil, ['value', T[chain], 0], nil
    for term, answer in reversed(entries):
        bend = f'{cons}{{{term.bend},{bend}}}'
        plan = ['con', T[chain], 1, [term.plan, plan]]
        tree = f'{cons}{{{names[int(answer)]}{{}},{tree}}}'
    used = []

    def number(node):
        if isinstance(node, list):
            if len(node) == 4 and node[0] == 'call' and isinstance(node[2], tuple):
                name = node[2][1]
                if name not in used:
                    used.append(name)
            for c in node:
                number(c)
    number(plan)
    functions = []
    for name in sorted(used, key=lambda n: PRIM[n]['id']):
        p = PRIM[name]
        ins, out = [T[n] for n in p['inputs']], T[p['output']]
        functions.append({'name': name, 'parameters': ins, 'result': out, 'slots': len(ins),
                          'body': ['prim', out, p['id'], [['ref', t, i] for i, t in enumerate(ins)]]})
    index = {f['name']: i for i, f in enumerate(functions)}

    def resolve(node):
        if isinstance(node, list):
            if len(node) == 4 and node[0] == 'call' and isinstance(node[2], tuple):
                node[2] = index[node[2][1]]
            for c in node:
                resolve(c)
    resolve(plan)
    functions.append({'name': 'main', 'parameters': [], 'result': T[chain], 'slots': 0, 'body': plan})
    source = ('import Base\n\ntype Bs is Data:\n  End{}\n  Ok{h: Bool, t: Bs}\n\n'
              'type Cs is Data:\n  CEnd{}\n  COk{h: Cmp, t: Cs}\n\n'
              f'def main() -> {chain}:\n  {bend}\n')
    representation = {'Nat': 2, 'U32': 1, 'Char': 3, 'String': 4, 'Bool': 0, 'Cmp': 5}
    return {'entry': 'book', 'representation': representation, 'types': sweep_types(), 'functions': functions}, source, tree


def compare_word(a: int, b: int) -> int:
    return 0 if a < b else (1 if a == b else 2)


def sweeps() -> list:
    """Every prim over boundary operands: (name, kind, [(Term, answer)], seedable). A sweep whose operands
    the seed cannot spell (a non-scalar Char, a shift by 2^31 or more, a String past U+10FFFF) is not
    seedable; its Book is still compared with the reference evaluation."""
    out = []
    values = {'U32.add': lambda a, b: (a + b) & M32, 'U32.sub': lambda a, b: (a - b) & M32,
              'U32.mul': lambda a, b: (a * b) & M32, 'U32.div': lambda a, b: a // b if b else 0,
              'U32.mod': lambda a, b: a % b if b else a, 'U32.and': lambda a, b: a & b}
    for name, f in values.items():
        out.append((name, 'b', [check(prim(name, u32(a), u32(b)), f(a, b)) for a in U for b in U], True))
    out.append(('U32.not', 'b', [check(prim('U32.not', u32(a)), ~a & M32) for a in U], True))
    for name, f in {'U32.is_eq': lambda a, b: a == b, 'U32.is_ne': lambda a, b: a != b, 'U32.is_lt': lambda a, b: a < b,
                    'U32.is_le': lambda a, b: a <= b, 'U32.is_gt': lambda a, b: a > b, 'U32.is_ge': lambda a, b: a >= b}.items():
        out.append((name, 'b', [shows(prim(name, u32(a), u32(b)), f(a, b)) for a in U for b in U], True))
    out.append(('U32.cmp', 'c', [shows(prim('U32.cmp', u32(a), u32(b)), compare_word(a, b)) for a in U for b in U], True))
    for name, f in (('U32.shln', lambda a, n: (a << n) & M32 if n < 32 else 0), ('U32.shrn', lambda a, n: a >> n if n < 32 else 0)):
        for suffix, counts, seedable in (('all', SHIFT_ALL, False), ('seed', SHIFT_SEED, True)):
            out.append((f'{name}#{suffix}', 'b', [check(prim(name, u32(a), nat(n)), f(a, n)) for a in U for n in counts], seedable))
    out.append(('conv-nat', 'b', [check(prim('U32.to_nat', u32(a)), a) for a in U] +
                [check(prim('U32.from_nat', nat(a)), a) for a in N], True))
    for suffix, codes in (('seed', [c for c in CHARS if scalar(c)]), ('all', CHARS)):
        seedable = suffix == 'seed'
        out.append((f'conv-char#{suffix}', 'b', [check(prim('Char.from_u32', u32(a)), a) for a in codes] +
                    [check(prim('Char.to_u32', char(a)), a) for a in codes], seedable))
        out.append((f'Char.is_eq#{suffix}', 'b', [shows(prim('Char.is_eq', char(a), char(b)), a == b)
                                                  for a in codes for b in codes], seedable))
        out.append((f'Char.is_space#{suffix}', 'b', [shows(prim('Char.is_space', char(a)), a == 32 or 9 <= a <= 13)
                                                     for a in codes], seedable))
    out.append(('Nat.sub', 'b', [check(prim('Nat.sub', nat(a), nat(b)), max(a - b, 0)) for a in N for b in N], True))
    out.append(('Nat.add', 'b', [check(prim('Nat.add', nat(a), nat(b)), a + b) for a in N for b in N if a + b <= M32], True))
    out.append(('Nat.mul', 'b', [check(prim('Nat.mul', nat(a), nat(b)), a * b) for a in N for b in N if a * b <= M32], True))
    for name, f in {'Nat.is_eq': lambda a, b: a == b, 'Nat.is_ne': lambda a, b: a != b, 'Nat.is_lt': lambda a, b: a < b,
                    'Nat.is_le': lambda a, b: a <= b, 'Nat.is_gt': lambda a, b: a > b, 'Nat.is_ge': lambda a, b: a >= b}.items():
        out.append((name, 'b', [shows(prim(name, nat(a), nat(b)), f(a, b)) for a in N for b in N], True))
    out.append(('Nat.cmp', 'c', [shows(prim('Nat.cmp', nat(a), nat(b)), compare_word(a, b)) for a in N for b in N], True))
    out.append(('U32.show', 'b', [check(prim('U32.show', u32(a)), [ord(c) for c in str(a)]) for a in U], True))
    out.append(('Nat.show', 'b', [check(prim('Nat.show', nat(a)), [ord(c) for c in str(a)]) for a in N], True))
    for suffix, pool in (('seed', [s for s in STRINGS if all(scalar(c) for c in s)]), ('all', STRINGS)):
        seedable = suffix == 'seed'
        out += [(f'String.eq#{suffix}', 'b', [shows(prim('String.eq', string(a), string(b)), a == b) for a in pool for b in pool], seedable),
                (f'String.append#{suffix}', 'b', [check(prim('String.append', string(a), string(b)), a + b) for a in pool for b in pool], seedable),
                (f'String.reverse#{suffix}', 'b', [check(prim('String.reverse', string(a)), a[::-1]) for a in pool], seedable),
                (f'String.length#{suffix}', 'b', [check(prim('String.length', string(a)), len(a)) for a in pool], seedable),
                (f'String.is_empty#{suffix}', 'b', [shows(prim('String.is_empty', string(a)), not a) for a in pool], seedable)]
    return out


def sweep_items() -> list:
    """The sweeps as Books, `CHUNK` answers to a Book (a deeper chain nests the plan and the reference)."""
    rows = []
    for name, kind, entries, seedable in sweeps():
        for c in range(0, len(entries), CHUNK):
            plan, source, tree = sweep_program(entries[c:c + CHUNK], kind)
            rows.append(item(f'sweep-{name}-{c}', 'sweep', plan, source if seedable else None, tree=tree))
    return rows


# ---------------------------------------------------------------------------- Programs and Books at the writers' boundaries
def out_types() -> list:
    """The types of a Program: Unit, U32, Char, String, IO.OP, `Unit -> IO.OP`, its continuation's arrow and the erased one."""
    def data(name, *constructors):
        return {'kind': 'data', 'name': name, 'constructors': [{'name': n, 'fields': f} for n, f in constructors]}
    return [data('Unit', ('Unit', [])), {'kind': 'opaque', 'name': 'U32'}, data('Char', ('Chr', [1])),
            data('String', ('SNil', []), ('SCon', [2, 3])), data('IO.OP', ('Emit', [None]), ('Halt', [1, 3])),
            {'kind': 'arrow', 'domain': 0, 'result': 4}, {'kind': 'arrow', 'domain': 5, 'result': 4},
            {'kind': 'erased-arrow', 'domain': None, 'result': 6}]


OUT_REPRESENTATION = {'Unit': 0, 'U32': 1, 'Char': 2, 'String': 3, 'IO.OP': 4}


def printing(codes: list) -> dict:
    """main = IO.print(<codes>): a Program that writes one line."""
    return {'entry': 'program', 'representation': OUT_REPRESENTATION, 'types': out_types(),
            'functions': [{'name': 'IO.print', 'parameters': [3], 'result': 7, 'slots': 1, 'body': ['foreign', 7, 1, [['ref', 3, 0]]]},
                          {'name': 'main', 'parameters': [], 'result': 7, 'slots': 0,
                           'body': ['call', 7, 0, [['lit', 3, 'String', list(codes)]]]}]}


def halting(code: int, message: list) -> dict:
    """main = @R. k => Halt{code, message}: a Program that stops with a code and a message."""
    return {'entry': 'program', 'representation': OUT_REPRESENTATION, 'types': out_types(),
            'functions': [{'name': 'main', 'parameters': [], 'result': 7, 'slots': 0,
                           'body': ['closure', 7, 0, 0, [], ['closure', 6, 1, 1, [], ['con', 4, 1, [
                               ['lit', 1, 'U32', code], ['lit', 3, 'String', list(message)]]]]]}]}


def escaped(codes: list) -> str:
    return ''.join(f'\\u{{{c:X}}}' for c in codes)


def print_items() -> list:
    """Every UTF-8 length boundary, alone, between two ASCII codes and repeated, and every Halt code and message.
    Where every code is a scalar the seed can run the program too."""
    rows = []
    for c in [0, 0x7f, 0x80, 0x7ff, 0x800, 0xfff, 0x1000, 0xd7ff, 0xe000, 0xffff, 0x10000, 0x1f600, 0x3b1, 0xfffff, 0x100000,
              0x10ffff, 0x110000, 0xd800]:
        for shape in ([120, c, 121], [c], [c, c, c]):
            source = f'import Base\n\ndef main() -> IO(Unit):\n  IO.print("{escaped(shape)}")\n' if all(map(scalar, shape)) else None
            rows.append(item(f'print-{c:x}-{len(shape)}-{shape[0]:x}', 'print', printing(shape), source))
    for code in (0, 1, 255, 256, 257, 65535, 2 ** 31, 2 ** 32 - 1):
        for message in ([], [97], [0x7f, 0x80, 0x7ff, 0x800, 0xffff, 0x10000, 0x10ffff], [0x1f600], [10, 13, 9], [0xd800]):
            source = (f'import Base\n\ndef main() -> IO(Unit):\n  IO.die(Unit, {code}, "{escaped(message)}")\n'
                      if all(map(scalar, message)) else None)
            rows.append(item(f'halt-{code}-{len(message)}-{message[0] if message else 0:x}', 'halt', halting(code, message), source))
    return rows


def digit_items() -> list:
    """A Book's result type index and tag are written in decimal: the type is preceded by `pad` others, the
    result is the last of a type with `count` nullary constructors. A Nat is written as its unary view."""
    rows = []
    for pad in (0, 8, 9, 10, 11, 98, 99, 100, 101, 1000):
        for count in (2, 10, 11, 100, 101, 300):
            types = [{'kind': 'data', 'name': f'P{i}', 'constructors': [{'name': f'P{i}a', 'fields': []}, {'name': f'P{i}b', 'fields': []}]}
                     for i in range(pad)]
            types.append({'kind': 'data', 'name': 'Big', 'constructors': [{'name': f'K{i}', 'fields': []} for i in range(count)]})
            main = {'name': 'main', 'parameters': [], 'result': pad, 'slots': 0, 'body': ['value', pad, count - 1]}
            rows.append(item(f'digits-{pad}-{count}', 'digits', {'entry': 'book', 'types': types, 'functions': [main]}))
    nat = {'kind': 'data', 'name': 'Nat', 'constructors': [{'name': 'Zero', 'fields': []}, {'name': 'Succ', 'fields': [0]}]}
    for n in (0, 1, 2, 3, 9, 10, 99, 100, 1000, 65536):
        main = {'name': 'main', 'parameters': [], 'result': 0, 'slots': 0, 'body': ['lit', 0, 'Nat', n]}
        rows.append(item(f'nat-{n}', 'nat', {'entry': 'book', 'representation': {'Nat': 0}, 'types': [nat], 'functions': [main]}))
    return rows


# ---------------------------------------------------------------------------- seeded rows: key Cases, wide constructors, tag Defaults
# Each row exists as a plan and as Bend, so the seed's native lane can freeze the expected result (D7).
# A result type has one constructor per arm and one more for the Default, so no arm's answer can stand
# in for its neighbour's. A Book returns a chain of the answers to its queries.
def bend_data(name: str, constructors: list) -> str:
    lines = [f'type {name} is Data:']
    for c, fields in constructors:
        lines.append(f"  {c}{{{', '.join(f'{f}: {t}' for f, t in fields)}}}")
    return '\n'.join(lines) + '\n\n'


def answer_types(count: int) -> tuple[list, str]:
    """plan types 0 (`Rs`, R0..R{count-1}) and 1 (`Ch`: End, Ok{Rs, Ch}), and their Bend."""
    plan = [{'kind': 'data', 'name': 'Rs', 'constructors': [{'name': f'R{i}', 'fields': []} for i in range(count)]},
            {'kind': 'data', 'name': 'Ch', 'constructors': [{'name': 'End', 'fields': []}, {'name': 'Ok', 'fields': [0, 1]}]}]
    source = (bend_data('Rs', [(f'R{i}', []) for i in range(count)]) +
              bend_data('Ch', [('End', []), ('Ok', [('h', 'Rs'), ('t', 'Ch')])]))
    return plan, source


def chain_plan(calls: list) -> list:
    """`Ok{c0, Ok{c1, .. End{}}}` over the answer types."""
    plan = ['value', 1, 0]
    for call in reversed(calls):
        plan = ['con', 1, 1, [call, plan]]
    return plan


def chain_bend(calls: list) -> str:
    text = 'End{}'
    for call in reversed(calls):
        text = f'Ok{{{call}, {text}}}'
    return text


def chain_tree(answers: list) -> str:
    """The Book's text for a chain of the answers `R<i>`: no spaces."""
    text = 'End{}'
    for a in reversed(answers):
        text = f'Ok{{R{a}{{}},{text}}}'
    return text


def key_program(name: str, scalar: str, keys: list, queries: list, computed=None, **more) -> dict:
    """A U32 or Char Case with `keys` (strictly increasing; `len(keys)` + 1 answers) queried at each of
    `queries`. A computed query is `U32.add(a, b)` (`Char.from_u32` of it): a fresh cell, a Big one from 2^31.
    `computed` says which queries; by default every second one."""
    assert keys == sorted(set(keys)), keys
    computed = computed or [i % 2 == 1 for i in range(len(queries))]
    types, source = answer_types(len(keys) + 1)
    u32, char = len(types), len(types) + 1
    types.append({'kind': 'opaque', 'name': 'U32'})
    if scalar == 'Char':
        types.append({'kind': 'data', 'name': 'Char', 'constructors': [{'name': 'Chr', 'fields': [u32]}]})
    domain = u32 if scalar == 'U32' else char
    functions = [{'name': 'U32.add', 'parameters': [u32, u32], 'result': u32, 'slots': 2,
                  'body': ['prim', u32, PRIM['U32.add']['id'], [['ref', u32, 0], ['ref', u32, 1]]]}]
    if scalar == 'Char':
        functions.append({'name': 'Char.from_u32', 'parameters': [u32], 'result': char, 'slots': 1,
                          'body': ['prim', char, PRIM['Char.from_u32']['id'], [['ref', u32, 0]]]})
    rows = [['branch', k, 1, 0, ['value', 0, i]] for i, k in enumerate(keys)]
    cls = len(functions)
    functions.append({'name': 'cls', 'parameters': [domain], 'result': 0, 'slots': 1,
                      'body': ['case', 0, 0, domain, 'keys', rows, ['default', ['value', 0, len(keys)]]]})
    literal = (lambda v: str(v)) if scalar == 'U32' else (lambda v: f"'\\u{{{v:X}}}'")
    calls_plan, calls_bend = [], []
    for v, fresh in zip(queries, computed):
        if fresh:
            a = v // 2
            plan = ['call', u32, 0, [['lit', u32, 'U32', a], ['lit', u32, 'U32', v - a]]]
            text = f'U32.add({a}, {v - a})'
            if scalar == 'Char':
                plan, text = ['call', char, 1, [plan]], f'Char.from_u32({text})'
        else:
            plan = ['lit', u32, 'U32', v] if scalar == 'U32' else ['lit', char, 'Char', v]
            text = literal(v)
        calls_plan.append(['call', 0, cls, [plan]])
        calls_bend.append(f'cls({text})')
    functions.append({'name': 'main', 'parameters': [], 'result': 1, 'slots': 0, 'body': chain_plan(calls_plan)})
    representation = {'U32': u32} if scalar == 'U32' else {'U32': u32, 'Char': char}
    plan = {'entry': 'book', 'representation': representation, 'types': types, 'functions': functions}
    arms = ''.join(f'    case {literal(k)}: R{i}{{}}\n' for i, k in enumerate(keys))
    source = ('import Base\n\n' + source + f"def cls(x: {'U32' if scalar == 'U32' else 'Char'}) -> Rs:\n  match x:\n" + arms +
              f'    case _: R{len(keys)}{{}}\n\ndef main() -> Ch:\n  {chain_bend(calls_bend)}\n')
    answers = [keys.index(q) if q in keys else len(keys) for q in queries]  # the arm of a key, else the Default's
    basis = (f"a {scalar} Case with keys {keys} answers R0.. for them and R{len(keys)} for any other word; queried at "
             f"{queries}, of which {sum(computed)} are computed")
    return item(name, 'keys', plan, source, tree=chain_tree(answers), basis=basis, **more)


def wide_program(name: str, k: int, nested: bool) -> dict:
    """A constructor of `k` fields (`k + 1` around two of them when nested), a different constructor of F at
    each position, printed by the Book's describe: its separators and its closing brace."""
    f_type = {'kind': 'data', 'name': 'F', 'constructors': [{'name': f'F{i}', 'fields': []} for i in range(10)]}
    inner = {'kind': 'data', 'name': f'W{k}', 'constructors': [{'name': f'W{k}', 'fields': [0] * k}]}
    types, top = [f_type, inner], 1
    fields = [((i * 7 + 1) % 10) for i in range(k)]
    plan = ['con', 1, 0, [['value', 0, f] for f in fields]]
    bend = f"W{k}{{{', '.join(f'F{f}{{}}' for f in fields)}}}"
    source = ('import Base\n\n' + bend_data('F', [(f'F{i}', []) for i in range(10)]) +
              bend_data(f'W{k}', [(f'W{k}', [(f'f{i}', 'F') for i in range(k)])]))
    if nested:
        outer = {'kind': 'data', 'name': f'V{k}', 'constructors': [{'name': f'V{k}', 'fields': [1] + [0] * (k - 1) + [1]}]}
        types.append(outer)
        top = 2
        flipped = fields[::-1]
        middle = [(i * 3 + 2) % 10 for i in range(k - 1)]
        parts_plan = [plan] + [['value', 0, m] for m in middle] + [['con', 1, 0, [['value', 0, f] for f in flipped]]]
        parts_bend = [bend] + [f'F{m}{{}}' for m in middle] + [f"W{k}{{{', '.join(f'F{f}{{}}' for f in flipped)}}}"]
        plan = ['con', 2, 0, parts_plan]
        bend = f"V{k}{{{', '.join(parts_bend)}}}"
        source += bend_data(f'V{k}', [(f'V{k}', [('g0', f'W{k}')] + [(f'g{i}', 'F') for i in range(1, k)] + [(f'g{k}', f'W{k}')])])
    main = {'name': 'main', 'parameters': [], 'result': top, 'slots': 0, 'body': plan}
    where = f'first and last inside a constructor of {k + 1}' if nested else 'the result itself'
    return item(name, 'wide', {'entry': 'book', 'types': types, 'functions': [main]},
                f"{source}def main() -> {types[top]['name']}:\n  {bend}\n", tree=bend.replace(' ', ''),
                basis=f'a constructor of {k} fields, {where}, a different constructor at each position')


def shape_types() -> tuple[list, str]:
    """Plan types 0..4 (`Rs`(4), `Ch`, `Flag`, `Shape`) and their Bend: Shape has two nullary constructors
    (A, B) and two with fields (C, D), one of each reached by an immediate or an Object."""
    plan, source = answer_types(4)
    plan.append({'kind': 'data', 'name': 'Flag', 'constructors': [{'name': 'Off', 'fields': []}, {'name': 'On', 'fields': []}]})
    plan.append({'kind': 'data', 'name': 'Shape', 'constructors': [
        {'name': 'A', 'fields': []}, {'name': 'B', 'fields': []}, {'name': 'C', 'fields': [2]}, {'name': 'D', 'fields': [2, 2]}]})
    source += (bend_data('Flag', [('Off', []), ('On', [])]) +
               bend_data('Shape', [('A', []), ('B', []), ('C', [('x', 'Flag')]), ('D', [('x', 'Flag'), ('y', 'Flag')])]))
    return plan, source


SHAPES = [(['value', 3, 0], 'A{}'), (['value', 3, 1], 'B{}'),
          (['con', 3, 2, [['value', 2, 1]]], 'C{On{}}'), (['con', 3, 3, [['value', 2, 0], ['value', 2, 1]]], 'D{Off{}, On{}}')]


def tag_program(name: str) -> dict:
    """Tag-mode Cases on Shape, every constructor queried: `dense` names each; `tail` defaults B and D (one
    nullary, reached by an immediate, and one with fields, an Object) and `head` defaults A and C."""
    types, source = shape_types()
    source = 'import Base\n\n' + source
    branch = lambda tag, fields, answer: ['branch', tag, 1, fields, ['value', 0, answer]]
    tables = {'dense': ([branch(0, 0, 0), branch(1, 0, 1), branch(2, 1, 2), branch(3, 2, 3)], None),
              'tail': ([branch(0, 0, 0), None, branch(2, 1, 1), None], ['default', ['value', 0, 2]]),
              'head': ([None, branch(1, 0, 0), None, branch(3, 2, 1)], ['default', ['value', 0, 2]])}
    bodies = {'dense': "    case A{}: R0{}\n    case B{}: R1{}\n    case C{+x}: R2{}\n    case D{+x, +y}: R3{}\n",
              'tail': "    case A{}: R0{}\n    case C{+x}: R1{}\n    case _: R2{}\n",
              'head': "    case B{}: R0{}\n    case D{+x, +y}: R1{}\n    case _: R2{}\n"}
    functions, calls_plan, calls_bend = [], [], []
    for i, (kind, (rows, default)) in enumerate(tables.items()):
        functions.append({'name': kind, 'parameters': [3], 'result': 0, 'slots': 1 + max(r[3] for r in rows if r),
                          'body': ['case', 0, 0, 3, 'tags', rows, default]})
        source += f'def {kind}(s: Shape) -> Rs:\n  match s:\n{bodies[kind]}\n'
        for plan, text in SHAPES:
            calls_plan.append(['call', 0, i, [plan]])
            calls_bend.append(f'{kind}({text})')
    functions.append({'name': 'main', 'parameters': [], 'result': 1, 'slots': 0, 'body': chain_plan(calls_plan)})
    answers = {'dense': [0, 1, 2, 3], 'tail': [0, 2, 1, 2], 'head': [2, 0, 2, 1]}  # per constructor A, B, C, D
    return item(name, 'tags', {'entry': 'book', 'types': types, 'functions': functions},
                f'{source}def main() -> Ch:\n  {chain_bend(calls_bend)}\n',
                tree=chain_tree([a for kind in tables for a in answers[kind]]),
                basis='Shape has A and B without fields, C and D with; each of three tag Cases (all named, and two whose '
                      'Default covers B and D, or A and C) is queried at A, B, C{On} and D{Off, On}, so a Default is reached by '
                      'an immediate and by an Object')


def ill_typed_program(name: str, cases: str) -> dict:
    """Section 6.1's inspection at the edge of the tag table, by literal review (the seed types every program).
    `pick(x: none)` cases on a word that `id` launders from another type; `cases` is one of
    - `at-count`: Tri's C{} (tag 2) at Flag, which has two constructors, without a Default;
    - `at-count-default`: the same with a Default over On;
    - `past-count`: Tri's C{} at Flag's one-constructor twin `Solo` (tag 2 is two past its end);
    - `fielded-branch`: Tri's C{} at Shape, whose tag 2 has a field, named by a Branch;
    - `fielded-default`: the same, named by the Default;
    - `nullary`: Tri's B{} at Shape's B, the control every check must admit."""
    types = [{'kind': 'data', 'name': 'Rs', 'constructors': [{'name': f'R{i}', 'fields': []} for i in range(3)]},
             {'kind': 'data', 'name': 'Tri', 'constructors': [{'name': n, 'fields': []} for n in 'ABC']},
             {'kind': 'data', 'name': 'Flag', 'constructors': [{'name': 'Off', 'fields': []}, {'name': 'On', 'fields': []}]},
             {'kind': 'data', 'name': 'Solo', 'constructors': [{'name': 'Solo', 'fields': []}]},
             {'kind': 'data', 'name': 'Shape', 'constructors': [{'name': 'A', 'fields': []}, {'name': 'B', 'fields': []},
                                                               {'name': 'C', 'fields': [2]}]}]
    branch = lambda tag, fields, answer: ['branch', tag, 1, fields, ['value', 0, answer]]
    scrutinee, rows, fallback, laundered = {
        'at-count': (2, [branch(0, 0, 0), branch(1, 0, 1)], None, 2),
        'at-count-default': (2, [branch(0, 0, 0), None], ['default', ['value', 0, 2]], 2),
        'past-count': (3, [branch(0, 0, 0)], None, 2),
        'fielded-branch': (4, [branch(0, 0, 0), branch(1, 0, 1), branch(2, 1, 2)], None, 2),
        'fielded-default': (4, [branch(0, 0, 0), branch(1, 0, 1), None], ['default', ['value', 0, 2]], 2),
        'nullary': (4, [branch(0, 0, 0), branch(1, 0, 1), branch(2, 1, 2)], None, 1)}[cases]
    depth = 1 + max(r[3] for r in rows if r)  # the parameter and the widest Branch's fields
    functions = [{'name': 'id', 'parameters': [None], 'result': None, 'slots': 1, 'body': ['ref', None, 0]},
                 {'name': 'pick', 'parameters': [None], 'result': 0, 'slots': depth,
                  'body': ['case', 0, 0, scrutinee, 'tags', rows, fallback]},
                 {'name': 'main', 'parameters': [], 'result': 0, 'slots': 0,
                  'body': ['call', 0, 1, [['call', None, 0, [['value', 1, laundered]]]]]}]
    plan = {'entry': 'book', 'types': types, 'functions': functions}
    basis = {'at-count': "pick cases on a word `id` launders from Tri's C{} (an immediate of tag 2) at Flag, which has 2 constructors and no Default: section 6.1 inspects it as ill-typed",
             'at-count-default': 'the same with a Default over On: the tag is still past the table',
             'past-count': "Tri's C{} at Solo, a one-constructor type: tag 2 is 2 past its end",
             'fielded-branch': "Tri's C{} at Shape, whose tag 2 has a field, named by a Branch: an immediate cannot name a constructor with fields",
             'fielded-default': 'the same, named by the Default',
             'nullary': "Tri's B{} at Shape's nullary B: the control, admitted"}[cases]
    if cases == 'nullary':
        return item(name, 'ill-typed', plan, tree='R1{}', basis=basis)
    return item(name, 'ill-typed', plan, refusal={'outcome': 'HostFailure', 'cause': 'image ill-typed'}, calls=3, basis=basis)  # main, id, pick


def big(values: list) -> tuple[list, list]:
    """Queries at each of `values` twice: as a literal, then computed (a fresh Big cell from 2^31)."""
    return values + values, [False] * len(values) + [True] * len(values)


def seeded() -> list:
    """The rows of vm/core/seeded.json. Each Case has 3 or 5 keys and is queried below the first key, at the
    first, between two keys, at a middle key, at the last and above it; the boundary rows put keys and
    scrutinees at 2^30, 2^31 and 2^32-1, one of them with 2^32-1 as its last key and one above its last."""
    top = 2 ** 32 - 1
    b3, b5 = [2 ** 30, 2 ** 31, top], [2 ** 30 - 1, 2 ** 30, 2 ** 31 - 1, 2 ** 31, top - 1]
    q3 = [2 ** 30 - 1, 2 ** 30, 2 ** 30 + 1, 2 ** 31 - 1, 2 ** 31, 2 ** 31 + 1, top - 1, top]
    q5 = [2 ** 30 - 2, 2 ** 30 - 1, 2 ** 30, 2 ** 30 + 1, 2 ** 31 - 2, 2 ** 31 - 1, 2 ** 31, 2 ** 31 + 1, top - 2, top - 1, top]
    chars3 = [0, 0x41, 0x42, 0x800, 0x801, 0x1F600, 0x1F601, 0x10FFFF, 0xD800, 0x110000, top]
    chars5 = [0, 0x9, 0xA, 0x20, 0x21, 0x7F, 0x80, 0x81, 0x7FF, 0x800, 0x10FFFF, 0xDFFF]
    fresh = lambda qs: [i % 2 == 1 or not scalar(q) for i, q in enumerate(qs)]
    rows = [key_program('keys-u32-3', 'U32', [10, 200, 30000], [0, 10, 11, 200, 201, 30000, 30001, top]),
            key_program('keys-u32-5', 'U32', [10, 200, 3000, 40000, 500000],
                        [0, 10, 11, 200, 201, 3000, 3001, 40000, 40001, 500000, 500001, top]),
            key_program('keys-u32-big-3', 'U32', b3, *big(q3)[:1], computed=big(q3)[1]),
            key_program('keys-u32-big-5', 'U32', b5, *big(q5)[:1], computed=big(q5)[1]),
            key_program('keys-char-3', 'Char', [0x41, 0x800, 0x1F600], chars3, computed=fresh(chars3)),
            key_program('keys-char-5', 'Char', [0x9, 0x20, 0x7F, 0x80, 0x7FF], chars5, computed=fresh(chars5))]
    nonscalar = [0xD800, 0xDFFF, 0x110000, top]  # the seed cannot spell these Char patterns: literal review
    plan_only = key_program('keys-char-nonscalar', 'Char', nonscalar,
                            [0, 0xD7FF, 0xD800, 0xD801, 0xDFFF, 0xE000, 0x10FFFF, 0x110000, 0x110001, top - 1, top],
                            computed=[True] * 11)
    plan_only['source'] = None
    rows.append(plan_only)
    rows += [wide_program(f'wide-{k}-{shape}', k, shape == 'nested') for k in (3, 5, 9) for shape in ('flat', 'nested')]
    rows.append(tag_program('tags-shape'))
    return rows


def ill_scalar_action() -> dict:
    """U32.is_eq(id(IO.print("a")), 0): the prim reads an Action (class 3, built and never applied) at U32. Section 6
    inspects a scalar as an immediate or a Big cell, so it is ill-typed after main, print, id and is_eq (4 entries)."""
    types = out_types() + [{'kind': 'data', 'name': 'Bool', 'constructors': [{'name': 'False', 'fields': []}, {'name': 'True', 'fields': []}]}]
    functions = [{'name': 'IO.print', 'parameters': [3], 'result': 7, 'slots': 1, 'body': ['foreign', 7, 1, [['ref', 3, 0]]]},
                 {'name': 'id', 'parameters': [None], 'result': None, 'slots': 1, 'body': ['ref', None, 0]},
                 {'name': 'U32.is_eq', 'parameters': [1, 1], 'result': 8, 'slots': 2,
                  'body': ['prim', 8, PRIM['U32.is_eq']['id'], [['ref', 1, 0], ['ref', 1, 1]]]},
                 {'name': 'main', 'parameters': [], 'result': 8, 'slots': 0, 'body': ['call', 8, 2, [
                     ['call', None, 1, [['call', 7, 0, [['lit', 3, 'String', [97]]]]]], ['lit', 1, 'U32', 0]]]}]
    plan = {'entry': 'book', 'representation': {**OUT_REPRESENTATION, 'Bool': 8}, 'types': types, 'functions': functions}
    return item('ill-scalar-action', 'ill-typed', plan, refusal={'outcome': 'HostFailure', 'cause': 'image ill-typed'}, calls=4,
                basis='a prim operand that is an Action (class 3) is ill-typed at U32: a class check that let class 3 pass as a Big cell would compute')


def ill_describe_at_count() -> dict:
    """A Book whose result is Tri's C{} (an immediate of tag 2) laundered to Flag, which has two constructors: describe
    inspects the result, so it is ill-typed after main, id and cast (3 entries). Solo follows Flag's constructors, so
    a tag range that let 2 through would read Solo's nullary record and print `Solo{}`."""
    types = [{'kind': 'data', 'name': 'Tri', 'constructors': [{'name': n, 'fields': []} for n in 'ABC']},
             {'kind': 'data', 'name': 'Flag', 'constructors': [{'name': 'Off', 'fields': []}, {'name': 'On', 'fields': []}]},
             {'kind': 'data', 'name': 'Solo', 'constructors': [{'name': 'Solo', 'fields': []}]}]
    functions = [{'name': 'id', 'parameters': [None], 'result': None, 'slots': 1, 'body': ['ref', None, 0]},
                 {'name': 'cast', 'parameters': [None], 'result': 1, 'slots': 1, 'body': ['ref', None, 0]},
                 {'name': 'main', 'parameters': [], 'result': 1, 'slots': 0, 'body': ['call', 1, 1, [['call', None, 0, [['value', 0, 2]]]]]}]
    return item('ill-describe-at-count', 'ill-typed', {'entry': 'book', 'types': types, 'functions': functions},
                refusal={'outcome': 'HostFailure', 'cause': 'image ill-typed'}, calls=3,
                basis="a Book's result word is read at its type: Tri's C{} (tag 2) at Flag (2 constructors) is ill-typed, not the next record's name")


def ill_typed() -> list:
    return [*(ill_typed_program(f'ill-{name}', name) for name in
              ('at-count', 'at-count-default', 'past-count', 'fielded-branch', 'fielded-default', 'nullary')),
            ill_scalar_action(), ill_describe_at_count()]


def display_bound(name: str, n: int) -> dict:
    """P{Nat n, Q{On, Off}}: section 8 counts one visit per constructor and n + 1 for a Nat, so 1 + (n + 1) + 3 = n + 5
    visits. n = 1,048,571 ends exactly at the bound of 1,048,576 and prints; one more is Exhausted (display). The
    constructors after the Nat are the ones whose visits an undercounted or overcounted Nat would shift."""
    types = [{'kind': 'data', 'name': 'Flag', 'constructors': [{'name': 'Off', 'fields': []}, {'name': 'On', 'fields': []}]},
             {'kind': 'data', 'name': 'Nat', 'constructors': [{'name': 'Zero', 'fields': []}, {'name': 'Succ', 'fields': [1]}]},
             {'kind': 'data', 'name': 'Q', 'constructors': [{'name': 'Q', 'fields': [0, 0]}]},
             {'kind': 'data', 'name': 'P', 'constructors': [{'name': 'P', 'fields': [1, 2]}]}]
    body = ['con', 3, 0, [['lit', 1, 'Nat', n], ['con', 2, 0, [['value', 0, 1], ['value', 0, 0]]]]]
    plan = {'entry': 'book', 'representation': {'Nat': 1}, 'types': types,
            'functions': [{'name': 'main', 'parameters': [], 'result': 3, 'slots': 0, 'body': body}]}
    return item(name, 'display', plan, basis=f'P{{Nat {n}, Q{{On, Off}}}} is {n + 5:,} visits against the bound of 1,048,576')


def display_items() -> list:
    return [display_bound('display-at-bound', 1_048_571), display_bound('display-over-bound', 1_048_572)]


def random_keys(index: int, seed: int) -> dict:
    """A random U32 or Char Case, keyed from boundary values: every key, its neighbours, and a few others."""
    rng = Rng(seed + 2, index)
    scalar_kind = 'Char' if index % 3 == 2 else 'U32'
    pool = ([0, 9, 10, 32, 0x41, 0x61, 0x7e, 0x7f, 0x80, 0x7ff, 0x800, 0xd7ff, 0xe000, 0xfffd, 0xffff, 0x10000, 0x1f600, 0x10ffff]
            if scalar_kind == 'Char' else
            [0, 1, 2, 3, 127, 128, 255, 256, 65535, 65536, 2 ** 24, 2 ** 30 - 1, 2 ** 30, 2 ** 30 + 1, 2 ** 31 - 2, 2 ** 31 - 1,
             2 ** 31, 2 ** 31 + 1, 3 * 2 ** 30, 2 ** 32 - 3, 2 ** 32 - 2, 2 ** 32 - 1, 12345678, 3000000000, 4000000000])
    keys = sorted({rng.choice(pool) for _ in range(rng.randrange(1, 9))})
    around = sorted({q for k in keys for q in (k - 1, k, k + 1) if 0 <= q <= M32 and (scalar_kind == 'U32' or scalar(q))})
    queries = rng.sample(around, min(len(around), 10)) + [rng.choice(pool) for _ in range(2)]
    return key_program(f'keys-random-{index}', scalar_kind, keys, queries, computed=[rng.random() < 0.5 for _ in queries])
