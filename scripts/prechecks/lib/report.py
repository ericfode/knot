"""Report assembly: JSON for tools, Markdown for reviewers, `known.txt` for the review harness."""
from __future__ import annotations

import json
from pathlib import Path

from .context import Context
from .model import SEVERITIES, severity_rank
from .runner import Outcome, all_conditions, summarize

VERSION = 1
LIST_LIMIT = 12          # conditions per rule printed in the terminal summary; JSON keeps them all


def to_json(ctx: Context, outcomes: list[Outcome], fail_on: str = 'major') -> dict:
    summary = summarize(outcomes, fail_on)
    return {
        'schema': VERSION,
        'increment': ctx.inc,
        'head': {'tree': ctx.head.treeish, 'commit': ctx.head_commit, 'worktree': ctx.worktree, 'dirty': ctx.dirty},
        'base': {'commit': ctx.base_commit, 'tree': ctx.base.treeish if ctx.base else None,
                 'kind': ctx.effective.kind if ctx.effective else ('explicit' if ctx.base else 'none'),
                 'stacked_on': ctx.effective.stacked_on if ctx.effective else []},
        'main_ref': ctx.main_ref,
        'manifest': ctx.manifest.source,
        'ledger': {'source': ctx.ledger.source, 'entries': len(ctx.ledger.entries)},
        'tier': ctx.tier,
        'fail_on': fail_on,
        'exit': summary['exit'],
        'summary': summary,
        'checks': [{'id': o.check.id, 'name': o.check.name, 'outcome': o.result.outcome, 'reason': o.result.reason,
                    'seconds': o.seconds, 'rules_run': o.result.rules_run,
                    'rules_unavailable': o.result.rules_unavailable, 'notes': o.result.notes,
                    'conditions': [c.to_json() for c in o.result.conditions]} for o in outcomes],
    }


def facts_json(ctx: Context, outcomes: list[Outcome]) -> dict:
    facts = {'head': ctx.head_commit, 'head_tree': ctx.head.treeish, 'base': ctx.base_commit,
             'commits_since_base': len(ctx.commits())}
    for outcome in outcomes:
        if outcome.result.facts:
            facts[outcome.check.id] = outcome.result.facts
    facts.update(ctx.facts)
    return facts


def known_lines(outcomes: list[Outcome]) -> list[str]:
    """Lines for the review harness: acknowledged or coordinator-only conditions reviewers must not re-report."""
    lines = []
    for condition in all_conditions(outcomes):
        if condition.status == 'known' or condition.actor != 'executor':
            where = condition.subject.get('path') or condition.subject.get('target') or condition.subject.get('commit') \
                or condition.subject.get('probe') or ''
            lines.append(f'{condition.fingerprint} {condition.id} {where}: {condition.observed or condition.expected}'
                         .replace('\n', ' ')[:300])
    return sorted(set(lines))


