#!/usr/bin/env python3
"""Seeded generators for the image gate's fuzz stages.

`program(seed)`: a small program in the checked profile of this base. Every type is Data. Constructors carry live,
erased (`-`) and reusable (`+`) fields, functions take reusable and erased parameters, and bodies nest matches on
parameters and bound fields (arms in any order), erased and reusable lets, and calls of earlier functions, with erased
arguments filled by the smallest closed value of their type. `check-cli` decides which programs are accepted; the gate
holds each accepted one to the independent reference's bytes and to `decode(encode(b)) = erase_tokens(b)`.

`plan(seed)`: a random record plan in the reference codec's format (vm/serializer.py), with every node form of SPEC
section 3, both Case modes, defaults, constants of each kind, closures, names that repeat, and representation words. This
base's core produces few of these forms, so the merge wave's encoders meet them first here: the gate encodes each with the
reference, and the Bend decoder must read it as the reference does and the Bend layout must write it back byte for byte.

Both are a function of the seed alone.
"""
import random
import re


class Type:
    def __init__(self, name, constructors):
        self.name = name
        self.constructors = constructors  # [(name, [(field name, type, quantity)])]; quantity is '', '-' or '+'


class Generator:
    def __init__(self, seed):
        self.r = random.Random(seed)
        self.types = []
        self.functions = []  # (name, [(parameter, type, quantity)], result type)
        self.counter = 0

    def fresh(self, base):
        self.counter += 1
        return f'{base}{self.counter}'

    def make_types(self):
        self.types = [Type('Flag', [('Off', []), ('On', [])])]
        for i in range(self.r.randint(1, 3)):
            constructors = []
            for j in range(self.r.randint(1, 3)):
                fields = [(f'f{i}{j}{k}', self.r.choice(self.types), self.r.choice(['', '', '', '-', '+']))
                          for k in range(self.r.randint(0, 3))]
                constructors.append((f'C{i}{j}', fields))
            self.types.append(Type(f'T{i}', constructors))

    def type_source(self, t):
        lines = [f'type {t.name} is Data:']
        for name, fields in t.constructors:
            lines.append(f'  {name}{{{", ".join(f"{q}{n}: {ft.name}" for n, ft, q in fields)}}}')
        return '\n'.join(lines)

    # The smallest closed expression of a type: the constructor with the fewest fields, defaults inside.
    def default_expr(self, t):
        return self.construct(min(t.constructors, key=lambda c: (len(c[1]), c[0])), lambda ft: self.default_expr(ft), lambda ft: self.default_expr(ft))

    def construct(self, constructor, live, erased):
        name, fields = constructor
        return f'{name}{{{",".join((erased if q == "-" else live)(ft) for n, ft, q in fields)}}}'

    def expr(self, scope, t, depth):
        options = [('var', v) for v, vt, live in scope if vt is t and live] * 2
        options.append(('construct', None))
        if depth > 0:
            options += [('call', f) for f in self.functions if f[2] is t]
        kind, payload = self.r.choice(options)
        if kind == 'var':
            return payload
        if kind == 'construct':
            constructor = self.r.choice(t.constructors) if depth > 0 else min(t.constructors, key=lambda c: (len(c[1]), c[0]))
            return self.construct(constructor, lambda ft: self.expr(scope, ft, depth - 1), lambda ft: self.default_expr(ft))
        name, params, result = payload
        return f'{name}({",".join(self.default_expr(pt) if q == "-" else self.expr(scope, pt, depth - 1) for pn, pt, q in params)})'

    # scope: [(name, type, live)]; matchable: [(order, name, type)]. A match may use a later binder than the one it
    # matched; a let closes every outer binder to matching.
    def body(self, scope, matchable, t, depth, indent):
        pad = '  ' * indent
        roll = self.r.random()
        if depth <= 0 or roll < 0.25:
            return f'{pad}{self.expr(scope, t, 2)}'
        if roll < 0.7 and matchable:
            order, name, mt = self.r.choice(matchable)
            later = [m for m in matchable if m[0] > order]
            arms = list(mt.constructors)
            self.r.shuffle(arms)
            out = [f'{pad}match {name}:']
            for cname, fields in arms:
                names = [self.fresh('v') for _ in fields]
                bound = [(n, ft, q != '-') for n, (fn, ft, q) in zip(names, fields)]
                base = max([m[0] for m in matchable] + [0]) + 1
                fresh = later + [(base + i, n, ft) for i, (n, (fn, ft, q)) in enumerate(zip(names, fields)) if q != '-']
                out.append(f'{pad}  case {cname}{{{",".join(names)}}}:')
                out.append(self.body(scope + bound, fresh, t, depth - 1, indent + 2))
            return '\n'.join(out)
        lt = self.r.choice(self.types)
        q = self.r.choice(['+', '+', '-'])
        name = self.fresh('y')
        head = f'{pad}{q}{name} : {lt.name} = {self.expr(scope, lt, 2)}'
        return f'{head}\n{self.body(scope + [(name, lt, q != "-")], [], t, depth - 1, indent)}'

    def program(self):
        self.make_types()
        out = [self.type_source(t) for t in self.types]
        for i in range(self.r.randint(1, 4)):
            params = [(f'p{i}{j}', self.r.choice(self.types), self.r.choice(['+', '+', '+', '-'])) for j in range(self.r.randint(0, 3))]
            result = self.r.choice(self.types)
            scope = [(pn, pt, q != '-') for pn, pt, q in params]
            matchable = [(k, pn, pt) for k, (pn, pt, q) in enumerate(params) if q != '-']
            head = f'def fn{i}({", ".join(q + pn + ": " + pt.name for pn, pt, q in params)}) -> {result.name}:'
            out.append(head + '\n' + self.body(scope, matchable, result, 3, 1))
            self.functions.append((f'fn{i}', params, result))
        result = self.r.choice(self.types)
        out.append(f'def main() -> {result.name}:\n  {self.expr([], result, 3)}')
        return '\n'.join(out) + '\n'


