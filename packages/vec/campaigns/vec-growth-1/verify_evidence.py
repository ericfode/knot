#!/usr/bin/env python3
"""Verify saved evidence and frozen inputs without rerunning inference or gates."""
from pathlib import Path
import hashlib
import json
import statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
load = lambda name: json.loads((HERE / name).read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
reg = load('preregistration.json')
source = sha(ROOT / 'packages/vec/main.bend')
assert source == sha(HERE / 'candidate-1.snapshot') == load('candidate-1-first-check.json')['source_sha256']
assert load('candidate-1-first-check.json')['exit'] == 0
assert sha(HERE / 'before.snapshot') == reg['baseline_source_sha256']
for path, expected in {**reg['frozen_files_sha256'], **reg['tooling_sha256']}.items():
    assert sha(ROOT / path) == expected, path
before, after = load('baseline-style.json'), load('candidate-1-style.json')
assert len(before['rows']) == len(after['rows']) == 12
assert all(r['source_sha256'] == source for r in after['rows'])
assert after['status'] == 'completed' and after['source_freshness']['status'] == 'current'
assert after['provider_requests'] == after['provider_responses'] == 12
assert all(r['model'] == 'jev-1.13.0' for r in before['rows'] + after['rows'])
gates, mutants, scaling = load('gates/gates.json'), load('gates/mutations.json'), load('gates/scaling.json')
assert gates['source_sha256']['main.bend'] == source
assert gates['proof']['exit'] == 0
for category in ['conformance', 'generic']:
    for backend in ['native', 'js']:
        r = gates[category][backend]
        assert r['build']['exit'] == r['run']['exit'] == 0
        assert r['run']['stdout'].strip() == 'True{}'
assert len(mutants) == 9
assert all(r['typecheck']['exit'] == 0 and r['runtime']['run']['exit'] == 0
           and r['runtime']['run']['stdout'].strip() == 'False{}'
           and r['proof_rejection']['exit'] != 0 for r in mutants)
assert [r['n'] for r in scaling] == [4096, 16384, 65536, 262144]
assert all(r['build']['exit'] == 0 and len(r['runs']) == 3
           and all(x['exit'] == 0 and x['stdout'].strip() == r['expected'] for x in r['runs']) for r in scaling)
semantic = []
for name in ['plan_step', 'push_ready', 'law-packet']:
    r = load(name + '-semantic-receipt.json')
    result = load(name + '-semantic-result.json')
    # issue_count and issues are nullable; inspect findings, broken and clean.
    assert r['status'] == 'completed' and r['findings'] == []
    assert result['broken'] == [] and result['issues'] in (None, []) and result['clean']
    assert r['provider_requests'] == r['provider_responses'] == 1
    semantic.append(r)
summary = {
    'status': 'passed', 'candidate_equals_first_shot': True, 'compiler_retry_used': False,
    'frozen_files_checked': len(reg['frozen_files_sha256']), 'tooling_identities_unchanged': True,
    'release_evidence_unchanged': True, 'mutation_locators_unchanged': True,
    'source_sha256': source, 'preregistration_sha256': sha(HERE / 'preregistration.json'),
    'baseline_exact_identity_reused': 12, 'style_review_units': 12, 'fresh_style_requests': 12,
    'semantic_checked': sum(r['checked'] for r in semantic), 'semantic_findings': 0,
    'disposition': 'accepted-unreleased; style-needs-review', 'gate_run': load('gate-run.json'),
    'scaling': [{'n': r['n'], 'median_seconds': statistics.median(x['seconds'] for x in r['runs']),
                 'expected': r['expected']} for r in scaling],
}
(HERE / 'validation.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
