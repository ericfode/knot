#!/usr/bin/env python3
"""A wide synthetic book whose image passes 4 MiB, with the plan it must encode to.

The source and the plan are generated together from one description, so the expected image comes from
vm/serializer.py and this file, never from Knot's checker or encoder. The book is wide, not deep:
`serializer.decode` and the reference lowering recurse on nesting, and Bun's stack is bounded.
FUNCTIONS make-functions each hold LETS affine `Row` lets and a final `Row`, every one a 256-field
constructor over the reusable parameter, so node offsets pass 2^20 words.
"""
from __future__ import annotations

FIELDS, FUNCTIONS, LETS = 256, 250, 3


def row(parameter: str) -> str:
    return 'Row{' + ','.join([parameter] * FIELDS) + '}'


def source() -> str:
    lines = ['type Flag is Data:', '  Off{}', '  On{}', '', 'type Row is Data:',
             '  Row{' + ', '.join(f'f{i}: Flag' for i in range(FIELDS)) + '}', '']
    for k in range(FUNCTIONS):
        lines.append(f'def make{k}(+x: Flag) -> Row:')
        lines += [f'  y{i} : Row = {row("x")}' for i in range(LETS)]
        lines += [f'  {row("x")}', '']
    lines += ['def main() -> Flag:', '  On{}', '']
    return '\n'.join(lines)


def plan() -> dict:
    """flag = type 0, row = type 1; a live `x` is slot 0, each let takes the next slot."""
    construct = ['con', 1, 0, [['ref', 0, 0]] * FIELDS]
    body = construct
    for i in reversed(range(LETS)):
        body = ['let', 1, 1 + i, construct, body]
    functions = [{'name': f'make{k}', 'parameters': [0], 'result': 1, 'slots': 1 + LETS, 'body': body}
                 for k in range(FUNCTIONS)]
    functions.append({'name': 'main', 'parameters': [], 'result': 0, 'slots': 0, 'body': ['value', 0, 1]})
    return {'entry': 'book', 'types': [
        {'kind': 'data', 'name': 'Flag', 'constructors': [{'name': 'Off', 'fields': []}, {'name': 'On', 'fields': []}]},
        {'kind': 'data', 'name': 'Row', 'constructors': [{'name': 'Row', 'fields': [0] * FIELDS}]}],
        'functions': functions}
