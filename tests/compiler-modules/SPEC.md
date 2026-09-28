# Imported books and pinned Base

This increment adds an explicit `--bundle ROOT` mode to the existing check,
evaluation and compilation CLIs. The original argument forms keep the enum
profile's budgets and exit codes; the few single-file diagnostic changes are
listed in the [compiler specification](../../src/SPEC.md). A bundle root supplies
files; it is never a hub address and is never filled from the network.

An imported book has one ordered declaration stream. Each user file contributes
all of its declarations, including unreachable definitions. An import header
suspends its file while dependencies load. Active paths detect cycles; completed
paths suppress repeat loads. Aliases belong to the importing file. Names become
ordinary qualified tokens before catalog construction, body checking, evaluation
or emission. A lexical binder keeps its bare name wherever it is read, a call
head included, so it shadows a global of the same spelling. The later compiler
phases have no module-specific bypass.

Imports accept `./path.bend`, `../path.bend`, plain `path.bend`, and lowercase
`0x<hash>/path.bend`, each with `as Name`. As in the seed, one empty segment may
follow the leading `./` or hash head (`.//path.bend`, `0x<hash>//path.bend`); it
names the module that the single-slash spelling names. Bare `import Base` loads the pinned
Base source. Named package pointers report `Unsupported load named-package`.
Malformed imports, absent bundle entries, cycles and alias/declaration collisions
report `Invalid`. File access failures other than missing imported files remain
`HostFailure`. Resource bounds report `Exhausted` and never establish invalidity.

Path identity uses normalized filesystem paths, with imported local namespaces
relative to the entry directory and bundle namespaces relative to the bundle.
Dot and parent segments are eliminated before identity or namespace decisions.
A relative entry, bundle root or import target whose normalized spelling still
begins with `..` names its file through a parent of the working directory, whose
name the loader cannot observe, so it has no canonical spelling and reports
`Unsupported load path-identity`. The normalized working directory (`--bundle .`)
contains every relative path. The seed's containment prefix for the root
directory is `//`, which contains nothing; `--bundle /` reports `Unsupported load
root-bundle`.
The host query rejects symlink components and non-exact directory-entry spellings
with `Unsupported load path-identity`, including case aliases on insensitive
filesystems. Entry and bundle roots are queried before lexical normalization;
user paths are queried before reading. Base's toolchain symlink is intentional
and is instead constrained by the pinned content digest. The query observes
filesystem metadata only; it does not resolve module names or parse source.
Missing paths retain the existing missing-file classification; query failures
remain HostFailure. This assumes stable files during loading, not race-resistant
file-descriptor identity. No realpath alias equivalence is implemented. Absolute
import spellings outside the profile report `Unsupported load absolute-import`.
Entry and bundle paths must use the same absolute/relative basis; a mixed basis
reports `Unsupported load mixed-path-roots` until the host boundary can supply
canonical module identities across both path bases.

Base is the unmodified 67,190-byte source from Bend 2.0.29 at `574b6d3`, SHA-256
`22eea83911e2395f63594fea7c10ac0c1e5b548251681fc97cd7667e0eb7031b`. The loader
verifies that digest before inventorying it. SHA-256 is implemented in Bend over
the pinned ASCII bytes, with independent Python-hashlib vectors fixed before
implementation. The seed's arithmetic lowering and host file primitives remain
trusted. No substitute prelude or synthesized Base implementation is used.

All 466 Base declarations participate in book-global name registration at their
import event. Name registration rejects both bare and qualified collisions in
the same category; Base imported later checks the accumulated user symbols.
The dependency slice does not shadow Base names with user declarations.
The reachable dependency closure starts from every user definition,
with separate type/function and constructor references and lexical binder scope.
Only that Base slice is parsed, checked and lowered. Source order is retained.
Uncheckable reachable Base syntax reports its specific `Unsupported` reason;
it cannot become accepted or `Invalid` by falling through a narrower checker.
An audit emitted after complete checking records the selected Base declarations
and the exact unchecked complement. Loading Base is not whole-Base acceptance.

