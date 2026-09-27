#!/usr/bin/env python3
"""Build the taste-duel page from verified variant files.

Usage: build.py SUMMARIES.json OUT.html MAPPING.json
SUMMARIES.json: {task_id: {"title": str, "contract": str}} plus the verified
variant files at variants/<task>/<pole>.bend. Only the part above the harness
marker is shown. Ids are opaque; the id -> pole mapping goes to MAPPING.json.
"""
import hashlib, json, random, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# In the repository the task folders sit beside this script as .bend.snapshot
# files (kept out of style discovery so they stay held-out controls).
VARIANTS = HERE if (HERE / 'bitpath').is_dir() else HERE.parent / 'variants'
SUFFIX = '.bend.snapshot' if (HERE / 'bitpath').is_dir() else '.bend'
MARKER = '# ---- harness (not shown) ----'
POLES = ['deadpan', 'algebra', 'mythic', 'baroque', 'golf', 'literate']
LABEL = {'deadpan': 'Deadpan: maximally plain', 'algebra': 'Algebra: one idea absorbs every case',
         'mythic': 'Mythic: invented vocabulary and rhythm', 'baroque': 'Baroque: deliberate ornament and ceremony',
         'golf': 'Golf: compressed to cryptic', 'literate': 'Literate: a narrated story'}
TASK_ORDER = ['bitpath', 'fuel', 'pipeline', 'slots']
# Round 2 (after the user's lineups): single-factor ablations of the renderings
# they preferred, interleaved so neighbouring duels differ in task and factor.
DUELS = [('bitpath', 'algebra', 'algebra-nolaws'), ('fuel', 'algebra', 'algebra-mythic'),
         ('pipeline', 'algebra', 'literate'), ('slots', 'algebra', 'algebra-nolaws'),
         ('bitpath', 'algebra', 'algebra-longnames'), ('fuel', 'algebra', 'algebra-noproof'),
         ('pipeline', 'literate', 'literate-nopuzzle'), ('slots', 'algebra', 'algebra-words'),
         ('bitpath', 'algebra', 'algebra-riddle'), ('fuel', 'algebra', 'algebra-dense'),
         ('pipeline', 'literate', 'literate-lite')]
REPEAT = 1  # index of the duel repeated last with sides swapped (fuel identity)
ABLATION_LABELS = json.loads((HERE / 'ablation-labels.json').read_text()) if (HERE / 'ablation-labels.json').exists() else {}
SALT = 'knot-taste-duel-2026-09-27'

def vid(task, pole):
    return 'v' + hashlib.sha256(f'{SALT}:{task}:{pole}'.encode()).hexdigest()[:8]

def shown(path):
    text = path.read_text()
    if MARKER not in text:
        raise SystemExit(f'missing harness marker: {path}')
    return text.split(MARKER, 1)[0].rstrip() + '\n'

def main(summaries_path, out_path, mapping_path):
    summaries = json.loads(Path(summaries_path).read_text())
    rng = random.Random(SALT)
    variants, tasks, mapping = {}, [], {}
    for task in TASK_ORDER:
        order = []
        for pole in POLES:
            code = shown(VARIANTS / task / f'{pole}{SUFFIX}')
            i = vid(task, pole)
            variants[i] = {'code': code, 'lines': code.count('\n')}
            mapping[i] = {'task': task, 'pole': pole}
            order.append(i)
        rng.shuffle(order)
        tasks.append({'id': task, 'title': summaries[task]['title'], 'contract': summaries[task]['contract'], 'order': order})
    duels = []
    for n, (task, a, b) in enumerate(DUELS, 1):
        # Alternate which side holds the base (first of the pair) to avoid position bias.
        left, right = (a, b) if n % 2 == 1 else (b, a)
        for pole in (left, right):
            i = vid(task, pole)
            if i not in variants:
                sub = 'ablations/' if pole not in POLES else ''
                code = shown(VARIANTS / task / f'{sub}{pole}{SUFFIX}')
                variants[i] = {'code': code, 'lines': code.count('\n')}
                mapping[i] = {'task': task, 'pole': pole}
        duels.append({'id': f'e{n}', 'task': task, 'left': vid(task, left), 'right': vid(task, right)})
    rep = duels[REPEAT]
    duels.append({'id': f'e{len(duels) + 1}', 'task': rep['task'], 'left': rep['right'], 'right': rep['left'], 'repeat_of': rep['id']})
    reveal = {i: LABEL.get(m['pole']) or ABLATION_LABELS[f"{m['task']}/{m['pole']}"] for i, m in mapping.items()}
    data = {'round': 2, 'tasks': tasks, 'variants': variants, 'duels': duels, 'reveal': reveal}
    template = (HERE / 'template.html').read_text()
    assert template.count('/*DATA*/null') == 1
    payload = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    Path(out_path).write_text(template.replace('/*DATA*/null', payload))
    Path(mapping_path).write_text(json.dumps({'salt': SALT, 'mapping': mapping, 'duels': duels,
        'task_order': {t['id']: t['order'] for t in tasks}}, indent=1) + '\n')
    print(f'{len(variants)} variants, {len(duels)} duels -> {out_path}')

if __name__ == '__main__':
    main(*sys.argv[1:])
