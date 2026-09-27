#!/usr/bin/env python3
"""Thirty resumable, isolated author trajectories with an adaptive inducer search."""
import argparse
import concurrent.futures
import datetime
import gzip
import hashlib
import json
import random
import subprocess
import threading
import time
from pathlib import Path

import gate
import stimuli
import transport

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SETTINGS = [('gpt-6-astra', 'low'), ('gpt-6-sol', 'xhigh')]
COHORT = ('Pure bounded Conway Life in Bend 2.0.29: dead exterior, synchronous B3/S23, '
          'binary row-major boards of dimensions 0..32, step and exact Nat-count evolution. '
          'Every declaration materially supporting this contract is subject to current Perch policy.')
STOP = threading.Event()
PRINT = threading.Lock()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    p = Path(path)
    if not p.is_absolute(): p = ROOT/p
    raw = p.read_bytes()
    return json.loads(gzip.decompress(raw) if p.suffix == '.gz' else raw)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, ensure_ascii=False)+'\n'
    if path.exists():
        assert path.read_text() == data, f'Refuse changed receipt: {path}'
    else:
        with path.open('x') as stream: stream.write(data)


def emit(event, **fields):
    with PRINT:
        print(json.dumps(dict(at=now(), event=event, **fields)), flush=True)


def source_file(path, source):
    if path.exists(): assert path.read_text() == source
    else: path.write_text(source)


