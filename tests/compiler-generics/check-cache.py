#!/usr/bin/env python3
"""Executable cache controls: changed input and corrupted output never reuse a build."""
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('generics_gate', Path(__file__).with_name('check.py'))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
gate.BUILD = gate.ROOT / '.local/generics/cache-controls'
gate.BUILD.mkdir(parents=True, exist_ok=True)
entry = gate.BUILD / 'main.bend'
dependency = gate.BUILD / 'value.bend'
entry.write_text('import Base\nimport ./value.bend as V\n\ndef main() -> U32:\n  V.value()\n')
rows = []
for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
    executable = gate.BUILD / ('control' + suffix)
    # A new entry name isolates these controls from any earlier run.
    for n, label in [(7, 'initial'), (7, 'reuse'), (8, 'dependency-change')]:
        dependency.write_text(f'import Base\n\ndef value() -> U32:\n  {n}\n')
        built = gate.build(entry, executable)
        result = gate.successful([*runtime, executable])
        gate.require(result['stdout'] == f'{n}\n', (label, result))
        if label == 'reuse':
            gate.require(built['cached'], ('identical build must be reused', lane))
        if label == 'dependency-change':
            gate.require(not built['cached'], ('changed dependency must rebuild', lane))
        rows.append({'lane': lane, 'control': label, 'cached': built['cached'], 'stdout': result['stdout']})
    # Corrupt every cached artifact, not the executable being invoked.
    for path in (gate.BUILD / 'build-cache').iterdir():
        if path.suffix != '.json':
            path.write_bytes(b'corrupt build cache\n')
    rebuilt = gate.build(entry, executable)
    gate.require(not rebuilt['cached'], ('corrupt artifact must rebuild', lane))
    gate.require(gate.successful([*runtime, executable])['stdout'] == '8\n', lane)
    rows.append({'lane': lane, 'control': 'corrupt-artifact', 'cached': False})
    dependency.write_text('import Base\n\ndef value() -> U32:\n  False{}\n')
    try:
        gate.build(entry, executable)
    except AssertionError as error:
        gate.require('expected' in str(error) and 'observed' in str(error), error)
    else:
        raise AssertionError(('seed-invalid source must not reuse a build', lane))
    rows.append({'lane': lane, 'control': 'seed-invalid-source', 'refused': True})
(gate.BUILD / 'controls.json').write_text(json.dumps(rows, indent=2) + '\n')
print('PASS: 10 executable cache controls in native and Bun; changed dependencies, corrupt artifacts and seed-invalid sources refuse reuse.')
