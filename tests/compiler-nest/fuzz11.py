#!/usr/bin/env python3
"""Round-11 differential generator: fixed seed, systematic classes, the pinned seed as the oracle.

Round 10 found new shapes one at a time; each family below draws a finding's shape and its
neighbours together, so a program the seed judges differently from Knot turns up by construction.
Every program carries a class `family:...`, and the summary counts seed and Knot outcomes per class.

- names: binder names drawn from a declared datatype, a declared constructor, a name that is both,
  a datatype and a constructor declared after the def, a function, Base's names (`String`, `List`,
  `T`, `Unit`) and plain names. Bare, `+`, erased and let binders, in rows, later columns, fields,
  nested fields, lets in arms, parameters, a parameter used as scrutinee and type fields; then a type
  written after the binder (an annotation of a datatype the binder may hide, or of another), a call
  of the binder, or nothing.
- dead: a match whose first row is irrefutable or repeated, so later rows are unreachable, holding
  nested matches (one to three deep, flat and multi-column, on a parameter or a fresh field, after a
  let) whose rows are good or bad: an unknown constructor, arity or width off by one, a bare
  constructor, a call, a promoted datatype or constructor, a bad nested field; lets with `+` names in
  those bodies, and terms the seed never checks there. Live twins of each.
- gaps: multi-scrutinee headers, row patterns and bodies with a space, line break or comment between
  adjacent tokens, commas, detached braces and markers, and literal patterns (Nat, U32, Char, hex).
- parens: header columns that are a name, a call `h(a)` or a parenthesized name, and row patterns that
  are a name, a wildcard, a constructor or a parenthesized name, with a space, line break or comment
  between any adjacent pair (the seed reads a `(` that starts a line as the next term, not a call);
  live, and nested in an unreachable row, where a computed scrutinee is accepted.
- widths: rows with one pattern too many or too few, constructor patterns with one field too many
  or too few, and their correct twins; reachable and not, flat and nested, one to three columns.
- layout: the case column, statement columns, marked and unmarked bodies at or left of their case, a
  let split before its colon or `=`, a statement on a let's line, a declaration at another column or
  on a body's line, in single and multi-scrutinee matches.

A false acceptance (seed rejects, Knot accepts), a false Invalid (seed accepts, Knot Invalid) or a host
or internal failure fails the gate. Accepted programs also run through the Bend evaluator. No let
binder is named after a constructor: that is the literals branch's finding 7.
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random

import check as gate

SEED = 0x4E455354 ^ 0x11
COUNT = 6100

PRELUDE = '''type Flag is Data:
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

type Nat is Data:
  Zero{}
  Succ{pred: Nat}

def h(a: Flag) -> Flag:
  a

'''
LATER = '''
type Later is Data:
  LateA{}
  LateB{}
'''
# Names by how the seed treats them at a binder.
CONSTRUCTORS = ['On', 'Off', 'Red', 'Blue', 'None', 'Some', 'Zero', 'Succ']
DATATYPES = ['Flag', 'Color', 'Opt', 'Nat']
BOTH = ['Tp', 'Pr']
AFTER = ['Later', 'LateA']
OTHER = ['h', 'String', 'List', 'T', 'Unit', 'q', 'v2', '_x']
NAMES = CONSTRUCTORS + DATATYPES + BOTH + AFTER + OTHER
LETTABLE = DATATYPES + ['Later'] + OTHER          # a let binder that is no constructor
ANNOTATED = {'Flag': 'On{}', 'Color': 'Red{}', 'Opt': 'None{}', 'Pr': 'Pr{On{}, Off{}}', 'Tp': 'Tp{On{}}', 'Nat': 'Zero{}',
             'Later': 'LateA{}', 'String': 'On{}', 'T': 'On{}'}
CALLS = {'Flag': 'On{}', 'Nat': 'Succ{Zero{}}', 'Opt': 'Some{On{}}'}


def kind(name):
    return ('both' if name in BOTH else 'constructor' if name in CONSTRUCTORS else 'datatype' if name in DATATYPES else
            'later' if name in AFTER else 'other')


def main(args, result='Flag'):
    return f'def main() -> {result}:\n  f({args})\n'


class Draw:
    def __init__(self, rng):
        self.rng = rng

    def pick(self, items):
        return self.rng.choice(items)

    def chance(self, n):
        return self.rng.randrange(n) == 0

    def weighted(self, table):
        point = self.rng.randrange(sum(weight for _, weight in table))
        for item, weight in table:
            if point < weight:
                return item
            point -= weight


# ---------------------------------------------------------------------------------------- names
def names_program(d):
    site = d.weighted([('row', 4), ('row2a', 3), ('row2b', 3), ('field', 3), ('nested', 3), ('let', 5), ('param', 3),
                       ('scrutinee', 2), ('typefield', 2), ('later', 2)])
    # a parameter or field named after a datatype is the case that hides a later type
    name = d.pick(LETTABLE if site == 'let' else AFTER + ['q'] if site == 'later' else
                  DATATYPES if site in ('param', 'typefield') and d.chance(2) else NAMES)
    mark = d.weighted([('', 5), ('+', 4), ('-', 1)]) if site in ('let', 'param', 'typefield') else d.weighted([('', 5), ('+', 4)])
    use = d.weighted([('type', 6), ('none', 2), ('call', 1)])
    used = d.pick(list(ANNOTATED)) if use == 'type' else None
    body = ''
    if used:
        body = f'      y : {used} = {ANNOTATED[used]}\n'
    elif use == 'call':
        body = '      y : Flag = h(On{})\n'
    body += '      On{}\n'
    binder = f'{mark}{name}'
    later = LATER if site == 'later' or d.chance(6) else ''
    if site == 'row':
        src = f'def f(a: Flag) -> Flag:\n  match a:\n    case {binder}:\n{body}    case _: Off{{}}\n\n' + main('On{}')
    elif site == 'row2a':
        src = f'def f(a: Flag, b: Flag) -> Flag:\n  match a b:\n    case {binder} _:\n{body}    case _ _: Off{{}}\n\n' + main('On{}, Off{}')
    elif site == 'row2b':
        src = f'def f(a: Flag, b: Flag) -> Flag:\n  match a b:\n    case _ {binder}:\n{body}    case _ _: Off{{}}\n\n' + main('On{}, Off{}')
    elif site == 'field':
        pattern = d.pick([f'Pr{{{binder}, _}}', f'Pr{{_, {binder}}}'])
        src = f'def f(p: Pr) -> Flag:\n  match p:\n    case {pattern}:\n{body}\n' + main('Pr{On{}, On{}}')
    elif site == 'nested':
        src = f'def f(p: Opt) -> Flag:\n  match p:\n    case Some{{{binder}}}:\n{body}    case _: Off{{}}\n\n' + main('Some{On{}}')
    elif site == 'let':
        form = d.pick(['plain', 'typed', 'marked', 'erased'])
        let = {'plain': f'{name} = h(a)', 'typed': f'{name} : Flag = On{{}}', 'marked': f'+{name} = h(a)',
               'erased': f'-{name} = h(a)'}[form]
        binder, mark = {'plain': name, 'typed': name, 'marked': f'+{name}', 'erased': f'-{name}'}[form], form
        lines = ''.join(f'{line.strip()}\n' for line in body.rstrip('\n').split('\n'))
        if d.chance(2):
            src = f'def f(a: Flag) -> Flag:\n  {let}\n' + ''.join(f'  {line}\n' for line in lines.split('\n') if line) + '\n' + main('On{}')
        else:
            src = (f'def f(a: Flag) -> Flag:\n  match a:\n    case _:\n      {let}\n'
                   + ''.join(f'      {line}\n' for line in lines.split('\n') if line) + '\n' + main('On{}'))
    elif site == 'param':
        result = d.pick(['Flag', 'Color'])
        two = d.chance(2)
        param = f'{binder}: Flag' + (', b: Flag' if two else '')
        ret = 'Red{}' if result == 'Color' else 'On{}'
        stmt = f'  y : {used} = {ANNOTATED[used]}\n' if used else ''
        src = f'def f({param}) -> {result}:\n{stmt}  {ret}\n\n' + main('On{}, Off{}' if two else 'On{}', result)
    elif site == 'scrutinee':
        # a parameter named like a constructor or datatype is still a variable scrutinee
        src = f'def f({name}: Flag) -> Flag:\n  match {name}:\n    case On{{}}: Off{{}}\n    case Off{{}}: On{{}}\n\n' + main('On{}')
        binder = name
    elif site == 'typefield':
        other = d.pick(['Flag', 'Color', 'Flag'])
        src = f'type Q is Type:\n  Q{{{binder}: Flag, y: {other}}}\n\ndef f(a: Flag) -> Flag:\n  a\n\n' + main('On{}')
    else:   # later: the datatype or constructor is declared after the def
        row = d.pick([binder, f'+{name}'])
        src = f'def f(a: Flag) -> Flag:\n  match a:\n    case {row}:\n{body}    case _: Off{{}}\n\n' + main('On{}')
    tag = 'annotated' if used else use
    return f'names:{site}:{mark or "bare"}:{kind(name)}:{tag}', PRELUDE + src + later


# ------------------------------------------------------------------------------------ dead rows
def dead_row(d, flag):
    """A nested row's pattern, whether it is good, and how it is bad, for a Flag or an Opt scrutinee."""
    on, none = 'On{}', 'None{}'
    ctor = on if flag else none
    table = [('good', 'var', 'x'), ('good', 'wild', '_'), ('good', 'ctor', ctor), ('good', 'other-type', 'Red{}'),
             ('bad', 'unknown', 'Nope{}'),
             ('bad', 'arity-up', 'On{x}' if flag else 'None{x}'), ('bad', 'bare', 'On' if flag else 'None'),
             ('bad', 'call', 'h(x)'), ('bad', 'plus-dtype', '+Flag' if flag else '+Opt'),
             ('bad', 'plus-ctor', '+On' if flag else '+None'), ('bad', 'count-up', f'{ctor} {ctor}')]
    if flag:
        table.append(('bad', 'arity-down', 'Some{}'))
    else:
        table += [('bad', 'field-unknown', 'Some{Nope{}}'), ('bad', 'field-arity', 'Some{On{x}}'), ('bad', 'field-call', 'Some{h(x)}'),
                  ('good', 'field-var', 'Some{x}'), ('good', 'field-ctor', 'Some{On{}}')]
    return d.pick(table)


