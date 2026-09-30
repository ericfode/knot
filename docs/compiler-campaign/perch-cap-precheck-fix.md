# perch-cap pre-review correction

Executor condition `C3.frozen-edit` (`24d9a4ea7e06181d0715`) is fixed in
`1f414e1d`. `tests/perch-context/check.py` is byte-identical to campaign base
`88f02bf1`, SHA-256 `9c2199dd7dbce69e792bb4ce52ebc6e19a34325cca4a0755e85b87ff9759ed2d`.

The existing seven review-round-1 controls and five mutants now run in the
separate additive `perch-cap` gate, with `check-round1.py` and `round1.json`.
The restored `perch-context` gate retains 40 controls and 13 mutants; the new
gate holds seven controls and five mutants. Combined coverage remains 47
controls and 18 assertion-killed mutants, also selected by `lint:verify`.
The registry and required-name set only gain the new gate. Every frozen
expectation, compiler/package source, production context builder and rubric
is unchanged from the prior verified head `591d451d`. Both caps remain 60,000
state bytes and 48,000 composition source bytes.

[The measurement artifact](perch-cap-precheck-fix-measurements.json) records
source pins, every affected unit, exact cut amounts, all compositions and gate
results. Historical reports remain intact.

## Fresh identity and motivating-tree measurements

Current main snapshot `b92b1359`: **957/957 declaration hashes and 17/17
composition hashes match** (974 total, zero changed). The full official
preflight receipt is byte-identical: 722,704 uncompressed bytes, SHA-256
`044303f73a4743fd95f46fe30ba64bfe2f9a44fe218a8d402f9ead579f95ff06`; deterministic gzip 42,490 bytes, SHA-256
`20f828fb6509eb060a25e007100ba5a66c5aee94692b2b90c701331bcdbc2e2d`. Zero provider requests and zero structural blockers.
No shared preflight receipt was written.

Current motivating snapshot `7aa8427e` of `campaign/literals-integ` was
exported to permitted scratch and given the production tool change. Variant
(a) preserves its source/tasks; (b) restores both `C.exhausted(C.Checked,token)`
uses; (c) also restores the original checking, modules and matrix task files.
Only the scratch export was modified. Each variant prepares 2,713 declaration
states and 36 compositions.

| Variant | Raw run state | After interface tier | Fitted run state | Names cuts | Source / encoded bytes cut |
| --- | ---: | ---: | ---: | ---: | ---: |
| (a) Snapshot as recorded | 68,192 | 59,941 | 59,941 | 0 | 0 / 0 |
| (b) Both calls restored | 68,447 | 60,784 | 59,834 | 4 | 1,004 / 950 |
| (c) Calls and original tasks restored | 73,295 | 65,632 | 59,881 | 27 | 4,984 / 5,751 |

Names-only units: **0 / 1 / 53**. In (b), only `src/check.bend::run` needs it.
In (c), checking has one affected unit (27 cuts), matrix laws 40 (12–40 cuts),
matrix proofs 11 (13–19), and module loading one (15). Their exact identities
and source/encoded byte reductions are in the artifact. All declaration states
fit; the largest in (c) is 59,979 bytes.

The three largest compositions with calls/tasks restored are
`literal-source-machine` **47,639**, `checking` **47,311**, and
`pattern-matrix-proofs` **46,848** against 48,000 (margins 361, 689 and 1,152).
Variant (a)'s checking composition is 47,243; the other two largest are unchanged.
**All 36 compositions remain available with the original tasks.** No composition
repair is proposed. The separate 16,000-byte task budget is unchanged; existing
unavailable task evidence is explicit and does not count as measured profundity.

## Deterministic checks

`BEND_NO_TELEMETRY=1 npm run -s gates -- --jobs 2`: **21/21 passed, exit 0**,
measured **430.961106 seconds**, with Bun 1.3.14 and
Node 22.22.3. Retained summary:
`.local/gates/run-pm4s7_tr/summary.json`. This run covers the executable inputs
committed in `1f414e1d`; receipt refresh and this evidence document change no
executable gate input.

