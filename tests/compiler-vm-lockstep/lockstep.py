"""Lockstep comparison of knot-vm-1 (vm/vm.wat) with its Bend model (vm/model/).

Both sides print the machine's complete state before its first transition and
after each one, in one line format (vm/model-trace.bend, js/vm-trace.mjs):

    step | control | act | fuel calls quantum | top | frames | bump | free | output | heap

`compare` matches the two lines of one step. The VM does not reclaim yet (vm/CORE.md
choice 1: rc stays 1, free lists stay empty), while the model does (SPEC section 5).
So a state is compared at one of two strengths:

- `layout`: the model has freed nothing and both bump pointers agree. Every word of
  the heap must be equal, except each cell's rc word, of which only immortality is
  compared. Addresses are identical.
- `graph`: after the model's first reclamation the two heaps differ in addresses and
  rc by construction. The words held by every root (control, `act`, frame values) are
  matched one to one, and each pair of cells they reach must have the same class,
  header, metadata words, padding and edges, edges being matched in turn. rc, free
  lists and unreachable memory are excluded. Cells below the load-time bump pointer
  (constants, the terminal continuation) are immortal and must be the same address.

`exact` is the strength vm-rc adds: identity of addresses, rc and free lists. It is
implemented and controlled here, and is not applied to the VM until it reclaims.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

IMMORTAL = 0xFFFFFFFF
# Class -> index of the first owning edge in the payload (SPEC section 5's table):
# Object [type, tag | fields], Closure [node | captures], Big [value], Action
# [foreign | operands], Activation [owner, depth | slots].
EDGES = {0: 2, 1: 1, 2: None, 3: 1, 4: 2}


@dataclass
class State:
    step: int
    ctl: tuple
    act: int
    fuel: int
    calls: int
    quantum: int
    top: int              # words the frames occupy
    frames: list          # top of the stack first: (kind, node, aux, n, values)
    bump: int             # bytes
    free: list            # nonzero free-list heads, as (class, address)
    out: tuple            # one tuple of codes per printed line, in order
    heap: list = field(repr=False)   # every word from H0 to the bump pointer
    text: str = field(repr=False, default='')

    @property
    def h0(self) -> int:
        return self.bump - 4 * len(self.heap)

    def halted(self) -> bool:
        return self.ctl[0] == 'H'


def ints(text: str) -> list:
    return [int(w) for w in text.split()]


def codes(text: str) -> tuple:
    return tuple(int(c) for c in text.split(',') if c)


def parse_ctl(text: str) -> tuple:
    head, _, rest = text.partition(' ')
    if head in ('E', 'R'):
        return (head, int(rest))
    if head == 'N':
        kind, _, tail = rest.partition(' ')
        words = ints(tail)
        return ('N', kind, words[0], tuple(words[1:]))
    if head == 'H':
        tag, _, tail = rest.partition(' ')
        if tag == 'D':
            result, tag_, tree = tail.split(' ', 2)
            return ('H', 'D', int(result), int(tag_), codes(tree))
        if tag == 'Z':
            code, _, message = tail.partition(' ')
            return ('H', 'Z', int(code), codes(message))
        if tag == 'S':
            stop, _, pending = tail.partition('@')
            return ('H', 'S', stop, pending)
        return ('H', tag, tail)
    raise ValueError(f'control {text!r}')


def parse_frame(text: str) -> tuple:
    w = [int(x) for x in text.split(',')]
    return (w[0], w[1], w[2], w[3], tuple(w[4:]))


def parse(line: str, side: str) -> State:
    """A state line; `side` is 'model' (bump in words) or 'vm' (bump in bytes)."""
    step, ctl, act, meter, top, frames, bump, free, out, heap = line.rstrip('\n').split('|', 9)
    fuel, calls, quantum = ints(meter)
    heads = [(i, h) for i, h in enumerate(ints(free)) if h]
    return State(int(step), parse_ctl(ctl), int(act), fuel, calls, quantum, int(top),
                 [parse_frame(f) for f in frames.split(';')] if frames else [],
                 int(bump) * (4 if side == 'model' else 1), heads,
                 tuple(codes(o) for o in out.partition(':')[2].split('/')) if out.partition(':')[2] or out.partition(':')[0] != '0' else (),
                 ints(heap), line)


@dataclass
class Divergence:
    step: int
    field: str
    detail: str
    model: object = None
    vm: object = None

    def report(self) -> dict:
        return {'step': self.step, 'field': self.field, 'detail': self.detail,
                'model': self.model, 'vm': self.vm}


def size_words(payload: int) -> int:
    n = 4
    while n < payload + 2:
        n *= 2
    return n


class Heap:
    """A side's heap words, read by byte address."""

    def __init__(self, state: State):
        self.words, self.h0, self.end = state.heap, state.h0, state.bump

    def cell(self, address: int):
        if address & 7 or address < self.h0 or address + 8 > self.end:
            return None
        i = (address - self.h0) // 4
        hdr = self.words[i + 1]
        payload, cls = hdr >> 3, hdr & 7
        size = size_words(payload)
        if cls > 4 or address + 4 * size > self.end:
            return None
        return self.words[i], hdr, self.words[i + 2:i + 2 + payload], self.words[i + 2 + payload:i + size]


