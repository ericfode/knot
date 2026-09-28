#!/usr/bin/env python3
"""Run the unchanged compiler gates in an exported working tree, without network."""
from __future__ import annotations

import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass
import datetime
import difflib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

from normalize import Normalizer, changed_fields, classify, digest, json_bytes


@dataclass(frozen=True)
class Gate:
    name: str
    argv: tuple[str, ...]
    outputs: tuple[str, ...] = ()
    needs: tuple[str, ...] = ()


GATES = (
    Gate('frontend', ('python3', 'tests/subsets/check_frontend.py'),
         ('tests/subsets/receipts/frontend.json',)),
    Gate('checker', ('python3', 'tests/compiler-checker/check.py'),
         ('tests/compiler-checker/receipts/checker.json',)),
    Gate('structural', ('python3', 'tests/compiler-structural/check.py'),
         ('tests/compiler-structural/receipts/catalog.json',)),
    Gate('fields', ('python3', 'tests/compiler-fields/check.py'),
         ('tests/compiler-fields/receipts/fields.json',)),
    Gate('wasm', ('python3', 'tests/compiler-wasm/check.py'),
         ('tests/compiler-wasm/receipts/wasm.json', 'tests/compiler-wasm/generated/*.wasm',
          'tests/compiler-wasm/generated/*.wat')),
    Gate('wasm-trust', ('bun', 'tests/compiler-wasm/trust.ts'),
         ('research/compiler-wasm/receipts/trust.json',), ('wasm',)),
    Gate('fields-trust', ('bun', 'tests/compiler-fields/trust.ts'),
         ('research/compiler-fields/receipts/trust.json',), ('fields',)),
    Gate('structural-trust', ('bun', 'tests/compiler-structural/trust.ts'),
         ('research/compiler-structural/receipts/trust.json',), ('structural',)),
    Gate('owned-store', ('python3', 'research/owned-store/check.py'),
         ('research/owned-store/receipts/gate.json', 'research/owned-store/receipts/inputs.json.gz',
          'research/owned-store/receipts/native.txt.gz', 'research/owned-store/receipts/bun.txt.gz')),
    Gate('flat-store', ('python3', 'research/flat-store/check.py'),
         ('research/flat-store/receipts/gate.json', 'research/flat-store/receipts/*-oracle.txt.gz',
          'research/flat-store/receipts/*-wasm.json', 'research/flat-store/receipts/mutant-*.json',
          'research/flat-store/receipts/native.wasm', 'research/flat-store/receipts/store.wat'),
         ('owned-store',)),
    Gate('recursion', ('python3', 'tests/compiler-recursion/check.py'),
         ('tests/compiler-recursion/receipts/recursion.json',)),
    Gate('fields-wasm', ('python3', 'tests/compiler-fields-wasm/check.py'),
         ('tests/compiler-fields-wasm/receipts/fields-wasm.json',)),
    Gate('census', ('node', 'tools/census/census.mjs', '--check')),
    Gate('perch-context', ('python3', 'tests/perch-context/check.py'),
         ('tests/perch-context/receipts/context.json',)),
    Gate('lint:verify', ('npm', 'run', '-s', 'lint:verify')),
    Gate('bootstrap', ('python3', 'tests/compiler-bootstrap/check.py'),
         ('tests/compiler-bootstrap/receipts/progress.json', 'tests/compiler-bootstrap/receipts/reference.json')),
    Gate('classification', ('python3', 'tests/compiler-classification/check.py'),
         ('tests/compiler-classification/receipts/precision.json',)),
    Gate('nest', ('python3', 'tests/compiler-nest/check.py'),
         ('tests/compiler-nest/receipts/nest.json',)),
    Gate('nest-review', ('python3', 'tests/compiler-nest/review.py'),
         ('tests/compiler-nest/receipts/review.json',)),
    Gate('io-host', ('python3', '-B', 'tests/compiler-io/host-check.py'),
         ('tests/compiler-io/receipts/host.json',)),
    Gate('io-abi-2', ('python3', '-B', 'tests/compiler-io-abi-2/check.py'),
         ('tests/compiler-io-abi-2/receipts/host.json', 'tests/compiler-io-abi-2/receipts/reference.json')),
    Gate('selfhost', ('python3', 'tests/compiler-selfhost/check.py'),
         ('tests/compiler-selfhost/receipts/selfhost.json',)),
    Gate('nest-round3', ('python3', 'tests/compiler-nest/round3.py'),
         ('tests/compiler-nest/receipts/round3.json',)),
    Gate('nest-round4', ('python3', 'tests/compiler-nest/round4.py'),
         ('tests/compiler-nest/receipts/round4.json',)),
    Gate('nest-round6', ('python3', 'tests/compiler-nest/round6.py'),
         ('tests/compiler-nest/receipts/round6.json',)),
)


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(['git', '-C', str(root), *args])


