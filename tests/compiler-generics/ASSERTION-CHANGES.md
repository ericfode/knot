# Changes to existing gate assertions

D7 and the executor prompt say that existing gate assertions do not change.
At `f39ba7e` the only such change was the restated `generic_header` law in
`src/LAWS.bend` and `src/PROOF.bend`, which the original task required.
`git diff --stat 690bfc6 f39ba7e` is empty over every other file below. Later
rounds changed assertions in the frontend, classification
and census tests. This ledger lists each change with its commit, the
authorization text and its status. Gate runs pass only with these changes, so
they need the coordinator's explicit confirmation or rejection before merge.

The round-1 and round-2 tasks are the coordinator's executor prompts for
those rounds. They are quoted here because they are not in the repository.

**Status** takes three values:

- *authorized*: coordinator text explicitly covers the change.
- *required*: a confirmed review finding demanded the change, and the executor
  chose its form.
- *unconfirmed*: the executor made the change, and no coordinator text
  covers it yet.

| # | File | Commit | Change | Authorization | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | `tests/subsets/classification-cases.json`, case `generic` | `5eea108` | The pin `Unsupported parse generic-datatype 8:9:1:8` becomes phase expectations: parse `Parsed`, check `Checked`, eval `Box{On{}}`, and compile `Unsupported check constructor-fields 30:33:2:2`. The old pin is kept under `superseded`. | Round-1 task: "COORDINATOR AUTHORIZATION ... is superseded by this increment. You are authorized to replace it in ONE separate commit" | authorized |
| 2 | `tests/subsets/check_frontend.py` | `5eea108` | `expectation()`/`observed()` read a case's `phases`, match `stdout`/`stdout_prefix`, and require artifact preservation only for a failing compile. The summary says "downstream phase observations". | Same text: "Use phase-specific expectations". The harness must read them, but the text does not describe these mechanics. | authorized in substance; mechanics unconfirmed |
| 3 | `check_frontend.py` mutant and `classification/function-parameter.bend` | `5eea108` | `generic-invalid` becomes `parameter-type-invalid` on `unsupported(rest,"parameter-type")`. Its witness is a new seed-valid case (seed `On{}`), because the only manifest witness (`application-parameter`) now parses. The frontend count goes from 29 to 30 cases, and 174 to 180 observations. | Round-1 task: retarget "for example `unsupported(rest,\"parameter-type\")`"; the round-1 finding: "or a new still-Unsupported fixture". The count stays at 7. | authorized |
| 4 | `classification-cases.json`, six classify-2 cases: `application-{parameter,return,binding}` and their `-after-prefix` twins | `78c4942` | The three seed-valid cases get phase expectations. The twins move to `Unsupported parse type-expression`, a precision loss against classify-2's Invalid. Old pins are kept under `superseded`. | `78c4942` (committed by the coordinator): "Coordinator authorization (2026-09-28)". Round-2 task: "now carries the coordinator-authorized supersession". The `by` fields said "awaiting coordinator authorization" until review round 4 corrected them. | authorized |
| 5 | `src/LAWS.bend`, `src/PROOF.bend` | `f39ba7e`, `78c4942`, `4e73b6c` | `generic_header` restated as parser acceptance (`f39ba7e`), with touching spans for `Type>` (`4e73b6c`). `return_type_application` restated as the typed-result transition, and `binding_type_application` retired (`78c4942`). | Original task and round-1 task: "restate or retire that law". `78c4942` as in row 4. The span restatement in `4e73b6c` came from a self-found repair. | authorized; `4e73b6c` spans unconfirmed |
| 6 | `tests/compiler-classification/check.py` | `78c4942`, `d3cee9f` | `78c4942` deleted three mutants (6 to 3). `d3cee9f` takes a file and a witness list per mutant, checks each witness's hash and unmutated outcome, and kills 7 mutants on 9 witnesses. The law summary moves from 16 laws to 17. | Round-2 finding: "Retarget `parameter-application-invalid` ... Add a type-correct mutant that demotes type-parse.bend's `Unsupported{...type-expression...}` ... restore the gate's kill count". | required for `parameter-application-invalid` and `type-expression-invalid`; the two route mutants and the witness mechanics unconfirmed |
| 7 | `tools/census/fixtures/expected.json` | `6086dfa` | `frontend_definitions` 41 to 47. Generics adds six definitions reachable from `lex.tokenize`/`parse.parse`: `type_then`, `wrap_generic`, `plain_parameters`, `wrap_typed_function`, `generic_parameter` and `typed_result`. | Round-3 finding reported `census:test` at 73/75; no text chose this repair. | unconfirmed |
| 8 | `tools/census/tests/evidence.test.mjs` | `6086dfa` | `recursion.wasm.evidence` changes from `[]` to the generics fixtures `quantity-parity.bend` and `seq-parity.bend`. | As in row 7. | unconfirmed |
| 9 | `docs/compiler-campaign/inventory/accepted.json` (generated) | `cac8dd2` (census regenerated at the round-1 merge) | `recursion.wasm` changes from `no-positive-fixture-evidence` to `observed-in-successful-fixtures`, driven by the generics receipt rather than by the recursion increment's own evidence. Every call of the two fixtures agreed in the evaluator and in Node Wasm, in both lanes. | none | proposed campaign decision; unconfirmed |

## Before and after

Direct runs on scratch exports of main `c0bd08d` and this branch (review
round 4, `BEND_NO_TELEMETRY=1`). The frontend tip run used the runner's
`KNOT_GATE_TIMEOUT_SCALE=4`. At scale 1, under load average about 30, its
first build exhausted the 30-second budget. That was a host timeout, not an
assertion result.

| Gate | main `c0bd08d` | branch |
| --- | --- | --- |
| `python3 tests/subsets/check_frontend.py` | `PASS: 14 reference fixtures, two parser lanes, 24 boundary observations, four boundary laws, six classification laws and four semantic mutants; 29 classification fixtures in two lanes, 7 classification mutants, 174 downstream rejection observations` | `... 30 classification fixtures in two lanes, 7 classification mutants, 180 downstream phase observations` |
| `python3 tests/compiler-classification/check.py` | `PASS: 17 frozen seed outputs; 17 parser observations; 6 type-correct semantic mutants killed; 16 filled frontend laws (6 added, 1 narrowed).` | `PASS: 17 frozen seed outputs; 17 parser observations; 7 type-correct semantic mutants killed on 9 witnesses; 17 filled frontend laws (classify-2: 5 added, 1 narrowed; generics: 1 restated, 1 retired, 2 added).` |
| `npm run -s census:test` | 75 tests, 75 pass | 75 tests, 75 pass (73 without rows 7 and 8) |

The gate runner's `counts` for the frontend (14/28/24/4) are the same on both
trees, because they omit the classification sub-counts that changed. A reviewer
comparing runner summaries alone would not see rows 1 to 3.

## Not assertion changes

The following behavior changes are covered by other records:

- The monomorphic path now reports some seed-valid books Unsupported where
  main reports Invalid: empty datatypes (`88e204b`), bare definition references
  (`c52929b`) and type-valued terms (`f39ba7e`). No main assertion pins those
  Invalid outcomes. The only related main pins, checker `erased-free-name` and
  `unknown-type` and structural `unknown-type`, are seed-invalid and still
  pass.
- The runner registration in `scripts/gates/run.py`, the census approvals in
  `tools/census/approved.json` and the style-manifest groups are the additions
  the executor prompt requires.
