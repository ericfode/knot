# `knot-image-1` and `knot-vm-1`

Status: the normative contract for the VM-first route (D14), fixed on 2026-09-27
before any implementation. `docs/compiler-campaign/VM-DESIGN.md` (main `454bf30`,
amended for D19 at `819bf17`) chose the design; this document fixes its details.
Decisions D15–D19 are adopted in `docs/COMPILER-CAMPAIGN.md`;
[DECISIONS.md](DECISIONS.md) proposes the exact wording of D15–D18. `vm-model` (Bend) and `vm-core` (WAT) are built independently from this
text and must then agree in lockstep.

The core forms come from two unmerged heads, pinned by
[oracles/manifest.json](oracles/manifest.json): literals `2ea222e7` (Literal,
Intrinsic, Default and the prim registry) and closures `a1d68911` (Closure,
Invoke and arrow types). Each snapshot's own `eval-cli` and `check-cli` are the
Knot oracles. Neither head is an integrated literals-plus-closures compiler.

| Artifact | Role |
|---|---|
| [registry.json](registry.json) | prim ids, foreign ids, representation order, pinned Base digest |
| [serializer.py](serializer.py) | reference codec: `encode`, an independent `decode`, and `validate` |
| [golden/](golden/) | 78 sources, frozen observations, hand-written plans and their `.kimg` images |
| [golden/vm-expected.json](golden/vm-expected.json) | what the VM must print for each golden, derived by the rule of §11 |
| [bench/](bench/) | six frozen speed workloads, seed-native baselines, parse-cli counts |
| [check-spec.py](check-spec.py) | gate `vm-spec` |

MUST marks a conformance condition. Integers are unsigned unless stated. A word
is 4 bytes, little-endian. `none` is `0xffffffff`. Arithmetic that validates a
size or an offset detects overflow before narrowing.

## 1. What an image is

An image is the **checked core Book**, resolved and erased, one record per core
form. Encoding does not evaluate, specialize generics, defunctionalize, insert
ownership instructions or lower to ANF or CPS. The checker remains responsible
for types, quantities, termination and proofs, so a well-formed image is not
evidence of a checked program. No unchecked node passes through; an unsupported
source form or reachable leaf is reported `Unsupported` before any image exists.
A malformed image is `HostFailure image`, never source `Invalid`.

The encoder maps core forms as follows:

| Core form (literals / closures heads) | Image |
|---|---|
| `Value{t,tag}` of an algebraic type | `Value` |
| `Value{t,n}` of the U32 or Char representation | `Literal` of a U32 or Char constant |
| `Literal` (Nat, String) | `Literal` of a Nat or String constant |
| `Intrinsic{op,args}` | `Intrinsic` with the registry id of `op` |
| `Construct`, `Reference`, `Application`, `Let`, `Case`, `Branch`, `Default` | the node of the same name |
| `Closure`, `Invoke` | the node of the same name |
| hash-pinned foreign body | `Foreign` with the registry id |
| `Sequence` | flattened into its containing operand list; elsewhere an encoder InternalFailure |

Erasure drops every binder of quantity 0 together with its expression: parameters,
constructor fields, `Let` initializers (the `Let` becomes its body), branch
binders, captures and the matching call and construct arguments. An erased lambda
still exists: it is invoked with zero live arguments. Type and proof tokens and
source locations have no encoding.

**Slots.** Surviving levels are projected to contiguous slots. A function's live
parameters are slots `0..arity-1`. A `Let` and each live branch field take the
next slot. A closure body has its own numbering: captures in ascending
enclosing-slot order are slots `0..n-1`, the live parameter (if any) is slot
`n`, and its lets continue from there. The core names captured variables by
their enclosing level; the encoder renames them.

**Tables follow the checked Book.** The type table is the Book's datatype list in
order, including the closures head's `Arrow` entries. The function table is the
Book's function list in order. Base intrinsics therefore appear as ordinary
functions whose body is one `Intrinsic`, as `check-cli` displays them. For the
pinned literals checker, reachable Base declarations come first in `base.bend`
order, then the file's own; the goldens witness this order.

`src/image.bend` (increment `image`) is the future encoder. `serializer.py` lays
out hand-written plans and is its independent cross-check; it never parses Bend.

## 2. File layout

All offsets are **absolute word offsets from the start of the image**, never byte
addresses or VM pointers. No path, date, host endianness or address appears.

The header is 32 words:

| Word | Meaning |
|---:|---|
| 0 | `0x474d494b` (bytes `KIMG`) |
| 1 | version, exactly 1 |
| 2 | total word count, header included |
| 3 | entry kind: 0 Book, 1 Program |
| 4 | index of the function named `main`, or `none` if there is none |
| 5–10 | offsets of the types, constructors, functions, constants, nodes and names sections |
| 11 | reserved, 0 |
| 12–23 | representation type indices in `registry.json` order: Nat, U32, Char, String, Bool, Cmp, Unit, List, Result, Sigma, IO.OP, File; `none` if absent |
| 24–31 | the pinned `base.bend` SHA-256, bytes in order, packed little-endian into 8 words |

