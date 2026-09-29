"""C8 perch-coherence: builds the packets for the seven advisory Perch rules; the live verdicts are the coordinator's.

The check itself is deterministic and offline: it selects claims and their evidence (packets/builders.py) and
writes `.local/prechecks/packets/<increment>/<head8>/<rule>/<n>.md`. It raises no condition, because a packet is a
question, not a finding; verdicts arrive only from a live Perch run of the main checkout
(`node scripts/prechecks-perch-run.mjs`), stay advisory (`gate: false`) until calibrated, and must be confirmed
deterministically before any code change (AGENTS.md: prove or test a suspected defect). A packet whose evidence
does not resolve is reported unavailable, never sent: missing evidence is not a pass.
"""
from __future__ import annotations

from lib.model import CheckResult
from lib.runner import Check
from packets.build import build

ID = 'C8'


def run(ctx) -> CheckResult:
    result = CheckResult()
    if ctx.base is None:
        return CheckResult(outcome='not-applicable', reason='no base to build diff-scoped packets against')
    if ctx.identity:
        return CheckResult(outcome='not-applicable', reason='identity: no changed claim or evidence')
    out = ctx.scratch / 'packets'
    report = build(ctx, out_dir=out)
    total = 0
    for rule, row in report.items():
        total += row['built']
        result.rules_run.append(rule)
        if row['unavailable']:
            result.rules_unavailable[rule] = f"{len(row['unavailable'])} packet(s) unavailable: " + \
                '; '.join(sorted({u['reason'] for u in row['unavailable']}))[:200]
    result.facts = {'packets': {rule: row['built'] for rule, row in report.items()}, 'total': total,
                    'directory': f'.local/prechecks/packets/{ctx.inc or "none"}/{(ctx.head_commit or "tree")[:8]}'}
    result.notes.append(f'{total} advisory packet(s) built; run them live from the main checkout '
                        '(node scripts/prechecks-perch-run.mjs --live), never from a linked worktree')
    if total == 0:
        result.outcome = 'not-applicable'
        result.reason = 'no packet-worthy claim in the changed documents'
    return result


CHECK = Check(ID, 'perch-coherence', 'advisory Perch packets: claims against the evidence that decides them', run, budget=20)
