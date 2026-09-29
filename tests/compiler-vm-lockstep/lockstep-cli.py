#!/usr/bin/env python3
"""Lockstep one image on both machines and report the first divergence.

    python3 tests/compiler-vm-lockstep/lockstep-cli.py IMAGE FN FUEL [ORDINALS...]      # a Book
    python3 tests/compiler-vm-lockstep/lockstep-cli.py IMAGE FUEL -- [ARGS...]          # a Program
        [--wasm TEST_WASM] [--model MODEL_TRACE] [--stride K --from A --to B] [--mode auto|exact]

The model's trace entry (vm/model-trace.bend) and the VM's test build are built into .local/vm-lockstep
on first use. Exit 0 when the two machines agree on the complete state after every transition, 1 with
the first divergence otherwise, 2 when a side produced no trace.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LS = ROOT / 'tests/compiler-vm-lockstep'
LOCAL = ROOT / '.local/vm-lockstep'


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main(argv) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--wasm', type=Path, default=LOCAL / 'vm-test.wasm')
    parser.add_argument('--model', type=Path, default=LOCAL / 'model-trace')
    parser.add_argument('--stride', type=int, default=1)
    parser.add_argument('--from', dest='first', type=int, default=1)
    parser.add_argument('--to', dest='last', type=int, default=0)
    parser.add_argument('--mode', default='auto', choices=('auto', 'exact'))
    parser.add_argument('image', type=Path)
    parser.add_argument('words', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    L = load('lockstep', LS / 'lockstep.py')
    env = {**os.environ, 'BEND_NO_TELEMETRY': '1'}
    LOCAL.mkdir(parents=True, exist_ok=True)
    if not args.model.exists():
        subprocess.run([str(ROOT / 'scripts/bend-reference'), str(ROOT / 'vm/model-trace.bend'), '-o', str(args.model)], check=True, env=env)
    if not args.wasm.exists() and args.wasm == LOCAL / 'vm-test.wasm':
        subprocess.run([sys.executable, str(ROOT / 'vm/build.py'), '--test', str(args.wasm)], check=True, env=env)
    window = (args.stride, args.first, args.last)
    words = args.words
    m = L.run_model(args.model, args.image, words, window=window)
    v = L.run_vm(args.wasm, args.image, words, window=window)
    res = L.lockstep(m, v, mode=args.mode)
    d = res['divergence']
    if d is None:
        s = res['strength']
        what = f"refused alike ({res['refused']!r})" if res['refused'] else \
            f"{res['steps']} transitions, {res['states']} states compared ({s['layout']} layout, {s['graph']} graph, {s['exact']} exact)"
        print(f'{args.image.name}: the machines agree: {what}')
        for note, n in sorted({n: res['notes'].count(n) for n in res['notes']}.items()):
            print(f'  relation used {n}x: {note}')
        if res.get('effect_class') not in (None, 'none'):
            print(f"  effects: {res['effect_class']} ({len(res['effects'])})")
        return 0
    print(f'{args.image.name}: DIVERGENCE at transition {d.step}, in {d.field}: {d.detail}')
    if d.model is not None or d.vm is not None:
        print(f'  model: {d.model!r}\n  VM:    {d.vm!r}')
    if d.field not in ('harness', 'refusal', 'length'):
        by_step = {int(l.split("|", 1)[0]): l for l in m if l and l[0].isdigit()}
        for step in (d.step - 1, d.step):
            for name, lines in (('model', by_step), ('VM', {int(l.split('|', 1)[0]): l for l in v if l and l[0].isdigit()})):
                line = lines.get(step)
                if line:
                    f = line.split('|')
                    bump = int(f[6]) * (4 if name == 'model' else 1)
                    print(f'  transition {step} {name}: control {f[1]!r} act {f[2]} meters {f[3]!r} top {f[4]} frames {f[5][:120]!r} bump {bump}')
    return 2 if d.field == 'harness' else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