The six sections follow in that order, adjacent, starting at word 32, with no
padding or trailing words. A section is a record count followed by the records;
each record starts with its own length in words (that word included). Counts may
be zero. An index is a record's zero-based position in its own table.

| Table | Record payload after the length word |
|---|---|
| Type | `kind, name, a, b` |
| Constructor | `type, tag, name, n, field_type[n]` |
| Function | `name, result_type, arity, slots, body_offset, parameter_type[arity]` |
| Constant | `kind, n, data[n]` |
| Node | `opcode, result_type, operands…` (§3) |
| Name | `byte_length, utf8_packed[ceil(byte_length/4)]` |

**Types.** Kinds: 0 algebraic (`a` = first constructor index, `b` = constructor
count), 1 live arrow (`a` domain, `b` result), 2 erased arrow (`a` domain or
`none`, `b` result), 3 opaque (`a = b = 0`). Arrows have name `none`; every other
type is named. Constructor rows are grouped by type in type order, tags dense
`0..b-1` in declaration order. A field, signature or node result type may be
`none`: a value of an erased abstract type (a generic parameter), which may be
moved but never inspected or described (§3). Arrow types MUST NOT form a cycle
through their domains and results.

**Representations.** Header words 12–23 name the hash-pinned Base types; a
familiar name is never authority. Their pinned constructors, by tag, with live field
types (`none` is an erased type parameter): Nat `Zero{}`, `Succ{Nat}`; Char
`Chr{U32}`; String `SNil{}`, `SCon{Char, String}`; Bool two and Cmp three nullary
constructors; Unit one; List `Nil{}`, `Con{none, List}`; Result `Fail{none}`,
`Done{none}`; Sigma `Tuple{none, none}`; IO.OP `Emit{none}`, `Halt{U32, String}`.
A field naming another representation requires that representation declared.
U32 and File are **opaque**:
U32's `Word` representation is never exposed to the VM, and the encoder rejects a
reachable non-prim body that destructures it. A File is a host handle token.

**Constants.** Kinds 0 U32, 1 Nat, 2 Char, 3 String. The first three have `n = 1`
and hold the full value. A String holds its exact ordered Chr codes, not UTF-8;
pure Char admits every u32 (scalar validation happens only at the IO boundary).
Literal pools hold source literals only, never computed results.

**Names.** Nonempty UTF-8 without NUL, unused final bytes zero, unique by bytes.
A type and a constructor with the same spelling share one name record.

**Canonical order.** Names are interned in first-use order over type names, then
constructor names, then function names. Constants are interned by `(kind, data)`
in node-stream order. Nodes are emitted by visiting function bodies in table
order, children in the order of §3, parent last (post-order). No node is shared
and none is unreachable. `Closure.site` numbers closures consecutively in stream
order. An image is **canonical exactly when re-encoding its decoded plan
reproduces it byte for byte**; `serializer.py` is that re-encoder.

## 3. Node records

`child` is the offset of an earlier node record. Every node carries its result
type; a Branch or Default carries its Case's. A node's type is `none` exactly when
its value has an erased abstract type; such a value may be referenced, bound,
passed, stored in a field or capture and returned, but never inspected.

| Code | Form | Operands after the result type | Children, in order |
|---:|---|---|---|
| 0 | Literal | `constant` | — |
| 1 | Intrinsic | `prim, n, child[n]` | operands |
| 2 | Default | `body` | body |
| 3 | Value | `tag` | — |
| 4 | Construct | `tag, n, child[n]` | operands |
| 5 | Reference | `slot` | — |
| 6 | Application | `function, n, child[n]` | operands |
| 7 | Let | `slot, value, body` | value, body |
| 8 | Case | `slot, scrutinee_type, mode, n, rows…, default` | rows' arms, then default |
| 9 | Branch | `key, first_slot, fields, body` | body |
| 10 | Closure | `site, live_argument, slots, n, capture_slot[n], body` | body only |
| 11 | Invoke | `function, n, argument[n]` | function, argument |
| 12 | Foreign | `foreign, n, child[n]` | operands |

- **Value** is a nullary constructor of an algebraic type, including Nat's Zero
  and String's SNil. **Construct** has exactly the constructor's live field count,
  at least one. U32 and Char literals are Literal nodes, never Values.
- **Application** passes exactly the callee's live arity. **Intrinsic** and
  **Foreign** pass exactly the registry arity; their operand types, and an
  Intrinsic's result type, are the pinned representations the registry names,
  which the image MUST declare. A Foreign's result type is `IO(X)` in §8's shape,
  with `X` the registry's `output` representation.