def lax(d, pad):
    """A statement or two the seed never reads in a discarded body."""
    return d.pick([''] * 8 + [f'{pad}zzz : Nope = Nope{{}}\n', f'{pad}-w : Flag = On{{}}\n', f'{pad}u = q\n',
                   f'{pad}{d.pick(["+", "", "-"])}{d.pick(LETTABLE)} = h(a)\n',
                   f'{pad}u = h(On{{}} {d.pick(["10n", "1n+m", "0n", "u"])})\n'])


def nested(d, depth, scrutinee, flag, kinds, pad, dead):
    """A nested match with one to three rows, each good or bad, on `scrutinee`; `dead` allows unchecked lets."""
    # the seed reads any term after the scrutinee, so a discarded header may carry more columns
    extra, more = d.pick([('', 0)] * 95 + [(' + b', 0), (' - b', 0), (' (a)', 0), (' 10n', 1), (' 1n+m', 1)])
    rest = ' _' * more
    rows = []
    for _ in range(d.pick([1, 2, 2, 3])):
        state, what, pattern = dead_row(d, flag)
        kinds.append(f'{state}-{what}')
        if depth > 1 and d.chance(2):
            rows.append(f'{pad}    case {pattern}{rest}:\n' + nested(d, depth - 1, scrutinee, flag, kinds, pad + '    ', dead))
        else:
            rows.append(f'{pad}    case {pattern}{rest}: On{{}}\n')
    if d.chance(2):
        rows.append(f'{pad}    case _{rest}: Off{{}}\n')
    return f'{pad}  match {scrutinee}{extra}:\n' + ''.join(rows)


