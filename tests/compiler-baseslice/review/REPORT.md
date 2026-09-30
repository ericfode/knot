# Baseslice review round 1

Starting head: `a7817bf89adbdbc819412af64f91d7265ad6ceb8`.

All three confirmed major findings are fixed. One complete final suite passes
15/15; its exact results and portable receipts are recorded below. No major
finding is disputed.

The three confirmed major findings are annotation shadowing, dotted typed-let
acceptance, and false Invalid classification of resolved function values.
`expectations.json` was frozen before production repairs. Two independent seed
freezes reproduce all 26 fixtures. Every rejected fixture reaches its intended
seed diagnostic in checking, interpreted execution and native compilation;
every accepted fixture has matching interpreted and native enum values.

The seven shadowing pairs cover result types, later parameters, erased parameters,
parameter/local/erased-local let annotations and dependent constructor fields.
Controls rename only the shadowing binder and its uses. An additional control
keeps a binder named `Flag` in its own annotation, before it enters scope.
The field control is checked/evaluated; the enum emitter remains Unsupported for
fielded declarations.

Typed-let probes retain the seed's distinction: ordinary dotted binders are
rejected as non-simple names; reusable dotted binders are rejected as malformed
promotion syntax; erased dotted binders are accepted. The latter requires a
conservative Unsupported until scope-aware binding is implemented. Simple-name
controls cover all three quantities.

Function-value probes cover a filled function and an erased forward reference.
Both are seed-valid and evaluate to `On{}`. Direct calls and local value shadowing
remain accepted. A genuinely free name stays Invalid. The original Base oracles,
regression assertions and program budgets are unchanged. The separate
seed-derived parameter-bound witness amendment is documented below.

Reproduce the immutable seed evidence with:

```sh
export BEND_NO_TELEMETRY=1
python3 -B tests/compiler-baseslice/review/regen.py
```

## Confirmed findings repaired

1. **Annotation shadowing:** `catalog.scoped_type` consults earlier parameter or
   field names before the global type catalog. Result annotations see all
   parameters. Let annotations use the current scope's binder names. Erased
   binders participate; own annotations and initializers precede extension.
   All seven rejected pairs now report `Invalid check type-shadow`.
2. **Dotted typed lets:** parsing rejects ordinary/reusable dotted binders with
   `Invalid parse binding-name`. The seed-valid erased form reports
   `Unsupported parse dotted-binder`. Simple-name controls still pass.
3. **Function values:** local lookup takes precedence over declared functions.
   A resolved bare function reports `Unsupported check function-reference`;
   a genuinely unknown name retains `Invalid check free-name`.

The initial targeted fresh run passes in native and Bun: **26 fixtures**, **156 phase
observations**, **13 accepted / 10 rejected / 3 Unsupported books**, **26 evaluator
observations**, **24 executed Wasm observations**, **12 byte-identical module
pairs**, and **28 output-preservation checks**. Three parseable/type-correct
native mutants separately restore global annotation lookup, dotted typed-let
acceptance and false-free-name classification. Each exhibits the frozen defect;
a parser failure, build failure or timeout never counts as its kill.

That initial run checks six laws with **zero holes**: four universal helper laws and two ground
spelling equations. They fix catalog fallback, the shadowing guard, global
function classification and local precedence. They do not prove whole-checker
soundness or parser conformance. The full loaded Base unsafe/foreign inventory in
the proof receipt is not runtime reach.

`base-enum` now runs these checks with its own fresh compiler family and adds
`review_*` counts. Its original seven fixtures, eight laws, five mutants, 31 calls
and all frozen observations/assertions remain unchanged. The gate registry and
all seven previously restored frozen harnesses remain unchanged. Census approval
adds seven helpers and the annotation helper's two-scrutinee match; generated source
manifests are current. No new compiler feature class is introduced.

Reproduce the targeted runner with:

```sh
export BEND_NO_TELEMETRY=1
python3 -B tests/compiler-baseslice/review/check.py
```

## Other review items and qualification limits

The source-attribution minor is fixed: String.append, not Bool.or, accounts for
the native source/intrinsic difference. The existing plan snapshot's counts and
source inventory remain a labeled historical snapshot.

Offline preflight on the five materially changed Bend files exits 3: 139 units,
16 truncated contexts and one unavailable composition (66,781 bytes against
48,000). It makes **zero provider requests**. Manifest context fitting belongs
to the pending Perch-cap/coordinator work; no whole-project qualification is
claimed. Conceptual compression, Delight, memetic identity, Anticipation and
Payoff all remain **unrated**, with no distribution or quality pass available.
Live semantic/style Perch remains coordinator-only.

