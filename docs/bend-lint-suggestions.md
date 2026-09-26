# Bend mistakes worth catching while building Knot

Read-only audit of `/Users/ericfode/src/bend-scrabble`, 2026-09-26. Its reference
compiler is Bend **2.0.16**. Knot's compatibility/bootstrap version remains
undecided. The audit included the working copy, which contains uncommitted
changes; these line references identify that inspected state, not a release.
No Scrabble source was changed or submitted to a model.

Use deterministic parsing, typing, quantity checking, proof checking, and
backend tests for compiler acceptance. Perch can flag suspicious intentions,
missing preconditions, and transformations that deserve those stronger checks.
Its probability is neither a proof nor evidence that compiled code ran.

## First rules to calibrate

### 1. Fuel proves termination, not completeness

**Prevented hazard.** Scrabble's tree-depth calculation must round upward for
odd splits and count the singleton leaf. Returning `NoMoves` at zero fuel can
silently discard valid work. The old hardcoded bound was sufficient; the source
does not establish that a production truncation occurred.

Evidence: [evaluate.bend:73](/Users/ericfode/src/bend-scrabble/engine/evaluate.bend:73)
and [forktree laws:6](/Users/ericfode/src/bend-scrabble/packages/forktree/LAWS.bend:6).

Installed rule: `bend-fuel-completeness`. In a compiler this means a parser,
normalizer, or AST traversal must not turn exhausted work into success.
Use explicit incomplete/error results, or establish a sufficient bound.
Calibrate with an odd-sized tree that drops its last leaf and a corrected
version. Deterministic regressions should cover sizes 0, 1, 2, 3, 5, 7, and 100,
plus unchanged output when already-sufficient fuel is increased.

### 2. Machine arithmetic is not unbounded arithmetic

**Documented domain constraint.** Scrabble uses Nat for exact list-length laws;
its U32 equations retain modular semantics. `1 - turn` only means alternating
players when `turn` is 0 or 1. Wrapped storage indices do not admit valid board
coordinates by themselves.

Evidence: [law domains:44](/Users/ericfode/src/bend-scrabble/docs/LAWS.md:44),
[modular equations:93](/Users/ericfode/src/bend-scrabble/docs/LAWS.md:93), and
[guarded board movement:155](/Users/ericfode/src/bend-scrabble/engine/types.bend:155).

Installed rule: `bend-machine-arithmetic`. Apply it to source offsets,
allocation lengths, fuel calculations, and constant folding. Test subtraction
underflow, maximum-word increments, conversion placement, and Nat/U32 type
annotations. Include an intentional modular PRNG as a clean control. A model
should identify the violated range assumption; exact arithmetic belongs in tests.

### 3. Preserve F32 fold order

**Prevented optimization hazard.** The scheduler retains raw trial values and
consumes them in sample order. Reassociating moment updates changes F32 results
even when a real-number equation looks equivalent.

Evidence: [moment update:175](/Users/ericfode/src/bend-scrabble/engine/search.bend:175),
[ordered consumption:34](/Users/ericfode/src/bend-scrabble/engine/waves.bend:34),
[raw-word tests:7](/Users/ericfode/src/bend-scrabble/tests/scheduling_probe.bend:7),
and [proof scope:125](/Users/ericfode/src/bend-scrabble/docs/LAWS.md:125).

Installed rule: `bend-ordered-f32`. For Knot, review reassociation, fused
operations, constant folding, and parallel reductions. Calibrate on a serial
fold versus completion-order accumulation, with cancellation-sensitive inputs
and signed zero. Compare raw words where bit preservation is the contract;
an explicitly approximate numerical contract is a separate case.

### 4. Terminating recursion can still overflow the device stack

**Observed failures, subsequently addressed.** An intermediate Metal artifact
failed on 256 depth-one trials while CPU completed. A separate two-blank root
with 138,144 legal moves also memory-faulted; the documented stack-safe revision
completed that root with CPU parity. These were separate regressions.

Evidence: [rollout failure:468](/Users/ericfode/src/bend-scrabble/docs/GPUMAX-VALIDATION.md:468),
[large-root failure:527](/Users/ericfode/src/bend-scrabble/docs/GPUMAX-VALIDATION.md:527),
and [large-root resolution:541](/Users/ericfode/src/bend-scrabble/docs/GPUMAX-VALIDATION.md:541).

Installed rule: `bend-device-stack`. Look for a retained continuation per token,
AST node, or list element, especially nested append/fold chains. Compare a
non-tail traversal with an accumulator or balanced representation. Compiler
regressions should preserve tail-call lowering and exercise large inputs on
each supported backend; termination checking alone is insufficient.

### 5. Bound pattern-lowering code growth

**Observed generated-code expansion.** Matching `fuel size` with U32 literals
produced a 6,620-line C entry and 63 copies of a substantial fork body. Those
are static copies, not evidence that all copies execute in one call. A separate
numeric-pattern Metal compilation was stopped after 45 minutes.

