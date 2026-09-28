#!/usr/bin/env python3
"""Gate vm-model: the Bend model of knot-vm-1 against the frozen goldens.

Builds vm/model.bend's three entries (run, RC audit, soundness sweep) with the
seed's native lane and requires:
- every golden image to be the one vm-spec froze, and each LAWS.bend fixture to
  equal its image's words;
- the model's prim and foreign tables to equal registry.json;
- every golden run to agree with vm/golden/vm-expected.json (SPEC section 11);
- literal fuel controls (SPEC section 7): fuel 0 exhausts every golden at its
  first entry, and value-on, which makes one entry, completes on fuel 1;
- the 61 frozen refusal controls, and a child at its parent's offset, refused
  with check-spec's exact reason;
- the RC audit before every transition of every golden, and no live mortal cell
  after each completed run;
- the bounded soundness sweep: every single-word mutation of the swept goldens
  is refused exactly when the reference codec refuses it, for the same reason,
  and every admitted mutation runs soundly;
- vm/PROOF.bend to print 'All terms check.';
- every model mutant killed by a wrong observation of those checks, never by a
  crash or a timeout, and five of them also refuted by a law of PROOF.bend.
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
SOURCES = ('model.bend', 'model-cli.bend', 'model-audit.bend', 'model-sweep.bend', 'LAWS.bend', 'PROOF.bend')
ENTRIES = {'model': 'model-cli.bend', 'audit': 'model-audit.bend', 'sweep': 'model-sweep.bend'}
SWEEP_FUEL = '256'  # every golden completes within 256 entries; mutants that loop stop early


def load_check_spec():
    spec = importlib.util.spec_from_file_location('check_spec', HERE / 'check-spec.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cs = load_check_spec()
codec = cs.codec
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
    """Goldens are vm-spec's frozen images; LAWS.bend's fixtures are their words."""
    spec = json.loads((HERE / 'receipts/spec.json').read_text())
    frozen = {f['name']: f['image_sha256'] for f in spec['fixtures']}
    require(set(frozen) == set(expected['cases']), 'golden set differs from vm-spec')
    for name, digest in frozen.items():
        require(sha((GOLDEN / f'{name}.kimg').read_bytes()) == digest, f'{name}.kimg is not the frozen image')
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
    source = (HERE / 'model.bend').read_text()
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


# ------------------------------------------------------------------ builds

def build_tree(name: str, mutation=None) -> Path:
    tree = BUILD / name
    (tree / 'vm').mkdir(parents=True, exist_ok=True)
    for source in SOURCES:
        text = (HERE / source).read_text()
        if source == 'model.bend' and mutation:
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


def agrees(case: dict, got: dict) -> bool:
    if 'outcome' not in case:
        return (got['exit'], got['stdout'], got['stderr']) == (case['exit'], case['stdout'], case['stderr'])
    fields = got['stderr'].rstrip('\n').split('\t')
    if case['outcome'] == 'Exhausted':
        return got['exit'] == 4 and got['stdout'] == '' and fields == ['Exhausted', 'vm', str(case['kind']), case['cause']]
    if case['outcome'] == 'Unsupported':
        return got['exit'] == 3 and got['stdout'] == '' and fields == ['Unsupported', *case['cause'].split(' ')]
    return False


def golden_runs(model: Path, expected: dict) -> dict:
    cases = expected['cases']
    with ThreadPoolExecutor(max_workers=8) as pool:
        got = dict(zip(cases, pool.map(lambda n: run(argv_of(model, n, cases[n]['argv']), 120), cases)))
    return {n: {'result': got[n], 'agrees': agrees(cases[n], got[n])} for n in cases}


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


def controls() -> list:
    names = sorted(p.stem for p in GOLDEN.glob('*.kimg'))
    images = {n: (GOLDEN / f'{n}.kimg').read_bytes() for n in names}
    plans = {n: json.loads((GOLDEN / f'{n}.plan.json').read_text()) for n in names}
    listed = cs.byte_controls(images, DIGEST) + [
        (f'plan:{k}', codec.encode(p, DIGEST), 'HostFailure image: validator: ', m) for k, p, m in cs.plan_controls(plans)]
    require(len(listed) == 61, f'{len(listed)} refusal controls, SPEC section 4 freezes 61')
    # One boundary the frozen controls leave open: a child at its own parent's
    # offset does not precede it. The reference supplies the expected reason.
    capture = images['closure-captures']
    body = cs.word(capture, cs.word(capture, 7) + 1 + 5)
    listed.append(('model:child-is-parent', cs.word_patch(capture, body + 4, body), '', ''))
    return [(label, data, cs.rejected(data, REGISTRY, DIGEST)) for label, data, _, _ in listed]


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


AUDIT = re.compile(r'^audit\t(passed|failed)\t(\d+)\t(\w+)\t(\d+)$')


def audit_runs(audit: Path, expected: dict) -> dict:
    """The RC audit before every transition; a completed run ends with no live
    mortal cell. result-u32 is refused before any transition."""
    cases = {n: c for n, c in expected['cases'].items() if c.get('outcome') != 'Unsupported'}
    with ThreadPoolExecutor(max_workers=8) as pool:
        got = dict(zip(cases, pool.map(lambda n: run(argv_of(audit, n, cases[n]['argv']), 300), cases)))
    out = {}
    for n, result in got.items():
        m = AUDIT.match(result['stdout'].strip() or result['stderr'].strip())
        outcome = 'Exhausted' if cases[n].get('outcome') == 'Exhausted' else (
            'Described' if cases[n]['argv'][1] == 'main' else 'Emitted')
        good = bool(m) and result['exit'] == 0 and m.group(1) == 'passed' and m.group(3) == outcome and (
            outcome == 'Exhausted' or m.group(4) == '0')
        out[n] = {'result': result, 'agrees': good,
                  'transitions': int(m.group(2)) if m else None, 'live': int(m.group(4)) if m else None}
    return out


# Literal review of SPEC sections 3 and 6: a `none`-typed result fits any
# declared type, so these images validate, and the VM must refuse the ill-typed
# word where it is read: at a Case scrutinee, and as a prim operand.
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


def inspection_runs(model: Path) -> dict:
    folder = BUILD / 'inspection'
    folder.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, plan in INSPECTION.items():
        data = codec.encode(plan, DIGEST)
        require(cs.rejected(data, REGISTRY, DIGEST) is None, f'{name}: the reference codec refuses it')
        path = folder / f'{name}.kimg'
        path.write_bytes(data)
        result = run([model, '--', path, 'main', '1000000'], 120)
        out[name] = {'result': result, 'agrees': (result['exit'], result['stdout'], result['stderr'])
                     == (5, '', 'HostFailure\timage\till-typed\n')}
    return out


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


# The one reference refusal the model does not share: SPEC section 2 admits
# every u32 in a String constant, while serializer.safe_chr refuses a code it
# cannot spell as plan text. The model admits such an image.
PLAN_TEXT = 'HostFailure image: string code beyond plan text'


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
        stats = {'mutations': len(want), 'admitted': 0, 'refused': 0, 'unsound': 0, 'differ': 0, 'plan-text': 0}
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
                same = want[j] is None or want[j] == PLAN_TEXT
                stats['plan-text'] += want[j] == PLAN_TEXT
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

# Type-correct semantic mutants of vm/model.bend: (name, [(old, new)], what it breaks).
MUTANTS = [
    ('rc-under-count', [('    Done{stored_word(heap,w,0,U32.add(rc,1))})))',
                         '    Done{stored_word(heap,w,0,rc)})))')], 'dup adds no reference'),
    ('rc-over-count', [('    u => Done{stored_word(heap,w,0,U32.sub(rc,1))})))\n\ndef drops(',
                        '    u => Done{stored_word(heap,w,0,rc)})))\n\ndef drops(')], 'drop above one keeps its count'),
    ('append-drops-tail', [('Bool.or(Bool.and(U32.is_eq(id,35),U32.is_eq(i,1)),Bool.and(within(id,16,19),U32.is_eq(i,0)))',
                            'Bool.and(within(id,16,19),U32.is_eq(i,0))')], 'String.append also drops its moved tail'),
    ('tail-keeps-caller', [('    u => bind(Heap,Next,drop(heap,room(unscoped(stack)),act_of(stack)),heap => to(Eval{0},with_act(unscoped(stack),0),heap)),',
                            '    u => to(Eval{0},with_act(unscoped(stack),0),heap),')], 'a tail entry does not release its caller'),
    ('scope-keeps-slots', [('      bind(Heap,Next,unwound(U32.to_nat(U32.sub(d,saved)),heap,act,U32.sub(d,1),room(popped)),heap =>',
                            '      bind(Heap,Next,unwound(0n,heap,act,U32.sub(d,1),room(popped)),heap =>')], 'leaving a scope keeps its slots'),
    ('arm-selection', [('u => operand(code,node,U32.add(4,tag)),u => none())', 'u => operand(code,node,U32.add(4,U32.sub(1,tag))),u => none())')],
     'a tag selects the other row'),
    ('slot-off-by-one', [('def slot(+heap: Heap, +act: U32, +i: U32) -> U32:\n  load_word(heap,act,U32.add(4,i))',
                          'def slot(+heap: Heap, +act: U32, +i: U32) -> U32:\n  load_word(heap,act,U32.add(5,i))')], 'slots read one word late'),
    ('erased-argument', [('      choose(Result<Stop,Next>,U32.is_eq(operand(code,node,1),1),\n        u => then_stack(Next,pushed(popped,InvokeArgument{node,w})',
                          '      choose(Result<Stop,Next>,U32.is_eq(operand(code,node,1),0),\n        u => then_stack(Next,pushed(popped,InvokeArgument{node,w})')],
     'live and erased Invokes swap'),
    ('nat-bound', [('choose(Result<Stop,Cell>,U32.is_gt(b,U32.sub(none(),a)),u => Fail{Exhausted{2,"NatRange"}},u => word_of(heap,U32.add(a,b)))',
                    'word_of(heap,U32.add(a,b))')], 'Nat.add wraps instead of exhausting'),
    ('succ-bound', [('choose(Result<Stop,Next>,U32.is_eq(scalar(heap,a),none()),u => Fail{Exhausted{2,"NatRange"}},u =>',
                     'choose(Result<Stop,Next>,False{},u => Fail{Exhausted{2,"NatRange"}},u =>')], 'Succ wraps instead of exhausting'),
    ('remainder-by-zero', [('    case 4n: word_of(heap,choose(U32,U32.is_eq(y,0),u => x,u => U32.mod(x,y)))',
                            '    case 4n: word_of(heap,choose(U32,U32.is_eq(y,0),u => 0,u => U32.mod(x,y)))')], 'x % 0 is 0'),
    ('wide-shift', [('choose(U32,U32.is_ge(n,32),u => 0,', 'choose(U32,U32.is_ge(n,31),u => 0,')], 'a shift by 31 loses its bits'),
    ('fuel-unchecked', [('  choose(Result<Stop,Machine>,U32.is_eq(fuel_of(meter),0),u => Fail{Exhausted{1,"fuel"}},u =>',
                         '  choose(Result<Stop,Machine>,False{},u => Fail{Exhausted{1,"fuel"}},u =>')], 'an entry at fuel 0 proceeds'),
    ('child-order', [('      unless(Claims,U32.is_ge(at,parent),"child after parent",u =>',
                      '      unless(Claims,U32.is_gt(at,parent),"child after parent",u =>')], 'a child may sit at its parent'),
    ('capture-exactness', [('        unless(U32,Bool.not(exact),at_where(owner,"captures are not exactly the free slots of the body"),u =>',
                            '        unless(U32,False{},at_where(owner,"captures are not exactly the free slots of the body"),u =>')],
     'unused captures are admitted'),
    ('inspection', [('  choose(Result<Stop,A>,admits(code,heap,t,w),next,u => ill_typed(A))',
                     '  choose(Result<Stop,A>,True{},next,u => ill_typed(A))')], 'words are read without inspection'),
]


# Mutants whose PROOF.bend must also fail, at a law and not by a crash.
LAW_MUTANTS = ('rc-under-count', 'tail-keeps-caller', 'arm-selection', 'nat-bound', 'remainder-by-zero')


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


def mutant_runs(expected: dict, listed: list, base: dict) -> list:
    def one(entry):
        name, mutation, meaning = entry
        tree = build_tree(f'mutants/{name}', mutation)
        bins = built(tree, ('model', 'audit'))
        observed = {'goldens': golden_runs(bins['model'], expected),
                    'inspection': inspection_runs(bins['model']),
                    'fuel': fuel_runs(bins['model'], expected),
                    'controls': control_runs(bins['model'], listed),
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

    tree = build_tree('base')
    bins = built(tree, ('model', 'audit', 'sweep'))
    listed = controls()
    base = {'goldens': golden_runs(bins['model'], expected),
            'inspection': inspection_runs(bins['model']),
            'fuel': fuel_runs(bins['model'], expected),
            'controls': control_runs(bins['model'], listed),
            'audit': audit_runs(bins['audit'], expected)}
    for check, rows in base.items():
        bad = {n: r['result'] for n, r in rows.items() if not r['agrees']}
        require(not bad, (check, dict(list(bad.items())[:3])))
    swept = sweep_runs(bins['sweep'], sorted(expected['cases']))
    bad = {n: (r['stats'], r['examples'], r['result']) for n, r in swept.items() if not r['agrees']}
    require(not bad, ('sweep', bad))
    with ThreadPoolExecutor(max_workers=2) as pool:
        proving = pool.submit(proof)
        mutants = mutant_runs(expected, listed, {**base, 'sweep': swept})
        proven = proving.result()
    require(proven['agrees'], ('proof', proven['result']))
    survivors = [m['mutant'] for m in mutants if not m['killed']]
    require(not survivors, f'surviving mutants {survivors}')

    record.update(
        status='passed',
        goldens={n: {'exit': r['result']['exit'], 'outcome': (r['result']['stdout'] or r['result']['stderr']).strip()[:120]}
                 for n, r in base['goldens'].items()},
        fuel=summary(base['fuel']),
        inspection={n: r['result']['stderr'].strip() for n, r in base['inspection'].items()},
        controls={n: r['reference'] for n, r in base['controls'].items()},
        audit={n: {'transitions': r['transitions'], 'live': r['live']} for n, r in base['audit'].items()},
        sweep={n: r['stats'] for n, r in swept.items()},
        proof={'laws': proven['laws'], 'stdout': proven['result']['stdout'].strip()},
        mutants=mutants)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(record, indent=1) + '\n')
    swept_total = sum(r['stats']['mutations'] for r in swept.values())
    print(f"vm-model passed: {len(base['goldens'])} goldens, {len(base['fuel'])} fuel controls, "
          f"{len(base['controls'])} refusal controls, {len(base['audit'])} audited runs, "
          f"{swept_total} swept mutations of {len(swept)} images, {proven['laws']} laws, "
          f"{len(mutants)} killed mutants; {RECEIPT.relative_to(ROOT)}")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except AssertionError as failure:
        print(f'vm-model failed: {failure}', file=sys.stderr)
        sys.exit(1)
