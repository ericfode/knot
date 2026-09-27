# Perch whole-repository throughput — 2026-09-26

The fastest tested configuration that completed every parsable target used
**16 workers**. The frozen whole-repository semantic scan fell from **70.57 s to
39.43 s (1.79×)**; v3 style review fell from **39.19 s to 19.78 s (1.98×)**.
Sixteen is now the default for scan, check and style. Explicit flags override
`PERCH_JOBS`, which overrides the default. The supported range is 1–256.

These are sequential local measurements, not a universal optimum or a clean
review verdict. Provider capacity varies. The existing **16 parser failures**
remain visible; the project wrapper still rejects partial scan coverage, and
whole-project style returns incomplete coverage. No rule, context cap, style
target, parser diagnostic or provider failure was removed to improve timing.

## What changed

- Refillable, bounded workers replace per-batch barriers and serial Bend file
  checks. A provider semaphore also bounds nested follow-up requests. Failures
  stop new admission and drain already-started work before returning.
- Each check reads its rules once. Every declaration gets its own existing
  request allowance; a large file no longer shares a 64-request allowance.
- Git blobs are read in one batch instead of one Git process per file. The
  complete original file universe and order remain available to context lookup.
  Concurrent reads of the same immutable source share a promise.
- Exact token counts use a bounded string cache. Mutated request objects are
  serialized again; token budgets and truncation behavior are unchanged.
- Style preflight reads/parses each real source once per invocation, indexes
  references, and reuses declaration slices. Files must still remain inside
  the workspace, and only explicit imports supply helper context. Source
  freshness is checked before and after provider work.
- Style summary construction is linear in the number of assessments. JSON is
  encoded once for receipt, optional output and stdout. Receipts expose
  preflight, evaluation, freshness and aggregation time, plus peak concurrency.
- Scan checkpoint headers and journal offsets are captured from the same
  snapshot. Work finishing during an append is retained for the next checkpoint.

The pinned Perch 0.3.5 installer checks the upstream checksum before applying
the patch. Throughput helper and patch hashes participate in the adapter/cache
identity. The newer v3 criticality, Anticipation and Payoff policy from
`4d856ca` is preserved.

## Live tuning

Sources were frozen at `645212b`; style used the v3 rubric from `4d856ca`.
Node was 22.22.3 and every successful response resolved to `jev-1.13.0`.
Native command wall times include preflight and receipt writes, and exclude
module imports. Each semantic run used a fresh store; no answer reuse occurred.
Repeated requests may benefit from provider caching.

| Semantic scan | Seconds | HTTP 200 | HTTP 429 | Unread declarations |
| --- | ---: | ---: | ---: | ---: |
| Previous implementation, 8 workers | 70.57 | 2,035 | 0 | 0 |
| Optimized, 8 | 41.87 | 2,037 | 0 | 0 |
| Optimized, 16 | 39.43 | 2,035 | 158 | 0 |
| Optimized, 32 | 38.45 | 2,020 | 469 | 13 |
| Optimized, 128 | 55.92 | 1,740 | 2,035 | 295 |

All scan attempts selected 1,941 declarations. The 16-worker run recovered its
rate-limited requests using the existing bounded retry policy. The 32- and
128-worker runs are failures, not speedup evidence. Eight workers are a useful
lower-pressure option when sharing provider capacity. The old file-rule tail
could exceed its configured concurrency; it peaked at 49 HTTP requests despite
the old `--parallel 8` setting. The new global semaphore enforces the limit.

| Whole-repository v3 style | Seconds | Successful responses | Outcome |
| --- | ---: | ---: | --- |
| Previous implementation, 8 workers | 39.19 | 2,337 | All parsable units rated |
| Optimized, 16 | 19.78 | 2,337 | All parsable units rated |
| Optimized, 32 | 6.97 | 1,296 | Failed: 7 rate-limit responses |
| Optimized, 64 | 3.97 | 949 | Failed: 14 rate-limit responses |

Both completed style runs sent exactly the same request set. The provider
returned `Retry-After: 1` on the overloaded trials. Style retains its existing
no-retry policy; it saves completed rows for explicit matching `--reuse` and
never turns a partial run into a ranking. Maximum concurrency is not maximum
completed throughput.

## Equivalence and deterministic checks

The retained [benchmark evidence](perch-calibration/throughput-2026-09-26.json.gz)
includes hashes, counts, timings, coverage and failed trials without source
bodies, credentials, cookies or provider error text.

- Fixed-answer full scans produced identical sets of **1,985 request bodies**,
  identical normalized **1,941 declaration results**, and identical parser
  coverage. Offline time fell from 19.75 s to 6.70 s at 8 versus 32 workers.
- V3 style's fixed-5-ms control produced identical **2,337 requests and complete
  normalized results**. Time fell from 5.22 s to 1.75 s at 8 versus 32 workers.
  New preflight was 1.19 s, with 295 real-source parse calls for 298 logical
  paths. These artificial timings measure plumbing, not semantic quality.
- The same ordered 1,056 extra Git blobs had an identical hash under serial
  and batched reads: 9.19 s versus 0.11–0.12 s. No candidate filtering changed.
- Repeated targeted controls now load rules once, rather than once per
  declaration. Serial and concurrent checks retain the same request states.
- `npm run lint:verify`: **46 tests pass**, plus the eight-law-rule wiring gate.
  Tests cover source/rule edits across commands, context boundaries, ordered
  attribution, nested limits, arbitrary rejection values, failure draining,
  budget isolation, model drift, reuse and checkpoint races.

## Running it

