#!/usr/bin/env python3
"""Gate vm-lockstep: knot-vm-1 in WAT (vm/vm.wat) against its Bend model (vm/model/), transition
by transition, and against the pinned eval-cli on value.

Nothing under vm/ changes. The gate builds the model's trace entry (vm/model-trace.bend) with the
seed's native lane and drives the test build of the VM (`vm_boot`, `vm_step`, `vm_dump`, and linear
memory) one transition at a time, then requires:
- the pins of vm/build.json hold: vm/vm.wat and vm/vm.wasm reassemble byte for byte, so the release
  module the gate reports is the one vm-core pinned;
- for every run of the frozen sets vm-model and vm-core already enumerate (the 93 goldens, their 44
  Book invocations, every golden at fuel 0, the admitted, inspection and argument controls), the
  complete machine state, before the first transition and after each one, is the same in both
  machines (tests/compiler-vm-lockstep/lockstep.py: registers, frames, output and every cell the
  roots reach; the constants word for word); a halting transition may differ from the model's atomic
  one only by the two relations CORE.md choice 8 documents, counted and frozen;
- the refusals the controls freeze are refused by both machines alike;
- two long runs (a 70,000-entry tail loop and a 40,000-deep recursion, each crossing the 65,536-entry
  quantum) agree in sampled states and at every state around the yield;
- the exact strength (identity of addresses, rc and free lists) holds between the model and itself and
  is refused where the model first reclaims, which is what vm-rc will change;
- the VM's release module, through the real host, equals the frozen expectation and, live, the pinned
  eval-cli under the Exhausted-lane rule (SPEC section 11) on every golden and Book invocation;
- every Program's effects are classified as eager and D23 give one trace (`spine`) or as pending D23,
  against the classes frozen by literal review;
- VM mutants, model mutants and harness weakenings, each killed at a named state through a wrong
  observation; the state-only ones first shown to leave every output-level observation intact.

It writes only tests/compiler-vm-lockstep/receipts/lockstep.json.
"""
from __future__ import annotations

import datetime
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'vm'
LS = ROOT / 'tests/compiler-vm-lockstep'
GOLDEN = HERE / 'golden'
BUILD = ROOT / '.local/vm-lockstep/gate'
RECEIPT = LS / 'receipts/lockstep.json'
SEED = ROOT / 'scripts/bend-reference'
HOST = ROOT / 'scripts/run-wasm-io.mjs'
SCALE = float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))  # hang guard only
WORKERS = 8
sys.path.insert(0, str(LS))


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


L = load('lockstep', LS / 'lockstep.py')
R = load('lockstep_runs', LS / 'runs.py')
vm_build = load('vm_build', HERE / 'build.py')
cs = R.load('check_spec', HERE / 'check-spec.py')
cc = R.load('check_core', HERE / 'check-core.py')
codec = cs.codec
REGISTRY = codec.registry()
DIGEST = codec.base_digest(REGISTRY)
EXPECTED = json.loads((LS / 'frozen.json').read_text())
VM_EXPECTED = json.loads((GOLDEN / 'vm-expected.json').read_text())


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(argv, timeout, cwd=ROOT):
    argv = [str(x) for x in argv]
    try:
        p = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout * SCALE,
                           env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
    except subprocess.TimeoutExpired:
        return {'exit': None, 'stdout': '', 'stderr': 'harness-timeout'}
    return {'exit': p.returncode, 'stdout': p.stdout.decode('utf-8', 'replace'), 'stderr': p.stderr.decode('utf-8', 'replace')}


def pool(fn, items, workers=WORKERS):
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, items))


# ------------------------------------------------------------------ builds

MODEL_SOURCES = [*(f'model/{s}.bend' for s in ('word', 'decode', 'validate', 'encode', 'memory', 'machine', 'audit')),
                 'model-cli.bend', 'model-trace.bend']
TRACE_SOURCES = ['model-trace.bend', '../tests/compiler-vm-lockstep/lockstep.py',
                 '../tests/compiler-vm-lockstep/js/vm-trace.mjs']


def build_model(name: str, section: str | None = None, mutation=()) -> Path:
    tree = BUILD / 'model' / name
    (tree / 'vm' / 'model').mkdir(parents=True, exist_ok=True)
    for source in MODEL_SOURCES:
        text = (HERE / source).read_text()
        if section and source == f'model/{section}.bend':
            for old, new in mutation:
                require(text.count(old) == 1, f'model mutant {name}: {old!r} occurs {text.count(old)} times')
                text = text.replace(old, new)
        (tree / 'vm' / source).write_text(text)
    out = tree / 'model-trace'
    got = run([SEED, tree / 'vm/model-trace.bend', '-o', out], 900)
    require(got['exit'] == 0 and out.exists(), (name, got['stderr'][-1500:]))
    return out


def build_vm(name: str, edits=()) -> Path:
    text = (HERE / 'vm.wat').read_text()
    for old, new in edits:
        require(text.count(old) == 1, f'vm mutant {name}: {old!r} occurs {text.count(old)} times')
        text = text.replace(old, new)
    out = BUILD / 'vm' / f'{name}.wasm'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(vm_build.assemble(vm_build.test_source(text)))
    return out


