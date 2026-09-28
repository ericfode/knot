#!/usr/bin/env python3
"""Replay fixed source observations through the seed, evaluator and owned Wasm."""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/compiler-owned-wasm/gate'
SEED = ['bun', '--no-env-file', ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']
RECEIPT = HERE / 'receipts/owned-wasm.json'


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, timeout=120):
    try:
        result = subprocess.run([str(x) for x in argv], cwd=ROOT, text=True,
                                capture_output=True, timeout=timeout,
                                env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
        return {'argv': [str(x) for x in argv], 'exit': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired:
        return {'argv': [str(x) for x in argv], 'exit': None,
                'outcome': 'Exhausted host-timeout', 'stdout': '', 'stderr': ''}
    except OSError as error:
        return {'argv': [str(x) for x in argv], 'exit': None,
                'outcome': 'HostFailure launch', 'stdout': '', 'stderr': str(error)}


def successful(argv):
    result = run(argv)
    require(result['exit'] == 0, result)
    return result


def diagnostic(result, expected):
    require(result['exit'] == expected['exit'] and
            result['stderr'].startswith(expected['diagnostic']) and not result['stdout'],
            (expected, result))


def compile_module(command, source, output, budgets=()):
    output.unlink(missing_ok=True)
    result = successful([*command, source, output, *budgets])
    require(result['stdout'].strip() == f'Built\t{output.stat().st_size}', result)
    return result


def host(module, label, request):
    path = BUILD / (label + '-request.json')
    path.write_text(json.dumps(request) + '\n')
    result = successful(['node', HERE / 'host.mjs', module, path])
    return {'command': result, 'observation': json.loads(result['stdout'])}


def agrees(observation, call):
    if observation['result']['outcome'] != 'Returned' or 'decoded' not in observation:
        return False
    decoded = observation['decoded']
    return (decoded['tree'] == call['tree'] and decoded['reachable'] == call['live_cells'] and
            decoded['ownership_valid'] and observation['after']['live'] == decoded['reachable'] and
            observation['after']['pending'] == 0 and observation['after']['status'] == 0 and
            observation['cleaned']['live'] == 0 and observation['cleaned']['pending'] == 0 and
            observation['cleaned']['status'] == 0)


def reference(manifest):
    observations = []
    for case in manifest['cases']:
        for index, call in enumerate(case['calls']):
            source = ROOT / case['source']
            if call['export'] == 'main':
                result = successful([*SEED, source])
                expected = case.get('reference', {}).get('stdout', call['tree'])
                actual = result['stdout'].strip().replace(' ', '')
            else:
                wrapper = BUILD / f'{case["name"]}-reference-{index}.bend'
                imported = os.path.relpath(source, wrapper.parent)
                wrapper.write_text(f'import {imported} as F\n\ndef main() -> F.' +
                    case['types'][call['result_type']]['name'] + f':\n  {call["seed"]}\n')
                result = successful([*SEED, wrapper])
                expected = call['tree']
                actual = result['stdout'].strip().replace(imported.removesuffix('.bend') + '.', '').replace(' ', '')
            require(actual == expected.replace(' ', ''), (case['name'], expected, result))
            observations.append({'case': case['name'], 'call': call, 'result': result})
    for case in manifest['negatives']:
        result = run([*SEED, ROOT / case['source'], *case.get('reference_args', [])])
        expected = case['reference']
        require(result['exit'] == expected['exit'], (case['name'], result))
        if 'stdout' in expected:
            require(result['stdout'].strip() == expected['stdout'], (expected, result))
        if 'diagnostic' in expected:
            require(expected['diagnostic'] in result['stderr'], (expected, result))
        observations.append({'case': case['name'], 'result': result})
    return observations


def legacy(lanes, manifest, baseline):
    records = []
    field_cases = {c['name'].removeprefix('fields-'): c for c in manifest['cases'] if c['name'].startswith('fields-')}
    for artifact, expected in baseline['fields'].items():
        case = field_cases[Path(artifact).stem]
        for lane, commands in lanes.items():
            output = BUILD / f'legacy-fields-{case["name"]}-{lane}.wasm'
            built = compile_module(commands['fields'], ROOT / case['source'], output, case.get('compile_budgets', []))
            require(digest(output) == expected, (case['name'], lane, 'fields bytes changed'))
            records.append({'profile': 'fields', 'case': case['name'], 'lane': lane, 'sha256': digest(output), 'compile': built})
    for source, expected in baseline['enum'].items():
        for lane, commands in lanes.items():
            for profile in ('fields', 'enum'):
                output = BUILD / f'legacy-{profile}-{Path(source).stem}-{lane}.wasm'
                built = compile_module(commands[profile], ROOT / source, output)
                require(digest(output) == expected, (source, lane, profile, 'enum bytes changed'))
                records.append({'profile': profile, 'case': source, 'lane': lane, 'sha256': digest(output), 'compile': built})
    return records


def boundaries(lanes, modules, cases, manifest):
    records = []
    for lane, commands in lanes.items():
        for case in json.loads((HERE / 'boundaries.json').read_text())['cases']:
            source = ROOT / case['source']
            require(digest(source) == case['source_sha256'], 'additive boundary source drift')
            seed = successful([*SEED, source])
            require(seed['stdout'].strip() == case['reference']['stdout'], seed)
            evaluated = successful([*commands['eval'], source, 'main', 1048576])
            require(evaluated['stdout'].strip() == case['evaluator']['stdout'], evaluated)
            output = BUILD / f'{case["name"]}-{lane}.wasm'; output.write_bytes(b'stale')
            result = run([*commands['owned'], source, output])
            diagnostic(result, case['compile'])
            require(output.read_bytes() == b'stale', 'reserved export changed artifact')
            records.append({'name': case['name'], 'lane': lane, 'seed': seed, 'evaluator': evaluated, 'compile': result, 'artifact_preserved': True})
        for case in json.loads((HERE / 'exhaustion-cases.json').read_text())['cases']:
            source = ROOT / case['source']
            require(digest(source) == case['source_sha256'], 'exhaustion source drift')
            seed = successful([*SEED, source])
            require(seed['stdout'].strip() == case['reference']['stdout'], seed)
            evaluated = successful([*commands['eval'], source, 'main', 1048576])
            require(evaluated['stdout'].strip() == case['evaluator']['stdout'], evaluated)
            output = BUILD / f'{case["name"]}-{lane}.wasm'
            built = compile_module(commands['owned'], source, output)
            result = run(['node', ROOT / 'scripts/run-wasm.mjs', '--profile=knot-owned-wasm-1', output, 'main'])
            diagnostic(result, case['runtime'])
            records.append({'name': case['name'], 'lane': lane, 'seed': seed, 'evaluator': evaluated, 'compile': built, 'runtime': result})
        pair = modules['fields-pair'][lane]
        for label, name, arguments, status, prefix in [
                ('adapter-success', 'direct', [0, 1], 0, ''),
                ('adapter-invalid-pointer', '__heap_open', [0], 6, 'InternalFailure\twasm\towned-heap'),
                ('adapter-missing-export', 'absent', [], 5, 'HostFailure\twasm\t')]:
            result = run(['node', ROOT / 'scripts/run-wasm.mjs', '--profile=knot-owned-wasm-1', pair, name, *arguments])
            if status:
                diagnostic(result, {'exit': status, 'diagnostic': prefix})
            else:
                require(result['exit'] == 0 and json.loads(result['stdout'])['result'] == 0, result)
            records.append({'name': label, 'lane': lane, 'result': result})
        persistent = manifest['persistent']
        observed = host(modules[persistent['case']][lane], 'persistent-' + lane,
            {'mode': 'persistent', **{key: value for key, value in persistent.items() if key != 'calls'},
             'count': persistent['calls']})
        value = observed['observation']
        require(value.get('completed') == persistent['calls'] and 'failure' not in value, observed)
        require(value['samples'][0]['bump'] == value['final']['bump'], ('storage not reused', observed))
        records.append({'name': 'persistent-reuse', 'lane': lane, **observed})
        reuse = manifest['reuse']
        observed = host(modules[reuse['case']][lane], 'recursive-reuse-' + lane,
            {'mode': 'persistent', 'export': reuse['export'], 'arguments': [], 'tag': 1, 'count': reuse['persistent_calls']})
        value = observed['observation']
        require(value.get('completed') == reuse['persistent_calls'] and 'failure' not in value, observed)
        require(value['final']['allocations'] >= reuse['minimum_lifetime_allocations'] * reuse['persistent_calls'], observed)
        require(value['final']['memory_bytes'] <= reuse['maximum_memory_bytes'], observed)
        require(value['samples'][0]['bump'] == value['final']['bump'], ('recursive storage not bounded', observed))
        records.append({'name': 'recursive-reuse', 'lane': lane, **observed})
        case = cases[reuse['case']]
        arena = BUILD / f'reuse-arena-{lane}.wasm'
        compiled = compile_module(commands['fields'], ROOT / case['source'], arena)
        result = run(['node', ROOT / 'scripts/run-wasm.mjs', '--profile=knot-fields-wasm-1', arena, reuse['export']])
        diagnostic(result, case['arena_expected'])
        records.append({'name': 'arena-exhaustion-control', 'lane': lane, 'result': result, 'compile': compiled, 'sha256': digest(arena)})
        case = cases[manifest['release']['case']]
        call = case['calls'][0]
        observed = host(modules[case['name']][lane], 'release-boundary-' + lane,
            {'mode': 'release-boundary', 'export': call['export'], 'result_type': call['result_type'], 'types': case['types']})
        value = observed['observation']; steps = value['steps']
        require(value['initial']['live'] == manifest['release']['cells'] and value['decoded']['ownership_valid'], observed)
        require(steps[1]['state']['live'] == value['initial']['live'] and steps[1]['state']['pending'] == 1, observed)
        for key in ('live', 'allocations', 'pending', 'bump'):
            require(steps[2]['state'][key] == steps[1]['state'][key], ('zero budget lost work', key, observed))
        require(all(steps[i]['result'] == {'outcome': 'Returned', 'value': 3} for i in (2, 3, 4)), observed)
        require(steps[4]['state']['live'] == manifest['release']['cells'] and steps[4]['state']['pending'] == 1, observed)
        require(steps[6]['result'] == {'outcome': 'Returned', 'value': 0} and
                steps[6]['state']['live'] == 0 and steps[6]['state']['pending'] == 0, observed)
        records.append({'name': 'resumable-release-stack', 'lane': lane, **observed})
        case = cases['share-live']; call = case['calls'][0]
        observed = host(modules[case['name']][lane], 'count-boundary-' + lane,
            {'mode': 'count-boundary', 'export': call['export'], 'result_type': call['result_type'], 'types': case['types']})
        value = observed['observation']
        require(value['share']['outcome'] == 'Exhausted' and value['share']['status'] == 3, observed)
        require(value['initial'] == value['after'], ('count overflow modified existing owners', observed))
        require(value['before']['live'] == value['state']['live'] and value['final']['live'] == 0 and value['final']['pending'] == 0, observed)
        records.append({'name': 'count-overflow-preserves-owner', 'lane': lane, **observed})
        for label, budgets in [('emitter-depth', [65536, 512, 512, 0, 65536]),
                              ('output-capacity', [65536, 512, 512, 4096, 32])]:
            output = BUILD / f'{label}-{lane}.wasm'; output.write_bytes(b'stale')
            result = run([*commands['owned'], ROOT / cases['fields-pair']['source'], output, *budgets])
            require(result['exit'] == 4 and result['stderr'].startswith('Exhausted\temit\t') and not result['stdout'], result)
            require(output.read_bytes() == b'stale', (label, 'artifact changed'))
            records.append({'name': label, 'lane': lane, 'result': result, 'artifact_preserved': True})
    return records


def extended_evaluator_values(cases):
    observations = []
    controls = json.loads((HERE / 'evaluator-extensions.json').read_text())
    for control in controls['cases']:
        source = ROOT / control['source']
        require(digest(source) == control['source_sha256'], 'extended evaluator fixture drift')
        limits = control['input_limits']
        require([limits['characters'], limits['parser'], limits['checker']] ==
                cases[control['fixture']]['compile_budgets'][:3], 'extended limits differ from frozen compile limits')
        require(cases[control['fixture']]['calls'][0]['tree'] == control['seed_value'], 'extended result differs from seed freeze')
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun', '--no-env-file'])]:
            executable = BUILD / (control['name'] + suffix)
            built = successful([*SEED, ROOT / control['entry'], '-o', executable])
            result = successful([*runtime, executable])
            require(result['exit'] == control['expected']['exit'] and
                    result['stdout'].strip() == control['expected']['stdout'], (control, result))
            observations.append({'name': control['name'], 'fixture': control['fixture'], 'lane': lane,
                'input_limits': limits, 'transition_budget': control['transition_budget'],
                'entry': control['entry'], 'build': built, 'sha256': digest(executable), 'result': result})
    require(len(observations) == 2, 'two extended evaluator value agreements')
    return observations


def runtime_components():
    records = []
    first = None
    for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun', '--no-env-file'])]:
        outputs, builds = {}, []
        for phase, extension in [('runtime-compile', 'json'), ('runtime-oracle', 'txt')]:
            executable = BUILD / (phase + suffix)
            built = successful([*SEED, HERE / (phase + '.bend'), '-o', executable])
            ran = successful([*runtime, executable])
            output = BUILD / (phase + '-' + lane + '.' + extension)
            output.write_text(ran['stdout'])
            outputs[phase] = output
            builds.append({'phase': phase, 'build': built, 'run': ran, 'sha256': digest(output)})
        result = successful(['node', HERE / 'runtime-check.mjs', outputs['runtime-compile'], outputs['runtime-oracle']])
        counts = json.loads(result['stdout'])
        expected = {'status': 'pass', 'allocator_observations': 12, 'runtime_witnesses': 10, 'memory_bytes': 131072, 'maximum_chain_cells': 3277}
        require(all(counts.get(key) == value for key, value in expected.items()), counts)
        bytes_ = json.loads(outputs['runtime-compile'].read_text())
        if first is None:
            first = bytes_
        else:
            require(first == bytes_, 'runtime component compiler lanes differ')
        records.append({'lane': lane, 'builds': builds, 'result': result, 'counts': counts})
    return records


def mutants(cases):
    records = []
    manifest = json.loads((HERE / 'mutants.json').read_text())
    require(len(manifest) == 5, 'five required semantic mutants')
    for mutation in manifest:
        name = mutation['name']; directory = BUILD / name; directory.mkdir(exist_ok=True)
        for source in (ROOT / 'src').glob('*.bend'):
            shutil.copy2(source, directory / source.name)
        target = directory / mutation['file']; source = target.read_text()
        require(source.count(mutation['old']) == 1, (name, 'mutation must be unique'))
        target.write_text(source.replace(mutation['old'], mutation['new']))
        entry = directory / 'entry.bend'
        entry.write_text((HERE / 'compile.bend').read_text().replace('../../src/', './'))
        checked = successful([*SEED, entry, '--check-only'])
        require(checked['stdout'].strip() == 'All terms check.', checked)
        case = cases[mutation['case']]
        calls = [call for call in case['calls'] if call['export'] == mutation.get('export', 'main')]
        require(len(calls) == 1, (name, 'literal witness'))
        item = {**mutation, 'sha256': digest(target), 'typecheck': checked, 'lanes': {}}
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun', '--no-env-file'])]:
            executable = directory / ('mutant' + suffix)
            built = successful([*SEED, entry, '-o', executable])
            output = directory / (lane + '.wasm')
            emission = compile_module([*runtime, executable], ROOT / case['source'], output)
            successful(['wasm2wat', '--enable-tail-call', output])
            if mutation.get('mode') == 'release-boundary':
                observed = host(output, name + '-' + lane, {'mode': 'release-boundary', 'export': calls[0]['export'], 'result_type': calls[0]['result_type'], 'types': case['types']})
                actual = observed['observation']['steps'][4]
                killed = actual['result'] != {'outcome': 'Returned', 'value': 3} or actual['state']['live'] != calls[0]['live_cells'] or actual['state']['pending'] != 1
            else:
                observed = host(output, name + '-' + lane, {'mode': 'observe', 'types': case['types'], 'calls': calls})
                killed = not agrees(observed['observation']['observations'][0], calls[0])
            require(killed, (name, lane, 'mutant survived', observed))
            item['lanes'][lane] = {'build': built, 'emission': emission, **observed, 'outcome': 'semantic-kill'}
        records.append(item)
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference-only', action='store_true')
    parser.add_argument('--no-mutants', action='store_true', help='iteration only; never a full pass')
    args = parser.parse_args()
    require(os.environ.get('BEND_NO_TELEMETRY') == '1', 'export BEND_NO_TELEMETRY=1')
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(exist_ok=True)
    manifest = json.loads((HERE / 'cases.json').read_text())
    frozen = json.loads((HERE / 'expectations.json').read_text())
    require(all(digest(ROOT / path) == expected for path, expected in frozen['inputs'].items()), 'D7 frozen inputs changed')
    if args.reference_only:
        observations = reference(manifest)
        print(f"Owned reference replay passed: {len(observations)} observations")
        return
    additions = json.loads((HERE / 'review-cases.json').read_text())['cases']
    require(all(digest(ROOT / case['source']) == case['source_sha256'] for case in additions), 'review fixture drift')
    manifest['cases'] += additions
    cases = {case['name']: case for case in manifest['cases']}
    paths = [*sorted((ROOT / 'src').glob('*.bend')), *sorted(HERE.glob('*.bend')),
        *sorted(HERE.glob('*.json')), *sorted(HERE.glob('*.mjs')), *sorted((HERE / 'fixtures').glob('*.bend')),
        ROOT / 'scripts/run-wasm.mjs', Path(__file__), HERE / 'SPEC.md',
        *[ROOT / c['source'] for c in manifest['cases'] + manifest['negatives']]]
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
        'profile': manifest['profile'], 'seed_revision': manifest['seed_revision'],
        'inputs': {str(path.relative_to(ROOT)): digest(path) for path in paths},
        'expectation_freeze_sha256': digest(HERE / 'expectations.json')}
    try:
        record['seed_inputs'] = {name: digest(ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2' / name)
                                for name in ('main.ts', 'bend.ts', 'comp.ts', 'base.bend')}
        record['tools'] = {tool: successful([tool, '--version'])['stdout'].strip()
                           for tool in ('bun', 'node', 'python3', 'wasm2wat')}
        require(record['tools']['node'] == 'v22.22.3', record['tools'])
        record['proofs'] = []
        for path in (ROOT / 'src/heap-PROOF.bend', ROOT / 'src/ownership-PROOF.bend', HERE / 'model-PROOF.bend'):
            if path.exists():
                result = successful([*SEED, path])
                require(result['stdout'].strip() == 'All terms check.', result)
                record['proofs'].append({'entry': str(path.relative_to(ROOT)), 'result': result})
        require({item['entry'] for item in record['proofs']} == {
            'src/heap-PROOF.bend', 'src/ownership-PROOF.bend',
            'tests/compiler-owned-wasm/model-PROOF.bend'}, 'missing complete proof entry')
        record['runtime_components'] = runtime_components()
        record['reference'] = reference(manifest)
        print(f"Owned seed: {len(record['reference'])} observations", flush=True)
        record['builds'], lanes = [], {}
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun', '--no-env-file'])]:
            lanes[lane] = {}
            for phase, entry in [('owned', HERE / 'compile.bend'), ('eval', ROOT / 'src/eval-cli.bend'),
                    ('fields', ROOT / 'tests/compiler-fields-wasm/compile.bend'), ('enum', ROOT / 'src/compile-cli.bend')]:
                output = BUILD / (phase + suffix)
                built = successful([*SEED, entry, '-o', output])
                record['builds'].append({'lane': lane, 'phase': phase, 'result': built, 'sha256': digest(output)})
                lanes[lane][phase] = [*runtime, output]
        record['legacy'] = legacy(lanes, manifest, json.loads((HERE / 'legacy-baseline.json').read_text()))
        print(f"Owned legacy: {len(record['legacy'])} byte checks", flush=True)
        record['fixtures'], modules = [], {}
        for case in manifest['cases']:
            item = {'name': case['name'], 'lanes': {}}; modules[case['name']] = {}
            for lane, commands in lanes.items():
                output = BUILD / f'{case["name"]}-{lane}.wasm'
                built = compile_module(commands['owned'], ROOT / case['source'], output, case.get('compile_budgets', []))
                modules[case['name']][lane] = output
                decoded = successful(['wasm2wat', '--enable-tail-call', output])
                evaluated = []
                for call in case['calls']:
                    result = run([*commands['eval'], ROOT / case['source'], call['export'], 1048576, *call['arguments']])
                    if 'eval_exhausted' in case:
                        diagnostic(result, {'exit': 4, 'diagnostic': case['eval_exhausted']})
                    else:
                        expected = f'Evaluated\t{call["result_type"]}\t{call["tag"]}\t{call["tree"]}'
                        require(result['exit'] == 0 and result['stdout'].strip() == expected, (expected, result))
                    evaluated.append({'call': call, 'result': result})
                observed = host(output, case['name'] + '-' + lane, {'mode': 'observe', 'types': case['types'], 'calls': case['calls']})
                values = observed['observation']['observations']
                require(len(values) == len(case['calls']) and all(agrees(value, call) for value, call in zip(values, case['calls'])), (case['name'], observed))
                if lane == 'bun':
                    require(output.read_bytes() == modules[case['name']]['native'].read_bytes(), ('compiler lanes differ', case['name']))
                item['lanes'][lane] = {'compile': built, 'sha256': digest(output), 'bytes': output.stat().st_size,
                    'decode_exit': decoded['exit'], 'evaluator': evaluated, **observed}
            record['fixtures'].append(item)
            print('Owned fixture:', case['name'], '2 lanes passed', flush=True)
        record['extended_evaluator_values'] = extended_evaluator_values(cases)
        record['negatives'] = []
        for case in manifest['negatives']:
            for lane, commands in lanes.items():
                output = BUILD / f'{case["name"]}-{lane}.wasm'; output.write_bytes(b'preserved')
                result = run([*commands['owned'], ROOT / case['source'], output])
                diagnostic(result, case['expected'])
                require(output.read_bytes() == b'preserved', (case['name'], 'rejection changed artifact'))
                evaluated = run([*commands['eval'], ROOT / case['source'], 'main', 1048576])
                diagnostic(evaluated, case['expected'])
                record['negatives'].append({'name': case['name'], 'lane': lane, 'compile': result, 'eval': evaluated, 'artifact_preserved': True})
        record['boundaries'] = boundaries(lanes, modules, cases, manifest)
        record['mutants'] = [] if args.no_mutants else mutants(cases)
        require(all(digest(ROOT / path) == expected for path, expected in record['inputs'].items()), 'inputs changed during gate')
        record['counts'] = {'positive_fixtures': len(cases), 'seed_observations': len(record['reference']),
            'evaluator_observations': 2 * sum(len(case['calls']) for case in cases.values()),
            'extended_evaluator_values': len(record['extended_evaluator_values']),
            'wasm_observations': 2 * sum(len(case['calls']) for case in cases.values()),
            'compiler_lane_byte_agreements': len(cases), 'legacy_byte_checks': len(record['legacy']),
            'negative_pairs': len(record['negatives']), 'boundary_probes': len(record['boundaries']),
            'semantic_mutants': len(record['mutants']), 'mutant_lane_kills': 2 * len(record['mutants']),
            'allocator_state_comparisons': sum(item['counts']['allocator_observations'] for item in record['runtime_components']),
            'runtime_component_witnesses': sum(item['counts']['runtime_witnesses'] for item in record['runtime_components']),
            'checked_laws': 43}
        record['status'] = 'partial-iteration' if args.no_mutants else 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print('Owned Wasm gate ' + record['status'] + ': ' + json.dumps(record['counts'], sort_keys=True) + f'. {RECEIPT}')


if __name__ == '__main__':
    main()
