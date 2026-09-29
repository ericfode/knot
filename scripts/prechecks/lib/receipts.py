"""Receipt helpers shared by C3, C4 and C6: what counts as a receipt, reading it, and its hash claims."""
from __future__ import annotations

import gzip
import hashlib
import json
import re

from . import globs

RECEIPT_GLOBS = (
    '**/receipts/**', '**/receipts.json', 'research/*/receipts/**', 'packages/*/receipts/**',
    'tests/*/evidence/**', 'packages/*/evidence/**', 'docs/compiler-campaign/*.json', 'docs/compiler-campaign/*.json.gz',
)
TEXT_SUFFIXES = ('.json', '.txt', '.md', '.log', '.yaml', '.yml', '.tsv', '.csv', '.wat', '.gz')
HEX64 = re.compile(r'^[0-9a-f]{64}$')
MAX_BYTES = 40 * 1024 * 1024


def is_receipt(path: str) -> bool:
    if '/history/' in path:
        return False                        # labelled historical; never judged as a current receipt
    return globs.match_any(RECEIPT_GLOBS, path)


def read_text(tree, path: str) -> str | None:
    """Text of a receipt, gzip unpacked; None when absent, binary or too large."""
    data = tree.read(path)
    if data is None or len(data) > MAX_BYTES:
        return None
    if path.endswith('.gz'):
        try:
            data = gzip.decompress(data)
        except OSError:
            return None
        if len(data) > MAX_BYTES:
            return None
    elif not path.endswith(TEXT_SUFFIXES):
        return None
    if b'\0' in data[:4096]:
        return None
    return data.decode('utf-8', 'replace')


def looks_like_path(key: str) -> bool:
    return ('/' in key or re.search(r'\.\w{1,6}$', key) is not None) and ' ' not in key


def hash_claims(value, pointer: str = '') -> list[tuple[str, str, str]]:
    """(pointer, repo path, sha256) for every recorded input hash in a parsed receipt.

    Two shapes are recognised: a mapping `{path: sha256}` and a record with `path`/`file` plus `sha256`.
    """
    found = []
    if isinstance(value, dict):
        for key in ('path', 'file'):
            if isinstance(value.get(key), str) and isinstance(value.get('sha256'), str) and HEX64.match(value['sha256']):
                found.append((pointer + '/sha256', value[key], value['sha256']))
        for key, child in value.items():
            if isinstance(child, str) and HEX64.match(child) and isinstance(key, str) and looks_like_path(key):
                found.append((pointer + '/' + key.replace('~', '~0').replace('/', '~1'), key, child))
            else:
                found.extend(hash_claims(child, pointer + '/' + str(key).replace('~', '~0').replace('/', '~1')))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            found.extend(hash_claims(child, f'{pointer}/{i}'))
    return found


def repo_path(claimed: str) -> str:
    """Strip receipt path decorations so a recorded name can be looked up in a tree."""
    claimed = claimed.replace('$ROOT/', '')
    while claimed.startswith('./'):
        claimed = claimed[2:]
    return claimed


def string_leaves(value, pointer: str = ''):
    """Yield (json pointer, string) for every string value, keys included as `<key>` markers."""
    if isinstance(value, dict):
        for key, child in value.items():
            here = pointer + '/' + str(key).replace('~', '~0').replace('/', '~1')
            if isinstance(key, str):
                yield here + '#key', key
            yield from string_leaves(child, here)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from string_leaves(child, f'{pointer}/{i}')
    elif isinstance(value, str):
        yield pointer, value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_json(text: str):
    try:
        return json.loads(text)
    except ValueError:
        return None
