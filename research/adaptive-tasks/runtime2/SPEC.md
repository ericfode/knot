# Device records 2

Contract fixed before implementation (gpu-2, 2026-09-27). Literal expectations
are frozen in `fixtures.json`; additions may strengthen coverage, never derive
an expected value from the implementation under test.

## State and ownership

One serial device interpreter owns mutations. A completed dispatch publishes
the next immutable snapshot. There is no parallel-writer or performance claim.
The independent Bend store/scheduler and independent Python reference compare
every command observation. The host reference is a research oracle, expressly
authorized for this increment; it is not compiler implementation.

Object records have metadata `(identity, kind, rc, arity)` followed by payload
`[tag][live child identities]`. Kind 0 is unique Type; kind 1 is immutable Data.
Data can contain only Data. Every object edge, capture, delivered join result,
and pending release is an owning obligation. RC is outside the payload. Type
has exactly one obligation; Data's RC counts all obligations. Erased fields have
no slot. This profile boxes scalar values as nullary tagged objects.

An identity starts at 1 and is never reissued; object *storage slots* are reused
in lowest-free order. Exhaust the configured identity ceiling before increment
could wrap. Identities are bundle-local, never external locators; no instruction
accepts a raw identity. A new bundle has a fresh host lifetime. Snapshot restore,
cross-bundle references and cyclic/backpatched objects are Unsupported.

Capture slots form owned arrays in one flat table. Move clears its source;
share requires Data and checks the count ceiling before publication. All
operations preflight capacity and operands before consuming any input. Failure
preserves state except the reply. Cleanup may commit a prefix and report
Exhausted with its explicit pending stack retained. Readers block physical
reclamation and opening; logical release remains possible.

A join contains `(attempt,state,arity,received,completions,code,captureBase,
captureCount)` and ordered result slots. States: 0 unused, 1 waiting, 2 ready,
3 cancelled, 4 resumed. Starting unused/cancelled/resumed joins increments the
attempt without wrapping. A delivery names both attempt and logical slot; stale
or duplicate delivery is Invalid and preserves its source capture. The final
delivery marks ready and increments completions exactly once. Cancel reserves
space for every saved capture and delivered result before moving them to the
pending stack. Resume transfers results to vacant captures, retains the saved
capture array, marks resumed, and returns the defunctionalized code identity.
The code identity is a validated instruction offset, not a function pointer.
Completions count cumulatively across attempts. Arity zero completes at start.
Sharing Type is Unsupported (the capability does not exist); a Data constructor
containing Type is an Invalid request. Opening with the wrong actual arity is
Invalid; a constructor/join exceeding configured arity is Exhausted.

## Instructions

Each instruction is eight u32 words, unused operands zero. Inputs below are
capture indexes unless stated otherwise. Operand ranges are checked without
wrapping. Outcome codes: Ok=0, Invalid=1, Unsupported=2, Exhausted=3,
InternalFailure=5; host/API/IO failures are HostFailure outside device words.

| op | operands | transition |
|---|---|---|
| 1 construct | dst, kind, tag, first, count | Move consecutive captures into a new object; dst must initially be empty and outside the input range. |
| 2 share | src, dst | Retain Data into an empty capture. |
| 3 move | src, dst | Transfer one capture. |
| 4 open | src, first, count | Require exact arity and vacant distinct destinations, outside src. Unique object transfers edges and frees storage; shared Data preflights every child acquire (including duplicates), then releases its parent edge. |
| 5 release | src | Move capture to the pending stack. |
| 6 clean | budget | Pop last pending identity; decrement Data or free a last/Type owner and append children in declaration order. Before each pop, reserve resulting stack space. Budget counts pops; remaining work or readers gives Exhausted. |
| 7 readers | count | Replace the number of outstanding reader leases; host may set zero only after submitted readers complete. |
| 8 start | join, arity, code, captureBase, captureCount | Start a fresh attempt; saved capture range must be in bounds and disjoint from other waiting/ready joins' ranges. |
| 9 deliver | join, attempt, slot, src | Move source into an empty ordered join result, completing once. |
| 10 cancel | join, attempt | Release saved captures/results transactionally; clear them and mark cancelled. |
| 11 resume | join, attempt, first | Move ready results into empty captures; return code in reply. |
| 12 inspect | src | Return the immutable tag in reply without consuming. |
| 13 span | base, count, stride, limit | Checked word-range calculation: base <= limit and count <= (limit-base)/stride; stride must be positive. Return end or Exhausted. |

