# knot-vm-1 in WAT: `vm/vm.wat`

Increment `vm-core` (D14). `vm/vm.wat` implements [SPEC.md](SPEC.md) as written,
independently of `vm/model.bend`; the two are compared in `vm-lockstep`. This file
records how the VM reports outcomes, where it places state the spec leaves open,
and where the spec needed an interpretation. Gate `vm-core` (`vm/check-core.py`)
is the evidence.

```sh
export BEND_NO_TELEMETRY=1
export PATH=/Users/ericfode/.bun/bin:$PATH
bun --version                      # must be 1.3.14; a different Bun fails io-host's frozen reference
python3 vm/build.py                 # the pinned wat2wasm reassembles vm/vm.wasm byte for byte
python3 vm/build.py --write         # after a reviewed edit of vm.wat: rebuild and re-pin
BEND_NO_TELEMETRY=1 node scripts/run-wasm-io.mjs vm/vm.wasm SANDBOX -- IMAGE FN FUEL [ORDINALS...]
BEND_NO_TELEMETRY=1 node scripts/run-wasm-io.mjs vm/vm.wasm SANDBOX -- IMAGE FUEL -- [ARGS...]
BEND_NO_TELEMETRY=1 python3 vm/check-core.py
BEND_NO_TELEMETRY=1 python3 vm/check-core.py --freeze         # rewrite core/seeded.json and core/lane.json from the seed
BEND_NO_TELEMETRY=1 KNOT_GATE_TIMEOUT_SCALE=2 python3 vm/check-core.py --study --heavy --jobs 10  # the 993 systematic mutants; guards recorded in the receipt
BEND_NO_TELEMETRY=1 python3 vm/check-core.py --study --only NAME,NAME  # the mutants whose names contain one of these (no receipt)
```

## Build and pins

- [build.json](build.json) pins `wat2wasm` 1.0.41 with no flags, the sha256 of
  `vm.wat`, of `vm.wasm` and of the test build. `vm.wasm` is committed; the gate
  reassembles it and requires identical bytes.
- The design puts the `vm.wasm` hash in `src/CONTRACT.json`. This increment does
  not edit `src/`, so the pin lives in `vm/build.json`. The coordinator can
  mirror it into the contract. Round 7 (D22 to D24, SPEC §6.3) re-pinned it:
  `vm.wasm` sha256 `a8ef5f83…49f9f9` (20,278 bytes; the scope-table fix of round 6 had
  `407cb872…a7a2`, 19,697), `vm.wat` `96bc6c90…bcb1a`. Nothing since has changed either.
- **The test build** strips the `;;TEST ` prefix from its lines. That adds the
  exports `vm_limits`, `vm_boot`, `vm_step` and `vm_dump`, a stop after
  every transition when stepping, and a count of `memory.grow` calls that
  `vm_dump` reports (`grows`). The production module exports only `memory`,
  `knot_alloc` and `knot_main`. It imports seven `knot_io` functions and
  declares a memory maximum of 65,536 pages.
- [harness.mjs](harness.mjs) is an in-memory `knot_io` host for batches and
  for the test build. It steps the machine, reads registers and audits each
  state. Acceptance runs use the real host, `scripts/run-wasm-io.mjs`.
- That host is main's file byte for byte (sha256 `4ee7b16d…`, last changed at
  `2e93d58`). It arrived with main through the vm-spec merge.

## Outcomes at the host boundary

| Outcome | How it is reported |
|---|---|
| Book result | `print("Evaluated\ttype\ttag\ttree")`, then `knot_main` returns (exit 0) |
| Program `Emit` / `Halt` | return (exit 0) / `die(code, message)` |
| HostFailure | `die(5, "HostFailure\t<phase>\t<code>")`; the phase is `image`, `invoke`, `arguments` or `io` (`io abi`: D20's non-scalar output) |
| Unsupported | `die(3, "Unsupported\t<phase>\t<code>")`: `invoke result-type`, `vm foreign` and `vm effect` |
| InternalFailure | `die(6, "InternalFailure\tvm\tinternal")` |
| Exhausted | `exhausted(kind)` |

These follow eval-cli's status numbers and its tab-separated layout, without a
source location. The host shows only an exhaustion's kind. The precise cause
(`fuel`, `heap`, `frames`, `NatRange`, `display`, and §4's image limits
`image-size`, `records`, `arity` and `slots`) stays in the outcome registers,
which the test build's `vm_dump` exposes (SPEC §11).

**Refusal codes.** A refused image names one kebab-case code, such as
`section-offset`, `slot-depth` or `noncanonical`. Each code corresponds to
exactly one of `serializer.py`'s messages; `check-core.py` holds the table. The
loader decodes in `serializer.decode`'s order. The validator follows the order
of `serializer.validate`'s recursion and stops at the first defect, and the
canonical check comes last. A refusal therefore names the reference codec's
first defect. A resource limit of §4 is no refusal: an image past one stops
`Exhausted` kind 2 with the limit as its cause (choice 14), and the gate
compares that in the reference's own words (`Exhausted 2 records`). The gate
requires this on:
- the 211 frozen controls, counted against SPEC §4's own figure (124 byte-level,
  9 at the limits, 78 plan-level). Before any VM runs, `refusal_expectation`
  derives the complete exit, empty stdout, stderr and outcome registers from the
  reference codec's first verdict and §11's host contract. Both the production
  module and the test build must equal that expectation; the test build must
  make zero entries and effects. The same expectation is used by mutant jobs;
- 4,440 seeded single mutations of the goldens: refused images must equal that
  complete independent refusal, and admitted images run to a clean outcome;
- 9,810 images that set one word of a limit (each section's record count, each
  function's arity and `slots`, each Closure's `slots`) to values around its
  limit and, for a count, around the fit of two words per record: every refusal
  is compared with the complete independent expectation, including zero entries
  and effects. Their mutant jobs also derive expectations from the reference,
  rather than copying a VM observation.

A refusal is read only from a run that stopped before `vm_boot` returned. A run
that got past boot and failed `ill-typed` inspected a word at run time (§6). It
did not refuse the image.

## Memory beyond SPEC §5's map

- **Growth.** Linear memory grows in 16 MiB steps (choice 15). The arguments,
  at `0x2010000`, already take it to 48 MiB.
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
  types and uses (W + 4200 indices at first, and doubled where an image needs more,
  choice 16), the task stack, the arrow-pair memo, the describe domain.
  Constants are then materialized from H0, so cell addresses follow SPEC §5
  exactly.
- **Linking in place.** After validation the loaded copy is rewritten:
  - Literal constant indices become pool words.
  - Application function indices become function record offsets.
  - A data type's first-constructor index becomes that constructor record's offset.
  - Constructor name indices become name record offsets.

  Node offsets, which the machine state names, do not change. Those words of
  the loaded copy no longer equal the file.
- **Scratch above the bump.** Describe's text, UTF-8 output and `Halt`
  messages are built above the bump pointer, which they do not advance. Their
  addresses are summed in 64 bits.
- **Describe's worklist** sits in the frame region above Top, where §5 keeps
  release's worklist. It holds one (cell, record, next field) triple per open
  Object. Each triple took a visit, so at most 1,048,576 triples (12 MiB) are
  open, and the 16 MiB region always holds them. A test build that lowers the
  frame limit can overflow it, which stops with `Exhausted` kind 3 (frames).
- **`knot_alloc` after boot (an obligation for vm-io).** After boot,
  `knot_alloc`'s cursor still points just past the loaded image, into the gap
  before the frame region. This is harmless in vm-core, because no allocating
  import runs after boot: `print`, `die` and `exhausted` return nothing.
  vm-io's `args`, `read` and `read_bytes` effects must first aim it at
  allocator blocks above the bump.

## Choices the spec leaves open

These are the VM's answers where SPEC is silent or ambiguous. `vm-model` should
adopt them or record its own, so that lockstep compares like with like.

1. **Reclamation.** vm-core has none (vm-rc adds it). Cells carry rc = 1.
   Constants and the terminal continuation are immortal. `$dup` and `$drop`
   mark every substep of §5–§7 and are empty.
2. **Foreign leaves.** vm-core performs only `IO.print`. A Program image that
   names any other foreign id is refused as `Unsupported vm foreign` before any
   entry, though its `main` may never reach it: a D4 capability gap, never Invalid.
   A Book loads whatever foreign it holds, since it never performs (D22): `book-args`
   (`IO.args`) builds a request and stops `Unsupported vm effect` where a read meets it
   (choice 17). vm-io lifts the refusal.
3. **Every operand is read over its whole extent (settled by SPEC §6 and
   §9, vm-spec DECISIONS 18).** A prim inspects each operand at its §9 type, in
   operand order, before it computes or allocates: a scalar's word, the four
   conversions' moved word included, and a String whole, each SCon cell and
   its Char word, head to tail, to SNil (`$scell`, walked by `$slen`).
   - `eq` walks all of `a`, then all of `b`, and only then compares: no early
     exit.
   - `append` walks all of `a`, then all of the `b` it moves.
   - `reverse`, `length` and `is_empty` walk their operand whole.

   So the ill-typed word a prim reports never depends on its answer or its
   moves. The first ill-typed word halts with `HostFailure image`
   (`ill-typed`) before the prim computes, allocates or drops anything; the
   halted state's frames are choice 8's.

   *Amended to follow the spec (fix round 4).* This choice used to read `b`
   of `append` not at all and only the head cell of `is_empty`, where §9 named
   no extent. vm-spec `31aeaf2` and `5517f26` made every extent whole, and two
   of its new inspection controls, `inspect-append-b` and
   `inspect-is-empty`, failed here after the merge
   (.local/vm-core/logs/r5-runs-prefix.log). The mutants `append-b-unread` and
   `is-empty-reads-one-cell` restore the old reading; `eq-exits-early` and
   `move-prims-unread` pin two points this VM already read.

   The VM inspects at exactly §6's points, and nowhere else. A word that is an
   immediate is refused before any load through it (review round 6: `$scell` and
   `$finish` once tested it in the same `or` as the loads, which Wasm evaluates
   whole, and a scalar of about 2^25 or more trapped at a String cell or a Program's
   final word instead of halting `ill-typed`):

   | §6 point | vm.wat |
   |---|---|
   | a Case scrutinee | `$select`: `$num` for keys, a Nat or a Char; the tag check of an algebraic word |
   | the operand of Succ and of Chr | `$complete`: `$num`, before the `NatRange` test or any allocation |
   | prims 0–33, the four conversions included | `$prim`: `$num` on each operand, in operand order |
   | String prims 34–38 | `$seq`, `$append`, `$reverse` and `$prim` walk each String with `$slen` first |
   | an Enter's target | `$enter`: a request first, then its class, then its operand count (§7) |
   | every rendered word | `$describe`: `$num` or `$tagof`, each before the word's visit is charged (choice 6) |
   | a request's operand | `$serve` → `$utf8out`, whose `$slen` walks the whole String before the scalar check (D20) |
   | the final IO.OP, a Halt's code and message | `$finish`: the IO.OP check, `$num` on the code, then `$utf8out` on the message, all before `act` is dropped |

   A request is read first at every point above (`$request`, choice 17): `Unsupported vm effect`, whatever the type and before
   any state changes, but at a Case, whose Default takes it.

   A byte List's extent (§6, `File.write_bytes`) has no site here: vm-core
   refuses every foreign but `IO.print` at load (choice 2), so vm-io owes it,
   with the inspection controls §12 assigns to vm-io.
