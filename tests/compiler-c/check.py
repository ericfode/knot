#!/usr/bin/env python3
"""Compare fixed source observations across seed, evaluator, Wasm and native C."""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/compiler-c/gate'
SEED = ['bun', '--no-env-file', ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']
HOST = ROOT / 'scripts/run-wasm.mjs'
PROFILE = '--profile=knot-fields-wasm-1'
CC_FLAGS = ['-O2', '-std=c99', '-Wall', '-Werror', '-fwrapv']
FREEZE = HERE / 'receipts/reference.json'
RECEIPT = HERE / 'receipts/c.json'


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, timeout=120, extra_env=None):
    env = {**os.environ, 'BEND_NO_TELEMETRY': '1', **(extra_env or {})}
    try:
        result = subprocess.run([str(x) for x in argv], cwd=ROOT, text=True,
                                capture_output=True, timeout=timeout, env=env)
        return {'argv': [str(x) for x in argv], 'exit': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired:
        return {'argv': [str(x) for x in argv], 'exit': None,
                'outcome': 'harness-timeout', 'stdout': '', 'stderr': ''}


def successful(argv, **kwargs):
    result = run(argv, **kwargs)
    require(result['exit'] == 0, result)
    return result


def diagnostic(result, status, prefix):
    require(result['exit'] == status and result['stderr'].startswith(prefix)
            and result['stdout'] == '', (prefix, result))


def observe(result, expected):
    require(result['exit'] == expected['exit'], (expected, result))
    if 'stdout' in expected:
        require(result['stdout'].strip() == expected['stdout'], (expected, result))
    if 'contains' in expected:
        require(expected['contains'] in result['stdout'], (expected, result))
    if 'diagnostic' in expected:
        require(expected['diagnostic'] in result['stderr'] and not result['stdout'], (expected, result))


def fixed_inputs(manifest):
    paths = {HERE / 'cases.json', ROOT / manifest['recursion_originals']}
    for suite in ('compiler-wasm', 'compiler-fields-wasm', 'compiler-recursion'):
        paths.add(ROOT / 'tests' / suite / 'cases.json')
    for case in [*manifest['cases'], *manifest['rejections']]:
        paths.add(ROOT / case['file'])
        if 'original_file' in case:
            original = ROOT / case['original_file']
            paths.add(original)
            require((ROOT / case['file']).read_bytes()[:case['original_prefix_bytes']] == original.read_bytes(),
                    ('recursion source prefix changed', case['name']))
    return {str(path.relative_to(ROOT)): digest(path) for path in sorted(paths)}


def reference(manifest):
    observations = []
    for case in manifest['cases']:
        for index, call in enumerate(case['calls']):
            wrapper = BUILD / f'{case["name"]}-reference-{index}.bend'
            imported = os.path.relpath(ROOT / case['file'], wrapper.parent)
            wrapper.write_text(f'import {imported} as F\n\ndef main() -> F.{case["type"]}:\n  {call["seed"]}\n')
            actual = successful([*SEED, wrapper])
            expected = imported.removesuffix('.bend') + '.' + case['constructors'][call['tag']] + '{}'
            require(actual['stdout'].strip() == expected, (case['name'], call, expected, actual))
            observations.append({'case': case['name'], 'call': call, 'source_sha256': digest(ROOT / case['file']), 'result': actual})
    originals = json.loads((ROOT / manifest['recursion_originals']).read_text())
    original_observations = []
    for case in originals['cases']:
        source = ROOT / 'tests/compiler-recursion' / case['file']
        actual = run([*SEED, source, *case.get('reference_args', [])])
        observe(actual, case['reference'])
        original_observations.append({'case': case['name'], 'result': actual})
    return observations, original_observations


def compiled(command, source, output, budgets=()):
    output.unlink(missing_ok=True)
    result = successful([*command, source, output, *budgets])
    require(output.is_file() and result['stdout'].strip() == f'Built\t{output.stat().st_size}', result)
    return result


def c_binary(source, output, extra=()):
    return successful(['cc', *CC_FLAGS, f'-DKNOT_SOURCE_BYTES={source.stat().st_size}',
                       *extra, source, '-o', output])


def json_value(result, call, size):
    require(result['exit'] == 0 and result['stderr'] == '', result)
    require(json.loads(result['stdout']) == {'validated': True, 'export': call['export'],
            'arguments': call['arguments'], 'result': call['tag'], 'bytes': size}, (call, result))


def evaluator_value(result, case, call):
    if 'eval_exhausted' in case:
        diagnostic(result, 4, case['eval_exhausted'])
    else:
        expected = f'Evaluated\t{case["type_id"]}\t{call["tag"]}\t{case["constructors"][call["tag"]]}{{}}'
        require(result['exit'] == 0 and result['stdout'].strip() == expected and result['stderr'] == '',
                (expected, result))


def corpus(manifest, lanes, record):
    artifacts = {}
    for case in manifest['cases']:
        source = ROOT / case['file']
        name = case['name']
        print(f'[compiler-c] corpus {name}', file=sys.stderr, flush=True)
        item = {'name': name, 'file': case['file'], 'lanes': {}}
        artifacts[name] = {}
        for lane, commands in lanes.items():
            c_source = BUILD / f'{name}-{lane}.c'
            wasm = BUILD / f'{name}-{lane}.wasm'
            binary = BUILD / f'{name}-{lane}'
            emitted_c = compiled(commands['c'], source, c_source, case.get('compile_budgets', []))
            emitted_wasm = compiled(commands['wasm'], source, wasm, case.get('compile_budgets', []))
            native = c_binary(c_source, binary)
            observations = []
            for call in case['calls']:
                evaluated = run([*commands['eval'], source, call['export'], 1048576, *call['arguments']])
                evaluator_value(evaluated, case, call)
                executed_wasm = run(['node', HOST, PROFILE, wasm, call['export'], *call['arguments']])
                if 'wasm_exhausted' in case:
                    diagnostic(executed_wasm, 4, case['wasm_exhausted'])
                else:
                    json_value(executed_wasm, call, wasm.stat().st_size)
                executed_c = run([binary, call['export'], *call['arguments']])
                if 'c_exhausted' in case:
                    diagnostic(executed_c, 4, case['c_exhausted'])
                else:
                    json_value(executed_c, call, c_source.stat().st_size)
                observations.append({'call': call, 'evaluator': evaluated, 'wasm': executed_wasm, 'c': executed_c})
            item['lanes'][lane] = {'c_emission': emitted_c, 'wasm_emission': emitted_wasm,
                    'cc': native, 'c_sha256': digest(c_source), 'wasm_sha256': digest(wasm),
                    'observations': observations}
            artifacts[name][lane] = {'source': c_source, 'wasm': wasm, 'binary': binary}
            if lane == 'bun':
                require(c_source.read_bytes() == artifacts[name]['native']['source'].read_bytes(),
                        (name, 'native/Bun C bytes differ'))
                require(wasm.read_bytes() == artifacts[name]['native']['wasm'].read_bytes(),
                        (name, 'native/Bun Wasm bytes differ'))
        c_source = artifacts[name]['native']['source']
        sanitized = BUILD / f'{name}-sanitized'
        instrumented = c_binary(c_source, sanitized,
                ['-fsanitize=address,undefined', '-fno-omit-frame-pointer'])
        sanitized_observations = []
        for call in case['calls']:
            actual = run([sanitized, call['export'], *call['arguments']],
                    extra_env={'ASAN_OPTIONS': 'detect_leaks=0:halt_on_error=1',
                               'UBSAN_OPTIONS': 'halt_on_error=1:print_stacktrace=1'})
            if 'c_exhausted' in case:
                diagnostic(actual, 4, case['c_exhausted'])
                require(actual['stderr'].strip() == case['c_exhausted'], actual)
            else:
                json_value(actual, call, c_source.stat().st_size)
            sanitized_observations.append({'call': call, 'result': actual})
        item['sanitizer'] = {'cc': instrumented, 'observations': sanitized_observations}
        record['fixtures'].append(item)
    return artifacts


def original_recursion(manifest, lanes, record):
    originals = json.loads((ROOT / manifest['recursion_originals']).read_text())
    for case in originals['cases']:
        source = ROOT / 'tests/compiler-recursion' / case['file']
        item = {'case': case['name'], 'lanes': {}}
        for lane, commands in lanes.items():
            checked = run([*commands['check'], source]); observe(checked, case['check'])
            evaluated = run([*commands['eval'], source, 'main', 65536]); observe(evaluated, case['eval'])
            row = {'check': checked, 'eval': evaluated}
            if case['check']['exit'] == 0:
                output = BUILD / f'original-{case["name"]}-{lane}.c'
                row['emission'] = compiled(commands['c'], source, output)
                row['c_sha256'] = digest(output)
                row['cc'] = c_binary(output, output.with_suffix(''))
                if lane == 'bun':
                    require(output.read_bytes() == (BUILD / f'original-{case["name"]}-native.c').read_bytes(),
                            (case['name'], 'original recursion C bytes differ'))
            item['lanes'][lane] = row
        record['recursion_originals'].append(item)


def rejections(manifest, lanes, record):
    cases = list(manifest['rejections'])
    old = json.loads((ROOT / manifest['checker_rejections']).read_text())
    cases += [{'name': Path(case['file']).stem, 'file': case['file'], 'check': case['knot']}
              for case in old['cases'] if case['knot']['exit'] != 0]
    for case in cases:
        for lane, commands in lanes.items():
            item = {'case': case['name'], 'file': case['file'], 'lane': lane}
            for phase, suffix in [('c', '.c'), ('wasm', '.wasm')]:
                output = BUILD / f'rejected-{lane}{suffix}'
                output.write_bytes(b'existing artifact\n')
                actual = run([*commands[phase], ROOT / case['file'], output])
                observe(actual, case['check'])
                require(output.read_bytes() == b'existing artifact\n', ('rejection changed output', actual))
                item[phase] = actual
            evaluated = run([*commands['eval'], ROOT / case['file'], 'main', 65536])
            observe(evaluated, case['check'])
            item['evaluator'] = evaluated
            item['artifact_preserved'] = True
            record['rejects'].append(item)


def arena_harness(source, output, export, count, tag, arguments):
    harness = output.with_suffix('.c')
    raw = ','.join(str(arg) for arg in arguments) or '0'
    harness.write_text('#define KNOT_NO_MAIN\n#include ' + json.dumps(str(source)) + '\n'
            'int main(void) {\n  uint32_t args[] = {' + raw + '};\n  knot_reset();\n'
            f'  for (size_t i = 0; i < {count}; ++i) {{\n'
            f'    if (knot_invoke({json.dumps(export)}, {len(arguments)}, args) != {tag}) return 9;\n'
            '  }\n'
            f'  printf("Boundary\\t{count}\\n");\n  fflush(stdout);\n'
            f'  (void)knot_invoke({json.dumps(export)}, {len(arguments)}, args);\n'
            '  return 0;\n}\n')
    built = c_binary(harness, output, ['-fsanitize=address,undefined', '-fno-omit-frame-pointer'])
    return built


def boundaries(manifest, lanes, artifacts, record):
    cases = {case['name']: case for case in manifest['cases']}
    for name, export, count, tag, args in [('fields-wasm-arena-overflow', 'f0', 8192, 1, []),
            ('fields-wasm-erased', 'ghost', 16384, 1, []), ('fields-wasm-erased', 'empty', 16384, 0, []),
            ('fields-wasm-pair', 'direct', 5461, 0, [0, 1])]:
        output = BUILD / f'arena-{export}'
        built = arena_harness(artifacts[name]['native']['source'], output, export, count, tag, args)
        actual = run([output])
        require(actual['exit'] == 4 and actual['stdout'] == f'Boundary\t{count}\n'
                and actual['stderr'].strip() == 'Exhausted\tc\tarena-overflow', actual)
        record['boundaries'].append({'name': 'arena-' + export, 'cc': built, 'successful_calls': count,
                'overflow_call': count + 1, 'result': actual, 'sanitized': True})
    for name, limit, status, tag in [('deep-recursion', 32, 4, 0), ('recursion-deep', 8, 0, 1)]:
        output = BUILD / f'depth-{name}'
        source = artifacts[name]['native']['source']
        built = c_binary(source, output, [f'-DKNOT_DEPTH_LIMIT={limit}',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer'])
        call = cases[name]['calls'][0]
        actual = run([output, call['export'], *call['arguments']])
        if status:
            diagnostic(actual, status, 'Exhausted\tc\tcall-stack')
            require(actual['stderr'].strip() == 'Exhausted\tc\tcall-stack', actual)
        else:
            json_value(actual, call, source.stat().st_size)
        record['boundaries'].append({'name': 'depth-' + name, 'depth_limit': limit,
                'cc': built, 'result': actual, 'sanitized': True})
    for lane, commands in lanes.items():
        flag = ROOT / cases['wasm-flag']['file']
        for name, budgets, phase in [('characters', [0, 512, 512, 4096, 1048576], 'lex'),
                ('parser', [65536, 0, 512, 4096, 1048576], 'parse'),
                ('checker', [65536, 512, 0, 4096, 1048576], 'check'),
                ('emitter', [65536, 512, 512, 0, 1048576], 'emit'),
                ('capacity', [65536, 512, 512, 4096, 32], 'emit')]:
            output = BUILD / f'budget-{lane}.c'; output.write_bytes(b'existing artifact\n')
            actual = run([*commands['c'], flag, output, *budgets])
            diagnostic(actual, 4, f'Exhausted\t{phase}\t')
            require(output.read_bytes() == b'existing artifact\n', ('budget changed output', actual))
            record['boundaries'].append({'name': name, 'lane': lane, 'result': actual, 'artifact_preserved': True})
        binary = artifacts['fields-wasm-pair'][lane]['binary']
        for name, args in [('missing-export', ['absent']), ('wrong-arity', ['direct', 0]),
                ('enum-domain', ['direct', 2, 0]), ('negative-ordinal', ['direct', '-1', 0]),
                ('nonnumeric-ordinal', ['direct', 'x', 0]), ('leading-zero', ['direct', '00', 0]),
                ('structured-export', ['first', 0])]:
            actual = run([binary, *args])
            diagnostic(actual, 5, 'HostFailure\tc\t')
            record['host_boundaries'].append({'name': name, 'lane': lane, 'result': actual})


def adapter_probes(artifacts, record):
    manifest = json.loads((HERE / 'host-expectations.json').read_text())
    pair = artifacts['fields-wasm-pair']['native']['source']
    absent = BUILD / 'absent.c'; absent.unlink(missing_ok=True)
    malformed = BUILD / 'malformed.c'; malformed.write_text('not C\n')
    sources = {'pair': pair, 'absent': absent, 'malformed': malformed}
    for case in manifest['cases']:
        source = sources[case['source']]
        actual = run(['python3', ROOT / 'scripts/run-c.py', source, case['export'], *case['arguments']])
        if case['exit'] == 0:
            json_value(actual, {'export': case['export'], 'arguments': case['arguments'],
                               'tag': case['result']}, source.stat().st_size)
        else:
            diagnostic(actual, case['exit'], case['diagnostic'])
        record['host_boundaries'].append({'name': case['name'], 'result': actual})


MUTANTS = [
    ('swapped-field-offset',
     'String.concat([pointer,"[",U32.show(offset),"]",projection(context,type_id)])',
     'String.concat([pointer,"[",U32.show(Bool.pick(U32,U32.is_eq(offset,1),2,1)),"]",projection(context,type_id)])',
     'fields-wasm-pair', 'direct', [0, 1], 0),
    ('missing-arena-bound',
     'if (size > KNOT_ARENA_SLOTS - knot_bump)', 'if (0)',
     'fields-wasm-pair', None, [], None),
    ('wrong-tag-compare',
     'value," == ",U32.show(tag)', 'value," != ",U32.show(tag)',
     'wasm-flag', 'flip', [0], 1),
    ('tail-skips-rebind',
     r'String.concat([parameter(level)," = ",name,";\n",rest])',
     r'String.concat([Bool.pick(String,U32.is_eq(level,1),"",String.concat([parameter(level)," = ",name,";\n"])),rest])',
     'tail-rebind', 'odd', [0, 1], 1),
]


def bound_harness(source, output):
    harness = output.with_suffix('.c')
    harness.write_text('#define KNOT_NO_MAIN\n#include ' + json.dumps(str(source)) + '\n'
            'int main(void) {\n  knot_reset();\n'
            '  (void)knot_alloc(KNOT_ARENA_SLOTS);\n  (void)knot_alloc(1);\n  return 0;\n}\n')
    # The missing guard returns a legal one-past pointer; this probe never
    # dereferences it. A semantic exit-code mismatch kills it without invoking UB.
    return c_binary(harness, output, ['-fsanitize=address,undefined', '-fno-omit-frame-pointer'])


def mutants(manifest, record):
    cases = {case['name']: case for case in manifest['cases']}
    control = BUILD / 'bound-control'
    control_build = bound_harness(BUILD / 'fields-wasm-pair-native.c', control)
    control_result = run([control])
    diagnostic(control_result, 4, 'Exhausted\tc\tarena-overflow')
    require(control_result['stderr'].strip() == 'Exhausted\tc\tarena-overflow', control_result)
    record['boundaries'].append({'name': 'allocator-exact-bound', 'cc': control_build,
            'result': control_result, 'sanitized': True})
    for name, old, new, witness, export, arguments, tag in MUTANTS:
        print(f'[compiler-c] mutant {name}', file=sys.stderr, flush=True)
        directory = BUILD / name; directory.mkdir(exist_ok=True)
        for source in (ROOT / 'src').glob('*.bend'):
            shutil.copy2(source, directory / source.name)
        target = directory / 'c.bend'; source = target.read_text()
        require(source.count(old) == 1, (name, 'mutation must be unique', source.count(old)))
        target.write_text(source.replace(old, new))
        entry = directory / 'entry.bend'
        entry.write_text((HERE / 'compile.bend').read_text().replace('../../src/', './'))
        checked = successful([*SEED, entry, '--check-only'])
        require(checked['stdout'].strip() == 'All terms check.', checked)
        item = {'name': name, 'old': old, 'new': new, 'source_sha256': digest(target),
                'typecheck': checked, 'witness': witness, 'export': export,
                'arguments': arguments, 'expected_tag': tag, 'lanes': {}}
        if export is not None:
            require(any(call['export'] == export and call['arguments'] == arguments and call['tag'] == tag
                        for call in cases[witness]['calls']), 'Mutant observation must be frozen')
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun', '--no-env-file'])]:
            compiler = directory / ('compile' + suffix)
            built = successful([*SEED, entry, '-o', compiler])
            output = directory / f'{lane}.c'
            emitted = compiled([*runtime, compiler], ROOT / cases[witness]['file'], output)
            binary = directory / lane
            if export is None:
                native = bound_harness(output, directory / (lane + '-bound'))
                actual = run([directory / (lane + '-bound')])
                require(actual['exit'] == 0 and actual['stdout'] == '' and actual['stderr'] == '', actual)
            else:
                native = c_binary(output, binary, ['-fsanitize=address,undefined', '-fno-omit-frame-pointer'])
                actual = successful([binary, export, *arguments])
                require(actual['stderr'] == '', actual)
                answer = json.loads(actual['stdout'])
                require(answer['result'] != tag and answer['result'] in range(len(cases[witness]['constructors'])),
                        (name, 'mutant survived or left result domain', answer))
            item['lanes'][lane] = {'build': built, 'emission': emitted, 'cc': native,
                    'actual': actual, 'outcome': 'semantic-kill'}
            if lane == 'bun':
                require(output.read_bytes() == (directory / 'native.c').read_bytes(),
                        (name, 'mutant native/Bun C bytes differ'))
        record['mutants'].append(item)


def execute(manifest, fixed):
    frozen = json.loads(FREEZE.read_text())
    require(frozen['status'] == 'passed' and frozen['frozen_inputs'] == fixed,
            'Expectations changed since the preimplementation seed freeze')
    paths = [*sorted((ROOT / 'src').glob('*.bend')), ROOT / 'src/SPEC.md', ROOT / 'src/CONTRACT.json',
             HOST, HERE / 'compile.bend', Path(__file__), *[ROOT / name for name in fixed],
             ROOT / manifest['checker_rejections'], ROOT / 'scripts/run-c.py', HERE / 'host-expectations.json']
    old = json.loads((ROOT / manifest['checker_rejections']).read_text())
    paths += [ROOT / case['file'] for case in old['cases'] if case['knot']['exit'] != 0]
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
              'profile': manifest['profile'], 'seed_revision': manifest['seed_revision'],
              'inputs': {str(path.relative_to(ROOT)): digest(path) for path in sorted(set(paths))},
              'expectation_freeze_sha256': digest(FREEZE), 'cc_flags': CC_FLAGS,
              'fixtures': [], 'recursion_originals': [], 'rejects': [], 'boundaries': [],
              'host_boundaries': [], 'mutants': []}
    try:
        record['tools'] = {tool: successful([tool, '--version'])['stdout'].strip()
                           for tool in ('bun', 'node', 'python3', 'cc')}
        require(record['tools']['node'] == 'v22.22.3', record['tools'])
        record['seed_inputs'] = {name: digest(ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2' / name)
                                for name in ('main.ts', 'bend.ts', 'comp.ts', 'base.bend')}
        record['checked_laws'] = sum(line.startswith('law ') for line in (ROOT / 'src/c-LAWS.bend').read_text().splitlines())
        require(record['checked_laws'] == 8, 'Declared C law inventory')
        record['proof'] = successful([*SEED, ROOT / 'src/c-PROOF.bend'])
        require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
        record['reference'], record['recursion_reference'] = reference(manifest)
        record['builds'], lanes = [], {}
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun', '--no-env-file'])]:
            lanes[lane] = {}
            for phase, entry in [('c', HERE / 'compile.bend'),
                    ('wasm', ROOT / 'tests/compiler-fields-wasm/compile.bend'),
                    ('eval', ROOT / 'src/eval-cli.bend'), ('check', ROOT / 'src/check-cli.bend')]:
                output = BUILD / (phase + suffix)
                built = successful([*SEED, entry, '-o', output])
                record['builds'].append({'lane': lane, 'phase': phase, 'result': built,
                                         'sha256': digest(output)})
                lanes[lane][phase] = [*runtime, output]
        artifacts = corpus(manifest, lanes, record)
        original_recursion(manifest, lanes, record)
        rejections(manifest, lanes, record)
        boundaries(manifest, lanes, artifacts, record)
        adapter_probes(artifacts, record)
        mutants(manifest, record)
        require(all(digest(ROOT / path) == value for path, value in record['inputs'].items()),
                'Inputs changed during gate')
        calls = sum(len(case['calls']) for case in manifest['cases'])
        accepted_recursion = sum('emission' in row['lanes']['native'] for row in record['recursion_originals'])
        record['counts'] = {'programs': len(manifest['cases']), 'reference_calls': calls,
                'original_recursion_reference': len(record['recursion_reference']),
                'evaluator_observations': 2 * calls, 'wasm_observations': 2 * calls,
                'c_observations': 2 * calls, 'sanitizer_observations': calls,
                'byte_identical_c': len(manifest['cases']) + accepted_recursion,
                'byte_identical_wasm': len(manifest['cases']),
                'original_recursion_phase_observations': len(record['recursion_originals']) * 4,
                'original_recursion_c_builds': 2 * accepted_recursion, 'rejection_pairs': len(record['rejects']),
                'boundary_probes': len(record['boundaries']),
                'host_boundary_probes': len(record['host_boundaries']),
                'host_adapter_probes': sum(row['name'].startswith('adapter-') for row in record['host_boundaries']),
                'mutants': len(record['mutants']), 'checked_laws': record['checked_laws']}
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print('C gate passed: ' + ', '.join(f'{key}={value}' for key, value in record['counts'].items())
          + '. ' + str(RECEIPT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference-only', action='store_true')
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(exist_ok=True)
    require(os.environ.get('BEND_NO_TELEMETRY') == '1', 'export BEND_NO_TELEMETRY=1')
    manifest = json.loads((HERE / 'cases.json').read_text())
    fixed = fixed_inputs(manifest)
    if args.reference_only:
        require(not FREEZE.exists(), 'The preimplementation reference freeze is immutable')
        observations, originals = reference(manifest)
        freeze = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'passed',
                  'seed_revision': manifest['seed_revision'], 'frozen_inputs': fixed,
                  'observations': observations, 'recursion_originals': originals}
        FREEZE.write_text(json.dumps(freeze, indent=2) + '\n')
        print(f"C reference freeze passed: {len(manifest['cases'])} programs, {len(observations)} calls, {len(originals)} original recursion observations. {FREEZE}")
        return
    execute(manifest, fixed)


if __name__ == '__main__':
    main()
