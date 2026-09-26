# Bounded checker and research review — 2026-09-26

The new resolver/checker is verified as an enum-profile checkpoint. The complete
compiler milestone remains unfinished: independent Bend evaluation and direct
Wasm emission/execution are still pending. The existing parser and adaptive-task
research were reviewed at bounded targets without changing their implementation.

## Current pass

Perch 0.3.5 / resolved model **jev-1.13.0** returned **321 checks in 105 requests,
105 responses**. All requests completed, and every target had nonzero coverage.
No above-floor findings were reported. There are no confirmed defects,
false-positive findings or unresolved reported findings from this pass. No code
was changed in response to Perch. No repair-model task was needed. Low-confidence
answers and incomplete context remain evidence limits, not a correctness proof.

The exact commands, rule selections, source/context hashes, per-unit probabilities
and wrapper receipts are retained in `receipts/perch.json`; individual payloads
are `receipts/perch-*.json`. Every recorded context file hash was verified against
the working copy before this checkpoint.

| Target | Rules | Checks / requests |
|---|---|---:|
| src/core.bend | checker trust, effect boundary | 8 / 4 |
| src/catalog.bend | checker trust, arithmetic, fuel | 54 / 18 |
| src/scope.bend | checker trust, arithmetic, fuel, pattern sharing | 60 / 15 |
| src/check.bend | checker trust, arithmetic, fuel, pattern sharing | 108 / 27 |
| src/checked-display.bend | fuel, growing-prefix copying | 10 / 5 |
| src/check-cli.bend | effect boundary, fuel | 22 / 11 |
| src/check-LAWS.bend | checker trust, fuel | 14 / 7 |
| src/check-PROOF.bend | checker trust | 7 / 7 |
| tests/compiler-checker/bounds.bend | arithmetic, fuel, effect boundary | 21 / 7 |
| research/compiler-checker/LAW_REVIEW.md | all eight law rules | 8 / 1 |
| src/parse.bend::run | checker trust, fuel, pattern sharing | 3 / 1 |
| research/adaptive-tasks/task.bend::run | fuel, borrow lifetime, device stack, invariant work | 4 / 1 |
| research/adaptive-tasks/LAW_REVIEW.md | state composition, proof-claim integrity | 2 / 1 |

Working-copy parsing is the pinned Bend parser adapter; the static helper context
is bounded to 16 helpers, 4 callers, 12 files and 48 KB. Twenty declaration contexts
are marked truncated, including checker/parser dispatchers and transitive CLI
callers. Imported Base and some constructor/type references remain unresolved in
Perch's metadata. The raw receipts retain these markers. Deterministic Bend
checking resolves the actual imports separately; Perch does not establish that.

## Validation and changes

This increment adds typed catalogs, lexical-level resolution, per-binder affine
sets, erased-context validation, constructor refinement inside match arms, and
whole-book checking. It adds a canonical checked-term observation CLI; this is
not a value evaluator. It preserves the existing lexer/parser files.

`python3 tests/compiler-checker/check.py` passed: 49 reference fixtures, 98 exact
Bun/native checked observations, 10 depth observations, 16 catalog boundary
observations, and 7 type-correct semantic mutants killed by unchanged expectations.
`src/check-PROOF.bend` fills seven helper/boundary laws and imports the four earlier
frontend proofs; the complete entry reports `All terms check.` The new laws are
not a general checker-soundness theorem.

`research/adaptive-tasks/PROOF.bend` was checked again and reported `All terms
check.` Its 12 laws and the implementation remain unchanged. Historical CPU/GPU
runtime receipts still refer to their recorded hashes; the 38 device runs were
not rerun in this bounded audit. No new runtime/device/performance claim follows
from this pass. No package source, release, or publication was changed.

The review itself made no code repair. All new checker work preceded this pass.
The earlier parser commit is df4ce4a; earlier adaptive-task implementation is
50855e0. The Git commit containing this report identifies the new checker and
this review. Shared documentation/tool edits made by other chats are excluded.

## Two mechanisms worth explaining

New code, `src/scope.bend:45-50`:

```bend
  match known:
    case Some{tag}: Done{C.Checked{C.Value{token,type_id,tag},type_id,Nil{}}}
    case None{}:
      S.choose(Result<S.Error,C.Checked>,Bool.and(live,U32.is_eq(q,0)),u => C.invalid(C.Checked,"erased-live",token),u =>
        Done{C.Checked{C.Reference{token,level,type_id},type_id,S.choose(List<&2,U32>,Bool.and(live,U32.is_eq(q,1)),u => [level],u => Nil{})}})
```

The same occurrence operation distinguishes a fresh constructor known from a
pattern, a forbidden live erased reference, and a live affine use. That small
representation choice permits `first(x,x)` inside a nullary arm after matching
x, while rejecting duplication of the original uninspected affine value.

Existing code, `research/adaptive-tasks/task.bend:52-59`:

```bend
def run(fuel: Nat, state: Run) -> Run:
  match fuel state:
    case 0n _:
      state
    case 1n+n Checkpoint{task}:
      run(n,step(task))
    case 1n+n Delivered{dest,payload}:
      Delivered{dest,payload}
```

The full residual state is the result at a budget boundary. Delivery is absorbing,
so re-slicing a completed task cannot replay its work. Its full-state fuel-addition
law is stronger than comparing a lossy output value. This mechanism predates the
current pass. There are no equivalent alternative implementations to rank; no
style scores or invented comparisons were produced.

## Proposed shared follow-up

For the coordinator's README update: the enum profile now has a seed-built Bend
lexer, parser, resolver and checker with 49 reference controls and 7 additional
checked helper laws. Evaluation and direct Wasm emission are the next increment.
Keep the distinction between Checked and Built.

Proposed development-log entry: checker implementation hit the seed's ordered-match
restriction when a dispatcher matched catalog/scope metadata before inspecting
an earlier AST field. Flattening constructor cases into the dispatcher's outer
match fixed it. A recursive function passed as a bare callback also failed the
seed's decreasing-call rule; an explicit thunk containing a call on the smaller
argument fixed it. The src/AGENTS.md guidance already names both structural fuel
and binder-order constraints; future dispatcher scaffolds should put expression
constructor patterns in the outer match before metadata. No elapsed time claim
is made. Shared AGENTS.md, README.md, review-log and rules were left to the
coordinating chat as requested.
