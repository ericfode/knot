# IntMap law review packet — unreleased int-map-paths-1

Bounded family: the eight public operations of the persistent U32 map in
`main.bend`. Reviewed 2026-09-26 against pinned Bend 2.0.29 revision
574b6d39a235b539eb19a5c532993a0abb3d11ad. Source hash inventory follows below.
This packet supplies observations and evidence, not a completeness theorem.

## Domain and public inventory

`IntMap<V>` is a Data trie with Tip, Entry(key,value), and Branch(lo,hi).
Supported inputs are generated from empty/set/remove/union; manually constructed
malformed trees and internal helper defs are not public API. Keys cover all U32
values, including 0 and 4294967295. Values are arbitrary copyable Data, including
stored zero. All operations are total over this reachable domain, subject to
host resources. No invalid U32, fuel exhaustion, or capacity condition is hidden.

Signatures (V erased; fold/union parameters prefixed ~ are templates):

```
empty(V) -> IntMap<V>
get(V,map,key) -> Maybe<&2,V>
set(V,map,key,value) -> IntMap<V>
remove(V,map,key) -> IntMap<V>
contains(V,map,key) -> Bool
size(V,map) -> Nat
fold(~V,~A,~step,map,initial) -> A
union_with(~V,~combine,left,right) -> IntMap<V>
step : A -> U32 -> V -> A; combine : V -> V -> V
```

Actual core behavior: build exactly 32 low-bit-first Bool path cells. Set copies
one Branch per bit and ends in Entry(key,value); get follows exactly that path.
Remove ends in Tip and prunes only Branch(Tip,Tip). Fold recursively visits lo,
then hi, applying step(acc,key,value) only at Entry. Union folds right entries
into left; None retains right, Some(left) yields combine(left,right), then set.
Size counts Entry nodes in Nat. All versions are immutable; retained copies
remain valid. Internal path/helper code and full inductive proof text are omitted
from this bounded packet, with exact hashes below for reproducibility.

Independent oracle: a unique-key association list. Lookup compares U32 equality;
remove filters matching pairs; set prepends after remove; union traverses its
right list, combining only where lookup on its accumulated left returns Some.
The oracle imports Base only and contains no trie or bit arithmetic. The
abstraction relation is equality of lookup at every U32, exact list length,
and exact once-per-binding fold contents. This is checked at runtime over
specified witnesses; full universal refinement is not claimed.

## Coverage matrix and inhabited observations

| Public operation/location in main.bend | Law or independent assertion | Domains and exact observations |
| --- | --- | --- |
| IntMap.empty | LAWS.empty_get; fixtures.boundary/fold_seed_case | For every key: None. Empty size=0; empty fold retains seed. |
| IntMap.get | LAWS.set_get/remove_get; fixtures.bit_cases/query_domain | Stored 0 is Some(0); absent key is None. Every single-bit and complement key, max U32, every query 0..63 after each composed transition. |
| IntMap.set | LAWS.set_get/overwrite/set_preserves; boundary/sequence | Empty then 0->0, max->99, overwrite 0->17: max remains99, size stays2; retained previous version still stores0. |
| IntMap.remove | LAWS.remove_get/remove_preserves; boundary/bit_cases/sequence | Removing max preserves 0->17; removing0 then empties. Absent high-bit removal preserves both bindings. Full erasure has zero retained nodes. |
| IntMap.contains | LAWS.set_contains; boundary/query_domain | Stored0 is present; missing1 is false; agrees with model presence for all64 queries after updates. |
| IntMap.size | concrete boundary_fixture; fixtures.agree/scaling | Independent list length; exact unique cardinality after overwrite, absent/present removal, and union. Counts 0,1,2,3 through4096; Nat avoids U32 wrap. |
| IntMap.fold | concrete fold_fixture/fold_seed_fixture; entries/agree/order_case | Visit keys 0,2^31,2,1 in that exact low-bit-first order, retaining paired values. Prepending fold yields [1->11,2->22,0->7,99->123] from seed[99->123]. |
| IntMap.union_with | concrete union_fixture/invocation_fixture/model_union_fixture; unions/union_stress | Direction, one-sided values, empty identities, prior versions, separate add/max semantics, exact Join tree; independent 96-entry unions. |

Composition runtime witnesses: 192 deterministic set/remove transitions starting
empty; each step compares old, updated, and removed versions to independent
list states, both directions of entry membership, exact size and fold cardinality,
and all64 query keys. Two 96-entry inputs exercise three different union
combiners against the list model. Scaling verifies every lookup at 64,256,1024,
4096 entries in dense and 16-shared-low-bit layouts on native CPU and JS.

## Explicit collision observations

Left={0->2,max->3}, right={1->5,max->7}, f(a,b)=100*a+b.
Expected union={0->2,1->5,max->307}. Addition instead produces max->10;
maximum instead produces max->7. Both retain0->2 and1->5. Empty union
identities and the two original maps are observed independently.

For Trace values, combine(a,b)=Join(a,b): key9 contains Atom(2) left and Atom(7)
right. Expected result is exactly Some(Join(Atom(2),Atom(7))), with no nested Join.
Left-only key10 remains Atom(11), right-only key12 remains Atom(13). This rejects
reversed operands, repeated combining, and combining on singletons. The language
is pure: this specifies observable expression structure, not timing or physical
callback evaluations under an optimizing compiler.

