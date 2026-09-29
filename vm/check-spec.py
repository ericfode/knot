#!/usr/bin/env python3
"""Gate vm-spec: frozen golden images against the pinned seed and eval-cli.

Re-executes the oracle lanes on every golden source and compares the frozen
observations byte for byte, and does the same for each seed witness (sources that
SPEC section 8 cites and no golden can carry); re-derives the prim registry; checks that every
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
import ast
import datetime
import gzip
import hashlib
import importlib.util
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import random
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
WITNESSES = GOLDEN / 'witnesses.json'
CODEC = HERE / 'serializer.py'
EVALUATOR = HERE / 'evaluate.py'
RULE = Path(__file__).resolve()


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


def core_view(name: str, case: dict, plan: dict, shown: dict, source: str, reg: dict) -> str:
    """How a golden's plan meets check-cli's core display: equal to the lowering of the core it
    prints, or, where none exists, a Program (whose main the pinned heads reject) or a Book whose
    review declared the exact Unsupported line before observation (SPEC section 11)."""
    declared = case.get('unavailable')
    if shown['exit'] == 0:
        require(not declared, f'{name}: declared unavailable, but check-cli prints a core')
        derived = from_display(shown['stdout'], plan, source, reg)
        require(derived == plan['functions'], (name, 'plan differs from the checked core', derived))
        return 'checked-core'
    if declared:
        require(unavailable_line(shown, declared), f'{name}: declared unavailable as {declared!r}, check-cli gives {observed(shown)}')
    else:
        require(plan['entry'] == 'program', f'{name}: no checked core for a Book plan')
    return f"unavailable: {shown['stderr'].strip()}"


def core_controls(cases: dict, plans: dict, sources: dict, displays: dict, reg: dict) -> list:
    """What the display lane must refuse: a Book without a core that declared no gap, a declaration
    where check-cli prints a core, and a declaration of another line than the one it prints."""
    def without(name, *keys):
        return {k: v for k, v in cases[name].items() if k not in keys}
    out = []
    for label, name, case in [
            ('undeclared', 'chr-pattern', without('chr-pattern', 'unavailable')),
            ('declared-with-core', 'value-on', {**cases['value-on'], 'unavailable': 'Unsupported check char-constructor-pattern'}),
            ('declared-other-line', 'list-head-match', {**cases['list-head-match'], 'unavailable': 'Unsupported check char-constructor-pattern'})]:
        try:
            core_view(name, case, plans[name], displays[name], sources[name], reg)
        except AssertionError as refusal:
            out.append({'control': f'core:{label}', 'refused': str(refusal)})
            continue
        raise AssertionError(f'core control {label} was admitted')
    return out


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
    """The source's own datatypes: names, constructor order and live field counts. A generic
    declaration (`type Box<-R: Type> is Type:`) counts, as Base's own do."""
    pinned = set(plan.get('representation', {}).values())
    declared = re.findall(r'^type (\w+)(?:<[^>]*>)? is (?:Data|Type):\n((?:  \w+\{[^}]*\}\n)+)', source, re.M)
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
        # Section 7: the entry that applies the Action to k builds the request that the loop then refuses;
        # it was debited, and the debit stands.
        require(case.get('vm_calls') == vm['calls'],
                f"{name}: literal review counts {case.get('vm_calls')} calls, the reference evaluation {vm['calls']}")
        return {'argv': argv, 'outcome': 'HostFailure', 'cause': 'io abi', 'stdout': case['vm_stdout'],
                'calls': case['vm_calls'], 'basis': f'divergent-by-contract ({NON_SCALAR})',
                'reason': f'D20: print {at} holds Char {code}; the native lane exits 0', 'eval_lane': classify(case['eval'])}
    require(vm.get('exit') == 0, f'{name}: the reference evaluation ends {vm}')
    require('divergence' not in case, f'{name}: a {NON_SCALAR} divergence, but every printed Char is a scalar')
    return {'argv': argv, 'exit': 0, 'stdout': seed['stdout'], 'stderr': '', 'basis': 'seed',
            'eval_lane': classify(case['eval'])}


def unavailable_line(lane: dict, declared: str) -> bool:
    """A head's exit-3 answer is `Unsupported<TAB>phase<TAB>cause<TAB>span` on stderr; `declared`
    spells its phase and cause with spaces, as a golden's literal review does."""
    line = re.fullmatch(r'Unsupported\t(\w+)\t([\w-]+)\t\d+:\d+:\d+:\d+\n', lane['stderr'])
    return lane['exit'] == 3 and lane['stdout'] == '' and line is not None and f'Unsupported {line[1]} {line[2]}' == declared


def vm_expectation(case, plan, bounds, source, evaluator=None) -> dict:
    """The Exhausted-lane rule, applied to the frozen observations of one golden."""
    seed, ev, declared = case['seed'], case['eval'], case.get('unavailable')
    fuel = VM_FUEL
    require('divergence' not in case or plan['entry'] == 'program', f"{case['name']}: only a Program's output diverges")
    require(declared is None or plan['entry'] == 'book', f"{case['name']}: only a Book's core is declared unavailable")
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
    if declared:
        # Section 11: a seed-accepted form that a pinned head reports Unsupported leaves its lane
        # unavailable, not excused. The review declares the exact line, and the VM owes the seed's value.
        require(unavailable_line(ev, declared), f"{case['name']}: declared unavailable as {declared!r}, eval-cli gives {ev}")
        lane = {'eval_lane': 'Unsupported', 'eval_unavailable': declared}
    elif ev['exit'] == 0:
        _, _, tree = result_view(plan, ev['stdout'])
        require(tree == value, f"{case['name']}: eval-cli prints {tree!r}, the seed {value!r}")
        return {'argv': ['IMAGE', 'main', str(fuel)], 'exit': 0, 'stdout': ev['stdout'], 'stderr': '',
                'basis': 'eval-cli', 'eval_lane': 'agree'}
    else:
        # The eval lane is excused only by a documented bound; the VM owes the seed's value.
        lane = {'eval_lane': 'Exhausted', 'eval_bound': eval_excuse(case, plan, value, evaluator)}
    root = re.match(r'[\w.]+', value)[0]
    ctors = [c['name'] for c in plan['types'][main['result']]['constructors']]
    require(root in ctors, f"{case['name']}: seed root {root} is not a constructor of main's result")
    return {'argv': ['IMAGE', 'main', str(fuel)], 'exit': 0,
            'stdout': f"Evaluated\t{main['result']}\t{ctors.index(root)}\t{value}\n", 'stderr': '',
            'basis': 'seed', **lane}


# Section 11's eval-cli bounds, by the phase it names in `Exhausted<TAB>phase<TAB>budget`, each
# budget in the units of `reach`. A lane is excused only past its budget.
EVAL_BOUNDS = {
    'primitive': ('unary Nat and String', {'units': 1 << 20}),
    'eval': ('transitions', {'transitions': 1 << 20}),
    'inspect': ('display', {'steps': 4096, 'characters': 65536}),
}


def reach(plan: dict, value: str, evaluator=None) -> dict:
    """What a Book's main reaches in eval-cli's units, measured without eval-cli. From the
    reference evaluation: `units`, the largest Nat or String length a node yields; and
    `transitions`, a lower bound on eval-cli's, which takes one per term it evaluates and one per
    successor or character it materializes for a Literal or an Intrinsic. From the seed's value in
    section 8's spelling: `steps`, the items of eval-cli's display worklist, two per constructor
    (it and its opening text) and two per field (its slot, then a separator or the closing
    brace), so 4N - 2 for N constructors; and its `characters`."""
    ev = evaluator or reference
    nat, string = (plan.get('representation', {}).get(r, -1) for r in ('Nat', 'String'))

    class Reach(ev.Machine):
        units = transitions = 0

        def eval(self, node, env):
            w = super().eval(node, env)
            size = w if node[1] == nat else len(self.codes(w)) if node[1] == string else 0
            self.units = max(self.units, size)
            self.transitions += 1 + (size if node[0] in ('lit', 'prim') else 0)
            return w
    m = Reach(plan, VM_FUEL)
    try:
        m.call(next(i for i, f in enumerate(plan['functions']) if f['name'] == 'main'), [])
    except ev.Halt:
        pass
    return {'units': m.units, 'transitions': m.transitions, 'steps': 4 * value.count('{') - 2,
            'characters': len(value)}


def eval_excuse(case, plan, value, evaluator=None) -> dict:
    """Section 11: the documented bound that excuses an exhausted eval lane, its budget, and the
    boundary the program reaches past it. Any other failure, or a budget not passed, is refused."""
    ev, name = case['eval'], case['name']
    phase = re.fullmatch(r'Exhausted\t(\w+)\tbudget\t0:0:0:0\n', ev['stderr']) if ev['exit'] == 4 else None
    bound, budget = EVAL_BOUNDS.get(phase and phase[1], (None, None))
    require(bound, f'{name}: eval lane {ev} is not a documented bound')
    reached = {unit: amount for unit, amount in reach(plan, value, evaluator).items() if unit in budget}
    require(any(reached[unit] > budget[unit] for unit in budget),
            f'{name}: eval-cli reports its {bound} budget {budget}, but the program reaches {reached}')
    return {'cause': f'Exhausted {phase[1]} budget', 'bound': bound, 'budget': budget, 'reached': reached}


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

    def exhausted(label, seed, phase):
        return {**row(label, seed, ''), 'eval': {'exit': 4, 'stdout': '', 'stderr': f'Exhausted\t{phase}\tbudget\t0:0:0:0\n'}}

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
            # Section 11: eval-cli's lane is excused only by a documented bound, past its budget.
            ('eval-undocumented-exhausted', 'nat-big',
             {**cases['nat-big'], 'eval': exhausted('', '', 'check')['eval']}, bounds, None),
            ('eval-primitive-within-budget', 'nat-pred', exhausted('eval-primitive-within-budget', '2n\n', 'primitive'),
             bounds, None),
            ('eval-transitions-within-budget', 'nat-pred', exhausted('eval-transitions-within-budget', '2n\n', 'eval'),
             bounds, None),
            ('eval-inspect-within-budget', 'nat-pred', exhausted('eval-inspect-within-budget', '1023n\n', 'inspect'),
             bounds, None),
            ('bound-for-unsupported', 'result-u32', cases['result-u32'], {**bounds, 'result-u32': describe_bound}, None),
            # Section 11: a Book's eval lane is unavailable only where its review declares the exact
            # Unsupported line that the head prints; no other failure of a Book's lane stands in.
            ('eval-unsupported-undeclared', 'chr-pattern', without('chr-pattern', 'unavailable'), bounds, None),
            ('unavailable-where-eval-agrees', 'value-on',
             {**cases['value-on'], 'unavailable': 'Unsupported check char-constructor-pattern'}, bounds, None),
            ('unavailable-other-line', 'list-head-match',
             {**cases['list-head-match'], 'unavailable': 'Unsupported check char-constructor-pattern'}, bounds, None),
            ('unavailable-on-program', 'foreign-print',
             {**cases['foreign-print'], 'unavailable': 'Unsupported check char-constructor-pattern'}, bounds, None),
            ('eval-invalid-book', 'value-on',
             {**cases['value-on'], 'eval': {'exit': 2, 'stdout': '', 'stderr': 'Invalid\tparse\tfunction-result\t0:0:0:0\n'}},
             bounds, None),
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
            # Section 7: the debit of the entry that builds the request that the loop refuses stands, so the
            # literal review counts it and must be frozen.
            ('d20-calls-refunded', 'print-non-scalar', {**cases['print-non-scalar'], 'vm_calls': 3}, bounds, None),
            ('d20-calls-unfrozen', 'print-non-scalar-second', without('print-non-scalar-second', 'vm_calls'), bounds, None),
            ('native-without-bun-record', 'print-non-scalar-wide', without('print-non-scalar-wide', 'seed_bun'), bounds, None)]:
        try:
            vm_expectation(case, plan or plans[name], table, sources[name], evaluator)
        except AssertionError as refusal:
            out.append({'control': f'expectation:{label}', 'refused': str(refusal)})
            continue
        raise AssertionError(f'expectation control {label} was admitted')
    return out


def excused_controls(cases: dict, plans: dict, bounds: dict, sources: dict) -> dict:
    """Rows that a documented bound excuses just past its budget, each frozen by literal review
    with the boundary it reaches: the Nat 1,024 takes 4 * 1,025 - 2 display steps and
    5 * 1,024 + 6 + 1,024 characters; u32-to-nat-big evaluates nine terms and materializes the
    Nats 2^31 (U32.to_nat) and 2^31 - 1 (a Literal)."""
    def exhausted(name, phase, seed=None):
        case = {**cases[name], 'name': f'control:{name}-{phase}',
                'eval': {'exit': 4, 'stdout': '', 'stderr': f'Exhausted\t{phase}\tbudget\t0:0:0:0\n'}}
        if seed:
            case['seed'] = {'exit': 0, 'stdout': seed, 'stderr': ''}
        return case
    out = {}
    for label, name, case, frozen in [
            ('eval-inspect-past-budget', 'nat-pred', exhausted('nat-pred', 'inspect', '1024n\n'),
             {'cause': 'Exhausted inspect budget', 'bound': 'display', 'budget': {'steps': 4096, 'characters': 65536},
              'reached': {'steps': 4098, 'characters': 6150}}),
            ('eval-transitions-past-budget', 'u32-to-nat-big', exhausted('u32-to-nat-big', 'eval'),
             {'cause': 'Exhausted eval budget', 'bound': 'transitions', 'budget': {'transitions': 1 << 20},
              'reached': {'transitions': 9 + 2 ** 31 + 2 ** 31 - 1}})]:
        got = vm_expectation(case, plans[name], bounds, sources[name]).get('eval_bound')
        require(got == frozen, f'excused control {label}: {got}, frozen {frozen}')
        out[f'expectation:{label}'] = got
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
        # A Program's written bytes: ASCII, but for the two UTF-8 controls, whose text is Python's own.
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


def rejected(data: bytes, reg: dict, digest: bytes, c=None, clauses=False) -> str | None:
    """None when the image is admitted; otherwise the refusal, as the VM loader must classify it:
    a resource limit of section 4 is Exhausted kind 2, any other refusal HostFailure image. Canonicality is decided by
    encoding the decoded plan again, or, with `clauses`, by the clauses of `canonical_violations`, as a loader
    that has no encoder decides it."""
    c = c or codec
    try:
        plan = c.decode(data, digest)
    except c.Exhausted as e:
        return f'Exhausted 2 {e}'
    except c.Malformed as e:
        return f'HostFailure image: {e}'
    problems = c.validate(plan, reg)
    if problems:
        return 'HostFailure image: validator: ' + problems[0]
    if clauses:
        return 'HostFailure image: noncanonical' if canonical_violations(data) else None
    try:
        again = c.encode(plan, digest)
    except ValueError:
        again = None        # a plan that the encoder refuses (a name with a surrogate) is the decoding of no image
    if again != data:
        return 'HostFailure image: noncanonical'
    return None


def byte_controls(images: dict, digest: bytes) -> list:
    """(label, bytes, frozen refusal prefix) for malformed and noncanonical images."""
    second, capture, hit = images['second'], images['closure-captures'], images['default-hit']
    first_node, names_at = word(second, 9) + 1, word(second, 10)
    swap = word(capture, 7) + 1                 # first function record (swap, arity 2: 8 words)
    body = word(capture, swap + 5)              # its root Let node
    oversize = b'\0' * (4 * codec.LIMITS['image_words'])
    # second's name records: `Flag` (its data word at names_at + 3) and `On` plus two padding bytes (names_at + 12).
    require((word(second, names_at + 3), word(second, names_at + 12)) ==
            (int.from_bytes(b'Flag', 'little'), int.from_bytes(b'On\0\0', 'little')), 'second: name records')
    # second's type records are [5, kind, name, first constructor, count]: Flag (data, 0, 2), then Pair (data, 2, 1).
    type_at = word(second, 5) + 1
    require([word(second, type_at + i) for i in (0, 1, 3, 4)] == [5, 0, 0, 2], 'second: Flag record')
    require([word(second, type_at + 5 + i) for i in (0, 1, 3, 4)] == [5, 0, 2, 1], 'second: Pair record')
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
        # Section 2: a name has no NUL and its unused final bytes are zero.
        ('name-nul', word_patch(second, names_at + 3, int.from_bytes(b'F\0ag', 'little')), 'name padding'),
        ('name-padding', word_patch(second, names_at + 12, int.from_bytes(b'On\0\1', 'little')), 'name padding'),
        # Section 4 step 2: a type's first constructor is the table's next, its count must fit the constructor
        # table before it sizes anything (a list of 0xFFFFFFFF would take 32 GiB), and the counts sum to the table.
        ('type-grouping', word_patch(second, type_at + 3, 1), 'constructor grouping'),
        ('type-count-max', word_patch(second, type_at + 4, 0xFFFFFFFF), 'constructor count'),
        ('type-count-short', word_patch(second, type_at + 5 + 4, 0), 'constructor count'),
        ('function-root-shared', word_patch(capture, swap + 8 + 5, body), 'function root'),
        ('child-not-record', word_patch(capture, body + 4, word(capture, body + 4) + 1), 'child offset'),
        ('child-after-parent', word_patch(capture, body + 4, body + 6), 'child after parent'),
        ('unused-constant', unused_constant(hit), 'noncanonical'),
    ]
    # Section 4.1 and D16: an image above 16 MiB is Exhausted kind 2, even when also malformed.
    exhausted = [
        ('oversize', second + oversize, 'image-size'),
        ('oversize-and-bad-magic', word_patch(second, 0, 0) + oversize, 'image-size'),
        ('oversize-and-misaligned', second + oversize + b'\0', 'image-size'),
    ]
    return [(label, data, 'HostFailure image: ' + reason, '') for label, data, reason in out] + \
        [(label, data, 'Exhausted 2 ' + cause, '') for label, data, cause in exhausted] + structure_controls(images)


