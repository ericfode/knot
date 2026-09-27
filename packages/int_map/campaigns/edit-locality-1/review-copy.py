"""Combine unchanged laws/fills for the observer's missing imported-template context.

This is a review view, not a replacement proof module or a new candidate.
Only import paths and the G namespace qualification change. Both source
modules must match the retained diagnostic-retry snapshots.
"""
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[4]
P = ROOT / 'packages/int_map'
OUT = pathlib.Path(__file__).resolve().parent
BUILD = P / 'build/edit-locality-1'
BUILD.mkdir(parents=True, exist_ok=True)
sources = {}
for name in ('LAWS', 'PROOF'):
    text = (P / f'locality/{name}.bend').read_text()
    assert text == (OUT / f'candidate-retry-{name}.bend.snapshot').read_text()
    sources[name] = text

header = '''# SPDX-License-Identifier: MIT-0
# Mechanical review view; canonical source: locality/LAWS.bend + locality/PROOF.bend.
import Base
import ../../main.bend as M
import ../../LAWS.bend as L
import ../../PROOF.bend as Original
'''
law_body = sources['LAWS'].split('import ../LAWS.bend as L\n', 1)[1]
proof_body = sources['PROOF'].split('import ./LAWS.bend as G\n', 1)[1]
view = header + law_body + '\n' + proof_body.replace('G.', '')
target = BUILD / 'review.bend'
target.write_text(view)
(OUT / 'review.bend.snapshot').write_text(view)
(OUT / 'review-copy.json').write_text(json.dumps(dict(
    canonical_files={f'locality/{name}.bend': hashlib.sha256(text.encode()).hexdigest()
                     for name, text in sources.items()},
    review_file=str(target.relative_to(ROOT)),
    review_sha256=hashlib.sha256(view.encode()).hexdigest(),
    transforms=['Combine the unchanged law body and proof body in source order.',
                'Remove only the local G. qualification from proof-body references.',
                'Retarget the three existing package imports for the build directory.'],
    omitted_source_declarations=0, canonical_automatic_style_coverage=False,
    reason='Observer lacks template-clause context for imported law fills.'), indent=2) + '\n')
print(target)
