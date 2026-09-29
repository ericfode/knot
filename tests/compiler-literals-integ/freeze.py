"""Freeze or verify the integration books against the pinned seed.

    python3 tests/compiler-literals-integ/freeze.py          # verify (default)
    python3 tests/compiler-literals-integ/freeze.py --write  # never after the behavior is checked

Each book is a program whose classification the merge of `campaign/nest` into the literals line
decides, and that neither parent suite pins. Expectations come only from the seed and from the
reviewed literals in PLAN; nothing here runs or reads Knot.
"""
import json
import re
import sys
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'compiler-literals'))
import regen as oracle  # noqa: E402  the seed oracle of the literals suite

ROOT = oracle.ROOT
FIXTURES = HERE / 'fixtures'
DEST = HERE / 'expectations.json'
CALLS = ROOT / '.local/compiler-literals-integ/calls'


def invalid(phase, code, why):
    return {'outcome': 'Invalid', 'exit': 2, 'artifact': False,
            'diagnostic_prefix': f'Invalid\t{phase}\t{code}\t', 'justification': why}


KEYWORD = invalid(
    'parse', 'body-indentation',
    'Seed-invalid (an orphaned `case`; "the keyword \'def\' cannot head" a term): the keywords `case` '
    'and `def` head no arm body, so a keyword in body position at or left of its arm is no body.')
CONCAT = oracle.unsupported(
    'parse', 'operator',
    'Seed-valid: `++` is the String concatenation operator, so a spaced `+` after an argument may be '
    'an operator. Knot does not check operator sugar, and reading it as a missing comma would be '
    'Invalid on a valid book (D4).')
COLUMN = oracle.unsupported(
    'check', 'literal-column',
    'Seed-valid: a literal or Nat offset in a row of several columns. Knot checks a literal only in '
    'a single-column match, and claims nothing about the rest (D4).')
LET_OPERATOR = oracle.unsupported(
    'parse', 'operator',
    'Seed-valid: the right side of a let is an operator expression (`a ++ b` concatenates). Knot does '
    'not check operator sugar, so an operator after the value is unsupported, never a missing line end (D4).')
WHITESPACE = oracle.unsupported(
    'parse', 'argument-whitespace',
    'Seed-valid: whitespace separates call arguments, constructor fields and pattern fields, a literal '
    'among them. Knot reads commas, so a term that follows another without one is unsupported (D4).')
BINDING = invalid(
    'parse', 'binding-name',
    'Seed-invalid ("a name (a parallel or typed let binds names; destructure in its body)"): a live dotted '
    'let is valid only where its exact name is already bound, by a parameter or an enclosing let.')
PROMOTED = invalid(
    'check', 'promoted-type',
    'Seed-invalid ("expected : a quantified datatype after +"): the seed reads `+D` as the quantified '
    'datatype D when D names a type declared before it, so no promoted binder is spelled like one.')
UNPLACED = oracle.unsupported(
    'check', 'promoted-type',
    'A promoted binder spelled like a type the checker cannot place: an imported datatype is spelled with '
    'its module, and Base\'s datatypes outside the reachable slice are not in the book. The seed reads '
    '`+D` as a quantified datatype where D is a type in scope, and a fresh name otherwise; the checker '
    'cannot tell which, so the binder is unsupported (D4).')
SHADOW = oracle.unsupported(
    'parse', 'parameter-shadow',
    'Seed-invalid ("expected : Type"): a parameter\'s name shadows the type of that name in the annotations '
    'that follow. Whether such a name is a type parameter is beyond Knot, so it is unsupported (D4).')
ANNOTATION = oracle.unsupported(
    'parse', 'annotation-shadow',
    'Seed-invalid ("expected : Type"): a binder in scope, a parameter, a let erased or live, or a pattern '
    'variable, shadows the type of its name in the annotations below it. Whether the binder is a type-valued '
    'variable is beyond Knot, so it is unsupported (D4).')
ARITY = invalid(
    'check', 'pattern-arity',
    'Seed-invalid ("expected : N patterns (one per scrutinee)"): every row names one pattern per scrutinee.')

