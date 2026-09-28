# Compiler campaign: self-hosting, backends, optimization, speed

Started 2026-09-27 at the user's direction:

> Get this merged into main then run a campaign to get this thing moving again. I want a full end to end working compiler that passes perch!

Session goal: "Knot is fully self hosting and capable of optimization passes and a benchmark framework is set up so we can hill climb it's speed."

Later additions the same day:

- "update the goal to include the gpu and cpu backends"
- "an extension to bends syntax that allows for unicode symbols but do that last … after we are self hosting"
- "you can delegate to codex too"
- "add a metaprogramming library to the end of the milestones. I want to be able to dynamically generate and run code in bend from bend"
- "You can let claude do actual work too. i just want you to use up my codex tokens as well"
- "Please keep the focus on self hosting first"

## Definition of done

1. **Self-hosting.** Knot compiles its own complete source bundle, including the Base slice it reaches. The seed builds C1; C1 emits the Wasm compiler A2; A2 compiles the same frozen bundle to A3.
   - **Names.** C1 means "compiler, generation 1": the upstream seed builds Knot's own Bend source into a runnable compiler. It is not the C language, and not the `knot-c-1` backend. A2 and A3 are Wasm modules: the self-hosted compiler emits Wasm directly from its core IR, and no step of the chain goes through Knot's C backend.
   - **C1 lane.** C1 is built with the seed's native lane (the seed compiles through clang). The seed's Bun lane is only a cross-check. Its known fault (`List.length` overflows the stack at about 32,000 elements) makes it inconclusive on compiler-sized inputs, so it is recorded as Exhausted there, not as a disagreement.
   - A2 and A3 are byte-identical.
   - Both generations pass the conformance corpus against the pinned reference Bend (2.0.29, `574b6d3`).
   - The upstream fallback is used only by the seed step.
2. **CPU backends.** Wasm is primary: the compiler itself runs as Wasm, and programs run under Node and Bun. A native C backend follows self-hosting and is the speed reference against upstream Bend's native output.
3. **GPU backend.** Compiler-generated WebGPU/WGSL execution of Bend programs on the real device, using the adaptive continuation-task model. Results agree with the independent evaluator and the CPU backends.
4. **Optimization passes.** A core IR with semantics-preserving passes, each checked by differential conformance: inlining, case-of-known-constructor, constant folding, dead-code elimination, tail calls to loops, and more.
5. **Benchmark framework.** Compile time and emitted-code runtime per backend, with correctness guards and noise-aware comparison, for hill-climbing speed. Landed in `f324221` as `bench/`; it grows with each backend.
6. **Passes Perch.** Two parts:
   - Semantic: targeted rules on every changed Bend file, with nonzero coverage and no unresolved confirmed findings.
   - Style (rubric v8): each mechanism in the [compiler manifest](compiler-campaign/manifest.json) meets its declaration and composition targets. `npm run lint:style -- --live --manifest=docs/compiler-campaign/manifest.json` reports each group and overall qualification; a filtered `--group=NAME` run qualifies only that selection. The [offline baseline](compiler-campaign/perch-baseline.md) records structural blockers, not ratings or a pass. Whether leading declarations keep the level-3 Anticipation/Payoff bar is the user's threshold decision (see the v8 calibration record); until then it is reported, not waived.
7. **Unicode syntax extension (after self-hosting).** Unicode symbols in identifiers and operators, as a Knot dialect with a desugaring to plain Bend.
8. **Metaprogramming library (last milestone).** Bend programs generate and run Bend code from Bend. The library is built on the self-hosted compiler used as a library, not on the upstream seed.
   - **Code as data.** A typed syntax and core representation, with builders and quotation, that generated programs are written in.
   - **Checking before running.** The same checker validates generated code before it runs. It never runs unchecked code. Invalid and Unsupported results come back as values.
   - **Running.** Generated code runs in-process through the evaluator, and through emitted Wasm that the host instantiates.
   - **Conformance.** Generated code agrees with the same program written by hand and run through the pinned reference.

## Decision record (coordinator, 2026-09-27, under the user's explicit instructions above)

