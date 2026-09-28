#!/usr/bin/env python3
"""Invoke independent Bend lanes against frozen observations; no compiler semantics."""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
TIMEOUT_SCALE = float(__import__('os').environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))  # harness hang guard only; gates set it under load

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/compiler-recursion/gate'
SEED = ['bun', ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']
RECEIPTS = HERE / 'receipts'


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, timeout=60*TIMEOUT_SCALE):
    try:
        p = subprocess.run([str(x) for x in argv], cwd=ROOT, text=True,
                           capture_output=True, timeout=timeout,
                           env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
        return {'argv': [str(x) for x in argv], 'exit': p.returncode,
                'stdout': p.stdout, 'stderr': p.stderr}
    except subprocess.TimeoutExpired:
        return {'argv': [str(x) for x in argv], 'exit': None,
                'outcome': 'harness-timeout', 'stdout': '', 'stderr': ''}


def successful(argv):
    result = run(argv)
    require(result['exit'] == 0, result)
    return result


def observe(result, expected):
    require(result['exit'] == expected['exit'], (expected, result))
    if 'stdout' in expected:
        require(result['stdout'].strip() == expected['stdout'], (expected, result))
    if 'contains' in expected:
        require(expected['contains'] in result['stdout'], (expected, result))
    if 'diagnostic' in expected:
        require(expected['diagnostic'] in result['stderr'] and not result['stdout'], (expected, result))


def reference(manifest):
    observations = []
    for case in manifest['cases']:
        actual = run([*SEED, HERE / case['file'], *case.get('reference_args', [])])
        observe(actual, case['reference'])
        observations.append({'case': case['name'], 'result': actual})
    return observations


# These replacements must remain uniquely located and independently typechecked.
MUTANTS = [
    ('admit-any-self-call', 'check.bend',
     'Bool.and(U32.is_eq(index,current),Bool.not(E.descends(items,smaller)))',
     'False{}', 'same-parameter', 0),
    ('stop-propagating-fields', 'patterns.bend',
     'E.descendants(level,E.levels(introduced),smaller)',
     'smaller', 'direct', 3),
    ('stop-nested-propagation', 'scope.bend',
     'Bool.or(U32.is_eq(level,0),contains(smaller,level))',
     'U32.is_eq(level,0)', 'even', 3),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference-only', action='store_true')
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((HERE / 'cases.json').read_text())
    fixtures = sorted((HERE / 'fixtures').glob('*.bend'))
    require({str(p.relative_to(HERE)) for p in fixtures} ==
            {c['file'] for c in manifest['cases']}, 'Fixture manifest mismatch')
    fixed = {str(p.relative_to(ROOT)): digest(p) for p in fixtures + [HERE / 'cases.json']}
    if args.reference_only:
        receipt = RECEIPTS / 'reference.json'
        require(not receipt.exists(), 'The preimplementation expectation freeze is immutable')
        result = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'seed_revision': manifest['seed_revision'], 'status': 'passed',
                  'frozen_inputs': fixed,
                  'baseline_implementation': {str(p.relative_to(ROOT)): digest(p)
                      for p in sorted((ROOT / 'src').glob('*.bend'))},
                  'observations': reference(manifest)}
        receipt.write_text(json.dumps(result, indent=2) + '\n')
        print(f"Reference freeze passed: {len(result['observations'])} fixtures; {receipt}")
        return
    frozen = json.loads((RECEIPTS / 'reference.json').read_text())
    require(frozen['status'] == 'passed' and frozen['frozen_inputs'] == fixed,
            'Expectations changed since the preimplementation seed freeze')
    paths = sorted((ROOT / 'src').glob('*.bend')) + fixtures + [Path(__file__), HERE / 'cases.json',
        ROOT / 'src/SPEC.md', ROOT / 'src/CONTRACT.json', HERE / 'SPEC.md']
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
              'seed_revision': manifest['seed_revision'],
              'inputs': {str(p.relative_to(ROOT)): digest(p) for p in paths},
              'seed_inputs': {str(p.relative_to(ROOT)): digest(p) for p in
                  sorted((ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2').glob('*.ts')) +
                  [ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/base.bend']},
              'expectation_freeze_sha256': digest(RECEIPTS / 'reference.json')}
    try:
        record['tools'] = {t: successful([t, '--version'])['stdout'].strip() for t in ('bun', 'node', 'python3')}
        record['proof'] = successful([*SEED, ROOT / 'src/recursion-PROOF.bend'])
        require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
        record['reference'] = reference(manifest)
        record['builds'], lanes = [], {}
        for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
            lanes[lane] = {}
            for phase in ('check', 'eval', 'compile'):
                output = BUILD / (phase + suffix)
                built = successful([*SEED, ROOT / f'src/{phase}-cli.bend', '-o', output])
                record['builds'].append({'lane': lane, 'phase': phase, 'result': built, 'sha256': digest(output)})
                lanes[lane][phase] = [*runtime, output]
        record['fixtures'] = []
        for case in manifest['cases']:
            item = {'case': case['name'], 'lanes': {}}
            for lane, commands in lanes.items():
                path = HERE / case['file']
                checked = run([*commands['check'], path]); observe(checked, case['check'])
                evaluated = run([*commands['eval'], path, 'main', 65536]); observe(evaluated, case['eval'])
                output = BUILD / (case['name'] + '-' + lane + '.wasm')
                marker = b'existing artifact: recursive programs remain unemitted\n'
                output.write_bytes(marker)
                compiled = run([*commands['compile'], path, output]); observe(compiled, case['compile'])
                require(output.read_bytes() == marker, ('artifact changed', compiled))
                item['lanes'][lane] = {'check': checked, 'eval': evaluated,
                    'compile': compiled, 'artifact_preserved': True}
            record['fixtures'].append(item)
        cases = {c['name']: c for c in manifest['cases']}
        record['fuel'] = []
        for lane, commands in lanes.items():
            for probe in manifest['fuel']:
                result = run([*commands['eval'], HERE / cases[probe['case']]['file'], 'main', probe['budget']])
                observe(result, probe['expected'])
                record['fuel'].append({'lane': lane, 'case': probe['case'], 'result': result})
        record['mutants'] = []
        for name, file, old, new, witness, exit_code in MUTANTS:
            directory = BUILD / name; directory.mkdir(exist_ok=True)
            for source in (ROOT / 'src').glob('*.bend'):
                shutil.copy2(source, directory / source.name)
            target = directory / file; source = target.read_text()
            require(source.count(old) == 1, (name, 'mutation must be unique'))
            target.write_text(source.replace(old, new))
            entry = directory / 'check-cli.bend'
            typecheck = successful([*SEED, entry, '--check-only'])
            require(typecheck['stdout'].strip() == 'All terms check.', typecheck)
            output = directory / 'mutant.js'; built = successful([*SEED, entry, '-o', output])
            actual = run(['bun', output, HERE / cases[witness]['file']])
            # Require the intended semantic observation, never a crash or timeout.
            observe(actual, {'exit': 0, 'contains': 'Checked\n'} if exit_code == 0 else
                    {'exit': 3, 'diagnostic': 'Unsupported\tcheck\trecursive-call\t'})
            try:
                observe(actual, cases[witness]['check'])
            except AssertionError:
                killed = True
            else:
                killed = False
            require(killed, (name, 'survived'))
            record['mutants'].append({'name': name, 'file': file, 'old': old, 'new': new,
                'sha256': digest(target), 'typecheck': typecheck, 'build': built,
                'witness': witness, 'expected': cases[witness]['check'], 'actual': actual,
                'outcome': 'semantic-kill'})
        require(all(digest(ROOT / p) == h for p, h in record['inputs'].items()), 'Inputs changed during gate')
        record['status'] = 'passed'
    except Exception as e:
        record['failure'] = repr(e)
        raise
    finally:
        (RECEIPTS / 'recursion.json').write_text(json.dumps(record, indent=2) + '\n')
    print(f"Recursion gate passed: {len(record['reference'])} seed fixtures, "
          f"{6*len(record['fixtures'])} native/Bun phase observations, "
          f"{len(record['fuel'])} fuel probes, {len(record['mutants'])} semantic mutants")


if __name__ == '__main__':
    main()
