#!/usr/bin/env python3
"""Verify fixed propositions, proof bodies, and the existing checker observations."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
registration = json.loads((HERE / 'registration.json').read_text())
freeze = json.loads((HERE / 'candidate/freeze.json').read_text())
receipt = HERE / 'gates/verification.json'
assert not receipt.exists()
record = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'status': 'incomplete', 'commands': []}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def tokens(source):
    # Preserve string contents, identifier boundaries, operators and punctuation.
    return [m.group() for m in re.finditer(
        r'"(?:[^"\\]|\\.)*"|#[^\n]*|[A-Za-z_][A-Za-z0-9_.]*|[0-9]+n?|==|->|<>|[^\s]',
        source) if not m.group().startswith('#')]

def verify_inputs():
    for name, expected in registration['inputs'].items():
        wanted = freeze['files']['check-LAWS.bend']['sha256'] if name == 'src/check-LAWS.bend' else expected
        assert sha(ROOT / name) == wanted, name
    for name, item in freeze['files'].items():
        assert sha(HERE / 'candidate' / (name + '.snapshot')) == item['sha256']
        assert sha(ROOT / 'src' / name) == item['sha256']

try:
    verify_inputs()
    before = (HERE / 'baseline/check-LAWS.bend.snapshot').read_text()
    after = (ROOT / 'src/check-LAWS.bend').read_text()
    assert tokens(before) == tokens(after), 'A theorem token changed'
    assert (HERE / 'baseline/check-PROOF.bend.snapshot').read_bytes() == (ROOT / 'src/check-PROOF.bend').read_bytes()
    split = r'(?=^law )'
    old = re.split(split, before, flags=re.M)
    new = re.split(split, after, flags=re.M)
    assert len(old) == len(new)
    changed = []
    for a, b in zip(old, new):
        if a != b:
            name = re.match(r'law ([^:]+):', a).group(1)
            assert name in registration['names']
            assert tokens(a) == tokens(b)
            changed.append(name)
    assert changed == registration['names']
    record.update({'complete_token_sequence_identical': True, 'proof_file_byte_identical': True,
                   'changed_laws': changed, 'other_declarations_byte_identical': True,
                   'frozen_input_files': len(registration['inputs'])})
    for entry in sorted((ROOT / 'src').glob('*PROOF.bend')):
        argv = [str(ROOT / 'scripts/bend-reference'), str(entry)]
        result = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=60)
        item = {'argv': argv, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
        record['commands'].append(item)
        assert result.returncode == 0 and result.stdout.strip() == 'All terms check.', item
    spec = importlib.util.spec_from_file_location('unchanged_checker_gate', ROOT / 'tests/compiler-checker/check.py')
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    gate.BUILD = ROOT / '.local/style-central-laws-1-checker-gate'
    gate.RECEIPT = HERE / 'gates/checker.json'
    assert not gate.RECEIPT.exists()
    record['existing_gate'] = {'path': 'tests/compiler-checker/check.py', 'sha256': sha(Path(gate.__file__)),
                               'overrides': {'BUILD': str(gate.BUILD), 'RECEIPT': str(gate.RECEIPT)},
                               'semantic_logic_and_assertions_changed': False}
    gate.main()
    fixed = json.loads(gate.RECEIPT.read_text())
    assert fixed['status'] == 'passed'
    record['observations'] = {'reference_fixtures': len(fixed['fixtures']),
        'native_and_bun': sum(len(x['lanes']) for x in fixed['fixtures']),
        'depth': len(fixed['budgets']), 'catalog_bound': 16,
        'semantic_mutants': len(fixed['mutants'])}
    verify_inputs()
    record['status'] = 'passed'
except Exception as error:
    record['failure'] = repr(error)
    raise
finally:
    receipt.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'status': record['status'], 'proof_entries': len(record['commands']),
                  'observations': record.get('observations')}))
