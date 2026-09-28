# Descent-2: seed decreasing-call rule

Implemented against pinned seed `574b6d39a235b539eb19a5c532993a0abb3d11ad`,
on `campaign/descent-2` from `57a0c01`. The rule and evidence boundary are in
[`tests/compiler-descent/SPEC.md`](../../tests/compiler-descent/SPEC.md).

Live self-calls compare non-erased parameter columns left to right, accepting
the first strict decrease and rejecting growth/incomparability or all equality.
Constructor fields use componentwise comparison, with the seed's exact subterm
fallback and first-failed-field exclusion. Comparison follows local aliases
without replacing runtime references or weakening quantity checks. Applications
remain opaque. Dead calls skip only the descent obligation.

`second-descent` is accepted. The seed rejects `other-parameter`, so it now
reports `Invalid check recursive-call`, as do both nest recursion negatives and
the checker recursive-call case. A rebuilt equal parent rejects; a genuinely
smaller rebuilt constructor can decrease. The original seed freezes remain
unchanged. Each legacy Unsupported assertion migration has a separate commit.

A source audit found that eager constructor expansion could perform exponential
work on shared alias DAGs despite bounded recursion depth. The final machine
exposes heads lazily and consumes one transition quota per examined live column,
including aliases, products and fallback. Continuation returns only pop frames
created by charged steps. The resource repair has its own seed-first freeze and
literal work-boundary controls. Resource exhaustion remains distinct from an
Invalid source decision.

All **16 registered gates passed**, exit 0, using
`BEND_NO_TELEMETRY=1 npm run -s gates -- --jobs 1`.
`gates:verify` also exited 0. Exact counts follow; categories overlap and must
not be summed as independent assertions.

| Gate | Passed coverage |
| --- | --- |
| `frontend` | 14 parser fixtures / 28 observations; 24 boundaries; 4 mutants; 12 classification fixtures / 24 lane observations / 72 downstream observations; 7 classification mutants; 4 boundary and 6 classification laws |
| `checker` | 49 fixtures / 98 observations; 10 depth probes; 16 catalog-bound observations; 7 mutants |
| `structural` | 16 fixtures / 64 catalog/compiler observations; 4 boundary pairs; 7 mutants |
| `fields` | 40 fixtures / 240 phase observations; 36 budgets; 6 host probes; 12 level/inspection observations; 9 mutants |
| `wasm` | 25 programs / 90 reference calls in 2 lanes; 62 rejection pairs; 44 boundaries; 7 mutants |
| `wasm-trust` | 3 entries; 0 proof holes |
| `fields-trust` | 4 entries; 0 proof holes |
| `structural-trust` | 2 entries; 0 proof holes |
| `owned-store` | 3,532 cases in 2 lanes; 15 literal witnesses; 6 mutants |
| `flat-store` | 13,621 observations, 3,534 instances, 2 installed boundary states and 7 lifecycle checks per lane; 2 lanes; 9 mutants |
| `recursion` | 19 fixtures / 114 phase observations; 4 fuel probes; 3 mutants |
| `fields-wasm` | 8 fixtures / 32 seed calls; 64 evaluator and 64 Node observations; 50 enum byte checks; 30 boundaries; 4 mutants / 8 lane kills; 5 new checked laws |
| `census` | 36 compiler files; 562 declarations; 40 feature classes |
| `lint:verify` | 127 tests; 8 law-rule wiring controls; no provider contacted |
| `nest` | 40/40 frozen outcomes / 174 seed calls; 0 unmet; 386 evaluator and 386 Wasm values; 24 boundaries; 100 enum hashes; 6 mutants / 12 lane kills |
| `descent` | 38 rule/legacy plus 2 resource seed fixtures; 228 plus 12 phase observations; 20 accepted programs; 24 boundary observations; 7 mutants / 14 lane kills |
| `gates:verify` | 18 wrapper tests; 6 semantic mutants |

The complete normalized runner summary, completion lines, source identities and
measured times are retained in
[`verification.json`](../../tests/compiler-descent/receipts/verification.json).
The final run compared 82 receipt artifacts: 63 identical, 7 volatile-only and
12 semantic. Semantic drift is recorded separately from passing unchanged
assertions. All 2,565 exported source files still matched before refreshing this
increment's own receipt.

