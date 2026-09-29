"""Packet builders P1-P7 (DESIGN 3.8): deterministic selection of a claim and the evidence that decides it.

Each builder takes the run context (two trees, the manifest) and returns (packets, unavailable). Builders read git
objects only. Selection is by mechanical triggers (absolute words, invariance verbs, named identifiers), never
by a model, so the same commit always yields the same packets.
"""
from __future__ import annotations

import ast
import json
import re

from lib import diffs, globs
from . import common as C
from .common import Packet, Source, Unavailable

TRIGGERS = re.compile(r'\b(only|exactly|every|all|never|always|unchanged|identical|requires?|enforces?|pending|remains?|'
                      r'regenerated|retained|unrun|not yet)\b', re.I)
INVARIANCE = re.compile(r'\b(unchanged|keeps?|only|never|forbid\w*|frozen|must not)\b', re.I)
DOC_SKIP = re.compile(r'(?:^|/)REVIEW-[^/]*\.md$|perch-review-log\.md$|decision-log|CHANGELOG|docs/perch-calibration/|docs/perch-experiments/|'
                      r'docs/prechecks\.md$|tests/prechecks/', re.I)
NORMATIVE = ('**/SPEC.md', '**/CONTRACT.json', '**/GATES.md', '**/README.md', 'vm/*.md', 'docs/compiler-campaign/*.md')
GATE_SCRIPT = re.compile(r'^(?:tests|research)/.+/(?:check[^/]*\.py|host-check\.py)$|^vm/check[^/]*\.py$')
NOT_CODE = re.compile(r'\.(?:md|json|gz|txt|log|lock|png|wasm)$|/receipts/|/evidence/|/generated/')
IDENT = re.compile(r'`([A-Za-z_][\w.-]{3,}(?:\(\))?)`')
PATHS = re.compile(r'`((?:[\w.-]+/)+[\w.-]+\.[A-Za-z0-9]+)`')
BUDGET = re.compile(r'\b(\d[\d,]{2,})\s+(?:[\w-]+\s+){0,2}(?:steps?|bytes?|pages?|words?|records?|depth|levels?|slots?|fuel|visits?|limit|budget|quantum|arity|MiB|KiB|characters?)\b', re.I)


# ---- shared selection helpers -------------------------------------------------------------
def changed_docs(ctx) -> list[str]:
    return [p for p in ctx.changed_paths(statuses='AMRC') if (p.endswith('.md') or p.endswith('CONTRACT.json')) and not DOC_SKIP.search(p)]


def changed_code(ctx) -> list[str]:
    return [p for p in ctx.changed_paths(statuses='AMRC') if not NOT_CODE.search(p) and not DOC_SKIP.search(p)]


_MEMO: dict = {}


def memo(ctx, kind: str, path: str, compute):
    """Per (head, base, kind, path) results: a big increment has hundreds of claims that all rank the same files."""
    key = (ctx.head.treeish, ctx.base.treeish if ctx.base else None, kind, path)
    if key not in _MEMO:
        _MEMO[key] = compute()
    return _MEMO[key]


def added_numbers(ctx, path: str) -> list[int]:
    def compute():
        patch = ctx.repo.patch(ctx.base.treeish, ctx.head.treeish, [path], unified=0)
        lines = []
        for hunks in diffs.parse(patch).values():
            for hunk in hunks:
                lines += list(range(hunk.new_start, hunk.new_start + len(hunk.added)))
        return lines
    return memo(ctx, 'added', path, compute)


STOP = set('''which their there after before every about would could should these those other while where because through '''
           '''between being still under until only never always'''.split())
_TOKEN_CACHE: dict = {}


def words(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r'[A-Za-z][A-Za-z0-9]{4,}', text)} - STOP


def diff_tokens(ctx) -> dict[str, set[str]]:
    """{changed code path: words on its added lines}, computed once per (head, base)."""
    key = (ctx.head.treeish, ctx.base.treeish if ctx.base else None)
    if key not in _TOKEN_CACHE:
        patch = diff_text(ctx, changed_code(ctx), unified=0)
        _TOKEN_CACHE[key] = {path: words(' '.join(line for hunk in hunks for line in hunk.added))
                             for path, hunks in diffs.parse(patch).items()}
    return _TOKEN_CACHE[key]


def relevance(ctx, paragraph: str) -> int:
    """How many distinct paragraph words occur on the added code lines: a claim the diff can decide scores high."""
    tokens = words(paragraph)
    seen = set().union(*diff_tokens(ctx).values()) if diff_tokens(ctx) else set()
    return len(tokens & seen)


