# census-2 review round 2: gated evidence and frozen requirements

Merged main `fa31fec` into `campaign/census-2` as `4aaffbd`, as requested.
The merged tree reproduced all four reported failures: **64/68 census tests
passed** before the repair. The frozen closures, baseslice, generics and literals
suites had been admitted as positive evidence before any Knot gate ran them.

Each adapter now names its gate. A recognized suite contributes accepted
evidence only when that exact registration invokes a program in the suite
directory. A trust gate sharing the directory, a different gate name, or the
right name pointing elsewhere cannot admit it. Known adapter directories stay
discoverable even when their gate is removed. Unknown formats remain excluded.

`accepted.json` schema 3 separates ungated suites, fixture records and class
requirements from evidence. `selfhost.json` schema 2 retains the pending suites
and per-class, per-stage fixture lists under `requirements`. Only unconditional
success at a stage supplies positive coverage. Failed or ambiguous expectations
remain recorded without contributing coverage at that stage.

| Closure | Evidenced check / Wasm | Covered by evidence + frozen requirements check / Wasm |
|---|---|---|
| Compiler, 328 declarations | 0 / 0 | 93 / 93 |
| Frontend, 87 declarations | 0 / 0 | 55 / 55 |

The inclusive second count is planned class coverage. Registration moves a
suite from requirements to evidence without dropping that count. All **171**
original evidence fixtures and all original class evidence sets are preserved
exactly, apart from the added gate/admission metadata. There are **162** ungated
requirements: baseslice 40, closures 42, generics 40 and literals 40. The
`string-reverse-word.bend` Wasm requirement is no longer accepted evidence.

## Fixed controls and mutation

`tools/census/fixtures/requirements.json` fixes the new observations by literal
review before implementation. The first six tests all failed against the old
code. It reuses the existing seed-checked `lambda.bend` and three-declaration
meter control; no Bend source or law was added.

Seven new tests cover ungated exclusion and requirement provenance, gate name
and directory matching, frontend discovery after gate removal, the merged
baseslice regression, both meter counts and remaining gaps, promotion without
double counting, and the new mutant. The integration control allows later suites
to arrive and their real gates to land; the isolated ungated regression always
runs.

The new semantic mutant removes the evidence admission filter and counts every
record. It passes JavaScript syntax checking, executes, and is killed by the
same literal assertion requiring zero lambda evidence from an ungated suite.
The census now kills **8 semantic mutants** in total. The two existing synthetic
module tests gained gate registrations in their setup; their assertions and
source/expected fixtures are unchanged. No compiler gate assertion changed.

## Executed verification

`BEND_NO_TELEMETRY=1 npm run -s gates` exited **0**, with **14/14 gates passed**.
Measured total wall time was **98.971041 seconds**, using four runner workers.
The runner compared **80** artifacts: **63 identical, 17 volatile-only,
0 semantic drift**. It wrote only scratch outputs; shared receipts were never
modified. The [round 2 receipt](../../../tools/census/receipts/census-2-round-2.json)
records the gate results, source hashes, proof observations and local log paths.
Pass categories overlap and must not be summed.

| Gate | Exact passed coverage |
|---|---|
| frontend | 14 reference fixtures; 28 parser-lane observations; 24 boundaries; 4 boundary laws; 4 mutants. Classification: 12 fixtures in 2 lanes; 6 laws; 7 mutants; 72 downstream rejection observations |
| checker | 49 fixtures; 98 lane observations; 10 budget probes; 2 catalog bounds / 16 bound observations; 7 mutants |
| structural | 16 fixtures; 64 lane observations; 4 boundary pairs; 7 mutants |
| fields | 40 fixtures; 240 phase observations; 36 budget probes; 6 host probes; 2 bounds / 12 level-inspection observations; 9 mutants |
| wasm | 25 programs; 90 independent reference calls in 2 execution lanes; 64 rejection pairs; 44 boundaries; 7 mutants |
| wasm-trust | 3 entries; 0 proof holes |
| fields-trust | 4 entries; 0 proof holes |
| structural-trust | 2 entries; 0 proof holes |
| owned-store | 3,532 cases in each of 2 lanes; 15 literal witnesses; 6 mutants |
| flat-store | In each of 2 lanes: 3,534 instances; 13,621 observations; 2 installed boundary states; 7 lifecycle checks; 9 mutants |
| recursion | 19 seed fixtures; 114 phase observations; 4 fuel probes; 3 mutants |
| fields-wasm | 8 fixtures; 32 seed calls; 64 evaluator and 64 Node observations; 50 enum-byte checks; 30 boundaries; 4 mutants killed in both lanes; 5 checked laws |
| census | 30 compiler files; 425 declaration events; 40 classes; all 5 manifests current |
| lint:verify | 127 tests; 8 law-rule wiring controls; 0 provider requests |

`census --check` passed; `census:test` passed **75/75 tests**, including three
complete pinned-seed checks of the unchanged Bend controls. `gates:verify`
passed **18/18 tests**, including six gate-runner mutants. The seven requirement
tests also passed separately after making the integration control tolerate future
gate registrations. Repeated census generation and the read-only meter are
byte-identical, as checked by the unchanged deterministic tests.

All seven compiler proof entry receipts record exit 0 and `All terms check.`;
the two unchanged store proof entry commands also passed inside their gates.
There are **0 changed Bend files in this repair**, so offline style preflight
has no targets or applicable blockers. No new law requires a proof entry.
No live Perch ratings or style qualification are claimed; live review belongs to
the coordinator.

## Boundaries and next increment

The census inventories registered gate contracts; it does not execute gates or
infer a fresh pass from a saved receipt. The separate run above supplies current
execution evidence for this tree. Coarse class coverage still does not establish
feature interactions, a host ABI, general acceptance or self-hosting.

There is no new gate, compiler capability, implementation file/import/class,
approval-policy change or style-manifest group. The implementation, closure and
host manifests changed only their census-source hashes. The old census-2 receipt
and report remain historical evidence.

When nest/modules or another frozen suite arrives, regenerate the census. Its
requirements become evidence only after the mapped gate lands and the full gate
runner passes. If a gate uses a different name or directory, update the reviewed
adapter mapping and its controls. The coordinator owns integration, live Perch
review and any shared receipt refresh. No push or other-worktree edit was made.
