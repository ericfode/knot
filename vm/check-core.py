#!/usr/bin/env python3
"""Gate vm-core: knot-vm-1 (vm/vm.wat) against the frozen contract of vm/SPEC.md.

Checks, in order:
- pins: the pinned wabt assembles vm/vm.wat into vm/vm.wasm byte for byte, and
  the module's imports, exports, memory and call graph are as SPEC section 10
  and section 6 require (no function reaches itself, no call_indirect);
- every golden image runs through scripts/run-wasm-io.mjs with the output
  vm/golden/vm-expected.json fixes, and through the test build with the
  precise Exhausted, Unsupported or HostFailure cause in the VM's own outcome
  registers and a structural audit after every transition; so does every Book
  invocation vm-expected.json freezes beside them (SPEC section 8's walk);
- vm/core/fixtures.json: literal-review runs (250,000-deep non-tail recursion,
  quantum re-entry after an Action, fuel boundaries, rendering and its bounds,
  frame exhaustion, invocation errors), state-dump rows and lowered limits
  (among them where a Nat Case's predecessor is made against its Scope push, describe's frame region at its
  exact fit, `append` at a lowered heap and an Action's cell); and Books whose frozen run the reference evaluation (vm/evaluate.py) must
  also give (Chr's operand, a Big predecessor);
- the ceiling fixtures: Books and a Program whose bump pointer ends near or
  exactly at 4 GiB, described exactly or completed, or Exhausted kind 2 (heap)
  where a cell or the text would end beyond it. Each row's bump pointer and
  outcome are first derived from SPEC section 5's cell sizes over its plan
  (`ceiling_run`), independently of any VM;
- the memory-end rows: Books whose last cell (an Object whose fields fill it, and an Action) ends exactly at 48 MiB,
  where boot leaves the memory, so that a read or a write past a cell's end faults there; each bump pointer and
  line is first derived from SPEC section 5 (`ceiling_run`), and the calls from the reference evaluation;
- the scope rows (`scope` in vm/core/fixtures.json, built by vm/scope.py): images whose validation needs far more scope
  indices than the tables' first size, W + 4200 for W words: the reviewer's four saved images (two valid, two not), rows
  one short of, at and one past that size and after each of three doublings (K's fields typed, so that a slot read after a
  doubling shows its type was carried over), a Closure whose capture sits where the tables must grow, and a unit deeper
  than its `slots` with a defect after that depth (the reference codec reports the defect). Each image's words, `need`
  (derived from its plan) and SHA-256 are frozen, and its verdict and run are the reference codec's and the reference
  evaluation's, fixed before the VM changed (D7); then a seeded corpus of such images, most with one small change,
  which the VM must judge as the reference codec does: the same first defect or the same run, and no trap;
- the growth rows: a Book whose every entry allocates a 16-byte Activation stops at a lowered
  heap (with a bounded `memory.grow` count in the test build), at the full 4 GiB through the
  real host within its 120 s guard, and, where the host refuses growth beyond 4,700 pages
  (`--wasm-max-mem-pages`), as the host's HostFailure; each stop is first derived from SPEC
  sections 5 and 7 (`loop_stop`);
- a 200,000-deep nested expression, generated iteratively, and the deep
  fixtures again under a 64 KiB host stack;
- the malformed-image controls vm-spec froze (as many as SPEC section 4
  states), refused with the reference codec's first defect, and nine of them
  at section 4's resource limits, each Exhausted kind 2 on one side and
  malformed or invalid on the other; the controls vm-spec admits (among them
  a function of exactly 4,096 parameters), loaded and run as
  vm/core/fixtures.json freezes them (and as the reference evaluation runs
  them), and its
  run controls, run to the outcome and call count check-spec.py freezes with
  them, at their frozen fuel (section 7's boundary) or also on exactly that
  much fuel (section 7's operand check); its argument controls, with their
  frozen verdicts or the reference evaluation's run (section 8's words); and a
  seeded fuzz corpus of mutated goldens, and another that varies every word of
  section 4's limits, where every refusal matches the reference and no run traps
  (a crash of the reference codec on any image fails the gate, it is never skipped);
- the seeded rows of vm/core/seeded.json: Books whose expected results the pinned seed's native lane fixed
  before any VM run them (D7), and the reference evaluation and the VM must both give them: U32 and Char key
  Cases of 3 and 5 keys queried below, at, between and above their keys, with keys and computed scrutinees at
  2^30, 2^31 and 2^32-1; constructors of 3, 5 and 9 fields, flat and inside a wider one; tag Cases whose Default
  is reached by an immediate and by an Object; and, by literal review, the edges of section 6.1's inspection;
- the differential lane (vm/lane.py, parameters and seed frozen in vm/core/lane.json): a seeded corpus of
  generated programs (every second one laundered through `none`), random key Cases, prim sweeps, the
  print, Halt, digit and Nat writers' boundaries and a matrix of every kind of word at every place section 6
  inspects one, each run through vm.wasm (test build and production module) and
  through vm/evaluate.py, which must agree on stdout, exit, stderr, outcome, cause and calls; a fixed
  sample of it also through the seed's native lane, with the seed's bytes frozen; and every admitted golden,
  control and fuzz image through both;
- WAT mutants, each killed by a named fixture group through a wrong
  observation (a trap, host stack failure or timeout never counts, except for groups `trap`, `traps` and
  `memory-end`, whose defect is the trap, and group `hang`, whose defect is a search that never ends: a row
  that outlives its deadline is the wrong observation there).

`--study [--heavy]` runs the systematic mutants of vm/study.py against these rows instead (it writes
vm/receipts/study.json); `--freeze` rewrites vm/core/seeded.json and vm/core/lane.json from the seed. The gate
writes only vm/receipts/core.json.
"""
from __future__ import annotations

import datetime
import hashlib
import importlib.util
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'vm'
BUILD = ROOT / '.local/vm-core/gate'
RECEIPT = HERE / 'receipts/core.json'
HOST = ROOT / 'scripts/run-wasm-io.mjs'
HARNESS = HERE / 'harness.mjs'
SCALE = float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))  # hang guard only
NONE = 0xFFFFFFFF
FUZZ_SEED, FUZZ_PER_IMAGE = 20260928, 40
NEST = 200_000
SMALL_STACK = '--stack-size=64'


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = load('vm_build', HERE / 'build.py')
spec = load('check_spec', HERE / 'check-spec.py')
lane = load('vm_lane', HERE / 'lane.py')
scope = load('vm_scope', HERE / 'scope.py')
study = load('vm_study', HERE / 'study.py')
codec = spec.codec
reference = spec.reference


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ------------------------------------------------------------------ reasons
# The VM names each refusal with a code; the reference codec's first message
# maps to exactly one. Dynamic parts (indices, depths, names) are not compared.
# A resource limit of section 4 is not a refusal but Exhausted kind 2, which the
# reference reports as `Exhausted 2 <limit>` and the VM as the same words, so that a
# limit reported as malformed differs from it.
LIMIT_CAUSES = ('image-size', 'records', 'arity', 'slots')
REASONS = [
    *[(f'Exhausted 2 {cause}', f'Exhausted 2 {cause}') for cause in LIMIT_CAUSES],
    (r'length', 'length'), (r'magic', 'magic'), (r'total', 'total'),
    (r'header', 'header'), (r'registry digest', 'registry-digest'), (r'section \d offset', 'section-offset'),
    (r'record count', 'record-count'), (r'section \d record length', 'record-length'),
    (r'trailing words', 'trailing-words'), (r'name length', 'name-length'), (r'name padding', 'name-padding'),
    (r'name utf-8', 'name-utf8'), (r'duplicate name', 'duplicate-name'), (r'name index', 'name-index'),
    (r'type record', 'type-record'), (r'constructor grouping', 'constructor-grouping'),
    (r'opaque type', 'opaque-type'), (r'arrow name', 'arrow-name'), (r'type index', 'type-index'),
    (r'constructor count', 'constructor-count'), (r'constructor record', 'constructor-record'),
    (r'constructor tag', 'constructor-tag'), (r'constructor order', 'constructor-order'),
    (r'constant record', 'constant-record'), (r'scalar constant width', 'scalar-constant-width'),
    (r'node record', 'node-record'),
    (r'(lit|prim|default|value|con|ref|call|let|case|branch|closure|invoke|foreign) length', 'node-length'),
    (r'function record', 'function-record'), (r'function root', 'function-root'),
    (r'child offset', 'child-offset'), (r'child after parent', 'child-after-parent'),
    (r'shared node', 'shared-node'), (r'standalone arm', 'standalone-arm'),
    (r'constant index', 'constant-index'), (r'case key', 'case-key'), (r'case arm kind', 'case-arm-kind'),
    (r'unreachable node', 'unreachable-node'), (r'main index', 'main-index'), (r'noncanonical', 'noncanonical'),
    (r'validator: representation: \S+ must be opaque', 'representation-opaque'),
    (r'validator: representation: \S+ shape', 'representation-shape'),
    (r'validator: functions: duplicate function name', 'duplicate-function'),
    (r'validator: types: arrow cycle', 'arrow-cycle'),
    (r'validator: program: main must exist with no live parameters', 'program-main'),
    (r'validator: program: missing representation .*', 'program-representation'),
    (r'validator: program: main must return IO\(Unit\)', 'program-io'),
    (r'validator: [^:]+: (U32|Nat|Char|String) literal at a non-\1 type', 'literal-kind'),
    (r'validator: [^:]+: value is not a nullary constructor', 'value-nullary'),
    (r'validator: [^:]+: slot \d+ beyond depth \d+', 'slot-depth'),
    (r'validator: [^:]+: reference type', 'reference-type'),
    (r'validator: [^:]+: construct tag', 'construct-tag'), (r'validator: [^:]+: construct arity', 'construct-arity'),
    (r'validator: [^:]+: construct field type', 'construct-field-type'),
    (r'validator: [^:]+: function index', 'function-index'), (r'validator: [^:]+: call arity', 'call-arity'),
    (r'validator: [^:]+: call types', 'call-types'), (r'validator: [^:]+: unknown prim id \d+', 'unknown-prim'),
    (r'validator: [^:]+: unknown foreign id \d+', 'unknown-foreign'),
    (r'validator: [^:]+: prim arity', 'prim-arity'), (r'validator: [^:]+: foreign arity', 'foreign-arity'),
    (r'validator: [^:]+: prim operand is not the pinned \S+', 'prim-operand'),
    (r'validator: [^:]+: foreign operand is not the pinned \S+', 'foreign-operand'),
    (r'validator: [^:]+: prim result is not the pinned \S+', 'prim-result'),
    (r'validator: [^:]+: foreign result is not IO\(\S+\)', 'foreign-result'),
    (r'validator: [^:]+: let slot \d+ at depth \d+', 'let-slot'),
    (r'validator: [^:]+: let body type', 'let-body-type'),
    (r'validator: [^:]+: case slot beyond depth', 'case-slot'),
    (r'validator: [^:]+: case scrutinee type', 'case-scrutinee-type'),
    (r'validator: [^:]+: tag case on a non-data type', 'tag-case-type'),
    (r'validator: [^:]+: tag table is not dense', 'tag-table'),
    (r'validator: [^:]+: default must cover exactly the missing tags', 'default-coverage'),
    (r'validator: [^:]+: branch key', 'branch-key'), (r'validator: [^:]+: branch binders', 'branch-binders'),
    (r'validator: [^:]+: branch body type', 'branch-body-type'),
    (r'validator: [^:]+: key case on a non-scalar type', 'key-case-type'),
    (r'validator: [^:]+: keys must increase strictly, with a default', 'key-order'),
    (r'validator: [^:]+: key branch binds nothing', 'key-branch-binders'),
    (r'validator: [^:]+: key branch body type', 'key-branch-body-type'),
    (r'validator: [^:]+: default body type', 'default-body-type'),
    (r'validator: [^:]+: closure arrow', 'closure-arrow'),
    (r'validator: [^:]+: captures must increase strictly below depth', 'capture-order'),
    (r'validator: [^:]+: captures are not exactly the free slots of the body', 'capture-use'),
    (r'validator: [^:]+: closure slots \d+, reached \d+', 'closure-slots'),
    (r'validator: [^:]+: closure result type', 'closure-result-type'),
    (r'validator: [^:]+: invoke arity', 'invoke-arity'), (r'validator: [^:]+: invoke types', 'invoke-types'),
    (r'validator: [^:]+: slots \d+, reached \d+', 'function-slots'),
    (r'validator: [^:]+: body type', 'body-type'),
]


def expected_reason(refusal: str) -> str:
    """The VM code for a refusal of the reference codec: `HostFailure image: ...`, or a limit's
    `Exhausted 2 <limit>`."""
    message = refusal.removeprefix('HostFailure image: ')
    codes = [code for pattern, code in REASONS if re.fullmatch(pattern, message)]
    require(len(codes) == 1, f'reason map covers {message!r} exactly once: {codes}')
    return codes[0]


def observed_reason(result: dict) -> str | None:
    """The VM's refusal of the image, from its stderr line or, for a limit of section 4, its
    exhaustion: the host shows only kind 2, so the limit is the cause its outcome registers
    keep. A traced run that got past vm_boot failed at run time (an `ill-typed` word, SPEC
    section 6), which is no refusal of the image."""
    require(result.get('booted') is not None, 'a refusal is read from a traced run')
    if result['booted']:
        return None
    line = result['stderr'].strip()
    if line.startswith('HostFailure\timage\t'):
        return line.split('\t')[2]
    cause = (result.get('state') or {}).get('cause')
    if line == 'Exhausted\tio\tmemory' and cause in LIMIT_CAUSES:
        return f'Exhausted 2 {cause}'
    return None


# ------------------------------------------------------------------ expectations
KINDS = {1: 'steps', 2: 'memory', 3: 'frames'}  # the host's exhaustion kinds


def expected_run(case: dict) -> dict:
    """What the host shows for a golden (SPEC section 11): vm-expected's run, or the
    line its outcome prints, after the output the VM owes before it."""
    if 'exit' in case:
        return {k: case[k] for k in ('exit', 'stdout', 'stderr')}
    outcome, cause = case['outcome'], case['cause'].replace(' ', '\t')
    if outcome == 'Exhausted':
        return {'exit': 4, 'stdout': case.get('stdout', ''), 'stderr': f"Exhausted\tio\t{KINDS[case['kind']]}\n"}
    require(outcome in ('Unsupported', 'HostFailure'), f'a golden outcome {outcome}')
    return {'exit': 3 if outcome == 'Unsupported' else 5, 'stdout': case.get('stdout', ''),
            'stderr': f'{outcome}\t{cause}\n'}


def expected_dump(case: dict) -> dict:
    """The VM's own outcome registers for a golden. A HostFailure there, not only on
    stderr, shows that the VM refused before its host call (D20), not the host."""
    if 'exit' in case:
        return {'outcome': 'Completed'}
    row = {'outcome': case['outcome'], 'cause': case['cause'].split(' ')[-1]}
    return {**row, 'kind': case['kind']} if case['outcome'] == 'Exhausted' else row


def refusal_dump(reason: str) -> dict:
    """The VM's own outcome registers for a refused image, from its reason (`expected_reason`): a
    limit of section 4 is Exhausted kind 2 with the limit as its cause, any other refusal a
    HostFailure with its code."""
    if reason.startswith('Exhausted 2 '):
        return {'outcome': 'Exhausted', 'kind': 2, 'cause': reason.removeprefix('Exhausted 2 ')}
    return {'outcome': 'HostFailure', 'cause': reason}


def shown(result: dict, want: dict) -> dict:
    """The host-visible run, with stdout as its digest where `want` freezes one (a display
    run control's 16 MiB line is frozen by SHA-256)."""
    seen = {k: result[k] for k in ('exit', 'stdout', 'stderr')}
    if 'stdout_sha256' in want:
        seen['stdout_sha256'] = sha(seen.pop('stdout').encode())
    return seen


def reference_run(plan: dict, fuel: int) -> tuple[dict, dict]:
    """(host run, outcome registers) of vm-spec's reference evaluation of a Book's `main`
    (vm/evaluate.py), independent of the VM."""
    got = spec.reference.book(plan, 'main', [], fuel)
    run = {'stderr': '', **got} if 'exit' in got else got
    return expected_run(run), {**expected_dump(run), 'calls': got['calls']}


# ------------------------------------------------------------------ SPEC section 5 arithmetic
class Tail(tuple):
    """A call in tail position, (function, operands): the entering loop takes it."""


def cell(payload: int) -> int:
    """Bytes of a cell with `payload` words: the smallest power of two not below
    max(4, 2 + payload) words."""
    words = 4
    while words < 2 + payload:
        words *= 2
    return 4 * words


class Beyond(Exception):
    """A cell that would end beyond 4 GiB, or a lowered heap limit (section 5): the machine
    stops, bump unchanged."""

    def __init__(self, bump: int):
        super().__init__(bump)
        self.bump = bump


TERMINAL = 'terminal'  # a Program's terminal continuation


