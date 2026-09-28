#!/usr/bin/env python3
"""Qualify record transitions; CPU, shader validation, and device evidence differ."""
import argparse
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from boundaries import cases as boundary_cases
from bundle import DEFAULT, initial_words
from reference import Reference
from validation import controls
from driver import Driver

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SEED = ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts'
ENV = {**os.environ, 'BEND_NO_TELEMETRY': '1', 'BEND_HUB': 'offline://disabled',
       'BEND_ORIGIN': 'offline://disabled', 'PYTHONDONTWRITEBYTECODE': '1'}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def run(args, timeout=240):
    try:
        result = subprocess.run(list(map(str, args)), cwd=ROOT, env=ENV,
                                capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as failure:
        raise RuntimeError(f'Exhausted host-timeout: {args[0]}') from failure
    except OSError as failure:
        raise RuntimeError(f'HostFailure launch: {failure}') from failure
    return {'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}


def success(result):
    if result['exit'] != 0:
        diagnostic = result['stdout'] + result['stderr']
        for kind in ('HostFailure', 'Exhausted'):
            if kind in diagnostic:
                raise RuntimeError(f'{kind}: {diagnostic}')
        raise AssertionError(result)
    return result['stdout']


def checked(path):
    result = run(['bun', SEED, path])
    assert 'All terms check.' in success(result), result
    return result


def imported(path, directory):
    name = os.path.relpath(path, directory)
    return name if name.startswith('.') else './' + name


def configuration(fixture):
    return {**DEFAULT, **fixture.get('config', {}),
            'instructionCount': len(fixture['commands'])}


def command_words(command):
    assert len(command) <= 8
    return command + [0] * (8 - len(command))


def entry(path, fixtures, model=HERE):
    lines = ['import Base',
             f'import {imported(model / "protocol.bend", path.parent)} as P',
             f'import {imported(model / "model.bend", path.parent)} as M', '',
             'def selected(+index: U32, samples: List<&2,U32>) -> Bool:',
             '  match samples:',
             '    case Nil{}: False{}',
             '    case Con{head,tail}: Bool.or(U32.is_eq(index,head),selected(index,tail))', '',
             'def fills(size: Nat, +index: U32) -> List<&2,P.Command>:',
             '  match size:',
             '    case 0n: Nil{}',
             '    case 1n+size: Con{P.Command{1,index,0,U32.add(index,1),0,0,0,0},fills(size,U32.add(index,1))}', '',
             'def trace(commands: List<&2,P.Command>, +samples: List<&2,U32>, +index: U32, state: P.State) -> IO(Unit):',
             '  match commands:',
             '    case Nil{}: IO.pure(Unit,Unit{})',
             '    case Con{head,tail}:',
             '      +after = M.step(head,state)',
             '      do IO<Unit>:',
             '        IO.print(P.choose(String,selected(index,samples),u => M.observe(after),u => U32.show(P.status(after))))',
             '        trace(tail,samples,U32.add(index,1),after)', '',
             'def main() -> IO(Unit):', '  do IO<Unit>:']
    fields = ['objects', 'captures', 'pending', 'joins', 'arity', 'rcLimit',
              'idLimit', 'attemptLimit', 'instructionCount']
    for fixture in fixtures:
        config = configuration(fixture)
        commands = ','.join('P.Command{' + ','.join(map(str, command_words(c))) + '}'
                            for c in fixture['commands'])
        command_list = (f'fills(U32.to_nat({len(fixture["commands"])}),0)'
                        if fixture['name'].startswith('objects-') and fixture['name'].endswith('-plus-one')
                        else f'[{commands}]')
        samples = fixture.get('observeIndexes', list(range(len(fixture['commands']))))
        initial = 'P.Config{' + ','.join(str(config[k]) for k in fields) + '}'
        lines.append(f'    trace({command_list},[{",".join(map(str,samples))}],0,P.initial({initial}))')
    lines.append('    IO.pure(Unit,Unit{})')
    path.write_text('\n'.join(lines) + '\n')


def literal(fixture, rows):
    expected = fixture['expect']
    statuses = [row[0] if isinstance(row, list) else row for row in rows]
    assert statuses == expected['statuses'], (fixture['name'], 'statuses', statuses, expected['statuses'])
    for index, value in expected.get('replies', {}).items():
        assert rows[int(index)][1] == value, (fixture['name'], 'reply', index)
    if 'ordered' in expected:
        control = expected['ordered']
        observation = rows[control['step']]
        objects = {o[0]: o for o in observation[5] if o}
        slots = observation[8][control['join']][8]
        tags = [objects[identity][3] for identity in slots]
        value = 0
        for tag in tags:
            value = value * 100 + tag
        assert tags == control['tags'] and value == control['base100'], (fixture['name'], 'order')
    if 'final' in expected:
        final = expected['final']
        row = rows[-1]
        for name, index in (('nextIdentity', 2), ('freed', 4), ('pending', 7)):
            assert row[index] == final[name], (fixture['name'], name, row[index], final[name])
        assert sum(bool(obj) for obj in row[5]) == final['live'], (fixture['name'], 'live')
        captures = {str(i): ref for i, ref in enumerate(row[6]) if ref}
        assert captures == final['captures'], (fixture['name'], 'captures', captures)
        for index, value in final.get('joins', {}).items():
            assert row[8][int(index)] == value, (fixture['name'], 'join', index, row[8][int(index)], value)


def host_observations(fixtures):
    data = []
    for fixture in fixtures:
        reference = Reference(configuration(fixture))
        samples = set(fixture.get('observeIndexes', range(len(fixture['commands']))))
        rows = []
        for index, command in enumerate(fixture['commands']):
            observation = reference.step(command)
            rows.append(observation if index in samples else observation[0])
        literal(fixture, rows)
        data.append(rows)
    return data


def observations(text, fixtures):
    lines = iter(text.splitlines())
    result = []
    for fixture in fixtures:
        rows = [json.loads(next(lines)) for _ in fixture['commands']]
        literal(fixture, rows)
        result.append(rows)
    assert next(lines, None) is None, 'unexpected model output'
    return result


def cpu_mutants(out, fixtures):
    mutants = json.loads((HERE / 'bend-mutants.json').read_text())
    result = []
    for mutant in mutants:
        directory = out / 'mutants' / mutant['name']
        directory.mkdir(parents=True, exist_ok=True)
        for source in HERE.glob('*.bend'):
            shutil.copy2(source, directory / source.name)
        source = directory / mutant['file']
        text = source.read_text()
        assert text.count(mutant['old']) == 1, mutant['name']
        source.write_text(text.replace(mutant['old'], mutant['new']))
        checked(directory / 'model.bend')
        witness = [f for f in fixtures if f['name'] == mutant['witness']]
        assert len(witness) == 1, mutant
        test = directory / 'witness.bend'
        entry(test, witness, directory)
        observed = success(run(['bun', SEED, test]))
        try:
            observations(observed, witness)
            assert observations(observed, witness) == host_observations(witness), 'host-reference-disagreement'
        except AssertionError as mismatch:
            rejection = str(mismatch)
        else:
            raise AssertionError(f'mutant survived: {mutant["name"]}')
        proof = run(['bun', SEED, directory / 'PROOF.bend'])
        diagnostic = proof['stdout'] + proof['stderr']
        if mutant.get('law'):
            assert proof['exit'] != 0 and mutant['law'] in diagnostic, proof
        result.append({'name': mutant['name'], 'typechecks': True, 'killed': True,
                       'witness': mutant['witness'], 'rejection': rejection,
                       'proofRejected': proof['exit'] != 0, 'proofDiagnostic': diagnostic})
    return result


def programs(out):
    fixtures = json.loads((HERE / 'programs.json').read_text())['cases']
    rows = []
    lines = ['import Base', f'import {imported(HERE / "protocol.bend", out)} as P',
             f'import {imported(HERE / "driver.bend", out)} as D', '',
             'def rounds(quanta: List<&2,U32>, +code: List<&2,P.Command>, frame: D.Frame) -> IO(Unit):',
             '  match quanta:', '    case Nil{}: IO.pure(Unit,Unit{})',
             '    case Con{head,tail}:', '      +after = D.run(U32.to_nat(head),code,frame)',
             '      do IO<Unit>:', '        IO.print(D.observe(after))', '        rounds(tail,code,after)', '',
             'def main() -> IO(Unit):', '  do IO<Unit>:']
    for fixture in fixtures:
        config = configuration(fixture)
        driver = Driver(config, fixture['commands'])
        observed = [driver.run(quantum) for quantum in fixture['quanta']]
        literal_control = fixture['expect']
        for field in ('pc', 'phase'):
            assert [row[field] for row in observed] == literal_control[field], (fixture['name'], field)
        for field, index in (('status', 0), ('reply', 1)):
            assert [row['state'][index] for row in observed] == literal_control[field], (fixture['name'], field)
        assert {str(i):v for i,v in enumerate(observed[-1]['state'][6]) if v} == literal_control['captures']
        rows.extend(observed)
        commands = ','.join('P.Command{' + ','.join(map(str, command_words(c))) + '}' for c in fixture['commands'])
        values = [config[key] for key in ('objects','captures','pending','joins','arity',
                                          'rcLimit','idLimit','attemptLimit','instructionCount')]
        lines.append(f'    rounds([{",".join(map(str,fixture["quanta"]))}],[{commands}],D.initial(P.Config{{{",".join(map(str,values))}}}))')
        fixture['observations'] = observed
        fixture['config'] = {key: config[key] for key in DEFAULT}
        fixture['commands'] = [command_words(c) for c in fixture['commands']]
        fixture['words'] = initial_words(fixture['config'], len(fixture['commands']))
    lines.append('    IO.pure(Unit,Unit{})')
    source = out / 'programs.bend'
    source.write_text('\n'.join(lines) + '\n')
    text = success(run(['bun', SEED, source]))
    assert [json.loads(line) for line in text.splitlines()] == rows, 'Bend / host program driver disagreement'
    binary = out / 'programs'
    success(run(['bun', SEED, source, '-o', binary]))
    assert success(run([binary])) == text, 'native program driver disagreement'
    (out / 'programs.txt').write_text(text)
    return fixtures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--cpu-only', action='store_true')
    mode.add_argument('--validate-only', action='store_true')
    parser.add_argument('--out-dir', type=Path, default=ROOT / '.local/gpu-2/runtime2')
    parser.add_argument('--receipt', type=Path, help='explicit receipt destination; defaults to output/checks.json')
    args = parser.parse_args()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {'contract': 'knot-device-records-2', 'date': datetime.now(timezone.utc).isoformat(),
              'status': 'running', 'scope': 'cpu', 'deviceExecution': False}
    try:
        seed = json.loads((ROOT / 'research/execution-models/reference-hashes.json').read_text())
        for name, expected in seed['files'].items():
            assert digest(SEED.parents[1] / name) == expected, name
        report['reference'] = seed
        report['proof'] = checked(HERE / 'PROOF.bend')
        report['laws'] = sum(line.startswith('law ') for path in HERE.glob('*LAWS.bend') for line in path.read_text().splitlines())
        report['host_boundaries'] = controls()
        fixtures = json.loads((HERE / 'fixtures.json').read_text())['cases'] + boundary_cases()
        expected = host_observations(fixtures)
        model_entry = out / 'observations.bend'
        entry(model_entry, fixtures)
        print('runtime2: host controls pass; running Bend Bun/native differential', file=sys.stderr)
        bun = run(['bun', SEED, model_entry], timeout=600)
        text = success(bun)
        actual = observations(text, fixtures)
        assert actual == expected, 'Bend Bun / independent host disagreement'
        binary = out / 'observations'
        report['nativeBuild'] = run(['bun', SEED, model_entry, '-o', binary], timeout=600)
        success(report['nativeBuild'])
        native = run([binary], timeout=600)
        assert success(native) == text, 'Bend native / Bun disagreement'
        transcript = gzip.compress(text.encode(), mtime=0)
        (out / 'observations.txt.gz').write_bytes(transcript)
        report['transcriptSha256'] = sha256(text.encode()).hexdigest()
        report['fixtures'] = [{'name': f['name'], 'commands': len(f['commands']),
            'snapshots': sum(isinstance(row, list) for row in rows),
            'observationSha256': sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest()}
            for f, rows in zip(fixtures, actual)]
        report['commands'] = sum(row['commands'] for row in report['fixtures'])
        report['snapshots'] = sum(row['snapshots'] for row in report['fixtures'])
        report['mutants'] = cpu_mutants(out, fixtures)
        program_rows = programs(out)
        report['programs'] = [{'name': f['name'], 'rounds': len(f['quanta'])} for f in program_rows]
        report['programRounds'] = sum(row['rounds'] for row in report['programs'])
        report['sources'] = {str(p.relative_to(ROOT)): digest(p) for p in sorted(HERE.iterdir())
            if p.is_file() and p.suffix in ('.bend', '.py', '.json', '.mjs', '.wgsl', '.md')}
        model = {'contract': report['contract'], 'sources': report['sources'], 'cases': [], 'programs': program_rows}
        for f, rows in zip(fixtures, actual):
            config = configuration(f)
            wire_config = {key: config[key] for key in DEFAULT}
            model['cases'].append({'name': f['name'], 'config': wire_config,
                'words': initial_words(wire_config, len(f['commands'])),
                'commands': [command_words(c) for c in f['commands']],
                'observations': [row if isinstance(row, list) else None for row in rows]})
        write(out / 'model.json', model)
        if not args.cpu_only:
            command = ['node', HERE / 'device.mjs', '--model', out / 'model.json', '--out-dir', out]
            if args.validate_only:
                command.append('--validate-only')
            report['gpu'] = run(command, timeout=600)
            success(report['gpu'])
            report['scope'] = 'cpu-and-shader-validation' if args.validate_only else 'cpu-and-device'
            report['deviceExecution'] = not args.validate_only
        report['status'] = 'pass'
    except Exception as failure:
        message = str(failure)
        report['status'] = next((kind for kind in ('HostFailure', 'Exhausted') if message.startswith(kind)), 'InternalFailure')
        report['error'] = message
        raise
    finally:
        write(args.receipt or out / 'checks.json', report)
        if args.receipt and report['status'] == 'pass':
            for name in ('observations.txt.gz', 'programs.txt'):
                shutil.copy2(out / name, args.receipt.parent / name)
    print(json.dumps({key: report[key] for key in ('status', 'scope', 'laws', 'commands', 'snapshots', 'programRounds', 'deviceExecution')} |
                     {'fixtures': len(report['fixtures']), 'cpuMutantsKilled': len(report['mutants']),
                      'hostBoundaries': len(report['host_boundaries']), 'programs': len(report['programs'])}))


if __name__ == '__main__':
    main()
