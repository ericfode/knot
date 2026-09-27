# Bounded law review: two finite Game of Life implementations

This packet reviews one operation family, synchronous Life evolution, in two
research specimens. The declared external contract consists of step and evolve.
Other named definitions are implementation helpers; this is not a published
package or a claim of module-level access restrictions.

## Sources and acceptance boundary

- arm-a/life.bend SHA-256:
  4aa35688d6970d1b2a7d03e5f69ace5a84467930feefd5a71d2dcd7969b2c107.
- arm-b/life.bend SHA-256:
  4c8fe33eb9d25aece6d47118e68c938ecf46cd6fd821f0abe5deffe464605804.
- Both source files and the public wrappers passed the Bend 2.0.29 checker,
  revision 574b6d39a235b539eb19a5c532993a0abb3d11ad. No candidate was edited
  after successful checking or after runtime observations.
- arm-a needed one compiler-diagnostic repair; arm-b passed its first check.
  Initial sources, diagnostics and repaired source are retained separately.

No universal behavioral theorem or Bend proof file is claimed. Evidence here
is pinned type/quantity/termination checking, bounded exhaustive enumeration,
independent runtime assertions, and concrete native observations. Base and the
seed compiler/runtime are trusted; no new axiom, unsafe annotation, hole or
foreign implementation was introduced. There is no GPU or performance claim.

## Abstract values and observation

A board is width * height binary cells in row-major order, with each dimension
in 0..32. Wrong lengths, nonbinary values and larger dimensions are outside this
experiment. Missing positions beyond any edge are permanently dead. The full
ordered result, its length, and preservation of the supplied reusable list are
observed; no live-cell-only projection discards positions.

    step(width: U32, height: U32, cells: List<&2,U32>) -> List<&2,U32>
    evolve(turns: Nat, width: U32, height: U32, cells: List<&2,U32>) -> List<&2,U32>

For each position, count the eight neighbors in the OLD board. The next value
is 1 exactly when the count is 3, or when the old value is 1 and the count is 2.
evolve(0,w,h,c) = c; evolve(n+1,w,h,c) = evolve(n,w,h,step(w,h,c)).
Evolution must compose: a steps followed by b steps equals a+b steps.
The runtime domain exercises counts 0,1,2,3,4,7,8; this is not exhaustive in
turn count or in all supported board dimensions.

The domains are inhabited. An empty 0x7 board is []; a 1x1 live board is [1].
A 2x2 block is [1,1,1,1] and stays unchanged. The 3x3 board
[0,0,0,1,1,1,0,0,0] changes to [0,1,0,0,1,0,0,1,0] and returns after two steps.
Three live cells at (0,0), (1,0), (0,1) on a 3x3 board produce a four-cell
corner block. These witnesses exercise live/dead states, survival, birth,
boundaries and multiple generations, with no impossible antecedent.

## Operation-to-evidence matrix

| Operation | Defining observation | Evidence for each source |
| --- | --- | --- |
| step | Exact ordered next state, binary range, fixed shape, dead boundaries, synchronous use of old state | One-turn corpus entries; exhaustive boards at listed small dimensions; canonical and generated boards; Node and Bun |
| evolve | Zero-turn identity, repeated independent reference steps, full state preservation and shape | Corpus at 0,2,4,8 turns; independent reference iteration; selected native observations also include one turn |
| composition | Three turns followed by four equals seven and equals the independent reference | 21 cases on Node and 21 on Bun |

Both implementations passed all 1,537 corpus observations and all 21 composition
checks under EACH of Node v22.22.3 and Bun. There are also 28 passing complete
board observations per implementation in native CPU executables. Native
examples are selected empty/thin, block, blinker, glider and generated boards
up to width 8; larger dimensions were tested on Node and Bun. Native output
is compared as complete nested lists, not just a checksum or process exit.

The small-board corpus exhausts every binary input at dimensions 0x0, 0x7,
7x0, 1x1, 1x5, 5x1, 2x2, 2x3, 3x2 and 3x3, at one and two steps. Remaining
cases include a known translated glider after four steps, still lifes,
oscillators, and seeded generated rectangles through 32x32. The frozen corpus
is finite. Passing it does not prove all states on a 32x32 board.

## Independent reference and representation

The oracle was frozen before either author began. It builds a SET of live
positions, adds each live position's contribution into a MAP of valid neighbor
counts, then reconstructs every output position. It never imports a candidate.
Before freezing, each initial board's reference step was crosschecked against
a separate dense coordinate enumeration. Explicit block, blinker, glider and
corner-block expected patterns also passed. Composition compares both candidate
paths against independent seven-step evolution, not only against each other.

arm-a packs rows into U32 lanes, composes a full-adder tally along two axes,
and selects center-inclusive totals three and four. Only the three low count
planes are needed for those totals: possible totals eight and nine alias zero
and one, not three or four. Unpacking clips unused columns before a subsequent
public step repacks the board. Width 32 uses the entire word. This explanation
is source reasoning, not a quantified bit-circuit proof.

arm-b creates three-cell horizontal sums, combines three row sums, and subtracts
the original center before applying B3/S23. A missing list front supplies zero.
Its moving window contains only old row sums. On valid binary inputs, the
square sum includes the center, so removing it is nonnegative and leaves at
most eight. This invariant explains the U32 subtraction's intended domain.

## Boundaries and effects

Empty dimensions and singleton boards have explicit observations. Row edges
do not wrap. List order and dead cells remain visible. The input domain keeps
cell counts and dimensions bounded; invalid inputs are not validated. There
is no exposed capacity, identifier lifetime, borrowed owner, foreign effect,
fallible result or shared mutable state. Iteration uses structurally decreasing
Nat; it does not return success after silently exhausting unrelated fuel.

## Semantic controls

All three deliberately broken controls first passed the pinned type checker
and JS generation. The SAME frozen runtime oracle rejected them by board
mismatch, not a parse failure, timeout, malformed result or harness crash.

| Control | Defect and concrete witness | Observed rejection |
| --- | --- | --- |
| identity | Copies the board instead of evolving; a live singleton must die | 1,455 of 1,537 corpus observations mismatch |
| extinction | Returns all-dead cells, including live zero-turn inputs and survivors; 1x5 [1,1,1,0,0] should yield [0,1,0,0,0] | 1,025 corpus observations mismatch |
| always-one-step | Replaces arm-b's evolve with step, ignoring turns | 553 corpus observations and 20 of 21 composition cases mismatch |

For the last control, the blinker composition witness produces the horizontal
form after two calls while direct seven-turn evaluation and the independent
reference require the vertical form. This attacks state composition and
zero-turn identity without changing the accepted source. The shared assertions
remain unchanged, and no surviving non-equivalent control is labeled a pass.

## Receipts and limits

The preregistration hashes the contract, fixture generator, independent runner,
compiler files and rubrics. submission-lock.json connects original sources to
the exact neutral copies used for Perch. receipts/arm-a-gates.json and
receipts/arm-b-gates.json retain commands, exits, hashes and full observations;
the three control receipts retain their mismatches. These links are provenance,
not additional material the reviewer must fetch to understand this packet.

Style targets are independent advisory judgments. No style score, ranking or
provider probability is used as evidence of a theorem, a performance result,
or the completeness of this finite specification. The current experiment
does not satisfy a package publication or full formal-verification claim.
