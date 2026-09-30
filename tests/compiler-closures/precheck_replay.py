"""Exercise seed-frozen C1 witnesses through the real compiler CLI lanes."""
from __future__ import annotations

import json
from pathlib import Path
import shutil

import check as gate

MUTANTS = (
    ('unclosed-family-refused', 'closure-types.bend',
     'case _: Fail{S.Invalid{"parse",code,S.at(open)}}',
     'case _: unsupported(Read,[open],code)', '87039ce5820e1495', 3),
    ('parameter-comma-required', 'parse.bend',
     'Bool.and(parameters,parameter_prefix(tokens))', 'False{}', 'e7f55ae9e39f6d41', 2),
    ('late-pattern-accepted', 'parse-visibility.bend',
     'Bool.and(pattern,Bool.not(declared(names,token)))', 'False{}', 'pattern-forward-complete', 0),
)


def replay(lanes):
    frozen = json.loads((gate.HERE / 'prechecks.json').read_text())
    record = {'cases': [], 'mutants': [], 'counts': {'programs': len(frozen['cases']),
              'parse_observations': 0, 'check_observations': 0,
              'eval_observations': 0, 'compile_observations': 0,
              'host_result_refusals': 0, 'wasm_calls': 0, 'byte_identity_checks': 0,
              'mutants': len(MUTANTS), 'mutant_lane_kills': 0}}
    directory = gate.BUILD / 'prechecks'
    directory.mkdir(exist_ok=True)
    parsers = {}
    for lane, suffix, runtime in gate.LANES:
        output = directory / ('parse' + suffix)
        build = gate.successful([*gate.SEED, gate.ROOT / 'src/parse-cli.bend', '-o', output])
        parsers[lane] = [*runtime, output]
        record.setdefault('builds', []).append({'lane': lane, 'result': build})
    for case in frozen['cases']:
        path = gate.HERE / case['file']
        gate.require(gate.digest(path) == case['source_sha256'], ('precheck source drift', case['name']))
        item = {'name': case['name'], 'lanes': {}}
        outputs = []
        for lane, commands in lanes.items():
            parsed = gate.run([*parsers[lane], path])
            expected = {'Parsed': 0, 'Invalid': 2, 'Unsupported': 3}[case['parse']]
            gate.require(parsed['exit'] == expected, ('precheck parse', case['name'], parsed))
            gate.classified(parsed)
            checked = gate.run([*commands['check'], path])
            gate.classified(checked)
            gate.require(checked['exit'] == expected, ('precheck check', case['name'], checked))
            output = directory / (case['name'] + '-' + lane + '.wasm')
            output.write_bytes(gate.MARKER)
            compiled = gate.run([*commands['compile'], path, output])
            gate.classified(compiled)
            gate.require(compiled['exit'] == expected, ('precheck compile', case['name'], compiled))
            row = {'parse': parsed, 'check': checked, 'compile': compiled}
            item['lanes'][lane] = row
            for phase in ('parse', 'check', 'compile'):
                record['counts'][phase + '_observations'] += 1
            if expected:
                gate.require(parsed['stderr'] == checked['stderr'] == compiled['stderr']
                             and output.read_bytes() == gate.MARKER, ('refusal consistency', case['name'], row))
                evaluated = gate.run([*commands['eval'], path, 'main', 65536])
                gate.require(evaluated['exit'] == expected and evaluated['stderr'] == parsed['stderr'],
                             ('precheck eval refusal', case['name'], evaluated))
                row['eval'] = evaluated
                record['counts']['eval_observations'] += 1
            else:
                gate.built(compiled, output)
                gate.successful(['wasm2wat', '--enable-tail-call', output])
                outputs.append(output.read_bytes())
                seed_run = case['seed'].get('run')
                if seed_run is None:
                    continue
                evaluated = gate.run([*commands['eval'], path, 'main', 65536])
                row['eval'] = evaluated
                record['counts']['eval_observations'] += 1
                if case['name'] == 'b507406b7c59d768':
                    gate.require(evaluated['exit'] == 5 and evaluated['stdout'] == ''
                                 and evaluated['stderr'] == 'HostFailure\tinvoke\tfunction-result\n',
                                 ('frozen function-result host boundary', evaluated))
                    record['counts']['host_result_refusals'] += 1
                else:
                    gate.require(seed_run['stdout'] == 'On{}\n', ('independent seed value', case))
                    gate.evaluator(evaluated, {'result': {'type': 'Flag', 'tag': 1, 'constructor': 'On'}})
                    executed = gate.run(['node', gate.HOST, gate.PROFILE, output, 'main'])
                    gate.wasm(executed, {'entry': 'main', 'ordinals': [], 'result': {'tag': 1}})
                    row['wasm'] = executed
                    record['counts']['wasm_calls'] += 1
        if outputs:
            gate.require(len(outputs) == len(gate.LANES) and len(set(outputs)) == 1,
                         ('precheck module lane disagreement', case['name']))
            record['counts']['byte_identity_checks'] += 1
        record['cases'].append(item)
    cases = {c['name']: c for c in frozen['cases']}
    for name, file, old, new, witness, wrong_exit in MUTANTS:
        mutant = directory / name
        mutant.mkdir(exist_ok=True)
        for source in (gate.ROOT / 'src').glob('*.bend'):
            shutil.copy2(source, mutant / source.name)
        target = mutant / file
        text = target.read_text()
        gate.require(text.count(old) == 1 and old != new, ('unique precheck mutant', name))
        target.write_text(text.replace(old, new))
        entry = mutant / 'parse-cli.bend'
        checked = gate.successful([*gate.SEED, entry, '--check-only'])
        gate.require(checked['stdout'] == 'All terms check.\n' and not checked['stderr'], checked)
        item = {'name': name, 'file': file, 'old': old, 'new': new,
                'witness': witness, 'source_sha256': gate.digest(target), 'typecheck': checked, 'lanes': {}}
        for lane, suffix, runtime in gate.LANES:
            output = mutant / ('parse' + suffix)
            built = gate.successful([*gate.SEED, entry, '-o', output])
            result = gate.run([*runtime, output, gate.HERE / cases[witness]['file']])
            gate.classified(result)
            gate.require(result['exit'] == wrong_exit, ('mutant did not exhibit intended wrong verdict', name, result))
            if wrong_exit:
                code = 'function-result' if name == 'unclosed-family-refused' else 'argument-separator'
                gate.require(result['stderr'].startswith(gate.OUTCOMES[wrong_exit] + '\tparse\t' + code + '\t'), result)
            else:
                gate.require(result['stdout'].startswith('Parsed\t'), result)
            item['lanes'][lane] = {'build': built, 'observation': result, 'outcome': 'semantic-kill'}
            record['counts']['mutant_lane_kills'] += 1
        record['mutants'].append(item)
    return record
