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
- That host is main's file byte for byte (sha256 `4ee7b16d…`, last changed at
  `2e93d58`). It arrived with main through the vm-spec merge.

## Outcomes at the host boundary

| Outcome | How it is reported |
|---|---|
| Book result | `print("Evaluated\ttype\ttag\ttree")`, then `knot_main` returns (exit 0) |
| Program `Emit` / `Halt` | return (exit 0) / `die(code, message)` |
| HostFailure | `die(5, "HostFailure\t<phase>\t<code>")`; the phase is `image`, `invoke`, `arguments` or `io` (`io abi`: D20's non-scalar output) |
| Unsupported | `die(3, "Unsupported\t<phase>\t<code>")`: `invoke result-type`, and `vm foreign` |
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
- the 71 frozen controls, counted against SPEC §4's own figure (20 byte-level,
  9 at the limits, 42 plan-level). Each equals its frozen refusal, and the
  VM's own outcome registers name the outcome the refusal gives;
- 3,720 seeded single mutations of the goldens: 3,431 refused, and 289 admitted
  and run to a clean outcome;
- 7,741 images that set one word of a limit (each section's record count, each
  function's arity and `slots`, each Closure's `slots`) to values around its
  limit and, for a count, around the fit of two words per record: all refused,
  516 of them at a limit.

A refusal is read only from a run that stopped before `vm_boot` returned. A run
that got past boot and failed `ill-typed` inspected a word at run time (§6). It
did not refuse the image.

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
2. **Foreign leaves.** vm-core performs only `IO.print`. An image that
   contains any other foreign id is refused as `Unsupported vm foreign` before
   any entry: a D4 capability gap, never Invalid. vm-io lifts this.
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

   The VM inspects at exactly §6's points, and nowhere else:

   | §6 point | vm.wat |
   |---|---|
   | a Case scrutinee | `$select`: `$num` for keys, a Nat or a Char; the tag check of an algebraic word |
   | the operand of Succ and of Chr | `$complete`: `$num`, before the `NatRange` test or any allocation |
   | prims 0–33, the four conversions included | `$prim`: `$num` on each operand, in operand order |
   | String prims 34–38 | `$seq`, `$append`, `$reverse` and `$prim` walk each String with `$slen` first |
   | an Enter's target | `$enter`: its class, then its operand count (§7) |
   | every rendered word | `$describe`: `$num` or `$tagof` |
   | an Action operand | `$perform` → `$utf8out`, whose `$slen` walks the whole String before the scalar check (D20) |
   | the final IO.OP, a Halt's code and message | `$finish`: the IO.OP check, `$num` on the code, then `$utf8out` on the message |

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
   `0e07562`), and its four display run controls pin it.
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
8. **Halted states.**
   - **Stated limit.** An ill-typed operand of a prim, Succ or Chr halts with
     its Gather frame already popped. When the last operand arrives, `$run`
     pops the frame (`$top` becomes the operand block) and only then calls
     `$complete`, which inspects the operands (`$num`, `$slen`). A step that
     inspects first would leave the frame in the halted state.

     The outcome, `HostFailure image` (`ill-typed`), the heap and `calls` do
     not depend on it: the inspection precedes every allocation and `$dup` and
     `$drop` do nothing in vm-core. No control observes it: the run controls
     and the dump rows pin a halted state's outcome, cause and `calls`, and the
     structural audit runs before each transition, so it never sees the state
     a halt leaves. Only a comparison of the frames of such a halt would tell
     the two readings apart. None exists, and the reading is not changed,
     since no outcome depends on it.
   - At zero fuel the pending Enter's registers are kept and the mode reads
     Halt. §7 asks that the Enter stay in the state, while §6 lists Halt as a
     control.
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
    exactly 2^32; an empty one needs no memory. §10 orders neither the
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

## Findings for the spec owner

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
- **Ambiguities.** Choice 8's zero-fuel state is a real ambiguity in §6–§7 and
  needs one normative reading before lockstep; its Gather frame at an
  ill-typed halt is a stated limit no control observes. SPEC §8 has settled
  choice 6, and §6.1 choice 5 (D17).
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
  - A `Halt` message holding a surrogate. The VM refuses it as `HostFailure io
    abi`: it treats the message as an outgoing String under §10. The
    reference's `program` returns the Halt with its codes.
  vm-io owns the effect path.

## Evidence (gate `vm-core`)

- **Goldens.** All 93 through the real host, equal to `vm-expected.json`. The
  test build confirms every Exhausted, Unsupported and HostFailure cause in the
  VM's own outcome registers, and audits the state at all 1,806 transitions.
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
  evaluation runs it, a 4,401-character ordinal of leading zeros among them.
- **Admitted controls.** vm-spec's six admitted plan controls, its admitted
  limit control and seven code-list controls load. They run as `fixtures.json`
  froze them by literal review, and vm-spec's reference evaluation
  (`evaluate.book`) gives each the same run and `calls`:
  - `arity-at-limit`, `value-on` beside an unused function of 4,096
    parameters, prints `On{}` after 1 call;
  - `list-head-match` prints `True{}`;
  - the two `case-none-*` controls fail `ill-typed` after boot;
  - `first-code`, `first-code-none-case` and `key-arms-none`, whose arms fit
    their Case (§3), print `True{}` after 3 calls;
  - every code list compares `False{}`.
- **Run controls.** All 41 that check-spec.py freezes (`run_controls`), as
  many as SPEC §12 states, load, and each runs to its frozen exit, output,
  outcome and `calls`:
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
- **Small host stack.** A generated 200,000-deep nested expression, and the
  deep runs, under `node --stack-size=64`. The call graph of `vm.wasm` has no
  cycle and no `call_indirect`.
- **Malformed images.** As above: 71 frozen controls, nine of them at §4's
  limits (each `Exhausted` kind 2 on one side, malformed or invalid on the
  other), 3,720 fuzz images and 7,741 limit-word images, with no trap. The
  VM of `6f78bd2` refused 2,190 of the limit-word images differently from the
  reference codec: 1,674 counts that the remaining words cannot hold (it read
  `record-length`), 468 `limits` and 48 Closure `closure-slots`
  (.local/vm-core/logs/r6-limit-words-prefix.log).
- **Mutants.** Fifty, each killed by a wrong observation in a named group
  (one by a trap, below):
  - arm selection, slot off-by-one, Nat bound and x % 0 (goldens);
  - fuel (fuel boundaries);
  - validator offset (goldens and controls);
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
    the limit-word images (group `limit-words`).
