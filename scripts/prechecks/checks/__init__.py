"""Registry of the pre-review checks. Each module exposes `CHECK` (a `lib.runner.Check`)."""
from __future__ import annotations

import importlib

# (module, id) in report order. Budgets and dependencies live with each check.
MODULES = (
    ('c1_probe_differential', 'C1'),
    ('c2_merge_forecast', 'C2'),
    ('c3_frozen_and_owned', 'C3'),
    ('c4_receipt_integrity', 'C4'),
    ('c5_preflight_delta', 'C5'),
    ('c6_claims_vs_facts', 'C6'),
    ('c7_gate_adequacy', 'C7'),
    ('c8_perch_coherence', 'C8'),
)


def load(only: set[str] | None = None, skip: set[str] | None = None) -> list:
    checks = []
    for module, check_id in MODULES:
        if only and check_id not in only:
            continue
        if skip and check_id in skip:
            continue
        try:
            checks.append(importlib.import_module(f'{__package__}.{module}').CHECK)
        except ModuleNotFoundError as error:
            if error.name != f'{__package__}.{module}':
                raise
    return checks
