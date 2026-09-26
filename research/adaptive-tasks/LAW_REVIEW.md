# Adaptive task protocol: bounded review packet

Scope: `slot.bend` and `task.bend`, with independent `oracle.bend` and executable
witnesses in `fixtures.bend`/`conformance.bend`. This is a prototype, not a package
release, full compiler, concurrent proof, or general heap. WGSL evidence is
listed separately and is not reviewed by Bend file rules.

## Domain, ownership, and public observations

`Slot<A:Type> = Vacant | Occupied(A)` is affine. `put(A,s,x)` returns
`Inserted(Occupied(x))` on vacancy, otherwise `Rejected(Occupied(old),x)`.
`take` returns `Extracted(Vacant,x)` or `Missing(Vacant)`. No numeric handles,
generations, or slot reuse protocol is provided. A client can explicitly put a
new value into a vacancy. This is one slot, not an indexed arena API.

Payload is affine `OwnedWord(U32)`. Frame is affine `Unary(factor,bias)` or
`Binary(left:Payload)`. Task is affine
`Work(destination:U32,remaining:Nat,payload:Payload,frames:List<&1,Frame>)`.
Run is affine `Checkpoint(Task)` or `Delivered(destination,Payload)`.
Neither a caller nor a scheduler can copy a live task under the checked API.
External-resource cleanup is not modeled by OwnedWord.

One tick computes `(x * 1664525 + 1013904223) mod 2^32`. A unary frame computes
`x*factor+bias`; a binary frame computes `left*31+right`, preserving source order.
These are deliberately noncommutative, independently specified fixture
operations. All arithmetic is U32 modular arithmetic, not index arithmetic.

`step` consumes a task: a positive tick count decrements once and updates the
payload; zero ticks with a frame apply that frame and retain the rest; zero
ticks and no frames deliver. `run(fuel,state)` performs at most fuel steps,
returns the full Checkpoint on budget exhaustion, and treats Delivered as
absorbing. `slices(count,quantum,state)` composes exactly count such budgets.
Zero quantum can preserve pending work indefinitely; no progress is promised
for that input. There is no implicit successful partial result.

The helpers `put_slot`, `take_slot`, `observe_payload`, and `observe` are
**destructive consumers** used for testing/composition. They may discard carried
payloads or residual work; they are not lossless schedulers. `observe` yields
`(status,destination,value)` and deliberately omits frames/ticks. The actual
state laws below compare full Run values, so that lossy observation is not the
sole oracle for frame or checkpoint preservation.

## Laws and quantification

All twelve laws are in LAWS.bend; PROOF.bend is a complete checked entry. Variables
`A:Type`, `x,y:A`, `n,m:Nat`, `d,a,b,f,x:U32`, `fs:List<&1,Frame>`, and `r:Run`
range arbitrarily as appropriate. Erased law arguments are proof parameters,
not unsafe inhabitants or permission to reuse runtime values.

1. `put_empty`: put(Vacant,x) = Inserted(Occupied(x)).
2. `put_full`: put(Occupied(x),y) = Rejected(Occupied(x),y).
3. `take_full`: take(Occupied(x)) = Extracted(Vacant,x).
4. `take_empty`: take(Vacant) = Missing(Vacant).
5. `put_take`: take(put_slot(put(Vacant,x))) = Extracted(Vacant,x).
6. `take_twice`: take(take_slot(take(Occupied(x)))) = Missing(Vacant).
7. `zero_fuel`: run(0,r) = r, comparing the entire residual state.
8. `delivered_absorbs`: run(n,Delivered(d,p)) = Delivered(d,p).
9. `one_tick`: run(1,start(d,1+n,x,fs)) =
   Checkpoint(Work(d,n,OwnedWord(x*1664525+1013904223),fs)).
10. `binary_order`: run(2,start(d,0,b,[Binary(OwnedWord(a))])) =
    Delivered(d,OwnedWord(a*31+b)).
11. `frame_captures`: run(2,start(d,0,x,[Unary(f,b)])) =
    Delivered(d,OwnedWord(x*f+b)).
12. `fuel_add`: run(m,run(n,r)) = run(Nat.add(n,m),r).

Law 12 uses induction on n and a case split on r. The Checkpoint case calls the
induction hypothesis on step(task); the Delivered case uses delivered_absorbs.
It covers arbitrary fuel and all task states, not just a finite literal budget.
The other equations use definitional equality or a Nat case split. This does
not prove a full arbitrary-program evaluator refinement or fair scheduling.

