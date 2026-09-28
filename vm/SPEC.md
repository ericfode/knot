# `knot-image-1` / `knot-vm-1`

Status: normative contract for the VM-first route, 2026-09-27. This increment
freezes inputs and observations; it implements neither a VM nor a compiler.
`VM-DESIGN.md` at `454bf30` and campaign decisions D14–D18 select the design.
`DECISIONS.md` supplies the remaining precise wording for coordinator review.
The literals core is pinned at `2ea222e7a832445a764f6ab1852b85aeaad11820`;
the closures core at `a1d68911d5fafe0c1033e8d5349b206e6136b29a`.
`oracles/manifest.json` identifies unmodified snapshots of those independent
evaluators. Neither snapshot is an integrated literals-plus-closures compiler.

MUST denotes a conformance condition. Integers in this document are unsigned
unless stated otherwise. Arithmetic used to validate sizes MUST detect overflow
before narrowing. A word is four bytes. `none = 0xffffffff`.

## 1. Image boundary and erasure

An image is an encoding of a completely checked, resolved core Book. Encoding
does not evaluate bodies, specialize generics, defunctionalize, insert ownership
instructions, or lower to ANF/CPS. The source checker remains responsible for
types, quantities, termination and proofs. A well-shaped image alone is not
evidence of a checked source program.

The encoder visits types, constructors and functions in the checked Book's
order. It drops erased parameters, constructor fields, let initializers/binders
and captures, including their expressions. A dropped let becomes its body.
It projects surviving lexical levels to contiguous slots. An erased lambda
still exists and is invoked with zero live arguments. Type/proof tokens and
source locations have no encoding. `Sequence` is a traversal container, not
an expression: flatten it at its containing list or reject an unexpected one
as an encoder InternalFailure. No unchecked core node may pass through.

`Value`, `Construct`, `Reference`, `Application`, `Let`, `Case`, `Branch`,
`Literal`, `Intrinsic`, `Default`, `Closure`, `Invoke` and `Foreign` are the
entire node grammar. `Branch` and `Default` occur only as Case arms.
`Foreign` denotes a recognized hash-pinned leaf, never arbitrary host code.
An unsupported source form or reachable leaf is `Unsupported`, before any
image is emitted. A malformed serialized image is `HostFailure image`, never
source `Invalid` or permission to execute unchecked nodes.

The future encoder is `src/image.bend`; its exhaustive match and checked codec
proof are separate work. `serializer.py` encodes hand-written records only.
It does not parse Bend or implement core evaluation.

## 2. File layout

All words are little-endian u32. All offsets are **absolute word offsets from
the beginning of the image**, not byte addresses, node indices or VM pointers.
Only relocation to VM memory multiplies an offset by four. No path, timestamp,
host endianness or allocation address appears in an image.

The header is 24 words:

| Word | Meaning |
|---:|---|
| 0 | `0x474d494b` (bytes `KIMG`) |
| 1 | version, exactly 1 |
| 2 | total word count, including header |
| 3 | entry kind: 0 Book, 1 Program |
| 4 | default entry function index; must exist and be named `main` |
| 5–10 | offsets of types, constructors, functions, constants, nodes, names |
| 11 | reserved, zero |
| 12–15 | representation type indices: Nat, U32, Char, String; `none` if absent |
| 16–23 | pinned Base SHA-256 bytes, packed into eight little-endian words |

The Base digest is the seed's `bend2/base.bend` digest in `registry.json`.
Even a Book with no Base types carries this registry identity. It authorizes
only identities listed in that registry; a familiar source spelling is not
an intrinsic or foreign authorization.

Sections occur in header order, adjacent, with no padding or trailing words.
Each starts with a record count, followed by that many records. Each record
starts with its total length in words, including its length word. Zero lengths,
overlap, gaps, wraparound, reserved nonzero bits and unused trailing data are
malformed. A section count can be zero. The first section begins at word 24.

Below, the record's initial length word is implicit. An index is the zero-based
record position in its own table. Lists are preceded by their element count.