def wide_program(d):
    """A nested match of two scrutinee columns whose rows have one pattern too few, too many, or the right number."""
    rows = []
    for _ in range(d.pick([1, 2, 3])):
        n = d.pick([1, 2, 2, 3])
        rows.append('    ' * 2 + 'case ' + ' '.join(d.pick(['_', 'x', 'On{}', 'Off{}', '+y']) for _ in range(n)) + ': On{}\n')
    live = d.chance(3)
    inner = '      match a b:\n' + ''.join(rows) + ('' if d.chance(2) else '        case _ _: Off{}\n')
    head = '    case _ _: Off{}\n    case On{} _:\n' if not live else '    case On{} _:\n'
    tail = '    case _ _: Off{}\n' if live else ''
    src = f'def f(a: Flag, b: Flag) -> Flag:\n  match a b:\n{head}{inner}{tail}\n' + main('On{}, Off{}')
    return f'dead:{"wide-live" if live else "wide"}', PRELUDE + src, []


def dead_program(d):
    if d.chance(8):
        return wide_program(d)
    shape = d.weighted([('single', 4), ('dup', 3), ('multi', 3), ('field', 4), ('let', 3), ('default', 2), ('live', 3)])
    depth = d.pick([1, 1, 2, 3])
    kinds = []
    if shape == 'live':
        inner = nested(d, depth, 'v', True, kinds, '    ', False)
        src = f'def f(p: Opt) -> Flag:\n  match p:\n    case Some{{v}}:\n{inner}    case _: Off{{}}\n\n' + main('Some{On{}}')
    elif shape == 'field':
        inner = nested(d, depth, 'v', True, kinds, '    ', True)
        head = d.pick(['    case _: Off{}\n', '    case None{}: Off{}\n    case _: Off{}\n'])
        src = f'def f(p: Opt) -> Flag:\n  match p:\n{head}    case Some{{v}}:\n{lax(d, "      ")}{inner}\n' + main('Some{On{}}')
    else:
        multi = shape == 'multi'
        inner = nested(d, depth, 'a', True, kinds, '    ', True)
        params = 'a: Flag, b: Flag' if multi else 'a: Flag'
        cols = 'a b' if multi else 'a'
        extra = ' _' if multi else ''
        pre = {'single': f'    case _{extra}: Off{{}}\n', 'dup': f'    case On{{}}{extra}: Off{{}}\n',
               'multi': f'    case _ _: Off{{}}\n', 'let': f'    case _{extra}: Off{{}}\n',
               'default': f'    case On{{}}{extra}: Off{{}}\n    case Off{{}}{extra}: On{{}}\n'}[shape]
        arm = {'single': f'    case On{{}}{extra}:\n', 'dup': f'    case On{{}}{extra}:\n', 'multi': f'    case On{{}} _:\n',
               'let': f'    case On{{}}{extra}:\n      u : Flag = a\n', 'default': f'    case _{extra}:\n'}[shape]
        tail = '    case Off{}: On{}\n' if shape == 'dup' and not multi else ''
        src = (f'def f({params}) -> Flag:\n  match {cols}:\n{pre}{arm}{lax(d, "      ")}{inner}{tail}\n'
               + main('On{}, Off{}' if multi else 'On{}'))
    return f'dead:{shape}', PRELUDE + src, kinds


