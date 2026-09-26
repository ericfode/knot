#!/usr/bin/env python3
"""Reproduce positive/negative performance controls and semantic mutant kills."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CASES = ('growing-prefix-copy', 'invariant-summary', 'indexed-linked-list')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
output = args.output.resolve()
output.parent.mkdir(parents=True, exist_ok=True)
receipts = output.with_suffix('.receipts')
receipts.mkdir(exist_ok=True)
rows = []
for case in CASES:
    variants = [('baseline/main.bend', True, False), ('clean/main.bend', True, True),
                ('held-out/broken.bend', True, False), ('held-out/clean.bend', True, True),
                ('fresh-held-out/broken.bend', True, False), ('fresh-held-out/clean.bend', True, True),
                ('mutants/wrong-order.bend', False, False), ('mutants/smoke-shortcut.bend', False, False),
                ('constant-empty', False, False)]
    for variant, correct, performance in variants:
        source = HERE / ('mutants/constant-empty.bend' if variant == 'constant-empty'
                         else f'cases/{case}/{variant}')
        receipt = receipts / f'{case}-{variant.replace("/", "-")}.json'
        subprocess.run([sys.executable, str(HERE / 'evaluate.py'), '--case', case,
                        '--candidate', str(source), '--output', str(receipt)], check=False)
        r = json.loads(receipt.read_text())
        compiled = any(c['name'] == 'compile' and c['exit_code'] == 0 for c in r['checks'])
        observed_correct = r.get('correctness', {}).get('pass')
        observed_performance = r.get('performance', {}).get('pass')
        pass_ = compiled and observed_correct == correct and observed_performance == performance
        rows.append({'case': case, 'source': str(source.relative_to(HERE)),
                     'source_sha256': r['candidate_sha256'], 'expected_correctness': correct,
                     'expected_performance': performance, 'expectation_met': pass_, 'result': r})
summary = {'schema': 1, 'gate_lock_sha256': hashlib.sha256((HERE / 'gate-lock.json').read_bytes()).hexdigest(),
           'passed': all(x['expectation_met'] for x in rows), 'controls': rows}
output.write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({'passed': summary['passed'], 'controls': len(rows), 'output': str(output)}))
sys.exit(0 if summary['passed'] else 1)
