#!/usr/bin/env python3
"""Agreement between the judge (production style reports) and the user's taste anchors.

Usage: analyze.py RUN_DIR [--json OUT.json]
Per rendering: declaration-mean and composition values per axis, as the
normalized expected score E[level]/(levels-1) and as P(level >= 3).
Judge overall = mean of five axes: compression and delight (declaration mean),
memetic, anticipation and payoff (composition). A pair agrees when the
human-preferred rendering has the higher overall; |diff| < TIE counts half.
Dev tasks: bitpath, fuel. Held-out: pipeline, slots.
"""
import glob, json, os, sys
from itertools import combinations

EVID = '/Users/ericfode/src/knot/.claude/worktrees/perch-style-framework-c2cdfc/docs/perch-calibration/taste-duel-2026-09-27'
AXES = ['maximally_big_brain', 'delightful_to_read', 'highly_memetic', 'anticipation', 'payoff']
SHORT = {'maximally_big_brain': 'brain', 'delightful_to_read': 'delight', 'highly_memetic': 'memetic', 'anticipation': 'antic', 'payoff': 'payoff'}
DEV, HELD = {'bitpath', 'fuel'}, {'pipeline', 'slots'}
TIE = 0.01
RANK = {'more': 2, 'meh': 1, 'much': 0}

def norm(ans):
    p = {int(k): v for k, v in ans['probabilities'].items()}
    n = max(p) ; tot = sum(p.values())
    return sum(k * v for k, v in p.items()) / tot / n, sum(v for k, v in p.items() if k >= 3) / tot

def rendering(path):
    r = json.load(open(path)); rep = r['report']
    if rep.get('failure'): return None
    rows = rep['rows']; out = {'task': r['task'], 'variant': r['variant'], 'decls': len(rows)}
    for axis in AXES:
        vals = [norm(row['answers'][axis]) for row in rows if axis in row['answers']]
        out[f'decl_{SHORT[axis]}'] = sum(v[0] for v in vals) / len(vals) if vals else None
        out[f'decl_{SHORT[axis]}_p3'] = sum(v[1] for v in vals) / len(vals) if vals else None
    comp = ((rep.get('composition') or {}).get('review') or {}).get('row')
    for axis in ['highly_memetic', 'anticipation', 'payoff']:
        if comp and axis in comp['answers']:
            e, p3 = norm(comp['answers'][axis]); out[f'comp_{SHORT[axis]}'] = e; out[f'comp_{SHORT[axis]}_p3'] = p3
        else:
            out[f'comp_{SHORT[axis]}'] = out[f'comp_{SHORT[axis]}_p3'] = None
    parts = [out['decl_brain'], out['decl_delight'], out['comp_memetic'], out['comp_antic'], out['comp_payoff']]
    out['overall'] = sum(parts) / len(parts) if all(x is not None for x in parts) else None
    q = rep.get('qualification') or {}
    out['qualified'] = q.get('fully_qualified'); out['requests'] = rep.get('provider_requests')
    out['comp_status'] = (rep.get('composition') or {}).get('assessment', {}).get('status')
    return out

def anchors():
    pairs = []
    r1 = json.load(open(f'{EVID}/round1-responses.json'))
    for task, cards in r1['lineups'].items():
        rated = [(p, RANK[c['reaction']]) for p, c in cards.items() if c['reaction']]
        for (a, ra), (b, rb) in combinations(rated, 2):
            if ra != rb:
                pairs.append({'task': task, 'win': a if ra > rb else b, 'lose': b if ra > rb else a, 'weight': abs(ra - rb), 'source': 'lineup'})
    for rnd in ('round1-responses.json', 'round2-responses.json'):
        for d in json.load(open(f'{EVID}/{rnd}'))['duels']:
            if d['preferred']:
                lose = d['right'] if d['preferred'] == d['left'] else d['left']
                pairs.append({'task': d['task'], 'win': d['preferred'], 'lose': lose, 'weight': d['strength'], 'source': d['id']})
    return pairs

def agree(pairs, R, key):
    got = tot = 0; detail = []
    for p in pairs:
        a, b = R.get((p['task'], p['win'])), R.get((p['task'], p['lose']))
        if not a or not b or a.get(key) is None or b.get(key) is None: continue
        d = a[key] - b[key]; s = 1 if d > TIE else 0.5 if abs(d) <= TIE else 0
        got += s; tot += 1; detail.append((p, round(d, 3), s))
    return got, tot, detail

def main(run_dir, *opts):
    R = {}
    for f in glob.glob(os.path.join(run_dir, '*.json')):
        x = rendering(f)
        if x: R[(x['task'], x['variant'])] = x
    pairs = anchors()
    print(f'renderings scored: {len(R)}; human preference pairs: {len(pairs)}')
    print(f"{'task/variant':30} {'brain':>6} {'delig':>6} {'memet':>6} {'antic':>6} {'payof':>6} | {'overall':>7} comp p3 M/A/P")
    for (t, v), x in sorted(R.items()):
        fmt = lambda k: f"{x[k]:6.2f}" if x[k] is not None else '   n/a'
        p3 = '/'.join(f"{x[k]:.2f}" if x[k] is not None else 'na' for k in ['comp_memetic_p3', 'comp_antic_p3', 'comp_payoff_p3'])
        print(f"{t+'/'+v:30} {fmt('decl_brain')} {fmt('decl_delight')} {fmt('comp_memetic')} {fmt('comp_antic')} {fmt('comp_payoff')} | {fmt('overall'):>7} {p3}")
    summary = {}
    for name, tasks in [('dev', DEV), ('held-out', HELD), ('all', DEV | HELD)]:
        sub = [p for p in pairs if p['task'] in tasks]
        line = []
        for key in ['overall', 'decl_brain', 'decl_delight', 'comp_memetic', 'comp_antic', 'comp_payoff', 'decl_memetic']:
            g, n, _ = agree(sub, R, key); line.append(f"{key}={g}/{n}" + (f" ({100*g/n:.0f}%)" if n else ''))
            summary.setdefault(name, {})[key] = [g, n]
        duels = [p for p in sub if p['source'] != 'lineup']
        g, n, det = agree(duels, R, 'overall'); summary[name]['duels_overall'] = [g, n]
        print(f"\n[{name}] " + '  '.join(line))
        print(f"[{name}] duels only, overall: {g}/{n}" + (f" ({100*g/n:.0f}%)" if n else ''))
        for p, d, s in det:
            if s < 1: print(f"   MISS {p['source']:4} {p['task']:9} wanted {p['win']:18} > {p['lose']:18} judge diff {d:+.3f}")
    if '--json' in opts:
        json.dump({'renderings': {f'{t}/{v}': x for (t, v), x in R.items()}, 'summary': summary}, open(opts[opts.index('--json') + 1], 'w'), indent=1)

if __name__ == '__main__':
    main(*sys.argv[1:])
