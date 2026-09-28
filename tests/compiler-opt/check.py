#!/usr/bin/env python3
"""Drive fixed seed observations, checked core passes, and actual Wasm.

This harness does not implement source parsing, checking, evaluation, or emission.
Only canonical observations and independently decoded Wasm signatures are compared.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/compiler-opt/gate'
RECEIPT = HERE / 'receipts/optimization.json'
SEED = ['bun', '--no-env-file', ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']
HOST = ROOT / 'scripts/run-wasm.mjs'
PROFILE = '--profile=knot-fields-wasm-1'
ENV = {**os.environ, 'BEND_NO_TELEMETRY': '1'}


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, timeout=60):
    argv = [str(x) for x in argv]
    try:
        result = subprocess.run(argv, cwd=ROOT, env=ENV, text=True,
                                capture_output=True, timeout=timeout)
        return {'argv': argv, 'exit': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired:
        return {'argv': argv, 'exit': None, 'outcome': 'harness-timeout',
                'budget_seconds': timeout, 'stdout': '', 'stderr': ''}


def successful(argv):
    result = run(argv)
    require(result['exit'] == 0, result)
    return result


def diagnostic(result, status, prefix):
    require(result['exit'] == status and result['stderr'].startswith(prefix)
            and not result['stdout'], (prefix, result))


def observe(result, expected):
    require(result['exit'] == expected['exit'], (expected, result))
    if 'stdout' in expected:
        require(result['stdout'].strip() == expected['stdout'], (expected, result))
    if 'diagnostic' in expected:
        require(expected['diagnostic'] in result['stderr'] and not result['stdout'],
                (expected, result))


def compiled(command, source, output, budgets=()):
    output.unlink(missing_ok=True)
    result = successful([*command, source, output, *budgets])
    require(output.is_file() and result['stdout'].strip() == f'Built\t{output.stat().st_size}', result)
    return result


def abi(wat):
    """Read wasm2wat's host signatures, never source-language types or values."""
    types = dict(re.findall(r'^\s*\(type \(;(\d+);\) (\(func[^\n]+)\)\s*$', wat, re.M))
    functions = dict(re.findall(r'^\s*\(func \(;(\d+);\) \(type (\d+)\)', wat, re.M))
    exports = re.findall(r'\(export "([^"]+)" \(func (\d+)\)\)', wat)
    require(exports and len(exports) == len(set(name for name, _ in exports)), 'unique function exports')
    require(len(re.findall(r'^\s*\(export ', wat, re.M)) == len(exports),
            'nonfunction export changes the host ABI')
    return [{'name': name, 'signature': types[functions[index]]} for name, index in exports]


def tail_calls(wat):
    current, tail, ordinary = None, [], []
    for line in wat.splitlines():
        function = re.match(r'^  \(func \(;(\d+);\)', line)
        if function:
            current = int(function[1])
        call = re.match(r'^\s+(return_call|call) (\d+)\b', line)
        if call:
            target = int(call[2])
            if call[1] == 'return_call':
                require(target == current, ('tail call is not self-recursive', current, target))
                tail.append(current)
            elif target == current:
                ordinary.append(current)
    return {'tail_self_calls': tail, 'ordinary_self_calls': ordinary}


def decode(path):
    result = successful(['wasm2wat', '--enable-tail-call', path])
    return result['stdout'], abi(result['stdout'])


def host(path, call, flags=()):
    return run(['node', *flags, HOST, PROFILE, path, call['export'], *call['arguments']])


def enum_value(result, case, call):
    expected = f'Evaluated\t{case["type_id"]}\t{call["tag"]}\t{case["constructors"][call["tag"]]}{{}}'
    observe(result, {'exit': 0, 'stdout': expected})


def host_value(result, call):
    require(result['exit'] == 0, result)
    value = json.loads(result['stdout'])
    require(value['validated'] is True and value['result'] == call['tag'], (call, result))