```sh
npm ci
npm run lint:scan -- --parallel 16
npm run lint:style -- --live --all --jobs=16
npm run lint -- packages/source/main.bend --parallel 16
```

For a new timing receipt, the profiler uses a fresh scan store and records
hashes/counts rather than source bodies. It defaults to offline fixed answers;
`--live` explicitly enables provider requests. Supply credentials through the
environment or a private env-file path.

```sh
node scripts/profile-perch-throughput.mjs --kind=scan --output=.local/scan-profile.json
node scripts/profile-perch-throughput.mjs --kind=style --jobs=16 --live --env-file=.env --output=.local/style-profile.json
```

`--module=path` selects an importable baseline exposing native `main` or
`runStyleRanking`. Full-scan and style inventories differ: scan reads committed
HEAD and its normal exclusions; style includes nonignored working-copy Bend
files and reports unranked files. Keep revision, working tree, rubric and model
identities fixed when comparing. Run one Perch command per Node process; the
native CLI still has process-global command state.

The [earlier latency diagnosis](perch-latency-2026-09-26.md) describes the old
implementation and remains historical evidence.

## Main integration

The implementation and current main were merged at `698d88a`; all 46 tooling
tests and law-rule wiring passed after integration. The primary checkout's
nine existing modified files and staged `research/adaptive-tasks/task.bend`
entry were preserved byte-for-byte during the fast-forward. No remote push
was performed.

A live whole-scan verification of that merged revision was rejected with
**HTTP 402 on the first request**. Paid checks stopped immediately. This does
not replace the earlier completed frozen-source trials or establish complete
live coverage of the merged source. The retained
[integration receipt](perch-calibration/throughput-integration-2026-09-26.json)
separately records offline plumbing verification and the rejected live attempt.
The merged-tree offline scan completed 2,030 fixed-answer requests across 1,986
declarations with zero failed requests; style rated all 2,345 parsable units.
Both retain the same 16 unparseable files. These fixed answers establish
execution/coverage only, not review findings or style quality.

### Live verification after credits were added

After the user purchased credits, both deferred checks ran on merged revision
`deddae2`, sequentially at the default 16 workers. The earlier HTTP 402 is
retained as historical evidence; it no longer blocks these completed runs.

- Semantic scan: **40.21 s**, 1,986 declarations, 71,824 rule checks, zero
  failed or incomplete requests, and no cached answers carried. All 152 HTTP
  429 responses recovered; 2,082 requests returned HTTP 200. Native exit 3
  reflects model findings, which this throughput task has not confirmed.
- Whole-project style: **22.00 s**, all **2,345 parsable units** rated, 2,345
  HTTP 200 responses and no provider failure. Source/context hashes remained
  current throughout the run. No saved answers were reused.

The same 16 parser failures remain visible, so neither run establishes a
complete repository coverage pass. Style returns exit 1 for those unranked
files; its ratings retain the current v3 requirements. These merged-source
measurements close the deferred live validation, rather than replacing the
earlier comparison on a different frozen inventory.

The [restored-credit receipt](perch-calibration/throughput-credits-restored-2026-09-26.json)
records counts, timings, hashes and coverage, with complete compressed
[scan results](perch-calibration/throughput-credits-restored-2026-09-26-scan.json.gz)
and [style results](perch-calibration/throughput-credits-restored-2026-09-26-style.json.gz).
Implementation and configuration are unchanged; the previous 46-test and
law-wiring verification remains the applicable deterministic evidence.

## Why fresh whole-repository reviews still take seconds

The optimization preserved the per-declaration review design. A fresh style
pass still sends 2,345 HTTP requests. Their measured mean round trip was
139 ms: `2345 × 0.139 / 16 = 20.4 seconds` even with fully occupied workers.
The actual provider phase was 20.54 s, with 15.88 requests in flight on average.
Preflight used 1.32 s; all remaining work used roughly 0.15 s. Style is now
dominated by request volume and round-trip latency.

Semantic review additionally encountered rate limiting. Its 2,082 successful
requests carried a median 35 questions each; it received 152 HTTP 429 replies.
Seventy-six requested a one-second retry delay and seventy-six requested two
seconds. The current semaphore retains a permit throughout retry sleep, so
those delays occupy **228 worker-seconds**. Dividing by 16 gives 14.25 seconds
of worker capacity; this is not an independently measured additive wall-time
cost. Actual HTTP concurrency averaged **8.27**, while pre-request work took
3.52 s. The provider phase slowed to roughly 50 successful requests/second
after the initial burst. Purchasing credits cleared billing rejection without
removing this observed throttling.

These timings deliberately forced fresh answers. A separate offline probe
reused the saved results and rejected every attempted provider call:

| Same-source repeat | Wall time | Actual or attempted network requests |
| --- | ---: | ---: |
| Semantic scan with its existing store | 6.90 s | 0 |
| Style with explicit matching `--reuse` | 1.43 s | 0 |

All 1,986 semantic declarations and 2,345 style units retained their prior
results. Existing findings and the 16 parser failures remain. This probe does
not measure the cost of reviewing changed code; the semantic run also rebuilt
analysis for the newer documentation-only revision. Normal scan reuse is
automatic within its store; style reuse must be requested explicitly.

The remaining optimization work is reducing fresh request count, avoiding
repeated context/rubric transmission, and making admission aware of provider
rate limits. Multi-declaration batching would change review inputs and needs
equivalence/calibration evidence. Simply releasing sleeping permits could
increase the rejected-request storm. None of those changes is claimed here.
The [latency breakdown and offline cache probe](perch-calibration/remaining-latency-2026-09-26.json)
retain the measured timelines, calculations and their limits.
