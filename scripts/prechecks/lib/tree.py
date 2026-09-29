"""A read-only view of one git tree (a commit's, or a snapshot of the working copy)."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from . import globs
from .gitx import Repo, clean_env


class Tree:
    def __init__(self, repo: Repo, treeish: str, label: str | None = None):
        self.repo = repo
        self.treeish = treeish
        self.label = label or treeish

    @property
    def entries(self) -> dict[str, tuple[str, str]]:
        return self.repo.ls_tree(self.treeish)

    def files(self) -> list[str]:
        return sorted(self.entries)

    def has(self, path: str) -> bool:
        return path in self.entries

    def sha(self, path: str) -> str | None:
        entry = self.entries.get(path)
        return entry[1] if entry else None

    def mode(self, path: str) -> str | None:
        entry = self.entries.get(path)
        return entry[0] if entry else None

    def read(self, path: str) -> bytes | None:
        sha = self.sha(path)
        return None if sha is None else self.repo.blob(sha)

    def text(self, path: str) -> str | None:
        data = self.read(path)
        return None if data is None else data.decode('utf-8', 'replace')

    def json(self, path: str):
        """Parsed JSON, or None when the file is absent; raises ValueError when present but invalid."""
        data = self.read(path)
        if data is None:
            return None
        if path.endswith('.gz'):
            data = gzip.decompress(data)
        return json.loads(data.decode('utf-8'))

    def sha256(self, path: str) -> str | None:
        data = self.read(path)
        return None if data is None else hashlib.sha256(data).hexdigest()

    def glob(self, *patterns: str) -> list[str]:
        return globs.filter_paths(patterns, self.files())

    def under(self, prefix: str) -> list[str]:
        prefix = prefix.rstrip('/') + '/'
        return [p for p in self.files() if p.startswith(prefix)]

    def is_dir(self, path: str) -> bool:
        prefix = path.rstrip('/') + '/'
        return any(p.startswith(prefix) for p in self.entries)

    def same(self, other: 'Tree', path: str) -> bool:
        return self.sha(path) == other.sha(path)

    # ---- materialization for tools that need real files ------------------
    def export(self, destination: Path, *, links: dict[str, Path] | None = None, only: list[str] | None = None) -> Path:
        """Write the tree's files below `destination` (no `.env*`), then link shared directories.

        Uses `git archive`, which never reads the working copy. Returns the destination.
        """
        destination = Path(destination)
        if destination.exists():
            return destination
        partial = destination.with_name(destination.name + '.partial')
        if partial.exists():
            shutil.rmtree(partial)
        partial.mkdir(parents=True)
        args = ['git', '-C', str(self.repo.root), 'archive', '--format=tar', self.treeish]
        if only:
            args += ['--', *only]
        archive = subprocess.Popen(args, stdout=subprocess.PIPE, env=clean_env())
        untar = subprocess.run(['tar', '-x', '-C', str(partial)], stdin=archive.stdout)
        archive.stdout.close()
        if archive.wait() != 0 or untar.returncode != 0:
            shutil.rmtree(partial, ignore_errors=True)
            raise RuntimeError(f'git archive of {self.label} failed')
        # `.env*` cannot be present in a tracked tree the runner uses, but never leave one behind.
        for path in list(partial.rglob('.env*')):
            if path.name == '.env' or path.name.startswith('.env.'):
                if path.is_file() or path.is_symlink():
                    os.unlink(path)
        for name, target in (links or {}).items():
            link = partial / name
            if not link.exists() and not link.is_symlink():
                link.symlink_to(target)
        partial.rename(destination)
        return destination
