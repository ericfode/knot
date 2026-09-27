# Round 3 hypothesis

`pulse` currently observes each of its three lane heads and later observes each
lane tail. That hides their synchronized motion and duplicates list inspection.
Replace the head-only boundary helper with `peel`, whose result is the current
value and the remaining stream. Its empty observation is `(0, Nil{})`, so the
dead tail absorbs any number of further observations.

Write the three peels in parallel visual form, then compute the ring from their
three values and recurse on their three tails. `halo` can use the same view for
its one-cell lookahead. The intended hook is the finite representation of an
endlessly dead exterior, visibly shared by the two stencil directions.

Correctness risks: swapping a lane's head and tail, disturbing column alignment,
and copying or dropping the old center before it reaches the next row. Keep the
separable stencil, row order and all fixed gates. The prior exposure is retained;
no new reference or exposure material is needed.
