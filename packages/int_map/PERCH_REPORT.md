# IntMap live Perch audit — 2026-09-26

Completed **18 live provider requests/responses and 94 rule evaluations** using
Perch 0.3.5, requested `jev-latest`, resolved **`jev-1.13.0` throughout**. Every
check had nonzero coverage and a completed provider response. No retries, rate
limits, credential failures, or incomplete requests occurred.

**No implementation or law-packet finding reached the configured reporting
floor. Two deliberate broken controls were correctly reported.** Manual source
review confirmed a benchmark CLI input defect that Perch did not report; it is
fixed locally. No published package source changed and no republish occurred.

## Coverage and receipts

All commands used the root wrapper:
`npm run lint -- <path> --rules <names> --json`.
The [receipt index](receipts/perch-audit-2026-09-26/index.json) links each durable
package copy and original `.perch/usage/` path. Receipts preserve full source and
aggregate-rule hashes, model identity, all raw probabilities, coverage, provider
counts, and exits. They contain no credentials.

Six source rules on **every one of the 11 maintained Bend files**:
`bend-fuel-completeness`, `bend-machine-arithmetic`, `bend-borrow-lifetime`,
`bend-ordered-f32`, `bend-effect-boundary`, `bend-device-stack`.
Each file received six completed checks; scaling received six more after its fix.
Even the small benchmark/release wrappers and retained remote consumer were checked.

| Current file | Checks | Receipt |
| --- | --- | --- |
| `LAWS.bend` | 6 | [930052fa-b37f-4cee-8e55-84652b103ef1](receipts/perch-audit-2026-09-26/930052fa-b37f-4cee-8e55-84652b103ef1.json) |
| `PROOF.bend` | 6 | [294e600f-a36e-488e-b9b5-1a15cff50e4f](receipts/perch-audit-2026-09-26/294e600f-a36e-488e-b9b5-1a15cff50e4f.json) |
| `benchmark.bend` | 6 | [d22bcad2-12e7-4adf-9f06-50e979d173e2](receipts/perch-audit-2026-09-26/d22bcad2-12e7-4adf-9f06-50e979d173e2.json) |
| `conformance.bend` | 6 | [c9d91e9a-5d5d-4624-8ee8-408e1d29fb8b](receipts/perch-audit-2026-09-26/c9d91e9a-5d5d-4624-8ee8-408e1d29fb8b.json) |
| `example.bend` | 6 | [7955fe9f-9ccc-4ea7-a3fe-ce58d2435108](receipts/perch-audit-2026-09-26/7955fe9f-9ccc-4ea7-a3fe-ce58d2435108.json) |
| `fixtures.bend` | 6 | [83373b5f-9a63-4d83-954f-310da5107f13](receipts/perch-audit-2026-09-26/83373b5f-9a63-4d83-954f-310da5107f13.json) |
| `main.bend` | 6 | [2bc88dc4-0d09-4b98-8e8d-c4776b072f05](receipts/perch-audit-2026-09-26/2bc88dc4-0d09-4b98-8e8d-c4776b072f05.json) |
| `model.bend` | 6 | [9233015d-48c3-4478-8821-19680a3f5eb2](receipts/perch-audit-2026-09-26/9233015d-48c3-4478-8821-19680a3f5eb2.json) |
| `release.bend` | 6 | [9f2fde2e-a331-4420-804f-053a676ea2d7](receipts/perch-audit-2026-09-26/9f2fde2e-a331-4420-804f-053a676ea2d7.json) |
| `scaling.bend` | 6 | [6a3ea768-8960-4f1c-b6ee-b520be1d082f](receipts/perch-audit-2026-09-26/6a3ea768-8960-4f1c-b6ee-b520be1d082f.json) |
| `receipts/remote-consumer.bend` | 6 | [9839f7b1-d25b-4754-b3ef-2223965a6246](receipts/perch-audit-2026-09-26/9839f7b1-d25b-4754-b3ef-2223965a6246.json) |

`LAW_REVIEW.md` received all eight shared `law-*` rules plus
`package-int-map-union-observation`: nine checks initially and nine after its
historical credential paragraph was updated. The current packet receipt is
[7f32228b-24fe-433a-a5b5-ae675f1d2849](receipts/perch-audit-2026-09-26/7f32228b-24fe-433a-a5b5-ae675f1d2849.json).

Four bounded controls received one dedicated-rule check each. Total:
66 initial source checks + 9 initial packet + 4 controls + 6 changed-source
rechecks + 9 current-packet rechecks = 94.

Excluded: 130 Bend files under ignored `build/`, consisting of generated
mutant copies and their drivers, fresh downloaded copies of the already-audited
release, and generated consumers. They are duplicate or intentionally broken
artifacts, not additional maintained implementation. No maintained Bend source
was excluded. Host orchestration scripts and ordinary Markdown are outside the
six Bend selectors; the real law packet and control Markdown are explicitly
covered by their dedicated selectors. No whole-repository scan was run.

Full current source identities (SHA-256):

