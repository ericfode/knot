"""The pinned seed (Bend 2.0.29) as an oracle: syntax verdicts in process, check and run verdicts by CLI.

Every call runs with cwd in a scratch directory and an allowlisted environment, so nothing here can
pick up a `.env` file (bun loads one from its working directory).
"""
from __future__ import annotations

import json
import re
import threading
from pathlib import Path

from . import proc as proc_mod
from .context import tool_env, tool_timeout_scale

SEED_DIR = '.toolchain/bend-2.0.29-574b6d3/bend2'
SEED_REVISION = '574b6d39a235b539eb19a5c532993a0abb3d11ad'
HERE = Path(__file__).resolve().parent.parent
DIAGNOSTIC = re.compile(r'\A\s*Error:\n- ')


class Seed:
    def __init__(self, root: Path, scratch: Path, timeout: float = 60, cancel: threading.Event | None = None):
        self.cancel = cancel
        self.dir = (Path(root) / SEED_DIR)
        self.main = self.dir / 'main.ts'
        self.bend_ts = self.dir / 'bend.ts'
        self.scratch = Path(scratch)
        self.scratch.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout * tool_timeout_scale()

    def available(self) -> bool:
        return self.main.is_file() and self.bend_ts.is_file()

    def parse_many(self, paths: list, batch: int = 400) -> dict:
        """The seed's own parse_book on each file: {path: {ok, exp, beg}}; 400 files per bun process."""
        result = {}
        for i in range(0, len(paths), batch):
            chunk = [str(p) for p in paths[i:i + batch]]
            code, stdout, stderr = proc_mod.run(['bun', str(HERE / 'seedparse.ts'), str(self.bend_ts.resolve()), *chunk],
                                                cwd=self.scratch, env=tool_env(), timeout=self.timeout * 4, cancel=self.cancel)
            if code is None and stderr == b'cancelled':
                raise proc_mod.Cancelled()
            if code != 0:
                raise RuntimeError('seed parse oracle failed: ' + stderr.decode(errors='replace')[:300])
            for row in json.loads(stdout):
                result[row['f']] = {'ok': row['ok'], 'exp': row.get('exp'), 'beg': row.get('beg')}
        return result

    def _cli(self, args: list, cwd: Path) -> dict:
        code, stdout, stderr = proc_mod.run(['bun', str(self.main.resolve()), *args], cwd=cwd, env=tool_env(),
                                            timeout=self.timeout, cancel=self.cancel)
        if code is None:
            if stderr == b'cancelled':
                raise proc_mod.Cancelled()
            return {'exit': None, 'stdout': '', 'stderr': '', 'verdict': 'timeout'}
        out, err = stdout.decode('utf-8', 'replace'), stderr.decode('utf-8', 'replace')
        if code == 0:
            verdict = 'accept'
        elif DIAGNOSTIC.match(err):
            verdict = 'reject'
        else:
            verdict = 'crash'
        return {'exit': code, 'stdout': out, 'stderr': err, 'verdict': verdict}

    def check_only(self, path: Path) -> dict:
        path = Path(path)
        return self._cli([path.name, '--check-only'], path.parent)

    def run(self, path: Path) -> dict:
        path = Path(path)
        return self._cli([path.name], path.parent)
