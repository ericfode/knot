#!/usr/bin/env python3
"""Run frozen review regressions through Bend check/eval/compile entries."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORK = ROOT / '.local/baseslice/review/knot'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


seed = load('baseslice_review_seed', HERE / 'regen.py')
require, run, sha, relative = seed.require, seed.run, seed.sha, seed.relative

MUTANTS = (
    ('global-annotations', 'catalog.bend', 'named(seen,name),u =>\n    C.invalid(TypeRef',
     'False{},u =>\n    C.invalid(TypeRef', 'shadow-result', 'accepted seed-rejected annotation'),
    ('dotted-typed-let', 'parse.bend', 'S.dotted(S.text(name)),u =>', 'False{},u =>',
     'dotted-affine', 'accepted seed-rejected typed let'),
    ('free-function-value', 'check.bend', 'u => global_variable(sigs,token))',
     'u => E.lookup(scope,token))', 'function-value', 'false Invalid on seed-valid function value'),
)


def refusal(observation, code, diagnostic):
    require(observation['exit'] == code and observation['stdout'] == ''
            and observation['stderr'].startswith(diagnostic), (code, diagnostic, observation))


def compile_refusal(command, source, output, code, diagnostic):
    output.unlink(missing_ok=True)
    observation = run([*command, source, relative(output)])
    refusal(observation, code, diagnostic)
    require(not output.exists(), 'refusal emitted an artifact')
    sentinel = b'baseslice review existing output\n'
    output.write_bytes(sentinel)
    existing = run([*command, source, relative(output)])
    refusal(existing, code, diagnostic)
    require(output.read_bytes() == sentinel, 'refusal modified existing output')
    return {'new_output': observation, 'existing_output': existing,
            'preserved_sha256': sha(sentinel)}


def observe(case, commands, lane):
    source = relative(HERE / 'fixtures' / (case['name'] + '.bend'))
    output = WORK / lane / (case['name'] + '.wasm')
    output.parent.mkdir(parents=True, exist_ok=True)
    checked = run([*commands['check'], source])
    row = {'check': checked}
    if case['require'] != 'agree':
        refusal(checked, case['exit'], case['diagnostic'])
        row['eval'] = run([*commands['eval'], source, 'main', '65536'])
        refusal(row['eval'], case['exit'], case['diagnostic'])
        row['compile'] = compile_refusal(commands['compile'], source, output,
                                         case['exit'], case['diagnostic'])
        return row
    require(checked['exit'] == 0 and checked['stderr'] == ''
            and checked['stdout'].startswith('Checked\n'), checked)
    row['eval'] = run([*commands['eval'], source, 'main', '65536'])
    require(row['eval'] == {'exit': 0, 'stderr': '',
                           'stdout': f'Evaluated\t{case["type_id"]}\t{case["tag"]}\t{case["constructor"]}{{}}\n'},
            (case, row['eval']))
    if 'compile_diagnostic' in case:
        row['compile'] = compile_refusal(commands['compile'], source, output,
                                         case['compile_exit'], case['compile_diagnostic'])
        return row
    output.unlink(missing_ok=True)
    row['compile'] = run([*commands['compile'], source, relative(output)])
    require(output.is_file() and row['compile'] == {'exit': 0, 'stderr': '',
            'stdout': f'Built\t{output.stat().st_size}\n'}, row['compile'])
    row['wasm_sha256'] = sha(output.read_bytes())
    observation = run(['node', 'scripts/run-wasm.mjs', relative(output), 'main'])
    require(observation['exit'] == 0 and observation['stderr'] == '', observation)
    row['wasm'] = json.loads(observation['stdout'])
    require(row['wasm']['validated'] is True and row['wasm']['arguments'] == []
            and row['wasm']['export'] == 'main' and row['wasm']['result'] == case['tag'], row['wasm'])
    return row


def mutant(spec, build):
    name, file, old, new, witness, kill = spec
    work = WORK / 'mutants' / name
    sources = work / 'src'
    sources.mkdir(parents=True, exist_ok=True)
    for source in sorted((ROOT / 'src').glob('*.bend')):
        shutil.copyfile(source, sources / source.name)
    target = sources / file
    text = target.read_text()
    require(text.count(old) == 1, ('changed mutant anchor', name))
    target.write_text(text.replace(old, new))
    binary = work / 'check'
    built = build(relative(sources / 'check-cli.bend'), binary)
    observation = run(['./' + relative(binary), relative(HERE / 'fixtures' / (witness + '.bend'))])
    if name == 'free-function-value':
        refusal(observation, 2, 'Invalid\tcheck\tfree-name\t')
    else:
        require(observation['exit'] == 0 and observation['stderr'] == ''
                and observation['stdout'].startswith('Checked\n'), observation)
    return {'name': name, 'file': file, 'source_sha256': sha(target.read_bytes()),
            'build': built, 'witness': witness, 'observation': observation, 'kill': kill}


def check(commands, build):
    document = json.loads(seed.EXPECTATIONS.read_text())
    minor = json.loads((HERE / 'empty-datatype.json').read_text())
    record = {'status': 'incomplete'}
    paths = [HERE / name for name in ('regen.py', 'check.py', 'expectations.json',
                                     'LAWS.bend', 'PROOF.bend', 'trust.ts', 'bounds-oracle.py',
                                     'receipts/bounds-amendment.json', 'empty-datatype.json')]
    paths += sorted((HERE / 'fixtures').glob('*.bend'))
    paths += sorted((ROOT / 'src').glob('*.bend'))
    paths.append(ROOT / 'scripts/run-wasm.mjs')
    paths.append(ROOT / 'tests/compiler-checker/bounds.bend')
    record['inputs'] = {relative(p): sha(p.read_bytes()) for p in paths}
    require(seed.observations(document) == document['observations'], 'review seed oracle changed')
    require(seed.observations(minor) == minor['observations'], 'empty-datatype seed oracle changed')
    record['seed_reproduced'] = True
    record['seed'] = document['observations']['seed_files']
    record['bounds_amendment'] = run(['python3', '-B', relative(HERE / 'bounds-oracle.py')])
    require(record['bounds_amendment'] == {'exit': 0, 'stderr': '',
            'stdout': 'bounds amendment: four frozen seed witnesses reproduced\n'}, record['bounds_amendment'])
    proof = run(['bun', relative(HERE / 'trust.ts')])
    require(proof['exit'] == 0 and proof['stderr'] == '', proof)
    record['proof'] = json.loads(proof['stdout'])
    record['fixtures'] = []
    cases = document['cases'] + minor['cases']
    for case in cases:
        lanes = {lane: observe(case, drivers, lane) for lane, drivers in commands.items()}
        if 'wasm_sha256' in lanes['native']:
            require(lanes['native']['wasm_sha256'] == lanes['bun']['wasm_sha256'],
                    ('review modules differ', case['name']))
        record['fixtures'].append({'name': case['name'], 'require': case['require'], 'lanes': lanes})
    record['mutants'] = [mutant(m, build) for m in MUTANTS]
    agreed = sum(c['require'] == 'agree' for c in cases)
    compiled = sum(c['require'] == 'agree' and 'compile_diagnostic' not in c for c in cases)
    refused = len(cases) - compiled
    record['counts'] = {'fixtures': len(cases), 'agreed_books': agreed,
                        'rejected_books': sum(c['require'] == 'reject' for c in cases),
                        'unsupported_books': sum(c['require'] == 'unsupported' for c in cases),
                        'lane_observations': len(cases) * 6,
                        'evaluator_observations': agreed * 2, 'wasm_observations': compiled * 2,
                        'byte_identical_modules': compiled, 'output_preservation_checks': refused * 2,
                        'laws': len(record['proof']['laws']), 'proof_holes': record['proof']['holes'],
                        'mutants': len(record['mutants']), 'amendment_seed_witnesses': 4}
    record['status'] = 'pass'
    return record


def main():
    # Standalone targeted run; the registered base-enum gate passes its fresh
    # drivers to check() instead, without building an extra compiler family.
    import sys
    sys.path.insert(0, str(HERE.parent / 'enum'))
    api = load('baseslice_enum_check', HERE.parent / 'enum/check.py')
    commands, builds = {}, []
    for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
        commands[lane] = {}
        for phase in ('check', 'eval', 'compile'):
            binary = WORK / lane / (phase + suffix)
            builds.append({'lane': lane, 'phase': phase,
                           **api.build(f'src/{phase}-cli.bend', binary)})
            commands[lane][phase] = [*runtime, './' + relative(binary)]
    record = check(commands, api.build)
    record['builds'] = builds
    output = WORK / 'review.json'
    output.write_text(json.dumps(record, indent=2) + '\n')
    print('baseslice review: PASS ' + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