```text
95f0f9551cfcd8b5e0b16437405177f4e79f8305c4b9a503bfda68d2a9eea311  LAWS.bend
64a59a7d38a2daac8bdbf31006c27f6de88733edbca5176e953386881e7715e6  PROOF.bend
77a420bb48003b31e4f24862fffe3227d629fc81f809246386919f5c040549b2  benchmark.bend
987b5f1fe814cefdc58ad39f95618bfcc58002983f021825c3c024b8c32b1de6  conformance.bend
58bb16bafcdb56f6e488d49e9e5fabc40c4930e688a8d65fca48cc7af1a309f6  example.bend
22374c110d4043af068e92d82c763022abebc10e292a5edd278f09f765a41b5e  fixtures.bend
e3e62df90a23f8f80ad6a0730f434b16035d1dda43fb93764fe03504d1c3f83a  main.bend
62ede4569dd2d11dd8d23734afbaca21710f58bc73a14cee5fb82efe684109fa  model.bend
71f59b2447b6c0e769ec6d73ce43d7e060d4f31226fb7367875f33d24d98992f  release.bend
cb6cb77a20a60026e7efd9a65e6d945f5dce923f299614e3899e4f59b57e283b  scaling.bend
4e0dc0919dd370881ce357c4550e8c37953eb73f2d75ee51cc63cffbae1700d9  receipts/remote-consumer.bend
62d38400b5eb88f7df0fbfcf0c8496fdd6e60e6dd03a509cf193200b3f817434  LAW_REVIEW.md
```

## Findings and control adjudication

Broken probability is `1 - probability_true`. The dedicated rule stayed at
its original **0.80 floor**, `gate: false`; `check` nevertheless exits 3 on a
reported advisory finding. No rule text or floor was changed. The separately
calibrated `source-checkpoint-observation` remains at 0.70 in its owning package;
that rule was neither applied to IntMap nor edited.

| Control | Expected | Broken probability | Reported | Adjudication |
| --- | --- | --- | --- | --- |
| `tests/perch/clean/LAW_REVIEW.md` | clean | 0.12 | no | Correct clean result: exact Join(2,7), unchanged one-sided values. |
| `tests/perch/broken/LAW_REVIEW.md` | broken | 0.93 | yes | **Confirmed intentional negative**: addition cannot distinguish argument reversal; singleton values unobserved. |
| `tests/perch/held_out/LAW_REVIEW.md` | clean | 0.08 | no | Correct clean result: 100*3+7=307 and exact one-sided values. |
| `tests/perch/held_out_equal_values/LAW_REVIEW.md` | broken | 0.89 | yes | **Confirmed intentional negative**: 100*7+7=707 survives reversal because operands are equal. |

The fresh equal-values case has no expected-label hint in its text. The three
original controls do contain expected-label text, which can bias those readings.
There were no misses in these four dedicated-rule controls, but this small set
is not a production accuracy estimate. Both emitted findings are adjudicated;
there are no duplicate, false-positive, or unresolved emitted findings. Intentional
negative controls stay broken. The rule remains advisory, without refinement.

The actual packet's dedicated-rule broken probability was 0.05 initially and
0.04 after the documentation update. No shared-law finding reached 0.80; the
largest current packet score was observable essence at 0.61. These scores do
not prove adequacy. Arithmetic scores were relatively elevated even on thin
wrappers (0.70 benchmark, 0.69 release, 0.67 conformance) with no local arithmetic
hazard established by the source. The raw answers have no causal explanation;
we do not promote those hints into confirmed defects or change correct code.

## Confirmed local defect, fix, and deterministic evidence

Source review found `scaling.bend` advertised `positive size <=4096` but accepted
any parsed Nat. A freshly compiled native `scaling-before 0` exited 0 and reported
zero depth/nodes/work: a vacuous benchmark despite the advertised input domain.
[Reproduction](receipts/perch-audit-2026-09-26/scaling-before.json) retains the
original source hash, exact arguments, exit and output. This is **confirmed**
in the local benchmark harness, not in the public map API. Perch did not emit a
finding: scaling arithmetic broken probability was 0.56 before and 0.55 after.
It therefore did not detect this independently established input-contract gap
at its 0.80 floor; no speculative precision score is computed.

Added bounds checks to both `parsed` and `parsed_core` through `run_checked`
and `run_core_checked`: only 1..4096 may start either layout. Outside values and
malformed input exit 2 before map construction. Accepted laws and map semantics
were preserved. [Regression receipt](receipts/perch-audit-2026-09-26/scaling-after.json)
records both entry points compiled to native and JS, **16 valid executions**
(default64,1,64,4096) and **20 invalid executions** (0,4097,65537,4294967296,
malformed), plus the unchanged complete proof entry passing with zero holes.
All passed. Reproduce with `python3 packages/int_map/scripts/check-scaling-inputs.py`.
The changed-file Perch recheck completed all six rules with no reported finding.
Historical release gates/receipts were preserved, not overwritten.

This report is also the package-local maintenance log entry for the missed
input-contract gap: explicit CLI-domain regression tests prevent recurrence;
no model-only rule change is justified by one case. Shared review logs were
not edited because this audit's ownership boundary forbids shared-file edits.

## Release comparison and limits

`scaling.bend` differs from the original local build snapshot, but it was never
in the published upload closure. [Exact comparison](receipts/perch-audit-2026-09-26/published-closure-unchanged.json)
confirms all nine uploaded files remain byte-identical to
`0x99e32f5f97dad3791a32b01d133555c5`. No republish. Documentation, the fresh
control, local audit/regression scripts, and audit receipts are new or updated.

Perch has no Bend AST, call graph, proof checker, or device execution. Passing
probability thresholds neither proves correctness nor covers GPU behavior.
Universal public-core laws, six concrete normalization laws, runtime/model
checks and benchmarks retain the boundaries in SPEC.md; full universal model
refinement and GPU execution remain unvalidated.

Per-request aggregate rule hashes differ because the checkout has concurrent
rule maintenance. Each wrapper receipt preserves its actual aggregate hash;
end-of-audit copies of the relevant six/eight/package rule definitions are in
this receipt directory. This chat changed no rule definition or shared file.
Original release-time missing-credential receipts remain historical evidence;
this report supersedes that limitation for the current live audit only.
