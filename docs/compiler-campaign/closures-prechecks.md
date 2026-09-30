# Closures pre-review repairs, 2026-09-29

This is the executor-owned follow-up to the historical
[refresh](closures-refresh.md). All changes, builds and commits are confined to
`campaign/closures`. Main was not merged; the executor instruction forbids it.
No other worktree was written, no `.env` was read or copied, and no provider,
live Perch, push or rebase was used. Commands export `BEND_NO_TELEMETRY=1`.

## Frozen evidence and repair

`fc45c5a3` freezes the 13 unique major/blocking C1 witnesses plus ten neighboring
controls before compiler edits. `8a519299` adds a newly exposed nonleading
template marker and two grouped typed-comparison controls before their repairs.
All previous rows remain identical. `prechecks.json` records 26 seed parse/check
verdicts and 52 native/Bun builds: six accepted books, twelve syntax rejections
and eight parse-valid type/check rejections. Native acceptance uses an import-Base
wrapper without modifying the original source; rejection builds use the source.

The arrow reader now distinguishes an unclosed untyped `<` and `<-` from a
closed out-of-profile family application. Grouped typed comparisons stay
Unsupported. Optional parameter commas follow the seed, including an erased
parameter after an arrow type; a nonleading template marker remains Invalid.
The SPEC prefix-only table records all three out-of-profile type codes.
Braced patterns require a matching constructor declared earlier in the source;
the visibility check compares source offsets and does not depend on AST list
order. Ordinary constructor terms retain forward references.

The checker/evaluator/emitter algorithms are unchanged. Four local visibility
laws supplement the unchanged 24 closure laws; they do not prove the general
visibility relation or the still-open capture/application preservation theorem.
Three added mutants must typecheck and exhibit their precise wrong parse
verdict in both lanes. All original frozen expectations, laws and five closure
mutants remain unchanged. No source budget or frozen assertion is weakened.

## C1 disposition

The original report has 29 conditions: 16 major/blocking and 13 undocumented
prefix minors. Fourteen major/blocking defects are repaired, and the prefix
policy is now explicit. A newly exposed nonleading-template condition
`f74331a573ccd15b4f26` is also repaired. The only retained conditions are the
two host-result findings below; neither is treated as a C1 pass.

- `7c0871a3666be44005dc` (`crash`): disputed. The exact source
  `b507406b7c59d76848eda88770afed980dd4a861ba9bbc3a10292b90f6588ef2`
  parses, checks and returns `invert` in the seed. It returns a function value.
  The unchanged `src/CONTRACT.json` host boundary explicitly requires
  `HostFailure invoke function-result` for that evaluator request. Knot parses,
  checks and builds the book, then exits 5 with that exact classified diagnostic
  at observation. C1 flags every HostFailure as a crash even though HostFailure
  is one of its five documented outcome classes. Its displayed program is only
  the first 240 characters; the full frozen source includes the `invert` body.
- `5a7d3ec9413a356cc1ef` (`diagnostic-shape`): disputed. `syntax.Error.Host`
  stores phase/code, and the unchanged `diagnostic.error` prints the documented
  three-column host diagnostic. `src/SPEC.md` requests offsets where available;
  this ABI refusal has no source span. Adding a fictitious span or changing it
  into a language refusal would alter the frozen host contract. The added gate
  requires the exact existing diagnostic independently in native and Bun lanes.

The complete sources, seed verdicts and original fingerprints are in
`tests/compiler-closures/prechecks.json`; the original C1 report is preserved in
`tests/compiler-closures/receipts/prechecks-before.json`. The coordinator may
adjudicate the two disputes in its ledger. This executor changes neither C1 nor
the coordinator ledger to suppress them.

## Verification and integration boundary

The first full run failed frontend on the AST-order guard, lint:verify on the
missing manifest closure, and closures on a new harness expected-value shape.
Its full unsuccessful summary is preserved in `precheck-first-gates.json`.
The other twelve gates passed. Those failures prompted the source-offset
repair, closed manifest entries and harness correction; no failed attempt is
counted as acceptance or a mutant kill.

The accepted command was `BEND_NO_TELEMETRY=1 npm run -s gates -- --jobs 2
--keep-scratch`: exit **0**, all **15** registered gates passed. The complete
summary is [precheck-gates.json](../../tests/compiler-closures/receipts/precheck-gates.json);
the full source/seed/runtime/proof/mutant receipt is
[precheck-closures.json](../../tests/compiler-closures/receipts/precheck-closures.json).
All 176 accepted closure input hashes match this worktree. The
[scope receipt](../../tests/compiler-closures/receipts/precheck-scope.json) checks
all 100 original fixture/oracle/expectation/law/proof/mutant files byte for byte
against `0dcc51a0`. The 32-program refresh still contributes 32 seed checks,
64 native/Bun builds, 40 seed calls and 192 Knot phase observations.

