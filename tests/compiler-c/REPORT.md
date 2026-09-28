# Milestone 13: native C executor handoff

`knot-c-1` adds deterministic C99 emission from checked core for the current
enum, fielded and first-parameter structural recursion profiles. The compiler
uses a typed cell arena, explicit return/save destinations, simultaneous tail
parameter transfer, and guarded non-tail calls. The separate compile entry and
host adapter leave the default compiler CLIs unchanged.

The implementation is `src/c.bend`; eight filled helper laws are in
`src/c-LAWS.bend` and `src/c-PROOF.bend`. The manifest, census approval, profile
contract and fifteenth gate are registered. This is an executor increment for
coordinator review, not a claim of general compiler refinement or live style
qualification.

## Deterministic verification

`BEND_NO_TELEMETRY=1 npm run -s gates` exited 0: **15/15 gates passed** in the
scratch checkout, measured wall time 453.665139 seconds. `npm run -s
gates:verify` passed **18/18 tests**. The retained
[verification receipt](receipts/verification.json) includes every gate command,
count dictionary, stdout, timing, snapshot hash and receipt classification.

Categories below overlap; they must not be summed into an invented test count.

| Gate | Exact passing coverage |
| --- | --- |
| frontend | 14 fixtures; 28 lane observations; 24 boundaries; 4 mutants |
| checker | 49 fixtures; 98 lane observations; 10 budgets; 2 bounds / 16 bound observations; 7 mutants |
| structural | 16 fixtures; 64 lane observations; 4 bounds; 7 mutants |
| fields | 40 fixtures; 240 lane observations; 36 budgets; 2 bounds / 12 bound observations; 6 host boundaries; 9 mutants |
| wasm | 25 fixtures; 90 reference calls; 2 execution lanes; 64 rejections; 44 boundaries; 7 mutants |
| wasm-trust | 3 entries; 0 proof holes |
| fields-trust | 4 entries; 0 proof holes |
| structural-trust | 2 entries; 0 proof holes |
| owned-store | 3,532 cases; 2 execution lanes; 15 literal witnesses; 6 mutants |
| flat-store | Each of native and Bun: 3,534 instances, 13,621 observations, 7 lifecycle checks, 2 installed boundary states; 9 mutants |
| recursion | 19 seed fixtures; 114 native/Bun phase observations; 4 fuel probes; 3 mutants |
| fields-wasm | 8 fixtures; 32 seed calls; 64 evaluator and 64 Node observations; 50 frozen enum-byte checks; 30 boundaries; 4 mutants; 5 new checked laws |
| census | 33 compiler files; 504 declarations; 440 unique declarations; 331 definitions; 40 classes |
| lint:verify | 127 tests; 8 law rules |
| c-backend | 46 programs; 143 reference calls; 19 original recursion references; 286 observations each for evaluator, Node Wasm and native C; 143 sanitized observations; 57 C and 46 Wasm byte-identity pairs; 76 original-recursion phase observations; 22 original-source C builds; 80 rejection lane cases; 17 resource/budget probes; 18 host probes including 4 adapter probes; 4 mutants; 8 checked laws |

The direct C gate passed separately with the same counts. All 142 hashed inputs
still matched when the verification receipt was written. The complete C proof
entry printed `All terms check.`. The compiler was Apple clang 21.0.0
(`clang-2100.1.1.101`), target `arm64-apple-darwin25.5.0`.

The runner classified 63 receipts as identical, 10 as volatile-only, and 8 as
semantic differences. One semantic record is the new C gate; the other seven
change only hashes of new C files and amended SPEC/CONTRACT inputs. Existing
outcomes and assertions are unchanged. No shared gate receipts are refreshed
in this increment; the coordinator owns that merge step.

The C comparison retains expected resource differences. `arena-overflow`
succeeds in seed/evaluator and exhausts C/Wasm. `deep-call` exhausts the default
evaluator parser budget while the compiler entries use larger explicit budgets.
Thus 286 observations per lane are not 286 successful four-way equal results.
See [README.md](README.md) for the full outcome split.

## Independent fixtures and mutants

