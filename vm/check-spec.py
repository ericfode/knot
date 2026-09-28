#!/usr/bin/env python3
"""Gate vm-spec: frozen golden images against the pinned seed and eval-cli.

Re-executes the oracle lanes on every golden source and compares the frozen
observations byte for byte; re-derives the prim registry; checks that every
committed image equals its plan's encoding, decodes back to that plan, passes
the validator and agrees with the oracle checker's own core display; freezes
the VM expectation table under the Exhausted-lane rule; checks the bench
freeze; and requires every negative control and mutant to be rejected.
It implements no VM. The reference evaluation of each plan (evaluate.py, on
values, not cells) supplies a Program's own output and must reproduce every
Book expectation and run control.
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
import shlex
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
EVALUATOR = HERE / 'evaluate.py'


def load(path: Path, text: str | None = None):
    module = types.ModuleType(path.stem)
    module.__file__ = str(path)
    exec(compile(text if text is not None else path.read_text(), str(path), 'exec'), module.__dict__)
    return module


def load_codec(text: str | None = None):
    return load(CODEC, text)


codec = load_codec()
reference = load(EVALUATOR)
sys.setrecursionlimit(20_000)  # the reference evaluation recurses on the plan's nesting


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
            'stderr': p.stderr.decode('utf-8', 'replace'), 'bytes': p.stdout}


def observed(result):
    """Exit and text; a stdout that is not UTF-8 (the native lane's non-scalar output) is
    also kept exactly, as hex."""
    row = {k: result[k] for k in ('exit', 'stdout', 'stderr')}
    try:
        result.get('bytes', b'').decode('utf-8')
    except UnicodeDecodeError:
        row['stdout_hex'] = result['bytes'].hex()
    return row


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


def invoke_argv(case, built, invocation):
    """eval-cli asked for `FN BUDGET ORDINALS...`, the Book invocation of SPEC section 8. A row
    that names a `fuel` word passes it as the budget: the word the VM reads as FUEL."""
    name, *ordinals = invocation['argv']
    return [built[case['lane']]['eval'], *lane_prefix(case), case['source'], name,
            invocation.get('fuel', EVAL_BUDGET), *ordinals]


def lanes(case, built):
    got = {'seed': observed(seed_observation(case)),
           'eval': observed(run(eval_argv(case, built), 120))}
    if 'seed_bun_stderr' in case:
        # The seed's Bun lane, recorded beside a native observation; it never classifies.
        got['seed_bun'] = observed(run([SEED, case['source']], 120))
    if 'invocations' in case:
        # The seed runs only `main`; eval-cli is the oracle for every other invocation.
        got['invocations'] = [{**reviewed(i), 'eval': observed(run(invoke_argv(case, built, i), 120))}
                              for i in case['invocations']]
    return got


def reviewed(invocation) -> dict:
    """An invocation's literal review, without its observation."""
    return {k: v for k, v in invocation.items() if k != 'eval'}


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


def foreign_output(base: str, name: str) -> str:
    """The representation X of a Base foreign declaration's `IO(X)` result."""
    m = re.search(rf'^def {re.escape(name)}\([^)]*\) ->\s*IO\((.*)\):$', base, re.M)
    require(m, f'foreign declaration {name}')
    top = m[1]
    while re.search(r'<[^<>]*>', top):
        top = re.sub(r'<[^<>]*>', '', top)
    if ' & ' in top:
        return 'Sigma'
    return re.match(r'[\w.]+', top)[0]


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
                require(foreign_output(base.read_text(), row['name']) == row['output'], f"foreign output {row['name']}")
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


def unescape(raw: str) -> list:
    """A displayed String literal's Chr codes; `\\u{hex}` spells any code, surrogates included."""
    table = {'0': 0, 'n': 10, 't': 9, 'r': 13, '\\': 92, '"': 34, "'": 39}
    out, i = [], 0
    while i < len(raw):
        if raw.startswith('\\u{', i):
            end = raw.index('}', i)
            out.append(int(raw[i + 3:end], 16))
            i = end + 1
        elif raw[i] == '\\':
            require(raw[i + 1] in table, f'display escape {raw[i:i + 2]!r}')
            out.append(table[raw[i + 1]])
            i += 2
        else:
            out.append(ord(raw[i]))
            i += 1
    return out


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
    prims = {p['name']: p for p in registry['prims']}
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

    def lower(term, scope, depth, deepest, want):
        """scope: level -> (slot or None, the slot's image type, the core's type). A slot takes
        its binder's image type (a Branch field its pinned field, a Let its value's node), while
        a Case names the core's type as its scrutinee; `want` is the type of the position the
        term fills, which a Case takes as its own (SPEC section 3). Returns (node, deepest)."""
        kind = term[0]
        if kind == 'value':
            _, t, tag = term
            if t in scalar:
                return ['lit', t, scalar[t], tag], deepest
            return ['value', t, tag], deepest
        if kind == 'con':
            _, t, tag, args = term
            kids, fields = [], iter(plan_types[t]['constructors'][tag]['fields'])
            for q, a in zip(ctor_quantities(t, tag), args):
                if q:
                    node, deepest = lower(a, scope, depth, deepest, next(fields))
                    kids.append(node)
            return ['con', t, tag, kids], deepest
        if kind == 'ref':
            slot, t, _ = scope[term[1]]
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
            for (q, t), a in zip(params, args):
                if q:
                    node, deepest = lower(a, scope, depth, deepest, t)
                    kids.append(node)
            return ['call', result, index, kids], deepest
        if kind == 'prim':
            # Section 3: an Intrinsic's operand and result types are the pinned representations
            # its registry row names.
            row = prims[term[1]]
            kids = []
            for a, name in zip(term[2], row['inputs']):
                node, deepest = lower(a, scope, depth, deepest, rep.get(name))
                kids.append(node)
            return ['prim', rep.get(row['output']), row['id'], kids], deepest
        if kind == 'let':
            _, q, level, t, value, body = term
            if not q:
                return lower(body, {**scope, level: (None, t, t)}, depth, deepest, want)
            v, deepest = lower(value, scope, depth, deepest, t)
            b, deepest = lower(body, {**scope, level: (depth, v[1], t)}, depth + 1, max(deepest, depth + 1), want)
            return ['let', b[1], depth, v, b], deepest
        if kind == 'case':
            _, level, arms = term
            slot, _, scrutinee = scope[level]
            data = plan_types[scrutinee]['kind'] == 'data' and scrutinee not in scalar
            rows, default, seen = {}, None, set()
            for arm in arms:
                if arm[0] == 'default':
                    if default is None:
                        body, deepest = lower(arm[1], scope, depth, deepest, want)
                        default = ['default', body]
                    break
                _, key, binders, body_term = arm
                if key in seen:
                    continue
                seen.add(key)
                fields = plan_types[scrutinee]['constructors'][key]['fields'] if data else []
                inner, at, live_fields = dict(scope), depth, iter(fields)
                for q, lv, t in binders:
                    if q:
                        field = next(live_fields)
                        require(field is None or field == t, f'display: binder type {t}, pinned field {field}')
                        inner[lv] = (at, field, t)
                        at += 1
                    else:
                        inner[lv] = (None, t, t)
                body, deepest = lower(body_term, inner, at, max(deepest, at), want)
                rows[key] = ['branch', key, depth, at - depth, body]
            if data:
                count = len(plan_types[scrutinee]['constructors'])
                table = [rows.get(tag) for tag in range(count)]
                if all(r is not None for r in table):
                    default = None
                return ['case', want, slot, scrutinee, 'tags', table, default], deepest
            return ['case', want, slot, scrutinee, 'keys', [rows[k] for k in sorted(rows)], default], deepest
        if kind == 'closure':
            _, t, captures, q, level, body_term = term
            slots = sorted(scope[lv][0] for _, lv, _ in captures)
            inner = {lv: (slots.index(scope[lv][0]), scope[lv][1], ty) for _, lv, ty in captures}
            n = len(slots) + (1 if q else 0)
            domain = plan_types[t]['domain']
            inner[level] = (len(slots), domain, domain) if q else (None, None, None)
            body, inner_deepest = lower(body_term, inner, n, n, plan_types[t]['result'])
            return ['closure', t, 1 if q else 0, inner_deepest, slots, body], deepest
        if kind == 'invoke':
            _, t, args = term
            f, deepest = lower(args[0], scope, depth, deepest, t)
            kids = []
            for a in args[1:] if plan_types[t]['kind'] == 'arrow' else []:
                node, deepest = lower(a, scope, depth, deepest, plan_types[t]['domain'])
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
            scope[level] = (slot, t, t) if q else (None, t, t)
            slot += 1 if q else 0
        body, deepest = lower(term, scope, slot, slot, result)
        if body[0] == 'prim':
            body[1] = result
        functions.append({'name': name, 'parameters': [t for q, t in params if q], 'result': result,
                          'slots': deepest, 'body': body})
    return functions


PRINT = re.compile(r'import Base\n\ndef main\(\) -> IO\(Unit\):\n  IO\.print\((.*)\)\n')


def named(node, types, functions) -> list:
    """A subtree with each type index replaced by its type's name and each function index by
    its function's name, so two tables can be compared."""
    op, t = node[0], types[node[1]]['name']
    if op in ('lit', 'value', 'ref'):
        return [op, t, *node[2:]]
    require(op in ('con', 'prim', 'call'), f'print argument: no named view of {op}')
    head = functions[node[2]]['name'] if op == 'call' else node[2]
    return [op, t, head, [named(k, types, functions) for k in node[3]]]


def called(node, functions) -> set:
    """Names of the functions a subtree calls, transitively."""
    names, work = set(), [node]
    while work:
        n = work.pop()
        if n[0] == 'call' and functions[n[2]]['name'] not in names:
            names.add(functions[n[2]]['name'])
            work.append(functions[n[2]]['body'])
        work += n[3] if n[0] in ('con', 'prim', 'call') else []
    return names


def print_argument(name: str, source: str, plan: dict, strings: dict, built: dict, registry: dict) -> str | None:
    """A Program `main = IO.print(e)` has no checked core in the pinned heads (Invalid parse
    function-result), so `e` is checked as the Book `main() -> String`, whose type table is
    `strings` (result-string's). Its projection, and that of every Base function it calls,
    must equal the hand plan's argument and functions."""
    m = PRINT.fullmatch(source)
    if not m:
        return None
    path = BUILD / 'print' / f'{name}.bend'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'import Base\n\ndef main() -> String:\n  {m[1]}\n')
    shown = run([built['literals']['check'], '--bundle', '.', path.relative_to(ROOT)], 120)
    require(shown['exit'] == 0, (name, 'print argument not checked', shown))
    book = from_display(shown['stdout'], strings, '', registry)
    require(book[-1]['name'] == 'main', f'{name}: print argument book {[f["name"] for f in book]}')
    call = next(f for f in plan['functions'] if f['name'] == 'main')['body']
    require(call[0] == 'call' and plan['functions'][call[2]]['name'] == 'IO.print', f'{name}: main is not IO.print(e)')
    mine, theirs = (plan['types'], plan['functions']), (strings['types'], book)
    require(named(call[3][0], *mine) == named(book[-1]['body'], *theirs),
            (name, 'print argument differs from the checked core', book[-1]['body']))
    callees = called(call[3][0], plan['functions'])
    require(callees == {f['name'] for f in book[:-1]}, f'{name}: print argument calls {sorted(callees)}')

    def signature(f, types, functions):
        return ([types[p]['name'] for p in f['parameters']], types[f['result']]['name'], f['slots'],
                named(f['body'], types, functions))
    for f in book[:-1]:
        mine_f = next(g for g in plan['functions'] if g['name'] == f['name'])
        require(signature(mine_f, *mine) == signature(f, *theirs), (name, f['name'], 'differs from the checked core'))
    return 'IO.print argument: checked-core'


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


