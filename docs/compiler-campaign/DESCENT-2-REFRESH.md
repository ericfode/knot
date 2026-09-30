# Descent-2 refresh

Starting checkpoint: `75e1ac69`. The refresh preserves the accepted decreasing-call implementation and all earlier freezes. No production Bend declaration changed.

The direct implementer instruction forbids merges. The refresh prompt's main merge therefore remains a coordinator action. This report qualifies the branch-local work; it does not qualify an integrated main/nest/modules tree. Main decisions D1-D26 and the standing coordinator rulings were read from main. Main's host reliability changes were carried over narrowly without a merge: a 1,800-second outer gate limit, factor-four legacy subprocess hang guards, resolved clang/SDK forwarding and one bounded clang-discovery retry with the first attempt retained. Frozen verdicts, compiler resource budgets, laws and semantic mutants remain unchanged. The new retry controls distinguish assertion failures and persistent host failures; `gates:verify` passes 20 tests and six semantic wrapper mutants.

A separate immutable freeze adds **28 new edge programs plus six verbatim nest round-4 sources**, observed by the seed book and its native/Bun executable lanes. It fixes 15 acceptances and 19 rejections. Seed executable wrappers add only `import Base` before the unchanged source body. No descent discrepancy requiring a production repair was found. The new cases remain part of the registered descent gate, with separate phase, value, module-byte and preserved-artifact counts. The original 38 rule/legacy cases, two resource cases, 12 boundaries and seven mutants stay fixed.

The probes cover a fourth parameter, erased columns inside and after equal columns, opaque later arguments after an earlier decrease, nested rebuilding, three-field product comparisons, both subterm-search sides, alias chains/shadowing, rejected local scrutinees, affine alias reuse, zero-argument recursion and dead growing calls. The seed rejects nest's `rebuilt-partial` at the self-call before reporting its missing coverage. Removing only that call produces `cases for Leaf`; this independently supports the branch's earlier `Invalid check missing-arm` code.

D21's two general matrix lowering laws remain required and explicitly open in `src/SPEC.md` and `tests/compiler-descent/LAW_REVIEW.md`. The branch's existing ground instances and helper equations do not discharge them. The first-row total obligation is limited by the unchanged 4,096-step quota, as its frozen matrix-work control demonstrates. Nest's newer proof/evidence must be preserved at integration. D22-D25 add no branch-local descent obligation: VM requests, Book/Program effects, request Defaults and atomic machine stops remain VM integration work. No IO/VM support is claimed here.

The D26 audit compares nest at `9645422d86e455e44ca853502210b7225c9c1e85`. There are 14 assertion migrations and two retired conservative overrides. The ten legacy items were already independently frozen and committed by descent-2; the six additional nest sources are re-observed in both seed lanes in `refresh-reference.json`. Full source paths, hashes, seed observations and selected phases are in [refresh-d26.json](../../tests/compiler-descent/receipts/refresh-d26.json). Main's decisions and coordinator state were re-read at `b92b1359`; this records an audit point, not an integrated tree. Nest merges first. The coordinator must preserve the most precise sound verdict, re-freeze losing pins in separate seed-citing commits and re-express any displaced mutant at the integrated rule with its original witness. The integrated checker determines diagnostic precedence, phase and code.

| Source/case | Nest effective assertion | D26 selection on this branch |
| --- | --- | --- |
| `recursion/same-parameter` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `recursion/other-parameter` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `recursion/rebuilt-parent` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `recursion/rebuilt-constructor` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `recursion/computed` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `recursion/shadow-let` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `recursion/second-descent` | `Unsupported check recursive-call` | `Checked` |
| `compiler-checker/recursive-call` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `compiler-nest/rec-swapped-args` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `compiler-nest/rec-alias` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `rebuilt-partial` | `Unsupported check recursive-call` | `Invalid check missing-arm` |
| `rebuilt-retyped-constant` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `rebuilt-root-source` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `rebuilt-root` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `rebuilt-swapped-fields` | `Unsupported check recursive-call` | `Invalid check recursive-call` |
| `rebuilt-unrefined-constant` | `Unsupported check recursive-call` | `Invalid check recursive-call` |

The original recursion gate still selects the enum emitter, so its checked `second-descent` retains `Unsupported check constructor-fields` at compilation. The fields-profile descent gate checks, evaluates and builds the original structured program and its enum observer. A Checked result does not change an emitter capability pin.

Offline style preflight selected 34 fixture files. It prepared 29 files and 130 declarations with zero structural blockers in those prepared contexts. Five intentional negative local-scrutinee programs are rejected by the pinned parser, so their style contexts are unavailable. Their seed rejection and compiler classification remain required semantic observations. The receipt retains each source hash, task/rubric/parser identity and prepared context summary. There were zero provider requests. Conceptual compression, Delight, Memetic identity, Anticipation and Payoff have no new ratings or distributions; no automatic style pass is claimed. The previous production style receipts retain their original rubric meaning. Live Perch remains coordinator-only.

