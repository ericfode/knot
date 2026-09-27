# Driver pipeline acceptance packet

Scope: the public `checked`, `parsed`, `source` entry points, new `parsed_root`
projection and unchanged `load` boundary in `src/driver.bend`. Fixed contract:
[SPEC.md](SPEC.md). Frozen inputs: [freeze.json](freeze.json). Candidate:
`4641537cb3b8d82a63ff519007d43ba6efc4f4458e656c12c1b83186a5c72a15`.
One generation passed the first compiler check; no diagnostic retry occurred.

## Claims and their limits

No new theorem, axiom or proof body is introduced. Five unchanged complete
proof entry points (`PROOF`, `check-PROOF`, `runtime-PROOF`, `fields-PROOF`,
`catalog-PROOF`) returned `All terms check.` in the existing suites. These prove
their existing stated claims; they do not prove universal driver equivalence.
Driver preservation is supported by finite native/Bun observations, immutable
independent fixture expectations, source review and exact emitted-byte comparison.
Seed Bend 2.0.29 / `574b6d3`, its checker/native backend, Bun, Base IO and Node's
Wasm engine remain trust dependencies. Model judgments are advisory.

## Public observations

| Operation | Constructible success witness | Failure/boundary observation |
| --- | --- | --- |
| `checked` | An empty `C.Book`; output is exactly `Before`, `Next`, `After`. | Each of five explicit `S.Error` constructors retains status, message, location and stream; no `Next` or `After`. |
| `parsed` | An empty sequence plus one residual token, with zero character/parser fuel and positive checker fuel, invokes `Next` once. | An injected parse error wins even with zero checker fuel; a successful parse with zero checker fuel reports checker exhaustion. Residual tokens remain deliberately ignored. |
| `source` | Empty text and zero character fuel succeed with positive parser/checker fuel. | Existing Wasm integration covers separate character/parser/checker exhaustion, invalid and unsupported source; direct source witness fixes callback order. |
| `load` | Existing evaluator and compiler corpus traverses file open/read/close and the shared driver. | Existing fields suite includes six host probes; failed compilation and exhaustion do not create an artifact or overwrite the preserved output marker. |
| `parsed_root` | Its matched `P.Parsed` contains an inhabited syntax sequence and residual list. | It returns the root and deliberately discards the residual tokens; direct `parsed` witnesses observe the resulting public behavior. |

[witnesses.json](witnesses.json) fixes literal expectations before generation.
All ten cases pass in both native and Bun lanes before and after (20 observations
per revision). Each is a runtime example, not a quantified law. IO traces observe
order and multiplicity, not wall-clock timing. Existing source fixtures, expected
diagnostics, theorem statements and assertion bodies were unchanged.

The pipeline is stateless except for its final IO continuation. Fuel belongs to
the supplied stage, never to a shared counter. Independent tests preserve the
original complete compiler observations. Error precedence follows the explicit
`syntax.bind` Fail/Done cases and is exercised by the direct incoming-failure
witness. No new arithmetic, storage index, allocation policy or GPU reachability
is introduced. These categories impose no new driver-specific law in this diff.

## Deterministic evidence

All existing suites passed: frontend (14 fixtures, 24 boundaries, 4 mutants),
checker (49 fixtures, 98 observations, 10 depth/16 catalog-bound observations,
7 mutants), Wasm (25 programs, 90 independent calls in two lanes, 64 rejection
pairs, 44 boundaries, 7 mutants), fields (40 fixtures, 240 phase observations,
36 budgets, 6 host probes, 12 level/inspection observations, 9 mutants), and
structural catalog (16 fixtures, 4 boundary pairs, 7 mutants).

Their 34 existing mutants first parse/type-check and then violate unchanged
observations. No new driver-specific mutant was introduced, and the existing
mutation coverage must not be described as exhaustive driver equivalence.
Complete machine records are the `receipts/candidate-*.json` files. The launcher
redirects build/receipt destinations only, preserving each test module's code.
The 25 Wasm modules emitted by the candidate match the fresh baseline byte for
byte. This is finite artifact equality, not a performance or bootstrap result.

Targeted semantic review ran four rules on each changed declaration, 12 completed
checks with no reported findings. The `parsed` and `source` dependency contexts
were truncated. Compression/delight ratings meet their targets, but memetic
ratings do not; normal composition review is unavailable. The supplementary
packet assumes explicit opaque stage interfaces and cannot supply an automatic
complete-composition pass. No review score licenses language acceptance.
