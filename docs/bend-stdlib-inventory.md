# Bend standard-library inventory for Knot

Inspected **2026-09-26**. **Bend has enough primitives to build a compiler in
Bend, but it does not supply all the efficient collections and algorithms a
substantial compiler needs.** Fixed arrays, linked lists, algebraic data,
machine arithmetic, sorting, and basic file IO are available. The main gaps
are source storage, growable collections, integer-keyed environments,
interning, evaluator storage, and graph utilities.

This is an inventory and source-cost analysis, not a compiler implementation
or a decision about Knot's bootstrap version or backend.

The current [project contract](BEND-SUBSET-STAGES.md) requires direct
self-hosting and a real GPU path for the supported language subset. The
compiler may bootstrap on CPU. Collection availability for that CPU compiler
and GPU support in its generated programs are separate obligations.

## Scope and evidence

| Reference | Inspected state |
| --- | --- |
| Installed compiler | `/Users/ericfode/src/bend-scrabble/.toolchain/bend/bin/bend`, reports **2.0.16** |
| Corresponding upstream release | `981899d6b2fb2c109ed83545cffed9d20910a025` (`v2.0.16`) |
| Current upstream main | `574b6d39a235b539eb19a5c532993a0abb3d11ad`, CLI source reports **2.0.29** |
| Standard library | Entire `bend2/base.bend`, native/JS intrinsics in `bend2/comp.ts`, and relevant `bend2/effs/` implementations |
| Compiler requirements | Actual parser, checker, evaluator, loader, and emitter in upstream `bend2/bend.ts`, `bend2/comp.ts`, and `bend2/main.ts` |

The installed Base file is byte-identical to the `v2.0.16` file: SHA-256
`e149828ca05581f61d1b06cf2a7d1a744e394d29a4c8e1942e5062ecbf30f5b8`.
Upstream main was resolved with `git ls-remote`; source links below pin that
revision. “Missing” means absent from this standard-library surface, not
absent from every Bend package. Local reusable libraries are listed separately.

Costs below describe **compiled native execution**, unless qualified.
They are inferred from implementation, not measured throughput. Element
comparison, allocation, retaining shared values, and releasing overwritten
values can add costs; an O(1) array slot operation does not make destroying a
large object O(1). Source-level normalization during proof checking has a
different cost model.

## Available structures and algorithms

