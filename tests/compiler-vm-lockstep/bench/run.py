#!/usr/bin/env python3
"""First VM speed ratio: knot-vm-1 against the seed's native lane on bump-sized variants of vm/bench.

    BEND_NO_TELEMETRY=1 python3 tests/compiler-vm-lockstep/bench/run.py [--repeat 5] [--out results.json]

Both lanes run every workload of workloads.json alternately, each as a whole process under
`/usr/bin/time -l`, as vm/bench/README.md prescribes ("subtract neither lane's start-up"): the seed
binary, and `node scripts/run-wasm-io.mjs vm/vm.wasm` on the image, which is the pinned release module.
The result records CPU (user + sys), cycles, retired instructions and peak memory for each sample, the
load average around it, and raw and null-subtracted ratios. Timings are observations, never a gate:
the gate (check.py) does not run this. The output is written only to --out.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import platform
import re
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/vm-lockstep/bench'
SEED = ROOT / 'scripts/bend-reference'
HOST = ROOT / 'scripts/run-wasm-io.mjs'
FROZEN = ROOT / 'vm/bench'
FIELDS = {'real': r'([\d.]+) real', 'user': r'([\d.]+) user', 'sys': r'([\d.]+) sys',
          'max_rss_bytes': r'(\d+)\s+maximum resident set size',
          'instructions': r'(\d+)\s+instructions retired', 'cycles': r'(\d+)\s+cycles elapsed'}
sys.path.insert(0, str(HERE))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def env():
    return {**os.environ, 'BEND_NO_TELEMETRY': '1'}


def timed(argv) -> dict:
    p = subprocess.run(['/usr/bin/time', '-l', *map(str, argv)], cwd=ROOT, capture_output=True, env=env(), timeout=3600)
    err = p.stderr.decode('utf-8', 'replace')
    row = {'exit': p.returncode, 'stdout': p.stdout.decode('utf-8', 'replace')}
    for key, pattern in FIELDS.items():
        m = re.search(pattern, err)
        row[key] = (float(m[1]) if key in ('real', 'user', 'sys') else int(m[1])) if m else None
    row['cpu'] = round((row['user'] or 0) + (row['sys'] or 0), 4)
    row['stderr'] = err.splitlines()[0] if err and not re.match(r'^\s+[\d.]+ real', err.splitlines()[0]) else ''
    return row


def machine() -> dict:
    def text(argv):
        try:
            return subprocess.run(argv, capture_output=True, text=True).stdout.strip()
        except OSError:
            return None
    return {'platform': platform.platform(), 'cpu': text(['sysctl', '-n', 'machdep.cpu.brand_string']), 'logical_cpus': os.cpu_count(),
            'memory_bytes': int(text(['sysctl', '-n', 'hw.memsize']) or 0), 'node': text(['node', '--version']), 'bun': text(['bun', '--version'])}


def summary(samples: list) -> dict:
    out = {}
    for key in ('cpu', 'user', 'sys', 'real', 'cycles', 'instructions', 'max_rss_bytes'):
        values = [s[key] for s in samples if s.get(key) is not None]
        if values:
            out[key] = {'median': statistics.median(values), 'min': min(values), 'max': max(values)}
    return out


def ratio(a: float, b: float):
    return round(a / b, 2) if b and b > 0 else None


# Units of work of each frozen workload (vm/bench/workloads.json shapes): rounds times the size of a round.
FROZEN_UNITS = {'deep-recursion': 4000 * 250000, 'peano': 200 * 1_000_000, 'list-fold': 240 * 1_000_000, 'string-scan': 900 * 10000}


def per_unit(row: dict, native: dict, vm: dict, null: dict, frozen_baselines: dict) -> dict:
    """Cycles per unit of work, start-up subtracted: the variant's, both lanes, and the seed's at the frozen size
    (vm/bench/baselines.json), which the variant's short seed run cannot resolve."""
    (unit, work), = row['work'].items()
    base = frozen_baselines['workloads'][row['frozen_workload']]['summary']['cycles']['median']
    seed_frozen = base / FROZEN_UNITS[row['frozen_workload']]
    seed_variant = (native['cycles']['median'] - null['native']['cycles']['median']) / work
    vm_variant = (vm['cycles']['median'] - null['vm']['cycles']['median']) / work
    return {'unit': unit, 'work': work, 'seed_cycles_per_unit_frozen_size': round(seed_frozen, 3),
            'seed_cycles_per_unit_variant': round(seed_variant, 3), 'vm_cycles_per_unit': round(vm_variant, 3),
            'ratio_vm_to_seed_frozen_size': ratio(vm_variant, seed_frozen), 'ratio_vm_to_seed_variant': ratio(vm_variant, seed_variant)}


