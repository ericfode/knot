#!/usr/bin/env python3
"""Bounded, offline Eikos/Nimble/AutoJev comparison using native decision runtimes.

Only state and questions reach the model. Native prompt templates and released
temperatures are retained; model-specific distributions remain in the receipt.
"""
import argparse
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
PINS = json.loads((ROOT / "tools/local-models/pins.json").read_text())
MAX_TOKENS = 8192


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def state_text(state):
    return state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)


def validate_questions(questions):
    if not isinstance(questions, dict) or not 1 <= len(questions) <= 16:
        raise ValueError("Require 1..16 typed questions")
    for question in questions.values():
        kind, criteria = question.get("type"), question.get("criteria")
        if kind not in ("noul", "choice", "score"):
            raise ValueError("Unknown decision type")
        if not isinstance(question.get("instructions"), str):
            raise ValueError("Require explicit string instructions")
        if kind == "score" and (not isinstance(criteria, list) or not 2 <= len(criteria) <= 255):
            raise ValueError("Score requires 2..255 ordered descriptions")
        if kind == "choice" and (not isinstance(criteria, dict) or not 1 <= len(criteria) <= 255):
            raise ValueError("Choice requires 1..255 options")
        if kind == "noul" and criteria is None:
            continue
        if kind == "noul" and (not isinstance(criteria, dict) or set(criteria) != {"false", "true"}):
            raise ValueError("Explicit Noul criteria must contain false and true")
        descriptions = criteria if isinstance(criteria, list) else criteria.values()
        if any(not isinstance(x, str) for x in descriptions):
            raise ValueError("This bounded trial requires string criteria")


def nimble_schema(questions):
    validate_questions(questions)
    schema = {}
    for name, question in questions.items():
        kind, criteria = question["type"], question.get("criteria", {})
        choices = [False, True] if kind == "noul" else (
            [str(i) for i in range(len(criteria))] if kind == "score" else list(criteria))
        descriptions = dict(enumerate(criteria)) if kind == "score" else criteria
        schema[name] = {"type": "boolean" if kind == "noul" else "enum",
                        "description": question["instructions"], "choices": choices,
                        "choice_descriptions": {str(k): v for k, v in descriptions.items()}}
    return schema


def bounded_audit(ids, extra=None):
    if not ids or any(not row for row in ids):
        raise ValueError("No input coverage")
    if max(map(len, ids)) > MAX_TOKENS:
        raise ValueError(f"Complete input exceeds {MAX_TOKENS} tokens; nothing was truncated")
    return {"complete": True, "max_tokens": MAX_TOKENS,
            "full_tokens": list(map(len, ids)), "encoding_sha256": digest(ids), **(extra or {})}


def summarize(question, probabilities):
    """Common probability view, without inventing a model confidence statistic."""
    expected = (["false", "true"] if question["type"] == "noul" else
                [str(i) for i in range(len(question["criteria"]))] if question["type"] == "score"
                else list(question["criteria"]))
    if set(probabilities) != set(expected):
        raise ValueError("Native output options differ from the submitted options")
    if any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities.values()):
        raise ValueError("Invalid probability")
    if abs(sum(probabilities.values()) - 1) > 1e-5:
        raise ValueError("Probability mass is not normalized")
    result = {"type": question["type"], "probabilities": probabilities}
    if question["type"] == "noul":
        result["noul"] = probabilities["true"]
    elif question["type"] == "score":
        result["score"] = sum(int(k) * p for k, p in probabilities.items())
        result["legend"] = dict(zip(expected, question["criteria"]))
    else:
        result["choice"] = max(probabilities, key=probabilities.get)
    return result


class Eikos:
    def __init__(self, path, load):
        from transformers import AutoTokenizer
        config = json.loads((path / "decision_config.json").read_text())
        os.environ["PROMPT_STYLE"] = config["prompt_version"].rsplit("-", 1)[-1]
        import decision_core as dc
        from mlx_decide import MLXDecider
        dc.set_max_one_pass(config.get("max_one_pass"))
        self.dc = dc
        self.model = MLXDecider(str(path)) if load else object.__new__(MLXDecider)
        if not load:
            self.model.tok = AutoTokenizer.from_pretrained(path, local_files_only=True)
        self.temperature = json.loads((path / "calib.json").read_text())

    def prepare(self, state, questions):
        validate_questions(questions)
        items = [(q, self.dc.options_of(q)) for q in questions.values()]
        ids = []
        for question, options in items:
            text = self.model.tok.apply_chat_template(self.dc.messages(state, question, options),
                tokenize=False, add_generation_prompt=True, enable_thinking=False)
            # The published input path encodes the entire rendered prompt.
            full = self.model.tok.encode(text, add_special_tokens=False)
            if hasattr(__import__("mlx_decide"), "messages"):
                if self.model._ids(state, question, options) != full:
                    raise ValueError("Native Eikos encoding differs from complete prompt")
            ids.append(full)
        return (state, items), bounded_audit(ids)

    def predict(self, prepared):
        state, items = prepared
        native = self.model.dist_many_cached(state, items)
        distributions = []
        for (q, _), (probs, _) in zip(items, native):
            distributions.append({{"yes": "true", "no": "false"}.get(k, k): v
                                  for k, v in probs.items()} if q["type"] == "noul" else probs)
        return distributions, native


