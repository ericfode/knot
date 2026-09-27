# One compiler-diagnostic repair

The first checker rejected the nested match on a reusable tail after the outer
multi-scrutinee match: "a match on a parameter or field ... consumed binder".
Flatten the two-column observations into nested constructor patterns in one
match. Because advancing those observations reconstructs their right tails,
make the exact row width the leading structural parameter. Each output cell
consumes one Nat successor, and the row supplied by sweep has precisely width
real cells plus one right sentinel. This is the declared dimension, not an
arbitrary exhaustion budget. Pass width explicitly from sweep.

This is the only diagnostic repair for the round. No runtime or style feedback
was available before it. The first and repaired snapshots remain separate.
