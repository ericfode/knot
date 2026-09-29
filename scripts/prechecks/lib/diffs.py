"""Parse unified diffs into per-file hunks."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

HUNK = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')


@dataclass
class Hunk:
    old_start: int
    old_len: int
    new_start: int
    new_len: int
    removed: list = field(default_factory=list)
    added: list = field(default_factory=list)


def parse(patch: str) -> dict[str, list[Hunk]]:
    """`git diff -U0` (or any -U) output -> {new path: [Hunk]}; renames are keyed by the new path."""
    files: dict[str, list[Hunk]] = {}
    path = old_path = None
    current: Hunk | None = None
    for line in patch.split('\n'):
        if line.startswith('diff --git '):
            path = old_path = None
            current = None
        elif line.startswith('--- ') and current is None or line.startswith('--- ') and path is None:
            source = line[4:]
            old_path = None if source == '/dev/null' else source[2:] if source.startswith('a/') else source
        elif line.startswith('+++ ') and path is None:
            target = line[4:]
            path = old_path if target == '/dev/null' else target[2:] if target.startswith('b/') else target
            if path is not None:
                files.setdefault(path, [])
            current = None
        elif path is not None:
            match = HUNK.match(line)
            if match:
                current = Hunk(int(match[1]), int(match[2] or 1), int(match[3]), int(match[4] or 1))
                files[path].append(current)
            elif current is not None:
                if line.startswith('-'):
                    current.removed.append(line[1:])
                elif line.startswith('+'):
                    current.added.append(line[1:])
    return files


def deleted_lines(patch: str) -> dict[str, list[str]]:
    return {p: [line for h in hunks for line in h.removed] for p, hunks in parse(patch).items()}
