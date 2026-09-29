"""C6 claims-vs-facts: prose, reports and names against measured facts.

The facts table (`facts.json`) is measured from the tree; claims come from the changed paragraphs of the
increment's docs, its handoff report and its commit messages. Only added lines are judged, so a stale
sentence that predates the branch is never re-reported.

  R1 stale-count            a number paired with a counted noun disagrees with its fact
  R2 retired-term           a superseded literal outside its allowed context
  R3 missing-path / untracked-evidence
  R4 report-missing / report-stale / report-gates
  R5 hardcoded-count        a gate script writes a literal where it should measure
  R6 count-extraction-shape a generic receipt key the runner would mis-count
  R7 ground-law-general-name
  R9 vestige                a new def that only laws and proofs reach
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from lib import diffs, facts as facts_lib, gates as gates_lib, globs
from lib import retired as retired_lib
from lib import receipts as R
from lib import textutil as T
from lib.model import CheckResult, Condition
from lib.runner import Check

ID = 'C6'
NOUNS = {r'mutants?': 'mutants', r'fixtures?': 'fixtures', r'controls?': 'controls', r'boundar(?:y|ies)': 'boundaries',
         r'budget probes?': 'budgets', r'rejection pairs?|rejects?': 'rejects', r'observations?': 'observations',
         r'goldens?': 'goldens', r'invocations?': 'invocations'}
ALIASES = {'controls': ('controls', 'fixtures'), 'fixtures': ('fixtures', 'cases')}
CLAIM_DOCS = ('docs/compiler-campaign/GATES.md', 'tests/**/README.md', 'tests/**/SPEC.md', 'tests/**/REPORT.md', 'vm/*.md',
              'research/*/README.md')
LIVE = ('docs/**/*.md', 'vm/**', 'src/**', 'tests/**', 'scripts/**', 'tools/**', 'README.md', 'AGENTS.md')
NOT_LIVE = ('**/receipts/**', '**/evidence/**', '**/REVIEW-*.md', 'docs/COMPILER-CAMPAIGN.md', '**/*.json', '**/*.gz',
            'docs/compiler-campaign/inventory/**', 'docs/perch-calibration/**', 'docs/perch-experiments/**',
            'tests/prechecks/**', 'scripts/prechecks/**', 'docs/prechecks.md', '**/fixtures/**')
GATE_SCRIPT = re.compile(r'^(?:tests|research)/.+/(?:check[^/]*\.py|host-check\.py)$')
COUNT_KEYS = re.compile(r"""['"](\w*(?:laws|mutants|fixtures|controls|observations|goldens|invocations|cases|proof_laws)\w*)['"]\s*:\s*(\d+)\b""")
COUNT_ASSIGN = re.compile(r'^\s*(new_laws|proof_laws|filled_laws|mutant_count|fixture_count|law_count)\s*=\s*(\d+)\s*$')
PRINTED = re.compile(r"""print\(f?['"][^'"{}]*\b(\d+) (?:filled |new |frozen )?(laws|mutants|fixtures|controls|observations)\b""")
LEN_PIN = re.compile(r'\blen\((corpus|files|names|units|sources|paths|programs)\w*\)\s*==\s*(\d+)')
SERIALIZED = re.compile(r'\bin\s+json\.dumps\(')


def _authored(ctx, path: str) -> list[str]:
    """Lines this branch added to `path` (empty when unchanged)."""
    if ctx.base is None:
        return []
    patch = ctx.repo.patch(ctx.base.treeish, ctx.head.treeish, [path], unified=0)
    return [line for hunks in diffs.parse(patch).values() for h in hunks for line in h.added]


def _changed_paragraphs(ctx, path: str):
    added = set(_authored(ctx, path))
    if not added:
        return
    for paragraph in T.paragraphs(ctx.head.text(path) or ''):
        if any(line in added for line in paragraph.text.split('\n')):
            yield paragraph


def _gate_of(paragraph: str, gates: dict) -> str | None:
    """The gate a paragraph is about: the first registered gate name it puts in backticks."""
    for token in re.findall(r'`([\w:-]+)`', paragraph):
        if token in gates:
            return token
    return None


