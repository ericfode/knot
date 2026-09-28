"""Independent imperative graph oracle. Never imports the Bend model or its output."""
from copy import deepcopy

OK, INVALID, UNSUPPORTED, EXHAUSTED = range(4)


class Reject(Exception):
    def __init__(self, status):
        self.status = status


class Store:
    def __init__(self, policy, capacity=100000, ceiling=100000):
        self.policy, self.capacity, self.ceiling = policy, capacity, ceiling
        self.nodes, self.roots, self.leases = {}, {}, {}
        self.pending, self.drops = [], []
        self.next = 1
        self.cost = [0] * 10

    def words(self, node):
        kind, _, children, _ = node
        return 2 + len(children) + (self.policy == 'B' and kind == 1)

    def root(self, slot):
        if slot not in self.roots:
            raise Reject(INVALID)
        return self.roots[slot]

    def vacant(self, slots):
        if len(set(slots)) != len(slots) or any(s in self.roots for s in slots):
            raise Reject(INVALID)

    def allocate(self, kind, tag, children):
        node = [kind, tag, children, 1]
        words = self.words(node)
        if self.cost[7] + words > self.capacity:
            raise Reject(EXHAUSTED)
        ref = self.next
        self.next += 1
        self.nodes[ref] = node
        self.cost[0] += 1
        self.cost[7] += words
        self.cost[8] = max(self.cost[8], self.cost[7])
        return ref

    def acquire(self, ref):
        node = self.nodes[ref]
        if node[0] != 1:
            raise Reject(UNSUPPORTED)
        if node[3] >= self.ceiling:
            raise Reject(EXHAUSTED)
        node[3] += 1
        self.cost[4] += 1
        return ref

    def clone(self, ref):
        kind, tag, children, _ = self.nodes[ref]
        copied = [self.clone(c) for c in children]
        self.cost[2] += 2 + len(children)
        self.cost[3] += len(children)
        return self.allocate(kind, tag, copied)

    def free(self, ref):
        node = self.nodes.pop(ref)
        self.cost[1] += 1
        self.cost[7] -= self.words(node)

    def queue(self, refs):
        self.pending = refs + self.pending
        self.cost[9] = max(self.cost[9], len(self.pending))

    def execute(self, op):
        name, *args = op
        if name == 'alloc':
            dst, kind, tag, *slots = args
            self.vacant([dst])
            if kind not in (0, 1) or len(slots) > 2 or len(set(slots)) != len(slots):
                raise Reject(INVALID)
            children = [self.root(s) for s in slots]
            if kind == 1 and any(self.nodes[c][0] == 0 for c in children):
                raise Reject(INVALID)
            ref = self.allocate(kind, tag, children)
            for s in slots:
                del self.roots[s]
            self.roots[dst] = ref
        elif name == 'share':
            src, dst = args
            ref = self.root(src)
            self.vacant([dst])
            if self.nodes[ref][0] != 1:
                raise Reject(UNSUPPORTED)
            self.roots[dst] = self.clone(ref) if self.policy == 'A' else self.acquire(ref)
        elif name == 'take':
            src, *slots = args
            ref = self.root(src)
            self.vacant(slots)
            node = self.nodes[ref]
            if len(slots) != len(node[2]):
                raise Reject(INVALID)
            if self.leases:
                raise Reject(UNSUPPORTED)
            self.cost[3] += len(node[2])
            if self.policy == 'B' and node[0] == 1:
                self.cost[5] += 1
            if node[3] == 1:
                self.free(ref)
            else:
                for c in node[2]:
                    self.acquire(c)
                node[3] -= 1
            del self.roots[src]
            for s, c in zip(slots, node[2]):
                self.roots[s] = c
        elif name == 'move':
            src, dst = args
            ref = self.root(src)
            self.vacant([dst])
            del self.roots[src]
            self.roots[dst] = ref
        elif name == 'release':
            ref = self.root(args[0])
            del self.roots[args[0]]
            self.queue([ref])
        elif name == 'clean':
            budget, = args
            if self.pending and self.leases:
                return EXHAUSTED
            while budget and self.pending:
                budget -= 1
                ref = self.pending.pop(0)
                node = self.nodes[ref]
                self.cost[6] += 1
                if self.policy == 'B' and node[0] == 1:
                    self.cost[5] += 1
                if node[3] > 1:
                    node[3] -= 1
                else:
                    self.cost[3] += len(node[2])
                    self.queue(node[2])
                    if node[0] == 0:
                        self.drops.insert(0, node[1])
                    self.free(ref)
            return EXHAUSTED if self.pending else OK
        elif name == 'pin':
            src, lease = args
            ref = self.root(src)
            if lease in self.leases:
                raise Reject(INVALID)
            self.leases[lease] = ref
        elif name == 'ack':
            lease, = args
            if lease not in self.leases:
                raise Reject(INVALID)
            del self.leases[lease]
        elif name == 'cycle':
            raise Reject(UNSUPPORTED)
        else:
            raise Reject(UNSUPPORTED)
        return OK

    def step(self, op):
        before = deepcopy(self.__dict__)
        try:
            result = self.execute(op)
        except Reject as error:
            self.__dict__ = before
            result = error.status
        self.invariant()
        return self.wire(result)

    def invariant(self):
        incoming = {ref: 0 for ref in self.nodes}
        for ref in list(self.roots.values()) + self.pending:
            incoming[ref] += 1
        for ref, (kind, _, children, count) in self.nodes.items():
            for child in children:
                assert child < ref, ('cycle', ref, child)
                assert kind == 0 or self.nodes[child][0] == 1
                incoming[child] += 1
            assert count >= 1
        for ref, count in incoming.items():
            assert count == self.nodes[ref][3], ('unbalanced', ref, count)
            assert count == 1 or (self.policy == 'B' and self.nodes[ref][0] == 1)
        assert all(ref in self.nodes for ref in self.leases.values())
        assert self.cost[7] == sum(self.words(n) for n in self.nodes.values())
        assert self.cost[7] <= self.capacity
        assert self.cost[0] - self.cost[1] == len(self.nodes)

    def wire(self, status):
        slots = lambda xs: ','.join(f'{s}:{r}' for s, r in reversed(list(xs.items())))
        nodes = ';'.join(f'{r}:{k}:{t}:{n}:' + ','.join(map(str, cs))
                         for r, (k, t, cs, n) in sorted(self.nodes.items(), reverse=True))
        seq = lambda xs: ','.join(map(str, xs))
        return '|'.join(map(str, [status, self.next, slots(self.roots), nodes,
                                  seq(self.pending), slots(self.leases),
                                  seq(self.cost), seq(self.drops)]))


def run(case, policy):
    store = Store(policy, case.get('capacity', 100000), case.get('ceiling', 100000))
    return [store.step(op) for op in case['ops']]
