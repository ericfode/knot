# TermStore bounded law review

Review unit: the public arena and memo API. First-order Data payloads; one affine
owner per store and one Scopes chain per identity realm. Independent roots may
alias, and fabricated containers are outside the supported API. Numeric IDs are
reconstructible. IDs remain stable until the store is dropped; slots are append-only.
No pointer identity, shared mutation, higher-order stored closures, or affine handles.

## Contract, oracle, and inhabited domains

Abstract store = (scope, bound, ordered list). alloc(x) below bound appends x and
returns (scope,old length); otherwise Limit and unchanged. get/set reject WrongScope
before Bounds; successful set changes one cell. length/limit/snapshot return exact
metadata/content. Scope allocation includes 0xffffffff once, then ScopeExhausted;
a zero-limit store also consumes a scope. Bound = min(request,16777216).

Independent model: `append([],x)=[x]`; `append(y::ys,x)=y::append(ys,x)`;
`at(x::xs,0)=Done(x)`; `at(x::xs,1+i)=at(xs,i)`; `at([],i)=Bounds`;
`replace(x::xs,0,y)=y::xs`; `replace(x::xs,1+i,y)=x::replace(xs,i,y)`.
Model bounds/indexing use list length and Nat; implementation uses checked Vec.
The relation compares every ordered element, scope, effective bound, and length.
The model never calls Store, Memo, Cell.step, or Cell.result.

Concrete inhabited witnesses: U32 values 17,29,43,97; empty and three-cell stores;
scope 7 and foreign scope 8; indices 0,1,2,length,0xffffffff; limits 0,3,5 and
0xffffffff (clamped). Generic Data witness: Atom(17), Atom(29), and
ApplyTerm(Id(23,0),Id(23,1)). Model lists include [] and [17,29]. Compiled runtime checks also instantiate Store with Term and Memo with distinct
Term/String payload and error types (data_checks.bend). Every law has no
precondition, or explicitly quantifies arbitrary Data payloads on a constructible
fixed history. No Empty/unsafe witnesses or impossible antecedents occur.

Memo table (all actions for every state):

| State | Begin | Succeed(v) | Reject(e) | Cancel |
| --- | --- | --- | --- | --- |
| Pending | Evaluating / OK | unchanged / InvalidTransition | unchanged / InvalidTransition | unchanged / InvalidTransition |
| Evaluating | unchanged / InvalidTransition | Ready(v) / OK | Failed(e) / OK | Pending / OK |
| Ready(x) | unchanged / InvalidTransition | unchanged / InvalidTransition | unchanged / InvalidTransition | unchanged / InvalidTransition |
| Failed(f) | unchanged / InvalidTransition | unchanged / InvalidTransition | unchanged / InvalidTransition | unchanged / InvalidTransition |

Result: Ready(v) -> Done(Done(v)); Failed(e) -> Done(Fail(e)); Pending/Evaluating ->
Fail(NotReady); absent ID -> Fail(Bounds/WrongScope). All four state constructors
are explicitly witnessed with payloads 37 and 53. The independent model switches
on action and encodes each legal predecessor. Runtime checks compare every occupied
cell and one out-of-bounds cell after each operation, plus exact observed results.
Cancellation example: Pending→Begin→Evaluating→Cancel→Pending; result stays NotReady;
Begin→Succeed(37) then yields exactly 37. Exhausted work must use cancel or remain
Evaluating. It must not call succeed/fail. The owner must discard stale attempts
before retry; no concurrent attempt-token protocol is promised.

## Public-operation matrix

Definitions below are in main.bend; trace/model sources are part of the release.

