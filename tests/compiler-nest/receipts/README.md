# Nest increment handoff

This is the historical first-round handoff from `57a0c01`. Its default-region,
budget and empty-emission claims were corrected in
[review round 2](REVIEW-2.md). That round's evidence is `nest.json`, `review.json` and
the round-2 gate report; the original frozen expectations remain unchanged. Later rounds are recorded in
[REVIEW-3](REVIEW-3.md) to [REVIEW-13](REVIEW-13.md): each round's gate writes `roundN.json` beside them, and the
receipts of the older gates record the hashes of the inputs they ran on, so the coordinator refreshes them after a
merge (`npm run gates:refresh`).


The remainder below is the historical first-round report; its counts describe that checkpoint. Current round-13
verification is in [REVIEW-13](REVIEW-13.md), `round13.json`, `round13-gates.json` and `round13-budget-corpus.json`. Earlier receipts
retain their original source hashes and observations until the coordinator regenerates them after merge.

Reproduce the law falsification with `python3 -B tests/compiler-nest/falsify.py round12` and
`python3 -B tests/compiler-nest/falsify.py --write round13`. The driver first checks each mutant's implementation
without the laws, then requires a failed proof in its law file. Round 12's old receipt predates the operator ruling;
its let-suffix mutant now fails `call_ends_a_let`. The new receipt records the current round-13 laws.

Measure the bootstrap corpus with `python3 -B tests/compiler-nest/budget_corpus.py`: compare the 65,536-node
checker against a 1,048,576-node control on all pre-round-13 files, run the new stress fixtures only on the
production bound, and report each top-level `src/*.bend` outcome. Unsupported source cannot establish that its
core fits; qualification on the whole compiler awaits literals, generics and modules.


The implementation is verified within the authorized bounded scope: all 15
registered gates pass, and the runner exits 0. Frozen nest conformance is
**38/40**, with `rec-swapped-args` and `rec-alias` explicitly unmet. Their Invalid
expectations are unchanged; Knot conservatively reports
`Unsupported check recursive-call`. `nest.json` sets
`qualification.complete=false` and excludes them from passing conformance.

## Change

`src/matrix.bend` lowers ordered pattern matrices by column specialization and
default rows. It supports multiple scrutinees, wildcard/variable patterns,
nested constructors, overlapping rows, and first-match selection. Deferred
aliases retain lexical identities, source binder order, quantities and descent
information. Source pattern validation precedes unreachable-body elimination.
The existing checker produces core `Case` trees; the evaluator and emitters
retain that representation. Empty datatypes and their zero-row matches are
accepted. The emitter handles their uninhabited case with `unreachable`.

Flat unique matches keep their original path. All 25 enum modules remain
byte-identical in both compiler lanes and both emitter profiles. The fields
profile executes the three accepted recursive nest books, including descent
through nested patterns. A partitioned 4096-step quota bounds matrix expansion
and reports `Exhausted check budget` conservatively.

The parser, catalog event lookup, checker dispatch, contracts, manifest and
census are updated. The new gate is appended to the existing 14 registrations.
Shared existing receipts are untouched in this worktree; the coordinator owns
their refresh after integration. Aggregate runner evidence records 63 identical,
7 volatile-only and 11 semantic receipt changes in the exported scratch tree.

## Commits before implementation

| Commit | Frozen change |
|---|---|
| `e82c79c` | Multi-scrutinee acceptance and restated classification law |
| `f5bcc0c` | Duplicate-constructor rows select the first body |
| `4b024ee` | Nested constructor discrimination and seed result |
| `2810a17` | Nested single-constructor binding and seed result |
| `997f83f` | Empty-datatype acceptance and checked catalog law |
| `b2637ad` | Three separate resource/affine controls, fixed before Knot execution |

The implementation commit contains this report. Each commit records the seed
or literal basis and the requested coauthor. The original 40 nest fixtures,
their expectations and regeneration script are byte-identical to base
`6f132ea`. No other existing assertion was changed. The frontend summary now
says “downstream observations” because the authorized match flip adds success.

## Fresh gates

Commands: `BEND_NO_TELEMETRY=1 npm run -s gates` exits 0;
`npm run -s gates:verify` passes 18 tests. Counts below come from this run's
receipts and completion lines; they are not inferred from historical receipts.