def program(seed: int) -> str:
    return Generator(seed).program()


def features(source: str) -> dict:
    """What a program exercises in the encoder, counted from its text."""
    counts = dict.fromkeys(('functions', 'erased_fields', 'erased_parameters', 'lets', 'erased_lets', 'matches', 'nested_matches'), 0)
    in_type = False
    for line in source.splitlines():
        stripped = line.strip()
        if line.startswith('type '):
            in_type = True
        elif line.startswith('def '):
            in_type = False
            counts['functions'] += 1
            counts['erased_parameters'] += len(re.findall(r'[(,] ?-\w+: ', line.split(') ->')[0]))
        elif in_type:
            counts['erased_fields'] += len(re.findall(r'[{,] ?-\w+: ', line))
        elif re.match(r'[+-]\w+ : ', stripped):
            counts['lets'] += 1
            counts['erased_lets'] += stripped.startswith('-')
        elif stripped.startswith('match '):
            counts['matches'] += 1
            counts['nested_matches'] += len(line) - len(line.lstrip()) > 2
    return counts


NAMES = ('a', 'b', 'Flag', 'Off', 'On', 'main', 'f', 'g', 'x1', 'List.map', 'U32', 'Nat', 'longer_name_of_some_kind', 'ab', 'abc', 'abcd', 'abcde')
REPRESENTATIONS = ('Nat', 'U32', 'Char', 'String', 'Bool', 'Cmp', 'Unit', 'List', 'Result', 'Sigma', 'IO.OP', 'File')


