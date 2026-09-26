# Vec 1 contract

An abstract vector is `(sequence, capacity, logical_limit)` with reusable Data
values, `0 <= length(sequence) <= logical_limit <= 2^24`, and power-of-two
physical capacity at least max(1,length). Capacity can exceed a non-power-of-two
logical limit because allocation rounds upward. Vec itself is an affine Type.
The public API is exactly the Vec functions in INTERFACE.md, including maximum.
Bend does not enforce module privacy: Buffer and unprefixed helpers are internal;
clients that construct malformed Buffers are outside this contract.

All operations are pure and consume/return the vector, including reads. Values
may be retained/copied because T is Data. Array/IO/closure elements are rejected.
There is no implicit copy-on-write vector or shared mutable alias. Dropping an
owned vector is permitted by Bend's affine discipline. Numeric indices and
lengths are U32; there are no negative indices or implicit signed conversions.

| Operation | Observable contract |
| --- | --- |
| maximum | 16,777,216, the allocation policy ceiling |
| new | empty sequence, capacity 1, limit maximum |
| bounded(limit) | empty, capacity 1, effective limit min(limit,maximum); zero valid |
| length/capacity/limit | return that metadata without changing state |
| get(i) | Done(sequence[i]) iff i < length, else Bounds; state unchanged |
| set(i,x) | replace exactly position i; Done(Unit), else Bounds and unchanged state |
| swap(i,x) | same replacement, returning previous value; same bounds rule |
| push(x) | append x in order; Done(Unit), or Limit if length == limit |
| pop | remove and return final value; Empty if empty; capacity retained |
| reserve(k) | Limit iff k > logical limit, even if physical capacity suffices; otherwise preserve sequence and allocate least power of two >= k if current capacity is smaller |
| slice(s,e) | Done(copied sequence[s:e]) iff s <= e <= length; InvalidRange otherwise; source unchanged |
| to_list | copy every live element in order; source unchanged |

All errors preserve the entire abstract state, including length, capacity and
limit. Set/swap failures discard the supplied Data value. Slice is a copied
half-open range rather than a retained view; it has no lifetime or stale-index
hazard. No erase-at, insertion, shrink, iterator, vector clone, or affine-element
storage is promised. Swap means replacement and old-value return, not exchanging
two vector indices.

The physical abstraction relation is: slot i is Some(sequence[i]) for i < length,
and every remaining slot is None; stored cap is Array.size and equals 2^depth;
0 <= depth <= 24. The independent model in model.bend uses linked lists, structural
index recursion, append and tail removal. It imports neither Vec nor Array.
trace.bend compares full ordered values, operation result, logical length, limit,
and capacity behavior after every operation through the public API. Filtering
None during to_list is not, by itself, proof of this abstraction relation.

The maximum is a deterministic allocation policy, not an OOM recovery promise.
Actual host allocation/heap failure remains a runtime failure. No package arithmetic
wraps for legal states: push checks length < limit before +1; pop checks nonempty
before -1; ranges check order before subtraction; growth takes at most 24 doublings.
reserve rejects U32.max before planning/allocation. Inputs forged through private
constructors are not protected by these preconditions.

With pinned native array lowering and constant-size element retain/drop costs:
metadata/get/set/swap/pop are O(1); reserve is O(new capacity) when growing and O(1)
otherwise; push is amortized O(1) across a sequence; slices/to_list are O(k) time
and output space. Explicit large reserves are charged to reserve, not to later
push calls. Doubling copies at most a geometric sum < 2N slots across N appends
and initializes < 4N slots (for arbitrary N>0). During growth both arrays coexist.
Large element destruction can add element-specific costs.

Pure code was checked by Bend 2.0.29 at revision
574b6d39a235b539eb19a5c532993a0abb3d11ad and executed on native CPU and JavaScript.
No GPU execution or Knot compiler support is claimed. Knot's proposed bootstrap
profile presently excludes arrays; adopting Vec there requires a profile decision.
The package build reference does not make that decision.

Proof boundary: 19 arbitrary-Data-element, fixed-shape laws and six concrete
metadata normalizations, all checked with zero holes. There is no claimed general
induction theorem over every reachable length/operation trace. Runtime conformance,
semantic mutation tests, source cost analysis, and timings are separate evidence.
Trust includes the pinned parser/typechecker/normalizer, Base definitions and
privileged native intrinsic agreement, compiler/lowerer, native runtime/Clang and
Bun JS runtime. The static release dependency walk finds no reachable unsafe,
foreign, or bodiless declarations. Loaded Base nevertheless contains its unsafe
Array.fork/join and foreign APIs; this is not a whole-Base safety theorem.
