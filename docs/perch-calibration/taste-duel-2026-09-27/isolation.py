#!/usr/bin/env python3
"""Check that an ablated Bend rendering changes only its intended factor.

Usage: isolation.py MODE BASE VARIANT
  comments  code tokens (comments stripped) are identical; only comments differ
  rename    code tokens identical up to a consistent one-to-one renaming of
            user identifiers; builtins/keywords/literals unchanged
  decls     variant's code is the base's code with whole declarations removed
Only the part above the harness marker is compared. Exit 0 = isolated.
"""
import re, sys

MARKER = '# ---- harness (not shown) ----'
KEYWORDS = {'def', 'match', 'case', 'type', 'is', 'law', 'for', 'import', 'as', 'if', 'else', 'Base'}
BUILTIN_HEADS = {'U32', 'Nat', 'Bool', 'List', 'Maybe', 'Equal', 'Char', 'String', 'I32', 'F32', 'U64'}
BUILTINS = {'Some', 'None', 'True', 'False', 'Nil', 'Con', 'Data', 'Type', 'Kind', 'Prop', 'Unit', 'Empty',
            'Some', 'Pair', 'Sigma', 'Refl'} | BUILTIN_HEADS
TOKEN = re.compile(r'(#[^\n]*)|("(?:[^"\\]|\\.)*")|(\d+n\+|\d+n|\d+)|([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)|(\s+)|(.)', re.S)

def shown(path):
    text = open(path, encoding='utf-8').read()
    return text.split(MARKER, 1)[0]

def tokens(src):
    out = []
    for m in TOKEN.finditer(src):
        com, s, num, ident, ws, other = m.groups()
        if com or ws:
            continue
        if ident:
            out.append(('id', ident))
        else:
            out.append(('lit', s or num or other))
    return out

def fixed(ident):
    head = ident.split('.')[0]
    return ident in KEYWORDS or ident in BUILTINS or head in BUILTIN_HEADS

def decl_blocks(src):
    """Top-level declarations as token tuples (a block starts at a column-0 def/type/law)."""
    blocks, cur = [], []
    for line in src.split('\n'):
        if re.match(r'^(def|type|law|import)\b', line) and cur:
            blocks.append(cur); cur = []
        cur.append(line)
    if cur: blocks.append(cur)
    return [tuple(tokens('\n'.join(b))) for b in blocks if tokens('\n'.join(b))]

def main(mode, base, variant):
    a, b = shown(base), shown(variant)
    ta, tb = tokens(a), tokens(b)
    if mode == 'comments':
        ok = ta == tb
        print('isolated: code tokens identical' if ok else f'NOT isolated: code differs ({len(ta)} vs {len(tb)} tokens)')
        return ok
    if mode == 'rename':
        if len(ta) != len(tb):
            print(f'NOT isolated: token count {len(ta)} vs {len(tb)}'); return False
        fwd, back = {}, {}
        for (ka, va), (kb, vb) in zip(ta, tb):
            if ka != kb or (ka == 'lit' and va != vb):
                print(f'NOT isolated: {va!r} -> {vb!r}'); return False
            if ka == 'id':
                if fixed(va) or fixed(vb):
                    if va != vb:
                        print(f'NOT isolated: builtin/keyword changed {va!r} -> {vb!r}'); return False
                    continue
                if fwd.setdefault(va, vb) != vb or back.setdefault(vb, va) != va:
                    print(f'NOT isolated: inconsistent renaming at {va!r} -> {vb!r}'); return False
        renamed = {k: v for k, v in fwd.items() if k != v}
        print(f'isolated: consistent renaming of {len(renamed)} identifiers')
        for k, v in sorted(renamed.items()): print(f'  {k} -> {v}')
        return True
    if mode == 'decls':
        ba, bb = decl_blocks(a), decl_blocks(b)
        it = iter(ba)
        ok = all(any(x == y for y in it) for x in bb)
        removed = len(ba) - len(bb)
        print(f'isolated: variant keeps {len(bb)} of {len(ba)} declarations unchanged ({removed} removed)' if ok and removed > 0
              else 'NOT isolated: declarations changed or none removed')
        return ok and removed > 0
    raise SystemExit('mode must be comments, rename or decls')

if __name__ == '__main__':
    sys.exit(0 if main(*sys.argv[1:]) else 1)
