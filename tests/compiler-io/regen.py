#!/usr/bin/env python3
"""Freeze or verify the IO fixture suite against the pinned seed.

    python3 tests/compiler-io/regen.py          # verify (default)
    python3 tests/compiler-io/regen.py --write  # regenerate expectations.json

Every accepted fixture runs as a whole program, once per planned run, in a
fresh sandbox under the ignored .local/compiler-io/runs/<fixture>/<run>/. The
sandbox holds only the run's seeded inputs. The record of a run is its argv,
empty stdin, stdout, stderr, exit status and every file left in the sandbox.

Verification re-runs the pinned seed, rebuilds expectations.json in memory
from PLAN and those observations, and fails on any byte difference: seed, Bun
or platform drift, an edited fixture or input, a fixture or input added or
removed, a changed plan entry, or a changed seed result. A run's `reviewed`
literals (exit status, stream text, file bytes) are written in PLAN by hand
from the host ABI in FIXTURES.md; the build fails if the seed disagrees with
any of them. --write builds the document twice and writes nothing unless both
builds agree.

Expectations come only from the seed and from the reviewed literals in PLAN.
Nothing here runs or reads Knot.
"""
import concurrent.futures
import difflib
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SUITE = HERE.relative_to(ROOT).as_posix()
FIXTURES = HERE / 'fixtures'
INPUTS = FIXTURES / 'inputs'
EXPECTATIONS = HERE / 'expectations.json'
RUNS = ROOT / '.local/compiler-io/runs'
SEED_DIR = '.toolchain/bend-2.0.29-574b6d3'
SEED_MAIN = SEED_DIR + '/bend2/main.ts'
SEED_FILES = ['bend2/main.ts', 'bend2/bend.ts', 'bend2/comp.ts', 'bend2/base.bend',
              *(f'bend2/effs/{e}.js' for e in ('args', 'print', 'write', 'print_err', 'get_env',
                                               'file_open', 'file_read', 'file_write',
                                               'file_close'))]
PLATFORM = {'system': 'Darwin', 'machine': 'arm64'}
UNSET = 'KNOT_IO_FIXTURE_UNSET'
TIMEOUT = 120
JOBS = 6
STREAM_LIMIT = 4096
FILE_LIMIT = 1024

AGREE = {'outcome': 'agree',
         'meaning': 'Knot checks the book and builds a module; run under the IO host adapter '
                    'with the same argv, empty stdin and a sandbox seeded with the same inputs, '
                    'every run reproduces the recorded exit status, stdout bytes, stderr bytes '
                    'and final sandbox files'}
INVALID = {'outcome': 'Invalid', 'exit': 2, 'artifact': False, 'phase_code': 'open',
           'meaning': 'the seed rejects this book; Knot rejects it as Invalid and emits nothing'}


def unsupported(phase, code, why):
    return {'outcome': 'Unsupported', 'exit': 3, 'artifact': False,
            'diagnostic_prefix': f'Unsupported\t{phase}\t{code}\t', 'justification': why}


HOST_EFFECT = unsupported(
    'compile', 'host-effect',
    'The IO host ABI of this increment is the compiler\'s own surface: IO.args, IO.print, '
    'File.open, File.read, File.write_bytes and File.close (census of src/*.bend), beside the '
    'pure Base IO.pure, IO.bind and IO.die. Coordinator decision D12 (docs/COMPILER-CAMPAIGN.md, '
    'following BEND-SUBSET-STAGES: build rejects a reachable missing capability before '
    'emission): check-cli checks the book successfully, and compile-cli rejects a reachable '
    'effect outside that surface with this prefix and emits no artifact.')
DO_BIND = unsupported(
    'parse', 'do-bind',
    'Knot\'s own do blocks hold statements only (census: no `<-` or `return` in src/*.bend); '
    'a `name : T <- action` binder is outside this increment, so D4 forbids an Invalid claim '
    'about it even where the seed rejects the book. Vetoable before implementation starts.')


# ---------------------------------------------------------------------------
# Reviewed literals. These restate the host ABI of FIXTURES.md in Python, from
# the input bytes and the argv alone; the seed must agree with every one.

LINE = b'0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.\n'
OLD = b'old content\n'
SMALL = b'hello\nworld\n'


