# Perch context contract (fixed before implementation)

This offline tooling increment changes no compiler capability, Bend source,
rubric, or quality target. Literal review fixes the following expectations.
Seed/evaluator/Wasm differential execution is inapplicable to context assembly;
the unchanged compiler gates still run. Fixtures below are tooling input, not
new accepted Bend language features.

`interfaces-v1` is an explicit context policy. Legacy invocations keep their
existing request identities and assertions. The compiler manifest opts in.
Its `files` remain the closed local dependency inventory. Optional
`selected_files` identify whole files reviewed in full, in reading order;
every compiler file must be selected in at least one group. Other inventory
files are hash-pinned interfaces, including earlier proof-entry chains.

1. Datatype targets follow referenced types through the transitive local import
   closure. Cycles terminate. No file-count or helper-count cut truncates types.
   The 48,000-byte source budget remains; omissions have explicit markers.
2. Published imports resolve offline from `packages/` or `--package-store`.
   A store may contain `0x<32 lowercase hex>/` directories (all regular files),
   or package directories with a `RELEASE.json` `closure` inventory. Verify
   actual bytes, never just a claimed hash: first 32 hex digits of SHA-256 of
   sorted `sha256(file) path\n` lines, exactly the pinned seed publish identity.
   Every closure member is verified; a change to an unused member invalidates
   the package. Reject traversal, symlinks, duplicate members, environment
   files and imports outside the verified membership. Preserve failure reasons.
3. An interface includes import aliases, complete datatype declarations, and
   definition signatures without implementation bodies. Law statements are
   signatures; law fills supply heads only. Mark all omitted bodies and pin
   the original full-file hash. Multiline types, nested colons, comments,
   strings and same-line bodies must not leak implementation text.
4. Composition source bytes are the UTF-8 bytes actually supplied: full
   selected sources plus marked interface text. Exact bound fits; bound + 1
   does not. Nothing silently drops a selected file to fit. Size overflow is
   unavailable with an explicit `composition_byte_limit` marker.
5. At most 48 helper and four caller bodies are supplied. Overflow supplies
   marked interfaces when they fit. Summarized is distinct from unresolved or
   truncated. Signature/type dependencies remain closed. Byte overflow retains
   an explicit reason and withholds qualification as before.
6. Snapshot, context, summary and package hashes participate in freshness and
   request identity. No environment file or network is read. A provider is
   unnecessary for all acceptance controls.

Controls: clean local/transitive/cyclic types, verified packages, full-source
selection, nested signatures and exact byte bounds; broken missing/tampered
packages, escaping members, lost declarations and oversize contexts; held-out
Unicode bytes, unused package-member tampering, multiline/law heads and proof
chains. Four syntax-valid semantic mutants must be rejected by these unchanged
controls: leaked body, unverified package accepted, lost truncation marker,
and silently accepted oversized composition. Infrastructure errors do not
count as mutant kills.
