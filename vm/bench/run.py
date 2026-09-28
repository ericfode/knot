#!/usr/bin/env python3
"""Seed-native baselines for the frozen knot-vm-1 speed workloads.

Builds each workload with the pinned seed's native lane, runs it under
/usr/bin/time -l, checks its output against the workload's independent guard,
and records CPU, wall, retired instructions and peak memory. It also measures
the literals snapshot's seed-built parse-cli over every file of that snapshot's
source bundle S. Timings are observations for later ratios, not gate thresholds.
"""
from __future__ import annotations

import argparse
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import posixpath
import re
import statistics
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/vm-spec/bench'
SEED = ROOT / 'scripts/bend-reference'
BASE = '.toolchain/bend-2.0.29-574b6d3/bend2/base.bend'
IMPORT = re.compile(r'^import\s+(\S+)(?:\s+as\s+\S+)?\s*$')
FIELDS = {'real': r'([\d.]+) real', 'user': r'([\d.]+) user', 'sys': r'([\d.]+) sys',
          'max_rss_bytes': r'(\d+)\s+maximum resident set size',
          'instructions': r'(\d+)\s+instructions retired', 'cycles': r'(\d+)\s+cycles elapsed'}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def env():
    return {**os.environ, 'BEND_NO_TELEMETRY': '1'}


def build(source: Path, out: Path) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run([str(SEED), str(source), '-o', str(out)], cwd=ROOT, capture_output=True, text=True,
                       env=env(), timeout=1800)
    if p.returncode != 0 or not out.exists():
        raise SystemExit(f'build failed: {source}: {p.stderr[-2000:]}')
    return {'argv': ['scripts/bend-reference', str(source.relative_to(ROOT)), '-o', 'BINARY'],
            'binary_sha256': sha(out.read_bytes())}


def timed(argv, cwd=ROOT) -> dict:
    p = subprocess.run(['/usr/bin/time', '-l', *map(str, argv)], cwd=cwd, capture_output=True, env=env(),
                       timeout=3600)
    err = p.stderr.decode('utf-8', 'replace')
    row = {'exit': p.returncode, 'stdout': p.stdout.decode('utf-8', 'replace')}
    for key, pattern in FIELDS.items():
        m = re.search(pattern, err)
        row[key] = (float(m[1]) if key in ('real', 'user', 'sys') else int(m[1])) if m else None
    lines = err.splitlines(keepends=True)
    cut = next((i for i, l in enumerate(lines) if re.match(r'^\s+[\d.]+ real', l)), len(lines))
    row['stderr'] = ''.join(lines[:cut])
    return row


def host() -> dict:
    def text(argv):
        try:
            return subprocess.run(argv, capture_output=True, text=True).stdout.strip()
        except OSError:
            return None
    return {'platform': platform.platform(), 'machine': platform.machine(),
            'cpu': text(['sysctl', '-n', 'machdep.cpu.brand_string']), 'logical_cpus': os.cpu_count(),
            'load_average': list(os.getloadavg()), 'bun': text(['bun', '--version']),
            'clang': (text(['clang', '--version']) or '').splitlines()[0:1]}


def summary(samples: list) -> dict:
    out = {}
    for key in ('real', 'user', 'sys', 'instructions', 'cycles', 'max_rss_bytes'):
        values = [s[key] for s in samples if s[key] is not None]
        if values:
            out[key] = {'median': statistics.median(values), 'min': min(values), 'max': max(values)}
    return out


def workloads(repeat: int) -> dict:
    manifest = json.loads((HERE / 'workloads.json').read_text())
    rows = {}
    for w in manifest['workloads']:
        source = ROOT / w['source']
        assert sha(source.read_bytes()) == w['sha256'], w['name']
        binary = BUILD / w['name']
        built = build(source, binary)
        load_before = list(os.getloadavg())
        samples = [timed([binary]) for _ in range(repeat)]
        for s in samples:
            assert s['exit'] == 0 and s['stdout'] == w['expected_stdout'], (w['name'], s)
        rows[w['name']] = {'source_sha256': w['sha256'], **built, 'exit': 0, 'stdout': w['expected_stdout'],
                           'repeat': repeat, 'load_average_before': load_before,
                           'load_average_after': list(os.getloadavg()), 'summary': summary(samples),
                           'samples': [{k: s[k] for k in FIELDS} for s in samples]}
        print(f"{w['name']}: {rows[w['name']]['summary']['instructions']['median']} instructions (median)")
    return rows


