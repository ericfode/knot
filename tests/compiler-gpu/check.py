#!/usr/bin/env python3
"""Frozen source differential, compiler mutants, and records-2 host boundaries."""
from __future__ import annotations
import argparse
import copy
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/gpu-emit/gate'
SEED = ['bun', ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']
HOST = ROOT / 'scripts/run-records.py'
sys.path.insert(0, str(ROOT / 'research/adaptive-tasks/runtime2'))
from bundle import validate  # noqa: E402
from driver import Driver  # noqa: E402


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, timeout=90):
    argv = list(map(str, argv))
    try:
        p = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
        return {'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except subprocess.TimeoutExpired:
        return {'argv': argv, 'exit': None, 'classification': 'Exhausted', 'stdout': '', 'stderr': 'harness-timeout'}


def success(argv):
    result = run(argv)
    require(result['exit'] == 0, result)
    return result


def diagnostic(result, code, prefix):
    require(result['exit'] == code and result['stderr'].startswith(prefix) and not result['stdout'], (prefix, result))


def compiled(command, source, output, tail=(), prefix=()):
    output.unlink(missing_ok=True)
    result = success([*command, *prefix, source, output, *tail])
    require(result['stdout'].strip() == f'Built\t{output.stat().st_size}', result)
    return {'sha256': sha(output), 'bytes': output.stat().st_size, 'command': result}


def host(bundle, label, cpu=True, quantum=64, extra=()):
    receipt = BUILD / (label + '-host.json')
    result = run(['python3', HOST, bundle, *(('--cpu-only',) if cpu else ()), '--quantum', quantum,
                  '--receipt', receipt, *extra])
    require(receipt.exists(), result)
    return result, json.loads(receipt.read_text())


def clean_result(observation, expected):
    """Independent final ownership assertion: an enum result is the only root."""
    require(observation['phase'] == 2, ('not halted', observation['phase']))
    status, tag, _, readers, _, objects, captures, pending, joins = observation['state']
    require(status == 0 and tag == expected, ('wrong result', status, tag, expected))
    live = [obj for obj in objects if obj]
    owners = [identity for identity in captures if identity]
    require(len(live) == len(owners) == 1 and live[0][0] == owners[0], 'surviving owners')
    require(live[0][2] == 1 and live[0][3] == expected and live[0][4] == [], 'result representation')
    require(not pending and readers == 0, 'pending cleanup or reader')
    require(all(j[1] in (0, 4) and all(x == 0 for x in j[8]) for j in joins), 'unconsumed join')
    require(all(j[0] == j[4] == 1 for j in joins if j[1]), 'one-shot attempts and completion')


MUTANTS = [
    ('branch-tag', 'Op{14,source,tag,label,', 'Op{14,source,U32.add(tag,1),label,', 'three-colors', 1, 'result'),
    ('move-data', 'Bool.pick(U32,retained,2,3)', 'Bool.pick(U32,retained,3,3)', 'sharing', 0, 'Invalid'),
    ('missing-release', 'Op{5,source,0,0,0,0}', 'Op{17,0,0,0,0,0}', 'aliasing', 0, 'owners'),
    ('swapped-slot', 'push(delivery(join,slot,source),deliveries',
     'push(delivery(join,Bool.pick(U32,U32.is_eq(slot,0),1,0),source),deliveries', 'argument-order', 0, 'result'),
    ('stale-attempt', 'Op{9,join,1,slot,source,0}', 'Op{9,join,0,slot,source,0}', 'pair', 0, 'Invalid'),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--device', action='store_true')
    mode.add_argument('--cpu-only', action='store_false', dest='device')
    parser.set_defaults(device=False)
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    receipt = args.receipt or HERE / ('receipts/device.json' if args.device else 'receipts/gpu.json')
    observations_path = HERE / ('receipts/device-observations.json.gz' if args.device else 'receipts/observations.json.gz')
    BUILD.mkdir(parents=True, exist_ok=True)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    require(os.environ.get('BEND_NO_TELEMETRY') == '1', 'export BEND_NO_TELEMETRY=1')
    cases = json.loads((HERE / 'cases.json').read_text())
    frozen = json.loads((HERE / 'expectations.json').read_text())
    record = {'schema': 1, 'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'incomplete', 'profile': 'knot-gpu-records-2', 'deviceExecution': False,
              'mode': 'metal' if args.device else 'cpu-simulation', 'seed_revision': cases['seed_revision']}
    observations = []
    try:
        sources = [*sorted((ROOT / 'src').glob('*.bend')), ROOT / 'src/SPEC.md', ROOT / 'src/CONTRACT.json',
                   HOST, ROOT / 'scripts/run-records-device.mjs', ROOT / 'scripts/run-wasm.mjs',
                   *sorted(HERE.glob('*.bend')), *sorted(HERE.glob('*.json')), HERE / 'SPEC.md', Path(__file__),
                   *[ROOT / c['file'] for c in cases['cases']], *[ROOT / c['file'] for c in cases['rejects']],
                   *[ROOT / 'research/adaptive-tasks/runtime2' / f for f in
                     ('bundle.py', 'driver.py', 'reference.py', 'layout.json', 'runtime.wgsl')]]
        record['inputs'] = {str(p.relative_to(ROOT)): sha(p) for p in sources}
        record['seed'] = {f: sha(ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2' / f)
                          for f in ('main.ts', 'bend.ts', 'comp.ts', 'base.bend')}
        record['tools'] = {t: success([t, '--version'])['stdout'].strip() for t in ('bun', 'node', 'python3', 'wasm2wat')}
        expected = [(c['name'], call, sha(ROOT / c['file'])) for c in cases['cases'] for call in c['calls']]
        require(expected == [(o['case'], o['call'], o['source_sha256']) for o in frozen['observations']], 'frozen expectations drifted')
        require([(c['name'], sha(ROOT / c['file'])) for c in cases['rejects']] ==
                [(c['name'], c['source_sha256']) for c in frozen['rejects']], 'frozen rejection sources drifted')
        record['proof'] = success([*SEED, ROOT / 'src/records-PROOF.bend'])
        require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
        record['laws'] = 13
        record['builds'], lanes = [], {}
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
            lanes[lane] = {}
            for phase, entry in [('compile', HERE / 'compile.bend'), ('eval', ROOT / 'src/eval-cli.bend'),
                                 ('wasm', ROOT / 'tests/compiler-fields-wasm/compile.bend')]:
                output = BUILD / (phase + suffix)
                result = success([*SEED, entry, '-o', output])
                record['builds'].append({'lane': lane, 'phase': phase, 'sha256': sha(output), 'result': result})
                lanes[lane][phase] = [*runtime, output]
        record['fixtures'], record['devices'] = [], []
        bundles, final_states = {}, {}
        for case in cases['cases']:
            name, source = case['name'], ROOT / case['file']
            fixture = {'name': name, 'reference': [], 'lanes': {}}
            for i, call in enumerate(case['calls']):
                wrapper = BUILD / f'{name}-seed-{i}.bend'
                imported = os.path.relpath(source, wrapper.parent)
                wrapper.write_text(f'import {imported} as F\n\ndef main() -> F.{case["type"]}:\n  {call["seed"]}\n')
                result = success([*SEED, wrapper])
                literal = imported.removesuffix('.bend') + '.' + case['constructors'][call['tag']] + '{}'
                require(result['stdout'].strip() == literal, (call, result))
                fixture['reference'].append(result)
            for lane, commands in lanes.items():
                wasm = BUILD / f'{name}-{lane}.wasm'
                compiled(commands['wasm'], source, wasm)
                decoded = success(['wasm2wat', wasm])
                fixture['lanes'][lane] = {'wasm_sha256': sha(wasm), 'wat_sha256': hashlib.sha256(decoded['stdout'].encode()).hexdigest(), 'calls': []}
                for i, call in enumerate(case['calls']):
                    tail = [call['export'], *call['arguments']]
                    bundle = BUILD / f'{name}-{i}-{lane}.json'
                    built = compiled(commands['compile'], source, bundle, tail)
                    validate(json.loads(bundle.read_text()))
                    evaluated = success([*commands['eval'], source, call['export'], 65536, *call['arguments']])
                    literal = f'Evaluated\t{case["type_id"]}\t{call["tag"]}\t{case["constructors"][call["tag"]]}{{}}'
                    require(evaluated['stdout'].strip() == literal, (literal, evaluated))
                    wasm_result = success(['node', ROOT / 'scripts/run-wasm.mjs', '--profile=knot-fields-wasm-1', wasm, *tail])
                    require(json.loads(wasm_result['stdout'])['result'] == call['tag'], wasm_result)
                    cpu, execution = host(bundle, f'{name}-{i}-{lane}')
                    require(cpu['exit'] == 0, cpu)
                    clean_result(execution['observation'], call['tag'])
                    observation = execution['observation']
                    key = (name, i)
                    if key in bundles:
                        require(built['sha256'] == sha(bundles[key]), ('compiler bytes differ', key))
                        require(observation == final_states[key], ('compiler ownership differs', key))
                    else:
                        bundles[key], final_states[key] = bundle, observation
                        if args.device:
                            device_result, device = host(bundle, f'{name}-{i}-metal', False)
                            require(device_result['exit'] == 0 and device['deviceExecution'], device_result)
                            require(device['observation'] == observation, ('device state mismatch', key))
                            record['devices'].append({k: v for k, v in device.items() if k != 'observation'})
                    observations.append({'case': name, 'call': i, 'lane': lane, 'observation': observation})
                    fixture['lanes'][lane]['calls'].append({'call': call, 'bundle_sha256': built['sha256'],
                        'bytes': built['bytes'], 'rounds': execution['rounds'], 'eval': evaluated, 'wasm': wasm_result})
            record['fixtures'].append(fixture)
            print(f'gpu-emit: {name}: {len(case["calls"])} calls x 2 compiler lanes', file=sys.stderr, flush=True)
        record['suspensions'] = []
        for key in [('sharing', 0), ('type-loop', 0), ('parity', 4)]:
            for quantum in (1, 7):
                result, execution = host(bundles[key], f'{key[0]}-{quantum}', quantum=quantum)
                require(result['exit'] == 0 and execution['observation'] == final_states[key], ('suspension changes state', key, quantum, result))
                if args.device:
                    device_result, device = host(bundles[key], f'{key[0]}-{quantum}-metal', False, quantum)
                    require(device_result['exit'] == 0 and device['observation'] == final_states[key], ('device suspension', key, quantum, device_result))
                record['suspensions'].append({'case': key[0], 'call': key[1], 'quantum': quantum, 'rounds': execution['rounds']})
        # One-instruction replay proves that the corpus exercises the emitted loop.
        record['executed_opcodes'] = []
        backward = 0
        for key in [('sharing', 0), ('type-loop', 0), ('parity', 4), ('argument-order', 0)]:
            data = json.loads(bundles[key].read_text()); machine = Driver(data['config'], data['instructions'])
            seen = set()
            for _ in range(4096):
                pc = machine.pc; op = data['instructions'][pc][0]; seen.add(op)
                observation = machine.run(1)
                backward += int(op == 15 and machine.pc < pc)
                if machine.phase == 2: break
            else: raise AssertionError('bounded one-step replay did not halt')
            require(observation == final_states[key], ('one-step state differs', key))
            record['executed_opcodes'] = sorted(set(record['executed_opcodes']) | seen)
        require({1, 2, 3, 4, 5, 6, 8, 9, 11, 14, 15, 16} <= set(record['executed_opcodes']) and backward > 0, 'missing core operation or executed recursion')
        record['executed_back_edges'] = backward
        record['rejects'] = []
        for case in frozen['rejects']:
            reference = success([*SEED, ROOT / case['file']])
            require(reference['stdout'].strip() == case['seed_stdout'], reference)
            results = []
            for lane, commands in lanes.items():
                output = BUILD / f'{case["name"]}-{lane}-unsupported.json'
                for stale in (False, True):
                    output.unlink(missing_ok=True)
                    if stale: output.write_bytes(b'previous artifact\n')
                    result = run([*commands['compile'], ROOT / case['file'], output, case['entry']])
                    diagnostic(result, 3, 'Unsupported\trecords\t' + case['code'] + '\t')
                    require(output.read_bytes() == b'previous artifact\n' if stale else not output.exists(), 'failed emission changed output')
                    results.append(result)
            record['rejects'].append({'name': case['name'], 'reference': reference, 'observations': results})
        record['boundaries'] = []
        control = ROOT / 'tests/compiler-fields-wasm/fixtures/pair.bend'
        for lane, commands in lanes.items():
            for label, source, prefix, tail, code, diagnostic_prefix in [
                ('depth', control, ['--limits', 0, 1048576], ['main'], 4, 'Exhausted\trecords\t'),
                ('bytes', control, ['--limits', 4096, 0], ['main'], 4, 'Exhausted\trecords\t'),
                ('unknown-export', control, [], ['absent'], 5, 'HostFailure\trecords\tunknown-export'),
                ('arity', control, [], ['main', 0], 5, 'HostFailure\trecords\targument-arity'),
                ('ordinal', control, [], ['direct', 2, 0], 5, 'HostFailure\trecords\targument-range'),
                ('structured-input', HERE / 'fixtures/parity.bend', [], ['even', 0], 3, 'Unsupported\trecords\tentry-parameters\t'),
                ('invalid', ROOT / 'tests/subsets/s1/affine-reuse.bend', [], ['main'], 2, 'Invalid\tcheck\taffine-reuse\t'),
            ]:
                output = BUILD / f'boundary-{label}-{lane}.json'; output.write_bytes(b'previous artifact\n')
                result = run([*commands['compile'], *prefix, source, output, *tail])
                diagnostic(result, code, diagnostic_prefix)
                require(output.read_bytes() == b'previous artifact\n', 'boundary clobbered output')
                record['boundaries'].append({'name': label, 'lane': lane, 'result': result})
            exact = bundles[('pair', 0)].stat().st_size
            for cap in (exact - 1, exact):
                output = BUILD / f'bytes-{cap}-{lane}.json'; output.unlink(missing_ok=True)
                result = run([*commands['compile'], '--limits', 4096, cap, control, output, 'main'])
                if cap == exact:
                    require(result['exit'] == 0 and output.read_bytes() == bundles[('pair', 0)].read_bytes(), 'exact byte boundary')
                else:
                    diagnostic(result, 4, 'Exhausted\trecords\t'); require(not output.exists(), 'one-past byte output')
                record['boundaries'].append({'name': 'exact-bytes' if cap == exact else 'one-past-bytes', 'lane': lane, 'result': result})
        original = json.loads(bundles[('pair', 0)].read_text())
        affine = copy.deepcopy(original); affine['config']['rcLimit'] = 1
        path = BUILD / 'host-affine-count.json'; path.write_text(json.dumps(affine))
        result, execution = host(path, 'affine-count')
        require(result['exit'] == 0, result)
        clean_result(execution['observation'], 1)
        record['boundaries'].append({'name': 'affine-data-count-one', 'result': result})
        for name, change, exit_code, prefix in [
            ('version', lambda b: b.update(version=3), 3, 'Unsupported\trecords\tversion'),
            ('opcode', lambda b: b['instructions'][0].__setitem__(0, 18), 3, 'Unsupported\trecords\topcode'),
            ('reserved', lambda b: b['instructions'][0].__setitem__(7, 1), 2, 'Invalid\trecords\treserved-operand'),
            ('storage', lambda b: b['config'].update(maxStorageBytes=32), 4, 'Exhausted\trecords\tstorage-range'),
            ('objects', lambda b: b['config'].update(objects=0), 4, 'Exhausted\trecords\tinstruction-'),
        ]:
            b = copy.deepcopy(original); change(b); path = BUILD / f'host-{name}.json'; path.write_text(json.dumps(b))
            result, execution = host(path, 'boundary-' + name)
            diagnostic(result, exit_code, prefix)
            record['boundaries'].append({'name': 'host-' + name, 'result': result})
        result, execution = host(bundles[('pair', 0)], 'zero-quantum', quantum=0, extra=['--max-rounds', '1'])
        diagnostic(result, 4, 'Exhausted\trecords\tround-budget')
        require(execution['observation']['pc'] == 0 and execution['observation']['state'][2] == 1, 'zero quantum executed')
        record['boundaries'].append({'name': 'zero-quantum', 'result': result})
        record['mutants'] = []
        original_source = (ROOT / 'src/records.bend').read_text()
        by_name = {c['name']: c for c in cases['cases']}
        for name, old, new, witness, number, reason in MUTANTS:
            require(original_source.count(old) == 1, ('mutation anchor', name))
            directory = BUILD / 'mutants' / name; (directory / 'src').mkdir(parents=True, exist_ok=True)
            for path in (ROOT / 'src').glob('*.bend'): shutil.copy2(path, directory / 'src' / path.name)
            (directory / 'src/records.bend').write_text(original_source.replace(old, new))
            entry = directory / 'tests/compiler-gpu/compile.bend'; entry.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(HERE / 'compile.bend', entry)
            checked = success([*SEED, entry, '--check-only'])
            require(checked['stdout'].strip() == 'All terms check.', checked)
            binary = directory / 'compile.js'; success([*SEED, entry, '-o', binary])
            case, call = by_name[witness], by_name[witness]['calls'][number]
            bundle = directory / 'bundle.json'
            compiled(['bun', binary], ROOT / case['file'], bundle, [call['export'], *call['arguments']])
            validate(json.loads(bundle.read_text()))  # A transport/type failure is not a semantic kill.
            result, execution = host(bundle, 'mutant-' + name, cpu=not args.device)
            if reason == 'Invalid':
                diagnostic(result, 2, 'Invalid\trecords\tinstruction-')
                killed_by = 'runtime Invalid'
            else:
                require(result['exit'] == 0, result)
                observed = execution['observation']
                if reason == 'result':
                    require(observed['state'][1] != call['tag'], ('surviving result mutant', name))
                    killed_by = 'fixed result tag'
                else:
                    require(observed['state'][1] == call['tag'], 'release mutant changed the unrelated result')
                    try: clean_result(observed, call['tag'])
                    except AssertionError as error:
                        require(str(error) == 'surviving owners', str(error)); killed_by = str(error)
                    else: raise AssertionError('surviving release mutant')
            record['mutants'].append({'name': name, 'typechecked': True, 'bundle_validated': True,
                'witness': witness, 'call': number, 'killed': True, 'killed_by': killed_by,
                'source_sha256': sha(directory / 'src/records.bend'), 'bundle_sha256': sha(bundle),
                'execution': {k: v for k, v in execution.items() if k != 'observation'}})
            observations.append({'mutant': name, 'observation': execution['observation']})
        record['summary'] = {'programs': len(cases['cases']), 'reference_calls': len(expected), 'compiler_lanes': 2,
            'eval_observations': len(expected) * 2, 'wasm_observations': len(expected) * 2,
            'records_observations': len(expected) * 2, 'unsupported_programs': len(record['rejects']),
            'unsupported_observations': sum(len(c['observations']) for c in record['rejects']),
            'boundaries': len(record['boundaries']), 'suspension_checks': len(record['suspensions']),
            'one_step_replays': 4, 'laws': record['laws'], 'mutants_killed': len(record['mutants']),
            'device_calls': len(record['devices'])}
        record['status'] = 'pass'; record['deviceExecution'] = args.device
    except Exception as error:
        record.update(status='failed', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        observations_path.write_bytes(gzip.compress(json.dumps(observations, separators=(',', ':')).encode(), mtime=0))
        record['observations_sha256'] = sha(observations_path)
        receipt.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'status': record['status'], **record['summary']}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
