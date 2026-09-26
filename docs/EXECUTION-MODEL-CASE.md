# Knot's execution model: adaptive continuation tasks

Decision accepted 2026-09-26: **adaptive continuation tasks**. The user chose:
"Adaptive continuation tasks it is then". Wasm and retained GPU execution are
also user decisions. WebGPU/WGSL is the working device path. A bounded
[task protocol/device probe](../research/adaptive-tasks/README.md) now executes
on hardware. A compiler backend and hardware performance benchmark remain open.

## Selected direction

Use a **strict affine continuation machine** as the common semantic target.
Compile its sequential execution to Wasm. For the GPU, start with **bounded
local execution and dispatch-separated exchange of task/continuation records**.
Keep enough structure to redistribute exposed independent work between phases.
Use regular map/reduce/scan regions as future candidates for specialized fused
kernels. Retain fixed placement as a baseline and potential fast path.

The execution-model choice is settled. Task/frame layouts, scheduling quantum,
work distribution policy, allocator and reclamation, host ABI, and bytecode
versus specialized shaders remain implementation decisions. The dispatch-phase
protocol below is the broader design. The first probe checks its tree-task
subset on Metal; general allocation, sharing, portability, and performance
still require evidence.

This preserves what is already useful in Bend 2: ownership, explicit sharing,
explicit forks, and continuations. The proposed changes concern scheduling,
publication, resource bounds, and host/device representation. They do not
require turning the language back into interaction nets or weakening affinity.

Semantics support this as a practical first architecture. They do **not** prove
it fastest. Work distribution, dispatch overhead, bandwidth, divergence, code
size, and live memory require measurements against the alternatives.

## What the current Bend runtime actually tells us

The inspected reference is Bend 2.0.29 at
`574b6d39a235b539eb19a5c532993a0abb3d11ad`. This is a research/toolchain pin, not
an implicit decision about Knot's final source-compatibility release.

Its [runtime paper][bendrt] describes a flat continuation machine with grow/work
phases and a transposed task grid. Assignment is not repaired by work stealing.
It explicitly places workload balance on the programmer and acknowledges
unverified runtime code. So phase scheduling is an existing Bend idea; the new
proposal is movable, budgeted continuations plus a portable publication/lifetime
contract. The paper's fixed dimensions and benchmark pin are historical details;
the newer [compiler source][comp] contains configurable grid sizing.

The paper's reported M4 Max measurements support caution: n-queens is 1.24 s on
GPU versus 0.46 s on 16 CPU threads; symbolic regression is 0.54 s versus 0.29 s.
Those are the authors' reported Metal results at `64fc4b7` (2026-08-31), **not
rerun here**, and not WebGPU measurements. They indicate that “has abundant
parallelism” is insufficient to predict the GPU winner. They do not isolate
scheduling as the cause of each loss.

Source inspection adds a concrete portability issue. `task_deliver` writes
result words, decrements a join counter, and lets the final child resume the
join. The CPU path uses release/acquire operations; device paths combine
relaxed atomics with Metal/CUDA fences (`comp.ts`, FENCE definitions around
3438–3465, atomic wrappers around 3743–3765, delivery around 4359–4376).
WGSL offers relaxed atomics and workgroup-scoped barriers. This protocol cannot
be translated by merely renaming its atomics. This is a WebGPU port obligation,
not a finding that the current Metal/CUDA implementation is broken.

## The choices are on different axes

Evaluation order, representation, scheduling, and code generation are separate.
A bytecode VM can use fixed placement or adaptive phases. Specialized WGSL can
use the same scheduler. A net calculus can also use phase queues. “Wasm versus
interaction nets” is therefore not a complete choice: Wasm can host either.

| Model | Best semantic argument | Main cost or obligation | Position for Knot |
|---|---|---|---|
| Sequential strict Wasm | Affine values map directly to moves; call order and effect dependencies are easy to inspect. | No parallel speedup; deep non-tail calls need stack discipline and bounded failure. | Initial self-hosted compiler and reference baseline. |
| Fixed fork/join placement | Independent owned children require little scheduling coordination; regular balanced work needs little repair. | Static type/ownership information does not establish equal work; skew leaves lanes idle. WGSL joins still need publication proof. | Benchmark baseline; plausible fast path for balanced workloads. |
| Adaptive continuation tasks | Independent pending computations can move without changing pure results; explicit frames permit bounded suspension. | More state, compaction, allocations, and phase latency. It cannot parallelize a serial chain. | Selected general execution model; correctness and performance gates remain. |
| CPU work stealing | A fully strict task DAG supports strong scheduling bounds under the relevant shared-memory model. | Deque linearization, weak-memory publication, and reclamation are nontrivial; CPU theorem does not establish WebGPU progress. | Later CPU-parallel option. Do not make a portable persistent GPU deque the first project. |
| Interaction nets | Local rewriting and confluence give an attractive foundation for independent reduction and graph sharing. | Must prove Bend encoding/readback, sharing/erasure, and actual memory protocol; pointer traffic and rewrite administration may dominate. | Separate experimental branch only if a concrete sharing-heavy workload justifies it. |
| Array/data-parallel kernels | Fusion and lawful flattening can remove intermediate storage and expose coalesced, uniform work. | Requires recognizable structure and valid associativity/shape laws; does not directly cover the entire language. | Strong candidate fast path for regular numeric/data workloads, after the general core works. |
| Demand/lazy graph evaluation | Can avoid unused work and share a demanded computation. | Thunks, updates, retention, and contention; differs from the compiled strict profile in resource behavior. | Consider for normalization or a separately specified mode, not an accidental runtime change. |