def described(printed: str, quantities: dict) -> str:
    """The seed's printed value in SPEC section 8's describe spelling: no spaces, erased
    fields dropped by the golden's own declarations, a Nat as its unary view. Section 8's
    inclusive bounds apply to the rendered tree: one visit per constructor (a Nat n costs
    n + 1) and its bytes. A value beyond them is refused; its golden declares the bound."""
    s, at = printed.removesuffix('\n'), 0
    token = re.compile(r'(\d+)n|([\w.]+)\{')

    def value() -> tuple:
        """(text, visits) of the subtree at `at`; the text is None once it cannot fit."""
        nonlocal at
        m = token.match(s, at)
        require(m, f'seed value: cannot read {s[at:at + 30]!r}')
        at = m.end()
        if m[1] is not None:
            n = int(m[1])
            return ('Succ{' * n + 'Zero{}' + '}' * n if n < reference.DISPLAY_VISITS else None), n + 1
        kids = []
        while not s.startswith('}', at):
            kids.append(value())
            if s.startswith(', ', at):
                at += 2
            else:
                require(s.startswith('}', at), f'seed value: cannot read {s[at:at + 30]!r}')
        at += 1
        live = quantities.get(m[2], [1] * len(kids))
        require(len(live) == len(kids), f'seed value: {m[2]} has {len(kids)} fields, declared {len(live)}')
        kept = [k for q, k in zip(live, kids) if q]
        visits = 1 + sum(v for _, v in kept)
        if visits > reference.DISPLAY_VISITS or any(t is None for t, _ in kept):
            return None, visits
        return m[2] + '{' + ','.join(t for t, _ in kept) + '}', visits

    tree, visits = value()
    require(at == len(s), f'seed value: trailing text {s[at:at + 30]!r}')
    require(visits <= reference.DISPLAY_VISITS, f'seed value: {visits} visits exceed the display bound')
    require(len(tree.encode()) <= reference.DISPLAY_BYTES,
            f'seed value: {len(tree.encode())} bytes exceed the display bound')
    return tree


def seed_display_controls() -> list:
    """`described` bounds the seed's printed value as the reference evaluation bounds the
    VM's (display_controls): the Nat 1,048,575 and a 16,777,214-byte name render exactly at
    the bounds, and one more visit or byte is refused."""
    out = []
    for label, printed, tree in [('visits', '1048575n', 'Succ{' * 1_048_575 + 'Zero{}' + '}' * 1_048_575),
                                 ('bytes', 'N' * 16_777_214 + '{}', 'N' * 16_777_214 + '{}')]:
        require(described(printed + '\n', {}) == tree, f'seed display at the {label} bound')
    for label, printed in [('visits', '1048576n'), ('bytes', 'N' * 16_777_215 + '{}')]:
        try:
            described(printed + '\n', {})
        except AssertionError as refusal:
            out.append({'control': f'display:seed-{label}-beyond-bound', 'refused': str(refusal)})
            continue
        raise AssertionError(f'display control seed-{label}-beyond-bound was admitted')
    return out


NON_SCALAR = 'non-scalar output'


def written(result) -> bytes:
    """The bytes a lane wrote: its stdout, or the hex kept for one that is not UTF-8."""
    return bytes.fromhex(result['stdout_hex']) if 'stdout_hex' in result else result['stdout'].encode()


def output_expectation(case, plan, evaluator=None) -> dict:
    """Section 11 and D20: a Program's own value classifies its output, never a seed lane.

    The reference evaluation of the plan yields the Strings it passes to IO.print, in order.
    The VM writes each as UTF-8 and refuses the first that holds a non-scalar Char as
    `HostFailure io abi`, before its host call. The seed lanes are recorded observations:
    the native lane must have written the whole trace in its generalized UTF-8 (which
    truncates the lead byte of a code from 2^21), and the Bun lane, which refuses a
    non-scalar Char where it is constructed, printed or not, a prefix of the VM's output."""
    ev, name, seed = evaluator or reference, case['name'], case['seed']
    require(seed['exit'] == 0, f'{name}: program seed must succeed')
    vm, native = ev.program(plan, VM_FUEL), ev.program(plan, VM_FUEL, 'native')
    require(native.get('exit') == 0 and native['stdout'] == written(seed),
            f"{name}: the plan prints {native['stdout']!r} in the seed lane's encoding; the seed wrote {written(seed)!r}")
    bun = case.get('seed_bun') if case.get('seed_lane') == 'native' else seed
    require(bun is not None, f'{name}: a native-lane Program records its Bun lane')
    require(vm['stdout'].startswith(bun['stdout'].encode()) and (bun['exit'] != 0 or vm.get('exit') == 0),
            f"{name}: the Bun lane wrote {bun['stdout']!r} (exit {bun['exit']}); the VM writes {vm['stdout']!r}")
    argv = ['IMAGE', str(VM_FUEL), '--']
    if vm.get('cause') == 'io abi':
        at, code = len(vm['prints']), next(c for c in vm['prints'][-1] if not ev.scalar(c))
        require('divergence' in case, f'{name}: print {at} holds Char {code}; D20 refuses that output, '
                                      f'so it is never seed agreement')
        require(case['divergence'] == NON_SCALAR, f"{name}: divergence {case['divergence']!r} is not D20's")
        require(case.get('vm_stdout', '').encode() == vm['stdout'] and 'vm_stdout' in case,
                f"{name}: VM output {case.get('vm_stdout')!r} is not {vm['stdout']!r}, what the earlier prints write")
        return {'argv': argv, 'outcome': 'HostFailure', 'cause': 'io abi', 'stdout': case['vm_stdout'],
                'basis': f'divergent-by-contract ({NON_SCALAR})',
                'reason': f'D20: print {at} holds Char {code}; the native lane exits 0', 'eval_lane': classify(case['eval'])}
    require(vm.get('exit') == 0, f'{name}: the reference evaluation ends {vm}')
    require('divergence' not in case, f'{name}: a {NON_SCALAR} divergence, but every printed Char is a scalar')
    return {'argv': argv, 'exit': 0, 'stdout': seed['stdout'], 'stderr': '', 'basis': 'seed',
            'eval_lane': classify(case['eval'])}


def vm_expectation(case, plan, bounds, source, evaluator=None) -> dict:
    """The Exhausted-lane rule, applied to the frozen observations of one golden."""
    seed, ev = case['seed'], case['eval']
    fuel = VM_FUEL
    require('divergence' not in case or plan['entry'] == 'program', f"{case['name']}: only a Program's output diverges")
    if plan['entry'] == 'program':
        return output_expectation(case, plan, evaluator)
    main = next(f for f in plan['functions'] if f['name'] == 'main')
    why = codec.undescribable(plan, main['result'])
    if why:
        # Section 8: Knot has no describe spelling for this result type. D4's Unsupported,
        # derived from the image before any entry; not a bound and not agreement.
        require(case['name'] not in bounds, f"{case['name']}: a bound cannot stand in for Unsupported")
        return {'argv': ['IMAGE', 'main', str(fuel)], 'outcome': 'Unsupported', 'cause': 'invoke result-type',
                'basis': 'describe-domain', 'reason': f'section 8: {why}', 'eval_lane': classify(ev)}
    if case['name'] in bounds:
        # Section 11: a bound is a declared domain or budget limit, and its outcome is Exhausted.
        bound = bounds[case['name']]
        require(sorted(bound) == ['basis', 'cause', 'kind'] and bound['kind'] in (1, 2, 3),
                f"{case['name']}: a bound is Exhausted with a kind, a cause and a basis")
        require(seed['exit'] == 0, f"{case['name']}: a bound excuses only a succeeding seed")
        return {'argv': ['IMAGE', 'main', str(fuel)], 'outcome': 'Exhausted', 'kind': bound['kind'],
                'cause': bound['cause'], 'basis': 'bound', 'reason': bound['basis'], 'eval_lane': classify(ev)}
    require(seed['exit'] == 0, f"{case['name']}: the seed must succeed")
    value = described(seed['stdout'], erased_fields(source))
    if ev['exit'] == 0:
        _, _, tree = result_view(plan, ev['stdout'])
        require(tree == value, f"{case['name']}: eval-cli prints {tree!r}, the seed {value!r}")
        return {'argv': ['IMAGE', 'main', str(fuel)], 'exit': 0, 'stdout': ev['stdout'], 'stderr': '',
                'basis': 'eval-cli', 'eval_lane': 'agree'}
    # The eval lane is excused only by a documented bound; the VM owes the seed's value.
    require(classify(ev) == 'Exhausted', f"{case['name']}: eval lane {ev} is not a documented bound")
    root = re.match(r'[\w.]+', value)[0]
    ctors = [c['name'] for c in plan['types'][main['result']]['constructors']]
    require(root in ctors, f"{case['name']}: seed root {root} is not a constructor of main's result")
    return {'argv': ['IMAGE', 'main', str(fuel)], 'exit': 0,
            'stdout': f"Evaluated\t{main['result']}\t{ctors.index(root)}\t{value}\n", 'stderr': '',
            'basis': 'seed', 'eval_lane': 'Exhausted'}


IMAGE_LOSS = ('opaque-parameter', 'erased-field')


def image_loss(plan: dict, name: str, ordinals: list, source: str) -> str | None:
    """What the image drops that eval-cli's core keeps, at the first live parameter it
    affects: eval-cli models U32 as one nullary constructor, and counts erased fields."""
    declared = erased_fields(source)
    f = next(f for f in plan['functions'] if f['name'] == name)
    for t, tag in zip(f['parameters'], ordinals):
        u = plan['types'][t] if t is not None else {}
        if u.get('kind') == 'opaque':
            return IMAGE_LOSS[0]
        ctors = u.get('constructors', [])
        if tag < len(ctors) and not ctors[tag]['fields'] and declared.get(ctors[tag]['name']):
            return IMAGE_LOSS[1]
    return None


