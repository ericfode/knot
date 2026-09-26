# Compiler-support handoff review — 2026-09-26

This bounded pass reviewed the survey and handoff against current package
contracts. Package owners are reviewing their implementations separately.
No package implementation, shared rule, compiler source or law was changed.

## Scope and Perch applicability

Reviewed documents: `docs/bend-stdlib-inventory.md`,
`docs/PACKAGE-CAMPAIGN.md`, and `docs/PACKAGE-RELEASES.md`. Contract inputs are
the six `packages/<name>/INTERFACE.md` files and the published release catalog.
Two unchanged source excerpts below illustrate the handoff; they were not
submitted as duplicate implementation audits.

Perch is **not applicable to this documentation-only increment**. There are
zero owned applicable Bend declarations and zero owned `LAW_REVIEW.md` packets
in this scope. Shared source rules select parsed source declarations; shared
law rules select `{packages,research,tests/perch-laws}/**/LAW_REVIEW.md`.
The installed skill, root/package instructions, `docs/perch.md`, and
`docs/perch-style.md` were read. No wrapper or ranking call was made: **0 targets,
0 checks, 0 provider requests/responses; no new `.perch/usage/` receipt**.
This is an applicability decision, not a zero-coverage semantic pass.

There are no new implementations of a shared contract to compare. The reading
observations below are direct explanations; no ordinal ranks were invented.

## Contract findings

| Package | Handoff assumption checked | Result |
| --- | --- | --- |
| Vec | Data elements in an affine container; unchanged-state failure; native indexed access; logical limit 16,777,216 | Matches. It cannot store affine continuations or serve as proof of Wasm/GPU lowering. |
| Source | Unicode scalar offsets, caller-managed file/revision identity, LF lines; logarithmic line lookup | Matches. Its maximum is 16,777,215 because the line index needs an extra slot; no byte/UTF-16 conversion is supplied. |
| OutputBuilder | Distinct text and checked raw-byte paths; constant structural composition and linear finishing | Matches. Bytes are U32 list elements, not a packed U8 buffer. ULEB/SLEB remain consumer algorithms. |
| IntMap | Persistent U32-keyed Data values, bounded 32-bit paths, explicit collision combiner, deterministic low-bit-first traversal | Matches. Traversal is not numeric sorting. Quantity addition must check or saturate; U32 arithmetic wraps. |
| Symbols | Exact strings, first-intern IDs, table lineage and caller-managed namespaces | Matches. Symbol numbers are neither lexical binder identities nor canonical cross-build numbering. |
| TermStore | Data payloads and affine store ownership; scope chain; append-only slots; Pending/Evaluating are not results | Matches. Cancel is serial interruption, not semantic failure or a concurrent attempt fence; no affine runtime heap is supplied. |

No support-contract mismatch or code defect was identified in this bounded
review. The stdlib survey is explicitly tied to its inspected versions and
distinguishes gaps in Base from packages outside Base. Its original proposal
remains historical context; the campaign and release catalog record completion.

One documentation defect was confirmed and fixed: the release summary described
live Perch calibration as currently unavailable. The existing calibration
receipt records 24 completed/covered controls, 19 correctly classified. The
summary now distinguishes unavailable review at release time from later live
evidence and retains the five misses and advisory status. It does not alter
historical receipts.

One proposed shared follow-up is returned to the Perch coordinator, without
editing its file: `docs/perch.md:95–97` still describes the compiler selector
locations as having no production targets. Clarify that the committed enum
lexer/parser under `src/` is now applicable, while the broader compiler milestone
is incomplete. This is stale coverage guidance, not a code defect.

There were no model findings to classify. Confirmed code defects: 0;
false-positive findings: 0; unresolved suspected code defects: 0. Documentation
disposition: 1 fixed, 1 shared follow-up proposed.

## Two useful mechanisms from the earlier package work

Exact excerpt from [IntMap](../packages/int_map/main.bend), lines 105–108:

```bend
def combine_value(~V: Data, ~combine: V -> V -> V, old: Maybe<&2,V>, right: V) -> V:
  match old:
    case None{}: right
    case Some{left}: combine(left,right)
```

The distinction between absence and collision is visible in four lines. The
fold at lines 110–114 supplies map traversal; the caller supplies only the
overlap algebra, with left/right order preserved. The same representation can
support sequential quantity addition or mutually exclusive branch maximum
without conflating their meanings. Missing entries stay distinct from present
sentinel values. The caller still owns safe counts and binder alignment.

Exact excerpt from [raw-byte composition](../packages/output_builder/bytes.bend),
lines 69–72:

```bend
def compose(left: Builder, right: Builder) -> Result<Error,Builder>:
  match left right:
    case Buffer{+cap,+n,a} Buffer{other,+m,b}:
      combine(U32.is_le(m,U32.sub(cap,n)),cap,n,m,a,b)
```

Given the checked-builder invariant `n <= cap`, the guard compares the right
length with remaining room before adding lengths. `combine` at lines 62–67
returns `Limit` on failure and constructs `Join{left,right}` only on success.
The syntax mirrors the safety argument: remaining capacity first, addition
second, deferred concatenation last. This preserves constant structural work
for composition; finishing later traverses bytes and chunks. It is the right
foundation for Wasm codecs but supplies no LEB128 implementation itself.

## Validation and change attribution

[The local review receipt](package-handoff-review-2026-09-26.json) retains input
hashes, release-record comparisons, exact excerpts, applicability, and scope.
All six catalog release-record hashes match their owner files, and catalog
content hashes match both expected and returned publication identities. Both
excerpt files match their recorded uploaded-file hashes. These are identity
checks, not fresh publication, remote downloads, performance tests or proof runs.
The existing shared-law calibration counters substantiate the documentation fix.

This pass changes only the release-summary paragraph and adds this review and
its receipt. The earlier frontend handoff is commit `a410053`; six-package
publication and implementation predate this pass. No code needed changing.
Document links, exact excerpt text, whitespace, and paused campaign state were
checked. No deterministic package gate was rerun without an implementation
change or suspected behavioral defect. No repair model was needed. The commit
for this review is reported in the coordinating chat's final result.

Published packages, package-owner audits, compiler work in progress, and the
paused campaign retain their existing ownership. No publishing or heartbeat
resumption occurred in this pass.
