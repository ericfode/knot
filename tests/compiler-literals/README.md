# Primitives and literals

Milestone 5 adds the frozen literals surface to the checked `--bundle` path.
The contract is the unchanged [40-fixture freeze](FIXTURES.md) and
[expectations](expectations.json): 275 seed calls, 24 agreeing books, 11 Invalid
books and 5 Unsupported books. The agreeing books contribute 268 calls.
[The supplemental freeze](supplemental.json), committed as `d3c1e7b` before
implementation, adds 12 calls for `1n+ +n`, `Nat.is_le`, `U32.and` and
`String.reverse`. Both freezes are verified against seed 2.0.29, commit
`574b6d39a235b539eb19a5c532993a0abb3d11ad`, on every gate run.

## Mechanism

Literal payloads are bounded U32 values or lists of U32 codes. Quoted source is
ASCII; `\u{...}` accepts 1–8 hexadecimal digits, including surrogates and values
past U+10FFFF. Decoding never passes through the host's String constructor.
Thus `"\u{d83d}\u{de00}"` remains two Chars and differs from `"\u{1f600}"`.
NUL is an ordinary code. Decimal overflow is Invalid. Bare decimals have type
U32; the `n` suffix selects Nat. There is no implicit numeric coercion.

The legacy lexer retains the previously gated single-file surface. The bundle
lexer composes its transitions with quoted-token reading. The shared parser
adds literal nodes and offsets, and reports the five frozen unsupported cases
with their exact phase/code prefixes. Arithmetic operator sugar, F32 and raw
non-ASCII quoted text remain Unsupported, including seed-invalid unannotated
operator sugar. Unsupported is not evidence that a source book is invalid.

The primitive pattern matrix specializes columns without changing row order.
Numeric and Char tests require a default. Nat literals and offsets expand into
Zero/Succ cases; String literals expand into SNil/SCon cases with Char tests.
The first applicable leaf supplies the result; all leaves, including redundant
ones, are checked. Offset fields preserve the existing quantity and strict
structural-descent rules. Offsets above 256 are Invalid, matching the seed.
General nested patterns and `Chr{...}` patterns remain outside this increment.

The checked core gains Literal, Intrinsic and Default. U32/Char expressions use
the existing scalar Value term. The independent evaluator interprets this core
and materializes Nat and String as ordinary immutable Value/Object trees.
Its primitive algebra uses temporary bounded counts for arithmetic and code
lists for text, then reconstructs source values. It never interprets Wasm or
the emitted instruction graph.

## Base trust boundary

The loader verifies the unchanged Base file's SHA-256 before selection. The
closed registry in `src/literal-base.bend` lowers four Base types and 39 primitive
operations. Their parameter quantities and result types are explicit; calls
are checked normally. Unsafe and foreign declarations are rejected before
registry lookup. User syntax cannot construct an Intrinsic node or a line-zero
installed-type marker.

Lowered Base bodies are trusted intrinsic implementations, not source proofs.
`--audit-bundle` reports three disjoint inventories whose union is all 466
Base declarations:

- `BaseChecked`: selected Base bodies parsed and checked as source.
- `BaseIntrinsic`: selected members of the closed lowering registry, including
  its four datatype representations.
- `BaseUnchecked`: the exact unselected complement.

The literal gate checks this partition in both lanes for all 25 accepted books.
The existing modules gate retains its Bool-only trust assertions. Pinning
identifies the source defining the semantics; differential observations and
helper laws do not prove equivalence for every possible intrinsic input.

## Wasm profile: `knot-literals-wasm-1`

A checked book containing an installed primitive type selects the new profile.
Other books keep the existing enum emitter and frozen module bytes. The new
profile serializes an instruction graph plus a fixed Wasm interpreter for that
graph. All checked function bodies are lowered. Entry arguments and recursive
calls run at invocation time; there is no compile-time evaluation of answers.
The emitted module has no imports and needs no host language semantics.

U32 and Char are unboxed i32 bits. Arithmetic is unsigned where required. Guards
implement division by zero (`div(x,0)=0`, `rem(x,0)=x`) and shifts of at least 32
(`shl(x,n)=shr(x,n)=0`). Right shift is logical. Bool and Cmp retain the pinned
Base constructor order.

