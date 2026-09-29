#!/usr/bin/env python3
"""Replay round-12 seed observations. --emit writes the fixtures; --write is only for the pre-fix freeze.

The fixtures are generated from small templates, as in round 11: Knot outcomes are literal review,
keyed by group, and the seed decides only acceptance and, for a rejected group, the reason.
The pinned seed (`bend2/bend.ts`) reads:

- `match_flatten` (finding 3): the field binders `xs` of a constructor split are the first row's own
  field variables, each joined with the marks of its column (`patt_mark`). A `+` on a field of the
  first row that starts a constructor's split therefore marks that field in every row below the
  split, and again at each later split of the remaining rows. A `+` in a later row marks only that
  row's own binder; the marks of a variable column reach every row of the column it closes.
- `parse_term_ops` (finding 1): after a term the seed reads a call `(`, an index `[`, an offload
  `!(`, a lambda `=>` and any operator of its INFIX table (`->`, `&`, `|`, `||`, `&&`, `<`, `<=`,
  `>`, `>=`, `<>`, `++`, `<&>`, `.|.`, `.^.`, `.&.`, `<<`, `>>`, `+`, `-`, `*`, `/`, `%`); `+` and
  `-` touching a name are markers instead. `parse_term_base` reads `+name` as a promoted
  variable. A body the lowering discards is parsed and never checked, so each of these is accepted
  there; a live one needs a target the program defines (`def Bool.or`, `def Pair`, `Array.get`).

The reviewed Knot outcomes: `Accepted` for finding 3's programs and `Invalid check affine-reuse` or
`reusable-type` for the controls the seed rejects; `Unsupported parse term-form` for a term suffix
and a `+name` term wherever they stand, since the parser cannot tell a discarded body from a live one
and never judges the operands; `Invalid` where no term can continue (a closer, `==`, `=>` after a
constructor, an erased `-name`).
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import regen as oracle
import review_seed

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'round12-expectations.json'
FIXTURES = HERE / 'round12-fixtures'
ACCEPTED = {'exit': 0, 'outcome': 'Accepted'}
AFFINE = 'consumed more than once'
KIND = 'expected : Data'


def check(code):
    return {'exit': 2, 'diagnostic': f'Invalid\tcheck\t{code}\t'}


def unsupported(code):
    return {'exit': 3, 'diagnostic': f'Unsupported\tparse\t{code}\t'}


def invalid(code):
    return {'exit': 2, 'diagnostic': f'Invalid\tparse\t{code}\t'}


GROUPS = {}   # group -> (Knot outcome, seed reason or None, [(name, source[, reason])])


def group(name, knot, reason, *cases):
    assert name not in GROUPS, name
    GROUPS[name] = (knot, reason, list(cases))


# --- Finding 3: the first row of a constructor split marks its fields for every row below it.
PLUS_PRE = '''type Flag is Data:
  Off{}
  On{}

type Pair is Type:
  P{l: Flag, r: Flag}

type Trip is Type:
  T3{a: Flag, b: Flag, c: Flag}

type Box is Type:
  Bx{p: Pair}

type Two is Type:
  A{x: Flag, y: Flag}
  B{x: Flag, y: Flag}

type Data2 is Data:
  D2{l: Flag, r: Flag}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

'''
# shape -> (parameters, scrutinees, probe parameters, probe body, main call)
SHAPES = {
    'pair': ('p: Pair', 'p', 'a: Flag, b: Flag', 'f(P{a, b})', 'probe(On{}, Off{})'),
    'trip': ('p: Trip', 'p', 'a: Flag, b: Flag, c: Flag', 'f(T3{a, b, c})', 'probe(On{}, Off{}, On{})'),
    'box': ('x: Box', 'x', 'a: Flag, b: Flag', 'f(Bx{P{a, b}})', 'probe(On{}, Off{})'),
    'two': ('t: Two', 't', 'a: Flag, b: Flag, k: Flag',
            'match k:\n    case On{}: f(A{a, b})\n    case Off{}: f(B{a, b})', 'probe(On{}, Off{}, On{})'),
    'data': ('p: Data2', 'p', 'a: Flag, b: Flag', 'f(D2{a, b})', 'probe(On{}, Off{})'),
    'pair2': ('p: Pair, q: Flag', 'p q', 'a: Flag, b: Flag, c: Flag', 'f(P{a, b}, c)', 'probe(On{}, Off{}, On{})'),
}


def plus(shape, *rows):
    params, scrutinees, probe_params, probe, main = SHAPES[shape]
    body = ''.join(f'    case {row}\n' for row in rows)
    return (PLUS_PRE + f'def f({params}) -> Flag:\n  match {scrutinees}:\n{body}\n'
            + f'def probe({probe_params}) -> Flag:\n  {probe}\n\ndef main() -> Flag:\n  {main}\n')


ROWS = {
    # the reviewer's programs: a `+` in the first row, a second row using the field twice
    'pair': ('pair', 'P{On{}, +v}: both(v, v)', 'P{Off{}, v}: both(v, v)'),
    'second-once': ('pair', 'P{On{}, +v}: v', 'P{Off{}, w}: both(w, w)'),
    'var-row-after': ('pair', 'P{On{}, +v}: v', 'P{_, w}: both(w, w)'),
    'three-rows': ('pair', 'P{On{}, +v}: v', 'P{Off{}, v}: v', 'P{_, v}: both(v, v)'),
    'underscore': ('pair', 'P{On{}, +_}: On{}', 'P{Off{}, v}: both(v, v)'),
    'underscore-name': ('pair', 'P{On{}, +_x}: _x', 'P{Off{}, v}: both(v, v)'),
    'two-levels': ('box', 'Bx{P{On{}, +b}}: b', 'Bx{P{Off{}, b}}: both(b, b)', 'Bx{P{_, _}}: Off{}'),
    'data-parent': ('data', 'D2{Off{}, +a}: both(a, a)', 'D2{a, b}: both(b, b)', 'D2{Off{}, Off{}}: Off{}'),
    # the neighbours: each field position, both fields, three fields, a nested split, two columns
    'first-field': ('pair', 'P{+a, On{}}: a', 'P{a, Off{}}: both(a, a)'),
    'both-fields': ('pair', 'P{+a, +b}: On{}', 'P{a, b}: both(both(a, a), both(b, b))'),
    'trip-first': ('trip', 'T3{+a, On{}, On{}}: a', 'T3{a, b, c}: both(a, both(a, b))', 'T3{_, _, _}: Off{}'),
    'trip-middle': ('trip', 'T3{On{}, +b, On{}}: b', 'T3{a, b, c}: both(b, both(b, c))', 'T3{_, _, _}: Off{}'),
    'trip-last': ('trip', 'T3{On{}, On{}, +c}: c', 'T3{a, b, c}: both(c, both(c, a))', 'T3{_, _, _}: Off{}'),
    'trip-two-marks': ('trip', 'T3{On{}, +b, +c}: both(b, c)', 'T3{Off{}, b, c}: both(both(b, b), both(c, c))', 'T3{_, _, _}: Off{}'),
    'wide': ('pair', 'P{On{}, +v}: v', 'P{Off{}, w}: both(w, w)', 'P{On{}, x}: both(x, x)', 'P{Off{}, y}: y'),
    'columns': ('pair2', 'P{On{}, +v} _: v', 'P{Off{}, v} _: both(v, v)'),
    'columns-second': ('pair2', 'P{On{}, +v} On{}: v', 'P{Off{}, v} On{}: both(v, v)', 'P{_, w} Off{}: both(w, w)'),
    # a constructor split in the default matrix of an earlier split takes the marks of its own first row
    'default-split': ('two', 'A{On{}, +y}: y', 'B{Off{}, +z}: z', 'A{Off{}, y}: both(y, y)', 'B{On{}, z}: both(z, z)'),
    # the marks of a variable row reach the fields of every row it shares a column with
    'var-row-marks': ('data', 'D2{On{}, a}: both(a, a)', '+q: On{}'),
}
group('plusfirst', ACCEPTED, None, *[(f'plusfirst-{name}', plus(*spec)) for name, spec in ROWS.items()])
# What the seed rejects for the same shapes: the `+` is in a later row, another constructor's first
# row, another column or a variable row; a first-row `+` on a Type field; no `+` at all.
CONTROLS = {
    'later-row': ('pair', 'P{Off{}, v}: both(v, v)', 'P{On{}, +v}: both(v, v)'),
    'other-constructor': ('two', 'A{On{}, +y}: y', 'B{Off{}, y}: both(y, y)', 'A{Off{}, y}: both(y, y)', 'B{On{}, +y}: y'),
    'second-column': ('pair2', 'P{On{}, y} +z: z', 'P{Off{}, y} z: both(z, z)'),
    'underscore-flat': ('pair2', 'P{On{}, y} +_: On{}', 'P{Off{}, y} v: both(v, v)', 'P{On{}, y} v: both(v, v)'),
    'no-plus': ('pair', 'P{On{}, v}: both(v, v)', 'P{Off{}, v}: both(v, v)'),
    'other-field': ('pair', 'P{On{}, +v}: v', 'P{a, Off{}}: both(a, a)', 'P{_, _}: Off{}'),
    'trip-other-field': ('trip', 'T3{On{}, +b, On{}}: b', 'T3{a, b, c}: both(a, both(a, c))', 'T3{_, _, _}: Off{}'),
    'default-split-plain': ('two', 'A{On{}, +y}: y', 'B{Off{}, z}: both(z, z)', 'A{Off{}, y}: both(y, y)', 'B{On{}, +z}: z'),
    'nested-later': ('box', 'Bx{P{On{}, b}}: both(b, b)', 'Bx{P{Off{}, +b}}: b', 'Bx{P{_, _}}: Off{}'),
    'data-later': ('data', 'D2{Off{}, a}: both(a, a)', 'D2{On{}, +a}: a', 'D2{_, _}: Off{}'),
}
group('plusfirst-control', check('affine-reuse'), AFFINE, *[(f'plusfirst-ctl-{name}', plus(*spec)) for name, spec in CONTROLS.items()])
# A `+` may raise a binder only within its type's kind: on a Type field it is rejected, first row or later.
TYPE_KIND = {
    'type-first': ('box', 'Bx{+q}: On{}', 'Bx{P{a, b}}: both(a, a)'),
    'type-later': ('box', 'Bx{P{a, b}}: both(a, a)', 'Bx{+q}: On{}'),
}
group('plusfirst-kind', check('reusable-type'), KIND, *[(f'plusfirst-ctl-{name}', plus(*spec)) for name, spec in TYPE_KIND.items()])
# One row: the field is marked in it, as before.
group('plusfirst-flat', ACCEPTED, None, ('plusfirst-ctl-flat', plus('pair', 'P{a, +v}: both(v, v)')))

# --- Finding 1: a term suffix after a complete term, and a `+name` term, are unsupported wherever they stand.
TERM_PRE = '''type Flag is Data:
  Off{}
  On{}

type Pr is Type:
  Pr{l: Flag, r: Flag}

def h(a: Flag) -> Flag:
  a

'''
# form -> (source text, the seed's reason when the same text stands in a row the lowering keeps)
FORMS = {
    'arrow': ('On{} -> Off{}', 'expected : Type'),
    'or': ('On{} || Off{}', 'a defined name'),
    'amp': ('a & a', 'a defined name'),
    'diamond': ('a <> a', 'a declared constructor'),
    'chain': ('h(a)(a)', 'a function type'),
    'index': ('a[0n]', 'a defined name'),
    'bang': ('h!(a)', None),
    'plus0': ('+x0', 'a bound variable'),
    'plus0-paren': ('+(a)', 'a bound variable'),
    'lam': ('a => a', 'expected : Flag'),
}
MORE = {
    'and': ('On{} && Off{}', 'a defined name'), 'bar': ('a | a', 'a defined name'),
    'lt': ('a < a', 'a type for this operator'), 'le': ('a <= a', 'a type for this operator'),
    'gt': ('a > a', 'a type for this operator'), 'ge': ('a >= a', 'a type for this operator'),
    'append': ('a ++ a', 'a defined name'), 'min': ('a <&> a', 'expected : Quant'),
    'dor': ('a .|. a', 'a type for this operator'), 'dxor': ('a .^. a', 'a type for this operator'),
    'dand': ('a .&. a', 'a type for this operator'), 'shl': ('a << a', 'a type for this operator'),
    'shr': ('a >> a', 'a type for this operator'), 'add': ('a + a', 'a type for this operator'),
    'sub': ('a - a', 'a type for this operator'), 'mul': ('a * a', 'a type for this operator'),
    'div': ('a / a', 'a type for this operator'), 'mod': ('a % a', 'a type for this operator'),
    'set': ('a[0n] <- a', 'a defined name'), 'call-op': ('h(a) + a', 'a type for this operator'),
    'call-ctor': ('On{}(a)', 'an annotated term'), 'lt-glue': ('a<a', 'a type for this operator'),
    'plus0-space': ('+ x0', 'a bound variable'), 'plus0-op': ('+x0 || a', 'a defined name'),
}


def term(site, body):
    """A def whose row `case Off{} Off{}` (or `Off{}`) is discarded, or kept, with `body` at `site`."""
    def two(arm):
        return f'def f(a: Flag, b: Flag) -> Flag:\n  match a b:\n    case _ _: On{{}}\n    case Off{{}} Off{{}}:{arm}\n\ndef main() -> Flag:\n  f(On{{}}, On{{}})\n'
    if site == 'dead':
        return TERM_PRE + two(f' {body}')
    if site == 'dead-own':
        return TERM_PRE + two(f'\n      {body}')
    if site == 'dead-let':
        return TERM_PRE + two(f'\n      u : Flag = {body}\n      On{{}}')
    if site == 'dead-arg':
        return TERM_PRE + two(f' h({body})')
    if site == 'dead-single':
        return TERM_PRE + f'def f(a: Flag) -> Flag:\n  match a:\n    case _: On{{}}\n    case Off{{}}: {body}\n\ndef main() -> Flag:\n  f(On{{}})\n'
    if site == 'live':
        return TERM_PRE + f'def f(a: Flag, b: Flag) -> Flag:\n  match a b:\n    case Off{{}} Off{{}}: {body}\n    case _ _: On{{}}\n\ndef main() -> Flag:\n  f(On{{}}, On{{}})\n'
    raise KeyError(site)


def stem(form, site):
    return f'suffix-{form}-{site}'


# The seed accepts every discarded body below. After a let's value a `+` or `-` reads as a statement on
# the let's line, an existing outcome; after an argument a `(` reads as another argument; every other
# suffix is a term the parser leaves unread.
STATEMENT = {'arrow', 'append', 'add', 'sub', 'call-op'}
ARGUMENT = {'chain', 'call-ctor'}


def dead_outcome(form, site):
    if site == 'dead-let' and form in STATEMENT:
        return unsupported('same-line-statement')
    if site == 'dead-arg' and form in ARGUMENT:
        return unsupported('argument-whitespace')
    return unsupported('term-form')


def dead_group(site, forms):
    by_outcome = {}
    for form in forms:
        by_outcome.setdefault(json.dumps(dead_outcome(form, site), sort_keys=True), []).append(form)
    for label, members in by_outcome.items():
        outcome = json.loads(label)
        suffix = outcome['diagnostic'].split('\t')[2]
        group(f'suffix-{site}-{suffix}', outcome, None, *[(stem(form, site), term(site, {**FORMS, **MORE}[form][0])) for form in members])


for site in ('dead', 'dead-own', 'dead-single', 'dead-let', 'dead-arg'):
    dead_group(site, list(FORMS) + (list(MORE) if site == 'dead' else []))
# The same text in a row the lowering keeps: the seed rejects it for a reason the parser cannot see (an
# undefined operator target, a type), so the program is unsupported, not invalid. An offload `h!(a)` is
# accepted there.
group('suffix-live', unsupported('term-form'), None,
      *[(stem(form, 'live'), term('live', text), reason) for form, (text, reason) in FORMS.items() if reason])
group('suffix-live-accepted', unsupported('term-form'), None, (stem('bang', 'live'), term('live', FORMS['bang'][0])))
# A live row whose operator target the program defines: the seed accepts these.
DEFINED = {
    'or': ('def Bool.or(a: Flag, b: Flag) -> Flag:\n  match a:\n    case On{}: On{}\n    case Off{}: b\n\n', 'On{} || Off{}'),
    'amp': ('def Pair(a: Flag, b: Flag) -> Flag:\n  match a:\n    case On{}: On{}\n    case Off{}: b\n\n', 'a & a'),
}
group('suffix-live-defined', unsupported('term-form'), None,
      *[(f'suffix-{form}-defined', TERM_PRE + defs + term('live', body)[len(TERM_PRE):]) for form, (defs, body) in DEFINED.items()])
# What the parser still reads as invalid: nothing can continue the term, or the seed rejects it even unread.
CLOSED = {
    'eqeq': ('On{} == Off{}', "expected : 'def', 'type' or 'law'", 'end-of-body'),
    'ctor-arrow': ('On{} => a', 'expected : a lambda binder', 'end-of-body'),
    'closer': ('On{})', "expected : 'def', 'type' or 'law'", 'end-of-body'),
    'comma': ('a, a', "expected : 'def', 'type' or 'law'", 'end-of-body'),
    'marker-plus': ('a +b', "expected : '='", 'end-of-body'),
    'marker-minus': ('a -b', "expected : 'def', 'type' or 'law'", 'end-of-body'),
    'dot': ('a . a', "expected : 'def', 'type' or 'law'", 'end-of-body'),
    'question': ('a ? a', "expected : 'def', 'type' or 'law'", 'end-of-body'),
    'bang': ('a ! a', "expected : 'def', 'type' or 'law'", 'end-of-body'),
    'minus0': ('-x0', "expected : '='", 'expected-='),
    'plus0-name': ('+x0 y', "expected : '='", 'expected-='),
    'plus0-call': ('+h(a)', 'expected : a quantified datatype after +', 'expected-='),
}
for label, (body, reason, code) in CLOSED.items():
    group(f'suffix-closed-{label}', invalid(code), reason, (f'suffix-ctl-{label}', term('dead', body)))
# A line that starts with an operator, `!(` or `=>` continues the term before it, wherever the line stands:
# at the margin, left of the arms, at a let's column or below it. A `(` or `[` at a line's start does not.
CONTINUES = {
    'cont-margin': 'case Off{} Off{}: x0\n|| a\n',
    'cont-left': 'case Off{} Off{}: x0\n  || a\n',
    'cont-let-margin': 'case Off{} Off{}:\n      u : Flag = x0\n|| a\n      On{}\n',
    'cont-let-deeper': 'case Off{} Off{}:\n      u : Flag = x0\n          || a\n      On{}\n',
    'cont-bang-margin': 'case Off{} Off{}: x0\n!(a)\n',
    'cont-let-le': 'case Off{} Off{}:\n      u : Flag = x0\n      <= a\n      On{}\n',
    'cont-let-ge': 'case Off{} Off{}:\n      u : Flag = x0 # c\n      >= a\n      On{}\n',
    'cont-lambda-let': 'case Off{} Off{}:\n      u : Flag = a\n            => a\n      On{}\n',
}


def continues(rows):
    return (TERM_PRE + f'def f(a: Flag, b: Flag) -> Flag:\n  match a b:\n    case _ _: On{{}}\n    {rows}'
            + '\ndef main() -> Flag:\n  f(On{}, On{})\n')


group('suffix-continues', unsupported('term-form'), None, *[(f'suffix-{name}', continues(rows)) for name, rows in CONTINUES.items()])
group('suffix-continues-arrow', unsupported('line-break'), None, ('suffix-cont-arrow-margin', continues('case Off{} Off{}: x0\n=> a\n')))
group('suffix-continues-index', invalid('declaration-name'), "expected : 'def', 'type' or 'law'",
      ('suffix-ctl-index-margin', continues('case Off{} Off{}: x0\n[0n]\n')))
# A `+` marker that ends its line: the seed skips the break and reads the promoted term that follows, `+(a)` or `+ +a`.
# An erased `-` marker wants a name: the seed rejects it either way.
MARKER_BREAKS = {
    'plus-break-paren': 'case Off{} Off{}: +\n      (a)\n',
    'plus-break-paren-glued': 'case Off{} Off{}:+\n      (a)\n',
    'plus-break-paren-own': 'case Off{} Off{}:\n      +\n      (a)\n',
    'plus-break-paren-comment': 'case Off{} Off{}: + # c\n      (a)\n',
    'plus-break-paren-blank': 'case Off{} Off{}: +\n\n      (a)\n',
}
group('suffix-marker-break', unsupported('term-form'), None, *[(f'suffix-{name}', continues(rows)) for name, rows in MARKER_BREAKS.items()])
group('suffix-marker-break-plus', unsupported('repeated-promotion'), None, ('suffix-plus-break-plus', continues('case Off{} Off{}: +\n      +a\n')))
group('suffix-marker-break-erased', invalid('binding-name'), 'expected : a name',
      ('suffix-ctl-minus-break-paren', continues('case Off{} Off{}:\n      -\n      (a)\n')),
      ('suffix-ctl-minus-inline-paren', continues('case Off{} Off{}: - (a)\n')))
# A let's value on the line after its `=` starts at any term, not only a name: the seed skips the break (a live let
# too: `u : Flag =`, then `(a)`); a token that starts no term (a closer, a colon, a keyword) is rejected there.
LET_BREAKS = {
    'let-break-plus': 'u : Flag =\n       +x0\n      On{}', 'let-break-paren': 'u : Flag =\n       (a)\n      On{}',
    'let-break-numeral': 'u : Flag =\n       0n\n      On{}', 'let-break-comment': 'u : Flag = # c\n       +x0\n      On{}',
    'let-break-untyped': 'u =\n       +x0\n      On{}', 'let-break-list': 'u : Flag =\n       [a]\n      On{}',
    'let-break-name': 'u : Flag =\n       a\n      On{}',
}
group('suffix-let-break', unsupported('line-break'), None,
      *[(f'suffix-{name}', continues(f'case Off{{}} Off{{}}:\n      {body}\n')) for name, body in LET_BREAKS.items()],
      ('suffix-let-break-live', TERM_PRE + 'def f(a: Flag) -> Flag:\n  u : Flag =\n    (a)\n  u\n\ndef main() -> Flag:\n  f(On{})\n'))
group('suffix-let-break-closed', invalid('expected-term'), 'expected : a term',
      *[(f'suffix-ctl-let-break-{name}', continues(f'case Off{{}} Off{{}}:\n      u : Flag =\n       {token}\n      On{{}}\n'))
        for name, token in (('closer', ')'), ('colon', ':'))])
group('suffix-plain', ACCEPTED, None, ('suffix-ctl-plain', term('dead', 'On{}')), ('suffix-ctl-variable', term('dead', 'a')),
      ('suffix-ctl-call', term('dead', 'h(a)')))


def cases():
    """Every fixture: (name, group, source, Knot outcome, seed reason)."""
    seen, out = set(), []
    for name, (knot, reason, items) in GROUPS.items():
        for item in items:
            stem_, source = item[:2]
            assert stem_ not in seen, stem_
            seen.add(stem_)
            out.append((stem_, name, source, knot, item[2] if len(item) > 2 else reason))
    return out


def direct(path, rejected=False):
    """The seed on the fixture alone: an Unsupported fixture has no Knot value to compare.
    `rejected` allows the seed's syntax or type error."""
    source = path.read_text()
    command = ['bun', oracle.SEED, str(path.relative_to(oracle.ROOT))]
    main = {'command': command, **oracle.run(command)}
    assert (main['exit'] == 0 and not main['stderr']) or (rejected and main['exit'] == 1 and main['stderr'].startswith('Error:')), main
    return {'name': path.stem, 'file': str(path.relative_to(oracle.ROOT)), 'sha256': oracle.sha256(path),
            'fields': any(not nullary for _, _, cs in oracle.declarations(source)[0] for _, nullary in cs),
            'seed': main, 'calls': []}


