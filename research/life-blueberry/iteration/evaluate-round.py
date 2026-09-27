#!/usr/bin/env python3
"""Freeze and evaluate one authorized revision without changing the fixed gates."""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPERIMENT = HERE.parent
RULES = 'bend-machine-arithmetic,bend-fuel-completeness,perf-growing-prefix-copy,perf-linked-list-indexing'
SLOTS = {'arm-a': 'slot-2', 'arm-b': 'slot-1'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def relative(path):
    return str(path.relative_to(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('arm', choices=SLOTS)
    parser.add_argument('round', type=int, choices=range(1, 11))
    args = parser.parse_args()
    directory = HERE / args.arm / f'round-{args.round:02d}'
    source = directory / 'life.bend'
    assert source.exists() and (directory / 'hypothesis.md').exists()
    assert (directory / 'first.bend.snapshot').exists(), 'Save the first compiler input'
    assert not (directory / 'started.json').exists(), 'A round may run only once'
    if args.round > 1:
        prior = read(HERE / args.arm / f'round-{args.round-1:02d}' / 'round.json')
        assert not prior.get('full_pass'), 'Stop at the first full pass'
    preserved = read(HERE / 'preserve.json')
    for path, digest in preserved['frozen_sha256'].items():
        assert sha(ROOT / path) == digest, 'Changed fixed evidence: ' + path
    previous_hashes = {preserved['originals'][args.arm]['sha256']}
    previous_hashes.update(read(p)['source_sha256'] for p in (HERE / args.arm).glob('round-*/round.json'))
    assert sha(source) not in previous_hashes, 'No unchanged candidate rerolls'
    report = {'arm': args.arm, 'round': args.round, 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'source': relative(source), 'source_sha256': sha(source), 'status': 'started', 'full_pass': False}
    write(directory / 'started.json', report)
    shutil.copyfile(source, directory / 'submitted.bend.snapshot')

    def run(label, argv, timeout=180):
        start = time.monotonic()
        try:
            process = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
            record = {'argv': argv, 'exit': process.returncode, 'stdout': process.stdout, 'stderr': process.stderr}
        except subprocess.TimeoutExpired as error:
            decode = lambda s: s.decode(errors='replace') if isinstance(s, bytes) else (s or '')
            record = {'argv': argv, 'exit': None, 'timeout': timeout, 'stdout': decode(error.stdout), 'stderr': decode(error.stderr)}
        record['seconds'] = time.monotonic() - start
        write(directory / (label + '-command.json'), record)
        return record

    try:
        gate = directory / f'{args.arm}-round-{args.round:02d}-gates.json'
        run('gates', ['python3', relative(EXPERIMENT / 'gates/evaluate.py'), relative(source), relative(gate)], 360)
        behavior = read(gate)
        report['behavior_passed'] = behavior['passed']
        report['behavior_receipt'] = relative(gate)
        if not behavior['passed']:
            report['status'] = 'deterministic_failure'
            return 3
        neutral = ROOT / '.local/life-loop' / SLOTS[args.arm] / 'life.bend'
        neutral.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, neutral)
        before_usage = set((ROOT / '.perch/usage').glob('*.json'))
        semantic_cmd = run('semantic', ['npm', 'run', 'lint', '--', relative(neutral), '--rules', RULES])
        raw = semantic_cmd['stdout']
        semantic = json.JSONDecoder().raw_decode(raw[raw.index('{'):])[0]
        write(directory / 'semantic.json', semantic)
        usages = []
        for receipt in set((ROOT / '.perch/usage').glob('*.json')) - before_usage:
            item = read(receipt)
            if item.get('command') == 'check' and item.get('target') == relative(neutral):
                usages.append(item)
        assert len(usages) == 1, 'Expected one matching semantic usage receipt'
        usage = usages[0]
        write(directory / 'semantic-usage.json', usage)
        assert semantic_cmd['exit'] in (0, 3)
        assert semantic['checked'] > 0 and usage['provider_requests'] == usage['provider_responses'] > 0
        assert usage['models'] == ['jev-1.13.0'], 'Judge model changed'
        report['semantic_checked'] = semantic['checked']
        report['semantic_clean'] = semantic['clean']
        output = directory / 'style.json.gz'
        argv = ['npm', 'run', 'lint:style', '--', '--live', relative(neutral),
                '--cohort=' + (HERE / 'cohort.txt').read_text().strip(), '--jobs=2', '--output=' + relative(output)]
        past = sorted((HERE / args.arm).glob('round-*/style.json.gz'))
        if past:
            argv.append('--reuse=' + relative(past[-1]))
        style_cmd = run('style', argv)
        style = read(output)
        assert style_cmd['exit'] in (0, 3) and style['status'] == 'completed'
        assert style['coverage']['ranked'] == style['coverage']['selected'] > 0
        assert style['provider_requests'] == style['provider_responses']
        assert style['source_freshness']['status'] == 'current'
        assert all(row['model'] == 'jev-1.13.0' for row in style['rows'])
        assert all(not row['context']['truncated'] for row in style['rows'])
        assert sha(source) == sha(neutral) == report['source_sha256']
        report['style_coverage'] = style['coverage']
        report['style_summary'] = style['style_summary']
        report['style_requests'] = style['provider_requests']
        report['style_responses'] = style['provider_responses']
        report['style_reused'] = style['reused_units']
        report['full_pass'] = bool(semantic['clean'] and style_cmd['exit'] == 0)
        report['status'] = 'passed' if report['full_pass'] else 'attention'
        return 0 if report['full_pass'] else 3
    except Exception as error:
        report['status'] = 'evaluation_failure'
        report['error'] = str(error)
        return 1
    finally:
        write(directory / 'round.json', report)
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    raise SystemExit(main())
