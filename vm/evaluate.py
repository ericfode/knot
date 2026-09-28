#!/usr/bin/env python3
"""Reference evaluation of a knot-image-1 plan: SPEC sections 6-10 on values, not cells.

A word is an int: a nullary constructor tag, or the value of a U32, Nat, Char or File
token, immediate and Big alike. An Object, Closure and Action is a tuple. There is no heap,
RC, frame region or quantum, so nothing here witnesses an address, a leak or a yield.
Entries are counted as section 7 debits them.

The gate reads the program's own value from it: the code lists a Program passes to
`IO.print`, in order, and a Book's result. Under the `vm` policy an outgoing String with a
non-scalar Char halts with `HostFailure io abi` before it is written (section 10, D20);
under the `native` policy every String is written as the seed's native lane writes it.
A Python exception other than `Halt` is a harness failure, never an outcome.
"""
from __future__ import annotations

WORD = 0xFFFFFFFF
DISPLAY_VISITS, DISPLAY_BYTES = 1 << 20, 16 << 20
TERMINAL = ('terminal',)
ILL_TYPED = {'outcome': 'HostFailure', 'cause': 'image ill-typed'}


class Halt(Exception):
    """The machine stopped without a value: Exhausted or HostFailure."""

    def __init__(self, outcome: dict):
        super().__init__(outcome)
        self.outcome = outcome


def scalar(code: int) -> bool:
    """A Unicode scalar value: neither a surrogate nor above U+10FFFF."""
    return code < 0xD800 or 0xDFFF < code <= 0x10FFFF


def utf8(code: int) -> bytes:
    """Generalized UTF-8, as the seed's native lane writes a Char: a surrogate encodes like a
    scalar, and from 2^21 the lead byte keeps only its low 8 bits, so Chr{0x401F600} writes
    F0 9F 98 80, the UTF-8 of U+1F600. On a scalar it is canonical UTF-8."""
    if code < 0x80:
        return bytes([code])
    if code < 0x800:
        return bytes([0xC0 | code >> 6, 0x80 | code & 0x3F])
    if code < 0x10000:
        return bytes([0xE0 | code >> 12, 0x80 | code >> 6 & 0x3F, 0x80 | code & 0x3F])
    return bytes([(0xF0 | code >> 18) & 0xFF, 0x80 | code >> 12 & 0x3F, 0x80 | code >> 6 & 0x3F, 0x80 | code & 0x3F])


def show(n: int) -> list:
    return [ord(c) for c in str(n)]