def load_corpus(frozen, baseline):
    cases, rejects = [], []
    for family in ('compiler-wasm', 'compiler-fields-wasm', 'compiler-recursion'):
        manifest = json.loads((ROOT / 'tests' / family / 'cases.json').read_text())
        for original in manifest['cases']:
            case = dict(original)
            case['family'] = family
            case['name'] = case.get('name', Path(case['file']).stem)
            case['key'] = family + '-' + case['name']
            if not case['file'].startswith('tests/'):
                case['file'] = 'tests/' + family + '/' + case['file']
            if family == 'compiler-recursion':
                if case['check']['exit'] != 0:
                    rejects.append(case)
                    continue
                case['calls'] = [{'export': 'main', 'arguments': [],
                                  'expected_eval': case['eval'], 'structured_result': True}]
            cases.append(case)
    for original in frozen['cases']:
        cases.append({**original, 'family': 'compiler-opt', 'key': 'compiler-opt-' + original['name']})
    for original in frozen['observer_cases']:
        cases.append({**original, 'family': 'compiler-opt-observer',
                      'key': 'compiler-opt-observer-' + original['name']})
    generated = json.loads(successful(['node', '--input-type=module', '-e',
        "import {generate} from './bench/generate.mjs'; console.log(JSON.stringify(generate()))"])
        ['stdout'])
    require(generated == baseline['generated'], 'benchmark generator or fixed generated domains drifted')
    for program in generated:
        flags = program['name'].startswith('calls-')
        size = int(program['name'].split('-')[-1])
        constructors = ['Off', 'On'] if flags else [f'T{i}' for i in range(size)]
        arguments = ','.join('F.' + constructors[i] + '{}' for i in program['args'])
        cases.append({'family': 'bench', 'name': program['name'], 'key': 'bench-' + program['name'],
                      'file': program['program'], 'type': 'Flag' if flags else 'Tag',
                      'type_id': 0, 'constructors': constructors,
                      'calls': [{'export': program['entry'], 'arguments': program['args'],
                                 'tag': program['expected'],
                                 'seed': f'F.{program["entry"]}({arguments})'}]})
    require(len(cases) == 74 and len(rejects) == 8, 'frozen corpus and observer coverage')
    return cases, rejects


def reference(case):
    if case['family'] == 'compiler-recursion':
        result = run([*SEED, ROOT / case['file']])
        observe(result, case['reference'])
        return [{'call': case['calls'][0], 'result': result}]
    observations = []
    for index, call in enumerate(case['calls']):
        wrapper = BUILD / f'{case["key"]}-reference-{index}.bend'
        imported = os.path.relpath(ROOT / case['file'], wrapper.parent)
        wrapper.write_text(f'import {imported} as F\n\ndef main() -> F.{case["type"]}:\n  {call["seed"]}\n')
        result = successful([*SEED, wrapper])
        expected = imported.removesuffix('.bend') + '.' + case['constructors'][call['tag']] + '{}'
        require(result['stdout'].strip() == expected, (expected, result))
        observations.append({'call': call, 'source_sha256': digest(wrapper), 'result': result})
    return observations


def build_lanes(record):
    sources = {'compile_off': ROOT / 'tests/compiler-fields-wasm/compile.bend',
               'compile_default': ROOT / 'src/compile-cli.bend',
               'compile_on': HERE / 'compile.bend',
               'eval_off': ROOT / 'src/eval-cli.bend',
               'eval_on': HERE / 'eval.bend', 'audit': HERE / 'audit.bend'}
    lanes = {}
    for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun', '--no-env-file'])]:
        lanes[lane] = {}
        for name, source in sources.items():
            output = BUILD / (name + suffix)
            result = successful([*SEED, source, '-o', output])
            record['builds'].append({'lane': lane, 'entry': str(source.relative_to(ROOT)),
                                     'result': result, 'sha256': digest(output)})
            lanes[lane][name] = [*runtime, output]
    return lanes


