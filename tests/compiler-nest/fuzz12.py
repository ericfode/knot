#!/usr/bin/env python3
"""Round-12 differential generator: fixed seed, systematic classes, the pinned seed as the oracle.

Round 11's generator drew binder names, dead rows, gaps, parenthesized columns, widths and layouts. Round
12's review found two more classes by shape; each family below draws the finding's shape with its neighbours.
Every program carries a class `family:...`, and the summary counts seed and Knot outcomes per class.

- plus: a match on one or two columns of fielded types (a pair, a triple, a box, constructors of two arities,
  an option, a list, Data-kind twins), two to four rows whose field slots are a wildcard, a name, a `+name`
  or a nested constructor, bodies that use one binder twice, once or not at all, and a catch-all row half of
  the time. `+` may stand in any row and any slot, so the seed's rule (the first row of a constructor's split
  marks its fields for every row below; a variable row marks its column) is drawn across every split.
- suffix: a complete term (a name, a constructor, a call) followed by one of the seed's term suffixes (each
  infix operator, a call, an index, an offload, a lambda), a junk token the seed rejects, or a `+name` term,
  after a gap of nothing, a space, a line break at a column, a comment or a blank line. It stands as an
  inline or own-line arm body, a let value, a call argument or a def body, in a row the lowering keeps or
  discards, in a one- or two-column match.

A false acceptance (seed rejects, Knot accepts), a false Invalid (seed accepts, Knot Invalid) or a host or
internal failure fails the gate. Accepted programs also run through the Bend evaluator, in both lanes.

Two seed-accepted shapes are open D4 families and are not drawn (src/SPEC.md): a spaced `+` or `-` that starts
the line after a let's value, which round 10's `detached_marker` law pins as `Invalid detached-marker`, and a term that starts with `?`, `@`
or a backslash, or a `+` marker, as the next argument after whitespace.
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random

import check as gate
import fuzz11

SEED = 0x4E455354 ^ 0x12
COUNT = 3000

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
  B{x: Flag}

type Opt is Type:
  N{}
  S{v: Flag}

type Lst is Type:
  Nl{}
  Cn{h: Flag, t: Lst}

type Dat is Data:
  Dt{l: Flag, r: Flag}

type DBx is Data:
  DB{p: Dat}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def u_pair(p: Pair) -> Flag:
  match p:
    case P{l, r}: both(l, r)

def u_trip(p: Trip) -> Flag:
  match p:
    case T3{a, b, c}: both(a, both(b, c))

def u_box(p: Box) -> Flag:
  match p:
    case Bx{q}: u_pair(q)

def u_two(p: Two) -> Flag:
  match p:
    case A{x, y}: both(x, y)
    case B{x}: x

def u_opt(p: Opt) -> Flag:
  match p:
    case N{}: On{}
    case S{v}: v

def u_lst(p: Lst) -> Flag:
  match p:
    case Nl{}: On{}
    case Cn{h, t}: both(h, u_lst(t))

def u_dat(p: Dat) -> Flag:
  match p:
    case Dt{l, r}: both(l, r)

def u_dbx(p: DBx) -> Flag:
  match p:
    case DB{q}: u_dat(q)

'''
# type -> (constructors [(name, field types)], the function that consumes a value, whether `+` may raise its binders)
TYPES = {
    'Flag': ([('Off', []), ('On', [])], None, True),
    'Pair': ([('P', ['Flag', 'Flag'])], 'u_pair', False),
    'Trip': ([('T3', ['Flag', 'Flag', 'Flag'])], 'u_trip', False),
    'Box': ([('Bx', ['Pair'])], 'u_box', False),
    'Two': ([('A', ['Flag', 'Flag']), ('B', ['Flag'])], 'u_two', False),
    'Opt': ([('N', []), ('S', ['Flag'])], 'u_opt', False),
    'Lst': ([('Nl', []), ('Cn', ['Flag', 'Lst'])], 'u_lst', False),
    'Dat': ([('Dt', ['Flag', 'Flag'])], 'u_dat', True),
    'DBx': ([('DB', ['Dat'])], 'u_dbx', True),
}
COLUMN_TYPES = ['Pair', 'Trip', 'Box', 'Two', 'Opt', 'Lst', 'Dat', 'DBx', 'Flag']
NAMES = 'abcdefgh'


def use(ty, name):
    consumer = TYPES[ty][1]
    return name if consumer is None else f'{consumer}({name})'


def value(d, ty, depth=0):
    """A constructor term of type `ty`, drawing fields at random."""
    ctors = TYPES[ty][0]
    name, fields = d.pick(ctors)
    if ty == 'Lst' and name == 'Cn' and depth >= 2:
        name, fields = ctors[0]
    return name + '{' + ', '.join('On{}' if f == 'Flag' and d.chance(2) else 'Off{}' if f == 'Flag' else value(d, f, depth + 1)
                                  for f in fields) + '}'


class Row:
    def __init__(self):
        self.binders = []
        self.marks = []            # where a `+` stands: 'field', 'top'


def pattern(d, ty, row, depth, top):
    """A pattern of type `ty`: a constructor with sub-patterns, a wildcard, a name or a `+name`."""
    ctors = TYPES[ty][0]
    if d.rng.random() < (0.85 if top else 0.6) and depth < 3:
        name, fields = d.pick(ctors)
        return name + '{' + ', '.join(pattern(d, f, row, depth + 1, False) for f in fields) + '}'
    roll = d.rng.random()
    if roll < 0.2:
        return '_'
    label = NAMES[len(row.binders) % len(NAMES)] + ('' if len(row.binders) < len(NAMES) else str(len(row.binders)))
    row.binders.append((label, ty))
    raised = d.rng.random() < (0.45 if TYPES[ty][2] else 0.06)
    if raised:
        row.marks.append('top' if top else 'field')
    return ('+' if raised else '') + label


def body(d, row):
    if not row.binders or d.chance(8):
        return d.pick(['On{}', 'Off{}'])
    name, ty = d.pick(row.binders)
    roll = d.rng.random()
    if roll < 0.6:
        return f'both({use(ty, name)}, {use(ty, name)})'
    if roll < 0.8:
        other, oty = d.pick(row.binders)
        return f'both({use(ty, name)}, {use(oty, other)})'
    return use(ty, name)


def plus_program(d):
    cols = d.pick([1, 1, 2])
    types = [d.pick(COLUMN_TYPES) for _ in range(cols)]
    rows, marks = [], []
    for _ in range(d.pick([2, 2, 3, 4])):
        row = Row()
        patterns = [pattern(d, t, row, 0, True) for t in types]
        rows.append(' '.join(patterns) + ': ' + body(d, row))
        marks.append(row.marks)
    if d.chance(2):
        rows.append(' '.join('_' for _ in types) + ': On{}')
    first, later = bool(marks[0]), any(marks[1:])
    kind = ('first-row' if first else 'later-row' if later else 'no-plus')
    params = ', '.join(f'x{i}: {t}' for i, t in enumerate(types))
    scrutinees = ' '.join(f'x{i}' for i in range(cols))
    args = ', '.join(value(d, t) for t in types)
    src = (PLUS_PRE + f'def f({params}) -> Flag:\n  match {scrutinees}:\n' + ''.join(f'    case {r}\n' for r in rows)
           + f'\ndef main() -> Flag:\n  f({args})\n')
    kinds = 'data' if all(TYPES[t][2] for t in types) else 'type'
    return f'plus:{cols}col:{kind}:{kinds}', src


# ---------------------------------------------------------------------------------------- suffix
SUFFIX_PRE = '''type Flag is Data:
  Off{}
  On{}

type Pr is Type:
  Pr{l: Flag, r: Flag}

def h(a: Flag) -> Flag:
  a

'''
LEFTS = ['a', 'On{}', 'h(a)', 'x0', 'Pr{a, a}']
OPERATORS = ['->', '&', '|', '||', '&&', '<', '<=', '>', '>=', '<>', '++', '<&>', '.|.', '.^.', '.&.', '<<', '>>', '+', '-', '*', '/', '%']
CALLS = ['(a)', '(a, a)', '[0n]', '!(a)', '=> a', '<- a']
# tokens the seed rejects after a term, and markers that touch a name
JUNK = ['== a', '= a', ', a', '. a', '~ a', ': Flag', ')', '}', '-a', '^ a', '@ a', '$ a', '!', ']']
PLUS_TERMS = ['+x0', '+ x0', '-x0', '+x0 y', '+h(a)', '+x0(a)', '+(a)', '+ (a)', '+\n      (a)', '+ # c\n      (a)', '+\n      +a', '-\n      (a)']
GAP_COLUMNS = [0, 2, 4, 6, 8, 12]


def suffix_text(d, site):
    """A term and what follows it: the seed accepts most of them in a row it discards."""
    gap = d.weighted([('space', 8), ('none', 3), ('break', 5), ('comment', 2), ('blank', 1)])
    column = d.pick(GAP_COLUMNS)
    joint = {'space': ' ', 'none': '', 'break': '\n' + ' ' * column, 'comment': ' # c\n' + ' ' * column,
             'blank': '\n\n' + ' ' * column}[gap]
    # After a let's value, a spaced `+` or `-` at the start of the next line reads as an operator to the seed and
    # as a detached marker here: round 10's `detached_marker` law pins `Invalid`, an open D4 family (SPEC).
    operators = [o for o in OPERATORS if not (site == 'let' and gap in ('break', 'comment', 'blank') and o[0] in '+-')]
    roll = d.rng.random()
    if roll < 0.12:
        lead = d.pick(PLUS_TERMS)
        if d.chance(3):
            return 'suffix:plus-term:alone', lead
        return f'suffix:plus-term:{gap}', lead + joint + d.pick(operators) + ' a'
    left = d.pick(LEFTS)
    if roll < 0.62:
        return f'suffix:operator:{gap}', left + joint + d.pick(operators) + ' a'
    if roll < 0.82:
        return f'suffix:call:{gap}', left + joint + d.pick(CALLS)
    return f'suffix:junk:{gap}', left + joint + d.pick(JUNK)


def suffix_program(d):
    site = d.weighted([('inline', 5), ('own', 3), ('let', 4), ('arg', 4), ('single', 2), ('body', 2), ('nested', 2)])
    klass, term = suffix_text(d, site)
    reach = 'live' if site == 'body' or d.chance(4) else 'dead'
    if site == 'body':
        src = SUFFIX_PRE + f'def f(a: Flag) -> Flag:\n  {term}\n\ndef main() -> Flag:\n  f(On{{}})\n'
        return f'{klass}:{site}:live', src
    two = site != 'single'
    head = ('def f(a: Flag, b: Flag) -> Flag:\n  match a b:\n' if two else 'def f(a: Flag) -> Flag:\n  match a:\n')
    catch, row = ('_ _' if two else '_'), ('Off{} Off{}' if two else 'Off{}')
    call = 'f(On{}, On{})' if two else 'f(On{})'
    arm = {'inline': f' {term}', 'own': f'\n      {term}', 'let': f'\n      u : Flag = {term}\n      On{{}}', 'arg': f' h({term})',
           'single': f' {term}', 'nested': f'\n      match a:\n        case _: {term}'}[site]
    if reach == 'dead':
        rows = f'    case {catch}: On{{}}\n    case {row}:{arm}\n'
    else:
        rows = f'    case {row}:{arm}\n    case {catch}: On{{}}\n'
    return f'{klass}:{site}:{reach}', SUFFIX_PRE + head + rows + f'\ndef main() -> Flag:\n  {call}\n'


FAMILIES = [('plus', plus_program, 1800), ('suffix', suffix_program, 1200)]


def programs(count=COUNT):
    """(index, class, source): each family gets its share of `count`, in order."""
    rng = random.Random(SEED)
    total = sum(share for _, _, share in FAMILIES)
    index = 0
    for _, family, share in FAMILIES:
        for _ in range(count * share // total):
            made = family(fuzz11.Draw(rng))
            yield index, made[0], made[1]
            index += 1


def check(lanes, directory, count=COUNT, workers=8):
    directory.mkdir(parents=True, exist_ok=True)
    cases = list(programs(count))

    def compare(case):
        index, klass, source = case
        path = directory / f'{index:04d}.bend'
        path.write_text(source)
        seed = gate.run([*gate.SEED, path])
        observed = gate.run([*lanes['native']['check'], path])
        reference, actual = fuzz11.classify(seed, seed=True), fuzz11.classify(observed)
        record = {'index': index, 'class': klass, 'sha256': hashlib.sha256(source.encode()).hexdigest(),
                  'seed': reference, 'knot': actual, 'seed_output': seed['stdout'], 'diagnostic': observed['stderr']}
        if reference == 'Invalid' and actual == 'Accepted':
            record['failure'] = 'seed rejects, Knot accepts'
        elif reference == 'Accepted' and actual == 'Invalid':
            record['failure'] = 'D4: seed accepts, Knot reports Invalid'
        if reference == actual == 'Accepted':
            expected = seed['stdout'].strip()
            tag = {'Off{}': 0, 'On{}': 1}.get(expected)
            gate.require(tag is not None, seed)
            for lane in ('native', 'bun'):
                result = gate.run([*lanes[lane]['eval'], path, 'main', 65536])
                gate.evaluated(result, {'type_id': 0, 'tag': tag, 'result': expected[:-2]})
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
