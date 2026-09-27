# Bounded review: owned continuation run

Only `research/adaptive-tasks/task.bend::run` changes. Its signature is
`run(fuel: Nat, state: Run) -> Run`. Run is affine Checkpoint(Task) or
Delivered(destination,Payload); Task owns destination, remaining ticks, payload
and an affine frame list. Payload is an inhabited OwnedWord(U32), and frames are
Unary(factor,bias) or Binary(left payload). This is an existing bounded prototype.

The candidate advances only a positive-fuel Checkpoint, recursively calling
`run(n,step(task))`. Every other input returns its existing Run unchanged.
Step's implementation, frame order, arithmetic and all other declarations are
unchanged. It runs at most fuel task steps. Exhaustion preserves full residual
work; it does not claim successful completion. Delivered is absorbing.

Three unchanged equations directly constrain this dispatch:

- zero_fuel: for arbitrary full Run r, run(0,r) = r.
- delivered_absorbs: for arbitrary Nat n, destination d and affine payload p,
  run(n,Delivered(d,p)) = Delivered(d,p).
- fuel_add: for arbitrary n,m,r, run(m,run(n,r)) = run(Nat.add(n,m),r).

The entire twelve-law PROOF entry, including the unchanged induction for fuel_add,
checks on the first candidate. One-tick, ordered binary and captured unary laws
compare independent arithmetic and full constructors. Generic slot laws remain
unchanged. No canonical proof body was inflated or axiom introduced.

The independent Bend oracle recursively evaluates source trees, without task
fuel or checkpoints. Existing fixtures supply ten trees and the unchanged
conformance program observes eleven outcomes. Its observation function omits
frames/ticks, so that transcript alone cannot establish full-state preservation;
the full-state laws supply that separate evidence. Valid affine usage and two
reuse negatives test the intended quantity phase. Affinity permits dropping;
this prototype does not model external-resource cleanup.

The existing five CPU mutation obligations remain fixed: wrong tick constant,
swapped binary arguments, lost destination, discarded zero-budget state, and
overwritten occupied slot. Their original observing assertions and rejecting
laws stay unchanged. The zero-budget mutation must now insert the original bad
zero-fuel arm before the new recurrence; changing the whole fallback would also
corrupt positive-fuel delivery and would be a different mutation. The gate must
record type acceptance, named proof rejection and the differing runtime witness.

Gate outcomes, exact commands and immutable hashes are separate receipts in
this pilot directory. Pending or unavailable checks are not claimed here as
passes. The device shader/runner and independent fixture/oracle closure are
unchanged and do not import task.run. Historical hardware evidence applies to
those exact components and fixture output, not a newly executed device run or
general source-to-GPU compilation. No speedup is inferred from shorter source.
