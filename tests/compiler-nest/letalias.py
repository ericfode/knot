#!/usr/bin/env python3
"""Round-7 let/alias differential; the pinned seed supplies every verdict.

`program` is the reviewer's generator (sem-r7-probes/lg/gen.py), verbatim, over
the random seeds 0 to 1499. Each program binds one or two lets over two Flag
parameters of random quantity and matches the latest let with a single
variable or `+` row. The seed and Knot must agree on acceptance; where both
accept, every call of `f` must agree between the seed and the Knot evaluator.
The generator declares only `Data` types; round-7 fixtures cover `Type` kinds.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import itertools
import json
from pathlib import Path
import random

import check as gate
import fuzz
import regen as oracle

SEEDS = range(0, 1500)

HDR = '''type Flag is Data:
  Off{}
  On{}

type Box is Data:
  B{f: Flag}
  E{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def keep(a: Flag, -b: Flag) -> Flag:
  a
'''
def use(r, names, n):
    # produce an expression using a random multiset of names
    if n == 0 or not names: return r.choice(['On{}', 'Off{}'])
    if n == 1:
        x = r.choice(names)
        return x if r.random() < 0.7 else f'keep(On{{}}, {x})'
    a = use(r, names, 1); b = use(r, names, n - 1)
    return f'both({a}, {b})'
def program(seed):
    r = random.Random(seed)
    pq = [r.choice(['', '+', '-']) for _ in range(2)]
    params = [f'{q}a: Flag', f'{pq[1]}b: Flag'] if False else [f'{pq[0]}a: Flag', f'{pq[1]}b: Flag']
    live = [n for n, q in zip(['a', 'b'], pq) if q != '-']
    erased = [n for n, q in zip(['a', 'b'], pq) if q == '-']
    body = []
    nlets = r.choice([1, 1, 2])
    names = list(live)
    for i in range(nlets):
        kq = r.choice(['', '', '+', '-'])
        src = r.choice(names + ['On{}', 'both(a, b)'] if names else ['On{}'])
        ann = ' : Flag' if src.endswith('}') or r.random() < 0.3 else ''
        body.append(f'  {kq}k{i}{ann} = {src}')
        if kq != '-': names.append(f'k{i}')
        else: erased.append(f'k{i}')
    last = f'k{nlets-1}'
    rows = []
    rq = r.choice(['', '+', '+'])
    y = 'y'
    inner = names + [y] + (erased if r.random() < 0.2 else [])
    rows.append(f'    case {rq}{y}: ' + use(r, inner, r.choice([1, 2, 2, 3])))
    body.append(f'  match {last}:')
    body += rows
    return HDR + '\ndef f(' + ', '.join(params) + ') -> Flag:\n' + '\n'.join(body) + '\n'


def compare(seed, path, check, evaluate):
    source = program(seed)
    path.write_text(source)
    reference = fuzz.classify(gate.run([*gate.SEED, path]), seed=True)
    actual = fuzz.classify(gate.run([*check, path]))
    record = {'seed': seed, 'sha256': hashlib.sha256(source.encode()).hexdigest(),
              'promoted': '    case +y:' in source, 'reference': reference, 'knot': actual}
    if reference == 'Invalid' and actual == 'Accepted':
        record['failure'] = 'seed rejects, Knot accepts'
    elif reference == 'Accepted' and actual == 'Invalid':
        record['failure'] = 'D4: seed accepts, Knot reports Invalid'
    enums, entries, ids = oracle.boundary(source)
    if reference == actual == 'Accepted' and evaluate and 'f' in entries:
        record['calls'] = []
        for arguments in itertools.product(*(enums[t] for t in entries['f']['parameters'])):
            fixture = {'name': path.stem, 'file': str(path.relative_to(gate.ROOT))}
            wpath, text, call, prefix = oracle.wrapper(fixture, 'f', list(arguments), 'Flag')
            (gate.ROOT / wpath).parent.mkdir(parents=True, exist_ok=True)
            (gate.ROOT / wpath).write_text(text)
            observed = gate.run([*gate.SEED, gate.ROOT / wpath])
            name = oracle.decode(observed['stdout'], prefix, enums['Flag'])
            gate.require(observed['exit'] == 0 and not observed['stderr'] and name is not None, observed)
            ordinals = [enums['Flag'].index(a) for a in arguments]
            value = gate.run([*evaluate, path, 'f', 65536, *ordinals])
            gate.evaluated(value, {'type_id': ids['Flag'], 'tag': enums['Flag'].index(name), 'result': name})
            record['calls'].append({'ordinals': ordinals, 'result': name})
    return record


def check(check, directory, evaluate=None):
    """Classify every program with `check`; evaluate agreed acceptances with `evaluate`."""
    directory.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(lambda s: compare(s, directory / f'l{s:05d}.bend', check, evaluate), SEEDS))
    failures = [r for r in records if 'failure' in r]
    summary = {'seeds': [SEEDS.start, SEEDS.stop - 1], 'programs': len(records),
               'generator_sha256': gate.digest(Path(__file__)),
               'promoted_rows': sum(r['promoted'] for r in records),
               'seed_outcomes': dict(Counter(r['reference'] for r in records)),
               'knot_outcomes': dict(Counter(r['knot'] for r in records)),
               'false_acceptances': sum(r.get('failure') == 'seed rejects, Knot accepts' for r in records),
               'false_invalid': sum(r.get('failure', '').startswith('D4:') for r in records),
               'evaluated_programs': sum('calls' in r for r in records),
               'evaluator_values': sum(len(r.get('calls', ())) for r in records),
               'failures': [{'seed': r['seed'], 'failure': r['failure'], 'promoted': r['promoted']} for r in failures],
               'observations_sha256': hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()}
    (directory / 'observations.json').write_text(json.dumps(records, indent=2) + '\n')
    (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


def main():
    args = argparse.ArgumentParser(description='Classify the let/alias programs with one checker binary.')
    args.add_argument('checker')
    args.add_argument('directory')
    options = args.parse_args()
    summary = check([Path(options.checker).resolve()], Path(options.directory).resolve())
    print(json.dumps({k: v for k, v in summary.items() if k != 'failures'}, sort_keys=True))
    print(' '.join(f"l{f['seed']:05d}" for f in summary['failures']))


if __name__ == '__main__':
    main()
