#!/usr/bin/env python3
"""Compare frozen seed outcomes with both Bend compiler lanes and real Wasm."""
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
BUILD = ROOT / '.local/compiler-closures/gate'
RECEIPT = HERE / 'receipts/closures.json'
SEED = ['bun', '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']
COMPILE = ROOT / 'tests/compiler-fields-wasm/compile.bend'
HOST = ROOT / 'scripts/run-wasm.mjs'
PROFILE = '--profile=knot-fields-wasm-1'
MARKER = b'An unsuccessful closure compilation must preserve this artifact.\n'
OUTCOMES = {0: 'success', 2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted',
            5: 'HostFailure', 6: 'InternalFailure'}
LANES = [('native', '', []), ('bun', '.js', ['bun'])]


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(value):
    text = str(value)
    return str(Path(text).relative_to(ROOT)) if text.startswith(str(ROOT) + '/') else text


def run(argv, timeout=120):
    command = [relative(a) for a in argv]
    try:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                                timeout=timeout, env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
        return {'argv': command, 'exit': result.returncode, 'stdout': result.stdout,
                'stderr': result.stderr}
    except subprocess.TimeoutExpired:
        return {'argv': command, 'exit': None, 'outcome': 'harness-timeout',
                'stdout': '', 'stderr': ''}
    except OSError as error:
        return {'argv': command, 'exit': None, 'outcome': 'host-process-failure',
                'stdout': '', 'stderr': str(error)}


def successful(argv, timeout=120):
    result = run(argv, timeout)
    require(result['exit'] == 0, result)
    return result


def classified(result):
    status = OUTCOMES.get(result['exit'])
    require(status is not None, ('unclassified process failure', result))
    if result['exit']:
        require(result['stdout'] == '' and result['stderr'].startswith(status + '\t'),
                ('outcome/exit disagreement', result))
    else:
        require(result['stderr'] == '', ('successful phase printed a diagnostic', result))
    return status


def diagnostic(result, status, prefix):
    require(classified(result) == OUTCOMES[status] and result['exit'] == status
            and result['stderr'].startswith(prefix), (prefix, result))


def seed_probe(probe):
    path = HERE / probe['file']
    require(digest(path) == probe['source_sha256'], ('supplemental probe changed', probe['name']))
    checked = run(probe['check_only']['argv'])
    require(checked == probe['check_only'], ('supplemental seed check drift', checked))
    observations = []
    for call in probe['calls']:
        if call['wrapper']:
            wrapper = ROOT / call['wrapper']
            wrapper.parent.mkdir(parents=True, exist_ok=True)
            wrapper.write_text(call['wrapper_source'])
        actual = run(call['argv'])
        expected = {key: call[key] for key in ('argv', 'exit', 'stdout', 'stderr')}
        require(actual == expected, ('supplemental seed result drift', expected, actual))
        observations.append(actual)
    return {'case': probe['name'], 'check': checked, 'calls': observations}


def seed_regression(case):
    path = HERE / case['file']
    require(digest(path) == case['source_sha256'], ('regression source changed', case['name']))
    observations = {}
    for phase, suffix in [('check_only', ['--check-only']), ('run', [])]:
        expected = case['seed'][phase]
        require(expected['argv'] == [*SEED, relative(path), *suffix],
                ('regression seed command must check its own source', case['name'], expected))
        actual = run(expected['argv'])
        require(actual == expected, ('regression seed drift', case['name'], expected, actual))
        observations[phase] = actual
    accepted = case['knot']['require'] == 'agree'
    if accepted:
        require(observations['check_only']['exit'] == 0
                and observations['check_only']['stdout'] == 'All terms check.\n'
                and observations['check_only']['stderr'] == '', observations)
        require(len(case['calls']) == 1 and case['calls'][0]['entry'] == 'main'
                and case['calls'][0]['ordinals'] == [], 'regression controls use main-only enum calls')
        require(observations['run']['exit'] == 0 and observations['run']['stderr'] == ''
                and observations['run']['stdout'] == case['calls'][0]['result']['constructor'] + '{}\n',
                ('regression call disagrees with frozen seed run', case['name']))
    else:
        require(case['knot']['require'] == 'reject' and not case['calls']
                and observations['check_only']['exit'] == 1 and observations['run']['exit'] == 1,
                ('negative regression must remain seed-rejected', case['name']))
    return {'case': case['name'], **observations}


