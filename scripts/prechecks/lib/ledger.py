"""The known-conditions ledger: conditions the coordinator has already acknowledged.

It is read from the base ref (main), never from the branch under test, so a branch cannot silence its
own condition; a branch edit to the ledger is itself reported by C3 as an out-of-scope edit.
"""
from __future__ import annotations

import datetime
import json
from dataclasses import dataclass, field

from .model import Condition, canonical

LEDGER_PATH = 'docs/compiler-campaign/known-conditions.json'


@dataclass
class Ledger:
    entries: list = field(default_factory=list)
    source: str = 'empty'

    def by_fingerprint(self) -> dict:
        return {e['fingerprint']: e for e in self.entries if e.get('fingerprint')}

    def annotate(self, conditions: list[Condition], today: str | None = None) -> None:
        today = today or datetime.date.today().isoformat()
        index = self.by_fingerprint()
        for condition in conditions:
            entry = index.get(condition.fingerprint)
            if entry is None:
                condition.status = 'new'
                continue
            if entry.get('until') and str(entry['until']) < today:
                condition.status = 'new'
                continue
            condition.ledger_entry = entry.get('reason') or entry.get('owner') or 'ledger'
            if 'value' in entry and canonical(entry['value']) != canonical(condition.value):
                condition.status = 'changed'
            else:
                condition.status = 'known'


def load(tree=None, path: str | None = None) -> Ledger:
    """Ledger from an explicit file, else from `tree` (the base or main tree)."""
    raw = None
    source = 'empty'
    if path:
        with open(path, encoding='utf-8') as handle:
            raw = json.load(handle)
        source = path
    elif tree is not None:
        try:
            raw = tree.json(LEDGER_PATH)
        except ValueError:
            raw = None
        if raw is not None:
            source = f'{tree.label}:{LEDGER_PATH}'
    if raw is None:
        return Ledger()
    entries = raw.get('entries', []) if isinstance(raw, dict) else raw
    return Ledger([e for e in entries if isinstance(e, dict)], source)


def entry_for(condition: Condition, *, owner: str = 'coordinator', reason: str = '', until: str | None = None,
              added: str | None = None) -> dict:
    """A ledger entry that would acknowledge `condition` (for `--emit-ledger`)."""
    return {'fingerprint': condition.fingerprint, 'check': condition.check, 'rule': condition.rule,
            'subject': condition.subject, 'value': condition.value, 'owner': owner, 'reason': reason,
            'added': added or datetime.date.today().isoformat(), 'until': until}