def claim_score(ctx, unit: str, *, named: bool = False) -> float:
    """Rank a claim unit: how much of it the diff speaks about (coverage and count), how absolute it is, how short."""
    tokens = words(unit)
    shared = relevance(ctx, unit)
    coverage = shared / len(tokens) if tokens else 0.0
    return round(20 * named + 80 * coverage + 3 * min(shared, 6) + 3 * len(TRIGGERS.findall(unit)) - min(len(tokens) / 4, 30), 2)


def ranked_paths(ctx, paragraph: str, paths: list[str]) -> list[str]:
    """Changed code paths ordered by the words they share with the paragraph (then by name)."""
    tokens, table = words(paragraph), diff_tokens(ctx)
    return sorted(paths, key=lambda p: (-len(tokens & table.get(p, set())), p))


def split_blocks(path: str, text: str) -> list[tuple[int, int, str]]:
    """Function-sized regions of a file: Python defs and methods, top-level Bend and JS declarations, else 40-line chunks."""
    lines = text.split('\n')
    if path.endswith('.py'):
        try:
            tree = ast.parse(text)
        except SyntaxError:
            tree = None
        if tree is not None:
            spans = []
            for node in tree.body:
                kids = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))] if isinstance(node, ast.ClassDef) else []
                for item in (kids or [node]):
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign)):
                        spans.append((min([item.lineno] + [d.lineno for d in getattr(item, 'decorator_list', [])]), item.end_lineno))
            return [(a, b, '\n'.join(lines[a - 1:b])) for a, b in spans]
    if path.endswith(('.bend', '.mjs', '.js', '.ts')):
        starts = [i for i, line in enumerate(lines) if C.TOP.match(line)]
        return [(a + 1, (starts[k + 1] if k + 1 < len(starts) else len(lines)), '\n'.join(lines[a:(starts[k + 1] if k + 1 < len(starts) else len(lines))]))
                for k, a in enumerate(starts)]
    return [(i + 1, min(i + 40, len(lines)), '\n'.join(lines[i:i + 40])) for i in range(0, len(lines), 40)]


def pieces_of(ctx, path: str) -> list[tuple[set, str, str]]:
    """(words, sort label, text) of the regions of one changed file that can serve as evidence, computed once."""
    def compute():
        pieces = []
        if ctx.base is not None and ctx.base.has(path):
            chunks = re.split(r'(?m)^(?=@@ )', diff_text(ctx, [path], unified=2))
            header, hunks = chunks[0], chunks[1:]
            for k, hunk in enumerate(hunks):
                pieces.append((words(hunk), f'{k:06d}', (header if k == 0 else '') + hunk))
        else:
            text = ctx.head.text(path) or ''
            for start, end, block in split_blocks(path, text):
                if block.strip():
                    pieces.append((words(block), f'{start:06d}', f'`{path}:{start}-{end}` (added)\n{C.numbered(block, start)}\n'))
        return pieces
    return memo(ctx, 'pieces', path, compute)


def relevant_evidence(ctx, paragraph: str, paths: list[str]) -> tuple[str, list[str]]:
    """The changed regions that share the most words with the claim, best first until the evidence cap.

    A modified file contributes its diff hunks; an added file contributes its function-sized blocks (its
    whole diff would exhaust the cap on the first declarations and never reach the one that decides the claim).
    """
    tokens = words(paragraph)
    scored = []
    for path in paths:
        for piece_words, label, body in pieces_of(ctx, path):
            scored.append((len(tokens & piece_words), path, label, body))
    ranked = sorted(scored, key=lambda p: (-p[0], p[1], p[2]))
    chosen, used, size = [], [], 0
    for score, path, label, body in ranked:
        if score == 0 and chosen:
            break
        cost = len(body.encode('utf-8'))
        if size + cost > C.EVIDENCE_LIMIT and chosen:
            continue
        chosen.append((path, label, body))
        used.append(path)
        size += cost
    chosen.sort(key=lambda c: (c[0], c[1]))
    return '\n'.join(body for _p, _l, body in chosen), sorted(set(used))


CODE_TOKEN = re.compile(r'[A-Za-z_][A-Za-z0-9_-]{3,}|(?<![\w.])\d{3,}(?![\w.])')


def code_index(ctx) -> dict:
    """{token: [(path, line, text)]} over every code file at head, built once: one pass replaces a `git grep` per token."""
    def compute():
        index: dict = {}
        for path in ctx.head.files():
            if not path.endswith(('.py', '.mjs', '.ts', '.js', '.bend')):
                continue
            for number, line in enumerate((ctx.head.text(path) or '').split('\n'), 1):
                for token in set(CODE_TOKEN.findall(line)):
                    hits = index.setdefault(token, [])
                    if len(hits) < 40:
                        hits.append((path, number, line))
        return index
    return memo(ctx, 'codeindex', '', compute)


