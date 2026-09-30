#!/usr/bin/env python3
"""Verify the pinned seed observations for the module/nest reconciliation.

--write freezes literal-review obligations from the ignored intake spec; normal
verification never changes expectations. Both native and Bun seed values stay
fixed. The module gate replays the same interpreter observations independently.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil

import check as gate

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'reconcile'
TARGET = gate.BUILD / 'reconcile'
EXPECT = HERE / 'reconcile.json'


def observations(fixture):
    path = TARGET / fixture['file']
    bundle = TARGET / 'em-hash/lib' if fixture['name'] == 'em-hash' else gate.BUNDLE
    interpreter = gate.run([*gate.SEED, path], bundle=bundle)
    wrapper = TARGET / 'seed-sources' / (fixture['name'] + '.bend')
    wrapper.parent.mkdir(exist_ok=True)
    wrapper.write_text(f'import Base\nimport ../{fixture["file"]} as F\n\ndef main() -> F.Light:\n  F.main()\n')
    lanes = {}
    for lane, suffix in [('native', ''), ('bun', '.js')]:
        output = TARGET / ('seed-' + fixture['name'] + suffix)
        built = gate.run([*gate.SEED, wrapper, '-o', output], bundle=bundle)
        seen = gate.run((['bun', output] if suffix else [output]), bundle=bundle) if built['exit'] == 0 else built
        lanes[lane] = gate.observation(seen)
    norm = lambda result: {k: v.replace(str(gate.ROOT), '<ROOT>') if isinstance(v, str) else v
                           for k, v in result.items()}
    call = norm(interpreter)
    if interpreter['exit'] == 0:
        # All result vocabularies and values are fixed by the intake's literal review.
        result = interpreter['stdout'].strip().removesuffix('{}')
        gate.require(result in fixture['result']['constructors'] and not interpreter['stderr'], (fixture, interpreter))
        call.update(constructor=result, tag=fixture['result']['constructors'].index(result))
        gate.require(all(l['exit'] == 0 and l['stdout'].endswith(interpreter['stdout']) and not l['stderr'] for l in lanes.values()), lanes)
    else:
        gate.require(interpreter['exit'] == 1 and interpreter['stderr'].startswith('Error:'), interpreter)
    return call, {name: norm(result) for name, result in lanes.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    data = ({'schema': 'knot-modules-reconciliation-1', 'seed': json.loads((HERE / 'expectations.json').read_text())['seed'],
             'purpose': 'Coordinator reconciliation; seed frozen before repairs. Native and Bun seed cross-checks.',
             'implementation_at_freeze': '85dcfb2a', 'fixtures': json.loads((gate.ROOT / '.local/modules/reconcile/spec.json').read_text())}
            if args.write else json.loads(EXPECT.read_text()))
    source_hashes = {p.relative_to(SOURCE).as_posix(): gate.digest(p) for p in sorted(SOURCE.rglob('*')) if p.is_file()}
    if not args.write: gate.require(data['sources'] == source_hashes, 'Reconciliation fixture sources changed')
    TARGET.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE, TARGET, dirs_exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(observations, data['fixtures']))
    for fixture, (seen, lanes) in zip(data['fixtures'], results):
        if args.write:
            fixture['calls'][0].update(seen)
            fixture['seed_lanes'] = lanes
        else:
            call = fixture['calls'][0]
            gate.require(gate.observation(seen) == gate.observation(call), (fixture['name'], seen, call))
            gate.require(lanes == fixture['seed_lanes'], (fixture['name'], lanes))
    data['sources'] = source_hashes
    if args.write: EXPECT.write_text(json.dumps(data, indent=2) + '\n')
    print(f"{'Frozen' if args.write else 'Verified'} reconciliation seed: {len(results)} programs, {2 * len(results)} native/Bun observations; "
          f"{sum(seen['exit'] == 0 for seen, _ in results)} accepted")


if __name__ == '__main__':
    main()
