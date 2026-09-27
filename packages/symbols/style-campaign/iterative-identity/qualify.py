#!/usr/bin/env python3
"""Run frozen Bend assertions against a Symbols candidate, without rewriting them."""
import argparse
import hashlib
import json
import pathlib
import platform
import statistics
import subprocess
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PKG = ROOT / 'packages/symbols'
BASE = HERE.parent / 'intern-identity-1'
PRE = json.loads((BASE / 'preregistration.json').read_text())
BEND = ROOT / 'scripts/bend-reference'
# These tracked implementation documents/drivers change during integration.
# Their original snapshots remain checked below; all independent Bend inputs,
# assertions, laws, benchmark workload, rubric and compiler launcher stay fixed.
INTEGRATION_FILES = {'packages/symbols/main.bend', 'packages/symbols/SPEC.md',
                     'packages/symbols/INTERFACE.md',
                     'packages/symbols/scripts/mutations.py',
                     'packages/symbols/scripts/benchmark.py', 'perch-style.json'}
# The coordinator installed rubric v3 after the v2 search completed. Both
# rubric identities and separate live results are retained in policy-transition.json;
# deterministic replay still verifies the original rubric snapshot above.


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def verify():
    for name, record in PRE['inputs'].items():
        assert sha(BASE / record['snapshot']) == record['sha256'], name
        if name not in INTEGRATION_FILES:
            assert sha(ROOT / name) == record['sha256'], name


def run(argv, records, receipt, expected=None):
    start = time.perf_counter()
    p = subprocess.run(list(map(str, argv)), cwd=ROOT, text=True,
                       capture_output=True, timeout=180)
    r = {'argv': list(map(str, argv)), 'exit': p.returncode,
         'stdout': p.stdout, 'stderr': p.stderr,
         'elapsed_seconds': time.perf_counter() - start}
    records.append(r)
    write(receipt, {'status': 'running', 'records': records})
    assert p.returncode == 0, r
    if expected is not None:
        assert p.stdout.strip() == expected, r
    return r


def prepare(args):
    verify()
    source = args.source.resolve()
    assert source.is_relative_to(PKG)
    output = HERE / 'qualification' / args.label
    output.mkdir(parents=True, exist_ok=True)
    snapshot = output / 'main.bend.snapshot'
    if snapshot.exists():
        assert snapshot.read_bytes() == source.read_bytes(), 'Label belongs to another candidate'
    else:
        snapshot.write_bytes(source.read_bytes())
    work = PKG / 'build/memetic-search/root' / args.label
    for variant in ['baseline', 'candidate']:
        dest = work / variant
        dest.mkdir(parents=True, exist_ok=True)
        for frozen in sorted((BASE / 'inputs').glob('*.bend.snapshot')):
            data = snapshot.read_bytes() if variant == 'candidate' and frozen.name == 'main.bend.snapshot' else frozen.read_bytes()
            (dest / frozen.name.removesuffix('.snapshot')).write_bytes(data)
    return output, work, source


def behavior(output, work):
    receipt = output / 'behavior.json'
    assert not receipt.exists(), receipt
    records = []
    dest = work / 'candidate'
    run([BEND, dest / 'main.bend', '--check-only'], records, receipt, 'All terms check.')
    run([BEND, dest / 'PROOF.bend', '--check-only'], records, receipt, 'All terms check.')
    for entry in ['conformance', 'release']:
        for lane in ['js', 'native']:
            binary = dest / (entry + ('.js' if lane == 'js' else '.native'))
            run([BEND, dest / (entry + '.bend'), '-o', binary], records, receipt)
            run(['bun', binary] if lane == 'js' else [binary], records, receipt, '1')
    verify()
    write(receipt, {'status': 'passed', 'candidate_sha256': sha(dest / 'main.bend'),
          'frozen_inputs': PRE['inputs'], 'records': records,
          'coverage': 'Eight unchanged laws; 6912 full-state traces and targeted cases; native and JS conformance and release consumers.'})
    print('PASS: complete frozen proof, native/JS full-state conformance, and release consumers.')


