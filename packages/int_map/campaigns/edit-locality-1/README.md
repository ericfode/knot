# IntMap edit locality — bounded proof experiment

## Before generation

The user accepted a single additive proof experiment after the random-number
sidecar proposed explaining the shared edit recurrence through its projections.
Author: GPT-6 Astra, max reasoning. One candidate, at most one separately retained
compiler-diagnostic retry. No runtime refactor, publication or score retries.

**Reading hypothesis:** one pair of equations explains both rebuilding policies:

```text
low(join(a,b)) = a                 high(join(a,b)) = b

get(p, edit(join,p,m,end)) = value(end)
separated(p,q) => get(q, edit(join,p,m,end)) = get(q,m)
```

The endpoint theorem follows the edited path; the locality theorem follows both
paths until their first different bit. Raw Branch satisfies both projections by
reduction. Pruning branch satisfies the existing branch_low/branch_high proofs.
Insertion selects Entry; removal selects Tip. This makes empty-pair collapse
compatible with lookup without allowing general child promotion across depths.

Add the generic laws and four public specializations in `locality/LAWS.bend`
and `locality/PROOF.bend`. Preserve the runtime, existing 23 laws and their
proofs, independent model, fixtures, conformance, mutation assertions, performance
driver, SPEC, INTERFACE, release metadata and historical receipts byte-for-byte.
`preregistration.json` records the actual baseline identities before generation.

The new statements quantify over arbitrary Data values, finite paths, raw maps
and endpoints, conditional on both projection laws. The locality premise is the
existing constructive `separated`: equal paths and proper prefixes are excluded,
and opposite bits provide Unit. Its existing checked high-bit witness traverses
31 shared bits before separating. Actual raw/pruning instances discharge the
projection premises; they are not unchecked axioms. Existing public preservation
laws retain their exact domain. No universal key-injectivity, size/fold/union,
depth, allocation or complete list-refinement theorem is added.

Acceptance: check the entire additive proof closure with zero holes and the
unchanged original proof entry point; rerun native/JS conformance, the 11 existing
type-valid mutants and scaling/model gates in a new evidence directory. Freeze
the first generated sources and first compiler response. If one diagnostic retry
cannot close the proof, or the bookkeeping obscures the two projection equations,
retain the failed research and stop. Runtime performance is inherited from the
identical source; do not reinterpret earlier measured slowdowns or rerun timings
to seek a favorable result. Review all new declarations, the bounded mechanism
and a law packet under Perch v6 after integrating the user's vacuity observation.
Record below-target style results independently of deterministic acceptance.

## Outcome — retained as an additive proof, unreleased

Two checked generic theorems now explain both insertion and deletion. The
endpoint observation depends only on value(end); preservation depends only on
both child projections and the first different path bit. Four public
specializations instantiate the actual raw/pruning rebuilding policies. Two
raw projection lemmas discharge constructor premises; the pruning instance
uses the original checked projections. All four public statements retain the
original propositions and quantified domains exactly.

Author's disposition: **keep the additive proof**. The shared premise explains
why empty-pair pruning preserves lookup and why unrestricted child promotion is
excluded. The 69-line proof module makes that consequence explicit. Equality
transport still accounts for much of its syntax; the result does not justify
replacing the simpler original proofs or claiming a style breakthrough. No
further candidate or score-driven rewrite is part of this trial.

The first candidate failed in the parser: a local `edited` binding preceded
the nested match on q and closed its pending binder. The single diagnostic
retry moves those two bindings into the four leaf branches. No statement or
equation changed. The retry passes the pinned checker. Both versions and both
compiler responses are retained separately.

### Verified gates

- 8 additional and 23 unchanged original filled laws; both complete entry
  points check with zero holes. No unsafe proof or new axiom.
- Unchanged native CPU and generated JavaScript conformance and example pass.
- All 11 original mutants typecheck, then fail their intended observation.
- Existing scaling/list-model gates pass at 64,256,1024,4096 entries, dense and
  shared-prefix layouts, on both backends.
- All 70 frozen inputs match: runtime, original statements/proofs, model,
  fixtures, assertions, scripts, contracts and historical release receipts.
- Runtime source remains c4c6e55effd8507d21a184428d36c3711bd282493133139d88782476b0cf0a04.
  The earlier 3.1% native / 5.4% JS slowdown remains accepted under the user's
  20% allowance. These proofs introduce no runtime-source change or new relative
  performance measurement. No package publication or dependency update.

Evidence: [first compiler result](first-result.json),
[diagnostic retry](retry-result.json), [deterministic gates](gates.json),
[mutations](mutations.json), [scaling/model checks](performance.json),
[fixed-source audit](source-audit.json), and [law packet](LAW_REVIEW.md).