def check_pins() -> dict:
    """vm-core's pins hold, so the lockstep drives the module vm-core froze."""
    pins, module, test = vm_build.build()
    frozen = json.loads((HERE / 'build.json').read_text())
    require(frozen == pins, 'vm/build.json pins differ from a fresh assembly of vm/vm.wat')
    require((HERE / 'vm.wasm').read_bytes() == module, 'vm/vm.wasm differs from a fresh assembly of vm/vm.wat')
    return {'tool': pins['tool'], 'version': pins['version'], 'source_sha256': pins['source']['sha256'],
            'release_sha256': pins['module']['sha256'], 'test_build_sha256': pins['test_build']['sha256']}


# ------------------------------------------------------------------ the lockstep lane

class Base:
    """Traces of the unmutated machines, kept so a mutant reruns only the side it changes."""

    def __init__(self, model: Path, wasm: Path, runs: list):
        self.model, self.wasm, self.runs = model, wasm, runs
        self.model_lines = dict(zip([r.label for r in runs], pool(lambda r: L.run_model(model, r.image, r.argv, window=r.window), runs)))
        self.vm_lines = dict(zip([r.label for r in runs], pool(lambda r: L.run_vm(wasm, r.image, r.argv, window=r.window), runs)))


def observed(lines: list):
    """What a run shows without state: its final control and output, or its refusal."""
    lines = [l for l in lines if not l.startswith('#yields')]
    if not lines:
        return None
    if lines[0].startswith(('R ', '#')):
        return lines[0]
    last = lines[-1].split('|')
    return (last[1].split('@')[0], last[8])


def lockstep_rows(base: Base, model_lines=None, vm_lines=None, ignore=frozenset(), same_refusal=None) -> list:
    """(run, result) for every run: the base traces, or a mutant's on one side."""
    def one(r):
        m = (model_lines or base.model_lines)[r.label]
        v = (vm_lines or base.vm_lines)[r.label]
        return r, L.lockstep(m, v, ignore=ignore, same_refusal=same_refusal)
    return pool(one, base.runs)


def same_refusal(rm: str | None, rv: str | None) -> bool:
    """The refusal of the model and the VM alike. The model spells an image's defect as
    serializer.py does and the VM as a kebab-case code (check-core's table); everything else is
    spelled the same, an Exhausted line included."""
    if rm is None or rv is None:
        return False
    if rm.startswith('HostFailure\timage\t') and rv.startswith('HostFailure\timage\t'):
        want = cc.expected_reason('HostFailure image: ' + rm.split('\t', 2)[2])
        return want == rv.split('\t', 2)[2]
    return rm == rv


def summarize(rows: list) -> dict:
    steps = sum(x['steps'] for _, x in rows)
    strength = {k: sum(x['strength'][k] for _, x in rows) for k in ('layout', 'graph', 'exact')}
    groups = {}
    for r, x in rows:
        g = groups.setdefault(r.group, {'runs': 0, 'transitions': 0, 'refused': 0})
        g['runs'] += 1
        g['transitions'] += x['steps']
        g['refused'] += 1 if x['refused'] else 0
    notes = {}
    for _, x in rows:
        for n in x['notes']:
            notes[n] = notes.get(n, 0) + 1
    return {'runs': len(rows), 'transitions': steps, 'states_compared': sum(x['states'] for _, x in rows),
            'fuel_stops_with_pending_enter_compared': sum(x['fuel_stops'] for _, x in rows),
            'strength': strength, 'groups': groups, 'halting_relations': notes}


def divergences(rows: list) -> list:
    out = [(r.group, r.label, x['divergence'].report()) for r, x in rows if x['divergence']]
    return sorted(out, key=lambda t: (t[2]['step'], t[0], t[1]))


def effect_classes(rows: list) -> dict:
    out = {}
    for r, x in rows:
        if x.get('effects'):
            out[f'{r.group}:{r.label}'] = {'class': x['effect_class'], 'effects': len(x['effects'])}
    return out


# ------------------------------------------------------------------ long runs

def long_runs(model: Path, wasm: Path) -> list:
    """Runs that cross the 65,536-entry quantum: states sampled every 60,000 transitions and
    every state within three of a yield."""
    plans = json.loads((LS / 'fixtures/long.plans.json').read_text())
    out = []
    for name, plan in plans.items():
        data = codec.encode(plan, DIGEST)
        require(cs.rejected(data, REGISTRY, DIGEST) is None, f'{name}: the reference codec refuses it')
        path = BUILD / 'long' / f'{name}.kimg'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        argv = ['main', '4294967295']
        _, extra = L.trailer(L.run_vm(wasm, path, argv, window=(10 ** 9, 1, 0), timeout=900))
        yields = [int(x) for x in extra['yields'].split(',') if x]
        require(yields, f'{name}: the VM never yields')
        window = (60000, min(yields) - 3, max(yields) + 3)
        m = L.run_model(model, path, argv, window=window, timeout=900)
        v = L.run_vm(wasm, path, argv, window=window, timeout=900)
        res = L.lockstep(m, v)
        out.append({'name': name, 'entries': int(res['final'][2] if res['final'] and res['final'][:2] == ('H', 'D') else 0),
                    'yields': yields, 'result': res})
    return out


# ------------------------------------------------------------------ exact strength

