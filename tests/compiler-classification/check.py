#!/usr/bin/env python3
"""Replay frozen classification controls and kill type-correct parser mutants."""
from __future__ import annotations

import datetime
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/compiler-classification'
RECEIPT = HERE / 'receipts/precision.json'
MANIFEST = ROOT / 'tests/subsets/classification-cases.json'

sys.path.insert(0, str(ROOT / 'tests/subsets'))
from check_frontend import classified, digest, require, run, successful  # noqa: E402


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    cases = [c for c in json.loads(MANIFEST.read_text())['cases']
             if c.get('increment') == 'classify-2']
    require(len(cases) == 17, 'The frozen classify-2 controls must remain complete')
    seed = ['bun', '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']
    sources = sorted((ROOT / 'src').glob('*.bend'))
    inputs = sources + [MANIFEST, Path(__file__), ROOT / 'tests/subsets/check_frontend.py']
    inputs += [ROOT / 'tests/subsets' / c['file'] for c in cases]
    record = {
        'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'incomplete',
        'scope': 'Parser classification precision; no new executable language capability',
        'seed_revision': json.loads(MANIFEST.read_text())['seed_revision'],
        'inputs': {str(p.relative_to(ROOT)): digest(p) for p in inputs},
        'fixtures': [], 'mutants': [],
    }
    try:
        record['proof'] = successful([*seed, 'src/PROOF.bend'])
        require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
        output = BUILD / 'parse.js'
        record['build'] = successful([*seed, 'src/parse-cli.bend', '-o', output])
        record['generated_sha256'] = digest(output)
        for case in cases:
            path = ROOT / 'tests/subsets' / case['file']
            require(digest(path) == case['sha256'], f"Frozen fixture changed: {case['file']}")
            expected = case['reference']
            require(expected['command'] == [*seed, str(path.relative_to(ROOT))], expected)
            reference = run(expected['command'])
            require(reference['exit'] == expected['exit'], reference)
            for stream in ('stdout', 'stderr'):
                require(reference[stream].replace(str(ROOT), '$ROOT') == expected[stream], reference)
            actual = run(['bun', output, path])
            classified(actual, case['knot'])
            record['fixtures'].append({'file': case['file'], 'reference': reference,
                                       'expected': case['knot'], 'lanes': {'bun': actual}})

        # Each mutant changes an outcome, not syntax, typing, budgets, or tests.
        mutations = [
            ('nonleading-template', 'Bool.and(parameters,starts(t,"~"))', 'False{}',
             'template-nonleading', 'Unsupported\tparse\ttemplate-binder'),
            ('equality-as-binding', 'Bool.or(starts(tail,"="),starts(tail,">"))',
             'starts(tail,">")', 'destructure-equality', 'Unsupported\tparse\tdestructuring-binding'),
            ('arrow-as-binding', 'Bool.or(starts(tail,"="),starts(tail,">"))',
             'starts(tail,"=")', 'destructure-arrow', 'Unsupported\tparse\tdestructuring-binding'),
            ('parameter-application-invalid', 'unsupported(rest,"parameter-type")',
             'invalid(rest,"parameter-type")', 'application-parameter', 'Invalid\tparse\tparameter-type'),
            ('return-application-invalid', 'unsupported(Con{colon,body},"type-application")',
             'invalid(Con{colon,body},"type-application")', 'application-return', 'Invalid\tparse\ttype-application'),
            ('binding-application-invalid', 'unsupported(tail,"type-application")',
             'invalid(tail,"type-application")', 'application-binding', 'Invalid\tparse\ttype-application'),
        ]
        for name, before, after, witness, wrong in mutations:
            directory = BUILD / name
            directory.mkdir(exist_ok=True)
            for source in sources:
                shutil.copyfile(source, directory / source.name)
            target = directory / 'parse.bend'
            source = target.read_text()
            require(source.count(before) == 1, f'Mutation anchor: {name}')
            target.write_text(source.replace(before, after))
            checked = successful([*seed, directory / 'parse-cli.bend', '--check-only'])
            require(checked['stdout'].strip() == 'All terms check.', checked)
            mutated = directory / 'parse.js'
            built = successful([*seed, directory / 'parse-cli.bend', '-o', mutated])
            case = next(c for c in cases if Path(c['file']).stem == witness)
            actual = run(['bun', mutated, ROOT / 'tests/subsets' / case['file']])
            span = case['knot']['diagnostic'].rsplit('\t', 1)[1]
            classified(actual, {'exit': 3 if wrong.startswith('Unsupported') else 2,
                                'diagnostic': wrong + '\t' + span})
            require(actual['exit'] != case['knot']['exit'], actual)
            record['mutants'].append({'name': name, 'before': before, 'after': after,
                                      'typecheck': checked, 'build': built,
                                      'mutated_sha256': digest(target), 'witness': case['file'],
                                      'expected': case['knot'], 'actual': actual,
                                      'outcome': 'semantic-kill'})
        require(all(digest(ROOT / p) == h for p, h in record['inputs'].items()),
                'Inputs changed during the gate')
        record['status'] = 'passed'
        print(f"PASS: {len(cases)} frozen seed outputs; {len(record['fixtures'])} parser observations; "
              f"{len(record['mutants'])} type-correct semantic mutants killed; "
              '16 filled frontend laws (6 added, 1 narrowed).')
    except Exception as error:
        record.update(status='failed', failure=str(error))
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')


if __name__ == '__main__':
    main()