def build_pass_lanes(record):
    lanes = {'native': {}, 'bun': {}}
    for name, constructor in [('inline', 'Inline'), ('fold', 'Fold'), ('dead', 'Dead')]:
        entries = {}
        for phase, anchor, replacement in [
            ('compile', 'O.pipeline(depth,book)', f'O.apply(depth,O.{constructor}{{}},book)'),
            ('eval', 'O.pipeline(4096n,book)', f'O.apply(4096n,O.{constructor}{{}},book)')]:
            source = (HERE / (phase + '.bend')).read_text()
            require(source.count(anchor) == 1, ('single-pass entry anchor', phase))
            entry = BUILD / f'pass-{name}-{phase}.bend'
            imported = os.path.relpath(ROOT / 'src', BUILD)
            entry.write_text(source.replace('../../src/', imported + '/').replace(anchor, replacement))
            entries[phase] = entry
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun', '--no-env-file'])]:
            lanes[lane][name] = {}
            for phase, entry in entries.items():
                output = BUILD / (f'pass-{name}-{phase}' + suffix)
                result = successful([*SEED, entry, '-o', output])
                record['builds'].append({'lane': lane, 'pass': name, 'phase': phase,
                                         'source_sha256': digest(entry), 'result': result,
                                         'sha256': digest(output)})
                lanes[lane][name][phase] = [*runtime, output]
    return lanes


def pass_observations(commands, case, expected_abi, lane):
    rows = {}
    for name, entry in commands.items():
        output = BUILD / f'{case["key"]}-{lane}-{name}.wasm'
        result = compiled(entry['compile'], ROOT / case['file'], output, case.get('compile_budgets', []))
        wat, signatures = decode(output)
        calls = tail_calls(wat)
        require(signatures == expected_abi, (case['key'], name, lane, 'single-pass ABI changed'))
        observations = []
        for call in case['calls']:
            evaluated = run([*entry['eval'], ROOT / case['file'], call['export'], 1048576, *call['arguments']])
            if 'eval_exhausted' in case:
                diagnostic(evaluated, 4, case['eval_exhausted'])
            elif call.get('structured_result'):
                observe(evaluated, call['expected_eval'])
            else:
                enum_value(evaluated, case, call)
            observation = {'call': call, 'evaluator': evaluated}
            if call.get('structured_result'):
                observation['wasm'] = {'outcome': 'covered-by-exact-tree-observer',
                                       'observer': 'compiler-opt-observer-' + case['name']}
            else:
                actual = host(output, call)
                if case['family'] == 'compiler-fields-wasm' and case['name'] == 'arena-overflow' and actual['exit'] == 4:
                    diagnostic(actual, 4, 'Exhausted\twasm\tarena-overflow')
                else:
                    host_value(actual, call)
                observation['wasm'] = actual
            observations.append(observation)
        if lane == 'bun':
            native = BUILD / f'{case["key"]}-native-{name}.wasm'
            require(output.read_bytes() == native.read_bytes(), (case['key'], name, 'single-pass native/Bun bytes differ'))
        rows[name] = {'compile': result, 'sha256': digest(output), 'bytes': output.stat().st_size,
                      'abi': signatures, 'calls': calls, 'observations': observations}
    return rows


def audit(commands, case):
    path = ROOT / case['file']
    # All three rounds use the same input bounds, including deep-call's enlarged parser.
    results = [successful([*commands['audit'], path, round]) for round in range(3)]
    text = [item['stdout'] for item in results]
    require(text[1] == text[2], (case['key'], 'pipeline not idempotent', results[1:]))
    signatures = [[line.split('=', 1)[0] for line in value.splitlines()] for value in text]
    require(signatures[0] == signatures[1], (case['key'], 'checked core signatures changed', signatures))
    return {'rounds': results, 'idempotent': True, 'signatures_preserved': True,
            'changed': text[0] != text[1]}


