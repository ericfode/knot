# Perch latency diagnosis — 2026-09-26

The main avoidable costs are **serial requests per declaration** and
**reloading the rules and Git tree for every declaration**. Individual Jev
responses were approximately 100 ms in the measured run. Parsing and style
report generation were small for the measured file.

This investigation used revision `876c2ff`, Node 22.22.3, Perch 0.3.5 and its
existing Bend adapter. It adds profiling tools and evidence; production
behavior, rules and acceptance policy are unchanged. Other checkouts were
read only. The measurements are small local samples, not throughput guarantees.

## Live measurement

Target: `packages/source/main.bend`, with 62 executable declarations and two
datatypes. Semantic review selected the four performance rules, grouped in
one request per executable declaration. Style asked all three axes in one
request per declaration, including datatypes.

| Operation | Requests | Peak in flight | Wall time |
| --- | ---: | ---: | ---: |
| Semantic check | 62 | 1 | 9.300 s |
| Style, default explicit-target concurrency | 64 | 1 | 7.168 s |
| Same style states, `--jobs=8` | 64 | 8 | 1.090 s |
| Semantic check, immediate offline responses | 62 | 1 | 2.913 s |

The live semantic check spent **6.427 s** inside provider round trips and
**2.872 s** outside them. Median round trip: **99.90 ms**; maximum: 162.12 ms.
Every request completed with HTTP 200 and resolved to `jev-1.13.0`.
All 248 selected semantic checks completed without findings. Style returned
exit 3 for attention, with complete coverage; that was not a transport failure.

Style concurrency improved wall time **6.58×** while preserving all 64 input
states. Median request latency increased from 104.99 to 118.38 ms, but requests
overlapped. Repeated inputs may benefit from provider caching. Offline controls
also reproduced the scheduling difference with fixed 25 ms responses:
1.701 s at one worker versus 0.238 s at eight.

[Request timing evidence](perch-calibration/latency-profile-2026-09-26.json.gz)
contains counts, timings and state hashes without source bodies or credentials.
Round trips include network, provider processing and decoding; they do not
isolate model inference. Normal local receipts retain the review results.

## Confirmed causes

1. **Serial fan-out.** The [Bend adapter](../scripts/install-perch-bend.mjs)
   preflights all contexts, then awaits each recursive `checkTarget` before
   dispatching the next. Required syntax/context preflight does not require
   serial model requests afterward. Explicit-file [style review](../scripts/perch-style.mjs)
   defaults to one worker; project mode defaults to eight. Three style axes
   are already batched, so they are not three separate network round trips.
2. **Repeated rule discovery.** The adapter reads rules to select declarations.
   Every recursive check reads them again. Upstream `readRuleFiles` calls
   `listTree`, running `git ls-tree -r -l -z <revision>` over the whole
   **1,443-entry** committed tree before filtering rule paths. It also rereads
   and reparses the same YAML. This file caused **63 rule loads and listings**.
3. **Whole-file scope and no check-answer reuse.** `file.bend` reviews every
   applicable declaration; `file.bend::name` selects one with helper context.
   `check` does not cache answers. The skill's unchanged-method caching refers
   to `scan`. Style reuse requires explicit `--reuse` and matching identities.

## Isolating the rule-loading cost

A disposable copy of the installed bundle wrapped rule loading and tested
command-local memoization with fixed offline answers. Alternating controls
produced identical request-sequence and complete-result hashes in all runs:

| Variant | Rule loads / Git listings | Wall | Rule-loading time |
| --- | ---: | ---: | ---: |
| Existing path, first | 63 / 63 | 2.813 s | 2.665 s |
| Load once, first | 1 / 1 | 0.131 s | 0.041 s |
| Existing path, second | 63 / 63 | 2.819 s | 2.707 s |
| Load once, second | 1 / 1 | 0.127 s | 0.043 s |

Git listing alone took 2.509–2.563 s in the uncached controls. Removing this
redundancy improved the offline baseline about **22×**. That is not a 22×
claim for live review: provider work remains. Function timings are nested.

[Rule-loading evidence](perch-calibration/latency-rule-loading-2026-09-26.json).
The temporary module is removed in `finally`; the installed CLI is unchanged.
The counterfactual assumes unchanged rules during an invocation. A production
fix should pass a command-local rule snapshot into recursive checks, not
retain an indefinite global cache.

## Existing receipts and measurement limits

A [snapshot of 735 primary-checkout receipts](perch-calibration/latency-history-2026-09-26.json)
contained 691 live semantic checks resolved to `jev-1.13.0`. The 451
single-request checks had a 237 ms median duration and 377 ms p95. A
63-request file reached 8.635 s. All 3,218 recorded semantic requests had
responses; no failed-attempt/retry gap appears in this sample.

The project style run made 1,872 fresh requests and took 25.890 s in its
evaluation/report timer, with 104 ms median row latency. A broad semantic
scan made 2,022 requests and took 65.830 s, reporting partial parser coverage.
These are broad-review costs, not single-change checks or full acceptance.

Semantic receipt timing omits initial CLI import, measured at 75.96 ms here.
Style timing excludes discovery, parsing/context preflight and receipt writes.
The harness measures around the full imported command invocation; omitted
style work was small for this file. Whole-project preflight was not timed.

Semantic requests have no explicit application timeout. The upstream client
can retry transport errors, HTTP 429 and 5xx up to four attempts with 2/4/8 s
backoffs or `Retry-After`. That explains possible long tails, not these
successful measurements. Style has a 30-second timeout and no automatic retries.

## Next increments

1. Load rules once per command, preserving selection and request contents.
2. Add bounded semantic workers after preflight, preserving result attribution,
   per-unit budgets, stable output order and stop-dispatch behavior on failure.
3. Use `--jobs=8` for explicit-file style review; it already works. Consider
   making bounded concurrency the explicit-file default.
4. Keep changed-declaration targeting and matching receipt reuse. Add phase
   timing and progress so slow responses can be distinguished from fan-out.

These are proposed production changes, not shipped optimizations in this
checkpoint. No accepted rule or context coverage was reduced for speed.

## Reproduce

```sh
npm ci
# Offline fixed answers measure plumbing, not model quality.
node scripts/profile-perch-latency.mjs --output=.local/new-latency.json
node scripts/profile-perch-rule-loading.mjs .local/new-rule-loading.json

# Optional live run: one semantic check and two style checks; consumes credits.
node scripts/profile-perch-latency.mjs --live --output=.local/new-live.json
# Add --env-file=/absolute/path/to/.env if credentials are not exported.

# Existing faster style invocation, preserving file coverage and all axes.
npm run lint:style -- --live packages/source/main.bend --jobs=8
```

Both scripts refuse existing outputs. The latency harness writes normal local
usage receipts, labeling fixed responses `offline-latency-probe`. The second
script uses a disposable instrumented bundle and no network. Its assertions
require identical requests and complete results across the cache controls.

Verification: both profiler scripts pass Node syntax checks; their offline
assertions completed. The two live style runs have identical ordered state
hashes, every live response is HTTP 200 from `jev-1.13.0`, and the target and
profiler hashes still match the evidence. `npm run lint:verify` passes all
28 offline tests and eight-rule law wiring. No Bend source was edited, so
compiler/package gates and additional semantic/style reviews were not rerun.
