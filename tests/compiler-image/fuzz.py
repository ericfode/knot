#!/usr/bin/env python3
"""A seeded generator of small programs in the checked profile of this base, for the image gate's fuzz stage.

Every type is Data. Constructors carry live, erased (`-`) and reusable (`+`) fields, functions take reusable and erased
parameters, and bodies nest matches on parameters and bound fields (arms in any order), erased and reusable lets, and
calls of earlier functions, with erased arguments filled by the smallest closed value of their type. `check-cli`
decides which programs are accepted; the gate holds each accepted one to the independent reference's bytes and to
`decode(encode(b)) = erase_tokens(b)`. The programs are a function of the seed alone.
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
