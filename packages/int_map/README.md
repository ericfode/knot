# Persistent U32 map

Published MIT-0 package for compiler environments and usage counts. Operations
use all 32 key bits without String conversion. Maps and previous versions are
immutable. Values must be copyable Data.

```bend
import Base
import 0x99e32f5f97dad3791a32b01d133555c5/main.bend as M

# Closed template callbacks may be reused; ordinary affine closures cannot.
def main() -> U32:
  +left = M.IntMap.set(U32,M.IntMap.empty(U32),4294967295,3)
  right = M.IntMap.set(U32,M.IntMap.empty(U32),4294967295,7)
  counts = M.IntMap.union_with(~U32,~U32.add,left,right)
  M.IntMap.fold(~U32,~U32,~(sum => key => value => U32.add(sum,value)),counts,0)
```

This consumer returns 10. To join usage quantities by maximum, use
`~(a => b => U32.max(a,b))`; that returns 7 on the same overlapping key.
Zero is a valid stored value. `get` returns `Maybe<&2,V>`, preserving absence.

Read INTERFACE.md for the API, SPEC.md for semantics and complexity, and
LAW_REVIEW.md for the operation coverage matrix and exact proof boundaries.
RELEASE.json records publication and fresh remote verification. The remote
`release.bend` imports the laws/proofs and runs all included conformance checks;
`PROOF.bend` is also independently importable by the same content hash.

Reproduce from the repository root:

```sh
python3 packages/int_map/scripts/check.py
node packages/int_map/scripts/perch-review.mjs
scripts/bend-reference packages/int_map/example.bend
```

Local deterministic checks pass on native CPU and generated JavaScript. Eleven
type-correct semantic mutants fail their intended observations. GPU is untested.
The subsequent live Perch audit completed 94 rule evaluations and detected
both broken controls. Manual review fixed benchmark CLI input bounds outside
the published closure; see PERCH_REPORT.md for findings, misses and receipts.
Universal proofs, concrete normalization, runtime tests, structural counts, and
timings remain separate claims. Runtime list-model agreement is not universal
refinement.