def exact_controls(base: Base) -> dict:
    """`exact` is identity of addresses, rc and free lists, which the VM will have once it reclaims
    (vm-rc). Two corruptions only `exact` sees, one of rc and one of a free-list head, are passed by
    `auto` and refused by `exact`, so that turning it on for VM against model is a tested claim; and
    against the VM, `exact` fails where the model first frees a cell."""
    lines = base.model_lines['recursion-map']
    rc_step = next(i for i, l in enumerate(lines) if not L.parse(l, 'model').free and i >= 10)
    free_step = next(i for i, l in enumerate(lines) if L.parse(l, 'model').free)
    controls = []
    m = L.parse(lines[rc_step], 'model')
    boot = L.parse(lines[0], 'model').bump
    # an rc-only change of a mortal cell
    n = (boot - m.h0) // 4
    heap = list(m.heap)
    heap[n] += 1
    rc = '|'.join([*lines[rc_step].split('|', 9)[:9], ''.join(f' {w}' for w in heap)])
    # a free-list-head-only change
    fields = lines[rc_step].split('|', 9)
    fields[7] = ' 16842752' + ' 0' * 28
    free = '|'.join(fields)
    for name, line, step in (('rc-only', rc, rc_step), ('free-list-head-only', free, rc_step)):
        v = L.parse(line, 'model')
        auto, _ = L.compare(m, v, mode='auto', boot=boot)
        exact, _ = L.compare(m, v, mode='exact', boot=boot)
        require(auto is None, f'exact control {name}: auto refuses it: {auto}')
        require(exact is not None and exact.field == 'heap', f'exact control {name}: exact passes it')
        controls.append({'control': name, 'step': step, 'auto': 'passes', 'exact': f'refuses ({exact.field})'})
    own = 0
    for r in [r for r in base.runs if r.group == 'golden'][:20]:
        for line in base.model_lines[r.label]:
            bad, _ = L.compare(L.parse(line, 'model'), L.parse(line, 'model'), mode='exact')
            require(bad is None, f'exact: the model differs from itself in {r.label}: {bad}')
            own += 1
    first = {}
    for r in base.runs:
        if r.group != 'golden':
            continue
        res = L.lockstep(base.model_lines[r.label], base.vm_lines[r.label], mode='exact')
        if res['divergence']:
            first[r.label] = {'step': res['divergence'].step, 'field': res['divergence'].field}
    require(first, 'exact: the VM matches the model bit for bit (it reclaims, so the gate is stale)')
    return {'controls': controls, 'model_against_itself_states': own, 'vm_against_model': {
        'goldens_with_an_exact_divergence': len(first),
        'first_divergence_of_recursion_map': first.get('recursion-map'),
        'note': 'the VM has no reclamation (CORE.md choice 1); vm-rc turns exact on for VM against model'}}


# ------------------------------------------------------------------ comparator controls

def corrupted(line: str, index: int, edit) -> str:
    fields = line.split('|', 9)
    fields[index] = edit(fields[index])
    return '|'.join(fields)


def comparator_controls(base: Base) -> list:
    """One field of one VM state line is corrupted, and the comparison must name it, at the strength the
    state is compared at. The lockstep is only as strong as each of these."""
    def pair(label, step):
        m = L.parse(base.model_lines[label][step], 'model')
        return m, base.vm_lines[label][step]

    def words(field):
        return field.split()

    def bump_word(index, by):
        def edit(field):
            w = words(field)
            w[index] = str(int(w[index]) + by)
            return ' ' + ' '.join(w)
        return edit

    def word_of_act(offset, by):
        def edit(field, act):
            w = words(field)
            at = (act - (int(base_h0[0]))) // 4 + offset
            w[at] = str(int(w[at]) + by)
            return ' ' + ' '.join(w)
        return edit

    rows = []
    label = 'recursion-map'
    spec = [
        # (name, step, field index, edit, expected field)
        ('control-node', 3, 1, lambda f: f'E {int(f.split()[1]) + 1}', 'control'),
        ('control-kind', 4, 1, lambda f: 'E ' + f.split()[1], 'control'),
        ('act', 5, 2, lambda f: str(int(f) + 8), 'act'),
        ('fuel', 5, 3, lambda f: ' '.join([str(int(f.split()[0]) - 1), *f.split()[1:]]), 'fuel'),
        ('calls', 5, 3, lambda f: ' '.join([f.split()[0], str(int(f.split()[1]) + 1), f.split()[2]]), 'calls'),
        ('quantum', 5, 3, lambda f: ' '.join([*f.split()[:2], str(int(f.split()[2]) + 1)]), 'quantum'),
        ('top', 6, 4, lambda f: str(int(f) + 1), 'top'),
        ('frame-aux', 6, 5, lambda f: f.replace(',1,202,0,', ',1,202,1,', 1) if ',1,202,0,' in f else f + ';9,9,9,9', 'frames'),
        ('output', 5, 8, lambda f: '1:65', 'out'),
    ]
    for name, step, index, edit, want in spec:
        m, line = pair(label, step)
        bad, _ = L.compare(m, L.parse(corrupted(line, index, edit), 'vm'))
        require(bad is not None and bad.field == want, f'comparator control {name}: {bad}')
        rows.append({'control': name, 'run': label, 'step': step, 'names': bad.field})
    # heap words at each strength: a mortal cell in a layout state, the Activation in a graph state, and a constant
    # (immortal, so compared word for word) in a graph state
    def heap_control(name, label, pick, want):
        boot = L.parse(base.model_lines[label][0], 'model').bump
        for step, mline in enumerate(base.model_lines[label]):
            m = L.parse(mline, 'model')
            if pick(m):
                break
        else:
            raise AssertionError(f'comparator control {name}: no such state in {label}')
        vm = L.parse(base.vm_lines[label][step], 'vm')
        idx = (vm.act - vm.h0) // 4 + 2 if name == 'heap-graph-act-owner' else (0 if name == 'heap-constant' else (boot - vm.h0) // 4 + 2)
        heap = list(vm.heap)
        heap[idx] += 1
        fields = base.vm_lines[label][step].split('|', 9)
        fields[9] = ''.join(f' {w}' for w in heap)
        bad, strength = L.compare(m, L.parse('|'.join(fields), 'vm'), boot=boot)
        require(bad is not None and bad.field == want, f'comparator control {name}: {bad}')
        rows.append({'control': name, 'run': label, 'step': step, 'names': bad.field, 'strength': strength})

    heap_control('heap-layout-cell', 'recursion-map', lambda m: m.step >= 10 and not m.free, 'heap')
    heap_control('heap-graph-act-owner', 'recursion-map', lambda m: m.free and m.act, 'heap')
    heap_control('heap-constant', 'string-append', lambda m: m.free and m.act, 'heap')
    # a halting outcome
    final = len(base.model_lines['value-on']) - 1
    m, line = pair('value-on', final)
    bad, _ = L.compare(m, L.parse(corrupted(line, 1, lambda f: f.replace('H D 0 1', 'H D 0 0')), 'vm'))
    require(bad is not None and bad.field == 'outcome', f'comparator control outcome: {bad}')
    rows.append({'control': 'outcome-tag', 'run': 'value-on', 'step': final, 'names': bad.field})
    return rows


