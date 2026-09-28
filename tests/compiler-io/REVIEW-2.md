# IO host review 2 — verified repair

All three confirmed findings are fixed within the IO-host increment. Main at
`ec43747` was merged in `b129047`; independent review controls and three-lane
seed witnesses were fixed in `8eecca0` before changing the host. D14's VM calls
the same `knot_io` ABI; no native Wasm lowering representation crosses it.

The original 40 fixtures, `expectations.json` and host `PLAN.json` are unchanged
from `6051e37`. The original expectation SHA-256 remains
`118c922f459aa2b968cd69ed886eca3e305349d56f61c1e45a92423d22047806`.
The extension lives under `host/`; no compiler assertion or budget changed.
Detailed current observations, sources and mutants are in [host.json](receipts/host.json).
The full verification and pre-repair evidence are in [review-2.json](receipts/review-2.json).

## Findings

| Finding | Disposition | Evidence |
| --- | --- | --- |
| Case variants bypass `.env` refusal | **Fixed** | Each component is lowercased before testing `.env` / `.env.*`, before any open. All 21 path/mode controls report `HostFailure io sandbox`, exit 5, preserving every dummy byte and directory entry. The previous host opened `.ENV` in `w` and truncated the dummy; `.env` and `.ENV` are confirmed to be the same inode. Restoring case-sensitive filtering is killed in all three modes. |
| JS-lane memory faults can become frozen expectations | **Fixed** | `regen.execute` rejects the marker in stdout, stderr or merged output as `Exhausted seed memory-fault`. Twelve controls cover streams, exits 0/1 and both `--write` passes; previous expectation bytes survive every refusal. Two ordinary exit 0/1 controls still pass. The guard-removal mutant is killed. No existing oracle input faults; D14 selects native for compiler-sized C1 inputs. |
| Empty `write_bytes` on `r` returns errno 9 | **Fixed** | The direction check now requires nonzero byte length, after the invalid-element check. File, empty file, directory and `.` agree with all three seed lanes (12 runs) and four independent Wasm runs. Restoring unconditional errno 9 is killed on all four. |

The one new Bend fixture, [empty-write.bend](host/empty-write.bend), has seven
definitions and no new laws. It writes `[]`, reports the Result, reads 64 bytes,
closes and reports again. Its expectations are reviewed literals, separately
witnessed by the pinned seed before repair. The sandbox probes use only dummy
files created inside fresh private directories; no real `.env` was read.

The seven path spellings are `.env`, `.ENV`, `.Env`, `sub/.ENV.local`,
`sub/.Env.local`, `SUB/.env.LOCAL`, and `./.eNv`; each runs under `r`, `w`, `a`.
These extend the original lowercase/nonexistent-path control.

The seed-lane finding was also reproduced outside the oracle suite: the
unchanged `mini-driver.bend` on a dummy 40,000-byte ASCII input faults on the
interpreter lane with exit 1 and a zero-byte output. Its native seed build
prints `Built\t40000`, exits 0 and writes 40,000 bytes. The guarded regenerator
refuses the actual interpreter fault. This is a lane-artifact receipt, not a
new expected program outcome.

## Full gate table

`BEND_NO_TELEMETRY=1 npm run -s gates -- --jobs 2` exits **0**, all **18/18**
registered gates pass. The run took 234.074845 seconds on this host. Counts
below come from the fresh runner receipts, not historical results.

