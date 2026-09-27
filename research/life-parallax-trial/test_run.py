#!/usr/bin/env python3
"""Offline controller checks: no authors, candidates, or provider dispatch."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("parallax_run", HERE / "run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def report():
    policy = runner.read(runner.POLICY)
    declaration = {"id": "D001", "name": "test-only-inventory"}
    family = []
    for i, dimension in enumerate(policy["family_dimensions"]):
        count = len(dimension["levels"])
        family.append({"dimension": dimension["id"], "target": policy["family_targets"][i], "required": True,
                       "request_id": "family", "requested_model": runner.JUDGE, "resolved_model": runner.JUDGE,
                       "probabilities": {str(k): 1 if k == count - 1 else 0 for k in range(count)},
                       "target_probability": 1, "status": "meets_target"})
    support = [{"declaration": declaration, "dimension": "supports_main_idea", "target": policy["support_target"],
                "required": True, "request_id": "support", "requested_model": runner.JUDGE, "resolved_model": runner.JUDGE,
                "probabilities": {str(k): 1 if k == 4 else 0 for k in range(5)},
                "target_probability": 1, "status": "meets_target"}]
    return {"schema": "life-helper-report-v1", "live": True, "requested_model": runner.JUDGE,
            "policy": {"sha256": runner.POLICY_SHA}, "status": "complete", "failure": None,
            "transport": {"peak_in_flight": 2}, "requests": [
                {"id": k, "status": "complete", "source_sha256": "abc", "receipt": {"resolved_model": runner.JUDGE}}
                for k in ("family", "support")],
            "entries": [{"status": "pass", "source_sha256": "abc", "actual_source_sha256": "abc",
                "declarations": [declaration], "family_assessments": family, "support_assessments": support,
                "deterministic_passed": True, "semantic_clean": True, "family_passed": True,
                "support_passed": True, "full_pass": True,
                "coverage": {"expected_family_assessments": 5, "expected_support_assessments": 1,
                    "completed_assessments": 6, "required_assessments": 6, "complete": True,
                    "full_source": True, "truncated": False}}]}


class Offline(unittest.TestCase):
    def test_packet_exact_first_bytes_and_only_permitted_parts(self):
        data, manifest = runner.packet()
        self.assertEqual(data[:3912], (HERE / "inputs/parallax.decoded.txt").read_bytes())
        self.assertEqual(len(manifest["parts"]), 6)
        for item in manifest["parts"]:
            raw = data[item["start_byte"]:item["start_byte"] + item["bytes"]]
            self.assertEqual(runner.digest(raw), item["sha256"])
        runner.transport._check_schema(runner.read(HERE / "schema.json"))

    def test_complete_conjunction(self):
        self.assertTrue(runner.audit_style(report(), "abc", True, True)["full_pass"])

    def test_one_helper_cannot_hide_in_family_pass(self):
        value = report()
        entry = value["entries"][0]
        a = entry["support_assessments"][0]
        a.update(probabilities={"0": 0, "1": 0, "2": 1, "3": 0, "4": 0}, target_probability=0, status="below_target")
        entry.update(support_passed=False, full_pass=False)
        self.assertFalse(runner.audit_style(value, "abc", True, True)["full_pass"])

    def test_galaxy_five_remains_required(self):
        value = report()
        entry = value["entries"][0]
        a = entry["family_assessments"][0]
        a.update(probabilities={"0": 0, "1": 0, "2": 0, "3": 0, "4": 1, "5": 0}, target_probability=0, status="below_target")
        entry.update(family_passed=False, full_pass=False)
        self.assertFalse(runner.audit_style(value, "abc", True, True)["full_pass"])

    def test_semantic_attention_not_accepted(self):
        value = report()
        value["entries"][0].update(semantic_clean=False, full_pass=False)
        self.assertFalse(runner.audit_style(value, "abc", True, False)["full_pass"])

    def test_missing_coverage_source_model_or_bad_mass_blocks(self):
        cases = []
        value = report(); value["entries"][0]["support_assessments"] = []; cases.append(value)
        value = report(); value["entries"][0]["coverage"]["truncated"] = True; cases.append(value)
        value = report(); value["requested_model"] = "jev-latest"; cases.append(value)
        value = report(); value["entries"][0]["actual_source_sha256"] = "wrong"; cases.append(value)
        value = report(); value["entries"][0]["family_assessments"][0]["target_probability"] = .8; cases.append(value)
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(runner.gate.GateError):
                    runner.audit_style(value, "abc", True, True)

    def test_provider_error_stops_as_provider_failure(self):
        value = report(); value.update(status="incomplete", failure="provider_http_error")
        with self.assertRaises(runner.gate.GateError) as caught:
            runner.audit_style(value, "abc", True, True)
        self.assertEqual(caught.exception.status, "provider_failure")

    def test_partial_run_blocks_replay(self):
        with tempfile.TemporaryDirectory(dir=HERE, prefix=".offline-") as directory:
            with patch.object(runner, "TRIAL", Path(directory)):
                with self.assertRaises(runner.gate.GateError):
                    runner.replay()

    def test_explicit_live_required_before_lock_or_dispatch(self):
        with patch.object(runner, "check", side_effect=AssertionError("must not run")):
            with self.assertRaises(runner.gate.GateError):
                runner.run(False)

    def test_no_oracle_answers_in_behavior_feedback(self):
        self.assertEqual(runner.body_feedback({"passed": False, "status": "deterministic_failure", "counts": {},
            "actual": [1], "expected": [0], "error": "secret fixture"}),
            {"passed": False, "status": "deterministic_failure", "counts": {}})


if __name__ == "__main__":
    unittest.main(verbosity=2)
