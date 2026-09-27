# Knot style campaign

Started 2026-09-26 at the user's request: bring the whole project up to the
three style targets. This is an implementation campaign, coordinated by
**Configure Perch for Knot**, with continued work through a dedicated heartbeat.
The [state file](style-campaign/state.json) records assignments and evidence.
The completed package-publication campaign remains a separate workflow.

## Target and baseline

Every declaration should earn conceptual compression, high-dopamine readability,
and a highly memetic identity. The form should have ideas, vocabulary and rhythm
that reward recognition and make the reader want more of this particular style.
Use the user's [three-axis objective](../AGENTS.md) and the
[rubrics](../perch-style.json). Novelty alone, ornamental jargon, self-praise,
or a new abstraction with no explanatory payoff do not satisfy the objective.

The [initial receipt](perch-calibration/style-project-2026-09-26.json.gz) contains
1,887 declarations and 5,661 ratings. It recorded 1,246 meeting the conceptual
target, 779 meeting delight, five meeting memetic identity, and none meeting all
three. Ten files were unranked and one had no declarations. These are a dated
baseline, not the current state of concurrently changing compiler code.

The [CSV](perch-calibration/style-project-2026-09-26.csv) is the complete initial
unit queue. The generated [inventory](style-campaign/inventory.json.gz) joins that
receipt to a fresh parser inventory, identifies changed source/helper context,
and keeps new, missing, empty and unranked files visible. Refresh it without
provider calls with:

```sh
node scripts/perch-style-campaign.mjs --output=docs/style-campaign/inventory.json.gz
```

It is a baseline comparison, not an aggregate of later improvement receipts.
Those remain linked by batch in the state file until a consolidation pass.
Stale ratings cannot establish current quality. A score is an advisory reading
judgment; it does not establish equivalence or measured psychological effects.

## Work order and ownership

The user's later 2026-09-26 instruction temporarily takes priority over the wave
queue: use GPT-6 Astra at **max** reasoning for a small feasibility pilot. After
new-chat creation was blocked, the user explicitly authorized the current
checkout. The [scoped pilot](style-campaign/scoped-pilot.md)
must demonstrate all three targets on its complete changed scope before wider
dispatch resumes. Keep queued components and prior results; do not call a
memetic deficit pilot success. The state file records the current execution
mode, historical evidence and the current unaccepted disposition. The clean-main
handoff preserves the candidate as a snapshot and restores the accepted runner;
the completed historical review remains uncertain on the memetic axis.

| Wave | Scope | Owner and first increment |
| --- | --- | --- |
| 1 | IntMap | Existing IntMap chat: path/branch vocabulary and the mirrored get/set/remove family. Test a concrete simplification of branch pruning before touching the public API. |
| 1 | OutputBuilder | Existing OutputBuilder chat: the shared chunk/join/suffix grammar across text and bytes; keep checked-byte error precedence and linear emission. |
| 1 | Compiler | Compiler Planning: one coherent family after its active structural-field checkpoint. Scope/usage algebra or a dispatcher family is preferable to a broad rewrite. |
| 2 | Vec, Source, Symbols, TermStore | Existing package owners, at most two style batches active at once. Prioritize representation, boundaries and recurring vocabulary before isolated projections. |
| 3 | Remaining compiler and runtime research | Compiler owner and runtime coordinator respectively; preserve their active semantic milestones and demonstrated backend boundaries. |
| 4 | Laws, proofs, models, tests, examples and retained experiments | Owning component reviews the remaining inventory. Canonical proof terms and intentional failure specimens stay visible; changing historical evidence to win a score is forbidden. |

All four waves are in scope. A tiny helper's low score is not permission to add
ceremony. An intentional negative fixture remains a negative fixture. Historical
repair candidates and receipts are immutable evidence; record a disagreement or
an applicable descendant improvement instead of rewriting the record. Such a
disposition is not an automatic three-axis pass and remains visible at closeout.

