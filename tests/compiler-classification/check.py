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
from check_frontend import classified, digest, expectation, observed, require, run, successful  # noqa: E402


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
    inputs += [ROOT / 'tests/subsets/classification/function-parameter.bend']
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
            expected = expectation(case, 'parse')
            observed(actual, expected)
            record['fixtures'].append({'file': case['file'], 'reference': reference,
                                       'expected': expected, 'lanes': {'bun': actual}})

        # Each mutant changes an outcome, not syntax, typing, budgets, or tests.
        # A witness is a frozen manifest case. The kill is the mutant's code at
        # the witness's own span, or at a literal span for an accepted witness.
        # Generics removed the classify-2 type-application prefixes: the
        # parameter mutant keeps its anchor through the generics witness
        # function-parameter, the malformed twins witness the type grammar's
        # Unsupported fallback, and the accepted applications witness the
        # routes into that grammar.
        mutations = [
            ('nonleading-template', 'parse.bend', 'Bool.and(parameters,starts(t,"~"))', 'False{}',
             ['template-nonleading'], 'Unsupported\tparse\ttemplate-binder'),
            ('equality-as-binding', 'parse.bend', 'Bool.or(starts(tail,"="),starts(tail,">"))',
             'starts(tail,">")', ['destructure-equality'], 'Unsupported\tparse\tdestructuring-binding'),
            ('arrow-as-binding', 'parse.bend', 'Bool.or(starts(tail,"="),starts(tail,">"))',
             'starts(tail,"=")', ['destructure-arrow'], 'Unsupported\tparse\tdestructuring-binding'),
            ('parameter-application-invalid', 'parse.bend', 'unsupported(rest,"parameter-type")',
             'invalid(rest,"parameter-type")', ['function-parameter'], 'Invalid\tparse\tparameter-type'),
            ('type-expression-invalid', 'type-parse.bend',
             'Fail{S.Unsupported{"parse","type-expression",S.at(h)}}',
             'Fail{S.Invalid{"parse","type-expression",S.at(h)}}',
             ['application-parameter-after-prefix', 'application-return-after-prefix',
              'application-binding-after-prefix'], 'Invalid\tparse\ttype-expression'),
            ('return-application-untyped', 'parse.bend',
             'S.choose(Result<S.Error,Parsed>,typed_result(tokens),u =>',
             'S.choose(Result<S.Error,Parsed>,False{},u =>',
             ['application-return'], 'Invalid\tparse\tfunction-result\t46:47:5:11'),
            ('binding-application-untyped', 'parse.bend',
             'Bool.and(S.identifier(typ),starts(tail,"="))', 'S.identifier(typ)',
             ['application-binding'], 'Invalid\tparse\texpected-=\t65:66:6:10'),
        ]
        manifest = {Path(c['file']).stem: c for c in json.loads(MANIFEST.read_text())['cases']}
        for name, file, before, after, witnesses, wrong in mutations:
            directory = BUILD / name
            directory.mkdir(exist_ok=True)
            for source in sources:
                shutil.copyfile(source, directory / source.name)
            target = directory / file
            source = target.read_text()
            require(source.count(before) == 1, f'Mutation anchor: {name}')
            target.write_text(source.replace(before, after))
            checked = successful([*seed, directory / 'parse-cli.bend', '--check-only'])
            require(checked['stdout'].strip() == 'All terms check.', checked)
            mutated = directory / 'parse.js'
            built = successful([*seed, directory / 'parse-cli.bend', '-o', mutated])
            kills = []
            for witness in witnesses:
                case = manifest[witness]
                path = ROOT / 'tests/subsets' / case['file']
                require(digest(path) == case['sha256'], f"Frozen witness changed: {case['file']}")
                expected = expectation(case, 'parse')
                observed(run(['bun', output, path]), expected)
                diagnostic = wrong if wrong.count('\t') == 3 else (
                    wrong + '\t' + expected['diagnostic'].rsplit('\t', 1)[1])
                actual = run(['bun', mutated, path])
                classified(actual, {'exit': 3 if wrong.startswith('Unsupported') else 2,
                                    'diagnostic': diagnostic})
                require(actual['exit'] != expected['exit'], actual)
                kills.append({'witness': case['file'], 'expected': expected, 'actual': actual})
            record['mutants'].append({'name': name, 'file': file, 'before': before, 'after': after,
                                      'typecheck': checked, 'build': built,
                                      'mutated_sha256': digest(target), 'kills': kills,
                                      'outcome': 'semantic-kill'})
        require(all(digest(ROOT / p) == h for p, h in record['inputs'].items()),
                'Inputs changed during the gate')
        record['status'] = 'passed'
        print(f"PASS: {len(cases)} frozen seed outputs; {len(record['fixtures'])} parser observations; "
              f"{len(record['mutants'])} type-correct semantic mutants killed on "
              f"{sum(len(m['kills']) for m in record['mutants'])} witnesses; "
              '17 filled frontend laws (classify-2: 5 added, 1 narrowed; generics: 1 restated, 1 retired, '
              '2 added).')
    except Exception as error:
        record.update(status='failed', failure=str(error))
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')


if __name__ == '__main__':
    main()
