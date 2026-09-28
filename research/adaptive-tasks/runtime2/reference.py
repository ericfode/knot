"""Independent research oracle for the literal device-records-2 contract.

This model uses Python objects and an owning graph, not the device word layout
or the Bend transition implementation. Every observation includes a fresh
whole-graph ownership audit. It is not a compiler or a production host runtime.
"""

from collections import Counter
from dataclasses import dataclass, field


U32_MAX = 0xFFFFFFFF
OK, INVALID, UNSUPPORTED, EXHAUSTED = range(4)
TYPE, DATA = range(2)
UNUSED, WAITING, READY, CANCELLED, RESUMED = range(5)


@dataclass
class Object:
    identity: int
    kind: int
    rc: int
    tag: int
    children: list[int]

    def wire(self):
        return [self.identity, self.kind, self.rc, self.tag, self.children.copy()]


@dataclass
class Join:
    attempt: int = 0
    state: int = UNUSED
    arity: int = 0
    received: int = 0
    completions: int = 0
    code: int = 0
    capture_base: int = 0
    capture_count: int = 0
    results: list[int] = field(default_factory=list)

    def wire(self):
        return [self.attempt, self.state, self.arity, self.received,
                self.completions, self.code, self.capture_base,
                self.capture_count, self.results.copy()]


class Rejected(Exception):
    def __init__(self, status):
        self.status = status


def require(condition, status=INVALID):
    if not condition:
        raise Rejected(status)


def invariant(condition, message):
    if not condition:
        raise AssertionError(message)


def word(value):
    return type(value) is int and 0 <= value <= U32_MAX