def invocation_words(invocation) -> list:
    """The words after IMAGE for a frozen invocation row: `FN FUEL ORDINAL...`, with FUEL the
    row's own word where it names one."""
    name, *ordinals = invocation['argv']
    return [name, invocation.get('fuel', str(VM_FUEL)), *ordinals]


def invocation_label(case_name: str, invocation) -> str:
    fuel = f" (FUEL {shlex.quote(invocation['fuel'])})" if 'fuel' in invocation else ''
    return f"{case_name} {shlex.join(invocation['argv'])}{fuel}"


def invocation_expectations(case, plan, source, evaluator=None) -> list:
    """Section 8 for each frozen Book invocation: the image-derived verdict, or the entered
    function's describe line from the reference evaluation. eval-cli is the oracle; a row
    that differs from it declares the image loss that explains the difference."""
    ev, rows = evaluator or reference, []
    for i in case.get('invocations', []):
        words = invocation_words(i)
        name, ordinals = words[0], [codec.decimal(o) for o in words[2:]]
        label, observed_eval = invocation_label(case['name'], i), i['eval']
        row = {'argv': ['IMAGE', *words]}
        verdict = codec.invocation(plan, words)
        if verdict:
            outcome, cause = verdict.split(' ', 1)
            row.update(outcome=outcome, cause=cause)
            review = verdict
            agrees = observed_eval['exit'] == 5 and observed_eval['stderr'] == verdict.replace(' ', '\t') + '\n'
        else:
            got = ev.book(plan, name, ordinals, codec.decimal(words[1]))
            require(got.get('exit') == 0, f'{label}: the reference evaluation gives {got}')
            row.update(exit=0, stdout=got['stdout'], stderr='')
            review = got['stdout'].split('\t')[3].removesuffix('\n')
            agrees = observed_eval['exit'] == 0 and observed_eval['stdout'] == got['stdout']
        require(i['vm'] == review, f"{label}: literal review {i['vm']!r}, section 8 gives {review!r}")
        if verdict == 'Unsupported invoke result-type':
            # eval-cli enters it and reports InternalFailure eval result-tag (DECISIONS finding 7).
            require('divergence' not in i, f'{label}: an Unsupported result is D4\'s refusal, not a divergence')
            row['basis'] = 'describe-domain'
        elif agrees:
            require('divergence' not in i, f'{label}: declared {i.get("divergence")!r}, but eval-cli agrees')
            row['basis'] = 'eval-cli'
        else:
            loss = image_loss(plan, name, ordinals, source) if None not in ordinals else None
            require(loss is not None and i.get('divergence') == loss,
                    f'{label}: eval-cli gives {observed_eval}, section 8 {review!r}; declared {i.get("divergence")!r}, '
                    f'image loss {loss!r}')
            row['basis'] = f'divergent-by-contract ({loss})'
        row['eval_lane'] = classify(observed_eval)
        rows.append(row)
    return rows


def invocation_controls(cases: dict, plans: dict, sources: dict) -> list:
    """What the invocation rule must refuse: a review other than section 8's verdict, an
    undeclared or misnamed image loss, and a divergence where eval-cli agrees."""
    def edit(name, argv, **change):
        rows = [{**i, **change} if i['argv'] == argv.split() and 'fuel' not in i else i for i in cases[name]['invocations']]
        return name, {**cases[name], 'invocations': [{k: v for k, v in i.items() if v is not None} for i in rows]}
    out = []
    for label, (name, case) in [
            ('review-arity-first', edit('invoke-args', 'two 5', vm='HostFailure invoke argument-arity')),
            ('opaque-undeclared', edit('invoke-args', 'is_zero 0', divergence=None)),
            ('erased-field-undeclared', edit('invoke-args', 'real 0', divergence=None)),
            ('opaque-as-erased-field', edit('invoke-args', 'is_zero 0', divergence='erased-field')),
            ('divergence-where-eval-agrees', edit('invoke-args', 'two 1 0', divergence='opaque-parameter')),
            # Section 8 reads the argument words before FN, and never reduces one modulo 2^32.
            ('review-lookup-before-words', edit('invoke-words', 'absent x', vm='HostFailure invoke unknown-export')),
            ('review-wrapped-word', edit('invoke-words', 'two 4294967296 0', vm='Two{Off{},Off{}}'))]:
        try:
            invocation_expectations(case, plans[name], sources[name])
        except AssertionError as refusal:
            out.append({'control': f'invocation:{label}', 'refused': str(refusal)})
            continue
        raise AssertionError(f'invocation control {label} was admitted')
    return out


def expectation_controls(cases: dict, plans: dict, bounds: dict, sources: dict, evaluator=None) -> list:
    """What the rule must refuse: an eval lane that disagrees with the seed, a bound that is
    not Exhausted or that stands in for an Unsupported result, and a D20 classification that
    is not the program's own output."""
    def row(label, seed, ev):
        return {'name': f'control:{label}', 'seed': {'exit': 0, 'stdout': seed, 'stderr': ''},
                'eval': {'exit': 0, 'stdout': ev, 'stderr': ''}}

    def without(name, *keys):
        return {k: v for k, v in cases[name].items() if k not in keys}

    def emoji(plan):
        """print-non-scalar-wide's plan printing U+1F600, which its native bytes cannot tell apart."""
        plan = json.loads(json.dumps(plan))
        plan['functions'][1]['body'][3][0][3][0][3][0][3] = 0x1F600
        return plan
    describe_bound = {'outcome': 'HostFailure', 'cause': 'invoke scalar-result',
                      'basis': 'round 1: a Book-describe bound, which section 11 no longer admits'}
    unprinted, second = cases['non-scalar-unprinted'], cases['print-non-scalar-second']
    out = []
    for label, name, case, table, plan in [
            ('eval-disagrees', 'value-on', row('eval-disagrees', 'Off{}\n', 'Evaluated\t0\t1\tOn{}\n'), bounds, None),
            ('eval-keeps-erased-field', 'erased-construct',
             row('eval-keeps-erased-field', 'ProofBox{Off{}, On{}}\n', 'Evaluated\t1\t0\tProofBox{Off{}}\n'), bounds, None),
            ('eval-nat-binds-n', 'nat-pred',
             row('eval-nat-binds-n', '2n\n', 'Evaluated\t0\t1\tSucc{Succ{Succ{Zero{}}}}\n'), bounds, None),
            ('bound-not-exhausted', 'value-on', cases['value-on'], {**bounds, 'value-on': describe_bound}, None),
            ('bound-for-unsupported', 'result-u32', cases['result-u32'], {**bounds, 'result-u32': describe_bound}, None),
            # D20: a declared divergence exactly where the program prints a non-scalar Char.
            ('non-scalar-as-agreement', 'print-non-scalar', without('print-non-scalar', 'divergence', 'vm_stdout'), bounds, None),
            ('divergence-on-scalar-output', 'foreign-print',
             {**cases['foreign-print'], 'divergence': NON_SCALAR, 'vm_stdout': ''}, bounds, None),
            ('divergence-other-class', 'print-non-scalar', {**cases['print-non-scalar'], 'divergence': 'other'}, bounds, None),
            ('vm-writes-non-scalar', 'print-non-scalar-mid',
             {**cases['print-non-scalar-mid'], 'vm_stdout': cases['print-non-scalar-mid']['seed']['stdout']}, bounds, None),
            ('wide-code-as-agreement', 'print-non-scalar-wide',
             without('print-non-scalar-wide', 'divergence', 'vm_stdout'), bounds, None),
            # The native bytes of Chr{67237376} are those of U+1F600; the plan's value decides.
            ('wide-plan-as-u1f600', 'print-non-scalar-wide', cases['print-non-scalar-wide'], bounds,
             emoji(plans['print-non-scalar-wide'])),
            # The Bun lane refuses a non-scalar Char where it is built, printed or not.
            ('unprinted-as-divergence', 'non-scalar-unprinted',
             {**unprinted, 'divergence': NON_SCALAR, 'vm_stdout': 'a\n'}, bounds, None),
            ('second-output-from-bun', 'print-non-scalar-second', {**second, 'vm_stdout': second['seed_bun']['stdout']},
             bounds, None),
            ('native-other-bytes', 'print-non-scalar',
             {**cases['print-non-scalar'], 'seed': {**cases['print-non-scalar']['seed'], 'stdout_hex': 'efbfbd0a'}}, bounds, None),
            ('bun-beyond-vm', 'non-scalar-unprinted',
             {**unprinted, 'seed_bun': {**unprinted['seed_bun'], 'stdout': 'b\n'}}, bounds, None),
            ('native-without-bun-record', 'print-non-scalar-wide', without('print-non-scalar-wide', 'seed_bun'), bounds, None)]:
        try:
            vm_expectation(case, plan or plans[name], table, sources[name], evaluator)
        except AssertionError as refusal:
            out.append({'control': f'expectation:{label}', 'refused': str(refusal)})
            continue
        raise AssertionError(f'expectation control {label} was admitted')
    return out


def classify(result) -> str:
    return {0: 'agree', 2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted', 5: 'HostFailure',
            6: 'InternalFailure'}.get(result['exit'], 'other')


def reproduced(name: str, plan: dict, expected: dict, evaluator=None):
    """The reference evaluation reproduces a Book golden's expectation: its describe line, or
    its bound's Exhausted outcome. A result section 8 cannot describe is never entered."""
    if plan['entry'] != 'book' or expected.get('outcome') == 'Unsupported':
        return
    got = (evaluator or reference).book(plan, 'main', [], VM_FUEL)
    keys = ('exit', 'stdout') if 'exit' in expected else ('outcome', 'kind', 'cause')
    require({k: got.get(k) for k in keys} == {k: expected.get(k) for k in keys},
            f'{name}: the reference evaluation gives {got}')


def ran(plan: dict, frozen: dict, evaluator=None) -> dict:
    """A run control's outcome and call count under the reference evaluation, at its frozen
    fuel (VM_FUEL unless it names one)."""
    ev, fuel = evaluator or reference, frozen.get('fuel', VM_FUEL)
    got = ev.book(plan, 'main', [], fuel) if plan['entry'] == 'book' else ev.program(plan, fuel)
    got['fuel'] = fuel
    if isinstance(got.get('stdout'), bytes):
        # A Program's written bytes; every run control writes ASCII.
        got['stdout'] = got['stdout'].decode('utf-8', 'replace')
    if 'stdout' in got:
        # A display control freezes its multi-megabyte line by digest.
        got['stdout_sha256'] = sha(got['stdout'].encode())
    return {k: got.get(k) for k in frozen}


