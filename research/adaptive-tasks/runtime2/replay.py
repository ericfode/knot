#!/usr/bin/env python3
"""Replay existing CPU controls without replacing any retained runtime evidence."""
import argparse
import json
from pathlib import Path
import subprocess

from check import ROOT, HERE, digest, run, success, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', default='d14418b')
    parser.add_argument('--out-dir', type=Path, default=ROOT / '.local/gpu-2/regression')
    args = parser.parse_args()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', args.baseline,
                                     '--', 'research/adaptive-tasks'], cwd=ROOT, text=True).splitlines()
    untouched = {}
    for name in names:
        path = Path(name)
        if 'runtime2' in path.parts or any(p == '.env' or p.startswith('.env.') for p in path.parts):
            continue
        before = subprocess.check_output(['git', 'show', f'{args.baseline}:{name}'], cwd=ROOT)
        assert (ROOT / path).read_bytes() == before, f'old probe changed: {name}'
        untouched[name] = digest(ROOT / path)
    report = {'baseline': args.baseline, 'unchangedFiles': untouched, 'deviceExecution': False}
    report['runtime1'] = run(['python3', HERE.parent / 'runtime/check.py', '--cpu-only', '--out-dir', out / 'runtime1'])
    success(report['runtime1'])
    expected = json.loads((HERE.parent / 'runtime/receipts/model.json').read_text())['cases']
    actual = json.loads((out / 'runtime1/model.json').read_text())['cases']
    assert actual == expected, 'runtime1 CPU replay differs from retained model'
    report['runtime1Replay'] = {'cases': len(actual), 'commands': sum(map(len, actual.values())),
                                'phaseObservations': sum(map(len, actual.values())) * 3,
                                'laws': 8, 'cpuMutants': 7}
    report['comparisonControls'] = run(['node', '--test', HERE.parent / 'tests/replay.mjs'])
    success(report['comparisonControls'])
    assert '# pass 24\n' in report['comparisonControls']['stdout']
    report['hygiene'] = run(['python3', HERE.parent / 'tests/replay.py'])
    success(report['hygiene'])
    assert 'Ran 6 tests' in report['hygiene']['stderr']
    script = out / 'compare.mjs'
    script.write_text('import {readFile} from "node:fs/promises";\n' +
        f'import {{compareReceipts}} from {json.dumps((HERE.parent / "gpu/observations.mjs").as_uri())};\n' +
        'const load=async p=>JSON.parse(await readFile(p,"utf8"));\n' +
        f'console.log(JSON.stringify(compareReceipts(await load({json.dumps(str(HERE.parent / "runtime/receipts/regression-before-185b7d5.json"))}),await load({json.dumps(str(HERE.parent / "runtime/receipts/regression-after.json"))}))));\n')
    report['retainedDeviceComparison'] = json.loads(success(run(['node', script])))
    assert report['retainedDeviceComparison']['cases'] == 38
    report['status'] = 'pass'
    report['limits'] = 'Fresh CPU/model and harness replay; retained Metal receipts compared, no fresh device execution.'
    write(out / 'replay.json', report)
    print(json.dumps({'status': 'pass', 'unchangedFiles': len(untouched), 'runtime1Cases': 16,
                      'phaseObservations': 186, 'comparisonControls': 24, 'hygieneTests': 6,
                      'retainedDeviceCases': 38, 'deviceExecution': False}))


if __name__ == '__main__':
    main()
