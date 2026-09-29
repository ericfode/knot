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
| [golden/](golden/) | 111 sources, frozen observations, hand-written plans and their `.kimg` images |
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

**Names.** A name is a nonempty byte string that is well-formed UTF-8 as the Unicode Standard defines it (Table 3-7)
and holds no NUL. Well-formed means: no overlong form (a lead of `C0` or `C1`, `E0` before a byte under `A0`, `F0`
before a byte under `90`), no surrogate (`ED` before a byte from `A0`), no code above U+10FFFF (`F4` before a byte from
`90`, and any lead from `F5`), no sequence cut short by the end or by a byte that is not a continuation, and no stray
continuation byte. So a name is a string of Unicode scalar values, any of them, U+0080 and U+10FFFF and the
noncharacters among them, and a loader that refuses a non-ASCII name, or one length of them, is wrong as much as one
that admits a malformed form. The bytes of the last word past the name's length are zero, each of them and not only the
last. Names are unique by bytes. A type and a constructor with the same spelling share one name record.

**Canonical order.** Names are interned in first-use order over type names, then
constructor names, then function names. Constants are interned by `(kind, data)`
in node-stream order. Nodes are emitted by visiting function bodies in table
order, children in the order of §3, parent last (post-order). No node is shared
and none is unreachable. `Closure.site` numbers closures consecutively from 0 in stream
order. An image is **canonical exactly when re-encoding its decoded plan
reproduces it byte for byte**; `serializer.py` is that re-encoder. A loader without an encoder checks the
ten clauses of §4 step 5, which say the same.

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
   length, UTF-8 (§2), padding and uniqueness; constructor grouping and count (below); known
   type, constant and node tags.
3. Every index and child offset is in range and names a record of the right
   table; every child precedes its parent; each node has exactly one parent or is
   exactly one function's root.
4. The scope, arity and type rules of §2–§3, form by form (below), and of the image as a whole:
   representation field types, acyclic arrows, `IO(Unit)` for a Program's `main`, distinct function names
   (`FN` is found by name, §8, and `main` is one of them), literal kinds, prim and foreign ids and
   arities (a reserved id is refused, never run as a Base body).
5. Canonicality (§2): ten clauses, below.

**Step 4, form by form.** Each condition has a frozen refusal (§12), and a loader that omits it admits an image.
- **Value**: an algebraic type, a tag below its constructor count, and no live field (`value-with-fields`).
- **Literal**: a constant of the kind that its type pins (`literal-kind`).
- **Reference**: a slot below the depth, typed as its binder (`ref-beyond-depth`, `reference-type`).
- **Construct**: an algebraic type and a tag below its constructor count (`construct-tag`); the constructor has
  **at least one live field** and the node exactly that many operands, so a nullary constructor is a Value and never
  a Construct, whatever it is handed (`construct-arity`, `construct-nullary`); each operand fits its field
  (`construct-field-type`).
- **Application**: the function is in the table (`function-index`), the operand count is its live arity
  (`call-arity`), and the operands and the result fit (`call-result`).
- **Intrinsic and Foreign**: the id is registered and not reserved (`prim-unknown`, `prim-reserved`,
  `foreign-unknown`); the operand count is the registry's (`prim-arity`); each operand and the result are the
  pinned representations that the registry names (`prim-on-flags`, `prim-result`, `foreign-operand-type`,
  `foreign-result`).
- **Let**: its slot is the depth (`let-slot`), and its body has its type (`let-body-type`).
- **Case**: its slot is below the depth (`case-slot-beyond-depth`). Its scrutinee type is concrete, and its slot's
  type is that type or `none`, so a slot of one concrete type under a scrutinee of another is refused
  (`inspect-none-parameter`, `case-slot-type-mismatch`). In tags mode the scrutinee is a data type
  (`tag-case-on-opaque`), the table has one row for each constructor (`tag-table-not-dense`), the Default is
  present exactly when some row is `none` (`missing-tag`, `redundant-default`), a row's key is its tag
  (`branch-key`), and it binds the live fields from the depth (`branch-first-slot`, `branch-fields`). In keys mode
  the scrutinee is U32 or Char (`key-case-on-flag`), the keys increase strictly, so **no key repeats**
  (`keys-descending`, `keys-repeated`), a Default is present (`keys-without-default`), and a row binds nothing
  (`key-branch-binds-field`). Every arm body fits the Case's type (`branch-body-type`, `key-body-type`,
  `default-body-type`).
- **Closure**: its arrow kind matches `live_argument` (`closure-arrow`); its captures are distinct enclosing slots in
  ascending order below the depth (`capture-order`, `captures-repeated`) and exactly the body's free live slots
  (`unused-capture`); `slots` is the body's exact depth (`closure-slots`); the body fits the arrow's result
  (`closure-result-type`).
- **Invoke**: the function's type is an arrow (`invoke-non-arrow`); a live arrow takes **exactly one operand** and an
  erased arrow **none**, so a missing operand and an extra one are both refused (`invoke-live-without-argument`,
  `invoke-live-two-arguments`, `invoke-erased-with-argument`); the operand and the result fit (`invoke-types`).
- **Function**: its body has its result type (`body-type`), and its `slots` are the body's exact depth
  (`function-slots`).

**Step 5, clause by clause.** An image that passes steps 1 to 4 is canonical exactly when these ten hold, and a decoded
plan does not keep the words that they are about, so no earlier step can refuse a breach: a layout may differ from the
canonical one and decode to the same plan. `canonical_violations` reads each clause from the image's words and never by encoding it
again, and the gate holds it against re-encoding (§12). One frozen control breaks each clause alone, and the image
passes every other step.
1. **Main word.** Header word 4 is the index of the function named `main`, or `none` if there is none
   (`main-index-none`; a wrong index is `main-index`, at step 3).
2. **Names in order.** The name records are in first-use order: the names of the data and opaque types, then the
   constructor names, then the function names, each at its first use (`names-out-of-order`).
3. **Names used.** No name record is unused (`name-unused`).
4. **Constants in order.** The constants are in first-use order over the node stream (`constants-out-of-order`).
5. **Constants used.** No constant is unused (`unused-constant`).
6. **Constants once.** No two constants have one kind and one datum (`constants-duplicate`).
7. **Constructors in order.** The constructor records are in type order, and in tag order within a type
   (`constructors-out-of-order`).
8. **Nodes in order.** The node records are the post-order of the function bodies in table order, the children of a
   node in the order of §3 (`nodes-out-of-order`).
9. **Sites from 0.** The Closure sites are 0, 1, 2, ... in stream order (`closure-site-first`, `closure-site-second`,
   `closure-sites-swapped`, `closure-sites-from-one`).
10. **Arms' types.** A Branch and a Default carry the result type of their Case (`arm-type-branch`,
    `arm-type-default`).

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

**A type record's constructor count** is a count that the structure bounds, and it is refused before it
sizes or governs anything. A data type's record names its first constructor, which must be the table's
next (`constructor grouping`), and its count, which must fit what the constructor table still holds
(`constructor count`); the counts of all data types then sum to the table's size, and a shortfall is
`constructor count` too. The order within a record is the first constructor, then the count, then the name.
A loader that sized a list from the count before this check would ask for 32 GiB at `0xFFFFFFFF`, and
on a smaller host would trap or exhaust instead of reporting `HostFailure image`; the control
`type-count-max` refuses it, as `type-grouping` refuses a first constructor that is not the table's next
and `type-count-short` a sum that falls short.

