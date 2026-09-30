#!/usr/bin/env python3
"""Replay fixed seed probes through the public CLIs, evaluator and actual Wasm."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/descent-2/precheck-gate'
RECEIPT = HERE / 'receipts/prechecks.json'
SEED = ['bun', ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']
MARKER = b'pre-existing artifact: refusal must preserve these bytes\n'
PHASES = ('parse', 'check', 'eval', 'compile')
ENTRIES = {'parse': 'src/parse-cli.bend', 'check': 'src/check-cli.bend', 'eval': 'src/eval-cli.bend',
           'compile': 'tests/compiler-fields-wasm/compile.bend'}


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value, root):
    if isinstance(value, str):
        return value.replace(str(root), '<ROOT>')
    if isinstance(value, list):
        return [normalized(v, root) for v in value]
    if isinstance(value, dict):
        return {k: normalized(v, root) for k, v in value.items()}
    return value


def run(args):
    env = {k: os.environ[k] for k in ('PATH', 'HOME', 'CC', 'SDKROOT', 'DEVELOPER_DIR') if k in os.environ}
    env.update(BEND_NO_TELEMETRY='1', BEND_HUB='offline://disabled', BEND_ORIGIN='offline://disabled')
    p = subprocess.run([str(a) for a in args], cwd=BUILD, env=env, text=True, capture_output=True, timeout=180)
    return {'argv': [str(a) for a in args], 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


def successful(args):
    actual = run(args)
    require(actual['exit'] == 0 and not actual['stderr'], actual)
    return actual


def observe(actual, fixed, phase):
    require(actual['exit'] == fixed['exit'], (phase, fixed, actual))
    if fixed['exit']:
        require(not actual['stdout'] and len(actual['stderr'].splitlines()) == 1
                and actual['stderr'].startswith(fixed['diagnostic']), (phase, fixed, actual))
        if fixed.get('located'):
            require(not actual['stderr'].strip().endswith('\t0:0:0:0'), actual)
    else:
        require(not actual['stderr'], actual)
        if phase == 'parse':
            require(actual['stdout'].startswith('Parsed\t'), actual)
        if phase == 'check':
            require(actual['stdout'].startswith('Checked\n'), actual)
        if phase == 'eval':
            require(actual['stdout'].strip() == f"Evaluated\t0\t{1 if fixed['value'] == 'On{}' else 0}\t{fixed['value']}", actual)


def seed_reference():
    frozen = json.loads((HERE / 'receipts/precheck-reference.json').read_text())
    for path, expected in frozen['inputs'].items():
        require(digest(ROOT / path) == expected, ('Seed input changed', path))
    for path, expected in frozen['seed'].items():
        require(digest(ROOT / path) == expected, ('Seed changed', path))
    spec = importlib.util.spec_from_file_location('precheck_seed', HERE / 'precheck-freeze.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    actual = module.observe()
    old_root = frozen['observations'][0]['book']['argv'][1].split('/.toolchain/')[0]
    require(normalized(actual, ROOT) == normalized(frozen['observations'], old_root), 'Seed observations changed')
    return frozen


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    fixed = json.loads((HERE / 'precheck-expectations.json').read_text())
    cases = fixed['fixtures']
    mutations = json.loads((HERE / 'precheck-mutants.json').read_text())['mutants']
    paths = [*sorted((ROOT / 'src').glob('*.bend')), Path(__file__), HERE / 'precheck-expectations.json',
             HERE / 'precheck-mutants.json', HERE / 'precheck-freeze.py', HERE / 'precheck-parse.ts',
             HERE / 'receipts/precheck-reference.json', *(ROOT / c['file'] for c in cases),
             ROOT / ENTRIES['compile'], ROOT / 'scripts/run-wasm.mjs']
    inputs = {str(p.relative_to(ROOT)): digest(p) for p in paths}
    record = {'status': 'incomplete', 'inputs': inputs, 'seed_revision': fixed['seed_revision'],
              'builds': [], 'fixtures': [], 'mutants': []}
    try:
        seed = seed_reference()
        require(len(cases) == len(seed['observations']) == 23, 'Frozen control count')
        require({c['file'] for c in cases} == {str(p.relative_to(ROOT)) for p in (HERE / 'precheck-fixtures').glob('*.bend')}, 'Fixture coverage')
        record['seed_controls'] = {'parse': 23, 'book': 23, 'native': 23, 'bun': 23,
                                   'accepted': 15, 'rejected': 8}
        record['proof'] = successful([*SEED, ROOT / 'src/precheck-PROOF.bend'])
        require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
        lanes = {}
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
            commands = lanes[lane] = {}
            for phase, entry in ENTRIES.items():
                output = BUILD / (phase + suffix)
                built = successful([*SEED, ROOT / entry, '-o', output])
                record['builds'].append({'lane': lane, 'phase': phase, 'build': built, 'sha256': digest(output)})
                commands[phase] = [*runtime, output]
        for case in cases:
            require(digest(ROOT / case['file']) == case['sha256'], ('Fixture changed', case['name']))
            row = {'name': case['name'], 'sha256': case['sha256'], 'lanes': {}}
            modules = []
            for lane, commands in lanes.items():
                observations = row['lanes'][lane] = {}
                for phase in PHASES:
                    output = BUILD / f"{case['name']}-{lane}.wasm"
                    if phase == 'compile':
                        output.write_bytes(MARKER)
                    args = ['main', '65536'] if phase == 'eval' else [output] if phase == 'compile' else []
                    actual = run([*commands[phase], ROOT / case['file'], *args])
                    observe(actual, case[phase], phase)
                    observations[phase] = actual
                    if phase == 'compile':
                        if case[phase]['exit']:
                            require(output.read_bytes() == MARKER, ('Refusal wrote artifact', case['name'], lane))
                        else:
                            require(actual['stdout'].strip() == f'Built\t{output.stat().st_size}' and output.read_bytes() != MARKER, actual)
                            modules.append(digest(output))
                            wasm = successful(['node', ROOT / 'scripts/run-wasm.mjs', '--profile=knot-fields-wasm-1', output, 'main'])
                            value = json.loads(wasm['stdout'])
                            require(value['validated'] is True and value['result'] == (1 if case['eval']['value'] == 'On{}' else 0), wasm)
                            observations['wasm'] = wasm
                            observations['module_sha256'] = digest(output)
            if modules:
                require(len(modules) == 2 and modules[0] == modules[1], ('Lane module disagreement', case['name']))
            record['fixtures'].append(row)
        by_name = {c['name']: c for c in cases}
        for mutation in mutations:
            item = {'name': mutation['name'], 'witness': mutation['witness'], 'lanes': {}}
            directory = BUILD / mutation['name']
            shutil.copytree(ROOT / 'src', directory, dirs_exist_ok=True)
            target = directory / mutation['file']
            text = target.read_text()
            require(text.count(mutation['old']) == 1, ('Mutant anchor', mutation['name']))
            target.write_text(text.replace(mutation['old'], mutation['new']))
            entry = directory / Path(ENTRIES[mutation['phase']]).name
            item['typecheck'] = successful([*SEED, entry, '--check-only'])
            require(item['typecheck']['stdout'].strip() == 'All terms check.', item)
            case = by_name[mutation['witness']]
            for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
                output = directory / ('mutant' + suffix)
                built = successful([*SEED, entry, '-o', output])
                actual = run([*runtime, output, ROOT / case['file']])
                observe(actual, mutation['wrong'], mutation['phase'])
                try:
                    observe(actual, case[mutation['phase']], mutation['phase'])
                except AssertionError:
                    killed = True
                else:
                    killed = False
                require(killed, ('Mutant survived', mutation['name'], lane))
                item['lanes'][lane] = {'build': built, 'actual': actual, 'outcome': 'semantic-kill'}
            record['mutants'].append(item)
        require(all(digest(ROOT / path) == expected for path, expected in inputs.items()), 'Inputs changed during gate')
        accepted = sum(c['check']['exit'] == 0 for c in cases)
        record['counts'] = {'fixtures': len(cases), 'phase_observations': len(cases) * 8, 'accepted_books': accepted,
                            'evaluation_values': accepted * 2, 'wasm_values': accepted * 2, 'module_pairs': accepted,
                            'preserved_artifacts': (len(cases) - accepted) * 2, 'proofs': 1, 'laws': 8,
                            'mutants': len(mutations), 'semantic_kills': len(mutations) * 2}
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print('Descent prechecks passed: ' + json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
