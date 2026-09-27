#!/usr/bin/env python3
"""Run the frozen gate with campaign receipts; leave release evidence untouched."""
import hashlib
import importlib.util
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
registration = json.loads((HERE / 'preregistration.json').read_text())
for name, expected in registration['frozen_files_sha256'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
spec = importlib.util.spec_from_file_location('vec_gate', ROOT / 'packages/vec/scripts/gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
gate.RECEIPTS = HERE / 'gates'
gate.RECEIPTS.mkdir(exist_ok=False)
start = time.monotonic()
result = {'command': 'python3 packages/vec/campaigns/vec-growth-1/run_gates.py', 'completed': []}
try:
    for name in ['gates', 'mutations', 'scaling']:
        getattr(gate, name)()
        result['completed'].append(name)
    result['status'] = 'passed'
except Exception as error:
    result['status'] = 'failed'
    result['failure'] = str(error)
    raise
finally:
    result['seconds'] = time.monotonic() - start
    (HERE / 'gate-run.json').write_text(json.dumps(result, indent=2) + '\n')
