# Perch context increment verification

2026-09-27, branch `campaign/perch-context`, base `3a162ab`.

The increment changes offline context assembly, explicit manifest selections,
tooling controls and documentation. No `src/*.bend`, existing gate assertion,
package source, or rubric text changed. The gate registration count increases
from 14 to 15, as required. No live provider, environment file, network fetch,
push, merge, rebase or other-worktree mutation was used.

## Fixed expectations and controls

The [literal contract](../../tests/perch-context/CONTRACT.md) was written before
implementation; its initial SHA-256 is
`3d49787a93b668a570304037c4984f89915aabd172b2183a72363295bc7ed651`.
The first 13 controls were also written before implementation. Two new fixture
expressions needed the seed parser's explicit operator annotation
`(x + 31337 : U32)`; their assertions and expected body-omission behavior did
not change. An integration fixture canonicalizes the macOS `/var` path alias
before comparing freshness paths. Existing tests and legacy request fixtures
were retained unchanged.

The package identity is fixed by literal review against the pinned seed's
`bend2/main.ts:481`: SHA-256 of sorted `sha256(file) path\n` lines, then the
first 32 hex digits. The independently written fixture oracle and the resolver
compute that rule separately. No publish command or network was needed.

The **23 clean/broken/held-out controls** cover transitive and cyclic types,
tiny byte budgets, both package layouts, actual member and root hashes, unused
license tampering, traversal and symlinks, forbidden environment members,
multiline signatures, nested colons, same-line bodies, law statements versus
proof fills, datatype retention, helper/caller overflow, exact UTF-8 bounds,
proof-entry chains, complete manifest coverage, offline dispatch, explicit
external stores, full-package freshness, package membership confinement,
encoded-state accounting, local symlink cycles and missing packages/laws.

The new gate independently inventories every current `src/*.bend` with the
pinned parser and compares its exact declaration set to preflight coverage.
The existing manifest test still checks all 30 files and every group's closed
local import inventory. New controls require every file to be selected in full
somewhere. The [fixed gate expectations](../../tests/perch-context/expectations.json)
retain the rubric identity, 48,000-byte cap and zero-blocker compiler result.

| Semantic mutant | Fixed rejecting witness |
| --- | --- |
| `summary-leaks-body` | Nested and inline signatures must exclude `g(x)` and literal `31337` bodies. |
| `unverified-package-accepted` | Tampering an unused LICENSE must reject an otherwise correctly named hash directory. |
| `truncation-marker-dropped` | A one-byte context budget must retain both truncation flags and its byte-limit reason. |
| `group-silently-over-bound` | UTF-8 source one byte beyond the bound must be unavailable and explicitly marked. |

All **4/4** preserve JavaScript value shapes, pass `node --check`, import the
real unchanged dependencies, and fail the original behavioral `ERR_ASSERTION`.
Syntax/import failures and harness failures do not count as kills. JavaScript
has no separate static type gate here; these are semantic tooling mutants,
not Bend compiler mutants or a new accepted source-language capability.

## Exact deterministic results

Both required commands ran with `BEND_NO_TELEMETRY=1` and exited 0:

```sh
BEND_NO_TELEMETRY=1 npm run -s gates
BEND_NO_TELEMETRY=1 npm run -s gates:verify
```

All **15/15 registered gates** passed. Counts below retain separate categories;
overlapping observations are not added into one assertion total.

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
| `perch-context` | 23 controls, 4 mutants killed, 17 available compositions, 425 distinct declarations, 945 group/declaration obligations, 0 blockers, 0 provider requests |
| `lint:verify` | 154 tests passed, 0 failed; all 8 law-rule wiring checks passed; provider results are local fixtures |
| `gates:verify` (wrapper suite) | 18 tests passed, 0 failed |

No new Bend laws were added. Existing complete proof checks remain in the
unchanged compiler/trust gates. Seed ⇔ evaluator ⇔ Wasm differential assertions
remain unchanged; there is no new compiler behavior requiring a new language
differential fixture. The new tooling observations have their own independent
literal controls and mutants.

The census needed **no approval update**: no source file, source import, or
feature class changed. The initial full run took 94.996334 measured seconds;
the final code's full rerun took 95.612649 seconds. Both runs passed
all 15 gates. These are gate wall times, not implementation time. Final logs
remain under ignored `.local/gates/run-xkhgsqey/`. The wrapper
suite was rerun after registration and again after the final code changes.

## Context result, freshness and limits

The [before/after table](perch-baseline.md) and
[machine-readable comparison](perch-context-comparison.json) cover each group.
On the same current compiler source, blockers fall from **374 to 0**, truncated
obligations from **366 to 0**, role-limited obligations from **475 to 0**,
unavailable compositions from **8 to 0** and oversized groups from **7 to 0**.
The historical main baseline (317 blockers) remains intact in the baseline
document. All five style axes remain unrated; no style pass is claimed.

The versioned policy preserves legacy requests and assertions. Seven explicit
group selections divide the old oversized full-source obligations across the
existing mechanisms; the original local closure inventories are unchanged.
Every selected file is supplied in full and every compiler file is selected
somewhere. Hash-pinned interfaces disclose omitted implementations and proof
bodies; live judges must respect that evidence boundary.

The explicit `--package-store="$HOME/.bend/lib"` supplies the verified published
OutputBuilder closure. Current repository package source has advanced past its
publication, so using only that candidate correctly leaves a digest-mismatch
gap. The gate runner supplies its own offline frozen local package copy.
No package source was edited or silently accepted as the old hash.

Declaration source context remains bounded by 48,000 bytes; encoded state by
60,000 bytes, including the task. Helpers/callers over their body caps enter as
interfaces with actual classifications. No truncations remain on this snapshot.
`checking` has only 97 source bytes of headroom. Future larger sources may need
new explicit group boundaries; the gate will reject an oversized composition.

Source and package-member hashes, complete package membership, interface hashes,
manifest/task/rubric identities and per-file representations are retained in
the raw receipts. The [new gate receipt](../../tests/perch-context/receipts/context.json)
is owned by this increment. All shared compiler/store receipts remain untouched:
the runner regenerated them only in scratch. Its two existing semantic receipt
drifts are `/inputs/scripts~1run-wasm.mjs` in the enum and fielded Wasm receipts,
from base commit `3a162ab`; refreshing those belongs to the coordinator.

Next: the coordinator reviews this increment, refreshes shared receipts after
merging, and runs live semantic/style qualification with the manifest's policy
and an explicit verified package store. Offline structural success does not
predict the model's ratings.
