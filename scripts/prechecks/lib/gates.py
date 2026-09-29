"""Static facts about the gate runner, read by AST from any tree (never by importing the tree's code)."""
from __future__ import annotations

import ast
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path

RUN_PY = 'scripts/gates/run.py'
TEST_RUNNER = 'scripts/gates/test_runner.py'
HERE_GATES = Path(__file__).resolve().parents[2] / 'gates'


@dataclass
class GateRow:
    name: str
    argv: tuple = ()
    outputs: tuple = ()
    needs: tuple = ()
    line: int = 0


def _literal(node, default=()):
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return default


def parse_gates(source: str | None) -> list[GateRow]:
    """Every `Gate(...)` call in the module-level `GATES` tuple of `scripts/gates/run.py`."""
    if not source:
        return []
    try:
        module = ast.parse(source)
    except SyntaxError:
        return []
    rows = []
    for node in ast.walk(module):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'GATES' for t in node.targets):
            container = node.value
            for item in getattr(container, 'elts', []):
                if isinstance(item, ast.Call) and getattr(item.func, 'id', None) == 'Gate' and item.args:
                    name = _literal(item.args[0], None)
                    if not isinstance(name, str):
                        continue
                    argv = tuple(_literal(item.args[1])) if len(item.args) > 1 else ()
                    outputs = tuple(_literal(item.args[2])) if len(item.args) > 2 else ()
                    needs = tuple(_literal(item.args[3])) if len(item.args) > 3 else ()
                    for kw in item.keywords:
                        if kw.arg == 'needs':
                            needs = tuple(_literal(kw.value))
                        elif kw.arg == 'outputs':
                            outputs = tuple(_literal(kw.value))
                        elif kw.arg == 'argv':
                            argv = tuple(_literal(kw.value))
                    rows.append(GateRow(name, argv, outputs, needs, item.lineno))
    return rows


def required_names(source: str | None) -> set[str]:
    """Names in the runner self-test's `assertLessEqual({...}, set(names))` required set."""
    if not source:
        return set()
    try:
        module = ast.parse(source)
    except SyntaxError:
        return set()
    for node in ast.walk(module):
        if isinstance(node, ast.Call) and getattr(node.func, 'attr', '') == 'assertLessEqual' and node.args:
            first = node.args[0]
            if isinstance(first, ast.Set):
                return {e.value for e in first.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)}
    return set()


def load_module(name: str):
    """Import `scripts/gates/<name>.py` from the tool's own checkout (normalize and run have no side effects)."""
    path = HERE_GATES / f'{name}.py'
    if not path.is_file():
        return None
    inserted = str(HERE_GATES) not in sys.path
    if inserted:
        sys.path.insert(0, str(HERE_GATES))
    try:
        spec = importlib.util.spec_from_file_location(f'_prechecks_gates_{name}', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if inserted:
            sys.path.remove(str(HERE_GATES))
