# Knot handoff

Prepared 2026-09-26 for the user's request to clean `main` and hand off. Main was
clean at `668e447` before adding this document and its verification record. Find
the final handoff commit with `git log -1 -- docs/HANDOFF.md`. No remote is
configured and nothing was pushed. Ignored toolchains, model weights and local
build artifacts remain local.

## Resume here

The immediate priority is the **memetic foundation before more compiler
implementation**. Start with owned time slicing: `Run → step → run → slices`.
The reading hypothesis is that giving a computation time returns either its
answer or the work still owed. The broader compiler goal was **paused in the app**
when inspected during this handoff; its state was not changed or completed.

Read [the starting packet](../research/compiler-style/hillclimb/START-HERE.md),
[hill-climbing plan](../research/compiler-style/MEMETIC-HILLCLIMB.md),
[transfer contract](../research/compiler-style/hillclimb/TRANSFER.md) and
[current search state](../research/compiler-style/hillclimb/state.json).

The next bounded increment is a separately recorded comparison gate:

1. Compare complete residual states, including remaining ticks, frame tags,
   captured values, order, destination and payload. `task.observe` omits ticks
   and frames. Build independent affine inputs for each execution lane.
2. Preserve existing laws and fixed observations; add independent Bend witnesses
   and discriminating mutants for the budget-list transfer exercise. Track task
   steps separately from host/list traversal. Expected results must not come
   from the candidate being judged.
3. Validate the general gate on the accepted baseline and mutants before new
   style candidates. The historical pilot harness pins one source hash and one
   exact emitted-code delta; it is not a general successor gate.
4. Coordinate the successor scope with the active style owner before generation.
   The proposed nine-candidate epoch remains unstarted, with zero new candidates,
   human preferences or transfer executions. Keep the wider component queue held.

Use [Git workflow](GIT-WORKFLOW.md), root [AGENTS.md](../AGENTS.md), and the closest
local instructions. Prefer an available managed worktree for further isolated
experiments; inspect attachments and ownership before creating another checkout.

## What was checkpointed

| Commit | Preserved work | Acceptance boundary |
| --- | --- | --- |
| `707a346` | First-family source packet and transfer contract | Selection and specification; no new candidate or transfer execution |
| `f1763e7` | Runtime dependency contracts and stored-evidence audits | Hash/link verification; no new runtime qualification |
| `f9412ae` | Local-model owner's four-model comparison and tooling | Small, previously exposed controls; default reviewer unchanged |
| `668e447` | Old runner pilot, complete receipts, campaign state and source snapshots | Unaccepted experiment preserved; accepted executable baseline restored |

The runner candidate survives byte for byte in
[candidate-first.bend.snapshot](../research/adaptive-tasks/style-pilot/adaptive-run-1/candidate-first.bend.snapshot).
Its [handoff record](../research/adaptive-tasks/style-pilot/adaptive-run-1/handoff.json)
reconciles the stale unavailable-review summary: the later completed historical
review has target mass 0.82 conceptual, 0.81 delight and 0.52 memetic (uncertain).
The current rubric differs and targeted semantic acceptance is unrecorded.
No historical failure or receipt was rewritten. Replay the old harness only in
an isolated checkout with its frozen candidate installed; leave main's baseline
intact. The archived unified diff retains its required context-space line.

## Compiler and runtime boundaries

The selected path remains Bend 2 → self-hosting Wasm, plus compiler-generated
execution on a real GPU through WebGPU/WGSL and adaptive continuation tasks.
The current seed/reference pin is Bend 2.0.29 / `574b6d3`.

Existing checkpoints are distinct: enum source-to-Wasm (`a884b14`), structural
checking and independent-model evaluation (`6413a1a`), owning store on seed CPU
(`b61df8d`), and generated bounded Wasm word-store transitions (`7478516`).
Fields and recursion in emitted programs, general value lifetime, whole-compiler
A2/A3 bootstrap and compiler-generated GPU execution remain open. The handwritten
GPU probe does not close generated-device acceptance.

Read [the full goal](SELF-HOSTING-GOAL.md),
[runtime support plan](RUNTIME-SUPPORT-PLAN.md) and
[remaining dependency contracts](RUNTIME-DEPENDENCY-CONTRACTS.md) when compiler
work is resumed. This cleanup does not advance those milestones.

## Ownership and evidence

`Swap Perch to Local Model` completed `f9412ae`, reported 35 focused integrity
tests passing and no remaining trial processes, and is holding shared-checkout
writes for this handoff. Its [report](local-models-2026-09-26.md) separates observed
local trials from reviewer qualification. Those tests were not rerun here.

Separate owner worktrees were left untouched:

- `StyleGuide (2)`: `/Users/ericfode/.codex/worktrees/2a20/knot`; ongoing isolated
  style work. Read that chat before duplicating its experiments or merging it.
- `StyleGuide`: `/Users/ericfode/.codex/worktrees/7e98/knot`, branch
  `codex/perch-takeover`.
- `Find why Perch is slow`: `/Users/ericfode/.codex/worktrees/890a/knot`, branch
  `codex/perch-throughput`.

The [verification record](handoff/verification-2026-09-26.json) distinguishes
checks performed during cleanup from owner-reported and historical results.
No compiler/device or paid model review was rerun by the handoff coordinator.
Automation settings were not changed; campaign state retains the historical
blocked prompt update, which is not a fresh observation of scheduler state.

Whiteboard `ec417549-1568-412d-b7e2-43ccc36acbd5` remains pinned to the earlier
selection checkpoint `707a346`. It is a historical design/code walkthrough;
this handoff and current Git state take precedence for checkout status.
