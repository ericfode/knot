"""Read the literal gate registry without importing or executing its module."""
import ast
import json
import sys


def registry(source):
    tree = ast.parse(source)
    if any(isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name)
           and n.target.id == 'GATES' for n in ast.walk(tree)):
        raise ValueError('Expected a complete literal GATES assignment')
    if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
           and isinstance(n.func.value, ast.Name) and n.func.value.id == 'GATES'
           for n in ast.walk(tree)):
        raise ValueError('Dynamic GATES operations are not supported')
    assignments = [n for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'GATES' for t in n.targets)]
    if len(assignments) != 1 or not isinstance(assignments[0].value, (ast.Tuple, ast.List)):
        raise ValueError('Expected one literal GATES sequence')
    result = []
    for entry in assignments[0].value.elts:
        if not (isinstance(entry, ast.Call) and isinstance(entry.func, ast.Name)
                and entry.func.id == 'Gate' and 2 <= len(entry.args) <= 4 and not entry.keywords):
            raise ValueError('Unrecognized Gate registration')
        name, argv, *_ = [ast.literal_eval(a) for a in entry.args]
        if not (isinstance(name, str) and isinstance(argv, (tuple, list))
                and argv and all(isinstance(a, str) for a in argv)):
            raise ValueError('Gate name and argv must be literals')
        result.append({'name': name, 'argv': list(argv)})
    if len({g['name'] for g in result}) != len(result):
        raise ValueError('Duplicate gate name')
    return result


if __name__ == '__main__':
    print(json.dumps(registry(sys.stdin.read())))
