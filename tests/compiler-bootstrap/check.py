#!/usr/bin/env python3
"""E2E-2 self-parse and E2E-3 fixpoint harness. Host only: it builds with the
seed, invokes compilers and modules, and compares bytes. No compiler semantics.

Every compiler generation is produced from one frozen bundle and one argv:
each step runs inside a staged sandbox of copied regular files, under a
recorded generation contract that the judge requires to be identical for
C1 -> A2 and A2 -> A3. See README.md.

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
import math
import os
from pathlib import Path
import platform
import posixpath
import re
import resource
import shutil
import stat
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REL = HERE.relative_to(ROOT).as_posix()
BUILD = '.local/compiler-bootstrap'
SEED = 'scripts/bend-reference'
HOST = f'{REL}/host.mjs'
RUN_WASM = 'scripts/run-wasm.mjs'
MANIFEST = HERE / 'manifest.json'
PROGRESS = HERE / 'receipts/progress.json'
REFERENCE = HERE / 'receipts/reference.json'
PARSER = 'src/parse-cli.bend'      # E2E-2 subject
COMPILER = 'src/compile-cli.bend'  # the one compiler entry for C1, A2 and A3
CHECKER = 'src/check-cli.bend'    # the loader audit (--audit-bundle), built only when advertised
PROGRAMS = 'tests/compiler-wasm/cases.json'
REJECTS = 'tests/compiler-checker/cases.json'
OUTCOMES = {2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted', 5: 'HostFailure', 6: 'InternalFailure'}
ALLOWED = ('Unsupported', 'Exhausted')
EXCLUDED = ('.git', '.local', '.toolchain', 'node_modules', 'build')
STAGES = (('e2e2.reference', 'E2E-2'), ('e2e2.compile', 'E2E-2'), ('e2e2.self-parse', 'E2E-2'),
          ('e2e3.c1', 'E2E-3'), ('e2e3.a2', 'E2E-3'), ('e2e3.a3', 'E2E-3'),
          ('e2e3.fixpoint', 'E2E-3'), ('e2e3.conformance', 'E2E-3'))
GENERATIONS = ('e2e3.a2', 'e2e3.a3')  # C1 -> A2 and A2 -> A3: one contract
LIB = 'lib'                # the relative bundle ROOT inside every sandbox
OUTPUT = 'generation.wasm'  # the one output operand of every generation step
SANDBOX = {COMPILER: 'bundle', PARSER: 'parser-bundle', CHECKER: 'checker-bundle'}
# Exhausted observations the host makes itself, by (phase, code).
HOST_EXHAUSTION = {('wasm', 'call-stack'): 'host-stack', ('wasm', 'memory'): 'host-memory'}


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def timeout_scale() -> float:
    value = float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE') or 1)
    require(math.isfinite(value) and value > 0, 'KNOT_GATE_TIMEOUT_SCALE must be a positive number')
    return value


# Wall-clock guards only catch hangs; they scale with host load (FX-08).
SECONDS = {k: v * timeout_scale() for k, v in
           {'parse': 60, 'compile': 600, 'host': 600, 'call': 60, 'tool': 60}.items()}
# Children never inherit Node preload options or a C compiler override: either
# would silently change the recorded runtime or build identity.
ENV = {**{k: v for k, v in os.environ.items() if k not in ('NODE_OPTIONS', 'CC')}, 'BEND_NO_TELEMETRY': '1'}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def text(data: bytes) -> str:
    return data.decode('utf-8', 'backslashreplace')


def run(argv, timeout, cwd: Path = ROOT, env=None):
    """Raw bytes; a timeout is exhaustion, a signal keeps its negative exit.
    Wall time and peak RSS come from this child's own rusage."""
    argv = [str(x) for x in argv]
    start = time.monotonic()
    child = subprocess.Popen(argv, cwd=cwd, env=env or ENV, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    streams = {}
    readers = [threading.Thread(target=lambda n=n: streams.__setitem__(n, getattr(child, n).read()))
               for n in ('stdout', 'stderr')]
    for reader in readers:
        reader.start()
    lock, state = threading.Lock(), {'reaped': False, 'expired': False}

    def expire():
        with lock:
            if not state['reaped']:
                state['expired'] = True
                child.kill()
    timer = threading.Timer(timeout, expire)
    timer.start()
    _, status, usage = os.wait4(child.pid, 0)
    with lock:
        state['reaped'] = True
    timer.cancel()
    child.returncode = os.waitstatus_to_exitcode(status)
    for reader in readers:
        reader.join()
    if state['expired']:
        return {'argv': argv, 'exit': None, 'outcome': 'Exhausted', 'budget_seconds': timeout,
                'stdout': b'', 'stderr': b''}
    return {'argv': argv, 'exit': child.returncode, 'stdout': streams['stdout'], 'stderr': streams['stderr'],
            'elapsed_seconds': round(time.monotonic() - start, 3),
            'peak_rss_bytes': usage.ru_maxrss * (1 if sys.platform == 'darwin' else 1024)}


def shown(obs) -> dict:
    """Receipt form of an observation: text, no host paths, no timings."""
    row = {'argv': obs['argv'], 'exit': obs['exit'], 'stdout': text(obs['stdout']), 'stderr': text(obs['stderr'])}
    row.update({k: obs[k] for k in ('outcome', 'budget_seconds', 'host') if k in obs})
    return row


def successful(argv, timeout=SECONDS['compile'], cwd: Path = ROOT, env=None):
    obs = run(argv, timeout, cwd, env)
    require(obs['exit'] == 0, shown(obs))
    return obs


def relative(path: Path, cwd: Path) -> str:
    return os.path.relpath(path, cwd)


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


def exhaustion(obs) -> str | None:
    """Which budget an Exhausted observation ran out of, from recorded fields
    only: Knot's own declared budget, or the host's stack, memory or time."""
    if outcome(obs) != 'Exhausted':
        return None
    if obs.get('exit') is None:
        return 'host-time'
    if obs.get('host'):
        return HOST_EXHAUSTION.get(tuple(obs['stderr'].rstrip('\n').split('\t')[1:]), 'host-unclassified')
    return 'knot-budget'


def reserved_in(argv, manifest) -> list[str]:
    return sorted(set(argv) & set(manifest['reserved_flags']['flags']))


def pin_of(place: str, manifest) -> str | None:
    if place == manifest['base']['path']:
        return manifest['base']['sha256']
    if place.startswith(f'{LIB}/'):
        return manifest['packages'].get(place[len(LIB) + 1:])
    return None


def bundle_problems(bundle, manifest) -> list[str]:
    """A staged bundle is copied regular single-link files inside its sandbox,
    Base and every hash package equal to their pins (FX-04, FX-05, A2H-08)."""
    problems = [f"unresolved imports {bundle['unresolved']}"] if bundle.get('unresolved') else []
    files = bundle.get('files', {})
    if sorted(bundle.get('order', [])) != sorted(files):
        problems.append('closure order and staged files differ')
    for place, f in files.items():
        if f.get('kind') != 'regular' or f.get('links') != 1:
            problems.append(f"{place} is not a regular single-link file ({f.get('kind')}, {f.get('links')} links)")
        if place.startswith(('/', '../')) or '/../' in place:
            problems.append(f'{place} escapes the sandbox')
        pin = pin_of(place, manifest)
        if pin is None and place.startswith(f'{LIB}/'):
            problems.append(f'{place} is an unpinned package file')
        elif pin is not None and f.get('sha256') != pin:
            problems.append(f'{place} differs from its pin')
    return problems


def contract_problems(c, bundle, manifest) -> list[str]:
    """One step's contract: the one argv over the staged closure, on the
    qualified host and the pinned runtime."""
    problems = []
    argv = [*(['--bundle', c['root']] if c['modules'] else []), c['entry'], c['target']['output'], *map(str, c['maxima'])]
    if c['argv'] != argv:
        problems.append(f"argv {c['argv']} is not the one generation argv {argv}")
    if reserved_in(c['argv'], manifest):
        problems.append(f"argv uses seed-reserved flags {reserved_in(c['argv'], manifest)}")
    if bundle is None or c['closure'] != bundle['order'] or c['bundle_sha256'] != digest(canonical(bundle['files'])):
        problems.append('contract closure or bundle digest differs from the staged sandbox')
    if c['host']['system'] != manifest['qualified_host']['system']:
        problems.append(f"host {c['host']['system']} is not the qualified host")
    if c['runtime']['node'] != c['runtime']['required_node']:
        problems.append(f"Node {c['runtime']['node']} is not the pinned {c['runtime']['required_node']}")
    if c['runtime']['memory_maximum'] != manifest['memory_maximum']:
        problems.append('memory maximum differs from the manifest (D19)')
    return problems


def generation_problems(p, manifest) -> list[str]:
    """The generation contract, the staged sandboxes, the loader audit, the
    artifacts and C1's per-case observations, from recorded fields."""
    problems = []
    bundles = p.get('bundles', {})
    for entry, bundle in sorted(bundles.items()):
        problems += [f'{entry}: {x}' for x in bundle_problems(bundle, manifest)]
    contracts = p.get('generation_contract', {})
    if any(sid not in contracts for sid in GENERATIONS):
        return problems + ['generation contract is missing a step']
    if contracts[GENERATIONS[0]] != contracts[GENERATIONS[1]]:
        problems.append('generation contracts differ between e2e3.a2 and e2e3.a3')
    for sid in GENERATIONS:
        c = contracts[sid]
        problems += [f'{sid}: {x}' for x in contract_problems(c, bundles.get(c['entry']), manifest)]
    by_id = {s['id']: s for s in p['stages']}
    for sid in GENERATIONS:
        s, c = by_id[sid], contracts[sid]
        if s['status'] != 'not-run' and s.get('args') != c['argv']:
            problems.append(f'{sid}: argv differs from its generation contract')
        a = s.get('artifact') if s['status'] == 'reached' else None
        if a is not None:
            if a['bytes'] > a['output_bytes'] or a['output_bytes'] != c['target']['output_bytes']:
                problems.append(f"{sid}: artifact of {a['bytes']} bytes exceeds output_bytes {c['target']['output_bytes']}")
            pages = c['runtime']['memory_maximum']['pages']
            if a['memory'] is not None and (a['memory'].get('maximum') is None or a['memory']['maximum'] > pages):
                problems.append(f"{sid}: artifact memory {a['memory']} has no maximum within the declared {pages} pages")
    audit = p.get('audit', {})
    modules = contracts[GENERATIONS[0]]['modules']
    if not modules and audit.get('status') != 'unavailable':
        problems.append('audit recorded although the compiler advertises no module loading')
    if modules and audit.get('status') == 'recorded':
        staged = {x for x in bundles[COMPILER]['order'] if x.endswith('.bend') and x != manifest['base']['path']}
        if set(audit['modules']) != staged:
            problems.append('loader closure (--audit-bundle Module lines) differs from the staged sandbox')
        if audit['trust']['base_pin'] != [manifest['base']['sha256']]:
            problems.append('audit BasePin differs from the pinned Base')
    elif modules and not (audit.get('status') == 'blocked' and outcome(audit['blocker']) in ALLOWED):
        problems.append(f"loader audit is {audit.get('status')}; module loading requires a recorded or blocked audit")
    c1 = by_id['e2e3.c1']
    reference = c1.get('observations') or []
    if len(reference) != c1['corpus']:
        problems.append('e2e3.c1: per-case observations are missing')
    conformance = by_id['e2e3.conformance']
    for g, r in sorted(conformance.get('generations', {}).items()) if conformance['status'] == 'reached' else ():
        rows = r.get('observations', [])
        first = next((a['file'] for a, b in zip(reference, rows) if a != b), None)
        if len(rows) != len(reference) or first:
            problems.append(f"e2e3.conformance: {g} diagnostics differ from C1 at {first or 'the case count'}")
    seed = p.get('seed_builds', {}).get('C1', {})
    if seed.get('sha256') is None or seed.get('sha256') != seed.get('repeat_sha256'):
        problems.append('C1 is not reproducible: two seed builds differ (FX-11)')
    return problems


def judge(progress, manifest=None) -> list[str]:
    """Gate verdict over recorded fields and the fixed manifest: reached stages
    agree exactly; blocked stages report Unsupported or Exhausted; host
    exhaustion after C1 built S is divergent; every generation step shares one
    contract; Knot never calls its own source Invalid."""
    manifest = manifest or json.loads(MANIFEST.read_bytes())
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
            kind, tag = outcome(s['blocker']), exhaustion(s['blocker'])
            if kind not in ALLOWED:
                violations.append(f"{sid}: {s['blocker']['source']} blocker is {kind}; only Unsupported or Exhausted may block")
            if s['blocker'].get('resource') != tag or tag == 'host-unclassified':
                violations.append(f"{sid}: blocker resource tag {s['blocker'].get('resource')} differs from its recorded fields ({tag})")
            if sid == 'e2e3.a3' and seen.get('e2e3.a2') == 'reached' and tag and tag.startswith('host-'):
                violations.append(f'{sid}: blocked by {tag} after C1 built S; must be divergent-exhausted')
            if s['disagree'] != 0:
                violations.append(f"{sid}: blocked stage also disagrees on {s['disagree']} inputs")
        elif status == 'divergent-exhausted':
            violations.append(f"{sid}: divergent-exhausted ({exhaustion(s['blocker'])}) is non-passing: "
                              'A2 ran out of a host resource on the S that C1 built')
        elif status == 'not-run':
            if seen.get(s['prerequisite']) not in ('blocked', 'not-run', 'divergent-exhausted'):
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
    return violations + generation_problems(progress, manifest)


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
FOREIGN = re.compile(r'^\s+import\s+"([^"]+)"\s*$')


def place(name: str) -> str:
    """Sandbox path of a bundle member: hash packages live under the relative ROOT."""
    return f'{LIB}/{name}' if name.startswith('0x') else name


def library_path() -> Path:
    return Path(ENV.get('BEND_LIB', str(Path.home() / '.bend/lib'))).expanduser()


def closure(entry: str, manifest, library: Path) -> dict:
    """The frozen source bundle of one entry: its transitive imports and the
    foreign host files they name, dependency-first. Base is a pinned leaf: the
    seed serves its effect files from its own toolchain, and Knot's loader
    reads only base.bend."""
    order, sources, unresolved = [], {}, set()

    def visit(name, active):
        if name in sources or name in active:
            return
        data = (library / name if name.startswith('0x') else ROOT / name).read_bytes()
        for line in data.decode().splitlines() if name.endswith('.bend') and name != manifest['base']['path'] else ():
            match, foreign = IMPORT.match(line), FOREIGN.match(line)
            spec = match[1] if match else foreign[1] if foreign else None
            if spec is None:
                continue
            if spec == 'Base':
                visit(manifest['base']['path'], active | {name})
            elif spec.startswith(('./', '../')):
                visit(posixpath.normpath(posixpath.join(posixpath.dirname(name), spec)), active | {name})
            elif re.fullmatch(r'0x[0-9a-f]+/[^/]+\.bend', spec):
                visit(spec, active | {name})
            else:
                unresolved.add(spec)
        sources[name] = data
        order.append(name)
    visit(entry, frozenset())
    return {'order': order, 'sources': sources, 'unresolved': sorted(unresolved)}


# ------------------------------------------------------------------ sandbox

def inspect(folder: Path) -> dict:
    """Every non-directory entry of a sandbox, without following links."""
    found = {}
    for top, dirs, files in os.walk(folder, followlinks=False):
        for name in dirs + files:
            path = Path(top) / name
            info = path.lstat()
            if stat.S_ISDIR(info.st_mode):
                continue
            kind = 'regular' if stat.S_ISREG(info.st_mode) else 'symlink' if stat.S_ISLNK(info.st_mode) else 'other'
            found[path.relative_to(folder).as_posix()] = {
                'kind': kind, 'links': info.st_nlink, 'sha256': digest(path.read_bytes()) if kind == 'regular' else None}
    return dict(sorted(found.items()))


def verify(folder: Path, bundle, manifest, outputs=()):
    """The sandbox still holds exactly its staged record, plus declared outputs."""
    seen = {k: v for k, v in inspect(folder).items() if k not in outputs}
    problems = bundle_problems({**bundle, 'files': seen}, manifest)
    if seen != bundle['files']:
        problems.append('sandbox differs from its staged record')
    require(not problems, f"{bundle['sandbox']}: " + '; '.join(problems))


def stage_sandbox(entry: str, folder: Path, manifest, library: Path | None = None) -> dict:
    """Copy one entry's closure into a fresh sandbox; pins fail here, before the seed step."""
    found = closure(entry, manifest, library or library_path())
    shutil.rmtree(folder, ignore_errors=True)
    (folder / LIB).mkdir(parents=True)
    for name in found['order']:
        dest = folder / place(name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(found['sources'][name])
    bundle = {'entry': entry, 'root': LIB, 'sandbox': folder.name, 'order': [place(n) for n in found['order']],
              'files': inspect(folder), 'unresolved': found['unresolved']}
    verify(folder, bundle, manifest)
    return bundle


def replica(source: Path, folder: Path, bundle) -> None:
    """A fresh copy of a staged sandbox: the same files, never links."""
    shutil.rmtree(folder, ignore_errors=True)
    (folder / LIB).mkdir(parents=True)
    for name in bundle['order']:
        (folder / name).parent.mkdir(parents=True, exist_ok=True)
        (folder / name).write_bytes((source / name).read_bytes())


# ---------------------------------------------------------------- contract

def budgets(contract) -> list[int]:
    limits = contract['compiler']['maximum_overrides']
    return [limits[k] for k in ('characters', 'parser_depth', 'checker_depth', 'emitter_depth', 'output_bytes')]


def modules_advertised(contract) -> bool:
    return contract['compiler']['arguments'].startswith('[--bundle ROOT] ')


def generation_argv(contract, manifest, entry: str) -> list[str]:
    """The one argv of every generation step: [--bundle ROOT] entry output maxima.
    --bundle appears once the compiler's CONTRACT advertises module loading."""
    argv = [*(['--bundle', LIB] if modules_advertised(contract) else []), entry, OUTPUT, *map(str, budgets(contract))]
    require(not reserved_in(argv, manifest), f'argv uses seed-reserved flags {reserved_in(argv, manifest)}')
    return argv


def environment(contract, manifest) -> dict:
    """The runtime and build identity every generation step shares (FX-09, FX-11, A2H-14)."""
    node = text(successful(['node', '--version'], SECONDS['tool'])['stdout']).strip().removeprefix('v')
    required = contract['host']['version']
    require(node == required, f'Node {node} is not the pinned {required}')
    system = platform.system()
    require(system == manifest['qualified_host']['system'], f'{system} is not the qualified host')
    options = text(successful(['node', '--v8-options'], SECONDS['tool'])['stdout'])
    stack = re.search(r'default: --stack-size=(\d+)', options)
    require(stack, 'V8 reports no default stack size')
    soft = resource.getrlimit(resource.RLIMIT_STACK)[0]
    clang = text(successful(['clang', '--version'], SECONDS['tool'])['stdout']).splitlines()
    return {
        'runtime': {'engine': 'Node', 'node': node, 'required_node': required, 'node_flags': [],
                    'NODE_OPTIONS': None, 'memory_maximum': manifest['memory_maximum'],
                    'stack': {'v8_stack_size_kb': int(stack[1]),
                              'native_stack_bytes': None if soft == resource.RLIM_INFINITY else soft,
                              'policy': 'V8 default for Knot-built modules; inherited soft limit for the '
                                        'seed-built native C1; the harness sets neither'}},
        'build': {'seed': contract['seed'], 'lane': 'native', 'CC': None,
                  'clang': [line for line in clang if line and not line.startswith('InstalledDir')]},
        'host': {'system': system, 'machine': platform.machine()},
    }


def generation_contract(contract, manifest, bundle, folder: Path, shared) -> dict:
    """What one generation step runs: entry, closure and argv, target, runtime and host.
    The executor is not part of it; each stage records its own."""
    maxima = budgets(contract)
    return {
        'entry': bundle['entry'], 'root': LIB, 'closure': bundle['order'],
        'bundle_sha256': digest(canonical(inspect(folder))),
        'modules': modules_advertised(contract), 'maxima': maxima,
        'argv': generation_argv(contract, manifest, bundle['entry']),
        'target': {'route': 'wasm', 'profile': contract['profile'], 'output': OUTPUT, 'output_bytes': maxima[-1]},
        'conformance_argv': ['<case>', '<output>'],
        **copy.deepcopy(shared),
        'reserved_flags': manifest['reserved_flags']['flags'],
        'excluded_metadata': manifest['excluded_metadata'],
    }


def wasm_memory(data: bytes):
    """Declared memory limits of a Wasm module (defined or imported), in pages;
    None when it has no memory."""
    def leb(at):
        value = shift = 0
        while True:
            byte = data[at]
            value, at, shift = value | (byte & 127) << shift, at + 1, shift + 7
            if byte < 128:
                return value, at

    def limits(at):
        flags, at = leb(at)
        minimum, at = leb(at)
        maximum, at = leb(at) if flags & 1 else (None, at)
        return {'minimum': minimum, 'maximum': maximum}, at

    at = 8
    try:
        while at < len(data):
            sid, (size, body) = data[at], leb(at + 1)
            if sid == 5 and leb(body)[0]:
                return limits(leb(body)[1])[0]
            if sid == 2:
                count, cursor = leb(body)
                for _ in range(count):
                    for _ in range(2):  # module and field names
                        length, cursor = leb(cursor)
                        cursor += length
                    kind, cursor = data[cursor], cursor + 1
                    if kind == 2:
                        return limits(cursor)[0]
                    # function: type index; table: reftype, limits; global: type, mutability; tag: flag, type index
                    cursor = (leb(cursor)[1] if kind == 0 else limits(cursor + 1)[1] if kind == 1
                              else cursor + 2 if kind == 3 else leb(cursor + 1)[1])
            at = body + size
    except IndexError:
        return {'unreadable': True, 'maximum': None}
    return None


def artifact(path: Path, cap: int) -> dict:
    data = path.read_bytes()
    return {'sha256': digest(data), 'bytes': len(data), 'output_bytes': cap,
            'headroom_bytes': cap - len(data), 'memory': wasm_memory(data)}


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


def tagged(row) -> dict:
    """A blocker row with its exhaustion tag, which the judge recomputes."""
    tag = exhaustion(row)
    return {**row, 'resource': tag} if tag else row


def stopped(obs, source) -> dict:
    return tagged({'source': source, **shown(obs)})


def blocked(sid, source, obs, corpus_size, **extra):
    return stage(sid, status='blocked', corpus=corpus_size, agree=extra.pop('agree', 0), disagree=0,
                 blocker=stopped(obs, source), **extra)


def built(obs, out: Path) -> bool:
    return (obs['exit'] == 0 and out.is_file() and out.read_bytes()[:4] == b'\0asm'
            and text(obs['stdout']).strip() == f'Built\t{out.stat().st_size}')


def compile_stage(sid, program: Path, folder: Path, bundle, manifest, argv, keep: Path, cap: int):
    """C1 compiles one bundle entry inside its sandbox. No seed fallback runs here."""
    produced = folder / OUTPUT
    produced.unlink(missing_ok=True)
    keep.unlink(missing_ok=True)
    obs = run([relative(program, folder), *argv], SECONDS['compile'], cwd=folder)
    verify(folder, bundle, manifest, outputs=(OUTPUT,))
    if obs['exit'] != 0:
        return blocked(sid, 'knot', obs, 1, args=argv, artifact_created=produced.exists()), obs
    ok = built(obs, produced)
    if produced.is_file():
        shutil.copyfile(produced, keep)
    return stage(sid, status='reached', corpus=1, agree=int(ok), disagree=int(not ok), args=argv, result=shown(obs),
                 artifact=artifact(produced, cap) if produced.is_file() else None), obs


def host(module: Path, runs, label, cwd: Path = ROOT):
    """One batched host request. Returns (answer, observations), or (answer or
    None, blocker) when the module cannot run; a crashed host is never hidden."""
    request = ROOT / BUILD / f'host-{label}.json'
    request.write_text(json.dumps({'abi': 'auto', 'module': relative(module, cwd), 'runs': runs}))
    obs = run(['node', relative(ROOT / HOST, cwd), relative(request, cwd)], SECONDS['host'], cwd=cwd)
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
                              'files': {k: base64.b64decode(v) for k, v in r.get('files', {}).items()},
                              'peak_rss_bytes': obs['peak_rss_bytes'], 'elapsed_seconds': obs['elapsed_seconds']}
    return answer, [decode(run_, r) for run_, r in zip(runs, answer['runs'], strict=True)]


def module_runner(module: Path, label):
    """A_n as a conformance compiler: argv [source, output], exactly as C1 ran it;
    the host returns declared outputs and the harness materializes them, so
    stale files never count."""
    def compile_one(source, out: Path):
        out.unlink(missing_ok=True)
        output = out.relative_to(ROOT).as_posix()
        answer, result = host(module, [{'argv': [source, output], 'inputs': [source], 'outputs': [output]}], label)
        if answer is None or answer['blocked']:
            return {'blocked': True, **result}
        got = result[0]
        if output in got['files']:
            out.write_bytes(got['files'][output])
        return got
    return compile_one


def observed(file, obs) -> dict:
    """One conformance case's full observation; later generations must repeat C1's byte for byte (FX-18)."""
    row = {'file': file, 'exit': obs['exit'], 'stdout': text(obs['stdout']), 'stderr': text(obs['stderr'])}
    return {**row, 'outcome': obs['outcome']} if 'outcome' in obs else row


def conformance(compile_one, reference=None) -> dict:
    """The existing gate corpus: seed-derived call tags and fixed rejections.
    Against a C1 reference, modules and observations must also equal C1's."""
    programs = json.loads((ROOT / PROGRAMS).read_bytes())['cases']
    rejects = [c for c in json.loads((ROOT / REJECTS).read_bytes())['cases'] if c['knot']['exit'] != 0]
    folder = ROOT / BUILD / 'conformance'
    folder.mkdir(parents=True, exist_ok=True)
    tally = {'programs': len(programs), 'calls': sum(len(c['calls']) for c in programs), 'rejects': len(rejects),
             'agree': 0, 'disagree': 0, 'first_disagreement': None, 'modules': {}, 'blocked': None,
             'observations': []}

    def verdict(ok, case, obs, detail):
        row = observed(case['file'], obs)
        if reference is not None and reference['observations'][len(tally['observations'])] != row:
            ok, detail['observation'] = False, 'differs from C1'
        tally['observations'].append(row)
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
            if reference is not None and reference['modules'].get(name) != tally['modules'][name]:
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
        verdict(ok, case, obs, detail)
    for case in rejects:
        out = folder / 'reject.wasm'
        obs = compile_one(case['file'], out)
        if obs.get('blocked'):
            tally['blocked'] = obs
            return tally
        want = case['knot']
        ok = (obs['exit'] == want['exit'] and obs['stdout'] == b''
              and text(obs['stderr']).startswith(want['diagnostic']) and not out.exists())
        verdict(ok, case, obs, {'expected': want, 'actual': shown(obs)})
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


def bytes_module(input_at: bytes, run_body: bytes, data: bytes = b'') -> bytes:
    """A hand-assembled knot-bytes-0 module: knot_input returns a constant, knot_run is given."""
    code = lambda body: leb(len(body)) + body
    return (b'\0asm\x01\0\0\0' + section(1, b'\x60\x01\x7f\x01\x7f') + section(3, b'\x00', b'\x00')
            + section(5, b'\x00\x01')
            + section(7, name('memory') + b'\x02\x00', name('knot_input') + b'\x00\x00', name('knot_run') + b'\x00\x01')
            + section(10, code(b'\x00\x41' + input_at + b'\x0b'), code(run_body))
            + (section(11, b'\x00\x41\x00\x0b' + leb(len(data)) + data) if data else b''))


def replay_module(obs) -> bytes:
    """Test double for knot-bytes-0: returns one fixed observation. Not a parser."""
    record = (obs['exit'].to_bytes(4, 'little') + len(obs['stdout']).to_bytes(4, 'little')
              + len(obs['stderr']).to_bytes(4, 'little') + obs['stdout'] + obs['stderr'])
    require(len(record) < 4096, 'replay record fits below the input region')
    return bytes_module(b'\x80\x20', b'\x00\x41\x00\x0b', record)  # no locals; i32.const 0; end


def recursive_module() -> bytes:
    """Test double whose knot_run recurses without bound: a host stack trap."""
    return bytes_module(b'\x80\x08', b'\x00\x20\x00\x10\x01\x0b')  # local.get 0; call knot_run; end


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
    # A real host stack trap, and the host's memory classification on V8's messages.
    module = folder / 'host-stack.wasm'
    module.write_bytes(recursive_module())
    answer, got = host(module, [{'argv': [str(MANIFEST.relative_to(ROOT))], 'inputs': [], 'outputs': []}], 'host-stack')
    result.append({'name': 'host-stack-trap', 'expected': {'abi': 'knot-bytes-0', 'resource': 'host-stack'},
                   'observed': {'abi': answer and answer['abi'],
                                'resource': exhaustion(shown(got[0])) if answer and not answer['blocked'] else None}})
    probe = ("import { trap } from './" + HOST + "';"
             "const see = m => { const r = trap(new RangeError(m)); return { exit: r.exit, host: r.host,"
             " stderr: Buffer.from(r.stderr, 'base64').toString() }; };"
             "console.log(JSON.stringify([see('WebAssembly.Instance(): Out of memory: Cannot allocate Wasm memory"
             " for new instance'), see('WebAssembly.Memory(): could not allocate memory'),"
             " see('Maximum call stack size exceeded'), see('offset is out of bounds')]));")
    r = run(['node', '--input-type=module', '-e', probe], SECONDS['tool'])
    try:
        seen = [exhaustion(row) or outcome(row) for row in json.loads(r['stdout'])]
    except ValueError:
        seen = shown(r)
    result.append({'name': 'host-trap-classification',
                   'expected': {'resources': ['host-memory', 'host-memory', 'host-stack', 'HostFailure']},
                   'observed': {'resources': seen}})
    return result


def sandbox_controls(bundle, manifest, argv) -> list[dict]:
    """Live refusals: damaged copies of S's sandbox must fail verification before any step."""
    source = ROOT / BUILD / bundle['sandbox']
    entry = bundle['entry']
    package = next((p for p in bundle['order'] if p.startswith(f'{LIB}/')), manifest['base']['path'])

    def symlink(folder):
        twin = folder.parent / f'{folder.name}-twin.bend'
        twin.write_bytes((folder / entry).read_bytes())
        (folder / entry).unlink()
        (folder / entry).symlink_to(twin)

    def hardlink(folder):
        os.link(folder / entry, folder.parent / f'{folder.name}-twin.bend')

    def tamper(folder):
        with (folder / package).open('ab') as f:
            f.write(b'\n')

    def extra(folder):
        (folder / LIB / 'extra.bend').write_bytes(b'')

    # Staging itself refuses a package whose bytes differ from its pin: the run
    # stops there, before any seed invocation.
    library = ROOT / BUILD / 'controls' / 'tampered-lib'
    shutil.rmtree(library, ignore_errors=True)
    for name in manifest['packages']:
        (library / name).parent.mkdir(parents=True, exist_ok=True)
        (library / name).write_bytes((library_path() / name).read_bytes() + b'\n')
    try:
        stage_sandbox(entry, ROOT / BUILD / 'controls' / 'staging-pin-refused', manifest, library)
        seen = {'refused': False}
    except AssertionError as error:
        seen = {'refused': True, 'reason': 'differs from its pin' if 'differs from its pin' in str(error) else str(error)}
    result = [{'name': 'staging-pin-refused', 'expected': {'refused': True, 'reason': 'differs from its pin'},
               'observed': seen}]
    for label, damage, reason in (
            ('sandbox-symlink-refused', symlink, 'not a regular single-link file'),
            ('sandbox-hardlink-refused', hardlink, 'not a regular single-link file'),
            ('sandbox-pin-refused', tamper, 'differs from its pin'),
            ('sandbox-extra-file-refused', extra, 'differs from its staged record')):
        folder = ROOT / BUILD / 'controls' / label
        for leftover in folder.parent.glob(f'{label}-twin.bend'):
            leftover.unlink()
        replica(source, folder, bundle)
        damage(folder)
        try:
            verify(folder, bundle, manifest)
            seen = {'refused': False}
        except AssertionError as error:
            seen = {'refused': True, 'reason': reason if reason in str(error) else str(error)}
        result.append({'name': label, 'expected': {'refused': True, 'reason': reason}, 'observed': seen})
    result.append({'name': 'argv-reserved-refused', 'expected': {'reserved': ['--threads']},
                   'observed': {'reserved': reserved_in([*argv, '--threads', '2'], manifest)}})
    return result


# --------------------------------------------------------------- mutants

def reached_chain(progress) -> dict:
    """The judge's positive control: the real receipt with every E2E-3 stage
    reached as a correct fixpoint would record it. The generation rules only
    bite on reached generations, which the current tree does not have."""
    p = copy.deepcopy(progress)
    c = p['generation_contract'][GENERATIONS[0]]
    by = {s['id']: s for s in p['stages']}
    rows, size = by['e2e3.c1']['observations'], 4096
    made = {'sha256': digest(b'fixpoint'), 'bytes': size, 'output_bytes': c['target']['output_bytes'],
            'headroom_bytes': c['target']['output_bytes'] - size, 'memory': None}

    def compiled(sid, program):
        return stage(sid, status='reached', corpus=1, agree=1, disagree=0, args=list(c['argv']),
                     result={'argv': [program, *c['argv']], 'exit': 0, 'stdout': f'Built\t{size}\n', 'stderr': ''},
                     artifact=dict(made))
    by['e2e3.a2'] = compiled('e2e3.a2', '../c1')
    by['e2e3.a3'] = compiled('e2e3.a3', '../a2.wasm')
    by['e2e3.fixpoint'] = stage('e2e3.fixpoint', status='reached', corpus=1, agree=1, disagree=0)
    by['e2e3.conformance'] = stage('e2e3.conformance', status='reached', corpus=2 * len(rows), agree=2 * len(rows),
                                   disagree=0, generations={g: {'agree': len(rows), 'disagree': 0, 'first_disagreement': None,
                                                                'observations': copy.deepcopy(rows)} for g in ('a2', 'a3')})
    p['stages'] = [by[sid] for sid, _ in STAGES]
    return p


def mutants(progress) -> list[dict]:
    """Scratch copies with substituted recorded fields; the judge must reject
    each for its named reason. The first nine mutate the real receipt; the
    rest mutate the reached chain, whose unmutated copy must pass."""
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

    def step(p, sid='e2e3.a3'):
        return next(s for s in p['stages'] if s['id'] == sid)

    def contracts(p):
        return [p['generation_contract'][sid] for sid in GENERATIONS]

    def bare_argv(p):  # The pre-harness-2 A2 -> A3 argv: [source, output], so default budgets.
        c = contracts(p)[1]
        c['argv'] = [c['entry'], c['target']['output']]
        step(p)['args'] = list(c['argv'])

    def reserved(p):
        for c, sid in zip(contracts(p), GENERATIONS):
            c['argv'] = ['--threads', '1', *c['argv']]
            step(p, sid)['args'] = list(c['argv'])

    def symlinked(p):
        b = p['bundles'][COMPILER]
        b['files'][b['entry']].update(kind='symlink', sha256=None)

    def unpinned(p):
        b = p['bundles'][COMPILER]
        f = b['files'][next(x for x in b['order'] if x.startswith(f'{LIB}/') or x.startswith('.toolchain/'))]
        f['sha256'] = digest(f['sha256'].encode())

    def exhausted(p, status='blocked', tag='host-stack'):
        s, c, cases = step(p), contracts(p)[1], step(p, 'e2e3.conformance')['corpus']
        s.clear()
        s.update(stage('e2e3.a3', status=status, corpus=1, agree=0, disagree=0, args=list(c['argv']),
                       blocker={'source': 'host', 'argv': list(c['argv']), 'exit': 4, 'stdout': '',
                                'stderr': 'Exhausted\twasm\tcall-stack\n', 'host': True, 'resource': tag}))
        p['stages'][-2:] = [not_run('e2e3.fixpoint', 'e2e3.a3', 1), not_run('e2e3.conformance', 'e2e3.a3', cases)]

    def diagnostic_tail(p):
        row = next(r for r in step(p, 'e2e3.conformance')['generations']['a3']['observations'] if r['stderr'])
        tail = row['stderr'].rstrip('\n')
        row['stderr'] = tail[:-1] + chr(ord(tail[-1]) ^ 1) + '\n'

    def oversize(p):
        a = step(p)['artifact']
        a['bytes'] = a['output_bytes'] + 1

    real = (
        ('unmutated', 0, None, lambda p: None),
        ('blocker-invalid', 1, 'only Unsupported or Exhausted may block', lambda p: invalid(knot_blocker(p))),
        ('blocker-invalid-word-only', 1, 'only Unsupported or Exhausted may block',
         lambda p: invalid(knot_blocker(p), exit=False)),
        ('blocker-invalid-exit-only', 1, 'only Unsupported or Exhausted may block',
         lambda p: invalid(knot_blocker(p), word=False)),
        ('blocker-host-crash', 1, 'only Unsupported or Exhausted may block', lambda p: knot_blocker(p).update(
            exit=1, stderr='error: uncaught RuntimeError: unreachable\n    at main\n')),
        ('blocker-signal', 1, 'only Unsupported or Exhausted may block',
         lambda p: knot_blocker(p).update(exit=-11, stderr='')),
        ('own-source-invalid', 1, 'reports its own source', lambda p: invalid(p['own_source'][0])),
        ('reached-disagreement', 1, 'reached without exact agreement', disagree),
        ('not-run-after-reached', 1, 'not run although prerequisite', silent_skip),
    )
    chain = (
        ('reached-chain', 0, None, lambda p: None),
        ('argv-mismatch', 1, 'generation contracts differ', bare_argv),
        ('argv-unrecorded', 1, 'argv differs from its generation contract',
         lambda p: step(p).update(args=step(p)['args'][:-1])),
        ('argv-seed-reserved', 1, 'seed-reserved', reserved),
        ('sandbox-symlink', 1, 'not a regular single-link file', symlinked),
        ('sandbox-unpinned', 1, 'differs from its pin', unpinned),
        ('a3-host-exhausted', 1, 'must be divergent-exhausted', exhausted),
        ('a3-divergent-exhausted', 1, 'is non-passing', lambda p: exhausted(p, status='divergent-exhausted')),
        ('a3-resource-forged', 1, 'resource tag', lambda p: exhausted(p, tag='knot-budget')),
        ('diagnostic-tail', 1, 'diagnostics differ from C1', diagnostic_tail),
        ('artifact-over-budget', 1, 'exceeds output_bytes', oversize),
    )
    result = []
    for base, cases in ((progress, real), (reached_chain(progress), chain)):
        for label, expected, reason, mutate in cases:
            scratch = copy.deepcopy(base)
            if mutate(scratch) is False:
                result.append({'name': label, 'applicable': False})
                continue
            path = folder / f'{label}.json'
            path.write_text(json.dumps(scratch, indent=2) + '\n')
            r = run([sys.executable, '-B', f'{REL}/check.py', '--judge', path.relative_to(ROOT).as_posix()],
                    SECONDS['tool'])
            violations = text(r['stdout']).splitlines()
            killed = r['exit'] == 1 and any(reason in v for v in violations) if reason else r['exit'] == 0
            result.append({'name': label, 'expected_exit': expected, 'expected_violation': reason, 'exit': r['exit'],
                           'violations': violations, 'killed_for_reason': killed,
                           'outcome': 'rejected' if r['exit'] == 1 else 'accepted' if r['exit'] == 0 else 'error'})
    return result


# ------------------------------------------------------------------- main

def seed_step(builds) -> dict:
    """The only seed invocations in the pipeline, each inside its entry's sandbox.
    C1 is built twice under the same name; the two binaries must be identical."""
    def build(item):
        label, (entry, folder, out) = item
        out.parent.mkdir(parents=True, exist_ok=True)
        lane = 'bun' if out.suffix == '.js' else 'native'
        successful([relative(ROOT / SEED, folder), entry, '-o', relative(out, folder)], cwd=folder,
                   env={**ENV, 'BEND_LIB': str(folder / LIB)})
        return label, {'entry': entry, 'lane': lane, 'sandbox': folder.name, 'sha256': digest(out.read_bytes())}
    with ThreadPoolExecutor(max_workers=3) as pool:
        records = dict(pool.map(build, builds.items()))
    repeat = records.pop('C1-repeat')
    records['C1']['repeat_sha256'] = repeat['sha256']
    return records


def audit(contract, manifest, folder: Path, bundle, checker: Path | None) -> dict:
    """C1's loader closure (--audit-bundle Module lines) against the staged
    files (FX-21), and the D2 trust inventory of unchecked Base (FX-20)."""
    if checker is None:
        return {'status': 'unavailable', 'reason': 'src/CONTRACT.json advertises no --audit-bundle'}
    argv = ['--audit-bundle', LIB, bundle['entry']]
    obs = run([relative(checker, folder), *argv], SECONDS['compile'], cwd=folder)
    verify(folder, bundle, manifest)
    if obs['exit'] != 0:
        return {'status': 'blocked', 'args': argv, 'tool': 'seed-built src/check-cli.bend', 'blocker': stopped(obs, 'knot')}
    fields = [line.split('\t', 1) for line in text(obs['stdout']).splitlines() if '\t' in line]
    pick = lambda key: [value for k, value in fields if k == key]
    return {'status': 'recorded', 'args': argv, 'tool': 'seed-built src/check-cli.bend', 'modules': pick('Module'),
            'trust': {'base_pin': pick('BasePin'), 'base_checked': pick('BaseChecked'),
                      'base_unchecked': pick('BaseUnchecked')}}


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
    build = ROOT / BUILD
    contract = json.loads((ROOT / 'src/CONTRACT.json').read_bytes())
    manifest = json.loads(MANIFEST.read_bytes())
    progress = {'schema': 2, 'status': 'incomplete', 'harness': f'{REL}/check.py',
                'seed': contract['seed'], 'compiler_entry': COMPILER, 'parser_entry': PARSER}
    reference = {'schema': 1, 'reference': f'seed-built {PARSER}, native and Bun lanes', 'files': []}
    code = 1
    try:
        progress['tools'] = {t: text(successful([t, '--version'], SECONDS['tool'])['stdout']).strip() for t in ('bun', 'node')}
        progress['inputs'] = {p: digest((ROOT / p).read_bytes()) for p in sorted(
            [f'{REL}/check.py', HOST, f'{REL}/manifest.json', RUN_WASM, SEED, 'src/CONTRACT.json', PROGRAMS, REJECTS,
             *[f'{REL}/io-abi.mjs'] * (HERE / 'io-abi.mjs').exists()])}
        shared = environment(contract, manifest)

        # Staging: copied regular files, pins checked, all before the seed step.
        auditing = bool(contract.get('module_loading', {}).get('audit_arguments'))
        entries = [PARSER, COMPILER, *[CHECKER] * auditing]
        progress['bundles'] = {e: stage_sandbox(e, build / SANDBOX[e], manifest) for e in entries}
        sandbox, bundle = build / SANDBOX[COMPILER], progress['bundles'][COMPILER]
        contracts = {'e2e3.a2': generation_contract(contract, manifest, bundle, sandbox, shared)}

        # The seed step: the only seed invocations in the pipeline.
        c1 = build / 'c1'
        builds = {'parse-cli': (PARSER, build / SANDBOX[PARSER], build / 'parse-cli'),
                  'parse-cli.js': (PARSER, build / SANDBOX[PARSER], build / 'parse-cli.js'),
                  'C1': (COMPILER, sandbox, c1), 'C1-repeat': (COMPILER, sandbox, build / 'repeat/c1'),
                  **({'check-cli': (CHECKER, build / SANDBOX[CHECKER], build / 'check-cli')} if auditing else {})}
        progress['seed_builds'] = seed_step(builds)
        for e in entries:
            verify(build / SANDBOX[e], progress['bundles'][e], manifest)
        progress['audit'] = audit(contract, manifest, sandbox, bundle, build / 'check-cli' if auditing else None)

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
        # A Bun-lane fault counts as a disagreement here, never as exhaustion: both oracle lanes must agree.
        stages = [stage('e2e2.reference', status='reached', corpus=len(names), agree=lanes['agree'],
                        disagree=lanes['disagree'] + lanes['exhausted'], lanes=['native', 'bun'],
                        first_disagreement=lanes['first_disagreement'],
                        outcomes=dict(sorted(outcomes.items(), key=lambda kv: (-kv[1], kv[0]))))]

        # E2E-2 Knot path: C1 compiles the parser; its module must reproduce the corpus.
        parser_module = build / 'parse-cli.wasm'
        cap = budgets(contract)[-1]
        compiled, _ = compile_stage('e2e2.compile', c1, build / SANDBOX[PARSER], progress['bundles'][PARSER], manifest,
                                    generation_argv(contract, manifest, PARSER), parser_module, cap)
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
                                        blocker=tagged({'source': 'knot', **first}), **fields))
                else:
                    stages.append(stage('e2e2.self-parse', status='reached', exhausted=t['exhausted'], **fields))

        # E2E-3: seed -> C1 -> A2 -> A3. C1 must already pass the conformance corpus.
        base = conformance(lambda source, out: run([f'./{BUILD}/c1', source, out.relative_to(ROOT).as_posix()],
                                                   SECONDS['compile']))
        cases = base['programs'] + base['rejects']
        stages.append(stage('e2e3.c1', status='reached', corpus=cases, agree=base['agree'], disagree=base['disagree'],
                            lane='native', first_disagreement=base['first_disagreement'],
                            programs=base['programs'], calls=base['calls'], rejects=base['rejects'],
                            modules=base['modules'], observations=base['observations']))
        a2, a3 = build / 'a2.wasm', build / 'a3.wasm'
        stage_a2, c1_on_s = compile_stage('e2e3.a2', c1, sandbox, bundle, manifest, contracts['e2e3.a2']['argv'], a2, cap)
        stages.append(stage_a2)
        # A2 runs in a fresh copy of the same sandbox, under a contract built the same way.
        sandbox_a2 = build / f"{SANDBOX[COMPILER]}-a2"
        replica(sandbox, sandbox_a2, bundle)
        verify(sandbox_a2, bundle, manifest)
        contracts['e2e3.a3'] = generation_contract(contract, manifest, bundle, sandbox_a2, shared)
        progress['generation_contract'] = contracts
        measured = {}
        if stage_a2['status'] != 'reached' or stage_a2['disagree']:
            stages += [not_run('e2e3.a3', 'e2e3.a2', 1), not_run('e2e3.fixpoint', 'e2e3.a3', 1),
                       not_run('e2e3.conformance', 'e2e3.a3', 2 * cases)]
        else:
            measured['e2e3.a2'] = {k: c1_on_s[k] for k in ('elapsed_seconds', 'peak_rss_bytes')}
            argv = contracts['e2e3.a3']['argv']
            answer, result = host(a2, [{'argv': argv, 'inputs': bundle['order'], 'outputs': [OUTPUT]}], 'a3', cwd=sandbox_a2)
            verify(sandbox_a2, bundle, manifest)
            a3.unlink(missing_ok=True)
            if answer is None or answer['blocked']:
                stages.append(blocked('e2e3.a3', result.pop('source'), result, 1, args=argv))
            else:
                got = result[0]
                measured['e2e3.a3'] = {k: got[k] for k in ('elapsed_seconds', 'peak_rss_bytes')}
                if OUTPUT in got['files']:
                    a3.write_bytes(got['files'][OUTPUT])
                tag = exhaustion(shown(got))
                if got['exit'] != 0 and tag and tag.startswith('host-'):
                    stages.append(stage('e2e3.a3', status='divergent-exhausted', corpus=1, agree=0, disagree=0,
                                        args=argv, blocker=stopped(got, 'host')))
                elif got['exit'] != 0:
                    stages.append(blocked('e2e3.a3', 'knot', got, 1, args=argv))
                else:
                    ok = built(got, a3)
                    stages.append(stage('e2e3.a3', status='reached', corpus=1, agree=int(ok), disagree=int(not ok),
                                        args=argv, result=shown(got),
                                        artifact=artifact(a3, cap) if a3.is_file() else None))
            if stages[-1]['status'] != 'reached' or stages[-1]['disagree']:
                stages += [not_run('e2e3.fixpoint', 'e2e3.a3', 1), not_run('e2e3.conformance', 'e2e3.a3', 2 * cases)]
            else:
                same = a2.read_bytes() == a3.read_bytes()
                stages.append(stage('e2e3.fixpoint', status='reached', corpus=1, agree=int(same), disagree=int(not same)))
                runs = {g: conformance(module_runner(m, g), base) for g, m in (('a2', a2), ('a3', a3))}
                stop = next((r['blocked'] for r in runs.values() if r['blocked']), None)
                if stop:
                    stages.append(blocked('e2e3.conformance', stop.pop('source'), stop, 2 * cases))
                else:
                    stages.append(stage('e2e3.conformance', status='reached', corpus=2 * cases,
                                        agree=sum(r['agree'] for r in runs.values()),
                                        disagree=sum(r['disagree'] for r in runs.values()),
                                        generations={g: {k: r[k] for k in ('agree', 'disagree', 'first_disagreement',
                                                                           'observations')}
                                                     for g, r in runs.items()}))
        progress['stages'] = stages
        if measured:  # Volatile: wall time and peak RSS, outside the contract (THIN-02).
            progress['measurements'] = measured
        progress['tiers'] = {}
        for tier in ('E2E-2', 'E2E-3'):
            rows = [s for s in stages if s['tier'] == tier]
            first = next((s for s in rows if s['status'] in ('blocked', 'divergent-exhausted')), None)
            progress['tiers'][tier] = {
                'reached': [s['id'] for s in rows if s['status'] == 'reached'],
                'first_blocker': first and {'stage': first['id'], 'source': first['blocker']['source'],
                                            'classification': first['blocker']['stderr'].strip(),
                                            **({'resource': first['blocker']['resource']}
                                               if 'resource' in first['blocker'] else {})}}

        progress['controls'] = controls(names, native, bun) + sandbox_controls(bundle, manifest, contracts['e2e3.a2']['argv'])
        progress['mutants'] = mutants(progress)
        violations = judge(progress, manifest)
        failed_controls = [c['name'] for c in progress['controls'] if c['expected'] != {
            k: c['observed'].get(k) for k in c['expected']}]
        surviving = [m['name'] for m in progress['mutants']
                     if m.get('applicable', True) and (m['exit'] != m['expected_exit'] or not m['killed_for_reason'])]
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
