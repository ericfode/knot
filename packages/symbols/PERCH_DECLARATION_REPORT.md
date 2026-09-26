# Symbols — bounded declaration review, 2026-09-26

**No code needed changing.** This fresh pass completed 169 relevant checks over
16 parsed Bend declarations and the current law-review packet, with 17/17 live
provider responses. Requested `jev-latest`; resolved `jev-1.13.0`. No reported
finding: confirmed package defects 0, reported false positives 0, unresolved
reported findings 0. No repair model, style ranking, rule edit, publication or
campaign resumption was needed.

This increment adds this report and bounded-review receipts only. Implementation,
laws, proofs and fixtures are unchanged from published Symbols
`0xf5507d46d06a1a8043dcb1a582194615`. Earlier work was the implementation/release
and the separate whole-file audit in PERCH_REPORT.md; none is counted as a change
made during this pass.

## Exact review scope

Every target used the root `npm run lint -- <target> --rules <names> --json`
wrapper. Source declarations received six `bend-*` rules (fuel completeness,
machine arithmetic, borrow lifetime, ordered F32, effect boundary, device stack)
and four `perf-*` rules (growing-prefix copy, loop-invariant work, linked-list
indexing, amortized growth), at their unchanged configured floors. The Markdown
packet received all eight `law-*` rules plus `symbols-bidirectional-preservation`.

| Target | Checks | Completed responses | Retained receipt |
| --- | ---: | ---: | --- |
| `main.bend` | 130 | 13 | [3b4ed23f](receipts/perch-declarations-2026-09-26/3b4ed23f-88f9-4b73-8c8d-5452b0dbb040.json) |
| `model.bend::insert_found` | 10 | 1 | [5e1c26f7](receipts/perch-declarations-2026-09-26/5e1c26f7-12c0-492b-bf13-bdf898b7020a.json) |
| `observe.bend::collect` | 10 | 1 | [f53ec4f6](receipts/perch-declarations-2026-09-26/f53ec4f6-bb16-4a25-a057-a54ff50461a0.json) |
| `observe.bend::collect_next` | 10 | 1 | [8f43eafd](receipts/perch-declarations-2026-09-26/8f43eafd-80e1-469a-99bd-c3dbb965771c.json) |
| `LAW_REVIEW.md` | 9 | 1 | [7469ca02](receipts/perch-declarations-2026-09-26/7469ca02-f958-46f9-ad1d-9d979dfd080b.json) |

All 13 main declarations were selected: `Table.bounded`, `Table.new`, `metadata`, `Table.length`, `Table.limit`, `found`, `Table.find`, `inserted`, `append_name`, `intern_found`, `Table.intern`, `resolved`, `Table.resolve`.
The additional named targets examine independent insertion behavior and complete
reverse snapshots, including the helper's failure branch. Current working-copy
callees, callers and datatype context were supplied by the adapter. Unchanged
conformance/proof fixtures, benchmark entries and rule controls were not sent
again; their earlier deterministic/control evidence remains separate.

[Exact commands/receipt mapping](receipts/perch-declarations-2026-09-26/index.json),
[verification and hashes](receipts/perch-declarations-2026-09-26/verification.json),
and [working-copy contexts](receipts/perch-declarations-2026-09-26/contexts.json)
retain scope, scores and limitations. Copied wrapper receipts include model,
source/rule identities, raw probabilities and provider counts; credentials were
neither read nor copied. Original receipt paths remain in the index.

Parser: `bend-2.0.29-574b6d3-observer-v2`, via adapter
`language-pack-1.20-v3+knot-bend-0cd9e831fc413760`. All selected source parses.
No reconstructed context was truncated. `Table.intern` includes three local
helpers; `collect` includes four helpers from two files. The remote hash-imported
Vec and Base internals are explicitly unresolved/nonlocal; Perch did not fetch
or review them. Pinned dependency behavior is supported by deterministic release
evidence, not by pretending the model saw those implementations.

## Adjudication and validation

No reported semantic or performance defect required repair. Below-floor scores
remain in the raw receipts, not reclassified as definite defects or successes.
The independent model deliberately uses list search/append; it is an oracle with
a simple representation, not an optimized interner. Public reverse lookup uses
Vec's checked random access; repeated collection does not index a linked list.
The existing common-prefix Base Map cost is documented and benchmarked, not a
new optimization or an undiscovered constant-time guarantee.

The fresh `scripts/bend-reference packages/symbols/PROOF.bend --check-only`
returned `All terms check.` Current upload files and every source digest from
receipts/gates.json match the release. Historical native/JS trace, mutation and
benchmark evidence therefore still identifies this source. Those unchanged
suites were not rerun solely to repeat earlier work. This pass does not establish
universal arbitrary-history refinement or GPU execution.

One **confirmed shared-tooling limitation**: named-declaration responses have
parser/probability coverage, but the wrapper writes `units: []` and loses the
selected name/context from those receipts. The exact requested selector is kept
in this pass's index. `contexts.json` separately reconstructs the contexts with
the same adapter from unchanged sources; it is explicitly not a capture of the
provider request. Main's file-level receipt retains all 13 full unit contexts.
The coordinator independently reproduced this gap and is repairing receipt
normalization with a regression test in a separate increment. That change does
not alter parser context or provider questions; these completed calls are retained
without repetition. No shared tooling or review log was edited by this package
chat, and the shared repair is not counted as a Symbols change.

## Two existing mechanisms worth showing

`main.bend:57` (unchanged) makes duplicate success independent of free capacity:

```bend
  match lookup:
    case Some{id}:
      (InternTable{v,m},Done{id})
    case None{}:
      append_name(m,name,V.Vec.length(String,v))
```

The two branches expose the invariant directly: a known name returns its original
ID with both stores retained; only absence reaches append. The symmetry rewards
a quick, accurate reading without a separate duplicate/growth state machine.

`main.bend:43` (unchanged) commits the forward entry only after reverse append:

```bend
  match result:
    case Fail{error}:
      (InternTable{v,m},Fail{Exhausted{}})
    case Done{unit}:
      (InternTable{v,Map.set(&2,Maybe<&2,U32>,m,name,Some{id})},Done{id})
```

Vec's unchanged-state failure and the retained map compose into an atomic
observable failure. The success branch places publication of the name/ID mapping
beside its returned ID. This is a direct explanation of useful structure, not an
invented ranking between unrelated algorithms; no genuine implementation
alternative was introduced for style comparison.

## Checkpoint boundary

Commit only this report and `receipts/perch-declarations-2026-09-26/` as the
coherent review increment. Root/shared files and other chats' active `src/` work
are outside this checkpoint. The final handoff records the resulting commit ID.
