#!/usr/bin/env python3
"""Replay the historical control table: accepted tips as clean controls, confirmed regressions as broken controls.

    python3 scripts/prechecks/replay.py [--only classify,recursion] [--table tests/prechecks/replay/contexts.json] [--json]

Each context runs the whole fast tier on a committed revision, once with the default policy and once with the proposed
ledger (tests/prechecks/replay/proposed-ledger.json), and compares the executor conditions of severity major or higher
with the table. A clean control (an accepted, merged tip) must end with none once its accepted debt is ledgered; a broken
control (a tip that carried a defect the reviewers confirmed) must keep exactly the conditions that report it, ledger or not.

It needs the campaign history: a checkout of the repository that has the campaign branches' commits, not the gate's export.
A context whose commit is absent is skipped and reported. The proposed ledger is never read by the suite: authority stays
on main (docs/compiler-campaign/known-conditions.json), where the coordinator adopts entries it accepts.
"""
from __future__ import annotations

import argparse
import collections
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_TABLE = ROOT / 'tests/prechecks/replay/contexts.json'
FAILING = ('major', 'blocking')


def residual(report: dict) -> dict[str, int]:
    """{check.rule: count} of the executor conditions of severity major or higher that no ledger entry acknowledges."""
    found: collections.Counter = collections.Counter()
    for check in report['checks']:
        for condition in check['conditions']:
            if condition['actor'] == 'executor' and condition['severity'] in FAILING and condition['ledger']['status'] != 'known':
                found[f"{condition['check']}.{condition['rule']}"] += 1
    return dict(sorted(found.items()))


def compare(context: dict, default: dict, ledgered: dict) -> list[str]:
    """Differences between a context's expectations and what its two runs reported."""
    problems = []
    for label, expected, actual in (('default', context['default'], default), ('with the ledger', context['with_ledger'], ledgered)):
        if actual['exit'] != expected['exit']:
            problems.append(f"{label}: exit {actual['exit']}, expected {expected['exit']}")
        if actual['executor_major'] != expected['executor_major']:
            problems.append(f"{label}: executor conditions {actual['executor_major']}, expected {expected['executor_major']}")
    return problems


def run_suite(repo: Path, context: dict, ledger: Path | None) -> dict:
    command = [sys.executable, '-B', str(HERE / 'run.py'), '--repo', str(repo), '--head', context['head'], '--main-ref', context['main_ref'],
               '--inc', context['inc'], '--json', '--no-write']
    if context.get('base'):
        command += ['--base', context['base']]
    if ledger is not None:
        command += ['--ledger', str(ledger)]
    proc = subprocess.run(command, capture_output=True, text=True)
    if proc.returncode not in (0, 3):
        raise RuntimeError(f"{context['name']}: the suite exited {proc.returncode}: {proc.stderr.strip()[-300:]}")
    report = json.loads(proc.stdout)
    return {'exit': report['exit'], 'executor_major': residual(report)}


def has_commit(repo: Path, sha: str) -> bool:
    return subprocess.run(['git', '-C', str(repo), 'cat-file', '-e', f'{sha}^{{commit}}'], capture_output=True).returncode == 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default=str(ROOT), help='repository with the campaign history (default: this checkout)')
    ap.add_argument('--table', default=str(DEFAULT_TABLE))
    ap.add_argument('--only', help='comma-separated context names')
    ap.add_argument('--json', action='store_true', help='print the results as JSON')
    args = ap.parse_args(argv)
    table = json.loads(Path(args.table).read_text(encoding='utf-8'))
    ledger = (Path(args.table).parent / table['ledger']) if table.get('ledger') else None
    only = set(args.only.split(',')) if args.only else None
    repo = Path(args.repo)
    results, failed = [], False
    for context in table['contexts']:
        if only and context['name'] not in only:
            continue
        row = {'name': context['name'], 'kind': context['kind']}
        needed = [context['head'], context['main_ref']] + ([context['base']] if context.get('base') else [])
        if not all(has_commit(repo, sha) for sha in needed):
            row['status'] = 'skipped: the campaign history is not in this repository'
        else:
            default = run_suite(repo, context, None)
            ledgered = run_suite(repo, context, ledger)
            problems = compare(context, default, ledgered)
            row.update(status='ok' if not problems else 'MISMATCH', default=default, with_ledger=ledgered, problems=problems)
            failed = failed or bool(problems)
        results.append(row)
        if not args.json:
            print(f"{row['name']:<12} {row['kind']:<7} {row['status']}"
                  + ('' if 'default' not in row else f"  exit {row['default']['exit']} -> {row['with_ledger']['exit']} with the ledger"))
            for problem in row.get('problems', []):
                print(f'    {problem}')
    if args.json:
        print(json.dumps(results, indent=1, sort_keys=True))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
