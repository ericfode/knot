#!/usr/bin/env python3
"""Measure the core budget on the bootstrap corpus; no source-language semantics live here.

Build the current checker and a 1,048,576-node control from private source copies. Compare their outcomes on
every pre-round-13 corpus file. The new stress fixtures run only on the production bound: the larger control
would repeat the blowup this round bounds. Report every top-level src/*.bend outcome separately; Unsupported
sources do not establish that their cores fit. Run: python3 -B tests/compiler-nest/budget_corpus.py
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import check as gate

ROOT = gate.ROOT
HERE = Path(__file__).resolve().parent
BUILD = ROOT / '.local/compiler-nest/budget-corpus'
RECEIPT = HERE / 'receipts/round13-budget-corpus.json'
BOUND = 'def core_budget() -> U32:\n  65536'
STRESS = 'tests/compiler-nest/round13-fixtures/'
EXCLUDED = {'.git', '.local', '.toolchain', 'node_modules', 'build'}


def outcome(result):
    if result['exit'] == 0:
        gate.checked(result)
        return 'Accepted'
    gate.require(result['exit'] in (2, 3, 4) and not result['stdout'], ('unclassified', result))
    parts = result['stderr'].splitlines()[0].split('\t')
    gate.require(len(parts) >= 3, result)
    return '\t'.join(parts[:3])


def build(limit):
    directory = BUILD / str(limit)
    directory.mkdir(parents=True, exist_ok=True)
    for source in sorted((ROOT / 'src').glob('*.bend')):
        shutil.copy2(source, directory / source.name)
    source = directory / 'check.bend'
    text = source.read_text()
    gate.require(text.count(BOUND) == 1, 'Core-budget anchor moved')
    source.write_text(text.replace(BOUND, BOUND.replace('65536', str(limit))))
    binary = directory / 'check'
    built = gate.successful([*gate.SEED, directory / 'check-cli.bend', '-o', binary])
    return binary, {'limit': limit, 'check_sha256': gate.digest(source), 'binary_sha256': gate.digest(binary), 'build': built}


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    listed = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard', '--', '*.bend'], cwd=ROOT)
    names = sorted({os.fsdecode(name) for name in listed.split(b'\0') if name})
    names = [name for name in names if name.split('/')[0] not in EXCLUDED
             and not any(part == '.env' or part.startswith('.env.') for part in Path(name).parts)
             and (ROOT / name).is_file()]
    inputs = {name: gate.digest(ROOT / name) for name in names}
    record = {'status': 'incomplete', 'inputs': inputs, 'builds': [], 'files': {}}
    try:
        binaries = {}
        for limit in (65536, 1048576):
            binaries[limit], receipt = build(limit)
            record['builds'].append(receipt)

        def one(name):
            results = {}
            for limit, binary in binaries.items():
                if limit != 65536 and name.startswith(STRESS):
                    continue
                result = gate.run([binary, ROOT / name])
                results[str(limit)] = {'outcome': outcome(result),
                                      'stdout_sha256': hashlib.sha256(result['stdout'].encode()).hexdigest()}
            if not name.startswith(STRESS):
                gate.require(results['65536'] == results['1048576'], ('budget changes the earlier corpus', name, results))
            return name, results

        with ThreadPoolExecutor(max_workers=8) as pool:
            record['files'] = dict(pool.map(one, names))
        src = {name: rows['65536']['outcome'] for name, rows in record['files'].items()
               if Path(name).parent == Path('src')}
        record['src'] = src
        record['counts'] = {
            'files': len(names), 'pre_round13_files': sum(not name.startswith(STRESS) for name in names),
            'pre_round13_outcomes_changed': 0,
            'outcomes': dict(sorted(Counter(rows['65536']['outcome'] for rows in record['files'].values()).items())),
            'src_files': len(src), 'src_outcomes': dict(sorted(Counter(src.values()).items())),
            'src_exhausted': sorted(name for name, seen in src.items() if seen.startswith('Exhausted')),
            'src_checked': sorted(name for name, seen in src.items() if seen == 'Accepted'),
        }
        gate.require(all(gate.digest(ROOT / name) == digest for name, digest in inputs.items()), 'Corpus changed')
        record['status'] = 'passed'
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
