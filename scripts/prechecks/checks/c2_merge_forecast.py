"""C2 merge-forecast: the branch against main, its declared upstreams and its merge-order siblings.

Merges belong to the coordinator: executors may not merge or rebase. Conditions here therefore go to
`known.txt` and the merge list, except the ones that are the branch's own text (R4, R6).

  R1 conflict                 a trial merge with main conflicts outside the generated-file registry
  R2 sibling-conflict         the same against each merge-order sibling
  R3 base-fix-missing         main commits to the runner, the host or owned paths that the branch lacks
  R4 decision-drift           a decision row changed on main; its superseded literals in the branch's normative docs
  R5 upstream-contract-unconsumed   a control exported by the upstream's green tip that no consumer references
  R6 brittle-upstream-coupling      a length pin, prose regex or literal fuel bound to upstream shape
  R7 oracle-behind            a pinned oracle commit behind its source branch, which has changed src/ since
  R8 census-after-merge       census --check fails on the trial merge (registry inventory excepted: known)
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from lib import diffs, globs
from lib import receipts as R
from lib import retired as retired_lib
from lib.model import CheckResult, Condition
from lib.runner import Check
from lib.tree import Tree

ID = 'C2'
RULES = ('conflict', 'sibling-conflict', 'base-fix-missing', 'decision-drift', 'upstream-contract-unconsumed',
         'brittle-upstream-coupling', 'oracle-behind', 'census-after-merge')
UPSTREAM_RULES = ('upstream-contract-unconsumed', 'brittle-upstream-coupling')
REGISTRY = (
    ('docs/compiler-campaign/inventory/*.json', "take main's copy, then run `node tools/census/census.mjs`"),
    ('scripts/gates/run.py', "keep both sides' Gate(...) rows"),
    ('scripts/gates/test_runner.py', 'keep the union of required gate names'),
    ('docs/compiler-campaign/GATES.md', 'keep both appended sections'),
    ('docs/perch-review-log.md', 'keep both appended sections'),
    ('package.json', 'keep the union of scripts entries'),
    ('**/receipts/**', 'coordinator refresh: `npm run gates:refresh` after integration'),
)
RUNNER_HOST = ('scripts/gates/**', 'scripts/run-wasm*.mjs', 'tests/compiler-io/host/**')
NORMATIVE = ('**/SPEC.md', 'vm/*.md', 'docs/compiler-campaign/*.md', 'tests/**/SPEC.md', 'tests/**/README.md')
DECISION = re.compile(r'(?m)^\|\s*(D\d+)\s*\|(.*)$')


def registry_hint(path: str) -> str | None:
    for pattern, hint in REGISTRY:
        if globs.match(pattern, path):
            return hint
    return None


def trial(ctx, ref: str):
    """(exit, conflicts, tree oid) of a trial merge of head with `ref`; None when nothing to merge."""
    if not ctx.head_commit or not ref:
        return None
    if ctx.repo.is_ancestor(ref, ctx.head_commit) or ctx.repo.is_ancestor(ctx.head_commit, ref):
        return None
    code, conflicts, _messages, oid = ctx.repo.merge_tree(ref, ctx.head_commit)
    return code, conflicts, oid


def conflicts_rules(ctx, result: CheckResult) -> None:
    main_tip = ctx.repo.rev_parse(ctx.main_ref) if ctx.main_ref else None
    if not main_tip:
        result.rules_unavailable['conflict'] = 'no main ref'
        return
    behind = ctx.repo.rev_count(f'{ctx.head_commit}..{main_tip}') if ctx.head_commit else 0
    result.facts['behind_main'] = behind
    result.facts['ahead_of_base'] = len(ctx.commits())
    outcome = trial(ctx, main_tip)
    result.rules_run.append('conflict')
    if outcome is None:
        result.facts['merge_with_main'] = 'up-to-date'
        return
    code, conflicts, oid = outcome
    result.facts['merge_with_main'] = 'clean' if code == 0 else f'{len(conflicts)} conflict(s)'
    for path in conflicts:
        hint = registry_hint(path)
        if hint:
            result.conditions.append(Condition(ID, 'merge-condition', 'info', {'path': path}, actor='coordinator',
                                               expected='generated and appendable files resolve mechanically at merge',
                                               observed=f'{path} conflicts with main: {hint}', fix_hint=hint))
        else:
            result.conditions.append(Condition(ID, 'conflict', 'major', {'path': path}, actor='coordinator',
                                               expected='a trial merge with main is clean outside the generated-file registry',
                                               observed=f'{path} conflicts with main and has no mechanical resolution',
                                               fix_hint='The coordinator resolves it at merge; the executor must not merge or rebase.'))
    result.merge_tree = oid if oid else None
    result.merge_conflicts = conflicts


def siblings(ctx, result: CheckResult) -> None:
    if not ctx.manifest.merge_before:
        if 'merge_before' in ctx.manifest.raw:
            result.na('sibling-conflict', 'the manifest declares no merge-order siblings')
        else:
            result.rules_unavailable['sibling-conflict'] = 'the increment manifest does not declare merge_before, so the siblings are unknown'
        return
    for sibling in ctx.manifest.merge_before:
        ref = sibling if '/' in sibling else f'campaign/{sibling}'
        tip = ctx.repo.rev_parse(ref)
        if not tip:
            result.rules_unavailable['sibling-conflict'] = f'unknown sibling ref {ref}'
            continue
        outcome = trial(ctx, tip)
        result.rules_run.append('sibling-conflict')
        if outcome is None:
            continue
        for path in outcome[1]:
            if registry_hint(path):
                continue
            result.conditions.append(Condition(ID, 'sibling-conflict', 'major', {'path': path, 'sibling': sibling}, actor='coordinator',
                                               expected='the branch merges cleanly after its merge-order siblings',
                                               observed=f'{path} conflicts with {sibling}, which merges first'))


def base_fixes(ctx, result: CheckResult) -> None:
    main_tip = ctx.repo.rev_parse(ctx.main_ref) if ctx.main_ref else None
    if not main_tip or not ctx.head_commit:
        result.rules_unavailable['base-fix-missing'] = 'no main ref or no commit to compare with main'
        return
    watched = list(RUNNER_HOST) + [p for p in ctx.manifest.owns()] + ctx.changed_paths()
    watched = [w for w in watched if not any(c in w for c in '[]{}')][:400]
    if not watched:
        result.na('base-fix-missing', 'no watched path: nothing is changed or owned')
        return
    text = ctx.repo.out('log', '--format=%H%x1f%s', main_tip, f'^{ctx.head_commit}', '--', *watched)
    result.rules_run.append('base-fix-missing')
    for line in text.splitlines():
        sha, _, subject = line.partition('\x1f')
        files = [c.path for c in ctx.repo.commit_files(sha)]
        runner = [f for f in files if globs.match_any(RUNNER_HOST, f)]
        result.conditions.append(Condition(ID, 'base-fix-missing', 'major' if runner else 'minor', {'commit': sha}, actor='coordinator',
                                           value={'files': len(files)},
                                           expected='main commits to the runner, host or owned paths are merged into the branch',
                                           observed=f'main has {sha[:8]} {subject[:70]!r} touching {(runner or files or ['a merged path'])[0]}, which the branch lacks',
                                           fix_hint='Known merge condition: the branch predates this fix.'))


def decision_drift(ctx, result: CheckResult) -> None:
    main_tree = ctx.main_tree
    if main_tree is None or ctx.base is None:
        result.rules_unavailable['decision-drift'] = 'no main tree or no base to compare the decision rows against'
        return
    path = 'docs/COMPILER-CAMPAIGN.md'
    rows = lambda tree: dict(DECISION.findall(tree.text(path) or '')) if tree.has(path) else {}
    now, before = rows(main_tree), rows(ctx.base)
    changed = sorted(k for k in now if before.get(k) != now[k])
    result.rules_run.append('decision-drift')
    if not changed:
        return
    terms = [(t, r) for t, r in retired_lib.load(main_tree) if t.get('id') in changed]
    result.facts['decisions_changed_on_main'] = changed
    for doc in ctx.changed_paths():
        if not globs.match_any(NORMATIVE, doc):
            continue
        patch = ctx.repo.patch(ctx.base.treeish, ctx.head.treeish, [doc], unified=0)
        lines = [line for hunks in diffs.parse(patch).values() for h in hunks for line in h.added]
        for term, regex in terms:
            for line in lines:
                if regex.search(line) and not retired_lib.allowed(term, line):
                    result.conditions.append(Condition(
                        ID, 'decision-drift', 'major' if doc.endswith('SPEC.md') else 'minor',
                        {'path': doc, 'decision': term['id'], 'text': re.sub(r'\W+', ' ', line).strip()[:50].lower()},
                        expected=f"{term['id']} changed on main after this branch's base; the branch's text follows it",
                        observed=f'{doc}: {line.strip()[:100]}', fix_hint='Update the sentence to the current decision.'))


def upstream_contracts(ctx, result: CheckResult) -> None:
    if not ctx.manifest.upstream:
        if 'upstream' in ctx.manifest.raw:
            result.na(UPSTREAM_RULES, 'the increment is not stacked: it declares no upstream increment')
        else:
            for rule in UPSTREAM_RULES:
                result.rules_unavailable[rule] = ('no upstream is declared (neither the increment manifest nor --upstream), so a stacked '
                                                  'increment would be judged as if it stood alone')
        return
    for upstream in ctx.manifest.upstream:
        tip = ctx.repo.rev_parse(upstream.get('tip') or upstream['ref'])
        if not tip or not ctx.head_commit:
            for rule in UPSTREAM_RULES:
                result.rules_unavailable[rule] = f"upstream {upstream['id']} is unavailable"
            continue
        green = green_tip(ctx, upstream, tip)
        shared = ctx.repo.merge_base(ctx.head_commit, green)
        result.facts.setdefault('upstreams', {})[upstream['id']] = {'tip': tip, 'green': green, 'merge_base': shared}
        if not shared:
            for rule in UPSTREAM_RULES:
                result.rules_unavailable[rule] = f"upstream {upstream['id']} shares no history with the branch"
            continue
        old, new = Tree(ctx.repo, ctx.repo.tree_sha(shared)), Tree(ctx.repo, ctx.repo.tree_sha(green))
        merge_now = bool(upstream.get('merge'))
        for item in ctx.manifest.consumes():
            pattern = re.compile(item.get('pattern', r'^def (\w+_controls)\('), re.M)
            file = item['file']
            fresh = set(pattern.findall(new.text(file) or '')) - set(pattern.findall(old.text(file) or ''))
            consumers = item.get('consumers') or [p for p in ctx.head.files() if re.search(r'(?:^|/)check[^/]*\.py$', p) and p != file]
            corpus = '\n'.join(ctx.head.text(p) or '' for p in consumers)
            for name in sorted(fresh):
                if name in (item.get('not_applicable') or []):
                    continue
                if not re.search(rf'(?<![\w]){re.escape(name)}(?![\w])', corpus):
                    result.conditions.append(Condition(
                        ID, 'upstream-contract-unconsumed', 'major', {'upstream': upstream['id'], 'item': name},
                        actor='executor' if merge_now else 'upstream',
                        expected=f"the branch runs every control that {upstream['id']} exports",
                        observed=f"{upstream['id']} {green[:8]} exports {name}() and no consumer references it",
                        fix_hint='Run it in the consumer gate, or list it under not_applicable with a reason.'))
        result.rules_run.append('upstream-contract-unconsumed')
        spec = 'vm/SPEC.md'
        if new.has(spec):
            must = lambda tree: {line.strip() for line in (tree.text(spec) or '').split('\n') if 'MUST' in line}
            added = sorted(must(new) - must(old))
            if added:
                result.facts.setdefault('merge_obligations', {})[upstream['id']] = [m[:120] for m in added[:20]]
        brittle_coupling(ctx, result, upstream)
        result.rules_run.append('brittle-upstream-coupling')


def green_tip(ctx, upstream: dict, tip: str) -> str:
    """Newest first-parent commit whose committed gate receipt says passed with input hashes that match its files."""
    receipt = upstream.get('receipt')
    if upstream.get('tip') or not receipt:
        return tip
    for commit in ctx.repo.rev_list('--first-parent', '-n', '40', tip):
        tree = Tree(ctx.repo, ctx.repo.tree_sha(commit))
        try:
            value = tree.json(receipt)
        except ValueError:
            continue
        if not isinstance(value, dict) or value.get('status') not in ('pass', 'passed'):
            continue
        if all(tree.sha256(R.repo_path(p)) in (None, sha) for _ptr, p, sha in R.hash_claims(value)):
            return commit
    return tip


def brittle_coupling(ctx, result: CheckResult, upstream: dict) -> None:
    alias = re.escape(str(upstream.get('alias', 'spec')))
    length_pin = re.compile(rf'\blen\(\s*(?:{alias}\w*[.\w]*|\w*controls\w*)\s*(?:\([^)]*\))?\s*\)\s*==\s*\d+')
    prose = re.compile(rf'\bre\.(?:search|findall|match|finditer)\(.*{alias}\w*(?:_text|\.read_text)|{alias}\w*\.read_text\(\).*re\.')
    for change in ctx.changes():
        if change.status not in 'AMR' or not re.search(r'(?:^|/)check[^/]*\.py$', change.path):
            continue
        patch = ctx.repo.patch(ctx.base.treeish, ctx.head.treeish, [change.path], unified=0)
        added = [line for hunks in diffs.parse(patch).values() for h in hunks for line in h.added]
        body = ctx.head.text(change.path) or ''
        for line in added:
            for pattern, kind in ((length_pin, 'length-pin'), (prose, 'prose-regex')):
                if pattern.search(line):
                    result.conditions.append(Condition(ID, 'brittle-upstream-coupling', 'minor',
                                                       {'path': change.path, 'kind': kind, 'text': re.sub(r'\s+', ' ', line.strip())[:50]},
                                                       expected='a downstream check does not hard-wire upstream shape',
                                                       observed=f'{kind}: {line.strip()[:100]}',
                                                       fix_hint='Iterate what the upstream exports instead of pinning its size or prose.'))
            if 'run_controls' in body and re.search(r"fuel\w*\s*[=:]\s*['\"]?\d{5,}", line):
                result.conditions.append(Condition(ID, 'brittle-upstream-coupling', 'minor',
                                                   {'path': change.path, 'kind': 'literal-fuel', 'text': re.sub(r'\s+', ' ', line.strip())[:50]},
                                                   expected="controls run at the fuel their own rows carry",
                                                   observed=f'literal fuel bound: {line.strip()[:100]}'))


def oracles(ctx, result: CheckResult) -> None:
    manifest = next((p for p in ctx.head.files() if p.endswith('oracles/manifest.json')), None)
    if not manifest:
        result.na('oracle-behind', 'the tree has no oracles/manifest.json')
        return
    try:
        value = ctx.head.json(manifest)
    except ValueError:
        result.rules_unavailable['oracle-behind'] = f'{manifest} is not valid JSON'
        return
    result.rules_run.append('oracle-behind')
    entries = value.get('pins', value) if isinstance(value, dict) else {}
    for name, entry in (entries.items() if isinstance(entries, dict) else []):
        if not isinstance(entry, dict):
            continue
        pin = entry.get('commit') or entry.get('pin')
        branch = entry.get('branch') or entry.get('source')
        if not (isinstance(pin, str) and isinstance(branch, str) and ctx.repo.rev_parse(pin) and ctx.repo.rev_parse(branch)):
            continue
        tip = ctx.repo.rev_parse(branch)
        if tip == ctx.repo.rev_parse(pin) or not ctx.repo.is_ancestor(pin, tip):
            continue
        moved = ctx.repo.out('diff', '--name-only', pin, tip, '--', 'src/')
        if moved:
            result.conditions.append(Condition(ID, 'oracle-behind', 'minor', {'path': manifest, 'oracle': name}, actor='coordinator',
                                               expected='a pinned oracle commit is the source branch tip, or src/ has not moved',
                                               observed=f'oracle {name} pins {pin[:8]}; {branch} moved src/ since ({len(moved.splitlines())} file(s))'))


def census_after_merge(ctx, result: CheckResult) -> None:
    oid = getattr(result, 'merge_tree', None)
    if not ctx.main_tree:
        result.rules_unavailable['census-after-merge'] = 'no main tree to merge with'
        return
    if not oid:
        result.na('census-after-merge', 'there is no trial merge: main and the branch lie in one line of history, or the merge produced no tree')
        return
    if ctx.identity or not any(p.startswith(('src/', 'tools/census/', 'docs/compiler-campaign/inventory/', 'scripts/gates/'))
                               for p in ctx.changed_paths() + ctx.deleted_paths()):
        result.na('census-after-merge', 'the diff touches none of src/, tools/census/, the inventory or scripts/gates/')
        return
    try:
        merged = Tree(ctx.repo, oid, label='merge')
        export = ctx.export(merged)
    except Exception as error:                              # noqa: BLE001 - a trial merge tree may be unexportable
        result.rules_unavailable['census-after-merge'] = f'cannot export the trial merge: {error}'
        return
    if not (export / 'tools/census/census.mjs').exists():
        result.na('census-after-merge', 'the merged tree has no tools/census')
        return
    conflicted = set(getattr(result, 'merge_conflicts', []))
    if conflicted - {p for p in conflicted if registry_hint(p)}:
        result.rules_unavailable['census-after-merge'] = 'the trial merge has conflicts outside the registry'
        return
    for path in conflicted:                                 # mechanical resolution: main's copy, then the census decides
        if globs.match('docs/compiler-campaign/inventory/*.json', path) and ctx.main_tree.has(path):
            (export / path).write_bytes(ctx.main_tree.read(path))
    code, out, err = ctx.run(['node', 'tools/census/census.mjs', '--check'], cwd=export, timeout=60)
    result.rules_run.append('census-after-merge')
    if code is None:
        result.rules_unavailable['census-after-merge'] = 'census --check timed out or node is missing'
        return
    text = (err or out).decode('utf-8', 'replace')
    if code != 0:
        if 'Stale inventory' in text:
            result.conditions.append(Condition(ID, 'merge-condition', 'info', {'path': 'docs/compiler-campaign/inventory'}, actor='coordinator',
                                               expected='the inventory is regenerated after the merge',
                                               observed='census --check reports a stale inventory on the trial merge',
                                               fix_hint='Run `node tools/census/census.mjs` after merging and commit the inventory.'))
        else:
            result.conditions.append(Condition(ID, 'census-after-merge', 'minor', {'command': 'census --check'}, actor='coordinator',
                                               expected='census --check passes on the trial merge',
                                               observed=next((l for l in text.splitlines() if l.strip() and not l.startswith('unrecognized-suite')), 'failed')[:160]))


def run(ctx) -> CheckResult:
    result = CheckResult()
    if ctx.head_commit is None or ctx.main_ref is None:
        return CheckResult(outcome='not-applicable', reason='no main ref or no commit to merge')
    conflicts_rules(ctx, result)
    siblings(ctx, result)
    base_fixes(ctx, result)
    decision_drift(ctx, result)
    upstream_contracts(ctx, result)
    oracles(ctx, result)
    if ctx.tier in ('slow', 'all') or ctx.options.get('census_after_merge', True):
        census_after_merge(ctx, result)
    else:
        result.rules_unavailable['census-after-merge'] = 'not requested: the census_after_merge option is off'
    if ctx.dirty:
        result.notes.append('uncommitted changes are not part of the trial merge')
    return result


CHECK = Check(ID, 'merge-forecast', 'the branch against main, its upstreams and its siblings', run, budget=20, rules=RULES)
