# Bend 2 subset stages for Knot

Status: proposed stages, researched 2026-09-26. The first seed-built
[enum compiler](../research/compiler-wasm/README.md) now parses, checks,
independently evaluates, and emits real Wasm. No full language-stage gate has
passed: S1 still needs fields and structural recursion. A bounded handwritten GPU probe has
[hardware evidence](../research/adaptive-tasks/README.md). Bend 2, direct self-hosting, retained GPU execution,
the Wasm target, and adaptive continuation tasks are decided. WebGPU/WGSL is the
working GPU path. The first enum profile pins Bend 2.0.29 and Node 22.22.3 in
[`src/CONTRACT.json`](../src/CONTRACT.json). The broader implementation closure,
host/device ABI and runtime representations remain open. These choices were recorded on 2026-09-26;
the staging below remains proposed. See [the backend plan](WASM-WEBGPU-BACKEND.md).

## Recommendation

Build six cumulative stages: **contract → affine structural core → dependent
computation → Base/proof/template closure → hosted self-compilation → broader
runtime capabilities**. Make the first executable small, but do not call a
simply typed language with unrestricted copying “Bend with proofs postponed.”
Binding, quantities, kind checking, conversion, termination, and erasure are
part of the acceptance contract from the first stage that encounters them.

**S4 is the first proposed stage that can compile and run the entire compiler,
including its driver and transitive dependencies.** This is a design constraint
on future source, not a measured closure of source that already exists. It is
conditional on implementing the Wasm target and its host interface.
S3 should be able to check that source and compile its pure components; a parser
parsing itself, a checker checking itself, and a compiler compiling a toy
program are earlier, distinct milestones.

Use ordinary upstream Base for the seed and ultimately check that exact Base
source with Knot. Keep the compiler's *executed* Base dependency set small.
Do not silently replace `import Base` with a hand-picked, trusted prelude or
claim whole-Base execution support because its declarations check.

## Required GPU path and proposed staging

The user requires: "I definitely want it to still be able to run on the gpu."
The working interpretation is that compiled Bend programs retain a real GPU
execution path for the declared supported subset. The compiler implementation
can bootstrap on CPU; running the entire compiler on GPU is not a prerequisite.
A sequential reference executor is useful but cannot satisfy the GPU objective.

Design the execution model for CPU and GPU from the start. Keep ownership,
closure captures, explicit control/continuations, fork/join, and device placement
visible until backend lowering. Define device-valid values and memory ownership;
do not assume host pointers, stacks, or function objects can cross to a device.
Keep host effects outside device execution. Specify synchronization, completion,
cancellation, and resource reclamation, including device quiescence before reuse.
The choice between a device interpreter and generated native device code is open.

The user selected [adaptive continuation tasks](EXECUTION-MODEL-CASE.md) on
2026-09-26. The compiler's initial sequential execution profile is compatible
with that model. The early GPU gate must exercise suspension/resumption and
transfer of owned pending work, as well as ordered joins; fixed placement is a
comparison baseline. Quantum, layouts, and the concrete phase protocol remain
implementation work.

Proposed gates alongside the language stages:

- **During S1-S2, before fixing the runtime representation:** execute the same
  small pure fork/join computation through a CPU reference and a real GPU backend.
  Exercise owned constructors, allocation/drop, and joins; add closure captures
  when they enter the core. A hand-built IR probe establishes feasibility only,
  not Bend-source GPU compilation.
- **After S3 admits offload syntax, before declaring the combined S4/GPU goal
  satisfied:** compile a supported Bend source fixture through Knot and execute
  it on the GPU. Compare its result with the CPU reference and record the actual
  device/backend and dispatch evidence. CPU fallback cannot pass this gate.
- **Across device gates:** test repeated execution and cleanup, ownership and
  sharing, unsupported operations, resource failures, and CPU/GPU primitive
  agreement under a declared numeric contract. The first bounded tree probe
  passes on Metal; general sharing, allocation, and source lowering are open.
- **In S5:** broaden the supported GPU profile, arrays/numerics, and scheduling.
  Measure balanced/divergent work and launch, synchronization, transfer, and
  compute costs separately. GPU capability is required; a speedup is a separate
  claim requiring measurements.

The first feasibility increment has 12 Bend laws, owning-slot/task quantity
controls, and 38 actual-device runs for a preallocated tree IR. It covers saved
numeric captures, suspension, logical-worker redistribution, ordered joins, and
explicit frontier/round exhaustion. It does not close the entire S1–S2 GPU gate:
general owned constructors, closure environments, allocation/drop, sharing, and
the Wasm host still need validation. See the [probe contract](../research/adaptive-tasks/SPEC.md).

Self-compilation and GPU execution remain separate acceptance gates. A CPU-only
S4 bootstrap may be reported as that milestone, but does not finish the combined
project objective. The Wasm runtime must have a tested WebGPU companion path;
a CPU/Wasm implementation alone is insufficient. The first supported host/device
profile and exact runtime contract remain open beyond the native Node/Metal
probe. Upstream's
[parallel execution model][guide] is reference material,
not a requirement to copy its scheduler.

## Evidence and authority

