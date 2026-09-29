"""The retired-terms ledger: literals that a numbered decision superseded (shared by C2 R4 and C6 R2)."""
from __future__ import annotations

import json
import re
from pathlib import Path

SEED = Path(__file__).resolve().parent.parent / 'data/retired-terms.json'
LEDGER = 'docs/compiler-campaign/retired-terms.json'


def load(tree=None) -> list[tuple[dict, re.Pattern]]:
    """The seed extended by the coordinator's ledger read from `tree` (main), compiled case-insensitively."""
    terms = list(json.loads(SEED.read_text())['terms'])
    if tree is not None:
        try:
            data = tree.json(LEDGER)
        except ValueError:
            data = None
        if isinstance(data, dict):
            terms += data.get('terms', [])
    return [(term, re.compile(term['pattern'], re.I)) for term in terms]


def allowed(term: dict, context: str) -> bool:
    context = context.lower()
    return any(marker.lower() in context for marker in term.get('allowed', []))
