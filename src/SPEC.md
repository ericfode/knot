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
  still constrain their columns and undergo name/arity validation, in the
  nested matches of a discarded body too: each row has one pattern per scrutinee
  and valid patterns (a declared constructor and its field count, no constructor
  as a bare binder, no call, no `+` before a datatype declared earlier in the
  file, which is `Invalid check datatype-pattern-binder`), while a discarded body
  is not type-, scope- or scrutinee-checked, as in the seed. A binder hides a
  datatype of its name from the types written after it (an annotation, a later
  parameter type, the result, a later field type): `Invalid check
  type-shadowed`. Variable
  defaults remain checked even past the last constructor, with a live binding
  at the emptied type. A missing arm is accepted only as dead code: some live
  binder already in context, before the scrutinee in match order, has an empty
  constructor set (an emptied residual or a zero-constructor datatype). This
  never bypasses the checking of a selected body. Pattern binders and live let
  binders are single words. The seed accepts a dotted name there only where it
  rebinds a name in scope, which the parser does not resolve, so every dotted
  binder (a pattern, a `+` promotion, a let, a typed let) reports `Unsupported
  parse dotted-binder`, never Invalid; an erased let's dotted name stays a name.
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
  A split's field binders are those of the first row that starts its constructor, as in the seed: a `+` on one of
  them marks that field in every row below the split, and at every later split of the remaining rows; a `+` in a later
  row marks only its own binder, and the marks of a variable row reach every row of its column.
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
| `import ./...` or `import 0x.../...` | `parse` | `import` |
| A line break where call or constructor arguments expect an element, a separator or their closer | `parse` | `line-break` |
| A second `case` arm on the line of an arm's body | `parse` | `same-line-arm` |
| A line break in a let before its `=` or `:`, before its value or between its marker and name | `parse` | `line-break` |
| A statement on the line of a let's value | `parse` | `same-line-statement` |
| A numeral opening a later column of a row (a Nat literal pattern), or a term after a header's scrutinee that is no closer, separator or keyword | `parse` | `term-form` |
| A `(` that starts a line in a match or case header, where the seed reads a parenthesized term as the next column and never as a call's arguments | `parse` | `term-form`, or `argument-whitespace` among call or constructor arguments |
| A case at, left of, or at the margin of its match's column | `parse` | `pattern-or-indentation` |
| A `def` or `type` at another column | `parse` | `top-level-indentation` |
| A `def` or `type` on the line of a body's end | `parse` | `same-line-declaration` |
| A name or a numeral (or in a pattern a marking `+`) after an argument, without a comma | `parse` | `argument-whitespace` |
| A promotion of a promotion (`++y`, `+ +y`) | `parse` | `repeated-promotion` |
| An arm body that starts with a name, `+`, `-` or `match` on the line after its `case`, at the case's column or below it; a later statement at another column | `parse` | `body-indentation` |
| A term suffix where a term ends (a body, a let's value, an expression argument): an infix operator, a call, an index, an offload `!(`, a lambda after a name; a `+name` term; a line that starts with an operator, `!(` or `=>` | `parse` | `term-form` |

After a term the seed reads an infix operator (each of its table: `->`, `&`, `|`, `||`, `&&`, comparisons, `<>`, `++`,
`<&>`, `.|.`, `.^.`, `.&.`, shifts, arithmetic), a call, an index, an offload `!(` and, after a name, a lambda `=>`;
`+name` is a promoted variable, and a line that starts with an operator, `!(` or `=>` continues the term before it.
A body the lowering discards is parsed and never checked, and a live one needs a target the program defines (`def
Bool.or`, `def Pair`), so the parser leaves each unread: `Unsupported parse term-form`, never Invalid. It keeps
`Invalid` where the seed rejects everywhere: a closer, `==`, `=>` after a constructor, a `+` or `-` touching a name
(a marker), a lone `.` or `!`, a `(` or `[` at a line's start, an erased `-name`, and a constructor line of a type.

The seed reads a line break inside call or constructor arguments and inside a let
as whitespace, arguments separated by whitespace alone as arguments, and a second
arm on an arm's line as the next arm; Knot ends a term at a line break and takes
a comma between arguments, so these forms are unsupported, never invalid. A def
header's parameters and a type's fields have the same gap, which stays open (the
selfhost suite's `layout` need), as do an unindented def body (the frontend gate
pins it Invalid, though the seed accepts it), a call with fewer arguments than
parameters that the seed reads as an unused partial application (`Invalid check
call-arity`), a global function used as a value (`Invalid check free-name`) and a
Nat literal pattern as a let binder at another column, a constructor line of a type declaration at another
column, a spaced `+` or `-` that starts the line after a let's value (the seed continues the value with an
operator; round 10's `detached_marker` law pins `Invalid parse detached-marker`) and a hole or a `+` marker as the next
argument after whitespace. An arm body that starts
with a name, `+`, `-` or `match` and sits at or below its `case` column, and a
later statement at another column, are `Unsupported parse body-indentation`; an
empty arm stays invalid. Recognition stops at that prefix; it neither validates
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
