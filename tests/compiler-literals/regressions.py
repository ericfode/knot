"""Freeze or verify the review-round-1 regression books against the pinned seed.

    python3 tests/compiler-literals/regressions.py          # verify (default)
    python3 tests/compiler-literals/regressions.py --write  # before implementation only

Each book reproduces a confirmed review finding or a seed-accepted control for
it. Expectations come only from the seed and the reviewed literals in PLAN;
nothing here runs or reads Knot. The 40-book freeze and the supplemental freeze
are unchanged.
"""
import json
import re
import sys
from itertools import product
import regen as oracle

HERE, ROOT = oracle.HERE, oracle.ROOT
FIXTURES = HERE / 'regressions'
DEST = HERE / 'regressions.json'
CALLS = ROOT / '.local/compiler-literals/regression-calls'

SPACED = oracle.unsupported(
    'parse', 'operator',
    'Seed-invalid: a Nat offset needs `+` adjacent to its literal, so a separated `+` is '
    'operator sugar, which Knot does not check; D4 forbids an Invalid claim.')
U32_CONSTRUCTOR = oracle.unsupported(
    'check', 'u32-constructor',
    "Seed-valid: Base spells U32{data: Word(32n)}, but an installed U32 is unboxed bits "
    'with no Word representation in Knot (D4).')
WORD = oracle.unsupported(
    'load', 'base-function-result',
    'Seed-valid: Word.zero returns the type-level Word(32n), which the Base loader does not '
    'lower, so the U32 construction is never reached (D4).')

# name -> (finding, covers, entries, Knot)
PLAN = {
    'offset-spaced-pattern': ('offset adjacency', 'case 1n + p', [], SPACED),
    'offset-spaced-promotion-pattern': ('offset adjacency', 'case 1n +p', [], SPACED),
    'offset-spaced-expression': ('offset adjacency', 'the expression 3n + x', [], SPACED),
    'offset-spaced-promotion-expression': ('offset adjacency', 'the expression 3n +x', [], SPACED),
    'offset-adjacent': ('offset adjacency control', '1n+ p, 1n+ +p, 1n++p and 3n+ x remain offsets',
                        ['after_space', 'after_promotion', 'after_join', 'sum'], oracle.AGREE),
    'u32-constructor-pattern': ('u32 constructor', 'case U32{w} on a U32 scrutinee', [], U32_CONSTRUCTOR),
    'u32-constructor-rebuild': ('u32 constructor', 'case U32{w}: U32{w}', [], U32_CONSTRUCTOR),
    'u32-constructor-word': ('u32 constructor', 'U32{Word.zero(32n)} without a pattern', [], WORD),
    'string-long-primitives': ('long strings', 'String.length, append (both sides) and eq at 39999-40001 Chars',
                               ['length', 'append_left', 'append_right', 'equal'], oracle.AGREE),
}


def call(name, fn, args, kinds, sigs):
    params, out = sigs[fn]
    assert out in kinds and all(t in kinds for t in params), (name, fn)
    record = {'export': fn, 'arguments': [kinds[t].index(a) for t, a in zip(params, args)],
              'argument_constructors': list(args), 'type': out}
    if fn == 'main':
        prefix, observed = '', oracle.seed([f'tests/compiler-literals/regressions/{name}.bend'])
    else:
        prefix = f'../../../tests/compiler-literals/regressions/{name}.'
        wrapper = CALLS / f'{name}-{fn}-{"-".join(args) or "0"}.bend'
        source = (f'import {prefix}bend as F\n\ndef main() -> F.{out}:\n'
                  f'  F.{fn}({", ".join(f"F.{a}{{}}" for a in args)})\n')
        wrapper.write_text(source)
        record['wrapper'] = {'path': str(wrapper.relative_to(ROOT)), 'source': source}
        observed = oracle.seed([record['wrapper']['path']])
    value = re.fullmatch(re.escape(prefix) + r'(\w+)\{\}\n', observed['stdout'])
    assert observed['exit'] == 0 and observed['stderr'] == '' and value, observed
    assert value.group(1) in kinds[out], observed
    record['constructor'] = value.group(1)
    record['tag'] = kinds[out].index(value.group(1))
    record['seed'] = observed
    return record


def fixture(name):
    finding, covers, entries, knot = PLAN[name]
    path = FIXTURES / f'{name}.bend'
    source = path.read_text()
    kinds, sigs = oracle.enums(source), oracle.signatures(source)
    entry = {'name': name, 'file': str(path.relative_to(ROOT)), 'sha256': oracle.sha256(path),
             'finding': finding, 'covers': covers, 'enums': kinds}
    entry['seed_check'] = oracle.seed([entry['file'], '--check-only'])
    if entry['seed_check']['exit'] == 0:
        assert entry['seed_check']['stdout'] == 'All terms check.\n', entry['seed_check']
        assert knot is oracle.AGREE or knot['outcome'] == 'Unsupported', name
        entry['calls'] = [call(name, 'main', [], kinds, sigs)]
        for fn in entries:
            for args in product(*(kinds[t] for t in sigs[fn][0])):
                entry['calls'].append(call(name, fn, args, kinds, sigs))
        if knot is oracle.AGREE:
            assert len({c['constructor'] for c in entry['calls']}) > 1, f'{name} is constant'
    else:
        assert entry['seed_check']['exit'] == 1 and not entries, (name, entry['seed_check'])
        assert knot['outcome'] == 'Unsupported', name
        entry['seed_run'] = oracle.seed([entry['file']])
        assert entry['seed_run']['exit'] == 1, entry['seed_run']
    entry['knot' if knot is oracle.AGREE else 'knot_expected'] = knot
    return entry


def build():
    names = sorted(p.stem for p in FIXTURES.glob('*.bend'))
    assert names == sorted(PLAN), ('fixtures and PLAN differ', names)
    CALLS.mkdir(parents=True, exist_ok=True)
    return {'purpose': 'D7 freeze of the confirmed review-round-1 findings before their fixes.',
            'generator': 'python3 tests/compiler-literals/regressions.py --write',
            'seed_sha256': {f: oracle.sha256(ROOT / oracle.SEED_DIR / f) for f in oracle.SEED_FILES},
            'fixtures': [fixture(n) for n in names]}


def main():
    text = oracle.render(build())
    if sys.argv[1:] == ['--write']:
        assert oracle.render(build()) == text, 'two seed passes disagree; nothing written'
        DEST.write_text(text)
    else:
        assert not sys.argv[1:], __doc__
        assert DEST.read_text() == text, 'regression seed observations changed'
    doc = json.loads(text)
    calls = sum(len(f.get('calls', [])) for f in doc['fixtures'])
    print(f'literals regressions match the seed: {len(doc["fixtures"])} fixtures, {calls} calls')


if __name__ == '__main__':
    main()