# ---- R1 ---------------------------------------------------------------------
def stale_counts(ctx, facts_now: dict, receipts: dict) -> list[Condition]:
    found = []
    gate_count = facts_now['gate_count']
    for path in ctx.changed_paths():
        if not globs.match_any(CLAIM_DOCS, path):
            continue
        for paragraph in _changed_paragraphs(ctx, path):
            if T.SKIP_SECTIONS.search(paragraph.heading):
                continue
            gate = _gate_of(paragraph.text, receipts)
            if gate:
                lists = receipts[gate]['lists']
                pairs = list(T.claim_pairs(paragraph.text, NOUNS))
                once = {k for k in {p[1] for p in pairs} if sum(1 for q in pairs if q[1] == k) == 1}   # a breakdown is not a total
                for number, key, text in (p for p in pairs if p[1] in once):
                    actual = next((lists[k] for k in ALIASES.get(key, (key,)) if k in lists), None)
                    if actual is not None and actual != number:
                        found.append(Condition(ID, 'stale-count', 'minor', {'path': path, 'gate': gate, 'claim': text.lower()},
                                               value={'claimed': number, 'measured': actual},
                                               expected=f'{gate} receipt records {actual} {key}',
                                               observed=f'{path}:{paragraph.line} says {text!r} but the receipt has {actual}',
                                               fix_hint='Derive the number from the receipt, or correct the sentence.'))
            for number, _key, text in T.claim_pairs(paragraph.text, {r'gates?': 'gates'}, gap=1):
                if re.search(r'\ball\s+' + re.escape(text.split()[0]) + r'\b', paragraph.text, re.I) and number != gate_count:
                    found.append(Condition(ID, 'stale-count', 'minor', {'path': path, 'claim': text.lower()},
                                           value={'claimed': number, 'measured': gate_count},
                                           expected=f'{gate_count} gates are registered in scripts/gates/run.py',
                                           observed=f'{path}:{paragraph.line} says {text!r}'))
    for commit in ctx.commits():
        if commit.is_merge:
            continue
        for number, _key, text in T.claim_pairs(commit.body, {r'gates?': 'gates'}, gap=1):
            if re.search(r'\ball\s+' + re.escape(text.split()[0]) + r'\b', commit.body, re.I) and number != gate_count:
                found.append(Condition(ID, 'stale-count', 'minor', {'commit': commit.sha, 'claim': text.lower()},
                                       actor='coordinator', value={'claimed': number, 'measured': gate_count},
                                       expected=f'{gate_count} gates are registered at head',
                                       observed=f'{commit.sha[:8]} says {text!r}'))
    return found


# ---- R2 ---------------------------------------------------------------------
def retired_terms(ctx) -> list[Condition]:
    terms = retired_lib.load(ctx.main_tree or ctx.base)
    found = []
    for path in ctx.changed_paths():
        if not globs.match_any(LIVE, path) or globs.match_any(NOT_LIVE, path):
            continue
        lines = ctx.head.text(path) or ''
        all_lines = lines.split('\n')
        added = set(_authored(ctx, path))
        for number, line in enumerate(all_lines):
            if line not in added:
                continue
            context = ' '.join(all_lines[max(number - 1, 0):number + 2]).lower()
            for term, regex in terms:
                if regex.search(line) and not retired_lib.allowed(term, context):
                    in_spec = path.endswith('SPEC.md')
                    found.append(Condition(ID, 'retired-term', 'major' if in_spec else 'minor',
                                           {'path': path, 'term': term['id'], 'text': re.sub(r'\W+', ' ', line).strip()[:50].lower()},
                                           expected=f"{term['id']} superseded this literal ({term.get('reason', '')})",
                                           observed=f'{path}:{number + 1}: {line.strip()[:100]}',
                                           fix_hint='Update it to the current decision, or mark the context (superseded, earlier drafts).'))
    return found


# ---- R3 ---------------------------------------------------------------------
def missing_paths(ctx) -> list[Condition]:
    found = []
    for path in ctx.changed_paths():
        if not path.endswith('.md') or globs.match_any(NOT_LIVE, path) and not globs.match_any(CLAIM_DOCS, path):
            continue
        if T.SKIP_SECTIONS.search(path):
            continue
        for line in _authored(ctx, path):
            for token in T.PATH_TOKEN.findall(line):
                if any(c in token for c in '*<>{}') or token.endswith('/'):
                    continue
                token = token.rstrip('.,:;')
                if not ctx.head.has(token) and not ctx.head.is_dir(token):
                    found.append(Condition(ID, 'missing-path', 'minor', {'path': path, 'cited': token},
                                           expected='a path cited in a document exists at head',
                                           observed=f'{path} cites `{token}`, which is not tracked',
                                           fix_hint='Fix the path, or drop the citation.'))
            for token in re.findall(r'`(\.local/[^`\s]+\.(?:log|txt|json))`', line):
                found.append(Condition(ID, 'untracked-evidence', 'minor', {'path': path, 'cited': token},
                                       expected='tracked evidence cites tracked files',
                                       observed=f'{path} cites ignored scratch {token}',
                                       fix_hint='Commit the evidence under the increment, or cite the command that produces it.'))
    return found


