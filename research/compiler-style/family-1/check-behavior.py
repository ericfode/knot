#!/usr/bin/env python3
"""Isolated baseline/candidate qualification; invokes Bend, never edits candidates."""
from pathlib import Path
import datetime
import gzip
import hashlib
import importlib.util
import json
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORK = ROOT / '.local/compiler-style/family-1'
SEED = ROOT / 'scripts/bend-reference'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def main():
    spec = importlib.util.spec_from_file_location('fixed_oracle', HERE / 'behavior-oracle.py')
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    frozen = json.loads((HERE / 'candidate-first-manifest.json').read_text())
    require(digest(HERE / 'candidate-first.bend.snapshot') == frozen['candidate_sha256'], 'candidate changed')
    inputs = {name: digest(HERE / name) for name in
              ('behavior.bend', 'behavior-oracle.py', 'candidate-first.bend.snapshot',
               'baseline/src__scope.bend.snapshot', 'preregistration.json', 'check-behavior.py')}
    receipt_dir = HERE / 'behavior-receipts'
    receipt_dir.mkdir(exist_ok=True)
    attempt = len(list(receipt_dir.glob('attempt-*.json'))) + 1
    receipt = receipt_dir / f'attempt-{attempt:03}.json'
    record = {'status': 'incomplete', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'inputs_frozen_before_execution': inputs, 'commands': [], 'observations': [],
              'sizes': oracle.SIZES, 'timing_boundary': 'Wall time includes startup, formatting, and output; no speedup claim.',
              'regression_gates': {'status': 'requires parent integration',
                'reason': 'Existing checker, fields, and Wasm runners derive ROOT from __file__, hard-code ROOT/src and shared output directories, and expose no supported source/build override. They were not edited or run against live sources.'}}

    def run(argv, timeout=90):
        argv = [str(x) for x in argv]
        started = time.monotonic()
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        result = {'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr,
                  'elapsed_seconds': time.monotonic() - started}
        record['commands'].append(result)
        require(p.returncode == 0, result)
        return result

    try:
        record['tools'] = {tool: run([tool, '--version'])['stdout'].strip() for tool in ('bun', 'python3')}
        # Reconstruct from committed objects, never an untracked previous session.
        baseline_commit=json.loads((HERE/'preregistration.json').read_text())['baseline_commit']
        source=WORK/'source-closure'
        source.mkdir(parents=True,exist_ok=True)
        for name,expected_hash in frozen['copied_sources'].items():
            if name=='scope.bend':
                body=(HERE/'candidate-first.bend.snapshot').read_bytes()
            else:
                body=subprocess.check_output(['git','show',f'{baseline_commit}:src/{name}'],cwd=ROOT)
            require(hashlib.sha256(body).hexdigest()==expected_hash,('frozen source mismatch',name))
            (source/name).write_bytes(body)
        record['reconstructed_source_commit']=baseline_commit
        for variant in ('baseline', 'candidate'):
            target = WORK / 'behavior' / variant
            target.mkdir(parents=True, exist_ok=True)
            for name, expected_hash in frozen['copied_sources'].items():
                require(digest(source / name) == expected_hash, ('isolated input changed', name))
                shutil.copy2(source / name, target / name)
            shutil.copy2(HERE / ('baseline/src__scope.bend.snapshot' if variant == 'baseline'
                               else 'candidate-first.bend.snapshot'), target / 'scope.bend')
            shutil.copy2(HERE / 'behavior.bend', target / 'behavior.bend')
            proof = run([SEED, target / 'fields-PROOF.bend'])
            require(proof['stdout'].strip() == 'All terms check.', proof)
            check = run([SEED, target / 'behavior.bend', '--check-only'])
            require(check['stdout'].strip() == 'All terms check.', check)
            for lane, suffix, runtime in (('native', '', []), ('bun', '.js', ['bun'])):
                program = target / ('behavior' + suffix)
                run([SEED, target / 'behavior.bend', '-o', program])
                for n in oracle.SIZES:
                    actual = run([*runtime, program, n])
                    expected = oracle.expected(n)
                    output = receipt_dir / f'{attempt:03}-{variant}-{lane}-{n}.stdout.gz'
                    with gzip.open(output, 'wt') as f:
                        f.write(actual['stdout'])
                    actual['stdout_file'] = str(output.relative_to(ROOT))
                    actual['stdout_sha256'] = hashlib.sha256(actual['stdout'].encode()).hexdigest()
                    observed = actual.pop('stdout')
                    record['observations'].append({'variant': variant, 'lane': lane, 'size': n,
                        'records': 10*n, 'sections': 12, 'exact_match': observed == expected,
                        'expected_sha256': hashlib.sha256(expected.encode()).hexdigest(),
                        'program_sha256': digest(program), 'scope_sha256': digest(target / 'scope.bend'),
                        'command_index': len(record['commands']) - 1})
                    require(observed == expected, ('observation mismatch', variant, lane, n, str(output)))
        require(all(digest(HERE / name) == h for name, h in inputs.items()), 'inputs changed during gate')
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        receipt.write_text(json.dumps(record, indent=2) + '\n')
    print(f"Passed {len(record['observations'])} native/Bun observations; {receipt}")


if __name__ == '__main__':
    main()
