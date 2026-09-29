"""Synthetic git repositories for the unit tests: every test builds its own, never the real one."""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from lib import context as context_mod
from lib.gitx import Repo

ID = ('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false',
      '-c', 'core.hooksPath=/dev/null')


class Fixture:
    """A throwaway repository on `main` with helpers to write, commit and branch."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='prechecks-fixture-')
        base = Path(self.tmp.name)
        self.root = base / 'repo'
        self.scratch = base / 'scratch'
        self.root.mkdir()
        self.git('init', '-q', '-b', 'main')
        self.n = 0
        self._repo = Repo(self.root)

    def close(self):
        self._repo.close()
        self.tmp.cleanup()

    def git(self, *args, check=True):
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        env['GIT_CEILING_DIRECTORIES'] = str(self.root.parent)
        proc = subprocess.run(['git', '-C', str(self.root), *ID, *args], capture_output=True, text=True, env=env)
        if check and proc.returncode:
            raise AssertionError(f'git {args} failed: {proc.stderr}')
        return proc.stdout.strip()

    def write(self, path: str, content: str | bytes = '') -> Path:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            target.write_text(content, encoding='utf-8')
        else:
            target.write_bytes(content)
        return target

    def remove(self, path: str):
        (self.root / path).unlink()

    def commit(self, message: str = 'change', files: dict | None = None, *, trailer: bool = True) -> str:
        for path, content in (files or {}).items():
            if content is None:
                self.remove(path)
            else:
                self.write(path, content)
        self.git('add', '-A')
        self.n += 1
        body = message + ('\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>' if trailer else '')
        self.git('commit', '-q', '--allow-empty', '-m', body)
        return self.git('rev-parse', 'HEAD')

    def branch(self, name: str, start: str | None = None):
        self.git('checkout', '-q', '-b', name, *([start] if start else []))

    def checkout(self, name: str):
        self.git('checkout', '-q', name)

    def repo(self) -> Repo:
        return self._repo

    def context(self, **kw):
        kw.setdefault('scratch', self.scratch)
        kw.setdefault('jobs', 2)
        return context_mod.build(self.repo(), **kw)


class RepoTest(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)

    def conditions(self, check_module, **kw):
        ctx = self.fx.context(**kw)
        result = check_module.CHECK.run(ctx).finish()
        return ctx, result

    def ids(self, result):
        return sorted(c.id for c in result.conditions)
