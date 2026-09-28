#!/usr/bin/env python3
"""Gate vm-spec: frozen golden images against the pinned seed and eval-cli.

Re-executes both oracle lanes on every golden source and compares the frozen
observations byte for byte; re-derives the prim registry; checks that every
committed image equals its plan's encoding, decodes back to that plan and
passes the validator; and requires every negative control and mutant to be
rejected. It implements no VM and evaluates no image.
"""
from __future__ import annotations

import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'vm'
GOLDEN = HERE / 'golden'
BUILD = ROOT / '.local/vm-spec/gate'
SEED = ROOT / 'scripts/bend-reference'
SCALE = float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))  # hang guard only
EVAL_BUDGET = '1048576'
RECEIPT = HERE / 'receipts/spec.json'

spec = importlib.util.spec_from_file_location('serializer', HERE / 'serializer.py')
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def run(argv, timeout):
    argv = [str(x) for x in argv]
    try:
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=timeout * SCALE,
                           env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
    except subprocess.TimeoutExpired:
        return {'exit': None, 'outcome': 'harness-timeout', 'stdout': '', 'stderr': ''}
    return {'exit': p.returncode, 'stdout': p.stdout.decode('utf-8', 'replace'),
            'stderr': p.stderr.decode('utf-8', 'replace')}


def observed(result):
    return {k: result[k] for k in ('exit', 'stdout', 'stderr')}


# ------------------------------------------------------------------ oracles

def oracles() -> dict:
    """Extract the pinned evaluator snapshots and build their eval-cli natively."""
    manifest = json.loads((HERE / 'oracles/manifest.json').read_text())
    built = {}
    for lane, entry in manifest.items():
        raw = (ROOT / entry['archive']).read_bytes()
        require(sha(raw) == entry['sha256'], f'{lane} archive digest')
        files = json.loads(gzip.decompress(raw))
        require({p: sha(t.encode()) for p, t in files.items()} == entry['files'], f'{lane} snapshot files')
        tree = BUILD / 'oracles' / lane
        for path, text in files.items():
            target = tree / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.read_text() != text:
                target.write_text(text)
        built[lane] = {'tree': tree, 'commit': entry['commit']}

    def build(lane):
        out = BUILD / f'{lane}-eval'
        result = run([SEED, built[lane]['tree'] / 'src/eval-cli.bend', '-o', out], 600)
        require(result['exit'] == 0 and out.exists(), (lane, result))
        return lane, out

    with ThreadPoolExecutor(max_workers=2) as pool:
        for lane, out in pool.map(build, built):
            built[lane]['eval'] = out
            built[lane]['eval_sha256'] = sha(out.read_bytes())
    return built


def eval_argv(case, built):
    tool = built[case['lane']]['eval']
    prefix = ['--bundle', '.'] if case['lane'] == 'literals' else []
    return [tool, *prefix, case['source'], 'main', EVAL_BUDGET]


def seed_observation(case):
    if case.get('seed_lane') == 'native':
        out = BUILD / 'native' / case['name']
        out.parent.mkdir(parents=True, exist_ok=True)
        built = run([SEED, case['source'], '-o', out], 600)
        require(built['exit'] == 0, (case['name'], built))
        return run([out], 120)
    return run([SEED, case['source']], 120)


def lanes(case, built):
    return {'seed': observed(seed_observation(case)),
            'eval': observed(run(eval_argv(case, built), 120))}


# ------------------------------------------------------------------ registry

def derived_prims(snapshot: dict) -> list:
    text = snapshot['src/primitive.bend']

    def table(fn):
        body = text.split(f'def {fn}(op: O.Op)')[1].split('\ndef ')[0]
        return dict(re.findall(r'case O\.(\w+)\{\}: (.+)', body))

    name, code, inputs, qs, out = (table(f) for f in ('name', 'code', 'inputs', 'quantities', 'output'))
    order = re.findall(r'^  (\w+)\{\}$', snapshot['src/primitive-op.bend'], re.M)
    rows = []
    for i, op in enumerate(order):
        require(int(code[op]) == i, f'prim code order {op}')
        rows.append({'id': i, 'op': op, 'name': json.loads(name[op]), 'inputs': json.loads(inputs[op]),
                     'quantities': json.loads(qs[op]), 'output': json.loads(out[op])})
    return rows


def check_registry(registry: dict) -> dict:
    manifest = json.loads((HERE / 'oracles/manifest.json').read_text())
    snapshot = json.loads(gzip.decompress((ROOT / manifest['literals']['archive']).read_bytes()))
    rows = derived_prims(snapshot)
    require(registry['prims'][:len(rows)] == rows, 'registry prims differ from the literals derivation')
    extra = registry['prims'][len(rows):]
    require([p['id'] for p in registry['prims']] == list(range(len(registry['prims']))), 'prim ids')
    require(all(p.get('status') == 'reserved' for p in extra), 'unwitnessed prims must stay reserved')
    names = [p['name'] for p in registry['prims']]
    require(len(set(names)) == len(names) and names.index('U32.not') == 5, 'prim names')
    base = ROOT / registry['base']['path']
    require(sha(base.read_bytes()) == registry['base']['sha256'], 'pinned Base digest')
    for row in registry['foreign']:
        for path, digest in row['bodies'].items():
            if path.startswith('effs/'):
                require(sha((base.parent / path).read_bytes()) == digest, f'foreign body {path}')
    require([f['id'] for f in registry['foreign']] == list(range(len(registry['foreign']))), 'foreign ids')
    require(tuple(registry['representations']) == codec.REPRESENTATIONS, 'representation order')
    return {'prims': len(registry['prims']), 'derived': len(rows), 'reserved': len(extra),
            'foreign': len(registry['foreign'])}


# ------------------------------------------------------------------ freeze

def freeze(built):
    """Append observations for planned cases not yet frozen. Never rewrites a frozen row."""
    plan = json.loads((GOLDEN / 'plan.json').read_text())
    path = GOLDEN / 'expectations.json'
    frozen = json.loads(path.read_text())
    known = {c['name'] for c in frozen['cases']}
    fresh = [c for c in plan['cases'] if c['name'] not in known]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda c: lanes(c, built), fresh))
    for case, got in zip(fresh, results):
        row = dict(case)
        row['sha256'] = sha((ROOT / case['source']).read_bytes())
        row.update(got)
        frozen['cases'].append(row)
        print(f"froze {case['name']}: seed {got['seed']['exit']} {got['seed']['stdout']!r}; "
              f"eval {got['eval']['exit']} {got['eval']['stdout'] or got['eval']['stderr']!r}")
    path.write_text(json.dumps(frozen, indent=2) + '\n')


# ------------------------------------------------------------------ main

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze-new', action='store_true',
                        help='observe and append planned cases that have no frozen row')
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    built = oracles()
    if args.freeze_new:
        freeze(built)
        return 0
    raise SystemExit('image checks are not written yet')


if __name__ == '__main__':
    sys.exit(main())