# Exact mutation anchors are tied to the implementation; expected values come only
# from the already frozen fixtures. Every mutant must still check in the seed.
MUTANTS = [
    ('case-wrong-arm', 'opt-fold.bend', 'U32.is_eq(tag,pattern)', 'U32.is_ne(tag,pattern)',
     'known', 'main', []),
    ('dce-used-let', 'opt-fold.bend',
     'Bool.and(discardable(quantity),U32.is_eq(uses,0))', 'discardable(quantity)',
     'used-let', 'choose', [1]),
    ('inline-capture', 'opt-term.bend',
     'C.Reference{token,U32.add(level,offset),typ}', 'C.Reference{token,level,typ}',
     'capture', 'observe', [0, 1]),
    ('dce-export', 'opt.bend',
     'Con{C.Function{signature,body},rest}', 'rest',
     'known', 'main', []),
]


def mutants(record, cases):
    require(len(MUTANTS) == 4, 'four registered semantic mutants required')
    by_name = {c['name']: c for c in cases if c['family'] == 'compiler-opt'}
    for mutation in MUTANTS:
        name, filename, old, new, witness, export, args = mutation
        directory = BUILD / 'mutants' / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / '.toolchain').symlink_to(ROOT / '.toolchain', target_is_directory=True) if not (directory / '.toolchain').exists() else None
        (directory / 'node_modules').symlink_to(ROOT / 'node_modules', target_is_directory=True) if not (directory / 'node_modules').exists() else None
        target_src = directory / 'src'
        target_src.mkdir(exist_ok=True)
        for source in (ROOT / 'src').glob('*.bend'):
            shutil.copy2(source, target_src / source.name)
        target = target_src / filename
        original = target.read_text()
        require(original.count(old) == 1, (name, 'unique mutation anchor'))
        target.write_text(original.replace(old, new))
        entry = directory / 'compile.bend'
        entry.write_text((HERE / 'compile.bend').read_text().replace('../../src/', './src/'))
        checked = successful([*SEED, entry, '--check-only'])
        require(checked['stdout'].strip() == 'All terms check.', checked)
        case = by_name[witness]
        call = next(c for c in case['calls'] if c['export'] == export and c['arguments'] == args)
        item = {'name': name, 'file': filename, 'old': old, 'new': new,
                'source_sha256': digest(target), 'typecheck': checked,
                'witness': case['file'], 'call': call, 'lanes': {}}
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun', '--no-env-file'])]:
            executable = directory / ('compiler' + suffix)
            built = successful([*SEED, entry, '-o', executable])
            module = directory / (lane + '.wasm')
            module.unlink(missing_ok=True)
            emitted = run([*runtime, executable, ROOT / case['file'], module])
            result = {'build': built, 'emission': emitted}
            expected_internal = {'dce-used-let': 'binding-level', 'inline-capture': 'affine-reuse'}.get(name)
            if expected_internal:
                expected = 'InternalFailure\topt-core\t' + expected_internal
                diagnostic(emitted, 6, expected)
                require(emitted['stderr'].strip() == expected, (name, emitted))
                require(not module.exists(), (name, 'invalid optimized artifact emitted'))
                result['outcome'] = 'checked-core-preservation-kill'
            else:
                require(emitted['exit'] == 0 and module.is_file(), (name, emitted))
                result['validation'] = successful(['wasm2wat', '--enable-tail-call', module])
                actual = host(module, call)
                require(actual['exit'] in (0, 5), actual)
                if actual['exit'] == 5:
                    diagnostic(actual, 5, 'HostFailure\twasm\tunknown export or wrong live arity')
                else:
                    require(json.loads(actual['stdout'])['result'] != call['tag'], (name, 'mutant survived'))
                result.update(actual=actual, outcome='semantic-kill')
            item['lanes'][lane] = result
        record['mutants'].append(item)


