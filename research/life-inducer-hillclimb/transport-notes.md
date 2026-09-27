# Fresh Life author transport

`transport.call(ident, prompt, schema, directory, model, effort, timeout=420)`
returns a receipt dictionary. Consume `response_path` only when `status` is
`completed`; the exact successful JSON is also available at `<ident>.json`.
Only `gpt-6-astra` with `low` and `gpt-6-sol` with `xhigh` are accepted, matching
the explicit experiment override. A completed transport is not a Life pass.

The adaptation source is
`/Users/ericfode/src/bend-tests/sigil/inducers/run.py`, SHA-256
`1a6ed1e6d67421aa24b9c11c0724d03eb9998e16ec74fe9ff93eb4e8ed3c37b7`.
It was read, never imported or executed. Historical `build()` and `main()` were
not run. Their Phi creativity objective and old schema are not used here.

## Isolation and records

Each subprocess starts in a new empty temporary directory, with no resumed
thread, ephemeral sessions, ignored user configuration and execution rules,
zero project-document bytes, disabled skill discovery, read-only sandbox, no
web search, and disabled tool/plugin/memory/agent features. The flags were
checked against local Codex CLI 0.153.2 help and feature inventory. Actual tool
events, unknown item types, unknown event types, malformed JSONL, a failed turn,
missing usage, or a missing fresh thread ID disqualify the attempt.

The environment uses an explicit allowlist for account authentication location,
ordinary process settings, TLS and proxy settings. `TYPESAFE*`, `PERCH*`, API
keys and inherited Codex task controls are absent. Environment values and
authentication files are never recorded. Codex still needs its own account
authentication and network access; this is context isolation, not an OS
security boundary against the CLI. Timeout cleanup signals the entire POSIX
process group and reaps the direct child; descendants that deliberately create
a new session are outside that guarantee.

An exclusive reservation allows one attempted subprocess per ID. Raw prompt,
schema snapshot, stdout JSONL, stderr, response and receipt are retained under
`<ident>.attempt-1.*`. These files are never overwritten. Interrupted or failed
IDs return their prior terminal receipt without retrying. A partial reservation
without a terminal receipt blocks reuse. A deliberate recovery must use a new
explicit ID after reviewing the evidence and be linked by the caller; the
transport never decides to spend another model call.

Replay identity covers the exact prompt and schema bytes, requested model and
effort, CLI executable and version, normalized options, timeout, environment
policy, transport source hash and adaptation provenance. A completed replay
rechecks all retained artifact hashes, the successful response alias, and the
local schema. Changing any identity component rejects same-ID reuse. The
attempt receipt and index receipt must agree exactly.

The local schema validator supports explicit JSON types, object properties and
required keys, boolean `additionalProperties`, homogeneous `items`, `enum`,
string length bounds, and descriptive metadata. Unsupported schema keywords
fail before the model call. This covers the experiment's required `source`,
`hypothesis`, and `findings` strings. Duplicate JSON keys and nonfinite constants
are rejected. The attempt response must match the final agent-message JSON.

Receipts distinguish requested configuration from model/effort actually
reported in CLI lifecycle events. If the CLI does not report resolved settings,
the corresponding validation field is `requested_only_not_reported`; command
arguments are evidence of the request, not proof of resolution. Explicitly
reported mismatches fail. Token usage is retained as emitted. Wall time includes
model CLI startup; per-call billed cost is unavailable and remains null.

## Experiment boundary

Use separate IDs for every model configuration and declared generation or
repair call. A 30-trial manifest should distinguish trial starts from additional
repair/review calls. The controller alone owns oracle code and private fixtures;
only the public contract, allowed language references, exact wordless inducer,
and explicitly permitted feedback belong in author prompts. Preserve the
assembled prompt before every call. Do not put parent history in it.

The old generator's grammar mode inserts English words and nonce mode inserts
syllables. A wordless adaptation must restrict glyph mode and validate its
allowed Unicode inventory and layout. Do not call the historical builder, which
writes directly into the old evidence directories. Pairing each of 15 inducer
conditions across the two configurations gives 30 fresh starts, if that is the
controller's frozen design; adaptive selection and any confirmation allocation
must be declared before observing outcomes.

Optimize correctness and complete, unchanged Perch acceptance before speed.
Report time and calls to first complete pass, with exhausted trials censored;
fast failures are not wins. Adaptive hill climbing provides search evidence,
not an unbiased estimate of an inducer's causal effect.

No paid smoke call was authorized for this implementation. The first actual
trial is the live transport qualification and must retain failures as evidence.

Offline verification used a temporary fake Codex executable, with no provider
access. Sixteen checks passed: exact Unicode prompt/response retention, empty
working directory and sanitized environment, completed replay, identity
conflicts, schema rejection, duplicate JSON keys, tool events, malformed events,
final-message mismatch, nonzero exit, model mismatch, explicit reported model
matching, rejected model/effort pairs, unsupported schemas, corrupted receipts,
partial reservations, and timeout cleanup. Failure cases also checked that
same-ID reuse did not launch again. All 27 feature toggles were present in the
installed CLI feature inventory. Live JSONL compatibility remains unverified
until the controller's first actual trial; CLI help documents JSONL output but
does not itself prove the emitted lifecycle schema.
