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


DOTTED = ['a.b', '+a.b', '_.x', 'On.x', 'v.', 'a..b', 'a.1']


def programs(count=COUNT):
    rng = random.Random(SEED)

    def atom():
        return rng.choice(DOTTED) if rng.randrange(12) == 0 else rng.choice(
            ['Off{}', 'On{}', '_', 'v', 'w', 'x', '+v', '_x'])

    def sep():
        # Headers run to their colon; a line break inside one separates nothing.
        return rng.choice(('\n      ', ',\n      ')) if rng.randrange(8) == 0 else rng.choice((' ', ', '))

    for index in range(count):
        shape = rng.choice(('flag', 'multi', 'pair', 'box'))
        kind = rng.choice(('Type', 'Data'))
        # Live, reusable or erased binders of an empty datatype, before or after
        # the scrutinee, as parameters or fields; f is then uncallable.
        empty = rng.randrange(4) == 0
        y = 'y.z' if rng.randrange(10) == 0 else 'y'
        prefix = f'type Flag is {kind}:\n  Off{{}}\n  On{{}}\n\ntype Color is Data:\n  Red{{}}\n'
        prefix += f"\ntype V is {rng.choice(('Type', 'Data'))}:\n"
        fields = shape in ('pair', 'box')
        slots = ['a: Flag', 'b: Flag']
        if fields and empty and rng.randrange(2) == 0:
            slots.insert(rng.randrange(3), rng.choice(('', '', '-')) + 'e: V')
        if fields:
            prefix += '\ntype Pair is Type:\n  P{' + ', '.join(slots) + '}\n'
        if shape == 'box':
            prefix += '\ntype Box is Type:\n  B{p: Pair}\n'
        prefix += '\ndef both(a: Flag, b: Flag) -> Flag:\n  a\n'
        prefix += '\ndef id(a: Flag) -> Flag:\n  a\n'
        params = ['x: Flag', f'{y}: Flag', '-ghost: Flag']
        arguments = 'Off{}, On{}, Off{}'
        if fields:
            prefix += '\ndef left(p: Pair) -> Flag:\n  match p:\n    case P{' + ', '.join('_' if s.endswith('V') else s[0] for s in slots) + '}: a\n'
            params[0] = 'p: Pair' if shape == 'pair' else 'p: Box'
            arguments = ('P{Off{}, On{}}' if shape == 'pair' else 'B{P{Off{}, On{}}}') + ', On{}, Off{}'
        elif rng.randrange(8) == 0:
            params[0] = rng.choice(('-', '+')) + params[0]
        if empty:
            params.insert(rng.randrange(4), rng.choice(('', '', '-', '+')) + 'e: V')
        body_terms = ['On{}', 'Off{}', y, 'v', 'w', '_', 'nope', 'Red{}', 'a.b', 'e',
                      'ghost', 'both(v, v)', f'both({y}, {y})', f'both(v, {y})', 'both(w, w)']
        if not fields:
            body_terms += ['x', 'both(x, x)', 'both(x, v)']
        elif shape == 'pair':
            body_terms += ['left(p)', 'both(left(p), left(p))', 'left(v)']
        columns = ['x', y] if shape == 'multi' else ['p' if fields else 'x']
        if empty and shape == 'multi' and rng.randrange(2) == 0:
            columns.insert(rng.randrange(3), 'e')
        rows = []
        for _ in range(rng.randrange(0 if empty else 1, 8)):
            if shape == 'flag':
                pattern = atom()
            elif shape == 'multi':
                pattern = sep().join(atom() for _ in columns)
            else:
                pattern = 'P{' + ', '.join(atom() for _ in slots) + '}'
                if shape == 'box':
                    pattern = 'B{' + rng.choice((pattern, '_', 'v')) + '}'
                pattern = rng.choice((pattern, pattern, '_', 'v', '+v'))
            rows.append(f'    case {pattern}: {rng.choice(body_terms)}\n')
        scrutinee = sep().join(columns)
        source = prefix + f'\ndef f({", ".join(params)}) -> Flag:\n  match {scrutinee}:\n' + ''.join(rows)
        call = rng.choice(('On{}', 'Off{}')) if empty else f'f({arguments})'
        source += f'\ndef main() -> Flag:\n  {call}\n'
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
