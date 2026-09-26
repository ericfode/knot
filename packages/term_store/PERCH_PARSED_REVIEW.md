# TermStore: bounded parsed Perch review — 2026-09-26

**No implementation change needed.** Fresh live review completed **169 checks**:
16 actual Bend declarations × (six Bend + four performance rules), plus the current
law-review packet × (eight law rules + the owned memo-completion rule).
**17/17 provider requests completed**, actual model `jev-1.13.0` (`jev-latest`).
No reported implementation/law findings: confirmed **0**, false-positive **0**,
unresolved **0**. The separate shared-receipt observation below is confirmed tooling
metadata loss, not a Perch finding about TermStore semantics.

## Exact targets and evidence

Every declaration is in `packages/term_store/main.bend`; each used
`npm run lint -- packages/term_store/main.bend::<name> --rules <10 names> --json`.
The pinned Bend parser found 44 declarations. The selected units and supplied helper/
caller context cover 42 unique declarations, with **no context truncation**.

| Parsed target | Start line | Checks | Receipt in `evidence/perch-parsed-review/` |
| --- | ---: | ---: | --- |
| `Scopes.claim` | 176 | 10 | `Scopes-claim.json` |
| `Store.new` | 192 | 10 | `Store-new.json` |
| `Store.alloc` | 213 | 10 | `Store-alloc.json` |
| `Store.get` | 218 | 10 | `Store-get.json` |
| `Store.set` | 225 | 10 | `Store-set.json` |
| `Store.length` | 132 | 10 | `Store-length.json` |
| `Store.limit` | 137 | 10 | `Store-limit.json` |
| `Store.snapshot` | 156 | 10 | `Store-snapshot.json` |
| `Cell.step` | 65 | 10 | `Cell-step.json` |
| `Cell.result` | 92 | 10 | `Cell-result.json` |
| `Memo.new` | 232 | 10 | `Memo-new.json` |
| `Memo.alloc` | 235 | 10 | `Memo-alloc.json` |
| `Memo.inspect` | 240 | 10 | `Memo-inspect.json` |
| `Memo.apply` | 271 | 10 | `Memo-apply.json` |
| `Memo.result` | 252 | 10 | `Memo-result.json` |
| `memo_commit` | 245 | 10 | `memo_commit.json` |
| `LAW_REVIEW.md` (file packet) | 1 | 9 | `LAW_REVIEW.json` |

[summary.json](evidence/perch-parsed-review/summary.json) records every exact target,
root `.perch/usage` receipt path, source hash and check count. Individual receipts
retain the command, resolved model, provider counts, raw probabilities, CLI target
span, and working-copy context provenance. The first `Scopes.claim` pilot's CLI JSON
was inspected in the tool output; its wrapper receipt and exact parsed context are
retained, without repeating the unchanged paid request.
[preflight.json](evidence/perch-parsed-review/preflight.json) contains exact parsed
target text, helper/caller bodies, datatypes, unresolved references and limits.

Parser identity: `language-pack-1.20-v3+knot-bend-0cd9e831fc413760`, based on Bend
2.0.29 commit `574b6d39a235b539eb19a5c532993a0abb3d11ad`. Context is the current
working copy, bounded to 16 helpers, four callers, 12 files and 48 KB. Base primitive
identities and the published Vec import remain unresolved; the adapter does not
fetch or type-check dependencies. Existing Vec release evidence supplies that
separate boundary, not these probabilities.

Selected rules: six `bend-*` rules at 80%; `perf-growing-prefix-copy` at 70%,
`perf-loop-invariant-work` and `perf-linked-list-indexing` at 60%, and
`perf-amortized-growth` at 80%. The packet used all eight `law-*` rules and
`term-store-memo-completion-boundary`, each at 80%. No floor or rule text changed.