def run_argv(plan: dict, frozen: dict) -> list:
    """How vm-core invokes a run control (section 8)."""
    fuel = str(frozen.get('fuel', VM_FUEL))
    return ['IMAGE', 'main', fuel] if plan['entry'] == 'book' else ['IMAGE', fuel, '--']


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
    """(label, plan, frozen validator message) for type-correct plan mutants; a message of
    None marks a plan the validator MUST admit."""
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
    flag = {'kind': 'data', 'name': 'Flag', 'constructors': [{'name': 'Off', 'fields': []}, {'name': 'On', 'fields': []}]}

    def flag_rows(depth):
        """A tag table over a Flag at type index 1 answering its own value."""
        return [['branch', 0, depth, 0, ['value', 1, 0]], ['branch', 1, depth, 0, ['value', 1, 1]]]

    def none_parameter(scrutinee):
        """pred(x: none) cases on x at `scrutinee`; main passes it a Nat."""
        return edits('nat-unpack', (['functions', 0, 'parameters'], [None]), (['functions', 0, 'slots'], 1),
                     ([*body(0), 3], scrutinee), ([*body(0), 5], flag_rows(1)),
                     (body(1), ['call', 1, 0, [['lit', 0, 'Nat', 7]]]))

    def none_let(scrutinee):
        """pred lets a none-typed call result and cases on it at `scrutinee`."""
        return edits('nat-unpack', (['functions'], [
            {'name': 'seven', 'parameters': [], 'result': 0, 'slots': 0, 'body': ['lit', 0, 'Nat', 7]},
            {'name': 'pred', 'parameters': [], 'result': 1, 'slots': 1,
             'body': ['let', 1, 0, ['call', None, 0, []], ['case', 1, 0, scrutinee, 'tags', flag_rows(1), None]]},
            {'name': 'main', 'parameters': [], 'result': 1, 'slots': 0, 'body': ['call', 1, 1, []]}]))

    def answer(tag, depth):
        return ['branch', tag, depth, 0, ['value', 0, tag]]
    # S's shape (catalog.bend's `case Con{+head,+tail}: match head: ...`): first_on(xs: List<Flag>)
    # matches the head bound from List's pinned `none` field at Flag. The seed prints True{}.
    list_head_match = {
        'entry': 'book', 'representation': {'Bool': 0, 'List': 1},
        'types': [plans['u32-zero']['types'][0],
                  {'kind': 'data', 'name': 'List', 'constructors': [{'name': 'Nil', 'fields': []},
                                                                    {'name': 'Con', 'fields': [None, 1]}]},
                  flag],
        'functions': [
            {'name': 'first_on', 'parameters': [1], 'result': 0, 'slots': 3,
             'body': ['case', 0, 0, 1, 'tags', [answer(0, 1), ['branch', 1, 1, 2, [
                 'case', 0, 1, 2, 'tags', [answer(0, 3), answer(1, 3)], None]]], None]},
            {'name': 'main', 'parameters': [], 'result': 0, 'slots': 0,
             'body': ['call', 0, 0, [['con', 1, 1, [['value', 2, 1], ['value', 1, 0]]]]]}]}

    def key_arms(case_type):
        """pick(x: none, k: U32) -> U32 answers the `none` x from both a key Branch (k = 0) and
        the Default: `U32.is_eq(pick(7,0),7)`. Each arm body fits the U32 Case."""
        return {
            'entry': 'book', 'representation': {'Bool': 0, 'U32': 1},
            'types': [plans['u32-zero']['types'][0], {'kind': 'opaque', 'name': 'U32'}],
            'functions': [
                {'name': 'U32.is_eq', 'parameters': [1, 1], 'result': 0, 'slots': 2,
                 'body': ['prim', 0, 8, [['ref', 1, 0], ['ref', 1, 1]]]},
                {'name': 'pick', 'parameters': [None, 1], 'result': 1, 'slots': 2,
                 'body': ['case', case_type, 1, 1, 'keys', [['branch', 0, 2, 0, ['ref', None, 0]]],
                          ['default', ['ref', None, 0]]]},
                {'name': 'main', 'parameters': [], 'result': 0, 'slots': 0, 'body': ['call', 0, 0, [
                    ['call', 1, 1, [['lit', 1, 'U32', 7], ['lit', 1, 'U32', 0]]], ['lit', 1, 'U32', 7]]]}]}

    def first_code(nil, case_type=1):
        """S's literal.bend `first_code(codes: List<U32>) -> U32` (Nil: 0, Con: the head), called
        as `U32.is_eq(first_code(Con{7,Nil{}}),7)`; the seed prints True{}. The Case takes its
        position's type, U32, and the Con arm returns the head, pinned `none` (SPEC section 3)."""
        return {
            'entry': 'book', 'representation': {'Bool': 0, 'U32': 1, 'List': 2},
            'types': [plans['u32-zero']['types'][0], {'kind': 'opaque', 'name': 'U32'},
                      {'kind': 'data', 'name': 'List', 'constructors': [{'name': 'Nil', 'fields': []},
                                                                        {'name': 'Con', 'fields': [None, 2]}]}],
            'functions': [
                {'name': 'U32.is_eq', 'parameters': [1, 1], 'result': 0, 'slots': 2,
                 'body': ['prim', 0, 8, [['ref', 1, 0], ['ref', 1, 1]]]},
                {'name': 'first_code', 'parameters': [2], 'result': 1, 'slots': 3,
                 'body': ['case', case_type, 0, 2, 'tags', [['branch', 0, 1, 0, nil], ['branch', 1, 1, 2, ['ref', None, 1]]], None]},
                {'name': 'main', 'parameters': [], 'result': 0, 'slots': 0, 'body': ['call', 0, 0, [
                    ['call', 1, 1, [['con', 2, 1, [['lit', 1, 'U32', 7], ['value', 2, 0]]]]], ['lit', 1, 'U32', 7]]]}]}
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
        # Type rules at inspection points and pinned representations (review round 1).
        ('key-body-type', edit('case-char', [*body(0), 5, 0, 4], ['lit', 0, 'U32', 7]), 'key branch body type'),
        ('default-body-type', edit('case-char', [*body(0), 6, 1], ['lit', 0, 'U32', 7]), 'default body type'),
        ('prim-on-flags', edit('value-on', body(0), ['prim', 0, 8, [['value', 0, 0], ['value', 0, 1]]]),
         'prim operand is not the pinned U32'),
        ('nat-add-of-flags', edit('value-on', body(0), ['prim', 0, 22, [['value', 0, 1], ['value', 0, 1]]]),
         'prim operand is not the pinned Nat'),
        ('prim-result-undeclared', edit('u32-zero', ['representation'], {'U32': 1}), 'prim result is not the pinned Bool'),
        ('foreign-on-flag', edit('value-on', body(0), ['foreign', 0, 1, [['value', 0, 1]]]),
         'foreign operand is not the pinned String'),
        ('foreign-result', edits('foreign-print', (['entry'], 'book'), (['types'], plans['foreign-print']['types'] + [flag]),
                                 (['functions', 0, 'result'], 8), ([*body(0), 1], 8),
                                 (['functions', 1, 'result'], 8), ([*body(1), 1], 8)),
         'foreign result is not IO(Unit)'),
        ('program-main-unit', edit('foreign-print', ['functions', 1],
                                   {'name': 'main', 'parameters': [], 'result': 0, 'slots': 0, 'body': ['value', 0, 0]}),
         'main must return IO(Unit)'),
        # A Case names a concrete scrutinee type, even when its slot is an erased position.
        ('inspect-none-parameter', none_parameter(None), 'case scrutinee type'),
        ('inspect-none-let', none_let(None), 'case scrutinee type'),
        ('case-none-parameter', none_parameter(1), None),
        ('case-none-let', none_let(1), None),
        ('list-head-match', list_head_match, None),
        # An arm body fits its Case: a concrete Nil arm beside the `none` head (review round 5).
        ('first-code', first_code(['lit', 1, 'U32', 0]), None),
        ('branch-body-type', first_code(['value', 0, 0]), 'branch body type'),
        # Positional typing makes plans canonical; validation checks only fit, so a `none`
        # Case in the U32 body is admitted too.
        ('first-code-none-case', first_code(['lit', 1, 'U32', 0], None), None),
        ('key-arms-none', key_arms(1), None),
        ('nat-field-type', edits('nat-unpack', (['types', 0, 'constructors', 1, 'fields'], [1]),
                                 ([*body(0), 5, 1], ['branch', 1, 1, 1, ['case', 1, 1, 1, 'tags', flag_rows(2), None]]),
                                 (['functions', 0, 'slots'], 2)),
         'Nat shape'),
        ('reference-none-view', edit('reference', [*body(0), 1], None), 'reference type'),
        ('arrow-cycle', edit('closure-id', ['types', 1, 'domain'], 1), 'arrow cycle'),
    ]


# first_code as the literals head's check-cli would display it: type 0 Bool, 1 U32, 2 List;
# the Con head binder `1 $1:1` carries the core's instantiated U32. No pinned head checks a
# List<U32> parameter (`Unsupported parse parameter-type`), so the text is written by hand.
FIRST_CODE_DISPLAY = """Checked
U32.is_eq(1:1,1:1)->0=U32.is_eq($0:1;$1:1)
first_code(1:2)->1=case $0 [0=>v1.0;1(1 $1:1;1 $2:2;)=>$1:1]
main()->0=call0(call1(v2.1{v1.7;v2.0});v1.7)
"""


def lowered_controls(planned: list, reg: dict) -> list:
    """The display cross-check follows section 3's typing: a Branch slot takes the pinned
    field (`none`), not the core binder's U32, and a Case takes its position's type, not
    its last arm's. The lowering of FIRST_CODE_DISPLAY is the admitted plan `first-code`."""
    plan = next(p for label, p, _ in planned if label == 'first-code')
    derived = from_display(FIRST_CODE_DISPLAY, plan, '', reg)
    require(derived == plan['functions'], ('first-code: lowering differs from the admitted plan', derived))
    return ['first-code']


ILL_TYPED = {'outcome': 'HostFailure', 'cause': 'image ill-typed'}


