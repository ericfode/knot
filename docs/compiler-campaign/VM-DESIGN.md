# VM-first self-hosting design (D14)

The coordinator's design panel synthesized this on 2026-09-27, after the user chose the VM-first route ("yep this is how i want to do it! make it happen"). Four independent designs (minimal, bytecode, Bend-hosted and skeptic) were critiqued adversarially and then synthesized; the critique scores were minimal 5, bytecode 5.5, bend-hosted 4, skeptic 3. Estimates are in agent-days and are uncertain.

## Recommendation

VM-first, as the user already chose in D14 ("yep this is how i want to do it! make it happen", main ec43747). It is hybrid only in that the native profiles stay in the bundle S, and their outputs must stay byte-identical when the VM runs them.

**The decisive reasons.**

1. Knot's own source is polymorphic and higher-order:
   - about 300 `S.choose`/`S.bind` sites and 531 lambdas;
   - Base's rank-2 `IO(A) = @-R -> (A -> IO.OP<R>) -> IO.OP<R>`;
   - quantity-polymorphic `Kind(a)` lists;
   - non-tail Base recursion.

   Going direct therefore needs four pieces of native machinery: polymorphic defunctionalization (campaign/closures is monomorphic per arrow type), an IO trampoline in emitted code, a general RC heap, and an engine-stack fix. Each would first fail at compiler scale. One small VM supplies all four once, and uniform words make polymorphism free.
2. Every remaining language increment shrinks to check + eval + core.
3. The I2 = I3 fixpoint becomes a very large differential test of one small runtime against a Bend model.

**What it does not do.** It does not shorten the checker. Polymorphic and rank-2 closures, templates, Sigma and `Kind(a)` are the long pole on both routes, and nobody owns them today. The day saving is modest and the ranges overlap: about 20 agent-days (15–27) against about 27 (21–36). The real gain is lower variance.

**One correction to the premise.** A VM already exists. campaign/literals 2ea222e ships a Knot-emitted instruction-graph interpreter, `knot-literals-wasm-1`. It should be superseded, not grown, because it has:
- only the enum ABI, and no `knot_io`;
- no closures and no reclamation;
- a 32,768-instruction cap;
- unary Nat;
- raw-opcode source.

It stays in S as a frozen native profile. Its opcode DSL seeds a later increment that emits the VM from Bend.

## Design

## knot-vm-1 runs knot-image-1 images (synthesis)

### 1. The image (knot-image-1)

**Encoded, not lowered.** The image is the checked core Book, resolved and erased:
- **Term set.** literals' core (Literal, Intrinsic, Default, Value, Construct, Reference, Application, Let, Case/Branch), plus closures' Closure/Invoke, plus one Foreign node for hash-pinned IO leaves.
- **No new passes.** No ANF, CPS, bytecode, ownership or defunctionalization pass.
- **From design A:** one node per core form.
- **From design C:**
  - Erased parameters, fields, lets and captures are dropped at encode time.
  - Levels become frame-slot indices, and functions become table indices.
  - A name section serves `describe` and debugging.
- **Case** gets a dense tag table built at encode time.
- **Serialization:** binary little-endian u32 words.
  - Header: magic, version, entry kind (Program `main: IO(Unit)`, or Book for eval mode), and a representation table naming the hash-pinned Nat, U32 and Char ids.
  - Function table, constructor table, constant pool, then a post-order node stream with absolute child offsets.
  - The encoding is canonical and carries no paths or dates.
- **Where it lives.** `src/image.bend` has an exhaustive match over C.Term, so a missing encoding is a checker error. It has a round-trip law.
- **Selecting it.** `compile-cli --profile=knot-image-1` must be an explicit override. The literals contract auto-selects `knot-literals-wasm-1` for any book with a loader-installed primitive type, and S is such a book.

### 2. The VM (knot-vm-1)

