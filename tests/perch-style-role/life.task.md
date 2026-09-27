# Bounded Conway Life

Write one pure Bend 2.0.29 implementation with public operations step and evolve.
Step accepts width, height and cells, in that order. Width and height are U32;
cells and the returned board have type List<&2,U32>. Evolve additionally accepts
a Nat turn count before those three arguments and returns the same board type.
Parameter quantities may be reusable where the checker requires it. Import only
Base and keep the complete implementation in one file; helpers and local
datatypes may use representations supported by the pinned compiler. No foreign
code, IO, unsafe annotations, new axioms, holes, external libraries or
fixture-specific behavior is allowed. Termination must satisfy the checker.

Valid dimensions are integers from zero through thirty-two inclusive. Input has
exactly width times height cells, each zero or one, in row-major order. All cells
outside the rectangle are permanently dead. There is no wrapping. Updates are
synchronous. Count the eight adjacent positions, excluding the cell itself. A
dead cell becomes live with exactly three live neighbors. A live cell survives
with exactly two or three. Every other result is dead.

Step returns the entire next board in the same order and dimensions. Evolve
applies exactly its turn count. Zero turns preserves the complete input; empty
boards stay empty. Applying a turns and then b turns agrees with applying a+b
turns. No state outside the returned board is observable. Runtime checks exercise
zero through eight turns and compare complete boards on two JavaScript runtimes
and selected native CPU cases. The process timeout is a practical gate, not a
speed ranking or an asymptotic performance requirement.

Wrong lengths, nonbinary cells and dimensions outside the stated range are
outside the contract. The finite test corpus does not constitute a proof for
all valid inputs. GPU execution, pattern classification, automatic discovery of
behaviors, and simulation of other computational systems are not requested.