`check-spec.py` freezes 211 refusals (124 byte-level, 9 at the limits, 78 plan-level), and
vm-model and vm-core MUST each refuse every one of them, with the frozen refusal: `Exhausted`
kind 2 for a limit, `HostFailure image` for the rest, and the reference codec's own reason where
the VM reports one (vm-model spells it, vm-core maps it to a code of its own). A control breaks exactly one
rule of §2–§4 in a golden's image or plan, and the reference's refusal names that rule alone. A loader that omits the
rule admits the image or, where it decides canonicality by encoding the decoded plan again, refuses it as `noncanonical`
instead (a changed reason: an opaque type's payload word, a named arrow, a scalar of two words and a repeated name are
words that a plan does not keep, so they are refused by their own rule or, failing that, by canonicality). Byte-level, on a valid
golden's records laid out again: every malformed form of a name
(each of the overlong forms, a surrogate, a code beyond U+10FFFF, a lead of `F5`, a sequence cut short inside or before
an ASCII byte, a stray continuation), a NUL inside a name and each nonzero unused byte (the first and both, not
only the last), an empty name, a name whose length word does not match its bytes, a repeated name, a name
index beyond the table; each of digest words 24 to 31; a first constructor that is not the table's next, a
constructor count of `0xFFFFFFFF`, and a sum of counts short of the table; a record of one word, a type of another
kind, an opaque type with a payload word, a named arrow, a constructor whose count, type, tag or name is wrong, a
constant of an unknown kind, of two words, of none or of the wrong length, a node record with an extra word or a
count that its operands contradict (each form), a Branch, a Default or a Case row that is the wrong node, a shared
node, an orphan, a keys row that does not repeat its key or whose arm is no Branch, a function whose record, root or type
words are wrong, a record cut short or overrunning the image, a count of records beyond the image, a main word beyond the
table; and the ten clauses of §4 step 5, one image each (four for the sites). Plan-level:
two functions of one name; a call to a function beyond the table; a Case on a slot at or above the depth, or whose slot
and scrutinee are two concrete types; a tags Case on a type with no constructors, a keys Case on a Flag, a Flag's
table one row short; a keys row that repeats; a construct tag, or field type, that does not fit, or a Construct of
a nullary constructor; a tag row keyed for another tag; a key Branch that binds a field; a closure whose arrow kind or
result does not fit, or that captures a slot twice; an Invoke that does not fit, or that takes the wrong number of
operands for its arrow (a live one with none or two, an erased one with one); a Let, or a function, whose body has
another type; a table one row too long, a representation or a Construct that names an arrow, a Program with no `main`, a
Value of a tag beyond its type or of a type with no constructors, a call or an Invoke whose operand does not fit, a capture
beyond the depth, a keys row whose first slot is not the depth, a closure or an Invoke of a data type; U32 or File declared as
a data type; and the rules of earlier rounds. Which control kills which codec mutant is `check-spec.py`'s (§12).
At the limits: the record, arity and `slots` limits passed by one (a function's
`slots` and a Closure's), a record count beyond the image and an arity beyond its
record, an image of exactly 16 MiB (`total`), 2^20 records whose first zero word is
a malformed record, and a `slots` of 65,536 that its body does not reach. vm-core
MUST refuse the same controls, and MUST admit its eight admitted plan controls (three
Cases on a `none` slot, among them `list-head-match`, three whose arms fit their
Case, among them `first-code`, S's shapes, and two of names, a type named with each length of
UTF-8 (U+0024, U+00A2, U+20AC, U+10348) and one named with every edge of a length (U+0080, U+07FF, U+0800, U+D7FF, U+E000,
U+FFFF, U+10000, U+10FFFF)), `arity-at-limit` (an unused function of
4,096 parameters), its seven code-list controls and its 135 run controls; vm-model and
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
| 5 Request | `foreign, operand…, k` | operands, then `k` |

`owner` is the function's root offset or the Closure node's offset; `depth` is the
live scope depth; `capacity` is the owner's `slots`; unused slots hold 0. Metadata
words are never edges. Every cell class, including Activations and File-holding
data, follows the same **uniform RC** rule; there is no Type/Data split, and no
operation creates a cycle.

A **Request** is what applying an Action to its continuation `k` builds (§7, D23): the
Action's foreign word, its operands in order, then `k`. It has the type IO.OP but is
neither an Emit nor a Halt, and it is inert: only Top's loop reads it (§8), and every other
read of a word refuses it (§6). Its `foreign` word is metadata, so its owning edges are the
operands and `k`, and releasing it releases them last to first like any cell's edges.

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
`Exhausted` kind 3. A release that would overflow it is a stop like any other
(§6.3): it decrements no count and frees no cell. Underflow, a dangling pointer, a
double free or a class mismatch is an InternalFailure, never exhaustion.

**Allocation.** A cell of `2 + payload` words takes the smallest power of two not
below `max(4, 2 + payload)` words. Each class has a LIFO free list; a free cell is
`[next_free, class_words, …]`. Allocation pops the class's list, else takes the
bump pointer; it writes `rc = 1`, the header and payload, and zeroes padding. A
debug build poisons freed payloads with `0xdeadbeef`. Addresses, bump, free-list
order and padding MUST agree in lockstep; the timing of `memory.grow` need not.
An allocation whose cell would end beyond the declared maximum of 65,536 pages
(4 GiB, D19) stops the machine with `Exhausted` kind 2 (heap), reproducibly on every
host, and the step that asked for it has changed nothing (§6.3): the room for every
cell that a step allocates is decided before the step's first change. A host that
refuses `memory.grow` below that maximum is `HostFailure`, never `Exhausted`.

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
| 0 Top | 0 | phase: 0 Book, 1 main's IO, 2 armed IO, 3 the loop | — |
| 1 Gather | the gathering node | operands filled | `n` operand slots, reserved as 0 at push |
| 2 Bind | the Let | 0 | — |
| 3 Scope | 0 | depth to restore | — |
| 4 Call | 0 | 0 | the caller's Activation |
| 5 InvokeFunction | the Invoke | 0 | — |
| 6 InvokeArgument | the Invoke | 0 | the function value |

A push that does not fit in the region is `Exhausted` kind 3, before anything is
written (§6.3). A 250,000-deep `U32.add(depth(p),1)` recursion holds one Scope (3 words),
one Gather (5) and one Call (4) per level: 12 MB of the 16 MiB region.

**Transitions.** Each row is one externally visible step. Its dups, drops,
releases and allocations are substeps performed in the order written, and belong
to its post-state. No row runs user code or a second host effect. A step that
stops the machine has no post-state: §6.3 says what it leaves, and the order in
which a row lists its substeps is the order of its effects, never of its refusals.

| Control | Step |
|---|---|
| Eval Literal | Return the pool word. |
| Eval Value | Return the immediate for `tag`. |
| Eval Reference | `dup` the slot; Return it. |
| Eval Construct/Intrinsic/Application/Foreign, `n > 0` | Push Gather; Eval operand 0. |
| same, `n = 0` | Complete the node (below) with no operands. |
| Return, top Gather | Move the word into the next operand slot. If operands remain, Eval the next one; otherwise complete the node (below) and pop the frame with it: a stop of the completion leaves the frame, with its operands, in place (§6.3). |
| Eval Let | Push Bind; Eval the value. |
| Return, top Bind | Pop; move the word into slot `depth`; push Scope(`depth`); `depth += 1`; Eval the body. |
| Return, top Scope | Pop; drop slots `depth-1` down to the saved depth, zeroing them; restore depth; keep returning. |
| Return, top Call | Pop; drop `act`; `act` = the saved caller; keep returning. |
| Eval Case | Select the arm (§6.1). Branch with `f > 0` fields: push Scope(`depth`), then bind the fields (§6.1), `depth += f`; a stop at the selection, the push or the predecessor's cell leaves neither Scope nor cell (§6.1, §6.3). Eval the arm body. |
| Eval Closure | `dup` the captured slots in order; allocate the Closure; Return it. |
| Eval Invoke | Push InvokeFunction; Eval the function. |
| Return, top InvokeFunction | Pop. Live: push InvokeArgument holding the function; Eval the argument. Erased: `Enter(function, [])`. The room for the push is judged on the region as the pop leaves it (§6.3). |
| Return, top InvokeArgument | Pop; `Enter(function, [argument])`. |
| Return, top Top | First the refusals of §8's phase, which change nothing (§6.3); then drop `act` and set it to 0; then the rest of §8. |
| Enter | §7. |

**Completing a gathered node.** The frame is popped by the completion, not before it:
what a completion can refuse (an ill-typed operand, `NatRange`, the room for its result
cell) it decides while the Gather frame still holds the operands, and a stop leaves the
frame, the operands and the heap as they were (§6.3).
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
  dropped nor duplicated. Return the result. A `NatRange` of the computation is a
  stop, and so is a result that has no room: neither has allocated or dropped anything.
- Foreign: allocate an Action that takes the operands. Return it.
- Application: `Enter(function, operands)`.

**Inspection.** A `none`-typed value may be instantiated at any type (§3), so the
validator cannot exclude every ill-typed word. The VM therefore checks a word
against the type it is read at, at exactly these points: a Case scrutinee (§6.1);
the operand of Succ and of Chr (above); every operand of every prim, over the
extent §9's table gives it, the moved operands included; an Enter's target, whose
class and operand count §7 checks; every word §8 renders; every operand of a request that the loop performs, whole (§8, §10); and the final IO.OP with a Halt's code and message (§8). Nothing
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

**A request is never inspected (D23).** At each of these points the machine reads the word's
class first, and a request (class 5) stops the run with `Unsupported vm effect`: whatever type the word
is read at, before the type test and before the step changes any state, and at an Enter's target before
its operand count and its debit (§7). A request is a legal value that this VM does not consume as data,
so D4 refuses it: it is not ill-typed, and it is never `Invalid`. The request's own operands and `k`
are not words that any of these points reads. Nothing reads them until Top's loop performs the
request (§8), and a Let, a Reference, a Construct, a Foreign, a Closure's captures and an Enter's
operands move or share a request unread, so a request can be stored, captured, passed and dropped.
Dropping one releases it (§5) and has no effect. One read takes a request without refusing it (D24): a
Case matches no row of a request, in either mode, so its Default takes it, unread; only a Case without a Default,
a tags Case whose every row names a constructor, refuses it (§6.1). The seed's native lane does the same for a source
with no catch-all; a source with one is taken by the native lane, and a compiler that lowers the catch-all into rows leaves
its plan no Default to take (§8).

### 6.1 Case selection

The scrutinee is borrowed from its slot. **A request selects no row (D24).** A class-5
scrutinee is not inspected: it matches no row, of a tags table or of a keys table, so the Case takes its Default, and a
Case without a Default, a tags Case whose every row names a constructor, stops `Unsupported vm effect` (§6). A keys Case
has a Default always (§3), so it never refuses a request. It holds at any scrutinee type, whether the Case's rows are an
Emit row, a Halt row, keys or none (`program-case-request-emit-default`, `-halt-default` and `-default-only`; a Case
that names Flag, `case-request-default-at-flag`; a keys Case, `case-request-default-keys`), because the Case never reads
the word beyond its class. The Default binds nothing, the request is neither read nor performed, and the Case borrows it
as it borrows every scrutinee, so the Default's value is what the run goes on with (§8: the goldens
`case-request-emit-default-u32`, `-halt-default-u32` and `case-request-emit-default`). Only a plan that holds a Default takes
one, and §3 keeps a Default only where a row is absent: a lowering that expands a source catch-all into a row for each
constructor that no arm names hands the VM a Case that names every constructor, which a request refuses like any Case without a
Default (§8's fourth row and its `-compiled` controls). Any other word is inspected (§6) against the Case's scrutinee type, whether its slot is typed so or `none`, and
whether the Case has rows or only a Default. Selection reads a tag and
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

The checks come in the order of the substeps, the room for the Scope first and then what the
fields need (the predecessor's cell, or the counts that the `dup`s raise, `RCOverflow`), and all of
them before either the push or the fields take effect (§6.3): a frame-region `Exhausted` (kind 3)
allocates nothing, a heap `Exhausted` (kind 2) leaves no Scope pushed, and when both would stop
the Case the frame region names the stop. Either way the machine is as the Case found it. Golden
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
The order is the order of the effects, and the fit is judged on what the entry
leaves: the callee's Activation fits if it fits after the pops and the release,
since it takes the cell that the release frees, and a Call frame if it fits on the
region as it stands. When it does not fit, the entry stops with the Scope frames
and `act` as they were (§6.3, §7).

### 6.3 Atomic stops

**A step that stops has no effect.** A **stop** is a step that ends the run instead of completing: a
`HostFailure` (an ill-typed word, D20's `io abi`), an `Exhausted` of any kind (fuel; `NatRange`, `RCOverflow`,
display and the heap, kind 2; the frame region and a release's worklist, kind 3) or an `Unsupported` (a request that a
read meets, D23). A broken invariant is a defect (§11) and no stop. The step that stops has no post-state: the
machine keeps the state in which the step began, whichever of its substeps had been tried. The control that could not
advance stays pending with the words it owns (an Enter its target and operands, a Return its word); `act`, `depth`,
every frame and `top`, every cell (each rc and payload word), the free lists, the bump pointer, the counters, the
constants and everything written or called on the host are as the step found them. A pop, a move into a slot, a `dup`,
a `drop`, a release, an allocation, a push, a byte written and a host call that the step would have made are none of
them made, or are undone. The one change that a stop leaves is the debit of `fuel`, `calls` and `quantum` that §7's
step 1 pays, when a later step of that Enter is what stops. A machine MUST leave exactly this state, and vm-lockstep
compares it.

**Check, then change.** So a row decides everything that it can refuse before it changes anything: its substeps take
effect together, once the last check has passed, and the order in which it lists them is the order of its effects and
never of its refusals. Where two checks of one step would both stop the machine, the earlier names the stop, in this
order: the words that the step reads, in the order of §6 and §9 (operand order), each with its request first
(`Unsupported vm effect`) and then its type (`ill-typed`); for an outgoing String, D20's scalar check (`io abi`, §8 and
§10) after the whole-extent inspection; then the limits, in the order of the row's substeps (§6.1's Scope before its
fields, §7's target before its fuel, §10's room after D20's check). A word is therefore inspected before it is charged against a
limit: §8's display counts a visit only for a word that it has inspected. Where the written order tempts a machine to
change first, the rows decide these before their first change:

| Row | Its checks |
|---|---|
| Return, top Gather (a completion) | the inspections of §6 and §9 in operand order; `NatRange`; the room for the result: the frame is popped by a completion that has passed them |
| Eval Case | the scrutinee's inspection (§6.1); the room for the Scope; the room or the counts that the fields need |
| Eval Closure, Return, top InvokeFunction, the cell of a Construct or a Foreign | the room for the cell or for the push; a `dup` that would overflow a count (`RCOverflow`) leaves every earlier `dup` of the step undone |
| Return, top Top | §8's refusals of the phase, before `act` is dropped: a Book's description (each word inspected, then charged, and the room for the text), a Program's request (its operands inspected whole, D20's scalar check, the room that its conversion and its result take), or its IO.OP, a Halt's code, its message and D20's check of it |
| Enter | §7: the target's class and operand count, then fuel; the debit is then paid, and a stop of steps 2 and 3 keeps the debit and nothing else |
| any `drop` or release | the worklist's room (kind 3): a release that would overflow it decrements no count and frees no cell |