def run_controls(plans: dict) -> list:
    """(label, plan, frozen run) for images the validator MUST admit and the VM MUST run to
    the frozen outcome, by literal review of section 7: `calls` counts successful debits.
    A generic function instantiated at an arrow type returns a `none`-typed value into an
    arrow-typed node (section 3), so `none` fits either arrow kind, and an identity can
    launder an arrow of the other kind into an Invoke or a Program phase, or the terminal
    continuation into an erased Invoke; section 7's operand check refuses each Enter before
    its debit."""
    flag = plans['value-on']['types'][0]
    live, erased = {'kind': 'arrow', 'domain': 0, 'result': 0}, {'kind': 'erased-arrow', 'domain': None, 'result': 0}
    ident = {'name': 'id', 'parameters': [None], 'result': None, 'slots': 1, 'body': ['ref', None, 0]}

    def book(body):
        return {'entry': 'book', 'types': [flag, live, erased],
                'functions': [ident, {'name': 'main', 'parameters': [], 'result': 0, 'slots': 0, 'body': body}]}

    def program(body):
        """foreign-print's types: 4 IO.OP, 5 Unit -> IO.OP, 6 (5) -> IO.OP, 7 IO(Unit); 8 is
        an erased arrow to IO.OP."""
        fp = plans['foreign-print']
        return {'entry': 'program', 'representation': fp['representation'],
                'types': fp['types'] + [{'kind': 'erased-arrow', 'domain': None, 'result': 4}],
                'functions': [ident, {'name': 'main', 'parameters': [], 'result': 7, 'slots': 0, 'body': body}]}
    halt = ['closure', 8, 0, 0, [], ['con', 4, 1, [['lit', 1, 'U32', 0], ['value', 3, 0]]]]
    controls = [
        ('arrow-through-identity',
         book(['invoke', 0, ['call', 1, 0, [['closure', 1, 1, 1, [], ['ref', 0, 0]]]], [['value', 0, 1]]]),
         {'exit': 0, 'stdout': 'Evaluated\t0\t1\tOn{}\n', 'calls': 3}),
        ('erased-closure-invoked-live',
         book(['invoke', 0, ['call', 1, 0, [['closure', 2, 0, 0, [], ['value', 0, 1]]]], [['value', 0, 0]]]),
         {**ILL_TYPED, 'calls': 2}),
        ('live-closure-invoked-erased',
         book(['invoke', 0, ['call', 2, 0, [['closure', 1, 1, 1, [], ['ref', 0, 0]]]], []]),
         {**ILL_TYPED, 'calls': 2}),
        ('terminal-invoked-erased',
         program(['closure', 7, 0, 0, [], ['closure', 6, 1, 1, [], ['invoke', 4, ['call', 8, 0, [['ref', 5, 0]]], []]]]),
         {**ILL_TYPED, 'calls': 4}),
        # Program phases 1 and 2 enter main's value through the same check.
        ('phase-one-live',
         program(['call', 7, 0, [['closure', 6, 1, 1, [], ['invoke', 4, ['ref', 5, 0], [['value', 0, 0]]]]]]),
         {**ILL_TYPED, 'calls': 2}),
        ('phase-two-erased', program(['closure', 7, 0, 0, [], ['call', 6, 0, [halt]]]), {**ILL_TYPED, 'calls': 3}),
        # U32 and File, the one representation pair without a pinned shape, may name one
        # opaque type; the run is ordinary.
        ('u32-file-alias',
         {'entry': 'book', 'representation': {'U32': 1, 'File': 1}, 'types': [flag, {'kind': 'opaque', 'name': 'U32'}],
          'functions': [{'name': 'main', 'parameters': [], 'result': 0, 'slots': 1,
                         'body': ['let', 0, 0, ['lit', 1, 'U32', 7], ['value', 0, 0]]}]},
         {'exit': 0, 'stdout': 'Evaluated\t0\t0\tOff{}\n', 'calls': 1}),
        # Section 6.1: a Nat Case makes the predecessor only for a selected Succ Branch. Its
        # Default on 2^31 + 1 is On{}; a VM that made the Big predecessor 2^31 first would
        # leak it, which vm-model's RC audit sees and this value does not.
        ('nat-default-big',
         {'entry': 'book', 'representation': {'Nat': 0},
          'types': [plans['nat-pred']['types'][0], flag],
          'functions': [{'name': 'main', 'parameters': [], 'result': 1, 'slots': 1,
                         'body': ['let', 1, 0, ['lit', 0, 'Nat', 2147483649],
                                  ['case', 1, 0, 0, 'tags', [['branch', 0, 1, 0, ['value', 1, 0]], None],
                                   ['default', ['value', 1, 1]]]]}]},
         {'exit': 0, 'stdout': 'Evaluated\t1\t1\tOn{}\n', 'calls': 1}),
    ]
    return [*controls, *display_controls(), *fuel_controls({**plans, **{label: p for label, p, _ in controls}})]


def fuel_controls(plans: dict) -> list:
    """Section 7's fuel boundary, by literal review of golden plans and two controls above:
    `calls` counts successful debits, so a run completes with fuel equal to its calls, and
    one unit less stops its last entry with Exhausted kind 1 after one call fewer.
    - recursion-map enters main, flip_all(Push{On{},Push{Off{},Stop{}}}), flip(On{}),
      flip_all(Push{Off{},Stop{}}), flip(Off{}) and flip_all(Stop{}): 6 Applications.
    - closure-nested enters main, keep(On{}), the closure keep returns and the closure that
      one returns: at 3 the last Invoke stops.
    - foreign-print enters main, IO.print, the Action applied to the erased R (phase 1),
      the Action applied to k (phase 2), which writes `vm\n`, and the terminal continuation
      k: at 4 the output is written and k's entry stops; at 3 the Action's second
      application stops before its effect, so nothing is written.
    - At fuel 0 the first entry stops: nothing is entered, written or counted.
    - The third Enter of erased-closure-invoked-live, and phase-one-live's phase 1, are
      ill-typed. At fuel 2 each meets fuel 0, and the operand check still refuses it first."""
    def at(fuel, outcome, calls, **more):
        return {'fuel': fuel, **outcome, **more, 'calls': calls}
    fuel = {'outcome': 'Exhausted', 'kind': 1, 'cause': 'fuel'}
    flags, closed, printed = plans['recursion-map'], plans['closure-nested'], plans['foreign-print']
    return [
        ('fuel-book-exact', flags, at(6, {'exit': 0}, 6, stdout='Evaluated\t1\t1\tPush{Off{},Push{On{},Stop{}}}\n')),
        ('fuel-book-short', flags, at(5, fuel, 5)),
        ('fuel-invoke-exact', closed, at(4, {'exit': 0}, 4, stdout='Evaluated\t0\t1\tOn{}\n')),
        ('fuel-invoke-short', closed, at(3, fuel, 3)),
        ('fuel-program-exact', printed, at(5, {'exit': 0}, 5, stdout='vm\n')),
        ('fuel-continuation-short', printed, at(4, fuel, 4, stdout='vm\n')),
        ('fuel-action-short', printed, at(3, fuel, 3, stdout='')),
        ('fuel-zero-book', flags, at(0, fuel, 0)),
        ('fuel-zero-program', printed, at(0, fuel, 0, stdout='')),
        ('fuel-zero-ill-typed-invoke', plans['erased-closure-invoked-live'], at(2, ILL_TYPED, 2)),
        ('fuel-zero-ill-typed-phase', plans['phase-one-live'], at(2, ILL_TYPED, 2)),
    ]


def display_controls() -> list:
    """Section 8's inclusive display bounds, each met exactly and then passed by one step, on
    Book results built from Nat literals (one call each). A visit is one rendered constructor,
    so the Nat word n costs n + 1: 1,048,575 renders and 1,048,576 is Exhausted. The text
    bound counts the tree's bytes, separators included: with a 15-byte successor name a level
    is 17 bytes, and Duo{a,b} with a + b = 986,894 is 3 + 1 + 2 * 6 + 17 * 986,894 + 1 + 1
    = 16,777,216 bytes in 986,897 visits; Pair's one extra byte is Exhausted."""
    exhausted = {'outcome': 'Exhausted', 'kind': 2, 'cause': 'display', 'calls': 1}

    def nat(succ):
        return {'kind': 'data', 'name': 'Nat', 'constructors': [{'name': 'Zero', 'fields': []},
                                                                {'name': succ, 'fields': [0]}]}

    def unary(n, succ='Succ'):
        return f'{succ}{{' * n + 'Zero{}' + '}' * n

    def shown(line):
        return {'exit': 0, 'stdout_sha256': sha(line.encode()), 'calls': 1}

    def word(n):
        return {'entry': 'book', 'representation': {'Nat': 0}, 'types': [nat('Succ')],
                'functions': [{'name': 'main', 'parameters': [], 'result': 0, 'slots': 0, 'body': ['lit', 0, 'Nat', n]}]}

    def pair(name, a, b):
        return {'entry': 'book', 'representation': {'Nat': 0},
                'types': [nat('S' * 15), {'kind': 'data', 'name': name, 'constructors': [{'name': name, 'fields': [0, 0]}]}],
                'functions': [{'name': 'main', 'parameters': [], 'result': 1, 'slots': 0,
                               'body': ['con', 1, 0, [['lit', 0, 'Nat', a], ['lit', 0, 'Nat', b]]]}]}
    half = 986_894 // 2
    return [
        ('display-visits-at-bound', word(1_048_575), shown(f'Evaluated\t0\t1\t{unary(1_048_575)}\n')),
        ('display-visits-beyond-bound', word(1_048_576), exhausted),
        ('display-bytes-at-bound', pair('Duo', half, half),
         shown(f"Evaluated\t1\t0\tDuo{{{unary(half, 'S' * 15)},{unary(half, 'S' * 15)}}}\n")),
        ('display-bytes-beyond-bound', pair('Pair', half, half), exhausted),
    ]


def describe_controls(plans: dict) -> list:
    """(label, type table, result type, section 8's frozen verdict) for the Book describe
    domain: None where the VM describes the result, else why it reports Unsupported."""
    flag = plans['value-on']['types'][0]
    box = [{'kind': 'opaque', 'name': 'U32'}, {'kind': 'data', 'name': 'Box', 'constructors': [{'name': 'Box', 'fields': [0]}]}]
    flags = [{'kind': 'data', 'name': 'List', 'constructors': [{'name': 'Nil', 'fields': []}, {'name': 'Con', 'fields': [None, 0]}]}, flag]
    return [
        ('flag', plans['value-on']['types'], 0, None),
        ('nat', plans['nat-unpack']['types'], 0, None),
        ('erased-field', plans['erased-construct']['types'], 1, None),
        ('u32', plans['result-u32']['types'], 0, 'opaque U32 as the result'),
        ('u32-field', box, 1, 'opaque U32 as field 0 of Box'),
        ('char', plans['char-code']['types'], 2, 'opaque U32 as field 0 of Chr'),
        ('string', plans['string-eq']['types'], 3, 'opaque U32 as field 0 of Chr'),
        ('list-of-flags', flags, 0, 'none-typed field 0 of Con'),
        ('arrow', plans['closure-return']['types'], 1, 'arrow type as the result'),
    ]


