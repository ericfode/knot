#!/usr/bin/env python3
"""Verify frozen seed records, then test the IO ABI through actual Wasm."""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HOST = ROOT / 'scripts/run-wasm-io.mjs'
WORK = ROOT / '.local/io-host'
RECEIPT = HERE / 'receipts/host.json'
PLAN = json.loads((HERE / 'host/PLAN.json').read_text())
sys.path.insert(0, str(HERE / 'host'))
from programs import fixture, TEMPLATE
from review import run as review_checks

spec = importlib.util.spec_from_file_location('frozen_io_records', HERE / 'regen.py')
frozen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frozen)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def command(argv, **kwargs):
    env = frozen.environment()
    return subprocess.run(argv, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                          capture_output=True, timeout=120, **kwargs)


def assemble(wat, target):
    source = target.with_suffix('.wat')
    source.write_text(wat)
    r = command(['wat2wasm', str(source), '-o', str(target)])
    assert r.returncode == 0, r.stderr.decode()
    return sha(target.read_bytes())


def fresh(name):
    directory = WORK / name
    assert directory.is_relative_to(WORK) and directory != WORK
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    return directory


def invoke(module, box, argv=(), merged=False, host=HOST):
    args = box.parent / (box.name + '-args.json')
    report = box.parent / (box.name + '-outcome.json')
    args.write_text(json.dumps(argv))
    report.unlink(missing_ok=True)
    r = subprocess.run(['node', str(HERE / 'host/invoke.mjs'), str(host), str(module),
                        str(box), str(args), str(report)], cwd=box,
                       env=frozen.environment(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT if merged else subprocess.PIPE, timeout=120)
    assert report.is_file(), (r.returncode, r.stderr)
    return r, json.loads(report.read_text())


def observe(name, run, module, host=HOST, cli=False):
    directory = fresh('runs/' + name + '/' + run['name'])
    box = directory / 'sandbox'
    box.mkdir()
    for dest, source in run['inputs'].items():
        shutil.copyfile(frozen.INPUTS / source, box / dest)
    if cli:
        argv = [a if isinstance(a, str) else bytes.fromhex(a['hex']) for a in run['argv']]
        r = command(['node', str(host), str(module), str(box), '--', *argv])
        outcome = None
    else:
        r, outcome = invoke(module, box, run['argv'], run['streams'] == 'merged', host)
    record = {'exit': r.returncode}
    if run['streams'] == 'merged':
        record['output'] = frozen.blob(r.stdout, frozen.STREAM_LIMIT)
    else:
        record['stdout'] = frozen.blob(r.stdout, frozen.STREAM_LIMIT)
        record['stderr'] = frozen.blob(r.stderr, frozen.STREAM_LIMIT)
    record['files'] = frozen.snapshot(box, run['inputs'])
    return record, outcome


def differences(expected, observed, outcome):
    result = [key for key in sorted(expected.keys() | observed.keys())
              if expected.get(key) != observed.get(key)]
    if outcome.get('status') not in ('Completed', 'Halted') or outcome.get('exit') != expected['exit']:
        result.append('host-outcome')
    return result


def small(body='', extra='', main_params='', allocator='i32.const 1024', imports=None):
    if imports is None:
        imports = '\n'.join(TEMPLATE.read_text().splitlines()[2:10])
    return f'''(module {imports}
      (memory (export "memory") 1 4)
      (func (export "knot_alloc") (param i32) (result i32) {allocator})
      (func (export "knot_main") {main_params} {body})
      {extra})'''


def controls():
    rows = []
    definitions = {
        'unknown_import': small(imports='(import "wasi_snapshot_preview1" "fd_write" (func))'),
        'wrong_import_signature': small(imports='(import "knot_io" "print" (func (param i32)))'),
        'wrong_entry_signature': small(main_params='(param i32)'),
        'start_section': small(extra='(func $start) (start $start)'),
        'bad_pointer': small('(call $print (i32.const -1) (i32.const 4))'),
        'unaligned_result': small('(call $args (i32.const 1))'),
        'non_scalar_text': small('(call $print (i32.const 100) (i32.const 3))',
                                '(data (i32.const 100) "\\ed\\a0\\80")'),
        'unknown_handle': small('(call $read (i32.const 999) (i32.const 4) (i32.const 64))'),
        'step_budget': fixture('print-lines', []).replace('(i32.const 2000000)', '(i32.const 0)'),
        'allocation_budget': small('(call $args (i32.const 64))',
                                  allocator='(call $exhausted (i32.const 2)) (i32.const 0)'),
        'allocator_effect': small('(call $args (i32.const 64))',
                                  allocator='(call $close (i32.const 999)) (i32.const 1024)'),
        'unexpected_trap': small('(unreachable)'),
    }
    directory = fresh('controls')
    sentinel = directory / 'outside.txt'
    sentinel.write_bytes(b'outside unchanged\n')
    for name, expected in PLAN['literal_controls'].items():
        box = directory / name
        box.mkdir()
        if name in ('parent_escape', 'absolute_escape', 'symlink_escape', 'symlink_parent', 'secret_path'):
            target = {'parent_escape': '../outside.txt', 'absolute_escape': str(sentinel),
                      'symlink_escape': 'link', 'symlink_parent': 'link/outside.txt',
                      'secret_path': '.env'}[name]
            if name == 'symlink_escape':
                (box / 'link').symlink_to(sentinel)
            if name == 'symlink_parent':
                (box / 'link').symlink_to(directory, target_is_directory=True)
            data = ''.join(f'\\{b:02x}' for b in target.encode())
            definitions[name] = small(
                f'(call $open (i32.const 100) (i32.const {len(target.encode())}) '
                '(i32.const 1000) (i32.const 1) (i32.const 64))',
                f'(data (i32.const 100) "{data}") (data (i32.const 1000) "w")')
        module = directory / (name + '.wasm')
        if name == 'invalid_module':
            module.write_bytes(b'not wasm')
        elif name != 'missing_module':
            assemble(definitions[name], module)
        r, outcome = invoke(module, box, ['argument'] if name in ('allocation_budget', 'allocator_effect') else [])
        actual = [outcome.get('status'), outcome.get('code'), outcome.get('exit')]
        assert actual == expected, (name, expected, actual, r.stderr)
        assert r.returncode == expected[2] and r.stdout == b'', (name, r)
        assert r.stderr == f'{expected[0]}\tio\t{expected[1]}\n'.encode(), (name, r.stderr)
        assert sentinel.read_bytes() == b'outside unchanged\n', name
        assert sorted(p.name for p in box.iterdir()) == (['link'] if name.startswith('symlink_') else []), name
        rows.append({'name': name, 'outcome': outcome})
    return rows


def mutants(witnesses):
    original = HOST.read_text()
    replacements = {
        'utf16-units': [("Buffer.from(decoder.decode(bytes), 'utf8')",
                         "Buffer.concat(decoder.decode(bytes).split('').map(unit => Buffer.from(unit)))")],
        'drop-truncated-replacement': [("decoder.decode(bytes)",
                         "new TextDecoder('utf-8', {ignoreBOM: true}).decode(bytes, {stream: true})")],
        'unmasked-exit': [('(code >>> 0) % 256', '(code >>> 0)')],
        'read-write-handle': [("if (h.mode !== 'r')", 'if (false)'), ('c.O_WRONLY', 'c.O_RDWR')],
        'unchecked-byte': [('if (invalid !== 0)', 'if (false)')],
        'print-no-lf': [("Buffer.concat([bytes, Buffer.from('\\n')])", 'bytes')],
    }
    rows = []
    directory = fresh('mutants')
    for mutant in PLAN['mutants']:
        name = mutant['name']
        source = original
        for old, new in replacements[name]:
            assert old in source, (name, old)
            source = source.replace(old, new)
        host = directory / (name + '.mjs')
        host.write_text(source)
        assert command(['node', '--check', str(host)]).returncode == 0, name
        fixture_name, run, module = witnesses[mutant['witness']]
        observed, outcome = observe('mutant-' + name, run, module, host)
        diff = differences(run['seed'], observed, outcome)
        assert diff, f'Survived: {name}'
        # A mutant must execute the well-typed program; infrastructure failures do not kill it.
        assert outcome['status'] in ('Completed', 'Halted'), (name, outcome)
        rows.append({'name': name, 'witness': mutant['witness'], 'killed': True,
                     'changed_fields': diff, 'host_outcome': outcome, 'host_sha256': sha(host.read_bytes())})
    return rows


def main():
    RECEIPT.unlink(missing_ok=True)
    # First executable gate action: independently verify the complete frozen suite.
    verify = command(['python3', '-B', str(HERE / 'regen.py')])
    sys.stdout.buffer.write(verify.stdout)
    sys.stderr.buffer.write(verify.stderr)
    if verify.returncode:
        return verify.returncode
    document = json.loads((HERE / 'expectations.json').read_text())
    fixtures = {f['name']: f for f in document['fixtures']}
    witnesses, records, cli_records = {}, [], []
    modules = fresh('modules')
    for name in PLAN['fixtures']:
        f = fixtures[name]
        assert f['knot']['outcome'] == 'agree', name
        rows = []
        for run in f['runs']:
            module = modules / (name + '-' + run['name'] + '.wasm')
            module_hash = assemble(fixture(name, run['argv']), module)
            observed, outcome = observe(name, run, module)
            diff = differences(run['seed'], observed, outcome)
            assert not diff, (name, run['name'], diff, observed, outcome)
            key = name + '/' + run['name']
            witnesses[key] = (name, run, module)
            rows.append({'name': run['name'], 'wasm_sha256': module_hash,
                         'outcome': outcome, 'observed': observed})
            if name == PLAN['cli_fixture']:
                cli_observed, _ = observe('cli-' + name, run, module, cli=True)
                assert cli_observed == run['seed'], (name, run['name'], cli_observed)
                cli_records.append({'name': name + '/' + run['name'], 'observed': cli_observed})
        records.append({'name': name, 'runs': rows})
        print(f'io-host {name}: {len(rows)} field-exact runs', flush=True)
    bounds = controls()
    killed = mutants(witnesses)
    review = review_checks(sys.modules[__name__])
    review_counts = {name: len(review[name]) for name in
                     ('seed_runs', 'empty_write', 'secret_paths', 'oracle_controls', 'mutants')}
    # Verify that every promised errno has an observed, seed-matched report.
    outputs = '\n'.join(json.dumps(r['observed'], ensure_ascii=False) for f in records for r in f['runs'])
    for code in PLAN['errno']:
        assert f' {code} ' in outputs or f'\\t{code}\\t' in outputs, code
    source_names = ['scripts/run-wasm-io.mjs', 'tests/compiler-io/host-check.py',
                    'tests/compiler-io/expectations.json', 'tests/compiler-io/regen.py',
                    *('tests/compiler-io/host/' + n for n in
                      ('PLAN.json', 'runtime.wat', 'programs.py', 'invoke.mjs', 'review.py',
                       'empty-write.bend', 'review-expectations.json', 'review-seed.json', 'REVIEW-2.md'))]
    receipt = {'schema': 1, 'status': 'pass', 'profile': 'knot-io-1',
               'boundary': PLAN['boundary'],
               'sources': {n: sha((ROOT / n).read_bytes()) for n in source_names},
               'seed': document['seed'],
               'tools': {tool: command([tool, '--version']).stdout.decode().strip()
                         for tool in ('node', 'bun', 'wat2wasm')},
               'seed_fixtures': len(fixtures),
               'seed_runs': sum(len(f.get('runs', [])) for f in fixtures.values()),
               'conformance_runs': len(witnesses), 'cli_runs': len(cli_records), 'cli': cli_records,
               'errno': PLAN['errno'],
               'stress': PLAN['stress'], 'fixtures': records,
               'host_boundaries': bounds, 'mutants': killed,
               'review': review, 'review_counts': review_counts,
               'style': {'changed_bend_targets': 1, 'status': 'preflight-only; live review pending',
                         'structural_blockers': review['preflight']['structural_blockers']}}
    RECEIPT.parent.mkdir(exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n')
    print(f'io-host: {len(records)} fixtures, {len(witnesses)} runs, '
          f'{len(cli_records)} CLI runs, {len(bounds)} host controls, {len(killed)} mutants killed')
    print(f'io-host review-2: {review_counts}')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except subprocess.TimeoutExpired:
        sys.exit('Exhausted\tio-host\ttimeout')