**Source.** `vm/vm.wat`, a transcription of `vm/model.bend` in which each handler cites its model case.
- It is assembled by a pinned wabt `wat2wasm`, a build tool that BEND-SUBSET-STAGES permits.
- The sha256 of `vm/vm.wasm` is pinned in `src/CONTRACT.json`.
- It imports only `knot_io` and exports `memory`, `knot_alloc` and `knot_main`.
- Run it with `node scripts/run-wasm-io.mjs vm/vm.wasm SANDBOX -- IMAGE ARGS`. It loads the image with the new `read_bytes`.
- A Book-kind image runs `FN FUEL ORDINALS` and prints eval-cli's `describe` text, so every frozen eval expectation applies (from A).

**Values** are 32-bit tagged words (from B, halving memory against the 128 MiB cap).
- **Immediate** (low bit 1): nullary tags, Char codes (the `Chr` wrapper is erased), and U32/Nat below 2^31.
- **Pointer** (low bit 0): a cell `[rc][hdr][fields]`, whose class is Object, Closure, Big, Action or Activation.
- U32 and Nat of 2^31 or more are boxed Big cells.
- Nat `Zero`/`Succ` construct and case act on words.

**Heap.**
- Uniform RC for every cell. This sidesteps per-constructor Type/Data kinds, which are wrong for `Kind(a)` types.
- Dup on Reference, unpack and capture. Slots own their values. Activations are released at scope exit, and a tail call releases its caller.
- Drop runs through an iterative worklist.
- Allocation uses size-class free lists plus bump, growing to 2,048 pages.
- Image constants are immortal (an rc sentinel) from day one, not deferred. Critique C measured an RC VM without this at 13–14× slower.

**Machine.**
- A CEK machine with an explicit frame stack in linear memory. Nothing recurses on the Wasm stack: loader, validator, drop, UTF-8 and render are all iterative.
- Dispatch is a single `br_table` loop with **quantum re-entry** (from B): it returns every 2^16 calls and `knot_main` re-enters. This is the measured fix for V8 keeping one long call in Liftoff.
- **Fuel** counts calls and invokes, decoupled from eval.bend's transition count. This keeps superinstructions possible later.
- **Budgets:** `exhausted(1)` for fuel, `(2)` for heap, `(3)` for the frame region.
- **Validator** (iterative, at load time): offsets in range, binder level equal to scope depth, arity against the constructor table, known prim and foreign ids, frame sizes. A malformed image is a HostFailure, never memory corruption.

**Primitives.**
- The prim table is literals' closed 39-op registry, extended with every intrinsic the merged S closure reaches. modules' `base-pin.bend` SHA-256 calls `U32.xor` 11 times and `U32.or` 4 times, and neither is in the registry.
- A gate fails if a reachable intrinsic lacks a prim, or if a reachable non-prim body destructures `U32{Word}`.
- Semantics are the seed's: unsigned compare, x/0 = 0, x%0 = x, shifts of 32 or more give 0.

**IO.**
- Foreign leaves evaluate to Action cells. Invoking one with its continuation does four things: performs the `knot_io` call, converts values (canonical UTF-8 to and from Chr lists, byte lists packed with the `invalid |= e>>8` flag), builds the Base Result, and invokes k.
- The terminal continuation turns `Emit` into exit 0 and `Halt` into `die`.
- The host is **knot-io-2** = knot-io-1 plus three things:
  - `read_bytes`;
  - `path_identity`, which serves modules' foreign `inspect`;
  - exhausted kind 3.

**Coordinator decisions to record (D15–D18):**
- **D15 (Nat):** Nat is a 32-bit word, with Exhausted above 2^32-1. Nat literals are already capped there.
- **D16:** the fuel contract above.
- **D17:** knot-io-2.
- **D18:** literals' machine is superseded as the self-hosting VM.

### 3. Trust

1. **Bend model.** `vm/model.bend` is written in the I-profile and is the normative semantics. It runs under the seed and under Knot eval. Its laws are bounded, computed equations with checked proofs, not a refinement proof:
   - codec round trip;
   - validator soundness on bounded images;
   - an RC audit (rc equals incoming edges) at every step of the trace fixtures;
   - zero live cells after releasing the result;
   - each prim equals its Base body on edge inputs.
