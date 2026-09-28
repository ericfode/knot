# Pinned Bend parser for Perch

This directory vendors the actual Bend 2.0.29 parser and its supporting kernel
from [bendlang/bend](https://github.com/bendlang/bend/tree/574b6d39a235b539eb19a5c532993a0abb3d11ad),
commit `574b6d39a235b539eb19a5c532993a0abb3d11ad`. The upstream code is Apache-2.0;
see `LICENSE`. `upstream.json` records the original source hashes.

`bend.mts` is the upstream `bend2/bend.ts` with the narrowly scoped changes in
`observer.patch`. The `.mts` extension explicitly selects ESM. Node 22.18 or
newer runs it with native TypeScript stripping. `base-source.mjs` embeds the
**unmodified** pinned `bend2/base.bend` text so parsing `import Base` needs no
filesystem access. Its text hash is checked by the tests.

Changes to the upstream module:

- Remove filesystem/path/OS imports and the complete filesystem, cache, hub,
  and `book_load` section. The module cannot resolve or load user imports.
- Add an optional `ParseObserver`. Record declaration spans and original bodies
  before match flattening; observe explicit call suffixes, including `f()`.
- Definitions also report `bodyBeg` immediately after the parser consumes the
  body delimiter. The adapter exposes its UTF-8 position as `body_start` for
  signature interfaces. This additive observation changes no parse semantics.
- Track the last consumed token around the existing trivia skipper, preserving
  ranges without counting comments before the following declaration.
- Add optional **dependency-context hooks** for imported law fills, constructor
  patterns, and explicitly marked template arguments. With no observer, normal
  parser behavior is retained. Local declarations and known Base declarations
  still use upstream checks.
- Record an unavailable-context error for `+Imported.Type<...>` when its quantity
  arity cannot be determined. Do not invent a datatype signature.
- Give an imported law-fill placeholder unknown (`Infinity`) template arity, as
  imported templates already have. A recursive `~` call inside the fill parses;
  the fill head's clause count and a foreign body's template check are skipped
  only for such placeholders, whose arity the pinned compiler validates. Local
  laws keep the upstream checks.

The adapter is `../../scripts/perch-bend.mjs`. Its asynchronous
`analyzeBendSource(source)` returns Perch's `SourceAnalysis` fields, with null
file/declaration metrics and additional `parser_metadata`. The profile is
`bend-2.0.29-574b6d3-observer-v3+law-template-arity`. Metrics are unsupported, not estimated.
`datatype_declarations` additionally retains parsed datatype ranges for review
context; datatypes are not counted as function/law checks.

Names and IDs are stable across whitespace/line changes. A declaration is an
upstream `def` or `law`; datatypes are parsed but are not presented as functions.
A local law and its implementation produce one method target. Its primary range
is the implementation; `law_location` preserves the law separately, so intervening
declarations do not leak into a method's body. Imported fills retain their source
alias, e.g. `L.proof`. Positions use one-based lines and UTF-8 columns, zero-based
UTF-8 byte offsets, and exclusive ends.
The optional `body_start` is the exclusive head end, before body trivia; law
statements and datatypes have no omitted body. Consumers do not scan colons or
quotes to infer it.

The import-header recognizer in the adapter is extracted from pinned
`book_load`'s real import grammar. It retains every original source offset while
masking validated header lines for `parse_book`. It validates named package
spelling but performs no package lookup, canonicalization, or import loading.

## Boundaries

This is syntax analysis with explicit unavailable-context diagnostics. It is
not a type, quantity, termination, law, or proof checker. Parsing invokes no
`book_valid`, evaluation entry point, foreign code, filesystem resolver, or hub
request. The retained upstream evaluator/checker exports are never called by the
adapter.

Source-only analysis cannot verify imported law existence/parameter counts,
constructor arities, or template signatures. Hooks are restricted to names with
an actual import alias and report this limitation. Imported constructors use the
written field count as provisional parse context; explicit imported `~` arguments
are parsed without pretending their expected count is known. Ordinary local
missing-law definitions, unknown local constructors, and malformed syntax reject.
A dependency requiring an unknown `+` datatype signature returns `unsupported`,
not a successful parse. Resource failures return `resource-unavailable`.

References come from original parser nodes and explicit call observations,
before lowering can duplicate or erase nodes. They include explicit static
calls/values in definitions and laws, plus module imports. Bound dynamic calls,
constructors, datatype declarations, foreign implementation paths, and implicit
or desugared operations are omitted. Module import references retain the written
module and alias with `imported_name: '*'`. No complete call-graph claim is made.

## Per-declaration review context

`../../scripts/perch-bend-context.mjs` is a separate **working-tree review**
layer; it does not change the parser's no-I/O contract. It reads only explicitly
referenced relative `.bend` imports inside the real workspace boundary, including
uncommitted helper changes. It never reads a Git revision, scans unrelated files,
fetches remote imports, or evaluates Bend. Each file is captured once per check.

The installed Perch extension expands `check file.bend --rules names` into the
parsed definitions and laws selected by `each: method` rules. No `sees` field is
needed or accepted on a method rule. A named `file.bend::declaration` remains one
check. Primary source uses the declaration's exact byte span and its adjacent
contract comment. Matching laws, local datatype declarations, static callees,
function values, and a bounded number of same-file callers are separate context.

Legacy helper context is bounded to 48 declarations, 12 files, 4 callers, and 48,000
source bytes. Truncation and unresolved names are explicit. Context receipts
contain working-tree file hashes. Aggregate results retain per-unit answers,
findings and source lines. All selected local helper sources are parsed before
the first request; a malformed helper or failed provider unit fails the aggregate.
Files with no function/law units do not manufacture successful method coverage.
Committed `scan` continues to use its committed graph and source snapshot.
The compiler's opt-in `interfaces-v1` policy follows the separate
[interface-context contract](../../tests/perch-context/CONTRACT.md), including
verified offline packages and marked overflow signatures.

## Validation and update

Run `node --test tests/perch-bend-parser.test.mjs` from the repository root.
The suite covers valid and malformed grammar, law/fill identity, original UTF-8
ranges, static versus dynamic references, import grammar, explicit unresolved
context, and filesystem/network traps. It also parses every nonignored `.bend`
file under `packages/` and `research/`; generated build/cache copies are excluded
by the repository's existing ignore rules.

For a pin update, obtain the exact upstream commit, verify its original hashes,
review/reapply `observer.patch`, re-embed Base without changing its text, update
`upstream.json` and the adapter profile, then rerun the parser and Perch CLI
integration tests. Changes must remain observer/context scaffolding around the
actual parser. Do not replace it with a regex function splitter or infer compiler
acceptance from a successful source analysis.
