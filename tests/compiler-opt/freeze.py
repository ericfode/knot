#!/usr/bin/env python3
"""Append reviewed off-path hashes without rewriting an earlier frozen entry."""
from __future__ import annotations

import argparse
import datetime
import json

import check as gate


def select(cases, pinned, names):
    by_key = {case['key']: case for case in cases}
    gate.require(names and len(set(names)) == len(names), 'select distinct new corpus keys')
    gate.require(set(names) <= set(by_key), ('unknown corpus key', sorted(set(names) - set(by_key))))
    selected = [by_key[name] for name in names]
    gate.require(all(case['file'] not in pinned for case in selected),
                 'an existing frozen baseline cannot be replaced; investigate off-byte drift separately')
    gate.require(len({case['file'] for case in selected}) == len(selected), 'select each source once')
    return selected


def freeze(cases, directory):
    commands, builds = {}, []
    for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun', '--no-env-file'])]:
        commands[lane] = {}
        for phase, entry in [('compile', 'tests/compiler-fields-wasm/compile.bend'), ('eval', 'src/eval-cli.bend')]:
            output = directory / (phase + suffix)
            builds.append(gate.successful([*gate.SEED, gate.ROOT / entry, '-o', output]))
            commands[lane][phase] = [*runtime, output]
    rows = []
    for case in cases:
        source = gate.corpus_path(case)
        source_hash = gate.digest(source)
        reference = gate.reference(case)
        lanes = {}
        for lane, command in commands.items():
            output = directory / (case['key'] + '-' + lane + '.wasm')
            built = gate.compiled(command['compile'], source, output, case.get('compile_budgets', []))
            _, abi = gate.decode(output)
            observations = []
            for call in case['calls']:
                evaluated = gate.run([*command['eval'], source, call['export'], 1048576, *call['arguments']])
                if 'eval_exhausted' in case:
                    gate.diagnostic(evaluated, 4, case['eval_exhausted'])
                elif call.get('structured_result'):
                    gate.observe(evaluated, call['expected_eval'])
                else:
                    gate.enum_value(evaluated, case, call)
                observation = {'call': call, 'evaluator': evaluated}
                if not call.get('structured_result'):
                    actual = gate.host(output, call)
                    gate.host_value(actual, call)
                    observation['wasm'] = actual
                observations.append(observation)
            lanes[lane] = {'build': built, 'wasm_sha256': gate.digest(output), 'bytes': output.stat().st_size,
                           'abi': abi, 'observations': observations}
        gate.require(lanes['native']['wasm_sha256'] == lanes['bun']['wasm_sha256'], 'off compiler lanes disagree')
        gate.require(gate.digest(source) == source_hash, 'source changed during freeze')
        rows.append({'source': case['file'], 'source_sha256': source_hash,
                     'budgets': case.get('compile_budgets', []), 'wasm_sha256': lanes['native']['wasm_sha256'],
                     'bytes': lanes['native']['bytes'], 'abi': lanes['native']['abi'],
                     'frozen_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                     'reference': reference, 'lanes': lanes})
    return rows, builds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', action='append', required=True, help='a corpus key reported as unfrozen_off_programs')
    parser.add_argument('--append', action='store_true', help='append to extensions.json after successful checks')
    args = parser.parse_args()
    gate.require(gate.os.environ.get('BEND_NO_TELEMETRY') == '1', 'export BEND_NO_TELEMETRY=1')
    read = lambda name: json.loads((gate.HERE / name).read_text())
    frozen, baseline, extensions, regressions = map(read, ['expectations.json', 'baseline.json', 'extensions.json', 'regressions.json'])
    for name, expected in frozen['seed_hashes'].items():
        gate.require(gate.digest(gate.ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2' / name) == expected,
                     ('pinned seed changed', name))
    cases, _ = gate.load_corpus(frozen, baseline, extensions, regressions)
    selected = select(cases, gate.baselines(baseline, extensions, regressions), args.case)
    selected_files = {case['file'] for case in selected}
    pinned = gate.baselines(baseline, extensions, regressions)
    for case in selected:
        if any(call.get('structured_result') for call in case['calls']):
            observer = next(c for c in cases if c.get('original') == case['file'])
            gate.require(observer['file'] in selected_files or observer['file'] in pinned,
                         ('also select the seeded exact-tree observer', observer['key']))
    directory = gate.BUILD / 'freeze'
    directory.mkdir(parents=True, exist_ok=True)
    rows, builds = freeze(selected, directory)
    result = gate.Normalizer(gate.ROOT).value({'status': 'checked', 'baselines': rows, 'builds': builds})
    candidate = directory / 'candidate.json'
    candidate.write_bytes(gate.json_bytes(result))
    if args.append:
        extensions['baselines'].extend(result['baselines'])
        (gate.HERE / 'extensions.json').write_bytes(gate.json_bytes(extensions))
    print(json.dumps({'status': 'appended' if args.append else 'candidate',
                      'sources': [row['source'] for row in rows], 'evidence': str(candidate.relative_to(gate.ROOT))}))


if __name__ == '__main__':
    main()