The inspected official repository is `https://github.com/bendlang/bend`, commit
`574b6d39a235b539eb19a5c532993a0abb3d11ad` (commit date
`2026-09-26 01:11:21 -0300`, subject “The flake names 2.0.29”). A disposable
detached checkout was used; `bun bend2/main.ts version` returned `bend 2.0.29`
under Bun 1.3.14. It was initially a research reference; the first compiler
increment subsequently selected this exact revision as its seed and enum-profile
compatibility pin. The previously observed 2.0.16 binary in
another project's toolchain was neither adopted nor updated.

Pinned primary sources used below:

- [Guide][guide]: intended user-facing language, especially quantities,
  recursion, templates, laws, effects, and modules.
- [Core representation and judgments][core], [conversion][conversion],
  [checking][checking], [templates and book validation][validation]: operative
  reference behavior, including distinctions a high-level guide omits.
- [Base][base]: actual dependency obligations; [loader][loader] establishes
  Base identity and module ordering.
- [Compiler][compiler] and [CLI][cli]: execution, intrinsic, erasure, and
  completeness boundaries; these are references, not a required architecture.
- [Tests][tests] and [test harness][harness]: candidate positive, negative,
  interpreter, JS, and native lanes. Inspect contents before selecting a test.

Observed facts that drive the sequence:

1. Base is not merely primitive declarations. `Word(n)` computes a type;
   `U32` contains `Word(32n)`. `List`, `Maybe`, `Result`, and `Map` carry
   quantities. `Sigma` has a dependent field. `List.map` uses templates.
2. The loader marks definitions from the actual Base file specially. User
   lookalikes named `Nat`, `String`, or `IO` do not inherit Base privileges.
   It loads imported books before validation; runtime dead-code elimination
   is not permission to ignore an invalid unused user declaration.
3. The inspected Base checks with zero holes and contains **466 top-level
   entries, 42 foreign definitions, and two unsafe definitions**, `Array.fork`
   and `Array.join`. It also has bodiless native claims. Counts describe this
   loaded book, not the compiler's future reachable dependency count.
4. Conversion distinguishes symmetric equality from directional “fits”
   checking. Function domains and constructor residuals matter. A syntactic
   type comparison is insufficient even before explicit proof syntax.
5. The reference accepts a partial recursive application when the supplied
   argument spine already establishes descent. “Ban every partial self-call”
   would be an additional restriction, not the reference termination rule.
6. `book_valid` alone does not certify a complete book: a `?TODO` or unfilled
   user law can leave a hole count. The CLI rejects such books. Never translate
   a non-throwing internal checker call directly into `Accepted`.

The source also records an operator-annotation change after 2.0.16
([operator resolution][operators]). Do not mix a newer guide, an older seed,
and test expectations without an explicit compatibility decision.

## Three independent sets

For stage `i`, record these sets separately in a versioned support manifest:

| Set | Meaning | Example |
| --- | --- | --- |
| `I` — implementation profile | Features permitted in Knot's own Bend source and its implementation libraries | Explicit ASTs, owned state, fueled machines; no user `@unsafe` |
| `A_i` — accepted source profile | Source forms and static semantics implemented by this Knot stage | S1 accepts monomorphic structural programs; S3 adds laws and templates |
| `H_i` — target/host capabilities | Runtime operations available when emitting and executing a checked program | Pure constructors before file I/O; CPU bootstrap and required GPU execution have separate gates |

The seed initially compiles `I` even when Knot accepts only `A_1`. This is
normal staged self-hosting. Do not force every early implementation file into
the language it currently accepts. Conversely, do not let implementation
convenience expand `I` without moving the self-hosting closure gate.

Recommended initial `I`: the safe computational fragment available by S3,
plus the S4 driver's narrow IO surface. Allow typed definitions, structural
recursion, explicit fuel, datatypes, affine closures, dependent signatures,
quantity-polymorphic collections, deterministic local imports, and bounded
closed templates when useful. Keep proofs in separate test modules unless
they are required by implementation types. Forbid holes, unfilled user laws,
user `@unsafe`, arrays, floating-point operations, dynamic host imports,
network access, concurrency, and GPU offload in the bootstrap executable.
The unmodified Base dependency has an explicitly inventoried exception for
its declarations; none of its unsafe array primitives may become reachable.

Use two public gates: `check(profile, source)` and
`build(profile, capabilities, source)`. A successful check does not promise
that every host intrinsic has an implementation. Build must check first, then
reject any reachable missing capability **before emitting a runnable artifact**.
Track dependencies through types, proof bodies, constructor telescopes,
templates, and value references as well as direct calls.

## Stage overview

| Stage | Executable milestone | Accepted source addition | Host addition |
| --- | --- | --- | --- |
| S0 | Reproducible seed and reference runner | Written profiles and outcome contract | Pinned development tools only |
| S1 | A small structural program checks, lowers, and runs in Wasm | Monomorphic affine data/functions/matching/structural recursion | Pure allocation, transfer, drop; Wasm engine and minimal host adapter |
| S2 | A generic tree walker and fueled evaluator run | Dependent computation, kind polymorphism, closures, local modules | Closure environments and generic data representation |
| S3 | Knot checks the unmodified pinned Base; pure compiler utilities run | Laws/proofs, templates, complete Base syntax and static rules, essential Base values | Only the selected pure Base execution slice |
| S4 | Entire fixed compiler source builds and executes across generations | Frozen compiler closure plus narrow effectful driver | Input/output, module bytes, diagnostics, artifact delivery |
| S5 | Applications beyond the compiler pass capability-specific gates | Additional profile breadth where needed | Arrays, F32, concurrency, broader GPU support, further effects/targets |

