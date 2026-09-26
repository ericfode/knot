#!/usr/bin/env python3
"""Build/drive Bend code and compare fixed observations; no compiler semantics."""
from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/compiler-frontend'
RECEIPT = HERE / 'receipts/frontend.json'
SEED = ROOT / 'scripts/bend-reference'


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, *, timeout=30):
    try:
        p = subprocess.run([str(x) for x in argv], cwd=ROOT, text=True,
                           capture_output=True, timeout=timeout)
        return {'argv': [str(x) for x in argv], 'exit': p.returncode,
                'stdout': p.stdout, 'stderr': p.stderr}
    except subprocess.TimeoutExpired:
        return {'argv': [str(x) for x in argv], 'exit': None,
                'outcome': 'Exhausted', 'budget_seconds': timeout,
                'stdout': '', 'stderr': ''}


def successful(argv):
    result = run(argv)
    require(result['exit'] == 0, result)
    return result


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((HERE / 'frontend-cases.json').read_text())
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'scope': 'Parser checkpoint, not checked source-to-Wasm compilation',
              'seed_revision': manifest['seed_revision'], 'status': 'incomplete'}
    try:
        source_paths = sorted((ROOT / 'src').glob('*.bend'))
        fixture_paths = sorted((HERE / 's1').glob('*.bend'))
        paths = source_paths + fixture_paths + [HERE / 'frontend-cases.json',
                HERE / 'lexer-observe.bend', Path(__file__)]
        record['inputs'] = {str(p.relative_to(ROOT)): digest(p) for p in paths}
        record['tools'] = {name: successful([name, '--version'])['stdout'].strip()
                           for name in ('bun', 'node', 'python3')}
        record['proof'] = successful([SEED, ROOT / 'src/PROOF.bend'])
        require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
        js = BUILD / 'parse-cli.js'
        native = BUILD / 'parse-cli'
        record['builds'] = [successful([SEED, ROOT / 'src/parse-cli.bend', '-o', p])
                            for p in (js, native)]
        record['generated'] = {str(p.relative_to(ROOT)): digest(p) for p in (js, native)}
        lanes = {'bun': ['bun', js], 'native': [native]}
        record['fixtures'] = []
        require({str(p.relative_to(HERE)) for p in fixture_paths} ==
                {x['file'] for x in manifest['cases']}, 'Fixture/manifest coverage mismatch')
        for case in manifest['cases']:
            path = HERE / case['file']
            ref = run([SEED, path])
            expected = case['reference']
            require(ref['exit'] == expected['exit'], ref)
            if expected['exit'] == 0:
                require(ref['stdout'].strip() == expected['value'], ref)
            else:
                require(expected['diagnostic_contains'] in ref['stderr'], ref)
            item = {'file': case['file'], 'reference': ref, 'lanes': {}}
            for name, command in lanes.items():
                actual = successful([*command, path])
                require(actual['stdout'].strip() == 'Parsed\t' + case['tree'], actual)
                item['lanes'][name] = actual
            record['fixtures'].append(item)

        lexer_expected = (
            '<nl>@3:4:1:3;a@5:6:2:1;<eof>@7:7:2:3;\n'
            'alpha.beta@0:10:1:0;(@10:11:1:10;foo@11:14:1:11;'
            ')@14:15:1:14;<eof>@15:15:1:15;\n'
            'Exhausted\tlex\tbudget\t1:1:1:1\n'
            '<eof>@0:0:1:0;\n')
        record['lexer_observation'] = successful([SEED, HERE / 'lexer-observe.bend'])
        require(record['lexer_observation']['stdout'] == lexer_expected,
                record['lexer_observation'])

        flag = (HERE / 's1/flag.bend').read_text()
        transformed = BUILD / 'comments.bend'
        transformed.write_text('# leading comment\n\n' + flag.replace('  Off{}', '  Off{} # tail'))
        for name, command in lanes.items():
            actual = successful([*command, transformed])
            require(actual['stdout'].strip() == 'Parsed\t' + manifest['cases'][0]['tree'], actual)

        record['boundaries'] = []
        boundary_cases = [
            ('lex-zero', flag, ['0', '512'], 4, 'Exhausted\tlex'),
            ('parse-zero', flag, ['65536', '0'], 4, 'Exhausted\tparse'),
            ('parse-small', flag, ['65536', '3'], 4, 'Exhausted\tparse'),
            ('source-exact', ' ' * 65536, [], 0, 'Parsed\t'),
            ('source-over', ' ' * 65537, [], 4, 'Exhausted\tlex'),
            ('import', 'import Base\n', [], 3, 'Unsupported\tparse'),
            ('fields', 'type Box is Type:\n  Box{x: Box}\n', [], 3, 'Unsupported\tparse\tconstructor-fields'),
            ('literal', 'def main() -> Flag:\n  "text"\n', [], 3, 'Unsupported\tlex\tliteral'),
            ('unicode', '# é\n', [], 3, 'Unsupported\tlex\tnon-ascii'),
            ('missing-colon', 'def main() -> Flag\n  On{}\n', [], 2, 'Invalid\tparse\tfunction-result'),
            ('indent', 'def main() -> Flag:\nOn{}\n', [], 2, 'Invalid\tparse\tbody-indentation'),
            ('options', flag, ['65537', '512'], 5, 'HostFailure\targuments'),
        ]
        for label, source, options, status, prefix in boundary_cases:
            path = BUILD / f'{label}.bend'
            path.write_text(source)
            for name, command in lanes.items():
                actual = run([*command, path, *options])
                require(actual['exit'] == status, actual)
                output = actual['stdout'] if status == 0 else actual['stderr']
                require(output.startswith(prefix), actual)
                record['boundaries'].append({'case': label, 'lane': name, **actual})

        record['mutants'] = []
        mutations = [
            ('word-spelling', 'lex.bend', 'String.reverse(rev)', '"discarded"', 'proof', 'word_source'),
            ('zero-depth-accept', 'parse.bend',
             'case 0n _: Fail{S.Exhausted{"parse",S.here(tokens)}}',
             'case 0n _: Done{Parsed{S.Sequence{Nil{}},tokens}}', 'proof', 'no_parser_budget'),
            ('reverse-sequence', 'parse.bend', 'S.Sequence{Con{head,items}}',
             'S.Sequence{List.append(&2,S.Node,items,Con{head,Nil{}})}', 'tree', None),
            ('reuse-default', 'parse.bend', 'parameter_parts(1,ts)',
             'parameter_parts(2,ts)', 'tree', None),
        ]
        for label, file, before, after, gate, law in mutations:
            directory = BUILD / label
            directory.mkdir(exist_ok=True)
            for p in source_paths:
                shutil.copyfile(p, directory / p.name)
            target = directory / file
            original = target.read_text()
            require(before in original, f'Mutation anchor missing: {label}')
            target.write_text(original.replace(before, after))
            typecheck = successful([SEED, directory / 'parse-cli.bend', '--check-only'])
            item = {'name': label, 'file': file, 'before': before, 'after': after,
                    'typecheck': typecheck, 'mutated_sha256': digest(target)}
            if gate == 'proof':
                rejected = run([SEED, directory / 'PROOF.bend'])
                require(rejected['exit'] == 1 and law in rejected['stderr'] and
                        'expected' in rejected['stderr'], rejected)
                item.update({'killed_by': law, 'result': rejected})
            else:
                output = directory / 'cli.js'
                item['build'] = successful([SEED, directory / 'parse-cli.bend', '-o', output])
                actual = successful(['bun', output, HERE / 's1/flag.bend'])
                require(actual['stdout'].startswith('Parsed\t'), actual)
                require(actual['stdout'].strip() != 'Parsed\t' + manifest['cases'][0]['tree'], actual)
                item.update({'killed_by': 'unchanged Flag tree observation', 'result': actual})
            record['mutants'].append(item)
        require(all(digest(ROOT / p) == h for p, h in record['inputs'].items()),
                'Inputs changed during the gate')
        record['status'] = 'passed'
        print(f"PASS: {len(record['fixtures'])} reference fixtures, two parser lanes, "
              f"{len(record['boundaries'])} boundary observations, four laws and four semantic mutants")
    except Exception as error:
        record['status'] = 'failed'
        record['failure'] = str(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')


if __name__ == '__main__':
    main()