4. **`append` on the bump arena.** It writes its L cells as one block, at the
   addresses that allocating from the last character to the first would give.
   A heap too small for the block is reported before any of it is written.
   Sequential allocation would stop partway, so only the halted state's bump
   pointer can differ.
5. **Nat Case.** Selection reads the tag and allocates nothing. Only a
   selected Succ Branch makes the predecessor n − 1, after its Scope push, and
   moves it into its slot; a Default or a Zero arm makes none. SPEC §6.1 now
   states this (vm-spec D17). The VM used to make the predecessor before the
   push; `nat-pred-frames` and `nat-pred-heap` pin the order.
6. **Rendering bounds.** A visit is one rendered constructor application. A
   Nat word n counts n + 1 visits, one per layer of its logical view, and is
   spelled with its own type's Zero and Succ names. The 16 MiB bound applies
   to the tree text, separators included, after `Evaluated\ttype\ttag\t`.
   Both bounds are inclusive. SPEC §8 now states this reading (vm-spec
   `0e07562`), and its four display run controls pin it. A word is inspected
   before its visit is charged: an ill-typed word is no constructor, so it is
   no visit. Review round 6 found `$describe` charging first, so that the
   1,048,577th visit was `Exhausted` (display) where the word is ill-typed
   (`describe-order-1048576`; SPEC §6.3 says the same). A Book's describe
   domain has no `none`-typed field and no arrow (§8 step 5): such a result is
   `Unsupported invoke result-type` before any entry, and rows pin both classes.
7. **Invocation order.** Checks run in this order, which SPEC §8 now states
   whole (vm-spec D16):
   1. no IMAGE word: `arguments usage`;
   2. the image (§4);
   3. the shape its entry kind selects: a Book's `FN FUEL`, a Program's
      `FUEL --`, else `arguments usage`;
   4. FUEL, then each ordinal, as a decimal u32 word (`arguments
      expected-u32`): ASCII digits only, any number of leading zeros, at most
      2^32 - 1, never reduced; the reader stops at the first digit past the
      maximum, so a word of any length is read;
   5. a Book's walk, as `serializer.invocation` reads it:
      - the export (`invoke unknown-export`);
      - each live parameter in turn:
        - no ordinal left: `argument-arity`;
        - an arrow of either kind: `function-argument`;
        - an ordinal at or beyond the type's constructor count:
          `argument-range`. An opaque or `none` parameter has no
          constructors;
        - a constructor with a live field: `structured-argument`;
      - leftover ordinals (`argument-arity`);
      - the result type (`Unsupported invoke result-type`).

   Step 1 is the host's: without an IMAGE word there is no image to read.
   Steps 2–5 are §8's; the 13 argument controls and `invoke-words` pin them.
8. **Stops change nothing (SPEC §6.3).** A step that stops the machine, by a refusal, a halt or an exhaustion of any kind, has
   no post-state: the control stays pending, and `act`, the frames and `top`, every cell, the bump pointer, the counters and
   everything written or called are as the step found them. The one change a stop leaves is the debit of an Enter whose step 2 or 3 stopped (§7).
   Every check of a step comes before its first change, and where two would both stop it the earlier names the stop: a request
   (`Unsupported vm effect`), then a word's type (`ill-typed`), then the limits in the order of the row's substeps. `vm.wat` orders each
   row so:

   | Row | Its checks, then its changes |
   |---|---|
   | Return, top Gather | `$complete` reads the last operand from `val` (`$opnd`), inspects, tests NatRange and allocates the result; `$pop` then stores that operand and pops the frame. `$prim` takes its operands as words. A refusal leaves the Gather frame with its last slot 0 and its count one short. |
   | Eval Case | the scrutinee's inspection, then `$spare` for the Scope (kind 3), then the predecessor's cell (kind 2), then the push and the binds. A heap stop leaves no Scope (`nat-pred-heap`). |
   | Enter | a request as the target, its class and operand count, fuel; then `$debit`, `$tail` (a Call frame's room, kind 3) and `$alloc` (the Activation, kind 2); only then `$leave` (a tail entry's pops and release) and `$activate`. A stop after the debit leaves the pending Enter, its Scope frames and `act` (`tail-heap`). |
   | Return, top InvokeFunction | `$spare` for the 16 bytes of InvokeArgument on the region as the pop leaves it; then the pop and the push (`invoke-frames`). |
   | String prims | `$fit` for every cell of a result before the first is allocated, `append`'s block as before (`reverse-heap-short`, `show-heap-short`). |
   | Return, top Top | a Book's description (`$describe`: every word inspected and then charged, the text built in scratch) or the loop (`$serve` and `$finish`: an operand, an IO.OP, a Halt's code and message inspected, D20's scalar check) refuses before `act` is dropped or anything is written; each drops `act` once its checks have passed. |

   *Amended by the coordinator's ruling and vm-spec round 14.* This choice used to state a limit: Return to Gather popped the
   frame before `$complete` inspected the operands or tested NatRange, and Return to Top dropped `act` before it inspected an
   IO.OP or a Halt (vm-lockstep findings 1 and 2, 23 and 2 runs). Both are gone, and so is the Book's exemption (a description that
   stops no longer finds `act` dropped). `nat-pred-heap` is re-frozen: its `top` counted the Scope that §6.1 used to leave pushed.

   *What holds it.* The harness's `atomic` replay plays every run that ends in a stop to its last step and names what that step changed
   (registers, frame words, cells); the goldens, invocations, run and admitted controls, reference rows, admitted fuzz images, the
   lane and the dump and limited rows are held to none. The witness rows pin by hand what a replay cannot know absolutely, and
   eight mutants restore a half-done step (group `atomic`, `limited`).

   *What stays open.* A `memory.grow` that the host refuses traps (§5: HostFailure, no state to keep); `$utf8out` grows memory
   before D20's scan (choice 11, vm-io's); and there is no release, so the release's worklist and a tail entry's release-then-allocate
   (§6.3) wait for vm-rc.

   At zero fuel the pending Enter's registers are kept and the mode reads Halt. §7 asks that the Enter stay in the state, while §6 lists Halt
   as a control; vm-lockstep confirmed the reading (95 fuel stops).
9. **A `Halt` result.** Its message is converted to UTF-8 before the result
   is dropped.
10. **4 GiB.** A cell or an `append` block may end exactly at 4 GiB: §5 stops
    only a cell that would end beyond the maximum. The bump pointer is 64-bit,
    so it reaches 2^32 without wrapping; every cell's own address stays below
    4 GiB. The heap is then full: any later cell, and describe's text
    (choice 12), is `Exhausted` kind 2 (heap), and a Program that allocates
    nothing more completes. Review round 4 found the VM trapping
    (`HostFailure io trap`) at such a cell, with a reason here that no host grows
    memory that far. `ceiling-top` refutes that reason: its run grows memory to
    all 65,536 pages. The trap came from the i32 bump pointer.
11. **Output before D20's check (open, vm-io).** `$utf8out` grows memory by 4
    bytes per Char for the whole String, then scans and encodes. Growth past
    4 GiB fails in `memory.grow`, which traps (`HostFailure io trap`). So a
    `print` or `Halt` message whose 4-byte bound crosses 4 GiB traps before the
    scan, even when its UTF-8 would fit and even if it holds a non-scalar Char.
    Since choice 10 this includes every nonempty String at a bump pointer of
    exactly 2^32; an empty one needs no memory. Since choice 15 the grow first
    steps memory to 4 GiB (untouched pages) and traps at the exact grow that
    follows. §10 orders neither the
    growth nor the scan, and the growth is not bounded by the heap limit. §11
    fails a trap where the outcome is a budget, so vm-io, which owns the effect
    path, must turn this into `Exhausted` kind 2 (heap), as describe does
    (choice 12), and order it against D20's check.
12. **Describe at 4 GiB.** Describe's text starts at the bump pointer and has
    no reserved window. Text ending beyond 4 GiB stops with `Exhausted` kind 2
    (heap), the outcome §5 gives an allocation beyond the maximum, because the
    text is memory the VM needs. The display bound is checked first. Text ending
    exactly at 4 GiB is printed. The `ceiling` fixtures pin both cases.
13. **Chr reads its operand.** Completing `Chr{w}` inspects `w` as a U32
    (§6), as Nat's Succ does, and then yields the word itself; a Big code
    stays the same cell. A laundered non-scalar operand is `HostFailure image`
    (`ill-typed`) there, even when the Char is never used. Review round 3
    found the VM storing the word unread and finishing where the reference
    halts; this choice followed the reference evaluation's `construct` and
    vm-model (`5b7ea75`) while §6 did not name Construct. §6 now names the
    Succ and Chr operand (vm-spec `31aeaf2`), and `inspect-chr` freezes it.
    The `reference` fixtures compare `chr-unchecked`, `chr-closure` and the
    control `chr-big-code` with `evaluate.book`.