def excluded(name: str) -> bool:
    parts = Path(name).parts
    return (any(p.lower() == '.env' or p.lower().startswith('.env.') or p == '.git' for p in parts)
            or parts[0] in ('.toolchain', 'node_modules', '.local', 'build'))


def file_names(root: Path) -> list[str]:
    names = git(root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard')
    return sorted({os.fsdecode(n) for n in names.split(b'\0') if n and not excluded(os.fsdecode(n))})


def fingerprint(root: Path, names: list[str]) -> dict:
    """Do not follow symlinks while reading the invoking worktree."""
    result = {}
    for name in names:
        path = root / name
        for parent in path.parents:
            if parent == root:
                break
            if parent.is_symlink():
                raise ValueError(f'Symlink parent in export: {name}')
        if path.is_symlink():
            result[name] = {'link': os.readlink(path)}
        elif path.is_file():
            result[name] = {'sha256': digest(path.read_bytes()), 'mode': path.stat().st_mode & 0o777}
        elif path.exists():
            raise ValueError(f'Not a regular file: {name}')
        else:
            result[name] = None  # Preserve a tracked deletion.
    return result


def export(root: Path, target: Path) -> dict:
    root = root.resolve()
    names = file_names(root)
    before = fingerprint(root, names)
    target.mkdir(parents=True)
    for name, identity in before.items():
        if identity is None:
            continue
        source, dest = root / name, target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if 'link' in identity:
            resolved = source.resolve()
            if not resolved.is_relative_to(root):
                raise ValueError(f'External source symlink: {name}')
            relative = resolved.relative_to(root).as_posix()
            if excluded(relative) or before.get(relative) is None:
                raise ValueError(f'Symlink outside exported files: {name}')
            dest.symlink_to(os.path.relpath(target / relative, dest.parent))
        else:
            shutil.copy2(source, dest)
    if fingerprint(root, names) != before or file_names(root) != names:
        raise RuntimeError('Working tree changed during export; retry with a stable increment')
    for name in ('.toolchain', 'node_modules'):
        source = (root / name).resolve(strict=True)
        (target / name).symlink_to(source, target_is_directory=True)
    return before


def copy_cache(source: Path, destination: Path, identities: dict, namespace: str):
    for folder, dirs, files in os.walk(source, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not excluded(d) and not (Path(folder) / d).is_symlink())
        for name in sorted(files):
            path = Path(folder) / name
            if excluded(name) or path.is_symlink() or name.endswith('.lock'):
                continue
            relative = path.relative_to(source)
            data = path.read_bytes()
            identities[namespace + '/' + relative.as_posix()] = digest(data)
            dest = destination / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)


