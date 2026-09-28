#!/usr/bin/env python3
"""Compare knot-io-2 with frozen literals and the modules foreign bodies."""
import errno
import hashlib
import itertools
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORK = ROOT / '.local/io-abi-2'
HOST = ROOT / 'scripts/run-wasm-io.mjs'
SEED = ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts'
PLAN = json.loads((HERE / 'expectations.json').read_text())
TEMPLATE = (HERE / 'probe.wat').read_text()
ENV = {**os.environ, 'BEND_NO_TELEMETRY': '1'}
# The seed sees no package, hub or origin settings, as in the frozen IO oracle.
SEED_ENV = {**{k: v for k, v in os.environ.items() if not k.startswith('BEND_')}, 'BEND_NO_TELEMETRY': '1'}
SCALE = float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))
BUN_STACK_CELLS = 32000
COMPLETED = {'status': 'Completed', 'exit': 0}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def command(argv, cwd=ROOT, env=ENV):
    return subprocess.run(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                          capture_output=True, timeout=120 * SCALE)


def fresh(name):
    directory = WORK / name
    assert directory.is_relative_to(WORK) and directory != WORK
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    return directory


def snapshot(box):
    rows = {}
    for p in sorted(box.rglob('*')):
        st = p.lstat()
        name = p.relative_to(box).as_posix()
        if stat.S_ISLNK(st.st_mode):
            rows[name] = ['link', os.readlink(p)]
        elif stat.S_ISREG(st.st_mode):
            rows[name] = ['file', st.st_size, sha(p.read_bytes()), st.st_nlink]
        elif stat.S_ISDIR(st.st_mode):
            rows[name] = ['directory']
        else:
            rows[name] = ['special', stat.S_IFMT(st.st_mode)]
    return rows


def identity_tree(name):
    box = fresh(name) / 'sandbox'
    box.mkdir()
    (box / 'file.bin').write_bytes(b'identity\x00\xff')
    (box / 'dir').mkdir()
    (box / 'dir/leaf').write_bytes(b'leaf')
    (box / 'dir/🪞').write_bytes(b'unicode')
    (box / 'link-file').symlink_to('file.bin')
    (box / 'link-dir').symlink_to('dir', target_is_directory=True)
    (box / 'dangling').symlink_to('missing')
    (box / 'outside').symlink_to('../unread-outside')
    os.link(box / 'file.bin', box / 'hardlink')
    os.mkfifo(box / 'fifo')
    return box


def case_mode(box):
    return 'insensitive' if (box / 'FILE.BIN').exists() else 'sensitive'


def identity_expected(case, mode):
    return case.get('expected', case.get('expected_by_case', {}).get(mode))


def data_segment(data, address=512):
    data = data.encode() if isinstance(data, str) else data
    escaped = ''.join(f'\\{b:02x}' for b in data)
    return f'(data (i32.const {address}) "{escaped}")'


def program(body='', data='', allocator=''):
    return TEMPLATE.replace(';; @BODY@', body).replace(';; @DATA@', data).replace(';; @ALLOC@', allocator)


def identity_program(target, out=64):
    if target.startswith('$SANDBOX'):
        # Absolute test paths enter as args so module bytes do not encode checkout paths.
        body = ('(call $args (i32.const 64)) '
                f'(call $path_identity (i32.load (i32.load (i32.const 72))) '
                f'(i32.load offset=4 (i32.load (i32.const 72))) (i32.const {out}))')
        return program(body + ' (call $dump)')
    return program(f'(call $path_identity (i32.const 512) (i32.const {len(target.encode())}) '
                   f'(i32.const {out})) (call $dump)', data_segment(target))


def opened(body, mode='r', allocator=''):
    return program('(call $open (i32.const 512) (i32.const 8) (i32.const 600) '
                   '(i32.const 1) (i32.const 64)) '
                   '(if (i32.load (i32.const 64)) (then (unreachable))) ' + body,
                   data_segment('data.bin') + data_segment(mode, 600), allocator)