14. **§4's resource limits (settled by SPEC §4, vm-spec DECISIONS 19).** An
    image past a limit of version 1 is `Exhausted` kind 2 with the limit as its
    cause, never a malformed image. Each limit is checked where its count is
    read, after the count's own structure and before anything it governs, in
    the order §4's table gives:

    | §4 limit, inclusive | cause | vm.wat |
    |---|---|---|
    | 4,194,304 words (16 MiB), first, even when the image is also malformed | `image-size` | `$read_image`, after each 1 MiB chunk, before the image's length is known |
    | 1,048,576 records per table | `records` | `$decode`, each section: `$limit` once the count is fitted to the words that remain at two per record (`record-count`), before any record |
    | a Closure's `slots`, 65,536 | `slots` | `$decode`'s node shapes: `$limit` once the record's length is known (`node-length`) |
    | a function's live arity, 4,096, then its `slots`, 65,536 | `arity`, `slots` | `$decode`'s function loop: `$limit` once the record's length holds its parameters (`function-record`), before its root, name and parameter types |

    `$limit` is the one test (`count > max`, then `$exhaust` kind 2 with the
    cause), so every limit is inclusive; the size check is its inline twin,
    because it must run while the image is still being read. A count the
    structure cannot hold (`record-count`, `function-record`) is malformed and
    is checked first. The validator checks no limit: `$check` used to refuse an
    arity above 4,096 or `slots` above 65,536 as `limits`, a `HostFailure
    image` that §4 does not give, and a Closure's `slots` had no limit at all.
    Decode has all of them for every function before validation starts. The
    gate names each verdict in the reference's words (`Exhausted 2 arity`), so a
    limit reported as malformed differs from it.
