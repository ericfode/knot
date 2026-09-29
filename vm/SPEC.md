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
| [golden/](golden/) | 96 sources, frozen observations, hand-written plans and their `.kimg` images |
| [golden/vm-expected.json](golden/vm-expected.json) | what the VM must print for each golden and frozen Book invocation, derived by the rules of §8 and §11 |
| [evaluate.py](evaluate.py) | reference evaluation of a plan on values, not cells: a Program's prints, a Book's result |
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
A Book's entry is chosen at invocation, so a Book result that §8 cannot describe is
reported `Unsupported` by the invocation, statically, before any entry.
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

In a Case record (§3) `none` is a sentinel only for an absent tag row and an absent
default; a key is a plain u32 and may be `0xffffffff`.

**Types.** Kinds: 0 algebraic (`a` = first constructor index, `b` = constructor
count), 1 live arrow (`a` domain, `b` result), 2 erased arrow (`a` domain or
`none`, `b` result), 3 opaque (`a = b = 0`). Arrows have name `none`; every other
type is named. Constructor rows are grouped by type in type order, tags dense
`0..b-1` in declaration order. A field, signature or node result type may be
`none`: a position of an erased abstract type (a generic parameter), whose value
may be moved, is inspected only by a Case that names a concrete scrutinee type
(§3), and is never described (§8). Arrow types MUST NOT form a cycle through
their domains and results.

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
Having no pinned shape, the two may name one opaque type (run control
`u32-file-alias`): a U32 immediate at a File position is then a token, which the
host refuses as `HostFailure io handle` unless it is open. A `none`-typed value
can deliver the same word without the alias.

