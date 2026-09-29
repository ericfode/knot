"""C1 probe-differential: every reviewer probe becomes a permanent control, replayed through Knot's own lanes.

A frozen, content-addressed corpus (the harvested registry, tracked fixtures that carry seed observations, and a
fixed sample of generated programs) is judged by the pinned seed, then run through Knot's parse, check and eval
CLIs built from head and from the effective base. Violations are ratcheted against the base: only a violation that
head adds is a condition, and a base-acceptable verdict that turns into a violation is raised one severity step.
A violation present at both is a known gap of the D4 ledger (reported as a fact, and as R7 when the increment
promised to repair its family).

The fast tier judges the same programs on every head, base and host: the sample is a function of constants and of
the tool's registry only, the seed's check and run verdicts on it are frozen in the repository, and lane builds and
outcome caches are keyed by the `src` subtree, so a rerun, a documentation-only commit and a cold cache all give the
same conditions. A program without a frozen verdict is counted and reported, never silently dropped.

  R1 d4-invalid          the seed accepts, a Knot lane says Invalid
  R2 unsound-accept      the seed rejects, a Knot lane says Checked or produces a value
  R3 crash               a lane exits 5, 6, 1, or anything unclassified, or times out
  R4 value-disagreement  eval stdout differs from the seed's value on an accepted `main` program
  R5 premature-unsupported   the seed rejects the program and a lane reports Unsupported for it although nothing valid
                         was recognized: the Unsupported span begins exactly at the seed's error offset (the recognized
                         token is the rejected token itself), or a registry probe that must stay Invalid (`expect`) is not.
                         A recognized valid prefix that the seed rejects only later (span before the seed's error) is
                         D4's documented prefix-only policy: no condition when the tree's src/SPEC.md table lists its code
                         (counted as a fact), a minor condition that the ratchet does not raise when it does not.
  R6 diagnostic-shape    a non-Checked line is not `Class<TAB>phase<TAB>code<TAB>span`, or has a control character
  R7 incomplete-repair   a violation that exists at base, in a family the manifest lists in d4_targets
  lane-build             a lane's src/*-cli.bend builds at base and not at head

  R11 reference-crash    (family V) the tree's reference codec raises an undeclared exception on a plan
  R12 roundtrip          (family V) decode(encode(golden)) != golden

R9/R10 (reference against the VM lanes) and R8 (helper lanes) need the VM binary and declared helpers; they report unavailable.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from lib import generate, oracle as oracle_mod
from lib.lanes import SHAPE, Lanes, Outcome
from lib.model import CheckResult, Condition, not_applicable, raised, unavailable
from lib.runner import Check
from lib.seed import SEED_REVISION, Seed

ID = 'C1'
SLOW_LIMIT = 5000             # programs in the slow tier (its sample follows the changed sources; the fast tier's is fixed)
MAX_CONDITIONS = 60           # conditions per (rule, lane); the rest are counted in the fact table
MANIFESTS = ('tests/subsets/classification-cases.json', 'tests/subsets/frontend-cases.json', 'tests/compiler-checker/cases.json')
SEVERITY = {'d4-invalid': 'major', 'unsound-accept': 'blocking', 'crash': 'major', 'value-disagreement': 'major',
            'premature-unsupported': 'minor', 'diagnostic-shape': 'minor'}
CONTROL = re.compile(r'[\x00-\x08\x0b-\x1f\x7f]')
# A row of the SPEC's prefix-only table: | Recognized form | `parse` | `code` |
PREFIX_ROW = re.compile(r'^\|[^\n]*?\|\s*`(?:parse|lex|check)`\s*\|\s*`([a-z0-9-]+)`\s*\|\s*$', re.M)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8', 'surrogatepass')).hexdigest()


TOOL_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = 'tests/prechecks/registry/lang.jsonl'
TOOL_REGISTRY = TOOL_ROOT / REGISTRY_PATH
TOOL_VERDICTS = TOOL_ROOT / 'tests/prechecks/registry/seed-verdicts.jsonl'
TOOL_VM_REGISTRY = TOOL_ROOT / 'tests/prechecks/registry/vm.jsonl'


def read_rows(text: str) -> list[dict]:
    rows = []
    for line in text.split('\n'):
        if line.strip():
            row = json.loads(line)
            if 'text' in row and row.get('kind') == 'lang':
                rows.append(row)
    return rows


def tool_rows() -> list[dict]:
    """The tool's own registry rows (frozen at harvest): a historical head is replayed against the same corpus."""
    return read_rows(TOOL_REGISTRY.read_text(encoding='utf-8')) if TOOL_REGISTRY.is_file() else []