class Machine:
    def __init__(self, plan: dict, fuel: int, policy: str = 'vm'):
        self.types, self.functions = plan['types'], plan['functions']
        self.rep = plan.get('representation', {})
        self.fuel, self.calls, self.policy = fuel, 0, policy
        self.stdout, self.prints = bytearray(), []

    # ---------------------------------------------------------------- inspection (section 6)

    def view(self, w, t) -> tuple:
        """(tag, fields) of word `w` read at the concrete type `t`, or ill-typed."""
        if t == self.rep.get('Nat') and isinstance(w, int):
            return (0, ()) if w == 0 else (1, (w - 1,))
        if t == self.rep.get('Char') and isinstance(w, int):
            return 0, (w,)
        ctors = self.types[t].get('constructors') if t not in (self.rep.get('Nat'), self.rep.get('Char')) else None
        if ctors and isinstance(w, int) and w < len(ctors) and not ctors[w]['fields']:
            return w, ()
        if ctors and isinstance(w, tuple) and w[0] == 'obj' and w[1] == t and ctors[w[2]]['fields']:
            return w[2], w[3]
        raise Halt(ILL_TYPED)

    def word(self, w) -> int:
        if not isinstance(w, int):
            raise Halt(ILL_TYPED)
        return w

    def codes(self, s) -> list:
        out = []
        while True:
            tag, fields = self.view(s, self.rep['String'])
            if tag == 0:
                return out
            out.append(self.view(fields[0], self.rep['Char'])[1][0])
            s = fields[1]

    def string(self, codes) -> object:
        s = 0
        for code in reversed(codes):
            s = ('obj', self.rep['String'], 1, (code, s))
        return s

    def nat(self, n: int) -> int:
        if n > WORD:
            raise Halt({'outcome': 'Exhausted', 'kind': 2, 'cause': 'NatRange'})
        return n

    # ---------------------------------------------------------------- evaluation (sections 3, 6)

    def eval(self, node, env):
        op = node[0]
        if op == 'lit':
            return self.string(node[3]) if node[2] == 'String' else node[3]
        if op == 'value':
            return node[2]
        if op == 'ref':
            return env[node[2]]
        if op == 'let':
            env[node[2]] = self.eval(node[3], env)
            return self.eval(node[4], env)
        if op == 'case':
            return self.case(node, env)
        if op == 'closure':
            return ('closure', node, tuple(env[s] for s in node[4]))
        if op == 'invoke':
            f = self.eval(node[2], env)
            return self.apply(f, [self.eval(a, env) for a in node[3]])
        operands = [self.eval(k, env) for k in node[3]]
        if op == 'con':
            return self.construct(node[1], node[2], operands)
        if op == 'prim':
            return self.prim(node[2], operands)
        if op == 'foreign':
            return ('action', node[2], tuple(operands))
        return self.call(node[2], operands)

    def construct(self, t, tag, operands):
        if t == self.rep.get('Nat'):
            return self.nat(self.word(operands[0]) + 1)
        if t == self.rep.get('Char'):
            return self.word(operands[0])
        return ('obj', t, tag, tuple(operands))

    def case(self, node, env):
        _, _, slot, t, mode, rows, default = node
        if mode == 'keys':
            key = self.word(env[slot])
            arm, fields = next((r for r in rows if r[1] == key), default), ()
        else:
            tag, fields = self.view(env[slot], t)
            arm = rows[tag] or default
        if arm[0] == 'branch':
            env[arm[2]:arm[2] + len(fields)] = fields
        return self.eval(arm[-1], env)

    # ---------------------------------------------------------------- entry (section 7)

    def debit(self):
        if self.fuel == 0:
            raise Halt({'outcome': 'Exhausted', 'kind': 1, 'cause': 'fuel'})
        self.fuel -= 1
        self.calls += 1

    def call(self, index: int, operands: list):
        self.debit()
        f = self.functions[index]
        return self.eval(f['body'], operands + [None] * f['slots'])

    def apply(self, f, operands: list):
        """Enter a value: the operand check precedes the debit."""
        kind = f[0] if isinstance(f, tuple) else None
        takes = {'closure': lambda: len(operands) == f[1][2], 'action': lambda: len(operands) <= 1,
                 'terminal': lambda: len(operands) == 1}
        if kind not in takes or not takes[kind]():
            raise Halt(ILL_TYPED)
        self.debit()
        if kind == 'closure':
            node, captures = f[1], list(f[2])
            return self.eval(node[5], captures + operands + [None] * node[3])
        if kind == 'terminal':
            return ('obj', self.rep['IO.OP'], 0, (operands[0],))
        if not operands:
            return f
        return self.apply(operands[0], [self.effect(f)])

    def effect(self, action):
        """Section 10: one Action applied to its continuation performs exactly one effect."""
        _, foreign, operands = action
        if foreign != 1:
            raise NotImplementedError(f'foreign {foreign} has no reference effect')
        codes = self.codes(operands[0])
        self.prints.append(codes)
        if self.policy == 'vm' and not all(map(scalar, codes)):
            raise Halt({'outcome': 'HostFailure', 'cause': 'io abi'})
        self.stdout += b''.join(map(utf8, codes)) + b'\n'
        return 0

    # ---------------------------------------------------------------- primitives (section 9)

    def prim(self, p: int, a: list):
        if p <= 15:
            x, y = self.word(a[0]), self.word(a[-1])
            return [lambda: (x + y) & WORD, lambda: (x - y) & WORD, lambda: (x * y) & WORD,
                    lambda: x // y if y else 0, lambda: x % y if y else x, lambda: ~x & WORD,
                    lambda: x & y, lambda: (x > y) - (x < y) + 1, lambda: int(x == y), lambda: int(x != y),
                    lambda: int(x < y), lambda: int(x <= y), lambda: int(x > y), lambda: int(x >= y),
                    lambda: x << y & WORD if y < 32 else 0, lambda: x >> y if y < 32 else 0][p]()
        if p in (16, 17, 18, 19):
            return self.word(a[0])
        if p in (20, 21):
            x = self.word(a[0])
            return int(x == self.word(a[1])) if p == 20 else int(9 <= x <= 13 or x == 32)
        if p <= 31:
            x, y = self.word(a[0]), self.word(a[1])
            return [lambda: self.nat(x + y), lambda: max(x - y, 0), lambda: self.nat(x * y),
                    lambda: (x > y) - (x < y) + 1, lambda: int(x == y), lambda: int(x != y),
                    lambda: int(x < y), lambda: int(x <= y), lambda: int(x > y), lambda: int(x >= y)][p - 22]()
        if p in (32, 33):
            return self.string(show(self.word(a[0])))
        s = self.codes(a[0])
        if p == 34:
            return int(s == self.codes(a[1]))
        if p == 35:
            return self.string(s + self.codes(a[1]))
        return [lambda: self.string(s[::-1]), lambda: len(s), lambda: int(not s)][p - 36]()

    # ---------------------------------------------------------------- results (section 8)

    def describe(self, w, t) -> str:
        """`Evaluated<TAB>type<TAB>tag<TAB>tree<LF>`, rendered iteratively within section 8's
        bounds. A visit is one rendered constructor, so a Nat word n costs n + 1; the tree's
        bytes, separators included, are its text. Both bounds are inclusive, and each charge
        is checked before its text is built."""
        nat = self.rep.get('Nat')
        out, cost, work = [], [0, 0], [(w, t)]

        def charge(visits: int, size: int):
            cost[0] += visits
            cost[1] += size
            if cost[0] > DISPLAY_VISITS or cost[1] > DISPLAY_BYTES:
                raise Halt({'outcome': 'Exhausted', 'kind': 2, 'cause': 'display'})
        while work:
            item = work.pop()
            if isinstance(item, str):
                charge(0, len(item))
                out.append(item)
                continue
            v, u = item
            tag, fields = self.view(v, u)
            if u == nat:
                zero, succ = (c['name'] for c in self.types[nat]['constructors'])
                charge(v + 1, v * (len(succ.encode()) + 2) + len(zero.encode()) + 2)
                out.append(f'{succ}{{' * v + f'{zero}{{}}' + '}' * v)
                continue
            ctor = self.types[u]['constructors'][tag]
            charge(1, len(ctor['name'].encode()) + 1)
            out.append(ctor['name'] + '{')
            parts = [p for i, f in enumerate(zip(fields, ctor['fields'])) for p in ((',',) if i else ()) + (f,)]
            work += ['}'] + parts[::-1]
        return f'Evaluated\t{t}\t{self.view(w, t)[0]}\t{"".join(out)}\n'


