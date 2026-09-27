# Transfer exercise: a list of time budgets

Status: frozen semantic exercise for the first family, 2026-09-26. The notation
below is specification prose/math, not a Bend implementation or a new proved law.
An executable independent gate remains to be prepared before candidate generation.

## Interface and domain

`run_many(budgets, state)` consumes one well-typed `Run` and returns one `Run`.
`budgets` is a finite list of natural numbers. States and arithmetic follow the
existing [task contract](../../adaptive-tasks/SPEC.md). There are no host effects,
GPU operations, new frame kinds or changes to task semantics in this exercise.

The result is the complete residual state after applying the budgets. It must
retain destination, remaining tick count, payload, frame tags, captured values
and their order. Type ownership remains affine; do not duplicate a task to inspect
it or manufacture a reusable owner snapshot.

The denotation is fixed by:

```text
run_many([], r)          = r
run_many(n :: ns, r)     = run_many(ns, run(n, r))

run_many(bs, Delivered(d, p)) = Delivered(d, p)
run_many(bs, r)              = run(sum(bs), r)
run_many(xs ++ ys, r)        = run_many(ys, run_many(xs, r))
```

`sum` is natural-number addition with empty sum zero. The latter two equations
are consequences expected from the existing fuel-composition law; their new
Bend formulations and proof fills have not been written or checked.

This interface exposes only the final `Run`. Summing or permuting the Nat budgets
is extensionally equivalent for this pure machine. Do not reject a correct
implementation solely for having different internal scheduling structure. Frame
order remains semantically significant. An interface exposing intermediate
events would need a different contract.

Zero remaining ticks does **not** itself imply delivery: saved frames still need
steps, and producing `Delivered` requires its own final step. An implementation
that returns a partial payload as a completed answer is wrong.

## Fixed distinguishing examples

For compactness, `P(d,n,p,fs)` abbreviates a Checkpoint/Work with destination `d`,
`n` remaining ticks, owned word `p` and frames `fs`; `D(d,p)` abbreviates Delivered.
`U(f,b)` is a unary frame and `B(a)` is a binary frame holding left word `a`.
These are mathematical abbreviations, not proposed Bend names.

Let:

```text
r0 = P(73, 0,  5, [U(3,1), B(2)])
r1 = P(73, 0, 16, [B(2)])
r2 = P(73, 0, 78, [])
r3 = D(73, 78)
```

The source operations give `5 * 3 + 1 = 16`, then `2 * 31 + 16 = 78`, then
delivery. These small constants do not overflow U32. Reversing the frames would
produce 202, so the case distinguishes ordering. The table is a hand-derived
contract example, not an observed execution receipt.

| Input state | Budgets | Required full result | Distinction |
| --- | --- | --- | --- |
| r0 | [] | r0 | Empty schedule preserves the complete owner |
| r0 | [0,0] | r0 | Zero budgets cannot erase captures or claim completion |
| r0 | [1] | r1 | Exactly one frame applies |
| r0 | [1,0,1] | r2 | Last frame applied; delivery still pending |
| r0 | [1,1,1] | r3 | Separate slices complete the same computation |
| r0 | [3] | r3 | Grouped fuel agrees with the separate slices |
| r0 | [0,4,0] | r3 | Completion absorbs surplus and zero budgets |
| r3 | [0,65536] | r3 | Delivered state performs no task steps |

The executable gate must also cover live tick counters, the existing LCG/wrap
fixtures, varied destinations, empty frames, differing unary captures, differing
binary left values and independently built affine inputs. Preserve all original
task laws and their existing counterexamples.

For this frozen task machine, the expected number of machine transitions is
`min(sum(budgets), W(state))`, where `W(Delivered)=0` and
`W(Checkpoint{Work{d,n,p,fs}})=n + length(fs) + 1`. This is a derived requirement
to check in the new gate, not a measured performance claim or a newly proved
bound. Record host/list traversal separately; elapsed time is not inferred from
step count. The first scope retains the existing `step` mechanism, so its calls
can be instrumented without introducing a host evaluator.

## What the experiment should reveal

After learning the selected `run` family, the reader receives this entire
contract but no `run_many` implementation. Record their actual expression,
required hints, new terms and semantic mistakes. Existing `slices` is part of the
visible teaching context; the fresh challenge is variable budgets and composition,
not pretending the reader has never seen a recursive loop.

Passing the semantic exercise establishes bounded transfer evidence when its
gate is executed. The style question is whether the learned form made the new
operation natural and desirable to write. Preserve that judgment separately from
correctness and all three required declaration ratings. Once a rendering is used
to revise a candidate, it becomes development material; reserve a fresh rendering
for the next validation.
