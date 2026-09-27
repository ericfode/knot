# Knot style campaign

Started 2026-09-26 at the user's request. On 2026-09-27 the user replaced the
whole-project style objective with independent trials on small central sections:
laws, compiler integration and one standard library. The current
[bounded plan](style-campaign/bounded-sections.md) defines their scope and owners.
The [state file](style-campaign/state.json) records assignments and evidence.
The completed package-publication campaign remains a separate workflow.

## Shape adoption passes (from 2026-09-27)

The user's 2026-09-27 request replaces owner batches that raise one declaration
at a time with **shape adoption passes** judged at the figure. The framework is
recorded in [KNOT-SHAPES.md](KNOT-SHAPES.md), the version 7 section of
[perch-style.md](perch-style.md) and the review log. Its premise is the survey
result below: compression and delight pass broadly, supporting helpers pass under
version 5, and the remaining failures sit in the declared lead and the
composition, judged without the repertoire they were supposed to be quoting.

One pass is one shape from the sheet applied to one owner's figure:

1. The owner writes or updates a figure manifest under
   `docs/style-campaign/figures/` naming the declarations, the lead, the task
   and the opaque interfaces. The coordinator owns the sheet and the manifests'
   schema; the owner owns the source.
2. Record the reading hypothesis and which sheet shapes the figure claims. Run
   `npm run lint:style -- --live --figure=<manifest>` once on the frozen baseline.
3. Make one substantive candidate under the existing generation, gate and
   retry rules. Layout conventions from the sheet apply first: stop arms
   first, shared spines, laws in mechanism order, mirrored proofs.
4. Run the figure review once on the candidate. Keep the change only with a
   concrete reading benefit and deterministic acceptance. Declarations that fit
   no sheet shape are the design work; record them, do not force them.
5. A shape earns a place on the sheet only with two instances in different
   vocabularies. Retiring or splitting a shape is a coordinator change with a
   review-log entry.

Prepared figures: `owned-time-slicing`, `int-map-paths`, `symbols-trie` and
`compiler-pipeline`. All four validate offline with complete context; the
compiler pipeline composition was unavailable under version 5. The first live
version 7 results are recorded under `docs/perch-calibration/style-v7-2026-09-27/`:
no figure qualifies yet, IntMap's lead meets its expressive targets, and
composition memetic identity remains the open axis. Human anchors recorded
before model review remain the prerequisite for any threshold discussion.

The passing criterion for the repository is: every mechanism-scope figure
returns exit 0 under the current rubric, and inventory outside mechanism scope
is reported. Fixtures, models, benchmarks and retained evidence are not gated.
The bounded-trial history below is retained unchanged.

## Target and baseline

Selected families should earn conceptual compression, high-dopamine readability,
and a highly memetic identity, with role-appropriate supporting helpers.
The form should have ideas, vocabulary and rhythm
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

The user's 2026-09-27 instruction supersedes the pilot-first prerequisite.
Use GPT-6 Astra at **max** reasoning for three independent bounded trials:

| Trial | Scope | Owner |
| --- | --- | --- |
| `central-laws-1` | Five checker boundary laws: affine sequencing, erased occurrences and fresh constructor refinement, with matching proofs. | Review plans for Perch, isolated worktree; Compiler Planning retains compiler ownership. |
| `compiler-pipeline-1` | `src/driver.bend` text-to-checked-book pipeline and directly necessary helpers. | Compiler Planning. |
| `int-map-paths-2` | IntMap's mirrored lookup/insert/remove path family and necessary projections. | Existing IntMap chat. |

See the [bounded plan](style-campaign/bounded-sections.md) for exact declarations,
fixed observations and independent closeout. The adaptive-task
[scoped pilot](style-campaign/scoped-pilot.md) and its candidates remain historical
evidence with their actual unaccepted dispositions. They do not block this work.

The former wave queue below is parked for later user selection. Completing the
three current trials does not authorize automatic expansion to the whole repo.

| Wave | Scope | Owner and first increment |
| --- | --- | --- |
| 1 | IntMap | Existing IntMap chat: path/branch vocabulary and the mirrored get/set/remove family. Test a concrete simplification of branch pruning before touching the public API. |
| 1 | OutputBuilder | Existing OutputBuilder chat: the shared chunk/join/suffix grammar across text and bytes; keep checked-byte error precedence and linear emission. |
| 1 | Compiler | Compiler Planning: one coherent family after its active structural-field checkpoint. Scope/usage algebra or a dispatcher family is preferable to a broad rewrite. |
| 2 | Vec, Source, Symbols, TermStore | Existing package owners, at most two style batches active at once. Prioritize representation, boundaries and recurring vocabulary before isolated projections. |
| 3 | Remaining compiler and runtime research | Compiler owner and runtime coordinator respectively; preserve their active semantic milestones and demonstrated backend boundaries. |
| 4 | Laws, proofs, models, tests, examples and retained experiments | Owning component reviews the remaining inventory. Canonical proof terms and intentional failure specimens stay visible; changing historical evidence to win a score is forbidden. |

These former waves are not the current completion criterion. A tiny helper's low score is not permission to add
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
   Judge the complete selected family with fixed task evidence. Identify any
   expanded whole-file context separately; outside-scope attention does not
   turn a bounded trial into a repository migration. Helpers use the current
   supporting-role targets. Missing coverage or unavailable evidence is explicit.
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

The existing heartbeat may reconcile owner progress and retained evidence for
these three trials. The current scope overrides its historical broader queue:
do not launch another family, restart the old pilot, or repeat unchanged scores.
At most two package/research batches and the compiler owner's bounded increment
run concurrently. Notify on an accepted improvement with a code example,
a material rejected approach or calibration finding, completion, or a blocker
requiring user judgment. This document does not change the saved schedule.

Close each trial with its exact diff, deterministic gate results, current
per-declaration and family style evidence, and a keep/reject/no-change disposition.
A retained improvement with unmet style targets is explicitly a partial style
result. Missing live review remains unavailable evidence. Full automatic style
success still requires every selected target and required composition check to
pass; no averaged-away failures or subjective waivers count as a pass.

This wave is complete when each of its three trials has a reviewable disposition
and any retained source is verified and committed. A rejected candidate need not
hold the other two open. Do not run a paid repository inventory or resume the
parked queue to close this wave.