| Table | Record payload |
|---|---|
| Type | `kind, name, a, b` |
| Constructor | `type, tag, name, n, field_type[n]` |
| Function | `name, result_type, arity, slots, body_offset, parameter_type[arity]` |
| Constant | `kind, n, data[n]` |
| Node | `opcode, result_type, operands...` (next section) |
| Name | `byte_length, packed_utf8[ceil(byte_length/4)]` |

Names are nonempty canonical UTF-8, no NUL, unique by bytes; final unused bytes
are zero. Name indices are interned in first-use order: types, constructors,
functions. No normalization of Unicode spelling occurs. Names are observations,
not lookup authority for primitive recognition. Function names are unique.

Type kinds: 0 algebraic (`a=first constructor`, `b=constructor count`),
1 live arrow (`a=domain`, `b=result`), 2 erased arrow (`a=domain`, `b=result`),
3 opaque (`a=b=0`). Constructor rows are grouped by type, with dense tags
`0..b-1` in declaration order. Only algebraic types have constructors.
An erased abstract type may be `none` in a signature or field type: it means
a uniform runtime value with no static description, not an additional word
tag or a value that may be inspected. A concrete type is required to Case or
describe it. Opaque File values are U32 host handle tokens, not heap addresses.

The four representation entries identify the pinned Nat/U32/Char/String types,
not arbitrary user datatypes with those names. Nat has Zero tag 0 and Succ
tag 1 with one live Nat field; String has SNil tag 0 and SCon tag 1 with Char
and String fields. Char's Chr wrapper is erased; its one field is U32. U32's
Word representation is **not** exposed to the VM. The encoder must reject any
reachable non-primitive body that destructures it. Constructor rows for these
types remain available to describe and validate their logical views.

Constant kinds are 0 U32, 1 Nat, 2 Char and 3 String. The first three have
`n=1`, containing the full unsigned value. String data is the exact ordered
list of Chr codes, not UTF-8 bytes. Pure Char permits every u32; the scalar
restriction is imposed only at the IO boundary. In particular a surrogate
pair in the seed's literal view must not silently be merged. Constants are
interned by `(kind,data)` in first node-use order. Duplicate constants or unused
constants are noncanonical. Literal pools contain no computed results.

## 3. Node records

`child` below always denotes an earlier node-record start. The stream is
post-order: visit function bodies in table order; recursively visit the children
in the order shown below; append the parent. No node sharing or unreachable
node records are permitted. Constants may be shared. A function reference is
a table index, so recursive calls do not create image-offset cycles.

Every node carries its erased result type. A Branch/Default carries the result
type of its enclosing Case. These metadata do not replace source checking.

| Code | Form | Operands (after result type) |
|---:|---|---|
| 0 | Literal | `constant_index` |
| 1 | Intrinsic | `prim_id, n, child[n]` |
| 2 | Default | `body` |
| 3 | Value | `tag` |
| 4 | Construct | `tag, n, child[n]` |
| 5 | Reference | `slot` |
| 6 | Application | `function_index, n, child[n]` |
| 7 | Let | `slot, value, body` |
| 8 | Case | `slot, scrutinee_type, mode, n, (key,arm)[n], default` |
| 9 | Branch | `key, first_slot, fields, body` |
| 10 | Closure | `site, live_argument, slots, n, capture_slot[n], body` |
| 11 | Invoke | `function_child, n, argument_child[n]` |
| 12 | Foreign | `foreign_id, n, child[n]` |

For traversal, Case visits its listed arms then its optional default; Closure
visits only its body (capture slots are not children). `default=none` is the
only absent child. A Default contains only a body and binds no new slot.
`Value` requires a nullary logical constructor. `Construct` requires the exact
number of live fields. Nullary constructions canonically use Value.

Case mode 0 is a **dense constructor-tag table**, including Nat's two logical
tags. Keys must be `0..constructor_count-1`, one per row; a default is absent.
To preserve first-match semantics, encoding selects the first matching source
arm for each tag before writing the table. A catch-all may therefore produce
separate copies of a Default node, one per tag. Mode 1 is only for U32/Char
literal tests: strictly increasing unsigned keys, zero-field Branch nodes and
one required Default. A dense 2^32-entry table is forbidden. The ordered sparse
keys plus fallback retain the literals core's Default form without changing
source behavior. The encoder resolves overlap before serialization. Branch
keys must equal their table key. Case evaluates no expression: it reads a slot.
Nat dispatch observes `0 -> Zero`, `n>0 -> Succ(n-1)`; Char constructor dispatch
observes `Chr(code)`. A U32 constructor dispatch is forbidden.