def load_registry(ctx) -> list[dict]:
    """The tool's rows, plus any rows the checked tree carries. `options['registry'] = 'none'` uses the tree's rows only."""
    sources = ([tool_rows()] if ctx.options.get('registry', 'tool') == 'tool' else []) + [read_rows(ctx.head.text(REGISTRY_PATH) or '')]
    rows, seen = [], set()
    for source in sources:
        for row in source:
            if row.get('sha256') not in seen:
                seen.add(row.get('sha256'))
                rows.append(row)
    return rows


def load_frozen() -> dict[str, dict]:
    """{sha256: seed verdict} of the generated programs, frozen by scripts/prechecks/freeze.py against the pinned seed."""
    frozen = {}
    if TOOL_VERDICTS.is_file():
        for line in TOOL_VERDICTS.read_text(encoding='utf-8').split('\n'):
            if line.strip():
                row = json.loads(line)
                if row.get('seed_revision') == SEED_REVISION:
                    frozen[row['sha256']] = row['seed']
    return frozen


def row_verdict(row: dict) -> dict | None:
    """The row's pinned seed verdict, plus what a lane must still say (`expect`: {lane: category}) when a reviewer froze it."""
    verdict = dict(row.get('seed') or {})
    if row.get('expect'):
        verdict['expect'] = row['expect']
    return verdict or None


def prefix_codes(tree) -> frozenset:
    """The codes of the prefix-only table in the tree's src/SPEC.md: forms that Knot recognizes by a prefix, reports
    Unsupported and does not validate any further. Empty when the SPEC has no such table."""
    text = tree.text('src/SPEC.md') or ''
    if not re.search(r'stops at that prefix', text):
        return frozenset()
    return frozenset(PREFIX_ROW.findall(text))


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


def accepted_by_seed(verdict: dict | None) -> bool:
    return bool(verdict) and verdict.get('parse') != 'reject' and verdict.get('check') != 'reject'