def describe_verdicts(controls: list, c=None) -> dict:
    c = c or codec
    return {label: c.undescribable({'types': types}, t) for label, types, t, _ in controls}


# String constants that a text spelling would merge (a UTF-16 surrogate pair beside U+1F600),
# refuse (above U+10FFFF) or cannot hold (a lone surrogate, the u32 maximum). SPEC section 2
# keeps every u32 code in order.
CODE_LISTS = {'surrogate-pair': [0xD83D, 0xDE00], 'u1f600': [0x1F600], 'lone-surrogate': [0xD800],
              'u10ffff': [0x10FFFF], 'u110000': [0x110000], 'u32-max': [0xFFFFFFFF]}


def code_controls(plans: dict) -> list:
    """(label, plan): `String.eq(a, b)` on string-ne-order's plan with code-list literals."""
    def eq(a, b):
        plan = json.loads(json.dumps(plans['string-ne-order']))
        left, right = plan['functions'][1]['body'][3]
        left[3], right[3] = a, b
        return plan
    return [(f'codes:{label}', eq(codes, [0x61])) for label, codes in CODE_LISTS.items()] + [
        ('codes:pair-beside-u1f600', eq(CODE_LISTS['surrogate-pair'], CODE_LISTS['u1f600']))]


def round_trip(plan: dict, image: bytes, digest: bytes, c=None) -> str | None:
    """None when `image` decodes to `plan` and survives the decode CLI's JSON text step."""
    c = c or codec
    decoded = c.decode(image, digest)
    if decoded != plan:
        return 'decodes to another plan'
    if c.encode(json.loads(json.dumps(decoded)), digest) != image:
        return 'the JSON text of its decoded plan re-encodes to other bytes'
    return None


def text_spelling(plans: dict, digest: bytes, c=None) -> str | None:
    """None when the encoder refuses a String constant spelled as text, the lossy spelling."""
    c = c or codec
    plan = json.loads(json.dumps(plans['string-ne-order']))
    plan['functions'][1]['body'][3][0][3] = 'ab'
    try:
        c.encode(plan, digest)
    except ValueError:
        return None
    return 'a text-spelled String constant was encoded'


# Semantic mutants of the reference codec: (name, [(old, new), ...]). Each must change a
# committed image, a frozen refusal, an admitted control or a frozen describe verdict; a crash
# is never a kill.
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
    ('string-reversed', [("        data = u32_list(value) if kind == 'String' else u32_list([value])",
                          "        data = u32_list(value[::-1]) if kind == 'String' else u32_list([value])")]),
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
    ('validator-ignores-prim-arity', [("            if len(node[3]) != len(row['inputs']):\n                fail(where, f'{op} arity')\n"
                                       "                return deepest\n", "")]),
    ('validator-any-literal-kind', [("            if kind_of_rep(t) != node[2]:", "            if False:")]),
    ('validator-ignores-representation', [("            fail('representation', f'{r} shape')", "            pass")]),
    ('validator-program-without-io-op', [("        missing = [r for r in ('Unit', 'String', 'IO.OP') if r not in rep]",
                                          "        missing = []")]),
    ('validator-ignores-foreign-operands', [("            for k, name in zip(node[3], row['inputs']):\n",
                                             "            for k, name in zip(node[3], row['inputs']) if op == 'prim' else []:\n")]),
    ('validator-ignores-key-body-type', [("                    if not fits(t, r[4][1]):\n                        fail(where, 'key branch body type')\n", "")]),
    ('validator-ignores-default-body-type', [("                if not fits(t, default[1][1]):\n                    fail(where, 'default body type')\n", "")]),
    ('validator-ignores-branch-body-type', [("                    if not fits(t, r[4][1]):\n                        fail(where, 'branch body type')\n", "")]),
    # Review round 5: arm bodies fit their Case; exact equality refuses S's first_code.
    ('validator-exact-arm-type', [("                    if not fits(t, r[4][1]):\n                        fail(where, 'branch body type')",
                                   "                    if r[4][1] != t:\n                        fail(where, 'branch body type')"),
                                  ("                    if not fits(t, r[4][1]):\n                        fail(where, 'key branch body type')",
                                   "                    if r[4][1] != t:\n                        fail(where, 'key branch body type')"),
                                  ("                if not fits(t, default[1][1]):", "                if default[1][1] != t:")]),
    ('validator-exact-key-and-default-type', [("                    if not fits(t, r[4][1]):\n                        fail(where, 'key branch body type')",
                                               "                    if r[4][1] != t:\n                        fail(where, 'key branch body type')"),
                                              ("                if not fits(t, default[1][1]):", "                if default[1][1] != t:")]),
    ('validator-vacuous-operand-representation', [("                if name not in rep or k[1] != rep[name]:",
                                                   "                if rep.get(name, k[1]) != k[1]:")]),
    ('validator-vacuous-prim-result', [("            if op == 'prim' and (row['output'] not in rep or t != rep[row['output']]):",
                                        "            if op == 'prim' and rep.get(row['output'], t) != t:")]),
    ('validator-ignores-foreign-result', [("            if op == 'foreign' and not io(t, rep.get(row['output'])):", "            if False:")]),
    ('validator-program-any-result', [("        elif main and not io(main[0]['result'], rep['Unit']):", "        elif False:")]),
    ('validator-inspects-none', [("            if scrutinee is None or scope[slot] not in (None, scrutinee):",
                                  "            if scope[slot] not in (None, scrutinee):")]),
    ('validator-strict-scrutinee', [("            if scrutinee is None or scope[slot] not in (None, scrutinee):",
                                     "            if scrutinee is None or scope[slot] != scrutinee:")]),
    ('validator-reference-wildcard', [("                if scope[node[2]] != t:", "                if not fits(scope[node[2]], t):")]),
    ('validator-shape-counts-only', [("[c['fields'] for c in types[t]['constructors']] != [\n                [pinned(n) for n in fields]",
                                      "[len(c['fields']) for c in types[t]['constructors']] != [\n                len(fields)")]),
    ('describe-root-only', [("        work += reversed([(f, f\"field {i} of {c['name']}\")\n"
                             "                          for c in types[u]['constructors'] for i, f in enumerate(c['fields'])])\n", "")]),
    ('describe-admits-scalar-leaves', [("        if kind != 'data':\n", "        if kind != 'data' and at != 'the result':\n"
                                                                     "            continue\n        if kind != 'data':\n")]),
    ('describe-admits-none', [("            return f'none-typed {at}'", "            continue")]),
    ('describe-admits-arrows', [("        if kind != 'data':\n", "        if kind in ('arrow', 'erased-arrow'):\n"
                                                              "            continue\n        if kind != 'data':\n")]),
    # A `none` value that never fits an arrow refuses a generic function instantiated at one.
    ('validator-none-never-arrow', [("        if declared is None or actual is None or declared == actual:\n            return True\n",
                                     "        if declared == actual:\n            return True\n"
                                     "        if declared is None or actual is None:\n"
                                     "            return kind(declared) not in arrows and kind(actual) not in arrows\n")]),
    # Review round 4: section 8's invocation walk, in eval-cli's order.
    ('invoke-arity-first', [("    for at, t in enumerate(f['parameters']):\n        if at == len(ordinals):",
                             "    if len(ordinals) != len(f['parameters']):\n        return 'HostFailure invoke argument-arity'\n"
                             "    for at, t in enumerate(f['parameters']):\n        if at == len(ordinals):")]),
    ('invoke-ignores-leftovers', [("    if len(ordinals) > len(f['parameters']):\n        return 'HostFailure invoke argument-arity'\n", "")]),
    ('invoke-arrow-as-range', [("        if kind in ('arrow', 'erased-arrow'):\n            return 'HostFailure invoke function-argument'\n", "")]),
    ('invoke-opaque-admits-zero', [("        ctors = plan['types'][t]['constructors'] if kind == 'data' else []",
                                    "        ctors = plan['types'][t]['constructors'] if kind == 'data' else "
                                    "[{'fields': []}] if kind == 'opaque' else []")]),
    ('invoke-result-first', [("        return 'HostFailure invoke unknown-export'\n    for at, t",
                              "        return 'HostFailure invoke unknown-export'\n    if undescribable(plan, f['result']):\n"
                              "        return 'Unsupported invoke result-type'\n    for at, t")]),
    ('invoke-admits-structured', [("        if ctors[ordinals[at]]['fields']:\n            return 'HostFailure invoke structured-argument'\n", "")]),
    # Round-5 re-review: section 8's argument words, Base's U32.read, checked before FN.
    ('invoke-words-after-lookup', [("    if None in map(decimal, argv[1:]):\n        return 'HostFailure arguments expected-u32'\n", ""),
                                   ("        return 'HostFailure invoke unknown-export'\n    for at, t",
                                    "        return 'HostFailure invoke unknown-export'\n    if None in map(decimal, argv[1:]):\n"
                                    "        return 'HostFailure arguments expected-u32'\n    for at, t")]),
    ('invoke-words-per-parameter', [("    if None in map(decimal, argv[1:]):", "    if decimal(argv[1]) is None:"),
                                    ("        if at == len(ordinals):\n            return 'HostFailure invoke argument-arity'\n",
                                     "        if at == len(ordinals):\n            return 'HostFailure invoke argument-arity'\n"
                                     "        if ordinals[at] is None:\n            return 'HostFailure arguments expected-u32'\n")]),
    ('invoke-fuel-unchecked', [("    if None in map(decimal, argv[1:]):", "    if None in map(decimal, argv[2:]):")]),
    ('invoke-words-wrap', [("    return int(word) if re.fullmatch('[0-9]+', word) and int(word) <= 0xFFFFFFFF else None",
                            "    return int(word) & 0xFFFFFFFF if re.fullmatch('[0-9]+', word) else None")]),
    ('invoke-words-maximum-exclusive', [("int(word) <= 0xFFFFFFFF", "int(word) < 0xFFFFFFFF")]),
    ('invoke-words-no-leading-zeros', [("re.fullmatch('[0-9]+', word)", "re.fullmatch('0|[1-9][0-9]*', word)")]),
    ('invoke-words-ten-digits', [("re.fullmatch('[0-9]+', word)", "re.fullmatch('[0-9]{1,10}', word)")]),
    ('invoke-words-empty-zero', [("    return int(word) if re.fullmatch('[0-9]+', word) and int(word) <= 0xFFFFFFFF else None",
                                  "    return int(word or 0) if re.fullmatch('[0-9]*', word) and int(word or 0) <= 0xFFFFFFFF else None")]),
    ('invoke-words-unicode-digits', [("re.fullmatch('[0-9]+', word)", "word.isdigit()")]),
    ('invoke-words-host-int', [("    return int(word) if re.fullmatch('[0-9]+', word) and int(word) <= 0xFFFFFFFF else None",
                                "    try:\n        value = int(word)\n    except ValueError:\n        return None\n"
                                "    return value if 0 <= value <= 0xFFFFFFFF else None")]),
    # Review round 3: a String constant is its code list at every step.
    ('encode-through-json-text', [("        data = u32_list(value) if kind == 'String' else u32_list([value])",
                                   "        data = [ord(c) for c in json.loads(json.dumps(''.join(map(chr, value))))] "
                                   "if kind == 'String' else u32_list([value])")]),
    ('encode-accepts-text', [("        data = u32_list(value) if kind == 'String' else u32_list([value])",
                              "        data = u32_list([ord(c) for c in value] if isinstance(value, str) else value) "
                              "if kind == 'String' else u32_list([value])")]),
    ('decode-string-as-text', [("list(r[2:]) if kind == 'String' else r[2]", "''.join(map(chr, r[2:])) if kind == 'String' else r[2]")]),
    ('decode-refuses-beyond-unicode', [("        constants.append((kind, list(r[2:]) if kind == 'String' else r[2]))\n",
                                        "        if kind == 'String' and max(r[2:], default=0) > 0x10FFFF:\n"
                                        "            raise Malformed('string code beyond plan text')\n"
                                        "        constants.append((kind, list(r[2:]) if kind == 'String' else r[2]))\n")]),
]