The initial four-worker run failed its frontend compile subprocess's unchanged
30-second limit, the stale census inventory and a missing manifest import
closure. The final serial run passed with the same existing test limits.

The new gate fixes 28 new rule fixtures plus 10 legacy transitions, then adds two
independently frozen 32-alias resource fixtures. Its 20 accepted programs produce
40 evaluator observations and 38 direct Wasm observations plus two links to the
checked enum observer for the original structured `second-descent`. Both lanes
compile all 20 accepted programs to byte-identical module pairs. Forty rejected
compilations preserve an existing output marker. The 24 boundary observations
include 14 Exhausted results, two InternalFailure results and eight successes.
The direct descent, recursion and matrix proof entry points all print
`All terms check.`; descent has 23 filled laws. These are algebraic/witness laws,
not a general termination or compiler-refinement theorem.

The seven type-correct semantic mutants are reversed parameter order,
equality accepted as descent, stripping a rebuilt constructor, lexicographic
constructor fields, forgotten local alias, descent required in dead code, and
comparison of an erased parameter. Each is killed by the frozen semantic
observation in both native and Bun lanes: 14 kills. A type error, harness timeout,
resource exhaustion or host failure cannot count as a semantic kill.

Offline style preflight covered 42 changed/new Bend files and 374 declarations,
with zero provider requests. It exited 3: 24 truncated declaration contexts
(3 caller/byte, 8 file, 13 helper limits) and one unavailable whole-selection
composition (125,806 bytes versus 48,000) yield 25 blockers. The explicit
`decreasing-calls` group has 107 declarations over five files and an available
19,466-byte composition, but 17 declaration contexts remain truncated (2
caller/byte, 15 file limits), so it also exits 3. Conceptual compression, Delight,
Memetic identity, Anticipation and Payoff have no live ratings or distributions
in this increment; no automatic style pass is claimed. The coordinator owns live
review. Both full preflight records are retained in
[`style-preflight.json`](../../tests/compiler-descent/receipts/style-preflight.json).

Implementation checkpoints (all carry the requested co-author trailer):

- `95c2c20` Freeze seed decreasing-call expectations for descent-2
- `8a7a61f` Implement seed structural descent and classify same-parameter Invalid
- `fbac98e` Migrate recursion assertion: classify other-parameter Invalid
- `b300897` Migrate recursion assertion: classify rebuilt-parent Invalid
- `c16bb4b` Migrate recursion assertion: classify rebuilt-constructor Invalid
- `23310bf` Migrate recursion assertion: classify computed Invalid
- `c805d0d` Migrate recursion assertion: classify shadow-let Invalid
- `32ae9d2` Migrate recursion assertion: accept second-descent
- `b3a783b` Migrate checker recursive-call assertion to Invalid
- `feebc5c` Migrate nest rec-swapped-args to its frozen Invalid outcome
- `d8647cc` Migrate nest rec-alias to its frozen Invalid outcome
- `d74e0d4` Freeze shared-alias resource controls before descent repair
- `ca5ac20` Bound descent comparison work while preserving seed decisions

The report and normalized final receipts are committed in a following evidence checkpoint.

Generated census source inventories were refreshed because the census gate
checks their exact current bytes. Existing gates' shared execution receipts were
not refreshed or committed; the coordinator owns their post-integration refresh.
Only this gate's execution receipt is updated here. Build products and detailed
local process logs remain ignored.

Limits: the supported profile remains monomorphic and first-order. Generics,
literals and other unsupported forms retain their specific frontend codes.
Knot checks arguments before the descent decision, whereas the seed inspects the
raw spine first, so multiply-invalid calls can differ in diagnostic precedence.
The quota applies per examined parameter column; source-size-bounded list scans
occur inside transitions. A seed-accepted input may exhaust this conservative
quota. No performance improvement or general semantic soundness claim is made.

Next: the coordinator reviews this increment against any subsequent fixes to the
`nest` base, performs bounded live style review, merges, and refreshes shared
receipts. Any future generic/literal extension must preserve specific Unsupported
boundaries until its own seed-first differential and mutant gates exist. No push,
merge, rebase, network access, credential read or other-worktree edit was made.