15. **Memory grows in 16 MiB steps (review round 1).** `$grow`, the one site
    behind `$alloc`, `$append`, `$take`, describe's text, `$utf8out` and
    `knot_alloc`, covers `end` by growing memory to the next 16 MiB boundary at
    or above it, at most to 4 GiB. A host that refuses that step is asked for
    exactly the pages `end` needs; only a refusal of that traps
    (`HostFailure io trap`), as §5 requires of a host that refuses growth below
    the maximum. §5 leaves the timing of `memory.grow` free ("need not
    agree"), so only time and the test build's count of grows depend on it:
    values, classification, `calls` and the bump pointer are as before, and the
    pages beyond the bump are untouched, so a step commits nothing more.

    V8 pays each `memory.grow` in the size of the memory. The VM used to grow by
    exactly the pages a cell needed, one grow per 4,096 16-byte cells, and a
    stream of small cells slowed down superlinearly. Review round 1 measured a
    tail loop whose every entry allocates one 16-byte Activation
    (`core/loop-cells`): 1.4, 4.9 and 21.8 s at 16M, 32M and 64M entries, against
    0.4, 0.7 and 1.4 s now, and 22 min 45 s to reach §5's `Exhausted` kind 2
    (heap) at the D19 ceiling, against 5.9 s (4.3 GB resident) now. §11 counts a
    timeout as neither Exhausted nor agreement, so a heap of small cells that
    stopped only after such a time was unreachable in practice, and a large live
    set (vm-rc) would pay it too. No earlier row saw it: the ceiling rows reach
    4 GiB through `dbl`'s append blocks, one grow each.

    Near a host's refusal every further page costs two calls, the refused step
    and the exact grow, for fewer than 256 pages (`loop-refused` counts 202);
    where the host grants the step there is one call per 16 MiB (254 up to 4 GiB
    on the real host, 16 to a 256 MiB heap).

16. **The validator's scope tables grow (review round 1 of round 6).** `$check`
    keeps each slot's type (`sc`, a word) and use mark (`us`, a byte) at an absolute
    scope index: a function's slots start at 0 and a Closure's at its enclosing
    unit's base plus the depth at the Closure, so an index is the sum of the depths
    of the Closures around it. No image size bounds that sum. A Branch binds every
    field of its constructor, whose one record serves every Case that matches it,
    so a few hundred words of image reach depths of thousands, and each nested
    Closure adds the depth it sits at. The tables held W + 4200 indices, and a
    slot past them fell on the next table (`us`, then the fits memo): the
    reviewer's images (`fixtures.json` section `scope`) were refused as
    `capture-use` (`valid-nest-1000-60-60`, 3,600,060 indices), trapped
    (`valid-nest-20000-3-200`, 12,000,200) and, for a malformed one, accepted and
    run (`falseaccept-100-60`: slot 5,394 = W + 4200 landed on the use marks,
    where the mark of an earlier Reference made it read as its declared type).

    `$holdscope` holds `n` indices. At an `n` past the tables' `scCap` it takes
    fresh scratch for both tables, twice as large or `n` if that is more, copies
    what the old ones held and leaves them (scratch has no free). `$setscope`
    calls it with `s + 1` before every write, and it is the one writer: a read or
    a mark of an index comes after the slot's own write (every slot below a depth
    was bound), and a write is never past the tables' size by more than the slot
    just before it. So no table can be indexed past its size, and no table can
    reach another. The first call, from `$validate`, holds W + 4200 as before, so
    the scratch and every row of the gate are as they were for an image that does
    not pass it. Doubling makes the copies sum to less than the last table; tables
    that grew by one index at a time would take gigabytes (the rows bound the test
    build's `memory.grow` count at boot's one). A doubling that `$take` cannot
    place, past the 4 GiB that scratch may reach, stops the image as `Exhausted`
    kind 2, cause `heap`, as it does any table of the loader; the guard on a table
    of 2^30 indices is unreachable, because the earlier tables stay in scratch and
    `$take` stops the image before one passes 2^29.

    Three consequences.
    - A valid image can need more scope indices than scratch holds: the sum of the
      depths of the units along one chain of Closures, each up to §4's 65,536
      `slots`, over as many Closures as the image's 16 MiB hold. The VM then stops it
      `Exhausted` kind 2 (heap) where the reference codec admits it: `exhausted-32767-2-8000`,
      8,000 units of 65,535 slots (400,863 words, 524,280,000 indices, tables of at
      least 8.29 GB of scratch), stops in 2 s, 4.2 GB resident, on the real host. §4 states
      no limit for it (a finding below); the review allowed the stop.
    - The review also proposed refusing a unit as soon as its depth passes its
      declared `slots`, "since exactness already requires equality". That is not
      taken. The reference codec checks a unit's `slots` when the unit ends, after its
      body, so a defect in the body after that depth is the first defect, and the
      first defect is what the gate compares (SPEC §4, and `$check`'s own order). `excess-function` and
      `excess-closure` are such units (`slots` 0, a Let, then a Reference to slot 5):
      the reference codec reports `slot 5 beyond depth 1`, not the slots. A validator that
      refused early would name the slots (mutant `scope-slots-refused-early`,
      killed by both). The tables grow instead.
    - "Allocate them last in scratch, so they can extend" is met by moving, not
      extending: the fits memo grows by `$take` while validation runs, so nothing can be
      last, and a table that moves keeps no neighbour to run into.
    - The tables are not sized up front from the image. An exact size is what `$check`
      itself reaches, and a bound needs a walk that repeats its rules. A bound from the
      declared `slots` is words the image chooses freely: each Closure would cost 65,536
      indices whatever its body reaches, and the VM would stop as `Exhausted` images the
      reference codec refuses for a defect. The tables hold what validation has reached.

    The fix changes `vm.wat`, so `vm.wasm` is re-pinned: sha256 `407cb872…a7a2`
    (19,697 bytes; was `41ca972b…cddc`, 19,581). The 21 lines it adds sit above every
    function of the study, whose survivors' names moved by 21.

17. **A request is a value (D22, D23, D24; SPEC §5 class 5, §6, §7, §8).** An Action applied to its continuation `k` builds a
    request, a class-5 cell `[foreign, operand…, k]`, and performs nothing (`$enter`'s Action branch): no operand is read, no foreign id
    checked, no host called, and the entry that builds it pays its debit. A request is inert, and every read meets it first
    (`$request`) and stops `Unsupported vm effect` (the reason code `effect`; D4: never Invalid): `$num`, `$tagof`, `$scell`, an Enter's
    target before its operand count and its debit, and so describe's result and fields, a prim's operand and a String's tail. A Let, a
    Reference, a Construct, a Foreign, a capture and an operand move a request unread, so it can be stored, passed and dropped, and a
    dropped request is no effect. One read takes a request without refusing it (D24): a Case matches no row of a request in either mode, so
    `$select` takes its Default, unread and binding nothing, at any scrutinee type, and refuses one only where it has no Default.
    Only Top's loop performs one (`$serve`), the one a run returns to phase 3: it reads the operand whole and makes D20's scalar check
    (`$utf8out`), drops `act`, calls the host and enters `k` with IO.print's answer, the Unit immediate, pending as an Enter, the phase
    still 3, so the loop is a loop and frames do not accumulate across effects. Its step is no entry and pays nothing. A Book has no
    loop (D22): it loads whatever foreign it holds and stops `Unsupported vm effect` where a read meets its request (`book-args`),
    while a Program that names another foreign than IO.print is still refused at load (choice 2). The harness counts host calls for
    requests (`effects`): every `print`, less the one that describes a completed Book. The audit reads class 5 (its edges are the
    operands and `k`, not the foreign word).

## Findings for the spec owner

- **A chain of Closures has no §4 limit on its scope depth (open).** §4 limits one
  unit's `slots` (65,536) and no sum. The validator's scope tables need one index per
  slot along a chain of nested Closures (choice 16), so a valid image of 16 MiB can need
  more indices than the 4 GiB of scratch holds, and the VM stops it `Exhausted` kind 2
  (heap), a stop no §4 row names, where the reference codec admits it. A limit on the
  sum of the `slots` of a chain of Closures, or on their nesting, with its own cause (D16),
  would make it a §4 limit that both sides give alike.

- **String constants above U+10FFFF (resolved).** At the branch base,
  `serializer.decode` refused a code above `0x10FFFF`, against §2, and vm-core
  refused too. vm-spec settled it in the codec (`4e3642f`): plans spell a String
  as its code list, and every u32 code is kept. vm-core now admits every code.
  `$materialize` already built Big code cells, so golden `string-beyond-unicode`
  and the seven code-list controls run unchanged. vm-model should admit them too.
- **Deep images.** The reference codec's `decode` and `encode` recurse, so they
  fail on images nested deeper than Python's recursion limit. `check-core.py`
  lays out its 200,000-deep image iteratively. At depth 40 that layout is
  checked equal to `serializer.encode`.
- **`serializer.decode` allocates from a count before it checks it (open,
  vm-spec).** The type loop builds `'constructors': [None] * r[3]` before
  `expect != len(ctors)` ties the counts to the constructor records. Nine of the
  gate's 3,720 fuzz images reach it with a count near 2^32 (`char-eq-38`,
  `erased-let-26`, `let-3`, `nat-add-21`, `print-non-scalar-24`,
  `result-u32-field-28`, `string-empty-9`, `string-ne-length-33` and
  `value-on-26`). Each makes the reference allocate a list of about 32 GB for 2
  to 5 s and then refuse the image (`constructor count` for five, `constructor
  grouping` for four), so the gate's process peaks at about 35 GB, though no
  limit-word image reaches it.

  The gate used to record such a crash of the reference and go on. On a host
  that could not allocate the list it would have compared fewer images than it
  reported. It now fails on any crash (`verdict`, both corpora), and
  `crash_fails` shows on every run that the guard fires. The allocation itself
  is in vm-spec's file. Making the slots after the `constructor count` check
  keeps every verdict (the counts then sum to the number of constructor
  records, so the lists fit the image):

  ```python
              plan_types.append({'kind': kind, 'name': text(r[1]), 'constructors': r[3]})
      ...
      if expect != len(ctors):
          raise Malformed('constructor count')
      for t in plan_types:  # the counts now sum to len(ctors), so the slots fit the image
          if t['kind'] == 'data':
              t['constructors'] = [None] * t['constructors']
  ```

  This was checked on the 3,720 fuzz and 7,741 limit-word images: the real
  original on the nine above, a lazy stand-in for their list on the rest, and
  the patched codec agree on every verdict, and the two corpora are generated
  in 1.2 s and 42 MiB instead of 35 GB.
- **Ambiguities (resolved).** Choice 8's zero-fuel state was a real ambiguity in §6–§7;
  vm-lockstep confirmed the reading against the model (95 fuel stops, the pending Enter,
  its target and operands alike) and §7 keeps the Enter pending. Its Gather frame at an
  ill-typed halt was a stated limit that no control observed: SPEC §6.3 (round 14) rules
  that a stop changes nothing, and choice 8 follows it. SPEC §8 has settled choice 6, and
  §6.1 choice 5 (D17), which round 14 reverses at a heap stop (no Scope is left pushed).
- **Chr's inspection (choice 13, resolved).** §6's Inspection list now names
  the operand of a Chr construction (vm-spec `31aeaf2`).
- **Other readings where the reference evaluation differs.** These are not
  review findings, but lockstep needs one reading of each. They came from
  review round 3's probes, re-run against this VM:
  - `append`'s `b` and `is_empty` (resolved). The VM read `b` not at all and
    `is_empty` only at its head, where `evaluate.py` reads both whole Strings.
    §9 now gives every extent (vm-spec DECISIONS 18); the VM follows it
    (choice 3). vm-spec's controls `inspect-append-b` and `inspect-is-empty`
    freeze both points, and the VM halts `ill-typed` at each.
  - A `Halt` message holding a surrogate (resolved). The VM refuses it as `HostFailure io
    abi`: it treats the message as an outgoing String under §10, which SPEC §8 now
    says (DECISIONS entry 24), and the reference's `program` refuses it too
    (`halt-surrogate`, `halt-scalar`).
  vm-io owns the effect path.

## Evidence (gate `vm-core`)

- **Goldens.** All 111 through the real host, equal to `vm-expected.json`. The
  test build confirms every Exhausted, Unsupported and HostFailure cause in the
  VM's own outcome registers, and audits the state at all 2,683 transitions. Every
  run that ends cleanly, here and in every row below, ends in control `Halt`
  (mode 3), which the gate's `observed_wrong` requires of every row of every group.
  For D20's `print-non-scalar`, `print-non-scalar-mid`,
  `print-non-scalar-wide` and `print-non-scalar-second`, the registers show
  that the VM refused before its
  host call. The real host would refuse the same bytes with the same
  `HostFailure io abi` line.
- **Book invocations.** The 44 that `vm-expected.json` freezes for
  `invoke-args`, `invoke-arrow` and `invoke-words` are checked through the
  real host and through the test build's registers. Together they cover every
  cause of §8's walk and its decimal words.
- **Argument controls.** check-spec.py's 13 (`argument_controls`), through
  the real host: each refusal equals its frozen verdict (`usage` before the
  lookup and before a Program's FUEL, `expected-u32`, and a bad magic word
  refused whatever the words), and each admitted one runs as the reference
  evaluation runs it, a 4,401-character ordinal of leading zeros among them. The
  host shows only the refusal's line, so the three fixture runs of the `usage`
  refusal (`book-usage`, `program-usage`, `program-separator`) also freeze the VM's
  own class and cause registers (`dumps`: HostFailure, `usage`, no entry): a
  refusal reported as another class would print the same line.
- **Admitted controls.** vm-spec's eight admitted plan controls, its admitted
  limit control and seven code-list controls load. They run as `fixtures.json`
  froze them by literal review, and vm-spec's reference evaluation
  (`evaluate.book`) gives each the same run and `calls`:
  - `arity-at-limit`, `value-on` beside an unused function of 4,096
    parameters, prints `On{}` after 1 call;
  - `list-head-match` prints `True{}`;
  - the two `case-none-*` controls fail `ill-typed` after boot;
  - `first-code`, `first-code-none-case` and `key-arms-none`, whose arms fit
    their Case (§3), print `True{}` after 3 calls;
  - the two name controls (a type named with each length of UTF-8, and with every
    edge of a length) print `On{}` after 1 call;
  - every code list compares `False{}`.
- **Run controls.** All 138 that check-spec.py freezes (`run_controls`), as
  many as SPEC §12 states, load, and each runs to its frozen exit, output,
  outcome, `calls` and, where it freezes them, host calls (`effects`). The families
  below are the first 41; later rounds added the D22 to D24 controls (a request is
  built by an Action's second application and performed only by Top's loop, so a
  dropped or stored request has no effect, a Case takes its Default over one and
  otherwise stops `Unsupported vm effect`, and a Book stops there where a read
  meets one) and the atomic controls of SPEC §6.3, whose stops the harness replays
  to their last step (below):
  - `arrow-through-identity` prints `On{}` after 3 calls;
  - `u32-file-alias` prints `Off{}` after 1;
  - five others fail `ill-typed` at §7's operand check;
  - the four display controls meet each of §8's inclusive bounds and pass it
    by one. `display-visits-at-bound` and `display-bytes-at-bound` print
    lines frozen by SHA-256, the latter with a 15-byte successor name. The
    other two are `Exhausted` kind 2 (`display`);
  - `nat-default-big` takes its Nat Case's Default on 2^31 + 1: `On{}`;
  - the eleven fuel controls (vm-spec D15) run at their frozen fuel and meet
    §7's boundary: each completes at its `calls`, and one unit less stops the
    last entry with `Exhausted` kind 1 after one call fewer. At 4,
    `foreign-print` has written `vm` when `k`'s entry stops; at 3 its Action's
    second application stops before the effect;
  - the eighteen inspection controls (vm-spec DECISIONS 18) each halt
    `HostFailure image` (`ill-typed`) at one of §6's points (choice 3): Chr's
    and Succ's operand after 2 calls; each conversion's moved word, `append`'s
    `b` and `a`'s Chars, `length` and `reverse`'s Chars, `is_empty` past its
    head, and `eq` past a differing code or past either end after 3; a
    Program's Halt code or message after 4; and a print whose String holds a
    closure after a surrogate after 5, having written nothing, so the cause is
    not `io abi`.

  §7 puts the operand check before the fuel test. Each control without its own
  fuel is therefore run again with exactly its `calls` of fuel, to the same
  outcome, and two fuel controls meet fuel 0 at an ill-typed Enter, so an
  ill-typed Enter is refused at fuel 0 too. The VM's checks were already in place; this merge
  adds the gate's evidence for them. An Action's check (`nops > 1`) cannot fail,
  because an Invoke and a Program phase pass at most one operand. Its removal
  is an equivalent mutant, so no mutant is listed for it.
- **Reference rows.** `chr-unchecked` (review round 3's repro),
  `chr-closure` and the control `chr-big-code` (choice 13), and
  `nat-pred-big` (choice 5). Each frozen run is literal review, and
  `evaluate.book` and the VM must both give it: two are `ill-typed` after 2
  calls, the Chr control prints `True{}`, and `nat-pred-big` prints `On{}`.
- **Seeded rows ([core/seeded.json](core/seeded.json)).** Twenty-four Books whose
  expected results the pinned seed's native lane fixed before any VM ran them (D7;
  `python3 vm/check-core.py --freeze` writes the file): each has a model tree that
  the seed's bytes, the reference evaluation and the VM must all give, and the
  gate runs the seed again and requires the frozen bytes (`source`, `image` and
  `seed` are pinned by hash and value). Review round 6 found that Case arm
  selection was pinned only at trivial shapes (one or two keys, a query at a key
  or one miss) and that describe was pinned only up to two fields; an inverted
  key comparison, a flipped tag Default and a describe with a wrong separator
  passed the whole gate.
  - *Key Cases.* U32 and Char Cases of 3 and 5 keys, queried below the first key,
    at the first, between two keys, at a middle key, at the last and above it.
    The boundary rows put keys and scrutinees at 2^30, 2^31 and 2^32-1, each
    query once as a literal and once computed by `U32.add` (a fresh Big cell from
    2^31): one key set ends at 2^32-1, one ends below it, so "above the last"
    includes 2^32-1. Every arm and the Default answer a different constructor
    (keys + 1 of them), so no neighbour's arm can stand in for another's. The
    Char rows use scalar keys and computed non-scalar scrutinees
    (`Char.from_u32`; D20: only a Tri is output). `keys-char-nonscalar`, whose keys
    are non-scalar codes the seed cannot spell, is by literal review.
  - *Wide constructors.* 3, 5 and 9 fields, flat and first and last inside one of
    one field more, a different constructor at each position, so a separator, a
    closing brace or an offset that fails from the third field on changes the text.
  - *Tag Defaults.* Three tag Cases on a type with two nullary and two fielded
    constructors: one names all four, two default one of each kind, so a Default
    is reached by an immediate and by an Object.
  - *Inspection edges, by literal review* (the seed types every program): an
    immediate of tag 2 at a two-constructor type (with a Default, without one, and
    at a one-constructor type), an immediate naming a constructor with fields (as a
    Branch and as the Default), a scalar operand that is an Action, a Book
    result whose tag equals its type's constructor count (these two need a type
    record after the result's constructors to differ from a refusal), a String
    operand that is a large scalar's immediate word, and an Action laundered to a
    String whose type index is its foreign id.
- **Differential lane ([lane.py](lane.py), [core/lane.json](core/lane.json)).**
  2,768 rows from a fixed SplitMix64 stream (seed 20260929, integer arithmetic
  only, so no row depends on the Python version): 2,000 random programs over small
  data types, closures, Nat recursion, U32 key Cases and every U32 and Nat prim,
  emitted as Bend and as a plan (every second one *laundered*: its values pass
  through `none`-typed identities, so a Case scrutinizes a word whose type only the
  run can check); 200 random key Cases; 76 prim sweeps over boundary operands (a
  model, not a VM, gives each answer); 54 prints and 48 Halts at the UTF-8 length
  boundaries and the exit-code residues; 60 type and tag indices of 10 to 1,000
  and 10 Nat renderings; two display rows at the visit bound; the seeded rows; and
  the inspection matrix below. Each runs through the test build and the
  production module and through `vm/evaluate.py`; stdout, exit, stderr, outcome,
  cause and calls must be equal, and a row with a model tree must give it too.
  The seeded rows and the sample (108 rows) also run on the real host. An 84-row
  sample (40 programs, 12 key Cases, 12 sweeps, 10 prints, 10 Halts, spread
  evenly through their families) runs through the seed's native lane again: a
  Book's tree must be the seed's and a Program's stdout, stderr and exit its own,
  and the seed's bytes are frozen in `lane.json`. Two readings
  stand in for what the reference evaluation does not model, both this VM's
  documented behaviour: an image with a foreign leaf other than IO.print is
  `Unsupported vm foreign` before any entry (choice 2), and a Halt message with a
  non-scalar Char is refused as `io abi` (open item below). The inspection matrix
  below puts a request (an Action applied to its continuation) at every place a
  word is read, and the golden and run controls of D22 to D24 build, store, drop
  and perform requests.
- **Inspection matrix (lane family `inspection`, 294 rows).** Every kind of word at
  every place section 6 inspects one, each Book or Program passing a producer's
  word through `id: none -> none` to a consumer. Producers: scalars (small, the
  largest immediate, Big), nullary constructors, an Object of another type, a
  Closure, an Action, a request, the empty String, a String cell and a Nat. Consumers: a
  scalar, Char and String prim operand, a String's head, tail and second operand,
  a Case by tag (Nat, a dense ADT, one with a Default) and by key, the operand of
  Succ and of Chr, describe of a result and of a field, an Invoke's target (never an
  Action: applying it would perform its effect in a Book, D22), and a Program's
  final word, Halt code, Halt message and print operand. The reference evaluation
  says which words each admits. **The matrix found a defect** in the VM of
  `2e0c9b1`: on 15 rows it trapped (`HostFailure io trap`) where §6 gives
  `HostFailure image` (ill-typed). `$scell` and `$finish` tested `word & 1` in the
  same `i32.or` as the loads through the word, and Wasm evaluates both operands,
  so an odd word past the end of the memory then in use (an immediate's address;
  48 MiB at the least, so a scalar from about 2^25 up) faulted before its test
  could refuse it: such a scalar used as a String cell, as a Program's final word
  or as a Halt message. The rows were
  frozen before the fix (D7; `.local/vm-core/logs/r8-scell-prefix.log` shows the
  gate failing on them at that commit), and the fix refuses an immediate before any
  load through it. It changes `vm.wat`, so `vm.wasm` is re-pinned:
  sha256 `41ca972b…cddc` (19,581 bytes; was `9c483def…817c`, 19,569).
