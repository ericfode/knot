# baseslice implementation report

The Base-slice plan and its first independent step, **BS1 enum-source
qualification**, are complete. `npm run -s gates` passes **15/15** registered gates
with the default four workers. This is acceptance of the owned branch's BS1
contract. Main integration, imported Base and VM execution remain separate.

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
`npm run -s gates`, exit 0, four workers. Every gate exited 0. Its ignored raw
record is `.local/gates/run-lat78q9s/summary.json`.

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

## Build-guard correction and historical failures

Initial full runs failed at legacy 30–60-second seed-native-build guards; even
serial scheduling hit frontend's 30-second and structural's 45-second guards.
The six affected harnesses now use a 180-second minimum for exact seed-prefix
`-o` builds. Flat-store uses the same shared guard. Program timeouts and all
byte/depth/fuel budgets, fixed expectations, proof obligations and mutant
requirements are unchanged.

A later serial run hit the seed's `found no clang` discovery diagnostic in
flat-store; default scheduling reproduced it in structural. Apple clang 21 was
installed, and twenty direct Bun discovery probes succeeded. The shared guard
permits at most two retries for that exact discovery diagnostic with exit 1 and
empty stdout, retaining every failed attempt. All other failures and timeouts
still fail immediately. Persistent missing-clang failures stop after three
attempts. The final successful run needed no discovery retry in structural or
flat-store. Every affected receipt hashes the guard.

Census regeneration changed exactly four gate SHA-256 fields in accepted.json.
It changed no fixture hash, classification, approval or other census manifest.
The fresh comparison has 64 identical, ten volatile-only and seven semantic
receipt differences. All seven semantic differences are harness/guard input
identities; two also carry the earlier fail-closed host-adapter identity. No
program observation changed. Shared execution receipts were not refreshed.

Historical failed/cancelled runs remain in ignored `.local/gates/`:
`run-g0kd4rov`, `run-049ignie`, `run-fvsfzgw_` and `run-dp8fuq9y`. They are not
aggregated into the final pass. The final pass comes from one fresh full run.
[The review log](../../../docs/perch-review-log.md) records prevention and evidence.

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
