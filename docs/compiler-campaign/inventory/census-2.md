# census-2: accepted evidence and self-hosting meter

Implemented on `campaign/census-2`, based on `d14418b`. The
[execution receipt](../../../tools/census/receipts/census-2.json) records source
hashes, normalized gate results and reviewed branch-format pins.

## Change and scope

Accepted evidence now discovers every literal registration in
`scripts/gates/run.py`, plus `tests/compiler-*` fixture manifests. Thirteen
explicit suite adapters preserve parse, catalog, check, evaluator and Wasm
boundaries. Unknown formats are reported, never interpreted by resemblance.
The current inventory contains 171 fixtures in seven suites, 140 distinct files,
13 check/evaluator classes and 12 Wasm classes. Recursion and fields-Wasm are
included. Compile success alone supplies no Wasm execution evidence. Frozen
failures and permitted alternatives never supply positive evidence.

`npm run census:meter` computes a read-only summary; `selfhost.json` records the
full rankings and each declaration's gaps, linked to its three input manifests
by SHA-256. The selected closure is the existing JS runtime/type upper bound.
Its 328 compiler declarations consist of 242 compiler, 14 package and 72 Base
entries; the frontend has 87 (48 compiler, 39 Base). Both check and Wasm counts
are currently zero because no declaration has every required class evidenced.
Law/proof files are excluded. Filled laws in ordinary files that implement
runtime functions remain counted, with law/fill features merged by identity.

The approval policy and feature taxonomy are unchanged. There are no new
`src/*.bend` files, imports or implementation classes, so no approval extension
or style-manifest group is needed. The existing `census --check` registration
now verifies five manifests; no gate registration was added.

The original census test's integration snapshot predated the first wave:
`expected.json` still said 37 frontend definitions and 37 Base closure entries,
while both committed integration inventories already said 41 and 39. Only those
two snapshot values were refreshed. The census assertion that fields lacked
Wasm evidence was updated for this increment's explicitly requested new suite;
the failure-classification mutant follows its function into `evidence.mjs`.
No compiler-suite source, fixture, assertion, gate-runner code or shared receipt
was edited.

## Executed verification

`BEND_NO_TELEMETRY=1 npm run -s gates` exited **0**, all **14 gates passed**.
The scratch run compared 80 artifacts: **63 identical, 17 volatile-only,
0 semantic drift**. Shared receipts were never written in this checkout.
Pass categories overlap and are not summed into a single assertion count.

| Gate | Exact passed coverage |
|---|---|
| frontend | 14 reference fixtures; 28 parser-lane observations; 24 boundaries; 4 boundary laws; 4 mutants. Classification: 12 fixtures in 2 lanes, 6 laws, 7 mutants, 72 downstream rejection observations |
| checker | 49 fixtures; 98 lane observations; 10 budget probes; 2 catalog bounds / 16 bound observations; 7 mutants |
| structural | 16 fixtures; 64 lane observations; 4 boundary pairs; 7 mutants |
| fields | 40 fixtures; 240 phase observations; 36 budget probes; 6 host probes; 2 bounds / 12 level-inspection observations; 9 mutants |
| wasm | 25 programs; 90 independent reference calls in 2 execution lanes; 64 rejection pairs; 44 boundaries; 7 mutants |
| wasm-trust | 3 entries; 0 proof holes |
| fields-trust | 4 entries; 0 proof holes |
| structural-trust | 2 entries; 0 proof holes |
| owned-store | 3,532 cases in each of 2 lanes; 15 literal witnesses; 6 mutants |
| flat-store | In each of 2 lanes: 3,534 instances, 13,621 observations, 2 installed boundary states, 7 lifecycle checks; 9 mutants |
| recursion | 19 seed fixtures; 114 phase observations; 4 fuel probes; 3 mutants |
| fields-wasm | 8 fixtures; 32 seed calls; 64 evaluator and 64 Node observations; 50 enum-byte checks; 30 boundaries; 4 mutants killed in both lanes; 5 checked laws |
| census | 30 compiler source files; 425 declaration events; 40 classes; all 5 generated manifests current |
| lint:verify | 127 tests; 8 law-rule wiring controls; 0 provider requests |