| Public operations / source | Law or narrower deterministic check | Domain and preservation |
| --- | --- | --- |
| Scopes.new/from; Store.new (main:37,122,192) | lifecycle_separation, exhaustion_never_wraps, zero_store_consumes_scope; lifecycle.bend runtime | first/final/exhausted scopes, zero consumes scope; different lifetimes reject IDs |
| Store.length/limit (main:132,137) | store_trace, zero_limit, limit_clamped; checks.trace Length/Limit | empty/nonempty/clamped bound; every mixed history; reads preserve values |
| Store.alloc (main:213) | generic_growth_write, store_trace; checks.trace and benchmark | freshness, append exact value, earlier IDs, full unchanged, growth 1→2→4→8 |
| Store.get/set (main:218,225) | generic_growth_write, store_trace; 128×128 mixed operations | exact same-slot read, unrelated cells, first/middle/last, wrong scope before invalid index, failure unchanged |
| Store.snapshot (main:156) | generic_growth_write, store_trace; state compare after each operation | all elements in order, empty/nonempty, state threaded and reused |
| Cell.step (main:65) | transition_refinement, universal all 16 state/action combinations | exact payload, rejection preserves original, independent table |
| Cell.result (main:92) | pending_is_incomplete, evaluating_is_incomplete, success_is_exact, failure_is_exact | generic T/E, exact completed payload/error, no incomplete success |
| Memo.new/alloc (main:232,235) | memo_trace; memo_checks.interleaved_witness | pending allocation, stable IDs, full failure, grow after Ready/Failed, exhaust while Evaluating |
| Memo.inspect/result (main:240,252) | memo_trace; inspect_all after each command; Observe commands | exact cell/result, absent/foreign/max slot, no read mutation |
| Memo.apply, begin/succeed/fail/cancel (main:271,276,279,282,285) | universal Cell.step table + memo_trace; all wrappers execute Memo.apply | all 16 pairs, read/write composition, unrelated cells, cancel/retry, terminal preservation |

All other definitions/container constructors are implementation details. There is
no deletion, slot recycling, reset, hash-consing, persistent store versioning,
concurrent completion fencing, or arbitrary affine-element storage in the contract.

## Proof boundary and adequacy challenge

LAWS has 14 claims. Seven are universally quantified: transition refinement;
four exact Cell.result equations; model append/lookup; and
`P.preserved(T,a,b,c,x) == [a,x,c]`, a public three-cell growth/write theorem for
arbitrary Data payloads. The model append theorem alone is not API refinement.
The remaining seven are concrete normalization equations on inhabited traces
(store, zero bound, memo, lifetime, exhaustion, clamp, zero-store scope use).
PROOF fills every claim; complete checker gates require zero holes. No arbitrary
length/history store-refinement theorem is claimed. Runtime tests and timings are
separate evidence. Source hashes are recorded in evidence/source-hashes.json.

Ten type-correct semantic mutants were killed by unchanged native assertions:
wrong allocated slot, writes targeting slot zero, foreign scopes accepted, scope
reuse, wrapping the exhausted scope supply, success before Begin, cancellation
remaining Evaluating, reporting success on a rejected terminal transition,
discarding completed values, and reporting memo success without committing a write.
Each receipt records its successful implementation typecheck and compilation before
the named expected runtime failure. No syntax/type/harness error is counted as a kill;
no mutant survived. These expose constant/stale/discarding behavior that shape-only
laws would miss. Full details: evidence/mutations.json, generated by scripts/mutations.py.

A separate read-only hostile review found two evidence gaps, no concrete code bug:
zero-limit scope consumption, and memo allocation after completion. Both gained
independent runtime regressions; the former also gained a concrete law. Remaining
limits: caller-provided root uniqueness, proper container construction, serial
attempt discipline, Vec/compiler correctness, and untested GPU execution.

Native/JS scaling: powers of two 16,384–524,288; every ID and value checked. Exactly
n public appends and n reads; source-derived Vec copied-slot sum n-1 and log2(n)
growth events. These counts are not instrumented heap measurements. Recorded
medians include process startup; source/native lowering, not timings alone,
support the O(1) indexing and amortized O(1) append claim.

Trust: pinned Bend 2.0.29 checker/normalizer/compiler, Base, Vec, C toolchain and
Bun runtime. Base contains native declarations and unsafe Array.fork/Array.join;
neither unsafe operation is called. Pure core defines no unsafe/native operation,
axiom or hole. Runtime test IO only prints or exits. Actual GPU work is untested.

Perch's eight shared law rules plus the dedicated memo-completion rule target this
packet. Rule loading/matching is checked separately from model execution. The
provider lacks PERCH_API_KEY; there is no model verdict, probability, or live
calibration claim. Clean/broken and held-out controls are retained under review/.
