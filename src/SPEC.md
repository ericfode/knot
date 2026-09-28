# Knot compiler contracts — enum and fielded Wasm

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
structured host arguments remain unsupported. Recursive Wasm lowering is not
yet a qualified capability of `knot-fields-wasm-1`.
References to nullary-only checking below describe the retained enum subprofile.

This is the first executable path toward S1, not the complete S1 stage or a
self-hosted compiler. The implementation is Bend 2, built by Bend 2.0.29 at
`574b6d39a235b539eb19a5c532993a0abb3d11ad`. The same revision's kernel interpreter
is the behavioral reference. The implementation imports its Base. The original
single-file commands retain their import rejection; explicit `--bundle ROOT`
commands additionally load user modules and a checked reachable Base slice.

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
| Leading `~name:` in a function parameter list | `parse` | `template-binder` |
| Parsed constructor pattern followed by `=` (next token neither `=` nor `>`) in a body | `parse` | `destructuring-binding` |
| `Name<...` in a parameter type | `parse` | `parameter-type` |
| `Name<...` in a return type or local binding annotation | `parse` | `type-application` |
| `import ./...`, `import ../...` or `import 0x.../...` | `parse` | `import` |

Recognition stops at that prefix; it neither validates the suffix nor loads a
module. Malformed supported syntax still reports `Invalid`. The reviewed
[classification fixtures](../tests/subsets/classification-cases.json) retain six
seed-accepted programs (local and hash imports separately) and six nearby
syntax errors, and add 17 precision controls with fixed seed commands and outputs,
including malformed suffixes after recognized prefixes. All 29 cases fix complete
Knot diagnostics including locations. The hash
fixture uses a frozen local cache; it does not claim a published package.
Twelve checked classification laws quantify over source locations and unconsumed
suffixes; they are classification laws, not a parser soundness theorem or feature
support. The destructuring law excludes `==` and `=>`; both report
`Invalid parse end-of-body`. A `~` after an ordinary binder reports
`Invalid parse parameter`. An initial template binder stops recognition, so its
later binders and body are not validated. Generic parameter types retain the
existing `parameter-type` code, which also covers other unsupported parameter
type forms. Return types and binding annotations use `type-application` at `<`.
These applications are recognized even before their generic datatype declaration.

The parser and catalog now have a separate
[structural declaration checkpoint](../research/compiler-structural/SPEC.md).
They preserve ordered field signatures and validate their declared kinds and
quantities, including forward/mutual type references. Structural term checking
now follows declaration checking. Selecting the default enum emission profile
still reports `Unsupported check constructor-fields` for a checked fielded book.
Known invalid declarations or bodies can report Invalid first. Declaration
inspection itself does not imply execution or a structured host ABI.

## Imported books and pinned Base

The [module contract](../tests/compiler-modules/SPEC.md) adds these explicit
argument forms; all existing single-file forms and exit codes are retained:

```text
check-cli --bundle ROOT source
check-cli --audit-bundle ROOT source
eval-cli --bundle ROOT source function transition-budget [live-ordinals...]
compile-cli --bundle ROOT source output [characters parser-depth checker-depth emitter-depth output-bytes]
```

`ROOT` is an existing frozen package directory, standing in for `BEND_LIB`.
The loader accepts local `./`, `../` and unprefixed paths, lowercase hash paths,
and bare `import Base`. It never fetches packages. Named package pointers report
`Unsupported load named-package`. Missing imported files, cycles and invalid
alias/declaration combinations report `Invalid`; other file failures remain
`HostFailure`. Parent-relative imports in the legacy single-file parser now
report `Unsupported parse import`, correcting the former D4 misclassification.

An explicit machine suspends import headers while dependencies load. Active
paths detect back edges; completed paths suppress repeated loads in diamonds.
Paths are normalized lexically before assigning module identity. Local names
are relative to the entry directory; bundle names are relative to `ROOT`.
Aliases are file-local. Symlink and case aliases are outside this profile.
Absolute import spellings report `Unsupported load absolute-import`; mixed
absolute/relative entry and bundle roots report `Unsupported load mixed-path-roots`.

Qualification produces one ordinary ordered book. Every user declaration is
checked, including unused imported definitions. Base names become book-global
at their import event, with independent type/function and constructor namespaces.
Declaration order governs duplicates and live calls, as in the frozen seed.
The downstream checker, evaluator and emitters have no module-specific bypass.

Base is the unmodified 67,190-byte `base.bend` from the pinned seed, SHA-256
`22eea83911e2395f63594fea7c10ac0c1e5b548251681fc97cd7667e0eb7031b`.
The loader verifies this digest in Bend before inventorying 466 declarations.
Only the dependency closure reachable from all user declarations is parsed,
checked and lowered. A required Base form outside the current language reports
its specific `Unsupported` reason. `--audit-bundle` first checks the entire
combined book, then prints the Base pin, loaded paths, checked Base declarations
and their exact unchecked complement. This is an explicit D2 trust inventory,
not whole-Base acceptance or proof of unchecked declarations.

Loading is bounded by 1,024 machine transitions and the existing per-file
character/parser limits. The character cap applies before import-header removal.
Base reads are capped at 131,072 ASCII bytes and constrained by the exact digest.
Base dependency traversal has a finite work bound. User and traversal bound
failures report `Exhausted`; Base identity/encoding failures report
`HostFailure load base-pin`. The default Wasm emitter remains the enum profile. No additional
foreign effects, fielded Wasm support or recursive Wasm support are introduced.

The [module gate](../tests/compiler-modules/README.md) compares frozen seed
expectations with native/Bun checking, evaluation and emittable Wasm. Four proof
entries check 68 path, scope, loader-transition, Base-selection and digest-boundary
laws. These are helper/transition laws; whole-graph order independence and
compiler correctness are not proved.

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

This profile accepts the same completely checked acyclic books as
`knot-structural-terms-1`: monomorphic constructor fields, flat field patterns,
parent reconstruction, `Type`/`Data` quantities and erased fields. It adds no
checker bypass. Recursion, nested patterns, imports and the other unsupported
forms remain unsupported. `wasm.emit_profile(Fields{},book,depth,bytes)` requires
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
That guard contains the profile's sole `unreachable`. An allocation ending at
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
`0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend`. Source imports require the explicit
module command forms above.

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