**What holds each stop.** The reference evaluation ([evaluate.py](evaluate.py)) has no frames, `act` or cells, so it sees this rule
only in its outcome, `calls`, `stdout` and `effects`. §12's atomic controls freeze each stop with all four: what a stopped run reports
is what the run held before the refusing step (a stop after an effect keeps that effect's bytes and its host call), and the same run
given exactly the fuel that it has spent reaches the same stop, since a refused step pays nothing (an Enter is refused before it
tests fuel, and any other step tests none). What the frames, `act`, `top`, the cells and the free lists hold at a stop is beyond it, and
is held by comparing machines: vm-model's steps are atomic, and vm-lockstep compares vm-core with it at every halt, as at every state,
on the images that reach each stop: `inspect-halt-code` and `inspect-halt-message` (Return to Top refuses a Halt whose code or message is
ill-typed before `act` is dropped), the `NatRange` goldens `nat-succ-range`, `nat-range` and `nat-mul-range`, and the ill-typed operands of
`inspection_controls` (a Gather completion). A fuel stop is the Enter's own test: §7's eleven fuel controls freeze it, and the lockstep already
compares its pending Enter, target and operands. An image past a limit of §4 is refused at load, before there is a state to keep (§4's limit
controls). The heap and the frame region (kinds 2 and 3), `RCOverflow` and a release's worklist are out of the reference evaluation's reach;
vm-core's frame-region and heap-limit rows, which freeze `calls`, `top` and the bump pointer beside the outcome, and the lockstep hold them.

## 7. Entry, fuel and quantum (D16)

`Enter(target, ops)`:

1. The target must be a function (Application), a Closure cell, an Action cell or
   the terminal continuation, and must take `ops`: a Closure exactly its
   `live_argument` operands, an Action zero or one, the terminal continuation
   exactly one (a function's live arity is checked by §3 and §8). Otherwise the
   step halts with `HostFailure image` (`ill-typed`) before anything else, at
   `fuel = 0` too: a `none`-typed value can hand an Invoke an arrow of the other
   kind, or `k` to an erased Invoke (§12's run controls). Program phases 1 and 2
   (§8) enter through this same check. A request as the target stops the run
   `Unsupported vm effect` instead (§6), at the same place: first of all, before the operand
   count, at `fuel = 0` too and without a debit. If `fuel = 0`, stop with `Exhausted`
   kind 1; the pending `Enter` stays in the state and nothing is built or performed.
   Otherwise `fuel -= 1`, `calls += 1`, `quantum += 1`.
2. By target:
   - a function: enter its body with `ops` moved into slots `0..arity-1`;
   - a Closure: enter its body with the captures `dup`ed into slots `0..n-1` and
     the argument (if live) moved into slot `n`; then drop the Closure;
   - an Action with no argument (the erased `R` of `IO(A)`): Return the Action;
   - an Action with continuation `k` (D23): build a **request**. `dup` each of the
     Action's operands in order, allocate a Request (§5) whose payload is the Action's
     foreign word, those operands and `k`, whose reference moves in, drop the Action, and
     Return the request. The step reads no operand, converts none, checks no foreign
     id and calls no host: the effect belongs to Top's loop (§8), and happens only if
     the run returns this request there, under a Program entry;
   - the terminal continuation with `x`: allocate `Emit{x}` of the pinned IO.OP
     type and Return it.
3. "Enter a body" means: apply §6.2 (tail: pop Scopes, drop `act`; otherwise push
   Call), allocate an Activation of the owner's `slots` capacity with depth equal
   to the bound slot count, fill it as above, and Eval the body. Steps 1 to 3 are
   one step (§6.3), and the debit is the one change of it that a stop leaves.

**A stop keeps the debit, and nothing else (§6.3).** Once step 1 has debited, the
debit stands whatever step 2 or 3 does: when one stops the machine (`Exhausted`
kind 2 or 3, a `HostFailure`), `fuel` is not refunded, `calls` counts that entry
and `quantum` its debit. Nothing else stands: the Enter stays pending with its
target and operands as they were, and what steps 2 and 3 had begun (a tail entry's
popped Scope frames and released `act`, a pushed Call frame, `dup`ed captures,
moved operands, a built cell) is as if never begun, so that the room for all of it
is decided before the first (§6.2). A refusal by the loop follows the debit of the
entry that built the request (D23): the loop's step is no entry, pays nothing and
changes nothing. A refused print is therefore debited. `print-non-scalar` (and `-mid` and `-wide`) stops after 4 calls (main,
IO.print, the erased `R` and the Action applied to `k`, which built the request that
the loop then refused), `print-non-scalar-second` after 13, and a Book's Case over a
request after the entry of the function that holds it (5 in `book-print`, §8).
vm-expected.json freezes the four D20 counts, and §12's run controls the others.

**Fuel** counts entries: the requested Book function or Program `main`, every
Application, every Invoke (erased ones included), both applications of an Action,
and every continuation application, the terminal one included. Nothing else pays:
operand evaluation, constructors, lets, cases, RC, prims, validation, rendering and
the loop's performing of a request (its host call and its Base result) cost zero. Operands are evaluated before their call is debited. Fuel is a u32
independent of eval-cli's transition budget, so no claim compares equal numbers
across the two. Goldens run with 1,000,000; benchmarks with the u32 maximum,
4,294,967,295 (`deep-recursion` alone makes about 2 × 10^9 entries).
`calls` is the total of successful debits, so the initial fuel is `fuel + calls`.

**The boundary.** A run whose entries total `calls` completes with initial fuel
`calls`; with one unit less, its last entry stops with `Exhausted` kind 1 after
`calls - 1` debits, and at fuel 0 its first entry stops after none. The operand
check precedes the fuel test, so an ill-typed Enter is `HostFailure image` at
fuel 0 too. The Action's second application builds the request and is debited there
(D23), and `k` is a separate entry that the loop enters after the effect: when the
second application meets fuel 0, no request exists and nothing is written; when `k`'s
entry does, the effect's output is already written; a request that is dropped has still
paid for its entry. A Book has no loop and performs nothing, and the same debits apply:
`book-print` makes 5 entries (main, IO.print, `R`, the Action applied to `k`, and `got`,
whose Case refuses the request), at fuel 4 its fifth meets fuel 0, and at fuel 3 the
Action's second application does (§8). Eleven fuel run controls freeze each side (§12),
and four more, three of the Book case and the request target at fuel 0.

**Quantum.** When a debit makes `quantum` reach 65,536, the Enter step completes
(the new body is ready to Eval, or the request that an Action's second application
builds is ready to Return) and dispatch returns to `knot_main` with the whole state
committed. `knot_main` resets `quantum` to 0 and re-enters dispatch. The loop performs
a request in one Return-to-Top step, which ends with `Enter(k, [r])` pending and which
no debit splits, so the effect of a request runs exactly once. Re-entry never recurses,
allocates a frame or restores fuel; it is a Wasm-to-Wasm return and call. Test dumps
show a Yield event here.

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
pushes Top(phase 0) and starts with `Enter(FN, ordinals)`; it has no loop, so no request
is performed under it (Actions, below). Return to Top(0) describes the
result, drops `act` and halts with it, printing

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
never a truncated value (§12's four display run controls). The description is
decided before anything changes (§6.3): every word is inspected and then charged,
the tree is built in scratch, and only a description that has passed drops `act` and
prints its line whole. A refusal (`ill-typed`, `display`, a request, the room for
the text) stops the machine with `act` still owned, the result still held and nothing
written, and it leaves the same `calls` as the run held before the step. The result
is dropped after printing.

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
| 3 | The loop. If `w` is a request (class 5), perform its effect and enter its continuation, in this order. The refusals come first and change nothing (§6.3): inspect (§6) every operand over its whole extent, in operand order, before any is converted (§10); make D20's scalar check of every outgoing String or byte List; and decide the room that the conversion and the Base result `r` take (§10), all before the host call. Then drop `act` and set it to 0 (§6's table), convert the operands, call the host and build `r`; then `dup` the request's `k`, drop `w` (which releases its operands and, with the `dup`, leaves `k` owned by the step), and continue with `Enter(k, [r])`. The phase stays 3, so the answer of that entry returns to Top and is read the same way, and the loop ends only at an Emit or a Halt. The step is no entry (§7); one effect at most. Otherwise `w` must be an IO.OP Object, and a Halt's code a U32 and its message a String over its whole extent (§6); else `HostFailure image` (`ill-typed`), with `act` and `w` still owned. Emit ends with exit 0, its field unread, after `act` and `w` are dropped. A Halt's message is an outgoing String (§10): the code and then the whole message are inspected, and a message holding a non-scalar Char is refused as `HostFailure io abi` before `die` (D20), with `act` and `w` still owned and nothing written. Otherwise, the room for the conversion being decided with those checks, the VM drops `act`, converts the message, drops `w` and calls the host's `die` with the code and the message. |

`IO.pure`, `IO.bind` and `IO.die` are ordinary Base code; `IO.die` returns `Halt`
directly. An Emit is a value that ends the loop, not a request, and a request is neither an Emit
nor a Halt. Program images require the Unit, String and IO.OP representations.

**Actions and requests (D23).** `Foreign` builds an Action and performs nothing, and its first
(erased) application returns the Action itself. Its second application, to a continuation `k`,
builds a **request** and performs nothing either (§7). A request is an inert value of type IO.OP,
held like any other: only Top's loop reads it, and it performs exactly one request each time a run
returns one to it, the one the run answers in phase 3, and then enters that request's `k`. Every
other request has no effect, wherever it is: one that a let, an argument, a field, a capture or an
unselected branch drops is never performed, nor is one that an Emit holds, since an Emit's field is
unread. This is the seed's own model: its `io_step` applies the continuation, and the pure evaluator
answers a request that the loop then performs, while the seed builds every argument, so an unused
request is built and dropped. Goldens `keep-swapped` (`keep(-R,x,y) = y`: the request of
`m1(R, x => Halt{7,"unreached"})` is dropped, and the run prints `kept`), `keep-first`, `run2-flag`
(`pick` over a user Flag) and `book-drop` (a Book) freeze that on both seed lanes, and `spine`
(`R => k => m1(R, x => m2(R, k))`, IO.bind's shape) freezes the requests that do reach the
loop. Six goldens freeze the same for each place a request can be held, every one with a call-shaped
`main` (`main = run(IO.print(..), ..)`, since the seed crashes on a `main` that is itself a lambda, below):
`let-dropped-request` and `let-live-request` (bound by a let, dropped, and the live one returned),
`field-request-returned` and `field-request-dropped` (a field of a user `Box`, unboxed by a match and
returned, or dropped), `emit-field-request-dropped` (an Emit's field) and `capture-request-dropped` (a
closure's capture). Each prints its `live\n` (or `boxed-then-returned\n`) on both seed lanes, and the dropped
request of each is built and never performed. Run control `program-print-through-id` applies the Action to its continuation inside an argument
of a call (`run(m) = λ@R. λk. id(m(R)(k))`, whose answer only passes through `id`) and writes `x`
after 9 entries, and the pinned seed writes `x` for that source on both of its lanes.

**Where a request is read and where its entry is paid.** A request holds its operands and `k`
unread. Operand inspection (§6), D20's scalar check and the host call belong to the loop, when it
performs the request, and the loop reads `k` when it enters it, after the effect. So a dropped
request that holds an ill-typed String is no failure (`program-request-dropped-ill-typed`), and
one that holds a non-scalar String is no `io abi` and writes nothing (the golden `keep-non-scalar`:
native `kept`, where the Bun lane refuses the Char where it is built), while a request that is
performed reads its operands as before. The debit is the application's: the Action's second
application is an entry and pays where it builds the request, so a dropped request has paid for
its entry (`book-request-dropped`, `program-request-dropped-let`), and performing it costs nothing
(§7). Run controls freeze each: `effects` 1 and 12 entries for `keep-swapped`'s plan
(`program-request-dropped-argument`), and `inspect-continuation-target` writes `x` before the
loop reads a `k` that is an immediate.

**Where the seed refuses, and the VM with it.** The seed's boundary is the loop: an effect fires only
where the pure evaluator answers its request to the loop, so a request that is dropped never fires. A
request that a Case meets is where the seed's two lanes part, and they do not fail-stop alike (the goldens
and witnesses below; the native lane is the reference, and the VM follows it wherever its plan can):

| A Case over a request that | seed native | seed Bun | VM |
|---|---|---|---|
| names both Emit and Halt, no Default (witness `case-request-both-arms`; the seed's own test `tests/io/request_out_of_band.bend`) | fail-stop (`bend: runtime fail-stop`), exit 1 | fail-stop, exit 1 | `Unsupported vm effect` (`program-case-request`) |
| names one constructor beside a catch-all (goldens `case-request-emit-default-u32` prints `2`, `-halt-default-u32` prints `4`, `case-request-emit-default` prints nothing) | takes the catch-all, exit 0 | fail-stop, exit 1 | takes the Default of a plan that holds one (D24); a compiled plan holds none (below) |
| is only a catch-all or a binder (witnesses `case-request-default-only`, `-binder`) | exit 0, the request is never read | exit 0 | binds it as a value: no Case (D24) |
| names every constructor and a catch-all beside them, or reaches the catch-all only through a field pattern (witnesses `case-request-both-plus-default` and `-nested-default` print `3`; the Book `case-request-book-both-plus-default` yields `On{}`) | takes the catch-all, exit 0 | fail-stop, exit 1 (the Book prints its stuck term) | `Unsupported vm effect`: a table that names every constructor has no Default (§3), and a request matches none of its rows (`case-request-emit-default-u32-compiled` and `case-request-nested-default-compiled` for a Program, `case-request-book-both-plus-default-compiled` for the Book) |

So "fail-stops in every lane" holds of the first row alone, and the Bun lane agrees with the native lane on the
first and third rows. **D24 is the VM's rule for a plan that holds a Default.** A request matches no row, so a Case
takes its Default when its plan has one (a keys Case always does) and otherwise stops `Unsupported vm effect`, which is
the first row's answer and D4's refusal (§6.1); a binder or a lone catch-all holds no Case and never reads the request, so
it binds it as a value, and a plan may still hold a Case whose rows are all `none`
(`program-case-request-default-only`), which takes its Default. The three goldens freeze the second row's values by the
seed's native lane, each with the Bun lane recorded beside it (a fail-stop, exit 1, on all three); before D24 they were
witnesses, and D23 refused every such Case, a Default included, as a capability gap (DECISIONS entries 33 and 35,
finding 14). Their plans are hand-lowered (§1) witnesses of the plan-level rule, and no lowering emits their Default.
A plan holds a Default only where a row is absent (§3), and the checker of the nest increment (`campaign/nest` at
2a84a4f5) lowers a source catch-all on an algebraic type into a row for each constructor that no arm of the source names,
with the catch-all's body copied into it, and emits no Default; a lone catch-all or a binder lowers to its bare body, with
no Case, the third row's shape. (That checker refuses an `IO.OP<R>` parameter as `Unsupported parse parameter-type`, so
this was measured on sources over a user type of IO.OP's shape; the merged head of `campaign/literals-integ` at 9f98fb09
lowers these shapes the same way, DECISIONS entry 37.) The second row's sources therefore lower to the complete tables of
`case-request-emit-default-u32-compiled`, `-halt-default-u32-compiled` and `case-request-emit-default-compiled`, a source
of the fourth row's first shape is a complete table already, and the VM refuses each request where the seed's native lane
takes the catch-all: five run controls, `Unsupported vm effect` with nothing written, four Programs after 8 entries (three golden sources and
the nested one) and the Book of `case-request-book-both-plus-default` after 6. That is a recorded capability gap (D4: Unsupported, never Invalid, never a bound), and no rule of the VM
closes it, because a complete table has lost what the catch-all was for: the sources of `case-request-emit-default-u32`
(`Emit: 1 / _: 2`, native `2`) and of `case-request-both-plus-default` (`Emit: 1 / Halt: 2 / _: 3`, native `3`) lower to
one plan. So do those of `case-request-inner-default-only` (a native fail-stop) and of `case-request-nested-default`
(native `3`) where a checker accepts the latter's `_` after a field pattern: nest at 2a84a4f5 does for a constructor
sub-pattern, and the merged head refuses it after a literal one as `Unsupported check variable-pattern`, at check time and
before any image exists. The image can express the seed's answer: a Default that tests the slot again for the arms that the source
names after the catch-all takes a request as the native lane does (`case-request-both-plus-default-retested` and
`-nested-default-retested`, each `3\n` after 13 entries with one effect). Closing the gap is therefore a change of the
lowering, to emit that shape, or of §3, to admit a Default beside a complete table; the VM's Case rule needs neither. The
refusal of a request that a Case without a Default or any other read of §6 meets is unchanged, and no golden agrees with the
seed there: `program-case-request` is a Case in a Program, `book-request-rendered` and `book-request-field` the render of a
root and of a field, and `inspect-request-chr`, `inspect-request-prim`, `inspect-request-print` and
`enter-request-target` each other kind of read (§12). The pinned literals head reports `Unsupported check
variable-pattern` for every catch-all on an algebraic type (`_` alone, a binder, and `_` after a constructor arm, each
tried on a Flag: the witnesses `catch-all-lone`, `-binder` and `-after-arm`, which the seed runs), so those goldens'
plans are hand-lowered and the eval lane of each is observed (`Unsupported parse parameter-type`), not compared.
A `_` after key arms on a U32 or a Char is accepted (`default-hit`, `case-char`) and is not about requests.

**The seed's crash is `main`'s form, not a let.** The seed crashes on a Program whose `main` is itself
`R => k => ...`, whatever the body: both lanes exit 1 with no output, native `bend: memory fault
(machine stack overflow?)` and Bun a TypeError (the witnesses `main-lambda-print`, `-continue`, `-halt`,
`-let` and `-nolet`, whose bodies print, continue, halt, hold a let and hold none). A request bound by a
let, held by a field, held by an Emit or captured runs on both lanes and agrees with D23 once `main` is a
call: the six goldens above freeze it, and `let-dropped-request` is `main-lambda-let` with the lambda moved
from `main` into a helper. No VM rule can agree with a crash of `main`'s form, none is owed one, and it is no
value. The plan-level run controls that build `main` as `λ@R. λk. body` (`program-request-dropped-let`,
`program-request-in-emit`, `program-case-request` and most of the D23 and D20 controls) freeze §7 and §8 by
literal review and make no claim about the seed; the call-shaped goldens are the seed-witnessed twins of
those that hold a request in a let, an Emit or a dropped argument.

**A Book entry never reaches the loop (D22, D23).** A Book invocation has no loop: its Top frame is
phase 0, which describes the result and halts. No request is performed under it, whatever it holds,
so no operand is read, converted or checked for D20, no host is called and nothing is written. A Book
may build, store and drop requests (`book-request-dropped`, and the golden `book-drop`, where the seed
runs a Book that applies `IO.print` to a continuation and drops the request); one that reaches a read
stops `Unsupported vm effect`, D4's refusal, never `Invalid` and never an effect nobody requested: a
Case over a request after 5 entries (main, IO.print, `R`, the Action applied to `k` and `got`, in
`book-print`, and the same for `IO.args`; 6 when an `id` call builds the String first), and a
result that is or holds a request, when rendered, after 5. D22's ordering question, whether the refusal
precedes the whole-extent inspection and D20's check, is settled by there being nothing to
inspect: the print of an ill-typed or a non-scalar String is refused by the Case, as
`Unsupported` and never `HostFailure` (`book-print-ill-typed`, `book-print-non-scalar`). The
pure `got(k(Unit{}))` evaluates after 3 entries, an Action built and dropped after 2, one applied to its
erased `R` after 3, and a request built and dropped after 4.

**No host call and no write are frozen.** Every Book control that stops at a request freezes
`stdout` empty and `effects` 0 beside its cause and `calls`, and so does `book-request-dropped`,
which builds one and ends. D23's Program controls freeze `effects` too: 1 where the loop performs the
one request that a run returns (`program-request-dropped-let`, `-argument`, `-ill-typed`), 0 where it
returns none (`program-request-in-emit`) or a refused one (`program-case-request`, `inspect-request-print`);
the three Default controls (`program-case-request-emit-default`, `-halt-default`, `-default-only`) also perform
none, since D24's Default takes the request unread. The reference evaluation reports
both on every Book outcome, a Halt included (§12): `stdout` is the bytes written, and `effects`
the host calls made, counted where the call would be, at the loop after D20's check and just
before the write. A VM's harness MUST compare both: `stdout` against what its host
wrote, and `effects` against the host calls that the run made (the `knot_io` calls of vm-core's
host trace, the effects that vm-model's model performs), which is the only observable of a call
that writes nothing (`IO.args`, whose control freezes no `stdout` that could differ). A Book that
wrote or called the host has performed a request, whatever its cause.

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
Big result is allocated before the operands are dropped. The order is that of the
effects: the room for every cell of a result is decided before the first is
allocated, so that a prim whose result does not all fit stops with none of it built
(§6.3). Prims still without a
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
comes from its pinned declaration). An Action applied to its continuation builds a request and
reads nothing (§7). Top's loop performs the request (§8, D23), which only a Program entry has,
and a Book never does (§8, D22). Performing it inspects (§6) every
operand before it converts any, a String or a byte List over its whole extent,
so an ill-typed cell anywhere in it halts as `ill-typed` even after a non-scalar
Char or a byte above 255. Then it
converts its operands, calls the host, builds the exact pinned Base Result, pair
and handle view, and the loop enters `k` with it. The host call is the step's last
change and nothing that the machine can refuse follows it (§6.3): after D20's check
and before the call, the step decides the room that its conversion (the allocator
blocks of §5) and the cells of the Result need, so that a request that cannot be
performed is refused with no call made and nothing written. `IO.print`'s Result is
the Unit immediate and takes no cell; a foreign whose Result allocates reserves its
cells before its call (vm-io owns those foreigns). Outgoing Strings must be Unicode scalars and are encoded as
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
result that §8 cannot describe and a request that is inspected, rendered or otherwise consumed as data (D23), a Case's
Default aside (D24); a broken invariant is a defect. A refusal, a halt or an exhaustion of any of these
kinds is a stop, and a stop is atomic (§6.3): it is reported with the meters, the output and the effects that the
run held before the refusing step, less the debit that an Enter's step 1 had paid when its step 2 or 3 stopped. A timeout or
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
D20 refuses (below). The effect trace is the requests that the loop performs, in order,
and a request that a run does not return to the loop is no part of it (§8). Another lane's
exhaustion never excuses the VM. A VM that exhausts early, corrupts a result or
reports an engine trap as a budget fails. Unsupported, timeout, unknown failure
and a missing lane are neither Exhausted nor agreement. An Unsupported outcome is
D4's refusal of a form Knot does not handle: a recorded capability gap, never a
bound. Round 12 recorded one that a hand-written plan could hold and Knot could not lower, a Case with a Default
over a request, where the seed's native lane picks the Default. D24 gave the VM the native lane's value for a plan that
holds the Default (§6.1, §8). A compiler that lowers a source catch-all into a row for each remaining constructor emits no
Default, so for compiled programs the gap stays open and §8's table records it (round 13, review round 1). Expected values
are never regenerated from a candidate VM.

**Non-scalar output (D20).** The program's own value decides it, never a seed
lane. The reference evaluation of the plan ([evaluate.py](evaluate.py), §6–§10 on
values) yields the Strings a Program passes to output effects, in order: those of the
requests its loop performs, and never the String of one that is dropped. It
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
`a\n` and refuses) build a surrogate without printing it and agree with the seed, and so does
`keep-non-scalar`, whose print of a surrogate is a request that `keep` drops (native `kept\n`; the
Bun lane refuses the Char where it is built and writes nothing): D20's check belongs to the loop,
which never meets that request.
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
`foreign-print`, `io-bind`, `non-scalar-code`, `non-scalar-unprinted`, and D23's `keep-swapped`, `keep-first`,
`run2-flag`, `spine` and `keep-non-scalar`, the six of round 12 with a request in a let, a field, an
Emit or a capture, and the three of D24 with a Case with a Default over a request (§8); and D20's
refusal for `print-non-scalar`, `print-non-scalar-mid` and `print-non-scalar-wide`,
with no output, and for `print-non-scalar-second` after `a\n`. For the Programs before D23
the eval lane is not excused but unavailable: both literals `eval-cli`
and `check-cli` report `Invalid parse function-result` for
`def main() -> IO(Unit)`, a program the seed runs. Under D4 that should be Unsupported; it is recorded as observed, not
relabelled, and their plans follow §1 by hand. Fourteen goldens (`list-head-match`, and those of D23, round 12 and D24 that hold a request) declare helpers with an
`IO(Unit)`, `IO.OP<R>` or `List<Flag>` parameter, which both heads answer `Unsupported parse parameter-type` (D4's own
answer), and follow §1 by hand as well. `io-bind`, `non-scalar-unprinted`
and `print-non-scalar-second` keep Base's `IO.bind` (and `IO.pure`) unspecialized,
so their `A`-typed nodes are `none`.

**A Book's unavailable lane.** A Book whose form a pinned head cannot check is
unavailable the same way, and Unsupported is still never a bound (above). `chr-pattern`,
the first tags-mode Case on Char (`case Chr{x}`, on an immediate Char and a Big one), and
`list-head-match`, S's Case on the head bound from a `List<Flag>` parameter, run on the
seed (`True{}` each). The golden's lane is the literals head, whose `check-cli` and
`eval-cli` both exit 3 for them, with `Unsupported check char-constructor-pattern` and
`Unsupported parse parameter-type`; the closures head answers otherwise (`Unsupported
lex literal`, `Unsupported parse declaration-form`) and is not consulted. `book-drop`, a Book that
applies `IO.print` to a continuation and drops the request (`On{}` on both seed lanes), is declared
`Unsupported parse parameter-type` too, for its `IO(Unit)` parameter. The golden's
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
  head's `check-cli` core display (save the three whose lane's head answers Unsupported,
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
- all 211 refusals of §4 with their frozen reasons (124 byte-level, 9 at the limits, 78 plan-level), each resource limit
  `Exhausted` kind 2 on one side and malformed or invalid on the other, its eight
  admitted plan controls and `arity-at-limit`; `first-code` and `list-head-match` also
  equal the independent lowering of a `check-cli` display written by hand in the
  literals head's grammar, because no pinned head checks a `List<T>` parameter;
- 135 admitted **run controls** (`check-spec.py run_controls`), each frozen with
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
  vm-io's. Forty-two effect controls (`effect_controls`) freeze
  D23 (§8), D24 (§6.1), D20 on a Halt's message and the UTF-8 of a scalar. In a Book image, `got` returns what an IO.OP
  carries and `IO.print("x")` is applied to its erased `R` and to a continuation `k`, which builds a
  request that `got` receives: `book-print`, `book-print-continuation-call` (`k` a function) and
  `book-print-twice` (the reviewers' bookio-1, bk-print and bookio-2) stop
  `Unsupported vm effect` after 5 calls, when `got`'s Case inspects the request, writing nothing (each of
  these Book controls freezes `stdout` empty and `effects` 0, `fuel-book-effect-short` too);
  `book-print-non-scalar` (a surrogate) too, so a Book never checks a request's String for D20,
  `book-print-ill-typed` (`"a"` then `id(λ)`) after 6, so it never inspects it either, and `book-args`
  (`IO.args`, foreign 0, of type `IO(List)`) after 5, whatever the foreign id. `book-print` at fuel 5
  (`fuel-book-effect-exact`) is refused after its 5 debits; at 4 (`fuel-book-request-short`) `got`'s entry
  meets fuel 0 and stops `Exhausted` kind 1 after 4; and at 3 (`fuel-book-effect-short`) the Action's
  second application does, after 3, so the debit is the application's (§7). The pure `got(k(Unit{}))`
  (`book-continuation-called`) evaluates `Evaluated 8 1 On{}` after 3, an Action built and dropped
  (`book-action-dropped`) after 2, one applied to its erased `R` (`book-action-erased`) after 3, and a
  request built and dropped (`book-request-dropped`) after 4, with `effects` 0. A request is dropped, and
  no effect follows, wherever it is held: by an Emit's field (`program-request-in-emit`, `Emit{request}`,
  exit 0 after 6, nothing written); by a let, the live request that the Program returns then performing
  alone (`program-request-dropped-let`, `live\n`, `effects` 1, after 10, the dead one's three entries
  paid); by an argument of a call (`program-request-dropped-argument`, `keep-swapped`'s plan, `kept\n`,
  `effects` 1, after 12); or holding an ill-typed String, which the loop never reads
  (`program-request-dropped-ill-typed`, a closure tail, `kept\n`, `effects` 1, after 12).
  `program-request-in-emit`, `-dropped-let` and `-dropped-ill-typed` build `main` as `λ@R. λk. body`, a form
  that crashes the seed (§8): they are literal review with no seed claim, and the call-shaped goldens
  `emit-field-request-dropped`, `let-dropped-request` and `keep-non-scalar` witness that the same holds. A request that
  any read meets stops `Unsupported vm effect` (§6), whatever the type and before an ill-typed
  test: a Case without a Default over the answer in a Program (`program-case-request`, `Emit{got(IO.print("x")(R)(k))}`,
  after 7, nothing written);
  a Book's result and a field of it, rendered (`book-request-rendered`,
  `book-request-field`, after 5); a request handed through `id` to a Chr operand (`inspect-request-chr`,
  after 5), a prim operand (`inspect-request-prim`, `U32.add`, after 6)
  and an Enter's target (`enter-request-target`, after 5, the Enter
  refused before it is debited, and with fuel 5 the same Enter meets fuel 0 and is refused all the same,
  `fuel-zero-request-target`); and a String whose tail is a request, which the loop reads whole when it
  performs the print (`inspect-request-print`, after 10, nothing written). A Case with a Default
  takes the request instead (D24, §6.1): the same Case with a Default beside an Emit row, a Halt row or no row ends
  exit 0 after the same 7 entries, nothing written and `effects` 0 (`program-case-request-emit-default`, `-halt-default`
  and `-default-only`, whose Default's Flag goes into an Emit's unread field), and so does a Book's Case that names
  Flag, handed the request through `id` (`case-request-default-at-flag`, `Evaluated 8 0 Off{}` after 6), and a Book's keys
  Case, which has a Default always (`case-request-default-keys`, the same line after the same 6 entries); the values
  are the seed's in the goldens `case-request-emit-default-u32` (`2`), `-halt-default-u32` (`4`) and
  `case-request-emit-default` (no output). Lowered as a compiler lowers those three sources and the fourth row's nested one
  (a row for each constructor, the catch-all's body copied, no Default), the same Cases refuse the request:
  `Unsupported vm effect` after 8 entries with nothing written and `effects` 0 (`case-request-emit-default-u32-compiled`,
  `-halt-default-u32-compiled`, `case-request-emit-default-compiled` and `case-request-nested-default-compiled`), and so does
  the Book of the fourth row (`case-request-book-both-plus-default-compiled`: `got` names Emit and Halt, `go` hands it the
  request) after 6; and a
  Default that tests the slot again for the arms named after the catch-all takes the request as the native lane does,
  `3\n` after 13 entries and one effect (`case-request-both-plus-default-retested` and `-nested-default-retested`). The
  same Action prints under a
  Program entry from inside an argument of a call (`program-print-through-id`, whose source the seed
  prints `x` for on both lanes), `x\n` after 9; a Halt whose message is a lone surrogate (`halt-surrogate`)
  stops `HostFailure io abi` before `die` after 3; and one whose message is scalar
  (`halt-scalar`, `x` and U+1F600) ends with `halt` 1 and that `message` after 3, the
  reference evaluation's view of a `die` whose exit status and stderr are the host's
  (IO-ABI.md). A scalar String is written as canonical UTF-8 (§10): `print-utf8-lengths` prints
  U+0024, U+00A2, U+20AC and U+10348 and `print-utf8-boundaries` the edges of every length (U+007F,
  U+0080, U+07FF, U+0800, U+D7FF, U+E000, U+FFFF, U+10000, U+10FFFF), each after 5 entries; the
  expected text is Python's own encoding, and the pinned seed writes the same 11 and 26 bytes on
  both lanes. Three key controls (`key_controls`)
  freeze §3's key: `pick` answers `On{}` from a key Branch at 0xffffffff for the U32
  and the Char `4294967295` (`key-max`, `char-key-max`) and `Off{}` from its Default for
  0xfffffffe (`key-max-miss`), each after 2 calls. Twenty-four **atomic controls** (`atomic_controls`) pin §6.3 where
  the reference evaluation can see it: a stopped run reports what the run held before the refusing step, and the same run
  given exactly the fuel that it has spent, `fuel = calls`, reaches the same stop, since a refused step pays nothing.
  Eighteen are twins that stop before any effect, each the run of an existing control or golden frozen again at that fuel and
  with the `stdout` and `effects` that its first freeze left out (a Book writes nothing and calls no host; a Program that
  stops before its first request has done neither). A Chr, a Succ, a word prim, a Case and a rendered field read an
  ill-typed word (`atomic-ill-typed-chr`, `-succ`, `-prim`, `-case` and `-render`, after 2, 2, 3, 3 and 2 entries). A Succ,
  `Nat.add` and `Nat.mul` have a result above 2^32-1 (`atomic-nat-succ-range`, `-add-range` and `-mul-range`, the plans of the
  goldens `nat-succ-range`, `nat-range` and `nat-mul-range`: `NatRange` after 2 entries, main and the callee, `Nat.is_gt` never
  entered). Return to Top refuses a Halt whose code, or whose message, is ill-typed and an IO.OP that is a closure (`atomic-halt-code`,
  `-halt-message` and `-io-op-closure`, `ill-typed` after 4), and a Halt whose message holds a surrogate (`atomic-halt-non-scalar`, `io abi`
  after 3). The loop refuses a String with a surrogate (`atomic-print-non-scalar`, `print-non-scalar`'s plan, `io abi` after 4),
  one with a scalar before it, of which nothing is written (`atomic-print-non-scalar-mid`, after 4) and one whose tail is
  ill-typed (`atomic-print-ill-typed`, after 5), each with no host call. A Case refuses a request (`atomic-case-request`,
  after 7), so does a Book's render of one (`atomic-request-rendered`, after 5), and a display exceeds its bounds
  (`atomic-display-visits`, `display` after 1). Four stop after
  an effect and freeze the bytes and the host call that it made: `atomic-print-then-non-scalar` (`print-non-scalar-second`'s plan:
  `a\n`, 1 effect, `io abi` after 13), `atomic-print-then-ill-typed-continuation` (`inspect-continuation-target`'s plan: `x\n`, 1 effect,
  an ill-typed `k` after 7), `atomic-print-then-io-op` (`x\n`, 1 effect, a closure that `k` answers through the identity as its
  IO.OP, after 8) and `atomic-print-then-nat-range` (`x\n`, 1 effect, `Succ{4294967295}` in `k`, `NatRange` after 7). Two order a word's
  inspection before its charge (§8): `Pair{n, w}` with the Nat word n = 1,048,574 has charged 1 + 1,048,575 visits, the whole
  bound, when it reaches `w`, so a Flag there is the 1,048,577th visit (`atomic-display-leaf-charged`, `display` after 1) and a
  closure that the identity hands there as a Flag is refused as `ill-typed` first (`atomic-display-leaf-ill-typed`, after 2), for a
  word that is not inspected is no visit;
- seven admitted code-list controls, each decoding back to its plan through the
  decode CLI's JSON text: a surrogate pair beside U+1F600 (two constants, never
  merged), each alone, a lone surrogate, U+10FFFF, U+110000 and the u32 maximum;
  and `encode`'s refusal of a String constant spelled as text;
- 137 codec mutants and 4 source mutants killed through a changed image, a decode
  that differs from its plan, a changed refusal, a refused admitted control, a
  changed describe, invocation or argument verdict or a changed observation, and 119 evaluator mutants
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
  instead of the frozen one, the rest by an admission. Three more, of a type record's constructors
  (round 12, review finding 3), are a count refused where it exactly fills the constructor table (by
  `opcode` and every other control of a valid image), the first-constructor check removed (by
  `type-grouping`, which the next check refuses as `noncanonical` instead) and the sum of the counts
  removed (by `type-count-short`, which a constructor's tag refuses instead). No mutant restores the late
  size check as it was, sizing the list from the raw count: it would allocate 32 GiB at `type-count-max`, which is a host's
  memory and no verdict, and a crash is no kill. The audit below omits the check with the list sized by the constructor table,
  so that control is refused as `constructor grouping` instead; and the gate holds its own peak memory under 4 GiB (a host with
  the memory would otherwise pass while holding 35 GB). Forty-eight more (round 13, review
  findings 1 to 3) each omit one clause that no control had pinned, and each dies by the control that breaks that clause
  alone: a keys row may repeat, a Construct may be nullary, an Invoke's operand count is unchecked (any, for a live arrow
  alone, for an erased one alone), a Case's slot may be any type, captures may repeat, a tags Case on any type, a keys
  Case on any type, a tag table of any length, a Program with no `main`, a call whose operands are not checked against the
  callee, an Invoke whose operand is not checked against the arrow, a keys row whose first slot is not the depth; an empty
  name, a name whose length word is unchecked, a repeated name, a shared child, an unreachable node, an opaque type with a
  payload, a named arrow, a scalar of any width, a record of one word, the type, constructor, constant and function length
  words; each digest word alone, each unused byte of a name alone, the last one only; and seven of UTF-8, which read a name
  as opaque bytes after a check of part of Unicode's table 3-7 (without the overlong forms, the surrogates, the range, the
  cut sequences or the stray continuations, without the first three, and ASCII only, which the two admitted names kill), and
  a decoder that accepts surrogates alone (`rejected` reads an encoder's refusal as a plan that no image encodes). Where
  removing a bound only makes the reference raise (the entry kind and the constant kind index a table), the mutant reads the
  kind modulo the table, so that the refusal changes (`decoder-entry-kind-mod-2`, `decoder-constant-kind-mod-4`).
  **Every refusal of the decoder and the validator, and every clause of its test, is accounted for** (`statement_audit`):
  the gate omits each of the codec's 100 `raise` statements, `fail` calls and `limit` calls in turn, as above, and each
  operand of the `or` in the 78 tests that have one (178 omissions; the omission of the constructor-count guard also sizes
  its list by the constructor table, so that no run asks for 32 GiB), and requires that a frozen image, refusal or verdict
  changes (136 do) or that the omission is listed with what holds it: 33 make the reference raise on the control that pins
  them (four refusals, `name index`, `child offset`, `node record` and `constant index`, and twenty-nine clauses, each a
  bound that keeps an index or a key inside its table; §11 does not count a raise as a kill, so the gate requires the raise
  on that control and that nothing else kills them); 5 are unreached, each with its argument (`constructor order`, the
  decoder's closing `opcode`, and the validator's `standalone {op}`, `type index` and `unknown node`, which earlier steps
  refuse first); and 4 are the encoder's input checks (`u32_list`, its two clauses, and an unknown plan node;
  `text_spelling` holds the first, and no decoded plan holds a form outside the table). It does not drop an operand of an
  `and`, a comparison's boundary or what a test computes. Three of round 12's reviewer mutants remove a bound
  whole and raise by construction (the entry kind, the constant kind, and the block of `tag case on a non-data type`, whose
  `return` goes with it): `CRASH_HELD_MUTANTS` requires that each survives every frozen image and raises on its
  control (`entry-kind`, `constant-kind-unknown`, `tag-case-on-opaque`). Twenty-three rule mutants of
  `check-spec.py` itself are killed the same way, the ten of them for §4 step 5 (below): `rejected` reporting a limit as
  `HostFailure image`; an eval lane excused by any Exhausted, or by a documented
  bound whose budget it does not pass; display steps counted as visits;
  transitions that omit materialization; a D20 golden whose `calls` are not
  checked; an unavailable Book lane whose declared line is not checked or whose cause
  is not named; a declaration kept where check-cli prints a core; a Book without a
  core that declared none; a witness (§8) whose source hash, lane bytes or literal review goes
  unchecked, each by its own frozen refusal; and, for each clause of §4 step 5, `piecewise_rejected` without that
  clause (`canonicality-without-*`), each by the control that breaks it alone (`canonical_differential`: the clauses and
  re-encoding decide 5,797 images alike, the controls, the admitted images, the goldens, 480 seeded layouts and 4,875
  perturbations of a word among them, and 527 of them are noncanonical).
  Four survive every golden and die by a fuel control: fuel that never runs
  out, fuel that runs out one entry early, the fuel test before the operand check,
  and a free terminal continuation. A request's debit paid by the loop after its effect, not
  where the Action's second application builds it (`debit-at-perform`), dies by the D20 goldens'
  frozen `calls` (§7), by `fuel-action-short` (its effect is written before the debit meets fuel 0),
  by the print inspection control, which counts it after 5 calls, and by the controls that drop a
  request. A
  predecessor narrowed to 31 bits dies only by `nat-case-big`. Eighteen read less
  than their inspection extent, and exactly as much on a well-typed word, so they
  survive every golden and each dies by the inspection controls of its own point and by
  no other (a Halt's message unread also by the two Halt controls that carry one): Chr passing its operand through; Succ passing an Object, or
  a Closure; each move prim returning its operand unread; `append` moving `b`
  unread, or copying `a`'s Char words unread; `length` and `reverse` leaving the
  Char words unread; `is_empty` reading one cell; `eq` stopping at the first
  difference, or reading one list only one cell past the other's length (either
  way round); a Halt's code, or its message, unread; and a print that checks each
  Char as it reads it. Twenty-one more of that kind, read less or read too early, were the points that
  no control reached before the review of round 9, and each dies by the controls of its own point and
  by no golden: a tag-mode Case that admits a closure for its scrutinee (at a Flag, a Nat or a
  Char), one that reads a Char scrutinee unread, an Object of another type, a Nat that is no word or
  an immediate beyond the constructors, and a key-mode Case that reads its scrutinee unread (at a
  U32 or a Char, and at a Char alone); a U32 prim with its first operand unread, or its second (the
  shift's amount included), a Char prim with its first, `Char.is_eq` with its second, a Nat prim with
  its first, or its second, and `show` with its operand; a rendered closure admitted; an Enter that
  takes an immediate for an Action, or an Object for its target; a request's continuation read when the
  request is built, or by the loop before its effect, or left unread and taken for the terminal
  continuation; and a last word that is no IO.OP taken for `Emit`. Four more, of §10's UTF-8 of a scalar (the one-byte edge, the two-byte
  lead, and the edges of two and three bytes), die by the two print controls. Thirty-three more,
  of D23 and D24, a Halt's message, keys and the debit, die
  by the controls above: the eager rule of round 10, performing at the Action's application (by ten goldens,
  `keep-swapped`, `keep-first`, `run2-flag`, `keep-non-scalar`, `book-drop`, `let-dropped-request`,
  `let-live-request`, `field-request-dropped`, `emit-field-request-dropped` and `capture-request-dropped`, and
  twenty-four run controls); a request performed although it is dropped, by the function that received it (by
  nine goldens, those but `field-request-dropped`, whose function receives the Box and not the request, and
  `program-request-dropped-argument`, `program-request-dropped-ill-typed` and `book-request-dropped`) or by the
  let that bound it (by `let-dropped-request`, `let-live-request`, `program-request-dropped-let` and
  `book-request-dropped`); a loop that enters `k`
  before it performs the effect (by `fuel-continuation-short`, `inspect-continuation-target`,
  `inspect-print-after-surrogate`, `inspect-request-print` and the four D20 goldens' `calls`); a Case
  without a Default that picks an arm of a request, or takes it for an ill-typed word (each by the seven Book
  controls that hand `got` a request, `program-case-request` and the five `-compiled` twins); a request taken for an ill-typed word where a
  String or a result is read (by `book-request-rendered`, `book-request-field` and `inspect-request-print`);
  D24's rule, that a Case takes its Default over a request: refused, as D23 refused it (by the three
  goldens of a Case with a Default, the three Default controls, `case-request-default-at-flag`,
  `case-request-default-keys` and the two `-retested` plans), picking a row and not the Default (by the goldens
  `case-request-emit-default-u32` and `-halt-default-u32`, which print 1 and 3 for 2 and 4, by those two controls and by the
  two `-retested` plans), taken only at IO.OP (by those two
  controls) or not by a keys Case (by `case-request-default-keys` alone); a request taken for an ill-typed word at a
  scalar (by `inspect-request-chr` and `-prim` alone) or at an
  Enter's target (by `enter-request-target` and `fuel-zero-request-target`); an Enter that tests fuel before it
  reads a request (by `fuel-zero-request-target` alone); a rendered field that admits a request (by
  `book-request-field` alone); a request's operands read when it is built (by `book-print-ill-typed` and
  `program-request-dropped-ill-typed`) and D20's check made then (also by `keep-non-scalar`, `book-print-non-scalar`
  and `print-non-scalar-second`); a loop that refuses its request (by every Program golden that prints), performs
  only the first (by `spine`, `io-bind`, `non-scalar-unprinted` and `print-non-scalar-second`) or performs the
  request that an Emit holds (by `program-request-in-emit` alone); a Book that runs the loop (by
  `book-request-rendered` alone), refuses where it builds the request, D22's rule of round 9 (by `book-drop`
  and the Book controls that build one), enters `k` without the effect (by fourteen Book run controls that build a request, not by `book-drop` or
  `fuel-book-request-short`),
  or refuses where it builds the Action or applies it to its erased `R` (by `book-drop`, `book-action-dropped`
  and `book-action-erased`); a Halt message never checked (by `halt-surrogate` alone), refused whatever it holds
  or above ASCII (by `halt-scalar` alone), checked as it is read (by
  `inspect-halt-after-surrogate` alone) or before the code
  (by `inspect-halt-code-first` alone); a key at 0xffffffff that is absent (by `key-max`
  and `char-key-max`) or a wildcard (by `key-max-miss` alone); and a refused print
  whose debit is refunded (by the D20 goldens' `calls`). Twenty-two more (round 14, §6.3) mutate before they refuse, and each
  dies by a changed observation of a control of the rule that it violates: the gate requires that at least one of the atomic
  controls (the 24 `atomic-*` controls and the three `fuel-zero-*` controls of a refused Enter, `-ill-typed-invoke`, `-ill-typed-phase`
  and `-request-target`, which are the same twin) changes under each. Eight spend an entry at a refusal (a `NatRange`, an ill-typed word, a Case over a request, a read of a
  request, D20's check, a display bound, and an Enter that pays its debit before it checks its operands or its request); six test
  fuel before a refusal that no fuel test precedes (the same sites but the Enter's); five change the output or the effects before their
  check (an effect counted before D20's check or before the String is inspected, a scalar prefix written before the refusal, a description
  whose head is written before its words are inspected, and a visit charged before its word is inspected); and three undo or defer (a
  stop that discards what earlier steps wrote, and a `NatRange` or an ill-typed word that is reported at the next entry). Nine survive
  every golden and every run control outside that set and die by it alone: the three `nat-range-` mutants, `ill-typed-tests-fuel`,
  `request-read-tests-fuel`, `d20-refusal-tests-fuel`, `display-refusal-tests-fuel`, `effect-counted-before-scalar-check` and
  `describe-charges-before-inspecting` (by `atomic-display-leaf-ill-typed` alone). The other thirteen die by earlier controls that freeze
  `calls`, `stdout` or `effects` as well, and DECISIONS entry 38 lists the kills of each, as measured;
- 15 **seed witnesses** (`golden/witnesses.json`, `check-spec.py witness_controls`): sources that §8 cites
  and no golden can carry, each re-run on both seed lanes (three also through the literals head's check-cli) and held
  to its source's hash, to its frozen exit, stdout and stderr, and to the review of its exit and stdout that
  was written before the bytes were frozen. Five show that the seed crashes on a `main` that is itself a
  lambda (`main-lambda-print`, `-continue`, `-halt`, `-let` and `-nolet`); three on a Case over a request that
  holds no Case with a Default beside a constructor row (`case-request-default-only` and `-binder`, which
  read nothing, and `-both-arms`, which fail-stops in both lanes; the three that D24 promoted to goldens are
  `case-request-emit-default-u32`, `-halt-default-u32` and `case-request-emit-default`); three (`catch-all-lone`, `-binder` and `-after-arm`) that both lanes run a catch-all on
  an algebraic type that the literals head refuses as `Unsupported check variable-pattern`; four (round 13, review round 1)
  on a catch-all for which a compiled plan has no place (`case-request-both-plus-default`, `-nested-default`,
  `-inner-default-only` and the Book `-book-both-plus-default`): the native lane takes it, printing `3`, `3` and `On{}`,
  and fail-stops only where the catch-all is inside the Halt arm; the plan of the first is the complete table of
  `case-request-emit-default-u32-compiled`, and that of the second, where a checker accepts its source, the nested table of
  `case-request-nested-default-compiled`, which is also the plan of the third (§8), and that of the fourth, a Book, is
  `case-request-book-both-plus-default-compiled`; the VM refuses all three. Three frozen
  refusals of the comparison (a source that drifted, a lane that drifted, a lane that contradicts its
  review) are held by three rule mutants. A witness is evidence for the text and never a VM expectation:
  vm-model and vm-core do not read it;
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