Thirteen new fixtures comprise eleven byte-prefix-preserving observers of the
original recursion trees, nine calls on a simultaneous tail-rebinding fixture,
and a 64-node non-tail recursive-copy fixture. The immutable
[reference receipt](receipts/reference.json) fixes seed observations before C
observations. Existing suite manifests and assertions were not changed.

All four mutants remain type-correct and emit compilable C: swapped field
offset, missing arena bound, inverted tag comparison, and skipped tail parameter
rebinding. Both compiler lanes kill every mutant through the fixed semantic
expectation, with clean ASan/UBSan execution. The missing-bound witness does not
dereference a one-past pointer. Earlier unsupported leak-detector and malformed
mutant attempts remain in [attempts.json](receipts/attempts.json); neither is
counted as a semantic kill.

The [independent review](receipts/review.json) preserves 256-tag and nested
256-tag matching probes, and default-depth exhaustion on a sanitized 300-node
non-tail recursion. These probes are separate from registered counts. Its
adapter-coverage gap was closed by four literal host controls in the final gate.

## First benchmark

The complete benchmark passed **46 programs / 143 calls**, with seven runtime
samples and three compile/process samples after warmup. C and Wasm each have
142 successful runtime cases and one expected arena exhaustion. Upstream Bend
native covers 111 calls in 32 programs; 32 calls in 14 programs are unavailable
because the required `Base` import collides with unchanged fixture names.
Diagnostic and import controls are retained; no fixtures were renamed.

Each warm loop checked 1,008,200 invocations. The benchmark's six independent
worker controls passed; all 1,066 recorded metric summaries and 440 bootstrap
comparisons recomputed exactly. [c-verification.json](../../bench/c-verification.json)
retains that auxiliary verification separately from the registered gate counts.

For `wasm-flag.main()`, median C emission was 3.79 ms and total emission plus
`cc` was 73.11 ms; Wasm emission was 3.62 ms. Median fresh-process times were
2.29 ms C, 27.93 ms Node Wasm, and 3.34 ms upstream native. Upstream's per-call
native build was 303.15 ms. These process measurements include startup and
printing; upstream's compilation boundary differs from Knot's.

The fresh-lifetime loop includes C reset/dispatch versus Wasm
instantiation/export lookup, so its ratio does not isolate generated instruction
speed. The host was shared with other campaign work. Full raw samples,
median/MAD statistics and bootstrap comparisons are in
[c-first.json](../../bench/c-first.json); per-program tables are in
[c-first.md](../../bench/c-first.md), with the protocol in
[README-c.md](../../bench/README-c.md).

## Offline style and remaining boundaries

The all-new-Bend preflight covers 269 declarations in 17 files, with 50
truncated declarations and 65 unresolved supporting roles. Its composition
context exceeds 48,000 bytes and has unresolved nonlocal context. The bounded
`c-backend` family covers 107 declarations in four files, with 23 truncated
declarations and 47 unresolved supporting roles; composition remains
unavailable despite fitting the byte cap. Both commands return attention status
3 with zero provider requests. See [style-preflight.json](receipts/style-preflight.json)
and [style-family.json](receipts/style-family.json).

Conceptual compression, Delight, memetic identity, Anticipation and Payoff have
**no live ratings or probability distributions** in this executor increment.
No style pass is claimed. The reading hypothesis is that a single destination
algebra makes tail position and continuation preservation explicit while the
mode dispatcher shares argument staging and field traversal. The coordinator
must judge that bounded mechanism with sufficient context.

The arena has 16,384 logical slots with no reclamation. Reset starts a new
execution and invalidates old cells; this does not qualify R3/R7. Non-tail calls
use a depth-256 guard and conservative 1 MiB frame charge on the recorded
ordinary main-thread stack, not a theorem about arbitrary host stack sizes.
There is no structured host ABI, threading, IO/GPU support, self-hosting claim,
or general compiler/memory refinement proof.

The next integration must explicitly lower or report Unsupported for each new
checked core expression added by concurrent compiler increments, before the
current Internal traversal-container fallback. Then rerun the complete gates,
refresh shared receipts at the coordinator boundary, and complete live semantic
and role-scaled style review. Larger accepted workloads and a Wasm reset ABI
would make the performance comparison more informative.
