#!/usr/bin/env python3
"""Gate vm-model: the Bend model of knot-vm-1 against the frozen goldens.

Builds the model's three entries (run, RC audit, soundness sweep) from vm/model/ with the
seed's native lane and requires:
- every golden image to be its frozen plan's encoding, and each LAWS.bend
  fixture to equal its image's words;
- the model's prim and foreign tables to equal registry.json;
- no Base Bool.or or Bool.xor in the natively built model, whose connectives are
  choices (W.or, W.xor), and vm/model-lanes.bend to print W's columns as the
  comparisons' values on both of the seed's lanes while the native lane still
  misreads Base's (MODEL.md);
- every golden run and frozen Book invocation to agree with
  vm/golden/vm-expected.json (SPEC sections 8 and 11);
- literal fuel controls (SPEC section 7): fuel 0 exhausts every golden at its
  first entry, and value-on, which makes one entry, completes on fuel 1;
- check-spec's frozen refusal controls, and a child at its parent's offset,
  refused with check-spec's exact reason;
- check-spec's argument controls (SPEC section 8): the image before the words,
  then its entry kind's form, `usage` before any word, each word a decimal u32;
  an admitted one runs as the reference evaluation runs it;
- the inspection controls (SPEC sections 3 and 6): a word laundered through a
  `none`-typed identity is refused ill-typed where it is read (a Case scrutinee,
  a prim operand, Chr's operand, a rendered word before its visit is charged),
  as the reference evaluation refuses it;
- every admitted control run to its outcome, its written output and its call
  count (SPEC sections 4 and 7): check-spec's admitted plan controls and
  code-list controls, as the reference evaluation (vm/evaluate.py) runs them,
  its run controls at the fuel frozen with each and to the run frozen with it
  (a display line by its SHA-256), and the model's own controls in
  vm/model-controls/, whose frozen values the seed and the reference evaluation
  reproduce, and its display controls and `inspect-append-b-whole` (a closure
  in the tail of the `b` that append moves, read whole by SPEC section 9),
  frozen by literal review; each count is check-spec's own or frozen with the
  control, never a literal here;
- the harness mutant `fuel-ignored`, which runs every run control at 1,000,000,
  killed by exactly the fuel controls whose frozen run differs there;
- the RC audit before every transition of every golden and admitted control, no
  live mortal cell after each completed run, and the reference evaluation's call
  count at the end of each run;
- the bounded soundness sweep: every single-word mutation of the swept goldens
  is refused exactly when the reference codec refuses it, for the same reason,
  and every admitted mutation runs soundly;
- vm/PROOF.bend to print 'All terms check.';
- every model mutant killed by a wrong observation of those checks, never by a
  crash or a timeout, and those in LAW_MUTANTS also refuted by a law of PROOF.bend.
It writes only vm/receipts/model.json.
"""
from __future__ import annotations

import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'vm'
GOLDEN = HERE / 'golden'
BUILD = ROOT / '.local/vm-model/gate'
SEED = ROOT / 'scripts/bend-reference'
RECEIPT = HERE / 'receipts/model.json'
SCALE = float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))  # hang guard only
SECTIONS = ('word', 'decode', 'validate', 'encode', 'memory', 'machine', 'audit')  # vm/model/, in import order
SOURCES = tuple(f'model/{s}.bend' for s in SECTIONS) + (
    'model-cli.bend', 'model-audit.bend', 'model-sweep.bend', 'model-lanes.bend', 'LAWS.bend', 'PROOF.bend')
ENTRIES = {'model': 'model-cli.bend', 'audit': 'model-audit.bend', 'sweep': 'model-sweep.bend', 'lanes': 'model-lanes.bend'}
BUILT = tuple(f'model/{s}.bend' for s in SECTIONS) + ('model-cli.bend', 'model-audit.bend', 'model-sweep.bend')  # the natively built model
SWEEP_FUEL = '256'  # every golden completes within 256 entries; mutants that loop stop early