- **Types agree.** Exactly, with `none` equal only to `none`: a Reference and its
  slot, a Let and its body, a Case and every arm body, and a Case's scrutinee type
  and its slot, which MUST be concrete. Where a value flows into a declared
  position (an Application's arguments and result, a Construct's fields, an
  Invoke's argument and result, a Closure's and a function's body) it **fits**:
  `none` on either side fits any type, arrows of one kind fit when their domains
  and results fit, and any other type fits only itself. Fit is instantiation of
  an erased parameter, so validation does not establish type soundness under
  generics; the VM inspects every word it reads (§6).
- **Let** binds slot = current depth; its value runs at that depth, its body one
  deeper. **Reference** and **Case** read a slot below the current depth.
- **Case mode 0 (tags)**: a dense table over the scrutinee type's constructors,
  `n` = constructor count, `rows = arm[n]` where `arm[t]` is a Branch with key `t`
  or `none`. The default is present exactly when some row is `none`. The encoder
  keeps the first matching source arm for each tag; arms after a catch-all are
  dropped. Nat dispatches on its logical view (`0` is Zero, `n>0` is Succ with
  field `n-1`); Char on `Chr(code)`. Mode 0 on U32 is forbidden.
- **Case mode 1 (keys)**: only for U32 and Char scrutinees; `rows = (key, arm)[n]`
  with strictly increasing keys, zero-field Branches, and a required Default. A
  dense 2^32 table is forbidden. This keeps the literals core's Default form.
- **Branch** binds the constructor's live fields to `first_slot = depth` and the
  following slots, in field order; `fields` is that live field count. **Default**
  binds nothing. Neither occurs outside a Case.
- **Closure** lists its captures as distinct enclosing slots in ascending order;
  they are exactly the body's free live slots. `live_argument` is 1 for a live
  arrow and 0 for an erased arrow, matching the result type's kind. `slots` is the
  exact maximum depth of the closure body. The body is a code offset, not a
  captured activation.
- **Invoke** evaluates its function, then its argument if live (`n = 1`), and
  applies. An erased Invoke has `n = 0`.
- **Foreign** evaluates its operands and builds an inert Action (§8).
- A function's `slots` is the exact maximum scope depth of its body, excluding
  nested closure bodies. Every operand list is evaluated strictly left to right.

## 4. Validation

The loader copies the bytes, checks the whole image, then materializes constants.
It never runs a body or an effect while validating. Validation, UTF-8 decoding,
constant materialization and rendering use explicit worklists, never the host
stack. The validator checks every function, reachable or not:

1. Size first: an image above 16 MiB (4,194,304 words) is `Exhausted image-size`,
   even when it is also malformed. Then length, magic, version, total, entry kind,
   reserved word and registry digest.
2. Section offsets, adjacency, counts, record lengths, name UTF-8, padding and
   uniqueness; constructor grouping; known type, constant and node tags.
3. Every index and child offset is in range and names a record of the right
   table; every child precedes its parent; each node has exactly one parent or is
   exactly one function's root.
4. The scope, arity and type rules of §2–§3, including representation field
   types, acyclic arrows, `IO(Unit)` for a Program's `main`, literal kinds, prim and foreign ids and arities (a reserved id is refused, never
   run as a Base body), arrow kinds, captures and exact `slots`.
5. Canonicality as defined in §2.

A refused image is `HostFailure image` with a reason. `check-spec.py` freezes 61
refusals (20 byte-level, 41 plan-level); vm-core MUST refuse the same controls.
Validation establishes these rules, not type soundness: a `none`-typed value may
be instantiated at any type (§3), so the VM's inspection (§6) and entry check
(§7) refuse the rest at run time as `HostFailure image` (`ill-typed`).
Other version-1 limits: at most 1,048,576 records per table, live arity at most
4,096, `slots` at most 65,536. These are resource limits, not source rules.

## 5. Words, cells and memory

**Words.** Zero is not a value; it marks an empty slot. An immediate is
`(v << 1) | 1` for `v < 2^31`: a nullary constructor tag, or the value of a U32,
Nat, Char or File token, according to the static type. Every other word is the
8-byte-aligned byte address of a cell, an unsigned 32-bit address: under the
4 GiB maximum (D19), pointers at or above 2^31 are ordinary. Scalars are **canonically boxed**: a
U32, Nat or Char value below 2^31 is always immediate, and one at or above 2^31
is always a Big cell. Nat is a word (D15), never a unary chain.

**Cells.** A cell is `[rc, hdr, payload…]` with `hdr = (payload_words << 3) | class`.

| Class | Payload | Owning edges |
|---:|---|---|
| 0 Object | `type, tag, field…` | fields |
| 1 Closure | `node, capture…` | captures |
| 2 Big | `value` | none |
| 3 Action | `foreign, operand…` | operands |
| 4 Activation | `owner, depth, slot[capacity]` | occupied slots |

`owner` is the function's root offset or the Closure node's offset; `depth` is the
live scope depth; `capacity` is the owner's `slots`; unused slots hold 0. Metadata
words are never edges. Every cell class, including Activations and File-holding
data, follows the same **uniform RC** rule; there is no Type/Data split, and no
operation creates a cycle.

`rc` is 1..`0xfffffffe`; `0xffffffff` is **immortal**. Overflow to the sentinel is
`Exhausted` kind 2 (`RCOverflow`), never wraparound. `dup(w)` does nothing to an
immediate, zero or immortal word and otherwise increments `rc`. `drop(w)` does
nothing to those and otherwise decrements `rc`; at zero it releases:

