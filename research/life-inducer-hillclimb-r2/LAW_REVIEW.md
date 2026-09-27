# Bounded law review: R2 Life contract and independent gates

This packet reviews the fixed specification and gate for two public operations,
prepared for the frozen v3 experiment and finalized after its user-requested stop.
The source and receipt index below identifies the completed observations.
Helpers are outside the declared API, not hidden by claimed access controls.
This is research, not package publication.

R2 planned 30 fresh trajectories: 15 GPT-6 Astra/low and 15 GPT-5.6 Sol/xhigh,
capped at three rounds and one compiler-diagnostic repair per round.
No old contexts/winners are supplied; later rounds receive their own history/feedback.
See [protocol and availability amendment](PROTOCOL.md).

## Domain, observations and defining laws

    step(width: U32, height: U32, cells: List<&2,U32>) -> List<&2,U32>
    evolve(turns: Nat, width: U32, height: U32, cells: List<&2,U32>) -> List<&2,U32>

Dimensions are in 0..32; exactly width*height binary cells occur in row-major order.
Outside cells are permanently dead: no wrapping. The complete ordered result,
including dead positions and length, and Node/Bun input-list preservation are observed.
There is no hidden state, capacity, identifier lifetime, IO or fallible result.
Wrong lengths, nonbinary cells and out-of-domain dimensions are unspecified.

For position i, let n count its eight neighbors in the OLD board, excluding i.
`step(c)[i] = 1` iff `n = 3` or (`c[i] = 1` and `n = 2`); otherwise it is 0.
All positions update synchronously. Shape and binary range are preserved.
`evolve(0,w,h,c) = c`; `evolve(n+1,w,h,c) = evolve(n,w,h,step(w,h,c))`.
`evolve(b,w,h,evolve(a,w,h,c)) = evolve(a+b,w,h,c)`; empty boards stay empty.
These are intended behavioral laws, not claimed universally proved equations.

The domain is inhabited: 0x7 has `[]`; live 1x1 `[1]` dies; 2x2 `[1,1,1,1]` survives.
The 3x3 horizontal blinker
`[0,0,0,1,1,1,0,0,0]` becomes `[0,1,0,0,1,0,0,1,0]` and returns after two
steps. A 3x3 board live at (0,0),(1,0),(0,1) births (1,1), retaining the corner
block. These witness identity, death, survival, birth, boundaries and iteration.

| Public observation | Fixed independent checks |
| --- | --- |
| `step`: ordered next board, dead exterior, shape, binary range, input preservation | One-turn corpus entries through the checked public wrapper on Node and Bun |
| `evolve`: zero identity and exact repeated stepping | Zero/two/four/eight-turn corpus entries on Node and Bun; 28 selected native full-board observations also include one turn |
| Composition of `evolve` | 21 cases per Node/Bun: three then four turns equals direct seven turns AND independent seven-turn evolution |

## Oracle independence and finite coverage

The frozen [oracle/fixtures](../life-blueberry/gates/fixtures.mjs) import no candidate:
a set of live positions contributes in-bounds neighbor counts to a map, then
EVERY position is reconstructed. The abstraction relation is full-board equality.
Each initial fixture's reference step is crosschecked by dense coordinate enumeration.
Explicit block, blinker, translated glider and corner patterns are asserted.
This crosscheck is not a proof of either oracle.
The [runner](../life-blueberry/gates/run.mjs) rejects wrong length/nonbinary output
and compares every position in complete decoded lists, rather than a checksum.

A complete pass requires 1,537 fixture observations plus 21 composition checks
under EACH of Node and Bun, and 28 native observations.
All binary boards are exhausted at 0x0, 0x7, 7x0, 1x1, 1x5, 5x1, 2x2, 2x3,
3x2 and 3x3 for one and two turns. Other cases include canonical patterns and
seeded 4x7, 7x4, 8x8, 12x12, 16x16 and 32x32 boards. Calls exercise turns
0,1,2,3,4,7,8. Native cases cover selected empty/small/canonical/generated
boards through width 8, comparing full nested lists. All 32x32 states, arbitrary
Nat turn counts and invalid inputs are not exhausted. No GPU or speed claim is made;
each 60-second process limit is operational, not a complexity guarantee.