# name -> (behavior, covers, entries, Knot)
PLAN = {
    'erased-dotted-let': ('erased dotted let', '`-a.b : Flag = x` and `-a.b = x` with no parameter a.b',
                          ['typed', 'plain'], oracle.AGREE),
    'arm-body-case': ('keyword arm body', 'a `case` in the arm column right after `case Off{}:`', [], KEYWORD),
    'arm-body-def': ('keyword arm body', 'a `def` in column 0 right after `case Off{}:`', [], KEYWORD),
    'spaced-plus-concat': ('spaced plus after an argument', 'two(a ++ b, "ab") on String variables',
                           [], CONCAT),
    'literal-column-u32': ('literal column', '`case 0 No{}` in a two-column match', [], COLUMN),
    'literal-column-offset': ('literal column', '`case 1n+p No{}` in a two-column match', [], COLUMN),
    # Review round 1: the behaviors its findings decided, each frozen before the repair.
    'erased-dotted-rebind': ('erased dotted let', 'a live let of the name of an erased let before it: plain, '
                             'typed, twice erased, three-part, in an arm',
                             ['plain', 'typed', 'twice', 'deep', 'arm'], oracle.AGREE),
    'erased-then-other-dotted': ('erased dotted let', 'a live let of another dotted name after an erased one',
                                 [], BINDING),
    'erased-in-other-arm': ('erased dotted let', 'a live let of the name an erased let binds in the other arm',
                            [], BINDING),
    'let-concat-typed': ('let operator', '`c : String = a ++ b`', [], LET_OPERATOR),
    'let-concat-untyped': ('let operator', '`c = a ++ b`', [], LET_OPERATOR),
    'let-concat-glued': ('let operator', '`c : String = a++b`', [], LET_OPERATOR),
    'literal-column-late-u32': ('literal column', '`case No{} 0` in a two-column match', [], COLUMN),
    'literal-column-late-offset': ('literal column', '`case No{} 1n+p` in a two-column match', [], COLUMN),
    'literal-column-late-nat': ('literal column', '`case No{} 2n` in a two-column match', [], COLUMN),
    'literal-column-late-char': ('literal column', "`case No{} 'a'` in a two-column match", [], COLUMN),
    'literal-column-late-string': ('literal column', '`case No{} "a"` in a two-column match', [], COLUMN),
    'literal-column-third': ('literal column', '`case No{} No{} 0` in a three-column match', [], COLUMN),
    'literal-column-after-binder': ('literal column', '`case v 0` in a two-column match', [], COLUMN),
    'arguments-literals': ('juxtaposed literals', '`two(3 4)`', [], WHITESPACE),
    'arguments-name-literal': ('juxtaposed literals', '`two(x 3)`', [], WHITESPACE),
    'arguments-constructor-literals': ('juxtaposed literals', '`Two{3 4}` as a value', [], WHITESPACE),
    'arguments-field-pattern-literal': ('juxtaposed literals', '`case Two{a 4}:`', [], WHITESPACE),
    'promoted-type-pattern': ('promoted type name', '`case +Flag:` in a default row', [], PROMOTED),
    'promoted-type-field': ('promoted type name', '`case Cell{+Flag}:`', [], PROMOTED),
    'promoted-type-let': ('promoted type name', '`+Flag = x`', [], PROMOTED),
    'promoted-type-let-typed': ('promoted type name', '`+Flag : Flag = x`', [], PROMOTED),
    'promoted-type-own-early': ('promoted type name', '`case +Early:` over the scrutinee\'s own type', [], PROMOTED),
    'promoted-type-nat': ('promoted type name', "Base's `+Nat`", [], PROMOTED),
    'promoted-type-bool': ('promoted type name', "Base's `+Bool`, which the book does not load", [], UNPLACED),
    'promoted-type-module': ('promoted type name', 'a module\'s own type, promoted in its own body', [], UNPLACED),
    'promoted-type-imported': ('promoted type name', '`+Flag` in a file that imports a Flag it does not spell',
                               [], UNPLACED),
    'promoted-type-string': ('promoted type name', "Base's `+String`", [], PROMOTED),
    'promoted-type-later': ('promoted type name', '`+Later` before the declaration of Later',
                            ['f'], oracle.AGREE),
    'promoted-function-name': ('promoted type name', '`+g` where g is a function', ['g', 'f'], oracle.AGREE),
    'promoted-fresh-name': ('promoted type name', '`+z`', ['f'], oracle.AGREE),
    'binder-type-name-plain': ('promoted type name', 'a type\'s name as a plain binder: pattern, erased let, let',
                               ['pattern', 'erased', 'plain'], oracle.AGREE),
    'parameter-shadows-own-type': ('parameter shadow', '`def f(+Flag: Flag)`', [], SHADOW),
    'parameter-shadows-type': ('parameter shadow', '`def f(Flag: Flag)`', [], SHADOW),
    'parameter-shadows-later-type': ('parameter shadow', '`def f(Flag: Other, y: Flag)`', [], SHADOW),
    'parameter-shadows-result': ('parameter shadow', '`def f(Flag: Other) -> Flag`', [], SHADOW),
    'parameter-shadow-unused': ('parameter shadow', 'a parameter named like a type that no annotation reads',
                                ['f', 'g'], oracle.AGREE),
    'annotation-shadow-let': ('annotation shadow', '`Flag = x` then `y : Flag = x`', [], ANNOTATION),
    'annotation-shadow-erased-let': ('annotation shadow', '`-Flag = x` then `y : Flag = x`', [], ANNOTATION),
    'annotation-shadow-pattern': ('annotation shadow', '`case Flag:` then `y : Flag = x` in its body', [], ANNOTATION),
    'annotation-shadow-parameter': ('annotation shadow', '`def f(Flag: Other, ..)` then `y : Flag = x`', [], ANNOTATION),
    'annotation-shadow-unread': ('annotation shadow', 'binders named like types that no annotation below reads, '
                                 'and a let\'s own annotation `Flag : Flag = x`', ['own', 'other', 'arm'], oracle.AGREE),
    'row-wide-nat': ('row width', '`case x y:` over one Nat scrutinee', [], ARITY),
    'row-wide-u32': ('row width', '`case _ _:` over one U32 scrutinee', [], ARITY),
    'row-narrow-literal': ('row width', '`case 0n:` in a two-scrutinee match', [], ARITY),
    'row-narrow-nested-literal': ('row width', '`case Bx{0}:` in a two-scrutinee match', [], ARITY),
    'qualified-order-lib-first': ('module order', 'qualified constructor patterns whose declarations sit later '
                                  'in their file than the patterns', ['f'], oracle.AGREE),
    'qualified-order-lib-last': ('module order', 'the same patterns after the imported declarations by offset',
                                 ['f'], oracle.AGREE),
}


