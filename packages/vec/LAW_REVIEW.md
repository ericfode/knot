# Vec bounded law review packet

Current working revision: unreleased `vec-growth-1`. Growth planning and the
push continuation use joint matches. Contract, laws, proof bodies, oracle and
assertions are unchanged; current gate evidence is under
`campaigns/vec-growth-1/gates/`. Published identities and release-time receipts
remain historical evidence for `0xd684886d10b431b9dce6c3b2d1ef1980`.

Scope: the entire small stable public Vec API. No private Buffer construction is
supported. Implementation uses Array<Maybe<Data>>, stores len/cap/depth/limit,
checks logical bounds before access, doubles on growth and copies the live prefix.
This packet includes the relevant contract; it omits full function bodies.

API: maximum()->U32; new(T)/bounded(T,limit)->Vec<T>;
length/capacity/limit(T,v)->(v,U32); get/swap/pop->(v,Result<Error,T>);
set/push/reserve->(v,Result<Error,Unit>); slice(T,v,s,e)->(v,Result<Error,List<T>>);
to_list(T,v)->(v,List<T>). T is Data and Vec is affine Type. Swap replaces one
index and returns the old value. Error variants: Bounds, Empty, Limit, InvalidRange.
All errors preserve sequence and metadata. reserve is a total minimum; ranges
are half-open and copied. Effective limit=min(requested,2^24); physical capacity
starts at 1, can round above a non-power-of-two limit, and never shrinks.

The list model has State{items:List<U32>,max:U32}; append walks to the tail,
get/set walk Nat indices, pop removes the final list node. It imports no Vec or
Array. The abstraction relation maps precisely the Some-valued live prefix to
the model list; every spare slot is None, cap=2^depth, len<=limit<=2^24.
The runtime driver compares result, complete ordered contents, independent list
length, limit, capacity power-of-two validity and exact growth rounding after
every public operation. It does not compare the implementation with itself.

## Laws and inhabited domains

LAWS.bend contains the following equations. T is any Data type and a,b,c,d,e,x
are arbitrary values. All lengths/indices in these theorems are fixed shapes.
Witnesses instantiate T=U32 and distinct values 11,23,37,49,61 in witnesses.bend.
No precondition is an Empty type, unsafe assumption, or impossible state.

- empty_contents: new -> []. singleton_get: get([x],0) -> Done(x).
- growth_order: five successive pushes -> [a,b,c,d,e], across 1->2->4->8.
- reserve_preserves: reserve([a,b,c],17) -> ([a,b,c],Done(Unit)).
- set_preserves: set([a,b,c],1,x) -> ([a,x,c],Done(Unit)).
- swap_old_and_preserves: swap([a,b,c],1,x) -> ([a,x,c],Done(b)).
- push_pop_growth: pop(push([a,b],x)) -> ([a,b],Done(x)).
- slice_order: slice([a,b,c,d,e],1,4) -> Done([b,c,d]).
- logical_bounds: set([a,b,c],3,x) -> ([a,b,c],Bounds), despite capacity=4.
- max_index: get([a],U32.max) -> Bounds.
- zero_limit: push(bounded(0),x) -> ([],Limit).
- empty_pop: pop(new) -> ([],Empty). empty_slice: slice(new,0,0)->Done([]).
- reversed_slice: slice([x],1,0)->InvalidRange.
- maximum_reserve: reserve([x],U32.max) -> ([x],Limit).
- get_preserves: get([a,b,c],1) -> ([a,b,c],Done(b)).
- set_then_get: get(set([a,b,c],1,x),1) -> Done(x).
- push_success: push([a,b],x) -> ([a,b,x],Done(Unit)).
- pop_length: length(pop([a,b,x]).vector)=2.

Six concrete boundary normalizations establish initial length=0, initial cap=1,
reserve(17) cap=32, bounded(U32.max) effective limit=16,777,216, reserve at exact limit 3 succeeds,
and arithmetic growth planning reaches (2^24, depth 24) without allocating. Their domains
are the displayed concrete constructors. All 25 are closed by PROOF.bend with
zero holes; there are no new axioms or unsafe proofs. The 19 parametric laws are
universal in element type/value, not universal in length, capacity or traces.
A general all-states refinement theorem is an explicit omission.

## Public coverage matrix

| Public operation | Laws above | Independent runtime assertion / partitions |
| --- | --- | --- |
| maximum | effective_limit | trace.state_eq ceiling and bounded clamp |
| new / bounded | empty_contents, initial_metadata, initial_capacity, effective_limit, zero_limit | empty; limits 0,3,17; default construction |
| length | initial_metadata, pop_length | trace.state_eq after every call; 0..5 and scaling sizes |
| capacity | initial_capacity, rounded_capacity | trace.capacity_op checks exact rounding/no-shrink; growth 1..32 |
| limit | effective_limit, zero_limit | trace.state_eq checks persistent limit after every call |
| get | singleton_get, max_index, get_preserves, set_then_get | logical_bounds and updates; first,last,len,capacity,U32.max |
| set | set_preserves, logical_bounds, set_then_get | updates and logical_bounds; unrelated values, failure preservation |
| swap | swap_old_and_preserves | updates/logical_bounds; previous value and state preservation |
| push | growth_order, push_success, zero_limit | growth_values/limits/push_pop; exact limit and post-pop reuse |
| pop | push_pop_growth, empty_pop, pop_length | push_pop; singleton, empty, reuse, retained capacity |
| reserve | reserve_preserves, maximum_reserve, rounded_capacity | growth_values/limits; no-op, boundary, non-power-of-two, U32.max |
| slice | slice_order, empty_slice, reversed_slice | ranges; start/end, [len,len), out-of-bounds, overflow-sized indices |
| to_list | empty_contents, growth_order and all preserved-content laws | complete order after every operation |