Census approval printed an empty summary: no compiler files, declarations, feature classes or imports widened. Regeneration retained 36 files, 562 declarations and 40 feature classes. The accepted inventory changed only the hashes of five gate drivers after their host hang guards changed.

The first full attempt hit the older 30/45-second host build guards and was stopped after four failures. The next completed run passed 14 gates but failed census at those stale hashes and descent at the refresh adapter: its freeze records the pure value `On{}`, while Knot's evaluator returns `Evaluated\t0\t1\tOn{}`. The adapter now requires the exact CLI frame and the unchanged frozen value/tag. No expectation or seed receipt was rewritten. A targeted replay passed all 34 refresh cases / 204 phases using the prior builds after verifying every production Bend and executable hash. The full rerun rebuilds them. The resource regression's explicit two-second limit remains unchanged.

`BEND_NO_TELEMETRY=1 KNOT_GATE_TIMEOUT_SCALE=8 npm run -s gates -- --jobs 3 --keep-scratch` passed **16/16 gates**, exit 0, in a measured 683.761 seconds of wall time. There were no discovery retries in this final run. The invoking source snapshot remained identical throughout execution, and every production Bend source still matches the pre-probe freeze. The timeout factor changes host hang guards only; compiler work budgets and the explicit two-second alias-resource limit remain fixed.

| Gate | Result and exact counts |
| --- | --- |
| frontend | Passed: 14 parser fixtures in two lanes / 28 observations; 24 boundaries; four boundary laws and six classification laws; four parser mutants; 12 classification fixtures in two lanes, seven classification mutants, 72 downstream observations |
| checker | Passed: 49 fixtures, 98 checked observations, 10 depth probes, two boundary cases / 16 catalog observations, seven semantic mutants |
| structural | Passed: 16 fixtures, 64 lane observations, four boundary pairs, seven semantic mutants |
| fields | Passed: 40 fixtures, 240 phase observations, 36 budget probes, six host probes, two boundary cases / 12 level and inspection observations, nine semantic mutants |
| wasm | Passed: 25 programs, 90 independent seed calls in two lanes, 62 rejection pairs, 44 boundary observations, seven semantic mutants |
| wasm-trust | Passed: three entries, zero proof holes |
| fields-trust | Passed: four entries, zero proof holes |
| structural-trust | Passed: two entries, zero proof holes |
| owned-store | Passed: 3,532 cases in two lanes, 15 literal witnesses, six semantic mutants |
| flat-store | Passed in each of two lanes: 13,621 observations, 3,534 instances, two installed boundary states, seven lifecycle checks; nine semantic mutants |
| recursion | Passed: 19 fixtures, 114 phase observations, four fuel probes, three semantic mutants |
| fields-wasm | Passed: eight fixtures, 32 seed calls, 64 evaluator and 64 Node observations, 50 frozen enum-byte checks, 30 boundaries, four mutants / eight kills, five checked laws |
| census | Current: compiler 36 files / 562 declarations / 40 feature classes; frontend 3 / 50 / 31; packages 8 / 225 / 34; published imports 2 / 53 / 26; Base 1 / 495 / 45 |
| lint:verify | Passed: 127 tests, eight law-rule wiring controls; mocked review only |
| nest | Passed: 40 fixtures, 174 seed calls, 40 matched outcomes / zero UNMET; 386 evaluator and 386 Wasm values, 24 boundaries, 100 enum hashes, six mutants / 12 kills |
| descent | Passed: original 38 fixtures / 228 phases / 19 accepted books; two resource fixtures / 12 phases / one accepted book; 34 refresh fixtures / 204 phases / 15 accepted books; 12 boundary cases / 24 observations, two proofs, seven mutants / 14 kills |

The descent total is **74 frozen books / 444 phase observations**, 35 accepted books, 70 evaluator values, 68 direct Wasm values plus two checked observer links, 35 equal native/Bun module-hash pairs, and 78 preserved rejection artifacts. Boundary observations include 14 Exhausted results, two InternalFailure results and eight successes. The original descent counts are unchanged; the refresh contributes 34 books, 204 phases, 30 evaluator values, 30 Wasm values, 15 module pairs and 38 preserved artifacts. All seven mutants remain type-correct and are killed semantically in both lanes.

`gates:verify` separately passed 20 tests, including six semantic wrapper mutants. [refresh-verification.json](../../tests/compiler-descent/receipts/refresh-verification.json) retains the normalized runner summary, counts, measured run data, completion lines, failed attempts and ownership boundary. Only [descent.json](../../tests/compiler-descent/receipts/descent.json) was copied back from this run. Other shared receipts remain untouched; their refresh belongs to the coordinator. Earlier qualification and seed receipts are retained.

The implementer refresh is complete. Remaining integration work is coordinator-owned: merge main and the completed nest/modules increments in the prescribed order; reconcile the 16 D26 items and displaced mutants in separate seed-citing commits; preserve the union of D21 obligations and nest's newer proof evidence; run prechecks, independent review and live Perch; refresh shared receipts. Newer upstream suites and VM behavior await that integration. This report does not establish main's self-hosting milestone or a new semantic/style review pass.
