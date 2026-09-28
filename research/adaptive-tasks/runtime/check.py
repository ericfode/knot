#!/usr/bin/env python3
"""Run independent Bend observations and the bounded WGSL record interpreter."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SEED = ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts'
ENV = {**os.environ, 'BEND_NO_TELEMETRY': '1'}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run(args):
    p = subprocess.run([str(x) for x in args], cwd=ROOT, env=ENV,
                       capture_output=True, text=True, timeout=120)
    return {'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


def success(result):
    assert result['exit'] == 0, result
    return result['stdout']


def checked(path):
    result = run(['bun', SEED, path])
    assert 'All terms check.' in success(result), result
    return result


def imported(path, directory):
    name = os.path.relpath(path, directory)
    return name if name.startswith('.') else './' + name


def store_command(c):
    return "R.Command{" + ",".join(map(str, (c + [0, 0, 0])[:4])) + "}"


def frontier_command(c):
    return 'F.Command{' + ','.join(map(str, (c + [0, 0])[:3])) + '}'


def entry(path, fixtures, frontier):
    imports = [(frontier, 'F'), (HERE / 'slot-model.bend', 'R'),
               (ROOT / 'research/owned-store/model.bend', 'M'),
               (ROOT / 'research/owned-store/protocol.bend', 'P'),
               (ROOT / 'research/owned-store/store.bend', 'S')]
    lines = ['import Base'] + [f'import {imported(p, path.parent)} as {alias}' for p, alias in imports]
    lines += ['', 'def main() -> IO(Unit):', '  do IO<Unit>:']
    for f in fixtures['store']:
        for n in range(1, len(f['commands']) + 1):
            commands = ','.join(map(store_command, f['commands'][:n]))
            lines.append(f'    IO.print(R.start({f["arena"]},{f["capacity"]},{f["ceiling"]},[{commands}]))')
    for f in fixtures['frontier']:
        for n, command in enumerate(f['commands']):
            previous = ','.join(map(frontier_command, f['commands'][:n]))
            pc = f.get('initialPc', [0, 0])
            lines.append(f'    IO.print(F.trace({frontier_command(command)},F.run([{previous}],F.initial_at({f["capacity"]},{pc[0]},{pc[1]}))))')
    path.write_text('\n'.join(lines) + '\n')


def observations(text, fixtures):
    lines = iter(text.splitlines())
    cases = {}
    for f in fixtures['store']:
        # Presentation whitespace is not a store observation.
        trace = [[next(lines).replace(' ', '')] * 3 for _ in f['commands']]
        assert trace[-1][-1] == f['expected'], (f['name'], trace[-1][-1], f['expected'])
        cases[f['name']] = trace
    for f in fixtures['frontier']:
        trace = [json.loads(next(lines)) for _ in f['commands']]
        assert trace[-1][-1] == f['expected'], (f['name'], trace[-1][-1], f['expected'])
        cases[f['name']] = trace
    assert next(lines, None) is None, 'unexpected model output'
    return cases


MUTANTS = [
    ('erase-internal-fault', 'case True{} _: result(s,5,6,0)',
     'case True{} _: result(s,0,0,0)', 'fault_retains'),
    ('consume-full-owner', 'case False{} _: result(s,3,1,id)',
     'case False{} State{cap,tasks,queue,status,reason,reply}: State{cap,mark(tasks,id,2),queue,3,1,id}', 'offer_full'),
    ('duplicate-offer', 'Bool.or(U32.is_eq(p,1),U32.is_eq(p,4))',
     'Bool.or(U32.is_le(p,2),U32.is_eq(p,4))', 'offer_duplicate'),
    ('change-destination', 'case Task{id,3,pc,value,dest,slot,code} 0: Task{id,4,pc,value,dest,slot,code}',
     'case Task{id,3,pc,value,dest,slot,code} 0: Task{id,4,pc,value,0,slot,code}', 'zero_slice'),
    ('advance-zero-budget', 'case Task{id,3,pc,value,dest,slot,code} 0: Task{id,4,pc,value,dest,slot,code}',
     'case Task{id,3,pc,value,dest,slot,code} 0: Task{id,4,U32.add(pc,1),value,dest,slot,code}', 'zero_slice'),
    ('ignore-wait', 'case 1 Task{id,p,pc,value,dest,slot,code}: Task{id,5,U32.add(pc,1),value,dest,slot,code}',
     'case 1 Task{id,p,pc,value,dest,slot,code}: Task{id,4,U32.add(pc,1),value,dest,slot,code}', 'round_wait'),
    ('retain-consumed-frontier', 'State{cap,tasks,Nil{},0,reason,reply}',
     'State{cap,tasks,queue,0,reason,reply}', 'round_suspend'),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--cpu-only', action='store_true')
    mode.add_argument('--validate-only', action='store_true', help='Dawn null shader validation; never device evidence')
    parser.add_argument('--out-dir', type=Path, default=ROOT / '.local/adaptive-tasks/runtime')
    args = parser.parse_args()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    fixtures = json.loads((HERE / 'fixtures.json').read_text())
    reference = json.loads((ROOT / 'research/execution-models/reference-hashes.json').read_text())
    for name, expected in reference['files'].items():
        assert digest(SEED.parents[1] / name) == expected, name
    report = {'date': datetime.now(timezone.utc).isoformat(), 'contract': fixtures['contract'],
              'reference': reference, 'deviceExecution': False}
    report['proof'] = checked(HERE / 'PROOF.bend')
    model_entry = out / 'model-fixtures.bend'
    entry(model_entry, fixtures, HERE / 'frontier.bend')
    report['bun'] = run(['bun', SEED, model_entry])
    text = success(report['bun'])
    cases = observations(text, fixtures)
    binary = out / 'model-fixtures'
    report['nativeBuild'] = run(['bun', SEED, model_entry, '-o', binary])
    success(report['nativeBuild'])
    report['native'] = run([binary])
    assert success(report['native']) == text, 'native model disagreement'
    source_paths = [HERE / n for n in ['frontier.bend', 'slot-model.bend', 'LAWS.bend', 'PROOF.bend', 'fixtures.json', 'check.py']]
    source_paths += [ROOT / 'research/owned-store' / n for n in ['model.bend', 'protocol.bend', 'store.bend', 'bounds.bend']]
    sources = {str(p.relative_to(ROOT)): digest(p) for p in source_paths}
    model = {'fixturesSha256': digest(HERE / 'fixtures.json'), 'sources': sources, 'cases': cases}
    (out / 'model.json').write_text(json.dumps(model, indent=2) + '\n')
    report['sources'] = sources
    report['cases'] = {name: len(trace) for name, trace in cases.items()}
    report['mutants'] = []
    source = (HERE / 'frontier.bend').read_text()
    for name, old, replacement, law in MUTANTS:
        assert source.count(old) == 1, name
        folder = out / 'mutants' / name
        folder.mkdir(parents=True, exist_ok=True)
        for file in ['LAWS.bend', 'PROOF.bend']:
            proof_source = (HERE / file).read_text()
            proof_source = proof_source.replace('./slot-model.bend', imported(HERE / 'slot-model.bend', folder))
            proof_source = proof_source.replace('../../owned-store/protocol.bend', imported(ROOT / 'research/owned-store/protocol.bend', folder))
            (folder / file).write_text(proof_source)
        mutant = folder / 'frontier.bend'
        mutant.write_text(source.replace(old, replacement))
        checked(mutant)
        proof = run(['bun', SEED, folder / 'PROOF.bend'])
        diagnostic = proof['stdout'] + proof['stderr']
        assert proof['exit'] != 0 and law in diagnostic and 'expected' in diagnostic and 'observed' in diagnostic, proof
        witness = folder / 'fixtures.bend'
        entry(witness, fixtures, mutant)
        observed = success(run(['bun', SEED, witness]))
        assert observed != text, f'no runtime difference: {name}'
        try:
            observations(observed, fixtures)
        except AssertionError as mismatch:
            rejecting = str(mismatch)
        else:
            raise AssertionError(f'literal fixtures did not kill {name}')
        report['mutants'].append({'name': name, 'typechecks': True, 'law': law,
                                  'diagnostic': diagnostic, 'literalMismatch': rejecting, 'killed': True})
    report['laws'] = 8
    report['commands'] = sum(report['cases'].values())
    report['phaseObservations'] = report['commands'] * 3
    report['status'] = 'cpu-pass-device-unrun'
    if not args.cpu_only:
        command = ['node', ROOT / 'research/adaptive-tasks/gpu/runtime.mjs', '--model', out / 'model.json', '--out-dir', out]
        if args.validate_only:
            command.append('--validate-only')
        report['gpu'] = run(command)
        if report['gpu']['exit'] == 0:
            report['status'] = 'cpu-and-shader-validation-pass' if args.validate_only else 'pass'
            report['deviceExecution'] = not args.validate_only
        else:
            report['status'] = 'HostFailure' if 'HostFailure' in report['gpu']['stderr'] else 'InternalFailure'
    (out / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['status', 'laws', 'commands', 'phaseObservations', 'deviceExecution']} | {
        'storeCases': len(fixtures['store']), 'frontierCases': len(fixtures['frontier']), 'cpuMutantsKilled': len(report['mutants'])}))
    if 'gpu' in report:
        print(report['gpu']['stdout'], end='')
        assert report['gpu']['exit'] == 0, report['gpu']


if __name__ == '__main__':
    main()
