#!/usr/bin/env python3
"""Round-8 Type-kind promotion differential; the pinned seed supplies every verdict.

`gen` is the reviewer's generator (sem-r8-probes/pb/gen.py), verbatim from
`def header` to `gen`, over the random seeds 0 to 2999: parameters, lets,
aliases, `+` rows and nested field binders over `Type`- and `Data`-kind
boxes, with a `probe` entry over Sel. The seed and Knot must agree on
acceptance: a seed rejection is never Checked, and a seed acceptance is never
Invalid (Unsupported and Exhausted do not accept). Where both accept a program
with a `+` binder and a `Type`-kind box, one seeded probe call must agree
between the seed and the Knot evaluator.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import itertools
import json
from pathlib import Path
import random
import re

import check as gate
import fuzz
import regen as oracle

SEEDS = range(0, 3000)
# A `+` row or field binder in a program with a Type-kind Wrap (Box may be too).
PROMOTED = re.compile(r'case .*\+v')


def header(kb, kw):
    return f'''type Flag is Data:
  Off{{}}
  On{{}}

type Box is {kb}:
  B{{f: Flag}}
  E{{}}

type Wrap is {kw}:
  W{{b: Box, -g: Flag}}

type Sel is Data:
  S0{{}}
  S1{{}}
  S2{{}}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{{}}: b
    case Off{{}}: Off{{}}

def keep(a: Flag, -b: Flag) -> Flag:
  a

def bkeep(a: Flag, -b: Box) -> Flag:
  a

def bx(x: Box) -> Flag:
  match x:
    case B{{f}}: f
    case E{{}}: On{{}}

def wx(w: Wrap) -> Flag:
  match w:
    case W{{b, g}}: bx(b)

def mkbox(s: Sel) -> Box:
  match s:
    case S0{{}}: B{{Off{{}}}}
    case S1{{}}: B{{On{{}}}}
    case S2{{}}: E{{}}

def mkwrap(s: Sel) -> Wrap:
  W{{mkbox(s), On{{}}}}

def mkflag(s: Sel) -> Flag:
  match s:
    case S0{{}}: Off{{}}
    case S1{{}}: On{{}}
    case S2{{}}: Off{{}}
'''

class G:
    def __init__(self, r, kinds):
        self.r = r; self.kinds = kinds; self.n = 0
    def fresh(self, p='v'):
        self.n += 1; return f'{p}{self.n}'
    def data(self, t):
        return t == 'Flag' or self.kinds[t] == 'Data'
    # expression of type Flag using names from env: list of (name, type, erased)
    def expr(self, env, depth=2):
        r = self.r
        live = [(n, t) for n, t, e in env if not e]
        allv = [(n, t) for n, t, e in env]
        k = r.random()
        if depth == 0 or k < 0.15:
            flags = [n for n, t in live if t == 'Flag']
            if flags and r.random() < 0.8: return r.choice(flags)
            return r.choice(['On{}', 'Off{}'])
        if k < 0.30:
            boxes = [n for n, t in live if t == 'Box']
            if boxes: return f'bx({r.choice(boxes)})'
        if k < 0.38:
            ws = [n for n, t in live if t == 'Wrap']
            if ws: return f'wx({r.choice(ws)})'
        if k < 0.50 and allv:
            n, t = r.choice(allv)
            if t == 'Flag': return f'keep({self.expr(env, depth-1)}, {n})'
            if t == 'Box': return f'bkeep({self.expr(env, depth-1)}, {n})'
        return f'both({self.expr(env, depth-1)}, {self.expr(env, depth-1)})'
    def pattern(self, t, binds, depth, varonly=False):
        r = self.r; k = r.random()
        if k < 0.15: return '_'
        if k < 0.35 or depth == 0 or varonly:
            v = self.fresh(); q = r.choice(['', '+', '+'])
            binds.append((v, t, False)); return q + v
        if t == 'Flag': return r.choice(['On{}', 'Off{}'])
        if t == 'Box':
            if r.random() < 0.3: return 'E{}'
            return 'B{' + self.pattern('Flag', binds, depth-1) + '}'
        if t == 'Wrap':
            b = self.pattern('Box', binds, depth-1)
            gb = []
            g = self.pattern('Flag', gb, 0) if r.random() < 0.5 else '_'
            for n, tt, e in gb: binds.append((n, tt, True))
            return 'W{' + b + ', ' + g + '}'
    def match(self, env, scruts, depth, ind, letlike=()):
        r = self.r
        lines = [ind + 'match ' + ' '.join(n for n, t in scruts) + ':']
        nrows = r.choice([1, 2, 2, 3])
        for i in range(nrows):
            binds = []
            pats = [self.pattern(t, binds, 2, n in letlike and r.random() < 0.85) for n, t in scruts]
            if i == nrows - 1 and r.random() < (0.7 if depth > 0 else 0.35):
                binds = []
                pats = []
                for n, t in scruts:
                    k = r.random()
                    if k < 0.5: pats.append('_')
                    else:
                        v = self.fresh(); q = r.choice(['', '+'])
                        binds.append((v, t, False)); pats.append(q + v)
            env2 = env + binds
            cand = [(n, t) for n, t, e in binds if not e and t != 'Flag']
            if depth > 0 and cand and r.random() < 0.65:
                s = r.choice(cand)
                lines.append(ind + '  case ' + ' '.join(pats) + ':')
                ll = set(letlike)
                # a row alias of a let-like column is let-like
                for (sn, st), pt in zip(scruts, pats):
                    if sn in letlike and pt.lstrip('+') == s[0]: ll.add(s[0])
                lines += self.match(env2, [s], depth - 1, ind + '    ', tuple(ll))
            else:
                lines.append(ind + '  case ' + ' '.join(pats) + ': ' + self.expr(env2))
        return lines

def gen(seed):
    r = random.Random(seed)
    kb = r.choice(['Type', 'Type', 'Data'])
    kw = 'Type' if kb == 'Type' else r.choice(['Type', 'Data'])
    g = G(r, {'Box': kb, 'Wrap': kw})
    ptypes = [r.choice(['Flag', 'Box', 'Wrap']) for _ in range(r.choice([1, 2, 2, 3]))]
    params = []
    env = []
    for i, t in enumerate(ptypes):
        q = r.choice(['', '', '+', '-'])
        n = f'p{i}'
        params.append((q, n, t))
        env.append((n, t, q == '-'))
    body = []
    nlets = r.choice([0, 0, 0, 0, 1])
    lets = []
    for i in range(nlets):
        t = r.choice(['Flag', 'Box', 'Box', 'Wrap'])
        q = r.choice(['', '', '+', '-'])
        names = [n for n, tt, e in env if tt == t and not e]
        if t == 'Flag':
            src = r.choice(names + ['On{}', g.expr(env, 1)]) if names else r.choice(['On{}', g.expr(env, 1)])
        elif t == 'Box':
            src = r.choice(names + ['B{On{}}', 'E{}']) if names else r.choice(['B{On{}}', 'E{}'])
        else:
            src = r.choice(names + ['W{E{}, On{}}']) if names else 'W{E{}, On{}}'
        ann = f' : {t}' if src.endswith('}') or r.random() < 0.3 else ''
        n = f'k{i}'
        body.append(f'  {q}{n}{ann} = {src}')
        env.append((n, t, q == '-'))
        lets.append((n, t))
    # scrutinees
    cands = [(n, t) for q, n, t in params if q != '-' or r.random() < 0.1]
    if not cands: cands = [(params[0][1], params[0][2])]
    if lets and r.random() < 0.85:
        scruts = [lets[-1]]
    else:
        ncols = 1 if len(cands) == 1 else r.choice([1, 1, 2])
        scruts = r.sample(cands, min(ncols, len(cands)))
    body += g.match(env, scruts, 1, '  ', tuple(n for n, t in lets))
    src = header(kb, kw)
    src += '\ndef f(' + ', '.join(f'{q}{n}: {t}' for q, n, t in params) + ') -> Flag:\n' + '\n'.join(body) + '\n'
    # probe wrapper: enum args for live params
    args, pargs = [], []
    for q, n, t in params:
        a = 's' + n
        pargs.append(f'{a}: Sel')
        args.append({'Flag': f'mkflag({a})', 'Box': f'mkbox({a})', 'Wrap': f'mkwrap({a})'}[t])
    src += '\ndef probe(' + ', '.join(pargs) + ') -> Flag:\n  f(' + ', '.join(args) + ')\n'
    return src


def promotes_type(source):
    return 'type Wrap is Type:' in source and PROMOTED.search(source) is not None


def compare(seed, path, check, evaluate):
    source = gen(seed)
    path.write_text(source)
    reference = fuzz.classify(gate.run([*gate.SEED, path], timeout=240), seed=True)
    actual = fuzz.classify(gate.run([*check, path]))
    record = {'seed': seed, 'sha256': hashlib.sha256(source.encode()).hexdigest(),
              'promotes_type': promotes_type(source), 'reference': reference, 'knot': actual}
    if reference == 'Invalid' and actual == 'Accepted':
        record['failure'] = 'seed rejects, Knot accepts'
    elif reference == 'Accepted' and actual == 'Invalid':
        record['failure'] = 'D4: seed accepts, Knot reports Invalid'
    enums, entries, ids = oracle.boundary(source)
    if reference == actual == 'Accepted' and evaluate and record['promotes_type'] and 'probe' in entries:
        tuples = list(itertools.product(*(enums[t] for t in entries['probe']['parameters'])))
        arguments = random.Random(seed).choice(tuples)
        fixture = {'name': path.stem, 'file': str(path.relative_to(gate.ROOT))}
        wpath, text, call, prefix = oracle.wrapper(fixture, 'probe', list(arguments), 'Flag')
        (gate.ROOT / wpath).parent.mkdir(parents=True, exist_ok=True)
        (gate.ROOT / wpath).write_text(text)
        observed = gate.run([*gate.SEED, gate.ROOT / wpath], timeout=240)
        name = oracle.decode(observed['stdout'], prefix, enums['Flag'])
        gate.require(observed['exit'] == 0 and not observed['stderr'] and name is not None, observed)
        ordinals = [enums['Sel'].index(a) for a in arguments]
        value = gate.run([*evaluate, path, 'probe', 65536, *ordinals])
        gate.evaluated(value, {'type_id': ids['Flag'], 'tag': enums['Flag'].index(name), 'result': name})
        record['call'] = {'ordinals': ordinals, 'result': name}
    return record


def check(check, directory, evaluate=None):
    """Classify every program with `check`; evaluate one call of each agreed promoted acceptance."""
    directory.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(lambda s: compare(s, directory / f'a{s:05d}.bend', check, evaluate), SEEDS))
    failures = [r for r in records if 'failure' in r]
    summary = {'seeds': [SEEDS.start, SEEDS.stop - 1], 'programs': len(records),
               'generator_sha256': gate.digest(Path(__file__)),
               'promotes_type': sum(r['promotes_type'] for r in records),
               'seed_outcomes': dict(Counter(r['reference'] for r in records)),
               'knot_outcomes': dict(Counter(r['knot'] for r in records)),
               'promoted_outcomes': dict(Counter(f"{r['reference']}/{r['knot']}" for r in records if r['promotes_type'])),
               'false_acceptances': sum(r.get('failure') == 'seed rejects, Knot accepts' for r in records),
               'false_invalid': sum(r.get('failure', '').startswith('D4:') for r in records),
               'evaluator_values': sum('call' in r for r in records),
               'failures': [{'seed': r['seed'], 'failure': r['failure']} for r in failures],
               'observations_sha256': hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()}
    (directory / 'observations.json').write_text(json.dumps(records, indent=2) + '\n')
    (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


def main():
    args = argparse.ArgumentParser(description='Classify the Type-kind promotion programs with one checker binary.')
    args.add_argument('checker')
    args.add_argument('directory')
    options = args.parse_args()
    summary = check([Path(options.checker).resolve()], Path(options.directory).resolve())
    print(json.dumps({k: v for k, v in summary.items() if k != 'failures'}, sort_keys=True))
    print(' '.join(f"a{f['seed']:05d}" for f in summary['failures']))


if __name__ == '__main__':
    main()
