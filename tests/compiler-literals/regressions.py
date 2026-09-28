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
DEAD = oracle.unsupported(
    'check', 'dead-arm',
    'Seed-valid: the seed checks a body only where its arm is the first applicable one, so a '
    'failing body that no path reaches first is not evidence of an invalid book (D4).')
LIVE = invalid(
    'check', 'type-mismatch',
    'Seed-invalid ("expected U32"): the arm is the first applicable one on some path, so its '
    'body is checked there.')
DEAD_PATTERN = {
    'arity': invalid('check', 'pattern-arity',
                     'Seed-invalid ("a Succ pattern with 1 field"): the seed checks the patterns of '
                     'unreachable arms.'),
    'offset-limit': invalid('parse', 'nat-offset-pattern',
                            'Seed-invalid ("a pattern (a binder or a constructor)"): an offset above '
                            '256 is no pattern, reachable or not.'),
    'constructor': invalid('check', 'pattern-type',
                           'Seed-invalid ("a constructor of Nat"): the seed checks the patterns of '
                           'unreachable arms.'),
    'type': invalid('check', 'pattern-type',
                    'Seed-invalid ("a constructor of U32"): the seed checks the patterns of '
                    'unreachable arms.'),
}
BASE_TYPE = oracle.unsupported(
    'check', 'literal-base-type',
    "A literal spells an installed primitive; the book's own datatype of that name is none. "
    'The seed accepts the Nat book and rejects the U32 book, so Knot claims neither (D4).')
SPELLED = oracle.unsupported(
    'check', 'literal-base-type',
    "Seed-valid: without Base, the seed spells the literal by bare constructor names (Zero and "
    'Succ, SNil and SCon) that the target datatype declares. Knot keys the case on the absent '
    'installed primitive, not on the type name, and does not interpret the spelling (D4).')
WORD_SPELLED = oracle.unsupported(
    'check', 'literal-base-type',
    'Seed-invalid ("unknown: U32"): without Base, a U32 literal spells Base\'s Word, which Knot '
    'does not model, so it claims no verdict for any target, as for own-u32-literal (D4).')
