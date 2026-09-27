#!/usr/bin/env python3
"""Locked Life gates. Importing this module performs no checks or paid calls.

The parent owns source snapshots and combines behavior['passed'] with
reviews['passed']. Each output directory admits one call of each kind.
"""
from __future__ import annotations

import ast
import datetime as dt
import fcntl
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUT_LOCK = HERE / "input-lock.json"
LEGACY = ROOT / "research/life-blueberry/gates/evaluate.py"
RULES = (
    "bend-machine-arithmetic", "bend-fuel-completeness",
    "perf-growing-prefix-copy", "perf-linked-list-indexing",
)
BEHAVIOR_PINS = {
    "research/life-blueberry/gates/evaluate.py": "e1a8c983855e55773382ca6d18bba58075003ba1e8a07dc5ca48f5adb2a6a825",
    "research/life-blueberry/gates/fixtures.mjs": "c04bbe26aaec07a9227afffcc57e9e720f5122d9b67e3a18b29ecf1a5c79ce9d",
    "research/life-blueberry/gates/run.mjs": "6351451411a79d8709aae499fe3067667b5391368f473de81a53d1df6c05a874",
    "scripts/bend-reference": "50f5b1843feef0e6120d11c71b60b7147fc94c5328e61e2ad5ac9f3e4a3bd3a3",
    "tests/perch-performance/compile.ts": "f6c82122b7c60ec3a3286a7ae5fe591a52295d3a9c4d590014ad66730d928b75",
    ".toolchain/bend-2.0.29-574b6d3/bend2/main.ts": "0a6c19ee942ec4fadcf7daaa69ca1cfd395a5ee8ef130df72b548291def93884",
    ".toolchain/bend-2.0.29-574b6d3/bend2/bend.ts": "09d2cc5c5d757f1a694dd126ccbac72ef2374cfe948d9d51c2b08247c5d2581e",
    ".toolchain/bend-2.0.29-574b6d3/bend2/comp.ts": "0cf866b28ff273d47970b3c16e82288e9676ce9f0ea3fce49877a82ce4a6301b",
    ".toolchain/bend-2.0.29-574b6d3/bend2/base.bend": "22eea83911e2395f63594fea7c10ac0c1e5b548251681fc97cd7667e0eb7031b",
}
REVIEW_FILES = {
    "perch-style.json", "scripts/perch-style.mjs", "scripts/perch-workflow.mjs",
    "scripts/perch-style-cache.mjs",
    "scripts/perch-bend.mjs", "scripts/perch-bend-context.mjs",
    "scripts/perch-throughput.mjs", "scripts/perch-throughput-patch.mjs",
    "scripts/install-perch-bend.mjs", "perch.yaml",
    ".perch/rules/bend.yaml", ".perch/rules/performance.yaml",
    "package.json", "package-lock.json",
}


class GateError(RuntimeError):
    """Unavailable, mismatched or incomplete gate evidence."""

    def __init__(self, message, status="configuration_failure"):
        super().__init__(message)
        self.status = status


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _rel(path):
    path = Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def _read(path):
    path = Path(path)
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def _write(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def _require(condition, message, status="configuration_failure"):
    if not condition:
        raise GateError(message, status)


def _lock_data(lock):
    if isinstance(lock, dict):
        raw = json.dumps(lock, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        return json.loads(raw), hashlib.sha256(raw).hexdigest()
    path = Path(lock) if lock is not None else INPUT_LOCK
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def check_files(lock=None):
    """Check a lock path or {'frozen_files': {root-relative path: SHA-256}}.

    Raises GateError (or a read error) on missing/changed inputs. The optional
    judge_model is an observed-model pin, defaulting to jev-1.13.0.
    """
    data, identity = _lock_data(lock)
    files = data.get("frozen_files")
    _require(isinstance(files, dict) and files, "Lock needs nonempty frozen_files")
    for name, digest in files.items():
        path = Path(name)
        _require(not path.is_absolute() and ".." not in path.parts,
                 f"Lock path must be root-relative: {name}")
        actual = (ROOT / path).resolve()
        _require(actual.is_relative_to(ROOT), f"Lock path escapes root: {name}")
        _require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest),
                 f"Invalid SHA-256 for {name}")
        _require(actual.is_file() and sha(actual) == digest, f"Changed frozen input: {name}")
    model = data.get("judge_model", "jev-1.13.0")
    _require(isinstance(model, str) and model and model != "jev-latest",
             "judge_model must name an observable resolved model")
    return {"passed": True, "lock_sha256": identity, "frozen_files": files,
            "judge_model": model, "file_count": len(files)}


