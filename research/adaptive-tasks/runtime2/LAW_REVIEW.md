# Owned device records: law review

Scope is version 2's single-writer object/capture/join/cleanup machine plus its
bounded PC driver. Inputs and literal controls preceded implementation. Bend
uses persistent algebraic lists; Python independently uses an owning graph;
WGSL uses flat word arrays. No host transition code is reused by Bend or WGSL.
The host oracle is research evidence authorized specifically for gpu-2.

The abstraction maps each nonzero identity in a capture, live object child,
pending stack entry or join result to one owning edge. A Type object has exactly
one incoming edge; Data RC equals the incoming count. Saved join capture ranges
name existing captures, so they do not add edges. Allocated objects reference
only earlier identities; cycles/backpatching have no instruction. Free storage
can be reused, but logical identities cannot. RC metadata precedes the exact
`[tag][live slots]` payload, preserving its own offsets.

| Family | Observation and inhabitants | Checked law / differential evidence | Mutant |
|---|---|---|---|
| Checked layout | Empty tables; counts 1/2/64/4096; exact and one-past storage; U32 last word | `span_exact_max`, `span_overflow_preserves`, `span_product_preserves`; 64 host controls | offset wrap |
| Owned captures | Type 7 moves to capture 5; second move refuses and keeps 5 | `move_once`; complete move-once fixture | source retained after move |
| Data lifetime | Shared leaves/tree/list; release one edge preserves alias, last frees; Data cannot own Type | `type_cannot_share`, `decrement_keeps_alias`; tree/list traces and independent edge census | skipped decrement |
| Open/rebuild | Mixed Type/Data parent; unique opening transfers; shared opening aggregates repeated child increments | `open_transfers`, `shared_open_atomic`; exact/overflow shared-open and rebuild literals | six-mutant suite plus fixed intermediate owners |
| Resumable cleanup | Pending roots remain after budgets0/1, reader barrier, and work-stack capacity failure | `cleanup_retains_work`, `reader_retains_work`; full retained stack and free count | double child release |
| Attempts/cancel | Saved Data and arrived Type moved to cleanup; cancelled generation 1 cannot deliver into 2 | `stale_preserves_source`, `cancel_owns_pending`; stale replacement fixture | stale accepted |
| Ordered/n-ary joins | Right 9 before left 7 yields ordered [7,9], noncommutative 709; reverse 64 deliveries retain order | `right_before_left`, `nary_once`, `empty_join_once`; repeated resume/start controls | completion twice |
| Classification | Unknown opcode, reserved words, malformed arity and mixed refusal | `unsupported_preserves`, `reserved_preserves`; host and dynamic controls | wrong outcome is a mismatch |
| Driver | Zero budget, suspended captures, branch/jump, saved continuation code, halt and fault | 10 filled driver laws; 7 programs / 29 complete rounds across three CPU lanes | WGSL swapped branch, zero-budget progress, ignored resume code, terminal cleanup exhaustion |

`PROOF.bend` imports `DRIVER-PROOF.bend` and fills all 28 laws: 17 quantified
laws and 11 concrete normalizations. Quantification over tags/states is exactly
what those statements say. These are not inductive global ownership, arbitrary
scheduling, source lowering, or WGSL memory-refinement theorems. Some model
constructors can represent malformed metadata; the runtime admits empty bundles
and checked transitions, and the independent graph audit covers generated states.

The six Bend mutants typecheck before execution. Every one fails a named filled
law and the unchanged literal/differential witness. Ten WGSL semantic variants
construct all three pipelines on Dawn's null backend. Hardware mode first
requires the baseline to match all cases, then kills only a type-valid variant
on a named complete-state/ownership/guard mismatch. Shader errors, host/API
failure, null execution and missing fixtures never count as kills.

Adversarial review found and fixed three concrete inconsistencies without
changing any prior assertion: wrong open arity classified Exhausted in WGSL,
an undeclared smaller GPU quantum bound, and compound invalid/resource refusal
precedence. Added controls pin each boundary. Optional supplied layout fields
now reject float/bool values even when Python numeric equality would match an
integer. A giant literal fixture exceeded seed expansion depth; runtime fixture
generation preserves the exact original command sequence and 4096 boundary. A final driver review
also caught terminal cleanup exhaustion: the new program control and quantified
law require suspension at the same PC with the pending stack intact. The
corresponding tenth WGSL mutant makes that exhaustion terminal.

The largest fills compare first/full/refused complete states and every status;
all other command observations are complete. The Python audit independently
checks all owners after every transition, including unsampled large-fill states.
Device readback also checks empty/padding words, all four capacity guards and
both executed/published snapshots. It compares actual branch/PC state in program
mode; the host never chooses source branches.

Limits: no fresh Metal run here; no general global arena issuer/restore, dynamic
recursive activation allocation, multiple simultaneous device writers, cyclic
Data, source compiler emission or general proof of host/device refinement.
The old runtime-1/38-case sources are unchanged. Fresh CPU replay agrees with
the retained runtime-1 model; old Metal receipts are compared as historical
evidence only. The coordinator must rerun both original device probes.

Style preflight parses 146 declarations in 10 files. 24 declarations have truncated
contexts (5 caller/byte,1 file,18 helper); those same 24 cannot receive the
supporting-role exemption. Composition is available at 36,810/48,000 bytes,
with no unresolved references. All five style axes remain unrated. Live Perch
and these context dispositions are coordinator work, not an automatic pass.
