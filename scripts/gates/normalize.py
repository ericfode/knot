"""Receipt identity: preserve observations and hashes; normalize named volatility."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
from pathlib import Path
import re


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode()


def pack(data: bytes) -> bytes:
    # GzipFile pins MTIME, omits FNAME, and uses the portable OS=255 header.
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode='wb', filename='', mtime=0) as stream:
        stream.write(data)
    return out.getvalue()


class Normalizer:
    def __init__(self, root: Path, toolchain: Path | None = None,
                 library: Path | None = None):
        self.root = root
        self.aliases = {str(root): '$ROOT'}
        for location, token in ((toolchain, '.toolchain'), (library, '$BEND_LIB')):
            if location:
                self.aliases[str(location)] = token
                import os
                self.aliases[os.path.relpath(location, root)] = token

    def text(self, value: str, aliases: dict) -> str:
        for old, new in sorted(aliases.items(), key=lambda pair: -len(pair[0])):
            # Only complete path prefixes, never /checkout-other or /a/checkout.
            pattern = r'(?<![\w/.-])' + re.escape(old) + r'(?=/|$|[\s\'"\):,])'
            value = re.sub(pattern, lambda _: new, value)
        # The seed realpaths Base and hash imports. Historical inventories may
        # spell these relative to a different worktree, or as absolute paths.
        value = re.sub(r'(?<![\w/.-])(?:/[^\s\'"<>]*?|(?:\.\./)+)\.toolchain/', '.toolchain/', value)
        value = re.sub(r'(?<![\w/.-])(?:/[^\s\'"<>]*?|(?:\.\./)+)\.bend/lib/', '$BEND_LIB/', value)
        value = value.replace('$ROOT/.toolchain/', '.toolchain/')
        value = re.sub(r'((?:\.toolchain|\$ROOT|\$BEND_LIB)/[^\s\'"<>]*)',
                       lambda m: m[0].replace('/./', '/'), value)
        return value

    def value(self, value):
        aliases = dict(self.aliases)

        def roots(item):
            if isinstance(item, dict):
                argv = item.get('argv', [])
                for arg in argv if isinstance(argv, list) else []:
                    if isinstance(arg, str) and arg.startswith('/') and arg.endswith('/scripts/bend-reference'):
                        aliases[arg.removesuffix('/scripts/bend-reference')] = '$ROOT'
                for child in item.values():
                    roots(child)
            elif isinstance(item, list):
                for child in item:
                    roots(child)

        roots(value)

        def visit(item, at=()):
            if isinstance(item, dict):
                result = {}
                for key, child in item.items():
                    name = self.text(key, aliases)
                    if (not at and key in ('date', 'at') and isinstance(child, str)
                            and re.fullmatch(r'\d{4}-\d\d-\d\dT[\d:.]+(?:Z|[+-]\d\d:\d\d)', child)):
                        result[name] = '<normalized-date>'
                    elif key == 'elapsed_seconds' and isinstance(child, (int, float)):
                        result[name] = 0
                    else:
                        result[name] = visit(child, (*at, key))
                return result
            if isinstance(item, list):
                return [visit(child, (*at, str(i))) for i, child in enumerate(item)]
            return self.text(item, aliases) if isinstance(item, str) else item

        return visit(value)

    def receipt(self, name: str, data: bytes, companions: dict[str, bytes]) -> bytes:
        if name.endswith('.gz'):
            # These are retained input/observation bytes, not JSON metadata.
            return pack(gzip.decompress(data))
        if not name.endswith('.json'):
            return data
        value = json.loads(data)
        # The flat gate hashes the *compressed* owned-store input. Normalize
        # that edge only when its recorded digest matches the supplied bytes.
        # A stale or invented hash is semantic drift, never discarded.
        if name == 'research/flat-store/receipts/gate.json':
            payload = companions.get('research/owned-store/receipts/inputs.json.gz')
            if payload is not None and value.get('original_inputs_sha256') == digest(payload):
                value['original_inputs_sha256'] = digest(pack(gzip.decompress(payload)))
        return json_bytes(self.value(value))


def classify(before: bytes | None, after: bytes | None,
             normalized_before: bytes | None, normalized_after: bytes | None) -> str:
    if before == after:
        return 'identical'
    if normalized_before == normalized_after:
        return 'volatile-only'
    return 'semantic'


def changed_fields(before, after, pointer='') -> list[str]:
    """JSON pointers locate drift without hiding a missing key behind null."""
    if type(before) is not type(after):
        return [pointer or '/']
    if isinstance(before, dict):
        result = []
        for key in sorted(before.keys() | after.keys()):
            child = pointer + '/' + key.replace('~', '~0').replace('/', '~1')
            result.extend([child] if key not in before or key not in after
                          else changed_fields(before[key], after[key], child))
        return result
    if isinstance(before, list):
        if len(before) != len(after):
            return [pointer or '/']
        return [p for i, (a, b) in enumerate(zip(before, after))
                for p in changed_fields(a, b, pointer + '/' + str(i))]
    return [] if before == after else [pointer or '/']
