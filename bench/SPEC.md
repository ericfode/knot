# Benchmark extension contract (bench-2)

Fixed before implementation, 2026-09-27. This increment owns `bench/` only.
Existing fixture sources, expectations, compiler sources and gate registration
are unchanged. `bench:verify` is the increment's independent executable gate.

- Discover every fixture in recursion, fields-wasm, closures, baseslice,
  generics and literals from their frozen manifests. Probe both compiler lanes
  on every run. Retain Invalid, Unsupported, Exhausted, HostFailure and
  InternalFailure separately. Never execute an unsuccessful compilation.
- Time accepted programs only. An accepted negative or a wrong result fails
  the run. A seed-valid program classified Invalid is an explicit D4 discrepancy,
  not a language rejection established by this harness.
- Select the frozen `main` observation where available, otherwise the first
  frozen enum-signature call. Structured results may be compiled and evaluated,
  but cannot be called through today's enum-only host ABI. Report that limit.
- Generated families have these literal contracts at sizes 32, 96 and 192:
  Peano parity of `size + 1` successors is `On` (ordinal 1); a list of `size`
  alternating On/Off fielded cells ending in On has final value On; a width
  `size` enum rotates its penultimate constructor to its last (ordinal size-1);
  `size` small flipping functions applied to On return On. Expectations are
  fixed here, independently of generated source, evaluator and Wasm.
- Check new generators with the pinned seed before any Knot timing. Check
  evaluator results against those fixed expectations and every Wasm call
  against that oracle. Semantic mutants remain seed-type-correct but violate
  the fixed expected result.
- Enum modules retain one instance. Fields-profile calls get fresh instances
  because the bounded arena has no reset or reclamation. Instantiation cost is
  included and named. Validation and module compilation stay outside timers.
  An invocation that exhausts the arena or stack is runtime-unavailable with
  its diagnostic retained, never a timing sample or a successful runtime guard.
- A runtime iteration is one measured batch of in-process export calls, not one
  source-language invocation. Each new-suite batch lasts at least 10 ms; record
  actual calls and elapsed nanoseconds and derive ns/call from them. Do not
  discard shorter/faster observations or subtract host overhead.
- Time compiler CLI and evaluator CLI separately. They include lex/parse/check
  and process/file costs. The driver has no phase clock; do not derive fake
  phase times by subtracting different CLI runs or alter compiler output.
- Named-baseline comparisons retain the existing bootstrap/margin verdict and
  refuse incompatible inputs, changed coverage, missing guards or failed runs.
  Two independent unchanged-compiler runs are a noise control, not a speedup.
