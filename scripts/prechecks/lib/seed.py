"""The pinned seed (Bend 2.0.29) as an oracle: syntax verdicts in process, check and run verdicts by CLI.

Every call runs with cwd in a scratch directory and an allowlisted environment, so nothing here can
pick up a `.env` file (bun loads one from its working directory).
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from .context import tool_env

SEED_DIR = '.toolchain/bend-2.0.29-574b6d3/bend2'
SEED_REVISION = '574b6d39a235b539eb19a5c532993a0abb3d11ad'
HERE = Path(__file__).resolve().parent.parent
DIAGNOSTIC = re.compile(r'\A\s*Error:\n- ')


class Seed:
    def __init__(self, root: Path, scratch: Path, timeout: float = 60):
        self.dir = (Path(root) / SEED_DIR)
        self.main = self.dir / 'main.ts'
        self.bend_ts = self.dir / 'bend.ts'
        self.scratch = Path(scratch)
        self.scratch.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout

    def available(self) -> bool:
        return self.main.is_file() and self.bend_ts.is_file()

    def parse_many(self, paths: list, batch: int = 400) -> dict:
        """The seed's own parse_book on each file: {path: {ok, exp, beg}}; 400 files per bun process."""
        result = {}
        for i in range(0, len(paths), batch):
            chunk = [str(p) for p in paths[i:i + batch]]
            proc = subprocess.run(['bun', str(HERE / 'seedparse.ts'), str(self.bend_ts.resolve()), *chunk],
                                  cwd=self.scratch, env=tool_env(), capture_output=True, timeout=self.timeout * 4)
            if proc.returncode != 0:
                raise RuntimeError('seed parse oracle failed: ' + proc.stderr.decode(errors='replace')[:300])
            for row in json.loads(proc.stdout):
                result[row['f']] = {'ok': row['ok'], 'exp': row.get('exp'), 'beg': row.get('beg')}
        return result

    def _cli(self, args: list, cwd: Path) -> dict:
        try:
            proc = subprocess.run(['bun', str(self.main.resolve()), *args], cwd=cwd, env=tool_env(), capture_output=True,
                                  timeout=self.timeout)
        except subprocess.TimeoutExpired:
            return {'exit': None, 'stdout': '', 'stderr': '', 'verdict': 'timeout'}
        out, err = proc.stdout.decode('utf-8', 'replace'), proc.stderr.decode('utf-8', 'replace')
        if proc.returncode == 0:
            verdict = 'accept'
        elif DIAGNOSTIC.match(err):
            verdict = 'reject'
        else:
            verdict = 'crash'
        return {'exit': proc.returncode, 'stdout': out, 'stderr': err, 'verdict': verdict}

    def check_only(self, path: Path) -> dict:
        path = Path(path)
        return self._cli([path.name, '--check-only'], path.parent)

    def run(self, path: Path) -> dict:
        path = Path(path)
        return self._cli([path.name], path.parent)