Owners keep their existing source boundaries. The style coordinator owns this
document, its state/inventory tool, shared rubric maintenance and consolidation.
Owners may improve working sources and record an unreleased revision, but this
campaign does not silently republish packages, update compiler dependency hashes,
or restart the paused publication automation. Retain existing release evidence.

## One batch

1. Inspect Git state and the latest owner state. Select one concept family and
   no more than 24 parsed declarations for live review. Record the concrete
   reading problem, intended improvement and unchanged contract **before**
   judging the candidate. Label the author's taste hypothesis separately from
   a preference actually expressed by the user.
2. Freeze the baseline source, contract and independent test hashes. Use GPT-6
   Astra at max reasoning for campaign repairs; exclude Luna 5.6. Make one substantive
   candidate. Preserve its first result. A compiler-rejected generation gets
   at most one diagnostic retry; record it separately and reject remaining
   failures. Do not silently hand-fix a failed model experiment or alter tests.
3. Check syntax, types, quantities, complete proofs and applicable independent
   behavior/backend/performance gates. Existing contracts and assertion bodies
   stay fixed. If an implementation refactor invalidates a text-based mutation
   locator, re-anchor that locator with evidence; preserve the mutant's intended
   semantic violation and original observing assertion. A changed assertion
   would require a separate reviewed gate increment, not a style acceptance.
4. Run targeted semantic Perch checks and all three style checks on changed
   declarations. Reuse matching receipts; retain source/helper/rubric/model
   identities, full distributions and context limits. Rate each declaration;
   family-level praise cannot excuse an unrated member. Never retry a provider
   failure repeatedly or rerun unchanged candidates to hunt a nicer score.
5. Review the actual diff. Keep an improvement only with concrete reading
   benefits and deterministic acceptance. Record remaining low/uncertain axes
   without calling them passes. Reject additional indirection, lost symmetry,
   invented vocabulary without ideas, or performance regressions even if the
   judge likes them. A defensible no-change decision is evidence, not success.
6. Save before/after snippets, target identities, all gate outcomes, rating
   distributions, accepted/rejected disposition and open work in an owner-local
   `STYLE_CAMPAIGN.md` and receipts directory. Commit only explicitly owned
   paths. The coordinator records that commit and selects the next increment.

Example commands, with a new output filename for each receipt:

```sh
npm run lint:style -- --live packages/int_map/main.bend \
  --reuse=docs/perch-calibration/style-project-2026-09-26.json.gz \
  --output=packages/int_map/receipts/style-wave-1.json
npm run lint -- packages/int_map/main.bend::branch \
  --rules bend-machine-arithmetic,perf-loop-invariant-work --json
```

## Calibration and continuation

The initial memetic distribution is unusually selective. It may reveal weak
code, a context limitation, a size/role bias, or disagreement with the user's
taste. Do not assume one explanation. Compare accepted improvements and
rejected embellishments across small helpers, datatypes and larger dispatchers.
Record a concrete preference before a new candidate is judged. Reserve fresh
examples for any later rubric change; previously scored source is not held out.
Do not lower bars, replace the baseline or promote the judge merely to shrink
the backlog. Feed demonstrated noise into `docs/perch-review-log.md` under the
existing maintenance procedure.

The heartbeat checks every 15 minutes. It reads compact owner progress and
retained evidence, advances ready work, and starts at most two package/research
style batches concurrently; the compiler owner can integrate style at its own
safe checkpoint. Each wake dispatches at most one new bounded batch. It does
not duplicate active work, repeatedly request unchanged scores, or flood chats
with unchanged status. Notify on an accepted improvement with a code example,
a material rejected approach or calibration finding, completion, or a blocker
requiring user judgment.

At a wave boundary, consolidate matching receipts and inspect new/changed units.
Run a paid full inventory only when it provides new coverage. Completion requires
an up-to-date inventory, evidence for every applicable declaration, all three
targets met, and all deterministic gates green. Review dispositions and
historical/unparseable specimens are reported separately; no silently excluded
files, averaged-away failures or subjective waivers count as automatic success.
If progress eventually requires human taste examples, retain the unresolved
queue and ask with actual code alternatives. Until then, continue useful work.
