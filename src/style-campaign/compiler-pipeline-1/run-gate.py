#!/usr/bin/env python3
"""Run an unchanged existing gate with private build and receipt destinations."""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GATES = {
    'frontend': 'tests/subsets/check_frontend.py',
    'checker': 'tests/compiler-checker/check.py',
    'wasm': 'tests/compiler-wasm/check.py',
    'fields': 'tests/compiler-fields/check.py',
    'structural': 'tests/compiler-structural/check.py',
}

phase, name = sys.argv[1:]
assert phase in ('baseline', 'candidate')
path = ROOT / GATES[name]
spec = importlib.util.spec_from_file_location('unchanged_gate', path)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
gate.BUILD = ROOT / '.local/style-campaign/compiler-pipeline-1' / phase / name
gate.RECEIPT = HERE / 'receipts' / (phase + '-' + name + '.json')
assert not gate.RECEIPT.exists(), 'Receipts are immutable; choose a fresh phase.'
gate.RECEIPT.parent.mkdir(parents=True, exist_ok=True)
if hasattr(gate, 'GENERATED'):
    gate.GENERATED = gate.BUILD / 'generated'
gate.main()
