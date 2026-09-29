# Coordinator state

As of 2026-09-29 17:00 PT. Main is at 88f02bf1. The campaign is **paused** at the user's request, and all branches are pushed.

This file is the hand-off point. Anyone can continue the campaign from it, whether the Claude coordinator, a Codex coordinator or a human. Until today the state lived in a session scratchpad; it is now here and in `handoff/`. The standing rules are in [../COMPILER-CAMPAIGN.md](../COMPILER-CAMPAIGN.md): decisions D1–D26, the protocol and the definition of done.

## Where self-hosting stands

On main, the selfhost gate passes **2 of 65** cases (`tests/compiler-selfhost/receipts/selfhost.json`). The 63 blocked cases are blocked by these missing capabilities; a case can count against more than one:

| Missing on main | Cases | Where it is |
|---|---|---|
| Base library slice | 48 | `campaign/baseslice` (ff44b974, 09-27). It has not been re-examined since D14. |
| Nested pattern matrix | 36 | `campaign/nest`, fix round 12 in progress |
| Literals | 31 | `campaign/literals-integ` |
| Generics | 30 | `campaign/generics`: needs-coordinator |
| Layout, closures | 18 each | `campaign/literals-layout` (merged into literals-integ); `campaign/closures` |
| Lists, Nat columns, modules | 15–16 each | `campaign/modules`; others follow |
| IO, `do`, packages, products | 4–6 each | later |

Even when the frontend compiles its own source, running it needs the VM track. The steps are the integration round, vm-rc (memory reclamation; required by the speed review), prims, closures and io, then vm-e2e2, then vm-e2e3 (the fixpoint I2 = I3).

## Merge order (serial)

nest → modules (a reconciliation round after nest) → descent-2 → closures → literals-integ → generics → VM track.

After each merge:
1. Refresh the shared receipts with `npm run -s gates:refresh`.
2. Push.

The VM track merges only after closures, because six closure goldens enter the bootstrap corpus as Invalid parse rows and must never be baselined.

## Increments

**Resume** means `Workflow({scriptPath, resumeFromRunId, args})`. It works only inside the Claude session that launched the run. Any other executor starts a fresh round from the prompt and the branch state instead.

| Increment | Branch tip | State | Next action |
|---|---|---|---|
| nest | 16:39, and the worktree holds 9 uncommitted files from the interrupted session | Fix round 12 was implementing when paused. It had added the nest-round13 gate (210 fixtures, the class grid, the zoo, 24 mutants) and amended 52 term-suffix pins to `Unsupported parse operator`, seed-derived. | Finish [handoff/prompts/nest-fix9.md](handoff/prompts/nest-fix9.md) (findings in [handoff/findings/nest-r12.md](handoff/findings/nest-r12.md)), then review. Claude resume: `wf_20fc87fe-6aa`. |
| literals-integ | 19ab584f | The re-run round-1 fix is done; a fresh review was interrupted. | **Wait for nest's round-12 commits**, re-merge that nest tip, then run a fix round. Its inputs are listed under "literals-integ fix round" below. |
| perch-cap | 15:51 | Implementation is done; review was interrupted. | Review it, then merge. It must land before literals-integ. Prompt: [handoff/prompts/perch-cap.md](handoff/prompts/perch-cap.md). Claude resume: `wf_201d213a-9dd`. |
| vm-spec | round 14 | D25 (atomic stops) adopted; review was interrupted (semantics lens). | Finish the review, then ready. Claude resume: `wf_319e8dfa-3a5`. |
| vm-core | round 7 (15:49) | D22–D25 and the round-6 majors are implemented; review was interrupted. | Finish the review. Claude resume: `wf_01136ea1-913`. |
| vm-model | round 4 (14:37) | D22–D25 implemented; review was interrupted (semantics lens). | Finish the review. Claude resume: `wf_7eef2cfb-a3c`. |
| image | b200a6a9 | **Reviewed, ready**: all three lenses, minors only. | Merge with the VM track. Its minors are listed under "VM-track integration round". |
| modules | 7ac90164 | Waiting on nest. | Reconciliation round after nest merges (see below). |
| descent-2, closures | 75e1ac69, a1d68911 (09-27) | Reviewed earlier; waiting in the merge order. | Merge main, re-run the gates and review the delta before merging. |
| generics | edfad8b9 | Needs the coordinator: 4 majors. | Closures pin collisions; assertion rulings; a gate timeout (now 1,800 s); the generic path accepts a spaced `->` or `{` that the seed rejects. Also the forward-declared pattern residual. |
| opt-1, opt-2, bench-2, c-backend, gpu-* | 09-27 | Parked by D13 until self-hosting. | Stay parked. |