The loader permits at most 1,024 machine transitions. Each user file is bounded
by the existing budget (maximum 65,536), counted in UTF-8 bytes of the text read,
before header removal; the loader reads one byte more, and decoding never shortens
input, so a larger file is `Exhausted` rather than truncated. Parser and checker
limits retain their existing meanings. Base input is capped at
131,072 ASCII bytes and then constrained by its exact digest. The slice traversal
has a separate finite depth/work bound. These limits are operational bounds, not
proofs about the validity of larger programs.

The compiler checks the combined book before opening its output. Rejection and
exhaustion preserve an existing output file. Before that, the output passes the
same path query as the sources and may not climb above the working directory
(`HostFailure arguments output-path`), and it may not name the entry, a loaded
module or the Base path (`HostFailure arguments source-is-output`). Spellings on
one basis must differ; across bases, the absolute spelling may not end with the
relative one. The default emitter remains the
enum profile; no fielded Wasm or recursive Wasm capability is added by importing
a module. Evaluator observations and Wasm results are compared with the frozen
seed calls, and native/Bun compiler builds must emit identical bytes.

The independent gate is `tests/compiler-modules/check.py`. Its main oracle is
the immutable `expectations.json` and bundle; two requested seed fixtures were
added and committed before implementation. Supplemental regressions and digest
vectors also have independent expectations. Type-correct mutants attack shared
module deduplication, alias re-export, importer-relative resolution, bundle
presence and cycle reporting. Laws cover loader transitions, canonical paths,
name scopes, Base dependency selection and pin boundaries. They are checked
helper/transition laws, not a theorem of compiler correctness or whole-graph
confluence.

Header lines follow the seed's import grammar: a `#` begins a comment at the
start of a word or right after the alias identifier, and is otherwise part of
its word, so `import Base#c` names a non-Base path without an alias (`Invalid
load import-alias`). The seed splits header lines on JavaScript whitespace; until
the header closes, a line holding anything but printable ASCII, space or tab
reports `Unsupported load header-character`.

Review-round-2 fixtures freeze symlink/case aliases, Base namespace collisions
in both import orders, ordinary/reusable constructor-named binders and a
column-zero foreign body. Constructor binder rejection uses resolved names
and the registered constructor inventory, even when Base is not in the
selected slice. Quoted foreign bodies remain Unsupported regardless of column;
non-string module imports after declarations remain Invalid.

Review-round-3 fixtures (`review-round3.json`) freeze byte-budget truncation,
glued `#` imports, header separators, binder order and let binders. As in the
seed's parser, a pattern or let binder (ordinary, reusable or typed) is rejected
only when its resolved name is a constructor registered before it: the loaded
globals, including all of Base once imported, and the file's earlier datatypes.
A constructor declared later leaves the binder a variable. Single-file books
apply the same rule to let, arm and flat field binders in declaration order
before checking; the checker no longer tests field binders against the whole
book, which crossed module namespaces. The gate also
pins the bytes of the path query's Bend wrapper and C/JS adapters to
`host-check-expectations.json`, requires the adapters to equal the io-abi-2
reference bodies, and runs literal drift controls.

Review-round-4 fixtures (`review-round4.json`) freeze relative spellings that
climb above the working directory, run from their own directory with literal
entry and bundle arguments for both the seed and Knot; multi-line string
literals whose continuation line begins with `import`; result types longer than
one name and a spaced `- >` arrow; and eleven literal output-guard cases. Once
body text has held a double quote, a later `import` line stays body text, and
the lexer or parser reports it. A result type other than one bare name reports
`Unsupported parse result-type`; a missing name or colon stays `Invalid parse
function-result`, and the arrow's two tokens must be adjacent.

