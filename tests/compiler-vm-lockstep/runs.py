"""The runs of vm-lockstep, from the frozen sets the vm-model gate already enumerates.

Each run is one image with the words after IMAGE (SPEC section 8) and the print window of
its traces. Runs that stop before the machine's first entry (a refused image or a refused
invocation) have no states: their outcomes are compared, not their transitions.
"""
from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'vm'
GOLDEN = HERE / 'golden'


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass
class Run:
    group: str
    label: str
    image: Path
    argv: list
    window: tuple = (1, 1, 0)   # print every state
    note: str = ''
    frozen: dict = field(default_factory=dict)


# Answers described past this many bytes make one state line of millions of codes. Their
# transitions are the same as a small answer's; the value lane compares the described line itself.
UNTRACED = {
    'run:display-visits-at-bound': 'answer of 1,048,576 visits',
    'run:display-visits-beyond-bound': 'answer past the visit bound',
    'run:display-bytes-at-bound': 'answer of 16 MiB of text',
    'run:display-bytes-beyond-bound': 'answer past the text bound',
    'model:display-utf8-at-bound': 'answer of 16 MiB of text',
    'model:display-utf8-beyond-bound': 'answer past the text bound',
}


def collect(stage: Path) -> tuple[list, list, dict]:
    """(traced runs, outcome-only runs, untraced runs and why), staged under `stage`."""
    cm = load('check_model', HERE / 'check-model.py')
    cm.BUILD = stage
    cs = cm.cs
    expected = json.loads((GOLDEN / 'vm-expected.json').read_text())
    traced, outcomes, skipped = [], [], {}

    for name, case in expected['cases'].items():
        traced.append(Run('golden', name, GOLDEN / f'{name}.kimg', case['argv'][1:], frozen=case))
    for name, listed in expected['invocations'].items():
        for row in listed:
            words = row['argv'][1:]
            traced.append(Run('invocation', f"{name}:{' '.join(words)}", GOLDEN / f'{name}.kimg', words, frozen=row))
    for name, case in expected['cases'].items():
        if case.get('outcome') == 'Unsupported':
            continue
        traced.append(Run('fuel', f'{name}@0', GOLDEN / f'{name}.kimg', cm.fuel_argv(case, '0')[1:]))
    traced.append(Run('fuel', 'value-on@1', GOLDEN / 'value-on.kimg', cm.fuel_argv(expected['cases']['value-on'], '1')[1:]))

    for label, path, plan, fuel, want, calls in cm.admitted_controls():
        if label in UNTRACED:
            skipped[label] = UNTRACED[label]
            continue
        words = cs.run_argv(plan, {'fuel': fuel})[1:]
        traced.append(Run('admitted', label, path, words, frozen={'want': want, 'calls': calls, 'fuel': fuel}))
    for name, path in cm.inspection_controls():
        traced.append(Run('inspection', name, path, ['main', '1000000']))
    for label, path, words, verdict, got, admitted in cm.argument_controls():
        if verdict is None:
            traced.append(Run('argument', label, path, list(words)))
        else:
            outcomes.append(Run('argument-refused', label, path, list(words), frozen={'verdict': verdict}))
    for label, path, want in cm.controls():
        outcomes.append(Run('refusal', label, path, ['main', '1000000'], frozen={'want': want}))
    return traced, outcomes, skipped
