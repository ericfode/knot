#!/usr/bin/env python3
"""Replay the immutable seed evidence for the parameter-bound witness amendment."""
import json

from regen import HERE, ROOT, SEED, relative, require, run, sha

WORK = ROOT / '.local/baseslice/review/bounds-amendment'
RECEIPT = HERE / 'receipts/bounds-amendment.json'


def main():
    document = json.loads(RECEIPT.read_text())
    require(document['status'] == 'passed', 'incomplete amendment receipt')
    for path, expected in document['seed'].items():
        require(sha((ROOT / path).read_bytes()) == expected, ('changed seed', path))
    WORK.mkdir(parents=True, exist_ok=True)
    for case in document['cases']:
        source = WORK / (case['name'] + '.bend')
        source.write_text(case['seed_source'])
        require(sha(source.read_bytes()) == case['sha256'], 'changed seed witness')
        require(run([*SEED, relative(source), '--check-only']) == case['check'], case['name'])
        require(run([*SEED, relative(source)]) == case['interpreter'], case['name'])
        output = WORK / case['name']
        output.unlink(missing_ok=True)
        require(run([*SEED, relative(source), '-o', relative(output)]) == case['native_build'], case['name'])
        if case['check']['exit'] == 0:
            require(output.is_file() and run(['./' + relative(output)]) == case['native'], case['name'])
        else:
            require(not output.exists(), 'rejected seed witness emitted a binary')
    print('bounds amendment: four frozen seed witnesses reproduced')


if __name__ == '__main__':
    main()
