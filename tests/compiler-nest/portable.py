#!/usr/bin/env python3
"""Tokenize checkout paths in owned JSON receipts, preserving observations and historical hashes."""
import gzip
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/gates'))
from normalize import Normalizer, pack

HOST = re.compile(r'/Users/|/home/[^/\s"\']+/|/private/(?:tmp|var)|/var/folders|[.]claude/worktrees|'
                  r'[.]local/gates/run-|(?:[.][.]/){2,}[.]toolchain')
RUN = re.compile(r'(?:\$ROOT/)?[.]local/gates/run-[^/\s"\'():,]+')


def portable(value):
    normalizer = Normalizer(ROOT, (ROOT / '.toolchain').resolve(),
                            Path(os.environ.get('BEND_LIB', str(Path.home() / '.bend/lib'))))
    aliases = dict(normalizer.aliases)

    def roots(item):
        if isinstance(item, dict):
            for arg in item.get('argv', []):
                if isinstance(arg, str) and arg.startswith('/') and arg.endswith('/scripts/bend-reference'):
                    aliases[arg.removesuffix('/scripts/bend-reference')] = '$ROOT'
            for child in item.values():
                roots(child)
        elif isinstance(item, list):
            for child in item:
                roots(child)

    roots(value)

    def text(s):
        return RUN.sub('$GATE_RUN', normalizer.text(s, aliases))

    def visit(item):
        if isinstance(item, dict):
            return {text(k): visit(v) for k, v in item.items()}
        if isinstance(item, list):
            return [visit(v) for v in item]
        return text(item) if isinstance(item, str) else item

    return visit(value)


def main():
    changed = []
    for path in sorted((ROOT / 'tests/compiler-nest/receipts').iterdir()):
        if not path.name.endswith(('.json', '.json.gz')):
            continue
        raw = path.read_bytes()
        data = gzip.decompress(raw) if path.suffix == '.gz' else raw
        original = json.loads(data)
        result = portable(original)
        if result == original:
            continue
        encoded = (json.dumps(result, indent=2) + '\n').encode()
        if HOST.search(encoded.decode()):
            raise ValueError(f'unmapped host path in {path.name}: {HOST.search(encoded.decode()).group()}')
        assert portable(result) == result, 'path normalization must be idempotent'
        path.write_bytes(pack(encoded) if path.suffix == '.gz' else encoded)
        changed.append(path.name)
    print('Portable receipt paths: ' + ', '.join(changed))


if __name__ == '__main__':
    main()
