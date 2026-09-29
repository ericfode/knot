"""C4 receipt-integrity: a committed receipt against the tree it describes.

Rules (DESIGN 3.4). Scope is receipts added or changed between the effective base and head, never the
whole tree: main already carries 52 legacy receipt and evidence files with host paths.

  R1 host-path                    a host-specific path in a changed receipt
  R2 stale-receipt-hash           a recorded input hash differs from the recomputed one (ratcheted against base)
  R2 decorative-hash              a newly recorded hash field that no code reads
  R3 unowned-receipt-drift-predicted / corpus-glob-coupling
  R4 unowned-receipt-drift / own-receipt-stale / gate-red   from the implementer's own gate run
  R5 receipt-volatility / receipt-orphan / receipt-duplicate / receipt-flood
  R6 receipt-date-only            a receipt commit whose normalized content is unchanged
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from lib import gaterun
from lib import gates as gates_lib
from lib import globs
from lib import receipts as R
from lib.model import CheckResult, Condition, not_applicable
from lib.runner import Check

ID = 'C4'
HOST_PATH = re.compile(r'/Users/|/home/[^/\s"\']+/|/private/(?:tmp|var)|/var/folders|[.]claude/worktrees|'
                       r'[.]local/gates/run-|(?:[.][.]/){2,}[.]toolchain')
MEASUREMENT_KEY = re.compile(r'(?:peak_)?rss(?:_bytes)?$|load_?avg|host_load|cpu_seconds|wall_seconds|wall_ms', re.I)
DOC_INPUTS = re.compile(r'(?:^|/)(?:README|REPORT|HANDOFF|FIXTURES|GATES|CLASSIFICATION)\.md$|^docs/')
runner_excluded = gaterun.runner_excluded


def is_own(ctx, path: str, status: str) -> bool:
    return status == 'A' or ctx.manifest.is_owned(path) or path in set(ctx.manifest.get('receipts', []) or [])


def excerpt(text: str, match: re.Match, width: int = 60) -> str:
    start = max(match.start() - 20, 0)
    return text[start:match.end() + width].replace('\n', ' ')[:width + 40]


def host_paths(ctx, changed) -> list[Condition]:
    found = []
    for change in changed:
        text = R.read_text(ctx.head, change.path)
        if text is None:
            continue
        matches = list(HOST_PATH.finditer(text))
        if not matches:
            continue
        before = 0
        if ctx.base is not None and change.status != 'A':
            old = R.read_text(ctx.base, change.old_path or change.path)
            before = len(HOST_PATH.findall(old)) if old else 0
        if len(matches) <= before:
            continue                                  # pre-existing paths, not added by this branch
        own = is_own(ctx, change.path, change.status)
        found.append(Condition(
            ID, 'host-path', 'major', {'path': change.path}, value={'hits': len(matches)}, actor='executor' if own else 'coordinator',
            expected='no host-specific path in a committed receipt (tokens such as $ROOT, .toolchain, $BEND_LIB)',
            observed=f'{len(matches)} host path(s) ({before} at base), e.g. {excerpt(text, matches[0])!r}',
            evidence={'examples': sorted({excerpt(text, m) for m in matches[:20]})[:3]},
            fix_hint='Have the gate write path tokens, or drop the field; another checkout would show permanent drift.'))
    return found


def stale_hashes(ctx, changed) -> list[Condition]:
    found = []
    for change in changed:
        if not change.path.endswith('.json'):
            continue
        text = R.read_text(ctx.head, change.path)
        value = R.parse_json(text) if text else None
        if value is None:
            continue
        old_claims = {}
        if ctx.base is not None and change.status != 'A':
            old_text = R.read_text(ctx.base, change.old_path or change.path)
            old_value = R.parse_json(old_text) if old_text else None
            old_claims = {(p, path): sha for p, path, sha in R.hash_claims(old_value)} if old_value is not None else {}
        stale = []
        for pointer, claimed, recorded in R.hash_claims(value):
            path = R.repo_path(claimed)
            actual = ctx.head.sha256(path)
            if actual is None or actual == recorded or path.endswith('.gz'):
                continue
            if old_claims.get((pointer, claimed)) == recorded and ctx.base is not None and \
                    ctx.base.sha256(path) not in (None, recorded):
                continue                                # was already stale at base, with the same recorded hash
            stale.append(path)
        if stale:
            own = is_own(ctx, change.path, change.status)
            found.append(Condition(
                ID, 'stale-receipt-hash', 'major' if own else 'minor', {'path': change.path}, value={'stale': len(stale)},
                actor='executor' if own else 'coordinator',
                expected='every recorded input hash equals the sha256 of that file at head',
                observed=f'{len(stale)} recorded input hash(es) differ from head, e.g. {sorted(stale)[:3]}',
                evidence={'inputs': sorted(stale)[:12]}, fix_hint='Regenerate the receipt (or its gate) after the last source edit.'))
    return found


def decorative_hashes(ctx, changed) -> list[Condition]:
    found = []
    code = [p for p in ctx.head.files() if p.endswith(('.py', '.mjs', '.ts', '.js')) and p.split('/')[0] in
            ('tests', 'scripts', 'tools', 'vm', 'research')]
    for change in changed:
        if change.status != 'A' or not change.path.endswith('.json'):
            continue
        text = R.read_text(ctx.head, change.path)
        value = R.parse_json(text) if text else None
        if not isinstance(value, dict):
            continue
        for key, child in value.items():
            if not (isinstance(child, str) and R.HEX64.match(child) and (key == 'sha256' or key.endswith('_sha256'))):
                continue
            mentions = 0
            for path in code:
                body = ctx.head.text(path) or ''
                mentions += body.count(key)
                if mentions > 1:
                    break
            if mentions <= 1:
                found.append(Condition(ID, 'decorative-hash', 'minor', {'path': change.path, 'field': key},
                                       expected='a recorded hash is read back by some check',
                                       observed=f'{key!r} appears in {mentions} code mention(s): written, never verified',
                                       fix_hint='Verify it in the gate or drop the field.'))
    return found


def predicted_drift(ctx, changed_paths: set) -> list[Condition]:
    """Unchanged receipts whose recorded input hashes the branch invalidated: refreshed at merge, not by the executor."""
    if ctx.base is None:
        return []
    moved = {c.path for c in ctx.changes() if c.status in 'MRCTD'} | {c.old_path for c in ctx.changes() if c.old_path}
    if not moved:
        return []
    found = []
    for path in ctx.head.files():
        if path in changed_paths or not path.endswith('.json') or not R.is_receipt(path):
            continue
        if ctx.base.sha(path) is None:
            continue
        value = R.parse_json(R.read_text(ctx.head, path) or '')
        if value is None:
            continue
        hit = sorted({R.repo_path(p) for _pointer, p, sha in R.hash_claims(value)
                      if R.repo_path(p) in moved and sha == ctx.base.sha256(R.repo_path(p))})
        if hit:
            found.append(Condition(ID, 'unowned-receipt-drift-predicted', 'info', {'path': path}, actor='coordinator',
                                   value={'inputs': len(hit)},
                                   expected='receipts refreshed after the inputs they hash change',
                                   observed=f'{len(hit)} recorded input(s) changed on this branch, e.g. {hit[:3]}; '
                                            'the gate will report semantic drift here until the coordinator refreshes it',
                                   fix_hint='Known merge condition: refresh with `npm run gates:refresh` after integration.'))
    return found


def corpus_coupling(ctx) -> list[Condition]:
    added = [p for p in ctx.added_paths() if p.endswith('.bend') and not runner_excluded(p)]
    if not added or not ctx.head.has('tests/compiler-bootstrap/check.py'):
        return []
    return [Condition(ID, 'corpus-glob-coupling', 'info', {'path': 'tests/compiler-bootstrap/receipts/progress.json'},
                      actor='coordinator', value={'added_bend': len(added)},
                      expected='new .bend files are known inputs of the bootstrap corpus',
                      observed=f'{len(added)} added .bend file(s) enter the bootstrap corpus (its files count and histogram drift)',
                      evidence={'examples': added[:5]},
                      fix_hint='Known merge condition; C1 checks each added file against the seed (a seed-valid file Knot calls '
                               'Invalid becomes baselined D4 debt).')]


def volatility(ctx, changed) -> list[Condition]:
    found = []
    registered = {o for g in gates_lib.parse_gates(ctx.head.text(gates_lib.RUN_PY)) for o in g.outputs}
    added_hashes: dict[str, list[str]] = {}
    preflight = []
    for change in changed:
        own = is_own(ctx, change.path, change.status)
        if change.path.endswith('.json'):
            value = R.parse_json(R.read_text(ctx.head, change.path) or '')
            if value is not None:
                keys = sorted({k for _p, k in _keys(value) if MEASUREMENT_KEY.search(k)})
                if keys and change.status == 'A':
                    found.append(Condition(ID, 'receipt-volatility', 'minor', {'path': change.path, 'kind': 'measurement'},
                                           actor='executor' if own else 'coordinator',
                                           expected='a receipt stores observations, not host measurements',
                                           observed=f'measurement field(s) {keys[:4]} change from run to run',
                                           fix_hint='Keep measurements in the run summary; normalize.py only zeroes elapsed_seconds.'))
                docs = sorted({R.repo_path(p) for _ptr, p, _s in R.hash_claims(value) if DOC_INPUTS.search(R.repo_path(p))})
                if docs:
                    found.append(Condition(ID, 'receipt-volatility', 'minor', {'path': change.path, 'kind': 'doc-input'},
                                           actor='executor' if own else 'coordinator',
                                           expected='input hashes cover executed sources, not READMEs or reports',
                                           observed=f'doc input(s) {docs[:3]} make the receipt drift on every doc edit',
                                           fix_hint='Drop documentation from the gate\'s hashed inputs.'))
        if change.status == 'A' and change.path.split('/')[-1].startswith('preflight-'):
            preflight.append(change.path)
        if change.status == 'A' and ('/receipts/' in change.path or change.path.startswith('receipts/')):
            sha = ctx.head.sha(change.path)
            if sha:
                added_hashes.setdefault(sha, []).append(change.path)
            if not any(globs.match(pattern, change.path) for pattern in registered):
                cited = any(change.path in (ctx.head.text(p) or '') for p in ctx.head.files()
                            if p.endswith(('.md', '.py', '.json', '.mjs')) and p != change.path)
                if not cited:
                    found.append(Condition(ID, 'receipt-orphan', 'minor', {'path': change.path},
                                           actor='executor' if own else 'coordinator',
                                           expected='a receipt is a registered gate output or cited in a document',
                                           observed='neither a registered gate output nor referenced anywhere',
                                           fix_hint='Register the producing gate, cite it, or remove the file.'))
    for sha, paths in added_hashes.items():
        if len(paths) > 1:
            found.append(Condition(ID, 'receipt-duplicate', 'minor', {'path': sorted(paths)[0], 'copies': sorted(paths)[1:]},
                                   expected='byte-identical receipts are kept once', observed=f'{len(paths)} identical copies: {sorted(paths)[:4]}'))
    if len(preflight) > 3:
        found.append(Condition(ID, 'receipt-flood', 'minor', {'kind': 'preflight'}, value={'count': len(preflight)},
                               expected='at most 3 preflight-* receipts per increment',
                               observed=f'{len(preflight)} preflight receipts added', evidence={'examples': sorted(preflight)[:5]}))
    return found


def _keys(value, at=''):
    if isinstance(value, dict):
        for key, child in value.items():
            yield at, str(key)
            yield from _keys(child, at + '/' + str(key))
    elif isinstance(value, list):
        for i, child in enumerate(value[:200]):
            yield from _keys(child, f'{at}/{i}')


REWRITE_MARKS = ('.toolchain/', '.bend/lib/', '$ROOT', '$BEND_LIB')


def fast_normalizer(normalize):
    """The gate's own Normalizer, with `text` skipped for a string that none of its rewrites can touch.

    Every rewrite in `Normalizer.text` needs one of the alias keys or one of REWRITE_MARKS to occur in the string, so
    a string with none of them comes back unchanged; the answer is identical, and a large inventory has over a million
    strings (10 s of regular expressions on a 581-file increment).
    """
    class Fast(normalize.Normalizer):
        def text(self, value, aliases):
            if any(key in value for key in aliases) or any(mark in value for mark in REWRITE_MARKS):
                return super().text(value, aliases)
            return value
    return Fast(Path('/nonexistent-prechecks-root'))


def date_only(ctx, receipts_touched) -> tuple[list[Condition], str]:
    normalize = gates_lib.load_module('normalize')
    if normalize is None:
        return [], 'scripts/gates/normalize.py unavailable'
    normalizer = fast_normalizer(normalize)
    memo: dict = {}

    def normalized(path, data):
        key = (path, hashlib.sha1(data).digest())
        if key not in memo:
            memo[key] = normalizer.receipt(path, data, {})
        return memo[key]

    found = []
    for commit in ctx.commits():
        if commit.is_merge:
            continue
        for change in ctx.repo.commit_files(commit.sha):
            if change.status != 'M' or not R.is_receipt(change.path) or not change.path.endswith('.json'):
                continue
            old = ctx.repo.blob(f'{commit.sha}^:{change.path}')
            new = ctx.repo.blob(f'{commit.sha}:{change.path}')
            if old is None or new is None:
                continue
            try:
                a, b = normalized(change.path, old), normalized(change.path, new)
            except ValueError:
                continue
            if normalize.classify(old, new, a, b) == 'volatile-only':
                found.append(Condition(ID, 'receipt-date-only', 'minor', {'commit': commit.sha, 'path': change.path},
                                       actor='coordinator', expected='a receipt commit changes an observation, not just a date',
                                       observed=f'{commit.sha[:8]} rewrites {change.path} with no normalized change',
                                       fix_hint='History is immutable; the ledger records it once.'))
    return found, ''


def gate_run(ctx) -> tuple[list[Condition], str]:
    """R4: read the implementer's newest gate run whose snapshot equals this head."""
    summary, path, reason = gaterun.find(ctx)
    if summary is None and ctx.tier == 'slow' and not ctx.options.get('no_gate_run') and _is_working_copy(ctx):
        # The slow tier runs the registered gates itself (ten minutes or more) on the working copy it is judging.
        ctx.run([sys.executable, '-B', 'scripts/gates/run.py'], cwd=ctx.root, timeout=2400)
        summary, path, reason = gaterun.find(ctx)
    if summary is None:
        return [], reason
    return _read_summary(ctx, summary, path), ''