UNSPELLED = invalid(
    'check', 'unknown-type',
    'Seed-invalid ("a declared constructor"): without Base, the literal takes no installed '
    'primitive, and the target declares no constructor it spells: N declares Z and S, and an '
    'imported datatype declares only qualified names.')

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
    'offset-expression-depth': ('offset expression depth', '`1n+`, `2n+` (Base Nat.double) and `3n+` '
                                'expression offsets through recursion 3000-4000 deep, and a `0n+t` control',
                                ['successor', 'successor_short', 'doubled', 'tripled', 'zero'], oracle.AGREE),
    'offset-expression-width': ('offset expression width', '`1364n+t`, `1365n+t` and `2000n+t` as single '
                                'expressions, and a No control', ['at_edge', 'past_edge', 'wide_sum', 'wide_short'],
                                oracle.AGREE),
    'offset-expression-mismatch': ('offset expression control', '`2n+t` where a U32 is expected', [],
                                   invalid('check', 'type-mismatch',
                                           'Seed-invalid ("expected U32"): an expression offset is a Nat.')),
    'offset-expression-unbound': ('offset expression control', '`2n+zz` with zz unbound', [],
                                  invalid('check', 'free-name',
                                          'Seed-invalid ("a defined name"): the tail of an offset is an expression '
                                          'like any other.')),
    'offset-expression-both': ('offset expression control', '`2n+zz` where a U32 is expected', [],
                               invalid('check', 'free-name',
                                       'Seed-invalid: an unbound tail and a wrong result type at once. The seed names '
                                       'the type first and Knot the tail; both are Invalid, and the frozen code is '
                                       'the one Knot reports today.')),
    'module-width': ('module width', 'a 3000-Char String, a `case 450n` and a 100-Char String pattern '
                     'in one module past 64 KiB', ['length', 'depth', 'spelled'], oracle.AGREE),
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
    'affine-default-scrutinee': ('promoted split binder control', '`v + v` in a catch-all after '
                                 '`Succ{+p}`', [], AFFINE),
    'affine-default-binder': ('promoted split binder control', '`x + x` in a `case x` after `1n+ +p`',
                              [], AFFINE),
    'affine-default-string': ('promoted split binder control', '`v ++ v` in a catch-all after '
                              '`SCon{+c, +t}`', [], AFFINE),
    'dead-arm-u32-duplicate': ('dead arm', "case 5: 'q' after case 5", [], DEAD),
    'dead-arm-u32-after-default': ('dead arm', 'case 3: "s" after case y', [], DEAD),
    'dead-arm-u32-affine': ('dead arm', 'case 3: k + k after case y', [], DEAD),
    'dead-arm-u32-free-name': ('dead arm', 'case 3: zzz after case y', [], DEAD),
    'dead-arm-char-duplicate': ('dead arm', "case 'a': \"no\" after case 'a'", [], DEAD),
    'dead-arm-nat-subsumed': ('dead arm', "case 2n: 'a' after case 1n+p", [], DEAD),
    'dead-arm-nat-affine': ('dead arm', 'case 2n: k + k after case 1n+p', [], DEAD),
    'dead-arm-nat-offset-subsumed': ('dead arm', "case 3n+q: 'x' after case 1n+p", [], DEAD),
    'dead-arm-nat-duplicate-zero': ('dead arm', "case 0n: 'x' after case 0n", [], DEAD),
    'dead-arm-nat-constructor-duplicate': ('dead arm', "case Zero{}: 'x' after case Zero{}", [], DEAD),
    'dead-arm-string-after-default': ('dead arm', "case \"a\": 'c' after case _", [], DEAD),
    'dead-arm-string-duplicate': ('dead arm', 'case "a": 1n after case "a"', [], DEAD),
    'dead-arm-string-nested': ('dead arm', "case SCon{'a', SNil{}}: 'x' after case \"a\"", [], DEAD),
    'live-arm-nat-offset': ('dead arm control', "case 3n+q: 'x' before case 1n+p", [], LIVE),
    'live-arm-u32-default': ('dead arm control', "case _: 'q', shadowed on the 5 path only", [], LIVE),
    'dead-pattern-arity': ('dead arm control', 'case Succ{a, b} after case _', [], DEAD_PATTERN['arity']),
    'dead-pattern-offset-limit': ('dead arm control', 'case 300n+p after case _', [],
                                  DEAD_PATTERN['offset-limit']),
    'dead-pattern-constructor': ('dead arm control', 'case SNil{} on Nat after case _', [],
                                 DEAD_PATTERN['constructor']),
    'dead-pattern-type': ('dead arm control', "case 'a' on U32 after case _", [], DEAD_PATTERN['type']),
    'own-nat-literal': ('own primitive type', "2n against the book's own Nat, without Base", [], BASE_TYPE),
    'own-u32-literal': ('own primitive type', "3 against the book's own U32, without Base", [], BASE_TYPE),
    'own-nat-zero-pattern': ('own primitive pattern', "case 0n on the book's own Nat, without Base", [], SPELLED),
    'own-nat-literal-pattern': ('own primitive pattern', "case 2n on the book's own Nat", [], SPELLED),
    'own-nat-offset-pattern': ('own primitive pattern', "case 1n+p on the book's own Nat", [], SPELLED),
    'own-n-literal-pattern': ('own primitive pattern', 'case 2n on an own Zero/Succ type named N', [], SPELLED),
    'own-n-offset-pattern': ('own primitive pattern', 'case 1n+p on an own Zero/Succ type named N', [], SPELLED),
    'own-dotted-literal-pattern': ('own primitive pattern', 'case 2n on an own Zero/Succ type named A.T',
                                   [], SPELLED),
    'own-string-empty-pattern': ('own primitive pattern', "case \"\" on the book's own String", [], SPELLED),
    'own-t-empty-pattern': ('own primitive pattern', 'case "" on an own SNil/SCon type named T', [], SPELLED),
    'own-u32-pattern': ('own primitive pattern', "case 3 on the book's own U32, which declares only Z",
                        [], WORD_SPELLED),
    'own-unspelled-pattern': ('own primitive pattern control', 'case 0n on an own type N{Z, S}', [], UNSPELLED),
    'own-nat-pattern-module': ('own primitive pattern control', 'own-nat-literal-pattern imported as a module',
                               [], UNSPELLED),
    'own-nat-offset-expr': ('own primitive expression', "1n+n against the book's own Nat", [], SPELLED),
    'own-string-empty-expr': ('own primitive expression', "\"\" against the book's own String", [], SPELLED),
    'own-n-literal-expr': ('own primitive expression', '2n against an own Zero/Succ type named N', [], SPELLED),
    'own-n-offset-expr': ('own primitive expression', '2n+n against an own Zero/Succ type named N', [], SPELLED),
    'own-t-empty-expr': ('own primitive expression', '"" against an own SNil/SCon type named T', [], SPELLED),
    'own-n-expr-module': ('own primitive expression control', 'own-n-literal-expr imported as a module',
                          [], UNSPELLED),
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
