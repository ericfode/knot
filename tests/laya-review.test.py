"""Offline checks against the actual pinned Laya tokenizer and input encoder."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("laya_review", ROOT / "scripts/laya-review.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class InputIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from transformers import AutoTokenizer
        cls.tok = AutoTokenizer.from_pretrained(review.SNAPSHOT / "tokenizer", local_files_only=True)
        cls.short = {"yes": {"type": "noul", "instructions": "Is this a refund request?"}}

    def test_short_request_matches_native_defaults(self):
        audit = review.audit_request(self.tok, "Please refund my payment.", self.short, 512)
        self.assertTrue(audit["complete"])
        self.assertTrue(audit["questions"]["yes"]["default_encoding_complete"])

    def test_long_instruction_is_preserved_with_larger_head(self):
        questions = {"long": {"type": "noul", "instructions": "Verify every constraint. " * 90}}
        audit = review.audit_request(self.tok, "source", questions, 2048)
        self.assertTrue(audit["complete"])
        self.assertFalse(audit["questions"]["long"]["default_encoding_complete"])

    def test_option_cap_is_not_hidden_by_larger_context(self):
        questions = {"style": {"type": "score", "instructions": "Rate this.",
                              "criteria": ["weak", "criterion " * 65]}}
        audit = review.audit_request(self.tok, "source", questions, 8192)
        self.assertFalse(audit["complete"])
        self.assertIn("48-token", audit["reasons"][0])

    def test_state_clipping_rejected_for_objects_and_conversations(self):
        for state in [{"source": "word " * 600}, ["word " * 600, "newest message"]]:
            self.assertFalse(review.audit_request(self.tok, state, self.short, 512)["complete"])

    def test_special_token_rewriting_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "mask token"):
            review.audit_request(self.tok, "source " + self.tok.mask_token, self.short, 512)

    def test_empty_questions_cannot_look_like_coverage(self):
        with self.assertRaisesRegex(ValueError, "1..16"):
            review.audit_request(self.tok, "source", {}, 512)

    def test_actual_semantic_controls_fit_without_state_truncation(self):
        requests = json.loads((ROOT / "docs/laya-trial/requests.json").read_text())
        for request in requests[:12]:
            audit = review.audit_request(self.tok, request["state"], request["questions"], 512)
            self.assertTrue(audit["complete"], request["id"])
            if request["phase"] == "native-narrow":
                self.assertTrue(all(q["default_encoding_complete"] for q in audit["questions"].values()))

    def test_unchanged_style_rubric_is_explicitly_unsupported(self):
        request = json.loads((ROOT / "docs/laya-trial/requests.json").read_text())[-1]
        audit = review.audit_request(self.tok, request["state"], request["questions"], 8192)
        self.assertFalse(audit["complete"])
        self.assertEqual(len(audit["reasons"]), 1)
        self.assertTrue(audit["reasons"][0].startswith("highly_memetic:"))


if __name__ == "__main__":
    unittest.main()
