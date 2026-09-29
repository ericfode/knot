"""Measured facts about a tree: what the prose, reports and commit messages are checked against."""
from __future__ import annotations

import json
import re

from . import gates as gates_lib
from . import receipts as R

GENERIC_KEYS = ('fixtures', 'mutants', 'controls', 'budgets', 'boundaries', 'bounds', 'host_boundaries', 'rejects',
                'observations', 'goldens', 'invocations', 'cases')
LAW = re.compile(r'(?m)^law\s+(\w+)\s*:\s*\n((?:[ \t]+for [^\n]*\n)*)')
FILLED = re.compile(r'(?m)^def\s+L\.(\w+)\s*\(')


def gate_receipts(tree) -> dict[str, dict]:
    """{gate name: {'path': first JSON output, 'lists': {key: length}, 'raw_types': {key: type name}}}"""
    rows = gates_lib.parse_gates(tree.text(gates_lib.RUN_PY))
    result = {}
    for gate in rows:
        info = {'path': None, 'lists': {}, 'raw_types': {}, 'outputs': list(gate.outputs)}
        for output in gate.outputs:
            if not output.endswith('.json') or '*' in output:
                continue
            try:
                value = tree.json(output)
            except ValueError:
                value = None
            if isinstance(value, dict):
                info['path'] = output
                for key in GENERIC_KEYS:
                    if key in value:
                        info['raw_types'][key] = type(value[key]).__name__
                        if isinstance(value[key], list):
                            info['lists'][key] = len(value[key])
                if isinstance(value.get('counts'), dict):
                    info['counts'] = value['counts']
                break
        result[gate.name] = info
    return result


def law_counts(tree) -> dict[str, dict]:
    """Per `*LAWS.bend`: laws, ground laws (no `for` binder), and filled `def L.<name>` in the sibling PROOF file."""
    result = {}
    for path in tree.files():
        if not path.endswith('LAWS.bend'):
            continue
        text = tree.text(path) or ''
        laws = LAW.findall(text)
        ground = [name for name, binders in laws if not binders.strip()]
        proof = path[:-len('LAWS.bend')] + 'PROOF.bend'
        filled = len(FILLED.findall(tree.text(proof) or '')) if tree.has(proof) else None
        result[path] = {'laws': len(laws), 'ground': sorted(ground), 'filled': filled}
    return result


def census_counts(tree) -> dict:
    try:
        data = tree.json('docs/compiler-campaign/inventory/accepted.json')
    except ValueError:
        data = None
    if not isinstance(data, dict):
        return {}
    compiler = data.get('compiler') or {}
    return {k: compiler[k] for k in ('files', 'declarations', 'classes') if k in compiler}


def collect(tree) -> dict:
    rows = gates_lib.parse_gates(tree.text(gates_lib.RUN_PY))
    receipts = gate_receipts(tree)
    laws = law_counts(tree)
    return {
        'gates': [g.name for g in rows],
        'gate_count': len(rows),
        'required_names': sorted(gates_lib.required_names(tree.text(gates_lib.TEST_RUNNER))),
        'receipts': {name: {'path': i['path'], 'lists': i['lists']} for name, i in receipts.items() if i['path']},
        'laws': {path: {k: v for k, v in info.items() if k != 'ground'} | {'ground': len(info['ground'])}
                 for path, info in laws.items()},
        'census': census_counts(tree),
    }