def pointer(w: int) -> bool:
    return w != 0 and not w & 1


class Bijection:
    """Roots and edges matched one to one, model address to VM address."""

    def __init__(self, model: State, vm: State, immortal: int):
        self.m, self.v = Heap(model), Heap(vm)
        self.immortal, self.to_vm, self.to_model = immortal, {}, {}
        self.work: list = []
        self.cells = 0

    def word(self, wm: int, wv: int, where: str, identity: bool = False):
        if wm == wv and not pointer(wm):
            return None
        if not (pointer(wm) and pointer(wv)):
            return f'{where}: model word {wm}, VM word {wv}'
        if wm < self.immortal or wv < self.immortal or identity:
            return None if wm == wv else f'{where}: model cell {wm}, VM cell {wv} (an immortal cell keeps its address)'
        if self.to_vm.get(wm, wv) != wv or self.to_model.get(wv, wm) != wm:
            return f'{where}: model cell {wm} is matched with VM cell {self.to_vm.get(wm)}, not {wv}'
        if wm not in self.to_vm:
            self.to_vm[wm], self.to_model[wv] = wv, wm
            self.work.append((wm, wv, where))
        return None

    def run(self):
        while self.work:
            wm, wv, where = self.work.pop()
            cm, cv = self.m.cell(wm), self.v.cell(wv)
            if cm is None or cv is None:
                return f'{where}: cell {wm if cm is None else wv} of the {"model" if cm is None else "VM"} is not a whole cell'
            self.cells += 1
            (_, hm, pm, gm), (_, hv, pv, gv) = cm, cv
            cls = hm & 7
            if hm != hv:
                return f'{where}: header of model cell {wm} is {hm}, of VM cell {wv} is {hv}'
            first = EDGES[cls]
            for i, (a, b) in enumerate(zip(pm, pv)):
                if first is not None and i >= first:
                    bad = self.word(a, b, f'{where} -> cell field {i}')
                    if bad:
                        return bad
                elif a != b:
                    return f'{where}: word {i} of the payload of model cell {wm} is {a}, of VM cell {wv} is {b}'
            if gm != gv:
                return f'{where}: padding of model cell {wm} is {gm}, of VM cell {wv} is {gv}'
        return None


def layout_diff(model: State, vm: State):
    """Cell by cell, every word but rc; rc is compared only as immortal or not."""
    if len(model.heap) != len(vm.heap):
        return f'the heaps hold {len(model.heap)} and {len(vm.heap)} words'
    i = 0
    while i < len(model.heap):
        hdr = model.heap[i + 1] if i + 1 < len(model.heap) else 0
        size = size_words(hdr >> 3)
        if (model.heap[i] == IMMORTAL) != (vm.heap[i] == IMMORTAL):
            return f'cell {model.h0 + 4 * i}: rc {model.heap[i]} (model) against {vm.heap[i]} (VM): only one is immortal'
        for j in range(1, size):
            if i + j >= len(model.heap) or model.heap[i + j] != vm.heap[i + j]:
                return f'cell {model.h0 + 4 * i} word {j}: model {model.heap[i + j:i + j + 1]}, VM {vm.heap[i + j:i + j + 1]}'
        i += size
    return None


