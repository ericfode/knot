# Bounded runtime law review

Scope: R4 locator freshness and R6 frontier transfer under `knot-device-records-1`.
Independent model code is Bend; the device implementation is handwritten WGSL.
The executable fixed controls precede implementation in `fixtures.json`.

| Operation | Public observations / witnesses | Law / independent check | Mutation |
| --- | --- | --- | --- |
| Slot insert/alloc | Incoming owner returned on occupied/full/retired; unrelated slot preserved; capacities 0/1/2 | Existing owning-store model; 30 command observations on Bun/native, all device phase observations compared when available | GPU generation-wrap, ignored arena/generation |
| Slot take/drop | Locator realm/bounds/state/generation; copied/old locator cannot extract twice; retirement at ceiling 0/1 | Existing owning-store complete proof gate plus model trace; new device readback gate | GPU generation-wrap, ignored arena/generation |
| Offer | Ready/Suspended -> Queued; full returns unchanged frontier and task owner; duplicate rejected | `offer_full`, `offer_duplicate`; fixed empty/full/duplicate/bounds cases | consume-full-owner, duplicate-offer |
| Prepare | Reversal changes physical queue positions and preserves task identity/destination | `prepare_reverse`; every phase compared to Bend | GPU duplicate-compaction, read-before-publication |
| Execute | Quantum 0 preserves PC/value/destination; quantum 1 advances once; Yield/Wait/Return differ | Quantified `zero_slice`; concrete `round_wait`; zero, waiting and complete controls | change-destination, advance-zero-budget, ignore-wait |
| Publish | Each consumed frontier is empty; Suspended/Waiting/Done retain owner obligations in their records | `round_suspend`; complete 13-command lifecycle | retain-consumed-frontier |
| Internal PC fault | Retain the faulted task and queue, return InternalFailure | `fault_retains`; internal-program-end control | erase-internal-fault |
| Wake / failures | Only Waiting wakes; full=Exhausted, bad quantum=Invalid, unknown command=Unsupported; rejected owners retained | Fixed 10-case R6 controls and complete prefix/phase traces | Wrong outcome or state is an observation mismatch |

`PROOF.bend` fills all eight new laws and passes the full seed entry. Both
`zero_slice` and `unsupported_slot` quantify over arbitrary record contents. The other six laws are
inhabited concrete normalization controls. These laws describe the independent
CPU model; they are not proofs of WGSL refinement, concurrency or arbitrary
ownership histories. The existing R4 model/store proof gate remains separate.

The seven CPU mutants typecheck before their complete proof entry fails at a named
law, and the fixed literals independently reject them. The first mutation pass
showed that the final complete lifecycle reconverges after `ignore-wait`: the
law already killed it, but that final value alone did not. A dedicated literal
`wait-before-wake` observation now exposes the intermediate Waiting owner.
No previously fixed assertion or expected value was changed.

WGSL mutants create valid pipelines before any semantic rejection can count.
The hardware runner first requires the unmutated implementation to match all
Bend observations. It then counts only a named fixture/phase observation
mismatch as a kill. Shader compilation, API validation, unavailable adapter,
missing model data or other host/internal failures cannot kill a mutant.
All nine device kills remain unrun in this environment.

The bounded source review also found and closed an Unsupported slot-decoder gap,
an unchecked cleared-payload word, a noncanonical success reason, and a mismatch
in malformed-PC publication. Unknown-slot and internal-program-end literals now
exercise those classifications; a ninth shader mutant retains an extracted
payload. External device request/submission/mapping failures carry HostFailure
explicitly, while shader/observation defects remain InternalFailure.

The full semantic projection retains ordered free IDs, empty/retired slots,
payloads, PC, destination, logical slot, reply and queue membership. Record
padding, reserved words, code ranges and every word outside capacity are checked
separately. The old 38-case comparison excludes only scheduling state hashes and
logical worker movement; neither field is language semantics.

Adversarial boundaries still open: arbitrary input record validation, issuer and
restore realm freshness, genuinely affine object payloads, owning capture arrays,
shared Data edges, join attempt freshness, cancellation, suspended readers,
resumable cleanup, multi-workgroup scheduling, general allocation and a GPU
memory-model proof. Task IDs are not recycled in R6. R4 reuse is synchronous
between completed commands. No source-level Knot evaluator/Wasm run is claimed
for these record fixtures because that compiler profile has not been implemented.

Offline Perch preflight parses 57 declarations, with complete bounded composition
but four caller-context truncations (`Task`, `State`, `Command`, `result`). No
live semantic or style score is available. The coordinator owns that review;
these deterministic receipts do not waive its quality targets.