The [full law set](EXECUTION-MODEL-LAWS.md) defines the domains and witnesses
behind each row. None of these models is universally fastest for all programs.

## What can actually be derived from the semantics

**Ownership favors coarse tasks over universal graph administration.** For an
affine value used once, a general duplication graph has no sharing benefit to
recover on that path. A direct move can suffice. This is a local argument; it
does not prove that interaction nets lose on programs with substantial reusable
data or that our direct code generator will optimize well.

**Purity permits schedule changes; it does not provide a balance oracle.** We
can move independent tasks while retaining logical output slots. Equal input
sizes can still hide unequal work. An adaptive scheduler has a semantic right
to redistribute exposed work, but must earn its overhead back in saved idle
time. A bounded quantum cannot split an indivisible sequential computation into
parallel work.

**Explicit continuations fit the device language.** WGSL forbids recursive calls.
Represent a suspended call by a code tag, captures, destination, and frame state;
execute it through a loop. Defunctionalization supplies the conventional
construction, rather than requiring a new evaluation calculus. This does not
require every source call to allocate a heap task: tail calls can loop and
local non-tail calls can use a private frame stack. [Reynolds][reynolds],
[WGSL function restrictions][functions].

**Fusion can offer a demonstrable cost improvement.** A pure
`map f (map g xs)` can become one map, eliminating its intermediate array under
the stated domain. Reduction order can change only when the operation is
associative under the selected machine semantics. Futhark's research is a useful
precedent for combining uniqueness, fusion, and flattening; it is not evidence
that arbitrary Bend functions already have those properties. [Futhark's PLDI
paper and summary][futhark].

**WebGPU favors explicit communication phases as a first correctness story.**
Dispatch scopes provide the publication boundary missing from a naive relaxed
ready-flag protocol. Multiple dependent dispatches can be encoded without a CPU
readback after each one; data can remain resident. The host still needs an
explicit completion, capability, and resource protocol. [WebGPU spec][webgpu],
[GPUWeb explanation][dispatch], [WGSL memory model][wgsl].

**Confluence and work stealing theorems have limited scope.** Strong confluence
of interaction nets concerns abstract reductions. It does not establish the
correctness or cost of our Bend encoding. CPU work-stealing bounds likewise
assume a particular computation and scheduler/machine model. ABP's dedicated
processor specialization has expected `O(W/P + S)` time; its result does not
justify a WGSL implementation. [de Falco][nets], [Arora–Blumofe–Plaxton][abp].

## Proposed first GPU machine

1. **Input phase:** each invocation receives an owned work record from an
   immutable frontier. State includes continuation tag, captures, result
   destination, local frames, and remaining quantum.
2. **Local work:** execute a bounded number of semantic operations. Tail calls
   loop. Use a private explicit stack for sequential subcalls. Forks can remain
   local while work is sufficiently distributed; exposing a fork must preserve
   capture ownership and logical result slots.
3. **Output phase:** write yielded tasks or child completions into assigned
   regions. A simple first implementation reserves bounded regions per input;
   this avoids a persistent cross-workgroup queue. Checked atomic reservation
   or scan-based compaction can replace that after their laws are established.
4. **Join phase:** in a later dispatch, one invocation per join checks published
   slots and emits its continuation at most once. The next work phase consumes
   it. Local same-workgroup joins can be optimized later with a separate proof.
5. **Exchange/reclaim:** compact live output if needed, preserve logical
   identities, retire dead records, and start the next phase. Reuse storage only
   after its readers are quiescent. A prototype may pin immutable shared data
   for an epoch; the resulting retention cost must be measured.

There is no kernel-wide spin barrier. All loops, including large copies/drops,
must be bounded or yield. A task's running registers and stack cannot simply
move by copying its task ID: they must be captured in its checkpoint. If a
paused task has latent independent fork branches, expose those branches to gain
parallelism; moving an otherwise serial stack only changes placement.