| Gate | Result / exit | Exact counts |
| --- | --- | --- |
| frontend | passed / 0 | `{"boundaries":24,"fixtures":14,"lane_observations":28,"mutants":4}` |
| checker | passed / 0 | `{"bound_observations":16,"bounds":2,"budgets":10,"fixtures":49,"lane_observations":98,"mutants":7}` |
| structural | passed / 0 | `{"bounds":4,"fixtures":16,"lane_observations":64,"mutants":7}` |
| fields | passed / 0 | `{"bound_observations":12,"bounds":2,"budgets":36,"fixtures":40,"host_boundaries":6,"lane_observations":240,"mutants":9}` |
| wasm | passed / 0 | `{"boundaries":44,"execution_lanes":2,"fixtures":25,"mutants":7,"reference_calls":90,"rejects":64}` |
| wasm-trust | passed / 0 | `{"entries":3,"proof_holes":0}` |
| fields-trust | passed / 0 | `{"entries":4,"proof_holes":0}` |
| structural-trust | passed / 0 | `{"entries":2,"proof_holes":0}` |
| owned-store | passed / 0 | `{"cases":3532,"execution_lanes":2,"literal_witnesses":15,"mutants":6}` |
| flat-store | passed / 0 | `{"bun":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621},"mutants":9,"native":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621}}` |
| recursion | passed / 0 | `{"fixtures":19,"mutants":3}` |
| fields-wasm | passed / 0 | `{"boundaries":30,"fixtures":8,"mutants":4}` |
| census | passed / 0 | `{"classes":41,"declarations":437,"files":30}` |
| perch-context | passed / 0 | `{"fixtures":40,"mutants":13}` |
| lint:verify | passed / 0 | `{"law_rules":8,"tests":192}` |
| bootstrap | passed / 0 | `{"corpus":789,"mutants":54,"reached":2,"stages":8}` |
| classification | passed / 0 | `{"fixtures":17,"mutants":6}` |
| io-host | passed / 0 | `{"cli_runs":6,"conformance_runs":86,"errno":[2,9,20,21,22,92],"fixtures":20,"host_boundaries":22,"mutants":6,"review":{"empty_write":4,"mutants":3,"oracle_controls":14,"secret_paths":21,"seed_runs":12},"seed_fixtures":40,"seed_runs":109,"stress":{"left_binds":100000,"right_binds":100000}}` |
| io-abi-2 | passed / 0 | `{"case_mode":"insensitive","fixtures":43,"host_boundaries":25,"mutants":5,"mutants_killed":5,"parity":153,"read_observations":21,"reference_observations":64,"seed_exhausted":2,"seed_observations":61}` |
| selfhost | passed / 0 | `{"blocked":63,"cases":65,"d4_gaps":5,"judge_mutants":20,"mutants":3,"passed":2}` |
| perch-cap | passed / 0 | `{"fixtures":7,"mutants":5}` |

The runner retried bootstrap once for its recognized `found no clang` host
failure. Both attempts remain in the logs; the final run passes without changing
an assertion. `gates:verify` passes 20 tests (exit 0), `lint:verify` passes 192
tests plus eight law-rule wiring controls (exit 0), guarded `lint:rules -- --json`
lists 57 rules (exit 0), and `census:check` exits 0. The catalog preload disables
environment-file loading and rejects network calls. All work used telemetry-off
execution. No provider/live Perch call or environment-file read ran.

Before the owned refresh, receipt classes were 65 identical, 20 volatile-only
and four semantic. The two context receipts reflect the coverage split and new
input hashes; only those were refreshed. All 15 plus 10 input-hash entries match
the working tree. Bootstrap `progress.json` and `reference.json` remain unchanged
for coordinator refresh.

## Pre-review disposition and remaining work

C3 on committed head `1f414e1d` exits 0 with no blocking or major executor
condition and **zero frozen-edit conditions**. The supplied fingerprint is absent.
This is an audit of C3 only, not a complete precheck pass: generator reproduction
and declared ownership are unavailable with the default manifest.

One nonblocking executor minor remains: `package.json`'s `lint:verify` selector
extension is not a new script key under the shared-file shape rule. Every base
test selector remains; the added review test files execute the same preserved
witnesses. The extension requires coordinator reconciliation at integration.
The controls-count amendment info and default `executor=claude` trailer flags
are coordinator conditions; the current user instruction requires the GPT-6.1
Sol trailer. No history or frozen expectations were rewritten.

Coordinator-only actions remain: integrate/merge, reconcile the motivating
branch's call/task restores, refresh shared bootstrap receipts, reconcile shared
script/trailer metadata and run live Perch calibration. Ordinary names-only
context is advisory and uncalibrated; omitted type/law evidence withholds
qualification. Selfhost remains two passing and 63 blocked cases. All implementer
acceptance items hold; no known failing acceptance check remains.