# ------------------------------------------------------------------------------------------ gaps
GAP = [' ', '  ', '\n      ', ' # gap\n      ', ',', ', ', ' , ', '\n      # gap\n      ', '']
PATTERNS = {
    'Flag': [['_'], ['x'], ['+', 'x'], ['On', '{', '}'], ['Off', '{', '}'], ['_x']],
    'Nat': [['_'], ['m'], ['+', 'm'], ['Zero', '{', '}'], ['Succ', '{', '_', '}'], ['Succ', '{', 'm', '}'],
            ['0n'], ['1n'], ['2n'], ['10n'], ['1n', '+', 'm'], ['0'], ['1'], ["'a'"], ['0x1'], ['Succ', '{', '0n', '}']],
    'Opt': [['_'], ['p'], ['None', '{', '}'], ['Some', '{', '_', '}'], ['Some', '{', 'x', '}'],
            ['Some', '{', 'On', '{', '}', '}'], ['Some', '{', '+', 'x', '}']],
}
COLUMNS = {'Flag': 'a', 'Nat': 'n', 'Opt': 'p'}
BODIES = [['On', '{', '}'], ['Off', '{', '}'], ['h', '(', 'On', '{', '}', ')'], ['a']]


def wordlike(text):
    return text[0].isalnum() or text[0] in "_'"


