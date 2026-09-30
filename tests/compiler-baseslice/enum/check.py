#!/usr/bin/env python3
"""BS1: drive existing Bend compilers on pinned Base source, with frozen oracles."""
from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import re
import shutil

import regen

HERE, ROOT = regen.HERE, regen.ROOT
WORK = ROOT / '.local/baseslice/enum/knot'
RECEIPT = HERE / 'receipts/enum.json'
HOST = 'scripts/run-wasm.mjs'
require, run, sha, relative = regen.require, regen.run, regen.sha, regen.relative

# Each change is a type-correct compiler defect. The frozen witness, not a
# parser/build error or timeout, must reject it for the named observation.
MUTANTS = [
    ('zero-tags', 'wasm.bend', 'W.positive_signed(cap,tag)', 'W.positive_signed(cap,0)',
     'compile', 'boolean', 'neg', [0]),
    ('inverted-case', 'wasm.bend', 'W.bytes(cap,[70,4,127])', 'W.bytes(cap,[71,4,127])',
     'compile', 'boolean', 'neg', [0]),
    ('aliased-arguments', 'wasm.bend',
     'parameters(tail,U32.add(level,1),U32.add(index,1),Con{Local{level,index},locals})',
     'parameters(tail,U32.add(level,1),U32.add(index,1),Con{Local{level,0},locals})',
     'compile', 'boolean', 'conjunction', [1, 0]),
    ('constant-evaluator', 'eval.bend', 'Done{Return{Value{type_id,tag},frames}}',
     'Done{Return{Value{type_id,0},frames}}', 'eval', 'boolean', 'neg', [0]),
    ('lost-type-boundary', 'check.bend', 'U32.is_eq(type_id,actual),u => Done{value}',
     'True{},u => Done{value}', 'check', 'wrong-type', None, []),
]


def successful(argv):
    obs = run(argv)
    require(obs['exit'] == 0 and obs['stderr'] == '', (argv, obs))
    return obs


