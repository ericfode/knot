# Start with owned time slicing

Selected 2026-09-26. The first reading family is **Run → step → run → slices**,
with zero-fuel, absorbing-delivery and fuel-composition laws beside it. The first
question is whether its form makes the reader feel able to hold and continue
unfinished work. This selects the starting point; no new candidate has been
generated and the existing pilot has not passed.

Handoff update: the candidate is now preserved as an
[unaccepted research snapshot](../../adaptive-tasks/style-pilot/adaptive-run-1/handoff.json).
The accepted baseline is restored in `task.bend`. The frozen packet below records
the original selection-time state; its untracked/staged labels are historical.

## Why this family

| Candidate starting point | Useful material | Decision |
| --- | --- | --- |
| Owned task family | A small explicit residual state; captured frames; fuel composition; existing ownership and behavioral gates | Start here. It directly expresses the selected runtime idea and has a bounded semantic surface. |
| Compiler evaluator | A strong Evaluate/Return rhythm and explicit continuation frames | Retain as a later comparison. Environments, fields, erasure, host arguments and failures make it a much larger first experiment. Its Data lifetime and exhaustion contract also differ. |
| OutputBuilder | Empty/Chunk/Join composition and suffix traversal | A useful later transfer family, under its package owner. Its byte protocol adds admission and error-precedence obligations. |
| Symbols | Stable IDs and two views of one table | Learn from the owner's ongoing search; do not duplicate or overwrite it. |

The runner's existing candidate meets the first two style targets and has 52%
memetic target mass, uncertain. That is a useful unresolved example, not the
reason for selecting it. The decisive properties are relevance to Knot's
identity, a complete small contract and an available transfer exercise.

## Read this packet in order

The [frozen packet](start-packet.json) pins committed baseline
`897cd0e2bb7cab481b992423dbb9a30c6b0fdbc4`, the then-staged runner candidate, nineteen
committed contract/gate/evidence inputs and four seed files. The candidate can
be reconstructed exactly by replacing the one retained `run` block in the
committed baseline. It remains the existing coordinator's candidate.

1. Read `Payload`, `Frame`, `Task` and `Run` in
   [task.bend](../../adaptive-tasks/task.bend). A checkpoint contains the complete
   owned residual state; a delivery contains the destination and result.
2. Read `step_parts` and `step`. One step consumes a remaining tick, applies one
   captured frame, or delivers after both are exhausted.
3. Compare the two existing `run` forms below. Both are source specimens already
   seen in this conversation, so this is not a fresh blinded taste comparison.
4. Read `slices`, then the three selected [laws](../../adaptive-tasks/LAWS.bend)
   and their [proofs](../../adaptive-tasks/PROOF.bend).
5. Read the [new transfer contract](TRANSFER.md), which deliberately supplies no
   implementation.

The committed baseline names its stopping cases:

```bend
def run(fuel: Nat, state: Run) -> Run:
  match fuel state:
    case 0n _:
      state
    case 1n+n Checkpoint{task}:
      run(n,step(task))
    case 1n+n Delivered{dest,payload}:
      Delivered{dest,payload}
```

The preserved candidate singles out the advancing case:

```bend
def run(fuel: Nat, state: Run) -> Run:
  match fuel state:
    case 1n+n Checkpoint{task}: run(n,step(task))
    case _ _: state
```

The future experiment should investigate what makes these clauses a grammar the
reader can use elsewhere. Another reduction in line count is insufficient. The
family's substantive payoff is expressed by these existing laws, shown here in
explanatory notation:

```text
run(0, r)                 = r
run(n, Delivered(d, p))   = Delivered(d, p)
run(m, run(n, r))         = run(n + m, r)
```

The proposed reading hypothesis is that the representation and these equations
can teach one reusable move: give an owned computation time, then keep what it
returns. The reader should be able to recognize and write another use of that
move without relying on a slogan in a comment. This remains an author hypothesis.

## Fix the experiment before varying the code

Keep `step_parts`, frame arithmetic/order, destination, affine ownership,
zero-fuel behavior and the meaning of delivery fixed. Treat the complete family
as reading context. The current owner assignment changes only `run`; any
successor scope must be recorded before generation. The proposed hill-climbing
budget does not retroactively enlarge the old one-candidate pilot.

Two observed details matter for the next gate:

- `task.observe` returns only status, destination and payload. It omits remaining
  ticks and captured frames. Final-answer agreement or that triple alone cannot
  establish preservation of a suspended computation. Compare the full state and
  use independently constructed owners for each execution lane.
- The owner's `check-cost.mjs` compares full emitted-JavaScript state and step
  counts, but also asserts that the sole emitted difference is replacing a
  Delivered reconstruction with identity. `check-pilot.py` pins the exact existing
  candidate hash. These are appropriate records for that particular trial, not
  reusable acceptance gates for arbitrary successors. The packet records their
  paths and hashes as then-untracked owner artifacts, now retained in the pilot checkpoint.

The next implementation step is therefore a **separately recorded general
comparison gate**, prepared before any new style candidate. Preserve the old
pilot and its assertions. Carry forward the accepted semantic observations,
laws and mutants; provide full-state observations and a cost check suitable for
the newly recorded scope. Source-specific mutation locators may be re-anchored
only while preserving the original violation and observing assertion. Validate
the successor gate on the frozen baseline and discriminating mutants before
using it to select a winner. A new gate must not obtain expected answers from
the candidate it judges.

After that gate and owner protocol are ready, make three actual source treatments
of this family under the hill-climbing plan. Review the source before model
scores, then test the best form against the budget-list operation. All three
style targets and independent gates remain required for integration.

## Prepared and still open

Prepared: a selected family, exact before/current source, verified input hashes,
reading sequence, concrete comparison questions and complete semantic transfer
contract. Nineteen pinned repository inputs and four local seed files matched;
the candidate reconstruction matched byte-for-byte.

Still open: the general successor gate, executable transfer oracle/mutants, owner
protocol reconciliation, new candidates and fresh human preference evidence.
No compiler, proof, device or paid review was rerun for this selection increment.
The old basic observer's limits and the pilot's deliberately narrow gate are not
new claims that its recorded experiment was incorrect.