def observe(path, group_name, knot, reason):
    # A stated reason with an Unsupported outcome marks a program the seed rejects and Knot cannot read.
    lax = knot['exit'] == 3 and bool(reason)
    case = direct(path, lax) if knot['exit'] == 3 else review_seed.observe(path)
    case['finding'] = group_name
    accepted = case['seed']['exit'] == 0
    assert lax or accepted == (knot['exit'] != 2), (path.name, 'seed acceptance and reviewed Knot outcome differ')
    if reason:
        assert reason in case['seed']['stderr'], (path.name, 'seed rejects for another reason', case['seed']['stderr'][:200])
    case['knot'] = knot
    return case


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--emit', action='store_true', help='write the fixtures from the templates')
    args.add_argument('--write', action='store_true')
    options = args.parse_args()
    table = {stem_: (name, source, knot, reason) for stem_, name, source, knot, reason in cases()}
    if options.emit:
        FIXTURES.mkdir(exist_ok=True)
        for old in FIXTURES.glob('*.bend'):
            if old.stem not in table:
                old.unlink()
        for stem_, (name, source, knot, reason) in table.items():
            (FIXTURES / f'{stem_}.bend').write_text(source)
        print(f'Emitted {len(table)} fixtures')
        return
    files = sorted(FIXTURES.glob('*.bend'))
    assert sorted(p.stem for p in files) == sorted(table), ('unreviewed or missing fixtures',
        sorted(set(p.stem for p in files) ^ set(table)))
    for path in files:
        assert path.read_text() == table[path.stem][1], (path.name, 'fixture differs from its template')
    with ThreadPoolExecutor(6) as pool:
        observed = list(pool.map(lambda p: observe(p, table[p.stem][0], table[p.stem][2], table[p.stem][3]), files))
    result = {'basis': 'The round-12 review findings (a `+` on a field of the first row of a constructor split, term suffixes '
                       'and `+name` terms in rows the lowering discards) as programs generated from templates, with their '
                       'controls, frozen with the pinned seed before the repairs.',
              'seed': oracle.environment()[0], 'fixtures': observed}
    if options.write:
        MANIFEST.write_text(json.dumps(result, indent=2) + '\n')
    else:
        assert result == json.loads(MANIFEST.read_text()), 'round-12 seed observations changed'
    print(f"Round-12 seed: {len(result['fixtures'])} fixtures, "
          f"{sum(len(c['calls']) for c in result['fixtures'])} calls; no differences")


if __name__ == '__main__':
    main()