def frames_diff(model: State, vm: State, bij: Bijection | None):
    if len(model.frames) != len(vm.frames):
        return f'{len(model.frames)} frames (model) against {len(vm.frames)} (VM)'
    for depth, (fm, fv) in enumerate(zip(model.frames, vm.frames)):
        if fm[:4] != fv[:4]:
            return f'frame {depth} from the top: model {fm[:4]}, VM {fv[:4]}'
        for i, (a, b) in enumerate(zip(fm[4], fv[4])):
            bad = bij.word(a, b, f'frame {depth} value {i}') if bij else (None if a == b else f'frame {depth} value {i}: {a} against {b}')
            if bad:
                return bad
    return None


def ctl_words(ctl: tuple) -> list:
    """(where, word) pairs of a control that hold values."""
    if ctl[0] == 'R':
        return [('result', ctl[1])]
    if ctl[0] == 'N':
        return ([('target', ctl[2])] if ctl[1] == 'W' else []) + [(f'operand {i}', w) for i, w in enumerate(ctl[3])]
    return []


def outcome_diff(model: tuple, vm: tuple):
    """A halting control: the outcome and its data. A stop's pending control is not
    compared (the VM keeps only registers, not which control it could not advance)."""
    if model[:2] != vm[:2]:
        return f'{model[:2]} against {vm[:2]}'
    if model[1] == 'S':
        return None if model[2] == vm[2] else f'stop {model[2]} against {vm[2]}'
    return None if model == vm else f'{model} against {vm}'


# Where a halting transition is not atomic in the VM. SPEC section 6 says an ill-typed word
# halts "before the step changes any state", and the model's transitions are atomic, so it
# keeps the state the step began in. The VM (vm/CORE.md choice 8) halts with the change
# already made in two places, and no control observes it. Each relation is accepted only at
# the halts it names, and every use is counted in the receipt.
CHOICE_8 = 'choice 8: a Gather frame is popped before its operands are inspected'
CHOICE_8_TOP = 'choice 8: the Activation is released before the final IO.OP is inspected'
POPPED_BEFORE = ('F:image:ill-typed', 'E:2:NatRange')


def halting_relation(model: State, vm: State, ignore: frozenset = frozenset()):
    """The documented difference between a model halt and a VM halt, or None. A dimension in
    `ignore` is not part of the relation either."""
    stop = model.ctl[2] if model.ctl[:2] == ('H', 'S') else None
    if stop not in POPPED_BEFORE:
        return None
    if model.frames and model.frames[0][0] == 1:
        n = model.frames[0][3]
        if ('frames' in ignore or model.frames[1:] == vm.frames) and ('top' in ignore or model.top - (n + 3) == vm.top):
            return CHOICE_8
    if stop == 'F:image:ill-typed' and ('frames' in ignore or model.frames == vm.frames) and vm.act == 0 and model.act != 0:
        return CHOICE_8_TOP
    return None


DIMENSIONS = ('fuel', 'calls', 'quantum', 'out', 'outcome', 'top', 'frames', 'act', 'heap')