def book(plan: dict, name: str, ordinals: list, fuel: int) -> dict:
    """A Book invocation whose section 8 checks passed: the ordinals are the live arguments."""
    m = Machine(plan, fuel)
    index = next(i for i, f in enumerate(plan['functions']) if f['name'] == name)
    try:
        w = m.call(index, list(ordinals))
        return {'exit': 0, 'stdout': m.describe(w, plan['functions'][index]['result']), 'calls': m.calls}
    except Halt as h:
        return {**h.outcome, 'calls': m.calls}


def program(plan: dict, fuel: int, policy: str = 'vm') -> dict:
    """Section 8's Program phases; `stdout` holds the bytes written, `prints` every String
    passed to IO.print (the refused one included)."""
    m = Machine(plan, fuel, policy)
    try:
        w = m.call(next(i for i, f in enumerate(plan['functions']) if f['name'] == 'main'), [])
        w = m.apply(w, [])
        w = m.apply(w, [TERMINAL])
        tag, fields = m.view(w, m.rep['IO.OP'])
        outcome = {'exit': 0} if tag == 0 else {'halt': m.word(fields[0]), 'message': m.codes(fields[1])}
    except Halt as h:
        outcome = h.outcome
    return {**outcome, 'stdout': bytes(m.stdout), 'prints': m.prints, 'calls': m.calls}