| Gate | Exact passing coverage |
|---|---|
| `frontend` | 14 reference fixtures in 2 parser lanes; 24 boundaries; 4 boundary laws and 6 classification laws; 4 original mutants; 12 classification fixtures in 2 lanes; 7 classification mutants; 72 downstream observations |
| `checker` | 49 reference fixtures; 98 checked observations; 10 depth and 16 catalog-bound observations; 7 mutants |
| `structural` | 16 seed fixtures; 64 phase observations; 4 boundary pairs; 7 mutants |
| `fields` | 40 seed fixtures; 240 phase observations; 36 budget probes; 6 host probes; 12 level/inspection observations; 9 mutants |
| `wasm` | 25 source books; 90 reference calls in 2 lanes; 62 rejection pairs; 44 boundaries; 7 mutants |
| `wasm-trust` | 3 entries, 0 proof holes |
| `fields-trust` | 4 entries, 0 proof holes |
| `structural-trust` | 2 entries, 0 proof holes |
| `owned-store` | 3,532 cases in 2 lanes; 15 literal witnesses; 6 mutants |
| `flat-store` | Each lane: 3,534 instances, 13,621 observations, 7 lifecycle checks, 2 installed-boundary states; 9 mutants |
| `recursion` | 19 seed fixtures; 114 phase observations; 4 fuel probes; 3 mutants |
| `fields-wasm` | 8 fixtures; 32 seed calls; 64 evaluator and 64 Node observations; 50 enum hashes; 30 boundary probes; 4 mutants killed in both lanes; 5 checked laws |
| `census` | 33 compiler files; 497 declarations; 40 feature classes; inventory current |
| `lint:verify` | 127 tests; 8 law rules |
| `nest` | 40 reproduced seed fixtures / 174 entry calls; 38 matching outcomes; 25 accepted books; 386 evaluator and 386 Wasm values; 78 rejection phase observations; 24 boundary observations; 100 enum hashes; 6 mutants / 12 semantic kills |

The nest receipt also records 76 check observations for the 38 matching
fixtures and 12 separate phase observations for the 2 unmet fixtures. These
categories overlap with phase counts; they must not be added as unique tests.
The 386 values per runtime are 25 main results plus 168 accepted entry calls,
each observed in two compiler lanes. The other 6 seed entry calls belong to
the two deliberately out-of-stage books, which remain Unsupported.

`src/matrix-PROOF.bend` prints `All terms check.`: all 13 new matrix laws and the
complete imported proof chain are filled. Stable row selection and helper
boundaries are universally quantified. The complete irrefutable/exhaustive
tree laws are concrete checker normalizations, not a universal compiler or
exhaustiveness theorem. See [the law packet](LAW_REVIEW.md) for the coverage
matrix, inhabited witnesses and omitted proof obligations.

## New controls and mutants

The frozen original suite is unchanged. Three separately committed controls add:

- `tree-arena`: the seed and evaluator return On for a depth-12 binary tree;
  its 82,008 literal bytes exceed the 65,536-byte arena, and Wasm reports
  `Exhausted wasm arena-overflow`. The depth-4 control uses 344 bytes and succeeds.
- `matrix-work`: a seed-accepted total matrix exhausts the explicit lowering
  quota with `Exhausted check budget`.
- `nested-alias-affine`: reconstructing and consuming the same nested alias
  twice is rejected as affine reuse, consistent with the seed.

Six type-correct semantic mutants are killed in both native and Bun lanes:
last-row-wins, most-specific-row-wins, dropped defaults, nonexhaustive
acceptance, erased nested fields made live, and affine reuse through a nested
alias. Wrong values/acceptance/rejection are required; type errors and host
failures cannot count as kills. Rejected/exhausted compiles preserve existing
artifacts.

## Preflight and next increment

Offline preflight covers all 17 changed/new Bend files and 288 declarations,
with zero provider requests. It returns attention (exit 3): 28 truncated
contexts, 51 declarations without sufficient supporting-role context, and an
unavailable combined composition (128,390 bytes against 48,000, plus 78
unresolved nonlocal-import references). The report counts 29 structural
blockers. Compression, Delight, Memetic identity, Anticipation and Payoff are
all **unrated**; no style pass is claimed. The matrix implementation itself
has no truncated declaration context in this receipt.

The next recursion increment must implement the seed's complete decreasing-call
rule before classifying the two unmet cases Invalid; it must retain the
accepted later-parameter descent behavior in the recursion controls. The
coordinator still needs targeted live semantic/style review and bounded proof
adequacy review. General full-tree preservation proofs, less conservative
matrix resource accounting, structured host arguments, generic/closure
patterns, and owned-memory reclamation are not established here.

Evidence: [nest receipt](nest.json), [runner summary](all-gates.json),
[verification and source hashes](verification.json),
[offline preflight](style-preflight.json). The verification record also retains
the initial manifest-closure failure and rejected ill-typed mutant attempt;
neither is counted as passing evidence.