def evaluator(result, call):
    expected = call['result']
    require(classified(result) == 'success', (call, result))
    match = re.fullmatch(r'Evaluated\t([0-9]+)\t([0-9]+)\t([A-Za-z_][A-Za-z_0-9]*)\{\}\n', result['stdout'])
    require(match is not None and int(match[2]) == expected['tag']
            and match[3] == expected['constructor'], (expected, result))


def wasm(result, call):
    require(classified(result) == 'success', (call, result))
    value = json.loads(result['stdout'])
    require(value.get('validated') is True and value.get('export') == call['entry']
            and value.get('arguments') == call['ordinals']
            and value.get('result') == call['result']['tag'], (call, result))


def rejected(result, requirement):
    outcome = classified(result)
    require(outcome in ('Invalid', 'Unsupported'), ('not a language rejection', result))
    if requirement['require'] in ('unsupported', 'agree-or-unsupported'):
        require(outcome == 'Unsupported', ('seed-valid source reported Invalid', result))
    if 'exit' in requirement:
        require(result['exit'] == requirement['exit'], (requirement, result))
    if 'diagnostic' in requirement:
        require(result['stderr'].startswith(requirement['diagnostic']), (requirement, result))


def built(result, output):
    require(classified(result) == 'success' and output.is_file()
            and result['stdout'] == f'Built\t{output.stat().st_size}\n'
            and output.read_bytes() != MARKER, result)


def inspect_module(output):
    decoded = successful(['wasm2wat', '--enable-tail-call', output])
    wat = decoded['stdout']
    require('(import ' not in wat and '(table ' not in wat and 'call_indirect' not in wat
            and 'ref.func' not in wat, ('closures must be defunctionalized', relative(output)))
    if '(memory ' in wat:
        require('(memory (;0;) 1 1)' in wat, ('bounded closure arena', relative(output)))
    require(not re.search(r'\(export "[^"]+" \(memory ', wat), 'closure memory stays internal')
    return {'sha256': digest(output), 'wat_sha256': hashlib.sha256(wat.encode()).hexdigest(),
            'tail_calls': wat.count('return_call '), 'defunctionalized': True}


def run_case(case, calls, lanes, modules, record):
    name, path, requirement = case['name'], HERE / case['file'], case['knot']
    item = {'case': name, 'origin': case.get('origin', 'frozen'),
            'requirement': requirement['require'], 'lanes': {}}
    record['fixtures'].append(item)
    dispositions = []
    for lane, commands in lanes.items():
        checked = run([*commands['check'], path])
        outcome = classified(checked)
        output = BUILD / f'{name}-{lane}.wasm'
        output.write_bytes(MARKER)
        compiled = run([*commands['compile'], path, output])
        classified(compiled)
        row = {'check': checked, 'compile': compiled, 'calls': []}
        item['lanes'][lane] = row
        # The immutable corpus explicitly allows a named prerequisite to block
        # a fixture. This preserves its original "agree" requirement and never
        # counts the blocked calls as agreement.
        blocked = (name == 'generic-choose-bind' and 'generics' in case.get('requires', [])
                   and outcome == 'Unsupported')
        if blocked:
            prefix = 'Unsupported\tparse\tgeneric-datatype\t'
            evaluated = run([*commands['eval'], path, 'main', 1048576])
            for result in (checked, compiled, evaluated):
                diagnostic(result, 3, prefix)
            require(output.read_bytes() == MARKER, ('blocked compilation changed artifact', name))
            row.update(eval=evaluated, artifact_preserved=True, disposition='blocked', need='generics')
            dispositions.append('blocked')
            continue
        if requirement['require'] == 'reject' or requirement['require'] == 'unsupported' or outcome != 'success':
            require(requirement['require'] != 'agree', ('required capability unavailable', name, checked))
            evaluated = run([*commands['eval'], path, 'main', 1048576])
            for result in (checked, compiled, evaluated):
                rejected(result, requirement)
            require(output.read_bytes() == MARKER, ('rejection changed artifact', name))
            row.update(eval=evaluated, artifact_preserved=True, disposition='rejected')
            dispositions.append('rejected')
            continue
        require(checked['stdout'].startswith('Checked\n'), checked)
        built(compiled, output)
        row['module'] = inspect_module(output)
        if name == 'deep-tail':
            require(row['module']['tail_calls'] > 0, 'the continuation-chain control needs return_call')
        modules.setdefault(name, {})[lane] = output
        for call in calls:
            evaluated = run([*commands['eval'], path, call['entry'], 1048576, *call['ordinals']])
            evaluator(evaluated, call)
            executed = run(['node', HOST, PROFILE, output, call['entry'], *call['ordinals']])
            wasm(executed, call)
            row['calls'].append({'entry': call['entry'], 'arguments': call['ordinals'],
                                 'expected': call['result'], 'evaluator': evaluated, 'wasm': executed})
        row['disposition'] = 'agreed'
        dispositions.append('agreed')
    require(len(set(dispositions)) == 1, ('compiler lanes disagree on classification', name, dispositions))
    item['disposition'] = dispositions[0]
    if dispositions[0] == 'agreed':
        require(modules[name]['native'].read_bytes() == modules[name]['bun'].read_bytes(),
                ('native/Bun emitted bytes differ', name))
        item['byte_identical'] = True
    elif dispositions[0] == 'blocked':
        record['blocked'].append({'case': name, 'need': 'generics', 'unrun_calls': len(calls),
                                  'original_requirement': requirement['require']})


