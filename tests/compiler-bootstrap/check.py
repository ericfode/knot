#!/usr/bin/env python3
"""E2E-2 self-parse and E2E-3 fixpoint harness. Host only: it builds with the
seed, invokes compilers and modules, and compares bytes. No compiler semantics.

    python3 tests/compiler-bootstrap/check.py            run every stage, write receipts
    python3 tests/compiler-bootstrap/check.py --judge P  apply the gate verdict to receipt P
"""
from __future__ import annotations

import argparse
import base64
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import posixpath
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REL = HERE.relative_to(ROOT).as_posix()
BUILD = '.local/compiler-bootstrap'
SEED = 'scripts/bend-reference'
HOST = f'{REL}/host.mjs'
RUN_WASM = 'scripts/run-wasm.mjs'
PROGRESS = HERE / 'receipts/progress.json'
REFERENCE = HERE / 'receipts/reference.json'
BASE = '.toolchain/bend-2.0.29-574b6d3/bend2/base.bend'
PARSER = 'src/parse-cli.bend'      # E2E-2 subject
COMPILER = 'src/compile-cli.bend'  # the one compiler entry for C1, A2 and A3
PROGRAMS = 'tests/compiler-wasm/cases.json'
REJECTS = 'tests/compiler-checker/cases.json'
OUTCOMES = {2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted', 5: 'HostFailure', 6: 'InternalFailure'}
ALLOWED = ('Unsupported', 'Exhausted')
EXCLUDED = ('.git', '.local', '.toolchain', 'node_modules', 'build')
STAGES = (('e2e2.reference', 'E2E-2'), ('e2e2.compile', 'E2E-2'), ('e2e2.self-parse', 'E2E-2'),
          ('e2e3.c1', 'E2E-3'), ('e2e3.a2', 'E2E-3'), ('e2e3.a3', 'E2E-3'),
          ('e2e3.fixpoint', 'E2E-3'), ('e2e3.conformance', 'E2E-3'))
SECONDS = {'parse': 60, 'compile': 600, 'host': 600, 'call': 60}


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text(data: bytes) -> str:
    return data.decode('utf-8', 'backslashreplace')


def run(argv, timeout, stdin=None):
    """Raw bytes; a timeout is exhaustion, a signal keeps its negative exit."""
    argv = [str(x) for x in argv]
    try:
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=timeout, input=stdin)
        return {'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except subprocess.TimeoutExpired:
        return {'argv': argv, 'exit': None, 'outcome': 'Exhausted', 'budget_seconds': timeout,
                'stdout': b'', 'stderr': b''}


def shown(obs) -> dict:
    """Receipt form of an observation: text, no host paths."""
    row = {'argv': obs['argv'], 'exit': obs['exit'], 'stdout': text(obs['stdout']), 'stderr': text(obs['stderr'])}
    row.update({k: obs[k] for k in ('outcome', 'budget_seconds') if k in obs})
    return row


def successful(argv, timeout=SECONDS['compile']):
    obs = run(argv, timeout)
    require(obs['exit'] == 0, shown(obs))
    return obs


# ---------------------------------------------------------------- the verdict

def outcome(obs) -> str:
    """Classification from recorded exit and stderr only; they must agree."""
    if obs.get('exit') is None:
        return 'Exhausted' if obs.get('outcome') == 'Exhausted' else 'HostCrash'
    if obs['exit'] == 0:
        return 'Success'
    word = obs['stderr'].split('\t', 1)[0]
    expected = OUTCOMES.get(obs['exit'])
    if expected is None:
        return 'HostCrash'
    return expected if word == expected else 'Unclassified'


def judge(progress) -> list[str]:
    """Gate verdict over recorded fields: reached stages agree exactly; blocked
    stages report Unsupported or Exhausted; Knot never calls its own source Invalid."""
    violations = []
    stages = progress.get('stages', [])
    if [(s.get('id'), s.get('tier')) for s in stages] != list(STAGES):
        return ['stage list differs from the fixed pipeline']
    seen = {}
    for s in stages:
        sid, status = s['id'], s['status']
        if status == 'reached':
            if s['corpus'] <= 0 or s['disagree'] != 0 or s['agree'] != s['corpus']:
                violations.append(f"{sid}: reached without exact agreement ({s['agree']}/{s['corpus']}, {s['disagree']} disagree)")
        elif status == 'blocked':
            kind = outcome(s['blocker'])
            if kind not in ALLOWED:
                violations.append(f"{sid}: {s['blocker']['source']} blocker is {kind}; only Unsupported or Exhausted may block")
            if s['disagree'] != 0:
                violations.append(f"{sid}: blocked stage also disagrees on {s['disagree']} inputs")
        elif status == 'not-run':
            if seen.get(s['prerequisite']) not in ('blocked', 'not-run'):
                violations.append(f"{sid}: not run although prerequisite {s['prerequisite']} is {seen.get(s['prerequisite'], 'absent')}")
            if s['agree'] or s['disagree']:
                violations.append(f'{sid}: not-run stage records comparisons')
        else:
            violations.append(f'{sid}: unknown status {status}')
        seen[sid] = status
    own = progress.get('own_source', [])
    if not own:
        violations.append('own-source observations are missing')
    for row in own:
        kind = outcome(row)
        if kind not in ('Success', *ALLOWED):
            violations.append(f"{row['path']}: Knot's parser reports its own source {kind} (D4)")
    return violations


# ------------------------------------------------------------------- inputs

def corpus() -> list[str]:
    """Tracked plus unignored .bend files: exactly what the gate runner exports.
    Inside the runner's scratch (no .git of its own) walk the exported tree."""
    top = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
    if top.returncode == 0 and Path(top.stdout.strip()).resolve() == ROOT:
        listed = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z', '--cached', '--others',
                                          '--exclude-standard', '--', '*.bend'])
        names = [os.fsdecode(n) for n in listed.split(b'\0') if n]
    else:
        names = []
        for folder, dirs, files in os.walk(ROOT):
            if Path(folder) == ROOT:
                dirs[:] = [d for d in dirs if d not in EXCLUDED]
            names += [(Path(folder) / f).relative_to(ROOT).as_posix() for f in files if f.endswith('.bend')]
    names = sorted({n for n in names if n.split('/')[0] not in EXCLUDED
                    and not any(p == '.env' or p.startswith('.env.') for p in n.split('/'))
                    and (ROOT / n).is_file()})
    require(names, 'empty corpus')
    return names