## Coverage and independent observations

| Operation family | Contract coverage | Executed witnesses and limits |
|---|---|---|
| put/take | Four branch laws and two compositions above | Occupied OwnedWord(7), incoming OwnedWord(9), vacancy, second extraction. Rejection includes both values. |
| put_slot/take_slot | Destructive slot projection specified; compositions 5–6 | Accepted insertion/extraction and empty second take. No resource-cleanup promise. |
| tick/tick_owned | Explicit independent arithmetic RHS in one_tick | seed 11, three ticks; oracle.iterate independently loops over source tick count. |
| combine/unary/apply | binary_order and frame_captures | Distinct operands 7 and 9; factor 3 and bias 5; nested frames. |
| step_parts/step | one_tick, binary_order, frame_captures, fuel_add | Tick, frame, and delivery branches; empty/nonempty frame stack. General one-step semantic theorem beyond these equations is open. |
| run/start | zero_fuel, delivered_absorbs, fuel_add and full-state expected constructors | Budgets 0,5,6; nonzero destination 73; delivery at exact boundary. |
| slices | Runtime comparison against full run for six 1-step and two 3-step slices; zero quantum case | No separate universal multiplication/iteration theorem is claimed for slices. |
| observe/observe_payload | Runtime transcript constrains status, destination and payload | Explicitly destructive and lossy; no frame-preservation proof is inferred from these observations. |

The independent source oracle recursively evaluates Data trees of Leaf, Fork,
and Then, with no task slots, fuel, phases, or checkpoint representation. The
CPU frame transcript's expected value comes from a separately evaluated source
tree (cpu_frames), not task.run. Ten fixture trees cover two completion orders,
balanced/skewed forks, an opaque heavy leaf, a serial frame chain, a singleton,
nested captures, and U32 wraparound. JS and native fixture transcripts agree.
The law witnesses are inhabited by OwnedWord(7), OwnedWord(9), both frame
constructors, Nat 0/1/3/6, and destination 73. Generic Type slot laws therefore
have concrete affine instances; they are not relying on Empty.

The valid ownership control compiles. Reusing Run or taking the same slot twice
fails specifically with `consumed more than once`; neither negative is counted
for a parse failure. No runtime type punning or new axioms are introduced.
Base/native U32 primitives and the upstream checker/compiler remain trusted.
Imported Base contains foreign/unsafe APIs; these modules call no unsafe Array
APIs. IO.print is used only by fixture/observation drivers.

## Mutation and device evidence

Five changed CPU models still typecheck, then fail the expected law and change
an executed witness: wrong tick constant → one_tick; swapped binary operands →
binary_order; destination replaced by zero → binary_order; zero fuel discards
state → zero_fuel; occupied slot overwritten → put_full. Expected and actual
rejecting law are recorded in receipts/checks.json. No type error is counted as
a semantic mutant kill.

The handwritten WGSL probe uses preallocated non-reused task slots and separate
prepare/execute/join dispatches. A bounded frontier redistributes checkpointed
work. Device output matches Bend on 38 runs, including explicit capacity/round
exhaustion and zero quantum, on a non-fallback Apple M5 Max Metal adapter.
Logical worker index changes are observed; physical GPU-core migration is not
measured. Three type-valid shaders build pipelines but fail the Bend oracle:
swapped join operands, lost unary bias, and early leaf completion. These are
finite device tests, not a proof of weak-memory safety, arbitrary histories,
general allocation, source compilation, portability, or speed.

## Hostile review

A lossy observe() could conceal changed frames, so zero_fuel and fuel_add compare
the full Run state and frame laws inspect captured values. A wrong tick body
could escape a law mentioning T.tick on both sides; one_tick instead spells its
arithmetic independently. Returning destination zero is a separate tested
mutation. A Data task snapshot could be copied and replayed; runtime Task, Run,
Slot, Frame, and Payload are Type, and negative quantity controls exercise this.

Known remaining omissions: generic frame stacks on the device, N-ary joins,
runtime-supplied invalid graph records (the host accepts only validated trees),
slot generations/reuse, shared data lifetimes, cancellation, host effects,
general allocator behavior, and a universal CPU↔GPU simulation proof. No public
operation or performance promise includes them.

Exact reviewed source and gate hashes are in receipts/checks.json; the live
Perch wrapper separately records this packet's own hash. Evidence remains valid
only for those hashes. Full live-review adjudication is in ../PERCH_REPORT.md.
