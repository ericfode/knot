"""C7 gate-adequacy: can the increment's gate observe what it claims to observe?

Static rules read the manifest's declared limits and coverage cells and the gate scripts; the verifier-soundness
rules run adapters (scripts/prechecks/adequacy/<gate>.py) against a gate module in an export. A gate that cannot be
exercised reports `unavailable`, never a pass.

  R1 limit-unwitnessed    a declared limit lacks frozen controls at L-1, L and L+1 (or a required value list)
  R2 witness-missing      a declared coverage cell has no witness and is not allow-listed
  R3-R5 adequacy-adapters adapters: expectation-from-implementation, kill-credit, judge-accepts-forgery
  R6 unscaled-timeout     a fixed timeout in a changed gate script that ignores KNOT_GATE_TIMEOUT_SCALE
  R6 gate-headroom        a gate's wall time in the matching gate run is too close to the runner's timeout
  R7 gate-wiring          a new check script or gate row that the runner registry and its self-test do not know
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import re
from pathlib import Path

from lib import diffs, gaterun, globs
from lib import gates as gates_lib
from lib.model import CheckResult, Condition
from lib.runner import Check

ID = 'C7'
RULES = ('limit-unwitnessed', 'witness-missing', 'adequacy-adapters', 'unscaled-timeout', 'gate-wiring', 'gate-headroom')
GATE_SCRIPT = re.compile(r'^(?:tests|research)/.+/(?:check[^/]*\.py|host-check\.py|regen\.py)$|^vm/check[^/]*\.py$')
CHECK_SCRIPT = re.compile(r'^(?:tests|research)/[^/]+/check[^/]*\.py$|^vm/check-[^/]*\.py$')
TIMEOUT = re.compile(r'\btimeout\s*=\s*(\d+(?:\.\d+)?)\b(?!\s*[*/.\w])')
SECONDS = re.compile(r"\bSECONDS\s*(?:\[[^\]]+\]\s*)?=\s*(\d+)\b(?!\s*\*)")
ADEQUACY_DIR = Path(__file__).resolve().parent.parent / 'adequacy'


def _added(ctx, path: str) -> list[str]:
    patch = ctx.repo.patch(ctx.base.treeish, ctx.head.treeish, [path], unified=0)
    return [line for hunks in diffs.parse(patch).values() for h in hunks for line in h.added]


# ---- R1 ---------------------------------------------------------------------
def _boundary_values(ctx, files: list[str]) -> tuple[dict[str, set], str]:
    """{limit name: values} from machine-readable `boundary: {limit, value}` fields, plus the concatenated JSON text."""
    found: dict[str, set] = {}
    text = []
    for path in files:
        try:
            data = ctx.head.json(path)
        except ValueError:
            continue
        text.append(ctx.head.text(path) or '')
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                boundary = node.get('boundary')
                if isinstance(boundary, dict) and 'limit' in boundary and 'value' in boundary:
                    found.setdefault(str(boundary['limit']), set()).add(boundary['value'])
                stack += list(node.values())
            elif isinstance(node, list):
                stack += node
    return found, '\n'.join(text)


def limits(ctx) -> list[Condition]:
    found = []
    for limit in ctx.manifest.get('limits', []) or []:
        name = limit['name']
        required = list(limit.get('required') or [limit['value'] - 1, limit['value'], limit['value'] + 1])
        recorded, text = _boundary_values(ctx, limit.get('controls', []))
        seen = set(recorded.get(name, set()))
        heuristic = not seen
        if heuristic:                                   # no boundary fields for this limit: numeric literals in the controls count
            seen = {v for v in required if re.search(rf'(?<![\w.]){v}(?![\w.])', text)}
        for value in required:
            if value in seen:
                continue
            at_limit = 'value' in limit and value == limit['value']
            severity = 'minor' if heuristic or not (at_limit or 'required' in limit) else 'major'
            note = ' (heuristic: the controls carry no boundary fields)' if heuristic else ''
            found.append(Condition(ID, 'limit-unwitnessed', severity, {'limit': name, 'value': value},
                                   expected=f'frozen controls witness {name} at {required}',
                                   observed=f'no control at {value} for the limit {name}{note}',
                                   fix_hint='Add a frozen control carrying boundary: {limit, value}.'))
    return found


# ---- R2 ---------------------------------------------------------------------
def coverage(ctx) -> list[Condition]:
    found = []
    for item in ctx.manifest.get('coverage', []) or []:
        cells = list(item.get('cells') or [])
        if item.get('axes'):
            cells += ['/'.join(map(str, combo)) for combo in itertools.product(*item['axes'].values())]
        witnessed = set()
        for path in item.get('witnesses', []):
            for match in ctx.head.glob(path) if any(c in path for c in '*?[') else [path]:
                try:
                    data = ctx.head.json(match)
                except ValueError:
                    continue
                stack = [data]
                while stack:
                    node = stack.pop()
                    if isinstance(node, dict):
                        if isinstance(node.get('cell'), str):
                            witnessed.add(node['cell'])
                        if isinstance(node.get('cells'), list):
                            witnessed.update(c for c in node['cells'] if isinstance(c, str))
                        stack += list(node.values())
                    elif isinstance(node, list):
                        stack += node
        for cell in sorted(set(cells) - witnessed - set(item.get('allow') or [])):
            found.append(Condition(ID, 'witness-missing', 'major' if item.get('must') else 'minor',
                                   {'matrix': item['name'], 'cell': cell},
                                   actor='upstream' if item.get('upstream') else 'executor',
                                   expected=f"every cell of {item['name']} has a golden or control witness, or an allow-list reason",
                                   observed=f'{item["name"]}: no witness for {cell}',
                                   fix_hint='Freeze a witness, or list the cell as unreachable with its reason.'))
    return found


# ---- R6, R7 -------------------------------------------------------------------------
def unscaled_timeouts(ctx) -> list[Condition]:
    found = []
    for change in ctx.changes():
        if change.status not in 'AMR' or not GATE_SCRIPT.match(change.path):
            continue
        for line in _added(ctx, change.path):
            code = line.split('#', 1)[0]
            match = TIMEOUT.search(code) or SECONDS.search(code)
            if match and 'SCALE' not in code.upper():
                found.append(Condition(ID, 'unscaled-timeout', 'minor',
                                       {'path': change.path, 'text': re.sub(r'\s+', ' ', line.strip())[:60]},
                                       expected='a gate hang guard scales with KNOT_GATE_TIMEOUT_SCALE (the runner sets it to 4 under load)',
                                       observed=f'{change.path}: fixed timeout {match.group(0)!r} ignores the scale',
                                       fix_hint='Multiply it by the scale, as tests/compiler-recursion/check.py does.'))
    return found


def wiring(ctx) -> list[Condition]:
    found = []
    head_rows = gates_lib.parse_gates(ctx.head.text(gates_lib.RUN_PY))
    base_names = {g.name for g in gates_lib.parse_gates(ctx.base.text(gates_lib.RUN_PY))}
    required = gates_lib.required_names(ctx.head.text(gates_lib.TEST_RUNNER))
    argv_paths = {a for g in head_rows for a in g.argv}
    for path in ctx.added_paths():
        if CHECK_SCRIPT.match(path) and path not in argv_paths and ctx.head.has(gates_lib.RUN_PY):
            found.append(Condition(ID, 'gate-wiring', 'minor', {'path': path, 'kind': 'unregistered-script'},
                                   expected='a new check script is registered as a Gate row in scripts/gates/run.py',
                                   observed=f'{path} is not the program of any Gate row',
                                   fix_hint='Append the Gate row and its required name (the coordinator merges the shared files).'))
    if ctx.head.has(gates_lib.TEST_RUNNER):
        for gate in head_rows:
            if gate.name not in base_names and gate.name not in required:
                found.append(Condition(ID, 'gate-wiring', 'minor', {'gate': gate.name, 'kind': 'required-name'},
                                       expected="a new gate's name is in test_runner.py's required set",
                                       observed=f'gate {gate.name} is registered but not required by the runner self-test'))
    return found


def headroom(ctx, result: CheckResult) -> list[Condition]:
    summary, path, reason = gaterun.find(ctx)
    if summary is None:
        result.rules_unavailable['gate-headroom'] = reason
        return []
    result.rules_run.append('gate-headroom')
    limit = float(summary.get('run', {}).get('timeout_seconds') or 900)
    found = []
    for gate in summary.get('run', {}).get('gates', []):
        seconds = gate.get('seconds') or 0
        if seconds > 0.5 * limit:
            found.append(Condition(ID, 'gate-headroom', 'major' if seconds > 0.8 * limit else 'minor', {'gate': gate.get('name')},
                                   actor='coordinator', value={'seconds': round(seconds), 'timeout': limit},
                                   expected='a gate finishes well inside the runner timeout (under 50%)',
                                   observed=f"gate {gate.get('name')} took {seconds:.0f}s of {limit:.0f}s in the matching run"))
    return found


# ---- R3-R5: adapters ------------------------------------------------------------------
def adapters(ctx, result: CheckResult) -> list[Condition]:
    """Run every adapter whose gate this branch touched. An adapter is a module exposing `GATE`, `touched(paths)` and
    `probe(export, ctx) -> list[Condition]`; a missing gate module or function reports unavailable."""
    found = []
    changed = ctx.changed_paths() + ctx.deleted_paths()
    for path in sorted(ADEQUACY_DIR.glob('*.py')) if ADEQUACY_DIR.is_dir() else []:
        if path.name.startswith('_'):
            continue
        spec = importlib.util.spec_from_file_location(f'_adequacy_{path.stem}', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not module.touched(changed):
            continue
        export = ctx.export(ctx.head)
        try:
            produced = module.probe(export, ctx)
        except Exception as error:                      # noqa: BLE001 - an adapter that cannot run is unavailable, not a pass
            result.rules_unavailable[f'adequacy:{module.GATE}'] = f'{type(error).__name__}: {str(error)[:120]}'
            continue
        found += produced
        result.rules_run.append(f'adequacy:{module.GATE}')
    return found


def run(ctx) -> CheckResult:
    result = CheckResult()
    if ctx.base is None:
        return CheckResult(outcome='not-applicable', reason='no base to compare against')
    # R1 and R2 compare a declaration with the tree: with no declaration there is nothing to compare, which is a rule that
    # could not run (unavailable), not a rule that ran and found nothing.
    for name, key, fn in (('limit-unwitnessed', 'limits', limits), ('witness-missing', 'coverage', coverage)):
        if ctx.manifest.get(key):
            result.conditions += fn(ctx)
            result.rules_run.append(name)
        else:
            result.rules_unavailable[name] = f'the manifest declares no {key}: there is nothing to compare'
    if not ctx.identity:
        result.conditions += unscaled_timeouts(ctx)
        result.conditions += wiring(ctx)
        result.rules_run += ['unscaled-timeout', 'gate-wiring']
        result.conditions += adapters(ctx, result)
        if not any(p.name[0] != '_' for p in (ADEQUACY_DIR.glob('*.py') if ADEQUACY_DIR.is_dir() else [])):
            result.rules_unavailable['adequacy-adapters'] = ('no adapter ships in this build: R3-R5 (expectation-from-implementation, '
                                                             'kill-credit, judge-accepts-forgery) need one per gate')
        elif any(rule.startswith('adequacy:') for rule in result.rules_run):
            result.rules_run.append('adequacy-adapters')
        elif any(rule.startswith('adequacy:') for rule in result.rules_unavailable):
            result.rules_unavailable['adequacy-adapters'] = 'an adapter could not run (see the adequacy:<gate> entries)'
        else:
            result.na('adequacy-adapters', "no shipped adapter's gate was touched by this diff")
    else:
        result.na(('unscaled-timeout', 'gate-wiring', 'adequacy-adapters'), 'identity: nothing changed since base')
    result.conditions += headroom(ctx, result)
    return result


CHECK = Check(ID, 'gate-adequacy', "the gate's claims against its witnesses and verdict function", run, budget=20, rules=RULES)