def compare(model: State, vm: State, mode: str = 'auto', halting: str = 'strict', notes: list | None = None,
            ignore: frozenset = frozenset(), boot: int | None = None):
    """(divergence or None, strength). `halting` is 'strict' (frames and heap compared at a halt
    as at any state, but for the relations above) or 'outcome' (only the outcome, meters, output).
    A relation used is appended to `notes`. `ignore` names dimensions of DIMENSIONS the comparison
    skips: the gate's harness mutants weaken it that way and require the weakening to be caught.
    `boot` is the bump pointer after loading: everything below it (the constants and the terminal
    continuation) is immortal and must stay word for word equal at every state, whatever the strength."""
    d = lambda field, detail, a=None, b=None: Divergence(model.step, field, detail, a, b)
    notes = [] if notes is None else notes
    if model.step != vm.step:
        return d('step', 'the traces are out of step', model.step, vm.step), None
    for name in ('fuel', 'calls', 'quantum', 'out'):
        if name not in ignore and getattr(model, name) != getattr(vm, name):
            return d(name, f'{name} differs', getattr(model, name), getattr(vm, name)), None
    if model.halted() != vm.halted():
        return d('control', 'one side halted', model.ctl, vm.ctl), None
    if model.halted():
        bad = None if 'outcome' in ignore else outcome_diff(model.ctl, vm.ctl)
        if bad:
            return d('outcome', bad, model.ctl, vm.ctl), None
    elif model.ctl[0] != vm.ctl[0]:
        return d('control', 'the controls are of different kinds', model.ctl, vm.ctl), None
    strength = mode
    if mode == 'auto':
        strength = 'layout' if not model.free and model.bump == vm.bump else 'graph'
    boot = model.h0 if boot is None else boot
    bij = Bijection(model, vm, boot) if strength == 'graph' else None

    def word(a, b, where):
        if bij:
            return bij.word(a, b, where)
        return None if a == b else f'{where}: model {a}, VM {b}'

    relation = halting_relation(model, vm, ignore) if model.halted() else None
    if relation:
        notes.append(relation)
    if 'heap' not in ignore and strength == 'graph':
        n = (boot - model.h0) // 4
        if model.h0 != vm.h0 or model.heap[:n] != vm.heap[:n]:
            at = next((i for i in range(min(n, len(model.heap), len(vm.heap))) if model.heap[i] != vm.heap[i]), None)
            return d('heap', f'an immortal word changed: word {at} of the constants is {model.heap[at:at + 1]} (model), '
                             f'{vm.heap[at:at + 1]} (VM)' if at is not None else 'the constants differ'), strength
    if 'heap' not in ignore and strength == 'graph' and model.bump > vm.bump:
        return d('heap', 'the model has allocated more than the VM: a reclaiming machine never does', model.bump, vm.bump), strength
    if 'heap' not in ignore and strength != 'graph':
        bad = None if strength == 'layout' else (
            None if (model.heap, model.free, model.bump) == (vm.heap, vm.free, vm.bump)
            else 'the heaps, free lists or bump pointers differ')
        bad = layout_diff(model, vm) if strength == 'layout' else bad
        if bad:
            return d('heap', bad), strength
    if not model.halted():
        if model.ctl[0] == 'E' and model.ctl != vm.ctl:
            return d('control', 'Eval node differs', model.ctl, vm.ctl), strength
        if model.ctl[0] == 'N' and (model.ctl[1] != vm.ctl[1] or len(model.ctl[3]) != len(vm.ctl[3])):
            return d('control', 'Enter differs', model.ctl, vm.ctl), strength
        if model.ctl[0] == 'N' and model.ctl[1] == 'F' and model.ctl[2] != vm.ctl[2]:
            return d('control', 'Enter targets another function', model.ctl, vm.ctl), strength
        for (where, a), (_, b) in zip(ctl_words(model.ctl), ctl_words(vm.ctl)):
            bad = word(a, b, f'control {where}')
            if bad:
                return d('control', bad, model.ctl, vm.ctl), strength
    if not model.halted() or halting == 'strict':
        top, frames = model.top, model.frames
        if relation == CHOICE_8:
            top, frames = model.top - (frames[0][3] + 3), frames[1:]
        if 'top' not in ignore and top != vm.top:
            return d('top', 'the frames occupy different numbers of words', model.top, vm.top), strength
        if 'frames' not in ignore:
            bad = frames_diff(replace(model, frames=frames), vm, bij)
            if bad:
                return d('frames', bad), strength
    if 'act' not in ignore and relation != CHOICE_8_TOP:
        bad = word(model.act, vm.act, 'act')
        if bad:
            return d('act', bad, model.act, vm.act), strength
    if bij and 'heap' not in ignore:
        bad = bij.run()
        if bad:
            return d('heap', bad), strength
    return None, strength


# ------------------------------------------------------------------ driving both sides
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRACE_JS = ROOT / 'tests/compiler-vm-lockstep/js/vm-trace.mjs'


def run_model(binary: Path, image: Path, argv: list, timeout: int = 600, window=(1, 1, 0)) -> list:
    done = subprocess.run([str(binary), '--', *(str(x) for x in window), str(image), *argv],
                          capture_output=True, text=True, timeout=timeout)
    if done.returncode not in (0,):
        return [f'#exit {done.returncode} {done.stderr.strip()}']
    return done.stdout.splitlines()


def trailer(lines: list) -> tuple[list, dict]:
    """The states of a trace and its `#name value` trailer lines."""
    states = [l for l in lines if not l.startswith('#yields')]
    extra = {l.split(' ', 1)[0][1:]: l.split(' ', 1)[1] if ' ' in l else '' for l in lines if l.startswith('#yields')}
    return states, extra