Function initial scope depth equals its live arity. Let's slot must equal the
incoming depth: its value runs at that depth; its body at depth+1. Branch's
first slot must equal incoming depth and its live fields occupy successive
slots, in declaration order. Reference and Case slots must be below the current
depth. All branches may reuse their otherwise disjoint slots. Scope restoration
clears appended slots after their body finishes. `slots` is the exact maximum
scope depth of that function or closure body (excluding nested closure bodies).

A Closure lists distinct captures in ascending enclosing slot order; the list
is exactly the free live slots of its body. It copies them into closure slots
`0..n-1`. Its live parameter, if present, is slot n. Its body starts at depth
`n+live_argument`. Its result type must be the corresponding live/erased arrow.
`site` is a consecutive global ordinal in node-stream order. The body is a
code pointer, not a captured activation. Invoke first evaluates its function,
then its sole argument if live, and applies it. An erased Invoke has `n=0`.
An Application uses the function table's compact live arity. Every operand
list is evaluated strictly left-to-right. Nothing evaluates erased syntax.

Foreign evaluates its live operands in order and constructs an inert Action.
It does not issue an effect until invoked with a continuation. Actions occupy
an arrow-shaped value: the live argument is that continuation. A Program root
is a zero-argument function returning `IO(Unit)` after erasure; a Book may expose
pure entries. Program execution applies that returned action/closure to the
terminal continuation. `Emit` ends successfully; `Halt` calls `die`. Emit is
not an effect request.

## 4. Validation and canonicalization

The loader copies bytes, checks the complete image, then materializes constants;
it MUST NOT run a body or effect during validation. Validation, UTF-8 decoding,
pool construction and rendering use explicit worklists, never the Wasm stack.

The validator must check all of the following, including unreachable functions:

1. Header identity, exact file length, section adjacency/counts/record lengths,
   name UTF-8/padding, known type/constant/node tags and pinned registry digest.
2. Every table reference and child offset is in range and points to a record
   start of the correct table. Children precede their parent. Every node is
   visited exactly once in the specified post-order. Function roots are distinct.
3. Constructor ranges/tags/field arities, arrow shapes, representation identities,
   literal kind against its type, exact primitive/foreign arities, signatures
   and known ids. A reserved primitive id is not a fallback to a Base body.
4. Function/call arities, result and known operand types, closure arity and result,
   scope depth, free captures, consecutive sites and exact maximum frame sizes.
   `none` may only erase a static type comparison; it never licenses inspection.
5. Complete dense cases or canonical sparse cases with a default, arm kind/key,
   field arity and contiguous binders. No standalone Branch or Default.
6. Canonical interning/order and absence of erased, unused, duplicate or trailing
   records. A validator may not canonicalize malformed input and then run it.

Limits for version 1: image <=16 MiB, every table <=1,048,576 records,
function/constructor/closure live arity <=4,096, slots <=65,536. The physical
image cap is checked before allocation. A valid larger input is
`Exhausted image-size`; a truncated/badly formed input is `HostFailure image`.
When both occur, the size guard is reached first. These are resource limits,
not additional source-language Invalid rules.

The reference serializer verifies the encoding and structural conditions; the
future image validator must additionally check the complete scope/type rules.
Its exact current coverage is reported by `check-spec.py`, not inferred from
this specification. The golden set is not a validator-soundness proof.

## 5. Words, cells and allocation

Zero is not a value. Immediate `v<2^31` is `(v<<1)|1`. It represents an enum
tag, Nat, U32, Char code or File token according to the checked term's type.
All other values are 8-byte-aligned nonzero cell addresses (low bit zero).
Scalar values >=2^31 use Big cells containing their full u32. Nat is therefore
a word with optional boxing, never a unary runtime chain.

Each cell begins with `[rc,hdr]`; `hdr=(payload_words<<3)|class`.
Classes and payloads are:

| Class | Payload |
|---:|---|
| 0 Object | `type, tag, field_values...` |
| 1 Closure | `node_offset, capture_values...` |
| 2 Big | `unsigned_bits` |
| 3 Action | `foreign_id, operand_values...` |
| 4 Activation | `owner_code, live_depth, slot_values[capacity]` |

`owner_code` is a function root or Closure node offset. Metadata words are
never RC edges. Every live field/capture/operand/slot is an owning edge.
Unused Activation slots are zero. Big carries no owning edge. Object field
count, capture count and operand count follow the validated descriptor. All
cells, including affine Type data and Activation cells, use the same RC rule.
There is no Type-versus-Data heap specialization and no cyclic value creation.

Ordinary rc is 1..0xfffffffe. `0xffffffff` means immortal. Literal-pool cells,
their transitive String tails, and boxed scalar constants are immortal from
the first VM implementation. They are allocated in pool order; strings are
built tail-first; sharing occurs only through exact constant interning.
RC overflow is Exhausted kind 2, not wraparound to immortality. Pointer copies
must not silently acquire this sentinel.

`dup(immediate)` and `drop(immediate)` do nothing. `dup(pointer)` increments
ordinary rc or leaves the immortal sentinel unchanged. `drop(pointer)` decrements
ordinary rc; on zero it releases edges with an explicit LIFO worklist, pushing
them in reverse payload order so the first field is processed first, then frees
the cell. It never recursively calls drop on the Wasm stack. A pending drop
worklist owns its references. Underflow, dangling pointer, double free and class
mismatch are InternalFailure, never resource exhaustion.

Allocation rounds `(2+payload_words)` up to a power of two in words, minimum
four words (16 bytes). Each size has a LIFO free list; no splitting/coalescing.
Allocate from that list, else bump. Padding is zero on allocation; debug free
poisons payload with `0xdeadbeef`. Free-list links and the saved size class are
allocator metadata, not live values. Allocation addresses, bump, free-list order
and padding must agree in lockstep; physical `memory.grow` timing need not.

Memory: control/scratch bytes `[0,4096)`; image at byte 4096; frame region starts
at the next 64-KiB boundary after the image and has 16 MiB; heap starts immediately
after that region and grows to the 2,048-page (128 MiB) total memory cap. VM
instances cannot hold two images. Constant cells use the same bump allocator
before any mutable cell. Outgoing/host-returned byte buffers use allocator
blocks with no RC edges and are freed by their IO operation after conversion.
`knot_alloc` must keep buffers disjoint through host callbacks and memory growth.
No live managed cell may alias a host byte buffer.

An allocation first checks its exact class and available space. It either
succeeds completely or returns Exhausted kind 2 with the pre-allocation state.
Cleanup after failure must release all non-immortal roots. A debug audit after
releasing the result requires zero live non-immortal cells and no live handles.
Logical frame/heap limits may be reduced only in test initialization, and those
smaller limits must be present in the receipt.

## 6. Machine, frames and transitions

The semantic state is `(mode, control, activation, continuations, owned_values,
heap, free_lists, bump, fuel, calls, quantum_calls, effects, outcome)`.
Code offsets and metadata are never value roots. A result register, a saved
argument, an activation pointer and a continuation's saved value each own one
reference. The test-only dump must expose all of these, including occupied
slots, allocation classes, live rc, drop worklist, buffers, budget limits and
pending IO. Equal final outputs do not establish lockstep.

Modes are Eval(node), Return(value), Gather(kind,node,next,values),
Enter(function,values), Apply(closure,arg-or-none), Release(worklist),
ForeignReturn(action,continuation,result), Halt(outcome). Lists in the dump
are in processing order; numbers are unsigned; missing values are `none`.
An implementation can subdivide a mode into mechanical load/store operations,
but one externally stepped transition must implement exactly one row below.
Allocator/drop micro-operations are deterministic substeps of that row and are
included in its post-state. No user code or second host effect may hide in one
transition.

