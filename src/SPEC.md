# Knot compiler contracts — enums, fields and closures

The default Wasm contract remains `knot-enum-1`. The checker and independent
evaluator additionally implement `knot-structural-terms-1`, specified in
[the field contract](../research/compiler-fields/SPEC.md). That extension accepts
constructor arguments and flat field binders, validates quantities and ordered
matching, and evaluates finite live-field trees. It does not provide owned
runtime storage. The default emitter rejects every fielded book after body
checking. The separately selected `knot-fields-wasm-1` profile below lowers those
checked books to a bounded bump arena. Owned-storage reclamation (R3/R7) remains
unmet; this increment does not qualify either runtime requirement.
The [first-parameter descent contract](../tests/compiler-recursion/SPEC.md)
adds structural self-calls to checking and evaluation: the first checked argument
must be a reference to a field of parameter 0, directly or through further
matches. Other self-calls report `Unsupported check recursive-call`; forward
and mutual calls retain their existing classification. Nested patterns and
structured host arguments remain unsupported. The closure gate additionally
qualifies those descending calls in higher-order programs under
`knot-fields-wasm-1`; the finite corpus is described below.
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

- Named, nonempty, monomorphic `type T is Type:` and `type T is Data:`
  declarations containing nullary constructors such as `Off{}` and `On{}`.
- Top-level functions with explicit parameter and result types. A parameter
  has quantity erased (`-x`), affine (`x`), or reusable (`+x`). A reusable
  parameter must have a `Data` type. Dropping an affine parameter is allowed.
- Variables, constructor applications and fully applied top-level calls.
  Datatypes/constructors may be declared after their uses as types or terms.
  Braced constructor patterns require a preceding constructor declaration,
  following the seed's parse-time declaration events. A function must be
  defined before its live calls, following the pinned reference's declaration
  events. Forward live calls are invalid even when the graph is acyclic.
- Sequential local bindings `x = value`, `+x = value`, and `-x = value`.
  An optional `: T` annotation supplies the initializer's expected type.
  Constructor initializers require it, as in `x : Flag = On{}`; an unannotated
  variable or call can infer its type from an already known declaration.
  A binding is visible in the remainder of its body, not in its own initializer.
  Shadowing creates a new binding. Repeated parameter names also shadow earlier
  parameters, as in the pinned seed. Reusable bindings require `Data` values.
- A body may end in a match on one function parameter. Every constructor of the
  scrutinee type must occur exactly once. Arms can contain bindings and nested
  matches. Constructor patterns have no fields in this profile.
  The pinned Bend parser rejects computed and local-binding scrutinees; Knot
  retains that restriction rather than accepting a different surface language.
  Matches follow parameter order: after matching a parameter, earlier parameters
  cannot be matched. A local binding closes all outer parameters to further
  matching. Already matched parameters cannot be matched again. Inside an arm,
  uses of its matched parameter become the known nullary constructor; this may
  construct several fresh values without reusing the consumed affine value.
- In the enum subprofile, live calls form an acyclic graph. Erased arguments may
  contain forward calls; no enum self-call can meet the field-descent rule.
  Every function is checked, including unused
  definitions. No executable artifact is emitted until the entire book passes.

Constructor names must be unique across the book in this first profile.
Repeated constructor declarations, including across datatypes, are invalid. Top-level type/function names share a namespace.
Free names, type/arity mismatches, missing arms,
affine reuse and live inspection of erased values are invalid.

Duplicate arms are outside this profile and report Unsupported: the pinned
reference can accept overlapping nullary patterns, choosing the first match.

Constructor fields, recursive calls, generic/dependent types, imports, literals,
closures, wildcard/multi-scrutinee patterns, laws, templates, foreign code and
effects remain explicitly unsupported. This restriction leaves recursive trees
and field-bound variables outstanding for the broader S1 stage. A recognized
unsupported form makes no claim about the validity of its remaining contents.

The parser recognizes these out-of-profile prefixes before applying the narrower
enum grammar. Each reports exit 3 with a stable `Unsupported` phase/code:

| Recognized form | Phase | Code |
| --- | --- | --- |
| `type Name<...` generic datatype header | `parse` | `generic-datatype` |
| `match a b...` with a second named scrutinee | `parse` | `match-scrutinees` |
| `~name:` in a function parameter list | `parse` | `template-binder` |
| Parsed constructor pattern followed by `=` in a body | `parse` | `destructuring-binding` |
| `import ./...` or `import 0x.../...` | `parse` | `import` |
| Out-of-profile parameter/field type atom, group, typed comparison or closed family application | `parse` | `parameter-type` |
| Out-of-profile result type atom, group, typed comparison or closed family application | `parse` | `function-result` |
| Out-of-profile binding type atom, group, typed comparison or closed family application | `parse` | `binding-type` |