Every row below has status **passed** and exit **0**. Counts overlap; they are
not summed into a test total. The 19 blocked generic calls remain excluded.

| Gate | Exact counts |
| --- | --- |
| `frontend` | `{"boundaries": 24, "fixtures": 14, "lane_observations": 28, "mutants": 4}` |
| `checker` | `{"bound_observations": 16, "bounds": 2, "budgets": 10, "fixtures": 49, "lane_observations": 98, "mutants": 7}` |
| `structural` | `{"bounds": 4, "fixtures": 16, "lane_observations": 64, "mutants": 7}` |
| `fields` | `{"bound_observations": 12, "bounds": 2, "budgets": 36, "fixtures": 40, "host_boundaries": 6, "lane_observations": 240, "mutants": 9}` |
| `wasm` | `{"boundaries": 44, "execution_lanes": 2, "fixtures": 25, "mutants": 7, "reference_calls": 90, "rejects": 64}` |
| `wasm-trust` | `{"entries": 3, "proof_holes": 0}` |
| `fields-trust` | `{"entries": 4, "proof_holes": 0}` |
| `structural-trust` | `{"entries": 2, "proof_holes": 0}` |
| `owned-store` | `{"cases": 3532, "execution_lanes": 2, "literal_witnesses": 15, "mutants": 6}` |
| `flat-store` | `{"bun": {"installed_boundary_states": 2, "instances": 3534, "lifecycle_checks": 7, "observations": 13621}, "mutants": 9, "native": {"installed_boundary_states": 2, "instances": 3534, "lifecycle_checks": 7, "observations": 13621}}` |
| `recursion` | `{"fixtures": 19, "mutants": 3}` |
| `fields-wasm` | `{"boundaries": 30, "fixtures": 8, "mutants": 4}` |
| `census` | `{"classes": 40, "declarations": 598, "files": 42}` |
| `lint:verify` | `{"law_rules": 8, "tests": 127}` |
| `closures` | `{"agreed_fixtures": 49, "blocked_calls": 19, "blocked_fixtures": 1, "boundaries": 14, "boundary_probes": 14, "byte_identity_checks": 49, "check_observations": 174, "checked_laws": 28, "compile_observations": 174, "evaluator_calls": 578, "fixtures": 87, "frozen_fixtures": 42, "mutant_lane_kills": 10, "mutants": 5, "prechecks": {"byte_identity_checks": 6, "check_observations": 52, "compile_observations": 52, "eval_observations": 46, "host_result_refusals": 2, "mutant_lane_kills": 6, "mutants": 3, "parse_observations": 52, "programs": 26, "wasm_calls": 4}, "proof_entries": 4, "refresh_fixtures": 32, "refresh_phase_observations": 192, "refresh_seed_builds": 64, "refresh_seed_calls": 40, "refresh_seed_checks": 32, "refresh_seed_rejections": 12, "regression_fixtures": 11, "regression_phase_observations": 66, "regression_seed_calls": 8, "regression_seed_rejections": 3, "rejected_fixtures": 37, "rejection_evaluator_observations": 76, "seed_calls": 292, "seed_rejections": 18, "supplemental_probes": 2, "supplemental_seed_calls": 8, "wasm_calls": 578}` |

The precheck seed replay independently reports 26 parses, 26 checks and 52
native/Bun builds (six accepted, twenty rejected). The precheck Knot subsection
has 52 parses, 52 checks, 52 compilations, 46 eval observations, two exact host
refusals, four Node Wasm calls, six byte-identity comparisons and six semantic
mutant kills across three mutants. The original five closure mutants retain
their ten lane kills. Four complete proof entries fill 28 laws with no holes.
The separate manifest test passes 20 tests; the whole-run offline lint gate
passes 127 tests and eight law-rule wiring controls, with no model rating.

Census is current: 42 compiler files, 598 declaration events, 514 unique
declarations, 381 definitions and 40 feature classes. Generated inventories and
approved policy come from `census:approve`/`census`, with the approval summaries
included in the implementation commit. Tool observations are Bun 1.3.14,
Node v22.22.3, Python 3.14.3 and wasm2wat 1.0.41.

All D21/D24/D26 merge obligations remain in `closures-refresh.md`. The
coordinator integrates nest/modules/descent before closures, reconciles the
function-field, closure-parameter, closure-apply and continuation pins, adapts
imported-constructor visibility to the modules context, regenerates merged
census/shared receipts and qualifies live Perch. Generics must run the unchanged
19 blocked chooser calls. Conceptual compression, Delight, Memetic identity,
Anticipation, Payoff and composition have no live rating here. The open general
capture/application law stays required under D21.