`npm run -s gates:verify` passed **18/18 tests**, including six executable
gate-runner mutants. `npm run -s census:test` passed **68/68 tests**, including
three complete pinned-seed checks of the unchanged Bend fixtures and seven
semantic census mutants. Each new mutant first passes JavaScript syntax
validation, then executes and violates the unchanged literal observation.

The new fixtures are `tools/census/fixtures/adapters.json` (13 small suite-format
controls) and `meter.json` (literal closure, evidence, counts, ranked blockers and
per-declaration gaps). Tests cover unknown formats, invalid JSON, exact stage
outcomes, companion-manifest joins, ambiguous requirements, frozen hashes,
module bundle pins, deterministic ordering, duplicate identities and read-only
CLI behavior. The new mutants are:

| Mutation | Independent observation that kills it |
|---|---|
| Count a failed fixture as evidence | Each of Invalid, Unsupported, Exhausted, HostFailure, InternalFailure and Unfixed has an empty positive class evidence set |
| Guess the Wasm adapter for an unknown suite | A lambda class present only in that unknown suite has no check evidence |
| Count a law-file helper as compiler code | The literal denominator remains 3, with check count 2 and Wasm count 1 |

Contradictory agreement/failure records are unknown formats, never silently
converted to success. Missing-module analysis preserves HostFailure separately
from the expected compiler outcome and normalizes checkout paths to `$ROOT`;
an independent relocation control verifies identical inventory bytes.

Repeated generation is byte-identical for all five manifests. The meter CLI is
also byte-identical across runs and does not write inventory or approval files.
Offline style preflight is **not applicable: 0 changed Bend files**. No new law
requires a proof entry. Existing proof entries ran inside their unchanged gates;
live Perch review and ratings remain the coordinator's responsibility.

## Future-format checks

Read via `git show` from these exact branch commits, exported only to ignored
scratch, and inventoried successfully. This checks adapter interpretation,
frozen source hashes and parser coverage. It does not execute the future compiler
gates or claim these capabilities are implemented. None of these fixtures enter
the current checkout's accepted evidence before integration.

| Branch | Commit | Fixtures |
|---|---|---:|
| campaign/nest | `997f83fdfb48f336353ae663346686633926baa5` | 40 |
| campaign/modules | `722fc1d0c6ffaa1ad3a791f7ff2b8f0e7ddb6795` | 42 |
| campaign/literals | `5a7bd5ff6a0dec42b2555bd563a79bd6143ca301` | 40 |
| campaign/generics | `66e83371fd002801d05cf195cbd57a2cb217ac39` | 40 |
| campaign/closures | `8dbd4145170dd773376b0dbfccf9511f5091d127` | 40 |
| campaign/baseslice | `8ac39f31286e454bbf916472081f7da38f356a7a` | 40 |

The controls preserve two important boundaries: nest's empty call domain still
has a frozen `main` execution; fields-Wasm's `deep-call` exhausts evaluation and
`arena-overflow` exhausts Wasm. These do not silently become successes. Module
fixtures use their own hash-verified local bundle, with no fallback to a cache
or hub. Optional acceptance in generics/closures/baseslice stays `Unfixed`.

## Remaining boundary and next increment

The meter measures coarse feature-class coverage from frozen expectations. It
does not infer general support, interaction correctness, runtime ABI readiness
or fresh gate execution. Higher-order flow, template instances and a complete
checked source bundle remain outside this closure approximation. Base host and
intrinsic operations still need their own lowering/ABI evidence.

After merging a capability suite, regenerate and check the census to expose
its effect on missing-class rankings. Add an adapter and literal controls if
the committed format has changed. The coordinator owns integration, live Perch
review and any shared receipt refresh; this executor neither merged nor pushed.