def ceiling_run(plan: dict, image: bytes, heap_bytes: int = 1 << 32) -> tuple[int, str | None]:
    """(bump, line) when a ceiling image finishes, from SPEC section 5 alone.

    The heap starts at H0: the image at byte 4096, the frame region from the next 64 KiB
    boundary, and its 16 MiB. The pool is materialized first, then a Program's terminal
    continuation. Each entry allocates an Activation of its owner's `slots` (section 7):
    a function's or a Closure node's. Each Construct with fields allocates an Object, a
    Closure its cell, a U32 result at or above 2^31 a Big cell, `append` one String cell
    per code of its first operand as one block (CORE.md choice 4), and the terminal
    continuation `Emit{x}`. Nothing is freed (choice 1), so the bump pointer is the sum.
    An Action (a Foreign node) is a cell of its foreign id and operands. A cell may end exactly at 4 GiB; one that would end beyond raises `Beyond`. A String
    here is its code count, since only sizes reach the heap. A Book's line is section 8's
    rendering, by the reference evaluation's `describe`; a Program's Emit has none. A heap
    lowered to `heap_bytes` (section 5's test limit) ends at H0 + heap_bytes instead."""
    rep, fns = plan['representation'], plan['functions']
    big, scon = cell(1), cell(4)  # a Big scalar; a String cell (type, tag, Char, tail)
    end = 4096 + len(image)
    require(end % 65536, 'the image does not end on a 64 KiB boundary, where "next" reads two ways')
    heap = [(end // 65536 + 1) * 65536 + (16 << 20)]
    limit = min(1 << 32, heap[0] + heap_bytes)

    def take(n: int):
        if heap[0] + n > limit:
            raise Beyond(heap[0])
        heap[0] += n

    pool = set()  # interned: one entry per distinct kind and value, as serializer.encode keeps them

    def lits(node):
        op = node[0]
        if op == 'lit':
            pool.add((node[2], tuple(node[3]) if node[2] == 'String' else node[3]))
        elif op == 'let':
            lits(node[3])
            lits(node[4])
        elif op == 'case':
            for arm in [r for r in node[5] if r] + [node[6]] * bool(node[6]):
                lits(arm[-1])
        elif op in ('con', 'prim', 'call'):
            for kid in node[3]:
                lits(kid)
        elif op == 'closure':
            lits(node[5])
        elif op == 'invoke':
            for kid in [node[2], *node[3]]:
                lits(kid)
    for f in fns:
        lits(f['body'])
    for kind, v in pool:  # the pool sits just above H0, far below 4 GiB
        take(sum(scon + big * (c >= 2 ** 31) for c in v) if kind == 'String' else big * (v >= 2 ** 31))
    if plan['entry'] == 'program':
        take(cell(1))  # the terminal continuation: a Closure-class cell, node none

    def apply(f, ops):
        """Section 7's entry of a Closure or the terminal continuation."""
        if f == TERMINAL:
            take(cell(3))  # Emit{x}: type, tag, x
            return ('obj', rep['IO.OP'], 0, tuple(ops))
        _, node, caps = f
        take(cell(2 + node[3]))  # the Closure node's Activation
        return value(node[5], [*caps, *ops] + [None] * node[3])

    def value(node, env, tail=False):
        op = node[0]
        if op == 'lit':
            return len(node[3]) if node[2] == 'String' else node[3]
        if op == 'value':
            return node[2]
        if op == 'ref':
            return env[node[2]]
        if op == 'let':
            env[node[2]] = value(node[3], env)
            return value(node[4], env, tail)
        if op == 'case':
            _, _, slot, t, mode, rows, default = node
            require((mode, default) == ('tags', None), 'the model cases by tag, without a Default')
            if t != rep.get('Nat'):  # an Object: selection allocates nothing, and a Branch binds its fields' words
                _, _, tag, fields = env[slot]
                arm = rows[tag]
                env[arm[2]:arm[2] + arm[3]] = fields[:arm[3]]
                return value(arm[4], env, tail)
            n = env[slot]
            arm = rows[n > 0]
            if n:  # choice 5: n - 1 is allocated only when a Branch binds it
                take(big * (n - 1 >= 2 ** 31))
                env[arm[2]] = n - 1
            return value(arm[4], env, tail)
        if op == 'closure':  # the captures in order; the body stays code
            take(cell(1 + len(node[4])))
            return ('clo', node, tuple(env[s] for s in node[4]))
        if op == 'invoke':  # the function, then its argument if live
            f = value(node[2], env)
            return apply(f, [value(k, env) for k in node[3]])
        ops = [value(k, env) for k in node[3]]
        if op == 'call':
            return Tail((node[2], ops)) if tail else enter(node[2], ops)
        if op == 'con' and node[1] not in (rep.get('Nat'), rep.get('Char')):  # Succ and Chr make words, not cells
            take(cell(2 + len(ops)))
            return ('obj', node[1], node[2], tuple(ops))
        if op == 'foreign':  # an inert Action: the foreign id and its operands, no type or tag word
            take(cell(1 + len(ops)))
            return ('action', node[2], tuple(ops))
        if op == 'prim' and node[2] == 0:  # U32.add
            r = (ops[0] + ops[1]) & NONE
            take(big * (r >= 2 ** 31))
            return r
        if op == 'prim' and node[2] == 35:  # String.append
            take(scon * ops[0])
            return ops[0] + ops[1]
        raise AssertionError(f'the section 5 model does not cover {node[:3]}')

    def enter(index, ops):
        while True:
            f = fns[index]
            take(cell(2 + f['slots']))  # an Activation: owner, depth, slot[slots]
            result = value(f['body'], ops + [None] * f['slots'], True)
            if not isinstance(result, Tail):
                return result
            index, ops = result

    main = next(i for i, f in enumerate(fns) if f['name'] == 'main')
    result = enter(main, [])
    if plan['entry'] == 'book':
        return heap[0], spec.reference.Machine(plan, 0).describe(result, fns[main]['result'])
    final = apply(apply(result, []), [TERMINAL])  # section 8's phases 1 and 2
    require(final[:3] == ('obj', rep['IO.OP'], 0), f'the model ends a Program at Emit only, not {final}')
    return heap[0], None


def ceiling_expectation(plan: dict, image: bytes) -> tuple[dict, dict]:
    """(host run, dump) that section 5's bump and CORE.md choice 12 give. A cell beyond
    4 GiB stops the machine with Exhausted kind 2 (heap). A Program's Emit completes with
    no text. A Book's text starts at the bump pointer and is printed when it ends at or
    below 4 GiB, else it is Exhausted kind 2 (heap) too."""
    exhausted = {'exit': 4, 'stdout': '', 'stderr': 'Exhausted\tio\tmemory\n'}
    try:
        bump, line = ceiling_run(plan, image)
    except Beyond as stop:
        return exhausted, {'outcome': 'Exhausted', 'kind': 2, 'cause': 'heap', 'bump': stop.bump}
    if line is None:
        return {'exit': 0, 'stdout': '', 'stderr': ''}, {'outcome': 'Completed', 'bump': bump}
    if bump + len(line) - 1 <= 1 << 32:  # the text is the line without its LF
        return {'exit': 0, 'stdout': line, 'stderr': ''}, {'outcome': 'Completed', 'bump': bump}
    return exhausted, {'outcome': 'Exhausted', 'kind': 2, 'cause': 'heap', 'bump': bump}


def refilled(plan: dict, fill: int, n: int) -> dict:
    """`plan` with its one Nat literal `fill` set to `n`: a memory-end row at a size the reference evaluation's
    recursion reaches."""
    text = json.dumps(plan)
    require(text.count(f'"Nat", {fill}]') == 1, f'one Nat literal {fill}')
    return json.loads(text.replace(f'"Nat", {fill}]', f'"Nat", {n}]'))


def loop_stop(image: bytes, heap_bytes: int = 1 << 32, memory_bytes: int = 1 << 32) -> tuple[int, int, bool]:
    """(bump, calls, refused) where the tail loop of core/loop-cells stops, from SPEC sections 5 and 7, in
    closed form: `ceiling_run` steps entry by entry, too many at 4 GiB (`growth_jobs` checks that the two
    agree at a small heap). main and every entry of `loop` are debited (calls += 1) and then take an
    Activation of 0 slots, 16 bytes, from H0. The first whose Activation would end beyond the heap's end
    (H0 + heap_bytes, at most 4 GiB) or beyond the `memory_bytes` the host grants stops the machine with
    the bump pointer unchanged: Exhausted kind 2 (heap) at the heap's end, the host's refusal (`refused`,
    HostFailure) at the memory's."""
    h0 = ((4096 + len(image)) // 65536 + 1) * 65536 + (16 << 20)
    heap_end = min(1 << 32, h0 + heap_bytes)
    cells = (min(heap_end, memory_bytes) - h0) // 16
    return h0 + 16 * cells, cells + 1, memory_bytes < heap_end


def run_control_count() -> int:
    """SPEC section 12's frozen number of admitted run controls."""
    text = ' '.join((HERE / 'SPEC.md').read_text().split())
    m = re.search(r'(\d+) admitted \*\*run controls\*\*', text)
    require(m, 'SPEC section 12 states its number of run controls')
    return int(m.group(1))


def refusal_counts() -> tuple[int, int, int, int]:
    """SPEC section 4's frozen refusals: (total, byte-level, at the limits, plan-level)."""
    text = ' '.join((HERE / 'SPEC.md').read_text().split())
    m = re.search(r'freezes (\d+) refusals \((\d+) byte-level, (\d+) at the limits, (\d+) plan-level\)', text)
    require(m, 'SPEC section 4 states its frozen refusal counts')
    return tuple(map(int, m.groups()))


# ------------------------------------------------------------------ runners
def host(module: Path, sandbox: Path, argv: list, node_flags=()) -> dict:
    p = subprocess.run(['node', *node_flags, str(HOST), str(module), str(sandbox), '--', *argv],
                       capture_output=True, timeout=120 * SCALE)
    return {'exit': p.returncode, 'stdout': p.stdout.decode(), 'stderr': p.stderr.decode()}


def harness(jobs: list, timeout=600, node_flags=(), max_timeouts=None) -> dict:
    env = {**os.environ, 'KNOT_HARNESS_MAX_TIMEOUTS': str(max_timeouts)} if max_timeouts is not None else None
    p = subprocess.run(['node', *node_flags, str(HARNESS)], input=json.dumps(jobs), capture_output=True, text=True,
                       timeout=timeout * SCALE, env=env)
    require(p.returncode == 0, f'harness failed: {p.stderr[-2000:]}')
    return {r['id']: r for r in map(json.loads, p.stdout.splitlines())}


def clean(result: dict) -> bool:
    """A reported outcome, not an engine trap, host stack failure or host error."""
    stderr = result['stderr']
    return result.get('status') not in ('Trap', 'HostStack', 'Timeout', 'Skipped') and not any(
        s in stderr for s in ('HostFailure\tio\ttrap', 'HostFailure\tio\thost', 'Exhausted\tio\tcall-stack'))


def observed_wrong(job: dict, out: dict) -> bool:
    """The run `out` differs from the row's frozen run (unless the row freezes none), its registers or its yields, or
    exceeds a bound the row states."""
    return ((job['want'] is not None and shown(out, job['want']) != job['want'])
            or any((out['yields'] if k == 'yields' else out['state'][k]) != v for k, v in job.get('dump', {}).items())
            or any(out['state'][k] > most for k, most in job.get('at_most', {}).items()))


def pool(fn, items, workers=8):
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, items))


# ------------------------------------------------------------------ static module checks
def module_shape(module: Path) -> dict:
    text = subprocess.run(['wasm2wat', str(module)], capture_output=True, text=True, check=True).stdout
    imports = re.findall(r'\(import "([^"]+)" "([^"]+)" \(func', text)
    exports = re.findall(r'\(export "([^"]+)" \((func|memory)', text)
    memory = re.findall(r'\(memory \(;\d+;\) (\d+) (\d+)\)', text)
    graph, current = {}, None
    for line in text.splitlines():
        m = re.match(r'\s*\(func \(;(\d+);\)', line)
        if m:
            current = int(m.group(1))
            graph[current] = set()
        elif current is not None:
            c = re.match(r'\s*call (\d+)\s*$', line)
            if c:
                graph[current].add(int(c.group(1)))
    cycle = None
    for start in graph:  # does any function reach itself?
        seen, stack = set(), list(graph[start])
        while stack:
            f = stack.pop()
            if f == start:
                cycle = start
                break
            if f not in seen:
                seen.add(f)
                stack += graph.get(f, ())
        if cycle is not None:
            break
    return {'imports': sorted(f'{m}.{n}' for m, n in imports), 'exports': sorted(n for n, _ in exports),
            'memory_pages': [list(map(int, x)) for x in memory], 'start_section': '(start' in text,
            'call_indirect': 'call_indirect' in text, 'functions': len(graph), 'reaches_itself': cycle}


def check_shape(shape: dict, test: bool):
    require(set(shape['imports']) <= {f'knot_io.{n}' for n in ('args', 'print', 'die', 'open', 'read', 'read_bytes',
                                                                'write_bytes', 'close', 'path_identity', 'exhausted')},
            f'imports only knot_io: {shape["imports"]}')
    base = {'memory', 'knot_alloc', 'knot_main'}
    extra = {'vm_limits', 'vm_boot', 'vm_step', 'vm_dump'} if test else set()
    require(set(shape['exports']) == base | extra, f'exports {shape["exports"]}')
    require(shape['memory_pages'] == [[1, 65536]], f'one memory with maximum 65,536 pages (D19): {shape["memory_pages"]}')
    require(not shape['start_section'], 'no start section')
    require(not shape['call_indirect'], 'no call_indirect')
    require(shape['reaches_itself'] is None, f'function {shape["reaches_itself"]} reaches itself')


# ------------------------------------------------------------------ fixtures
def nested_image(n: int, digest: bytes) -> bytes:
    """U32.is_eq(add(...add(0, 1)..., 1), n) nested n deep, laid out iteratively in
    the canonical order serializer.encode would produce (checked for small n)."""
    types = [[3, 0, 0, 0], [0, 1, 0, 2]]                       # U32 opaque, Bool data
    ctors = [[1, 0, 2, 0], [1, 1, 3, 0]]                       # False, True
    names = [b'U32', b'Bool', b'False', b'True', b'U32.add', b'U32.is_eq', b'main']
    consts = [[0, 1, 0], [0, 1, 1], [0, 1, n]]
    section = lambda rs: [len(rs)] + [w for r in rs for w in [len(r) + 1, *r]]
    named = [[len(b), *[int.from_bytes(b[i:i + 4].ljust(4, b'\0'), 'little') for i in range(0, len(b), 4)]]
             for b in names]
    head = [section(types), section(ctors), None, section(consts), None, section(named)]
    offsets = [32, 32 + len(head[0]), 32 + len(head[0]) + len(head[1])]
    functions_size = 1 + 8 + 8 + 6
    offsets.append(offsets[2] + functions_size)
    offsets.append(offsets[3] + len(head[3]))
    at = offsets[4] + 1
    nodes, place = [], {}

    def node(key, record):
        nonlocal at
        place[key] = at
        nodes.append(record)
        at += len(record) + 1

    node('a0', [5, 0, 0]); node('a1', [5, 0, 1]); node('add', [1, 0, 0, 2, place['a0'], place['a1']])
    node('e0', [5, 0, 0]); node('e1', [5, 0, 1]); node('eq', [1, 1, 8, 2, place['e0'], place['e1']])
    node(0, [0, 0, 0])
    for k in range(1, n + 1):
        node(('one', k), [0, 0, 1])
        node(k, [6, 0, 0, 2, place[k - 1], place[('one', k)]])
    node('n', [0, 0, 2])
    node('main', [6, 1, 1, 2, place[n], place['n']])
    head[4] = [len(nodes)] + [w for r in nodes for w in [len(r) + 1, *r]]
    head[2] = section([[4, 0, 2, 2, place['add'], 0, 0], [5, 1, 2, 2, place['eq'], 0, 0], [6, 1, 0, 0, place['main']]])
    offsets.append(at)
    body = [w for s in head for w in s]
    header = [codec.MAGIC, 1, 32 + len(body), 0, 2, *offsets, 0,
              NONE, 0, NONE, NONE, 1, NONE, NONE, NONE, NONE, NONE, NONE, NONE,
              *(int.from_bytes(digest[i:i + 4], 'little') for i in range(0, 32, 4))]
    return b''.join(w.to_bytes(4, 'little') for w in header + body)


def nested_plan(n: int) -> dict:
    chain = ['lit', 0, 'U32', 0]
    for _ in range(n):
        chain = ['call', 0, 0, [chain, ['lit', 0, 'U32', 1]]]
    return {'entry': 'book', 'representation': {'U32': 0, 'Bool': 1},
            'types': [{'kind': 'opaque', 'name': 'U32'},
                      {'kind': 'data', 'name': 'Bool', 'constructors': [{'name': 'False', 'fields': []},
                                                                        {'name': 'True', 'fields': []}]}],
            'functions': [{'name': 'U32.add', 'parameters': [0, 0], 'result': 0, 'slots': 2,
                           'body': ['prim', 0, 0, [['ref', 0, 0], ['ref', 0, 1]]]},
                          {'name': 'U32.is_eq', 'parameters': [0, 0], 'result': 1, 'slots': 2,
                           'body': ['prim', 1, 8, [['ref', 0, 0], ['ref', 0, 1]]]},
                          {'name': 'main', 'parameters': [], 'result': 1, 'slots': 0,
                           'body': ['call', 1, 1, [chain, ['lit', 0, 'U32', n]]]}]}


def verdict(data: bytes, label: str, reg: dict, digest: bytes) -> str | None:
    """The reference codec's verdict on an image (`spec.rejected`). A crash of the reference is no
    verdict, and a corpus that skipped the row would compare less than it reports, so it fails the
    gate, naming the image."""
    try:
        return spec.rejected(data, reg, digest)
    except Exception as error:
        raise AssertionError(f'{label}: the reference codec crashed ({type(error).__name__}: {error})') from error


def crash_fails() -> bool:
    """Whether `verdict` fails on a reference that crashes: `spec.rejected` is replaced by one that raises."""
    saved = spec.rejected

    def crash(*_):
        raise MemoryError('probe')
    spec.rejected = crash
    try:
        verdict(b'', 'probe', {}, b'')
    except AssertionError:
        return True
    finally:
        spec.rejected = saved
    return False


def fuzz_corpus(images: dict, reg: dict, digest: bytes, out: Path) -> list:
    """Seeded single mutations of the goldens: a header or body word replaced from a
    pool of boundary values, two body words swapped, a truncation, or a small shift."""
    rng = random.Random(FUZZ_SEED)
    rows = []
    for name in sorted(images):
        base = images[name]
        for k in range(FUZZ_PER_IMAGE):
            w = [int.from_bytes(base[i:i + 4], 'little') for i in range(0, len(base), 4)]
            op = rng.randrange(6)
            if op <= 2:
                i = rng.randrange(32) if op == 0 else rng.randrange(32, len(w))
                w[i] = rng.choice([0, 1, 2, 3, NONE, (w[i] + 1) & NONE, (w[i] - 1) & NONE, rng.randrange(64),
                                   rng.getrandbits(32), rng.choice(w)])
                data = b''.join(x.to_bytes(4, 'little') for x in w)
            elif op == 3:
                i, j = rng.randrange(32, len(w)), rng.randrange(32, len(w))
                w[i], w[j] = w[j], w[i]
                data = b''.join(x.to_bytes(4, 'little') for x in w)
            elif op == 4:
                data = base[:rng.randrange(len(base))]
            else:
                i = rng.randrange(32, len(w))
                w[i] = (w[i] + rng.choice([-4, -2, 2, 4])) & NONE
                data = b''.join(x.to_bytes(4, 'little') for x in w)
            label = f'{name}-{k}'
            reference = verdict(data, f'fuzz {label}', reg, digest)
            (out / f'{label}.kimg').write_bytes(data)
            entry = int.from_bytes(data[12:16], 'little') if len(data) >= 16 else 0
            rows.append({'label': label, 'sha256': sha(data), 'reference': reference,
                         'argv': [f'{label}.kimg', '1000', '--'] if entry == 1 else [f'{label}.kimg', 'main', '1000']})
    return rows


def limit_corpus(images: dict, reg: dict, digest: bytes, out: Path) -> list:
    """Every golden with one word of section 4's limits set to values around its limit: a section's
    record count (around 2^20 and around the fit of two words per record), a function's arity and
    `slots`, a Closure's `slots`. The frozen controls hold one image for each side of a limit; this
    varies each such word of each golden, in every section and function."""
    around = lambda n: [0, n - 1, n, n + 1, NONE]
    rows = []
    for name in sorted(images):
        w = [int.from_bytes(images[name][i:i + 4], 'little') for i in range(0, len(images[name]), 4)]
        words = []  # (what, index of the word, its values)
        cursor = 32
        for s in range(6):
            fit = (len(w) - (cursor + 1)) // 2
            words.append((f'count {s}', cursor, [*around(fit), *around(1 << 20), w[cursor] + 1]))
            count, cursor = w[cursor], cursor + 1
            for _ in range(count):
                cursor += w[cursor]
        at = w[7] + 1
        for f in range(w[w[7]]):
            words.append((f'arity {f}', at + 3, [*around(4096), w[at + 3] + 1]))
            words.append((f'slots {f}', at + 4, [*around(65536), w[at + 4] + 1]))
            at += w[at]
        at = w[9] + 1
        for n in range(w[w[9]]):
            if w[at + 1] == 10:  # a Closure node
                words.append((f'closure {n}', at + 5, [*around(65536), w[at + 5] + 1]))
            at += w[at]
        for what, index, values in words:
            for v in sorted({v for v in values if 0 <= v <= NONE and v != w[index]}):
                data = b''.join(x.to_bytes(4, 'little') for x in [*w[:index], v, *w[index + 1:]])
                reference = verdict(data, f'limit word {name}: {what} = {v}', reg, digest)
                file = f'l{len(rows)}.kimg'
                (out / file).write_bytes(data)
                rows.append({'label': f'{name}: {what} = {v}', 'sha256': sha(data), 'reference': reference,
                             'argv': [file, '1000', '--'] if w[3] == 1 else [file, 'main', '1000']})
    return rows


def compare(kind: str, corpus: list, outcomes: dict) -> dict:
    """The VM refuses each image of a corpus with the reference codec's first defect, a limit of
    section 4 as Exhausted kind 2 among them, admits what the reference admits, and never traps.
    Every row has the reference's verdict (`verdict`): none is skipped."""
    tally = {'refused': 0, 'limits': 0, 'accepted': 0}
    for r in corpus:
        g = outcomes[r['label']]
        require(clean(g), f"{kind} {r['label']} is not a clean outcome: {g['status']} {g['stderr']!r}")
        ref = r['reference']
        if ref is None:
            require(observed_reason(g) is None, f"{kind} {r['label']}: reference admits it, VM refused {g['stderr']!r}")
            tally['accepted'] += 1
        else:
            require(observed_reason(g) == expected_reason(ref), f"{kind} {r['label']}: VM {g['stderr']!r}, reference {ref!r}")
            tally['refused'] += 1
            tally['limits'] += ref.startswith('Exhausted')
    return tally


def growth_jobs(rows: list, plan: dict, image: bytes, name: str, sandbox: Path) -> list:
    """A job for each frozen growth row of vm/core/fixtures.json, its stop first derived from SPEC sections
    5 and 7 by `loop_stop` (which must agree with `ceiling_run` at a small heap). A row lowers the heap
    (`limits`, test build only) or makes the host refuse growth beyond `pages` (`--wasm-max-mem-pages`); a
    trap is the outcome only where the host refuses."""
    small = 1 << 20
    try:
        ceiling_run(plan, image, small)
    except Beyond as stop:
        require(stop.bump == loop_stop(image, small)[0], f'loop_stop gives {loop_stop(image, small)}, section 5 stops at {stop.bump}')
    else:
        raise AssertionError('the loop of core/loop-cells does not stop under a heap of 1 MiB')
    jobs = []
    for r in rows:
        bump, calls, refused = loop_stop(image, r.get('limits', {}).get('heap', 1 << 32), r.get('pages', 1 << 16) << 16)
        if refused:  # section 5: a host that refuses growth below the maximum is HostFailure, never Exhausted
            expect, dump = {'exit': 5, 'stdout': '', 'stderr': 'HostFailure\tio\ttrap\n'}, {'outcome': None, 'calls': calls, 'bump': bump}
        else:
            expect = {'exit': 4, 'stdout': '', 'stderr': 'Exhausted\tio\tmemory\n'}
            dump = {'outcome': 'Exhausted', 'kind': 2, 'cause': 'heap', 'calls': calls, 'bump': bump}
        require((r['expect'], r['dump']) == (expect, dump),
                f"growth {r['name']}: frozen {r['expect']} {r['dump']}, sections 5 and 7 give {expect} {dump}")
        jobs.append({'id': f"growth:{r['name']}", 'files': {name: str(sandbox / name)}, 'argv': [name, *r['argv']],
                     'limits': r.get('limits'), 'flags': [f"--wasm-max-mem-pages={r['pages']}"] if 'pages' in r else [],
                     'expect': expect, 'want': {**expect, 'stderr': ''} if refused else expect, 'dump': dump,
                     'at_most': {'grows': r['grows_at_most']} if 'grows_at_most' in r else {}})
    return jobs


def growth_registers(job: dict, wasm: Path) -> dict:
    """The job on the test build `wasm` in the in-memory host, its registers after the stop."""
    keys = {k: job[k] for k in ('id', 'files', 'argv', 'limits')}
    return harness([{**keys, 'wasm': str(wasm)}], 120, job['flags'])[job['id']]


def check_growth(jobs: list, module: Path, test: Path) -> list:
    """Each growth job on the test build, with its registers and its `memory.grow` count, and, where the
    heap is not lowered, on the production module through the real host, whose 120 s guard is what growth
    one page at a time overruns at 4 GiB (a timeout is neither Exhausted nor agreement, SPEC section 11)."""
    def real(job):
        try:
            return host(module, Path(next(iter(job['files'].values()))).parent, job['argv'], job['flags'])
        except subprocess.TimeoutExpired as late:
            raise AssertionError(f"{job['id']}: no stop within {late.timeout:g} s on the real host") from late

    def verified(job, out):
        trap = job['dump']['outcome'] is None
        require((out['status'] == 'Trap') if trap else clean(out), f"{job['id']}: {out['status']} {out['stderr']!r}")
        require(shown(out, job['want']) == job['want'], f"{job['id']}: {shown(out, job['want'])} vs {job['want']}")
        require(all(out['state'][k] == v for k, v in job['dump'].items()), f"{job['id']}: {out['state']} vs {job['dump']}")
        require(all(out['state'][k] <= most for k, most in job['at_most'].items()),
                f"{job['id']}: memory.grow called {out['state']['grows']} times, at most {job['at_most']} expected")
        return {'name': job['id'].split(':', 1)[1], **{k: out['state'][k] for k in ('outcome', 'calls', 'bump', 'grows')}}

    record = {j['id']: verified(j, growth_registers(j, test)) for j in jobs if j['limits']}  # quick, deterministic
    rest = [j for j in jobs if not j['limits']]
    tasks = [(j, run) for j in rest for run in (real, lambda j: growth_registers(j, test))]
    for (j, run), out in zip(tasks, pool(lambda t: t[1](t[0]), tasks, workers=2)):
        if run is real:
            require(out == j['expect'], f"{j['id']}: the real host shows {out}, section 5 gives {j['expect']}")
        else:
            record[j['id']] = verified(j, out)
    return [record[j['id']] for j in jobs]


# ------------------------------------------------------------------ the differential lane
# Seeded rows (vm/core/seeded.json) and a generated corpus (vm/lane.py) run through vm.wasm and the
# reference evaluation, which must agree on stdout, outcome, cause and calls. A fixed sample also runs
# through the seed's native lane, and its bytes are frozen (D7; vm/core/lane.json).
SEED_BIN = ROOT / 'scripts/bend-reference'
SEEDED = HERE / 'core/seeded.json'
LANE = HERE / 'core/lane.json'
DEADLINE = 5000  # ms: rows that end in microseconds, run under a mutant that may never end


def book_line(row: dict) -> str:
    """The `Evaluated` line of a Book row with a model tree: main's result type and the root's tag (SPEC section 8)."""
    plan = row['plan']
    main = next(f for f in plan['functions'] if f['name'] == 'main')
    root = re.match(r'[\w.]+', row['tree'])[0]
    tag = [c['name'] for c in plan['types'][main['result']]['constructors']].index(root)
    return f"Evaluated\t{main['result']}\t{tag}\t{row['tree']}\n"


def foreign_ids(node) -> set:
    """Every foreign id a plan applies: the VM performs only IO.print (CORE.md choice 2) and refuses an image with another."""
    if isinstance(node, list):
        found = {node[2]} if len(node) > 3 and node[0] == 'foreign' and isinstance(node[2], int) else set()
        return found.union(*(foreign_ids(k) for k in node if isinstance(k, list)))
    if isinstance(node, dict):
        return set().union(*(foreign_ids(v) for v in node.values()))
    return set()


def book_result(plan: dict, argv: list) -> tuple[dict, dict]:
    got = reference.book(plan, argv[0], [codec.decimal(w) for w in argv[2:]], codec.decimal(argv[1]))
    run = {'stderr': '', **got} if 'exit' in got else got
    return expected_run(run), {**expected_dump(run), 'calls': got['calls']}


def reference_result(plan: dict, argv: list) -> tuple[dict, dict]:
    """(host run, outcome registers) that SPEC sections 4 and 8 and vm/evaluate.py give for `IMAGE argv`: the argument
    checks first, then the evaluation of a Book or a Program. Two readings stand in for what the evaluation does not
    model, each a documented behaviour of the VM: an image with a foreign leaf other than IO.print is `Unsupported vm
    foreign` before any entry (choice 2), and a Halt whose message holds a non-scalar Char is refused as `io abi`
    (CORE.md, open for vm-io)."""
    bad = codec.arguments(plan, argv)
    if bad:
        outcome, cause = bad.split(' ', 1)
        case = {'outcome': outcome, 'cause': cause}
        return expected_run(case), expected_dump(case)
    if foreign_ids(plan['functions']) - {1}:
        case = {'outcome': 'Unsupported', 'cause': 'vm foreign'}
        return expected_run(case), expected_dump(case)
    if plan['entry'] == 'book':
        return book_result(plan, argv)
    got = reference.program(plan, codec.decimal(argv[0]))
    written = got['stdout'].decode()
    if 'halt' in got:
        message = got['message']
        if all(map(reference.scalar, message)):
            return ({'exit': got['halt'] % 256, 'stdout': written, 'stderr': b''.join(map(reference.utf8, message)).decode() + '\n'},
                    {'outcome': 'Halted', 'calls': got['calls']})
        return {'exit': 5, 'stdout': written, 'stderr': 'HostFailure\tio\tabi\n'}, {'outcome': 'HostFailure', 'cause': 'abi', 'calls': got['calls']}
    case = {'exit': 0, 'stdout': written, 'stderr': ''} if 'exit' in got else {**got, 'stdout': written}
    return expected_run(case), {**expected_dump(case), 'calls': got['calls']}


def disagreement(plan: dict, argv: list, out: dict) -> str | None:
    """None where the test build's run `out` equals the reference's in stdout, exit, stderr, outcome, cause and calls."""
    run, dump = reference_result(plan, argv)
    if not clean(out) or shown(out, run) != run:
        return f"the VM ran {shown(out, run)} ({out['status']}), the reference {run}"
    wrong = {k: (out['state'][k], v) for k, v in dump.items() if out['state'][k] != v}
    return f'registers (VM, reference) {wrong}' if wrong else None


def seeded_expectation(row: dict) -> tuple[dict, dict]:
    """A seeded row's frozen run: its model tree's `Evaluated` line or its literal refusal, with the reference's calls."""
    if 'refusal' in row:
        return expected_run(row['refusal']), {**expected_dump(row['refusal']), 'calls': row['calls']}
    return ({'exit': 0, 'stdout': book_line(row), 'stderr': ''},
            {'outcome': 'Completed', 'calls': reference_run(row['plan'], lane.FUEL)[1]['calls']})


def seed_native(rows: list, where: Path) -> dict:
    """The pinned seed's native lane on each row's source: {name: {exit, stdout, stderr}}. A row the seed cannot build
    fails the gate; it is never skipped."""
    def one(row):
        source, exe = where / f"{row['name']}.bend", where / f"{row['name']}.exe"
        source.write_text(row['source'])
        for _ in range(5):  # macOS's clang shim intermittently prints nothing under load, which the seed reports as no clang
            built = subprocess.run([str(SEED_BIN), str(source), '-o', str(exe)], cwd=ROOT, capture_output=True,
                                   env={**os.environ, 'BEND_NO_TELEMETRY': '1'}, timeout=900 * SCALE)
            if built.returncode == 0 or b'found no clang' not in built.stderr:
                break
            time.sleep(1)
        require(built.returncode == 0, f"seed native build of {row['name']}: {built.stderr.decode()[-300:]}")
        ran = subprocess.run([str(exe)], capture_output=True, timeout=120 * SCALE)
        return {'exit': ran.returncode, 'stdout': ran.stdout.decode(), 'stderr': ran.stderr.decode()}
    where.mkdir(parents=True, exist_ok=True)
    return dict(zip([r['name'] for r in rows], pool(one, rows, workers=6)))


def seed_tree(seen: dict) -> str:
    """A Book's tree as the seed printed it, in SPEC section 8's spelling: the printed value without spaces."""
    return seen['stdout'].strip().replace(' ', '')


def lane_rows(cfg: dict) -> list:
    """Every row of the lane: the seeded and ill-typed rows (`frozen`), sweeps, writers, random key Cases, programs."""
    frozen = [*lane.seeded(), *lane.ill_typed()]
    for r in frozen:
        r['frozen'] = True
    rows = [*frozen, *lane.inspection_items(), *lane.sweep_items(), *lane.print_items(), *lane.digit_items(), *lane.display_items(),
            *(lane.random_keys(i, cfg['seed']) for i in range(cfg['keys'])),
            *(lane.program(i, cfg['seed']) for i in range(cfg['programs']))]
    names = [r['name'] for r in rows]
    require(len(set(names)) == len(names), 'the lane rows have distinct names')
    return rows


def sample_rows(rows: list, cfg: dict) -> list:
    """The fixed sample the seed runs: rows of each family with a Bend source, spread evenly, never a seeded row."""
    out = []
    for family, count in cfg['sample'].items():
        pool_ = [r for r in rows if r['family'] == family and r['source'] and not r.get('frozen')]
        out += [pool_[i * len(pool_) // count] for i in range(count)]
    return out


def lane_job(row: dict, wasm: Path, where: Path, trace=None) -> dict:
    return {'id': row['name'], 'wasm': str(wasm), 'files': {row['file']: str(where / row['file'])},
            'argv': [row['file'], *row['argv']], **({'trace': trace} if trace else {})}


def check_lane(cfg: dict, seeded: dict, module: Path, test: Path, where: Path, reg: dict, digest: bytes) -> tuple[dict, list]:
    """The lane rows through the test build and the production module, each compared with the reference evaluation
    (and a model tree, where the row has one); the seeded rows with their frozen source, image, seed bytes, run and
    registers, also on the real host; the sample with the seed's native lane run again. Returns the receipt's record
    and the rows, each with its image, for the mutant groups."""
    rows = lane_rows(cfg)
    where.mkdir()
    for r in rows:
        r['image'], r['file'] = codec.encode(r['plan'], digest), f"{r['name']}.kimg"
        (where / r['file']).write_bytes(r['image'])
    refused = [r['name'] for r in rows if spec.rejected(r['image'], reg, digest) is not None]
    require(not refused, f'the reference codec refuses lane rows: {refused[:5]}')
    frozen = {r['name']: r for r in seeded['rows']}
    fixed = {r['name']: r for r in rows if r.get('frozen')}
    require(sorted(frozen) == sorted(fixed), f'seeded rows {sorted(frozen)} vs the lane {sorted(fixed)}')
    sample = sample_rows(rows, cfg)
    audited = set(fixed) | {r['name'] for r in sample}
    ran = harness([lane_job(r, test, where, 'audit' if r['name'] in audited else None) for r in rows], timeout=1800)
    made = harness([lane_job(r, module, where) for r in rows], timeout=1800)
    tally, failures = {}, []
    for r in rows:
        out, prod = ran[r['name']], made[r['name']]
        why = disagreement(r['plan'], r['argv'], out)
        if why is None and (prod['exit'], prod['stdout'], prod['stderr']) != (out['exit'], out['stdout'], out['stderr']):
            why = f"vm.wasm ran {(prod['exit'], prod['stdout'][:60], prod['stderr'])}, the test build {(out['exit'], out['stdout'][:60], out['stderr'])}"
        if why is None and out['broken'] is not None:
            why = f"state audit {out['broken']}"
        if why is None and r.get('tree') is not None and reference_result(r['plan'], r['argv'])[0]['stdout'] != book_line(r):
            why = f"the model tree gives {book_line(r)!r}, the reference {reference_result(r['plan'], r['argv'])[0]['stdout']!r}"
        if why:
            failures.append(f"{r['name']}: {why}")
        state = out['state']
        seen = tally.setdefault(r['family'], {'rows': 0, 'outcomes': {}})
        seen['rows'] += 1
        key = (state['outcome'] or out['status']) + (f":{state['cause']}" if state['cause'] else '')  # a trap has no outcome
        seen['outcomes'][key] = seen['outcomes'].get(key, 0) + 1
    require(not failures, f'{len(failures)} lane rows disagree with the reference, first: {failures[:3]}')

    wanted = {r['name']: r for r in [*fixed.values(), *sample] if r['source']}
    seeds = seed_native(list(wanted.values()), where / 'seed')
    by_name = {r['name']: r for r in rows}
    on_host = dict(zip(sorted(audited), pool(lambda n: host(module, where, [by_name[n]['file'], *by_name[n]['argv']]), sorted(audited))))
    for name in sorted(fixed):
        r, f = fixed[name], frozen[name]
        require(r['source'] == f['source'] and sha((r['source'] or '').encode()) == f['source_sha256'],
                f'seeded {name}: the source differs from the frozen one')
        require(sha(r['image']) == f['image_sha256'], f'seeded {name}: the image differs from the frozen one')
        run, dump = seeded_expectation(r)
        require((run, dump) == (f['expect'], f['dump']), f"seeded {name}: frozen {f['expect']} {f['dump']}, derived {run} {dump}")
        require(on_host[name] == f['expect'], f"seeded {name}: the real host shows {on_host[name]}, frozen {f['expect']}")
        require(all(ran[name]['state'][k] == v for k, v in f['dump'].items()), f"seeded {name}: registers {ran[name]['state']} vs {f['dump']}")
        if f['seed'] is None:
            require(r['source'] is None, f'seeded {name} has a source but no frozen seed run')
        else:
            require(seeds[name] == f['seed'], f"seeded {name}: the seed now gives {seeds[name]}, frozen {f['seed']}")
            require(seed_tree(f['seed']) == r['tree'], f'seeded {name}: the seed prints another tree than the model')
    frozen_sample = {r['name']: r for r in cfg['sample_rows']}
    require(sorted(frozen_sample) == sorted(r['name'] for r in sample), 'the frozen sample is the one the configuration picks')
    for r in sample:
        f, seen, out = frozen_sample[r['name']], seeds[r['name']], ran[r['name']]
        require(sha(r['source'].encode()) == f['source_sha256'], f"sample {r['name']}: the source differs from the frozen one")
        require(seen == f['seed'], f"sample {r['name']}: the seed now gives {seen}, frozen {f['seed']}")
        got = out['stdout'].rstrip('\n').split('\t', 3)[3] if r['plan']['entry'] == 'book' else None
        require((got == seed_tree(seen)) if got is not None else
                ((out['exit'], out['stdout'], out['stderr']) == (seen['exit'], seen['stdout'], seen['stderr'])),
                f"sample {r['name']}: the VM gives {out['stdout'][:80]!r} (exit {out['exit']}), the seed {seen}")
        require((on_host[r['name']]['exit'], on_host[r['name']]['stdout']) == (out['exit'], out['stdout']), f"sample {r['name']}: the real host differs")
    record = {'seed': cfg['seed'], 'rows': len(rows), 'corpus_sha256': sha(json.dumps([sha(r['image']) for r in rows]).encode()),
              'families': tally, 'seeded': sorted(fixed), 'on_real_host': len(on_host),
              'sample': {'rows': len(sample), 'seed_bytes_sha256': sha(json.dumps([frozen_sample[r['name']]['seed'] for r in sample],
                                                                                     sort_keys=True).encode())}}
    return record, rows


def lane_groups(rows: list, where: Path) -> dict:
    """Mutant groups from the lane rows: each job's expectation is the reference evaluation's, which check_lane
    showed equal to the frozen and model ones. `keys` holds the seeded key Cases and the first random ones,
    `describe` the wide constructors, `tags` the tag Cases and the edges of section 6.1's inspection."""
    def job(r, deadline=20_000):
        want, dump = reference_result(r['plan'], r['argv'])
        return {'id': f"lane:{r['name']}", 'files': {r['file']: str(where / r['file'])}, 'argv': [r['file'], *r['argv']],
                'want': want, 'dump': dump, 'deadline': deadline}
    keys = [r for r in rows if r['family'] == 'keys']
    fixed = [r for r in keys if r.get('frozen')]
    return {'keys': [job(r) for r in fixed + [r for r in keys if not r.get('frozen')][:24]],
            'describe': [job(r) for r in rows if r['family'] == 'wide'],
            'display': [job(r) for r in rows if r['family'] == 'display'],
            'inspection': [job(r) for r in rows if r['family'] == 'inspection'],
            'tags': [job(r) for r in rows if r['family'] in ('tags', 'ill-typed')],
            'sweeps': [job(r) for r in rows if r['family'] == 'sweep'],
            'writers': [job(r) for r in rows if r['family'] in ('print', 'halt', 'digits', 'nat')],
            'programs': [job(r) for r in rows if r['family'] == 'program' or (r['family'] == 'keys' and not r.get('frozen'))],
            'hang': [job(r, 3_000) for r in fixed]}


STUDY = HERE / 'receipts/study.json'
STUDY_ORDER = ['keys', 'describe', 'tags', 'display', 'inspection', 'goldens', 'invocations', 'runs', 'reference', 'sweeps', 'writers',
               'fuzz-admitted', 'programs', 'fixtures', 'dumps', 'limited', 'memory-end', 'scope', 'controls']  # cheap and telling first
HEAVY = ['ceiling']  # about 4 GiB a row: only a study's survivors run them (`--heavy`)
GUARD = {'fixtures': 120_000, 'limited': 120_000, 'programs': 120_000, 'ceiling': 600_000, 'full-heap': 600_000,
         'trap': 600_000, 'growth': 600_000, 'refused': 600_000, 'scope': 5_000}  # ms a row may take before it is stopped, else 30,000


BASELINE = ['keys', 'describe', 'tags', 'display', 'inspection', 'sweeps', 'writers', 'programs', 'hang', 'fuzz-admitted', 'dumps', 'scope']


def deadline(job: dict, group: str) -> int:
    """Milliseconds a mutant row may run: its own, or its group's, scaled like every hang guard of the gate."""
    return int((job.get('deadline') or GUARD.get(group, 30_000)) * SCALE)


def check_baseline(groups: dict, test: Path):
    """The groups of the lane, the mutated goldens and the dump rows are built apart from the checks that froze them, so
    the unmutated test build must show nothing wrong on any of them: a group that kills every mutant, this one included,
    kills none."""
    for group in BASELINE:
        jobs = groups[group]
        batch = [{**{k: v for k, v in j.items() if k not in ('want', 'dump', 'at_most')}, 'wasm': str(test),
                  'deadline': deadline(j, group)} for j in jobs]
        out = harness(batch, timeout=1800)
        wrong = [j['id'] for j in jobs if not clean(out[j['id']]) or observed_wrong(j, out[j['id']])]
        require(not wrong, f'group {group}: the unmutated VM is wrong on {len(wrong)} of {len(jobs)} rows, first {wrong[:3]}')


def run_group(batch: list, group: str) -> dict:
    """A group's jobs on the test build: rows that touch about 4 GiB each get a process of their own, two at a time."""
    if group in ('ceiling', 'full-heap', 'trap'):
        return {k: v for part in pool(lambda j: harness([j], timeout=1200), batch, workers=2) for k, v in part.items()}
    return harness(batch, timeout=1200, max_timeouts=1)


def run_study(groups: dict, source: str, args: list) -> int:
    """Each systematic mutant of vm/study.py against the gate's own rows, group by group in STUDY_ORDER, until a row
    shows a wrong observation (the gate's `observed_wrong`) or outlives its deadline (a hang). A mutant no row
    kills must be explained in `study.EQUIVALENT`, and each explanation must name a survivor. Writes vm/receipts/study.json."""
    workers = int(args[args.index('--jobs') + 1]) if '--jobs' in args else 6
    only = args[args.index('--only') + 1] if '--only' in args else ''
    mutants = [m for m in study.mutants(source) if only in m[0]]
    started = time.monotonic()

    def strike(item, order=STUDY_ORDER):
        index, mutant = item
        row = {'mutant': mutant[0]}
        wasm = BUILD / f'study-{index}.wasm'
        try:
            wasm.write_bytes(build.assemble(build.test_source(study.apply(source, mutant))))
        except subprocess.CalledProcessError:
            return {**row, 'result': 'unassemblable'}
        unclean = None  # the first hang or trap: it kills only if no row shows a clean wrong observation
        for group in order:
            jobs = groups[group]
            batch = [{**{k: v for k, v in j.items() if k not in ('want', 'dump', 'at_most')}, 'wasm': str(wasm),
                      'deadline': deadline(j, group)} for j in jobs]
            try:
                out = run_group(batch, group)
            except AssertionError as failure:
                return {**row, 'result': 'crashed', 'group': group, 'by': str(failure)[-120:]}
            wrong = [j['id'] for j in jobs if clean(out[j['id']]) and observed_wrong(j, out[j['id']])]
            if wrong:
                return {**row, 'result': 'killed', 'group': group, 'by': wrong[0]}
            if unclean is None:
                for result, states in (('hang', ('Timeout',)), ('trap', ('Trap', 'HostStack'))):
                    ids = [j['id'] for j in jobs if out[j['id']]['status'] in states]
                    if ids:
                        unclean = {**row, 'result': result, 'group': group, 'by': ids[0]}
                        break
        return unclean or {**row, 'result': 'survived'}
    rows = pool(strike, list(enumerate(mutants)), workers=workers)
    if '--heavy' in args:  # what the rows of about 4 GiB add, for the survivors only
        again = [(i, m) for (i, m), r in zip(enumerate(mutants), rows) if r['result'] == 'survived']
        for (i, _), r in zip(again, pool(lambda item: strike(item, HEAVY), again, workers=max(1, workers // 3))):
            rows[i] = {**r, 'heavy': True}
    tally = {}
    for r in rows:
        tally[r['result']] = tally.get(r['result'], 0) + 1
    survivors = [r['mutant'] for r in rows if r['result'] == 'survived']
    unexplained = [m for m in survivors if m not in study.EQUIVALENT]
    stale = [m for m in study.EQUIVALENT if m not in survivors and not only]
    by_group = {}  # result -> the group of its first wrong observation, hang or trap -> mutants
    for r in rows:
        if 'group' in r:
            first = by_group.setdefault(r['result'], {})
            first[r['group']] = first.get(r['group'], 0) + 1
    receipt = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'vm_wat_sha256': sha(source.encode()),
               'mutants': len(rows), 'tally': tally, 'by_group': by_group,
               'survivors': [{'mutant': m, 'reason': study.EQUIVALENT.get(m)} for m in survivors],
               'elapsed_seconds': round(time.monotonic() - started), 'rows': rows}
    if not only:
        STUDY.write_text(json.dumps(receipt, indent=1) + '\n')
    print(f"study: {len(rows)} mutants, {tally}; {len(survivors)} survivors, {len(unexplained)} unexplained, {len(stale)} stale explanations")
    for m in unexplained:
        print('  unexplained survivor:', m)
    for m in stale:
        print('  explained but not a survivor:', m)
    return 1 if unexplained or stale else 0


LANE_RULE = ("Parameters of the differential lane (vm/lane.py) and the frozen sample the seed's native lane runs: `sample` "
             "counts the rows of each family (with a Bend source, never a seeded row) spread evenly through the corpus, and "
             "`sample_rows` freeze each one's source hash and the seed's exit, stdout and stderr. Regenerate with "
             "`python3 vm/check-core.py --freeze`.")
SEEDED_RULE = ("Rows whose expected results the pinned seed's native lane fixed (D7), written by `--freeze` before the VM ran "
               "them: the seed's bytes, the model tree they must equal, the source, the image and the run they give "
               "the VM (SPEC section 8) with the reference evaluation's calls. A row with no `seed` is by literal review: "
               "the seed cannot spell its Char keys, and types every program.")
DEFAULT_LANE = {'schema': 1, 'rule': LANE_RULE, 'seed': 20260929, 'programs': 2000, 'keys': 200,
                'sample': {'program': 40, 'keys': 12, 'sweep': 12, 'print': 10, 'halt': 10}, 'sample_rows': []}


def freeze() -> int:
    """Write vm/core/seeded.json and vm/core/lane.json from the seed's native lane (D7): its bytes are the expectation."""
    cfg = json.loads(LANE.read_text()) if LANE.exists() else DEFAULT_LANE
    reg = codec.registry()
    digest = codec.base_digest(reg)
    rows = lane_rows(cfg)
    for r in rows:
        r['image'] = codec.encode(r['plan'], digest)
    fixed, sample = [r for r in rows if r.get('frozen')], sample_rows(rows, cfg)
    where = BUILD / 'freeze'
    if where.exists():
        shutil.rmtree(where)
    seeds = seed_native([r for r in {r['name']: r for r in [*fixed, *sample] if r['source']}.values()], where)
    seeded = []
    for r in fixed:
        run, dump = seeded_expectation(r)
        require(r['source'] is None or seed_tree(seeds[r['name']]) == r['tree'], f"seeded {r['name']}: the seed prints another tree than the model")
        seeded.append({'name': r['name'], 'family': r['family'], 'basis': r['basis'], 'source': r['source'],
                       'source_sha256': sha((r['source'] or '').encode()), 'image_sha256': sha(r['image']),
                       'seed': seeds.get(r['name']), 'expect': run, 'dump': dump})
    SEEDED.write_text(json.dumps({'schema': 1, 'rule': SEEDED_RULE, 'rows': seeded}, indent=1) + '\n')
    cfg = {**cfg, 'rule': LANE_RULE, 'sample_rows': [{'name': r['name'], 'source_sha256': sha(r['source'].encode()), 'seed': seeds[r['name']]}
                                                      for r in sample]}
    LANE.write_text(json.dumps(cfg, indent=1) + '\n')
    print(f'froze {len(seeded)} seeded rows ({sum(1 for s in seeded if s["seed"])} with seed bytes) and a sample of {len(sample)}')
    return 0


# ------------------------------------------------------------------ the validator's scope tables
SCOPE_STACK = 1 << 29  # bytes of host stack, and (below) the recursion limit, for the reference codec on images 20,000 Closures deep


def deep(fn):
    """`fn()` on a thread with a large stack and recursion limit: the plan builders, the encoder and the reference codec
    recurse once per node, and the scope images nest tens of thousands of Closures inside one another."""
    out = {}

    def run():
        try:
            out['value'] = fn()
        except BaseException as error:  # noqa: BLE001 -- handed back to the caller's thread
            out['error'] = error
    limit, size = sys.getrecursionlimit(), threading.stack_size()
    sys.setrecursionlimit(2_000_000)
    threading.stack_size(SCOPE_STACK)
    try:
        thread = threading.Thread(target=run)
        thread.start()
        thread.join()
    finally:
        sys.setrecursionlimit(limit)
        threading.stack_size(size)
    if 'error' in out:
        raise out['error']
    return out['value']


def scope_expected(reference: str | None, plan: dict) -> tuple[dict, dict]:
    """(host run, outcome registers) of an image the reference codec judged `reference`: its Book's run under the reference
    evaluation when it admits it, else the refusal, or for a limit of section 4 the exhaustion, that names its first defect."""
    if reference is None:
        return reference_run(plan, 1000)
    code = expected_reason(reference)
    case = {'outcome': 'Exhausted', 'kind': 2, 'cause': code} if code.startswith('Exhausted 2 ') else {'outcome': 'HostFailure', 'cause': f'image {code}'}
    return expected_run(case), refusal_dump(code)


def check_scope(section: dict, module: Path, test: Path, where: Path, reg: dict, digest: bytes) -> tuple[dict, list]:
    """The validator's scope tables at the depths where they grow (CORE.md choice 16; vm/scope.py). The frozen rows: each image
    is rebuilt, and its words, `need` and SHA-256 must be the frozen ones, the reference codec's verdict and the reference
    evaluation's run the frozen ones (fixed before the VM changed, D7), and the VM, on the real host and in the test build, must
    show them. Then a seeded corpus of such images, most with one small change, where the VM must judge each as the reference
    codec does: the same first defect, or the same run, and no trap. Returns the receipt's record and the rows for the mutant
    group `scope`."""
    where.mkdir()
    words = lambda plan: len(codec.encode(plan, digest)) // 4
    cfg = section['corpus']

    def judged(plan, label):
        image = codec.encode(plan, digest)
        reference = verdict(image, label, reg, digest)
        return image, reference, scope_expected(reference, plan)

    def stopped(plan, image):
        """A `resource` row: valid by construction, but its tables need more scratch than 4 GiB holds (`scope.scratch`), so the VM
        stops it as Exhausted kind 2, cause `heap`. The reference codec is not run on it: its recursion would hold thousands of scopes."""
        require(scope.scratch(scope.need(plan), len(image) // 4) > 0xfffff000, 'a resource row needs more scratch than 4 GiB holds')
        case = {'outcome': 'Exhausted', 'kind': 2, 'cause': 'heap'}
        return image, None, (expected_run(case), expected_dump(case))

    def prepare():
        frozen = [(row, plan, *(stopped(plan, codec.encode(plan, digest)) if row.get('resource') else judged(plan, f"scope {row['name']}")))
                  for row in section['rows'] for plan in [scope.build(row)]]
        made = [(name, plan, change, *judged(plan, f'scope corpus {name}'))
                for name, plan, change in scope.corpus(cfg['seed'], cfg['images'], words, lane.Rng)]
        return frozen, made
    frozen, made = deep(prepare)
    failures = []
    for row, plan, image, reference, expected in frozen:
        name = row['name']
        got = {'words': len(image) // 4, 'need': scope.need(plan), 'sha256': sha(image)}
        if 'tables' in row:
            got['edge'] = got['need'] - (got['words'] + scope.CAPACITY) * (1 << row['tables'])
        elif 'unit' in row:
            got['delta'] = got['words'] + scope.CAPACITY - row['unit']
        failures += [f'{name}: the generator gives {k} {v}, frozen {row[k]}' for k, v in got.items() if row[k] != v]
        if reference != row['reference']:
            failures.append(f"{name}: the reference codec gives {reference!r}, frozen {row['reference']!r}")
        elif expected != (row['expect'], row['dump']):
            failures.append(f"{name}: frozen {row['expect']} {row['dump']}, the reference gives {expected}")
        (where / f'{name}.kimg').write_bytes(image)
    argv = lambda name: [f'{name}.kimg', 'main', '1000']
    job = lambda name, wasm, trace=None: {'id': name, 'wasm': str(wasm), 'files': {f'{name}.kimg': str(where / f'{name}.kimg')},
                                          'argv': argv(name), **({'trace': trace} if trace else {})}
    ran = pool(lambda r: host(module, where, argv(r[0]['name'])), frozen)
    traced = harness([job(r[0]['name'], test, 'audit') for r in frozen], timeout=600)
    rows = []
    for (row, plan, image, reference, expected), on_host in zip(frozen, ran):
        out = traced[row['name']]
        seen = {k: out['state'][k] for k in row['dump']}
        seen_more = {k: out['state'][k] for k in row.get('at_most', {})}
        if seen_more and any(v > row['at_most'][k] for k, v in seen_more.items()):
            failures.append(f"{row['name']}: the test build's {seen_more} exceeds the frozen bound {row['at_most']}")
        if on_host != row['expect'] or not clean(out) or shown(out, row['expect']) != row['expect'] or seen != row['dump'] or out['broken'] is not None:
            failures.append(f"{row['name']}: the real host shows {(on_host['exit'], on_host['stdout'][:40], on_host['stderr'].strip())}, the test build "
                            f"{(out['exit'], out['stdout'][:40], out['stderr'].strip(), seen, out['broken'])}; frozen {row['expect']} {row['dump']}")
        rows.append({'name': row['name'], 'words': len(image) // 4, 'need': scope.need(plan), 'sha256': sha(image),
                     'reference': 'resource' if row.get('resource') else 'admitted' if reference is None else expected_reason(reference),
                     'exit': on_host['exit']})
    require(not failures, f'{len(failures)} of {len(frozen)} frozen scope rows differ: ' + '; '.join(failures[:30]))

    corpus, reasons, grown = [], {}, 0
    for name, plan, change, image, reference, expected in made:
        (where / f'{name}.kimg').write_bytes(image)
        corpus.append({'label': name, 'sha256': sha(image), 'reference': reference, 'argv': argv(name), 'plan': plan, 'expected': expected})
        grown += scope.need(plan) > len(image) // 4 + scope.CAPACITY
        reason = 'admitted' if reference is None else expected_reason(reference)
        reasons[reason] = reasons.get(reason, 0) + 1
    seen = harness([job(r['label'], test, 'yields') for r in corpus], timeout=900)
    in_module = harness([job(r['label'], module) for r in corpus], timeout=900)
    tally = compare('scope corpus', corpus, seen)
    for r in corpus:
        g, prod = seen[r['label']], in_module[r['label']]
        require((prod['exit'], prod['stdout'], prod['stderr']) == (g['exit'], g['stdout'], g['stderr']),
                f"scope corpus {r['label']}: vm.wasm ran {(prod['exit'], prod['stderr'])}, the test build {(g['exit'], g['stderr'])}")
        run, dump = r['expected']
        require(shown(g, run) == run and all(g['state'][k] == v for k, v in dump.items()),
                f"scope corpus {r['label']}: the VM ran {shown(g, run)} {g['state']}, the reference codec and evaluation give {run} {dump}")
    require(grown >= len(corpus) // 4 and tally['accepted'] >= len(corpus) // 10 and len(reasons) >= 6,
            f'the corpus is too uniform: {grown} of {len(corpus)} images grow the tables, {tally["accepted"]} are admitted, reasons {reasons}')
    record = {'rows': rows, 'corpus': {'seed': cfg['seed'], 'images': len(corpus), 'changed': sum(change != 'none' for _, _, change, *_ in made),
                                       'grow_the_tables': grown, 'corpus_sha256': sha(json.dumps([r['sha256'] for r in corpus]).encode()),
                                       'reasons': dict(sorted(reasons.items())), **tally}}
    costs = {row['name']: scope.need(plan) for row, plan, *_ in frozen} | {r['label']: scope.need(r['plan']) for r in corpus}
    jobs = [{'id': f"scope:{row['name']}", 'files': job(row['name'], test)['files'], 'argv': argv(row['name']), 'want': row['expect'],
             'dump': row['dump'], **({'at_most': row['at_most']} if 'at_most' in row else {})} for row, *_ in frozen if not row.get('resource')]
    jobs += [{'id': f"scope:{r['label']}", 'files': job(r['label'], test)['files'], 'argv': r['argv'], 'want': r['expected'][0], 'dump': r['expected'][1]}
             for r in corpus]
    return record, sorted(jobs, key=lambda j: costs[j['id'].removeprefix('scope:')])  # the deepest last: a mutant that stalls on them is stopped there


# ------------------------------------------------------------------ mutants
# (name, what it breaks, [(old, new)], kill group). Each edit must apply once.
MUTANTS = [
    ('arm-selection', 'a tag Case takes the mirrored row',
     [('(local.set $arm (call $w (i32.add (i32.add (local.get $n) (i32.const 7)) (local.get $tag))))',
       '(local.set $arm (call $w (i32.add (i32.add (local.get $n) (i32.const 7)) '
       '(i32.sub (i32.sub (local.get $cnt) (i32.const 1)) (local.get $tag)))))')], 'goldens'),
    ('slot-off-by-one', 'Eval Reference reads the slot below',
     [('(global.set $val (i32.load offset=16 (i32.add (global.get $act) (i32.shl (i32.load offset=4108 (local.get $na)) (i32.const 2)))))',
       '(global.set $val (i32.load offset=12 (i32.add (global.get $act) (i32.shl (i32.load offset=4108 (local.get $na)) (i32.const 2)))))')],
     'goldens'),
    ('fuel', 'entering a Closure is free',
     [('(br_if $bad (i32.ne (global.get $nops) (local.get $live)))\n        (call $debit)',
       '(br_if $bad (i32.ne (global.get $nops) (local.get $live)))')], 'fuel'),
    ('validator-offset', 'name bytes are read one word early',
     [('(local.set $p (i32.add (i32.const 4096) (i32.shl (i32.add (local.get $at) (i32.const 2)) (i32.const 2))))',
       '(local.set $p (i32.add (i32.const 4096) (i32.shl (i32.add (local.get $at) (i32.const 1)) (i32.const 2))))')],
     'controls'),
    ('quantum-state-loss', 'a yield after an effect commits the Action as still pending',
     [('(local.set $r (call $perform (local.get $x)))',
       '(local.set $r (call $perform (local.get $x)))\n'
       '      (if (i32.eq (global.get $quantum) (i32.const 65536)) (then (return)))')], 'quantum'),
    ('nat-bound', 'Succ of 2^32-1 wraps instead of NatRange',
     [('(if (i32.eq (local.get $v) (i32.const -1)) (then (call $exhaust (i32.const 2) (global.get $R_nat_range))))', '')],
     'goldens'),
    ('tail-release', 'no entry is a tail entry',
     [('(if (i32.or (i32.eqz (local.get $k)) (i32.eq (local.get $k) (i32.const 4)))',
       '(if (i32.const 0)')], 'fixtures'),
    ('rem-zero', 'x % 0 is 0',
     [('(then (i32.rem_u (local.get $x) (local.get $y))) (else (local.get $x))',
       '(then (i32.rem_u (local.get $x) (local.get $y))) (else (i32.const 0))')], 'goldens'),
    ('host-stack-recursion', 'the pair memo rehashes by calling itself',
     [('(then (drop (call $pairslot (i32.sub', '(then (drop (call $entered (i32.sub')], 'shape'),
    # vm-spec 5f9a0fd: a none slot, every u32 String code, and D20's refusal in the VM
    ('none-slot-refused', 'a Case on a none-typed slot is refused at load',
     [('(i32.and (i32.ne (local.get $x) (local.get $y)) (i32.ne (local.get $x) (i32.const -1)))',
       '(i32.ne (local.get $x) (local.get $y))')], 'controls'),
    ('string-code-refused', 'a String constant whose first code is above U+10FFFF is refused at load',
     [('          (then (call $refuse (global.get $R_scalar_constant_width))))\n',
       '          (then (call $refuse (global.get $R_scalar_constant_width))))\n'
       '        (if (i32.and (i32.eq (local.get $kind) (i32.const 3)) (i32.ne (local.get $nw) (i32.const 0)))\n'
       '          (then (if (i32.gt_u (call $w (i32.add (local.get $at) (i32.const 3))) (i32.const 0x10ffff))\n'
       '            (then (call $refuse (global.get $R_constant_record))))))\n')], 'goldens'),
    ('surrogate-left-to-host', 'a surrogate reaches the host call, which refuses it in the VM\'s place',
     [('(i32.eq (i32.and (local.get $c) (i32.const 0xfffff800)) (i32.const 0xd800))', '(i32.const 0)')], 'goldens'),
    # review round 2: describe near 4 GiB
    ('display-reservation', 'describe demands its whole 16 MiB text window below 4 GiB',
     [('(local.set $end (i64.add (global.get $out) (local.get $upto)))',
       '(local.set $end (i64.add (global.get $out) (i64.add (local.get $upto) (i64.const 0x1000000))))')],
     'ceiling'),
    # vm-spec 94bc3d5: section 7's operand check and section 8's invocation walk
    ('closure-operand-count', 'a Closure is entered whatever its operand count',
     [('(br_if $bad (i32.ne (global.get $nops) (local.get $live)))', '')], 'runs'),
    ('terminal-operand-count', 'the terminal continuation is entered whatever its operand count',
     [('(br_if $bad (i32.ne (global.get $nops) (i32.const 1)))', '')], 'runs'),
    ('operand-check-after-debit', "a Closure's operand count is checked after its fuel",
     [('(br_if $bad (i32.ne (global.get $nops) (local.get $live)))\n        (call $debit)',
       '(call $debit)\n        (br_if $bad (i32.ne (global.get $nops) (local.get $live)))')], 'runs'),
    ('invocation-arity-first', 'the ordinal count is checked before the walk',
     [('(local.set $k (i32.sub (global.get $argc) (i32.const 3)))',
       '(local.set $k (i32.sub (global.get $argc) (i32.const 3)))\n'
       '    (if (i32.ne (local.get $k) (local.get $n))\n'
       '      (then (call $stop (i32.const 3) (i32.const 5) (i32.const 160) (global.get $R_argument_arity))))')],
     'invocations'),
    ('function-argument-dropped', 'an arrow parameter is refused as argument-range',
     [('        (if (i32.lt_u (i32.sub (call $kind (local.get $p)) (i32.const 1)) (i32.const 2))\n'
       '          (then (call $stop (i32.const 3) (i32.const 5) (i32.const 160) (global.get $R_function_argument))))\n',
       '')], 'invocations'),
    # vm-spec 8ef906e: every arm fits its Case; section 8's display visit and inclusive bounds
    ('arm-exact-type', "a Branch's body must have exactly its Case's type",
     [('(if (i32.eqz (call $fits (call $nodetype (local.get $a)) (call $nodetype (call $w (i32.add (local.get $b) (i32.const 6))))))',
       '(if (i32.ne (call $nodetype (call $w (i32.add (local.get $b) (i32.const 6)))) (call $nodetype (local.get $a)))')],
     'controls'),
    ('default-exact-type', "a Default's body must have exactly its Case's type",
     [('(if (i32.eqz (call $fits (call $nodetype (local.get $a)) (call $nodetype (call $w (i32.add (local.get $b) (i32.const 3))))))',
       '(if (i32.ne (call $nodetype (call $w (i32.add (local.get $b) (i32.const 3)))) (call $nodetype (local.get $a)))')],
     'controls'),
    ('nat-succ-named-zero', "a Nat's successor is spelled with its zero's name",
     [('(local.set $succ (call $w (i32.add (call $ctor (local.get $t) (i32.const 1)) (i32.const 3))))',
       '(local.set $succ (call $w (i32.add (call $ctor (local.get $t) (i32.const 0)) (i32.const 3))))')], 'runs'),
    ('nat-text-sized-by-zero', "a Nat's text is sized by its zero's name, not its successor's",
     [('(i64.extend_i32_u (i32.add (call $w (i32.add (local.get $succ) (i32.const 1))) (i32.const 2)))',
       '(i64.extend_i32_u (i32.add (call $w (i32.add (local.get $zero) (i32.const 1))) (i32.const 2)))')], 'runs'),
    ('nat-one-visit', 'a Nat word costs one visit',
     [('(local.set $visits (i32.add (i32.add (local.get $visits) (local.get $v)) (i32.const 1)))',
       '(local.set $visits (i32.add (local.get $visits) (i32.const 1)))'),
      ('(i64.add (i64.add (i64.extend_i32_u (local.get $visits)) (i64.extend_i32_u (local.get $v))) (i64.const 1))',
       '(i64.add (i64.extend_i32_u (local.get $visits)) (i64.const 1))')], 'runs'),
    ('display-visits-exclusive', 'the visit bound is exclusive',
     [('                            (i64.const 1048576))', '                            (i64.const 1048575))')], 'runs'),
    ('display-bytes-exclusive', 'the text bound is exclusive',
     [('(global.set $cap (i32.add (global.get $len) (i32.const 0x1000000)))',
       '(global.set $cap (i32.add (global.get $len) (i32.const 0xffffff)))')], 'runs'),
    # review round 3: Chr reads its operand as the reference evaluation's construct does
    ('chr-operand-unchecked', "Chr yields its operand's word without reading it",
     [('            (drop (call $num (i32.load (local.get $ops))))\n', '')], 'reference'),
    # review round 4: a cell or an append block may end exactly at 4 GiB (section 5). These three
    # readings change the outcome at the rows whose heap ends exactly at 4 GiB; `top-trap` below
    # restores the old trap itself
    ('top-cell-exhausted', 'a cell ending exactly at 4 GiB is Exhausted',
     [('(local.set $end (i64.add (global.get $bump) (i64.extend_i32_u (local.get $bytes))))\n'
       '    (if (i64.gt_u (local.get $end) (global.get $HL))',
       '(local.set $end (i64.add (global.get $bump) (i64.extend_i32_u (local.get $bytes))))\n'
       '    (if (i64.ge_u (local.get $end) (global.get $HL))')], 'full-heap'),
    ('top-block-exhausted', 'an append block ending exactly at 4 GiB is Exhausted',
     [('(local.set $end (i64.add (global.get $bump) (i64.shl (i64.extend_i32_u (local.get $n)) (i64.const 5))))\n'
       '    (if (i64.gt_u (local.get $end) (global.get $HL))',
       '(local.set $end (i64.add (global.get $bump) (i64.shl (i64.extend_i32_u (local.get $n)) (i64.const 5))))\n'
       '    (if (i64.ge_u (local.get $end) (global.get $HL))')], 'full-heap'),
    ('bump-wraps', 'the bump pointer wraps to 0 when a cell ends at 4 GiB (a 32-bit bump pointer)',
     [('    (global.set $bump (local.get $end))\n    (local.get $p))',
       '    (global.set $bump (i64.extend_i32_u (i32.wrap_i64 (local.get $end))))\n    (local.get $p))')],
     'full-heap'),
    # vm-spec D17: a Nat Case's predecessor is made after the Branch's Scope push
    ('nat-pred-before-push', "a Nat Case's predecessor is made before its Scope push",
     [('        (drop (call $frame (i32.const 3) (i32.const 0) (local.get $d) (i32.const 0)))\n'
       '        (if (i32.eq (local.get $scr) (global.get $rNat))\n'
       '          (then (local.set $w (call $scalar (i32.sub (local.get $v) (i32.const 1))))))\n',
       '        (if (i32.eq (local.get $scr) (global.get $rNat))\n'
       '          (then (local.set $w (call $scalar (i32.sub (local.get $v) (i32.const 1))))))\n'
       '        (drop (call $frame (i32.const 3) (i32.const 0) (local.get $d) (i32.const 0)))\n')], 'limited'),
    # vm-spec DECISIONS 18: every operand is read over its section 9 extent, a String whole.
    # Each reads less, and exactly as much on a well-typed word; an inspection control kills it
    ('append-b-unread', 'append moves b unread (the old CORE.md choice 3)',
     [('    (drop (call $slen (local.get $b)))\n', '')], 'runs'),
    ('is-empty-reads-one-cell', 'is_empty reads only its head cell (the old CORE.md choice 3)',
     [('(return (call $bool (i32.eqz (call $slen (local.get $a))))))',
       '(return (if (result i32) (i32.eq (local.get $a) (i32.const 1)) (then (i32.const 3))'
       ' (else (drop (call $scell (local.get $a))) (i32.const 1)))))')], 'runs'),
    ('eq-exits-early', 'eq reads both Strings in step and stops at the first difference or either end',
     [('  (func $seq (param $a i32) (param $b i32) (result i32)\n'
       '    (if (i32.ne (call $slen (local.get $a)) (call $slen (local.get $b))) (then (return (i32.const 1))))\n'
       '    (block $done\n'
       '      (loop $next\n'
       '        (br_if $done (i32.eq (local.get $a) (i32.const 1)))\n',
       '  (func $seq (param $a i32) (param $b i32) (result i32)\n'
       '    (block $done\n'
       '      (loop $next\n'
       '        (br_if $done (i32.or (i32.eq (local.get $a) (i32.const 1)) (i32.eq (local.get $b) (i32.const 1))))\n'
       '        (drop (call $scell (local.get $a)))\n'
       '        (drop (call $scell (local.get $b)))\n'),
      ('        (br $next)))\n    (i32.const 3))',
       '        (br $next)))\n    (call $bool (i32.eq (local.get $a) (local.get $b))))')], 'runs'),
    ('move-prims-unread', 'the four conversions move their word unread',
     [('(if (i32.lt_u (local.get $id) (i32.const 34))',
       '(if (i32.and (i32.lt_u (local.get $id) (i32.const 34)) (i32.gt_u (i32.sub (local.get $id) (i32.const 16)) (i32.const 3)))')],
     'runs'),
    # the pre-fix VM itself: both guards restored. Its defect is the trap, so group `trap` kills
    # it only when every row ending exactly at 4 GiB traps and every other ceiling row stays right
    ('top-trap', 'a cell or an append block ending exactly at 4 GiB traps (the pre-fix VM)',
     [('(i64.extend_i32_u (local.get $bytes))))\n    (if (i64.gt_u (local.get $end) (global.get $HL)) (then (call $exhaust (i32.const 2) (global.get $R_heap))))',
       '(i64.extend_i32_u (local.get $bytes))))\n    (if (i64.gt_u (local.get $end) (global.get $HL)) (then (call $exhaust (i32.const 2) (global.get $R_heap))))\n    (if (i64.ge_u (local.get $end) (i64.const 0x100000000)) (then unreachable))'),
      ('(i64.const 5))))\n    (if (i64.gt_u (local.get $end) (global.get $HL)) (then (call $exhaust (i32.const 2) (global.get $R_heap))))',
       '(i64.const 5))))\n    (if (i64.gt_u (local.get $end) (global.get $HL)) (then (call $exhaust (i32.const 2) (global.get $R_heap))))\n    (if (i64.ge_u (local.get $end) (i64.const 0x100000000)) (then unreachable))')], 'trap'),
    # vm-spec cea554a, section 4's limit table: each limit is Exhausted kind 2 with its own cause, inclusive,
    # checked in the order the table gives. Each survives every golden and run control, and dies by a limit
    # control (group `image-limits`) or, where no frozen control holds the boundary, by the limit-word corpus
    ('size-checked-after-length', 'an image above 16 MiB is refused for its length before its size',
     [('        (if (i32.gt_u (local.get $total) (i32.const 0x1000000))\n'
       '          (then (call $io_close (local.get $h))\n'
       '                (call $exhaust (i32.const 2) (global.get $R_image_size))))\n', ''),
      ('      (then (call $refuse (global.get $R_length))))\n',
       '      (then (call $refuse (global.get $R_length))))\n'
       '    (if (i32.gt_u (local.get $total) (i32.const 0x1000000))\n'
       '      (then (call $exhaust (i32.const 2) (global.get $R_image_size))))\n')], 'image-limits'),
    ('record-limit-before-fit', 'the record limit is checked before the count is fitted to the words that remain',
     [('      (if (i32.gt_u (local.get $count) (i32.shr_u (i32.sub (global.get $W) (local.get $at)) (i32.const 1)))\n'
       '        (then (call $refuse (global.get $R_record_count))))\n'
       '      (call $limit (local.get $count) (i32.const 0x100000) (global.get $R_records))\n',
       '      (call $limit (local.get $count) (i32.const 0x100000) (global.get $R_records))\n'
       '      (if (i32.gt_u (local.get $count) (i32.shr_u (i32.sub (global.get $W) (local.get $at)) (i32.const 1)))\n'
       '        (then (call $refuse (global.get $R_record_count))))\n')], 'image-limits'),
    ('arity-limit-before-record', "the arity limit is checked before the function record's length",
     [('        (call $limit (call $w (i32.add (local.get $at) (i32.const 3))) (i32.const 4096) (global.get $R_arity))\n', ''),
      ('        (call $tabset (global.get $tF) (local.get $i) (local.get $at))\n'
       '        (local.set $len (i32.sub (call $w (local.get $at)) (i32.const 1)))\n',
       '        (call $tabset (global.get $tF) (local.get $i) (local.get $at))\n'
       '        (local.set $len (i32.sub (call $w (local.get $at)) (i32.const 1)))\n'
       '        (call $limit (call $w (i32.add (local.get $at) (i32.const 3))) (i32.const 4096) (global.get $R_arity))\n')],
     'image-limits'),
    ('slots-limit-after-exactness', 'the slots limits are checked after the validator\'s exact-slots rule',
     [('        (call $limit (call $w (i32.add (local.get $at) (i32.const 4))) (i32.const 65536) (global.get $R_slots))\n', ''),
      ('        (if (i32.eq (local.get $op) (i32.const 10))\n'
       '          (then (call $limit (call $w (i32.add (local.get $at) (i32.const 5))) (i32.const 65536) (global.get $R_slots))))\n', ''),
      ('            (then (call $refuse (global.get $R_function_slots))))\n',
       '            (then (call $refuse (global.get $R_function_slots))))\n'
       '          (call $limit (call $w (i32.add (local.get $a) (i32.const 4))) (i32.const 65536) (global.get $R_slots))\n'),
      ('              (then (call $refuse (global.get $R_closure_slots))))\n',
       '              (then (call $refuse (global.get $R_closure_slots))))\n'
       '            (call $limit (call $w (i32.add (local.get $a) (i32.const 5))) (i32.const 65536) (global.get $R_slots))\n')],
     'image-limits'),
    ('closure-slots-unlimited', "a Closure's slots have no limit",
     [('        (if (i32.eq (local.get $op) (i32.const 10))\n'
       '          (then (call $limit (call $w (i32.add (local.get $at) (i32.const 5))) (i32.const 65536) (global.get $R_slots))))\n', '')],
     'image-limits'),
    ('function-slots-unlimited', "a function's slots have no limit",
     [('        (call $limit (call $w (i32.add (local.get $at) (i32.const 4))) (i32.const 65536) (global.get $R_slots))\n', '')],
     'image-limits'),
    ('arity-unlimited', 'a function record has no arity limit',
     [('        (call $limit (call $w (i32.add (local.get $at) (i32.const 3))) (i32.const 4096) (global.get $R_arity))\n', '')],
     'image-limits'),
    ('records-unlimited', 'a table has no record limit',
     [('      (call $limit (local.get $count) (i32.const 0x100000) (global.get $R_records))\n', '')], 'image-limits'),
    ('limit-as-malformed', 'a count past its limit is refused as a malformed image',
     [('      (then (call $exhaust (i32.const 2) (local.get $cause)))))\n',
       '      (then (call $refuse (local.get $cause)))))\n')], 'image-limits'),
    ('size-as-malformed', 'an image above 16 MiB is refused as a malformed image',
     [('                (call $exhaust (i32.const 2) (global.get $R_image_size))))\n',
       '                (call $refuse (global.get $R_image_size))))\n')], 'image-limits'),
    ('limit-exclusive', 'a count equal to its limit is past it',
     [('    (if (i32.gt_u (local.get $count) (local.get $max))\n', '    (if (i32.ge_u (local.get $count) (local.get $max))\n')],
     'image-limits'),
    ('size-exclusive', 'an image of exactly 16 MiB is past the size limit',
     [('        (if (i32.gt_u (local.get $total) (i32.const 0x1000000))\n', '        (if (i32.ge_u (local.get $total) (i32.const 0x1000000))\n')],
     'image-limits'),
    ('arity-cause-slots', 'an arity past its limit names slots as its cause',
     [('(i32.const 4096) (global.get $R_arity))', '(i32.const 4096) (global.get $R_slots))')], 'image-limits'),
    ('record-fit-exclusive', 'a count that exactly fills the words that remain is one they cannot hold',
     [('      (if (i32.gt_u (local.get $count) (i32.shr_u (i32.sub (global.get $W) (local.get $at)) (i32.const 1)))\n',
       '      (if (i32.ge_u (local.get $count) (i32.shr_u (i32.sub (global.get $W) (local.get $at)) (i32.const 1)))\n')],
     'limit-words'),
    ('record-fit-one-word', 'a record takes one word of the words that remain, not two',
     [('(i32.shr_u (i32.sub (global.get $W) (local.get $at)) (i32.const 1)))', '(i32.sub (global.get $W) (local.get $at)))')],
     'limit-words'),
    # review round 1, finding 2: growth in 16 MiB steps (CORE.md choice 15). Both keep every outcome; the first is
    # the VM of dcc7c09 and costs time only, so its kill is the test build's memory.grow count, never a timeout
    ('grow-per-page', 'memory grows to exactly the 64 KiB pages a cell needs, one grow per page (the VM of dcc7c09)',
     [('(i64.add (local.get $end) (i64.const 0xffffff)) (i64.const -16777216)',
       '(i64.add (local.get $end) (i64.const 0xffff)) (i64.const -65536)')], 'growth'),
    ('step-refusal-traps', 'a host that refuses the 16 MiB step traps instead of being asked for the size the cell needs',
     [('        (drop (memory.grow (i32.wrap_i64 (i64.shr_u (i64.sub (local.get $to) (local.get $have)) (i64.const 16)))))\n',
       '        (if (i32.lt_s (memory.grow (i32.wrap_i64 (i64.shr_u (i64.sub (local.get $to) (local.get $have)) (i64.const 16)))) (i32.const 0))\n'
       '          (then unreachable))\n')], 'refused'),
    # review round 6, gate adequacy: Case arm selection and describe were pinned only at trivial shapes. Each of the
    # first five passed gate 2e0c9b1 whole, or (`key-lo-stalls`) only hung it; the seeded rows kill them.
    ('key-search-inverted', 'the key search steps toward the wrong half',
     [('(if (i32.lt_u (local.get $key) (local.get $v))\n              (then (local.set $lo (i32.add (local.get $mid) (i32.const 1))))',
       '(if (i32.lt_u (local.get $v) (local.get $key))\n              (then (local.set $lo (i32.add (local.get $mid) (i32.const 1))))')], 'keys'),
    ('key-lo-stalls', 'the key search steps to the middle, not past it: a miss above a key never ends',
     [('(then (local.set $lo (i32.add (local.get $mid) (i32.const 1))))', '(then (local.set $lo (local.get $mid)))')], 'hang'),
    ('key-hi-drops-last', 'the key search never looks at the last key',
     [('(local.set $hi (local.get $cnt))', '(local.set $hi (i32.sub (local.get $cnt) (i32.const 1)))')], 'keys'),
    ('default-immediate-flip', 'an immediate that reaches a tag Default is checked as if it named a Branch, and a Branch as a Default',
     [('(then (if (if (result i32) (i32.eq (local.get $arm) (i32.const -1))', '(then (if (if (result i32) (i32.ne (local.get $arm) (i32.const -1))')], 'tags'),
    ('tag-range-off-by-one', "a tag equal to its Case's constructor count is in range",
     [('(if (i32.ge_u (local.get $tag) (local.get $cnt)) (then (call $refuse (global.get $R_ill_typed))))',
       '(if (i32.gt_u (local.get $tag) (local.get $cnt)) (then (call $refuse (global.get $R_ill_typed))))')], 'tags'),
    # describe of an Object with three or more fields: no earlier row has more than two
    ('describe-comma-first-only', 'only the second field is preceded by a separator',
     [('(if (local.get $j) (then (call $emitc (i32.const 44))))',
       '(if (i32.eq (local.get $j) (i32.const 1)) (then (call $emitc (i32.const 44))))')], 'describe'),
    ('describe-comma-odd-only', 'every second field is preceded by a separator',
     [('(if (local.get $j) (then (call $emitc (i32.const 44))))',
       '(if (i32.and (local.get $j) (i32.const 1)) (then (call $emitc (i32.const 44))))')], 'describe'),
    ('describe-close-after-two', 'an Object is closed after its second field, whatever it has',
     [('(if (i32.eq (local.get $j) (i32.sub (i32.shr_u (i32.load offset=4 (local.get $w)) (i32.const 3)) (i32.const 2)))',
       '(if (i32.or (i32.eq (local.get $j) (i32.sub (i32.shr_u (i32.load offset=4 (local.get $w)) (i32.const 3)) (i32.const 2)))'
       ' (i32.eq (local.get $j) (i32.const 2)))')], 'describe'),
    # review round 6, the inspection matrix: an immediate word must be refused before any load through it. Wasm evaluates
    # both operands of an `or`, so the fault of the VM of 2e0c9b1 was a trap where section 6 gives `HostFailure image`
    ('scell-loads-before-immediate-test', 'a String cell is tested for an immediate in the same `or` as the loads through it',
     [('    ;; an immediate is no cell: refuse it before any load through it (Wasm evaluates both operands of an or)\n'
       '    (if (i32.and (local.get $s) (i32.const 1)) (then (call $refuse (global.get $R_ill_typed))))\n'
       '    (if (i32.or (i32.and (i32.load offset=4 (local.get $s)) (i32.const 7))\n'
       '          (i32.or (i32.ne (i32.load offset=8 (local.get $s)) (global.get $rString))\n'
       '                  (i32.ne (i32.load offset=12 (local.get $s)) (i32.const 1))))\n'
       '      (then (call $refuse (global.get $R_ill_typed))))',
       '    (if (i32.or (i32.and (local.get $s) (i32.const 1))\n'
       '          (i32.or (i32.and (i32.load offset=4 (local.get $s)) (i32.const 7))\n'
       '            (i32.or (i32.ne (i32.load offset=8 (local.get $s)) (global.get $rString))\n'
       '                    (i32.ne (i32.load offset=12 (local.get $s)) (i32.const 1)))))\n'
       '      (then (call $refuse (global.get $R_ill_typed))))')], 'traps'),
    ('finish-loads-before-immediate-test', "a Program's final word is tested for an immediate in the same `or` as the loads through it",
     [('    (if (i32.or (i32.and (local.get $x) (i32.const 1)) (i32.eqz (local.get $x)))\n'
       '      (then (call $refuse (global.get $R_ill_typed))))\n'
       '    (if (i32.or (i32.and (i32.load offset=4 (local.get $x)) (i32.const 7))\n'
       '                (i32.ne (i32.load offset=8 (local.get $x)) (global.get $rIoop)))\n'
       '      (then (call $refuse (global.get $R_ill_typed))))',
       '    (if (i32.or (i32.or (i32.and (local.get $x) (i32.const 1)) (i32.eqz (local.get $x)))\n'
       '          (i32.or (i32.and (i32.load offset=4 (local.get $x)) (i32.const 7))\n'
       '                  (i32.ne (i32.load offset=8 (local.get $x)) (global.get $rIoop))))\n'
       '      (then (call $refuse (global.get $R_ill_typed))))')], 'traps'),
    # past a cell's end: into its padding or the free heap above the bump pointer, which `$alloc` zeroes before any cell
    # holds it, so each is unobservable except where the cell ends at the end of the memory in use (section `memory-end`)
    ('object-fields-overrun', "an Object's operands are copied 8 bytes each: past its cell at 3, 4, 7 to 12 or 15 to 28 fields",
     [('(memory.copy (i32.add (local.get $c) (i32.const 16)) (local.get $ops) (i32.shl (local.get $cnt) (i32.const 2)))',
       '(memory.copy (i32.add (local.get $c) (i32.const 16)) (local.get $ops) (i32.shl (local.get $cnt) (i32.const 3)))')],
     'memory-end'),
    ('action-operands-overrun', "an Action's operands are copied 8 bytes each: past the 16-byte cell of IO.print's Action",
     [('(memory.copy (i32.add (local.get $c) (i32.const 12)) (local.get $ops) (i32.shl (local.get $cnt) (i32.const 2)))',
       '(memory.copy (i32.add (local.get $c) (i32.const 12)) (local.get $ops) (i32.shl (local.get $cnt) (i32.const 3)))')],
     'memory-end'),
    ('branch-binds-past-fields', "a Branch binds one word more than its constructor's fields: past a cell its fields fill",
     [('(br_if $bound (i32.ge_u (local.get $j) (local.get $f)))', '(br_if $bound (i32.gt_u (local.get $j) (local.get $f)))')],
     'memory-end'),
    # describe's own bounds (section 8): a Nat then constructors near 1,048,576 visits, and the frame region its worklist
    # shares (12 bytes an open Object). The visit and frame checks were pinned only where nothing followed or opened
    ('nat-visits-undercount', 'a Nat word adds n visits to the running count, not n + 1',
     [('(local.set $visits (i32.add (i32.add (local.get $visits) (local.get $v)) (i32.const 1)))',
       '(local.set $visits (i32.add (i32.add (local.get $visits) (local.get $v)) (i32.const 0)))')], 'display'),
    ('nat-visits-overcount', 'a Nat word adds n + 2 visits to the running count',
     [('(local.set $visits (i32.add (i32.add (local.get $visits) (local.get $v)) (i32.const 1)))',
       '(local.set $visits (i32.add (i32.add (local.get $visits) (local.get $v)) (i32.const 2)))')], 'display'),
    ('object-visits-twice', 'a constructor costs two visits',
     [('(local.set $visits (i32.add (local.get $visits) (i32.const 1)))\n', '(local.set $visits (i32.add (local.get $visits) (i32.const 2)))\n')], 'display'),
    ('visits-bound-inclusive', 'a result of exactly 1,048,576 visits is past the bound',
     [('(if (i32.gt_u (local.get $visits) (i32.const 1048576)) (then (call $exhaust (i32.const 2) (global.get $R_display))))',
       '(if (i32.ge_u (local.get $visits) (i32.const 1048576)) (then (call $exhaust (i32.const 2) (global.get $R_display))))')], 'display'),
    ('worklist-frames-inclusive', "a worklist triple that ends exactly at the frame region's end does not fit",
     [('(if (i32.gt_u (i32.add (local.get $sp) (i32.const 12)) (global.get $FL))', '(if (i32.ge_u (i32.add (local.get $sp) (i32.const 12)) (global.get $FL))')], 'limited'),
    ('worklist-triple-13', 'the worklist checks room for a 13-byte triple',
     [('(if (i32.gt_u (i32.add (local.get $sp) (i32.const 12)) (global.get $FL))', '(if (i32.gt_u (i32.add (local.get $sp) (i32.const 13)) (global.get $FL))')], 'limited'),
    ('worklist-triple-11', 'the worklist checks room for an 11-byte triple',
     [('(if (i32.gt_u (i32.add (local.get $sp) (i32.const 12)) (global.get $FL))', '(if (i32.gt_u (i32.add (local.get $sp) (i32.const 11)) (global.get $FL))')], 'limited'),
    ('worklist-frames-unchecked', 'the worklist never runs out of frames',
     [('(if (i32.gt_u (i32.add (local.get $sp) (i32.const 12)) (global.get $FL))', '(if (i32.gt_u (i32.sub (local.get $sp) (i32.const 12)) (global.get $FL))')], 'limited'),
    ('worklist-frames-kind', 'a worklist that does not fit stops as a heap exhaustion',
     [('(if (i32.gt_u (i32.add (local.get $sp) (i32.const 12)) (global.get $FL))\n            (then (call $exhaust (i32.const 3) (global.get $R_frames))))',
       '(if (i32.gt_u (i32.add (local.get $sp) (i32.const 12)) (global.get $FL))\n            (then (call $exhaust (i32.const 2) (global.get $R_frames))))')], 'limited'),
    # a lowered heap: append's block is checked where it is made, the same edits as `top-block-exhausted` at the edge of 4 GiB
    ('append-block-fits-heap', 'an append block ending exactly at a lowered heap limit is Exhausted',
     [('    (if (i64.gt_u (local.get $end) (global.get $HL)) (then (call $exhaust (i32.const 2) (global.get $R_heap))))\n    (call $grow (local.get $end))',
       '    (if (i64.ge_u (local.get $end) (global.get $HL)) (then (call $exhaust (i32.const 2) (global.get $R_heap))))\n    (call $grow (local.get $end))')], 'limited'),
    ('append-heap-kind', 'an append block that does not fit the heap stops as a frame exhaustion',
     [('    (if (i64.gt_u (local.get $end) (global.get $HL)) (then (call $exhaust (i32.const 2) (global.get $R_heap))))\n    (call $grow (local.get $end))',
       '    (if (i64.gt_u (local.get $end) (global.get $HL)) (then (call $exhaust (i32.const 3) (global.get $R_heap))))\n    (call $grow (local.get $end))')], 'limited'),
    ('action-cell-oversize', 'an Action takes one payload word more than its id and operands',
     [('(local.set $c (call $alloc (i32.add (local.get $cnt) (i32.const 1)) (i32.const 3)))',
       '(local.set $c (call $alloc (i32.add (local.get $cnt) (i32.const 2)) (i32.const 3)))')], 'limited'),
    # inspection (section 6): a class check that lets class 3 pass as a Big cell, and a tag range that lets a tag equal to the count through
    ('scalar-reads-action', 'a scalar operand that is an Action (class 3) passes as a Big cell',
     [('    (if (i32.ne (i32.and (i32.load offset=4 (local.get $x)) (i32.const 7)) (i32.const 2))\n      (then (call $refuse (global.get $R_ill_typed))))\n    (i32.load offset=8 (local.get $x)))',
       '    (if (i32.ne (i32.and (i32.load offset=4 (local.get $x)) (i32.const 6)) (i32.const 2))\n      (then (call $refuse (global.get $R_ill_typed))))\n    (i32.load offset=8 (local.get $x)))')], 'tags'),
    ('describe-tag-at-count', "a result whose tag equals its type's constructor count is in range",
     [('        (if (i32.ge_u (local.get $tag) (call $ty (local.get $t) (i32.const 3)))\n          (then (call $refuse (global.get $R_ill_typed))))',
       '        (if (i32.gt_u (local.get $tag) (call $ty (local.get $t) (i32.const 3)))\n          (then (call $refuse (global.get $R_ill_typed))))')], 'tags'),
]


# ------------------------------------------------------------------ main
def main(args: list) -> int:
    if args[:1] == ['--freeze']:
        return freeze()
    study = args[:1] == ['--study']
    started = datetime.datetime.now(datetime.timezone.utc)
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    reg = codec.registry()
    digest = codec.base_digest(reg)
    require(crash_fails(), 'a crash of the reference codec fails the gate')
    record = {'date': started.isoformat(), 'status': 'incomplete',
              'scope': 'knot-vm-1 vm/vm.wat: loader, validator, machine, describe; vm-core subset of SPEC section 10',
              'inputs': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(
                  [HERE / 'vm.wat', HERE / 'vm.wasm', HERE / 'build.json', HERE / 'build.py', HERE / 'harness.mjs',
                   HERE / 'check-core.py', HERE / 'lane.py', HERE / 'scope.py', HERE / 'study.py', HERE / 'SPEC.md', HERE / 'serializer.py',
                   HERE / 'registry.json', HOST, HERE / 'check-spec.py', HERE / 'evaluate.py', HERE / 'golden/vm-expected.json',
                   *(HERE / 'core').glob('*')])}, 'stages': []}
    clock = [time.monotonic()]

    def stage(name: str):
        """Note the time since the last stage, on stderr and in the receipt (where the runner treats it as volatile)."""
        now = time.monotonic()
        record['stages'].append({'stage': name, 'elapsed_seconds': round(now - clock[0], 1)})
        print(f'[{now - clock[0]:7.1f} s] {name}', file=sys.stderr, flush=True)
        clock[0] = now

    # pins and module shape
    pins, module_bytes, test_bytes = build.build()
    frozen = json.loads((HERE / 'build.json').read_text())
    require(frozen == pins, f'vm/build.json pins differ from a fresh build: {frozen} vs {pins}')
    require((HERE / 'vm.wasm').read_bytes() == module_bytes, 'vm/vm.wasm reassembles byte-identically')
    module, test = HERE / 'vm.wasm', BUILD / 'vm-test.wasm'
    test.write_bytes(test_bytes)
    shapes = {'module': module_shape(module), 'test_build': module_shape(test)}
    check_shape(shapes['module'], False)
    check_shape(shapes['test_build'], True)
    record['pins'] = pins
    record['shape'] = shapes

    # goldens through the host, then the test build
    expected = json.loads((HERE / 'golden/vm-expected.json').read_text())
    golden = HERE / 'golden'

    def golden_argv(name):
        return [a if a != 'IMAGE' else f'{name}.kimg' for a in expected['cases'][name]['argv']]

    names = sorted(expected['cases'])
    results = dict(zip(names, pool(lambda n: host(module, golden, golden_argv(n)), names)))
    traced = harness([{'id': n, 'wasm': str(test), 'files': {f'{n}.kimg': str(golden / f'{n}.kimg')},
                       'argv': golden_argv(n), 'trace': 'audit'} for n in names])
    golden_out = traced
    goldens = []
    for name in names:
        case, got, dump = expected['cases'][name], results[name], traced[name]
        state = dump['state']
        require(dump['broken'] is None, f'{name}: state audit {dump["broken"]}')
        require(got == expected_run(case), f'{name}: {got} differs from vm-expected {expected_run(case)}')
        require(all(state[k] == v for k, v in expected_dump(case).items()), f'{name}: dump {state} vs {expected_dump(case)}')
        require((dump['exit'], dump['stdout']) == (got['exit'], got['stdout']), f'{name}: harness and host differ')
        goldens.append({'name': name, 'exit': got['exit'], 'stdout_sha256': sha(got['stdout'].encode()),
                        'outcome': state['outcome'], 'cause': state['cause'], 'calls': state['calls'],
                        'transitions': dump['steps'], 'audited': dump['audited']})
    record['goldens'] = goldens
    stage('goldens')

    # the Book invocations vm-spec froze with the goldens (SPEC section 8's walk)
    invoked = [(f"{n} {' '.join(row['argv'][1:])}", n, row) for n in sorted(expected.get('invocations', {}))
             for row in expected['invocations'][n]]
    invocation_argv = {label: [a if a != 'IMAGE' else f'{n}.kimg' for a in row['argv']] for label, n, row in invoked}
    got = dict(zip([c[0] for c in invoked], pool(lambda c: host(module, golden, invocation_argv[c[0]]), invoked)))
    traced = harness([{'id': label, 'wasm': str(test), 'files': {f'{n}.kimg': str(golden / f'{n}.kimg')},
                       'argv': invocation_argv[label], 'trace': 'audit'} for label, n, _ in invoked])
    invocation_out = traced
    invocations = []
    for label, n, row in invoked:
        dump, state = traced[label], traced[label]['state']
        require(dump['broken'] is None, f'invocation {label}: state audit {dump["broken"]}')
        require(got[label] == expected_run(row), f'invocation {label}: {got[label]} differs from {expected_run(row)}')
        require(all(state[k] == v for k, v in expected_dump(row).items()), f'invocation {label}: dump {state}')
        require((dump['exit'], dump['stdout']) == (got[label]['exit'], got[label]['stdout']),
                f'invocation {label}: harness and host differ')
        invocations.append({'invocation': label, 'exit': got[label]['exit'], 'outcome': state['outcome'],
                            'cause': state['cause'], 'calls': state['calls']})
    record['invocations'] = invocations
    stage('invocations')

    # vm/core fixtures: literal-review runs, dumps and lowered limits
    fixtures = json.loads((HERE / 'core/fixtures.json').read_text())
    sandbox = BUILD / 'sandbox'
    sandbox.mkdir()

    def staged(image):
        if image is None:
            return 'missing.kimg'
        name = image.replace('/', '-') + '.kimg'
        if not (sandbox / name).exists():
            shutil.copy(HERE / f'{image}.kimg', sandbox / name)
        return name

    runs = fixtures['runs']
    for r in runs:
        staged(r['image'])
    ran = pool(lambda r: host(module, sandbox, [staged(r['image']), *r['argv']]), runs)
    core = []
    for r, got in zip(runs, ran):
        require(got == r['expect'], f"fixture {r['name']}: {got} vs {r['expect']}")
        core.append({'name': r['name'], 'exit': got['exit'], 'stdout_sha256': sha(got['stdout'].encode())})
    by_name = {r['name']: r for r in runs}
    jobs = [{'id': n, 'wasm': str(test), 'files': {staged(by_name[n]['image']): str(sandbox / staged(by_name[n]['image']))},
             'argv': [staged(by_name[n]['image']), *by_name[n]['argv']], 'trace': 'yields'} for n in fixtures['dumps']]
    jobs += [{'id': l['name'], 'wasm': str(test), 'files': {staged(l['image']): str(sandbox / staged(l['image']))},
              'argv': [staged(l['image']), *l['argv']], 'limits': l['limits']} for l in fixtures['limited']]
    for l in fixtures['limited']:  # a pinned bump under a lowered heap: section 5's model stops (or ends) there too
        if (l['dump'].get('cause') == 'heap' or l.get('model')) and 'bump' in l['dump']:
            plan, image = json.loads((HERE / f"{l['image']}.plan.json").read_text()), (HERE / f"{l['image']}.kimg").read_bytes()
            require(codec.encode(plan, digest) == image, f"limited {l['name']}: the image is its plan's encoding")
            try:
                stop = ceiling_run(plan, image, l['limits']['heap'])[0]
            except Beyond as beyond:
                stop = beyond.bump
            require(stop == l['dump']['bump'], f"limited {l['name']}: frozen bump {l['dump']['bump']}, section 5 gives {stop}")
    limited_expect = {l['name']: l['expect'] for l in fixtures['limited'] if 'expect' in l}
    dumped = harness(jobs)
    dumps = []
    for name, want in [*fixtures['dumps'].items(), *((l['name'], l['dump']) for l in fixtures['limited'])]:
        got, state = dumped[name], dumped[name]['state']
        seen = {'outcome': state['outcome'], 'kind': state['kind'], 'cause': state['cause'],
                'calls': state['calls'], 'yields': got['yields'], 'top': state['top'], 'bump': state['bump']}
        require(all(seen[k] == v for k, v in want.items()), f'dump {name}: {seen} vs {want}')
        if name in limited_expect:  # a limited row that completes also freezes the run it writes
            require(shown(got, limited_expect[name]) == limited_expect[name], f'dump {name}: {shown(got, limited_expect[name])} vs {limited_expect[name]}')
        dumps.append({'name': name, **{k: seen[k] for k in want}})
    record['fixtures'] = {'runs': core, 'dumps': dumps}
    stage('fixtures')

    # Books compared with the reference evaluation: the frozen run is literal review, and
    # vm/evaluate.py and the VM must each give it (review round 3: Chr's operand)
    compared = fixtures['reference']['rows']
    for r in compared:
        plan, image = json.loads((HERE / f"{r['image']}.plan.json").read_text()), (HERE / f"{r['image']}.kimg").read_bytes()
        require(codec.encode(plan, digest) == image and spec.rejected(image, reg, digest) is None,
                f"reference {r['name']}: the image is its plan's encoding, and the reference codec admits it")
        derived = reference_run(plan, int(r['argv'][1]))
        require(derived == (r['expect'], r['dump']), f"reference {r['name']}: frozen {r['expect']} {r['dump']}, "
                                                     f"the reference evaluation {derived}")
    reference_jobs = [{'id': f"reference:{r['name']}", 'files': {staged(r['image']): str(sandbox / staged(r['image']))},
                       'argv': [staged(r['image']), *r['argv']], 'want': r['expect'], 'dump': r['dump']} for r in compared]
    ran = pool(lambda j: host(module, sandbox, j['argv']), reference_jobs)
    dumped = harness([{**{k: j[k] for k in ('id', 'files', 'argv')}, 'wasm': str(test), 'trace': 'audit'}
                      for j in reference_jobs])
    agreed = []
    for j, got in zip(reference_jobs, ran):
        dump, state = dumped[j['id']], dumped[j['id']]['state']
        require(dump['broken'] is None, f"{j['id']}: state audit {dump['broken']}")
        require(got == j['want'], f"{j['id']}: {got} vs the reference evaluation {j['want']}")
        require((dump['exit'], dump['stdout']) == (got['exit'], got['stdout']), f"{j['id']}: harness and host differ")
        require(all(state[k] == v for k, v in j['dump'].items()), f"{j['id']}: {state} vs {j['dump']}")
        agreed.append({'name': j['id'].split(':', 1)[1], 'exit': got['exit'], **j['dump']})
    record['reference'] = agreed
    stage('reference rows')

    # a cell that ends exactly at the end of the memory in use (48 MiB after boot): the one place where a read or a write
    # past a cell's end faults. Section 5's model gives each row's bump pointer and line, the reference evaluation at
    # a fill of 3 the line and the calls (each further step is one entry)
    edge = fixtures['memory-end']['rows']
    for r in edge:
        plan, image = json.loads((HERE / f"{r['image']}.plan.json").read_text()), (HERE / f"{r['image']}.kimg").read_bytes()
        require(codec.encode(plan, digest) == image and spec.rejected(image, reg, digest) is None,
                f"memory-end {r['name']}: the image is its plan's encoding, and the reference codec admits it")
        derived = ceiling_expectation(plan, image)
        require(derived == (r['expect'], {'outcome': 'Completed', 'bump': r['dump']['bump']}) and r['dump']['bump'] == 48 << 20,
                f"memory-end {r['name']}: frozen {r['expect']} {r['dump']}, section 5 gives {derived}")
        shrunk = refilled(plan, r['fill'], 3)
        derived = reference_run(shrunk, 1000)
        require(derived == (r['expect'], {'outcome': 'Completed', 'calls': r['dump']['calls'] - (r['fill'] - 3)}),
                f"memory-end {r['name']}: frozen {r['expect']} {r['dump']}, the reference evaluation at a fill of 3 {derived}")
    edge_jobs = [{'id': f"memory-end:{r['name']}", 'files': {staged(r['image']): str(sandbox / staged(r['image']))},
                  'argv': [staged(r['image']), *r['argv']], 'want': r['expect'], 'dump': r['dump']} for r in edge]
    ran = pool(lambda j: host(module, sandbox, j['argv']), edge_jobs)
    dumped = harness([{**{k: j[k] for k in ('id', 'files', 'argv')}, 'wasm': str(test)} for j in edge_jobs])
    ends = []
    for j, got in zip(edge_jobs, ran):
        dump, state = dumped[j['id']], dumped[j['id']]['state']
        require(got == j['want'], f"{j['id']}: {got} vs {j['want']}")
        require((dump['exit'], dump['stdout']) == (got['exit'], got['stdout']), f"{j['id']}: harness and host differ")
        require(all(state[k] == v for k, v in j['dump'].items()), f"{j['id']}: {state} vs {j['dump']}")
        ends.append({'name': j['id'].split(':', 1)[1], 'exit': got['exit'], 'stdout_sha256': sha(got['stdout'].encode()), **j['dump']})
    record['memory_end'] = ends
    stage('memory end')

    # the differential lane: seeded rows, generated programs, sweeps and writers through vm.wasm and the reference
    # evaluation, the frozen seed sample through the seed's native lane (vm/lane.py, vm/core/lane.json)
    lane_cfg = json.loads(LANE.read_text())
    seeded_rows = json.loads(SEEDED.read_text())
    record['lane'], lane_all = check_lane(lane_cfg, seeded_rows, module, test, BUILD / 'lane', reg, digest)
    stage('lane')

    # the bump pointer near 4 GiB: each run touches about 4 GiB, so two at a time,
    # each in its own process
    # SPEC section 5's arithmetic fixes each row before the VM runs it
    ceiling = fixtures['ceiling']['rows']
    for r in ceiling:
        plan, image = json.loads((HERE / f"{r['image']}.plan.json").read_text()), (HERE / f"{r['image']}.kimg").read_bytes()
        require(codec.encode(plan, digest) == image, f"ceiling {r['name']}: the image is its plan's encoding")
        derived = ceiling_expectation(plan, image)
        require(derived == (r['expect'], r['dump']), f"ceiling {r['name']}: frozen {r['expect']} {r['dump']}, "
                                                      f"section 5 gives {derived}")
    ceiling_jobs = [{'id': r['name'], 'wasm': str(test), 'files': {staged(r['image']): str(sandbox / staged(r['image']))},
                     'argv': [staged(r['image']), *r['argv']]} for r in ceiling]
    high = []
    if not study:
        ran = pool(lambda r: host(module, sandbox, [staged(r['image']), *r['argv']]), ceiling, workers=2)
        dumped = {j['id']: harness([j])[j['id']] for j in ceiling_jobs}
        for r, got in zip(ceiling, ran):
            dump, state = dumped[r['name']], dumped[r['name']]['state']
            require(got == r['expect'], f"ceiling {r['name']}: {got} vs {r['expect']}")
            require((dump['exit'], dump['stdout']) == (got['exit'], got['stdout']), f"ceiling {r['name']}: harness and host differ")
            require(all(state[k] == v for k, v in r['dump'].items()), f"ceiling {r['name']}: {state} vs {r['dump']}")
            high.append({'name': r['name'], 'exit': got['exit'], 'stdout_sha256': sha(got['stdout'].encode()), **r['dump']})
        record['ceiling'] = high
        stage('ceiling')

    # heap growth (CORE.md choice 15): a stream of small cells reaches the heap's end, or a host's refusal
    # to grow, in bounded time. SPEC section 5 leaves the timing of memory.grow free; growing one 64 KiB
    # page at a time costs 22 minutes at 4 GiB on V8, which section 11 counts as neither Exhausted nor agreement
    loop_plan = json.loads((HERE / 'core/loop-cells.plan.json').read_text())
    loop_image = (HERE / 'core/loop-cells.kimg').read_bytes()
    require(codec.encode(loop_plan, digest) == loop_image, "growth: the image is its plan's encoding")
    growth = growth_jobs(fixtures['growth']['rows'], loop_plan, loop_image, staged('core/loop-cells'), sandbox)
    if not study:
        record['growth'] = check_growth(growth, module, test)
        stage('growth')

    # nothing recurses: a 200,000-deep nested expression, and the deep runs on a 64 KiB host stack
    stack = {}
    if not study:
        small = nested_plan(40)
        require(nested_image(40, digest) == codec.encode(small, digest), 'the nested generator matches serializer.encode')
        deep = nested_image(NEST, digest)
        (sandbox / 'nested.kimg').write_bytes(deep)
        for label, argv in [('nested-200k', ['nested.kimg', 'main', str(NEST + 2)]),
                            ('deep-250k', [staged('core/deep-250k'), 'main', '500003']),
                            ('render-list', [staged('core/render-list'), 'main', '1000000'])]:
            got = host(module, sandbox, argv, (SMALL_STACK,))
            want = by_name.get(label, {}).get('expect') or {'exit': 0, 'stdout': 'Evaluated\t1\t1\tTrue{}\n', 'stderr': ''}
            require(got == want, f'{label} under {SMALL_STACK}: {got}')
            stack[label] = {'exit': got['exit'], 'stdout_sha256': sha(got['stdout'].encode())}
        stack['nested-200k'].update(words=len(deep) // 4, sha256=sha(deep), fuel=NEST + 2)
        record['host_stack'] = {'node_flag': SMALL_STACK, 'runs': stack}
        stage('host stack')

    # malformed images: the frozen controls, then a seeded fuzz corpus
    plans = {p.name[:-len('.plan.json')]: json.loads(p.read_text()) for p in golden.glob('*.plan.json')}
    images = {p.stem: p.read_bytes() for p in golden.glob('*.kimg')}
    planned = spec.plan_controls(plans)  # a row without a message is one the VM MUST admit
    byte_level = spec.byte_controls(images, digest)
    at_limits = spec.limit_controls(plans, images, digest)  # a row without a verdict is one the VM MUST admit
    limit_level = [(f'limit:{k}', data, verdict, '') for k, data, verdict in at_limits if verdict]
    plan_level = [(f'plan:{k}', codec.encode(p, digest), 'HostFailure image: validator: ', m) for k, p, m in planned if m]
    total, bytes_frozen, limits_frozen, plans_frozen = refusal_counts()
    require((len(byte_level), len(limit_level), len(plan_level), len(byte_level) + len(limit_level) + len(plan_level))
            == (bytes_frozen, limits_frozen, plans_frozen, total),
            f'SPEC section 4 freezes {total} refusals ({bytes_frozen} byte-level, {limits_frozen} at the limits, '
            f'{plans_frozen} plan-level); check-spec.py yields {len(byte_level)}, {len(limit_level)} and {len(plan_level)}')
    controls = byte_level + limit_level + plan_level
    malformed = BUILD / 'malformed'
    malformed.mkdir()

    def argv_for(name, data):
        return [name, '1000', '--'] if int.from_bytes(data[12:16], 'little') == 1 else [name, 'main', '1000']

    def traced(rows, where, timeout=600):
        return harness([{'id': r['label'], 'wasm': str(test), 'files': {r['argv'][0]: str(where / r['argv'][0])},
                         'argv': r['argv'], 'trace': 'yields'} for r in rows], timeout)

    rows = []
    for i, (label, data, reason, message) in enumerate(controls):
        reference = spec.rejected(data, reg, digest)  # the frozen refusal: the VM owes the reference's first defect
        require(reference is not None and reference.startswith(reason) and message in reference,
                f'control {label}: the reference codec gives {reference!r}, frozen {reason!r} {message!r}')
        (malformed / f'c{i}.kimg').write_bytes(data)
        rows.append({'label': label, 'sha256': sha(data), 'reference': reference, 'argv': argv_for(f'c{i}.kimg', data)})
    got = pool(lambda r: host(module, malformed, r['argv']), rows)
    dumped = traced(rows, malformed)
    refused = []
    for r, g in zip(rows, got):
        code = expected_reason(r['reference'])
        g.update(state=dumped[r['label']]['state'], booted=dumped[r['label']]['booted'])
        require(clean(g), f"control {r['label']}: {g}")
        require(observed_reason(g) == code, f"control {r['label']}: VM {g['stderr']!r}, reference {r['reference']!r}")
        require(all(g['state'][k] == v for k, v in refusal_dump(code).items()),
                f"control {r['label']}: the VM's outcome registers {g['state']} differ from {refusal_dump(code)}")
        refused.append({'control': r['label'], 'reference': r['reference'], 'vm': code, 'exit': g['exit']})

    # the controls vm-spec admits (SPEC section 4): loaded, then run as literal review froze them
    admitted = [(f'plan:{k}', p) for k, p, m in planned if m is None] + \
        [(f'limit:{k}', codec.decode(data, digest)) for k, data, verdict in at_limits if verdict is None] + \
        spec.code_controls(plans)
    frozen = {r['control']: r for r in fixtures['admitted']['rows']}
    require(sorted(label for label, _ in admitted) == sorted(frozen),
            f'admitted controls {sorted(label for label, _ in admitted)} vs frozen rows {sorted(frozen)}')
    loaded = BUILD / 'admitted'
    loaded.mkdir()
    welcome = []
    for i, (label, plan) in enumerate(admitted):
        data, row = codec.encode(plan, digest), frozen[label]
        require(spec.rejected(data, reg, digest) is None, f'admitted control {label}: the reference refuses it')
        require(plan['entry'] == 'book' and row['argv'][0] == 'main', f'admitted control {label}: a Book of main')
        run, dump = reference_run(plan, int(row['argv'][1]))
        require(run == row['expect'] and {k: dump.get(k) for k in row['dump']} == row['dump'],
                f"admitted control {label}: frozen {row['expect']} {row['dump']}, the reference evaluation {run} {dump}")
        (loaded / f'a{i}.kimg').write_bytes(data)
        welcome.append({'label': label, 'sha256': sha(data), 'argv': [f'a{i}.kimg', *frozen[label]['argv']]})
    ran = pool(lambda r: host(module, loaded, r['argv']), welcome)
    dumped = traced(welcome, loaded)
    admitted_out, admitted_plan = dumped, dict(admitted)
    admissions = []
    for r, g in zip(welcome, ran):
        row, dump = frozen[r['label']], dumped[r['label']]
        state = dump['state']
        require(g == row['expect'], f"admitted control {r['label']}: {g} vs {row['expect']}")
        require(dump['booted'] and (dump['exit'], dump['stdout']) == (g['exit'], g['stdout']),
                f"admitted control {r['label']}: not loaded, or harness and host differ: {dump}")
        seen = {'outcome': state['outcome'], 'kind': state['kind'], 'cause': state['cause'], 'calls': state['calls']}
        require(all(seen[k] == v for k, v in row['dump'].items()), f"admitted control {r['label']}: {seen} vs {row['dump']}")
        admissions.append({'control': r['label'], 'sha256': r['sha256'], 'exit': g['exit'], **row['dump']})

    # the run controls vm-spec admits and freezes with their runs (SPEC sections 4, 7
    # and 12): loaded, then run to the frozen outcome and call count. A control that
    # freezes its fuel (section 7's boundary) runs on exactly that fuel; any other on
    # 1,000,000 and again on exactly its `calls`, to the same outcome, since section 7
    # checks Enter's operands before its fuel: an ill-typed Enter is refused at fuel 0 too.
    runs_frozen = spec.run_controls(plans)
    require(len(runs_frozen) == run_control_count(),
            f'SPEC section 12 freezes {run_control_count()} run controls; check-spec.py yields {len(runs_frozen)}')
    run_rows = []
    for i, (label, plan, run) in enumerate(runs_frozen):
        data = codec.encode(plan, digest)
        require(spec.rejected(data, reg, digest) is None, f'run control {label}: the reference refuses it')
        (loaded / f'r{i}.kimg').write_bytes(data)
        want = ({'stderr': '', **{k: v for k, v in run.items() if k not in ('calls', 'fuel')}} if 'exit' in run
                else expected_run(run))
        dump = {**expected_dump(run if 'exit' not in run else {'exit': 0}), 'calls': run['calls']}
        for fuel in [str(run['fuel'])] if 'fuel' in run else ['1000000', str(run['calls'])]:
            argv = ['main', fuel] if plan['entry'] == 'book' else [fuel, '--']
            run_rows.append({'label': f'run:{label}@{fuel}', 'sha256': sha(data), 'argv': [f'r{i}.kimg', *argv],
                             'want': want, 'dump': dump})
    ran = pool(lambda r: host(module, loaded, r['argv']), run_rows)
    dumped = traced(run_rows, loaded)
    run_out, run_plan = dumped, {f'run:{label}': plan for label, plan, _ in runs_frozen}
    for r, g in zip(run_rows, ran):
        dump, state = dumped[r['label']], dumped[r['label']]['state']
        require(shown(g, r['want']) == r['want'], f"run control {r['label']}: {shown(g, r['want'])} vs {r['want']}")
        require(dump['booted'] and (dump['exit'], dump['stdout']) == (g['exit'], g['stdout']),
                f"run control {r['label']}: not loaded, or harness and host differ: {dump}")
        seen = {'outcome': state['outcome'], 'kind': state['kind'], 'cause': state['cause'], 'calls': state['calls']}
        require(all(seen[k] == v for k, v in r['dump'].items()), f"run control {r['label']}: {seen} vs {r['dump']}")
    for label, _, _ in runs_frozen:
        rows_for = [r for r in run_rows if r['label'].startswith(f'run:{label}@')]
        admissions.append({'control': f'run:{label}', 'sha256': rows_for[0]['sha256'], 'exit': rows_for[0]['want']['exit'],
                           **rows_for[0]['dump'], 'fuel_runs': [r['label'].split('@')[1] for r in rows_for]})

    # section 8's argument words where no frozen invocation reaches (vm-spec D16): the image
    # first, its entry kind's shape (`usage`), then each decimal u32 word. Each control gets
    # its frozen verdict; where the words are admitted, the reference evaluation's run
    argued = BUILD / 'arguments'
    argued.mkdir()
    word_rows = []
    for i, (label, data, words, verdict) in enumerate(spec.argument_controls(images)):
        (argued / f'w{i}.kimg').write_bytes(data)
        if verdict is None:
            plan = codec.decode(data, digest)
            if plan['entry'] == 'book':
                ran = spec.reference.book(plan, words[0], [codec.decimal(w) for w in words[2:]], codec.decimal(words[1]))
                want = {'exit': ran['exit'], 'stdout': ran['stdout'], 'stderr': ''}
            else:
                ran = spec.reference.program(plan, codec.decimal(words[0]))
                want = {'exit': ran['exit'], 'stdout': ran['stdout'].decode(), 'stderr': ''}
        elif verdict.startswith('HostFailure image: '):
            want = {'exit': 5, 'stdout': '', 'stderr': f'HostFailure\timage\t{expected_reason(verdict)}\n'}
        else:
            want = {'exit': 5, 'stdout': '', 'stderr': verdict.replace(' ', '\t') + '\n'}
        word_rows.append({'label': label, 'argv': [f'w{i}.kimg', *words], 'verdict': verdict, 'want': want})
    for r, g in zip(word_rows, pool(lambda r: host(module, argued, r['argv']), word_rows)):
        require(g == r['want'], f"argument control {r['label']}: {g} vs {r['want']}")
    record['arguments'] = [{'control': r['label'], 'verdict': r['verdict'], 'exit': r['want']['exit']} for r in word_rows]
    stage('controls')

    # the validator's scope tables at the depths where they grow: fixtures.json's `scope` rows, then a seeded corpus
    record['scope'], scope_jobs = check_scope(fixtures['scope'], module, test, BUILD / 'scope', reg, digest)
    stage('scope tables')

    fuzz = BUILD / 'fuzz'
    fuzz.mkdir()
    corpus = fuzz_corpus(images, reg, digest, fuzz)
    fuzz_plans = [(r, codec.decode((fuzz / r['argv'][0]).read_bytes(), digest)) for r in corpus if r['reference'] is None]
    words_corpus, word_jobs = [], []
    if not study:
        fuzzed = traced(corpus, fuzz, timeout=1200)
        tally = compare('fuzz', corpus, fuzzed)
        limit_words = BUILD / 'limit-words'
        limit_words.mkdir()
        words_corpus = limit_corpus(images, reg, digest, limit_words)
        words_seen = traced(words_corpus, limit_words, timeout=1200)
        words_tally = compare('limit word', words_corpus, words_seen)
        record['malformed'] = {'controls': refused, 'admitted': admissions,
                               'fuzz': {'seed': FUZZ_SEED, 'per_image': FUZZ_PER_IMAGE, 'images': len(corpus),
                                        'corpus_sha256': sha(json.dumps([r['sha256'] for r in corpus]).encode()), **tally},
                               'limit_words': {'images': len(words_corpus),
                                               'corpus_sha256': sha(json.dumps([r['sha256'] for r in words_corpus]).encode()),
                                               **words_tally}}
        stage('fuzz and limit-word corpora')

        # every admitted image through both the VM and the reference evaluation: the goldens, the invocations,
        # the admitted and run controls and the mutated goldens the reference admits
        seen = [(f'golden:{n}', plans[n], golden_argv(n)[1:], golden_out[n]) for n in names] + \
            [(f'invocation:{label}', plans[n], invocation_argv[label][1:], invocation_out[label]) for label, n, _ in invoked] + \
            [(f"admitted:{r['label']}", admitted_plan[r['label']], r['argv'][1:], admitted_out[r['label']]) for r in welcome] + \
            [(r['label'], run_plan[r['label'].split('@')[0]], r['argv'][1:], run_out[r['label']]) for r in run_rows] + \
            [(f"fuzz:{r['label']}", plan, r['argv'][1:], fuzzed[r['label']]) for r, plan in fuzz_plans]
        failures = [f'{label}: {why}' for label, plan, words, out in seen if (why := disagreement(plan, words, out))]
        require(not failures, f'{len(failures)} admitted images run otherwise than the reference evaluation says, first: {failures[:3]}')
        record['both'] = {'goldens': len(names), 'invocations': len(invoked), 'admitted_controls': len(welcome),
                          'run_controls': len(run_rows), 'fuzz_admitted': len(fuzz_plans)}
        stage('admitted images through both')

    # mutants: a changed observation in their group, never a crash, except group `trap`, whose
    # defect is a trap where section 5 gives an outcome. Runs use the test build, so a golden
    # also compares the VM's own outcome registers.
    source = (HERE / 'vm.wat').read_text()
    goldens_jobs = [{'id': f'golden:{n}', 'files': {f'{n}.kimg': str(golden / f'{n}.kimg')}, 'argv': golden_argv(n),
                     'want': expected_run(expected['cases'][n]), 'dump': expected_dump(expected['cases'][n])}
                    for n in names]
    fixture_jobs = [{'id': f"fixture:{r['name']}", 'files': {staged(r['image']): str(sandbox / staged(r['image']))} if r['image'] else {},
                     'argv': [staged(r['image']), *r['argv']], 'want': r['expect']} for r in runs]
    control_jobs = [{'id': f"control:{r['label']}", 'files': {r['argv'][0]: str(malformed / r['argv'][0])},
                     'argv': r['argv'], 'want': {'exit': g['exit'], 'stdout': g['stdout'], 'stderr': g['stderr']}}
                    for r, g in zip(rows, got)]
    admitted_jobs = [{'id': f"admitted:{r['label']}", 'files': {r['argv'][0]: str(loaded / r['argv'][0])},
                      'argv': r['argv'], 'want': frozen[r['label']]['expect']} for r in welcome]
    invocation_jobs = [{'id': f'invocation:{label}', 'files': {f'{n}.kimg': str(golden / f'{n}.kimg')},
                        'argv': invocation_argv[label], 'want': expected_run(row), 'dump': expected_dump(row)}
                       for label, n, row in invoked]
    run_jobs = [{'id': r['label'], 'files': {r['argv'][0]: str(loaded / r['argv'][0])}, 'argv': r['argv'],
                 'want': r['want'], 'dump': r['dump']} for r in run_rows]
    limited_jobs = [{'id': f"limited:{l['name']}", 'files': {staged(l['image']): str(sandbox / staged(l['image']))},
                     'argv': [staged(l['image']), *l['argv']], 'limits': l['limits'], 'want': l.get('expect') or expected_run(l['dump']),
                     'dump': {k: v for k, v in l['dump'].items() if k != 'yields'}} for l in fixtures['limited']]
    ceiling_mutant_jobs = [{**j, 'id': f"ceiling:{r['name']}", 'want': r['expect'], 'dump': r['dump']}
                           for j, r in zip(ceiling_jobs, ceiling)]
    full_heap = [j for j in ceiling_mutant_jobs if j['dump']['bump'] == 1 << 32]
    require(len(full_heap) == 3, f'three ceiling rows fill the heap to exactly 4 GiB: {[j["id"] for j in full_heap]}')
    # section 4's limits: the controls at them, and the three oversize images, with the VM's outcome registers
    image_limits = [{**j, 'dump': refusal_dump(expected_reason(r['reference']))}
                    for j, r in zip(control_jobs, rows) if r['label'].startswith(('limit:', 'oversize'))] + \
        [j for j in admitted_jobs if j['id'].startswith('admitted:limit:')]
    word_jobs = [{'id': f"limit-word:{r['label']}", 'files': {r['argv'][0]: str(limit_words / r['argv'][0])},
                  'argv': r['argv'], 'want': {k: words_seen[r['label']][k] for k in ('exit', 'stdout', 'stderr')},
                  'dump': {k: words_seen[r['label']]['state'][k] for k in ('outcome', 'cause')}} for r in words_corpus]
    require(len(image_limits) == 13, f'nine limit refusals, three oversize images and arity-at-limit: {[j["id"] for j in image_limits]}')
    groups = {'goldens': goldens_jobs, 'fixtures': fixture_jobs, 'controls': goldens_jobs + control_jobs + admitted_jobs,
              'fuel': [j for j in fixture_jobs if 'fuel' in j['id']],
              'quantum': [j for j in fixture_jobs if 'quantum' in j['id']], 'ceiling': ceiling_mutant_jobs,
              'full-heap': full_heap, 'trap': ceiling_mutant_jobs,
              'invocations': invocation_jobs, 'runs': run_jobs, 'reference': reference_jobs, 'limited': limited_jobs,
              'image-limits': image_limits, 'limit-words': word_jobs,
              'growth': [j for j in growth if j['at_most']], 'refused': [j for j in growth if j['dump']['outcome'] is None]}
    require(all(groups[g] for g in ('growth', 'refused')), 'the growth rows have a bounded count and a refusal')
    groups.update(lane_groups(lane_all, BUILD / 'lane'))
    groups['scope'] = scope_jobs  # the scope rows and corpus: a refusal, or a run, other than the reference codec's
    # the rows that bound their memory.grow count: tables that grow by one index a slot take gigabytes, and the rows that show it are few
    groups['scope-growth'] = [j for j in scope_jobs if j['id'] in ('scope:nest-mark', 'scope:edge-t1-past')]
    groups['traps'] = groups['inspection']  # the same rows: a fault where the frozen run is a refusal is the wrong observation
    groups['memory-end'] = edge_jobs  # a fault where the frozen run completes, at a cell that ends where memory does
    groups['dumps'] = [{'id': f'dump:{n}', 'files': {staged(by_name[n]['image']): str(sandbox / staged(by_name[n]['image']))},
                        'argv': [staged(by_name[n]['image']), *by_name[n]['argv']], 'trace': 'yields', 'want': None, 'dump': want}
                       for n, want in fixtures['dumps'].items()]
    groups['fuzz-admitted'] = [{'id': f"fuzz:{r['label']}", 'files': {r['argv'][0]: str(fuzz / r['argv'][0])}, 'argv': r['argv'],
                                'want': reference_result(plan, r['argv'][1:])[0], 'dump': reference_result(plan, r['argv'][1:])[1]}
                               for r, plan in fuzz_plans]
    # a search that never ends is the defect of group `hang`: the goldens' one-key Default miss joins the lane's key rows
    groups['hang'] += [{**j, 'deadline': 3_000} for j in goldens_jobs if j['id'] == 'golden:default-miss']
    check_baseline(groups, test)
    stage('baseline of the mutant groups')
    if study:
        return run_study(groups, source, args[1:])

    killed = []
    for name, breaks, edits, group in MUTANTS:
        text = source
        for old, new in edits:
            require(text.count(old) == 1, f'mutant {name}: edit applies once')
            text = text.replace(old, new)
        wasm = BUILD / f'mutant-{name}.wasm'
        if group == 'shape':
            wasm.write_bytes(build.assemble(text))
            reached = module_shape(wasm)['reaches_itself']
            require(reached is not None, f'mutant {name} survives the call-graph check')
            killed.append({'mutant': name, 'breaks': breaks, 'group': group,
                           'killed_by': [f'function {reached} reaches itself'], 'wrong_observations': 1, 'crashes': 0})
            continue
        wasm.write_bytes(build.assemble(build.test_source(text)))
        batch = [{**{k: v for k, v in j.items() if k not in ('want', 'dump')}, 'wasm': str(wasm),
                  'deadline': deadline(j, group)} for j in groups[group]]  # a hang ends as a Timeout
        if group in ('ceiling', 'full-heap', 'trap'):  # about 4 GiB each: one process per run
            out = run_group(batch, group)
        else:
            out = harness(batch, node_flags=next(iter(groups[group]), {}).get('flags', ()), max_timeouts=1 if group in ('hang', 'scope') else None)
        refusal = group == 'refused'  # the frozen outcome is the host's refusal: a trap, whose registers are the observation
        crashed = [j['id'] for j in groups[group] if not (out[j['id']]['status'] == 'Trap' if refusal else
                                                          clean(out[j['id']]) or out[j['id']]['status'] in ('Timeout', 'Skipped') and group == 'hang')]
        if group == 'hang':  # the frozen outcome always ends: a row that outlives its deadline is the wrong observation
            wrong = [j['id'] for j in groups[group] if out[j['id']]['status'] == 'Timeout']
        elif group in ('traps', 'memory-end'):  # no frozen run is a trap: a row that traps is the wrong observation, and every other row stays right
            wrong = [j['id'] for j in groups[group] if out[j['id']]['status'] == 'Trap']
            askew = [j['id'] for j in groups[group] if out[j['id']]['status'] != 'Trap'
                     and not (clean(out[j['id']]) and not observed_wrong(j, out[j['id']]))]
            require(not askew, f'mutant {name}: rows that do not trap are wrong too: {askew[:5]}')
        elif group == 'trap':  # the frozen outcome is never a trap, so a trap is the wrong observation
            wrong = [j['id'] for j in full_heap if out[j['id']]['status'] == 'Trap']
            right = [j['id'] for j in groups[group] if j not in full_heap
                     and clean(out[j['id']]) and not observed_wrong(j, out[j['id']])]
            require(len(wrong) == len(full_heap) and len(right) == len(groups[group]) - len(full_heap),
                    f'mutant {name}: traps {wrong}, right {right}')
        else:
            wrong = [j['id'] for j in groups[group] if (refusal or clean(out[j['id']])) and observed_wrong(j, out[j['id']])]
        require(wrong, f'mutant {name} survives group {group} (crashes: {crashed[:5]})')
        killed.append({'mutant': name, 'breaks': breaks, 'group': group, 'killed_by': wrong[:5],
                       'wrong_observations': len(wrong), 'crashes': len(crashed)})
    record['mutants'] = killed

    record['status'] = 'passed'
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(record, indent=1) + '\n')
    print(f"vm-core passed: {len(goldens)} golden images, {len(invocations)} Book invocations, {len(core)} fixture runs, "
          f"{len(dumps)} dump rows, {len(agreed)} runs equal to the reference evaluation, "
          f"{len(seeded_rows['rows'])} seeded rows, a lane of {record['lane']['rows']} rows (seed {record['lane']['seed']}; "
          f"{record['lane']['sample']['rows']} run again through the seed), {sum(record['both'].values())} admitted images "
          f"through both, {len(high)} ceiling runs, {len(ends)} memory-end runs, {len(growth)} growth runs, {len(stack)} small-stack runs, "
          f"{len(refused)} refused and {len(admissions)} admitted controls, "
          f"{len(record['scope']['rows'])} scope rows and {record['scope']['corpus']['images']} scope images, "
          f"{len(word_rows)} argument controls, "
          f"{len(corpus)} fuzz images "
          f"({tally['refused']} refused, {tally['accepted']} admitted), "
          f"{len(words_corpus)} limit-word images "
          f"({words_tally['refused']} refused, {words_tally['limits']} of them at a limit, {words_tally['accepted']} admitted), "
          f"{len(killed)} killed mutants; {RECEIPT.relative_to(ROOT)}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
