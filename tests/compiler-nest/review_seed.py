#!/usr/bin/env python3
"""Replay round-2 seed observations. --write is only for the pre-fix freeze."""
import argparse
import itertools
import json
import math
from pathlib import Path

import regen as oracle

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'review-expectations.json'


def observe(path):
    source = path.read_text()
    enums, entries, ids = oracle.boundary(source)
    case = {'name': path.stem, 'file': str(path.relative_to(oracle.ROOT)),
            'sha256': oracle.sha256(path), 'fields': any(
                not nullary for _, _, cs in oracle.declarations(source)[0] for _, nullary in cs)}
    command = ['bun', oracle.SEED, case['file']]
    main = {'command': command, **oracle.run(command)}
    assert main['exit'] in (0, 1), main
    case['seed'] = main
    case['calls'] = []
    if main['exit'] == 0:
        assert not main['stderr'], main
        for export, sig in entries.items():
            # Keep the large-column controls bounded; main still checks the book.
            if math.prod(len(enums[t]) for t in sig['parameters']) > 16:
                continue
            for args in itertools.product(*(enums[t] for t in sig['parameters'])):
                wpath, text, call, prefix = oracle.wrapper(case, export, list(args), sig['result'])
                oracle.publish(oracle.ROOT / wpath, text)
                result = oracle.run(['bun', oracle.SEED, wpath])
                name = oracle.decode(result['stdout'], prefix, enums[sig['result']])
                assert result['exit'] == 0 and not result['stderr'] and name is not None, result
                case['calls'].append({'export': export, 'ordinals': [enums[t].index(a) for t, a in zip(sig['parameters'], args)],
                    'type_id': ids[sig['result']], 'tag': enums[sig['result']].index(name), 'result': name,
                    'command': ['bun', oracle.SEED, wpath], 'observation': result})
        case['knot'] = {'exit': 0, 'outcome': 'Accepted'}
    else:
        assert main['stderr'].startswith('Error:'), main
        message = main['stderr']
        code = ('affine-reuse' if 'consumed more than once' in message else
                'free-name' if 'a defined name' in message else
                'erased-live' if 'expected : -_' in message else 'type-mismatch')
        case['knot'] = {'exit': 2, 'diagnostic': 'Invalid\tparse\t' if path.stem == 'comma-c4' else f'Invalid\tcheck\t{code}\t'}
    return case


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--write', action='store_true')
    write = args.parse_args().write
    result = {'basis': 'Copied reviewer repros; pinned seed and literal classification before fixes.',
              'seed': oracle.environment()[0], 'fixtures': [observe(p) for p in sorted((HERE / 'review-fixtures').glob('*.bend'))]}
    if write:
        MANIFEST.write_text(json.dumps(result, indent=2) + '\n')
    else:
        assert result == json.loads(MANIFEST.read_text()), 'round-2 seed observations changed'
    print(f"Round-2 seed: {len(result['fixtures'])} fixtures, {sum(len(c['calls']) for c in result['fixtures'])} calls; no differences")


if __name__ == '__main__':
    main()