IMPORT = re.compile(r'^import\s+(\S+)(?:\s+as\s+\S+)?\s*$')


def bundle(entry: str) -> dict:
    """The frozen source bundle S: an entry's transitive imports with hashes."""
    library = Path(os.environ.get('BEND_LIB', str(Path.home() / '.bend/lib'))).expanduser()
    files, pending, unresolved = {}, [entry], set()
    while pending:
        name = pending.pop()
        if name in files:
            continue
        data = (library / name if name.startswith('0x') else ROOT / name).read_bytes()
        files[name] = digest(data)
        for line in data.decode().splitlines():
            match = IMPORT.match(line)
            if not match:
                continue
            spec = match[1]
            if spec == 'Base':
                pending.append(BASE)
            elif spec.startswith(('./', '../')):
                pending.append(posixpath.normpath(posixpath.join(posixpath.dirname(name), spec)))
            elif re.fullmatch(r'0x[0-9a-f]+/[^/]+\.bend', spec):
                pending.append(spec)
            else:
                unresolved.add(spec)
    return {'entry': entry, 'files': dict(sorted(files.items())), 'unresolved': sorted(unresolved)}


# -------------------------------------------------------------- comparisons

def observe_all(command, names):
    with ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(lambda n: run([*command, n], SECONDS['parse']), names))


def identity(obs):
    return (obs['exit'], digest(obs['stdout']), digest(obs['stderr']))


