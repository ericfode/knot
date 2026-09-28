#!/usr/bin/env python3
"""Gate vm-spec: frozen golden images against the pinned seed and eval-cli.

Re-executes the oracle lanes on every golden source and compares the frozen
observations byte for byte; re-derives the prim registry; checks that every
committed image equals its plan's encoding, decodes back to that plan, passes
the validator and agrees with the oracle checker's own core display; freezes
the VM expectation table under the Exhausted-lane rule; checks the bench
freeze; and requires every negative control and mutant to be rejected.
It implements no VM and evaluates no image.
"""
from __future__ import annotations

import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'vm'
GOLDEN = HERE / 'golden'
BUILD = ROOT / '.local/vm-spec/gate'
SEED = ROOT / 'scripts/bend-reference'
SCALE = float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))  # hang guard only
EVAL_BUDGET = '1048576'
VM_FUEL = 1_000_000
RECEIPT = HERE / 'receipts/spec.json'
EXPECTED = GOLDEN / 'vm-expected.json'
CODEC = HERE / 'serializer.py'


def load_codec(text: str | None = None):
    module = types.ModuleType('serializer')
    module.__file__ = str(CODEC)
    exec(compile(text if text is not None else CODEC.read_text(), str(CODEC), 'exec'), module.__dict__)
    return module


codec = load_codec()


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(argv, timeout):
    argv = [str(x) for x in argv]
    try:
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=timeout * SCALE,
                           env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
    except subprocess.TimeoutExpired:
        return {'exit': None, 'outcome': 'harness-timeout', 'stdout': '', 'stderr': ''}
    return {'exit': p.returncode, 'stdout': p.stdout.decode('utf-8', 'replace'),
            'stderr': p.stderr.decode('utf-8', 'replace')}


def observed(result):
    return {k: result[k] for k in ('exit', 'stdout', 'stderr')}


# ------------------------------------------------------------------ oracles

def oracles() -> dict:
    """Extract the pinned evaluator snapshots and build eval-cli and check-cli natively."""
    manifest = json.loads((HERE / 'oracles/manifest.json').read_text())
    built = {}
    for lane, entry in manifest.items():
        raw = (ROOT / entry['archive']).read_bytes()
        require(sha(raw) == entry['sha256'], f'{lane} archive digest')
        files = json.loads(gzip.decompress(raw))
        require({p: sha(t.encode()) for p, t in files.items()} == entry['files'], f'{lane} snapshot files')
        tree = BUILD / 'oracles' / lane
        for path, text in files.items():
            target = tree / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.read_text() != text:
                target.write_text(text)
        built[lane] = {'tree': tree, 'commit': entry['commit'], 'files': files}

    def build(job):
        lane, tool = job
        out = BUILD / f'{lane}-{tool}'
        result = run([SEED, built[lane]['tree'] / f'src/{tool}-cli.bend', '-o', out], 900)
        require(result['exit'] == 0 and out.exists(), (lane, tool, result))
        return lane, tool, out

    with ThreadPoolExecutor(max_workers=4) as pool:
        for lane, tool, out in pool.map(build, [(l, t) for l in built for t in ('eval', 'check')]):
            built[lane][tool] = out
    return built


def lane_prefix(case):
    return ['--bundle', '.'] if case['lane'] == 'literals' else []


def eval_argv(case, built):
    return [built[case['lane']]['eval'], *lane_prefix(case), case['source'], 'main', EVAL_BUDGET]


def seed_observation(case, source=None):
    source = source or case['source']
    if case.get('seed_lane') == 'native':
        out = BUILD / 'native' / case['name']
        out.parent.mkdir(parents=True, exist_ok=True)
        built = run([SEED, source, '-o', out], 900)
        require(built['exit'] == 0, (case['name'], built))
        return run([out], 120)
    return run([SEED, source], 120)


def lanes(case, built):
    return {'seed': observed(seed_observation(case)),
            'eval': observed(run(eval_argv(case, built), 120))}


# ------------------------------------------------------------------ registry

def derived_prims(snapshot: dict) -> list:
    text = snapshot['src/primitive.bend']

    def table(fn):
        body = text.split(f'def {fn}(op: O.Op)')[1].split('\ndef ')[0]
        return dict(re.findall(r'case O\.(\w+)\{\}: (.+)', body))

    name, code, inputs, qs, out = (table(f) for f in ('name', 'code', 'inputs', 'quantities', 'output'))
    order = re.findall(r'^  (\w+)\{\}$', snapshot['src/primitive-op.bend'], re.M)
    rows = []
    for i, op in enumerate(order):
        require(int(code[op]) == i, f'prim code order {op}')
        rows.append({'id': i, 'op': op, 'name': json.loads(name[op]), 'inputs': json.loads(inputs[op]),
                     'quantities': json.loads(qs[op]), 'output': json.loads(out[op])})
    return rows


