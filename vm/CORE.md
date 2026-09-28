# knot-vm-1 in WAT: `vm/vm.wat`

Increment `vm-core` (D14). `vm/vm.wat` implements [SPEC.md](SPEC.md) as written,
independently of `vm/model.bend`; the two are compared in `vm-lockstep`. This file
records how the VM reports outcomes, where it places state the spec leaves open,
and where the spec needed an interpretation. Gate `vm-core` (`vm/check-core.py`)
is the evidence.

```sh
python3 vm/build.py                 # the pinned wat2wasm reassembles vm/vm.wasm byte for byte
python3 vm/build.py --write         # after a reviewed edit of vm.wat: rebuild and re-pin
BEND_NO_TELEMETRY=1 node scripts/run-wasm-io.mjs vm/vm.wasm SANDBOX -- IMAGE FN FUEL [ORDINALS...]
BEND_NO_TELEMETRY=1 node scripts/run-wasm-io.mjs vm/vm.wasm SANDBOX -- IMAGE FUEL -- [ARGS...]
BEND_NO_TELEMETRY=1 python3 vm/check-core.py
```

## Build and pins

- [build.json](build.json) pins `wat2wasm` 1.0.41 with no flags, the sha256 of
  `vm.wat`, of `vm.wasm` and of the test build. `vm.wasm` is committed; the gate
  reassembles it and requires identical bytes.
- The design puts the `vm.wasm` hash in `src/CONTRACT.json`. This increment does
  not edit `src/`, so the pin lives in `vm/build.json`. The coordinator can
  mirror it into the contract.
- **The test build** strips the `;;TEST ` prefix from its lines. That adds the
  exports `vm_limits`, `vm_boot`, `vm_step` and `vm_dump`, plus a stop after
  every transition when stepping. The production module exports only `memory`,
  `knot_alloc` and `knot_main`. It imports seven `knot_io` functions and
  declares a memory maximum of 65,536 pages.
- [harness.mjs](harness.mjs) is an in-memory `knot_io` host for batches and
  for the test build. It steps the machine, reads registers and audits each
  state. Acceptance runs use the real host, `scripts/run-wasm-io.mjs`.
- That host is main's file byte for byte (`2e93d58`, sha256 `4ee7b16d…`),
  because this branch's base predates io-host. An identical add merges cleanly.

## Outcomes at the host boundary

| Outcome | How it is reported |
|---|---|
| Book result | `print("Evaluated\ttype\ttag\ttree")`, then `knot_main` returns (exit 0) |
| Program `Emit` / `Halt` | return (exit 0) / `die(code, message)` |
| HostFailure | `die(5, "HostFailure\t<phase>\t<code>")`; the phase is `image`, `invoke`, `arguments` or `io` |
| Unsupported | `die(3, "Unsupported\t<phase>\t<code>")`: `invoke result-type`, and `vm foreign` |
| InternalFailure | `die(6, "InternalFailure\tvm\tinternal")` |
| Exhausted | `exhausted(kind)` |

These follow eval-cli's status numbers and its tab-separated layout, without a
source location. The host shows only an exhaustion's kind. The precise cause
(`fuel`, `heap`, `frames`, `NatRange`, `image-size`, `display`) stays in the
outcome registers, which the test build's `vm_dump` exposes (SPEC §11).

**Refusal codes.** A refused image names one kebab-case code, such as
`section-offset`, `slot-depth` or `noncanonical`. Each code corresponds to
exactly one of `serializer.py`'s messages; `check-core.py` holds the table. The
loader decodes in `serializer.decode`'s order. The validator follows the order
of `serializer.validate`'s recursion and stops at the first defect, and the
canonical check comes last. A refusal therefore names the reference codec's
first defect. The gate requires this on:
- the 61 frozen controls;
- 3,120 seeded single mutations of the goldens: 2,868 refused, and 252 admitted
  and run to a clean outcome.

## Memory beyond SPEC §5's map

- **Arguments** arrive at `0x2010000`, above every possible frame region.
- **The image** is read in 1 MiB `read_bytes` chunks. `knot_alloc` points each
  chunk directly at its place after byte 4096. A 17th MiB means
  `Exhausted image-size`, even when the image is also malformed.
- **Boot tables** sit in the frame region, which stays free until the machine
  starts:
  - record offsets of names, constructors, functions and constants at F0 + 64 KiB;
  - the arrow-fit stack at F0 + 8 MiB;
  - Book ordinals at F0 + 64.
- **Boot scratch** starts above both H0 and the arguments: node marks, scope
  types and uses, the task stack, the arrow-pair memo, the describe domain.
  Constants are then materialized from H0, so cell addresses follow SPEC §5
  exactly.
- **Linking in place.** After validation the loaded copy is rewritten:
  - Literal constant indices become pool words.
  - Application function indices become function record offsets.
  - A data type's first-constructor index becomes that constructor record's offset.
  - Constructor name indices become name record offsets.

  Node offsets, which the machine state names, do not change. Those words of
  the loaded copy no longer equal the file.
