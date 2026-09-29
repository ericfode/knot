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
The [first-parameter descent contract](../tests/compiler-recursion/SPEC.md)
adds structural self-calls to checking and evaluation: the first checked argument
must be a reference to a field of parameter 0, directly or through further
matches, or a rebuilt value denoting such a field: the level's refinement,
unfolded, with the same types, tags and field levels in order. This rebuilt
form supersedes two sentences of the linked contract, which say that
reconstructed constructors, and reconstruction of a strict descendant, never
qualify; `src/CONTRACT.json` `structural_recursion.rule` is authoritative, and
the linked contract's amendment is left to the coordinator (it belongs to
another increment). Other self-calls report `Unsupported check recursive-call`; forward
and mutual calls retain their existing classification. The
[pattern-matrix gate](../tests/compiler-nest/SPEC.md) executes nested-pattern
structural recursion in `knot-fields-wasm-1`. Structured host arguments remain
unsupported. Its two seed-rejected recursion fixtures retain conservative
Unsupported outcomes and are explicitly unmet.
References to nullary-only checking below describe the retained enum subprofile.

This is the first executable path toward S1, not the complete S1 stage or a
self-hosted compiler. The implementation is Bend 2, built by Bend 2.0.29 at
`574b6d39a235b539eb19a5c532993a0abb3d11ad`. The same revision's kernel interpreter
is the behavioral reference. The implementation imports its Base. The original
single-file commands retain their import rejection; explicit `--bundle ROOT`
commands additionally load user modules and a checked reachable Base slice.

## Accepted language

The retained enum profile accepts ASCII Bend source with LF line endings, spaces, `#` comments,
and indentation. A name is words joined by single dots, as the pinned seed reads one: each
word is a letter or underscore followed by letters, digits or underscores. Keywords cannot be
names. A run of name characters that starts like a name and is not one (`x.`, `a..b`, `A.1`)
is `Invalid lex name`, in every position, before any structure is read.

- Named, possibly empty, monomorphic `type T is Type:` and `type T is Data:`
  declarations containing nullary constructors such as `Off{}` and `On{}`.
- Top-level functions with explicit parameter and result types. A parameter
  has quantity erased (`-x`), affine (`x`), or reusable (`+x`). A reusable
  parameter must have a `Data` type. Dropping an affine parameter is allowed.
  The return arrow is `->`: split into `-` and `>` it reports `Invalid parse
  function-result`, as the seed rejects it.
- Variables, constructor applications and fully applied top-level calls.
  Datatypes and constructor expressions may precede their declarations.
  Constructor patterns resolve at their source declaration event. A function must be
  defined before its live calls, following the pinned reference's declaration
  events. Forward live calls are invalid even when the graph is acyclic.
- Sequential local bindings `x = value`, `+x = value`, and `-x = value`.
  An optional `: T` annotation supplies the initializer's expected type.
  Constructor initializers require it, as in `x : Flag = On{}`, and so does a
  binder that a match has refined to a constructor: in a positive branch the
  seed substitutes the binder by its constructor term, which it cannot infer,
  so an unannotated `v = z` there reports `Invalid check annotation-required`,
  through an alias, a nested field level or an enclosing match, in every let
  form (`v =`, `+v =`, `-v =`). An unannotated variable or call can infer its
  type from an already known declaration: a residual or default-row binder
  (the seed types it `Flag<> - Off{}`), a field never split, a later parameter
  and a call on a rebuilt binder.
  After another statement a marker touches its name: the seed reads `+ u` there
  as an operator on the previous value, so it reports `Invalid parse
  detached-marker`. First in a body, and in a parameter list, a marker may be
  spaced.
  A binding is visible in the remainder of its body, not in its own initializer.
  Shadowing creates a new binding. Repeated parameter names also shadow earlier
  parameters, as in the pinned seed. Reusable bindings require `Data` values.