This first version deliberately gives up immediate cross-workgroup join
execution. Its risk is excessive rounds and retained memory. The benefit is a
publication and reclamation boundary we can state, test, and refine.

## Performance prediction and what would overturn it

Use an accounting estimate, not a claimed theorem:

`T_gpu ≈ W/(P·utilization) + dispatch_count·dispatch_cost + bytes/bandwidth`
`        + allocation/scheduling_cost + compile_cost/reuse_count + transfers`.

The terms can overlap, so measure them instead of treating the sum as exact.
Relevant counters are useful work, lane work distribution, dispatches, active
frontier size, peak live/retired bytes, bytes copied, and compilation/transfer
time. Report cold and warm end-to-end time separately. High GPU occupancy does
not by itself imply useful speedup.

| Experiment | Compared implementations and observations | Decision rule |
|---|---|---|
| Balanced binary reduction with tunable leaf work | Sequential Wasm, fixed phases, adaptive phases; equal answers, records, rounds, peak bytes. | Keep fixed placement as default for this class if redistribution adds cost without reducing idle time. |
| Skewed **splittable** tree | Same total work; expose irregular independent descendants. | Adaptive phases earn adoption only if reduced imbalance exceeds their scheduling/dispatch cost. Include an opaque heavy leaf as a negative control. |
| Long serial recurrence | Small and large quantum; checkpoint counts and end-to-end time. | CPU execution should remain available; small quantum is a responsiveness choice, not a parallel speedup claim. |
| Allocation/share/drop stress | Distinct and reused `Data`, phase-delayed reclamation, tight capacity. | Reject a design that violates ownership or silently loses work; quantify retained-memory penalty separately. |
| Dense map/reduce pipeline | General task machine versus fused WGSL for the same supported region. | Add structured lowering when saved traffic/dispatches justify compiler complexity and all algebraic premises hold. |
| Bytecode versus specialized WGSL | Same IR and scheduler, different instruction delivery. | Compare shader compilation, module size, runtime dispatch overhead, and repeated-use break-even; do not conflate scheduler and emitter gains. |
| Sharing-heavy higher-order fixture | Direct machine versus a separately correct net prototype, if built. | Net work must demonstrate reduced total cost including encoding/readback and storage; reduction count alone is insufficient. |

Use fixed seeds, source/artifact hashes, device/driver/feature limits, warmup and
multiple timed repetitions. Check noncommutative results and ordering before
timing. Compare the reference and CPU paths, but require an actual device
submission/result receipt for a GPU claim. First-device success is feasibility;
the portable profile also needs independent implementations/adapters.

## Delivery and decision state

The research includes [18 checked abstract join equations and four semantic
mutants](../research/execution-models/README.md), plus the first
[affine task/device increment](../research/adaptive-tasks/README.md): 12 Bend
laws, quantity-negative controls, and 38 WebGPU runs on a non-fallback Apple
M5 Max Metal adapter. Independent Bend values catch three shader mutations.
Fixed and adaptive placement agree semantically on selected fixtures; no timing
comparison has been made. The device machine uses a preallocated tree, saved
unary/binary captures, and prepare/execute/join phases. It is handwritten WGSL,
not a Bend-source backend or Wasm host. Full refinement remains open.

Next, refine the owning slot, continuation/join, and bounded frontier contracts
into reusable indexed storage. Add a compiler-emitted representation while
retaining independent observations. The first compiler still targets sequential
Wasm; source-to-device execution and performance need separate gates. Package
dependencies and ownership are in the [handoff packet](EXECUTION-MODEL-DEPENDENCIES.md).

[bendrt]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/paper/BendRT.pdf
[comp]: https://github.com/bendlang/bend/blob/574b6d39a235b539eb19a5c532993a0abb3d11ad/bend2/comp.ts
[reynolds]: https://surface.syr.edu/lcsmith_other/13/
[functions]: https://www.w3.org/TR/WGSL/#restrictions-on-functions
[futhark]: https://pldi17.sigplan.org/details/pldi-2017-papers/27/Futhark-Purely-Functional-GPU-programming-with-Nested-Parallelism-and-In-place-Array
[webgpu]: https://www.w3.org/TR/2026/CRD-webgpu-20260915/#synchronization
[dispatch]: https://github.com/gpuweb/gpuweb/discussions/4434
[wgsl]: https://www.w3.org/TR/WGSL/#memory-model
[nets]: https://arxiv.org/abs/1010.1066v2
[abp]: https://www.cs.cmu.edu/~guyb/paralg/papers/AroraBlumofePlaxton01.pdf
