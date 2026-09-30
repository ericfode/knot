# Knot compiler contracts — enum and fielded Wasm

The default Wasm contract remains `knot-enum-1`. The checker and independent
evaluator additionally implement `knot-structural-terms-1`, specified in
[the field contract](../research/compiler-fields/SPEC.md). That extension accepts
constructor arguments and pattern matrices, validates quantities and ordered
matching, and evaluates finite live-field trees. It does not provide owned
runtime storage. The default emitter rejects every fielded book after body
checking. The separately selected `knot-fields-wasm-1` profile below lowers those
checked books to a bounded bump arena. Owned-storage reclamation (R3/R7) remains
unmet; this increment does not qualify either runtime requirement.
The [decreasing-call contract](../tests/compiler-descent/SPEC.md) implements the
pinned seed's rule for supported monomorphic terms. Live self-calls compare
arguments lexicographically against match-refined parameters, skipping erased
columns. Constructor fields compare componentwise; a strict subterm also
establishes descent. Local aliases retain their initializer for comparison only.
A fully checked nondecreasing self-call reports `Invalid check recursive-call`;
dead calls need no decrease. Forward and mutual calls retain their existing
classification. The [pattern-matrix gate](../tests/compiler-nest/SPEC.md) executes
nested-pattern recursion in `knot-fields-wasm-1`. Structured host arguments remain
unsupported. The original first-parameter corpus remains a regression gate.
References to nullary-only checking below describe the retained enum subprofile.

This is the first executable path toward S1, not the complete S1 stage or a
self-hosted compiler. The implementation is Bend 2, built by Bend 2.0.29 at
`574b6d39a235b539eb19a5c532993a0abb3d11ad`. The same revision's kernel interpreter
is the behavioral reference. The implementation may import its Base; accepted
programs do not import Base or any other module.

## Accepted language

The retained enum profile accepts ASCII Bend source with LF line endings, spaces, `#` comments,
and indentation. Identifiers use letters/underscore followed by letters,
digits, underscores or dots. Keywords cannot be identifiers.

- Named, possibly empty, monomorphic `type T is Type:` and `type T is Data:`
  declarations containing nullary constructors such as `Off{}` and `On{}`.
- Top-level functions with explicit parameter and result types. A parameter
  has quantity erased (`-x`), affine (`x`), or reusable (`+x`). A reusable
  parameter must have a `Data` type. Dropping an affine parameter is allowed.
- Variables, constructor applications and fully applied top-level calls.
  Datatypes and constructor expressions may precede their declarations.
  Constructor patterns resolve at their source declaration event. A function must be
  defined before its live calls, following the pinned reference's declaration
  events. Forward live calls are invalid even when the graph is acyclic.
- Sequential local bindings `x = value`, `+x = value`, and `-x = value`.
  An optional `: T` annotation supplies the initializer's expected type.
  Constructor initializers require it, as in `x : Flag = On{}`; an unannotated
  variable or call can infer its type from an already known declaration.
  A binding is visible in the remainder of its body, not in its own initializer.
  Shadowing creates a new binding. Repeated parameter names also shadow earlier
  parameters, as in the pinned seed. Reusable bindings require `Data` values.
- A body may end in a match on function parameters or bound fields. Rows contain
  constructor, wildcard or variable patterns, with nested constructor fields in
  the structural profile. The first matching row wins, including duplicate rows;
  every constructor combination must be covered. Empty datatypes admit zero
  rows. Unreachable bodies are discarded before checking, but source patterns
  still constrain their columns and undergo name/arity validation.
  Computed and local-binding scrutinees remain invalid at the pinned seed.
  Constructor columns follow binder order and close earlier parameters.
  Variable-only columns leave that frontier open, so they may be reordered.
  Local bindings close the outer frontier; matched constructors cannot be
  inspected again. A matched parent is rebuilt from its known constructor and
  field identities. Rebuilding an affine parent spends its remaining live field
  obligations. Row aliases share those identities, even through nested patterns;
  later row binders shadow earlier names without capturing other columns.
- In the enum subprofile, live calls form an acyclic graph. Erased arguments may
  contain forward or self-calls; no live enum self-call can meet the descent rule.
  Every function is checked, including unused
  definitions. No executable artifact is emitted until the entire book passes.

