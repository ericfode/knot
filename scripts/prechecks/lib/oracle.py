"""The pinned seed as a verdict oracle with a persistent cache.

Verdicts are keyed by the sha256 of the program text, the seed revision and the mode, so a program is judged at most
once across runs and branches. Parse verdicts come from the seed's own `parse_book` in process (400 files per bun
process); check and run verdicts come from its CLI, and the number of uncached CLI runs per invocation is capped.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .seed import SEED_REVISION, Seed

IMPORT = re.compile(r'(?m)^import\b')


def has_main(text: str) -> bool:
    return re.search(r'(?m)^def main\b', text) is not None


class Oracle:
    def __init__(self, seed: Seed, cache: Path, budget: int = 200):
        self.seed, self.cache, self.budget = seed, Path(cache), budget
        self.used = 0
        self.skipped = 0
        self.cache.mkdir(parents=True, exist_ok=True)

    def _path(self, mode: str, sha: str) -> Path:
        return self.cache / mode / sha[:2] / f'{sha}.{SEED_REVISION[:7]}.json'

    def _load(self, mode: str, sha: str):
        try:
            return json.loads(self._path(mode, sha).read_text())
        except (OSError, ValueError):
            return None

    def _store(self, mode: str, sha: str, value) -> None:
        path = self._path(mode, sha)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def prefill(self, sha: str, verdict: dict | None) -> None:
        """Seed the cache from frozen registry rows (their verdicts were observed against this same seed revision)."""
        if not verdict:
            return
        if verdict.get('parse') in ('ok', 'reject') and self._load('parse', sha) is None:
            self._store('parse', sha, {'ok': verdict['parse'] == 'ok', 'beg': verdict.get('offset'), 'exp': verdict.get('expected')})
        if verdict.get('check') and self._load('check', sha) is None:
            self._store('check', sha, {'verdict': verdict['check']})
        if verdict.get('run') and self._load('run', sha) is None:
            self._store('run', sha, {'verdict': verdict['run'], 'stdout': verdict.get('stdout', '')})

    def parse(self, programs: dict[str, Path]) -> dict[str, dict]:
        """{sha: {ok, beg, exp}} for import-free programs; misses are batched into one process per 400 files."""
        result, missing = {}, {}
        for sha, path in programs.items():
            cached = self._load('parse', sha)
            if cached is not None:
                result[sha] = cached
            else:
                missing[str(path)] = sha
        if missing:
            for file, verdict in self.seed.parse_many(list(missing)).items():
                sha = missing[file]
                result[sha] = verdict
                self._store('parse', sha, verdict)
        return result

    def _cli(self, mode: str, sha: str, path: Path):
        cached = self._load(mode, sha)
        if cached is not None:
            return cached
        if self.used >= self.budget:
            self.skipped += 1
            return None
        self.used += 1
        row = self.seed.check_only(path) if mode == 'check' else self.seed.run(path)
        value = {'verdict': row['verdict']}
        if mode == 'run':
            value['stdout'] = row['stdout']
        self._store(mode, sha, value)
        return value

    def check(self, sha: str, path: Path):
        return self._cli('check', sha, path)

    def run(self, sha: str, path: Path):
        return self._cli('run', sha, path)
