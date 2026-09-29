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
    ('Nat.sub at x = y is 0 by either arm of the select',
     ['$prim:2112:i32.gt_u->i32.ge_u@39']),
    ('the key differs from the word at this point (equality returned above), so `<` and `<=` agree',
     ['$select:2295:i32.lt_u->i32.le_u@17']),
    ("a flag or an answer that its reader tests only for truth: `$select`'s `imm`, the `tfn` that a completion sets, "
     "`$tail`'s answer (`$enter` tests it and `$activate` compares it with 0), `$serve`'s answer (`$run` tests it), "
     "`$describable`'s seen mark and its answer (its caller tests `eqz`)",
     ['$complete:2207:const 1->2@25', '$describable:2914:const 1->2@63', '$describable:2932:const 1->2@4',
      '$select:2309:const 1->2@34', '$serve:2473:const 1->2@16', '$tail:2160:const 1->2@20']),
    ("the class mask lets a Closure past the class test, but its word at offset 8 is a node's word offset, which "
     'exceeds every type index (each type record is 5 words and precedes the nodes), so the type test that follows '
     "refuses it as before: at a Case's scrutinee, in `$tagof` and `$scell`, and at the final IO.OP of `$finish`",
     ['$finish:2692:const 7->6@60', '$scell:1954:const 7->6@60', '$select:2312:const 7->6@70',
      '$tagof:1937:const 7->6@60']),
    ("the class test reads only the payload's parity: a wrong-class word passes it, then the type word and the tag "
     'word, only if it is an Action whose foreign id is the String type index and whose operand is the word 1; the '
     "mutant then reads past the Action's 16-byte cell, and what follows it decides the outcome (`ill-string-action` "
     'builds that Action and still refuses by the words it finds, not by its class; one that ended where memory does '
     'would trap)',
     ['$scell:1954:const 7->8@60']),
    ('which operands a prim or a completion drops is unobservable while `$drop` is empty (CORE.md choice 1); vm-rc '
     'makes it observable',
     ['$complete:2218:const 16->15@46', '$complete:2218:const 16->17@46', '$complete:2218:const 19->18@88',
      '$complete:2218:const 19->20@88', '$complete:2218:i32.gt_u->i32.ge_u@63',
      '$complete:2218:i32.lt_u->i32.le_u@21', '$complete:2221:const 2->1@50', '$complete:2221:const 2->3@50',
      '$complete:2221:const 35->34@89', '$complete:2221:const 35->36@89', '$complete:2221:i32.and->i32.or@17',
      '$complete:2221:i32.eq->i32.ne@26', '$complete:2221:i32.ne->i32.eq@66']),
    ('the reference count of an append cell, unread until vm-rc',
     ['$append:2029:const 1->0@34', '$append:2029:const 1->2@34']),
    ('clears half of the append block first: every word a cell reads is then written, so only padding words differ',
     ['$append:2025:const 5->4@73']),
    ("the payload count in the header of a String cell, a Big cell or the terminal continuation's `Emit{x}`, whose "
     'size class it leaves unchanged (a word more or less is padding of the same 16 or 32 bytes): nothing but the '
     'state audit reads it, and the audit accepts the padding zero that a larger count names',
     ['$enter:2393:const 3->4@39', '$scalar:1891:const 1->0@35', '$scalar:1891:const 1->2@35',
      '$scon:1974:const 4->3@31', '$scon:1974:const 4->5@31']),
    ("the Action's foreign id, which a mutant fills with the Foreign node's operand count instead: only Top's loop "
     'reads it (`$serve` stops `InternalFailure` unless it is 1), a Book never performs (D22), and a Program admits no '
     'foreign but IO.print (choice 2), whose id and operand count are both 1',
     ['$complete:2257:const 3->4@72']),
    ('the scope tables grow one write early, a write holding one index more than it needs or the tables doubling when '
     "exactly full: the result and the scratch of every image are the same, and the tables' size is no observation",
     ['$holdscope:1431:i32.le_u->i32.lt_u@9', '$setscope:1420:const 1->2@45']),
    ('at a size equal to the index that passed it, either arm gives the same size',
     ['$holdscope:1433:i64.lt_u->i64.le_u@9']),
    ('the guard on a table of 2^30 indices, which no image reaches: the earlier tables stay in scratch (`$take` has no '
     'free), so `$take` stops the image before a table passes 2^29 indices (CORE.md choice 16)',
     ['$holdscope:1435:const 2->1@80', '$holdscope:1435:const 2->3@80', '$holdscope:1435:i64.gt_u->i64.ge_u@9']),
    ('a type table of twice the bytes it needs: only scratch is wasted',
     ['$holdscope:1437:const 2->3@73']),
    ('copies as many bytes again, from after the old type table, into the upper half of the new one, whose indices are '
     'written before they are read',
     ['$holdscope:1438:const 2->3@80']),
    ("the owner word of an Activation (offset 8: the function's root or the Closure node), written at entry and loaded "
     "by nothing until vm-rc releases the Activation: no load of `vm.wat` takes offset 8 of `act` or of a Call frame's "
     "saved Activation, no register holds it, and the state audit's edges begin at offset 16",
     ['$enter:2369:const 5->4@76', '$enter:2369:const 5->6@76', '$enter:2369:i32.add->i32.sub@53']),
    ('the operand-count test of an Action target (`nops > 1`): SPEC section 7 admits zero or one and no valid image '
     "passes more (an Invoke's arrow has one domain or, erased, none, and a Program phase enters `k` with one), so the "
     "mutant's threshold of 2 is never met (CORE.md, Run controls)",
     ['$enter:2426:const 1->2@47']),
    ('the width of the copy from an Action into its request, 8 bytes a word, not 4: an Action has at most 3 payload '
     'words (its foreign id and its operands, of which no registry foreign has more than 2), so the copy stays within '
     "the request's cell of 16 or 32 bytes; it reads at most 8 bytes past a 16-byte Action, which lie in memory (the "
     'request was allocated after the Action), and what it writes past the operands is overwritten by `k` or is '
     "padding that nothing reads (the state audit's edges for a request stop at `k`)",
     ['$enter:2432:const 2->3@121']),
    ("the loop over an Action's operands as its request is built: its one effect is `$dup`, empty until vm-rc (CORE.md "
     "choice 1), and every word it loads for it lies within a few words of the Action's cell, in memory (the request "
     'above it was allocated first)',
     ['$enter:2433:const 1->0@20', '$enter:2433:const 1->2@20', '$enter:2436:i32.ge_u->i32.gt_u@25',
      '$enter:2437:const 2->1@102', '$enter:2437:const 2->3@102', '$enter:2437:const 8->7@64',
      '$enter:2437:const 8->9@64', '$enter:2437:i32.add->i32.sub@32', '$enter:2437:i32.add->i32.sub@56',
      '$enter:2438:const 1->2@48', '$enter:2438:i32.add->i32.sub@25']),
    ('an operand that no completion reads: `$complete` reads operand 0 as `a` only where the node has an operand (a '
     'prim, Succ or Chr) and operand 1 as `b` only where it has two, and there operand 1 is the last, taken from '
     '`val`. The other loads are unread words of the frame region: the word past the operands (`i = cnt`), operand 1 '
     'of a node with three or more (`ops - 4`, `ops + 8`), and operand 0 at a shift that changes nothing (`ops + 0`)',
     ['$opnd:2184:i32.ge_u->i32.gt_u@9', '$opnd:2186:const 2->1@64', '$opnd:2186:const 2->3@64',
      '$opnd:2186:i32.add->i32.sub@15']),
    ('the scratch tables of `$describable`, sized with slack: `seen` holds a byte per type index (`nT + 7` and `nT + '
     '9` cover them), and the stack a word per constructor field and the first push (`W + 7`, `W + 9`, `2W + 16` or `W '
     '- 8` words: fewer than `W - 8` are pushed, since the image holds its 8 header words, a type record, the '
     "constructor records and `main`'s function record besides the fields)",
     ['$describable:2903:const 8->7@59', '$describable:2903:const 8->9@59', '$describable:2904:const 2->3@83',
      '$describable:2904:const 8->7@68', '$describable:2904:const 8->9@68', '$describable:2904:i32.add->i32.sub@44']),
    ("a stack of `$describable` of half the words: it overruns only for constructors of more than half of the image's "
     'words, and then into memory above scratch, which nothing reads (no `$take` follows `$describable`) and `$alloc` '
     "zeroes before a cell holds it; a trap only where that block ends exactly at the memory's end, a layout no row "
     'builds',
     ['$describable:2904:const 2->1@83']),
    ("a Program's first test of its words at argc 2: the second test reads argument 2 past the argv table, where the "
     'first bytes of scratch (`mk`, whose leading bytes mark the header words) give length 0, not the 2 of `--`, and '
     'stops `usage` there: the same stop',
     ['$entry:2940:const 3->2@41']),
    ('the walk over the ordinals starts at FUEL, argument 2, which `$u32must` accepted a line above',
     ['$entry:2949:const 3->2@18']),
]
EQUIVALENT: dict[str, str] = {m: why for why, names in _WHY for m in names}
assert sum(len(names) for _, names in _WHY) == len(EQUIVALENT), 'a survivor is explained twice'