| Control | One transition |
|---|---|
| Eval Literal/Value | Return the pool value (immortal) / logical nullary word. |
| Eval Reference | Dup the selected live slot into Return. |
| Eval Construct/Intrinsic/Application/Foreign | Start Gather with index 0 and no accumulated operands. |
| Gather, operands remain | Push a Gather continuation, evaluate the next operand. |
| Return to Gather | Move the result into the operand vector, advance index. |
| Gather complete | Construct the object / apply primitive / enter function / build Action; consume owned operands. |
| Eval Let | Save body, activation and old depth in Bind; evaluate initializer. |
| Return to Bind | Move value into slot, push Scope(old depth), evaluate body. |
| Return to Scope | Drop appended slots, restore old depth, preserve returned value. |
| Eval Case | Read tag, select arm, dup each live field into consecutive slots, push Scope(old depth), evaluate arm body. |
| Eval Closure | Dup listed captures in order, allocate Closure, Return it. |
| Eval Invoke | Push InvokeFunction, evaluate the function expression. |
| Return to InvokeFunction | For a live arrow, save function and evaluate argument; for erased arrow enter Apply immediately. |
| Return to InvokeArgument | Move function and argument to Apply. |
| Apply Closure | Charge one invoke; copy captured edges to a fresh Activation, transfer argument, evaluate body. |
| Apply Action | Charge one invoke; perform exactly one effect, convert its result, then schedule Apply of its continuation. |
| Return with no continuation | Stop with result; Program then schedules its terminal application as specified below. |

Construct specializes Nat Zero/Succ and Char Chr into words; overflow is checked
before incrementing a Nat. Scalar boxes consumed by a primitive are dropped
after its result is allocated. Case field copies are dups; the scrutinee slot
continues owning its original value. Ordinary Bind/call arguments move their
owned result into the destination slot. Closure captures always dup. Leaving
an activation drops all its live slots. Persistent snapshots may share an
Activation by RC, but mutation requires uniqueness; the normative machine
keeps one mutable owner plus suspended frame references, never two evaluators.

Frame kinds are Gather, Bind, Scope, InvokeFunction, InvokeArgument and Call.
Each record is `[size,kind,previous,activation,depth,node,index,n,values[n]]`,
where size is the total word count, previous is a byte address (zero at bottom),
kind is 0..5 in that order, and inapplicable metadata is zero. `activation` is
an owning pointer, except Scope (borrowed from the still-active activation).
Every `values` entry owns one value. Records occupy a contiguous LIFO region,
aligned to eight bytes with zero padding. Exact size is `align2(8+n)` words.
Pushing beyond the region reports Exhausted kind 3 before writing. Frame size
and the region are independent of the native/Wasm engine's stack.

A call has a Call continuation exactly when its value must return to caller
work. A function/closure body is tail; Let's body and Case's arm inherit tail
position, their initializers and operands do not. A tail Application or Invoke
removes pending Scope frames, drops its caller activation after all arguments
and captures are owned, and replaces it. The outer Call remains. Non-tail entry
saves the caller in Call; return releases the callee and restores that caller.
Erased closure invocation still enters a body and pays fuel.

Each entry into Program `main`, each requested Book function, each Application
entry and each Invoke application costs **one** unit of fuel, immediately before
entry/effect. No other step pays fuel: argument evaluation, constructors, lets,
cases, RC, primitive instructions, encoding, validation and display cost zero.
Arguments are evaluated before the call's own debit; their nested calls charge
normally. A direct Intrinsic costs zero. Foreign construction costs zero;
applying the Action and subsequently applying its continuation cost one each.
Program's application of `main`'s IO value and application of the terminal
continuation also cost one each. The terminal continuation itself performs no
further source call. If fuel is zero at a debit point, preserve the pending
call, perform no effect, and stop as Exhausted kind 1. A terminal Return needs
no further fuel. Calls is the total of successful debits; `initial=fuel+calls`.

Fuel is u32 (0..4294967295), independent of eval-cli's transition budget. The
ordinary benchmark budget is 1,000,000,000 calls; fixture budgets are explicit.
No claim compares the same numeric fuel across evaluators with different units.

After exactly 65,536 successful debits since re-entry, dispatch returns to
`knot_main` **before executing the newly entered body/effect**. The entire next
state is committed. `knot_main` immediately re-enters dispatch with
quantum_calls reset to zero. A pending Action effect thus runs exactly once.
Re-entry never recurses or allocates a guest frame and never replenishes fuel.
This is a Wasm-to-Wasm function return/call, not a JS effect callback. Test
dumps have a Yield event at this boundary; counters alone reset between events.

