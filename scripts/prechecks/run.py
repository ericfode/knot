#!/usr/bin/env python3
"""Pre-review checks: compare two views of one fact, report only where they disagree.

    npm run -s prechecks -- [--base <ref>] [--json]

Runs the deterministic checks C1-C8 on the current tree (the working copy, including uncommitted and
untracked files) against a base (default: the merge-base with main, or the effective base of a stacked
increment). Exit 0: no new or changed executor-actionable condition at or above --fail-on (default
major). Exit 3: at least one. Exit 1: a check crashed. Exit 2: usage error. Exit 4 (--strict only): nothing
failed but some check or rule did not run. Coordinator- and upstream-actor conditions never fail the run.
A check in which a rule did not run is `partial`, and one that could not run at all is `unavailable`:
neither is ever reported as a pass, and both are listed by name with their reasons.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import context as context_mod  # noqa: E402
from lib import ledger as ledger_mod  # noqa: E402
from lib import report as report_mod  # noqa: E402
from lib import runner as runner_mod  # noqa: E402
from lib.gitx import Repo  # noqa: E402
from lib.model import SEVERITIES  # noqa: E402
import checks as checks_mod  # noqa: E402


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='prechecks', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--repo', help='repository to check (default: the current directory\'s)')
    p.add_argument('--head', help='check a committed revision instead of the working copy')
    p.add_argument('--base', help='compare against this ref (default: merge-base with main, or the effective base)')
    p.add_argument('--inc', help='increment id (default: the campaign/<id> branch, or with --head the one campaign ref '
                                 'that names that commit; `none` for no increment)')
    p.add_argument('--main-ref', help='the trunk ref (default: main, then origin/main)')
    p.add_argument('--manifest', help='increment manifest file (default: docs/compiler-campaign/increments/<id>.json on main)')
    p.add_argument('--ledger', help='known-conditions ledger file (default: read from main)')
    p.add_argument('--upstream', action='append', default=[], metavar='ID[=REF]',
                   help='declare an upstream increment this branch is stacked on (repeatable)')
    p.add_argument('--tier', choices=('fast', 'slow', 'all'), default='fast',
                   help='fast (default): the pre-review stage; slow (or all): the same checks with their minute-scale extras')
    p.add_argument('--only', help='comma-separated check ids, for example C3,C4')
    p.add_argument('--skip', help='comma-separated check ids to skip')
    p.add_argument('--jobs', type=int, default=4)
    p.add_argument('--fail-on', choices=('none',) + SEVERITIES, default='major')
    p.add_argument('--strict', action='store_true',
                   help='exit 4 when some check or rule did not run (unavailable or partial) and nothing else fails; '
                        'the default reports the gap but lets the run pass on the rules that could run')
    p.add_argument('--json', action='store_true', help='print the full report as JSON on stdout')
    p.add_argument('--out', help='output directory (default: .local/prechecks/<head8>/)')
    p.add_argument('--no-write', action='store_true', help='do not write report files')
    p.add_argument('--verbose', action='store_true', help='also list known conditions')
    p.add_argument('--list', action='store_true', help='list the checks and exit')
    p.add_argument('--emit-ledger', action='store_true',
                   help='print ledger entries that would acknowledge every new condition (for the coordinator)')
    return p


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    if args.list:
        for check in checks_mod.load():
            print(f'{check.id} {check.name}: {check.title}')
        return 0
    only = set(args.only.split(',')) if args.only else None
    skip = set(args.skip.split(',')) if args.skip else None
    repo = Repo(args.repo or Path.cwd())
    try:
        repo = Repo(repo.top())
    except Exception:
        print('prechecks: not inside a git repository', file=sys.stderr)
        return 2
    started = time.monotonic()
    try:
        ctx = context_mod.build(repo, head=args.head, base=args.base, inc=args.inc, main_ref=args.main_ref,
                                manifest_path=args.manifest, ledger_path=args.ledger, tier=args.tier, jobs=args.jobs,
                                upstream=args.upstream, options={'fail_on': args.fail_on})
    except SystemExit as error:
        print(error, file=sys.stderr)
        return 2
    if args.head and args.inc is None and ctx.inc is None:
        print(f'prechecks: no campaign/<id> ref names {args.head}; running without an increment '
              '(manifest, ownership and ledger lookups need --inc <id>; `--inc none` silences this)', file=sys.stderr)
    selected = checks_mod.load(only, skip)
    if args.tier == 'all':
        args.tier = ctx.tier = 'slow'

    def progress(outcome):
        print(f'{outcome.check.id} {outcome.check.name}: {outcome.result.outcome} ({outcome.seconds:.1f}s)', file=sys.stderr)

    outcomes = runner_mod.execute(selected, ctx, progress=progress)
    for outcome in outcomes:
        ctx.ledger.annotate(outcome.result.conditions)
    out_dir = Path(args.out) if args.out else ctx.scratch / (ctx.head_commit or 'tree')[:8]
    report = None
    if not args.no_write:
        report = report_mod.write(ctx, outcomes, args.fail_on, out_dir, args.strict)
    if args.emit_ledger:
        entries = [ledger_mod.entry_for(c) for o in outcomes for c in o.result.conditions if c.status == 'new']
        print(json.dumps(entries, indent=1))
        return 0
    if args.json:
        print(json.dumps(report or report_mod.to_json(ctx, outcomes, args.fail_on, args.strict), indent=1, sort_keys=True))
    else:
        sys.stdout.write(report_mod.text(ctx, outcomes, args.fail_on, verbose=args.verbose, strict=args.strict))
        print(f'({time.monotonic() - started:.1f}s; report in {out_dir})' if not args.no_write else f'({time.monotonic() - started:.1f}s)')
    return runner_mod.summarize(outcomes, args.fail_on, args.strict)['exit']


if __name__ == '__main__':
    sys.exit(main())
