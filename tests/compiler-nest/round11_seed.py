#!/usr/bin/env python3
"""Replay round-11 seed observations. --emit writes the fixtures; --write is only for the pre-fix freeze.

The fixtures are generated here from small templates, so each reviewed group states its
shape once. Knot outcomes are literal review, keyed by group; the seed decides only
acceptance and, for a rejected group, must reject for the stated reason. The seed
(`bend2/bend.ts`) reads a whole book before it checks anything:

- `parse_body` parses every row and `parse_patt` validates each pattern (a declared
  constructor, its field count, a binder that is no constructor, a pattern count equal to
  the scrutinee count) whether or not the row can be selected. A row's body is only
  checked where the lowering keeps it: a type error, an unbound name, a computed scrutinee
  or an unknown annotation inside a shadowed row is accepted.
- `+X` reads as a quantified datatype when X is a datatype declared earlier in the file, and
  fails; later or unrelated names are promoted binders.
- One namespace: a binder shadows a datatype of its name in every type written after it
  (an annotation, a later parameter type, the result, a later field type).
- `parse_terms` reads any term as the next column of a row, so a Nat literal there is a
  pattern (`lit_step`); a U32, hex or fractional literal is not.
- A statement or `case` sits at any column; a let may break before its `:`.

The reviewed Knot outcomes are: `Invalid check` with the code the live path already uses for a
dead nested match; `datatype-pattern-binder` for a promoted datatype; `type-shadowed` for a
hidden type name; `Unsupported parse` for a numeral column and for the layouts the parser
does not model (a case left of its match, a statement or marked body at another column, a
let split before its `:`).
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import regen as oracle
import review_seed

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'round11-expectations.json'
FIXTURES = HERE / 'round11-fixtures'
ACCEPTED = {'exit': 0, 'outcome': 'Accepted'}


def check(code):
    return {'exit': 2, 'diagnostic': f'Invalid\tcheck\t{code}\t'}


def unsupported(code):
    return {'exit': 3, 'diagnostic': f'Unsupported\tparse\t{code}\t'}


PRE = '''type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Opt is Data:
  None{}
  Some{v: Flag}

type Tp is Type:
  Tp{x: Flag}

type Pr is Type:
  Pr{l: Flag, r: Flag}

def h(a: Flag) -> Flag:
  a

'''
GROUPS = {}   # group -> (Knot outcome, seed reason or None, [(name, source)])


def group(name, knot, reason, *cases):
    assert name not in GROUPS, name
    GROUPS[name] = (knot, reason, list(cases))


def main_of(args, result='Flag'):
    return f'def main() -> {result}:\n  f({args})\n'


# --- Finding 1: a nested match inside a row the lowering discards is audited like any other.
# Bad nested rows: kind -> (pattern, seed reason, Knot code).
BAD = {
    'unknown': ('Nope{}', 'a declared constructor (unknown: Nope)', 'unknown-constructor'),
    'arity-up': ('On{x}', 'a On pattern with 0 fields', 'pattern-arity'),
    'arity-down': ('Some{}', 'a Some pattern with 1 field', 'pattern-arity'),
    'bare': ('On', 'a braced constructor pattern', 'constructor-pattern-binder'),
    'call': ('h(x)', 'a pattern (a binder or a constructor)', 'pattern-form'),
    'count-up': ('On{} On{}', 'patterns (one per scrutinee)', 'pattern-arity'),
    'plus-dtype': ('+Flag', 'a quantified datatype after +', 'datatype-pattern-binder'),
    'plus-ctor': ('+On', 'a braced constructor pattern', 'constructor-pattern-binder'),
    'deep-unknown': ('Some{Nope{}}', 'a declared constructor (unknown: Nope)', 'unknown-constructor'),
    'deep-arity': ('Some{On{x}}', 'a On pattern with 0 fields', 'pattern-arity'),
}
GOOD = {'var': 'x', 'ctor': 'On{}'}


def dead(row):
    """Shape -> source whose nested match has the first row `row`; the outer row holding it is unreachable."""
    return {
        # the reviewer's shape: a wildcard row first, so `On{}` is dead
        'single': f'''def f(a: Flag) -> Flag:
  match a:
    case _: Off{{}}
    case On{{}}:
      match a:
        case {row}: On{{}}
        case _: Off{{}}

''' + main_of('On{}'),
        # a duplicated constructor row
        'dup': f'''def f(a: Flag) -> Flag:
  match a:
    case On{{}}: Off{{}}
    case On{{}}:
      match a:
        case {row}: On{{}}
        case _: Off{{}}
    case Off{{}}: On{{}}

''' + main_of('On{}'),
        # the outer match has two scrutinee columns
        'multi': f'''def f(a: Flag, b: Flag) -> Flag:
  match a b:
    case _ _: Off{{}}
    case On{{}} _:
      match a:
        case {row}: On{{}}
        case _: Off{{}}

''' + main_of('On{}, Off{}'),
        # two matches below the dead row
        'deep': f'''def f(a: Flag) -> Flag:
  match a:
    case _: Off{{}}
    case On{{}}:
      match a:
        case _: Off{{}}
        case On{{}}:
          match a:
            case {row}: On{{}}
            case _: Off{{}}

''' + main_of('On{}'),
        # a let ahead of the nested match
        'let': f'''def f(a: Flag) -> Flag:
  match a:
    case _: Off{{}}
    case On{{}}:
      u : Flag = a
      match a:
        case {row}: On{{}}
        case _: Off{{}}

''' + main_of('On{}'),
        # a fresh field is scrutinised in the dead row
        'field': f'''def f(p: Opt) -> Flag:
  match p:
    case _: Off{{}}
    case Some{{v}}:
      match v:
        case {row}: On{{}}
        case _: Off{{}}
    case None{{}}: Off{{}}

''' + main_of('Some{On{}}'),
    }


def live(row):
    """The same row in a body the lowering keeps: the seed and Knot agree already."""
    return f'''def f(p: Opt) -> Flag:
  match p:
    case Some{{v}}:
      match v:
        case {row}: On{{}}
        case _: Off{{}}
    case _: Off{{}}

''' + main_of('Some{On{}}')


for kind, (row, reason, code) in BAD.items():
    group(f'dead-{kind}', check(code), reason,
          *[(f'dead-{shape}-{kind}', PRE + source) for shape, source in dead(row).items()],
          (f'dead-live-{kind}', PRE + live(row)))
group('dead-ok', ACCEPTED, None,
      *[(f'dead-{shape}-ok-{name}', PRE + source) for name, row in GOOD.items() for shape, source in dead(row).items()])
# A nested match of two scrutinee columns whose row has too few or too many patterns.
WIDE = '''def f(a: Flag, b: Flag) -> Flag:
  match a b:
    case _ _: Off{{}}
    case On{{}} _:
      match a b:
        case {row}: On{{}}
        case _ _: Off{{}}

'''
WIDE_MAIN = main_of('On{}, Off{}')
group('dead-wide', check('pattern-arity'), 'patterns (one per scrutinee)',
      ('dead-wide-short', PRE + WIDE.format(row='On{}') + WIDE_MAIN),
      ('dead-wide-long', PRE + WIDE.format(row='On{} On{} On{}') + WIDE_MAIN))
group('dead-wide-ok', ACCEPTED, None, ('dead-wide-ok', PRE + WIDE.format(row='_ x') + WIDE_MAIN))
# A shadowed row of a reached nested match, and the outer row's own pattern.
INNER = '''def f(p: Opt) -> Flag:
  match p:
    case Some{{v}}:
      match v:
        case _: Off{{}}
        case {row}: On{{}}
    case _: Off{{}}

'''
OUTER = '''def f(a: Flag) -> Flag:
  match a:
    case _: Off{{}}
    case {row}: On{{}}

'''
for kind in ('unknown', 'arity-up', 'bare'):
    row, reason, code = BAD[kind]
    group(f'dead-edge-{kind}', check(code), reason,
          (f'dead-inner-{kind}', PRE + INNER.format(row=row) + main_of('Some{On{}}')),
          (f'dead-outer-{kind}', PRE + OUTER.format(row=row) + main_of('On{}')))
# Seed-accepted contents of a discarded body: only patterns are read up front.
LAX = '''def f(a: Flag) -> Flag:
  match a:
    case _: Off{{}}
    case On{{}}:
{body}

'''
LAX_MAIN = main_of('On{}')
group('dead-lax', ACCEPTED, None,
      *[(f'dead-lax-{name}', PRE + LAX.format(body=body) + LAX_MAIN) for name, body in (
          ('type-error', '      Some{On{}}'), ('unbound-name', '      zzz'),
          ('unbound-scrutinee', '      match zzz:\n        case _: On{}'),
          ('computed-scrutinee', '      match h(a):\n        case _: On{}'),
          ('unknown-annotation', '      y : Nope = On{}\n      y'),
          ('erased-live', '      -y : Flag = On{}\n      y'),
          ('shadowed-annotation', '      Flag = a\n      y : Flag = On{}\n      y'),
          ('call-arity', '      h(a, a)'))])

# --- Finding 2: `+X` names no datatype declared earlier in the file.
PLUS = {
    'row': ('def f(a: Flag) -> Flag:\n  match a:\n    case +{n}: On{{}}\n\n', 'On{}'),
    'row2-second': ('def f(a: Flag, b: Flag) -> Flag:\n  match a b:\n    case _ +{n}: On{{}}\n\n', 'On{}, On{}'),
    'row2-first': ('def f(a: Flag, b: Flag) -> Flag:\n  match a b:\n    case +{n} _: On{{}}\n\n', 'On{}, On{}'),
    'row2-third': ('def f(a: Flag, b: Flag, c: Flag) -> Flag:\n  match a b c:\n    case _ _ +{n}: On{{}}\n\n', 'On{}, On{}, On{}'),
    'field': ('def f(p: Pr) -> Flag:\n  match p:\n    case Pr{{+{n}, _}}: On{{}}\n\n', 'Pr{On{}, On{}}'),
    'field-second': ('def f(p: Pr) -> Flag:\n  match p:\n    case Pr{{_, +{n}}}: On{{}}\n\n', 'Pr{On{}, On{}}'),
    'nested': ('def f(p: Opt) -> Flag:\n  match p:\n    case Some{{+{n}}}: On{{}}\n    case _: Off{{}}\n\n', 'Some{On{}}'),
    'default': ('def f(a: Flag) -> Flag:\n  match a:\n    case On{{}}: Off{{}}\n    case +{n}: On{{}}\n\n', 'On{}'),
    'let': ('def f(a: Flag) -> Flag:\n  +{n} = a\n  On{{}}\n\n', 'On{}'),
    'let-typed': ('def f(a: Flag) -> Flag:\n  +{n} : Flag = a\n  On{{}}\n\n', 'On{}'),
    'let-arm': ('def f(a: Flag) -> Flag:\n  match a:\n    case _:\n      +{n} = a\n      On{{}}\n\n', 'On{}'),
}


def plus(shape, name):
    text, args = PLUS[shape]
    return PRE + text.format(n=name) + main_of(args)


group('plusd-datatype', check('datatype-pattern-binder'), 'a quantified datatype after +',
      *[(f'plusd-{shape}-flag', plus(shape, 'Flag')) for shape in PLUS],
      *[(f'plusd-{shape}-color', plus(shape, 'Color')) for shape in ('row', 'row2-second', 'field', 'nested', 'let')],
      ('plusd-row-opt', plus('row', 'Opt')))
# A name that is also a constructor keeps the constructor rule (the seed rejects both ways).
group('plusd-constructor', check('constructor-pattern-binder'), None,
      ('plusd-row-both', plus('row', 'Tp')), ('plusd-row-ctor', plus('row', 'On')),
      ('plusd-row2-both', plus('row2-second', 'Tp')), ('plusd-field-ctor', plus('field', 'Red')))
# Not datatypes at that point of the file, or not datatypes at all: promoted binders.
ORDER = '''def f(a: Flag) -> Flag:
  match a:
    case +Later: On{{}}

type Later is Data:
  L0{{}}

def g(a: Flag) -> Flag:
  match a:
    case {g}: On{{}}

'''
group('plusd-ok', ACCEPTED, None,
      ('plusd-order-before', PRE + ORDER.format(g='+q') + main_of('On{}')),
      ('plusd-ctl-later-let', PRE + 'def f(a: Flag) -> Flag:\n  +Later = a\n  On{}\n\ntype Later is Data:\n  L0{}\n\n' + main_of('On{}')),
      *[(f'plusd-ctl-{label}', plus('row', name)) for label, name in
        (('function', 'h'), ('undeclared', 'Nat'), ('base-name', 'String'), ('plain', 'q'), ('underscore-name', '_x'))],
      *[(f'plusd-ctl-{shape}', plus(shape, 'q')) for shape in ('row2-second', 'field', 'nested', 'let')],
      ('plusd-ctl-erased-let-datatype', PRE + 'def f(a: Flag) -> Flag:\n  -Flag = a\n  On{}\n\n' + main_of('On{}')),
      ('plusd-ctl-bare-datatype', PRE + 'def f(a: Flag) -> Flag:\n  match a:\n    case Flag: On{}\n\n' + main_of('On{}')))
group('plusd-order-after', check('datatype-pattern-binder'), 'a quantified datatype after +',
      ('plusd-order-after', PRE + ORDER.format(g='+Later') + main_of('On{}')))

# --- Finding 3: a binder hides a datatype of its name from the types written after it.
SHADOW = {
    'row': ('def f(a: Flag) -> Flag:\n  match a:\n    case {n}:\n      y : {t} = {v}\n      {u}\n\n', 'On{}'),
    'row2-second': ('def f(a: Flag, b: Flag) -> Flag:\n  match a b:\n    case _ {n}:\n      y : {t} = {v}\n      {u}\n\n', 'On{}, On{}'),
    'row2-first': ('def f(a: Flag, b: Flag) -> Flag:\n  match a b:\n    case {n} _:\n      y : {t} = {v}\n      {u}\n\n', 'On{}, On{}'),
    'nested': ('def f(p: Opt) -> Flag:\n  match p:\n    case Some{{{n}}}:\n      y : {t} = {v}\n      {u}\n    case _: Off{{}}\n\n', 'Some{On{}}'),
    'field': ('def f(p: Pr) -> Flag:\n  match p:\n    case Pr{{{n}, _}}:\n      y : {t} = {v}\n      {u}\n\n', 'Pr{On{}, On{}}'),
    'let': ('def f(a: Flag) -> Flag:\n  {n} = a\n  y : {t} = {v}\n  {u}\n\n', 'On{}'),
    'let-typed': ('def f(a: Flag) -> Flag:\n  {n} : Flag = On{{}}\n  y : {t} = {v}\n  {u}\n\n', 'On{}'),
    'let-arm': ('def f(a: Flag) -> Flag:\n  match a:\n    case _:\n      {n} = a\n      y : {t} = {v}\n      {u}\n\n', 'On{}'),
    'erased': ('def f(a: Flag) -> Flag:\n  match a:\n    case {n}:\n      -y : {t} = {v}\n      On{{}}\n\n', 'On{}'),
    'param': ('def f({n}: Flag) -> Color:\n  y : {t} = {v}\n  Red{{}}\n\n', 'On{}'),
    'param-late': ('def f(b: Flag, {n}: Flag) -> Color:\n  y : {t} = {v}\n  Red{{}}\n\n', 'On{}, On{}'),
}


def shadow(shape, n='Flag', t='Flag', v='On{}', u='y'):
    text, args = SHADOW[shape]
    return PRE + text.format(n=n, t=t, v=v, u=u) + main_of(args, 'Color' if shape.startswith('param') else 'Flag')


group('shadow', check('type-shadowed'), 'expected : Type',
      *[(f'shadow-{shape}', shadow(shape)) for shape in SHADOW],
      *[(f'shadow-{shape}-color', shadow(shape, 'Color', 'Color', 'Red{}', 'h(On{})')) for shape in ('row', 'nested', 'let', 'param')])
# The signature and the type declarations: earlier parameters and fields hide a type name.
TAIL = 'def f(a: Flag) -> Flag:\n  a\n\n' + main_of('On{}')
group('shadow-signature', check('type-shadowed'), 'expected : Type',
      ('shadow-param-result', PRE + 'def f(Flag: Flag) -> Flag:\n  On{}\n\n' + main_of('On{}')),
      ('shadow-param-plus-result', PRE + 'def f(+Flag: Flag) -> Flag:\n  On{}\n\n' + main_of('On{}')),
      ('shadow-param-erased-result', PRE + 'def f(-Flag: Flag) -> Flag:\n  On{}\n\n' + main_of('On{}')),
      ('shadow-param-type', PRE + 'def f(Flag: Flag, x: Flag) -> Color:\n  Red{}\n\n' + main_of('On{}, On{}', 'Color')),
      ('shadow-param-type-third', PRE + 'def f(a: Flag, Flag: Flag, x: Flag) -> Color:\n  Red{}\n\n' + main_of('On{}, On{}, On{}', 'Color')),
      ('shadow-param-result-second', PRE + 'def f(a: Flag, Flag: Flag) -> Flag:\n  On{}\n\n' + main_of('On{}, On{}')),
      ('shadow-field-erased', PRE + 'type Q is Type:\n  Q{-Flag: Flag, y: Flag}\n\n' + TAIL))
group('shadow-fields', check('type-shadowed'), 'expected : Data',
      ('shadow-field-type', PRE + 'type Q is Data:\n  Q{Flag: Flag, y: Flag}\n\n' + TAIL),
      ('shadow-field-type-third', PRE + 'type Q is Data:\n  Q{a: Flag, Flag: Flag, b: Flag}\n\n' + TAIL))
group('shadow-ok', ACCEPTED, None,
      ('shadow-ctl-other-type', shadow('row', 'Flag', 'Color', 'Red{}', 'On{}')),
      ('shadow-ctl-plain-binder', shadow('row', 'q')),
      ('shadow-ctl-plain-let', shadow('let', 'q')),
      ('shadow-ctl-annotation-first', PRE + 'def f(a: Flag) -> Flag:\n  y : Flag = On{}\n  Flag = a\n  y\n\n' + main_of('On{}')),
      ('shadow-ctl-own-annotation', PRE + 'def f(a: Flag) -> Flag:\n  Flag : Flag = On{}\n  Flag\n\n' + main_of('On{}')),
      ('shadow-ctl-param-own-type', PRE + 'def f(a: Flag, Flag: Flag) -> Color:\n  Red{}\n\n' + main_of('On{}, On{}', 'Color')),
      ('shadow-ctl-param-other-type', PRE + 'def f(Flag: Flag) -> Color:\n  Red{}\n\n' + main_of('On{}', 'Color')),
      ('shadow-ctl-field-own-type', PRE + 'type Q is Data:\n  Q{Flag: Flag}\n  R{y: Flag}\n\n' + TAIL),
      ('shadow-ctl-row-scope-ends', PRE + '''def f(p: Pr) -> Flag:
  match p:
    case Pr{l, Flag}: Off{}
    case _:
      y : Flag = On{}
      y

''' + main_of('Pr{On{}, On{}}')),
      ('shadow-ctl-dead-body', PRE + '''def f(a: Flag) -> Flag:
  match a:
    case _: Off{}
    case On{}:
      Flag = a
      y : Flag = On{}
      y

''' + main_of('On{}')))
# A type declared after its use is still a datatype: the seed rejects the hidden name too.
group('shadow-later-type', check('type-shadowed'), 'expected : Type',
      ('shadow-later-type', 'def f(a: Later) -> Later:\n  match a:\n    case Later:\n      y : Later = L0{}\n      y\n\n'
       'type Later is Data:\n  L0{}\n\ndef main() -> Later:\n  f(L0{})\n'))

# --- Finding 5: a Nat literal opens a later column of a row. Knot has no literal patterns.
NAT = '''type Nat is Data:
  Zero{{}}
  Succ{{pred: Nat}}

def f(b: Flag, n: Nat) -> Flag:
  match b n:
    case {row}: On{{}}
    case _ _: Off{{}}

def probe(a: Flag, k: Flag) -> Flag:
  match k:
    case Off{{}}: f(a, Zero{{}})
    case On{{}}: f(a, Succ{{Zero{{}}}})

def main() -> Flag:
  probe(On{{}}, Off{{}})
'''
GAPS = {'space': ' ', 'spaces': '   ', 'newline': '\n      ', 'comment': ' # gap\n      ', 'comma': ', '}
LEFTS = {'wild': '_', 'var': 'x', 'ctor': 'On{}', 'promo': '+x'}
LITERALS = {'zero': '0n', 'two': '2n', 'ten': '10n', 'succ': '1n+m'}
group('nat-column', unsupported('term-form'), None,
      *[(f'nat-{left}-{gap}-{lit}', PRE + NAT.format(row=f'{LEFTS[left]}{GAPS[gap]}{LITERALS[lit]}'))
        for left in ('wild', 'ctor') for gap in ('space', 'newline', 'comment') for lit in ('zero', 'two', 'succ')],
      *[(f'nat-{left}-space-zero', PRE + NAT.format(row=f'{LEFTS[left]} 0n')) for left in ('var', 'promo')],
      ('nat-wild-spaces-ten', PRE + NAT.format(row='_   10n')),
      ('nat-wild-comma-zero', PRE + NAT.format(row='_, 0n')))
NAT3 = '''type Nat is Data:
  Zero{{}}
  Succ{{pred: Nat}}

def f(b: Flag, n: Nat, m: Nat) -> Flag:
  match b n m:
    case {row}: On{{}}
    case _ _ _: Off{{}}

def probe(a: Flag, k: Flag) -> Flag:
  match k:
    case Off{{}}: f(a, Zero{{}}, Succ{{Zero{{}}}})
    case On{{}}: f(a, Succ{{Zero{{}}}}, Zero{{}})

def main() -> Flag:
  probe(On{{}}, Off{{}})
'''
group('nat-column3', unsupported('term-form'), None,
      ('nat3-middle', PRE + NAT3.format(row='_ 0n _')), ('nat3-last', PRE + NAT3.format(row='_ _ 1n+m')),
      ('nat3-last-newline', PRE + NAT3.format(row='_ _\n      0n')), ('nat3-both', PRE + NAT3.format(row='_ 0n\n      1n+m')))
# Seed-accepted spellings of the same pattern that Knot reads.
group('nat-ok', ACCEPTED, None,
      ('nat-ctl-ctor', PRE + NAT.format(row='_ Zero{}')), ('nat-ctl-var', PRE + NAT.format(row='_ m')),
      ('nat-ctl-succ', PRE + NAT.format(row='_ Succ{m}')), ('nat-ctl-two', PRE + NAT.format(row='x _')),
      ('nat-ctl-comma', PRE + NAT.format(row='_, Zero{}')))
# A literal the row's later column already read as Unsupported: first column, nested field.
group('nat-first', unsupported('term-form'), None,
      ('nat-first', PRE + NAT.replace('match b n:', 'match n b:').replace('def f(b: Flag, n: Nat)', 'def f(n: Nat, b: Flag)')
       .replace('f(a, Zero{{}})', 'f(Zero{{}}, a)').replace('f(a, Succ{{Zero{{}}}})', 'f(Succ{{Zero{{}}}}, a)').format(row='0n _')),
      ('nat-nested', PRE + NAT.format(row='_ Succ{0n}')))

# --- Finding 6: a row has one pattern per scrutinee and a constructor pattern its fields.
ROWS = '''def f(a: Flag, b: Flag) -> Flag:
  match a b:
    case On{{}} On{{}}: Off{{}}
{first}    case _ _: On{{}}
{last}
'''
group('arity-width', check('pattern-arity'), 'patterns (one per scrutinee)',
      ('arity-short-live', PRE + ROWS.format(first='    case Off{}: On{}\n', last='') + main_of('On{}, On{}')),
      ('arity-long-live', PRE + ROWS.format(first='    case Off{} On{} Off{}: On{}\n', last='') + main_of('On{}, On{}')),
      ('arity-short-dead', PRE + ROWS.format(first='', last='    case Off{}: On{}\n') + main_of('On{}, On{}')),
      ('arity-long-dead', PRE + ROWS.format(first='', last='    case Off{} On{} Off{}: On{}\n') + main_of('On{}, On{}')),
      ('arity-short-first', PRE + ROWS.format(first='', last='').replace('case On{} On{}:', 'case On{}:') + main_of('On{}, On{}')),
      ('arity-single-long', PRE + 'def f(a: Flag) -> Flag:\n  match a:\n    case On{} On{}: On{}\n    case _: Off{}\n\n' + main_of('On{}')),
      ('arity-single-long-dead', PRE + 'def f(a: Flag) -> Flag:\n  match a:\n    case _: Off{}\n    case On{} On{}: On{}\n\n' + main_of('On{}')),
      ('arity-triple-short', PRE + '''def f(a: Flag, b: Flag, c: Flag) -> Flag:
  match a b c:
    case _ _ _: On{}
    case On{} _: Off{}

''' + main_of('On{}, On{}, On{}')),
      ('arity-triple-long', PRE + '''def f(a: Flag, b: Flag, c: Flag) -> Flag:
  match a b c:
    case On{} _ _ _: Off{}
    case _ _ _: On{}

''' + main_of('On{}, On{}, On{}')))
FIELDS = '''type Bx is Type:
  Bx{p: Pr}

'''
CARRY = '''def f(p: Pr, c: Flag) -> Flag:
  match p c:
{first}    case _ _: On{{}}
{last}
'''
group('arity-fields', check('pattern-arity'), None,
      ('arity-ctor-less-live', PRE + CARRY.format(first='    case Pr{a} _: Off{}\n', last='') + main_of('Pr{On{}, On{}}, On{}')),
      ('arity-ctor-more-live', PRE + CARRY.format(first='    case Pr{a, b, c} _: Off{}\n', last='') + main_of('Pr{On{}, On{}}, On{}')),
      ('arity-ctor-less-dead', PRE + '''def f(p: Pr, c: Flag) -> Flag:
  match p c:
    case Pr{a, b} _: On{}
    case Pr{a} _: Off{}

''' + main_of('Pr{On{}, On{}}, On{}')),
      ('arity-ctor-more-dead', PRE + '''def f(p: Pr, c: Flag) -> Flag:
  match p c:
    case Pr{a, b} _: On{}
    case Pr{a, b, c} _: Off{}

''' + main_of('Pr{On{}, On{}}, On{}')),
      ('arity-field-less-live', PRE + FIELDS + 'def f(x: Bx) -> Flag:\n  match x:\n    case Bx{Pr{a}}: On{}\n    case _: Off{}\n\n' + main_of('Bx{Pr{On{}, On{}}}')),
      ('arity-field-more-live', PRE + FIELDS + 'def f(x: Bx) -> Flag:\n  match x:\n    case Bx{Pr{a, b, c}}: On{}\n    case _: Off{}\n\n' + main_of('Bx{Pr{On{}, On{}}}')),
      ('arity-field-less-dead', PRE + FIELDS + 'def f(x: Bx) -> Flag:\n  match x:\n    case Bx{Pr{a, b}}: On{}\n    case Bx{Pr{a}}: Off{}\n\n' + main_of('Bx{Pr{On{}, On{}}}')),
      ('arity-field-more-dead', PRE + FIELDS + 'def f(x: Bx) -> Flag:\n  match x:\n    case Bx{Pr{a, b}}: On{}\n    case Bx{Pr{a, b, c}}: Off{}\n\n' + main_of('Bx{Pr{On{}, On{}}}')),
      ('arity-outer-less-live', PRE + FIELDS + 'def f(x: Bx) -> Flag:\n  match x:\n    case Bx{}: On{}\n    case _: Off{}\n\n' + main_of('Bx{Pr{On{}, On{}}}')),
      ('arity-outer-more-dead', PRE + FIELDS + 'def f(x: Bx) -> Flag:\n  match x:\n    case _: Off{}\n    case Bx{a, b}: On{}\n\n' + main_of('Bx{Pr{On{}, On{}}}')),
      ('arity-flat-less', PRE + 'def f(p: Pr) -> Flag:\n  match p:\n    case Pr{a}: On{}\n\n' + main_of('Pr{On{}, On{}}')),
      ('arity-flat-more', PRE + 'def f(p: Pr) -> Flag:\n  match p:\n    case Pr{a, b, c}: On{}\n\n' + main_of('Pr{On{}, On{}}')))
group('arity-ok', ACCEPTED, None,
      ('arity-ctl-widths', PRE + ROWS.format(first='    case Off{} _: On{}\n', last='') + main_of('On{}, On{}')),
      ('arity-ctl-fields', PRE + FIELDS + 'def f(x: Bx) -> Flag:\n  match x:\n    case Bx{Pr{a, b}}: a\n    case _: Off{}\n\n' + main_of('Bx{Pr{On{}, On{}}}')),
      ('arity-ctl-dead-fields', PRE + FIELDS + 'def f(x: Bx) -> Flag:\n  match x:\n    case Bx{Pr{a, b}}: On{}\n    case Bx{Pr{a, b}}: Off{}\n\n' + main_of('Bx{Pr{On{}, On{}}}')))

# --- Finding 4: layouts the seed reads and the parser does not model are Unsupported, never Invalid.
LAYOUT = {
    # one row, the nested constructor patterns apart, then a default row
    'canonical': 'match {cols}:\n    case {pat}:\n      F1{{}}\n    case {dflt}:\n      F0{{}}\n',
    'case-at-match': 'match {cols}:\n  case {pat}:\n    F1{{}}\n  case {dflt}:\n    F0{{}}\n',
    'case-first-at-match': 'match {cols}:\n  case {pat}:\n    F1{{}}\n    case {dflt}:\n    F0{{}}\n',
    'case-left-of-match': 'match {cols}:\n case {pat}:\n   F1{{}}\n case {dflt}:\n   F0{{}}\n',
    'later-deeper': 'match {cols}:\n    case {pat}:\n      v : F = F1{{}}\n        v\n    case {dflt}:\n      F0{{}}\n',
    'later-shallower': 'match {cols}:\n    case {pat}:\n      v : F = F1{{}}\n     v\n    case {dflt}:\n      F0{{}}\n',
    'later-at-case': 'match {cols}:\n    case {pat}:\n      v : F = F1{{}}\n    v\n    case {dflt}:\n      F0{{}}\n',
    'later-untyped': 'match {cols}:\n    case {pat}:\n      v = h(a)\n        v\n    case {dflt}:\n      F0{{}}\n',
    'plus-body': 'match {cols}:\n    case {pat}:\n    +v : F = F1{{}}\n      v\n    case {dflt}:\n      F0{{}}\n',
    'minus-body': 'match {cols}:\n    case {pat}:\n    -v : F = F1{{}}\n      F0{{}}\n    case {dflt}:\n      F0{{}}\n',
    'plus-body-shallow': 'match {cols}:\n    case {pat}:\n  +v : F = F1{{}}\n      v\n    case {dflt}:\n      F0{{}}\n',
    'split-colon-plus': 'match {cols}:\n    case {pat}:\n      +u\n        : F = F1{{}}\n      u\n    case {dflt}:\n      F0{{}}\n',
    'split-colon-erased': 'match {cols}:\n    case {pat}:\n      -u\n        : F = F1{{}}\n      F0{{}}\n    case {dflt}:\n      F0{{}}\n',
    'split-colon-comment': 'match {cols}:\n    case {pat}:\n      +u # gap\n        : F = F1{{}}\n      u\n    case {dflt}:\n      F0{{}}\n',
}
LAYOUT_OUTCOME = {'canonical': ACCEPTED, 'case-at-match': unsupported('pattern-or-indentation'),
                  'case-first-at-match': unsupported('pattern-or-indentation'),
                  'case-left-of-match': unsupported('pattern-or-indentation'),
                  'later-deeper': unsupported('body-indentation'), 'later-shallower': unsupported('body-indentation'),
                  'later-at-case': unsupported('body-indentation'), 'later-untyped': unsupported('body-indentation'),
                  'plus-body': unsupported('body-indentation'), 'minus-body': unsupported('body-indentation'),
                  'plus-body-shallow': unsupported('body-indentation'),
                  'split-colon-plus': unsupported('line-break'), 'split-colon-erased': unsupported('line-break'),
                  'split-colon-comment': unsupported('line-break')}
CONTEXTS = {'single': ('def f(a: Flag) -> Flag:\n  ', 'a', 'On{}', '_', 'On{}'),
            'multi': ('def f(a: Flag, b: Flag) -> Flag:\n  ', 'a b', 'On{} On{}', '_ _', 'On{}, On{}')}


def layout(shape, context):
    head, cols, pat, dflt, args = CONTEXTS[context]
    body = LAYOUT[shape].format(cols=cols, pat=pat, dflt=dflt).replace('F1{}', 'On{}').replace('F0{}', 'Off{}').replace(': F =', ': Flag =')
    return PRE + head + body + '\n' + main_of(args)


for shape, outcome in LAYOUT_OUTCOME.items():
    group(f'layout-{shape}', outcome, None, *[(f'layout-{shape}-{context}', layout(shape, context)) for context in CONTEXTS])
# A nested match as an arm's body at the case column: only a fresh field can be matched.
NESTED = '''def f(p: Opt, b: Flag) -> Flag:
  match p b:
    case Some{v} _:
    match v:
      case _: On{}
    case _ _: Off{}

''' + main_of('Some{On{}}, On{}')
group('layout-match-body', unsupported('body-indentation'), None, ('layout-match-body-multi', PRE + NESTED),
      ('layout-match-body-single', PRE + NESTED.replace('match p b:', 'match p:').replace('Some{v} _', 'Some{v}').replace('case _ _:', 'case _:')
       .replace('f(p: Opt, b: Flag)', 'f(p: Opt)').replace('Some{On{}}, On{}', 'Some{On{}}')))
# The seed rejects these: a let that has no body, and a `case` where a statement should be.
group('layout-invalid', {'exit': 2, 'diagnostic': 'Invalid\tparse\tbody-indentation\t'}, None,
      ('layout-ctl-def-after-let', PRE + 'def f(a: Flag) -> Flag:\n  u : Flag = a\n' + main_of('On{}')),
      ('layout-ctl-case-after-let', PRE + 'def f(a: Flag, b: Flag) -> Flag:\n  match a b:\n    case _ _:\n      u : Flag = a\n    case On{} _: Off{}\n\n' + main_of('On{}, On{}')),
      ('layout-ctl-punctuation-after-let', PRE + 'def f(a: Flag) -> Flag:\n  u : Flag = a\n    )\n\n' + main_of('On{}')))


def cases():
    """Every fixture: (name, group, source, Knot outcome, seed reason)."""
    seen, out = set(), []
    for name, (knot, reason, items) in GROUPS.items():
        for stem, source in items:
            assert stem not in seen, stem
            seen.add(stem)
            out.append((stem, name, source, knot, reason))
    return out


def direct(path):
    """The seed on the fixture alone: an Unsupported fixture has no Knot value to compare, and a Nat literal
    does not resolve through the import that wraps a call."""
    source = path.read_text()
    command = ['bun', oracle.SEED, str(path.relative_to(oracle.ROOT))]
    main = {'command': command, **oracle.run(command)}
    assert main['exit'] == 0 and not main['stderr'], main
    return {'name': path.stem, 'file': str(path.relative_to(oracle.ROOT)), 'sha256': oracle.sha256(path),
            'fields': any(not nullary for _, _, cs in oracle.declarations(source)[0] for _, nullary in cs),
            'seed': main, 'calls': []}


def observe(path, group_name, knot, reason):
    case = direct(path) if knot['exit'] == 3 else review_seed.observe(path)
    case['finding'] = group_name
    accepted = case['seed']['exit'] == 0
    assert accepted == (knot['exit'] != 2), (path.name, 'seed acceptance and reviewed Knot outcome differ')
    if reason:
        assert reason in case['seed']['stderr'], (path.name, 'seed rejects for another reason')
    case['knot'] = knot
    return case


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--emit', action='store_true', help='write the fixtures from the templates')
    args.add_argument('--write', action='store_true')
    options = args.parse_args()
    table = {stem: (name, source, knot, reason) for stem, name, source, knot, reason in cases()}
    if options.emit:
        FIXTURES.mkdir(exist_ok=True)
        for old in FIXTURES.glob('*.bend'):
            if old.stem not in table:
                old.unlink()
        for stem, (name, source, knot, reason) in table.items():
            (FIXTURES / f'{stem}.bend').write_text(source)
        print(f'Emitted {len(table)} fixtures')
        return
    files = sorted(FIXTURES.glob('*.bend'))
    assert sorted(p.stem for p in files) == sorted(table), ('unreviewed or missing fixtures',
        sorted(set(p.stem for p in files) ^ set(table)))
    for path in files:
        assert path.read_text() == table[path.stem][1], (path.name, 'fixture differs from its template')
    with ThreadPoolExecutor(6) as pool:
        observed = list(pool.map(lambda p: observe(p, table[p.stem][0], table[p.stem][2], table[p.stem][3]), files))
    result = {'basis': 'The round-10 review findings (dead-body nested matches, promoted datatypes, hidden type names, '
                       'Nat literal columns, multi-scrutinee layouts, pattern arities) as programs generated from '
                       'templates, with their controls, frozen with the pinned seed before the repairs.',
              'seed': oracle.environment()[0], 'fixtures': observed}
    if options.write:
        MANIFEST.write_text(json.dumps(result, indent=2) + '\n')
    else:
        assert result == json.loads(MANIFEST.read_text()), 'round-11 seed observations changed'
    print(f"Round-11 seed: {len(result['fixtures'])} fixtures, "
          f"{sum(len(c['calls']) for c in result['fixtures'])} calls; no differences")


if __name__ == '__main__':
    main()
