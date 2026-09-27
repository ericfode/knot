# Persistent U32 IntMap

Original MIT-0 Bend implementation. Build reference: Bend 2.0.29 at
574b6d39a235b539eb19a5c532993a0abb3d11ad. This reference does not select Knot's
future compatibility profile.

## Abstract contract

A map is a finite partial function from all 2^32 U32 keys to values of a
copyable `Data` type V. Absence is `None{}`; every V value, including zero,
is stored as `Some{v}`. There is no reserved key or sentinel value.

The supported representation domain is the closure of `IntMap.empty`, `set`,
`remove`, and `union_with`. Bend exposes module constructors; manually forged
Tip/Entry/Branch trees and internal path helpers are outside the public contract.
A reachable map has entries only at depth 32, each entry key matches its bit
path, and every Branch has a nonempty descendant. No identifier lifetime,
capacity, index wrapping, or invalid-key error applies: every U32 is a key.
Host allocation failure is not encoded as a successful map result.

- `empty(V)` represents the nowhere-defined function.
- `get(V,m,k)` returns `Some(m[k])` exactly when k is in the domain.
- `set(V,m,k,v)` maps k to v, preserves every other lookup, and increases size
  iff k was absent. Repeated set overwrites; it does not create another entry.
- `remove(V,m,k)` makes k absent and preserves every other lookup. Removing an
  absent key is extensionally the identity, including on the empty map.
- `contains(V,m,k)` is true iff get returns Some; it does not examine the value.
- `size(V,m)` is the exact number of bindings as Nat, not modulo 2^32. The
  maximum representable map size is 2^32, within the pinned runtime Nat bound.
- `fold(~V,~A,~step,m,initial)` applies step exactly once to each binding,
  threading its returned accumulator. Order is lexicographic on 32 key bits
  from least significant to most significant, false before true. For keys
  0,2147483648,2,1 that is the visit order. It is not numeric sorting. Empty
  returns initial. `step : A -> U32 -> V -> A` is a template; A may be affine.
- `union_with(~V,~combine,left,right)` has domain equal to the union of the
  input domains. At an overlap its value is `combine(left[k],right[k])`.
  One-sided values are retained verbatim. Combiner applications are once per
  overlap in right-map fold order. This specifies the pure result expression;
  it does not promise physical evaluation counts under compiler optimization.
  `combine : V -> V -> V` is a closed template argument, never an affine closure
  reused dynamically. No commutativity, associativity, or identity is assumed.

All operations are pure. A retained `+` copy observes its original contents
across later updates and unions; there are no mutable buffers or unsafe aliases.
Values share Bend's ordinary immutable Data semantics. Addition of usage counts
uses U32 modular arithmetic; maximum is a distinct branch-join operation.
The same fixture yields overlap 10 with add and 7 with max. Neither operation
is presented as equivalent to the other. Arbitrary-size count values can be Nat.

## Representation and independent model

`main.bend` converts the key to a 32-element low-bit-first Bool path using
machine U32 bit operations. It path-copies a binary trie. Removal prunes only
branches whose two children are empty; it never promotes a leaf across levels.
`model.bend` is an independent unsorted association list with equality-based
lookup, filtering removal, front insertion, and pointwise collision combining.
It imports no implementation code and performs no bit extraction. Its lists
are unique-key lists generated from empty by model operations.

Abstraction relation: for every U32 k, trie get equals list-model get; size is
list length; the fold visits precisely that set of bindings once in the stated
bit order. Tests check both directions of entry membership and exact cardinality,
plus all 64 query keys after each transition. This is runtime refinement evidence,
not a proved universal theorem that the whole API refines the list model.

## Complexity and allocation

Let W=32, n=left/current entry count, and m=right entry count. Exclude callback
work, payload copying, reference-count reclamation, and allocation failure.
Native C and JS lower U32 arithmetic to machine operations; source proof
normalization uses a different cost model.

| Operation | Structural work | Source allocation |
| --- | --- | --- |
| empty | O(1) | empty constructor |
| get/contains | O(W), even for empty paths | W path cons cells; no new trie nodes |
| set | O(W) | W path cons cells; W Branch + 1 Entry constructors |
| remove | O(W) | W path cons cells; at most W rebuilt Branch constructors |
| size | O(W*n+1), bounded by retained nodes | arithmetic/intermediate values; no new trie |
| fold | O(W*n+1) plus n callbacks | callback accumulator cost; no new trie |
| union_with | O(W*m+1) plus overlap callbacks | at most 33*m new trie constructors, plus two 32-cell paths per right entry |

A reachable nonempty trie contains at most 33*n nonempty nodes. Retaining
versions retains shared old subtrees, with at most 33 additional trie nodes per
set before reclamation. Retaining no old versions still does not make reference
reclamation free: consuming the last map copy may release O(W*n) nodes, including
on a lookup. Payload release may cost more. These are bounded key-depth operations,
not unconditional constant-time wall-clock operations. Temporary path construction
is an explicit allocation tradeoff; a future direct-word trie could remove it.

Performance fixtures verify each lookup, exact sum/size, maximum depth 32, and
zero retained nodes after full erasure for n=64,256,1024,4096, using dense and
16-common-low-bit layouts. The independent quadratic list oracle runs separately
from timings. Recorded constructor counts are source counts, not heap allocator
telemetry. CPU and generated JavaScript are validated; GPU is not validated.

## Proof and trust boundary

`LAWS.bend` states universal get/set/remove/contains/overwrite properties and
unrelated-path preservation, with structural induction in `PROOF.bend`.
Preservation requires a constructive `separated(bits(key),bits(other))` witness.
The witness is Unit at a differing bit, Empty at equal/prefix paths. Concrete
0 versus 2^31 witnesses show the boundary domain is inhabited. An all-distinct-U32
bit-injectivity theorem is not supplied; runtime tests cover every single-bit
and complement position. The universal statements themselves have no unsafe
assumption or hole.

Five additional laws are labeled concrete normalization of inhabited boundary,
fold, union, invocation-tree, and independent-model examples. They are not
universal fold/size/union refinement proofs. Runtime state-machine and scaling
checks extend coverage; finite observations do not prove completeness.

Trust dependencies: the pinned Bend parser, checker, equality conversion,
termination and quantity checking; Base Bool/U32/Nat/List/Maybe and proved
Equal.cong/sym/trans; native/JS primitive lowering, generated-code compiler and
runtime memory management. Base as loaded includes foreign/opaque declarations
and unsafe Array.fork/Array.join, but those are not reachable from this map or
its proofs. Test executables additionally use Base IO.print/die/args and numeric
formatting. No original package definition uses @unsafe, a foreign import,
an axiom, a hole, mutable Array, String key conversion, or GPU offload.