- A body may end in a match on function parameters or bound fields.
  Scrutinees and row patterns may be separated by spaces or commas, and a
  match or case header continues across lines up to its colon. In patterns
  and bodies a constructor's `{` touches its name, as in `On{}`. A space,
  comment or line break between them reports `Invalid parse detached-brace`,
  as the seed rejects it; a joined header keeps each token's offset, so its
  line breaks never bridge that gap. After a term in a row, a `+` opens another
  column only where it touches its binder (`a +b`); the seed reads `a + b` as
  one operator term, so the row ends at the `+` (`Invalid parse expected-:`). A
  `+` that starts a row or follows a comma stays a promotion, spaced or not.
  Spaces inside the braces, before a
  call's `(` and in a type declaration's `Off {}` remain accepted. Rows contain
  constructor, wildcard or variable patterns, with nested constructor fields in
  the structural profile. The first matching row wins, including duplicate rows;
  every constructor combination must be covered. Empty datatypes admit zero
  rows. Bodies shadowed at the same leaf are discarded, but source patterns
  still constrain their columns and undergo name/arity validation. Variable
  defaults remain checked even past the last constructor, with a live binding
  at the emptied type. A missing arm is accepted only as dead code: some live
  binder already in context, before the scrutinee in match order, has an empty
  constructor set (an emptied residual or a zero-constructor datatype). This
  never bypasses the checking of a selected body. Pattern binders and live let
  binders are single words; a dotted one repeats a parameter of the same function
  and is otherwise invalid (see Binding and quantity semantics), while an erased
  let's name is a name, however it is spelled.
  `_` is anonymous in row and
  field positions; referring to it reports `Invalid check free-name`. Names
  such as `_x` remain ordinary binders.
  All-variable columns on the latest local binder are aliases without
  inspection. Constructor inspection of local binders and computed scrutinees
  remain invalid at the pinned seed. A `+` row makes a lambda-case binder (a
  parameter or field) reusable together with every alias of its level; a let
  binder and its aliases keep the let's declared quantity under any row, so a
  second use of a `+` alias of an affine let is affine reuse. A `+` mark, on a
  row or a field binder or inherited from a promoted parent, may raise a
  binder past its type's kind while it waits on the match frontier. As in the
  seed, the kind is judged only where the frontier binds the binder: when it
  leaves the frontier undestructured, ahead of a later matched binder (a flat
  match, a matrix split or a zero-row match), or at a body that is not a match
  (a let included). A promoted `Type`-kind binder that is destructured first is
  never bound; its fields carry the promoted quantity and face the same rule.
  A binder that the frontier binds at a `Type` kind reports `Invalid check
  reusable-type`.
  Constructor columns follow binder order and close earlier parameters.
  Variable-only columns leave that frontier open, so they may be reordered.
  Local bindings close the outer frontier; matched constructors cannot be
  inspected again. A matched parent is rebuilt from its known constructor and
  field identities. Rebuilding an affine parent spends its remaining live field
  obligations. Row aliases share those identities, even through nested patterns;
  later row binders shadow earlier names without capturing other columns.
- In the enum subprofile, live calls form an acyclic graph. Erased arguments may
  contain forward calls; no enum self-call can meet the field-descent rule.
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
identities, declared quantities and reconstruction obligations. Each constructor
splits a positive matrix from its negative remainder. The negative branch keeps
the scrutinee live and unrefined; only its available constructor set narrows.
A later source match on that residual binding currently reports
`Unsupported check default-scrutinee`. Internal binary remainder processing is
supported. `src/lowering-LAWS.bend::irrefutable_first_row_selected` proves
that every successful lowering of a matrix whose first row is irrefutable
selects that row's body at every leaf. The general exhaustive-lowering theorem
remains unmet; `exhaustive_matrix_witness` is a checked ground normalization.

Generic/dependent types, imports, literals, closures, destructuring local
bindings, laws, templates, foreign code and effects remain explicitly
unsupported. The default enum emitter rejects fielded books after checking;
selecting the fields profile enables their checked runtime representation.
Self-calls beyond the first-parameter field-descent rule, including its rebuilt
descendants, remain Unsupported.
A recognized unsupported form makes no claim about its remaining contents.

The parser recognizes these out-of-profile prefixes before applying the narrower
enum grammar. Each reports exit 3 with a stable `Unsupported` phase/code:

| Recognized form | Phase | Code |
| --- | --- | --- |
| `type Name<...` generic datatype header | `parse` | `generic-datatype` |
| Leading `~name:` in a function parameter list | `parse` | `template-binder` |
| Parsed constructor pattern followed by `=` (next token neither `=` nor `>`) in a body | `parse` | `destructuring-binding` |
| `Name<...` in a parameter type | `parse` | `parameter-type` |
| `Name<...` in a return type or local binding annotation | `parse` | `type-application` |
| `import ./...`, `import ../...` or `import 0x.../...` | `parse` | `import` |
| A second `case` arm on the line of an arm's body | `parse` | `same-line-arm` |
| A line break in a let before its `=` or between its marker and name | `parse` | `line-break` |
| A name (or in a pattern a marking `+`) after an argument, without a comma | `parse` | `argument-whitespace` |
| A promotion of a promotion (`++y`, `+ +y`) | `parse` | `repeated-promotion` |