| Gate | Exact passing coverage |
| --- | --- |
| frontend | 14 fixtures; 28 lane observations; 24 boundaries; 4 mutants. Classification extension: 29 fixtures, 174 downstream observations, 7 mutants. |
| checker | 49 fixtures; 98 lane observations; 10 budget probes; 16 bound observations across 2 bounds; 7 mutants. |
| structural | 16 fixtures; 64 lane observations; 4 boundary pairs; 7 mutants. |
| fields | 40 fixtures; 240 phase/lane observations; 36 budget probes; 6 host controls; 12 bound observations across 2 bounds; 9 mutants. |
| wasm | 25 programs; 90 independent reference calls in 2 execution lanes; 64 rejection pairs; 44 boundaries; 7 mutants. |
| wasm-trust | 3 entries; 0 proof holes. |
| fields-trust | 4 entries; 0 proof holes. |
| structural-trust | 2 entries; 0 proof holes. |
| owned-store | 3,532 cases in 2 lanes; 15 literal witnesses; 6 mutants. |
| flat-store | Per lane: 13,621 observations, 3,534 instances, 2 installed boundary states, 7 lifecycle checks. 2 lanes; 9 mutants. |
| recursion | 19 fixtures in 2 lanes; 4 fuel probes; 3 mutants. |
| fields-wasm | 8 fixtures; 32 independent reference calls in 2 lanes; 50 enum-preservation checks; 30 boundaries; 4 mutants. |
| census | 30 compiler files; 437 declarations; 41 feature classes. |
| perch-context | 41 offline tests; 33 fixtures; 8 mutants; 17 bounded groups with 957 group/declaration obligations and no structural blockers. |
| lint:verify | 168 tests; 8 law-rule wiring controls; no provider requests. |
| bootstrap | 624/624 reference files agree; C1 conformance 57/57 (25 programs, 90 calls, 32 rejects); 9 mutants. 8 stages: 2 reached, 2 explicitly blocked, 4 not run. |
| classification | 17 fixtures; 6 mutants. |
| io-host | Original 40 seed fixtures / 109 seed runs; 20 Wasm fixtures / 86 runs; 6 CLI runs; 19 host controls; 6 mutants; both 100,000-bind directions. Review extension: 1 fixture, 12 seed runs, 4 Wasm runs, 21 path controls, 14 oracle controls, 3 mutants. |

`BEND_NO_TELEMETRY=1 npm run -s gates:verify` also exits **0**: **18/18** runner
tests and six semantic mutants. All nine existing proof entries print
`All terms check.`; the new fixture's seed check does too. No law was added.

The initial merged-tree run failed frontend because the seed could not discover
clang; the other 17 gates passed. The final two-worker run passed without
changing any assertion, timeout or compiler budget. That earlier failure is
retained in the validation record.

## Preflight and receipts

Offline `node scripts/perch-style.mjs --preflight
tests/compiler-io/host/empty-write.bend --task=tests/compiler-io/host/REVIEW-2.md`
reports **7 declarations**, **0 structural blockers**, **0 truncated contexts**,
complete role context and an available composition (1,539/48,000 bytes). The
2,372-byte task is available. Provider requests: **0**. Live semantic/style
ratings, including all rubric axes, remain the coordinator's work; this is not
an automatic style pass.

The direct IO receipt is byte-identical to the full-run receipt. Of 85
regenerated artifacts, **64** are identical, **19** volatile-only, and **2**
semantic. The semantic changes are only bootstrap `progress.json` and
`reference.json`: the new fixture raises its corpus from 623 to 624. Those
shared receipts remain unchanged in the worktree for coordinator refresh.

The census was regenerated with `npm run -s census`, never hand-merged.
`npm run -s census:approve` emitted only a blank summary: no new compiler
declaration, source file, import or feature class needed approval. The existing
unrecognized IO, sugar and Perch-context suite warnings remain explicit; host
tests do not qualify a new compiler capability.

## Limits and next increment

The host remains a synchronous, private-directory ABI; the existing filesystem
rename race and bounded memory/errno surface remain as documented in
[IO-ABI.md](../../docs/compiler-campaign/IO-ABI.md). Tests use a hand-assembled
Wasm effect interpreter, not Knot-produced images. An IO evaluator lane does
not exist here, and bootstrap's passing harness does not mean self-hosting.

The VM owner should connect checked image execution to `knot_io`, run all 103
original agree runs plus the four new empty-write cases, and preserve the
frozen Invalid/Unsupported checks. The compile-cli owner must replace the
post-write `List.length(bytes)` and audit output-sized non-tail traversals
before increasing budgets. Compiler-sized C1 inputs use native under D14;
JS lane faults remain inconclusive. No compiler source or budget changed here.