def grep_code(ctx, token: str, suffixes: tuple = ('.py', '.mjs', '.ts', '.js', '.bend')) -> list[tuple[str, int, str]]:
    return [h for h in code_index(ctx).get(token, []) if h[0].endswith(suffixes)]


def source(ctx, path: str) -> Source:
    return Source(path, ctx.head_commit or ctx.head.treeish, ctx.head.sha256(path) or '')


def quote(text: str) -> str:
    return '\n'.join('> ' + line if line.strip() else '>' for line in text.split('\n'))


def diff_text(ctx, paths: list[str], unified: int = 3) -> str:
    if not paths:
        return ''
    if len(paths) == 1:
        return memo(ctx, f'diff{unified}', paths[0], lambda: ctx.repo.patch(ctx.base.treeish, ctx.head.treeish, paths, unified=unified))
    return ctx.repo.patch(ctx.base.treeish, ctx.head.treeish, paths, unified=unified)


def evidence_block(title: str, text: str, lang: str = '') -> str:
    body, marker = C.cap(text)
    return f'{title}\n{C.fence(body, lang)}' + (f'\n{marker}' if marker else '')


def _top(packets: list[Packet], limit: int = C.PER_RULE_LIMIT) -> list[Packet]:
    """The `limit` highest-scoring packets, numbered in key order so rebuilding is byte-identical."""
    best = sorted(_dedupe(packets), key=lambda p: (-p.meta.get('score', 0), p.key))[:limit]
    return sorted(best, key=lambda p: p.key)


def _dedupe(packets: list[Packet]) -> list[Packet]:
    seen, out = set(), []
    for packet in sorted(packets, key=lambda p: (p.key, p.claim)):
        if (packet.rule, packet.key) not in seen:
            seen.add((packet.rule, packet.key))
            out.append(packet)
    return out


# ---- P1 claim-holds-against-evidence ------------------------------------------------------
def claim_units(ctx, path: str):
    """(first, last, text, lead, section) for every claim unit (list item or sentence run) that has an added line."""
    text = ctx.head.text(path) or ''
    rows = text.split('\n')
    seen, out = set(), []
    for number in added_numbers(ctx, path):
        if number > len(rows) or not rows[number - 1].strip():
            continue                                             # a blank line is not a claim
        first, last, unit, lead = C.unit_at(text, number)
        if (first, last) in seen or not unit.strip() or unit.lstrip().startswith(('|', '```', '#')):
            continue
        seen.add((first, last))
        out.append((first, last, unit, lead, C.section_at(text, first)))
    return out


def claim_text(path, first, last, section, unit, lead) -> str:
    where = f'{path}:{first}-{last}' + (f' (section: {section})' if section else '')
    return where + ' - verbatim text:\n\n' + (quote(lead) + '\n' if lead else '') + quote(unit)


