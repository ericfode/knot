"""Literal/formula controls, fixed before implementing the device transitions.

The formulas are elementary empty/leaf states, not a second execution of the
interpreter. Large cases sample first, exact-full and rejected-full snapshots.
"""


def cases():
    result = []
    for size in (1, 2, 64, 4096):
        result.append({
            'name': f'objects-{size}-plus-one',
            'config': {'objects': size, 'captures': size + 1, 'pending': 1,
                       'joins': 0, 'arity': 0},
            'commands': [[1, i, 0, i + 1, 0, 0] for i in range(size + 1)],
            'observeIndexes': sorted({0, size - 1, size}),
            'expect': {'statuses': [0] * size + [3],
                       'final': {'nextIdentity': size + 1, 'freed': 0,
                                 'live': size, 'pending': [],
                                 'captures': {str(i): i + 1 for i in range(size)}}}})
    def add(name, commands, statuses, config=None, final=None):
        result.append({'name': name, 'commands': commands,
                       'config': config or {},
                       'expect': {'statuses': statuses, **({'final': final} if final else {})}})
    add('objects-zero', [[1, 0, 0, 7, 0, 0]], [3], {'objects': 0})
    add('captures-one-past', [[1, 1, 0, 7, 0, 0]], [1], {'captures': 1})
    add('rc-exact-and-one-past', [[1,0,1,7,0,0],[2,0,1],[2,0,2],[5,1],[6,1],[12,0]],
        [0,0,3,0,0,0], {'rcLimit': 2})
    add('identity-exact-and-one-past', [[1,0,0,7,0,0],[5,0],[6,1],[1,0,0,9,0,0],[1,1,0,11,0,0]],
        [0,0,0,0,3], {'idLimit': 2},
        {'nextIdentity':0,'freed':1,'live':1,'pending':[],'captures':{'0':2}})
    add('pending-zero', [[1,0,0,7,0,0],[5,0]], [0,3], {'pending': 0})
    add('pending-one-past', [[1,0,0,7,0,0],[1,1,0,9,0,0],[5,0],[5,1],[6,1],[5,1],[6,1]],
        [0,0,0,3,0,0,0], {'pending':1})
    add('cleanup-expansion-preserves-stack',
        [[1,0,0,7,0,0],[1,1,0,9,0,0],[1,2,0,13,0,2],[5,2],[6,1]],
        [0,0,0,0,3], {'pending':1},
        {'nextIdentity':4,'freed':0,'live':3,'pending':[3],'captures':{}})
    add('arity-one-past', [[1,0,0,7,0,0],[1,1,0,9,0,0],[1,2,0,13,0,2]],
        [0,0,3], {'arity':1})
    add('open-wrong-arity', [[1,0,0,7,0,0],[4,0,1,1],[12,0]],
        [0,1,0], {'arity':0, 'captures':2})
    add('malformed-before-resource', [[1,0,0,7,0,0],[1,0,0,9,1,1],
        [1,2,0,9,1,1],[1,2,1,9,0,1],[8,0,0,0,8,2],
        [8,0,1,0,8,2],[8,1,1,0,9,1]], [0,1,1,1,0,1,1], {'arity':0})
    add('attempt-exact-and-one-past', [[8,0,1,0,8,0],[10,0,1],[8,0,1,0,8,0],
                                     [10,0,2],[8,0,1,0,8,0]],
        [0,0,0,0,3], {'attemptLimit':2})
    add('join-one-past', [[8,0,0,0,8,0],[8,1,0,0,8,0]], [0,1], {'joins':1})
    add('nullary-join-once', [[8,0,0,0,8,0],[11,0,1,0],[11,0,1,0]], [0,0,1])
    add('cancel-pending-capacity', [[1,8,0,7,0,0],[1,0,0,9,0,0],
                                   [8,0,2,0,8,1],[9,0,1,1,0],[10,0,1]],
        [0,0,0,0,3], {'pending':1})
    add('shared-open-duplicate-overflow', [[1,0,1,7,0,0],[2,0,1],[1,2,1,13,0,2],
                                        [2,2,3],[4,2,4,2],[12,2],[12,3]],
        [0,0,0,0,3,0,0], {'rcLimit':3})
    add('shared-open-duplicate-exact', [[1,0,1,7,0,0],[2,0,1],[1,2,1,13,0,2],
                                     [2,2,3],[4,2,4,2],[5,3],[5,4],[5,5],[6,6]],
        [0,0,0,0,0,0,0,0,0], {'rcLimit':4},
        {'nextIdentity':3,'freed':2,'live':0,'pending':[],'captures':{}})
    add('list-shared-tail', [[1,0,1,0,0,0],[1,1,1,7,0,1],[2,1,4],
                            [1,2,1,9,1,1],[5,2],[6,2],[12,4],[5,4],[6,2]],
        [0,0,0,0,0,0,0,0,0], final=
        {'nextIdentity':4,'freed':3,'live':0,'pending':[],'captures':{}})
    add('type-not-shareable', [[1,0,0,7,0,0],[2,0,1],[12,0]], [0,2,0])
    add('data-cannot-own-type', [[1,0,0,7,0,0],[1,1,1,9,0,1],[12,0]], [0,1,0])
    add('overlapping-join-captures', [[8,0,1,0,8,2],[8,1,1,0,9,2]], [0,1])
    add('cancel-empty-then-resume-stale', [[8,0,1,0,8,0],[10,0,1],[11,0,1,0]], [0,0,1])
    size = 64
    add('nary-64-ordered',
        [[1,i,0,i+1,0,0] for i in range(size)] + [[8,0,size,0,65,0]] +
        [[9,0,1,i,i] for i in reversed(range(size))] + [[1,64,0,99,0,0],[9,0,1,0,64]],
        [0] * (2 * size + 2) + [1],
        {'objects':65, 'captures':66, 'joins':1, 'arity':64},
        {'nextIdentity':66,'freed':0,'live':65,'pending':[],'captures':{'64':65},
         'joins':{'0':[1,2,64,64,1,0,65,0,list(range(1,65))]}})
    add('completion-count-across-attempts', [[8,0,0,0,8,0],[11,0,1,0],
                                          [8,0,0,0,8,0],[11,0,2,0]],
        [0,0,0,0], final={'nextIdentity':1,'freed':0,'live':0,'pending':[],
                         'captures':{},'joins':{'0':[2,4,0,0,2,0,8,0,[]]}})
    return result