2. **Lockstep.** VM and model are compared on the complete machine state after every transition, through a test-only state-dump export.
3. **Four-lane differential** on every frozen suite: seed ⇔ src/eval.bend ⇔ model(image) ⇔ vm.wasm (from B and C).
   - A lane may report Exhausted only under a documented bound: eval.bend's unary Nat/String at 2^20 and its fuel cap, the Bun lane's ~32k stack, and the VM's declared Nat and memory bounds.
   - The VM lane must return the seed's value on every fixture where the seed succeeds within the declared budgets. Any other Exhausted is a failure.
4. **Mutants** in the WAT and the model, each killed by a named gate through a wrong observation, never a crash.
5. **Debug VM:** poison on free, trap on RC underflow, audit live cells at halt.
6. **End to end:** E2E-2 on 623 files, then E2E-3.
7. **Perch** semantic rules on model.bend and image.bend; style is reported per v8.

### 4. Route

- **C1** is the seed-native build of compile-cli.
- **I2** = `C1 --profile=knot-image-1 src/compile-cli.bend I2`.
- **A2** = vm.wasm running I2.
- **I3** = A2 with the same argv. The fixpoint is sha256(I2) = sha256(I3).
- **Conformance:** A2 and A3 image outputs are byte-identical to C1's, and VM runs of them agree with the seed. Their knot-enum-1, knot-fields-wasm-1 and knot-literals-wasm-1 modules are byte-identical to C1's (25 programs, 90 calls, 32 rejects today).
- **Ladder:**
  - Milestone 9 becomes: C1 compiles parse-cli to an image, and the VM runs it byte-identical to the seed-built parse-cli on every repo file (623).
  - Milestone 10 becomes: the whole compiler on the VM, then I2 = I3.
  - Milestones 5–8 lose their Wasm-lowering halves.

### 5. Grafts and what is superseded

- From the skeptic (D): the frontend is the pole, so no day claims rest on the VM.
- Output path:
  - On literals, compile-cli already uses a tail `A.length`. The open issue is that `B.finish` materializes the whole byte list before a single write. The image profile streams sections through chunked `write_bytes`.
  - The input cap must rise too: base.bend is 67,190 characters against a 65,536-character bundle cap.
- literals' machine (`machine-code`, `machine-lower`, `machine-vm`, `machine-runtime`) is frozen as a native profile. It stays in S, is checked by Knot, runs inside the VM for conformance, and seeds `vm-emit`.
- wasm-owned's heap laws inform vm-rc; its code goes to the speed track.
- Speed track after E2E-3:
  - `vm-emit`: the VM emitted from Bend, with its bytes brought into the fixpoint.
  - `vm-speed`: last-use moves, superinstructions, a compact image format.
  - The native fixpoint, qualified byte-for-byte against the VM.

## Definition of done, item 1 (as rewritten)

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

## Increments