def build(entry, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    for _ in range(3):
        obs = run([*regen.SEED, entry, '-o', relative(output)])
        if not (obs['exit'] != 0 and 'bend needs clang' in obs['stderr']):
            break
    require(obs['exit'] == 0 and output.is_file(), ('compiler build failure', entry, obs))
    return {'entry': entry, 'sha256': sha((ROOT / entry).read_bytes()), 'observation': obs}


def evaluated(obs, typ, answer):
    expected = f'Evaluated\t{typ}\t{answer["tag"]}\t{answer["constructor"]}{{}}\n'
    return obs == {'exit': 0, 'stdout': expected, 'stderr': ''}


def enum_observation(obs, typ, constructors):
    require(obs['exit'] == 0 and obs['stderr'] == '', obs)
    match = re.fullmatch(r'Evaluated\t(\d+)\t(\d+)\t(\w+)\{\}\n', obs['stdout'])
    require(match and int(match[1]) == typ and int(match[2]) < len(constructors)
            and constructors[int(match[2])] == match[3], ('unclassified enum observation', obs))
    return int(match[2]), match[3]


def compile(command, source, output):
    output.unlink(missing_ok=True)
    obs = successful([*command, source, relative(output)])
    require(output.is_file() and obs['stdout'] == f'Built\t{output.stat().st_size}\n', obs)
    require(output.read_bytes()[:8] == b'\0asm\x01\0\0\0', 'Wasm binary header')
    return obs


def wasm(output, call):
    obs = successful(['node', HOST, relative(output), call['entry'], *call['ordinals']])
    value = json.loads(obs['stdout'])
    require(value['validated'] is True and value['export'] == call['entry']
            and value['arguments'] == call['ordinals'], ('host invocation', value))
    return value


def refusal(obs, code, diagnostic):
    require(obs['exit'] == code and obs['stdout'] == '' and obs['stderr'].startswith(diagnostic),
            ('refusal does not match frozen requirement', code, diagnostic, obs))


def observe(case, frozen, commands, document, lane):
    source = relative(HERE / 'fixtures' / (case['name'] + '.bend'))
    out = WORK / lane / (case['name'] + '.wasm')
    out.parent.mkdir(parents=True, exist_ok=True)
    checked = run([*commands['check'], source])
    row = {'check': checked}
    if case['require'] == 'agree':
        require(checked['exit'] == 0 and checked['stderr'] == '' and checked['stdout'].startswith('Checked\n'), checked)
        row['compile'] = compile(commands['compile'], source, out)
        row['wasm_sha256'] = sha(out.read_bytes())
        row['calls'] = []
        for call, want in zip(case['calls'], frozen['calls'], strict=True):
            obs = run([*commands['eval'], source, call['entry'], '65536', *call['ordinals']])
            answer = want['result']
            require(evaluated(obs, document['type_ids'][call['result_type']], answer),
                    ('evaluation differs from the frozen seed', case['name'], call, answer, obs))
            value = wasm(out, call)
            require(value['result'] == answer['tag'],
                    ('Wasm differs from the frozen seed', case['name'], call, answer, value))
            row['calls'].append({'entry': call['entry'], 'ordinals': call['ordinals'],
                                 'eval': obs, 'wasm': value})
    else:
        code = 2 if case['require'] == 'reject' else 3
        refusal(checked, code, case['diagnostic'])
        row['eval'] = run([*commands['eval'], source, 'main', '65536'])
        refusal(row['eval'], code, case['diagnostic'])
        out.unlink(missing_ok=True)
        row['compile'] = run([*commands['compile'], source, relative(out)])
        refusal(row['compile'], code, case['diagnostic'])
        require(not out.exists(), 'refusal created an artifact')
        sentinel = b'BS1 existing output must remain untouched\n'
        out.write_bytes(sentinel)
        row['existing_output'] = run([*commands['compile'], source, relative(out)])
        refusal(row['existing_output'], code, case['diagnostic'])
        require(out.read_bytes() == sentinel, 'refusal changed an existing output')
        row['preserved_sha256'] = sha(sentinel)
    return row


def mutate(mutant, document):
    name, file, old, new, phase, case_name, entry, ordinals = mutant
    work = WORK / 'mutants' / name
    sources = work / 'src'
    sources.mkdir(parents=True, exist_ok=True)
    for source in sorted((ROOT / 'src').glob('*.bend')):
        shutil.copyfile(source, sources / source.name)
    target = sources / file
    text = target.read_text()
    require(text.count(old) == 1, ('mutant anchor changed', name))
    target.write_text(text.replace(old, new))
    binary = work / phase
    built = build(relative(sources / (phase + '-cli.bend')), binary)
    command = ['./' + relative(binary)]
    source = relative(HERE / 'fixtures' / (case_name + '.bend'))
    if phase == 'check':
        obs = run([*command, source])
        # A classified acceptance is the witnessed type-checker mistake; neither
        # a compiler diagnostic nor a host failure can count as this semantic kill.
        require(obs['exit'] == 0 and obs['stderr'] == '' and obs['stdout'].startswith('Checked\n'),
                ('mutant must exhibit acceptance of the seed-rejected bad type', name, obs))
        return {'name': name, 'phase': phase, 'file': file, 'source_sha256': sha(target.read_bytes()),
                'build': built, 'witness': case_name, 'observation': obs, 'kill': 'accepted seed-rejected type boundary'}
    case = next(c for c in document['cases'] if c['name'] == case_name)
    i = next(i for i, c in enumerate(case['calls']) if c['entry'] == entry and c['ordinals'] == ordinals)
    call = case['calls'][i]
    frozen = next(f for f in document['observations']['fixtures'] if f['case'] == case_name)
    answer = frozen['calls'][i]['result']
    if phase == 'eval':
        obs = successful([*command, source, entry, '65536', *ordinals])
        # Successful enum observation of the right type, but the wrong value.
        actual = enum_observation(obs, document['type_ids'][call['result_type']],
                                  document['constructors'][call['result_type']])
        require(actual != (answer['tag'], answer['constructor']),
                ('surviving evaluator mutant', name, obs))
    else:
        out = work / 'mutant.wasm'
        compile(command, source, out)
        obs = wasm(out, call)
        require(obs['result'] != answer['tag'], ('surviving Wasm mutant', name, obs))
    return {'name': name, 'phase': phase, 'file': file, 'source_sha256': sha(target.read_bytes()),
            'build': built, 'witness': {'case': case_name, 'entry': entry, 'ordinals': ordinals},
            'expected': answer, 'observation': obs, 'kill': 'classified value disagreement'}


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    document = json.loads(regen.EXPECTATIONS.read_text())
    record = {'schema': 1, 'status': 'incomplete', 'step': document['step'], 'profile': 'knot-enum-1'}
    try:
        paths = [regen.EXPECTATIONS, HERE / 'regen.py', HERE / 'check.py', HERE / 'trust.ts',
                 HERE / 'LAWS.bend', HERE / 'PROOF.bend', ROOT / HOST,
                 *sorted((ROOT / 'src').glob('*.bend')), *sorted((HERE / 'fixtures').glob('*.bend'))]
        record['inputs'] = {relative(p): sha(p.read_bytes()) for p in paths}
        require(regen.observations(document) == document['observations'], 'frozen seed observations changed')
        record['seed_reproduced'] = True
        record['seed'] = document['observations']['seed_files']
        record['declarations'] = document['declarations']
        record['proof'] = json.loads(successful(['bun', relative(HERE / 'trust.ts')])['stdout'])
        record['builds'], commands = [], {}
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
            commands[lane] = {}
            for phase in ('check', 'eval', 'compile'):
                binary = WORK / lane / (phase + suffix)
                record['builds'].append({'lane': lane, 'phase': phase,
                                         **build(f'src/{phase}-cli.bend', binary)})
                commands[lane][phase] = [*runtime, './' + relative(binary)]
        record['fixtures'] = []
        for case, frozen in zip(document['cases'], document['observations']['fixtures'], strict=True):
            require(case['name'] == frozen['case'], 'frozen case order')
            row = {'case': case['name'], 'require': case['require'], 'lanes': {}}
            for lane in commands:
                row['lanes'][lane] = observe(case, frozen, commands[lane], document, lane)
            if case['require'] == 'agree':
                require(row['lanes']['native']['wasm_sha256'] == row['lanes']['bun']['wasm_sha256'],
                        ('compiler lanes emitted different modules', case['name']))
            record['fixtures'].append(row)
        record['mutants'] = [mutate(m, document) for m in MUTANTS]
        review_path = HERE.parent / 'review/check.py'
        spec = importlib.util.spec_from_file_location('baseslice_review_check', review_path)
        review = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(review)
        record['review'] = review.check(commands, build)
        record['inputs'].update(record['review']['inputs'])
        calls = sum(len(c.get('calls', [])) for c in document['cases'] if c['require'] == 'agree')
        record['counts'] = {'declarations': len(record['declarations']), 'fixtures': len(record['fixtures']),
                            'agreed_books': 2, 'rejected_books': 4, 'deferred_books': 1,
                            'seed_calls': 32, 'seed_lane_observations': 64, 'reference_calls': calls,
                            'evaluator_observations': calls * 2, 'wasm_observations': calls * 2,
                            'byte_identical_modules': 2, 'execution_lanes': 2,
                            'laws': len(record['proof']['laws']), 'proof_holes': record['proof']['holes'],
                            'mutants': len(record['mutants']), 'output_preservation_checks': 10}
        record['counts'].update({'review_' + k: v for k, v in record['review']['counts'].items()})
        record['status'] = 'pass'
    except Exception as error:
        record['status'], record['error'] = 'failed', repr(error)
        raise
    finally:
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print('base-enum: PASS ' + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
