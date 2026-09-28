"""Freeze or verify the primitive-result books against the pinned seed.

    python3 tests/compiler-literals/results.py          # verify (default)
    python3 tests/compiler-literals/results.py --write  # before implementation only

Review round 4 found that the evaluator printed U32 and Char results as
constructor tags. Each call below returns a primitive, or a record with
primitive fields, and names the display Knot must print, fixed here by literal
review before the fix (D7). A primitive's display is the seed's own text for
it, byte for byte. A record keeps Knot's constructor frame, Name{a,b} over live
fields, which the fields and recursion suites already pin; the seed separates
fields with ", " and qualifies an imported book's constructors, so a record
call also writes the seed's text literally. Nothing here runs or reads Knot.
"""
import json
import re
import sys
import regen as oracle

HERE, ROOT = oracle.HERE, oracle.ROOT
FIXTURES = HERE / 'results'
DEST = HERE / 'results.json'
CALLS = ROOT / '.local/compiler-literals/result-calls'
FINDING = 'review round 4: U32 and Char results printed as constructor tags'
QUALIFIED = '../../../tests/compiler-literals/results/result-record.'


def char(code):
    """A code the seed prints raw, as UTF-8, inside Char quotes."""
    return "'" + chr(code) + "'"


def text(*codes):
    return '"' + ''.join(map(chr, codes)) + '"'


# name -> (covers, {(export, argument constructors): (Knot display, seed stdout or None)})
# None means the seed prints the display itself, followed by a newline.
PLAN = {
    'result-u32': ('decimal U32 results, from literals and from wrapping and shifting operations', {
        ('main', ()): ('300', None),
        ('sample', ('Least',)): ('0', None),
        ('sample', ('Hundreds',)): ('300', None),
        ('sample', ('Most',)): ('4294967295', None),
        ('sample', ('Wrapped',)): ('4294967295', None),
        ('sample', ('Shifted',)): ('2147483648', None),
    }),
    'result-char': ('quoted Char results: every named escape, the quote rule, the raw and escaped '
                    'code ranges at each boundary, and computed Chars', {
        ('main', ()): (r"'\u{1}'", None),
        ('sample', ('Nul',)): (r"'\0'", None),
        ('sample', ('Start',)): (r"'\u{1}'", None),
        ('sample', ('Letter',)): ("'a'", None),
        ('sample', ('Apostrophe',)): (r"'\''", None),
        ('sample', ('Quotation',)): ("'\"'", None),
        ('sample', ('Backslash',)): (r"'\\'", None),
        ('sample', ('Newline',)): (r"'\n'", None),
        ('sample', ('Tab',)): (r"'\t'", None),
        ('sample', ('CarriageReturn',)): (r"'\r'", None),
        ('sample', ('UnitSeparator',)): (r"'\u{1f}'", None),
        ('sample', ('Space',)): ("' '", None),
        ('sample', ('Tilde',)): ("'~'", None),
        ('sample', ('Delete',)): (r"'\u{7f}'", None),
        ('sample', ('FirstC1',)): (char(0x80), None),
        ('sample', ('LastC1',)): (char(0x9f), None),
        ('sample', ('Latin',)): (char(0xe9), None),
        ('sample', ('BeforeSurrogates',)): (char(0xd7ff), None),
        ('sample', ('HighSurrogate',)): (r"'\u{d83d}'", None),
        ('sample', ('LowSurrogate',)): (r"'\u{dfff}'", None),
        ('sample', ('AfterSurrogates',)): (char(0xe000), None),
        ('sample', ('Noncharacter',)): (char(0xfffe), None),
        ('sample', ('Emoji',)): (char(0x1f600), None),
        ('sample', ('LastScalar',)): (char(0x10ffff), None),
        ('sample', ('PastScalar',)): (r"'\u{110000}'", None),
        ('sample', ('AllOnes',)): (r"'\u{ffffffff}'", None),
        ('sample', ('Sum',)): ("'A'", None),
        ('sample', ('FromCode',)): (r"'\n'", None),
    }),
    'result-string': ('quoted String results: escapes, the quote rule, boundaries, separators and '
                      'braces, surrogate pairs literal and computed, and computed Strings', {
        ('main', ()): (r'"\0"', None),
        ('sample', ('Blank',)): ('""', None),
        ('sample', ('Nul',)): (r'"\0"', None),
        ('sample', ('Greeting',)): ('"hi"', None),
        ('sample', ('Escapes',)): (r'"\0\t\n\r\\"', None),
        ('sample', ('Quotes',)): ('"\'\\""', None),
        ('sample', ('Separators',)): ('"a, b{}"', None),
        ('sample', ('Controls',)): (r'"\u{1}\u{1f}\u{7f}"', None),
        ('sample', ('Boundaries',)): (text(0x80, 0x9f, 0xfffe, 0x10ffff), None),
        ('sample', ('Surrogates',)): (r'"\u{d83d}\u{de00}"', None),
        ('sample', ('JoinedSurrogates',)): (r'"\u{d83d}\u{de00}"', None),
        ('sample', ('ReversedSurrogates',)): (r'"\u{d83d}\u{de00}"', None),
        ('sample', ('PastScalar',)): (r'"a\u{110000}"', None),
        ('sample', ('Emoji',)): (text(0x1f600), None),
        ('sample', ('Shown',)): ('"300"', None),
        ('sample', ('NatShown',)): ('"12"', None),
        ('sample', ('Appended',)): (r'"a\nb"', None),
    }),
    'result-nat': ('Nat results as decimal n literals, from literals and operations', {
        ('main', ()): ('3n', None),
        ('sample', ('Nothing',)): ('0n', None),
        ('sample', ('Three',)): ('3n', None),
        ('sample', ('Sum',)): ('5n', None),
        ('sample', ('Saturated',)): ('0n', None),
        ('sample', ('FromWord',)): ('300n', None),
        ('sample', ('Largest',)): ('256n', None),
    }),
    'result-record': ('records with U32, Char, Nat, String, enum, Bool and nested record fields', {
        ('main', ()): ("Box{1,'a'}", "Box{1, 'a'}\n"),
        ('zeroes', ()): (r"Box{0,'\0'}", QUALIFIED + r"Box{0, '\0'}" + '\n'),
        ('mix', ()): ('Mix{3n,"a, b{}",Right{},True{},Box{4294967295,\'\\\'\'},Box{0,\'"\'}}',
                      f'{QUALIFIED}Mix{{3n, "a, b{{}}", {QUALIFIED}Right{{}}, True{{}}, '
                      f'{QUALIFIED}Box{{4294967295, \'\\\'\'}}, {QUALIFIED}Box{{0, \'"\'}}}}\n'),
    }),
}

