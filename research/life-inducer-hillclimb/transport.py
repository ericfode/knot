"""One account-backed Codex call per ID, with strict replay and raw receipts.

Adapted from bend-tests/sigil/inducers/run.py; no historical builder is imported.
Transport completion is not a compiler, behavior, semantic, or style pass.
"""

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile
import time


PROVENANCE = {
    "path": "/Users/ericfode/src/bend-tests/sigil/inducers/run.py",
    "sha256": "1a6ed1e6d67421aa24b9c11c0724d03eb9998e16ec74fe9ff93eb4e8ed3c37b7",
}
ALLOWED_CONFIGURATIONS = {("gpt-6-astra", "low"), ("gpt-6-sol", "xhigh")}
DISABLED_FEATURES = (
    "apps", "browser_use", "browser_use_external", "browser_use_full_cdp_access",
    "code_mode", "code_mode_host", "code_mode_only", "computer_use",
    "remote_plugin", "plugins", "recommended_plugins", "skill_search",
    "skill_mcp_dependency_install", "shell_tool", "unified_exec", "sleep_tool",
    "view_image", "image_generation", "multi_agent", "multi_agent_v2", "goals",
    "chronicle", "memories", "hooks", "tool_suggest", "unbounded_connection_retries",
)
# Account authentication stays in CODEX_HOME. API keys and inherited task controls
# are not passed through. Values (including proxy credentials) are never logged.
ENVIRONMENT_ALLOWLIST = frozenset({
    "HOME", "PATH", "TMPDIR", "TMP", "TEMP", "USER", "LOGNAME", "SHELL",
    "LANG", "LC_ALL", "LC_CTYPE", "TERM", "CODEX_HOME", "XDG_CONFIG_HOME",
    "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME", "SSL_CERT_FILE",
    "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "HTTP_PROXY",
    "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "http_proxy", "https_proxy",
    "all_proxy", "no_proxy", "SYSTEMROOT", "WINDIR",
})
SCHEMA_KEYWORDS = {
    "$schema", "title", "description", "type", "properties", "required",
    "additionalProperties", "items", "enum", "minLength", "maxLength",
}
JSON_TYPES = {"object", "array", "string", "integer", "number", "boolean", "null"}


