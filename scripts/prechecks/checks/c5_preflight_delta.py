"""C5 preflight-delta: the offline Perch style preflight at base and at head.

`node scripts/perch-style.mjs --preflight --json` is offline (zero provider requests) and never loads a
dotenv file. The suite runs it on exports, at head and at the base on the targets as they existed there,
and reports only what the branch changed; absolute counts are not findings (25 to 137 blockers already
exist at every base).

  R1 preflight-new-blocker    a unit newly truncated at head
  R2 composition-budget       a group's composition crossed the 48,000-byte cap, or headroom fell under 2%; a changed file in
                              no group that composes over the cap alone (a file in a group is judged by its group)
  R3 unit-cap                 the full manifest run exceeds the style unit cap
  R4 manifest-membership      a new .bend outside every manifest group, or a group lost a file
  R5 task-provenance          a --task file that did not exist at base, or is over the size cap
  R6 bend-hygiene             a non-ASCII byte or a divider comment in an added .bend line
  R7 facts                    the preflight numbers, for C6 and the reviewers
  R8 perch-identity-change    a parser profile, rubric or judge sentence changed without a review-log entry
"""
from __future__ import annotations

import hashlib
import json
import re

from lib import diffs, globs
from lib.model import CheckResult, Condition
from lib.runner import Check

ID = 'C5'
COMPOSITION_CAP = 48000
TASK_CAP = 16000
MANIFESTS = ('docs/compiler-campaign/manifest.json', 'vm/perch-manifest.json')
EXCLUDED_TARGETS = ('tests/**/fixtures/**', 'tests/**/generated/**', 'research/**/generated/**', 'packages/**')
OFFLINE = {'TREE_SITTER_LANGUAGE_PACK_MANIFEST_URL': 'offline://disabled'}


def _key(*parts) -> str:
    return hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:16]


def preflight(ctx, tree, args: list[str], label: str, timeout: float = 120):
    """(report dict | None, error text). Cached by tree and arguments; runs on an export, never the checkout."""
    cache = ctx.scratch / 'cache'
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f'preflight-{tree.treeish}-{_key(*args)}.json'
    if path.is_file():
        stored = json.loads(path.read_text())
        return stored.get('report'), stored.get('error', '')
    export = ctx.export(tree)
    code, out, err = ctx.run(['node', 'scripts/perch-style.mjs', '--preflight', '--json', *args], cwd=export,
                             timeout=timeout, env=OFFLINE)
    report, error = None, ''
    if code is None:
        error = f'{label}: preflight timed out or node is missing'
    else:
        try:
            report = json.loads(out.decode('utf-8', 'replace'))
        except ValueError:
            error = (err or out).decode('utf-8', 'replace').strip().splitlines()[-1][:200] if (err or out) else f'exit {code}'
    if code is not None:                                   # a timeout is not a fact worth caching
        path.write_text(json.dumps({'report': report, 'error': error}))
    return report, error


def truncated_units(report: dict | None) -> dict:
    result = {}
    for unit in (report or {}).get('units') or []:
        if unit.get('truncated') or unit.get('limit_reasons'):
            result[(unit['target'], tuple(sorted(unit.get('limit_reasons') or [])))] = unit
    return result


def group_table(report: dict | None) -> dict:
    table = {}
    for group in (report or {}).get('groups') or []:
        composition = group.get('composition') or {}
        table[group['name']] = {'files': group.get('files') or [], 'bytes': composition.get('source_bytes'),
                                'limit': composition.get('byte_limit') or COMPOSITION_CAP,
                                'available': composition.get('available'), 'reasons': composition.get('reasons') or [],
                                'units': (group.get('summary') or {}).get('units'),
                                'truncated': (group.get('summary') or {}).get('truncated_units')}
    return table


def changed_targets(ctx) -> list[str]:
    return [p for p in ctx.changed_paths(statuses='AMRC') if p.endswith('.bend') and not globs.match_any(EXCLUDED_TARGETS, p)]


