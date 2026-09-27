#!/usr/bin/env python3
"""Run the frozen adaptive CPU obligations; keep historical receipts unchanged."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
ADAPTIVE = HERE.parents[1]
ROOT = ADAPTIVE.parents[1]
WORK = ROOT / '.local/style-pilot/adaptive-run-1'
SEED = ROOT / 'scripts/bend-reference'
SOURCES = ['slot.bend', 'task.bend', 'oracle.bend', 'fixtures.bend',
           'LAWS.bend', 'PROOF.bend', 'conformance.bend']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--receipt', default='cpu-gates.json')
    options = args.parse_args()
    assert Path(options.receipt).name == options.receipt and options.receipt.endswith('.json')
    output = HERE / options.receipt
    assert not output.exists(), 'Preserve prior attempts in separate receipts'
    pre = json.loads((HERE / 'preregistration.json').read_text())
    first = json.loads((HERE / 'candidate-first-check.json').read_text())
    historical = json.loads((ADAPTIVE / 'receipts/checks.json').read_text())
    candidate = sha(ADAPTIVE / 'task.bend')
    assert candidate == first['candidate_sha256'] == sha(HERE / 'candidate-first.bend.snapshot')
    record = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'scope': 'Unchanged CPU assertions and independently fixed Bend oracle; device evidence reuse is separate',
              'status': 'incomplete', 'candidate_sha256': candidate,
              'driver_sha256': sha(Path(__file__)), 'commands': []}
    work_root = WORK / output.stem
    work_root.mkdir(parents=True, exist_ok=False)

    def run(argv):
        argv = list(map(str, argv))
        started = time.monotonic()
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=60)
        result = {'argv': argv, 'exit': p.returncode, 'stdout': p.stdout,
                  'stderr': p.stderr, 'seconds': time.monotonic() - started}
        record['commands'].append(result)
        return result

    try:
        for name, digest in pre['frozen_files'].items():
            assert sha(ADAPTIVE / name) == digest, ('frozen input', name)
        for name, digest in pre['reference']['files'].items():
            assert sha(ROOT / '.toolchain/bend-2.0.29-574b6d3' / name) == digest, name
        assert historical['hashes']['task.bend'] == pre['baseline_source_sha256']
        record['frozen_files'] = pre['frozen_files']
        record['reference'] = pre['reference']
        assert len(first['commands']) == 2 and all(c['exit'] == 0 for c in first['commands'])
        assert 'All terms check.' in first['commands'][1]['stdout']
        record['proof'] = {'receipt': 'candidate-first-check.json', 'sha256': sha(HERE / 'candidate-first-check.json'),
                           'laws': 12, 'unchanged_assertions': True}
        valid = run([SEED, ADAPTIVE / 'tests/affine-valid.bend'])
        assert valid['exit'] == 0 and 'All terms check.' in valid['stdout'], valid
        record['valid_control'] = valid
        record['negative_quantity'] = {}
        for name in ['affine-task-reuse.bend', 'affine-slot-reuse.bend']:
            r = run([SEED, ADAPTIVE / 'tests' / name])
            assert r['exit'] != 0 and 'consumed more than once' in r['stdout'] + r['stderr'], r
            record['negative_quantity'][name] = r

        fixtures = run([SEED, ADAPTIVE / 'fixtures.bend'])
        assert fixtures['exit'] == 0, fixtures
        records = [json.loads(line) for line in fixtures['stdout'].splitlines()]
        assert len(records) == 10 and records == historical['fixtures']
        value = next(r['expected'] for r in records if r['name'] == 'cpu_frames')
        # Exact assertion sequence from the immutable check.py; expected numeric
        # payload comes from the independent Bend tree evaluator, not task.run.
        expected = '\n'.join(['0,73,11', f'0,73,{value}', f'1,73,{value}', f'1,73,{value}', f'1,73,{value}',
                              '0,73,11', f'1,73,{value}', '1,41,226', 'rejected:7,9', 'extracted:7', 'missing', ''])
        assert expected == historical['js_conformance']['stdout']
        record['fixture_output_sha256'] = hashlib.sha256(fixtures['stdout'].encode()).hexdigest()
        record['expected_conformance'] = expected
        record['execution'] = []
        for variant in ['baseline', 'candidate']:
            work = work_root / variant
            work.mkdir()
            inputs = work / 'inputs'
            inputs.mkdir()
            # Recover inputs from committed objects and the frozen candidate,
            # rather than relying on a previous session's ignored binaries.
            for name in SOURCES:
                if name == 'task.bend':
                    body = (HERE / ('baseline-task.bend.snapshot' if variant == 'baseline'
                                    else 'candidate-first.bend.snapshot')).read_bytes()
                    digest = pre['baseline_source_sha256'] if variant == 'baseline' else candidate
                else:
                    body = subprocess.check_output(['git', 'show',
                        pre['base_commit'] + ':research/adaptive-tasks/' + name], cwd=ROOT)
                    digest = pre['frozen_files'][name]
                assert hashlib.sha256(body).hexdigest() == digest, ('source reconstruction', variant, name)
                (inputs / name).write_bytes(body)
            for lane, suffix, runtime in [('native', '', []), ('js', '.js', ['bun'])]:
                program = work / ('conformance' + suffix)
                build = run([SEED, inputs / 'conformance.bend', '-o', program])
                assert build['exit'] == 0, build
                observed = run([*runtime, program])
                assert observed['exit'] == 0 and observed['stdout'] == expected, observed
                record['execution'].append({'variant': variant, 'lane': lane,
                                            'program_sha256': sha(program), 'exact_match': True,
                                            'command_index': len(record['commands']) - 1})
        record['reconstructed_source_commit'] = pre['base_commit']
        native_fixtures = work_root / 'candidate/fixtures'
        build = run([SEED, ADAPTIVE / 'fixtures.bend', '-o', native_fixtures])
        assert build['exit'] == 0, build
        observed = run([native_fixtures])
        assert observed['exit'] == 0 and observed['stdout'] == fixtures['stdout'], observed

        mutations = [
            ('wrong_tick', 'task.bend', '1013904223', '1013904224', 'one_tick'),
            ('swapped_join', 'task.bend', 'U32.add(U32.mul(a,31),b)', 'U32.add(U32.mul(b,31),a)', 'binary_order'),
            ('lost_destination', 'task.bend', 'case 0n Nil{}:\n      Delivered{dest,p}', 'case 0n Nil{}:\n      Delivered{0,p}', 'binary_order'),
            ('discard_zero_budget', 'task.bend',
             '  match fuel state:\n    case 1n+n Checkpoint{task}:',
             '  match fuel state:\n    case 0n _: Delivered{0,OwnedWord{0}}\n    case 1n+n Checkpoint{task}:', 'zero_fuel'),
            ('overwrite_owned_slot', 'slot.bend', 'case Occupied{value}: Rejected{Occupied{value},x}',
             'case Occupied{value}: Inserted{Occupied{x}}', 'put_full'),
        ]
        record['mutants'] = []
        for name, file, old, new, law in mutations:
            folder = work_root / 'mutants' / name
            folder.mkdir(parents=True, exist_ok=False)
            for source in SOURCES:
                shutil.copyfile(ADAPTIVE / source, folder / source)
            body = (folder / file).read_text()
            assert body.count(old) == 1, (name, body.count(old))
            (folder / file).write_text(body.replace(old, new))
            model = run([SEED, folder / file, '--check-only'])
            assert model['exit'] == 0 and 'All terms check.' in model['stdout'], model
            proof = run([SEED, folder / 'PROOF.bend'])
            diagnostic = proof['stdout'] + proof['stderr']
            assert proof['exit'] != 0 and law in diagnostic and 'expected' in diagnostic and 'observed' in diagnostic, proof
            witness = run([SEED, folder / 'conformance.bend'])
            assert witness['exit'] == 0 and witness['stdout'] != expected, witness
            old_result = next(m for m in historical['mutants'] if m['name'] == name)
            assert witness['stdout'] == old_result['stdout'], ('changed mutation observation', name)
            record['mutants'].append({'name': name, 'source_sha256': sha(folder / file),
                                      'typecheck': model, 'proof': proof, 'witness': witness,
                                      'rejecting_law': law, 'matches_original_mutant_observation': True})
        record['zero_budget_locator'] = {'reanchored': True, 'domain': 'fuel == 0 only',
                                         'before': 'replace original zero-fuel arm body',
                                         'after': 'insert same bad zero-fuel arm before recurrence',
                                         'positive_fuel_delivered_unchanged': True,
                                         'original_assertion_and_runtime_failure_preserved': True}
        device = json.loads((ADAPTIVE / 'receipts/gpu.json').read_text())
        assert device['hashes']['shader'] == sha(ADAPTIVE / 'gpu/tasks.wgsl')
        assert device['hashes']['runner'] == sha(ADAPTIVE / 'gpu/check.mjs')
        assert device['hashes']['fixtures'] == record['fixture_output_sha256']
        assert './task.bend' not in (ADAPTIVE / 'fixtures.bend').read_text() + (ADAPTIVE / 'oracle.bend').read_text()
        record['device_evidence'] = {'mode': 'matching historical component evidence, not a new hardware run',
                                     'receipt': 'research/adaptive-tasks/receipts/gpu.json',
                                     'sha256': sha(ADAPTIVE / 'receipts/gpu.json'),
                                     'matched_shader_runner_and_fresh_independent_fixture_output': True,
                                     'new_gpu_execution': False}
        for name, digest in pre['frozen_files'].items():
            assert sha(ADAPTIVE / name) == digest, ('input changed during gate', name)
        assert sha(ADAPTIVE / 'task.bend') == candidate
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        output.write_text(json.dumps(record, indent=2) + '\n')
    print('PASS: 12 unchanged laws, two quantity negatives, exact baseline/candidate native/JS observations, five semantic mutations, matching historical device components.')


if __name__ == '__main__':
    main()
