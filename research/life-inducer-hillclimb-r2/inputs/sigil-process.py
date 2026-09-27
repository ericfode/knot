"""Deterministic creative-stimulus generator; no Phi evaluator is implemented."""
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent
SEED = 2026091901


def rotate(xs, n):
    n %= len(xs)
    return xs[n:] + xs[:n]


def transform(g, family, step, salt, alphabet):
    """Ten bounded inscription transformations on a toroidal 7x9 field."""
    h, w = len(g), len(g[0])
    if family == 0:  # Crossing rows exchange their neighbors.
        return [[g[(r+c+step)%h][(c+(-1 if r%2 else 1)*step)%w]
                 for c in range(w)] for r in range(h)]
    if family == 1:  # Concentric shells rotate with unequal periods.
        out = [row[:] for row in g]
        for d in range(min(h,w)//2+1):
            cells = [(r,c) for r in range(d,h-d) for c in range(d,w-d)
                     if r in (d,h-d-1) or c in (d,w-d-1)]
            vals = rotate([g[r][c] for r,c in cells], (d+1)*step)
            for (r,c),v in zip(cells,vals): out[r][c] = v
        return out
    if family == 2:  # Three countercurrents braid without stable lane identities.
        rows = [rotate(row, step if r%3==0 else -step*(r%3))
                for r,row in enumerate(g)]
        return [rows[(r+step)%h] for r in range(h)]
    if family == 3:  # Residue selects the next coordinate; traversal rewrites order.
        src = sum(g,[]); available = list(range(len(src))); out = []
        at = salt % len(src)
        while available:
            at %= len(available)
            value = src[available.pop(at)]; out.append(value)
            at += value + step + 2
        return [out[r*w:(r+1)*w] for r in range(h)]
    if family == 4:  # Voids spread; displaced marks reappear across the seam.
        out = [row[:] for row in g]
        for r in range(h):
            for c in range(w):
                if (r+2*c+step+salt)%5==0:
                    out[(r+step)%h][(c+step+1)%w] = g[r][c]
                    out[r][c] = -1
        return out
    if family == 5:  # A moving cut changes membership in each side's rotation.
        out = []
        for r,row in enumerate(g):
            b = 1+(salt+step*(r+1))%(w-1)
            a,z = row[:b],row[b:]
            out.append(rotate(z,-step)+rotate(a,step))
        return out
    if family == 6:  # Every site is reinterpreted by simultaneous other-row reads.
        return [[g[(r+(1 if (r+c+step)%2 else -1))%h][(c+r+step)%w]
                 for c in range(w)] for r in range(h)]
    if family == 7:  # Crossing strands share a mark, then branch with inherited residue.
        out = [rotate(row,step*(1 if r%2 else -1)) for r,row in enumerate(g)]
        for r in range(h):
            c = (r*step+salt)%w
            out[r][c] = g[(r+step)%h][c]
            out[(r+1)%h][(c+1)%w] = out[r][c]
        return out
    if family == 8:  # Fold coordinates into aliases, then unfold through another axis.
        return [[g[(c+step)%h][(abs(r-h//2)*2+c+salt)%w]
                 for c in range(w)] for r in range(h)]
    if family == 9:  # A phase changes which repeated marks share an identity.
        return [[-1 if v<0 else (v+(r+c+step)%3)%alphabet
                 for c,v in enumerate(rotate(row,(r+step)%w))]
                for r,row in enumerate(rotate(g,step))]
    raise ValueError(family)


def display(g, tokens, rotation=0):
    rows = g
    for _ in range(rotation%4): rows = [list(x) for x in zip(*rows[::-1])]
    width = max(map(len,tokens))
    return [' '.join((' '*width if v<0 else tokens[v].ljust(width)) for v in row).rstrip()
            for row in rows]


def render(seed, family, variant, inventory):
    rng = random.Random(seed)
    glyphs = list(dict.fromkeys(inventory.split()))
    rng.shuffle(glyphs); glyphs = glyphs[:7]
    mode = ['glyph','nonce','grammar'][variant%3]
    if mode=='nonce':
        stems = ['ɬa','ŋe','ʑu','øɣ','ǂi','ʘa','ɲə']
        tokens = [g+stems[i] for i,g in enumerate(glyphs)]
    elif mode=='grammar':
        stems = ['if','as','of','yet','which','until','here']
        rng.shuffle(stems)
        tokens = [g+stems[i] for i,g in enumerate(glyphs)]
    else: tokens = glyphs
    g = [[(r*2+c+rng.randrange(3))%len(tokens) for c in range(9)] for r in range(7)]
    states = [g]
    secondary = (family+1+variant)%10
    for step in range(1,7):
        g = transform(g, family if step%2 else secondary, step, seed%97, len(tokens))
        if step in [2,4,6]: states.append(g)
    # Related views are placed in a square, not a numbered sequence.
    order = [0,3,2,1]; rng.shuffle(order)
    panes = [display(states[i],tokens,(variant+i)%4) for i in order]
    columns = max(max(map(len,p),default=0) for p in panes)+5
    height = max(map(len,panes))
    lines=[]
    for a,b in [(0,1),(2,3)]:
        for row in range(height):
            left=panes[a][row] if row<len(panes[a]) else ''
            right=panes[b][row] if row<len(panes[b]) else ''
            lines.append(left.ljust(columns)+right)
        lines.append(' '*max(0,columns//2)+'⋰   ◌   ⋱')
    # Reprise comes from the transformed field, not an unrelated flourish.
    lines += ['', ' '.join(tokens[v] for v in states[-1][variant%7] if v>=0)]
    return '\n'.join(line.rstrip() for line in lines)+'\n', mode, secondary


def build():
    families = sum([json.loads(p.read_text()) for p in sorted(ROOT.glob('families-*.json'))],[])
    assert sorted(f['id'] for f in families)==list(range(10))
    (ROOT/'stimuli').mkdir(exist_ok=True)
    (ROOT/'prompts').mkdir(exist_ok=True)
    brief=(ROOT/'BRIEF.md').read_text()
    manifest=[]
    for f in sorted(families,key=lambda f:f['id']):
        for v in range(10):
            n=f['id']*10+v+1; ident=f'I{n:03}'; seed=SEED+n*104729
            text,mode,secondary=render(seed,f['id'],v,f['glyph_inventory'])
            prompt=brief+'\n--- INSCRIPTION ---\n\n'+text+'\n--- DESIGN QUESTION ---\nHow should this language work? Give the paragraph and code specimen.\n'
            (ROOT/'stimuli'/f'{ident}.txt').write_text(text)
            (ROOT/'prompts'/f'{ident}.txt').write_text(prompt)
            manifest.append({'id':ident,'family':f['id'],'family_name':f['name'],
                'variant':v,'secondary_family':secondary,'lexical_mode':mode,'seed':seed,
                'stimulus_sha256':hashlib.sha256(text.encode()).hexdigest(),
                'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()})
    assert len({m['stimulus_sha256'] for m in manifest})==100
    (ROOT/'manifest.json').write_text(json.dumps({'version':'phi-inducers/v1','seed':SEED,
        'process_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'family_source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted(ROOT.glob('families-*.json'))},
        'brief_sha256':hashlib.sha256(brief.encode()).hexdigest(),'trials':manifest},indent=2)+'\n')
    print('100 unique deterministic inducers and complete prompts generated.')


if __name__=='__main__': build()