def invoke(wat, box, host=HOST, args=()):
    directory = box.parent
    source, module = directory / 'probe.wat', directory / 'probe.wasm'
    source.write_text(wat)
    assembled = command(['wat2wasm', str(source), '-o', str(module)])
    assert assembled.returncode == 0, assembled.stderr.decode()
    arguments, receipt = directory / 'args.json', directory / 'outcome.json'
    arguments.write_text(json.dumps(args))
    receipt.unlink(missing_ok=True)
    before = snapshot(box)
    r = command(['node', str(ROOT / 'tests/compiler-io/host/invoke.mjs'), str(host),
                 str(module), str(box), str(arguments), str(receipt)], cwd=box)
    assert receipt.is_file(), (r.returncode, r.stderr)
    assert snapshot(box) == before, 'Guest changed fixture files or entries'
    outcome = json.loads(receipt.read_text())
    assert r.returncode == outcome['exit'], (r.returncode, outcome)
    return r, outcome, sha(module.read_bytes())


def observations(r, outcome):
    assert outcome == COMPLETED and r.stderr == b'', (outcome, r.stderr)
    records = []
    for line in r.stdout.decode('ascii').splitlines():
        code, value, data = line.split(' ')
        assert len(code) == len(value) == 8 and bytes.fromhex(data).hex() == data
        records.append([int(code, 16), int(value, 16), data])
    return records


