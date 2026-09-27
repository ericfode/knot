"""Frozen input and rejection checks against the real pinned Julia tokenizer."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("julia_review", ROOT / "scripts/julia-review.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class InputIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from julia_mlx.tokenizer import JuliaTokenizer
        cls.tok = JuliaTokenizer(review.SNAPSHOT / "tokenizer", cache_size=0)
        cls.requests = json.loads((ROOT / "docs/laya-trial/requests.json").read_text())

    def test_all_semantic_and_sanity_inputs_fit_whole(self):
        for request in self.requests[:-1]:
            audit = review.audit_request(self.tok, request["state"], request["questions"])
            self.assertTrue(audit["complete"], request["id"])
            self.assertTrue(all(q["full_sequence_tokens"] <= 1024 for q in audit["questions"].values()))

    def test_boolean_descriptions_are_preserved_in_false_true_order(self):
        questions = {"check": {"type": "noul", "instructions": "Which condition holds?",
                              "criteria": {"true": "constraint holds", "false": "constraint fails"}}}
        rows = review.native_rows("source", questions)
        self.assertEqual(rows[0]["options"], ["constraint fails", "constraint holds"])

    def test_style_is_rejected_without_shortening_any_description(self):
        request = self.requests[-1]
        before = copy.deepcopy(request)
        audit = review.audit_request(self.tok, request["state"], request["questions"])
        self.assertFalse(audit["complete"])
        self.assertEqual(audit["reasons"], ["highly_memetic: option exceeds 48-token model contract"])
        self.assertEqual(request, before)

    def test_oversized_state_is_rejected(self):
        request = self.requests[0]
        audit = review.audit_request(self.tok, "word " * 3000, request["questions"])
        self.assertFalse(audit["complete"])
        self.assertIn("state exceeds", audit["reasons"][0])

    def test_instruction_overflow_is_rejected(self):
        questions = {"check": {"type": "noul", "instructions": "word " * 600}}
        audit = review.audit_request(self.tok, "source", questions)
        self.assertFalse(audit["complete"])
        self.assertIn("lossless head budget", audit["reasons"][0])

    def test_reserved_marker_rewriting_is_rejected(self):
        request = self.requests[0]
        audit = review.audit_request(self.tok, "source " + self.tok.mask_token, request["questions"])
        self.assertFalse(audit["complete"])
        self.assertIn("reserved model marker", audit["reasons"][0])

    def test_empty_questions_cannot_look_like_coverage(self):
        with self.assertRaisesRegex(ValueError, "1..16"):
            review.native_rows("source", {})


if __name__ == "__main__":
    unittest.main()