## Saved semantic controls

The [preflight summary](../life-inducer-hillclimb/preflight/behavior-controls/summary.json) records
a historical good source passing all three backends and three mutants passing
the pinned checker and JS generation before Node rejects their outputs.
Every mutant's failures below are actual board mismatches with input preserved,
not parse/type errors, timeouts, malformed lists or harness crashes. The frozen
evaluator stops after Node failure; no Bun/native mutant result is implied.

| Control | Witness and observed Node rejection | Saved receipt |
| --- | --- | --- |
| Identity | Live singleton is retained rather than dying; 1,455 fixture and 20 composition mismatches | [identity](../life-inducer-hillclimb/preflight/behavior-controls/identity/behavior.json) |
| Extinction | Thin 1x5 `[1,1,1,0,0]` loses its required middle survivor; also breaks live zero-turn identity; 1,025 fixture and 19 composition mismatches | [extinction](../life-inducer-hillclimb/preflight/behavior-controls/extinction/behavior.json) |
| Always one step | Ignores turns; the blinker after three-then-four calls is horizontal while direct seven/reference is vertical; 553 fixture and 20 composition mismatches | [one-step](../life-inducer-hillclimb/preflight/behavior-controls/one-step/behavior.json) |

Control SHA-256s: identity `f763be8acfdd544d5a4b69602cb49bc04d1f969201ff609a4d8ba60f2ad259e4`; extinction `f380d92d7f7ac435e32eca46e76665696dc0728e1f9caf0ebf94b2cf9ba67f8a`; one-step `ead72a74b11b54a515b7d58f8437dd4445622177649b4ac4c71fb81aec282ca4`.
The [preservation manifest](../life-inducer-hillclimb/preflight/behavior-controls/preservation.json)
locates byte-identical raw receipts. Controls establish no new candidate's result.

## Proof and acceptance boundary

There is NO universal behavioral proof or completed Bend `LAWS`/`PROOF` artifact.
Acceptance requires the Bend 2.0.29 checker, including quantity/termination checks,
plus finite behavior gates. Base, the seed compiler and CPU runtimes are trusted.
Only Base imports are permitted; new axioms, holes, unsafe/foreign code are excluded.
The [locked adapter](gate.py) reuses the frozen evaluator's behavioral assertions,
changing lock/work paths and recording transport; [input-lock.json](input-lock.json)
pins oracle, runner, compiler and review tooling. Oracle SHA-256: `c04bbe26aaec07a9227afffcc57e9e720f5122d9b67e3a18b29ecf1a5c79ce9d`.

Current Perch v3 adds conditional Galaxy-brain and Anticipation/Payoff targets
to the three style axes. All required per-declaration assessments and clean
source review are necessary for the experiment's full-pass label, independently
of behavior. These advisory judgments are not proofs or guarantees of human taste.
Missing coverage, stale/truncated context or provider failure cannot
establish a pass. The parent's final source/receipt index must identify exactly
which submitted bytes passed which gates; planned trials are not passing trials.

## Observed submissions at the user-requested stop

[The source/receipt index](interrupted-results.json) records 15 completed trajectories
and 45 submitted rounds: 42 passed the full finite behavior gate; two exhausted
compiler repair, and T020 round 1 failed behavior. Forty-one had clean source
review; T002 round 1 has a confirmed repeated-list-indexing issue and two
duplicate caller findings ([dispositions](semantic-dispositions.json)). Zero
rounds met every v3 style requirement. The [independent receipt audit](interrupted-audit.json)
found no discrepancies in the available evidence and explicitly marks the
30-trial campaign incomplete. No candidate is accepted as a full v3 success.
