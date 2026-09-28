# Generics and quantity arguments

`knot-generics-1` checks erased type/quantity parameters, nested nominal
applications, invariant phantom parameters, `Kind(q)` meets, compact quantity
forms, generic fields and first-live-parameter descent. It projects checked
terms into the existing evaluator and fielded Wasm backend. The contract is
[research/compiler-generics/SPEC.md](../../research/compiler-generics/SPEC.md).
`src/check-dispatch.bend` sends a book with generic syntax to this checker;
the original monomorphic path and its fixed assertions remain in place for
every other book.

The frontend's generic-header pin was superseded under the coordinator's
review-round-1 authorization (`5eea108`). Main's classify-2 pins for `Name<...>`
in parameter, return and binding types conflict with the same capability, and
two of its laws fail on the generic parser. They are unchanged here; see
[Review round 1](#review-round-1) for the proposed supersession.

The mechanism is a type-expression algebra with rigid binder indices. A single
sequential substitution list instantiates later parameter domains and results.
Literal quantity meets reduce; `&2` is identity and `&0` is an absorber for
symbolic expressions. Remaining symbolic syntax stays invariant. The checked
result crosses into runtime terms through one erasure module.

Every generic family uses a boxed `[tag][live fields...]` cell. An erased marker
selects the existing fielded representation even for nullary constructors,
without adding a live slot. Closed monomorphic enums remain ordinals. Abstract
values are opaque words; their checked instantiations determine whether the
word holds an ordinal or a cell address. Each source function has one emitted
body, with erased arguments absent from its live signature.

| Independent expectations | Fixtures | Seed calls | Origin |
| --- | ---: | ---: | --- |
| Original corpus | 40 | 122 | Unchanged source, outcomes and regeneration script from the integration base |
| Two-quantity short form | 1 | 4 | Frozen before implementation in `16d5d22` |
| Compact reusable binder | 1 | 4 | Frozen before implementation in `629c51f` |
| Kind and representation boundaries | 15 | 26 | Seed probes and literal Unsupported boundaries |
| Local type-value and dispatch boundaries | 9 | 9 | Fixed before their corresponding boundary repairs |
| [Bare family names](bare-families/README.md) | 7 | 3 | Frozen in `0c4eb10` before the arity repair |
| Total | 73 | 168 | 44 seed-valid programs and 29 seed rejections |

The original `closure-apply` and `template-twice` pins remain. Optional
`match-erased-type` and `alias-type` remain Unsupported. Five independent literal
ABI controls inspect erased parameter counts without invoking generic exports.

| Type-correct mutant | Fixed witness | Observed violation |
| --- | --- | --- |
| Skipped substitution | `box-unbox` | Rejects the valid instantiated constructor/function path |
| Erased argument kept live | `unbox` ABI | Two live arguments instead of one |
| Wrong quantity meet | `meet-not-reusable` | Accepts an invalid reusable quantity |
| Missing arity check | `type-arity` | Accepts excess type arguments |
| Bare quantity default | `bare-family-parameter` | Accepts a bare all-quantity family name |

Each mutant is seed-typechecked and exercised in native and Bun lanes. A parser
failure, host/internal error, exhausted budget or invalid Wasm cannot count as
a semantic kill. Seed regeneration never invokes Knot or derives expectations
from emitted code.

```sh
export BEND_NO_TELEMETRY=1
python3 tests/compiler-generics/regen.py
python3 tests/compiler-generics/check.py
npm run -s gates
npm run -s gates:verify
```

The gate uses `tests/compiler-fields-wasm/compile.bend` for the fielded profile.
The default enum emitter still rejects fielded books. Node calls use the
`--profile=knot-fields-wasm-1` host adapter and only closed monomorphic enum
signatures. Generic/cell-valued exports are for compiled callers. The existing
one-page arena and exhaustion policy apply; there is no reclamation or owned
storage guarantee.

`src/types-PROOF.bend` fills 12 laws, including universal substitution composition
and the quantity meet algebra. `src/type-erasure-PROOF.bend` fills 17 laws,
including erased evaluator transitions with their one-step fuel adjustment.
The complete frontend proof fills the restated generic-header acceptance law.
These proofs and finite differential observations are distinct from a universal
checker-soundness or compiler-correctness theorem. The bounded proof and review
obligations are in [LAW_REVIEW.md](LAW_REVIEW.md).

Local type/quantity normalization, type-returning definitions, value-indexed
families, constructor-local type binders, live static arguments, type-variable
application, pair sugar, function types, templates and general lexicographic
descent remain Unsupported. This increment covers only the documented S2 subset.
The legacy structural catalog
observer remains monomorphic and reports Unsupported for generic declarations.

The next integration step must settle the classify-2 supersession below,
compose this checker with the parallel modules/pattern/descent work (which
extends `generics.bend`; see the dual checker path in
[COMPILER-CAMPAIGN.md](../../docs/COMPILER-CAMPAIGN.md)), and run live Perch
semantic and style review. No package, runtime IR, evaluator or Wasm emitter
implementation changes are part of this increment.

## Review round 1

The branch merges main (`cac8dd2`) and fixes the confirmed findings:

- the authorized `generic` pin supersession (`5eea108`);
- bare family names (`0c4eb10` expectations, `feeea07` repair and mutant);
- the dispatch moved to `src/check-dispatch.bend`, shared `term_name`, the
  generics contract in its own task file and the manifest closures (`5f86882`);
- the dual checker path recorded with its convergence plan (`52c9e8a`).

**Blocker.** Main's classify-2 pins `Name<...>` in parameter, return and binding
types as Unsupported. The generic parser accepts them, so six classification
cases, three classification-gate mutants and the laws `return_type_application`
and `binding_type_application` conflict. Because every proof entry chains
through `src/PROOF.bend`, the committed tree's `npm run -s gates` stops nine
gates at their proof step:

| Run | Result |
| --- | --- |
| Committed tree, 4 jobs (161 s) | exit 1: 9 passed (census, lint:verify, owned-store, flat-store, perch-context, io-host, io-abi-2, bootstrap, selfhost); frontend, checker, structural, fields, wasm, recursion, fields-wasm, classification and generics failed at their proof entry; 3 trust gates blocked |
| Proposed supersession applied, 4 jobs (271 s) | exit 0: 21 of 21 passed |
| Proposed supersession applied, `--jobs 1` (854 s, load about 15) | exit 0: 21 of 21 passed |

Runner summaries: [committed tree](receipts/review-1/gates-tree.json),
[proposal, 4 jobs](receipts/review-1/gates-proposal.json) and
[proposal, 1 job](receipts/review-1/gates-proposal-jobs1.json).

The proposal (not committed; it changes classify-2 assertions and needs the
coordinator's authorization) gives the three seed-accepted application cases
phase expectations like `generic`, pins the after-prefix twins at
`Unsupported parse type-expression`, retires the three classification-gate
mutants with their anchors, restates `return_type_application` as the
typed-result transition and retires `binding_type_application`.
[CLASSIFICATION.md](../subsets/CLASSIFICATION.md) lists the derivations.

With the proposal applied, the generics gate reports 73 fixtures, 168 seed
calls, 284 evaluator and 284 Node agreements, 270 negative phase observations,
90 preserved artifacts, 28 byte-identical module pairs, 10 ABI arity
observations, 3 proof entries and 5 mutants killed in both lanes. The frontend
reports 30 classification fixtures in two lanes, 7 classification mutants and
180 downstream phase observations. `npm run -s gates:verify` passes 18 tests.

**Build cost.** Linking the second checker roughly doubles the generated code.
Sequential seed builds at load about 7 (main `cc9f2fd` → branch):

| CLI | Generated C (bytes) | Native build, real s |
| --- | ---: | ---: |
| parse | 1,240,306 → 1,838,731 | 2.8 → 3.8 |
| check | 2,497,614 → 4,824,594 | 5.5 → 11.2 |
| eval | 2,760,021 → 5,071,593 | 5.6 → 11.0 |
| compile | 3,413,614 → 5,733,438 | 7.2 → 11.9 |

Under main's default `KNOT_GATE_TIMEOUT_SCALE=4` the default four-job run
passes. The convergence plan (one checker) is the lever that removes the
duplicate code; no budget was changed.

**Style preflight (offline, 0 provider requests).** Full manifest: 24 groups,
1,196 units, 0 truncated units, 24 of 24 compositions available, 0 structural
blockers (main: 17 groups, 957 units, 0 blockers). The seven generic groups use
the 3,731-byte generics contract as their task. Targets mode over this round's
seven changed sources reports 227 declarations, 58 truncated contexts and an
unavailable 158,052-byte composition; the per-group manifest run is the
qualifying form. No style rating is claimed.

## Round 0 verification (`f39ba7e`)

The [scratch-run summary](receipts/gates.json) records **14 of 15 gates passed**;
`npm run -s gates` exits 1 on the retained frontend pin. Before that failure,
the frontend completed 14 reference fixtures, 28 parser-lane observations,
24 boundaries and four mutants. Its classification loop stops on the first
generic case, so its remaining classification checks are not reported as passes.

| Gate | Exact completed coverage |
| --- | --- |
| Frontend — failed | 14 reference fixtures; 28 parser observations; 24 boundaries; 4 mutants; then obsolete generic pin |
| Checker | 49 fixtures; 98 observations; 10 depth probes; 16 catalog-bound observations; 7 mutants |
| Structural | 16 fixtures; 64 observations; 4 boundary pairs; 7 mutants |
| Fields | 40 fixtures; 240 observations; 36 budget probes; 6 host probes; 12 level/inspection observations; 9 mutants |
| Wasm | 25 fixtures; 90 reference calls in 2 lanes; 64 rejection pairs; 44 boundaries; 7 mutants |
| Wasm trust | 3 entries; 0 proof holes |
| Fields trust | 4 entries; 0 proof holes |
| Structural trust | 2 entries; 0 proof holes |
| Owned-store | 3,532 cases in 2 lanes; 15 literal witnesses; 6 mutants |
| Flat-store | Per lane: 13,621 observations, 3,534 instances, 2 installed boundary states, 7 lifecycle checks; 2 lanes; 9 mutants |
| Recursion | 19 fixtures; 114 phase observations; 4 fuel probes; 3 mutants |
| Fields Wasm | 8 fixtures; 32 seed calls; 64 evaluator and 64 Node observations; 50 frozen enum-byte checks; 30 boundaries; 4 mutants in both lanes |
| Census | 39 source files; 677 declarations; 41 feature classes |
| Lint verification | 127 tests; 8 law-rule wiring controls |
| Generics | 66 fixtures; 165 seed calls; 278 evaluator and 278 Node agreements; 234 negative-phase observations; 78 preserved artifacts; 27 byte-identical module pairs; 10 ABI arity observations; 3 proof entries; 4 mutants / 8 lane kills |

The [generic receipt](receipts/generics.json) has 27 agreed fixtures, 23 required
rejections and 16 Unsupported fixtures. Across the two lanes, checking records
54 successes, 40 Invalid outcomes and 38 Unsupported outcomes. No exhaustion,
host failure or internal failure satisfies a fixture. All three complete proof
entries print `All terms check.` The gate wrapper's independent `gates:verify`
run passes 18 tests, including its six semantic mutants.

The scratch runner classified 81 artifacts: 63 identical, 8 volatile-only and
10 semantic. The semantic group contains changed compiler/source hashes and
the retained frontend failure. Existing gates' receipts
were left unchanged for coordinator refresh. The [census approval summary](receipts/census-approval.txt)
is also included verbatim in the implementation commit message.

A preceding parallel run exceeded existing build and harness timeouts. Its
[resource-exhaustion summary](receipts/gates-resource-exhaustion.json) remains
as failed-run evidence. The final run uses `npm run -s gates -- --jobs 1` with
the same assertions and time budgets.

The [classification transition](receipts/classification-transition.json) records
fresh Bun observations of the old generic fixture: parse/check/eval succeed and
eval returns `Box{On{}}`; the default enum compiler reports
`Unsupported check constructor-fields` and preserves the old output. Reconciling
the old harness requires phase-specific expectations, not one shared rejection
pin. The [legacy catalog controls](receipts/catalog-boundaries.json) retain two
Bun Unsupported observations at its monomorphic inspection boundary.

Final [offline preflight](receipts/preflight.json): 386 declarations in 16 files,
zero provider requests, 58 truncated contexts (6 caller/byte, 23 file, 29 helper
limits). These same 58 declarations cannot receive the supporting-role exemption.
The combined composition is unavailable: 195,340 bytes against 48,000, with
60 collaborators outside the group and 51 nonlocal imports. Its task is present
(4,152 bytes). Exit 3 records 59 structural blockers. Compression, Delight,
memetic identity, Anticipation and Payoff remain unreviewed; no style pass or
semantic Perch review is claimed. The earlier preflight remains as historical
evidence under `preflight-before-dispatch.json`.
