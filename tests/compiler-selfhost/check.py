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
   first-blocker evidence, but a blocked case never counts as passing. Invalid,
   Unsupported and Exhausted may block; a host or internal failure, a signal,
   an unclassified exit or a timeout fails the gate even while blocked.
4. An unblocked case must meet its requirement: `agree` checks the book and
   evaluates every frozen call to the seed's constructor and tag; `reject` and
   `unsupported` report the pinned exit, phase and code (and position, where
   pinned) from every phase that runs.
5. The judge is applied to the recorded receipt, then to mutated copies, each
   of which it must reject. Type-correct mutants of `src/` must be killed by
   an unblocked case with a classified, non-crashing observation.
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
BUILD = '.local/compiler-selfhost/knot'
RECEIPT = HERE / 'receipts/selfhost.json'
EXPECTATIONS = HERE / 'expectations.json'
SCALE = float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))
SECONDS = {'build': 600 * SCALE, 'call': 120 * SCALE}
OUTCOMES = {0: 'Success', 2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted', 5: 'HostFailure', 6: 'InternalFailure'}
MAY_BLOCK = ('Success', 'Invalid', 'Unsupported', 'Exhausted')
JOBS = int(os.environ.get('KNOT_SELFHOST_JOBS', '6'))

# Knot's lanes for this suite. Route-independent: the evaluator is the reference
# every backend and the VM are compared with. Multi-module cases run in the
# CLIs' single-file mode until `modules` lands; that increment adds its
# bundle argument here when it flips the need.
KNOT_PHASES = ('check', 'eval')


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
        calls = knot.get('calls', [])
        frozen = seed['calls']
        if [(c['entry'], c['arguments']) for c in calls] != [(c['entry'], c['arguments']) for c in frozen]:
            return ['the evaluated calls differ from the frozen calls']
        for call, want in zip(calls, frozen):
            got = evaluated(call)
            result = want['result']
            if result is None:
                problems.append(f"{call['entry']}{call['arguments']}: the seed lanes disagree without an oracle")
            elif got != (result['tag'], result['constructor']):
                problems.append(f"{call['entry']}{call['arguments']}: {diagnostic(call) or call['stdout'].strip()} "
                                f"!= {result['constructor']} (tag {result['tag']})")
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


def status_of(case, seed, knot, available) -> dict:
    blocked_by = [n for n in case['needs'] if n not in available]
    missing = meets(case, seed, knot)
    outcomes = [classify(o) for o in [knot.get('check'), knot.get('eval'), *knot.get('calls', [])] if o]
    if blocked_by:
        status = 'blocked'
    else:
        status = 'fail' if missing else 'pass'
    return {'status': status, 'blocked_by': blocked_by, 'meets_requirement': not missing,
            'problems': missing, 'outcomes': sorted(set(outcomes))}


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
    rows = {r['case']: r for r in receipt.get('cases', [])}
    if sorted(rows) != sorted(c['name'] for c in document['cases']):
        violations.append('the receipt does not cover exactly the frozen cases')
    counts = {'pass': 0, 'fail': 0, 'blocked': 0}
    for case in document['cases']:
        row = rows.get(case['name'])
        if row is None:
            continue
        again = status_of(case, frozen.get(case['name'], {}), row['knot'], available)
        counts[again['status']] += 1
        if row['status'] != again['status']:
            violations.append(f"{case['name']}: recorded {row['status']}, recomputed {again['status']}")
        if again['status'] == 'fail':
            violations.append(f"{case['name']}: {'; '.join(again['problems'])}")
        if again['status'] == 'blocked':
            bad = [k for k in again['outcomes'] if k not in MAY_BLOCK]
            if bad:
                violations.append(f"{case['name']}: blocked by {again['blocked_by']} but Knot reported {bad}")
    if receipt.get('counts', {}).get('status') != counts:
        violations.append(f"recorded counts {receipt.get('counts', {}).get('status')} != {counts}")
    if counts['pass'] == 0:
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
    rows = []
    for case, knot in zip(chosen, knots):
        verdict = status_of(case, frozen[case['name']], knot, available)
        seed_valid = case['knot']['require'] != 'reject'
        rows.append({'case': case['name'], 'owner': case['owner'], 'requirements': case['requirements'],
                     'require': case['knot']['require'], **verdict,
                     'first_blocker': diagnostic(knot['check']) or classify(knot['check']),
                     'd4_gap': seed_valid and classify(knot['check']) == 'Invalid',
                     'knot': knot})
    return rows


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
        target = ROOT / directory / 'src' / file
        text = target.read_text()
        require(text.count(old) == 1, (name, 'a mutation site must be unique'))
        target.write_text(text.replace(old, new))
        typecheck = run(['bun', SEED, f'{directory}/src/{phases[-1]}-cli.bend', '--check-only'], SECONDS['build'])
        require(typecheck['exit'] == 0 and typecheck['stdout'] == 'All terms check.\n', (name, 'type-correct', typecheck))
        bins, builds = {}, []
        for phase in ('check', 'eval'):
            if phase in phases:
                build(f'{directory}/src/{phase}-cli.bend', f'{directory}/{phase}', builds)
                bins[phase] = f'./{directory}/{phase}'
            else:
                bins[phase] = f'./{BUILD}/{phase}'
        row = cases_run(document, bins, only={witness})[0]
        crashes = [k for k in row['outcomes'] if k not in MAY_BLOCK + ('HostFailure', 'InternalFailure')]
        results.append({'name': name, 'file': f'src/{file}', 'old': old, 'new': new,
                        'mutated_sha256': digest(target.read_bytes()), 'typecheck': typecheck['stdout'],
                        'builds': [{k: b[k] for k in ('entry', 'exit', 'sha256')} for b in builds],
                        'witness': witness, 'status': row['status'], 'problems': row['problems'],
                        'outcomes': row['outcomes'],
                        'killed': row['status'] == 'fail' and not crashes})
        require(results[-1]['killed'], (name, 'survived or crashed', row))
    return results


def judge_mutants(document, receipt) -> list[dict]:
    """Mutated receipts and expectations the judge must reject."""
    rows = {r['case']: r for r in receipt['cases']}
    passing = next(r['case'] for r in receipt['cases'] if r['status'] == 'pass' and r['require'] == 'agree')
    rejecting = next(r['case'] for r in receipt['cases'] if r['status'] == 'pass' and r['require'] == 'reject')
    blocked = next(r['case'] for r in receipt['cases'] if r['status'] == 'blocked')
    seeded = next(o['case'] for o in document['observations']['fixtures'] if o.get('calls'))

    def with_receipt(edit):
        r = copy.deepcopy(receipt)
        edit({x['case']: x for x in r['cases']}, r)
        return document, r

    def with_document(edit):
        d = copy.deepcopy(document)
        edit({o['case']: o for o in d['observations']['fixtures']}, d)
        return d, receipt

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

    cases = [
        ('blocked-counted-as-pass', with_receipt(lambda rs, r: rs[blocked].update(status='pass'))),
        ('failure-relabelled-blocked', with_receipt(lambda rs, r: (rs[passing].update(status='blocked'),
                                                                   rs[passing]['knot']['calls'].pop()))),
        ('dropped-knot-call', with_receipt(lambda rs, r: rs[passing]['knot']['calls'].pop())),
        ('flipped-evaluated-tag', with_receipt(flip_tag)),
        ('crash-while-blocked', with_receipt(crash)),
        ('reworded-diagnostic', with_receipt(reword)),
        ('shifted-position', with_receipt(shift)),
        ('stale-needs', with_receipt(lambda rs, r: r.update(available=sorted(r['available'] + ['layout'])))),
        ('seed-not-reproduced', with_receipt(lambda rs, r: r['seed'].update(reproduced=False))),
        ('unreviewed-lane-disagreement', with_document(
            lambda os_, d: os_[seeded]['calls'][0].update(lanes='disagree'))),
        ('dropped-native-lane', with_document(
            lambda os_, d: os_[seeded]['calls'][0]['native'].update(run=None))),
    ]
    results = []
    for name, (d, r) in cases:
        found = judge(d, r)
        results.append({'name': name, 'rejected': bool(found), 'first_violation': found[0] if found else None})
        require(found, (name, 'the judge accepted a mutated receipt'))
    return results


# ------------------------------------------------------------------ main

def counts(rows) -> dict:
    status = {'pass': 0, 'fail': 0, 'blocked': 0}
    owners = {}
    for row in rows:
        status[row['status']] += 1
        owner = owners.setdefault(row['owner'], {'pass': 0, 'fail': 0, 'blocked': 0})
        owner[row['status']] += 1
    return {'status': status, 'by_owner': dict(sorted(owners.items())),
            'd4_gaps': sorted(r['case'] for r in rows if r['d4_gap']),
            'blocked_meeting_requirement': sorted(r['case'] for r in rows
                                                  if r['status'] == 'blocked' and r['meets_requirement'])}


def inputs() -> dict:
    paths = sorted((ROOT / 'src').glob('*.bend')) + [ROOT / 'src/CONTRACT.json', HERE / 'check.py',
                                                     HERE / 'regen.py', EXPECTATIONS]
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
        receipt['counts'] = counts(receipt['cases'])
        found = judge(document, receipt)
        require(not found, ('judge', found))
        receipt['judge_mutants'] = judge_mutants(document, receipt)
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
          f"{len(receipt['judge_mutants'])} judge mutants and {len(receipt['mutants'])} src mutants killed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
