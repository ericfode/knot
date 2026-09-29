"""Deterministic program families for the seed differential (DESIGN 3.1, family L).

Every program is plain text, generated from fixed grids and operators. The fast tier's corpus is a function of
constants and of the tool's own registry only (`fixed_programs`): the same programs on every head, base and host, so
the pinned seed's verdicts on them can be frozen in tests/prechecks/registry/seed-verdicts.jsonl. Grids follow the classify-2 reviewer's grid (parameters, fields, tails after a constructor head, return
types, annotations) and add binder spellings, empty datatypes, let marks and literal forms. Operators perturb a
seed-accepted text at token boundaries: a gap (space, tab, newline plus indent, comment plus newline, CRLF) before
`{`, `->`, `+`/`-`, `<`, `>`, `&`, `|`, `:` and `=`, and literal substitutions (0x7F, 0x80, U+00A0, backslash-brace).
"""
from __future__ import annotations

import itertools
import random
import re
from typing import Iterator

HEAD = 'type Flag is Data:\n  Off{}\n  On{}\n\ntype Cell is Data:\n  Cell{value: Flag}\n\n'
BINDERS = ['~{}: Flag', '{}: Flag', '-{}: Flag', '+{}: Flag', '~{}:', '~', '{}', '{}: List<Flag>', '~{}: List<Flag>',
           '{}: Flag -> Flag', '~ {}: Flag']
SEPS = [', ', ',', ' ', ',\n  ', ', ~']
TAILS = ['= x', '== x', '=> x', '= = x', '= > x', '=< x', '=( x)', '=\n    x', '= ; x', '=', '==', '=>', '= x ; On{}', '=x',
         '= +x', '= -x', '= ~x', '= Cell{x}', '= (x)', '= [x]', '= x => x', '= {x}', '= %x', '= @x', '= ?x', '= !x',
         '= =x', '= >x', '= <x', '= :x', '= ,x', '= )x', '= }x', '= &x', '= |x', '= *x', '= /x', '= .x', '= 0', '= 1n']
HEADS = ['Cell{v}', 'On{}', 'Cell{+v}', 'Cell{Cell{v}}']
TYPES = ['Flag', 'Flag<Flag>', 'Flag -> Flag', 'Flag & Flag', 'Flag | Flag', '(Flag)', '+Flag', 'Flag<Flag> -> Flag', 'Type',
         '@x: Flag -> Flag', 'Flag<', 'Flag<>', 'Flag<Flag', 'Flag<Flag,>', 'Flag<Flag, Flag>', 'Flag<(Flag)>',
         'Flag<Flag<Flag>>', '[Flag]', 'Flag Flag', 'Flag<Flag> & Flag', 'Flag.x', 'Flag<~x>', 'Flag<-A: Type>', '&0',
         'Flag<&1>', 'Flag < x', 'Flag<x>=', '{Flag}', '?h', 'Flag<Flag>>']
SPELLINGS = ['a', 'a.b', 'a.', '_', 'Off', 'On', 'x.y.z', '~a', '-a', '+a', 'a b', 'a,b', '0a', 'A', 'a\u00a0b'.encode('ascii', 'backslashreplace').decode()]
MARKS = ['', '~', '-', '+', '&', '~ ', '- ']
VALUES = ['On{}', 'Cell{On{}}', 'x', 'y', '[On{}]', '(On{})', '{On{}}', 'On {}', 'On{ }']

Program = tuple[str, str, str]           # (family, key, text)


def params() -> Iterator[Program]:
    for n in (1, 2, 3):
        for combo in itertools.product(BINDERS, repeat=n):
            for sep in (SEPS if n > 1 else [', ']):
                ps = sep.join(b.format(chr(97 + i)) if '{}' in b else b for i, b in enumerate(combo))
                yield 'params', ps, f'{HEAD}def f({ps}) -> Flag:\n  On{{}}\n'


def fields() -> Iterator[Program]:
    for n in (1, 2):
        for combo in itertools.product(BINDERS, repeat=n):
            ps = ', '.join(b.format(chr(97 + i)) if '{}' in b else b for i, b in enumerate(combo))
            yield 'fields', ps, f'{HEAD}type Box is Data:\n  Box{{{ps}}}\n\n'


def tails() -> Iterator[Program]:
    for head in HEADS:
        for tail in TAILS:
            yield 'tails', f'{head} {tail}', f'{HEAD}def take(x: Cell) -> Flag:\n  {head} {tail}\n  On{{}}\n'


