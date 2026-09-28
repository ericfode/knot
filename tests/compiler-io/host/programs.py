"""Hand translations of PLAN's fixtures into deferred actions and IO.OP terminals.

This module consumes fixture argv, never seed output or sandbox contents. WAT
continuations compute all reports from actual ABI responses.
"""
import struct
from pathlib import Path

TEMPLATE = Path(__file__).with_name('runtime.wat')


class Program:
    def __init__(self):
        self.data = bytearray()

    def raw(self, data):
        self.data.extend(b'\0' * (-len(self.data) % 4))
        p = 4096 + len(self.data)
        self.data.extend(data)
        return p

    def string(self, text):
        data = text.encode()
        return self.raw(data), len(data)

    def node(self, tag, *fields):
        return self.raw(struct.pack('<8I', tag, *fields, *([0] * (7 - len(fields)))))

    def pure(self, value=0):
        return self.node(0, value)

    def bind(self, action, continuation):
        return self.node(1, action, continuation)

    def sequence(self, *actions):
        if not actions:
            return self.pure()
        root = actions[-1]
        for action in reversed(actions[:-1]):
            root = self.bind(action, root)
        return root

    def say(self, text):
        return self.node(2, 1, *self.string(text))

    def die(self, code, message):
        return self.node(3, code, *self.string(message))

    def open(self, path, mode):
        return self.node(2, 2, *self.string(path), *self.string(mode))

    def read(self, maximum):
        return self.node(2, 3, maximum)

    def write(self, values):
        values = list(values)
        data = struct.pack(f'<{len(values)}I', *values)
        return self.node(2, 4, self.raw(data), len(values))

    def close(self):
        return self.node(2, 5)

    def report(self, mode, prefix=''):
        return self.node(5, mode, *self.string(prefix))

    def require(self, code=5, stage=''):
        prefix = f'HostFailure\t{stage}\t' if stage else ''
        return self.node(6, code, *(self.string(prefix) if prefix else (0, 0)))

    def branch(self, failed, done):
        return self.node(8, failed, done)

    def wat(self, root, steps=2000000):
        heap = (4096 + len(self.data) + 3) & ~3
        return (TEMPLATE.read_text().replace('@@PAGES@@', str((heap + 65535) // 65536))
                .replace('@@HEAP@@', str(heap)).replace('@@ROOT@@', str(root))
                .replace('@@STEPS@@', str(steps))
                .replace('@@DATA@@', ''.join(f'\\{b:02x}' for b in self.data)))


def fixture(name, argv):
    p = Program()
    if name == 'args-echo':
        root = p.sequence(p.node(2, 0), p.node(7))
    elif name == 'print-lines':
        root = p.sequence(*(p.say(s) for s in [
            'plain', '', 'two\nlines', 'tab\there\rreturn', 'nul\0inside',
            'é😀\U0010ffff', '\\ and "quotes"', 'end']))
    elif name == 'print-large':
        root = p.say('0123456789' * 10000)
    elif name == 'print-many':
        root = p.sequence(*(p.say(str(i)) for i in range(5000)), p.say('printed 5000'))
    elif name == 'die-codes':
        root = p.sequence(p.say('before'), p.die(int(argv[0]), 'stop'), p.say('never'))
    elif name == 'die-messages':
        root = p.die(3, argv[0] if argv else 'HostFailure\tread\t21\tIs a directory')
    elif name == 'die-stops-effects':
        root = p.sequence(p.say('one'), p.die(4, 'halt'), p.say('never'))
    elif name == 'die-after-write':
        work = p.sequence(p.open(argv[1], 'w'), p.require(), p.write(b'KNOT'), p.die(3, 'after write'))
        root = p.sequence(p.die(3, 'before open'), work) if argv[0] == 'before' else work
    elif name == 'open-nul-path':
        root = p.sequence(*(p.sequence(p.say('mode ' + mode), p.open('a\0b', mode),
                                      p.branch(p.report(3), p.close())) for mode in 'rwq'))
    elif name == 'open-modes':
        root = p.sequence(p.open(*argv), p.branch(p.report(3, 'open '), p.sequence(
            p.write(b'AB\n'), p.report(3, 'write '), p.read(64), p.close(), p.report(6, 'read '))))
    elif name == 'read-text':
        root = (p.sequence(p.open(argv[0], 'r'), p.require(stage='open'),
                           p.read(65537), p.close(), p.require(stage='read'), p.report(0, 'Read\t'))
                if argv else p.die(5, 'HostFailure\targuments\texpected path'))
    elif name in ('read-limit', 'read-decode'):
        mode = 2 if name == 'read-limit' else 1
        suffix = ' ' if mode == 2 else ':'
        root = p.sequence(p.open(argv[0], 'r'), p.require(), p.read(int(argv[1])),
                          p.report(mode, 'first' + suffix), p.read(int(argv[1])),
                          p.report(mode, 'second' + suffix), p.close())
    elif name == 'write-bytes':
        root = (p.sequence(p.open(argv[0], 'w'), p.require(stage='output-open'),
                           p.write(i & 255 for i in range(int(argv[1]))), p.close(),
                           p.require(stage='write'), p.say('Built\t' + argv[1]))
                if argv[1].isdigit() else p.die(5, 'HostFailure\targuments\texpected-u32'))
    elif name == 'write-values':
        root = p.sequence(p.open(argv[0], 'w'), p.require(), p.write(map(int, argv[1:])),
                          p.close(), p.report(3, 'write '))
    elif name == 'write-read-back':
        root = p.sequence(p.open(argv[0], 'w'), p.require(), p.write('héllo 😀\n'.encode()), p.close(),
                          p.open(argv[0], 'r'), p.require(), p.read(64), p.close(), p.require(),
                          p.report(0, 'text '), p.report(1, 'codes'))
    elif name == 'handle-dropped':
        root = p.sequence(p.open(argv[0], 'w'), p.require(), p.write(b'drop\n'), p.say('dropped'))
    elif name == 'bind-deep':
        increment = p.node(4, 1)
        right = p.report(4, 'right ')
        for _ in range(100000):
            right = p.bind(increment, right)
        left = p.pure()
        for _ in range(100000):
            left = p.bind(left, increment)
        root = p.sequence(p.pure(), right, left, p.report(4, 'left '))
    elif name == 'main-value':
        root = p.sequence(p.say('value discarded'), p.pure(7))
    elif name == 'result-try':
        root = p.sequence(p.open(argv[0], 'r'), p.require(0), p.read(65537), p.close(),
                          p.require(0), p.report(0))
    else:
        raise AssertionError(f'No hand translation: {name}')
    return p.wat(root)
