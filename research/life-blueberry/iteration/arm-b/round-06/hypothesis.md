# Round 6 hypothesis

Fresh list-based design that retains the visible ring and eliminates the
representation changes of round 5. Extend the input with one dead bottom row;
start with a dead north row; append one dead east cell to each row entering the
scanner. Carry the west column as three scalar values initially zero.

Every real position now has exactly the same local shape. A single pulse scan
matches three current cells and three lookahead cells, counts the literal
north-west / north / north-east, west / east, south-west / south / south-east
ring, then advances all three tails while carrying the old current column.
The missing center is visible in the actual expression. The sentinel right
column terminates without generating an extra cell. Padding absorbs all four
boundaries, including empty width, before the cell rule is applied.

The reading improvement is an invariant and geometric correspondence: the
same row window advances as one operation, with no dynamic default observer,
head/tail adapter, or packed-count predicate to reconstruct. Fewer declarations
is a consequence, not the criterion.

Correctness risks: padding the bottom by one cell instead of one full row;
including the right sentinel in output; using the newly computed cell as a
carried neighbor; swapped north/south lookahead; and invalid structural descent
when a reusable tail is inspected before recursion. Preserve all fixed gates.
The same original exposure condition is retained.
