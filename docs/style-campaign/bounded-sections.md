# Three bounded style trials

The user's 2026-09-27 direction is to try rewriting small sections central to
Knot and one standard library, instead of bringing the whole repository to
Memetic 3 or Payoff 3. This replaces the adaptive-task pilot prerequisite and
the universal campaign completion criterion. Existing rubrics, theorem claims
and deterministic acceptance gates remain unchanged.

Baseline: main `3dc7774`. Model: GPT-6 Astra, max reasoning. Owner chats received
the assignments below. Delivery is not evidence of completion; the
[state file](state.json) and each owner's receipts record actual progress.

## Central laws

Owner: Review plans for Perch (`01a0e16c-05d0-7543-a087-e84c21ebb01d`), using
its isolated checkout. Compiler Planning retains compiler subtree ownership.

Scope: five declarations in `src/check-LAWS.bend` and their matching proof
entries in `src/check-PROOF.bend`:

- `empty_sequence_preserves_uses`
- `repeated_affine_level`
- `live_erased_occurrence`
- `erased_occurrence_preserves_identity`
- `refined_constructor_is_fresh`

Author's reading hypothesis: arrange the laws so the reader sees one progression:
sequencing accounts for affine use, erasure suppresses use while preserving
identity, and a refined constructor is a fresh value. The existing statements
already describe useful boundaries; stronger claims require separate proofs.

Freeze every original quantified domain, quantity annotation and proposition.
Keep the original statements and proof bodies as independent snapshots and check
the complete proof entry point. Do not rename public theorem identifiers, weaken
claims, add assumptions, introduce axioms, or claim checker soundness. Verify
the unchanged compiler observations appropriate to the actual diff. A layout
change alone is not a reason to invent a new abstraction.

## Compiler pipeline

Owner: Compiler Planning (`01a0dea7-91b5-7480-b80a-7fe9584f9966`).

Scope: `checked`, `parsed` and `source` in `src/driver.bend`, with only directly
necessary helpers. The checker laws above belong to the separate trial.

Author's reading hypothesis: the path from text through tokens and a parsed
program to a checked book, including first-error propagation, should read as
one composition. The current driver mixes pure stage transitions and IO across
several functions. A clearer composition must justify any new helper.

Preserve the public driver behavior, language profile, all three independent
fuel budgets, error category/status/location, first-failure order and callback
timing. Parser, checker and emitter semantics stay fixed. Use existing complete
proof and native/Bun frontend, checker and Wasm integration gates. Record new
coverage separately if an actual gap is found; preserve existing assertions.
Evidence belongs in `src/style-campaign/compiler-pipeline-1/`.

## IntMap path family

Owner: Build and publish Bend integer maps
(`01a0deee-b662-7730-98de-0679e0f47959`).

Scope: `get_path`, `set_path`, `remove_path`, and necessary `low`, `high`, `value`
and `branch` vocabulary in `packages/int_map/main.bend`. The previously accepted
empty-pair branch simplification remains the starting point.

Author's reading hypothesis: learning lookup's path grammar should prepare the
reader to understand insertion and deletion, with their terminal actions and
pruning difference visible. A shared operation earns its place only by making
those relationships easier to recognize.

Keep the SPEC and INTERFACE, independent model, all law claims and assertions
fixed. Preserve full-width keys, persistence, absence versus stored zero,
depth32 paths, no child promotion during pruning, low-bit-first fold order and
the left/right order of noncommutative union. Run complete proofs, native/JS
conformance, all 11 type-valid semantic mutants and existing scaling/model
gates. Compare exact baseline performance when traversal changes. Preserve the
published hash, historical release receipts and compiler dependency pins.
Evidence belongs in `packages/int_map/campaigns/int-map-paths-2/`.

## Trial and closeout rules

Each owner freezes source and independent gate identities before one substantive
candidate. Preserve the first result; allow at most one separately recorded
compiler-diagnostic retry. This is a bounded comparison, not an open-ended
search. Unsuccessful trials keep their evidence and an explicit disposition.

Run targeted semantic Perch, current role-aware declaration style review and a
bounded family review with fixed task evidence. Retain distributions, source
and helper hashes, model/rubric identities, coverage and context limits. Every
changed declaration needs coverage; an expanded whole-file judgment must be
identified separately from the selected family. Do not rerun unchanged source
to obtain a different score or run a whole-repository inventory for this wave.

Assess concrete reading benefits alongside unchanged deterministic gates.
Record keep/reject/no-change independently for each trial. A useful verified
revision may be kept with explicitly unmet style targets; that is a partial
style result, not an automatic pass. Missing live evidence remains unavailable.
The numerical targets and helper/leading distinction stay unchanged.

Commit explicit owned paths. Law work from an isolated branch is integrated
only as its narrow reviewed increment, not the entire divergent branch. The
coordinator owns shared campaign instructions; Review plans for Perch records
dispatch and results in the state file. Do not modify another owner's pending
work. Do not publish packages or expand compiler milestones for this trial.

The wave ends with three reviewable dispositions and verified commits for any
retained source. A stalled or rejected family does not block the others. The
former broader queue stays parked unless the user selects further work.
