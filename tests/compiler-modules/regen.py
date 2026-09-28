#!/usr/bin/env python3
"""Re-run the pinned seed over the frozen modules fixtures and diff expectations.

Verification is the default and never writes. `--write` records the seed's
observations (command, exit, stdout, stderr, sources) into expectations.json
and keeps every hand-reviewed field: kinds, result types, constructors,
requires, knot obligations and knot_expected entries. This script contains no
Bend semantics; it only invokes the seed, normalizes absolute paths and
compares text.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SUITE = HERE.relative_to(ROOT).as_posix()
EXPECTATIONS = HERE / 'expectations.json'
SEED_DIR = '.toolchain/bend-2.0.29-574b6d3/bend2'
SEED = f'{SEED_DIR}/main.ts'
LIB = f'{SUITE}/bundle/lib'
HUB = f'{SUITE}/bundle/hub'
PACKAGE = re.compile(r'^0x[0-9a-f]{32}$')
TIMEOUT = 180


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def roots() -> list[str]:
    # Longest first, so a real path wins over a symlinked spelling of it.
    spellings = {str(ROOT), os.path.realpath(ROOT), os.path.abspath(ROOT)}
    return sorted(spellings, key=len, reverse=True)


def normalize(text: str) -> str:
    for spelling in roots():
        text = text.replace(spelling, '<ROOT>')
    return text


def environment() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith('BEND_')}
    env.update({'BEND_NO_TELEMETRY': '1', 'BEND_LIB': LIB,
                'BEND_HUB': 'file://' + os.path.realpath(ROOT / HUB)})
    return env


def command(target: str) -> str:
    return (f'cd <ROOT> && BEND_NO_TELEMETRY=1 BEND_LIB={LIB} '
            f'BEND_HUB=file://<ROOT>/{HUB} bun {SEED} {SUITE}/{target}')


def run(target: str) -> dict:
    try:
        p = subprocess.run(['bun', SEED, f'{SUITE}/{target}'], cwd=ROOT,
                           env=environment(), capture_output=True, text=True,
                           timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return {'command': command(target), 'exit': None, 'stdout': '',
                'stderr': f'harness timeout after {TIMEOUT}s'}
    return {'command': command(target), 'exit': p.returncode,
            'stdout': normalize(p.stdout), 'stderr': normalize(p.stderr)}


def package_hash(directory: Path) -> str:
    # The seed's publish identity (main.ts cli_publish): the first 32 hex digits
    # of sha256 over sorted "sha256(file) path\n" lines.
    paths = sorted(p.relative_to(directory).as_posix()
                   for p in directory.rglob('*') if p.is_file())
    lines = ''.join(sha256((directory / p).read_bytes()) + ' ' + p + '\n' for p in paths)
    return '0x' + sha256(lines.encode())[:32]


def bundle_state() -> dict:
    lib, hub = ROOT / LIB, ROOT / HUB
    state = {'packages': {}, 'names': {}, 'hub': sorted(
        p.relative_to(hub).as_posix() for p in hub.rglob('*') if p.is_file())}
    for entry in sorted(lib.iterdir()):
        if entry.name == 'names':
            for name in sorted(entry.iterdir()):
                state['names'][name.name] = name.read_text().strip()
        elif PACKAGE.match(entry.name) and entry.is_dir():
            state['packages'][entry.name] = {
                'content_hash': package_hash(entry),
                'files': {p.relative_to(entry).as_posix(): sha256(p.read_bytes())
                          for p in sorted(entry.rglob('*')) if p.is_file()}}
        else:
            state.setdefault('unexpected', []).append(entry.name)
    return state


def check_bundle(expected: dict, problems: list[str], when: str) -> None:
    state = bundle_state()
    for name, pkg in state['packages'].items():
        if pkg['content_hash'] != name:
            problems.append(f'bundle {when}: {name} content hashes to {pkg["content_hash"]}')
    for name, target in state['names'].items():
        if target not in state['packages']:
            problems.append(f'bundle {when}: name {name} points outside the bundle: {target}')
    if state.get('unexpected'):
        problems.append(f'bundle {when}: unexpected entries {state["unexpected"]}')
    if state['hub'] != ['README.md']:
        problems.append(f'bundle {when}: hub stub must hold only README.md, found {state["hub"]}')
    recorded = {'packages': expected.get('packages'), 'names': expected.get('names')}
    if recorded != {'packages': state['packages'], 'names': state['names']}:
        problems.append(f'bundle {when}: files differ from expectations.json bundle record')


def check_pins(data: dict, problems: list[str]) -> None:
    for name, digest in data['seed']['sha256'].items():
        actual = sha256((ROOT / SEED_DIR / name).read_bytes())
        if actual != digest:
            problems.append(f'seed pin: {name} is {actual}, expected {digest}')
    bun = subprocess.run(['bun', '--version'], capture_output=True, text=True).stdout.strip()
    if bun != data['tools']['bun']:
        problems.append(f'tool pin: bun {bun}, expected {data["tools"]["bun"]}')


def sources() -> dict[str, str]:
    files = [p for d in ('fixtures', 'calls') for p in (HERE / d).rglob('*') if p.is_file()]
    return {p.relative_to(HERE).as_posix(): sha256(p.read_bytes()) for p in sorted(files)}


def check_structure(data: dict, problems: list[str]) -> list[tuple[dict, dict]]:
    entries = {f['file'] for f in data['fixtures']}
    actual = {p.relative_to(HERE).as_posix() for p in (HERE / 'fixtures').glob('*.bend')}
    if entries != actual:
        problems.append(f'fixture set: unrecorded {sorted(actual - entries)}, '
                        f'absent {sorted(entries - actual)}')
    calls = [(f, c) for f in data['fixtures'] for c in f['calls']]
    wrappers = {c['run'] for _, c in calls if c['run'].startswith('calls/')}
    present = {p.relative_to(HERE).as_posix() for p in (HERE / 'calls').glob('*.bend')}
    if wrappers != present:
        problems.append(f'wrapper set: unrecorded {sorted(present - wrappers)}, '
                        f'absent {sorted(wrappers - present)}')
    helpers = {p.relative_to(HERE).as_posix() for p in (HERE / 'fixtures/lib').rglob('*') if p.is_file()}
    listed = {m for f in data['fixtures'] for m in f['modules'] if m.startswith('fixtures/')}
    if helpers - listed:
        problems.append(f'helper modules no fixture lists: {sorted(helpers - listed)}')
    for f in data['fixtures']:
        for m in f['modules']:
            if m.startswith('fixtures/') and m not in helpers:
                problems.append(f'{f["file"]}: listed module {m} does not exist')
        obligation = f['knot']['obligation']
        if (obligation == 'knot_expected') != ('knot_expected' in f):
            problems.append(f'{f["file"]}: knot_expected obligation/entry mismatch')
        if f['kind'] == 'negative' and obligation != 'reject':
            problems.append(f'{f["file"]}: negative fixtures carry the reject obligation')
        if f['calls'][0]['export'] != 'main' or f['calls'][0]['run'] != f['file']:
            problems.append(f'{f["file"]}: the first call runs the fixture main directly')
    return calls


def check_result(fixture: dict, call: dict, observed: dict, problems: list[str]) -> None:
    where = f'{call["run"]}'
    if call['run'] != fixture['file'] and call.get('wrapper_source') != (HERE / call['run']).read_text():
        problems.append(f'{where}: wrapper_source differs from the committed wrapper')
    for key in ('command', 'exit', 'stdout', 'stderr'):
        if call.get(key) != observed[key]:
            problems.append(f'{where}: {key} differs\n  expected {json.dumps(call.get(key))}\n'
                            f'  observed {json.dumps(observed[key])}')
    if fixture['kind'] == 'negative':
        if observed['exit'] == 0:
            problems.append(f'{where}: negative fixture was accepted by the seed')
        return
    # An accepted run prints exactly one nullary constructor of the declared
    # result enum. A wrapper prints it under the fixture's namespace.
    prefix = '' if call['run'] == fixture['file'] else '../' + fixture['file'][:-5] + '.'
    match = re.fullmatch(re.escape(prefix) + r'([A-Za-z_][A-Za-z0-9_]*)\{\}\n', observed['stdout'])
    constructors = fixture['result']['constructors']
    if observed['exit'] != 0 or match is None or match.group(1) not in constructors:
        problems.append(f'{where}: expected one {prefix}<{"|".join(constructors)}>{{}} line')
        return
    if call.get('constructor') != match.group(1) or call.get('tag') != constructors.index(match.group(1)):
        problems.append(f'{where}: constructor/tag record differs from observed {match.group(1)}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--write', action='store_true',
                        help='record observations into expectations.json (review the diff)')
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    data = json.loads(EXPECTATIONS.read_text())
    problems: list[str] = []

    check_pins(data, problems)
    if args.write:
        state = bundle_state()
        data['bundle'].update({'packages': state['packages'], 'names': state['names']})
    check_bundle(data['bundle'], problems, 'before')
    current = sources()
    if args.write:
        data['sources'] = current
    elif data.get('sources') != current:
        changed = sorted(set(current.items()) ^ set(data.get('sources', {}).items()))
        problems.append(f'sources differ from recorded hashes: {sorted({k for k, _ in changed})}')
    calls = check_structure(data, problems)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        observed = list(pool.map(lambda fc: run(fc[1]['run']), calls))
    for (fixture, call), seen in zip(calls, observed):
        if seen['exit'] is None:
            problems.append(f'{call["run"]}: {seen["stderr"]}')
            continue
        if args.write:
            call.update(seen)
            if call['run'] != fixture['file']:
                call['wrapper_source'] = (HERE / call['run']).read_text()
            if fixture['kind'] != 'negative':
                prefix = '' if call['run'] == fixture['file'] else '../' + fixture['file'][:-5] + '.'
                name = seen['stdout'].removeprefix(prefix).removesuffix('{}\n')
                if name in fixture['result']['constructors']:
                    call['constructor'] = name
                    call['tag'] = fixture['result']['constructors'].index(name)
        check_result(fixture, call, seen, problems)
    check_bundle(data['bundle'], problems, 'after')

    # A pin, bundle, structure or seed-contract failure never reaches the file.
    if args.write and not problems:
        EXPECTATIONS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    accepted = sum(1 for _, c in calls if c.get('exit') == 0)
    summary = (f'{len(data["fixtures"])} fixtures, {len(calls)} seed calls '
               f'({accepted} accepted, {len(calls) - accepted} rejected)')
    if problems:
        print('\n'.join(problems), file=sys.stderr)
        print(f'FAIL modules fixtures: {len(problems)} problem(s); {summary}', file=sys.stderr)
        return 1
    print(f'{"Recorded" if args.write else "Verified"} modules fixtures: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
