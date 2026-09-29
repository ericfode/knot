#!/usr/bin/env python3
"""Systematic mutants of vm/vm.wat's semantic functions, for the study of what the gate's rows kill.

A mutant changes one token of one line: a comparison or an arithmetic or bitwise operator swapped for
its neighbour, or a small `i32.const` moved by one. The functions are the ones that decide what a
program computes and what a Book or a Program writes: the prims and their helpers, Case selection, the
completion of a gathered node, describe and the UTF-8 writer, and the two that hold the validator's scope
tables (`$setscope` and `$holdscope`, whose depth no image size bounds). Round 7 added what D22 to D24 and
SPEC 6.3 put in the machine (a request, the operands of a completion, the room checks, Enter, Top's loop
and the final IO.OP) and the two of the describe domain and the invocation (`$describable`, `$entry`). The
rest of the loader and the validator, the frames and the memory are not among them; the limit, refusal,
ceiling and growth rows of the gate cover those.

`python3 vm/check-core.py --study` runs every mutant against the gate's own rows (the same jobs and the
same `observed_wrong`, so a kill here is a kill there) and writes vm/receipts/study.json.
"""
from __future__ import annotations

import re

FUNCTIONS = ['$prim', '$select', '$complete', '$show', '$seq', '$append', '$reverse', '$scon', '$nat', '$cmp',
             '$scalar', '$num', '$tagof', '$ctor', '$describe', '$emitdec', '$utf8out', '$slen', '$scell',
             '$spell', '$room', '$setscope', '$holdscope',
             '$request', '$opnd', '$pop', '$fit', '$spare', '$unscoped', '$tail', '$enter', '$serve', '$finish', '$describable', '$entry']
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
    ('Nat.sub at x = y is 0 by either arm of the select', ['$prim:2072:i32.gt_u->i32.ge_u@39']),
    ('the key differs from the word at this point (equality returned above), so `<` and `<=` agree', ['$select:2220:i32.lt_u->i32.le_u@17']),
    ('a flag that is only tested for truth', ['$select:2234:const 1->2@34', '$complete:2146:const 1->2@25']),
    ("the class mask lets a Closure past the class test, but its word at offset 8 is a node's word offset, which exceeds every "
     "type index (each type record is 5 words and precedes the nodes), so the type test refuses it as before",
     ['$select:2237:const 7->6@70', '$tagof:1903:const 7->6@60', '$scell:1919:const 7->6@60']),
    ("the class test reads only the payload's parity: a wrong-class word passes it, then the type word and the tag word, only "
     "if it is an Action whose foreign id is the String type index and whose operand is the word 1; the mutant then reads "
     "past the Action's 16-byte cell, and what follows it decides the outcome (`ill-string-action` builds that Action and "
     "still refuses by the words it finds, not by its class; one that ended where memory does would trap)", ['$scell:1919:const 7->8@60']),
    ('which operands a prim or a completion drops is unobservable while `$drop` is empty (CORE.md choice 1); vm-rc makes it observable',
     ['$complete:2155:i32.lt_u->i32.le_u@21', '$complete:2155:i32.gt_u->i32.ge_u@63', '$complete:2155:const 16->17@46',
      '$complete:2155:const 16->15@46', '$complete:2155:const 19->20@88', '$complete:2155:const 19->18@88',
      '$complete:2158:i32.eq->i32.ne@26', '$complete:2158:i32.ne->i32.eq@66', '$complete:2158:i32.and->i32.or@17',
      '$complete:2158:const 2->3@50', '$complete:2158:const 2->1@50', '$complete:2158:const 35->36@89', '$complete:2158:const 35->34@89']),
    ("the reference count of an append cell, unread until vm-rc",
     ['$append:1988:const 1->2@34', '$append:1988:const 1->0@34']),
    ("clears half of the append block first: every word a cell reads is then written, so only padding words differ",
     ['$append:1984:const 5->4@73']),
    ("the payload count in the header of an Action, which stays a 16-byte cell for 0 to 2 words; only the state audit reads it",
     ['$complete:2189:i32.add->i32.sub@32', '$complete:2189:const 1->0@57']),
    ("the payload count in the header of a String or Big cell, whose size class it leaves unchanged",
     ['$scon:1939:const 4->5@31', '$scon:1939:const 4->3@31', '$scalar:1865:const 1->2@35', '$scalar:1865:const 1->0@35']),
    ("stores the Foreign node's operand count where the Action's foreign id belongs: for IO.print, the only foreign vm-core "
     "admits (choice 2), both are 1", ['$complete:2190:const 3->4@72']),
    ("the mode register after a finished run: `$run` returns at once and no observation reads the register",
     ['$describe:2727:const 3->4@22', '$describe:2727:const 3->2@22']),
    ("the scope tables grow one write early, a write holding one index more than it needs or the tables doubling when exactly full: "
     "the result and the scratch of every image are the same, and the tables' size is no observation",
     ['$setscope:1394:const 1->2@45', '$holdscope:1405:i32.le_u->i32.lt_u@9']),
    ("at a size equal to the index that passed it, either arm gives the same size", ['$holdscope:1407:i64.lt_u->i64.le_u@9']),
    ("the guard on a table of 2^30 indices, which no image reaches: the earlier tables stay in scratch (`$take` has no free), so "
     "`$take` stops the image before a table passes 2^29 indices (CORE.md choice 16)",
     ['$holdscope:1409:i64.gt_u->i64.ge_u@9', '$holdscope:1409:const 2->3@80', '$holdscope:1409:const 2->1@80']),
    ("a type table of twice the bytes it needs: only scratch is wasted", ['$holdscope:1411:const 2->3@73']),
    ("copies as many bytes again, from after the old type table, into the upper half of the new one, whose indices "
     "are written before they are read", ['$holdscope:1412:const 2->3@80']),
]
EQUIVALENT: dict[str, str] = {m: why for why, names in _WHY for m in names}
assert sum(len(names) for _, names in _WHY) == len(EQUIVALENT), 'a survivor is explained twice'
