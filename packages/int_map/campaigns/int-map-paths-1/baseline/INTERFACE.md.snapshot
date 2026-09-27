# IntMap interface

Status: complete, published and verified remotely on native CPU and JavaScript.

```bend
import 0x99e32f5f97dad3791a32b01d133555c5/main.bend as M
```
Base-only dependency, pinned Bend 2.0.29. Pure persistent U32-keyed trie,
independent of String conversion. Values must be `Data` (copyable).

Public API in `main.bend`, imported as `M`:
- `M.IntMap<V>`
- `M.IntMap.empty(V) -> M.IntMap<V>`
- `M.IntMap.get(V, map, key) -> Maybe<&2,V>`
- `M.IntMap.set(V, map, key, value) -> M.IntMap<V>`
- `M.IntMap.remove(V, map, key) -> M.IntMap<V>`
- `M.IntMap.contains(V, map, key) -> Bool`
- `M.IntMap.size(V, map) -> Nat`
- `M.IntMap.fold(~V,~A,~step,map,initial) -> A`, step `(A,U32,V)->A`
- `M.IntMap.union_with(~V,~combine,left,right) -> M.IntMap<V>`, combine `(V,V)->V`

Callbacks are Bend templates, not reusable affine closures. `union_with`
combines overlapping entries as `combine(left_value,right_value)` exactly once
per overlapping key in the pure result expression (not a physical call-count
guarantee under compiler optimization). Left-only/right-only entries
are retained without calling combine. Fold visits each key exactly once in
lexicographic least-significant-bit-first path order (not numeric order).
Addition of U32 counts wraps; maximum/join is a separate operation.

All versions remain observable when callers retain a `+` copy. Full U32 domain,
including 0 and 4294967295. No sentinel value. Size uses Nat, not wrapping U32.
Lookup/update walk at most 32 key bits. Fold and size traverse the trie; union
folds the right input into the left and is O(32 * right entry count), excluding
value/combiner and reference-count reclamation costs. Full contract in SPEC.md.