base_h0 = [0]


# ------------------------------------------------------------------ mutants

# (name, what it breaks, edits of vm.wat, the dimension the lockstep kills it in, state_only)
VM_MUTANTS = [
    ('scope-slots-not-zeroed', 'a Scope pop drops its slots but leaves their words in the Activation',
     [('                (call $drop (i32.load offset=16 (local.get $p)))\n                (i32.store offset=16 (local.get $p) (i32.const 0))\n',
       '                (call $drop (i32.load offset=16 (local.get $p)))\n')], 'heap', True),
    ('call-frame-node', "a Call frame's node word holds 7, which nothing reads",
     [('(i32.store (call $frame (i32.const 4) (i32.const 0) (i32.const 0) (i32.const 1)) (global.get $act))',
       '(i32.store (call $frame (i32.const 4) (i32.const 7) (i32.const 0) (i32.const 1)) (global.get $act))')], 'frames', True),
    ('calls-counted-twice', 'each entry adds two to `calls`',
     [('(global.set $calls (i32.add (global.get $calls) (i32.const 1)))', '(global.set $calls (i32.add (global.get $calls) (i32.const 2)))')],
     'calls', True),
    ('fuel-charged-twice', 'each entry takes two units of fuel',
     [('(global.set $fuel (i32.sub (global.get $fuel) (i32.const 1)))', '(global.set $fuel (i32.sub (global.get $fuel) (i32.const 2)))')],
     'fuel', False),
    ('quantum-counted-twice', 'each entry adds two to the quantum',
     [('(global.set $quantum (i32.add (global.get $quantum) (i32.const 1))))', '(global.set $quantum (i32.add (global.get $quantum) (i32.const 2))))')],
     'quantum', True),
    ('act-not-cleared', 'Return to Top leaves `act` pointing at the released Activation',
     [('            (call $drop (global.get $act))\n            (global.set $act (i32.const 0))\n            (local.set $aux (i32.load (i32.sub (global.get $top) (i32.const 8))))',
       '            (call $drop (global.get $act))\n            (local.set $aux (i32.load (i32.sub (global.get $top) (i32.const 8))))')], 'act', True),
    ('describe-tag-off', "a Book's printed tag is one more than the answer's",
     [('(else (call $emitdec (call $tagof (local.get $x) (global.get $resT)))))', '(else (call $emitdec (i32.add (call $tagof (local.get $x) (global.get $resT)) (i32.const 1)))))')],
     'outcome', False),
    ('arm-mirrored', 'a tag Case takes the mirrored row',
     [('(local.set $arm (call $w (i32.add (i32.add (local.get $n) (i32.const 7)) (local.get $tag))))',
       '(local.set $arm (call $w (i32.add (i32.add (local.get $n) (i32.const 7)) '
       '(i32.sub (i32.sub (local.get $cnt) (i32.const 1)) (local.get $tag)))))')], 'control', False),
    ('reference-slot-below', 'Eval Reference reads the slot below',
     [('(global.set $val (i32.load offset=16 (i32.add (global.get $act) (i32.shl (i32.load offset=4108 (local.get $na)) (i32.const 2)))))',
       '(global.set $val (i32.load offset=12 (i32.add (global.get $act) (i32.shl (i32.load offset=4108 (local.get $na)) (i32.const 2)))))')],
     'control', False),
    ('activation-depth-off', "an entered body's Activation starts one slot deep",
     [('(i32.store offset=12 (local.get $a) (global.get $nops))', '(i32.store offset=12 (local.get $a) (i32.add (global.get $nops) (i32.const 1)))')],
     'heap', False),
    ('gather-count-stale', 'a Gather frame counts its filled operands from one',
     [('(drop (call $frame (i32.const 1) (global.get $node) (i32.const 0) (local.get $n)))', '(drop (call $frame (i32.const 1) (global.get $node) (i32.const 1) (local.get $n)))')],
     'frames', False),
    ('fuel-stop-drops-operands', 'a fuel stop forgets the operands of the Enter it leaves pending',
     [('    (if (i32.eqz (global.get $fuel)) (then (call $exhaust (i32.const 1) (global.get $R_fuel))))',
       '    (if (i32.eqz (global.get $fuel)) (then (global.set $nops (i32.const 0)) (call $exhaust (i32.const 1) (global.get $R_fuel))))')],
     'outcome', True),
    ('closure-entry-free', 'entering a Closure costs nothing',
     [('(br_if $bad (i32.ne (global.get $nops) (local.get $live)))\n        (call $debit)', '(br_if $bad (i32.ne (global.get $nops) (local.get $live)))')],
     'fuel', False),
]

