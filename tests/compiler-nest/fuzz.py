#!/usr/bin/env python3
"""Fixed-seed differential control; the pinned seed supplies every verdict."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random

import check as gate

SEED = 0x4E455354
COUNT = 3000


def programs(count=COUNT):
    rng = random.Random(SEED)
    for index in range(count):
        shape = rng.choice(('flag', 'multi', 'pair', 'box'))
        kind = rng.choice(('Type', 'Data'))
        prefix = f'type Flag is {kind}:\n  Off{{}}\n  On{{}}\n\ntype Color is Data:\n  Red{{}}\n'
        fields = shape in ('pair', 'box')
        if fields:
            prefix += '\ntype Pair is Type:\n  P{a: Flag, b: Flag}\n'
        if shape == 'box':
            prefix += '\ntype Box is Type:\n  B{p: Pair}\n'
        prefix += '\ndef both(a: Flag, b: Flag) -> Flag:\n  a\n'
        prefix += '\ndef id(a: Flag) -> Flag:\n  a\n'
        params = 'x: Flag, y: Flag, -ghost: Flag'
        arguments = 'Off{}, On{}, Off{}'
        if fields:
            prefix += '\ndef left(p: Pair) -> Flag:\n  match p:\n    case P{a, b}: a\n'
            params = ('p: Pair' if shape == 'pair' else 'p: Box') + ', y: Flag, -ghost: Flag'
            arguments = ('P{Off{}, On{}}' if shape == 'pair' else 'B{P{Off{}, On{}}}') + ', On{}, Off{}'
        elif rng.randrange(8) == 0:
            params = rng.choice(('-', '+')) + params
        body_terms = ['On{}', 'Off{}', 'y', 'v', 'w', '_', 'nope', 'Red{}',
                      'ghost', 'both(v, v)', 'both(y, y)', 'both(v, y)', 'both(w, w)']
        if not fields:
            body_terms += ['x', 'both(x, x)', 'both(x, v)']
        elif shape == 'pair':
            body_terms += ['left(p)', 'both(left(p), left(p))', 'left(v)']
        atoms = ['Off{}', 'On{}', '_', 'v', 'w', 'x', '+v', '_x']
        rows = []
        for _ in range(rng.randrange(1, 8)):
            if shape == 'flag':
                pattern = rng.choice(atoms)
            elif shape == 'multi':
                pattern = rng.choice(atoms) + rng.choice((' ', ', ')) + rng.choice(atoms)
            else:
                pattern = f'P{{{rng.choice(atoms)}, {rng.choice(atoms)}}}'
                if shape == 'box':
                    pattern = 'B{' + rng.choice((pattern, '_', 'v')) + '}'
                pattern = rng.choice((pattern, pattern, '_', 'v', '+v'))
            rows.append(f'    case {pattern}: {rng.choice(body_terms)}\n')
        scrutinee = 'p' if fields else ('x' + rng.choice((' y', ', y')) if shape == 'multi' else 'x')
        source = prefix + f'\ndef f({params}) -> Flag:\n  match {scrutinee}:\n' + ''.join(rows)
        source += f'\ndef main() -> Flag:\n  f({arguments})\n'
        yield index, fields, source


def classify(result, seed=False):
    if seed:
        if result['exit'] == 0 and not result['stderr']:
            return 'Accepted'
        if result['exit'] == 1 and result['stderr'].startswith('Error:'):
            return 'Invalid'
    else:
        outcome = {0: 'Accepted', 2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted',
                   5: 'HostFailure', 6: 'InternalFailure'}.get(result['exit'])
        if outcome == 'Accepted':
            gate.checked(result)
        elif outcome:
            gate.require(result['stderr'].startswith(outcome + '\t') and not result['stdout'], result)
        if outcome in ('Accepted', 'Invalid', 'Unsupported', 'Exhausted'):
            return outcome
    raise AssertionError(('fuzz host/internal failure', result))


def check(lanes, directory, count=COUNT):
    directory.mkdir(parents=True, exist_ok=True)
    cases = list(programs(count))

    def compare(case):
        index, fields, source = case
        path = directory / f'{index:04d}.bend'
        path.write_text(source)
        seed = gate.run([*gate.SEED, path])
        observed = gate.run([*lanes['native']['check'], path])
        reference, actual = classify(seed, seed=True), classify(observed)
        record = {'index': index, 'sha256': hashlib.sha256(source.encode()).hexdigest(),
                  'seed': reference, 'knot': actual, 'seed_output': seed['stdout'], 'diagnostic': observed['stderr']}
        if reference == 'Invalid' and actual == 'Accepted':
            record['failure'] = 'seed rejects, Knot accepts'
        elif reference == 'Accepted' and actual == 'Invalid':
            record['failure'] = 'D4: seed accepts, Knot reports Invalid'
        if reference == actual == 'Accepted':
            expected = seed['stdout'].strip()
            tag = {'Off{}': 0, 'On{}': 1}.get(expected)
            gate.require(tag is not None, seed)
            result = gate.run([*lanes['native']['eval'], path, 'main', 65536])
            gate.evaluated(result, {'type_id': 0, 'tag': tag, 'result': expected[:-2]})
            record['evaluated'] = tag
        return record

    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(compare, cases))
    failures = [r for r in records if 'failure' in r]
    summary = {'random_seed': SEED, 'programs': len(records), 'generator_sha256': gate.digest(Path(__file__)),
               'seed_outcomes': dict(Counter(r['seed'] for r in records)),
               'knot_outcomes': dict(Counter(r['knot'] for r in records)),
               'false_acceptances': sum(r.get('failure') == 'seed rejects, Knot accepts' for r in records),
               'false_invalid': sum(r.get('failure', '').startswith('D4:') for r in records),
               'evaluator_values': sum('evaluated' in r for r in records), 'failures': failures,
               'observations_sha256': hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()}
    (directory / 'observations.json').write_text(json.dumps(records, indent=2) + '\n')
    (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    gate.require(not failures, ('fuzz classification mismatch', summary))
    return summary
