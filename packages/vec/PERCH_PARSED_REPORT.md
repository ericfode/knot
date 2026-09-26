# Vec: fresh parsed Perch pass — 2026-09-26

No Bend code needed changing. No confirmed, false-positive, duplicate or unresolved
finding was reported. This pass adds review evidence, not an implementation repair.
All 13 uploaded files remain byte-identical to
`0xd684886d10b431b9dce6c3b2d1ef1980`; nothing was published or resumed.

## Exact scope and evidence

| Target | Parsed declarations | Checks | Completed responses | Retained receipt |
| --- | ---: | ---: | ---: | --- |
| `packages/vec/main.bend` | 35 | 350 | 35 | [implementation](evidence/perch-parsed/implementation-receipt.json) |
| `packages/vec/LAW_REVIEW.md` | file packet | 9 | 1 | [law packet](evidence/perch-parsed/law-packet-receipt.json) |

Actual model: **jev-1.13.0** (requested jev-latest), Perch 0.3.5 with the installed
Bend adapter. Both npm-wrapper commands exited 0. No missing response, partial
request or zero-coverage result counted as a pass. Exact commands and original
`.perch/usage/` paths are in [runs.json](evidence/perch-parsed/runs.json).

The implementation target includes all 14 public declarations and 21 helpers.
Every declaration received six `bend-*` rules plus `perf-growing-prefix-copy`,
`perf-loop-invariant-work`, `perf-linked-list-indexing`, and
`perf-amortized-growth`. The packet received all eight `law-*` rules plus
`vec-logical-state-observation`. Full unit names, locations, per-rule raw scores,
file/context hashes, and parser diagnostics are retained in the receipts and
[summary](evidence/perch-parsed/summary.json).

Source SHA-256: `baddf475d1fffb58749a6ab780dade30a10c8cf12b810320bc1903c5cdb28bb0`. Packet SHA-256:
`f0ca169fc459739d7c50d2c2e2bdc5ef1717c68dc7f1ddc8420a95876e984f4d`.

Parser identity: `language-pack-1.20-v3+knot-bend-0cd9e831fc413760`, backed by Bend 2.0.29 commit
574b6d39a235b539eb19a5c532993a0abb3d11ad. Context used the current working copy:
local helper bodies, direct callers and datatypes. **None of the 35 contexts was
truncated.** Caps were 16 helpers, four callers, 12 files and 48 KB. Base names
remain `unresolved-or-builtin`; dynamic calls and desugared operations are not a
complete semantic call graph. Parsing is not type/proof checking. The exact
preflight inventory is [preflight.json](evidence/perch-parsed/preflight.json).

Unchanged proof/test/benchmark fixtures and control packets were not sent again.
They were covered by earlier package work; this pass concentrates on implementation
mechanisms and the current contract packet. The prior broader audit and rule
refinement in PERCH_REPORT.md are historical, not changes made in this pass.

## Adjudication and validation

There were no reported findings to repair or escalate. The highest source score
below its floor was machine-arithmetic at 0.66 for `discard_value`, which performs
no arithmetic. Such unlocalized probabilities do not justify changing semantics.
No rules or thresholds changed and no stronger repair generation was needed.

Fresh deterministic check: `scripts/bend-reference packages/vec/PROOF.bend
--check-only` passed with all terms checked. The 13 release-file hashes match,
and the prior runtime gate's source hashes still match the working copy. Native/
JS conformance, mutation tests and scaling were **not rerun** because no semantic
edit or concrete suspected defect required them. See
[validation.json](evidence/perch-parsed/validation.json). GPU and general all-length
refinement remain outside the existing evidence.

## Two mechanisms worth reading

These excerpts are existing source reviewed during this pass, not new changes.
There is no genuine pair of alternative implementations here, so no style ranking
was run or invented.

`packages/vec/main.bend:94` (lines 94–99):

```bend
      match enough:
        case True{}:
          (cap,depth)
        case False{}:
          +next = U32.add(cap,cap)
          plan_step(p,next,1n+depth,minimum,U32.is_le(minimum,next))
```

The recursive step keeps the growth invariant visible: capacity doubles while
depth increases once and fuel decreases once. The caller bounds the minimum to
2^24, so 24 steps suffice. Growth consequently copies at geometric boundaries;
there is no hidden length+1 reallocation policy.

`packages/vec/main.bend:190` (lines 190–199):

```bend
def collect(-T: Data, count: Nat, last: U32, a: Array<Maybe<&2,T>>,
  acc: List<T>) -> Array<Maybe<&2,T>> & List<T>:
  match count:
    case 0n:
      (a,acc)
    case 1n+p:
      +i = U32.sub(last,1)
      unpack(Array<Maybe<&2,T>>,Maybe<&2,T>,Array<Maybe<&2,T>> & List<T>,
        Array.get(Maybe<&2,T>,a,i),
        b => x => collect(T,p,i,b,prepend_slot(T,acc,x)))
```

Read from the right and prepend: the two directions cancel, yielding original
order in one linear pass. `unpack` passes the returned owned array into the next
step, making ownership transfer explicit. The same small operation serves both
full conversion and checked range copies, without repeated prefix append or a
second reversal. That symmetry explains the compact structure's payoff.

No shared workflow/rule change is proposed. Only explicit owned report, driver
and evidence paths belong to this checkpoint; concurrent compiler/sibling work
remains outside it. The checkpoint ID is reported in the final handoff.