def boundary_probes(probes, lanes, modules):
    observations = []
    arena, tail = probes['arena'], probes['tail']
    for lane, commands in lanes.items():
        result = successful(['node', HERE / 'arena.mjs', modules[arena['case']][lane],
                             arena['entry'], arena['successful_calls'], arena['expected_tag'],
                             *arena['arguments']])
        require(json.loads(result['stdout']) == {
            'successful': arena['successful_calls'], 'overflow': arena['overflow_call'],
            'repeatedOverflow': True}, ('erased capture changed cell layout', result))
        observations.append({'case': 'erased-capture-layout', 'lane': lane, 'result': result})
        for entry in (tail['shallow'], tail['deep']):
            result = run(['node', *tail['node_flags'], HOST, PROFILE,
                          modules[tail['case']][lane], entry, *tail['arguments']])
            wasm(result, {'entry': entry, 'ordinals': tail['arguments'],
                          'result': {'tag': tail['expected_tag']}})
            observations.append({'case': 'tail-' + entry, 'lane': lane, 'result': result})
        path = HERE / 'fixtures/lambda-apply.bend'
        result = run([*commands['eval'], path, 'main', 0])
        diagnostic(result, 4, 'Exhausted\teval\t')
        observations.append({'case': 'evaluator-fuel', 'lane': lane, 'result': result})
        for name, budgets in [('emitter-depth', [65536, 512, 512, 0, 65536]),
                              ('output-capacity', [65536, 512, 512, 4096, 32])]:
            output = BUILD / f'{name}-{lane}.wasm'; output.write_bytes(MARKER)
            result = run([*commands['compile'], path, output, *budgets])
            diagnostic(result, 4, 'Exhausted\t' if name == 'emitter-depth' else 'Exhausted\temit\t')
            require(output.read_bytes() == MARKER, (name, 'exhaustion changed artifact'))
            observations.append({'case': name, 'lane': lane, 'result': result,
                                 'artifact_preserved': True})
        result = run([*commands['eval'], path, 'missing', 1048576])
        diagnostic(result, 5, 'HostFailure\t')
        observations.append({'case': 'unknown-entry', 'lane': lane, 'result': result})
    return observations


