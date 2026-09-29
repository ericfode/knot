"""Conditions, fingerprints and check results.

A condition is one disagreement between two views of a fact. Its fingerprint hashes the check, the
rule and a subject key that never contains a line number, so it survives unrelated edits and can be
subtracted against the known-conditions ledger.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

SEVERITIES = ('info', 'minor', 'major', 'blocking')
ACTORS = ('executor', 'coordinator', 'upstream')
OUTCOMES = ('pass', 'conditions', 'partial', 'unavailable', 'not-applicable', 'error')


def severity_rank(name: str) -> int:
    return SEVERITIES.index(name)


def raised(name: str) -> str:
    """One severity step up (the ratchet's regression rule)."""
    return SEVERITIES[min(severity_rank(name) + 1, len(SEVERITIES) - 1)]


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, default=str)


def fingerprint(check: str, rule: str, subject) -> str:
    return hashlib.sha256(f'{check}|{rule}|{canonical(subject)}'.encode()).hexdigest()[:20]


@dataclass
class Condition:
    check: str
    rule: str
    severity: str
    subject: dict
    expected: str = ''
    observed: str = ''
    actor: str = 'executor'
    value: object = None
    evidence: dict = field(default_factory=dict)
    fix_hint: str = ''
    status: str = 'new'                # new | changed | known
    ledger_entry: str | None = None

    def __post_init__(self):
        assert self.severity in SEVERITIES, self.severity
        assert self.actor in ACTORS, self.actor

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.check, self.rule, self.subject)

    @property
    def id(self) -> str:
        return f'{self.check}.{self.rule}'

    def to_json(self) -> dict:
        return {'check': self.check, 'rule': self.rule, 'severity': self.severity, 'actor': self.actor,
                'subject': self.subject, 'fingerprint': self.fingerprint, 'value': self.value,
                'expected': self.expected, 'observed': self.observed, 'evidence': self.evidence,
                'fix_hint': self.fix_hint, 'ledger': {'status': self.status, 'entry': self.ledger_entry}}

    def line(self) -> str:
        where = self.subject.get('path') or self.subject.get('target') or self.subject.get('commit') \
            or self.subject.get('probe') or next(iter(self.subject.values()), '')
        return f'[{self.severity}] {self.id} {where}: {self.observed or self.expected}'.strip()


@dataclass
class CheckResult:
    outcome: str = 'pass'
    conditions: list = field(default_factory=list)
    reason: str = ''
    facts: dict = field(default_factory=dict)
    rules_run: list = field(default_factory=list)
    rules_unavailable: dict = field(default_factory=dict)     # could not look: never a pass
    rules_na: dict = field(default_factory=dict)              # nothing to look at in this tree or run: {rule: why}
    notes: list = field(default_factory=list)

    def finish(self):
        """Settle the outcome. `pass` means every rule ran and found nothing; a check that found nothing but had a rule
        that did not run is `partial`, never a pass (DESIGN 2.2: `unavailable` never counts as a pass)."""
        if self.outcome in ('pass', 'conditions', 'partial'):
            if self.conditions:
                self.outcome = 'conditions'
            elif self.rules_unavailable:
                self.outcome = 'partial'
            else:
                self.outcome = 'pass'
        return self

    def na(self, rules, reason: str) -> None:
        """Say that these rules had nothing to look at (an absent input artifact, an empty diff), so they are neither run nor unavailable."""
        for rule in ([rules] if isinstance(rules, str) else rules):
            self.rules_na[rule] = reason

    @property
    def incomplete(self) -> bool:
        """True when some rule, or the whole check, did not run."""
        return self.outcome in ('unavailable', 'partial') or bool(self.rules_unavailable)


def not_applicable(reason: str) -> CheckResult:
    return CheckResult(outcome='not-applicable', reason=reason)


def unavailable(reason: str) -> CheckResult:
    return CheckResult(outcome='unavailable', reason=reason)