def plan(seed: int) -> dict:
    r = random.Random(seed)
    count = r.randint(1, 5)
    types = []
    for i in range(count):
        kind = 'data' if i == 0 else r.choice(['data', 'data', 'data', 'arrow', 'erased-arrow', 'opaque'])
        if kind == 'data':
            constructors = [{'name': r.choice(NAMES), 'fields': [None if r.random() < 0.15 else r.randrange(count) for _ in range(r.randint(0, 3))]}
                            for _ in range(r.randint(0, 3))]
            types.append({'kind': 'data', 'name': r.choice(NAMES), 'constructors': constructors})
        elif kind == 'opaque':
            types.append({'kind': 'opaque', 'name': r.choice(NAMES)})
        else:
            types.append({'kind': kind, 'domain': None if r.random() < 0.2 else r.randrange(count), 'result': None if r.random() < 0.2 else r.randrange(count)})

    def type_id():
        return None if r.random() < 0.1 else r.randrange(count)

    def node(depth):
        if depth <= 0:
            return r.choice([lambda: ['value', type_id(), r.randrange(4)], lambda: ['ref', type_id(), r.randrange(6)],
                             lambda: ['lit', type_id(), 'U32', r.randrange(2**32)]])()
        form = r.choice(['lit', 'value', 'ref', 'prim', 'con', 'call', 'foreign', 'let', 'case', 'case', 'closure', 'invoke'])
        if form == 'lit':
            kind = r.choice(['U32', 'Nat', 'Char', 'String'])
            value = ([r.randrange(2 ** r.choice([7, 11, 16, 21])) for _ in range(r.randint(0, 4))] if kind == 'String'
                     else r.randrange(2 ** 21) if kind == 'Char' else r.randrange(300) if kind == 'Nat' else r.randrange(2 ** 32))
            return ['lit', type_id(), kind, value]
        if form == 'value':
            return ['value', type_id(), r.randrange(5)]
        if form == 'ref':
            return ['ref', type_id(), r.randrange(8)]
        if form in ('prim', 'con', 'call', 'foreign'):
            return [form, type_id(), r.randrange(30), [node(depth - 1) for _ in range(r.randint(0, 3))]]
        if form == 'let':
            return ['let', type_id(), r.randrange(8), node(depth - 1), node(depth - 1)]
        if form == 'case':
            mode = r.choice(['tags', 'keys'])
            if mode == 'tags':
                rows = [None if r.random() < 0.25 else ['branch', i, r.randrange(6), r.randrange(4), node(depth - 1)] for i in range(r.randint(0, 4))]
            else:
                rows = [['branch', key, r.randrange(6), r.randrange(4), node(depth - 1)] for key in sorted(r.sample(range(50), r.randint(0, 4)))]
            fallback = ['default', node(depth - 1)] if r.random() < 0.5 else None
            return ['case', type_id(), r.randrange(6), None if r.random() < 0.1 else r.randrange(count), mode, rows, fallback]
        if form == 'closure':
            return ['closure', type_id(), r.randrange(4), r.randrange(8), sorted(r.sample(range(8), r.randint(0, 3))), node(depth - 1)]
        return ['invoke', type_id(), node(depth - 1), [node(depth - 1) for _ in range(r.randint(0, 3))]]

    functions = [{'name': r.choice(NAMES + ('main',)), 'parameters': [type_id() for _ in range(r.randint(0, 4))], 'result': type_id(),
                  'slots': r.randrange(10), 'body': node(r.randint(0, 4))} for _ in range(r.randint(1, 4))]
    result = {'entry': r.choice(['book', 'program']), 'types': types, 'functions': functions}
    if r.random() < 0.4:
        result['representation'] = {name: r.randrange(count) for name in r.sample(REPRESENTATIONS, r.randint(1, 4))}
    return result


def forms(plan: dict) -> set:
    """The node forms a plan uses."""
    found = set()

    def walk(n):
        found.add(n[0])
        if n[0] in ('prim', 'con', 'call', 'foreign'):
            for k in n[3]:
                walk(k)
        elif n[0] == 'let':
            walk(n[3]); walk(n[4])
        elif n[0] == 'case':
            for row in n[5]:
                if row is not None:
                    walk(row)
            if n[6] is not None:
                walk(n[6])
        elif n[0] in ('branch', 'default'):
            walk(n[-1])
        elif n[0] == 'closure':
            walk(n[5])
        elif n[0] == 'invoke':
            walk(n[2])
            for a in n[3]:
                walk(a)
    for f in plan['functions']:
        walk(f['body'])
    return found
