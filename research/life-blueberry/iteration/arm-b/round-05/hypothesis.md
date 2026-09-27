# Round 5 hypothesis

Fresh design after the stream-view branch introduced adapters that conceal the
stencil. Represent each bounded row by one U32: bit x is column x. Zero words
supply the north/south exterior, and shifts naturally supply dead horizontal
edges. Packing and unpacking mirror each other at the public list boundary.

For each lane, north and south each contribute three bits and center contributes
its two horizontal neighbors. Compute each group's parity (low bit) and carry
(high bit). Carry the three low bits once more. Exactly one of the resulting
four high bits identifies neighbor counts 2 or 3; the final low bit distinguishes
3 from 2. The result is that high-bit predicate AND (low bit OR center).

The small reusable circuit primitives are majority-of-three (`carry3`) and
exactly-one-of-four (`one4`). The latter is odd parity with both disjoint pair
carries absent: odd counts are 1 or 3, and every set of three contains one of
those pairs. This exposes one arithmetic representation across all eight
neighbor positions, rather than eight coordinate cases or a chain of tuple
adapters. The hypothesis is a recognizable packing/carrying/unpacking grammar.

Correctness risks: bit direction, width 32 truncation, unwanted wraparound,
confusing logical lane operations with integer sums, and retaining cropped
outside cells between generations. Only the low width bits are unpacked; each
new generation repacks those returned cells. Width and height remain 0-32 under
the unchanged contract. Use no fixture-specific behavior and no timing claim.

Additional allowed reference read: pinned Base's U32 operations, lines
1325-1445, to confirm one-bit logical shift and boolean word primitives.
The original assigned inducer and current rubric remain the only exposure.