def grouped_files(ctx) -> set[str]:
    """Every file that a manifest group lists (files or selected_files): those are reviewed, and budgeted, as their group."""
    for path in MANIFESTS:
        if ctx.head.has(path):
            try:
                data = ctx.head.json(path) or {}
            except ValueError:
                return set()
            return {f for g in data.get('groups', []) for f in (g.get('files') or []) + (g.get('selected_files') or [])}
    return set()


def tolerant_preflight(ctx, tree, targets: list[str], label: str, timeout: float = 120):
    """(report, error, dropped). A target that does not parse under the Perch parser aborts the whole batch
    ("Bend target does not parse: <path>"); such a target is dropped and the rest are preflighted again, so one intentionally
    malformed fixture does not blind the check to every other changed file. `dropped` lists what was not preflighted."""
    dropped: list[str] = []
    targets = list(targets)
    for _ in range(12):
        report, error = preflight(ctx, tree, targets, label, timeout)
        match = re.search(r'Bend target does not parse: (\S+)', error or '')
        if report is not None or not match or match.group(1) not in targets:
            return report, error, dropped
        dropped.append(match.group(1))
        targets = [t for t in targets if t != match.group(1)]
        if not targets:
            return None, error, dropped
    return None, error, dropped


def sole_member_budgets(ctx, targets: list[str], old_targets: list[str]) -> list[Condition]:
    """A changed file that is in no manifest group and exceeds the cap on its own (each file preflighted alone).

    A file that a group lists is reviewed as part of its group, and the group composition check (ratcheted against the
    base) judges it; measuring it alone would charge it for helper files that no split of the file can remove.
    """
    from concurrent.futures import ThreadPoolExecutor
    grouped = grouped_files(ctx)
    targets = [t for t in targets if t not in grouped]
    if len(targets) > 24:
        targets = targets[:24]

    def one(tree, path, label):
        report, _error = preflight(ctx, tree, [path], label)
        composition = (report or {}).get('composition') or {}
        return path, composition.get('source_bytes'), composition.get('byte_limit') or COMPOSITION_CAP, composition.get('context_files')

    with ThreadPoolExecutor(max_workers=max(ctx.jobs, 1)) as pool:
        heads = list(pool.map(lambda p: one(ctx.head, p, 'head'), targets))
        bases = {p: b for p, b, _l, _c in pool.map(lambda p: one(ctx.base, p, 'base'), [t for t in targets if t in old_targets])}
    found = []
    for path, size, limit, context in heads:
        if size is None or size <= limit:
            continue
        if (bases.get(path) or 0) > limit:
            continue                                      # already over the cap at base
        own = len(ctx.head.read(path) or b'')
        found.append(Condition(ID, 'composition-budget', 'major', {'target': path}, value={'bytes': size},
                               expected=f'a file outside every manifest group composes within {limit} bytes',
                               observed=f'{path} is in no manifest group and composes {size} bytes (cap {limit}): '
                                        f'{own} bytes of its own and {context if context is not None else "?"} helper file(s)',
                               fix_hint='Add it to a group of the manifest, which judges its composition as a group, or '
                                        'shrink the helper closure it reaches (splitting the file alone rarely helps).'))
    return found