The seed reads arguments separated by whitespace alone as arguments, a second arm on
an arm's line as the next arm, and a line break before a let's `=` or between its marker
and its name as whitespace; Knot takes a comma between arguments and ends a let and an arm
body at a line break, so these forms are unsupported, never invalid. Layout elsewhere follows
the seed's term reader (see Binding and quantity semantics); an unindented def body (the
frontend gate pins it Invalid, though the seed accepts it) and an untyped let split before its
`=` keep open D4 gaps. An arm body that starts with `case` or `def` at or below its `case` column
is `Invalid parse body-indentation`. Recognition stops at that prefix; it neither validates
the suffix nor loads a module. Malformed supported syntax still reports `Invalid`. The reviewed
[classification fixtures](../tests/subsets/classification-cases.json) retain six
seed-accepted programs (local and hash imports separately) and six nearby
syntax errors, and add 17 precision controls with fixed seed commands and outputs,
including malformed suffixes after recognized prefixes. All 29 cases fix complete
Knot diagnostics including locations. The hash
fixture uses a frozen local cache; it does not claim a published package.
Eleven checked classification laws quantify over source locations and unconsumed
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
Aliases are file-local. A minimal native/Bun host query verifies exact directory
entry spelling and rejects symlink components before user-module reads. Entry
and bundle roots are queried before lexical normalization. Symlink and case
aliases report `Unsupported load path-identity`; canonical identity support
remains a later IO ABI capability. Host query failures stay `HostFailure`.
Absolute import spellings report `Unsupported load absolute-import`; mixed
absolute/relative entry and bundle roots report `Unsupported load mixed-path-roots`.

Qualification produces one ordinary ordered book. Every user declaration is
checked, including unused imported definitions. Base names become book-global
at their import event, with independent type/function and constructor namespaces.
Declaration order governs duplicates and live calls, as in the frozen seed.
Fresh declarations check both bare and qualified names. Installing Base rejects
same-category collisions with user names already loaded; Base selection never
lets a user declaration shadow a Base dependency. Pattern binders, including
reusable binders, are resolved against the full constructor inventory before
qualification, independently of Base reachability.
The downstream checker, evaluator and emitters have no module-specific bypass.

Base is the unmodified 67,190-byte `base.bend` from the pinned seed, SHA-256
`22eea83911e2395f63594fea7c10ac0c1e5b548251681fc97cd7667e0eb7031b`.
The loader verifies this digest in Bend before inventorying 466 declarations.
The dependency closure reachable from all user declarations is selected.
Ordinary bodies are parsed and checked; the literals extension below
distinguishes its closed intrinsic registry from those source-checked bodies.
A required Base form outside the current language reports its specific
`Unsupported` reason. `--audit-bundle` first checks the combined book, then
prints the Base pin, loaded paths, checked and intrinsic Base declarations
and their exact unchecked complement. This is an explicit D2 trust inventory,
not whole-Base acceptance or proof of unchecked declarations.

Loading is bounded by 1,024 machine transitions and the existing per-file
character/parser limits. The character cap applies before import-header removal.
Base reads are capped at 131,072 ASCII bytes and constrained by the exact digest.
Base dependency traversal has a finite work bound. User and traversal bound
failures report `Exhausted`; Base identity/encoding failures report
`HostFailure load base-pin`. The host identity query adds one trusted foreign
effect; user foreign definitions remain Unsupported. Books without installed
primitive types retain the default enum profile; the separate literals profile
below supplies its own fielded and recursive execution path.

The [module gate](../tests/compiler-modules/README.md) compares frozen seed
expectations with native/Bun checking, evaluation and emittable Wasm. Four proof
entries check 81 path, scope, loader-transition, Base-selection and digest-boundary
laws. These are helper/transition laws; whole-graph order independence and
compiler correctness are not proved.

## Binding and quantity semantics

