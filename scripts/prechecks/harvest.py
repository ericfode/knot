#!/usr/bin/env python3
"""One-shot harvest of reviewers' probes into the frozen C1 registry (tests/prechecks/registry/).

The inputs are session scratch that is deleted eventually (round directories under `review/<inc>/` and
the findings that cite their files), so this ran once, at build time, and its output is committed:

  lang.jsonl   single-file `.bend` probes cited by dev-round findings, with pinned-seed verdicts
  vm.jsonl     `.plan.json` probes cited by dev-round findings (family V; no verdicts, stored for later)
  quarantine   probes created at or after the held-out cutoff, copied unread to an ignored directory;
               they are admitted to the registry only after replay has measured held-out recall

Rounds whose review started at or after the cutoff are held out: their findings are never opened here.
Nothing named `.env*` is ever opened. Rerun only with a scratch directory that still exists.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.seed import SEED_REVISION, Seed  # noqa: E402

CUTOFF = '2026-09-28T12:00:00Z'
MAX_BYTES = 200_000
CITE = re.compile(r'[\w./~+@-]*\.(?:bend|plan\.json)\b')
REPO_DIRS = ('src/', 'tests/', 'packages/', 'research/', '.toolchain/', 'vm/', 'docs/', 'scripts/', 'tools/', 'bench/')
SKIP_NAMES = re.compile(r'(?:-?LAWS|-?PROOF)\.bend$|-cli\.bend$|^\.bend$|^\.plan\.json$')
REGISTRY_BYTES = 32_000
QUARANTINE_DIR_CAP = 100          # a directory with more probes than this is a generated grid, not a witness
QUARANTINE_INC_CAP = 500
# The classes C1 replays (DESIGN 3.1): the primary set and the agent-only recurrence set.
FAMILIES = {
    'd4-seed-differential-grid', 'type-and-literal-form-grid-d4', 'lexical-perturbation-differential',
    'binder-spelling-grid-d4', 'empty-datatype-d4', 'let-and-dead-region-form-grid-d4',
    'import-and-path-spelling-differential', 'd4-ledger-recompute', 'diagnostic-position-and-precedence',
    'classification-precedence-and-spec-table', 'host-abi-type-kind-matrix', 'helper-vs-oracle',
    'cross-implementation-differential', 'generated-input-property-tests', 'd20-nonscalar-rule-churn',
    'shadowing-and-site-identity', 'checker-quantity-and-promotion-interactions', 'conservative-unsupported-gap',
}


def is_secret(name: str) -> bool:
    return name == '.env' or name.startswith('.env.')


def index_files(review: Path) -> list:
    """(relative path, absolute path, mtime) of every probe-sized `.bend` / `.plan.json` below `review`.

    Exported repository trees (a `package.json` or `perch.yaml` at their root) are pruned except for
    their `.local` directory, where reviewers usually put probes.
    """
    found = []
    for directory, dirs, files in os.walk(review):
        dirs[:] = sorted(d for d in dirs if not is_secret(d) and d not in ('.git', 'node_modules', '.toolchain', '.perch',
                                                                            '__pycache__'))
        if 'package.json' in files or 'perch.yaml' in files:
            dirs[:] = [d for d in dirs if d == '.local']
            files = []
        for name in files:
            if is_secret(name) or not (name.endswith('.bend') or name.endswith('.plan.json')):
                continue
            path = Path(directory) / name
            try:
                stat = path.stat()
            except OSError:
                continue
            if stat.st_size <= MAX_BYTES and path.is_file() and not path.is_symlink():
                found.append((path.relative_to(review).as_posix(), path, stat.st_mtime))
    return found


def normalize(token: str) -> str:
    match = re.search(r'/review/[^/]+/(.*)$', token)
    if match:
        token = match.group(1)
    token = re.sub(r'^(?:\.{1,3}/)+', '', token)
    token = re.sub(r'^[A-Z]/', '', token)
    return token


def resolve(token: str, files: list) -> list:
    rel = normalize(token)
    if not rel or rel.startswith(REPO_DIRS) or SKIP_NAMES.search(rel.rsplit('/', 1)[-1]):
        return []
    hits = [f for f in files if f[0] == rel or f[0].endswith('/' + rel)]
    if '/' not in rel and len(hits) > 1:
        return []                      # a bare basename that many probes share is not a citation of one file
    if not hits and '/' in rel:
        base = rel.rsplit('/', 1)[-1]
        only = [f for f in files if f[0].rsplit('/', 1)[-1] == base]
        hits = only if len(only) == 1 else []      # the citation's root differs, but the name is unique
    return hits[:4]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode_text(data: bytes) -> dict:
    try:
        return {'text': data.decode('utf-8')}
    except UnicodeDecodeError:
        import base64
        return {'b64': base64.b64encode(data).decode()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--scratch', required=True, help='directory containing review/<increment>/...')
    ap.add_argument('--findings', required=True)
    ap.add_argument('--replay', required=True)
    ap.add_argument('--root', required=True, help='repository root (for the pinned seed)')
    ap.add_argument('--registry', default='tests/prechecks/registry')
    ap.add_argument('--quarantine', default='.local/prechecks/quarantine')
    ap.add_argument('--cutoff', default=CUTOFF)
    ap.add_argument('--no-seed', action='store_true', help='skip seed verdicts (structure only)')
    args = ap.parse_args(argv)

    review = Path(args.scratch) / 'review'
    replay = json.load(open(args.replay, encoding='utf-8'))
    cutoff = datetime.datetime.fromisoformat(args.cutoff.replace('Z', '+00:00')).timestamp()
    info = {}
    for key, value in replay.items():
        if key == 'meta':
            continue
        for split in ('dev', 'held_out'):
            for row in value[split]:
                if isinstance(row, dict):
                    info[row['instance']] = (split, row.get('class') or key, row['increment'])
    # Only dev findings are ever read.
    citations = collections.OrderedDict()
    for line in open(args.findings, encoding='utf-8'):
        row = json.loads(line)
        split, family, inc = info.get(f"{row['id']}@{row['review_agent']}", (None, None, None))
        if split != 'dev':
            continue
        for token in CITE.findall(row['evidence'] + '\n' + row['fix']):
            if family not in FAMILIES and not token.endswith('.plan.json'):
                continue
            citations.setdefault((inc, token), (row['id'] + '@' + row['review_agent'], family))
    rows, seen = [], set()
    indexes = {}
    unresolved = 0
    for (inc, token), (finding, family) in citations.items():
        if inc not in indexes:
            indexes[inc] = index_files(review / inc) if (review / inc).is_dir() else []
        hits = resolve(token, indexes[inc])
        if not hits:
            unresolved += 1
        for rel, path, _mtime in hits:
            data = path.read_bytes()
            if len(data) > REGISTRY_BYTES:
                continue
            digest = sha256(data)
            if digest in seen:
                continue
            seen.add(digest)
            kind = 'vm' if rel.endswith('.plan.json') else 'lang'
            row = {'sha256': digest, 'kind': kind, 'family': family, 'increment': inc,
                   'source': {'finding': finding, 'cited': normalize(token), 'found': rel}}
            row.update(encode_text(data))
            rows.append(row)
    rows.sort(key=lambda r: (r['kind'], r['increment'], r['family'], r['sha256']))

    lang = [r for r in rows if r['kind'] == 'lang']
    if lang and not args.no_seed:
        seed = Seed(Path(args.root), Path(args.root) / '.local/prechecks/harvest')
        if not seed.available():
            print('pinned seed not available; rerun with --no-seed or install the toolchain', file=sys.stderr)
            return 1
        work = seed.scratch / 'programs'
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True)
        paths = {}
        for r in lang:
            text = r.get('text')
            if text is None:
                continue
            path = work / f"{r['sha256'][:16]}.bend"
            path.write_bytes(text.encode('utf-8'))
            paths[r['sha256']] = path
        parsed = seed.parse_many(list(paths.values()))
        for r in lang:
            path = paths.get(r['sha256'])
            if path is None:
                r['seed'] = None
                continue
            p = parsed[str(path)]
            standalone = not re.search(r'(?m)^import ', r['text'])
            r['standalone'] = standalone
            if not standalone:
                # `parse_book` never sees imports (the loader consumes them), so its verdict says nothing here.
                r['seed'] = {'parse': 'skipped', 'reason': 'imports need the loader and their sibling files'}
                continue
            verdict = {'parse': 'ok' if p['ok'] else 'reject', 'offset': p['beg'], 'expected': p['exp']}
            if p['ok']:
                check = seed.check_only(path)
                verdict['check'] = check['verdict']
                if check['verdict'] == 'accept' and re.search(r'(?m)^def main\b', r['text']):
                    run = seed.run(path)
                    verdict['run'] = run['verdict']
                    if run['verdict'] == 'accept':
                        verdict['stdout'] = run['stdout']
            r['seed'] = verdict
        r_revision = SEED_REVISION
        for r in lang:
            r['seed_revision'] = r_revision
        shutil.rmtree(work, ignore_errors=True)
    for r in rows:
        r['frozen_at'] = '2026-09-28'

    registry = Path(args.registry)
    registry.mkdir(parents=True, exist_ok=True)
    for kind in ('lang', 'vm'):
        body = ''.join(json.dumps(r, sort_keys=True, ensure_ascii=True) + '\n' for r in rows if r['kind'] == kind)
        (registry / f'{kind}.jsonl').write_text(body, encoding='utf-8')

    # Held-out probes: copied unread (bytes only) into the quarantine, indexed by path and digest.
    quarantine = Path(args.quarantine)
    quarantine.mkdir(parents=True, exist_ok=True)
    quarantined, listing = set(), []
    for inc in sorted(p.name for p in review.iterdir() if p.is_dir() and not is_secret(p.name)):
        files = [f for f in index_files(review / inc) if f[2] >= cutoff]
        per_dir = collections.Counter(f[0].rsplit('/', 1)[0] for f in files)
        taken = 0
        for rel, path, mtime in files:
            if per_dir[rel.rsplit('/', 1)[0]] > QUARANTINE_DIR_CAP or taken >= QUARANTINE_INC_CAP:
                continue
            data = path.read_bytes()
            digest = sha256(data)
            if digest in seen or digest in quarantined:
                continue
            quarantined.add(digest)
            taken += 1
            suffix = '.plan.json' if rel.endswith('.plan.json') else '.bend'
            target = quarantine / inc / f'{digest[:16]}{suffix}'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            listing.append({'sha256': digest, 'increment': inc, 'found': rel})
    (quarantine / 'index.jsonl').write_text(''.join(json.dumps(x, sort_keys=True) + '\n' for x in listing), encoding='utf-8')

    counts = collections.Counter(r['kind'] for r in rows)
    print(f"citations {len(citations)}, unresolved {unresolved}, registry lang {counts['lang']}, vm {counts['vm']}, "
          f"quarantined {len(listing)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
