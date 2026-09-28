"""Freeze or verify the review regression books against the pinned seed.

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


def invalid(phase, code, why):
    return {'outcome': 'Invalid', 'exit': 2, 'artifact': False,
            'diagnostic_prefix': f'Invalid\t{phase}\t{code}\t', 'justification': why}


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
ANNOTATION = invalid(
    'check', 'annotation-required',
    'Seed-invalid ("an annotated term (cannot infer)"): a literal or a Nat offset checks '
    'against a known type, and an unannotated binding supplies none.')
SCRUTINEE = invalid(
    'check', 'constructor-scrutinee',
    'Seed-invalid ("an undestructed scrutinee"): a literal or a Nat offset is already a '
    'constructor value.')
PATTERN = invalid(
    'check', 'pattern-type',
    'Seed-invalid ("a constructor of" the scrutinee type): a literal or a Nat offset '
    'pattern spells a constructor of its primitive type, never of the scrutinee type.')
NESTED = oracle.unsupported(
    'check', 'nested-field-pattern',
    'Knot has no nested field patterns, and a literal inside a constructor pattern is one '
    '(D4); the seed also rejects this single-arm book as missing cases.')
BINDER = oracle.unsupported(
    'check', 'variable-pattern',
    'Seed-valid: `0n+p` reads as the binder p, and Knot does not check a binder arm over a '
    'datatype (D4).')
ESCAPE = invalid(
    'lex', 'escape',
    'Seed-invalid ("an escape"): `\\q` is no escape; a following `{` opens a code point only '
    'after `u` or `U`.')
AFFINE = invalid(
    'check', 'affine-reuse',
    'Seed-invalid ("consumed more than once"): a binder or field without `+` over a split '
    'column is affine, so two uses are a reuse.')

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
    'string-doubling': ('long strings', 'String.append doubling to 131072 Chars; length, reverse and eq',
                        ['length', 'mirrored'], oracle.AGREE),
    'let-u32': ('let literal', 'n = 3', [], ANNOTATION),
    'let-u32-promoted': ('let literal', '+n = 3', [], ANNOTATION),
    'let-char': ('let literal', "c = 'a'", [], ANNOTATION),
    'let-nat': ('let literal', 'n = 3n', [], ANNOTATION),
    'let-nat-promoted': ('let literal', '+n = 3n', [], ANNOTATION),
    'let-string': ('let literal', 's = "ab"', [], ANNOTATION),
    'let-string-promoted': ('let literal', '+s = "ab"', [], ANNOTATION),
    'let-offset': ('let literal', 'n = 2n+m', [], ANNOTATION),
    'let-annotated': ('let literal control', 'annotated U32, Char, Nat offset and String lets',
                      ['word', 'letter', 'number', 'text'], oracle.AGREE),
    'scrutinee-u32': ('literal scrutinee', 'match 3', [], SCRUTINEE),
    'scrutinee-char': ('literal scrutinee', "match 'a'", [], SCRUTINEE),
    'scrutinee-nat': ('literal scrutinee', 'match 3n', [], SCRUTINEE),
    'scrutinee-string': ('literal scrutinee', 'match "ab"', [], SCRUTINEE),
    'scrutinee-offset': ('literal scrutinee', 'match 1n+m', [], SCRUTINEE),
    'pattern-u32-on-enum': ('literal pattern on a datatype', 'case 3 on Answer', [], PATTERN),
    'pattern-string-on-enum': ('literal pattern on a datatype', 'case "a" on Answer', [], PATTERN),
    'pattern-offset-on-enum': ('literal pattern on a datatype', 'case 1n+p on Answer', [], PATTERN),
    'pattern-u32-on-bool': ('literal pattern on a datatype', 'case 0 on Base Bool', [], PATTERN),
    'offset-zero': ('zero offset', '0n+t as an inferred let, a checked argument, a scrutinee, '
                    'and a Nat, U32 or String binder arm',
                    ['inferred', 'checked', 'scrutinee', 'nat_binder', 'u32_binder', 'string_binder'],
                    oracle.AGREE),
    'let-offset-zero-literal': ('zero offset', 'n = 0n+3n reads as n = 3n', [], ANNOTATION),
    'pattern-offset-zero-on-enum': ('zero offset', 'case 0n+p on Answer is the binder p', [], BINDER),
    'field-pattern-u32': ('literal field pattern', 'case Box{3}', [], NESTED),
    'field-pattern-offset': ('literal field pattern', 'case Cell{1n+p}', [], NESTED),
    'escape-brace': ('escape before a brace', 'the seven escapes before `{`, plus `\\n}`, `ab{`, '
                     '`\\u{41}{` and `\\U{41}{`', ['pair', 'decoded'], oracle.AGREE),
    'escape-brace-unknown': ('escape before a brace', '`\\q{` stays an unknown escape', [], ESCAPE),
    'promoted-split': ('promoted split binder', '`+x`, `1n+ +p` and `SCon{c, +t}` used twice over '
                       'Nat and String columns that literal, offset or constructor rows split',
                       ['nat_after_literals', 'nat_after_offset', 'nat_default', 'nat_first',
                        'nat_unlettered', 'string_default', 'string_tail'], oracle.AGREE),
    'affine-split-alias': ('promoted split binder control', 'case x used twice after case 0n', [], AFFINE),
    'affine-split-field': ('promoted split binder control', 'case 1n+p with p used twice', [], AFFINE),
    'affine-split-tail': ('promoted split binder control', 'case SCon{c, t} with t used twice after '
                          'case "ab"', [], AFFINE),
    'promoted-scrutinee': ('promoted split binder', 'the scrutinee used twice, or beside the binder, in '
                           'a `+x` or `SCon{c, +t}` arm over Nat, String and U32',
                           ['nat_alone', 'nat_after_literal', 'nat_after_constructor', 'nat_beside',
                            'string_doubled', 'string_tail', 'u32_twice'], oracle.AGREE),
    'affine-scrutinee': ('promoted split binder control', 'the scrutinee used twice in a `case x` arm '
                         'after case 0n', [], AFFINE),
    'promoted-column': ('promoted split binder', 'one `+` row promotes its column and fields in every '
                        'row: fields and the scrutinee used twice in plain rows over Nat, String, U32 '
                        'and Char, an inner `1n+ +q`, and an unreachable `+y`',
                        ['nat_offset', 'nat_successor', 'nat_deep', 'nat_inner', 'nat_unreached',
                         'string_tail', 'string_whole', 'u32_twice', 'char_same'], oracle.AGREE),
    'affine-column': ('promoted split binder control', 'case 1n+p with p used twice before a plain '
                      'case x', [], AFFINE),
}


def enums(source):
    """Nullary enums by name; a datatype with fields never types an entry argument."""
    found = {}
    for name, body in re.findall(r'^type (\w+) is (?:Type|Data):\n((?:  .*\n)+)', source, re.M):
        ctors = re.findall(r'^  (\w+)\{\}$', body, re.M)
        if len(ctors) == len(body.splitlines()):
            found[name] = ctors
    return found


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
    kinds, sigs = enums(source), oracle.signatures(source)
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
        assert knot['outcome'] in ('Invalid', 'Unsupported'), name
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