class Nimble:
    def __init__(self, path, load):
        from transformers import AutoTokenizer
        from nimble.scoring.parallel_scorer import ParallelScorer
        from nimble.scoring.release_contract import prompt_builder
        if load:
            self.model = ParallelScorer(model_path=str(path), model_id=PINS["nimble"]["repo"],
                                       revision=PINS["nimble"]["revision"], max_input_tokens=MAX_TOKENS)
        else:
            self.model = object.__new__(ParallelScorer)
            self.model.tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
            self.model.prepare_prompts = prompt_builder(path, self.model.tokenizer)
            self.model.max_input_tokens = MAX_TOKENS
        self.temperature = 1.0

    def prepare(self, state, questions):
        schema = nimble_schema(questions)
        prepared = self.model.prepare(state_text(state), schema)
        if any(prepared.prefix_ids + suffix != full for suffix, full in
               zip(prepared.suffix_ids, prepared.full_ids)):
            raise ValueError("Nimble shared prefix lost input tokens")
        return prepared, bounded_audit(prepared.full_ids, {"prepared_sha256": digest(asdict(prepared))})

    def predict(self, prepared):
        import mlx.core as mx
        logits, stats = self.model.evaluate(prepared, mode="parallel")
        from nimble.scoring.parallel_schema import choice_key
        distributions = []
        for choices, row in zip(prepared.choices, logits):
            probs = mx.softmax(row / self.model.temperature)
            mx.eval(probs)
            distributions.append(dict(zip(map(choice_key, choices), probs.tolist())))
        return distributions, {"logits": [r.tolist() for r in logits], "metrics": stats}


class AutoJev:
    def __init__(self, path, load):
        from autojev.model import DecisionModel
        from transformers import AutoProcessor
        config = json.loads((path / "decision_config.json").read_text())
        self.cls = DecisionModel
        self.model = (DecisionModel(checkpoint=path, device="mps") if load else
                      SimpleNamespace(processor=AutoProcessor.from_pretrained(path, local_files_only=True),
                                      codes=config["codes"], device_name="cpu"))
        self.model.processor.tokenizer.padding_side = "left"
        self.temperature = config["temperature"]

    def prepare(self, state, questions):
        validate_questions(questions)
        rows = [{"state": state, "question": q} for q in questions.values()]
        # One question at a time bounds MPS working memory and avoids pad effects.
        batches = [self.cls.prepare(self.model, [row], max_length=MAX_TOKENS) for row in rows]
        ids = [batch.inputs["input_ids"][0].tolist() for batch in batches]
        from autojev.model import decision_messages
        for row, full in zip(rows, ids):
            text = self.model.processor.apply_chat_template(decision_messages(row, self.model.codes),
                tokenize=False, add_generation_prompt=True, enable_thinking=False)
            expected = self.model.processor.tokenizer.encode(text, add_special_tokens=False)
            if expected != full:
                raise ValueError("AutoJev processor changed the complete text-only prompt")
        return batches, bounded_audit(ids)

    def predict(self, prepared):
        import torch
        distributions = []
        with torch.inference_mode():
            for batch in prepared:
                probabilities = (self.model(batch) / self.temperature).softmax(-1).cpu().tolist()[0]
                distributions.append(probabilities[:batch.counts[0]])
        return distributions, distributions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=PINS, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Evidence output already exists")
    pin, directory = PINS[args.model], ROOT / ".local" / args.model
    repo = directory / "repo"
    if subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip() != pin["runtime_commit"]:
        parser.error("Runtime source differs from its reviewed revision")
    difference = subprocess.check_output(["git", "-C", str(repo), "diff", "HEAD", "--"], text=True)
    expected = (ROOT / "tools/local-models/autojev-mps.patch").read_text() if args.model == "autojev" else ""
    if difference != expected:
        parser.error("Unexpected runtime modifications")
    sys.path.insert(0, str(repo / "eikos" if args.model == "eikos" else repo / "src" if args.model == "autojev" else repo))
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    requests = json.loads(args.input.read_text())
    if not isinstance(requests, list) or not 1 <= len(requests) <= 32:
        parser.error("Require 1..32 requests")
    started = time.perf_counter()
    engine = {"eikos": Eikos, "nimble": Nimble, "autojev": AutoJev}[args.model](directory / "model", not args.audit_only)
    report = {"schema": 1, "model": pin, "input_sha256": digest(requests),
              "load_ms": round(1000 * (time.perf_counter() - started), 3), "temperature": engine.temperature,
              "advisory": True, "offline": True, "rows": [],
              "runtime": {p: importlib.metadata.version(p) for p in ["torch", "transformers", "safetensors"]}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusively reserve the receipt; failed inference retains completed rows.
    with args.output.open("x") as output:
        output.write(json.dumps(report, indent=2) + "\n")
    for request in requests:
        row = {k: v for k, v in request.items() if k not in ("state", "questions")}
        row["input_sha256"] = digest({k: request[k] for k in ("state", "questions")})
        prepared, row["audit"] = engine.prepare(request["state"], request["questions"])
        row["status"] = "audited"
        if not args.audit_only:
            started = time.perf_counter()
            distributions, native = engine.predict(prepared)
            if args.model == "autojev":
                from autojev.model import options
                distributions = [dict(zip(options(q)[0], p)) for q, p in zip(request["questions"].values(), distributions)]
            if len(distributions) != len(request["questions"]):
                raise ValueError("Missing native decisions")
            row.update(status="inferred", elapsed_ms=round(1000 * (time.perf_counter() - started), 3),
                       result={"answers": {name: summarize(q, p) for (name, q), p in
                                           zip(request["questions"].items(), distributions)}}, native=native)
        report["rows"].append(row)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        print(f"{row['id']}: {row['status']} {row.get('elapsed_ms', '')}", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
