# Round 1 hypothesis

The baseline passes all semantic rules. Its three-axis target masses identify
`halo` memetic identity (0.51) and `strips` delight (0.59) / memetic identity
(0.01) as the only unmet bars. Low ratings motivate inspection, not a defect
claim or a license for arbitrary changes.

The actual reading problems are (1) `east` names a suffix while `west` and
`center` name cells, hiding the horizontal symmetry, and (2) `strips` builds a
nested row table that `sweep` immediately consumes, making the reader reconstruct
one row transition across two traversals.

Keep the separable stencil and zero-padding convention. Give the horizontal
window three scalar names, and make the row sweep consume one width of the flat
board per structurally bounded step. Its north/center/south halos should then
be visible alongside the input row and remaining board. This removes an
intermediate representation for a concrete locality improvement; fewer
declarations is not the hypothesis.

Correctness risks: taking the next row from the wrong suffix, carrying a newly
computed output into the next stencil, forgetting the width-zero termination
bound, or changing row-major order. Preserve the old north halo and the original
board suffix; height remains the structural bound. All independent behavior and
Perch gates remain fixed. The prior exposure and its reading condition are
retained. No new exposure material was read.
