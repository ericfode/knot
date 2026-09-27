#!/usr/bin/env python3
"""One prospectively frozen Parallax trajectory; paid dispatch requires run --live."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
R2 = ROOT / "research/life-inducer-hillclimb-r2"
POLICY = ROOT / "research/life-helper-review/config.json"
REVIEWER = ROOT / "research/life-helper-review/review.mjs"
LOCK = HERE / "input-lock.json"
TRIAL = HERE / "trial"
SCRATCH = ROOT / ".local/life-parallax-trial/P001"
POLICY_SHA = "2455ea1a27e80142f32f9cf0ca43af67ed905234e125811ecc06ff229d67d710"
PAYLOAD_SHA = "e54aa04b8fe3f8c2a8fed4836798b49cd4f00c352b58ca4c422298346826b837"
MODEL, EFFORT, JUDGE, ROUNDS = "gpt-6-astra", "low", "jev-1.13.0", 3
AXES = ["maximally_big_brain", "delightful_to_read", "highly_memetic", "anticipation", "payoff"]
SETTINGS = {"trial": "P001", "author_model": MODEL, "reasoning_effort": EFFORT,
            "judge_model": JUDGE, "max_rounds": ROUNDS, "compiler_repairs_per_round": 1,
            "trajectory_slots_consumed": 1, "remaining_slots_before": 15,
            "policy_validation": "provisional_held_out_target_separation_failed"}
PACKET_PARTS = [HERE / "inputs/parallax.decoded.txt", HERE / "AUTHOR.md", POLICY,
                R2 / "inputs/Bend-GUIDE.md", R2 / "inputs/base.bend.snapshot", HERE / "schema.json"]
WRAPPER = ("import Base\nimport ./candidate.bend as C\n\n"
           "def call_step(w: U32, h: U32, xs: List<&2,U32>) -> List<&2,U32>:\n  C.step(w,h,xs)\n\n"
           "def call_evolve(n: Nat, w: U32, h: U32, xs: List<&2,U32>) -> List<&2,U32>:\n  C.evolve(n,w,h,xs)\n")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


gate = module("parallax_behavior_gate", R2 / "gate.py")
transport = module("parallax_author_transport", R2 / "transport.py")


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    return digest(Path(path).read_bytes())


def rel(path):
    return str(Path(path).resolve().relative_to(ROOT))


def read(path):
    return json.loads(Path(path).read_bytes())


def save(path, value):
    raw = value if isinstance(value, bytes) else (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def require(ok, message, status="configuration_failure"):
    if not ok:
        raise gate.GateError(message, status)


def packet():
    stimulus = PACKET_PARTS[0].read_bytes()
    require(len(stimulus) == 3912 and digest(stimulus) == PAYLOAD_SHA, "Wrong Parallax payload")
    require(sha(POLICY) == POLICY_SHA, "The experimental policy must remain unchanged")
    data = stimulus
    parts = [{"path": rel(PACKET_PARTS[0]), "sha256": digest(stimulus), "start_byte": 0, "bytes": len(stimulus)}]
    for path, title in zip(PACKET_PARTS[1:], ["ASSIGNMENT AND FIXED CONTRACT", "EXACT FAMILY AND SUPPORT POLICY",
                          "PINNED BEND GUIDE", "PINNED BASE LIBRARY", "OUTPUT JSON SCHEMA"]):
        data += ("\n\n--- " + title + " ---\n").encode()
        raw = path.read_bytes()
        parts.append({"path": rel(path), "sha256": digest(raw), "start_byte": len(data), "bytes": len(raw)})
        data += raw
    data.decode("utf-8", errors="strict")
    return data, {"schema": "parallax-author-packet-v1", "sha256": digest(data), "bytes": len(data), "parts": parts}


def dependencies():
    paths = set(gate.BEHAVIOR_PINS) | set(gate.REVIEW_FILES)
    paths |= {rel(path) for path in PACKET_PARTS}
    paths |= {rel(path) for path in (HERE / "inputs").iterdir() if path.is_file()}
    paths |= {rel(HERE / name) for name in ("run.py", "test_run.py", "AUTHOR.md", "PROTOCOL.md", "README.md",
                                          "schema.json", "author-packet.txt", "packet-manifest.json")}
    paths |= {rel(R2 / "transport.py"), rel(R2 / "gate.py"), rel(REVIEWER), "README.md", "AGENTS.md",
              "docs/perch.md", "docs/perch-style.md", ".codex/skills/perch/SKILL.md"}
    # Include installed and transitive implementation files, not just package metadata.
    for tree in (ROOT / "node_modules", ROOT / "vendor/bend-parser", ROOT / ".perch/rules",
                 ROOT / ".toolchain/bend-2.0.29-574b6d3/bend2"):
        require(tree.is_dir(), "Missing installed dependency tree: " + str(tree))
        paths.update(str(path.relative_to(ROOT)) for path in tree.rglob("*") if path.is_file())
    return sorted(paths)


def runtime_identity():
    result = {}
    for name in ("python3", "node", "bun", "npm", "codex", "clang"):
        found = shutil.which(name)
        require(found, "Required runtime unavailable: " + name)
        path = Path(found).resolve()
        completed = subprocess.run([str(path), "--version"], capture_output=True, text=True, timeout=20)
        require(completed.returncode == 0, "Cannot identify runtime: " + name)
        result[name] = {"path": str(path), "sha256": sha(path), "version": completed.stdout.strip()}
    require(str(Path(sys.executable).resolve()) == result["python3"]["path"], "Use the pinned python3 executable")
    return result


def freeze():
    if LOCK.exists():
        return check(runtime=True)
    require(not TRIAL.exists(), "Cannot freeze inputs after trial creation")
    data, manifest = packet()
    for path, value in ((HERE / "author-packet.txt", data), (HERE / "packet-manifest.json", manifest)):
        if path.exists():
            expected = value if isinstance(value, bytes) else (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()
            require(path.read_bytes() == expected, "Existing packet differs: " + str(path))
        else:
            save(path, value)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    frozen = {path: sha(ROOT / path) for path in dependencies()}
    require(all(frozen[path] == value for path, value in gate.BEHAVIOR_PINS.items()), "Historical behavior changed")
    save(LOCK, {"schema": "life-parallax-input-lock-v1", "created_at": now(), "head_at_freeze": head,
                "settings": SETTINGS, "judge_model": JUDGE, "policy_sha256": POLICY_SHA,
                "frozen_files": frozen, "runtimes": runtime_identity(),
                "runtime_limit": "System libraries and compiler SDK are not recursively vendored; command receipts identify execution."})
    return check(runtime=True)


def check(*, runtime=False):
    require(LOCK.exists(), "Create the NEW Parallax input lock with freeze; never use the old R2 lock")
    data = read(LOCK)
    require(data.get("schema") == "life-parallax-input-lock-v1" and data.get("settings") == SETTINGS,
            "Wrong experiment lock/settings")
    require(data.get("policy_sha256") == POLICY_SHA and sha(POLICY) == POLICY_SHA, "Policy identity changed")
    state = gate.check_files(LOCK)
    require(set(dependencies()) == set(state["frozen_files"]), "Dependency inventory changed")
    require(all(state["frozen_files"][p] == v for p, v in gate.BEHAVIOR_PINS.items()), "Behavior pin changed")
    expected, manifest = packet()
    require((HERE / "author-packet.txt").read_bytes() == expected and read(HERE / "packet-manifest.json") == manifest,
            "Packet construction mismatch")
    if runtime:
        require(runtime_identity() == data["runtimes"], "Runtime identity changed")
    return {"status": "ready", "input_lock_sha256": state["lock_sha256"], "frozen_files": state["file_count"],
            "packet_sha256": manifest["sha256"], "policy_sha256": POLICY_SHA, "settings": SETTINGS}


def command(argv, receipt, timeout=180, env=None):
    before = check()["input_lock_sha256"]
    result = gate._command(argv, receipt, timeout=timeout, env=env)
    require(check()["input_lock_sha256"] == before, "Input lock changed during command")
    return result


def command_complete(result, allowed=(0,), status="provider_failure"):
    require(not result.get("timed_out") and not result.get("error") and result["exit"] in allowed,
            "Command did not complete; inspect its exact saved output", status)


def author(history, directory, ident):
    before = check()["input_lock_sha256"]
    prompt = (HERE / "author-packet.txt").read_text()
    for item in history:
        prompt += "\n\n--- " + item["role"] + " ---\n" + item["text"]
    prompt += "\n\nReturn only the requested JSON object containing your complete implementation.\n"
    receipt = transport.call(ident, prompt, HERE / "schema.json", directory, MODEL, EFFORT, timeout=600)
    require(check()["input_lock_sha256"] == before, "Input lock changed during author call")
    require(receipt["status"] == "completed", "Author transport unavailable: " + str(receipt.get("error")), "provider_failure")
    response = read(receipt["response_path"])
    history.append({"role": "YOUR PREVIOUS RESPONSE", "text": json.dumps(response, ensure_ascii=False)})
    return response


def compile_source(source, directory, scratch, name):
    raw = source.encode("utf-8")
    snapshot = directory / f"{name}.bend.snapshot"
    save(snapshot, raw)  # Always before any compiler invocation.
    if len(raw) > 49152 or raw.startswith(b"\xef\xbb\xbf"):
        return snapshot, {"exit": None, "source_limit": True, "stdout": "", "stderr": "Source exceeds UTF-8 cap or has BOM"}
    work = scratch / name
    work.mkdir(parents=True, exist_ok=False)
    save(work / "candidate.bend", raw)
    save(work / "entry.bend", WRAPPER.encode())
    receipt = command([ROOT / "scripts/bend-reference", work / "entry.bend", "--check-only"],
                      directory / f"compiler-{name}.json", timeout=75)
    require(not receipt.get("timed_out") and not receipt.get("error") and receipt["exit"] is not None and receipt["exit"] >= 0,
            "Compiler unavailable or interrupted", "evaluation_failure")
    require(sha(snapshot) == sha(work / "candidate.bend") == digest(raw), "Compiler source changed")
    return snapshot, receipt


def reviewer_call(manifest, directory, live):
    argv = ["node", REVIEWER, "--manifest", manifest, "--config", POLICY,
            "--output", directory / "helper-review", "--jobs", "2"]
    if live:
        argv.append("--live")
    result = command(argv, directory / ("style-command.json" if live else "style-preflight-command.json"), timeout=1200)
    if result.get("timed_out") or result.get("error"):
        command_complete(result)
    try:
        index = json.loads(result["stdout"])
        path = Path(index["report_path"]).resolve()
        require(path.is_relative_to(directory / "helper-review"), "Reviewer report escaped its output directory")
        report = read(path)
    except (ValueError, KeyError, TypeError) as error:
        raise gate.GateError("Missing structured reviewer report: " + str(error), "provider_failure") from error
    return result, path, report


def audit_style(report, source_hash, behavior_passed, semantic_clean):
    require(report.get("schema") == "life-helper-report-v1" and report.get("live") is True,
            "Expected a live composition/support report")
    require(report.get("requested_model") == JUDGE and report.get("policy", {}).get("sha256") == POLICY_SHA,
            "Style model or policy mismatch")
    failures = [str(report.get("failure") or "")] + [str(r.get("error") or "") for r in report.get("requests", [])]
    require(not any("model_mismatch" in v or "identity" in v or "receipt_" in v for v in failures),
            "Style model/receipt integrity failure: " + "; ".join(failures))
    require(report.get("status") == "complete" and not report.get("failure"),
            "Incomplete style provider result: " + "; ".join(failures), "provider_failure")
    require(len(report.get("entries", [])) == 1, "Expected one reviewed program")
    entry = report["entries"][0]
    require(entry.get("source_sha256") == entry.get("actual_source_sha256") == source_hash, "Style source mismatch")
    require(entry.get("status") != "preflight_rejected", "Candidate review preflight rejected", "attention")
    declarations = entry.get("declarations", [])
    family, support = entry.get("family_assessments", []), entry.get("support_assessments", [])
    require(0 < len(declarations) <= 64 and len({d["id"] for d in declarations}) == len(declarations), "Invalid declaration inventory")
    require([a["dimension"] for a in family] == AXES, "Missing family axis")
    require([a.get("declaration") for a in support] == declarations, "Missing or duplicate declaration support")
    coverage = entry.get("coverage", {})
    require(coverage == {"expected_family_assessments": 5, "expected_support_assessments": len(declarations),
            "completed_assessments": 5 + len(declarations), "required_assessments": 5 + len(declarations),
            "complete": True, "full_source": True, "truncated": False}, "Incomplete style coverage", "provider_failure")
    requests = report.get("requests", [])
    require(len(requests) == len(declarations) + 1 and len({r["id"] for r in requests}) == len(requests), "Style request coverage mismatch")
    request_ids = {r["id"] for r in requests}
    for response in requests:
        require(response.get("status") == "complete", "Style request unavailable", "provider_failure")
        receipt = response.get("receipt", {})
        require(receipt.get("resolved_model") == JUDGE and response.get("source_sha256") == source_hash,
                "Style response model/source mismatch")
    for index, assessment in enumerate(family + support):
        dimension = AXES[index] if index < 5 else "supports_main_idea"
        target = {"dimension": dimension, "level": 5 if index == 0 else 3, "minimum_probability": .6}
        require(assessment.get("dimension") == dimension and assessment.get("target") == target and assessment.get("required") is True,
                "Style target changed")
        require(assessment.get("request_id") in request_ids and assessment.get("resolved_model") == JUDGE
                and assessment.get("requested_model") == JUDGE, "Assessment model or request mismatch")
        probabilities = assessment.get("probabilities", {})
        count = len(read(POLICY)["family_dimensions"][index]["levels"]) if index < 5 else 5
        require(set(probabilities) == {str(i) for i in range(count)}, "Malformed probability levels")
        require(all(type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 1 for v in probabilities.values())
                and sum(probabilities.values()) > 0, "Malformed probability values")
        mass = sum(v for k, v in probabilities.items() if int(k) >= target["level"]) / sum(probabilities.values())
        status = "meets_target" if mass >= .6 else "below_target" if mass <= .4 else "uncertain"
        require(abs(mass - assessment.get("target_probability", -1)) < 1e-12 and status == assessment.get("status"),
                "Style target mass/status inconsistent")
    family_passed = all(a["status"] == "meets_target" for a in family)
    support_passed = all(a["status"] == "meets_target" for a in support)
    passed = bool(behavior_passed and semantic_clean and family_passed and support_passed)
    require(entry.get("deterministic_passed") is behavior_passed and entry.get("semantic_clean") is semantic_clean,
            "Style input gates mismatch")
    require(entry.get("family_passed") is family_passed and entry.get("support_passed") is support_passed
            and entry.get("full_pass") is passed, "Style acceptance fields inconsistent")
    require(report.get("transport", {}).get("peak_in_flight", 99) <= 2, "Review concurrency exceeded bound")
    return {"family_passed": family_passed, "support_passed": support_passed, "full_pass": passed,
            "family_met": sum(a["status"] == "meets_target" for a in family), "family_required": 5,
            "support_met": sum(a["status"] == "meets_target" for a in support), "support_required": len(support)}


def semantic_review(source, directory, neutral):
    target, source_hash = rel(neutral), sha(source)
    before = set((ROOT / ".perch/usage").glob("*.json"))
    result = command(["npm", "run", "lint", "--", target, "--rules", ",".join(gate.RULES), "--parallel", "2"],
                     directory / "semantic-command.json", timeout=600,
                     env={**os.environ, "PERCH_JOBS": "2", "PERCH_MODEL_ID": JUDGE})
    usages = [read(p) for p in sorted(set((ROOT / ".perch/usage").glob("*.json")) - before)]
    usages = [u for u in usages if u.get("command") == "check" and u.get("target") == target]
    save(directory / "semantic-usage.json", usages)
    command_complete(result, (0, 3))
    require(len(usages) == 1, "Expected exactly one matching semantic usage receipt", "provider_failure")
    semantic = gate._json_result(result["stdout"])
    save(directory / "semantic.json", semantic)
    require(sha(source) == sha(neutral) == source_hash, "Source changed during semantic review")
    try:
        summary = gate._semantic_valid(semantic, usages[0], source_hash, target, JUDGE)
    except gate.GateError as error:
        if error.status != "attention":
            raise
        summary = {"clean": False, "adjudication": "unresolved", "coverage_attention": str(error)}
    return summary, semantic


def reviews(source, directory, behavior):
    source_hash = sha(source)
    entry = {"id": "specimen", "source": rel(source), "source_sha256": source_hash,
             "deterministic_passed": behavior["passed"], "semantic_clean": None}
    preflight_manifest = directory / "style-preflight-manifest.json"
    save(preflight_manifest, {"root": str(ROOT), "entries": [entry]})
    result, preflight_path, preflight = reviewer_call(preflight_manifest, directory, False)
    command_complete(result, (0,), "configuration_failure")
    require(len(preflight.get("entries", [])) == 1, "Preflight inventory missing")
    pre = preflight["entries"][0]
    if pre.get("errors"):
        return {"status": "attention", "full_pass": False, "semantic_clean": False,
                "style_preflight_receipt": rel(preflight_path), "preflight_errors": pre["errors"]}, {"preflight_errors": pre["errors"]}
    neutral = SCRATCH / "life.bend"
    neutral.parent.mkdir(parents=True, exist_ok=True)
    neutral.write_bytes(source.read_bytes())
    require(sha(neutral) == source_hash, "Neutral copy differs")
    summary, semantic = semantic_review(source, directory, neutral)
    clean = bool(summary["clean"])
    entry["semantic_clean"] = clean
    manifest = directory / "style-manifest.json"
    save(manifest, {"root": str(ROOT), "entries": [entry]})
    result, path, style = reviewer_call(manifest, directory, True)
    # Audit failure/model evidence before generic command exit classification.
    assessment = audit_style(style, source_hash, bool(behavior["passed"]), clean)
    command_complete(result)
    require(sha(source) == sha(neutral) == source_hash, "Source changed during review")
    report = {"status": "passed" if assessment["full_pass"] else "attention", **assessment,
              "semantic_clean": clean, "semantic_summary": summary, "semantic_receipt": rel(directory / "semantic.json"),
              "style_receipt": rel(path), "usage": style["usage"], "transport": style["transport"]}
    own_entry = style["entries"][0]
    feedback = {"semantic": {"summary": summary, "units": semantic.get("units", []), "issues": semantic.get("issues", [])},
                "composition_support": {"coverage": own_entry["coverage"], "family_assessments": own_entry["family_assessments"],
                                        "support_assessments": own_entry["support_assessments"]}}
    return report, feedback


def body_feedback(behavior):
    return {key: behavior.get(key) for key in ("passed", "status", "counts", "legacy_status") if key in behavior}


def run_round(number, history, hashes):
    directory = TRIAL / f"round-{number:02d}"
    directory.mkdir(exist_ok=False)
    scratch = SCRATCH / f"round-{number:02d}"
    report = {"number": number, "status": "started", "full_pass": False, "behavior_passed": False,
              "semantic_clean": False, "compiler_first_passed": False, "compiler_repair": False}
    feedback = {}
    try:
        history.append({"role": "ROUND REQUEST", "text": f"Round {number} of at most 3. " +
                        ("Write your initial implementation and concrete reading hypothesis." if number == 1 else
                         "Read your own prior feedback and revise under a concrete reading hypothesis. No unchanged reroll.")})
        response = author(history, directory, "author")
        first, compiler = compile_source(response["source"], directory, scratch, "first")
        source = first
        report["compiler_first_passed"] = compiler["exit"] == 0
        if compiler["exit"] and not compiler.get("source_limit"):
            history.append({"role": "COMPILER DIAGNOSTIC REPAIR", "text":
                            "One repair is allowed based ONLY on this compiler diagnostic. Preserve your intended mechanism.\n" +
                            compiler["stdout"] + "\n" + compiler["stderr"]})
            response = author(history, directory, "repair")
            source, compiler = compile_source(response["source"], directory, scratch, "repaired")
            report["compiler_repair"] = True
        final = directory / "final.bend.snapshot"
        save(final, source.read_bytes())
        source_hash = sha(final)
        report.update(source=rel(final), source_sha256=source_hash, first_source=rel(first),
                      final_from=rel(source), hypothesis=response["hypothesis"], findings=response["findings"])
        if compiler["exit"] != 0:
            report["status"] = "source_limit" if compiler.get("source_limit") else "compiler_failed"
            feedback = {"compiler": compiler, "note": "This round is exhausted; no further compiler repair is permitted."}
        elif source_hash in hashes:
            report["status"] = "unchanged_submission"
            feedback = {"note": "This exact source was already submitted. No behavior or model review was rerolled."}
        else:
            hashes.add(source_hash)
            check()
            behavior = gate.evaluate_behavior(final, directory, f"parallax-P001-r{number}", lock=LOCK)
            check()
            report.update(behavior_receipt=rel(directory / "behavior.json"), behavior_passed=bool(behavior["passed"]))
            require(behavior["status"] not in ("evaluation_failure", "configuration_failure"),
                    "Behavior unavailable: " + str(behavior.get("error")), behavior["status"])
            feedback = {"behavior": body_feedback(behavior)}
            report["status"] = "behavior_failed"
            if behavior["passed"]:
                review, review_feedback = reviews(final, directory, behavior)
                save(directory / "reviews.json", review)
                report.update(status=review["status"], full_pass=review["full_pass"],
                              semantic_clean=review["semantic_clean"], reviews_receipt=rel(directory / "reviews.json"))
                feedback.update(review_feedback)
        hashes.add(source_hash)
    except Exception as error:
        report.update(status=getattr(error, "status", "configuration_failure"), error=f"{type(error).__name__}: {error}")
        feedback = {"unavailable": report["error"]}
    save(directory / "feedback.json", feedback)
    save(directory / "round.json", report)
    history.append({"role": "YOUR ROUND FEEDBACK", "text": json.dumps(feedback, ensure_ascii=False)})
    print(json.dumps({"event": "round_complete", **report}), flush=True)
    return report


def seal():
    save(TRIAL / "artifacts.json", {"schema": "parallax-trial-artifacts-v1",
                                    "files": {rel(p): sha(p) for p in sorted(TRIAL.rglob("*")) if p.is_file()}})


def replay():
    require((TRIAL / "result.json").exists() and (TRIAL / "artifacts.json").exists(),
            "Partial trajectory exists. Inspect it; automatic resume and reroll are blocked")
    files = read(TRIAL / "artifacts.json")["files"]
    require(set(files) == {rel(p) for p in TRIAL.rglob("*") if p.is_file() and p.name != "artifacts.json"},
            "Saved trial inventory changed")
    for name, expected in files.items():
        require(sha(ROOT / name) == expected, "Saved trial artifact changed: " + name)
    result = read(TRIAL / "result.json")
    require(result["input_lock_sha256"] == sha(LOCK), "Saved trial lock changed")
    return result


def run(live):
    require(live, "Paid dispatch requires the explicit run --live command")
    state = check(runtime=True)
    if TRIAL.exists():
        return replay()
    require(not SCRATCH.exists(), "Neutral/scratch identity already exists; inspect without reroll")
    TRIAL.mkdir(exist_ok=False)
    save(TRIAL / "started.json", {"at": now(), **state})
    rounds, history, hashes = [], [], set()
    for number in range(1, ROUNDS + 1):
        report = run_round(number, history, hashes)
        rounds.append(report)
        if report["full_pass"] or report["status"] in ("provider_failure", "configuration_failure", "evaluation_failure"):
            break
    selected = next((r for r in rounds if r["full_pass"]), None)
    last = rounds[-1]
    unavailable = last["status"] in ("provider_failure", "configuration_failure", "evaluation_failure")
    authors = []
    for path in sorted(TRIAL.glob("round-*/*.receipt.json")):
        if ".attempt-" in path.name:
            continue
        receipt = read(path)
        authors.append({"receipt": rel(path), "sha256": sha(path),
                        **{k: receipt.get(k) for k in ("requested_model", "requested_reasoning_effort", "reported_models",
                           "reported_reasoning_efforts", "model_validation", "effort_validation", "usage", "status")}})
    result = {"schema": "life-parallax-result-v1", **SETTINGS, "input_lock_sha256": state["input_lock_sha256"],
              "finished_at": now(), "status": last["status"] if unavailable else "experimental_full_pass" if selected else "completed_no_full_pass",
              "full_pass": selected is not None, "experimental_full_pass": selected is not None,
              "policy_qualified_for_global_acceptance": False, "global_perch_v3_evaluated": False,
              "author_receipts": authors, "round_count": len(rounds), "rounds": rounds,
              "selected_source": selected.get("source") if selected else None,
              "selected_source_sha256": selected.get("source_sha256") if selected else None,
              "last_source": last.get("source"), "last_source_sha256": last.get("source_sha256"), "billed_cost_usd": None,
              "limits": ["One trajectory; no causal inducer claim", "Finite fixed corpus; no general behavioral proof",
                         "Mixed helper calibration; experimental policy", "No performance claim", "No automatic semantic finding dismissal"]}
    save(TRIAL / "result.json", result)
    seal()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "check", "run"))
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    try:
        result = freeze() if args.command == "freeze" else check(runtime=True) if args.command == "check" else run(args.live)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return 2 if result["status"] in ("provider_failure", "configuration_failure", "evaluation_failure") else 0
    except Exception as error:
        print(json.dumps({"status": getattr(error, "status", "configuration_failure"), "error": str(error)}), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
