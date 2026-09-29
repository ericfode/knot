#!/usr/bin/env python3
"""Exhaustive gap search: not a gate, a tool for the next reviewer's question "every pair of adjacent tokens".

Each base is a complete program; for every pair of adjacent tokens inside its match region (from the first
`match` to the last def before `main`) the search inserts each of eight gaps (a line break, a break and
indent, a comment, a blank line, a space, a comma, a spaced comma, nothing) and compares the pinned seed with a
Knot checker binary. A false acceptance (seed rejects, Knot Checked), a false Invalid (seed accepts, Knot
Invalid) or a host failure is reported with its base; with a merge-base binary each false Invalid is also
labelled `main-era` (that binary reports Invalid too) or `BRANCH`.

    python3 tests/compiler-nest/gapsearch.py CHECK-BINARY OUTDIR [MERGE-BASE-BINARY]

Bases cover multi-scrutinee headers of names, commas, calls and parenthesized terms; row patterns of names,
constructors, fields, `+` marks, Nat literals and parentheses; nested matches in unreachable rows; lets; and
call and constructor arguments. The receipt of the round-11 run is `receipts/round11-gapsearch.json`.
"""
import collections
import hashlib
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = ['bun', str(ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts')]
ENV = {**os.environ, 'BEND_NO_TELEMETRY': '1'}

PRE = '''type Flag is Data:
  Off{}
  On{}

type Nat is Data:
  Zero{}
  Succ{pred: Nat}

type Opt is Data:
  None{}
  Some{v: Flag}

type Pr is Data:
  Pr{l: Flag, r: Flag}

def h(a: Flag) -> Flag:
  a

def g(a: Flag, b: Flag) -> Flag:
  a

'''


def prog(defs, call='f(On{}, Off{})', result='Flag'):
    return PRE + defs + f'\ndef main() -> {result}:\n  {call}\n'


def two(body, call='f(On{}, Off{})', sig='a: Flag, b: Flag'):
    return prog(f'def f({sig}) -> Flag:\n{body}', call)


DEAD2 = '  match a b:\n    case _ _: Off{}\n    case On{} _:\n'
BASES = {
    'names2': two('  match a b:\n    case x y: On{}\n'),
    'names2-two-rows': two('  match a b:\n    case On{} y: On{}\n    case x _: Off{}\n'),
    'names3': two('  match a b c:\n    case x y z: On{}\n', 'f(On{}, Off{}, On{})', 'a: Flag, b: Flag, c: Flag'),
    'comma2': two('  match a, b:\n    case x, y: On{}\n'),
    'plus2': two('  match a b:\n    case +x y: On{}\n'),
    'plus2b': two('  match a b:\n    case x +y: On{}\n'),
    'field2': prog('def f(p: Opt, b: Flag) -> Flag:\n  match p b:\n    case Some{v} y: On{}\n    case None{} _: Off{}\n',
                   'f(Some{On{}}, Off{})'),
    'ctor2': two('  match a b:\n    case On{} Off{}: On{}\n    case _ _: Off{}\n'),
    'nat2': prog('def f(n: Nat, b: Flag) -> Flag:\n  match n b:\n    case Succ{m} y: On{}\n    case Zero{} _: Off{}\n',
                 'f(Succ{Zero{}}, Off{})'),
    'numeral-dead': two(DEAD2 + '      match a b:\n        case 0n _: On{}\n        case _ _: Off{}\n'),
    'numeral2-dead': two(DEAD2 + '      match a b:\n        case _ 1n: On{}\n        case _ _: Off{}\n'),
    'dead-names': two(DEAD2 + '      match a b:\n        case x y: On{}\n'),
    'dead-call': two(DEAD2 + '      match h(a) b:\n        case x y: On{}\n'),
    'dead-call-arg': two(DEAD2 + '      match g(a, b) b:\n        case x y: On{}\n'),
    'dead-paren': two(DEAD2 + '      match a (b):\n        case x y: On{}\n'),
    'dead-row-paren': two(DEAD2 + '      match a b:\n        case x (y): On{}\n'),
    'dead-plus-let': two(DEAD2 + '      +q = a\n      On{}\n'),
    'dead-let-typed': two(DEAD2 + '      q : Flag = a\n      On{}\n'),
    'let-live': two('  match a b:\n    case On{} y:\n      q : Flag = y\n      q\n    case _ _: Off{}\n'),
    'let-live-plus': two('  match a b:\n    case On{} y:\n      +q = y\n      q\n    case _ _: Off{}\n'),
    'let-live-erased': two('  match a b:\n    case On{} y:\n      -q = y\n      On{}\n    case _ _: Off{}\n'),
    'nested-live': two('  match a b:\n    case On{} y:\n      match y:\n        case On{}: On{}\n        case Off{}: Off{}\n    case _ _: Off{}\n'),
    'arm-call': two('  match a b:\n    case On{} y: g(y, a)\n    case _ _: Off{}\n'),
    'arm-ctor-args': prog('def f(a: Flag, b: Flag) -> Pr:\n  match a b:\n    case On{} y: Pr{y, a}\n    case _ _: Pr{a, b}\n',
                          result='Pr'),
    'dead-field': prog('def f(p: Opt, b: Flag) -> Flag:\n  match p b:\n    case _ _: Off{}\n    case Some{v} _:\n      match v b:\n        case x y: On{}\n',
                       'f(Some{On{}}, Off{})'),
    'dead-arity': two(DEAD2 + '      match a b:\n        case On{} On{} On{}: On{}\n        case _ _: Off{}\n'),
    'width-live': two('  match a b:\n    case x: On{}\n    case _ _: Off{}\n'),
    'comment-dead': two(DEAD2 + '      match a b: # c\n        case x y: On{}\n'),
    'let-call-live': two('  match a b:\n    case On{} y:\n      q : Flag = h(y)\n      q\n    case _ _: Off{}\n'),
    'let-call-dead': two(DEAD2 + '      q : Flag = h (a)\n      q\n'),
    'let-plain-call-dead': two(DEAD2 + '      q = g(a, h(b))\n      q\n'),
    'arg-nested-call': two('  match a b:\n    case On{} y: g(h(y), a)\n    case _ _: Off{}\n'),
    # the parenthesis shapes that the seed reads as the next term when the line breaks before them
    'paren-dead-one': two(DEAD2 + '      match h (a):\n        case _: On{}\n'),
    'paren-dead-tight': two(DEAD2 + '      match h(a):\n        case _: On{}\n'),
    'paren-dead-two-call': two(DEAD2 + '      match g(a, b) (a):\n        case _ _: On{}\n'),
    'paren-scrutinee': two('  match a (b):\n    case _ _: On{}\n'),
    'paren-row': two('  match a b:\n    case x (y): On{}\n'),
    'paren-row-first': two('  match a b:\n    case (x) y: On{}\n'),
    'paren-row-single': two('  match a b:\n    case (x): On{}\n', 'f(On{}, Off{})'),
    'paren-field': prog('def f(a: Pr) -> Flag:\n  match a:\n    case Pr{(x), y}: On{}\n', 'f(Pr{On{}, Off{}})'),
    'paren-argument-dead': two('  match a:\n    case _: Off{}\n    case On{}: g(a, (a))\n', 'f(On{}, Off{})', 'a: Flag, b: Flag'),
    'paren-call-argument-dead': two('  match a:\n    case _: Off{}\n    case On{}: g(h (a), a)\n'),
    'paren-ctor-then-paren-dead': two(DEAD2 + '      match Pr{a, b} (a):\n        case _ _: On{}\n'),
}
TOKEN = re.compile(r'(\s+|#[^\n]*|[A-Za-z_][A-Za-z0-9_.]*|\d[A-Za-z0-9_.]*|.)', re.S)
GAPS = ['\n', '\n  ', ' # c\n', '\n\n', ' ', ',', ' , ', '']


def programs():
    jobs = []
    for name, source in BASES.items():
        tokens = TOKEN.findall(source)
        first = next(i for i, t in enumerate(tokens) if t == 'match')
        last = max(i for i, t in enumerate(tokens) if t == 'main') - 4
        jobs.append((name, 'base', source))
        for i in range(first, last):
            if tokens[i].isspace():
                continue    # a gap goes after a token, before the next one
            if i + 1 < len(tokens) and tokens[i + 1].isspace() and '\n' in tokens[i + 1]:
                continue    # never join across a structural line end
            for k, gap in enumerate(GAPS):
                jobs.append((name, f'{i}g{k}', ''.join(tokens[:i + 1]) + gap + ''.join(tokens[i + 1:])))
    return jobs


def run(command):
    try:
        done = subprocess.run(command, capture_output=True, text=True, cwd=ROOT, env=ENV, timeout=90)
        return done.returncode, done.stderr
    except subprocess.TimeoutExpired:
        return None, 'timeout'


def main():
    check, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    merge_base = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else None
    out.mkdir(parents=True, exist_ok=True)
    jobs = programs()

    def one(job):
        name, tag, source = job
        path = out / f'{name}-{tag}.bend'
        path.write_text(source)
        seed_code, seed_err = run([*SEED, path])
        code, err = run([check, path])
        seed_ok = seed_code == 0 and not seed_err
        if not (seed_ok or (seed_code == 1 and seed_err.startswith('Error:'))):
            path.unlink()
            return name, 'seed-failure', ''
        knot = {0: 'Accepted', 2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted'}.get(code, 'Host')
        klass = ('seed-Accepted' if seed_ok else 'seed-Rejected') + ' ' + knot
        label = ''
        if not seed_ok and knot == 'Accepted':
            klass = 'FALSE-ACCEPTANCE'
        elif seed_ok and knot == 'Invalid':
            klass = 'FALSE-INVALID'
            if merge_base:
                label = 'main-era' if run([merge_base, path])[0] == 2 else 'branch-introduced'
        elif knot == 'Host':
            klass = 'HOST-FAILURE'
        if klass not in ('FALSE-ACCEPTANCE', 'FALSE-INVALID', 'HOST-FAILURE'):
            path.unlink()
        return name, klass, label

    with ThreadPoolExecutor(12) as pool:
        results = list(pool.map(one, jobs))
    classes = collections.Counter(klass for _, klass, _ in results)
    per_base = {name: dict(collections.Counter(klass for n, klass, _ in results if n == name)) for name in BASES}
    receipt = {'programs': len(results), 'bases': len(BASES), 'gaps': GAPS, 'classes': dict(classes),
               'false_acceptances': classes['FALSE-ACCEPTANCE'], 'false_invalid': classes['FALSE-INVALID'],
               'host_failures': classes['HOST-FAILURE'], 'per_base': per_base,
               'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('per_base', 'gaps')}, indent=1))


if __name__ == '__main__':
    main()