Recognition stops at that prefix; it neither validates the suffix nor loads a
module. Malformed supported syntax still reports `Invalid`. The reviewed
[classification fixtures](../tests/subsets/classification-cases.json) pair six
seed-accepted programs (local and hash imports separately) with six nearby
syntax errors, fixing complete diagnostics including locations. The hash
fixture uses a frozen local cache; it does not claim a published package.
Six checked prefix laws quantify over source locations and unconsumed suffixes;
they are classification laws, not a parser soundness theorem or feature support.
The monomorphic arrow reader locates a family's closing `>` before refusing it;
an unclosed untyped `<` or the `<-` operator in a type position stays Invalid rather
than being mistaken for an unsupported family application. Parameters and
fields can be separated by whitespace or commas, as in the seed. A nonleading
template marker still stays Invalid; optional separators do not move it into
the leading-template prefix policy.

The parser and catalog now have a separate
[structural declaration checkpoint](../research/compiler-structural/SPEC.md).
They preserve ordered field signatures and validate their declared kinds and
quantities, including forward/mutual type references. Structural term checking
now follows declaration checking. Selecting the default enum emission profile
still reports `Unsupported check constructor-fields` for a checked fielded book.
Known invalid declarations or bodies can report Invalid first. Declaration
inspection itself does not imply execution or a structured host ABI.

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

This profile accepts the completely checked structural books of
`knot-structural-terms-1`: monomorphic constructor fields, flat field patterns,
parent reconstruction, `Type`/`Data` quantities and erased fields. It adds no
checker bypass. The closure extension below adds higher-order code and qualifies
its descending self-calls. Nested patterns, imports and the other unsupported
forms retain their separate boundaries. `wasm.emit_profile(Fields{},book,depth,bytes)` requires
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
That guard is the only reachable `unreachable` for valid inhabited host signatures;
the closure extension also emits an unreachable dispatcher for a function type
with no constructor sites. An allocation ending at
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

All original function indices and exports are retained. Closure dispatchers and
the allocator are appended and unexported. **Host precondition:** invoke only functions whose live parameters and
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
`Exhausted<TAB>wasm<TAB>call-stack` (exit 4). In the fields profile, the arena's
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

## Closures and higher-order code

The checker and evaluator accept monomorphic, right-associative `A -> B` types,
including parenthesized domains such as `(Flag -> Flag) -> Flag`. Function types
have kind `Type`; reusable function binders and live function fields in a `Data`
datatype are Invalid. The retained enum profile still reports
`Unsupported compile closures` for actual closure terms. Select `Fields{}` for
execution. Arrow metadata alone leaves the old enum modules byte-identical.
The two characters within `->` and `=>` must occupy adjacent source spans;
whitespace between them cannot form an arrow. Type atoms resolve in the active
lexical scope. An earlier parameter, field, lambda binder or local value that
shadows a type name makes that type occurrence `Unsupported check dependent-type`:
this profile cannot interpret local values as types. A binder is not visible in
its own annotation. This guard applies recursively to both arrow components.

Lambdas have the source shapes `x => body` and `+x => body`. They check against
an expected arrow; an unannotated lambda initializer is Invalid
`annotation-required`. A promoted binder must have a `Data` domain. The binder
shadows earlier names. `_` discards its argument without introducing or shadowing
a name. A newline may separate a lambda binder from its contiguous `=>`.
Lambda bodies can contain bindings and further lambdas; binding continuations
may follow a semicolon or newline, with independent continuation indentation.
matches in those bodies are Invalid `unmatchable-binder`, as in the seed.
Closure applications and literal lambdas used as match scrutinees are Invalid
`computed-scrutinee`.
Live calls inside a lambda still obey definition order and structural descent.

Function values may be passed, returned, held in `Type` constructors or lists,
and consumed through variable calls. Application is curried: `f(a,b)` applies
both arrows, and `g(a)(b)` observes a returned closure. Named functions can be
used as values or partially applied. Supplied partial arguments are evaluated
and saved once, in order, when forming the closure. A partial self-call must
already supply a descending first argument; delaying the call does not bypass
that rule. An erased remaining parameter requires a dependent function type
and reports `Unsupported check function-quantity` in this profile.