Unknown version, profile or opcode is Unsupported. A supported opcode with bad
word types, nonzero reserved operands, malformed ranges/kinds/code offsets is
Invalid. Runtime empty/occupied/stale requests are Invalid requests, not source
judgements. Resource capacity/count/identity/attempt limits are Exhausted.
Instruction execution is exposed one transition at a time for qualification,
and through the bounded program driver below. No
source compiler, source evaluator or source Wasm profile is changed here.

## Program driver (fixed before its implementation)

Header words 24 and 25 hold PC and phase: Ready=0, Suspended=1, Halted=2,
Faulted=3. One serial dispatch executes at most `quantum` instructions, then
publishes the complete state. Quantum is a u32; there is no smaller implicit
cap. Actual host timeout is Exhausted and device/API failure is HostFailure.
Quantum zero preserves the whole state. A
positive quantum resumes Suspended; Halted/Faulted are terminal and unchanged.
Every attempted instruction consumes one step. Successful ordinary instructions
advance PC; successful resume (11) sets PC to its returned code index. Exhausting
quantum suspends with the next PC retained. Exhausted preserves the current PC
and suspends, so cleanup can resume from its retained pending stack on the next
dispatch. Other failed instructions preserve PC, set Faulted, retain their
classified status, and preserve every owner. Cleanup may retain a committed
prefix. Falling off the instruction
buffer is InternalFailure. The host supplies only quantum, never branch decisions.

| op | operands | transition |
|---|---|---|
| 14 branch | src, tag, yes, no | Inspect without consuming; select a validated instruction index; reply zero. |
| 15 jump | target | Set PC to a validated instruction index. |
| 16 halt | src | Retain result capture, return tag, mark Halted without advancing PC. |
| 17 yield | none | Advance PC, suspend immediately. |

These four opcodes belong to program mode. The transition-test mode (opcodes
1–13) remains separately available. No per-program shader is emitted. Program
fixtures in `programs.json` precede driver implementation. The driver wraps the
same independent Bend and Python store/scheduler models. Program observations
are `{pc,phase,state}` with the complete state projection above.

## Layout

Configuration: `objects`, `captures`, `pending`, `joins`, `arity`, `rcLimit`,
`idLimit`, `attemptLimit`, `maxStorageBytes`. Capacities may be zero; count limits
are 1..4294967295. The maximum storage binding is supplied by the adapter and
capped at 4294967292 bytes (whole u32 words). Every segment is checked by division
before multiplication/addition. No fixed object-count ceiling below this limit.

Header is 32 words. Objects use stride `5+arity`, captures/pending stride 1,
joins stride `8+arity`. Each segment ends with one `0xdeadbeef` guard. Header
offsets/counts and all unused record payload words are validated independently.
The immutable instruction buffer uses stride 8 and has its own storage limit.
The exact header table is specified by `layout.json` before device implementation.

Complete observations are `[status,reply,nextIdentity,readers,freed,objects,
captures,pending,joins]`; objects are in physical slot order and are either `[]`
or `[identity,kind,rc,tag,[children]]`; joins are fixed arrays
`[attempt,state,arity,received,completions,code,captureBase,captureCount,[results]]`.
`freed` counts physical cells freed (including open). Slots beyond join arity
are zero. These observations deliberately expose surviving owners and cleanup.

Within dynamic construct/start, malformed operands, ownership and saved-range
conflicts precede resource failures. The static bundle validator checks only
transport and operand facts available without executing the program; an input
may therefore be refused at that earlier boundary before dynamic ownership is
examined. Neither boundary silently accepts an unhandled operand.

## Evidence boundary

Require counts 1, 2, 64 and 4096; zero/exact/one-past capacity, count, identity,
attempt, arity and storage boundaries; shared trees/lists, rebuilds, suspended
captures, cancel/replace, stale completion, right-before-left ordered 7/9
(noncommutative observation 709), n-ary completion once, and cleanup resumption.
WGSL mutants must typecheck. Only real-device mismatches kill WGSL mutants;
null-backend validation records them as constructed/typechecked, never killed.
The old runtime-1 and 38-case source/receipts remain byte-identical; replay on
Metal is an explicit coordinator gate. Filled Bend laws are model laws, not a
proof of WGSL refinement or a general scheduler correctness theorem.