def _is_working_copy(ctx) -> bool:
    """True when the judged tree is what a gate run in this checkout would export (not a historical --head)."""
    return (ctx.root / 'scripts/gates/run.py').is_file() and (ctx.worktree or (
        ctx.head_commit is not None and ctx.head_commit == ctx.repo.rev_parse('HEAD') and not ctx.dirty))


def _read_summary(ctx, summary: dict, path: str) -> list[Condition]:
    found = []
    normalized = summary.get('normalized', {})
    for gate in normalized.get('gates', []):
        if gate.get('status') != 'passed':
            found.append(Condition(ID, 'gate-red', 'major', {'gate': gate.get('name')},
                                   expected='every registered gate passes on the head snapshot',
                                   observed=f"gate {gate.get('name')} is {gate.get('status')} in the matching run",
                                   evidence={'summary': str(Path(path).relative_to(ctx.root))},
                                   fix_hint='Read the gate log named in the summary.'))
    receipts = list(ctx.manifest.get('receipts', []) or [])
    for row in normalized.get('receipts', []):
        if row.get('classification') != 'semantic':
            continue
        target = row['path']
        own = ctx.manifest.is_owned(target) or target in receipts
        found.append(Condition(ID, 'own-receipt-stale' if own else 'unowned-receipt-drift', 'minor' if own else 'major',
                               {'path': target}, actor='executor' if own else 'coordinator',
                               value={'changed_fields': row.get('changed_fields', [])[:6]},
                               expected='regenerated receipts equal the committed ones up to normalization',
                               observed=f"{'own' if own else 'unowned'} receipt is semantically different after the gate run",
                               fix_hint='Refresh an owned receipt; an unowned one is the coordinator\'s known merge condition.'))
    return found


