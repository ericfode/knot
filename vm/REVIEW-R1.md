# vm-model review r1

The review was made against `4e4c4760`. Frozen VM goldens, invocation outcomes,
fuel, calls and loader expectations are unchanged. New installed-state controls
were fixed by literal review in `94e54bb0` and `6f988dff` before their repairs.

| Finding | Disposition and evidence |
| --- | --- |
| Atomic audit accepts changed stopped states | Confirmed, repaired. `audit.atomic` compares the complete store tries, allocation metadata, stack, meters, pending control and output sequences. RC-balanced input 42 → 43, output A → B and pending Return 7 → 8 each fail atomicity. The controls also cover an unrelated stored word, output order and line boundaries, and every control/outcome constructor. |
| Law-only mutant exception | Confirmed, repaired. `killed` again requires a wrong execution observation. The native full-frame control spends one fuel and retains calls 18 and quantum 1 from calls 17 and quantum 0. `debit-refunded` returns a well-formed wrong answer; its existing checked law remains additional evidence. |
| Book description's pending control | Exposed by the complete comparison. The description is the rest of Return to Top(0), so its stopped fallback now retains `Return`, with the same word and state, instead of `Finished(Answered)`. A separately frozen control, checked law and executable mutant hold the boundary. |
| Seed-accepted empty datatype classified Invalid | Confirmed, inherited, frontend-owner dependency. A fresh seed check prints `All terms check.` and evaluation prints `High{}`. Fresh Knot checker, evaluator and compiler builds all exit 2 with `Invalid check empty-datatype 5:9:1:5`; no artifact is produced. `src/catalog.bend` has blob `107ff05786337ef157f0449a41dcf19695796b8c` here and on vm-spec. The coordinator assigns acceptance to the modules reconciliation round; an unsupported lane must report `Unsupported check empty-datatype`. No frontend edit belongs to this increment. |
| Historical timestamp-only receipt commit | Retained as history. Replacement model evidence is normalized before staging and must contain semantic changes; no timestamp-only receipt checkpoint is added. |
| PATH selects Bun 1.3.11 | Repaired. The runner checks PATH's executable against io-host's unchanged Bun 1.3.14 pin before builds or receipt removal. `gates:verify` has 22 passing tests, including wrong-version, missing/failed-probe and no-mutation controls. |

## Deterministic controls

`model-boundaries.json` fixes 45 installed-state observations. Its `value_on`
fixture must equal the committed golden words. These exercise the model directly;
they are not new source-language seed/evaluator/Wasm outcomes.

Four new audit/description mutants are type-correct and execution-killed by
these controls, as well as refuted by their designated laws. The existing
`debit-refunded` mutant is execution-killed by `entry-frame-debit`. There are no
law-only kills. The complete gate requires all 65 model mutants and 25 designated
law refutations, alongside the unchanged zero-leak audit and soundness sweep.

Targeted runs and build/proof logs are under `.local/vm-model/review-r1/`.
The registered gate writes current source hashes and all observations to
`vm/receipts/model.json`. The full gate runner preserves its per-gate logs and
normalized evidence under `.local/gates/run-*/`.

## Completed gates

Two consecutive `npm run -s gates` executions of the source at `95149e19`
passed all 22 registered gates with exit 0. Their normalized summaries are
identical, and all 90 normalized receipt files match byte for byte. The runs are
`.local/gates/run-grme3s31` and `.local/gates/run-mjl8p267`.
[The review receipt](receipts/review-r1.json) records the exact per-gate counts,
source/dependency hashes, comparison hashes and finding dispositions.

The model gate passed 111 goldens, 44 invocations, 108 fuel controls, 212 refusal
controls, 13 argument controls, 165 admitted controls, 107 audited runs and 45
installed-state controls. Its sweep covers 65,469 mutations of 111 images; all
49 laws check, all 65 model mutants have execution kills, and the harness mutant
is killed. The existing `enter-arity` mutant also crashes on two controls; those
inherited observations are excluded from its three proper execution kills.
The five mutants for this repair have zero recorded crashes.

The adopted model receipt has the same normalized bytes in both runs, with
SHA-256 `d1feba383a81142fae9c15cd3b8328fcd1a5f75a8f9c9b373e1a0759da0a10a2`.
All 14 model source hashes and the boundary-expectations hash match this tree.
Only the owned model receipt is refreshed; bootstrap and vm-spec receipt
reconciliation belongs to the coordinator.

The installed empty-datatype image runs in the model as
`Evaluated\t1\t1\tHigh{}`. The source-lane refusal therefore remains a frontend
dependency, with the reproduction retained in the review receipt.

## Review limits

Offline preflight of the five changed Bend files reports 113 structural blockers:
112 units have truncated helper/caller context, and the combined composition
exceeds its byte cap. The bounded `vm/perch-manifest.json` preflight covers 10
groups and reports zero blockers, with complete declaration and composition
contexts. This is structural evidence only. Compression, Delight, memetic
identity, Anticipation and Payoff have no fresh live ratings; the coordinator
owns live Perch, integration and shared-receipt refresh.

The symbolic machine-state laws and finite controls do not prove universal
validator soundness or compiler correctness. The full-frame control installs
the region boundary; it does not allocate four million frame words. General
Case/tail heap-and-frame exhaustion remains bounded by the existing laws and
recorded proof limits in MODEL.md.