def environment(run_dir: Path) -> tuple[dict, dict]:
    # Preserve only host tool discovery; never import credentials, dotenv files,
    # NODE_OPTIONS, shell hooks, or caller-specific Bend/network configuration.
    env = {key: os.environ[key] for key in ('PATH', 'HOME', 'SDKROOT', 'DEVELOPER_DIR',
                                          'SYSTEMROOT') if key in os.environ}
    library = run_dir / 'bend-lib'
    library.mkdir()
    cache = Path(os.environ.get('BEND_LIB', str(Path.home() / '.bend/lib'))).expanduser().resolve()
    dependencies = {}
    # Freeze already installed hash packages. The seed must fail offline on a
    # missing import, never fill or mutate the user's package cache.
    for package in sorted(cache.glob('0x*')):
        if not re.fullmatch(r'0x[0-9a-f]{32,64}', package.name) or not package.is_dir():
            continue
        copy_cache(package, library / package.name, dependencies, 'bend-lib/' + package.name)
    cache_default = (Path.home() / 'Library/Caches' if sys.platform == 'darwin'
                     else Path(os.environ.get('XDG_CACHE_HOME', str(Path.home() / '.cache'))))
    parser_cache = Path(os.environ.get('TREE_SITTER_LANGUAGE_PACK_CACHE_DIR', str(cache_default)))
    copy_cache(parser_cache / 'tree-sitter-language-pack', run_dir / 'cache/tree-sitter-language-pack',
               dependencies, 'tree-sitter-language-pack')
    temp = run_dir / 'tmp'
    temp.mkdir()
    env.setdefault('KNOT_GATE_TIMEOUT_SCALE', os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '4'))
    env.update(BEND_NO_TELEMETRY='1', BEND_LIB=str(library), BEND_HUB='offline://disabled',
               BEND_ORIGIN='offline://disabled', PYTHONDONTWRITEBYTECODE='1',
               TREE_SITTER_LANGUAGE_PACK_CACHE_DIR=str(run_dir / 'cache'),
               TREE_SITTER_LANGUAGE_PACK_MANIFEST_URL='offline://disabled',
               TMPDIR=str(temp), TMP=str(temp), TEMP=str(temp), TZ='UTC', LC_ALL='C',
               npm_config_offline='true', npm_config_audit='false', npm_config_fund='false')
    return env, dependencies


def output_names(root: Path, gate: Gate) -> set[str]:
    return {p.relative_to(root).as_posix() for pattern in gate.outputs for p in root.glob(pattern) if p.is_file()}