def check_registry(registry: dict, built: dict) -> dict:
    rows = derived_prims(built['literals']['files'])
    require(registry['prims'][:len(rows)] == rows, 'registry prims differ from the literals derivation')
    extra = registry['prims'][len(rows):]
    require([p['id'] for p in registry['prims']] == list(range(len(registry['prims']))), 'prim ids')
    require(all(p.get('status') == 'reserved' for p in extra), 'unwitnessed prims must stay reserved')
    names = [p['name'] for p in registry['prims']]
    require(len(set(names)) == len(names) and names.index('U32.not') == 5, 'prim names')
    base = ROOT / registry['base']['path']
    require(sha(base.read_bytes()) == registry['base']['sha256'], 'pinned Base digest')
    for row in registry['foreign']:
        for path, digest in row['bodies'].items():
            if path.startswith('effs/'):
                require(sha((base.parent / path).read_bytes()) == digest, f'foreign body {path}')
    require([f['id'] for f in registry['foreign']] == list(range(len(registry['foreign']))), 'foreign ids')
    require(tuple(registry['representations']) == codec.REPRESENTATIONS, 'representation order')
    return {'prims': len(registry['prims']), 'derived': len(rows), 'reserved': len(extra),
            'foreign': len(registry['foreign'])}


# ------------------------------------------------------------------ display cross-check

class Display:
    """Reads the oracle check-cli's canonical core display (checked-display.bend)."""

    def __init__(self, text):
        self.s, self.i = text, 0

    def peek(self, token):
        return self.s.startswith(token, self.i)

    def take(self, token):
        require(self.peek(token), f'display: expected {token!r} at {self.s[self.i:self.i + 30]!r}')
        self.i += len(token)

    def number(self):
        m = re.compile(r'\d+').match(self.s, self.i)
        require(m, f'display: number at {self.s[self.i:self.i + 30]!r}')
        self.i = m.end()
        return int(m[0])

    def binder(self):
        q = self.number()
        self.take(' $')
        level = self.number()
        self.take(':')
        return q, level, self.number()

    def items(self, close, item):
        out = []
        while not self.peek(close):
            out.append(item())
            if self.peek(';'):
                self.take(';')
        self.take(close)
        return out

    def term(self):
        if self.peek('let'):
            self.take('let')
            q, level, t = self.binder()
            self.take('=')
            value = self.term()
            self.take(' in ')
            return ('let', q, level, t, value, self.term())
        if self.peek('case $'):
            self.take('case $')
            level = self.number()
            self.take(' [')
            return ('case', level, self.items(']', self.arm))
        if self.peek('close'):
            self.take('close')
            self.number()
            self.take(':')
            t = self.number()
            self.take('[')
            captures = self.items(']', self.binder)
            self.take(' ')
            q = self.number()
            self.take(' $')
            level = self.number()
            self.take('=>')
            return ('closure', t, captures, q, level, self.term())
        if self.peek('apply'):
            self.take('apply')
            t = self.number()
            self.take('(')
            return ('invoke', t, self.items(')', self.term))
        if self.peek('call'):
            self.take('call')
            index = self.number()
            self.take('(')
            return ('call', index, self.items(')', self.term))
        if self.peek('$'):
            self.take('$')
            level = self.number()
            self.take(':')
            return ('ref', level, self.number())
        if self.peek('v'):
            self.take('v')
            t = self.number()
            self.take('.')
            tag = self.number()
            if self.peek('{'):
                self.take('{')
                return ('con', t, tag, self.items('}', self.term))
            return ('value', t, tag)
        if self.peek('"'):
            end = self.i + 1
            while self.s[end] != '"':
                end += 2 if self.s[end] == '\\' else 1
            raw, self.i = self.s[self.i + 1:end], end + 1
            return ('string', unescape(raw))
        m = re.compile(r'(\d+)n').match(self.s, self.i)
        if m:
            self.i = m.end()
            return ('nat', int(m[1]))
        m = re.compile(r'[A-Za-z0-9_.]+\(').match(self.s, self.i)
        require(m, f'display: term at {self.s[self.i:self.i + 30]!r}')
        self.i = m.end()
        return ('prim', m[0][:-1], self.items(')', self.term))

    def arm(self):
        if self.peek('_=>'):
            self.take('_=>')
            return ('default', self.term())
        key = self.number()
        binders = []
        if self.peek('('):
            self.take('(')
            binders = self.items(')', self.binder)
        self.take('=>')
        return ('branch', key, binders, self.term())


def unescape(raw: str) -> str:
    table = {'0': '\0', 'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', '"': '"', "'": "'"}
    out, i = [], 0
    while i < len(raw):
        if raw[i] == '\\':
            require(raw[i + 1] in table, f'display escape {raw[i:i + 2]!r}')
            out.append(table[raw[i + 1]])
            i += 2
        else:
            out.append(raw[i])
            i += 1
    return ''.join(out)


def erased_fields(source: str) -> dict:
    """Constructor name -> field quantities, from the golden's own declarations."""
    table = {}
    for name, fields in re.findall(r'^  (\w+)\{([^}]*)\}$', source, re.M):
        table[name] = [0 if f.strip().startswith('-') else 1 for f in fields.split(',') if f.strip()]
    return table


