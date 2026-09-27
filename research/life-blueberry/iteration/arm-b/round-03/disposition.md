# Round 3 disposition

Rejected by the compiler after exactly one permitted diagnostic repair.
The first snapshot used destructuring lets on computed pairs, which Bend rejects.
The repair moved those observations to matching parameters, but the subsequent
check rejected tuple shorthand in the four-scrutinee pattern. The common runner
confirmed deterministic failure and performed no semantic or style review.

Both compiler commands, complete output, first and repaired snapshots, and the
repair rationale are retained. This round consumes budget and cannot be selected
as behavior-correct. The paired stream-view reading hypothesis remains untested.
No further edit was made to this submitted round. Round 4 will use explicit
constructor patterns rather than silently hand-fix this evidence.