def counts(root: Path, gate: Gate, stdout: str) -> dict:
    if gate.name == 'census':
        record = json.loads(stdout)
        if record.get('status') != 'current':
            raise ValueError('Census inventory is not current')
        return {key: record['compiler'][key] for key in ('files', 'declarations', 'classes')}
    if not gate.outputs:
        match = re.search(r'(?m)^# pass (\d+)\s*$', stdout)
        if not match or 'PASS: eight law rules;' not in stdout:
            raise ValueError('Missing lint TAP or law wiring completion record')
        return {'tests': int(match[1]), 'law_rules': 8}
    record = json.loads((root / gate.outputs[0]).read_bytes())
    if gate.name.endswith('-trust'):
        entries = record['entries']
        if any(e['holes'] != 0 for e in entries):
            raise ValueError('Trust receipt contains proof holes')
        return {'entries': len(entries), 'proof_holes': 0}
    if record['status'] not in ('pass', 'passed'):
        raise ValueError('Receipt does not record a completed gate')
    result = {key: len(record[key]) for key in ('fixtures', 'mutants', 'budgets', 'boundaries',
                                               'bounds', 'host_boundaries', 'rejects') if key in record}
    if gate.name in ('frontend', 'checker', 'structural', 'fields'):
        phases = {'frontend': 1, 'checker': 1, 'structural': 2, 'fields': 3}[gate.name]
        result['lane_observations'] = sum(len(row['lanes']) * phases for row in record['fixtures'])
    if gate.name == 'wasm':
        result['reference_calls'] = sum(len(row['reference']) for row in record['fixtures'])
        result['execution_lanes'] = len(record['fixtures'][0]['lanes'])
    if gate.name in ('checker', 'fields'):
        field = 'observation' if gate.name == 'checker' else 'result'
        result['bound_observations'] = sum(len(row[field]['stdout'].splitlines()) for row in record['bounds'])
    if gate.name == 'owned-store':
        result.update(cases=record['case_count'], literal_witnesses=record['literal_witnesses'], execution_lanes=2)
    if gate.name == 'bootstrap':
        stages = record['stages']
        if (any(record['verdict'].values()) or any(s['status'] == 'reached' and (s['disagree'] or s['agree'] != s['corpus'])
                                                  for s in stages)
                or any(not ((b['exit'] is None and b.get('outcome') == 'Exhausted')
                            or (b['exit'], b['stderr'].split('\t', 1)[0]) in ((3, 'Unsupported'), (4, 'Exhausted')))
                       for b in (s['blocker'] for s in stages if s['status'] == 'blocked'))):
            raise ValueError('Bootstrap receipt violates its stage verdict')
        result.update(corpus=record['corpus']['files'], stages=len(stages),
                      reached=sum(s['status'] == 'reached' for s in stages))
    if gate.name == 'selfhost':
        status = record['counts']['status']
        if status['fail'] or not status['pass'] or record['seed']['reproduced'] is not True:
            raise ValueError('Selfhost receipt violates its verdict')
        result.update(cases=len(record['cases']), passed=status['pass'], blocked=status['blocked'],
                      d4_gaps=len(record['counts']['d4_gaps']), judge_mutants=len(record['judge_mutants']))
    if gate.name == 'flat-store':
        for lane in ('native', 'bun'):
            wasm = json.loads((root / f'research/flat-store/receipts/{lane}-wasm.json').read_bytes())
            result[lane] = {k: wasm[k] for k in ('observations', 'instances', 'installed_boundary_states', 'lifecycle_checks')}
    if gate.name in ('nest', 'nest-review', 'nest-round3', 'nest-round4', 'nest-round6'):
        result.update(record['counts'])
    if gate.name == 'io-host':
        for key in ('seed_fixtures', 'seed_runs', 'conformance_runs', 'cli_runs', 'errno', 'stress'):
            result[key] = record[key]
        result['review'] = record['review_counts']
    if gate.name == 'io-abi-2':
        for key in ('read_observations', 'reference_observations', 'seed_observations', 'seed_exhausted',
                    'mutants_killed', 'case_mode'):
            result[key] = record[key]
        result['parity'] = len(record['parity'])
    return result


def execute(gate: Gate, root: Path, logs: Path, env: dict, timeout: float) -> dict:
    start = time.monotonic()
    name = gate.name.replace(':', '-')
    stdout, stderr = logs / f'{name}.stdout', logs / f'{name}.stderr'
    result = {'name': gate.name, 'command': list(gate.argv), 'status': 'host-failure',
              'exit_code': None, 'counts': {}, 'stdout': stdout.name, 'stderr': stderr.name}
    try:
        with stdout.open('wb') as out, stderr.open('wb') as err:
            child = subprocess.Popen(gate.argv, cwd=root, env=env, stdout=out, stderr=err, start_new_session=True)
            try:
                result['exit_code'] = child.wait(timeout=timeout)
                result['status'] = 'passed' if result['exit_code'] == 0 else 'failed'
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait()
                result.update(status='exhausted', error=f'Gate timeout: {timeout:g} seconds')
        if result['status'] == 'passed':
            result['counts'] = counts(root, gate, stdout.read_text(errors='replace'))
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        result.update(status='host-failure', error=str(error))
    result['seconds'] = round(time.monotonic() - start, 6)
    return result


