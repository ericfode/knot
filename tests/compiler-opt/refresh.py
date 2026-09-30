#!/usr/bin/env python3
"""Probe the frozen refresh programs without implementing language semantics."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

import check as gate

ROOT = gate.ROOT
HERE = gate.HERE
BUILD = ROOT / '.local/opt-1/refresh/check'
RECEIPT = HERE / 'receipts/refresh.json'


def seed(case):
    """The seed's native build needs Base; fixture names avoid its namespace."""
    wrapper = BUILD / (case['name'] + '-reference.bend')
    relative = os.path.relpath(gate.corpus_path(case), wrapper.parent)
    wrapper.write_text(f'import Base\nimport {relative} as F\n\ndef main() -> F.Flag:\n  F.main()\n')
    expected = relative.removesuffix('.bend') + '.' + case['constructors'][case['calls'][0]['tag']] + '{}'
    interpreted = gate.successful([*gate.SEED, wrapper])
    gate.observe(interpreted, {'exit': 0, 'stdout': expected})
    executable = BUILD / (case['name'] + '-reference')
    built = gate.successful([*gate.SEED, wrapper, '-o', executable])
    native = gate.successful([executable])
    gate.observe(native, {'exit': 0, 'stdout': expected})
    return {'wrapper_sha256': gate.digest(wrapper), 'interpreted': interpreted,
            'build': built, 'native': native}


def compact_audit(observation):
    for row in observation['rounds']:
        raw = row.pop('stdout').encode()
        row.update(stdout_sha256=hashlib.sha256(raw).hexdigest(), stdout_bytes=len(raw))
    return observation


def module(commands, case, lane, setting, expected_abi=None):
    output = BUILD / (case['name'] + '-' + lane + '-' + setting + '.wasm')
    built = gate.compiled(commands['compile'], gate.corpus_path(case), output)
    wat, signatures = gate.decode(output)
    if expected_abi is not None:
        gate.require(signatures == expected_abi, (case['name'], lane, setting, 'ABI changed'))
    calls = gate.tail_calls(wat)
    if setting == 'on' and case['name'] == 'tail-after-local':
        gate.require(calls['tail_self_calls'], 'missing tail call through a local initializer')
    if setting == 'on' and case['name'] in ('nontail-in-initializer', 'nontail-in-constructor', 'nontail-even'):
        gate.require(calls['ordinary_self_calls'] and not calls['tail_self_calls'],
                     (case['name'], 'non-tail self call changed position', calls))
    observations = []
    for call in case['calls']:
        evaluated = gate.run([*commands['eval'], gate.corpus_path(case), call['export'],
                              1048576, *call['arguments']])
        gate.enum_value(evaluated, case, call)
        actual = gate.host(output, call)
        gate.host_value(actual, call)
        observations.append({'call': call, 'evaluator': evaluated, 'wasm': actual})
    if lane == 'bun':
        native = BUILD / (case['name'] + '-native-' + setting + '.wasm')
        gate.require(output.read_bytes() == native.read_bytes(),
                     (case['name'], setting, 'native/Bun bytes differ'))
    return {'build': built, 'sha256': gate.digest(output), 'bytes': output.stat().st_size,
            'abi': signatures, 'self_calls': calls, 'observations': observations}