class Reference:
    """Execute capture-indexed instructions from an empty, validated bundle."""

    # Number of meaningful words, including the opcode; the rest must be zero.
    WIDTHS = {1: 6, 2: 3, 3: 3, 4: 4, 5: 2, 6: 2, 7: 2,
              8: 6, 9: 5, 10: 3, 11: 4, 12: 2, 13: 5}

    def __init__(self, config):
        self.config = dict(config)
        self.config.setdefault("instructionCount", U32_MAX)
        for name in ("objects", "captures", "pending", "joins", "arity",
                     "instructionCount"):
            if not word(self.config[name]):
                raise ValueError(f"unvalidated configuration: {name}")
        for name in ("rcLimit", "idLimit", "attemptLimit"):
            if not word(self.config[name]) or self.config[name] == 0:
                raise ValueError(f"unvalidated configuration: {name}")
        self.objects = [None] * self.config["objects"]
        self.captures = [0] * self.config["captures"]
        self.pending = []
        self.joins = [Join() for _ in range(self.config["joins"])]
        self.next_identity = 1
        self.readers = 0
        self.freed = 0
        self.status = OK
        self.reply = 0
        self.audit()

    def observe(self):
        return [self.status, self.reply, self.next_identity, self.readers,
                self.freed, [obj.wire() if obj else [] for obj in self.objects],
                self.captures.copy(), self.pending.copy(),
                [join.wire() for join in self.joins]]

    def step(self, command):
        before = self.observe()[2:]
        self.reply = 0
        opcode = None
        try:
            require(isinstance(command, (list, tuple)) and len(command) <= 8)
            require(all(word(value) for value in command))
            command = list(command) + [0] * (8 - len(command))
            opcode = command[0]
            require(opcode in self.WIDTHS, UNSUPPORTED)
            require(not any(command[self.WIDTHS[opcode]:]))
            self.status = self._execute(opcode, command[1:])
        except Rejected as rejected:
            self.status = rejected.status
        self.audit()
        if self.status != OK and opcode != 6:
            invariant(self.observe()[2:] == before,
                      "rejected instruction changed owning state")
        return self.observe()

    def _capture(self, index, occupied=None):
        require(index < len(self.captures))
        identity = self.captures[index]
        if occupied is not None:
            require(bool(identity) == occupied)
        return identity

    def _range(self, first, count):
        # Division/subtraction checks model a range without host word wrapping.
        require(first <= len(self.captures))
        require(count <= len(self.captures) - first)
        return range(first, first + count)

    def _object(self, identity):
        for slot, obj in enumerate(self.objects):
            if obj is not None and obj.identity == identity:
                return slot, obj
        raise AssertionError(f"owning edge targets absent object {identity}")

    def _join(self, index, attempt=None, states=None):
        require(index < len(self.joins))
        join = self.joins[index]
        if attempt is not None:
            require(join.attempt == attempt)
        if states is not None:
            require(join.state in states)
        return join

    def _execute(self, opcode, operands):
        a, b, c, d, e, _, _ = operands
        if opcode == 1:
            self._construct(a, b, c, d, e)
        elif opcode == 2:
            self._share(a, b)
        elif opcode == 3:
            identity = self._capture(a, True)
            self._capture(b, False)
            self.captures[a], self.captures[b] = 0, identity
        elif opcode == 4:
            self._open(a, b, c)
        elif opcode == 5:
            identity = self._capture(a, True)
            require(len(self.pending) < self.config["pending"], EXHAUSTED)
            self.pending.append(identity)
            self.captures[a] = 0
        elif opcode == 6:
            return self._clean(a)
        elif opcode == 7:
            self.readers = a
        elif opcode == 8:
            self._start(a, b, c, d, e)
        elif opcode == 9:
            self._deliver(a, b, c, d)
        elif opcode == 10:
            self._cancel(a, b)
        elif opcode == 11:
            self._resume(a, b, c)
        elif opcode == 12:
            _, obj = self._object(self._capture(a, True))
            self.reply = obj.tag
        elif opcode == 13:
            require(c != 0)
            require(a <= d and b <= (d - a) // c, EXHAUSTED)
            self.reply = a + b * c
        return OK

    def _construct(self, dst, kind, tag, first, count):
        self._capture(dst, False)
        require(kind in (TYPE, DATA))
        sources = self._range(first, count)
        require(dst not in sources)
        children = [self._capture(index, True) for index in sources]
        if kind == DATA:
            require(all(self._object(identity)[1].kind == DATA
                        for identity in children))
        require(count <= self.config["arity"], EXHAUSTED)
        free = next((i for i, obj in enumerate(self.objects) if obj is None), None)
        require(free is not None and self.next_identity != 0, EXHAUSTED)
        identity = self.next_identity
        self.objects[free] = Object(identity, kind, 1, tag, children)
        self.next_identity = (identity + 1
                              if identity < self.config["idLimit"] else 0)
        for index in sources:
            self.captures[index] = 0
        self.captures[dst] = identity

    def _share(self, src, dst):
        identity = self._capture(src, True)
        self._capture(dst, False)
        _, obj = self._object(identity)
        require(obj.kind == DATA, UNSUPPORTED)
        require(obj.rc < self.config["rcLimit"], EXHAUSTED)
        obj.rc += 1
        self.captures[dst] = identity

    def _open(self, src, first, count):
        slot, obj = self._object(self._capture(src, True))
        destinations = self._range(first, count)
        require(src not in destinations and count == len(obj.children))
        require(all(self._capture(index) == 0 for index in destinations))
        require(self.readers == 0, EXHAUSTED)
        if obj.kind == DATA and obj.rc > 1:
            acquisitions = Counter(obj.children)
            for identity, amount in acquisitions.items():
                child = self._object(identity)[1]
                require(amount <= self.config["rcLimit"] - child.rc, EXHAUSTED)
            for identity, amount in acquisitions.items():
                self._object(identity)[1].rc += amount
            obj.rc -= 1
        else:
            self.objects[slot] = None
            self.freed += 1
        self.captures[src] = 0
        for index, identity in zip(destinations, obj.children):
            self.captures[index] = identity

    def _clean(self, budget):
        if self.readers:
            return EXHAUSTED
        while self.pending and budget:
            slot, obj = self._object(self.pending[-1])
            last = obj.kind == TYPE or obj.rc == 1
            children = obj.children if last else []
            if len(children) > self.config["pending"] - len(self.pending) + 1:
                return EXHAUSTED
            self.pending.pop()
            if last:
                self.objects[slot] = None
                self.freed += 1
                self.pending.extend(children)
            else:
                obj.rc -= 1
            budget -= 1
        return EXHAUSTED if self.pending else OK

    def _start(self, index, arity, code, first, count):
        join = self._join(index, states=(UNUSED, CANCELLED, RESUMED))
        captures = self._range(first, count)
        require(code < self.config["instructionCount"])
        for other_index, other in enumerate(self.joins):
            if other_index != index and other.state in (WAITING, READY):
                other_end = other.capture_base + other.capture_count
                require(not count or not other.capture_count
                        or first >= other_end or other.capture_base >= captures.stop)
        require(arity <= self.config["arity"], EXHAUSTED)
        require(join.attempt < self.config["attemptLimit"], EXHAUSTED)
        join.attempt += 1
        join.state = READY if arity == 0 else WAITING
        join.arity = arity
        join.received = 0
        join.completions += int(arity == 0)
        join.code = code
        join.capture_base = first
        join.capture_count = count
        join.results = [0] * arity

    def _deliver(self, index, attempt, slot, src):
        join = self._join(index, attempt, (WAITING,))
        require(slot < join.arity)
        require(join.results[slot] == 0)
        identity = self._capture(src, True)
        join.results[slot] = identity
        self.captures[src] = 0
        join.received += 1
        if join.received == join.arity:
            join.state = READY
            join.completions += 1

    def _cancel(self, index, attempt):
        join = self._join(index, attempt, (WAITING, READY))
        saved = self._range(join.capture_base, join.capture_count)
        releases = [self.captures[i] for i in saved if self.captures[i]]
        releases.extend(identity for identity in join.results if identity)
        require(len(releases) <= self.config["pending"] - len(self.pending),
                EXHAUSTED)
        self.pending.extend(releases)
        for capture in saved:
            self.captures[capture] = 0
        join.results = [0] * join.arity
        join.received = 0
        join.state = CANCELLED

    def _resume(self, index, attempt, first):
        join = self._join(index, attempt, (READY,))
        destinations = self._range(first, join.arity)
        require(all(self._capture(i) == 0 for i in destinations))
        for index, identity in zip(destinations, join.results):
            self.captures[index] = identity
        join.results = [0] * join.arity
        join.state = RESUMED
        self.reply = join.code

    def audit(self):
        """Recount every owning edge without using operation-side RC updates."""
        config = self.config
        invariant(len(self.objects) == config["objects"], "object capacity changed")
        invariant(len(self.captures) == config["captures"], "capture capacity changed")
        invariant(len(self.pending) <= config["pending"], "pending stack overflow")
        invariant(len(self.joins) == config["joins"], "join capacity changed")
        invariant(word(self.readers) and word(self.reply), "invalid scalar word")
        live = {obj.identity: obj for obj in self.objects if obj is not None}
        invariant(len(live) == sum(obj is not None for obj in self.objects),
                  "object identity reused")
        issued = self.next_identity - 1 if self.next_identity else config["idLimit"]
        invariant(0 <= issued <= config["idLimit"], "invalid identity counter")
        invariant(issued == self.freed + len(live), "lost or duplicated physical cell")
        owners = Counter()

        def edge(identity):
            invariant(identity in live, f"dangling owner {identity}")
            owners[identity] += 1

        roots = [identity for identity in self.captures if identity]
        roots.extend(self.pending)
        active_ranges = []
        for join in self.joins:
            invariant(join.state in (UNUSED, WAITING, READY, CANCELLED, RESUMED),
                      "unknown join state")
            invariant(0 <= join.attempt <= config["attemptLimit"], "attempt overflow")
            invariant(0 <= join.completions <= join.attempt, "completion duplicated")
            invariant(0 <= join.arity <= config["arity"], "join arity overflow")
            invariant(len(join.results) == join.arity, "join result shape changed")
            invariant(0 <= join.capture_base <= len(self.captures)
                      and 0 <= join.capture_count <= len(self.captures) - join.capture_base,
                      "invalid saved capture range")
            if join.state == UNUSED:
                invariant(join.wire() == [0] * 8 + [[]], "nonempty unused join")
                continue
            invariant(join.attempt > 0 and join.code < config["instructionCount"],
                      "join has no valid attempt or code")
            filled = sum(identity != 0 for identity in join.results)
            if join.state == WAITING:
                invariant(0 <= join.received == filled < join.arity,
                          "waiting join is complete or miscounted")
                invariant(join.completions < join.attempt,
                          "waiting attempt already counted complete")
            elif join.state == READY:
                invariant(join.received == filled == join.arity
                          and join.completions > 0, "ready join is incomplete")
            elif join.state == CANCELLED:
                invariant(join.received == filled == 0, "cancelled join owns results")
            else:
                invariant(join.received == join.arity and filled == 0
                          and join.completions > 0, "resumed join owns results")
            if join.state in (WAITING, READY) and join.capture_count:
                active_ranges.append((join.capture_base,
                                      join.capture_base + join.capture_count))
            roots.extend(identity for identity in join.results if identity)
        active_ranges.sort()
        invariant(all(left[1] <= right[0]
                      for left, right in zip(active_ranges, active_ranges[1:])),
                  "active joins overlap their saved capture ranges")
        for identity in roots:
            edge(identity)
        for identity, obj in live.items():
            invariant(0 < identity <= issued, "object identity was never issued")
            invariant(obj.kind in (TYPE, DATA) and word(obj.tag), "invalid object record")
            invariant(len(obj.children) <= config["arity"], "object arity overflow")
            invariant(0 < obj.rc <= config["rcLimit"], "invalid reference count")
            for child in obj.children:
                edge(child)
                invariant(child < identity, "object graph is cyclic or backpatched")
                invariant(obj.kind != DATA or live[child].kind == DATA,
                          "Data contains a unique Type child")
        for identity, obj in live.items():
            invariant(owners[identity] == obj.rc, f"RC mismatch for {identity}")
            invariant(obj.kind != TYPE or owners[identity] == 1,
                      f"Type object {identity} has multiple owners")
        reachable, work = set(), roots.copy()
        while work:
            identity = work.pop()
            if identity not in reachable:
                reachable.add(identity)
                work.extend(live[identity].children)
        invariant(reachable == set(live), "unreachable live objects")
