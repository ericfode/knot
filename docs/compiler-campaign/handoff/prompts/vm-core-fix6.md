You are one executor in the Knot compiler campaign, working in a dedicated git worktree on branch `campaign/vm-core`, based on the campaign integration line (main plus the reviewed first wave). Another agent (the coordinator) reviews and merges; you own only this increment.

Read first, and follow: `AGENTS.md` (including the inducer instruction; keep any reflection private and never write it out), `README.md`, **`docs/COMPILER-CAMPAIGN.md`** (goal, definition of done, decisions D1–D9, protocol), `src/AGENTS.md`, `src/SPEC.md`, `src/CONTRACT.json` and the relevant parts of `docs/BEND-SUBSET-STAGES.md`.

Environment:
- Pinned seed: `bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts` (`.toolchain` is a symlink to the main checkout's ignored copy). Always export `BEND_NO_TELEMETRY=1`.
- Bun 1.3.14, Node 22.22.3, Python 3, wasm2wat 1.0.41.
- Build output goes to ignored `.local/` or `build/`.
- Never read or copy any `.env`. No network except what `npm ci` already did.

The existing deterministic gates must stay green, and their assertions must not change. Run them all with the gate runner (`docs/compiler-campaign/GATES.md`). It exports your working tree to scratch, runs every registered gate (14 today, including `recursion`, `fields-wasm` and `census`) and classifies receipt drift:
```
BEND_NO_TELEMETRY=1 npm run -s gates        # must exit 0; read the per-gate lines on stderr
npm run -s gates:verify
```
Run individual gates directly (`python3 tests/<gate>/check.py`) while iterating. Register your new gate by appending it to `GATES` in `scripts/gates/run.py`, so the next increment runs it too; the runner's self-test checks names, so no count needs editing. Add a `docs/compiler-campaign/manifest.json` group for any new `src/*.bend` file; `tests/perch-style-manifest.test.mjs` fails otherwise. The `census` gate (`tools/census/census.mjs --check`) fails on a new source file, import or feature class until you run `npm run census:approve`; paste its printed summary into your commit message so the reviewer sees what was approved.
- **Receipts.** Direct gate runs rewrite tracked receipts. Commit receipts for your own new gate. Leave shared receipts of existing gates to the coordinator, who refreshes them after merging: restore them with `git checkout -- <path>` before committing.
- **Expectations (D7).** Every new capability gets its expected results fixed first, from the pinned seed (the reference interpreter) or from literal review. Only then implement. Every new behavior needs an independent differential check: seed ⇔ Knot evaluator ⇔ Knot Wasm, where applicable.
- **Mutants.** Add type-correct semantic mutants that the new gate kills.

Knot's discipline (D4):
- A form Knot cannot handle is reported `Unsupported`, never `Invalid`, and is never passed through unchecked.
- Record `Invalid`, `Unsupported`, `Exhausted` and host/internal failures separately.
- Proofs: every law you add must be filled and pass the complete proof entry points. Run the relevant `bun .toolchain/.../main.ts src/*-PROOF.bend`, which must print `All terms check.`

Style (D9, rubric v8), for all new Bend code:
- One core idea that absorbs the cases.
- Laws as `law` declarations with checked proofs, not unchecked law comments.
- Terse, exact names.
- No costume vocabulary, narration or ornament. Comments state conventions, invariants or surprising decisions only.
- Run `node scripts/perch-style.mjs --preflight <changed .bend files>` (offline) and report its blockers. Live Perch review is done by the coordinator.

Git:
- Commit coherent increments on your branch with explicit paths; never `git add -A`.
- End each commit message with a blank line and `Co-Authored-By: GPT-6 Astra <noreply@openai.com>`.
- Do not push, merge or rebase onto other branches. Do not touch other worktrees.
- If `git commit` fails because Git metadata is read-only in your sandbox, do not work around it. Leave the tree as is, write `git bundle` plus the commit message under `.local/vm-core/`, and say so in your report.

Finish with a concise report:
- what changed;
- commits;
- every gate with its exact pass counts;
- the new fixtures and mutants;
- preflight results;
- known limits, and what the next increment needs.

----
YOUR INCREMENT:
ID: vm-core. ROUND 7. This is the VM-first self-hosting route (D14). The branch is `campaign/vm-core` (171226eb), and its base is `campaign/vm-spec`.

First merge `campaign/vm-spec` at ec68c1a6 or later (D22, D23, D24 and the round-13 loader refusals; round 14's atomic-stops text lands there soon, so merge again if it has). Then merge `main`. Do not rebase.

**1. Adopt D22, D23 and D24 together.** Follow vm-spec DECISIONS "What vm-model and vm-core must now follow (round 13)":
- IO requests are values, performed only at the Program's Top loop (D23). Applying an Action builds a request cell.
- A Case over a request takes its Default in either mode, and otherwise stops `Unsupported vm effect` (D24).
- A Book entry never performs an effect (D22).
- Pass every vm-spec golden and control, including the 121 new loader refusals, at their frozen outcomes and `calls`.
- Add VM mutants for the eager rule, for performing a dropped request, and for refusing a Case with a Default.

**2. Atomic stops.** **Coordinator ruling (atomic stops), settling vm-lockstep findings 1 and 2.** No refusal, halt or exhaustion changes machine state: every check a step can fail (operand inspection, NatRange, IO.OP inspection at Return to Top, limits) happens before the step mutates frames, `act`, `top`, the heap or the meters. The only exception is the fuel debit that SPEC §7 already prescribes, and the Enter-debit rule that keeps it. So the VM must not pop a Gather frame before it inspects operands or tests NatRange. Return to Top refuses an ill-typed IO.OP before it drops `act`. The lockstep (branch campaign/vm-lockstep, tests/compiler-vm-lockstep/) records the current deviations as named halting relations; these rounds remove them. Fix both deviations in vm.wat, and add mutants that reintroduce each one.

**3. Two confirmed findings from your round-6 review.** Evidence is in `/private/tmp/claude-501/-Users-ericfode-src-knot--claude-worktrees-perch-style-framework-c2cdfc/d7a4ddd4-7d29-4f63-803d-fca5b417c923/scratchpad/campaign-infra/vm-core-r7-findings.md`.
- (a) The gate cannot see how the VM classifies arrow-typed and none-field Book results. Pin it, and add a mutant that turns Unsupported into HostFailure.
- (b) describe counts a visit before it inspects the word: inspect first. Freeze the 1,048,577th-visit ill-typed control from the seed or by literal review.

Keep the differential lane and the mutant study green, and rerun the study, reporting its kill rate. Rebuild `vm.wasm`, pin its sha in `vm/build.json`, and report it.

Finish with:
- `BEND_NO_TELEMETRY=1 npm run -s gates` exiting 0, with per-gate lines;
- the vm-core summary line.