def main():
    gate.require(os.environ.get('BEND_NO_TELEMETRY') == '1', 'export BEND_NO_TELEMETRY=1')
    BUILD.mkdir(parents=True, exist_ok=True)
    gate.BUILD = BUILD
    gate.ENV.update(BEND_HUB='offline://disabled', BEND_ORIGIN='offline://disabled')
    manifest = json.loads((HERE / 'refresh-cases.json').read_text())
    frozen = json.loads((HERE / manifest['seed_receipt']).read_text())
    cases = [{**case, 'family': 'compiler-opt-refresh', 'key': 'refresh-' + case['name']}
             for case in manifest['cases']]
    paths = [*sorted((ROOT / 'src').glob('*.bend')), *sorted(HERE.glob('*.bend')),
             Path(__file__), HERE / 'check.py', HERE / 'refresh-cases.json',
             HERE / manifest['seed_receipt'], gate.HOST, *[gate.corpus_path(c) for c in cases]]
    inputs = {str(p.relative_to(ROOT)): gate.digest(p) for p in paths}
    record = {'schema': 1, 'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'incomplete', 'profile': 'knot-core-opt-1', 'inputs': inputs,
              'seed_revision': frozen['seed_revision'], 'builds': [], 'fixtures': []}
    try:
        gate.require(len(cases) >= 20 and len({c['name'] for c in cases}) == len(cases),
                     'twenty or more distinct refresh programs required')
        gate.require(frozen['status'] == 'pass' and frozen['programs'] == len(cases)
                     and all(row['passed'] for row in frozen['observations']), 'seed freeze incomplete')
        seed_sources = {row['name']: row['source_sha256'] for row in frozen['observations']}
        for case in cases:
            actual = gate.digest(gate.corpus_path(case))
            gate.require(actual == manifest['source_sha256'][case['file']]
                         == seed_sources[case['name']], ('frozen source changed', case['name']))
            gate.require(len(case['calls']) == 1 and case['calls'][0]['export'] == 'main'
                         and case['calls'][0]['arguments'] == [], 'seed and host domains differ')
            expected = case['constructors'][case['calls'][0]['tag']] + '{}'
            frozen_row = next(row for row in frozen['observations'] if row['name'] == case['name'])
            gate.require(frozen_row['expected'].endswith('.' + expected)
                         and frozen_row['interpreted']['stdout'].strip() == frozen_row['expected']
                         and frozen_row['native']['stdout'].strip() == frozen_row['expected'],
                         ('literal expectation differs from seed freeze', case['name']))
        for name, expected in frozen['seed_hashes'].items():
            gate.require(gate.digest(ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2' / name) == expected,
                         ('pinned seed changed', name))
        record['tools'] = {name: gate.successful([name, '--version'])['stdout'].strip()
                           for name in ('bun', 'node', 'python3', 'wasm2wat')}
        gate.require(record['tools']['node'] == 'v22.22.3', record['tools'])
        # Recheck every seed observation before any optimized probe.
        references = {case['name']: seed(case) for case in cases}
        lanes = gate.build_lanes(record)
        passes = gate.build_pass_lanes(record)
        for case in cases:
            row = {'name': case['name'], 'obligation': case['obligation'],
                   'source_sha256': inputs[case['file']], 'reference': references[case['name']],
                   'lanes': {}}
            record['fixtures'].append(row)
            for lane, commands in lanes.items():
                settings = {
                    'off': {'compile': commands['compile_off'], 'eval': commands['eval_off']},
                    'on': {'compile': commands['compile_on'], 'eval': commands['eval_on']},
                    **passes[lane],
                }
                result = {}
                row['lanes'][lane] = result
                expected_abi = None
                for setting, entry in settings.items():
                    result[setting] = module(entry, case, lane, setting, expected_abi)
                    expected_abi = result['off']['abi']
                observation = gate.audit(commands, case, fixed_point=False)
                if lane == 'bun':
                    # Complete core renderings are compared before compacting evidence.
                    expected = row['lanes']['native']['audit']['rounds']
                    for actual, reference in zip(observation['rounds'], expected):
                        raw = actual['stdout'].encode()
                        gate.require(hashlib.sha256(raw).hexdigest() == reference['stdout_sha256']
                                     and len(raw) == reference['stdout_bytes'],
                                     (case['name'], 'native/Bun checked core differs'))
                result['audit'] = compact_audit(observation)
            print(case['name'] + ': passed', flush=True)
        gate.require(all(gate.digest(ROOT / name) == expected for name, expected in inputs.items()),
                     'inputs changed during refresh probes')
        record['counts'] = {
            'source_programs': len(cases), 'accepted_programs': len(cases), 'execution_lanes': 2,
            'seed_reference_calls': len(cases) * 2, 'abi_decodes': len(cases) * 2 * 5,
            'abi_checks': len(cases) * 2 * 4,
            'evaluator_checks': len(cases) * 2 * 5, 'wasm_calls': len(cases) * 2 * 5,
            'native_bun_byte_checks': len(cases) * 5, 'core_signature_checks': len(cases) * 2,
            'core_round_observations': len(cases) * 2 * 3, 'native_bun_core_checks': len(cases) * 3,
            'tail_position_controls': 4 * 2, 'seed_rejected_programs': 0,
            'false_invalid': 0, 'value_mismatches': 0,
        }
        record['status'] = 'pass'
    finally:
        record = gate.Normalizer(ROOT).value(record)
        RECEIPT.write_bytes(gate.json_bytes(record))
    print(json.dumps({'status': record['status'], 'counts': record['counts'],
                      'receipt': str(RECEIPT.relative_to(ROOT))}, sort_keys=True))


if __name__ == '__main__':
    main()
