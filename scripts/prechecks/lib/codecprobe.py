#!/usr/bin/env python3
"""Family V's reference-codec probe (R11 reference-crash, R12 roundtrip), run in a child process with a memory limit.

    python3 codecprobe.py <export dir> <plans.json> <out.json>

`plans.json` is a list of {name, plan, strict}. For each plan the tree's own `vm/serializer.py` encodes it, decodes the
result, and (for a `strict` plan, a golden) compares. The codec declares `Malformed` and `Exhausted` for images and
raises `ValueError` to refuse a plan it can see is not a plan; anything else, including AttributeError, IndexError,
MemoryError and RecursionError, is a crash of the reference, which every lane of the VM is judged against.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def outcome(codec, plan, digest, registry, strict=False):
    declared = tuple(getattr(codec, name) for name in ('Malformed', 'Exhausted') if hasattr(codec, name)) + (ValueError,)
    try:
        data = codec.encode(plan, digest)
    except declared as error:
        return {'kind': 'declared', 'stage': 'encode', 'error': type(error).__name__}
    except BaseException as error:                      # noqa: BLE001 - the point is to see every failure of the reference
        return {'kind': 'crash', 'stage': 'encode', 'error': f'{type(error).__name__}: {str(error)[:100]}'}
    try:
        again = codec.decode(data, digest)
    except declared as error:
        return {'kind': 'roundtrip', 'stage': 'decode', 'error': f'decode refuses encode\'s own output: {type(error).__name__}'}
    except BaseException as error:                      # noqa: BLE001
        return {'kind': 'crash', 'stage': 'decode', 'error': f'{type(error).__name__}: {str(error)[:100]}'}
    if strict and again != plan:
        return {'kind': 'roundtrip', 'stage': 'compare', 'error': 'decode(encode(plan)) != plan'}
    if hasattr(codec, 'validate'):
        try:
            codec.validate(plan, registry)
        except declared:
            pass
        except BaseException as error:                  # noqa: BLE001
            return {'kind': 'crash', 'stage': 'validate', 'error': f'{type(error).__name__}: {str(error)[:100]}'}
    return {'kind': 'ok'}


def main(argv) -> int:
    export, plans_path, out_path = Path(argv[1]), Path(argv[2]), Path(argv[3])
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (4 << 30, 4 << 30))
    except (ImportError, ValueError, OSError):
        pass
    sys.setrecursionlimit(3000)
    spec = importlib.util.spec_from_file_location('_prechecks_codec', export / 'vm/serializer.py')
    codec = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(export / 'vm'))
    spec.loader.exec_module(codec)
    registry = codec.registry(export / 'vm/registry.json')
    digest = codec.base_digest(registry)
    results = {}
    for item in json.loads(plans_path.read_text()):
        results[item['name']] = outcome(codec, item['plan'], digest, registry, bool(item.get('strict')))
    out_path.write_text(json.dumps(results))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
