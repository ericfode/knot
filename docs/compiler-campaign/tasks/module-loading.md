Excerpt of tests/compiler-modules/SPEC.md: the loading and import-path paragraphs that the loader laws state and prove.

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

