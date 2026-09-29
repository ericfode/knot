#!/usr/bin/env python3
"""Build the calibration set for the advisory Perch rules from git history (tests/prechecks/perch-controls/).

    python3 scripts/prechecks/controls.py [--specs tests/prechecks/perch-controls/specs.json]

Each spec names a rule, a split (dev `broken` or `clean`, or `held-out` with its expected label), an increment and the
commits to build from. The packet
is chosen by the unmodified builders, by text anchors that must all occur in a built packet (the first match, with
the per-rule cap lifted to 500: a control tests the rule, and the cap only limits which claims a live run asks); a spec that
does not find its packet is reported and skipped, never faked. A spec may instead give `excerpt`: verbatim line
ranges of files at the head commit, for a defect passage that the builders' selection does not reach (the header
says so). Held-out specs come from the design's control table, not from any finding's evidence.

Nothing here calls Perch. `cases.json` records the expected label of every packet, which the coordinator's live
run compares with the probabilities it gets (each rule's floor is its `min` in .perch/rules/prechecks.yaml). A stub
probability is never calibration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import context as context_mod  # noqa: E402
from lib.gitx import Repo  # noqa: E402
from packets import common as C  # noqa: E402
from packets.builders import BUILDERS  # noqa: E402

DEFAULT = 'tests/prechecks/perch-controls'


def main_at(repo: Repo, head: str) -> str:
    when = repo.commit_time(head)
    found = repo.out('rev-list', '-1', '--first-parent', f'--before={when}', 'main', check=False)
    return found or 'main'


def excerpt_packet(repo: Repo, spec: dict) -> C.Packet:
    head = repo.rev_parse(spec['head'])
    sources, claim, evidence = [], [], []
    for part, target in (('claim', claim), ('evidence', evidence)):
        for item in spec['excerpt'][part]:
            blob = repo.blob(f"{head}:{item['path']}")
            if blob is None:
                raise SystemExit(f"{spec['id']}: {item['path']} is missing at {head[:8]}")
            text = blob.decode('utf-8', 'replace')
            lines = text.split('\n')
            a, b = item['lines']
            body = '\n'.join(lines[a - 1:b])
            label = f"`{item['path']}:{a}-{b}`" + (f" ({item['note']})" if item.get('note') else '')
            target.append(f'{label}\n\n' + (C.fence(C.numbered(body, a)) if part == 'evidence' else '\n'.join('> ' + l for l in body.split('\n'))))
            sources.append(C.Source(item['path'], head, C.sha256(text)))
    return C.Packet(spec['rule'], spec['id'], '\n\n'.join(claim), '\n\n'.join(evidence), sources, {})


def build_one(repo: Repo, spec: dict, scratch: Path):
    head = repo.rev_parse(spec['head'])
    if head is None:
        return None, f"unknown head {spec['head']}"
    if 'excerpt' in spec:
        base = repo.rev_parse(spec['base']) if spec.get('base') else None
        return (excerpt_packet(repo, spec), head, base, 'manual-excerpt'), ''
    manifest = None
    if spec.get('manifest'):
        manifest = scratch / f"{spec['id']}.manifest.json"
        manifest.write_text(json.dumps({'id': spec['increment'], **spec['manifest']}))
    ctx = context_mod.build(repo, head=head, base=spec.get('base'), inc=spec['increment'],
                            main_ref=spec.get('main_at') or main_at(repo, head), manifest_path=str(manifest) if manifest else None,
                            upstream=spec.get('upstream') or [], scratch=scratch / 'work',
                            options={'packet_limit': spec.get('limit', 500)})
    packets, _missing = BUILDERS[spec['rule']](ctx)
    matches = []
    for packet in packets:
        text = packet.claim + '\n' + packet.evidence
        if all(anchor in text for anchor in spec.get('anchors', [])):
            matches.append(packet)
    if not matches:
        return None, f"no built packet contains all anchors {spec.get('anchors')} ({len(packets)} packets built)"
    packet = matches[spec.get('choose', 0)]
    return (packet, head, ctx.base_commit, 'builder'), ''


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default='.')
    ap.add_argument('--specs', default=f'{DEFAULT}/specs.json')
    ap.add_argument('--out', default=DEFAULT)
    args = ap.parse_args(argv)
    repo = Repo(args.repo)
    specs = json.loads(Path(args.specs).read_text())
    out = Path(args.out)
    cases, skipped = [], []
    with tempfile.TemporaryDirectory(prefix='prechecks-controls-') as tmp:
        scratch = Path(tmp)
        for spec in specs['controls']:
            built, reason = build_one(repo, spec, scratch)
            if not built:
                skipped.append({'id': spec['id'], 'reason': reason})
                print(f"skipped {spec['id']}: {reason}", file=sys.stderr)
                continue
            packet, head, base, how = built
            text = C.render(packet, inc=spec['increment'], head=head, base=base)
            if how == 'manual-excerpt':
                text = text.replace('builder=scripts/prechecks/packets@', 'builder=manual-excerpt@', 1)
            path = Path(spec['rule']) / f"{spec['split']}-{spec['id']}.md"
            (out / path.parent).mkdir(parents=True, exist_ok=True)
            (out / path).write_text(text, encoding='utf-8')
            cases.append({'id': spec['id'], 'rule': spec['rule'], 'split': spec['split'], 'expected': spec['expected'],
                          'packet': path.as_posix(), 'sha256': hashlib.sha256(text.encode()).hexdigest(),
                          'increment': spec['increment'], 'head': head, 'base': base, 'how': how, 'note': spec.get('note', '')})
    document = {'schema': 1, 'note': specs.get('note', ''), 'cases': cases, 'gaps': specs.get('gaps', []), 'skipped': skipped}
    (out / 'cases.json').write_text(json.dumps(document, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    print(f'{len(cases)} controls built, {len(skipped)} skipped')
    return 1 if skipped else 0


if __name__ == '__main__':
    sys.exit(main())