A pattern or let binder names one value. The seed reads a dotted name as a reference to a
global, so a dotted binder is `Invalid parse pattern-binder` (`binding-name` for a let)
unless a parameter of the same function binds that exact name, which the binder then repeats;
the parser checks this for the single-file and the bundle entry alike. A constructor is no
binder once it is registered, and the seed registers constructors in source order: a pattern
or let binder that names a constructor of Base, of an import or of the book's own earlier
declarations is `Invalid check constructor-pattern-binder`, while one may name a constructor
declared later, as a parameter, a function or a type may. Qualification orders registration
for a `--bundle` book. For a single file the parser's `registered` judges each body against
the constructors declared before it, and the driver runs it before checking; the checker
repeats the source-order test for field and row binders (`G.constructor_before`), which
agrees with it on a single file.

Layout follows the seed's term reader, which skips line breaks between a term's tokens. A line
break may follow `case`, `match`, a let's `=` and an offset's `+`, may precede the `:` that
closes a case pattern or a match scrutinee, and may stand around any item of a `(..)` or
`{..}` list: arguments, constructor values and patterns, parameters and constructor fields.
A newline still ends a term body and a let's value. The seed checks no body column: an arm body
may start anywhere, left of its `case` or in column 0, and a let's next line may stand in any
column. A match takes only cases right of both its own keyword and the `case` whose body holds
it, so a match in a dedented body leaves the enclosing match's cases alone; the seed reads such
a match with no rows. Known imprecisions, each Invalid where the seed accepts: a function body's
first line must leave column 0 (`Invalid parse body-indentation`, pinned by the frontend
gate); a function body's match must put its cases right of `match`; a line break inside a
parameter, in a function header outside its parentheses, after a promotion's `+` or before a
let's `=` or `:`; and a list item without its comma (`Invalid parse argument-separator`).

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
instructions from the eight-operation whitelist in `CONTRACT.json`.
An empty case emits `i32.const 0`; no domain-valid call reaches that branch.
Enum values are i32 constructor ordinals in declaration order.
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
`knot-structural-terms-1` and first-parameter structural recursion: monomorphic constructor fields, nested patterns,
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
That guard is the only `unreachable` in the profile. Empty matches emit
`i32.const 0` and have no domain-valid execution. An allocation ending at
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
of these bounds is exhaustion. Each expanded source match has 4096 matrix
visits, including leaves and empty remainders. `Expansion` returns the unused
counter from each positive branch to its negative branch. The counter is never
divided; the bound covers total expansion separately from recursion depth. Catalog passes and
environment/set scans are structural list traversals bounded by the catalog
limits and source cap. Lookup
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

## Trust inventory: open proof obligations

Two general pattern-matrix lowering laws stay required and are never weakened
or dropped (coordinator decision D21). Until they are proved, they are open
obligations in this trust inventory; the pattern-matrix profile rests on the
evidence named here, not on a proof.

| Law | Status | Witnessed by |
| --- | --- | --- |
| Irrefutable first row: a matrix whose first row is irrefutable lowers to that row's body | Unproved general law in its total form, which includes that the lowering succeeds. Its partial-correctness part is proved: `src/lowering-LAWS.bend::irrefutable_first_row_selected` shows that every *successful* `M.expand` selects the body at every leaf. The total form is **false at the implemented quota**: the frozen control `tests/compiler-nest/controls/matrix-work.bend` (13 columns, a first row of 13 `_` with body `On{}`, which the seed evaluates to `On{}`) reports `Exhausted check budget`, because expansion splits on a constructor head in any row even when the first row is irrefutable (`T(n+1)=2+2T(n)`, 24,574 visits against 4,096). That `Exhausted` is Knot's cost model applied to a seed-accepted program, a resource limit under D4. The total obligation holds only relative to sufficient work, and stays undischargeable as stated until expansion selects an irrefutable first row without splitting, which changes that frozen control and needs coordinator review | The ground-instance laws `irrefutable_lowering_witness` and `irrefutable_first_row_witness`, the helper laws `first_row_selected`, `irrefutable_specialization` and `irrefutable_default`, the `first-match-*`, `wildcard-default`, `unreachable-after-wildcard` and `variable-*` fixtures, and the 3,000-program seed fuzz |
| Exhaustive matrix: an exhaustive matrix lowers to a tree with no missing branch | Unproved general law | The ground-instance law `exhaustive_matrix_witness`, the remainder helper laws (`remainder_omits_split`, `remainder_keeps_other`, `remainder_drops_split_rows`, `irrefutable_remainder`), the `multi-*`, `nested-*`, `rec-*-nested` and `empty-*` fixtures, and the 3,000-program seed fuzz |

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


## Primitives and literals: `knot-literals-wasm-1`