def mutants(frozen, probes):
    """Source replacements are filled only once closure lowering has stable names."""
    manifest_path = HERE / 'mutants.json'
    require(manifest_path.is_file(), 'The five required source mutants have not been wired.')
    definitions = json.loads(manifest_path.read_text())['mutants']
    required = {'wrong-dispatch-arm', 'capture-dropped', 'affine-capture-duplicated',
                'erased-capture-stored-live', 'tail-call-not-tail'}
    require({m['name'] for m in definitions} == required and len(definitions) == len(required),
            'Every required semantic mutant needs exactly one checked replacement')
    cases = {c['name']: c for c in frozen['cases']}
    calls = {f['case']: f['calls'] for f in frozen['observations']['fixtures']}
    observations = []
    for mutation in definitions:
        name = mutation['name']; directory = BUILD / name
        directory.mkdir(exist_ok=True)
        for source in (ROOT / 'src').glob('*.bend'):
            shutil.copy2(source, directory / source.name)
        changes = mutation['replacements'] if 'replacements' in mutation else [mutation]
        changed = {}
        require(changes, (name, 'a mutant needs a source change'))
        for change in changes:
            require(Path(change['file']).name == change['file'], 'mutants change copied source modules only')
            target = directory / change['file']
            text = target.read_text()
            require(text.count(change['old']) == 1 and change['old'] != change['new'],
                    (name, 'mutation must have a unique source anchor and change it'))
            target.write_text(text.replace(change['old'], change['new']))
            changed[change['file']] = digest(target)
        phase = mutation['phase']
        require(phase == ('check' if name == 'affine-capture-duplicated' else 'compile'),
                (name, 'mutant must run its intended compiler phase'))
        entry = directory / ('entry.bend' if phase == 'compile' else 'check-cli.bend')
        if phase == 'compile':
            entry.write_text(COMPILE.read_text().replace('../../src/', './'))
        checked = successful([*SEED, entry, '--check-only'])
        require(checked['stdout'] == 'All terms check.\n' and checked['stderr'] == '', checked)
        item = {'name': name, 'replacement': mutation, 'typecheck': checked,
                'source_sha256': changed, 'lanes': {}}
        for lane, suffix, runtime in LANES:
            executable = directory / ('mutant' + suffix)
            build = successful([*SEED, entry, '-o', executable])
            command = [*runtime, executable]
            row = {'build': build}
            if name == 'affine-capture-duplicated':
                witness = cases[mutation['case']]
                require(witness['knot'].get('diagnostic') == 'Invalid\tcheck\taffine-reuse\t',
                        'quantity mutant must contradict the frozen affine rejection')
                result = run([*command, HERE / witness['file']])
                require(classified(result) == 'success' and result['stdout'].startswith('Checked\n'),
                        ('quantity mutant did not exhibit its intended wrong acceptance', result))
                row['observation'] = result
            else:
                witness = mutation['case']
                source = HERE / ('probes' if name in ('erased-capture-stored-live', 'tail-call-not-tail') else 'fixtures') / (witness + '.bend')
                output = directory / (lane + '.wasm')
                emission = run([*command, source, output]); built(emission, output)
                successful(['wasm2wat', '--enable-tail-call', output])
                row['compile'] = emission
                if name == 'erased-capture-stored-live':
                    arena = probes['arena']
                    result = successful(['node', HERE / 'arena.mjs', output, arena['entry'],
                                         arena['successful_calls'], arena['expected_tag'], *arena['arguments']])
                    actual = json.loads(result['stdout'])
                    require(0 < actual['successful'] < arena['successful_calls']
                            and actual['overflow'] == actual['successful'] + 1
                            and actual['repeatedOverflow'] is True, ('erasure mutant survived', result))
                    row['observation'] = result
                elif name == 'tail-call-not-tail':
                    tail = probes['tail']
                    control = run(['node', *tail['node_flags'], HOST, PROFILE, output,
                                   tail['shallow'], *tail['arguments']])
                    wasm(control, {'entry': tail['shallow'], 'ordinals': tail['arguments'],
                                   'result': {'tag': tail['expected_tag']}})
                    result = run(['node', *tail['node_flags'], HOST, PROFILE, output,
                                  tail['deep'], *tail['arguments']])
                    diagnostic(result, 4, tail['mutant_diagnostic'])
                    row.update(shallow=control, observation=result)
                else:
                    matching = [c for c in calls[witness] if c['entry'] == mutation['entry']
                                and c['ordinals'] == mutation['arguments']]
                    require(len(matching) == 1, (name, 'mutant witness must be an immutable seed call'))
                    call = matching[0]
                    result = run(['node', HOST, PROFILE, output, call['entry'], *call['ordinals']])
                    require(classified(result) == 'success'
                            and json.loads(result['stdout'])['result'] != call['result']['tag'],
                            ('semantic mutant survived or failed for another reason', name, result))
                    row.update(expected=call['result'], observation=result)
            row['outcome'] = 'semantic-kill'
            item['lanes'][lane] = row
        observations.append(item)
    return observations


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(exist_ok=True)
    frozen = json.loads((HERE / 'expectations.json').read_text())
    probes = json.loads((HERE / 'probes.json').read_text())
    regressions = json.loads((HERE / 'regressions.json').read_text())
    refresh = json.loads((HERE / 'refresh.json').read_text())
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'incomplete', 'profile': PROFILE.removeprefix('--profile='),
              'fixtures': [], 'blocked': []}
    paths = [*sorted((ROOT / 'src').glob('*.bend')), ROOT / 'src/SPEC.md', ROOT / 'src/CONTRACT.json',
             COMPILE, HOST, *sorted(HERE.glob('*.py')), *sorted(HERE.glob('*.json')),
             *sorted(HERE.glob('*.md')),
             *sorted(HERE.glob('*.mjs')), *sorted((HERE / 'fixtures').glob('*.bend')),
             *sorted((HERE / 'probes').glob('*.bend')), *sorted((HERE / 'regressions').glob('*.bend')),
             *sorted((HERE / 'refresh').glob('*.bend')), *sorted((HERE / 'prechecks').glob('*.bend'))]
    record['inputs'] = {relative(p): digest(p) for p in paths}
    try:
        record['seed'] = frozen['seed']
        record['seed_inputs'] = frozen['observations']['seed_files']
        require(probes['seed'] == frozen['seed'], 'supplemental seed identity differs')
        require(regressions['seed'] == frozen['seed'], 'regression seed identity differs')
        require(regressions['seed_files'] == frozen['observations']['seed_files'],
                'regression seed files differ from the immutable suite')
        require(sorted(c['file'] for c in regressions['cases']) ==
                sorted(relative(p).removeprefix(relative(HERE) + '/')
                       for p in (HERE / 'regressions').glob('*.bend')),
                'regression sources and manifest differ')
        record['reference'] = successful(['python3', HERE / 'regen.py'])
        require(len(frozen['cases']) == 42 and sum(len(f['calls']) for f in frozen['observations']['fixtures']) == 292,
                'frozen corpus coverage changed')
        record['supplemental_reference'] = [seed_probe(p) for p in probes['probes']]
        record['regression_reference'] = [seed_regression(c) for c in regressions['cases']]
        record['refresh_reference'] = successful(['python3', HERE / 'refresh_seed.py'], timeout=600)
        refresh_counts = json.loads(record['refresh_reference']['stdout'])
        require(refresh_counts == {'programs': 32, 'accepted': 20, 'rejected': 12,
                                   'seed_checks': 32, 'seed_builds': 64, 'seed_runs': 40},
                ('frozen refresh coverage changed', refresh_counts))
        record['precheck_reference'] = successful(['python3', HERE / 'precheck_seed.py'], timeout=600)
        require(json.loads(record['precheck_reference']['stdout']) ==
                {'programs': 26, 'accepted': 6, 'rejected': 20, 'seed_parses': 26,
                 'seed_checks': 26, 'seed_builds': 52}, 'frozen precheck coverage changed')
        record['tools'] = {tool: successful([tool, '--version'])['stdout'].strip()
                           for tool in ('bun', 'node', 'python3', 'wasm2wat')}
        require(record['tools']['node'] == 'v22.22.3', record['tools'])
        record['proofs'] = []
        for family in ('closure-types', 'closure-check', 'closure', 'parse-visibility'):
            entry = ROOT / f'src/{family}-PROOF.bend'
            result = successful([*SEED, entry])
            require(result['stdout'] == 'All terms check.\n' and result['stderr'] == '', result)
            laws = re.findall(r'^law ([A-Za-z_][A-Za-z_0-9]*):',
                              (ROOT / f'src/{family}-LAWS.bend').read_text(), re.M)
            require(laws, (family, 'proof entry needs declared laws'))
            record['proofs'].append({'entry': relative(entry), 'result': result, 'laws': laws})
        record['proof'] = next(p['result'] for p in record['proofs']
                               if p['entry'] == 'src/closure-PROOF.bend')
        record['builds'], lanes = [], {}
        for lane, suffix, runtime in LANES:
            lanes[lane] = {}
            for phase, source in [('check', ROOT / 'src/check-cli.bend'),
                                  ('eval', ROOT / 'src/eval-cli.bend'), ('compile', COMPILE)]:
                output = BUILD / (phase + suffix)
                result = successful([*SEED, source, '-o', output])
                record['builds'].append({'lane': lane, 'phase': phase, 'result': result, 'sha256': digest(output)})
                lanes[lane][phase] = [*runtime, output]
        modules = {}
        calls = {f['case']: f['calls'] for f in frozen['observations']['fixtures']}
        for case in frozen['cases']:
            run_case(case, calls[case['name']], lanes, modules, record)
        for probe in probes['probes']:
            case = {'name': probe['name'], 'file': probe['file'], 'origin': 'supplemental',
                    'knot': {'require': 'agree'}}
            run_case(case, probe['calls'], lanes, modules, record)
        for case in regressions['cases']:
            run_case({**case, 'origin': 'regression'}, case['calls'], lanes, modules, record)
        for case in refresh['cases']:
            run_case({**case, 'origin': 'refresh'}, case['calls'], lanes, modules, record)
        record['boundaries'] = boundary_probes(probes, lanes, modules)
        record['mutants'] = mutants(frozen, probes)
        import precheck_replay
        record['prechecks'] = precheck_replay.replay(lanes)
        require(all(digest(ROOT / path) == value for path, value in record['inputs'].items()),
                'inputs changed while the closure gate ran')
        record['counts'] = {
            'frozen_fixtures': 42, 'seed_calls': 292, 'seed_rejections': 18,
            'supplemental_probes': len(probes['probes']),
            'supplemental_seed_calls': sum(len(p['calls']) for p in probes['probes']),
            'regression_fixtures': len(regressions['cases']),
            'regression_seed_calls': sum(len(c['calls']) for c in regressions['cases']),
            'regression_seed_rejections': sum(c['knot']['require'] == 'reject' for c in regressions['cases']),
            'regression_phase_observations': 3 * len(regressions['cases']) * len(LANES),
            'refresh_fixtures': len(refresh['cases']),
            'refresh_seed_checks': refresh_counts['seed_checks'],
            'refresh_seed_builds': refresh_counts['seed_builds'],
            'refresh_seed_calls': refresh_counts['seed_runs'],
            'refresh_seed_rejections': refresh_counts['rejected'],
            'refresh_phase_observations': 3 * len(refresh['cases']) * len(LANES),
            'agreed_fixtures': sum(f['disposition'] == 'agreed' for f in record['fixtures']),
            'rejected_fixtures': sum(f['disposition'] == 'rejected' for f in record['fixtures']),
            'blocked_fixtures': len(record['blocked']),
            'blocked_calls': sum(f['unrun_calls'] for f in record['blocked']),
            'check_observations': sum(len(f['lanes']) for f in record['fixtures']),
            'compile_observations': sum(len(f['lanes']) for f in record['fixtures']),
            'rejection_evaluator_observations': sum(len(f['lanes']) for f in record['fixtures']
                                                   if f['disposition'] != 'agreed'),
            'evaluator_calls': sum(len(lane['calls']) for f in record['fixtures'] for lane in f['lanes'].values()),
            'wasm_calls': sum(len(lane['calls']) for f in record['fixtures'] for lane in f['lanes'].values()),
            'byte_identity_checks': sum(f['disposition'] == 'agreed' for f in record['fixtures']),
            'boundary_probes': len(record['boundaries']), 'mutants': len(record['mutants']),
            'mutant_lane_kills': sum(len(m['lanes']) for m in record['mutants']),
            'proof_entries': len(record['proofs']),
            'checked_laws': sum(len(p['laws']) for p in record['proofs'])}
        record['counts']['prechecks'] = record['prechecks']['counts']
        record['qualification'] = 'blocked-prerequisites' if record['blocked'] else 'complete'
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print('Closures gate passed for available capabilities: ' + json.dumps(record['counts'], sort_keys=True))
    for blocked in record['blocked']:
        print(f"Blocked (not passed): {blocked['case']}: {blocked['need']}; {blocked['unrun_calls']} unrun calls")
    print(relative(RECEIPT))


if __name__ == '__main__':
    main()
