# Design review: how the VM route reaches its speed targets

**Date:** 2026-09-29.

**What this is.** The synthesis of the vmperf design-review workflow, which vm-lockstep's "above 10× stops for design review" rule triggered. Five roles did the work, and each ran in its own scratch copy:

| Role | Question it answered |
|---|---|
| **profile** | where the cycles go |
| **projection** | what A2(S) costs |
| **interp** | making the interpreter faster in place |
| **aot** | translating images ahead of time |
| **repr** | changing the representation |

**How it was done.** Nothing in the repository, on a branch or in a campaign worktree was edited. Nothing was committed and no provider was called.

**How to read the numbers.** Every number comes from the named role's own run, with its load. A ratio is only ever formed between two lanes of the same run, never across roles.
- Host: Apple M5 Max (18 logical CPUs), macOS 26.5.2, node 22.22.3 (V8 12.4) unless a row says otherwise.
- The host was shared throughout: one-minute load average 20 to 107.
- **Instructions retired are the primary metric.** They reproduce to 0.1–1%. Cycles carry ±5–15%, and string-scan's cycles are the noisiest.

---

## 1. Answer

**Can the VM route meet A2(S) ≤ 15 minutes?** Yes on time, even with no speed work. No on memory until vm-rc lands.

| Question | Finding |
|---|---|
| Time | The projection models A2(S) of S_B (Knot's compile-cli closure plus the image encoder, 556 M entries) at **68 s of CPU** on the pinned VM, using the measured per-idiom mix (523 cycles per entry). |
| | The four S scenarios span **47–128 s**. |
| | With reference counting at vm-rc's ceiling (2× bump): **94–256 s**. |
| | Worst modeled corner (S_D, cycles +30%, RC 2×): **5.5 min**. It rises to **10.5 min** if the entry count also sits at its 1.9× upper bound. |
| | The 60-minute kill line is never approached. |
| Memory | A bump-only VM needs **15–39 GiB** (S_B: 21 GiB, 5.3× D19's 4 GiB cap). It stops with `Exhausted` heap about 23% of the way in, during module loading. |
| | Reclamation (vm-rc) is the one change A2(S) requires. It is already ordered before vm-e2e2. |
| Bench gate | "≤ 4× seed-native on every frozen workload" is met by no measured design on deep-recursion, peano or list-fold (§3.3). |
| | No interpreter variant comes close: the best is 23× on peano. |
| | Ahead-of-time compiled wasm that keeps D16's debit measures **23×** (deep-recursion), **7.9×** (peano) and **11.9×** (list-fold) in exact mode. |
| | On deep-recursion, 4× is out of reach for every design that debits fuel per entry. |
| | Only string-scan measures the VM rather than clang's loop collapse. The gate needs restating; that is a user decision (§8, D27). |
| Where the 240 cycles go (V8 12.4) | ≈40%: 25 helper calls per entry, which V8 12.4 does not inline. |
| | ≈15%: bulk-memory C calls on 0–32 bytes. |
| | ≈11%: growing and first touching an arena that never reuses a cell. |
| | 30–40%: the machine's own transitions (the Eval/Return/Enter protocol). |
| | The first two are engine artifacts. JavaScriptCore runs the same pinned module at 208 cycles per deep level, against V8's 489. |

**Recommendation.**
- **Keep the interpreter and its per-transition lockstep.**
- **Before vm-e2e2, do only work that leaves every machine state unchanged or that is already required:**
  - freeze the compiler-shaped workloads and restate the gate;
  - add a generated inlining pass (**vm-codegen**): 2× on V8, with bit-identical state after every transition;
  - land **vm-rc** on the existing Activation cells, with the heap and frame measurements that vm-e2e2 then gates on.
- **Everything else is speed track after vm-e2e3:** fused spans, the frame layout, load-time lowering and ahead-of-time translation. Each changes the transition granularity, the state layout or the trusted base. They are ordered by gain per unit of verification risk, and pulled forward only by a measured miss at vm-e2e2.

---

## 2. The trigger, and this review as its disposition

**The rule.** vm-lockstep's acceptance (VM-DESIGN, Increments): "Bench ratio: VM CPU at most 4× seed-native on each frozen workload, measured on a quiet host. Above 10× stops for design review."

**What was measured.** The first ratio is in `tests/compiler-vm-lockstep/REPORT.md` at load 22–28. It is about 240 cycles per entry:

| Workload | VM ÷ seed-native |
|---|---:|
| deep-recursion-b | 315× |
| list-fold-b | 170× |
| peano-b | 87× |
| string-scan | 11.9× |

**Why it is not a clean measurement.** REPORT records the blockers:
- no reclamation, so bump-sized variants had to be used;
- no encoder, so the plans were lowered by hand;
- sha256-64k cannot run (it needs vm-prims);
- cps-choose was not lowered;
- the host was never quiet.

**Disposition (proposed for the coordinator's record).**
- vm-lockstep's bench criterion failed as measured.
- For three workloads the failure is structural (§3.3), not a defect of the increment.
- This review is the design review that the criterion calls for.
- vm-lockstep's bench acceptance closes when the user decides D27 (§8). REPORT's measurement stays as evidence.
- Nothing here blocks the lockstep, value-differential or mutant results of vm-lockstep.

---

## 3. Measurements

### 3.1 Where the cycles go (profile)

**Setup.**
- Pinned module: `vm/vm.wasm` 9c483def… (campaign/vm-lockstep 019e615f).
- Method: two-size differencing, medians of 5–9 alternating runs, load 26–107 (mostly 40–90).
- Exact dynamic operation counts come from a gas-metered build whose outputs and final registers equal the pinned build's.

| Workload | Entries per unit | Instructions per entry | Cycles per entry | IPC |
|---|---:|---:|---:|---:|
| deep-recursion | 2.0 | 1,292 | ≈248 | 5.2 |
| peano | 3.0 | 1,551 | ≈300 | |
| list-fold | 4.0 | 1,548 | 321 | |
| string-scan | 6.0 | 1,437 | 490 | 2.9 |

**Where the time goes, by mechanism.** Deep-recursion shape, per entry. The rows overlap, so they do not add up.

| Mechanism | Count per entry | Instructions | Cycles |
|---|---|---|---|
| Wasm call boundaries | 25.5 helper calls | ≈410 (32%) | ≈100 (34–40%) |
| `memory.fill`/`memory.copy` as C calls | 3.5 fills and 1.0 copy, each 0–32 bytes | ≈215 (16%) | 35–44 (13–17%) |
| `memory.grow` and first touch of fresh pages (no reuse) | | | ≈27 (≈11%) |
| The machine's own transitions: 8 dispatch iterations, 2.5 frame pushes and pops, one Activation | | ≈650 | 75–95 (30–40%) |

**Why V8 12.4 costs this.**
- V8 12.4 inlines no wasm-to-wasm call by default.
- The wasm calling convention has no callee-saved registers, so every call spills and reloads.
- `memory.fill` and `memory.copy` are C calls costing 55–70 instructions even for 0 bytes.
- Mutable globals are memory loads and stores.
- The machine is retire-bound (68.8% useful slots). Fewer instructions is therefore the lever; branch and cache behaviour are not.

**Ablations on deep-recursion.** Per level, instructions / cycles, `--no-liftoff`, median of 9. The ladder runs to the full codegen row, then three further levers.

| Variant | Instructions / cycles |
|---|---|
| Release | 2,583 / 496 |
| All 16 hot helpers inlined | 1,765 / 326 (−32% / −34%) |
| Plus stores instead of fill/copy (**the codegen tier**) | 1,308 / 238 (−49% / −52%) |
| Leaf-operand fusion (G) | −4% / −5% alone; −11% / −12% on top of codegen |
| The profiler's wrapper path (W): a function whose body is one Intrinsic runs at Enter **without an Activation or Call frame** | −26% / −28% alone on deep; −38% / −62% on string-scan |
| Codegen + G + W | 868 / 150 (−66% / −70%) |

The profiler's W is **heap-visible**: it does not allocate the Activation, so it is not the state-identical W of §4.1.

**Other levers.**

| Lever | Effect |
|---|---|
| Pre-grow and pre-touch memory | −11% cycles |
| Growth in 256 MiB steps | −4% cycles (−8 to −13% after codegen) |
| Machine registers in wasm locals | −6% instructions after codegen. The ablation loses state on abnormal halts. |
| V8's own `--experimental-wasm-inlining` | −30% / −33% |

**Throughput.** About 17 M entries/s on deep-recursion and 9 M/s on string-scan today.

### 3.2 What A2(S) costs (projection)

**No direct measurement is possible yet: C1 cannot compile S today.**
- Seed-built check-cli, compile-cli and parse-cli on main reject every file of S (`Unsupported lex literal`).
- compile-cli on campaign/literals-integ stops at `Unsupported parse parameter-type` (syntax.bend's `List<&2,U32>`).

**So A2(S) is a model built from measured stage kernels.**
- Interpreter-predicted entry counts equal the pinned VM's exact call meter on 34 prim-free goldens and on four hand-lowered compiler loops.
- Stage entries times native cost per entry predict a measured native module-bundle compile within 8–21%.
- Load was 40–95. Seconds are cycles at 4.3 GHz: CPU time on an idle P-core, not wall time on this host.

**S_B, by stage.** VM cycles per entry come from the per-idiom kernels measured on the pinned VM.

| Stage | Entries (M) | Share | Cycles per entry | Seconds | Bump heap (GB) |
|---|---:|---:|---:|---:|---:|
| Q.qualify: identifier resolution, 4 strict scans of the globals list per reference, quadratic | 321.8 | 57.8% | 600 | 44.9 | 11.6 |
| Base slice dependency scan | 67.2 | 12.1% | 430 | 6.7 | 3.1 |
| Loader glue (modelled as +10%) | 50.6 | 9.1% | 430 | 5.1 | 2.3 |
| check | 40.6 | 7.3% | 430 | 4.1 | 1.9 |
| encode + write | 35.6 | 6.4% | 430 | 3.6 | 1.6 |
| lex | 26.6 | 4.8% | 340 | 2.1 | 1.6 |
| Base SHA-256 verify + inventory | 8.6 | 1.5% | 340 | 0.7 | 0.3 |
| parse | 5.3 | 1.0% | 430 | 0.5 | 0.3 |
| **Total** | **556.3** | | **523** | **67.6** | **22.7 GB = 21.1 GiB** |

About 35% of these entries are calls to one-Intrinsic Base wrappers.

**Across scenarios.** S_C and S_D stand for the S that vm-e2e3 will actually compile once poly-closures, templates, sugar and io-check exist.

| Scenario | Entries | CPU at measured mix | At uniform 240 cycles per entry | With RC at 2× bump | Bump-only heap |
|---|---:|---:|---:|---:|---:|
| S_integ (today's closure) | 390 M | 47.0 s | 21.7 s | 94 s | 14.9 GiB |
| S_B (+ encoder) | 556 M | 67.6 s | 31.0 s | 135 s | 21.1 GiB |
| S_C (S_B × 1.25) | 777 M | 95.0 s | 43.3 s | 190 s | 29.4 GiB |
| S_D (S_B × 1.5, checker 2× heavier) | 1,042 M | 127.8 s | 58.1 s | 256 s | 39.3 GiB |

**Uncertainty.**
- Entries: 0.7–1.9× of central.
- Cycles per entry: ±25%.
- check and encode come from toy fits.
- **Break-even** for 15 minutes at 523 cycles per entry is 7.4 G entries: 13× S_B, 7× S_D.

**Memory in detail.**
- Bump-only costs 36–60 bytes per entry.
- The 4 GiB cap is reached at about 127 M entries, in the load phase (module check.bend, about 17 of 39). The load phase alone needs about 14 GiB.
- With RC the live set is estimated at 0.1–0.5 GiB. This is **not measured**.

**The pipeline ratio differs from the bench ratio.** Compiler code costs the seed 13–68 cycles per counted entry, not the 1.5 of a collapsed loop. So VM ÷ native on the whole pipeline is about 10× (model). The 87–315× bench ratios are not what A2(S) sees.

### 3.3 Why no measured design meets 4× on three frozen workloads

**The seed's per-entry cost.** The seed's native lane (clang) collapses these loops. Per unit: 1.53 cycles (deep-recursion), 10.2 (peano), 7.1 (list-fold). Per VM entry that is 0.77, 3.4 and 1.8 cycles.

**What 4× allows per entry.** 3.1 cycles (deep-recursion), 13.6 (peano), 7.1 (list-fold).

**The floor for anything that debits fuel per entry.** D16 requires a fuel debit and a frame-room check at every entry.
- The AOT role's floor is about 3.5 cycles per entry: native recursion at shallow depth, with fuel in a register.
- At deep-recursion's depth of 250,000 the floor is far higher. With **both the debit and the frame accounting switched off**, native wasm recursion measured 28.4 cycles per level, 14 per entry, because past about 32 native frames every return mispredicts.

**What results.**
- **Deep-recursion: out of reach for every design that keeps per-entry fuel.** The 3.1-cycle budget is below the shallow floor and far below the 14-cycle floor at this depth.
  - Measured AOT, exact mode: 17.8 cycles per entry, 23× the seed.
  - Best interpreter variants: 72× (repr V2cg) to 124× (interp fused).
- **Peano and list-fold: not ruled out, but not met by any measured design.**
  - Their budgets (13.6 and 7.1) sit above the floor.
  - The AOT's `fast` variant measures about 21 and 15 cycles per entry (6.3× and 8.6× the seed), and 7.9× and 11.9× in exact mode. Fuel batching and user-function inlining are untried.
  - No interpreter variant comes close: the best is repr V2cg, 77 cycles per entry on peano (23×).
- **Only string-scan** (seed 225 cycles per character, no collapse) measures the VM:

| Design | string-scan ÷ seed |
|---|---:|
| Pinned VM | 12–13× |
| Codegen tier | 9× |
| Interp fused spans | 8× |
| repr V2cg | 2.1× |
| AOT (non-reclaiming against a reclaiming native binary; no parity claim) | 0.5× |

---

## 4. Prototypes

### 4.1 In-place interpreter (interp)

**What was built.** `vm/vm.wat` of 019e615f, changed in two tiers. The image format and every observable stay as they were.

1. **Codegen tier** (the profiler's levers 1 and 3):
   - A build-time inliner (`vm/inline.py`, 146 lines) inlines 19 hot helpers into `$run`.
   - `memory.fill` and `memory.copy` of 0–32 bytes in `$frame`, `$alloc`, `$enter` and `$complete` become stores.
   - After every SPEC transition, all 26 registers, the control region, the frame region and the heap are **identical to the pinned test build**. Evidence:
     - interp's test build stepping unfused: 137 runs, 1,856 transitions;
     - the profiler's equivalent build: 93 goldens (1,810 transitions) and 17,972 transitions on bench-shaped images.
   - The vm-core gate passes with identical counts.
2. **Fused spans**, macro-transitions of weight 1 + xw that no observer can split:
   - **G:** leaf operands fused into the gather arms.
   - **W:** a one-Intrinsic wrapper call runs Enter, the prim and the Return in one step. The wrapper's Activation **is still allocated**, so the heap is bit-identical.
   - W applies only to immediate operands and prims 0–21, 23 and 25–31. That excludes Nat.add, Nat.mul, show and the String prims.
   - A span runs only when a precondition proves that no sub-step can stop, yield or touch the host. Otherwise the reference arm runs.

**Results.** Whole process, 7 interleaved repeats, load 43–92, start-up subtracted. Each cell is instructions / cycles per entry, then the speedup over pinned.

| Workload | Pinned | Codegen only | Fused (final) |
|---|---|---|---|
| deep-recursion-b | 1,287 / 244 | 653 / 119 (1.97× / 2.05×) | 523 / 93 (2.46× / 2.64×) |
| peano-b | 1,548 / 302 | 816 / 157 (1.90× / 1.92×) | 667 / 122 (2.32× / 2.47×) |
| list-fold-b | 1,548 / 317 | 839 / 169 (1.84× / 1.88×) | 654 / 122 (2.37× / 2.60×) |
| string-scan | 1,418 / 487 | 766 / 343 (1.85× / 1.42×) | 566 / 293 (2.50× / 1.66×) |
| cps-count-b (the role's own closure workload, not frozen) | 1,250 / 250 | 661 / 126 (1.89× / 1.99×) | 533 / 98 (2.35× / 2.55×) |

- **With V8's inliner:** under node's `--experimental-wasm-inlining`, fused against pinned drops to 1.73× / 1.70× on deep-recursion (load 48–57).
- **The fused spans' own share:** on top of codegen they are worth about −20% instructions (deep-recursion 653 → 523).

**Verification.**
- **Codegen:** bit-identical state.
- **Fused:**
  - An aligned comparer advances the reference by 1 + xw transitions and compares the whole state at each boundary: 1,051 steps standing for 1,856 transitions.
  - The same comparison runs against the Bend model with the lockstep's own comparer: 315 runs, 0 divergences.
  - Other checks: 20 coverage images, and fuel/frame/heap boundary sweeps (7,936 runs).
  - Refused-growth page-cap sweeps.
  - The frozen bench images whole, up to 2.0 GB of heap.
  - 25 of 28 twin mutants of the spans' own guards killed.
- **The warning.** The first fused build had a trap-inside-a-span bug. It passed the whole vm-core gate, the lockstep gate, the aligned goldens and 10.8 M fixture steps, and was caught only by the page-cap sweep.
- **Two guards still lack evidence:**
  - one guard (`w-memory-unchecked`) has no covering image;
  - the lockstep needed one mutant anchor re-pinned, caused by a micro-change (family A) outside the codegen tier.

**Effort.**
- The prototype took 4 h 09 min of wall clock.
- A full version is estimated at 6–8 agent-days (range 5–9), including RC-awareness, gate integration and further spans.

**Ceiling.**
- About 420 instructions and 80 cycles per entry for a state-identical in-place design.
- 65–80 cycles with vm-rc's cell reuse.

**Caveats.**
- **Built on an old tree.** Built on 019e615f. vm-core has since changed `vm/vm.wat` by +233 / −85 lines (D22–D25, atomic stops, round 7), so the spans need re-derivation. The codegen post-pass does not care what the source says.
- **Module size.** The module grows from 19.5 KB to 77 KB (fused build).
- **Start-up.** Start-up rises from 304 M to 324 M instructions (codegen only) and 382 M (fused).
- **W's reach on S is unmeasured.** The projection's 35% counts every wrapper call. Qualify, 58% of the entries, is bound by String.eq, which W does not cover.

### 4.2 Ahead-of-time translation (aot)

**What was built.** A 1,130-line Python translator (`aotc.py`) turns a checked image into one wasm module. Only the machine loop of `vm/vm.wat` is replaced; the loader, validator, describe, IO.print, inspections and prims stay the VM's code.

**How the machine maps to wasm.**

| VM concept | Compiled form |
|---|---|
| Slot | wasm local |
| Call | wasm call |
| Non-self tail call | `return_call` |
| Self tail call | loop |
| Fuel | one global debited at every entry |
| Frame-region usage | tracked as an exact static offset, so `Exhausted` kind 3 fires at the same entry |

**Exact mode (`vheap`).** Every entry also charges the Activation the VM would have allocated to a virtual bump pointer. `Exhausted` heap therefore fires at the same allocation as on the VM.

**Results.** Five lanes in one alternating loop, 7 rounds, load 25–33, per unit.

| Workload | VM cycles | vheap cycles | VM ÷ vheap (cycles; instructions) | Cycles per entry, VM → vheap | ÷ seed (vheap) |
|---|---:|---:|---|---|---:|
| deep-recursion-b (level) | 478.9 | 35.7 | 13.4×; 34.6× | 239.5 → 17.8 | 23× |
| peano-b (product cell) | 886.0 | 80.5 | 11.0×; 20.9× | 294.9 → 26.8 | 7.9× |
| list-fold-b (list cell) | 1,243.2 | 84.4 | 14.7×; 17.6× | 310.8 → 21.1 | 11.9× |
| string-scan (character) | 2,775.6 | 113.3 | 24.5×; 19.0× | 462.1 → 18.9 | 0.5× |

**Compiler-shaped workloads** (load 34–42, cycles per entry, VM → vheap):

| Workload | VM → vheap | Speedup |
|---|---|---:|
| Lexer-shaped closure churn | 344 → 31.0 | 11.1× (seed native: 12.9) |
| Qualify contains-loop | 565 → 148 | 3.8× |
| Find scan | 404 → 49.6 | 8.1× |

**Extrapolated A2(S) for S_B** (nothing ran S):

| Variant | Time | Heap without RC |
|---|---|---|
| base | 12.9 s (4.3–18.8) | 3.3 GiB central (0.07–9.2) |
| fast | 6.7 s | 3.3 GiB central (0.07–9.2) |

**Verification.** Observational only: per-transition lockstep is impossible for compiled code.
- Differential against the VM: 7,863 of 7,864 compared jobs the same.
- Heap-limit sweeps: 2,922 of 2,922.
- Entry traces: 2.16 M entries.
- Frozen oracles: seed 137/137, model call counts 143/143.
- Mutants: 30, of which 29 killed and 1 argued equivalent.

**Named divergences.**
- A wide recursion dies on the engine's native stack; no launcher setting fixes it.
- No quantum yield.
- Arity above about 900 is refused.
- **`vheap` is exact only against a VM that never reclaims.** With vm-rc, where the heap is exhausted depends on free lists and release order. The SPEC would have to restate `Exhausted` heap as a bound on live data.
- **A fuel bug here is a hang, not a wrong answer.**
- **The one-walk String.eq predates the pinned read order.** The role's one-walk String.eq (variant `fast`) was verified against 019e615f, before vm-spec 09e2bc77 pinned the order of reads (§6.1).

**Effort.**
- Production with RC: 10–14 engineer-weeks (range 8–20).
- A hardened accelerator without RC: 4–5 weeks.

**Ceiling.**
- About 10 cycles per entry on call-bound recursion.
- 30–40 on compiler-shaped code including RC.
- Never below about 3.5 under per-entry fuel.

### 4.3 Representation (repr)

**What was built.** Two separable layers:
- **V1, frame layout.** Each activation is a record `[slot[cap], owner, link, head]` on the frame stack.
  - The 32-byte Activation heap cell, the Call frame and every Scope frame disappear.
  - Operands are gathered in place into the callee's record.
  - The tail test becomes O(1).
  - Patch: +128 / −68 lines.
- **V2, a dense derived section on top of V1:**
  - one-word operand descriptors and static all-leaf flags;
  - callee capacity, body and owner resolved in advance;
  - dense Case rows;
  - leaf fusion inside the parent's step;
  - +297 / −13 lines and a 191-line translator.

**Controls.**
- V2 without fusion (V2nf) is **33% worse** than V1: a dense format alone buys nothing.
- Fusion by peeking at image-1 children (V1g) is worse than V1 without codegen, and only −4 to −7% with it.
- The gain is the static per-node data.

**Results.** Long-baseline differencing, paired ratios ±2%, load 37–89, per unit, instructions / cycles.

| Workload | V0 pinned | V1 | V2 | V0cg (same inliner) | V2cg |
|---|---|---|---|---|---|
| deep (level) | 2,575 / 489 | 1,916 / 359 | 1,772 / 344 | 1,305 / 236 | **779 / 110** (55 per entry) |
| peano (product cell) | 4,648 / 914 | 3,603 / 711 | 3,367 / 681 | 2,448 / 452 | **1,559 / 235** (77 per entry) |
| string (character) | 8,500 / 2,831 | 6,687 / 1,439 | 6,113 / 1,361 | 4,507 / 1,856 | **2,827 / 465** (77 per entry) |
| qual (contains step, 3 entries) | 5,696 / 1,581 | 4,723 / 969 | 4,478 / 947 | 2,782 / 722 | **2,288 / 352** (117 per entry) |
| cps (character, ≈20 entries) | 30,624 / 7,065 | 25,229 / 5,691 | 24,431 / 5,655 | 18,172 / 4,260 | **12,888 / 2,645** |

**Gains.**

| Comparison | Instructions | Cycles |
|---|---|---|
| V1 against V0 | −21 to −26% (qual −17%, cps −18%) | −27% deep, −22% peano, −49% string-scan |
| V1cg against V0cg | −17 to −21% on the bench; qual −6%, cps −15% | −20 to −60% (the larger figures are the no-reclamation arena's memory behaviour) |
| V2cg against V0cg | −36 to −40% on the bench; qual −18%, cps −29% | −48 to −75%; qual −51%, cps −38% |

**Heap and memory.**
- Activation heap per entry falls to 0: deep 64 → 0 bytes per level; qual 32 → 0 per entry; cps 58 → 18.
- Peak RSS of the frozen deep run falls from 1.9 GiB to 56 MiB.

**On another engine.**
- On JavaScriptCore (Bun 1.3.14, load 61–106), the **pinned** VM already costs 208 cycles per deep level against 489 on V8 (2.4×).
- V0cg gains only −17% instructions there.
- V2cg reaches 47, 69 and 68 cycles per entry.

**Verification.** Entry-boundary equality with the pinned VM under an abstraction:
- 141 goldens, 87 controls and 4,000 random plans, plus compiler-shaped and long runs;
- mutants: V1 10 of 10; V2 21 of 22, the 22nd equivalent;
- closed-form frame accountants.

**Not identical, by design.**
- Heap and frame addresses.
- The resource boundaries:
  - 26 vm-core soft failures for V1 and 27–29 for V2, all resource-boundary rows or gate mutants the variant no longer reaches;
  - the kind-3 boundary moves in both directions. One random plan (`fz6-383`) exhausts the 16 MiB frame region where the pinned VM does not.
- SPEC and the model were **not** edited or run.

**Effort.** ±40%:
- V1: about 5.5 agent-days (SPEC 5–7 and model 2.0, WAT 1.0, fixtures 1.5, RC drop lists 1.0).
- V2 as load-time lowering: about 7.

**Ceiling.**
- Measured: V2cg 51–55 cycles per entry on deep.
- Extrapolated: 30–40 with wrappers, registers in locals and a Nat fast path.

---

## 5. Comparison

Each speedup is against that role's own same-run baseline. Rows are ordered by verification risk.

| Approach | Measured gain | Credible ceiling (cycles per entry) | Effort | Risk to model, lockstep, D16, D4, D7 | Fit with campaign order |
|---|---|---|---|---|---|
| **Codegen tier** (inlining pass + stores for 0–32 B fill/copy) | V8: 1.84–1.97× instructions, 1.88–2.05× cycles (bench); 1.69–2.05× instructions (qual, cps). JSC: about −17%. | ≈120 on deep (V8) | ≈1–1.5 agent-days (estimate) | **None.** State is bit-identical after every transition; no SPEC, model or expectation changes. The trusted build gains a flattener and an inliner. | A post-pass, so any vm.wat edit flows through it. Fits after the VM-track integration round, before vm-rc. |
| Growth policy (larger steps) | −4% cycles (−8 to −13% after codegen) | – | Trivial | Refused-growth rows move unless a refused large step falls back to the pinned 16 MiB rounding | Inside vm-rc, where the allocator changes anyway |
| One-walk String.eq | AOT: −33% on string-scan | – | Small | **SPEC 6.3 now pins the read order** (a whole, then b; vm-spec 09e2bc77). Needs a fallback to that order on any anomaly, or it is a SPEC change. | Speed track (vm-fuse), or earlier if qualify dominates the measured A2(S) |
| Fused spans G + W (interp; Activation kept) | −20% instructions on top of codegen (deep); total 2.3–2.5× instructions, 1.7–2.6× cycles | ≈80 (≈420 instructions); 65–80 with rc reuse | 6–8 agent-days | **Moderate.** A SPEC 6 macro-step sentence; an aligned comparer in two gates; page-cap rows; twin mutants. Existing gates step unfused, so they never exercise a span. A span bug passed every existing gate. | After vm-rc: spans must learn RC; pointer operands take the slow path |
| V1 frame layout | −21 to −26% instructions (under codegen: −17 to −21% on the bench, but only −6% on qual and −15% on cps); cycles −20 to −60% under codegen, much of it the no-reclamation arena's memory behaviour; activation heap → 0 | with V2: 51–55 | ≈5.5 agent-days | **High.** SPEC 5–7, model frames, audit laws, 26 re-frozen resource rows (D7), a kind-3 boundary move, an RC release-order decision | repr: before vm-rc. This review: decide with vm-e2e2's frame and heap data (§6.3). |
| V2 load-time lowering | V2cg against V0cg: −36 to −40% instructions on the bench, −18% (qual) and −29% (cps); qual 525 → 117 cycles per entry | 30–40 (extrapolated) | ≈7 agent-days | Fused model plus a refinement law; a ≈300-line lowering pass in the trusted runtime; no second byte format | Speed track after V1 |
| AOT translation | 11–15× cycles against the pinned VM (bench, exact mode); 3.8–11× compiler-shaped | ≈10 call-bound; 30–40 compiler-shaped with RC | 8–20 engineer-weeks | **Highest.** No per-transition lockstep; exact heap exhaustion lost under RC; engine-stack divergence; fuel bug = hang; changes D14's trust base unless kept as an accelerator | Native track after vm-e2e3; the VM stays the reference |
| Engine (JSC / Bun) | Pinned VM on JSC: 2.4× fewer cycles on deep, 2.3× on peano, 1.5× on string-scan, against V8 12.4 | – | Host validation only | D19's memory evidence and every gate are on node; quantum re-entry and 4 GiB growth are unmeasured on Bun | A decision (§8) |
| Registers in wasm locals | interp: +5% instructions (12 registers), −1.8% (2); profiler: −6% | – | – | Must write back on every stop path | Not recommended now |

---

## 6. The questions, answered

### 6.1 Can the VM route meet the targets?

**Time: yes, with margin, before any speed work.** A2(S) CPU time by scenario:

| Machine | S_B central | Across scenarios | With RC ≤ 2× bump | Worst corner (S_D, cycles +30%, RC 2×; and × 1.9 entries) |
|---|---:|---:|---:|---:|
| Pinned VM | 68 s | 47–128 s | 94–256 s | 5.5 min; 10.5 min |
| + codegen (estimate: repr's same-run factors applied to the model — qual 2.19×, lex-shaped 1.66×, others 1.9×) | 33 s | 23–62 s | 46–123 s | 2.7 min; 5.1 min |
| + codegen and fused spans (interp estimate: 2.4× on the pinned mix) | ≈30 s | | | |
| V1 + V2 + codegen, i.e. V2cg (repr estimate, ±40%) | ≈15 s | | | |
| AOT (aot extrapolation) | 7–13 s | | | |

Qualify dominates every scenario: 58–60% of entries, quadratic in the number of globals.

**The 15-minute target and the 60-minute kill line both hold** on every row, including the pinned VM, under the model's stated uncertainty.

**Memory: no, until vm-rc.**
- Bump-only needs 15–39 GiB.
- A layout change alone gets close to the cap but not safely under it: repr V1 about 3 GiB, AOT about 3.3 GiB, both ±40% or wider, both without RC.
- With RC, the live set is estimated at 0.1–0.5 GiB. That is the number vm-rc must measure first.

**Frames: unknown.**
- The 16 MiB frame region's use on S has not been measured by anyone.
- The pinned VM uses 48 bytes per level for the simplest non-tail recursion (about 350,000 levels), and more for wide functions.
- A non-tail Base recursion over a whole file's Char list (base.bend has 67,190 characters) or over an output byte list is the plausible kind-3 risk.

### 6.2 Which changes, in which order, and which must precede vm-e2e2?

**Must precede vm-e2e2:**
1. **The gate decision** (D27) and **frozen compiler-shaped workloads** (D7), before any speed change is timed.
   - Without D27, vm-lockstep cannot merge cleanly.
   - Every later increment would inherit a gate that no measured design meets on three workloads, and that no design keeping per-entry fuel can meet on deep-recursion.
2. **vm-rc**, already ordered: memory is the actual blocker.
   - Its acceptance must include the live heap of the compiler-shaped workloads and the growth policy.
3. **Measurement rows for vm-e2e2:** peak frame-region use, peak live heap, and instructions and cycles per entry. vm-e2e2 gates on all of them.

**Recommended before vm-e2e2, conditional on node staying the engine of record:**

4. **vm-codegen.** It is not needed for 15 minutes. Its case before vm-rc:
   - vm-rc turns the empty `$dup` and `$drop` stubs into real work at every Reference, capture and exit. On V8 12.4 each is a call boundary of about 16 instructions, so vm-rc's "RC ≤ 2× bump" acceptance would partly measure V8's call tax rather than RC.
   - It halves the CPU of the large runs vm-e2e2 and vm-e2e3 exist to do: the 623-file corpus, A2(S), A3 and conformance.
   - It changes no state, no expectation and no gate count.

**Must not precede vm-e2e2** unless vm-e2e2 measures a miss:
- fused spans, V1, V2 and AOT;
- a shipped compact image format, which V2nf shows buys nothing by itself.

Each of these reopens SPEC, the model and the lockstep, or the trust base, in the VM track that has just closed D22–D25, and none is needed for the targets.

### 6.3 The fork on V1 (frame layout), stated fairly

repr recommends V1 **before** vm-rc.

**For doing it early:**
- RC is written once, against records in frames.
- Under RC every entry would otherwise pay an Activation allocation, a slot-release walk and a free-list push. V1 removes that traffic, so its gain may be larger after vm-rc than the bump-only measurement shows.

**Against doing it early** (this review):
- vm-rc's LIFO reuse of Activation cells already removes V1's decisive argument, the 21 GiB → 3 GiB memory cut.
- V1 reopens SPEC 5–7, the model's frames and audit laws, 26 frozen resource rows and the lockstep fixtures, right after the VM track's most-reviewed artifacts converged (vm-spec is at review round 14).
- V1 moves the kind-3 boundary. A deep recursion through a function with `cap` slots uses (cap + 3) + (cap2 + 3) frame words per level, against the pinned 12. That trades heap for exactly the frame region whose use on S is unmeasured.
- V1 needs an RC decision it cannot make alone: static drop lists (an encoder and image change), or release at record pop (a new release order the model must follow).

**The cost of deferring.** When V1 lands, vm-rc's release order and the lockstep's address fixtures are rewritten. That is about 1–2 extra agent-days, plus a review cycle.

**Recommendation.** Defer V1 and decide it with vm-e2e2's measured frame and heap profile of S. It is a user decision, not a blocker (§8).

---

## 7. Recommended path and increment plan

**Before vm-e2e2.** The path is interpreter-first. Every change is either bit-identical after each transition or already required, and each has frozen expectations before it is timed.

### P0: vm-perf freeze and disposition

**Effort and slot.** 0.5–1 agent-day, now. It rides with the VM-track integration round, which already re-measures the bench on campaign/vm-lockstep.

**Freeze, before any timed run of a changed VM (D7):**
- **Workloads:**
  - the four bump-sized bench variants;
  - cps-choose, the lexer-shaped closure churn over a generic `choose`, which the projection lowered by hand;
  - two further compiler-shaped workloads: the qualify contains-loop and the find scan with closures;
  - sha256-64k joins when vm-prims lands.
- **For each:** source, independent guard, seed-native baseline and image sha.
- **Encoding:** produce images with campaign/image's encoder wherever Knot's checker accepts the source. Use hand-lowered plans only where it does not, and label them so.
- **Baselines:** instructions retired per entry (primary), cycles per entry and peak RSS, with the one-minute load. Measure on the **post-integration** vm.wasm (D22–D25 applied), not on 019e615f, with node 22.22.3 and a recorded JSC cross-check.

**Record** this review as vm-lockstep's bench disposition, and D27 once decided.

**Acceptance:**
- workloads.json pins every source, image and baseline;
- the runner reports per-entry figures and never gates on a seed ratio;
- a changed workload fails the pin check until re-pinned in a reviewed commit.

### P1: vm-codegen (if node stays the engine of record)

**Effort and slot.** 1–1.5 agent-days. It comes after the integration round and before vm-rc, on its own branch.

**Build.** `wat2wasm` → a pinned flattener → `vm/inline.py` → `wat2wasm`.
- The flattener is wabt's `wasm2wat`, keeping the toolchain wabt-only, or a pinned wasm-tools.
- The inliner inlines the hot helpers into `$run`.
- In the source, `memory.fill` and `memory.copy` of 0–32 bytes in `$frame`, `$alloc`, `$enter` and `$complete` become stores.
- **Nothing else:** no growth-step change and none of interp's micro-changes, which forced a lockstep anchor re-pin.

**Which binary the gates run.**
- Gates apply their mutants to `vm/vm.wat`.
- The pipeline builds both the release and the test module.

**Acceptance:**
1. **Identity row.** After every transition, the pipeline's test build equals the plain `wat2wasm` test build in every register, the control region, the frame region and the heap. The corpus: all goldens, Book invocations and run controls (including D25's atomic and 09e2bc77's order controls), the vm-core fixtures (250,000-deep recursion, quantum) and small sizes of the frozen workloads.
2. **Gates unchanged.** vm-core, vm-spec and vm-lockstep pass with unchanged counts and no edited mutant anchor.
3. **Reproducible and pinned.**
   - Re-assembly reproduces vm.wasm byte for byte.
   - Flattener and inliner versions and sha256 are pinned in `src/CONTRACT.json` beside wabt.
4. **Inliner mutants.** At least five are killed by the identity row, e.g.:
   - a lost global write-back;
   - swapped arguments;
   - a skipped zero store;
   - a wrong local;
   - a dropped result.
5. **Measured gain.** On V8, instructions per entry fall by a median of at least 1.6× across the frozen workloads that have a prototype figure (prototypes: 1.69–2.05×), with none below 1.3×.
   - Workloads without a prototype figure (the find scan) are recorded, not gated.
   - The JSC figure is recorded, not gated.

### P2: vm-rc

**Effort and slot.** As VM-DESIGN has it (2 agent-days), on the SPEC's existing Activation cells (class 4, recycled LIFO). There is no layout change.

**Additions to its acceptance:**
- measured on the vm-codegen build;
- RC ≤ 2× bump in **instructions per entry** on every frozen workload;
- flat peak heap under 10^8 allocations on the compiler-shaped set;
- **live heap per entry** reported for the three compiler-shaped workloads, since this is A2(S)'s heap input;
- the growth step revisited: larger or geometric steps are allowed only with a fallback to the pinned 16 MiB rounding when the host refuses, so every refused-growth row is unchanged;
- RC under-count and over-count mutants killed, as already planned.

### P3: vm-prims, vm-closures, vm-io, vm-trust

**Unchanged.** vm-trust registers P1's identity row and inliner mutants in the `vm` gate.

### P4: vm-e2e2 (2 agent-days)

**Record:**
- parse-cli's per-stage entries and calls per byte;
- instructions and cycles per entry on a quiet host (or instructions as the primary figure), naming the engine;
- peak live heap, peak bump and **peak frame-region use**.

**Extrapolate** A2(S) from C1-native stage counts.

**What vm-e2e2 does not measure.** parse-cli is lex and parse: about 6% of A2(S)'s modeled entries. Qualify (58%), the Base slice, check and encode, with their heap and frame use, stay modeled until vm-e2e3. The go decision here therefore rests on the model plus vm-rc's measured compiler-shaped kernels (qualify loop, closure churn, find scan). The margins below allow for that.

**Go only if all hold** (projected bars, with margins for model error):
- A2(S) ≤ 15 minutes of CPU;
- projected peak heap < 3 GiB (a 25% margin to D19's 4 GiB);
- frame-region use < 8 MiB (half the region) on the largest file.

**Otherwise escalate** (replacing VM-DESIGN's order):

| Miss | Escalation, in order |
|---|---|
| Time | S1 vm-fuse, then S3 vm-lower |
| Heap | A compact cell header (Objects from 32 to 16 bytes), then S2 vm-frames |
| Frames | A region-size decision (64 MiB costs nothing: the heap follows it) **before** vm-frames, which uses more frame words on wide functions |

### P5: vm-e2e3 (3 agent-days)

**Scope.** As VM-DESIGN has it, with one added acceptance row.

**Its A2(S) run is the first measurement of the dominant stages** (qualify, the Base slice, check and encode), so it checks D27's hard bars:
- at most 15 minutes of CPU, with the kill line at 60;
- peak heap under 4 GiB (D19);
- peak frame-region use within the region.

It records per-stage entries and the time, heap and frame peaks. A miss escalates as in P4. The fixpoint I2 = I3 is judged separately, unchanged.

### Speed track after vm-e2e3

VM-DESIGN's `vm-speed` is split, and the shipped compact image is dropped.

| Increment | Effort | What it does | Acceptance | Expected gain |
|---|---|---|---|---|
| **S1 vm-fuse** | 3–4 agent-days | interp's fused spans, made RC-aware: W for immediate-operand wrappers with the Activation kept, and G for leaf operands. A one-walk String.eq whose fast path covers well-typed strings and whose slow path reads in SPEC 6.3's pinned order (a whole, then b). SPEC 6 gains a macro-step sentence; test builds step unfused by default and report xw. | An aligned macro-step comparer in check-core and in the lockstep, against the unfused build and against the model; page-cap rows; coverage images, including a directed image that closes `w-memory-unchecked`; twin mutants of every guard and commit killed or argued equivalent; the order and atomic controls pass | ≥ 15% fewer instructions per entry than P1 (prototype: −20% on deep) |
| **S2 vm-frames** (V1) | ≈ 5.5 agent-days | Decided with vm-e2e2's data. SPEC 5–7, the model's frames and audit laws, the frame-region size, and the RC drop points re-expressed. The moved resource rows are re-frozen by SPEC amendment before implementation (D7). | Lockstep VM = model on complete state per transition; entry-boundary equality with the pre-change VM under the abstraction; closed-form frame accountants; V1 mutants killed | Under codegen, bump-only prototype: −17 to −21% instructions on the bench, −6% (qual), −15% (cps). Under RC the gain may be larger, since the Activation's allocation, release walk and free-list push also go. |
| **S3 vm-lower** (V2) | ≈ 7 agent-days | A VM-private dense cache computed after `$validate` and `$canonical`, with no `knot-image-2` file. Closure, Invoke and Foreign descriptor forms. It replaces S1's G. | Fused model plus a refinement law: entry-boundary equality with the unfused model on every golden, control and random plan; lowering mutants killed; at least 10% fewer instructions per entry than S2 on the compiler-shaped workloads | Prototype V2cg against V1cg, measured before any fused span: −21 to −24% on the bench, −12% (qual), −17% (cps) |
| **vm-moves** | | Encode-time last-use moves, after RC exists | Measured on the frozen workloads | RC dups per unit: peano 5.05 → 2.02, list-fold 3.00 → 1.00, string-scan 1.01 → 0 |
| **S4 native track** (AOT, `vm-emit`) | 8–20 weeks | Only if the hill-climb wants less than about 30–50 cycles per entry. The translator lives outside the trusted runtime and the VM stays the reference (D14). A compiled image is admitted only against the VM, by differential, heap sweeps and entry traces, each job under a watchdog. | The SPEC must first restate `Exhausted` heap as a bound on live data under RC | 10–40 cycles per entry |

---

## 8. SPEC and decision changes

**Nothing before vm-e2e2 changes SPEC:**
- P1 is bit-identical.
- P2 changes only what vm-rc already owns. SPEC 5 already says the timing of `memory.grow` need not agree between machines, and CORE.md's growth choice is revisited there.

**Decisions proposed (the user or coordinator decides):**

**D27: restate the speed gate.**
- vm-lockstep's and vm-rc's speed acceptance judge the VM per entry, not against seed loops that clang collapses.
  - Why: no measured design meets 4× on deep-recursion, peano or list-fold. No interpreter variant comes close. On deep-recursion no design that keeps D16's per-entry fuel can (§3.3).
- Frozen workloads (D7) include compiler-shaped ones, encoded by the image encoder where Knot's checker accepts them.
- The gate records instructions retired per entry (primary) and cycles per entry (secondary), with load, on the engine of record, as medians of at least 5 alternating runs. A rise of more than 5% in instructions per entry on any frozen workload needs a recorded reason.
- The binding speed gate is A2(S), in two stages.
  - **Projected at vm-e2e2, with margins for model error:** at most 15 minutes of CPU; projected peak heap under 3 GiB; frame region below half its size (8 MiB).
  - **Measured at vm-e2e3, against the hard bars:** at most 15 minutes of CPU, with the kill line at 60; peak heap under 4 GiB (D19); frame-region use within the region.
- Seed-native ratios are recorded, never gated.
- The 10× design-review stop is discharged by this review.

**D28: a generated release module.**
- `vm/vm.wasm` may be built through the pinned inlining pass of P1. The pass is admitted only while the identity row holds.
- `vm/vm.wat` stays the reviewed source.
- DoD item 1's "assembled by the pinned wabt `wat2wasm`" gains "through the pinned inliner".
- **Consequence for vm-emit-2.** The Knot-emitted VM must reproduce the inlined module. Otherwise the VM-bytes fixpoint is stated over the plain build, with the inlined module as a derived, state-identical artifact.

**Engine of record.**
- Recommended: node 22.22.3 (V8 12.4) stays the engine for gates and for A2(S). D19's growth evidence and every VM gate are on it.
- Bun/JavaScriptCore is recorded as a cross-check lane.
- If Bun is chosen instead:
  - drop P1, which gains only about 17% there;
  - validate the host under Bun first: quantum re-entry, growth to 65,536 pages and knot-io-2.

**VM-DESIGN edits:**
- vm-speed splits into vm-fuse, vm-frames, vm-lower and vm-moves.
- vm-e2e2's escalation order becomes §7's P4.
- The shipped compact image leaves the plan.
- vm-rc and vm-e2e2 gain P2's and P4's rows.

**Later SPEC changes, each in its own increment:**

| Increment | SPEC change |
|---|---|
| S1 | SPEC 6: one sentence defining a macro-step, as a composition of 1 + xw rows none of which can stop, yield or perform an effect. The one-walk eq keeps 6.3's read order. |
| S2 | SPEC 5 (the Activation class goes); 6 (Scope frames go, Act and Args frames arrive, the rows); 6.2 (the tail rule); 7 step 3; 11 and 12 (bounds and re-frozen rows); the frame-region size |
| S3 | SPEC 6: the fused rows, with the unfused table as the normative anchor through the refinement law. The image format is unchanged. |
| S4 | `Exhausted` heap restated as a bound on live data. A native-stack exhaustion rule. Quantum behaviour. |

---

## 9. What the user must decide

1. **D27.** Restate the bench gate as in §8, or keep "≤ 4× seed-native".
   - No measured design meets 4× on deep-recursion, peano or list-fold.
   - No interpreter variant comes close: the best is 23× on peano.
   - On deep-recursion, no design that keeps per-entry fuel can.
2. **D28.** Allow a generated, state-identical release module, knowing how it bears on vm-emit-2's VM-bytes fixpoint.
3. **Engine of record.** node (recommended) or Bun. This decides whether P1 is worth doing.
4. **V1 timing:**
   - before vm-rc: RC is written once; +5.5 agent-days on the VM chain; SPEC 5–7, the model and the fixtures are reopened; the kind-3 boundary moves;
   - or after vm-e2e2 (recommended): about 1–2 agent-days of RC rework later, decided with S's measured frame and heap profile.
5. **The escalation order at vm-e2e2** in §7 P4, which replaces "dense tables and superinstructions, then the compact image, then a cap raise". A cap raise beyond 4 GiB would need memory64, which is outside D19.
6. **Optional, outside the VM.** Knot's Q.qualify makes 4 strict scans of about 1,500–2,000 globals per non-local reference. That is 58% of A2(S)'s entries and quadratic in S's size.
   - A single scan or an indexed lookup in the frontend would cut roughly half of A2(S)'s entries, and C1's native time too.
   - It is a compiler-source change owned by the modules and literals line, with byte-identical output required.
   - It is not needed for the targets.
7. **A quiet-host window** for vm-e2e2's and vm-e2e3's measurements. The host ran at load 20–107 through this review. If no window is available, instructions retired are the figure of record.
8. **Direction after vm-e2e3.** Interpreter hill-climb (S1–S3, towards 30–55 cycles per entry, about 15–20 agent-days) or the native track (S4, 10–40 cycles per entry, 8–20 weeks, a trust-base change).

---

## 10. Risks and open questions

- **A2(S) is a model, not a measurement.**
  - C1 cannot compile S yet.
  - Entries are 0.7–1.9× of central and cycles per entry ±25%.
  - check and encode rest on toy fits.
  - The S that vm-e2e3 compiles will be larger than S_B.
  - vm-e2e2's parse-cli covers only lex and parse, about 6% of the modeled entries. Qualify (58%), the Base slice, check and encode stay modeled until vm-e2e3's A2(S) run. That run is the first real gate on them (P5).
- **RC's live set (0.1–0.5 GiB) and its cost are unmeasured.** The profiler estimates +5–10% instructions; the AOT's `rc-count` lower bound is +17–27% on much cheaper compiled code. P2 measures both.
- **The frame region on S is unmeasured.**
  - Non-tail Base recursion over a file's Char list or an output byte list is the plausible kind-3 risk.
  - V1 increases frame use for wide functions.
  - P4 gates on it.
- **Engine and machine.**
  - Every table is one Apple M5 Max (arm64). Most are on node 22.22.3.
  - repr repeated its ladder on JSC and on V8 with its inliner.
  - The pinned VM's per-entry cost differs 2.4× between engines, so every ratio depends on the engine.
  - x86-64 and other versions are unmeasured.
- **Load.**
  - All roles measured at one-minute load 20–107.
  - Instructions retired are reliable; cycles carry ±5–15%.
  - About a third of string-scan's cycles are cache misses on dead Activations interleaved with live cells, an artifact of an arena that never reclaims, which vm-rc changes.
- **The prototypes target 019e615f.**
  - vm.wat has since moved (+233 / −85 lines: D22–D25 and atomic stops).
  - vm-spec pinned the order of reads (09e2bc77).
  - Fused spans, V1 and V2 need re-derivation. The codegen pass does not.
  - The AOT's one-walk String.eq would name a different stop than the pinned order when both Strings hold bad words of different kinds.
- **Fused spans.**
  - Existing gates step unfused and never exercise a span. Only the new aligned rows, page-cap sweeps and twin mutants do.
  - The comparer is stricter than SPEC (all registers); which registers a macro-step must reproduce is undecided.
- **W's reach on S is unmeasured.** interp's W covers immediate-operand wrappers of prims 0–21, 23 and 25–31 only. The profiler's larger W gain skips the Activation and is heap-visible.
- **Trusted build.** P1 adds a flattener and a roughly 150-line inliner to the build. The module grows, and start-up rises by about 20 M instructions (codegen only).
- **AOT.**
  - Its exact-heap mode is exact only against a VM that never reclaims.
  - Its native-stack divergence has no launcher fix.
  - A missing fuel debit hangs.
- **Disclosure from the projection role.** It ran one broad `pkill -f 'mbrun|run-wasm-io.mjs'`, which may have terminated other roles' `run-wasm-io.mjs` jobs. The results cited here come from completed, logged runs. A timing that coincided with that kill could have been disturbed.

---

## 11. Sources

Scratch directories under `…/scratchpad/vmperf/`.

| Role | Where |
|---|---|
| profile | `profiler/work/` (tools and `out/*.json`) |
| projection | `projection/`: `project.py`, `final_tables.py`, `logs/` |
| interp | `interp/README.md`, `interp/out/`, `interp/tools/` |
| aot | `aot/aotproto/README.md`, `aot/aotproto/out/` |
| repr | `repr/README.md`, `repr/results/`, `repr/work/` |

**Repository sources, read only:**
- `docs/COMPILER-CAMPAIGN.md` (D13–D26) on main;
- `docs/compiler-campaign/VM-DESIGN.md`;
- on campaign/vm-lockstep: `vm/SPEC.md` §5–7, `vm/bench/README.md` and `tests/compiler-vm-lockstep/REPORT.md`;
- vm-spec commit 09e2bc77 (read-order pins).

The A2(S) figures under codegen in §6.1 were recomputed here from the projection's saved module data, using repr's same-run V0 → V0cg factors.