# (name, what it breaks, the section, [(old, new)], dimension, state_only)
MODEL_MUTANTS = [
    ('scope-pop-off-by-one', 'a popped Scope frame takes two words off `top`, not three',
     'machine', [('    case H.Stack{+act,Con{H.Scope{+saved},rest},+top}:\n      +popped : H.Stack = H.Stack{act,rest,U32.sub(top,3)}',
                  '    case H.Stack{+act,Con{H.Scope{+saved},rest},+top}:\n      +popped : H.Stack = H.Stack{act,rest,U32.sub(top,2)}')], 'top', True),
    ('reuse-keeps-padding', 'a cell taken from a free list keeps the stale words of its padding',
     'memory', [('u => Done{Cell{Heap{filled(memory,U32.shrn(head,2n),rc,class,payload,words),bump,',
                 'u => Done{Cell{Heap{filled(memory,U32.shrn(head,2n),rc,class,payload,U32.add(2,W.count(U32,payload))),bump,')],
     'heap', True),
    ('quantum-never-resets', 'the quantum counts past 65,536 without a yield',
     'machine', [('Bool.pick(U32,U32.is_eq(U32.add(quantum,1),65536),0,U32.add(quantum,1))', 'U32.add(quantum,1)')], 'quantum', True),
    ('output-oldest-first', 'a printed line joins the output at the wrong end',
     'machine', [('Done{Machine{Enter{Held{k},[H.immediate(0)]},stack,heap2,meter,Con{H.scalars_of(line,heap),out}}}',
                  'Done{Machine{Enter{Held{k},[H.immediate(0)]},stack,heap2,meter,List.append(&2,List<&2,U32>,out,[H.scalars_of(line,heap)])}}')],
     'out', False),
    ('bind-slot-off-by-one', 'a Let binds its value one slot above its depth',
     'machine', [('to(Eval{H.operand(code,node,2)},stack,H.deepened(H.bound(heap,act,d,w),act,U32.add(d,1))))',
                  'to(Eval{H.operand(code,node,2)},stack,H.deepened(H.bound(heap,act,U32.add(d,1),w),act,U32.add(d,1))))')],
     'heap', False),
    ('call-frame-caller-lost', 'a Call frame keeps no caller',
     'machine', [('then_stack(Next,H.pushed(stack,H.Call{H.act_of(stack)}),stack => to(Eval{0},H.with_act(stack,0),heap)))',
                  'then_stack(Next,H.pushed(stack,H.Call{0}),stack => to(Eval{0},H.with_act(stack,0),heap)))')],
     'frames', False),
]

# state-only mutants that vm-core's structural audit (harness.mjs, after every transition of every golden) must pass
AUDITED = ('scope-slots-not-zeroed', 'call-frame-node', 'act-not-cleared')

# (weakened dimension, the mutant it must let through, machine) -- a knob that hides no mutant is unused
KNOBS = [
    ('calls', 'calls-counted-twice', 'vm'), ('act', 'act-not-cleared', 'vm'), ('quantum', 'quantum-counted-twice', 'vm'),
    ('frames', 'call-frame-node', 'vm'), ('heap', 'scope-slots-not-zeroed', 'vm'), ('outcome', 'describe-tag-off', 'vm'),
    ('top', 'scope-pop-off-by-one', 'model'), ('out', 'output-oldest-first', 'model'),
]


def vm_core_audit(wasm: Path) -> dict:
    """What vm-core's own state check sees of a build: `harness.mjs` audits the frame chain and every word
    frames, the result and cells hold after each transition of every golden. A mutant it passes is one only
    the lockstep catches."""
    jobs = [{'id': n, 'wasm': str(wasm), 'files': {f'{n}.kimg': str(GOLDEN / f'{n}.kimg')},
             'argv': [f'{n}.kimg', *c['argv'][1:]], 'trace': 'audit'} for n, c in VM_EXPECTED['cases'].items()]
    p = subprocess.run(['node', str(HERE / 'harness.mjs')], input=json.dumps(jobs), capture_output=True, text=True, timeout=600 * SCALE)
    require(p.returncode == 0, f'harness failed: {p.stderr[-800:]}')
    got = [json.loads(l) for l in p.stdout.splitlines()]
    return {'goldens': len(got), 'audited_states': sum(g['audited'] for g in got), 'broken': sorted(g['id'] for g in got if g['broken'])}


