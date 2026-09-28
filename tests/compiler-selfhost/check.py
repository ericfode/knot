#!/usr/bin/env python3
"""Self-hosting joint gate: the seed's two lanes, then Knot, aware of blocked cases.

    python3 tests/compiler-selfhost/check.py              run everything, write the receipt
    python3 tests/compiler-selfhost/check.py --judge P    apply the verdict to receipt P

Host only: it builds with the pinned seed, invokes Knot's CLIs and compares
their records with the frozen seed observations. It implements no parser,
checker or evaluator.

1. `regen.py` recomputes every seed observation on the interpreter and the
   native lane; any difference from `expectations.json` fails the gate.
2. The seed builds Knot's `check-cli` and `eval-cli` on the native lane (C1's lane).
3. Each case is `blocked` while a need it names is unavailable in the reviewed
   `needs` table. Knot still runs on it, and the receipt records the outcome as
   first-blocker evidence, but a blocked case never counts as passing.
4. A missing need excuses an unfinished result, never a wrong one. Even while
   blocked, a case fails on a fault: a host or internal failure, a signal, an
   unclassified exit or a timeout; any phase accepting a seed-rejected twin; or
   a seed-valid call that succeeds with other than the seed's constructor and
   tag, or a call list other than the frozen one. Invalid, Unsupported and
   Exhausted may block.
5. A seed-valid case that Knot reports Invalid is a D4 gap. A gap is excused
   only by a reviewed row of `D4_GAPS` for a need that still blocks the case:
   one of the row's codes, spanning one line break of the entry file.
6. An unblocked case must meet its requirement: `agree` checks the book and
   evaluates every frozen call to the seed's constructor and tag; `reject` and
   `unsupported` report the pinned exit, phase and code (and position, where
   pinned) from every phase that runs.
7. The judge rederives every recorded verdict, then is applied to mutated
   copies, each of which it must reject for the named reason, and to restated
   controls, each of which it must accept. Type-correct mutants of `src/` must
   be killed by an unblocked case with a classified, non-crashing observation.
"""
from __future__ import annotations

import argparse
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import regen  # noqa: E402  (the seed lane; shares the expectation schema)

