"""Replay seed-frozen precheck probes without changing earlier expectations."""
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent


def rows(gate):
    document = json.loads((HERE / 'expectations.json').read_text())
    for name in ('reported-expectations.json', 'review-r0-expectations.json',
                 'review-r0-layout-guards.json', 'review-r0-named-guard.json',
                 'template-tail-expectations.json'):
        reported = json.loads((HERE / name).read_text())
        gate.require(all(document[key] == reported[key] for key in ('seed_revision', 'seed_files')),
                     (name, 'reported probes use the same pinned seed'))
        document['cases'] += reported['cases']
    result = []
    for case in document['cases']:
        source = HERE / case['file']
        gate.require(gate.digest(source) == case['sha256'], (case['name'], 'frozen source'))
        requirement = {'require': 'agree' if 'value' in case else 'reject', **case['expected']['check']}
        # This seed-valid book may remain Unsupported on its independent body.
        if 'allowed_exits' in requirement:
            requirement['require'] = 'agree-or-unsupported'
        result.append({'source': source, 'case': {'name': case['name'], 'knot': requirement,
                       'parse': case['expected']['parse']}, 'reference': {'calls': []}, 'control': case})
    return document, result


def outcome(gate, actual, expected):
    wanted = expected.get('allowed_exits', [expected.get('exit')])
    gate.require(actual['exit'] in wanted, (expected, actual))
    if actual['exit'] == 0:
        gate.require(actual['stderr'] == '', actual)
    else:
        # Four TSV fields; punctuation in the established code is permitted.
        fields = actual['stderr'].rstrip('\n').split('\t')
        gate.require(actual['stdout'] == '' and len(fields) == 4, actual)
        gate.require(fields[0] == {2: 'Invalid', 3: 'Unsupported'}[actual['exit']], actual)
        gate.require(fields[1].islower() and fields[2]
                     and not re.search(r'[\x00-\x1f\x7f]', fields[2])
                     and re.fullmatch(r'\d+:\d+:\d+:\d+', fields[3]), actual)
    if 'diagnostic' in expected:
        gate.require(actual['stderr'].startswith(expected['diagnostic']), (expected, actual))


def replay(gate, lanes):
    document, probes = rows(gate)
    for file, frozen in document['seed_files'].items():
        gate.require(gate.digest(gate.ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2' / file) == frozen,
                     (file, 'seed identity'))
    paths = [str(p['source'].relative_to(gate.ROOT)) for p in probes]
    parsed = gate.successful(['bun', HERE / 'seed-parse.ts',
              (gate.ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/bend.ts').resolve(), *paths])
    observations = json.loads(parsed['stdout'])
    gate.require(len(observations) == len(probes), 'seed parser observation inventory')
    record = {'fixtures': [], 'seed_parse_observations': len(probes), 'seed_check_observations': 0,
              'seed_runs': 0, 'lane_observations': 0, 'preserved_artifacts': 0,
              'evaluator_agreements': 0, 'wasm_agreements': 0, 'byte_identical_modules': 0,
              'seed_constructor_observations': 0, 'boxed_module_validations': 0}
    for probe, path, seed_parse in zip(probes, paths, observations):
        case, source = probe['control'], probe['source']
        gate.require(seed_parse == case['seed']['parse'], (case['name'], 'seed parse drift', seed_parse))
        seed_check = gate.run([*gate.SEED, path, '--check-only'])
        gate.require({k: seed_check[k] for k in ('exit', 'stdout', 'stderr')} == case['seed']['check'],
                     (case['name'], 'seed check drift', seed_check))
        record['seed_check_observations'] += 1
        if 'run' in case['seed']:
            seed_run = gate.run([*gate.SEED, path])
            gate.require({k: seed_run[k] for k in ('exit', 'stdout', 'stderr')} == case['seed']['run'],
                         (case['name'], 'seed value drift', seed_run))
            record['seed_runs'] += 1
        if 'constructor' in case['seed']:
            raw = gate.successful(['bun', HERE / 'seed-value.ts',
                  (gate.ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/bend.ts').resolve(), path])
            gate.require(json.loads(raw['stdout']) == case['seed']['constructor'],
                         (case['name'], 'seed constructor drift', raw))
            record['seed_constructor_observations'] += 1
        row = {'name': case['name'], 'sha256': case['sha256'], 'seed_parse': seed_parse,
               'seed_check': seed_check, 'lanes': {}}
        modules = []
        for lane, commands in lanes.items():
            output = gate.BUILD / f'precheck-{case["name"]}-{lane}.wasm'
            output.write_bytes(gate.MARKER)
            actual = {'parse': gate.run([*commands['parse'], source]),
                      'check': gate.run([*commands['check'], source]),
                      'eval': gate.run([*commands['eval'], source, 'main', 1048576]),
                      'compile': gate.run([*commands['compile'], source, output])}
            outcome(gate, actual['parse'], case['expected']['parse'])
            if actual['parse']['exit'] == 0:
                gate.require(actual['parse']['stdout'].startswith('Parsed\t'), actual['parse'])
            for phase in ('check', 'eval', 'compile'):
                outcome(gate, actual[phase], case['expected']['check'])
            if 'value' in case:
                gate.checked(actual['check'])
                gate.compiled(actual['compile'], output)
                tag = case.get('tag', 1)
                rendered = case.get('rendered_value', case['value'])
                gate.require(re.fullmatch(r'Evaluated\t\d+\t' + str(tag) + r'\t' +
                                          re.escape(rendered) + r'\n', actual['eval']['stdout']), actual)
                if case.get('abi', 'enum') == 'enum':
                    host = gate.run(['node', gate.HOST, gate.PROFILE, output, 'main'])
                    gate.require(host['exit'] == 0 and host['stderr'] == ''
                                 and json.loads(host['stdout']) == {'validated': True, 'export': 'main',
                                     'arguments': [], 'result': tag, 'bytes': output.stat().st_size}, host)
                    actual['wasm'] = host
                    record['wasm_agreements'] += 1
                else:
                    # A cell address is not an enum ordinal. Validate the module
                    # without pretending this host ABI decodes the boxed value.
                    validation = gate.successful(['node', '--input-type=module', '-e',
                        'import fs from "node:fs"; const b = fs.readFileSync(process.argv[1]); '
                        'if (!WebAssembly.validate(b)) throw new Error("invalid Wasm"); '
                        'const m = await WebAssembly.compile(b); '
                        'if (WebAssembly.Module.imports(m).length) throw new Error("unexpected imports"); '
                        'console.log(JSON.stringify({validated:true,bytes:b.length}));', output])
                    gate.require(json.loads(validation['stdout']) ==
                                 {'validated': True, 'bytes': output.stat().st_size}, validation)
                    actual['wasm_validation'] = validation
                    record['boxed_module_validations'] += 1
                modules.append(output.read_bytes())
                record['evaluator_agreements'] += 1
            else:
                gate.require(actual['check']['exit'] != 0, (case['name'], 'unmodeled control must not execute'))
                gate.require(output.read_bytes() == gate.MARKER, (case['name'], 'artifact changed'))
                record['preserved_artifacts'] += 1
            record['lane_observations'] += 4
            row['lanes'][lane] = actual
        if modules:
            gate.require(len(modules) == len(lanes) and len(set(modules)) == 1, (case['name'], 'module drift'))
            record['byte_identical_modules'] += 1
        record['fixtures'].append(row)
    return record
