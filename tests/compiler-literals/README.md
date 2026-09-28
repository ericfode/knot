# Primitives and literals

Milestone 5 adds the frozen literals surface to the checked `--bundle` path.
The contract is the unchanged [40-fixture freeze](FIXTURES.md) and
[expectations](expectations.json): 275 seed calls, 24 agreeing books, 11 Invalid
books and 5 Unsupported books. The agreeing books contribute 268 calls.
[The supplemental freeze](supplemental.json), committed as `d3c1e7b` before
implementation, adds 12 calls for `1n+ +n`, `Nat.is_le`, `U32.and` and
`String.reverse`. [The regression freeze](regressions.json) adds books for
confirmed review findings, each committed before its fix. Round 1 (ten books):
spaced Nat offsets and their adjacent controls, the Base U32 constructor, and
40000- and 131072-Char String primitives. Round 2 (23 books): unannotated
literal and Nat-offset bindings, literal and offset scrutinees, literal
patterns on datatype scrutinees, literal field patterns, zero offsets and two
agreeing controls. Round 3 (13 books): escapes before `{`, and the seed's
`+` promotion of a matrix column (every row and field of the column, but not
a binder row's view of a parent whose field alone is promoted), with nine
seed-invalid controls. [The result freeze](results.json), committed as
`60a4795` before its fix, adds five books and 61 calls whose results are
U32, Char, String, Nat or records with primitive fields, each with the
display Knot must print. Round 5 (21 regression books, committed as
`42a775b` before its fix): thirteen seed-valid books whose failing body sits
in an arm that no value reaches first (duplicates, arms after a catch-all,
`2n` and `3n+q` after `1n+p`, `SCon{'a', SNil{}}` after `"a"`), six
seed-invalid controls (two reachable failing arms and four invalid patterns
in unreachable arms), and a literal typed by a book's own Nat or U32 without
Base. Round 7 (one book, committed as `068539e` before its fix):
expression offsets `1n+`, `2n+` (Base's `Nat.double`) and `3n+` through
recursion 3000 to 4000 deep, with a `0n+t` control and a mismatch control.
All four freezes are verified against seed 2.0.29,
commit `574b6d39a235b539eb19a5c532993a0abb3d11ad`, on every gate run.

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
with their exact phase/code prefixes. An offset needs its `+` to touch the
literal token (`1n+p`, `1n+ p`, `1n++p`); a separated `+` (`1n +p`, `3n + x`)
is operator sugar and reports `Unsupported\tparse\toperator`, as bare
operators do. The seed reads `kn+t` as k successors around t, so the parser
reads `0n+t` as t itself, whatever t's type; every parsed offset therefore
spells at least one `Succ`. Arithmetic operator sugar, F32 and raw
non-ASCII quoted text remain Unsupported, including seed-invalid unannotated
operator sugar. Unsupported is not evidence that a source book is invalid.

An expression offset checks as its matrix spelling, the expansion the
pattern matrix uses (`M.literal`): `kn+t` is k `Succ` constructors around t,
which is checked once and shared, as the seed builds it. Evaluation allocates
k cells, so recursion through `1n+up(p)` or Base's `Nat.double`
(`2n+double(p)`) is linear in its depth. Until round 7 it lowered to
`Nat.add(kn,t)`, which counts both arguments and materializes a fresh Nat:
about n²/2 cells over a depth-n recursion, Exhausted at `up(2000n)` in the
evaluator and at `up(3400n)` in Wasm. Each successor costs three levels of
the 4096-deep checker budget, so an expression offset above 1364 (less
inside a deeper expression) is `Exhausted check budget`; it checked before,
at O(k+|t|) per evaluation.
Pattern offsets stop at 256 either way.

The primitive pattern matrix specializes columns without changing row order.
Numeric and Char tests require a default. Nat literals and offsets expand into
Zero/Succ cases; String literals expand into SNil/SCon cases with Char tests.
Each path ends in the list of rows that apply to it. Its first leaf supplies
the result and is live on that path; the rest are dead there. Every leaf is
checked, in two walks of the plan: all live leaves first, then all dead ones.
The seed checks a body only where a path selects its row, so a dead leaf's
failure reports `Unsupported\tcheck\tdead-arm`, and only a book whose live
leaves all check reaches it. Duplicates, rows subsumed by an offset
(`2n` after `1n+p`) and rows repeated through nested String columns are all
dead this way; patterns stay checked in every row, as in the seed. One
imprecision remains: a catch-all after rows naming every constructor is dead
in the plan, but the seed checks it in a default continuation, so a failure
there is Unsupported where the seed reports an error.
Offset fields preserve the existing quantity and strict
structural-descent rules. Offsets above 256 are Invalid, matching the seed.
Quantities follow the seed's `match_flatten`:
- a row that binds a column with `+` promotes that column, and every field
  opened from it, in all rows;
- a binder row (`x`, `_`) names its column's unrefined value, so a `+` on a
  field alone does not let a catch-all use the column twice.
General nested patterns and `Chr{...}` patterns remain outside this increment.
Base spells U32 as `U32{data: Word(32n)}`, but an installed U32 is unboxed
bits, so that constructor reports `Unsupported\tcheck\tu32-constructor` in
patterns and expressions. A literal checks against the installed primitive
of its kind; Base installs it for every literal a book uses. Without Base
nothing is installed, and the seed spells the literal by bare constructor
names instead, as the matrix expands it: `0n` as `Zero{}`, `2n` and `1n+p`
through `Succ`, `""` as `SNil{}`. Knot keys this case on the absent
primitive, not on a type name, and does not interpret the spelling:
- a literal or offset, in an expression or as a match arm, whose target
  datatype declares the spelled constructor reports
  `Unsupported\tcheck\tliteral-base-type`, whatever the type is called
  (Nat, N, A.T, String, T);
- a target that declares no such constructor, or no target at all, reports
  `Invalid\tcheck\tunknown-type` at the literal, as the seed rejects it;
- a U32 or Char literal spells Base's `Word`, which Knot does not model, so
  it is Unsupported against any target.
The seed accepts `2n` for an own Zero/Succ Nat and rejects `3` for an own
`U32 is Data: Z{}`.

Literals and Nat offsets are constructor values that check against a known
type; like the seed, Knot infers none. An unannotated binding such as `n = 3`,
`+s = "ab"` or `n = 2n+m` reports `Invalid\tcheck\tannotation-required`, as a
bare constructor does; `n : U32 = 3` checks. A literal or offset scrutinee
(`match 3:`, `match 1n+m:`) reports `Invalid\tcheck\tconstructor-scrutinee`.
A datatype scrutinee never enters the primitive matrix. With Base, a literal
or offset arm there reports `Invalid\tcheck\tpattern-type`; without it, the
arm takes the spelled-constructor rule above. A literal inside a constructor
field pattern reports `Unsupported\tcheck\tnested-field-pattern`, as a nested
constructor does.

The checked core gains Literal, Intrinsic and Default. U32/Char expressions use
the existing scalar Value term. The independent evaluator interprets this core
and materializes Nat and String as ordinary immutable Value/Object trees.
Its primitive algebra uses temporary bounded counts for arithmetic and code
lists for text, then reconstructs source values. Code-list traversals are
tail calls with accumulators (`count`, `onto` = reverse-append, and `equal`),
so the Bun and native evaluator lanes reach the same bounds. It never interprets Wasm or
the emitted instruction graph.

The evaluator prints `Evaluated<TAB>type<TAB>word<TAB>display`. A value of an
installed primitive type displays as the seed's literal for it, the text that
reads back as the value: `300`, `3n`, `'a'`, `"a\n"`. `quoted` in
`primitive-eval.bend` inverts the reader's escape table: `\0 \t \n \r \\`,
the quote escaped only inside its own kind of literal (`'\''` but `"'"`),
`\u{hex}` in lowercase for controls, DEL, surrogates and codes past U+10FFFF,
and raw UTF-8 for every other code. Escaped surrogate pairs stay two codes, as
in the seed. Records keep Knot's live-field frame `Name{a,b}`; only the leaves
follow the seed. The word column is a U32 or Char value's bits and otherwise a
constructor tag. Before this fix the evaluator read a scalar's bits as a
constructor index: `#U32{}` or `Chr{}` with exit 0 for bits 0, and
`InternalFailure eval result-tag` otherwise.

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

The literal gate checks this partition in both lanes for all 30 accepted books.
The modules gate's audit accepts `BaseIntrinsic` rows under the same
three-way partition and requires each modules book to declare any intrinsic
rows it reaches (none do); see the literals amendment in
[its contract](../compiler-modules/SPEC.md). Pinning
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
python3 tests/compiler-literals/regressions.py
python3 tests/compiler-literals/results.py
python3 tests/compiler-literals/check.py
npm run -s gates
npm run -s gates:verify
```

The new gate builds native and Bun versions of check/eval/compile. It requires:

- 126 fixture books, 487 fresh seed calls, 252 checks and 252 primary compilations.
- 898 agreeing evaluator observations and 898 matching Node/Wasm observations;
  182 additional evaluator rejections, giving 1080 evaluator observations total.
- 35 byte-identical native/Bun module pairs and 70 complete Base trust audits.
- 182 rejected-compilation output-preservation probes and 182 additional
  compilations proving no artifact is created at an absent output path.
- 5 result books and 61 frozen displays: 122 exact evaluator displays across
  both lanes, lane-equal, and 5 byte-identical native/Bun module pairs. The
  Node host observes enum results only, so these calls have no Wasm lane.
- Eight budget/host probes, including four preserved outputs on exhaustion.
- Three complete proof entries, 33 filled laws; 24 type-correct semantic
  mutants: five Wasm value kills, one exhaustion kill in both Wasm and the
  evaluator, fourteen verdict kills and six evaluator kills.
  The two dead-arm laws, the five own-type literal laws and the offset
  spelling law live in
  `src/check-LAWS.bend`, beside the checker they describe, and the checker
  gate proves them.

The mutant witnesses are frozen calls: unsigned compare across the high bit,
zero divisor, shift by 32, surrogate equality and the 255/256 Nat offset edge.
Each mutant compiler must typecheck, build and emit a valid module. Four kills
are explicit wrong enum results; the division mutant must reach the real Wasm
`divide by zero` trap. Fourteen verdict mutants change a frozen book's
classification: dropping the offset adjacency test compiles `case 1n + p` to
`Built`; restoring the catalog lookup reports the U32 constructor as
`Invalid`; inferring a literal's type compiles `n = 3` to `Built`; keeping
`0n+t` as `Nat.add(0n,t)` rejects the seed-valid offset-zero book as
`Invalid pattern-type`; dropping the literal scrutinee arm fails with
`InternalFailure`; an Unsupported literal arm on a datatype replaces the
seed's Invalid; the broad `\X{` arm rejects the escape-brace book as
`Invalid lex escape`; disabling column promotion rejects promoted-column as
`Invalid check affine-reuse`; keeping the refinement for a binder row
compiles the seed-invalid affine-default-scrutinee to `Built`; checking every
leaf in the live walk rejects the seed-valid dead-arm-u32-duplicate as
`Invalid check type-mismatch`; walking dead leaves before live ones reports
the seed-invalid live-arm-u32-default as `Unsupported check dead-arm`; and
restoring Invalid for a literal typed by a book's own datatype rejects the
seed-valid own-nat-literal as `Invalid check literal-base-type`; skipping the
literal-arm type check rejects the seed-valid own-nat-zero-pattern as
`Invalid check pattern-type`; and ignoring the spelled constructor rejects the
seed-valid own-n-literal-expr as `Invalid check unknown-type`. The
exhaustion mutant offset-nat-add restores the `Nat.add(kn,t)` lowering of an
expression offset; `successor` in offset-expression-depth (frozen Yes) then
reports `Exhausted wasm resource-limit` from its compiled module and
`Exhausted eval budget` from its evaluator. The evaluator-only `append-reversed` mutant changes no emitted byte;
its evaluator answers No for `"ab" ++ ""` = `"ab"`. Three display mutants
are killed by an exact wrong display: skipping the primitive dispatch prints
`'\0'` as `Chr{}` again, escaping both quotes everywhere prints `'"'` as
`'\"'`, and dropping DEL from the escaped range prints `'\u{7f}'` raw. A compiler failure,
timeout, malformed Wasm or any other verdict is not a kill. Only the Bun lanes
are mutated; both unmodified lanes are covered by all differential
observations.

The [receipt](receipts/literals.json) records source/seed/tool identities,
separate exit categories and complete observations. It is regenerated; it is
not a substitute for running the gate. [LAW_REVIEW.md](LAW_REVIEW.md) states the
proof boundary. The gate is registered in `scripts/gates/run.py` after the
existing gates. CLI builds must report exactly the seed's frozen
foreign-dependency verdict for the modules host query
(`tests/compiler-modules/host-check-expectations.json`), and harness timeouts
scale with `KNOT_GATE_TIMEOUT_SCALE`.
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
primitive/structured Wasm host observations and host arguments (a U32 host
argument is still read as an ordinal of U32's one constructor), and owned
storage/reclamation. General
compiler correctness, all-input intrinsic refinement, R3/R7 storage acceptance,
and self-hosting remain unproved. Operator sugar and F32 need their own scoped
acceptance work.
