"""Input integrity and option mapping tests; no model weights are loaded."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("local_review", ROOT / "scripts/local-model-review.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")


class MappingIntegrity(unittest.TestCase):
    def test_noul_polarity_and_descriptions_survive_schema_conversion(self):
        questions = {"q": {"type": "noul", "instructions": "Assess.",
                            "criteria": {"true": "positive meaning", "false": "negative meaning"}}}
        schema = review.nimble_schema(questions)["q"]
        self.assertEqual(schema["choices"], [False, True])
        self.assertEqual(schema["choice_descriptions"], questions["q"]["criteria"])
        self.assertEqual(review.summarize(questions["q"], {"false": .8, "true": .2})["noul"], .2)

    def test_style_criteria_are_complete_ordered_options(self):
        request = json.loads((ROOT / "docs/laya-trial/requests.json").read_text())[-1]
        schema = review.nimble_schema(request["questions"])
        for key, q in request["questions"].items():
            self.assertEqual(list(schema[key]["choice_descriptions"].values()), q["criteria"])
            self.assertEqual(schema[key]["choices"], [str(i) for i in range(len(q["criteria"]))])

    def test_malformed_or_missing_probability_mass_is_rejected(self):
        q = {"type": "score", "criteria": ["bad", "good"]}
        for probabilities in ({"0": 1}, {"0": .1, "1": .1}, {"0": float("nan"), "1": 1}):
            with self.assertRaises(ValueError):
                review.summarize(q, probabilities)

    def test_empty_questions_and_token_overflow_are_rejected(self):
        with self.assertRaises(ValueError):
            review.nimble_schema({})
        with self.assertRaises(ValueError):
            review.bounded_audit([[1] * (review.MAX_TOKENS + 1)])


@unittest.skipUnless(os.environ.get("MODEL_REVIEW_MODEL"), "Select a downloaded runtime for native encoding checks")
class NativeIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.name = os.environ["MODEL_REVIEW_MODEL"]
        directory = ROOT / ".local" / cls.name
        source = directory / "repo"
        sys.path.insert(0, str(source / "eikos" if cls.name == "eikos" else source / "src" if cls.name == "autojev" else source))
        cls.engine = {"eikos": review.Eikos, "nimble": review.Nimble, "autojev": review.AutoJev}[cls.name](
            directory / ("adapter" if cls.name == "nimble" else "model"), False)
        cls.requests = json.loads((ROOT / "docs/laya-trial/requests.json").read_text())

    def test_all_fifteen_requests_have_complete_native_encodings(self):
        for row in self.requests:
            _, audit = self.engine.prepare(row["state"], row["questions"])
            self.assertTrue(audit["complete"], row["id"])
            self.assertEqual(len(audit["full_tokens"]), len(row["questions"]))

    def test_native_templates_contain_the_original_state_and_every_description(self):
        # Observe the native renderer before tokenization, including the real
        # tokenizer's full encoding checks performed by engine.prepare.
        if self.name == "autojev":
            target = self.engine.model.processor
        else:
            target = self.engine.model.tok if self.name == "eikos" else self.engine.model.tokenizer
        original, messages = target.apply_chat_template, []
        def capture(conversation, *args, **kwargs):
            messages.append(conversation)
            return original(conversation, *args, **kwargs)
        target.apply_chat_template = capture
        try:
            for row in self.requests:
                messages.clear()
                self.engine.prepare(row["state"], row["questions"])
                if self.name == "eikos":
                    payloads = [json.loads(m[-1]["content"]) for m in messages]
                    for payload, question in zip(payloads, row["questions"].values()):
                        self.assertEqual(payload["evidence"], row["state"])
                        self.assertEqual(payload["criterion"], question["instructions"])
                        descriptions = question.get("criteria", {})
                        descriptions = descriptions if isinstance(descriptions, list) else list(descriptions.values())
                        for description in descriptions:
                            self.assertTrue(any(o["description"].endswith(": " + description) for o in payload["options"]))
                elif self.name == "nimble":
                    payload = json.loads(messages[0][-1]["content"].rsplit("\n\nRequested field: ", 1)[0])
                    self.assertEqual(payload["context"], review.state_text(row["state"]))
                    for field, question in zip(payload["schema"], row["questions"].values()):
                        self.assertEqual(field["description"], question["instructions"])
                        criteria = question.get("criteria", {})
                        expected = [criteria["false"], criteria["true"]] if question["type"] == "noul" and criteria else list(criteria.values()) if isinstance(criteria, dict) else criteria
                        self.assertEqual([c["description"] for c in field["choices"] if "description" in c], expected)
                else:
                    for m, question in zip(messages[:len(row["questions"])], row["questions"].values()):
                        text = m[-1]["content"][-1]["text"]
                        self.assertIn(review.state_text(row["state"]), text)
                        self.assertIn(question["instructions"], text)
                        criteria = question.get("criteria", {})
                        for description in criteria.values() if isinstance(criteria, dict) else criteria:
                            self.assertIn(description, text)
        finally:
            target.apply_chat_template = original

    def test_long_state_is_rejected_without_truncation(self):
        row = self.requests[12]
        with self.assertRaises(ValueError):
            self.engine.prepare(" word" * 8500, row["questions"])


if __name__ == "__main__":
    unittest.main()
