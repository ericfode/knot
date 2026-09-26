#!/usr/bin/env python3
"""Compile and independently gate one Bend performance-repair candidate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PIN = ROOT / '.toolchain/bend-2.0.29-574b6d3'
CASES = ('growing-prefix-copy', 'invariant-summary', 'indexed-linked-list')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', required=True, choices=CASES)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    candidate = args.candidate.resolve()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    artifacts = output.with_suffix('.artifacts')
    artifacts.mkdir(exist_ok=True)
    report = {'schema': 1, 'case': args.case, 'candidate': str(candidate),
              'passed': False, 'status': 'harness-error', 'checks': []}
    start = time.monotonic()
    # Do not pass credentials into compiler, instrumenter, or candidate runtime.
    env = {key: os.environ[key] for key in ('PATH', 'HOME', 'TMPDIR', 'LANG') if key in os.environ}

    def run(name, command, timeout=60):
        t0 = time.monotonic()
        result = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                capture_output=True, timeout=timeout)
        (artifacts / f'{name}.stdout').write_text(result.stdout)
        (artifacts / f'{name}.stderr').write_text(result.stderr)
        report['checks'].append({'name': name, 'exit_code': result.returncode,
                                 'seconds': time.monotonic() - t0})
        if result.returncode:
            raise RuntimeError(f'{name} failed; see {artifacts / (name + ".stderr")}')
        return result

    try:
        lock_path = HERE / 'gate-lock.json'
        lock = json.loads(lock_path.read_text())
        report['gate_lock_sha256'] = digest(lock_path)
        report['compiler'] = lock['compiler']
        for relative, wanted in lock['files'].items():
            if digest(ROOT / relative) != wanted:
                raise RuntimeError(f'Frozen gate changed: {relative}')
        report['candidate_sha256'] = digest(candidate)
        source = candidate.read_text()
        # Restrict this bounded list benchmark to ordinary, pure Bend definitions.
        # Not a security sandbox: the model receives no filesystem/tool execution.
        uncommented = '\n'.join(line.split('#', 1)[0] for line in source.splitlines())
        imports = re.findall(r'^\s*import\s+(.+)$', uncommented, re.M)
        if imports != ['Base']:
            report['status'] = 'candidate-rejected'
            raise RuntimeError('Candidate must import only Base exactly once')
        forbidden = re.search(r'\b(?:Array|Buffer|String|IO|GPU|extern|foreign|axiom)\b|@|\?', uncommented)
        if forbidden:
            report['status'] = 'candidate-rejected'
            raise RuntimeError(f'Unsupported benchmark construct: {forbidden.group(0)}')
        saved = artifacts / 'candidate.bend'
        saved.write_text(source)
        wrapper = artifacts / 'entry.bend'
        wrapper.write_text('import Base\nimport ./candidate.bend as C\n\n'
                           'def call(xs: List<&2,U32>) -> List<&2,U32>:\n  C.solve(xs)\n')
        report['status'] = 'compile-failed'
        run('check', [str(ROOT / 'scripts/bend-reference'), str(wrapper), '--check-only'])
        raw = artifacts / 'compiled.mjs'
        measured = artifacts / 'instrumented.mjs'
        sites = artifacts / 'sites.json'
        run('compile', ['bun', str(HERE / 'compile.ts'), str(wrapper), str(raw)])
        report['status'] = 'harness-error'
        run('instrument', ['node', str(HERE / 'instrument.mjs'), str(raw), str(measured), str(sites)])
        results = artifacts / 'results.json'
        run('execute', ['node', str(HERE / 'run.mjs'), args.case, str(measured), str(results)])
        report.update(json.loads(results.read_text()))
        report['instrumentation_sites'] = json.loads(sites.read_text())
        report['compiled_sha256'] = digest(raw)
        report['instrumented_sha256'] = digest(measured)
        if digest(candidate) != report['candidate_sha256']:
            raise RuntimeError('Candidate changed during evaluation')
        report['passed'] = report['correctness']['pass'] and report['performance']['pass']
        report['status'] = 'passed' if report['passed'] else 'gate-failed'
    except Exception as error:
        report['error'] = str(error)
    report['seconds'] = time.monotonic() - start
    report['artifacts'] = str(artifacts)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'case': args.case, 'passed': report['passed'],
                      'status': report['status'], 'output': str(output)}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
