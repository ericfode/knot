"""C1 probe-differential: every reviewer probe becomes a permanent control, replayed through Knot's own lanes.

A frozen, content-addressed corpus (the harvested registry, tracked fixtures that carry seed observations, and
deterministically generated programs) is judged by the pinned seed, then run through Knot's parse, check and eval
CLIs built from head and from the effective base. Violations are ratcheted against the base: only a violation that
head adds is a condition, and a base-acceptable verdict that turns into a violation is raised one severity step.
A violation present at both is a known gap of the D4 ledger (reported as a fact, and as R7 when the increment
promised to repair its family).

  R1 d4-invalid          the seed accepts, a Knot lane says Invalid
  R2 unsound-accept      the seed rejects, a Knot lane says Checked or produces a value
  R3 crash               a lane exits 5, 6, 1, or anything unclassified, or times out
  R4 value-disagreement  eval stdout differs from the seed's value on an accepted `main` program
  R5 premature-unsupported   an Unsupported span begins before the seed's parse-error offset
  R6 diagnostic-shape    a non-Checked line is not `Class<TAB>phase<TAB>code<TAB>span`, or has a control character
  R7 incomplete-repair   a violation that exists at base, in a family the manifest lists in d4_targets

Family V (VM images) and R8 (helper lanes) need `vm/evaluate.py` and declared helpers; they report unavailable.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from lib import generate, oracle as oracle_mod
from lib.lanes import SHAPE, Lanes, Outcome
from lib.model import CheckResult, Condition, not_applicable, raised, unavailable
from lib.runner import Check
from lib.seed import SEED_REVISION, Seed

ID = 'C1'
LIMIT = 1000                  # programs per fast run
COLD_LIMIT = 500              # when the base lanes are not cached yet
MAX_CONDITIONS = 60           # conditions per (rule, lane); the rest are counted in the fact table
MANIFESTS = ('tests/subsets/classification-cases.json', 'tests/subsets/frontend-cases.json', 'tests/compiler-checker/cases.json')
SEVERITY = {'d4-invalid': 'major', 'unsound-accept': 'blocking', 'crash': 'major', 'value-disagreement': 'major',
            'premature-unsupported': 'minor', 'diagnostic-shape': 'minor'}
CONTROL = re.compile(r'[\x00-\x08\x0b-\x1f\x7f]')


def sha(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8', 'surrogatepass')).hexdigest()


TOOL_REGISTRY = Path(__file__).resolve().parents[3] / 'tests/prechecks/registry/lang.jsonl'


def load_registry(ctx) -> list[dict]:
    """Registry rows (frozen at harvest): the tool's own file, so a historical head is replayed against the same
    corpus, plus any rows the checked tree carries. `options['registry'] = 'none'` uses the tree's rows only."""
    texts = []
    if ctx.options.get('registry', 'tool') == 'tool' and TOOL_REGISTRY.is_file():
        texts.append(TOOL_REGISTRY.read_text(encoding='utf-8'))
    texts.append(ctx.head.text('tests/prechecks/registry/lang.jsonl') or '')
    rows, seen = [], set()
    for text in texts:
        for line in text.split('\n'):
            if line.strip():
                row = json.loads(line)
                if 'text' in row and row.get('kind') == 'lang' and row.get('sha256') not in seen:
                    seen.add(row.get('sha256'))
                    rows.append(row)
    return rows


def load_fixtures(ctx) -> list[dict]:
    """Tracked programs whose manifests carry a seed observation: referenced by path, judged by the recorded reference."""
    rows = []
    for manifest in MANIFESTS:
        try:
            data = ctx.head.json(manifest)
        except ValueError:
            continue
        if not isinstance(data, dict):
            continue
        base = manifest.rsplit('/', 1)[0]
        for case in data.get('cases', []):
            reference = case.get('reference') or {}
            file = case.get('file', '')
            path = file if file.startswith(('tests/', 'src/')) else f'{base}/{file}'
            text = ctx.head.text(path)
            if text is None or 'exit' not in reference or '\n' in path:
                continue
            verdict = {'check': 'accept' if reference['exit'] == 0 else 'reject'}
            if reference['exit'] == 0 and reference.get('value') is not None and oracle_mod.has_main(text):
                verdict.update(run='accept', stdout=str(reference['value']) + '\n')
            rows.append({'family': 'fixture', 'text': text, 'seed': verdict, 'source': path, 'imports': bool(oracle_mod.IMPORT.search(text))})
    return rows