def load_check_spec():
    spec = importlib.util.spec_from_file_location('check_spec', HERE / 'check-spec.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cs = load_check_spec()
codec = cs.codec
reference = cs.reference  # vm/evaluate.py
REGISTRY = codec.registry()
DIGEST = codec.base_digest(REGISTRY)


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
    return {'exit': p.returncode, 'stdout': p.stdout.decode('utf-8', 'replace'),
            'stderr': p.stderr.decode('utf-8', 'replace')}


def words(data: bytes) -> list:
    return [int.from_bytes(data[i:i + 4], 'little') for i in range(0, len(data), 4)]


# ------------------------------------------------------------------ inputs

def check_inputs(expected: dict) -> dict:
    """Goldens are the encodings of vm-spec's frozen plans (vm/receipts/spec.json
    is vm-spec's own output, absent while that gate runs); LAWS.bend's fixtures
    are their words."""
    names = sorted(p.stem for p in GOLDEN.glob('*.kimg'))
    require(names == sorted(expected['cases']), 'golden images differ from vm-expected.json')
    for name in names:
        plan = json.loads((GOLDEN / f'{name}.plan.json').read_text())
        require((GOLDEN / f'{name}.kimg').read_bytes() == codec.encode(plan, DIGEST), f'{name}.kimg is not its plan')
    laws = (HERE / 'LAWS.bend').read_text()
    fixtures = {}
    for name, body in re.findall(r'^def (\w+)\(\) -> List<&2,U32>:\n  \[([0-9,\s]+)\]', laws, re.M):
        image = GOLDEN / f"{name.replace('_', '-')}.kimg"
        if image.exists():
            listed = [int(x) for x in re.split(r'[,\s]+', body.strip()) if x]
            require(listed == words(image.read_bytes()), f'LAWS.bend fixture {name} differs from its image')
            fixtures[name] = len(listed)
    require(len(fixtures) >= 5, f'LAWS.bend fixtures {sorted(fixtures)}')
    return fixtures


def check_registry() -> dict:
    """The model's prim and foreign rows equal registry.json's, by representation position."""
    source = (HERE / 'model/validate.bend').read_text()
    reps = REGISTRY['representations']

    def table(name):
        body = source.split(f'def {name}() -> List<&2,Primitive>:')[1].split('\ndef ')[0]
        return [([int(x) for x in a.split(',') if x], int(b))
                for a, b in re.findall(r'Primitive\{\[([0-9,]*)\],(\d+)\}', body)]

    def rows(entries):
        return [([reps.index(i) for i in r['inputs']], reps.index(r['output'])) for r in entries
                if r.get('status') != 'reserved']
    require(table('prims') == rows(REGISTRY['prims']), 'model prim table differs from registry.json')
    require(table('foreigns') == rows(REGISTRY['foreign']), 'model foreign table differs from registry.json')
    return {'prims': len(table('prims')), 'foreign': len(table('foreigns'))}


# ------------------------------------------------------------------ the seed's lanes

# The seed's native lane can read a U32 comparison against a nullary or constant-argument
# call as True when it is an operand of Base's Bool.or or Bool.xor (MODEL.md). The model
# spells both as choices, W.or and W.xor, which vm/model-lanes.bend witnesses on the two
# lanes; Base's pair is refused anywhere in the natively built model.
BASE_CONNECTIVE = re.compile(r'(?<![\w.])Bool\.(or|xor)\(')


def base_connectives(texts: dict) -> list:
    """Each line of the natively built model that applies Base's Bool.or or Bool.xor."""
    return [f'{name}:{i}' for name, text in texts.items() for i, line in enumerate(text.split('\n'), 1)
            if BASE_CONNECTIVE.search(line.split('#', 1)[0])]


def connective_runs(tree: Path) -> dict:
    """The natively built model (a mutant's included) applies neither of Base's connectives."""
    found = base_connectives({name: (tree / 'vm' / name).read_text() for name in BUILT})
    return {'base': {'result': {'exit': 0, 'stdout': '\n'.join(found), 'stderr': ''}, 'agrees': not found}}


def check_connectives() -> dict:
    """Control: a W.or put back as Base's Bool.or is refused."""
    memory = (HERE / 'model/memory.bend').read_text()
    require(base_connectives({'model/memory.bend': memory.replace('W.or(', 'Bool.or(', 1)}),
            "control: the connective check refuses Base's Bool.or")
    texts = [(HERE / name).read_text() for name in BUILT]
    return {'sources': len(texts), 'choices': sum(len(re.findall(r'(?<![\w.])(?:W\.)?x?or\(', t)) for t in texts)}


LANE_LITERALS = ('3', '2000000', '4294967295')  # vm/model-lanes.bend's literal rows
LANE_WORDS = ('3', '2000000', '4294967295', '1048576', '1048577', '0')  # its rows read at run time


def lane_row(x: int) -> str:
    """vm/model-lanes.bend's seven columns for the word x, as its comparisons' values."""
    over, none = x > 1_048_576, x == 0xFFFF_FFFF
    return f"{x}\t{''.join(str(int(b)) for b in (over, over, not over, not over, none, False, none or x == 3))}"


LANE_ROWS = [lane_row(int(x)) for x in (*LANE_LITERALS, *LANE_WORDS)]


def lane_columns(result: dict, base: bool) -> list:
    """Each printed row's word with W's columns (base False) or Base's (base True)."""
    rows = [line.split('\t') for line in result['stdout'].strip().split('\n')]
    return ['\t'.join((r[0], r[2 if base else 1])) for r in rows if len(r) == 3]


def lane_runs(lanes: Path) -> dict:
    """The native lane prints W.or's and W.xor's columns as the comparisons' values."""
    result = run([lanes, '--', *LANE_WORDS], 60)
    return {'native': {'result': result, 'agrees': result['exit'] == 0 and lane_columns(result, False) == LANE_ROWS}}


def check_lanes(tree: Path, lanes: Path) -> dict:
    """Both lanes print W's columns as the comparisons' values, and the Bun lane Base's too;
    the native lane misreads some of Base's, so the probe still reaches the defect."""
    bun = run([SEED, tree / 'vm' / 'model-lanes.bend', '--', *LANE_WORDS], 300)
    native = run([lanes, '--', *LANE_WORDS], 60)
    require(bun['exit'] == 0 and lane_columns(bun, False) == LANE_ROWS == lane_columns(bun, True),
            f'model-lanes on the Bun lane: {bun}')
    require(native['exit'] == 0 and lane_columns(native, False) == LANE_ROWS, f'model-lanes natively: {native}')
    misread = [f'{i}:{j}' for i, (got, want) in enumerate(zip(lane_columns(native, True), LANE_ROWS))
               for j, (x, y) in enumerate(zip(got.split('\t')[1], want.split('\t')[1])) if x != y]
    require(misread, "model-lanes: the native lane reads Base's Bool.or and Bool.xor correctly; the probe no longer reaches the defect")
    return {'rows': len(LANE_ROWS), 'base_misread': misread}  # row:column


# ------------------------------------------------------------------ builds

def build_tree(name: str, section=None, mutation=()) -> Path:
    tree = BUILD / name
    (tree / 'vm' / 'model').mkdir(parents=True, exist_ok=True)
    for source in SOURCES:
        text = (HERE / source).read_text()
        if source in (f'model/{section}.bend', f'{section}.bend'):
            for old, new in mutation:
                require(text.count(old) == 1, f'mutant {name}: {old!r} occurs {text.count(old)} times')
                text = text.replace(old, new)
        (tree / 'vm' / source).write_text(text)
    return tree


def build(tree: Path, entry: str) -> Path:
    out = tree / entry
    got = run([SEED, tree / 'vm' / ENTRIES[entry], '-o', out], 900)
    require(got['exit'] == 0 and out.exists(), (str(tree), entry, got['stderr'][-2000:]))
    return out


def built(tree: Path, entries) -> dict:
    with ThreadPoolExecutor(max_workers=len(entries)) as pool:
        return dict(zip(entries, pool.map(lambda e: build(tree, e), entries)))


# ------------------------------------------------------------------ observations

KNOWN_EXITS = {0, 3, 4, 5, 6, 7}


def well_formed(result) -> bool:
    """A model answer, not a crash, trap or timeout: those never count as a kill."""
    return result['exit'] in KNOWN_EXITS and 'bend:' not in result['stderr']


def argv_of(model: Path, name: str, argv: list) -> list:
    # The runtime strips its options up to the first `--`; the image's own
    # `--` for Programs follows it literally.
    return [model, '--', GOLDEN / f'{name}.kimg', *argv[1:]]


def written(case: dict, got: dict) -> bool:
    """The output a run wrote before it halted: frozen as text, or a display line by its SHA-256."""
    if 'stdout_sha256' in case:
        return sha(got['stdout'].encode()) == case['stdout_sha256']
    return got['stdout'] == case.get('stdout', '')


def agrees(case: dict, got: dict) -> bool:
    if 'outcome' not in case:
        return (got['exit'], got['stderr']) == (case['exit'], case.get('stderr', '')) and written(case, got)
    fields = got['stderr'].rstrip('\n').split('\t')
    if case['outcome'] == 'Exhausted':
        # A Program that runs out of fuel keeps what it wrote (SPEC section 7).
        return got['exit'] == 4 and written(case, got) and fields == ['Exhausted', 'vm', str(case['kind']), case['cause']]
    if case['outcome'] == 'Unsupported':
        return got['exit'] == 3 and got['stdout'] == '' and fields == ['Unsupported', *case['cause'].split(' ')]
    if case['outcome'] == 'HostFailure':
        return got['exit'] == 5 and written(case, got) and fields == ['HostFailure', *case['cause'].split(' ')]
    return False


def golden_runs(model: Path, expected: dict) -> dict:
    cases = expected['cases']
    with ThreadPoolExecutor(max_workers=8) as pool:
        got = dict(zip(cases, pool.map(lambda n: run(argv_of(model, n, cases[n]['argv']), 120), cases)))
    return {n: {'result': got[n], 'agrees': agrees(cases[n], got[n])} for n in cases}


def invocation_runs(model: Path, audit: Path, expected: dict) -> dict:
    """SPEC section 8's frozen Book invocations: each refusal or describe line, and for an
    entered one the RC audit and the reference evaluation's call count."""
    plans = golden_plans()
    rows = {f"{n}:{' '.join(r['argv'][1:])}": (n, r) for n, listed in expected['invocations'].items() for r in listed}

    def one(label):
        n, row = rows[label]
        result = run(argv_of(model, n, row['argv']), 120)
        good = agrees(row, result)
        if good and row.get('exit') == 0:
            audited = run(argv_of(audit, n, row['argv']), 300)
            m = AUDIT.match(audited['stdout'].strip())
            calls = reference_calls(plans[n], row['argv'])
            good = bool(m) and audited['exit'] == 0 and m.group(1) == 'passed' and m.group(4) == '0' and int(m.group(5)) == calls
            result = result if good else audited
        return label, {'result': result, 'agrees': good}
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(pool.map(one, rows))


def fuel_argv(case: dict, fuel: str) -> list:
    argv = list(case['argv'])
    argv[argv.index('1000000')] = fuel
    return argv


def fuel_runs(model: Path, expected: dict) -> dict:
    """SPEC section 7: every run starts with an entry, which fuel 0 cannot pay;
    value-on's `main` returns a nullary value after exactly one entry."""
    cases = {n: c for n, c in expected['cases'].items() if c.get('outcome') != 'Unsupported'}
    want = {n: ('Exhausted', 'vm', '1', 'fuel') for n in cases}
    jobs = [(n, fuel_argv(c, '0')) for n, c in cases.items()] + [('value-on@1', fuel_argv(cases['value-on'], '1'))]
    with ThreadPoolExecutor(max_workers=8) as pool:
        got = dict(zip([j[0] for j in jobs],
                       pool.map(lambda j: run(argv_of(model, j[0].split('@')[0], j[1]), 120), jobs)))
    out = {}
    for n, result in got.items():
        if n == 'value-on@1':
            good = (result['exit'], result['stdout']) == (0, 'Evaluated\t0\t1\tOn{}\n')
        else:
            good = result['exit'] == 4 and tuple(result['stderr'].rstrip('\n').split('\t')) == want[n]
        out[n] = {'result': result, 'agrees': good}
    return out


def golden_plans() -> dict:
    return {p.stem.removesuffix('.plan'): json.loads(p.read_text()) for p in sorted(GOLDEN.glob('*.plan.json'))}


def controls() -> list:
    """SPEC section 4's refusal controls; the plan controls it must admit run with the
    admitted ones (`admitted_controls`)."""
    names = sorted(p.stem for p in GOLDEN.glob('*.kimg'))
    images = {n: (GOLDEN / f'{n}.kimg').read_bytes() for n in names}
    plans = golden_plans()
    refusals = [(f'plan:{k}', codec.encode(p, DIGEST), 'HostFailure image: validator: ', m)
                for k, p, m in cs.plan_controls(plans) if m is not None]
    listed = cs.byte_controls(images, DIGEST) + refusals
    require(refusals and len(listed) > len(refusals), 'check-spec lists byte and plan refusal controls')
    # One boundary the frozen controls leave open: a child at its own parent's
    # offset does not precede it. The reference supplies the expected reason.
    capture = images['closure-captures']
    body = cs.word(capture, cs.word(capture, 7) + 1 + 5)
    listed.append(('model:child-is-parent', cs.word_patch(capture, body + 4, body), '', ''))
    return [(label, data, cs.rejected(data, REGISTRY, DIGEST)) for label, data, _, _ in listed]


def argument_runs(model: Path, audit: Path) -> dict:
    """SPEC section 8's argument controls, check-spec's by literal review: the image first,
    then its entry kind's form and words. A refused one halts with check-spec's verdict; an
    admitted one runs as the reference evaluation runs its fuel and ordinals, and its RC
    audit passes."""
    folder = BUILD / 'arguments'
    folder.mkdir(parents=True, exist_ok=True)
    images = {p.stem: p.read_bytes() for p in GOLDEN.glob('*.kimg')}
    listed = cs.argument_controls(images)
    require(any(v is None for *_, v in listed) and any(v for *_, v in listed), 'check-spec lists admitted and refused argument controls')

    def one(item):
        label, data, words, verdict = item
        require(cs.argument_verdict(data, words, REGISTRY, DIGEST) == verdict, f'argument control {label}: check-spec gives another verdict')
        path = folder / f'{label}.kimg'
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
        result = run([model, '--', path, *words], 120)
        if verdict is not None and verdict.startswith('HostFailure image: '):
            return label, {'result': result, 'agrees': model_refusal(result) == verdict}
        if verdict is not None:
            return label, {'result': result, 'agrees': agrees({'outcome': 'HostFailure', 'cause': verdict.split(' ', 1)[1]}, result)}
        plan = codec.decode(data, DIGEST)
        if plan['entry'] == 'book':
            got = reference.book(plan, words[0], [codec.decimal(w) for w in words[2:]], codec.decimal(words[1]))
        else:
            got = reference_run(plan, codec.decimal(words[0]))
        audited = run([audit, '--', path, *words], 300)
        m = AUDIT.match(audited['stdout'].strip())
        good = agrees(expected_run(got), result)
        balanced = bool(m) and audited['exit'] == 0 and m.group(1) == 'passed' and m.group(4) == '0' and int(m.group(5)) == got['calls']
        return label, {'result': audited if good else result, 'agrees': good and balanced}
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(pool.map(one, listed))


def model_refusal(result) -> str | None:
    """The model's refusal in check-spec's spelling; oversize is Exhausted image-size."""
    fields = result['stderr'].rstrip('\n').split('\t')
    if result['exit'] == 5 and fields[:2] == ['HostFailure', 'image']:
        return 'HostFailure image: ' + '\t'.join(fields[2:])
    if result['exit'] == 4 and fields == ['Exhausted', 'vm', '2', 'image-size']:
        return 'HostFailure image: exhausted image-size'
    return None


def control_runs(model: Path, listed: list) -> dict:
    folder = BUILD / 'controls'
    folder.mkdir(parents=True, exist_ok=True)

    def one(item):
        label, data, want = item
        path = folder / (label.replace(':', '_') + '.kimg')
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
        result = run([model, '--', path, 'main', '1000000'], 120)
        return label, {'result': result, 'reference': want, 'agrees': model_refusal(result) == want}
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(pool.map(one, listed))


def expected_run(got: dict) -> dict:
    """A reference run in vm-expected.json's shape: an exit and its stdout, or an outcome
    with what a Program wrote before it."""
    if 'exit' in got:
        return {'exit': got['exit'], 'stdout': got['stdout'], 'stderr': ''}
    return {k: got[k] for k in ('outcome', 'kind', 'cause', 'stdout') if k in got}


def reference_run(plan: dict, fuel: int) -> dict:
    got = reference.book(plan, 'main', [], fuel) if plan['entry'] == 'book' else reference.program(plan, fuel)
    return {**got, 'stdout': got['stdout'].decode('utf-8')} if isinstance(got.get('stdout'), bytes) else got


def admitted_controls() -> list:
    """(label, plan, fuel, run, calls) for images the validator MUST admit and the VM MUST run
    at `fuel` to `run` after `calls` entries (SPEC sections 4 and 7): check-spec's admitted
    plan controls and code-list controls, its frozen run controls and the model's own frozen
    controls, seed-derived and display. A run control runs at the fuel frozen with it, every
    other control at SPEC section 7's 1,000,000; the reference evaluation runs each at that
    fuel and reproduces what the control froze."""
    plans = golden_plans()
    listed = [(f'plan:{k}', p, {}) for k, p, m in cs.plan_controls(plans) if m is None]
    listed += [(k, p, {}) for k, p in cs.code_controls(plans)]
    listed += [(f'run:{k}', p, frozen) for k, p, frozen in cs.run_controls(plans)]
    listed += [(f'model:{k}', p, {'exit': 0, 'stdout': line}) for k, p, line in MODEL_CONTROLS]
    listed += [(f'model:{k}', p, frozen) for k, p, frozen in DISPLAY_CONTROLS]
    listed += [('model:inspect-append-b-whole', append_b_whole(plans), {**cs.ILL_TYPED, 'calls': 3})]
    require(all(any(k.startswith(f'{kind}:') for k, _, _ in listed) for kind in ('plan', 'codes', 'run')),
            'check-spec lists admitted plan, code-list and run controls')
    require(any('fuel' in frozen for k, _, frozen in listed if k.startswith('run:')), 'check-spec freezes fuel run controls')
    out = []
    for label, plan, frozen in listed:
        require(cs.rejected(codec.encode(plan, DIGEST), REGISTRY, DIGEST) is None, f'{label}: the reference codec refuses it')
        fuel = frozen.get('fuel', cs.VM_FUEL)
        # check-spec's own comparison, at the control's fuel: a display line is frozen by its SHA-256.
        observed = cs.ran(plan, frozen)
        require(observed == frozen, f'{label}: the reference evaluation gives {observed}')
        got = reference_run(plan, fuel)
        want = {k: v for k, v in frozen.items() if k not in ('fuel', 'calls')} or expected_run(got)
        out.append((label, plan, fuel, want, frozen.get('calls', got['calls'])))
    return out


def control_argv(binary: Path, path: Path, plan: dict, fuel: int) -> list:
    """SPEC section 8's command line for a control, as check-spec's receipt records it."""
    return [binary, '--', path, *cs.run_argv(plan, {'fuel': fuel})[1:]]


def admitted_runs(model: Path, audit: Path, listed: list, argv=control_argv) -> dict:
    """Each admitted control's run at its fuel, its RC audit and its entries paid for."""
    folder = BUILD / 'admitted'
    folder.mkdir(parents=True, exist_ok=True)

    def one(item):
        label, plan, fuel, want, calls = item
        path = folder / (label.replace(':', '_') + '.kimg')
        data = codec.encode(plan, DIGEST)
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
        result = run(argv(model, path, plan, fuel), 120)
        audited = run(argv(audit, path, plan, fuel), 300)
        m = AUDIT.match(audited['stdout'].strip())
        balanced = bool(m) and audited['exit'] == 0 and m.group(1) == 'passed' and (
            'exit' not in want or m.group(4) == '0') and int(m.group(5)) == calls
        # A kill is judged on the observation that went wrong.
        return label, {'result': audited if agrees(want, result) else result,
                       'agrees': agrees(want, result) and balanced, 'calls': int(m.group(5)) if m else None}
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(pool.map(one, listed))


# Harness mutants: the gate's own reading of the run controls, weakened. Each runs the
# run controls against the base model and must be killed by the controls named.
def fuel_ignored(binary: Path, path: Path, plan: dict, fuel: int) -> list:
    return control_argv(binary, path, plan, cs.VM_FUEL)


def harness_runs(model: Path, audit: Path, admitted: list, base: dict) -> list:
    """`fuel-ignored` runs every control at 1,000,000: exactly the fuel controls whose frozen
    run differs from the reference evaluation's at 1,000,000 must kill it."""
    runs = [a for a in admitted if a[0].startswith('run:')]
    killers = sorted(label for label, plan, fuel, want, calls in runs
                     if fuel != cs.VM_FUEL and cs.ran(plan, {**want, 'calls': calls}) != {**want, 'calls': calls})
    got = admitted_runs(model, audit, runs, fuel_ignored)
    killed = sorted(n for n, r in got.items() if not r['agrees'] and base[n]['agrees'])
    require(killers and killed == killers, f'harness mutant fuel-ignored: killed by {killed}, the fuel controls {killers}')
    return [{'mutant': 'fuel-ignored', 'breaks': 'each run control runs at 1,000,000, not its frozen fuel', 'by': killed}]


AUDIT = re.compile(r'^audit\t(passed|failed)\t(\d+)\t(\w+)\t(\d+)\t(\d+)$')


def reference_calls(plan: dict, argv: list) -> int:
    """Entries the reference evaluation pays for on a golden's command line (SPEC section 7)."""
    if plan['entry'] == 'program':
        return reference.program(plan, codec.decimal(argv[1]))['calls']
    return reference.book(plan, argv[1], [codec.decimal(x) for x in argv[3:]], codec.decimal(argv[2]))['calls']


def audit_runs(audit: Path, expected: dict) -> dict:
    """The RC audit before every transition; a completed run ends with no live
    mortal cell, while a stopped one keeps its pending words. Every run pays for
    the entries the reference evaluation pays for. An Unsupported result type is
    refused before any transition."""
    cases = {n: c for n, c in expected['cases'].items() if c.get('outcome') != 'Unsupported'}
    plans = golden_plans()
    calls = {n: reference_calls(plans[n], cases[n]['argv']) for n in cases}
    with ThreadPoolExecutor(max_workers=8) as pool:
        got = dict(zip(cases, pool.map(lambda n: run(argv_of(audit, n, cases[n]['argv']), 300), cases)))
    out = {}
    for n, result in got.items():
        m = AUDIT.match(result['stdout'].strip() or result['stderr'].strip())
        outcome = cases[n].get('outcome') or ('Described' if cases[n]['argv'][1] == 'main' else 'Emitted')
        good = bool(m) and result['exit'] == 0 and m.group(1) == 'passed' and m.group(3) == outcome and (
            outcome in ('Exhausted', 'HostFailure') or m.group(4) == '0') and int(m.group(5)) == calls[n]
        out[n] = {'result': result, 'agrees': good, 'transitions': int(m.group(2)) if m else None,
                  'live': int(m.group(4)) if m else None, 'calls': int(m.group(5)) if m else None}
    return out


# Literal review of SPEC sections 3 and 6: a `none`-typed result fits any
# declared type, so these images validate, and the VM must refuse the ill-typed
# word where it is read: at a Case scrutinee, as a prim operand, and as the
# operand of a scalar constructor, whose completion reads the word it yields
# (Chr, as the reference evaluation's `construct` does, used or not). Neither
# the seed nor Bend source can launder a value, so the reference evaluation
# alone reproduces them.
FLAG = {'kind': 'data', 'name': 'Flag', 'constructors': [{'name': 'Off', 'fields': []}, {'name': 'On', 'fields': []}]}
PAIR = {'kind': 'data', 'name': 'Pair', 'constructors': [{'name': 'Pair', 'fields': [0, 0]}]}
IDENTITY = {'name': 'id', 'parameters': [None], 'result': None, 'slots': 1, 'body': ['ref', None, 0]}
INSPECTION = {
    'inspect-case': {'entry': 'book', 'types': [FLAG, PAIR], 'functions': [IDENTITY, {
        'name': 'main', 'parameters': [], 'result': 0, 'slots': 3,
        'body': ['let', 0, 0, ['call', 1, 0, [['value', 0, 1]]],
                 ['case', 0, 0, 1, 'tags', [['branch', 0, 1, 2, ['value', 0, 0]]], None]]}]},
    'inspect-prim': {'entry': 'book', 'representation': {'U32': 2, 'Bool': 3},
                     'types': [FLAG, PAIR, {'kind': 'opaque', 'name': 'U32'},
                               {'kind': 'data', 'name': 'Bool', 'constructors': [{'name': 'False', 'fields': []},
                                                                                {'name': 'True', 'fields': []}]}],
                     'functions': [IDENTITY, {
                         'name': 'main', 'parameters': [], 'result': 3, 'slots': 0,
                         'body': ['prim', 3, 8, [['prim', 2, 0, [['call', 2, 0, [['con', 1, 0, [['value', 0, 0], ['value', 0, 1]]]]],
                                                               ['lit', 2, 'U32', 1]]], ['lit', 2, 'U32', 2]]]}]},
}
# id(x: none) -> none launders a Pair or a closure into Chr's U32 operand: `c` below.
CHR_TYPES = [FLAG, PAIR, {'kind': 'opaque', 'name': 'U32'},
             {'kind': 'data', 'name': 'Char', 'constructors': [{'name': 'Chr', 'fields': [2]}]},
             {'kind': 'arrow', 'domain': 0, 'result': 0}]


def chr_of(value: list, body: list, slots: int) -> dict:
    """main() -> Flag = let c = Chr{id(value)} in body."""
    return {'entry': 'book', 'representation': {'U32': 2, 'Char': 3}, 'types': CHR_TYPES, 'functions': [IDENTITY, {
        'name': 'main', 'parameters': [], 'result': 0, 'slots': slots,
        'body': ['let', 0, 0, ['con', 3, 0, [['call', 2, 0, [value]]]], body]}]}


PAIRED = ['con', 1, 0, [['value', 0, 0], ['value', 0, 1]]]
NAT = {'kind': 'data', 'name': 'Nat', 'constructors': [{'name': 'Zero', 'fields': []}, {'name': 'Succ', 'fields': [0]}]}
INSPECTION.update({
    'inspect-chr-unused': chr_of(PAIRED, ['value', 0, 1], 1),
    'inspect-chr-closure': chr_of(['closure', 4, 1, 1, [], ['ref', 0, 0]], ['value', 0, 1], 1),
    'inspect-chr-used': chr_of(PAIRED, ['case', 0, 0, 3, 'tags', [['branch', 0, 1, 1, ['value', 0, 1]]], None], 2),
    # Section 8 renders Pair{1048574n, b} to exactly 1,048,576 visits before it reaches b,
    # a Pair laundered into a Nat field: the word is inspected before the visit is charged.
    'inspect-before-charge': {'entry': 'book', 'representation': {'Nat': 0}, 'types': [NAT, PAIR],
                              'functions': [IDENTITY, {'name': 'main', 'parameters': [], 'result': 1, 'slots': 0,
                                            'body': ['con', 1, 0, [['lit', 0, 'Nat', 1_048_574], ['call', 0, 0, [
                                                ['con', 1, 0, [['lit', 0, 'Nat', 0], ['lit', 0, 'Nat', 0]]]]]]]}]},
})


def inspection_runs(model: Path) -> dict:
    folder = BUILD / 'inspection'
    folder.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, plan in INSPECTION.items():
        data = codec.encode(plan, DIGEST)
        require(cs.rejected(data, REGISTRY, DIGEST) is None, f'{name}: the reference codec refuses it')
        got = reference.book(plan, 'main', [], 1000000)
        require({k: got.get(k) for k in cs.ILL_TYPED} == cs.ILL_TYPED, f'{name}: the reference evaluation gives {got}')
        path = folder / f'{name}.kimg'
        path.write_bytes(data)
        result = run([model, '--', path, 'main', '1000000'], 120)
        out[name] = {'result': result, 'agrees': (result['exit'], result['stdout'], result['stderr'])
                     == (5, '', 'HostFailure\timage\till-typed\n')}
    return out


# The model's own run controls, frozen by literal review of SPEC sections 3 and 6.1 before
# the model ran them: each plan is its source's core by hand, and the seed prints the value
# after the last tab. A tags-mode Case on Char dispatches on Chr (tag 0) for every code,
# immediate or Big; a key-mode Case admits every u32 key, 0xffffffff included (section 2).
U32 = {'kind': 'opaque', 'name': 'U32'}
CHAR = {'kind': 'data', 'name': 'Char', 'constructors': [{'name': 'Chr', 'fields': [0]}]}
BOOL = {'kind': 'data', 'name': 'Bool', 'constructors': [{'name': 'False', 'fields': []}, {'name': 'True', 'fields': []}]}


def chr_book(name: str, body: list, result: int, slots: int, argument: int) -> dict:
    """`name(c: Char)` over [U32, Char, Flag], applied by main to the Char `argument`."""
    return {'entry': 'book', 'representation': {'U32': 0, 'Char': 1}, 'types': [U32, CHAR, FLAG],
            'functions': [{'name': name, 'parameters': [1], 'result': result, 'slots': slots, 'body': body},
                          {'name': 'main', 'parameters': [], 'result': 2, 'slots': 0,
                           'body': ['call', 2, 0, [['lit', 1, 'Char', argument]]]}]}


def top_u32(key: int, argument: int) -> dict:
    return {'entry': 'book', 'representation': {'U32': 0}, 'types': [U32, FLAG],
            'functions': [{'name': 'top', 'parameters': [0], 'result': 1, 'slots': 1,
                           'body': ['case', 1, 0, 0, 'keys', [['branch', key, 1, 0, ['value', 1, 1]]], ['default', ['value', 1, 0]]]},
                          {'name': 'main', 'parameters': [], 'result': 1, 'slots': 0, 'body': ['call', 1, 0, [['lit', 0, 'U32', argument]]]}]}


PICK = ['case', 2, 0, 1, 'tags', [['branch', 0, 1, 1, ['value', 2, 1]]], None]
TOP = ['case', 2, 0, 1, 'keys', [['branch', 0xFFFFFFFF, 1, 0, ['value', 2, 1]]], ['default', ['value', 2, 0]]]
CHAR_MATCH = {'entry': 'book', 'representation': {'Bool': 0, 'U32': 1, 'Char': 2},
              'types': [BOOL, U32, {**CHAR, 'constructors': [{'name': 'Chr', 'fields': [1]}]}],
              'functions': [{'name': 'U32.is_eq', 'parameters': [1, 1], 'result': 0, 'slots': 2,
                             'body': ['prim', 0, 8, [['ref', 1, 0], ['ref', 1, 1]]]},
                            {'name': 'code', 'parameters': [2], 'result': 1, 'slots': 2,
                             'body': ['case', 1, 0, 2, 'tags', [['branch', 0, 1, 1, ['lit', 1, 'U32', 7]]], None]},
                            {'name': 'main', 'parameters': [], 'result': 0, 'slots': 0,
                             'body': ['call', 0, 0, [['call', 1, 1, [['lit', 2, 'Char', 65]]], ['lit', 1, 'U32', 7]]]}]}
MODEL_CONTROLS = [
    ('char-pick', chr_book('pick', PICK, 2, 2, 65), 'Evaluated\t2\t1\tOn{}\n'),
    ('char-pick-big', chr_book('pick', PICK, 2, 2, 2147483653), 'Evaluated\t2\t1\tOn{}\n'),
    ('char-match', CHAR_MATCH, 'Evaluated\t0\t1\tTrue{}\n'),
    ('key-max', top_u32(0xFFFFFFFF, 0xFFFFFFFF), 'Evaluated\t1\t1\tOn{}\n'),
    ('key-max-miss', top_u32(0xFFFFFFFF, 0xFFFFFFFE), 'Evaluated\t1\t0\tOff{}\n'),
    ('key-below-max', top_u32(0xFFFFFFFE, 0xFFFFFFFE), 'Evaluated\t1\t1\tOn{}\n'),
    ('char-key-max', chr_book('top', TOP, 2, 1, 0xFFFFFFFF), 'Evaluated\t2\t1\tOn{}\n'),
    ('char-key-max-miss', chr_book('top', TOP, 2, 1, 0xFFFFFFFE), 'Evaluated\t2\t0\tOff{}\n'),
]
MODEL_SOURCES = HERE / 'model-controls'


def utf8_nat(n: int) -> dict:
    """main() -> Nat = n, over a Nat whose Zero is named `üüüü` (8 bytes) and Succ
    `üüüüüüüü` (16 bytes): section 8 counts the tree's bytes, not its scalars."""
    return {'entry': 'book', 'representation': {'Nat': 0},
            'types': [{'kind': 'data', 'name': 'Nat', 'constructors': [{'name': 'ü' * 4, 'fields': []},
                                                                       {'name': 'ü' * 8, 'fields': [0]}]}],
            'functions': [{'name': 'main', 'parameters': [], 'result': 0, 'slots': 0, 'body': ['lit', 0, 'Nat', n]}]}


# Frozen by literal review of section 8, as check-spec freezes its display controls:
# 932,067 levels of 18 bytes around a 10-byte Zero are exactly 16,777,216 bytes, and one
# more level is Exhausted; counted as scalars (10 a level) both would print.
AT_BOUND = 'Evaluated\t0\t1\t' + ('ü' * 8 + '{') * 932_067 + 'ü' * 4 + '{}' + '}' * 932_067 + '\n'
DISPLAY_CONTROLS = [
    ('display-utf8-at-bound', utf8_nat(932_067), {'exit': 0, 'stdout_sha256': sha(AT_BOUND.encode()), 'calls': 1}),
    ('display-utf8-beyond-bound', utf8_nat(932_068), {'outcome': 'Exhausted', 'kind': 2, 'cause': 'display', 'calls': 1}),
]


def append_b_whole(plans: dict) -> dict:
    """String.append("x", SCon{'a', id(λ)}), its result discarded, frozen by literal review of
    SPEC sections 6 and 9: append reads the `b` it moves whole, so the closure in b's tail
    halts it with HostFailure image (ill-typed) after 3 calls (main, id, append).
    check-spec's inspect-append-b puts the closure at b's head, where a shallow read of b
    already refuses it."""
    nat, u32, char, string, boolean, flag, pair, arrow = range(8)
    types = [*plans['string-codes']['types'][:4], plans['string-eq']['types'][0], plans['value-on']['types'][0],
             {**PAIR, 'constructors': [{'name': 'Pair', 'fields': [flag, flag]}]}, {'kind': 'arrow', 'domain': flag, 'result': flag}]
    tail = ['call', string, 0, [['closure', arrow, 1, 1, [], ['ref', flag, 0]]]]
    b = ['con', string, 1, [['lit', char, 'Char', 97], tail]]
    append = {'name': 'String.append', 'parameters': [string, string], 'result': string, 'slots': 2,
              'body': ['prim', string, 35, [['ref', string, 0], ['ref', string, 1]]]}
    main = {'name': 'main', 'parameters': [], 'result': boolean, 'slots': 1,
            'body': ['let', boolean, 0, ['call', string, 1, [['lit', string, 'String', [120]], b]], ['value', boolean, 1]]}
    return {'entry': 'book', 'representation': {'Nat': nat, 'U32': u32, 'Char': char, 'String': string, 'Bool': boolean},
            'types': types, 'functions': [IDENTITY, append, main]}


def seed_controls() -> dict:
    """The seed's Bun lane prints each model control's frozen value."""
    names = [name for name, _, _ in MODEL_CONTROLS]
    require(sorted(p.stem for p in MODEL_SOURCES.glob('*.bend')) == sorted(names), 'vm/model-controls/ differs from MODEL_CONTROLS')
    with ThreadPoolExecutor(max_workers=8) as pool:
        got = dict(zip(names, pool.map(lambda n: run([SEED, MODEL_SOURCES / f'{n}.bend'], 300), names)))
    for name, _, line in MODEL_CONTROLS:
        seed = got[name]
        require((seed['exit'], seed['stdout']) == (0, line.split('\t')[-1]), f'{name}: the seed gives {seed}')
    return {name: got[name]['stdout'].strip() for name in names}


def reference_verdicts(name: str) -> list:
    data = (GOLDEN / f'{name}.kimg').read_bytes()
    w = words(data)
    require(all(t['kind'] != 'data' or t['constructors'] for t in codec.decode(data, DIGEST)['types']),
            f'{name}: a zero-constructor type would make the reference allocate 2^32 entries')
    out = []
    for i in range(len(w)):
        for k, value in enumerate((0, (w[i] + 1) & codec.NONE, (w[i] - 1) & codec.NONE)):
            m = list(w)
            m[i] = value
            out.append(cs.rejected(b''.join(x.to_bytes(4, 'little') for x in m), REGISTRY, DIGEST))
    return out


def sweep_runs(sweep: Path, swept) -> dict:
    """Validator soundness on bounded images: every single-word mutation (zero,
    successor, predecessor) of each swept golden, against the reference codec.
    The reference materializes a data type's constructor count before checking
    it, so a swept image must have no zero-constructor type, whose predecessor
    would be a 2^32-entry list."""
    reference = {name: reference_verdicts(name) for name in swept}
    with ThreadPoolExecutor(max_workers=8) as pool:
        got = dict(zip(swept, pool.map(lambda n: run([sweep, '--', GOLDEN / f'{n}.kimg', SWEEP_FUEL], 600), swept)))
    out = {}
    for name in swept:
        result, want = got[name], reference[name]
        lines = result['stdout'].strip().split('\n') if result['stdout'].strip() else []
        stats = {'mutations': len(want), 'admitted': 0, 'refused': 0, 'unsound': 0, 'differ': 0}
        examples = []
        good = result['exit'] == 0 and len(lines) == len(want)
        for j, line in enumerate(lines[:len(want)]):
            f = line.split('\t')
            require(f[:2] == [str(j // 3), str(j % 3)], f'{name}: sweep line {j} out of order')
            if f[-1] != 'sound':
                stats['unsound'] += 1
                examples.append(line)
            if f[2] == 'refused':
                stats['refused'] += 1
                refusal = model_refusal({'exit': 5 if f[3] == 'HostFailure' else 4, 'stderr': '\t'.join(f[3:-1])})
                same = refusal == want[j]
            else:
                stats['admitted'] += 1
                same = want[j] is None
            if not same:
                stats['differ'] += 1
                examples.append(f'{line} | reference {want[j]!r}')
        good = good and stats['unsound'] == 0 and stats['differ'] == 0
        out[name] = {'result': {'exit': result['exit'], 'stderr': result['stderr'][-400:]}, 'agrees': good,
                     'stats': stats, 'examples': examples[:5]}
    return out


def proof() -> dict:
    result = run([SEED, HERE / 'PROOF.bend'], 1800)
    laws = len(re.findall(r'^law ', (HERE / 'LAWS.bend').read_text(), re.M))
    return {'result': result, 'agrees': result['exit'] == 0 and result['stdout'].strip() == 'All terms check.',
            'laws': laws}


# ------------------------------------------------------------------ mutants

# Type-correct semantic mutants of the model: (name, section of vm/model/ or an entry of
# vm/, [(old, new)], what it breaks). Review fix rounds 1 and 2 add theirs, each killed by
# the control that witnessed its defect.
MUTANTS = [
    ('rc-under-count', 'memory', [('    Done{stored_word(heap,w,0,U32.add(rc,1))})))',
       '    Done{stored_word(heap,w,0,rc)})))')],
     'dup adds no reference'),
    ('rc-over-count', 'memory', [('    u => Done{stored_word(heap,w,0,U32.sub(rc,1))})))\n\ndef drops(',
       '    u => Done{stored_word(heap,w,0,rc)})))\n\ndef drops(')],
     'drop above one keeps its count'),
    ('append-drops-tail', 'memory', [('W.or(Bool.and(U32.is_eq(id,35),U32.is_eq(i,1)),Bool.and(W.within(id,16,19),U32.is_eq(i,0)))',
       'Bool.and(W.within(id,16,19),U32.is_eq(i,0))')],
     'String.append also drops its moved tail'),
    ('tail-keeps-caller', 'machine', [('    u => H.bind(H.Heap,Next,H.drop(heap,H.room(unscoped(stack)),H.act_of(stack)),heap => to(Eval{0},H.with_act(unscoped(stack),0),heap)),',
       '    u => to(Eval{0},H.with_act(unscoped(stack),0),heap),')],
     'a tail entry does not release its caller'),
    ('scope-keeps-slots', 'machine', [('      H.bind(H.Heap,Next,unwound(U32.to_nat(U32.sub(d,saved)),heap,act,U32.sub(d,1),H.room(popped)),heap =>',
       '      H.bind(H.Heap,Next,unwound(0n,heap,act,U32.sub(d,1),H.room(popped)),heap =>')],
     'leaving a scope keeps its slots'),
    ('arm-selection', 'machine', [('u => H.operand(code,node,U32.add(4,tag)),u => W.none())',
       'u => H.operand(code,node,U32.add(4,U32.sub(1,tag))),u => W.none())')],
     'a tag selects the other row'),
    ('slot-off-by-one', 'memory', [('def slot(+heap: Heap, +act: U32, +i: U32) -> U32:\n  load_word(heap,act,U32.add(4,i))',
       'def slot(+heap: Heap, +act: U32, +i: U32) -> U32:\n  load_word(heap,act,U32.add(5,i))')],
     'slots read one word late'),
    ('erased-argument', 'machine', [('      W.choose(Result<W.Stop,Next>,U32.is_eq(H.operand(code,node,1),1),\n        u => then_stack(Next,H.pushed(popped,H.InvokeArgument{node,w})',
       '      W.choose(Result<W.Stop,Next>,U32.is_eq(H.operand(code,node,1),0),\n        u => then_stack(Next,H.pushed(popped,H.InvokeArgument{node,w})')],
     'live and erased Invokes swap'),
    ('nat-bound', 'memory', [('W.choose(Result<W.Stop,Cell>,U32.is_gt(b,U32.sub(W.none(),a)),u => Fail{W.Exhausted{2,"NatRange"}},u => word_of(heap,U32.add(a,b)))',
       'word_of(heap,U32.add(a,b))')],
     'Nat.add wraps instead of exhausting'),
    ('succ-bound', 'machine', [('W.choose(Result<W.Stop,Next>,U32.is_eq(H.scalar(heap,a),W.none()),u => Fail{W.Exhausted{2,"NatRange"}},u =>',
       'W.choose(Result<W.Stop,Next>,False{},u => Fail{W.Exhausted{2,"NatRange"}},u =>')],
     'Succ wraps instead of exhausting'),
    ('remainder-by-zero', 'memory', [('    case 4n: word_of(heap,W.choose(U32,U32.is_eq(y,0),u => x,u => U32.mod(x,y)))',
       '    case 4n: word_of(heap,W.choose(U32,U32.is_eq(y,0),u => 0,u => U32.mod(x,y)))')],
     'x % 0 is 0'),
    ('wide-shift', 'memory', [('W.choose(U32,U32.is_ge(n,32),u => 0,',
       'W.choose(U32,U32.is_ge(n,31),u => 0,')],
     'a shift by 31 loses its bits'),
    ('fuel-unchecked', 'machine', [('  W.choose(Result<W.Stop,Machine>,U32.is_eq(fuel_of(meter),0),u => Fail{W.Exhausted{1,"fuel"}},u =>',
       '  W.choose(Result<W.Stop,Machine>,False{},u => Fail{W.Exhausted{1,"fuel"}},u =>')],
     'an entry at fuel 0 proceeds'),
    ('child-order', 'decode', [('      W.unless(Claims,U32.is_ge(at,parent),"child after parent",u =>',
       '      W.unless(Claims,U32.is_gt(at,parent),"child after parent",u =>')],
     'a child may sit at its parent'),
    ('capture-exactness', 'validate', [('        W.unless(U32,Bool.not(exact),at_where(owner,"captures are not exactly the free slots of the body"),u =>',
       '        W.unless(U32,False{},at_where(owner,"captures are not exactly the free slots of the body"),u =>')],
     'unused captures are admitted'),
    ('inspection', 'memory', [('  W.choose(Result<W.Stop,A>,admits(code,heap,t,w),next,u => ill_typed(A))',
       '  W.choose(Result<W.Stop,A>,True{},next,u => ill_typed(A))')],
     'words are read without inspection'),
    ('char-tag', 'memory', [('  W.choose(U32,is_rep(code,t,2),u => 0,u =>\n',
       '  W.choose(U32,False{},u => 0,u =>\n')],
     'a Char dispatches on its code, not on Chr'),
    ('key-bound', 'validate', [('Expect{W.or(Bool.not(increasing(keys_of(rows))),Maybe.is_none(&2,W.Node,fallback))',
       'Expect{W.or(Bool.not(Bool.and(increasing(keys_of(rows)),below(keys_of(rows),W.none()))),Maybe.is_none(&2,W.Node,fallback))')],
     'the key 0xffffffff is refused'),
    ('none-slot', 'validate', [('Bool.not(W.or(W.is_none(held),U32.is_eq(held,scrutinee)))',
       'Bool.not(U32.is_eq(held,scrutinee))')],
     'a Case on a none-typed slot is refused'),
    ('debit-refunded', 'machine', [('    case Fail{stop}: Done{halted(m,stop)}',
       '    case Fail{stop}: Fail{stop}')],
     'a target that stops the machine refunds its entry'),
    ('non-scalar-printed', 'machine', [('W.choose(Result<W.Stop,Machine>,Bool.not(is_scalar_text(H.scalars_of(line,heap))),u => Fail{W.Refused{"io","abi"}},u =>',
       'W.choose(Result<W.Stop,Machine>,False{},u => Fail{W.Refused{"io","abi"}},u =>')],
     'a non-scalar Char is printed (D20)'),
    ('enter-arity', 'machine', [('u => U32.is_eq(W.count(U32,ops),W.choose(U32,W.is_none(node),u => 1,u => H.operand(code,node,1))),',
       'u => U32.is_le(W.count(U32,ops),1),')],
     'a closure takes either operand count'),
    ('calls-uncounted', 'machine', [('Meter{U32.sub(fuel,1),U32.add(calls,1),',
       'Meter{U32.sub(fuel,1),calls,')],
     'an entry is not counted'),
    ('arrow-argument', 'machine', [('W.choose(Result<W.Stop,List<&2,U32>>,V.is_arrow(V.kind(types,p)),u => Fail{W.Refused{"invoke","function-argument"}},u =>',
       'W.choose(Result<W.Stop,List<&2,U32>>,False{},u => Fail{W.Refused{"invoke","function-argument"}},u =>')],
     'an arrow parameter is refused as argument-range'),
    # Review round 1, second batch: arm fit (SPEC section 3), section 8's display
    # visits and bytes, and Chr's inspection.
    ('exact-branch-type', 'validate', [('Expect{Bool.not(fit(types,t,type_of(body))),at_where(site,"branch body type")}',
       'Expect{Bool.not(U32.is_eq(type_of(body),t)),at_where(site,"branch body type")}')],
     "a Branch body must equal its Case's type"),
    ('exact-key-and-default-type', 'validate', [
        ('Expect{Bool.not(fit(types,t,type_of(body))),at_where(site,"key branch body type")}',
         'Expect{Bool.not(U32.is_eq(type_of(body),t)),at_where(site,"key branch body type")}'),
        ('Expect{Bool.not(fit(types,t,type_of(body))),at_where(site,"default body type")}',
         'Expect{Bool.not(U32.is_eq(type_of(body),t)),at_where(site,"default body type")}')],
     "key Branch and Default bodies must equal their Case's type"),
    ('chr-uninspected', 'machine', [('u => H.inspected_at(Next,code,heap,t,a,u => to(Return{a},stack,heap)),u =>',
       'u => to(Return{a},stack,heap),u =>')],
     'Chr yields its operand without inspecting it'),
    ('display-visits-exclusive', 'machine', [('W.choose(Result<W.Stop,List<&2,U32>>,U32.is_gt(n,U32.sub(visit_limit(),visits)),',
       'W.choose(Result<W.Stop,List<&2,U32>>,U32.is_ge(n,U32.sub(visit_limit(),visits)),')],
     'the visit bound is exclusive'),
    ('display-bytes-exclusive', 'machine', [('U32.is_gt(text_size(t),U32.sub(display_limit(),size))',
       'U32.is_ge(text_size(t),U32.sub(display_limit(),size))')],
     'the byte bound is exclusive'),
    ('display-unary-bytes-exclusive', 'machine', [('U32.is_gt(n,U32.div(U32.sub(room,base),level))',
       'U32.is_gt(n,U32.div(U32.sub(U32.sub(room,1),base),level))')],
     "the byte bound is exclusive for a Nat's spelling"),
    ('display-nat-one-visit', 'machine', [
        ('W.choose(Result<W.Stop,List<&2,U32>>,U32.is_gt(n,U32.sub(visit_limit(),visits)),', 'W.choose(Result<W.Stop,List<&2,U32>>,False{},'),
        ('render(f,code,heap,rest,U32.add(visits,n),', 'render(f,code,heap,rest,visits,')],
     'a Nat word is one visit'),
    ('display-unary-unbounded', 'machine', [('W.choose(U32,U32.is_gt(n,U32.div(U32.sub(room,base),level)),u => W.none(),',
       'W.choose(U32,False{},u => W.none(),')],
     "a Nat's spelling is not charged against the byte bound"),
    ('display-commas-free', 'machine', [('u => 1,u => W.choose(U32,U32.is_lt(c,2048)',
       'u => Bool.pick(U32,U32.is_eq(c,44),0,1),u => W.choose(U32,U32.is_lt(c,2048)')],
     'separators are not text'),
    ('display-scalars', 'machine', [('u => 1,u => W.choose(U32,U32.is_lt(c,2048),u => 2,u => W.choose(U32,U32.is_lt(c,65536),u => 3,u => 4))',
       'u => 1,u => 1')],
     'the tree is counted in scalars, not bytes'),
    ('display-succ-named', 'machine', [('repeated_text(U32.to_nat(n),List.append(&2,U32,constructor_name(code,t,1),text("{")))',
       'repeated_text(U32.to_nat(n),text("Succ{"))')],
     "a Nat spells Succ, not its type's successor"),
    ('display-charge-first', 'machine', [(
        '      H.inspected_at(List<&2,U32>,code,heap,t,w,u =>\n'
        '      W.choose(Result<W.Stop,List<&2,U32>>,U32.is_ge(visits,visit_limit()),u => exhausted(List<&2,U32>),u =>\n',
        '      W.choose(Result<W.Stop,List<&2,U32>>,U32.is_ge(visits,visit_limit()),u => exhausted(List<&2,U32>),u =>\n'
        '      H.inspected_at(List<&2,U32>,code,heap,t,w,u =>\n')],
     'a word is charged before it is inspected'),
    # SPEC section 8's argument forms, in the command line (vm/model-cli.bend).
    ('separator-unchecked', 'model-cli', [(
        'case False{} Con{budget,Con{separator,rest}}: W.choose(IO(Unit),String.eq(separator,"--"),',
        'case False{} Con{budget,Con{separator,rest}}: W.choose(IO(Unit),True{},')],
     "a Program's second word need not be `--`"),
    ('usage-as-word', 'model-cli', [('  stopped(W.Refused{"arguments","usage"})', '  stopped(W.Refused{"arguments","expected-u32"})')],
     'a missing word is expected-u32, not usage'),
    # Review round 2: the model's connectives are choices, which the native lane reads.
    ('or-through-base', 'word', [('def or(a: Bool, b: Bool) -> Bool:\n  choose(Bool,a,u => True{},u => b)',
                                  'def or(a: Bool, b: Bool) -> Bool:\n  Bool.or(a,b)')],
     "W.or is Base's Bool.or"),
    ('xor-through-base', 'word', [('def xor(a: Bool, +b: Bool) -> Bool:\n  choose(Bool,a,u => Bool.not(b),u => b)',
                                   'def xor(a: Bool, +b: Bool) -> Bool:\n  Bool.xor(a,b)')],
     "W.xor is Base's Bool.xor"),
    # vm-spec 5517f26: append reads the b it moves whole (SPEC section 9).
    ('append-b-shallow', 'memory', [('    case 35n: string_cell(code,heap,a,s => string_cell(code,heap,b,t => chain(List.reverse(&2,U32,s),code,heap,b)))',
                                     '    case 35n: string_cell(code,heap,a,s => chain(List.reverse(&2,U32,s),code,heap,b))')],
     "append reads only the head of the b it moves"),
]


# Mutants whose PROOF.bend must also fail, at a law and not by a crash.
LAW_MUTANTS = ('rc-under-count', 'tail-keeps-caller', 'arm-selection', 'nat-bound', 'remainder-by-zero',
               'char-tag', 'key-bound', 'exact-key-and-default-type', 'chr-uninspected', 'display-scalars',
               'display-succ-named')


def law_kill(tree: Path) -> str | None:
    result = run([SEED, tree / 'vm' / 'PROOF.bend'], 1800)
    found = re.search(r'Location: LAWS\.(\w+)', result['stdout'] + result['stderr'])
    return found.group(1) if result['exit'] not in (0, None) and found else None


def kills(base: dict, mutant: dict) -> list:
    """Checks whose observation changed to a well-formed wrong one."""
    killed = []
    for check, rows in mutant.items():
        for name, row in rows.items():
            if not row['agrees'] and base[check][name]['agrees'] and (
                    check == 'sweep' or well_formed(row['result'])):
                killed.append(f'{check}:{name}')
    return killed


def mutant_runs(expected: dict, listed: list, admitted: list, base: dict) -> list:
    def one(entry):
        name, section, mutation, meaning = entry
        tree = build_tree(f'mutants/{name}', section, mutation)
        # vm/model-lanes.bend imports word.bend alone: only a word mutant can change it.
        bins = built(tree, ('model', 'audit', 'lanes') if section == 'word' else ('model', 'audit'))
        observed = {'goldens': golden_runs(bins['model'], expected),
                    'invocations': invocation_runs(bins['model'], bins['audit'], expected),
                    'inspection': inspection_runs(bins['model']),
                    **({'lanes': lane_runs(bins['lanes'])} if 'lanes' in bins else {}),
                    'connectives': connective_runs(tree),
                    'fuel': fuel_runs(bins['model'], expected),
                    'controls': control_runs(bins['model'], listed),
                    'admitted': admitted_runs(bins['model'], bins['audit'], admitted),
                    'arguments': argument_runs(bins['model'], bins['audit']),
                    'audit': audit_runs(bins['audit'], expected)}
        killed = kills(base, observed)
        law = law_kill(tree) if name in LAW_MUTANTS else None
        require(name not in LAW_MUTANTS or law, f'mutant {name}: PROOF.bend did not fail at a law')
        crashes = [f'{c}:{n}' for c, rows in observed.items() for n, r in rows.items()
                   if not r['agrees'] and not well_formed(r['result'])]
        return {'mutant': name, 'breaks': meaning, 'killed': bool(killed), 'by': killed[:8],
                'kills': len(killed), 'law': law, 'crashes': len(crashes)}
    with ThreadPoolExecutor(max_workers=3) as pool:
        return list(pool.map(one, MUTANTS))


# ------------------------------------------------------------------ main

def kinds(rows: dict) -> dict:
    """Controls counted by their source, the label's prefix (plan, codes, run, model)."""
    out = {}
    for label in rows:
        out[label.split(':')[0]] = out.get(label.split(':')[0], 0) + 1
    return out


def summary(rows: dict) -> dict:
    return {'agree': sum(r['agrees'] for r in rows.values()), 'total': len(rows),
            'differ': sorted(n for n, r in rows.items() if not r['agrees'])}


def main() -> int:
    BUILD.mkdir(parents=True, exist_ok=True)
    expected = json.loads((GOLDEN / 'vm-expected.json').read_text())
    record = {'gate': 'vm-model', 'date': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
              'status': 'failed', 'sources': {s: sha((HERE / s).read_bytes()) for s in SOURCES}}
    record['fixtures'] = check_inputs(expected)
    record['registry'] = check_registry()
    record['connectives'] = check_connectives()
    record['seed'] = seed_controls()

    tree = build_tree('base')
    bins = built(tree, ('model', 'audit', 'sweep', 'lanes'))
    record['lanes'] = check_lanes(tree, bins['lanes'])
    listed = controls()
    admitted = admitted_controls()
    base = {'goldens': golden_runs(bins['model'], expected),
            'invocations': invocation_runs(bins['model'], bins['audit'], expected),
            'inspection': inspection_runs(bins['model']),
            'lanes': lane_runs(bins['lanes']),
            'connectives': connective_runs(tree),
            'fuel': fuel_runs(bins['model'], expected),
            'controls': control_runs(bins['model'], listed),
            'admitted': admitted_runs(bins['model'], bins['audit'], admitted),
            'arguments': argument_runs(bins['model'], bins['audit']),
            'audit': audit_runs(bins['audit'], expected)}
    for check, rows in base.items():
        bad = {n: r['result'] for n, r in rows.items() if not r['agrees']}
        require(not bad, (check, dict(list(bad.items())[:3])))
    swept = sweep_runs(bins['sweep'], sorted(expected['cases']))
    bad = {n: (r['stats'], r['examples'], r['result']) for n, r in swept.items() if not r['agrees']}
    require(not bad, ('sweep', bad))
    with ThreadPoolExecutor(max_workers=2) as pool:
        proving = pool.submit(proof)
        mutants = mutant_runs(expected, listed, admitted, {**base, 'sweep': swept})
        proven = proving.result()
    require(proven['agrees'], ('proof', proven['result']))
    survivors = [m['mutant'] for m in mutants if not m['killed']]
    require(not survivors, f'surviving mutants {survivors}')
    harness = harness_runs(bins['model'], bins['audit'], admitted, base['admitted'])

    record.update(
        status='passed',
        goldens={n: {'exit': r['result']['exit'], 'outcome': (r['result']['stdout'] or r['result']['stderr']).strip()[:120]}
                 for n, r in base['goldens'].items()},
        invocations={n: (r['result']['stdout'] or r['result']['stderr']).strip()[:120] for n, r in base['invocations'].items()},
        fuel=summary(base['fuel']),
        inspection={n: r['result']['stderr'].strip() for n, r in base['inspection'].items()},
        arguments={n: (r['result']['stdout'] or r['result']['stderr']).strip()[:120] for n, r in base['arguments'].items()},
        controls={n: r['reference'] for n, r in base['controls'].items()},
        admitted_kinds=kinds(base['admitted']),
        admitted={n: {'outcome': (r['result']['stdout'] or r['result']['stderr']).strip()[:120], 'calls': r['calls']}
                  for n, r in base['admitted'].items()},
        audit={n: {'transitions': r['transitions'], 'live': r['live'], 'calls': r['calls']} for n, r in base['audit'].items()},
        sweep={n: r['stats'] for n, r in swept.items()},
        proof={'laws': proven['laws'], 'stdout': proven['result']['stdout'].strip()},
        mutants=mutants,
        harness_mutants=harness)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(record, indent=1) + '\n')
    swept_total = sum(r['stats']['mutations'] for r in swept.values())
    print(f"vm-model passed: {len(base['goldens'])} goldens, {len(base['invocations'])} invocations, "
          f"{len(base['fuel'])} fuel controls, "
          f"{len(base['controls'])} refusal controls, {len(base['arguments'])} argument controls, "
          f"{len(base['admitted'])} admitted controls "
          f"({', '.join(f'{n} {k}' for k, n in kinds(base['admitted']).items())}), "
          f"{len(base['audit'])} audited runs, "
          f"{swept_total} swept mutations of {len(swept)} images, {proven['laws']} laws, "
          f"{len(mutants)} killed mutants, {len(harness)} killed harness mutant; {RECEIPT.relative_to(ROOT)}")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except AssertionError as failure:
        print(f'vm-model failed: {failure}', file=sys.stderr)
        sys.exit(1)
