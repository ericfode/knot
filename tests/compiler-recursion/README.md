# Structural recursion checkpoint

`campaign/recursion` adds a first-parameter field-descent rule to the checker.
`Scope.smaller` holds strict descendant lexical levels independently of the
ordered match frontier. Opening fields propagates membership; `call_result`
admits a self-call only when the first checked argument is a marked Reference.
The existing evaluator executes these calls without modification.

The [contract](SPEC.md), [frozen expectations](cases.json), and
[law review](LAW_REVIEW.md) define the boundary. The Wasm emitter is unchanged.
The only existing test-source edit supplies the added Scope field to
`tests/compiler-fields/bounds.bend`; every preexisting assertion is unchanged.

## Reproduction

Always export `BEND_NO_TELEMETRY=1`. No credentials or network are needed.

```sh
export BEND_NO_TELEMETRY=1
python3 tests/compiler-recursion/check.py
bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts src/recursion-PROOF.bend
node scripts/perch-style.mjs --preflight --task=tests/compiler-recursion/SPEC.md \
  src/scope.bend src/patterns.bend src/check.bend \
  src/recursion-LAWS.bend src/recursion-PROOF.bend \
  tests/compiler-fields/bounds.bend tests/compiler-recursion/fixtures/*.bend
```

`--reference-only` was run before implementation and wrote the immutable
`receipts/reference.json`. Normal runs verify those fixture/expectation hashes
and rerun the seed observations; they never infer new expected results.
The seed prints Zero/Succ trees using Nat sugar; the manifest independently
fixes Knot's constructor-tree spelling. The 19 fixtures comprise 11 positives
and eight negative capability/order cases. Each negative names a valid control.

| Required gate | Recorded passing observations |
| --- | --- |
| `tests/subsets/check_frontend.py` | 14 reference fixtures, two parser lanes (28 fixture observations), 24 boundaries, 4 laws, 4 semantic mutants |
| `tests/compiler-checker/check.py` | 49 reference fixtures, 98 checked observations, 10 depth + 16 catalog bounds, 7 semantic mutants |
| `tests/compiler-structural/check.py` | 16 reference fixtures, 64 catalog/compiler phase observations, 4 boundary pairs, 7 semantic mutants |
| `tests/compiler-fields/check.py` | 40 reference fixtures, 240 phase observations, 36 budgets, 6 host + 12 level/inspection observations, 9 semantic mutants |
| `tests/compiler-wasm/check.py` | 25 programs, 90 independent reference calls, 180 evaluator + 180 Wasm observations, 64 rejection pairs, 44 boundaries, 7 semantic mutants |
| `tests/compiler-wasm/trust.ts` | 3 entries, zero holes; host capabilities unchanged |
| `tests/compiler-fields/trust.ts` | 4 entries, zero holes; host capabilities unchanged |
| `tests/compiler-structural/trust.ts` | 2 entries, zero holes; host capabilities unchanged |
| `research/owned-store/check.py` | 3,532 cases per backend, 15 literal witnesses, 5 ownership fixtures, 4 generation-boundary observations, 6 semantic mutants |
| `research/flat-store/check.py` | 3,534 instances per backend, including 2 installed boundary states; 7 lifecycle checks per backend, 9 semantic mutants; identical 1,050-byte modules |
| `npm run -s lint:verify` | 103 tests, 0 failures; eight law rules and packet wiring pass |
| `tests/compiler-recursion/check.py` | 19 reference fixtures, 114 phase observations, 4 fuel probes, 3 semantic mutants |
| `src/recursion-PROOF.bend` | `All terms check.`; 16 new filled laws, 50 laws in the complete proof closure |

All 1,534 captured command observations in the seven regenerated deterministic
gate receipts match the branch baseline after normalizing checkout paths.
All 25 enum Wasm binaries are byte-identical to that baseline. All three trust
inventories retain their entries, native/unsafe dependencies and host effects.
`receipts/regression-comparison.json` records the compared hashes and counts.
Compiler receipts are regenerated because source/build identities changed;
store receipts with only path, timing or gzip-header changes were restored.

The first lint run could not create the tree-sitter cache lock in the read-only
user cache. Copying the installed manifest and parser libraries into ignored
`.local/compiler-recursion/parser-cache` and setting
`TREE_SITTER_LANGUAGE_PACK_CACHE_DIR` to that directory made the unchanged gate
pass. `receipts/regressions.json` retains both attempts and the cache hashes.

## Fixtures and mutants

- `even`, `add`, `mirror`, `length`: multiple base/recursive cases, nested descent,
  asymmetric field order, and a non-first recursive field.
- `direct`, `first-parameter`, `ordered-calls`, `shadow-field`, `after-let`:
  nearby valid controls and identity/frontier separation.
- `deep`, `deep-input`: a fixed 64-successor input. Both succeed with 65,536
  transitions. At 600, construction still succeeds and recursion reports
  `Exhausted eval budget`.
- `same-parameter`, `other-parameter`, `rebuilt-parent`, `rebuilt-constructor`,
  `computed`, `shadow-let`, `second-descent`: `Unsupported check recursive-call`.
- `mutual`: `Invalid check forward-live-call`, unchanged from the earlier rule.

All three mutants typecheck with the seed and are killed by fixed observations:
admitting every self-call incorrectly checks `same-parameter`; suppressing field
propagation rejects `direct`; suppressing nested propagation rejects `even`.
The latter two report `Unsupported check recursive-call`, as required for a
semantic kill. No crash, missing import or timeout counts as a kill.

The pinned seed rejects the six nondecreasing/computed cases with its own
decreasing-self-call diagnostic. It accepts `second-descent` (lexicographic
descent on parameter 1), which Knot conservatively leaves Unsupported. This is
the observed reference boundary, rather than the task's general-recursion premise.

## Review and integration limits

Offline preflight covered all 174 declarations in 25 changed/new Bend files:
nine contexts truncate, and the full group exceeds the composition limit
(76,328 / 48,000 bytes). The separately bounded seven-declaration descent family
has zero truncations, no unresolved dependencies, and available composition
context (47,903 / 48,000 bytes). See `receipts/preflight*.json` for exact targets.
There were zero provider requests. Compression, Delight, Memetic identity,
Anticipation and Payoff remain unscored; live Perch belongs to the coordinator.

Recursion is checked and evaluated only. The next increment must integrate the
fields-wasm branch, preserve its heap/exhaustion contract, and add the recursive
fixtures to seed/evaluator/actual-Wasm differential execution. Broader descent,
local aliases, nested constructor patterns and structured host arguments remain
outside this profile. No performance or general checker-soundness theorem is claimed.

This executor's sandbox makes the shared Git metadata read-only. The verified
changes remain in this worktree; an isolated commit/bundle under ignored
`.local/compiler-recursion/` provides the coordinator's Git handoff. The actual
shared branch cannot be advanced from this sandbox.