def pattern(n):
    return (LINE * (n // len(LINE) + 1))[:n]


def ramp(n):
    return bytes(i & 255 for i in range(n))


def text(data):
    # WHATWG UTF-8 decoding with U+FFFD for each maximal invalid subpart; the BOM is kept.
    return data.decode('utf-8', 'replace')


def codes(s):
    return ''.join(f' {ord(c)}' for c in s)


def arg_text(a):
    return a if isinstance(a, str) else text(a)


def echo(argv):
    return ''.join(f'[{arg_text(a)}]{codes(arg_text(a))}\n' for a in argv) + f'argc {len(argv)}\n'


def chunks(data, limit):
    return data[:limit], data[limit:2 * limit]


def limit_report(data, limit):
    def summary(chunk):
        s = text(chunk)
        return f'chars {len(s)} last {ord(s[-1]) if s else 0}'
    first, second = chunks(data, limit)
    return f'first {summary(first)}\nsecond {summary(second)}\n'


def decode_report(data, limit):
    first, second = chunks(data, limit)
    return f'first:{codes(text(first))}\nsecond:{codes(text(second))}\n'


def failure(stage, code, message):
    return f'HostFailure\t{stage}\t{code}\t{message}\n'


ENOENT, EBADF, ENOTDIR, EISDIR, EINVAL, EILSEQ = (
    (2, 'No such file or directory'), (9, 'Bad file descriptor'), (20, 'Not a directory'),
    (21, 'Is a directory'), (22, 'Invalid argument'), (92, 'Illegal byte sequence'))


def fail(prefix, errno):
    return f'{prefix}Fail {errno[0]} {errno[1]}\n'


def run(name, *argv, inputs=None, merged=False, **reviewed):
    """One program run. `inputs` maps a sandbox path to a file under fixtures/inputs.
    `reviewed` may fix exit, stdout, stderr, output (merged streams) and files
    (sandbox path -> exact bytes, or None for a path that must be absent)."""
    return {'name': name, 'argv': list(argv), 'inputs': dict(inputs or {}), 'merged': merged,
            'reviewed': reviewed}


def ok(stdout, **more):
    return {'exit': 0, 'stdout': stdout, 'stderr': '', **more}


def die(status, stderr, stdout='', **more):
    return {'exit': status, 'stdout': stdout, 'stderr': stderr, **more}


SEED_SMALL = {'small.txt': 'small.txt'}
SEED_OLD = {'old.txt': 'old.txt'}
DIE_CODES = [0, 1, 2, 3, 4, 5, 255, 256, 4294967295]
ARGS_MANY = [chr(c) for c in range(ord('a'), ord('q'))]
ARGS_UNICODE = ['\u00e9', '\u65e5\u672c', '\U0001F600', 'e\u0301', '\U0010FFFF']
ARGS_BLANK = ['', ' ', 'a b', 'tab\tx', 'nl\nx', 'cr\rx']
ARGS_DASHES = ['-x', '--', '--check-only', '-o', '--help']
ARGS_BYTES = [b'\xff', b'a\xc3', b'\xed\xa0\x80', b'\xc0\xaf']
LIMIT = 65537
UNICODE = 'caf\u00e9 \U0001F600 \u65e5\u672c\n'.encode()
BACK = 'h\u00e9llo \U0001F600\n'.encode()
AB = b'AB\n'


def read_text_run(name, path, inputs, **reviewed):
    return run(name, path, inputs=inputs, **reviewed)


def limit_run(name, source, limit, data):
    return run(name, source, str(limit), inputs={source: source},
               **ok(limit_report(data, limit)))


def decode_run(name, source, limit, data):
    return run(name, source, str(limit), inputs={source: source},
               **ok(decode_report(data, limit)))


PLAN = {
    # print ------------------------------------------------------------------
    'print-lines': dict(
        feature='print', kind='positive',
        covers='each IO.print appends one LF; empty, LF, CR, TAB, NUL, U+10FFFF and escapes pass '
               'through as UTF-8',
        knot=AGREE, runs=[run('one', **ok(
            'plain\n\ntwo\nlines\ntab\there\rreturn\nnul\x00inside\n'
            '\u00e9\U0001F600\U0010FFFF\n\\ and "quotes"\nend\n'))]),
    'print-large': dict(
        feature='print', kind='edge', covers='one print of a 100,000-character String',
        knot=AGREE, runs=[run('one', **ok('0123456789' * 10000 + '\n'))]),
    'print-many': dict(
        feature='print', kind='edge', covers='5,000 prints, in order, through a recursive IO loop',
        knot=AGREE, runs=[run('one', **ok(''.join(f'{i}\n' for i in range(5000))
                                          + 'printed 5000\n'))]),
    # args -------------------------------------------------------------------
    'args-echo': dict(
        feature='args', kind='positive',
        covers='IO.args: none, many, non-ASCII, empty and blank, dash-led, and invalid UTF-8 '
               'bytes (decoded to U+FFFD); the program name is excluded',
        knot=AGREE, runs=[
            run('none', **ok(echo([]))),
            run('many', *ARGS_MANY, **ok(echo(ARGS_MANY))),
            run('unicode', *ARGS_UNICODE, **ok(echo(ARGS_UNICODE))),
            run('blank', *ARGS_BLANK, **ok(echo(ARGS_BLANK))),
            run('dashes', *ARGS_DASHES, **ok(echo(ARGS_DASHES))),
            run('invalid-utf8', *ARGS_BYTES, **ok(echo(ARGS_BYTES))),
        ]),
    # die --------------------------------------------------------------------
    'die-codes': dict(
        feature='die', kind='edge',
        covers='IO.die(code): stdout written earlier stays; the exit status is code mod 256',
        knot=AGREE, runs=[run(f'code-{c}', str(c), **die(c % 256, 'stop\n', 'before\n'))
                          for c in DIE_CODES]),
    'die-messages': dict(
        feature='die', kind='positive',
        covers='the die message reaches stderr as UTF-8 plus one LF: tab-separated, empty, '
               'multi-line, non-ASCII and 4,096 characters',
        knot=AGREE, runs=[
            run('host-failure', **die(3, failure('read', *EISDIR))),
            run('empty', '', **die(3, '\n')),
            run('lines', 'multi\nline', **die(3, 'multi\nline\n')),
            run('unicode', '\u00e9\U0001F600', **die(3, '\u00e9\U0001F600\n')),
            run('long', 'm' * 4096, **die(3, 'm' * 4096 + '\n')),
        ]),
    'die-stops-effects': dict(
        feature='die', kind='edge',
        covers='a die inside a bind skips its continuation and every later effect; the merged '
               'stream shows stdout before the die message',
        knot=AGREE, runs=[
            run('split', **die(4, 'halt\n', 'one\n')),
            run('merged', merged=True, exit=4, output='one\nhalt\n'),
        ]),
    'die-after-write': dict(
        feature='die', kind='edge',
        covers='bytes written before a die stay on disk though the handle is never closed; a '
               'die before File.open leaves no file',
        knot=AGREE, runs=[
            run('after', 'after', 'out.bin', **die(3, 'after write\n', files={'out.bin': b'KNOT'})),
            run('before', 'before', 'out.bin', **die(3, 'before open\n', files={'out.bin': None})),
        ]),
    # read -------------------------------------------------------------------
    'read-text': dict(
        feature='read', kind='positive',
        covers="the driver's read path (open r, read 65537, close) and its HostFailure report "
               'for each failing stage',
        knot=AGREE, runs=[
            read_text_run('small', 'small.txt', SEED_SMALL, **ok('Read\thello\nworld\n\n')),
            read_text_run('empty', 'empty.txt', {'empty.txt': 'empty.txt'}, **ok('Read\t\n')),
            read_text_run('unicode', 'unicode.txt', {'unicode.txt': 'unicode.txt'},
                          **ok('Read\t' + text(UNICODE) + '\n')),
            read_text_run('unicode-path', '\u00e9.txt', {'\u00e9.txt': 'small.txt'},
                          **ok('Read\thello\nworld\n\n')),
            read_text_run('at-limit', 'limit-65537.txt', {'limit-65537.txt': 'limit-65537.txt'},
                          **ok('Read\t' + text(pattern(LIMIT)) + '\n')),
            read_text_run('over-limit', 'limit-65538.txt', {'limit-65538.txt': 'limit-65538.txt'},
                          **ok('Read\t' + text(pattern(LIMIT)) + '\n')),
            read_text_run('missing', 'missing.txt', {}, **die(5, failure('open', *ENOENT))),
            read_text_run('directory', '.', {}, **die(5, failure('read', *EISDIR))),
            read_text_run('not-directory', 'small.txt/x', SEED_SMALL,
                          **die(5, failure('open', *ENOTDIR))),
            read_text_run('empty-path', '', {}, **die(5, failure('open', *ENOENT))),
            run('usage', **die(5, 'HostFailure\targuments\texpected path\n')),
        ]),
    'read-limit': dict(
        feature='read', kind='edge',
        covers='File.read(max) returns at most max bytes, the rest on the next read: 65,536, '
               '65,537 and 65,538 bytes against the driver limit 65537, a character straddling '
               'the limit, max 0 and max 4294967295',
        knot=AGREE, runs=[
            limit_run('empty', 'empty.txt', LIMIT, b''),
            limit_run('below', 'limit-65536.txt', LIMIT, pattern(65536)),
            limit_run('at', 'limit-65537.txt', LIMIT, pattern(65537)),
            limit_run('over', 'limit-65538.txt', LIMIT, pattern(65538)),
            limit_run('straddle', 'limit-straddle.txt', LIMIT, pattern(65536) + '\u00e9'.encode()),
            limit_run('zero', 'small.txt', 0, SMALL),
            limit_run('max-u32', 'small.txt', 4294967295, SMALL),
        ]),
    'read-decode': dict(
        feature='read', kind='edge',
        covers='each read decodes its own bytes as UTF-8: split characters, invalid bytes, a '
               'kept BOM, NUL, and a directory read failing with 21 on every attempt',
        knot=AGREE, runs=[
            decode_run('split-char', 'split-char.txt', 4, b'abc\xc3\xa9x'),
            decode_run('split-emoji', 'split-emoji.txt', 2, b'\xf0\x9f\x98\x80z'),
            decode_run('bad-utf8', 'bad-utf8.txt', 8, b'\xff\xc3(\xe2\x82\xed\xa0\x80z'),
            decode_run('bom', 'bom.txt', 16, b'\xef\xbb\xbfhi\n'),
            decode_run('nul-byte', 'nul-byte.txt', 16, b'a\x00b\n'),
            decode_run('unicode', 'unicode.txt', 64, UNICODE),
            run('directory', '.', '4', **ok(fail('first: ', EISDIR) + fail('second: ', EISDIR))),
        ]),
    'open-nul-path': dict(
        feature='open', kind='edge',
        covers='a path holding NUL fails with 92 (darwin EILSEQ) before its mode is examined',
        knot=AGREE, runs=[run('one', **ok(''.join(f'mode {m}\n' + fail('', EILSEQ)
                                                   for m in 'rwq')))]),
    'open-modes': dict(
        feature='open', kind='edge',
        covers='modes r, w (create, truncate) and a (create, append); any other mode is 22; the '
               'wrong direction on a handle is 9; directories answer 21',
        knot=AGREE, runs=[
            run('w-new', 'out.txt', 'w', **ok('write Done\n' + fail('read ', EBADF),
                                             files={'out.txt': AB})),
            run('w-truncate', 'old.txt', 'w', inputs=SEED_OLD,
                **ok('write Done\n' + fail('read ', EBADF), files={'old.txt': AB})),
            run('a-append', 'old.txt', 'a', inputs=SEED_OLD,
                **ok('write Done\n' + fail('read ', EBADF), files={'old.txt': OLD + AB})),
            run('a-new', 'out.txt', 'a', **ok('write Done\n' + fail('read ', EBADF),
                                             files={'out.txt': AB})),
            run('r-existing', 'old.txt', 'r', inputs=SEED_OLD,
                **ok(fail('write ', EBADF) + 'read Done old content\n\n', files={'old.txt': OLD})),
            run('r-missing', 'out.txt', 'r', **ok(fail('open ', ENOENT), files={'out.txt': None})),
            *(run(f'mode-{label}', 'old.txt', mode, inputs=SEED_OLD,
                  **ok(fail('open ', EINVAL), files={'old.txt': OLD}))
              for label, mode in (('rw', 'rw'), ('empty', ''), ('upper', 'W'), ('plus', 'r+'))),
            run('w-directory', '.', 'w', **ok(fail('open ', EISDIR))),
            run('a-directory', '.', 'a', **ok(fail('open ', EISDIR))),
            run('r-directory', '.', 'r', **ok(fail('write ', EBADF) + fail('read ', EISDIR))),
        ]),
    # write ------------------------------------------------------------------
    'write-bytes': dict(
        feature='write', kind='positive',
        covers="compile-cli's write path: empty, all 256 byte values, 1,048,576 bytes (the "
               'output budget), truncation, and HostFailure for each failing stage',
        knot=AGREE, runs=[
            run('empty', 'empty.bin', '0', **ok('Built\t0\n', files={'empty.bin': b''})),
            run('all-bytes', 'all.bin', '256', **ok('Built\t256\n', files={'all.bin': ramp(256)})),
            run('large', 'large.bin', '1048576',
                **ok('Built\t1048576\n', files={'large.bin': ramp(1048576)})),
            run('truncate', 'old.txt', '3', inputs=SEED_OLD,
                **ok('Built\t3\n', files={'old.txt': ramp(3)})),
            run('missing-dir', 'nodir/out.bin', '1', **die(5, failure('output-open', *ENOENT))),
            run('directory', '.', '1', **die(5, failure('output-open', *EISDIR))),
            run('bad-count', 'x.bin', 'many',
                **die(5, 'HostFailure\targuments\texpected-u32\n', files={'x.bin': None})),
        ]),
    'write-values': dict(
        feature='write', kind='edge',
        covers='a byte list holding any value above 255 fails with 22 and writes nothing, though '
               'the w open has already truncated',
        knot=AGREE, runs=[
            run('none', 'out.bin', **ok('write Done\n', files={'out.bin': b''})),
            run('edges', 'out.bin', '0', '255', **ok('write Done\n', files={'out.bin': b'\x00\xff'})),
            run('over', 'out.bin', '1', '2', '256',
                **ok(fail('write ', EINVAL), files={'out.bin': b''})),
            run('max', 'out.bin', '4294967295', **ok(fail('write ', EINVAL), files={'out.bin': b''})),
            run('truncate-then-refuse', 'old.txt', '300', inputs=SEED_OLD,
                **ok(fail('write ', EINVAL), files={'old.txt': b''})),
        ]),
    'write-read-back': dict(
        feature='write', kind='positive',
        covers='written UTF-8 bytes read back through a second handle decode to the same Chars',
        knot=AGREE, runs=[run('one', 'back.txt', **ok(
            'text ' + text(BACK) + '\ncodes' + codes(text(BACK)) + '\n', files={'back.txt': BACK}))]),
    'handle-dropped': dict(
        feature='write', kind='edge', covers='a handle dropped without File.close keeps its bytes',
        knot=AGREE, runs=[run('one', 'drop.txt', **ok('dropped\n', files={'drop.txt': b'drop\n'}))]),
    'mini-driver': dict(
        feature='driver', kind='positive',
        covers='read, then write one byte per Char: ASCII, Latin-1, the same path in and out, and '
               'HostFailure open/read/output-open/write with nothing else written',
        knot=AGREE, runs=[
            run('ascii', 'small.txt', 'out.bin', inputs=SEED_SMALL,
                **ok('Built\t12\n', files={'out.bin': SMALL})),
            run('latin1', 'latin1.txt', 'out.bin', inputs={'latin1.txt': 'latin1.txt'},
                **ok('Built\t5\n', files={'out.bin': b'caf\xe9\n'})),
            run('same-path', 'small.txt', 'small.txt', inputs=SEED_SMALL,
                **ok('Built\t12\n', files={'small.txt': SMALL})),
            run('missing', 'missing.txt', 'out.bin',
                **die(5, failure('open', *ENOENT), files={'out.bin': None})),
            run('directory', '.', 'out.bin',
                **die(5, failure('read', *EISDIR), files={'out.bin': None})),
            run('output-missing-dir', 'small.txt', 'nodir/out.bin', inputs=SEED_SMALL,
                **die(5, failure('output-open', *ENOENT))),
            run('output-directory', 'small.txt', '.', inputs=SEED_SMALL,
                **die(5, failure('output-open', *EISDIR))),
            run('wide', 'wide.txt', 'out.bin', inputs={'wide.txt': 'wide.txt'},
                **die(5, failure('write', *EINVAL), files={'out.bin': b''})),
            run('usage', 'small.txt', inputs=SEED_SMALL,
                **die(5, 'HostFailure\targuments\texpected source output\n')),
        ]),
    # sequencing --------------------------------------------------------------
    'bind-order': dict(
        feature='sequencing', kind='positive',
        covers='left- and right-nested IO.bind with bare-name, partial and capturing '
               'continuations run in written order',
        knot=AGREE, runs=[run('one', **ok('a\nab\nab!\nc\ncd\ncd!\ne\nef!\nend\n'))]),
    'bind-lazy': dict(
        feature='sequencing', kind='edge',
        covers='an IO value runs where it is bound: never when dropped, after earlier effects '
               'when passed along, and only on the chosen branch',
        knot=AGREE, runs=[run('one', **ok('before the action\nthe action\nchosen\nchosen too\n'))]),
    'bind-deep': dict(
        feature='sequencing', kind='edge',
        covers='100,000 right-nested and 100,000 left-nested binds complete',
        knot=AGREE, runs=[run('one', **ok('right 100000\nleft 100000\n'))]),
    'main-value': dict(
        feature='sequencing', kind='edge', covers='main : IO(U32); the final value is discarded',
        knot=AGREE, runs=[run('one', **ok('value discarded\n'))]),
    # results ----------------------------------------------------------------
    'result-try': dict(
        feature='result', kind='positive',
        covers='IO.try and IO.pass turn a host Fail{(code, message)} into exit code and message',
        knot=AGREE, runs=[
            run('small', 'small.txt', inputs=SEED_SMALL, **ok('hello\nworld\n\n')),
            run('missing', 'missing.txt', **die(ENOENT[0], ENOENT[1] + '\n')),
            run('directory', '.', **die(EISDIR[0], EISDIR[1] + '\n')),
            run('not-directory', 'small.txt/x', inputs=SEED_SMALL,
                **die(ENOTDIR[0], ENOTDIR[1] + '\n')),
        ]),
    'result-bind': dict(
        feature='result', kind='positive',
        covers='a Result chain stops at its first failing step, whose code and message reach '
               'IO.die',
        knot=AGREE, runs=[
            run('ok', '3', '10', **ok('difference 7\n')),
            run('first-bad', 'x', '10', **die(3, 'not a number: x\n')),
            run('second-bad', '3', 'y', **die(3, 'not a number: y\n')),
            run('both-bad', 'x', 'y', **die(3, 'not a number: x\n')),
            run('zero', '10', '10', **die(4, 'zero difference\n')),
            run('wrap', '10', '3', **ok('difference 4294967289\n')),
        ]),
    # outside the increment ----------------------------------------------------
    'effect-write': dict(
        feature='boundary', kind='knot', covers='IO.write, a Base effect outside the ABI',
        knot=HOST_EFFECT, runs=[run('one', **ok('no newline;then a line\n'))]),
    'effect-print-err': dict(
        feature='boundary', kind='knot', covers='IO.print_err, a Base effect outside the ABI',
        knot=HOST_EFFECT, runs=[run('one', **ok('to stdout\n', stderr='to stderr\n'))]),
    'effect-get-env': dict(
        feature='boundary', kind='knot',
        covers=f'IO.get_env, a Base effect outside the ABI; {UNSET} is removed from the '
               'environment',
        knot=HOST_EFFECT, runs=[run('one', **ok(fail('', ENOENT)))]),
    'effect-file-write': dict(
        feature='boundary', kind='knot', covers='File.write (String data), outside the ABI',
        knot=HOST_EFFECT, runs=[run('one', **ok('written\n', files={'out.txt': b'text\n'}))]),
    'do-bind-arrow': dict(
        feature='boundary', kind='knot', covers='a `name : T <- action` binder in a do block',
        knot=DO_BIND, runs=[run('none', **ok('argc 0\n')), run('two', 'a', 'b', **ok('argc 2\n'))]),
    'do-bind-type-mismatch': dict(
        feature='boundary', kind='negative', covers='a `<-` binder annotated U32 over IO(Unit)',
        knot=DO_BIND, twin='do-bind-arrow',
        reason=['@_:U32 -> IO.OP<R>', '@_:Unit -> IO.OP<R>']),
    # negatives --------------------------------------------------------------
    'reuse-io': dict(
        feature='sequencing', kind='negative', covers='one IO value bound twice',
        knot=INVALID, twin='bind-lazy', reason=['action (consumed more than once)']),
    'reuse-file': dict(
        feature='read', kind='negative', covers='a handle used again after File.read returned it',
        knot=INVALID, twin='read-text', reason=['file (consumed more than once)']),
    'forge-file': dict(
        feature='read', kind='negative', covers='a U32 literal where a File is expected',
        knot=INVALID, twin='read-text', reason=['- expected : File', '- observed : U32']),
    'print-non-string': dict(
        feature='print', kind='negative', covers='IO.print of a U32',
        knot=INVALID, twin='print-lines', reason=['- expected : String', '- observed : U32']),
    'die-nat-code': dict(
        feature='die', kind='negative', covers='a Nat exit code',
        knot=INVALID, twin='die-codes', reason=['- expected : U32', '- observed : Nat']),
    'bind-non-io-continuation': dict(
        feature='sequencing', kind='negative', covers='a bind continuation answering Unit',
        knot=INVALID, twin='bind-order', reason=['- observed : Unit']),
    'result-missing-fail': dict(
        feature='result', kind='negative', covers='a File.open result matched without Fail',
        knot=INVALID, twin='read-text', reason=['cases for Fail']),
    'read-result-without-handle': dict(
        feature='read', kind='negative', covers='File.read bound as a bare Result',
        knot=INVALID, twin='read-text',
        reason=['- observed : @-R:Type -> @k:(@_:Sigma<&1, &1, File, _ =>']),
    'write-bytes-string': dict(
        feature='write', kind='negative', covers='File.write_bytes given a String',
        knot=INVALID, twin='write-bytes', reason=['- expected : List<&2, U32>', '- observed : String']),
    'write-bytes-affine-list': dict(
        feature='write', kind='negative', covers='File.write_bytes given an affine List<&1, U32>',
        knot=INVALID, twin='write-values',
        reason=['- expected : List<&2, U32>', '- observed : List<&1, U32>']),
}


# ---------------------------------------------------------------------------
# Seed runs.

def sha256(data):
    return hashlib.sha256(data).hexdigest()


def blob(data, limit):
    record = {'size': len(data), 'sha256': sha256(data)}
    if len(data) <= limit:
        try:
            record['text'] = data.decode('utf-8')
        except UnicodeDecodeError:
            record['hex'] = data.hex()
    return record


def environment():
    env = {k: v for k, v in os.environ.items() if not k.startswith('BEND_') and k != UNSET}
    env['BEND_NO_TELEMETRY'] = '1'
    return env


def leaks(data, command):
    for spelling in {str(ROOT), os.path.realpath(ROOT), '/Users/', '/private/', '/tmp/'}:
        if spelling.encode() in data:
            sys.exit(f'seed output leaks a local path ({spelling}): {command}')


def execute(command, cwd, merged=False):
    """Run the seed; timeouts and lane memory faults are never frozen."""
    try:
        r = subprocess.run(command, cwd=cwd, env=environment(), stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT if merged else subprocess.PIPE,
                           timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        sys.exit(f'seed timed out after {TIMEOUT}s: {command}')
    if b'bend: memory fault' in r.stdout + (r.stderr or b''):
        sys.exit(f'Exhausted\tseed\tmemory-fault: {command}')
    leaks(r.stdout + (r.stderr or b''), command)
    return r


def shown_arg(a):
    return a if isinstance(a, str) else {'hex': a.hex()}


def check_only(name):
    command = ['bun', SEED_MAIN, f'{SUITE}/fixtures/{name}.bend', '--check-only']
    r = execute(command, ROOT)
    return {'command': command, 'exit': r.returncode, 'stdout': r.stdout.decode(),
            'stderr': r.stderr.decode()}


def sandbox(name, run_name):
    box = RUNS / name / run_name
    assert box.resolve().is_relative_to(RUNS.resolve()) and box != RUNS, box
    if box.exists():
        shutil.rmtree(box)
    box.mkdir(parents=True)
    return box


def snapshot(box, seeded):
    files = []
    for path in sorted(box.rglob('*')):
        rel = path.relative_to(box).as_posix()
        if path.is_dir():
            files.append({'path': rel, 'type': 'directory'})
            continue
        data = path.read_bytes()
        entry = {'path': rel, 'type': 'file', **blob(data, FILE_LIMIT)}
        if rel in seeded:
            entry['seeded_from'] = seeded[rel]
            entry['changed'] = data != (INPUTS / seeded[rel]).read_bytes()
        files.append(entry)
    return files


def program(name, spec):
    box = sandbox(name, spec['name'])
    for dest, source in spec['inputs'].items():
        shutil.copyfile(INPUTS / source, box / dest)
    up = os.path.relpath(ROOT, box)
    command = ['bun', f'{up}/{SEED_MAIN}', f'{up}/{SUITE}/fixtures/{name}.bend', '--',
               *spec['argv']]
    r = execute(command, box, spec['merged'])
    record = {'exit': r.returncode}
    if spec['merged']:
        record['output'] = blob(r.stdout, STREAM_LIMIT)
    else:
        record['stdout'] = blob(r.stdout, STREAM_LIMIT)
        record['stderr'] = blob(r.stderr, STREAM_LIMIT)
    record['files'] = snapshot(box, spec['inputs'])
    raw = {'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr,
           'files': {f['path']: (box / f['path']).read_bytes()
                     for f in record['files'] if f['type'] == 'file'}}
    shown = [c if isinstance(c, str) else {'hex': c.hex()} for c in command]
    return {'cwd': box.relative_to(ROOT).as_posix(), 'command': shown}, record, raw


def review(name, spec, raw):
    """Compare the seed with the run's reviewed literals; name the fields they fixed."""
    want, fields, problems = spec['reviewed'], [], []
    if 'exit' in want:
        fields.append('exit')
        if raw['exit'] != want['exit']:
            problems.append(f'exit {raw["exit"]}, reviewed {want["exit"]}')
    for key, stream in (('stdout', 'stdout'), ('stderr', 'stderr'), ('output', 'stdout')):
        if key in want:
            fields.append(key)
            if raw[stream] != want[key].encode():
                problems.append(f'{key} differs from its reviewed literal')
    for path, data in want.get('files', {}).items():
        fields.append(f'{"absent" if data is None else "file"}:{path}')
        if raw['files'].get(path) != data:
            problems.append(f'file {path} differs from its reviewed literal')
    if problems:
        sys.exit(f'{name}/{spec["name"]}: the seed disagrees with the review: {problems}')
    return fields


# ---------------------------------------------------------------------------
# Static checks on fixtures and inputs.

def base_names():
    text_ = (ROOT / SEED_DIR / 'bend2/base.bend').read_text()
    names = set(re.findall(r'^(?:def|law) ([\w.]+)', text_, re.M))
    names |= set(re.findall(r'^type ([\w.]+)', text_, re.M))
    names |= set(re.findall(r'^  ([A-Z]\w*)\{', text_, re.M))
    return {n.split('.')[0] for n in names}


def hygiene(name, source, base):
    data = source.encode()
    assert data.isascii(), f'{name}: fixtures are ASCII; write non-ASCII text with \\u{{..}}'
    assert b'\t' not in data and b'\r' not in data, f'{name}: no raw tab or CR'
    assert source.endswith('\n') and not source.endswith('\n\n'), f'{name}: one final LF'
    local = set(re.findall(r'^(?:def|type) (\w+)', source, re.M))
    local |= set(re.findall(r'^  ([A-Z]\w*)\{', source, re.M))
    assert not local & base, f'{name} reuses a Base name: {sorted(local & base)}'


def plan_shape(name, entry):
    kind, knot = entry['kind'], entry['knot']
    assert kind in ('positive', 'edge', 'negative', 'knot'), name
    if kind == 'negative':
        assert not entry.get('runs') and entry.get('reason') and entry.get('twin'), name
        assert entry['twin'] in PLAN and PLAN[entry['twin']]['kind'] != 'negative', name
        assert knot is INVALID or knot['outcome'] == 'Unsupported', name
    else:
        assert entry['runs'] and 'twin' not in entry and 'reason' not in entry, name
        assert (knot is AGREE) == (kind in ('positive', 'edge')), name
        assert len({r['name'] for r in entry['runs']}) == len(entry['runs']), name
        for r in entry['runs']:
            assert {'exit'} <= set(r['reviewed']), f'{name}/{r["name"]}: review the exit status'


def fixture(name, base, pool):
    entry = PLAN[name]
    plan_shape(name, entry)
    path = FIXTURES / f'{name}.bend'
    source = path.read_text()
    hygiene(name, source, base)
    record = {'name': name, 'file': path.relative_to(ROOT).as_posix(),
              'sha256': sha256(path.read_bytes()), 'feature': entry['feature'],
              'kind': entry['kind'], 'covers': entry['covers']}
    if 'twin' in entry:
        record['twin'] = entry['twin']
        record['seed_reason'] = entry['reason']
    record['seed_check'] = pool.submit(check_only, name)
    if entry['kind'] == 'negative':
        record['seed_run'] = pool.submit(program, name, run('seed-run'))
    else:
        record['runs'] = [(spec, pool.submit(program, name, spec)) for spec in entry['runs']]
    record['knot' if entry['knot'] in (AGREE, INVALID) else 'knot_expected'] = entry['knot']
    return record


def settle(record):
    """Wait for the fixture's seed runs and check them against its plan."""
    name, knot = record['name'], record.get('knot') or record['knot_expected']
    check = record['seed_check'] = record['seed_check'].result()
    if record['kind'] == 'negative':
        assert check['exit'] == 1 and check['stdout'] == '', (name, check)
        missing = [s for s in record['seed_reason'] if s not in check['stderr']]
        assert not missing, f'{name}: the seed rejects it for another reason; missing {missing}'
        where, seen, raw = record['seed_run'].result()
        assert seen['exit'] == 1 and raw['stderr'] == check['stderr'].encode(), (name, seen)
        record['seed_run'] = {**where, 'argv': [], 'stdin': '', 'seed': seen}
        return record
    assert check == {**check, 'exit': 0, 'stdout': 'All terms check.\n', 'stderr': ''}, check
    assert knot is AGREE or knot['outcome'] == 'Unsupported', name
    runs = []
    for spec, future in record['runs']:
        where, seen, raw = future.result()
        runs.append({'name': spec['name'], 'argv': [shown_arg(a) for a in spec['argv']],
                     'stdin': '', 'inputs': spec['inputs'], **where,
                     'streams': 'merged' if spec['merged'] else 'separate',
                     'reviewed': review(name, spec, raw), 'seed': seen})
    if knot is AGREE and len(runs) > 1:
        outcomes = {json.dumps(r['seed'], sort_keys=True) for r in runs}
        assert len(outcomes) > 1, f'{name}: every run observes the same result'
    record['runs'] = runs
    return record


def inputs(used):
    on_disk = sorted(p.name for p in INPUTS.iterdir() if p.is_file())
    assert on_disk == sorted(used), (f'inputs and PLAN differ: unused {sorted(set(on_disk) - used)}, '
                                     f'absent {sorted(used - set(on_disk))}')
    return {n: {'size': (INPUTS / n).stat().st_size, 'sha256': sha256((INPUTS / n).read_bytes())}
            for n in on_disk}


def build():
    host = {'system': platform.system(), 'machine': platform.machine()}
    if host != PLATFORM:
        sys.exit(f'errno values and messages are pinned to {PLATFORM}; this host is {host}')
    names = sorted(p.stem for p in FIXTURES.glob('*.bend'))
    if names != sorted(PLAN):
        sys.exit(f'fixtures and PLAN differ: only on disk {sorted(set(names) - set(PLAN))}, '
                 f'only in PLAN {sorted(set(PLAN) - set(names))}')
    used = {src for e in PLAN.values() for r in e.get('runs', []) for src in r['inputs'].values()}
    bun = subprocess.run(['bun', '--version'], capture_output=True, text=True, check=True)
    base = base_names()
    with concurrent.futures.ThreadPoolExecutor(max_workers=JOBS) as pool:
        records = [fixture(n, base, pool) for n in names]
        fixtures = [settle(r) for r in records]
    return {
        'suite': 'compiler-io',
        'increment': 'io: campaign milestone 10, the IO host ABI (docs/COMPILER-CAMPAIGN.md, D4, D7)',
        'generator': f'python3 {SUITE}/regen.py --write',
        'seed': {'version': '2.0.29', 'commit': '574b6d39a235b539eb19a5c532993a0abb3d11ad',
                 'launcher': ['bun', SEED_MAIN], 'bun': bun.stdout.strip(),
                 'sha256': {f: sha256((ROOT / SEED_DIR / f).read_bytes()) for f in SEED_FILES}},
        'platform': PLATFORM,
        'environment': {'check_cwd': 'repository root',
                        'run_cwd': '.local/compiler-io/runs/<fixture>/<run>, created empty and '
                                   'seeded with the run\'s inputs',
                        'set': {'BEND_NO_TELEMETRY': '1'},
                        'removed': ['BEND_*', UNSET], 'stdin': 'empty (/dev/null)',
                        'separator': 'the seed launcher takes `--` before argv; the program '
                                     'sees only argv'},
        'inputs': inputs(used),
        'fixtures': fixtures,
    }


def render(doc):
    return json.dumps(doc, indent=2, ensure_ascii=False) + '\n'


def summary(doc):
    runs = sum(len(f.get('runs', [])) for f in doc['fixtures'])
    return f'{len(doc["fixtures"])} fixtures, {runs} runs'


def main():
    text_ = render(build())
    if sys.argv[1:] == ['--write']:
        if render(build()) != text_:
            sys.exit('two seed passes disagree; nothing written')
        EXPECTATIONS.write_text(text_)
        print(f'wrote {EXPECTATIONS.relative_to(ROOT)}: {summary(json.loads(text_))}')
        return
    if sys.argv[1:]:
        sys.exit(__doc__)
    frozen = EXPECTATIONS.read_text() if EXPECTATIONS.exists() else ''
    if text_ != frozen:
        diff = difflib.unified_diff(frozen.splitlines(), text_.splitlines(),
                                    'expectations.json', 'seed now', lineterm='', n=2)
        print('\n'.join(list(diff)[:200]))
        sys.exit('seed observations differ from expectations.json')
    print(f'io fixtures match the seed: {summary(json.loads(text_))}')


if __name__ == '__main__':
    main()
