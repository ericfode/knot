# Game of Life: fixed experiment contract

Write one pure Bend 2.0.29 implementation of Conway's Game of Life. The two
authors receive this same contract and the same current Perch style targets.
The exposure condition is supplied separately. This is a research specimen,
not a published package or a GPU implementation.

## Public interface

    import Base

    def step(width: U32, height: U32, cells: List<&2,U32>) -> List<&2,U32>:
      ...

    def evolve(turns: Nat, width: U32, height: U32, cells: List<&2,U32>) -> List<&2,U32>:
      ...

Parameter quantities may be made reusable where the checker requires it.
Keep both names, argument order and result types. Helpers and local datatypes
may use any representation supported by the pinned compiler. Import only Base;
keep the complete implementation in life.bend. No foreign code, IO, unsafe
annotations, new axioms, holes, external libraries or fixture-specific behavior.

## Observable behavior

- Valid dimensions are integers from 0 through 32 inclusive. The input has
  exactly width * height cells, each 0 or 1, in row-major order.
- Cells outside the rectangle are permanently dead. There is no wrapping.
- Updates are synchronous. Count the eight adjacent positions, excluding the
  cell itself. A dead cell becomes live with exactly three live neighbors.
  A live cell survives with exactly two or three. Every other result is dead.
- step returns the entire next board in the same order and with the same
  dimensions. evolve applies exactly turns steps. Zero turns preserves the
  complete input; empty boards stay empty. Runtime gates exercise 0–8 turns.
- Evolution composes: applying a then b turns agrees with a+b turns within
  the tested range. No state outside the returned board is observable.
- Wrong lengths, nonbinary cells and dimensions outside the declared domain
  are outside this bounded experiment. Do not claim validation of them.

The implementation must terminate according to Bend's checker. There is no
claimed asymptotic improvement or timing competition. The evaluator records
runtime and uses a 60-second process timeout as a practical gate, not a speed
ranking. Correct outputs on the declared finite corpus do not prove all inputs.

## Fixed acceptance

1. The pinned checker accepts the complete implementation and public wrapper.
2. Independent full-board observations agree on exhaustive small boards,
   canonical still-life/oscillator/glider cases, thin and empty boards, and
   deterministic larger boards. Composition and input preservation are checked.
3. Selected full-board observations also agree on the native CPU backend.
4. Parent-run targeted Perch semantic and bounded law-packet reviews retain
   nonzero coverage and findings. They do not replace the deterministic gates.
5. Every implementation declaration is rated once against the frozen current
   rubric. Each of its three axes needs probability mass at level 3 or higher
   of at least 0.60. Uncertain or below-target declarations prevent a full pass.

Implementation generation uses GPT-6 Astra, max reasoning, in two fresh delegated
contexts. One candidate per condition; no author receives style or runtime-oracle
feedback. Preserve the first source before checking it. At most one repair based
only on the first compiler diagnostic is allowed. Record first-shot acceptance
and repaired acceptance separately. The parent does not hand-fix either source.