def join(d, tokens, rate, focus=None):
    """Adjacent tokens are joined by their usual separator, or, one time in `rate`, by a random gap;
    a rate of 0 puts exactly one random gap between one random pair, half the time before a token `focus`
    accepts."""
    out = [tokens[0]]
    only = None
    if rate == 0 and len(tokens) > 1:
        aimed = [i for i, tok in enumerate(tokens[1:]) if focus and focus(tok)]
        only = d.pick(aimed) if aimed and d.chance(2) else d.rng.randrange(len(tokens) - 1)
    for i, (prev, tok) in enumerate(zip(tokens, tokens[1:])):
        needs = wordlike(prev[-1]) and wordlike(tok)
        usual = ' ' if needs else ''
        gapped = i == only if rate == 0 else d.chance(rate)
        pool = [gap for gap in GAP if gap or not needs]
        if gapped and focus and focus(tok) and d.chance(2):
            pool = [gap for gap in pool if '\n' in gap]
        out.append(d.pick(pool) if gapped else usual)
        out.append(tok)
    return ''.join(out)


def gaps_program(d):
    types = [d.pick(['Flag', 'Nat', 'Opt', 'Flag', 'Nat']) for _ in range(d.pick([1, 2, 2, 3]))]
    names = [COLUMNS[t] + (str(i) if types[:i].count(t) else '') for i, t in enumerate(types)]
    params = ', '.join(f'{n}: {t}' for n, t in zip(names, types))
    rate = d.pick([0, 0, 6, 10, 20])
    literal = False
    rows = []
    for _ in range(d.pick([1, 2, 3])):
        tokens = ['case']
        for i, t in enumerate(types):
            pattern = d.pick(PATTERNS[t])
            literal |= pattern[0][0].isdigit() or pattern[0] == "'a'"
            tokens += ([','] if i and d.chance(5) else []) + pattern
        body = d.pick(BODIES) if 'a' not in names or not d.chance(3) else ['a']
        rows.append(join(d, tokens + [':'] + [tok for tok in body if tok != 'a' or 'a' in names], rate))
    header = join(d, ['match'] + [tok for i, n in enumerate(names) for tok in ([','] if i and d.chance(6) else []) + [n]] + [':'], rate)
    wild = 'case ' + ' '.join('_' for _ in types) + ': Off{}'
    args = ', '.join(CALLS[t] for t in types)
    src = f'def f({params}) -> Flag:\n  {header}\n    ' + '\n    '.join(rows + [wild]) + '\n\n' + main(args)
    return f'gaps:{len(types)}col:{"literal" if literal else "plain"}', PRELUDE + src


