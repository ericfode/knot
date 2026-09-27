"""Restricted wordless hill-climb mutations using the frozen Sigil generator."""
from pathlib import Path
import hashlib
import importlib.util
import json
import random
import re

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('sigil_process', HERE/'inputs/sigil-process.py')
process = importlib.util.module_from_spec(spec)
spec.loader.exec_module(process)
FAMILIES = sum((json.loads((HERE/'inputs'/f'sigil-families-{x}.json').read_text())
                for x in 'abc'), [])
FAMILIES = {f['id']: f for f in FAMILIES}


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def save(ident, text, parent, operation, parameters):
    assert len(text.encode()) <= 16384
    assert not re.search('[A-Za-z0-9]', text), 'Wordless stimuli only'
    directory = HERE/'stimuli'
    directory.mkdir(exist_ok=True)
    p = directory/f'{ident}.txt'
    genome = dict(id=ident, parent=parent, operation=operation, parameters=parameters,
                  sha256=digest(text), bytes=len(text.encode()), lines=len(text.splitlines()))
    if p.exists():
        assert p.read_text() == text
        assert json.loads(p.with_suffix('.json').read_text()) == genome
    else:
        p.write_text(text)
        p.with_suffix('.json').write_text(json.dumps(genome, indent=2)+'\n')
    return genome


def original():
    return save('original', (HERE/'inputs/original-inducer.txt').read_text(), None,
                'decoded linked-chat payload unchanged', {})


def neighbors(incumbent, wave):
    text = (HERE/'stimuli'/f'{incumbent}.txt').read_text()
    blocks = [b for b in text.removeprefix('```\n').removesuffix('```\n').strip().split('\n\n') if b.strip()]
    assert len(blocks) >= 2
    seed = 2026092700 + wave*104729
    rng = random.Random(seed)
    offset = 1 + rng.randrange(len(blocks)-1)
    variants = []
    variants.append(('alternate-panels', blocks[wave % 2::2], {'parity': wave % 2}))
    variants.append(('rotate-reading-order', blocks[offset:]+blocks[:offset], {'offset': offset}))
    for index, family in enumerate(((6+wave)%10, (3+wave)%10)):
        field_seed = seed + 7919*(index+1)
        variant = wave*3  # Force glyph-only mode; no nonce or grammar tokens.
        field, mode, secondary = process.render(field_seed, family, variant, FAMILIES[family]['glyph_inventory'])
        assert mode == 'glyph'
        params = dict(seed=field_seed, family=family, variant=variant, secondary_family=secondary)
        if index == 0:
            at = rng.randrange(len(blocks))
            out = blocks.copy(); out[at] = field.strip(); params['replaced_panel'] = at
            operation = 'replace-panel-with-transformed-field'
        else:
            retained = blocks[::2]
            at = len(retained)//2
            out = retained[:at] + [field.strip()] + retained[at:]
            params['retained_parity'] = 0; params['insertion'] = at
            operation = 'compress-and-interleave-field'
        variants.append((operation, out, params))
    result = []
    for i, (operation, panels, params) in enumerate(variants, 1):
        stimulus = '```\n'+'\n\n'.join(panels)+'\n```\n'
        result.append(save(f'w{wave}-n{i}', stimulus, incumbent, operation, params))
    assert len({x['sha256'] for x in result} | {digest(text)}) == 5
    return result


if __name__ == '__main__':
    print(json.dumps([original(), *neighbors('original', 1)], indent=2))