def from_display(text: str, plan: dict, source: str, registry: dict) -> list:
    """An independent erasure and slot projection of Knot's own checked core."""
    lines = [l for l in text.splitlines() if l and l != 'Checked']
    plan_types, rep = plan['types'], plan.get('representation', {})
    scalar = {rep.get('U32'): 'U32', rep.get('Char'): 'Char'}
    prim_ids = {p['name']: p['id'] for p in registry['prims']}
    quantities = erased_fields(source)
    headers = []
    for line in lines:
        m = re.fullmatch(r'([^(]+)\(([^)]*)\)->(\d+)=(.*)', line)
        require(m, f'display line {line!r}')
        params = [tuple(map(int, p.split(':'))) for p in m[2].split(',') if p]
        headers.append((m[1], params, int(m[3]), m[4]))

    def ctor_quantities(t, tag):
        name = plan_types[t]['constructors'][tag]['name']
        return quantities.get(name, [1] * len(plan_types[t]['constructors'][tag]['fields']))

    def lower(term, scope, depth, deepest):
        """scope: level -> (slot or None, type). Returns (node, deepest)."""
        kind = term[0]
        if kind == 'value':
            _, t, tag = term
            if t in scalar:
                return ['lit', t, scalar[t], tag], deepest
            return ['value', t, tag], deepest
        if kind == 'con':
            _, t, tag, args = term
            kids = []
            for q, a in zip(ctor_quantities(t, tag), args):
                if q:
                    node, deepest = lower(a, scope, depth, deepest)
                    kids.append(node)
            return ['con', t, tag, kids], deepest
        if kind == 'ref':
            slot, t = scope[term[1]]
            require(slot is not None, 'display: reference to an erased binder')
            return ['ref', t, slot], deepest
        if kind == 'nat':
            return ['lit', rep['Nat'], 'Nat', term[1]], deepest
        if kind == 'string':
            return ['lit', rep['String'], 'String', term[1]], deepest
        if kind == 'call':
            _, index, args = term
            _, params, result, _ = headers[index]
            kids = []
            for (q, _), a in zip(params, args):
                if q:
                    node, deepest = lower(a, scope, depth, deepest)
                    kids.append(node)
            return ['call', result, index, kids], deepest
        if kind == 'prim':
            kids = []
            for a in term[2]:
                node, deepest = lower(a, scope, depth, deepest)
                kids.append(node)
            return ['prim', None, prim_ids[term[1]], kids], deepest
        if kind == 'let':
            _, q, level, t, value, body = term
            if not q:
                return lower(body, {**scope, level: (None, t)}, depth, deepest)
            v, deepest = lower(value, scope, depth, deepest)
            b, deepest = lower(body, {**scope, level: (depth, t)}, depth + 1, max(deepest, depth + 1))
            return ['let', b[1], depth, v, b], deepest
        if kind == 'case':
            _, level, arms = term
            slot, scrutinee = scope[level]
            data = plan_types[scrutinee]['kind'] == 'data' and scrutinee not in scalar
            rows, default, seen, result = {}, None, set(), None
            for arm in arms:
                if arm[0] == 'default':
                    if default is None:
                        body, deepest = lower(arm[1], scope, depth, deepest)
                        default, result = ['default', body], body[1]
                    break
                _, key, binders, body_term = arm
                if key in seen:
                    continue
                seen.add(key)
                inner, at = dict(scope), depth
                for q, lv, t in binders:
                    inner[lv] = (at, t) if q else (None, t)
                    at += 1 if q else 0
                body, deepest = lower(body_term, inner, at, max(deepest, at))
                rows[key] = ['branch', key, depth, at - depth, body]
                result = body[1]
            if data:
                count = len(plan_types[scrutinee]['constructors'])
                table = [rows.get(tag) for tag in range(count)]
                if all(r is not None for r in table):
                    default = None
                return ['case', result, slot, scrutinee, 'tags', table, default], deepest
            return ['case', result, slot, scrutinee, 'keys', [rows[k] for k in sorted(rows)], default], deepest
        if kind == 'closure':
            _, t, captures, q, level, body_term = term
            slots = sorted(scope[lv][0] for _, lv, _ in captures)
            inner = {lv: (slots.index(scope[lv][0]), ty) for _, lv, ty in captures}
            n = len(slots) + (1 if q else 0)
            inner[level] = (len(slots), plan_types[t]['domain']) if q else (None, None)
            body, inner_deepest = lower(body_term, inner, n, n)
            return ['closure', t, 1 if q else 0, inner_deepest, slots, body], deepest
        if kind == 'invoke':
            _, t, args = term
            f, deepest = lower(args[0], scope, depth, deepest)
            kids = []
            for a in args[1:] if plan_types[t]['kind'] == 'arrow' else []:
                node, deepest = lower(a, scope, depth, deepest)
                kids.append(node)
            return ['invoke', plan_types[t]['result'], f, kids], deepest
        raise AssertionError(f'display: {kind}')

    functions = []
    for name, params, result, body_text in headers:
        reader = Display(body_text)
        term = reader.term()
        require(reader.i == len(body_text), f'display: trailing text in {name}')
        scope, slot = {}, 0
        for level, (q, t) in enumerate(params):
            scope[level] = (slot, t) if q else (None, t)
            slot += 1 if q else 0
        body, deepest = lower(term, scope, slot, slot)
        if body[0] == 'prim':
            body[1] = result
        functions.append({'name': name, 'parameters': [t for q, t in params if q], 'result': result,
                          'slots': deepest, 'body': body})
    return functions


# ------------------------------------------------------------------ images

def check_declarations(plan: dict, source: str):
    """The source's own datatypes: names, constructor order and live field counts."""
    pinned = set(plan.get('representation', {}).values())
    declared = re.findall(r'^type (\w+) is Data:\n((?:  \w+\{[^}]*\}\n)+)', source, re.M)
    fields = erased_fields(source)
    for t in (t for i, t in enumerate(plan['types']) if t['kind'] == 'data' and i not in pinned):
        ctors = next((re.findall(r'^  (\w+)\{', block, re.M) for n, block in declared if n == t['name']), None)
        require(ctors == [c['name'] for c in t['constructors']], f"type {t['name']} constructors")
        for c in t['constructors']:
            require(sum(fields[c['name']]) == len(c['fields']), f"constructor {c['name']} live fields")


