#!/usr/bin/env python3
"""Independent reference for the image increment: the knot-image-1 bytes a checked book must encode to.

Nothing here reads src/image.bend or any Bend output. A book's image is derived from two facts the
encoder does not produce: the declarations, read from the source text by a line reader, and the
checked core that Knot's own `check-cli` displays (src/checked-display.bend). The projection of
that display into an erased, slot-numbered plan is vm/check-spec.py's `from_display` (the
independent reading that froze the golden plans); vm/serializer.py lays the plan out.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'vm'))
sys.setrecursionlimit(20_000)


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


codec = load('knot_serializer', ROOT / 'vm/serializer.py')
projection = load('knot_check_spec', ROOT / 'vm/check-spec.py')
REGISTRY = codec.registry()
DIGEST = codec.base_digest(REGISTRY)


def strip(source: str) -> str:
    """The source without `#` comments and blank lines (this profile has no strings)."""
    lines = (line.split('#', 1)[0].rstrip() for line in source.splitlines())
    return '\n'.join(line for line in lines if line.strip()) + '\n'


def declarations(source: str) -> dict:
    """Types and constructors, in declaration order, from the text alone.

    A `type T is Data:` or `Type:` header, then indented `Name{field: Type, -erased: Type}` lines.
    A field is live unless its name starts with `-`."""
    header = re.compile(r'type (\w+) is (?:Data|Type):')
    types, current = [], None
    for line in strip(source).splitlines():
        if line.startswith('type '):
            m = header.fullmatch(line)
            assert m, f'reference: type header {line!r}'
            current = {'name': m[1], 'raw': []}
            types.append(current)
        elif line.startswith('  ') and current is not None:
            m = re.fullmatch(r'\s+(\w+)\{(.*)\}', line)
            assert m, f'reference: constructor line {line!r}'
            fields = []
            for field in filter(None, (f.strip() for f in m[2].split(','))):
                name, _, type_name = field.partition(':')
                assert type_name, f'reference: field {field!r}'
                fields.append((not name.strip().startswith('-'), type_name.strip()))
            current['raw'].append((m[1], fields))
        else:
            current = None
    index = {t['name']: i for i, t in enumerate(types)}
    return {'kind': 'book', 'types': [
        {'kind': 'data', 'name': t['name'],
         'constructors': [{'name': n, 'fields': [index[ty] for live, ty in fields if live]} for n, fields in t['raw']]}
        for t in types]}


def function_names(source: str) -> list:
    return re.findall(r'^def (\w+)\(', strip(source), re.M)


def valued(node, types):
    """SPEC section 3: a Construct has at least one live field. A constructor whose fields are all
    erased has none, so its Construct is the nullary Value (`from_display` lowers it to a `con`)."""
    if not isinstance(node, list) or not node:
        return node
    if node[0] == 'con' and not types[node[1]]['constructors'][node[2]]['fields']:
        return ['value', node[1], node[2]]
    return [valued(part, types) if isinstance(part, list) else part for part in node]


def plan(source: str, display: str) -> dict:
    """The erased, slot-numbered plan of a checked Book: the declarations plus `from_display`."""
    text = strip(source)
    shell = declarations(text)
    functions = projection.from_display(display, {'types': shell['types']}, text, REGISTRY)
    functions = [{**f, 'body': valued(f['body'], shell['types'])} for f in functions]
    assert [f['name'] for f in functions] == function_names(text), 'reference: function order'
    return {'entry': 'book', 'types': shell['types'], 'functions': functions}


def image(source: str, display: str) -> bytes:
    return codec.encode(plan(source, display), DIGEST)