| Id | Starts | Depends on | Est. days | Goal | Acceptance |
|---|---|---|---:|---|---|
| `merge-wave` | now | — | 2.5 | Review and merge the on-path branches onto main in dependency order: nest, modules, descent-2, closures (rebased onto Scope{...,aliases}, with its partial-self-same pin migrated to Invalid), literals (re-merged onto the final modules), generics, io-host. Record the dispositions of literals' machine lane and wasm-owned, and decisions D15-D18. | main contains all seven branches. Every registered gate passes in one serial run. Every frozen suite's assertions are unchanged (D7). The enum-baseline, fields-wasm and literals-wasm hashes are unchanged. state.json and the decision table are updated. |
| `vm-spec` | now | — | 1.5 | Write vm/SPEC.md. Freeze the golden images and the speed workloads before any implementation. Contents: - the knot-image-1 grammar (literals' core forms, Closure/Invoke, Foreign), binary layout, tables and validator rules; - the knot-vm-1 word and cell layout, uniform RC, frames, quantum, and fuel per call/invoke; - the prim derivation rule; - the knot-io-2 delta; - the Exhausted-lane rule. Work from the campaign/literals and campaign/closures heads. | The spec is committed with D15-D18 drafted for the coordinator. Frozen: - At least 30 hand-serialized golden images, with expected outputs from the seed and eval-cli. - The Exhausted-lane rule: only documented bounds excuse a lane, and the VM must return the seed's value wherever the seed succeeds within budgets. - Bench workloads with seed-native baselines: Peano; CPS closure churn shaped like lex.bend's S.choose; Char-list String building and String.eq scans; SHA-256 over 64 KB. - Seed-native instruction counts for parse-cli over S's files. |
| `io-abi-2` | now | — | 1 | Extend knot-io-1 to knot-io-2 in scripts/run-wasm-io.mjs and IO-ABI.md: - read_bytes: raw bytes, no decoding; - path_identity: the same semantics as modules' path-identity.c/.js; - exhausted kind 3. Branch from campaign/io-host f42ae39. | All 86 existing host runs are unchanged and pass. New fixtures for each import are frozen first; they cover symlinks, case aliases, binary bytes including invalid UTF-8, and kind 3. A mutant for each new import is killed. |
| `poly-fixtures` | now | — | 1 | Freeze seed expectations for the checker residue that neither route owns today: - lambdas and function values at generic and erased-type arrows (the S.choose, S.bind and List.map shapes); - higher-rank IO(A) arrows; - quantity-polymorphic Kind(a) parameters; - template binders (~A) as used by scope.bend; - Sigma pair destructuring outside Base. | A frozen suite with seed-derived expectations, classified as agree, Invalid or Unsupported, covering every shape that S's census lists under generics, higher-order, templates and dependent. No implementation. |
| `image` | later | vm-spec, merge-wave | 2 | Write src/image.bend, the encoder with an exhaustive match over C.Term, plus a decoder and image-LAWS/PROOF for the round trip. Add compile-cli --profile=knot-image-1 as an explicit override of the literals auto-selection. Output path: stream sections through chunked write_bytes instead of one B.finish list. Raise the input and output budgets for the image profile. | - The round-trip law checks, and the image of every frozen-suite book decodes to erase_tokens(book). - The bundle character cap admits base.bend (67,190 characters, against 65,536 today) and the output cap admits images of at least 8 MiB, with CONTRACT.json updated. - A synthetic image of at least 4 MB is written through the chunked path. - The default-profile module hashes are unchanged. |
| `vm-model` | later | vm-spec | 3 | Write vm/model.bend in the I-profile: decoder, validator, word encoding, word store (the flat-store pattern), RC cells, frames, step and fuel. Laws are bounded, computed equations with checked proofs: codec, validator soundness, RC audit, zero leak. | The model runs under the seed's native lane and agrees with eval-cli on every golden image and every frozen eval fixture. vm/PROOF.bend prints 'All terms check.' Model mutants are killed by the laws. Perch semantic review has nonzero coverage, and its findings are labelled. |
| `vm-core` | later | vm-spec | 3 | Write vm/vm.wat, developed from the spec in parallel with vm-model. It covers: - the loader, iterative validator and read_bytes image loading; - a br_table dispatch with quantum re-entry; - the frame region, fuel, and immortal image constants on a bump arena; - eval-mode describe; - a test-only state-dump export. Pin wabt and the vm.wasm hash. | All golden images run with the expected outputs. Re-assembling produces identical vm.wasm bytes. Nothing recurses on the Wasm stack: a 250K-deep non-tail recursion completes. |
| `vm-lockstep` | later | vm-model, vm-core | 1 | Integrate the VM with the model. Add the per-transition lockstep and the value differential against eval-cli, and take the first speed-ratio measurement. | - The VM equals the model on complete machine state after every transition, on all golden images. - The VM equals eval-cli on value for every frozen eval fixture, under the Exhausted-lane rule. - Bench ratio: VM CPU at most 4× seed-native on each frozen workload, measured on a quiet host. Above 10× stops for design review. |
| `vm-rc` | later | vm-lockstep | 2 | Add the RC heap to the model and the WAT: - size-class free lists and memory.grow up to 2,048 pages; - dup on Reference, unpack and capture; - activation and tail release, and an iterative drop worklist; - a poison-on-free debug build and a live-cell audit. | - The RC audit law holds on the trace fixtures, including data-lifetime candidate B's shapes through an adapter. - Zero live cells remain after releasing the result, on every fixture. - The lexer-shaped closure-churn workload runs 10^8 allocations with a flat peak heap under 128 MiB. - RC overhead is at most 2× bump on the bench workloads. - An RC under-count mutant and an over-count mutant are both killed. |
| `vm-prims` | later | vm-lockstep, merge-wave | 1.5 | Build the prim table: literals' 39-op registry plus every intrinsic the merged S closure reaches, including U32.or, U32.xor and U32.not. Add word Nat and Char, and Text constants as immortal SCon chains. | - The reachability gate passes: no reachable intrinsic lacks a prim, and no reachable non-prim body destructures U32{Word}. - The law 'prim equals its Base body' holds on edge inputs: U32 values 0, 1, 2^31 and 2^32-1; x/0=0; x%0=x; shift ≥32 → 0; unsigned compare. - The literals suite's 40 books and the bootstrap helpers agree on the VM lane. |
| `vm-closures` | later | vm-lockstep, merge-wave | 1 | Run Closure/Invoke directly: capture copies with dup, and code offsets. Generics are erased at encode time. Polymorphic fixtures are added as poly-closures lands. | The closures and generics suites agree on the VM lane under the four-lane rule. A mutant that captures the wrong slot is killed. |
| `poly-closures` | later | merge-wave, poly-fixtures | 3 | Checker and evaluator work, shared by both routes: - closures and function values at generic and erased-type arrows; - higher-rank IO(A); - quantity-polymorphic Kind(a) parameters. | The poly-fixtures agree with the seed through check and eval. Existing closures and generics pins are migrated only where the frozen suite records the change. Nothing is passed through unchecked (D4). |
| `templates` | later | merge-wave, poly-fixtures | 1.5 | Checker and evaluator work: template binders (~A) and Sigma destructuring, as used by scope.bend and the compiler. | The template and Sigma fixtures in poly-fixtures agree with the seed, and scope.bend's refine, replace and set_known check under Knot. |
| `baseslice-check` | later | merge-wave, poly-closures | 3 | Check or trust-inventory the reachable Base slice under D2: Word(32n), Sigma, higher-rank IO declarations and List.map. Produce the prim and foreign identity table that image.bend consumes. | The frozen baseslice suite passes. The trust inventory lists every unchecked reachable Base declaration. The identity table is hash-pinned and consumed by the vm-prims gate. |
| `sugar-check` | later | merge-wave | 2 | Elaborate the surface sugar that Knot's own source uses into existing core. | The frozen sugar suite passes through check and eval, and on the VM lane once vm-lockstep lands. |
| `io-check` | later | baseslice-check, io-abi-2 | 1.5 | The check side of IO: - IO(A) as the Base CPS type; - hash-pinned foreign identities: Base's six plus modules' inspect; - affine File. D12's 'Unsupported compile host-effect' is lifted for knot-image-1 only. | The io suite's check expectations pass. Native profiles still report Unsupported compile host-effect with exit 3. The foreign identity table is complete for S. |
| `vm-io` | later | vm-rc, vm-closures, io-abi-2 | 2 | Add Action cells for every foreign leaf, including path_identity, and the terminal continuation (Emit/Halt). Convert UTF-8 in both directions and pack byte lists with the invalid flag. Add a pure World semantics to the model. | - The io suite's 103 agree runs pass on images, including both 100k-bind stresses, first on hand-built images and then on C1-emitted ones. - A guest that builds and writes a 4 MB byte list completes within 128 MiB. - Mutants for non-BMP UTF-8 and for a dropped invalid flag are killed. |
| `vm-trust` | later | vm-io, vm-prims, image | 1 | Close the assurance battery and register the `vm` gate. | - At least 14 WAT mutants and the model mutants, each killed by a named gate through a wrong observation: arm selection, slot off-by-one, erased argument, wraparound, Nat bound, x%0, RC under-count, RC over-count, host-stack recursion, fuel, UTF-8, invalid flag, validator offset, quantum state loss. - Malformed-image HostFailure controls. - The vm.wasm re-assembly check. - A `vm` gate registered in scripts/gates/run.py. - Perch semantic review of model.bend and image.bend, with findings labelled. |
| `vm-e2e2` | later | vm-trust, baseslice-check, sugar-check, poly-closures, templates | 2 | Milestone 9 on the VM: C1 compiles parse-cli to an image, and the VM runs it over the whole corpus. Measure, extrapolate A2(S), and decide go or no-go. | - Output is byte-identical to the seed-built parse-cli on all 623 corpus files (exit, stdout, stderr). - Recorded: calls per byte, peak heap, wall time, and A2(S) extrapolated from C1 costs. - Go if A2(S) projects to 15 minutes or less and peak heap under 128 MiB. Above 60 minutes or 128 MiB, stop and escalate, in this order: dense tables and superinstructions, then the compact image, then a coordinator-decided cap raise. |
| `vm-e2e3` | later | vm-e2e2, io-check | 3 | Milestone 10: C1 → I2 → A2 → I3 with I2 = I3, plus the conformance run and the bootstrap harness stages. | - sha256(I2) = sha256(I3). - A2 and A3 image outputs equal C1's on the corpus, and VM runs of them agree with the seed. - Their native-profile modules are byte-identical to C1's (25 programs, 90 calls, 32 rejects). - Harness seams fixed: host.mjs no longer returns 'Unsupported io-abi-pending' (io-abi.mjs is added); check.py conformance passes --profile to run-wasm. - The e2e3.i2, e2e3.a2, e2e3.i3 and e2e3.fixpoint stages and their receipts are committed. - The DoD precision is adopted. |
| `vm-emit-1` | later | vm-e2e3 | 2.5 | Speed track, after E2E-3: grow literals' machine-code.bend opcode DSL into a typed Wasm instruction layer, rendered for review with wasm-tools print. | The layer re-emits machine-vm.bend byte-identically, and the literals-wasm hashes are unchanged. |
| `vm-emit-2` | later | vm-emit-1 | 3 | Speed track: re-express the VM in Bend on the typed layer, so that C1 and A2 emit vm.wasm and the fixpoint extends over the VM's own bytes. | The Knot-emitted vm.wasm passes every vm gate and mutant. The copies emitted by C1 and by A2 are byte-identical. wabt becomes a cross-check only. |
| `vm-speed` | later | vm-e2e3 | 3 | Speed track: encode-time last-use moves, superinstructions, and a compact knot-image-2, each checked differentially and benchmarked. | Each pass keeps the four-lane agreement and I2 = I3 under knot-image-2, and shows a noise-aware bench improvement. |

## In-flight dispositions

- nest (eb15da8, codex fix round 2): keep on path. The pattern-matrix check and eval produce image grammar. Its Wasm lowering is speed track.
- modules (0111f13, fix round 2): keep on path. Its foreign path-host `inspect` needs knot-io-2 `path_identity` (io-abi-2). literals must re-merge the final modules.
- literals (2ea222e): keep on path the lexer, parser, checker and evaluator, the Literal/Intrinsic/Default core forms, and the 39-op registry. The registry is the VM prim contract, extended with U32.or, U32.xor and U32.not. Its knot-literals-wasm-1 instruction machine (machine-code, machine-lower, machine-vm and machine-runtime.bend) is explicitly superseded as the self-hosting VM (D18) and frozen with no further growth. Those files stay in S: compile-cli imports machine-code and literal-wasm. So they must check under Knot and emit byte-identical modules inside the VM. Its 40-book freeze reruns on the VM lane. Its opcode DSL seeds vm-emit.
- generics (f39ba7e): keep the checker and erasure on path. The boxed-erasure Wasm lowering is finished speed-track work and is not extended. The closure_apply Unsupported pin is revisited by poly-closures.
- closures (a1d6891, in review): keep on path the check half, the Closure/Invoke core forms and the eval (Capture/ApplyArgument/ApplyBody). The VM interprets these directly. Typed defunctionalization and the return_call lowering are speed track. The monomorphic limit is lifted by poly-closures.
- descent-2 (75e1ac6, reviewed, 0 blocking): keep on path. Merge after closures rebases onto Scope{...,aliases}. Its native recursion lowering is speed track.
- io-host (f42ae39, fix round 2): keep on path. It becomes the VM's host, extended to knot-io-2 by io-abi-2. runtime.wat stays as the host gate's independent test runtime.
- wasm-owned (37baabe): pause as speed track and do not merge before the self-hosting queue clears. Its release worklist, heap laws and bounded-cleanup findings inform the vm-rc model; there is no code reuse.
- sugar, baseslice, io suites (frozen, fixtures only): keep on path, check side only. Their Wasm-lane pins are met by the VM lane, with an explicit disposition recorded for each.
- classify-3 (queued): keep on path as checker classification work.
- fields-wasm (merged) and knot-enum-1: keep as native profiles inside S. Their modules must stay byte-identical when emitted inside the VM (E2E-3 conformance).
- opt-1, opt-2, c-backend, gpu-2, gpu-emit, bench-2: stay parked under D13. gpu-2 runtime2 is prior art for model plus lockstep. bench-2 and bench/ gain a VM lane after vm-lockstep.
- census-2 and the bootstrap harness: keep. Add a VM evidence lane and the e2e2.vm and e2e3.* stages.

## Estimates

These are agent-days in the increment table ("raw"). A stated fix-round factor of 1.3 covers the one or two codex fix rounds each increment has needed so far.

**VM route**

Two chains run in parallel and are balanced at about 10–10.5 raw days:
- **Checker chain:** merge-wave 2.5 → poly-closures 3 → baseslice-check 3 = 8.5. io-check then adds 1.5, which is off the E2E-2 path. templates (1.5) and sugar (2) run in parallel.
- **VM chain:** vm-spec 1.5 → vm-model and vm-core in parallel, 3 → vm-lockstep 1 → vm-rc 2 → vm-io 2 → vm-trust 1 = 10.5. image, io-abi-2, vm-prims and vm-closures fit inside it.

The chains join at vm-e2e2 (2), followed by vm-e2e3 (3):
- raw: 10.5 + 2 + 3 = 15.5;
- with the factor: about **20 agent-days**, range **15–27**.

A slip in either chain moves the date. The checker chain is the likelier to slip, since it carries unowned residue.

**Direct-Wasm route**

The same checker chain (10 raw including io-check), plus native work that cannot fully overlap it:
- IO trampoline in emitted code: 2.5;
- serialized residue of per-feature lowering (polymorphic defunctionalization, Base-slice lowering): about 2;
- native E2E-2: 2.5;
- native E2E-3: 4. Stack, RC and IO faults first appear at compiler scale here.

That is about 21 raw. General-layout RC (2) and stack mitigation (1.5–3) run in parallel. With the factor: about **27**, range **21–36**.

**Net.** Roughly 5–7 days saved at the median, but the ranges overlap, so the saving is not established. The defensible gain is lower variance: three open-ended native risks become one bounded runtime tested per transition against a Bend model. Total work to E2E-3 is similar on both routes, because the VM adds about 17 raw days while about 12 days of native lowering move off the path.

**Speed evidence** (feasibility only, not a claim):
- The seed-native eval-cli runs about 15–20M transitions/s.
- B's scratch bytecode VM ran at about 1.65–2× seed-native on Peano.
- The owned-RC Bend-native VM (design C) ran 13–14× slower than a bump arena. This is why immortal image constants and a hand-tuned WAT come first.

**A2(S) wall time** is unmeasured. My projection is 1–15 minutes. The first ratio gate is at vm-lockstep; the real measurement comes at vm-e2e2, with a kill line at 60 minutes. Memory against 128 MiB is the larger unknown: lexer closure churn, the output byte list, and frames for non-tail Base recursion. It is gated at vm-rc, vm-io and vm-e2e2.

**Accuracy** is ±30% or worse. Merge-wave alone could reach 3–4 days, since nest and modules are both in fix round 2.

## Risks

- **The checker is the long pole on both routes.**
- 0 of 328 compiler declarations are check-evidenced.
- Polymorphic and higher-rank closures, templates, Sigma and Kind(a) had no owner; poly-fixtures, poly-closures and templates now own them.
- If these slip, both routes slip equally, because the VM removes only lowering work.
- **Speed at compiler scale is unmeasured.** The projected A2(S) is 1–15 minutes.
- Gates: bench ratios at vm-lockstep and vm-rc, then the real measurement at vm-e2e2 (target 15 minutes, kill line 60).
- Escalation order: dense tables and superinstructions, then a compact image, then encode-time moves. Only after those does the native track take the checker's hot path.
- **Memory is capped at 128 MiB** (2,048 pages). Three loads press on it:
- lexer closure churn, about 16 closures per character;
- the materialized output byte list: B.finish, even though literals already made the length tail-recursive;
- frames for non-tail Base recursion.
Mitigations: 32-bit words, RC plus immortal constants from vm-rc onward, and streaming output. The fallback is a cap raise, which is the coordinator's decision.
- **Nat has three semantics.** eval.bend uses unary Nat bounded at 2^20; the VM uses a 32-bit word; the seed caps at about 2^48. D15 and the Exhausted-lane rule must stop a VM that exhausts everywhere from passing the differential, and a wrong rule would either mask bugs or fail correct runs.
- **The prim table may be incomplete.** base-pin's SHA-256 reaches U32.xor, U32.or and U32.not, which are not in literals' registry. Any missed intrinsic would run a Base body that destructures Word bit lists on an immediate, giving a wrong value or a trap. The reachability gate in vm-prims must run on the final merged S.
- **Two VMs could cause churn.** literals' Knot-emitted machine and knot-vm-1 overlap.
- If D18 is not recorded, both may keep growing.
- Its frozen files stay in S and must run byte-identically inside the VM.
- **The trusted base grows** by an estimated 2,000–3,000 lines of hand-written WAT plus a pinned wabt, which is double design A's 1,400-line figure.
- A bug symmetric across A2 and A3 passes the fixpoint, so the four-lane differential, lockstep, mutants and debug VM are mandatory.
- vm-emit later brings the VM bytes into the fixpoint.
- **Mutable activation slots** depend on the checker's rule that a binder's level equals its scope depth. A core producer that breaks this rule makes the VM wrong where eval.bend is right. The validator rejects such images; the fallback is persistent environments, at a speed cost.
- **Merge-wave may overrun.**
- nest and modules are in fix round 2.
- closures must rebase onto nest and descent-2's Scope.
- literals merged a stale modules and must re-merge.
2.5 days is optimistic; 3–4 is plausible.
- **The knot-io-2 amendment carries a parity risk.** It is a coordinator decision (D17). path_identity must match modules' C and JS host bodies exactly, including Darwin case-insensitivity and symlink rules.
- **Several contracts must change, and each needs an owner and a CONTRACT.json update:**
- the bundle character cap (65,536, against base.bend's 67,190 characters);
- output caps of 65,536 (single file) and 1,048,576 (bundle);
- B.Builder's U32 bounds;
- the harness seams (io-abi.mjs missing; run-wasm called without --profile).
- **Quantum re-entry and tiering** were measured only on Node 22.22.3. Bun/JavaScriptCore and other Node versions are unmeasured.
- **The model laws are bounded computed equations with checked proofs**, not a general refinement proof. The data-lifetime traces need an adapter to reach the heap-cell level. Assurance claims must say so.
- **Four artifacts move together.** A core change from sugar, IO or later work must land in eval.bend, image.bend, model.bend and vm.wat at once. The exhaustive match in image.bend and the versioned knot-image-N formats keep drift visible, but this is a recurring coordination cost.