| Id | Decision | Why |
|---|---|---|
| D1 | Resume compiler implementation now. The goal's direct instruction supersedes the memetic-first sequencing in `SELF-HOSTING-GOAL.md` ("Immediate priority"). All six milestones remain. | User instruction; the style rubric is now calibrated (v8), which was the purpose of the memetic foundation. |
| D2 | Base policy: load the hash-pinned unmodified `base.bend`, lower only the reachable slice, and keep an explicit trust inventory of unchecked Base declarations. Checking all of Base (S3) remains a later milestone. | This is the shortest path to self-hosting. The whole-Base check is kept as a milestone, not dropped. |
| D3 | Wasm profile for fielded programs: linear memory, a bump arena first (owned-storage reclamation later, per `RUNTIME-SUPPORT-PLAN.md`), `return_call` for tail calls, and defunctionalized closures. | `return_call` validates on the pinned Node. Defunctionalization also suits WGSL, which has no function pointers. |
| D4 | The compile path covers the full implementation language. The checker grows alongside, never silently accepting what it cannot check. A form it cannot check is reported `Unsupported`, never `Invalid`, and never passed through unchecked. | Keeps Knot's identity as a checked compiler while it grows. |
| D5 | GPU backend: records plus a device interpreter first (the task machine); specialized WGSL emission later, as an optimization. | Correct first, then fast; the benchmark framework measures the difference. |
| D6 | A native C backend follows Wasm self-hosting. | It shares the core IR; Wasm comes first because the compiler must run as Wasm. |
| D7 | Every new capability gets fixed expectations from the pinned reference (seed) or literal review before implementation, and existing assertions stay unchanged. Differential conformance (seed ⇔ Knot evaluator ⇔ Knot Wasm) is the core gate. | Preserves the law-quality discipline. |
| D8 | The user's instruction authorizes this campaign to edit `src/` through delegated worktrees. Compiler Planning's accepted work and all receipts are preserved; package directories are not edited unless an increment explicitly requires it; arrays (`vec`) stay out of the bootstrap profile. | Ownership continuity. |
| D9 | New Bend code follows the user's calibrated register: one core idea, laws stated as `law` declarations with checked proofs (not unchecked law comments), and terse, exact names. It avoids costume vocabulary, narration and ornament. | `docs/perch-calibration/taste-duel-2026-09-27/`, rubric v8. |
| D10 | Data lifetime for milestone 1: unique `Type` objects plus reference-counted immutable `Data` (candidate B of `research/data-lifetime/`). Copied Data (A) stays as the conformance control. Reclamation is part of owned-storage acceptance; the bump arena stays interim. | The r3r7 packet: both candidates pass 105 traces with 16 of 16 mutants killed, and B peaks at 43 words against 1,532 on the shared-subterm trace. The packet asked for a coordinator or user decision; the coordinator decided under the goal. The user can reverse it. |
| D11 | D6 revised. The native C backend starts now, in parallel on the current core IR, and grows with each accepted profile. It no longer waits for self-hosting. | The user asked for maximal parallel use of Codex and of Claude implementers. The C emitter shares only core terms, so its conflicts are small. |
| D12 | Host effects before the IO ABI lands. A reachable IO or host-effect declaration checks successfully. Evaluation of a pure entry agrees with the seed. Compilation reports `Unsupported compile host-effect` (exit 3) and emits no artifact. | This follows `docs/BEND-SUBSET-STAGES.md` (build rejects a missing capability before emission) over the baseslice suite's check-phase pin. The coordinator reconciles that pin when baseslice is implemented. |
| D13 | Self-hosting has priority over every other track, at the user's direction. New increments, reviews and merge work go first to the self-hosting path: literals, generics, closures, the descent rule, modules, the Base slice, surface sugar, the IO host and its lowering, owned Wasm storage, the frontend as Wasm (E2E-2) and the fixpoint (E2E-3). The C backend, GPU emission and optimizer branches wait for review and merge until the self-hosting queue is clear. Their finished work is preserved on their branches. | User, 2026-09-27: "Please keep the focus on self hosting first". |

## Milestone ladder

Increments are bounded at 1 to 3 agent-days each. Each has deterministic gates first, then Perch.

| # | Increment | Track |
|---|---|---|
| 0 | Classification repair: forms the seed accepts become `Unsupported`, never `Invalid`. | language |
| 1 | Structural recursion with a descent check (checker and evaluator). | runtime |
| 2 | Heap and fielded constructors in Wasm (new profile `knot-fields-wasm-1`), with Exhausted classification at the host. | runtime |
| 3 | Pattern matrix: multi-scrutinee, wildcard and variable patterns, nested patterns, first-match semantics. | runtime |
| 4 | Modules and Base loading: `./` and hash imports from a frozen local bundle; the pinned `base.bend`. | language |
| 5 | Primitives and literals: U32, Char, Nat and String; Base intrinsics. | language |
| 6 | Generics and quantity arguments: erasure and a uniform boxed representation. | language |
| 7 | Closures and higher-order code: defunctionalization, `return_call`. | language/runtime |
| 8 | Base slice lowering for the frontend closure. | language |
| 9 | Frontend as Wasm: Knot-compiled lexer and parser byte-identical to the seed-built `parse-cli` on every repo file. | milestone |
| 10 | Whole compiler as Wasm (checker, evaluator, emitter, IO host ABI), then the C1 → A2 → A3 fixpoint. | milestone |
| 11 | Core IR and optimization passes, each conformance-checked and benchmarked. | optimization |
| 12 | GPU: device runtime probes (R4 to R7) in parallel from now, then records emission, host bundle and generated device runs. | gpu |
| 13 | Native C backend. | cpu |
| 14 | Unicode syntax dialect. | language |
| 15 | Metaprogramming library: code as data (typed syntax and core terms with builders and quotation), then `check`, `eval` and `compile` as library functions, then `run` of generated code in-process and as host-instantiated Wasm. Each result is differentially checked against the same program written by hand. | language/runtime |

Parallel tracks throughout:

- **Perch enablement:** a compiler manifest, group-mode style review, and the truncation and hash-import blockers.
- **Implementation-profile inventory:** a census tool so feature creep in Knot's own source is visible.
- **Benchmarks:** grow with each backend.

## Protocol

- **One branch per increment.** Each increment gets branch `campaign/<id>` in worktree `.claude/worktrees/campaign-<id>`, created from `main`. `.toolchain` is linked to the main checkout's pinned copy.
- **Executors.** Codex (`gpt-6-astra`, max reasoning), run with `codex exec -s workspace-write -C <worktree>`, or Claude agents. Executors commit only on their branch and never push or merge.
- **Merge path.** The coordinator reviews each branch: diff scope, all 11 existing gates, the new gates, and targeted Perch when a key is available. It then merges to `main` and pushes.
- **Conflicts.** Receipts that differ only in date or path are regenerated on `main` after merging.
- **State.** Kept in [compiler-campaign/state.json](compiler-campaign/state.json).
- **Other chats' branches.** For example `claude/interesting-lamport-c393ad` (the rubric v7 line). These are not merged by this campaign. They reconcile against `main`.