| Capability | What exists | Cost and suitability for a compiler |
| --- | --- | --- |
| ASTs, tagged unions, records | User ADTs; `Unit`, `Bool`, `Cmp`, `Either`, `Sigma`/`Pair`, `Maybe`, `Result` | Suitable. Use `Data` for reusable syntax and explicit IDs for mutable compiler state. No general automatic equality/hash derivation. [Types][base-types] |
| Integers and bit operations | `U32` arithmetic, comparison, shifts, Boolean operations, conversions | Compiled machine operations. Suitable for IDs, indices, hashing, and bitsets. Arithmetic is modular; offsets and capacity calculations need checks. [Intrinsics][intrinsics] |
| Natural numbers | `Nat` arithmetic, comparisons, conversions, text IO | Compiled immediate arithmetic, but the runtime limit is **2^48−1**. The unary Base definition is not the native representation. This is not an arbitrary-precision integer implementation. [Native limits][nat-limit] |
| Floating-point constants | `F32` arithmetic, comparisons, `bits`, `read`, `show`, conversions | Suitable substrate for the reference language's F32 literals and folding. Parsing/printing are host operations; exact cross-target folding still needs conformance checks. No standard F64. [Intrinsics][intrinsics] |
| Symbolic fixed-width words | `Word(n)` and operations over its bits | Available for specifications and proofs. Do not assume arbitrary `Word(n)` operations receive the U32 intrinsic treatment. No standard fast U64/I64/BigInt layer. [Word][base-word] |
| Stacks and sequential lists | `List`, constructors, `head`, `tail`, `reverse`, `append`, `concat` | Push/pop are O(1) when the remainder is preserved; reverse is O(n); append walks its left input. Good for scopes, frames, and accumulated output. [List][base-list] |
| List traversal/search | `map`, `filter`, `foldl`, `foldr`, `any`, `all`, `find`, `contains`, `get`, `set`, `take`, `drop`, `zip`, `range`, `replicate` | Linear traversals; indexing walks the prefix. Not a substitute for an indexed token or node store. Several search helpers eagerly compute recursive arguments; do not assume early exit. [List][base-list] |
| Generic sorting | `List.sort(~A, ~le, xs)` | Stable bottom-up merge sort: O(n log n) comparisons for a valid ordering predicate. Present in both versions. No standard array sort, selection, or binary search. [Sort][base-sort] |
| Fixed indexed storage | `Array.new`, `size`, `get`, `set`, `swap`, `clone` | Native `size/get/set/swap` use direct block access: O(1) for fixed-size elements. Initialization and cloning are O(n). Strong substrate for arenas and dense tables. Capacity is a nonzero power of two; indices **wrap**. [Array][base-array], [emitter][array-emitter] |
| Array traversal | `Array.map`, `Array.to_list`, structural matching | Current `map` uses an O(n) indexed loop. Structural splitting copies blocks; repeated tree traversal can cost O(n log n). The older `map` follows that structural route. See the version notes below. [Array][base-array], [blocks][array-blocks] |
| String-keyed maps | `Map.new/set/get/has/pop/del`, `keys`, `values`, `to_list`, `from_list`, `union`, `size` | A compressed bit trie over strings. Available for a first symbol table, but key probing repeatedly scans string prefixes. Not a generic hash table or integer map. `size` traverses the map. [Map][base-map] |
| String sets | `Set.new/add/has/del/size/to_list/from_list` | A `Map<Unit>` wrapper with the same costs. No named set union/intersection/difference/subset operations or integer sets. [Set][base-set] |
| Text and character utilities | `String` comparison, append/concat/join, split/lines, get/take/drop, prefix/suffix/contains, trim, case conversion; `Char` classification | Native strings are linked code points. Good for sequential consumption; random indexing and length are linear. Character classification is ASCII-oriented, which matches the current identifier grammar. No source-buffer/slice abstraction. [Text][base-text], [parser][parser] |
| Errors and optional values | `Maybe`, `Result`, `map`, `bind`, defaults; `IO.try/pass/die` | Enough to express explicit diagnostics and incomplete results. Source spans, diagnostic accumulation, and recovery are compiler code to write. [Base][base] |
| File and CLI operations | `File.open/read/read_bytes/read_at/size/write/write_bytes/close`; `IO.args/get_env/print/print_err` | Enough for a local source-to-source compiler. Raw reads return `List<U32>` bytes, not a flat byte buffer. No standard directory/path/realpath/temp-file/atomic-replace layer. [File API][files], [raw reads][file-read] |
| External tool invocation | `Process.run` on current main | Supports program, argument list, stdin, output bound, and timeout. Useful for invoking a C compiler/linker. **Absent in 2.0.16**. This is distinct from `IO.spawn`, which runs Bend IO. [Process API][process-api], [native implementation][process-c] |
| Parallel work | Parallel lets/`!`, `IO.spawn/fork/join`, `Chan`; current main adds array atomics and fork/join | Basic facilities exist. They do not supply a dependency scheduler or parallel collection library. `Array.fork/join` are explicitly unsafe shared-array operations. Not required to bootstrap a serial compiler. [Guide][guide], [Array][base-array] |
| Proof infrastructure | Equality, congruence, symmetry, transitivity, dependent types, termination checking | Useful for collection and compiler laws. Mere presence of an API or passing finite examples does not establish the laws of a new implementation. [Equality][base-equal] |

Base also includes TCP/UDP, graphics, audio, images, events, and application
loops. Those are existing facilities, but not missing compiler prerequisites.

## Performance details that change the inventory

### Arrays are a usable foundation, with incomplete collection APIs

`Array` looks like a binary tree in Base. The compiler recognizes its
operations and emits contiguous block reads/writes. Do not classify indexed
access as O(log n) just by reading Base.

Conversely, matching an array into `ANode` children invokes block splitting,
which allocates and copies the halves. Combining children also copies.
For a full recursive walk the resulting recurrence is
`T(n) = 2 T(n/2) + O(n)`, hence O(n log n), before element work.
Use indexed loops for bulk array processing. This applies to the inspected
`Array.to_list` and the 2.0.16 structural `Array.map`; current main rewrites
`Array.map` as an indexed loop. [Block implementation][array-blocks]

Missing wrappers are consequential: logical length, empty vectors, bounds
errors, append/pop, reserve/growth, range copying, slices, folds, and indexed
iteration. A length/capacity wrapper with geometric growth can be written in
Bend using existing arrays. It does not inherently require a new runtime
primitive. Affine elements need move/swap-based operations; reusable `Data`
elements can use `get`.