def main(argv) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repeat', type=int, default=5)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise SystemExit(f'{args.out} exists; results are never overwritten')
    frozen = json.loads((HERE / 'workloads.json').read_text())
    cs = load('check_spec', ROOT / 'vm/check-spec.py')
    codec = cs.codec
    registry = codec.registry()
    digest = codec.base_digest(registry)
    workloads = load('bench_workloads', HERE / 'workloads.py')
    variants = workloads.variants()
    BUILD.mkdir(parents=True, exist_ok=True)
    sandbox = BUILD / 'images'
    sandbox.mkdir(exist_ok=True)

    jobs = []
    for row in frozen['workloads'] + [{**frozen['null'], 'name': 'null', 'expected_stdout': 'True{}\n'}]:
        name = row['name']
        source = ROOT / row['source']
        assert sha(source.read_bytes()) == row['source_sha256'], f'{name}: the frozen source changed'
        if name != 'null':
            assert workloads.frozen_source(row['frozen_workload']) is not None
            plan = variants[name]['plan']
        else:
            plan = workloads.null_book()
        image = codec.encode(plan, digest)
        assert sha(image) == row['image_sha256'], f'{name}: the frozen image changed'
        assert cs.rejected(image, registry, digest) is None, f'{name}: the reference codec refuses the image'
        (sandbox / f'{name}.kimg').write_bytes(image)
        binary = BUILD / f'seed-{name}'
        built = subprocess.run([str(SEED), str(source), '-o', str(binary)], cwd=ROOT, capture_output=True, text=True, env=env(), timeout=1800)
        assert built.returncode == 0 and binary.exists(), f'{name}: seed build failed: {built.stderr[-800:]}'
        jobs.append({'name': name, 'row': row, 'binary': binary})

    def native(job):
        return timed([job['binary']])

    def vm(job):
        return timed(['node', HOST, ROOT / 'vm/vm.wasm', sandbox, '--', f"{job['name']}.kimg", 'main', '4294967295'])

    samples = {j['name']: {'native': [], 'vm': []} for j in jobs}
    for i in range(args.repeat + (5 if args.repeat < 10 else 0)):
        for job in jobs:
            if job['name'] != 'null' and i >= args.repeat:
                continue
            for lane, fn in (('native', native), ('vm', vm)):
                before = os.getloadavg()[0]
                s = fn(job)
                s['load_1m_before'], s['load_1m_after'] = round(before, 2), round(os.getloadavg()[0], 2)
                want = job['row']['expected_stdout']
                good = s['exit'] == 0 and (s['stdout'] == want if lane == 'native' else re.fullmatch(r'Evaluated\t\d+\t1\tTrue\{\}\n', s['stdout']) is not None)
                assert good, f"{job['name']} {lane}: {s}"
                samples[job['name']][lane].append(s)

    null = {lane: summary(samples['null'][lane]) for lane in ('native', 'vm')}
    frozen_baselines = json.loads((FROZEN / 'baselines.json').read_text())
    rows = {}
    for job in jobs:
        name = job['name']
        if name == 'null':
            continue
        n, v = summary(samples[name]['native']), summary(samples[name]['vm'])
        row = job['row']
        net_native = n['cpu']['median'] - null['native']['cpu']['median']
        net_vm = v['cpu']['median'] - null['vm']['cpu']['median']
        entry = {'source_sha256': row['source_sha256'], 'image_sha256': row['image_sha256'], 'work': row['work'],
                 'repeat': args.repeat, 'native': n, 'vm': v,
                 'ratio_cpu_raw': ratio(v['cpu']['median'], n['cpu']['median']),
                 'ratio_cpu_min_of_min': ratio(v['cpu']['min'], n['cpu']['min']),
                 'ratio_cpu_null_subtracted': ratio(net_vm, net_native) if net_native > 0.05 else None,
                 'cpu_note': 'user + sys is read to 10 ms by /usr/bin/time: a seed run under about 50 ms is not resolved by it, so cycles, which are not rounded, carry those rows',
                 'ratio_cycles_raw': ratio(v['cycles']['median'], n['cycles']['median']),
                 'ratio_cycles_null_subtracted': ratio(v['cycles']['median'] - null['vm']['cycles']['median'],
                                                       n['cycles']['median'] - null['native']['cycles']['median']),
                 'per_unit': per_unit(row, n, v, null, frozen_baselines),
                 'samples': {lane: [{k: s[k] for k in ('cpu', 'user', 'sys', 'real', 'cycles', 'instructions', 'max_rss_bytes', 'load_1m_before', 'load_1m_after')}
                                    for s in samples[name][lane]] for lane in ('native', 'vm')}}
        rows[name] = entry
    result = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'host': machine(),
              'load_average_at_start_and_end': [list(os.getloadavg())],
              'protocol': 'whole-process CPU (user + sys) and cycles under /usr/bin/time -l, lanes alternated; the VM is the pinned release vm.wasm through scripts/run-wasm-io.mjs',
              'null_program': null, 'workloads': rows}
    args.out.write_text(json.dumps(result, indent=1) + '\n')
    print(json.dumps({k: {'cpu_raw': v['ratio_cpu_raw'], 'cycles_raw': v['ratio_cycles_raw'], 'cycles_net': v['ratio_cycles_null_subtracted'],
                          'per_unit_frozen_size': v['per_unit']['ratio_vm_to_seed_frozen_size'],
                          'seed_cpu': v['native']['cpu']['median'], 'vm_cpu': v['vm']['cpu']['median']} for k, v in rows.items()}, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
