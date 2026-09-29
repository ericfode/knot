"""Increment manifest: what an increment owns, appends to, freezes and consumes.

Manifests are written by the coordinator at launch (`docs/compiler-campaign/increments/<id>.json`).
Only `id` is required; every other field has a default, and a missing manifest yields the defaults, so
the suite runs on any branch. Rules that need declared ownership say so instead of guessing.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from . import globs

APPENDS = {
    'scripts/gates/run.py': 'gate-row',
    'scripts/gates/test_runner.py': 'required-name',
    'docs/compiler-campaign/GATES.md': 'gate-paragraph',
    'tools/census/approved.json': 'census-approval',
    'docs/compiler-campaign/manifest.json': 'manifest-group',
    'docs/perch-review-log.md': 'gate-paragraph',
    'package.json': 'package-scripts',
}

# Byte-identical to base unless the coordinator authorizes the edit.
FROZEN = (
    'tests/**/expectations*.json', 'tests/**/cases.json', 'tests/**/*-cases.json',
    'scripts/gates/**', 'docs/compiler-campaign/state.json',
    'docs/compiler-campaign/known-conditions.json', 'docs/compiler-campaign/retired-terms.json',
    'docs/compiler-campaign/increments/**', 'docs/COMPILER-CAMPAIGN.md',
    'tests/**/check*.py', 'tests/**/trust.ts', 'research/**/check*.py', 'research/**/trust.ts',
)

# Files whose rows are frozen data: a row present at base must be identical at head (additions allowed).
FROZEN_DATA = (
    'vm/golden/plan.json', 'vm/golden/expectations.json', 'vm/golden/vm-expected.json', 'vm/golden/bounds.json',
    'vm/core/fixtures.json', 'tests/**/expectations*.json', 'tests/**/cases.json', 'tests/**/*-cases.json',
)

DEFAULT_LANES = {'parse': 'parse-cli', 'check': 'check-cli', 'eval': 'eval-cli'}


@dataclass
class Manifest:
    id: str | None = None
    raw: dict = field(default_factory=dict)
    source: str = 'defaults'

    def get(self, key, default=None):
        return self.raw.get(key, default)

    @property
    def upstream(self) -> list[dict]:
        out = []
        for item in self.raw.get('upstream', []) or []:
            item = {'id': item} if isinstance(item, str) else dict(item)
            item.setdefault('ref', f"campaign/{item['id']}")
            out.append(item)
        return out

    @property
    def merge_before(self) -> list[str]:
        return list(self.raw.get('merge_before', []) or [])

    @property
    def declared_owns(self) -> bool:
        return 'owns' in self.raw

    def owns(self) -> list[str]:
        patterns = list(self.raw.get('owns', []) or [])
        if self.id:
            patterns.append(f'tests/compiler-{self.id}/**')
        return patterns

    def appends(self) -> dict[str, str]:
        result = dict(APPENDS)
        result.update(self.raw.get('appends', {}) or {})
        return result

    def frozen(self) -> list[str]:
        return list(FROZEN) + list(self.raw.get('frozen', []) or [])

    def frozen_data(self) -> list[str]:
        return list(FROZEN_DATA) + list(self.raw.get('frozen_data', []) or [])

    def authorized(self) -> list[dict]:
        return list(self.raw.get('authorized', []) or [])

    def is_owned(self, path: str) -> bool:
        return globs.match_any(self.owns(), path)

    def is_frozen(self, path: str) -> bool:
        return globs.match_any(self.frozen(), path) and not self.is_owned(path)

    def is_authorized(self, path: str, change: str | None = None) -> bool:
        for entry in self.authorized():
            if globs.match(entry.get('path', ''), path) and (change is None or entry.get('change') in (None, change)):
                return True
        return False

    def executor(self) -> str:
        return self.raw.get('executor', 'claude')

    def consumes(self) -> list[dict]:
        found = self.raw.get('consumes')
        if found is not None:
            return list(found)
        if self.id in ('vm-core', 'vm-model'):
            return [{'file': 'vm/check-spec.py', 'pattern': r'^def (\w+_controls)\(', 'consumers': [], 'not_applicable': []}]
        return []

    def d4_targets(self) -> list[str]:
        return list(self.raw.get('d4_targets', []) or [])

    def prompt_requires_freeze_first(self) -> bool:
        return bool(self.raw.get('freeze_first', False))


def load(id_: str | None, tree=None, path: str | None = None) -> Manifest:
    """Manifest from an explicit file, else `docs/compiler-campaign/increments/<id>.json` in `tree`."""
    if path:
        with open(path, encoding='utf-8') as handle:
            raw = json.load(handle)
        return Manifest(raw.get('id', id_), raw, source=path)
    if tree is not None and id_:
        candidate = f'docs/compiler-campaign/increments/{id_}.json'
        try:
            raw = tree.json(candidate)
        except ValueError:
            raw = None
        if raw is not None:
            return Manifest(raw.get('id', id_), raw, source=candidate)
    return Manifest(id_)
