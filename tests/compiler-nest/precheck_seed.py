#!/usr/bin/env python3
"""Freeze the precheck probes with the pinned seed before changing the parser."""
import hashlib
import json
from pathlib import Path

import check as gate

HERE = Path(__file__).resolve().parent
EXPECT = HERE / 'precheck-expectations.json'
DIGESTS = {
    '208934010de44d63': 'forward-pattern',
    '4304fba29c0c7ed1': 'dead-minus-list',
    '6852b91f4976a029': 'dead-minus-value',
    '8583b8be9bce45eb': 'dotted-binder',
    'cc0ef3b84774b2f8': 'dead-minus-constructor',
    'd60650b715505586': 'dead-minus-parens',
    'f3d0539e6c7bc793': 'dead-minus-spaced-brace',
}


def sources():
    rows = [json.loads(line) for line in
            (gate.ROOT / 'tests/prechecks/registry/lang.jsonl').read_text().splitlines() if line.strip()]
    result = {DIGESTS[row['sha256'][:16]]: row['text'] for row in rows if row['sha256'][:16] in DIGESTS}
    result['forward-pattern'] = ('type V is Type:\n\ndef f(x: V, y: Flag) -> Flag:\n'
                                 '  match x y:\n    case _ On{}: Off{}\n\ndef main() -> Flag:\n'
                                 '  On{}\n\ntype Flag is Data:\n  Off{}\n  On{}\n')
    prelude = ('type Flag is Data:\n  Off{}\n  On{}\n\ntype Cell is Data:\n'
               '  Cell{value: Flag}\n\ndef f() -> Flag:\n  On{}\n  - x = ')
    for name, value in [('dead-minus-list', '[On{}]'), ('dead-minus-value', 'On{}'),
                        ('dead-minus-constructor', 'Cell{On{}}'), ('dead-minus-parens', '(On{})'),
                        ('dead-minus-spaced-brace', 'On {}')]:
        result[name] = prelude + value + '\n'
    gate.require(len(result) == len(DIGESTS), 'missing frozen precheck probe')
    for digest, name in DIGESTS.items():
        gate.require(hashlib.sha256(result[name].encode()).hexdigest().startswith(digest), name)
    text = result['forward-pattern']
    flag = 'type Flag is Data:\n  Off{}\n  On{}\n'
    result['declared-pattern'] = flag + '\n' + text.removesuffix(flag)
    result['forward-expression'] = text.replace('  match x y:\n    case _ On{}: Off{}', '  On{}')
    result['discarded-forward-pattern'] = text.replace('    case _ On{}:', '    case _ _: y\n    case _ On{}:')
    return result


def seed_parse(paths):
    actual = gate.successful(['bun', '--no-env-file', gate.ROOT / 'scripts/prechecks/seedparse.ts',
                             (gate.ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/bend.ts').resolve(), *paths])
    return [{k: row[k] for k in ('ok', 'exp', 'beg') if k in row} for row in json.loads(actual['stdout'])]


def seed_check(path):
    return gate.run(['bun', '--no-env-file', gate.SEED[-1], path, '--check-only'])


def main():
    gate.require(not EXPECT.exists(), 'the freeze is immutable')
    directory = HERE / 'precheck-fixtures'
    directory.mkdir(exist_ok=True)
    programs = sources()
    paths = []
    for name, text in programs.items():
        path = directory / (name + '.bend')
        path.write_text(text)
        paths.append(path)
    fixed = []
    for (name, text), path, parsed in zip(programs.items(), paths, seed_parse(paths)):
        checked = seed_check(path)
        code = 'dotted-binder' if name == 'dotted-binder' else 'operator'
        knot = ({'exit': 2, 'diagnostic': 'Invalid\tcheck\tunknown-constructor\t'}
                if 'forward-pattern' in name else
                {'exit': 0} if name in ('declared-pattern', 'forward-expression') else
                {'exit': 3, 'diagnostic': f'Unsupported\tparse\t{code}\t'})
        gate.require(parsed['ok'] == (knot['exit'] == 0), (name, parsed))
        gate.require((checked['exit'] == 0) == parsed['ok'], (name, checked))
        fixed.append({'name': name, 'file': str(path.relative_to(gate.ROOT)),
                      'sha256': hashlib.sha256(text.encode()).hexdigest(), 'knot': knot,
                      'seed_parse': parsed, 'seed_check': {k: checked[k] for k in ('exit', 'stdout', 'stderr')}})
    EXPECT.write_text(json.dumps({'schema': 1, 'seed_revision': '574b6d39a235b539eb19a5c532993a0abb3d11ad',
                                 'fixtures': fixed}, indent=2) + '\n')
    print(f'Frozen {len(fixed)} precheck probes and controls before the parser repair.')


if __name__ == '__main__':
    main()
