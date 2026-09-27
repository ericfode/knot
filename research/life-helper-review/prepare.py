#!/usr/bin/env python3
"""Index retained round submissions without changing any historical artifact."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    entries = []
    original = read('research/life-blueberry/results.json')
    for arm, result in original['arms'].items():
        checks = original['semantic_checks'][arm]
        entries.append(dict(
            id=f'original-{arm}', group='historical-original', arm=arm,
            source=result['source'], source_sha256=result['source_sha256'],
            deterministic_passed=result['gates_pass'],
            semantic_clean=checks['checked'] > 0 and checks['threshold_findings'] == 0,
            legacy_receipt='research/life-blueberry/receipts/style.json',
            legacy_policy='v2', legacy_full_pass=result['gates_pass'] and result['full_style_pass'],
            legacy_all_style_pass=result['full_style_pass'],
            legacy_axes=result['axes'],
            author_request={'model': 'gpt-6-astra', 'effort': 'max'},
        ))

    continuation = read('research/life-blueberry/iteration/results.json')
    for arm, result in continuation['arms'].items():
        for round_ in result['history']:
            entries.append(dict(
                id=f'continuation-{arm}-{round_["round"]:02d}',
                group='historical-continuation', arm=arm, round=round_['round'],
                source=round_['source'], source_sha256=round_['source_sha256'],
                deterministic_passed=round_['behavior_passed'],
                semantic_clean=round_.get('semantic_clean'),
                legacy_receipt=round_.get('review_receipt'),
                legacy_policy='v2', legacy_full_pass=round_['full_pass'],
                legacy_all_style_pass=round_['full_pass'],
                legacy_axes=round_.get('axes'),
                legacy_status=round_['status'],
                recovered=round_.get('recovered', False),
                author_request={'model': 'gpt-6-astra', 'effort': 'max'},
            ))

    search = read('research/life-inducer-hillclimb-r2/interrupted-results.json')
    for trial in search['results']:
        for round_ in trial['rounds']:
            review = read(round_['reviews_receipt']) if round_.get('reviews_receipt') else None
            entries.append(dict(
                id=f'r2-{trial["id"]}-{round_["number"]:02d}', group='r2-v3',
                trial=trial['id'], round=round_['number'], stimulus=trial['stimulus'],
                source=round_['source'], source_sha256=round_['source_sha256'],
                deterministic_passed=round_['behavior_passed'],
                semantic_clean=review.get('semantic_clean') if review else None,
                legacy_receipt=review.get('style_receipt') if review else None,
                legacy_policy='v3', legacy_full_pass=round_['full_pass'],
                legacy_all_style_pass=review.get('style_passed') if review else None,
                legacy_axes=review.get('style', {}).get('axes') if review else None,
                legacy_status=round_['status'],
                author_request={'model': trial['model'], 'effort': trial['effort']},
            ))

    assert len(entries) == 63 and len({e['id'] for e in entries}) == 63
    for entry in entries:
        assert sha(entry['source']) == entry['source_sha256'], entry['id']
        if entry['legacy_receipt']:
            assert (ROOT / entry['legacy_receipt']).is_file(), entry['legacy_receipt']
            entry['legacy_receipt_sha256'] = sha(entry['legacy_receipt'])
    result = dict(schema='life-helper-review-manifest-v1', root=str(ROOT),
        scope='All 63 retained final round submissions: two originals, sixteen continuation rounds, forty-five interrupted R2 rounds.',
        comparison='Post-hoc new-policy review of unchanged source; v2 and v3 baselines are separate. Author and condition metadata must not enter judge requests.',
        entries=entries)
    output = HERE / 'manifest.json'
    if output.exists():
        assert json.loads(output.read_text()) == result, 'Refusing to overwrite a different manifest'
    else:
        output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'entries': len(entries), 'source_hashes_verified': len(entries),
                      'behavior_passed': sum(e['deterministic_passed'] is True for e in entries),
                      'semantic_clean': sum(e['semantic_clean'] is True for e in entries),
                      'manifest_sha256': sha(output.relative_to(ROOT))}))


if __name__ == '__main__':
    main()