def materialize(programs: dict[str, tuple], directory: Path) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = {}
    for digest, (_family, _key, text, _verdict) in programs.items():
        path = directory / digest[:2] / f'{digest[:16]}.bend'
        if not path.exists():
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(text.encode('utf-8', 'surrogatepass'))
        paths[digest] = path
    return paths


def value_of(outcome: Outcome) -> str | None:
    if outcome.kind != 'Checked' or not outcome.stdout.startswith('Evaluated'):
        return None
    return outcome.stdout.rstrip('\n').split('\t')[-1].strip()


def violations(text: str, verdicts: dict, outcomes: dict) -> dict[tuple, dict]:
    """{(lane, rule): detail} for one program at one tree."""
    found: dict[tuple, dict] = {}
    parse, check, run = verdicts.get('parse'), verdicts.get('check'), verdicts.get('run')

    def flag(lane, rule, **detail):
        found[(lane, rule)] = detail

    for lane in ('parse', 'check', 'eval'):
        outcome = outcomes.get(lane)
        if outcome is None:
            continue
        if outcome.kind in ('crash', 'timeout', 'HostFailure', 'InternalFailure') and outcome.line != 'lane unavailable':
            flag(lane, 'crash', outcome=f'{outcome.kind} exit {outcome.exit}', line=outcome.line)
        if outcome.kind != 'Checked' and outcome.exit in (2, 3, 4, 5, 6):
            if not SHAPE.match(outcome.line) or CONTROL.search(outcome.line) or outcome.line.endswith('\t0:0:0:0'):
                flag(lane, 'diagnostic-shape', line=outcome.line[:80])
    p = outcomes.get('parse')
    if p is not None and parse is not None and parse.get('ok') is not None:
        if parse['ok'] and p.kind == 'Invalid':
            flag('parse', 'd4-invalid', seed='parse ok', knot=p.line)
        elif not parse['ok'] and p.kind == 'Checked':
            flag('parse', 'unsound-accept', seed=f"parse rejects at {parse.get('beg')}", knot='Parsed')
        elif not parse['ok'] and p.kind == 'Unsupported' and p.begin is not None and parse.get('beg') is not None and p.begin < parse['beg']:
            flag('parse', 'premature-unsupported', seed_offset=parse['beg'], knot=p.line)
    c = outcomes.get('check')
    if c is not None and check is not None and check.get('verdict') in ('accept', 'reject'):
        if check['verdict'] == 'accept' and c.kind == 'Invalid':
            flag('check', 'd4-invalid', seed='check accepts', knot=c.line)
        elif check['verdict'] == 'reject' and c.kind == 'Checked':
            flag('check', 'unsound-accept', seed='check rejects', knot='Checked')
    e = outcomes.get('eval')
    if e is not None and check is not None:
        if check.get('verdict') == 'reject' and e.kind == 'Checked' and e.stdout.startswith('Evaluated'):
            flag('eval', 'unsound-accept', seed='check rejects', knot='Evaluated')
        elif run is not None and run.get('verdict') == 'accept' and e.kind == 'Checked':
            want, got = (run.get('stdout') or '').strip(), value_of(e)
            if got is not None and want != got:
                flag('eval', 'value-disagreement', seed=want[:60], knot=got[:60])
    return found


def outcome_table(lanes: Lanes, programs: dict, paths: dict[str, Path], have_main: dict, cache_file: Path, jobs: int) -> dict:
    """{sha: {lane: Outcome}} for every program, reusing outcomes cached by (tree, lane, program)."""
    cached = {}
    if cache_file.is_file():
        try:
            cached = {k: {lane: Outcome.from_json(v) for lane, v in row.items()} for k, row in json.loads(cache_file.read_text()).items()}
        except ValueError:
            cached = {}
    todo = []
    for digest in programs:
        wanted = ['parse', 'check'] + (['eval'] if have_main[digest] else [])
        missing = [lane for lane in wanted if lane not in cached.get(digest, {})]
        if missing:
            todo.append((digest, missing))

    def work(item):
        digest, missing = item
        row = {}
        for lane in missing:
            args = ('main', '65536') if lane == 'eval' else ()
            row[lane] = lanes.run(lane, paths[digest], *args)
        return digest, row

    with ThreadPoolExecutor(max_workers=jobs * 2) as pool:
        for digest, row in pool.map(work, todo):
            cached.setdefault(digest, {}).update(row)
    if todo:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps({k: {lane: o.to_json() for lane, o in row.items()} for k, row in cached.items()}))
    return cached


