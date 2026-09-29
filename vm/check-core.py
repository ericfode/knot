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
  (among them where a Nat Case's predecessor is made against its Scope push);
  and Books whose frozen run the reference evaluation (vm/evaluate.py) must
  also give (Chr's operand, a Big predecessor);
- the ceiling fixtures: Books and a Program whose bump pointer ends near or
  exactly at 4 GiB, described exactly or completed, or Exhausted kind 2 (heap)
  where a cell or the text would end beyond it. Each row's bump pointer and
  outcome are first derived from SPEC section 5's cell sizes over its plan
  (`ceiling_run`), independently of any VM;
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
- WAT mutants, each killed by a named fixture group through a wrong
  observation (a trap, host stack failure or timeout never counts, except for
  group `trap`, whose defect is the trap).

It writes only vm/receipts/core.json.
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
codec = spec.codec


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
    A cell may end exactly at 4 GiB; one that would end beyond raises `Beyond`. A String
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
            require((t, mode, default) == (rep['Nat'], 'tags', None), 'the model cases on Nat only')
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
        if op == 'con' and node[1] not in (rep['Nat'], rep['Char']):
            take(cell(2 + len(ops)))
            return ('obj', node[1], node[2], tuple(ops))
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


def harness(jobs: list, timeout=600, node_flags=()) -> dict:
    p = subprocess.run(['node', *node_flags, str(HARNESS)], input=json.dumps(jobs), capture_output=True, text=True,
                       timeout=timeout * SCALE)
    require(p.returncode == 0, f'harness failed: {p.stderr[-2000:]}')
    return {r['id']: r for r in map(json.loads, p.stdout.splitlines())}


def clean(result: dict) -> bool:
    """A reported outcome, not an engine trap, host stack failure or host error."""
    stderr = result['stderr']
    return result.get('status') not in ('Trap', 'HostStack') and not any(
        s in stderr for s in ('HostFailure\tio\ttrap', 'HostFailure\tio\thost', 'Exhausted\tio\tcall-stack'))


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
]


# ------------------------------------------------------------------ main
def main() -> int:
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
                   HERE / 'check-core.py', HERE / 'SPEC.md', HERE / 'serializer.py', HERE / 'registry.json', HOST,
                   HERE / 'check-spec.py', HERE / 'evaluate.py', HERE / 'golden/vm-expected.json',
                   *(HERE / 'core').glob('*')])}}

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

    # the Book invocations vm-spec froze with the goldens (SPEC section 8's walk)
    invoked = [(f"{n} {' '.join(row['argv'][1:])}", n, row) for n in sorted(expected.get('invocations', {}))
             for row in expected['invocations'][n]]
    invocation_argv = {label: [a if a != 'IMAGE' else f'{n}.kimg' for a in row['argv']] for label, n, row in invoked}
    got = dict(zip([c[0] for c in invoked], pool(lambda c: host(module, golden, invocation_argv[c[0]]), invoked)))
    traced = harness([{'id': label, 'wasm': str(test), 'files': {f'{n}.kimg': str(golden / f'{n}.kimg')},
                       'argv': invocation_argv[label], 'trace': 'audit'} for label, n, _ in invoked])
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
    for l in fixtures['limited']:  # a pinned bump under a lowered heap: section 5's model stops there too
        if l['dump'].get('cause') == 'heap' and 'bump' in l['dump']:
            plan, image = json.loads((HERE / f"{l['image']}.plan.json").read_text()), (HERE / f"{l['image']}.kimg").read_bytes()
            try:
                stop = ceiling_run(plan, image, l['limits']['heap'])
            except Beyond as beyond:
                stop = beyond.bump
            require(stop == l['dump']['bump'], f"limited {l['name']}: frozen bump {l['dump']['bump']}, section 5 gives {stop}")
    dumped = harness(jobs)
    dumps = []
    for name, want in [*fixtures['dumps'].items(), *((l['name'], l['dump']) for l in fixtures['limited'])]:
        got, state = dumped[name], dumped[name]['state']
        seen = {'outcome': state['outcome'], 'kind': state['kind'], 'cause': state['cause'],
                'calls': state['calls'], 'yields': got['yields'], 'top': state['top'], 'bump': state['bump']}
        require(all(seen[k] == v for k, v in want.items()), f'dump {name}: {seen} vs {want}')
        dumps.append({'name': name, **{k: seen[k] for k in want}})
    record['fixtures'] = {'runs': core, 'dumps': dumps}

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
    ran = pool(lambda r: host(module, sandbox, [staged(r['image']), *r['argv']]), ceiling, workers=2)
    dumped = {j['id']: harness([j])[j['id']] for j in ceiling_jobs}
    high = []
    for r, got in zip(ceiling, ran):
        dump, state = dumped[r['name']], dumped[r['name']]['state']
        require(got == r['expect'], f"ceiling {r['name']}: {got} vs {r['expect']}")
        require((dump['exit'], dump['stdout']) == (got['exit'], got['stdout']), f"ceiling {r['name']}: harness and host differ")
        require(all(state[k] == v for k, v in r['dump'].items()), f"ceiling {r['name']}: {state} vs {r['dump']}")
        high.append({'name': r['name'], 'exit': got['exit'], 'stdout_sha256': sha(got['stdout'].encode()), **r['dump']})
    record['ceiling'] = high

    # heap growth (CORE.md choice 15): a stream of small cells reaches the heap's end, or a host's refusal
    # to grow, in bounded time. SPEC section 5 leaves the timing of memory.grow free; growing one 64 KiB
    # page at a time costs 22 minutes at 4 GiB on V8, which section 11 counts as neither Exhausted nor agreement
    loop_plan = json.loads((HERE / 'core/loop-cells.plan.json').read_text())
    loop_image = (HERE / 'core/loop-cells.kimg').read_bytes()
    require(codec.encode(loop_plan, digest) == loop_image, "growth: the image is its plan's encoding")
    growth = growth_jobs(fixtures['growth']['rows'], loop_plan, loop_image, staged('core/loop-cells'), sandbox)
    record['growth'] = check_growth(growth, module, test)

    # nothing recurses: a 200,000-deep nested expression, and the deep runs on a 64 KiB host stack
    small = nested_plan(40)
    require(nested_image(40, digest) == codec.encode(small, digest), 'the nested generator matches serializer.encode')
    deep = nested_image(NEST, digest)
    (sandbox / 'nested.kimg').write_bytes(deep)
    stack = {}
    for label, argv in [('nested-200k', ['nested.kimg', 'main', str(NEST + 2)]),
                        ('deep-250k', [staged('core/deep-250k'), 'main', '500003']),
                        ('render-list', [staged('core/render-list'), 'main', '1000000'])]:
        got = host(module, sandbox, argv, (SMALL_STACK,))
        want = by_name.get(label, {}).get('expect') or {'exit': 0, 'stdout': 'Evaluated\t1\t1\tTrue{}\n', 'stderr': ''}
        require(got == want, f'{label} under {SMALL_STACK}: {got}')
        stack[label] = {'exit': got['exit'], 'stdout_sha256': sha(got['stdout'].encode())}
    stack['nested-200k'].update(words=len(deep) // 4, sha256=sha(deep), fuel=NEST + 2)
    record['host_stack'] = {'node_flag': SMALL_STACK, 'runs': stack}

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

    fuzz = BUILD / 'fuzz'
    fuzz.mkdir()
    corpus = fuzz_corpus(images, reg, digest, fuzz)
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
                     'argv': [staged(l['image']), *l['argv']], 'limits': l['limits'], 'want': expected_run(l['dump']),
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
              'image-limits': image_limits, 'limit-words': word_jobs}

    def observed_wrong(job, out):
        return shown(out, job['want']) != job['want'] or any(out['state'][k] != v for k, v in job.get('dump', {}).items())

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
        batch = [{**{k: v for k, v in j.items() if k not in ('want', 'dump')}, 'wasm': str(wasm)} for j in groups[group]]
        if group in ('ceiling', 'full-heap', 'trap'):  # about 4 GiB each: one process per run
            out = {k: v for part in pool(lambda j: harness([j]), batch, workers=2) for k, v in part.items()}
        else:
            out = harness(batch)
        crashed = [j['id'] for j in groups[group] if not clean(out[j['id']])]
        if group == 'trap':  # the frozen outcome is never a trap, so a trap is the wrong observation
            wrong = [j['id'] for j in full_heap if out[j['id']]['status'] == 'Trap']
            right = [j['id'] for j in groups[group] if j not in full_heap
                     and clean(out[j['id']]) and not observed_wrong(j, out[j['id']])]
            require(len(wrong) == len(full_heap) and len(right) == len(groups[group]) - len(full_heap),
                    f'mutant {name}: traps {wrong}, right {right}')
        else:
            wrong = [j['id'] for j in groups[group] if clean(out[j['id']]) and observed_wrong(j, out[j['id']])]
        require(wrong, f'mutant {name} survives group {group} (crashes: {crashed[:5]})')
        killed.append({'mutant': name, 'breaks': breaks, 'group': group, 'killed_by': wrong[:5],
                       'wrong_observations': len(wrong), 'crashes': len(crashed)})
    record['mutants'] = killed

    record['status'] = 'passed'
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(record, indent=1) + '\n')
    print(f"vm-core passed: {len(goldens)} golden images, {len(invocations)} Book invocations, {len(core)} fixture runs, "
          f"{len(dumps)} dump rows, {len(agreed)} runs equal to the reference evaluation, "
          f"{len(high)} ceiling runs, {len(growth)} growth runs, {len(stack)} small-stack runs, "
          f"{len(refused)} refused and {len(admissions)} admitted controls, "
          f"{len(word_rows)} argument controls, "
          f"{len(corpus)} fuzz images "
          f"({tally['refused']} refused, {tally['accepted']} admitted), "
          f"{len(words_corpus)} limit-word images "
          f"({words_tally['refused']} refused, {words_tally['limits']} of them at a limit, {words_tally['accepted']} admitted), "
          f"{len(killed)} killed mutants; {RECEIPT.relative_to(ROOT)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