def returns() -> Iterator[Program]:
    for t in TYPES:
        yield 'return', t, f'{HEAD}def f() -> {t}:\n  On{{}}\n'


def annotations() -> Iterator[Program]:
    for t in TYPES:
        for q in ('', '-', '+'):
            yield 'annot', q + t, f'{HEAD}def f() -> Flag:\n  {q}x: {t} = On{{}}\n  x\n'


def binders() -> Iterator[Program]:
    for s in SPELLINGS:
        yield 'binder', f'param {s}', f'{HEAD}def f({s}: Flag) -> Flag:\n  On{{}}\n'
        yield 'binder', f'field {s}', f'{HEAD}type Box is Data:\n  Box{{{s}: Flag}}\n\n'
        yield 'binder', f'let {s}', f'{HEAD}def f() -> Flag:\n  {s} = On{{}}\n  On{{}}\n'
        yield 'binder', f'case {s}', f'{HEAD}def f(c: Cell) -> Flag:\n  match c:\n    case Cell{{{s}}}: On{{}}\n'


def empties() -> Iterator[Program]:
    yield 'empty', 'alone', 'type Void is Data:\n\ndef main() -> Void:\n  ?\n'
    yield 'empty', 'declared', f'{HEAD}type Void is Data:\n\ndef f() -> Flag:\n  On{{}}\n'
    yield 'empty', 'param', f'{HEAD}type Void is Data:\n\ndef f(v: Void) -> Flag:\n  On{{}}\n'
    yield 'empty', 'match', f'{HEAD}type Void is Data:\n\ndef f(v: Void) -> Flag:\n  match v:\n'
    yield 'empty', 'field', f'{HEAD}type Void is Data:\n\ntype Box is Data:\n  Box{{v: Void}}\n'
    yield 'empty', 'typed-binder', f'{HEAD}type Void is Data:\n\ndef f() -> Flag:\n  x: Void = ?\n  On{{}}\n'
    yield 'empty', 'unused-generic', f'{HEAD}type Box<-A: Type> is Type:\n  Box{{a: A}}\n\ndef f() -> Flag:\n  On{{}}\n'


def lets() -> Iterator[Program]:
    for mark, value in itertools.product(MARKS, VALUES):
        yield 'let', f'{mark!r} {value}', f'{HEAD}def f() -> Flag:\n  {mark}x = {value}\n  On{{}}\n'
        yield 'let', f'dead {mark!r} {value}', f'{HEAD}def f() -> Flag:\n  On{{}}\n  {mark}x = {value}\n'


def literals() -> Iterator[Program]:
    forms = ['0', '7', '0x7F', '0x80', '0xFFFFFFFF', '4294967296', '1_000', "'a'", "'\\u{80}'", "'\\u{d800}'", '"a"', '"a\\{b"',
             '"\u00a0"'.encode('ascii', 'backslashreplace').decode(), '0n', '3n', '2n+1', '1n+n']
    for form in forms:
        yield 'literal', f'u32 {form}', f'import Base\n\ndef f() -> U32:\n  {form}\n'
        yield 'literal', f'char {form}', f'import Base\n\ndef f() -> Char:\n  {form}\n'
        yield 'literal', f'string {form}', f'import Base\n\ndef f() -> String:\n  {form}\n'
        yield 'literal', f'match {form}', f'import Base\n\ndef f(x: U32) -> U32:\n  match x:\n    case {form}: 1\n'


GRIDS = {'params': params, 'fields': fields, 'tails': tails, 'return': returns, 'annot': annotations, 'binder': binders,
         'empty': empties, 'let': lets, 'literal': literals}
# Families that a change to these source files is most likely to disturb.
FOCUS = {'parse': ('params', 'fields', 'tails', 'return', 'annot', 'binder', 'literal'),
         'lex': ('literal', 'params', 'tails'),
         'check': ('let', 'empty', 'binder'), 'scope': ('let', 'binder'), 'catalog': ('empty', 'fields'),
         'driver': ('literal',), 'patterns': ('binder', 'tails')}

GAPS = [' ', '\t', '\n  ', ' # c\n  ', '\r\n']
BOUNDARIES = [r'(?<=[A-Za-z0-9_\.])\{', r'->', r'(?<=[0-9n])\+', r'(?<=[0-9n])-', r'(?<=[A-Za-z])<', r'(?<=[A-Za-z0-9])>', r'&',
              r'\|', r'(?<=[a-z0-9_)])\s*:(?=\s)', r'(?<=[a-z0-9_])\s*=(?=\s)']