SEED = regen.SEED
# The modules host query makes the seed name its five foreign-dependent CLI
# definitions; a mutant CLI must report exactly that frozen set.
HOST_CHECKS = json.loads((ROOT / 'tests/compiler-modules/host-check-expectations.json').read_text())['entries']
BUILD = '.local/compiler-selfhost/knot'
RECEIPT = HERE / 'receipts/selfhost.json'
EXPECTATIONS = HERE / 'expectations.json'
SCALE = float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))
SECONDS = {'build': 600 * SCALE, 'call': 120 * SCALE}
OUTCOMES = {0: 'Success', 2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted', 5: 'HostFailure', 6: 'InternalFailure'}
CLASSIFIED = ('Success', 'Invalid', 'Unsupported', 'Exhausted')
JOBS = int(os.environ.get('KNOT_SELFHOST_JOBS', '6'))

# Knot's lanes for this suite. Route-independent: the evaluator is the reference
# every backend and the VM are compared with. Multi-module cases run in the
# CLIs' single-file mode until `modules` lands; that increment adds its
# bundle argument here when it flips the need.
KNOT_PHASES = ('check', 'eval')

# Reviewed D4 gaps, keyed by the missing need they belong to: Invalid where D4
# requires Unsupported. The layout gap predates this suite (SELF-HOSTING-PATH.md,
# SF-01 and SF-02): Knot's parser reads a continuation line break inside a
# delimiter or a def header as the end of the term or parameter list, and its
# diagnostic spans exactly that line break. A seed-valid case still blocked by
# the need may report it; one whose other blockers land later surfaces the same
# gap (`layout-lambda-statements` once closures parses its arrow-typed
# parameter). Any other Invalid on a seed-valid case fails the gate. The table
# is literal review of Knot's output, so it lives here, not in the seed-derived
# expectations. When the need lands the excuse ends; the receipt lists the row
# under `d4_gaps_closed` until the owner deletes it.
D4_GAPS = {  # need: (owner, diagnostic prefixes)
    'layout': ('selfsource', ('Invalid\tparse\texpected-term\t', 'Invalid\tparse\tparameter\t')),
}


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(argv, timeout):
    argv = [str(a) for a in argv]
    try:
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=timeout, stdin=subprocess.DEVNULL,
                           env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
        return {'argv': argv, 'exit': p.returncode,
                'stdout': p.stdout.decode('utf-8', 'backslashreplace'),
                'stderr': p.stderr.decode('utf-8', 'backslashreplace')}
    except subprocess.TimeoutExpired:
        return {'argv': argv, 'exit': None, 'stdout': '', 'stderr': '', 'timeout_seconds': timeout}


# ------------------------------------------------------------------ classification

def classify(obs) -> str:
    """Knot's outcome from its exit status and the first stderr field; both must agree."""
    code = obs.get('exit')
    if code is None:
        return 'Timeout'
    kind = OUTCOMES.get(code)
    if kind is None:
        return 'Crash'
    if kind == 'Success':
        return kind if obs['stderr'] == '' else 'Crash'
    first = obs['stderr'].split('\n', 1)[0]
    return kind if first.split('\t', 1)[0] == kind else 'Crash'


def diagnostic(obs) -> str:
    return obs['stderr'].split('\n', 1)[0]


def position(obs) -> str | None:
    """`line:column` of a Knot diagnostic `Kind<TAB>phase<TAB>code<TAB>start:end:line:col`."""
    fields = diagnostic(obs).split('\t')
    parts = fields[3].split(':') if len(fields) > 3 else []
    return f'{parts[2]}:{parts[3]}' if len(parts) == 4 else None


def evaluated(obs):
    """`Evaluated<TAB>type-id<TAB>tag<TAB>Name{}` from a successful nullary result."""
    match = re.fullmatch(r'Evaluated\t(\d+)\t(\d+)\t(\w+)\{\}\n?', obs['stdout'])
    return (int(match.group(2)), match.group(3)) if match and classify(obs) == 'Success' else None


def labelled(knot) -> list[tuple[str, dict]]:
    """Every observation of one case: the phases, then each call by entry and arguments."""
    return ([(p, knot[p]) for p in KNOT_PHASES if knot.get(p)]
            + [(f"{c['entry']}{c['arguments']}", c) for c in knot.get('calls', [])])


def paired(knot, seed):
    """Knot's calls beside the frozen ones, or None when the two call lists differ."""
    calls, frozen = knot.get('calls', []), seed['calls']
    same = [(c['entry'], c['arguments']) for c in calls] == [(c['entry'], c['arguments']) for c in frozen]
    return list(zip(calls, frozen)) if same else None


def answer(call, want) -> str:
    return (f"{call['entry']}{call['arguments']}: {diagnostic(call) or call['stdout'].strip()} "
            f"!= {want['constructor']} (tag {want['tag']})")


# ------------------------------------------------------------------ requirements

def meets(case, seed, knot) -> list[str]:
    """Why Knot's observations miss the case's requirement; empty when they meet it."""
    need, problems = case['knot'], []
    check = knot.get('check')
    if check is None:
        return ['no check observation']
    if need['require'] == 'agree':
        if case['kind'] != 'value':
            return ['no Knot lane runs io programs yet']
        if classify(check) != 'Success' or not check['stdout'].startswith('Checked\n'):
            return [f'check: {diagnostic(check) or classify(check)}']
        pairs = paired(knot, seed)
        if pairs is None:
            return ['the evaluated calls differ from the frozen calls']
        for call, want in pairs:
            result = want['result']
            if result is None:
                problems.append(f"{call['entry']}{call['arguments']}: the seed lanes disagree without an oracle")
            elif evaluated(call) != (result['tag'], result['constructor']):
                problems.append(answer(call, result))
        return problems
    for phase in KNOT_PHASES:
        obs = knot.get(phase)
        if obs is None:
            problems.append(f'{phase}: not observed')
            continue
        if obs['exit'] != need['exit'] or not obs['stderr'].startswith(need['diagnostic']) or obs['stdout']:
            problems.append(f'{phase}: {diagnostic(obs) or classify(obs)} != {need["diagnostic"].strip()}')
        elif 'at' in need and position(obs) != need['at']:
            problems.append(f'{phase}: at {position(obs)} != {need["at"]}')
    return problems


def faults(case, seed, knot) -> list[str]:
    """What no missing need excuses: an unclassified outcome, a seed-rejected twin
    accepted by any phase, or a seed-valid call answered other than the seed does."""
    found = [f'{label}: Knot reported {classify(o)}' for label, o in labelled(knot) if classify(o) not in CLASSIFIED]
    check = knot.get('check')
    if case['knot']['require'] == 'reject':
        found += [f'{p}: accepted a seed-rejected twin' for p in KNOT_PHASES
                  if knot.get(p) and classify(knot[p]) == 'Success']
    elif case['knot']['require'] == 'agree' and case['kind'] == 'value' and check and classify(check) == 'Success':
        pairs = paired(knot, seed)
        if pairs is None:
            found.append('the evaluated calls differ from the frozen calls')
        else:
            found += [answer(call, want['result']) for call, want in pairs
                      if want['result'] is not None and classify(call) == 'Success'
                      and evaluated(call) != (want['result']['tag'], want['result']['constructor'])]
    return found


def d4_gap(case, knot) -> list[str]:
    """Knot's Invalid diagnostics on a seed-valid case, where D4 requires Unsupported."""
    if case['knot']['require'] == 'reject':
        return []
    return [diagnostic(o) for _, o in labelled(knot) if classify(o) == 'Invalid']


def line_break(case, diagnostic) -> bool:
    """Whether a diagnostic's `start:end` span is exactly one line break of the entry file."""
    fields = diagnostic.split('\t')
    span = fields[3].split(':')[:2] if len(fields) > 3 else []
    if len(span) != 2 or not all(s.isdigit() for s in span):
        return False
    start, end = map(int, span)
    return end == start + 1 and (ROOT / case['files'][0]).read_bytes()[start:end] == b'\n'


def unreviewed(case, knot, blocked_by) -> list[str]:
    """The D4 gaps of a case that no reviewed row of a need still blocking it excuses."""
    prefixes = [p for n in blocked_by for p in D4_GAPS.get(n, (None, ()))[1]]
    return [d for d in d4_gap(case, knot)
            if not (any((d + '\t').startswith(p) for p in prefixes) and line_break(case, d))]


def derive(case, seed, knot, available) -> dict:
    """Every recorded verdict field of one case, from its observations alone."""
    blocked_by = [n for n in case['needs'] if n not in available]
    missing, wrong = meets(case, seed, knot), faults(case, seed, knot)
    status = 'fail' if wrong or (missing and not blocked_by) else 'blocked' if blocked_by else 'pass'
    check = knot.get('check')
    return {'status': status, 'blocked_by': blocked_by, 'meets_requirement': not missing,
            'problems': missing, 'faults': wrong, 'outcomes': sorted({classify(o) for _, o in labelled(knot)}),
            'first_blocker': (diagnostic(check) or classify(check)) if check else None,
            'd4_gap': bool(d4_gap(case, knot))}


# ------------------------------------------------------------------ judge

def judge(document, receipt) -> list[str]:
    """Gate verdict over recorded fields only."""
    violations = []
    if receipt.get('seed', {}).get('reproduced') is not True:
        violations.append('the seed observations were not reproduced')
    observations = document.get('observations', {})
    frozen = {o['case']: o for o in observations.get('fixtures', [])}
    decisions = {d['id'] for d in document.get('lane_decisions', [])}
    for o in frozen.values():
        for call in o.get('calls', []) + o.get('runs', []):
            if call.get('lanes') != 'agree' and call.get('decision') not in decisions:
                violations.append(f"{o['case']}: an unreviewed seed lane disagreement")
            if 'calls' in o and (call.get('interpreter') is None or call.get('native', {}).get('run') is None):
                violations.append(f"{o['case']}: a seed call lacks a lane")
    available = {n for n, v in document['needs'].items() if v['available']}
    if sorted(available) != receipt.get('available'):
        violations.append('the receipt was taken under other needs')
    by = {c['name']: c for c in document['cases']}
    for need, (owner, prefixes) in D4_GAPS.items():
        if (document['needs'].get(need, {}).get('owner') != owner or not prefixes
                or not all(re.fullmatch(r'Invalid\t[a-z]+\t[a-z-]+\t', p) for p in prefixes)):
            violations.append(f'{need}: the D4 gap table must name a need, its owner and Invalid codes')
    for o in frozen.values():  # gap spans are read from the entry files
        for path, sha in o.get('sources', {}).items():
            if not (ROOT / path).is_file() or digest((ROOT / path).read_bytes()) != sha:
                violations.append(f"{o['case']}: {path} differs from its frozen digest")
    rows = {r['case']: r for r in receipt.get('cases', [])}
    if sorted(rows) != sorted(by):
        violations.append('the receipt does not cover exactly the frozen cases')
    again_rows = []
    for case in document['cases']:
        name, row = case['name'], rows.get(case['name'])
        if row is None:
            continue
        again = derive(case, frozen.get(name, {}), row['knot'], available)
        again_rows.append({'case': name, 'owner': case['owner'], **again})
        if again['faults']:
            blocked = f" while blocked by {again['blocked_by']}" if again['blocked_by'] else ''
            violations.append(f"{name}: {'; '.join(again['faults'])}{blocked}")
        elif again['status'] == 'fail':
            violations.append(f"{name}: {'; '.join(again['problems'])}")
        for key, value in again.items():
            if row.get(key) != value:
                violations.append(f'{name}: recorded {key} {row.get(key)!r}, recomputed {value!r}')
        stray = unreviewed(case, row['knot'], again['blocked_by'])
        if stray:
            violations.append(f'{name}: an unreviewed D4 gap: seed-valid, but Knot reported {stray}')
    recorded = receipt.get('counts', {})
    for key, value in counts(again_rows, available).items():
        if recorded.get(key) != value:
            violations.append(f'recorded counts.{key} {recorded.get(key)!r} != {value!r}')
    if not any(r['status'] == 'pass' for r in again_rows):
        violations.append('no case passes: the gate would be vacuous')
    return violations


# ------------------------------------------------------------------ Knot lanes

def build(entry, out, record):
    for _ in range(3):  # the seed's clang probe can fail to spawn under host load
        built = run(['bun', SEED, entry, '-o', out], SECONDS['build'])
        if not (built['exit'] != 0 and regen.HOST_TOOLCHAIN in built['stderr']):
            break
    require(built['exit'] == 0, ('seed build failed', built))
    record.append({'entry': entry, 'output': out, 'exit': built['exit'], 'stdout': built['stdout'],
                   'stderr': built['stderr'], 'sha256': digest((ROOT / out).read_bytes())})


def observe(case, seed, bins) -> dict:
    """Knot on one case. Evaluation runs only after a successful check."""
    entry = case['files'][0]
    knot = {'check': run([bins['check'], entry], SECONDS['call'])}
    budget = str(case['knot'].get('budget', 65536))
    if case['knot']['require'] != 'agree':
        knot['eval'] = run([bins['eval'], entry, 'main', budget], SECONDS['call'])
    elif case['kind'] == 'value' and classify(knot['check']) == 'Success':
        knot['calls'] = [
            {'entry': c['entry'], 'arguments': c['arguments'],
             **run([bins['eval'], entry, c['entry'], budget, *c['ordinals']], SECONDS['call'])}
            for c in seed['calls']]
    for obs in [knot['check'], knot.get('eval'), *knot.get('calls', [])]:
        if obs is not None and obs['exit'] == 0 and obs['stdout'].startswith('Checked\n'):
            # The checked-book display is large and implied by the source; keep its digest.
            obs['stdout'] = f"Checked\n<sha256 {digest(obs['stdout'].encode())}>\n"
    return knot


def lanes(bins_dir) -> tuple[dict, list]:
    record = []
    (ROOT / bins_dir).mkdir(parents=True, exist_ok=True)
    for phase in KNOT_PHASES:
        build(f'src/{phase}-cli.bend', f'{bins_dir}/{phase}', record)
    return {p: f'./{bins_dir}/{p}' for p in KNOT_PHASES}, record


def cases_run(document, bins, only=None) -> list[dict]:
    frozen = {o['case']: o for o in document['observations']['fixtures']}
    available = {n for n, v in document['needs'].items() if v['available']}
    chosen = [c for c in document['cases'] if only is None or c['name'] in only]
    with ThreadPoolExecutor(JOBS) as pool:
        knots = list(pool.map(lambda c: observe(c, frozen[c['name']], bins), chosen))
    return [{'case': case['name'], 'owner': case['owner'], 'requirements': case['requirements'],
             'require': case['knot']['require'], **derive(case, frozen[case['name']], knot, available), 'knot': knot}
            for case, knot in zip(chosen, knots)]


# ------------------------------------------------------------------ mutants

# Type-correct replacements in src/; each must be killed by an unblocked case.
MUTANTS = [
    ('reject-every-self-call', 'check.bend',
     'Bool.and(U32.is_eq(index,current),Bool.not(E.descends(items,smaller)))',
     'U32.is_eq(index,current)', 'nested-self-call', ('check',)),
    ('admit-mistyped-constant', 'check.bend',
     'S.choose(Result<S.Error,C.Checked>,U32.is_eq(type_id,target),u => Done{C.Checked{C.Value{token,type_id,tag},type_id,Nil{}}}',
     'S.choose(Result<S.Error,C.Checked>,True{},u => Done{C.Checked{C.Value{token,type_id,tag},type_id,Nil{}}}',
     'nested-self-call-mistyped', ('check', 'eval')),
    ('unreversed-fields', 'eval.bend',
     'Done{Return{Object{type_id,tag,List.reverse(&2,Value,values)},frames}}',
     'Done{Return{Object{type_id,tag,values},frames}}', 'nested-self-call', ('check', 'eval')),
]


def mutants(document) -> list[dict]:
    results = []
    by_case = {c['name']: c for c in document['cases']}
    available = {n for n, v in document['needs'].items() if v['available']}
    for name, file, old, new, witness, phases in MUTANTS:
        case = by_case[witness]
        require(all(n in available for n in case['needs']), (name, 'a mutant witness must be unblocked'))
        directory = f'{BUILD}/mutants/{name}'
        if (ROOT / directory).exists():
            shutil.rmtree(ROOT / directory)
        (ROOT / directory / 'src').mkdir(parents=True)
        for source in (ROOT / 'src').glob('*.bend'):
            shutil.copy2(source, ROOT / directory / 'src' / source.name)
        shutil.copytree(ROOT / 'src/host', ROOT / directory / 'src/host')
        target = ROOT / directory / 'src' / file
        text = target.read_text()
        require(text.count(old) == 1, (name, 'a mutation site must be unique'))
        target.write_text(text.replace(old, new))
        typecheck = run(['bun', SEED, f'{directory}/src/{phases[-1]}-cli.bend', '--check-only'], SECONDS['build'])
        require(typecheck['exit'] == 0 and typecheck['stdout'] == HOST_CHECKS[f'{phases[-1]}-cli.bend']['stdout'],
                (name, 'type-correct', typecheck))
        bins, builds = {}, []
        for phase in ('check', 'eval'):
            if phase in phases:
                build(f'{directory}/src/{phase}-cli.bend', f'{directory}/{phase}', builds)
                bins[phase] = f'./{directory}/{phase}'
            else:
                bins[phase] = f'./{BUILD}/{phase}'
        row = cases_run(document, bins, only={witness})[0]
        crashes = [k for k in row['outcomes'] if k not in CLASSIFIED + ('HostFailure', 'InternalFailure')]
        results.append({'name': name, 'file': f'src/{file}', 'old': old, 'new': new,
                        'mutated_sha256': digest(target.read_bytes()), 'typecheck': typecheck['stdout'],
                        'builds': [{k: b[k] for k in ('entry', 'exit', 'sha256')} for b in builds],
                        'witness': witness, 'status': row['status'], 'problems': row['problems'],
                        'outcomes': row['outcomes'],
                        'killed': row['status'] == 'fail' and not crashes})
        require(results[-1]['killed'], (name, 'survived or crashed', row))
    return results


def restate(document, receipt):
    """Rederive every recorded verdict and count, as an honest runner records them."""
    frozen = {o['case']: o for o in document['observations']['fixtures']}
    by = {c['name']: c for c in document['cases']}
    for row in receipt['cases']:
        row.update(derive(by[row['case']], frozen[row['case']], row['knot'], set(receipt['available'])))
    receipt['counts'] = counts(receipt['cases'], set(receipt['available']))


def judge_mutants(document, receipt) -> list[dict]:
    """Mutated receipts and expectations the judge must reject, each for its named reason.

    A `restated` mutant rederives every verdict from its edited observations, so
    only the rule under test can reject it."""
    by = {c['name']: c for c in document['cases']}
    frozen = {o['case']: o for o in document['observations']['fixtures']}
    passing = next(r['case'] for r in receipt['cases'] if r['status'] == 'pass' and r['require'] == 'agree')
    rejecting = next(r['case'] for r in receipt['cases'] if r['status'] == 'pass' and r['require'] == 'reject')
    blocked = next(r['case'] for r in receipt['cases'] if r['status'] == 'blocked')
    twin = next(r['case'] for r in receipt['cases'] if r['status'] == 'blocked' and r['require'] == 'reject')
    positive = next(r['case'] for r in receipt['cases'] if r['status'] == 'blocked' and r['require'] == 'agree'
                    and by[r['case']]['kind'] == 'value')
    valid = next(r['case'] for r in receipt['cases'] if r['status'] == 'blocked' and r['require'] != 'reject'
                 and not any(n in D4_GAPS for n in r['blocked_by']))
    gap = next((r['case'] for r in receipt['cases'] if r['d4_gap']), None)
    hidden = next(iter(hidden_gaps(document, receipt)), None)
    seeded = next(o['case'] for o in document['observations']['fixtures'] if o.get('calls'))

    def with_receipt(edit, restated=False):
        r = copy.deepcopy(receipt)
        edit({x['case']: x for x in r['cases']}, r)
        if restated:
            restate(document, r)
        return document, r

    def with_document(edit):
        d = copy.deepcopy(document)
        edit({o['case']: o for o in d['observations']['fixtures']}, d)
        return d, receipt

    def checked(obs):
        return {**obs, 'exit': 0, 'stdout': f"Checked\n<sha256 {'0' * 64}>\n", 'stderr': ''}

    def flip_tag(rs, r):
        call = rs[passing]['knot']['calls'][0]
        tag, name = evaluated(call)
        call['stdout'] = call['stdout'].replace(f'\t{tag}\t{name}', f'\t{tag + 1}\t{name}')

    def crash(rs, r):
        rs[blocked]['knot']['check'] = {**rs[blocked]['knot']['check'], 'exit': 134,
                                         'stderr': 'Error: RangeError: Maximum call stack size exceeded\n'}

    def reword(rs, r):
        obs = rs[rejecting]['knot']['check']
        obs['stderr'] = obs['stderr'].replace('\tcheck\t', '\tparse\t', 1)

    def shift(rs, r):
        obs = rs[rejecting]['knot']['eval']
        fields = obs['stderr'].split('\t')
        start, end, line, col = fields[3].split('\n')[0].split(':')
        obs['stderr'] = '\t'.join(fields[:3] + [f'{start}:{end}:{line}:{int(col) + 1}\n'])

    def accept_twin(rs, r):
        knot = rs[twin]['knot']
        knot['check'] = checked(knot['check'])
        knot['eval'] = {**knot['eval'], 'exit': 0, 'stdout': 'Evaluated\t0\t0\tLeaf{}\n', 'stderr': ''}

    def answer_calls(rs, mistake):
        knot = rs[positive]['knot']
        knot['check'] = checked(knot['check'])
        knot['calls'] = [{'entry': c['entry'], 'arguments': c['arguments'], 'argv': [], 'exit': 0,
                          'stdout': f"Evaluated\t0\t{c['result']['tag']}\t{c['result']['constructor']}{{}}\n",
                          'stderr': ''} for c in frozen[positive]['calls']]
        mistake(knot['calls'])

    def wrong_value(calls):
        calls[0]['stdout'] = f"Evaluated\t0\t{evaluated(calls[0])[0] + 1}\tWrong{{}}\n"

    def report_invalid(rs, r):
        rs[valid]['knot']['check'] = {**rs[valid]['knot']['check'], 'exit': 2, 'stdout': '',
                                       'stderr': 'Invalid\tparse\texpected-term\t0:1:1:0\n'}

    def recode_gap(rs, r):
        obs = rs[gap]['knot']['check']
        fields = obs['stderr'].split('\t')
        obs['stderr'] = '\t'.join(fields[:2] + ['end-of-body'] + fields[3:])

    def displace_gap(rs, r):
        obs = rs[gap]['knot']['check']
        kind, phase, code, span = diagnostic(obs).split('\t')
        start, end, line, column = map(int, span.split(':'))
        obs['stderr'] = f'{kind}\t{phase}\t{code}\t{start - 1}:{end - 1}:{line}:{column - 1}\n'

    def surface_other_code(rs, r):
        rs[hidden]['knot'] = reported(by[hidden], rs[hidden]['knot'], 'Invalid\tcheck\ttype-mismatch\t')

    def landed(need):
        d, r = copy.deepcopy(document), copy.deepcopy(receipt)
        d['needs'][need]['available'] = True
        r['available'] = sorted(r['available'] + [need])
        restate(d, r)
        return d, r

    cases = [
        ('blocked-counted-as-pass', with_receipt(lambda rs, r: rs[blocked].update(status='pass')),
         'recorded status'),
        ('failure-relabelled-blocked', with_receipt(lambda rs, r: (rs[passing].update(status='blocked'),
                                                                   rs[passing]['knot']['calls'].pop())),
         "recorded status 'blocked', recomputed 'fail'"),
        ('dropped-knot-call', with_receipt(lambda rs, r: rs[passing]['knot']['calls'].pop()),
         'the evaluated calls differ from the frozen calls'),
        ('flipped-evaluated-tag', with_receipt(flip_tag), '(tag '),
        ('crash-while-blocked', with_receipt(crash), 'check: Knot reported Crash while blocked'),
        ('reworded-diagnostic', with_receipt(reword), 'check: Invalid\tparse'),
        ('shifted-position', with_receipt(shift), 'eval: at '),
        ('stale-needs', with_receipt(lambda rs, r: r.update(available=sorted(r['available'] + ['layout']))),
         'other needs'),
        ('seed-not-reproduced', with_receipt(lambda rs, r: r['seed'].update(reproduced=False)), 'not reproduced'),
        ('unreviewed-lane-disagreement', with_document(
            lambda os_, d: os_[seeded]['calls'][0].update(lanes='disagree')), 'unreviewed seed lane disagreement'),
        ('dropped-native-lane', with_document(
            lambda os_, d: os_[seeded]['calls'][0]['native'].update(run=None)), 'lacks a lane'),
        ('accepted-blocked-twin', with_receipt(accept_twin, restated=True),
         'check: accepted a seed-rejected twin'),
        ('wrong-value-while-blocked', with_receipt(lambda rs, r: answer_calls(rs, wrong_value), restated=True),
         'Wrong{} != '),
        ('dropped-call-while-blocked', with_receipt(lambda rs, r: answer_calls(rs, list.pop), restated=True),
         'the evaluated calls differ from the frozen calls while blocked'),
        ('unreviewed-d4-gap', with_receipt(report_invalid, restated=True), f'{valid}: an unreviewed D4 gap'),
    ]
    if gap:  # a reviewed gap shows today
        cases += [
            ('recoded-d4-gap', with_receipt(recode_gap, restated=True), f'{gap}: an unreviewed D4 gap'),
            ('displaced-d4-gap', with_receipt(displace_gap, restated=True), f'{gap}: an unreviewed D4 gap'),
            ('gap-outlives-need', landed(next(n for n in by[gap]['needs'] if n in D4_GAPS)),
             f'{gap}: an unreviewed D4 gap'),
            ('erased-d4-gaps', with_receipt(lambda rs, r: r['counts'].update(d4_gaps=[])), 'recorded counts.d4_gaps'),
        ]
    if hidden:  # another blocker hides a gap row's need today
        cases.append(('surfaced-other-code', with_receipt(surface_other_code, restated=True),
                      f'{hidden}: an unreviewed D4 gap'))
    results = []
    for name, (d, r), reason in cases:
        found = judge(d, r)
        matched = next((v for v in found if reason in v), None)
        results.append({'name': name, 'rejected': matched is not None, 'reason': reason, 'violation': matched,
                        'violations': len(found)})
        require(matched is not None, (name, 'the judge did not reject it for its reason', reason, found))
    return results


def hidden_gaps(document, receipt) -> list[str]:
    """Seed-valid cases a gap row's need still blocks, whose recorded observations show no gap:
    another blocker stops Knot first, and landing it will surface the gap."""
    return [r['case'] for r in receipt['cases'] if r['require'] != 'reject' and not r['d4_gap']
            and any(n in D4_GAPS for n in r['blocked_by'])]


def continuation(case) -> int:
    """Offset of the entry file's first line break inside an open delimiter, outside comments."""
    depth, comment = 0, False
    for offset, ch in enumerate((ROOT / case['files'][0]).read_bytes().decode('ascii')):
        if ch == '\n':
            if depth:
                return offset
            comment = False
        elif not comment:
            comment = ch == '#'
            depth += (ch in '([{') - (ch in ')]}')
    raise AssertionError((case['name'], 'no line break inside a delimiter'))


def reported(case, knot, prefix) -> dict:
    """Knot's phases on a case, each reporting `prefix` at the case's first continuation line break."""
    source, at = (ROOT / case['files'][0]).read_bytes(), continuation(case)
    line, column = source.count(b'\n', 0, at) + 1, at - source.rfind(b'\n', 0, at) - 1
    exit_code = next(k for k, v in OUTCOMES.items() if v == prefix.split('\t')[0])
    return {p: {'argv': knot[p].get('argv', []), 'exit': exit_code, 'stdout': '',
                'stderr': f'{prefix}{at}:{at + 1}:{line}:{column}\n'} for p in KNOT_PHASES if p in knot}


def judge_controls(document, receipt) -> list[dict]:
    """Restated receipts the judge must accept: each hidden gap surfacing with a reviewed code
    at its first continuation line break, as `layout-lambda-statements` does once closures lands."""
    by = {c['name']: c for c in document['cases']}
    results = []
    for name in hidden_gaps(document, receipt):
        r = copy.deepcopy(receipt)
        row = next(x for x in r['cases'] if x['case'] == name)
        need = next(n for n in row['blocked_by'] if n in D4_GAPS)
        row['knot'] = reported(by[name], row['knot'], D4_GAPS[need][1][0])
        restate(document, r)
        found = judge(document, r)
        results.append({'name': f'surfaced-{need}-gap', 'case': name, 'diagnostic': diagnostic(row['knot']['check']),
                        'accepted': not found, 'violations': found})
        require(not found, (name, 'the judge rejected a surfaced reviewed gap', found))
    return results


# ------------------------------------------------------------------ main

def counts(rows, available) -> dict:
    status = {'pass': 0, 'fail': 0, 'blocked': 0}
    owners = {}
    for row in rows:
        status[row['status']] += 1
        owner = owners.setdefault(row['owner'], {'pass': 0, 'fail': 0, 'blocked': 0})
        owner[row['status']] += 1
    return {'status': status, 'by_owner': dict(sorted(owners.items())),
            'd4_gaps': sorted(r['case'] for r in rows if r['d4_gap']),
            'd4_gaps_closed': sorted(n for n in D4_GAPS if n in available),
            'blocked_meeting_requirement': sorted(r['case'] for r in rows
                                                  if r['status'] == 'blocked' and r['meets_requirement'])}


def inputs() -> dict:
    paths = sorted((ROOT / 'src').glob('*.bend')) + [ROOT / 'src/CONTRACT.json', HERE / 'check.py',
                                                     HERE / 'regen.py', EXPECTATIONS]
    paths += sorted((ROOT / 'src/host').glob('*')) + [ROOT / 'tests/compiler-modules/host-check-expectations.json']
    return {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in paths}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--judge', metavar='RECEIPT', help='apply the verdict to a recorded receipt')
    args = parser.parse_args(argv)
    document = json.loads(EXPECTATIONS.read_text())
    if args.judge:
        found = judge(document, json.loads(Path(args.judge).read_text()))
        for v in found:
            print('judge:', v, file=sys.stderr)
        return 1 if found else 0
    before = inputs()
    receipt = {'schema': 1, 'suite': 'compiler-selfhost', 'increment': 'joint', 'status': 'incomplete'}
    try:
        stored = document['observations']
        try:
            observations = regen.observe_all(document)
        except regen.Mismatch as e:
            raise AssertionError(('seed lane', e))
        receipt['seed'] = {'reproduced': observations == stored, 'summary': regen.summary(document, observations)}
        require(receipt['seed']['reproduced'], 'seed observations differ from expectations.json; run regen.py')
        if (ROOT / BUILD).exists():
            shutil.rmtree(ROOT / BUILD)
        bins, builds = lanes(BUILD)
        receipt['knot'] = {'lane': 'native', 'builds': [{k: b[k] for k in ('entry', 'exit', 'sha256')} for b in builds]}
        receipt['available'] = sorted(n for n, v in document['needs'].items() if v['available'])
        receipt['cases'] = cases_run(document, bins)
        receipt['counts'] = counts(receipt['cases'], set(receipt['available']))
        found = judge(document, receipt)
        require(not found, ('judge', found))
        receipt['judge_mutants'] = judge_mutants(document, receipt)
        receipt['judge_controls'] = judge_controls(document, receipt)
        receipt['mutants'] = mutants(document)
        require(inputs() == before, 'inputs changed while the gate ran')
        receipt['inputs'] = before
        receipt['status'] = 'passed'
    except AssertionError as e:
        receipt['status'] = 'failed'
        receipt['failure'] = repr(e)[:4000]
        print('selfhost: FAIL', repr(e)[:4000], file=sys.stderr)
        return 1
    finally:
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(receipt, indent=2) + '\n')
    c = receipt['counts']['status']
    print(f"selfhost: PASS {receipt['seed']['summary']}; Knot {c['pass']} pass, {c['blocked']} blocked, "
          f"{c['fail']} fail; {len(receipt['counts']['d4_gaps'])} blocked D4 gaps; "
          f"{len(receipt['judge_mutants'])} judge mutants and {len(receipt['mutants'])} src mutants killed; "
          f"{len(receipt['judge_controls'])} judge controls accepted")
    return 0


if __name__ == '__main__':
    sys.exit(main())