Runtime results: all 4,096 length-three words over a 16-operation alphabet at
limits 0,3,17 (12,288 traces), plus seven longer targeted families, pass on CPU
and JS. Every trace compares all state observations after each transition.
No claim of exhaustive U32/value coverage. Negative tests require the exact duplicate-use diagnostic for Vec ownership
and expected Data / observed Type for a parenthesized closure element type. A
release audit disqualified the earlier unparenthesized fixture because it failed
parsing first; receipts/ownership_repair.json preserves that rejected evidence
and the corrected gate result. No uploaded source changed. Data generic proofs also cover non-U32
values; native and JS runtime checks also exercise Data records containing Strings and
a non-ASCII label through growth, reserve and replacement.

## Pop/growth state-observation review

Adversarial candidate: leave len unchanged when pop clears its final slot.
Because to_list skips None, the original contents-only theorem passed. The
unchanged runtime length oracle rejected it. Added pop_length now also rejects
it (3 != 2). This records an actual law refinement, not a passing mutant.
An initial mutant candidate reused an affine numeric binder and failed typing;
it was corrected to a reusable U32 binder and only then counted. No type failure
counts as a semantic kill. The rule vec-logical-state-observation preserves this
lesson with clean, broken and held-out packets.

Nine type-correct semantic mutants are killed by unchanged named assertions:
discard push value, drop growth contents, overwrite growth prefix, wrapped get,
stale pop length, reversed slice order, ignore logical limit, reject exact limit,
and failed swap corrupting position zero. All nine also fail checked laws, including exact-limit reserve. Full receipts
record the intended observation separately from the first rejecting law: e.g.
discard_push first rejects singleton_get, stale pop rejects pop_length, and
reverse_collection first rejects growth_order. Implementation checks precede
property failure. No tested non-equivalent
mutant survives. Unattempted mutants remain outside the evidence.

Hostile reread: constants/input discard fail growth_order; reversed copies fail
slice_order/growth checks; writing unrelated slots fails set_preserves or the
oracle; capacity-based wrapping fails logical_bounds/max_index; stale metadata
fails pop_length. Forged Buffer states remain excluded explicitly, not assumed
valid. Host OOM is a runtime failure; the typed Limit error enforces policy only.

## Evidence categories and trust

Native CPU workloads N=4096,16384,65536,262144 verify every value against i*17+3.
At power-of-two N, observed capacity transitions imply log2(N) growth events,
N-1 copied slots and 2N-1 initialized slots. These are source-derived slot counts
from observed transitions, not allocator instrumentation or a formal cost proof.
Three timing samples per workload are separate from correctness and include
process startup. The emitted C contains direct blk_at/blk_read/blk_write indexing
and blk_new allocation; no structural array traversal is used by Vec.

Pinned compiler: Bend 2.0.29, revision 574b6d39a235b539eb19a5c532993a0abb3d11ad.
Trust: checker/normalizer, Base, intrinsic agreement, compiler, native runtime,
Clang and Bun. No GPU execution claimed. Static dependency walk of release code,
types and proofs finds no reachable unsafe, foreign or bodiless definitions.
Loaded Base has unsafe/foreign APIs outside that reachable closure.

Perch rules are advisory. The original release had only deterministic rule
selection/packet-fit evidence because no provider key was configured. That
historical receipt is preserved. The subsequent live audit and control outcomes
are recorded in PERCH_REPORT.md; model scores do not replace the proofs or tests.

## Reviewed source identities

- main.bend (unreleased): `3e4d79031d5a1aede6b1d08c9859b4549d99f6628b3538ef399600280873e70a`
- model.bend: `4fb68671f7cb104d229d153c67e6f87eefebcc79e12db0f038647897bf32b7a9`
- LAWS.bend: `bf5cc273eeebb8a63f498afd5c27744a00d4e5988c881742ebf599a3f20a2edd`
- PROOF.bend: `09a438b139bf4f6f1a638547a8b51a69b1497c9397ba835a809cebc4cae0b871`
- trace.bend: `9378a64a7edfa9b89bc40fe52c598f3bf248292e2c2260ed25e03bfb10075ecd`
- conformance.bend: `eb2d7eebaa79a868cce1549507788cec28f2bf15d5325bd8b4735278bde4cc91`
- witnesses.bend: `e432b1b510973857f635361f12251942a603c60363417813ab5993b9bbdde70a`

Current receipts: campaigns/vec-growth-1/gates/{gates,mutations,scaling}.json.
Historical release receipts: receipts/{gates,mutations,scaling,closure}.json.
