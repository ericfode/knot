#!/usr/bin/env python3
"""Extract the fixed five-law family without altering any theorem or proof body."""
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VIEW = ROOT / '.local/style-central-laws-1'
variant = sys.argv[1]
assert variant in ('baseline', 'candidate')
registration = json.loads((HERE / 'registration.json').read_text())
names = registration['names']
source = (HERE / 'baseline/check-LAWS.bend.snapshot' if variant == 'baseline'
          else ROOT / 'src/check-LAWS.bend').read_text()
proof = (ROOT / 'src/check-PROOF.bend').read_text()
assert proof == (HERE / 'baseline/check-PROOF.bend.snapshot').read_text()

def blocks(text, prefix):
    return dict((m.group(1), m.group(0).rstrip()) for m in re.finditer(
        rf'^{prefix} ([^\s(:]+)[\s\S]*?(?=^{prefix} |\Z)', text, re.M))

laws = blocks(source, 'law')
proofs = blocks(proof, 'def')
law_prefix = '\n'.join(source.splitlines()[:4]) + '\n\n'
assert 'import ./scope.bend as E' in law_prefix
files = {
    'check-LAWS.bend': law_prefix + '\n\n'.join(laws[n] for n in names) + '\n',
    'check-PROOF.bend': 'import Base\nimport ./check-LAWS.bend as L\n\n'
                      + '\n'.join(proofs['L.' + n] for n in names) + '\n',
}
for name in ('syntax.bend', 'core.bend', 'scope.bend'):
    path = ROOT / 'src' / name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == registration['inputs']['src/' + name]
    files[name] = path.read_text()
VIEW.mkdir(parents=True, exist_ok=True)
for name, body in files.items():
    (VIEW / name).write_text(body)
record = {
    'variant': variant,
    'scope': 'Exact five law/proof blocks; unused checker/frontend imports omitted only in the review projection. All supplied implementation modules are byte-identical originals.',
    'original_law_file_sha256': hashlib.sha256(source.encode()).hexdigest(),
    'original_proof_file_sha256': hashlib.sha256(proof.encode()).hexdigest(),
    'files': {name: {'sha256': hashlib.sha256(body.encode()).hexdigest(), 'source': body}
              for name, body in files.items()},
}
out = HERE / 'reviews' / (variant + '-family.json.gz')
assert not out.exists()
with gzip.open(out, 'wt') as f:
    json.dump(record, f, indent=2)
print(json.dumps({'variant': variant, 'projection': str(VIEW), 'files': len(files)}))