def limit_controls(plans: dict, images: dict, digest: bytes) -> list:
    """(label, bytes, frozen refusal or None to admit) on both sides of section 4's limits. A
    count its structure admits and that passes its limit is Exhausted kind 2, even when what it
    governs is malformed or inexact; a count its structure cannot hold is malformed; every
    limit is inclusive. The size's malformed side is an image of exactly 16 MiB."""
    limits, second, capture = codec.LIMITS, images['second'], images['closure-captures']
    names_at, swap = word(second, 10), word(capture, 7) + 1

    def names(count, room):
        """`second` with `count` name records declared and `room` more zero words."""
        data = word_patch(second, names_at, count) + b'\0' * 4 * room
        return word_patch(data, 2, len(data) // 4)

    def edited(name, path, value):
        plan = json.loads(json.dumps(plans[name]))
        *head, last = path
        target = plan
        for key in head:
            target = target[key]
        target[last] = value
        return codec.encode(plan, digest)

    def wide(arity):
        """value-on beside an unused function of `arity` Flag parameters."""
        plan = json.loads(json.dumps(plans['value-on']))
        plan['functions'].insert(0, {'name': 'wide', 'parameters': [0] * arity, 'result': 0, 'slots': arity,
                                     'body': ['value', 0, 0]})
        return codec.encode(plan, digest)
    room = 2 * (limits['records'] + 1)                  # two words for each of 2^20 + 1 records
    return [
        ('size-at-limit', second + b'\0' * (4 * limits['image_words'] - len(second)), 'HostFailure image: total'),
        ('records-over-limit', names(limits['records'] + 1, room), 'Exhausted 2 records'),
        ('records-beyond-image', names(limits['records'] + 1, 0), 'HostFailure image: record count'),
        ('records-at-limit', names(limits['records'], room), 'HostFailure image: section 5 record length'),
        ('arity-over-limit', wide(limits['arity'] + 1), 'Exhausted 2 arity'),
        ('arity-beyond-record', word_patch(capture, swap + 3, limits['arity'] + 1), 'HostFailure image: function record'),
        ('arity-at-limit', wide(limits['arity']), None),
        ('slots-over-limit', edited('value-on', ['functions', 0, 'slots'], limits['slots'] + 1), 'Exhausted 2 slots'),
        ('closure-slots-over-limit', edited('closure-id', ['functions', 1, 'body', 3, 0, 3], limits['slots'] + 1),
         'Exhausted 2 slots'),
        ('slots-at-limit', edited('value-on', ['functions', 0, 'slots'], limits['slots']),
         'HostFailure image: validator: main: slots 65536, reached 0'),
    ]


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


# ------------------------------------------------------------------ record layout

class Ref(int):
    """A node index standing where the image holds a node record's offset."""


class Layout:
    """A valid image cut into the payload words of its records (the words after each record's length word), with child
    offsets and function roots as `Ref`s. A control changes one record and lays the image out again, every length,
    section offset and node offset recomputed, so that the image breaks exactly one rule."""

    def __init__(self, image: bytes):
        w = [word(image, i) for i in range(len(image) // 4)]
        self.header, self.sections, at = w[:32], [], 32
        for _ in range(6):
            count, at, records = w[at], at + 1, []
            for _ in range(count):
                records.append(w[at + 1:at + w[at]])
                at += w[at]
            self.sections.append(records)
        require(at == len(w), 'a valid image ends with its names')
        starts, cursor = [], w[9] + 1
        for _ in range(w[w[9]]):
            starts.append(cursor)
            cursor += w[cursor]
        index = {start: i for i, start in enumerate(starts)}
        for i, start in enumerate(starts):
            for p in children(w, start):
                if w[p] != codec.NONE:
                    self.sections[4][i][p - start - 1] = Ref(index[w[p]])
        for f in self.functions:
            f[4] = Ref(index[f[4]])

    types = property(lambda self: self.sections[0])
    constructors = property(lambda self: self.sections[1])
    functions = property(lambda self: self.sections[2])
    constants = property(lambda self: self.sections[3])
    nodes = property(lambda self: self.sections[4])
    names = property(lambda self: self.sections[5])

    def insert_node(self, index: int, payload: list):
        """A node record before position `index`; every reference at or beyond it moves up one."""
        for record in self.nodes:
            record[:] = [Ref(x + 1) if isinstance(x, Ref) and x >= index else x for x in record]
        for f in self.functions:
            if f[4] >= index:
                f[4] = Ref(f[4] + 1)
        self.nodes.insert(index, payload)

    def dump(self) -> bytes:
        offsets, at = [], 32
        for records in self.sections:
            offsets.append(at)
            at += 1 + sum(len(r) + 1 for r in records)
        place, cursor = [], offsets[4] + 1
        for r in self.nodes:
            place.append(cursor)
            cursor += len(r) + 1
        out = [*self.header[:2], at, *self.header[3:5], *offsets, *self.header[11:]]
        for records in self.sections:
            out.append(len(records))
            for r in records:
                out += [len(r) + 1, *(place[x] if isinstance(x, Ref) else x for x in r)]
        return b''.join(v.to_bytes(4, 'little') for v in out)


def packed(text: bytes) -> list:
    """The words of a name record's bytes, the last padded with zeros."""
    return [int.from_bytes(text[i:i + 4].ljust(4, b'\0'), 'little') for i in range(0, len(text), 4)]


def structure_controls(images: dict) -> list:
    """(label, bytes, frozen refusal, '') for a golden's image with one record changed so that it breaks one clause of
    SPEC section 2 or 4 (round 13, review findings 1 to 3). Every control changes one record of a valid image and
    breaks one clause, so the reference's refusal names it. A loader that omits the clause admits the image (a name of
    no bytes leaves it valid and canonical) or, where it decides canonicality by encoding the plan again, refuses it as
    `noncanonical` instead (an opaque type with a payload word: a plan does not keep it); the canonicality controls
    break one clause of section 4 step 5 each (`canonical_violations`)."""
    second = images['second']

    def put(section, record, index, value):
        return lambda l: l.sections[section][record].__setitem__(index, value)

    def grow(section, record, *words):
        return lambda l: l.sections[section][record].extend(words)

    def replace(section, record, payload):
        return lambda l: l.sections[section].__setitem__(record, payload)

    def spell(record, text: bytes):
        return replace(5, record, [len(text), *packed(text)])

    def word_of(opcode, index, at):
        return lambda l: l.nodes[next(i for i, n in enumerate(l.nodes) if n[0] == opcode)].__setitem__(index, at)

    def extend_first(opcode, *words):
        return lambda l: l.nodes[next(i for i, n in enumerate(l.nodes) if n[0] == opcode)].extend(words)

    def orphan(l):                                             # a Value that nothing holds
        l.nodes.append([3, 0, 0])

    def standalone(l):                                         # a Default that a function's root names
        l.nodes.append([2, 0, Ref(0)])
        l.functions[0][4] = Ref(1)

    def value_named_by(word_at):
        """`case-on`'s Case, with a Value node before it that its default word (-1) or a row names instead of an arm"""
        def change(l):
            l.insert_node(0, [3, 0, 1])
            l.nodes[5][word_at] = Ref(0)
        return change

    def constant_twice(l):                                     # string-eq's constant, and a copy that the second literal names
        l.constants.append(list(l.constants[0]))
        l.nodes[4][2] = 1

    def constants_swapped(l):                                  # char-code's two constants in the other order
        l.constants[0], l.constants[1] = l.constants[1], l.constants[0]
        l.nodes[5][2], l.nodes[7][2] = 1, 0

    def on_off_swapped(l):                                     # `Off` and `On` swapped in the table, every name word re-pointed
        l.names[2], l.names[3] = l.names[3], l.names[2]
        moved = {2: 3, 3: 2}
        for t in l.types:
            t[1] = moved.get(t[1], t[1]) if t[0] in (0, 3) else t[1]
        for c in l.constructors:
            c[2] = moved.get(c[2], c[2])
        for f in l.functions:
            f[0] = moved.get(f[0], f[0])

    def flag_constructors_swapped(l):                          # Flag's two constructor records, and their names with them
        c = l.constructors
        c[0], c[1] = c[1], c[0]
        l.names[2], l.names[3] = l.names[3], l.names[2]
        c[0][2], c[1][2] = 2, 3

    def pair_operands_swapped(l):                              # the two Values that Pair takes, emitted in the other order
        l.nodes[3], l.nodes[4] = l.nodes[4], l.nodes[3]
        l.nodes[5][4], l.nodes[5][5] = Ref(4), Ref(3)

    def sites(inner, outer):
        return lambda l: (l.nodes[1].__setitem__(2, inner), l.nodes[2].__setitem__(2, outer))

    def key_row_not_branch(l):                                 # default-hit's key 7 becomes 1, and its row a Value typed 1
        l.insert_node(0, [3, 1, 1])
        l.nodes[5][6], l.nodes[5][7] = 1, Ref(0)

    utf8 = lambda label, text: (label, 'second', spell(0, text), 'name utf-8')      # noqa: E731  (Flag, at its own length)
    rows = [
        # names (section 5)
        utf8('name-utf8-overlong-2', b'\xC0\x80ag'),
        utf8('name-utf8-overlong-3', b'\xE0\x80\x80g'),
        utf8('name-utf8-overlong-4', b'\xF0\x80\x80\x80'),
        utf8('name-utf8-surrogate', b'\xED\xA0\x80g'),
        utf8('name-utf8-beyond-unicode', b'\xF4\x90\x80\x80'),
        utf8('name-utf8-lead-f5', b'\xF5\x80\x80\x80'),
        utf8('name-utf8-truncated-inside', b'Fl\xE2\x82'),
        utf8('name-utf8-truncated-before-ascii', b'\xE2\x82ag'),
        utf8('name-utf8-stray-continuation', b'\x80lag'),
        ('name-nul-middle', 'second', spell(2, b'O\0f'), 'name padding'),
        ('name-padding-first', 'second', put(5, 3, 1, int.from_bytes(b'On\x01\0', 'little')), 'name padding'),
        ('name-padding-both', 'second', put(5, 3, 1, int.from_bytes(b'On\x01\x01', 'little')), 'name padding'),
        ('name-length-extra-word', 'second', grow(5, 3, 0), 'name length'),
        ('name-length-missing-word', 'second', lambda l: l.names[4].pop(), 'name length'),
        ('name-empty', 'second', replace(5, 0, [0]), 'name length'),
        ('name-duplicate', 'second', lambda l: l.names.append(list(l.names[0])), 'duplicate name'),
        ('name-index-beyond', 'second', put(1, 0, 2, 6), 'name index'),
        # types (section 0)
        ('type-record-long', 'second', grow(0, 0, 0), 'type record'),
        ('type-kind-unknown', 'second', put(0, 0, 0, 4), 'type record'),
        ('type-record-length-one', 'second', replace(0, 0, []), 'section 0 record length'),
        ('opaque-first-word', 'default-hit', put(0, 0, 2, 1), 'opaque type'),
        ('opaque-second-word', 'default-hit', put(0, 0, 3, 1), 'opaque type'),
        ('arrow-named', 'closure-id', put(0, 1, 1, 0), 'arrow name'),
        ('type-domain-beyond', 'closure-id', put(0, 1, 2, 2), 'type index'),
        ('type-name-beyond', 'second', put(0, 0, 1, 6), 'name index'),
        # constructors (section 1)
        ('constructor-record-short', 'second', replace(1, 0, [0, 0, 2]), 'constructor record'),
        ('constructor-field-count', 'second', put(1, 2, 3, 3), 'constructor record'),
        ('constructor-type-beyond', 'second', put(1, 0, 0, 2), 'constructor record'),
        ('constructor-tag-repeated', 'second', put(1, 1, 1, 0), 'constructor tag'),
        ('constructor-tag-beyond', 'second', put(1, 1, 1, 2), 'constructor tag'),
        ('constructor-of-arrow', 'closure-id', put(1, 0, 0, 1), 'constructor tag'),
        ('constructor-field-type-beyond', 'construct', put(1, 2, 4, 5), 'type index'),
        ('constructor-name-beyond', 'second', put(1, 0, 2, 7), 'name index'),
        # constants (section 3)
        ('constant-kind-unknown', 'default-hit', put(3, 0, 0, 4), 'constant record'),
        ('constant-record-short', 'default-hit', replace(3, 0, [0]), 'constant record'),
        ('constant-record-extra-word', 'default-hit', grow(3, 0, 0), 'constant record'),
        ('constant-scalar-two-words', 'default-hit', replace(3, 0, [0, 2, 7, 8]), 'scalar constant width'),
        ('constant-scalar-empty', 'default-hit', replace(3, 0, [0, 0]), 'scalar constant width'),
        ('constant-string-missing-word', 'string-eq', lambda l: l.constants[0].pop(), 'constant record'),
        ('constant-index-beyond', 'default-hit', put(4, 5, 2, 1), 'constant index'),
        # nodes (section 4): a payload is opcode, type, operands
        ('node-record-short', 'second', replace(4, 0, [5]), 'node record'),
        ('node-record-length-one', 'second', replace(4, 0, []), 'section 4 record length'),
        ('lit-extra-word', 'default-hit', grow(4, 5, 0), 'lit length'),
        ('value-extra-word', 'second', grow(4, 3, 0), 'value length'),
        ('ref-extra-word', 'second', grow(4, 0, 0), 'ref length'),
        ('default-extra-word', 'default-hit', grow(4, 3, 0), 'default length'),
        ('branch-extra-word', 'second', grow(4, 1, 0), 'branch length'),
        ('let-extra-word', 'let', extend_first(7, 0), 'let length'),
        ('con-record-short', 'second', replace(4, 5, [4, 1, 0]), 'con length'),
        ('closure-record-short', 'closure-id', replace(4, 4, [10, 1, 0]), 'closure length'),
        ('con-count-word', 'second', put(4, 5, 3, 1), 'con length'),
        ('call-count-word', 'second', put(4, 6, 3, 2), 'call length'),
        ('prim-count-word', 'string-eq', put(4, 2, 3, 1), 'prim length'),
        ('invoke-count-word', 'closure-id', put(4, 2, 3, 0), 'invoke length'),
        ('foreign-count-word', 'foreign-print', word_of(12, 3, 0), 'foreign length'),
        ('case-count-word', 'case-on', put(4, 4, 5, 3), 'case length'),
        ('case-mode-unknown', 'case-on', put(4, 4, 4, 2), 'case length'),
        ('closure-count-word', 'closure-id', put(4, 4, 5, 1), 'closure length'),
        ('child-shared', 'second', put(4, 5, 5, Ref(3)), 'shared node'),
        ('node-orphan', 'second', orphan, 'unreachable node'),
        ('arm-standalone', 'value-on', standalone, 'standalone arm'),
        ('case-key-row-mismatch', 'default-hit', put(4, 4, 6, 8), 'case key'),
        ('case-key-row-not-branch', 'default-hit', key_row_not_branch, 'case key'),
        ('case-default-not-default', 'case-on', value_named_by(-1), 'case arm kind'),
        ('case-row-not-branch', 'case-on', value_named_by(7), 'case arm kind'),
        # functions (section 2)
        ('function-record-arity', 'second', put(2, 0, 2, 2), 'function record'),
        ('function-record-short', 'second', replace(2, 0, [4, 0, 1, 3]), 'function record'),
        ('function-record-tiny', 'second', replace(2, 0, [4, 0]), 'function record'),
        ('function-root-not-node', 'second', put(2, 0, 4, 0), 'function root'),
        ('function-root-owned', 'second', put(2, 1, 4, Ref(0)), 'function root'),
        ('function-param-type-beyond', 'second', put(2, 0, 5, 5), 'type index'),
        ('function-result-type-beyond', 'second', put(2, 0, 1, 5), 'type index'),
        ('function-name-beyond', 'second', put(2, 0, 0, 9), 'name index'),
        ('node-type-beyond', 'second', put(4, 0, 1, 9), 'type index'),
        # canonicality (section 4 step 5): one clause of `canonical_violations` each
        ('name-unused', 'second', lambda l: l.names.append([3, *packed(b'Zed')]), 'noncanonical'),
        ('names-out-of-order', 'second', on_off_swapped, 'noncanonical'),
        ('constants-duplicate', 'string-eq', constant_twice, 'noncanonical'),
        ('constants-out-of-order', 'char-code', constants_swapped, 'noncanonical'),
        ('constructors-out-of-order', 'second', flag_constructors_swapped, 'noncanonical'),
        ('nodes-out-of-order', 'second', pair_operands_swapped, 'noncanonical'),
        ('closure-site-first', 'closure-nested', sites(7, 1), 'noncanonical'),
        ('closure-site-second', 'closure-nested', sites(0, 8), 'noncanonical'),
        ('closure-sites-swapped', 'closure-nested', sites(1, 0), 'noncanonical'),
        ('closure-sites-from-one', 'closure-nested', sites(1, 2), 'noncanonical'),
        ('arm-type-branch', 'second', put(4, 1, 1, 1), 'noncanonical'),
        ('arm-type-default', 'default-hit', put(4, 3, 1, 0), 'noncanonical'),
    ]

    def laid_out(image, change):
        layout = Layout(images[image])
        change(layout)
        return layout.dump()
    out = [(label, laid_out(image, change), 'HostFailure image: ' + reason, '') for label, image, change, reason in rows]
    header = [(f'registry-digest-word-{i}', word_patch(second, i, word(second, i) ^ 1), 'registry digest') for i in range(25, 32)] + [
        ('length-misaligned', second + b'\0', 'length'),
        ('length-short-header', second[:4 * 31], 'length'),
        ('names-count-beyond-image', word_patch(second, word(second, 10), 7), 'section 5 record length'),
        ('record-overruns-image', word_patch(second, len(second) // 4 - 3, 4), 'section 5 record length'),
        ('main-index-beyond', word_patch(second, 4, 9), 'main index'),
        ('main-index-none', word_patch(second, 4, codec.NONE), 'noncanonical')]
    return out + [(label, data, 'HostFailure image: ' + reason, '') for label, data, reason in header]


# ------------------------------------------------------------------ canonicality as clauses

CANONICAL_CLAUSES = ('main-word', 'names-order', 'names-unused', 'constants-order', 'constants-unused',
                     'constants-duplicate', 'constructors-order', 'nodes-order', 'closure-sites', 'arm-types')


def canonical_violations(image: bytes) -> set:
    """The clauses of section 4 step 5 that a decodable image breaks, read from its own words and never by encoding it
    again: a loader that has no encoder checks these. Each clause is about words that `decode` drops or takes by
    position (the header's main word, the order and the use of names and constants, the order of constructor and node
    records, the sites of Closures, and the result type that a Branch or a Default repeats from its Case), so a
    layout can differ from the canonical one and decode to the same plan."""
    layout = Layout(image)
    bad, none = set(), codec.NONE
    spelled = [b''.join(x.to_bytes(4, 'little') for x in r[1:])[:r[0]] for r in layout.names]
    mains = [i for i, f in enumerate(layout.functions) if spelled[f[0]] == b'main']
    if layout.header[4] != (mains[0] if mains else none):
        bad.add('main-word')

    def first_used(indices):
        seen = []
        for i in indices:
            if i != none and i not in seen:
                seen.append(i)
        return seen
    # names in first-use order over type names, then constructor names, then function names, and every name used
    used = first_used([t[1] for t in layout.types if t[0] in (0, 3)] + [c[2] for c in layout.constructors] +
                      [f[0] for f in layout.functions])
    if used != list(range(len(used))):
        bad.add('names-order')
    if len(used) < len(layout.names):
        bad.add('names-unused')
    # constants in first-use order over the node stream, each used once, none twice
    literal = first_used([n[2] for n in layout.nodes if n[0] == 0])
    if literal != list(range(len(literal))):
        bad.add('constants-order')
    if len(literal) < len(layout.constants):
        bad.add('constants-unused')
    if len({(c[0], *c[2:]) for c in layout.constants}) < len(layout.constants):
        bad.add('constants-duplicate')
    if [(c[0], c[1]) for c in layout.constructors] != sorted((c[0], c[1]) for c in layout.constructors):
        bad.add('constructors-order')
    # nodes in post-order over the function bodies in table order, children in the order of section 3
    stream = []
    for f in layout.functions:
        work = [(f[4], False)]
        while work:
            at, done = work.pop()
            if done:
                stream.append(at)
                continue
            work += [(at, True)] + [(x, False) for x in reversed([x for x in layout.nodes[at][1:] if isinstance(x, Ref)])]
    if stream != list(range(len(layout.nodes))):
        bad.add('nodes-order')
    sites = [n[2] for n in layout.nodes if n[0] == 10]
    if sites != list(range(len(sites))):
        bad.add('closure-sites')
    for n in layout.nodes:
        if n[0] == 8 and any(layout.nodes[x][1] != n[1] for x in n[1:] if isinstance(x, Ref)):
            bad.add('arm-types')
    return bad


def piecewise_rejected(data: bytes, reg: dict, digest: bytes, c=None) -> str | None:
    return rejected(data, reg, digest, c, clauses=True)


def layout_variants(images: dict) -> list:
    """(label, bytes) for seeded random layouts of goldens that decode to the goldens' own plans: names and constants
    permuted, nodes emitted in another order that keeps children before parents, Closure sites renumbered, unused and
    repeated names and constants added, a pair of constructor records swapped, and result types that a Case's arms do not
    repeat. `piecewise_rejected` and `rejected` must agree on each: the clauses are the whole of step 5."""
    rng, out = random.Random(13), []

    def permuted(records, references):
        order = list(range(len(records)))
        rng.shuffle(order)
        moved = [None] * len(records)
        for old, new in enumerate(order):
            moved[new] = records[old]
        records[:] = moved
        references(order)

    def nodes_shuffled(l):
        kids = [[x for x in r[1:] if isinstance(x, Ref)] for r in l.nodes]
        done, order, todo = set(), [], list(range(len(kids)))
        while todo:
            i = rng.choice([j for j in todo if all(k in done for k in kids[j])])
            done.add(i)
            order.append(i)
            todo.remove(i)
        new = {old: at for at, old in enumerate(order)}
        l.nodes[:] = [[Ref(new[x]) if isinstance(x, Ref) else x for x in l.nodes[old]] for old in order]
        for f in l.functions:
            f[4] = Ref(new[f[4]])

    def names_shuffled(l):
        def repoint(order):
            for t in l.types:
                t[1] = order[t[1]] if t[0] in (0, 3) else t[1]
            for c in l.constructors:
                c[2] = order[c[2]]
            for f in l.functions:
                f[0] = order[f[0]]
        permuted(l.names, repoint)

    def constants_shuffled(l):
        def repoint(order):
            for n in l.nodes:
                if n[0] == 0:
                    n[2] = order[n[2]]
        permuted(l.constants, repoint)

    def sites_renumbered(l):
        closures = [n for n in l.nodes if n[0] == 10]
        for n, site in zip(closures, rng.sample(range(12), len(closures))):
            n[2] = site

    def names_added(l):
        l.names.append([3, *packed(bytes([rng.randrange(65, 90)]) * 3)])
        if rng.random() < .3:
            l.names.append(list(l.names[rng.randrange(len(l.names) - 1)]))

    def constant_repeated(l):
        if l.constants:
            l.constants.append(list(l.constants[0]))

    def constructors_swapped(l):
        c = l.constructors
        i = rng.randrange(len(c) - 1)
        if c[i][0] == c[i + 1][0]:
            c[i], c[i + 1] = c[i + 1], c[i]

    def arms_retyped(l):
        for n in l.nodes:
            if n[0] == 8:
                for x in n[1:]:
                    if isinstance(x, Ref) and rng.random() < .5:
                        l.nodes[x][1] = rng.choice([l.nodes[x][1], 0, 1])
    edits = [nodes_shuffled, names_shuffled, constants_shuffled, sites_renumbered, names_added, constant_repeated,
             constructors_swapped, arms_retyped]
    for name in ('second', 'closure-nested', 'default-hit', 'string-eq', 'case-on', 'closure-captures', 'char-code', 'invoke-args'):
        for n in range(60):
            layout = Layout(images[name])
            for edit in rng.sample(edits, rng.randrange(1, 4)):
                edit(layout)
            out.append((f'{name}#{n}', layout.dump()))
    return out


def perturbations(images: dict) -> list:
    """(label, bytes) for every word of a few goldens set to its neighbours, 0, 1, 2 and none: most are refused for
    another reason, and the rest are the images whose canonicality the clauses must decide as re-encoding does."""
    out = []
    for name in ('second', 'closure-nested', 'default-hit', 'string-eq', 'case-on', 'closure-captures', 'char-code'):
        image = images[name]
        for i in range(len(image) // 4):
            here = word(image, i)
            for value in sorted({(here + 1) & 0xFFFFFFFF, (here - 1) & 0xFFFFFFFF, 0, 1, 2, codec.NONE} - {here}):
                out.append((f'{name}[{i}]={value}', word_patch(image, i, value)))
    return out


def canonical_differential(images: dict, controls: list, admitted: list, reg: dict, digest: bytes) -> dict:
    """Section 4 step 5 as clauses, held against re-encoding. Every frozen control, admitted image, golden, layout
    variant and perturbation is decided both ways and the two must give one answer, so the clauses are the whole of step 5
    on this corpus; and each clause has a frozen control that breaks it alone, so that a loader without the clause
    admits an image (`piecewise_rejected` without the clause, in the rule mutants)."""
    corpus = [(label, data) for label, data, _, _ in controls] + admitted + [(f'golden {k}', d) for k, d in images.items()] + \
        layout_variants(images) + perturbations(images)
    decided = {'noncanonical': 0, 'admitted': 0}
    for label, data in corpus:
        reencoded, clauses = rejected(data, reg, digest), piecewise_rejected(data, reg, digest)
        require(reencoded == clauses, f'{label}: encoding again gives {reencoded!r}, the clauses give {clauses!r}')
        decided['noncanonical'] += reencoded == 'HostFailure image: noncanonical'
        decided['admitted'] += reencoded is None
    require(all(decided.values()), f'the corpus must hold canonical and noncanonical images: {decided}')
    alone = {clause: [] for clause in CANONICAL_CLAUSES}
    for label, data, reason, _ in controls:
        if reason.endswith('noncanonical'):
            broken = canonical_violations(data)
            if len(broken) == 1:
                alone[next(iter(broken))].append(label)
    require(all(alone.values()), f'a canonicality clause with no control that breaks it alone: {alone}')
    return {'corpus': len(corpus), **decided, 'controls_by_clause': alone}


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
    key_row, case_rows = plans['default-hit']['functions'][0]['body'][5][0], plans['case-on']['functions'][0]['body'][5]
    flag = {'kind': 'data', 'name': 'Flag', 'constructors': [{'name': 'Off', 'fields': []}, {'name': 'On', 'fields': []}]}
    duo = {'kind': 'data', 'name': 'Duo', 'constructors': [{'name': 'Lo', 'fields': []}, {'name': 'Hi', 'fields': []}]}

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
        # Rules of sections 2-4 that no control refused (review of round 9, finding 4): each control
        # breaks one rule of a golden plan, and its frozen message is the validator's first.
        ('function-index', edit('reference', [*body(1), 2], 9), 'function index'),
        ('case-slot-beyond-depth', edit('case-on', [*body(0), 2], 3), 'case slot beyond depth'),
        ('construct-tag', edit('pair', [*body(0), 2], 3), 'construct tag'),
        ('construct-field-type', edit('construct', ['types', 1, 'constructors', 0, 'fields', 0], 1), 'construct field type'),
        ('branch-key', edit('case-on', [*body(0), 5, 0, 1], 1), 'branch key'),
        ('key-branch-binds-field', edit('case-char', [*body(0), 5, 0, 3], 1), 'key branch binds nothing'),
        ('closure-arrow', edit('closure-id', [*body(1), 3, 0, 2], 0), 'closure arrow'),
        ('invoke-types', edit('closure-id', [*body(0), 1], 1), 'invoke types'),
        ('closure-result-type', edit('closure-nested', [*body(0), 5, 1], 2), 'closure result type'),
        ('let-body-type', edit('closure-shadow', [*body(0), 4, 1], 1), 'let body type'),
        ('body-type', edit('pair', ['functions', 0, 'result'], 0), 'body type'),
        ('u32-not-opaque', edit('u32-zero', ['representation', 'U32'], 0), 'U32 must be opaque'),
        ('file-not-opaque', edit('value-on', ['representation'], {'File': 0}), 'File must be opaque'),
        ('duplicate-function-name', edit('reference', ['functions', 1, 'name'], 'id'), 'duplicate function name'),
        # Round 13, review finding 1: the conditions of section 4 step 4 that a one-condition mutant admitted. A keys row
        # repeats (a first-match scan and a binary search would answer differently), a Construct names a nullary
        # constructor (a Value's job, and the Object it allocates has no field for section 6 to inspect), an Invoke passes
        # the other number of operands than its arrow kind takes (a live arrow one, an erased arrow none), a Case's slot
        # and its scrutinee are two different concrete types, and a Closure captures a slot twice.
        ('keys-repeated', edit('default-hit', [*body(0), 5], [key_row, json.loads(json.dumps(key_row))]),
         'keys must increase strictly'),
        ('construct-nullary', edit('value-on', body(0), ['con', 0, 1, []]), 'construct arity'),
        ('invoke-live-without-argument', edit('closure-id', [*body(0), 3], []), 'invoke arity'),
        ('invoke-live-two-arguments', edit('closure-id', [*body(0), 3], [['ref', 0, 1], ['ref', 0, 1]]), 'invoke arity'),
        ('invoke-erased-with-argument', edit('book-drop', [*body(2), 3, 0, 2, 3], [['value', 8, 1]]), 'invoke arity'),
        ('case-slot-type-mismatch', edits('case-on', (['types'], [flag, duo]), ([*body(0), 3], 1)), 'case scrutinee type'),
        ('captures-repeated', edit('closure-captures', [*body(0), 3, 4], [0, 0]), 'captures must increase strictly'),
        # Review finding 2: statements that no control pinned. Each control keeps every other rule, so a validator that
        # omits the statement admits it: a Case tags a type that has no constructors, keys a Flag, or leaves a Flag's
        # table short.
        ('tag-case-on-opaque', edits('default-hit', ([*body(0), 4], 'tags'), ([*body(0), 5], []), ([*body(0), 6], None)),
         'tag case on a non-data type'),
        ('key-case-on-flag', edits('case-on', ([*body(0), 4], 'keys'), ([*body(0), 6], ['default', ['value', 0, 0]])),
         'key case on a non-scalar type'),
        ('tag-table-not-dense', edit('case-on', [*body(0), 5], case_rows[:1]), 'tag table is not dense'),
        # The clauses that a test joins, each broken alone (the statement's other controls break another): a table that is
        # too long, a representation that names an arrow, a Program with no `main`, a Value of a tag beyond its type or of
        # a type with no constructors, a Construct of an arrow, a call or an Invoke whose operand does not fit, a capture
        # beyond the depth, a key row whose first slot is not the depth, a closure that names a data type, and an Invoke of
        # a data type.
        ('tag-table-too-long', edit('case-on', [*body(0), 5], [*case_rows, ['branch', 2, 1, 0, ['value', 0, 0]]]),
         'tag table is not dense'),
        ('representation-of-arrow', edit('closure-id', ['representation'], {'Bool': 1}), 'Bool shape'),
        ('program-without-main', edit('foreign-print', ['functions', 1, 'name'], 'entry'), 'main must exist with no live parameters'),
        ('value-tag-beyond', edit('value-on', [*body(0), 2], 5), 'value is not a nullary constructor'),
        ('value-of-opaque', edit('default-hit', [*body(0), 6, 1, 1], 0), 'value is not a nullary constructor'),
        ('construct-of-arrow', edits('pair', (['types'], [*plans['pair']['types'], {'kind': 'arrow', 'domain': 0, 'result': 0}]),
                                     ([*body(0), 1], 2)), 'construct tag'),
        ('call-operand-type', edit('keep-swapped', ['functions', 1, 'parameters', 0], 0), 'call types'),
        ('invoke-argument-type', edit('closure-id', [*body(0), 3], [['ref', 1, 0]]), 'invoke types'),
        ('capture-beyond-depth', edit('closure-captures', [*body(0), 3, 4], [0, 5]), 'captures must increase strictly'),
        ('key-branch-first-slot', edit('default-hit', [*body(0), 5, 0, 2], 2), 'key branch binds nothing'),
        ('closure-erased-at-data-type', edits('closure-id', ([*body(1), 3, 0, 1], 0), ([*body(1), 3, 0, 2], 0)), 'closure arrow'),
        ('invoke-non-arrow-without-argument', edits('closure-id', ([*body(0), 2], ['ref', 0, 1]), ([*body(0), 3], [])),
         'invoke arity'),
        # Finding 3, the admit side: a name is any well-formed UTF-8 of section 2, at every length and at every edge of
        # a length, so a loader that refuses non-ASCII names, or one length of them, is refused by an admitted control.
        ('name-utf8-lengths', edit('value-on', ['types', 0, 'name'], '$\u00a2\u20ac\U00010348'), None),
        ('name-utf8-edges', edit('value-on', ['types', 0, 'name'],
                                 '\u0080\u07ff\u0800\ud7ff\ue000\uffff\U00010000\U0010ffff'), None),
    ]


# first_code as the literals head's check-cli would display it: type 0 Bool, 1 U32, 2 List;
# the Con head binder `1 $1:1` carries the core's instantiated U32. No pinned head checks a
# List<U32> parameter (`Unsupported parse parameter-type`), so the text is written by hand.
FIRST_CODE_DISPLAY = """Checked
U32.is_eq(1:1,1:1)->0=U32.is_eq($0:1;$1:1)
first_code(1:2)->1=case $0 [0=>v1.0;1(1 $1:1;1 $2:2;)=>$1:1]
main()->0=call0(call1(v2.1{v1.7;v2.0});v1.7)
"""


# list_head_match as the literals head's check-cli would display it were a `List<Flag>` parameter
# checked: type 0 Bool, 1 List, 2 Flag, the Con head binder `1 $1:2` carrying the core's Flag and
# the plan typing its slot by List's pinned `none` field. It follows the display that check-cli
# does print for the same source over a monomorphic list, `first_on(1:2)->0=case $0 [...]`.
LIST_HEAD_MATCH_DISPLAY = """Checked
first_on(1:1)->0=case $0 [0=>v0.0;1(1 $1:2;1 $2:1;)=>case $1 [0=>v0.0;1=>v0.1]]
main()->0=call0(v1.1{v2.1;v1.0})
"""


def lowered_controls(planned: list, plans: dict, reg: dict) -> list:
    """The display cross-check follows section 3's typing: a Branch slot takes the pinned
    field (`none`), not the core binder's U32, and a Case takes its position's type, not
    its last arm's. The lowering of FIRST_CODE_DISPLAY is the admitted plan `first-code`, and
    that of LIST_HEAD_MATCH_DISPLAY the admitted plan `list-head-match`, which is also the plan
    of the golden of that name."""
    out = []
    for label, display in (('first-code', FIRST_CODE_DISPLAY), ('list-head-match', LIST_HEAD_MATCH_DISPLAY)):
        plan = next(p for name, p, _ in planned if name == label)
        derived = from_display(display, plan, '', reg)
        require(derived == plan['functions'], (f'{label}: lowering differs from the admitted plan', derived))
        out.append(label)
    require(plans['list-head-match'] == next(p for name, p, _ in planned if name == 'list-head-match'),
            'the golden list-head-match is the admitted plan')
    return out


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
    return [*controls, *display_controls(), *fuel_controls({**plans, **{label: p for label, p, _ in controls}}),
            *inspection_controls(plans), *effect_controls(plans), *key_controls(plans)]


def effect_controls(plans: dict) -> list:
    """Effects, by literal review of sections 6, 7, 8 and 10 (D23). An Action applied to its continuation
    builds a request and performs nothing; only Top's loop performs the request that a run returns to it,
    after which it enters `k`, and a request that any read of section 6 meets stops the run
    `Unsupported vm effect`. Building an Action, dropping it, applying it to its erased R (the first
    application) and dropping a request perform nothing. `got` returns what an IO.OP carries, and
    `printing(t)` is `IO.print(t)` applied to R and then to a continuation: main, IO.print, R and the
    Action, whose application builds the request, are 4 entries, 5 when an `id` call builds the String
    first. A Book has no loop, so no operand is read, converted or checked for D20 and no host is called:
    the first read of the request is `got`'s Case, one entry after it is built, so `book-print` stops after
    5 entries and `book-print-ill-typed` after 6. Every Book control that stops at a request freezes
    `stdout` empty and `effects` 0, and a `print` that wrote and then refused would differ by its
    `stdout`. `effects` counts the host calls the reference evaluation makes (a request's effect, at
    the loop after D20's check, just before its write), so it also shows a call that writes nothing:
    `IO.args` under a Book, whose request is built and refused like any other whatever its foreign id.
    - The debit is the application's: `book-print` completes its refusal with fuel 5, its debited
      entries; at fuel 4 its `got` meets fuel 0 and stops `Exhausted` kind 1 after 4
      (`fuel-book-request-short`); and at fuel 3 the Action's second application does, after 3.
    - A request is dropped, and no effect follows, wherever it is held: a Book's let, an Emit's field, a
      Program's let, an argument of a call (keep-swapped's plan) and a String that the loop never reads.
      The Program that returns the other request performs it: `kept\n` or `live\n`, effects 1. The controls
      built by `entered` and `halting` have `main` = `λ@R. λk. body`, a form on which the seed crashes (the
      witnesses main-lambda-*): they are literal review and no seed claim. Their seed-witnessed analogues have a
      call-shaped `main` and are goldens: let-dropped-request, emit-field-request-dropped, keep-non-scalar and
      keep-swapped, whose plan is `program-request-dropped-argument`.
    - Under a Program the same Action prints, and where it meets `k` may lie in an argument of a
      call: `run(m) = λ@R. λk. id(m(R)(k))` passes the answer of `IO.print("x")(R)(k)` through
      `id`. The pinned seed writes `x` for that source on both lanes; main, IO.print, run, R,
      run's closure, the Action twice, the terminal continuation and id are 9 entries. The seed
      refuses the shape that a Case reads the answer of (`got(IO.print("x")(R)(k))`, its own
      test request_out_of_band.bend), and D23 refuses it as well: `program-case-request`, and the
      reads that a request meets in a Book (`inspect-request-*`, `book-request-rendered`, `-field`
      and `enter-request-target`), each `Unsupported vm effect` and never ill-typed. A Case with a
      Default takes it (D24), as the seed's native lane does: beside an Emit row, a Halt row or no row
      (`program-case-request-emit-default`, `-halt-default`, `-default-only`), each ends exit 0 after the same 7
      entries with nothing written and no effect, since the request is never read or performed; at any scrutinee
      type (`case-request-default-at-flag`, a Book), and in either mode (`case-request-default-keys`, a Book: a keys
      Case has a Default always). The goldens `case-request-emit-default-u32` (`2`),
      `case-request-halt-default-u32` (`4`) and `case-request-emit-default` freeze the seed's values. A Case
      without a Default, a tags Case whose every row names a constructor (`program-case-request`), still refuses
      the request.
    - A scalar String is written as canonical UTF-8 (section 10): `foreign-print`'s plan prints the four
      examples of each length (U+0024, U+00A2, U+20AC, U+10348) and the edges of every length
      (U+007F, U+0080, U+07FF, U+0800, U+D7FF, U+E000, U+FFFF, U+10000, U+10FFFF), after 5 entries.
    - A Halt's message is an outgoing String (D20): a lone surrogate in it stops the run as
      `HostFailure io abi` before `die`, at the third entry (main, R, k's closure). A scalar one,
      `x` and U+1F600, reaches `die` after the same 3 entries, so the run ends with `halt` 1 and
      that `message`, which the reference evaluation reports as values; a `die` that refused every
      message, or every one above ASCII, would differ."""
    fp, flag = plans['foreign-print'], plans['value-on']['types'][0]
    types = [*fp['types'], flag, {'kind': 'arrow', 'domain': 8, 'result': 8}]   # 8 Flag, 9 Flag -> Flag
    print_, got, ident, resume, through = 0, 1, 2, 3, 4
    functions = [
        {'name': 'IO.print', 'parameters': [3], 'result': 7, 'slots': 1, 'body': ['foreign', 7, 1, [['ref', 3, 0]]]},
        {'name': 'got', 'parameters': [4], 'result': 8, 'slots': 3, 'body': ['case', 8, 0, 4, 'tags', [
            ['branch', 0, 1, 1, ['ref', None, 1]], ['branch', 1, 1, 2, ['value', 8, 0]]], None]},
        {'name': 'id', 'parameters': [None], 'result': None, 'slots': 1, 'body': ['ref', None, 0]},
        {'name': 'k', 'parameters': [0], 'result': 4, 'slots': 1, 'body': ['con', 4, 0, [['value', 8, 1]]]}]

    def image(entry, body, slots=0, *more, result=None):
        result = result or (7 if entry == 'program' else 8)
        return {'entry': entry, 'representation': fp['representation'], 'types': types,
                'functions': [*functions, *more, {'name': 'main', 'parameters': [], 'result': result, 'slots': slots, 'body': body}]}

    def text(s):
        return ['lit', 3, 'String', [ord(c) for c in s]]
    inline = ['closure', 5, 1, 1, [], ['con', 4, 0, [['value', 8, 1]]]]            # u => Emit{On{}}
    calling = ['closure', 5, 1, 1, [], ['call', 4, resume, [['ref', 0, 0]]]]        # u => k(u)

    def printing(string, k=inline):
        return ['invoke', 4, ['invoke', 6, ['call', 7, print_, [string]], []], [k]]

    def bound(*string_and_k):
        return ['call', 8, got, [printing(*string_and_k)]]
    laundered = ['con', 3, 1, [['lit', 2, 'Char', 97], ['call', 3, ident, [['closure', 9, 1, 1, [], ['ref', 8, 0]]]]]]
    on = 'Evaluated\t8\t1\tOn{}\n'
    # IO.args (foreign 0) is IO(List<String>): a List of Strings' continuation type 11, applied to 12.
    args_types = [{'kind': 'data', 'name': 'List', 'constructors': [{'name': 'Nil', 'fields': []}, {'name': 'Con', 'fields': [None, 10]}]},
                  {'kind': 'arrow', 'domain': 10, 'result': 4}, {'kind': 'arrow', 'domain': 11, 'result': 4},
                  {'kind': 'erased-arrow', 'domain': None, 'result': 12}]
    args = {'name': 'IO.args', 'parameters': [], 'result': 13, 'slots': 0, 'body': ['foreign', 13, 0, []]}
    listed = ['invoke', 4, ['invoke', 12, ['call', 13, 4, []], []], [['closure', 11, 1, 1, [], ['con', 4, 0, [['value', 8, 1]]]]]]
    # run(m: IO(Unit)) = λ@R. λk. id(m(R)(k)): the Action meets k inside an argument of a call, and the
    # IO.OP it answers only passes through id. Slots: m is 0, k 1; both closures capture m.
    running = {'name': 'run', 'parameters': [7], 'result': 7, 'slots': 1, 'body': [
        'closure', 7, 0, 1, [0], ['closure', 6, 1, 2, [0], ['call', 4, ident, [
            ['invoke', 4, ['invoke', 6, ['ref', 7, 0], []], [['ref', 5, 1]]]]]]]}

    def halting(message):
        """main = λ@R. λk. Halt{1, message}"""
        return ['closure', 7, 0, 0, [], ['closure', 6, 1, 1, [], ['con', 4, 1, [['lit', 1, 'U32', 1], message]]]]

    def printing_codes(codes):
        """foreign-print's plan, printing a String of these Chr codes"""
        plan = json.loads(json.dumps(fp))
        plan['functions'][1]['body'][3][0][3] = codes
        return plan
    # The canonical UTF-8 examples, and each length's boundary; Python's own encoder is the literal review.
    lengths, edges = [0x24, 0xA2, 0x20AC, 0x10348], [0x7F, 0x80, 0x7FF, 0x800, 0xD7FF, 0xE000, 0xFFFF, 0x10000, 0x10FFFF]
    # D23, by literal review of sections 6, 7, 8 and 10: the Action's second application builds a request and is
    # debited, nothing reads the request or its operands until the Top loop performs it, and a run that returns
    # no request to the loop performs nothing. `request` is IO.print("x")(R)(k): main, IO.print, R and the
    # Action applied to k are 4 entries, and each further call is one more. A Program's main is
    # λ@R. λk. body, entered as main, phase 1's R and phase 2's closure (3 entries) with k as slot 0.
    keep = {'name': 'keep', 'parameters': [4, 4], 'result': 4, 'slots': 2, 'body': ['ref', 4, 1]}    # keep(x, y) = y
    add = {'name': 'U32.add', 'parameters': [1, 1], 'result': 1, 'slots': 2,
           'body': ['prim', 1, 0, [['ref', 1, 0], ['ref', 1, 1]]]}
    pick = {'name': 'pick', 'parameters': [None], 'result': 8, 'slots': 1, 'body': [
        'case', 8, 0, 1, 'keys', [['branch', 7, 1, 0, ['value', 8, 1]]], ['default', ['value', 8, 0]]]}
    pair = {'kind': 'data', 'name': 'Pair', 'constructors': [{'name': 'Pair', 'fields': [8, 8]}]}      # type 10

    def defaulted(name, rows, slots):
        """`got` with a Default beside these rows: one Flag per arm, Off{} from the Default"""
        return {'name': name, 'parameters': [4], 'result': 8, 'slots': slots,
                'body': ['case', 8, 0, 4, 'tags', rows, ['default', ['value', 8, 0]]]}
    emit_default = defaulted('got-emit-default', [['branch', 0, 1, 1, ['value', 8, 1]], None], 2)
    halt_default = defaulted('got-halt-default', [None, ['branch', 1, 1, 2, ['value', 8, 1]]], 3)
    default_only = defaulted('got-default-only', [None, None], 1)
    request, k_ref = printing(text('x')), ['ref', 5, 0]
    unsupported = {'outcome': 'Unsupported', 'cause': 'vm effect', 'stdout': '', 'effects': 0}
    quiet = {'exit': 0, 'stdout': '', 'effects': 0}
    pick_default = {'name': 'pick-default', 'parameters': [None], 'result': 8, 'slots': 1, 'body': [
        'case', 8, 0, 8, 'tags', [None, ['branch', 1, 1, 0, ['value', 8, 1]]], ['default', ['value', 8, 0]]]}

    def through_id(node, t):
        return ['call', t, ident, [node]]

    def entered(body, slots=1, *more):
        """main = λ@R. λk. body, k being slot 0 of the inner closure and `slots` its depth"""
        return image('program', ['closure', 7, 0, 0, [], ['closure', 6, 1, slots, [], body]], 0, *more)
    return [
        ('book-print', image('book', bound(text('x'))), {**unsupported, 'calls': 5}),
        ('book-print-continuation-call', image('book', bound(text('x'), calling)), {**unsupported, 'calls': 5}),
        ('book-print-twice', image('book', ['let', 8, 0, bound(text('y')), bound(text('x'))], 1),
         {**unsupported, 'calls': 5}),
        ('book-print-non-scalar', image('book', bound(['lit', 3, 'String', [0xD800]])),
         {**unsupported, 'calls': 5}),
        ('book-print-ill-typed', image('book', bound(laundered)), {**unsupported, 'calls': 6}),
        ('book-args', {**image('book', ['call', 8, got, [listed]], 0, args), 'types': [*types, *args_types],
                       'representation': {**fp['representation'], 'List': 10}}, {**unsupported, 'calls': 5}),
        ('fuel-book-effect-exact', image('book', bound(text('x'))), {'fuel': 5, **unsupported, 'calls': 5}),
        ('fuel-book-effect-short', image('book', bound(text('x'))),
         {'fuel': 3, 'outcome': 'Exhausted', 'kind': 1, 'cause': 'fuel', 'stdout': '', 'effects': 0, 'calls': 3}),
        ('book-continuation-called', image('book', ['call', 8, got, [['call', 4, resume, [['value', 0, 0]]]]]),
         {'exit': 0, 'stdout': on, 'calls': 3}),
        ('book-action-dropped', image('book', ['let', 8, 0, ['call', 7, print_, [text('x')]], ['value', 8, 1]], 1),
         {'exit': 0, 'stdout': on, 'calls': 2}),
        ('book-action-erased', image('book', ['let', 8, 0, ['invoke', 6, ['call', 7, print_, [text('x')]], []], ['value', 8, 1]], 1),
         {'exit': 0, 'stdout': on, 'calls': 3}),
        ('program-print-through-id', image('program', ['call', 7, through, [['call', 7, print_, [text('x')]]]], 0, running),
         {'exit': 0, 'stdout': 'x\n', 'calls': 9}),
        ('halt-surrogate', image('program', halting(['lit', 3, 'String', [0xD800]])),
         {'outcome': 'HostFailure', 'cause': 'io abi', 'stdout': '', 'calls': 3}),
        ('halt-scalar', image('program', halting(['lit', 3, 'String', [0x78, 0x1F600]])),
         {'halt': 1, 'message': [0x78, 0x1F600], 'stdout': '', 'calls': 3}),
        ('print-utf8-lengths', printing_codes(lengths), {'exit': 0, 'stdout': ''.join(map(chr, lengths)) + '\n', 'calls': 5}),
        ('print-utf8-boundaries', printing_codes(edges), {'exit': 0, 'stdout': ''.join(map(chr, edges)) + '\n', 'calls': 5}),
        # A request built and dropped is no effect and no error, whatever holds it: a Book's let (4 entries),
        # an Emit's field (6), a Program's let (the dead request is 3 of 10 entries, the live one prints) and
        # an argument of a call that answers the other request (keep-swapped's plan, 12 entries).
        ('book-request-dropped', image('book', ['let', 8, 0, request, ['value', 8, 1]], 1),
         {'exit': 0, 'stdout': on, 'effects': 0, 'calls': 4}),
        ('program-request-in-emit', entered(['con', 4, 0, [request]]), {'exit': 0, 'stdout': '', 'effects': 0, 'calls': 6}),
        ('program-request-dropped-let',
         entered(['let', 4, 1, printing(text('dead')), printing(text('live'), k_ref)], 2),
         {'exit': 0, 'stdout': 'live\n', 'effects': 1, 'calls': 10}),
        ('program-request-dropped-argument', plans['keep-swapped'], {'exit': 0, 'stdout': 'kept\n', 'effects': 1, 'calls': 12}),
        # The loop reads a request's operands only when it performs it, so a dropped request may hold an ill-typed
        # String (laundered: 12 entries, `kept\n`), as the seed's dropped non-scalar print is no D20 refusal.
        ('program-request-dropped-ill-typed',
         entered(['call', 4, 4, [printing(laundered), printing(text('kept'), k_ref)]], 1, keep),
         {'exit': 0, 'stdout': 'kept\n', 'effects': 1, 'calls': 12}),
        # A request is never inspected: a Case over it (the seed fail-stops, request_out_of_band.bend), a
        # rendered root or field, an operand, a key and an Enter's target each stop `Unsupported vm effect`,
        # before any ill-typed check and, for the Enter, before the debit.
        ('program-case-request', entered(['con', 4, 0, [['call', 8, got, [printing(text('x'), k_ref)]]]]),
         {**unsupported, 'calls': 7}),
        # D24: a request matches no constructor row, so a Case with a Default takes the Default, whatever rows it
        # has: an Emit row or a Halt row beside it, or no row at all (the same 7 entries: main, IO.print, R, the
        # Action, k, `got-*`; the Default's Flag goes into an Emit, whose field is unread, so the run ends exit 0
        # with nothing written and no effect: the request is never read or performed). The seed's native lane
        # takes the Default of the first two and both lanes run the third without reading the request; the Bun lane
        # fail-stops on a constructor row (the goldens case-request-*, which freeze the values `2` and `4`).
        ('program-case-request-emit-default',
         entered(['con', 4, 0, [['call', 8, 4, [printing(text('x'), k_ref)]]]], 1, emit_default), {**quiet, 'calls': 7}),
        ('program-case-request-halt-default',
         entered(['con', 4, 0, [['call', 8, 4, [printing(text('x'), k_ref)]]]], 1, halt_default), {**quiet, 'calls': 7}),
        ('program-case-request-default-only',
         entered(['con', 4, 0, [['call', 8, 4, [printing(text('x'), k_ref)]]]], 1, default_only), {**quiet, 'calls': 7}),
        # The Default is taken at any scrutinee type: `pick_default` names Flag for the `none` word that
        # `id` hands it, a request, and answers Off{} from its Default (6 entries: main, IO.print, R, the Action, id,
        # pick_default); the keys Case of `case-request-default-keys` below takes its Default too (a keys Case has one).
        ('case-request-default-at-flag', image('book', ['call', 8, 4, [through_id(request, None)]], 0, pick_default),
         {'exit': 0, 'stdout': 'Evaluated\t8\t0\tOff{}\n', 'effects': 0, 'calls': 6}),
        ('book-request-rendered', image('book', through_id(request, 8)), {**unsupported, 'calls': 5}),
        ('book-request-field',
         {**image('book', ['con', 10, 0, [['value', 8, 1], through_id(request, 8)]], 0, result=10), 'types': [*types, pair]},
         {**unsupported, 'calls': 5}),
        ('inspect-request-chr', image('book', ['let', 8, 0, ['con', 2, 0, [through_id(request, 1)]], ['value', 8, 1]], 1),
         {**unsupported, 'calls': 5}),
        ('inspect-request-prim',
         image('book', ['let', 8, 0, ['call', 1, 4, [through_id(request, 1), ['lit', 1, 'U32', 1]]], ['value', 8, 1]], 1, add),
         {**unsupported, 'calls': 6}),
        ('case-request-default-keys', image('book', ['call', 8, 4, [through_id(request, None)]], 0, pick),
         {'exit': 0, 'stdout': 'Evaluated\t8\t0\tOff{}\n', 'effects': 0, 'calls': 6}),
        ('inspect-request-print',
         entered(printing(['con', 3, 1, [['lit', 2, 'Char', 97], through_id(printing(text('y')), 3)]], k_ref)),
         {**unsupported, 'calls': 10}),
        ('enter-request-target', image('book', ['invoke', 8, through_id(request, 9), [['value', 8, 1]]]),
         {**unsupported, 'calls': 5}),
        # The class check precedes the fuel test at an Enter, as the operand check does (fuel-zero-ill-typed-invoke):
        # with fuel 5 the Invoke of the request meets fuel 0, and is refused, not exhausted.
        ('fuel-zero-request-target', image('book', ['invoke', 8, through_id(request, 9), [['value', 8, 1]]]),
         {'fuel': 5, **unsupported, 'calls': 5}),
        # The Action's application is debited, and the loop's k after it: at fuel 4 book-print's got is entered
        # with fuel 0, after the 4 entries that built the request.
        ('fuel-book-request-short', image('book', bound(text('x'))),
         {'fuel': 4, 'outcome': 'Exhausted', 'kind': 1, 'cause': 'fuel', 'stdout': '', 'effects': 0, 'calls': 4}),
    ]


def key_controls(plans: dict) -> list:
    """Section 2 and 3: in a Case record `none` marks only an absent tag row or an absent default,
    and a key is any u32, 0xffffffff included. `pick(x)` answers On{} from a key Branch at
    0xffffffff and Off{} from its Default, at U32 and at Char (pure Char admits every u32); each
    run is main and pick, 2 entries. A key that matches is not absent, and one that misses is
    not a wildcard."""
    flag = plans['value-on']['types'][0]
    u32, char = {'kind': 'opaque', 'name': 'U32'}, plans['char-code']['types'][2]

    def book(scalar, argument):
        """pick(x: <scalar>) with a key Branch at 0xffffffff, applied to `argument`."""
        return {'entry': 'book', 'representation': {'U32': 1, 'Char': 2}, 'types': [flag, u32, char],
                'functions': [{'name': 'pick', 'parameters': [scalar], 'result': 0, 'slots': 1,
                               'body': ['case', 0, 0, scalar, 'keys', [['branch', 0xFFFFFFFF, 1, 0, ['value', 0, 1]]],
                                        ['default', ['value', 0, 0]]]},
                              {'name': 'main', 'parameters': [], 'result': 0, 'slots': 0,
                               'body': ['call', 0, 0, [['lit', scalar, 'U32' if scalar == 1 else 'Char', argument]]]}]}
    hit, miss = ('Evaluated\t0\t1\tOn{}\n', 'Evaluated\t0\t0\tOff{}\n')
    return [
        ('key-max', book(1, 0xFFFFFFFF), {'exit': 0, 'stdout': hit, 'calls': 2}),
        ('key-max-miss', book(1, 0xFFFFFFFE), {'exit': 0, 'stdout': miss, 'calls': 2}),
        ('char-key-max', book(2, 0xFFFFFFFF), {'exit': 0, 'stdout': hit, 'calls': 2}),
    ]


def inspection_controls(plans: dict) -> list:
    """Section 6's inspection points and section 9's extents, by literal review. A generic
    `id` (parameter and result `none`) delivers a closure, or a Pair Object, to a position
    typed Nat, U32, Char or String; the first read of that word halts with HostFailure image
    (`ill-typed`), and a `let` discards every other result, so only the read can halt.
    - Construction is free: a Succ or Chr halts after 2 calls (main, id).
    - A prim sits in its Base function: 3 calls (main, id, the function). A moved operand is
      read like any other. A String is read whole, each cell and its Char word: `append`
      reads the `b` it moves and the Chars of the `a` it copies, `length` and `reverse` each
      Char, `is_empty` past its first cell, and `eq` past a differing code and past either
      list's end.
    - A Program's Halt with a closure for its code or its message's tail halts after 4 (main,
      the erased R, k's closure, id). IO.print of a surrogate followed by a closure halts
      after 5 (main, id, IO.print, both applications of the Action), writing nothing: the
      whole String is read before the scalar check, so the cause is not `io abi`. A Halt's
      message is an outgoing String too: a surrogate then a closure halts `ill-typed` after 4,
      and so does a closure code beside a surrogate message, the code being read first.
    - A Case reads its scrutinee at the Case's type (section 6.1). `pick(x: none)` cases on
      the word that `id` hands it: 3 calls (main, id, pick). A closure is no Flag, Nat, Char, U32
      or Pair; nor is the Object of another type (a Box, whose tag 0 also has fields), nor an
      immediate beyond the constructors (5 at a Flag). Key mode reads a U32 or a Char the same way.
    - Every prim reads each operand (section 9), a second one as well as a first: the word
      prims through U32.add (its first), U32.sub (its second), U32.shln (its Nat amount),
      Char.is_space, Char.is_eq (its second), Nat.add, Nat.sub (its second) and both show
      prims, each after 3 calls. The other ids of a family are vm-prims' to witness (section 9).
    - An Enter checks its target (section 7): an immediate or an Object handed to an Invoke halts
      after 2 calls (main, id). The Action's continuation is entered after its effect: a Program
      whose Action meets an immediate for `k` writes `x`, then halts after 7 calls (main, the two
      closures, IO.print, the erased R, id, the Action's second application), the target being read
      when its Enter comes and not before the effect. The last word is read too: a Program whose
      k answers a closure, or an immediate, for its IO.OP halts after 4 (main, the erased R, k's
      closure, id) writing nothing.
    - Rendering reads every word (section 8): a Book result that is a closure, or a Pair whose
      field is one, halts after 2 (main, id)."""
    nat, u32, char, string, boolean, flag, pair, arrow = range(8)
    types = [*plans['string-codes']['types'][:4], plans['string-eq']['types'][0], plans['value-on']['types'][0],
             {'kind': 'data', 'name': 'Pair', 'constructors': [{'name': 'Pair', 'fields': [flag, flag]}]},
             {'kind': 'arrow', 'domain': flag, 'result': flag}]
    rep = {'Nat': nat, 'U32': u32, 'Char': char, 'String': string, 'Bool': boolean}
    prims = {p['id']: p for p in codec.registry()['prims']}
    ident = {'name': 'id', 'parameters': [None], 'result': None, 'slots': 1, 'body': ['ref', None, 0]}
    fp = plans['foreign-print']       # 1 U32, 2 Char and 3 String here too; 4 IO.OP, 6 k's arrow, 7 IO(Unit)
    identity = ['closure', arrow, 1, 1, [], ['ref', flag, 0]]
    unit_identity = ['closure', len(fp['types']), 1, 1, [], ['ref', 0, 0]]

    def via_id(t, value=identity):
        return ['call', t, 0, [value]]

    def text(*cells, tail=None):
        """A String: a literal, or SCon cells (a code or a node each) ending in `tail`."""
        if tail is None:
            return ['lit', string, 'String', list(cells)]
        for c in reversed(cells):
            tail = ['con', string, 1, [c if isinstance(c, list) else ['lit', char, 'Char', c], tail]]
        return tail

    def base(p):
        ins = [rep[name] for name in prims[p]['inputs']]
        out = rep[prims[p]['output']]
        return {'name': prims[p]['name'], 'parameters': ins, 'result': out, 'slots': len(ins),
                'body': ['prim', out, p, [['ref', t, i] for i, t in enumerate(ins)]]}

    def applied(p, *operands):
        return ['call', rep[prims[p]['output']], 1, list(operands)]

    def book(body, result=flag, prim=None, extra=(), more=()):
        main = {'name': 'main', 'parameters': [], 'result': result, 'slots': int(body[0] == 'let'), 'body': body}
        return {'entry': 'book', 'representation': rep, 'types': [*types, *more],
                'functions': [ident, *([base(prim)] if prim is not None else []), *extra, main]}

    def dropped(node, result=flag):
        return ['let', result, 0, node, ['value', result, 1]]

    def program(body, *functions):
        return {'entry': 'program', 'representation': fp['representation'],
                'types': fp['types'] + [{'kind': 'arrow', 'domain': 0, 'result': 0}],
                'functions': [ident, *functions, {'name': 'main', 'parameters': [], 'result': 7, 'slots': 0, 'body': body}]}

    def halting(code, message):
        """main = λ@R. λk. Halt{code, message}"""
        return program(['closure', 7, 0, 0, [], ['closure', 6, 1, 1, [], ['con', 4, 1, [code, message]]]])

    def ill(calls, **more):
        return {**ILL_TYPED, **more, 'calls': calls}

    def pick(scrutinee, rows, default=None, mode='tags', slots=1):
        """pick(x: none) -> Flag cases on its erased parameter at a concrete type (section 6.1)."""
        return {'name': 'pick', 'parameters': [None], 'result': flag, 'slots': slots,
                'body': ['case', flag, 0, scrutinee, mode, rows, default]}

    def picking(word, *function):
        """main = pick(id(word)), pick being function index 1"""
        return book(['call', flag, 1, [via_id(None, word)]], extra=function)

    def answering(node):
        """main = λ@R. λk. node: the IO.OP that k's body answers is the run's last word"""
        return program(['closure', 7, 0, 0, [], ['closure', 6, 1, 1, [], node]])

    def continuing(k):
        """main = λ@R. λk. IO.print("x")(R)(k'), IO.print being function index 1"""
        applied_to = ['invoke', 4, ['invoke', 6, ['call', 7, 1, [text(120)]], []], [k]]
        return program(['closure', 7, 0, 0, [], ['closure', 6, 1, 1, [], applied_to]], fp['functions'][0])
    snil, closure_tail = ['value', string, 0], via_id(string)
    on, off = ['value', flag, 1], ['value', flag, 0]
    one_u32, one_nat, a_char = ['lit', u32, 'U32', 1], ['lit', nat, 'Nat', 1], ['lit', char, 'Char', 97]
    box = {'kind': 'data', 'name': 'Box', 'constructors': [{'name': 'Box', 'fields': [flag]}]}
    flag_rows = [['branch', 0, 1, 0, off], ['branch', 1, 1, 0, on]]
    key_rows = [['branch', 7, 1, 0, on]]
    keys_default = ['default', off]
    return [
        ('inspect-chr', book(dropped(['con', char, 0, [via_id(u32)]])), ill(2)),
        ('inspect-succ-object',
         book(dropped(['con', nat, 1, [via_id(nat, ['con', pair, 0, [['value', flag, 0], ['value', flag, 1]]])]])),
         ill(2)),
        ('inspect-succ-closure', book(dropped(['con', nat, 1, [via_id(nat)]])), ill(2)),
        ('inspect-u32-to-nat', book(dropped(applied(16, via_id(u32))), prim=16), ill(3)),
        ('inspect-u32-from-nat', book(dropped(applied(17, via_id(nat))), prim=17), ill(3)),
        ('inspect-char-from-u32', book(dropped(applied(18, via_id(u32))), prim=18), ill(3)),
        ('inspect-char-to-u32', book(dropped(applied(19, via_id(char))), prim=19), ill(3)),
        ('inspect-append-b', book(dropped(applied(35, text(120), closure_tail), boolean), boolean, 35), ill(3)),
        ('inspect-append-char', book(dropped(applied(35, text(via_id(char), tail=snil), text(121))), prim=35), ill(3)),
        ('inspect-length-char', book(applied(37, text(via_id(char), tail=snil)), nat, 37), ill(3)),
        ('inspect-reverse-char', book(dropped(applied(36, text(via_id(char), tail=snil))), prim=36), ill(3)),
        ('inspect-is-empty', book(applied(38, text(97, tail=closure_tail)), boolean, 38), ill(3)),
        ('inspect-eq-code', book(applied(34, text(97), text(98, tail=closure_tail)), boolean, 34), ill(3)),
        ('inspect-eq-a-ends', book(applied(34, text(), text(97, tail=closure_tail)), boolean, 34), ill(3)),
        ('inspect-eq-b-ends', book(applied(34, text(97, tail=closure_tail), text()), boolean, 34), ill(3)),
        ('inspect-halt-code', halting(via_id(u32, unit_identity), text()), ill(4)),
        ('inspect-halt-message', halting(['lit', u32, 'U32', 1], text(97, tail=via_id(string, unit_identity))), ill(4)),
        ('inspect-halt-after-surrogate',
         halting(['lit', u32, 'U32', 1], text(0xD800, tail=via_id(string, unit_identity))), ill(4)),
        ('inspect-halt-code-first', halting(via_id(u32, unit_identity), text(0xD800)), ill(4)),
        ('inspect-print-after-surrogate',
         program(['call', 7, 1, [text(0xD800, tail=via_id(string, unit_identity))]], fp['functions'][0]),
         ill(5, stdout='')),
        # A Case's scrutinee, at each type it can be read at (section 6.1).
        ('inspect-case-closure-scrutinee', picking(identity, pick(flag, flag_rows)), ill(3)),
        ('inspect-case-nat-closure',
         picking(identity, pick(nat, [['branch', 0, 1, 0, off], ['branch', 1, 1, 1, on]], slots=2)), ill(3)),
        ('inspect-case-char-closure', picking(identity, pick(char, [['branch', 0, 1, 1, on]], slots=2)), ill(3)),
        ('inspect-case-object-of-another-type',
         book(['call', flag, 1, [via_id(None, ['con', 8, 0, [on]])]], extra=[pick(pair, [['branch', 0, 1, 2, on]], slots=3)],
              more=[box]), ill(3)),
        ('inspect-case-tag-out-of-range', picking(['lit', u32, 'U32', 5], pick(flag, flag_rows)), ill(3)),
        ('inspect-case-keys-closure', picking(identity, pick(u32, key_rows, keys_default, 'keys')), ill(3)),
        ('inspect-case-char-keys-closure', picking(identity, pick(char, key_rows, keys_default, 'keys')), ill(3)),
        # Every prim reads each operand: a first, a second, a Nat amount and a show.
        ('inspect-u32-add', book(dropped(applied(0, via_id(u32), one_u32)), prim=0), ill(3)),
        ('inspect-u32-sub-second', book(dropped(applied(1, one_u32, via_id(u32))), prim=1), ill(3)),
        ('inspect-u32-shln-amount', book(dropped(applied(14, one_u32, via_id(nat))), prim=14), ill(3)),
        ('inspect-char-is-space', book(applied(21, via_id(char)), boolean, 21), ill(3)),
        ('inspect-char-is-eq-second', book(applied(20, a_char, via_id(char)), boolean, 20), ill(3)),
        ('inspect-nat-add', book(dropped(applied(22, via_id(nat), one_nat)), prim=22), ill(3)),
        ('inspect-nat-sub-second', book(dropped(applied(23, one_nat, via_id(nat))), prim=23), ill(3)),
        ('inspect-u32-show', book(dropped(applied(32, via_id(u32))), prim=32), ill(3)),
        ('inspect-nat-show', book(dropped(applied(33, via_id(nat))), prim=33), ill(3)),
        # An Enter reads its target, an Action's continuation included, and the run's last word.
        ('enter-immediate-target',
         book(['invoke', flag, ['call', arrow, 0, [['lit', u32, 'U32', 5]]], [on]]), ill(2)),
        ('enter-object-target',
         book(['invoke', flag, ['call', arrow, 0, [['con', pair, 0, [off, on]]]], [on]]), ill(2)),
        ('inspect-continuation-target', continuing(via_id(5, ['lit', u32, 'U32', 5])), ill(7, stdout='x\n')),
        ('inspect-io-op-closure', answering(via_id(4, unit_identity)), ill(4, stdout='')),
        ('inspect-io-op-immediate', answering(via_id(4, ['lit', u32, 'U32', 5])), ill(4, stdout='')),
        # Rendering reads every word it prints (section 8).
        ('inspect-render-closure', book(['call', flag, 0, [identity]]), ill(2)),
        ('inspect-render-field', book(['con', pair, 0, [on, via_id(flag)]], result=pair), ill(2)),
    ]


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


def argument_controls(images: dict) -> list:
    """(label, image, words after IMAGE, section 8's frozen verdict), by literal review, for
    what the frozen invocations cannot show beside eval-cli: the usage refusal, which
    eval-cli spells otherwise; the Program form; a word of any length; and the image read
    before the words. None admits the words."""
    book, program = images['invoke-words'], images['foreign-print']
    usage, word = 'HostFailure arguments usage', 'HostFailure arguments expected-u32'
    return [
        ('book-without-fuel', book, ['two'], usage),
        ('book-usage-before-lookup', book, ['absent'], usage),
        ('book-long-zeros', book, ['two', '1000000', '0' * 4400 + '1', '0'], None),
        ('book-program-form', book, ['5', '--'], word),
        ('program-runs', program, ['5', '--'], None),
        ('program-args', program, ['0005', '--', 'a', '--'], None),
        ('program-fuel-word', program, ['x', '--'], word),
        ('program-fuel-beyond', program, ['4294967296', '--'], word),
        ('program-without-fuel', program, ['--'], usage),
        ('program-without-separator', program, ['5', 'a'], usage),
        ('program-shape-before-fuel', program, ['x', 'a'], usage),
        ('program-book-form', program, ['main', '5'], usage),
        ('image-before-words', word_patch(book, 0, 0x474D494C), ['absent', 'x'], 'HostFailure image: magic'),
    ]


def argument_verdict(data: bytes, argv: list, reg: dict, digest: bytes, c=None) -> str | None:
    """Sections 4 and 8 before any entry: the image first, then its entry kind's words."""
    c = c or codec
    return rejected(data, reg, digest, c) or c.arguments(c.decode(data, digest), argv)


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


# A name's bytes read as Unicode's table 3-7 reads them, except for the rows that `skipped` leaves out: what a loader
# does that checks the shape of UTF-8 and not all of its ranges. The mutants below splice it into serializer.py; it keeps
# the bytes (Latin-1 text stands for them), so an image that it admits comes back from `encode` unchanged.
LAX_UTF8 = """
def lax_utf8(raw, skipped):
    rows = [(0xC2, 0xDF, 1, 0x80, 0xBF), (0xE0, 0xE0, 2, 0xA0, 0xBF), (0xE1, 0xEC, 2, 0x80, 0xBF), (0xED, 0xED, 2, 0x80, 0x9F),
            (0xEE, 0xEF, 2, 0x80, 0xBF), (0xF0, 0xF0, 3, 0x90, 0xBF), (0xF1, 0xF3, 3, 0x80, 0xBF), (0xF4, 0xF4, 3, 0x80, 0x8F)]
    if 'overlong' in skipped:
        rows += [(0xC0, 0xC1, 1, 0x80, 0xBF), (0xE0, 0xE0, 2, 0x80, 0x9F), (0xF0, 0xF0, 3, 0x80, 0x8F)]
    if 'surrogate' in skipped:
        rows += [(0xED, 0xED, 2, 0xA0, 0xBF)]
    if 'range' in skipped:
        rows += [(0xF4, 0xF4, 3, 0x90, 0xBF), (0xF5, 0xF7, 3, 0x80, 0xBF)]
    if 'stray' in skipped:
        rows += [(0x80, 0xBF, 0, 0, 0)]

    def take(row, i):
        for k in range(row[2]):
            if i >= len(raw) or not 0x80 <= raw[i] <= 0xBF:
                return -1
            if k == 0 and not row[3] <= raw[i] <= row[4]:
                return None
            i += 1
        return i
    i = 0
    while i < len(raw):
        lead = raw[i]
        if lead < 0x80:
            i += 1
            continue
        if 'ascii' in skipped:
            raise UnicodeDecodeError('utf-8', raw, i, i + 1, 'not ASCII')
        rest = [take(r, i + 1) for r in rows if r[0] <= lead <= r[1]]
        after = next((j for j in rest if j is not None and j >= 0), None)
        if after is None and -1 in rest and 'truncated' in skipped:
            after = i + 1
            while after < len(raw) and 0x80 <= raw[after] <= 0xBF:
                after += 1
        if after is None:
            raise UnicodeDecodeError('utf-8', raw, i, i + 1, 'malformed')
        i = after
    return raw.decode('latin-1')
"""

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
    # Section 2 and 3: a key may be 0xffffffff (key_controls); `none` marks only absent tag rows and defaults.
    ('key-none-row-dropped', [("                    rows.append(arm)\n",
                               "                    if x[4 + 2 * i] != NONE:\n                        rows.append(arm)\n")]),
    ('size-guard-after-shape', [("    if len(data) > LIMITS['image_words'] * 4:\n        raise Exhausted('image-size')\n", ""),
                                ("        raise Malformed('length')\n",
                                 "        raise Malformed('length')\n    if len(data) > LIMITS['image_words'] * 4:\n"
                                 "        raise Exhausted('image-size')\n")]),
    # Review round 8: section 4's limits are Exhausted kind 2, checked after their count's
    # structure and before what it governs, inclusively.
    ('limit-as-malformed', [("        raise Exhausted(name)\n", "        raise Malformed(name)\n")]),
    ('limit-exclusive', [("    if count > LIMITS[name]:", "    if count >= LIMITS[name]:")]),
    ('record-limit-before-fit', [("        limit(count, 'records')\n", ""),
                                 ("        if count > (len(w) - at) // 2:",
                                  "        limit(count, 'records')\n        if count > (len(w) - at) // 2:")]),
    ('arity-limit-before-record', [("        limit(r[2], 'arity')\n", ""),
                                   ("        if len(r) < 5 or len(r) != 5 + r[2]:\n            raise Malformed('function record')",
                                    "        limit(r[2], 'arity')\n"
                                    "        if len(r) < 5 or len(r) != 5 + r[2]:\n            raise Malformed('function record')")]),
    ('closure-slots-unlimited', [("            limit(x[2], 'slots')\n", "")]),
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
    ('invoke-words-wrap', [("    return int(digits) if re.fullmatch('[0-9]+', word) and len(digits) <= 10 and int(digits) <= 0xFFFFFFFF else None",
                            "    return int(digits) & 0xFFFFFFFF if re.fullmatch('[0-9]+', word) else None")]),
    ('invoke-words-maximum-exclusive', [("int(digits) <= 0xFFFFFFFF", "int(digits) < 0xFFFFFFFF")]),
    ('invoke-words-no-leading-zeros', [("re.fullmatch('[0-9]+', word)", "re.fullmatch('0|[1-9][0-9]*', word)")]),
    ('invoke-words-ten-digits', [("re.fullmatch('[0-9]+', word)", "re.fullmatch('[0-9]{1,10}', word)")]),
    ('invoke-words-empty-zero', [("re.fullmatch('[0-9]+', word)", "re.fullmatch('[0-9]*', word)")]),
    ('invoke-words-unicode-digits', [("re.fullmatch('[0-9]+', word)", "word.isdigit()")]),
    ('invoke-words-host-int', [("    return int(digits) if re.fullmatch('[0-9]+', word) and len(digits) <= 10 and int(digits) <= 0xFFFFFFFF else None",
                                "    try:\n        value = int(word)\n    except ValueError:\n        return None\n"
                                "    return value if 0 <= value <= 0xFFFFFFFF else None")]),
    # Section 8's forms (argument_controls): usage, the Program's shape before its FUEL word.
    ('arguments-without-usage', [("    if len(argv) < 2:\n        return 'HostFailure arguments usage'\n", "")]),
    ('arguments-ignore-entry', [("    if plan['entry'] == 'book':\n        return invocation(plan, argv)",
                                 "    if True:\n        return invocation(plan, argv)")]),
    ('program-fuel-unchecked', [("    return None if decimal(argv[0]) is not None else 'HostFailure arguments expected-u32'",
                                 "    return None")]),
    ('program-without-separator', [("    if len(argv) < 2 or argv[1] != '--':", "    if len(argv) < 2:")]),
    ('program-fuel-before-shape', [("    if len(argv) < 2 or argv[1] != '--':\n        return 'HostFailure arguments usage'\n",
                                    "    if not argv or decimal(argv[0]) is None:\n        return 'HostFailure arguments expected-u32'\n"
                                    "    if len(argv) < 2 or argv[1] != '--':\n        return 'HostFailure arguments usage'\n")]),
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
    # Review of round 9, finding 4: each check of serializer.py that a frozen control must pin, removed
    # (its statement becomes `pass`; the `return` or `continue` after it stays). Each survives every golden.
    ('decoder-allows-nul-in-name', [("        if any(raw[size:]) or 0 in raw[:size]:\n            raise Malformed('name padding')\n",
                                     "        if any(raw[size:]):\n            raise Malformed('name padding')\n")]),
    ('decoder-allows-nonzero-name-padding', [("        if any(raw[size:]) or 0 in raw[:size]:\n            raise Malformed('name padding')\n",
                                              "        if 0 in raw[:size]:\n            raise Malformed('name padding')\n")]),
    ('validator-u32-may-be-data', [("            if types[t]['kind'] != 'opaque':\n                fail('representation', f'{r} must be opaque')\n",
                                    "            if types[t]['kind'] != 'opaque' and r != 'U32':\n                fail('representation', f'{r} must be opaque')\n")]),
    ('validator-file-may-be-data', [("            if types[t]['kind'] != 'opaque':\n                fail('representation', f'{r} must be opaque')\n",
                                     "            if types[t]['kind'] != 'opaque' and r != 'File':\n                fail('representation', f'{r} must be opaque')\n")]),
    ('validator-allows-duplicate-function-name', [("        fail('functions', 'duplicate function name')\n", "        pass\n")]),
    ('validator-ignores-function-index', [("                fail(where, 'function index')\n", "                pass\n")]),
    ('validator-ignores-construct-tag', [("                fail(where, 'construct tag')\n", "                pass\n")]),
    ('validator-ignores-construct-field-type', [("                    fail(where, 'construct field type')\n", "                    pass\n")]),
    ('validator-ignores-let-body-type', [("                fail(where, 'let body type')\n", "                pass\n")]),
    ('validator-ignores-case-slot-depth', [("                fail(where, 'case slot beyond depth')\n", "                pass\n")]),
    ('validator-ignores-branch-key', [("                        fail(where, 'branch key')\n", "                        pass\n")]),
    ('validator-key-branch-may-bind', [("                        fail(where, 'key branch binds nothing')\n", "                        pass\n")]),
    ('validator-ignores-closure-arrow', [("                fail(where, 'closure arrow')\n", "                pass\n")]),
    ('validator-ignores-closure-result-type', [("                fail(where, 'closure result type')\n", "                pass\n")]),
    ('validator-ignores-invoke-types', [("                fail(where, 'invoke types')\n", "                pass\n")]),
    ('validator-ignores-body-type', [("            fail(f['name'], 'body type')\n", "            pass\n")]),
    # Review of round 11, finding 3: a type record's constructor count is checked against the constructor table
    # before it sizes a list. The late check would allocate from `type-count-max`'s 0xFFFFFFFF, so no mutant
    # restores it (a crash is no kill); these three change a verdict: a count refused where it exactly fills the
    # table (every valid image), and the first-constructor check, or the sum of the counts, removed (each refusal
    # is then another one, `noncanonical` or a constructor's tag).
    ('constructor-count-exclusive', [("            if r[3] > len(ctors) - expect:", "            if r[3] >= len(ctors) - expect:")]),
    ('constructor-grouping-unchecked', [("            if r[2] != expect:\n                raise Malformed('constructor grouping')\n", "")]),
    ('constructor-count-sum-unchecked', [("    if expect != len(ctors):\n        raise Malformed('constructor count')\n", "")]),
    # Round 13, review findings 1 to 3: a mutant for each condition that no control pinned. Each omits one clause of the
    # validator or the decoder, keeps what follows it (the `return` after a `fail` stays), and dies by an admission or a
    # changed refusal of the frozen control that breaks that clause alone.
    ('validator-keys-may-repeat', [("                if keys != sorted(set(keys)) or default is None:",
                                    "                if keys != sorted(keys) or default is None:")]),
    ('validator-construct-nullary-ok', [("                if not fields or len(fields) != len(node[3]):",
                                         "                if len(fields) != len(node[3]):")]),
    ('validator-invoke-count-any', [("            if arrow not in arrows or len(node[3]) != (1 if arrow == 'arrow' else 0):",
                                     "            if arrow not in arrows:")]),
    ('validator-invoke-live-count-unchecked', [("            if arrow not in arrows or len(node[3]) != (1 if arrow == 'arrow' else 0):",
                                                "            if arrow not in arrows or (arrow == 'erased-arrow' and node[3]):")]),
    ('validator-invoke-erased-count-unchecked', [("            if arrow not in arrows or len(node[3]) != (1 if arrow == 'arrow' else 0):",
                                                  "            if arrow not in arrows or (arrow == 'arrow' and len(node[3]) != 1):")]),
    ('validator-case-slot-any-type', [("            if scrutinee is None or scope[slot] not in (None, scrutinee):",
                                       "            if scrutinee is None:")]),
    ('validator-captures-may-repeat', [("            if captures != sorted(set(captures)) or any(c >= depth for c in captures):",
                                        "            if captures != sorted(captures) or any(c >= depth for c in captures):")]),
    ('validator-tag-case-on-any-type', [("                    fail(where, 'tag case on a non-data type')\n", "                    pass\n")]),
    ('validator-key-case-on-any-type', [("                    fail(where, 'key case on a non-scalar type')\n", "                    pass\n")]),
    ('validator-tag-table-any-length', [("                    fail(where, 'tag table is not dense')\n", "                    pass\n")]),
    ('validator-program-without-main-ok', [("        if not main or main[0]['parameters']:", "        if main and main[0]['parameters']:")]),
    ('validator-call-operand-types-unchecked', [("            elif not fits(callee['result'], t) or not all(\n"
                                                 "                    fits(p, k[1]) for p, k in zip(callee['parameters'], node[3])):\n",
                                                 "            elif not fits(callee['result'], t):\n")]),
    ('validator-invoke-argument-type-unchecked',
     [("            elif not fits(types[f]['result'], t) or (node[3] and not fits(types[f]['domain'], node[3][0][1])):\n",
       "            elif not fits(types[f]['result'], t):\n")]),
    ('validator-key-branch-first-slot-unchecked', [("                    if r[2] != depth or r[3] != 0:", "                    if r[3] != 0:")]),
    ('decoder-empty-name-ok', [("if size == 0 or len(r) != 1 + (size + 3) // 4:", "if len(r) != 1 + (size + 3) // 4:")]),
    ('decoder-name-length-word-unchecked', [("if size == 0 or len(r) != 1 + (size + 3) // 4:", "if size == 0:")]),
    ('decoder-duplicate-names-ok', [("    if len(set(names)) != len(names):\n        raise Malformed('duplicate name')\n", "")]),
    ('decoder-shared-child-ok', [("        if offset in owner:\n            raise Malformed('shared node')\n", "")]),
    ('decoder-unreachable-node-ok', [("    if len(owner) + len(roots) != len(node_records):\n        raise Malformed('unreachable node')\n", "")]),
    ('decoder-opaque-payload-ok', [("            if r[2] or r[3]:\n                raise Malformed('opaque type')\n", "")]),
    ('decoder-arrow-name-ok', [("            if r[1] != NONE:\n                raise Malformed('arrow name')\n", "")]),
    ('decoder-scalar-width-any', [("if kind != 'String' and r[1] != 1:", "if kind != 'String' and r[1] < 1:")]),
    ('decoder-record-length-one-ok', [("if at >= len(w) or w[at] < 2 or at + w[at] > len(w):", "if at >= len(w) or w[at] < 1 or at + w[at] > len(w):")]),
    ('decoder-type-record-length-unchecked', [("if len(r) != 4 or r[0] >= len(TYPE_KINDS):", "if r[0] >= len(TYPE_KINDS):")]),
    ('decoder-constructor-field-count-unchecked', [("if len(r) < 4 or len(r) != 4 + r[3] or r[0] >= len(plan_types):",
                                                    "if len(r) < 4 or r[0] >= len(plan_types):")]),
    ('decoder-constant-length-unchecked', [("if len(r) < 2 or r[0] >= len(CONSTANT_KINDS) or len(r) != 2 + r[1]:",
                                            "if len(r) < 2 or r[0] >= len(CONSTANT_KINDS):")]),
    ('decoder-function-arity-word-unchecked', [("if len(r) < 5 or len(r) != 5 + r[2]:", "if len(r) < 5:")]),
    # The two decoders that would crash without their guard read the kind modulo the table instead: what a loader that
    # forgets the bound does, and a refusal that changes (the re-encoded image holds the kind that the table names).
    ('decoder-entry-kind-mod-2', [("if w[3] >= len(ENTRIES) or w[11] != 0:", "if w[11] != 0:"),
                                  ("'entry': ENTRIES[w[3]]", "'entry': ENTRIES[w[3] % 2]")]),
    ('decoder-constant-kind-mod-4', [("if len(r) < 2 or r[0] >= len(CONSTANT_KINDS) or len(r) != 2 + r[1]:", "if len(r) < 2 or len(r) != 2 + r[1]:"),
                                     ("kind = CONSTANT_KINDS[r[0]]", "kind = CONSTANT_KINDS[r[0] % 4]")]),
    # Section 2: the registry digest is eight words, and each is compared; a name's unused bytes are each zero.
    *[(f'decoder-digest-word-{i}-unchecked',
       [("    if bytes(b for x in w[24:32] for b in x.to_bytes(4, 'little')) != digest:",
         f"    if bytes(b for j, x in enumerate(w[24:32]) if j != {i - 24} for b in x.to_bytes(4, 'little')) != "
         f"b''.join(digest[4 * j:4 * j + 4] for j in range(8) if j != {i - 24}):")]) for i in range(24, 32)],
    *[(f'decoder-name-padding-byte-{k}-unchecked',
       [("if any(raw[size:]) or 0 in raw[:size]:",
         f"if any(b for j, b in enumerate(raw[size:]) if j != {k}) or 0 in raw[:size]:")]) for k in (0, 1)],
    ('decoder-name-padding-last-byte-only', [("if any(raw[size:]) or 0 in raw[:size]:", "if raw[size:][-1:].strip(b'\\0') or 0 in raw[:size]:")]),
    # Section 2: a name is well-formed UTF-8 (Unicode, table 3-7). A loader that reads names as opaque bytes after a check
    # of some part of that table (`lax_utf8`, which skips the rows named) admits the malformed forms that part misses,
    # and the image comes back unchanged, so each admission is a change of the frozen refusal.
    *[(f'decoder-name-utf8-{label}',
       [("def decode(data: bytes, digest: bytes) -> dict:\n", LAX_UTF8 + "\ndef decode(data: bytes, digest: bytes) -> dict:\n"),
        ("            names.append(raw[:size].decode('utf-8'))\n", f"            names.append(lax_utf8(raw[:size], {skipped!r}))\n"),
        ("        return names.setdefault(text.encode('utf-8'), len(names))", "        return names.setdefault(text.encode('latin-1'), len(names))")])
      for label, skipped in (('overlong-ok', ('overlong',)), ('surrogates-ok', ('surrogate',)), ('beyond-unicode-ok', ('range',)),
                             ('truncated-ok', ('truncated',)), ('stray-continuation-ok', ('stray',)),
                             ('structure-only', ('overlong', 'surrogate', 'range')), ('ascii-only', ('ascii',)))],
    ('decoder-name-utf8-surrogatepass', [("raw[:size].decode('utf-8')", "raw[:size].decode('utf-8', 'surrogatepass')")]),
]


def invocation_verdicts(invoking: list, c=None) -> dict:
    """Section 8's verdict on every frozen Book invocation, by label."""
    c = c or codec
    return {label: c.invocation(plan, words) for label, plan, words in invoking}


def codec_kill(mutant, plans, images, controls, admitted, describing, reg, digest, invoking, arguing):
    """(what changed, where the mutant crashed): the first frozen image, refusal, verdict or control that the mutant changes,
    or None; and every control on which it raised, which is no kill (section 11) but holds the clause it omits when the
    control is the one that pins it."""
    killed_by, crashed = None, []
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
            crashed.append(case)
    if not killed_by:
        try:
            killed_by = text_spelling(plans, digest, mutant)
        except Exception:
            pass
    for label, data, reason, message in [] if killed_by else controls:
        try:
            got = rejected(data, reg, digest, mutant)
        except Exception:
            crashed.append(label)
            continue
        if got is None or not got.startswith(reason) or message not in got:
            killed_by = f'control {label}: {got}'
            break
    for label, data in [] if killed_by else admitted:
        try:
            got = rejected(data, reg, digest, mutant)
        except Exception:
            crashed.append(label)
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
    for label, data, argv, verdict in [] if killed_by else arguing:
        try:
            got = argument_verdict(data, argv, reg, digest, mutant)
        except Exception:
            continue
        if got != verdict:
            killed_by = f'argument control {label}: {got}'
            break
    return killed_by, crashed


def edited_codec(name, edits, source):
    text = source
    for old, new in edits:
        require(text.count(old) == 1, f'codec mutant {name} is not uniquely located')
        text = text.replace(old, new)
    return load_codec(text)


def codec_mutants(plans, images, controls, admitted, describing, reg, digest, invoking, arguing) -> list:
    """`plans` and `images` include the code-list controls; a decode that differs from its
    plan kills as surely as an encode that differs from its image."""
    source, results = CODEC.read_text(), []
    for name, edits in CODEC_MUTANTS:
        killed_by, _ = codec_kill(edited_codec(name, edits, source), plans, images, controls, admitted, describing, reg,
                                  digest, invoking, arguing)
        results.append({'mutant': name, 'killed': killed_by is not None, 'by': killed_by})
    return results


def refusal_mutants(source: str) -> list:
    """(id, [(old, new)]) for each refusal of the reference codec and for each clause of its test, as a mutant that omits it.
    A refusal is a `raise`, or a call of `fail` or `limit`, as a statement. Omitting it turns it into `pass`, so whatever
    follows it in its block (a `return` or a `continue`) stays, as a loader that forgot the check would go on; a refusal
    that opens an `if` is replaced inside its guard. Omitting a clause drops one operand of a guard whose test is an `or`,
    so that the guard refuses on the others. An id names the function and the message of the refusal, counts repeats in
    source order, and ends `/i` for the i-th clause."""
    starts, at = [], 0
    for line in source.split('\n'):
        starts.append(at)
        at += len(line) + 1                                   # the codec is ASCII: a column is a character

    def span(node):
        return starts[node.lineno - 1] + node.col_offset, starts[node.end_lineno - 1] + node.end_col_offset

    def refuses(stmt):
        return isinstance(stmt, ast.Raise) or (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)
                                               and getattr(stmt.value.func, 'id', None) in ('fail', 'limit'))

    def message(stmt):
        call = stmt.exc if isinstance(stmt, ast.Raise) else stmt.value
        return ast.get_source_segment(source, call.args[1] if isinstance(stmt, ast.Expr) else call.args[0])
    out, seen = [], {}
    for fn in (n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)):
        guards = {id(n.body[0]): n for n in ast.walk(fn) if isinstance(n, ast.If) and n.body and refuses(n.body[0])}
        for stmt in sorted((n for n in ast.walk(fn) if refuses(n)), key=lambda n: (n.lineno, n.col_offset)):
            key = f'{fn.name}:{message(stmt)}'
            seen[key] = seen.get(key, 0) + 1
            key = key if seen[key] == 1 else f'{key}#{seen[key]}'
            guard = guards.get(id(stmt))
            (a, _), (sa, sb) = span(guard or stmt), span(stmt)
            out.append((key, [(source[a:sb], source[a:sa] + 'pass')]))
            if guard and isinstance(guard.test, ast.BoolOp) and isinstance(guard.test.op, ast.Or):
                (ta, tb), operands = span(guard.test), guard.test.values
                for i in range(len(operands)):
                    rest = ' or '.join(f'({ast.get_source_segment(source, v)})' for j, v in enumerate(operands) if j != i)
                    out.append((f'{key}/{i}', [(source[a:sb], source[a:ta] + rest + source[tb:sb])]))
    return out


# The refusals and clauses that no frozen image makes a mutant admit or refuse differently, and why they hold anyway.
# Omitting one of the first kind makes the reference raise (an IndexError, a KeyError) on the control that pins it, which is
# no kill (section 11) but shows that a loader without the check has nothing to read; nothing reaches the second kind; the
# third is the encoder's own input check, which `text_spelling` holds and whose removal makes `encode` raise another error.
# A clause is `/i`, the i-th operand of its refusal's `or`.
CRASH_HELD = {
    "decode:'length'/0": 'length-misaligned',
    "decode:'header'/0": 'entry-kind',
    "decode:f'section {s} record length'/0": 'names-count-beyond-image',
    "decode:'name index'": 'name-index-beyond',
    "decode:'type record'/1": 'type-kind-unknown',
    "decode:'constructor record'/0": 'constructor-record-short',
    "decode:'constructor record'/2": 'constructor-type-beyond',
    "decode:'constructor tag'/0": 'constructor-of-arrow',
    "decode:'constructor tag'/1": 'constructor-tag-beyond',
    "decode:'constant record'/0": 'constant-record-short',
    "decode:'constant record'/1": 'constant-kind-unknown',
    "decode:'child offset'": 'child-not-record',
    "decode:'node record'": 'node-record-short',
    "decode:'node record'/0": 'node-record-short',
    "decode:'node record'/1": 'opcode',
    "decode:f'{op} length'#2/0": 'con-record-short',
    "decode:'closure length'/0": 'closure-record-short',
    "decode:'constant index'": 'constant-index-beyond',
    "decode:'case arm kind'/1": 'case-default-not-default',
    "decode:'function record'/0": 'function-record-tiny',
    "decode:'function root'/0": 'function-root-not-node',
    "validate:f'{r} shape'/0": 'plan:representation-of-arrow',
    "validate:'main must exist with no live parameters'/0": 'plan:program-without-main',
    "validate:'value is not a nullary constructor'/0": 'plan:value-of-opaque',
    "validate:'value is not a nullary constructor'/1": 'plan:value-tag-beyond',
    "validate:'construct tag'/0": 'plan:construct-of-arrow',
    "validate:'construct tag'/1": 'plan:construct-tag',
    "validate:f'unknown {op} id {node[2]}'/0": 'plan:prim-unknown',
    "validate:f'{op} operand is not the pinned {name}'/0": 'plan:prim-on-flags',
    "validate:'branch key'/1": 'plan:tag-table-too-long',
    "validate:'closure arrow'/0": 'plan:closure-erased-at-data-type',
    "validate:'captures must increase strictly below depth'/1": 'plan:capture-beyond-depth',
    "validate:'invoke arity'/0": 'plan:invoke-non-arrow-without-argument',
}
UNREACHABLE = {
    "decode:'constructor order'": "every constructor record has a tag below its type's count and no tag repeats "
                                  "(`constructor tag`), and the counts sum to the table (`constructor count`), so the "
                                  "records fill every slot",
    "validate:f'standalone {op}'": "`decode` refuses a Branch or a Default that no Case holds (`standalone arm`), so "
                                   "`check` is handed none",
    "validate:'type index'": "`decode` refuses a type word beyond the table (`type index`) before `validate` reads it",
    "decode:'opcode'": "`node record` refuses an opcode beyond the table, and every opcode within it has its own case above",
    "validate:f'unknown node {op}'": "`decode` yields only the thirteen forms of the table, each with its own case above",
}
EXCUSED = {
    "u32_list:f'constant data is not a list of u32 words: {values!r}'":
        "the encoder's input check: `text_spelling` holds it, and without it `encode` fails on the text with another error",
    "u32_list:f'constant data is not a list of u32 words: {values!r}'/0": "the same check, its first clause",
    "u32_list:f'constant data is not a list of u32 words: {values!r}'/1": "the same check, its second clause",
    "encode:f'unknown plan node {op!r}'": "the encoder's input check: no decoded plan holds a form outside the table",
}


# Round 12's reviewer removed each of these bounds whole: the reference then raises on the control that pins the bound (the
# entry kind and the constant kind index a table; the block of `tag case on a non-data type` takes its `return` with it,
# so `types[t]['constructors']` raises on every type that has none). That is no kill (section 11), so `crash_held` requires
# what holds them instead: the mutant changes nothing that the gate freezes, and it raises on the named control. The
# modelled omissions that do not raise are the codec mutants `decoder-entry-kind-mod-2`, `decoder-constant-kind-mod-4`
# and `validator-tag-case-on-any-type`.
CRASH_HELD_MUTANTS = [
    ('decoder-entry-kind-unbounded', [("if w[3] >= len(ENTRIES) or w[11] != 0:", "if w[11] != 0:")], 'entry-kind'),
    ('decoder-constant-kind-unbounded', [("if len(r) < 2 or r[0] >= len(CONSTANT_KINDS) or len(r) != 2 + r[1]:",
                                          "if len(r) < 2 or len(r) != 2 + r[1]:")], 'constant-kind-unknown'),
    ('validator-tag-case-block-removed', [("                if kind(scrutinee) != 'data':\n                    fail(where, 'tag case on a non-data type')\n"
                                           "                    return depth\n", "")], 'plan:tag-case-on-opaque'),
]


def crash_held(plans, images, controls, admitted, describing, reg, digest, invoking, arguing) -> dict:
    source, held = CODEC.read_text(), {}
    for name, edits, control in CRASH_HELD_MUTANTS:
        by, crashed = codec_kill(edited_codec(name, edits, source), plans, images, controls, admitted, describing, reg, digest,
                                 invoking, arguing)
        require(by is None and control in crashed, f'{name}: killed by {by}, or does not raise on {control} ({crashed})')
        held[name] = control
    return held


def statement_audit(plans, images, controls, admitted, describing, reg, digest, invoking, arguing) -> dict:
    """Omit each refusal of the reference codec, and each clause of its test, in turn (`refusal_mutants`) and account for it:
    killed by a frozen image, refusal or verdict, or listed above with what holds it. A refusal that a new statement adds and no
    control pins fails here, and so does a listed one that a control has come to kill, or that no longer raises where it is
    said to."""
    source, killed, held, other = CODEC.read_text(), [], {}, {}
    frozen = {label: reason + message for label, _, reason, message in controls}
    for name, edits in refusal_mutants(source):
        by, crashed = codec_kill(edited_codec(name, edits, source), plans, images, controls, admitted, describing, reg, digest,
                                 invoking, arguing)
        if by:
            require(name not in CRASH_HELD and name not in UNREACHABLE and name not in EXCUSED,
                    f'refusal {name} is listed as held, but {by} kills its removal')
            killed.append(name)
        elif name in CRASH_HELD:
            control = CRASH_HELD[name]
            require(control in crashed, f'refusal {name}: its removal no longer raises on {control}')
            literal = re.fullmatch(r"\w+:'([^']*)'", name)
            require(not literal or frozen[control].endswith(literal[1]), f'refusal {name}: {control} does not freeze it')
            held[name] = control
        elif name in UNREACHABLE or name in EXCUSED:
            require(not crashed, f'refusal {name}: its removal raises on {crashed}, so it is not unreached')
            other[name] = UNREACHABLE.get(name) or EXCUSED[name]
        else:
            raise AssertionError(f'refusal {name}: no frozen control makes its removal admit an image or refuse another way')
    listed = set(CRASH_HELD) | set(UNREACHABLE) | set(EXCUSED)
    require(listed <= set(held) | set(other), f'listed refusals that the codec no longer holds: {sorted(listed - set(held) - set(other))}')
    return {'omissions': len(killed) + len(held) + len(other), 'killed': len(killed), 'held_by_crash': held, 'unreached': other}


# Lines of evaluate.py that several mutants replace: the Top loop's step, and the attribute that a Book
# mutant reads to tell a Book from a Program (D23 needs no such distinction).
LOOP = '            w = m.apply(w[3], [m.effect(w)])'
ENTRY = ("        self.rep = plan.get('representation', {})\n",
         "        self.rep, self.entry = plan.get('representation', {}), plan['entry']\n")

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
    # Section 2 and 3 (key_controls): a key of 0xffffffff is neither absent nor a wildcard.
    ('case-key-max-absent', [('arm, fields = next((r for r in rows if r[1] == key), default), ()',
                              'arm, fields = next((r for r in rows if r[1] == key != WORD), default), ()')]),
    ('case-key-max-wildcard', [('arm, fields = next((r for r in rows if r[1] == key), default), ()',
                                'arm, fields = next((r for r in rows if r[1] in (key, WORD)), default), ()')]),
    # Section 7: the debit of the entry that built a request stands when the loop's effect stops the machine,
    # which the D20 goldens' `calls` count.
    ('effect-refusal-refunds-debit', [(LOOP, '            try:\n                r = m.effect(w)\n            except Halt:\n'
                                             '                m.fuel, m.calls = m.fuel + 1, m.calls - 1\n                raise\n'
                                             '            w = m.apply(w[3], [r])')]),
    # Section 7's fuel boundary (fuel_controls): no golden runs out of fuel.
    ('fuel-never-exhausts', [('        if self.fuel == 0:\n            raise Halt', '        if False:\n            raise Halt')]),
    ('fuel-exhausts-early', [('        if self.fuel == 0:\n            raise Halt', '        if self.fuel <= 1:\n            raise Halt')]),
    # The Action's second application is debited where it builds the request; a debit paid by the loop after
    # the effect leaves a dropped request free and writes before it meets fuel 0.
    ('debit-at-perform', [("        self.debit()\n        if kind == 'closure':",
                           "        if kind != 'action' or not operands:\n            self.debit()\n        if kind == 'closure':"),
                          (LOOP, '            r = m.effect(w)\n            m.debit()\n            w = m.apply(w[3], [r])')]),
    ('fuel-before-operand-check', [('        if kind not in takes or not takes[kind]():',
                                    '        if self.fuel == 0:\n            self.debit()\n'
                                    '        if kind not in takes or not takes[kind]():')]),
    ('terminal-entry-free', [("        self.debit()\n        if kind == 'closure':",
                              "        if kind != 'terminal':\n            self.debit()\n        if kind == 'closure':")]),
    # Sections 6, 8, 9 and 10 (inspection_controls): each reads less than its inspection extent
    # and is exact on well-typed words, so no golden changes; each dies by one inspection control.
    ('chr-passes-operand', [("        if t == self.rep.get('Char'):\n            return self.word(operands[0])",
                             "        if t == self.rep.get('Char'):\n            return operands[0]")]),
    *[(f'succ-admits-{kind}', [('            return self.nat(self.word(operands[0]) + 1)',
                                f"            if isinstance(operands[0], tuple) and operands[0][0] == '{tag}':\n"
                                '                return operands[0]\n'
                                '            return self.nat(self.word(operands[0]) + 1)')])
      for kind, tag in (('object', 'obj'), ('closure', 'closure'))],
    *[(f'{name}-unread', [('        if p in (16, 17, 18, 19):\n            return self.word(a[0])',
                           f'        if p in (16, 17, 18, 19):\n            return a[0] if p == {p} else self.word(a[0])')])
      for p, name in ((16, 'u32-to-nat'), (17, 'u32-from-nat'), (18, 'char-from-u32'), (19, 'char-to-u32'))],
    ('append-b-unread', [('            return self.string(s + self.codes(a[1]))',
                          '            out = a[1]\n            for code in reversed(s):\n'
                          "                out = ('obj', self.rep['String'], 1, (code, out))\n            return out")]),
    *[(name, [('        s = self.codes(a[0])\n', f'{body}        s = self.codes(a[0])\n')]) for name, body in (
        # The cells' Char words are copied or counted unread.
        ('append-a-chars-unread', "        if p == 35:\n            cells, x = [], a[0]\n"
                                  "            while (cell := self.view(x, self.rep['String']))[0]:\n"
                                  '                cells, x = cells + [cell[1][0]], cell[1][1]\n'
                                  '            return self.string(cells + self.codes(a[1]))\n'),
        ('length-chars-unread', "        if p == 37:\n            n, x = 0, a[0]\n"
                                "            while (cell := self.view(x, self.rep['String']))[0]:\n"
                                '                n, x = n + 1, cell[1][1]\n            return n\n'),
        ('reverse-chars-unread', "        if p == 36:\n            cells, x = [], a[0]\n"
                                 "            while (cell := self.view(x, self.rep['String']))[0]:\n"
                                 '                cells, x = [cell[1][0]] + cells, cell[1][1]\n'
                                 '            return self.string(cells)\n'),
        ('is-empty-reads-one-cell', "        if p == 38:\n            return int(self.view(a[0], self.rep['String'])[0] == 0)\n"),
        ('eq-stops-at-difference', "        if p == 34:\n            x, y = a\n            while True:\n"
                                   "                (i, f), (j, g) = self.view(x, self.rep['String']), self.view(y, self.rep['String'])\n"
                                   "                if i != j or i and self.view(f[0], self.rep['Char']) != self.view(g[0], self.rep['Char']):\n"
                                   '                    return 0\n                if i == 0:\n                    return 1\n'
                                   '                x, y = f[1], g[1]\n'),
        # One list is read whole, the other only one cell past the first one's length.
        *[(name,
           f'        if p == 34:\n            {a}, {b}, rest = self.codes(a[{i}]), [], a[{1 - i}]\n'
           f"            while len({b}) <= len({a}) and (cell := self.view(rest, self.rep['String']))[0]:\n"
           f"                {b}, rest = {b} + [self.view(cell[1][0], self.rep['Char'])[1][0]], cell[1][1]\n"
           f'            return int({a} == {b})\n')
          for name, a, b, i in (('eq-reads-b-one-past-a', 'x', 'y', 0), ('eq-reads-a-one-past-b', 'y', 'x', 1))])],
    ('halt-code-unread', [('            code, message = m.word(fields[0]), m.codes(fields[1])\n',
                           '            code, message = fields[0], m.codes(fields[1])\n')]),
    ('halt-message-unread', [('            code, message = m.word(fields[0]), m.codes(fields[1])\n            m.outgoing(message)\n',
                              '            code, message = m.word(fields[0]), fields[1]\n')]),
    # Section 10 (effect_controls): a scalar String is written as canonical UTF-8; the goldens write only
    # ASCII beside the non-scalar codes, whose lead byte the native lane truncates, so the two-byte form and
    # every boundary are frozen by the two print controls.
    ('utf8-one-byte-threshold', [("    if code < 0x80:", "    if code < 0x7F:")]),
    ('utf8-two-byte-wrong-lead',
     [("        return bytes([0xC0 | code >> 6, 0x80 | code & 0x3F])", "        return bytes([0xC0 | code >> 7, 0x80 | code & 0x3F])")]),
    ('utf8-two-byte-threshold', [("    if code < 0x800:", "    if code <= 0x800:")]),
    ('utf8-three-byte-threshold', [("    if code < 0x10000:", "    if code <= 0x10000:")]),
    # Sections 6, 7, 8 and 9 (inspection_controls): a Case's scrutinee, each prim operand, an Enter's
    # target (the Action's continuation among them), the run's last word and a rendered word are read
    # like the rest. Each reads less than section 6 requires and is exact on a well-typed word, so no golden
    # changes, and each dies by the control of its own point.
    ('case-tags-closure-scrutinee-admitted',
     [("            tag, fields = self.view(env[slot], t)\n            arm = rows[tag] or default",
       "            tag, fields = (0, ()) if isinstance(env[slot], tuple) and env[slot][0] == 'closure' else self.view(env[slot], t)\n"
       "            arm = rows[tag] or default")]),
    ('case-char-scrutinee-unread',
     [("            tag, fields = self.view(env[slot], t)\n            arm = rows[tag] or default",
       "            tag, fields = (0, (0,)) if t == self.rep.get('Char') and not isinstance(env[slot], int) "
       "else self.view(env[slot], t)\n            arm = rows[tag] or default")]),
    ('view-object-type-unchecked',
     [("isinstance(w, tuple) and w[0] == 'obj' and w[1] == t and ctors[w[2]]['fields']",
       "isinstance(w, tuple) and w[0] == 'obj' and ctors[w[2]]['fields']")]),
    ('view-nat-non-word-as-zero',
     [("        if t == self.rep.get('Nat') and isinstance(w, int):\n            return (0, ()) if w == 0 else (1, (w - 1,))",
       "        if t == self.rep.get('Nat'):\n            return (0, ()) if not isinstance(w, int) or w == 0 else (1, (w - 1,))")]),
    ('view-immediate-tag-out-of-range-as-zero',
     [("        if ctors and isinstance(w, int) and w < len(ctors) and not ctors[w]['fields']:\n            return w, ()",
       "        if ctors and isinstance(w, int) and not ctors[min(w, len(ctors) - 1)]['fields']:\n"
       "            return min(w, len(ctors) - 1), ()")]),
    ('keys-case-scrutinee-uninspected',
     [("            key = self.word(env[slot])\n",
       "            key = env[slot] if isinstance(env[slot], tuple) else self.word(env[slot])\n")]),
    ('keys-case-char-scrutinee-unread',
     [("            key = self.word(env[slot])\n",
       "            key = env[slot] if t == self.rep.get('Char') and not isinstance(env[slot], int) else self.word(env[slot])\n")]),
    ('u32-arith-first-unread',
     [("            x, y = self.word(a[0]), self.word(a[-1])\n",
       "            x, y = (a[0] if isinstance(a[0], int) else 0), self.word(a[-1])\n")]),
    ('u32-arith-second-unread',
     [("            x, y = self.word(a[0]), self.word(a[-1])\n",
       "            x, y = self.word(a[0]), (a[-1] if isinstance(a[-1], int) else 0)\n")]),
    ('char-prim-first-unread',
     [("            x = self.word(a[0])\n            return int(x == self.word(a[1])) if p == 20",
       "            x = a[0] if isinstance(a[0], int) else 0\n            return int(x == self.word(a[1])) if p == 20")]),
    ('char-eq-second-unread',
     [("            return int(x == self.word(a[1])) if p == 20 else",
       "            return int(x == (a[1] if isinstance(a[1], int) else 0)) if p == 20 else")]),
    ('nat-prim-first-unread',
     [("            x, y = self.word(a[0]), self.word(a[1])\n",
       "            x, y = (a[0] if isinstance(a[0], int) else 0), self.word(a[1])\n")]),
    ('nat-prim-second-unread',
     [("            x, y = self.word(a[0]), self.word(a[1])\n",
       "            x, y = self.word(a[0]), (a[1] if isinstance(a[1], int) else 0)\n")]),
    ('show-operand-unread',
     [("            return self.string(show(self.word(a[0])))",
       "            return self.string(show(a[0] if isinstance(a[0], int) else 0))")]),
    ('describe-closure-word-admitted',
     [("            tag, fields = self.view(v, u)\n            if u == nat:",
       "            tag, fields = (0, ()) if isinstance(v, tuple) and v[0] == 'closure' else self.view(v, u)\n            if u == nat:")]),
    ('enter-immediate-target-as-action',
     [("        kind = f[0] if isinstance(f, tuple) else None\n",
       "        f = f if isinstance(f, tuple) else ('action', 0, ())\n        kind = f[0]\n")]),
    ('enter-object-target-admitted',
     [("'terminal': lambda: len(operands) == 1}", "'terminal': lambda: len(operands) == 1, 'obj': lambda: True}")]),
    # A request's continuation is entered by the loop after the effect, and read only then: not when the
    # request is built, not before the effect, and not left unread as the terminal continuation.
    ('continuation-read-at-build',
     [("        return ('request', f[1], f[2], operands[0])",
       "        if not (isinstance(operands[0], tuple) and operands[0][0] in ('closure', 'action', 'terminal')):\n"
       "            raise Halt(ILL_TYPED)\n        return ('request', f[1], f[2], operands[0])")]),
    ('continuation-read-before-effect',
     [(LOOP, "            if not (isinstance(w[3], tuple) and w[3][0] in ('closure', 'action', 'terminal')):\n"
             "                raise Halt(ILL_TYPED)\n" + LOOP)]),
    ('continuation-unread-as-terminal',
     [(LOOP, "            r = m.effect(w)\n            if not isinstance(w[3], tuple):\n"
             "                w = ('obj', m.rep['IO.OP'], 0, (r,))\n                continue\n"
             "            w = m.apply(w[3], [r])")]),
    ('final-word-unread-as-emit',
     [("        tag, fields = m.view(w, m.rep['IO.OP'])",
       "        tag, fields = m.view(w, m.rep['IO.OP']) if isinstance(w, tuple) and w[0] == 'obj' else (0, ())")]),
    # A print that checks each Char as it reads refuses the surrogate before the ill-typed cell.
    ('print-checks-while-reading', [('        codes = self.codes(operands[0])\n',
                                     '        codes, s = [], operands[0]\n'
                                     "        while not codes or self.policy != 'vm' or scalar(codes[-1]):\n"
                                     "            tag, fields = self.view(s, self.rep['String'])\n"
                                     '            if tag == 0:\n                break\n'
                                     "            codes.append(self.view(fields[0], self.rep['Char'])[1][0])\n"
                                     '            s = fields[1]\n')]),
    # Section 8 (D23; the goldens keep-swapped, keep-first, run2-flag, keep-non-scalar and book-drop, and effect_controls):
    # the Action's second application builds an inert request, and only Top's loop performs the one a run returns.
    # Each survives some golden or run control, and dies by those that name it.
    # The eager rule, that round 10 froze and the seed's `keep(x, y) = y` refutes, and a request dropped by the
    # function that received it or by the let that bound it, performed anyway:
    ('eager-effect', [("        return ('request', f[1], f[2], operands[0])",
                       "        return self.apply(operands[0], [self.effect(('request', f[1], f[2], operands[0]))])")]),
    ('dropped-argument-request-performed',
     [("        return self.eval(f['body'], operands + [None] * f['slots'])",
       "        env = operands + [None] * f['slots']\n        w = self.eval(f['body'], env)\n        for v in env:\n"
       "            if isinstance(v, tuple) and v[0] == 'request' and v is not w:\n                self.effect(v)\n        return w")]),
    ('dropped-let-request-performed',
     [("            env[node[2]] = self.eval(node[3], env)\n            return self.eval(node[4], env)\n",
       "            env[node[2]] = self.eval(node[3], env)\n            w = self.eval(node[4], env)\n"
       "            if isinstance(env[node[2]], tuple) and env[node[2]][0] == 'request' and env[node[2]] is not w:\n"
       "                self.effect(env[node[2]])\n            return w\n")]),
    # The loop enters k before the effect: it survives every run that finishes, and dies where k's entry stops.
    ('loop-enters-k-before-effect', [(LOOP, '            req, w = w, m.apply(w[3], [0])\n            m.effect(req)')]),
    # A request is never inspected, except that D24 gives a tags-mode Case its Default: a request matches no
    # constructor row. Each mutant changes one part of that rule. The old refusal (D23's, the rule of round 12) refuses
    # a Case whatever its Default; a Case that ignores its Default picks a row (the goldens `case-request-emit-default-u32`
    # and `-halt-default-u32` print 1 and 3 for 2 and 4), and one without a Default picks its first row or takes the
    # request for an ill-typed word; the Default is taken only at IO.OP, or also by a key-mode Case, a scalar read.
    ('case-request-refused-with-default', [("            if default is None:\n                raise Halt(UNSUPPORTED)\n            arm, fields = default, ()\n",
                                            "            raise Halt(UNSUPPORTED)\n")]),
    ('case-request-ignores-default', [("            if default is None:\n                raise Halt(UNSUPPORTED)\n            arm, fields = default, ()\n",
                                       "            if default is None:\n                raise Halt(UNSUPPORTED)\n"
                                       "            arm = next((r for r in rows if r is not None), default)\n"
                                       "            fields = (0,) * arm[3] if arm[0] == 'branch' else ()\n")]),
    ('case-request-picks-arm', [("            if default is None:\n                raise Halt(UNSUPPORTED)\n            arm, fields = default, ()\n",
                                 "            arm = default or rows[0]\n            fields = (0,) * arm[3] if arm[0] == 'branch' else ()\n")]),
    ('case-request-without-default-ill-typed', [("                raise Halt(UNSUPPORTED)\n            arm, fields = default, ()\n",
                                                 "                raise Halt(ILL_TYPED)\n            arm, fields = default, ()\n")]),
    ('case-request-default-at-io-op-only',
     [("        elif isinstance(env[slot], tuple) and env[slot][0] == 'request':\n",
       "        elif isinstance(env[slot], tuple) and env[slot][0] == 'request' and t == self.rep.get('IO.OP'):\n")]),
    ('keys-case-takes-request-default',
     [("            key = self.word(env[slot])\n            arm, fields = next((r for r in rows if r[1] == key), default), ()\n",
       "            if isinstance(env[slot], tuple) and env[slot][0] == 'request':\n                return self.eval(default[-1], env)\n"
       "            key = self.word(env[slot])\n            arm, fields = next((r for r in rows if r[1] == key), default), ()\n")]),
    ('view-request-as-ill-typed', [("        self.read(w)\n        if t == self.rep.get('Nat') and isinstance(w, int):",
                                    "        if t == self.rep.get('Nat') and isinstance(w, int):")]),
    ('word-request-as-ill-typed', [("        self.read(w)\n        if not isinstance(w, int):", "        if not isinstance(w, int):")]),
    ('enter-request-as-ill-typed', [("        self.read(f)\n", "")]),
    ('fuel-test-before-request-check',
     [("        self.read(f)\n",
       "        if self.fuel == 0 and isinstance(f, tuple) and f[0] == 'request':\n            self.debit()\n        self.read(f)\n")]),
    ('describe-request-word-admitted',
     [("            tag, fields = self.view(v, u)\n            if u == nat:",
       "            tag, fields = (0, ()) if isinstance(v, tuple) and v[0] == 'request' else self.view(v, u)\n            if u == nat:")]),
    # A request's operands, and D20's check of them, belong to the loop that performs it, not to the application that builds it.
    ('request-operands-read-at-build', [("        return ('request', f[1], f[2], operands[0])",
                                         "        if f[1] == 1:\n            self.codes(f[2][0])\n        return ('request', f[1], f[2], operands[0])")]),
    ('request-scalar-check-at-build', [("        return ('request', f[1], f[2], operands[0])",
                                        "        if f[1] == 1:\n            codes = self.codes(f[2][0])\n            self.prints.append(codes)\n"
                                        "            self.outgoing(codes)\n        return ('request', f[1], f[2], operands[0])")]),
    # The loop performs each request it is handed, one after another, and nothing that is not returned to it.
    ('loop-refuses-request', [(LOOP, '            raise Halt(UNSUPPORTED)')]),
    ('loop-performs-once', [("        while isinstance(w, tuple) and w[0] == 'request':\n",
                             "        if isinstance(w, tuple) and w[0] == 'request':\n")]),
    ('emit-performs-its-field',
     [("        if tag == 0:\n            outcome = {'exit': 0}\n",
       "        if tag == 0:\n            if isinstance(fields[0], tuple) and fields[0][0] == 'request':\n"
       "                m.effect(fields[0])\n            outcome = {'exit': 0}\n")]),
    # A Book has no loop (D22 follows from D23): one that runs it performs the request its result is, and one that
    # refuses or drops a request where it is built (D22's rule of round 9, which D23 replaces) is not the seed's, nor
    # is one that refuses to build the Action or to apply it to its erased R.
    ('book-runs-loop', [("        w = m.call(index, list(ordinals))\n",
                         "        w = m.call(index, list(ordinals))\n        while isinstance(w, tuple) and w[0] == 'request':\n"
                         "            w = m.apply(w[3], [m.effect(w)])\n")]),
    ('book-refuses-request-build', [ENTRY, ("        return ('request', f[1], f[2], operands[0])",
                                            "        if self.entry != 'program':\n            raise Halt(UNSUPPORTED)\n"
                                            "        return ('request', f[1], f[2], operands[0])")]),
    ('book-enters-k-without-effect', [ENTRY, ("        return ('request', f[1], f[2], operands[0])",
                                              "        if self.entry != 'program':\n            return self.apply(operands[0], [0])\n"
                                              "        return ('request', f[1], f[2], operands[0])")]),
    ('book-refuses-action-build', [ENTRY, ("        if op == 'foreign':\n            return ('action', node[2], tuple(operands))\n",
                                           "        if op == 'foreign':\n            if self.entry != 'program':\n"
                                           "                raise Halt(UNSUPPORTED)\n            return ('action', node[2], tuple(operands))\n")]),
    ('book-refuses-erased-application', [ENTRY, ('        if not operands:\n            return f\n',
                                                 "        if not operands:\n            if self.entry != 'program':\n"
                                                 "                raise Halt(UNSUPPORTED)\n            return f\n")]),
    # Sections 8 and 10 (D20 on a Halt's message): read after the code, whole, then checked.
    ('halt-message-unchecked', [('            m.outgoing(message)\n', '')]),
    ('halt-message-refused', [('            m.outgoing(message)\n', "            raise Halt({'outcome': 'HostFailure', 'cause': 'io abi'})\n")]),
    ('halt-message-ascii-only', [('            m.outgoing(message)\n',
                                  "            if not all(c < 0x80 for c in message):\n"
                                  "                raise Halt({'outcome': 'HostFailure', 'cause': 'io abi'})\n")]),
    ('halt-message-before-code', [('            code, message = m.word(fields[0]), m.codes(fields[1])\n            m.outgoing(message)\n',
                                   '            message = m.codes(fields[1])\n            m.outgoing(message)\n'
                                   '            code = m.word(fields[0])\n')]),
    ('halt-checks-while-reading', [('            code, message = m.word(fields[0]), m.codes(fields[1])\n',
                                    '            code, message, cells = m.word(fields[0]), [], fields[1]\n'
                                    "            while not message or policy != 'vm' or scalar(message[-1]):\n"
                                    "                tag, parts = m.view(cells, m.rep['String'])\n"
                                    '                if tag == 0:\n                    break\n'
                                    "                message.append(m.view(parts[0], m.rep['Char'])[1][0])\n"
                                    '                cells = parts[1]\n')]),
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


# Semantic mutants of this gate's own rule: each must change a refusal or an expectation, or
# admit an expectation control; a crash is never a kill.
RULE_MUTANTS = [
    ('rejected-limit-as-host-failure', [("        return f'Exhausted 2 {e}'\n", "        return f'HostFailure image: exhausted {e}'\n")]),
    # Review round 8: an eval lane is excused only by a documented bound, past its budget.
    ('eval-any-exhausted', [("    require(bound, f'{name}: eval lane {ev} is not a documented bound')\n",
                             "    require(classify(ev) == 'Exhausted', f'{name}: eval lane {ev} is not Exhausted')\n"
                             "    if not bound:\n        return {'cause': ev['stderr'].strip()}\n")]),
    ('eval-budget-unreached', [("    require(any(reached[unit] > budget[unit] for unit in budget),\n",
                                "    require(True or any(reached[unit] > budget[unit] for unit in budget),\n")]),
    ('d20-calls-unchecked', [("        require(case.get('vm_calls') == vm['calls'],\n"
                              "                f\"{name}: literal review counts {case.get('vm_calls')} calls, the reference evaluation {vm['calls']}\")\n",
                              "")]),
    # Section 11: an unavailable Book lane is declared, exactly, and the declaration must match a head that has no core.
    ('unavailable-line-unchecked', [("        require(unavailable_line(ev, declared), f\"{case['name']}: declared unavailable as {declared!r}, eval-cli gives {ev}\")\n",
                                     "")]),
    ('unavailable-cause-unnamed', [("and f'Unsupported {line[1]} {line[2]}' == declared\n", "and bool(declared)\n")]),
    ('core-declaration-ignored', [("        require(not declared, f'{name}: declared unavailable, but check-cli prints a core')\n", "")]),
    ('core-undeclared-book', [("        require(plan['entry'] == 'program', f'{name}: no checked core for a Book plan')\n", "        pass\n")]),
    ('inspect-steps-as-visits', [("'steps': 4 * value.count('{') - 2,\n", "'steps': value.count('{'),\n")]),
    ('transitions-without-materialization', [("            self.transitions += 1 + (size if node[0] in ('lit', 'prim') else 0)\n",
                                              "            self.transitions += 1\n")]),
    # Review of round 11: a witness is held to its source's hash, both lanes' bytes and its literal review.
    ('witness-source-unchecked', [("    require(source_sha == entry['sha256'], f'witness {name}: source hash')\n", "")]),
    ('witness-lane-unchecked', [("        require(got[lane] == entry[lane], f'witness {name}: {lane} lane {got[lane]}, frozen {entry[lane]}')\n", "")]),
    ('witness-review-unchecked', [("        require(seen == entry['review'][lane], f\"witness {name}: literal review {entry['review'][lane]}, {lane} lane {seen}\")\n", "")]),
    # Round 13, review finding 3: each clause of section 4 step 5 is held by a control that breaks it alone. A loader
    # without one clause (`piecewise_rejected` with its `bad.add` removed) admits that control.
    *[(f'canonicality-without-{clause}', [(f"        bad.add('{clause}')\n", "        pass\n")]) for clause in CANONICAL_CLAUSES],
]


def rule_mutants(cases, plans, bounds, sources, table, controls, reg, digest, displays) -> list:
    """Each mutant of check-spec.py re-derives every refusal, golden expectation, expectation
    control and display-lane control."""
    source = RULE.read_text()
    results = []
    for name, edits in RULE_MUTANTS:
        text = source
        for old, new in edits:
            require(text.count(old) == 1, f'rule mutant {name} is not uniquely located')
            text = text.replace(old, new)
        mutant, killed_by = load(RULE, text), None
        for label, data, reason, message in controls:
            try:
                got = mutant.rejected(data, reg, digest)
            except Exception:
                continue
            if got is None or not got.startswith(reason) or message not in got:
                killed_by = f'control {label}: {got}'
                break
        for label, data, reason, message in [] if killed_by else controls:
            try:
                got = mutant.piecewise_rejected(data, reg, digest)
            except Exception:
                continue
            if got is None or not got.startswith(reason) or message not in got:
                killed_by = f'control {label}: {got} (by clauses)'
                break
        for case_name, case in [] if killed_by else cases.items():
            try:
                got = mutant.vm_expectation(case, plans[case_name], bounds, sources[case_name])
            except AssertionError as refusal:
                killed_by = f'{case_name}: {refusal}'
            except Exception:
                continue
            else:
                killed_by = None if got == table[case_name] else f'{case_name}: expectation {got}'
            if killed_by:
                break
        for controls_of in [] if killed_by else (mutant.expectation_controls, mutant.excused_controls):
            try:
                controls_of(cases, plans, bounds, sources)
            except AssertionError as changed:
                killed_by = str(changed)
                break
            except Exception:
                continue
        if not killed_by:
            try:
                mutant.core_controls(cases, plans, sources, displays, reg)
            except AssertionError as changed:
                killed_by = str(changed)
            except Exception:
                pass
        if not killed_by:
            try:
                mutant.witness_refusals()
            except AssertionError as changed:
                killed_by = str(changed)
            except Exception:
                pass
        results.append({'mutant': f'rule:{name}', 'killed': killed_by is not None, 'by': killed_by})
    return results


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

def witness_lanes(entry, built) -> dict:
    """The lanes a witness's review names: both seed lanes (the native lane is the reference, the Bun lane a
    cross-check) and, where it names `head`, the literals head's check-cli on the source."""
    case = {'name': f"witness-{entry['name']}", 'source': entry['source'], 'seed_lane': 'native'}
    lanes_ = {'native': lambda: observed(seed_observation(case)),
              'bun': lambda: observed(run([SEED, entry['source']], 120)),
              'head': lambda: observed(run([built['literals']['check'], '--bundle', '.', entry['source']], 120))}
    return {lane: lanes_[lane]() for lane in entry['review']}


def check_witness(entry, got, source_sha):
    """One witness against its frozen row: the source's hash, each lane's bytes and the literal review."""
    name = entry['name']
    require(source_sha == entry['sha256'], f'witness {name}: source hash')
    for lane in entry['review']:
        require(got[lane] == entry[lane], f'witness {name}: {lane} lane {got[lane]}, frozen {entry[lane]}')
        seen = {k: entry[lane][k] for k in entry['review'][lane]}
        require(seen == entry['review'][lane], f"witness {name}: literal review {entry['review'][lane]}, {lane} lane {seen}")


def witness_controls(built) -> dict:
    """The seed's lanes, and where a witness asks it the literals head, on the sources that section 8 cites and no
    golden can carry, because the seed fails, or holds no Case over the request it binds, or Knot cannot lower the
    form. Each source's hash, and each lane's exit, stdout and stderr, are re-observed and must equal
    `witnesses.json`; the literal review of each lane's exit and stdout was written before the bytes were frozen. A
    witness is evidence for SPEC's text and never a VM expectation."""
    frozen = json.loads(WITNESSES.read_text())['witnesses']
    with ThreadPoolExecutor(max_workers=4) as pool:
        fresh = list(pool.map(lambda entry: witness_lanes(entry, built), frozen))
    rows = {}
    for entry, got in zip(frozen, fresh):
        check_witness(entry, got, sha((ROOT / entry['source']).read_bytes()))
        rows[entry['name']] = {lane: {k: got[lane][k] for k in ('exit', 'stdout', 'stderr')} for lane in got}
    return rows


def witness_refusals() -> list:
    """Frozen refusals of `check_witness`: a source that drifted, a lane that drifted, and a frozen lane
    that contradicts its literal review. Each is refused by name, so a check that is dropped admits one."""
    entry = next(w for w in json.loads(WITNESSES.read_text())['witnesses'] if w['name'] == 'case-request-both-arms')
    got = {lane: entry[lane] for lane in entry['review']}
    other = {**got['native'], 'stdout': '1\n'}
    out = []
    for label, frozen, seen, source_sha in [('source-drift', entry, got, '0' * 64),
                                            ('lane-drift', entry, {**got, 'native': other}, entry['sha256']),
                                            ('review-drift', {**entry, 'native': other}, {**got, 'native': other}, entry['sha256'])]:
        try:
            check_witness(frozen, seen, source_sha)
        except AssertionError as refusal:
            out.append({'control': f'witness:{label}', 'refused': str(refusal)})
            continue
        raise AssertionError(f'witness control {label} was admitted')
    return out


def freeze_witnesses(built):
    """Observe the lanes that a witness's review names and that have no frozen row yet. Never rewrites one."""
    data = json.loads(WITNESSES.read_text())
    for entry in data['witnesses']:
        if not all(lane in entry for lane in entry['review']):
            entry.setdefault('sha256', sha((ROOT / entry['source']).read_bytes()))
            for lane, row in witness_lanes(entry, built).items():
                entry.setdefault(lane, row)
    WITNESSES.write_text(json.dumps(data, indent=2) + '\n')


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
    freeze_witnesses(built)


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
        for key in ('seed_stdout_hex', 'seed_bun_stderr', 'divergence', 'vm_stdout', 'vm_calls', 'unavailable'):
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
        view = core_view(name, case, plan, displays[name], sources[name], reg)
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
    chars = [n for p in plans.values() for n in walk(p)
             if n[0] == 'case' and n[4] == 'tags' and n[3] == p.get('representation', {}).get('Char')]
    require(chars, 'a tags-mode Case on Char')

    planned = plan_controls(plans)
    lowered = lowered_controls(planned, plans, reg)
    limited = limit_controls(plans, images, digest)
    controls = byte_controls(images, digest) + [(f'limit:{k}', d, r, '') for k, d, r in limited if r] + [
        (f'plan:{k}', codec.encode(p, digest), 'HostFailure image: validator: ', m) for k, p, m in planned if m]
    admitted = [(f'plan:{k}', codec.encode(p, digest)) for k, p, m in planned if m is None] + \
        [(f'limit:{k}', d) for k, d, r in limited if r is None]
    boundaries = expectation_controls(cases, plans, bounds, sources) + invocation_controls(cases, plans, sources) + \
        seed_display_controls() + core_controls(cases, plans, sources, displays, reg)
    excused = excused_controls(cases, plans, bounds, sources)
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
    arguing = argument_controls(images)
    for label, data, argv, verdict in arguing:
        got = argument_verdict(data, argv, reg, digest)
        require(got == verdict, f'argument control {label}: {got!r}, frozen {verdict!r}')
    canonical = canonical_differential(images, controls, admitted, reg, digest)
    held = crash_held({**plans, **coded}, {**images, **{k: codec.encode(p, digest) for k, p in coded.items()}},
                      controls, admitted, describing, reg, digest, invoking, arguing)
    audit = statement_audit({**plans, **coded}, {**images, **{k: codec.encode(p, digest) for k, p in coded.items()}},
                            controls, admitted, describing, reg, digest, invoking, arguing)
    mutants = codec_mutants({**plans, **coded}, {**images, **{k: codec.encode(p, digest) for k, p in coded.items()}},
                            controls, admitted, describing, reg, digest, invoking, arguing) + source_mutants(cases, built) + \
        evaluator_mutants(cases, plans, bounds, sources, table, run_controls(plans)) + \
        rule_mutants(cases, plans, bounds, sources, table, controls, reg, digest, displays)
    survivors = [m['mutant'] for m in mutants if not m['killed']]
    require(not survivors, f'surviving mutants {survivors}')

    record['bench'] = check_bench(built)
    boundaries += bench_controls(built)
    witnessed = witness_controls(built)
    boundaries += witness_refusals()
    record.update(status='passed', fixtures=fixtures, boundaries=boundaries, excused=excused, witnesses=witnessed,
                  admitted=[label for label, _ in admitted], lowered=lowered, runs=runs, describe=verdicts,
                  arguments={label: {'argv': ['IMAGE', *argv], 'verdict': verdict} for label, _, argv, verdict in arguing},
                  mutants=mutants, canonical=canonical, refusal_audit={**audit, 'omitted_bounds_that_raise': held},
                  code_lists={'round_trip': sorted(coded), 'text_spelling': 'refused by encode'},
                  coverage={'opcodes': sorted(opcodes), 'case_modes': sorted(modes),
                            'program_images': sum(p['entry'] == 'program' for p in plans.values()),
                            'none_typed_nodes': len(abstract), 'tags_cases_on_char': len(chars)})
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(record, indent=1) + '\n')
    print(f"vm-spec passed: {len(fixtures)} golden images, {len(boundaries)} refused controls, "
          f"{len(admitted)} admitted controls ({len(coded)} code lists, {len(runs)} runs), "
          f"{len(verdicts)} describe controls, {len(arguing)} argument controls, {len(excused)} excused controls, "
          f"{len(witnessed)} seed witnesses, {len(mutants)} killed mutants, {audit['omissions']} omissions of a codec refusal "
          f"or clause accounted for ({audit['killed']} killed, {len(audit['held_by_crash'])} held by a raise, "
          f"{len(audit['unreached'])} unreached or excused; {len(held)} of the reviewer's bounds held by a raise); "
          f"{RECEIPT.relative_to(ROOT)}")
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
