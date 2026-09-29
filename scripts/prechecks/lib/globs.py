"""Path globs with `**`, `*`, `?`, `[set]` and `{a,b}`, matched on `/`-separated repository paths."""
from __future__ import annotations

import functools
import re


def _braces(pattern: str) -> list[str]:
    """Expand the first top-level `{a,b}` group; recurse for the rest."""
    depth, start = 0, -1
    for i, ch in enumerate(pattern):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}' and depth:
            depth -= 1
            if depth == 0:
                inner, parts, level, last = pattern[start + 1:i], [], 0, 0
                for j, c in enumerate(inner):
                    level += (c == '{') - (c == '}')
                    if c == ',' and level == 0:
                        parts.append(inner[last:j])
                        last = j + 1
                parts.append(inner[last:])
                out = []
                for part in parts:
                    out.extend(_braces(pattern[:start] + part + pattern[i + 1:]))
                return out
    return [pattern]


def _one(pattern: str) -> str:
    out, i, n = [], 0, len(pattern)
    while i < n:
        ch = pattern[i]
        if ch == '*':
            if pattern[i:i + 3] == '**/':
                out.append('(?:.*/)?')
                i += 3
                continue
            if pattern[i:i + 2] == '**':
                out.append('.*')
                i += 2
                continue
            out.append('[^/]*')
        elif ch == '?':
            out.append('[^/]')
        elif ch == '[':
            j = pattern.find(']', i + 2)
            if j < 0:
                out.append(re.escape(ch))
            else:
                body = pattern[i + 1:j]
                out.append('[' + ('^' if body.startswith('!') else '') + re.escape(body.lstrip('!')).replace('\\-', '-') + ']')
                i = j
        else:
            out.append(re.escape(ch))
        i += 1
    return ''.join(out)


@functools.lru_cache(maxsize=None)
def compile_glob(pattern: str) -> re.Pattern:
    return re.compile('^(?:' + '|'.join(_one(p) for p in _braces(pattern)) + ')$')


def match(pattern: str, path: str) -> bool:
    return compile_glob(pattern).match(path) is not None


def match_any(patterns, path: str) -> bool:
    return any(match(p, path) for p in patterns)


def filter_paths(patterns, paths):
    return [p for p in paths if match_any(patterns, p)]
