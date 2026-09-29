#!/usr/bin/env python3
"""Systematic mutants of vm/vm.wat's semantic functions, for the study of what the gate's rows kill.

A mutant changes one token of one line: a comparison or an arithmetic or bitwise operator swapped for
its neighbour, or a small `i32.const` moved by one. The functions are the ones that decide what a
program computes and what a Book or a Program writes: the prims and their helpers, Case selection, the
completion of a gathered node, describe and the UTF-8 writer. The loader, validator, frames and memory
are not among them; the limit, refusal, ceiling and growth rows of the gate cover those.

`python3 vm/check-core.py --study` runs every mutant against the gate's own rows (the same jobs and the
same `observed_wrong`, so a kill here is a kill there) and writes vm/receipts/study.json.
"""
from __future__ import annotations

import re

FUNCTIONS = ['$prim', '$select', '$complete', '$show', '$seq', '$append', '$reverse', '$scon', '$nat', '$cmp',
             '$scalar', '$num', '$tagof', '$ctor', '$describe', '$emitdec', '$utf8out', '$slen', '$scell',
             '$spell', '$room']
SWAPS = [('i32.lt_u', 'i32.le_u'), ('i32.le_u', 'i32.lt_u'), ('i32.gt_u', 'i32.ge_u'), ('i32.ge_u', 'i32.gt_u'),
         ('i32.eq ', 'i32.ne '), ('i32.ne ', 'i32.eq '), ('i32.add', 'i32.sub'), ('i32.sub', 'i32.add'),
         ('i64.lt_u', 'i64.le_u'), ('i64.gt_u', 'i64.ge_u'), ('i32.shr_u', 'i32.shl'), ('i32.and', 'i32.or')]


def ranges(lines: list) -> dict:
    """Each function's [first, end) line indices."""
    starts = [(i, m.group(1)) for i, line in enumerate(lines) if (m := re.match(r'\s*\(func (\$\w+)', line))]
    return {name: (i, starts[k + 1][0] if k + 1 < len(starts) else len(lines)) for k, (i, name) in enumerate(starts)}


def mutants(text: str) -> list:
    """(name, line index, column, old, new) for every mutant, in a stable order: by function, line, swap, then constant.
    The name is `function:line:change@column` (lines count from 1)."""
    lines = text.split('\n')
    where = ranges(lines)
    out = []
    for name in FUNCTIONS:
        first, end = where[name]
        for li in range(first, end):
            code = lines[li].split(';;')[0]
            if not code.strip():
                continue
            for old, new in SWAPS:
                for m in re.finditer(re.escape(old), code):
                    out.append((f'{name}:{li + 1}:{old.strip()}->{new.strip()}@{m.start()}', li, m.start(), old, new))
            for m in re.finditer(r'\(i32\.const (\d+)\)', code):
                k = int(m.group(1))
                if 1 <= k <= 200 and 'offset' not in code[:m.start()][-12:]:
                    for moved in (k + 1, k - 1):
                        out.append((f'{name}:{li + 1}:const {k}->{moved}@{m.start()}', li, m.start(), m.group(0), f'(i32.const {moved})'))
    return out


def apply(text: str, mutant: tuple) -> str:
    """`text` with the mutant's one token changed."""
    _, li, col, old, new = mutant
    lines = text.split('\n')
    assert lines[li][col:col + len(old)] == old, (mutant, lines[li])
    lines[li] = lines[li][:col] + new + lines[li][col + len(old):]
    return '\n'.join(lines)


# Survivors of the gate's rows, each with the reason no observation can tell it from vm.wat.
EQUIVALENT: dict[str, str] = {}