SUBSTITUTIONS = ['0x7F', '0x80', '\\u{a0}', '\\{', '\\u{80}', '\u00a0'.encode('ascii', 'backslashreplace').decode()]


def gap_variants(text: str, limit: int = 6, rng: random.Random | None = None) -> Iterator[Program]:
    """O1: a gap inserted at token boundaries of `text`, at most `limit` variants."""
    rng = rng or random.Random(0)
    spots = sorted({m.start() for pattern in BOUNDARIES for m in re.finditer(pattern, text)})
    rng.shuffle(spots)
    for spot in spots[:limit]:
        gap = rng.choice(GAPS)
        yield 'lexical', f'gap@{spot}:{gap!r}', text[:spot] + gap + text[spot:]


def literal_variants(text: str, limit: int = 4, rng: random.Random | None = None) -> Iterator[Program]:
    """O2: substitute a literal's body (strings and chars) with a hostile spelling."""
    rng = rng or random.Random(0)
    spans = []
    for m in re.finditer(r"\"((?:[^\"\\\n]|\\.)*)\"|'((?:[^'\\\n]|\\.)*)'", text):
        spans.append(m.span(1) if m.group(1) is not None else m.span(2))
    rng.shuffle(spans)
    for a, b in spans[:limit]:
        sub = rng.choice(SUBSTITUTIONS)
        yield 'literal-op', f'sub@{a}:{sub}', text[:a] + sub + text[b:]


def layout_variants(text: str) -> Iterator[Program]:
    """O3/O4: move a type below its first use; append an unused empty datatype."""
    blocks = [b for b in re.split(r'\n\n+', text.strip('\n')) if b.strip()]
    for i, block in enumerate(blocks):
        if block.startswith('type ') and i + 1 < len(blocks):
            moved = blocks[:i] + blocks[i + 1:] + [block]
            yield 'layout', f'move-type-{i}', '\n\n'.join(moved) + '\n'
            break
    yield 'layout', 'append-empty', text.rstrip('\n') + '\n\ntype Void is Data:\n'


FIXED_SEED = 0x4B6E6F74          # 'Knot': never derived from a commit, a tree, a cache or the changed paths
GRID_TOTAL = 560                 # grid programs in the fast corpus (each family gets an equal share)
OPERATOR_TOTAL = 260             # operator variants of the frozen registry in the fast corpus


def fixed_programs(registry_texts: list[str]) -> list[Program]:
    """The generated part of the fast corpus: grids at equal quotas, plus operator variants of the accepted registry
    programs, all sampled with FIXED_SEED. A function of its argument and constants: nothing about the checked branch."""
    grid = grid_programs(quotas(GRID_TOTAL, []), FIXED_SEED)
    rng = random.Random(FIXED_SEED)
    operators: list[Program] = []
    for text in registry_texts:
        if len(text) > 4000:
            continue
        operators += list(gap_variants(text, 3, rng)) + list(literal_variants(text, 1, rng)) + list(layout_variants(text))[:1]
    return grid + sample(operators, OPERATOR_TOTAL, FIXED_SEED + 1)


def sample(programs: list[Program], limit: int, seed: int) -> list[Program]:
    rng = random.Random(seed)
    if len(programs) <= limit:
        return programs
    picked = rng.sample(range(len(programs)), limit)
    return [programs[i] for i in sorted(picked)]


def grid_programs(quota: dict[str, int], seed: int) -> list[Program]:
    """Up to `quota[family]` programs per grid family, sampled deterministically."""
    out = []
    for family, count in quota.items():
        if count <= 0:
            continue
        rows = list(GRIDS[family]())
        out += sample(rows, count, seed ^ hash_family(family))
    return out


def hash_family(family: str) -> int:
    return sum(ord(c) * 31 ** i for i, c in enumerate(family)) & 0xFFFFFF


def quotas(total: int, changed: list[str]) -> dict[str, int]:
    """Split `total` across the grid families, doubling those the changed sources are likely to disturb."""
    weights = {family: 1 for family in GRIDS}
    for path in changed:
        stem = path.rsplit('/', 1)[-1].removesuffix('.bend').split('-')[0]
        for family in FOCUS.get(stem, ()):
            weights[family] = 2
    unit = total / sum(weights.values())
    return {family: max(int(unit * w), 1) for family, w in weights.items()}