- **Scratch above the bump.** Describe, UTF-8 output and `Halt` messages are
  built above the bump pointer, which they do not advance.

## Choices the spec leaves open

These are the VM's answers where SPEC is silent or ambiguous. `vm-model` should
adopt them or record its own, so that lockstep compares like with like.

1. **Reclamation.** vm-core has none (vm-rc adds it). Cells carry rc = 1.
   Constants and the terminal continuation are immortal. `$dup` and `$drop`
   mark every substep of §5–§7 and are empty.
2. **Foreign leaves.** vm-core performs only `IO.print`. An image that
   contains any other foreign id is refused as `Unsupported vm foreign` before
   any entry: a D4 capability gap, never Invalid. vm-io lifts this.
3. **String prims inspect before they allocate.**
   - `eq` walks all of `a`, then all of `b`, then compares.
   - `append` walks `a` only; `b` is moved, not read.
   - `reverse` and `length` walk their operand.
   - `is_empty` reads only the head cell.

   So the ill-typed word a prim reports does not depend on where a comparison
   stops.
4. **`append` on the bump arena.** It writes its L cells as one block, at the
   addresses that allocating from the last character to the first would give.
   A heap too small for the block is reported before any of it is written.
   Sequential allocation would stop partway, so only the halted state's bump
   pointer can differ.
5. **Nat Case.** The new word n − 1 is allocated only when the selected arm is
   the Branch that binds it, not when the Default is taken.
6. **Rendering bounds.** A visit is one rendered constructor application. A
   Nat word n counts n + 1 visits, one per layer of its logical view. The
   16 MiB bound applies to the tree text, after `Evaluated\ttype\ttag\t`.
7. **Invocation order.** Checks run in this order:
   1. usage;
   2. the image;
   3. the syntax of FUEL and the ordinals (`arguments expected-u32`);
   4. the export (`invoke unknown-export`);
   5. arity;
   6. each ordinal: `argument-range` (also for a parameter of a
      non-algebraic type), then `structured-argument`;
   7. the result type (`Unsupported invoke result-type`).

   A Program's third word must be `--` (`arguments usage` otherwise).
8. **Halted states.**
   - At an `ill-typed` halt only the outcome is specified: a Gather frame may
     already be popped.
   - At zero fuel the pending Enter's registers are kept and the mode reads
     Halt. §7 asks that the Enter stay in the state, while §6 lists Halt as a
     control.
9. **A `Halt` result.** Its message is converted to UTF-8 before the result
   is dropped.
10. **4 GiB.** A cell ending exactly at 4 GiB would wrap the i32 bump pointer.
    It traps (HostFailure) instead; no host grows memory that far.

## Findings for the spec owner

- **String constants above U+10FFFF.** §2 says a String constant holds exact
  Chr codes and pure Char admits every u32. `serializer.decode` instead refuses
  a code above `0x10FFFF` (`string code beyond plan text`). Canonical form is
  defined by that codec, so vm-core refuses too (`string-code`). The spec or
  the codec should change, and vm-model should follow whichever rule results.
- **Deep images.** The reference codec's `decode` and `encode` recurse, so they
  fail on images nested deeper than Python's recursion limit. `check-core.py`
  lays out its 200,000-deep image iteratively. At depth 40 that layout is
  checked equal to `serializer.encode`.
- **Ambiguities.** Choices 5, 6 and 8 above are real ambiguities in §6–§8 and
  need one normative reading before lockstep.

## Evidence (gate `vm-core`)

- **Goldens.** All 78 through the real host, equal to `vm-expected.json`. The
  test build confirms every Exhausted and Unsupported cause and audits the
  state after all 1,503 transitions.
- **[core/fixtures.json](core/fixtures.json).** Literal review, frozen before
  any run:
  - the 250,000-deep non-tail recursion, with 500,003 entries and seven yields
    at multiples of 65,536;
  - a 400,000-deep one, which exhausts the 16 MiB frame region;
  - a yield immediately after an Action's effect (`q` printed once);
  - exact fuel boundaries, rendering and both display bounds;
  - an ill-typed flow through a `none` parameter;
  - the Unsupported foreign leaf, and the invocation errors.
- **Small host stack.** A generated 200,000-deep nested expression, and the
  deep runs, under `node --stack-size=64`. The call graph of `vm.wasm` has no
  cycle and no `call_indirect`.
- **Malformed images.** As above: 61 frozen controls and 3,120 fuzz images,
  with no trap.
- **Mutants.** Nine, each killed by a wrong observation in a named group:
  - arm selection, slot off-by-one, Nat bound and x % 0 (goldens);
  - fuel (fuel boundaries);
  - validator offset (goldens and controls);
  - quantum state loss (quantum re-entry);
  - tail release (display bound);
  - host-stack recursion (call graph).
