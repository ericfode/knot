#!/usr/bin/env python3
"""Read-only R2 receipt audit. JSON goes to stdout; no model or gate is rerun."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import statistics
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PIN = "39bef908c7d7ce572b899c73f3d4f8c04ccedffb"
SETTINGS = (("gpt-6-astra", "low"), ("gpt-5.6-sol", "xhigh"))
RULES = {"bend-machine-arithmetic", "bend-fuel-completeness",
         "perf-growing-prefix-copy", "perf-linked-list-indexing"}
RULE_FLOORS = {"bend-machine-arithmetic": .8, "bend-fuel-completeness": .8,
               "perf-growing-prefix-copy": .7, "perf-linked-list-indexing": .6}
COHORT = ("Pure bounded Conway Life in Bend 2.0.29: dead exterior, synchronous B3/S23, "
          "binary row-major boards of dimensions 0..32, step and exact Nat-count evolution. "
          "Every declaration materially supporting this contract is subject to current Perch policy.")
AXES = ("maximally_big_brain", "delightful_to_read", "highly_memetic", "anticipation", "payoff")
FORBIDDEN = re.compile(r"gpt[- ](?:5|6)|\bAstra\b|\bSol\b|\bBlueberry\b|\bFRV1T\b|\bw[12]-n[1-4]\b|STIMULUS TO READ", re.I)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load(path):
    path = Path(path)
    with (gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz"
          else path.open(encoding="utf-8")) as stream:
        return json.load(stream)


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def equivalent(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-12)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equivalent(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equivalent(x, y) for x, y in zip(a, b))
    return a == b


def stamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def add_usage(target, usage):
    for key, value in (usage or {}).items():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            target[key] = target.get(key, 0) + value


def require(condition, message):
    if not condition:
        raise ValueError(message)


def left_sum(values):
    # JavaScript reduce adds left to right; Python 3.12+ sum uses compensation.
    # Retain the frozen policy's exact boundary decisions, including 0.4 + ulp.
    result = 0.0
    for value in values:
        result += value
    return result


def score(answer, levels):
    probabilities = answer["probabilities"]
    require(set(probabilities) == {str(i) for i in range(levels)}, "incomplete score distribution")
    values = [probabilities[str(i)] for i in range(levels)]
    require(all(type(p) in (int, float) and math.isfinite(p) and 0 <= p <= 1 for p in values), "invalid probability")
    total = left_sum(values)
    require(abs(total - 1) <= .021, "probability mass outside rounding tolerance")
    require(0 <= answer["score"] <= levels - 1 and 0 <= answer["confidence"] <= 1, "invalid score/confidence")
    require(abs(sum(i*p for i, p in enumerate(values))/total - answer["score"]) <= .075,
            "mean disagrees with score distribution")
    return values, total


def style_policy(rows, config):
    """Independent Python reconstruction of the frozen v3 conditional policy."""
    rubrics = {d["id"]: d for d in config["dimensions"] + config["diagnostic_dimensions"]}
    policy = config["criticality"]
    assessments, criticality, diagnostics = [], [], []
    for row in rows:
        context = row["context"]
        truncated = context["truncated"]
        values, total = score(row["answers"][policy["id"]], 2)
        p_critical = values[1]/total
        critical = ("critical" if p_critical >= policy["minimum_probability"] else
                    "noncritical" if not truncated and p_critical <= 1-policy["minimum_probability"] else "uncertain")
        criticality.append(dict(target=row["target"], status=critical, probability_critical=p_critical,
                                context_truncated=truncated))
        strict = critical != "noncritical"
        extras = policy["diagnostic_targets"] if strict else []
        for base in config["style_targets"] + extras:
            raised = strict and row["kind"] != "bend_datatype" and base["dimension"] == policy["style_target"]["dimension"]
            target = policy["style_target"] if raised else base
            unavailable = base in extras and truncated
            if unavailable:
                probability = None
            else:
                values, total = score(row["answers"][target["dimension"]], len(rubrics[target["dimension"]]["levels"]))
                probability = left_sum(values[target["level"]:])/total
            status = ("unavailable" if unavailable else "meets_target" if probability >= target["minimum_probability"]
                      else "below_target" if probability <= 1-target["minimum_probability"] else "uncertain")
            assessments.append(dict(target=row["target"], dimension=target["dimension"], target_level=target["level"],
                minimum_probability=target["minimum_probability"], criticality_status=critical,
                target_basis="criticality" if raised or base in extras else "default", context_truncated=truncated,
                probability_at_target=None if unavailable else probability, status=status))
        for rubric in config["diagnostic_dimensions"]:
            needed = strict and any(t["dimension"] == rubric["id"] for t in policy["diagnostic_targets"])
            meta = dict(target=row["target"], dimension=rubric["id"], required=needed, advisory=not needed,
                        context_truncated=truncated, unresolved_references=len(context.get("unresolved", [])))
            if truncated:
                meta.update(status="unavailable", reason="context_truncated")
            else:
                answer = row["answers"][rubric["id"]]
                score(answer, len(rubric["levels"]))
                meta.update(status="limited_context" if meta["unresolved_references"] else "rated", **answer)
            diagnostics.append(meta)
    axes = []
    for dimension in AXES:
        subset = [a for a in assessments if a["dimension"] == dimension]
        axes.append(dict(dimension=dimension, required=len(subset), met=sum(a["status"] == "meets_target" for a in subset),
                         statuses=dict(Counter(a["status"] for a in subset))))
    met = sum(a["status"] == "meets_target" for a in assessments)
    return dict(assessments=assessments, criticality=criticality, diagnostics=diagnostics, axes=axes,
                required=len(assessments), met=met, passed=bool(assessments) and met == len(assessments),
                fraction=met/len(assessments) if assessments else 0.0,
                shortfall=sum(max(0, 1-(a["probability_at_target"] or 0)/a["minimum_probability"])
                              for a in assessments)/len(assessments) if assessments else 1.0)


# This calls only the pinned parser/context constructors. Network is disabled in
# process, credentials are absent, and historical source is supplied in memory.
# The mutable neutral file is used for realpath identity only, never its bytes.
CONTEXT_AUDIT = r"""
import {readFileSync, realpathSync} from 'node:fs';
import {createHash} from 'node:crypto';
globalThis.fetch = () => { throw Error('Network forbidden in receipt audit'); };
const {analyzeBendSource} = await import('./scripts/perch-bend.mjs');
const {prepareStyleTargets} = await import('./scripts/perch-style.mjs');
const input = JSON.parse(readFileSync(0, 'utf8'));
const root = realpathSync(input.root), config = JSON.parse(readFileSync(root+'/perch-style.json'));
const result = {};
for (const task of input.tasks) {
  try {
    const source = readFileSync(root+'/'+task.source, 'utf8');
    const source_sha256 = createHash('sha256').update(source).digest('hex');
    const analysis = await analyzeBendSource(source);
    if (analysis.parser_status !== 'parsed') throw Error(analysis.parser_status);
    const snapshot = {root, load: async path => {
      if (path !== task.neutral) throw Object.assign(Error('Audit disallows external source context'), {bend_snapshot_io:true, code:'ENOENT'});
      return {source, source_sha256, analysis};
    }};
    const candidates = await prepareStyleTargets([task.neutral], input.cohort, config, root, snapshot);
    result[task.source] = {semantic_names:analysis.declarations.map(d=>d.qualified_name),
      candidates:candidates.map(({state,...metadata})=>metadata)};
  } catch(error) { result[task.source] = {error:String(error.message)}; }
}
console.log(JSON.stringify(result));
"""


class Audit:
    def __init__(self, here=HERE, root=ROOT):
        self.here, self.root = Path(here).resolve(), Path(root).resolve()
        self.errors, self.pending, self.records = [], [], []
        self.thread_ids = set()
        self.contexts = {}
        self.calls = []
        self.results = {}
        self.lock = load(self.here/"input-lock.json")
        self.lock_hash = file_hash(self.here/"input-lock.json")
        self.config = load(self.root/"perch-style.json")
        self.common = (self.here/"inputs/common-packet.md").read_text()
        self.result_paths = set((self.here/"trials").glob("*/result.json"))
        self.completed_round_paths = sorted((self.here/"trials").glob("*/round-*/round.json"))

    def path(self, name):
        path = Path(name)
        path = (self.root/path).resolve() if not path.is_absolute() else path.resolve()
        require(path.is_relative_to(self.root), "receipt path outside repository")
        return path

    def rel(self, path):
        return str(Path(path).resolve().relative_to(self.root))

    def check(self, condition, label, path=None):
        if not condition:
            self.errors.append(dict(check=label, path=self.rel(path) if path else None))
        return condition

    def guarded(self, label, path, function, *args):
        try:
            return function(*args)
        except (OSError, ValueError, TypeError, KeyError, IndexError, ZeroDivisionError, subprocess.SubprocessError) as error:
            self.errors.append(dict(check=label, path=self.rel(path), detail=f"{type(error).__name__}: {error}"))
            return None

    def frozen(self):
        pinned = subprocess.run(["git", "show", PIN+":"+self.rel(self.here/"input-lock.json")],
                                cwd=self.root, capture_output=True, check=True, timeout=15).stdout
        self.check(pinned == (self.here/"input-lock.json").read_bytes(), "lock equals preregistered commit", self.here/"input-lock.json")
        for name, expected in self.lock["frozen_files"].items():
            path = self.path(name)
            self.check(path.is_file() and file_hash(path) == expected, "frozen input hash", path)
        self.check(self.lock["trial_count"] == 30 and self.lock["round_cap"] == 3, "fixed allocation and round cap")
        self.check(self.lock["judge_model"] == "jev-1.13.0" and self.config["version"] == 3, "fixed actual judge and rubric")
        expected = [dict(model=m, effort=e, trials=15) for m, e in SETTINGS]
        self.check(self.lock["author_configurations"] == expected, "15 trials per requested configuration")

    def assignments(self):
        assignments = []
        for wave in range(1, 4):
            path = self.here/f"wave-{wave}-assignments.json"
            if not path.exists():
                self.pending.append(self.rel(path))
                continue
            group = load(path)
            self.check(len(group) == 10, "ten assignments per wave", path)
            candidates = (["original"]+[f"w1-n{i}" for i in range(1, 5)] if wave == 1 else
                          [load(self.here/"wave-1-selection.json")["selected"]]+[f"w2-n{i}" for i in range(1, 5)] if wave == 2 else
                          ["original", load(self.here/"selected-inducer.json")["id"], "original",
                           load(self.here/"selected-inducer.json")["id"], None])
            expected = []
            for index, stimulus in enumerate(candidates):
                text = "" if stimulus is None else (self.here/"stimuli"/(stimulus+".txt")).read_text()
                for offset, (model, effort) in enumerate(SETTINGS):
                    n = (wave-1)*10 + index*2 + offset+1
                    item = dict(id=f"T{n:03d}", slot=f"slot-{n:02d}", wave=wave, stimulus=stimulus,
                                stimulus_sha256=digest(text.encode()), model=model, effort=effort, max_rounds=3)
                    if wave == 3:
                        item["validation_condition"] = ["original", "selected", "original", "selected", "none"][index]
                    expected.append(item)
            random.Random(20260927+wave).shuffle(expected)
            self.check(group == expected, "exact fixed assignments and deterministic schedule", path)
            assignments.extend(group)
        self.check(len({a["id"] for a in assignments}) == len(assignments), "unique trajectory IDs")
        assigned_ids = {a["id"] for a in assignments}
        self.check(all(path.name in assigned_ids for path in (self.here/"trials").glob("T*")), "no unassigned trajectory directories")
        for path in sorted((self.here/"stimuli").glob("*.json")):
            meta, text = load(path), path.with_suffix(".txt").read_bytes()
            self.check(meta["sha256"] == digest(text) and meta["bytes"] == len(text) <= 16384,
                       "stimulus hash and byte cap", path)
            self.check(not re.search(rb"[A-Za-z0-9]", text), "wordless stimulus inventory", path)
            if meta["id"].startswith("w2-"):
                self.check(meta["parent"] == load(self.here/"wave-1-selection.json")["selected"], "mutation ancestry", path)
        return assignments

    def build_contexts(self):
        tasks = []
        for path in self.completed_round_paths:
            report = load(path)
            reviews_path = path.parent/"reviews.json"
            if reviews_path.exists():
                review = load(reviews_path)
                if review.get("neutral_path") and review.get("semantic_receipt"):
                    tasks.append(dict(source=report["source"], neutral=review["neutral_path"]))
        if not tasks:
            return
        env = {k:v for k,v in os.environ.items() if not k.upper().startswith(("TYPESAFE", "PERCH")) and k != "NODE_COMPILE_CACHE"}
        proc = subprocess.run(["node", "--input-type=module", "-e", CONTEXT_AUDIT], cwd=self.root,
                              input=json.dumps(dict(root=str(self.root), cohort=COHORT, tasks=tasks)),
                              capture_output=True, text=True, timeout=55, env=env, check=True)
        self.contexts = json.loads(proc.stdout)

    def prompt(self, trial, history):
        stimulus = "" if trial["stimulus"] is None else (self.here/"stimuli"/(trial["stimulus"]+".txt")).read_text()
        text = ("You are an independent author. Use only this complete packet. No tools.\n\n"
                "--- STIMULUS TO READ BEFORE DESIGN ---\n"+(stimulus or "(No stimulus.)\n")+
                "\n--- COMMON ASSIGNMENT AND REFERENCES ---\n"+self.common)
        for item in history:
            text += "\n--- "+item["role"]+" ---\n"+item["text"]+"\n"
        return text+"\nReturn only the requested JSON object with your complete current implementation.\n"

    def author(self, trial, directory, ident, prompt):
        path = directory/f"{ident}.receipt.json"
        receipt = load(path)
        require(receipt["attempt"] == 1, "more than one transport attempt")
        stem = directory/f"{ident}.attempt-1"
        require(path.read_bytes() == Path(str(stem)+".receipt.json").read_bytes(), "author receipt index differs")
        identity = receipt["identity"]
        require(digest(encoded(identity)) == receipt["identity_sha256"], "author identity hash mismatch")
        for key, suffix in dict(events=".events.jsonl", prompt=".prompt.txt", response=".response.json", schema=".schema.json", stderr=".stderr.txt").items():
            require(file_hash(Path(str(stem)+suffix)) == receipt["artifact_sha256"][key], "author artifact hash mismatch: "+key)
        require(Path(str(stem)+".prompt.txt").read_bytes() == prompt.encode(), "author prompt includes unexpected history or inputs")
        require(identity["prompt_sha256"] == receipt["prompt_sha256"] == digest(prompt.encode()), "prompt identity mismatch")
        require(identity["schema_sha256"] == receipt["schema_sha256"] == file_hash(self.here/"schema.json"), "schema identity mismatch")
        require(identity["transport_sha256"] == self.lock["frozen_files"][self.rel(self.here/"transport.py")], "transport source pin mismatch")
        for m, e in [(identity["model"], identity["reasoning_effort"]), (receipt["model"], receipt["reasoning_effort"]),
                     (receipt["requested_model"], receipt["requested_reasoning_effort"])]:
            require((m, e) == (trial["model"], trial["effort"]) in SETTINGS, "author requested configuration mismatch")
        options = identity["options"]
        require(all(flag in options for flag in ("--ignore-user-config", "--ignore-rules", "--ephemeral", "--skip-git-repo-check", "--json")), "missing isolation flags")
        require(options[options.index("--model")+1] == trial["model"] and f'model_reasoning_effort="{trial["effort"]}"' in options, "CLI configuration mismatch")
        require("project_doc_max_bytes=0" in options and 'web_search="disabled"' in options and "read-only" in options, "isolation policy mismatch")
        disabled = {options[i+1] for i,x in enumerate(options[:-1]) if x == "--disable"}
        require({"apps", "plugins", "shell_tool", "code_mode_host", "browser_use", "computer_use", "memories"} <= disabled, "tool/memory features enabled")
        command = receipt["command"]
        require(command[0] == identity["cli_executable"] and len(command) == len(options)+1, "recorded CLI command differs from identity")
        substitutions = {"<SCHEMA_SNAPSHOT>": str(stem)+".schema.json", "<ATTEMPT_RESPONSE>": str(stem)+".response.json"}
        for expected, actual in zip(options, command[1:]):
            if expected == "<EMPTY_TEMP_DIRECTORY>":
                require(Path(actual).name.startswith("life-inducer-empty-") and not Path(actual).is_relative_to(self.root), "author working directory is not isolated")
            else:
                require(actual == substitutions.get(expected, expected), "recorded CLI option differs from identity")
        raw = Path(str(stem)+".response.json").read_bytes()
        require(digest(raw) == receipt["response_sha256"] and raw == (directory/f"{ident}.json").read_bytes(), "response hash/alias mismatch")
        response = json.loads(raw)
        require(set(response) == {"source", "hypothesis", "findings"} and all(isinstance(v, str) for v in response.values()), "author JSON schema violation")
        events = [json.loads(line) for line in Path(str(stem)+".events.jsonl").read_text().splitlines() if line.strip()]
        require(all(e.get("type") in {"thread.started", "turn.started", "turn.completed", "turn.failed", "error",
                    "item.started", "item.updated", "item.completed"} for e in events), "unrecognized author lifecycle event")
        tools = [e for e in events if e.get("type", "").startswith("item.") and e.get("item", {}).get("type") not in ("agent_message", "reasoning", "error")]
        require(not tools and receipt["tool_events"] == 0 and not receipt["tool_event_details"], "tool event in author context")
        require(not any(e.get("type") in ("error", "turn.failed") for e in events), "failed author event")
        completed = [e for e in events if e.get("type") == "turn.completed"]
        threads = [e["thread_id"] for e in events if e.get("type") == "thread.started"]
        require(len(completed) == len(threads) == 1 and threads[0] == receipt["thread_id"], "fresh thread/turn evidence missing")
        require(threads[0] not in self.thread_ids, "author thread reused across calls")
        self.thread_ids.add(threads[0])
        require(completed[0]["usage"] == receipt["usage"], "token usage differs from events")
        final = [e["item"]["text"] for e in events if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "agent_message"]
        require(final and json.loads(final[-1]) == response, "final agent message differs from response")
        models = sorted({e["model"] for e in events if e.get("type") in ("thread.started", "turn.started", "turn.completed") and isinstance(e.get("model"), str)})
        efforts = sorted({e[k] for e in events if e.get("type") in ("thread.started", "turn.started", "turn.completed")
                          for k in ("reasoning_effort", "model_reasoning_effort") if isinstance(e.get(k), str)})
        require(models == receipt["reported_models"] and efforts == receipt["reported_reasoning_efforts"], "resolved settings receipt mismatch")
        require(not models or models == [trial["model"]], "reported model mismatch")
        require(not efforts or efforts == [trial["effort"]], "reported effort mismatch")
        require(receipt["model_validation"] == ("matched_reported" if models else "requested_only_not_reported"), "requested/resolved model conflation")
        require(receipt["effort_validation"] == ("matched_reported" if efforts else "requested_only_not_reported"), "requested/resolved effort conflation")
        require(receipt["status"] == "completed" and receipt["exit_code"] == 0 and receipt["schema_validation"] == receipt["final_message_validation"] == "passed", "transport did not complete")
        self.calls.append(dict(trial=trial["id"], round=int(directory.name[-2:]), kind=ident, model=trial["model"], effort=trial["effort"],
            requested_model=receipt["requested_model"], reported_models=models, reported_efforts=efforts, cli_version=identity["cli_version"],
            seconds=receipt["wall_seconds_including_cli_startup"], usage=receipt["usage"], started_at=receipt["started_at"], finished_at=receipt["finished_at"]))
        return response

    def behavior(self, directory, source_hash):
        report = load(directory/"behavior.json")
        require(report["source_sha256"] == source_hash and report["input_lock_sha256"] == self.lock_hash, "behavior source/lock mismatch")
        raw_path = self.path(report["raw_receipt"])
        require(raw_path.parent == directory and raw_path.suffix == ".gz", "raw behavior receipt escapes round")
        require(file_hash(raw_path) == report["raw_sha256"], "compressed behavior hash mismatch")
        raw_bytes = gzip.decompress(raw_path.read_bytes())
        require(digest(raw_bytes) == report["raw_uncompressed_sha256"], "decompressed behavior hash mismatch")
        raw = json.loads(raw_bytes)
        require(raw["candidate_sha256"] == source_hash, "raw behavior candidate mismatch")
        require(load(directory/"behavior-input-lock.json") == self.lock, "behavior lock snapshot mismatch")
        require(raw["preregistration_sha256"] == file_hash(directory/"behavior-input-lock.json"), "raw behavior lock identity mismatch")
        counts, successes = {}, []
        for runtime in ("node", "bun"):
            if runtime not in raw:
                successes.append(False)
                continue
            observation = raw[runtime]
            fixtures, composition = observation["observations"], observation["composition"]
            require(observation["fixture_count"] == len(fixtures) == len({r["id"] for r in fixtures}) == 1537, runtime+" fixture coverage mismatch")
            require(observation["composition_count"] == len(composition) == len({r["id"] for r in composition}) == 21, runtime+" composition coverage mismatch")
            require(all(type(row["pass"]) is bool for row in fixtures+composition), "nonboolean behavior observation")
            failures = sum(not row["pass"] for row in fixtures+composition)
            passed = failures == 0
            require(observation["passed"] == passed, runtime+" aggregate pass mismatch")
            counts[runtime] = dict(fixtures=1537, composition=21, failure_count=failures)
            successes.append(passed)
        if "native" in raw:
            native = raw["native"]
            require(native["fixtures"] == len(native["expected"]) == 28, "native fixture count mismatch")
            failures = sum(a != b for a,b in zip(native["actual"], native["expected"])) + abs(len(native["actual"])-len(native["expected"]))
            require(native["passed"] == (failures == 0), "native aggregate pass mismatch")
            counts["native"] = dict(fixtures=28, failure_count=failures)
            successes.append(failures == 0)
        else:
            successes.append(False)
        require(counts == report["counts"], "summarized behavior counts differ from raw observations")
        passed = all(successes)
        require(report["passed"] == raw["passed"] == passed, "behavior acceptance differs from observations")
        command = load(directory/"behavior-command.json")
        if passed:
            require(command["exit"] == 0 and report["status"] == "passed", "passing behavior command failed")
        return dict(passed=passed, counts=counts, seconds=command["seconds"], raw_sha256=report["raw_sha256"])

    def reviews(self, directory, report, trial, previous_style):
        review = load(directory/"reviews.json")
        source_hash, source = report["source_sha256"], report["source"]
        neutral = f'.local/life-inducer-hillclimb-r2/review/{trial["slot"]}/life.bend'
        require(review["source_sha256"] == source_hash and review["input_lock_sha256"] == self.lock_hash, "review source/lock mismatch")
        require(review["neutral_path"] == neutral and review["judge_model"] == "jev-1.13.0", "review neutral path/judge mismatch")
        built = self.contexts[source]
        require(not built.get("error"), "historical context reconstruction failed: "+str(built.get("error")))
        source_bytes = self.path(source).read_bytes()
        require(not FORBIDDEN.search(source_bytes.decode()), "exposure/model label found in judged source")
        if trial["stimulus"]:
            stimulus = (self.here/"stimuli"/(trial["stimulus"]+".txt")).read_bytes().strip()
            require(stimulus not in source_bytes, "whole inducer found in judged source")
        semantic = load(directory/"semantic.json")
        usage_list = load(directory/"semantic-usage.json")
        require(len(usage_list) == 1, "semantic usage receipt count mismatch")
        usage = usage_list[0]
        units = semantic["units"]
        require(semantic["parser"]["status"] == "parsed" and len(units) == semantic["parser"]["declarations"] > 0, "semantic parser coverage missing")
        require({u["name"] for u in units} == set(built["semantic_names"]) and len(units) == len(built["semantic_names"]), "semantic declaration inventory differs from reparsed source")
        require(semantic["checked"] == 4*len(units) == usage["checked"], "semantic total coverage mismatch")
        require(usage["models"] == ["jev-1.13.0"] and usage["resolved_model"] == "jev-1.13.0" and usage["model_resolution"] == "provider-responses-this-run", "actual semantic judge unverified")
        require(usage["source_sha256"] == source_hash and usage["target"] == neutral and set(usage["selected_rules"]) == RULES, "semantic identity mismatch")
        require(usage["provider_requests"] == usage["provider_responses"] >= len(units), "semantic provider coverage incomplete")
        candidates = {c["target"]: c for c in built["candidates"]}
        findings = 0
        for unit in units:
            require(unit["path"] == neutral and unit["checked"] == len(unit["asked"]) == 4 and {a["rule"] for a in unit["asked"]} == RULES, "semantic unit rule coverage mismatch")
            require(unit["context"] == candidates[neutral+"::"+unit["name"]]["context"], "semantic helper context differs from snapshot")
            for answer in unit["asked"]:
                require(all(type(answer[k]) in (int, float) and math.isfinite(answer[k]) and 0 <= answer[k] <= 1 for k in ("broken", "floor")), "invalid semantic probability")
                require(answer["floor"] == RULE_FLOORS[answer["rule"]], "semantic finding threshold changed")
                findings += answer["broken"] >= answer["floor"]
        clean = bool(not findings and not semantic.get("issues") and not semantic.get("broken") and semantic.get("clean") and
                     all(u.get("clean") and not u.get("issues") and not u.get("broken") for u in units))
        require(review["semantic_clean"] == clean, "semantic acceptance differs from findings")
        require(usage["status"] in ("completed", "findings"), "semantic status unavailable")
        style = load(directory/"style.json.gz")
        rows = style["rows"]
        require(style["status"] == "completed" and not style.get("failure") and style["rubric_version"] == 3,
                "style receipt unavailable or wrong version")
        require(style["rubric_sha256"] == file_hash(self.root/"perch-style.json") and style["criticality"]["policy"] == self.config["criticality"], "style rubric/policy mismatch")
        require(style["style_targets"] == self.config["style_targets"] and style["diagnostics"]["targets"] == self.config["criticality"]["diagnostic_targets"], "published style thresholds changed")
        require(style["cohort"] == COHORT and style["mode"] == "targets", "judge contract changed")
        require(style["coverage"] == dict(selected=len(rows), ranked=len(rows), unranked_files=0) and rows, "style coverage incomplete")
        require(len(rows) == len(candidates) and {r["target"] for r in rows} == set(candidates), "whole-file style inventory differs from parsed source")
        require(style["targets"] == built["candidates"], "style target/state metadata differs from reconstructed judge inputs")
        require(style["requested_model"] == "jev-1.13.0" and style["model_resolution"]["resolved_models"] == ["jev-1.13.0"], "actual style judge unverified")
        require(style["provider_requests"] == style["provider_responses"] and style["provider_responses"]+style["reused_units"] == len(rows), "style provider/reuse coverage incomplete")
        require(style["incremental_cache"] is None and style.get("cached_units", 0) == 0, "unexpected incremental cache")
        require(style["concurrency"] == 2 and 0 <= style["provider_peak_in_flight"] <= 2, "style worker bound changed")
        require(style["source_freshness"] == dict(status="current", changed_sources=[]), "style source was stale")
        old_rows = {}
        if previous_style:
            previous = load(previous_style)
            require(review["previous_style_sha256"] == file_hash(previous_style), "previous style hash mismatch")
            require(self.path(style["reused_from"]) == previous_style, "reuse crosses trajectory or skips predecessor")
            old_rows = {r["target"]:r for r in previous["rows"]}
        else:
            require(style["reused_from"] is None, "unexpected first-round reuse")
        # Start with this semantic invocation exactly once. Reused style rows
        # retain old usage in their receipts, so only fresh rows are added below.
        reused, judge_tokens = 0, dict(usage.get("usage", {}))
        truncated_targets = []
        for row in rows:
            require(row["model"] == "jev-1.13.0" and row["path"] == neutral and row["source_sha256"] == source_hash, "style row model/source mismatch")
            expected = candidates[row["target"]]
            require(all(row[k] == expected[k] for k in expected), "style row context/state mismatch")
            require(row["context"]["files"] == [dict(path=neutral, source_sha256=source_hash)], "unexpected judge input files")
            if row["context"]["truncated"]:
                truncated_targets.append(row["target"])
            old = old_rows.get(row["target"])
            if old and all(old[k] == row[k] for k in ("kind", "state_sha256", "source_sha256", "context")):
                require(old == row, "reused answer was changed")
                reused += 1
            else:
                add_usage(judge_tokens, row.get("usage"))
        require(reused == style["reused_units"], "style reuse accounting mismatch")
        policy = style_policy(rows, self.config)
        for key in ("assessments",):
            require(equivalent(policy[key], style[key]), "v3 required assessments disagree")
        require(equivalent(policy["criticality"], style["criticality"]["assessments"]), "criticality assessments disagree")
        require(equivalent(policy["diagnostics"], style["diagnostics"]["assessments"]), "diagnostic assessments disagree")
        style_passed = bool(policy["passed"] and not truncated_targets)
        if truncated_targets:
            require(review["status"] == "attention" and review.get("failed_stage") == "style"
                    and review.get("error") == "GateError: Truncated review context", "truncated context lacks explicit gate rejection")
            require(not (directory/"style-policy.json").exists() and not (directory/"style-policy-command.json").exists(),
                    "truncated context unexpectedly reached policy gate")
        else:
            saved = load(directory/"style-policy.json")
            for key in ("passed", "required", "met", "assessments", "criticality", "diagnostics"):
                require(equivalent(saved[key], policy[key]), "saved policy differs: "+key)
            require(equivalent(saved["fraction_met"], policy["fraction"]) and equivalent(saved["normalized_shortfall"], policy["shortfall"]), "saved partial metrics disagree")
        require(review["style_passed"] == style_passed and review["passed"] == (clean and style_passed), "review acceptance mismatch")
        seconds = 0
        commands = ("semantic-command", "style-command") if truncated_targets else ("semantic-command", "style-command", "style-policy-command")
        for name in commands:
            command = load(directory/(name+".json"))
            require(command["exit"] in ((0,) if name == "style-policy-command" else (0, 3)), "review command unavailable")
            seconds += command["seconds"]
            if name == "style-command":
                require(neutral in command["argv"] and "--cohort="+COHORT in command["argv"] and "--jobs=2" in command["argv"], "style command context changed")
                require((command["exit"] == 0) == policy["passed"], "style exit disagrees with recomputed policy")
        return dict(semantic_clean=clean, semantic_checks=semantic["checked"], semantic_findings=findings,
                    style_passed=style_passed, style_context_complete=not truncated_targets, truncated_targets=truncated_targets,
                    fraction=policy["fraction"], shortfall=policy["shortfall"],
                    axes=policy["axes"], criticality=dict(Counter(c["status"] for c in policy["criticality"])),
                    judge_usage=judge_tokens, seconds=seconds, required=policy["required"], met=policy["met"],
                    judge_model="jev-1.13.0", style_sha256=file_hash(directory/"style.json.gz"))

    def trial(self, trial):
        directory = self.here/"trials"/trial["id"]
        if not directory.exists():
            return dict(**trial, status="not_started", terminal=False, rounds=[], calls=[])
        require(load(directory/"assignment.json") == trial, "trial assignment differs from wave")
        round_directories = sorted(path for path in directory.glob("round-*") if path.is_dir())
        require(all(path.name in ("round-01", "round-02", "round-03") for path in round_directories), "unexpected round directory outside budget")
        history, audited, previous_style, seen = [], [], None, set()
        completed = [p for p in self.completed_round_paths if p.parent.parent == directory]
        require([int(p.parent.name[-2:]) for p in completed] == list(range(1, len(completed)+1)), "round gap")
        require(len(completed) <= 3, "round budget exceeded")
        for path in completed:
            report, number = load(path), int(path.parent.name[-2:])
            rd = path.parent
            history.append(dict(role="ROUND REQUEST", text=f"Round {number} of at most 3. "+
                ("Write your initial implementation." if number == 1 else "Read your own prior feedback, state a concrete improvement hypothesis, then revise. Do not reroll unchanged code.")))
            first = self.author(trial, rd, "author", self.prompt(trial, history))
            history.append(dict(role="YOUR PREVIOUS RESPONSE", text=json.dumps(first, ensure_ascii=False)))
            require((rd/"first.bend.snapshot").read_bytes() == first["source"].encode(), "first source snapshot differs from response")
            compiler = load(rd/"compiler-first.json")
            compiler_seconds = compiler["seconds"]
            require(report["compiler_first_passed"] == (compiler["exit"] == 0), "first compiler outcome mismatch")
            submitted = rd/"first.bend.snapshot"
            repaired = compiler["exit"] != 0
            if repaired:
                history.append(dict(role="COMPILER DIAGNOSTIC REPAIR", text=
                    "The first source was rejected. One repair is allowed based only on this complete diagnostic. Preserve your intended algorithm and contract.\n"+compiler["stdout"]+"\n"+compiler["stderr"]))
                response = self.author(trial, rd, "repair", self.prompt(trial, history))
                history.append(dict(role="YOUR PREVIOUS RESPONSE", text=json.dumps(response, ensure_ascii=False)))
                submitted = rd/"repaired.bend.snapshot"
                require(submitted.read_bytes() == response["source"].encode(), "repaired snapshot differs from response")
                compiler = load(rd/"compiler-repaired.json")
                compiler_seconds += compiler["seconds"]
            require(report["compiler_repair"] == repaired, "compiler repair count mismatch")
            require(len(list(rd.glob("*.attempt-*.receipt.json"))) == 1+repaired, "unexpected author attempts")
            source_hash = file_hash(submitted)
            require(report["source_sha256"] == source_hash and self.path(report["source"]) == submitted, "submitted source hash/path mismatch")
            repeated = source_hash in seen
            if compiler["exit"] == 0:
                seen.add(source_hash)
            behavior, review = None, None
            if (rd/"behavior.json").exists():
                require(compiler["exit"] == 0 and not repeated, "behavior rerun on rejected/unchanged source")
                behavior = self.behavior(rd, source_hash)
            if (rd/"reviews.json").exists():
                require(behavior and behavior["passed"], "review ran before behavior acceptance")
                review = self.reviews(rd, report, trial, previous_style)
                previous_style = rd/"style.json.gz"
            behavior_passed = bool(behavior and behavior["passed"])
            semantic_clean = bool(review and review["semantic_clean"])
            full_pass = bool(behavior_passed and semantic_clean and review["style_passed"])
            require(report["behavior_passed"] == behavior_passed and report["semantic_clean"] == semantic_clean and report["full_pass"] == full_pass, "round acceptance differs from raw evidence")
            fraction, shortfall = (review["fraction"], review["shortfall"]) if review else (0.0, 1.0)
            require(equivalent(report["metrics"]["fraction"], fraction) and equivalent(report["metrics"]["shortfall"], shortfall), "round selection metrics differ")
            audited.append(dict(number=number, source=report["source"], source_sha256=source_hash,
                first_source_sha256=file_hash(rd/"first.bend.snapshot"), repaired_source_sha256=source_hash if repaired else None,
                compiler_first_passed=report["compiler_first_passed"], compiler_repair=repaired, compiler_passed=compiler["exit"] == 0,
                compiler_seconds=compiler_seconds, behavior_passed=behavior_passed, semantic_clean=semantic_clean, full_pass=full_pass,
                status=report["status"], fraction=fraction, shortfall=shortfall, behavior=behavior, review=review))
            history.append(dict(role="YOUR ROUND FEEDBACK", text=json.dumps(load(rd/"feedback.json"), ensure_ascii=False)))
            require(not full_pass or path == completed[-1], "continued after first full pass")
        result_path = directory/"result.json"
        terminal = result_path in self.result_paths
        result = load(result_path) if terminal else None
        calls = [c for c in self.calls if c["trial"] == trial["id"]]
        record = dict(**trial, terminal=terminal, status=result["status"] if result else "running", rounds=audited, calls=calls)
        if terminal:
            if result["status"] in ("passed", "completed_no_full_pass"):
                require(len(round_directories) == len(completed), "terminal trajectory retains an extra unfinished round")
            require(result["rounds"] == [load(p) for p in completed], "trial round index differs from receipts")
            require(all(result[k] == v for k,v in trial.items()), "result assignment differs")
            passes = [r for r in audited if r["full_pass"]]
            require(result["full_pass"] == bool(passes) and result["rounds_to_pass"] == (passes[0]["number"] if passes else None), "trial pass/rounds mismatch")
            if result["status"] == "completed_no_full_pass":
                require(len(audited) == 3 and not passes, "budget exhaustion incorrectly reported")
            if result["status"] == "passed":
                require(passes and len(audited) == passes[0]["number"], "first-pass stopping rule violated")
            eligible = [r for r in audited if r["behavior_passed"] and r["semantic_clean"]]
            require(result["eligible"] == bool(eligible), "trial eligibility mismatch")
            selected = max(eligible, key=lambda r:(r["full_pass"], r["fraction"], -r["shortfall"], -r["number"])) if eligible else None
            if selected:
                require(result["selected_round"] == selected["number"] and result["selected_source"] == selected["source"], "best eligible round mismatch")
            require(equivalent(result["metrics"]["fraction"], selected["fraction"] if selected else 0.0) and
                    equivalent(result["metrics"]["shortfall"], selected["shortfall"] if selected else 1.0), "trial partial metrics mismatch")
            elapsed = (datetime.fromisoformat(result["finished_at"])-datetime.fromisoformat(
                load(directory/"round-01/author.receipt.json")["started_at"])).total_seconds()
            require(equivalent(elapsed, result["elapsed_seconds_including_interruptions"]), "trajectory elapsed time mismatch")
            record.update(full_pass=bool(passes), rounds_to_pass=passes[0]["number"] if passes else None,
                censored_at_round_3=result["status"] == "completed_no_full_pass", selection_failure_penalty=4 if not passes else passes[0]["number"],
                selected_round=selected["number"] if selected else None, elapsed_seconds_including_interruptions=elapsed,
                invocation_wall_seconds_including_replay=result["invocation_wall_seconds_including_replay"])
            self.results[trial["id"]] = result
        else:
            record.update(full_pass=any(r["full_pass"] for r in audited), rounds_to_pass=None, censored_at_round_3=False)
        return record

    def selections(self):
        incumbent = "original"
        for wave in (1, 2):
            path = self.here/f"wave-{wave}-selection.json"
            if not path.exists():
                self.pending.append(self.rel(path))
                continue
            saved, published = load(path), load(self.here/f"wave-{wave}-results.json")
            require(published == sorted([r for r in self.results.values() if r["wave"] == wave], key=lambda r:r["id"]), "wave results differ from trial receipts")
            ranking = []
            for stimulus in [incumbent]+[f"w{wave}-n{i}" for i in range(1, 5)]:
                pair = [r for r in published if r["stimulus"] == stimulus]
                require(len(pair) == 2 and {(r["model"],r["effort"]) for r in pair} == set(SETTINGS), "selection pair incomplete")
                objective = [sum(r["full_pass"] for r in pair), sum(r["eligible"] for r in pair),
                             -sum(r["rounds_to_pass"] or 4 for r in pair), sum(r["metrics"]["fraction"] for r in pair)/2,
                             -sum(r["metrics"]["shortfall"] for r in pair)/2, -len((self.here/"stimuli"/(stimulus+".txt")).read_bytes())]
                ranking.append(dict(stimulus=stimulus, objective=objective, trials=[r["id"] for r in pair]))
            ranking.sort(key=lambda r:(r["objective"], r["stimulus"] == incumbent), reverse=True)
            require(equivalent(saved["ranking"], ranking) and saved["selected"] == ranking[0]["stimulus"] and saved["incumbent"] == incumbent,
                    "selection differs from preregistered lexicographic objective")
            require(saved["improved"] == (saved["selected"] != incumbent), "selection change label mismatch")
            incumbent = saved["selected"]
        frozen = self.here/"selected-inducer.json"
        if not frozen.exists():
            self.pending.append(self.rel(frozen))
            return None
        selected = load(frozen)
        require(selected == dict(id=incumbent, sha256=file_hash(self.here/"stimuli"/(incumbent+".txt")),
                                 frozen_before_validation=True, selection_waves=[1, 2]), "holdout selection identity mismatch")
        progress = [json.loads(line) for line in (self.here/"progress.jsonl").read_text().splitlines() if line.strip()]
        selections = [(i,p) for i,p in enumerate(progress) if p.get("event") == "selected" and p.get("wave") == 2]
        require(selections, "no pre-holdout selection event")
        selected_index, selected_event = selections[0]
        require(selected_event["selected"] == selected["id"], "selection event differs from frozen winner")
        runner = self.here/"run.py"
        runner_hash = file_hash(runner)
        require(runner_hash == self.lock["frozen_files"][self.rel(runner)], "freeze sequencing runner differs from preregistered source")
        # The pinned main() writes selected-inducer.json after select(2, ...) and
        # before assignments(3, ...) and wave_run(3, ...). Events bind that
        # immutable source sequence to the observed run; filesystem times do not.
        starts = [(i,p) for i,p in enumerate(progress) if p.get("event") == "trial_started" and p.get("wave") == 3]
        for index, start in starts:
            require(index > selected_index and stamp(start["at"]) >= stamp(selected_event["at"]), "holdout started before selection event")
        reservations = sorted((self.here/"trials").glob("T0[23]*/round-01/author.attempt-1.reservation.json"))
        author_starts = []
        for path in reservations:
            if int(path.parent.parent.name[1:]) >= 21:
                at = stamp(load(path)["started_at"])
                require(at >= stamp(selected_event["at"]), "holdout author receipt predates selection event")
                require(any(event["id"] == path.parent.parent.name for _, event in starts), "holdout author lacks ordered trial-start event")
                author_starts.append(at)
        try:
            mtime = frozen.stat().st_mtime
            corroboration = dict(observed_utc=datetime.fromtimestamp(mtime, timezone.utc).isoformat(),
                precedes_all_observed_author_starts=all(mtime <= at+.001 for at in author_starts) if author_starts else None,
                affects_acceptance=False, portable=False,
                note="Corroboration only. Git checkout or archival restoration can reset filesystem mtime.")
        except OSError:
            corroboration = dict(available=False, affects_acceptance=False, portable=False)
        return dict(**selected, observed_selection_event=selected_event["at"], holdout_started=len(starts),
                    runner_sequencing_sha256=runner_hash, selection_file_mtime=corroboration,
                    freeze_evidence="immutable selection contents, ordered selected/trial_started events, author receipt times and pinned runner sequencing; not external timestamp attestation")

    def run(self):
        self.guarded("frozen inputs", self.here/"input-lock.json", self.frozen)
        assignments = self.guarded("assignment allocation", self.here, self.assignments) or []
        if not self.errors:
            self.guarded("historical judge context reconstruction", self.here, self.build_contexts)
        for trial in assignments:
            record = self.guarded("trajectory receipt audit", self.here/"trials"/trial["id"], self.trial, trial)
            if record:
                self.records.append(record)
        selected = self.guarded("selection and holdout freeze", self.here, self.selections)
        final_path = self.here/"results.json"
        complete = len(assignments) == len(self.results) == 30 and final_path.exists()
        if complete:
            final = load(final_path)
            self.check(final["status"] == "completed" and final["trials"] == 30, "final completion count", final_path)
            self.check({r["id"] for r in final["results"]} == set(self.results) and all(r == self.results[r["id"]] for r in final["results"]), "final result index matches receipts", final_path)
            self.check(final["full_passes"] == sum(r["full_pass"] for r in self.results.values()), "final full-pass count", final_path)
            self.check(selected is not None and final["selected_inducer"] == selected["id"], "final selected-inducer identity", final_path)
            self.check(all(sum(a["model"] == m and a["effort"] == e for a in assignments) == 15 for m,e in SETTINGS), "final 15/15 split")
            self.check(all(r["status"] in ("passed", "completed_no_full_pass") for r in self.results.values()), "no unavailable trajectory counted complete")
        else:
            self.pending.append("30 terminal audited trajectories and results.json")
        groups = defaultdict(list)
        for record in self.records:
            stage = "held_out" if record["wave"] == 3 else "adaptive_search"
            condition = record.get("validation_condition", record["stimulus"] or "none")
            groups[(stage, record["model"], record["effort"], condition)].append(record)
            groups[(stage, record["model"], record["effort"], "ALL_WITHIN_STAGE")].append(record)
        summaries = [dict(stage=k[0], model=k[1], effort=k[2], condition=k[3], **summarize(v)) for k,v in sorted(groups.items())]
        return dict(schema="life-inducer-r2-independent-audit/v1", at=datetime.now(timezone.utc).isoformat(),
            audit_source_sha256=file_hash(Path(__file__)), pinned_commit=PIN, input_lock_sha256=self.lock_hash,
            frozen_files=len(self.lock["frozen_files"]), audit_status="invalid" if self.errors else "complete" if complete else "partial",
            complete=complete, available_evidence_passed=not self.errors, final_audit_passed=complete and not self.errors,
            assignments_observed=len(assignments), expected_assignments=30, assignments_by_configuration=dict(Counter(a["model"]+"/"+a["effort"] for a in assignments)),
            terminal_trajectories=len(self.results), observed_full_passes=sum(r["full_pass"] for r in self.results.values()),
            pending=self.pending, errors=self.errors, selected_inducer=selected,
            author_configuration_evidence=dict(calls=len(self.calls), reported_model_calls=sum(bool(c["reported_models"]) for c in self.calls),
                requested_only_calls=sum(not c["reported_models"] for c in self.calls), cli_versions=sorted({c["cli_version"] for c in self.calls}),
                note="Requested author models are recorded CLI arguments. Absent resolved-model fields do not establish server model identity."),
            statistics=summaries, trajectories=self.records,
            limits=["Read-only observation during a live run is not an atomic snapshot; only finalized round/result receipts in the initial census are audited.",
                    "Unfinished current-round calls are outside completed-round statistics; partial totals are lower bounds.",
                    "No provider request, compiler run, or behavior fixture is rerun. Current pinned parser/context constructors reconstruct historical judge inputs in memory.",
                    "Adaptive-search scores are selection evidence, not causal effect estimates. Held-out conditions are reported separately.",
                    "Failure is right-censored at round 3 for descriptive trial statistics; the preregistered selection penalty is 4.",
                    "Author billed cost is unavailable. Token fields overlap: reasoning output is a subset of output, cached input a subset of input.",
                    "Behavior gates establish the fixed tested cases, not universal correctness or GPU performance."])


def summarize(records):
    rounds = [r for trial in records for r in trial["rounds"]]
    calls = [call for trial in records for call in trial["calls"]]
    author_usage, judge_usage = {}, {}
    for call in calls:
        add_usage(author_usage, call["usage"])
    reviews = [r["review"] for r in rounds if r["review"]]
    for review in reviews:
        add_usage(judge_usage, review["judge_usage"])
    times = [r["elapsed_seconds_including_interruptions"] for r in records if "elapsed_seconds_including_interruptions" in r]
    axes = {axis:dict(required=0, met=0, statuses=Counter()) for axis in AXES}
    criticality = Counter()
    for review in reviews:
        criticality.update(review["criticality"])
        for axis in review["axes"]:
            acc = axes[axis["dimension"]]
            acc["required"] += axis["required"]
            acc["met"] += axis["met"]
            acc["statuses"].update(axis["statuses"])
    return dict(assigned=len(records), terminal=sum(r["terminal"] for r in records), statuses=dict(Counter(r["status"] for r in records)),
        full_passes=sum(r.get("full_pass", False) for r in records), right_censored_at_round_3=sum(r.get("censored_at_round_3", False) for r in records),
        first_round_full_passes=sum(r.get("rounds_to_pass") == 1 for r in records),
        first_round_full_passes_without_compiler_repair=sum(r.get("rounds_to_pass") == 1 and not r["rounds"][0]["compiler_repair"] for r in records),
        rounds_to_pass_successes=[r["rounds_to_pass"] for r in records if r.get("rounds_to_pass")],
        completed_rounds=len(rounds), rounds_observed_histogram=dict(Counter(len(r["rounds"]) for r in records)),
        compiler_first_passes=sum(r["compiler_first_passed"] for r in rounds), compiler_repair_calls=sum(r["compiler_repair"] for r in rounds),
        compiler_after_repair_passes=sum(r["compiler_repair"] and r["compiler_passed"] for r in rounds),
        behavior_passes=sum(r["behavior_passed"] for r in rounds), semantic_clean_rounds=sum(r["semantic_clean"] for r in rounds),
        per_axis_across_reviewed_rounds=axes, criticality_across_reviewed_rounds=dict(criticality),
        author_calls=len(calls), author_usage=author_usage, judge_usage_current_responses=judge_usage,
        author_seconds=sum(c["seconds"] for c in calls), compiler_seconds=sum(r["compiler_seconds"] for r in rounds),
        behavior_command_seconds=sum(r["behavior"]["seconds"] for r in rounds if r["behavior"]),
        review_command_seconds=sum(r["seconds"] for r in reviews),
        terminal_elapsed_seconds=dict(count=len(times), total=sum(times), mean=statistics.mean(times) if times else None,
                                      median=statistics.median(times) if times else None), author_cost_usd=None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-complete", action="store_true", help="Exit 2 unless all 30 finalized trajectories are audited")
    args = parser.parse_args()
    try:
        report = Audit().run()
    except Exception as error:
        report = dict(audit_status="invalid", complete=False, final_audit_passed=False,
                      errors=[dict(check="audit execution", detail=f"{type(error).__name__}: {error}")])
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    return 1 if report["audit_status"] == "invalid" else 2 if args.require_complete and not report["complete"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