def schedule(gates: tuple[Gate, ...], worker, jobs: int) -> list[dict]:
    pending, running, done = list(gates), {}, {}
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        while pending or running:
            for gate in pending[:]:
                if all(name in done for name in gate.needs):
                    if any(done[name]['status'] != 'passed' for name in gate.needs):
                        done[gate.name] = {'name': gate.name, 'command': list(gate.argv),
                                           'status': 'blocked', 'exit_code': None, 'counts': {},
                                           'seconds': 0, 'dependencies': list(gate.needs)}
                        pending.remove(gate)
                    elif len(running) < jobs:
                        running[pool.submit(worker, gate)] = gate
                        pending.remove(gate)
            if running:
                finished, _ = wait(running, return_when=FIRST_COMPLETED)
                for future in finished:
                    gate = running.pop(future)
                    done[gate.name] = future.result()
                    print(f"{gate.name}: {done[gate.name]['status']} ({done[gate.name]['seconds']:.2f}s)", file=sys.stderr, flush=True)
            elif pending:
                raise ValueError('Cyclic or missing gate dependency')
    return [done[gate.name] for gate in gates]


def compare_receipts(before: dict[str, bytes], after: dict[str, bytes], normalizer: Normalizer,
                     run_dir: Path) -> list[dict]:
    result = []
    for name in sorted(before.keys() | after.keys()):
        old, new = before.get(name), after.get(name)
        a = normalizer.receipt(name, old, before) if old is not None else None
        b = normalizer.receipt(name, new, after) if new is not None else None
        kind = classify(old, new, a, b)
        row = {'path': name, 'classification': kind,
               'before_sha256': digest(a) if a is not None else None,
               'after_sha256': digest(b) if b is not None else None}
        if b is not None:
            dest = run_dir / 'normalized' / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b)
        if kind == 'semantic':
            row['changed_fields'] = (changed_fields(json.loads(a), json.loads(b))
                                     if name.endswith('.json') and a and b else ['/'])
            if name.endswith(('.json', '.wat')):
                patch = ''.join(difflib.unified_diff((a or b'').decode().splitlines(True),
                                (b or b'').decode().splitlines(True), 'tracked/' + name, 'regenerated/' + name))
                dest = run_dir / 'diffs' / (name + '.diff')
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(patch)
        result.append(row)
    return result