# ---- R4 ---------------------------------------------------------------------
def report(ctx, facts_now: dict) -> list[Condition]:
    if not ctx.inc or ctx.identity:
        return []
    directory = ctx.root / '.local' / ctx.inc
    handoff, report_json = directory / 'HANDOFF.md', directory / 'REPORT.json'
    if not handoff.is_file() and not report_json.is_file():
        return [Condition(ID, 'report-missing', 'info', {'path': f'.local/{ctx.inc}/HANDOFF.md'}, actor='coordinator',
                          expected='the executor leaves HANDOFF.md or REPORT.json for the reviewers',
                          observed='no handoff report; a harness artifact that no increment commit can create',
                          fix_hint='The harness writes REPORT.json after each session.')]
    found = []
    text = handoff.read_text(errors='replace') if handoff.is_file() else ''
    if report_json.is_file():
        try:
            text += '\n' + '\n'.join(f'{k}: {v}' for k, v in json.loads(report_json.read_text()).items() if not isinstance(v, (dict, list)))
        except ValueError:
            pass
    head = re.search(r'(?im)^\W*head\W*[:=]\s*`?([0-9a-f]{7,40})', text)
    if head and ctx.head_commit and not ctx.head_commit.startswith(head.group(1)):
        recorded = ctx.repo.rev_parse(head.group(1))
        moved = ctx.repo.name_status(recorded, ctx.head_commit) if recorded else None
        meaningful = [c for c in (moved or []) if not (c.path.endswith('.md') or R.is_receipt(c.path))]
        if recorded is None or meaningful:
            found.append(Condition(ID, 'report-stale', 'minor', {'path': f'.local/{ctx.inc}', 'field': 'head'},
                                   expected='the report describes the head under review',
                                   observed=f'report head {head.group(1)} is not head {ctx.head_commit[:8]}'
                                            + (f' ({len(meaningful)} non-doc file(s) changed since)' if meaningful else '')))
    gates_claim = re.search(r'(?im)^\W*gates\W*[:=]\s*(?:all\s+)?(\d+)', text)
    if gates_claim and int(gates_claim.group(1)) != facts_now['gate_count']:
        found.append(Condition(ID, 'report-gates', 'minor', {'path': f'.local/{ctx.inc}', 'field': 'gates'},
                               value={'claimed': int(gates_claim.group(1)), 'measured': facts_now['gate_count']},
                               expected=f"{facts_now['gate_count']} gates are registered",
                               observed=f"the report says gates: {gates_claim.group(1)}"))
    return found


# ---- R5 ---------------------------------------------------------------------
def hardcoded_counts(ctx) -> list[Condition]:
    found = []
    for change in ctx.changes():
        if change.status not in 'AMR' or not GATE_SCRIPT.match(change.path):
            continue
        for line in _authored(ctx, change.path):
            for pattern, kind in ((COUNT_KEYS, 'counted-key'), (COUNT_ASSIGN, 'counted-assignment'), (PRINTED, 'printed-literal'),
                                  (LEN_PIN, 'len-pin'), (SERIALIZED, 'serialized-membership')):
                match = pattern.search(line)
                if match:
                    found.append(Condition(ID, 'hardcoded-count', 'minor',
                                           {'path': change.path, 'kind': kind, 'text': re.sub(r'\s+', ' ', line.strip())[:60]},
                                           expected='a gate records measured counts, never literals or loose substring coverage',
                                           observed=f'{kind}: {line.strip()[:100]}',
                                           fix_hint='Derive the number from the data the gate just checked.'))
                    break
    return found


# ---- R6 ---------------------------------------------------------------------
def extraction_shape(ctx) -> list[Condition]:
    if ctx.base is None:
        return []
    source = ctx.head.text(gates_lib.RUN_PY) or ''
    branches = set(re.findall(r"gate\.name\s*(?:==|in)\s*\(?\s*['\"]([\w:-]+)['\"]", source))
    branches |= set(re.findall(r"gate\.name\.endswith\(['\"]([^'\"]+)['\"]", source))
    now, before = facts_lib.gate_receipts(ctx.head), facts_lib.gate_receipts(ctx.base)
    found = []
    for name, info in now.items():
        if name in branches or any(name.endswith(s) for s in ('-trust',)) or not info['path']:
            continue
        changed = name not in before or info['path'] != before[name]['path'] or not ctx.head.same(ctx.base, info['path'])
        if not changed:
            continue
        for key, kind in info['raw_types'].items():
            if kind != 'list':
                found.append(Condition(ID, 'count-extraction-shape', 'minor', {'gate': name, 'key': key}, actor='coordinator',
                                       value={'type': kind},
                                       expected="a generic receipt key holds a list, so the runner's counts() reports its length",
                                       observed=f'{info["path"]}: {key} is a {kind}; counts() would report len() of it',
                                       fix_hint='Write a list, or add a counts() branch (owned by scripts/gates).'))
    return found