S1's executable exit requires a Wasm emission and execution path. Its parser,
checker, and reference evaluator can develop independently. S3's broad static
work is an intentional cost of using unmodified Base. S5 is a set of separate
extensions, not a prerequisite for declaring S4 complete.
The required GPU track above begins during S1-S2 and adds a source-to-device
gate after S3; its initial feasibility work is not postponed to S5.

## S0 — Freeze a testable contract and bootstrap budget

**Enters.** A selected seed revision/binary and Base identity, a separately
identified behavioral reference, feature IDs, diagnostic outcomes, dependency
receipts, and independent positive/negative corpus manifests. Write the small
core judgments and a definition of observable behavior before claiming parity.
Wasm is selected. Freeze the initial Wasm feature profile, module/host interface,
artifact format, and WebGPU capability policy before their executable gates.

**Implementation.** Seed-built Bend may use `I`. Propose an explicit first-order
syntax tree with binder IDs or indices, source spans, and owned environments.
Do not reproduce TypeScript's host-language closures merely for similarity.
Represent mutually recursive algorithms as tagged machine states with an
explicit stack/worklist and a decreasing fuel parameter where necessary.

**Still unsupported.** All Knot compilation. No claim of accepting Bend input.

**Why / prerequisites.** There is no durable meaning to “matches upstream”
until versions, Base identity, failure outcomes, and resource limits are
fixed. No feature implementation is a prerequisite for the contract runner.

**Programs and gates.** Run a tiny no-Base datatype program, an affine-overuse
negative, an incomplete-law negative, and a template-closure negative through
the selected reference. Record exact input hashes, exit classifications, tool
versions, and lane. A clean re-run must reproduce the classifications. Verify
that an imposed timeout is reported as exhaustion, never a language rejection.
Enumerate the first intended compiler library imports and an empty runtime
capability allowlist; do not invent a completed closure inventory.

## S1 — A sound affine structural slice

**Enters.** Source spans and deterministic parsing; named monomorphic
datatypes and constructors; explicit function signatures; top-level calls;
local value bindings; `Type` versus `Data`; fixed erased/default/reusable
quantities; nested, exhaustive constructor matching in the supported binder
order; first-order structural recursion. Allow dropping affine values.
Require the decreasing parameter first; detect a genuinely unsupported more
general recursive form instead of inventing an unsound acceptance rule.

**Binding contract.** Resolve each occurrence to a binder independently of its
display name. Specify simultaneous local binding scopes, shadowing, weakening,
capture-avoiding substitution, and pattern-bound variables. Preserve source
locations through elaboration. Match branches join usage; sequential operands
add usage. Never sum mutually exclusive branches as if both execute.

**Implementation.** May already use S3 features under the seed. The checker
and evaluator being written are ordinary Bend code; they are not yet
self-compiled. Maintain explicit live/dead checking even for this small slice.

**Host.** A sequential pure Wasm execution path, tagged
constructors, calls, ownership transfer/drop, and a test observation adapter.
No user IO is required. A representation may start simple; copying `Data`
must preserve values, while duplicating an affine value remains illegal.

**Still unsupported.** `import Base`, user modules, numeric/string literal
sugars, generic families, escaping closures, type-level computation beyond
this monomorphic fragment, laws/rewrite syntax, templates, arrays, effects,
parallel notation, and `@unsafe`. Unsupported features fail explicitly.

**Why / prerequisites.** This exercises scope, usage, case trees, recursion,
erasure, and lowering together without pretending machine integers are
independent of Bend's type system. Requires S0 and a Wasm host for the final exit.

**Representative programs.** A `Flag` negator; a recursive `Tree` mirror;
an enum-returning AST classifier. Spell constructors explicitly and avoid Base
names and literal sugars. Compare their constructor results with the upstream
kernel interpreter; upstream's compiled lanes normally require Base, so record
that this is an interpreter comparison, not a seed-generated binary comparison.

**Exit gates.** Positive cases include dropping an argument, using a reusable
Data parameter twice, exhaustive nested matches, and descent on a constructor
field. Negative cases include capture by shadowing, free names, duplicate
declarations, constructor arity/type mismatch, missing/repeated arms, affine
overuse, erased values inspected by live matching, illegal `Data` fields, and
non-decreasing recursion. Property tests check substitution identity/composition
under freshness premises, scope preservation, alpha-renaming invariance, and
evaluation agreement. Test both checker outcomes and executed output. No
emission follows invalid input, unsupported input, or exhaustion.

## S2 — Dependent computation and reusable compiler structures

**Enters.** Dependent function types and applications, erased type parameters,
parameterized datatypes, dependent fields, type-returning definitions, and
dependent match refinement. Add `Quant`, `Kind(q)`, quantity meet, generic
collections written with ordinary declarations, affine lambdas/captures and
partial application, full supported lexicographic descent, and local imports.

