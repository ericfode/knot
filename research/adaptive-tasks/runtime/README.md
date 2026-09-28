# GPU runtime increment: R4 and R6

Status: implemented candidate; **device acceptance blocked**. Metal
`requestAdapter` returns null in this executor environment. The host reports an
Apple M5 Max with Metal support. No fallback execution is counted as device
success. The old 38-case before/after comparison and nine new WGSL mutant kills
remain unrun. This increment is not ready to claim the campaign's GPU gate.

The [versioned record contract](../../../docs/WASM-WEBGPU-BACKEND.md#device-record-contract-knot-device-records-1)
specifies `knot-device-records-1`: checked slot locators and scalar continuation
records interpreted across prepare, execute and publish dispatches. The
[probe specification](SPEC.md) fixes its small domain. No `src/` file changes.

## Evidence

| Gate | Fresh result |
| --- | --- |
| Literal controls | 6 R4 cases + 10 R6 cases |
| Seed CPU comparison | 62 commands / 186 phase observations, identical Bun/native output |
| New complete proof entry | 8 filled laws; `All terms check.` |
| New CPU mutants | 7 type-correct mutants killed by named laws and literal observations |
| WGSL validation | 10 variants / 30 pipelines; Dawn null backend, 0 device executions |
| WGSL semantic mutants | 9 constructed and typechecked; 0 hardware kills established |
| Existing adaptive CPU gate | 12 laws, 10 fixtures, 11 observations, 2 quantity negatives, 5 mutants |
| Replay comparison tests | 24 checks: 3 equivalence controls and 21 rejection controls |
| Replay/output tests | 6 checks; retained artifacts unchanged |
| Codegen replay | Seed, generated Node JS and native C agree on 11 observations |
| Offline style preflight | 57 declarations; 4 truncated contexts; composition available, no unresolved references |

Evidence lives in [receipts/](receipts/), including the [eleven required regression gates](receipts/regressions.json). Device-unavailable receipts are failures,
not replacement passes for the historical tree probe. Existing receipts outside
this increment are restored after regression execution; they are not promoted
by this run. In particular, old trust receipts may describe earlier source
hashes; the fresh gate output is retained separately here.

The proof consists of two quantified laws and six concrete
normalizations. It is not a device refinement theorem. The seven CPU mutants are
consume-full-owner, duplicate-offer, change-destination, advance-zero-budget,
ignore-wait, retain-consumed-frontier and erase-internal-fault. The nine WGSL variants target retained extracted payloads, ignored
generation/arena checks, generation wrap, consuming an owner on full, duplicate
compaction, destination corruption, reading before publication and advancing PC
at zero quantum. See [LAW_REVIEW.md](LAW_REVIEW.md) for coverage and limits.

## Run

All commands are local. The dependency is pinned `webgpu` 0.6.1; it was installed
with `npm ci --prefix research/adaptive-tasks/gpu --offline --no-audit --no-fund`.
The seed is Bend 2.0.29 (`574b6d3`).

```sh
export BEND_NO_TELEMETRY=1
# Fresh hardware acceptance, including nine semantic mutation kills:
python3 research/adaptive-tasks/runtime/check.py
# Explicitly partial checks for environments without Metal access:
python3 research/adaptive-tasks/runtime/check.py --cpu-only
python3 research/adaptive-tasks/runtime/check.py --validate-only
# Existing semantic regression against a separately captured baseline:
node research/adaptive-tasks/gpu/check.mjs --out-dir .local/gpu-before
node research/adaptive-tasks/gpu/check.mjs --out-dir .local/gpu-after --compare-receipt .local/gpu-before/gpu.json
# Offline harness checks:
node --test research/adaptive-tasks/tests/replay.mjs
python3 research/adaptive-tasks/tests/replay.py
node scripts/perch-style.mjs --preflight --task=research/adaptive-tasks/runtime/SPEC.md research/adaptive-tasks/runtime/frontier.bend research/adaptive-tasks/runtime/slot-model.bend research/adaptive-tasks/runtime/LAWS.bend research/adaptive-tasks/runtime/PROOF.bend
```

`runtime/check.py` defaults to ignored `.local/adaptive-tasks/runtime/`. An
explicit `--out-dir DIR` changes that destination. Plain replays never replace
retained receipts. The old harnesses also expose `--update-receipts` for an
explicit evidence refresh. `--cpu-only` cannot replace a complete old receipt.

To obtain a true pre-change baseline, the coordinator must run the old host at
parent `185b7d5` in its own review checkout, save that receipt, then use the
current `--compare-receipt` flag. Two new-code runs above test repeatability;
they alone do not establish pre-change agreement. This executor did not touch
another checkout to manufacture a baseline after losing Metal access.

## Remaining acceptance and next increment

1. Run the old 38 cases before/after on hardware, the new R4/R6 probes, and all
   nine WGSL mutants. Confirm full phase observations and every capacity guard.
2. Resolve or explicitly review preflight's four caller-context limits:
   `Task`, `State`, `Command`, `result` (57 declarations across four files;
   composition 25,587 / 48,000 bytes). Live Perch semantic/style review belongs
   to the coordinator. Compression, Delight, memetic identity, Anticipation and
   Payoff are all **unrated**, not passed by the offline preflight.
3. Only after device qualification, emit one versioned record bundle from Knot,
   add the host decoder/validator and connect a Wasm host. Preserve source-level
   seed ⇔ Knot evaluator ⇔ Knot Wasm ⇔ device differential checks.
4. R5 waits for mixed affine capture storage, reusable Data lifetime and explicit
   attempt identity/cancellation. Add right-before-left 709 and n-ary joins only
   with those ownership obligations; R3/R7 remain separate gates.

The current R4 model is the independent list-based owning-store model, unchanged;
R6 is the new Bend list/state model. The host only constructs test inputs and
decodes observations. The probe accepts trusted fixture bundles, not arbitrary
external record graphs. Scalar owner serials, two-record bounds, supplied arena
IDs and quiescent command-by-command reuse are explicit limits. No speed, general
allocation, generic Type captures, shared Data, multi-workgroup scheduling or
compiler-generated GPU execution claim is made.