def mutations(output, work):
    receipt = output / 'mutations.json'
    assert not receipt.exists(), receipt
    anchors = json.loads((output / 'mutation-anchors.json').read_text())
    required = {'alias_ids': ('repeat', 4), 'forget_forward': ('repeat', 4),
                'repeat_grows': ('repeat', 4), 'reverse_wrong': ('unicode', 6),
                'wrap_invalid': ('full', 1), 'exhaustion_success': ('full', 1),
                'failure_forgets': ('full', 1), 'wrong_error': ('full', 1)}
    assert {a['name']: (a['case'], a['limit']) for a in anchors} == required
    rows, records = [], []
    for anchor in anchors:
        dest = work / 'mutants' / anchor['name']
        dest.mkdir(parents=True, exist_ok=True)
        for name in ['main.bend', 'observe.bend', 'protocol.bend', 'model.bend', 'cases.bend']:
            (dest / name).write_bytes((work / 'candidate' / name).read_bytes())
        fixture = (f'import Base\nimport ./cases.bend as C\n'
                   f'def main() -> U32: Bool.to_u32(C.check(C.{anchor["case"]}(),{anchor["limit"]}))\n')
        (dest / 'test.bend').write_text(fixture)
        start = len(records)
        run([BEND, dest / 'test.bend', '-o', dest / 'test.js'], records, receipt)
        run(['bun', dest / 'test.js'], records, receipt, '1')
        source = (dest / 'main.bend').read_text()
        assert source.count(anchor['old']) == 1, anchor['name']
        (dest / 'main.bend').write_text(source.replace(anchor['old'], anchor['new']))
        run([BEND, dest / 'main.bend', '--check-only'], records, receipt, 'All terms check.')
        run([BEND, dest / 'test.bend', '-o', dest / 'test.js'], records, receipt)
        run(['bun', dest / 'test.js'], records, receipt, '0')
        rows.append({**anchor, 'classification': 'semantic kill',
                     'source_sha256': sha(dest / 'main.bend'),
                     'fixture_sha256': sha(dest / 'test.bend'), 'records': records[start:]})
    verify()
    write(receipt, {'status': 'passed', 'candidate_sha256': sha(work / 'candidate/main.bend'), 'mutants': rows})
    print('PASS: all eight type-correct faults killed by unchanged observing cases.')


def benchmark(output, work):
    receipt = output / 'benchmark.json'
    assert not receipt.exists(), receipt
    records, rows = [], []
    for n in [128, 256, 512]:
        for prefix in [0, 64, 256]:
            binaries = {}
            for variant in ['baseline', 'candidate']:
                dest = work / variant
                entry = dest / f'bench_{n}_{prefix}.bend'
                entry.write_text(f'import Base\nimport ./benchmark.bend as B\n'
                                 f'def main() -> U32: B.repeated(16n,{n}n,B.prefix({prefix}n))\n')
                binary = entry.with_suffix('.native')
                run([BEND, entry, '-o', binary], records, receipt)
                binaries[variant] = binary
            times = {'baseline': [], 'candidate': []}
            for trial in range(3):
                order = ['baseline', 'candidate'] if trial % 2 == 0 else ['candidate', 'baseline']
                for variant in order:
                    result = run([binaries[variant]], records, receipt, '0')
                    times[variant].append(result['elapsed_seconds'])
            medians = {key: statistics.median(value) for key, value in times.items()}
            rows.append({'distinct_names': n, 'extra_common_prefix_codepoints': prefix,
                         'repetitions': 16, 'intern_calls': 32*n, 'resolve_calls': 16*n,
                         'errors': 0, 'seconds': times, 'median_seconds': medians,
                         'candidate_over_baseline': medians['candidate']/medians['baseline']})
    verify()
    write(receipt, {'status': 'completed', 'lane': 'native CPU', 'platform': platform.platform(),
          'measure': 'Wall time including startup; three paired trials, alternating order.',
          'limitations': 'Shared-host timings; no allocation instrumentation or GPU claim.',
          'baseline_sha256': sha(work / 'baseline/main.bend'),
          'candidate_sha256': sha(work / 'candidate/main.bend'), 'rows': rows, 'records': records})
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['behavior', 'mutations', 'benchmark'])
    p.add_argument('source', type=pathlib.Path)
    p.add_argument('label')
    args = p.parse_args()
    assert args.label and all(c.isalnum() or c in '-_' for c in args.label)
    output, work, source = prepare(args)
    before = sha(source)
    globals()[args.phase](output, work)
    assert sha(source) == before, 'Candidate changed during qualification'