Implement normalization and both equality/fit relations over explicit terms.
Keep neutral references stuck until the relevant definition event; preserve
declaration versus definition order. Data declarations may refer forward;
ordinary safe live function bodies may not bypass the definition-order wall.
Do not add arbitrary indexed-constructor/GADT result syntax: the observed
constructor contract returns the family at its own parameters.

**Implementation.** This is the natural representation layer: recursive syntax
trees, persistent environments, lists of obligations, Result-like diagnostics,
and an explicit evaluator/checker machine. Algorithms whose structural descent
is obscure use fuel and return an inconclusive result on depletion. No user
`@unsafe` escape hatch is needed just to write a parser or worklist loop.

**Host.** Closure creation/application, captures owned exactly once, generic
constructor storage, and read-only module contents supplied as a finite source
bundle. This need not introduce filesystem effects inside generated programs.

**Still unsupported.** General Base import, templates, explicit equality proofs
and laws, foreign effects, arrays, floating-point execution, and concurrency.
Use project-named explicit datatypes until S3; do not substitute a partial Base
under the canonical Base name. Remote package discovery/download remains out.

**Why / prerequisites.** Generic AST transformations and environments need
these features. More importantly, the Base dependency requires them. A correct
binding/usage/match core from S1 is prerequisite to extending substitution into
types and dependent fields. Definitional equality enters here independently of
the later equality proposition and rewrite surface.

**Representative programs.** A quantity-polymorphic list length; a dependent
pair whose second field's type depends on its first; a `Word`-like type family;
an affine closure capturing an AST; a small explicit-machine evaluator bounded
by a structural fuel datatype. Use local modules for syntax and evaluation.

**Exit gates.** Test capture preservation, dependent substitution into constructor
telescopes, matching-refined goals, beta conversion, neutral/stuck types, and
directional fits versus symmetric equality. Accept a shrinking partial self-call;
reject bare/non-shrinking self-references and erased-column fake descent.
Reject closure duplication even when all captured values are Data, and reject
generic misuse hidden behind an alias. Cover imports with alias shadowing,
canonical identity, a real locally constructed diamond, cycles, missing files,
and definition-order effects. Compare closed evaluator results and every
negative classification against the reference. A normalization budget failure
is not evidence that two types differ.

## S3 — Check Base honestly; add proof and template closure

**Enters.** Paired `law`/`def`, equality types, reflexivity, explicit-motive
rewrite, empty elimination, dependent witnesses, cross-module law filling,
holes as diagnostics (never successful compilation), closed `~` templates,
and all syntax/static rules exercised by the pinned unmodified Base. This
includes numeric/string literal elaboration, operators, collection sugars,
`do` desugaring, foreign declaration shapes, and parallel/offload annotations
as checked syntax. Recognizing a host operation does not implement it.

Templates require capture-avoiding substitution, closed arguments, stable
instance identity, definition-order discipline, instance checking, and cycle
guards. A runtime closure that captures a caller's local state cannot be
silently turned into a reusable template argument. Deduplicate equivalent
instance keys under a specified scheme; never reparse generated source as the
semantic definition of an instance.

**Base policy.** Load and check the whole exact Base file, including ordinary
bodies and laws. Inventory privileged native claims, foreign declarations, and
the two observed unsafe array definitions by identity and source hash. Allow
those declarations to be checked without claiming a safe proof theorem about
the entire Base book. User-created names/files gain no privilege. User
`@unsafe` remains outside the bootstrap profile; attempting to reach the unsafe
Base array primitives fails its capability/profile gate, including through
aliases, templates, and proof/type dependencies where relevant.

**Pure execution slice.** Support Nat/U32, Bool/Cmp, Char/String, List,
Maybe/Result, pairs, and the small selected set of list/string/numeric
operations the compiler uses. Prefer source definitions before intrinsics.
Map/Set are optional conveniences: add only if their closure beats a simple
explicit environment. Fully check unused Base code, then limit emitted code
by sound runtime reachability after checked erasure. Do not skip validation
because an unused declaration would later be erased.

**Implementation.** Compiler utilities can now use ordinary Base, closed
templates, and a small reusable library instead of duplicating each list walk.
Whole-Base *static* closure is intentionally larger than compiler execution
closure. Keep all actual compiler code within `I`; full Base syntax support
does not grant arbitrary new implementation dependencies.

**Host.** Pure values, integers, Unicode conversion under a specified text
contract, and deterministic artifact buffers. Sequential evaluation of pure
parallel bindings may be an explicit semantic-only capability, as in the
upstream JS lane. It is not a parallel-performance claim. The separate GPU
profile must define offload behavior and demonstrate actual device execution;
CPU fallback does not count as passing its gate.

**Still unsupported for execution.** File/process/network effects, live foreign
imports, array operations, F32 operations, channels, shared-array atomics,
GPU offload outside the separately gated GPU profile, and user unsafe code.
A checked but runtime-unsupported request
gets `UnsupportedCapability`; it does not produce an artifact with a latent
missing intrinsic. Generic/higher-order uncertainty requires a conservative
capability set, not a direct-call-only scan.

**Why / prerequisites.** Standard Base forces dependent types, proofs,
templates, and privileged declarations into the front-end closure. This is
the point at which supporting a useful library stops being a list of isolated
features. Requires S2's substitution, evaluator, kinds, and module identities.

