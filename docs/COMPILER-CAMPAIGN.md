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
- "would it it make sense to make a virtualized bend first?" … "yep this is how i want to do it! make it happen"
- "Codex is out of tokens, so start using Claude instead. I mean, yourself with workflows."

## Definition of done

1. **Self-hosting (VM-first route, D14).** Knot compiles its complete source bundle S to a `knot-image-1` image. S is `src/compile-cli.bend` and its imports, including the frozen native-profile emitters, the reachable slice of the hash-pinned Base, and the bytes package.
   - **The image is encoded, not lowered:** the checked core, erased and resolved.
     - There is one node per core form.
     - Levels become frame slots and functions become table indices.
     - Intrinsics and foreign leaves become hash-pinned identities.
     - It is serialized as little-endian 32-bit words.
   - **One small virtual machine, `knot-vm-1`, runs images.**
     - `vm/vm.wat` is assembled by the pinned wabt `wat2wasm`, a build tool outside the trusted runtime, into `vm/vm.wasm`. Its sha256 is pinned in `src/CONTRACT.json`.
     - Its semantics are fixed by the Bend model `vm/model.bend` and its laws.
   - **The host is `knot-io-2`:** `knot-io-1` plus `read_bytes`, `path_identity` (the modules loader's foreign `inspect`) and a stack-exhaustion kind.
   - Every step uses the same frozen bundle.
   - **The chain:**
     - The seed builds C1. `C1 --profile=knot-image-1 src/compile-cli.bend` emits image I2.
     - `vm.wasm` runs I2 as A2. A2 emits image I3 of the same bundle.
   - **Fixpoint.** I2 and I3 are byte-identical (equal sha256). A4 is built only to investigate instability, never to mask it.
   - **Conformance.** Both generations pass the conformance corpus against the pinned reference Bend (2.0.29, `574b6d3`).
     - Their image outputs are byte-identical to C1's, and running those images on the VM agrees with the reference.
     - Their native-profile outputs (`knot-enum-1`, `knot-fields-wasm-1`, `knot-literals-wasm-1`) are byte-identical to C1's.
   - **Trusted runtime.** The upstream fallback is used only by the seed step. The VM and the `knot_io` host are the whole trusted runtime. Each has an independent model and differential tests:
     - VM ⇔ model after every transition on small images;
     - VM ⇔ `src/eval.bend` ⇔ seed on the values of every frozen suite, where Exhausted excuses a lane only under a documented bound;
     - mutants killed by named gates.
   - **Names.** C1 means "compiler, generation 1": the upstream seed builds Knot's own Bend source into a runnable compiler. It is not the C language, and not the `knot-c-1` backend.
   - **C1 lane.** C1 is built with the seed's native lane (the seed compiles through clang). The seed's Bun lane is only a cross-check. Its known fault (`List.length` overflows the stack at about 32,000 elements) makes it inconclusive on compiler-sized inputs, so it is recorded as Exhausted there, not as a disagreement.
   - **Native Wasm codegen.** Direct emission of Wasm from core is now the speed track. It covers `knot-enum-1`, `knot-fields-wasm-1`, `knot-literals-wasm-1`, closures' defunctionalization and owned storage. It is no longer the self-hosting route.
   - **Later speed-track milestones:**
     - `vm.wasm` emitted from Knot's Bend source, with its bytes brought into the fixpoint;
     - a native fixpoint A2ⁿ = A3ⁿ, qualified byte for byte against the VM-hosted compiler.
   - **Names.** C1 means "compiler, generation 1": the upstream seed builds Knot's own Bend source into a runnable compiler. It is not the C language, and not the `knot-c-1` backend. C1 is built with the seed's native lane; the seed's Bun lane is only a cross-check, which is inconclusive (Exhausted) on compiler-sized inputs.
   - Design and increments: [VM-DESIGN.md](compiler-campaign/VM-DESIGN.md).
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
| D14 | The self-hosting route is VM-first ("virtualized Bend"). Knot compiles to a serialized image that one small Wasm VM executes; the fixpoint is image I2 = image I3. Every language feature then needs only frontend, checker and core support, and the VM, written once, supplies the heap, closures, primitives, stack discipline and IO. Native Wasm codegen continues as the speed track under D13's priority. The VM gets a Bend model with laws, differential tests against `src/eval.bend` and the seed, and mutants. | User, 2026-09-27: "would it it make sense to make a virtualized bend first?" then "yep this is how i want to do it! make it happen". |
| D15 | Nat is a 32-bit word in the VM; a Nat above 2^32-1 is Exhausted. Nat literals are already capped there. | VM design synthesis. eval.bend's unary Nat (bounded at 2^20) and the seed (about 2^48) differ, so the Exhausted-lane rule in VM-DESIGN.md governs differential comparisons. |
| D16 | VM fuel counts calls and invokes, independent of eval.bend's transition count. Exhausted kinds are 1 (fuel), 2 (heap and representation: NatRange, RCOverflow, the image limits of `vm/SPEC.md` §4 (size, records per table, arity and slots), and display), and 3 (frame region). | Keeps superinstructions and later optimization possible without changing observable budgets. Kind 2 was widened in vm-spec review round 8: an image past a resource limit is exhausted, not malformed. |
| D17 | The host ABI becomes `knot-io-2`: `knot-io-1` plus `read_bytes`, `path_identity` (the modules loader's foreign `inspect`) and a stack-exhaustion kind. | The VM loads images as raw bytes. The loader needs symlink and case identity, per the modules review. |
| D18 | The literals increment's Knot-emitted instruction machine (`knot-literals-wasm-1`) is superseded as the self-hosting VM. It stays in the bundle as a frozen native profile, and its opcode DSL seeds the later `vm-emit` speed track. | Enum-only ABI, no `knot_io`, no closures, no reclamation, a 32,768-instruction cap and unary Nat. |
| D19 | The VM's linear-memory maximum is 65,536 pages (4 GiB, the wasm32 limit), declared in the image and VM contract. Exhausting the declared budget is `Exhausted` kind 2 (heap), reproducibly on every host. This replaces the 2,048-page (128 MiB) bound that the io-host increment chose and the VM design adopted. The `knot_io` host's module-memory check is raised to match. | That bound was a conservative guess, not a platform limit: Node 22.22.3 accepts a 65,536-page maximum and grows a memory to 2 GiB on this host. A declared budget keeps heap exhaustion deterministic without starving self-compilation. User question, 2026-09-27: "why is this the case 'Memory is capped at 128 MiB (2,048 pages)'". |
| D20 | Non-scalar Chars (lone surrogates and codes above U+10FFFF) on output. The program's value decides non-scalar output, not any seed lane's behaviour. A golden is `divergent-by-contract (non-scalar output)` exactly when a String the program passes to an output effect holds a Char outside the Unicode scalar range. This is determined from the program's own semantics: the reference evaluation of its plan, or eval-cli or vm-model on the same program. The VM then follows the `knot-io` contract: it refuses that String as `HostFailure io abi` before the host call, after the earlier output, and never encodes it. Constructing a non-scalar Char is legal in the VM; only outputting one is refused. The seed lanes are observations only, and both are recorded. The Bun lane may refuse early, when the Char is constructed. The native lane prints generalized UTF-8, truncating the lead byte of a code from 2^21. Neither lane classifies. A D20 case never counts as seed agreement; a program that builds a non-scalar Char but outputs only scalars is ordinary seed agreement. | The vm-spec review found the reference lane and the IO contract in conflict. The IO contract is the one the host enforces, and a VM that encoded what the host refuses could not be conformance-tested. Review round 4 found both lanes unfit to classify: the Bun lane refuses at construction, and the native bytes are lossy from 2^21. The coordinator then made the program's value the classifier. |
| D21 | A law that an increment's prompt requires but that cannot yet be proved in general stays required and is never weakened. The increment may merge with it recorded as an open proof obligation, with its evidence (ground-instance laws, fixtures, fuzz), in `src/SPEC.md`'s trust/limits section and the increment's LAW_REVIEW. First application: nest's irrefutable-first-row and exhaustive-lowering laws. | Keeps the law-quality discipline honest without blocking self-hosting on a general proof. The obligation stays visible in the trust inventory until it is discharged. |
| D22 | A Book (value) entry never performs an effect. Under a Book invocation, applying a Foreign Action is refused as `Unsupported vm effect` before the host call; the Program (IO) entry is the only one that performs effects. | vm-model review round 2: an admitted Book image applying `IO.print` to a continuation printed in the model, `evaluate.book` dropped the output, and the seed's native lane fail-stops. Refusing is D4-safe (never Invalid, never an unrequested effect) and gives all three lanes one reading. vm-spec owns the SPEC change and its control. |
| D23 | IO requests are values, as in the seed's `io_step`. Applying an Action to a continuation builds an inert request; only the request the Program entry returns to its Top loop is performed, and then its continuation is entered. A request that is dropped has no effect. A request that is inspected (a Case over it), rendered by a Book, or otherwise consumed as data is refused as `Unsupported vm effect`. D22 follows from this: a Book entry never reaches the loop, so it never performs an effect. This supersedes vm-spec's eager rule (perform at application). | vm-spec review round 10: `keep(m1(..), m2(k))` prints `kept` in both seed lanes, but `dropped` then `kept` under the eager rule in the reference evaluator, vm-core and vm-model. VM-DESIGN §11 requires the seed's effect trace wherever the seed succeeds; recording a divergence by contract would weaken that rule. |
| D24 | A request matches no constructor row: a Case over a request takes its Default when it has one and otherwise stops `Unsupported vm effect`, as the seed's native lane does. A binder or a lone catch-all binds the request as a value. This refines D23's "a request that is inspected is refused", which remains the rule for a Case without a Default. | vm-spec review round 12 measured six shapes. The native lane takes the catch-all wherever one exists, and fail-stops only when every row names a constructor; the Bun lane agrees on two of the three rows. vm-spec recommended refusal (option a) because the checker refused catch-alls on algebraic types. The pattern-matrix increment (nest) now accepts them, so compiled programs will reach these shapes, and VM-DESIGN §11 requires the native lane's result wherever it succeeds. |

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
- **Executors.** Claude workflows since 2026-09-27, when the Codex quota ran out. Each increment runs an implementer loop in its worktree, then the scope/gates/semantics review with adversarial verification, then fix-and-re-review rounds. Earlier increments used Codex (`gpt-6-astra`) through `codex exec -s workspace-write`. Executors commit only on their branch and never push or merge.
- **Merge path.** The coordinator reviews each branch: diff scope, all 11 existing gates, the new gates, and targeted Perch when a key is available. It then merges to `main` and pushes.
- **Conflicts.** Receipts that differ only in date or path are regenerated on `main` after merging.
- **State.** Kept in [compiler-campaign/state.json](compiler-campaign/state.json).
- **Other chats' branches.** For example `claude/interesting-lamport-c393ad` (the rubric v7 line). These are not merged by this campaign. They reconcile against `main`.
