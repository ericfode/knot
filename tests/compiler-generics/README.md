# Generics and quantity arguments

`knot-generics-1` checks erased type/quantity parameters, nested nominal
applications, invariant phantom parameters, `Kind(q)` meets, compact quantity
forms, generic fields and first-live-parameter descent. It projects checked
terms into the existing evaluator and fielded Wasm backend. The original
monomorphic path and its fixed assertions remain in place.

Integration is blocked by the unchanged frontend classification pin at
`tests/subsets/classification-cases.json`: it requires a valid generic header
to report `Unsupported parse generic-datatype`, while this increment accepts
that header. The corresponding old `generic-invalid` mutation anchor is also
obsolete. Neither assertion has been changed. The coordinator must reconcile
this explicit capability transition before an all-green integration claim.

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
| Total | 66 | 165 | 43 seed-valid programs and 23 seed rejections |

The original `closure-apply` and `template-twice` pins remain. Optional
`match-erased-type` and `alias-type` remain Unsupported. Five independent literal
ABI controls inspect erased parameter counts without invoking generic exports.

| Type-correct mutant | Fixed witness | Observed violation |
| --- | --- | --- |
| Skipped substitution | `box-unbox` | Rejects the valid instantiated constructor/function path |
| Erased argument kept live | `unbox` ABI | Two live arguments instead of one |
| Wrong quantity meet | `meet-not-reusable` | Accepts an invalid reusable quantity |
| Missing arity check | `type-arity` | Accepts excess type arguments |

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

The next integration step must reconcile the frontend classification pin,
compose this checker with the parallel modules/pattern/descent work, and run
live Perch semantic and style review. No package, runtime IR, evaluator or Wasm
emitter implementation changes are part of this increment.

## Final verification

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