def result_view(plan: dict, stdout: str):
    """(type, tag, constructor name) of a Book result line printed by eval-cli."""
    m = re.fullmatch(r'Evaluated\t(\d+)\t(\d+)\t(.*)\n', stdout)
    require(m, f'not an Evaluated line: {stdout!r}')
    t, tag, tree = int(m[1]), int(m[2]), m[3]
    main = next(f for f in plan['functions'] if f['name'] == 'main')
    require(main['result'] == t, f'image main result type {main["result"]}, eval type-id {t}')
    ctor = plan['types'][t]['constructors'][tag]['name']
    require(tree.startswith(ctor + '{'), f'eval tree {tree!r} is not constructor {ctor}')
    return t, tag, tree


def vm_expectation(case, plan, bounds) -> dict:
    """The Exhausted-lane rule, applied to the frozen observations of one golden."""
    seed, ev = case['seed'], case['eval']
    fuel = VM_FUEL
    if plan['entry'] == 'program':
        require(seed['exit'] == 0, 'program seed must succeed')
        return {'argv': ['IMAGE', str(fuel), '--'], 'exit': 0, 'stdout': seed['stdout'], 'stderr': '',
                'basis': 'seed', 'eval_lane': classify(ev)}
    if case['name'] in bounds:
        bound = bounds[case['name']]
        return {'argv': ['IMAGE', 'main', str(fuel)], 'outcome': 'Exhausted', 'kind': bound['kind'],
                'cause': bound['cause'], 'basis': 'bound', 'reason': bound['basis'], 'eval_lane': classify(ev)}
    require(seed['exit'] == 0, f"{case['name']}: the seed must succeed")
    if ev['exit'] == 0:
        result_view(plan, ev['stdout'])
        return {'argv': ['IMAGE', 'main', str(fuel)], 'exit': 0, 'stdout': ev['stdout'], 'stderr': '',
                'basis': 'eval-cli', 'eval_lane': 'agree'}
    # The eval lane is excused only by a documented bound; the VM owes the seed's value.
    require(classify(ev) == 'Exhausted', f"{case['name']}: eval lane {ev} is not a documented bound")
    main = next(f for f in plan['functions'] if f['name'] == 'main')
    m = re.fullmatch(r'(\w+)\{\}\n', seed['stdout'])
    require(m, f"{case['name']}: only a nullary seed value can be rendered without eval-cli")
    ctors = [c['name'] for c in plan['types'][main['result']]['constructors']]
    tag = ctors.index(m[1])
    return {'argv': ['IMAGE', 'main', str(fuel)], 'exit': 0,
            'stdout': f"Evaluated\t{main['result']}\t{tag}\t{m[1]}{{}}\n", 'stderr': '',
            'basis': 'seed', 'eval_lane': 'Exhausted'}


def classify(result) -> str:
    return {0: 'agree', 2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted', 5: 'HostFailure',
            6: 'InternalFailure'}.get(result['exit'], 'other')


# ------------------------------------------------------------------ controls and mutants

def word_patch(data: bytes, index: int, value: int) -> bytes:
    return data[:4 * index] + (value & 0xFFFFFFFF).to_bytes(4, 'little') + data[4 * index + 4:]


def word(data: bytes, index: int) -> int:
    return int.from_bytes(data[4 * index:4 * index + 4], 'little')


def rejected(data: bytes, reg: dict, digest: bytes, c=None) -> str | None:
    """None when the image is admitted; otherwise the refusal, as the VM loader must classify it."""
    c = c or codec
    try:
        plan = c.decode(data, digest)
    except c.Malformed as e:
        return f'HostFailure image: {e}'
    problems = c.validate(plan, reg)
    if problems:
        return 'HostFailure image: validator: ' + problems[0]
    if c.encode(plan, digest) != data:
        return 'HostFailure image: noncanonical'
    return None


def byte_controls(images: dict, digest: bytes) -> list:
    """(label, bytes, frozen refusal prefix) for malformed and noncanonical images."""
    second, capture, hit = images['second'], images['closure-captures'], images['default-hit']
    first_node, names_at = word(second, 9) + 1, word(second, 10)
    swap = word(capture, 7) + 1                 # first function record (swap, arity 2: 8 words)
    body = word(capture, swap + 5)              # its root Let node
    oversize = b'\0' * (4 * codec.LIMITS['image_words'])
    out = [
        ('truncated', second[:-4], 'total'),
        ('bad-magic', word_patch(second, 0, 0x474D494C), 'magic'),
        ('version-2', word_patch(second, 1, 2), 'magic'),
        ('total-words', word_patch(second, 2, word(second, 2) + 1), 'total'),
        ('entry-kind', word_patch(second, 3, 2), 'header'),
        ('reserved-word', word_patch(second, 11, 1), 'header'),
        ('registry-digest', word_patch(second, 24, word(second, 24) ^ 1), 'registry digest'),
        ('section-offset', word_patch(second, 6, word(second, 6) + 1), 'section 1 offset'),
        ('record-length', word_patch(second, first_node, 1), 'section 4 record length'),
        ('trailing-word', word_patch(second + b'\0' * 4, 2, word(second, 2) + 1), 'trailing words'),
        ('opcode', word_patch(second, first_node + 1, 13), 'node record'),
        ('main-index', word_patch(second, 4, 0), 'main index'),
        ('name-utf8', word_patch(second, names_at + 3, 0xFFFFFFFF), 'name utf-8'),
        ('function-root-shared', word_patch(capture, swap + 8 + 5, body), 'function root'),
        ('child-not-record', word_patch(capture, body + 4, word(capture, body + 4) + 1), 'child offset'),
        ('child-after-parent', word_patch(capture, body + 4, body + 6), 'child after parent'),
        ('oversize', second + oversize, 'exhausted image-size'),
        ('oversize-and-bad-magic', word_patch(second, 0, 0) + oversize, 'exhausted image-size'),
        ('oversize-and-misaligned', second + oversize + b'\0', 'exhausted image-size'),
        ('unused-constant', unused_constant(hit), 'noncanonical'),
    ]
    return [(label, data, 'HostFailure image: ' + reason, '') for label, data, reason in out]


