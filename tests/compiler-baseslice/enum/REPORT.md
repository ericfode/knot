# baseslice implementation report

Current repair status is in [the review-round report](../review/REPORT.md).
The body and stored receipts below retain the pre-review BS1 checkpoint at
`a7817bf8`; they are historical evidence after the production repairs. The new
round stores its own passing-suite receipt without refreshing shared receipts.

The Base-slice plan and its first independent step, **BS1 enum-source
qualification**, are complete. `npm run -s gates -- --jobs=1` passes **15/15**
registered gates with the original frozen harnesses and limits. This is acceptance
of the owned branch's BS1 contract. Main integration, imported Base and VM
execution remain separate.

## Plan and ownership

[BASE-SLICE-PLAN.md](../../../docs/compiler-campaign/BASE-SLICE-PLAN.md) and
[BASE-SLICE-INVENTORY.json](../../../docs/compiler-campaign/BASE-SLICE-INVENTORY.json)
analyze main `aef68c86`, the unmodified seed Base and each reached declaration.
The plan includes frontend/checker, independent evaluation, core, image and
executor obligations, waiting owners and eight ordered increments with D7
oracles and semantic mutants.

| Roots | Runtime Base, JS / native | Static Base | Unresolved |
|---|---:|---:|---:|
| frontend | 39 / 39 | 53 | 0 |
| complete compiler | 72 / 72 | 110 | 0 |
| every declaration in every src/*.bend | 76 / 76 | 114 | 0 |

The compiler runtime partition is seven enum declarations qualified by BS1,
28 representation/primitive identities inspected on literals-integ `7aa8427e`,
and 37 remaining source/effect/opaque declarations. The latter branch's coverage
is unmerged source evidence. Modules `7ac90164` owns hash-verified Base loading,
name registration and reachable selection. Every imported Base book still waits
on that integration. Main's selfhost judge reads an explicit `base` availability
flag: 48 blocked rows name it, including negative twins and overlapping needs.
Neither the flag nor the reviewed selfhost pins changed here.

## Implemented BS1

Seven declarations are byte-for-byte excerpts of pinned Base: Unit, Bool, Cmp,
Bool.not, Bool.and, Bool.or and Cmp.is_eq. Knot checks them as ordinary source;
its production CLI still refuses imports. The reference books import unmodified
Base and use the identical consumers. This distinction qualifies source bodies,
not the loader or a synthesized production prelude.

The immutable oracle was committed in **3b32cc4c** before the runner. Implementation
and the initial complete BS1 receipt were committed in **b034708b**. The original
forty-book suite and its expectations remain unchanged.

- Seven books: two agree, four seed-rejected negatives, one deferred import.
- Thirty-two seed calls on interpreter and native lanes: 64 observations.
- Thirty-one unblocked reference calls: 62 independent evaluator observations
  and 62 validated Node Wasm observations across native/Bun-built Knot.
- Two byte-identical modules across the compiler builds.
- Eight filled source-algebra laws, zero proof holes; five universal finite-domain
  laws and three ground Cmp equations. They are not a compiler-refinement theorem.
- Five type-correct compiler mutants killed by classified wrong values or
  acceptance of a seed-rejected type. No build failure, timeout, crash or invalid
  Wasm counts as a kill.
- Ten existing-output preservation checks; every rejected/deferred book refuses
  check, eval and compile in both compiler builds and creates no fresh artifact.

[LAW_REVIEW.md](LAW_REVIEW.md) fixes the witnesses, mutation obligations, trust
boundary and reading hypothesis. [receipts/enum.json](receipts/enum.json) records
the original BS1 execution; all 44 input hashes still match. The full-suite run
re-executed BS1 successfully from the same inputs.

## Fresh gate results

[receipts/gates.json](receipts/gates.json) retains every exact normalized count,
source identities, receipt comparisons and the raw run's hash. The command was
`npm run -s gates -- --jobs=1`, exit 0, one worker. Every gate exited 0. The
committed receipt retains the raw summary hash and omits its machine-local location.
Its repository path is `tests/compiler-baseslice/enum/receipts/gates.json`.

| Gate | Result / exit | Exact wrapper counts |
|---|---|---|
| frontend | PASS / 0 | `{"boundaries":24,"fixtures":14,"lane_observations":28,"mutants":4}` |
| checker | PASS / 0 | `{"bound_observations":16,"bounds":2,"budgets":10,"fixtures":49,"lane_observations":98,"mutants":7}` |
| structural | PASS / 0 | `{"bounds":4,"fixtures":16,"lane_observations":64,"mutants":7}` |
| fields | PASS / 0 | `{"bound_observations":12,"bounds":2,"budgets":36,"fixtures":40,"host_boundaries":6,"lane_observations":240,"mutants":9}` |
| wasm | PASS / 0 | `{"boundaries":44,"execution_lanes":2,"fixtures":25,"mutants":7,"reference_calls":90,"rejects":64}` |
| wasm-trust | PASS / 0 | `{"entries":3,"proof_holes":0}` |
| fields-trust | PASS / 0 | `{"entries":4,"proof_holes":0}` |
| structural-trust | PASS / 0 | `{"entries":2,"proof_holes":0}` |
| owned-store | PASS / 0 | `{"cases":3532,"execution_lanes":2,"literal_witnesses":15,"mutants":6}` |
| flat-store | PASS / 0 | `{"bun":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621},"mutants":9,"native":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621}}` |
| recursion | PASS / 0 | `{"fixtures":19,"mutants":3}` |
| fields-wasm | PASS / 0 | `{"boundaries":30,"fixtures":8,"mutants":4}` |
| census | PASS / 0 | `{"classes":40,"declarations":425,"files":30}` |
| lint:verify | PASS / 0 | `{"law_rules":8,"tests":127}` |
| base-enum | PASS / 0 | `{"agreed_books":2,"byte_identical_modules":2,"declarations":7,"deferred_books":1,"evaluator_observations":62,"execution_lanes":2,"fixtures":7,"laws":8,"mutants":5,"output_preservation_checks":10,"proof_holes":0,"reference_calls":31,"rejected_books":4,"seed_calls":32,"seed_lane_observations":64,"wasm_observations":62}` |

Additional receipt/stdout counts, not exposed by the wrapper's count projection:

- Frontend: four boundary laws, six classification laws, twelve classification
  fixtures in two lanes, seven classification mutants, 72 downstream rejections.
- Recursion: 114 phase observations and four fuel probes.
- Fields-Wasm: 32 seed calls, 64 evaluator and 64 Node observations, 50 frozen
  enum-byte checks, five new checked laws; four mutants killed in both lanes.
- `npm run -s gates:verify`: 26 tests pass, including eight seed-build guard
  controls. This is a separate offline wrapper check.

## Pre-review correction and historical failures

The seven C3 frozen-edit findings were confirmed. The added decorators/imports
and guard input hashes are removed from `research/flat-store/check.py` and the
frontend, structural, fields, Wasm, recursion and fields-Wasm harnesses. All seven
are now byte-identical to base **ff44b974**. The matching census inventory is also
restored; census validation passes. Frozen expectations, proof obligations,
program observations and production compiler sources are unchanged.

The C4 finding was confirmed: `provenance.raw_summary` named an ephemeral local
run. That field is removed. The portable receipt records the raw summary SHA-256,
normalized results and **54 matching executed input identities**, including each
restored script. The guard and its controls remain as an uninstalled proposal;
their future integration requires coordinator authorization. Eight proposal
controls pass as part of the 26 offline wrapper tests; they do not alter this run.

The earlier 15/15 run at 4559c20a used the unauthorized harness integrations and
is historical evidence, not acceptance of the restored scripts. Earlier failed
and cancelled runs are preserved in ignored local evidence. A fresh default
four-worker run of the restored tree passed 14/15 gates; frontend alone timed out
at its original 30-second seed-native build guard. The identical standalone
native checker build succeeded in **18.48 measured seconds**. The subsequent
complete one-worker run passes all fifteen gates without changing a timeout,
expectation, fixture or compiler source. These runs are not combined into a pass.

The final receipt comparison has 64 identical, 15 volatile-only and 2 semantic
differences. Both semantic differences contain only the earlier fail-closed
host-adapter input identity; program observations are unchanged. Shared execution
receipts were not refreshed. See the appended pre-review correction in
[the review log](../../../docs/perch-review-log.md).

## Fast pre-review limits and minor dispositions

The committed-head C3/C4 audit exits 0 with no blocking or major executor finding;
the seven frozen-edit conditions and the host-path condition are absent. This is
a partial audit: ownership/generator metadata is unavailable, and the raw run's
snapshot predates the three final evidence documents. All 54 executed input
identities independently match committed HEAD. No full precheck pass is claimed.

- The inventory's three reported stale hashes are snapshot evidence, not current
  branch inputs. `source_ref` is `aef68c86`; the generator reads each source with
  `git show` at that ref. The hashes of `src/LAWS.bend`, `src/PROOF.bend` and
  `src/parse.bend` were rechecked against that Git object and match exactly.
- The alleged documentation input, `docs/compiler-campaign/inventory/accepted.json`,
  is executed census data. `tools/census/census.mjs` generates it in `build()`
  and reads/compares its bytes in `--check`; its identity belongs in the gate run.
- The original orphan note missed the relative Markdown link to the receipt in
  this report. The full repository path is now also stated above.
- The wrapper's count assertion changes from 14 to 15 because BS1 adds the
  fifteenth gate; it remains strict and all 26 tests pass. The additive-shape
  ruling stays with the coordinator. The trailer notes expect Claude by default;
  this task explicitly requires GPT-6.1 Sol, which every new commit uses.

## Coordinator and later increments

The task file requests a main-into-baseslice merge. The executor instructions
prohibit merges; the campaign and coordinator executor rules also reserve them
for the coordinator. No merge, rebase, push or other-worktree mutation occurred.
Task step 1's main integration and its twenty-gate reconciliation therefore
remain explicit coordinator actions. The fifteen owned-branch gates above do
not claim execution of main's additional gates.

BS2–BS8 require modules, nest/descent, literals, generics, closures, IO and the
image/VM track as assigned in the plan. Full Base loading, the forty-book ladder,
selfhost capability promotion and the C1/I2/I3 fixpoint are unrun follow-on work.
This task stops after the first independent increment.

Live semantic and style Perch are unrun under the no-provider instruction.
Conceptual compression, Delight and memetic identity, plus Anticipation, Payoff
and conditional Galaxy brain, are unreviewed. No style score, distribution or
automatic style pass is claimed. Coordinator review, merging to main and shared
receipt refresh remain separate from deterministic BS1 acceptance.
