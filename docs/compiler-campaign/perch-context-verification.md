# Perch context review round 2 verification

2026-09-27, branch `campaign/perch-context`. Review base `6796108`;
current main `fa31fec` was merged as `f4eb462` before these repairs. Both
review-log entries were retained, and the gate runner now requires
`perch-context` by name. Its 18 wrapper controls pass.

The repairs change offline review tooling, parser observations, its controls,
and receipts. No compiler source, published package source, rubric, quality
target, accepted-language contract, or existing compiler-gate assertion changed.
No provider or network request, environment-file read, push, rebase, history
rewrite or other-worktree mutation was used. Live review remains the coordinator's
work. The requested merge is the only branch integration in this increment.

## Confirmed findings and repair

- Package members use `0x<hash>/<member>` in interface headers, representations,
  file lists, provenance, source byte counts and request identities. Filesystem
  locations remain private local read handles. Verified member bytes establish
  identity; `RELEASE.json` locates a candidate closure and is not a published
  member. This also makes the two supported store layouts agree.
- Default candidates are `packages/`, followed by `--package-store` if supplied,
  otherwise `BEND_LIB`, otherwise `~/.bend/lib`. All members still need the
  pinned seed publish-hash check; missing/tampered packages remain unresolved.
- The complete legacy composition instruction is retained verbatim. The warning
  against inferring collaborator implementations or checked proofs is appended.
- `parse_def` reports its position immediately after consuming the body colon.
  The adapter converts it to a UTF-8 `body_start`; interface extraction and
  signature dependency filtering use that endpoint. No signature lexer remains.
- Bare relative paths are local imports and enter manifest closure checks.
  Other hash lengths are recognized as package imports but remain explicitly
  `unsupported-package-identity`; they are never searched as local paths.
- The gate asserts the retained 475-to-zero role result and runs the literal
  manifest command twice, requiring byte-identical compressed reports.
  Composition `state_sha256` is now exposed in offline receipts.

The original verification record's claim of only two semantic receipt drifts
was incomplete: the uncommitted new receipt had not been compared after commit.
Its old after receipt also embedded store paths. This round replaces the gate,
after and comparison receipts. The original before receipt remains unchanged.
Current `main` already refreshed the two shared Wasm receipts; this increment
leaves all existing shared gate receipts untouched.

## Fixed fixtures and mutants

The initial [contract](../../tests/perch-context/CONTRACT.md) is retained with the
review decisions made explicit. [Review expectations](../../tests/perch-context/review-expectations.json)
fix literal heads, the complete legacy instruction and zero-count targets.
Eight targeted regressions failed before the implementation fixes. The new
[signature fixture](../../tests/perch-context/fixtures/signatures.bend) passed
the pinned seed checker before the fixes; a final apostrophe-in-body control
also passes. The complete fixture has 11 declarations and prints
`All terms check.`; no new law declaration or proof hole was introduced.

The **33 controls** retain all original semantic/byte-bound checks and add:
character literals in heads and bodies (`'''`, `':'`, `')'`, escaped and Unicode
characters); dependent/existential return types and their `width` dependency;
the anti-anchoring instruction; bare/long-hash import classification; BEND_LIB
and home defaults with tampering; equal identities across checkout/store
locations and store layouts; and the parameter-type preflight crash regression.
The location control compares complete declaration and composition candidates,
including source bytes and `state_sha256`.

A standing parse-back oracle replaces interface body markers with `?h`, then
requires a successful parse and exactly the original declaration names. It
covers **32 files and 411 definition/law heads**: every compiler source, its
reachable published Bend member and the adversarial fixture. These temporary
holes are a syntax oracle only; no incomplete interface is claimed type/proof
accepted. The separate fixture passes the seed's complete checking entry.

| Semantic mutant | Rejecting witness |
| --- | --- |
| `summary-leaks-body` | Nested/inline heads exclude their body text. |
| `unverified-package-accepted` | An unused LICENSE edit invalidates the package. |
| `truncation-marker-dropped` | A one-byte budget retains both truncation flags. |
| `group-silently-over-bound` | One byte beyond the UTF-8 cap is unavailable. |
| `store-path-in-identity` | Members have import identities in different stores. |
| `anti-anchoring-omitted` | The full legacy instruction must be a verbatim prefix. |
| `binder-colon-truncates-head` | The existential head retains its type and `width` closure. |
| `default-store-omitted` | An unflagged resolver finds and verifies BEND_LIB. |

All **8/8** preserve JavaScript value shapes, pass `node --check`, and fail
behavioral `ERR_ASSERTION` controls. Syntax, import and harness failures do not
count as kills. These are semantic tooling mutants; no new compiler capability
requires a new evaluator/Wasm fixture. Existing seed/evaluator/Wasm conformance
and complete proof gates remain unchanged.

## Deterministic gates

Both required commands exit 0 with `BEND_NO_TELEMETRY=1`:

```sh
BEND_NO_TELEMETRY=1 npm run -s gates
BEND_NO_TELEMETRY=1 npm run -s gates:verify
```

All **15/15 gates** pass. Counts below preserve independent categories rather
than summing overlapping observations.

