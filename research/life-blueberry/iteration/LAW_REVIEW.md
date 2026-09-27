# Bounded law review: selected iterative Life candidates

This packet records parent source review and fixed deterministic evidence.
Its live Perch outcome is retained separately with provider receipts. The
original packet's eight checks are historical evidence and are not reported
as a fresh review of these revised representations.

## Sources and contract

- Selected unexposed source: arm-a/round-10/life.bend, SHA-256
  0c21fa5a78ba0dc2d4e0b4682a5b3735987f81d8d2f6536cbbbca3e6d7cbea17.
- Selected exposed source: arm-b/round-06/life.bend, SHA-256
  f5706bb44322246209fd0f1538d8635cc59034517aa19abad324c9417cada737.
- Both candidates and public wrappers passed the pinned Bend 2.0.29 checker,
  revision 574b6d39a235b539eb19a5c532993a0abb3d11ad. The former passed its first
  local check; the latter needed one diagnostic repair. First and final inputs
  and full diagnostic streams are retained. Submitted sources are immutable.

The unchanged public operations are:

    step(width: U32, height: U32, cells: List<&2,U32>) -> List<&2,U32>
    evolve(turns: Nat, width: U32, height: U32, cells: List<&2,U32>) -> List<&2,U32>

Valid dimensions are 0..32. The input is exactly width * height binary cells in
row-major order. Outside positions are permanently dead. Every next cell uses
only the OLD board: it is live with three neighbors, or with two neighbors and
a live old center. The eight neighbors exclude the center. Output preserves
dimensions, order and binary range; the reusable input remains unchanged.

evolve(0,w,h,c)=c and evolve(n+1,w,h,c)=evolve(n,w,h,step(w,h,c)). Applying a
then b turns must equal a+b turns and independently computed reference evolution.
Wrong lengths, nonbinary cells and dimensions beyond 32 are outside the domain.

The domain is inhabited: an empty 0x7 board is []; a live singleton [1] dies;
the 2x2 block [1,1,1,1] survives; the 3x3 horizontal blinker
[0,0,0,1,1,1,0,0,0] becomes [0,1,0,0,1,0,0,1,0] and returns after two steps.
Three cells at (0,0), (1,0), (0,1) become a four-cell corner block.

## Independent public observations

| Operation | Observation | Evidence for each selected source |
| --- | --- | --- |
| step | Full ordered next board, fixed shape, binary range, dead boundaries, synchronous update | 1-turn entries in the independent Node/Bun corpus |
| evolve | Identity at zero, exact repeated evolution, full board and input preservation | Corpus counts 0,1,2,4,8; selected native cases |
| composition | Three turns then four agrees with seven and with an independent reference | 21 Node and 21 Bun checks |

Each selected source passes all 1,537 full-board observations and 21 composition
cases on EACH of Node and Bun, plus 28 complete-board native CPU observations.
Every result is compared as ordered cell values, not merely shape, population,
a checksum, or process exit. The small-board corpus exhausts all binary states
at dimensions 0x0, 0x7, 7x0, 1x1, 1x5, 5x1, 2x2, 2x3, 3x2 and 3x3 for one
and two turns. Other cases include block, blinker, translated glider, corners,
thin boards and deterministic generated rectangles through 32x32. Native cases
are a smaller set up to width 8. Counts 3,4,7 occur in composition evidence.

The oracle and assertions were frozen before original author dispatch. The
reference builds a set of live coordinates, accumulates neighbor counts in a
map, then reconstructs every board position. It does not import either source.
Before freezing, one-step results were crosschecked against dense coordinate
enumeration and explicit known patterns. Composition compares both candidate
paths with the independent seven-step result. The same assertions are used in
this continuation, with no test changes or score-dependent exemptions.

## Representation arguments from parent source inspection

The unexposed source uses width-clipped U32 row masks. Its vertical
full adder and shifted horizontal count planes compute center-inclusive totals.
Three low planes distinguish selected totals three and four; possible eight and
nine alias zero and one, not a selected value. Total four requires an old live
center, equivalent to B3/S23. These are source arguments, not quantified proofs.

Its duplex recurrence emits low bits of a completed output mask while its
continuation packs one old input row. The row pipeline carries only old north,
center and south masks. Initially all are zero. Running height+2 pipeline rows
and dropping the first 2*width output cells accounts for startup latency and
drains the bottom boundary with zero input. Width zero emits no cells; height
zero leaves no output after dropping startup rows. Nat recursion is structural.

The exposed source establishes a border invariant before pulse. The appended
dead bottom row and initial dead north row each have width cells. At every sweep,
center/north/south have width cells; appending an east zero makes each width+1.
With k positions left, pulse receives k+1 cells per row and old west-column
values. Its positive case therefore has two cells available in every row. It
adds exactly eight old binary values, so the U32 total is in 0..8. Carrying old
current-column values and advancing each suffix preserves that invariant.

The fallback Nil branch in pulse is unreachable for valid inputs under this
invariant. It is not evidence of validation for malformed rows. Width zero
selects the zero-count case and height zero selects the empty sweep. New cell
values appear only in output and never enter the subsequent old-state window.
Output rows are appended once in row-major order; no growing prefix is copied.

These arguments address empty/thin boards, exact border padding, row order,
old-state use, shifts at width 32 and termination. They do not establish a
universal formal refinement theorem or a measured performance advantage.

## Fixed harness controls and proof boundary

Three type-correct deliberately broken BASELINE controls were already executed
against the unchanged assertions. They are retained as harness evidence, not
reported as new mutations of the selected iterative source:

| Control | Defining witness | Historical runtime rejection |
| --- | --- | --- |
| Identity | A live singleton must die after one turn | 1,455 corpus mismatches |
| Extinction | Live zero-turn inputs and stable survivors must remain live | 1,025 corpus mismatches |
| Always one step | Blinker zero-turn identity and 3+4=7 evolution | 553 corpus mismatches and 20/21 composition failures |

All controls passed type checking and JS generation; rejection came from actual
state disagreement, not malformed input, compiler failure, timeout or harness
error. The original control receipts and their assertions remain hash-identical.

No Bend behavioral proof file, new axiom, unsafe annotation, hole, foreign code
or additional dependency is introduced. Base and the seed compiler/runtime are
trusted. Evidence consists of type/quantity/termination checking, bounded
exhaustion, runtime assertions and native observations. All 32x32 states, arbitrary
turn counts, invalid inputs, GPU execution and package publication are unproved.

Perch completed 20 relevant source checks for the unexposed selection and 16
for the exposed selection without threshold findings. The former still has an
uncertain memetic judgment; the latter meets every recorded style target. Style
probabilities do not prove behavior, specification completeness or human taste.

The candidate hashes, complete gate receipts, snapshots and provider outputs
are retained per round. The 85-file preservation manifest and parent receipt
audit verify that the original contract, oracle, compiler and standards remain
unchanged. A TypeSafe credit interruption in round 9 was retained, then recovered
after user replenishment without changing that candidate. The unexposed author
used all ten rounds and did not reach a complete style pass. No failed receipt
or earlier candidate was overwritten to present the selected outcomes.
