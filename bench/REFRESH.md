# bench-2 refresh, 2026-09-29

The branch started clean at `36e7fcb4`, with the completed 2026-09-27 benchmark
increment and no local handoff. Its work is preserved. This refresh changes
only `bench/`; the compiler, package boundaries, frozen upstream fixture suites
and timed hillclimb inventory remain unchanged.

## Independent edge controls

The [contract](fixtures/refresh/CONTRACT.md) and
[seed observations](fixtures/refresh/expectations.json) were committed in
`17b37de4` before Knot probing. There are 24 new programs, six per family:
Peano parity, last-cell traversal, flip chains and wraparound enum matches.
Empty/singleton inputs, odd/even lengths, lengths on either side of 32 and enum
width 255 produce both zero and nonzero results. Every source passed the seed
checker; all 48 seed native/Bun executions matched the literal results.

`bench:verify` now checks these controls using the existing guarded compiler
and evaluator builds. Both lanes compile all 24 programs and agree with the
frozen seed values in 48 evaluator observations and 48 guarded Wasm batches.
All 24 emitted module pairs are byte-identical. The probes found **no false
acceptance or false Invalid**. [Current edge receipt](receipts/refresh-edges.json).
The seed build wrapper imports the unchanged fixture as F and adds Base, which
the seed requires for emitted builds; qualified outputs are retained verbatim.

The refresh at `035fa0d9` passed 53 unit tests, the original two-lane
smoke, 201 inventoried programs, 31 measured programs, 38 runtime batches of at
least 10 ms, and four seed-type-correct mutants killed in both lanes. Coverage
remains 157 Unsupported, 13 Invalid and five known seed-valid D4 discrepancies.
These are unchanged compiler-owner findings, not newly discovered rejections.
There is no new optimization or performance comparison.

Offline Perch structural preflight covered 160 declarations in the 24 new
files, with zero provider requests and an available selected composition.
Six contexts were truncated: Flag in inline-2, inline-3, inline-31 and inline-33,
and flip in inline-31 and inline-33. Exit 3 records that attention requirement.
Compression, Delight, memetic identity, Anticipation and Payoff remain unrated;
this is **not a style pass**. [Preflight receipt](receipts/refresh-preflight.json).

## Decisions and merge boundary

The implementer read COMPILER-CAMPAIGN.md (D1–D26), COORDINATOR-STATE.md
(2026-09-29 17:00 PT) and the refresh prompt from main. This explicit dispatch
finishes the bounded refresh; D13 still parks broader benchmark development.

- **D7:** the new seed expectations were frozen before the Knot probes. No
  existing assertion, source-language expectation, law or mutant was weakened.
- **D21:** no required source-language law was added, removed or left open by
  bench-2. Its concrete controls make no universal-proof claim. The open
  obligations owned by nest and the VM track remain required in those increments.
- **D24:** the benchmark does not implement Case, requests or IO. Default-arm
  semantics belong to the pending core/VM integration; no local change applies.
- **D26 items owned by bench-2: none.** `bench/expectations.json` pins literal
  values for the generators and second-descent, not Knot phase/code verdicts.
  The new manifest likewise pins seed observations, not stopgap diagnostics.
  Its programs use existing constructor rows, without a Default, dotted binders,
  layout extensions or unmodeled term suffixes. Nest therefore supplies no
  contradictory bench-owned verdict that needs re-freezing.
  The six imported fixture suites retain their owners' pins. At integration,
  apply D26 to collisions in those suites: Checked for a seed-accepted form the
  merged tree checks, Invalid only for the seed-rejected reason named, otherwise
  Unsupported. Seed values never change. The five closure D4 discrepancies
  remain visible pending the compiler-owner merges.

**No merge was performed.** The refresh prompt asks for a main merge, while
the direct executor instructions prohibit merging other branches and reserve
integration for the coordinator. Consequently this branch does not contain
main's gate-runner upgrades or additional gates. The counts below qualify this
branch's 14 registered gates, not main's expanded registry.

Coordinator work remaining: merge main (5571625f or later), resolve shared
receipts using main's copy, integrate the gate runner and new registered gates,
run the expanded gate registry, refresh shared receipts, review/register
`bench:verify`, and run the authorized live Perch semantic/style reviews.
Preserve nest-first merge order and the standing diagnostic rulings. These
coordinator-only actions do not block implementer completion.

## Deterministic gates

The receipt-portability revalidation passes all 14 registered gates, exit 0, in
**743.113962 seconds**, on the repair committed as `c44b04fb`. Its exported
snapshot includes the new edge corpus, runner and portable serializers.
Receipt comparison reports **63 identical,
17 volatile-only and 0 semantic** differences. No shared receipt was refreshed.
[Fresh gate receipt](receipts/refresh-gates.json) retains the earlier
422.539081-second run's hashes and harness identity under `previousRun`.
The exact fresh counts are
below; categories overlap and are not summed.