# ---------------------------------------------------------------------------------------- parens
def parens_program(d):
    opens = lambda tok: tok == '('
    cols = d.pick([1, 2, 2, 3])
    reach = d.pick(['dead', 'live'])
    rate = d.pick([0, 0, 0, 6, 12])
    names = 'abc'[:cols]
    kinds = [d.weighted([('name', 4), ('call', 3), ('paren', 2)]) for _ in range(cols)]
    header = ['match']
    for name, form in zip(names, kinds):
        header += {'name': [name], 'call': ['h', '(', name, ')'], 'paren': ['(', name, ')']}[form]
    header.append(':')
    rows = []
    for _ in range(d.pick([1, 2])):
        row = ['case']
        for _ in range(max(cols + d.pick([0, 0, 0, 0, 1, -1]), 1)):
            row += d.pick([['_'], ['x'], ['(', 'x', ')'], ['On', '{', '}'], ['_'], ['x']])
        rows.append(join(d, row + [':', 'On', '{', '}'], rate, opens))
    sig = ', '.join(f'{n}: Flag' for n in names)
    args = ', '.join(['On{}', 'Off{}', 'On{}'][:cols])
    scrut = ' '.join(names)
    if reach == 'live':
        src = f'def f({sig}) -> Flag:\n  {join(d, header, rate, opens)}\n    ' + '\n    '.join(rows) + '\n\n' + main(args)
    else:
        outer = ' '.join(['On{}'] + ['_'] * (cols - 1))
        src = (f'def f({sig}) -> Flag:\n  match {scrut}:\n    case {" ".join("_" for _ in names)}: Off{{}}\n    case {outer}:\n'
               f'      {join(d, header, rate, opens)}\n        ' + '\n        '.join(rows) + '\n\n' + main(args))
    return f'parens:{cols}col:{reach}:{"-".join(sorted(set(kinds)))}', PRELUDE + src


# ---------------------------------------------------------------------------------------- widths
def widths_program(d):
    cols = d.pick([1, 2, 3])
    shape = d.weighted([('width', 4), ('ctor', 4), ('nested', 3), ('flat', 2)])
    reach = d.pick(['live', 'dead'])
    delta = d.pick([-1, 0, 1, 1, 2])
    sig = ', '.join(f'{c}: Flag' for c in 'abc'[:cols])
    scrut = ' '.join('abc'[:cols])
    args = ', '.join(['On{}'] * cols)
    wild = ' '.join(['_'] * cols)
    if shape == 'width':
        n = cols + delta
        row = ' '.join(['On{}'] * n)
        bad = f'    case {row}: Off{{}}\n'
        rows = bad + f'    case {wild}: On{{}}\n' if reach == 'live' else f'    case {wild}: On{{}}\n' + bad
        return f'widths:width:{reach}:{delta}', PRELUDE + f'def f({sig}) -> Flag:\n  match {scrut}:\n{rows}\n' + main(args)
    fields = d.pick([1, 2, 3])
    arity = ', '.join('x' for _ in range(fields))
    rest = ''.join(' _' for _ in range(cols - 1))
    if shape == 'ctor':
        bad = f'    case Pr{{{arity}}}{rest}: On{{}}\n'
        good = f'    case Pr{{a, b}}{rest}: Off{{}}\n'
        rows = (bad + good if reach == 'live' else good + bad) + f'    case _{rest}: On{{}}\n'
        sig2 = 'p: Pr' + ''.join(f', {c}: Flag' for c in 'bc'[:cols - 1])
        call = 'Pr{On{}, Off{}}' + ''.join(', On{}' for _ in range(cols - 1))
        src = f'def f({sig2}) -> Flag:\n  match p' + ''.join(f' {c}' for c in 'bc'[:cols - 1]) + f':\n{rows}\n' + main(call)
        return f'widths:ctor:{reach}:{fields}', PRELUDE + src
    if shape == 'nested':
        rows = (f'    case Bx{{Pr{{{arity}}}}}: On{{}}\n    case _: Off{{}}\n' if reach == 'live'
                else f'    case _: Off{{}}\n    case Bx{{Pr{{{arity}}}}}: On{{}}\n')
        src = 'type Bx is Type:\n  Bx{p: Pr}\n\ndef f(x: Bx) -> Flag:\n  match x:\n' + rows + '\n' + main('Bx{Pr{On{}, Off{}}}')
        return f'widths:nested:{reach}:{fields}', PRELUDE + src
    src = f'def f(p: Pr) -> Flag:\n  match p:\n    case Pr{{{arity}}}: On{{}}\n\n' + main('Pr{On{}, Off{}}')
    return f'widths:flat:live:{fields}', PRELUDE + src