## Standing coordinator rulings not yet in COMPILER-CAMPAIGN.md

- **One diagnostic vocabulary for unmodeled terms, shared by nest and literals-integ.**
  - An operator token continuing a term is `Unsupported parse operator`. That covers `+`, `-`, `++` and `->` after a value, spaced or on the next line; a glued `x+y`; and a spaced `a + b` in an argument list.
  - Other unmodeled term forms are `Unsupported parse term-form`: a touching `+name` in expression arguments, or a `?` hole.
  - Invalid stays only where the seed rejects for the syntactic reason named: the marker-gap shape, `@`, backslash and closers in argument lists, and pattern fields.
  - Re-freezing one suite's false-Invalid pin uses the seed-derived amendment path, not D26.
- **Terminal default copies (nest).** For now, bound them: charge the copies to a core-size budget, which answers `Exhausted check budget`, and classify the seed's Bun-lane memory fault as Exhausted (host). Knot's own `src/*.bend` must stay within the budget. The fix proper is the queued `core-default` increment.
- **Dotted binders.** modules' scope-aware checker rule is canonical. Until then, nest's `Unsupported parse dotted-binder` is the stopgap; literals-integ implements the scope-aware `binders` rule. The modules reconciliation round removes nest's parser rule.
- **The modules reconciliation round**, right after nest merges:
  1. Merge main.
  2. Remove nest's dotted-binder parser rule, and amend the nest-frozen dotted prefixes in one seed-citing commit.
  3. Freeze the detached constructor brace (`spm-*`) as `Invalid parse detached-brace` in both bundle lanes.
  4. Freeze the empty-datatype programs as accepted.
  5. `Unsupported function-reference` and `type-as-term` stay: they are D4-compliant.
- **Empty datatypes are accepted.** A lane that cannot handle one says `Unsupported check empty-datatype`, never Invalid.
- **Atomic stops** are D25. The lockstep's two halting relations are dropped in the integration round.
- **Unimplemented foreigns.** Until vm-io lands, both machines refuse at load an image that names an unimplemented foreign: `Unsupported vm foreign N`.
- **The image round-trip law** is partial correctness: encode succeeds ⇒ decode = erase_tokens.
- **The image name refusal** (`Unsupported compile image-name`) is accepted. Condition: the integration round measures that no name in `src/*.bend` is refused.
- **literals-integ 8ea6faf** (fitting `check.bend::run` under the Perch cap):
  - accepted: the local `then`, the row order and the one promotion walk;
  - revert after perch-cap: the spelled-out `C.exhausted`;
  - restore after perch-cap, where they fit: the three verbatim excerpt task files.