def invocation_verdicts(invoking: list, c=None) -> dict:
    """Section 8's verdict on every frozen Book invocation, by label."""
    c = c or codec
    return {label: c.invocation(plan, words) for label, plan, words in invoking}


def codec_mutants(plans, images, controls, admitted, describing, reg, digest, invoking) -> list:
    """`plans` and `images` include the code-list controls; a decode that differs from its
    plan kills as surely as an encode that differs from its image."""
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
                lost = round_trip(plan, images[case], digest, mutant)
                if lost:
                    killed_by = f'image {case} {lost}'
                    break
            except Exception:
                continue
        if not killed_by:
            try:
                killed_by = text_spelling(plans, digest, mutant)
            except Exception:
                pass
        for label, data, reason, message in [] if killed_by else controls:
            try:
                got = rejected(data, reg, digest, mutant)
            except Exception:
                continue
            if got is None or not got.startswith(reason) or message not in got:
                killed_by = f'control {label}: {got}'
                break
        for label, data in [] if killed_by else admitted:
            try:
                got = rejected(data, reg, digest, mutant)
            except Exception:
                continue
            if got is not None:
                killed_by = f'admitted control {label}: {got}'
                break
        if not killed_by:
            try:
                verdicts = describe_verdicts(describing, mutant)
            except Exception:
                verdicts = None
            changed = [label for label, _, _, verdict in describing if verdicts and verdicts[label] != verdict]
            if changed:
                killed_by = f'describe control {changed[0]}: {verdicts[changed[0]]}'
        if not killed_by:
            frozen = invocation_verdicts(invoking)
            try:
                verdicts = invocation_verdicts(invoking, mutant)
            except Exception:
                verdicts = frozen
            changed = [label for label in frozen if verdicts[label] != frozen[label]]
            if changed:
                killed_by = f'invocation {changed[0]}: {verdicts[changed[0]]}'
        results.append({'mutant': name, 'killed': killed_by is not None, 'by': killed_by})
    return results


# Semantic mutants of the reference evaluation: each must change a golden expectation, a Book
# value or a run control, or be refused by the rule; a crash is never a kill.
EVALUATOR_MUTANTS = [
    ('scalar-admits-beyond-unicode', [('    return code < 0xD800 or 0xDFFF < code <= 0x10FFFF',
                                       '    return code < 0xD800 or 0xDFFF < code')]),
    ('scalar-admits-surrogates', [('    return code < 0xD800 or 0xDFFF < code <= 0x10FFFF', '    return code <= 0x10FFFF')]),
    ('print-without-lf', [("        self.stdout += b''.join(map(utf8, codes)) + b'\\n'",
                           "        self.stdout += b''.join(map(utf8, codes))")]),
    ('native-stops-at-non-scalar', [("        if self.policy == 'vm' and not all(map(scalar, codes)):",
                                     '        if not all(map(scalar, codes)):')]),
    ('wide-code-clamped', [('    return bytes([(0xF0 | code >> 18) & 0xFF,',
                            '    code = min(code, 0x10FFFF)\n    return bytes([(0xF0 | code >> 18) & 0xFF,')]),
    ('nat-case-binds-n', [('            return (0, ()) if w == 0 else (1, (w - 1,))',
                           '            return (0, ()) if w == 0 else (1, (w,))')]),
    # Section 6.1: a predecessor at or above 2^31 is a Big, never an immediate's 31 bits.
    ('nat-predecessor-narrowed', [('            return (0, ()) if w == 0 else (1, (w - 1,))',
                                   '            return (0, ()) if w == 0 else (1, ((w - 1) & 0x7FFFFFFF,))')]),
    ('string-literal-reversed', [('        for code in reversed(codes):', '        for code in codes:')]),
    ('captures-reversed', [("            return ('closure', node, tuple(env[s] for s in node[4]))",
                            "            return ('closure', node, tuple(env[s] for s in node[4][::-1]))")]),
    ('closure-arity-unchecked', [("        takes = {'closure': lambda: len(operands) == f[1][2],",
                                  "        takes = {'closure': lambda: True,")]),
    ('erased-entry-free', [("        self.debit()\n        if kind == 'closure':",
                            "        if operands or kind != 'closure':\n            self.debit()\n        if kind == 'closure':")]),
    ('u32-sub-saturates', [('lambda: (x - y) & WORD,', 'lambda: max(x - y, 0),')]),
    # Section 8's display bounds are inclusive, a Nat word n is n + 1 visits, and the tree's
    # separators are text (display_controls).
    ('display-visits-exclusive', [('            if cost[0] > DISPLAY_VISITS or', '            if cost[0] >= DISPLAY_VISITS or')]),
    ('display-bytes-exclusive', [(' or cost[1] > DISPLAY_BYTES:', ' or cost[1] >= DISPLAY_BYTES:')]),
    ('display-nat-one-visit', [('                charge(v + 1, ', '                charge(1, ')]),
    ('display-separators-free', [('                charge(0, len(item))', '                charge(0, 0)')]),
    # Section 7's fuel boundary (fuel_controls): no golden runs out of fuel.
    ('fuel-never-exhausts', [('        if self.fuel == 0:\n            raise Halt', '        if False:\n            raise Halt')]),
    ('fuel-exhausts-early', [('        if self.fuel == 0:\n            raise Halt', '        if self.fuel <= 1:\n            raise Halt')]),
    ('effect-before-debit', [("        self.debit()\n        if kind == 'closure':",
                              "        if kind != 'action' or not operands:\n            self.debit()\n        if kind == 'closure':"),
                             ('        return self.apply(operands[0], [self.effect(f)])',
                              '        r = self.effect(f)\n        self.debit()\n        return self.apply(operands[0], [r])')]),
    ('fuel-before-operand-check', [('        if kind not in takes or not takes[kind]():',
                                    '        if self.fuel == 0:\n            self.debit()\n'
                                    '        if kind not in takes or not takes[kind]():')]),
    ('terminal-entry-free', [("        self.debit()\n        if kind == 'closure':",
                              "        if kind != 'terminal':\n            self.debit()\n        if kind == 'closure':")]),
]


def evaluator_mutants(cases, plans, bounds, sources, table, runs) -> list:
    """Each mutant re-derives every golden expectation, Book value and run control."""
    source = EVALUATOR.read_text()
    results = []
    for name, edits in EVALUATOR_MUTANTS:
        text = source
        for old, new in edits:
            require(text.count(old) == 1, f'evaluator mutant {name} is not uniquely located')
            text = text.replace(old, new)
        mutant, killed_by = load(EVALUATOR, text), None
        for case_name, case in cases.items():
            try:
                got = vm_expectation(case, plans[case_name], bounds, sources[case_name], mutant)
                reproduced(case_name, plans[case_name], got, mutant)
            except AssertionError as refusal:
                killed_by = f'{case_name}: {refusal}'
            except Exception:
                continue
            else:
                killed_by = None if got == table[case_name] else f'{case_name}: expectation {got}'
            if killed_by:
                break
        for label, plan, frozen in [] if killed_by else runs:
            try:
                got = ran(plan, frozen, mutant)
            except Exception:
                continue
            killed_by = None if got == frozen else f'run control {label}: {got}'
            if killed_by:
                break
        results.append({'mutant': f'evaluator:{name}', 'killed': killed_by is not None, 'by': killed_by})
    return results