def refresh(root: Path, run_dir: Path, snapshot: dict, receipts: list[dict], passed: bool):
    if not passed:
        raise RuntimeError('Refresh requires every gate and receipt check to pass')
    if file_names(root) != sorted(snapshot) or fingerprint(root, sorted(snapshot)) != snapshot:
        raise RuntimeError('Working tree changed since export; refresh refused')
    tracked = set(os.fsdecode(p) for p in git(root, 'ls-files', '-z').split(b'\0') if p)
    for row in receipts:
        if row['path'] not in tracked or row['after_sha256'] is None:
            raise RuntimeError(f"Refresh requires an existing tracked receipt: {row['path']}")
        if row['after_sha256'] != digest((run_dir / 'normalized' / row['path']).read_bytes()):
            raise RuntimeError(f"Normalized receipt changed: {row['path']}")
    written = []
    for row in receipts:
        dest = root / row['path']
        data = (run_dir / 'normalized' / row['path']).read_bytes()
        if dest.read_bytes() != data:
            with tempfile.NamedTemporaryFile(dir=dest.parent, prefix='.gates-', delete=False) as tmp:
                tmp.write(data)
                temporary = Path(tmp.name)
            temporary.chmod(dest.stat().st_mode & 0o777)
            temporary.replace(dest)
            written.append(row['path'])
    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='copy normalized receipts back after all gates pass')
    parser.add_argument('--jobs', type=int, default=4, help='maximum concurrent gates (default: 4)')
    parser.add_argument('--timeout', type=float, default=900, help='per-gate wall limit in seconds (default: 900)')
    parser.add_argument('--keep-scratch', action='store_true', help='retain the exported sources and build outputs')
    args = parser.parse_args(argv)
    if args.jobs < 1 or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('jobs and timeout must be positive')
    root = Path(git(Path.cwd(), 'rev-parse', '--show-toplevel').decode().strip()).resolve()
    start = time.monotonic()
    parent = root / '.local/gates'
    if (root / '.local').is_symlink() or parent.is_symlink():
        raise RuntimeError('Gate output directories must belong to the invoking worktree')
    # These commands must not create unignored or tracked output.
    probe = '.local/gates/.ignore-probe'
    if subprocess.run(['git', '-C', str(root), 'check-ignore', '-q', probe]).returncode != 0:
        raise RuntimeError('.local/gates must be ignored')
    parent.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix='run-', dir=parent))
    scratch, logs = run_dir / 'worktree', run_dir / 'logs'
    logs.mkdir()
    summary = {'schema': 1, 'run': {'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                  'directory': str(run_dir), 'jobs': args.jobs, 'timeout_seconds': args.timeout},
               'normalized': {'status': 'host-failure', 'gates': [], 'receipts': []}}
    code = 1
    try:
        snapshot = export(root, scratch)
        (run_dir / 'snapshot.json').write_bytes(json_bytes(snapshot))
        env, dependencies = environment(run_dir)
        (run_dir / 'dependencies.json').write_bytes(json_bytes(dependencies))
        tracked = set(os.fsdecode(p) for p in git(root, 'ls-files', '-z').split(b'\0') if p)
        expected = {gate.name: output_names(scratch, gate) for gate in GATES}
        before = {name: (scratch / name).read_bytes() for paths in expected.values() for name in paths if name in tracked}
        # Absence after execution must never reuse a stale passing receipt.
        for paths in expected.values():
            for name in paths:
                (scratch / name).unlink()
        normalizer = Normalizer(scratch, (root / '.toolchain').resolve(), Path(env['BEND_LIB']))
        results = schedule(GATES, lambda gate: execute(gate, scratch, logs, env, args.timeout), args.jobs)
        # Keep process evidence even if a malformed receipt cannot be normalized.
        summary['run']['gates'] = results
        summary['normalized']['gates'] = [
            {k: normalizer.value(v) for k, v in row.items() if k not in ('seconds', 'stdout', 'stderr')}
            for row in results]
        after = {}
        for gate, result in zip(GATES, results):
            names = output_names(scratch, gate)
            missing = expected[gate.name] - names
            if missing and result['status'] == 'passed':
                result.update(status='host-failure', error='Missing regenerated receipts', missing=sorted(missing))
            after.update({name: (scratch / name).read_bytes() for name in names})
        receipts = compare_receipts(before, after, normalizer, run_dir)
        passed = all(row['status'] == 'passed' for row in results)
        summary['run']['gates'] = results
        summary['normalized'] = {'status': 'passed' if passed else 'failed',
            'snapshot_sha256': digest(json_bytes(snapshot)), 'dependencies_sha256': digest(json_bytes(dependencies)),
            'gates': [{k: normalizer.value(v) for k, v in row.items() if k not in ('seconds', 'stdout', 'stderr')}
                      for row in results], 'receipts': receipts,
            'receipt_counts': {kind: sum(r['classification'] == kind for r in receipts)
                               for kind in ('identical', 'volatile-only', 'semantic')}}
        if args.refresh:
            summary['run']['refreshed'] = refresh(root, run_dir, snapshot, receipts, passed)
        code = 0 if passed else 1
    except Exception as error:
        summary['error'] = f'{type(error).__name__}: {error}'
        summary['normalized']['status'] = 'host-failure'
        print(summary['error'], file=sys.stderr)
    finally:
        if not args.keep_scratch:
            shutil.rmtree(scratch, ignore_errors=True)
            shutil.rmtree(run_dir / 'bend-lib', ignore_errors=True)
            shutil.rmtree(run_dir / 'tmp', ignore_errors=True)
            shutil.rmtree(run_dir / 'cache', ignore_errors=True)
        summary['run']['total_seconds'] = round(time.monotonic() - start, 6)
        path = run_dir / 'summary.json'
        path.write_bytes(json_bytes(summary))
        print(json_bytes(summary).decode(), end='')
        print(f'Summary: {path}', file=sys.stderr)
    return code


if __name__ == '__main__':
    sys.exit(main())
