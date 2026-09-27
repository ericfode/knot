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
DUELS = [('bitpath', 'mythic', 'deadpan'), ('bitpath', 'algebra', 'baroque'),
         ('fuel', 'mythic', 'baroque'), ('fuel', 'golf', 'literate'),
         ('pipeline', 'mythic', 'algebra'), ('pipeline', 'deadpan', 'literate'),
         ('slots', 'algebra', 'golf'), ('slots', 'baroque', 'literate')]
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
        left, right = (a, b) if rng.random() < .5 else (b, a)
        duels.append({'id': f'd{n}', 'task': task, 'left': vid(task, left), 'right': vid(task, right)})
    first = duels[0]
    duels.append({'id': f'd{len(duels) + 1}', 'task': first['task'], 'left': first['right'], 'right': first['left'], 'repeat_of': first['id']})
    reveal = {i: LABEL[m['pole']] for i, m in mapping.items()}
    data = {'tasks': tasks, 'variants': variants, 'duels': duels, 'reveal': reveal}
    template = (HERE / 'template.html').read_text()
    assert template.count('/*DATA*/null') == 1
    payload = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    Path(out_path).write_text(template.replace('/*DATA*/null', payload))
    Path(mapping_path).write_text(json.dumps({'salt': SALT, 'mapping': mapping, 'duels': duels,
        'task_order': {t['id']: t['order'] for t in tasks}}, indent=1) + '\n')
    print(f'{len(variants)} variants, {len(duels)} duels -> {out_path}')

if __name__ == '__main__':
    main(*sys.argv[1:])