These costs also depend on the compiler doing the intrinsic lowering. If
Knot emits the structural Base definitions literally, it does not inherit
the seed compiler's direct arrays or machine arithmetic. Self-compilation
needs correct lowering/runtime support for the Base operations actually
used by the compiler, including element layouts, ownership, bounds semantics,
and numeric limits. The upstream loader identifies the actual Base source;
user declarations with the same names are not interchangeable intrinsics.
The required GPU path needs its own execution evidence. [Intrinsics][intrinsics],
[Base identity][base-loader]

### The existing Map is useful, but it does not close the map gap

At each branch, `Map.bit` computes a character index from the bit position,
then walks the string from its beginning to that character. A path through
`h` branches therefore costs up to O(hL + L), where L bounds the examined
key lengths. It also reconstructs the traversed prefixes. Tree height is
driven by differing key bits; this is not a balanced-by-entry-count
O(log n) guarantee. Long common prefixes deserve a dedicated scaling test.
There is no specialized native Map intrinsic in the inspected emitter.
[Bit probing][base-map], [intrinsics][intrinsics]

`Map.get` takes a default and only copies `Data` values; `Map.pop` returns a
`Maybe` and supports taking affine values. `Map.union` enumerates the right
map and repeatedly inserts, with right-hand values winning. It has no
collision-combining callback. `Map.size` is O(n), not stored metadata.

This is especially relevant to the checker: upstream already implements a
separate **persistent U32-keyed `PMap`** for contexts and usage counts in
TypeScript. Its recursive merge combines usage quantities by addition or
branch join. That structure is **not exposed by Base**. It is a concrete
porting requirement, not a hypothetical compiler feature. A word trie with
at most 32 bit steps is one straightforward Bend implementation.
[PMap][pmap], [usage combination][uses]

### Text scanning is possible; indexed source handling needs work

Native IO builds one linked string node per decoded code point. `String.get`
and `String.length` walk these nodes; appending walks the left string.
Scanning by repeatedly requesting positions 0, 1, 2, ... from the original
string is quadratic. Consuming successive tails is linear, so a simple
lexer can start without any new runtime support.

Likewise, repeatedly doing `output = output ++ fragment` is quadratic in
total output for bounded-size fragments. Prepending fragments to a list,
then reversing and concatenating once, provides a viable linear assembly
strategy. A builder packages that discipline; a reusable closure-based
difference list is not a free fit because Bend closures are affine.
[Text][base-text], [native strings][native-strings], [closures][guide]

For source spans and parser checkpoints, an indexed buffer plus offsets is
a better general substrate. `Array<U32>` can hold bytes or code points now;
it is not a packed U8 buffer. `File.read_bytes` creates a list node per byte,
so file-to-array loading still has transient allocation overhead. A direct
buffer IO primitive would improve this, but is an optimization rather than
a requirement for the first parser. Define byte/code-point/UTF-16 offset
conversion explicitly: upstream's TypeScript parser stores UTF-16 indices.
[Raw reads][file-read], [parser][parser]

## Missing components and their priority

“Build first” means needed for a practical implementation of the chosen
stage, not that an inefficient prototype is impossible without it. Target
costs below are proposed acceptance criteria, not existing performance claims.