# ---- R6, R8 need no preflight run ------------------------------------------
def hygiene(ctx) -> list[Condition]:
    found = []
    for path in ctx.changed_paths(statuses='AMRC'):
        if not path.endswith('.bend') or path.startswith('tests/') and '/fixtures/' in path:
            continue
        patch = ctx.repo.patch(ctx.base.treeish, ctx.head.treeish, [path], unified=0)
        added = [line for hunks in diffs.parse(patch).values() for h in hunks for line in h.added]
        non_ascii = [line for line in added if any(ord(c) > 127 for c in line)]
        dividers = [line for line in added if re.match(r'\s*#\s*-{4,}', line)]
        if non_ascii:
            found.append(Condition(ID, 'bend-hygiene', 'minor', {'path': path, 'kind': 'non-ascii'}, value={'lines': len(non_ascii)},
                                   expected='Bend sources are ASCII (the seed rejects non-ASCII bytes in some positions)',
                                   observed=f'{len(non_ascii)} added line(s) with a non-ASCII byte, e.g. {non_ascii[0].strip()[:60]!r}',
                                   fix_hint='Use an ASCII spelling or an escape.'))
        if dividers:
            found.append(Condition(ID, 'bend-hygiene', 'minor', {'path': path, 'kind': 'divider'}, value={'lines': len(dividers)},
                                   expected='house style has no divider comments',
                                   observed=f'{len(dividers)} added divider comment(s), e.g. {dividers[0].strip()[:40]!r}'))
    return found


def sentences(text: str) -> set[str]:
    strings = re.findall(r"`([^`]{80,})`|'([^'\n]{80,})'|\"([^\"\n]{80,})\"", text)
    out = set()
    for group in strings:
        body = next(g for g in group if g)
        for piece in re.split(r'(?<=[.!?])\s+', re.sub(r'\s+', ' ', body)):
            if len(piece) >= 40 and ' ' in piece:
                out.add(piece.strip())
    return out


def identity(ctx) -> list[Condition]:
    def constants(tree):
        style = tree.text('scripts/perch-style.mjs') or ''
        bend = tree.text('scripts/perch-bend.mjs') or ''
        profile = re.search(r"BEND_PARSER_PROFILE\s*=\s*(['\"`])([^'\"`]+)\1", bend)
        return {'parser_profile': profile.group(2) if profile else None,
                'rubric_sha256': tree.sha256('perch-style.json'),
                'sentences': sentences(style) | sentences(tree.text('perch-style.json') or '')}
    before, after = constants(ctx.base), constants(ctx.head)
    changed = [k for k in ('parser_profile', 'rubric_sha256') if before[k] != after[k] and before[k] is not None]
    lost = sorted(before['sentences'] - after['sentences'])
    if not changed and not lost:
        return []
    log = 'docs/perch-review-log.md'
    patch = ctx.repo.patch(ctx.base.treeish, ctx.head.treeish, [log], unified=0)
    logged = any(h.added for hunks in diffs.parse(patch).values() for h in hunks)
    found = []
    if changed and not logged:
        found.append(Condition(ID, 'perch-identity-change', 'minor', {'kind': 'identity', 'constants': changed},
                               expected='a change to a cache or reuse identity is recorded in docs/perch-review-log.md',
                               observed=f'{changed} changed, and the review log gained no entry',
                               fix_hint='State that it invalidates .perch/cache/style-v1, --reuse receipts and campaign baselines.'))
    if lost and not logged:
        found.append(Condition(ID, 'perch-identity-change', 'major', {'kind': 'judge-sentence', 'sentence': _key(lost[0])},
                               value={'lost': len(lost)},
                               expected='every sentence of the base judge-facing instruction survives, or the change is declared',
                               observed=f'{len(lost)} sentence(s) of the judge-facing text disappeared, e.g. {lost[0][:110]!r}',
                               fix_hint='Restore it, or log the intended prompt change in docs/perch-review-log.md.'))
    return found