The core retains original datatype IDs and interns arrow types after them.
Its `Closure` term records a code identity, binder level, domain, quantity,
checked body and free-variable descriptors. `Invoke` records the arrow identity,
callee and argument. Live affine usage in a lambda body is transferred to the
construction of its closure. Building two closures over one affine value is
Invalid `affine-reuse`, even if a later chooser invokes only one. A promoted
`Data` parameter or field can be captured by several thunks. Erased expressions
remain scope/type checked and consume no affine usage; erased-only captures
retain a descriptor with quantity zero and occupy no runtime slot.

The evaluator creates an explicit captured environment. Application evaluates
the callee and then the argument, binds the argument in the captured environment, and enters the
stored body without adding a return frame. It never runs the defunctionalized
book or Wasm instructions. Closure values are internal: host function arguments
or results report HostFailure, while ordinary enum observations retain the
existing format.

Before Wasm emission, `closure.bend` replaces each used arrow type with a closure
datatype, with one constructor per lambda or eta-expansion site. Each cell is
`[dense site tag][live captures]`. Fields keep capture order and erased captures
have neither storage nor evaluation. A single apply dispatcher for that type
matches the tag, binds captures and the argument to the original lexical
levels, and runs the site's body. This is defunctionalization, with no function
pointers, indirect calls or tables. Source functions keep their original
indices; dispatchers and the allocator are hidden from exports. Even a closure
without live captures is a tag-only cell. An arrow type used by an uncalled
function may have no sites; its dispatcher is unreachable for any value a
checked source program can construct. Forged host function handles are outside
the enum-only host precondition.

Closure-containing modules use `return_call` in actual tail positions, including
match arms and let bodies, when both signatures have at most 32 live parameters.
Wider callees use `call; return`, and wider callers use ordinary body lowering.
This conservative guard avoids the pinned Node 22 arm64 Liftoff abort on wide
tail-call stack adjustments. Erased parameters do not count. Wide calls retain
value semantics but can exhaust the call stack; no constant-stack guarantee is
made for them. Calls in arguments and initializers keep `call`.
The frozen continuation probe constructs and invokes 2,048 continuations under
a reduced Node stack. This establishes that bounded execution and kills an
ordinary-call mutant; it is not an unbounded space theorem. The unchanged
65,536-byte bump arena still limits allocation and provides no reclamation.

The registry admits at most 4,096 interned types, independently of the existing
256 source datatype limit. Type inventory and type syntax have bounded traversals.
Arrow keys are pairs of resolved domain/result IDs, so lookup and interning do
not recursively print synthetic signature trees. Nominal lookup skips arrows.
Closure inventory and rewriting share the selected emitter-depth ceiling and
report Exhausted if it is insufficient. Lexical-level limits remain 4,096.
Code identity combines the source function index, source offset and eta ordinal;
Wasm constructor tags are separate dense ordinals and never encode that identity
as a signed i32 constant.

The [closure gate](../tests/compiler-closures/GATE.md) reruns all 42 immutable seed
fixtures and 292 calls before comparing native/Bun Knot evaluators and actual
Node Wasm. It records unsupported boundaries and the `generic-choose-bind`
prerequisite separately. That fixture's 19 calls remain blocked until generics
land; its expectations are unchanged. Supplemental seed-fixed erasure and deep
continuation probes, complete checked proofs and five type-correct semantic
mutants qualify the available monomorphic capability. The laws establish local
type, capture, lowering and evaluator-step equations; finite corpus agreement
is separate evidence, not a general compiler-correctness theorem.

### Trust inventory: open proof obligations

Capture-preserving defunctionalization remains an open general proof obligation:
for any checked monomorphic book and source-constructible function value,
application in the independent evaluator must agree with execution of its
lowered constructor/apply dispatcher whenever both computations stay within
their stated resource bounds. The 24 checked local equations, frozen fixtures,
semantic mutants and refresh edges are evidence for that obligation; they do
not discharge it. All existing law statements and proof domains remain required
and unchanged (campaign D21).

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
of these bounds is exhaustion. Catalog passes and environment/set scans are
structural list traversals bounded by these limits and the source cap. Lookup
and affine-set merging are deliberately simple linear/quadratic algorithms.
No performance claim or general checker-soundness proof is made.

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