| Missing component | Why the compiler needs it | Implementation route / target | Priority |
| --- | --- | --- | --- |
| Checked `Vec<T>` and slices | Tokens, declarations, instructions, work arrays; distinguish size from allocated capacity | Owned `Array<T>` plus length/capacity. O(1) indexed access, amortized O(1) append, O(n) growth. Explicit bounds and overflow results | Build first |
| Source store, cursor, spans, line index | Lookahead/backtracking, diagnostics, source retention | One owned indexed buffer per file; file IDs and offset ranges. O(1) cursor steps and range descriptors, O(log lines) offset-to-line lookup | Build with lexer |
| Output builder | C/JS output, generated names, diagnostics | Reversed chunks plus one flatten, or a vector/buffer builder. O(total output) construction | Build with emitter |
| `IntMap<V>` with combining merge | Persistent typing environments, free variables, quantity accounting | U32 trie with bounded bit depth; `get/set/remove/fold/union_with`. Reproduce pointwise add/join semantics explicitly | Build with checker |
| Symbol interner | Avoid repeating string comparisons throughout the compiler | `String -> SymbolId` plus ID-to-text storage. Existing Map can bootstrap it; measure long-prefix keys before replacing it | Build early |
| Generic/specialized hash maps and sets | Composite memo keys, intern tables, constant deduplication | Open addressing over arrays or a persistent hash trie; explicit hash/equality and collision handling. Expected O(1) slot work after hashing | Add when memoization needs it |
| Stable node arena and evaluator cells | Node identity, cached normalization, shared evaluator state | Growable array of first-order nodes/cells indexed by U32; explicit ownership threaded through evaluation | Build with evaluator |
| Queue/deque/worklist | Dependency traversal, reachable definitions, pending analyses | Two lists for a serial queue, or a ring buffer over Vec. O(1) amortized enqueue/dequeue. No `Chan` needed for a serial worklist | Small early utility |
| Graph representation and algorithms | Imports, reachability, call cycles, ordering | ID-indexed adjacency plus DFS/BFS, cycle detection, topological ordering, SCC. O(V+E) with suitable storage | Build as loader/backend require |
| Integer sets and bitsets | Dense visited sets, liveness, free variables, set algebra | Bitset over `Array<U32>`; O(1) membership and O(N/32) dense Boolean operations. Sparse alternatives over IntMap | Add for analyses |
| Binary search, array sort, dedup/grouping | Indexed diagnostic lookup, deterministic tables and passes | Ordinary Bend over arrays/vectors. Reuse list merge sort where conversion is acceptable | Small utilities as needed |
| Priority queue/heap | Heuristic scheduling or some optimization passes | Binary heap over Vec; O(log n) push/pop | Conditional; not a bootstrap blocker |
| Union-find | Metavariable solving, congruence classes, some optimizations | Parent/rank arrays with compression; amortized inverse-Ackermann if that representation and update discipline are chosen | Conditional; the reference bidirectional checker does not imply HM unification |
| Dominators, SSA, fixed-point dataflow, register allocation | A lower-level optimizing backend | Compiler modules over graph/worklist/set primitives | Conditional on backend; not required to emit C/JS |
| Path/module/cache helpers | Canonical module identity, import resolution, cache files | Path operations in Bend; OS effects for realpath, directory operations, replacement, etc. Host adapter can bootstrap this | Needed for full driver parity |
| Hashing and UTF-8 validation | Package integrity, cache keys, strict byte-level diagnostics | Reuse existing local libraries where applicable; no such general layer in Base | Needed by package/cache scope |
| U64/I64/BigInt, binary writer | Wider constants, some hashes, direct object-file emission | Multiword arithmetic/serialization or explicit runtime extension | Conditional on target and numeric compatibility |

Regex engines, parser combinators, ropes, balanced ordered maps, and persistent
vectors are also absent. They are design options, not mandatory dependencies:
a handwritten lexer/parser, byte or code-point buffers, list stacks, IntMap,
and Vec can cover the initial compiler.

## A representation issue beyond the library

The current TypeScript compiler is not mechanically portable by replacing
`Map` and `Array` names. Its higher-order terms contain reusable host
functions, its evaluator updates shared term cells, and several caches use
object identity as keys. Bend closures are affine, and arrays have explicit
ownership. [Terms and contexts][terms], [cells][cells], [cell update][cell-update],
[memo tables][memo-tables], [guide][guide]

A first-order AST/term representation, explicit environments, and stable
node/cell IDs is a plausible route. It permits a `Data` syntax representation
with an owned evaluator store. This is a proposed design, not an implemented
solution. The choice determines whether Knot needs persistent maps, mutable
arenas, hash-consing, or some combination; hash-consing itself is optional.

Safe recursion also needs a plan. The language requires structural descent
and disallows safe mutual recursion; parser and evaluator control can use
explicit modes/frames with justified fuel. Exhausting fuel must return an
incomplete/error state, never “verified.” Using `@unsafe` is another route,
with a different proof boundary. Neither choice is merely a missing
collection. [Recursion rules][guide]

## Changes between the inspected versions

| Area | 2.0.16 | Current main / 2.0.29 |
| --- | --- | --- |
| Basic lists, string Map/Set, text helpers, generic merge sort | Present | Same relevant algorithms |
| Fixed-array random access | Native direct indexing | Native direct indexing |
| `Array.map` | Structural split/rebuild, permits affine element types | Indexed loop into new storage; requires Data input/output elements |
| Shared arrays | No Base fork/join/atomic family | Unsafe `fork/join` plus add/min/max/and/or/xor/exch/cas/fadd atomics |
| Process invocation | No `Process.run` | Present; native implementation and Bun-based JS implementation |
| Other additions relevant to utility code | No `U32.log2`, no `IO.thread_count` | Both present; Nat parsing and min/max implementations also changed |

The additional APIs do not provide Vec, IntMap, interning, source buffers,
queues, or graph algorithms. Nothing in this inventory selects a version.
[Release Base][base-old], [current Base][base]

## Existing local reuse, outside the standard library

These source files were inspected; their full test/proof suites were not
rerun for this inventory. They remain owned by their existing project.