def snapshot() -> tuple[Path, dict]:
    manifest = json.loads((ROOT / 'vm/oracles/manifest.json').read_text())['literals']
    files = json.loads(gzip.decompress((ROOT / manifest['archive']).read_bytes()))
    tree = BUILD / 'oracle-literals'
    for path, text in files.items():
        target = tree / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    return tree, manifest


def bundle(tree: Path, entry: str) -> list[dict]:
    """S: the entry's transitive imports, as the modules loader resolves them."""
    library = Path(os.environ.get('BEND_LIB', str(Path.home() / '.bend/lib'))).expanduser()
    local = tree / 'tests/compiler-modules/bundle/lib'
    found, pending = {}, [entry]
    while pending:
        name = pending.pop()
        if name in found:
            continue
        if name == BASE:
            path, origin = ROOT / BASE, 'base'
        elif name.startswith('0x'):
            path = library / name if (library / name).exists() else local / name
            origin = 'package'
        else:
            path, origin = tree / name, 'literals-snapshot'
        data = path.read_bytes()
        found[name] = {'path': name, 'origin': origin, 'sha256': sha(data), 'bytes': len(data),
                       'characters': len(data.decode('utf-8')), 'file': path}
        for line in data.decode().splitlines():
            m = IMPORT.match(line)
            if not m:
                continue
            spec = m[1]
            if spec == 'Base':
                pending.append(BASE)
            elif spec.startswith(('./', '../')):
                pending.append(posixpath.normpath(posixpath.join(posixpath.dirname(name), spec)))
            elif re.fullmatch(r'0x[0-9a-f]+/[^/]+\.bend', spec):
                pending.append(spec)
    return [found[k] for k in sorted(found)]


def parse_cli(repeat: int) -> dict:
    tree, manifest = snapshot()
    binary = BUILD / 'parse-cli'
    built = build(tree / 'src/parse-cli.bend', binary)
    built['argv'] = ['scripts/bend-reference', 'literals-snapshot/src/parse-cli.bend', '-o', 'BINARY']
    rows = []
    for f in bundle(tree, 'src/compile-cli.bend'):
        samples = [timed([binary, f['file']]) for _ in range(repeat)]
        first = samples[0]
        assert all(s['exit'] == first['exit'] and s['stdout'] == first['stdout'] for s in samples), f['path']
        kind = 'Parsed' if first['exit'] == 0 else (first['stderr'].split('\t', 1)[0] or f"exit {first['exit']}")
        rows.append({k: f[k] for k in ('path', 'origin', 'sha256', 'bytes', 'characters')} | {
            'exit': first['exit'], 'classification': kind, 'stdout_sha256': sha(first['stdout'].encode()),
            'stdout_bytes': len(first['stdout'].encode()), 'stderr': first['stderr'][:400],
            'summary': summary(samples)})
        print(f"{f['path']}: {kind} {rows[-1]['summary'].get('instructions', {}).get('median')}")
    return {'subject': 'seed-native parse-cli of the literals snapshot', 'commit': manifest['commit'],
            'entry': 'src/compile-cli.bend', **built, 'repeat': repeat,
            'total_instructions_median': sum(r['summary']['instructions']['median'] for r in rows),
            'files': rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repeat', type=int, default=5)
    parser.add_argument('--only', choices=('workloads', 'parse-cli'))
    args = parser.parse_args()
    stamp = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'host': host(),
             'seed': '2.0.29 574b6d3 (native lane, clang)'}
    if args.only != 'parse-cli':
        rows = workloads(args.repeat)
        (HERE / 'baselines.json').write_text(json.dumps({**stamp, 'workloads': rows}, indent=1) + '\n')
    if args.only != 'workloads':
        result = parse_cli(max(1, args.repeat // 2 + 1))
        (HERE / 'parse-cli.json').write_text(json.dumps({**stamp, **result}, indent=1) + '\n')


if __name__ == '__main__':
    main()