**Representative programs.** The upstream `List.map` examples; a token stream
lexer over String; a scope-aware AST serializer using Lists/Results; a proved
list-length property; generic IO syntax checked without execution; actual
unmodified Base. `tests/spec/comp_map_mint.bend` is a concrete template case.

**Exit gates.** Knot checks the complete pinned Base without a pre-validated
seed snapshot or a call to the upstream checker. Every exception is listed.
Keep positive proofs and false equalities, wrong rewrite motives, fake empty
elimination, unfilled laws, `?TODO`, live use of erased evidence, template capture,
and cross-instance recursion negatives. Require zero unresolved user holes.
Compare interpreted and target results for the supported pure slice. Test
erasure preserves witnesses/data while removing only erasable evidence and
type arguments; test nested dependent fields and closure environments.
Cross-check U32 wraparound and division/shift edge behavior, Nat boundaries,
strings with non-ASCII characters/NUL, and literal-versus-constructor views.
Check-only fixtures and runnable fixtures must remain different lanes.

## S4 — Host the compiler and close the bootstrap

**Enters.** The narrow driver: source/dependency bytes in, structured diagnostics
and target artifact bytes out. If the compiler is a CLI, add argument parsing,
read, write, and exit/reporting effects through the selected host interface.
If it is a hosted pure entry point, the host supplies the entire source bundle
and receives the result. Either is compatible with direct self-hosting; record
which adapter belongs to the trusted execution environment.

For an IO-based driver, implement checked IO construction/bind and affine
handles/results before executing effects. Map only the declared Base effects
needed by the driver. Supporting upstream `.c`/`.js` foreign bodies on a new
target is not automatic: unsupported custom foreign imports must be refused.
Never execute a host effect during elaboration, normalization, or proof checking.

**Implementation.** All compiler files, including parsing, checking,
elaboration, lowering, selected backend, driver, and every imported library
must satisfy the frozen implementation manifest. Prefer deterministic source
bundles over runtime package fetching. A launcher may move bytes or invoke a
declared assembler/linker; it may not secretly parse, check, or compile Bend
on behalf of the self-built compiler.

**Host.** Wasm needs an engine, module validation/instantiation, and a narrow
import/export ABI. Source/dependency bytes enter and artifact/diagnostic bytes
leave through owned buffers. Programs using the GPU also need a WebGPU adapter,
WGSL pipeline creation, buffers, dispatch, synchronization, and error reporting.
These dependencies remain separate from the Bend compiler's own source closure.
Pin the runner, adapter, and any external assembler used during bootstrap.

**Still unsupported.** Any feature outside `I`/the selected accepted profile,
unlisted effects, remote resolution, user unsafe code, arrays and F32 in the
bootstrap implementation, concurrency in that implementation, GPU capabilities
outside the separately tested profile, and additional targets. CPU self-hosting
does not waive the required source-to-GPU acceptance gate.

**Why / prerequisites.** S3 supplies the static and pure computational closure;
S4 supplies the remaining host/backend closure and proves it by execution.
Real compile/check resource consumption is measured here. A toy closure list
or a build that succeeds only through an upstream fallback does not pass.

**Representative programs.** Compile the same small multi-module project from
a CLI/source-bundle adapter, emit and execute its artifact, reject a malformed
dependency, and finally compile the entire compiler's exact fixed source.

**Exit gates.** The bootstrap protocol below passes. Missing source files and
host read/write failures are separately reported. Check stable byte encoding,
diagnostic spans, module order, output hashes, exit behavior, capability
refusals, and bounded failure. A generated compiler must compile both itself
and the independent positive/negative corpus without invoking the seed.

## S5 — Extend by capability, not by bundling everything

**Enters / ordering.** Broaden the earlier required GPU path and pure fork/join
profile under separate contracts. Consider ordinary owned arrays for measured
workloads, F32 for numeric applications, then concurrent IO/channels and shared
arrays/atomics. These are candidates, not a mandatory order where there is no
dependency. Other targets and remote package distribution are independent
tracks. Admit user `@unsafe` only under a separately named unsafe profile with
accurate proof/termination claims.

**Implementation.** Keep the compiler on `I` until measurements justify changing
it. Adding an array optimization to generated programs does not require the
compiler to start using arrays; the converse changes the bootstrap closure.

**Host.** Arrays need the observed get/swap/set/clone and wrapping-index
semantics; an optimization must refine their structural meaning. `Array.fork`
and atomics introduce shared mutable storage and cannot be equated with an
ordinary owned array. Parallelism needs scheduling, ownership/drop rules,
failure propagation, and effect ordering. F32 needs an explicit numerical and
conversion contract, including bit patterns and exceptional values.

**Still unsupported.** Every capability not individually gated, arbitrary FFI,
unmeasured performance guarantees, and any claim of full Bend conformance.

**Why / prerequisites.** These broader capabilities are not inherently necessary
for a compiler using lists, strings, owned worklists, and a narrow driver.
The initial GPU path is already required and gated earlier. Add further breadth
after S4 unless target feasibility proves an earlier dependency; if so, move it
explicitly without silently expanding the bootstrap implementation profile.

