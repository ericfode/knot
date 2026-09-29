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
2. Published imports resolve offline from `packages/`, then `--package-store`
   if supplied, otherwise `BEND_LIB` if set, otherwise `~/.bend/lib`.
   A store may contain `0x<32 lowercase hex>/` directories (all regular files),
   or package directories with a `RELEASE.json` `closure` inventory. Verify
   actual bytes, never just a claimed hash: first 32 hex digits of SHA-256 of
   sorted `sha256(file) path\n` lines, exactly the pinned seed publish identity.
   Every closure member is verified; a change to an unused member invalidates
   the package. Reject traversal, symlinks, duplicate members, environment
   files and imports outside the verified membership. Preserve failure reasons.
   Members are named `0x<hash>/<member>` in all review text and provenance.
   Store paths remain private local read handles. Release metadata locates a
   candidate closure; only verified member identities/hashes enter provenance.
3. An interface includes import aliases, complete datatype declarations, and
   definition signatures without implementation bodies. Law statements are
   signatures; law fills supply heads only. Mark all omitted bodies and pin
   the original full-file hash. Multiline types, nested colons, comments,
   strings and same-line bodies must not leak implementation text. The parser
   supplies the UTF-8 endpoint immediately after the body's colon; consumers
   never re-lex the signature. This includes `'''`, `':'`, `')'`, escapes,
   Unicode, and unparenthesized dependent/existential return binders.
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
7. Preserve the legacy composition instruction verbatim, then append the
   interface-specific warning against inferring implementations/checked proofs.
8. Equal package bytes have equal source byte counts and state identities
   across store and checkout locations and supported store layouts. Two
   unchanged manifest preflights must produce byte-identical receipts. The
   literal command needs no package-store flag; it must have zero blockers,
   unresolved imports and role-limited obligations on the frozen compiler tree.
9. Bare relative imports are local dependencies subject to manifest closure.
   Hash imports of other lengths remain syntactically recognized but explicitly
   `unsupported-package-identity`: only the seed's 32-hex publish identity is
   verified. Named packages and absolute imports remain unresolved offline.

Controls: clean local/transitive/cyclic types, verified packages, full-source
selection, nested signatures and exact byte bounds; broken missing/tampered
packages, escaping members, lost declarations and oversize contexts; held-out
Unicode bytes, unused package-member tampering, multiline/law heads and proof
chains. Four syntax-valid semantic mutants must be rejected by these unchanged
controls: leaked body, unverified package accepted, lost truncation marker,
and silently accepted oversized composition. Infrastructure errors do not
count as mutant kills.

Review round 2 fixes the additional literal expectations in
`review-expectations.json` before the repairs. It adds mutants for store paths
in identity, omitted anti-anchoring, binder-colon truncation and an omitted
default store. A standing parse-back oracle replaces omitted bodies with holes
and requires parsing plus the exact declaration-name set. This is a syntax
oracle, not acceptance of incomplete proofs or implementations. The adversarial
`fixtures/signatures.bend` separately passes the complete pinned seed checker.

## Encoded-state fitting (perch-cap increment; fixed before implementation)

Tooling only: no rubric, target, Bend source or accepted contract changes. The
60,000-byte encoded-state cap (task and metadata included) and the 48,000-byte
composition cap do not move. A declaration state that is still over the cap once
every helper and caller body is an interface summary gets a third tier, instead
of failing. Shaping source to fit a tool cap is not a fix.

10. **Order.** Every fitting step takes the largest saving first, then path, then
    name. The interface tier keeps its saving (the source bytes it removes). The
    names tier's saving is the encoded-state bytes the cut removes, including the
    change to its `summarized` row; a cut that cannot shrink the state is skipped.
    The choice is a function of the entries alone: the order in which `calls` and
    `called_by` were filled never changes which entries are cut. The names tier
    compares path and name by code point, so the process locale never changes its
    choice. The interface tier's tie-break is unchanged (the runtime's collation),
    which keeps every state that fits today byte-identical.
11. **Names-only entry.** A helper or caller entry that is not yet a name (an
    interface summary, or a body the interface tier kept because its interface
    was no smaller) becomes `{path, name, representation: "names-only"}`: no
    lines, no text, no signature. The signature is what the interface tier
    already supplies; keeping only its first line saved 337 of 13,357 bytes for
    `check.bend::run` (103 of its 105 interfaces are one line), so it is dropped,
    not shortened.
12. **Recorded and marked.** Each cut has exactly one `provenance.summarized` row
    with reason `context-state-names-only` (an interface entry's row changes its
    reason; a body entry gets a new row). The judge-visible `context_notes` gains
    `names_only: {count, note}` saying which context was cut to names.
    `provenance.source_bytes` and `context_notes.source_bytes` fall by the source
    bytes removed and still equal the supplied source. The files behind names-only
    entries stay in `provenance.files` with their hashes. Neither `truncated` nor a
    role-context gap is set: the tier is advisory, never a structural blocker.
13. **Nothing else is cut.** The primary source, the task or cohort text, the
    datatypes and the laws are byte-identical. Every state that fits today is
    byte-identical, with no marker and no row change, because the tier runs only
    where the fitting used to throw. Over the whole compiler manifest the state
    hashes before and after are equal.
14. **Failure.** The fitting throws only when no cuttable entry is left and the
    state still exceeds the cap. The error names the case (`after names-only
    summaries`) and reports the bytes that remain: the primary source, the task,
    the names-only entries and the retained datatypes, laws and notes.

Controls: a unit that is over the cap after every interface summary fits, with
its marker, its rows, its source-byte accounting and an untouched primary source
and task, both at unit level (a small cap) and through the whole preparation
(the 60,000-byte cap); a unit whose primary source exceeds the cap still fails
with the new error; states that fit are pinned to hashes taken before the tier
existed; entries inserted out of size order, with four equal-size entries (two of
them differing only in case) inserted out of path and name order, are cut in
exactly the specified order. Four
syntax-valid semantic mutants must be rejected by these controls:
`names-only-marker-dropped`, `primary-source-shortened`, `names-only-tier-skipped`
and `names-only-order-nondeterministic` (its mutation drops the path and name
tie-break, so the choice depends on the order the entries were filled in). A fifth,
`names-only-row-not-recorded`, was added during implementation to hold item 12's
one-row requirement. Infrastructure errors are not kills.