Book launcher arguments are `IMAGE FN FUEL [ENUM_ORDINALS...]`. Program arguments
are `IMAGE FUEL -- [ARGS...]`; only ARGS are visible to Base `IO.args`. The image
is read as raw bytes. Book validates exact live arity and nullary enum argument
domains; structured arguments report HostFailure invoke structured-argument.
Book prints `Evaluated<TAB>type-id<TAB>tag<TAB>tree<LF>` using the image's names
and live fields, no spaces after commas, matching eval-cli on shared profiles.
Closure/abstract results report HostFailure invoke function-result/abstract-result.
Rendering uses an iterative worklist with declared limits: 1,048,576 visits
and 16 MiB output. Exhaustion is explicit, never a truncated successful value.

## 7. Primitive derivation and numeric bounds

`registry.json` freezes ids 0..38 in literals' Op declaration order. It also
reserves 39 U32.or and 40 U32.xor, with seed-derived edge witnesses required in
vm-prims. U32.not is **already id 5**; it must not be added under another id.
Each entry records its exact pinned Base name, live input kinds and result kind.

Derivation is a reachability gate over the **final merged S**, from compile-cli
and parse-cli, following calls, value references and selected foreign bodies
after erasure. For every reachable seed intrinsic, either a registered prim
implements the seed semantics or compilation is Unsupported. For every
reachable non-prim body, reject an inspection of an immediate representation
(particularly `U32{Word}`). Reachability must be regenerated when S changes.
These snapshots and 41 ids do not assert that the final S registry is complete.
New ids append; a changed meaning or binary grammar requires a new version.

U32 addition/subtraction/multiplication wrap modulo 2^32. Comparisons are
unsigned. Division by zero returns 0; remainder by zero returns the dividend.
Shifts by >=32 return 0, not a masked shift count. Nat subtraction saturates at
zero; addition/multiplication/Succ and any conversion check the mathematical
result before narrowing. Nat above 2^32-1 is Exhausted with NatRange evidence,
never U32 wrapping. Char.from_u32/to_u32 preserve the full word. Char.is_space
recognizes 9..13 and 32. Bool tags are False=0/True=1; Cmp is LT=0/EQ=1/GT=2.
String is the immutable Char list: equality compares codes and length; append,
reverse, length and empty have their ordinary list observations. Show uses
unsigned decimal digits with no leading zero except `0`.

## 8. IO and `knot-io-2` (D17)

The host ABI at `campaign/io-host` commit `f42ae395` is the baseline.
The VM imports only `knot_io`, exports memory, `knot_alloc(i32)->i32`, and
`knot_main()->()`, declares <=2,048 pages, and has no start section. Additional
debug exports are allowed only in the test build. Every inherited signature,
16-byte Result layout, errno, synchronous ordering, sandbox rule and ownership
obligation remains in force.

The delta, owned by io-abi-2, is:

| Import | Signature (i32 parameters, no return) | Delta |
|---|---|---|
| read_bytes | `handle, maximum, out` | Like read, returning raw bytes without any UTF-8 decoding/re-encoding. |
| path_identity | `path, path_length, out` | The pinned modules `path-host.inspect` identity: canonical path and same-file identity, including symlink/case aliases. |
| exhausted | `kind` | Add 3 for explicit guest frame-region exhaustion; retain 1 fuel, 2 memory/representation resources. |

`path_identity`'s result payload and filesystem precedence must be frozen by
io-abi-2 from `campaign/modules` `0111f133` C/JS bodies, then copied into the
host contract before vm-io implementation. This document does not invent a
different identity algorithm or authorize relaxing ordinary open's sandbox.
An image may encode the reserved Foreign identity now; execution cannot claim
IO conformance until that host contract and its fixtures are integrated.

Foreign ids, pinned declaration names, arities and operand kinds are listed in
`registry.json`. Args, print, open, read, write_bytes, close and path inspect
produce Action cells. On application the VM converts values, calls the host,
builds the exact pinned Base Result/pair/handle view, and applies the saved k.
IO.pure and IO.bind run as ordinary checked closure code. Dropped actions and
unselected branches do nothing. No host effect occurs in a proof or validation.