# ---------------------------------------------------------------------------------------- layout
def layout_program(d):
    multi = d.chance(2)
    match_col = d.pick([2, 2, 2, 3])
    case_col = max(d.pick([match_col - 1, match_col, match_col + 2, match_col + 2, match_col + 2, match_col + 1]), 0)
    body_col = max(case_col + d.pick([-1, 0, 2, 2, 2, 3]), 0)
    stmt_col = max(body_col + d.pick([0, 0, 0, -1, 2]), 0)
    form = d.weighted([('flag', 3), ('marked', 2), ('erased', 1), ('split', 2), ('match', 1), ('plain', 2), ('two', 2),
                       ('same-line', 2), ('plain-split', 2)])
    pad = lambda n: ' ' * n
    pattern = 'On{} On{}' if multi else 'On{}'
    dflt = '_ _' if multi else '_'
    cols = 'a b' if multi else 'a'
    head = 'def f(a: Flag, b: Flag) -> Flag:\n' if multi else 'def f(a: Flag) -> Flag:\n'
    args = 'On{}, On{}' if multi else 'On{}'
    at = pad(body_col)
    if form == 'flag':
        body = f'{at}Off{{}}\n'
    elif form == 'marked':
        body = f'{at}+v : Flag = On{{}}\n{pad(stmt_col)}v\n'
    elif form == 'erased':
        body = f'{at}-v : Flag = On{{}}\n{pad(stmt_col)}Off{{}}\n'
    elif form == 'split':
        marker = d.pick(['+', '-', ''])
        body = f'{at}{marker}u\n{pad(body_col + 2)}: Flag = On{{}}\n{pad(stmt_col)}{"Off{}" if marker == "-" else "u"}\n'
    elif form == 'plain':
        body = f'{at}v : Flag = On{{}}\n{pad(stmt_col)}v\n'
    elif form == 'two':
        body = f'{at}v : Flag = On{{}}\n{pad(stmt_col)}w : Flag = Off{{}}\n{pad(stmt_col + d.pick([0, 0, 2]))}v\n'
    elif form == 'same-line':
        body = f'{at}v : Flag = On{{}}{d.pick(["", " "])}v\n'
    elif form == 'plain-split':
        body = f'{at}v{d.pick(["", " # gap"])}\n{pad(d.pick([0, 1, body_col, body_col + 2]))}{d.pick([": Flag = On{}", "= h(a)"])}\n{pad(stmt_col)}v\n'
    else:
        head = 'def f(p: Opt, b: Flag) -> Flag:\n' if multi else 'def f(p: Opt) -> Flag:\n'
        cols = 'p b' if multi else 'p'
        args = 'Some{On{}}, On{}' if multi else 'Some{On{}}'
        pattern = 'Some{v} _' if multi else 'Some{v}'
        body = f'{at}match v:\n{pad(body_col + 2)}case _: On{{}}\n'
    second = f'{pad(case_col + d.pick([0, 0, 0, 2, -1]))}case {dflt}: Off{{}}\n'
    block = f'{pad(match_col)}match {cols}:\n{pad(case_col)}case {pattern}:\n{body}{second}'
    # the declaration after the match: a blank line, none, on the same line, or at another column
    sep = d.pick(['\n\n'] * 5 + [' \n\n', '\n', '', ' '])
    indent = d.pick([''] * 10 + [' ', '  '])
    src = PRELUDE + head + block.rstrip('\n') + sep + indent + f'def main() -> Flag:\n  f({args})\n'
    return f'layout:{"multi" if multi else "single"}:{form}', src


FAMILIES = [('names', names_program, 1300), ('dead', dead_program, 1300), ('gaps', gaps_program, 1200),
            ('parens', parens_program, 700), ('widths', widths_program, 700), ('layout', layout_program, 900)]