Constructor names must be unique across the book in this first profile.
A zero-constructor datatype permits an exhaustive zero-row match and has no
valid host ordinal. Repeated constructor declarations, including across
datatypes, are invalid. Top-level type/function names share a namespace.
Free names, type/arity mismatches, missing arms,
affine reuse and live inspection of erased values are invalid.

Duplicate constructor rows are accepted. The first matching row supplies the
body; shadowed row bodies are discarded before checking. Nested patterns
expand into single-constructor decisions; field binders retain their lexical
identities, declared quantities and reconstruction obligations.

Generic/dependent types, imports, literals, closures, destructuring local
bindings, laws, templates, foreign code and effects remain explicitly
unsupported. The default enum emitter rejects fielded books after checking;
selecting the fields profile enables their checked runtime representation.
Supported live self-calls that fail the decreasing-call rule are Invalid.
A recognized unsupported form makes no claim about its remaining contents.

The parser recognizes these out-of-profile prefixes before applying the narrower
enum grammar. Each reports exit 3 with a stable `Unsupported` phase/code:

| Recognized form | Phase | Code |
| --- | --- | --- |
| `type Name<...` generic datatype header | `parse` | `generic-datatype` |
| `~name:` in a function parameter list | `parse` | `template-binder` |
| Parsed constructor pattern followed by `=` in a body | `parse` | `destructuring-binding` |
| `import ./...` or `import 0x.../...` | `parse` | `import` |
| Dotted variable pattern needing the modules scope rule | `parse` | `dotted-binder` |

Recognition stops at that prefix; it neither validates the suffix nor loads a
module. Malformed supported syntax still reports `Invalid`. The reviewed
[classification fixtures](../tests/subsets/classification-cases.json) pair six
seed-accepted programs (local and hash imports separately) with six nearby
syntax errors, fixing complete diagnostics including locations. The hash
fixture uses a frozen local cache; it does not claim a published package.
Five checked prefix laws quantify over source locations and unconsumed suffixes;
a separate law pins ordered multi-scrutinee parsing. These are classification laws, not a parser soundness theorem or feature support.

The parser and catalog now have a separate
[structural declaration checkpoint](../research/compiler-structural/SPEC.md).
They preserve ordered field signatures and validate their declared kinds and
quantities, including forward/mutual type references. Structural term checking
now follows declaration checking. Selecting the default enum emission profile
still reports `Unsupported check constructor-fields` for a checked fielded book.
Known invalid declarations or bodies can report Invalid first. Declaration
inspection itself does not imply execution or a structured host ABI.

The parse CLI also validates constructor-pattern declaration events and arity,
including patterns in unreachable rows. The checked pipeline retains its frozen
check-phase diagnostics for those restrictions. Detached constructor braces in
patterns are `Invalid parse detached-brace`; constructor expressions may still
precede their declarations. `_` never denotes a source value.

Until the later pattern-matrix and Default-core increments are integrated,
an empty variable column reports `Unsupported check empty-datatype`. A
constructor-expanded default that repeats or inspects its residual affine
identity reports `Unsupported check residual-alias`. The bounded guard follows
source names through lexical shadowing and uses maximum usage across alternatives;
single uses and explicit reusable promotion keep their accepted behavior. This is
a conservative refusal, not a full implementation of the seed's residual region.
Unlocated helper exhaustion escaping from a function receives that function's
source boundary; helper algebra laws retain their location-free outcomes.

## Binding and quantity semantics

Resolved occurrences use lexical levels within a function environment, never
display-name lookup. New bindings append a level; shadowing resolves to the
nearest binding. Levels in mutually exclusive branch scopes may be reused.
Sequential expressions add affine usage; alternatives take the maximum. Match
scrutinee usage is sequenced before branch usage after constructor refinement.
Erased contexts still undergo
scope and type checking but do not consume runtime values. Erased arguments and
initializers are absent from emitted execution. A call consumes each live
argument once, including transfer of a Data value to a reusable callee binder.

The evaluator interprets checked terms with explicit environments and call
frames. It does not run emitted instructions or derive expected results from
Wasm. The emitter lowers checked terms to calls, locals and conditional branches;
it must not replace whole functions by evaluator results.