def build_corpus(registry: list[dict], generated_from: list[dict], fixtures: list[dict], *, slow: bool = False,
                 changed_sources: list[str] = (), generated_limit: int | None = None) -> dict[str, tuple]:
    """{sha: (family, key, text, seed verdict)}.

    The fast corpus is the registry rows, the tree's fixtures and `generate.fixed_programs` of the tool's registry rows
    (`generated_from`): a function of constants and of the tool's own files, apart from the tree's own fixtures. The slow
    corpus is larger and follows the changed sources, with the same fixed seed.
    """
    corpus: dict[str, tuple] = {}
    for row in registry:
        corpus.setdefault(sha(row['text']), (row['family'], row['source'].get('cited', row['sha256'][:8]), row['text'], row_verdict(row)))
    for row in fixtures:
        corpus.setdefault(sha(row['text']), (row['family'], row['source'], row['text'], row['seed']))
    if not slow:
        extra = generate.fixed_programs([row['text'] for row in generated_from if accepted_by_seed(row_verdict(row))])
    else:
        fixed = list(corpus.items())
        generated = generate.grid_programs(generate.quotas(max(SLOW_LIMIT - len(fixed), 100) * 2 // 3, changed_sources), generate.FIXED_SEED)
        rng = random.Random(generate.FIXED_SEED)
        operators = []
        for _digest, (_f, _k, text, verdict) in fixed:
            if len(text) > 4000 or not accepted_by_seed(verdict):
                continue
            operators += list(generate.gap_variants(text, 3, rng)) + list(generate.literal_variants(text, 1, rng)) \
                + list(generate.layout_variants(text))[:1]
        extra = generated + generate.sample(operators, max(SLOW_LIMIT - len(fixed) - len(generated), 0), generate.FIXED_SEED + 1)
    for family, key, text in extra[:generated_limit]:
        corpus.setdefault(sha(text), (family, key, text, None))
    return corpus


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


def premature(text: str, parse: dict, p: Outcome, documented: frozenset) -> dict | None:
    """R5 for a seed-rejected program that the parse lane calls Unsupported: the detail of the violation, or None.

    Unsupported is D4's answer for a form Knot cannot check yet, and a recognizer may stop at a valid prefix and leave
    the rest unvalidated (the SPEC's prefix-only table): then the seed's error lies after the span, and nothing is wrong.
    When the span begins exactly where the seed's error is, the token Knot recognized is the token the seed rejects: no
    valid form was recognized, and the program should have stayed Invalid (the classify reviewers' criterion: the seed's
    error is at the recognized prefix token itself). A span that begins after the seed's error is not judged: the seed
    backtracks to the end of the last production it finished (`'def', 'type' or 'law'`) and reports there, so its offset
    then says nothing about the token Knot recognized further on. The offsets are comparable only in ASCII text (the seed
    counts UTF-16 units, Knot bytes), so any other program is never judged by them.
    """
    beg, begin = parse.get('beg'), p.begin
    if beg is None or begin is None or not text.isascii():
        return None
    if begin == beg:
        return {'seed_offset': beg, 'knot': p.line, 'at': "the seed's error token"}
    if begin < beg and p.code not in documented:
        return {'seed_offset': beg, 'knot': p.line, 'at': 'a prefix that the SPEC does not list', 'raise': False}
    return None


def violations(text: str, verdicts: dict, outcomes: dict, documented: frozenset = frozenset()) -> dict[tuple, dict]:
    """{(lane, rule): detail} for one program at one tree. `documented` is the tree's SPEC prefix-only code set."""
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
        elif not parse['ok'] and p.kind == 'Unsupported':
            detail = premature(text, parse, p, documented)
            if detail:
                flag('parse', 'premature-unsupported', **detail)
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
    # A reviewer froze what a lane must say about this probe. The seed's verdict is binary, so it cannot tell Invalid from
    # Unsupported; this can, and it does not depend on where the offsets of the two parsers happen to fall.
    for lane, wanted in (verdicts.get('expect') or {}).items():
        outcome = outcomes.get(lane)
        if outcome is None or outcome.kind == wanted:
            continue
        if wanted == 'Invalid' and outcome.kind == 'Unsupported':
            flag(lane, 'premature-unsupported', expected='Invalid', knot=outcome.line, at='a probe frozen as malformed')
        elif wanted == 'Invalid' and outcome.kind == 'Checked':
            flag(lane, 'unsound-accept', expected='Invalid', knot='Checked')
        elif wanted == 'Unsupported' and outcome.kind == 'Invalid':
            flag(lane, 'd4-invalid', expected='Unsupported', knot=outcome.line)
    return found


def outcome_table(lanes: Lanes, programs: dict, paths: dict[str, Path], have_main: dict, cache_file: Path, jobs: int) -> dict:
    """{sha: {lane: Outcome}} for every program, reusing outcomes cached by (src subtree, lane, program)."""
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
            row[lane] = lanes.run(lane, paths[digest], *args)        # raises Cancelled once the hang guard gave up
        return digest, row

    with ThreadPoolExecutor(max_workers=jobs * 2) as pool:
        try:
            for digest, row in pool.map(work, todo):
                cached.setdefault(digest, {}).update(row)
        except BaseException:
            pool.shutdown(wait=False, cancel_futures=True)
            raise
    if todo:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps({k: {lane: o.to_json() for lane, o in row.items()} for k, row in cached.items()}))
    return cached


def family_v(ctx, result: CheckResult) -> None:
    """R11 reference-crash and R12 roundtrip over the VM plans: the goldens (strict) and the harvested reviewer plans.

    The tree's own `vm/serializer.py` is exercised in a child process at head and at the base; a crash or a
    roundtrip failure that only head has is a condition. R9 and R10 (lane divergence) need the VM binary and its
    machine-readable divergence table and are not implemented here.
    """
    if not ctx.head.has('vm/serializer.py') or not ctx.head.has('vm/registry.json'):
        return
    plans = []
    for path in ctx.head.glob('vm/golden/*.plan.json'):
        try:
            plans.append({'name': path, 'plan': json.loads(ctx.head.text(path) or 'null'), 'strict': True})
        except ValueError:
            continue
    if ctx.options.get('registry', 'tool') == 'tool' and TOOL_VM_REGISTRY.is_file():
        for line in TOOL_VM_REGISTRY.read_text(encoding='utf-8').split('\n'):
            if line.strip():
                row = json.loads(line)
                try:
                    plans.append({'name': 'registry:' + row['source'].get('cited', row['sha256'][:8]), 'plan': json.loads(row['text']), 'strict': False})
                except (ValueError, KeyError):
                    continue
    directory = ctx.scratch / 'family-v'
    directory.mkdir(parents=True, exist_ok=True)
    plan_file = directory / 'plans.json'
    plan_file.write_text(json.dumps(plans))

    def probe(tree, label):
        out = directory / f'{tree.treeish}.json'
        if out.is_file():
            return json.loads(out.read_text())
        export = ctx.export(tree)
        code, _o, err = ctx.run([sys.executable, '-B', str(Path(__file__).resolve().parents[1] / 'lib/codecprobe.py'), export, plan_file, out],
                                timeout=120)
        if code != 0 or not out.is_file():
            raise RuntimeError(f'{label} codec probe failed: {(err or b"").decode("utf-8", "replace").strip()[-160:]}')
        return json.loads(out.read_text())

    try:
        head = probe(ctx.head, 'head')
    except RuntimeError as error:
        result.rules_unavailable['family-v'] = str(error)
        return
    try:
        base = probe(ctx.base, 'base') if ctx.base.has('vm/serializer.py') and ctx.base.treeish != ctx.head.treeish else (head if ctx.base.treeish == ctx.head.treeish else {})
    except RuntimeError:
        base = {}
    known = 0
    # A golden that this branch added or edited has no verdict at base: the branch's own artifact is judged as new.
    fresh = {p['name'] for p in plans if p['strict'] and (not ctx.base.has(p['name']) or ctx.base.sha(p['name']) != ctx.head.sha(p['name']))}
    for name, row in sorted(head.items()):
        if row['kind'] in ('ok', 'declared'):
            continue
        rule = 'reference-crash' if row['kind'] == 'crash' else 'roundtrip'
        if name not in fresh and base.get(name, {}).get('kind') == row['kind']:
            known += 1
            continue
        result.conditions.append(Condition(
            ID, rule, 'major', {'probe': hashlib.sha256(name.encode()).hexdigest()[:16], 'lane': 'reference-codec'},
            expected='the reference codec refuses a bad plan with a declared error and round-trips every golden',
            observed=f"{name}: {row['stage']}: {row['error']}", value={'family': 'vm-plan'}, evidence={'plan': name, **row},
            fix_hint='A crash of the reference is a defect of the oracle every VM lane is judged against.'))
    result.rules_run += ['reference-crash', 'roundtrip']
    result.facts['family_v'] = {'plans': len(plans), 'known': known}


def lane_build_conditions(head_lanes: Lanes, base_lanes: Lanes | None, base_has: dict[str, bool]) -> list[Condition]:
    """A lane whose CLI builds at base and does not build at head: the branch broke a source that every lane needs."""
    found = []
    for name in ('parse', 'check'):
        error = head_lanes.errors.get(name)
        if not error or base_lanes is None or not base_has.get(name) or base_lanes.errors.get(name):
            continue
        found.append(Condition(ID, 'lane-build', 'major', {'lane': name},
                               expected=f'src/{name}-cli.bend builds with the pinned seed, as it does at the base',
                               observed=f'the {name} lane does not build at head: {error}',
                               fix_hint='Fix the source the CLI imports; until it builds, no program is checked at head.'))
    return found


def family_l(ctx) -> CheckResult:
    """Family L: programs, judged by the seed, run through Knot's lanes at head and at the base."""
    started = time.monotonic()
    result = CheckResult()
    slow = ctx.tier == 'slow'
    clis = ('src/parse-cli.bend', 'src/check-cli.bend')
    if not all(ctx.head.has(path) for path in clis):
        if all(ctx.base.has(path) for path in clis):
            result = unavailable('a lane source that exists at the base is missing at head')
            result.conditions.append(Condition(ID, 'lane-build', 'major', {'lane': 'source'},
                                               expected='src/parse-cli.bend and src/check-cli.bend exist, as they do at the base',
                                               observed=', '.join(path for path in clis if not ctx.head.has(path)) + ' is missing at head',
                                               fix_hint='Restore the CLI: every lane is built from it.'))
            return result
        return not_applicable('the tree has no src/parse-cli.bend and src/check-cli.bend')
    seed = Seed(ctx.root, ctx.scratch / 'seed-run', cancel=ctx.cancel)
    if not seed.available():
        return unavailable('the pinned seed (.toolchain/bend-2.0.29-574b6d3) is not installed')
    if shutil.which('bun') is None:
        return unavailable('bun is not on PATH')
    if ctx.head.has('vm/evaluate.py'):
        result.rules_unavailable['vm-lanes'] = 'R9 and R10 (reference against VM lanes) need the VM binary and a divergence table; not implemented'
    result.rules_unavailable['helper-divergence'] = 'no helper lanes are declared (lanes.helpers)'
    targets = set(ctx.manifest.d4_targets())
    if not targets:
        result.rules_unavailable['incomplete-repair'] = 'the manifest declares no d4_targets: nothing was promised to repair'

    # ---- lanes at head and at the base ---------------------------------------------------------------
    programs_dir = ctx.scratch / 'programs'
    head_lanes = Lanes(ctx, ctx.head, 'head', programs_dir)
    base_lanes = Lanes(ctx, ctx.base, 'base', programs_dir)
    same_src = head_lanes.key == base_lanes.key
    cached_base = (base_lanes.cache / 'check.js').is_file()
    for lanes in ([head_lanes] if same_src else [head_lanes, base_lanes]):
        lanes.build()
        if lanes.errors:
            result.rules_unavailable[f'lanes:{lanes.label}'] = '; '.join(f'{k}: {v}' for k, v in lanes.errors.items())
    if head_lanes.errors.get('parse') or head_lanes.errors.get('check'):
        failed = unavailable('head lanes did not build: ' + '; '.join(f'{k}: {v}' for k, v in head_lanes.errors.items()))
        failed.rules_unavailable.update(result.rules_unavailable)
        failed.conditions += [] if same_src else lane_build_conditions(head_lanes, base_lanes, {n: ctx.base.has(p) for n, p in zip(('parse', 'check'), clis)})
        return failed
    result.rules_run.append('lane-build')

    # ---- corpus ------------------------------------------------------------------------------------------
    changed_sources = [p for p in ctx.changed_paths() if p.startswith('src/') and p.endswith('.bend')]
    corpus = build_corpus(load_registry(ctx), tool_rows(), load_fixtures(ctx), slow=slow, changed_sources=changed_sources,
                          generated_limit=ctx.options.get('c1_limit'))
    paths = materialize(corpus, programs_dir)

    # ---- oracle ------------------------------------------------------------------------------------------
    oracle = oracle_mod.Oracle(seed, ctx.scratch / 'seed-cache', budget=3000 if slow else 0, frozen_only=not slow)
    frozen = load_frozen()
    for digest, (_f, _k, _t, verdict) in corpus.items():
        oracle.prefill(digest, verdict)
        oracle.prefill(digest, frozen.get(digest))
    plain = {d: paths[d] for d, (_f, _k, text, _v) in corpus.items() if not oracle_mod.IMPORT.search(text)}
    parse_verdicts = oracle.parse(plain)
    if slow:
        oracle.warm('check', {d: paths[d] for d in corpus if (parse_verdicts.get(d) or {'ok': True}).get('ok')}, jobs=ctx.jobs * 2)
    verdicts: dict[str, dict] = {}
    unjudged = {'imports': 0, 'no-frozen-verdict': 0}
    for digest, (_f, _k, text, verdict) in corpus.items():
        row = {'parse': parse_verdicts.get(digest), 'expect': (verdict or {}).get('expect')}
        parse_ok = row['parse'] is None or row['parse'].get('ok')
        if parse_ok:
            row['check'] = oracle.check(digest, paths[digest])
            if row['check'] is None:
                unjudged['imports' if oracle_mod.IMPORT.search(text) else 'no-frozen-verdict'] += 1
            elif row['check'].get('verdict') == 'accept' and oracle_mod.has_main(text):
                if slow:
                    oracle.warm('run', {digest: paths[digest]}, jobs=1)
                row['run'] = oracle.run(digest, paths[digest])
        elif row['parse'] is not None:
            row['check'] = {'verdict': 'reject'}
        verdicts[digest] = row
    have_main = {d: bool((verdicts[d].get('check') or {}).get('verdict') == 'accept' and oracle_mod.has_main(corpus[d][2]))
                 for d in corpus}

    head_table = outcome_table(head_lanes, corpus, paths, have_main, ctx.scratch / 'cache' / f'outcomes-{head_lanes.key}.json', ctx.jobs)
    if same_src:
        base_table = head_table
    elif base_lanes.errors.get('parse') or base_lanes.errors.get('check'):
        result.rules_unavailable['ratchet'] = 'base lanes did not build; every violation is reported as new'
        base_table = {}
    else:
        base_table = outcome_table(base_lanes, corpus, paths, have_main, ctx.scratch / 'cache' / f'outcomes-{base_lanes.key}.json', ctx.jobs)

    # ---- rules and the ratchet -----------------------------------------------------------------------------
    documented_head, documented_base = prefix_codes(ctx.head), prefix_codes(ctx.base)
    counts = {'programs': len(corpus), 'new': 0, 'known': 0}
    known_by_rule: dict[str, int] = {}
    policy: dict[str, int] = {}
    gaps = []
    per_bucket: dict[tuple, int] = {}
    for digest, (family, key, text, _v) in sorted(corpus.items()):
        now = violations(text, verdicts[digest], head_table.get(digest, {}), documented_head)
        before = violations(text, verdicts[digest], base_table.get(digest, {}), documented_base) if base_table else {}
        seed_parse, head_parse = verdicts[digest].get('parse'), head_table.get(digest, {}).get('parse')
        if seed_parse and seed_parse.get('ok') is False and head_parse is not None and head_parse.kind == 'Unsupported' \
                and head_parse.begin is not None and seed_parse.get('beg') is not None and head_parse.begin < seed_parse['beg'] \
                and head_parse.code in documented_head and text.isascii():          # premature() ruled this a documented prefix
            policy[head_parse.code] = policy.get(head_parse.code, 0) + 1
        # A verdict is acceptable at base unless it broke a D4 rule; how its diagnostic code is spelled (R6) does not make the
        # category wrong, so it does not stop a regression from being raised.
        clean_at_base = {lane for lane in ('parse', 'check', 'eval') if not any(l == lane and r != 'diagnostic-shape' for (l, r) in before)}
        for (lane, rule), detail in sorted(now.items()):
            if (lane, rule) in before:
                counts['known'] += 1
                known_by_rule[rule] = known_by_rule.get(rule, 0) + 1
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
            allow_raise = detail.pop('raise', True)
            # A regression is a verdict that was acceptable at base: the same program and lane had no violation there. A lane
            # that was already wrong at base and is wrong in another way now is a change, not a regression.
            if base_table and lane in clean_at_base and allow_raise:
                severity = raised(severity)
            result.conditions.append(Condition(
                ID, rule, severity, {'probe': digest[:16], 'lane': lane},
                expected={'d4-invalid': 'a seed-accepted form is Parsed, Checked or Unsupported, never Invalid',
                          'unsound-accept': 'a seed-rejected form is never accepted or evaluated',
                          'crash': 'every lane ends in one of the five classified outcomes',
                          'value-disagreement': 'eval agrees with the seed on every accepted main program',
                          'premature-unsupported': 'a program the seed rejects at the recognized token stays Invalid; '
                                                   'a recognized valid prefix is listed in the SPEC prefix-only table',
                          'diagnostic-shape': 'a diagnostic is Class<TAB>phase<TAB>code<TAB>span'}[rule],
                observed=f'{family} {key!r}: ' + ', '.join(f'{k}={v}' for k, v in detail.items()),
                value={'family': family}, evidence={'program': text[:240], 'sha256': digest, **detail},
                fix_hint='The probe is frozen in tests/prechecks/registry when it came from review; replay it with the CLI lane.'))
    for bucket, n in per_bucket.items():
        if n > MAX_CONDITIONS:
            counts.setdefault('elided', {})[f'{bucket[0]}/{bucket[1]}'] = n - MAX_CONDITIONS
    result.rules_run += ['d4-invalid', 'unsound-accept', 'crash', 'value-disagreement', 'premature-unsupported', 'diagnostic-shape']
    if targets:
        result.rules_run.append('incomplete-repair')
    if unjudged['no-frozen-verdict']:
        result.rules_unavailable['seed-verdicts'] = (f"{unjudged['no-frozen-verdict']} program(s) have no frozen seed verdict, so their check-level "
                                                     'rules did not run; python3 scripts/prechecks/freeze.py freezes them, and the slow tier judges them live')
    if oracle.skipped:
        result.rules_unavailable['seed-budget'] = f'{oracle.skipped} check-level verdict(s) exceed the {oracle.budget}-run cap of the slow tier'
    result.facts = {'counts': counts, 'known_by_rule': dict(sorted(known_by_rule.items())), 'd4_gaps': gaps[:200], 'd4_gap_count': len(gaps),
                    'prefix_policy': dict(sorted(policy.items())), 'unjudged': unjudged, 'spec_prefix_codes': sorted(documented_head),
                    'seed_runs': oracle.used, 'base_lanes_cached': cached_base, 'src_tree': head_lanes.key,
                    'seconds': round(time.monotonic() - started, 1), 'seed_revision': SEED_REVISION}
    return result


def run(ctx) -> CheckResult:
    if ctx.base is None:
        return not_applicable('no base to ratchet against')
    result = family_l(ctx)
    if result.outcome in ('not-applicable', 'unavailable'):
        # Family L cannot run here; family V may still. The gap is never turned into a pass: a family L that is
        # unavailable stays a named unavailable rule beside whatever family V finds, and alone it stays `unavailable`.
        gap, reason = result.outcome, result.reason
        merged = CheckResult(conditions=list(result.conditions), rules_unavailable=dict(result.rules_unavailable))
        merged.notes.append(f'family L {gap}: {reason}')
        if gap == 'unavailable':
            merged.rules_unavailable['family-l'] = reason
        family_v(ctx, merged)
        if not merged.rules_run and not merged.conditions and 'family-v' not in merged.rules_unavailable:
            return not_applicable(reason) if gap == 'not-applicable' else unavailable(reason)
        return merged
    family_v(ctx, result)
    return result


CHECK = Check(ID, 'probe-differential', "the pinned seed against Knot's parse, check and eval lanes on a frozen corpus", run, budget=45)