def programs(count=COUNT):
    """(index, class, source, tags): each family gets its share of `count`, in order."""
    rng = random.Random(SEED)
    total = sum(share for _, _, share in FAMILIES)
    index = 0
    for _, family, share in FAMILIES:
        for _ in range(count * share // total):
            made = family(Draw(rng))
            yield index, made[0], made[1], (made[2] if len(made) > 2 else [])
            index += 1


def classify(result, seed=False):
    if seed:
        if result['exit'] == 0 and not result['stderr']:
            return 'Accepted'
        if result['exit'] == 1 and result['stderr'].startswith('Error:'):
            return 'Invalid'
    else:
        outcome = {0: 'Accepted', 2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted',
                   5: 'HostFailure', 6: 'InternalFailure'}.get(result['exit'])
        if outcome == 'Accepted':
            gate.checked(result)
        elif outcome:
            gate.require(result['stderr'].startswith(outcome + '\t') and not result['stdout'], result)
        if outcome in ('Accepted', 'Invalid', 'Unsupported', 'Exhausted'):
            return outcome
    raise AssertionError(('sweep host/internal failure', result))


def check(lanes, directory, count=COUNT, workers=8):
    directory.mkdir(parents=True, exist_ok=True)
    cases = list(programs(count))

    def compare(case):
        index, klass, source, tags = case
        path = directory / f'{index:04d}.bend'
        path.write_text(source)
        seed = gate.run([*gate.SEED, path])
        observed = gate.run([*lanes['native']['check'], path])
        reference, actual = classify(seed, seed=True), classify(observed)
        record = {'index': index, 'class': klass, 'sha256': hashlib.sha256(source.encode()).hexdigest(),
                  'seed': reference, 'knot': actual, 'seed_output': seed['stdout'], 'diagnostic': observed['stderr']}
        if reference == 'Invalid' and actual == 'Accepted':
            record['failure'] = 'seed rejects, Knot accepts'
        elif reference == 'Accepted' and actual == 'Invalid':
            record['failure'] = 'D4: seed accepts, Knot reports Invalid'
        if reference == actual == 'Accepted':
            expected = seed['stdout'].strip()
            tag = {'Off{}': 0, 'On{}': 1, 'Red{}': 0, 'Blue{}': 1}.get(expected)
            gate.require(tag is not None, seed)
            result = gate.run([*lanes['native']['eval'], path, 'main', 65536])
            gate.evaluated(result, {'type_id': 1 if expected in ('Red{}', 'Blue{}') else 0, 'tag': tag, 'result': expected[:-2]})
            record['evaluated'] = tag
        return record

    with ThreadPoolExecutor(max_workers=workers) as pool:
        records = list(pool.map(compare, cases))
    failures = [r for r in records if 'failure' in r]
    classes = {}
    for r in records:
        for key in (r['class'].split(':')[0], r['class']):
            cell = classes.setdefault(key, Counter())
            cell[f"seed-{r['seed']}"] += 1
            cell[f"knot-{r['knot']}"] += 1
    summary = {'random_seed': SEED, 'programs': len(records), 'generator_sha256': gate.digest(Path(__file__)),
               'seed_outcomes': dict(Counter(r['seed'] for r in records)),
               'knot_outcomes': dict(Counter(r['knot'] for r in records)),
               'families': {k: dict(v) for k, v in sorted(classes.items()) if ':' not in k},
               'classes': {k: dict(v) for k, v in sorted(classes.items()) if ':' in k},
               'false_acceptances': sum(r.get('failure') == 'seed rejects, Knot accepts' for r in records),
               'false_invalid': sum(r.get('failure', '').startswith('D4:') for r in records),
               'evaluator_values': sum('evaluated' in r for r in records), 'failures': failures,
               'observations_sha256': hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()}
    (directory / 'observations.json').write_text(json.dumps(records, indent=2) + '\n')
    (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    gate.require(not failures, ('sweep classification mismatch', summary))
    return summary
