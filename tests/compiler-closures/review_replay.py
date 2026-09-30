"""Drive the seed-frozen review corpus through both real compiler lanes."""
from __future__ import annotations

import json
import shutil
import statistics
import time

import check as gate

# A wide-call mutant is killed by its decoded, unsafe lowering before execution.
# A V8 abort is host failure evidence, never a semantic mutation kill.
MUTANTS = (
    ('split-type-accepted', 'closure-types.bend', 'S.adjacent(dash,arrow)', 'True{}',
     'check', 'split-type-result', 0),
    ('split-lambda-accepted', 'parse.bend',
     'Bool.and(lambda_arrow(tokens),S.adjacent(equal,arrow))', 'lambda_arrow(tokens)',
     'check', 'split-lambda-result', 0),
    ('shadowed-type-accepted', 'catalog.bend',
     'Bool.and(Bool.not(S.matches(name,"_")),named(seen,name))', 'False{}',
     'check', 'shadow-let', 0),
    ('semicolon-lambda-invalid', 'parse.bend',
     'Bool.pick(String,starts(tokens,";"),";","\\n")', '"\\n"',
     'check', 'layout-semicolon', 2),
    ('wide-return-call', 'wasm.bend',
     'S.choose(Result<S.Error,Code>,narrow(params),u =>',
     'S.choose(Result<S.Error,Code>,True{},u =>',
     'compile', 'wide-partial-39', None),
)


def replay(lanes, with_mutants=True):
    frozen = json.loads((gate.HERE / 'review-r1.json').read_text())
    record = {'fixtures': [], 'blocked': [], 'mutants': [], 'performance': []}
    modules = {}
    for case in frozen['cases']:
        path = gate.HERE / case['file']
        gate.require(gate.digest(path) == case['source_sha256'], ('review source drift', case['name']))
        calls = ([{'entry': 'main', 'ordinals': [],
                   'result': {'type': 'T', 'tag': case['result'], 'constructor': 'K'}}]
                 if case['knot']['require'] == 'agree' else [])
        gate.run_case({**case, 'origin': 'review-r1'}, calls, lanes, modules, record)
        if case['area'] == 'wide-tail':
            for lane, output in modules[case['name']].items():
                wat = gate.successful(['wasm2wat', '--enable-tail-call', output])['stdout']
                gate.require('return_call 0' not in wat, ('wide target must use ordinary call', case['name'], lane))
                for host in (['node', '--liftoff-only', '--no-wasm-tier-up'],
                             ['node', '--no-liftoff'], ['bun', '--no-env-file']):
                    actual = gate.run([*host, gate.HOST, gate.PROFILE, output, 'main'])
                    gate.wasm(actual, calls[0])
                    record.setdefault('wide_host_controls', []).append(
                        {'case': case['name'], 'lane': lane, 'observation': actual})
        if case['area'] == 'performance':
            native = lanes['native']['compile']
            output = gate.BUILD / (case['name'] + '-timing.wasm')
            samples = []
            for _ in range(3):
                begin = time.monotonic()
                actual = gate.run([*native, path, output], timeout=30)
                seconds = time.monotonic() - begin
                gate.built(actual, output)
                gate.require(output.read_bytes() == modules[case['name']]['native'].read_bytes(),
                             ('timed output drift', case['name']))
                samples.append({'seconds': seconds, 'observation': actual})
            record['performance'].append({'case': case['name'], 'samples': samples,
                'median_seconds': statistics.median(row['seconds'] for row in samples),
                'module_sha256': gate.digest(output),
                'limit': '30-second external hang guard; timings are observations, not a complexity proof'})
    cases = {c['name']: c for c in frozen['cases']}
    if with_mutants:
        for name, file, old, new, phase, witness, wrong_exit in MUTANTS:
            directory = gate.BUILD / 'review-r1-mutants' / name
            directory.mkdir(parents=True, exist_ok=True)
            for source in (gate.ROOT / 'src').glob('*.bend'):
                shutil.copy2(source, directory / source.name)
            target = directory / file
            source = target.read_text()
            gate.require(source.count(old) == 1, ('unique review mutant', name))
            target.write_text(source.replace(old, new))
            entry = directory / ('entry.bend' if phase == 'compile' else 'check-cli.bend')
            if phase == 'compile':
                entry.write_text(gate.COMPILE.read_text().replace('../../src/', './'))
            checked = gate.successful([*gate.SEED, entry, '--check-only'])
            gate.require(checked['stdout'] == 'All terms check.\n' and not checked['stderr'], checked)
            item = {'name': name, 'witness': witness, 'typecheck': checked,
                    'file': file, 'old': old, 'new': new, 'source_sha256': gate.digest(target), 'lanes': {}}
            for lane, suffix, runtime in gate.LANES:
                executable = directory / ('mutant' + suffix)
                build = gate.successful([*gate.SEED, entry, '-o', executable])
                argv = [*runtime, executable, gate.HERE / cases[witness]['file']]
                if phase == 'compile':
                    output = directory / (lane + '.wasm')
                    actual = gate.run([*argv, output])
                    gate.built(actual, output)
                    decoded = gate.successful(['wasm2wat', '--enable-tail-call', output])
                    gate.require('return_call 0' in decoded['stdout'], ('unsafe-lowering mutant survived', name))
                    row = {'build': build, 'observation': actual, 'decoded': decoded,
                           'outcome': 'lowering-safety-kill', 'execution': 'not attempted'}
                else:
                    actual = gate.run(argv)
                    gate.classified(actual)
                    gate.require(actual['exit'] == wrong_exit, ('review mutant survived', name, actual))
                    if wrong_exit == 0:
                        gate.require(actual['stdout'].startswith('Checked\n'), actual)
                    else:
                        gate.require(actual['stderr'].startswith('Invalid\tparse\texpected-\n\t'), actual)
                    row = {'build': build, 'observation': actual, 'outcome': 'semantic-kill'}
                item['lanes'][lane] = row
            record['mutants'].append(item)
    record['counts'] = dict(programs=len(frozen['cases']),
        agreed_fixtures=sum(f['disposition'] == 'agreed' for f in record['fixtures']),
        rejected_fixtures=sum(f['disposition'] == 'rejected' for f in record['fixtures']),
        check_observations=2 * len(frozen['cases']), compile_observations=2 * len(frozen['cases']),
        evaluator_observations=2 * len(frozen['cases']),
        wasm_calls=2 * sum(c['knot']['require'] == 'agree' for c in frozen['cases']),
        byte_identity_checks=len(modules), wide_host_controls=len(record.get('wide_host_controls', [])),
        timing_samples=sum(len(p['samples']) for p in record['performance']),
        mutants=len(record['mutants']),
        semantic_mutant_lane_kills=sum(row['outcome'] == 'semantic-kill'
            for m in record['mutants'] for row in m['lanes'].values()),
        lowering_safety_lane_kills=sum(row['outcome'] == 'lowering-safety-kill'
            for m in record['mutants'] for row in m['lanes'].values()))
    return record