Outgoing String lists must consist of Unicode scalars and are encoded to
canonical UTF-8; no surrogate merging or replacement is allowed on output.
Incoming text follows the host's replacement decoding, preserving BOM, and is
converted to one Chr per scalar. Raw input bytes become U32 list elements
0..255. Byte-list output scans the **whole** list before writing, computes
`invalid |= element >> 8`, and copies low bytes. The host sees the original
invalid flag. A nonzero flag yields errno 22 before any write.

## 9. Outcomes, budgets and the Exhausted-lane rule

Record Accepted/Invalid/Unsupported/Exhausted/HostFailure/InternalFailure
separately. Malformed images and unknown ids are HostFailure; source forms not
handled by Knot are Unsupported; an internal invariant failure is a defect.
A timeout or process crash never counts as a semantic mutant kill.

The shared observation lanes are seed reference, pinned Knot eval-cli, Bend
model(image), and Wasm VM(image). This increment records the first two plus
byte round trips; it cannot record agreement with a nonexistent VM.

A lane can be excused **only** when its receipt identifies a documented bound,
the requested budget and the reached boundary. Relevant limits include:

| Lane | Documented bound |
|---|---|
| literals eval | unary Nat/String materialization <=2^20; <=2^20 source transitions; display 4,096 visits/65,536 chars |
| seed Bun | observed approximately 32K stack limit; an actual matching stack-exhaustion observation is required |
| seed native | seed's approximately 2^48 Nat range and declared runtime/resource limits |
| knot-vm-1 | u32 Nat range, explicit call fuel, 16 MiB image, 16 MiB frames, 128 MiB total memory, display bounds above |

NatRange, RCOverflow and image/display capacity are representation-resource
exhaustion (kind 2 at the narrow host boundary). The VM's typed outcome/dump
must retain the more precise cause, request and limit; the host's generic
`exhausted(2)` alone does not prove which bound was hit. Frame capacity is kind 3.
Model tracing memory is a harness bound, not a reason to excuse the actual VM.

**Where the seed succeeds within the VM's declared domain and budgets, the VM
MUST return the seed's value/effect trace.** Another lane's exhaustion does not
excuse the VM. A VM that exhausts early, corrupts a result, or labels an engine
trap as a budget hit fails. Unsupported, timeout, unknown failure and missing
lane are not Exhausted and not agreement. Fixture expected values cannot be
regenerated from the candidate VM. A scalar/heap boundary witness must say why
the mathematical result or counted live allocation crosses the stated limit.

## 10. Frozen evidence and subsequent acceptance

`golden/expectations.json` fixes source hashes and raw seed/eval exit/stdout/stderr
before serialization. Hand-written record plans accompany committed `.kimg`
bytes. `check-spec.py` re-executes both oracles, compares exact observations,
checks record/byte round trips, and kills semantic serializer and source mutants.
The Foreign fixture records seed output and a real Unsupported evaluator
observation; it remains an explicit future IO differential obligation.

`bench/` freezes Peano, S.choose-shaped CPS closure churn, Char-list building
and String.eq scans, list build/fold, deep non-tail recursion and SHA-256 over
65,536 ASCII bytes. It records native build provenance, outputs, process CPU
and wall measurements, and hardware retired-instruction counts where available.
Parse-cli is measured over the frozen transitive compiler bundle, including
Base and the byte package. Parse classifications are preserved; measuring it
does not establish Knot acceptance of its own source. Timings are observations,
not deterministic gate thresholds or a VM speedup claim.

vm-model must add complete checked proof entries for codec, bounded validator,
RC edge audit and zero-leak observations. vm-core must add an iterative loader,
validator, CEK machine, state dump and quantum re-entry. vm-lockstep compares
each transition and the four value lanes. vm-rc/vm-io/vm-prims close reclamation,
effects and the final S registry. They must retain these expected results,
including the 250,000-deep workload, and kill type-correct semantic mutants.
The first speed gate is <=4x seed-native on each frozen workload on a quiet host;
>10x requires design review. No speed ratio is claimed in this increment.