### Perch v6 review and its limits

The user's vacuity observation is integrated on main in merge `7750e5b`, retaining
both original commits `80c7ca5` and `b2d6b86`. Memetic appeal is independent of
conceptual value; vacuity alone cannot disqualify that axis. The merge passed all
84 offline checks, law-rule wiring and verification of the eight frozen v5/v6
comparisons. Other style criteria and thresholds are unchanged. This observation
does not relax the separate logical requirement for inhabited proof premises.

The canonical proof file passes the compiler but fails Perch's side-effect-free
observer, which supplies zero template clauses for imported law fills. It then
rejects the recursive `~join` argument. The original semantic/style preflight
failures are retained; no provider request was made for those failures.

[review-copy.py](review-copy.py) creates a mechanical review view from the exact
retry snapshots: concatenate the original laws and fills, remove only the local
G qualification, and relocate imports. This view also passes the pinned compiler.
The [mapping](review-copy.json), [complete source](review.bend.snapshot) and
[parser observations](parser-observations.json) are preserved. This is
supplementary review of the same law/proof bodies, not canonical per-file
automatic style coverage or a replacement maintained module.

Two named generic-proof reviews completed 22 reported checks (20 explicit rule
evaluations and two default general audits); the bounded law packet completed
nine. All five provider responses resolve to Jev 1.13.0, with
no finding at its floor. The source contexts were untruncated, with bounds of
16 helpers, 12 files, 48000 bytes and four callers. Built-in Bool/Empty/Unit and
Equal operations are marked unresolved-or-builtin. These judgments supplement
the deterministic checks, not prove correctness. See [semantic usage](semantic-usage.json),
[endpoint review](semantic-review-edit_here.json),
[locality review](semantic-review-edit_away.json), [packet review](semantic-laws.json).

The first supplementary style run covers all eight combined law/fill pairs with
eight fresh declaration responses plus one fixed-task response. The automatically
assembled composition omits the fixture collaborators referenced by the original
law file, so its composition is explicitly unavailable. One context-completion
run adds the frozen original proof/fixture/model files. It reuses all eight
identical declaration answers and the task answer, then obtains one composition
response and two context-declaration responses. No unchanged unit was rejudged.
Both runs resolve to Jev 1.13.0 under rubric v6; the later moving-alias cache
identity remains explicitly unverified by the tool, despite matching resolved
model names in the fresh responses. Historical v5 scores are not a baseline for
a numerical comparison under the changed rubric.

| New law/fill pair | Role | Compression | Delight | Memetic | Anticipation | Payoff |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| edit_here | leading | .58 uncertain | .73 | .09 below | .19 below | .17 below |
| edit_away | uncertain | .47 uncertain | .78 | .10 below | .21 below | .25 below |
| raw_low | supporting | .98 | .69 | .59 uncertain | .91 | .71 |
| raw_high | supporting | .97 | .63 | .52 uncertain | .89 | .69 |
| set_get | uncertain | .60 | .80 | .11 below | .25 below | .21 below |
| remove_get | supporting | .61 | .78 | .65 | .90 | .79 |
| set_preserves | supporting | .61 | .79 | .67 | .96 | .95 |
| remove_preserves | supporting | .67 | .79 | .69 | .96 | .95 |

Cells are probability mass at each applicable target (pass >=.60). Compression
and Delight require level3. The last three axes require level2 for supporting
roles and level3 for leading/uncertain roles. Three of eight pairs meet all five
targets. Every declaration context is untruncated. set_get's uncertain role
versus remove_get's supporting role is a noisy distinction: both are thin
specializations. That author's disagreement is not a replacement model score.

The expanded composition includes six complete files, 27257 bytes, no unresolved
references or truncation. It is broader than the new proof family: it includes
the unchanged implementation, original laws/proofs, fixtures and model.
Composition target mass is Memetic .21, Anticipation .12, Payoff .36: all below
.60. Task potential relevance is .35 (low), so Galaxy level5 is not required.
This is **not a complete style pass**. Full distributions, requested/resolved
models and exact context/rubric identities are in
[first supplementary ratings](style-review-copy.json) and
[expanded composition](style-composition.json).

### Reproduce

```sh
python3 packages/int_map/campaigns/edit-locality-1/validate.py
python3 packages/int_map/campaigns/edit-locality-1/review-copy.py
scripts/bend-reference packages/int_map/build/edit-locality-1/review.bend --check-only
```

Live review commands and exact target coverage are retained in the console and
usage receipts. Choose new output paths for a future review; do not overwrite
this run's scores. A later tooling increment can add imported template-law
context to the observer or classify its missing context as unsupported. That
parser work is outside this package proof increment. No universal key-injectivity,
depth, size/fold/union or complete model-refinement theorem is claimed.
