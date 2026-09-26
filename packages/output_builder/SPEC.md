# Ordered output builder

Abstract value: a finite sequence of Bend characters. Observation is `finish`.
The independent reference value is an ordered list of string fragments,
interpreted by right-associated flattening. Tree grouping is unobservable.

`empty` observes the empty string. `fragment(s)` observes exactly s.
`append(b,s)` observes the characters of b followed by s.
`character(b,c)` appends exactly one Char, including LF, CR, NUL and non-ASCII.
`compose(a,b)` observes a followed by b. `finish` returns this exact sequence.
No formatting, newline insertion/conversion, Unicode normalization, scalar
validation, or byte encoding occurs. Raw `Chr{U32}` values are preserved too;
only callers supplying Unicode scalars may call the result Unicode text.

All operations are pure and persistent. Retaining an old value preserves every
character. Inputs include empty strings/builders, singleton and arbitrary finite
trees, repeated fragments, all U32 Char payloads, and arbitrary tree groupings.
There are no indices, capacity integers, invalid-input failures, or partial
completion results. Allocation/stack/host exhaustion aborts execution rather
than returning success; no unbounded-resource runtime guarantee is made.

Complexity counts the expanded tree (shared subtrees count once per occurrence
in emitted output), N character occurrences and K nodes, including empty nodes.
Construction allocates O(1) nodes and performs no string traversal. Finish uses
O(N+K) structural work and O(N) output, with O(tree depth + longest fragment)
recursive stack in a direct evaluator. Native lowering may optimize recursion;
finite scaling runs do not prove stack safety for every possible depth.
Releasing a final retained tree can have O(K+N) reference-release cost. Repeated
finish repeats traversal. No streaming IO, byte codec or pretty-printer.

Refinement relation: tree Empty maps to []; Chunk(s) to [s]; Join(a,b) to
concatenation of their ordered fragment lists. `finish(t)` equals independent
`model.flatten(model.chunks(t))` for every tree. The implementation emits into a
suffix; it never appends the accumulated output as the left operand.

## Checked bytes

Bytes use a distinct builder, explicit `List<&2,U32>` output and a U32 limit.
Abstract state is (limit, ordered byte sequence). Reachable states maintain
length equal to sequence length, every element <=255 and length <= limit.
`empty(cap)` observes (cap,[]). `fragment` is checked append to empty. `byte`
is checked singleton append. `append` validates the fragment left to right:
first inspect byte validity; then remaining capacity. First encountered error
wins. `compose` concatenates sequences if right length fits the left remaining
capacity; the output retains the left limit. `length` and `limit` observe the
metadata. Failures return no new builder and cannot alter retained arguments.

Unchecked constructors/helpers are visible because Bend has no module privacy;
they require the stated representation invariant. Constructible witnesses are
`empty(0)`, `fragment(4,[0,127,128,255])` and checked compositions in conformance.
A forged count is outside the checked API's domain. Boundary arithmetic probes
may deliberately call internal helpers with synthetic lengths: these test the
arithmetic guard, not feasibility of allocating four billion bytes.

The length guard compares before adding, including at U32 maximum. No counters
are used in text assembly. Text native behavior preserves raw Char payloads;
JS scalar-text restriction is a backend limitation, not byte validation.
No automatic conversion exists between text codepoints and raw bytes.

Byte fragment validation is linear in its input; byte/compose/metadata access
are constant structural work. Finish is linear in byte occurrences plus tree
nodes. Different capacities can make one association fail while another
succeeds, so checked-result associativity requires sufficient intermediate
capacity. Content associativity is universal for the underlying trees.