def run(ctx) -> CheckResult:
    started = time.monotonic()
    result = CheckResult()
    if ctx.base is None:
        return not_applicable('no base to ratchet against')
    if not ctx.head.has('src/parse-cli.bend') or not ctx.head.has('src/check-cli.bend'):
        return not_applicable('the tree has no src/parse-cli.bend and src/check-cli.bend')
    seed = Seed(ctx.root, ctx.scratch / 'seed-run')
    if not seed.available():
        return unavailable('the pinned seed (.toolchain/bend-2.0.29-574b6d3) is not installed')
    if shutil.which('bun') is None:
        return unavailable('bun is not on PATH')
    if ctx.head.has('vm/evaluate.py'):
        result.rules_unavailable['family-v'] = 'family V (VM image lanes) is not implemented in this build'
    result.rules_unavailable['helper-divergence'] = 'no helper lanes are declared (lanes.helpers)'

    # ---- corpus -------------------------------------------------------------------------
    corpus: dict[str, tuple] = {}
    changed_sources = [p for p in ctx.changed_paths() if p.startswith('src/') and p.endswith('.bend')]
    for row in load_registry(ctx):
        corpus.setdefault(sha(row['text']), (row['family'], row['source'].get('cited', row['sha256'][:8]), row['text'], row.get('seed')))
    for row in load_fixtures(ctx):
        corpus.setdefault(sha(row['text']), (row['family'], row['source'], row['text'], row['seed']))
    slow = ctx.tier == 'slow'
    limit = int(ctx.options.get('c1_limit', 5000 if slow else LIMIT))
    cold = not (ctx.scratch / 'cache' / 'lanes' / ctx.base.treeish / 'check.js').is_file()
    if cold and not slow:
        limit = min(limit, COLD_LIMIT)
    rng_seed = int((ctx.head_commit or ctx.head.treeish)[:8], 16)
    fixed = list(corpus.items())
    generated = generate.grid_programs(generate.quotas(max(limit - len(fixed), 100) * 2 // 3, changed_sources), rng_seed)
    rng = random.Random(rng_seed)
    accepted_bases = [(digest, text) for digest, (_f, _k, text, verdict) in fixed
                      if verdict and verdict.get('parse') != 'reject' and verdict.get('check') != 'reject']
    operators = []
    for digest, text in accepted_bases:
        if len(text) > 4000:
            continue
        operators += list(generate.gap_variants(text, 3, rng)) + list(generate.literal_variants(text, 1, rng)) + list(generate.layout_variants(text))[:1]
    extras = generate.sample(operators, max(limit - len(fixed) - len(generated), 0), rng_seed + 1)
    for family, key, text in generated + extras:
        corpus.setdefault(sha(text), (family, key, text, None))
    if len(corpus) > limit:
        keep = fixed[:limit] + [(d, corpus[d]) for d in corpus if d not in {x for x, _ in fixed}]
        corpus = dict(keep[:limit])
    programs_dir = ctx.scratch / 'programs'
    paths = materialize(corpus, programs_dir)

    # ---- oracle -------------------------------------------------------------------------------
    oracle = oracle_mod.Oracle(seed, ctx.scratch / 'seed-cache', budget=3000 if slow else 200)
    for digest, (_f, _k, _t, verdict) in corpus.items():
        oracle.prefill(digest, verdict)
    plain = {d: paths[d] for d, (_f, _k, text, _v) in corpus.items() if not oracle_mod.IMPORT.search(text)}
    parse_verdicts = oracle.parse(plain)
    verdicts: dict[str, dict] = {}
    for digest, (_f, _k, text, _v) in corpus.items():
        row = {'parse': parse_verdicts.get(digest)}
        parse_ok = row['parse'] is None or row['parse'].get('ok')
        if parse_ok:
            row['check'] = oracle.check(digest, paths[digest])
            if row['check'] and row['check'].get('verdict') == 'accept' and oracle_mod.has_main(text):
                row['run'] = oracle.run(digest, paths[digest])
        elif row['parse'] is not None:
            row['check'] = {'verdict': 'reject'}
        verdicts[digest] = row
    have_main = {d: bool((verdicts[d].get('check') or {}).get('verdict') == 'accept' and oracle_mod.has_main(corpus[d][2]))
                 for d in corpus}

    # ---- lanes at head and at the base -----------------------------------------------------------------
    head_lanes = Lanes(ctx, ctx.head, 'head', programs_dir)
    base_lanes = Lanes(ctx, ctx.base, 'base', programs_dir)
    same_tree = ctx.base.treeish == ctx.head.treeish
    for lanes in ([head_lanes] if same_tree else [head_lanes, base_lanes]):
        lanes.build()
        if lanes.errors:
            result.rules_unavailable[f'lanes:{lanes.label}'] = '; '.join(f'{k}: {v}' for k, v in lanes.errors.items())
    if head_lanes.errors.get('parse') or head_lanes.errors.get('check'):
        return unavailable('head lanes did not build: ' + '; '.join(f'{k}: {v}' for k, v in head_lanes.errors.items()))
    head_table = outcome_table(head_lanes, corpus, paths, have_main, ctx.scratch / 'cache' / f'outcomes-{ctx.head.treeish}.json', ctx.jobs)
    if same_tree:
        base_table = head_table
    else:
        if base_lanes.errors.get('parse') or base_lanes.errors.get('check'):
            result.rules_unavailable['ratchet'] = 'base lanes did not build; every violation is reported as new'
            base_table = {}
        else:
            base_table = outcome_table(base_lanes, corpus, paths, have_main, ctx.scratch / 'cache' / f'outcomes-{ctx.base.treeish}.json', ctx.jobs)

    # ---- rules and the ratchet -----------------------------------------------------------------------------
    targets = set(ctx.manifest.d4_targets())
    counts = {'programs': len(corpus), 'new': 0, 'known': 0}
    gaps = []
    per_bucket: dict[tuple, int] = {}
    for digest, (family, key, text, _v) in sorted(corpus.items()):
        now = violations(text, verdicts[digest], {k: v for k, v in head_table.get(digest, {}).items()})
        before = violations(text, verdicts[digest], {k: v for k, v in base_table.get(digest, {}).items()}) if base_table else {}
        for (lane, rule), detail in sorted(now.items()):
            if (lane, rule) in before:
                counts['known'] += 1
                if rule == 'd4-invalid':
                    gaps.append({'program': digest[:16], 'family': family, 'lane': lane, 'key': key})
                if family in targets and rule in ('d4-invalid', 'unsound-accept', 'value-disagreement'):
                    result.conditions.append(Condition(
                        ID, 'incomplete-repair', 'major', {'probe': digest[:16], 'lane': lane, 'rule': rule},
                        expected=f'the family {family} is repaired (the manifest lists it in d4_targets)',
                        observed=f'{rule} still holds at base and head: {key}', evidence={'program': text[:240], **detail}))
                continue
            counts['new'] += 1
            bucket = (rule, lane)
            per_bucket[bucket] = per_bucket.get(bucket, 0) + 1
            if per_bucket[bucket] > MAX_CONDITIONS:
                continue
            severity = SEVERITY[rule]
            regressed = bool(base_table)                 # every program is judged at both trees: a new violation is a regression
            if regressed and rule not in ('diagnostic-shape', 'premature-unsupported'):
                severity = raised(severity)
            result.conditions.append(Condition(
                ID, rule, severity, {'probe': digest[:16], 'lane': lane},
                expected={'d4-invalid': 'a seed-accepted form is Parsed, Checked or Unsupported, never Invalid',
                          'unsound-accept': 'a seed-rejected form is never accepted or evaluated',
                          'crash': 'every lane ends in one of the five classified outcomes',
                          'value-disagreement': 'eval agrees with the seed on every accepted main program',
                          'premature-unsupported': 'Unsupported starts at or after the seed\'s parse error',
                          'diagnostic-shape': 'a diagnostic is Class<TAB>phase<TAB>code<TAB>span'}[rule],
                observed=f'{family} {key!r}: ' + ', '.join(f'{k}={v}' for k, v in detail.items()),
                value={'family': family}, evidence={'program': text[:240], 'sha256': digest, **detail},
                fix_hint='The probe is frozen in tests/prechecks/registry when it came from review; replay it with the CLI lane.'))
    for bucket, n in per_bucket.items():
        if n > MAX_CONDITIONS:
            counts.setdefault('elided', {})[f'{bucket[0]}/{bucket[1]}'] = n - MAX_CONDITIONS
    result.rules_run = ['d4-invalid', 'unsound-accept', 'crash', 'value-disagreement', 'premature-unsupported', 'diagnostic-shape',
                        'incomplete-repair']
    if oracle.skipped:
        result.rules_unavailable['seed-budget'] = f'{oracle.skipped} check-level verdict(s) exceed the {oracle.budget}-run cap; the slow tier completes them'
    result.facts = {'counts': counts, 'd4_gaps': gaps[:200], 'd4_gap_count': len(gaps), 'seed_runs': oracle.used,
                    'cold_base_cache': cold, 'seconds': round(time.monotonic() - started, 1), 'seed_revision': SEED_REVISION}
    return result


CHECK = Check(ID, 'probe-differential', "the pinned seed against Knot's parse, check and eval lanes on a frozen corpus", run, budget=45)
