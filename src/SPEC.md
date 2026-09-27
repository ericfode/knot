# Knot compiler contracts — enum Wasm and structural checking

The Wasm contract below remains `knot-enum-1`. The checker and independent
evaluator additionally implement `knot-structural-terms-1`, specified in
[the field contract](../research/compiler-fields/SPEC.md). That extension accepts
constructor arguments and flat field binders, validates quantities and ordered
matching, and evaluates finite live-field trees. It does not provide owned
runtime storage. The emitter rejects every fielded book after body checking.
Nested patterns, recursion and structured host arguments remain unsupported.
References to nullary-only checking below describe the retained enum subprofile.

This is the first executable path toward S1, not the complete S1 stage or a
self-hosted compiler. The implementation is Bend 2, built by Bend 2.0.29 at
`574b6d39a235b539eb19a5c532993a0abb3d11ad`. The same revision's kernel interpreter
is the behavioral reference. The implementation may import its Base; accepted
programs do not import Base or any other module.

## Accepted language

The profile accepts ASCII Bend source with LF line endings, spaces, `#` comments,
and indentation. Identifiers use letters/underscore followed by letters,
digits, underscores or dots. Keywords cannot be identifiers.

- Named, nonempty, monomorphic `type T is Type:` and `type T is Data:`
  declarations containing nullary constructors such as `Off{}` and `On{}`.
- Top-level functions with explicit parameter and result types. A parameter
  has quantity erased (`-x`), affine (`x`), or reusable (`+x`). A reusable
  parameter must have a `Data` type. Dropping an affine parameter is allowed.
- Variables, constructor applications and fully applied top-level calls.
  Datatypes/constructors may be declared after their uses. A function must be
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
- Live calls form an acyclic graph. Erased arguments may contain forward calls;
  self-calls remain unsupported in any context. Every function is checked, including unused
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

The parser and catalog now have a separate
[structural declaration checkpoint](../research/compiler-structural/SPEC.md).
They preserve ordered field signatures and validate their declared kinds and
quantities, including forward/mutual type references. A fielded datatype still
reports `Unsupported check constructor-fields` before function-body checking.
Known invalid field declarations can report Invalid first. This extends
declaration inspection, not the accepted executable language or Wasm ABI.

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

The first runtime represents only nullary enum values. Its evaluator values are
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
