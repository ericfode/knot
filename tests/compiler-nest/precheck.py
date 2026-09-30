#!/usr/bin/env python3
"""Replay the exact precheck probes through seed, parser, checker, evaluator and both emitters."""
import json
from pathlib import Path
import shutil

import check as gate
import precheck_seed as seed

HERE = Path(__file__).resolve().parent
BUILD = gate.ROOT / '.local/compiler-nest/precheck'
RECEIPT = HERE / 'receipts/precheck.json'
FIXED = json.loads((HERE / 'precheck-expectations.json').read_text())
gate.SEED = ['bun', '--no-env-file', gate.SEED[-1]]
MUTANTS = (
    ('audit-bypassed', 'parse.bend',
     'S.bind(Parsed,Parsed,run(depth,Book{},tokens),tree => audited(depth,tree))',
     'run(depth,Book{},tokens)', 'forward-pattern', {'exit': 0}),
    ('event-order-ignored', 'catalog.bend',
     'Bool.or(Bool.and(String.eq(S.text(token),S.text(name)),U32.is_le(start(token),start(name))),prior_constructor(tail,name))',
     'Bool.or(String.eq(S.text(token),S.text(name)),prior_constructor(tail,name))', 'discarded-forward-pattern', {'exit': 0}),
    ('expression-treated-as-pattern', 'parse.bend',
     'S.choose(Result<S.Error,Unit>,pattern,u =>',
     'S.choose(Result<S.Error,Unit>,True{},u =>', 'forward-expression',
     {'exit': 2, 'diagnostic': 'Invalid\tcheck\tunknown-constructor\t'}),
)


def parse_result(actual, expected):
    if expected['exit'] == 0:
        gate.require(actual['exit'] == 0 and actual['stdout'].startswith('Parsed\t') and not actual['stderr'], actual)
    else:
        gate.diagnostic(actual, expected)


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    for name, file, before, after, witness, wrong in MUTANTS:
        gate.require((gate.ROOT / 'src' / file).read_text().count(before) == 1, ('mutation anchor', name))
    gate.BUILD = BUILD
    seed_pin = json.loads((HERE / 'round13-expectations.json').read_text())['seed']
    for file, digest in seed_pin['sha256'].items():
        gate.require(gate.digest(gate.ROOT / '.toolchain/bend-2.0.29-574b6d3' / file) == digest,
                     ('seed identity', file))
    inputs = [*(gate.ROOT / 'src').glob('*.bend'), Path(__file__), HERE / 'precheck_seed.py',
              HERE / 'check.py', HERE / 'precheck-expectations.json', *[gate.ROOT / f['file'] for f in FIXED['fixtures']]]
    record = {'schema': 1, 'status': 'running', 'seed': seed_pin,
              'inputs': {str(p.relative_to(gate.ROOT)): gate.digest(p) for p in inputs},
              'builds': [], 'fixtures': [], 'mutants': []}
    lanes = gate.build_lanes(record)
    for lane, commands in lanes.items():
        if lane == 'bun':
            for command in commands.values():
                command.insert(1, '--no-env-file')
        output = BUILD / ('parse.js' if lane == 'bun' else 'parse')
        result = gate.successful(['bun', '--no-env-file', *gate.SEED[1:], gate.ROOT / 'src/parse-cli.bend', '-o', output])
        record['builds'].append({'lane': lane, 'phase': 'parse', 'result': result, 'sha256': gate.digest(output)})
        commands['parse'] = ['bun', '--no-env-file', output] if lane == 'bun' else [output]
    paths = [gate.ROOT / case['file'] for case in FIXED['fixtures']]
    parsed = seed.seed_parse(paths)
    for case, path, observed in zip(FIXED['fixtures'], paths, parsed):
        gate.require(gate.digest(path) == case['sha256'], ('changed fixture', case['name']))
        gate.require(observed == case['seed_parse'], (case['name'], 'seed parse drift', observed))
        reference = seed.seed_check(path)
        gate.require(all(reference[k] == case['seed_check'][k] for k in ('exit', 'stdout', 'stderr')), reference)
        item = {'name': case['name'], 'seed_parse': observed, 'seed_check': reference, 'lanes': {}}
        for lane, commands in lanes.items():
            expected = case['knot']
            outputs = {}
            for phase in ('parse', 'check', 'eval', 'enum', 'fields'):
                args = [path]
                artifact = BUILD / f"{case['name']}-{lane}-{phase}.wasm"
                marker = b'prior artifact\n'
                if phase == 'eval':
                    args += ['main', 65536]
                if phase in ('enum', 'fields'):
                    artifact.write_bytes(marker)
                    args += [artifact]
                actual = gate.run([*commands[phase], *args])
                if phase == 'parse':
                    parse_result(actual, expected)
                elif expected['exit'] != 0:
                    gate.diagnostic(actual, expected)
                elif phase == 'check':
                    gate.checked(actual)
                elif phase == 'eval':
                    gate.require(actual['exit'] == 0 and not actual['stderr'] and actual['stdout'].rstrip().endswith('\t1\tOn{}'), actual)
                else:
                    gate.require(actual['exit'] == 0 and not actual['stderr'] and actual['stdout'].strip() == f'Built\t{artifact.stat().st_size}', actual)
                    execution = gate.successful(['node', gate.HOST, artifact, 'main'])
                    gate.require(json.loads(execution['stdout'])['result'] == 1, execution)
                    outputs[phase + '_wasm'] = execution
                if phase in ('enum', 'fields') and expected['exit'] != 0:
                    gate.require(artifact.read_bytes() == marker, ('artifact changed', actual))
                outputs[phase] = actual
            item['lanes'][lane] = outputs
        record['fixtures'].append(item)
    pool = {case['name']: case for case in FIXED['fixtures']}
    for name, file, before, after, witness, wrong in MUTANTS:
        directory = BUILD / name
        directory.mkdir(exist_ok=True)
        for source in (gate.ROOT / 'src').glob('*.bend'):
            shutil.copy2(source, directory / source.name)
        target = directory / file
        text = target.read_text()
        gate.require(text.count(before) == 1, ('mutation anchor', name))
        target.write_text(text.replace(before, after))
        entry = directory / 'parse-cli.bend'
        checked = gate.successful(['bun', '--no-env-file', *gate.SEED[1:], entry, '--check-only'])
        item = {'name': name, 'typecheck': checked, 'witness': witness, 'lanes': {}}
        for lane in ('native', 'bun'):
            output = directory / ('parse.js' if lane == 'bun' else 'parse')
            built = gate.successful(['bun', '--no-env-file', *gate.SEED[1:], entry, '-o', output])
            command = ['bun', '--no-env-file', output] if lane == 'bun' else [output]
            actual = gate.run([*command, gate.ROOT / pool[witness]['file']])
            parse_result(actual, wrong)
            try:
                parse_result(actual, pool[witness]['knot'])
            except AssertionError:
                item['lanes'][lane] = {'build': built, 'result': actual, 'killed': True}
            else:
                raise AssertionError(('surviving mutant', name, lane))
        record['mutants'].append(item)
    record['proof'] = gate.successful(['bun', '--no-env-file', *gate.SEED[1:], gate.ROOT / 'src/PROOF.bend'])
    record.update(status='passed', counts={'fixtures': 10, 'seed_parse_observations': 10,
                  'seed_check_observations': 10, 'phase_observations': 100,
                  'preserved_artifacts': 32, 'evaluator_values': 4, 'wasm_values': 8,
                  'mutants': 3, 'semantic_kills': 6, 'proof_entries': 1})
    RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print('Nest precheck gate passed: ' + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