def enums(source):
    """The nullary enums of a book: the values a call is compared on. A datatype with fields has no tag."""
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
        prefix, observed = '', oracle.seed([f'tests/compiler-literals-integ/fixtures/{name}.bend'])
    else:
        prefix = f'../../../tests/compiler-literals-integ/fixtures/{name}.'
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
    behavior, covers, entries, knot = PLAN[name]
    path = FIXTURES / f'{name}.bend'
    source = path.read_text()
    kinds, sigs = enums(source), oracle.signatures(source)
    entry = {'name': name, 'file': str(path.relative_to(ROOT)), 'sha256': oracle.sha256(path),
             'behavior': behavior, 'covers': covers, 'enums': kinds}
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
    return {'purpose': 'D7 freeze of the merge behaviors of nest into literals that no parent suite pins.',
            'generator': 'python3 tests/compiler-literals-integ/freeze.py --write',
            'seed_sha256': {f: oracle.sha256(ROOT / oracle.SEED_DIR / f) for f in oracle.SEED_FILES},
            'fixtures': [fixture(n) for n in names]}


def main():
    text = oracle.render(build())
    if sys.argv[1:] == ['--write']:
        assert oracle.render(build()) == text, 'two seed passes disagree; nothing written'
        DEST.write_text(text)
    else:
        assert not sys.argv[1:], __doc__
        assert DEST.read_text() == text, 'integration seed observations changed'
    doc = json.loads(text)
    calls = sum(len(f.get('calls', [])) for f in doc['fixtures'])
    print(f'integration books match the seed: {len(doc["fixtures"])} fixtures, {calls} calls')


if __name__ == '__main__':
    main()