## Wasm and host contract

Emit an actual Wasm binary with version 1 header and only MVP numeric/control
instructions. Enum values are i32 constructor ordinals in declaration order.
Use type, function, export and code sections. No imports, linear memory, tables,
GC, SIMD, threads or WASI are required for this profile. Erased parameters are
omitted from the external function signature; live arguments/results are i32.
Host observations only supply ordinals belonging to each declared parameter
type and decode results through the declared result type. Out-of-domain host
arguments are outside this ABI, not valid source programs.

The declared first host is Node 22.22.3 on macOS arm64, using its native
`WebAssembly.validate`, `WebAssembly.compile` and `WebAssembly.instantiate`.
The host adapter supplies files and invokes exports; it contains no source
language semantics. GPU source lowering and full self-hosting are later gates.

The binary format follows the official WebAssembly specifications for
[modules](https://webassembly.github.io/spec/core/binary/modules.html),
[instructions](https://webassembly.github.io/spec/core/binary/instructions.html)
and [integer encoding](https://webassembly.github.io/spec/core/binary/values.html),
consulted 2026-09-26. Only the stated MVP subset is used.

## Fielded Wasm profile: `knot-fields-wasm-1`

This profile accepts completely checked books from
`knot-structural-terms-1` and lexicographic structural recursion: monomorphic constructor fields, nested patterns,
parent reconstruction, `Type`/`Data` quantities and erased fields. It adds no
checker bypass. Imports and forms beyond the stated structural and matrix
contracts remain unsupported. `wasm.emit_profile(Fields{},book,depth,bytes)` requires
a checked book, as does the original `wasm.emit` entry. `emit` still selects
`Enum{}`; `check.enum_profile` and its existing capability law remain unchanged.

An enum-only datatype uses i32 ordinals, even inside a fielded book. If any
constructor of a datatype declares fields (including only erased fields), every
value of that datatype is an i32 cell address. The cell contains `[tag][live
field 0]...[live field k-1]`, with one 4-byte word per entry. Fields retain
declaration order; erased fields take no slot and their arguments never run.
Nullary constructors of such a datatype allocate a tag-only cell. Field values
are either enum ordinals or cell addresses according to their declared type.
Constructor arguments are evaluated left to right into fresh locals before
allocation; matching loads the tag and then its arm's live fields into locals.
Checked arms are exhaustive, so their field signatures identify the scrutinee
representation independently of the match's result type.

A module containing a fielded datatype adds memory and global sections:
`[1,3,5,6,7,10]`. Memory has exactly one page (65,536 bytes, min=max=1). The
mutable i32 bump starts at zero; zero is a valid cell address. The appended,
unexported allocator checks `size > 65536 - bump` before advancing the bump.
That guard traps with `unreachable`. Empty matches also emit `unreachable`,
but their scrutinee has no domain-valid runtime value. An allocation ending at
65,536 succeeds; an allocation beyond the remaining space traps before writing.
Cells stay immutable after initialization, so reusable Data may share addresses.
There is no memory growth, free, reset, reclamation, generation tracking or
storage transfer. Dropped values retain their cells until the instance is
discarded. This is bounded allocation, not the owning-store runtime from R3/R7.

The profile adds `global.get`, `global.set`, `i32.load`, `i32.store`, `i32.add`,
`i32.sub`, `i32.gt_u`, and `unreachable` to the enum instruction whitelist.
There are no imports, tables, memory exports, GC, SIMD, threads or GPU execution.
When the book has no fielded constructors, no allocator, memory or global is
emitted; the 25 enum corpus modules remain byte-identical, in both profiles and
both compiler lanes, with sections `[1,3,7,10]`.

All original function indices and exports are retained; only the allocator is
appended. **Host precondition:** invoke only functions whose live parameters and
result have enum-only datatypes, supplying each parameter's valid constructor
ordinal. Functions taking or returning cells are for compiled callers. The host
adapter does not carry source signatures and cannot enforce this precondition;
an integer that happens to lie in 0..255 is not evidence that a pointer is a
valid ordinal. Structured host arguments and pointer observations are outside
this ABI.

The explicit driver is `tests/compiler-fields-wasm/compile.bend`, built with the
pinned seed to a native executable or Bun JS. It uses the same checked loader,
budgets, byte writer and failure policy as `src/compile-cli.bend`, but selects
`Fields{}`. Its command is `compile source output [characters parser-depth
checker-depth emitter-depth output-bytes]`. Keeping this entry separate preserves
the existing enum compiler's rejection assertions. Unifying profile selection
in the public compiler CLI is a subsequent driver increment.

Run its output with `node scripts/run-wasm.mjs --profile=knot-fields-wasm-1 module
export [live-ordinals...]`. Profile selection asserts that the module came from
the corresponding checked Knot emitter; it is not a verifier for arbitrary
Wasm. During export invocation, a call-stack `RangeError` reports
`Exhausted<TAB>wasm<TAB>call-stack` (exit 4). For domain-valid calls in the fields profile, the arena's
`unreachable` reports `Exhausted<TAB>wasm<TAB>arena-overflow` (exit 4). Other traps,
invalid modules, file failures, unknown exports and malformed host arguments
remain HostFailure (exit 5). Node startup failures occur before this adapter can
classify them; the stack test pairs a shallow control with an acyclic wide-frame
fixture under identical Node flags. No stack overflow is evidence of Invalid.

The gate is `BEND_NO_TELEMETRY=1 python3 tests/compiler-fields-wasm/check.py`.
Its frozen seed observations, enum hashes, five checked helper/erasure laws,
instruction whitelist, persistent-instance arena boundaries and four
type-correct semantic mutants are independent evidence, not a general compiler
correctness or memory-refinement theorem. See its [report and limits](../tests/compiler-fields-wasm/README.md).

## Outcomes and budgets

Return stable phase/code diagnostics with source offsets where available:
`Invalid`, `Unsupported`, `Exhausted`, `HostFailure`, or `InternalFailure`.
`Built` means a complete checked module has been emitted. The evaluator has a
separate result and exhaustion outcome. A host timeout is exhaustion and cannot
be relabeled as an invalid program. Stale output files cannot count as emission.

The executable [contract manifest](CONTRACT.json) fixes source, parser, checker,
emitter-depth, evaluator-transition and output-byte budgets. Exhaustion is
inconclusive. The compiler and evaluator have separate commands and outcomes;
emission never calls the evaluator.

## Current checker bounds

`check-cli.bend path [character-budget checker-depth]` defaults to 65,536 source
characters and depth 512; parser depth is 512. Both frontend and checker depth
are recursion-depth bounds, not total work counters. Overrides permit checker
depth 0 through 4,096 and source budgets 0 through 65,536. The catalog allows
256 types, 256 functions, 256 constructors per type, 256 fields per constructor and 256 parameters per
function; lexical levels are limited to 4,096 per branch scope. Exceeding any
of these bounds is exhaustion. Each expanded source match has 4096 matrix steps; constructor splits divide
the remaining quota among their branches. This conservative work cap bounds
pattern-tree expansion separately from checker depth. Catalog passes and
environment/set scans are structural list traversals bounded by the catalog
limits and source cap. Lookup
and affine-set merging are deliberately simple linear/quadratic algorithms.
Self-call comparison gives each live column a total transition quota equal to
the available checker depth. A single machine spends that quota on alias heads,
componentwise fields and fallback search. Constructor children remain deferred;
comparison does not expand shared aliases into trees in advance. Returning
through frames costs no extra transition, and every frame was pushed by a
charged transition. Per-transition list scans are bounded by the catalog/scope
limits above. Aliases and branch refinements resolve without evaluating
applications. Exhaustion remains separate from `GT` and cannot establish
nondecrease. No performance claim or general checker-soundness proof is made.

The checker CLI prints a resolved-term observation and emits no executable.
Its `Checked` result is not `Built`. The separate compiler/evaluator commands
below execute the rest of this profile.

## Executable compiler and evaluator

Build the Bend entries with `scripts/bend-reference src/compile-cli.bend -o
.local/compiler-wasm/compile-cli` and the corresponding `eval-cli.bend` entry.
Native and Bun-generated JS are tested seed hosts. The compiler implementation
imports pinned Base and the published ByteOutput package
`0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend`; accepted source imports nothing.

`compile-cli source output [characters parser-depth checker-depth emitter-depth
output-bytes]` writes actual Wasm bytes with Bend's File.write_bytes. Defaults
are 65,536 / 512 / 512 / 4,096 / 65,536; depth overrides stop at 4,096 and output
bytes at 1,048,576. It emits all top-level functions, one signature per function,
compact live parameters, local slots and typed conditional branches. It never
uses evaluator results to replace function bodies. The published byte builder
checks lengths before addition. Section sizes and indexes use unsigned LEB128;
nonnegative enum constants use signed LEB128 with a 6-bit final group.

`eval-cli source function transition-budget [live-ordinals...]` independently
interprets checked terms with explicit environments and argument/binding frames.
Its input limits are 65,536 / 512 / 512. At most 1,048,576 transitions can be
requested; 65,536 is the normal test budget. Each source-machine step costs one
unit, including argument binding; a terminal value needs no further fuel. An
erased initializer/argument is skipped before entering its expression. The
evaluator enforces exact live arity and each parameter's constructor domain.

`scripts/run-wasm.mjs module export [live-ordinals...]` is a Node host adapter.
It uses WebAssembly.validate, compile and instantiate, rejects imports, checks
live arity and the profile-wide 0..255 ordinal range, and returns an execution
record. Supplying each ordinal from its declared enum is the caller's ABI
precondition. Tests supply domain-valid arguments from literal observations. It contains no Bend
source-language semantics and performs no code generation. `wasm2wat` is only
an independent decoder used to inspect generated modules, not an assembler or
a compilation dependency.

Checking and byte construction finish before the output file is opened. Invalid,
unsupported and exhausted compilation leaves existing output untouched and prints
no Built record. File-open/read/write failures report HostFailure; a failed write
can leave a partial file. A file left after failure cannot count as a new module.
These commands do not promise atomic replacement or crash durability.

The retained enum runtime represents only nullary enum values. Its evaluator values are
Data records used as an independent pure model; source quantities are checked
before execution. This does not establish an owning heap for general affine
resources, a parallel runtime, or source compilation to the existing GPU probe.

## Trust inventory: open proof obligations

The two general pattern-matrix lowering laws remain required under coordinator
decision D21. This branch carries checked ground instances and helper equations,
not proofs of either general statement. Nest's later proofs and rulings must be
reconciled when the coordinator integrates that increment.

| Required law | Current evidence | Status |
| --- | --- | --- |
| An irrefutable first row lowers to that row's body | `matrix-LAWS.bend::irrefutable_lowering_selects_first`, the specialization/default/selection helper laws, and the frozen first-match and wildcard fixtures | Open general obligation. Success at a fixed work quota is not guaranteed; the seed-accepted `tests/compiler-nest/controls/matrix-work.bend` exhausts the 4,096-step quota. |
| An exhaustive matrix lowers without a missing branch | `matrix-LAWS.bend::exhaustive_matrix_has_no_missing_branch` and the frozen multi-column, nested and empty-type fixtures | Open general obligation. Ground normalization does not establish arbitrary exhaustive lowering. |

The descent algebra's 23 filled laws and the differential controls are separate
evidence. They establish no general termination or compiler-refinement theorem.
The bounded review is in
[`tests/compiler-descent/LAW_REVIEW.md`](../tests/compiler-descent/LAW_REVIEW.md).

## Required evidence

Compare accepted fixtures with the pinned reference interpreter and compare
the independent Bend evaluator against actual Wasm execution. Include Flag
negation, nested branches, shadowing, forward datatypes, Data reuse, affine drop,
erased forwarding and renamed equivalents. Pair quantity/type/match negatives
with nearby accepted controls. Exercise each budget and unsupported feature
class. Kill parseable/type-correct semantic mutants with unchanged expectations.

Record the actual proof boundary: focused algebraic laws, concrete fixture
checks and runtime agreement are distinct evidence. Do not claim a general
compiler-correctness or checker-soundness theorem. Final receipts must identify
source hashes, seed hashes, commands, generated modules, tool versions, Perch
coverage/adjudications and remaining limitations.
