#!/usr/bin/env python3
"""Run pinned Kev-4B or Kev-9B on frozen native System One requests.

Uses the same {id, state, questions, ...metadata} input as laya-review.py.
Metadata never reaches inference. No server or remote inference is involved.
"""
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
RUNTIME = ROOT / ".local/kev/repo"
PIN = {
    "runtime_commit": "5920c5fe4ca8e0970ed4209ac2c9b8e18bea5109",
    "repo": "jaredpalmer/kev-4b",
    "revision": "139fdd94f1b6a6ad80cc15e08fcb99cac885a101",
    "base": "Qwen/Qwen3.5-4B-Base",
    "base_revision": "1001bb4d826a52d1f399e183466143f4da7b741b",
}
CACHE = ROOT / ".local/kev/hf"
SNAPSHOT = CACHE / "hub/models--jaredpalmer--kev-4b/snapshots" / PIN["revision"]
PINS = {"kev-4b": PIN, "kev-9b": {
    "runtime_commit": PIN["runtime_commit"],
    "repo": "jaredpalmer/kev-9b",
    "revision": "2629c06a5aeb0feb3b9783bafed17ed8f39ecf5c",
    "base": "Qwen/Qwen3.5-9B-Base",
    "base_revision": "68c46c4b3498877f3ef123c856ecfde50c39f404",
}}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def prepare_request(tok, request, model="kev-4b"):
    from kev.api import SystemOneRequest, to_record
    from kev.model import encode
    # Construct a new object: expected labels and source paths stay out of it.
    req = SystemOneRequest(state=request["state"], questions=request["questions"], model=model)
    record, meta = to_record(req)
    enc = encode(tok, record, strict=True, max_state=2048, max_branch=4096)
    state_tokens = enc["seg"].count(0)
    audit = {"state_truncated": enc["state_truncated"], "state_tokens": state_tokens,
             "packed_tokens": len(enc["ids"]), "encoding_sha256": digest(enc),
             "branch_tokens": [enc["seg"].count(i + 1) for i in range(len(meta))],
             "options": [len(indices) for indices in enc["opt_idx"]],
             "max_state": 2048, "max_row": 4096}
    return record, meta, enc, audit


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--input", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--audit-only", action="store_true")
    ap.add_argument("--model", choices=PINS, default="kev-4b")
    args = ap.parse_args()
    pin = PINS[args.model]
    snapshot = CACHE / ("hub/models--" + pin["repo"].replace("/", "--")) / "snapshots" / pin["revision"]
    revision = subprocess.check_output(["git", "-C", str(RUNTIME), "rev-parse", "HEAD"], text=True).strip()
    if revision != PIN["runtime_commit"]:
        ap.error("Kev source revision differs from the reviewed runtime pin")
    subprocess.run(["git", "-C", str(RUNTIME), "diff", "--exit-code", "HEAD", "--", "kev", "uv.lock", "pyproject.toml"],
                   check=True, stdout=subprocess.DEVNULL)
    os.environ["HF_HOME"] = str(CACHE)
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    if args.download:
        from huggingface_hub import snapshot_download
        for repo, rev in [(pin["repo"], pin["revision"]), (pin["base"], pin["base_revision"])]:
            snapshot_download(repo, revision=rev, cache_dir=CACHE / "hub",
                              allow_patterns=["*.json", "*.safetensors", "*.pt", "*.txt", "*.jinja"])
        return 0
    if not args.input or not args.output:
        ap.error("Supply --input and --output, or --download")
    if args.output.exists():
        ap.error("Output exists; choose a new evidence path")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    requests = json.loads(args.input.read_text())
    if not isinstance(requests, list) or not 1 <= len(requests) <= 32:
        ap.error("Require 1..32 bounded requests")
    from kev.checkpoint import Checkpoint, LoadOptions
    from kev.model import load_tokenizer
    from kev.api import to_answers
    ck = Checkpoint(str(snapshot))
    if (ck.meta.base, ck.meta.base_revision) != (pin["base"], pin["base_revision"]):
        ap.error("Checkpoint base differs from the pinned base")
    tok = load_tokenizer(ck.meta.base, revision=ck.meta.base_revision)
    prepared = [prepare_request(tok, request, args.model) for request in requests]
    model, load_ms = None, None
    if not args.audit_only:
        started = time.perf_counter()
        tok, model = ck.load("mps", LoadOptions(backend="mlx"))
        load_ms = round(1000 * (time.perf_counter() - started), 3)
        print(f"Loaded {args.model} via {model.backend} ({model.dtype}) in {load_ms} ms", file=sys.stderr, flush=True)
    report = {"schema": 1, "model": pin, "input_sha256": digest(requests),
              "runtime": {p: importlib.metadata.version(p) for p in ["kev", "mlx", "mlx-lm", "torch", "transformers", "tokenizers"]},
              "temperature": ck.meta.temperature, "advisory": True, "offline": True,
              "load_ms": load_ms, "cache": "state shared within each request; no reuse across requests",
              "backend": model.backend if model else None, "dtype": model.dtype if model else None,
              "rows": [], "note": "Completed inference is not a lint pass or model qualification. Input shape is identical to the Laya trial; each runtime uses its native text rendering."}
    for request, (record, meta, enc, audit) in zip(requests, prepared):
        row = {k: v for k, v in request.items() if k not in ["state", "questions"]}
        row.update(input_sha256=digest({k: request[k] for k in ["state", "questions"]}), audit=audit)
        if args.audit_only:
            row["status"] = "audited"
        else:
            actual = model.encode(tok, record, strict=True, max_state=2048, max_branch=4096)
            if actual != enc:
                raise ValueError("Loaded model encoding differs from preflight")
            started = time.perf_counter()
            # MLX's hidden pass calls mx.eval; conversion materializes each probability.
            probabilities = [p.tolist() for p in model.probs(enc)]
            row.update(status="inferred", elapsed_ms=round(1000 * (time.perf_counter() - started), 3),
                       result={"model": args.model, "answers": to_answers(probabilities, meta)})
        report["rows"].append(row)
        print(f"{row.get('id', '?')}: {row['status']} {row.get('result', {}).get('answers', {})}", file=sys.stderr, flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