Nat retains unary Zero/Succ cells; it is not replaced by an unproved binary
ABI. String follows Base's `SNil` / `SCon{head: Char,tail: String}`. Each cell
contains its tag followed by live fields in declaration order. Erased fields
have no slot. A shared immutable zero cell at address 0 represents empty Nat
and String; other nullary constructors of fielded types may have allocated
cells. Allocation is monotonic and instance-scoped, with no reclamation.

This deviates from the one-page fields ABI for a concrete reason: the frozen
65536n witnesses already exceed a 64 KiB unary heap, and non-tail structural
recursion at depth 65536 exceeds the host call stack. The new ABI fixes memory
at 1024 pages (64 MiB) and keeps explicit disjoint stacks:

| Region | Byte range | Purpose |
| --- | --- | --- |
| Static | `[0,1048576)` | Empty cell, function metadata, instruction words |
| Returns | `[1048576,5242880)` | 12-byte continuation records |
| Frames | `[5242880,23068672)` | Lexical slots and operand stack |
| Heap | `[23068672,67108864)` | Immutable tag/field cells |

An instruction is five U32 words: opcode, three operands, next index. Function
metadata gives entry index, frame slots and source parameter count. Lowering
permits at most 32768 instructions; serialization separately bounds static
data and the total output. Temporary Nat counts and traversed String primitive
inputs are bounded at 1048576 elements. Guards report resource exhaustion.
Evaluator transitions, Wasm allocation, graph size and primitive traversal have
different budgets; exhaustion is not an Invalid judgment or a claim of semantic
disagreement. The profile has no arbitrary source loop or mutual-recursion
support; checked self-recursion retains the first-parameter descent restriction.

The host adapter accepts only enum-signatured entry observations and results
0–255, just as before. Structured and primitive-signatured functions are
internal-call targets even though all source functions are exported. Valid
signature provenance and per-type ordinals remain caller preconditions. A
profile-owned `unreachable` during invocation reports
`Exhausted\twasm\tresource-limit`; other traps report HostFailure. Profile
selection is a provenance assertion, not an arbitrary-Wasm validator.

## Verification

Run with network disabled and `BEND_NO_TELEMETRY=1`:

```sh
python3 tests/compiler-literals/regen.py
python3 tests/compiler-literals/supplemental.py
python3 tests/compiler-literals/check.py
npm run -s gates
npm run -s gates:verify
```

The new gate builds native and Bun versions of check/eval/compile. It requires:

- 41 fixture books, 287 fresh seed calls, 82 checks and 82 primary compilations.
- 560 agreeing evaluator observations and 560 matching Node/Wasm observations;
  32 additional evaluator rejections, giving 592 evaluator observations total.
- 25 byte-identical native/Bun module pairs and 50 complete Base trust audits.
- 32 rejected-compilation output-preservation probes and 32 additional
  compilations proving no artifact is created at an absent output path.
- Eight budget/host probes, including four preserved outputs on exhaustion.
- Three complete proof entries, 24 filled laws; five type-correct semantic
  mutants, five Wasm kills and two additional evaluator kills.

The mutant witnesses are frozen calls: unsigned compare across the high bit,
zero divisor, shift by 32, surrogate equality and the 255/256 Nat offset edge.
Each mutant compiler must typecheck, build and emit a valid module. Four kills
are explicit wrong enum results; the division mutant must reach the real Wasm
`divide by zero` trap. A compiler failure, timeout or malformed Wasm is not a
kill. Only the Bun compiler lane is mutated; both unmodified compiler lanes are
covered by all differential observations.

The [receipt](receipts/literals.json) records source/seed/tool identities,
separate exit categories and complete observations. It is regenerated; it is
not a substitute for running the gate. [LAW_REVIEW.md](LAW_REVIEW.md) states the
proof boundary. The gate is registered after the existing fifteen gates.
Existing gate assertions and shared receipts belong to their owners.

Nine new style families close local imports and each stays below 48000 source
bytes. Offline Perch preflight reports context blockers independently of the
deterministic gates; unresolved ByteOutput context and truncated helper/caller
context can still block automatic style qualification. Earlier oversized
compiler families remain visible. Live style ratings, distributions and
semantic Perch review are deferred to the coordinator under D9; no live style
pass is claimed.

## Next increment

Broaden the source and host boundaries only with new seed freezes. Priorities
are constructor patterns for Char, broader nested matrices and recursion,
primitive/structured host observations, and owned storage/reclamation. General
compiler correctness, all-input intrinsic refinement, R3/R7 storage acceptance,
and self-hosting remain unproved. Operator sugar and F32 need their own scoped
acceptance work.