| Gate | Exact passing counts |
| --- | --- |
| `frontend` | 14 reference fixtures, 28 parser-lane observations, 24 boundary observations, 4 boundary laws, 6 classification laws; 12 classification fixtures in 2 lanes, 72 downstream rejection observations; 4 original + 7 classification mutants killed |
| `checker` | 49 fixtures, 98 checked observations, 10 depth probes, 16 catalog-bound observations, 7 mutants killed |
| `structural` | 16 seed fixtures, 64 phase/lane observations, 4 boundary pairs, 7 mutants killed |
| `fields` | 40 fixtures, 240 native/Bun phase observations, 36 budget probes, 6 host probes, 12 level/inspection observations, 9 mutants killed |
| `wasm` | 25 programs, 90 independent reference calls in each of 2 lanes, 64 rejection pairs, 44 boundary observations, 7 mutants killed |
| `wasm-trust` | 3 complete entries, 0 proof holes |
| `fields-trust` | 4 complete entries, 0 proof holes |
| `structural-trust` | 2 complete entries, 0 proof holes |
| `owned-store` | 3,532 cases, 15 literal witnesses, 2 execution lanes, 6 mutants killed |
| `flat-store` | Per native/Bun lane: 13,621 observations, 3,534 Wasm instances, 2 installed boundary states, 7 lifecycle checks; 9 mutants killed; identical 1,050-byte module |
| `recursion` | 19 seed fixtures, 114 phase observations, 4 fuel probes, 3 mutants killed |
| `fields-wasm` | 8 fixtures, 32 seed calls, 64 evaluator and 64 Node observations, 50 frozen enum-byte checks, 30 boundary probes; 4 mutants killed in both lanes; 5 existing checked laws |
| `census` | 30 source files, 425 declarations, 40 feature classes; current approved inventory |
| `perch-context` | 33 controls, 8 mutants killed, 1 seed signature check, 2 byte-identical preflights, 17 available compositions, 425 distinct declarations, 945 group/declaration obligations, 0 blockers, 0 provider requests |
| `lint:verify` | 168 tests passed, 0 failed; all 8 law-rule wiring checks passed; provider results are local fixtures |
| `gates:verify` (wrapper suite) | 18 tests passed, 0 failed |

The first review-round runner attempt failed census because its metadata pinned
the previous parser/adapter hashes, and lint because a freshness refactor changed
an existing mutant's exact replacement site. The three census inventories were
regenerated with only those two hash fields changed. `census:approve` printed
an empty summary (one newline); `approved.json` is unchanged. There are no new
source files, declarations, imports or feature classes to approve. The original
freshness mutant and all existing compiler assertions remain unchanged.
A separate direct lint attempt hit the sandbox's unwritable global parser-cache
lock; the runner's private offline cache completes the full suite.

The two successful full runs used the same unchanged working-copy inputs:
`.local/gates/run-mi2jlhto/` (four workers, 114.659365 measured seconds) and
`.local/gates/run-lho419io/` (one worker, 519.745557 measured seconds). Their
entire `normalized` summary objects are equal, and **all 81 normalized receipt
files are byte-identical**. The canonical JSON summary SHA-256 is
`533fac3284467268a016b87d693cdcd7b40471149fa6e98aeba407ae4fae2805`.
These are measured gate wall times, not compiler performance measurements.

Both runs classify `tests/perch-context/receipts/context.json` as **identical**
to the direct gate's tracked working-copy receipt, not merely volatile-only.
Its normalized digest is
`092e792f4e245950fa5ae86b07799b169f709b52db3b4335dfe7a3ff1e7d129d`;
its actual committed-byte digest is
`8f9555460069f5a06f3043b2ca5e3666e43027076f7e66ce646f0efef5ac3219`.
Across the complete gate set: **64 identical, 17 volatile-only, zero semantic
receipt drifts**. No shared receipts were refreshed or written in the worktree.
The changed context gate receipt is the increment's own artifact.

An intervening four-worker repeat (`run-01fngh2f`) exhausted the existing native
build limits in frontend, fields and Wasm; their two dependent trust gates were
blocked. It is retained as a failed run, not a pass or Invalid-language result.
The host load average was 43.30 when inspected. The context gate still produced
an identical receipt in that run. The serial retry changed no assertion or
budget and completed all gates. Only final verification documentation changed
after the successful-run comparison; executable input hashes remain recorded
in the context receipt.


## Preflight and remaining limits

The literal acceptance command, without `--package-store`, exits 0:

```sh
BEND_NO_TELEMETRY=1 node scripts/perch-style.mjs --preflight \
  --manifest=docs/compiler-campaign/manifest.json --output=<fresh-path>.json.gz
```

It covers **17/17 available compositions, 425 distinct declarations and 945 group
obligations**, with **zero blockers, truncations, role-limited obligations,
unresolved composition references, oversized groups and provider requests**.
The full [before/after table](perch-baseline.md) and
[comparison receipt](perch-context-comparison.json) retain the same compiler
source in both arms: 374 blockers → 0; 366 truncated obligations → 0;
475 role-limited obligations → 0; eight unavailable compositions → 0;
seven oversized groups → 0. Seven package-bearing compositions lose 26 host-prefix
bytes each; the package interface is 708 bytes regardless of store location.
The gate, after receipt and comparison agree on all 17 group compositions.

The new 11-declaration fixture passes `--preflight --context=interfaces-v1`
with zero blockers and a 646-byte composition. The required bare `--preflight`
command retains legacy policy and reports one `Tag` caller-cap truncation
(exit 3, no provider). That legacy limit is disclosed, not waived; the compiler
manifest explicitly selects the repaired policy. Neither run has explicit task
context for a potential-profundity judgment.

No live ratings were requested. Compression, Delight, memetic identity,
Anticipation and Payoff remain **unrated**. Interface syntax and signature
closure do not establish unseen behavior or checked proof bodies. The largest
compiler composition (`checking`) remains 47,903/48,000 bytes, with 97 bytes of
headroom. Named packages, non-publish hash lengths and absolute imports remain
explicit unresolved/unsupported contexts. A verified default package store
must exist; there is no network fallback.

Next: coordinator review/merge, then live semantic and style qualification using
the unchanged rubric and the manifest's `interfaces-v1` policy. Any shared receipt
refresh after integration remains the coordinator's responsibility.
