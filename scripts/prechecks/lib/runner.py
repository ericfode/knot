"""Run checks in dependency order on worker threads, with per-check budgets, and assemble the report."""
from __future__ import annotations

import threading
import time
import traceback
from dataclasses import dataclass, field

from .context import Context, timeout_scale
from .model import CheckResult, Condition, severity_rank


@dataclass
class Check:
    id: str
    name: str
    title: str
    run: object                     # callable(ctx) -> CheckResult
    budget: float = 10.0            # soft budget in seconds (fast tier)
    needs: tuple = ()               # check ids that must finish first
    slow: bool = False              # only in the slow tier


@dataclass
class Outcome:
    check: Check
    result: CheckResult
    seconds: float = 0.0
    timed_out: bool = False


def _call(check: Check, ctx: Context, box: dict) -> None:
    try:
        box['result'] = check.run(ctx).finish()
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
                box: dict = {}
                thread = threading.Thread(target=_call, args=(check, ctx, box), daemon=True)
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
                result = CheckResult(outcome='unavailable', reason=f'timeout after {check.budget * scale * budget_env:.0f}s')
            else:
                result = box['result']
            done[check_id] = Outcome(check, result, round(time.monotonic() - started, 3), timed_out)
            if progress:
                progress(done[check_id])
        if running or pending:
            time.sleep(0.02)
    return [done[c.id] for c in checks]


def summarize(outcomes: list[Outcome], fail_on: str = 'major') -> dict:
    """Exit-code policy: only new or changed executor conditions at or above `fail_on` fail the run."""
    threshold = severity_rank(fail_on) if fail_on != 'none' else 99
    failing = [c for o in outcomes for c in o.result.conditions
               if c.actor == 'executor' and c.status in ('new', 'changed') and severity_rank(c.severity) >= threshold]
    errors = [o for o in outcomes if o.result.outcome == 'error']
    if errors:
        code = 1
    elif failing:
        code = 3
    else:
        code = 0
    counts: dict[str, int] = {}
    for outcome in outcomes:
        for condition in outcome.result.conditions:
            key = f'{condition.severity}/{condition.status}'
            counts[key] = counts.get(key, 0) + 1
    return {'exit': code, 'failing': len(failing), 'errors': len(errors), 'counts': counts}


def all_conditions(outcomes: list[Outcome]) -> list[Condition]:
    return [c for o in outcomes for c in o.result.conditions]
