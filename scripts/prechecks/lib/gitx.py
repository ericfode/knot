"""Small, dependency-free git layer: plumbing calls, a batch blob reader, a working-tree snapshot.

Nothing here reads `.env*`: the working-tree snapshot excludes those names by pathspec, so git
never opens them, and no path handed to a reader is ever taken from user data.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path

ENV_EXCLUDES = (':(exclude).env', ':(exclude).env.*', ':(glob,exclude)**/.env', ':(glob,exclude)**/.env.*')


class GitError(RuntimeError):
    pass


@dataclass(frozen=True)
class Change:
    status: str          # A, M, D, R, C, T
    path: str            # the path at the new side (or the deleted path)
    old_path: str | None = None
    score: int | None = None


@dataclass(frozen=True)
class Commit:
    sha: str
    parents: tuple[str, ...]
    author: str
    date: str
    subject: str
    body: str            # the whole message, subject included

    @property
    def is_merge(self) -> bool:
        return len(self.parents) > 1


def clean_env(extra: dict | None = None) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(LC_ALL='C', GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0')
    if extra:
        env.update(extra)
    return env


class Repo:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self._cat: subprocess.Popen | None = None
        self._cat_lock = threading.Lock()
        self._blobs: dict[str, bytes] = {}
        self._tree_cache: dict[str, dict] = {}

    # ---- plain commands -------------------------------------------------
    def git(self, *args, input: bytes | None = None, env: dict | None = None, check: bool = True,
            ok=(0,)) -> subprocess.CompletedProcess:
        proc = subprocess.run(['git', '-C', str(self.root), *args], input=input, capture_output=True,
                              env=clean_env(env))
        if check and proc.returncode not in ok:
            raise GitError(f"git {' '.join(args[:4])} failed ({proc.returncode}): "
                           f"{proc.stderr.decode(errors='replace').strip()[:400]}")
        return proc

    def out(self, *args, **kw) -> str:
        return self.git(*args, **kw).stdout.decode('utf-8', 'replace').strip()

    def rev_parse(self, rev: str) -> str | None:
        proc = self.git('rev-parse', '--verify', '--quiet', rev + '^{commit}', check=False)
        return proc.stdout.decode().strip() or None if proc.returncode == 0 else None

    def tree_sha(self, rev: str) -> str | None:
        proc = self.git('rev-parse', '--verify', '--quiet', rev + '^{tree}', check=False)
        return proc.stdout.decode().strip() or None if proc.returncode == 0 else None

    def top(self) -> Path:
        return Path(self.out('rev-parse', '--show-toplevel'))

    def branch(self) -> str | None:
        proc = self.git('symbolic-ref', '--short', '-q', 'HEAD', check=False)
        return proc.stdout.decode().strip() or None if proc.returncode == 0 else None

    def merge_base(self, a: str, b: str) -> str | None:
        proc = self.git('merge-base', a, b, check=False)
        text = proc.stdout.decode().strip().splitlines()
        return text[0] if proc.returncode == 0 and text else None

    def is_ancestor(self, a: str, b: str) -> bool:
        return self.git('merge-base', '--is-ancestor', a, b, check=False).returncode == 0

    def rev_count(self, spec: str) -> int:
        return int(self.out('rev-list', '--count', spec))

    def rev_list(self, *args) -> list[str]:
        return self.out('rev-list', *args).split()

    def commit_time(self, rev: str) -> int:
        return int(self.out('log', '-1', '--format=%ct', rev))

    # ---- commits and diffs ---------------------------------------------
    def commits(self, base: str | None, head: str, *, first_parent: bool = False, reverse: bool = True) -> list[Commit]:
        spec = f'{base}..{head}' if base else head
        args = ['log', '--format=%H%x1f%P%x1f%an%x1f%aI%x1f%s%x1f%B%x1e']
        if first_parent:
            args.append('--first-parent')
        if reverse:
            args.append('--reverse')
        text = self.git(*args, spec).stdout.decode('utf-8', 'replace')
        result = []
        for record in text.split('\x1e'):
            record = record.strip('\n')
            if not record.strip():
                continue
            sha, parents, author, date, subject, body = (record.split('\x1f') + [''] * 6)[:6]
            result.append(Commit(sha.strip(), tuple(parents.split()), author, date, subject, body))
        return result

    def name_status(self, a: str, b: str, *, renames: bool = True) -> list[Change]:
        args = ['diff-tree', '-r', '-z', '--name-status', '--no-commit-id']
        if renames:
            args.append('-M')
        raw = self.git(*args, a, b).stdout.split(b'\0')
        out, i = [], 0
        while i < len(raw) and raw[i]:
            code = raw[i].decode()
            kind = code[0]
            if kind in 'RC':
                out.append(Change(kind, raw[i + 2].decode('utf-8', 'surrogateescape'),
                                  raw[i + 1].decode('utf-8', 'surrogateescape'), int(code[1:] or 0)))
                i += 3
            else:
                out.append(Change(kind, raw[i + 1].decode('utf-8', 'surrogateescape')))
                i += 2
        return out

    def patch(self, a: str, b: str, paths=None, *, unified: int = 3, renames: bool = True) -> str:
        args = ['diff-tree', '-r', '-p', '--no-color', '--no-ext-diff', f'--unified={unified}', '--no-commit-id']
        if renames:
            args.append('-M')
        args += [a, b]
        if paths:
            args += ['--', *paths]
        return self.git(*args).stdout.decode('utf-8', 'replace')

    def commit_patch(self, sha: str, paths=None, *, unified: int = 3) -> str:
        args = ['show', '--format=', '--no-color', '--no-ext-diff', f'--unified={unified}', '-M', sha]
        if paths:
            args += ['--', *paths]
        return self.git(*args).stdout.decode('utf-8', 'replace')

    def commit_files(self, sha: str) -> list[Change]:
        """Files a commit changed. A merge lists only the paths that differ from every parent (its own resolution): the
        side's commits are listed on their own, and plain diff-tree shows a merge as empty."""
        parents = self.out('rev-list', '--parents', '-n', '1', sha).split()[1:]
        if len(parents) > 1:
            raw = self.git('diff-tree', '-c', '-r', '-z', '--name-only', '--no-commit-id', sha).stdout.split(b'\0')
            return [Change('M', path.decode('utf-8', 'surrogateescape')) for path in raw if path]
        raw = self.git('diff-tree', '-r', '-z', '--name-status', '--no-commit-id', '-M', '--root', sha).stdout.split(b'\0')
        out, i = [], 0
        while i < len(raw) and raw[i]:
            code = raw[i].decode()
            if code[0] in 'RC':
                out.append(Change(code[0], raw[i + 2].decode('utf-8', 'surrogateescape'),
                                  raw[i + 1].decode('utf-8', 'surrogateescape'), int(code[1:] or 0)))
                i += 3
            else:
                out.append(Change(code[0], raw[i + 1].decode('utf-8', 'surrogateescape')))
                i += 2
        return out

    # ---- trees and blobs -----------------------------------------------
    def ls_tree(self, treeish: str) -> dict[str, tuple[str, str]]:
        """path -> (mode, blob sha) for every blob and symlink under the tree."""
        if treeish in self._tree_cache:
            return self._tree_cache[treeish]
        raw = self.git('ls-tree', '-r', '-z', '--full-tree', treeish).stdout
        entries = {}
        for item in raw.split(b'\0'):
            if not item:
                continue
            meta, _, path = item.partition(b'\t')
            mode, kind, sha = meta.decode().split()
            if kind == 'blob':
                entries[path.decode('utf-8', 'surrogateescape')] = (mode, sha)
        self._tree_cache[treeish] = entries
        return entries

    def _reader(self) -> subprocess.Popen:
        if self._cat is None or self._cat.poll() is not None:
            self._cat = subprocess.Popen(['git', '-C', str(self.root), 'cat-file', '--batch'], stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=clean_env(),
                                         bufsize=0)
        return self._cat

    def blob(self, sha: str) -> bytes | None:
        if sha in self._blobs:
            return self._blobs[sha]
        with self._cat_lock:
            proc = self._reader()
            proc.stdin.write(sha.encode() + b'\n')
            proc.stdin.flush()
            header = b''
            while not header.endswith(b'\n'):
                chunk = proc.stdout.read(1)
                if not chunk:
                    self._cat = None
                    raise GitError('git cat-file closed unexpectedly')
                header += chunk
            fields = header.split()
            if len(fields) == 2 and fields[1] == b'missing':
                return None
            size = int(fields[2])
            data = b''
            while len(data) < size:
                chunk = proc.stdout.read(size - len(data))
                if not chunk:
                    self._cat = None
                    raise GitError('git cat-file truncated a blob')
                data += chunk
            proc.stdout.read(1)  # trailing newline
        if size <= 4 * 1024 * 1024:
            self._blobs[sha] = data
        return data

    def close(self):
        proc, self._cat = self._cat, None
        if proc:
            try:
                if proc.poll() is None:
                    proc.stdin.close()
                    proc.wait(timeout=5)
            except Exception:
                proc.kill()
                proc.wait()
            finally:
                for stream in (proc.stdin, proc.stdout):
                    try:
                        stream.close()
                    except Exception:
                        pass

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def grep(self, treeish: str, token: str, pathspecs: list[str]) -> list[tuple[str, int, str]]:
        """(path, line, text) of whole-word literal matches of `token` in a tree, without a checkout."""
        proc = self.git('grep', '-n', '-w', '-F', '-I', '--no-color', '-e', token, treeish, '--', *pathspecs,
                        check=False, ok=(0, 1))
        rows = []
        for line in proc.stdout.decode('utf-8', 'replace').split('\n'):
            parts = line.split(':', 3)
            if len(parts) == 4 and parts[2].isdigit():
                rows.append((parts[1], int(parts[2]), parts[3]))
        return rows

    # ---- the working tree as a tree object -------------------------------
    def snapshot_worktree(self) -> str:
        """Tree sha of HEAD plus the working copy, through a private index; `.env*` is never staged."""
        with tempfile.TemporaryDirectory(prefix='prechecks-index-') as directory:
            env = {'GIT_INDEX_FILE': os.path.join(directory, 'index')}
            head = self.rev_parse('HEAD')
            if head:
                self.git('read-tree', head, env=env)
            self.git('add', '-A', '--', '.', *ENV_EXCLUDES, env=env)
            return self.out('write-tree', env=env)

    def worktree_dirty(self) -> bool:
        return bool(self.git('status', '--porcelain', '--untracked-files=normal', '--', '.', *ENV_EXCLUDES).stdout.strip())

    # ---- merge simulation -------------------------------------------------
    def merge_tree(self, a: str, b: str) -> tuple[int, list[str], str, str | None]:
        """Trial merge without touching any checkout: (exit code, conflicted paths, messages, merged tree oid)."""
        proc = self.git('merge-tree', '--write-tree', '--name-only', '--messages', a, b, check=False)
        if proc.returncode not in (0, 1):
            raise GitError(proc.stderr.decode(errors='replace').strip()[:300])
        lines = proc.stdout.decode('utf-8', 'replace').split('\n')
        # Format: <tree oid>\n<conflicted names...>\n\n<messages>
        oid = lines[0].strip() or None
        conflicts, messages = [], []
        i = 1
        while i < len(lines) and lines[i] != '':
            conflicts.append(lines[i])
            i += 1
        messages = lines[i + 1:]
        return proc.returncode, sorted(set(conflicts)), '\n'.join(messages), oid
