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
The profile excludes symlink and case aliases, as does the frozen oracle. No
claim of filesystem-realpath or case-folding equivalence is made. Absolute
import spellings outside the profile report `Unsupported load absolute-import`.
Entry and bundle paths must use the same absolute/relative basis; a mixed basis
reports `Unsupported load mixed-path-roots` until the host boundary can supply
canonical paths without expanding the existing effect inventory.

Base is the unmodified 67,190-byte source from Bend 2.0.29 at `574b6d3`, SHA-256
`22eea83911e2395f63594fea7c10ac0c1e5b548251681fc97cd7667e0eb7031b`. The loader
verifies that digest before inventorying it. SHA-256 is implemented in Bend over
the pinned ASCII bytes, with independent Python-hashlib vectors fixed before
implementation. The seed's arithmetic lowering and host file primitives remain
trusted. No substitute prelude or synthesized Base implementation is used.

All 466 Base declarations participate in book-global name registration at their
import event. The reachable dependency closure starts from every user definition,
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

The reading hypothesis is one explicit machine state for loading: pending
headers, active paths, completed paths and the accumulated declaration stream.
Qualification and Base reachability are separate mechanisms with bounded
composition groups. Offline Perch preflight records structural context limits;
the coordinator owns live semantic and style review.