```
release(p): worklist = [p]
  while worklist: q = pop(worklist)
    for each owning edge e of q, last to first:
      if e is a mortal pointer: rc(e) -= 1; if rc(e) == 0: push(worklist, e)
    free(q)
```

Children are processed first-field-first. The worklist lives in the frame region
above the top frame and is empty between transitions; overflowing it is
`Exhausted` kind 3. Underflow, a dangling pointer, a double free or a class
mismatch is an InternalFailure, never exhaustion.

**Allocation.** A cell of `2 + payload` words takes the smallest power of two not
below `max(4, 2 + payload)` words. Each class has a LIFO free list; a free cell is
`[next_free, class_words, …]`. Allocation pops the class's list, else takes the
bump pointer; it writes `rc = 1`, the header and payload, and zeroes padding. A
debug build poisons freed payloads with `0xdeadbeef`. Addresses, bump, free-list
order and padding MUST agree in lockstep; the timing of `memory.grow` need not.
An allocation whose cell would end beyond the declared maximum of 65,536 pages
(4 GiB, D19) stops the machine with `Exhausted` kind 2 (heap), reproducibly on every
host. A host that refuses `memory.grow` below that maximum is `HostFailure`, never
`Exhausted`.

**Constants.** At load, before any other allocation, pool entries are materialized
in index order from the bump pointer, immortal: a scalar at or above 2^31 is a Big
cell; a String is an SCon chain built last character first (a Big code cell just
before the SCon holding it), ending in SNil (the word for tag 0). Sharing happens
only through interning. A Program image then allocates one immortal Closure-class
cell with `node = none` and no captures: the **terminal continuation**.

**Memory map.** Bytes `[0, 4096)` are control and scratch; the image is copied to
byte 4096; the frame region starts at the next 64 KiB boundary and is 16 MiB; the
heap follows it and grows up to the declared 65,536-page (4 GiB) maximum (D19). Host byte buffers are
allocator blocks with no edges, freed by their IO operation; `knot_alloc` keeps
them disjoint from cells across host callbacks and memory growth. Test builds may
lower the frame or heap limit only at initialization, and must report it.

## 6. The machine

**State.** `control` is one of `Eval(node)`, `Return(w)`, `Enter(target, ops)`,
`Halt(outcome)`. `act` is the current Activation (0 before the first entry);
`depth` means `act.depth`. The frame region is a LIFO stack. The counters are
`fuel`, `calls` and `quantum`. Code offsets and metadata are never roots; the
result register, `ops`, `act` and every frame value own one reference.

**Frames.** A record is `[value[n], node, aux, head]`, with `head = kind | (n << 4)`
on top and `top` one word past it; popping reads `head` and removes `n + 3` words.

| Kind | `node` | `aux` | Values |
|---|---|---|---|
| 0 Top | 0 | phase: 0 Book, 1 main's IO, 2 armed IO, 3 final | — |
| 1 Gather | the gathering node | operands filled | `n` operand slots, reserved as 0 at push |
| 2 Bind | the Let | 0 | — |
| 3 Scope | 0 | depth to restore | — |
| 4 Call | 0 | 0 | the caller's Activation |
| 5 InvokeFunction | the Invoke | 0 | — |
| 6 InvokeArgument | the Invoke | 0 | the function value |

A push that does not fit in the region is `Exhausted` kind 3, before anything is
written. A 250,000-deep `U32.add(depth(p),1)` recursion holds one Scope (3 words),
one Gather (5) and one Call (4) per level: 12 MB of the 16 MiB region.

**Transitions.** Each row is one externally visible step. Its dups, drops,
releases and allocations are substeps performed in the order written, and belong
to its post-state. No row runs user code or a second host effect.

| Control | Step |
|---|---|
| Eval Literal | Return the pool word. |
| Eval Value | Return the immediate for `tag`. |
| Eval Reference | `dup` the slot; Return it. |
| Eval Construct/Intrinsic/Application/Foreign, `n > 0` | Push Gather; Eval operand 0. |
| same, `n = 0` | Complete the node (below) with no operands. |
| Return, top Gather | Move the word into the next operand slot. If operands remain, Eval the next one; otherwise pop and complete. |
| Eval Let | Push Bind; Eval the value. |
| Return, top Bind | Pop; move the word into slot `depth`; push Scope(`depth`); `depth += 1`; Eval the body. |
| Return, top Scope | Pop; drop slots `depth-1` down to the saved depth, zeroing them; restore depth; keep returning. |
| Return, top Call | Pop; drop `act`; `act` = the saved caller; keep returning. |
| Eval Case | Select the arm (§6.1). Branch with `f > 0` fields: push Scope(`depth`), bind the fields, `depth += f`. Eval the arm body. |
| Eval Closure | `dup` the captured slots in order; allocate the Closure; Return it. |
| Eval Invoke | Push InvokeFunction; Eval the function. |
| Return, top InvokeFunction | Pop. Live: push InvokeArgument holding the function; Eval the argument. Erased: `Enter(function, [])`. |
| Return, top InvokeArgument | Pop; `Enter(function, [argument])`. |
| Return, top Top | Drop `act` and set it to 0; then §8. |
| Enter | §7. |

