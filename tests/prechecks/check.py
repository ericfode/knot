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
    ('c4-ignore-stale-hashes', 'checks.c4_receipt_integrity', 'stale_hashes', 'lambda ctx, changed: ([], 0)',
     'tests.test_c4.C4Tests.test_stale_hash_fires_and_fresh_hash_is_clean'),
    ('c5-ignore-judge-text', 'checks.c5_preflight_delta', 'identity', EMPTY1,
     'tests.test_c5.C5Tests.test_dropping_a_judge_sentence_is_major'),
    ('c6-ignore-retired-terms', 'checks.c6_claims_vs_facts', 'retired_terms', EMPTY1,
     'tests.test_c6.C6Tests.test_retired_terms'),
    ('c6-ignore-stale-counts', 'checks.c6_claims_vs_facts', 'stale_counts', 'lambda ctx, facts, receipts: []',
     'tests.test_c6.C6Tests.test_stale_count_after_the_receipt_moves'),
    ('packets-uncapped-evidence', 'packets.common', 'cap', 'lambda text, limit=12288: (text, "")',
     'tests.test_packets.PacketTests.test_cap_marker_text'),
    ('packets-no-passages', 'packets.builders', "BUILDERS['passages-agree']", 'lambda ctx: ([], [])',
     'tests.test_packets.PacketTests.test_p2_collects_every_passage_that_mentions_a_term'),
    ('packets-no-claims', 'packets.builders', "BUILDERS['claim-holds-against-evidence']", 'lambda ctx: ([], [])',
     'tests.test_packets.PacketTests.test_p1_type_a_selects_the_declaration_that_decides_the_claim'),
    ('c1-ignore-violations', 'checks.c1_probe_differential', 'violations', 'lambda text, verdicts, outcomes: {}',
     'tests.test_c1.RuleTests.test_d4_invalid_and_its_clean_control'),
    ('c1-ignore-reference-crashes', 'checks.c1_probe_differential', 'family_v', 'lambda ctx, result: None',
     'tests.test_c1.FamilyVTests.test_a_new_crash_of_the_reference_is_major_and_an_old_one_is_known'),
    ('c2-ignore-base-fixes', 'checks.c2_merge_forecast', 'base_fixes', NOOP2,
     'tests.test_c2.C2Tests.test_base_fix_missing'),
    ('c7-ignore-timeouts', 'checks.c7_gate_adequacy', 'unscaled_timeouts', EMPTY1,
     'tests.test_c7.C7Tests.test_unscaled_timeouts'),
    ('c7-ignore-limits', 'checks.c7_gate_adequacy', 'limits', EMPTY1,
     'tests.test_c7.C7Tests.test_limit_needs_controls_at_l_minus_one_l_and_l_plus_one'),
    ('c7-ignore-wiring', 'checks.c7_gate_adequacy', 'wiring', EMPTY1, 'tests.test_c7.C7Tests.test_gate_wiring'),
    ('c1-any-unsupported-is-fine', 'checks.c1_probe_differential', 'premature', 'lambda text, parse, p, documented: None',
     'tests.test_c1.RuleTests.test_premature_unsupported_is_the_recognized_token_being_the_rejected_token'),
    ('c1-every-prefix-is-premature', 'checks.c1_probe_differential', 'premature',
     "lambda text, parse, p, documented: {'seed_offset': 0, 'knot': p.line, 'at': 'a prefix'}",
     'tests.test_c1.RuleTests.test_a_valid_prefix_is_documented_policy_only_when_the_spec_lists_its_code'),
    ('c1-no-spec-table', 'checks.c1_probe_differential', 'prefix_codes', 'lambda tree: frozenset()',
     'tests.test_c1.EndToEndTests.test_a_recognized_prefix_that_the_spec_lists_is_policy_not_a_condition'),
    ('c3-forbid-new-gate-branches', 'checks.c3_frozen_and_owned', 'run_py_problems',
     "lambda base, head, added: ['counts() gained a statement other than a branch for a new gate']",
     'tests.test_c3.C3Tests.test_a_new_gates_counts_branch_is_the_registration_that_gates_md_asks_for'),
    ('c3-allow-any-counts-edit', 'checks.c3_frozen_and_owned', 'run_py_problems', 'lambda base, head, added: []',
     'tests.test_c3.C3Tests.test_editing_or_removing_an_existing_gates_count_branch_is_still_flagged'),
    ('c4-judge-baseline-sections', 'checks.c4_receipt_integrity', 'is_provenance', 'lambda pointer: False',
     'tests.test_c4.C4Tests.test_a_pre_implementation_freeze_section_is_history_not_staleness'),
    ('c5-measure-grouped-files-alone', 'checks.c5_preflight_delta', 'grouped_files', 'lambda ctx: set()',
     'tests.test_c5.C5Tests.test_a_file_that_a_group_lists_is_judged_by_its_group_not_alone'),
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
    # Documents are not inputs, except the calibration packets: the wiring test reads and asserts every one of them and a live
    # calibration sends them, so editing one must leave a stale input hash.
    inputs += sorted(p for p in (ROOT / 'tests/prechecks').rglob('*') if p.is_file() and p != RECEIPT and p != Path(__file__)
                     and '__pycache__' not in p.parts and 'receipts' not in p.parts
                     and (p.suffix != '.md' or ('perch-controls' in p.parts and p.name != 'README.md')))
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
        # The whole suite has just run: a test that is neither skipped nor failed passed unmutated, so no mutant re-runs it.
        skipped = {test.id() for test, _reason in result.skipped}
        passed = set(record['fixtures']) - skipped

        for name, module, function, replacement, test in MUTANTS:
            imported = __import__(module, fromlist=['*'])
            table = re.match(r"(\w+)\['([\w-]+)'\]$", function)                # a dispatch table entry, e.g. BUILDERS['name']
            require(hasattr(imported, table.group(1) if table else function), f'{name}: {module}.{function} is missing')
            require(test in passed, f'{name}: its pinning test must exist, pass unmutated and not be skipped: {test}')
            patch = (mock.patch.dict(getattr(imported, table.group(1)), {table.group(2): eval(replacement)}) if table
                     else mock.patch.object(imported, function, eval(replacement)))
            with patch:
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
