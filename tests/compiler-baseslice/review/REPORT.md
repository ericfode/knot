# Baseslice review round 1

Starting head: `a7817bf89adbdbc819412af64f91d7265ad6ceb8`.

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
remain accepted. A genuinely free name stays Invalid. No existing fixture,
expectation, assertion or program budget is changed.

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

The targeted fresh run passes in native and Bun: **26 fixtures**, **156 phase
observations**, **13 accepted / 10 rejected / 3 Unsupported books**, **26 evaluator
observations**, **24 executed Wasm observations**, **12 byte-identical module
pairs**, and **28 output-preservation checks**. Three parseable/type-correct
native mutants separately restore global annotation lookup, dotted typed-let
acceptance and false-free-name classification. Each exhibits the frozen defect;
a parser failure, build failure or timeout never counts as its kill.

Six laws check with **zero holes**: four universal helper laws and two ground
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

Offline preflight on the five materially changed Bend files exits 3: 138 units,
16 truncated contexts and one unavailable composition (66,615 bytes against
48,000). It makes **zero provider requests**. Manifest context fitting belongs
to the pending Perch-cap/coordinator work; no whole-project qualification is
claimed. Conceptual compression, Delight, memetic identity, Anticipation and
Payoff all remain **unrated**, with no distribution or quality pass available.
Live semantic/style Perch remains coordinator-only.

The empty-datatype minor belongs to the standing modules reconciliation, which
requires accepting empty declarations and re-freezing that branch's expectations.
This repair does not import an unmerged branch or change that independently owned
boundary. Main integration, shared receipt refresh and BS2–BS8 remain coordinator
or follow-on increment actions. The refuted host-timeout finding remains retained
historical evidence; no host guard or program budget was changed here.

Full-suite results will be recorded after this verified repair checkpoint.

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