- **Every admitted image through both.** The 93 goldens, the 44 invocations, the
  14 admitted controls, the 71 fuel-and-call runs of the 41 run controls and the
  289 mutated goldens the reference codec admits (511 in all) are also compared
  with the reference evaluation, in the same fields.
- **[core/fixtures.json](core/fixtures.json).** Literal review, frozen before
  any run:
  - the 250,000-deep non-tail recursion, with 500,003 entries and seven yields
    at multiples of 65,536;
  - a 400,000-deep one, which exhausts the 16 MiB frame region;
  - a yield immediately after an Action's effect (`q` printed once);
  - exact fuel boundaries, rendering and both display bounds;
  - an ill-typed flow through a `none` parameter;
  - the Unsupported foreign leaf, and the invocation errors;
  - `nat-pred-big` under a 24-byte frame region and a 48-byte heap (choice 5):
    the Case's Scope does not fit, so the predecessor is never made (bump
    H0 + 48); or the Scope is pushed and the predecessor's Big is `Exhausted`
    kind 2 (top F0 + 36). The heap row's bump is also where §5's model
    (`ceiling_run`) stops under that heap. Unlike the rows above, these were
    not frozen untouched: a draft left out the cells' 2 header words, and a
    run of the pre-fix VM before commit exposed it. They were rederived from
    §5's cell rule and §6's 3-word frames; `ceiling_run` checks the heap row's
    bump, while both `top` values and the frames row's bump rest on that
    hand derivation (80bd5cf).
