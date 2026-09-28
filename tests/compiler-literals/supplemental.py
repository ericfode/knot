"""Verify the supplemental seed freeze; --write is used before implementation only."""
import json
import re
import sys
from pathlib import Path
import regen as oracle

HERE, ROOT = oracle.HERE, oracle.ROOT
DEST = HERE / 'supplemental.json'
SOURCE = HERE / 'supplemental/bootstrap-helpers.bend'

def build():
    path = str(SOURCE.relative_to(ROOT))
    source = SOURCE.read_text()
    kinds = oracle.enums(source)
    calls = []
    directory = ROOT / '.local/literals'
    directory.mkdir(parents=True, exist_ok=True)
    for constructor in kinds['Probe']:
        prefix = '../../tests/compiler-literals/supplemental/bootstrap-helpers.'
        wrapper = directory / f'probe-{constructor}.bend'
        text = f'import {prefix}bend as F\n\ndef main() -> F.Answer:\n  F.observe(F.{constructor}{{}})\n'
        wrapper.write_text(text)
        result = oracle.seed([str(wrapper.relative_to(ROOT))])
        value = re.fullmatch(re.escape(prefix) + r'(No|Yes)\{\}\n', result['stdout'])
        assert result['exit'] == 0 and result['stderr'] == '' and value, result
        calls.append({'export': 'observe', 'arguments': [kinds['Probe'].index(constructor)],
                      'argument_constructors': [constructor], 'type': 'Answer',
                      'constructor': value.group(1), 'tag': kinds['Answer'].index(value.group(1)),
                      'wrapper': {'path': str(wrapper.relative_to(ROOT)), 'source': text}, 'seed': result})
    checked = oracle.seed([path, '--check-only'])
    assert checked['exit'] == 0 and checked['stdout'] == 'All terms check.\n', checked
    return {'purpose': 'D7 freeze before implementing reusable Nat offset patterns, Nat.is_le, U32.and, String.reverse.',
            'seed_sha256': {f: oracle.sha256(ROOT / oracle.SEED_DIR / f) for f in oracle.SEED_FILES},
            'fixtures': [{'name': 'bootstrap-helpers', 'file': path, 'sha256': oracle.sha256(SOURCE),
                          'enums': kinds, 'seed_check': checked, 'calls': calls, 'knot': oracle.AGREE}]}

def main():
    data = json.dumps(build(), indent=2) + '\n'
    if sys.argv[1:] == ['--write']:
        assert data == json.dumps(build(), indent=2) + '\n'
        DEST.write_text(data)
    else:
        assert not sys.argv[1:]
        assert DEST.read_text() == data, 'supplemental seed observations changed'
    print('supplemental literals match the seed: 1 fixture, 12 calls')

if __name__ == '__main__':
    main()