**Representative programs and gates.** Owned-array swap/clone/wrapping-index
tests; F32 bit round-trips and numerical edge cases; balanced tree reduction;
ordered effect traces; channel progress/deadlock fixtures; racing atomic
operations. Retain negative ownership tests. Compare sequential and parallel
observable results before claiming speedups, then measure scaling separately.
Every implementation-profile expansion reruns closure and bootstrap gates.

## Essential Base dependency budget

This is a proposed *selection policy*, not an already computed call graph.

| Need | Start with | What enters the closure / restraint |
| --- | --- | --- |
| Syntax and environments | Project datatypes, List, Maybe/Result | Quantity parameters, Kind meet, constructors/matching; avoid generic library imports with no concrete use |
| Positions and names | Nat/U32, Char/String | `Word` family, literal identities, integer/text behavior; do not assume host UTF-16 indices are source-byte offsets |
| Returning state | Explicit records or pairs | Dependent Sigma/Pair definitions still check even if a particular pair is nondependent |
| Repeated transformations | Named recursive helpers; a few closed templates | No repeatedly called affine closure; `List.map`/fold templates are allowed when they shrink duplication |
| Lookup tables | List-backed environment first | Map/Set only after measuring lookup cost and recording their added closure |
| Compiler loops | Tagged states, fuel, worklists | No implicit general recursion or seed-only exceptions; make exhaustion explicit |
| Output | List/chunks of bytes or text | Avoid quadratic concatenation; a binary target does not inherently require mutable Bend arrays |
| Driver | Bundle adapter or narrow IO/Result surface | Only the chosen read/write/args/exit boundary; no Jev/network dependency in semantic acceptance |

Maintain two machine-readable inventories once source exists:

1. **Static closure:** every imported source, declaration, type/proof dependency,
   generated template instance, Base privilege, and feature used. Validate all
   included user declarations, not merely `main`'s runtime call graph.
2. **Execution closure:** definitions and capabilities that survive checked
   erasure and are reachable from compiler entry points, including returned
   closures and possible indirect calls. Treat uncertainty conservatively.

Each inventory entry should include an identity/hash, reason for inclusion,
owning stage, and introducing source span. Fail CI when implementation source
adds an unapproved feature, dependency, foreign primitive, or capability.
Check canonical local module identity, aliases, and stable definition/instance
ordering. Never grant Base privilege just by spelling or pathname resemblance.
Verify the closure under both seed-built and self-built tools, plus an
independent audit of its manifest; do not trust a compiler solely to report its
own omissions. Keep a cold build that checks Base from source even if a cache
later makes ordinary builds faster.

The budget controls the **implementation**, not every feature the compiler
can accept. A compiler can implement proofs using data structures without
containing large proofs in its own executable closure.

## Restrictions that must be named, and their cost

- **Early profiles are deliberately incomplete.** Recognized but unimplemented
  valid Bend is unsupported, not invalid. Name the exact profile in every
  result. Do not describe S1 or S2 as a general Bend 2 compiler.
- **No user unsafe code.** This avoids adopting upstream's broader unsafe
  acceptance/proof boundary, but costs explicit fuel, state machines, and
  additional helper definitions. Termination of the compiler implementation
  does not imply it can decide every input within its resource budget.
- **No mutable arrays in the bootstrap implementation.** Lists/persistent
  structures simplify closure but may cost memory and lookup/append time.
  Measure this on real source; do not defend the restriction after it becomes
  the dominant obstacle. Moving arrays earlier changes the declared S4 gate.
- **Local, frozen modules only.** This costs an external dependency acquisition
  step. It avoids network/cache mutation inside compilation and makes hashes
  and source identity reviewable. Missing material is a resolution failure.
- **A smaller prelude is an alternative, not the default recommendation.** It
  could move self-compilation earlier, but would require a maintained Bend
  library/dialect, explicit import names, numeric/literal decisions, and seed
  compatibility tests. Never relabel it Base or trust an extracted declaration
  set without proving its static closure. Rejecting full Base is an honest
  early restriction; pretending to support it partially is not.
- **Source representation freedom is real.** Explicit ASTs and machines fit
  Bend naturally. There is no requirement to port the TypeScript layout,
  preserve its pass boundaries, or generate identical C.

Cannot safely postpone once the corresponding construct is accepted:
capture avoidance and binder identity; affinity/kinds (including captures and
branches); checking before erasure; dependent substitution and conversion;
termination/definition-order rules for recursive safe definitions; correct
Base identity; closed and checked templates; unresolved-proof detection; and
effect isolation. Postpone their *syntax or capability* by refusing it, never
their enforcement while accepting the program.

## Outcome and observational contracts

Use structured outcomes with stable codes and source spans where possible:

| Outcome | Meaning |
| --- | --- |
| Accepted / Checked | Complete supported book passes the declared static profile; no unresolved user obligations |
| Built | Checked book also fits target capabilities and an artifact was produced |
| Invalid | A supported rule establishes a syntax, scope, type, quantity, termination, or completeness violation |
| UnsupportedFeature / UnsupportedCapability | This profile cannot handle a form or reachable operation; no judgment of validity is implied |
| Exhausted | A declared time/step/heap/stack/instantiation budget prevented a decision or execution |
| ResolutionFailure / HostFailure | Required source or an external operation failed; preserve the cause |
| InternalFailure | An invariant or implementation failed; never classify this as invalid user input |