- **Study rows (round 7).** The mutant study (below) left survivors that were holes in the rows, not
  equal mutants. Each is now a frozen row, derived by hand from §5 to §8 before its image was run (a probe
  of the VM then agreed on every value, and none was changed), and derived again by the gate:
  - `closure-let` (a `reference` row): a Closure whose body binds a slot after its capture and its live
    argument. §7 gives the Activation a depth equal to the bound count, so the Let binds slot 2; a depth
    that left out the live argument reads the slot back as 0. `Succ{Succ{Zero{}}}` after 2 entries, which
    the reference evaluation gives too;
  - the room of a step at its exact fit and one byte short (`limited` rows; section 5's model gives the
    bump pointer of each fit row, and the frames listed give its `top`): a Case's Scope
    (`nat-pred-frames-fit` at 36 bytes, `nat-pred-frames-11` at 35), a Call frame (`call-frames-fit` at 40,
    `call-frames-15` at 39), a tail loop entered below a Call frame (`tail-call-fit` at 68, which a machine
    that took a Call frame per tail entry would overflow by 16 bytes an iteration, and `tail-call-short`
    at 67), and `U32.show`'s digits (`show-9-fit`: one digit, where a count in base 9 asks for two;
    `show-10-short`: two, where a count in base 11 asks for one and stops after making it);
  - `arrow-second-field` (describe `domain`): a Pair whose second field is an arrow, which a walk that
    skips or stops at a field misses (the codec's `undescribable` says it is outside the domain);
  - `erased-arrow-parameter`, `unknown-export-constructor` and `unknown-export-type` (`runs`, checked
    against the codec's `arguments`): an erased arrow is a function argument like a live one, and the
    name of a constructor or a type is no function's. A search that reads one entry past the function
    table finds there, for an image without constants, the record of the image's second name, so it
    takes `Off` for a function;
  - the class and cause registers of `book-usage`, `program-usage` and `program-separator` (`dumps`);
  - `memory-end-closure` (group `memory-end`): the 32-byte Activation of a Closure that its four
    captures fill, with no slot beside them, is the last cell and ends at 48 MiB. A capture loop that runs
    one time too many writes one word past it, and traps only there.

  Two changes of the gate came with them: `ceiling_run`, the section 5 model, no longer needs a
  `representation` table (a Book of constructors alone names none) and cases on a nullary immediate.
- **Ceiling.** Ten images whose bump pointer ends near or exactly at 4 GiB, at
  most two at a time. Each dump pins the bump pointer, which keeps the image in
  its band:
  - review round 2's three images, where a worklist based in i32 arithmetic
    16 MiB above the text wrapped into the image: `On{}`;
  - `ceiling-band`, just below that wrap: `B1{B1{B0{}}}`;
  - `ceiling-top`, whose text ends exactly at 4 GiB;
  - `ceiling-over`, 16 bytes beyond it: `Exhausted` kind 2 (heap);
  - review round 4's `ceiling-top32`, whose last Object ends exactly at
    4 GiB (bump 2^32), and describe's text then cannot fit: `Exhausted` kind 2
    (heap). Its control `ceiling-cell-over`, 16 bytes higher, stops at the
    Object itself, with the bump pointer unchanged;
  - `ceiling-append-top`, whose `append` block ends exactly at 4 GiB:
    `Exhausted` kind 2 (heap) at describe;
  - `ceiling-program-top`, a Program whose `Emit{Unit}` ends exactly at
    4 GiB: exit 0, no output, `Completed`.

  **Provenance.** `c9869ef` chose the first six plans' fill counts by
  measuring the pre-fix VM's bump pointer, and pinned `bump` from that
  measurement. It called the pins literal review, which they were not (review
  round 3). The gate now derives every row before the VM runs. `ceiling_run`
  sums §5's cell sizes over the plan:
  - H0 from the image length;
  - the materialized pool, then a Program's terminal continuation;
  - an Activation per entry, a function's or a Closure node's;
  - Objects, Closures, Big U32 results, `append`'s block and the terminal
    `Emit` (choices 1, 4 and 5).

  A cell that would end beyond 4 GiB stops the model with `Exhausted` kind 2
  (heap) and the bump pointer unchanged; one ending exactly there is
  allocated. `ceiling_expectation` then completes a Program at its `Emit`, or
  starts a Book's text at the bump pointer (choice 12). The frozen `expect` and
  `dump` must equal the derivation, which agrees with all six measured pins.
  The first six rows skipped the one point where the pre-fix VM and the
  derivation disagreed, a heap ending exactly at 2^32 (review round 4). Three
  round-4 rows sit on it and the fourth is their control; all four took their
  fill counts from the model alone, before any VM ran them. The reference
  evaluation (`evaluate.program`) completes `ceiling-program-top`'s plan with
  every Nat literal of `main` (each `dbl` depth and both fill counts) set to 3,
  with exit 0 and no output after 56 calls. That check was run by hand
  (d4d33cc, and again in review round 4); the gate does not repeat it. So
  each row's outcome, on either side of 4 GiB and at
  it, follows from §5 and choice 12, not from a VM. Each row's `basis` records
  the arithmetic.
- **Scope tables (choice 16; [scope.py](scope.py), `fixtures.json` section `scope`).**
  The validator's tables of slot types and use marks began at W + 4200 indices. A
  slot sits at the sum of the depths of the Closures around it, and one wide
  constructor serves every Case, so the reviewer's images reached 3.6 and 12 million
  indices from a few dozen thousand words. Twenty-four rows, each frozen before the VM
  changed (D7) with its words, `need` (the indices validation holds, from the plan
  alone), SHA-256, the reference codec's verdict and the reference evaluation's run,
  which the gate derives again:
  - the reviewer's four saved images, rebuilt byte for byte: `valid-nest-1000-60-60`
    and `valid-nest-20000-3-200` (valid: refused `capture-use` and a trap before),
    `falseaccept-100-60` (refused `reference-type`: accepted and run before, its slot
    W + 4200 on a use mark) and its control `control-100-60-target-5395`;
  - `edge-t0` to `edge-t3`: a `chain` of nested Cases over a constructor whose
    fields cycle four types, so that a slot read after a doubling shows its type was
    carried over (type 0 is also what an uncopied table reads); its `need` is one
    short of, exactly at, and one past the tables' size after 0, 1, 2 and 3 doublings
    (`tuned` sets W with an unused constructor's words and `need` with Lets), with
    references at the parameter, the first slots, the last two and below, at and above
    each size; each `-past` row has a `-wrong` twin, refused `reference-type` at the
    deepest slot;
  - `nest-mark`, `nest-capture`, `nest-unused`: a Closure whose capture sits where the
    tables grow, at its own slot or just after its use mark (which a doubling must
    carry), and one with an unused second capture;
  - `nest-32767-2-20`, 20 units of 65,535 slots, and `exhausted-32767-2-8000`, 8,000
    of them: valid, and needing 8.29 GB of tables in scratch, so `Exhausted` kind 2
    (heap) and no trap (the reference codec is not run on it; the frozen stop is
    `scope.scratch`'s arithmetic);
  - `excess-function`, `excess-closure`: see choice 16.

  `at_most` bounds the test build's `memory.grow` count at boot's one on the `edge`
  and `nest-` rows, whose scratch (under 20 * need + 64 * W + 64 KiB, about 2 MB)
  boot's 48 MiB holds; tables that grew by one index at a time take gigabytes.
  Then a corpus of 300 (seed 20260930, [scope.py](scope.py)`.corpus`): `chain` and
  `nest` shapes with `need` at, just short of and just past a table size after 0 to 3
  doublings, typed or untyped fields, one to six references at the edges of those
  sizes (some at another type, some past the depth), one or two captures, and, in
  two rows of three, one small change (`poke`: a slot, a declared type, a Case's
  slot, a Branch's first slot or field count, a Closure's `slots` or a capture, a
  function's `slots`). Each is judged by the reference codec and by the VM, in the
  test build and in `vm.wasm`: 106 admitted and 194 refused with eight different first
  defects, 126 of them past the first size, and none differs. The unchanged VM
  differed on 13 of the 24 rows and 30 of the 300 (.local/vm-core/logs/r10-scope-prefix.log,
  r10-corpus-prefix.log).
- **Growth (choice 15).** Three rows on `core/loop-cells` (`loop() = call loop`,
  `main() = call loop`, review round 1's probe byte for byte), each stop derived
  from §5 and §7 in closed form (`loop_stop`, which agrees with the
  entry-by-entry `ceiling_run` at a 1 MiB heap) and frozen before the policy
  changed:
  - `loop-256mib`, a heap lowered to 256 MiB: `Exhausted` kind 2 (heap) after
    16,777,217 calls (main's entry and each of `loop`'s, debited before its
    16-byte Activation) with bump 285,278,208, in at most 24 `memory.grow` calls
    of the test build. The VM of `dcc7c09` made 3,840;
  - `loop-4gib`, the full heap through the real host: `Exhausted io memory`
    after 267,382,785 calls with bump 2^32, the last Activation ending exactly at
    4 GiB, within the 120 s guard. The VM of `dcc7c09` overran the guard;
  - `loop-refused`, a host that refuses growth beyond 4,700 pages
    (`node --wasm-max-mem-pages=4700`, 293.75 MiB, not a multiple of 16 MiB):
    §5's HostFailure, `HostFailure io trap` on the real host, at bump
    308,019,200 after 18,198,529 calls, the cap. A VM whose refused step traps
    stops 5.75 MiB lower.
- **Memory end (`fixtures.json` section `memory-end`).** Boot grows memory once, to
  48 MiB (the arguments), and the heap grows it only when a cell would end beyond
  it, to the next 16 MiB boundary at or above that cell's end (choice 15). So the
  memory ends exactly where a cell does whenever that cell ends on such a
  boundary, and only there does a read or a write past a cell's end fault:
  anywhere else it lands in the cell's padding or in free heap above the bump
  pointer, which `$alloc` zeroes before any cell holds it. Three Books fill the
  heap with `fill(k, B0{})` (a 32-byte Activation and a 32-byte `B1` a step) so
  that their last cell ends at 48 MiB:
  - `memory-end-object` (k = 523,262): `T4{1, 2, 3, 4}`, whose four fields fill
    its 32-byte cell, then a Case that binds them; `On{}` after 523,264 entries;
  - `memory-end-action` (k = 523,261, with the pool constants `"y"` and 2^31
    aligning it): the 16-byte Action of an `IO.print` that is never applied;
    `On{}` after 523,264 entries;
  - `memory-end-closure` (k = 523,261, with two Big pool constants aligning it; round 7): an
    erased Closure over four Flags (live 0, `slots` 4) whose body cases on each and answers
    `On{}`. Its Activation (owner, depth and the 4 captures: 32 bytes, full) is the last cell
    and allocates nothing after it; `On{}` after 523,264 entries.

  Section 5's model (`ceiling_run`, which now also binds a Branch's fields) gives
  each fill count, bump pointer and line; the reference evaluation of the same
  plan with k = 3 gives the line and the calls, each further step being one
  entry. The test build pins `bump` = 48 MiB and `grows` = 2 (boot's grow, and
  one for describe's text, which starts at the memory's end), so a change of
  policy that moved the memory's end would fail the rows, not leave them testing
  nothing. A probe of the VM (`.local/vm-core/probe/r9/`) found that three of the
  study's survivors trap on these Books and nowhere else, before the rows were
  frozen; the frozen values come from the model and the reference, which the gate
  derives again.
- **Small host stack.** A generated 200,000-deep nested expression, and the
  deep runs, under `node --stack-size=64`. The call graph of `vm.wasm` has no
  cycle and no `call_indirect`.
- **Malformed images.** As above: 211 frozen controls, nine of them at §4's
  limits (each `Exhausted` kind 2 on one side, malformed or invalid on the
  other), 4,440 fuzz images and 9,810 limit-word images, with no trap and no
  crash of the reference codec (a crash fails the gate, and `crash_fails`
  checks that it does). The
  VM of `6f78bd2` refused 2,190 of the limit-word images differently from the
  reference codec: 1,674 counts that the remaining words cannot hold (it read
  `record-length`), 468 `limits` and 48 Closure `closure-slots`
  (.local/vm-core/logs/r6-limit-words-prefix.log).
- **Mutants.** One hundred and thirty-nine, each killed by a wrong observation in a named group
  (seven by a trap and one by a hang, below; the 87 that came before round 7 are listed first):
  - arm selection, slot off-by-one, Nat bound and x % 0 (goldens);
  - fuel (fuel boundaries);
  - validator offset (goldens and controls);
  - output during a magic refusal (`loader-refusal-prints`, controls): exit and
    stderr still name the correct refusal, but stdout and the effect count
    violate the independent loader expectation. Review r0 reproduced a faulty
    baseline that printed `--\n`, then copied those bytes into its mutant jobs;
    the revised baseline rejects it before any such job is constructed;
  - quantum state loss (quantum re-entry);
  - tail release (display bound);
  - host-stack recursion (call graph);
  - a refused `none` slot (the admitted controls);
  - a refused code above U+10FFFF (`string-beyond-unicode`);
  - a surrogate left to the host (the D20 goldens, through the VM's registers);
  - a describe that demands its whole 16 MiB text window below 4 GiB (ceiling);
  - a Closure or the terminal continuation entered whatever its operand
    count, and a Closure's count checked after its fuel (run controls);
  - the ordinal count checked before the walk, and an arrow parameter
    refused as `argument-range` (Book invocations);
  - a Branch's or a Default's body required to equal its Case's type (the
    admitted controls);
  - a Nat's successor spelled with its zero's name, its text sized by the
    zero's name, a Nat word costing one visit, and each display bound
    exclusive (run controls);
  - Chr yielding its operand unread (the reference rows);
  - `append` moving `b` unread, `is_empty` reading only its head cell, `eq`
    reading both Strings in step and stopping at the first difference or
    either end, and the four conversions moving their word unread (run
    controls). Each reads exactly as much on a well-typed String or word, so
    each survives all 93 goldens and, among the 41 run controls, dies only by
    its own inspection controls (.local/vm-core/logs/r5-mutants-probe.log);
  - a Nat Case's predecessor made before its Scope push (the two
    `nat-pred` limited rows);
  - a cell, or an `append` block, ending exactly at 4 GiB taken as
    `Exhausted`, and a bump pointer that wraps to 0 there (the three ceiling
    rows at exactly 4 GiB);
  - the pre-fix VM's trap restored at both (`top-trap`, group `trap`). Its
    defect is the trap, so it is killed by a trap, but only when all three
    rows at exactly 4 GiB trap and the other seven ceiling rows stay right;
  - §4's limits (fifteen, choice 14). Order: the size checked after the image's
    length, the record limit before the count's fit, the arity limit before
    the record's length, and both `slots` limits after the validator's
    exact-slots rule. Absence: no limit on a Closure's `slots`, on a function's
    `slots`, on the arity or on the records.
    Kind: a count, or the size, refused as a malformed image; each limit
    exclusive; an arity that names `slots` as its cause. Fit: a count that
    exactly fills the remaining words refused, and a record taken as one word
    of them. Each survives all 93 goldens and 41 run controls
    (.local/vm-core/logs/r6-mutants-probe.log) and dies by a limit control
    (group `image-limits`: the nine refusals, the three oversize images and
    `arity-at-limit`, with the outcome registers). The two fit mutants survive
    every frozen control, whose counts sit far from the fit, and die only by
    the limit-word images (group `limit-words`);
  - the growth policy (two, choice 15). Memory grown to exactly the 64 KiB pages a
    cell needs (the VM of `dcc7c09`) gives every outcome, call count and bump
    pointer, so a timeout cannot kill it (§11); group `growth` kills it by the test
    build's `memory.grow` count in `loop-256mib`. A refused 16 MiB step that traps
    instead of falling back to the size needed is killed by `loop-refused`, at bump
    301,989,888 instead of the cap (group `refused`, judged on the registers of a
    run whose frozen outcome is itself a trap).
  - Case arm selection (review round 6; the seeded rows, groups `keys` and `tags`).
    The key search stepping toward the wrong half, never looking at the last key,
    or (group `hang`, below) stepping to the middle instead of past it; a tag
    Default reached by an immediate checked as a Branch and a Branch as a Default;
    and a tag equal to its Case's constructor count taken as in range (an
    immediate of tag 2 at a type with 2 constructors, read as the next record's).
    On gate `2e0c9b1`, run with each installed, the inverted comparison, the flipped
    Default check and the tag range passed whole; the stepping to the middle hung
    it (below); and the last key dropped was already caught by golden `case-char`,
    whose second key is its last;
  - describe of three or more fields (group `describe`): a separator before
    only the second field, before every second field, or a closing brace after
    the second whatever the Object has;
  - describe's bounds (groups `display`, `limited`): a Nat word adding n or n + 2
    visits, a constructor costing two, the visit bound exclusive, and the worklist
    triple 11 or 13 bytes, exclusive, unchecked, or reported as a heap exhaustion
    (the frame region it shares holds exactly 12 bytes per open Object);
  - append at a lowered heap (group `limited`): a block ending exactly at the
    limit refused, or a block past it reported as another kind. The exact edit of
    `top-block-exhausted`, which the 4 GiB rows kill, so the pin no longer needs a
    row that touches 4 GiB;
  - an Action's cell one payload word too large (`action-cell`, bump);
  - a scalar operand that is an Action passing as a Big cell (`ill-scalar-action`),
    and a Book result whose tag equals its type's constructor count
    (`ill-describe-at-count`) (group `tags`).

  - the scope tables (seven, choice 16; groups `scope` and `scope-growth`). The tables
    that never grow, W + 4200 restored (41 rows differ; the 20,000-Closure nest
    traps); a write that holds `s` indices, not `s + 1` (the slot at the tables' size
    lands on the use marks; killed by the edge rows whose size is even, where the two
    tables abut); a doubling that drops the types, carries a quarter of them, or
    drops the use marks (the typed edge rows; `nest-mark` and the 20,000-Closure
    nest); a table that grows to the index that passed it, not to twice its size (the
    result is right and the scratch gigabytes: killed by the `memory.grow` bound of
    `nest-mark` and `edge-t1-past`, in a group of their own, in 0.2 s, where the whole
    group took a minute); and a validator that refuses a unit as soon as its depth
    passes its `slots` (`excess-function`, `excess-closure` and corpus rows whose
    first defect is another).
  - an immediate tested in the same `or` as the loads through it (group `traps`):
    `$scell` and `$finish` as the VM of `2e0c9b1` had them. Its defect is the trap
    (like `top-trap`): the mutant is killed when a row of the inspection matrix
    traps where the frozen run is a refusal, and every other row stays right.
  - past a cell's end (group `memory-end`, four, from the study's survivors):
    an Object's operands copied 8 bytes each (past its cell at 3, 4, 7 to 12 or 15
    to 28 fields), an Action's operand copied 8 bytes (past IO.print's 16-byte
    cell), a Branch that binds one word more than its constructor's fields
    (past a cell the fields fill: 4, 12 or 28 of them), and a Closure's entry that
    copies one capture too many (past an Activation that the captures fill: 4, 12
    or 28 of them, and no other slot; round 7's `memory-end-closure`). Everywhere else the copy
    or read lands in padding or in free heap and changes nothing; each traps on
    its own memory-end row, and is killed there only while the other rows stay
    right.

  Round 7 adds 51 more:
  - D22 to D24 (twelve, groups `goldens`, `runs`, `quantum`): the eager rule (an Action's second
    application performs its effect and enters `k`), a request that a scope drops performed, Top's loop
    that enters `k` without performing, or ends the run after its first request, a Case with a
    Default that refuses a request (D23 before D24), a Case without one, a scalar read, a tag read, a
    String's tail and an Enter's target that meet a request as an ill-typed word or unread, a
    request that stops the run as a HostFailure and not an Unsupported (D4), and a Book that
    refuses every foreign but IO.print at load; and, for vm-spec's round 13 loader controls, a type
    record's constructor count that is not fitted to the constructor table before it sizes
    anything (`type-count-unfitted`, group `controls`);
  - atomic stops (SPEC §6.3; fourteen, groups `atomic` and `limited`): a Gather frame popped, or
    its last slot filled, before its node completes and can refuse; Succ and an intrinsic that pop
    before they inspect; Return to Top, the loop, a Halt, the final IO.OP and a Book's answer that
    drop `act` before their checks; a tail entry that pops and releases before its Activation is
    judged to fit; a non-tail entry that does not decide the room for its Call frame, and an
    InvokeFunction that pops before the room for the frame that replaces it; `reverse` and `show`
    that allocate cell by cell. The harness's `atomic` replay plays each run that ends in
    a stop to its last step and names what the step changed, so each mutant dies by the row
    whose last step it makes half-done (the two Nat Case mutants, before or after the Scope's
    room, are earlier);
  - the describe domain and the order of a word's inspection and its visit (the round 6
    review's findings a and b, fixed in round 7; five): an arrow (live or erased) or a `none`-typed field inside the domain,
    a result outside it that stops as a HostFailure and not an Unsupported, a visit charged
    before its word is inspected, killed at the 1,048,577th visit (`describe-order`), and a Book's
    description that writes its head before its result is inspected (group `runs`);
  - the study's survivors that new rows now kill (nineteen, from the round 7 study): a Closure
    whose depth leaves out its live argument (`closure-let`); a tail entry taken only below Top
    (`tail-call-fit`); the room of a Scope and of a Call frame one byte too large or too small
    (the four `-fit` and `-11` and `-15` rows); `show` counting its digits in base 9 or 11;
    a describe walk that takes every second field, or only the first; an arrow-only function
    argument and a search for FN that reads one entry past the function table (the invocation
    rows); the class of each of the three usage refusals; a Book, an Emit and a Halt that end in
    control Enter (the mode every clean run must end in); and the closure capture loop above.

  **Group `hang`.** The reviewer's `mid+1 -> mid` steps the key search to the
  middle instead of past it: on a miss above a key `lo` never moves, and the search
  never ends. It shows no wrong observation, only no observation, and the frozen
  outcome of every row ends. So it is killed the way `top-trap` is: a row that
  outlives its deadline (the harness's `deadline`, a watchdog that also stops a
  Wasm loop) is the wrong observation in this group. The mutant also hangs the
  goldens (`default-miss`: one key 7, queried at 9), so it never passed the gate
  silently: the real-host run waited for its 120 s timeout and the gate failed by
  it. Every mutant row has a deadline in the gate, so a hang in another group is
  a Timeout that never counts, and the mutant is reported as surviving that
  group, not left to stall the gate.
- **Mutant study.** `vm/study.py` enumerates the 993 systematic single-token mutants of 35 functions of
  `vm.wat` (a comparison or an arithmetic or bitwise operator swapped, or a small `i32.const` moved by
  one): the 21 semantic ones of round 6, `$setscope` and `$holdscope`, which hold the validator's scope
  tables, and the twelve that round 7 added for D22 to D24 and SPEC §6.3 (`$request`, `$opnd`, `$pop`,
  `$fit`, `$spare`, `$unscoped`, `$tail`, `$enter`, `$serve` and `$finish`, and the two of the describe
  domain and the invocation, `$describable` and `$entry`). On round 6's source it reproduced the
  reviewer's 567 name for name (on the lines they have now). `python3 vm/check-core.py --study --heavy`
  runs each against the gate's own rows (the same jobs and the same `observed_wrong`, so a kill there is
  a kill in the gate), group by group until a clean row shows a wrong observation. Otherwise it records
  the first hang or trap; a mutant with neither is a survivor. It runs each survivor against the ten
  ceiling rows too, and writes `vm/receipts/study.json`. `--only
  NAME,NAME` runs the mutants whose names contain any of those words and writes no receipt.

  Review r0 found one first-kill witness moved when the timeout scale changed from 2 to 4:
  `$ctor:1919:i32.sub->i32.add@25`, from `tags/lane:tags-shape` to `keys/lane:keys-u32-3`.
  Its killed classification and all 72 survivor explanations agreed. Receipts now record the
  scale, workers, group order, job and harness guards, source hashes of the gate and harness,
  and every timed-out or skipped job, even when a later group gives a clean kill. A timeout
  records whether the deadline or print-count guard fired. `by_group` and `by` are the first
  observations in that run, dependent on guards and scheduling; compare them with matching
  guards before attributing a difference to code. Outcome classifications remain separate.

  *Review round 1 result*, with the same WAT and frozen expectations: 993 mutants in 3,585 measured
  seconds, scale 2, 10 ordinary workers and 3 heavy mutant workers: **880 clean kills, 14 hangs,
  27 traps, 72 survivors; 921/993 detected (92.7%)**, no crashes or unassemblable mutants, no
  unexplained survivors or stale explanations. Every classification and all 72 explanations match
  the earlier receipt. Heavy replay adds four clean kills and one trap. The receipt records 178
  Timeout jobs (169 deadline, 9 print-count) and 42,486 Skipped jobs, with per-job deadlines; these
  are job events, not mutant counts. Two clean kills retain earlier interruptions.

  The one changed first witness is the same `$ctor:1919:i32.sub->i32.add@25`: still killed, now by
  `inspection/lane:inspect-u32-snil`, after keys, describe, tags and display each time out at
  40,000 ms and skip 46 following jobs in all. Its earlier witness was `tags/lane:tags-shape`;
  review r0 at scale 4 found `keys/lane:keys-u32-3`. Thus the fresh killed-group counts are
  keys 259 / tags 51 / inspection 161; the earlier run's were 259 / 52 / 160, and review r0's
  260 / 51 / 160. The historical receipt has no interruption trace: the documented scale alone
  does not establish equal opportunity for those earlier jobs to finish. See [REVIEW-R1.md](REVIEW-R1.md)
  for the complete dispositions, build pins and all 22 gate counts.

  *Earlier result*, on `vm.wat` sha256 `96bc6c90…` (round 7; 2,783 s on 10 workers, a load of about 35;
  timeout scale 2, absent from that historical receipt at `02aab74d`): of the 993 mutants,
  **880 show a wrong observation** (4 only on a ceiling
  row), **14 are killed only by a hang** (`$select`'s search, `$ctor`'s walk, and loops of `$enter`,
  `$serve`, `$describable` and `$entry` that never end) and **27 only by a trap** (an out-of-bounds
  store or load: `append`'s block, describe's worklist arithmetic, the String cells' immediate tests,
  the loads of a large scalar in `$enter` and `$finish`, the walks of the describe domain and of the
  invocation's arguments, and the copies and reads past a cell's end that only the four memory-end rows
  reach), and **72 survive**, each explained in `study.EQUIVALENT`, which the study checks against its
  survivors both ways. The gate's rule for its own mutants counts a trap or a hang only in the groups
  whose defect it is, but installed as `vm.wat` each of the 921 fails the gate: a frozen run is never a
  trap, and a hang outlives the gate's own timeouts. So the gate detects **921 of the 993 (92.7%)**: 880
  by a wrong observation, 14 by a hang, 27 by a trap (round 6's 541 of 582, 93%). The groups run
  cheapest first, and `by_group` in the receipt counts each result by the group of its first wrong
  observation, hang or trap: the 880 were first killed by keys 259, inspection 160, goldens 138,
  invocations 58, tags 52, display 47, runs 47, describe-domain 24, fixtures 23, limited 23, sweeps 20,
  dumps 6, ceiling 4, programs 4, scope 3, witness 3, describe 2, memory-end 2, writers 2,
  describe-order 1, fuzz-admitted 1, reference 1; the hangs by keys 8, describe-domain 2, inspection 2,
  goldens 1, tags 1; the traps by keys 7, goldens 5, inspection 4, memory-end 4, display 3, tags 2,
  ceiling 1, describe-domain 1.

  That reading is the study's, and installing mutants confirms it: a scratch copy of the branch whose
  `vm.wat` carries one mutant, re-pinned (`python3 vm/build.py --write`), makes the whole gate exit 1.
  Round 6's closing session did it for five of its 541 (three memory-end mutants, a golden that traps, a
  golden that outlives the host's timeout). Round 7 did it for five the study finds by other means than
  a wrong observation (`.local/vm-core/probe/r12/accept7.py`): `$enter:2409:i32.ge_u->i32.gt_u@28`, the
  trap of `memory-end-closure` (exit 1 after 17 s); `$room:2735:i64.gt_u->i64.ge_u@9`, found only by a
  ceiling row (164 s, at `ceiling-top`); `$entry:2954:const 1->0@46`, a hang (243 s, the real host's 120
  s timeout); `$describable:2914:const 1->0@63`, a trap in the study and a hang on the real host (a
  golden outlived its 120 s timeout: 123 s); and `$finish:2690:const 1->2@40`, a trap that a lane row
  reports (59 s). Earlier results: on round 6's source (`f206e6e3…`, after the scope-table fix) the same
  study ran 582 mutants of 23 functions in 3,057 s at a load of about 45: 515 by a wrong observation, 8
  by a hang, 18 by a trap and 41 survivors (541 detected, 93%); the reviewer's study of gate `2e0c9b1`
  had found 426 of its 567 by a frozen row, 67 more only by its own corpora, 12 hangs and 62 survivors.

  How round 7 used it. The first run on the VM that follows D22 to D24 and SPEC §6.3 (993 mutants) left
  109 survivors and one crash (a `$serve` mutant that repeated a print without end filled the process;
  the harness now stops a run at 1,000,000 prints, and it is a hang). Holding the study's goldens,
  invocations and reference rows to the state audit, which the gate already required of them, killed 12
  of the 109 (the class of an Activation, the operand copy of a function's entry, the payload count read
  from an Action, and the scratch word where the loop keeps IO.print's answer). Of the 97 left, 25 were
  holes in the rows, not equal mutants, and each is now a frozen row (`Study rows` above) and a registered mutant: a Closure whose
  depth leaves out its live argument (no row bound a slot inside a Closure that had a live argument),
  a tail loop below a Call frame taken for a non-tail entry, the room of a Case's Scope and of a Call
  frame off by one byte either way, `show` counting its digits in base 9 or 11, a describe walk that
  skips a field, an erased arrow that is not a function argument, a search of the export table that
  reads one entry too far, the class of a usage refusal, a Book, an Emit or a Halt that ends in control
  Enter (the study's kill of six needed one invariant: every clean run ends in Halt), and a capture loop
  that copies one word too many, which only a Closure's full Activation at the memory's end shows. The
  72 that remain are argued below.

  An earlier reading filed three of the survivors as differing only at 4 GiB: an Object's and an
  Action's operands copied 8 bytes each and a Branch that binds one word past its constructor's fields.
  Memory grows to the next 16 MiB boundary at or above a cell's end (choice 15), so it ends where a
  cell does at every boundary a cell ends on, from 48 MiB up. The memory-end rows sit on the first;
  each of the three traps there and nowhere else, and the gate registers them (group `memory-end`). The
  fourth, the Closure's capture loop, is `memory-end-closure`.

  The 72 survivors, by why no run tells them apart: 70 are argued equal on every input or unobservable until
  vm-rc, and two are reachable by a layout no row builds.
  - *unobservable until vm-rc* (29): 13 change which operands a prim or a completion drops (`$drop` is
    empty, choice 1); two the reference count of an append cell; three the owner word of an Activation
    (offset 8, which nothing loads); and eleven the loop over an Action's operands as its request is
    built, whose only effect is `$dup`, every load of it in bounds;
  - *equal on every input the VM admits* (27): `Nat.sub` at x = y (both arms of the select give 0), and
    the key search's `<` against `<=` where the keys differ; the flags and answers that a reader tests
    only for truth (6: `imm`, `tfn`, `$tail`'s and `$serve`'s answers, a seen mark and `$describable`'s
    answer); the four class masks (`7 -> 6`), where a Closure passes the class test and the type test
    refuses it, since its word at offset 8 is a node's word offset and every node follows every type
    record; the Action's foreign id, which only Top's loop reads, in a Program, whose one foreign is
    IO.print (its id and its operand count are both 1); the operand-count test of an Action target
    (`nops > 1`), which no valid image meets (Run controls above); the width of the copy of an Action
    into its request, which no foreign of the registry (two operands at most) overflows; the four loads
    of `$opnd` for an operand that no completion reads; six sizes of `$describable`'s scratch tables,
    which have slack; and two of `$entry`: a Program's first test at argc 2, which the second test (it
    reads argument 2 past the table, where scratch's first bytes give length 0) makes in its place (the real host's
    production module prints the same `usage` line on both argc-2 controls), and
    the walk over the ordinals, which starts at the FUEL that `$u32must` read a line above;
  - *no state is read* (6): the header payload count of a String cell (2), a Big cell (2) or the
    terminal continuation's `Emit{x}` (1), which leaves the cell's size class unchanged and is read only
    by the state audit; and the half of an append block cleared first (1), every word of which that is
    read is written after it;
  - *the scope tables' size and copying are no observation* (8, `$setscope:1420` and `$holdscope`): the
    tables grow one write early (a write holding one index more than it needs, or a doubling when
    exactly full: 2); at a size equal to the index that passed it either arm gives the same size (1); a
    type table of twice the bytes it needs (1); a copy of as many bytes again, into the half of the new
    type table that is written before it is read (1); and the guard on a table of 2^30 indices (3), which
    no image reaches: the earlier tables stay in scratch, so `$take` stops the image before a table
    passes 2^29 (choice 16);
  - *reachable, but by no row* (2): a class mask (`7 -> 8`) that only an Action whose foreign id is the
    String type index and whose operand is the word 1 passes, after which it reads past the Action's
    16-byte cell, so the words of the next cell decide the outcome (`ill-string-action` builds that
    Action and still refuses by the words it finds; another layout after it could read as a String, and
    one ending where memory does would trap); and the halved stack of `$describable`, which overruns only
    for constructors of more than half of the image's words, into memory above scratch that nothing reads
    (no `$take` follows it), and traps only where that block ends where memory does. No row builds either.