- [SHA-256](/Users/ericfode/src/bend-ideas/lib/sha256.bend:150): byte-list and string hashing. Useful for package/cache integrity; no implication that it is the right inner-loop hash for every compiler table.
- [UTF-8](/Users/ericfode/src/bend-ideas/protocol/utf8.bend:37): explicit decoder state, validation, and byte-length helpers. Its input representation needs adapting if Knot uses an indexed byte buffer.
- [JSON parser](/Users/ericfode/src/bend-ideas/protocol/json_read.bend:167): an existing deterministic Bend lexer/parser using explicit modes and fuel. Reusable technique; not a Bend-language parser.
- [Filesystem effects](/Users/ericfode/src/bend-ideas/lib/fs.bend:6): bounded read and create through a host bridge. It does not fill the entire path/directory/process API gap.

## Verification performed

Five upstream fixtures were copied into a temporary directory and compiled
to native binaries separately with installed 2.0.16 and current-main 2.0.29
(`bun bend2/main.ts`). Every binary exited successfully and matched the
fixture's exact `#|` output: **10/10 runs passed**.

| Upstream fixture | What this check exercises | 2.0.16 | 2.0.29 |
| --- | --- | --- | --- |
| `tests/run/array_wrap_index.bend` | Explicit wrap behavior, with accompanying concrete laws | Pass | Pass |
| `tests/run/array_poly_elem.bend` | Bool, enum, Cmp, and F32 array elements | Pass | Pass |
| `tests/base/list_fold.bend` | List combinators and actual generic `List.sort` | Pass | Pass |
| `tests/base/map_prefix_keys.bend` | Prefix keys, ordered enumeration, right-biased union | Pass | Pass |
| `tests/run/array_map_loop.bend` | U32-to-Bool-to-U32 mapping at 1,024 slots and one slot | Pass | Pass |

Command shape: `<compiler> <fixture-copy.bend> -o <temporary-binary>`, then
run that binary and compare stdout with the fixture expectations. Compiler
check/build and runtime failures were treated separately. The normalized
[receipts](bend-stdlib-inventory-checks.json) retain each fixture's source
hash, expected/actual output, exit codes, and compiler invocation.

This establishes those finite native behaviors. It does **not** establish
large-input throughput, stack safety, collection laws in general, or JS/GPU
parity. The next performance gate should cover indexed scanning versus
tail scanning, output growth, common-prefix Map keys, retained-map updates,
and flat versus structural array traversal at increasing sizes. No compiler
implementation or broad upstream test suite was run.

## Proposed first increment

Build a small compiler-support layer: **checked Vec, Source/Cursor/Span,
OutputBuilder, IntMap with quantity-aware merge, SymbolTable, and explicit
term storage**. Add worklists and graph routines when their first pass needs
them. Most gaps can be filled in Bend over existing primitives; packed byte
IO and some driver effects are the clearest potential runtime additions.

For acceptance, test vector bounds/growth and preservation, span round trips,
builder equivalence to fragment concatenation, map get/set/remove laws,
quantity-merge laws, and interning identity. Verify asymptotic behavior with
scaling tests separately from semantic laws.

[base]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/base.bend
[base-old]: https://github.com/bendlang/bend/blob/981899d6b2fb2c109ed83545cffed9d20910a025/bend2/base.bend
[base-types]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/base.bend#L7-L88
[base-list]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/base.bend#L804-L1012
[base-sort]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/base.bend#L1014-L1083
[base-word]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/base.bend#L1094-L1329
[base-array]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/base.bend#L2223-L2440
[base-map]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/base.bend#L2442-L2880
[base-set]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/base.bend#L2882-L2914
[base-text]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/base.bend#L1776-L2042
[base-equal]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/base.bend#L376-L415
[intrinsics]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/comp.ts#L146-L295
[array-emitter]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/comp.ts#L1792-L1837
[array-blocks]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/comp.ts#L4183-L4309
[nat-limit]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/comp.ts#L3568
[native-strings]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/comp.ts#L5520-L5599
[files]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/base.bend#L251-L288
[file-read]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/effs/file_read.c
[process-api]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/base.bend#L178-L182
[process-c]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/effs/process_run.c
[guide]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/guide/GUIDE.md
[parser]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/bend.ts#L1462-L1590
[terms]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/bend.ts#L278-L337
[pmap]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/bend.ts#L508-L575
[uses]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/bend.ts#L622-L642
[cells]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/bend.ts#L670-L683
[cell-update]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/bend.ts#L2844-L2865
[memo-tables]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/comp.ts#L555-L590
[base-loader]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/bend.ts#L1012-L1020
