# IntMap bounded declaration review — 2026-09-26

**No package code needed changing.** Completed 223 live rule evaluations over
23 parsed Bend declarations and the current law packet, with 24/24 provider
responses from `jev-1.13.0` (requested `jev-latest`). No reported package findings:
confirmed 0, false-positive 0, unresolved 0. No new rule or style change, no stronger
repair-model invocation, no publication, and no campaign resumption.

## Exact scope and evidence

Every request used `npm run lint -- <target> --rules <names> --json`.
[The index](receipts/perch-declarations-2026-09-26/index.json) preserves exact
commands/targets, source hashes, original `.perch/usage/` paths and durable
package copies. Each ID below links the full wrapper receipt; corresponding
`-result.json` files preserve the complete CLI result with per-declaration
scores and working-copy context, including single-declaration requests.

| Target | Declarations | Checks | Receipt |
| --- | ---: | ---: | --- |
| `main.bend` | 19 | 190 | [23c2aace-5d00-4e33-ad03-6781b0b425e4](receipts/perch-declarations-2026-09-26/23c2aace-5d00-4e33-ad03-6781b0b425e4.json) |
| `model.bend::get` | 1 | 10 | [934a6f19-d71f-4a1e-bc39-d5ef04ce6240](receipts/perch-declarations-2026-09-26/934a6f19-d71f-4a1e-bc39-d5ef04ce6240.json) |
| `model.bend::union_with` | 1 | 10 | [520f680b-f3a7-4816-990b-4bca46e18004](receipts/perch-declarations-2026-09-26/520f680b-f3a7-4816-990b-4bca46e18004.json) |
| `PROOF.bend::L.path_preserve` | 1 | 2 | [e9108339-0e31-4231-bac1-364bdd947610](receipts/perch-declarations-2026-09-26/e9108339-0e31-4231-bac1-364bdd947610.json) |
| `PROOF.bend::L.path_remove_preserve` | 1 | 2 | [b1edb7d3-64ce-447a-baae-f89aa00d93ab](receipts/perch-declarations-2026-09-26/b1edb7d3-64ce-447a-baae-f89aa00d93ab.json) |
| `LAW_REVIEW.md` | file packet | 9 | [5b85cddc-bb81-4067-95e9-5bcff4c226f9](receipts/perch-declarations-2026-09-26/5b85cddc-bb81-4067-95e9-5bcff4c226f9.json) |

All 19 implementation declarations received the six Bend rules and the four
performance rules (190 checks). This covers all eight public operations and
every local implementation helper. Both model operations received the same ten
rules (20 checks); their helper context includes equality-based lookup,
filtering removal, insertion and merge. The two proof targets received
`bend-fuel-completeness` and `bend-borrow-lifetime` (4 checks). The packet received
all eight `law-*` rules plus `package-int-map-union-observation` (9 checks).
Floors and rules were unchanged.

Exact implementation declarations:
`bits`, `low`, `high`, `value`, `get_path`, `set_path`, `branch`, `remove_path`,
`IntMap.empty`, `IntMap.get`, `IntMap.set`, `IntMap.remove`, `present`,
`IntMap.contains`, `IntMap.size`, `IntMap.fold`, `combine_value`, `union_step`,
`IntMap.union_with`.

The parser identified every target with profile
`language-pack-1.20-v3+knot-bend-0cd9e831fc413760`, Bend parser
`bend-2.0.29-574b6d3-observer-v2`. All 23 actual source-review contexts report
`truncated:false`. Union includes its 11 transitive helpers. Both proof targets
include the corresponding law and current main.bend helpers. Standard Base
names remain explicitly unresolved; parsing/context assembly is not type or
proof checking. Metrics, dynamic-call completeness and foreign implementations
remain outside this adapter's claims.

Excluded from paid rechecking: unchanged conformance/fixture/example files,
benchmark drivers and scaling harness, historical receipts, generated artifacts,
negative controls and unrelated packages. Fixture semantics were re-executed as
deterministic conformance below. This pass does not claim a new calibration run
or a review of every unchanged test declaration. The 16-helper cap was reached
by scaling during exploratory local context inspection, so it was not presented
as a complete new model review; it was outside the public-map focus.

## Judgment and validation

No source, performance, proof-target or packet score reached its reporting
floor. Scores remain advisory. For example, arithmetic broken probabilities
on constructor-only `IntMap.empty` and `present` were 0.63 and 0.62 below 0.80;
there is no arithmetic path in either target to repair. They are weak signals,
not emitted findings or grounds to rewrite correct code.

The whole proof entry was checked again with zero holes. Current conformance
was rebuilt and passed on native CPU and generated JavaScript: all nine existing
families, including full-width keys, persistent snapshots, fold contents/seed,
noncommutative combining and independent model transitions/unions.
[Validation receipt](receipts/perch-declarations-2026-09-26/validation.json)
contains commands and outputs. All nine published file hashes still match
`0x99e32f5f97dad3791a32b01d133555c5`. GPU remains unvalidated; no performance
benchmark or mutation campaign was repeated because no code changed.

This pass adds only review evidence and this report/status pointer. The benchmark
CLI bound fix described in PERCH_REPORT.md happened during the **earlier** file
review and is already in checkpoint e17f977. It is not a change from this pass.
Historical evidence is preserved. Full universal list-model refinement remains
outside the existing proof claims.

## Shared-tooling proposal

Confirmed receipt-attribution gap, outside this package's ownership:
At receipt collection, `scripts/perch-workflow.mjs` only stored `result.units`. Explicit `file::name`
results instead put `name`, `asked` and `context` at the top level, so their
wrapper receipts have `units:[]` and only the source file as target. Compare
`934a6f19-d71f-4a1e-bc39-d5ef04ce6240.json` with its `-result.json`: the latter
retains the selected `get` declaration and its untruncated working-copy context.
No provider result was missing; the metadata was dropped when recording it.
The package copies preserve both forms, so this review remains attributable.

Proposed coordinator change: normalize a top-level parsed declaration result
into one receipt unit when `result.units` is absent, preserving its declaration
name, scores and context. Add an offline receipt regression for a `::name`
check. A concurrent chat has now placed this normalization in the shared
working copy; this chat did not apply or validate that shared patch. Shared
files and the shared review log were not edited here.

## Two existing structures worth showing

These excerpts are unchanged published code. No alternate implementation was
created, so no style comparison or invented rank was requested.

`main.bend:44-51` makes path copying and sibling preservation visible in the
same mirrored form. Each branch recurses into exactly one child and carries the
other child through unchanged. The readable symmetry exposes persistence.

```bend
def set_path(-V: Data, path: List<&2,Bool>, +m: IntMap<V>, key: U32, v: V) -> IntMap<V>:
  match path:
    case Nil{}:
      Entry{key,v}
    case Con{False{},tail}:
      Branch{set_path(V,tail,low(V,m),key,v),high(V,m)}
    case Con{True{},tail}:
      Branch{low(V,m),set_path(V,tail,high(V,m),key,v)}
```

`main.bend:105-108` reduces collision behavior to the two constructors of Maybe.
Absence passes the right value through; presence combines left then right.
That argument order is explicit, with no commutativity assumption hiding it.

```bend
def combine_value(~V: Data, ~combine: V -> V -> V, old: Maybe<&2,V>, right: V) -> V:
  match old:
    case None{}: right
    case Some{left}: combine(left,right)
```