def compare(names, expected, actual) -> dict:
    """Byte identity of (exit, stdout, stderr); host exhaustion is inconclusive."""
    tally = {'agree': 0, 'disagree': 0, 'exhausted': 0, 'first_disagreement': None, 'first_exhausted': None}
    for name, want, got in zip(names, expected, actual, strict=True):
        if got['exit'] is None or want['exit'] is None or (got.get('host') and got['exit'] == 4):
            tally['exhausted'] += 1
            tally['first_exhausted'] = tally['first_exhausted'] or {'path': name, **shown(got)}
        elif identity(want) == identity(got):
            tally['agree'] += 1
        else:
            tally['disagree'] += 1
            tally['first_disagreement'] = tally['first_disagreement'] or {
                'path': name, 'expected': shown(want), 'actual': shown(got)}
    return tally


def stage(sid, **fields):
    tier = dict(STAGES)[sid]
    return {'id': sid, 'tier': tier, **fields}


def not_run(sid, prerequisite, corpus_size):
    return stage(sid, status='not-run', prerequisite=prerequisite, corpus=corpus_size, agree=0, disagree=0)


def blocked(sid, source, obs, corpus_size, **extra):
    return stage(sid, status='blocked', corpus=corpus_size, agree=extra.pop('agree', 0), disagree=0,
                 blocker={'source': source, **shown(obs)}, **extra)


def budgets():
    limits = json.loads((ROOT / 'src/CONTRACT.json').read_bytes())['compiler']['maximum_overrides']
    return [limits[k] for k in ('characters', 'parser_depth', 'checker_depth', 'emitter_depth', 'output_bytes')]


def built(obs, out: Path) -> bool:
    return (obs['exit'] == 0 and out.is_file() and out.read_bytes()[:4] == b'\0asm'
            and text(obs['stdout']).strip() == f'Built\t{out.stat().st_size}')


def compile_stage(sid, compiler, entry, out: Path):
    """C1 compiles one bundle entry. No seed fallback runs inside this step."""
    out.unlink(missing_ok=True)
    obs = run([*compiler, entry, out.relative_to(ROOT).as_posix(), *budgets()], SECONDS['compile'])
    if obs['exit'] != 0:
        return blocked(sid, 'knot', obs, 1, artifact_created=out.exists())
    ok = built(obs, out)
    return stage(sid, status='reached', corpus=1, agree=int(ok), disagree=int(not ok),
                 result=shown(obs), artifact_sha256=digest(out.read_bytes()) if out.is_file() else None)


def host(module: Path, runs, label):
    """One batched host request. Returns (answer, observations), or (answer or
    None, blocker) when the module cannot run; a crashed host is never hidden."""
    request = ROOT / BUILD / f'host-{label}.json'
    request.write_text(json.dumps({'abi': 'auto', 'module': module.relative_to(ROOT).as_posix(), 'runs': runs}))
    obs = run(['node', HOST, request.relative_to(ROOT).as_posix()], SECONDS['host'])
    try:
        require(obs['exit'] == 0, 'host exit')
        answer = json.loads(obs['stdout'])
    except (AssertionError, ValueError):
        return None, {**obs, 'source': 'harness'}
    if answer['blocked']:
        b = answer['blocked']
        return answer, {'argv': obs['argv'], 'exit': b['exit'], 'stdout': b['stdout'].encode(),
                        'stderr': b['stderr'].encode(), 'source': b['source']}
    decode = lambda run_, r: {'argv': run_['argv'], 'exit': r['exit'], 'host': r.get('host', False),
                              'stdout': base64.b64decode(r['stdout']), 'stderr': base64.b64decode(r['stderr']),
                              'files': {k: base64.b64decode(v) for k, v in r.get('files', {}).items()}}
    return answer, [decode(run_, r) for run_, r in zip(runs, answer['runs'], strict=True)]


