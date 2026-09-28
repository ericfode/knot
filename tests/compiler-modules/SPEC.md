# Imported books and pinned Base

This increment adds an explicit `--bundle ROOT` mode to the existing check,
evaluation and compilation CLIs. The original argument forms retain the enum
profile's diagnostics, budgets and exit codes. A bundle root supplies files; it
is never a hub address and is never filled from the network.

An imported book has one ordered declaration stream. Each user file contributes
all of its declarations, including unreachable definitions. An import header
suspends its file while dependencies load. Active paths detect cycles; completed
paths suppress repeat loads. Aliases belong to the importing file. Names become
ordinary qualified tokens before catalog construction, body checking, evaluation
or emission. The later compiler phases have no module-specific bypass.

Imports accept `./path.bend`, `../path.bend`, plain `path.bend`, and lowercase
`0x<hash>/path.bend`, each with `as Name`. Bare `import Base` loads the pinned
Base source. Named package pointers report `Unsupported load named-package`.
Malformed imports, absent bundle entries, cycles and alias/declaration collisions
report `Invalid`. File access failures other than missing imported files remain
`HostFailure`. Resource bounds report `Exhausted` and never establish invalidity.

Path identity uses normalized filesystem paths, with imported local namespaces
relative to the entry directory and bundle namespaces relative to the bundle.
Dot and parent segments are eliminated before identity or namespace decisions.
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
by the existing character budget (maximum 65,536), before header removal; parser
and checker limits retain their existing meanings. Base input is capped at
131,072 ASCII bytes and then constrained by its exact digest. The slice traversal
has a separate finite depth/work bound. These limits are operational bounds, not
proofs about the validity of larger programs.

The compiler checks the combined book before opening its output. Rejection and
exhaustion preserve an existing output file. The default emitter remains the
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

Review-round-2 fixtures freeze symlink/case aliases, Base namespace collisions
in both import orders, ordinary/reusable constructor-named binders and a
column-zero foreign body. Constructor binder rejection uses resolved names
and the full registered constructor inventory, even when Base is not in the
selected slice. Quoted foreign bodies remain Unsupported regardless of column;
non-string module imports after declarations remain Invalid.

## Literals amendment

The literals increment (milestone 5) changes this contract in four places.
The coordinator and the modules owner sign off on them; until then they are
recorded here, not assumed accepted.

- `base-load.bend::parse`: a selected Base declaration that names one of the
  closed registry's four types (U32, Nat, Char, String) or 39 primitive
  operations is replaced by its checked lowering from
  `src/literal-base.bend`, instead of being tokenized and checked as source.
  Unsafe and foreign declarations are still rejected first. The dependency
  walk (`references`, `pattern_scope`) follows literal, offset and intrinsic
  nodes.
- `load.bend` tokenizes module files with the literal-aware
  `literal-lex.bend`, and `describe` emits `BaseIntrinsic` rows for the
  lowered declarations. The audit is now five row kinds: `BasePin`, `Module`,
  `BaseChecked`, `BaseIntrinsic` and `BaseUnchecked`. The three declaration
  inventories partition all 466 Base declarations, each in pinned source
  order. This gate's adapter accepts the new kind, requires that partition,
  and requires every modules book's intrinsic rows to equal its declared
  `intrinsic_base` set (empty for every current book).
- `qualify.bend` passes literal nodes through and walks an offset's tail
  like any other pattern, so its binder gets round 2's constructor-binder
  check. An intrinsic node in user source is an internal failure: user
  syntax cannot spell one.
- The `--bundle` defaults are raised: checker depth 512 to 4096 in check,
  eval and compile, compile output 65,536 to 1,048,576 bytes, and the
  audit's checker depth 512 to 4096, sufficient for the frozen 256-offset
  literal matrix. Explicit budget arguments keep their meaning.

The reading hypothesis is one explicit machine state for loading: pending
headers, active paths, completed paths and the accumulated declaration stream.
Qualification and Base reachability are separate mechanisms with bounded
composition groups. Offline Perch preflight records structural context limits;
the coordinator owns live semantic and style review.