def optimizer_boundaries(record, lanes):
    for lane, commands in lanes.items():
        for label, budgets, expected in [
            ('optimizer-depth', [65536, 512, 512, 0, 65536], 'Exhausted\topt-core\tbudget\t0:0:0:0'),
            ('output-capacity', [65536, 512, 512, 4096, 0], 'Exhausted\temit\tbudget\t0:0:0:0')]:
            output = BUILD / f'{label}-{lane}.wasm'
            output.write_bytes(b'unchanged-output')
            result = run([*commands['compile_on'], HERE / 'fixtures/known.bend', output, *budgets])
            diagnostic(result, 4, expected)
            require(result['stderr'].strip() == expected, result)
            require(output.read_bytes() == b'unchanged-output', ('exhaustion changed output', lane, label))
            record['boundaries'].append({'name': label, 'lane': lane, 'budgets': budgets,
                                         'result': result, 'artifact_preserved': True})
        missing = BUILD / 'absent-source.bend'
        missing.unlink(missing_ok=True)
        output = BUILD / f'missing-source-{lane}.wasm'
        output.write_bytes(b'unchanged-output')
        result = run([*commands['compile_on'], missing, output])
        diagnostic(result, 5, 'HostFailure\topen\t')
        require(output.read_bytes() == b'unchanged-output', ('host failure changed output', lane))
        record['boundaries'].append({'name': 'missing-source', 'lane': lane,
                                     'result': result, 'artifact_preserved': True})


