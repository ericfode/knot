#!/usr/bin/env python3
"""Replay round-13 seed observations. --emit writes the fixtures; --write is only for the pre-fix freeze.

Fixtures are generated from small templates, as in rounds 11 and 12: Knot outcomes are literal review, keyed
by group, and the seed decides only acceptance and, for a group it rejects, the reason. The pinned seed
(`bend2/bend.ts`) reads:

- `parse_term_ops` (finding 1): after a let's value it continues the term with any operator of its INFIX
  table, spaced or on the next line (`v = x` then `+ y` is one value `x + y`); `+` and `-` touching a name
  are markers, not operators. A statement cannot start at the `=` or `:` that follows the operand
  (`+ u : F = ..`), so that pair is a syntax error. A body the lowering discards is parsed and never
  checked; a live one needs a target the program defines, which is why the same text is rejected "for its
  type" in a live row.
- `parse_term_args` (finding 2): `x +y` and the glued `x+y` are the same tokens to the seed: `x`, then the
  promoted term `+y`; `?y` is a hole term. The seed rejects them in a live row for their scope or type
  (`expected : a bound variable`, `expected : Flag`) and accepts them in a discarded row. `@y`, `\\y`, `-y`
  and `$y` are no terms.
- `parse_body` (finding 3): an arm body, or a statement after a let, is any term at any column; a `(`, `[`,
  numeral or `?` starts one. A closer, a separator, a keyword, `!` and `@` start none.
- The whole program (finding 4): the seed compiles a match as a decision tree with shared defaults, so a
  wildcard row costs it nothing per column and it answers each program below in a few milliseconds.

The reviewed Knot outcomes (the coordinator's code ruling, D26): `Unsupported parse operator` for an operator
token that continues a term (`+`, `-`, `++`, `->`, `*`, `<=`, ... after a value, on the next line or glued);
`Unsupported parse term-form` for another unmodeled term form (a touching `+name` after an argument, a hole);
`Unsupported parse body-indentation` for a body or statement that starts with a term at another column;
`Invalid` only where the seed rejects for the reason the diagnostic names (the marker gap, `@`, backslash and
closers in an argument list, a closer, a keyword or `!` at a body's start); `Accepted` or
`Exhausted check budget` for the default-copy programs, which the seed accepts.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path

import regen as oracle
import review_seed

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'round13-expectations.json'
GRID = HERE / 'round13-grid.json'
FIXTURES = HERE / 'round13-fixtures'
ACCEPTED = {'exit': 0, 'outcome': 'Accepted'}
EXHAUSTED = {'exit': 4, 'diagnostic': 'Exhausted\tcheck\tbudget\t'}


def unsupported(code):
    return {'exit': 3, 'diagnostic': f'Unsupported\tparse\t{code}\t'}


def invalid(code):
    return {'exit': 2, 'diagnostic': f'Invalid\tparse\t{code}\t'}


GROUPS = {}   # group -> (Knot outcome, seed reason or None, [(name, source[, reason])])


def group(name, knot, reason, *cases):
    assert name not in GROUPS, name
    GROUPS[name] = (knot, reason, list(cases))


PRE = '''type Flag is Data:
  Off{}
  On{}

def h(a: Flag, b: Flag) -> Flag:
  a

def k(a: Flag) -> Flag:
  a

'''


def indented(text, width):
    return '\n'.join(' ' * width + line if line else line for line in text.split('\n'))


def dead2(body):
    """A discarded row of a two-scrutinee match holds `body` (lines at column 6)."""
    return (PRE + 'def f(x: Flag, y: Flag) -> Flag:\n  match x y:\n    case _ _: On{}\n    case Off{} Off{}:\n'
            + indented(body, 6) + '\n\ndef main() -> Flag:\n  f(On{}, Off{})\n')


def dead3(body):
    return (PRE + 'def f(x: Flag, y: Flag, z: Flag) -> Flag:\n  match x y z:\n    case _ _ _: On{}\n    case Off{} Off{} Off{}:\n'
            + indented(body, 6) + '\n\ndef main() -> Flag:\n  f(On{}, Off{}, Off{})\n')


def single(body):
    return (PRE + 'def f(x: Flag) -> Flag:\n  match x:\n    case _: On{}\n    case Off{}:\n'
            + indented(body, 6) + '\n\ndef main() -> Flag:\n  f(On{})\n')


def live2(body):
    """The first row of the match is kept by the lowering."""
    return (PRE + 'def f(x: Flag, y: Flag) -> Flag:\n  match x y:\n    case Off{} Off{}:\n'
            + indented(body, 6) + '\n    case _ _: On{}\n\ndef main() -> Flag:\n  f(On{}, Off{})\n')


def flat(body):
    return PRE + 'def f(x: Flag, y: Flag) -> Flag:\n' + indented(body, 2) + '\n\ndef main() -> Flag:\n  f(On{}, Off{})\n'


# --- Finding 1: a spaced operator at the start of the line after a let's value, in a discarded row.
# token -> the tokens as they stand at the line's start (the operand `y` follows after a space)
LINE_OPERATORS = {
    'plus': '+', 'minus': '-', 'plusplus': '++', 'arrow': '->', 'minusplus': '-+', 'star': '*', 'slash': '/',
    'percent': '%', 'lt': '<', 'gt': '>', 'le': '<=', 'ge': '>=', 'diamond': '<>', 'amp': '&', 'bar': '|',
    'and': '&&', 'or': '||', 'shl': '<<', 'shr': '>>', 'dor': '.|.', 'dxor': '.^.', 'dand': '.&.', 'min': '<&>',
}
group('letop', unsupported('operator'), None,
      *[(f'letop-{name}-dead2', dead2(f'v = x\n{token} y\nv')) for name, token in LINE_OPERATORS.items()])
group('letop-lambda', unsupported('term-form'), None, ('letop-lambda-dead2', dead2('v = x\n=> y\nv')))
# The same continuation in other shapes: a typed let, two lets, three scrutinees, one scrutinee, a blank line
# and a comment between the lines, an operand that is no name, the operator with no operand.
group('letop-shape', unsupported('operator'), None,
      ('letop-plus-typed-dead2', dead2('v : Flag = x\n+ y\nv')),
      ('letop-minus-typed-dead2', dead2('v : Flag = x\n- y\nv')),
      ('letop-plus-two-lets-dead2', dead2('v = x\nw = v\n+ y\nw')),
      ('letop-plus-dead3', dead3('v = x\n+ y\nv')),
      ('letop-arrow-dead3', dead3('v = x\n-> y\nv')),
      ('letop-plus-single', single('v = x\n+ y\nv')),
      ('letop-minus-single', single('v = x\n- y\nv')),
      ('letop-plus-blank-dead2', dead2('v = x\n\n+ y\nv')),
      ('letop-plus-comment-dead2', dead2('v = x\n# a comment\n+ y\nv')),
      ('letop-plus-call-operand-dead2', dead2('v = x\n+ k(y)\nv')),
      ('letop-plus-ctor-operand-dead2', dead2('v = x\n+ On{}\nv')),
      ('letop-plus-break-dead2', dead2('v = x\n+\ny\nv')),
      ('letop-minus-break-dead2', dead2('v = x\n-\ny\nv')),
      ('letop-star-typed-single', single('v : Flag = x\n* y\nv')),
      ('letop-plus-arm-later-dead2', dead2('w = y\nv = x\n+ w\nv')))
# The operator sits on the line of the let's value, or after a header's scrutinee: the same continuation.
group('letop-site', unsupported('operator'), None,
      ('letop-sameline-plus-dead2', dead2('v : Flag = x + y\nv')),
      ('letop-sameline-minus-dead2', dead2('v : Flag = x - y\nv')),
      ('letop-sameline-star-dead2', dead2('v : Flag = x * y\nv')),
      ('letop-sameline-arrow-dead2', dead2('v : Flag = x -> y\nv')),
      ('letop-header-plus-dead2', dead2('match x + y:\n  case _: On{}')),
      ('letop-header-star-dead2', dead2('match x * y:\n  case _: On{}')))
# The seed reads the same text in a live row or a flat body and rejects it for the operator's type.
group('letop-live', unsupported('operator'), 'a type for this operator',
      ('letop-plus-live2', live2('v = x\n+ y\nv')),
      ('letop-minus-live2', live2('v = x\n- y\nv')),
      ('letop-plus-flat', flat('v = x\n+ y\nv')),
      ('letop-plus-typed-flat', flat('v : Flag = x\n+ y\nv')))
# `x -> y` is a function type to the seed, which rejects the value's type.
group('letop-live-arrow', unsupported('operator'), '- expected : Type', ('letop-arrow-flat', flat('v = x\n-> y\nv')))
# An operator with no operand swallows the next line as its operand: the seed then finds no statement after the let.
group('letop-rejected', unsupported('operator'), '- expected : a term',
      ('letop-plus-alone-dead2', dead2('v = x\n+\nv')), ('letop-minus-alone-dead2', dead2('v = x\n-\nv')))
# The marker gap: the operand is a name and `=` or `:` follows it. The seed rejects the pair, so Invalid stays.
group('letop-gap', invalid('detached-marker'), '- expected : a term',
      ('letop-gap-plus-typed-dead2', dead2('v = x\n+ u : Flag = y\nu')),
      ('letop-gap-minus-typed-dead2', dead2('v = x\n- u : Flag = y\nv')),
      ('letop-gap-plus-untyped-dead2', dead2('v = x\n+ u = y\nu')),
      ('letop-gap-plus-typed-single', single('v = x\n+ u : Flag = x\nu')),
      ('letop-gap-plus-dead3', dead3('v = x\n+ u = y\nu')),
      ('letop-gap-plus-two-lets-dead2', dead2('v = x\nw = v\n+ u = w\nu')),
      ('letop-gap-plus-typed-flat', flat('v = x\n+ u : Flag = y\nu')))
# The seed rejects a second sign after the operator, since `-` followed by a space starts no term. The gap rule
# reads only a name and its `=` or `:`, so these answer Unsupported: sound, if less precise than before.
group('letop-doubled', unsupported('operator'), '- expected : a term',
      ('letop-doubled-minusminus-dead2', dead2('v = x\n-- y\nv')),
      ('letop-doubled-plusminus-dead2', dead2('v = x\n+- y\nv')))
# What stays invalid because the seed rejects it however it is written: `==` and `!=` after a let.
group('letop-control', invalid('binding-name'), '- expected : a term',
      ('letop-ctl-eqeq-dead2', dead2('v = x\n== y\nv')),
      ('letop-ctl-neq-dead2', dead2('v = x\n!= y\nv')))


# --- Finding 2: a touching `+name`, a glued `x+y` or a hole after an expression argument.
# The exact body of round 10's `argspace-promoted-call`, in a row the lowering discards.
PROMOTED_CALL = '''type F is Data:
  F0{}
  F1{}

type P is Type:
  Pr{l: F, r: F}

def two(a: F, b: F) -> F:
  match a:
    case F1{}: b
    case F0{}: F0{}

def f(+a: F, b: F) -> F:
  match a b:
    case _ _: F0{}
    case F1{} F1{}: two(a +b)

def main() -> F:
  f(F1{}, F1{})
'''
PROMO = {   # form -> the argument list of a call in a discarded row, and the seed's reason in a live row
    'promo': 'h(x +y)', 'promo-comma': 'h(x +y, x)', 'promo-nested': 'h(x, k(x +y))', 'promo-call': 'h(k(x) +y)',
    'promo-ctor': 'h(On{} +y)', 'promo-twice': 'h(x +y +x)', 'promo-first-comma': 'h(x, x +y)',
}
HOLE = {'hole': 'h(x ?y)', 'hole-glued': 'h(x?y)', 'hole-spaced': 'h(x ? y)',
        'hole-call': 'h(k(x) ?y)', 'hole-ctor': 'h(On{} ?y)', 'hole-nested': 'h(x, k(x ?y))'}
GLUED = {'glued': 'h(x+y)', 'glued-comma': 'h(x+y, x)', 'glued-call': 'h(k(x)+y)', 'glued-ctor': 'h(On{}+y)',
         'glued-nested': 'h(x, k(x+y))', 'glued-right-space': 'h(x+ y)', 'glued-first-comma': 'h(x, x+y)',
         'spaced': 'h(x + y)'}
group('argterm', unsupported('term-form'), None,
      *[(f'argterm-{name}-dead2', dead2(text)) for name, text in {**PROMO, **HOLE}.items()],
      ('argterm-promo-single', single('h(x +y)')),
      ('argterm-hole-single', single('h(x ?y)')),
      ('argterm-promo-own-dead2', dead2('h(x +y)\n')),
      ('argterm-promoted-call-dead2', PROMOTED_CALL))
# A hole needs a name after it: the seed rejects the bare `?`.
group('argterm-rejected', unsupported('term-form'), '- expected : a name', ('argterm-hole-bare-dead2', dead2('h(x ?)')))
group('argterm-operator', unsupported('operator'), None,
      *[(f'argterm-{name}-dead2', dead2(text)) for name, text in GLUED.items()],
      ('argterm-glued-single', single('h(x+y)')))
# The seed rejects the live twins for their scope or type, not for the syntax.
group('argterm-live', unsupported('term-form'), '- expected : a bound variable',
      ('argterm-promo-live2', live2('h(x +y)')), ('argterm-promo-flat', flat('h(x +y)')))
group('argterm-live-hole', unsupported('term-form'), '- expected : Flag',
      ('argterm-hole-live2', live2('h(x ?y)')), ('argterm-hole-flat', flat('h(x ?y)')))
group('argterm-live-operator', unsupported('operator'), '- expected : a bound variable',
      ('argterm-glued-live2', live2('h(x+y)')), ('argterm-glued-flat', flat('h(x+y)')))
# What the seed rejects for the syntax and Knot keeps invalid: `@y`, `\y`, `-y`, `$y`, a closer.
group('argterm-control', invalid('argument-separator'), 'expected',
      ('argterm-ctl-at-dead2', dead2('h(x @y)')), ('argterm-ctl-backslash-dead2', dead2('h(x \\y)')),
      ('argterm-ctl-minus-dead2', dead2('h(x -y)')), ('argterm-ctl-dollar-dead2', dead2('h(x $y)')),
      ('argterm-ctl-closer-dead2', dead2('h(x })')), ('argterm-ctl-eq-dead2', dead2('h(x = y)')),
      ('argterm-ctl-at-live2', live2('h(x @y)')))


# --- Finding 3: an arm body, or a statement after a let, that starts with a term at another column.
def body_multi(term, live):
    rows = 'case On{} x: a\n    case Off{} y:\n    ' + term if live else 'case _ _: a\n    case Off{} y:\n    ' + term
    return PRE + f'def f(a: Flag, b: Flag) -> Flag:\n  match a b:\n    {rows}\n\ndef main() -> Flag:\n  f(On{{}}, Off{{}})\n'


def body_single(term, live):
    rows = 'case On{}: a\n    case Off{}:\n    ' + term if live else 'case x: x\n    case On{}:\n    ' + term
    return PRE + f'def f(a: Flag) -> Flag:\n  match a:\n    {rows}\n\ndef main() -> Flag:\n  f(On{{}})\n'


def stmt_multi(term, live):
    let = 'u : Flag = y' if live else 'u : Flag = z'
    rows = f'case On{{}} x: a\n    case Off{{}} y:\n      {let}\n  {term}' if live else f'case x y: x\n    case On{{}} z:\n      {let}\n  {term}'
    return PRE + f'def f(a: Flag, b: Flag) -> Flag:\n  match a b:\n    {rows}\n\ndef main() -> Flag:\n  f(On{{}}, Off{{}})\n'


def stmt_single(term, live):
    rows = ('case Off{}: a\n    case On{}:\n      u : Flag = a\n  ' + term if live
            else 'case x: x\n    case On{}:\n      u : Flag = a\n  ' + term)
    return PRE + f'def f(a: Flag) -> Flag:\n  match a:\n    {rows}\n\ndef main() -> Flag:\n  f(On{{}})\n'


BODY_TERMS = {'paren': '(a)', 'paren2': '((a))', 'ctor': '(On{})', 'call': '(k(a))', 'bracket': '[a]', 'nil': '[]',
              'numeral': '0n', 'succ': '1n', 'u32': '0', 'hole': '?x'}
LIVE_TERMS = {'paren', 'paren2', 'ctor', 'call'}    # a live row needs a well-typed body
SHAPES = {'body-multi': body_multi, 'body-single': body_single, 'stmt-multi': stmt_multi, 'stmt-single': stmt_single}
group('bodystart', unsupported('body-indentation'), None,
      *[(f'bodystart-{shape}-{name}-{"live" if live else "dead"}', make(term, live))
        for shape, make in SHAPES.items() for name, term in BODY_TERMS.items() for live in (True, False)
        if not live or name in LIVE_TERMS])
# The precision controls: a token that starts no term stays invalid.
CONTROL_TERMS = {'closer': ')', 'comma': ',', 'colon': ':', 'eq': '=', 'case': 'case', 'def': 'def', 'type': 'type',
                 'bang': '!a', 'at': '@a', 'backslash': '\\'}
group('bodystart-control', invalid('body-indentation'), None,
      *[(f'bodystart-ctl-{shape}-{name}', make(term, False)) for shape, make in SHAPES.items()
        for name, term in CONTROL_TERMS.items()])


# --- The class grid of the round-12 reviewer: 60 terms at three columns in a discarded row, as an arm body
# and as a statement after a let, in a one- and a two-scrutinee match (720 cells). It is a table, not fixtures.
GRID_PRE = '''type Flag is Data:
  Off{}
  On{}

def id(a: Flag) -> Flag:
  a

'''
GRID_TERMS = ['(a)', '((a))', '(On{})', '(id(a))', '(', 'a', 'On{}', 'id(a)', 'nope', '0n', '1n', '0', '[]', '[a]', '"x"', "'c'",
              '\\x => x', 'λx => x', '!a', '@a', '?', '?x', '~x', '&a', '*a', '<a', '>a', '-a', '+a', '- a', '+ a', 'match a:',
              ')', ',', ':', '=', 'case', 'def', 'type', 'import', '$', '%', '^', '.', ';', '_', 'x.y', 'a b', '{', '}', ']',
              '\\', '<>', '->', '=>', '==', '~']
GRID_COLUMNS = [4, 2, 0]
INFIX_START = ('*', '<', '>', '&', '|', '%')
TERM_OPENERS = ('(', '[', '?', '+', '-')


def grid_source(term, col, shape, form):
    ind = ' ' * col
    if form == 'body':
        if shape == 'single':
            return (GRID_PRE + 'def f(a: Flag) -> Flag:\n  match a:\n    case x: x\n    case On{}:\n' + ind + term
                    + '\n\ndef main() -> Flag:\n  f(On{})\n')
        return (GRID_PRE + 'def f(a: Flag, b: Flag) -> Flag:\n  match a b:\n    case x y: x\n    case On{} z:\n' + ind + term
                + '\n\ndef main() -> Flag:\n  f(On{}, Off{})\n')
    if shape == 'single':
        return (GRID_PRE + 'def f(a: Flag) -> Flag:\n  match a:\n    case x: x\n    case On{}:\n      u : Flag = a\n' + ind + term
                + '\n\ndef main() -> Flag:\n  f(On{})\n')
    return (GRID_PRE + 'def f(a: Flag, b: Flag) -> Flag:\n  match a b:\n    case x y: x\n    case On{} z:\n      u : Flag = z\n' + ind + term
            + '\n\ndef main() -> Flag:\n  f(On{}, Off{})\n')


def grid_knot(term, form):
    """The reviewed Knot outcome of a cell, or None where only the D4 constraint applies (a seed-accepted
    program is never Invalid, a seed-rejected one never Accepted)."""
    if '"' in term or "'" in term:
        return unsupported_lex('literal')
    if 'λ' in term:
        return unsupported_lex('non-ascii')
    first = term.split(' ')[0]
    words = first.replace('(', ' ').replace('[', ' ').split()
    opener = (first[:1].isalpha() or first[:1] == '_' or first[:1].isdigit() or first.startswith(TERM_OPENERS)
              or first == 'match') and first not in ('case', 'def', 'type', 'import')
    if opener:
        return unsupported('body-indentation')
    if term in (')', ',', ':', '=', 'case', 'def', 'type', '!a', '@a', '\\'):
        return invalid('body-indentation')
    return None


def unsupported_lex(code):
    return {'exit': 3, 'diagnostic': f'Unsupported\tlex\t{code}\t'}


def grid_cells():
    return [{'term': term, 'column': col, 'shape': shape, 'form': form,
             'source': grid_source(term, col, shape, form)}
            for term in GRID_TERMS for col in GRID_COLUMNS for shape in ('single', 'multi') for form in ('body', 'let')]


# --- Finding 4: a terminal default is copied into every remaining constructor arm of the core.
def columns(width, ctors, heavy=False):
    """`width` columns of `ctors` constructors: a row that names the first constructor in one column, and a
    catch-all row. The seed compiles the tree once; Knot's core grows as ctors^width. A heavy body is a call
    of three nodes, so that a core that counted only its cases and branches would fall under the budget."""
    names = ''.join(f'  Q{i}{{}}\n' for i in range(ctors))
    params = ', '.join(f'{chr(97 + i)}: Q' for i in range(width))
    scrutinees = ' '.join(chr(97 + i) for i in range(width))
    body = lambda flag: f'pair({flag}, {flag})' if heavy else flag
    rows = ''
    for i in range(width):
        cells = ' '.join('Q0{}' if j == i else '_' for j in range(width))
        rows += f'    case {cells}: {body("On{}" if i % 2 == 0 else "Off{}")}\n'
    rows += f'    case {" ".join("_" for _ in range(width))}: {body("On{}")}\n'
    args = ', '.join('Q1{}' for _ in range(width))
    helper = 'def pair(a: Flag, b: Flag) -> Flag:\n  a\n\n' if heavy else ''
    return (f'type Flag is Data:\n  Off{{}}\n  On{{}}\n\ntype Q is Data:\n{names}\n{helper}def f({params}) -> Flag:\n  match {scrutinees}:\n{rows}\n'
            f'def main() -> Flag:\n  f({args})\n')


# `ddWxC` is W columns of C constructors. Accepted ones stay under the core budget (dd5x5's module is 34,434 bytes;
# the seed's Bun lane computes it and then faults, which the gates classify as Exhausted (host)); the others exceed it.
BUDGET = {'dd4x5': (4, 5, ACCEPTED, False), 'dd5x5': (5, 5, ACCEPTED, False), 'dd7x5': (7, 5, EXHAUSTED, False),
          'dd9x5': (9, 5, EXHAUSTED, False), 'dd10x5': (10, 5, EXHAUSTED, False), 'dd10x3': (10, 3, EXHAUSTED, False),
          'dd7x4-heavy': (7, 4, EXHAUSTED, True)}
for label, outcome in (('accepted', ACCEPTED), ('exhausted', EXHAUSTED)):
    group(f'default-{label}', outcome, None,
          *[(f'default-{name}', columns(width, ctors, heavy)) for name, (width, ctors, expected, heavy) in BUDGET.items()
            if expected == outcome])


# --- The round-12 reviewer's zoo: 64 forms of a discarded row's body (strings, chars, lists, tuples, lambdas, `!`, `~`,
# `#`, `@`, `$`, fields, indexes, lets, nested matches, operators). A table like the grid: the seed's answer is
# frozen, and a seed-accepted form is never `Invalid` in Knot.
ZOO = {
    'string': 'h("a", x)', 'char': "h('a', x)", 'nat': 'h(0n, x)', 'u32': 'h(7, x)', 'list': 'h([x], x)', 'tuple': 'h((x, y), x)',
    'lambda': 'h(k => x, x)', 'lambda2': 'k => x', 'bang': '!x', 'tilde': '~x', 'hash': '#x', 'at': '@x', 'dollar': '$x',
    'field': 'x.y', 'index': 'x[0]', 'ctor-call-newline': 'h(x,\n  y)', 'call-newline-paren': 'h\n(x, y)',
    'let-tuple': '(a, b) = x\na', 'let-annot': 'v : Flag = x\nv', 'let-erased': '-v = x\nx', 'let-plus': '+v = x\nx',
    'let-ctor': 'On{} = x\nx', 'if': 'if x: On{}', 'elif': 'x if y else x', 'match-nested': 'match x:\n  case _: y',
    'match-nested2': 'match x y:\n  case _ _: x', 'fork': 'fork x: y', 'open': 'open x: y', 'with': 'with x: y',
    'ask': 'ask v = x\nv', 'use': 'use v = x\nv', 'return': 'return x', 'lam-dup': 'λx x', 'unicode-lambda': 'λ x. x',
    'double-colon': 'x::y', 'pipe': 'x |> k', 'range': 'x..y', 'dollar-call': 'k $ x', 'backslash': '\\x. x',
    'paren-only': '(x)', 'paren-call': '(k)(x)', 'ann': '(x : Flag)', 'ann-nat': '(x + y : Nat)', 'trailing-comma': 'h(x, y,)',
    'empty-call': 'k()', 'ctor-empty-fields': 'On{ }', 'ctor-space-brace': 'On {}', 'comment-inline': 'x # c',
    'tab': 'x\t', 'semicolon': 'x; y', 'dot-call': 'x.k(y)', 'question': '?x', 'hole': '?', 'star': 'x * y',
    'percent': 'x % y', 'eq': 'x == y', 'neq': 'x != y', 'lt': 'x < y', 'arrow': 'x -> y', 'and': 'x && y',
    'or': 'x || y', 'shift': 'x << y', 'pp': 'x ++ y', 'diamond': 'x <> y',
}


def zoo_cells():
    return [{'form': name, 'source': dead2(body)} for name, body in ZOO.items()]


def observe_zoo(cell):
    name = hashlib.sha256(cell['source'].encode()).hexdigest()[:16]
    path = oracle.ROOT / '.local/compiler-nest/round13-grid' / f'{name}.bend'
    oracle.publish(path, cell['source'])
    result = oracle.run(['bun', oracle.SEED, str(path.relative_to(oracle.ROOT))])
    assert result['exit'] in (0, 1), (cell['form'], result)
    return {'form': cell['form'], 'sha256': hashlib.sha256(cell['source'].encode()).hexdigest(),
            'seed': {'exit': result['exit'], 'stdout': result['stdout'] if result['exit'] == 0 else ''}}


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
    command = ['bun', oracle.SEED, str(path.relative_to(oracle.ROOT))]
    main = {'command': command, **oracle.run(command)}
    assert (main['exit'] == 0 and not main['stderr']) or (rejected and main['exit'] == 1 and main['stderr'].startswith('Error:')), main
    source = path.read_text()
    return {'name': path.stem, 'file': str(path.relative_to(oracle.ROOT)), 'sha256': oracle.sha256(path),
            'fields': any(not nullary for _, _, cs in oracle.declarations(source)[0] for _, nullary in cs),
            'seed': main, 'calls': []}


def observe(path, group_name, knot, reason):
    # A stated reason with an Unsupported outcome marks a program the seed rejects and Knot cannot read; an
    # Invalid outcome is a program the seed rejects, and its group states the reason too.
    lax = knot['exit'] == 3 and bool(reason)
    case = direct(path, lax or knot['exit'] == 2) if knot['exit'] in (2, 3) else review_seed.observe(path)
    case['finding'] = group_name
    accepted = case['seed']['exit'] == 0
    assert lax or accepted == (knot['exit'] != 2), (path.name, 'seed acceptance and reviewed Knot outcome differ', case['seed']['stderr'][:200])
    if reason:
        assert reason in case['seed']['stderr'], (path.name, 'seed rejects for another reason', case['seed']['stderr'][:200])
    case['knot'] = knot
    return case


def observe_cell(cell):
    """The seed's answer to one grid cell. Sources are written under `.local` and never kept."""
    name = hashlib.sha256(cell['source'].encode()).hexdigest()[:16]
    path = oracle.ROOT / '.local/compiler-nest/round13-grid' / f'{name}.bend'
    oracle.publish(path, cell['source'])
    command = ['bun', oracle.SEED, str(path.relative_to(oracle.ROOT))]
    result = oracle.run(command)
    assert result['exit'] in (0, 1), (cell, result)
    knot = grid_knot(cell['term'], cell['form'])
    return {'term': cell['term'], 'column': cell['column'], 'shape': cell['shape'], 'form': cell['form'],
            'sha256': hashlib.sha256(cell['source'].encode()).hexdigest(),
            'seed': {'exit': result['exit'], 'stdout': result['stdout'] if result['exit'] == 0 else '',
                     'error': result['stderr'].split('\n')[1] if result['exit'] == 1 and '\n' in result['stderr'] else ''},
            'knot': knot}


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
        grid = list(pool.map(observe_cell, grid_cells()))
        zoo = list(pool.map(observe_zoo, zoo_cells()))
    for cell in grid:
        # a seed-accepted program is never Invalid and a seed-rejected one never Accepted: the class constraints
        expected = cell['knot']
        if expected is not None and cell['seed']['exit'] == 0:
            assert expected['exit'] != 2, ('a reviewed Invalid for a seed-accepted cell', cell)
    result = {'basis': 'The round-12 review findings (a spaced operator after a let, a `+name`, glued `x+y` or hole after an '
                       'argument, a body that starts with a term at another column, the default copies of a wildcard matrix) '
                       'as programs generated from templates, with their controls, frozen with the pinned seed before the repairs.',
              'seed': oracle.environment()[0], 'fixtures': observed}
    grid_result = {'basis': 'The reviewer\'s 720-cell class grid: 60 terms, three columns, one and two scrutinees, an arm body and '
                            'a statement after a let, in a discarded row. Cells are generated (round13_seed.grid_cells) and frozen '
                            'by source hash with the seed\'s answer; `knot` is the reviewed outcome where the ruling fixes one.',
                   'seed': result['seed'], 'cells': grid, 'zoo': zoo}
    if options.write:
        MANIFEST.write_text(json.dumps(result, indent=2) + '\n')
        GRID.write_text(json.dumps(grid_result, indent=2) + '\n')
    else:
        assert result == json.loads(MANIFEST.read_text()), 'round-13 seed observations changed'
        assert grid_result == json.loads(GRID.read_text()), 'round-13 grid observations changed'
    print(f"Round-13 seed: {len(result['fixtures'])} fixtures, "
          f"{sum(len(c['calls']) for c in result['fixtures'])} calls, {len(grid)} grid cells, {len(zoo)} zoo forms; no differences")


if __name__ == '__main__':
    main()
