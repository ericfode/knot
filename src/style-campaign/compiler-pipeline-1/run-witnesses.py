#!/usr/bin/env python3
"""Invoke frozen Bend public-API calls and compare literal IO observations."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
phase = sys.argv[1]
assert phase in ('baseline', 'candidate')
BUILD = ROOT / '.local/style-campaign/compiler-pipeline-1' / phase / 'witnesses'
RECEIPT = HERE / 'receipts' / (phase + '-witnesses.json')
assert not RECEIPT.exists(), 'Do not overwrite a witness receipt.'
BUILD.mkdir(parents=True, exist_ok=True)
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
cases = json.loads((HERE / 'witnesses.json').read_text())
sources = sorted((ROOT / 'src').glob('*.bend'))
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
inputs = sources + [HERE / 'witnesses.json', Path(__file__)]
record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'status': 'incomplete', 'phase': phase,
          'inputs': {str(p.relative_to(ROOT)): digest(p) for p in inputs},
          'observations': []}

def run(argv):
    p = subprocess.run([str(x) for x in argv], cwd=ROOT, text=True,
                       capture_output=True, timeout=60)
    return {'argv': [str(x) for x in argv], 'exit': p.returncode,
            'stdout': p.stdout, 'stderr': p.stderr}

try:
    for path in sources:
        shutil.copyfile(path, BUILD / path.name)
    for case in cases:
        source = BUILD / (case['name'] + '.bend')
        source.write_text('import Base\nimport ./driver.bend as D\n'
                          'import ./syntax.bend as S\nimport ./parse.bend as P\n'
                          'import ./core.bend as C\n\n'
                          'def main() -> IO(Unit):\n  do IO<Unit>:\n'
                          '    IO.print("Before")\n    ' + case['call'] + '\n'
                          '    IO.print("After")\n')
        for lane in ('native', 'bun'):
            output = BUILD / (case['name'] + ('.js' if lane == 'bun' else ''))
            built = run([ROOT / 'scripts/bend-reference', source, '-o', output])
            assert built['exit'] == 0, built
            observed = run((['bun'] if lane == 'bun' else []) + [output])
            item = {'case': case['name'], 'lane': lane, 'build': built,
                    'source_sha256': digest(source), 'artifact_sha256': digest(output),
                    'expected': case['expected'], 'actual': observed}
            record['observations'].append(item)
            assert all(observed[k] == v for k, v in case['expected'].items()), item
    assert all(digest(ROOT / path) == sha for path, sha in record['inputs'].items()), 'Inputs changed'
    record['status'] = 'passed'
except Exception as error:
    record['status'] = 'failed'
    record['failure'] = repr(error)
    raise
finally:
    RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
print(f"PASS: {len(record['observations'])} direct driver IO observations; {RECEIPT}")
