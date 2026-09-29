#!/usr/bin/env python3
"""The canonical text of a decoded plan, as tests/compiler-image/image-cli.bend prints it.

`render(plan)` reads a plan that vm/serializer.py decoded; the Bend driver prints the plan that
`image.decode` produced. Two independent decoders agreeing on this text is the decode evidence.
"""
from __future__ import annotations

NONE = 0xFFFFFFFF
KINDS = ('U32', 'Nat', 'Char', 'String')
MODES = ('tags', 'keys')
REPRESENTATIONS = ('Nat', 'U32', 'Char', 'String', 'Bool', 'Cmp', 'Unit', 'List', 'Result', 'Sigma', 'IO.OP', 'File')


def opt(value) -> int:
    return NONE if value is None else value


def numbers(values) -> str:
    return ';'.join(str(v) for v in values)


def node(n) -> str:
    op = n[0]
    t = opt(n[1]) if op not in ('branch', 'default') else None
    if op == 'lit':
        data = n[3] if n[2] == 'String' else [n[3]]
        return f'lit[{t},{KINDS.index(n[2])},{numbers(data)}]'
    if op in ('value', 'ref'):
        return f'{op}[{t},{n[2]}]'
    if op in ('prim', 'con', 'call', 'foreign'):
        return f'{op}[{t},{n[2]}]({";".join(node(k) for k in n[3])})'
    if op == 'let':
        return f'let[{t},{n[2]}]({node(n[3])};{node(n[4])})'
    if op == 'case':
        _, _, slot, scrutinee, mode, rows, default = n
        shown = ';'.join('-' if r is None else branch(r) for r in rows)
        fallback = '-' if default is None else node(default[1])
        return f'case[{t},{slot},{opt(scrutinee)},{MODES.index(mode)}]({shown}|{fallback})'
    if op == 'closure':
        return f'closure[{t},{n[2]},{n[3]},{numbers(n[4])}]({node(n[5])})'
    if op == 'invoke':
        return f'invoke[{t}]({";".join([node(n[2]), *(node(a) for a in n[3])])})'
    raise AssertionError(f'render: {op}')


def branch(r) -> str:
    return f'branch[{r[1]},{r[2]},{r[3]}]({node(r[4])})'


def shape(index: int, t: dict) -> str:
    if t['kind'] == 'data':
        constructors = ' '.join(f'{c["name"]}({numbers(opt(f) for f in c["fields"])})' for c in t['constructors'])
        return f'type {index} algebraic {t["name"]} {constructors}'
    if t['kind'] == 'opaque':
        return f'type {index} opaque {t["name"]}'
    kind = 'arrow' if t['kind'] == 'arrow' else 'erased'
    return f'type {index} {kind} {opt(t["domain"])} {opt(t["result"])}'


def render(plan: dict) -> str:
    """What `image-cli decode` prints, less the newline that IO.print adds."""
    rep = plan.get('representation', {})
    lines = [f'entry {("book", "program").index(plan["entry"])}',
             'representation ' + numbers(opt(rep.get(r)) for r in REPRESENTATIONS)]
    lines += [shape(i, t) for i, t in enumerate(plan['types'])]
    for i, f in enumerate(plan['functions']):
        lines.append(f'function {i} {f["name"]} ({numbers(opt(p) for p in f["parameters"])}) '
                     f'{opt(f["result"])} {f["slots"]} {node(f["body"])}')
    return '\n'.join(lines) + '\n'