def command(argv, output, timeout=75):
    if output.exists(): return read(output)
    start = time.monotonic()
    try:
        p = subprocess.run(list(map(str, argv)), cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        record = dict(argv=list(map(str, argv)), exit=p.returncode, stdout=p.stdout, stderr=p.stderr)
    except subprocess.TimeoutExpired as error:
        decode = lambda x: x.decode(errors='replace') if isinstance(x, bytes) else x or ''
        record = dict(argv=list(map(str, argv)), exit=124, stdout=decode(error.stdout), stderr=decode(error.stderr), timeout=timeout)
    record['seconds'] = time.monotonic()-start
    write(output, record)
    return record


def author_prompt(trial, history):
    stimulus = '' if trial['stimulus'] is None else (HERE/'stimuli'/f"{trial['stimulus']}.txt").read_text()
    actual = hashlib.sha256(stimulus.encode()).hexdigest()
    assert actual == trial['stimulus_sha256']
    prompt = ('You are an independent author. Use only this complete packet. No tools.\n\n'
              '--- STIMULUS TO READ BEFORE DESIGN ---\n'+(stimulus or '(No stimulus.)\n')+
              '\n--- COMMON ASSIGNMENT AND REFERENCES ---\n'+(HERE/'inputs/common-packet.md').read_text())
    for item in history:
        prompt += '\n--- '+item['role']+' ---\n'+item['text']+'\n'
    prompt += '\nReturn only the requested JSON object with your complete current implementation.\n'
    return prompt


def request(trial, history, directory, ident):
    if STOP.is_set(): raise RuntimeError('Dispatch stopped by a shared provider failure')
    gate.check_files()
    receipt = transport.call(ident, author_prompt(trial, history), HERE/'schema.json',
                             directory, trial['model'], trial['effort'], timeout=600)
    if receipt['status'] != 'completed':
        STOP.set()
        raise RuntimeError('Author transport unavailable: '+str(receipt.get('error') or receipt['status']))
    response = read(receipt['response_path'])
    history.append({'role': 'YOUR PREVIOUS RESPONSE', 'text': json.dumps(response, ensure_ascii=False)})
    return response, receipt


def compile_source(source, directory, scratch, name):
    snapshot = directory/f'{name}.bend.snapshot'
    source_file(snapshot, source)
    target = scratch/f'{name}.bend'
    source_file(target, source)
    return snapshot, command([ROOT/'scripts/bend-reference', target, '--check-only'], directory/f'compiler-{name}.json')


def feedback(behavior, reviews):
    result = {'behavior': {k: behavior.get(k) for k in ('passed', 'status', 'error', 'counts') if k in behavior}}
    if reviews:
        result['review'] = {k: reviews.get(k) for k in ('passed', 'status', 'semantic_clean', 'style_passed', 'error') if k in reviews}
        if reviews.get('semantic_receipt'):
            sem = read(reviews['semantic_receipt'])
            result['semantic'] = {k: sem[k] for k in ('checked', 'clean', 'broken', 'issues') if k in sem}
        if reviews.get('style_receipt'):
            style = read(reviews['style_receipt'])
            result['style'] = dict(assessments=style.get('assessments', []),
                criticality=style.get('criticality', {}).get('assessments', []),
                diagnostics=style.get('diagnostics', {}).get('assessments', []),
                distributions=[{'target': r['target'], 'answers': r['answers'],
                                'context_truncated': r.get('context', {}).get('truncated')} for r in style.get('rows', [])])
    return result


def metrics(reviews):
    if not reviews or not reviews.get('style_receipt'): return {'fraction': 0.0, 'shortfall': 1.0}
    style = read(reviews['style_receipt'])
    assessments = style.get('assessments', [])
    if not assessments: return {'fraction': 0.0, 'shortfall': 1.0}
    fraction = sum(a['status']=='meets_target' for a in assessments)/len(assessments)
    shortfall = sum(max(0, 1-(a.get('probability_at_target') or 0)/a['minimum_probability']) for a in assessments)/len(assessments)
    return dict(fraction=fraction, shortfall=shortfall, assessments=len(assessments),
                style_summary=style['style_summary'])


def trial_run(trial):
    directory = HERE/'trials'/trial['id']
    directory.mkdir(parents=True, exist_ok=True)
    if (directory/'result.json').exists():
        saved = read(directory/'result.json')
        if saved['status'] == 'unavailable': STOP.set()
        return saved
    write(directory/'assignment.json', trial)
    history, rounds, previous_style, hashes = [], [], None, set()
    begun = time.monotonic()
    result = dict(**trial, status='started', full_pass=False, rounds_to_pass=None, rounds=[], at=now())
    emit('trial_started', id=trial['id'], model=trial['model'], effort=trial['effort'], wave=trial['wave'])
    try:
        for number in range(1, 4):
            if STOP.is_set(): raise RuntimeError('Dispatch stopped by a shared provider failure')
            directory_round = directory/f'round-{number:02d}'
            directory_round.mkdir(exist_ok=True)
            scratch = ROOT/'.local/life-inducer-hillclimb/authors'/trial['slot']/f'round-{number:02d}'
            scratch.mkdir(parents=True, exist_ok=True)
            history.append({'role': 'ROUND REQUEST', 'text': f'Round {number} of at most 3. '+
                            ('Write your initial implementation.' if number == 1 else
                             'Read your own prior feedback, state a concrete improvement hypothesis, then revise. Do not reroll unchanged code.')})
            response, receipt = request(trial, history, directory_round, 'author')
            first_source = response['source']
            source, compiler = compile_source(first_source, directory_round, scratch, 'first')
            report = dict(number=number, compiler_first_passed=compiler['exit']==0, compiler_repair=False,
                          full_pass=False, behavior_passed=False, semantic_clean=False)
            if compiler['exit']:
                history.append({'role': 'COMPILER DIAGNOSTIC REPAIR', 'text':
                    'The first source was rejected. One repair is allowed based only on this complete diagnostic. '
                    'Preserve your intended algorithm and contract.\n'+compiler['stdout']+'\n'+compiler['stderr']})
                response, repair_receipt = request(trial, history, directory_round, 'repair')
                source, compiler = compile_source(response['source'], directory_round, scratch, 'repaired')
                report['compiler_repair'] = True
            report['source_sha256'] = sha(source)
            report['source'] = str(source.relative_to(ROOT))
            behavior, reviews = {}, None
            cached_round = directory_round/'round.json'
            if cached_round.exists():
                saved = read(cached_round)
                assert saved['source_sha256'] == report['source_sha256']
                report = saved
                feedback_value = read(directory_round/'feedback.json')
                if saved.get('reviews_receipt'):
                    reviews = read(saved['reviews_receipt'])
                    if reviews.get('style_receipt'): previous_style = ROOT/reviews['style_receipt']
                hashes.add(report['source_sha256'])
            elif compiler['exit']:
                report['status'] = 'compiler_failed'
                report['metrics'] = dict(fraction=0.0, shortfall=1.0)
                feedback_value = {'compiler': {'exit': compiler['exit'], 'stdout': compiler['stdout'], 'stderr': compiler['stderr']},
                                  'note': 'The allowed repair did not pass; this round is exhausted.'}
            elif report['source_sha256'] in hashes:
                report['status'] = 'unchanged_submission'
                report['metrics'] = dict(fraction=0.0, shortfall=1.0)
                feedback_value = {'note': 'Exact source already submitted in this trajectory. No unchanged review was run.'}
            else:
                hashes.add(report['source_sha256'])
                behavior = gate.evaluate_behavior(source, directory_round, trial['id']+f'-r{number}')
                if behavior['status'] in ('evaluation_failure', 'configuration_failure'):
                    raise RuntimeError('Behavior gate unavailable: '+str(behavior.get('error')))
                report['behavior_passed'] = bool(behavior['passed'])
                report['behavior_receipt'] = behavior.get('behavior_receipt')
                report['status'] = 'behavior_failed'
                if behavior['passed']:
                    neutral = ROOT/'.local/life-inducer-hillclimb/review'/trial['slot']/'life.bend'
                    reviews = gate.evaluate_reviews(source, directory_round, neutral, COHORT, previous_style)
                    report['semantic_clean'] = bool(reviews.get('semantic_clean'))
                    report['full_pass'] = bool(reviews['passed'])
                    report['status'] = reviews['status']
                    report['reviews_receipt'] = reviews.get('reviews_receipt', str((directory_round/'reviews.json').relative_to(ROOT)))
                    if reviews.get('style_receipt'):
                        previous_style = ROOT/reviews['style_receipt']
                    if reviews.get('status') in ('provider_failure', 'configuration_failure'):
                        STOP.set()
                report['metrics'] = metrics(reviews)
                feedback_value = feedback(behavior, reviews)
            write(directory_round/'feedback.json', feedback_value)
            write(directory_round/'round.json', report)
            history.append({'role': 'YOUR ROUND FEEDBACK', 'text': json.dumps(feedback_value, ensure_ascii=False)})
            rounds.append(report)
            emit('round_completed', id=trial['id'], round=number, status=report['status'],
                 full_pass=report['full_pass'], fraction=report['metrics']['fraction'])
            if STOP.is_set():
                result.update(status='unavailable', error='Review unavailable; inspect round receipts')
                break
            if report['full_pass']:
                result.update(full_pass=True, rounds_to_pass=number)
                break
        if result['status'] != 'unavailable':
            result['status'] = 'passed' if result['full_pass'] else 'completed_no_full_pass'
    except Exception as error:
        STOP.set()
        result.update(status='unavailable', error=str(error))
        emit('trial_unavailable', id=trial['id'], error=str(error))
    result['rounds'] = rounds
    result['invocation_wall_seconds_including_replay'] = time.monotonic()-begun
    result['finished_at'] = now()
    first_receipt = directory/'round-01/author.receipt.json'
    if first_receipt.exists():
        first_at = read(first_receipt)['started_at']
        result['elapsed_seconds_including_interruptions'] = (
            datetime.datetime.fromisoformat(result['finished_at'])-datetime.datetime.fromisoformat(first_at)).total_seconds()
    eligible = [r for r in rounds if r['behavior_passed'] and r['semantic_clean']]
    result['eligible'] = bool(eligible)
    if eligible:
        best = max(eligible, key=lambda r:(r['full_pass'], r['metrics']['fraction'], -r['metrics']['shortfall'], -r['number']))
        result['selected_round'] = best['number']
        result['selected_source'] = best['source']
        result['metrics'] = best['metrics']
    else:
        result['metrics'] = dict(fraction=0.0, shortfall=1.0)
    write(directory/'result.json', result)
    emit('trial_completed', id=trial['id'], status=result['status'], rounds=len(rounds), full_pass=result['full_pass'])
    return result


def assignments(wave, candidates, start):
    data = []
    for stimulus in candidates:
        for model, effort in SETTINGS:
            n = start+len(data)
            text = '' if stimulus is None else (HERE/'stimuli'/f'{stimulus}.txt').read_text()
            data.append(dict(id=f'T{n:03d}', slot=f'slot-{n:02d}', wave=wave,
                stimulus=stimulus, stimulus_sha256=hashlib.sha256(text.encode()).hexdigest(),
                model=model, effort=effort, max_rounds=3))
    random.Random(20260927+wave).shuffle(data)
    return data


def wave_run(wave, tasks, workers):
    write(HERE/f'wave-{wave}-assignments.json', tasks)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        # Only submit a bounded active set; provider failure prevents queued dispatch.
        waiting = iter(tasks)
        active = {}
        def launch():
            if STOP.is_set(): return
            task = next(waiting, None)
            if task is not None: active[pool.submit(trial_run, task)] = task
        for _ in range(workers): launch()
        results = []
        while active:
            done, _ = concurrent.futures.wait(active, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                active.pop(future)
                results.append(future.result())
                launch()
    if STOP.is_set() or len(results) != len(tasks):
        raise RuntimeError('Wave incomplete; inspect unavailable receipts before any recovery')
    results.sort(key=lambda r:r['id'])
    write(HERE/f'wave-{wave}-results.json', results)
    return results


def select(wave, incumbent, candidates, results):
    rankings = []
    for stimulus in candidates:
        pair = [r for r in results if r['stimulus'] == stimulus]
        assert len(pair) == 2
        objective = [sum(r['full_pass'] for r in pair), sum(r['eligible'] for r in pair),
            -sum(r['rounds_to_pass'] or 4 for r in pair),
            sum(r['metrics']['fraction'] for r in pair)/2,
            -sum(r['metrics']['shortfall'] for r in pair)/2,
            -len((HERE/'stimuli'/f'{stimulus}.txt').read_bytes())]
        rankings.append(dict(stimulus=stimulus, objective=objective, trials=[r['id'] for r in pair]))
    rankings.sort(key=lambda r:(r['objective'], r['stimulus']==incumbent), reverse=True)
    selected = rankings[0]['stimulus']
    write(HERE/f'wave-{wave}-selection.json', dict(wave=wave, incumbent=incumbent, selected=selected,
          improved=selected!=incumbent, ranking=rankings))
    emit('selected', wave=wave, incumbent=incumbent, selected=selected, objective=rankings[0]['objective'])
    return selected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=3, choices=range(1,4))
    args = parser.parse_args()
    gate.check_files()
    stimuli.original()
    first = ['original']+[x['id'] for x in stimuli.neighbors('original', 1)]
    one = wave_run(1, assignments(1, first, 1), args.workers)
    incumbent = select(1, 'original', first, one)
    second = [incumbent]+[x['id'] for x in stimuli.neighbors(incumbent, 2)]
    two = wave_run(2, assignments(2, second, 11), args.workers)
    winner = select(2, incumbent, second, two)
    write(HERE/'selected-inducer.json', {'id':winner, 'sha256':sha(HERE/'stimuli'/f'{winner}.txt'),
          'frozen_before_validation':True, 'selection_waves':[1,2]})
    validation = assignments(3, ['original',winner,'original',winner,None], 21)
    for task in validation:
        index = (int(task['id'][1:])-21)//2
        task['validation_condition'] = ['original','selected','original','selected','none'][index]
    three = wave_run(3, validation, args.workers)
    all_trials = one+two+three
    assert len(all_trials) == len({r['id'] for r in all_trials}) == 30
    assert all(sum(r['model'] == model and r['effort'] == effort for r in all_trials) == 15 for model, effort in SETTINGS)
    write(HERE/'results.json', {'status':'completed', 'trials':len(all_trials), 'selected_inducer':winner,
          'full_passes':sum(r['full_pass'] for r in all_trials), 'results':all_trials})
    emit('experiment_completed', trials=len(all_trials), full_passes=sum(r['full_pass'] for r in all_trials))


if __name__ == '__main__':
    main()
