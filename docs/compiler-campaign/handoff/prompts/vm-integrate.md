# VM-track integration round on campaign/vm-lockstep

`campaign/vm-lockstep` (019e615f) is vm-model and vm-core combined, plus a lockstep harness. It compares the VM with the model on full machine state after every transition, and it holds a bench. It becomes the branch the whole VM track merges to main from, after closures lands (six closure goldens must never be baselined as Invalid).

1. **Merge the reviewed tips** with merge commits, never a rebase:
   - `campaign/vm-spec` (round 14: D25 atomic stops, ready);
   - `campaign/vm-model` (round 4);
   - `campaign/vm-core` (round 7);
   - `campaign/image` (the encoder, reviewed and ready);
   - `main`.

   Resolve conflicts so both sides' intent survives. Regenerate the census; do not hand-merge it. Keep main's copy of shared receipts.
2. **Atomic stops (D25).** Remove the lockstep's two halting relations (shape predicates and raw-frame applicability). Once both machines stop atomically, the lockstep compares full state at every halt with plain equality. Any disagreement is a bug in the machine that deviates from vm/SPEC.md §6–§8. Fix it there, with a frozen run.
3. **Two known divergences.** Fix whichever machine deviates, and freeze a run for each:
   - (a) A Halt with a non-scalar Char message. The VM refuses it as `io abi`, while the model dies. The model must follow D20's Halt rule.
   - (b) An image that names an unimplemented (non-print) foreign. Both machines must refuse it at load as `Unsupported vm foreign N`, until vm-io.
4. **Encoder fixes**, from image's review:
   - (a) Refuse (Exhausted kind 2) a Closure whose slots exceed the §4 limit, and make decode refuse it too.
   - (b) `arm_for` must answer InternalFailure, not an invalid image, when it meets a non-Branch arm (make `image-arm-node` live).
   - (c) Reconcile the 3 decoder-refusal expectations that differ from the reference codec (`vm/serializer.py`). The reference codec decides. Each change goes in a seed or reference-derived amendment commit.
   - (d) Measure that no name in Knot's own `src/*.bend` is refused by `Unsupported compile image-name`. If one is, report it prominently.
5. **Speed review P0** (`/Users/ericfode/src/knot/docs/compiler-campaign/handoff/vm-perf-design-review.md`, sections P0 and D27):
   - Freeze the compiler-shaped workloads under D7: the four bench variants, cps-choose, the qualify contains-loop and the find scan with closures. Record each one's source, an independent guard, its seed-native baseline and its image sha. Use campaign/image's encoder where Knot's checker accepts the source, and label any hand-lowered plan.
   - Measure on the integrated vm.wasm under node 22.22.3: instructions retired per entry (primary), cycles per entry and peak RSS, with the load recorded, taking the median of at least 5 alternating runs, and with a JavaScriptCore cross-check.
   - `workloads.json` pins every source, image and baseline. The runner reports per-entry figures and **never gates on a seed ratio** (D27, pending the user's confirmation; record the ratios anyway).
   - Record the design review as vm-lockstep's bench disposition.
6. Run `npm run -s gates` and the lockstep's full differential, and report every gate's exact counts.

For the coordinator, not you: mirror `vm/build.json`'s vm.wasm sha into `src/CONTRACT.json` at merge, fix the stale `vm/model.bend` paths, and fix VM-DESIGN §2's eager IO wording.