# ---- R5 ---------------------------------------------------------------------
def task_provenance(ctx) -> list[Condition]:
    found = []
    texts = {}
    for path in ctx.changed_paths(statuses='AMRC'):
        if path.endswith('.md'):
            patch = ctx.repo.patch(ctx.base.treeish, ctx.head.treeish, [path], unified=0)
            texts[path] = '\n'.join(line for hunks in diffs.parse(patch).values() for h in hunks for line in h.added)
    handoff = ctx.root / '.local' / (ctx.inc or '-') / 'HANDOFF.md'
    if ctx.inc and handoff.is_file():
        texts[f'.local/{ctx.inc}/HANDOFF.md'] = handoff.read_text(errors='replace')
    for source, text in texts.items():
        for task in sorted(set(re.findall(r'--task[= ]`?([\w./-]+\.md)', text))):
            in_head, in_base = ctx.head.has(task), ctx.base.has(task)
            size = len((ctx.head.read(task) or b''))
            if not in_head:
                continue
            if not in_base and task in ctx.changed_paths():
                found.append(Condition(ID, 'task-provenance', 'minor', {'path': source, 'task': task},
                                       expected='a --task file exists at base (the increment\'s own report is not a task)',
                                       observed=f'{source} names --task {task}, which this branch added'))
            if size > TASK_CAP:
                found.append(Condition(ID, 'task-provenance', 'minor', {'path': source, 'task': task, 'kind': 'size'},
                                       value={'bytes': size}, expected=f'a task file is at most {TASK_CAP} bytes',
                                       observed=f'{task} is {size} bytes; the judge would see task_byte_limit'))
    return found


