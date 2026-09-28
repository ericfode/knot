"""Review-2 regressions against literals and the seed, independent of Knot lowering."""
import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

from programs import Program

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / 'review-expectations.json').read_text())


def contents(box):
    paths = sorted(box.rglob('*'))
    return {'files': {p.relative_to(box).as_posix(): p.read_text() for p in paths if p.is_file()},
            'directories': [p.relative_to(box).as_posix() for p in paths if p.is_dir()]}


def seeded(h, name, case):
    box = h.fresh('review/' + name) / 'sandbox'
    box.mkdir()
    for name in case['directories']:
        (box / name).mkdir()
    for name, data in case['inputs'].items():
        (box / name).write_text(data)
    return box


def observation(r, box):
    return {'exit': r.returncode, 'stdout': r.stdout.decode(), 'stderr': r.stderr.decode(),
            **contents(box)}


def seed_checks(h):
    frozen = json.loads((HERE / 'review-seed.json').read_text())
    fixture = h.ROOT / PLAN['seed_fixture']
    assert h.sha(fixture.read_bytes()) == frozen['fixture_sha256']
    assert h.sha((HERE / 'review-expectations.json').read_bytes()) == frozen['expectations_sha256']
    assert h.sha((h.HERE / 'expectations.json').read_bytes()) == frozen['original_expectations_sha256']
    directory = h.fresh('review/seed-build')
    seed = h.ROOT / h.frozen.SEED_MAIN
    checked = h.command(['bun', str(seed), str(fixture), '--check-only'])
    assert checked.returncode == 0 and checked.stdout.strip() == b'All terms check.', checked
    built = h.command(['bun', str(seed), str(fixture), '-o', str(directory / 'empty-write'),
                       '-o', str(directory / 'empty-write.js')])
    assert built.returncode == 0, built.stderr.decode()
    lanes = {'interpreter': ['bun', str(seed), str(fixture), '--'],
             'native': [str(directory / 'empty-write')],
             'js': ['bun', str(directory / 'empty-write.js')]}
    assert list(lanes) == PLAN['seed_lanes']
    rows = []
    for case in PLAN['empty_write']:
        for lane, argv in lanes.items():
            box = seeded(h, 'seed/' + case['name'] + '-' + lane, case)
            r = h.frozen.execute([*argv, *case['argv']], box)
            observed = observation(r, box)
            assert observed == case['expected'], (case['name'], lane, observed)
            rows.append({'name': case['name'], 'lane': lane, 'observed': observed})
    assert rows == frozen['runs']
    return rows


def empty_write(h, case, host, label):
    box = seeded(h, label, case)
    p = Program()
    root = p.sequence(p.open(*case['argv']), p.branch(p.report(3, 'open '), p.sequence(
        p.write([]), p.report(3, 'write '), p.read(64), p.close(), p.report(6, 'read '))))
    module = box.parent / 'empty-write.wasm'
    digest = h.assemble(p.wat(root), module)
    r, outcome = h.invoke(module, box, host=host)
    return {'name': case['name'], 'wasm_sha256': digest, 'observed': observation(r, box),
            'outcome': outcome}


def secret_probe(h, target, mode, host, label):
    box = h.fresh('review/' + label) / 'sandbox'
    box.mkdir()
    (box / 'sub').mkdir()
    # These files are created here; no checkout or pre-existing secret is read.
    (box / '.env').write_text('DUMMY_NOT_A_SECRET\n')
    (box / 'sub/.env.local').write_text('DUMMY_LOCAL\n')
    before = contents(box)
    data = ''.join(f'\\{b:02x}' for b in target.encode())
    wat = h.small(
        f'(call $open (i32.const 100) (i32.const {len(target.encode())}) '
        '(i32.const 1000) (i32.const 1) (i32.const 64))',
        f'(data (i32.const 100) "{data}") (data (i32.const 1000) "{mode}")')
    module = box.parent / 'open.wasm'
    digest = h.assemble(wat, module)
    r, outcome = h.invoke(module, box, host=host)
    return {'path': target, 'mode': mode, 'wasm_sha256': digest, 'outcome': outcome,
            'exit': r.returncode, 'stdout': r.stdout.decode(), 'stderr': r.stderr.decode(),
            'files_unchanged': contents(box) == before}


def secret_agrees(row):
    return (row['outcome'] == PLAN['secret_outcome'] and row['exit'] == PLAN['secret_outcome']['exit']
            and row['stdout'] == '' and row['stderr'] == PLAN['secret_stderr'] and row['files_unchanged'])