def module_runner(module: Path, label, inputs=None):
    """A_n as a compiler: argv [source, output]; the host returns declared outputs
    and the harness materializes them, so stale files never count."""
    def compile_one(source, out: Path):
        out.unlink(missing_ok=True)
        output = out.relative_to(ROOT).as_posix()
        answer, result = host(module, [{'argv': [source, output], 'inputs': inputs or [source],
                                        'outputs': [output]}], label)
        if answer is None or answer['blocked']:
            return {'blocked': True, **result}
        got = result[0]
        if output in got['files']:
            out.write_bytes(got['files'][output])
        return got
    return compile_one


def conformance(compile_one, reference_modules=None) -> dict:
    """The existing gate corpus: seed-derived call tags and fixed rejections."""
    programs = json.loads((ROOT / PROGRAMS).read_bytes())['cases']
    rejects = [c for c in json.loads((ROOT / REJECTS).read_bytes())['cases'] if c['knot']['exit'] != 0]
    folder = ROOT / BUILD / 'conformance'
    folder.mkdir(parents=True, exist_ok=True)
    tally = {'programs': len(programs), 'calls': sum(len(c['calls']) for c in programs), 'rejects': len(rejects),
             'agree': 0, 'disagree': 0, 'first_disagreement': None, 'modules': {}, 'blocked': None}

    def verdict(ok, case, detail):
        tally['agree' if ok else 'disagree'] += 1
        if not ok and tally['first_disagreement'] is None:
            tally['first_disagreement'] = {'file': case['file'], **detail}

    for case in programs:
        name = Path(case['file']).stem
        out = folder / f'{name}.wasm'
        obs = compile_one(case['file'], out)
        if obs.get('blocked'):
            tally['blocked'] = obs
            return tally
        ok = built(obs, out)
        detail = {'compile': shown(obs)}
        if ok:
            tally['modules'][name] = digest(out.read_bytes())
            if reference_modules is not None and reference_modules.get(name) != tally['modules'][name]:
                ok, detail['module'] = False, 'bytes differ from C1'
        for call in case['calls'] if ok else ():
            r = run(['node', RUN_WASM, out.relative_to(ROOT).as_posix(), call['export'], *call['arguments']], SECONDS['call'])
            try:
                good = r['exit'] == 0 and json.loads(r['stdout'])['result'] == call['tag']
            except ValueError:
                good = False
            if not good:
                ok, detail['call'] = False, {'call': call, **shown(r)}
                break
        verdict(ok, case, detail)
    for case in rejects:
        out = folder / 'reject.wasm'
        obs = compile_one(case['file'], out)
        if obs.get('blocked'):
            tally['blocked'] = obs
            return tally
        want = case['knot']
        ok = (obs['exit'] == want['exit'] and obs['stdout'] == b''
              and text(obs['stderr']).startswith(want['diagnostic']) and not out.exists())
        verdict(ok, case, {'expected': want, 'actual': shown(obs)})
    return tally


# ------------------------------------------------------------ Wasm controls

def leb(n: int) -> bytes:
    out = bytearray()
    while True:
        byte, n = n & 127, n >> 7
        out.append(byte | (128 if n else 0))
        if not n:
            return bytes(out)


def section(sid: int, *items: bytes) -> bytes:
    body = leb(len(items)) + b''.join(items)
    return bytes([sid]) + leb(len(body)) + body


def name(s: str) -> bytes:
    return leb(len(s)) + s.encode()


def replay_module(obs) -> bytes:
    """Test double for knot-bytes-0: returns one fixed observation. Not a parser."""
    record = (obs['exit'].to_bytes(4, 'little') + len(obs['stdout']).to_bytes(4, 'little')
              + len(obs['stderr']).to_bytes(4, 'little') + obs['stdout'] + obs['stderr'])
    require(len(record) < 4096, 'replay record fits below the input region')
    constant = lambda value: b'\x00\x41' + value + b'\x0b'  # no locals; i32.const; end
    code = lambda body: leb(len(body)) + body
    return (b'\0asm\x01\0\0\0' + section(1, b'\x60\x01\x7f\x01\x7f') + section(3, b'\x00', b'\x00')
            + section(5, b'\x00\x01')
            + section(7, name('memory') + b'\x02\x00', name('knot_input') + b'\x00\x00', name('knot_run') + b'\x00\x01')
            + section(10, code(constant(b'\x80\x20')), code(constant(b'\x00')))
            + section(11, b'\x00\x41\x00\x0b' + leb(len(record)) + record))