def main():
    require(os.environ.get('BEND_NO_TELEMETRY') == '1', 'export BEND_NO_TELEMETRY=1')
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(exist_ok=True)
    frozen = json.loads((HERE / 'expectations.json').read_text())
    baseline = json.loads((HERE / 'baseline.json').read_text())
    cases, rejected = load_corpus(frozen, baseline)
    baseline_by_file = {row['source']: row for row in baseline['cases'] + baseline['observer_cases']}
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'incomplete', 'profile': 'knot-core-opt-1',
              'seed_revision': frozen['seed_revision'], 'builds': [], 'fixtures': [],
              'rejects': [], 'boundaries': [], 'mutants': []}
    try:
        require(set(baseline_by_file) == {c['file'] for c in cases}, 'baseline corpus coverage')
        current_sources = {source: digest(ROOT / source) if (ROOT / source).is_file() else None
                           for source in baseline['unchanged_source']}
        record['baseline_source_audit'] = {source: {'baseline': expected, 'current': current_sources[source],
                                                  'unchanged': current_sources[source] == expected}
                                           for source, expected in baseline['unchanged_source'].items()}
        record['baseline_sources_unchanged'] = all(row['unchanged'] for row in record['baseline_source_audit'].values())
        require([(o['case'], o['call'], o['source_sha256']) for o in frozen['observations']] ==
                [(c['name'], call, digest(ROOT / c['file'])) for c in frozen['cases'] for call in c['calls']],
                'new fixture expectations or domains drifted')
        for observer in frozen['observer_cases']:
            original = ROOT / observer['original']
            require(digest(original) == observer['original_sha256'], ('observer input drifted', observer['name']))
            require((ROOT / observer['file']).read_text() == original.read_text() + observer['suffix'],
                    ('observer changes original source', observer['name']))
            require(digest(ROOT / observer['file']) == observer['source_sha256'],
                    ('frozen observer drifted', observer['name']))
        for name, expected in frozen['seed_hashes'].items():
            require(digest(ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2' / name) == expected,
                    ('pinned seed changed', name))
        paths = [*sorted((ROOT / 'src').glob('*.bend')), *sorted(HERE.glob('*.bend')),
                 HERE / 'baseline.json', HERE / 'expectations.json', HERE / 'SPEC.md', Path(__file__),
                 ROOT / 'bench/generate.mjs', HOST,
                 *[ROOT / 'tests' / family / 'cases.json'
                   for family in ('compiler-wasm', 'compiler-fields-wasm', 'compiler-recursion')], *[ROOT / c['file'] for c in cases + rejected]]
        record['inputs'] = {str(p.relative_to(ROOT)): digest(p) for p in paths}
        record['tools'] = {t: successful([t, '--version'])['stdout'].strip()
                           for t in ('bun', 'node', 'python3', 'wasm2wat')}
        require(record['tools']['node'] == 'v22.22.3', record['tools'])
        record['proof'] = successful([*SEED, ROOT / 'src/opt-PROOF.bend'])
        require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
        record['new_laws'] = len(re.findall(r'^law ', (ROOT / 'src/opt-LAWS.bend').read_text(), re.M))
        require(record['new_laws'] == 12, 'twelve complete optimizer laws required')
        lanes = build_lanes(record)
        pass_lanes = build_pass_lanes(record)
        record['core_controls'] = []
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun', '--no-env-file'])]:
            output = BUILD / ('core-controls' + suffix)
            built = successful([*SEED, HERE / 'core-controls.bend', '-o', output])
            result = successful([*runtime, output])
            require(result['stdout'].strip() == 'CoreControls\t43', result)
            record['core_controls'].append({'lane': lane, 'build': built, 'result': result, 'count': 43})
        modules = {}
        for case in cases:
            path = ROOT / case['file']
            pinned = baseline_by_file[case['file']]
            require(digest(path) == pinned['source_sha256'], ('source drifted', case['file']))
            row = {'key': case['key'], 'file': case['file'], 'reference': reference(case), 'lanes': {}}
            for lane, commands in lanes.items():
                off, on = [BUILD / f'{case["key"]}-{lane}-{setting}.wasm' for setting in ('off', 'on')]
                disabled = compiled(commands['compile_off'], path, off, case.get('compile_budgets', []))
                require(digest(off) == pinned['wasm_sha256'], (case['key'], lane, 'unoptimized bytes changed'))
                enabled = compiled(commands['compile_on'], path, on, case.get('compile_budgets', []))
                off_wat, off_abi = decode(off)
                on_wat, on_abi = decode(on)
                calls = tail_calls(on_wat)
                require(off_abi == on_abi, (case['key'], lane, 'host ABI changed', off_abi, on_abi))
                inspection = audit(commands, case)
                observations = []
                for call in case['calls']:
                    evaluations = {setting: run([*commands['eval_' + setting], path, call['export'],
                                                 1048576, *call['arguments']]) for setting in ('off', 'on')}
                    for setting, evaluated in evaluations.items():
                        if 'eval_exhausted' in case:
                            diagnostic(evaluated, 4, case['eval_exhausted'])
                        elif call.get('structured_result'):
                            observe(evaluated, call['expected_eval'])
                        else:
                            enum_value(evaluated, case, call)
                    observation = {'call': call, 'evaluator': evaluations}
                    if call.get('structured_result'):
                        observation['wasm'] = {'outcome': 'covered-by-exact-tree-observer',
                                               'observer': 'compiler-opt-observer-' + case['name'],
                                               'reason': 'exact tree is checked inside Bend, returning an enum; no pointer interpretation at the host'}
                    else:
                        actual = {setting: host(module, call) for setting, module in [('off', off), ('on', on)]}
                        if case['family'] == 'compiler-fields-wasm' and case['name'] == 'arena-overflow':
                            diagnostic(actual['off'], 4, 'Exhausted\twasm\tarena-overflow')
                            if actual['on']['exit'] == 4:
                                diagnostic(actual['on'], 4, 'Exhausted\twasm\tarena-overflow')
                            else:
                                host_value(actual['on'], call)
                            observation['resource_relation'] = 'bounded arena exhaustion is inconclusive, not a semantic value'
                        else:
                            for value in actual.values():
                                host_value(value, call)
                        observation['wasm'] = actual
                    observations.append(observation)
                row['lanes'][lane] = {'off': {'compile': disabled, 'sha256': digest(off), 'bytes': off.stat().st_size},
                                      'on': {'compile': enabled, 'sha256': digest(on), 'bytes': on.stat().st_size},
                                      'abi': on_abi, 'calls': calls, 'audit': inspection, 'observations': observations,
                                      'passes': pass_observations(pass_lanes[lane], case, off_abi, lane)}
                modules[(case['key'], lane)] = (off, on)
                if case['family'] == 'compiler-wasm':
                    default = BUILD / f'{case["key"]}-{lane}-default.wasm'
                    row['lanes'][lane]['default_compile'] = compiled(commands['compile_default'], path, default)
                    require(default.read_bytes() == off.read_bytes(), (case['key'], 'default enum bytes changed'))
                if case['key'] == 'compiler-opt-tail':
                    require(calls['tail_self_calls'], ('missing tail lowering', lane))
                if case['key'] == 'compiler-opt-non-tail':
                    require(calls['ordinary_self_calls'] and not calls['tail_self_calls'],
                            ('non-tail self call incorrectly lowered', lane, calls))
                if lane == 'bun':
                    native_off, native_on = modules[(case['key'], 'native')]
                    require(off.read_bytes() == native_off.read_bytes() and on.read_bytes() == native_on.read_bytes(),
                            (case['key'], 'native/Bun emitted bytes differ'))
                    require(inspection['rounds'][1]['stdout'] == row['lanes']['native']['audit']['rounds'][1]['stdout'],
                            (case['key'], 'native/Bun core differs'))
            record['fixtures'].append(row)
        for case in rejected:
            reference_result = run([*SEED, ROOT / case['file'], *case.get('reference_args', [])])
            observe(reference_result, case['reference'])
            for lane, commands in lanes.items():
                row = {'key': case['key'], 'lane': lane, 'reference': reference_result, 'observations': {}}
                for setting in ('off', 'on'):
                    module = BUILD / f'reject-{lane}-{setting}.wasm'
                    module.unlink(missing_ok=True)
                    emitted = run([*commands['compile_' + setting], ROOT / case['file'], module])
                    evaluated = run([*commands['eval_' + setting], ROOT / case['file'], 'main', 1048576])
                    for result in (emitted, evaluated):
                        observe(result, case['check'])
                    require(not module.exists(), ('rejected source emitted artifact', case['key']))
                    row['observations'][setting] = {'compile': emitted, 'eval': evaluated}
                record['rejects'].append(row)
        stack = json.loads((ROOT / 'tests/compiler-fields-wasm/cases.json').read_text())['stack']
        for lane in lanes:
            for name, key in [('shallow', 'compiler-fields-wasm-pair'), ('deep', 'compiler-fields-wasm-deep-stack')]:
                for setting, module in zip(('off', 'on'), modules[(key, lane)]):
                    result = host(module, {'export': 'main', 'arguments': [], 'tag': 1}, stack['node_flags'])
                    if name == 'deep' and result['exit'] == 4:
                        diagnostic(result, 4, stack['diagnostic'])
                    else:
                        host_value(result, {'tag': 1})
                    record['boundaries'].append({'name': 'stack-' + name, 'lane': lane, 'setting': setting, 'result': result})
        optimizer_boundaries(record, lanes)
        mutants(record, cases)
        require(all(digest(ROOT / p) == expected for p, expected in record['inputs'].items()), 'inputs changed during gate')
        record['counts'] = {'source_programs': len(cases) + len(rejected) - 11, 'accepted_programs': len(cases) - 11,
                            'observer_programs': 11,
                            'rejected_programs': len(rejected), 'reference_calls': sum(len(c['calls']) for c in cases),
                            'execution_lanes': len(lanes), 'new_laws': record['new_laws'], 'core_verifier_controls_per_lane': 43, 'core_idempotence_checks': len(cases) * len(lanes),
                            'abi_checks': len(cases) * len(lanes),
                            'single_pass_abi_checks': len(cases) * len(lanes) * 3,
                            'self_tail_module_checks': len(cases) * len(lanes) * 4,
                            'single_pass_evaluator_checks': sum(len(c['calls']) for c in cases) * len(lanes) * 3, 'unoptimized_byte_checks': len(cases) * len(lanes),
                            'default_enum_byte_checks': 25 * len(lanes),
                            'structured_result_observers': 11 * len(lanes), 'direct_pointer_host_calls': 0,
                            'rejection_lane_observations': len(record['rejects']),
                            'boundaries': len(record['boundaries']), 'semantic_mutants': len(record['mutants']),
                            'new_fixtures': 10, 'new_fixture_reference_calls': 47, 'observer_reference_calls': 22, 'generated_programs': 9}
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print('Optimization gate passed: ' + json.dumps(record['counts'], sort_keys=True) + '. ' + str(RECEIPT))


if __name__ == '__main__':
    main()
