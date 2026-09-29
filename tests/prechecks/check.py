#!/usr/bin/env python3
"""Offline verification of the prechecks suite: no provider, no network, no credentials.

It runs (1) every unit test of scripts/prechecks/tests, each rule against a synthetic clean and a synthetic broken
repository; (2) a fixed set of semantic mutants of the checks, each of which must be killed by the unit test that
pins its rule (a mutant that survives means the rule is vacuous); and (3) the Perch rule wiring test with a stubbed
provider, which proves selection and plumbing and is never calibration. It writes only its own receipt.
"""
from __future__ import annotations

import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RECEIPT = HERE / 'receipts/prechecks.json'
PACKAGE = ROOT / 'scripts/prechecks'
TIMEOUT_SCALE = float(os.environ.get('KNOT_GATE_TIMEOUT_SCALE', '1'))  # harness hang guard only; gates set it under load

# (name, module, function, replacement, the unit test that must fail without the function)
NOOP2 = 'lambda ctx, result: None'
EMPTY1 = 'lambda ctx: []'
MUTANTS = [
    ('c2-ignore-main-conflicts', 'checks.c2_merge_forecast', 'conflicts_rules', NOOP2,
     'tests.test_c2.C2Tests.test_conflict_outside_the_registry_is_major'),
    ('c2-ignore-upstream-controls', 'checks.c2_merge_forecast', 'upstream_contracts', NOOP2,
     'tests.test_c2.C2Tests.test_unconsumed_upstream_control'),
    ('c2-ignore-decision-drift', 'checks.c2_merge_forecast', 'decision_drift', NOOP2,
     'tests.test_c2.C2Tests.test_decision_drift_in_the_branch_spec'),
    ('c3-ignore-frozen-paths', 'checks.c3_frozen_and_owned', 'frozen_edits', EMPTY1,
     'tests.test_c3.C3Tests.test_frozen_edits'),
    ('c3-ignore-weakened-assertions', 'checks.c3_frozen_and_owned', 'assertion_weakening', EMPTY1,
     'tests.test_c3.C3Tests.test_removed_assertion'),
    ('c3-ignore-frozen-rows', 'checks.c3_frozen_and_owned', 'frozen_rows', EMPTY1,
     'tests.test_c3.C3Tests.test_frozen_rows'),
    ('c3-ignore-history', 'checks.c3_frozen_and_owned', 'history', EMPTY1,
     'tests.test_c3.C3Tests.test_history_lints'),
    ('c4-ignore-host-paths', 'checks.c4_receipt_integrity', 'host_paths', 'lambda ctx, changed: []',
     'tests.test_c4.C4Tests.test_host_path_in_new_receipt'),
    ('c4-ignore-stale-hashes', 'checks.c4_receipt_integrity', 'stale_hashes', 'lambda ctx, changed: []',
     'tests.test_c4.C4Tests.test_stale_hash_fires_and_fresh_hash_is_clean'),
    ('c5-ignore-judge-text', 'checks.c5_preflight_delta', 'identity', EMPTY1,
     'tests.test_c5.C5Tests.test_dropping_a_judge_sentence_is_major'),
    ('c6-ignore-retired-terms', 'checks.c6_claims_vs_facts', 'retired_terms', EMPTY1,
     'tests.test_c6.C6Tests.test_retired_terms'),
    ('c6-ignore-stale-counts', 'checks.c6_claims_vs_facts', 'stale_counts', 'lambda ctx, facts, receipts: []',
     'tests.test_c6.C6Tests.test_stale_count_after_the_receipt_moves'),
    ('packets-uncapped-evidence', 'packets.common', 'cap', 'lambda text, limit=12288: (text, "")',
     'tests.test_packets.PacketTests.test_cap_marker_text'),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def run_suite(suite) -> unittest.TestResult:
    return unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)


def names(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from names(item)
        else:
            yield item.id()


def main():
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
              'scope': 'Offline verification of the pre-review checks and their Perch rule wiring; no provider requests',
              'fixtures': [], 'mutants': []}
    sys.path.insert(0, str(PACKAGE))
    sys.dont_write_bytecode = True
    inputs = sorted(p for p in PACKAGE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py', '.ts', '.json'))
    inputs += sorted(p for p in (ROOT / 'tests/prechecks').rglob('*') if p.is_file() and p != RECEIPT and p != Path(__file__)
                     and '__pycache__' not in p.parts and 'receipts' not in p.parts)
    inputs += [ROOT / '.perch/rules/prechecks.yaml', ROOT / 'scripts/check-prechecks-rule-wiring.mjs',
               ROOT / 'scripts/prechecks-perch-run.mjs', Path(__file__)]
    record['inputs'] = {str(p.relative_to(ROOT)): digest(p) for p in inputs}
    try:
        loader = unittest.TestLoader()
        suite = loader.discover(str(PACKAGE / 'tests'), pattern='test_*.py', top_level_dir=str(PACKAGE))
        record['fixtures'] = sorted(names(suite))
        result = run_suite(suite)
        require(result.wasSuccessful(), '\n'.join(text for _test, text in result.failures + result.errors)[:4000])
        require(result.testsRun == len(record['fixtures']), 'every discovered test ran')

        for name, module, function, replacement, test in MUTANTS:
            imported = __import__(module, fromlist=['*'])
            require(hasattr(imported, function), f'{name}: {module}.{function} is missing')
            control = run_suite(loader.loadTestsFromName(test))
            require(control.wasSuccessful() and control.testsRun == 1, f'{name}: its pinning test must pass unmutated: {test}')
            with mock.patch.object(imported, function, eval(replacement)):
                mutated = run_suite(loader.loadTestsFromName(test))
            require(not mutated.wasSuccessful(), f'Surviving semantic mutant: {name} ({test} still passes)')
            record['mutants'].append({'name': name, 'target': f'{module}.{function}', 'killed_by': test,
                                      'outcome': 'semantic-kill'})

        wired = subprocess.run(['node', 'scripts/check-prechecks-rule-wiring.mjs'], cwd=ROOT, text=True, capture_output=True,
                               timeout=120 * TIMEOUT_SCALE)
        require(wired.returncode == 0 and re.search(r'^PASS: seven advisory prechecks rules;', wired.stdout, re.M), wired.stdout + wired.stderr)
        cases = json.loads((HERE / 'perch-controls/cases.json').read_text())
        record['perch'] = {'rules': 7, 'controls': len(cases['cases']), 'gaps': len(cases['gaps']),
                           'wiring': wired.stdout.strip().splitlines()[0]}
        record['status'] = 'passed'
        print(f"PASS: {len(record['fixtures'])} unit tests over synthetic clean and broken repositories; "
              f"{len(record['mutants'])} semantic mutants killed; Perch wiring for 7 advisory rules and "
              f"{len(cases['cases'])} calibration packets (stub provider, not calibration).")
    except Exception as error:
        record.update(status='failed', failure=str(error)[:4000])
        raise
    finally:
        RECEIPT.write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