Review-round-6 fixtures (`review-round6.json`) freeze three seed rules. A
declaration is fresh only when neither its spelling nor its qualified name is
already registered, and each declaration registers before the next: a sibling
module's `def m.f` after its own `def f` is `Invalid load duplicate-global`, the
reverse order is accepted, and exact duplicates within one file report the same
code in the bundle lanes. One empty segment after a leading `./` or hash head is
accepted, and every other empty segment stays `Invalid load import-path`. The
seed resolves a binder before binding it, so an unbound dotted let, typed-let or
field binder is `Invalid check dotted-binder` in both lanes, while a dotted
binder that rebinds a name in scope, and an erased let's dotted name, are
accepted.

Review-round-7 fixtures (`review-round7.json`) freeze two more seed rules. The
seed reads a type as a term, so a binder in scope shadows a type name in every
later type position of its scope: a later parameter type, the result type, a
typed-let annotation after a let (live or erased) or arm field binder, and a
later field type. Such a program is `Invalid check binder-as-type` in both
lanes. Every Knot binder holds a value; a Type binder is Unsupported at parse.
Qualification leaves a bound name bare in a type position, and a declared
constructor's fields bind only within it. The seed also reads a declared type
or function as a term. Knot has neither value yet, so an unbound term name
naming a type is `Unsupported check type-as-term` and one naming a function is
`Unsupported check function-reference`, in both lanes and for own, forward,
module and Base declarations. A constructor without braces, an undeclared name
and a match scrutinee naming a declaration stay `Invalid check free-name`. The
Base slice classifies a user value mention of a Base type or function before
selection, so no such mention selects, parses or checks a Base declaration.

The reading hypothesis is one explicit machine state for loading: pending
headers, active paths, completed paths and the accumulated declaration stream.
Qualification and Base reachability are separate mechanisms with bounded
composition groups. Offline Perch preflight records structural context limits;
the coordinator owns live semantic and style review.

## Single-file deltas (accepted by the coordinator, 2026-09-28)

The single-file CLIs share the parser and checker with the bundle lanes, so the
module rules change some of their diagnostics. Arguments, limits and exit codes
are unchanged. The coordinator accepted the first ten changes on 2026-09-28:
each moves Knot toward the seed's verdict and is pinned by seed-derived
fixtures. The round-7 findings asked for the last two, which are pinned the
same way.

| Form | Before | After |
| --- | --- | --- |
| Let binder named like an earlier constructor | Checked | `Invalid check constructor-pattern-binder` |
| Arm binder named like an earlier constructor | `Unsupported check variable-pattern` | `Invalid check constructor-pattern-binder` |
| Field binder named like a later constructor | `Invalid check constructor-pattern-binder` | accepted |
| Declaration-order binder walk past 65,536 steps | — | `Exhausted check` |
| Result type longer than one name | `Invalid parse function-result` | `Unsupported parse result-type` |
| Spaced `- >` arrow | Checked | `Invalid parse function-result` |
| Parent-relative import | `Invalid parse declaration-name` | `Unsupported parse import` |
| `&` or `\|` after a parameter or field type | `Invalid parse argument-separator` | `Unsupported parse parameter-type` |
| `(`, `->`, `&` or `\|` after a typed-let type | `Invalid parse expected-=` | `Unsupported parse binding-type` |
| Unbound dotted let, typed-let or field binder | Checked | `Invalid check dotted-binder` |
| Binder named in a later type position of its scope | Checked | `Invalid check binder-as-type` |
| Declared type or function as an unapplied term | `Invalid check free-name` | `Unsupported check type-as-term` or `function-reference` |

Rounds 3 to 5 made the first nine; their seed evidence, fixtures and
authorization are in the [round-5 decision table](REVIEW-ROUND-5.md#single-file-deltas).
Round 6 adds the tenth ([round 6](REVIEW-ROUND-6.md#single-file-deltas)) and
round 7 the last two ([round 7](REVIEW-ROUND-7.md#single-file-deltas)). The seed
rejects a declared function or type where a datatype is expected; Knot reports
it Unsupported there too, which round 7 records as conservative. The
[compiler specification](../../src/SPEC.md) and `legacy_commands` in
`src/CONTRACT.json` list the same changes.