def kill_record(rows: list) -> dict:
    """A kill is a wrong observation at a named state. A side that produced no trace (a trap, a crash, a
    timeout) is a harness fault, counted apart, and never a kill (SPEC section 11)."""
    bad = divergences(rows)
    faults = [b for b in bad if b[2]['field'] in ('harness', 'length')]
    kills = [b for b in bad if b not in faults]
    fields = sorted({b[2]['field'] for b in kills})
    first = kills[0] if kills else None
    return {'killed_by_runs': len(kills), 'harness_faults': len(faults), 'fields': fields,
            'first': {'run': f'{first[0]}:{first[1]}', **{k: first[2][k] for k in ('step', 'field', 'detail')}} if first else None}


def mutant_lane(base: Base, rows_base: list) -> dict:
    """Every mutant is run through the lockstep; the state-only ones are also compared with the
    unmutated machine on what a run shows (final control and output)."""
    vm_wasm = {name: build_vm(name, edits) for name, _, edits, _, _ in VM_MUTANTS}
    model_bin = {}

    def build_one(m):
        name, _, section, edits, _, _ = m
        return name, build_model(name, section, edits)
    for name, out in pool(build_one, MODEL_MUTANTS, workers=3):
        model_bin[name] = out
    result, traces = {}, {}
    for name, breaks, edits, dimension, state_only in VM_MUTANTS:
        lines = dict(zip([r.label for r in base.runs],
                         pool(lambda r: L.run_vm(vm_wasm[name], r.image, r.argv, window=r.window), base.runs)))
        rows = lockstep_rows(base, vm_lines=lines, same_refusal=same_refusal)
        record = kill_record(rows)
        differs = [r.label for r in base.runs if observed(lines[r.label]) != observed(base.vm_lines[r.label])]
        record.update({'machine': 'vm', 'breaks': breaks, 'dimension': dimension, 'state_only': state_only,
                       'output_visible_runs': len(differs)})
        require(record['killed_by_runs'] > 0, f'mutant {name} survives the lockstep')
        require(dimension in record['fields'], f'mutant {name} is killed in {record["fields"]}, not {dimension}')
        require(bool(differs) != state_only, f'mutant {name}: state_only={state_only} but {len(differs)} runs change what they show')
        if name in AUDITED:
            record['vm_core_audit'] = vm_core_audit(vm_wasm[name])
            require(not record['vm_core_audit']['broken'], f'mutant {name} is caught by vm-core\'s audit: {record["vm_core_audit"]}')
        result[name], traces[name] = record, ('vm', lines)
    for name, breaks, section, edits, dimension, state_only in MODEL_MUTANTS:
        lines = dict(zip([r.label for r in base.runs],
                         pool(lambda r: L.run_model(model_bin[name], r.image, r.argv, window=r.window), base.runs)))
        rows = lockstep_rows(base, model_lines=lines, same_refusal=same_refusal)
        record = kill_record(rows)
        differs = [r.label for r in base.runs if observed(lines[r.label]) != observed(base.model_lines[r.label])]
        record.update({'machine': 'model', 'breaks': breaks, 'dimension': dimension, 'state_only': state_only,
                       'output_visible_runs': len(differs)})
        if dimension == 'quantum':
            record.update(long_kill(model_bin[name], base))
        else:
            require(record['killed_by_runs'] > 0, f'mutant {name} survives the lockstep')
            require(dimension in record['fields'], f'mutant {name} is killed in {record["fields"]}, not {dimension}')
        require(bool(differs) != state_only, f'mutant {name}: state_only={state_only} but {len(differs)} runs change what they show')
        result[name], traces[name] = record, ('model', lines)
    knobs = []
    for dimension, name, machine in KNOBS:
        side, lines = traces[name]
        kwargs = {'vm_lines': lines} if side == 'vm' else {'model_lines': lines}
        rows = lockstep_rows(base, ignore=frozenset({dimension}), same_refusal=same_refusal, **kwargs)
        left = divergences(rows)
        require(not left, f'the lockstep without {dimension} still kills {name}: {left[:1]}')
        knobs.append({'weakened': dimension, 'lets_through': name, 'machine': side})
    return {'mutants': result, 'weakenings': knobs}


def long_kill(model: Path, base: Base) -> dict:
    """The quantum mutant survives every short run; a run past the 65,536th entry kills it."""
    path = BUILD / 'long' / 'loop-tail.kimg'
    _, extra = L.trailer(L.run_vm(base.wasm, path, ['main', '4294967295'], window=(10 ** 9, 1, 0), timeout=900))
    yields = [int(x) for x in extra['yields'].split(',') if x]
    window = (60000, min(yields) - 3, max(yields) + 3)
    m = L.run_model(model, path, ['main', '4294967295'], window=window, timeout=900)
    v = L.run_vm(base.wasm, path, ['main', '4294967295'], window=window, timeout=900)
    res = L.lockstep(m, v)
    require(res['divergence'] and res['divergence'].field == 'quantum', f'the long run does not kill the quantum mutant: {res["divergence"]}')
    return {'killed_by_long_run': {'run': 'loop-tail', **{k: res['divergence'].report()[k] for k in ('step', 'field')}}}


# ------------------------------------------------------------------ the value lane

KINDS = {1: 'steps', 2: 'memory', 3: 'frames'}


