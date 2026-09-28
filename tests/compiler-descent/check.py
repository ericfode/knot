#!/usr/bin/env python3
"""Compare frozen observations across seed, Bend and Wasm; no language semantics."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/compiler-descent/gate'
RECEIPT = HERE / 'receipts/descent.json'
REFERENCE = HERE / 'receipts/reference.json'
RESOURCE_REFERENCE = HERE / 'receipts/resources-reference.json'
SEED_DIR = ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2'
SEED = ['bun', SEED_DIR / 'main.ts']
HOST = ROOT / 'scripts/run-wasm.mjs'
PROFILE = '--profile=knot-fields-wasm-1'
LANES = [('native', '', []), ('bun', '.js', ['bun'])]
PHASES = ('check', 'eval', 'compile')
STATUSES = {'Invalid': 2, 'Unsupported': 3, 'Exhausted': 4,
            'HostFailure': 5, 'InternalFailure': 6}
MARKER = b'existing artifact: a rejected compilation must preserve these bytes\n'


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(paths):
    return {str(path.relative_to(ROOT)): digest(path) for path in sorted(set(paths))}


def input_paths(manifest):
    return [*sorted((ROOT / 'src').glob('*.bend')),
            ROOT / 'src/SPEC.md', ROOT / 'src/CONTRACT.json',
            *sorted(HERE.glob('*.py')), HERE / 'expectations.json', HERE / 'mutants.json',
            HERE / 'bounds.json', HERE / 'work-bounds.json', HERE / 'bounds.bend',
            HERE / 'resources.json', RESOURCE_REFERENCE,
            *sorted((HERE / 'resources').glob('*.bend')),
            REFERENCE, HOST, ROOT / 'tests/compiler-fields-wasm/compile.bend',
            *(ROOT / case['file'] for case in manifest['fixtures'] + manifest['legacy']),
            *sorted(SEED_DIR.glob('*.ts')), SEED_DIR / 'base.bend']


def run(argv, timeout=120):
    command = [str(arg) for arg in argv]
    try:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                                timeout=timeout,
                                env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
        return {'argv': command, 'exit': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired as error:
        def text(value):
            return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
        return {'argv': command, 'exit': None, 'outcome': 'harness-timeout',
                'stdout': text(error.stdout), 'stderr': text(error.stderr)}
    except OSError as error:
        return {'argv': command, 'exit': None, 'outcome': 'harness-launch-error',
                'stdout': '', 'stderr': str(error)}


def successful(result):
    require(result['exit'] == 0 and not result['stderr'], result)
    return result


def line(result, expected):
    successful(result)
    require(result['stdout'] in (expected, expected + '\n'), (expected, result))


def observe(result, expected, phase):
    require(result['exit'] == expected['exit'], (expected, result))
    if expected['exit'] != 0:
        prefix = expected['diagnostic']
        category = prefix.split('\t', 1)[0]
        require(STATUSES.get(category) == expected['exit'], ('diagnostic status', expected))
        require(not result['stdout'] and len(result['stderr'].splitlines()) == 1
                and result['stderr'].startswith(prefix), (expected, result))
        return
    successful(result)
    if phase == 'check':
        require(result['stdout'].startswith('Checked\n')
                and result['stdout'][len('Checked\n'):].strip(), result)
    if 'stdout' in expected:
        line(result, expected['stdout'])
    if 'contains' in expected:
        require(expected['contains'] in result['stdout'], (expected, result))


def validate_manifest(manifest):
    cases = manifest['fixtures'] + manifest['legacy']
    names = {case['name'] for case in cases}
    require(len(names) == len(cases), 'Duplicate case names')
    require({str(path.relative_to(ROOT)) for path in (HERE / 'fixtures').glob('*.bend')}
            == {case['file'] for case in manifest['fixtures']}, 'Fixture manifest mismatch')
    by_name = {case['name']: case for case in cases}
    for case in cases:
        for phase in PHASES:
            expected = case[phase]
            require(expected['exit'] == 0 or 'diagnostic' in expected,
                    ('missing diagnostic', case['name'], phase))
        if case['check']['exit'] == 0:
            require(case['eval']['exit'] == case['compile']['exit'] == 0,
                    ('accepted phase contract', case['name']))
            require(('wasm' in case) != ('wasm_observer' in case),
                    ('one Wasm observation route required', case['name']))
        else:
            require(all(case[phase]['exit'] != 0 for phase in PHASES),
                    ('rejected source accepted by a later phase', case['name']))
        if 'wasm_observer' in case:
            observer = by_name.get(case['wasm_observer'])
            require(observer is not None and observer['check']['exit'] == 0
                    and 'wasm' in observer, ('missing Wasm observer', case['name']))
        if 'control' in case:
            require(case['control'] in by_name and by_name[case['control']]['check']['exit'] == 0,
                    ('missing positive control', case['name']))
    return cases


def verify_reference(record, cases):
    fixed = json.loads(REFERENCE.read_text())
    require(fixed['status'] == 'passed', 'Seed reference is not passed')
    require(fixed['inputs'] == hashes([HERE / 'expectations.json',
                                      *(ROOT / case['file'] for case in cases)]),
            'Frozen expectations or fixtures changed')
    require(fixed['seed'] == hashes(SEED_DIR.glob('*.ts')), 'Frozen seed changed')
    require([item['name'] for item in fixed['observations']] == [case['name'] for case in cases],
            'Frozen observation coverage differs')
    record['reference'] = {'file': str(REFERENCE.relative_to(ROOT)), 'sha256': digest(REFERENCE),
                           'observations': len(fixed['observations'])}
    record['oracle'] = run([sys.executable, HERE / 'freeze.py'], timeout=max(120, 10 * len(cases)))
    line(record['oracle'], f'Verified {len(cases)} frozen seed observations; no differences')


def resource_cases(record):
    manifest = json.loads((HERE / 'resources.json').read_text())
    cases = manifest['cases']
    require(cases and len({case['name'] for case in cases}) == len(cases),
            'Empty or duplicate resource cases')
    require({str(path.relative_to(ROOT)) for path in (HERE / 'resources').glob('*.bend')}
            == {case['file'] for case in cases}, 'Resource fixture manifest mismatch')
    fixed = json.loads(RESOURCE_REFERENCE.read_text())
    require(fixed['status'] == 'passed', 'Resource reference is not passed')
    require(fixed['inputs'] == hashes([HERE / 'resources.json', HERE / 'resource-freeze.py',
                                      *(ROOT / case['file'] for case in cases)]),
            'Frozen resource inputs changed')
    require(fixed['seed'] == hashes([*SEED_DIR.glob('*.ts'), SEED_DIR / 'base.bend']),
            'Resource reference seed changed')
    require([item['name'] for item in fixed['observations']] == [case['name'] for case in cases],
            'Resource reference coverage differs')
    record['resource_reference'] = {'file': str(RESOURCE_REFERENCE.relative_to(ROOT)),
                                    'sha256': digest(RESOURCE_REFERENCE), 'observations': len(cases)}
    record['resource_oracle'] = run([sys.executable, HERE / 'resource-freeze.py'])
    line(record['resource_oracle'], f'Verified {len(cases)} frozen resource seed observations; no differences')
    return cases


def build_lanes(record):
    entries = {'check': ROOT / 'src/check-cli.bend', 'eval': ROOT / 'src/eval-cli.bend',
               'compile': ROOT / 'tests/compiler-fields-wasm/compile.bend'}
    lanes = {}
    for lane, suffix, runtime in LANES:
        lanes[lane] = {}
        for phase, entry in entries.items():
            output = BUILD / (phase + suffix)
            output.unlink(missing_ok=True)
            item = {'lane': lane, 'phase': phase, 'result': run([*SEED, entry, '-o', output])}
            record['builds'].append(item)
            successful(item['result'])
            require(output.is_file() and output.stat().st_size > 0, ('missing build', item))
            item['sha256'] = digest(output)
            lanes[lane][phase] = [*runtime, output]
    return lanes


def executed(module, expected, timeout=120):
    result = run(['node', HOST, PROFILE, module, expected['export'], *expected['arguments']], timeout=timeout)
    successful(result)
    observation = json.loads(result['stdout'])
    require(observation == {'validated': True, 'export': expected['export'],
                            'arguments': expected['arguments'], 'result': expected['result'],
                            'bytes': module.stat().st_size}, (expected, result))
    return result


def fixtures(record, manifest, cases, lanes, *, target='fixtures', timeout=120):
    new_names = {case['name'] for case in manifest['fixtures']}
    records = record[target]
    for index, case in enumerate(cases):
        source = ROOT / case['file']
        item = {'name': case['name'], 'file': case['file'], 'sha256': digest(source),
                'group': target if case['name'] in new_names else 'legacy',
                'expected': {phase: case[phase] for phase in PHASES}, 'lanes': {}}
        records.append(item)
        module_hashes = []
        for lane, commands in lanes.items():
            actual = item['lanes'][lane] = {}
            actual['check'] = run([*commands['check'], source], timeout=timeout)
            observe(actual['check'], case['check'], 'check')
            actual['eval'] = run([*commands['eval'], source, *case.get('eval_args', ['main', 65536])], timeout=timeout)
            observe(actual['eval'], case['eval'], 'eval')
            output = BUILD / f'{target}-{index:03d}-{lane}.wasm'
            output.write_bytes(MARKER)
            actual['compile'] = run([*commands['compile'], source, output], timeout=timeout)
            observe(actual['compile'], case['compile'], 'compile')
            if case['compile']['exit'] == 0:
                require(output.is_file() and output.read_bytes().startswith(b'\0asm\x01\0\0\0'),
                        ('missing Wasm module', case['name'], actual['compile']))
                line(actual['compile'], f'Built\t{output.stat().st_size}')
                actual['module_sha256'] = digest(output)
                module_hashes.append(actual['module_sha256'])
                if 'wasm' in case:
                    actual['wasm_expected'] = case['wasm']
                    actual['wasm'] = executed(output, case['wasm'], timeout=timeout)
                else:
                    actual['wasm_observer'] = case['wasm_observer']
            else:
                require(output.is_file() and output.read_bytes() == MARKER,
                        ('rejection changed output', case['name'], actual['compile']))
                actual['artifact_preserved'] = True
        if case['compile']['exit'] == 0:
            require(len(module_hashes) == len(LANES) and len(set(module_hashes)) == 1,
                    ('native/Bun module bytes differ', case['name'], module_hashes))
            item['module_bytes_equal'] = True
    by_name = {item['name']: item for item in records}
    for item in records:
        for lane, actual in item['lanes'].items():
            if 'wasm_observer' in actual:
                observer = by_name[actual['wasm_observer']]['lanes'][lane]
                require('wasm' in observer, ('observer was not executed', item['name'], lane))
                actual['observer_module_sha256'] = observer['module_sha256']


def mutants(record, cases, mutations):
    by_name = {case['name']: case for case in cases}
    require(isinstance(mutations, list) and mutations, 'A nonempty mutation list is required')
    require(len({mutation['name'] for mutation in mutations}) == len(mutations), 'Duplicate mutant names')
    for mutation in mutations:
        name = mutation['name']
        require(re.fullmatch(r'[a-z][a-z0-9_-]*', name), ('mutant directory name', name))
        require(Path(mutation['file']).name == mutation['file'] and mutation['file'].endswith('.bend'),
                ('mutant source path', name))
        require(mutation['old'] and mutation['old'] != mutation['new'], ('empty mutation', name))
        require(mutation['witness'] in by_name, ('unknown witness', name))
        require(mutation['wrong']['exit'] in (0, 2, 3),
                ('mutation witness must be semantic, not exhaustion or host failure', name))
        directory = BUILD / name
        directory.mkdir(exist_ok=True)
        for stale in directory.glob('*.bend'):
            stale.unlink()
        for source in sorted((ROOT / 'src').glob('*.bend')):
            copied = directory / source.name
            shutil.copy2(source, copied)
            require(digest(copied) == record['inputs'][str(source.relative_to(ROOT))],
                    ('source changed before mutation', name, source.name))
        target = directory / mutation['file']
        original = target.read_text()
        require(original.count(mutation['old']) == 1, ('mutation anchor is not unique', name))
        target.write_text(original.replace(mutation['old'], mutation['new'], 1))
        entry = directory / 'check-cli.bend'
        case = by_name[mutation['witness']]
        item = {**mutation, 'mutated_sha256': digest(target), 'expected': case['check'], 'lanes': {}}
        record['mutants'].append(item)
        item['typecheck'] = run([*SEED, entry, '--check-only'])
        line(item['typecheck'], 'All terms check.')
        for lane, suffix, runtime in LANES:
            output = directory / ('mutant' + suffix)
            output.unlink(missing_ok=True)
            actual = item['lanes'][lane] = {'build': run([*SEED, entry, '-o', output])}
            successful(actual['build'])
            require(output.is_file() and output.stat().st_size > 0, ('missing mutant build', name, lane))
            actual['build_sha256'] = digest(output)
            actual['observation'] = run([*runtime, output, ROOT / case['file']])
            observe(actual['observation'], mutation['wrong'], 'check')
            try:
                observe(actual['observation'], case['check'], 'check')
            except AssertionError as error:
                actual['frozen_assertion'] = str(error)
                actual['outcome'] = 'semantic-kill'
            else:
                raise AssertionError(('mutant survived frozen assertion', name, lane, actual))


def bounds(record):
    paths = [HERE / 'bounds.json', HERE / 'work-bounds.json']
    manifests = [json.loads(path.read_text()) for path in paths]
    require(all(manifest['driver'] == 'tests/compiler-descent/bounds.bend' for manifest in manifests),
            'Unexpected bounds driver')
    cases = [case for manifest in manifests for case in manifest['cases']]
    by_name = {case['name']: case for case in cases}
    require(cases and len(by_name) == len(cases), 'Empty or duplicate bounds cases')
    for case in cases:
        if 'control' in case:
            require(case['control'] in by_name and by_name[case['control']]['expected']['exit'] == 0,
                    ('bounds control', case['name']))
    source = HERE / 'bounds.bend'
    record['bounds_inputs'] = hashes([*paths, source])
    record['bounds_typecheck'] = run([*SEED, source, '--check-only'])
    line(record['bounds_typecheck'], 'All terms check.')
    for case in cases:
        record['bounds'].append({'name': case['name'], 'expected': case['expected'], 'lanes': {}})
    for lane, suffix, runtime in LANES:
        output = BUILD / ('bounds' + suffix)
        output.unlink(missing_ok=True)
        built = {'lane': lane, 'phase': 'bounds', 'result': run([*SEED, source, '-o', output])}
        record['builds'].append(built)
        successful(built['result'])
        require(output.is_file() and output.stat().st_size > 0, ('missing bounds build', lane))
        built['sha256'] = digest(output)
        for item in record['bounds']:
            actual = item['lanes'][lane] = run([*runtime, output, item['name']])
            observe(actual, item['expected'], 'bounds')
            if item['expected']['exit'] != 0:
                diagnostic = item['expected']['diagnostic']
                require(actual['stderr'] in (diagnostic, diagnostic + '\n'), (item, actual))
    require(hashes([*paths, source]) == record['bounds_inputs'],
            'Bounds inputs changed during execution')


def counts(record):
    observations = [(phase, result) for item in record['fixtures']
                    for lane in item['lanes'].values() for phase, result in lane.items()
                    if phase in PHASES]
    resources = record['resources']
    resource_observations = [(phase, result) for item in resources
                             for lane in item['lanes'].values() for phase, result in lane.items()
                             if phase in PHASES]
    return {'seed_fixtures': record['reference']['observations'],
            'resource_seed_fixtures': record['resource_reference']['observations'],
            'resource_accepted_books': sum(item['expected']['check']['exit'] == 0 for item in resources),
            'resource_phase_observations': len(resource_observations),
            'resource_evaluation_values': sum(phase == 'eval' and result['exit'] == 0
                                              for phase, result in resource_observations),
            'resource_wasm_values': sum('wasm' in lane for item in resources for lane in item['lanes'].values()),
            'resource_module_hash_pairs': sum(item.get('module_bytes_equal', False) for item in resources),
            'resource_preserved_artifacts': sum(lane.get('artifact_preserved', False)
                                                for item in resources for lane in item['lanes'].values()),
            'new_fixtures': sum(item['group'] == 'fixtures' for item in record['fixtures']),
            'legacy_fixtures': sum(item['group'] == 'legacy' for item in record['fixtures']),
            'accepted_books': sum(item['expected']['check']['exit'] == 0 for item in record['fixtures']),
            'phase_observations': len(observations),
            'check_observations': sum(phase == 'check' for phase, _ in observations),
            'evaluation_values': sum(phase == 'eval' and result['exit'] == 0 for phase, result in observations),
            'wasm_values': sum('wasm' in lane for item in record['fixtures'] for lane in item['lanes'].values()),
            'wasm_observer_links': sum('wasm_observer' in lane for item in record['fixtures'] for lane in item['lanes'].values()),
            'module_hash_pairs': sum(item.get('module_bytes_equal', False) for item in record['fixtures']),
            'rejected_phase_observations': sum(result['exit'] != 0 for _, result in observations),
            'preserved_artifacts': sum(lane.get('artifact_preserved', False)
                                       for item in record['fixtures'] for lane in item['lanes'].values()),
            'bounds_cases': len(record['bounds']),
            'bounds_observations': sum(len(item['lanes']) for item in record['bounds']),
            'bounds_exhaustions': sum(result['exit'] == 4 for item in record['bounds']
                                      for result in item['lanes'].values()),
            'bounds_internal_failures': sum(result['exit'] == 6 for item in record['bounds']
                                            for result in item['lanes'].values()),
            'proofs': len(record['proofs']), 'mutants': len(record['mutants']),
            'semantic_kills': sum(lane.get('outcome') == 'semantic-kill'
                                  for item in record['mutants'] for lane in item['lanes'].values())}


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
              'profile': 'knot-fields-wasm-1', 'builds': [], 'proofs': [], 'fixtures': [],
              'mutants': [], 'bounds': [], 'resources': []}
    try:
        manifest = json.loads((HERE / 'expectations.json').read_text())
        cases = validate_manifest(manifest)
        mutations = json.loads((HERE / 'mutants.json').read_text())
        record['inputs'] = hashes(input_paths(manifest))
        record['seed_revision'] = manifest['seed_revision']
        verify_reference(record, cases)
        resources = resource_cases(record)
        require(not {case['name'] for case in cases}.intersection(case['name'] for case in resources),
                'Resource case names overlap the original manifest')
        record['tools'] = {}
        for tool in ('bun', 'node', 'python3'):
            record['tools'][tool] = successful(run([tool, '--version']))['stdout'].strip()
        require(record['tools']['node'] == 'v22.22.3' and record['tools']['bun'] == '1.3.14', record['tools'])
        for proof in ('src/descent-PROOF.bend', 'src/recursion-PROOF.bend'):
            item = {'file': proof, 'result': run([*SEED, ROOT / proof])}
            record['proofs'].append(item)
            line(item['result'], 'All terms check.')
        lanes = build_lanes(record)
        fixtures(record, manifest, cases, lanes)
        # A short harness limit prevents an expansion regression from running unchecked.
        # A timeout fails this gate; it is never a matched language diagnostic.
        fixtures(record, {'fixtures': resources}, resources, lanes, target='resources', timeout=2)
        bounds(record)
        mutants(record, cases, mutations)
        validate_manifest(manifest)
        require(hashes(input_paths(manifest)) == record['inputs'], 'Inputs changed during gate')
        record['inputs_unchanged'] = True
        record['counts'] = counts(record)
        record['status'] = 'passed'
    except Exception as error:
        record['status'] = 'failed'
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    total = record['counts']
    print(f"Descent gate passed: {total['seed_fixtures']} seed fixtures, "
          f"{total['accepted_books']} accepted books, {total['phase_observations']} phase observations; "
          f"{total['evaluation_values']} evaluator values, {total['wasm_values']} Wasm values; "
          f"{total['resource_seed_fixtures']} resource fixtures / {total['resource_phase_observations']} phases; "
          f"{total['bounds_observations']} bounds observations; "
          f"{total['mutants']} mutants / {total['semantic_kills']} semantic kills")


if __name__ == '__main__':
    main()
