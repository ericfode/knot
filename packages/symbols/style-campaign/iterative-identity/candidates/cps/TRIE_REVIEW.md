# Independent trie review

Reviewed source: `packages/symbols/build/memetic-search/phase/04_trie/main.bend`.
SHA-256: `8833421f56c5d7686800ed1e712abad777ade6b7fe37c3ede20065c3e1135354`.
Review is read-only. No candidate, production, independent model, law, assertion,
or rubric was modified. Root owns native performance and mutation checks.

## Behavioral result

No concrete functional defect was found by source inspection. This is not a
universal formal refinement proof.

A sufficient representation invariant is:

- `Vacant` denotes no keys.
- `Here{id,more}` binds the empty suffix; every key in `more` is nonempty.
- `Fork{c,less,same,more}` routes empty suffixes and smaller leading codepoints
  to `less`, strips exactly one equal leading codepoint into `same`, and routes
  larger leading codepoints into `more`.

`Trie.path` establishes the invariant for one string. `Trie.put` preserves it:
only the selected branch changes, and the empty-name branch never aliases a
character branch. `Trie.get` follows the same comparisons and reconstructs the
visited path from the returned child. This preserves all table observations.
`Here` is an explicit terminator, separate from `Fork{0,...}`, so NUL and empty
strings are distinct. `U32.cmp` is exactly the code comparison used by Base
`Char.cmp` at `.toolchain/bend-2.0.29-574b6d3/bend2/base.bend:1729`.
Only EQ strips the head character; LT and GT retain the complete remaining name.
This includes prefix distinctions and composed/decomposed Unicode spelling.

`Table.intern` probes before requesting an append. A hit returns its original ID
without consulting capacity. A miss obtains the old Vec length, then pushes the
name. `inserted` publishes `Trie.put` only in the successful Vec branch. A failed
push retains the original trie and Vec's returned unchanged owner. Reverse lookup,
limit clamping, and ID lifetime remain the original public implementation.

## Termination and costs

`Trie.path` recurses on the string tail. `Trie.get` and `Trie.put` recurse on a
strict subtree; encountering `Vacant` starts the separately structural path
builder. No unsafe declaration or owner cloning is present. This is consistent
with the already reported successful pinned compiler gate.

The node path has no balancing guarantee. A get rebuilds one node and creates a
continuation at each visited edge. Successful interning performs a get and then
a put over that path, plus the unchanged Vec work. New suffixes allocate one Fork
per remaining character and one Here. Vec still stores complete source strings,
so the trie is an additional character representation; memory cost should be
measured alongside runtime if this representation is retained.

A concrete adverse sequence is N increasing one-character names
`SCon{Chr{i},SNil{}}`, i = 1..N. Every new key follows the growing `more` chain.
The last lookup/insertion is linear in N and population performs quadratic
forward-index work. Reverse sorted names similarly grow `less`. Recursive path
reconstruction has depth linear in N. The original compressed-bit Map's height
for fixed one-character keys is bounded by the finite key bit width, so this is
a new practically significant shape. Paired native runs at N = 1024, 4096, 8192
were requested from root. Alphabet-limited identifier benchmarks can miss it.

## Missing adversarial partitions

The frozen exhaustive corpus uses only empty, a and ab and runs three commands.
It cannot first build a larger branched tree and then observe all its forward
bindings. The Unicode witness includes isolated NUL but no NUL prefix chain.
A useful fixed full-capacity sequence is:

1. Insert a-NUL, empty, NUL-a, a, NUL, ab, b, aa, in that order, at capacity 8.
2. Find and repeat each name, preserving every original ID and length.
3. Attempt fresh a-NUL-b, require Exhausted, then recheck all names and resolutions.

The same names in reverse and a pivot-first order exercise both lateral
branches. Supplementary Unicode prefixes and long repeated-prefix misses deserve
coverage. The public wording is exact Bend Strings; if all constructible Char
values are included, raw boundaries such as Chr{0}, Chr{0xD800}, Chr{0x10FFFF},
and Chr{0xFFFFFFFF} are also relevant because Base Char is an unvalidated U32
wrapper. Actual scalar values suffice for the sorted-key performance witness.

## Proof and documentation boundaries

The universal laws first, zero_limit, and empty_find do not establish arbitrary
put/get correspondence in a nonempty trie. first observes reverse Vec storage
after insertion; the other two do not construct a nonempty forward index. The
remaining forward observations are concrete normalization or finite conformance.
Keep that boundary explicit even if all current laws, mutations and tests pass.

The frozen SPEC's implementation description and abstraction relation mention
Base Map and its compressed bit trie. A retained Trie representation needs an
accurate replacement of those descriptive statements and a disclosed new cost
model. Preserve the behavioral contract and independent gates.