On mixed inputs, report the rule actually reached; an early unsupported form
does not prove that the remainder is valid. A hole/open law may be valid editing
syntax but is **incomplete and invalid for final compilation**. Diagnostic
inspection is allowed; executable emission is not.

Distinguish language-defined numeric behavior from compiler resources.
U32 wrapping is not exhaustion. The inspected native/JS Nat paths fail past
`2^48-1`; choose whether the compatibility contract includes that runtime bound
before S3 execution gates. Do not substitute host integer overflow or silently
advertise arbitrary precision. Likewise, the reference's template key/depth
limits are operational guards; Knot's budget exhaustion is inconclusive, even
if the reference prints an ordinary error for a similar guard.

For pure programs compare canonical observable values, including observable
data constructors and supported numeric/text semantics. For proof-only inputs
compare completeness/acceptance, not an invented runtime proof object. Observe
closures through specified applications. For IO compare exit status, output
bytes, ordered effect requests/results, and produced files under a fixed host
fixture. Timing and allocation counts are separate measurements. Parallel
effect traces require a documented equivalence relation before inclusion.

Keep independent hand-written positive/negative tests alongside inspected
upstream fixtures and generated tests. Minimize disagreements; classify them
as Knot defects, reference defects, specified differences, unsupported features,
or inconclusive runs. Do not silently edit expected outputs to fit either tool.
Test generated code against a small evaluator separately from checker
agreement. A test suite entirely generated by the compiler under test cannot
independently validate its scope or rejection rules.

## Bootstrap protocol and first self-compiling stage

Let `S` be a fixed source bundle for the **whole** compiler plus its exact
transitive Bend dependencies. Let `U` be the pinned seed and `E` the selected
execution environment/toolchain. The S4 claim requires:

1. `U(S)` builds runnable seed-built compiler `C1`. Record how it was built;
   upstream may use C for this seed artifact without choosing C as Knot's target.
2. Running `C1` on `S` produces `A2`. No upstream checking or compilation
   fallback is permitted inside this operation.
3. `run_E(A2, S)` produces `A3`. Run both generations on the independent
   positive/negative/capability corpus, including cases unlike compiler source.
4. Compare `A2` with `A3` under a documented deterministic generation contract:
   fixed source/import order, canonical names, template ordering, options,
   target settings, environment, runtime identity, and excluded metadata.
   Prefer byte equality of Knot's direct output. Compare reproducible IR/object
   inputs separately if an external linker injects nondeterminism; name any
   normalization rather than hiding differences. Optionally build `A4` to
   investigate instability, not to mask it.
5. Compare the compilers' diagnostics, accepted/rejected/unsupported sets,
   exhaustion classifications, and executed program behavior. A byte-stable
   compiler can still be wrong; this is not checker soundness or conformance.

The seed's artifact and Knot's artifact may use different targets. Neither
generated-C equality with upstream nor removal of the VM/linker/host from the
trusted base is required. The compiler's first complete closure is S4 only if
the source inventory proves it: using an S5 feature moves that boundary, and
an unfinished compiler cannot satisfy it by compiling a smaller driver alone.
Separately, require the self-built compiler to emit the supported GPU fixture
and run it on a recorded device before claiming the combined project objective.

## Target-dependent decisions and evidence gaps

| Decision | When it blocks | What must be settled |
| --- | --- | --- |
| Compatibility and seed pins | S0 | Exact source/Base/tests and seed binary provenance; 2.0.16 and observed 2.0.29 are not interchangeable |
| Wasm feature profile and value/call representation | S1 executable exit; S2 closures | Wasm/WebGPU feasibility, allocation/drop, closures, device-valid layouts, explicit control, artifact format |
| Driver form and effect ABI | S4 | Hosted source bundle or CLI; bytes/text ownership, error protocol, IO and foreign mappings |
| Numeric/text contract | S3 execution | U32 edges, Nat bound, Unicode units/encoding, literal normalization and source spans |
| Base trust inventory | S3 | Native/opaque declarations and unsafe Base exceptions; no unproved whole-book safety claim |
| Compiler resource budget | S2 onward, measured at S4 | Fuel accounting, worklist/memory representation, resumability/retry and diagnostics |
| Parallel meaning and required GPU path | S1-S2 device feasibility; S3 source-to-device gate; S5 breadth | Fork/join and ownership semantics, WebGPU/WGSL lowering, host effects, first hardware/host profile; CPU fallback cannot satisfy the GPU gate |

Unresolved evidence: no compiler implementation closure, target performance
benchmark, memory profile, or cross-generation artifact exists. The bounded
task/device prototype is separate from the checker probes below, which did not
build native/JS fixtures or run the cluster suite. Those original probes
establish reference checker behavior only. The official Lean core
is useful material for later rule review; no Lean proof was executed or
transferred to Knot, and source-to-model correspondence is not assumed.

## First executable increment and next stage