The empty-datatype minor is repaired conservatively under the standing ruling:
empty declarations report `Unsupported check empty-datatype`, never Invalid.
Its separate immutable seed oracle reproduces two fresh freezes before this
repair. One additional book and a seventh checked helper law exercise this
classification without changing the original 26-fixture oracle or its six laws.
Accepting empty declarations remains part of modules reconciliation. No unmerged
branch is imported. Main integration, shared receipt refresh and BS2–BS8 remain coordinator
or follow-on increment actions. The refuted host-timeout finding remains retained
historical evidence; no host guard or program budget was changed here.

The final full-suite results below supersede the intermediate repair checkpoints.

## Compatibility follow-up

The first full run exposes a direct frozen caller in
`tests/compiler-checker/bounds.bend`: the catalog's three-argument `parameters`
entry must remain available. Scope tracking now lives in `parameters_in`, with
the original entry delegating from an empty scope. The bounds entry checks under
the seed again, and all six new helper laws still check with zero holes.

Executing that entry then exposes its original shadowing witness: parameter
names `N0`, `N1`, ... share the type name `N0`, so later annotations correctly
stop with `Invalid check type-shadow` before the 256/257 boundary. This is the
same confirmed finding, not a resource-limit failure. A separate seed-citing
amendment renames these binders without changing a boundary assertion. The failed
run and the intermediate eight-line bounds output are retained as evidence.

## Final acceptance

`npm run -s gates -- --jobs=1` passes **15/15**, exit 0, in **717.820073 measured wall seconds**. PATH selects the installed Xcode clang 21 directly and SDKROOT selects its installed SDK. No compiler flag, seed byte, frozen gate script, expectation or resource budget was changed for host discovery.

Reproduce the passing host selection with:

```sh
export BEND_NO_TELEMETRY=1
export PATH=/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin:$PATH
export SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk
npm run -s gates -- --jobs=1
```

| Gate | Status / exit | Exact counts |
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
| census | PASS / 0 | `{"classes":40,"declarations":432,"files":30}` |
| lint:verify | PASS / 0 | `{"law_rules":8,"tests":127}` |
| base-enum | PASS / 0 | `{"agreed_books":2,"byte_identical_modules":2,"declarations":7,"deferred_books":1,"evaluator_observations":62,"execution_lanes":2,"fixtures":7,"laws":8,"mutants":5,"output_preservation_checks":10,"proof_holes":0,"reference_calls":31,"rejected_books":4,"review_agreed_books":13,"review_amendment_seed_witnesses":4,"review_byte_identical_modules":12,"review_evaluator_observations":26,"review_fixtures":27,"review_lane_observations":162,"review_laws":7,"review_mutants":3,"review_output_preservation_checks":30,"review_proof_holes":0,"review_rejected_books":10,"review_unsupported_books":4,"review_wasm_observations":24,"seed_calls":32,"seed_lane_observations":64,"wasm_observations":62}` |

The current review family adds **27 fixtures**, **162 phase observations**, **13 accepted / 10 rejected / 4 Unsupported books**, **26 evaluator observations**, **24 executed Wasm observations**, **12 byte-identical module pairs**, **30 output-preservation checks**, **7 zero-hole laws**, **3 killed mutants**, and **4 replayed amendment seed witnesses**.

[The portable receipt](receipts/gates.json) records all 15 normalized gate results, **91 matching tested input identities**, the pinned seed, host compiler identity and all three failed earlier runs. [The base-enum receipt](receipts/base-enum.json) retains every fixture, proof and semantic mutant observation. Both are evidence from one passing run, not a union of earlier passing gates.

The earlier runs remain separate: 14/15 at the first repair checkpoint (direct-helper API mismatch), 14/15 at the final code with default scheduling (30-second frontend native-build guard), and the ordinary-PATH serial run (seed clang discovery). They do not invalidate a program or establish acceptance. The parameter witness amendment is the only frozen witness change and has its own seed-citing commit; every existing assertion and both original Base oracles are unchanged.

Plan headline numbers remain **72 compiler-runtime / 110 static Base declarations**; **7 BS1 + 28 unmerged literals identities + 37 remaining runtime declarations**. This increment completes the plan and BS1 plus the three confirmed review repairs. No imported Base, VM image, self-hosting fixpoint or live style pass is claimed.