def importing_module() -> bytes:
    return (b'\0asm\x01\0\0\0' + section(1, b'\x60\x00\x00')
            + section(2, name('knot') + name('io') + b'\x00\x00'))


def controls(names, native, bun) -> list[dict]:
    """Self-tests of the comparator and host seam. Test doubles, not Knot evidence."""
    result = []
    folder = ROOT / BUILD / 'controls'
    folder.mkdir(parents=True, exist_ok=True)
    perturbed = [dict(o) for o in bun]
    perturbed[0]['stderr'] = bytes([perturbed[0]['stderr'][0] ^ 1]) + perturbed[0]['stderr'][1:] if perturbed[0]['stderr'] \
        else b'\n'
    tally = compare(names, native, perturbed)
    result.append({'name': 'comparator-one-byte', 'expected': {'agree': len(names) - 1, 'disagree': 1},
                   'observed': {'agree': tally['agree'], 'disagree': tally['disagree']}})
    # Replay the first own-source observation; any file with other bytes must disagree.
    first = next(i for i, n in enumerate(names) if n.startswith('src/'))
    other = next(i for i, o in enumerate(native) if identity(o) != identity(native[first]))
    module = folder / 'replay.wasm'
    module.write_bytes(replay_module(native[first]))
    picked = [names[first], names[other]]
    answer, got = host(module, [{'argv': [n], 'inputs': [n], 'outputs': []} for n in picked], 'control-replay')
    tally = compare(picked, [native[first], native[other]], got) if answer and not answer['blocked'] else {}
    result.append({'name': 'host-bytes-abi-replay', 'expected': {'abi': 'knot-bytes-0', 'agree': 1, 'disagree': 1},
                   'observed': {'abi': answer and answer['abi'], 'agree': tally.get('agree'), 'disagree': tally.get('disagree')}})
    for label, data, expected in (
            ('host-io-seam', importing_module(),
             {'abi': 'knot-io', 'outcome': 'Unsupported' if not (HERE / 'io-abi.mjs').exists() else None}),
            ('host-invalid-module', b'\0asm\x01\0\0\0\xff', {'abi': None, 'outcome': 'HostFailure'})):
        module = folder / f'{label}.wasm'
        module.write_bytes(data)
        answer, got = host(module, [], label)
        result.append({'name': label, 'expected': expected, 'observed': {
            'abi': answer and answer['abi'],
            'outcome': outcome(shown(got)) if answer and answer['blocked'] else None}})
    return result


# --------------------------------------------------------------- mutants

