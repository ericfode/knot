#!/usr/bin/env python3
"""Validate and execute records-2; CPU mode uses the existing research oracle."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'research/adaptive-tasks/runtime2'
sys.path.insert(0, str(RUNTIME))
from bundle import Boundary, LAYOUT, initial_words, validate, word  # noqa: E402
from driver import Driver, HALTED, FAULTED  # noqa: E402

CODES = {'Invalid': 2, 'Unsupported': 3, 'Exhausted': 4, 'HostFailure': 5, 'InternalFailure': 6}
STATUS = {1: 'Invalid', 2: 'Unsupported', 3: 'Exhausted', 5: 'InternalFailure'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def decode(words, original, layout):
    """Decode the published ABI, without interpreting any source or instruction."""
    if not isinstance(words, list) or len(words) != len(original):
        raise Boundary('InternalFailure', 'state-length')
    for value in words:
        word(value)
    if words[:17] != original[:17] or words[23] != original[23] or words[26:32] != original[26:32]:
        raise Boundary('InternalFailure', 'immutable-header')
    if any(words[g] != LAYOUT['guard'] for g in layout['guards']):
        raise Boundary('InternalFailure', 'capacity-guard')
    h = lambda name: words[LAYOUT['header'][name]]
    if h('phase') > 3 or h('pendingCount') > h('pending'):
        raise Boundary('InternalFailure', 'control-bounds')
    objects = []
    for slot in range(h('objects')):
        start = h('objectBase') + slot * h('objectStride')
        identity, kind, rc, arity, tag = words[start:start + 5]
        if arity > h('arity'):
            raise Boundary('InternalFailure', 'object-arity')
        objects.append([identity, kind, rc, tag, words[start + 5:start + 5 + arity]] if identity else [])
        if any(words[start + (5 + arity if identity else 0):start + h('objectStride')]):
            raise Boundary('InternalFailure', 'object-unused-payload')
    captures = words[h('captureBase'):h('captureBase') + h('captures')]
    pending = words[h('pendingBase'):h('pendingBase') + h('pendingCount')]
    if any(words[h('pendingBase') + len(pending):h('pendingBase') + h('pending')]):
        raise Boundary('InternalFailure', 'pending-unused-payload')
    joins = []
    for slot in range(h('joins')):
        start = h('joinBase') + slot * h('joinStride')
        head = words[start:start + 8]
        if head[2] > h('arity'):
            raise Boundary('InternalFailure', 'join-arity')
        joins.append([*head, words[start + 8:start + 8 + head[2]]])
        if any(words[start + 8 + head[2]:start + h('joinStride')]):
            raise Boundary('InternalFailure', 'join-unused-payload')
    state = [h('status'), h('reply'), h('nextIdentity'), h('readers'), h('freed'), objects, captures, pending, joins]
    return {'pc': h('pc'), 'phase': h('phase'), 'state': state}


def simulate(bundle, quantum, max_rounds, timeout):
    machine = Driver(bundle['config'], bundle['instructions'])
    deadline = time.monotonic() + timeout
    for rounds in range(1, max_rounds + 1):
        observation = machine.run(quantum)
        if observation['phase'] in (HALTED, FAULTED) or observation['state'][0]:
            return {'observation': observation, 'rounds': rounds, 'deviceExecution': False}
        if time.monotonic() >= deadline:
            return {'observation': observation, 'rounds': rounds, 'deviceExecution': False, 'exhausted': 'timeout'}
    return {'observation': machine.observe(), 'rounds': max_rounds, 'deviceExecution': False, 'exhausted': 'round-budget'}


def execute(bundle, cpu_only=True, quantum=64, max_rounds=1024, timeout=60, storage_bytes=16777216):
    layout = validate(bundle, storage_bytes)
    if cpu_only:
        return simulate(bundle, quantum, max_rounds, timeout)
    original = initial_words(bundle['config'], len(bundle['instructions']))
    request = {'bundle': bundle, 'words': original, 'layout': layout,
               'quantum': quantum, 'maxRounds': max_rounds}
    child = subprocess.run(['node', str(ROOT / 'scripts/run-records-device.mjs')],
                           input=json.dumps(request), text=True, capture_output=True, timeout=timeout)
    try:
        result = json.loads(child.stdout)
    except json.JSONDecodeError as error:
        raise Boundary('HostFailure', 'device-transport: ' + child.stderr.strip()) from error
    if child.returncode:
        raise Boundary(result.get('status', 'HostFailure'), result.get('reason', child.stderr.strip()))
    result['observation'] = decode(result.pop('words'), original, layout)
    return result


def outcome(result):
    if result.get('exhausted'):
        raise Boundary('Exhausted', result['exhausted'])
    observed = result['observation']
    status = observed['state'][0]
    if status:
        raise Boundary(STATUS.get(status, 'InternalFailure'), f'instruction-{observed["pc"]}')
    if observed['phase'] != HALTED:
        raise Boundary('InternalFailure', 'nonterminal-result')
    return observed['state'][1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--cpu-only', action='store_true')
    parser.add_argument('--quantum', type=int, default=64)
    parser.add_argument('--max-rounds', type=int, default=1024)
    parser.add_argument('--timeout', type=float, default=60)
    parser.add_argument('--storage-bytes', type=int, default=16777216)
    parser.add_argument('--receipt', type=Path)
    # These labels describe the already compiled invocation; they supply no inputs.
    parser.add_argument('--export', default='entry', dest='name')
    parser.add_argument('--arguments', type=int, nargs='*', default=[])
    args = parser.parse_args()
    receipt = {'schema': 1, 'profile': 'knot-gpu-records-2', 'status': 'incomplete',
               'mode': 'cpu-simulation' if args.cpu_only else 'metal', 'deviceExecution': False}
    code = 0
    try:
        import math
        for value in (args.quantum, args.max_rounds, args.storage_bytes, *args.arguments):
            word(value)
        if args.max_rounds == 0 or not math.isfinite(args.timeout) or args.timeout <= 0:
            raise Boundary('HostFailure', 'positive-round-and-time-budgets-required')
        raw = args.bundle.read_bytes()
        receipt['bundle_sha256'] = digest(raw)
        receipt['sources'] = {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in (
            Path(__file__), ROOT / 'scripts/run-records-device.mjs',
            *[RUNTIME / name for name in ('bundle.py', 'layout.json', 'driver.py', 'reference.py', 'runtime.wgsl')])}
        receipt.update(execute(json.loads(raw), args.cpu_only, args.quantum, args.max_rounds, args.timeout, args.storage_bytes))
        value = outcome(receipt)
        result = {'validated': True, 'export': args.name, 'arguments': args.arguments, 'result': value, 'bytes': len(raw)}
        receipt.update(status='pass', result=result)
        print(json.dumps(result))
    except json.JSONDecodeError:
        receipt.update(status='Invalid', reason='json'); code = 2
    except Boundary as error:
        receipt.update(status=error.status, reason=error.reason); code = CODES.get(error.status, 6)
    except (subprocess.TimeoutExpired, MemoryError):
        receipt.update(status='Exhausted', reason='host-budget'); code = 4
    except (OSError, subprocess.SubprocessError) as error:
        receipt.update(status='HostFailure', reason=str(error)); code = 5
    except Exception as error:
        receipt.update(status='InternalFailure', reason=f'{type(error).__name__}: {error}'); code = 6
    if code:
        print(f'{receipt["status"]}\trecords\t{receipt["reason"]}', file=sys.stderr)
    if args.receipt:
        try:
            args.receipt.parent.mkdir(parents=True, exist_ok=True)
            args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
        except OSError as error:
            print(f'HostFailure\treceipt\t{error}', file=sys.stderr)
            code = 5
    return code


if __name__ == '__main__':
    sys.exit(main())
