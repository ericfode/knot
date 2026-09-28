# Monomorphic closures: bounded contract

This packet selects the closure increment's fixed obligations from
`FIXTURES.md` and `src/SPEC.md` for bounded review. `expectations.json` and the
seed remain authoritative; this summary changes no result or quality target.

Support `x => body` and `+x => body`, nondependent monomorphic arrows `A -> B`,
function-valued parameters and Type fields, variable calls, named values,
partial application, returned and nested closures, closure lists and CPS.
Parenthesized arrow domains and right association matter. All code is checked
before execution or emission. Function types have kind Type, never Data.

Captures transfer affine usage when the closure is built. Building two thunks
that share an affine value is Invalid even when only one will be invoked.
Promoted Data parameters and fields may be shared by several thunks. Erased
reads are scope/type checked, consume no live usage, and occupy no runtime
slot. Closures remain affine even when their captures are Data. A lambda binder
shadows its surrounding names; `_` discards its argument and cannot be read.
Matches inside lambda bodies are Invalid under the pinned seed's binder rules.

Application is curried. A definition may return further arrows, and a call may
consume them. Partial application evaluates and saves supplied arguments once,
in order. A partial self-call must already supply a first-parameter descendant;
a self-call inside a continuation preserves the enclosing descent evidence.
Forward live calls remain Invalid. Erased remaining parameters, generics,
dependent arrows, templates, do-notation and lambda-match shorthand retain their
explicit Unsupported boundary. Unsupported never becomes Invalid merely because
a feature is unavailable. Exhausted, host and internal failures stay separate.

The independent evaluator interprets closures as a body plus a captured
environment. Wasm instead defunctionalizes each used function type into a
closure datatype and apply dispatcher, using the existing cell layout:
`[dense site tag][live captures]`. Site identity and dense runtime tag are
separate. No function pointers, indirect calls or tables. Tail applications
use `return_call`; initializer and argument applications use ordinary call.
The fixed 65,536-byte bump arena has no reclamation. Function values never cross
the host boundary, whose live arguments and results remain nullary enums.

The core idea under review is one explicit code/environment representation
shared by all function-value forms, followed by ordinary constructor/case/call
lowering. Exact type/quantity checks precede that transformation. Checked laws
state capture, type identity, lowering and evaluator-step equations. Differential
seed/evaluator/Wasm agreement and semantic mutants independently test the whole
mechanism. These are bounded corpus and local algebra results, not a general
checker-soundness or compiler-correctness theorem.

The frozen corpus has 42 fixtures, 292 seed calls and 18 seed rejections.
`generic-choose-bind` retains its original agree requirement but has 19 calls
blocked on the separate generics increment. Supplemental seed-fixed probes
exercise the exact erased-capture arena boundary and 2,048 tail continuations.
The five required mutants corrupt dispatch, drop a capture, duplicate affine
capture usage, store an erased capture live, or replace a tail call with call.
Existing gate assertions remain unchanged except the separately committed
seed-backed structural/function-field catalog amendment.