The no-Base enum path is implemented: **parse, resolve, check, independently
evaluate, emit Wasm, validate and execute**. `src/catalog.bend`, `src/scope.bend`
and `src/check.bend` resolve and check one lexical-level representation;
`src/eval.bend` runs a source machine; `src/wasm.bend` maps it to compact live
locals and emits binary sections through the published ByteOutput package.
Neither backend uses the other's output as its oracle.

The [milestone audit](../research/compiler-wasm/README.md) links exact commands,
hashes, dependencies and retained modules. Native and Bun builds agree byte for
byte on 25 programs; 90 fixed calls agree with the upstream interpreter,
independent evaluator and actual Node Wasm execution. Rejection tests include
affine reuse, erased live use and missing match arms. Eighteen filled laws cover
specific frontend, checker, source-machine and codec properties; they do not
constitute a whole-compiler refinement proof.

This completes the bounded enum milestone, not the full S1 profile above.
Next add owned constructor fields and structural recursion, with explicit
allocation/drop and continuation layouts that can serve both Wasm and the
required WebGPU path. Keep source-to-device execution and full self-hosting as
separate acceptance gates. Preserve the current enum corpus as regression
evidence while widening the accepted profile.

## Research receipt and reproducibility

The disposable investigation cloned the official repository, checked out the
commit above detached, and imported `bend2/bend.ts` directly. Each of the 17
fixtures below received a **fresh** `book_nil()`, `book_load()`, and
`book_valid()`; the probe then read `book.hols`. No execution/code-generation
claim is made. The outcomes were 7 complete checks, 8 thrown rejections, and
2 incomplete books. A separate fresh load/check of Base produced the inventory
above. Probe directory: `/tmp/knot-bend-subsets.4rKTwA` (disposable, not a
required project dependency).

| Fixture under the pinned upstream tree | Observed outcome |
| --- | --- |
| `tests/check/partial_self_call.bend` | Checks; zero holes |
| `tests/check/linear_binder_discard.bend` | Checks; zero holes |
| `tests/check/mutual_type_def.bend` | Checks; zero holes |
| `tests/proof/reflexivity_basic.bend` | Checks; zero holes |
| `tests/proof/dependent_pair.bend` | Checks; zero holes |
| `tests/proof/word_hom_axiom.bend` | Checks; zero holes; file contains an actual Word proof |
| `tests/spec/comp_map_mint.bend` | Checks; zero holes |
| `tests/import/alias_twice.bend` | Rejects duplicate import alias |
| `tests/check/negative_data_reuse.bend` | Rejects repeated affine function use |
| `tests/check/lambda_single_use.bend` | Rejects closure duplication |
| `tests/check/erased_match_ctor.bend` | Rejects erased live scrutinee |
| `tests/spec/comp_capture_linear.bend` | Rejects open template argument |
| `tests/check/template_inst_cycle.bend` | Rejects non-decreasing instance cycle |
| `tests/parse/ctor_indexed_target.bend` | Rejects constructor result-annotation syntax |
| `tests/check/hole_todo.bend` | Internal check returns with one hole; CLI contract refuses |
| `tests/check/axiom_warn.bend` | Internal check returns with one hole; CLI contract refuses |
| `tests/import/diamond_dedup.bend` | Rejects absent `/diamond/top.bend`; does not demonstrate a successful diamond |

Minimal replay shape, run with Bun against the detached checkout and the exact
fixture paths above (local fixtures only; no hub imports):

```ts
import * as B from './bend2/bend.ts';
const book = B.book_nil();
try {
  await B.book_load(book, process.argv[2], '', new Map());
  B.book_valid(book);
  console.log(book.hols ? `incomplete:${book.hols}` : 'checked');
} catch (e) {
  console.log(e?.$ === 'Err' ? B.err_show(e) : String(e));
}
```

Inspect the thrown category in a production runner: the research probe's
generic exception printing is not the proposed Invalid/Exhausted classifier.
Count Base entries using `Object.entries(book.tlds)` after loading
`B.BASE_BEND`; foreign definitions have `i`, unsafe definitions have `u`.

SHA-256 of inspected files:

```text
bend2/bend.ts   09d2cc5c5d757f1a694dd126ccbac72ef2374cfe948d9d51c2b08247c5d2581e
bend2/base.bend 22eea83911e2395f63594fea7c10ac0c1e5b548251681fc97cd7667e0eb7031b
bend2/comp.ts   0cf866b28ff273d47970b3c16e82288e9676ce9f0ea3fce49877a82ce4a6301b
bend2/main.ts   0a6c19ee942ec4fadcf7daaa69ca1cfd395a5ee8ef130df72b548291def93884
guide/GUIDE.md b285b81366683203623777d8d0136eb48c3f8fec75ea712db482749376326106
```

[guide]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/guide/GUIDE.md
[core]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/bend.ts#L94-L240
[conversion]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/bend.ts#L2988-L3110
[checking]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/bend.ts#L3119-L3627
[validation]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/bend.ts#L3628-L3787
[base]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/base.bend
[loader]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/bend.ts#L951-L1020
[compiler]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/comp.ts
[cli]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/main.ts#L763-L826
[tests]: https://github.com/bendlang/bend/tree/574b6d39a235b539eb19a5c532993a0abb3d11ad/tests
[harness]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/gates/test.ts#L1-L99
[operators]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/bend.ts#L706-L713
