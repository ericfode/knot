"""The pinned seed as a verdict oracle.

Verdicts are keyed by the sha256 of the program text, the seed revision and the mode. Parse verdicts come from the
seed's own `parse_book` in process (400 files per bun process) and are a pure function of the text, so a persistent
cache only saves time. Check and run verdicts come from the seed's CLI, in one of two modes:

  frozen_only (the fast tier)  only verdicts that were frozen beforehand are used: the registry rows' own verdicts, the
                               tracked fixtures' recorded observations and tests/prechecks/registry/seed-verdicts.jsonl.
                               The local cache is never read and the seed's CLI never runs, so what is judged cannot
                               depend on how warm a cache is. A program without a frozen verdict is counted, not judged.
  live (the slow tier)         cached, else run in parallel, at most `budget` uncached runs per invocation.
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .seed import SEED_REVISION, Seed

IMPORT = re.compile(r'(?m)^import\b')


def has_main(text: str) -> bool:
    return re.search(r'(?m)^def main\b', text) is not None


class Oracle:
    def __init__(self, seed: Seed, cache: Path, budget: int = 200, frozen_only: bool = False):
        self.seed, self.cache, self.budget, self.frozen_only = seed, Path(cache), budget, frozen_only
        self.used = 0
        self.skipped = 0
        self.memo: dict[tuple[str, str], dict] = {}          # frozen verdicts (a frozen-only oracle never writes them to disk)
        self.cache.mkdir(parents=True, exist_ok=True)

    def _path(self, mode: str, sha: str) -> Path:
        return self.cache / mode / sha[:2] / f'{sha}.{SEED_REVISION[:7]}.json'

    def _load(self, mode: str, sha: str):
        if (mode, sha) in self.memo:
            return self.memo[(mode, sha)]
        if self.frozen_only and mode != 'parse':
            return None                                        # the local cache is not consulted for check and run verdicts
        try:
            return json.loads(self._path(mode, sha).read_text())
        except (OSError, ValueError):
            return None

    def _store(self, mode: str, sha: str, value) -> None:
        path = self._path(mode, sha)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def prefill(self, sha: str, verdict: dict | None) -> None:
        """Take frozen verdicts (registry rows, fixtures, the frozen verdict file: all observed against this seed revision)."""
        if not verdict:
            return
        entries = {}
        if verdict.get('parse') in ('ok', 'reject'):
            entries['parse'] = {'ok': verdict['parse'] == 'ok', 'beg': verdict.get('offset'), 'exp': verdict.get('expected')}
        if verdict.get('check'):
            entries['check'] = {'verdict': verdict['check']}
        if verdict.get('run'):
            entries['run'] = {'verdict': verdict['run'], 'stdout': verdict.get('stdout', '')}
        for mode, value in entries.items():
            if self.frozen_only:
                self.memo[(mode, sha)] = value
            elif self._load(mode, sha) is None:
                self._store(mode, sha, value)

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
        if self.frozen_only:
            return None
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

    def warm(self, mode: str, items: dict[str, Path], jobs: int = 8) -> None:
        """Run the missing CLI verdicts of `items` ({sha: path}) in parallel (live mode), within the budget."""
        if self.frozen_only:
            return
        todo = [(sha, path) for sha, path in items.items() if self._load(mode, sha) is None][:max(self.budget - self.used, 0)]

        def one(item):
            sha, path = item
            row = self.seed.check_only(path) if mode == 'check' else self.seed.run(path)
            value = {'verdict': row['verdict']}
            if mode == 'run':
                value['stdout'] = row['stdout']
            return sha, value

        with ThreadPoolExecutor(max_workers=max(jobs, 1)) as pool:
            for sha, value in pool.map(one, todo):
                self._store(mode, sha, value)
                self.used += 1

    def check(self, sha: str, path: Path):
        return self._cli('check', sha, path)

    def run(self, sha: str, path: Path):
        return self._cli('run', sha, path)
