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


def classified(actual, expected, phase="parse"):
    if expected["exit"] == 0:
        require(actual["exit"] == 0 and actual["stderr"] == "", actual)
        if phase in ("parse", "eval"):
            require(actual["stdout"].strip() == expected[phase + "_stdout"], actual)
        else:
            require(actual["stdout"].startswith("Checked\n" if phase == "check" else "Built\t"), actual)
        return
    require(actual['exit'] == expected['exit'], actual)
    require(actual['stdout'] == '', actual)
    require(actual['stderr'].strip() == expected['diagnostic'], actual)


def classification(record, manifest, lanes, source_paths):
    # A frozen local cache exercises the seed's hash loader without a hub request.
    module = manifest['hash_import']
    require(digest(HERE / module['module']) == module['module_sha256'], module)
    require(module['manifest'] == module['module_sha256'] + ' module.bend\n', module)
    require(module['package'] == '0x' + hashlib.sha256(module['manifest'].encode()).hexdigest()[:32], module)
    library = BUILD / 'classification-lib'
    package = library / module['package']
    package.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE / module['module'], package / 'module.bend')
    (package / 'manifest').write_text(module['manifest'])
    require({str(p.relative_to(HERE)) for p in (HERE / 'classification').glob('*.bend')} ==
            {c['file'] for c in manifest['cases']} | {module['module']},
            'Classification fixture/manifest coverage mismatch')
    record['fixtures'] = []
    for case in manifest['cases']:
        path = HERE / case['file']
        ref = run(['env', f'BEND_LIB={library}', 'BEND_NO_TELEMETRY=1', SEED, path])
        expected = case['reference']
        require(ref['exit'] == expected['exit'], ref)
        if expected['exit'] == 0:
            require(ref['stdout'].strip() == expected['value'] and ref['stderr'] == '', ref)
        else:
            require(expected['diagnostic_contains'] in ref['stderr'], ref)
        item = {'file': case['file'], 'reference': ref, 'lanes': {}}
        for name, command in lanes.items():
            actual = run([*command, path])
            classified(actual, case['knot'])
            item['lanes'][name] = actual
        record['fixtures'].append(item)

    record['downstream_builds'] = []
    record['downstream'] = []
    for phase in ('check', 'eval', 'compile'):
        for lane in ('bun', 'native'):
            output = BUILD / ('classification-' + phase + ('.js' if lane == 'bun' else ''))
            built = successful([SEED, ROOT / 'src' / (phase + '-cli.bend'), '-o', output])
            record['downstream_builds'].append({'phase': phase, 'lane': lane, 'build': built,
                                                'sha256': digest(output)})
            command = ['bun', output] if lane == 'bun' else [output]
            for case in manifest['cases']:
                arguments = [HERE / case['file']]
                artifact = BUILD / 'classification-rejected.wasm'
                if phase == 'eval':
                    arguments += ['main', '65536']
                if phase == 'compile':
                    artifact.write_bytes(b'prior artifact\n')
                    arguments.append(artifact)
                actual = run([*command, *arguments])
                classified(actual, case['knot'], phase)
                if phase == 'compile':
                    if case['knot']['exit'] == 0:
                        executed = successful(['node', ROOT / 'scripts/run-wasm.mjs', artifact, 'main'])
                        require(json.loads(executed['stdout'])['result'] == case['knot']['wasm_tag'], executed)
                    else:
                        require(artifact.read_bytes() == b'prior artifact\n', actual)
                record['downstream'].append({'phase': phase, 'lane': lane, 'file': case['file'],
                                              'output_preserved': phase == 'compile' and case['knot']['exit'] != 0, **actual})

    record['mutants'] = []
    mutations = [
        ('generic-invalid', 'unsupported(tokens,"generic-datatype")',
         'invalid(tokens,"generic-datatype")', 'generic'),
        ('match-invalid', 'run(n,MatchTail{token,columns(value,more),column},rest)',
         'invalid(tokens,"match-scrutinees")', 'match'),
        ('template-invalid', 'unsupported(ts,"template-binder")',
         'invalid(ts,"template-binder")', 'template'),
        ('destructure-invalid', 'unsupported(ts,"destructuring-binding")',
         'invalid(ts,"destructuring-binding")', 'destructure'),
        ('import-invalid', 'unsupported(Con{name,tokens},"import")',
         'invalid(Con{name,tokens},"import")', 'local-import'),
        ('malformed-unsupported', 'Fail{S.Invalid{"parse",code,S.here(ts)}}',
         'Fail{S.Unsupported{"parse",code,S.here(ts)}}', 'template-malformed'),
        ('expected-unsupported', 'S.Invalid{"parse",String.append("expected-",word),S.at(h)}',
         'S.Unsupported{"parse",String.append("expected-",word),S.at(h)}', 'generic-malformed'),
    ]
    for label, before, after, witness in mutations:
        directory = BUILD / label
        directory.mkdir(exist_ok=True)
        for p in source_paths:
            shutil.copyfile(p, directory / p.name)
        target = directory / 'parse.bend'
        source = target.read_text()
        require(source.count(before) == 1, f'Classification mutation anchor: {label}')
        target.write_text(source.replace(before, after))
        checked = successful([SEED, directory / 'parse-cli.bend', '--check-only'])
        require(checked['stdout'].strip() == 'All terms check.', checked)
        output = directory / 'cli.js'
        built = successful([SEED, directory / 'parse-cli.bend', '-o', output])
        case = next(c for c in manifest['cases'] if Path(c['file']).stem == witness)
        actual = run(['bun', output, HERE / case['file']])
        require(actual['exit'] == (3 if case['knot']['exit'] == 2 else 2), actual)
        if case['knot']['exit'] == 0:
            require(actual['stdout'] == '' and actual['stderr'].startswith('Invalid\tparse\tmatch-scrutinees\t'), actual)
        else:
            require(actual['stdout'] == '' and
                    actual['stderr'].split('\t', 1)[1] == case['knot']['diagnostic'].split('\t', 1)[1] + '\n', actual)
        record['mutants'].append({'name': label, 'before': before, 'after': after,
                                  'typecheck': checked, 'build': built,
                                  'mutated_sha256': digest(target), 'witness': case['file'],
                                  'expected': case['knot'], 'actual': actual,
                                  'outcome': 'semantic-kill'})


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((HERE / 'frontend-cases.json').read_text())
    classification_manifest = json.loads((HERE / 'classification-cases.json').read_text())
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'scope': 'Parser checkpoint, not checked source-to-Wasm compilation',
              'seed_revision': manifest['seed_revision'], 'status': 'incomplete'}
    try:
        source_paths = sorted((ROOT / 'src').glob('*.bend'))
        fixture_paths = sorted((HERE / 's1').glob('*.bend'))
        paths = source_paths + fixture_paths + [HERE / 'frontend-cases.json',
                HERE / 'lexer-observe.bend', Path(__file__)]
        paths += sorted((HERE / 'classification').glob('*.bend')) + [HERE / 'classification-cases.json']
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
            ('fields', 'type Box is Type:\n  Box{x: Box}\n', [], 0, 'Parsed\ttype Box Type(Box{1 x:Box})'),
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
        record['classification'] = {}
        classification(record['classification'], classification_manifest, lanes, source_paths)
        require(all(digest(ROOT / p) == h for p, h in record['inputs'].items()),
                'Inputs changed during the gate')
        record['status'] = 'passed'
        print(f"PASS: {len(record['fixtures'])} reference fixtures, two parser lanes, "
              f"{len(record['boundaries'])} boundary observations, four boundary laws, six classification laws "
              f"and four semantic mutants; "
              f"{len(record['classification']['fixtures'])} classification fixtures in two lanes, "
              f"{len(record['classification']['mutants'])} classification mutants, "
              f"{len(record['classification']['downstream'])} downstream rejection observations")
    except Exception as error:
        record['status'] = 'failed'
        record['failure'] = str(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')


if __name__ == '__main__':
    main()