def oracle_controls(h, module, label):
    directory = h.fresh('review/' + label)
    expected = directory / 'expectations.json'
    original = b'previous frozen bytes\n'
    rows = []
    for stream in ('stdout', 'stderr', 'merged'):
        for status in (0, 1):
            for fault_pass in (1, 2):
                calls = 0
                expected.write_bytes(original)
                destination = 'stdout' if stream == 'stdout' else 'stderr'
                script = (f'import sys; print({PLAN["oracle_fault"]["marker"]!r}, '
                          f'file=sys.{destination}); sys.exit({status})')

                def build():
                    nonlocal calls
                    calls += 1
                    if calls == fault_pass:
                        module.execute([sys.executable, '-c', script], h.ROOT, merged=stream == 'merged')
                    return {'fixtures': []}

                reason = ''
                with patch.object(module, 'build', build), patch.object(module, 'EXPECTATIONS', expected), \
                     patch.object(module, 'ROOT', h.ROOT), \
                     patch.object(sys, 'argv', ['regen.py', '--write']), contextlib.redirect_stdout(io.StringIO()):
                    try:
                        module.main()
                    except SystemExit as error:
                        reason = str(error.code).split(':', 1)[0]
                exhausted = reason == PLAN['oracle_fault']['outcome_prefix']
                preserved = expected.read_bytes() == original
                rows.append({'stream': stream, 'seed_exit': status, 'fault_pass': fault_pass,
                             'exhausted': exhausted, 'expectations_preserved': preserved,
                             'passed': exhausted and preserved and calls == fault_pass})
    # A normal compiler rejection is still an observation, not a lane fault.
    for status in (0, 1):
        script = f'import sys; print("ordinary result", file=sys.stderr); sys.exit({status})'
        r = module.execute([sys.executable, '-c', script], h.ROOT)
        rows.append({'ordinary_exit': status,
                     'passed': r.returncode == status and r.stdout == b'' and r.stderr == b'ordinary result\n'})
    return rows


def mutants(h):
    directory = h.fresh('review/mutants')
    source = h.HOST.read_text()
    rows = []
    replacements = {
        'case-sensitive-secret': ('const q = p.toLowerCase();', 'const q = p;'),
        'empty-write-ebadf': ("h.mode === 'r' && bytes.length > 0", "h.mode === 'r'"),
    }
    for name, (old, new) in replacements.items():
        assert source.count(old) == 1, (name, old)
        host = directory / (name + '.mjs')
        host.write_text(source.replace(old, new))
        assert h.command(['node', '--check', str(host)]).returncode == 0, name
        if name == 'case-sensitive-secret':
            witnesses = [secret_probe(h, '.ENV', mode, host, 'mutant-secret-' + mode)
                         for mode in PLAN['secret_modes']]
            assert all(r['outcome']['status'] == 'Completed' and r['exit'] == 0 for r in witnesses), witnesses
            assert all(not secret_agrees(r) for r in witnesses), name
        else:
            witnesses = [empty_write(h, case, host, 'mutant-empty-' + case['name'])
                         for case in PLAN['empty_write']]
            assert all(r['outcome'] == {'status': 'Completed', 'exit': 0} for r in witnesses), witnesses
            assert all(r['observed'] != c['expected'] for r, c in zip(witnesses, PLAN['empty_write'])), name
        rows.append({'name': name, 'killed': True, 'sha256': h.sha(host.read_bytes()), 'witnesses': witnesses})

    name = 'freeze-seed-memory-fault'
    old = "if b'bend: memory fault' in r.stdout + (r.stderr or b''):"
    source = (h.HERE / 'regen.py').read_text()
    assert source.count(old) == 1
    changed = source.replace(old, 'if False:')
    compile(changed, name, 'exec')
    path = directory / (name + '.py')
    path.write_text(changed)
    spec = importlib.util.spec_from_file_location('mutant_regen', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    witnesses = oracle_controls(h, module, 'mutant-oracle')
    assert all(not r['passed'] for r in witnesses if 'fault_pass' in r), witnesses
    assert all(r['passed'] for r in witnesses if 'ordinary_exit' in r), witnesses
    rows.append({'name': name, 'killed': True, 'sha256': h.sha(path.read_bytes()), 'witnesses': witnesses})
    assert [r['name'] for r in rows] == PLAN['mutants']
    return rows


def run(h):
    seed = seed_checks(h)
    empty = [empty_write(h, case, h.HOST, 'empty/' + case['name']) for case in PLAN['empty_write']]
    for row, case in zip(empty, PLAN['empty_write']):
        assert row['observed'] == case['expected'], row
        assert row['outcome'] == {'status': 'Completed', 'exit': 0}, row
    secrets = [secret_probe(h, target, mode, h.HOST, f'secret/{i}-{mode}')
               for i, target in enumerate(PLAN['secret_paths']) for mode in PLAN['secret_modes']]
    assert all(secret_agrees(row) for row in secrets), secrets
    oracle = oracle_controls(h, h.frozen, 'oracle')
    assert all(r['passed'] for r in oracle), oracle
    killed = mutants(h)
    preflight = h.command(['node', 'scripts/perch-style.mjs', '--preflight', PLAN['seed_fixture'],
                           '--task=tests/compiler-io/host/REVIEW-2.md', '--json'])
    assert preflight.returncode == 0, preflight.stderr.decode()
    return {'seed_runs': seed, 'empty_write': empty, 'secret_paths': secrets,
            'oracle_controls': oracle, 'mutants': killed, 'preflight': json.loads(preflight.stdout)}
