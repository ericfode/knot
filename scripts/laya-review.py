#!/usr/bin/env python3
"""Offline, bounded System One experiments with pinned Laya; no server or API key.

Input is a JSON array of {id, state, questions, ...metadata}. Metadata (including
expected labels) never reaches the model. Output is advisory evidence, not a lint
pass. See docs/laya-local-2026-09-26.md for setup and the failed qualification.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
MODEL = {
    "repo": "convaiinnovations/laya",
    "revision": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851",
    "laya_version": "0.3.20",
}
CACHE = ROOT / ".local/perch-laya/hf/hub"
SNAPSHOT = CACHE / "models--convaiinnovations--laya/snapshots" / MODEL["revision"]


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def full_sequence(tok, state, question):
    """Construct the uncut equivalent of pinned Laya's input format.

    Compare against the actual library encoder before inference. Neither source
    nor instructions nor options may silently disappear. This does not replace
    the model encoder or manufacture probabilities.
    """
    from laya import Agent
    from laya.common import render_options, serialize_state

    Agent._check_question("question", question)
    q = Agent._to_internal(question)
    texts = [serialize_state(state), q["ins"], *render_options(q)]
    if any(tok.mask_token in text for text in texts):
        raise ValueError("Input contains the model mask token; native encoding would rewrite it")
    tokens = lambda text: tok(text, add_special_tokens=False)["input_ids"]
    head = tokens(q["t"] + " question: " + q["ins"])
    options = [tokens(" " + text) for text in render_options(q)]
    state_ids = tokens(serialize_state(state))
    ids = [tok.cls_token_id] + head + [tok.sep_token_id]
    markers = []
    for option in options:
        markers.append(len(ids))
        ids += [tok.mask_token_id] + option
    ids += [tok.sep_token_id] + state_ids + [tok.sep_token_id]
    return q, ids, markers, {
        "state_tokens": len(state_ids), "instruction_tokens": len(head),
        "option_tokens": [len(option) for option in options],
        "sequence_tokens": len(ids),
        "head_budget": len(head) + sum(len(option) + 1 for option in options) + 16,
    }


def audit_request(tok, state, questions, max_len):
    from laya.common import build_sequence

    if not isinstance(questions, dict) or not questions or len(questions) > 16:
        raise ValueError("Require 1..16 typed questions per request")
    if any(not isinstance(name, str) or not name for name in questions):
        raise ValueError("Question IDs must be nonempty strings")
    if state is None or not isinstance(state, (str, dict, list)):
        raise ValueError("Require an explicit string, object, or array state")
    if not isinstance(max_len, int) or not 1 <= max_len <= 8192:
        raise ValueError("Sequence budget must be within the encoder's 8192-token limit")
    prepared = {name: full_sequence(tok, state, q) for name, q in questions.items()}
    head_budget = max(item[3]["head_budget"] for item in prepared.values())
    checks, reasons = {}, []
    for name, (q, expected, markers, info) in prepared.items():
        actual, actual_markers = build_sequence(tok, state, q, max_len, head_budget,
                                               truncate_left=isinstance(state, list))
        default, _ = build_sequence(tok, state, q, 512, 192,
                                    truncate_left=isinstance(state, list))
        checks[name] = {**info, "complete": actual == expected and actual_markers == markers,
                        "default_encoding_complete": default == expected,
                        "sequence_sha256": digest(actual)}
        if max(info["option_tokens"]) > 48:
            reasons.append(f"{name}: option description exceeds Laya's fixed 48-token cap")
        if len(expected) > max_len:
            reasons.append(f"{name}: full sequence needs {len(expected)} tokens, budget is {max_len}")
        if not checks[name]["complete"] and not any(r.startswith(name + ":") for r in reasons):
            reasons.append(f"{name}: native encoding differs from the complete input")
    return {"complete": not reasons, "reasons": reasons, "head_budget": head_budget,
            "max_len": max_len, "questions": checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Fetch only the pinned English checkpoint")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--device", choices=["mps", "cpu"], default="mps")
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()
    if importlib.metadata.version("laya") != MODEL["laya_version"]:
        parser.error("Input audit requires pinned Laya 0.3.20")
    if args.download:
        from huggingface_hub import snapshot_download
        snapshot_download(MODEL["repo"], revision=MODEL["revision"], cache_dir=CACHE,
                          allow_patterns=["rl_agent_config.json", "model.safetensors", "tokenizer/*", "encoder/*"])
        print(SNAPSHOT)
        return 0
    if not args.input or not args.output:
        parser.error("Supply --input and --output, or --download")
    if args.output.exists():
        parser.error("Output exists; choose a new evidence path")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    if not (SNAPSHOT / "model.safetensors").exists():
        parser.error("Pinned weights missing; run --download first")
    requests = json.loads(args.input.read_text())
    if not isinstance(requests, list) or not requests or len(requests) > 32:
        parser.error("Supply 1..32 bounded requests")
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(SNAPSHOT / "tokenizer", local_files_only=True)
    # Preflight every request before loading the model. No partial answer is
    # inferred for a request whose questions or source cannot fit intact.
    audits = [audit_request(tok, r["state"], r["questions"], args.max_tokens) for r in requests]
    agent, load_ms = None, None
    if not args.audit_only and any(a["complete"] for a in audits):
        from laya import Agent
        started = time.perf_counter()
        agent = Agent(str(SNAPSHOT), device=args.device)
        load_ms = round(1000 * (time.perf_counter() - started), 3)
    report = {"schema": 1, "model": MODEL, "input_sha256": digest(requests),
              "runtime": {p: importlib.metadata.version(p) for p in ["laya", "torch", "transformers", "tokenizers", "numpy"]},
              "advisory": True, "offline": True, "load_ms": load_ms, "rows": [],
              "note": "Successful inference is not a lint pass. Expected labels remain outside model input. Budget overrides preserve complete wording; extended inputs are outside the checkpoint's default 512-token setting."}
    for request, audit in zip(requests, audits):
        row = {k: v for k, v in request.items() if k not in ["state", "questions"]}
        row.update(input_sha256=digest({k: request[k] for k in ["state", "questions"]}), audit=audit)
        if not audit["complete"]:
            row["status"] = "unsupported-input"
        elif args.audit_only:
            row["status"] = "audited"
        else:
            # Verify the loaded Agent uses the same tokenizer as preflight.
            if audit_request(agent.tok, request["state"], request["questions"], args.max_tokens) != audit:
                raise ValueError("Loaded model tokenizer differs from preflight")
            started = time.perf_counter()
            result = agent.predict(request["state"], request["questions"], max_len=args.max_tokens,
                                   head_max_len=audit["head_budget"])
            row.update(status="inferred", elapsed_ms=round(1000 * (time.perf_counter() - started), 3),
                       device=str(agent.device), result=result)
        report["rows"].append(row)
        print(f"{row.get('id', '?')}: {row['status']}", file=sys.stderr, flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    return 1 if any(not audit["complete"] for audit in audits) else 0


if __name__ == "__main__":
    sys.exit(main())