def mutants(progress) -> list[dict]:
    """Scratch copies with substituted recorded classifications; the judge must reject each."""
    folder = ROOT / BUILD / 'judge'
    folder.mkdir(parents=True, exist_ok=True)

    def knot_blocker(p):
        s = next((s for s in p['stages'] if s['status'] == 'blocked' and s['blocker']['source'] == 'knot'), None)
        if s is None:  # Nothing blocked any more: substitute into the A2 stage.
            s = next(s for s in p['stages'] if s['id'] == 'e2e3.a2')
            s.update(status='blocked', agree=0, disagree=0, blocker={'source': 'knot', 'exit': 3, 'stdout': '',
                     'stderr': 'Unsupported\tlex\tliteral\t0:1:1:1\n'})
        return s['blocker']

    def invalid(row, exit=True, word=True):
        if exit:
            row['exit'] = 2
        if word:
            row['stderr'] = 'Invalid\t' + row['stderr'].split('\t', 1)[-1]

    def disagree(p):
        s = next(s for s in p['stages'] if s['status'] == 'reached')
        s['agree'] -= 1
        s['disagree'] += 1

    def silent_skip(p):
        s = next((s for s in p['stages'] if s['status'] == 'not-run'), None)
        if s is None:
            return False
        pre = next(x for x in p['stages'] if x['id'] == s['prerequisite'])
        pre.update(status='reached', agree=pre['corpus'], disagree=0)
        pre.pop('blocker', None)

    cases = (
        ('unmutated', 0, lambda p: None),
        ('blocker-invalid', 1, lambda p: invalid(knot_blocker(p))),
        ('blocker-invalid-word-only', 1, lambda p: invalid(knot_blocker(p), exit=False)),
        ('blocker-invalid-exit-only', 1, lambda p: invalid(knot_blocker(p), word=False)),
        ('blocker-host-crash', 1, lambda p: knot_blocker(p).update(
            exit=1, stderr='error: uncaught RuntimeError: unreachable\n    at main\n')),
        ('blocker-signal', 1, lambda p: knot_blocker(p).update(exit=-11, stderr='')),
        ('own-source-invalid', 1, lambda p: invalid(p['own_source'][0])),
        ('reached-disagreement', 1, disagree),
        ('not-run-after-reached', 1, silent_skip),
    )
    result = []
    for label, expected, mutate in cases:
        scratch = copy.deepcopy(progress)
        if mutate(scratch) is False:
            result.append({'name': label, 'applicable': False})
            continue
        path = folder / f'{label}.json'
        path.write_text(json.dumps(scratch, indent=2) + '\n')
        r = run([sys.executable, '-B', f'{REL}/check.py', '--judge', path.relative_to(ROOT).as_posix()], 60)
        result.append({'name': label, 'expected_exit': expected, 'exit': r['exit'],
                       'violations': text(r['stdout']).splitlines(),
                       'outcome': 'rejected' if r['exit'] == 1 else 'accepted' if r['exit'] == 0 else 'error'})
    return result