class TransportError(RuntimeError):
    """A preflight or receipt-integrity failure; no automatic paid retry is made."""


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def _load_json(data):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result

    def constant(value):
        raise ValueError("non-JSON numeric constant: " + value)

    def number(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("nonfinite JSON number")
        return parsed

    return json.loads(data, object_pairs_hook=pairs, parse_constant=constant, parse_float=number)


def _check_schema(schema, at="$schema"):
    """Reject unsupported schema features before a paid call, rather than skip them."""
    if not isinstance(schema, dict) or set(schema) - SCHEMA_KEYWORDS:
        raise TransportError(f"{at}: unsupported schema shape or keywords")
    if schema.get("type") not in JSON_TYPES:
        raise TransportError(f"{at}: one explicit JSON type is required")
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    if not isinstance(properties, dict) or not isinstance(required, list):
        raise TransportError(f"{at}: malformed properties/required")
    if any(not isinstance(key, str) for key in required) or len(set(required)) != len(required):
        raise TransportError(f"{at}: required must contain unique strings")
    additional = schema.get("additionalProperties", True)
    if not isinstance(additional, bool):
        raise TransportError(f"{at}: only boolean additionalProperties is supported")
    if "enum" in schema and (not isinstance(schema["enum"], list) or not schema["enum"]):
        raise TransportError(f"{at}: enum must be a nonempty array")
    for bound in ("minLength", "maxLength"):
        if bound in schema and (type(schema[bound]) is not int or schema[bound] < 0):
            raise TransportError(f"{at}: {bound} must be a nonnegative integer")
    for name, child in properties.items():
        _check_schema(child, at + ".properties." + name)
    if "items" in schema:
        _check_schema(schema["items"], at + ".items")


def _validate(value, schema, at="$"):
    kind = schema["type"]
    valid = {
        "object": isinstance(value, dict), "array": isinstance(value, list),
        "string": isinstance(value, str), "integer": type(value) is int,
        "number": type(value) in (int, float), "boolean": type(value) is bool,
        "null": value is None,
    }[kind]
    if not valid:
        raise ValueError(f"{at}: expected {kind}")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{at}: nonfinite number")
    if "enum" in schema and not any(type(value) is type(x) and value == x for x in schema["enum"]):
        raise ValueError(f"{at}: value outside enum")
    if kind == "object":
        props = schema.get("properties", {})
        missing = set(schema.get("required", [])) - set(value)
        if missing:
            raise ValueError(f"{at}: missing keys {sorted(missing)}")
        if schema.get("additionalProperties") is False and set(value) - set(props):
            raise ValueError(f"{at}: extra keys {sorted(set(value) - set(props))}")
        for name, child in value.items():
            if name in props:
                _validate(child, props[name], at + "." + name)
    elif kind == "array" and "items" in schema:
        for index, child in enumerate(value):
            _validate(child, schema["items"], f"{at}[{index}]")
    elif kind == "string":
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", len(value)):
            raise ValueError(f"{at}: string length outside schema bounds")


def _write_new(path, data):
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _environment():
    return {key: value for key, value in os.environ.items()
            if key in ENVIRONMENT_ALLOWLIST and not key.upper().startswith(("TYPESAFE", "PERCH"))}


def _cli_info(environment):
    executable = shutil.which("codex", path=environment.get("PATH"))
    if not executable:
        raise TransportError("codex executable not found; no model request made")
    executable = str(Path(executable).resolve())
    version = subprocess.run([executable, "--version"], env=environment,
                             capture_output=True, timeout=15, check=True)
    return executable, version.stdout.decode("utf-8").strip()


def _options(model, effort):
    args = ["exec", "--ignore-user-config", "--ignore-rules", "--ephemeral",
            "--skip-git-repo-check", "--model", model,
            "-c", f'model_reasoning_effort="{effort}"',
            "-c", "project_doc_max_bytes=0", "-c", 'approval_policy="never"',
            "-c", 'web_search="disabled"', "-c", "suppress_unstable_features_warning=true"]
    for feature in DISABLED_FEATURES:
        args.extend(["--disable", feature])
    args.extend(["--enable", "skip_host_skill_discovery", "--sandbox", "read-only",
                 "--cd", "<EMPTY_TEMP_DIRECTORY>", "--output-schema", "<SCHEMA_SNAPSHOT>",
                 "--json", "--output-last-message", "<ATTEMPT_RESPONSE>", "-"])
    return args


def _stop_group(proc):
    cleanup = []
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
            cleanup.append(sig.name)
        except ProcessLookupError:
            cleanup.append(sig.name + ": already gone")
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            continue
    # The second signal also removes descendants if the group leader exited first.
    proc.wait(timeout=5)
    return cleanup


def _review_events(raw, model, effort):
    events, errors = [], []
    for number, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = _load_json(line)
            if not isinstance(event, dict):
                raise ValueError("event is not an object")
            events.append(event)
        except (ValueError, UnicodeError):
            errors.append(f"unparseable event line {number}")
    known = {"thread.started", "turn.started", "turn.completed", "turn.failed", "error",
             "item.started", "item.updated", "item.completed"}
    tools, warnings, messages, models, efforts = [], [], [], [], []
    for event in events:
        kind = event.get("type")
        if kind not in known:
            errors.append("unrecognized event type: " + str(kind))
        if kind in ("error", "turn.failed"):
            errors.append("CLI reported " + kind)
        if kind in ("item.started", "item.updated", "item.completed"):
            item = event.get("item", {})
            if not isinstance(item, dict):
                errors.append("malformed item event")
                continue
            item_kind = item.get("type")
            if item_kind not in ("agent_message", "reasoning", "error"):
                tools.append({"event": kind, "item_type": item_kind, "item_id": item.get("id")})
            if item_kind == "error":
                warnings.append(item.get("message"))
            if kind == "item.completed" and item_kind == "agent_message":
                messages.append(item.get("text"))
        if kind in ("thread.started", "turn.started", "turn.completed"):
            if isinstance(event.get("model"), str):
                models.append(event["model"])
            for key in ("reasoning_effort", "model_reasoning_effort"):
                if isinstance(event.get(key), str):
                    efforts.append(event[key])
    completions = [event for event in events if event.get("type") == "turn.completed"]
    threads = [event.get("thread_id") for event in events if event.get("type") == "thread.started"]
    usage = completions[-1].get("usage") if completions else None
    if len(completions) != 1:
        errors.append("expected exactly one completed turn")
    if len(threads) != 1 or not isinstance(threads[0], str) or not threads[0]:
        errors.append("expected exactly one fresh thread ID")
    if not isinstance(usage, dict) or any(type(usage.get(key)) is not int or usage[key] < 0
                                          for key in ("input_tokens", "output_tokens")):
        errors.append("missing or malformed token usage")
    if tools:
        errors.append("tool events disqualify this attempt")
    if any(reported != model for reported in models):
        errors.append("reported model differs from requested model")
    if any(reported != effort for reported in efforts):
        errors.append("reported reasoning effort differs from requested effort")
    return {
        "usage": usage, "thread_id": threads[0] if len(threads) == 1 else None,
        "tool_events": len(tools), "tool_event_details": tools, "warnings": warnings,
        "reported_models": sorted(set(models)), "reported_reasoning_efforts": sorted(set(efforts)),
        "model_validation": "matched_reported" if models and not any(x != model for x in models)
                            else "mismatch" if models else "requested_only_not_reported",
        "effort_validation": "matched_reported" if efforts and not any(x != effort for x in efforts)
                             else "mismatch" if efforts else "requested_only_not_reported",
        "event_errors": errors,
    }, messages[-1] if messages else None


def call(ident, prompt, schema, directory, model, effort, timeout=420):
    """Return a receipt; only status == 'completed' permits consuming response_path.

    An identifier allows one subprocess attempt. Repeating a failed/interrupted ID
    never retries. Choose a new explicit ID only after inspecting its evidence.
    Completed replay requires identical inputs/options and untampered artifacts.
    """
    if not isinstance(ident, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,119}", ident):
        raise TransportError("ident must be a safe 1-120 character basename")
    if (model, effort) not in ALLOWED_CONFIGURATIONS:
        raise TransportError("only gpt-6-astra/low and gpt-6-sol/xhigh are authorized")
    if not isinstance(prompt, str) or not prompt.strip():
        raise TransportError("prompt must be a nonempty string")
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise TransportError("timeout must be positive and finite")
    if os.name != "posix":
        raise TransportError("this transport requires POSIX process-group cleanup")
    prompt_bytes = prompt.encode("utf-8")
    schema_path = Path(schema).resolve()
    schema_bytes = schema_path.read_bytes()
    schema_value = _load_json(schema_bytes)
    _check_schema(schema_value)
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    environment = _environment()
    executable, version = _cli_info(environment)
    options = _options(model, effort)
    identity = {
        "protocol": "life-inducer-transport/1", "prompt_sha256": _sha(prompt_bytes),
        "schema_sha256": _sha(schema_bytes), "model": model, "reasoning_effort": effort,
        "cli_executable": executable, "cli_version": version, "options": options,
        "timeout_seconds": timeout, "transport_sha256": _sha(Path(__file__).read_bytes()),
        "environment_allowlist": sorted(ENVIRONMENT_ALLOWLIST),
        "provenance": PROVENANCE,
    }
    identity_hash = _sha(_json_bytes(identity))
    receipt_path = directory / f"{ident}.receipt.json"
    stem = directory / f"{ident}.attempt-1"
    files = {key: Path(str(stem) + suffix) for key, suffix in {
        "prompt": ".prompt.txt", "schema": ".schema.json", "events": ".events.jsonl",
        "stderr": ".stderr.txt", "response": ".response.json", "receipt": ".receipt.json",
        "reservation": ".reservation.json",
    }.items()}
    if receipt_path.exists():
        prior = _load_json(receipt_path.read_bytes())
        if prior.get("identity_sha256") != identity_hash or prior.get("identity") != identity:
            raise TransportError("identifier already exists with a different request identity")
        if files["receipt"].read_bytes() != receipt_path.read_bytes():
            raise TransportError("immutable attempt receipt and receipt index differ")
        for key, digest in prior.get("artifact_sha256", {}).items():
            if key not in files or not files[key].is_file() or _sha(files[key].read_bytes()) != digest:
                raise TransportError("receipt artifact integrity failure: " + key)
        if prior.get("status") == "completed":
            raw_response = files["response"].read_bytes()
            if _sha(raw_response) != prior.get("response_sha256"):
                raise TransportError("completed response hash mismatch")
            _validate(_load_json(raw_response), schema_value)
            if (directory / f"{ident}.json").read_bytes() != raw_response:
                raise TransportError("completed response alias differs from attempt output")
            return {**prior, "replayed": True}
        return {**prior, "replayed": True, "retry_blocked": True}
    if list(directory.glob(ident + ".*")):
        raise TransportError("partial or running attempt exists; inspect it, do not retry blindly")

    started = time.perf_counter()
    result = {
        "id": ident, "attempt": 1, "status": "running", "replayed": False,
        "model": model, "reasoning_effort": effort,
        "requested_model": model, "requested_reasoning_effort": effort,
        "identity": identity, "identity_sha256": identity_hash,
        "prompt_sha256": identity["prompt_sha256"], "schema_sha256": identity["schema_sha256"],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "response_path": str(files["response"]), "receipt_path": str(receipt_path),
        "cost_usd": None, "cost_note": "Codex account run; billed cost unavailable, not inferred.",
        "schema_validation": "not_run", "final_message_validation": "not_run",
        "environment_policy": "allowlist; credential values not logged",
        "error": None, "cleanup": [], "exit_code": None,
    }
    # Exclusive reservation prevents concurrent duplicate calls and survives a crash.
    try:
        _write_new(files["reservation"], _json_bytes(result))
    except FileExistsError as exc:
        raise TransportError("concurrent or partial attempt exists; no model request made") from exc
    _write_new(files["prompt"], prompt_bytes)
    _write_new(files["schema"], schema_bytes)
    errors, timed_out, interrupted = [], False, False
    proc = None
    with tempfile.TemporaryDirectory(prefix="life-inducer-empty-") as cwd:
        replacements = {"<EMPTY_TEMP_DIRECTORY>": cwd, "<SCHEMA_SNAPSHOT>": str(files["schema"]),
                        "<ATTEMPT_RESPONSE>": str(files["response"])}
        command = [executable] + [replacements.get(arg, arg) for arg in options]
        result["command"] = command
        try:
            with files["events"].open("xb") as stdout, files["stderr"].open("xb") as stderr:
                proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                        cwd=cwd, env=environment, start_new_session=True)
                try:
                    proc.communicate(input=prompt_bytes, timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    result["cleanup"] = _stop_group(proc)
                    errors.append("model subprocess exceeded wall timeout")
                except BaseException:
                    interrupted = True
                    result["cleanup"] = _stop_group(proc)
                    raise
                result["exit_code"] = proc.returncode
        except BaseException as exc:
            # Raw files and a terminal receipt survive Python interruption as well.
            interrupted = interrupted or isinstance(exc, (KeyboardInterrupt, SystemExit))
            errors.append(type(exc).__name__ + ": " + str(exc))
            if proc is not None:
                result["exit_code"] = proc.returncode
    result["wall_seconds_including_cli_startup"] = time.perf_counter() - started
    if result["exit_code"] != 0:
        errors.append("nonzero or missing CLI exit status")
    review, final_message = _review_events(files["events"].read_bytes() if files["events"].exists() else b"",
                                          model, effort)
    result.update(review)
    errors.extend(review["event_errors"])
    try:
        raw_response = files["response"].read_bytes()
        result["response_sha256"] = _sha(raw_response)
        value = _load_json(raw_response)
        _validate(value, schema_value)
        result["schema_validation"] = "passed"
    except (OSError, ValueError, UnicodeError) as exc:
        errors.append(type(exc).__name__ + ": " + str(exc))
        result["schema_validation"] = "failed"
    if result["schema_validation"] == "passed":
        try:
            if not isinstance(final_message, str) or _load_json(final_message) != value:
                raise ValueError("attempt response does not match the final agent-message JSON")
            result["final_message_validation"] = "passed"
        except (ValueError, UnicodeError) as exc:
            errors.append(type(exc).__name__ + ": " + str(exc))
            result["final_message_validation"] = "failed"
    result["status"] = "interrupted" if interrupted else "timed_out" if timed_out else "failed" if errors else "completed"
    result["error"] = "; ".join(errors) if errors else None
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    result["artifact_sha256"] = {key: _sha(path.read_bytes()) for key, path in files.items()
                                  if key not in ("receipt", "reservation") and path.exists()}
    if result["status"] == "completed":
        _write_new(directory / f"{ident}.json", files["response"].read_bytes())
    _write_new(files["receipt"], _json_bytes(result))
    _write_new(receipt_path, _json_bytes(result))
    return result