def p1(ctx):
    rule, packets, missing = 'claim-holds-against-evidence', [], []
    code = changed_code(ctx)
    for path in changed_docs(ctx):
        for first, last, unit, lead, section in claim_units(ctx, path):
            claim = claim_text(path, first, last, section, unit, lead)
            key = f'{path}:{first}'
            if TRIGGERS.search(unit):                              # type A: the claim against the diff that decides it
                named = [p for p in PATHS.findall(unit) if p in code]
                if named:
                    patch, used_paths = diff_text(ctx, named, unified=2), named
                else:
                    patch, used_paths = relevant_evidence(ctx, unit, ranked_paths(ctx, unit, code))
                if patch.strip():
                    scope = ('the diff of the paths the claim names' if named
                             else 'the changed regions that share the most words with the claim (diff hunks of modified files, '
                                  'declarations of added files)')
                    packets.append(Packet(rule, key + ':A', claim, evidence_block(f'Evidence: {scope}.', patch, 'diff' if named else ''),
                                          [source(ctx, path)] + [source(ctx, p) for p in used_paths if ctx.head.has(p)][:8],
                                          {'type': 'A', 'score': claim_score(ctx, unit, named=bool(named))}))
                else:
                    missing.append(Unavailable(rule, key + ':A', 'the branch changes no code to check the claim against'))
            if globs.match_any(NORMATIVE, path):                   # type B: the claim against the declarations it names
                blocks, used = [], []
                for token in sorted(set(IDENT.findall(unit)))[:6]:
                    name = token.removesuffix('()')
                    if (not re.search(r'[_-]', name) and not token.endswith('()')) or '/' in name or re.search(r'\.\w{1,4}$', name):
                        continue
                    hits = [h for h in grep_code(ctx, name) if h[0] != path]
                    defs = [h for h in hits if re.search(rf'\b(?:def|function|law|type)\s+{re.escape(name)}\b|\b{re.escape(name)}\s*=', h[2])]
                    for hit in (defs or hits)[:1]:
                        body = ctx.head.text(hit[0]) or ''
                        start, end, block = C.block_at(hit[0], body, hit[1])
                        blocks.append(f'`{hit[0]}:{start}-{end}` (declaration naming `{name}`)\n{C.fence(C.numbered(block, start))}')
                        used.append(source(ctx, hit[0]))
                if blocks:
                    body, marker = C.cap('\n\n'.join(blocks))
                    packets.append(Packet(rule, key + ':B', claim, 'Evidence: the declarations the claim names, at head.\n\n' + body
                                          + (f'\n{marker}' if marker else ''), [source(ctx, path)] + used,
                                          {'type': 'B', 'score': 5 * len(blocks) + claim_score(ctx, unit)}))
                budget_blocks, budget_used = [], []                 # type N: a numeric budget against the code that uses the number
                for number in sorted({m.group(1).replace(',', '') for m in BUDGET.finditer(unit)})[:2]:
                    if int(number) < 100:
                        continue
                    hits = [h for h in grep_code(ctx, number) if h[0] != path]
                    hits.sort(key=lambda h: (h[0] not in code, h[0], h[1]))
                    for hit in hits[:1]:
                        body = ctx.head.text(hit[0]) or ''
                        start, end, block = C.block_at(hit[0], body, hit[1])
                        budget_blocks.append(f'`{hit[0]}:{start}-{end}` (declaration using the budget {number})\n{C.fence(C.numbered(block, start))}')
                        budget_used.append(source(ctx, hit[0]))
                if budget_blocks:
                    body, marker = C.cap('\n\n'.join(budget_blocks))
                    packets.append(Packet(rule, key + ':N', claim, 'Evidence: the declarations that use the stated number, at head.\n\n' + body
                                          + (f'\n{marker}' if marker else ''), [source(ctx, path)] + budget_used,
                                          {'type': 'N', 'score': 5 * len(budget_blocks) + claim_score(ctx, unit)}))
    limit = ctx.options.get('packet_limit', C.PER_RULE_LIMIT)
    share = {'A': 0.4, 'B': 0.3, 'N': 0.3}                       # slots by kind of claim: against diffs, declarations, budgets
    by_type = {t: sorted((p for p in _dedupe(packets) if p.meta['type'] == t), key=lambda p: (-p.meta['score'], p.key)) for t in share}
    chosen, spare = [], []
    for kind, ranked in by_type.items():
        take = -(-int(limit * share[kind] * 100) // 100)
        chosen += ranked[:take]
        spare += ranked[take:]
    chosen += sorted(spare, key=lambda p: (-p.meta['score'], p.key))[:max(limit - len(chosen), 0)]
    return sorted(chosen[:limit], key=lambda p: p.key), missing


# ---- P2 passages-agree ------------------------------------------------------------------
def _corpus(ctx) -> list[str]:
    return [p for p in ctx.head.files() if p.endswith('.md') and not DOC_SKIP.search(p)
            and globs.match_any(('vm/*.md', 'docs/COMPILER-CAMPAIGN.md', 'docs/compiler-campaign/*.md', 'src/*.md', 'tests/*/*.md',
                                 'README.md'), p)]


def p2(ctx):
    rule, packets, missing = 'passages-agree', [], []
    terms: dict[str, list[tuple[str, int]]] = {}
    for path in changed_docs(ctx):
        text = ctx.head.text(path) or ''
        for number in added_numbers(ctx, path):
            _f, _l, paragraph = C.paragraph_at(text, number)
            for term in set(re.findall(r'\bD\d{1,3}\b', paragraph)) | {t.removesuffix('()') for t in IDENT.findall(paragraph) if re.search(r'[_-]', t)}:
                terms.setdefault(term, []).append((path, number))
    corpus = _corpus(ctx)
    texts = {p: ctx.head.text(p) or '' for p in corpus}
    for term in sorted(terms)[:200]:
        passages = []
        pattern = re.compile(rf'(?<![\w-]){re.escape(term)}(?![\w-])')
        for path in corpus:
            body = texts[path]
            for match in pattern.finditer(body):
                line = body.count('\n', 0, match.start()) + 1
                first, last, paragraph = C.paragraph_at(body, line)
                sentence = next((s for s in C.sentences_of(paragraph) if pattern.search(s)), paragraph.strip()[:300])
                passages.append((path, first, C.section_at(body, first), sentence))
        unique = sorted({(p, f, s, x) for p, f, s, x in passages})
        distinct = {(p, s) for p, _f, s, _x in unique}
        if len(distinct) < 2:
            continue
        changed = set(terms[term])
        claim_rows, evidence_rows = [], []
        for path, line, section, sentence in unique[:14]:
            row = f'- {path}:{line}' + (f' (section: {section})' if section else '') + f': {sentence}'
            (claim_rows if any(p == path and abs(n - line) <= 12 for p, n in changed) else evidence_rows).append(row)
        if not claim_rows:
            continue
        if term.startswith('D') and term[1:].isdigit() and ctx.head.has('docs/COMPILER-CAMPAIGN.md'):
            row = re.search(rf'(?m)^\|\s*{term}\s*\|.*$', ctx.head.text('docs/COMPILER-CAMPAIGN.md') or '')
            if row:
                evidence_rows.insert(0, f'- docs/COMPILER-CAMPAIGN.md (decision row, verbatim): {row.group(0)}')
        body_claim = f'Term `{term}`. Passages this branch changed or added:\n\n' + '\n'.join(claim_rows)
        body_evidence = 'Other passages that mention the term:\n\n' + ('\n'.join(evidence_rows) or '(none)')
        text, marker = C.cap(body_evidence)
        packets.append(Packet(rule, term, body_claim, text + (f'\n{marker}' if marker else ''),
                              [source(ctx, p) for p, *_ in unique[:8]],
                              {'term': term, 'score': len(unique) + 2 * len(claim_rows) + 10 * (term.startswith('D') and term[1:].isdigit())}))
    return _top(packets, ctx.options.get('packet_limit', C.PER_RULE_LIMIT)), missing


# ---- P3 outcome-follows-d4 -----------------------------------------------------------------
OUTCOME = re.compile(r'\b(Unsupported|Invalid|Exhausted|HostFailure)\b')


def p3(ctx):
    rule, missing = 'outcome-follows-d4', []
    specs = [p for p in ctx.changed_paths(statuses='AMRC') if p.endswith('SPEC.md') and not DOC_SKIP.search(p)]
    decisions = ctx.head.text('docs/COMPILER-CAMPAIGN.md') or ''
    rows = [m.group(0) for m in re.finditer(r'(?m)^\|\s*D(?:4|16)\s*\|.*$', decisions)]
    if not rows:
        return [], [Unavailable(rule, 'D4', 'no D4 or D16 decision rows at head')]
    packets = []
    for path in sorted(specs):
        text = ctx.head.text(path) or ''
        by_section: dict[str, list] = {}
        for first, last, unit, lead, section in claim_units(ctx, path):
            if OUTCOME.search(unit):
                by_section.setdefault(section, []).append((first, last, unit, lead))
        context_blocks = ['Decision rows (verbatim, docs/COMPILER-CAMPAIGN.md):\n\n' + '\n'.join(rows)]
        for number, level, heading in C.sections(text):
            if re.search(r'limit|outcome|bound|exhaust|refus|resource', heading, re.I):
                nxt = next((n for n, lv, _h in C.sections(text) if n > number and lv <= level), len(text.split('\n')) + 1)
                context_blocks.append(f'{path}:{number}-{nxt - 1} (section: {heading}):\n\n'
                                      + quote('\n'.join(text.split('\n')[number - 1:nxt - 1])))
        for expected in ('vm/golden/vm-expected.json',):
            if ctx.head.has(expected):
                try:
                    data = json.loads(ctx.head.text(expected) or 'null')
                except ValueError:
                    data = None
                rows_ = data if isinstance(data, list) else (data or {}).get('rows', []) if isinstance(data, dict) else []
                departs = [r for r in rows_ if isinstance(r, dict) and re.search(r'diverg|refus|host-?failure|exhaust', json.dumps(r), re.I)]
                if departs:
                    context_blocks.append(f'{expected}: frozen rows that record a refusal or divergence:\n'
                                          + C.fence(json.dumps(departs[:12], indent=1, sort_keys=True), 'json'))
        body, marker = C.cap('\n\n'.join(context_blocks))
        for section, units in by_section.items():
            for at in range(0, len(units), 3):                      # three outcome claims per packet, none dropped
                group = units[at:at + 3]
                claims = [claim_text(path, f, l, section, u, lead) for f, l, u, lead in group]
                score = sum(len(set(OUTCOME.findall(u))) + 2 * bool(re.search(r'limit|bound|refus|cause|budget', u, re.I))
                            for _f, _l, u, _lead in group)
                frozen, used = [], [source(ctx, path)]
                for token in sorted({t for _f, _l, u, _lead in group for t in re.findall(r'`([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`', u)})[:4]:
                    hits = [h for h in grep_code(ctx, token, ('.py', '.mjs', '.ts')) if h[0] != path and '/receipts/' not in h[0]]
                    for hit in hits[:1]:
                        text_ = ctx.head.text(hit[0]) or ''
                        if hit[0].endswith('.py'):
                            a, b, block = C.block_at(hit[0], text_, hit[1])
                        else:
                            a, b = max(hit[1] - 6, 1), hit[1] + 6
                            block = '\n'.join(text_.split('\n')[a - 1:b])
                        frozen.append(f'`{hit[0]}:{a}-{b}` (frozen expectation code naming `{token}`)\n{C.fence(C.numbered(block, a))}')
                        used.append(source(ctx, hit[0]))
                extra, extra_marker = C.cap('\n\n'.join(frozen), C.EVIDENCE_LIMIT // 2) if frozen else ('', '')
                packets.append(Packet(rule, f'{path}:{group[0][0]}', 'Outcome claims this branch changed:\n\n' + '\n\n'.join(claims),
                                      body + (f'\n{marker}' if marker else '') + (f'\n\nFrozen expectations that name the same cause:\n\n{extra}'
                                                                                + (f'\n{extra_marker}' if extra_marker else '') if extra else ''),
                                      used, {'score': score + 3 * len(frozen)}))
    return _top(packets, ctx.options.get('packet_limit', C.PER_RULE_LIMIT)), missing


# ---- P4 clause-vs-delta --------------------------------------------------------------------
def _clauses(ctx) -> list[tuple[str, str]]:
    found = []
    for path in ('src/CONTRACT.json',):
        if ctx.head.has(path):
            try:
                data = json.loads(ctx.head.text(path) or 'null')
            except ValueError:
                data = None
            stack = [data]
            while stack:
                node = stack.pop()
                if isinstance(node, dict):
                    stack += list(node.values())
                elif isinstance(node, list):
                    stack += node
                elif isinstance(node, str) and INVARIANCE.search(node) and len(node) > 30:
                    found.append((path, node.strip()))
    for path in ctx.changed_paths(statuses='AMRC'):
        if path.endswith(('SPEC.md', 'README.md')) and not DOC_SKIP.search(path):
            for _first, _last, unit, _lead, _section in claim_units(ctx, path):
                if INVARIANCE.search(unit):
                    found.append((path, re.sub(r'\s+', ' ', unit).strip()))
    for sentence in ctx.manifest.get('charter', []) or []:
        found.append(('manifest.charter', sentence))
    return found


def _norm(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip().lower()


def _reworded_clauses(ctx) -> list[tuple[str, str]]:
    """Invariance clauses of the base documents that the branch reworded or deleted: a contract changed under the same name."""
    found = []
    for path in ctx.changed_paths(statuses='MRC'):
        if not (path.endswith(('SPEC.md', 'README.md', 'CONTRACT.json')) and not DOC_SKIP.search(path)) or ctx.base is None:
            continue
        old, new = ctx.base.text(path) or '', _norm(ctx.head.text(path) or '')
        if path.endswith('.json'):
            units = [t for t in re.findall(r'"((?:[^"\\]|\\.){30,})"', old) if INVARIANCE.search(t)]
        else:
            units = [re.sub(r'\s+', ' ', u).strip() for para in re.split(r'\n\s*\n', old) for u in C.sentences_of(para)
                     if INVARIANCE.search(u) and len(u) > 30]
        for unit in units:
            if _norm(unit) not in new:
                found.append((path, unit))
    return found


def p4(ctx):
    rule, packets, missing = 'clause-vs-delta', [], []
    code = changed_code(ctx)
    for path, clause in sorted(set(_reworded_clauses(ctx)))[:120]:
        shared = relevance(ctx, clause)
        hunks = [h for h in re.split(r'(?m)^(?=@@ )', diff_text(ctx, [path], unified=1))[1:]
                 if len(words(clause) & words(''.join(l for l in h.split('\n') if l.startswith('-')))) >= max(2, len(words(clause)) // 2)]
        patch, used = relevant_evidence(ctx, clause, ranked_paths(ctx, clause, code))
        if not hunks and not patch.strip():
            continue
        evidence = ('Evidence: the document change that rewords or removes the clause (unified diff, base to head).\n'
                    + C.fence(''.join(hunks)[:C.EVIDENCE_LIMIT // 3], 'diff') if hunks else '')
        if patch.strip():
            evidence += ('\n\n' if evidence else '') + evidence_block('Evidence: the changed code regions that share the most words with the clause.', patch)
        packets.append(Packet(rule, f'{path}:{C.sha256(clause)[:10]}:base', f'Invariance clause at base ({path}), reworded or removed by this branch:\n\n' + quote(clause),
                              evidence, [source(ctx, path)], {'score': 30 + shared + 2 * len(INVARIANCE.findall(clause))}))
    for path, clause in sorted(set(_clauses(ctx)))[:200]:
        named = [p for p in PATHS.findall(clause) if p in code]
        key = f'{path}:{C.sha256(clause)[:10]}'
        if named:
            patch, used = diff_text(ctx, sorted(set(named)), unified=3), sorted(set(named))
            shared = 100
        else:
            shared = relevance(ctx, clause)
            if shared < 3:                                       # the clause shares too little with the change to govern any of it
                continue
            patch, used = relevant_evidence(ctx, clause, ranked_paths(ctx, clause, code))
        if not patch.strip():
            continue
        packets.append(Packet(rule, key, f'Invariance clause ({path}):\n\n' + quote(clause),
                              evidence_block('Evidence: the governed diff hunks (base to head).', patch, 'diff' if named else ''),
                              [source(ctx, p) for p in used[:6] if ctx.head.has(p)] + ([source(ctx, path)] if ctx.head.has(path) else []),
                              {'score': shared + 2 * len(INVARIANCE.findall(clause))}))
    return _top(packets, ctx.options.get('packet_limit', C.PER_RULE_LIMIT)), missing


# ---- P5 expectation-independent / P6 kill-is-semantic -----------------------------------------
EXPECT_NAMES = {'want', 'expected', 'baseline', 'expect', 'expectation'}


def _functions(source_text: str):
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return []
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _builds_expectation(node) -> bool:
    if re.search(r'expect|want|baseline', node.name, re.I):
        return True
    for child in ast.walk(node):
        if isinstance(child, ast.Assign) and any(isinstance(t, ast.Name) and t.id in EXPECT_NAMES for t in child.targets):
            return True
        if isinstance(child, ast.Dict) and any(isinstance(k, ast.Constant) and k.value in EXPECT_NAMES for k in child.keys):
            return True
    return False


def _claim_sentences(ctx, pattern: str, fallback_rows: str) -> str:
    found = []
    for path in changed_docs(ctx):
        text = ctx.head.text(path) or ''
        for number in added_numbers(ctx, path)[:400]:
            _f, _l, paragraph = C.paragraph_at(text, number)
            for sentence in C.sentences_of(paragraph):
                if re.search(pattern, sentence, re.I) and f'{path}: {sentence}' not in found:
                    found.append(f'{path}: {sentence}')
    if not found:
        return fallback_rows
    return '\n'.join('- ' + f for f in found[:4])


def p5(ctx):
    rule, packets, missing = 'expectation-independent', [], []
    d7 = re.search(r'(?m)^\|\s*D7\s*\|.*$', ctx.head.text('docs/COMPILER-CAMPAIGN.md') or '')
    fallback = f'- docs/COMPILER-CAMPAIGN.md (decision row, verbatim): {d7.group(0)}' if d7 else ''
    claim = _claim_sentences(ctx, r'independent|from the seed|pinned seed|reference|frozen|derived|oracle', fallback)
    for path in ctx.changed_paths(statuses='AMRC'):
        if not GATE_SCRIPT.match(path):
            continue
        text = ctx.head.text(path) or ''
        for node in _functions(text):
            if not _builds_expectation(node):
                continue
            block = '\n'.join(text.split('\n')[node.lineno - 1:node.end_lineno])
            if not claim:
                missing.append(Unavailable(rule, f'{path}::{node.name}', 'no sentence names the expectation source'))
                continue
            packets.append(Packet(rule, f'{path}::{node.name}', 'Statements about where expected values come from:\n\n' + claim,
                                  evidence_block(f'`{path}:{node.lineno}-{node.end_lineno}` function `{node.name}`, which builds expected values:',
                                                 C.numbered(block, node.lineno), 'python'), [source(ctx, path)], {}))
    return _top(packets, ctx.options.get('packet_limit', C.PER_RULE_LIMIT)), missing


def p6(ctx):
    rule, packets, missing = 'kill-is-semantic', [], []
    claim = _claim_sentences(ctx, r'\bkill(?:ed|s)?\b', '- docs/COMPILER-CAMPAIGN.md: mutants killed by named gates (definition of done, trusted runtime).')
    for path in ctx.changed_paths(statuses='AMRC'):
        if not GATE_SCRIPT.match(path):
            continue
        text = ctx.head.text(path) or ''
        blocks = []
        for node in _functions(text):
            body = '\n'.join(text.split('\n')[node.lineno - 1:node.end_lineno])
            if re.search(r'kill|KNOWN_EXITS|semantic-kill|killed_by', node.name + '\n' + body) and re.search(r'mutant|kill', body):
                blocks.append((node.lineno, node.end_lineno, node.name, body))
        constants = re.findall(r'(?m)^(?:KNOWN_EXITS|KILL\w*)\s*=.*(?:\n[ \t].*)*', text)
        if not blocks:
            continue
        rendered = [f'`{path}:{a}-{b}` function `{name}`:\n{C.fence(C.numbered(body, a), "python")}' for a, b, name, body in blocks[:5]]
        rendered += [f'`{path}` constant:\n{C.fence(c, "python")}' for c in constants[:2]]
        evidence, marker = C.cap('\n\n'.join(rendered))
        packets.append(Packet(rule, path, 'Statements about what counts as a kill:\n\n' + claim, evidence + (f'\n{marker}' if marker else ''),
                              [source(ctx, path)], {}))
    return _top(packets, ctx.options.get('packet_limit', C.PER_RULE_LIMIT)), missing


# ---- P7 required-laws-met ----------------------------------------------------------------------
LAW = re.compile(r'(?m)^law\s+(\w+)\s*:\s*\n((?:[ \t]+for [^\n]*\n)*)([ \t]*\{[^\n]*(?:\n(?![ \t]*(?:law|def|type)\b)[^\n]*)*)')


def p7(ctx):
    rule = 'required-laws-met'
    required = ctx.manifest.get('required_laws', []) or []
    if not required:
        return [], [Unavailable(rule, 'manifest', 'the increment manifest declares no required_laws')]
    rows, used = [], []
    for path in sorted(p for p in ctx.head.files() if p.endswith('LAWS.bend') and (p in ctx.changed_paths(statuses='AMRC') or ctx.manifest.is_owned(p))):
        text = ctx.head.text(path) or ''
        proof = path[:-len('LAWS.bend')] + 'PROOF.bend'
        proof_text = ctx.head.text(proof) or ''
        for name, binders, statement in LAW.findall(text):
            count = len([b for b in binders.split('\n') if b.strip()])
            filled = bool(re.search(rf'(?m)^def\s+L\.{re.escape(name)}\s*\(', proof_text)) if ctx.head.has(proof) else None
            flat = re.sub(r'\s+', ' ', statement).strip()[:110]
            status = 'yes' if filled else 'no' if filled is not None else 'no PROOF file'
            rows.append(f'| {path} | {name} | {count} | {status} | {flat} |')
        used.append(source(ctx, path))
    spec = ctx.head.text('src/SPEC.md') or ''
    trust = ''
    for number, level, heading in C.sections(spec):
        if re.search(r'trust|limit|obligation', heading, re.I):
            nxt = next((n for n, lv, _h in C.sections(spec) if n > number and lv <= level), len(spec.split('\n')) + 1)
            trust += f'src/SPEC.md:{number}-{nxt - 1} (section: {heading}):\n\n' + quote('\n'.join(spec.split('\n')[number - 1:nxt - 1])) + '\n\n'
    claim = 'Required laws (verbatim from the increment manifest):\n\n' + '\n'.join(f'- {r}' for r in required)
    matrix = ('| file | law | for-binders | PROOF filled | statement |\n|---|---|---|---|---|\n' + '\n'.join(rows)) if rows else '(no law declarations found)'
    body, marker = C.cap('Operation-to-law matrix computed from the sources:\n\n' + matrix + '\n\nRecorded obligations and limits:\n\n' + (trust or '(none recorded)'))
    return [Packet(rule, 'required-laws', claim, body + (f'\n{marker}' if marker else ''), used, {})], []


BUILDERS = {
    'claim-holds-against-evidence': p1,
    'passages-agree': p2,
    'outcome-follows-d4': p3,
    'clause-vs-delta': p4,
    'expectation-independent': p5,
    'kill-is-semantic': p6,
    'required-laws-met': p7,
}