def compact(records):
    return [[code, value, data if len(data) <= 1024 else
             {'bytes': len(data) // 2, 'sha256': sha(bytes.fromhex(data))}]
            for code, value, data in records]


def read_box(name, case):
    box = fresh(name) / 'sandbox'
    box.mkdir()
    fill = case.get('fill')
    data = bytes([fill['byte']]) * fill['count'] if fill else bytes.fromhex(case.get('hex', ''))
    if case.get('directory'):
        (box / 'data.bin').mkdir()
    else:
        (box / 'data.bin').write_bytes(data)
    return box


def read_expected(case):
    if 'expected_fill' in case:
        e = case['expected_fill']
        return [[e['errno'], e['value'], (bytes([e['byte']]) * e['count']).hex()]]
    return case['expected']


def read_case(case, host=HOST, prefix='bytes'):
    box = read_box(prefix + '/' + case['name'], case)
    body = ''.join(f'(call ${op} (i32.const 1) (i32.const {maximum}) (i32.const 64)) '
                   '(call $dump) ' for op, maximum in case['reads'])
    r, outcome, digest = invoke(opened(body + '(call $close (i32.const 1))',
                                      case.get('mode', 'r')), box, host)
    actual = observations(r, outcome)
    return actual, read_expected(case), {'name': case['name'], 'wasm_sha256': digest,
                                         'observations': compact(actual), 'outcome': outcome}


def seed_read(op, line):
    word, *words = line.split(' ')
    if word == 'Fail':
        return [int(words[0]), ' '.join(words[1:]).encode().hex()]
    assert word == 'Done', line
    values = [int(w) for w in words]
    data = bytes(values) if op == 'read_bytes' else ''.join(map(chr, values)).encode()
    return [0, data.hex()]


def seed():
    """The pinned seed's File.read_bytes/File.read witness errno and bytes; handles are opaque."""
    directory = fresh('seed')
    fixture = HERE / 'read-bytes.bend'
    checked = command(['bun', str(SEED), str(fixture), '--check-only'], env=SEED_ENV)
    assert checked.returncode == 0 and checked.stdout.strip() == b'All terms check.', checked
    native, js = directory / 'read-bytes', directory / 'read-bytes.js'
    built = command(['bun', str(SEED), str(fixture), '-o', str(native), '-o', str(js)], env=SEED_ENV)
    assert built.returncode == 0, built.stderr.decode()
    lanes = {'interpreter': ['bun', str(SEED), str(fixture), '--'],
             'native': [str(native)], 'js': ['bun', str(js)]}
    rows = []
    for case in PLAN['read_bytes']:
        ops = [word for op, maximum in case['reads']
               for word in ('bytes' if op == 'read_bytes' else 'text', str(maximum))]
        expected = [[code, data] for code, _, data in read_expected(case)]
        for lane, argv in lanes.items():
            box = read_box(f'seed/{lane}/{case["name"]}', case)
            before = snapshot(box)
            r = command([*argv, 'data.bin', case.get('mode', 'r'), *ops], box, SEED_ENV)
            assert snapshot(box) == before, (case['name'], lane)
            if lane != 'native' and r.stderr == b'bend: memory fault (machine stack overflow?)\n':
                # Exhausted-lane rule: only the documented Bun stack bound excuses a lane.
                assert case.get('fill', {}).get('count', 0) > BUN_STACK_CELLS, (case['name'], lane)
                rows.append({'name': case['name'], 'lane': lane, 'status': 'Exhausted',
                             'bound': f'Bun lane stack, lists over {BUN_STACK_CELLS} cells'})
                continue
            assert r.returncode == 0 and r.stderr == b'', (case['name'], lane, r.returncode, r.stderr)
            lines = r.stdout.decode().split('\n')
            assert lines[-1] == '' and len(lines) == len(case['reads']) + 1, (case['name'], lane)
            actual = [seed_read(op, line) for (op, _), line in zip(case['reads'], lines)]
            assert actual == expected, (case['name'], lane, compact([[c, 0, d] for c, d in actual]))
            rows.append({'name': case['name'], 'lane': lane, 'status': 'agree',
                         'observations': [[c, d] for c, _, d in compact([[c, 0, d] for c, d in actual])]})
    return rows


def identity_case(case, host=HOST, prefix='identity'):
    box = identity_tree(prefix + '/' + case['name'])
    target = case['path'].replace('$SANDBOX', str(box.resolve()))
    r, outcome, digest = invoke(identity_program(case['path']), box, host,
                                [target] if '$SANDBOX' in case['path'] else [])
    actual = observations(r, outcome)
    expected = [identity_expected(case, case_mode(box))]
    return actual, expected, {'name': case['name'], 'wasm_sha256': digest,
                              'observations': actual, 'outcome': outcome}


def references():
    directory = fresh('reference')
    for name, digest in PLAN['reference_sha256'].items():
        assert sha((HERE / 'reference' / name).read_bytes()) == digest, name
    source = (HERE / 'reference/path-identity.c').read_text()
    source = source.split('static void knot_path_identity_call')[0]
    source = ('#include <stdbool.h>\n#include <stdio.h>\n#include <stdlib.h>\n'
              '#include <string.h>\n#include <unistd.h>\n#include <errno.h>\n' + source +
              (HERE / 'reference-main.c').read_text())
    c_source, native = directory / 'reference.c', directory / 'reference'
    c_source.write_text(source)
    built = command(['clang', '-Wall', '-Wextra', '-Werror', str(c_source), '-o', str(native)])
    assert built.returncode == 0, built.stderr.decode()
    box = identity_tree('reference-tree')
    before, mode = snapshot(box), case_mode(box)
    rows = []
    for case in PLAN['path_identity']:
        for lane, actual in foreign(native, case['path'].replace('$SANDBOX', str(box.resolve())), box):
            assert actual == identity_expected(case, mode), (case['name'], lane, actual)
            rows.append({'name': case['name'], 'lane': lane, 'observed': actual})
    assert snapshot(box) == before
    return {'status': 'pass', 'reference_commit': PLAN['reference_commit'],
            'reference_sha256': PLAN['reference_sha256'], 'case_mode': mode,
            'expectations_sha256': sha((HERE / 'expectations.json').read_bytes()), 'runs': rows}, native


def foreign(native, target, box):
    """Both unmodified modules bodies, as [lane, [Darwin errno, value, message hex]]."""
    encoded, rows = target.encode().hex(), []
    for lane, argv in [('c', [str(native), encoded]),
                       ('js', ['node', str(HERE / 'reference.mjs'),
                               str(HERE / 'reference/path-identity.js'), encoded])]:
        r = command(argv, cwd=box)
        assert r.returncode == 0 and r.stderr == b'', (target, lane, r.stderr)
        code, value = json.loads(r.stdout)
        darwin = {errno.EILSEQ: 92, errno.ENAMETOOLONG: 63}.get(code, code)
        rows.append((lane, [darwin, value, os.strerror(code).encode().hex() if code else '']))
    return rows


# Generated spellings over the identity tree; the foreign bodies alone decide each result.
SPELLINGS = ['file.bin', 'FILE.BIN', 'dir', 'DIR', 'leaf', 'link-file', 'link-dir',
             'dangling', 'fifo', 'missing', '.', '..']


def inside(parts):
    depth = 0
    for part in parts:
        depth += {'.': 0, '..': -1}.get(part, 1)
        if depth < 0:
            return False
    return True


def parity(native):
    """Every one- and two-component spelling inside the root, and each rooted single."""
    box = identity_tree('parity')
    root = str(box.resolve())
    targets = ['/'.join(parts) for n in (1, 2) for parts in itertools.product(SPELLINGS, repeat=n)
               if inside(parts)]
    targets += [root + '/' + part for part in SPELLINGS if part != '..']
    before, rows = snapshot(box), []
    for target in targets:
        lanes = foreign(native, target, box)
        rooted = target.startswith('/')
        r, outcome, _ = invoke(identity_program('$SANDBOX' if rooted else target), box,
                               args=[target] if rooted else [])
        host = observations(r, outcome)
        assert all([observed] == host for _, observed in lanes), (target, lanes, host)
        rows.append([target.replace(root, '$SANDBOX'), host[0][1]])
    assert snapshot(box) == before
    return rows


def control(name, host=HOST, prefix='controls'):
    box = fresh(prefix + '/' + name) / 'sandbox'
    box.mkdir()
    (box / 'data.bin').write_bytes(b'\xff')
    body = '(call $read_bytes (i32.const 1) (i32.const 1) (i32.const 64))'
    args = []
    if name.endswith('wrong-signature'):
        imp = 'read_bytes' if name.startswith('bytes') else 'path_identity'
        wat = program().replace(f'(func ${imp} (param i32 i32 i32))', f'(func ${imp} (param i32 i32))')
    elif name in ('bytes-unaligned-result', 'bytes-bad-result', 'bytes-unknown-handle', 'bytes-closed-handle'):
        out = {'bytes-unaligned-result': 65, 'bytes-bad-result': 65532}.get(name, 64)
        call = f'(call $read_bytes (i32.const 999) (i32.const 1) (i32.const {out}))'
        wat = program(call) if name != 'bytes-closed-handle' else opened(
            '(call $close (i32.const 1)) ' + body)
    elif name in ('identity-unaligned-result', 'identity-bad-result'):
        wat = identity_program('', 65 if name.endswith('unaligned-result') else 65532)
    elif name == 'identity-bad-pointer':
        wat = program('(call $path_identity (i32.const -1) (i32.const 1) (i32.const 64))')
    elif name == 'identity-invalid-utf8':
        wat = program('(call $path_identity (i32.const 512) (i32.const 1) (i32.const 64))',
                      data_segment(b'\xff'))
    elif name.endswith('allocator-effect'):
        call = body if name.startswith('bytes') else '(call $path_identity (i32.const 0) (i32.const 0) (i32.const 64))'
        wat, args = program('(call $args (i32.const 64))', allocator=call), ['argument']
    elif name == 'bytes-allocator-exhaustion':
        wat = opened(body, allocator='(call $exhausted (i32.const 2))')
    elif name == 'bytes-transfer-limit':
        with (box / 'data.bin').open('wb') as file:
            file.truncate(16 * 1024 * 1024 + 1)
        wat = opened(body.replace('(i32.const 1) (i32.const 64)', '(i32.const -1) (i32.const 64)'))
    elif name.startswith('allocator-'):
        kind = {'allocator-step-exhaustion': 1, 'allocator-frame-exhaustion': 3}[name]
        wat = program('(call $args (i32.const 64))', allocator=f'(call $exhausted (i32.const {kind}))')
        args = ['argument']
    elif name.startswith('frame-exhaustion') or name == 'unknown-exhaustion':
        kind = 4 if name == 'unknown-exhaustion' else 3
        wat = program(f'(call $exhausted (i32.const {kind}))' +
                      (' (call $print (i32.const 0) (i32.const 0))' if name.endswith('stops') else ''))
    else:
        targets = {'identity-parent-escape': '../unread',
                   'identity-absolute-escape': str(box.parent / 'unread'),
                   'identity-secret-lower': '.env', 'identity-secret-upper': '.ENV',
                   'identity-secret-nested': 'sub/.Env.local',
                   'identity-secret-after-missing': 'missing/.ENV.LOCAL'}
        wat = identity_program(targets[name])
    r, outcome, digest = invoke(wat, box, host, args)
    return [outcome.get('status'), outcome.get('code'), outcome['exit']], {
        'name': name, 'wasm_sha256': digest, 'outcome': outcome,
        'stdout': r.stdout.decode(), 'stderr': r.stderr.decode()}


def mutants(mode):
    directory = fresh('mutants')
    source = HOST.read_text()
    replacements = {
        'decode-raw-bytes': ('readFile(id, maximum, out, bytes => bytes)', 'readFile(id, maximum, out, normalize)'),
        'ignore-path-identity': ('if (st.isSymbolicLink()) return false;', 'if (st.isSymbolicLink()) return true;'),
        'ignore-case-identity': ('if (!exact) return false;', 'if (false) return false;'),
        'misclassify-frames': ("if (kind === 3) exhausted('frames');", "if (kind === 3) exhausted('steps');"),
    }
    rows = []
    for mutant in PLAN['mutants']:
        name = mutant['name']
        old, new = replacements[name]
        assert source.count(old) == 1, (name, old)
        host = directory / (name + '.mjs')
        host.write_text(source.replace(old, new))
        checked = command(['node', '--check', str(host)])
        assert checked.returncode == 0, checked.stderr.decode()
        if name == 'decode-raw-bytes':
            case = next(c for c in PLAN['read_bytes'] if c['name'] == mutant['witness'])
            actual, expected, record = read_case(case, host, 'mutant-bytes')
        elif name == 'misclassify-frames':
            actual, record = control(mutant['witness'], host, 'mutant-frames')
            expected = PLAN['controls'][mutant['witness']]
            assert actual == ['Exhausted', 'steps', 4] and record['stdout'] == ''
            assert record['stderr'] == 'Exhausted\tio\tsteps\n'
        else:
            if name == 'ignore-case-identity' and mode != 'insensitive':
                rows.append({'name': name, 'killed': False, 'unavailable': 'case-insensitive filesystem'})
                continue
            case = next(c for c in PLAN['path_identity'] if c['name'] == mutant['witness'])
            actual, expected, record = identity_case(case, host, 'mutant-' + name)
        assert actual != expected, f'Survived: {name}'
        rows.append({'name': name, 'witness': mutant['witness'], 'killed': True,
                     'host_sha256': sha(host.read_bytes()), 'observation': record})
    return rows


def style():
    """Offline structural preflight of the seed witness; live rating belongs to the coordinator."""
    r = command(['node', 'scripts/perch-style.mjs', '--preflight', 'tests/compiler-io-abi-2/read-bytes.bend',
                 '--task=tests/compiler-io-abi-2/FIXTURES.md', '--json'])
    assert r.returncode == 0, r.stderr.decode()
    record = json.loads(r.stdout)
    assert record['provider_requests'] == 0 and record['structural_blockers'] == 0, record['structural_blockers']
    assert record['composition']['available'] and record['summary']['truncated_units'] == 0
    return {'changed_bend_targets': record['summary']['units'], 'structural_blockers': 0,
            'provider_requests': 0, 'rubric_version': record['rubric_version'],
            'status': 'preflight-only; no laws added; live review pending'}


def main():
    assert sys.argv[1:] in ([], ['--witnesses-only']), 'usage: check.py [--witnesses-only]'
    receipts = HERE / 'receipts'
    receipts.mkdir(exist_ok=True)
    receipt = receipts / 'host.json'
    receipt.unlink(missing_ok=True)
    reference, native = references()
    (receipts / 'reference.json').write_text(json.dumps(reference, indent=2) + '\n')
    print(f'io-abi-2 references: {len(reference["runs"])} C/JS observations, {reference["case_mode"]} filesystem', flush=True)
    witnesses = seed()
    print(f'io-abi-2 seed: {len(witnesses)} read_bytes lane runs', flush=True)
    if sys.argv[1:]:
        return 0
    fixtures = []
    for family, run in [('read_bytes', read_case), ('path_identity', identity_case)]:
        for case in PLAN[family]:
            actual, expected, record = run(case)
            assert actual == expected, (family, case['name'], compact(actual), compact(expected))
            fixtures.append({'family': family, **record})
        print(f'io-abi-2 {family}: {len(PLAN[family])} fixtures', flush=True)
    bounds = []
    for name, expected in PLAN['controls'].items():
        actual, record = control(name)
        assert actual == expected, (name, actual, expected)
        assert record['stdout'] == '' and record['stderr'] == f'{expected[0]}\tio\t{expected[1]}\n', record
        bounds.append(record)
    generated = parity(native)
    print(f'io-abi-2 parity: {len(generated)} generated spellings, host = C = JS', flush=True)
    killed = mutants(reference['case_mode'])
    files = [HOST, ROOT / 'tests/compiler-io/host/invoke.mjs',
             *(p for p in HERE.rglob('*') if p.is_file() and 'receipts' not in p.parts)]
    result = {'schema': 1, 'status': 'pass', 'profile': PLAN['profile'],
              'sources': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(files)},
              'tools': {tool: command([tool, '--version']).stdout.decode().splitlines()[0]
                        for tool in ('node', 'bun', 'wat2wasm', 'clang')},
              'seed': {name: sha((SEED.parent / name).read_bytes()) for name in
                       ('main.ts', 'base.bend', 'effs/file_open.c', 'effs/file_open.js',
                        'effs/file_read.c', 'effs/file_read.js')},
              'fixtures': fixtures, 'parity': generated, 'seed_runs': witnesses, 'host_boundaries': bounds, 'mutants': killed,
              'read_observations': sum(len(c['reads']) for c in PLAN['read_bytes']),
              'reference_observations': len(reference['runs']), 'case_mode': reference['case_mode'],
              'seed_observations': sum(len(r.get('observations', [])) for r in witnesses),
              'seed_exhausted': sum(r['status'] == 'Exhausted' for r in witnesses),
              'mutants_killed': sum(m['killed'] for m in killed),
              'style': style()}
    receipt.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(f'io-abi-2: {len(fixtures)} fixtures, {result["read_observations"]} read observations, '
          f'{len(bounds)} host controls, {result["mutants_killed"]}/{len(killed)} mutants killed')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except subprocess.TimeoutExpired:
        sys.exit('Exhausted\tio-abi-2\ttimeout')
