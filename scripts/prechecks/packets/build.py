#!/usr/bin/env python3
"""Build self-contained Markdown packets for the advisory Perch rules from any checkout.

    npm run -s prechecks:packets -- --repo <path> --out <dir> [--head REV] [--base REF] [--inc ID] [--rules a,b]

Packets are read from git objects only and written to `<out>/<increment>/<head8>/<rule>/<n>.md`, the layout
that `.perch/rules/prechecks.yaml` selects. Nothing here contacts Perch or a provider. A packet whose
evidence cannot be resolved is reported `unavailable` and not written: missing evidence is never a pass.
Run the packets live only from the main checkout, with `scripts/prechecks-perch-run.mjs`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import context as context_mod  # noqa: E402
from lib.gitx import Repo  # noqa: E402
from packets import common as C  # noqa: E402
from packets.builders import BUILDERS  # noqa: E402


def build(ctx, rules=None, out_dir: Path | None = None) -> dict:
    """{rule: {built, unavailable, files}}; writes packets below `out_dir` when given."""
    report = {}
    head = C.head_label(ctx)
    label = (ctx.inc or 'none')
    for rule, builder in BUILDERS.items():
        if rules and rule not in rules:
            continue
        packets, missing = ([], [])
        if ctx.base is None:
            missing = [C.Unavailable(rule, '-', 'no base to build a diff-scoped packet against')]
        else:
            packets, missing = builder(ctx)
        files, rendered = [], []
        for packet in packets:
            text = C.render(packet, inc=ctx.inc, head=head, base=ctx.base_commit)
            if len(text.encode('utf-8')) > C.PACKET_LIMIT:
                missing.append(C.Unavailable(rule, packet.key, f'packet is over {C.PACKET_LIMIT // 1024} KB'))
                continue
            rendered.append((packet.key, text))
        directory = None
        if out_dir is not None:
            directory = Path(out_dir) / label / C.short(head, 8) / rule
            assert directory.parent.parent.parent == Path(out_dir), directory
            if directory.exists():
                for stale in directory.glob('*.md'):
                    stale.unlink()
            directory.mkdir(parents=True, exist_ok=True)
        for number, (key, text) in enumerate(rendered, 1):
            name = f'{number:04d}.md'
            if directory is not None:
                (directory / name).write_text(text, encoding='utf-8')
            files.append({'file': f'{label}/{C.short(head, 8)}/{rule}/{name}', 'key': key, 'bytes': len(text.encode('utf-8'))})
        report[rule] = {'built': len(rendered), 'files': files,
                        'unavailable': [{'key': u.key, 'reason': u.reason} for u in missing]}
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.', help='repository to read (a git checkout or worktree)')
    ap.add_argument('--out', help='output directory (default: <repo>/.local/prechecks/packets)')
    ap.add_argument('--head', help='revision to build from (default: the working copy, labelled <HEAD>+worktree.<tree> throughout)')
    ap.add_argument('--base', help='base ref (default: merge-base with main, or the effective base)')
    ap.add_argument('--inc', help='increment id (default: from a campaign/<id> branch)')
    ap.add_argument('--main-ref')
    ap.add_argument('--manifest')
    ap.add_argument('--upstream', action='append', default=[])
    ap.add_argument('--rules', help='comma-separated rule names (default: all seven)')
    ap.add_argument('--limit', type=int, default=C.PER_RULE_LIMIT,
                    help=f'packets per rule (default {C.PER_RULE_LIMIT}: packets/limits.json, the same number as the live runner\'s --cap)')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    repo = Repo(args.repo)
    try:
        repo = Repo(repo.top())
    except Exception:
        print('prechecks:packets: not a git repository', file=sys.stderr)
        return 2
    try:
        ctx = context_mod.build(repo, head=args.head, base=args.base, inc=args.inc, main_ref=args.main_ref,
                                manifest_path=args.manifest, upstream=args.upstream,
                                options={'packet_limit': args.limit})
    except SystemExit as error:
        print(error, file=sys.stderr)
        return 2
    out = Path(args.out) if args.out else repo.root / '.local/prechecks/packets'
    report = build(ctx, set(args.rules.split(',')) if args.rules else None, out)
    if args.json:
        print(json.dumps({'increment': ctx.inc, 'head': ctx.head_commit, 'base': ctx.base_commit, 'out': str(out),
                          'builder': C.builder_id(), 'rules': report}, indent=1, sort_keys=True))
    else:
        total = sum(r['built'] for r in report.values())
        for rule, row in report.items():
            print(f"{rule:<32} {row['built']:>3} built, {len(row['unavailable'])} unavailable")
            for item in row['unavailable'][:3]:
                print(f"    unavailable {item['key']}: {item['reason']}")
        print(f'{total} packet(s) below {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