def _locked(lock, required):
    result = check_files(lock)
    missing = set(required) - result["frozen_files"].keys()
    _require(not missing, "Lock omits required inputs: " + ", ".join(sorted(missing)))
    return result


def _unchanged_lock(lock, before):
    after = check_files(lock)
    _require(after["lock_sha256"] == before["lock_sha256"], "Input lock changed during gate")


def _command(argv, path, *, timeout, env=None):
    """One process, no retries; preserve full output even on timeout/spawn error."""
    argv = [str(x) for x in argv]
    start = time.monotonic()
    record = {"argv": argv, "cwd": str(ROOT), "timeout_seconds": timeout,
              "at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "exit": None, "stdout": "", "stderr": ""}
    try:
        process = subprocess.Popen(argv, cwd=ROOT, env=env, text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True)
        try:
            record["stdout"], record["stderr"] = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            record["timed_out"] = True
            os.killpg(process.pid, signal.SIGKILL)
            record["stdout"], record["stderr"] = process.communicate()
        record["exit"] = process.returncode
    except OSError as error:
        record["error"] = str(error)
    record["seconds"] = time.monotonic() - start
    _write(path, record)
    return record


class _LegacyPaths(ast.NodeTransformer):
    """Only the old evaluator's lock and ignored work paths may change."""
    def __init__(self, lock_path):
        self.lock_path = str(lock_path)
        self.lock_count = 0
        self.work_count = 0

    def visit_BinOp(self, node):
        if (isinstance(node.op, ast.Div) and isinstance(node.left, ast.Name)
                and node.left.id == "EXPERIMENT" and isinstance(node.right, ast.Constant)
                and node.right.value == "preregistration.json"):
            self.lock_count += 1
            return ast.copy_location(ast.Call(func=ast.Name(id="Path", ctx=ast.Load()),
                args=[ast.Constant(self.lock_path)], keywords=[]), node)
        return self.generic_visit(node)

    def visit_Constant(self, node):
        if node.value == ".local/life-blueberry/evaluation":
            self.work_count += 1
            return ast.copy_location(ast.Constant(".local/life-inducer-hillclimb/behavior"), node)
        return node


def _behavior_worker(candidate, raw_output, lock_path, command_dir):
    """Private child entry point; all behavioral code comes from the frozen file."""
    _require(sha(LEGACY) == BEHAVIOR_PINS[_rel(LEGACY)], "Frozen evaluator changed")
    tree = ast.parse(LEGACY.read_text(), filename=str(LEGACY))
    adapter = _LegacyPaths(lock_path)
    tree = ast.fix_missing_locations(adapter.visit(tree))
    _require((adapter.lock_count, adapter.work_count) == (2, 1), "Unexpected evaluator path shape")
    namespace = {"__name__": "frozen_life_behavior", "__file__": str(LEGACY)}
    exec(compile(tree, str(LEGACY), "exec"), namespace)

    class RecordedSubprocess:
        calls = 0

        @classmethod
        def run(cls, argv, **kwargs):
            cls.calls += 1
            record = _command(argv, Path(command_dir) / f"{cls.calls:02d}.json",
                              timeout=kwargs["timeout"], env=kwargs.get("env"))
            if record.get("timed_out"):
                raise subprocess.TimeoutExpired(argv, kwargs["timeout"], record["stdout"], record["stderr"])
            if record.get("error"):
                raise OSError(record["error"])
            return subprocess.CompletedProcess(argv, record["exit"], record["stdout"], record["stderr"])

    namespace["subprocess"] = RecordedSubprocess
    sys.argv = [str(LEGACY), str(candidate), str(raw_output)]
    return namespace["main"]()


def _begin(candidate, outdir, stage):
    candidate, outdir = Path(candidate).resolve(), Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    receipt = outdir / f"{stage}.json"
    _require(not receipt.exists(), f"Preserve existing receipt: {receipt}")
    report = {"schema": "life-hillclimb-gate-v1", "stage": stage,
              "at": dt.datetime.now(dt.timezone.utc).isoformat(), "candidate": _rel(candidate),
              "source_sha256": sha(candidate), "status": "started", "passed": False}
    _write(outdir / f"{stage}-started.json", report)
    return candidate, outdir, receipt, report


def _start_failure(candidate, outdir, stage, error):
    """Return refusal without overwriting a prior receipt or unfinished attempt."""
    return {"schema": "life-hillclimb-gate-v1", "stage": stage, "passed": False,
            "status": "configuration_failure", "candidate": _rel(candidate),
            f"{stage}_receipt": _rel(Path(outdir) / f"{stage}.json"),
            "error": f"Cannot start {stage}; prior evidence is preserved: {type(error).__name__}: {error}"}


def evaluate_behavior(candidate, outdir, unique_id, *, lock=None) -> dict:
    """Run the exact old behavioral gate under a new lock and unique work root."""
    try:
        candidate, outdir, receipt, report = _begin(candidate, outdir, "behavior")
    except Exception as error:
        return _start_failure(candidate, outdir, "behavior", error)
    report["behavior_receipt"] = _rel(receipt)
    report["counts"] = {}
    try:
        _require(isinstance(unique_id, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", unique_id),
                 "unique_id must be a bounded filename token")
        state = _locked(lock, BEHAVIOR_PINS)
        for path, digest in BEHAVIOR_PINS.items():
            _require(state["frozen_files"][path] == digest, "Changed historical behavior pin: " + path)
        report["input_lock_sha256"] = state["lock_sha256"]
        report["legacy_evaluator_sha256"] = sha(LEGACY)
        report["adaptations"] = ["input-lock path (two references)", "ignored work root (one reference)",
                                 "recording subprocess transport; original 60-second command limits"]
        lock_snapshot = outdir / "behavior-input-lock.json"
        data, _ = _lock_data(lock)
        _write(lock_snapshot, data)
        commands = outdir / "behavior-commands"
        commands.mkdir()
        raw_path = outdir / f"behavior-raw-{unique_id}.json"
        _require(not raw_path.exists() and not raw_path.with_suffix(".json.gz").exists(),
                 "Preserve existing raw behavior evidence")
        work = ROOT / ".local/life-inducer-hillclimb/behavior" / raw_path.stem
        _require(not work.exists(), f"Behavior unique_id already used: {unique_id}")
        report["raw_receipt"] = _rel(raw_path)
        command = _command([sys.executable, Path(__file__).resolve(), "_behavior-worker",
                            candidate, raw_path, lock_snapshot, commands],
                           outdir / "behavior-command.json", timeout=480)
        _require(not command.get("timed_out") and not command.get("error"), "Behavior worker unavailable", "evaluation_failure")
        _require(raw_path.exists(), "Behavior worker produced no receipt", "evaluation_failure")
        raw_bytes = raw_path.read_bytes()
        compressed = raw_path.with_suffix(".json.gz")
        with compressed.open("xb") as stream:
            stream.write(gzip.compress(raw_bytes, mtime=0))
        report.update(raw_receipt=_rel(compressed), raw_sha256=sha(compressed),
                      raw_uncompressed_sha256=hashlib.sha256(raw_bytes).hexdigest())
        raw_path.unlink()  # Only the receipt exclusively created by this worker.
        raw = json.loads(raw_bytes)
        failures = {}
        for runtime in ("node", "bun"):
            if runtime not in raw:
                continue
            observation = raw[runtime]
            _require(observation.get("fixture_count") == 1537 and observation.get("composition_count") == 21,
                     f"Changed {runtime} behavioral coverage")
            failed = [row for row in observation["observations"] + observation["composition"] if not row["pass"]]
            failures[runtime] = failed
            report[runtime] = {key: observation[key] for key in
                               ("passed", "runtime", "fixture_count", "composition_count", "milliseconds")}
            report[runtime]["failure_count"] = len(failed)
            report["counts"][runtime] = {"fixtures": observation["fixture_count"],
                                         "composition": observation["composition_count"],
                                         "failure_count": len(failed)}
        if "native" in raw:
            native = raw["native"]
            _require(native.get("fixtures") == 28, "Changed native behavioral coverage")
            mismatches = sum(a != b for a, b in zip(native["actual"], native["expected"]))
            mismatches += abs(len(native["actual"]) - len(native["expected"]))
            report["native"] = {"passed": native["passed"], "fixtures": native["fixtures"],
                                "failure_count": mismatches}
            report["counts"]["native"] = {"fixtures": native["fixtures"], "failure_count": mismatches}
            if not native["passed"]:
                failures["native"] = {"actual": native["actual"], "expected": native["expected"]}
        failure_path = outdir / "behavior-failures.json.gz"
        with failure_path.open("xb") as stream:
            stream.write(gzip.compress((json.dumps(failures, indent=2, allow_nan=False) + "\n").encode(), mtime=0))
        report["failures_receipt"] = _rel(failure_path)
        report["artifacts"] = raw.get("artifacts")
        report["legacy_status"] = raw["status"]
        report["passed"] = bool(raw["passed"])
        if report["passed"]:
            _require(command["exit"] == 0 and all(report.get(k, {}).get("passed") for k in ("node", "bun", "native")),
                     "Incomplete passing behavior receipt")
        else:
            report["error"] = raw.get("error", "Behavior rejected")
        _require(sha(candidate) == report["source_sha256"] == raw["candidate_sha256"], "Source changed during behavior gate")
        _unchanged_lock(lock, state)
        report["status"] = "passed" if report["passed"] else "deterministic_failure"
    except Exception as error:
        report.update(passed=False, status=getattr(error, "status", "evaluation_failure"),
                      error=f"{type(error).__name__}: {error}")
    _write(receipt, report)
    return report


def _json_result(stdout):
    decoder = json.JSONDecoder()
    for position, character in enumerate(stdout):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(stdout[position:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "checked" in value and "units" in value:
            return value
    raise GateError("No structured semantic result", "provider_failure")


def _contexts(rows, source_hash, neutral):
    for row in rows:
        context = row.get("context")
        _require(isinstance(context, dict), "Missing review context")
        _require(context.get("truncated") is False, "Truncated review context", "attention")
        files = context.get("files", [])
        _require(any(file.get("path") == neutral and file.get("source_sha256") == source_hash for file in files),
                 "Review context does not identify the current source")
        for file in files:
            path = (ROOT / file["path"]).resolve()
            _require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == file["source_sha256"],
                     "Changed review context: " + file["path"])


def _semantic_valid(result, usage, source_hash, neutral, model):
    units = result.get("units", [])
    _require(result.get("parser", {}).get("status") == "parsed", "Semantic parser did not cover the source", "attention")
    _require(units, "Zero semantic coverage", "attention")
    _require(len(units) == result["parser"]["declarations"], "Incomplete semantic unit coverage", "provider_failure")
    _require(len({unit["name"] for unit in units}) == len(units), "Duplicate semantic units")
    _require(result.get("checked") == len(units) * len(RULES), "Incomplete semantic rule coverage")
    for unit in units:
        asked = unit.get("asked", [])
        _require(unit.get("checked") == 4 and len(asked) == 4 and {a["rule"] for a in asked} == set(RULES),
                 "Missing semantic rule on " + unit["name"])
        for answer in asked:
            _require(all(isinstance(answer.get(k), (int, float)) and math.isfinite(answer[k]) and 0 <= answer[k] <= 1
                         for k in ("broken", "floor")), "Malformed semantic probability")
    _require(usage.get("provider_requests") == usage.get("provider_responses") and usage["provider_responses"] >= len(units),
             "Incomplete semantic provider coverage", "provider_failure")
    _require(usage.get("models") == [model], "Semantic judge model changed")
    _require(usage.get("status") in ("completed", "findings"), "Semantic usage reports unavailable evidence", "provider_failure")
    _require(usage.get("source_sha256") == source_hash and usage.get("target") == neutral,
             "Semantic usage source mismatch")
    _require(set(usage.get("selected_rules", [])) == set(RULES), "Semantic rule set changed")
    _require(usage.get("checked") == result["checked"], "Semantic usage coverage mismatch")
    _contexts(units, source_hash, neutral)
    findings = [{"name": unit["name"], **answer} for unit in units for answer in unit["asked"]
                if answer["broken"] >= answer["floor"]]
    issues = result.get("issues") or []
    clean = bool(result.get("clean") and not findings and not result.get("broken") and not issues
                 and all(unit.get("clean") and not unit.get("issues") and not unit.get("broken") for unit in units))
    return {"checked": result["checked"], "units": len(units), "clean": clean,
            "findings": findings, "issues": issues, "adjudication": "none" if clean else "unresolved"}


STYLE_AUDIT = r"""
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {assessStyle, diagnoseStyle} from './scripts/perch-style.mjs';
const [path, configPath] = process.argv.slice(1);
const bytes = readFileSync(path);
const report = JSON.parse(path.endsWith('.gz') ? gunzipSync(bytes) : bytes);
const config = JSON.parse(readFileSync(configPath));
const same = (a,b) => JSON.stringify(a) === JSON.stringify(b);
if (config.version !== 3 || report.rubric_version !== 3) throw Error('Current v3 required');
if (!same(report.criticality?.policy, config.criticality)) throw Error('Criticality policy mismatch');
if (!same(report.diagnostics?.targets, config.criticality.diagnostic_targets)) throw Error('Diagnostic targets mismatch');
const assessments = assessStyle(report.rows, config);
const diagnostics = diagnoseStyle(report.rows, config);
if (!same(assessments, report.assessments)) throw Error('Required assessments mismatch');
if (!same(diagnostics, report.diagnostics?.assessments)) throw Error('Diagnostic assessments mismatch');
const byTarget = new Map(assessments.map(a => [a.target, a.criticality_status]));
const criticality = report.criticality?.assessments;
if (!Array.isArray(criticality) || criticality.length !== report.rows.length
 || new Set(criticality.map(a => a.target)).size !== report.rows.length
 || criticality.some(a => byTarget.get(a.target) !== a.status)) throw Error('Criticality coverage mismatch');
const required = assessments.length;
const met = assessments.filter(a => a.status === 'meets_target').length;
const axes = [...new Set(assessments.map(a => a.dimension))].map(dimension => ({dimension,
 required: assessments.filter(a => a.dimension === dimension).length,
 met: assessments.filter(a => a.dimension === dimension && a.status === 'meets_target').length}));
console.log(JSON.stringify({passed: required > 0 && met === required, required, met,
 fraction_met: required ? met / required : 0,
 normalized_shortfall: required ? assessments.reduce((s,a) => s + Math.max(0, (a.minimum_probability - (a.probability_at_target ?? 0)) / a.minimum_probability),0) / required : 1,
 axes, criticality, assessments, diagnostics}));
"""


def _style_valid(style, source_hash, neutral, model):
    _require(style.get("status") == "completed" and not style.get("failure"), "Style provider/evaluation failed", "provider_failure")
    _require(style.get("rubric_version") == 3 and style.get("rubric_sha256") == sha(ROOT / "perch-style.json"),
             "Wrong style rubric identity")
    rows = style.get("rows", [])
    coverage = style.get("coverage", {})
    _require(rows, "Zero style coverage", "attention")
    _require(coverage.get("selected") == coverage.get("ranked") == len(rows)
             and coverage.get("unranked_files") == 0, "Incomplete style coverage")
    _require(len({row["target"] for row in rows}) == len(rows), "Duplicate style targets")
    _require({row["target"] for row in rows} == {target["target"] for target in style.get("targets", [])},
             "Style target inventory mismatch")
    _require(style.get("source_freshness", {}).get("status") == "current"
             and not style["source_freshness"].get("changed_sources"), "Stale style source")
    _require(style.get("provider_requests") == style.get("provider_responses")
             and style["provider_responses"] + style.get("reused_units", 0) == len(rows),
             "Incomplete style provider/reuse coverage", "provider_failure")
    _require(style.get("concurrency") == 2 and 0 <= style.get("provider_peak_in_flight", -1) <= 2,
             "Style concurrency outside bound")
    _require(style.get("incremental_cache") is None and style.get("cached_units", 0) == 0,
             "Unrequested incremental cache use; only explicit previous_style reuse is permitted")
    _require(all(row.get("model") == model and row.get("path") == neutral
                 and row.get("source_sha256") == source_hash for row in rows), "Style model/source mismatch")
    _contexts(rows, source_hash, neutral)


def evaluate_reviews(candidate, outdir, neutral_path, cohort, previous_style=None, *, lock=None) -> dict:
    """One semantic command and one complete v3 style command, with no retries.

    `passed` means review acceptance, not behavioral correctness. Semantic
    findings are returned as unresolved attention; this function never edits code.
    """
    try:
        candidate, outdir, receipt, report = _begin(candidate, outdir, "reviews")
    except Exception as error:
        return {**_start_failure(candidate, outdir, "reviews", error),
                "semantic_receipt": None, "style_receipt": None,
                "semantic_clean": False, "style_passed": False, "provider_failed": False}
    report.update(reviews_receipt=_rel(receipt), semantic_receipt=None, style_receipt=None,
                  semantic_clean=False, style_passed=False, provider_failed=False)
    stage = "preflight"
    guard = None
    try:
        state = _locked(lock, REVIEW_FILES)
        report["input_lock_sha256"] = state["lock_sha256"]
        config = _read(ROOT / "perch-style.json")
        _require(config.get("version") == 3 and config.get("criticality", {}).get("diagnostic_targets"),
                 "The complete current v3 policy is required")
        model = state["judge_model"]
        neutral_path = Path(neutral_path)
        neutral_path = (ROOT / neutral_path).resolve() if not neutral_path.is_absolute() else neutral_path.resolve()
        _require(neutral_path.is_relative_to(ROOT / ".local/life-inducer-hillclimb")
                 and neutral_path.suffix == ".bend", "Neutral source must live under the new ignored experiment root")
        _require(candidate != neutral_path, "Neutral copy must not overwrite the submitted source")
        _require(isinstance(cohort, str) and cohort.strip(), "A common nonempty cohort is required")
        neutral = _rel(neutral_path)
        report["neutral_path"] = neutral
        neutral_path.parent.mkdir(parents=True, exist_ok=True)
        guard = (neutral_path.parent / ".review.lock").open("a+")
        fcntl.flock(guard.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        if previous_style is not None:
            previous_style = Path(previous_style).resolve()
            previous = _read(previous_style)
            _require(previous.get("rubric_version") == 3 and previous.get("rubric_sha256") == sha(ROOT / "perch-style.json"),
                     "Cannot reuse a different rubric")
            old_rows = previous.get("rows") or previous.get("completed_rows") or []
            _require(old_rows and all(row.get("path") == neutral and row.get("model") == model for row in old_rows),
                     "Reuse crosses a neutral path or judge model")
            report["previous_style_sha256"] = sha(previous_style)
        neutral_path.write_bytes(candidate.read_bytes())
        _require(sha(neutral_path) == report["source_sha256"], "Candidate changed before review")
        env = {**os.environ, "PERCH_JOBS": "2", "PERCH_MODEL_ID": model}
        report["judge_model"] = model
        report["provider_concurrency"] = 2
        usage_dir = ROOT / ".perch/usage"
        before = set(usage_dir.glob("*.json"))
        stage = "semantic"
        command = _command(["npm", "run", "lint", "--", neutral, "--rules", ",".join(RULES), "--parallel", "2"],
                           outdir / "semantic-command.json", timeout=180, env=env)
        usages = []
        for path in sorted(set(usage_dir.glob("*.json")) - before):
            usage = _read(path)
            if usage.get("command") == "check" and usage.get("target") == neutral:
                usages.append(usage)
        _write(outdir / "semantic-usage.json", usages)
        _require(all(not usage.get("models") or usage["models"] == [model] for usage in usages),
                 "Semantic judge model changed")
        _require(command["exit"] in (0, 3) and not command.get("timed_out") and not command.get("error"),
                 "Semantic command failed; do not retry automatically", "provider_failure")
        _require(len(usages) == 1, "Expected exactly one matching semantic usage receipt", "provider_failure")
        semantic = _json_result(command["stdout"])
        _write(outdir / "semantic.json", semantic)
        report["semantic_receipt"] = _rel(outdir / "semantic.json")
        summary = _semantic_valid(semantic, usages[0], report["source_sha256"], neutral, model)
        report["semantic"] = summary
        report["semantic_clean"] = summary["clean"]
        _require(sha(candidate) == sha(neutral_path) == report["source_sha256"], "Source changed during semantic review")
        _unchanged_lock(lock, state)

        stage = "style"
        style_path = outdir / "style.json.gz"
        argv = ["npm", "run", "lint:style", "--", "--live", neutral,
                "--cohort=" + cohort, "--jobs=2", "--output=" + str(style_path)]
        if previous_style is not None:
            argv.append("--reuse=" + str(previous_style))
        style_command = _command(argv, outdir / "style-command.json", timeout=180, env=env)
        style = None
        if style_path.exists():
            report["style_receipt"] = _rel(style_path)
            style = _read(style_path)
            observed = style.get("rows", []) + style.get("completed_rows", [])
            _require(all(row.get("model") == model for row in observed), "Style judge model changed")
            _require(not re.search(r"model (?:changed|mismatch)", str(style.get("failure", "")), re.I),
                     "Style judge model changed")
        _require(style_command["exit"] in (0, 3) and not style_command.get("timed_out") and not style_command.get("error"),
                 "Style command failed; do not retry automatically", "provider_failure")
        _require(style_path.exists(), "Style command produced no receipt", "provider_failure")
        _style_valid(style, report["source_sha256"], neutral, model)
        audit_command = _command(["node", "--input-type=module", "-e", STYLE_AUDIT, style_path, ROOT / "perch-style.json"],
                                 outdir / "style-policy-command.json", timeout=30)
        _require(audit_command["exit"] == 0, "Style v3 policy audit failed")
        audit = json.loads(audit_command["stdout"])
        _write(outdir / "style-policy.json", audit)
        _require((style_command["exit"] == 0) == audit["passed"], "Style exit disagrees with full v3 requirements")
        report["style_passed"] = audit["passed"]
        report["style"] = {key: audit[key] for key in
                           ("required", "met", "fraction_met", "normalized_shortfall", "axes", "criticality")}
        report["style_coverage"] = style["coverage"]
        report["style_summary"] = style["style_summary"]
        report["style_provider"] = {key: style[key] for key in
                                    ("provider_requests", "provider_responses", "provider_peak_in_flight", "reused_units")}
        _require(sha(candidate) == sha(neutral_path) == report["source_sha256"], "Source changed during style review")
        _unchanged_lock(lock, state)
        report["passed"] = bool(report["semantic_clean"] and report["style_passed"])
        report["status"] = "passed" if report["passed"] else "attention"
    except Exception as error:
        status = getattr(error, "status", "configuration_failure")
        report.update(passed=False, status=status, failed_stage=stage,
                      provider_failed=status == "provider_failure",
                      error=f"{type(error).__name__}: {error}")
    finally:
        if guard is not None:
            guard.close()
    _write(receipt, report)
    return report


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "_behavior-worker":
        raise SystemExit(_behavior_worker(*map(Path, sys.argv[2:])))
    raise SystemExit("Import evaluate_behavior/evaluate_reviews; there is no automatic paid CLI.")