PRIMITIVES = {'U32', 'Char', 'String', 'Nat'}


def enums(source):
    """Nullary enums by name; a datatype with fields never types an entry argument."""
    found = {}
    for name, body in re.findall(r'^type (\w+) is (?:Type|Data):\n((?:  .*\n)+)', source, re.M):
        ctors = re.findall(r'^  (\w+)\{\}$', body, re.M)
        if len(ctors) == len(body.splitlines()):
            found[name] = ctors
    return found


def call(name, fn, args, kinds, sigs, display, stdout):
    params, out = sigs[fn]
    assert all(t in kinds for t in params), (name, fn)
    record = {'export': fn, 'arguments': [kinds[t].index(a) for t, a in zip(params, args)],
              'argument_constructors': list(args), 'type': out, 'display': display}
    if fn == 'main':
        observed = oracle.seed([f'tests/compiler-literals/results/{name}.bend'])
    else:
        prefix = f'../../../tests/compiler-literals/results/{name}.'
        wrapper = CALLS / f'{name}-{fn}-{"-".join(args) or "0"}.bend'
        result = out if out in PRIMITIVES else f'F.{out}'
        source = (f'import {prefix}bend as F\n\ndef main() -> {result}:\n'
                  f'  F.{fn}({", ".join(f"F.{a}{{}}" for a in args)})\n')
        wrapper.write_text(source)
        record['wrapper'] = {'path': str(wrapper.relative_to(ROOT)), 'source': source}
        observed = oracle.seed([record['wrapper']['path']])
    expected = display + '\n' if stdout is None else stdout
    assert observed == {**observed, 'exit': 0, 'stdout': expected, 'stderr': ''}, (name, fn, args, observed)
    record['seed'] = observed
    return record


def fixture(name, base):
    covers, calls = PLAN[name]
    path = FIXTURES / f'{name}.bend'
    source = path.read_text()
    kinds, sigs = enums(source), oracle.signatures(source)
    local = {*kinds, *sigs, *sum(kinds.values(), [])}
    assert not local & {n.split('.')[0] for n in base}, f'{name} reuses a Base name'
    entry = {'name': name, 'file': str(path.relative_to(ROOT)), 'sha256': oracle.sha256(path),
             'finding': FINDING, 'covers': covers, 'enums': kinds}
    entry['seed_check'] = oracle.seed([entry['file'], '--check-only'])
    assert entry['seed_check'] == {**entry['seed_check'], 'exit': 0, 'stdout': 'All terms check.\n',
                                   'stderr': ''}, entry['seed_check']
    entry['calls'] = [call(name, fn, args, kinds, sigs, *expected) for (fn, args), expected in calls.items()]
    assert len({c['display'] for c in entry['calls']}) > 1, f'{name} is constant'
    return entry


def build():
    names = sorted(p.stem for p in FIXTURES.glob('*.bend'))
    assert names == sorted(PLAN), ('fixtures and PLAN differ', names)
    CALLS.mkdir(parents=True, exist_ok=True)
    base = oracle.base_names()
    return {'purpose': 'D7 freeze of the review-round-4 result displays before their fix.',
            'generator': 'python3 tests/compiler-literals/results.py --write',
            'display': 'Knot prints Evaluated<TAB>type<TAB>word<TAB>display; each display below is '
                       'compared byte for byte. The seed prints a primitive display itself.',
            'seed_sha256': {f: oracle.sha256(ROOT / oracle.SEED_DIR / f) for f in oracle.SEED_FILES},
            'fixtures': [fixture(n, base) for n in names]}


def main():
    text = oracle.render(build())
    if sys.argv[1:] == ['--write']:
        assert oracle.render(build()) == text, 'two seed passes disagree; nothing written'
        DEST.write_text(text)
    else:
        assert not sys.argv[1:], __doc__
        assert DEST.read_text() == text, 'result seed observations changed'
    doc = json.loads(text)
    calls = sum(len(f['calls']) for f in doc['fixtures'])
    print(f'literals results match the seed: {len(doc["fixtures"])} fixtures, {calls} calls')


if __name__ == '__main__':
    main()
