# Compiler target interface

The compiler emits a JSON bundle with numeric version/profile 2, the explicit
configuration from `layout.json`, and a flat array of eight-u32 instructions.
The validator derives offsets with checked arithmetic; no host address or
function pointer enters the bundle. It starts from empty storage. The immutable
code buffer indexes instructions (not bytes). All operands name capture slots,
join slots, scalar tags, lengths, or code indexes as specified in `SPEC.md`.

| Core form | Required records and operations |
|---|---|
| `Construct` | Boxed object kind/tag/arity plus a live field range. Evaluate live arguments in source order into distinct captures. `construct(dst,kind,tag,first,count)` moves the range only after successful reservation. Erased fields emit no instruction or slot. |
| `Let` | A capture in the current activation. Transfer a last/affine occurrence with `move`; add a reusable Data edge with `share`. An unused owned binding emits `release`; preserve `clean`'s pending work at a suspension boundary. |
| `Case` | `branch(src,tag,yes,no)` selects an arm on device without consuming the scrutinee. The selected arm uses `open` to transfer its live fields. Shared Data opening preflights all child acquires, including repeated edges. Reconstruction is `construct` over the transferred fields; it must not retain the old Type parent. |
| `Application` | A defunctionalized code entry and owned argument/capture range. Save the caller continuation in `start(join,arity,code,base,count)`, move Type and retain additional Data occurrences into the callee range, then `jump(entry)`. Results use `deliver(join,attempt,logicalSlot,src)`; `resume(join,attempt,first)` transfers ordered results and jumps to saved code once. |

A continuation is the code identity plus its owned capture array. Saved capture
ranges designate existing holders; they are not additional RC edges. Logical
join slot order survives delivery order. A completion carries the *attempt it
was issued under*. Reading the current attempt when a late completion arrives
would defeat cancellation and is forbidden. `cancel` consumes saved captures
and arrived results into pending cleanup before `start` can replace the attempt.

These are exact operation contracts, not an accepted lowering algorithm.
The first emitter must freeze its activation/capture allocation and attempt
transport separately. This version uses immediate capture/join/attempt operands
and one active PC. Statically assigned activations can target it directly;
general recursive activation allocation and dynamic attempt operands require an
explicit extension or a checked record-construction stage. Such programs remain
Unsupported until that extension has independent evidence. No host JS branch
interpretation, per-program shader, unchecked form, or copied Type capture may
be used to bypass that boundary.

An execution outcome is independent of source validity. `Invalid` here denotes
a malformed supported bundle/request. Unknown format/profile/opcode is
`Unsupported`. Capacity/count/identity/attempt/work failure is `Exhausted`.
Falling off checked record code is `InternalFailure`; adapter, submission,
mapping and IO errors are `HostFailure`. The source compiler must finish its
own semantic checks before publishing any executable bundle.

Next acceptance is a bounded source program containing all four core forms,
with expectations fixed from the pinned seed and then seed ⇔ Knot evaluator ⇔
Knot Wasm ⇔ emitted records on Metal. This increment supplies independent
record-model Bun/native/host comparisons, not that source compilation claim.
