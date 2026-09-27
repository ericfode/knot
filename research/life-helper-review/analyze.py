#!/usr/bin/env python3
"""Summarize unchanged-source judgments; do not average incompatible rubrics."""
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REPORT = HERE / 'receipts/runs/ec8dcc5eeb1ad6efe74cb25f25f91be9f4849f243dfebe8c4693379d593430d6.json'


def main():
    report = json.loads(REPORT.read_text())
    assert report['status'] == 'complete'
    entries = report['entries']
    groups = []
    for group in ['historical-original', 'historical-continuation', 'r2-v3']:
        rows = [e for e in entries if e['manifest_entry']['group'] == group]
        reviewed = [e for e in rows if e['coverage']['complete']]
        axes = []
        for target in report['policy']['config']['family_targets']:
            assessments = [next(a for a in e['family_assessments']
                                if a['dimension'] == target['dimension']) for e in reviewed]
            axes.append(dict(dimension=target['dimension'], target=target,
                assessed=len(assessments), met=sum(a['status'] == 'meets_target' for a in assessments),
                median_target_mass=statistics.median(a['target_probability'] for a in assessments),
                maximum_target_mass=max(a['target_probability'] for a in assessments)))
        groups.append(dict(group=group, submissions=len(rows), reviewed=len(reviewed),
            behavior_passed=sum(e['deterministic_passed'] is True for e in rows),
            semantic_clean=sum(e['semantic_clean'] is True for e in rows),
            old_full_pass=sum(e['manifest_entry']['legacy_full_pass'] is True for e in rows),
            new_full_pass=sum(e['full_pass'] for e in rows),
            new_support_pass=sum(e['support_passed'] for e in rows),
            new_family_pass=sum(e['family_passed'] for e in rows), family_axes=axes))
    source_checks = []
    for e in entries:
        source = ROOT / e['source']
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        assert actual == e['source_sha256'], e['id']
        source_checks.append(dict(id=e['id'], source=e['source'], source_sha256=actual,
            status=e['status'], deterministic_passed=e['deterministic_passed'],
            semantic_clean=e['semantic_clean'], old_full_pass=e['manifest_entry']['legacy_full_pass'],
            new_full_pass=e['full_pass'], family_passed=e['family_passed'],
            support_passed=e['support_passed'], family_assessments=e['family_assessments'],
            support_assessments=e['support_assessments']))
    result = dict(schema='life-helper-comparison-v1', report=str(REPORT.relative_to(ROOT)),
        report_sha256=hashlib.sha256(REPORT.read_bytes()).hexdigest(),
        policy_sha256=report['policy']['sha256'], requested_model=report['requested_model'],
        calibration_status='development-separated-held-out-target-separation-failed',
        default_adoption_qualified=False, summary=report['summary'], groups=groups,
        support_declarations_assessed=sum(len(e['support_assessments']) for e in entries),
        support_declarations_met=sum(a['status'] == 'meets_target' for e in entries for a in e['support_assessments']),
        interpretation='Helpers commonly qualify under the support question, but every reviewed family remains below the Galaxy target. Old v2 and new family policy are different standards; their pass rates are not a causal improvement measure. These are post-hoc judgments, not new author trials or evidence of an inducer effect.',
        entries=source_checks)
    (HERE / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'summary': result['summary'], 'source_hashes_verified': len(source_checks),
                      'support_declarations_met': result['support_declarations_met'],
                      'support_declarations_assessed': result['support_declarations_assessed']}))


if __name__ == '__main__':
    main()
