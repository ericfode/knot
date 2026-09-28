"""Independent literal boundaries for the host's checked transport arithmetic."""
from copy import deepcopy
from bundle import Boundary, DEFAULT, MAX_BYTES, U32, layout, span, validate


def controls():
    records = []
    def check(name, expected, action, value=None):
        try:
            result = action()
            observed = 'Ok'
        except Boundary as failure:
            observed, result = failure.status, None
        assert observed == expected, (name, expected, observed)
        if value is not None:
            assert result == value, (name, result, value)
        records.append({'name': name, 'status': observed})
    for size in (1, 2, 64, 4096):
        # Formula written from the record contract, independently of the
        # segmented layout implementation; includes all four guard words.
        config = {**DEFAULT, 'objects': size, 'captures': size,
                  'pending': size, 'joins': size, 'arity': 3}
        words = 36 + size * (8 + 1 + 1 + 11)
        exact = {**config, 'maxStorageBytes': words * 4}
        check(f'all-record-counts-{size}', 'Ok', lambda: layout(exact)['words'], words)
        check(f'storage-{size}-one-word-short', 'Exhausted',
              lambda: layout({**exact, 'maxStorageBytes': words * 4 - 4}))
        check(f'object-count-{size}-one-past', 'Exhausted',
              lambda: layout({**exact, 'objects': size + 1}))
        check(f'capture-count-{size}-one-past', 'Exhausted',
              lambda: layout({**exact, 'captures': size + 1}))
        check(f'pending-count-{size}-one-past', 'Exhausted',
              lambda: layout({**exact, 'pending': size + 1}))
        check(f'join-count-{size}-one-past', 'Exhausted',
              lambda: layout({**exact, 'joins': size + 1}))
    for byte_limit in (134217728, MAX_BYTES):
        maximum = (byte_limit // 4 - 36) // 5
        config = {**DEFAULT, 'objects': maximum, 'captures': 0, 'pending': 0,
                  'joins': 0, 'arity': 0, 'maxStorageBytes': byte_limit}
        check(f'device-limit-{byte_limit}', 'Ok', lambda: layout(config)['words'],
              36 + maximum * 5)
        check(f'device-limit-{byte_limit}-one-past', 'Exhausted',
              lambda: layout({**config, 'objects': maximum + 1}))
    check('arity-stride-overflow', 'Exhausted', lambda: layout({**DEFAULT, 'arity': U32}))
    check('product-overflow', 'Exhausted', lambda: span(16, 1073741824, 4, U32))
    check('addition-overflow', 'Exhausted', lambda: span(U32 - 1, 2, 1, U32))
    check('exact-u32-end', 'Ok', lambda: span(U32 - 1, 1, 1, U32), U32)
    check('base-past-limit', 'Exhausted', lambda: span(1, 0, 1, 0))
    check('zero-stride', 'Invalid', lambda: span(0, 0, 0, U32))
    check('minimum-layout', 'Ok', lambda: layout({**DEFAULT, 'objects': 0, 'captures': 0,
          'pending': 0, 'joins': 0, 'arity': 0, 'maxStorageBytes': 144})['words'], 36)
    check('header-does-not-fit', 'Exhausted', lambda: layout({**DEFAULT, 'maxStorageBytes': 127}))
    check('adapter-limit-overrides-bundle', 'Exhausted', lambda: layout(DEFAULT, 144))
    good = {'version': 2, 'profile': 2, 'config': dict(DEFAULT),
            'instructions': [[1,0,0,7,0,0,0,0]]}
    check('supported-bundle', 'Ok', lambda: validate(good))
    annotated = deepcopy(good)
    annotated['layout'] = layout(DEFAULT)
    check('canonical-layout', 'Ok', lambda: validate(annotated))
    annotated['layout']['objectStride'] = float(annotated['layout']['objectStride'])
    check('float-layout-word', 'Invalid', lambda: validate(annotated))
    changes = [
        ('unknown-version', 'Unsupported', lambda b: b.update(version=3)),
        ('unknown-profile', 'Unsupported', lambda b: b.update(profile=99)),
        ('unknown-opcode', 'Unsupported', lambda b: b.update(instructions=[[99]+[0]*7])),
        ('reserved-operand', 'Invalid', lambda b: b['instructions'][0].__setitem__(7, 1)),
        ('short-instruction', 'Invalid', lambda b: b.update(instructions=[[1,0]])),
        ('bool-word', 'Invalid', lambda b: b['instructions'][0].__setitem__(3, True)),
        ('negative-word', 'Invalid', lambda b: b['instructions'][0].__setitem__(3, -1)),
        ('oversize-word', 'Invalid', lambda b: b['instructions'][0].__setitem__(3, U32+1)),
        ('fraction-word', 'Invalid', lambda b: b['instructions'][0].__setitem__(3, 0.5)),
        ('invalid-kind', 'Invalid', lambda b: b['instructions'][0].__setitem__(2, 2)),
        ('capture-bounds', 'Invalid', lambda b: b['instructions'][0].__setitem__(1, 12)),
        ('range-overflow', 'Invalid', lambda b: b.update(instructions=[[1,0,0,7,U32,2,0,0]])),
        ('invalid-code', 'Invalid', lambda b: b.update(instructions=[[8,0,1,1,0,0,0,0]])),
        ('invalid-branch', 'Invalid', lambda b: b.update(instructions=[[14,0,7,0,1,0,0,0]])),
        ('invalid-jump', 'Invalid', lambda b: b.update(instructions=[[15,1,0,0,0,0,0,0]])),
        ('yield-reserved', 'Invalid', lambda b: b.update(instructions=[[17,1,0,0,0,0,0,0]])),
        ('offset-tamper', 'Invalid', lambda b: b.update(layout={'objectBase':0})),
        ('unknown-data', 'Invalid', lambda b: b.update(initialState=[1,2,3])),
        ('unknown-config', 'Invalid', lambda b: b['config'].update(extra=0)),
        ('zero-rc-limit', 'Invalid', lambda b: b['config'].update(rcLimit=0)),
        ('zero-id-limit', 'Invalid', lambda b: b['config'].update(idLimit=0)),
        ('zero-attempt-limit', 'Invalid', lambda b: b['config'].update(attemptLimit=0)),
        ('storage-cap', 'Exhausted', lambda b: b['config'].update(maxStorageBytes=144)),
    ]
    for name, outcome, change in changes:
        candidate = deepcopy(good)
        change(candidate)
        check(name, outcome, lambda: validate(candidate))
    # This fits the state but not 65 eight-word instructions.
    code_full = deepcopy(good)
    code_full['config']['maxStorageBytes'] = layout(DEFAULT)['bytes']
    code_full['instructions'] = [[7,0,0,0,0,0,0,0]] * (code_full['config']['maxStorageBytes'] // 32 + 1)
    check('instruction-buffer-one-past', 'Exhausted', lambda: validate(code_full))
    return records


if __name__ == '__main__':
    import json
    print(json.dumps({'status': 'pass', 'controls': len(controls())}))