**Completing a gathered node.**
- Construct: Nat Succ yields `n + 1`, `Exhausted` kind 2 (`NatRange`) above
  2^32-1, allocating a Big if needed and then dropping the operand; Char Chr yields
  its code word unchanged; any other constructor allocates an Object that takes the
  operands. Return the result.
- Intrinsic: compute the prim (§9), allocating its result, then drop the operands
  in operand order, except an operand the prim moves into its result (§9), which
  is neither dropped nor duplicated. Return the result.
- Foreign: allocate an Action that takes the operands. Return it.
- Application: `Enter(function, operands)`.

**Inspection.** A `none`-typed value may be instantiated at any type (§3), so the
validator cannot exclude every ill-typed word. Every word the VM inspects is
therefore first checked against the type it is read at: a Case scrutinee (§6.1),
every word a prim reads (String cells included), every word §8 renders, every
Action operand §10 converts, and the final IO.OP (§8). An algebraic type admits an
immediate naming one of its nullary constructors, or an Object (class 0) whose
`type` is that type and whose tag names a constructor with fields; Nat, U32 and
Char admit an immediate or a Big cell (class 2), and File an immediate. A mismatch
halts with `HostFailure image` (`ill-typed`) before the step changes any state;
no read leaves a cell.

### 6.1 Case selection

The scrutinee is borrowed from its slot and inspected (§6). For an Object, the
tag and fields come from its payload; for an immediate of an
algebraic type, the tag is `v` and there are no fields. A Nat word `n` is Zero when `n = 0`, otherwise Succ with the new
word `n - 1` (a Big is allocated when `n - 1 >= 2^31`). A Char word is Chr with
its own code word. In key mode, the scalar's value is compared with the keys;
there is no field. The selected arm is `row[tag]`, or the matching key's arm, or
else the default. Fields are `dup`ed into consecutive slots in field order.

### 6.2 Tail position

An entry is a **tail entry** when every frame between `top` and the nearest Call
or Top frame is a Scope frame. This is exactly the static rule: function and
closure bodies are in tail position, and a Let body or Case arm inherits its
parent's position, while initializers and operands never do. A tail entry pops
those Scope frames and drops `act` (releasing the caller) **before** allocating
the callee, so a tail loop reuses its cell. A non-tail entry pushes Call(`act`).

## 7. Entry, fuel and quantum (D16)

`Enter(target, ops)`:

1. A target that is neither a function (Application) nor a Closure cell, an Action
   cell or the terminal continuation halts with `HostFailure image` (`ill-typed`)
   before anything else. If `fuel = 0`, stop with `Exhausted` kind 1; the pending
   `Enter` stays in the state and no effect happens. Otherwise `fuel -= 1`,
   `calls += 1`, `quantum += 1`.
2. By target:
   - a function: enter its body with `ops` moved into slots `0..arity-1`;
   - a Closure: enter its body with the captures `dup`ed into slots `0..n-1` and
     the argument (if live) moved into slot `n`; then drop the Closure;
   - an Action with no argument (the erased `R` of `IO(A)`): Return the Action;
   - an Action with continuation `k`: perform its effect (§10), build the Base
     result `r`, drop the Action, and continue with `Enter(k, [r])`;
   - the terminal continuation with `x`: allocate `Emit{x}` of the pinned IO.OP
     type and Return it.
3. "Enter a body" means: apply §6.2 (tail: pop Scopes, drop `act`; otherwise push
   Call), allocate an Activation of the owner's `slots` capacity with depth equal
   to the bound slot count, fill it as above, and Eval the body.

**Fuel** counts entries: the requested Book function or Program `main`, every
Application, every Invoke (erased ones included), both applications of an Action,
and every continuation application, the terminal one included. Nothing else pays:
operand evaluation, constructors, lets, cases, RC, prims, validation and rendering
cost zero. Operands are evaluated before their call is debited. Fuel is a u32
independent of eval-cli's transition budget, so no claim compares equal numbers
across the two. Goldens run with 1,000,000; benchmarks with the u32 maximum,
4,294,967,295 (`deep-recursion` alone makes about 2 × 10^9 entries).
`calls` is the total of successful debits, so the initial fuel is `fuel + calls`.