The `--bundle` path accepts the unchanged 40-book literals freeze plus the
separately frozen bootstrap-helper fixture. See
[`tests/compiler-literals/README.md`](../tests/compiler-literals/README.md) for
the complete representation, bounds, evidence and remaining obligations.
Decimal U32 and Nat literals reject overflow. Escaped Char/String payloads are
lists of U32 codes: 1–8 hex digits, NUL, surrogates and codes above U+10FFFF are
preserved. Escaped surrogate pairs remain two Chars. Only `\u{` and `\U{` open
a code point, as the seed's `u{...}` match does; any other escape before `{`
(`"\n{"`) is that escape followed by a brace. Operator sugar, F32 and
raw non-ASCII quoted text report the exact frozen Unsupported prefixes.

The first-match matrix lowers Nat literals/offsets through Zero/Succ and String
patterns through SNil/SCon. U32/Char literal patterns require a default. Each
path's first leaf is live there and the others are dead. Every leaf is
checked, all live leaves before any dead one; the seed checks a body only
where a path selects its row, so a dead leaf's failure is
`Unsupported check dead-arm`, never Invalid. Patterns stay checked in every
row, reachable or not, as in the seed. The 256-offset bound, quantities, first-parameter strict
field descent and forward-call restrictions remain enforced. An offset's `+`
must touch its literal (`1n+p`); a separated `+` is operator sugar,
`Unsupported parse operator`. The tail follows the `+` after a space, a newline, a
comment or a blank line, as the seed's term reader skips them; a keyword on a later line is no
tail (`Unsupported parse term-form`). As in the seed, `0n+t` reads as t itself, so a
parsed offset always spells a successor. An expression offset checks as that
spelling, the matrix's own expansion: `kn+t` is k Succ constructors around the
shared tail, as the seed builds it, so recursion through `1n+f(p)` allocates
linearly in its depth. The checker checks the tail once and wraps it in
k = `U32.to_nat` of the count Succ constructors with one Nat-indexed builder
(`literal-offset.bend::successors`), so a successor takes no checker level. The
count sizes the core, so above 4096 it is `Exhausted check`; the seed answers Yes
there. Compilation stops earlier: the emitter takes two of its 4096 levels for
each successor, so an offset above 2047 (less inside a deeper expression) is
`Exhausted emit`, and the checker CLI's core display is `Exhausted inspect`; it
still evaluates up to 4096. These are resource bounds, never rejections. Until
review round 9 the checker took three levels per successor and stopped at 1364.
The construction is proved for every count, not only k = 2:
`literal-core-LAWS.bend::offset_cells` (by induction on k, in any book, k
successors around any tail whose value is known return k cells around it, in
4k+c transitions), `check-LAWS.bend::offset_lowering` (for every count up to
4096 and every tail that checks to a term and its uses, against the installed
Nat, the checker returns `successors(to_nat(count), term)` with those uses) and
`offset_bound` (the same tails above 4096: `Exhausted check`). Their k = 2
ground instances,
`natural_offset` and `offset_spelling`, stay as witnesses. Outside the laws:
`U32.to_nat` as Base's reading of the count, and the linear-allocation claim,
which the frozen depth books measure.
Literals and Nat offsets check against
a known type, as bare constructors do: an unannotated binding (`n = 3`,
`n = 2n+m`) is `Invalid check annotation-required`, a literal or offset
scrutinee is `Invalid check constructor-scrutinee`, and with Base a literal or
offset arm on a datatype scrutinee is `Invalid check pattern-type`. A literal field pattern
is `Unsupported check nested-field-pattern`. A single-column match takes this matrix when an
arm spells a literal or a Nat offset (also in a constructor's fields) or its scrutinee is an
installed primitive; every other match is a datatype match, flat or a binary matrix, and a
literal in a row of several columns is `Unsupported check literal-column`. As in the seed, a row that binds
a matrix column with `+` (`+x`, `1n+ +p`, `SCon{c, +t}`) promotes that column
in every row of the match, and so every field opened from it. The binder, the
scrutinee and those fields may then be used twice, even in rows before the `+`
row. Without a `+` row the column and its fields stay affine. A binder row
(`x`, `_`) also names its column's unrefined value, as the seed's default
continuation does: a `+` on a field (`Succ{+p}`) does not let a catch-all use
the column twice. `Chr{...}` patterns and broader
nested pattern support are still Unsupported. The Base constructor `U32{data: Word(32n)}` has
no representation in the unboxed U32 and is `Unsupported check u32-constructor`
in patterns and expressions. Base installs the primitive of every literal a
book uses. Without it nothing is installed, and the seed spells a literal by
bare constructor names, as the matrix expands it (`Zero`/`Succ`,
`SNil`/`SCon`), or, for U32 and Char, by Base's `Word`. The case is keyed on
the absent primitive, not on a type name. A literal or offset, in an
expression or as an arm, whose target datatype declares the spelled
constructor, and a U32 or Char literal with any target, is
`Unsupported check literal-base-type`. A target that declares no spelled
constructor, or no target at all, is `Invalid check unknown-type` at the
literal.

Hash-verified Base supplies a closed lowering registry: four primitive types
and 39 operations. Calls retain explicit typed quantities. Intrinsic nodes and
installed-type markers cannot be written in user syntax. `BaseIntrinsic` audit
lines identify these trusted lowerings, including datatype representations;
`BaseChecked` identifies bodies parsed/checked as source; `BaseUnchecked` is
the exact remainder of all 466 seed declarations. This does not claim checked
Base-body proofs for the lowered operations.

The independent evaluator interprets Literal, Intrinsic and Default core
terms. Nat remains unary source data and String remains SNil/SCon data.
Its result line is `Evaluated<TAB>type<TAB>word<TAB>display`. A value of an
installed primitive type displays as the seed's literal for it: `300`, `3n`,
`'a'` and `"a\n"`, with the seed's escapes (named escapes, each quote escaped
only inside its own kind of literal, `\u{hex}` for controls, DEL, surrogates
and codes past U+10FFFF, raw UTF-8 otherwise). This holds inside records
too; other data keeps the live-field frame `Name{a,b}`, which differs from the
seed's `Name{a, b}` in separators, omitted erased fields and module
qualification. The word is
a U32 or Char value's bits and otherwise the constructor tag, so it is not an
ordinal for a primitive result. The display budget and 65,536-character cap
still apply.

