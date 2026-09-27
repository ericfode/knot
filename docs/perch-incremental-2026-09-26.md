# Incremental Perch scans — 2026-09-26

Semantic scans and style reviews now support automatic incremental reuse.
The first invocation establishes the cache. Later invocations retain the full
selected inventory and ask only about unmatched model inputs.

```sh
npm run lint:incremental
npm run lint:style -- --live --all --incremental
```

Semantic scans read committed `HEAD`; style reads the working copy. Targeted
`npm run lint -- file.bend` remains the semantic path for uncommitted edits.
Use `lint:scan -- --fresh` or `lint:style -- --live --all --fresh` to obtain new
answers. Fresh runs refresh the answer cache without discarding deterministic
parser results. `--since` remains a changed-path filter; it can omit unchanged
dependents and cannot be combined with the new semantic modes.

## Implementation and correctness

Semantic review already stored previous answers, but analysis caching was tied
to an entire commit. The new parser cache uses source content, language and the
installed analysis profile, then rebuilds file identities and the dependency
graph from the current tree. Deterministic parse errors remain visible and are
cacheable; transient parser resource failures are retried. Corruption is a
cache miss. Atomic publication prevents partially written parser records.

All selected declarations still have their prepared request compared. Changing
an imported helper can invalidate its unchanged callers. Exact request keys now
include question names and compiled questions: renaming a rule cannot reuse the
old question's answer. Search keys include supplied context, rule kind and
threshold. Empty existential searches report their deterministic missing result.
Deleted/renamed units and failed rereads no longer retain old successful answers
as current findings.

`run.reviewed_checks` counts successful applicable answers, including carried
ones, and `run.coverage` reports their actual per-rule coverage. The wrapper's
receipt `checked` uses this count. Upstream `run.checked` remains available for
compatibility, but its formula multiplies fresh methods by the global question
count and should not be used to compare incremental coverage. Parser cache
statistics distinguish whole-revision reuse from per-content hits and misses.

Style review stores validated answers under `.perch/cache/style-v1/`, keyed by
the exact request body, rubric, parser/context contract, configured model and
normalized endpoint. Full-file hashes are provenance and freshness checks,
rather than reasons to discard an unchanged request after an unrelated edit.
Each reused row receives current metadata and retains the original answer's
provenance separately. Current discovery removes deleted declarations and
continues to report invalid files. Valid completed answers can survive a
transport interruption; source-stale or model-inconsistent runs seed nothing.
Concurrent publication is atomic and corrupt records become misses.

Both caches preserve negative, uncertain and below-target results. Reuse does
not establish a new model review. A moving model alias is not re-resolved on a
zero-request run; receipts disclose that limit and `--fresh` refreshes it.
Changing the configured model or endpoint invalidates answers. The corrected
semantic key has a new version, so older unsafe keys miss once. Legacy explicit
style receipts lacking endpoint identity are rejected; they are not silently
imported into the automatic cache.

## Verification

`npm run lint:verify`: **60 tests passed**, followed by the eight-law-rule wiring
gate. New controls exercise unchanged scans, imported-helper changes, isolated
same-file edits, renamed rules, changed model/endpoint/rubric, deleted/renamed
files, failed rereads, search scope/threshold changes, cache corruption,
transient parser failures, forced fresh answers, partial recovery, source
freshness, model drift and concurrent style cache publication.

The [full-inventory offline profile](perch-calibration/incremental-2026-09-26.json)
uses committed source at `0d23a4d` with the new tooling identified by hashes.
It builds a disposable Git fixture, supplies fixed valid answers locally and
checks unchanged result identities, coverage and exit status across all runs.
No provider is contacted and no credentials are copied. These are cache and
request-wiring measurements, not new semantic/style judgments or live latency.

| Full inventory | Cold, fixed answers | Warm unchanged | After documentation-only commit | Warm requests |
| --- | ---: | ---: | ---: | ---: |
| Semantic, 1,986 declarations | 7.94 s | 3.50 s | 3.69 s | 0 |
| Style, 2,345 declarations | 1.77 s | 1.48 s | 1.48 s | 0 |

The warm semantic scan carries 2,314 method/file answers and retains 59,203
applicable checks. Across a documentation-only commit, all 401 source analyses
are cache hits, with zero parser invocations. Style reuses all 2,345 answers;
its remaining cost is current inventory/context preparation and reporting.
Both commands retain the same 16 unparseable files and exit 1 for incomplete
coverage. Nothing in this change waives those failures or adjudicates historical
model findings. No Bend implementation, law, rubric or acceptance threshold was
changed.

Reproduce the offline inventory exercise with a new output path:

```sh
node scripts/profile-perch-incremental.mjs --output=/tmp/perch-incremental-new.json
```

Wall time includes cache/receipt writes, but excludes module import and fixture
construction. The cold run has no provider latency; compare it only as local
overhead. Prior complete live first-pass timings remain in the
[throughput report](perch-throughput-2026-09-26.md).