**Quantum.** When a debit makes `quantum` reach 65,536, the Enter step completes
(the new body is ready to Eval, or the Action's continuation is pending) and
dispatch returns to `knot_main` with the whole state committed. `knot_main` resets
`quantum` to 0 and re-enters dispatch. The effect of a pending Action therefore
runs exactly once. Re-entry never recurses, allocates a frame or restores fuel; it
is a Wasm-to-Wasm return and call. Test dumps show a Yield event here.

## 8. Books, Programs and Actions

**Book** (`IMAGE FN FUEL [ORDINALS…]`). The VM finds `FN` by name, checks that the
ordinals match its live arity and are nullary constructor tags of the parameter
types, pushes Top(phase 0) and starts with `Enter(FN, ordinals)`. Failures are
`HostFailure invoke unknown-export`, `argument-arity`, `argument-range` or
`structured-argument`, as in eval-cli. Return to Top(0) halts with the result and
prints

```
Evaluated<TAB>type<TAB>tag<TAB>tree<LF>
```

where `type` is `FN`'s result type index, `tag` is the result's constructor tag
(a Nat word is tag 0 when zero, else 1), and `tree` renders `Name{}` for a nullary
value and `Name{f1,f2}` for an Object's live fields, without spaces. A Nat word
`n` renders as its logical view, `n` times `Succ{`, then `Zero{}`, then `n` times
`}`. Erased fields do not exist and are not printed (golden `erased-construct`:
eval-cli prints `ProofBox{On{}}`, the seed `ProofBox{Off{}, On{}}`). eval-cli
reports `InternalFailure eval result-tag` for any U32, Char or String result, so
the VM reports `HostFailure invoke scalar-result` for one anywhere in the tree
(§11's Book-describe bound; golden `result-u32`);
a closure is `function-result` and an untyped (`none`) immediate is
`abstract-result`. Every rendered word is inspected (§6). Rendering is iterative, bounded by 1,048,576 visits and 16 MiB
of text; hitting either is `Exhausted` kind 2 (`display`), never a truncated
value. The result is dropped after printing.

**Program** (`IMAGE FUEL -- [ARGS…]`; only `ARGS` reach `IO.args`). `main` takes no
live argument and returns `IO(Unit)`, where
`IO(A) = @-R: Type -> (A -> IO.OP<R>) -> IO.OP<R>`: an erased arrow (domain `none`)
to a live arrow whose domain is a live arrow from `A` to IO.OP and whose result is
IO.OP. The validator requires exactly this shape, with `A` the pinned Unit.
The VM pushes Top(phase 1) and starts with `Enter(main, [])`. Returns to Top:

| Phase | On Return of `w` |
|---|---|
| 1 | set phase 2; `Enter(w, [])` applies the erased `R` |
| 2 | set phase 3; `Enter(w, [terminal])` |
| 3 | `w` must be an IO.OP Object (else `HostFailure image`, `ill-typed`): Emit ends with exit 0, Halt calls the host's `die` with its code and message. Drop `w` first. |

`IO.pure`, `IO.bind` and `IO.die` are ordinary Base code; `IO.die` returns `Halt`
directly. Emit is not an effect request. Program images require the Unit, String
and IO.OP representations.

**Actions.** `Foreign` builds an Action and performs nothing; dropping it or leaving
it in an unselected branch has no effect. Its first (erased) application returns
the Action itself; its second, with `k`, performs exactly one effect.

## 9. Primitives and numeric bounds (D15)

**Registry.** `registry.json` freezes ids 0..38 exactly as literals' `primitive.bend`
`code` table orders them (derived and re-checked mechanically by the gate), with
each Base name, input kinds, quantities and output. It reserves 39 `U32.or` and 40
`U32.xor`: base-pin's SHA-256 needs them, and they stay refused until vm-prims
freezes seed witnesses for them. `U32.not` is already id 5. New ids append; a
changed meaning or binary grammar needs a new version.

**Derivation rule.** A reachability pass over the **final merged S**, from
compile-cli and parse-cli, follows calls, value references and selected foreign
bodies after erasure. Each reachable seed intrinsic either has a registered prim
with the seed's semantics, or compilation is Unsupported. Each reachable non-prim
body that inspects an immediate representation (in particular `U32{Word}`) is
rejected. The pass is rerun whenever S changes; 41 ids today do not claim S's
registry is complete.

**Semantics** (the pinned Base bodies, on words):
- U32 `add`, `sub` and `mul` wrap modulo 2^32; comparisons are unsigned; `div` by 0
  is 0 and `mod` by 0 is the dividend; `shln` and `shrn` by 32 or more give 0;
  `not` and `and` are bitwise. Witnesses: `u32-wrap`, `u32-sub-wrap`,
  `u32-mul-wrap`, `u32-unsigned`, `u32-lt-unsigned`, `u32-div-zero`,
  `u32-rem-zero`, `u32-not`, `u32-and`, `u32-cmp`; shifts below 32 `u32-shr` (by
  31); shifts by 32 or more `u32-shift` (`shln` by 32), `u32-shl-33`, `u32-shr-32`
  and `u32-shr-33`, the last three observed as a Nat rather than through an
  equality. Equalities answer False as well as True (`u32-ne`, `nat-ne`,
  `char-ne`, `string-ne-order`, `string-ne-length`).
- Nat `sub` floors at 0 (`base.bend` lines 562–571; `nat-sub-floor`). `add`, `mul`,
  Succ and every conversion check the mathematical result before narrowing:
  above 2^32-1 is `Exhausted` kind 2 (`NatRange`), never U32 wraparound
  (`nat-big` and `u32-to-nat-big` inside the bound; `nat-range`, `nat-mul-range`
  and `nat-succ-range` beyond it). A Nat Case binds `n-1` (`nat-pred`); Succ adds
  one (`nat-succ`); `Nat.cmp` orders (`nat-cmp`).
- `U32.to_nat`, `U32.from_nat`, `Char.from_u32` and `Char.to_u32` keep the word.
  `Char.is_space` is 9..13 or 32 (`base.bend` 1765–1768; `char-space`).
- Bool is False 0, True 1; Cmp is LT 0, EQ 1, GT 2.
- String is the immutable Chr list: `eq` compares length and codes, `append`,
  `reverse`, `length` and `is_empty` observe the list, and `U32.show`/`Nat.show`
  give unsigned decimal without leading zeros except `0`. `string-codes` and
  `nat-show-codes` observe `append`, `reverse` and `show` through their character
  codes, not through `String.eq`.

**Ownership.** Every prim borrows its operands, and §6 drops them after the result
is allocated, except for these moves, which consume the operand into the result:
`String.append(a,b)` moves `b`, whose reference becomes the result's tail, and
drops only `a`; `U32.to_nat`, `U32.from_nat`, `Char.from_u32` and `Char.to_u32`
move their operand word, which is the result (a Big cell is reused, never copied
or dropped). Golden `string-append-mortal` appends a freshly allocated `b`, so
dropping it as well is a use after free.

**Allocation order.** A String result is allocated last cell first: `append(a,b)`
copies `a`'s cells onto the moved `b` from `a`'s last character to its first;
`reverse(a)` allocates from `a`'s first character; `show` from its last digit. A
Big result is allocated before the operands are dropped. Prims still without a
golden witness (U32 `is_ne/le/ge`, `U32.from_nat`, `Char.from_u32`, and Nat
`is_ne/lt/le/ge`) owe edge witnesses in vm-prims: 0, 1, 2^31 and 2^32-1.

## 10. IO and `knot-io-2` (D17)

The baseline is `knot-io-1` as merged on main: `campaign/io-host` `963a759`
(merge `0b9498b`), with D19's host memory ceiling (`a60307d`). The VM imports only
`knot_io`, exports `memory`, `knot_alloc(i32)->i32` and `knot_main()->()`, declares
a memory maximum of exactly 65,536 pages (D19), and has no start section; debug
exports exist only in the test build. Every inherited signature, the 16-byte result
record, errno table, ordering, sandbox and ownership rule stays in force. The
delta, owned by io-abi-2 and merged on main (`2e93d58`), whose
`docs/compiler-campaign/IO-ABI.md` section "knot-io-2 delta" is authoritative:

| Import | Parameters (i32, no result) | Delta |
|---|---|---|
| `read_bytes` | `handle, maximum, out` | Like `read`, but returns raw bytes with no decoding. |
| `path_identity` | `path, path_length, out` | modules' `path-host.bend` `inspect`: canonical spelling and absence of symlinks. |
| `exhausted` | `kind` | Adds kind 3 (frame region); 1 stays fuel, 2 memory and representation. |

io-abi-2 froze `path_identity`'s payload and precedence from `campaign/modules`
`0111f133`'s C and JS bodies, the same bodies whose hashes `registry.json` pins.
This document invents no identity algorithm and relaxes no sandbox rule. An image
may already encode foreign id 7; no VM run claims IO conformance before vm-io
passes that contract's fixtures.

Foreign rows in `registry.json`: 0 `IO.args`, 1 `IO.print`, 2 `File.open`,
3 `File.read`, 4 `File.write_bytes`, 5 `File.close`, 6 `File.read_bytes`,
7 modules `inspect`. Each row's `output` names the representation `X` of its
`IO(X)` result; the gate re-derives it from the Base declarations (`inspect`'s
comes from its pinned declaration). Applying an Action inspects (§6) and converts
its operands, calls the host, builds the exact pinned Base Result, pair and handle
view, and enters `k`. Outgoing Strings must be Unicode scalars and are encoded as
canonical UTF-8, with no surrogate merging or replacement. Incoming text follows
the host's replacement decoding, BOM kept, one Chr per scalar. Raw input bytes
become U32 elements 0..255.
A byte-list write scans the **whole** list first, computes `invalid |= e >> 8`,
copies low bytes and passes the flag; a nonzero flag is errno 22 before any write.

## 11. Outcomes and the Exhausted-lane rule

Accepted, Invalid, Unsupported, Exhausted, HostFailure and InternalFailure are
recorded separately. Malformed images and unknown ids are HostFailure; source forms
Knot does not handle are Unsupported; a broken invariant is a defect. A timeout or
crash never counts as a semantic mutant kill.

The observation lanes are the seed, pinned Knot eval-cli, the Bend model on the
image, and the Wasm VM on the image. The seed's **native** lane (the C1 lane) is
the reference; its Bun lane is a cross-check. A lane may be excused **only** by a
documented bound, and its receipt must name the bound, the budget and the boundary
reached:

| Lane | Documented bounds (observed evidence) |
|---|---|
| seed native | Nat to about 2^48; its runtime resources |
| seed Bun | about 32K stack frames (`List.length`); unary Nat materialization: `nat-big` passed 60 GB of RSS in about 6 minutes and was stopped, so word-Nat goldens use the native lane |
| literals eval | unary Nat and String up to 2^20 (`nat-big`, `nat-range`: `Exhausted primitive budget`); at most 1,048,576 transitions; display 4,096 visits and 65,536 characters |
| knot-vm-1 | Nat at most 2^32-1; call fuel; 16 MiB image; 16 MiB frames; 65,536 pages (4 GiB) of memory (D19); display bounds of §8; Book describe: algebraic trees with unary Nats only, so a U32, Char or String leaf is `HostFailure invoke scalar-result` (`result-u32`: eval-cli has no describe spelling for it either; Programs print scalars through IO) |

`NatRange`, `RCOverflow`, image size and display are representation-resource
exhaustion, kind 2 at the host boundary; the VM's own outcome keeps the precise
cause, request and limit, because `exhausted(2)` alone does not say which bound
was hit. Frame capacity is kind 3. Model tracing memory is a harness bound and
never excuses the VM.

**The rule.** Wherever the seed succeeds inside the VM's declared domain and
budgets, the VM MUST return the seed's value and effect trace. Another lane's
exhaustion never excuses the VM. A VM that exhausts early, corrupts a result or
reports an engine trap as a budget fails. Unsupported, timeout, unknown failure
and a missing lane are neither Exhausted nor agreement. Expected values are never
regenerated from a candidate VM.

[golden/vm-expected.json](golden/vm-expected.json) applies the rule to every
golden: the eval-cli line where eval agrees with the seed (70 goldens), agreement
meaning that eval's tree equals the seed's printed value in §8's spelling (no
spaces, erased fields dropped by the golden's declarations, a Nat unary); the seed's
value rendered by §8 where eval is excused (`nat-big`, `u32-to-nat-big`);
`Exhausted` kind 2 `NatRange` where the seed's value lies outside the VM's domain
(`nat-range`, `nat-mul-range`, `nat-succ-range`) and `HostFailure invoke
scalar-result` outside the Book-describe domain (`result-u32`), each justified in
[golden/bounds.json](golden/bounds.json); and the seed's stdout for the Programs
`foreign-print` and `io-bind`. For those Programs the eval lane is not excused but
unavailable: both literals `eval-cli` and `check-cli` report
`Invalid parse function-result` for `def main() -> IO(Unit)`, a program the seed
runs. Under D4 that should be Unsupported; it is recorded as observed, not
relabelled, and their plans follow §1 by hand. `io-bind` keeps Base's `IO.bind`
and `IO.pure` unspecialized, so its `A`-typed nodes are `none`.

## 12. Frozen evidence and later obligations

`check-spec.py` (gate `vm-spec`) builds both oracle heads with the seed's native
lane and requires:
- every golden source's hash, and a byte-identical re-execution of the seed and
  eval-cli observations frozen in `golden/expectations.json`;
- the registry re-derived from the literals snapshot;
- each committed `.kimg` equal to its plan's encoding, decoding back to the plan,
  and passing validation;
- each Book plan equal to an independent erasure and slot projection of that
  head's `check-cli` core display;
- the eval result's type index and constructor matching the image, and its tree
  equal to the seed's value in §8's spelling; a disagreeing eval lane is refused
  (three frozen expectation controls);
- every literal review (`seed_stdout`, written before observation) equal to the
  seed's printed value;
- `vm-expected.json` equal to the rule of §11 applied to the frozen observations;
- all 13 node forms, both Case modes, a Program, a boxed scalar constant and a
  `none`-typed node covered;
- all 61 refusals of §4 with their frozen reasons;
- 30 codec mutants and 3 source mutants killed through a changed image, a changed
  refusal or a changed observation, never a crash;
- the bench sources, guards and recorded outputs unchanged, and `baselines.json`
  and `parse-cli.json` equal to the digests pinned in `bench/workloads.json`; a
  re-measurement is refused until a reviewed commit re-pins it (two controls).

[bench/](bench/README.md) freezes Peano, lexer-shaped CPS closure churn, Char-list
String building with `String.eq` scans, List build and fold, 250,000-deep non-tail
recursion, and SHA-256 over 64 KiB, each with an independent guard and a seed-native
baseline, plus parse-cli's seed-native counts over S's 34 files. Timings are
observations, not gate thresholds, and claim no VM speed.

Later increments keep these expectations. vm-model adds checked proof entries for
the codec round trip, bounded validator soundness, the RC edge audit and zero
leaks. vm-core adds the iterative loader, validator, CEK machine, state dump and
quantum re-entry, and completes the 250,000-deep workload. vm-lockstep compares
every transition and the four value lanes, and derives each golden's exact call
count; vm-rc, vm-io and vm-prims close reclamation, effects and the final registry.
The first speed gate is at most 4× seed-native on each frozen workload on a quiet
host; above 10× requires design review.
