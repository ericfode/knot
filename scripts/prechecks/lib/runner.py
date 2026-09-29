"""Run checks in dependency order on worker threads, with per-check budgets, and assemble the report.

A check that overruns its budget is reported `unavailable` and is also stopped: the runner raises the check's
cancel flag, every tool the check started through `ctx.run` is killed with its whole process group, and pools of
queued tool runs stop starting new ones (lib/proc.py). A guard that only relabelled the check would let the queued
work run on, keep the process alive and spend the host's time on a result nobody reads.
"""
from __future__ import annotations

import threading
import time
import traceback
from dataclasses import dataclass, field

from .context import Context, timeout_scale
from .model import CheckResult, Condition, severity_rank


UNREPORTED = 'not reported by the check: it neither ran nor said why it did not (a defect of the check)'


@dataclass
class Check:
    id: str
    name: str
    title: str
    run: object                     # callable(ctx) -> CheckResult
    budget: float = 10.0            # soft budget in seconds (fast tier)
    needs: tuple = ()               # check ids that must finish first
    slow: bool = False              # only in the slow tier
    rules: tuple = ()               # the documented rules: each ends a run in rules_run, rules_unavailable or rules_na
    groups: dict = field(default_factory=dict)   # an alias that stands for several rules: {'family-l': (rule, ...)}


def account(check: Check, result: CheckResult) -> CheckResult:
    """Every documented rule of a check that ran ends in exactly one state: it ran, it could not (unavailable), or it had nothing
    to look at (not applicable). A rule that the check did not report is made unavailable, so a rule that was forgotten, or
    renamed away from its documented name, is a loud gap in the coverage table and never a silent pass."""
    if result.outcome in ('unavailable', 'not-applicable', 'error'):
        return result                                  # the whole check is the gap: its outcome and reason say so
    seen = set(result.rules_run) | set(result.rules_unavailable) | set(result.rules_na)
    for alias, members in check.groups.items():
        if alias in seen:
            seen.update(members)
    for rule in check.rules:
        if rule not in seen:
            result.rules_unavailable[rule] = UNREPORTED
    return result


@dataclass
class Outcome:
    check: Check
    result: CheckResult
    seconds: float = 0.0
    timed_out: bool = False


class CheckContext:
    """The run context as one check sees it: every attribute of the Context, plus the `cancel` flag that the hang
    guard raises when the check overruns. `run` starts tools that the guard can kill. A check must not assign
    attributes; shared state goes through `ctx.publish` and the facts it returns."""

    def __init__(self, ctx: Context, cancel: threading.Event):
        object.__setattr__(self, '_ctx', ctx)
        object.__setattr__(self, 'cancel', cancel)

    def __getattr__(self, name):
        return getattr(self._ctx, name)

    def __setattr__(self, name, value):
        raise AttributeError(f'a check must not assign ctx.{name}')

    def run(self, argv, **kw):
        kw.setdefault('cancel', self.cancel)
        return self._ctx.run(argv, **kw)


def _call(check: Check, ctx: CheckContext, box: dict) -> None:
    try:
        box['result'] = account(check, check.run(ctx).finish()).finish()
    except Exception as error:      # a bug in a check must be visible, never a silent pass
        box['result'] = CheckResult(outcome='error', reason=f'{type(error).__name__}: {error}',
                                    notes=[traceback.format_exc(limit=6)])


def execute(checks: list[Check], ctx: Context, *, progress=None) -> list[Outcome]:
    pending = list(checks)
    done: dict[str, Outcome] = {}
    running: dict[str, tuple] = {}
    scale = timeout_scale()
    budget_env = ctx.options.get('budget_scale', 1.0)
    while pending or running:
        for check in list(pending):
            if all(dep in done or dep not in {c.id for c in checks} for dep in check.needs) and len(running) < ctx.jobs:
                box: dict = {'cancel': threading.Event()}
                thread = threading.Thread(target=_call, args=(check, CheckContext(ctx, box['cancel']), box), daemon=True)
                running[check.id] = (thread, box, time.monotonic(), check)
                thread.start()
                pending.remove(check)
        finished = []
        for check_id, (thread, box, started, check) in running.items():
            limit = check.budget * scale * budget_env
            if not thread.is_alive():
                finished.append((check_id, False))
            elif time.monotonic() - started > limit:
                finished.append((check_id, True))
        for check_id, timed_out in finished:
            thread, box, started, check = running.pop(check_id)
            if timed_out:
                box['cancel'].set()                     # stop the check's tools and its queued runs, not just the label
                result = CheckResult(outcome='unavailable', reason=f'timeout after {check.budget * scale * budget_env:.0f}s')
            else:
                result = box['result']
            done[check_id] = Outcome(check, result, round(time.monotonic() - started, 3), timed_out)
            if progress:
                progress(done[check_id])
        if running or pending:
            time.sleep(0.02)
    return [done[c.id] for c in checks]


def incomplete(outcomes: list[Outcome]) -> list[dict]:
    """Checks and rules that did not run: [{check, outcome, reason, rules: {rule: reason}}]. Never a pass."""
    rows = []
    for o in outcomes:
        if o.result.outcome in ('unavailable', 'error') or o.result.rules_unavailable or o.result.outcome == 'partial':
            rows.append({'check': o.check.id, 'name': o.check.name, 'outcome': o.result.outcome, 'reason': o.result.reason,
                         'rules': dict(o.result.rules_unavailable)})
    return rows


def summarize(outcomes: list[Outcome], fail_on: str = 'major', strict: bool = False) -> dict:
    """Exit-code policy: only new or changed executor conditions at or above `fail_on` fail the run (3). A check
    error is 1. With `strict`, a run in which some check or rule did not run and nothing else failed is 4: the
    default lets an implementer proceed on the rules that could run, but never calls the gap a pass."""
    threshold = severity_rank(fail_on) if fail_on != 'none' else 99
    failing = [c for o in outcomes for c in o.result.conditions
               if c.actor == 'executor' and c.status in ('new', 'changed') and severity_rank(c.severity) >= threshold]
    errors = [o for o in outcomes if o.result.outcome == 'error']
    gaps = incomplete(outcomes)
    if errors:
        code = 1
    elif failing:
        code = 3
    elif strict and gaps:
        code = 4
    else:
        code = 0
    counts: dict[str, int] = {}
    for outcome in outcomes:
        for condition in outcome.result.conditions:
            key = f'{condition.severity}/{condition.status}'
            counts[key] = counts.get(key, 0) + 1
    return {'exit': code, 'failing': len(failing), 'errors': len(errors), 'counts': counts,
            'incomplete': sum(1 for g in gaps if g['outcome'] != 'error'), 'strict': strict}


def all_conditions(outcomes: list[Outcome]) -> list[Condition]:
    return [c for o in outcomes for c in o.result.conditions]