| Gate | Passed counts |
| --- | --- |
| frontend | 14 seed fixtures, 28 parser observations, 24 boundaries, 4 boundary laws, 6 classification laws, 4 semantic mutants; 12 classification fixtures in 2 lanes, 7 classification mutants, 72 downstream rejection observations |
| checker | 49 fixtures, 98 lane observations, 10 budget probes, 2 bounds / 16 bound observations, 7 mutants |
| structural | 16 fixtures, 64 lane observations, 4 bounds, 7 mutants |
| fields | 40 fixtures, 240 phase observations, 36 budget probes, 6 host boundaries, 2 bounds / 12 bound observations, 9 mutants |
| wasm | 25 programs, 90 seed calls, 2 execution lanes, 64 rejection pairs, 44 boundaries, 7 mutants |
| wasm-trust | 3 entries, 0 proof holes |
| fields-trust | 4 entries, 0 proof holes |
| structural-trust | 2 entries, 0 proof holes |
| owned-store | 3,532 cases in 2 lanes, 15 literal witnesses, 6 mutants |
| flat-store | Each lane: 13,621 observations, 3,534 instances, 2 installed boundary states, 7 lifecycle checks; 2 lanes, 9 mutants |
| recursion | 19 seed fixtures, 114 phase observations, 4 fuel probes, 3 mutants |
| fields-wasm | 8 fixtures, 32 seed calls, 64 evaluator observations, 64 Node observations, 50 frozen enum-byte checks, 30 boundaries, 4 mutants in both lanes, 5 checked laws |
| census | 30 compiler files, 425 declarations, 40 feature classes |
| lint:verify | 127 tests, 8 law-rule wiring controls, no live provider calls |

`gates:verify` passes all 18 tests. `census:approve`, then `census`, regenerated
the inventories byte-identically. Approval summary: **empty; no new files,
declarations, widened classes or imports**. No census policy change is needed.

Commands use `BEND_NO_TELEMETRY=1`, Bun `--no-env-file` for benchmark/seed
calls, and the installed Xcode toolchain:

```sh
export BEND_NO_TELEMETRY=1
export TMPDIR=/private/tmp/knot-codex/bench-2/scratch/
export SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk
export PATH=/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin:$PATH
npm run -s bench:verify
npm run -s gates -- --jobs 1 --timeout 1800
npm run -s gates:verify
npm run -s census:approve
npm run -s census
npm run -s lint:style -- --preflight --json --task=bench/fixtures/refresh/CONTRACT.md bench/fixtures/refresh/*.bend
```

No environment file was read or copied, no provider or live Perch call was
made, and no other worktree was modified. Shared receipts remain coordinator-owned.

## C4 receipt path repair

The pre-review's five executor conditions were confirmed and repaired. Receipt
serialization now replaces checkout, seed, package-cache and Node installation
paths with the tokens documented in [README.md](README.md). Gate completion
paths identify the exported tree directly, without its temporary run directory.
The helper is used by benchmark results and both verification receipt writers;
the explicit-path migration command is `node bench/normalize-receipts.mjs`.
Execution paths and worker requests remain usable local paths.

An independent recursive comparison of the five original and migrated JSON
payloads checked identical keys, array lengths and every non-path value. Only
the following string values changed during migration:

| Receipt | C4 fingerprint | Changed strings | Host hits before → after |
| --- | --- | ---: | ---: |
| hillclimb-after.json.gz | 78ee9daa6c137bc784d7 | 4,296 | 8,590 → 0 |
| hillclimb-before.json.gz | a33a7130eaa41123721c | 4,296 | 8,590 → 0 |
| refresh-edges.json | 3c4245db720aaf29ddae | 336 | 672 → 0 |
| refresh-gates.json | 51c3e05fd642236be7fc | 5 | 5 → 0 |
| validation.json | 50c103ab883f833da942 | 1 | 3 → 0 |

Both historical hillclimb results still validate. Recomputing their comparison
reproduces all **226 rows and verdicts** exactly, including the original
regressions. The original payload hashes in `comparison.json` retain their
meaning as hashes of the original ignored results; the normalized committed
copies have these SHA-256 payload identities:

| Receipt | Original payload SHA-256 | Portable payload SHA-256 |
| --- | --- | --- |
| hillclimb-before.json.gz | f0e428d8a0ed9964ec55cbbad45262306fb11879d2ad2606db4ff86a86cea90d | 1a64ebdf76f18a16a909dd09db4237dc59fe424e0686b88bbff4c87f405eb7d8 |
| hillclimb-after.json.gz | ae7cf9e445297d6a7b71957f4c62c2644cedf8d95938fd9ac4126ba7af90b488 | e051ae0444e4534e3f06fbb10ebf8693f1c3f58368501c5da4b18d58739e45db |

Four new tests check identical serialization across two checkout locations,
unchanged execution state, prefix boundaries, temporary export paths and the
independent C4 pattern across every benchmark receipt. Fresh `bench:verify`
passes **57 unit tests**, the original two-lane smoke, the unchanged
**201-program inventory / 31 measured programs / 38 runtime batches**, and
all **four mutants in two lanes**. It regenerated the edge and verification
receipts with the new harness identities. The **24 edge programs / 48 compiler,
evaluator and Wasm observations / 24 byte-identical pairs** still pass.
All 26 frozen edge-corpus files are byte-identical. `gates:verify` passes
**18 tests**. Full registry revalidation passed with every gate's exact counts
unchanged from the earlier run, as listed above. Shared receipts were not
refreshed. D21, D24 and D26 dispositions and the coordinator integration
boundary remain unchanged.
