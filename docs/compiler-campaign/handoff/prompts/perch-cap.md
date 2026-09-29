You are one executor in the Knot compiler campaign, working in the dedicated git worktree for branch `campaign/perch-cap` (from `main`). Another agent, the coordinator, reviews and merges. You own only this increment. This is Perch-context tooling (JavaScript), not compiler code. The user authorized ongoing Perch configuration maintenance (AGENTS.md, docs/perch-maintenance.md).

Read first: `AGENTS.md` (the Perch sections), `docs/perch.md`, `docs/perch-style.md` (context and caps), `docs/perch-maintenance.md`, `scripts/perch-context-interfaces.mjs`, `scripts/perch-style.mjs`, `tests/perch-context/` (check.py, its controls and mutants), and `docs/compiler-campaign/GATES.md`.

Environment:
- Always export `BEND_NO_TELEMETRY=1`.
- Never read or copy any `.env`.
- Make no live Perch or provider call. Everything here is offline: preflight, the context builders, gates.
- Gates: `BEND_NO_TELEMETRY=1 npm run -s gates` must exit 0, and `npm run -s gates:verify` must pass. Receipts of gates you did not change are left to the coordinator: restore them with `git checkout -- <path>`.
- Git: commit coherent increments with explicit paths. Do not push, merge or rebase onto other branches. Do not touch other worktrees.

----
YOUR INCREMENT: perch-cap.

**Problem.** `fitInterfaceContext` turns full callee and caller bodies into interface summaries until the encoded state is at most 60,000 bytes. When all of them are interfaces and the state is still over the cap, it throws `Style context too large after interface summaries`, and the `perch-context` gate fails.

On campaign/literals-integ, `src/check.bend::run` (a large dispatcher that reaches over 100 declarations) hit that error at 64,553 bytes. The branch then changed code and task files to fit, measured by the tool:
- it spelled out the two `C.exhausted` uses;
- it reordered rows;
- it swapped three owner-held task files for verbatim excerpts.

It fit with a margin of 59 bytes. Any later row, for example from the modules merge, breaks it again. Shaping source to fit a tool cap is what AGENTS.md forbids ("never change correct code to satisfy a model"), so the fix belongs in the tool.

**Build a third fitting tier below interfaces.**
- When the interface tier is exhausted, replace interface summaries with a names-only entry. Proceed in a deterministic order: largest saving first, then path, then name. A names-only entry keeps the qualified name and its path, and at most a one-line signature if you can show that fits.
- Record each replacement in `provenance.summarized` with reason `context-state-names-only`.
- Give the judge-visible state an explicit marker saying which context was cut to names, so the judge knows it was cut.
- Never shorten the primary unit's source or the task/cohort text. Throw only when the primary source, the task and the names-only list alone exceed the cap, and name that case in the error.
- Keep both caps as they are: the 60,000-byte state cap and the 48,000-byte composition cap.

**Acceptance.**
1. **Byte-identical where nothing is cut.** Every unit that fits today has a byte-identical encoded state. Measure this over the whole manifest preflight on main (`node scripts/perch-style.mjs --preflight --manifest=docs/compiler-campaign/manifest.json`), comparing state hashes before and after. Report the counts. Existing receipts must not move.
2. **perch-context gate.** Add controls and mutants to `tests/perch-context`:
   - a unit over the cap after interfaces now fits with the marker and the provenance entries;
   - a unit whose primary source alone exceeds the cap still fails, with the new error.

   The mutants: dropping the marker, shortening the primary source, skipping the tier, and a nondeterministic order. The gate kills each.
3. **Measure on the motivating tree.** Export campaign/literals-integ (`git archive`) to scratch and apply your tool change there. Report `check.bend::run`'s state three ways:
   - (a) as the branch has it;
   - (b) with the two `C.exhausted` uses restored to `C.exhausted(C.Checked,token)`;
   - (c) additionally with the three original task files restored: `research/compiler-fields/SPEC.md` for `checking`, `tests/compiler-modules/SPEC.md` for the modules group, and `tests/compiler-nest/SPEC.md` for the nest matrix groups.

   Report which units need the names-only tier and how much was cut. Also report the three largest compositions against 48,000, and whether any group's composition would fail with the original tasks. If a composition fails, propose (do not implement) the smallest honest fix.

   Do not change campaign/literals-integ; the coordinator applies the reverts there after this merges.
4. **Documentation.** `docs/perch-style.md` states the tier and its marker. Add a `docs/perch-review-log.md` entry in the maintenance format: evidence (literals-integ's 8ea6faf and its 59-byte margin), the root cause (the tool cap shaped the source), the change, the controls, and the remaining uncertainty. Judge calibration on names-only contexts is unmeasured, so leave the tier advisory.
5. Run `npm run -s gates`, `npm run -s gates:verify`, `npm run lint:rules -- --json` and `npm run lint:verify`. Report exact results.

Finish with a concise report:
- what changed;
- commits;
- gate results;
- the byte-identity counts;
- the measurements of item 3;
- known limits.
