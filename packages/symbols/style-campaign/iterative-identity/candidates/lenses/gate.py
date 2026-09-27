#!/usr/bin/env python3
import hashlib
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path('/Users/ericfode/src/knot')
BEND = ROOT / 'scripts/bend-reference'
variant = pathlib.Path(sys.argv[1]).resolve()
tag = sys.argv[2]
dest = variant / f'gates-{tag}.json'
if dest.exists():
    raise SystemExit(f'receipt already exists: {dest}')
records = []
hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in variant.glob('*.bend')}
(variant / f'main-{tag}.bend.snapshot').write_bytes((variant / 'main.bend').read_bytes())

def run(command, expected=None):
    start = time.monotonic()
    result = subprocess.run([str(x) for x in command], cwd=ROOT, text=True, capture_output=True, timeout=180)
    record = {'command': [str(x) for x in command], 'exit': result.returncode,
              'stdout': result.stdout, 'stderr': result.stderr,
              'elapsed_seconds': time.monotonic() - start}
    records.append(record)
    ok = result.returncode == 0 and (expected is None or result.stdout.strip() == expected)
    print(json.dumps({'command':record['command'],'exit':result.returncode,'elapsed_seconds':record['elapsed_seconds'],
                      'output':(result.stdout+result.stderr)[-5000:],'passed':ok}), flush=True)
    dest.write_text(json.dumps({'source_sha256':hashes,'records':records,'completed':False},indent=2)+'\n')
    if not ok:
        raise SystemExit(1)

run([BEND, variant/'main.bend', '--check-only'], 'All terms check.')
run([BEND, variant/'PROOF.bend', '--check-only'], 'All terms check.')
for lane in ['js','native']:
    output=variant/('conformance.js' if lane=='js' else 'conformance-native')
    run([BEND,variant/'conformance.bend','-o',output])
    run(['bun',output] if lane=='js' else [output],'1')
current={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in variant.glob('*.bend')}
assert current==hashes, 'source changed during gates'
dest.write_text(json.dumps({'source_sha256':hashes,'records':records,'completed':True},indent=2)+'\n')