def run_vm(wasm: Path, image: Path, argv: list, timeout: int = 600, window=(1, 1, 0)) -> list:
    done = subprocess.run(['node', str(TRACE_JS), str(wasm), *(str(x) for x in window), str(image), *argv],
                          capture_output=True, text=True, timeout=timeout)
    if done.returncode != 0:
        return [f'#exit {done.returncode} {done.stderr.strip()[:400]}']
    return done.stdout.splitlines()


def refusal_text(lines: list, side: str):
    """The stop line of a run that never entered: the model prints it to stderr and exits
    (`#exit N text`), the VM's tracer prints `R text`. None for a trace."""
    if not lines:
        return None
    first = lines[0]
    if side == 'model' and first.startswith('#exit '):
        return first.split(' ', 2)[2].strip()
    if first.startswith('R '):
        return first[2:].strip()
    return None


def effect_of(state: State):
    """(step, phase, offending frame kinds) when the state applies an Action to a continuation,
    the eager effect of the reference reading (SPEC section 7): an Enter of an Action cell (class
    3) with one operand. `phase` is the bottom Top frame's (0 Book, 1 to 3 Program). D23 moves the
    effect to the Program's Top loop, and eager and D23 agree exactly when only Scope and Call
    frames, which return a value unread, lie between the effect and Top."""
    if state.ctl[:2] != ('N', 'W') or len(state.ctl[3]) != 1 or not state.frames:
        return None
    cell = Heap(state).cell(state.ctl[2])
    if cell is None or cell[1] & 7 != 3:
        return None
    others = [f[0] for f in state.frames[:-1] if f[0] not in (3, 4)]
    return {'step': state.step, 'phase': state.frames[-1][2], 'blocked_by': others}


def classify_effects(effects: list) -> str:
    """'none': no effect. 'spine': every effect meets Top through Scope and Call frames only,
    in a Program, where eager and D23 give one trace. 'pending-D23': an effect under a Book
    (D22 refuses it), or one whose request another frame would inspect or drop."""
    if not effects:
        return 'none'
    if all(e['phase'] != 0 and not e['blocked_by'] for e in effects):
        return 'spine'
    return 'pending-D23'


def lockstep(model_lines: list, vm_lines: list, mode: str = 'auto', halting: str = 'strict', same_refusal=None,
             ignore: frozenset = frozenset()) -> dict:
    """Compare the two traces state by state. The result names the first divergence."""
    res = {'steps': 0, 'strength': {'layout': 0, 'graph': 0, 'exact': 0}, 'divergence': None, 'final': None,
           'notes': [], 'refused': None, 'states': 0, 'effects': []}
    vm_lines, _ = trailer(vm_lines)
    rm, rv = refusal_text(model_lines, 'model'), refusal_text(vm_lines, 'vm')
    if rm is not None or rv is not None:
        res['refused'] = rm or rv
        agree = (rm == rv) if same_refusal is None else same_refusal(rm, rv)
        if not (rm is not None and rv is not None and agree):
            res['divergence'] = Divergence(0, 'refusal', 'the sides refuse differently', rm, rv)
        return res
    for side, lines in (('model', model_lines), ('vm', vm_lines)):
        if lines and lines[0].startswith('#'):
            res['divergence'] = Divergence(0, 'harness', f'the {side} did not produce a trace', lines[0][:300])
            return res
    boot = None
    for i in range(max(len(model_lines), len(vm_lines))):
        if i >= len(model_lines) or i >= len(vm_lines):
            res['divergence'] = Divergence(i, 'length', 'one trace ends before the other', len(model_lines), len(vm_lines))
            return res
        m, v = parse(model_lines[i], 'model'), parse(vm_lines[i], 'vm')
        boot = m.bump if i == 0 else boot
        effect = effect_of(m)
        if effect:
            res['effects'].append(effect)
        bad, strength = compare(m, v, mode, halting, res['notes'], ignore, boot)
        res['steps'], res['states'] = m.step, res['states'] + 1
        if strength:
            res['strength'][strength] += 1
        if bad:
            res['divergence'] = bad
            return res
        res['final'] = m.ctl
    res['effect_class'] = classify_effects(res['effects'])
    return res