def unused_constant(image: bytes) -> bytes:
    """Decodable and valid, but not canonical: one extra U32 constant nothing uses."""
    w = [word(image, i) for i in range(len(image) // 4)]
    consts_at, nodes_at, delta = w[8], w[9], 4
    w = w[:nodes_at] + [4, 0, 1, 99] + w[nodes_at:]
    w[consts_at] += 1
    for i in (2, 9, 10):
        w[i] += delta
    nodes_at += delta
    at = w[7] + 1
    for _ in range(w[w[7]]):
        w[at + 5] += delta
        at += w[at]
    at = nodes_at + 1
    for _ in range(w[nodes_at]):
        for i in children(w, at):
            if w[i] != codec.NONE:
                w[i] += delta
        at += w[at]
    return b''.join(v.to_bytes(4, 'little') for v in w)


def children(w: list, at: int) -> list:
    """Word positions of child offsets inside the node record at `at`."""
    op, x, end = codec.OPCODES[w[at + 1]], at + 3, at + w[at]
    if op in ('prim', 'con', 'call', 'foreign'):
        return list(range(x + 2, end))
    if op == 'let':
        return [x + 1, x + 2]
    if op in ('default', 'closure', 'branch'):
        return [end - 1]
    if op == 'invoke':
        return [x] + list(range(x + 2, end))
    if op == 'case':
        rows = range(x + 4, end - 1) if w[x + 2] == 0 else range(x + 5, end - 1, 2)
        return list(rows) + [end - 1]
    return []


def plan_controls(plans: dict) -> list:
    """(label, plan, frozen validator message) for type-correct plan mutants."""
    def edit(name, path, value):
        plan = json.loads(json.dumps(plans[name]))
        target = plan
        for step in path[:-1]:
            target = target[step]
        target[path[-1]] = value
        return plan

    def body(i):
        return ['functions', i, 'body']

    def edits(name, *changes):
        plan = json.loads(json.dumps(plans[name]))
        for path, value in changes:
            target = plan
            for step in path[:-1]:
                target = target[step]
            target[path[-1]] = value
        return plan

    char_rows = plans['case-char']['functions'][0]['body'][5]
    return [
        ('ref-beyond-depth', edit('reference', [*body(0), 2], 1), 'slot 1 beyond depth 1'),
        ('let-slot', edit('let', [*body(0), 2], 1), 'let slot 1 at depth 0'),
        ('branch-first-slot', edit('second', [*body(0), 5, 0, 2], 2), 'branch binders'),
        ('branch-fields', edit('second', [*body(0), 5, 0, 3], 1), 'branch binders'),
        ('missing-tag', edit('case-on', [*body(0), 5, 1], None), 'default must cover exactly the missing tags'),
        ('redundant-default', edit('case-on', [*body(0), 6], ['default', ['value', 0, 0]]),
         'default must cover exactly the missing tags'),
        ('keys-without-default', edit('default-hit', [*body(0), 6], None), 'keys must increase strictly'),
        ('keys-descending', edit('case-char', [*body(0), 5], char_rows[::-1]), 'keys must increase strictly'),
        ('unused-capture', edit('closure-capture-on', [*body(0), 3, 5, 2], 1), 'captures are not exactly the free slots'),
        ('capture-order', edit('closure-captures', [*body(0), 3, 4], [1, 0]), 'captures must increase strictly'),
        ('closure-slots', edit('closure-id', [*body(1), 3, 0, 3], 2), 'closure slots 2, reached 1'),
        ('function-slots', edit('second', ['functions', 0, 'slots'], 2), 'slots 2, reached 3'),
        ('call-arity', edit('reference', [*body(1), 3], []), 'call arity'),
        ('call-result', edit('u32-wrap', [*body(2), 1], 1), 'call types'),
        ('construct-arity', edit('pair', [*body(0), 3], [['value', 0, 0]]), 'construct arity'),
        ('value-with-fields', edit('construct', body(0), ['value', 1, 0]), 'value is not a nullary constructor'),
        ('reference-type', edit('unpack', [*body(0), 5, 0, 4, 1], 1), 'reference type'),
        ('prim-unknown', edit('u32-zero', [*body(0), 2], 41), 'unknown prim id 41'),
        ('prim-reserved', edit('u32-wrap', [*body(0), 2], 39), 'unknown prim id 39'),
        ('prim-arity', edit('u32-not', [*body(0), 3], []), 'prim arity'),
        ('prim-result', edit('u32-zero', [*body(0), 1], 1), 'prim result is not the pinned Bool'),
        ('foreign-unknown', edit('foreign-print', [*body(0), 2], 99), 'unknown foreign id 99'),
        ('invoke-non-arrow', edit('closure-id', [*body(0), 2], ['ref', 0, 1]), 'invoke arity'),
        ('literal-kind', edit('nat-add', [*body(2), 3, 1, 2], 'U32'), 'U32 literal at a non-U32 type'),
        ('program-main-arity', edit('foreign-print', ['functions', 1, 'parameters'], [3]),
         'main must exist with no live parameters'),
        ('program-representation', edit('foreign-print', ['representation'], {'Unit': 0, 'U32': 1, 'Char': 2, 'String': 3}),
         "missing representation ['IO.OP']"),
        ('foreign-operand-type', edits('foreign-print', (['functions', 0, 'parameters'], [0]),
                                       ([*body(0), 3, 0, 1], 0)), 'foreign operand is not the pinned String'),
        ('representation-shape', edit('u32-zero', ['types', 0, 'constructors'], [{'name': 'False', 'fields': []}]),
         'Bool shape'),
    ]


# Semantic mutants of the reference codec: (name, [(old, new), ...]). Each must change a
# committed image or change a frozen refusal; a crash is never a kill.
CODEC_MUTANTS = [
    ('big-endian', [("b''.join(w.to_bytes(4, 'little') for w in header + body)",
                     "b''.join(w.to_bytes(4, 'big') for w in header + body)")]),
    ('function-names-first', [("    types, first = [], 0\n",
                               "    for f in plan['functions']:\n        name(f['name'])\n    types, first = [], 0\n")]),
    ('site-from-one', [('sites = [0]', 'sites = [1]')]),
    ('child-offset-plus-one', [("        return place[w[1]] if isinstance(w, tuple) else w",
                                "        return place[w[1]] + 1 if isinstance(w, tuple) else w")]),
    ('default-before-rows', [
        ("        elif op == 'case':\n            _, _, slot, scrutinee, mode, rows, default = node\n",
         "        elif op == 'case':\n            _, _, slot, scrutinee, mode, rows, default = node\n"
         "            fallback = NONE if default is None else ('@', emit(default, t))\n"),
        ("            fallback = NONE if default is None else ('@', emit(default, t))\n            operands",
         "            operands")]),
    ('constants-uninterned', [("        return constants.setdefault(key, len(constants))",
                               "        constants[key + (len(constants),)] = len(constants)\n        return len(constants) - 1"),
                              ("for (k, d) in constants]", "for (k, d, *_) in constants]")]),
    ('nat-constant-as-u32', [("        key = (CONSTANT_KINDS.index(kind), tuple(data))",
                              "        key = (CONSTANT_KINDS.index(kind) % 1 if kind == 'Nat' else CONSTANT_KINDS.index(kind), tuple(data))")]),
    ('string-reversed', [("        data = [ord(c) for c in value] if isinstance(value, str) else (",
                          "        data = [ord(c) for c in value[::-1]] if isinstance(value, str) else (")]),
    ('arrow-named', [("            types.append([kind, NONE, opt(t['domain']), opt(t['result'])])",
                      "            types.append([kind, 0, opt(t['domain']), opt(t['result'])])")]),
    ('decoder-skips-digest', [("    if bytes(b for x in w[24:32] for b in x.to_bytes(4, 'little')) != digest:\n"
                               "        raise Malformed('registry digest')\n", "")]),
    ('size-guard-after-shape', [("    if len(data) > LIMITS['image_words'] * 4:\n        raise Malformed('exhausted image-size')\n", ""),
                                ("        raise Malformed('length')\n",
                                 "        raise Malformed('length')\n    if len(data) > LIMITS['image_words'] * 4:\n"
                                 "        raise Malformed('exhausted image-size')\n")]),
    ('validator-ignores-let-slot', [("            if node[2] != depth:\n                fail(where, f'let slot {node[2]} at depth {depth}')\n", "")]),
    ('validator-ignores-free-captures', [("                fail(where, 'captures are not exactly the free slots of the body')\n", "                pass\n")]),
    ('validator-optional-key-default', [("                if keys != sorted(set(keys)) or default is None:",
                                         "                if keys != sorted(set(keys)):")]),
    ('validator-ignores-binders', [("                    if r[2] != depth or r[3] != len(fields):\n",
                                    "                    if r[3] != len(fields):\n")]),
    ('validator-admits-reserved-prim', [(" or table[node[2]].get('status') == 'reserved'", "")]),
    ('validator-ignores-prim-arity', [("            if len(node[3]) != arity:\n                fail(where, f'{op} arity')\n            elif",
                                       "            if False:\n                pass\n            elif")]),
    ('validator-any-literal-kind', [("            if kind_of_rep(t) != node[2]:", "            if False:")]),
    ('validator-ignores-representation', [("            fail('representation', f'{r} shape')", "            pass")]),
    ('validator-program-without-io-op', [("        missing = [r for r in ('Unit', 'String', 'IO.OP') if r not in rep]",
                                          "        missing = []")]),
    ('validator-ignores-foreign-operands', [("                for k, name in zip(node[3], table[node[2]]['inputs']):\n",
                                             "                for k, name in zip(node[3], table[node[2]]['inputs']) if op == 'prim' else []:\n")]),
]


def codec_mutants(plans, images, controls, reg, digest) -> list:
    source = CODEC.read_text()
    results = []
    for name, edits in CODEC_MUTANTS:
        text = source
        for old, new in edits:
            require(text.count(old) == 1, f'codec mutant {name} is not uniquely located')
            text = text.replace(old, new)
        mutant = load_codec(text)
        killed_by = None
        for case, plan in plans.items():
            try:
                if mutant.encode(plan, digest) != images[case]:
                    killed_by = f'image {case} differs'
                    break
            except Exception:
                continue
        for label, data, reason, message in [] if killed_by else controls:
            try:
                got = rejected(data, reg, digest, mutant)
            except Exception:
                continue
            if got is None or not got.startswith(reason) or message not in got:
                killed_by = f'control {label}: {got}'
                break
        results.append({'mutant': name, 'killed': killed_by is not None, 'by': killed_by})
    return results


SOURCE_MUTANTS = [
    ('case-on', 'flip(On{})', 'flip(Off{})'),
    ('u32-wrap', 'U32.add(4294967295,1)', 'U32.add(4294967295,2)'),
    ('closure-capture-on', 'capture(On{})', 'capture(Off{})'),
]


def source_mutants(cases, built) -> list:
    out = []
    for name, old, new in SOURCE_MUTANTS:
        case = cases[name]
        text = (ROOT / case['source']).read_text()
        require(text.count(old) == 1, f'source mutant {name}')
        path = BUILD / 'mutants' / f'{name}.bend'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text.replace(old, new))
        mutated = dict(case, source=path.relative_to(ROOT).as_posix())
        got = lanes(mutated, built)
        killed = got['seed'] != case['seed'] and got['eval'] != case['eval']
        out.append({'mutant': f'source:{name}', 'killed': killed, 'seed': got['seed'], 'eval': got['eval']})
    return out


# ------------------------------------------------------------------ bench freeze

def check_bench(built: dict, registry: dict) -> dict:
    """The speed freeze: sources unchanged, baselines recorded against those exact sources."""
    manifest = json.loads((HERE / 'bench/workloads.json').read_text())
    baselines = json.loads((HERE / 'bench/baselines.json').read_text())
    require([w['name'] for w in manifest['workloads']] == list(baselines['workloads']), 'bench workload set')
    for w in manifest['workloads']:
        require(sha((ROOT / w['source']).read_bytes()) == w['sha256'], f"bench source {w['name']}")
        row = baselines['workloads'][w['name']]
        require(row['source_sha256'] == w['sha256'], f"bench baseline source {w['name']}")
        require(row['stdout'] == w['expected_stdout'] == 'True{}\n' and row['exit'] == 0, f"bench output {w['name']}")
        require(len(row['samples']) == row['repeat'] >= 3 and row['summary']['instructions']['median'] > 0,
                f"bench samples {w['name']}")
    parse = json.loads((HERE / 'bench/parse-cli.json').read_text())
    snapshot = built['literals']['files']
    library = Path(os.environ.get('BEND_LIB', str(Path.home() / '.bend/lib'))).expanduser()
    for f in parse['files']:
        if f['origin'] == 'literals-snapshot':
            data = snapshot[f['path']].encode()
        elif f['origin'] == 'base':
            data = (ROOT / f['path']).read_bytes()
        else:
            local = f"tests/compiler-modules/bundle/lib/{f['path']}"
            data = (library / f['path']).read_bytes() if (library / f['path']).exists() else snapshot[local].encode()
        require(sha(data) == f['sha256'], f"parse-cli corpus {f['path']}")
        require(f['summary']['instructions']['median'] > 0, f"parse-cli count {f['path']}")
    require(parse['commit'] == built['literals']['commit'], 'parse-cli subject commit')
    return {'workloads': len(manifest['workloads']), 'parse_cli_files': len(parse['files'])}


# ------------------------------------------------------------------ main

def freeze(built):
    """Append observations for planned cases not yet frozen. Never rewrites a frozen row."""
    plan = json.loads((GOLDEN / 'plan.json').read_text())
    path = GOLDEN / 'expectations.json'
    frozen = json.loads(path.read_text())
    known = {c['name'] for c in frozen['cases']}
    fresh = [c for c in plan['cases'] if c['name'] not in known]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda c: lanes(c, built), fresh))
    for case, got in zip(fresh, results):
        row = dict(case)
        row['sha256'] = sha((ROOT / case['source']).read_bytes())
        row.update(got)
        frozen['cases'].append(row)
    path.write_text(json.dumps(frozen, indent=2) + '\n')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze-new', action='store_true',
                        help='observe and append planned cases that have no frozen row')
    parser.add_argument('--write-expected', action='store_true',
                        help='write vm-expected.json from the frozen observations (first freeze only)')
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    started = datetime.datetime.now(datetime.timezone.utc)
    built = oracles()
    if args.freeze_new:
        freeze(built)
        return 0

    reg = codec.registry()
    digest = codec.base_digest(reg)
    record = {'date': started.isoformat(), 'status': 'incomplete',
              'scope': 'knot-image-1 golden images and the frozen VM contract; no VM exists',
              'oracles': {lane: b['commit'] for lane, b in built.items()},
              'inputs': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in
                         sorted([*HERE.glob('*.md'), *HERE.glob('*.py'), HERE / 'registry.json',
                                 *GOLDEN.glob('*'), *(HERE / 'oracles').glob('*'), *(HERE / 'bench').glob('*')])
                         if p.is_file()}}
    record['registry'] = check_registry(reg, built)

    frozen = json.loads((GOLDEN / 'expectations.json').read_text())
    cases = {c['name']: c for c in frozen['cases']}
    planned = [c['name'] for c in json.loads((GOLDEN / 'plan.json').read_text())['cases']]
    require(sorted(planned) == sorted(cases) and len(planned) == len(cases), 'plan.json and expectations.json list the same cases')
    for c in cases.values():
        require(sha((ROOT / c['source']).read_bytes()) == c['sha256'], f"frozen source {c['name']}")

    with ThreadPoolExecutor(max_workers=4) as pool:
        fresh = dict(zip(cases, pool.map(lambda c: lanes(c, built), cases.values())))

    def display(case):
        tool = built[case['lane']]['check']
        return run([tool, *lane_prefix(case), case['source']], 120)

    with ThreadPoolExecutor(max_workers=4) as pool:
        displays = dict(zip(cases, pool.map(display, cases.values())))

    bounds = json.loads((GOLDEN / 'bounds.json').read_text())['cases']
    plans, images, fixtures, table = {}, {}, [], {}
    for name, case in cases.items():
        require(fresh[name]['seed'] == case['seed'], (name, 'seed drift', fresh[name]['seed'], case['seed']))
        require(fresh[name]['eval'] == case['eval'], (name, 'eval drift', fresh[name]['eval'], case['eval']))
        plan = json.loads((GOLDEN / f'{name}.plan.json').read_text())
        data = (GOLDEN / f'{name}.kimg').read_bytes()
        require(codec.encode(plan, digest) == data, f'{name}: committed image differs from its plan')
        require(codec.decode(data, digest) == plan, f'{name}: image does not decode to its plan')
        problems = codec.validate(plan, reg)
        require(not problems, (name, problems))
        check_declarations(plan, (ROOT / case['source']).read_text())
        shown = displays[name]
        if shown['exit'] == 0:
            derived = from_display(shown['stdout'], plan, (ROOT / case['source']).read_text(), reg)
            require(derived == plan['functions'], (name, 'plan differs from the checked core', derived))
            view = 'checked-core'
        else:
            require(plan['entry'] == 'program', f'{name}: no checked core for a Book plan')
            view = f"unavailable: {shown['stderr'].strip()}"
        table[name] = vm_expectation(case, plan, bounds)
        plans[name], images[name] = plan, data
        fixtures.append({'name': name, 'lane': case['lane'], 'seed_lane': case.get('seed_lane', 'bun'),
                         'features': case['features'], 'image_sha256': sha(data), 'words': len(data) // 4,
                         'plan_matches': view, 'seed': classify(case['seed']), 'eval': classify(case['eval']),
                         'vm': table[name]})

    expected = {'rule': 'SPEC section 9: the VM owes the seed value wherever the seed succeeds within the '
                        'declared domain and budgets; eval-cli supplies the describe text where it agrees.',
                'fuel': VM_FUEL, 'bounds': bounds, 'cases': table}
    if args.write_expected:
        EXPECTED.write_text(json.dumps(expected, indent=1) + '\n')
    require(json.loads(EXPECTED.read_text()) == expected, 'vm-expected.json differs from the rule')

    opcodes = {n[0] for p in plans.values() for n in walk(p)}
    require(opcodes == set(codec.OPCODES), f'uncovered node forms {set(codec.OPCODES) - opcodes}')
    modes = {n[4] for p in plans.values() for n in walk(p) if n[0] == 'case'}
    require(modes == set(codec.CASE_MODES), 'both case modes')
    big = [n for p in plans.values() for n in walk(p) if n[0] == 'lit' and n[2] != 'String' and n[3] >= 1 << 31]
    require(big, 'a boxed scalar constant')

    controls = byte_controls(images, digest) + [
        (f'plan:{k}', codec.encode(p, digest), 'HostFailure image: validator: ', m) for k, p, m in plan_controls(plans)]
    boundaries = []
    for label, data, reason, message in controls:
        got = rejected(data, reg, digest)
        require(got is not None and got.startswith(reason) and message in got, f'control {label}: {got}')
        boundaries.append({'control': label, 'refused': got})

    mutants = codec_mutants(plans, images, controls, reg, digest) + source_mutants(cases, built)
    survivors = [m['mutant'] for m in mutants if not m['killed']]
    require(not survivors, f'surviving mutants {survivors}')

    record['bench'] = check_bench(built, reg)
    record.update(status='passed', fixtures=fixtures, boundaries=boundaries, mutants=mutants,
                  coverage={'opcodes': sorted(opcodes), 'case_modes': sorted(modes),
                            'program_images': sum(p['entry'] == 'program' for p in plans.values())})
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(record, indent=1) + '\n')
    print(f"vm-spec passed: {len(fixtures)} golden images, {len(boundaries)} refused controls, "
          f"{len(mutants)} killed mutants; {RECEIPT.relative_to(ROOT)}")
    return 0


def walk(plan):
    stack = [f['body'] for f in plan['functions']]
    while stack:
        n = stack.pop()
        if n is None:
            continue
        yield n
        op = n[0]
        if op in ('prim', 'con', 'call', 'foreign'):
            stack += n[3]
        elif op == 'let':
            stack += [n[3], n[4]]
        elif op == 'case':
            stack += [r for r in n[5] if r is not None] + ([n[6]] if n[6] else [])
        elif op in ('branch',):
            stack.append(n[4])
        elif op == 'default':
            stack.append(n[1])
        elif op == 'closure':
            stack.append(n[5])
        elif op == 'invoke':
            stack += [n[2], *n[3]]


if __name__ == '__main__':
    sys.exit(main())