The new Wasm profile uses an instruction graph, a Wasm dispatcher and explicit
source frames/returns. Every function body is emitted and executed at invocation time.
U32/Char use i32 bits; Nat uses Zero/Succ cells, String uses tag/head/tail cells.
Unsigned division/remainder, zero divisors, logical right shift and counts of
at least 32 match the frozen seed algebra. This is not a binary Nat ABI.

The frozen 65536n and deep non-tail-recursion witnesses require more than the
old one-page heap and host call stack. The new ABI therefore fixes 64 MiB of
linear memory, with static data below 1 MiB, returns at 1–5 MiB, frames at
5–22 MiB and an immutable bump heap at 22–64 MiB. It bounds instructions at
32768 and traversed primitive Nat/String values at 1048576 elements. It has no
reclamation. Resource guards are Exhausted, not Invalid; other runtime traps
are HostFailure. The profile must be selected explicitly in the Node adapter.

Bundle checking now defaults to depth 4096 and compilation to a 1048576-byte
output budget, sufficient for the frozen offset matrix. Legacy single-file
defaults and explicit maximum limits remain. Evaluator transition budgeting is
unchanged; primitive decoding/application also has separate fixed work bounds.
Enum-signatured host observations remain the supported external boundary.
Primitive Nat/String traversals in the evaluator are tail calls with
accumulators, so both evaluator lanes reach the same bounds without host
stack depth. The compiler hands each section body to the published byte
builder as runs of at most 4,096 bytes (`machine-code.bend::runs`, inverted by
`seq`): the builder's `finish` copies a chunk with Base's non-tail
`List.append`, so the run width, not the module size, bounds that stack depth,
and both compiler lanes build identical modules up to the instruction bound.

Three complete new proof entries check 37 helper laws. They cover the required
arithmetic guard equations, String traversal order and length, literal
decoding and display round trips, section runs, core transitions (including
the successor chain of an expression offset for every k) and matrix
expansion; they
do not prove whole-compiler correctness or all-input intrinsic refinement. The
registered literals gate compares the frozen accepted calls in both evaluator
and compiler lanes, compares 61 frozen primitive and record result displays in
both evaluator lanes, and kills 36 type-correct semantic mutants. The Wasm host
observes enum results only, so result displays have no Wasm lane.
Live Perch review remains a coordinator gate; offline preflight alone is not a
style pass. Existing compiler gates and their frozen expectations are retained.
