"""Fail-closed host transport validator; no Bend evaluation or ownership logic."""
import json
from pathlib import Path

LAYOUT = json.loads(Path(__file__).with_name('layout.json').read_text())
U32 = (1 << 32) - 1
MAX_BYTES = U32 - 3
DEFAULT = LAYOUT['defaultConfig']
ARITY = {1: 5, 2: 2, 3: 2, 4: 3, 5: 1, 6: 1, 7: 1,
         8: 5, 9: 4, 10: 2, 11: 3, 12: 1, 13: 4,
         14: 4, 15: 1, 16: 1, 17: 0}


class Boundary(Exception):
    def __init__(self, status, reason):
        super().__init__(reason)
        self.status, self.reason = status, reason


def require(test, status, reason):
    if not test:
        raise Boundary(status, reason)


def word(value):
    require(type(value) is int and 0 <= value <= U32, 'Invalid', 'u32')
    return value


def span(base, count, stride, limit):
    for value in (base, count, stride, limit):
        word(value)
    require(stride != 0, 'Invalid', 'zero-stride')
    require(base <= limit and count <= (limit - base) // stride,
            'Exhausted', 'storage-range')
    return base + count * stride


def layout(config, adapter_bytes=MAX_BYTES):
    require(type(config) is dict and set(config) == set(DEFAULT), 'Invalid', 'config-schema')
    for value in config.values():
        word(value)
    word(adapter_bytes)
    for field in ('rcLimit', 'idLimit', 'attemptLimit'):
        require(config[field] > 0, 'Invalid', field)
    limit = min(config['maxStorageBytes'], adapter_bytes, MAX_BYTES) // 4
    # Adding a stride is itself checked; neither a huge count nor a huge arity
    # reaches a multiplication or memory allocation before these guards.
    obj_stride = span(5, config['arity'], 1, U32)
    join_stride = span(8, config['arity'], 1, U32)
    cursor = span(0, 32, 1, limit)
    result = {'objectStride': obj_stride, 'joinStride': join_stride, 'guards': []}
    for name, count, stride in (
        ('objectBase', config['objects'], obj_stride),
        ('captureBase', config['captures'], 1),
        ('pendingBase', config['pending'], 1),
        ('joinBase', config['joins'], join_stride),
    ):
        result[name] = cursor
        end = span(cursor, count, stride, limit)
        result['guards'].append(end)
        cursor = span(end, 1, 1, limit)
    result['words'], result['bytes'] = cursor, cursor * 4
    return result


def within(first, count, length):
    require(first <= length and count <= length - first, 'Invalid', 'operand-range')


def instruction(cmd, config, code_count):
    require(type(cmd) is list and len(cmd) == 8, 'Invalid', 'instruction-stride')
    for value in cmd:
        word(value)
    op, a, b, c, d, e, f, g = cmd
    require(op in ARITY, 'Unsupported', 'opcode')
    require(not any(cmd[ARITY[op] + 1:]), 'Invalid', 'reserved-operand')
    cap, joins, arity = config['captures'], config['joins'], config['arity']
    def capture(index):
        require(index < cap, 'Invalid', 'capture-index')
    def join(index):
        require(index < joins, 'Invalid', 'join-index')
    if op == 1:
        capture(a)
        require(b in (0, 1), 'Invalid', 'object-kind')
        within(d, e, cap)
        require(not (e and d <= a < d + e), 'Invalid', 'construct-alias')
        require(e <= arity, 'Exhausted', 'arity')
    elif op in (2, 3):
        capture(a)
        capture(b)
        require(a != b, 'Invalid', 'capture-alias')
    elif op == 4:
        capture(a)
        within(b, c, cap)
        require(not (c and b <= a < b + c), 'Invalid', 'open-alias')
        require(c <= arity, 'Invalid', 'open-arity')
    elif op in (5, 12, 16):
        capture(a)
    elif op == 8:
        join(a)
        require(c < code_count, 'Invalid', 'continuation-code')
        within(d, e, cap)
        require(b <= arity, 'Exhausted', 'arity')
    elif op == 9:
        join(a)
        capture(d)
        require(c < arity, 'Invalid', 'join-slot')
    elif op == 10:
        join(a)
    elif op == 11:
        join(a)
        within(c, 0, cap)  # Dynamic join arity is checked by the interpreter.
    elif op == 13:
        require(c > 0, 'Invalid', 'zero-stride')
    elif op == 14:
        capture(a)
        require(c < code_count and d < code_count, 'Invalid', 'branch-code')
    elif op == 15:
        require(a < code_count, 'Invalid', 'jump-code')


def validate(bundle, adapter_bytes=MAX_BYTES):
    require(type(bundle) is dict, 'Invalid', 'bundle-schema')
    # Recognized headers precede interpreting a possibly different format.
    word(bundle.get('version'))
    require(bundle['version'] == 2, 'Unsupported', 'version')
    word(bundle.get('profile'))
    require(bundle['profile'] == 2, 'Unsupported', 'profile')
    require(set(bundle) in ({'version', 'profile', 'config', 'instructions'},
                           {'version', 'profile', 'config', 'instructions', 'layout'}),
            'Invalid', 'bundle-schema')
    config, code = bundle['config'], bundle['instructions']
    record_layout = layout(config, adapter_bytes)
    require(type(code) is list, 'Invalid', 'instruction-buffer')
    span(0, len(code), 8, min(config['maxStorageBytes'], adapter_bytes, MAX_BYTES) // 4)
    for cmd in code:
        instruction(cmd, config, len(code))
    if 'layout' in bundle:
        require(type(bundle['layout']) is dict and set(bundle['layout']) == set(record_layout),
                'Invalid', 'layout-schema')
        for name, value in bundle['layout'].items():
            if name == 'guards':
                require(type(value) is list and len(value) == 4, 'Invalid', 'layout-guards')
                for guard in value:
                    word(guard)
            else:
                word(value)
        require(bundle['layout'] == record_layout, 'Invalid', 'layout-mismatch')
    return record_layout


def initial_words(config, code_count):
    result = layout(config)
    words = [0] * result['words']
    fields = {**config, **result, 'version': 2, 'profile': 2,
              'nextIdentity': 1, 'instructionCount': code_count}
    for name, offset in LAYOUT['header'].items():
        words[offset] = fields.get(name, 0)
    for offset in result['guards']:
        words[offset] = LAYOUT['guard']
    return words


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--adapter-bytes', type=int, default=MAX_BYTES)
    args = parser.parse_args()
    try:
        data = json.loads(args.bundle.read_text())
        result = {'status': 'Validated', 'layout': validate(data, args.adapter_bytes)}
    except Boundary as failure:
        result = {'status': failure.status, 'reason': failure.reason}
    except json.JSONDecodeError:
        result = {'status': 'Invalid', 'reason': 'json'}
    except OSError as failure:
        result = {'status': 'HostFailure', 'reason': str(failure)}
    print(json.dumps(result))
    raise SystemExit({'Validated': 0, 'Invalid': 2, 'Unsupported': 3,
                      'Exhausted': 4, 'HostFailure': 5}[result['status']])


if __name__ == '__main__':
    main()