# ---- R7 ---------------------------------------------------------------------
def ground_laws(ctx) -> list[Condition]:
    if ctx.base is None:
        return []
    now, before = facts_lib.law_counts(ctx.head), facts_lib.law_counts(ctx.base)
    found, new_total, new_ground = [], 0, 0
    for path, info in now.items():
        old = set(before.get(path, {}).get('ground', []))
        previous = {n for n, _ in facts_lib.LAW.findall(ctx.base.text(path) or '')} if ctx.base.has(path) else set()
        current = {n for n, _ in facts_lib.LAW.findall(ctx.head.text(path) or '')}
        new_total += len(current - previous)
        for name in sorted(set(info['ground']) - old):
            new_ground += 1
            if not re.search(r'_witness|_example|_instance|_case', name):
                found.append(Condition(ID, 'ground-law-general-name', 'minor', {'path': path, 'law': name},
                                       expected='a law with a general name quantifies over its domain (a `for` binder)',
                                       observed=f'law {name} has no binder: a ground instance under a general name',
                                       fix_hint='Add the universal binder, or rename it `..._witness` / `..._example`.'))
    if new_total >= 4 and new_ground / new_total > 0.25:
        found.append(Condition(ID, 'ground-law-general-name', 'info', {'kind': 'ground-share'},
                               value={'ground': new_ground, 'new': new_total},
                               expected='at most a quarter of new laws are ground instances',
                               observed=f'{new_ground} of {new_total} new laws have no binder'))
    return found


# ---- R9 ---------------------------------------------------------------------
def vestiges(ctx) -> list[Condition]:
    if ctx.base is None:
        return []
    bend = [p for p in ctx.head.files() if p.endswith('.bend') and (p.startswith('src/') or p.startswith('tests/'))]
    added = {}
    for path in ctx.changed_paths():
        if path.endswith('.bend') and path.startswith('src/') and not re.search(r'(?:LAWS|PROOF)\.bend$', path):
            for line in _authored(ctx, path):
                match = re.match(r'def\s+(\w+)\s*\(', line)
                if match:
                    added.setdefault(match.group(1), path)
    if not added:
        return []
    live_text = {p: ctx.head.text(p) or '' for p in bend if not re.search(r'(?:LAWS|PROOF)\.bend$', p)}
    proof_text = {p: ctx.head.text(p) or '' for p in bend if re.search(r'(?:LAWS|PROOF)\.bend$', p)}
    tests = ' '.join(ctx.head.text(p) or '' for p in ctx.head.files() if p.startswith('tests/') and p.endswith(('.py', '.mjs', '.ts')))
    docs = ' '.join(ctx.head.text(p) or '' for p in ctx.head.files() if p.endswith('.md'))
    found = []
    for name, path in sorted(added.items()):
        token = re.compile(rf'(?<![\w]){re.escape(name)}(?![\w])')
        uses = sum(len(token.findall(text)) for text in live_text.values())
        if uses > 1 or name == 'main' or token.search(tests):
            continue                                    # more than its own definition, or an entry point
        cited = any(token.search(text) for text in proof_text.values()) or token.search(docs)
        found.append(Condition(ID, 'vestige', 'minor' if cited else 'info', {'path': path, 'def': name},
                               expected='a new def is reachable from the program, not only from laws and proofs',
                               observed=f'def {name} is referenced only by its own definition'
                                        + (' and by laws or documents' if cited else ''),
                               fix_hint='Delete it, or use it.'))
    return found


def run(ctx) -> CheckResult:
    result = CheckResult()
    now = facts_lib.collect(ctx.head)
    result.facts = now
    if ctx.base is not None:
        result.facts['base'] = {k: v for k, v in facts_lib.collect(ctx.base).items() if k in ('gate_count', 'gates')}
    if ctx.base is None or (ctx.identity and not ctx.commits()):
        result.notes.append('identity: no changed paragraphs, lines or commits to judge')
        return result
    receipts = facts_lib.gate_receipts(ctx.head)
    rules = [('stale-count', lambda: stale_counts(ctx, now, receipts)), ('retired-term', lambda: retired_terms(ctx)),
             ('missing-path', lambda: missing_paths(ctx)), ('report', lambda: report(ctx, now)),
             ('hardcoded-count', lambda: hardcoded_counts(ctx)), ('count-extraction-shape', lambda: extraction_shape(ctx)),
             ('ground-law-general-name', lambda: ground_laws(ctx)), ('vestige', lambda: vestiges(ctx))]
    for name, fn in rules:
        result.conditions += fn()
        result.rules_run.append(name)
    return result


CHECK = Check(ID, 'claims-vs-facts', 'prose, reports and names against measured facts', run, budget=10, needs=('C5',))
