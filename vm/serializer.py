#!/usr/bin/env python3
"""Reference codec for knot-image-1 (vm/SPEC.md sections 2-4).

`encode` lays out a hand-written record plan; `decode` reads words back into a
plan without sharing layout code with `encode`; `validate` checks a decoded
plan's scope, arity and type rules. An image is canonical exactly when
`encode(decode(image)) == image`. Nothing here parses Bend or evaluates a term.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

MAGIC, VERSION, HEADER, NONE = 0x474D494B, 1, 32, 0xFFFFFFFF
ENTRIES = ('book', 'program')
REPRESENTATIONS = ('Nat', 'U32', 'Char', 'String', 'Bool', 'Cmp', 'Unit', 'List',
                   'Result', 'Sigma', 'IO.OP', 'File')
TYPE_KINDS = ('data', 'arrow', 'erased-arrow', 'opaque')
CONSTANT_KINDS = ('U32', 'Nat', 'Char', 'String')
OPCODES = ('lit', 'prim', 'default', 'value', 'con', 'ref', 'call', 'let', 'case',
           'branch', 'closure', 'invoke', 'foreign')
CASE_MODES = ('tags', 'keys')
LIMITS = {'image_words': 4 * 1024 * 1024, 'records': 1 << 20, 'arity': 4096, 'slots': 65536}
# Pinned shapes of the representation types (constructor field counts by tag).
SHAPES = {'Nat': [0, 1], 'Char': [1], 'String': [0, 2], 'Bool': [0, 0], 'Cmp': [0, 0, 0],
          'Unit': [0], 'List': [0, 2], 'Result': [1, 1], 'Sigma': [2], 'IO.OP': [1, 2]}
OPAQUE = ('U32', 'File')


class Malformed(Exception):
    """The bytes are not a knot-image-1 image: HostFailure image."""


def opt(value):
    return NONE if value is None else value


# ---------------------------------------------------------------- encoding

def encode(plan: dict, digest: bytes) -> bytes:
    names: dict[bytes, int] = {}

    def name(text: str) -> int:
        return names.setdefault(text.encode('utf-8'), len(names))

    types, first = [], 0
    for t in plan['types']:
        kind = TYPE_KINDS.index(t['kind'])
        if t['kind'] == 'data':
            types.append([kind, name(t['name']), first, len(t['constructors'])])
            first += len(t['constructors'])
        elif t['kind'] == 'opaque':
            types.append([kind, name(t['name']), 0, 0])
        else:
            types.append([kind, NONE, opt(t['domain']), opt(t['result'])])
    ctors = [[index, tag, name(c['name']), len(c['fields']), *map(opt, c['fields'])]
             for index, t in enumerate(plan['types']) if t['kind'] == 'data'
             for tag, c in enumerate(t['constructors'])]
    for f in plan['functions']:
        name(f['name'])

    constants: dict[tuple, int] = {}
    nodes: list[list] = []          # [opcode, type, operands...] with ('@', node index) children
    sites = [0]

    def constant(kind: str, value) -> int:
        data = [ord(c) for c in value] if isinstance(value, str) else (
            list(value) if isinstance(value, list) else [value])
        key = (CONSTANT_KINDS.index(kind), tuple(data))
        return constants.setdefault(key, len(constants))

    def emit(node, result=None) -> int:
        op = node[0]
        if op in ('branch', 'default'):
            kids = [emit(node[-1])]
            operands = [node[1], node[2], node[3], ('@', kids[0])] if op == 'branch' else [('@', kids[0])]
            nodes.append([OPCODES.index(op), result, *operands])
            return len(nodes) - 1
        t = node[1]
        if op == 'lit':
            operands = [constant(node[2], node[3])]
        elif op == 'value':
            operands = [node[2]]
        elif op == 'ref':
            operands = [node[2]]
        elif op in ('prim', 'con', 'call', 'foreign'):
            kids = [emit(k) for k in node[3]]
            operands = [node[2], len(kids), *(('@', k) for k in kids)]
        elif op == 'let':
            value, body = emit(node[3]), emit(node[4])
            operands = [node[2], ('@', value), ('@', body)]
        elif op == 'case':
            _, _, slot, scrutinee, mode, rows, default = node
            if mode == 'tags':
                arms = [None if r is None else emit(r, t) for r in rows]
                table = [NONE if a is None else ('@', a) for a in arms]
            else:
                table = []
                for r in rows:
                    table += [r[1], ('@', emit(r, t))]
            fallback = NONE if default is None else ('@', emit(default, t))
            operands = [slot, scrutinee, CASE_MODES.index(mode), len(rows), *table, fallback]
        elif op == 'closure':
            _, _, live, slots, captures, body = node
            kid = emit(body)
            operands = [sites[0], live, slots, len(captures), *captures, ('@', kid)]
            sites[0] += 1
        elif op == 'invoke':
            kids = [emit(node[2])] + [emit(a) for a in node[3]]
            operands = [('@', kids[0]), len(kids) - 1, *(('@', k) for k in kids[1:])]
        else:
            raise ValueError(f'unknown plan node {op!r}')
        nodes.append([OPCODES.index(op), t, *operands])
        return len(nodes) - 1

    roots = [emit(f['body']) for f in plan['functions']]

    def section(records):
        return [len(records)] + [w for r in records for w in [len(r) + 1, *r]]

    named = [(len(b), [int.from_bytes(b[i:i + 4].ljust(4, b'\0'), 'little')
                       for i in range(0, len(b), 4)]) for b in names]
    fixed = [section(types), section(ctors), None,
             section([[k, len(d), *d] for (k, d) in constants]), None,
             section([[n, *packed] for n, packed in named])]
    functions_size = 1 + sum(6 + len(f['parameters']) for f in plan['functions'])
    offsets = [HEADER]
    for words in (fixed[0], fixed[1]):
        offsets.append(offsets[-1] + len(words))
    offsets.append(offsets[-1] + functions_size)
    offsets.append(offsets[-1] + len(fixed[3]))
    at, place = offsets[-1] + 1, []
    for n in nodes:
        place.append(at)
        at += len(n) + 1
    offsets.append(at)

    def resolve(w):
        return place[w[1]] if isinstance(w, tuple) else w

    fixed[4] = [len(nodes)] + [w for n in nodes for w in [len(n) + 1, *map(resolve, n)]]
    fixed[2] = section([[names[f['name'].encode('utf-8')], opt(f['result']), len(f['parameters']),
                         f['slots'], place[r], *map(opt, f['parameters'])]
                        for f, r in zip(plan['functions'], roots)])
    main = next((i for i, f in enumerate(plan['functions']) if f['name'] == 'main'), NONE)
    representation = [plan.get('representation', {}).get(r, NONE) for r in REPRESENTATIONS]
    body = [w for s in fixed for w in s]
    header = [MAGIC, VERSION, HEADER + len(body), ENTRIES.index(plan['entry']), main, *offsets, 0,
              *representation, *(int.from_bytes(digest[i:i + 4], 'little') for i in range(0, 32, 4))]
    assert len(header) == HEADER
    return b''.join(w.to_bytes(4, 'little') for w in header + body)


# ---------------------------------------------------------------- decoding

def decode(data: bytes, digest: bytes) -> dict:
    if len(data) > LIMITS['image_words'] * 4:
        raise Malformed('exhausted image-size')
    if len(data) % 4 or len(data) < HEADER * 4:
        raise Malformed('length')
    w = [int.from_bytes(data[i:i + 4], 'little') for i in range(0, len(data), 4)]
    if w[0] != MAGIC or w[1] != VERSION:
        raise Malformed('magic')
    if w[2] != len(w):
        raise Malformed('total')
    if w[3] >= len(ENTRIES) or w[11] != 0:
        raise Malformed('header')
    if bytes(b for x in w[24:32] for b in x.to_bytes(4, 'little')) != digest:
        raise Malformed('registry digest')

    sections, cursor = [], HEADER
    for s in range(6):
        if w[5 + s] != cursor:
            raise Malformed(f'section {s} offset')
        count, at, records = w[cursor], cursor + 1, []
        if count > LIMITS['records']:
            raise Malformed('record count')
        for _ in range(count):
            if at >= len(w) or w[at] < 2 or at + w[at] > len(w):
                raise Malformed(f'section {s} record length')
            records.append((at, w[at + 1:at + w[at]]))
            at += w[at]
        sections.append(records)
        cursor = at
    if cursor != len(w):
        raise Malformed('trailing words')
    types, ctors, funcs, consts, node_records, name_records = sections

    names = []
    for _, r in name_records:
        size = r[0]
        if size == 0 or len(r) != 1 + (size + 3) // 4:
            raise Malformed('name length')
        raw = b''.join(x.to_bytes(4, 'little') for x in r[1:])
        if any(raw[size:]) or 0 in raw[:size]:
            raise Malformed('name padding')
        try:
            names.append(raw[:size].decode('utf-8'))
        except UnicodeDecodeError:
            raise Malformed('name utf-8') from None
    if len(set(names)) != len(names):
        raise Malformed('duplicate name')

    def text(i):
        if i >= len(names):
            raise Malformed('name index')
        return names[i]

    def ref(i, bound, what):
        if i == NONE:
            return None
        if i >= bound:
            raise Malformed(f'{what} index')
        return i

    plan_types, expect = [], 0
    for _, r in types:
        if len(r) != 4 or r[0] >= len(TYPE_KINDS):
            raise Malformed('type record')
        kind = TYPE_KINDS[r[0]]
        if kind == 'data':
            if r[2] != expect:
                raise Malformed('constructor grouping')
            expect += r[3]
            plan_types.append({'kind': kind, 'name': text(r[1]), 'constructors': [None] * r[3]})
        elif kind == 'opaque':
            if r[2] or r[3]:
                raise Malformed('opaque type')
            plan_types.append({'kind': kind, 'name': text(r[1])})
        else:
            if r[1] != NONE:
                raise Malformed('arrow name')
            plan_types.append({'kind': kind, 'domain': ref(r[2], len(types), 'type'),
                               'result': ref(r[3], len(types), 'type')})
    if expect != len(ctors):
        raise Malformed('constructor count')
    for i, (_, r) in enumerate(ctors):
        if len(r) < 4 or len(r) != 4 + r[3] or r[0] >= len(plan_types):
            raise Malformed('constructor record')
        t = plan_types[r[0]]
        if t['kind'] != 'data' or r[1] >= len(t['constructors']) or t['constructors'][r[1]] is not None:
            raise Malformed('constructor tag')
        t['constructors'][r[1]] = {'name': text(r[2]),
                                   'fields': [ref(x, len(types), 'type') for x in r[4:]]}
    if any(c is None for t in plan_types if t['kind'] == 'data' for c in t['constructors']):
        raise Malformed('constructor order')

    constants = []
    for _, r in consts:
        if len(r) < 2 or r[0] >= len(CONSTANT_KINDS) or len(r) != 2 + r[1]:
            raise Malformed('constant record')
        kind = CONSTANT_KINDS[r[0]]
        if kind != 'String' and r[1] != 1:
            raise Malformed('scalar constant width')
        constants.append((kind, ''.join(map(safe_chr, r[2:])) if kind == 'String' else r[2]))

    start = {at: i for i, (at, _) in enumerate(node_records)}
    owner: dict[int, int] = {}

    def child(offset, parent_at):
        if offset not in start:
            raise Malformed('child offset')
        if offset >= parent_at:
            raise Malformed('child after parent')
        if offset in owner:
            raise Malformed('shared node')
        owner[offset] = parent_at
        return offset

    shapes = {}
    for at, r in node_records:
        if len(r) < 2 or r[0] >= len(OPCODES):
            raise Malformed('node record')
        op, t, x = OPCODES[r[0]], r[1], r[2:]
        need = {'lit': 1, 'value': 1, 'ref': 1, 'default': 1, 'let': 3, 'branch': 4}.get(op)
        if need is not None and len(x) != need:
            raise Malformed(f'{op} length')
        if op in ('prim', 'con', 'call', 'foreign', 'invoke'):
            if len(x) < 2 or len(x) != 2 + x[1]:
                raise Malformed(f'{op} length')
        if op == 'case' and (len(x) < 4 or x[2] >= len(CASE_MODES) or
                             len(x) != 5 + x[3] * (1 if x[2] == 0 else 2)):
            raise Malformed('case length')
        if op == 'closure' and (len(x) < 5 or len(x) != 5 + x[3]):
            raise Malformed('closure length')
        shapes[at] = (op, t, x)

    def tree(at, arm_of_case=False):
        op, t, x = shapes[at]
        typ = ref(t, len(types), 'type')
        if op in ('branch', 'default') and not arm_of_case:
            raise Malformed('standalone arm')
        if op == 'lit':
            if x[0] >= len(constants):
                raise Malformed('constant index')
            kind, value = constants[x[0]]
            return ['lit', typ, kind, value]
        if op in ('value', 'ref'):
            return [op, typ, x[0]]
        if op == 'default':
            return ['default', tree(child(x[0], at))]
        if op == 'branch':
            return ['branch', x[0], x[1], x[2], tree(child(x[3], at))]
        if op in ('prim', 'con', 'call', 'foreign'):
            return [op, typ, x[0], [tree(child(k, at)) for k in x[2:]]]
        if op == 'let':
            return ['let', typ, x[0], tree(child(x[1], at)), tree(child(x[2], at))]
        if op == 'case':
            slot, scrutinee, mode, n = x[:4]
            if mode == 0:
                rows = [None if a == NONE else tree(child(a, at), True) for a in x[4:4 + n]]
            else:
                rows = []
                for i in range(n):
                    arm = tree(child(x[5 + 2 * i], at), True)
                    if arm[0] != 'branch' or arm[1] != x[4 + 2 * i]:
                        raise Malformed('case key')
                    rows.append(arm)
            last = x[-1]
            default = None if last == NONE else tree(child(last, at), True)
            if any(r is not None and r[0] != 'branch' for r in rows) or (
                    default is not None and default[0] != 'default'):
                raise Malformed('case arm kind')
            return ['case', typ, slot, ref(scrutinee, len(types), 'type'), CASE_MODES[mode], rows, default]
        if op == 'closure':
            return ['closure', typ, x[1], x[2], list(x[4:4 + x[3]]), tree(child(x[-1], at))]
        if op == 'invoke':
            return ['invoke', typ, tree(child(x[0], at)), [tree(child(k, at)) for k in x[2:]]]
        raise Malformed('opcode')

    plan_functions, roots = [], set()
    for _, r in funcs:
        if len(r) < 5 or len(r) != 5 + r[2]:
            raise Malformed('function record')
        if r[4] not in start or r[4] in roots or r[4] in owner:
            raise Malformed('function root')
        roots.add(r[4])
        plan_functions.append({'name': text(r[0]), 'parameters': [ref(p, len(types), 'type') for p in r[5:]],
                               'result': ref(r[1], len(types), 'type'), 'slots': r[3],
                               'body': tree(r[4])})
    if len(owner) + len(roots) != len(node_records):
        raise Malformed('unreachable node')

    main = w[4]
    if main != NONE and (main >= len(plan_functions) or plan_functions[main]['name'] != 'main'):
        raise Malformed('main index')
    plan = {'entry': ENTRIES[w[3]], 'types': plan_types, 'functions': plan_functions}
    representation = {r: ref(i, len(types), 'type') for r, i in zip(REPRESENTATIONS, w[12:24]) if i != NONE}
    if representation:
        plan['representation'] = representation
    return plan


def safe_chr(code: int) -> str:
    # Plans spell String constants as text; codes outside Unicode keep a list form.
    if code > 0x10FFFF:
        raise Malformed('string code beyond plan text')
    return chr(code)


# ---------------------------------------------------------------- validation

def validate(plan: dict, registry: dict) -> list[str]:
    """Scope, arity and type rules of SPEC section 4 on a decoded plan."""
    errors: list[str] = []
    types, functions = plan['types'], plan['functions']
    rep = plan.get('representation', {})
    prims = {p['id']: p for p in registry['prims']}
    foreign = {f['id']: f for f in registry['foreign']}

    def fail(where, what):
        errors.append(f'{where}: {what}')

    def kind(t):
        return None if t is None else types[t]['kind']

    def live_fields(t, tag):
        return types[t]['constructors'][tag]['fields']

    for r, t in rep.items():
        if r in OPAQUE:
            if types[t]['kind'] != 'opaque':
                fail('representation', f'{r} must be opaque')
        elif types[t]['kind'] != 'data' or [len(c['fields']) for c in types[t]['constructors']] != SHAPES[r]:
            fail('representation', f'{r} shape')
    scalar = {rep.get('U32'): 'U32', rep.get('Char'): 'Char'}
    scalar.pop(None, None)
    names = [f['name'] for f in functions]
    if len(set(names)) != len(names):
        fail('functions', 'duplicate function name')
    if plan['entry'] == 'program':
        main = [f for f in functions if f['name'] == 'main']
        if not main or main[0]['parameters']:
            fail('program', 'main must exist with no live parameters')

    def kind_of_rep(t):
        return next((r for r, i in rep.items() if i == t), None)

    def same(a, b):
        return a is None or b is None or a == b

    def check(node, scope, where, used) -> int:
        """Returns the maximum scope depth reached; records slot uses in `used`."""
        op, depth = node[0], len(scope)
        if op in ('branch', 'default'):
            fail(where, f'standalone {op}')
            return depth
        t = node[1]
        if t is not None and t >= len(types):
            fail(where, 'type index')
            return depth
        if op == 'lit':
            if kind_of_rep(t) != node[2]:
                fail(where, f'{node[2]} literal at a non-{node[2]} type')
            return depth
        if op == 'value':
            if kind(t) != 'data' or node[2] >= len(types[t]['constructors']) or live_fields(t, node[2]):
                fail(where, 'value is not a nullary constructor')
            return depth
        if op == 'ref':
            if node[2] >= depth:
                fail(where, f'slot {node[2]} beyond depth {depth}')
            else:
                used.add(node[2])
                if not same(scope[node[2]], t):
                    fail(where, 'reference type')
            return depth
        if op == 'con':
            deepest = max([depth] + [check(k, scope, where, used) for k in node[3]])
            if kind(t) != 'data' or node[2] >= len(types[t]['constructors']):
                fail(where, 'construct tag')
            else:
                fields = live_fields(t, node[2])
                if not fields or len(fields) != len(node[3]):
                    fail(where, 'construct arity')
                elif not all(same(f, k[1]) for f, k in zip(fields, node[3])):
                    fail(where, 'construct field type')
            return deepest
        if op in ('prim', 'foreign', 'call'):
            deepest = max([depth] + [check(k, scope, where, used) for k in node[3]])
            if op == 'call':
                if node[2] >= len(functions):
                    fail(where, 'function index')
                    return deepest
                callee = functions[node[2]]
                arity, result = len(callee['parameters']), callee['result']
                inputs = callee['parameters']
            else:
                table = prims if op == 'prim' else foreign
                if node[2] not in table or table[node[2]].get('status') == 'reserved':
                    fail(where, f'unknown {op} id {node[2]}')
                    return deepest
                arity, result, inputs = len(table[node[2]]['inputs']), None, [None] * len(node[3])
                if op == 'prim':
                    expected = table[node[2]]['output']
                    if rep.get(expected, t) != t:
                        fail(where, f'prim result is not the pinned {expected}')
                    for k, name in zip(node[3], table[node[2]]['inputs']):
                        if rep.get(name, k[1]) != k[1]:
                            fail(where, f'prim operand is not the pinned {name}')
            if len(node[3]) != arity:
                fail(where, f'{op} arity')
            elif not same(result, t) or not all(same(p, k[1]) for p, k in zip(inputs, node[3])):
                fail(where, f'{op} types')
            return deepest
        if op == 'let':
            if node[2] != depth:
                fail(where, f'let slot {node[2]} at depth {depth}')
            a = check(node[3], scope, where, used)
            b = check(node[4], scope + [node[3][1]], where, used)
            if not same(node[4][1], t):
                fail(where, 'let body type')
            return max(a, b)
        if op == 'case':
            _, _, slot, scrutinee, mode, rows, default = node
            if slot >= depth:
                fail(where, 'case slot beyond depth')
                return depth
            used.add(slot)
            if not same(scope[slot], scrutinee):
                fail(where, 'case scrutinee type')
            deepest = depth
            if mode == 'tags':
                if kind(scrutinee) != 'data':
                    fail(where, 'tag case on a non-data type')
                    return depth
                ctors = types[scrutinee]['constructors']
                if len(rows) != len(ctors):
                    fail(where, 'tag table is not dense')
                if (default is None) != all(r is not None for r in rows):
                    fail(where, 'default must cover exactly the missing tags')
                for tag, r in enumerate(rows):
                    if r is None:
                        continue
                    if r[1] != tag or tag >= len(ctors):
                        fail(where, 'branch key')
                        continue
                    fields = ctors[tag]['fields']
                    if r[2] != depth or r[3] != len(fields):
                        fail(where, 'branch binders')
                        continue
                    deepest = max(deepest, check(r[4], scope + list(fields), where, used))
                    if not same(r[4][1], t):
                        fail(where, 'branch body type')
            else:
                if scrutinee not in scalar:
                    fail(where, 'key case on a non-scalar type')
                keys = [r[1] for r in rows]
                if keys != sorted(set(keys)) or default is None:
                    fail(where, 'keys must increase strictly, with a default')
                for r in rows:
                    if r[2] != depth or r[3] != 0:
                        fail(where, 'key branch binds nothing')
                        continue
                    deepest = max(deepest, check(r[4], scope, where, used))
            if default is not None:
                deepest = max(deepest, check(default[1], scope, where, used))
            return deepest
        if op == 'closure':
            _, _, live, slots, captures, body = node
            arrow = kind(t)
            if arrow not in ('arrow', 'erased-arrow') or live != (arrow == 'arrow'):
                fail(where, 'closure arrow')
                return depth
            if captures != sorted(set(captures)) or any(c >= depth for c in captures):
                fail(where, 'captures must increase strictly below depth')
                return depth
            used.update(captures)
            inner_scope = [scope[c] for c in captures] + ([types[t]['domain']] if live else [])
            inner_used: set[int] = set()
            deepest = check(body, inner_scope, where + '/closure', inner_used)
            if {s for s in inner_used if s < len(captures)} != set(range(len(captures))):
                fail(where, 'captures are not exactly the free slots of the body')
            if deepest != slots:
                fail(where, f'closure slots {slots}, reached {deepest}')
            if not same(body[1], types[t]['result']):
                fail(where, 'closure result type')
            return depth
        if op == 'invoke':
            deepest = max([check(node[2], scope, where, used)] + [check(a, scope, where, used) for a in node[3]])
            f = node[2][1]
            arrow = kind(f)
            if arrow not in ('arrow', 'erased-arrow') or len(node[3]) != (1 if arrow == 'arrow' else 0):
                fail(where, 'invoke arity')
            elif not same(types[f]['result'], t) or (node[3] and not same(types[f]['domain'], node[3][0][1])):
                fail(where, 'invoke types')
            return deepest
        fail(where, f'unknown node {op}')
        return depth

    for f in functions:
        if len(f['parameters']) > LIMITS['arity'] or f['slots'] > LIMITS['slots']:
            fail(f['name'], 'limits')
        used: set[int] = set()
        deepest = check(f['body'], list(f['parameters']), f['name'], used)
        if deepest != f['slots']:
            fail(f['name'], f'slots {f["slots"]}, reached {deepest}')
        if not same(f['body'][1], f['result']):
            fail(f['name'], 'body type')
    return errors


# ---------------------------------------------------------------- command line

def registry(path=Path(__file__).with_name('registry.json')) -> dict:
    return json.loads(path.read_text())


def base_digest(reg: dict) -> bytes:
    return bytes.fromhex(reg['base']['sha256'])


def main(argv):
    reg = registry()
    digest = base_digest(reg)
    if len(argv) == 3 and argv[0] == 'encode':
        plan = json.loads(Path(argv[1]).read_text())
        Path(argv[2]).write_bytes(encode(plan, digest))
    elif len(argv) == 2 and argv[0] == 'decode':
        print(json.dumps(decode(Path(argv[1]).read_bytes(), digest), indent=1))
    elif len(argv) == 2 and argv[0] == 'check':
        data = Path(argv[1]).read_bytes()
        plan = decode(data, digest)
        problems = validate(plan, reg)
        if encode(plan, digest) != data:
            problems.append('noncanonical encoding')
        print('\n'.join(problems) or 'valid')
        return 1 if problems else 0
    else:
        print('usage: serializer.py encode PLAN IMAGE | decode IMAGE | check IMAGE', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
