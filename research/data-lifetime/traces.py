"""Fixed-seed workload construction; no policy implementation or expected costs."""
import random


def fixtures():
    return [
        dict(name='unique-drop', ops=[['alloc', 0, 0, 7], ['release', 0], ['clean', 0], ['clean', 1]]),
        dict(name='two-holders', ops=[['alloc', 0, 1, 9], ['share', 0, 1], ['release', 0], ['clean', 8], ['release', 1], ['clean', 8]]),
        dict(name='zero-capacity', capacity=0, ops=[['alloc', 0, 1, 9]]),
        dict(name='copy-capacity', capacity=3, ops=[['alloc', 0, 1, 9], ['share', 0, 1], ['release', 0], ['clean', 8]]),
        dict(name='count-ceiling', ceiling=2, ops=[['alloc', 0, 1, 9], ['share', 0, 1], ['share', 0, 2]]),
        dict(name='unique-reject', ops=[['alloc', 0, 0, 7], ['share', 0, 1], ['alloc', 1, 1, 9, 0], ['cycle']]),
        dict(name='rebuild', ops=[['alloc', 0, 0, 7], ['alloc', 1, 1, 9], ['alloc', 2, 0, 13, 0, 1], ['take', 2, 3, 4], ['alloc', 5, 0, 13, 3, 4], ['release', 5], ['clean', 1], ['clean', 1], ['clean', 1]]),
        dict(name='shared-open', ops=[['alloc', 0, 1, 9], ['alloc', 1, 1, 11], ['alloc', 2, 1, 5, 0, 1], ['share', 2, 3], ['take', 3, 4, 5], ['release', 2], ['clean', 20], ['release', 4], ['release', 5], ['clean', 20]]),
        dict(name='open-overflow-rollback', ceiling=3, ops=[['alloc', 0, 1, 9], ['share', 0, 1], ['alloc', 2, 1, 5, 0, 1], ['share', 2, 3], ['take', 3, 4, 5]]),
        dict(name='occupied-delivery', ops=[['alloc', 0, 0, 7], ['alloc', 1, 0, 9], ['move', 0, 1], ['move', 0, 2], ['move', 0, 3], ['release', 1], ['release', 2], ['clean', 8]]),
        dict(name='reader-barrier', ops=[['alloc', 0, 0, 7], ['pin', 0, 5], ['pin', 0, 6], ['take', 0], ['release', 0], ['clean', 8], ['ack', 5], ['clean', 8], ['ack', 6], ['clean', 1], ['alloc', 0, 0, 11]]),
        dict(name='invalid-neighbors', ops=[['take', 0], ['ack', 0], ['alloc', 0, 1, 9], ['alloc', 0, 1, 11], ['pin', 0, 0], ['pin', 0, 0], ['share', 0, 0], ['take', 0, 1], ['alloc', 1, 1, 5, 0, 0]]),
    ] + [roots(cancel) for cancel in (False, True)]


def roots(cancel):
    # 10 is a suspended frame, 20 a delivered join slot, 30 an in-flight reader.
    ops = [['alloc', 0, 1, 9], ['alloc', 1, 1, 11], ['alloc', 2, 1, 5, 0, 1],
           ['share', 2, 3], ['share', 2, 4], ['alloc', 5, 0, 7],
           ['alloc', 6, 0, 13, 5, 3], ['move', 6, 10], ['move', 4, 20],
           ['pin', 20, 30], ['release', 2], ['clean', 0], ['clean', 1]]
    if cancel:
        ops += [['release', 10], ['release', 20]]
    else:
        ops += [['move', 10, 11], ['ack', 30], ['take', 11, 12, 13],
                ['take', 13, 14, 15], ['alloc', 16, 1, 5, 14, 15],
                ['alloc', 17, 0, 13, 12, 16], ['alloc', 21, 0, 9],
                ['alloc', 22, 0, 709, 20, 21], ['release', 17], ['release', 22]]
    if cancel:
        ops += [['clean', 1], ['ack', 30]]
    ops += [['clean', 0], ['clean', 1], ['clean', 1000]]
    return dict(name='cancel-roots' if cancel else 'suspend-join-resume', ops=ops)


class Program:
    def __init__(self):
        self.ops, self.next = [], 0

    def alloc(self, kind, tag, *children):
        slot = self.next
        self.next += 1
        self.ops.append(['alloc', slot, kind, tag, *children])
        return slot

    def share(self, root):
        slot = self.next
        self.next += 1
        self.ops.append(['share', root, slot])
        return slot

    def tree(self, depth, kind=1):
        if depth == 0:
            return self.alloc(kind, 9 + self.next % 7)
        return self.alloc(kind, 5, self.tree(depth - 1, kind), self.tree(depth - 1, kind))

    def end(self, *roots):
        for root in roots:
            self.ops.append(['release', root])
        self.ops += [['clean', 0], ['clean', 1], ['clean', 100000]]


def cases():
    out = fixtures()
    for size in (1, 2, 4, 8, 16, 32, 64):
        p = Program()
        root = p.alloc(1, 0)
        for i in range(size):
            root = p.alloc(1, i + 1, root)
        alias = p.share(root)
        p.end(root, alias)
        out.append(dict(name=f'list-{size}', family='list', size=size, ops=p.ops))
    for depth in range(1, 6):
        p = Program()
        root = p.tree(depth)
        aliases = [p.share(root) for _ in range(4)]
        p.end(root, *aliases)
        out.append(dict(name=f'tree-{depth}', family='tree', size=2 ** (depth + 1) - 1, ops=p.ops))
    for depth in range(1, 9):
        p = Program()
        root = p.alloc(1, 9)
        for _ in range(depth):
            alias = p.share(root)
            root = p.alloc(1, 5, root, alias)
        p.end(root)
        out.append(dict(name=f'dag-{depth}', family='shared-subterm', size=depth, ops=p.ops))
    for count in (1, 4, 16, 64):
        p = Program()
        root = p.alloc(0, 7, p.alloc(1, 9))
        for _ in range(count):
            child = p.next
            p.next += 1
            p.ops.append(['take', root, child])
            root = p.alloc(0, 7, child)
        p.end(root)
        out.append(dict(name=f'rebuild-{count}', family='rebuild', size=count, capacity=16, ops=p.ops))
    rng = random.Random(0xDADA)
    for i in range(64):
        p = Program()
        root = p.tree(rng.randrange(4), rng.randrange(2))
        # Some requests are deliberately Unsupported; clean still owns the input.
        alias = p.share(root)
        p.ops += [['move', alias, 1000], ['pin', root, 0], ['release', root],
                  ['clean', rng.randrange(3)], ['ack', 0], ['release', 1000], ['clean', 100000]]
        out.append(dict(name=f'generated-{i}', family='mixed', size=i, capacity=512, ops=p.ops))
    return out