`Memo.apply` includes the whole read → transition → commit path and the four
begin/succeed/fail/cancel wrappers as callers. Store operations include their
scope checks, result translation and state-rewrapping helpers. Only `Scopes.new`
and `Scopes.from` were not supplied as target/helper/caller declarations; their
trivial initial constructors were inspected directly. No unchanged conformance,
model, proof, benchmark or calibration fixture was resubmitted. The law packet
covers their documented role; historical deterministic evidence is identified below.

## Adjudication and changes

No reported finding required a package repair or the authorized stronger repair
model. The largest below-floor source signals were arithmetic (55–65%), including
65% on `Cell.result`, which has no arithmetic. The supplied scope helpers visibly
check the final U32 value before incrementing. Store bounds/growth delegate to the
pinned Vec dependency; no local growing-prefix copy or linked-list indexing loop
exists in the reviewed implementation. These signals provide no concrete defect;
correct semantics were preserved. The law packet's largest score was observable
essence at 58%, also below its reporting floor. Probabilities are retained, not
silently rounded into proof claims.

**Confirmed shared tooling gap at the reviewed version; proposal only:** the
wrapper writes `units` from `result.units`. A single named declaration instead returns its name, span and
context at the top level. Its root usage receipt therefore retains checks/scores
but drops that declaration attribution and helper-context provenance. This pass
stores the named CLI result beside the root receipt, with preflight context for
the pilot. Proposed shared fix: normalize a named Bend result to one unit when
`result.units` is absent; add a regression asserting target name, span, context
hashes and truncation flags survive. This pass edited no shared file. Concurrent
shared-tooling changes are outside this review. The reviewed
wrapper hash is recorded in [validation.json](evidence/perch-parsed-review/validation.json).

New in this pass: this report, exact-declaration/context receipts and a bounded
review driver (`scripts/perch-parsed-review.py`). Earlier work: all implementation,
laws, independent model, conformance, semantic mutants, and publication. The prior
`PERCH_REPORT.md` remains the historical file-level audit. No implementation, rule,
accepted law, package release or campaign state changed. No style ranking was run:
there was no genuine implementation alternative with the same contract to compare.

## Validation and two mechanisms worth reading

Fresh command: `scripts/bend-reference packages/term_store/main.bend --check-only`
returned `All terms check.` All 14 uploaded file hashes still match published
`0xce7bfa94c40ded8493cdb39d330add0c`. Existing proof, CPU/JS conformance, ten semantic
mutation kills, scaling and remote-consumer receipts were verified against current
source hashes; they were not rerun. No hidden completion, GPU/Wasm, concurrency, or
all-history refinement claim was added.

The existing code makes three observations explicit with two Result layers
(`main.bend`, lines 92–101): outer failure means no completed result; inner failure
is a completed computation error. The matching constructors make this distinction
visible without a sentinel value.

```bend
def Cell.result(-T: Data,-E: Data,cell: Cell<T,E>) -> Result<Error,Result<E,T>>:
  match cell:
    case Pending{}:
      Fail{NotReady{}}
    case Evaluating{}:
      Fail{NotReady{}}
    case Ready{x}:
      Done{Done{x}}
    case Failed{e}:
      Done{Fail{e}}
```

The existing commit helper (`main.bend`, lines 245–250) makes preservation visible
in the returned owner: a rejected transition returns the original store; only
an accepted transition reaches the write. Its two branches expose the state rule
without implicit mutation.

```bend
def memo_commit(-T: Data,-E: Data,s: Store<Cell<T,E>>,id: Id,cell: Cell<T,E>,r: Result<Error,Unit>) -> Memo<T,E> & Result<Error,Unit>:
  match r:
    case Fail{e}:
      (Memo{s},Fail{e})
    case Done{u}:
      memo_wrap(T,E,Unit,Store.set(Cell<T,E>,s,id,cell))
```

This verified review increment is committed only under `packages/term_store/`;
the final handoff records the commit ID. Concurrent shared/compiler/sibling changes
remain owned by their respective chats. No publish or push is part of this pass.