# ------------------------------------------------------------------- main

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--judge', metavar='RECEIPT', help='apply the gate verdict to a recorded progress receipt')
    args = parser.parse_args()
    if args.judge:
        violations = judge(json.loads(Path(args.judge).read_bytes()))
        print('\n'.join(violations) if violations else 'Judge passed')
        return 1 if violations else 0

    shutil.rmtree(ROOT / BUILD, ignore_errors=True)  # A stale artifact can never count.
    (ROOT / BUILD).mkdir(parents=True)
    contract = json.loads((ROOT / 'src/CONTRACT.json').read_bytes())
    progress = {'schema': 1, 'status': 'incomplete', 'harness': f'{REL}/check.py',
                'seed': contract['seed'], 'compiler_entry': COMPILER, 'parser_entry': PARSER}
    reference = {'schema': 1, 'reference': f'seed-built {PARSER}, native and Bun lanes', 'files': []}
    code = 1
    try:
        progress['tools'] = {t: text(successful([t, '--version'], 60)['stdout']).strip() for t in ('bun', 'node')}
        progress['inputs'] = {p: digest((ROOT / p).read_bytes()) for p in sorted(
            [f'{REL}/check.py', HOST, RUN_WASM, SEED, 'src/CONTRACT.json', PROGRAMS, REJECTS,
             *[f'{REL}/io-abi.mjs'] * (HERE / 'io-abi.mjs').exists()])}
        progress['bundles'] = {entry: bundle(entry) for entry in (PARSER, COMPILER)}

        # The seed step: the only seed invocations in the pipeline.
        build = {'parse-cli': [PARSER, f'{BUILD}/parse-cli'], 'parse-cli.js': [PARSER, f'{BUILD}/parse-cli.js'],
                 'C1': [COMPILER, f'{BUILD}/c1']}
        progress['seed_builds'] = {}
        for label, (entry, out) in build.items():
            obs = successful([SEED, entry, '-o', out])
            progress['seed_builds'][label] = {'entry': entry, 'lane': 'bun' if out.endswith('.js') else 'native',
                                              'sha256': digest((ROOT / out).read_bytes())}
        c1 = [f'./{BUILD}/c1']

        # E2E-2 reference corpus: the seed is the oracle.
        names = corpus()
        native = observe_all([f'./{BUILD}/parse-cli'], names)
        bun = observe_all(['bun', f'{BUILD}/parse-cli.js'], names)
        lanes = compare(names, native, bun)
        outcomes = {}
        for n, obs in zip(names, native):
            kind = 'Parsed' if obs['exit'] == 0 else '\t'.join(text(obs['stderr']).split('\t')[:3]).strip()
            outcomes[kind] = outcomes.get(kind, 0) + 1
            reference['files'].append({'path': n, 'sha256': digest((ROOT / n).read_bytes()), 'exit': obs['exit'],
                                       'stdout_sha256': digest(obs['stdout']), 'stderr_sha256': digest(obs['stderr'])})
        progress['own_source'] = [{'path': n, 'exit': o['exit'], 'stderr': text(o['stderr'])}
                                  for n, o in zip(names, native) if re.fullmatch(r'src/[^/]+\.bend', n)]
        reference_bytes = json.dumps(reference, indent=2).encode() + b'\n'
        progress['corpus'] = {'files': len(names), 'reference_sha256': digest(reference_bytes)}
        stages = [stage('e2e2.reference', status='reached', corpus=len(names), agree=lanes['agree'],
                        disagree=lanes['disagree'] + lanes['exhausted'], lanes=['native', 'bun'],
                        first_disagreement=lanes['first_disagreement'],
                        outcomes=dict(sorted(outcomes.items(), key=lambda kv: (-kv[1], kv[0]))))]

        # E2E-2 Knot path: C1 compiles the parser; its module must reproduce the corpus.
        parser_module = ROOT / BUILD / 'parse-cli.wasm'
        compiled = compile_stage('e2e2.compile', c1, PARSER, parser_module)
        stages.append(compiled)
        if compiled['status'] != 'reached' or compiled['disagree']:
            stages.append(not_run('e2e2.self-parse', 'e2e2.compile', len(names)))
        else:
            answer, got = host(parser_module, [{'argv': [n], 'inputs': [n], 'outputs': []} for n in names], 'self-parse')
            if answer is None or answer['blocked']:
                stages.append(blocked('e2e2.self-parse', got.pop('source'), got, len(names),
                                      abi=answer and answer['abi']))
            else:
                t = compare(names, native, got)
                fields = dict(corpus=len(names), agree=t['agree'], disagree=t['disagree'], abi=answer['abi'],
                              first_disagreement=t['first_disagreement'])
                if t['exhausted'] and not t['disagree']:
                    first = t['first_exhausted']
                    stages.append(stage('e2e2.self-parse', status='blocked', exhausted=t['exhausted'],
                                        blocker={'source': 'knot', **first}, **fields))
                else:
                    stages.append(stage('e2e2.self-parse', status='reached', exhausted=t['exhausted'], **fields))

        # E2E-3: seed -> C1 -> A2 -> A3. C1 must already pass the conformance corpus.
        base = conformance(lambda source, out: run([*c1, source, out.relative_to(ROOT).as_posix()], SECONDS['compile']))
        cases = base['programs'] + base['rejects']
        stages.append(stage('e2e3.c1', status='reached', corpus=cases, agree=base['agree'], disagree=base['disagree'],
                            lane='native', first_disagreement=base['first_disagreement'],
                            programs=base['programs'], calls=base['calls'], rejects=base['rejects'],
                            modules=base['modules']))
        a2, a3 = ROOT / BUILD / 'a2.wasm', ROOT / BUILD / 'a3.wasm'
        stage_a2 = compile_stage('e2e3.a2', c1, COMPILER, a2)
        stages.append(stage_a2)
        if stage_a2['status'] != 'reached' or stage_a2['disagree']:
            stages += [not_run('e2e3.a3', 'e2e3.a2', 1), not_run('e2e3.fixpoint', 'e2e3.a3', 1),
                       not_run('e2e3.conformance', 'e2e3.a3', 2 * cases)]
        else:
            got = module_runner(a2, 'a3', list(progress['bundles'][COMPILER]['files']))(COMPILER, a3)
            if got.get('blocked'):
                stages.append(blocked('e2e3.a3', got.pop('source'), got, 1))
            elif got['exit'] != 0:
                stages.append(blocked('e2e3.a3', 'knot', got, 1))
            else:
                ok = built(got, a3)
                stages.append(stage('e2e3.a3', status='reached', corpus=1, agree=int(ok), disagree=int(not ok),
                                    result=shown(got), artifact_sha256=digest(a3.read_bytes()) if a3.is_file() else None))
            if stages[-1]['status'] != 'reached' or stages[-1]['disagree']:
                stages += [not_run('e2e3.fixpoint', 'e2e3.a3', 1), not_run('e2e3.conformance', 'e2e3.a3', 2 * cases)]
            else:
                same = a2.read_bytes() == a3.read_bytes()
                stages.append(stage('e2e3.fixpoint', status='reached', corpus=1, agree=int(same), disagree=int(not same)))
                runs = {g: conformance(module_runner(m, g), base['modules']) for g, m in (('a2', a2), ('a3', a3))}
                stop = next((r['blocked'] for r in runs.values() if r['blocked']), None)
                if stop:
                    stages.append(blocked('e2e3.conformance', stop.pop('source'), stop, 2 * cases))
                else:
                    stages.append(stage('e2e3.conformance', status='reached', corpus=2 * cases,
                                        agree=sum(r['agree'] for r in runs.values()),
                                        disagree=sum(r['disagree'] for r in runs.values()),
                                        generations={g: {k: r[k] for k in ('agree', 'disagree', 'first_disagreement')}
                                                     for g, r in runs.items()}))
        progress['stages'] = stages
        progress['tiers'] = {}
        for tier in ('E2E-2', 'E2E-3'):
            rows = [s for s in stages if s['tier'] == tier]
            first = next((s for s in rows if s['status'] == 'blocked'), None)
            progress['tiers'][tier] = {
                'reached': [s['id'] for s in rows if s['status'] == 'reached'],
                'first_blocker': first and {'stage': first['id'], 'source': first['blocker']['source'],
                                            'classification': first['blocker']['stderr'].strip()}}

        progress['controls'] = controls(names, native, bun)
        progress['mutants'] = mutants(progress)
        violations = judge(progress)
        failed_controls = [c['name'] for c in progress['controls'] if c['expected'] != {
            k: c['observed'][k] for k in c['expected']}]
        surviving = [m['name'] for m in progress['mutants']
                     if m.get('applicable', True) and m['exit'] != m['expected_exit']]
        progress['verdict'] = {'violations': violations, 'failed_controls': failed_controls,
                               'surviving_mutants': surviving}
        if not (violations or failed_controls or surviving):
            progress['status'] = 'passed'
            code = 0
    except Exception as error:
        progress['failure'] = repr(error)
        raise
    finally:
        PROGRESS.parent.mkdir(parents=True, exist_ok=True)
        PROGRESS.write_text(json.dumps(progress, indent=2) + '\n')
        if reference['files']:
            REFERENCE.write_text(json.dumps(reference, indent=2) + '\n')
    for s in progress['stages']:
        blocker = s.get('blocker')
        detail = (blocker['stderr'].strip() if blocker else f"after {s['prerequisite']}" if s['status'] == 'not-run'
                  else f"{s['agree']}/{s['corpus']} agree")
        print(f"{s['id']:<18} {s['status']:<8} {detail}")
    print(f"Bootstrap harness {progress['status']}: {progress['corpus']['files']} corpus files; "
          f"{len(progress['mutants'])} judge mutants; {len(progress['controls'])} controls. {PROGRESS.relative_to(ROOT)}")
    for line in progress['verdict']['violations'] + progress['verdict']['failed_controls'] + progress['verdict']['surviving_mutants']:
        print('FAIL', line, file=sys.stderr)
    return code


if __name__ == '__main__':
    sys.exit(main())