def run(ctx) -> CheckResult:
    result = CheckResult()
    if ctx.base is None:
        return not_applicable('no base to compare against')
    changed = [c for c in ctx.changes() if c.status in 'AMRC' and R.is_receipt(c.path)]
    result.facts = {'receipts_in_scope': len(changed)}
    if changed:
        result.conditions += host_paths(ctx, changed)
        result.rules_run.append('host-path')
        result.conditions += stale_hashes(ctx, changed)
        result.rules_run.append('stale-receipt-hash')
        result.conditions += decorative_hashes(ctx, changed)
        result.conditions += volatility(ctx, changed)
        result.rules_run += ['decorative-hash', 'receipt-volatility']
    result.conditions += predicted_drift(ctx, {c.path for c in changed})
    result.conditions += corpus_coupling(ctx)
    result.rules_run += ['unowned-receipt-drift-predicted', 'corpus-glob-coupling']
    found, reason = date_only(ctx, changed)
    result.conditions += found
    if reason:
        result.rules_unavailable['receipt-date-only'] = reason
    else:
        result.rules_run.append('receipt-date-only')
    if ctx.tier in ('slow', 'all') or ctx.options.get('use_gate_run', True):
        found, reason = gate_run(ctx)
        result.conditions += found
        if reason:
            result.rules_unavailable['gate-run'] = reason
        else:
            result.rules_run.append('gate-run')
    return result


CHECK = Check(ID, 'receipt-integrity', 'a committed receipt against the tree it describes', run, budget=15)
