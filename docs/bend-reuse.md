# Existing Bend libraries and the Perch parser route

Inspected 2026-09-26. These are available components and proposed integration
steps, not decisions about Knot's bootstrap or compatibility version.

## The Jev library exists

Saved project labels differ from directory names:

| Saved project | Source directory | Role |
| --- | --- | --- |
| bend-tests | `/Users/ericfode/src/bend-ideas` | Reusable Bend libraries |
| bendy | `/Users/ericfode/src/bend-tests` | Focal Life and Φ/Sigil applications |

The source owner is
[`jev/jev.bend`](/Users/ericfode/src/bend-ideas/jev/jev.bend:1), documented in
[`JEV_CLIENT.md`](/Users/ericfode/src/bend-ideas/jev/JEV_CLIENT.md:1).
It provides typed `Choice`, `Noul`, `Score`, `NamedQuestion`, and `Request`
values, `ask` / `ask_with`, raw requests, authentication, status handling, and
bounded retries. It delegates JSON to `protocol/json.bend` and HTTP/TLS to
`net/http.bend` and `net/https.bend`. Response schema validation and experiment
receipts currently belong to the application's Python orchestration.

The application calls the shared CLI through
[`sigil/bend_transport.py`](/Users/ericfode/src/bend-tests/sigil/bend_transport.py:1).
Its experimental Jev-selected expression compiler is not a general Bend parser.
The libraries are pinned locally to Bend 2.0.16. Reuse the owning library;
do not copy a second client into Knot. The existing application uses the
`bend_libraries` alias because hyphens in import paths trigger invalid generated
JS identifiers under 2.0.16; preserve or independently retest that constraint.

There is also an independent TypeScript semantic linter at
[`/Users/ericfode/src/jevlint`](/Users/ericfode/src/jevlint/README.md:1).
Its experiments suggest asking Jev narrow, closed-set semantic questions and
doing counting, structure extraction, and policy decisions deterministically.
That is useful design evidence, not a substitute for evaluating Bend rules.

## Can Bend parse Bend?

Yes: Bend has the strings, algebraic datatypes, recursion, and explicit state
needed to implement a deterministic lexer and parser. There is already a
[`JSON parser written in Bend`](/Users/ericfode/src/bend-ideas/protocol/json_read.bend:1).
No existing complete Bend-in-Bend parser was found in the inspected projects.
The Jev library supplies model calls, not a parser.

The current Bend 2 parser is handwritten **TypeScript** in `bend2/bend.ts`.
This is true of both the reference
[`v2.0.16` parser](https://github.com/bendlang/bend/blob/v2.0.16/bend2/bend.ts#L2558)
and upstream main inspected at
[`574b6d39a235b539eb19a5c532993a0abb3d11ad`](https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/bend.ts#L2440),
whose CLI identifies itself as 2.0.29. The trusted interpreter/checker is in the
same TypeScript module, code generation is in `bend2/comp.ts`, and the CLI is
`bend2/main.ts`. This does not mean emitted native programs execute TypeScript.

For Knot, a Bend parser can initially be compiled with the existing compiler.
Parsing its own source is one milestone; compiling itself also requires the
checker, lowering, backend, and runtime interfaces.

## Extending Perch is feasible

Perch is JavaScript/TypeScript. A direct Node 22.22.3 smoke test imported
upstream `bend2/bend.ts` with `--experimental-strip-types`, called `book_nil()`
and `parse_book()` on `def identity(x: U32) -> U32: x`, and obtained one `Def`
with a body. It required neither Bun nor an external process. This establishes
a useful integration seam, not complete parser-adapter compatibility.

The local adapter is now implemented in `scripts/perch-bend.mjs`, installed into
the pinned Perch bundle by `scripts/install-perch-bend.mjs`. It uses vendored
upstream parser code with additive source observers, supplies embedded Base
syntax context, and reports unresolved imported semantic context. See
[current setup and limits](perch.md). The roadmap below motivated the adapter;
complete dependency-aware resolution and quality metrics remain future work.

Integration boundaries:

1. Pin the Bend parser revision independently of Knot's eventual bootstrap pin.
   Package or vendor the parser and required Base resource with its license.
2. Dispatch `.bend` to a Bend adapter in Perch's `src/analysis.js`, retaining
   tree-sitter for other languages. Implement the existing `Analyzer` contract
   from `src/treesitter/types.ts`; no tree-sitter grammar is inherently required.
3. Emit declarations with stable names, full source ranges, and explicit
   diagnostics. Add import aliases, direct-call references, and value references
   for function arguments, then make `src/graph.js` resolve Bend module paths.
   Unresolved and higher-order calls must remain explicitly unresolved.
4. Preserve source before elaboration. `parse_def` currently flattens bodies;
   `Book` stores lowered terms, and whole-definition/comment spans are not its
   primary output. Capture source-level spans before flattening. Convert
   TypeScript string offsets to Perch's UTF-8 byte/column locations correctly.
5. Separate source parsing from loading. `book_load` can resolve and fetch hub
   imports and write cache files. Analysis should use an explicit resolver over
   the scanned revision, never run the target program, and not fetch packages
   merely to identify a definition. Import extraction and Base/name context
   need a deliberate API; `parse_book` alone is not a complete module loader.
6. Test `.bend`-only `scan`, per-definition `check`, exact Unicode spans,
   multiline signatures, nested matches, quantities, laws/proofs, imports,
   partial files, and failure coverage. Do not fabricate risk metrics when an
   equivalent metric is unavailable; make their definition explicit.

After that, narrow the most useful draft rules to `each: method` and add real
caller/callee context. Whole-file rules remain useful for cross-definition
contracts. Re-evaluate their precision after changing context granularity.

The existing Bend Jev client is a separate path: it can power a future linter
written in Bend. Perch already has its own TypeSafe transport, so a parser
adapter does not require replacing that transport or wrapping the Bend client
inside Node. Keep deterministic syntax, typing, and proof acceptance outside
model decisions in either implementation.