Evidence: [emission analysis:173](/Users/ericfode/src/bend-scrabble/docs/PERFORMANCE-RUNTIME.md:173)
and [rejected experiment:99](/Users/ericfode/src/bend-scrabble/docs/PERFORMANCE.md:99).

Installed rule: `compiler-pattern-sharing`, scoped to compiler source. Review
decision-tree construction for duplicated defaults and continuations. Keep arm
priority and semantics intact when introducing sharing. Deterministic tests
should count emitted nodes/bytes for compact joint-match inputs and bound
specialization growth. Source-level Boolean helpers can be a workaround for
the reference compiler; they are not a universal style rule.

### 6. Preserve affine ownership and borrowed lifetimes

**Language constraint and performance evidence.** Closures stay affine even
when their captures are Data. Storing trie subtrees in a `Visit` constructor
changes the ownership behavior of a traversal; an outer retaining wrapper does
not repair what the callee stores. `+` permits duplication, not a promise of
zero-cost borrowing.

Evidence: [closure semantics:83](/Users/ericfode/src/bend-scrabble/.toolchain/bend/guide/GUIDE.md:83)
and [ownership analysis:54](/Users/ericfode/src/bend-scrabble/docs/PERFORMANCE-RUNTIME.md:54).

Installed rule: `bend-borrow-lifetime` covers visible escape/reuse hazards.
Deterministic compiler tests must reject duplicated closures/handles, illegal
quantities, and erased evidence reaching live code. Review lowering passes for
preserved use counts. Treat unnecessary retention as a separate performance
suggestion requiring generated-code and runtime evidence, not a correctness bug.

### 7. Keep proof claims inside their actual trust boundary

**Explicitly documented limits, not discovered unsoundness.** The Scrabble proof
gate imports nine unsafe annotations from numeric/runtime dependencies. The
forktree laws over literal inputs normalize successfully but do not establish
the corresponding universal theorem; compiled conformance cases remain finite.

Evidence: [dependency boundary:29](/Users/ericfode/src/bend-scrabble/docs/LAWS.md:29)
and [literal-law scope:17](/Users/ericfode/src/bend-scrabble/packages/forktree/LAWS.bend:17).

Installed rule: `compiler-checker-trust`. Review any path that converts an open
law, unsupported term, normalization timeout, unsafe dependency, or model verdict
into “verified.” Negative compiler fixtures must fail deterministically. Keep
the live/erased distinction, proof holes, and termination checks in the trusted
checker. A future diff-aware rule should also catch weakened law domains;
a whole-file snapshot cannot establish that a contract was weakened.

### 8. Keep host effects and target support explicit

**Guarded boundary.** Scrabble's bridge deliberately rejects JavaScript execution.
Its foreign code depends on the pinned runtime ABI. A `!` annotation also does
not itself establish that a particular request ran on a GPU or used one physical
kernel launch.

Evidence: [explicit unsupported backend:1](/Users/ericfode/src/bend-scrabble/engine/bridge.js:1),
[build version check:10](/Users/ericfode/src/bend-scrabble/scripts/build.sh:10),
[effect boundaries:7](/Users/ericfode/src/bend-scrabble/engine/stream.bend:7), and
[ABI contract:127](/Users/ericfode/src/bend-scrabble/.toolchain/bend/guide/EFFECTS.md:127).

Installed rule: `bend-effect-boundary`. Test failure-path resource handling,
backend selection, and unsupported-target errors. Do not demand a fabricated JS
implementation for an explicitly native-only capability. ABI compatibility and
actual device execution require deterministic builds and runtime observations.

### 9. Cache exactly the semantics being reused

**Transferable design pattern; no cache bug established.** Scrabble's exact table
stores only completed exact results. Its key deliberately omits prior scores
because the stored value is a future spread delta within one scoped search.

Evidence: [key/value contract:5](/Users/ericfode/src/bend-scrabble/engine/transpositions.bend:5)
and [store admission:52](/Users/ericfode/src/bend-scrabble/engine/transpositions.bend:52).

Installed rule: `compiler-cache-identity`. For Knot, make source/import identity,
binding context, compiler semantics, target, and relevant flags explicit inputs
when they affect a cached result. Never promote interrupted checking to a cache
hit marked verified. Test each key dimension independently and include a valid
omission as a clean control. This recommendation is an inference from the cache
contract, not a diagnosed Scrabble defect.

## What belongs in the compiler

Syntax, name resolution, pattern coverage, legal scrutinees, kind/quantity
checking, affine-use counts, proof holes, erased/live separation, and invalid
foreign signatures should produce deterministic diagnostics. Do not ask Jev to
decide whether to accept these programs. For transformations, use laws where
expressible and independent differential tests for execution behavior.

Suggested first calibration order: fuel completeness, F32 order, device stack
growth, pattern sharing, then numeric domains. They have the strongest concrete
examples here. All nine installed rules are drafts with `gate: false`; see
[setup and coverage limits](perch.md). Their positive/negative model separation
has not yet been measured.

The [reuse note](bend-reuse.md) records the existing Bend Jev client and the
TypeScript parser adapter route. A proper parser adapter would let Perch report
exact definition locations and include callers, substantially improving these
checks over whole-file prompts.
