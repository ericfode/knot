#!/usr/bin/env python3
"""Pinned, offline Julia-1 MLX trial on the frozen local-review request format."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".local/julia/repo"
PIN = {"runtime_commit": "afbef9ee5d08646efd9baf4ab6d7ad75b0b23b93",
       "repo": "SupersonicLabs/Julia-1", "revision": "a85b127321d580d65176c89ced8273f305745d85"}
CACHE = ROOT / ".local/julia/hf/hub"
SNAPSHOT = CACHE / "models--SupersonicLabs--Julia-1/snapshots" / PIN["revision"]
MAX_LENGTH, HEAD_LENGTH = 2048, 512


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


class RowsPrepared(Exception):
    pass


class RowCapture:
    def logits(self, rows):
        # Stop the native typed adapter at its inference boundary. No fabricated
        # probabilities or model calls are used to obtain the exact input rows.
        raise RowsPrepared(rows)


def native_rows(state, questions):
    from julia_mlx.engine import JuliaEngine
    if not isinstance(questions, dict) or not 1 <= len(questions) <= 16:
        raise ValueError("Require 1..16 typed questions")
    try:
        JuliaEngine.predict_typed(RowCapture(), state, questions)
    except RowsPrepared as prepared:
        return prepared.args[0]
    raise RuntimeError("Native adapter did not reach the expected inference boundary")


def audit_request(tok, state, questions):
    from julia_mlx.encoding import sequence, validate_row
    rows = native_rows(state, questions)
    audits, reasons = {}, []
    for name, row in zip(questions, rows):
        validate_row(row)
        text = row["state"] if isinstance(row["state"], str) else json.dumps(row["state"], ensure_ascii=False)
        head = tok.encode(f"{row['type']} question: {row['question']}")
        options = [tok.encode(" " + option) for option in row["options"]]
        state_ids = tok.encode(text)
        expected = [tok.cls_token_id] + head + [tok.sep_token_id]
        markers = []
        for option in options:
            markers.append(len(expected))
            expected += [tok.mask_token_id] + option
        expected += [tok.sep_token_id] + state_ids + [tok.sep_token_id]
        audit = {"state_tokens": len(state_ids), "instruction_tokens": len(head),
                 "option_tokens": list(map(len, options)), "full_sequence_tokens": len(expected),
                 "complete": False}
        try:
            encoded = sequence(tok, row, MAX_LENGTH, HEAD_LENGTH, strict=True)
            if encoded["ids"] != expected or encoded["markers"] != markers:
                raise ValueError("Native encoding differs from the complete input")
            audit.update(complete=True, encoding_sha256=digest(encoded))
        except ValueError as error:
            audit["reason"] = str(error)
            reasons.append(f"{name}: {error}")
        audits[name] = audit
    return {"complete": not reasons, "reasons": reasons, "max_length": MAX_LENGTH,
            "head_length": HEAD_LENGTH, "questions": audits}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()
    revision = subprocess.check_output(["git", "-C", str(RUNTIME), "rev-parse", "HEAD"], text=True).strip()
    if revision != PIN["runtime_commit"]:
        parser.error("Julia MLX runtime differs from the reviewed source pin")
    subprocess.run(["git", "-C", str(RUNTIME), "diff", "--exit-code", "HEAD", "--",
                    "julia_mlx", "uv.lock", "pyproject.toml"], check=True, stdout=subprocess.DEVNULL)
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    if args.download:
        from huggingface_hub import snapshot_download
        snapshot_download(PIN["repo"], revision=PIN["revision"], cache_dir=CACHE,
                          allow_patterns=["julia_config.json", "config.json", "encoder/config.json",
                                          "model.safetensors", "tokenizer/*"])
        return 0
    if not args.input or not args.output:
        parser.error("Supply --input and --output, or --download")
    if args.output.exists():
        parser.error("Output exists; choose a new evidence path")
    os.environ["HF_HUB_OFFLINE"] = "1"
    requests = json.loads(args.input.read_text())
    if not isinstance(requests, list) or not 1 <= len(requests) <= 32:
        parser.error("Require 1..32 bounded requests")
    from julia_mlx.tokenizer import JuliaTokenizer
    tok = JuliaTokenizer(SNAPSHOT / "tokenizer", cache_size=0)
    audits = [audit_request(tok, row["state"], row["questions"]) for row in requests]
    engine, load_ms = None, None
    if not args.audit_only and any(a["complete"] for a in audits):
        from julia_mlx import load_model
        started = time.perf_counter()
        engine = load_model(str(SNAPSHOT), max_length=MAX_LENGTH, head_length=HEAD_LENGTH,
                            strict_encoding=True, dtype="float32", embedding="mapped",
                            encoding_cache=0, token_cache=0)
        load_ms = round(1000 * (time.perf_counter() - started), 3)
    report = {"schema": 1, "model": PIN, "input_sha256": digest(requests),
              "runtime": {p: importlib.metadata.version(p) for p in ["julia-mlx", "mlx", "numpy", "tokenizers", "safetensors"]},
              "backend": "mlx", "dtype": "float32", "embedding": "mapped",
              "encoding_cache": 0, "token_cache": 0, "load_ms": load_ms,
              "advisory": True, "offline": True, "rows": [],
              "note": "Completed inference is not a lint pass. Unsupported requests have no partial answers. Native typed probabilities are preserved without display rounding."}
    for request, audit in zip(requests, audits):
        row = {k: v for k, v in request.items() if k not in ["state", "questions"]}
        row.update(input_sha256=digest({k: request[k] for k in ["state", "questions"]}), audit=audit)
        if not audit["complete"]:
            row["status"] = "unsupported-input"
        elif args.audit_only:
            row["status"] = "audited"
        else:
            if audit_request(engine.tokenizer, request["state"], request["questions"]) != audit:
                raise ValueError("Loaded engine's input encoding differs from preflight")
            started = time.perf_counter()
            result = engine.predict(state=request["state"], questions=request["questions"])
            row.update(status="inferred", elapsed_ms=round(1000 * (time.perf_counter() - started), 3), result=result)
        report["rows"].append(row)
        print(f"{row.get('id', '?')}: {row['status']} {row.get('result', audit['reasons'])}", file=sys.stderr, flush=True)
    if engine:
        report["memory_bytes"] = engine.memory_stats()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    return 1 if any(not a["complete"] for a in audits) else 0


if __name__ == "__main__":
    sys.exit(main())