SOURCE_MUTANTS = [
    ('case-on', 'flip(On{})', 'flip(Off{})'),
    ('u32-wrap', 'U32.add(4294967295,1)', 'U32.add(4294967295,2)'),
    ('closure-capture-on', 'capture(On{})', 'capture(Off{})'),
    ('string-surrogate-pair', '"\\u{1f600}"', '"\\u{d83d}\\u{de00}"'),
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

def committed(path: str) -> bytes:
    return (ROOT / path).read_bytes()


def check_bench(built: dict, read=committed) -> dict:
    """The speed freeze: sources and seed-native measurements unchanged, the measurements
    recorded against those exact sources."""
    manifest = json.loads(read('vm/bench/workloads.json'))
    for path, digest in manifest['measurements']['sha256'].items():
        require(sha(read(path)) == digest, f'bench measurement {path} differs from its pin')
    baselines = json.loads(read('vm/bench/baselines.json'))
    require([w['name'] for w in manifest['workloads']] == list(baselines['workloads']), 'bench workload set')
    for w in manifest['workloads']:
        require(sha(read(w['source'])) == w['sha256'], f"bench source {w['name']}")
        row = baselines['workloads'][w['name']]
        require(row['source_sha256'] == w['sha256'], f"bench baseline source {w['name']}")
        require(row['stdout'] == w['expected_stdout'] == 'True{}\n' and row['exit'] == 0, f"bench output {w['name']}")
        require(len(row['samples']) == row['repeat'] >= 3 and row['summary']['instructions']['median'] > 0,
                f"bench samples {w['name']}")
    parse = json.loads(read('vm/bench/parse-cli.json'))
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
    return {'workloads': len(manifest['workloads']), 'parse_cli_files': len(parse['files']),
            'measurements': manifest['measurements']['sha256']}


def bench_controls(built: dict) -> list:
    """A re-measurement must not pass as the frozen baseline."""
    out = []
    for path, field in [('vm/bench/baselines.json', 'workloads'), ('vm/bench/parse-cli.json', 'files')]:
        data = json.loads(committed(path))
        rows = data[field]
        row = rows[next(iter(rows))] if isinstance(rows, dict) else rows[0]
        row['summary']['instructions']['median'] += 1
        remeasured = (json.dumps(data, indent=1) + '\n').encode()
        try:
            check_bench(built, lambda p: remeasured if p == path else committed(p))
        except AssertionError as refusal:
            out.append({'control': f'bench:remeasured-{Path(path).stem}', 'refused': str(refusal)})
            continue
        raise AssertionError(f'bench control {path} was admitted')
    return out


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
    planned = {c['name']: c for c in json.loads((GOLDEN / 'plan.json').read_text())['cases']}
    require(sorted(planned) == sorted(cases) and len(planned) == len(frozen['cases']),
            'plan.json and expectations.json list the same cases')
    for c in cases.values():
        require(sha((ROOT / c['source']).read_bytes()) == c['sha256'], f"frozen source {c['name']}")
        # D7: the literal review written before observation is the seed's printed value
        # (plan.json's first reviews spelled `, ` as `,`); a stdout that is not UTF-8 is
        # reviewed byte for byte, and the Bun cross-check by its stderr.
        if 'seed_stdout_hex' in c:
            require(c['seed_stdout_hex'] == c['seed'].get('stdout_hex'),
                    f"{c['name']}: literal review {c['seed_stdout_hex']}, seed wrote {c['seed'].get('stdout_hex')}")
        else:
            require(c['seed_stdout'] == c['seed']['stdout'],
                    f"{c['name']}: literal review {c['seed_stdout']!r}, seed printed {c['seed']['stdout']!r}")
            require(planned[c['name']]['seed_stdout'].replace(', ', ',') == c['seed_stdout'].replace(', ', ','),
                    f"{c['name']}: plan.json literal review differs from the frozen row")
        if 'seed_bun_stderr' in c:
            require(c['seed_bun_stderr'] == c['seed_bun']['stderr'],
                    f"{c['name']}: literal review {c['seed_bun_stderr']!r}, Bun lane {c['seed_bun']['stderr']!r}")
        for key in ('seed_stdout_hex', 'seed_bun_stderr', 'divergence', 'vm_stdout'):
            require(planned[c['name']].get(key) == c.get(key), f"{c['name']}: plan.json {key} differs from the frozen row")
        require(planned[c['name']].get('invocations') == ([reviewed(i) for i in c.get('invocations', [])] or None),
                f"{c['name']}: plan.json invocations differ from the frozen row")
    sources = {name: (ROOT / c['source']).read_text() for name, c in cases.items()}

    with ThreadPoolExecutor(max_workers=4) as pool:
        fresh = dict(zip(cases, pool.map(lambda c: lanes(c, built), cases.values())))

    def display(case):
        tool = built[case['lane']]['check']
        return run([tool, *lane_prefix(case), case['source']], 120)

    with ThreadPoolExecutor(max_workers=4) as pool:
        displays = dict(zip(cases, pool.map(display, cases.values())))

    bounds = json.loads((GOLDEN / 'bounds.json').read_text())['cases']
    plans, images, fixtures, table, invoked = {}, {}, [], {}, {}
    for name, case in cases.items():
        require(fresh[name]['seed'] == case['seed'], (name, 'seed drift', fresh[name]['seed'], case['seed']))
        require(fresh[name]['eval'] == case['eval'], (name, 'eval drift', fresh[name]['eval'], case['eval']))
        require(fresh[name].get('seed_bun') == case.get('seed_bun'), (name, 'Bun lane drift', fresh[name].get('seed_bun')))
        require(fresh[name].get('invocations') == case.get('invocations'), (name, 'invocation drift', fresh[name].get('invocations')))
        plan = json.loads((GOLDEN / f'{name}.plan.json').read_text())
        data = (GOLDEN / f'{name}.kimg').read_bytes()
        require(codec.encode(plan, digest) == data, f'{name}: committed image differs from its plan')
        require(codec.decode(data, digest) == plan, f'{name}: image does not decode to its plan')
        problems = codec.validate(plan, reg)
        require(not problems, (name, problems))
        check_declarations(plan, sources[name])
        shown = displays[name]
        if shown['exit'] == 0:
            derived = from_display(shown['stdout'], plan, sources[name], reg)
            require(derived == plan['functions'], (name, 'plan differs from the checked core', derived))
            view = 'checked-core'
        else:
            require(plan['entry'] == 'program', f'{name}: no checked core for a Book plan')
            view = f"unavailable: {shown['stderr'].strip()}"
        table[name] = vm_expectation(case, plan, bounds, sources[name])
        reproduced(name, plan, table[name])
        if 'invocations' in case:
            invoked[name] = invocation_expectations(case, plan, sources[name])
        plans[name], images[name] = plan, data
        fixtures.append({'name': name, 'lane': case['lane'], 'seed_lane': case.get('seed_lane', 'bun'),
                         'features': case['features'], 'image_sha256': sha(data), 'words': len(data) // 4,
                         'plan_matches': view, 'seed': classify(case['seed']), 'eval': classify(case['eval']),
                         'vm': table[name]})

    strings = plans['result-string']
    for row in fixtures:
        argument = print_argument(row['name'], sources[row['name']], plans[row['name']], strings, built, reg)
        if argument:
            row['plan_matches'] += f'; {argument}'

    expected = {'rule': 'SPEC section 11: the VM owes the seed value wherever the seed succeeds within the '
                        'declared domain and budgets; eval-cli supplies the describe text where it agrees with the seed. '
                        'A Book result outside section 8\'s describe domain is Unsupported, never a bound. '
                        'A Program\'s own value classifies its output: where the reference evaluation of its plan '
                        'passes IO.print a String holding a non-scalar Char, the VM writes the earlier prints and '
                        'refuses that one as D20\'s HostFailure io abi, divergent by contract, never agreement; '
                        'otherwise the VM owes the seed\'s output. The seed lanes are observations and never '
                        'classify it. A Book invocation owes section 8\'s verdict, or the describe line of the '
                        'entered function; eval-cli agrees except where the image drops what its core reads.',
                'fuel': VM_FUEL, 'bounds': bounds, 'cases': table, 'invocations': invoked}
    if args.write_expected:
        EXPECTED.write_text(json.dumps(expected, indent=1) + '\n')
    require(json.loads(EXPECTED.read_text()) == expected, 'vm-expected.json differs from the rule')

    opcodes = {n[0] for p in plans.values() for n in walk(p)}
    require(opcodes == set(codec.OPCODES), f'uncovered node forms {set(codec.OPCODES) - opcodes}')
    modes = {n[4] for p in plans.values() for n in walk(p) if n[0] == 'case'}
    require(modes == set(codec.CASE_MODES), 'both case modes')
    big = [n for p in plans.values() for n in walk(p) if n[0] == 'lit' and n[2] != 'String' and n[3] >= 1 << 31]
    require(big, 'a boxed scalar constant')
    abstract = [n for p in plans.values() for n in walk(p) if n[0] not in ('branch', 'default') and n[1] is None]
    require(abstract, 'a none-typed node')

    planned = plan_controls(plans)
    lowered = lowered_controls(planned, reg)
    controls = byte_controls(images, digest) + [
        (f'plan:{k}', codec.encode(p, digest), 'HostFailure image: validator: ', m) for k, p, m in planned if m]
    admitted = [(f'plan:{k}', codec.encode(p, digest)) for k, p, m in planned if m is None]
    boundaries = expectation_controls(cases, plans, bounds, sources) + invocation_controls(cases, plans, sources) + \
        seed_display_controls()
    for label, data, reason, message in controls:
        got = rejected(data, reg, digest)
        require(got is not None and got.startswith(reason) and message in got, f'control {label}: {got}')
        boundaries.append({'control': label, 'refused': got})
    for label, data in admitted:
        require(rejected(data, reg, digest) is None, f'admitted control {label}: {rejected(data, reg, digest)}')
    runs = {}
    for label, plan, frozen in run_controls(plans):
        data = codec.encode(plan, digest)
        require(rejected(data, reg, digest) is None, f'run control {label}: {rejected(data, reg, digest)}')
        require(codec.decode(data, digest) == plan, f'run control {label}: decodes to another plan')
        admitted.append((f'run:{label}', data))
        require(ran(plan, frozen) == frozen, f'run control {label}: the reference evaluation gives {ran(plan, frozen)}')
        runs[label] = {'argv': run_argv(plan, frozen), **frozen, 'image_sha256': sha(data)}
    describing = describe_controls(plans)
    verdicts = describe_verdicts(describing)
    for label, _, _, verdict in describing:
        require(verdicts[label] == verdict, f'describe control {label}: {verdicts[label]!r}, frozen {verdict!r}')
    coded = dict(code_controls(plans))
    for label, plan in coded.items():
        data = codec.encode(plan, digest)
        require(rejected(data, reg, digest) is None, f'code-list control {label}: {rejected(data, reg, digest)}')
        require(round_trip(plan, data, digest) is None, f'code-list control {label}: {round_trip(plan, data, digest)}')
        admitted.append((label, data))
    require(text_spelling(plans, digest) is None, text_spelling(plans, digest))

    invoking = [(invocation_label(name, i), plans[name], invocation_words(i))
                for name, case in cases.items() for i in case.get('invocations', [])]
    mutants = codec_mutants({**plans, **coded}, {**images, **{k: codec.encode(p, digest) for k, p in coded.items()}},
                            controls, admitted, describing, reg, digest, invoking) + source_mutants(cases, built) + \
        evaluator_mutants(cases, plans, bounds, sources, table, run_controls(plans))
    survivors = [m['mutant'] for m in mutants if not m['killed']]
    require(not survivors, f'surviving mutants {survivors}')

    record['bench'] = check_bench(built)
    boundaries += bench_controls(built)
    record.update(status='passed', fixtures=fixtures, boundaries=boundaries,
                  admitted=[label for label, _ in admitted], lowered=lowered, runs=runs, describe=verdicts, mutants=mutants,
                  code_lists={'round_trip': sorted(coded), 'text_spelling': 'refused by encode'},
                  coverage={'opcodes': sorted(opcodes), 'case_modes': sorted(modes),
                            'program_images': sum(p['entry'] == 'program' for p in plans.values()),
                            'none_typed_nodes': len(abstract)})
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(record, indent=1) + '\n')
    print(f"vm-spec passed: {len(fixtures)} golden images, {len(boundaries)} refused controls, "
          f"{len(admitted)} admitted controls ({len(coded)} code lists, {len(runs)} runs), "
          f"{len(verdicts)} describe controls, "
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
