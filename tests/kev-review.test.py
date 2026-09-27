"""Offline input-integrity checks with Kev's pinned tokenizer and native encoder."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("kev_review", ROOT / "scripts/kev-review.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
os.environ.update(HF_HOME=str(review.CACHE), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")


class InputIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from kev.model import load_tokenizer
        cls.tok = load_tokenizer(review.PIN["base"], revision=review.PIN["base_revision"])
        cls.requests = json.loads((ROOT / "docs/laya-trial/requests.json").read_text())

    def test_every_frozen_request_contains_every_rendered_token(self):
        from kev.model import SPECIAL
        marker = [self.tok.convert_tokens_to_ids(x) for x in SPECIAL]
        tokens = lambda text: self.tok(text, add_special_tokens=False).input_ids
        for request in self.requests:
            record, meta, enc, audit = review.prepare_request(self.tok, request)
            # Independent uncut construction, including each entire option description.
            expected = [marker[0]] + tokens(record["state"])
            for question in record["questions"]:
                expected += [marker[1]] + tokens(question["instr"])
                for option in question["options"]:
                    expected += [marker[2]] + tokens(option) + [marker[3]]
                expected += [marker[4]]
            self.assertEqual(enc["ids"], expected, request["id"])
            self.assertFalse(audit["state_truncated"])
            self.assertEqual(len(meta), len(request["questions"]))

    def test_labels_and_paths_cannot_change_the_inference(self):
        request = copy.deepcopy(self.requests[4])
        before = review.prepare_request(self.tok, request)
        request.update(id="different", target="broken/expected-failure.bend", expected_performance=False)
        self.assertEqual(review.prepare_request(self.tok, request), before)

    def test_full_style_descriptions_reach_the_pointer_options(self):
        request = self.requests[-1]
        record, meta, enc, _ = review.prepare_request(self.tok, request)
        for question, native, mapping, indices in zip(request["questions"].values(), record["questions"], meta, enc["opt_idx"]):
            self.assertEqual(native["options"], question["criteria"])
            self.assertEqual(list(mapping["legend"].values()), question["criteria"])
            self.assertEqual(len(indices), len(question["criteria"]))

    def test_long_options_are_accepted_whole(self):
        request = {"state": "source", "questions": {"style": {"type": "score",
                   "instructions": "Rate this.", "criteria": ["weak", "criterion " * 65]}}}
        record, _, enc, _ = review.prepare_request(self.tok, request)
        self.assertEqual(record["questions"][0]["options"][1], "criterion " * 65)
        self.assertGreater(enc["opt_idx"][0][1] - enc["opt_idx"][0][0], 65)

    def test_oversized_state_is_rejected(self):
        from kev.model import ContextOverflow
        request = copy.deepcopy(self.requests[12])
        request["state"] = "word " * 2100
        with self.assertRaisesRegex(ContextOverflow, "state exceeds"):
            review.prepare_request(self.tok, request)

    def test_oversized_branch_is_rejected(self):
        from kev.model import ContextOverflow
        request = {"state": "source", "questions": {"too_long": {
            "type": "noul", "instructions": "word " * 4200}}}
        with self.assertRaisesRegex(ContextOverflow, "branch too long"):
            review.prepare_request(self.tok, request)

    def test_empty_questions_cannot_look_like_coverage(self):
        with self.assertRaises(ValueError):
            review.prepare_request(self.tok, {"state": "source", "questions": {}})


if __name__ == "__main__":
    unittest.main()
