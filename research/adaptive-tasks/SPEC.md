# First adaptive-task increment

Status: bounded increment implemented and checked, 2026-09-26. See
[the results and reproduction procedure](README.md) and
[the exact device protocol](DEVICE-PROTOCOL.md).

This is a bounded runtime feasibility probe. It is not the Knot compiler, a
Bend-source lowerer, a general GPU heap, or a package release.

## Contract

- A task/frame is affine. Moving it consumes the previous owner. An owning slot
  can be taken once; a rejected insertion returns both the unchanged slot and
  the uninserted payload. Taking an empty slot is explicit failure.
- A runnable task holds a logical destination, instruction state, captured
  continuation data, and its live numeric payload. Quantum counts machine steps.
  Zero fuel yields the same residual work. Returning a checkpoint never means
  returning a successful partial value.
- A binary continuation receives left and right in source order. Its
  noncommutative operation is `left * 31 + right`, modulo 2^32. A unary frame
  computes `value * factor + bias`, modulo 2^32. These are fixture operations,
  not a proposal to restrict Bend's eventual primitive set.
- Fixture programs are finite trees of delayed leaves, binary forks, and unary
  frames. A leaf starts with a seed and repeats `x * 1664525 + 1013904223` for its
  declared tick count. The independent Bend evaluator recursively computes the
  tree's value, with no task scheduling or checkpoint representation.
- GPU storage is preallocated for the validated tree. Each logical node has one
  owning task slot. No slot is reused during a run. A producer writes only its
  own task record; a later dispatch observes published results. Each join is
  processed by one invocation. No cross-workgroup spin waiting is permitted.
- Ready work is gathered into a bounded frontier, then distributed to worker
  invocations. A checkpoint preserves task identity/destination while its
  frontier position and worker may change. Capacity exhaustion, invalid input,
  and round exhaustion are explicit outcomes. They cannot be reported as done.

The initial arena trades general allocation for an auditable lifetime: all
records remain allocated until submitted GPU work is quiescent and the run is
released. Retirement invalidates task execution; it is not physical slot reuse.
Generic closures, sharing/refcounts, arbitrary native handles, source effects,
and cancellation during a dispatch remain outside this increment.

## Evidence contract

1. Complete Bend proof entry, quantified transition/composition laws, and
   inhabited witnesses. Record any missing arbitrary-history/refinement proof.
2. CPU reference and protocol fixtures agree on JS and native execution.
3. A nearby valid affine control checks; deliberate reuse fails in the intended
   quantity/type phase, not parsing. Type-valid behavior mutants are rejected.
4. GPU results match the independently computed Bend values for balanced,
   skewed, serial-frame, and reversed-result-order cases with multiple quanta.
   Record real adapter identity, dispatch/completion/readback, bounds outcomes,
   repeated runs, and migration observations. No speed claim follows.
5. Targeted Perch checks have nonzero rule selection, or record one provider
   blocker and continue deterministic work without repeated credential retries.