**Constants.** Kinds 0 U32, 1 Nat, 2 Char, 3 String. The first three have `n = 1`
and hold the full value. A String holds its exact ordered Chr codes, not UTF-8;
pure Char admits every u32 (scalar validation happens only at the IO boundary).
The reference codec's plans spell a String constant as that code list, never as
text, and `decode` returns every u32 code: a text step would merge a surrogate
pair or refuse a code above U+10FFFF (§12).
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
type; a Branch or Default carries its Case's. Types are positional: a node's type
is `none` exactly when the checked core gives its position an erased abstract type
(a generic parameter, including §2's pinned generic fields), whatever type the
value is instantiated at. Such a value may be referenced, bound, passed, stored in
a field or capture and returned; only a Case that names a concrete scrutinee type
inspects it (§6.1).

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
- **Slots are typed by their binders:** a parameter by its declared type, a Let
  by its value's node type, a capture by its enclosing slot's type, a live closure
  argument by its domain, and a Branch field by its constructor's pinned live field
  type (`none` for a generic field), never by the checked core's instantiated
  binder type.
- **Types agree.** Exactly, with `none` equal only to `none`: a Reference and its
  slot, and a Let and its body. A Case's scrutinee type MUST be concrete, and its
  slot's type is either that type or `none`: S matches the head bound from a
  List's `Con` (`case Con{+head,+tail}: match head: …` in `catalog.bend`), whose
  field is pinned `none`. A Case has the type of the position it fills: a
  function's or closure's result; its Let's or enclosing Case's type as a Let body
  or an arm; a Let binder's type as its value; an operand's declared parameter,
  field, registry input, arrow or domain type. That is how the encoder and the
  gate's display cross-check type a Case, so plans are canonical; validation
  checks only fit, and admits a `none`-typed Case in a concrete position
  (`first-code-none-case`). Where a value flows into a declared
  position (an Application's arguments and result, a Construct's fields, an
  Invoke's argument and result, a Closure's and a function's body, and every arm
  body of a Case) it **fits**: `none` on either side fits any type, arrows of one
  kind fit when their domains and results fit, and any other type fits only
  itself. S's `first_code(codes: List<U32>) -> U32` (`literal.bend`) answers `0`
  for Nil and the `none`-typed head for Con in one U32 Case (admitted plan control
  `first-code`); a key Branch and a Default answer a `none` parameter in another
  (`key-arms-none`). Fit is instantiation of an erased parameter, so validation does
  not establish type soundness under generics; the VM inspects every word it reads
  (§6).
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
  dense 2^32 table is forbidden. This keeps the literals core's Default form. A key
  is any u32, `0xffffffff` included: `none` marks only an absent tag row (mode 0) and an
  absent default, so no keys row is absent, a matching key is selected and a missing one
  falls to the Default (run controls `key-max`, `key-max-miss` and `char-key-max`, §12).
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

1. Size first: an image above 16 MiB (4,194,304 words) is `Exhausted` kind 2
   (`image-size`), even when it is also malformed. Then length, magic, version,
   total, entry kind, reserved word and registry digest.
2. Section offsets, adjacency, counts and the limits below, record lengths, name
   UTF-8, padding and uniqueness; constructor grouping; known type, constant and
   node tags.
3. Every index and child offset is in range and names a record of the right
   table; every child precedes its parent; each node has exactly one parent or is
   exactly one function's root.
4. The scope, arity and type rules of §2–§3, including representation field
   types, acyclic arrows, `IO(Unit)` for a Program's `main`, distinct function names
   (`FN` is found by name, §8, and `main` is one of them), literal kinds, prim and foreign ids and
   arities (a reserved id is refused, never run as a Base body), arrow kinds, captures and exact
   `slots`.
5. Canonicality as defined in §2.

A refused image is `HostFailure image` with a reason, except past a **resource
limit** of version 1, which is `Exhausted` kind 2 with the limit as its cause (D16).
These are limits of this VM, not source rules. Each bounds a count that the image's
structure admits: a count the structure cannot hold is malformed, and a count equal
to the limit is within it. A limit is checked when its count is read, after the
count's own structure and before anything the count governs, so it precedes a
malformed record, an inexact `slots` and every later rule:

| Limit, inclusive | `Exhausted` kind 2 (cause) | Malformed: `HostFailure image` |
|---|---|---|
| 4,194,304 words (16 MiB) per image | more words (`image-size`), checked first, even when also malformed | none: a size is not a count |
| 1,048,576 records per table | a larger count that the words after it can hold, at two words per record (`records`) | a count they cannot hold (`record count`) |
| live arity 4,096 | a larger arity in a function record whose length holds it (`arity`) | a length that does not (`function record`) |
| `slots` 65,536, a function's or a Closure's | a larger `slots` (`slots`), even when inexact | none: every word is a count; exactness is step 4 |

`check-spec.py` freezes 87 refusals (22 byte-level, 9 at the limits, 56 plan-level), and
vm-model and vm-core MUST each refuse every one of them, with the frozen refusal: `Exhausted`
kind 2 for a limit, `HostFailure image` for the rest, and the reference codec's own reason where
the VM reports one (vm-model spells it, vm-core maps it to a code of its own). A plan-level
control breaks exactly one rule of §2–§4 in a golden's plan, and its message is the validator's
first, so a loader that omits the rule admits it: a name with a NUL, or with a nonzero unused
final byte (byte-level); two functions of one name; a call to a function beyond the table; a
Case on a slot at or above the depth; a construct tag, or field type, that does not fit; a tag
row keyed for another tag; a key Branch that binds a field; a closure whose arrow kind or result
does not fit; an Invoke that does not fit; a Let, or a function, whose body has another type;
U32 or File declared as a data type; and the rules of earlier rounds. Which control kills which
codec mutant is `check-spec.py`'s (§12).
At the limits: the record, arity and `slots` limits passed by one (a function's
`slots` and a Closure's), a record count beyond the image and an arity beyond its
record, an image of exactly 16 MiB (`total`), 2^20 records whose first zero word is
a malformed record, and a `slots` of 65,536 that its body does not reach. vm-core
MUST refuse the same controls, and MUST admit its six admitted plan controls (three
Cases on a `none` slot, among them `list-head-match`, and three whose arms fit their
Case, among them `first-code`, S's shapes), `arity-at-limit` (an unused function of
4,096 parameters), its seven code-list controls and its 85 run controls; vm-model and
vm-core MUST run each run control, at the fuel frozen with it, to the outcome frozen
with it (§7, §12).
Validation establishes these rules, not type soundness: a `none`-typed value may
be instantiated at any type (§3), so the VM's inspection (§6) and entry check
(§7) refuse the rest at run time as `HostFailure image` (`ill-typed`).

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
| Eval Case | Select the arm (§6.1). Branch with `f > 0` fields: push Scope(`depth`), then bind the fields (§6.1), `depth += f`. Eval the arm body. |
| Eval Closure | `dup` the captured slots in order; allocate the Closure; Return it. |
| Eval Invoke | Push InvokeFunction; Eval the function. |
| Return, top InvokeFunction | Pop. Live: push InvokeArgument holding the function; Eval the argument. Erased: `Enter(function, [])`. |
| Return, top InvokeArgument | Pop; `Enter(function, [argument])`. |
| Return, top Top | Drop `act` and set it to 0; then §8. |
| Enter | §7. |

**Completing a gathered node.**
- Construct: Nat Succ first inspects its operand as a Nat, and Char Chr its
  operand as a U32 (below). An Object or a Closure there (class 0 or 1), like any
  cell but a Big, halts with `HostFailure image` (`ill-typed`) before the
  `NatRange` test or any allocation. Then Succ yields `n + 1`, `Exhausted` kind 2
  (`NatRange`) above 2^32-1, allocating a Big if needed and then dropping the
  operand, and Chr yields its code word unchanged. Any other constructor inspects
  nothing and allocates an Object that takes the operands. Return the result.
- Intrinsic: inspect every operand over its §9 extent, in operand order; then
  compute the prim (§9), allocating its result, then drop the operands in operand
  order, except an operand the prim moves into its result (§9), which is neither
  dropped nor duplicated. Return the result.
- Foreign: allocate an Action that takes the operands. Return it.
- Application: `Enter(function, operands)`.

**Inspection.** A `none`-typed value may be instantiated at any type (§3), so the
validator cannot exclude every ill-typed word. The VM therefore checks a word
against the type it is read at, at exactly these points: a Case scrutinee (§6.1);
the operand of Succ and of Chr (above); every operand of every prim, over the
extent §9's table gives it, the moved operands included; an Enter's target, whose
class and operand count §7 checks; every word §8 renders; every Action operand §10
converts, whole; and the final IO.OP with a Halt's code and message (§8). Nothing
else is inspected: a Let, a Reference, any other Construct, a Foreign, a Closure's
captures and an Enter's operands move or share their words unread. An algebraic type admits an immediate naming one of its nullary
constructors, or an Object (class 0) whose `type` is that type and whose tag
names a constructor with fields; Nat, U32 and Char admit an immediate or a Big
cell (class 2), and File an immediate. Checking a word is shallow: it reads the
word and, for a cell, its class and an Object's `type` and tag. The deeper reads
are **whole** extents: a String's, each SCon cell and its Char word, head to
tail, to SNil; and a byte List's (`File.write_bytes`, §10), each cell and its U32
element, head to tail, to its end. A mismatch halts with `HostFailure image` (`ill-typed`) before the
step changes any state; no read leaves a cell.

### 6.1 Case selection

The scrutinee is borrowed from its slot and inspected (§6) against the Case's
scrutinee type, whether its slot is typed so or `none`. Selection reads a tag and
allocates nothing: an Object's tag is in its payload, an immediate of an algebraic
type is tag `v`, a Nat word `n` is Zero (tag 0) when `n = 0` and otherwise Succ
(tag 1), and a Char word is Chr (tag 0). In key mode the scalar's value is
compared with the keys. The selected arm is `row[tag]`, or the matching key's arm,
or else the default.

A selected Branch with `f > 0` fields pushes Scope(`depth`) and then binds its
fields into consecutive slots in field order:
- An Object's fields, and Chr's field (the Char's own code word), are shared with
  the scrutinee, which keeps its slot: each is `dup`ed.
- Succ's field is the predecessor `n - 1`, a word made here and nowhere else: an
  immediate when `n - 1 < 2^31`, otherwise a Big cell allocated now (rc 1, §5).
  It is **moved** into its slot, never `dup`ed: the slot owns its one reference,
  and the Scope pop drops it like any other. A Default or a Zero arm makes no
  predecessor.

The allocation follows the Scope push, so a frame-region `Exhausted` (kind 3)
allocates nothing, and a heap `Exhausted` (kind 2) leaves the Scope pushed. Golden
`nat-case-big` binds the Big predecessor 2^31, which its run frees only if it was
moved; run control `nat-default-big` takes the Default of a Nat Case on 2^31 + 1
and allocates nothing (§12).

### 6.2 Tail position

An entry is a **tail entry** when every frame between `top` and the nearest Call
or Top frame is a Scope frame. This is exactly the static rule: function and
closure bodies are in tail position, and a Let body or Case arm inherits its
parent's position, while initializers and operands never do. A tail entry pops
those Scope frames and drops `act` (releasing the caller) **before** allocating
the callee, so a tail loop reuses its cell. A non-tail entry pushes Call(`act`).

## 7. Entry, fuel and quantum (D16)

`Enter(target, ops)`:

1. The target must be a function (Application), a Closure cell, an Action cell or
   the terminal continuation, and must take `ops`: a Closure exactly its
   `live_argument` operands, an Action zero or one, the terminal continuation
   exactly one (a function's live arity is checked by §3 and §8). Otherwise the
   step halts with `HostFailure image` (`ill-typed`) before anything else, at
   `fuel = 0` too: a `none`-typed value can hand an Invoke an arrow of the other
   kind, or `k` to an erased Invoke (§12's run controls). Program phases 1 and 2
   (§8) enter through this same check. If `fuel = 0`, stop with `Exhausted`
   kind 1; the pending `Enter` stays in the state and no effect happens.
   Otherwise `fuel -= 1`, `calls += 1`, `quantum += 1`.
2. By target:
   - a function: enter its body with `ops` moved into slots `0..arity-1`;
   - a Closure: enter its body with the captures `dup`ed into slots `0..n-1` and
     the argument (if live) moved into slot `n`; then drop the Closure;
   - an Action with no argument (the erased `R` of `IO(A)`): Return the Action;
   - an Action with continuation `k`: under a Program entry, perform its effect
     (§10), build the Base result `r`, drop the Action, and continue with
     `Enter(k, [r])`; under a Book entry, stop with `Unsupported vm effect`
     without reading an operand (§8, D22);
   - the terminal continuation with `x`: allocate `Emit{x}` of the pinned IO.OP
     type and Return it.
3. "Enter a body" means: apply §6.2 (tail: pop Scopes, drop `act`; otherwise push
   Call), allocate an Activation of the owner's `slots` capacity with depth equal
   to the bound slot count, fill it as above, and Eval the body.

**A stop keeps the debit.** Once step 1 has debited, the debit stands whatever
step 2 or 3 does: when one stops the machine (a D20 or D22 refusal, `Exhausted` kind
2 or 3, a `HostFailure`), `fuel` is not refunded and `calls` counts that entry. A
refused print is therefore debited. `print-non-scalar` (and `-mid` and `-wide`)
stops after 4 calls (main, IO.print, the erased `R` and the Action applied to
`k`), `print-non-scalar-second` after 13, and a Book's refused Action after its fourth
entry (§8). vm-expected.json freezes the four D20 counts, and §12's run controls the
others.

**Fuel** counts entries: the requested Book function or Program `main`, every
Application, every Invoke (erased ones included), both applications of an Action,
and every continuation application, the terminal one included. Nothing else pays:
operand evaluation, constructors, lets, cases, RC, prims, validation and rendering
cost zero. Operands are evaluated before their call is debited. Fuel is a u32
independent of eval-cli's transition budget, so no claim compares equal numbers
across the two. Goldens run with 1,000,000; benchmarks with the u32 maximum,
4,294,967,295 (`deep-recursion` alone makes about 2 × 10^9 entries).
`calls` is the total of successful debits, so the initial fuel is `fuel + calls`.

**The boundary.** A run whose entries total `calls` completes with initial fuel
`calls`; with one unit less, its last entry stops with `Exhausted` kind 1 after
`calls - 1` debits, and at fuel 0 its first entry stops after none. The operand
check precedes the fuel test, so an ill-typed Enter is `HostFailure image` at
fuel 0 too. An Action applied to `k` is debited before its effect, and `k` is a
separate entry: when the Action's second application meets fuel 0, nothing is
written; when `k`'s entry does, the effect's output is already written. A Book's D22
refusal follows the same debit, so at fuel 0 that entry is `Exhausted`, not refused (§8).
Eleven fuel run controls freeze each side (§12), and two more the Book case.

**Quantum.** When a debit makes `quantum` reach 65,536, the Enter step completes
(the new body is ready to Eval, or the Action's continuation is pending) and
dispatch returns to `knot_main` with the whole state committed. `knot_main` resets
`quantum` to 0 and re-enters dispatch. The effect of a pending Action therefore
runs exactly once. Re-entry never recurses, allocates a frame or restores fuel; it
is a Wasm-to-Wasm return and call. Test dumps show a Yield event here.

## 8. Books, Programs and Actions

**Arguments.** The VM loads and validates the image first (§4); its entry kind
selects the form of the words after `IMAGE`: a Book takes `FN FUEL [ORDINALS…]`
and a Program `FUEL -- [ARGS…]`. The form's shape is checked before its words:
fewer words than it names, or a Program's second word other than `--`, is
`HostFailure arguments usage`. FUEL and every ORDINAL are **decimal
u32 words**: one or more ASCII digits `0`–`9` and nothing else (no sign, space,
separator, radix prefix or other script's digit), with a value at most
4,294,967,295. Any number of leading zeros is allowed: `01`, `000000000001` and
4,400 zeros followed by `1` are all 1. Every
other word, the empty word included, is `HostFailure arguments expected-u32`; a
value above the maximum is refused, never reduced modulo 2^32 (`4294967296` is
not 0). This is Base's `U32.read`, which eval-cli applies to its budget and
ordinals. FN and ARGS are any words, and FUEL any u32, 0 included (§7); eval-cli
also refuses a budget above its 1,048,576 transitions as `budget-out-of-range`, a
cap the VM does not share. eval-cli reads its words before its source; the VM
reads the image first because the entry kind selects the form, so an image §4
refuses is `HostFailure image`, or `Exhausted` kind 2 past a §4 limit, whatever the
words.

**Book** (`IMAGE FN FUEL [ORDINALS…]`). These checks run in this order, before any
entry and without debiting fuel; steps 2–4 fail as `HostFailure invoke` with the
cause named:
1. FUEL, then each ORDINAL left to right, is a decimal u32 word, else
   `HostFailure arguments expected-u32`. eval-cli reads every word before it looks
   `FN` up, so a malformed word refuses the invocation whatever `FN` names
   (`absent x`) and whatever an earlier ordinal would be refused for
   (`two F 9 x`).
2. `FN` is found by name, else `unknown-export`.
3. `FN`'s live parameters are walked left to right, as eval-cli walks them; an
   erased parameter takes no ordinal. With no ordinal left, `argument-arity`. An
   arrow parameter is `function-argument`. Otherwise the ordinal is a constructor
   tag of the parameter's type: at or beyond its constructor count it is
   `argument-range`, so an opaque type (U32, File) or a `none` parameter refuses
   every ordinal; naming a constructor with a live field, `structured-argument`.
   An admitted ordinal is that nullary constructor's immediate.
4. Ordinals left over are `argument-arity`.
5. `FN`'s result type must be **describable**: algebraic, with every live field of
   every constructor describable in turn. A cycle through algebraic types stays
   describable (Nat's `Succ{Nat}`); a `none` field, an arrow and an opaque type are
   not, so neither are the pinned Char (its U32 field) and String. Otherwise
   `Unsupported invoke result-type`: Knot has no describe spelling for such a
   result, so the VM refuses the request instead of inventing one (§11; goldens
   `result-u32`, `result-u32-field`, `result-char` and `result-string`).

The reference predicate is `serializer.invocation`, with `serializer.decimal` for
step 1's words; `serializer.arguments` selects the form by entry kind. The image keeps less than
eval-cli's core, so two eval-cli answers differ by contract: eval-cli admits a U32
ordinal 0 as the value 0, because its loader models U32 as one nullary constructor
(`opaque-parameter`), and refuses a constructor whose fields are all erased as
`structured-argument`, while the image has no erased field (`erased-field`).
Goldens `invoke-args` and `invoke-arrow` freeze each cause of steps 2–5, and
`invoke-words` step 1's words (§12). The VM then
pushes Top(phase 0) and starts with `Enter(FN, ordinals)`; no Action is performed under
it (Actions, below). Return to Top(0) halts
with the result and prints

```
Evaluated<TAB>type<TAB>tag<TAB>tree<LF>
```

where `type` is `FN`'s result type index, `tag` is the result's constructor tag
(a Nat word is tag 0 when zero, else 1), and `tree` renders `Name{}` for a nullary
value and `Name{f1,f2}` for an Object's live fields, without spaces. A Nat word
`n` renders as its logical view, `n` times `Succ{`, then `Zero{}`, then `n` times
`}`. Erased fields do not exist and are not printed (golden `erased-construct`:
eval-cli prints `ProofBox{On{}}`, the seed `ProofBox{Off{}, On{}}`). Every
rendered word sits at a concrete describable type, so the tree never meets a
scalar, closure or `none`-typed word; each is still inspected against that type
(§6). Rendering is iterative. A **visit** is one rendered constructor: an Object
or a nullary value costs one, and a Nat word `n` costs `n + 1`. The bounds are
inclusive: at most 1,048,576 visits and 16 MiB (16,777,216 bytes) of `tree`,
separators included. A result that needs more is `Exhausted` kind 2 (`display`),
never a truncated value (§12's four display run controls). The result is dropped
after printing.

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
| 3 | `w` must be an IO.OP Object, and a Halt's code a U32 and its message a String over its whole extent (§6); else `HostFailure image` (`ill-typed`). Emit ends with exit 0, its field unread, after `w` is dropped. A Halt's message is an outgoing String (§10): the code and then the whole message are inspected, and a message holding a non-scalar Char is refused as `HostFailure io abi` before `die` (D20), with `w` still owned and nothing written. Otherwise the VM converts the message, drops `w` and calls the host's `die` with the code and the message. |

`IO.pure`, `IO.bind` and `IO.die` are ordinary Base code; `IO.die` returns `Halt`
directly. Emit is not an effect request. Program images require the Unit, String
and IO.OP representations.

**Actions.** `Foreign` builds an Action and performs nothing; dropping it or leaving
it in an unselected branch has no effect. Its first (erased) application returns
the Action itself; its second, with `k`, performs exactly one effect under a Program
entry, wherever that application occurs, in evaluation order. Run control
`program-print-through-id` applies the Action to its continuation inside an argument of
a call (`run(m) = λ@R. λk. id(m(R)(k))`, whose answer only passes through `id`) and writes
`x` after 9 entries. The pinned seed writes `x` for that source on both of its lanes.

**Where the seed refuses (not frozen).** The seed does not run every shape that this
machine can. A Case over the IO.OP that an applied effect answers, such as
`got(IO.print("x")(R)(k))` with `got` matching `Emit` and `Halt`, fail-stops in every
lane and never fires the effect: an applied effect answers a request that only the
event loop decodes (the seed's own test, `tests/io/request_out_of_band.bend`). §11 binds
a VM only where the seed succeeds, so that shape lies outside it. The transition rules of
§6 and §7 apply to it unchanged (the effect is performed, then the Case reads what `k`
returned), and no run control freezes it or claims that the seed agrees. Whether a VM
should refuse it, as D22 refuses an effect under a Book, is the coordinator's decision
(DECISIONS, finding 11).

**A Book entry never performs an effect (D22).** Under a Book invocation the second
application of any Action, `Enter(Action, [k])`, stops the run with `Unsupported vm
effect` after its debit (§7) and before the step reads, inspects or converts an operand
(§6, §10), checks the foreign id or calls the host. Nothing is written, and neither the
whole-extent inspection nor D20's scalar check runs, so the print of an ill-typed or a
non-scalar String is refused the same way, as `Unsupported`, never `HostFailure`. An
Action built, dropped or applied to its erased `R` under a Book is no effect and runs as
under a Program. The refusal is D4's: never `Invalid`, never an effect nobody requested.
Run controls freeze it (§12). A print stops after 4 entries (main, IO.print, `R`, the
Action), and so does `IO.args`; a print whose String an `id` call builds stops after 5.
The pure `got(k(Unit{}))` evaluates after 3 entries, an Action built and dropped after 2
and one applied to its erased `R` after 3.

**No host call and no write are frozen.** Every Book control that stops at an Action freezes
`stdout` empty and `effects` 0 beside its cause and `calls`. The reference evaluation reports
both on every Book outcome, a Halt included (§12): `stdout` is the bytes written, and `effects`
the host calls made, counted where the call would be, after D22's guard and after D20's check
and just before the write. A VM's harness MUST compare both: `stdout` against what its host
wrote, and `effects` against the host calls that the run made (the `knot_io` calls of vm-core's
host trace, the effects that vm-model's model performs), which is the only observable of a call
that writes nothing (`IO.args`, whose control freezes no `stdout` that could differ). A stop
that had written or called first is not D22's stop, whatever its cause.

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
  and `nat-succ-range` beyond it). A Nat Case binds `n-1` (`nat-pred`; a Big
  predecessor in `nat-case-big`); Succ adds
  one (`nat-succ`); `Nat.cmp` orders (`nat-cmp`).
- `U32.to_nat`, `U32.from_nat`, `Char.from_u32` and `Char.to_u32` keep the word.
  `Char.is_space` is 9..13 or 32 (`base.bend` 1765–1768; `char-space`).
- Bool is False 0, True 1; Cmp is LT 0, EQ 1, GT 2.
- String is the immutable Chr list: `eq` compares length and codes, `append`,
  `reverse`, `length` and `is_empty` observe the list, and `U32.show`/`Nat.show`
  give unsigned decimal without leading zeros except `0`. `string-codes` and
  `nat-show-codes` observe `append`, `reverse` and `show` through their character
  codes, not through `String.eq`.

**Inspection.** Before a prim computes or allocates anything, §6 inspects each
operand at the type and over the extent below, in operand order. A scalar's
extent is its word; a String's is whole: each SCon cell and its Char word, head
to tail, to SNil. The first ill-typed word halts with `HostFailure image`
(`ill-typed`). No prim reads less than its extent, whatever its answer or its
moves: a moved operand is inspected like any other, `append` reads the `b` it
neither copies nor drops, and `eq` and `is_empty` read both lists to their ends
although the answer may be known sooner.

| Ids | Prims | Operands, read at | Extent | Moved |
|---|---|---|---|---|
| 0–15 | U32 `add` … `shrn` | `U32, U32`; `not` one `U32`; `shln`, `shrn` `U32, Nat` | each word | — |
| 16 | `U32.to_nat` | `U32` | the word | the operand |
| 17 | `U32.from_nat` | `Nat` | the word | the operand |
| 18 | `Char.from_u32` | `U32` | the word | the operand |
| 19 | `Char.to_u32` | `Char` | the word | the operand |
| 20, 21 | `Char.is_eq`; `Char.is_space` | `Char, Char`; `Char` | each word | — |
| 22–31 | Nat `add` … `is_ge` | `Nat, Nat` | each word | — |
| 32, 33 | `U32.show`; `Nat.show` | `U32`; `Nat` | the word | — |
| 34 | `String.eq` | `String, String` | `a` whole, then `b` whole | — |
| 35 | `String.append` | `String, String` | `a` whole, then `b` whole | `b` |
| 36–38 | `String.reverse`, `length`, `is_empty` | `String` | whole | — |

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
comes from its pinned declaration). An Action is applied to its continuation, and so
performs its effect, only under a Program entry: under a Book entry that step stops
with `Unsupported vm effect` before anything below (§8, D22). Under a Program, applying
an Action inspects (§6) every
operand before it converts any, a String or a byte List over its whole extent,
so an ill-typed cell anywhere in it halts as `ill-typed` even after a non-scalar
Char or a byte above 255. Then it
converts its operands, calls the host, builds the exact pinned Base Result, pair
and handle view, and enters `k`. Outgoing Strings must be Unicode scalars and are encoded as
canonical UTF-8, with no surrogate merging or replacement. An outgoing String that
holds a non-scalar Char (a surrogate, or a code above U+10FFFF) halts with
`HostFailure io abi` before the host call: none of it is encoded or written (D20,
§11). A Halt's message is an outgoing String too (§8): the code and then the whole
message are inspected, and a non-scalar Char in it halts as `HostFailure io abi` before
`die`. Only output is checked: building, storing or measuring a non-scalar Char is
pure code (§2). Incoming text follows
the host's replacement decoding, BOM kept, one Chr per scalar. Raw input bytes
become U32 elements 0..255.
A byte-list write scans the **whole** list first, computes `invalid |= e >> 8`,
copies low bytes and passes the flag; a nonzero flag is errno 22 before any write.

## 11. Outcomes and the Exhausted-lane rule

Accepted, Invalid, Unsupported, Exhausted, HostFailure and InternalFailure are
recorded separately. Malformed images, unknown ids and malformed invocations are
HostFailure, and an image past a resource limit of §4 is Exhausted kind 2; source forms Knot does not handle are Unsupported, and so is a Book
result that §8 cannot describe and an effect that a Book entry would perform (D22); a broken invariant is a defect. A timeout or
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
| literals eval | unary Nat and String up to 2^20 (`Exhausted primitive budget`: `nat-big`, `nat-range`); 1,048,576 transitions (`Exhausted eval budget`), one per term evaluated and one per successor or character materialized, so `Nat.is_gt(U32.to_nat(1048576),0n)` exhausts them; display 4,096 worklist steps and 65,536 characters (`Exhausted inspect budget`), two steps per constructor and two per field, so a tree of N constructors takes 4N − 2 and a Nat `n` renders only for `n` ≤ 1,023 |
| knot-vm-1 | Nat at most 2^32-1; call fuel; §4's image limits (16 MiB, records, arity, `slots`); 16 MiB frames; 65,536 pages (4 GiB) of memory (D19); display bounds of §8 |

`NatRange`, `RCOverflow`, §4's image limits and display are representation-resource
exhaustion, kind 2 at the host boundary; the VM's own outcome keeps the precise
cause, request and limit, because `exhausted(2)` alone does not say which bound
was hit. Frame capacity is kind 3. Model tracing memory is a harness bound and
never excuses the VM.

**An exhausted eval lane** where the VM owes the seed's value is excused only by
one of the three literals eval bounds, named by the phase eval-cli prints
(`Exhausted<TAB>phase<TAB>budget`), and only when the program passes that budget.
(Where a VM bound of golden/bounds.json applies, the VM's own outcome is Exhausted
and eval's lane is only recorded.) The gate measures it without eval-cli
(`check-spec.py` `EVAL_BOUNDS` and `reach`): `primitive` by the largest Nat or String
length a node yields in the reference evaluation; `eval` by a lower bound on
eval-cli's transitions, the terms the reference evaluation evaluates plus the Nat
and String sizes its Literals and Intrinsics yield; `inspect` by the steps and
characters of the seed's value. Any other Exhausted, or a documented one whose
budget the program does not pass, is refused. For each excused lane,
vm-expected.json and the receipt record the cause, the bound, the budget and the
boundary reached.

**The rule.** Wherever the seed succeeds inside the VM's declared domain and
budgets, the VM MUST return the seed's value and effect trace, except the output
D20 refuses (below). Another lane's
exhaustion never excuses the VM. A VM that exhausts early, corrupts a result or
reports an engine trap as a budget fails. Unsupported, timeout, unknown failure
and a missing lane are neither Exhausted nor agreement. An Unsupported outcome is
D4's refusal of a form Knot does not handle: a recorded capability gap, never a
bound. Expected values are never regenerated from a candidate VM.

**Non-scalar output (D20).** The program's own value decides it, never a seed
lane. The reference evaluation of the plan ([evaluate.py](evaluate.py), §6–§10 on
values) yields the Strings a Program passes to output effects, in order. It
implements `IO.print`, the only effect the goldens use; any other foreign or a
Halt fails the gate and counts as neither agreement nor D20 (a Halt's message is
refused like a print's, §8, but only a run control reaches it). When one String holds
a non-scalar Char, the VM writes the earlier Strings and refuses that one as
`HostFailure io abi` (§10); the golden is `divergent-by-contract (non-scalar
output)`, neither seed agreement nor a bound. Otherwise the case is ordinary seed
agreement, whatever Chars the program builds. The seed lanes are recorded and never
classify. The native lane exits 0 and writes every String as generalized UTF-8,
surrogates included, but keeps only the low 8 bits of the lead byte from 2^21, so
`Chr{67237376}` (0x401F600) writes `F0 9F 98 80`, the UTF-8 of U+1F600; its bytes
must equal the whole trace in that encoding. The Bun lane refuses a non-scalar Char
where it is constructed (`bend: N is not a Unicode scalar value`, exit 1), printed
or not; its earlier output must be a prefix of the VM's, and a native-lane Program
records it. D20 goldens: `print-non-scalar` (`IO.print(SCon{Chr{55296}, SNil{}})`,
ASCII source; native `ED A0 80 0A`), `print-non-scalar-mid` (`"a\u{D800}b"`; native
`61 ED A0 80 62 0A`, of which the VM writes nothing), `print-non-scalar-wide`
(`Chr{67237376}`; native `F0 9F 98 80 0A`) and `print-non-scalar-second` (`"a"`, then
the lone surrogate; the VM writes `a\n`, the Bun lane nothing). `non-scalar-code`
(`55296\n`) and `non-scalar-unprinted` (`a\nnonempty\n`, where the Bun lane writes
`a\n` and refuses) build a surrogate without printing it and agree with the seed.
The refused entry stays debited (§7), so each D20 row of vm-expected.json freezes its
`calls`, by literal review of the entries: 4 for the first three goldens (main,
IO.print, the erased `R` and the Action applied to `k`) and 13 for
`print-non-scalar-second`.

[golden/vm-expected.json](golden/vm-expected.json) applies the rule to every
golden: the eval-cli line where eval agrees with the seed (75 goldens), agreement
meaning that eval's tree equals the seed's printed value in §8's spelling (no
spaces, erased fields dropped by the golden's declarations, a Nat unary); the seed's
value rendered by §8 where eval is excused (`nat-big`, `u32-to-nat-big`,
`nat-case-big`, each by `Exhausted primitive budget`, their largest Nats 2^31, 2^31
and 2^31 + 1 past 2^20; `nat-transitions`, `Nat.is_gt(U32.to_nat(1048576),0n)`, by
`Exhausted eval budget`: its Nat 2^20 is inside the inclusive primitive budget, but
its 1,048,585 transitions pass the 1,048,576 budget) or unavailable (`chr-pattern` and
`list-head-match`, below);
`Exhausted` kind 2 `NatRange` where the seed's value lies outside the VM's domain
(`nat-range`, `nat-mul-range`, `nat-succ-range`), each justified in
[golden/bounds.json](golden/bounds.json), whose entries are all Exhausted;
`Unsupported invoke result-type` where `main`'s result type is outside §8's
describe domain (`result-u32`, `result-u32-field`, `result-char`,
`result-string`: the seed prints `5`, `Box{5}`, `'a'` and `"ab"`, and eval-cli
reports the `InternalFailure eval result-tag` defect recorded in DECISIONS.md
each time), derived from the
image's type table and never listed as a bound; the seed's stdout for the Programs
`foreign-print`, `io-bind`, `non-scalar-code` and `non-scalar-unprinted`; and D20's
refusal for `print-non-scalar`, `print-non-scalar-mid` and `print-non-scalar-wide`,
with no output, and for `print-non-scalar-second` after `a\n`. For those
Programs the eval lane is not excused but unavailable: both literals `eval-cli`
and `check-cli` report `Invalid parse function-result` for
`def main() -> IO(Unit)`, a program the seed runs. Under D4 that should be Unsupported; it is recorded as observed, not
relabelled, and their plans follow §1 by hand. `io-bind`, `non-scalar-unprinted`
and `print-non-scalar-second` keep Base's `IO.bind` (and `IO.pure`) unspecialized,
so their `A`-typed nodes are `none`.

**A Book's unavailable lane.** A Book whose form a pinned head cannot check is
unavailable the same way, and Unsupported is still never a bound (above). `chr-pattern`,
the first tags-mode Case on Char (`case Chr{x}`, on an immediate Char and a Big one), and
`list-head-match`, S's Case on the head bound from a `List<Flag>` parameter, run on the
seed (`True{}` each). The golden's lane is the literals head, whose `check-cli` and
`eval-cli` both exit 3 for them, with `Unsupported check char-constructor-pattern` and
`Unsupported parse parameter-type`; the closures head answers otherwise (`Unsupported
lex literal`, `Unsupported parse declaration-form`) and is not consulted. The golden's
literal review declares that exact line (`unavailable`, in plan.json before
observation), and the gate requires the lane's two CLIs to print it: a CLI that prints a
core, another line, no declaration, or another failure (an Invalid lane of a Book, an
Unsupported one without its declaration) is refused. The expectation is the seed's value, basis `seed`,
`eval_lane` `Unsupported` and `eval_unavailable` the declared line, never agreement.
With no checked core to compare, the plan is held to the reference evaluation against
the seed's value; `list-head-match`'s plan also equals the lowering of a hand-written
display (§12) and is the plan of the admitted control of that name.

## 12. Frozen evidence and later obligations

`check-spec.py` (gate `vm-spec`) builds both oracle heads with the seed's native
lane and requires:
- every golden source's hash, and a byte-identical re-execution of the seed and
  eval-cli observations frozen in `golden/expectations.json` (a stdout that is not
  UTF-8 kept as hex; a native-lane Program's Bun lane and each frozen Book
  invocation's eval-cli answer too);
- the registry re-derived from the literals snapshot;
- each committed `.kimg` equal to its plan's encoding, decoding back to the plan,
  and passing validation;
- each Book plan equal to an independent erasure and slot projection of that
  head's `check-cli` core display (save the two whose lane's head answers Unsupported,
  declared in plan.json, §11), and each Program `main = IO.print(e)`'s argument
  equal to that projection of `e` checked as a `String` Book;
- the eval result's type index and constructor matching the image, and its tree
  equal to the seed's value in §8's spelling; a disagreeing eval lane is refused
  (three frozen expectation controls);
- every literal review (`seed_stdout`, written before observation) equal to the
  seed's printed value, byte for byte where it is not UTF-8;
- `vm-expected.json` equal to the rule of §11 applied to the frozen observations,
  with every bound Exhausted and no bound standing in for an Unsupported result
  (two frozen expectation controls), every excused eval lane matched to a documented
  eval-cli bound past its budget (four frozen expectation controls refuse an
  undocumented phase, `check`, and each budget unpassed, among them the Nat 1,023 at
  4,094 steps; two excused controls admit the Nat 1,024 at 4,098 steps and 6,150
  characters, and a transitions exhaustion of `u32-to-nat-big` at 4,294,967,304),
  and every Program classified by the reference
  evaluation of its plan: a declared D20 divergence exactly where it prints a
  non-scalar Char, with the VM output of the earlier prints, the native bytes equal
  to the whole trace in that lane's encoding and the Bun lane's output a prefix of
  the VM's (eleven frozen expectation controls, among them the wide code as
  agreement, its plan printing U+1F600, a surrogate built but never printed as a
  divergence, and the Bun lane's empty output as `print-non-scalar-second`'s; two more
  refuse a `calls` review that refunds the refused entry, or that is missing); five
  more refuse an unavailable eval lane that is undeclared, declared where eval-cli
  agrees, declared as another line or on a Program, or an Invalid lane of a Book, and
  three refuse the same at the display lane (`core:`); a Book's declared line is read
  from the lane's `check-cli` and `eval-cli`;
- the reference evaluation reproducing every Book golden's expectation and every
  run control's outcome and call count;
- each of the 44 frozen Book invocations of `invoke-args`, `invoke-arrow` and
  `invoke-words` equal to its literal review and to §8: `serializer.invocation`'s
  verdict, or the reference evaluation's describe line for the entered function;
  eval-cli's frozen answer agrees except where a declared `opaque-parameter` or
  `erased-field` divergence names the image loss the gate derives (seven frozen
  invocation controls, among them reviews that look `FN` up before the words and
  that reduce `4294967296` to 0). `invoke-words`' 16 rows pass step 1's
  words, a row's own FUEL word going to eval-cli as its budget: `absent x`, `absent`
  with FUEL `x`, `two 9 x`, `4294967296`, `4294967297`, `+1`, `-1`, ` 1`, the empty
  word, U+0661, `1_0` and FUEL `4294967296` are `expected-u32`; `01`,
  `000000000001` and FUEL `0001048576` enter; `4294967295` is `argument-range`;
- 13 **argument controls** (`check-spec.py argument_controls`), verdicts by literal
  review of what no eval-cli row can show: on `invoke-words`' image, `two` and
  `absent` are `usage` (before the lookup), a 4,401-character ordinal of leading
  zeros enters (eval-cli agrees, observed but not frozen), and the Program form
  `5 --` is `expected-u32` (FUEL `--`); on `foreign-print`'s, `5 --` and
  `0005 -- a --` run, FUEL `x` and `4294967296` are `expected-u32`, and `--`,
  `5 a`, `x a` (the shape before FUEL) and the Book form `main 5` are `usage`; and
  a bad magic word is `HostFailure image` whatever the words (`absent x`);
- §8's describe domain on nine frozen type controls: Flag, Nat and an erased-field
  box are describable; a U32 root, a U32 field, Char, String, a List of flags
  (`none` field) and an arrow are Unsupported;
- all 13 node forms, both Case modes, a tags-mode Case on Char, a Program, a boxed
  scalar constant and a `none`-typed node covered;
- all 87 refusals of §4 with their frozen reasons, each resource limit
  `Exhausted` kind 2 on one side and malformed or invalid on the other, its six
  admitted plan controls and `arity-at-limit`; `first-code` and `list-head-match` also
  equal the independent lowering of a `check-cli` display written by hand in the
  literals head's grammar, because no pinned head checks a `List<T>` parameter;
- 85 admitted **run controls** (`check-spec.py run_controls`), each frozen with
  its fuel (1,000,000 unless named) and the run §7 and §8 require, by literal
  review; the receipt records each one's argv. Through a `none`-typed identity: a
  live closure invoked live, `Evaluated 0 1 On{}` after 3 calls; an erased
  closure invoked live, a live closure invoked erased, the terminal continuation
  invoked erased, a live closure as main's value at phase 1 and an erased closure
  at phase 2, each `HostFailure image` (`ill-typed`) after 2, 2, 4, 2 and 3
  calls. And U32 and File named by one opaque type, `Evaluated 0 0 Off{}` after 1
  call; and a tags-mode Nat Case on the constant 2^31 + 1 whose Succ row is
  `none` (`nat-default-big`), `Evaluated 1 1 On{}` from its Default after 1 call.
  A validator mutant in which `none` never fits an arrow refuses the first,
  a generic function instantiated at an arrow type, so `fits` stays loose and §7
  checks the count. Four display controls meet §8's bounds exactly and then pass
  them by one, each after 1 call: the Nat 1,048,575 renders (1,048,576 visits)
  and 1,048,576 is `Exhausted` kind 2 `display`; `Duo{a,b}` of two Nats whose
  successor is named with 15 bytes renders in exactly 16,777,216 bytes, and
  `Pair{a,b}`, one byte longer, is `Exhausted`. Their lines are frozen by SHA-256.
  The seed's value obeys the same bounds (two frozen controls refuse one visit
  and one byte beyond them). Eleven fuel controls meet §7's boundary:
  `recursion-map` completes at fuel 6 and stops at 5 after 5 calls; `closure-nested`
  completes at 4, and its last Invoke stops at 3; `foreign-print` completes at 5,
  stops at `k` at 4 after writing `vm\n`, and stops at the Action's second
  application at 3 having written nothing; a Book and a Program stop at fuel 0 after
  0 calls; and two ill-typed Enters (an erased closure invoked live, a live closure
  at phase 1) meet fuel 0 after 2 calls and stay `HostFailure image`. Forty-three
  inspection controls (`inspection_controls`) hand a word of another type (a closure `λ`, a Pair
  or Box Object, an immediate beyond a type's constructors) through the identity to one
  inspection point each (§6, §9's table); each halts with `HostFailure image` (`ill-typed`).
  After 2 calls (main, id): a discarded `Chr{id(λ)}`, `Succ{id(Pair{Off{},On{}})}` and
  `Succ{id(λ)}`; a Book result that is `id(λ)`, or a Pair whose field is one, which §8 renders
  through the same reads; and an Invoke of the immediate 5 or of a Pair Object, neither a Closure,
  an Action nor the terminal continuation (§7 reads the target). After 3 (main, id, the prim's Base
  function, or `pick`): each move prim on `id(λ)`; `String.append("x", id(λ))`,
  whose `b` it moves; `append(SCon{id(λ), SNil{}}, "y")`, and `length` and
  `reverse` of that String, whose Char words they copy or count;
  `is_empty(SCon{'a', id(λ)})`; and `eq` past a differing code (`"a"` against
  `SCon{'b', id(λ)}`) and past either list's end (`""` against `SCon{'a', id(λ)}`,
  and the reverse); the word prims, each family in each operand position, through
  `U32.add` (first operand), `U32.sub` (second), `U32.shln` (its Nat amount),
  `Char.is_space`, `Char.is_eq` (second), `Nat.add`, `Nat.sub` (second), `U32.show` and
  `Nat.show`; and `pick(id(w))`, which cases on the word `w` (§6.1): `λ` at a Flag, a Nat
  and a Char in tag mode and at a U32 and a Char in key mode, a Box Object at a Pair (whose
  tag 0 also has fields), and the immediate 5 at a Flag. After 4 (main, the erased `R`, `k`'s
  closure, id): a Program's Halt whose code is `id(λ)`, or whose message is `SCon{'a', id(λ)}`,
  and a Program whose `k` answers `id(λ)`, or `id(5)`, for its IO.OP (§8's phase 3 reads the last
  word), writing nothing. After 5, having written nothing: `IO.print(SCon{Chr{55296}, id(λ)})`,
  whose whole String is read before the scalar check, so the cause is not `io abi`. After 7,
  having written `x\n`: `IO.print("x")(R)(id(5))`, whose Action meets an immediate for `k`: the
  effect comes first, and `k`'s Enter reads its target only then (main, the two closures,
  IO.print, the erased `R`, id, the Action's second application). A Halt's message is an
  outgoing String too: a surrogate then `id(λ)`, and `id(λ)` for the code beside a
  surrogate message, each halt `ill-typed` after 4, the code and then the whole message
  being read before D20's scalar check. Each kind of point in §6's list has a frozen
  control, and not each instance: the prim ids that no control names (U32 `mul` … `shrn`
  but `shln`, and Nat `mul` … `is_ge`) are vm-prims' to witness, one control per id and
  operand (§9), and the byte List and the operands of every foreign but `IO.print` are
  vm-io's. Sixteen effect controls (`effect_controls`) freeze
  D22 (§8), D20 on a Halt's message and the UTF-8 of a scalar. In a Book image, `got` returns what an IO.OP
  carries and `IO.print("x")` is applied to its erased `R` and to a continuation `k`:
  `book-print`, `book-print-continuation-call` (`k` a function) and
  `book-print-twice` (the reviewers' bookio-1, bk-print and bookio-2) stop
  `Unsupported vm effect` after 4 calls, writing nothing (each of these Book controls freezes
  `stdout` empty and `effects` 0, `fuel-book-effect-short` too); `book-print-non-scalar` (a
  surrogate) too, so D22 precedes D20; `book-print-ill-typed` (`"a"` then `id(λ)`)
  stops the same way after 5, so it precedes the inspection, and `book-args`
  (`IO.args`, foreign 0, of type `IO(List)`) after 4, so it precedes the check of the
  foreign id, and `book-print` at fuel 4 (`fuel-book-effect-exact`) is refused after its 4
  debits while at 3 (`fuel-book-effect-short`) its Action meets fuel 0 and stops
  `Exhausted` kind 1 after 3, so D22 follows §7's fuel test; the pure `got(k(Unit{}))` (`book-continuation-called`) evaluates
  `Evaluated 8 1 On{}` after 3,
  an Action built and dropped (`book-action-dropped`) after 2 and one applied to its
  erased `R` (`book-action-erased`) after 3; the same Action prints under a Program
  entry from inside an argument of a call (`program-print-through-id`, whose source the seed
  prints `x` for on both lanes), `x\n` after 9; a Halt whose message is a lone surrogate (`halt-surrogate`) stops
  `HostFailure io abi` before `die` after 3; and one whose message is scalar
  (`halt-scalar`, `x` and U+1F600) ends with `halt` 1 and that `message` after 3, the
  reference evaluation's view of a `die` whose exit status and stderr are the host's
  (IO-ABI.md). A scalar String is written as canonical UTF-8 (§10): `print-utf8-lengths` prints
  U+0024, U+00A2, U+20AC and U+10348 and `print-utf8-boundaries` the edges of every length (U+007F,
  U+0080, U+07FF, U+0800, U+D7FF, U+E000, U+FFFF, U+10000, U+10FFFF), each after 5 entries; the
  expected text is Python's own encoding, and the pinned seed writes the same 11 and 26 bytes on
  both lanes. Three key controls (`key_controls`)
  freeze §3's key: `pick` answers `On{}` from a key Branch at 0xffffffff for the U32
  and the Char `4294967295` (`key-max`, `char-key-max`) and `Off{}` from its Default for
  0xfffffffe (`key-max-miss`), each after 2 calls;
- seven admitted code-list controls, each decoding back to its plan through the
  decode CLI's JSON text: a surrogate pair beside U+1F600 (two constants, never
  merged), each alone, a lone surrogate, U+10FFFF, U+110000 and the u32 maximum;
  and `encode`'s refusal of a String constant spelled as text;
- 86 codec mutants and 4 source mutants killed through a changed image, a decode
  that differs from its plan, a changed refusal, a refused admitted control, a
  changed describe, invocation or argument verdict or a changed observation, and 85 evaluator mutants
  through a changed or refused expectation, Book value or run control, never a crash.
  Five codec mutants move §4's limits: a limit reported as malformed, a limit
  exclusive, the record limit before the count's fit, the arity limit before its
  record's length, and no limit on a Closure's `slots`; and a decoder that drops a keys
  row at 0xffffffff, which `key-max`, `key-max-miss` and `char-key-max` each refuse. Sixteen more remove one check of the reference
  codec (the statement of a `raise` or `fail` becomes `pass`, and the `return` or `continue` after
  it stays): a NUL in a name, or a nonzero unused final byte; U32, or File, declared as a data type;
  two functions of one name; a function index beyond the table; a construct tag, or a construct
  field type, that does not fit; a Let whose body has another type; a Case slot at or above the
  depth; a tag row keyed for another tag; a key Branch that binds a field; a closure arrow, or a
  closure result, that does not fit; an Invoke that does not fit; and a function body of another
  type. Each survives every golden and dies by the control that breaks its rule, three of them (a
  nonzero padding byte, U32 not opaque and the Invoke) by another refusal that the next check gives
  instead of the frozen one, the rest by an admission. The other 34 `raise` and `fail` statements
  of the codec that the review's audit removed one at a time are pinned by no control: for 12 of them
  the audit found only images on which the codec then crashes, which §11 does not count as a kill, and
  for 22 no image at all (DECISIONS, finding 12). Ten rule mutants of
  `check-spec.py` itself are killed the same way: `rejected` reporting a limit as
  `HostFailure image`; an eval lane excused by any Exhausted, or by a documented
  bound whose budget it does not pass; display steps counted as visits;
  transitions that omit materialization; a D20 golden whose `calls` are not
  checked; an unavailable Book lane whose declared line is not checked or whose cause
  is not named; a declaration kept where check-cli prints a core; and a Book without a
  core that declared none.
  Four survive every golden and die by a fuel control: fuel that never runs
  out, fuel that runs out one entry early, the fuel test before the operand check,
  and a free terminal continuation. An Action's effect before its debit dies by the
  D20 goldens' frozen `calls` (§7) and by the print inspection control, which counts
  it after 4 calls. A
  predecessor narrowed to 31 bits dies only by `nat-case-big`. Eighteen read less
  than their inspection extent, and exactly as much on a well-typed word, so they
  survive every golden and each dies by the inspection controls of its own point and by
  no other (a Halt's message unread also by the two Halt controls that carry one): Chr passing its operand through; Succ passing an Object, or
  a Closure; each move prim returning its operand unread; `append` moving `b`
  unread, or copying `a`'s Char words unread; `length` and `reverse` leaving the
  Char words unread; `is_empty` reading one cell; `eq` stopping at the first
  difference, or reading one list only one cell past the other's length (either
  way round); a Halt's code, or its message, unread; and a print that checks each
  Char as it reads it. Twenty more of that kind, read less or read too early, were the points that
  no control reached before the review of round 9, and each dies by the controls of its own point and
  by no golden: a tag-mode Case that admits a closure for its scrutinee (at a Flag, a Nat or a
  Char), one that reads a Char scrutinee unread, an Object of another type, a Nat that is no word or
  an immediate beyond the constructors, and a key-mode Case that reads its scrutinee unread (at a
  U32 or a Char, and at a Char alone); a U32 prim with its first operand unread, or its second (the
  shift's amount included), a Char prim with its first, `Char.is_eq` with its second, a Nat prim with
  its first, or its second, and `show` with its operand; a rendered closure admitted; an Enter that
  takes an immediate for an Action, or an Object for its target; an Action's continuation read before
  its effect, or left unread and taken for the terminal continuation; and a last word that is no
  IO.OP taken for `Emit`. Four more, of §10's UTF-8 of a scalar (the one-byte edge, the two-byte
  lead, and the edges of two and three bytes), die by the two print controls. Twenty-two more,
  of D22, a Halt's message, keys and the debit, die
  by the controls above: a Book that performs the effect and one that drops it silently
  (by every `book-print*` control); one that writes and then refuses (by every `book-print*`
  control's empty `stdout`) or writes as its Action meets fuel 0 (by `fuel-book-effect-short`
  alone); one that calls the host and then refuses (by the `effects` 0 of the seven Book controls whose
  Action is entered, `fuel-book-effect-short`'s meeting fuel 0 first) or does so for a foreign that
  writes nothing (by `book-args` alone); one that refuses before the debit (by every Book
  print control and both fuel controls) or when the fuel is 0 (by `fuel-book-effect-short`
  alone); one that names the foreign it refuses, as vm-model
  answered `Unsupported vm foreign 0` (by `book-args` alone); one that refuses only
  after the whole-extent inspection (by `book-print-ill-typed` alone), after D20's scalar check (by
  `book-print-non-scalar` and `-ill-typed`), when an Action is built (also
  `book-action-dropped`) or when it meets its erased `R` (also `book-action-erased`); a
  Program that refuses its effects (by the golden `foreign-print`); a Halt message
  never checked (by `halt-surrogate` alone), refused whatever it holds or above ASCII (by
  `halt-scalar` alone), checked as it is read (by
  `inspect-halt-after-surrogate` alone) or before the code
  (by `inspect-halt-code-first` alone); a key at 0xffffffff that is absent (by `key-max`
  and `char-key-max`) or a wildcard (by `key-max-miss` alone); and a refused Action
  whose debit is refunded (by the D20 goldens' `calls`);
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
leaks. The audit runs on every golden and run control that completes: a
predecessor `dup`ed rather than moved leaks a cell in `nat-case-big`, and one made
before its arm is chosen leaks in `nat-default-big`. The reference evaluation has no
RC, so this gate checks only their values. vm-core adds the iterative loader, validator, CEK machine, state dump and
quantum re-entry, and completes the 250,000-deep workload. vm-lockstep compares
every transition and the four value lanes, and derives each golden's exact call
count; vm-rc, vm-io and vm-prims close reclamation, effects and the final registry.
The reference evaluation performs only `IO.print`, so vm-io also owes the
inspection controls and mutants for every other foreign's operands, the byte
List's whole extent among them, and a Halt's `die` through the real host (exit
`code mod 256`, the message and LF on stderr).
A golden of the `first-code` shape (a concrete arm beside the `none` head), seed
`True{}`, is still owed; until then its admitted control witnesses validation and the
hand-written lowering, not the seed. `list-head-match` has its golden (§11).
The first speed gate is at most 4× seed-native on each frozen workload on a quiet
host; above 10× requires design review.
