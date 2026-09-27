#!/usr/bin/env python3
"""Record one explicitly selected local compiler invocation for an owned round."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

arm = Path(__file__).resolve().parent
root = arm.parents[3]
number = int(sys.argv[1])
stage = sys.argv[2]
assert 1 <= number <= 10 and stage in ('first', 'repair')
directory = arm / f'round-{number:02d}'
source = directory / 'life.bend'
assert not (directory / 'started.json').exists()
assert not (directory / f'compiler-{stage}.json').exists()
if stage == 'repair':
    assert json.loads((directory / 'compiler-first.json').read_text())['exit_code'] != 0
snapshot = directory / ('first.bend.snapshot' if stage == 'first' else 'repaired.bend.snapshot')
with snapshot.open('xb') as stream:
    stream.write(source.read_bytes())
argv = ['scripts/bend-reference', str(source.relative_to(root)), '--check-only']
start = time.monotonic()
process = subprocess.run(argv, cwd=root, capture_output=True)
record = {'argv': argv, 'exit_code': process.returncode, 'seconds': time.monotonic()-start,
          'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'stdout': process.stdout.decode(), 'stderr': process.stderr.decode()}
with (directory / f'compiler-{stage}.json').open('x') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
print(json.dumps(record, indent=2))