## Proof classification and witness domains

Universal, zero-hole inductive proofs: empty_get, set_get, remove_get,
set_contains, overwrite, set_preserves, remove_preserves. The preservation laws
quantify over arbitrary values/maps and over two key paths with a constructive
separated witness. separated is Unit at the first differing bit and Empty for
equal/prefix paths. `distinct_witness` inhabits bits(0) versus bits(2^31) without
unsafe assumptions. Path variants provide induction, and branch_low/high and
observe_low/high are auxiliary projection lemmas, not headline behavior claims.

Universal no-precondition laws have ordinary witnesses V=U32, empty and maps
{0->0,max->99}, keys0/max, values0/17. The overwrite witness uses two different
values. Preservation's premise is constructible for any exhibited differing
bit; the checked high-bit witness traverses31 equal bits first. An equivalence
between numeric key inequality and separated is NOT universally proven.

Concrete normalization only: boundary_fixture, fold_fixture, union_fixture,
invocation_fixture, model_union_fixture, fold_seed_fixture. Their propositions
are the named fixture's exact observable Bool result equaling True. Each fixture
uses explicit maps/expected values above; it does not compare an implementation
to itself. Fold/size/union are not advertised as fully universally refined.

Native/JS execution, scaling timings, source-node counts, and Perch judgments
are separate from these proofs. Trust includes the pinned checker/conversion/
termination, Base's pure numeric/list/equality definitions, native primitive
lowering, C compiler, JS runtime, and memory management. Base is loaded with
foreign declarations and unsafe Array.fork/join, but neither unsafe Array def
is reachable from the implementation or proofs. Original code has no unsafe,
foreign declaration, hole, or axiom; test IO uses Base effects. GPU unvalidated.

## Adversarial deterministic review

Candidates: discard set values; erase a sibling; ignore bit31; leave removal
stale; report false membership; count every entry as zero; drop fold entries;
reverse fold; reverse collision operands; combine singletons; combine twice.
All are implemented as isolated source mutations with the unchanged independent
assertions. A mutant must first pass the pinned checker and executable build.
The final receipt records each typecheck, failing property, exit code and hash.
A syntax/type/build failure is rejected by the harness, never counted as a kill.
No equivalent mutant is counted; there are no surviving listed candidates.

The review also checked an initially missing fold-seed observation. It was
added as an exact retained-seed fixture and concrete law. The narrow Perch rule
`package-int-map-union-observation` captures the repeated direction/singleton
hazard; clean, broken additive-only, and held-out arithmetic controls accompany
it. All findings remain advisory. The original release had no provider
credentials. A subsequent live audit using jev-1.13.0 recorded broken probabilities
0.12 for clean, 0.93 for broken, 0.08 for held-out clean, and 0.89 for a fresh
held-out equal-values collision case. At the unchanged 0.80 floor, both broken
controls were detected and both clean controls passed. Four controls do not
establish production accuracy. PERCH_REPORT.md and the preserved provider
receipts record current file coverage, adjudication, and deterministic evidence.

Remaining limits: no universal full list-model refinement, no bit-injectivity
theorem, no exhaustive 2^32-key enumeration, no allocation-failure API, no GPU
run, no measured heap-allocation telemetry, no performance claim about unbounded
payload release. Large raw manually forged tries are excluded by the public
reachable-map contract. These limitations are stated in SPEC.md.

## Frozen source hashes

```text
95f0f9551cfcd8b5e0b16437405177f4e79f8305c4b9a503bfda68d2a9eea311  LAWS.bend
b1555c91af9ac6f8d84cd242aed3c969de38acd58603151c6c8e0868bb58c6e4  LICENSE
64a59a7d38a2daac8bdbf31006c27f6de88733edbca5176e953386881e7715e6  PROOF.bend
987b5f1fe814cefdc58ad39f95618bfcc58002983f021825c3c024b8c32b1de6  conformance.bend
58bb16bafcdb56f6e488d49e9e5fabc40c4930e688a8d65fca48cc7af1a309f6  example.bend
22374c110d4043af068e92d82c763022abebc10e292a5edd278f09f765a41b5e  fixtures.bend
53f771454f0e13b7128494a45e4ace529740eeb60c8eccb1f7724532359048d2  main.bend
62ede4569dd2d11dd8d23734afbaca21710f58bc73a14cee5fb82efe684109fa  model.bend
71f59b2447b6c0e769ec6d73ce43d7e060d4f31226fb7367875f33d24d98992f  release.bend
```

## Current candidate boundary

This is an owner-local derivative of the release review packet. All source paths
above are relative to packages/int_map. Only main.bend::branch changed: a joint
match collapses Tip/Tip, otherwise Branch(a,b) retains the input children. The
get/set/remove path family, law/proof bodies, independent model, fixtures and
assertions are byte-identical to preregistration.json. Proof checking and native/JS
conformance passed on this candidate; all 11 mutants typechecked and were killed
by their original observations. No mutation locator changed. Scaling and list
model checks passed at 64,256,1024,4096 on both backends. gates.json, mutations.json
and performance.json contain the candidate receipts. Historical release receipts
and the published hash remain unchanged. This revision is not published.