def run(ctx) -> CheckResult:
    result = CheckResult()
    if ctx.base is None:
        return CheckResult(outcome='not-applicable', reason='no base to compare against')
    result.conditions += hygiene(ctx)
    result.conditions += identity(ctx)
    result.conditions += task_provenance(ctx)
    result.rules_run += ['bend-hygiene', 'perch-identity-change', 'task-provenance']
    targets = changed_targets(ctx)
    facts = {'changed_targets': len(targets)}
    result.facts = {'preflight': facts}
    if not targets:
        result.notes.append('0 changed .bend targets: no declaration or composition review changed')
        return result
    if not ctx.head.has('scripts/perch-style.mjs'):
        result.rules_unavailable['preflight'] = 'no scripts/perch-style.mjs in this tree'
        return result
    old_targets = [p for p in targets if ctx.base.has(p)]
    head_report, head_error, unparsed = tolerant_preflight(ctx, ctx.head, targets, 'head')
    base_report, base_error, _base_unparsed = (tolerant_preflight(ctx, ctx.base, old_targets, 'base') if old_targets else (None, '', []))
    if unparsed:
        facts['unparsed_targets'] = unparsed
        result.rules_unavailable['preflight-targets'] = (f'{len(unparsed)} changed .bend target(s) do not parse under the Perch parser and were '
                                                         f'not preflighted: {", ".join(unparsed[:3])}' + (' ...' if len(unparsed) > 3 else ''))
    if head_report is None:
        result.rules_unavailable['preflight-new-blocker'] = head_error or 'preflight produced no report'
    else:
        result.rules_run.append('preflight-new-blocker')
        head_units, base_units = truncated_units(head_report), truncated_units(base_report)
        facts.update(units=head_report['summary']['units'], files=head_report['summary']['files'],
                     truncated=head_report['summary']['truncated_units'], blockers=head_report['structural_blockers'])
        if base_report is None and old_targets:
            result.rules_unavailable['preflight-new-blocker'] = base_error or 'the base preflight failed; new blockers cannot be told apart'
        else:
            parser_moved = base_report is not None and base_report.get('parser') != head_report.get('parser')
            for (target, reasons), unit in sorted(head_units.items()):
                if (target, reasons) in base_units:
                    continue
                if parser_moved:
                    continue
                result.conditions.append(Condition(
                    ID, 'preflight-new-blocker', 'minor', {'target': target, 'reasons': list(reasons)},
                    expected='a changed declaration fits its review context',
                    observed=f'{target} is newly truncated ({", ".join(reasons) or "truncated"}); a truncated unit cannot pass style review',
                    fix_hint='Shrink the declaration or its helper closure, or record the unit in the ledger if permanent.'))
            if parser_moved:
                result.notes.append('parser profile differs between base and head: truncation deltas reported once as info')
        for condition in sole_member_budgets(ctx, targets, old_targets):
            result.conditions.append(condition)
        result.rules_run.append('composition-budget')
    manifest_path = next((m for m in MANIFESTS if ctx.head.has(m)), None)
    if manifest_path:
        head_m, head_error = preflight(ctx, ctx.head, [f'--manifest={manifest_path}'], 'head manifest', timeout=240)
        base_m, base_error = (preflight(ctx, ctx.base, [f'--manifest={manifest_path}'], 'base manifest', timeout=240)
                              if ctx.base.has(manifest_path) else (None, ''))
        if head_m is None:
            cap = re.search(r'limited to (\d+) units', head_error or '')
            if cap:
                result.conditions.append(Condition(ID, 'unit-cap', 'major', {'manifest': manifest_path},
                                                   value={'max_units': int(cap.group(1))},
                                                   expected=f'the whole manifest fits the {cap.group(1)}-unit style cap',
                                                   observed=head_error, fix_hint='Narrow the groups or raise max_units (coordinator).'))
                result.rules_run.append('unit-cap')
            else:
                result.conditions.append(Condition(ID, 'preflight-new-blocker', 'major', {'target': manifest_path, 'reasons': ['run-aborted']},
                                                   expected='the full-manifest preflight completes',
                                                   observed=f'the full-manifest run aborted: {head_error}'))
        else:
            result.rules_run += ['composition-budget', 'manifest-membership']
            head_groups, base_groups = group_table(head_m), group_table(base_m)
            facts['groups'] = {n: {'bytes': g['bytes'], 'available': g['available']} for n, g in head_groups.items()}
            facts['manifest_units'] = head_m['summary']['units']
            facts['manifest_blockers'] = head_m['structural_blockers']
            for name, group in sorted(head_groups.items()):
                old = base_groups.get(name)
                room = (group['limit'] - group['bytes']) / group['limit'] if group['bytes'] is not None else 1
                old_room = ((old['limit'] - old['bytes']) / old['limit']) if old and old['bytes'] is not None else 1
                if group['available'] is False and 'composition_byte_limit' in group['reasons'] and (old is None or old['available'] is not False):
                    result.conditions.append(Condition(ID, 'composition-budget', 'major', {'group': name}, value={'bytes': group['bytes']},
                                                       expected=f'group {name} composes within its byte limit',
                                                       observed=f"group {name} lost its composition: {group['bytes']} > {group['limit']} bytes",
                                                       fix_hint='Split the group along a real seam, or move a file.'))
                elif room < 0.02 and old_room >= 0.02 or (room < 0.02 and old is None):
                    result.conditions.append(Condition(ID, 'composition-budget', 'minor', {'group': name}, value={'bytes': group['bytes']},
                                                       expected='a group keeps at least 2% composition headroom',
                                                       observed=f"group {name} is at {group['bytes']} of {group['limit']} bytes ({room:.1%} left)"))
            manifest = ctx.head.json(manifest_path) or {}
            grouped = {f for g in manifest.get('groups', []) for f in (g.get('files') or []) + (g.get('selected_files') or [])}
            for path in ctx.added_paths():
                if path.startswith('src/') and path.endswith('.bend') and path not in grouped:
                    result.conditions.append(Condition(ID, 'manifest-membership', 'minor', {'path': path},
                                                       expected='a new source file belongs to a manifest group',
                                                       observed=f'{path} is outside every group of {manifest_path}',
                                                       fix_hint='Add it to a group (or a new one) so its declarations and composition are reviewed.'))
            if base_m is not None:
                for name, group in base_groups.items():
                    now = head_groups.get(name)
                    if now is not None:
                        dropped = sorted(set(group['files']) - set(now['files']))
                        if dropped:
                            result.conditions.append(Condition(ID, 'manifest-membership', 'minor', {'group': name, 'dropped': dropped[:3]},
                                                               expected='a group does not shrink without a stated reason',
                                                               observed=f'group {name} lost {dropped[:3]}'))
    ctx.publish('preflight', facts)
    return result


CHECK = Check(ID, 'preflight-delta', 'the offline style preflight at base and at head', run, budget=30)