- **The prechecks Perch rules** all stay advisory at 80 (PR #3). The claim-holds floor was declined: its gap is inside the noise.
- **At the VM-track merge:**
  - mirror `vm/build.json`'s vm.wasm sha into `src/CONTRACT.json`;
  - fix the stale `vm/model.bend` paths (now `vm/model/`) in COMPILER-CAMPAIGN.md and VM-DESIGN.md;
  - fix VM-DESIGN §2's eager IO wording (D23);
  - take the union of the "Trust inventory: open proof obligations" rows in `src/SPEC.md`.
- **PR #1** (`campaign/literals-layout`) is closed as superseded when literals-integ merges.

## literals-integ fix round (after nest round 12)

1. Merge nest's round-12 tip.
2. Follow D26 and the vocabulary ruling above. The 39 pins, the nest oracle widening and the 19 re-expressed mutants are ratified; a reviewer who re-flags them gets that answer.
3. Must fix:
   - the false Invalid `check unmatchable-binder` on a binder bound by a primitive (Nat/String) matrix, or by an alias or let of primitive type;
   - after verifying it: the unsound acceptance of a constructor field named like a type that a later field reads. Unsupported at minimum.
4. **Laws are outside D26 (D21 applies).** The 8 parent laws reported removed must be restored, or shown to have moved. `offset_spelling`'s narrowing is either undone or recorded as a true open obligation.
5. Check the inherited checker gap that image's review found: an unannotated let of a matched parent is accepted, and the seed rejects it. Fix it here if no other branch owns it.
6. Findings: [handoff/findings/literals-integ-r2.md](handoff/findings/literals-integ-r2.md).

## Queued increments

- **perch-cap** (in review): a names-only fitting tier in `scripts/perch-context-interfaces.mjs`.
- **VM-track integration round** on `campaign/vm-lockstep`:
  - merge vm-spec, vm-model, vm-core and image;
  - drop the halting relations;
  - fix any machine that deviates on a Halt with a non-scalar message (D20) and on the unimplemented-foreign load refusal, with frozen runs for both;
  - image minors: refuse a Closure whose slots exceed the §4 limit; `arm_for` must return InternalFailure instead of an invalid image; 3 decoder-refusal expectations differ from the reference codec;
  - carry P0 of the speed review: freeze the compiler-shaped workloads and re-measure the bench per entry.
- **core-default**: a Default arm in core `Case`, replacing the per-constructor copies, in the evaluator, both Wasm emitters and the image encoder.
- **vm-rc**, required before vm-e2e2; the bump-only heap needs 15–39 GiB. Then **vm-codegen**, only while node/V8 is the engine of record.
- **Frontend optimization** (optional): qualify's quadratic scans, 58% of the modeled self-compile entries.
- **Base slice**: re-examine `campaign/baseslice` against the 48 blocked selfhost cases.

## Pending user decisions

From the VM speed review, [handoff/vm-perf-design-review.md](handoff/vm-perf-design-review.md). These defaults apply until the user answers:

1. **D27:** the VM is judged per entry on frozen workloads. The binding gate is A2(S) ≤ 15 min of CPU, with heap < 4 GiB. Seed ratios are recorded, never gated. Default: yes.
2. **Engine of record:** node 22 (V8), with Bun/JSC as a cross-check. Default: node.
3. **D28:** the generated, inlined release vm.wasm. Default: yes, while V8 is the engine.
4. **After vm-e2e3:** interpreter hill-climb or the native track. Default: decide from vm-e2e3's measurements.

**Executors (user, 2026-09-29 17:00): Codex is back. All work (implementation, fixes, reviews and verification) runs on Codex `gpt-6.1-sol` at max reasoning in fast mode. Claude usage stays minimal: the Claude coordinator only dispatches, rules and merges.**

## How an increment runs

The Claude workflows are in [handoff/workflows/](handoff/workflows/). An increment runs in this order:

1. **Implement.** Implementer sessions (Sonnet at max effort, retried on Opus) run in the increment's worktree until the report says complete.
2. **Precheck.** `python3 -B scripts/prechecks/run.py --head campaign/<id> [--upstream <id>=<ref>]` runs from the main checkout. Executor conditions get one fix session.
3. **Review.** Three lenses run in fresh scratch exports, each verified adversarially:
   - *scope*: diff discipline, frozen expectations, D4, D9;
   - *gates*: re-run every gate and compare the counts;
   - *semantics*: independent probes against the pinned seed.
4. **Fix.** Fix rounds address the confirmed blocking and major findings.
5. **Status.** A dead lens or verifier makes the result `review-incomplete`, never ready.

Codex executors get the same prompts, run with `codex exec -s workspace-write` in the worktree. The model is `gpt-6.1-sol` (max reasoning, fast); the increments before 2026-09-27 used `gpt-6-astra`.

Every executor follows these rules:
- commit only on its own branch;
- never push, merge or rebase;
- never read `.env`;
- make no live Perch or provider call; live Perch is coordinator-only, from the main checkout;
- always run with `BEND_NO_TELEMETRY=1`;
- use the pinned seed `bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts`;
- keep variables out of `rm` targets: guard them as `"${VAR:?}"`.

The workflows' INDUCER block points to a session-local decoded copy. Other executors read AGENTS.md's first line directly and keep any reflection private.
