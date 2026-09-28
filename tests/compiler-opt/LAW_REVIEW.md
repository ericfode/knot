# Optional core pipeline: review boundary

The public entry is `opt.pipeline(depth,book)`. It accepts already checked core,
rechecks its input and every pass output, and returns a complete checked book or
a classified failure. `opt.apply` composes one checked-core transformation;
`opt.compose` sequences them. Types, ordered signatures and exports are carried
unchanged. Only bodies change. The source checker and original emitters are
unchanged by this increment. Their source identities are audited and the original
module bytes remain hard assertions from `baseline.json`.

| Mechanism | Local checked equations | Independent integration evidence |
| --- | --- | --- |
| Case reduction | Matching arm, Value result, ordered field binding, empty binding | Reordered enum arms, second-field projection, all corpus calls |
| Inlining | Zero-parameter argument binding, once-only ordered arguments, level translation | Distinct actuals, nested actual locals, nullary locals, shadowing, erased forward calls |
| DCE | Used reusable let retained; unused reusable let removed | Fixed used-let calls, individual Dead-pass evaluation, used-let mutant |
| Export retention | Function reconstruction retains its exact signature; deleting an input export fails rechecking | Ordered input/output signatures checked before the output catalog; independent Wasm ABI decode; one-export mutant with working main |
| Composition | Empty composition identity; zero round fuel Exhausted; last verified round stops | Each individual pass and full pipeline checked against seed/evaluator/Wasm; original fixed points retained, slow-convergence chains still build |
| Representation | Enum literals propagate; boxed literals are retained | Near-arena shared cells, direct reference/cache controls, boxed-duplication mutant |
| Tail lowering | No separate universal instruction refinement law claimed | Tail fixture contains `return_call`; non-tail recursion and complete tree observers retain fixed values |
| Core checking | Existing quantity/descent helpers reused | 43 literal malformed/valid-core controls; source rejection classifications retained |

The equations quantify over arbitrary tokens, bodies, argument terms, signatures
and continuations where stated. Tags and levels are fixed witnesses in several
laws. `zero_parameter_binding_is_identity` is about binding an empty parameter
list **after relocation**; a closed nullary callee with locals still needs fresh
levels in a caller. `export_reconstruction_preserves_signature` is a structural
lemma used by the complete function traversal, not a quantified DCE theorem.
The translation equation describes U32 arithmetic; the inliner separately checks
the no-wrap, 4,096-level bound before calling it. No holes, new axioms or unsafe
constructs were added. Seed Base and the existing byte builder remain trusted
dependencies; no new published dependency was introduced.

The independent evaluator is `src/eval.bend`; no optimizer code implements its
semantics. The six primary fixtures' expectations were frozen before optimizer
implementation. Additional hostile and observer expectations come from literal
contracts and fresh seed runs, never from optimized results.
Recursive structured outputs are observed by frozen Bend suffixes that recognize
the complete expected trees, paired with near misses. The host only invokes
enum exports and compares integers. It never interprets heap pointers.

Hostile review found four acceptance failures before handoff: nested actual
locals overlapped sequential parameter bindings; nullary callee locals were not
relocated; constructor argument locals overlapped extracted fields; and erased
forward calls could become unsupported self-calls. The fixed policy moves every
callee above both the caller and rewritten actuals, excludes introduced self
calls, and refuses constructor fusion when field scope can capture an argument
local or the original parent remains referenced. All four source witnesses are
frozen regressions. Two raw-core controls independently check the parent and
scope refusal paths. This is substantive scope evidence, not a style judgment.

A larger existing arena program exposed a Bun machine-stack failure when a
fixed-point check compared complete rendered strings. Bounded structural term
comparison now determines the fixed point. The gate independently compares
canonical rendered output after one and two complete pipeline applications.
The original baseline must still be idempotent. New slow-convergence programs
may return a checked intermediate book at the work cap. This corrects the
original fixed-point-as-success contract without deleting its zero-fuel law.

Limits remain explicit: no universal semantic preservation proof, no arithmetic
primitives, no private function metadata, no reclamation and no generalized
recursion. DCE retains affine lets. Constructor fusion is conservative. Changes
in evaluator fuel, stack or arena exhaustion are resource observations; only
successful constructor observations establish value equality. Perch is offline
preflight here; conceptual compression, Delight and memetic ratings are
unavailable until the coordinator runs live review.

Exact source hashes, commands, tool versions, pass domains, failure records and
mutation outcomes are retained in `receipts/optimization.json`. Benchmark source
identities, raw samples, emitted bytes, correctness guards and confidence
intervals are retained with the benchmark report.

The round-2 [regression expectations](regressions.json) were committed before
repair. Independent reproduction records default/max-budget optimization
exhaustion and Fold-only arena exhaustion in [the before receipt](receipts/regressions-before.json).
The final gate keeps host errors separate from actual wrong-value, checked-core,
ABI, availability and allocation failures. A valid empty output book is not
evidence of ABI preservation: the recheck now compares against the input.
