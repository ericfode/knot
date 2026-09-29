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


# The survivors of the gate's rows, each with why no run can tell it from vm/vm.wat (CORE.md, "Mutant study"). A name
# carries its line, so an edit to vm.wat that moves a survivor, or kills one, shows as an unexplained or a stale entry.
_WHY = [
    ('Nat.sub at x = y is 0 by either arm of the select', ['$prim:2051:i32.gt_u->i32.ge_u@39']),
    ('the key differs from the word at this point (equality returned above), so `<` and `<=` agree', ['$select:2199:i32.lt_u->i32.le_u@17']),
    ('a flag that is only tested for truth', ['$select:2213:const 1->2@34', '$complete:2125:const 1->2@25']),
    ("the class mask lets a Closure past the class test, but its word at offset 8 is a node's word offset, which exceeds every "
     "type index (each type record is 5 words and precedes the nodes), so the type test refuses it as before",
     ['$select:2216:const 7->6@70', '$tagof:1882:const 7->6@60', '$scell:1898:const 7->6@60']),
    ("the class test reads only the payload's parity: a wrong-class word passes it, then the type word and the tag word, only "
     "if it is an Action whose foreign id is the String type index and whose operand is the word 1; the mutant then reads "
     "past the Action's 16-byte cell, and what follows it decides the outcome (`ill-string-action` builds that Action and "
     "still refuses by the words it finds, not by its class)", ['$scell:1898:const 7->8@60']),
    ('which operands a prim or a completion drops is unobservable while `$drop` is empty (CORE.md choice 1); vm-rc makes it observable',
     ['$complete:2134:i32.lt_u->i32.le_u@21', '$complete:2134:i32.gt_u->i32.ge_u@63', '$complete:2134:const 16->17@46',
      '$complete:2134:const 16->15@46', '$complete:2134:const 19->20@88', '$complete:2134:const 19->18@88',
      '$complete:2137:i32.eq->i32.ne@26', '$complete:2137:i32.ne->i32.eq@66', '$complete:2137:i32.and->i32.or@17',
      '$complete:2137:const 2->3@50', '$complete:2137:const 2->1@50', '$complete:2137:const 35->36@89', '$complete:2137:const 35->34@89']),
    ("binds one field past the Branch's: it reads a word past the Object and writes the slot after the Branch's, padding of "
     "the Activation or the reference count of the next cell, both unread until vm-rc", ['$select:2248:i32.ge_u->i32.gt_u@31']),
    ("the reference count of an append cell, unread until vm-rc",
     ['$append:1967:const 1->2@34', '$append:1967:const 1->0@34']),
    ("copies 4 bytes more for each operand, into padding or free heap above the bump pointer, which `$alloc` zeroes when it "
     "reuses it; it differs only where a copy leaves memory, an Object of three fields or an Action ending exactly at 4 GiB, "
     "which no ceiling row builds", ['$complete:2163:const 2->3@104', '$complete:2170:const 2->3@100']),
    ("clears half of the append block first: every word a cell reads is then written, so only padding words differ",
     ['$append:1963:const 5->4@73']),
    ("the payload count in the header of an Action, which stays a 16-byte cell for 0 to 2 words; only the state audit reads it",
     ['$complete:2168:i32.add->i32.sub@32', '$complete:2168:const 1->0@57']),
    ("the payload count in the header of a String or Big cell, whose size class it leaves unchanged",
     ['$scon:1918:const 4->5@31', '$scon:1918:const 4->3@31', '$scalar:1844:const 1->2@35', '$scalar:1844:const 1->0@35']),
    ("stores the Foreign node's operand count where the Action's foreign id belongs: for IO.print, the only foreign vm-core "
     "admits (choice 2), both are 1", ['$complete:2169:const 3->4@72']),
    ("the mode register after a finished run: `$run` returns at once (vm.wat line 2459) and no observation reads the register",
     ['$describe:2706:const 3->4@22', '$describe:2706:const 3->2@22']),
]
EQUIVALENT: dict[str, str] = {m: why for why, names in _WHY for m in names}
assert sum(len(names) for _, names in _WHY) == len(EQUIVALENT), 'a survivor is explained twice'
