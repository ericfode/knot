# growing-prefix-copy

Public entry: `def solve(xs: List<&2,U32>) -> List<&2,U32>`. The input
may be marked `+xs` when reused; quantities must check.

Domain: every finite standard Base list of U32 values, with length at most
2^32-1. Empty and singleton inputs are valid. Every arithmetic operation is
U32 arithmetic modulo 2^32, including multiplication and addition.

For input [x0, ..., x(n-1)], return [3*x0+1, ..., 3*x(n-1)+1]. Preserve every position and duplicate.

The result is the entire observable output. Do not print, mutate external state,
ignore elements, reorder elements, or return a checksum instead of the list.

Required performance: O(n) dynamic work and O(n) result storage in the pinned
Bend 2.0.29 JavaScript backend, excluding host input construction and output
validation. Dynamic work includes generated function entries, loop iterations,
and allocations. A bounded number of full traversals is allowed.

Keep the implementation self-contained in one `.bend` file using `import Base`
only. Preserve the public entry and behavior; internal helper names may change.
Use ordinary Base lists, U32, Nat, Bool, Maybe, and pure helper definitions.
No arrays, strings, external imports, foreign functions, IO, unsafe declarations,
axioms, holes, GPU/backend escape, or candidate-supplied performance counters.
Do not depend on the supplied smoke cases being the only inputs.

The fixture's algorithm is replaceable. Acceptance checks types, full result
equivalence, and dynamic-work scaling on additional undisclosed inputs.