def host_run(argv: list) -> dict:
    p = subprocess.run(['node', str(HOST), str(HERE / 'vm.wasm'), str(GOLDEN), '--', *argv], capture_output=True, timeout=300 * SCALE,
                       env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
    return {'exit': p.returncode, 'stdout': p.stdout.decode('utf-8', 'replace'), 'stderr': p.stderr.decode('utf-8', 'replace')}


def eval_oracles() -> dict:
    """The pinned Knot evaluators (eval-cli of the literals and closures snapshots), built natively."""
    manifest = json.loads((HERE / 'oracles/manifest.json').read_text())
    root = BUILD / 'oracles'
    built = {}
    for lane, entry in manifest.items():
        import gzip
        raw = (ROOT / entry['archive']).read_bytes()
        require(sha(raw) == entry['sha256'], f'{lane} archive digest')
        files = json.loads(gzip.decompress(raw))
        require({p: sha(t.encode()) for p, t in files.items()} == entry['files'], f'{lane} snapshot files')
        for path, text in files.items():
            target = root / lane / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        built[lane] = {'tree': root / lane, 'commit': entry['commit']}

    def build(lane):
        out = root / f'{lane}-eval'
        got = run([SEED, built[lane]['tree'] / 'src/eval-cli.bend', '-o', out], 900)
        require(got['exit'] == 0 and out.exists(), (lane, got['stderr'][-1500:]))
        return lane, out
    for lane, out in pool(build, list(built), workers=2):
        built[lane]['eval'] = out
    return built


def eval_live(argv: list) -> dict:
    return run(argv, 300)


def value_lane() -> dict:
    """The release VM through the real host against the frozen expectation (SPEC section 11) and, live,
    against the pinned eval-cli. Every golden and every Book invocation lands in exactly one bucket."""
    built = eval_oracles()
    frozen = json.loads((GOLDEN / 'expectations.json').read_text())['cases']
    by_name = {c['name']: c for c in frozen}
    rows = []

    def eval_argv(case, invocation=None):
        prefix = ['--bundle', '.'] if case['lane'] == 'literals' else []
        if invocation is None:
            return [built[case['lane']]['eval'], *prefix, case['source'], 'main', cs.EVAL_BUDGET]
        name, *ordinals = invocation['argv']
        return [built[case['lane']]['eval'], *prefix, case['source'], name, invocation.get('fuel', cs.EVAL_BUDGET), *ordinals]

    jobs = []
    for name, case in VM_EXPECTED['cases'].items():
        jobs.append((name, case, by_name[name], None, [f'{name}.kimg', *case['argv'][1:]]))
    for name, listed in VM_EXPECTED['invocations'].items():
        for row, invocation in zip(listed, by_name[name]['invocations']):
            words = [invocation['argv'][0], str(invocation.get('fuel', cs.VM_FUEL)), *invocation['argv'][1:]]
            require(row['argv'][1:] == words, f'{name}: vm-expected row {row["argv"]} against invocation {invocation["argv"]}')
            jobs.append((f"{name}:{' '.join(words)}", row, by_name[name], invocation, [f'{name}.kimg', *words]))

    def one(job):
        label, row, case, invocation, argv = job
        vm = host_run(argv)
        ev = eval_live(eval_argv(case, invocation))
        return label, row, vm, ev

    for label, row, vm, ev in pool(one, jobs):
        want = cc.expected_run(row)
        require({k: vm[k] for k in ('exit', 'stdout', 'stderr')} == want, f'{label}: the VM shows {vm}, vm-expected {want}')
        basis, lane = row.get('basis'), row.get('eval_lane')
        frozen_eval = by_name[label]['eval'] if invocation_label(label) is None else None
        if frozen_eval is not None:
            require({k: ev[k] for k in ('exit', 'stdout', 'stderr')} == frozen_eval, f'{label}: eval-cli {ev} against its frozen observation')
        if basis == 'eval-cli':
            # eval-cli is the value: the VM's exit, stdout and stderr equal it, a refusal included
            require({k: vm[k] for k in ('exit', 'stdout', 'stderr')} == {k: ev[k] for k in ('exit', 'stdout', 'stderr')},
                    f'{label}: eval-cli {ev}, VM {vm}')
            bucket = 'agree: the VM equals eval-cli' if lane == 'agree' else 'agree-refusal: the VM refuses as eval-cli does'
        elif basis == 'seed' and lane == 'Exhausted':
            require(ev['stderr'].startswith('Exhausted\t') and row.get('eval_bound'), f'{label}: eval-cli {ev}')
            bucket = 'excused: eval-cli exhausted a documented bound; the VM returns the seed value'
        elif basis == 'bound':
            require(ev['stderr'].startswith('Exhausted\t'), f'{label}: eval-cli {ev}')
            bucket = 'vm-bound: the seed succeeds beyond a bound of the VM, which stops Exhausted (bounds.json)'
        elif basis == 'seed':
            bucket = f'eval-unavailable: eval-cli reports {lane}; the VM shows the seed value'
        else:
            bucket = f'declared: {basis}'
        rows.append({'fixture': label, 'lane': lane, 'basis': basis, 'bucket': bucket})
    counts = {}
    for r in rows:
        counts[r['bucket'].split(':')[0]] = counts.get(r['bucket'].split(':')[0], 0) + 1
    return {'eval_commits': {lane: built[lane]['commit'] for lane in built}, 'fixtures': len(rows), 'buckets': counts,
            'rows': rows}


def invocation_label(label: str):
    return label.split(':', 1)[1] if ':' in label else None


def frozen_suites() -> list:
    """The frozen eval suites of the repository and their images: none exists until src/image.bend (increment
    `image`) encodes a checked Book. A fixture without an image is not compared, and never counts as agreement."""
    inventory = json.loads((ROOT / 'docs/compiler-campaign/inventory/accepted.json').read_text())
    return [{'suite': s['suite'], 'directory': s['directory'], 'admission': s['admission'], 'fixtures': s['fixtures'],
             'image': 'none: needs src/image.bend (the `image` increment)'}
            for s in inventory['suites'] if s.get('fixtures')]


# ------------------------------------------------------------------ main

def main(argv=()) -> int:
    started = time.time()
    skip = {a.removeprefix('--skip=') for a in argv if a.startswith('--skip=')}  # development only: a skipped gate writes no receipt
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    record = {'gate': 'vm-lockstep', 'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'failed'}
    record['pins'] = check_pins()
    record['inputs'] = {p: sha((HERE / p).read_bytes()) for p in ('vm.wat', 'vm.wasm', 'model-trace.bend', *MODEL_SOURCES)}
    record['inputs'].update({p: sha((LS / p).read_bytes()) for p in ('lockstep.py', 'runs.py', 'check.py', 'js/vm-trace.mjs',
                                                                    'frozen.json', 'fixtures/long.plans.json')})
    test_wasm = BUILD / 'vm-test.wasm'
    test_wasm.write_bytes(vm_build.assemble(vm_build.test_source((HERE / 'vm.wat').read_text())))
    require(sha(test_wasm.read_bytes()) == record['pins']['test_build_sha256'], 'the lockstep drives the pinned test build')
    model = build_model('base')

    traced, outcomes, skipped = R.collect(BUILD / 'stage')
    record['untraced'] = skipped
    base = Base(model, test_wasm, traced)
    rows = lockstep_rows(base, same_refusal=same_refusal)
    bad = divergences(rows)
    require(not bad, f'{len(bad)} runs diverge; first: {bad[:3]}')
    summary = summarize(rows)
    frozen = EXPECTED['halting_relations']
    require(summary['halting_relations'] == frozen, f'halting relations {summary["halting_relations"]} against the frozen {frozen}')
    require(summary['fuel_stops_with_pending_enter_compared'] == EXPECTED['fuel_stops_with_pending_enter_compared'],
            f"fuel stops compared: {summary['fuel_stops_with_pending_enter_compared']}, frozen {EXPECTED['fuel_stops_with_pending_enter_compared']}")
    record['lockstep'] = summary

    # outcomes of the runs that stop before their first entry
    def outcome(r):
        m = L.run_model(model, r.image, r.argv)
        v = L.run_vm(test_wasm, r.image, r.argv)
        return r, L.lockstep(m, v, same_refusal=same_refusal)
    refused = pool(outcome, outcomes)
    left = [(r.group, r.label, x['divergence'].report()) for r, x in refused if x['divergence']]
    require(not left, f'refusals differ: {left[:3]}')
    require(all(x['refused'] for _, x in refused), 'a refusal control was admitted by both machines')
    record['refusals'] = {'runs': len(refused), 'by_group': {g: sum(1 for r, _ in refused if r.group == g) for g in sorted({r.group for r, _ in refused})}}

    # effects: eager against D23
    classes = effect_classes(rows)
    for label, want in EXPECTED['d23']['programs'].items():
        got = classes.get(label)
        require(got == want, f'D23 class of {label}: {got}, frozen {want}')
    for label in classes:
        if label not in EXPECTED['d23']['programs']:
            require(label.startswith(('fuel:', 'admitted:', 'argument:')), f'{label} has effects and no frozen class')
    record['d23'] = {'frozen_by_literal_review': EXPECTED['d23']['programs'], 'observed_elsewhere': {
        k: v for k, v in classes.items() if k not in EXPECTED['d23']['programs']},
        'pending': sorted(k for k, v in classes.items() if v['class'] == 'pending-D23')}

    record['long'] = []
    for item in long_runs(model, test_wasm):
        res = item['result']
        require(res['divergence'] is None, f'{item["name"]}: {res["divergence"]}')
        record['long'].append({'name': item['name'], 'transitions': res['steps'], 'states_compared': res['states'],
                               'quantum_yields_at_step': item['yields'], 'strength': res['strength']})
    record['comparator_controls'] = comparator_controls(base)
    record['exact'] = exact_controls(base)
    if 'mutants' not in skip:
        record.update(mutant_lane(base, rows))
    if 'value' not in skip:
        record['value'] = value_lane()
    record['suites'] = frozen_suites()
    record['pending'] = EXPECTED['pending']
    record['elapsed_seconds'] = round(time.time() - started, 1)
    if skip:
        print('skipped', sorted(skip), '- no receipt written')
        return 0
    record['status'] = 'passed'
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(record, indent=1, sort_keys=False) + '\n')
    print(f"vm-lockstep passed: {summary['runs']} runs, {summary['transitions']} transitions, {summary['states_compared']} states compared "
          f"({summary['strength']['layout']} layout, {summary['strength']['graph']} graph), {record['refusals']['runs']} refusals, "
          f"{len(record['long'])} long runs, {len(record['mutants'])} mutants, {len(record['weakenings'])} weakenings, "
          f"{record['value']['fixtures']} value fixtures; {RECEIPT.relative_to(ROOT)}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