def markdown(ctx: Context, outcomes: list[Outcome], fail_on: str = 'major') -> str:
    report = to_json(ctx, outcomes, fail_on)
    out = [f"# Prechecks report", '',
           f"- increment: {ctx.inc or 'none'}",
           f"- head: {ctx.head_commit or 'none'}{' (working copy included)' if ctx.worktree else ''}",
           f"- base: {ctx.base_commit or 'none'} ({report['base']['kind']})",
           f"- exit: {report['exit']}  (fails on new or changed executor conditions of severity {fail_on} or higher)", '',
           '| check | outcome | seconds | new | changed | known |', '|---|---|---|---|---|---|']
    for o in outcomes:
        cs = o.result.conditions
        out.append(f"| {o.check.id} {o.check.name} | {o.result.outcome}{' (' + o.result.reason + ')' if o.result.reason else ''} "
                   f"| {o.seconds:.1f} | {sum(c.status == 'new' for c in cs)} | {sum(c.status == 'changed' for c in cs)} "
                   f"| {sum(c.status == 'known' for c in cs)} |")
    for status in ('new', 'changed'):
        rows = sorted((c for c in all_conditions(outcomes) if c.status == status),
                      key=lambda c: (-severity_rank(c.severity), c.id))
        if rows:
            out += ['', f'## {status.capitalize()} conditions', '']
            shown: dict[str, int] = {}
            for c in rows:
                shown[c.id] = shown.get(c.id, 0) + 1
                if shown[c.id] == LIST_LIMIT + 1:
                    out.append(f"- ... {sum(1 for x in rows if x.id == c.id) - LIST_LIMIT} more `{c.id}` conditions in report.json")
                if shown[c.id] > LIST_LIMIT:
                    continue
                out.append(f"- **{c.severity}** `{c.id}` ({c.actor}) {c.line().split(': ', 1)[0].split('] ', 1)[-1]}: "
                           f"{c.observed or c.expected}")
                if c.fix_hint:
                    out.append(f"  - fix: {c.fix_hint}")
    known = [c for c in all_conditions(outcomes) if c.status == 'known']
    if known:
        out += ['', f'## Known conditions ({len(known)}, not findings)', '']
    unavailable = [o for o in outcomes if o.result.outcome in ('unavailable', 'error')]
    if unavailable:
        out += ['', '## Unavailable checks (never a pass)', '']
        for o in unavailable:
            out.append(f"- {o.check.id} {o.check.name}: {o.result.outcome}: {o.result.reason}")
    return '\n'.join(out) + '\n'


def text(ctx: Context, outcomes: list[Outcome], fail_on: str = 'major', *, verbose: bool = False) -> str:
    report = to_json(ctx, outcomes, fail_on)
    lines = [f"prechecks: head {(ctx.head_commit or 'none')[:10]}{'+worktree' if ctx.worktree else ''}"
             f" base {(ctx.base_commit or 'none')[:10]} ({report['base']['kind']})"
             f"{' inc ' + ctx.inc if ctx.inc else ''}"]
    for o in outcomes:
        cs = sorted(o.result.conditions, key=lambda c: (-severity_rank(c.severity), c.id))
        head = f"{o.check.id} {o.check.name:<20} {o.result.outcome:<14} {o.seconds:5.1f}s"
        if o.result.reason:
            head += f'  ({o.result.reason})'
        lines.append(head)
        per_rule: dict[str, int] = {}
        for c in cs:
            if c.status == 'known' and not verbose:
                continue
            per_rule[c.id] = per_rule.get(c.id, 0) + 1
            if per_rule[c.id] == LIST_LIMIT + 1:
                lines.append(f"    ... {sum(1 for x in cs if x.id == c.id and (verbose or x.status != 'known')) - LIST_LIMIT} more {c.id} "
                             'condition(s) in report.json')
            if per_rule[c.id] > LIST_LIMIT:
                continue
            lines.append(f"    {c.status[:3]:<3} {c.line()}")
        hidden = sum(c.status == 'known' for c in cs) if not verbose else 0
        if hidden:
            lines.append(f'    ({hidden} known condition{"s" if hidden != 1 else ""} not shown)')
    summary = report['summary']
    lines.append(f"exit {summary['exit']}: {summary['failing']} failing condition(s), {summary['errors']} check error(s)")
    return '\n'.join(lines) + '\n'


def write(ctx: Context, outcomes: list[Outcome], fail_on: str, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    report = to_json(ctx, outcomes, fail_on)
    paths = {'report.json': json.dumps(report, indent=1, sort_keys=True) + '\n',
             'facts.json': json.dumps(facts_json(ctx, outcomes), indent=1, sort_keys=True, default=str) + '\n',
             'report.md': markdown(ctx, outcomes, fail_on),
             'known.txt': '\n'.join(known_lines(outcomes)) + ('\n' if known_lines(outcomes) else '')}
    for name, content in paths.items():
        (out_dir / name).write_text(content, encoding='utf-8')
    return report
