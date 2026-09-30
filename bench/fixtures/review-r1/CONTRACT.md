# bench-2 review round 1: fixed regression contract

The four confirmed findings at `4bd63ab3` define this bounded repair. Freeze
these literal programs against Bend 2.0.29, commit their observations, then
change the compiler. Existing suites, laws and mutants retain their expectations.

- A constructor expression or pattern requires name/brace adjacency. One or
  three intervening spaces yield `Invalid parse detached-brace`. Adjacent
  expression and pattern controls stay accepted. Constructor declarations have
  their own seed grammar; the spaced declaration control stays accepted.
- A matched parent denotes its refined constructor. Inference of that term
  requires an annotation, including erased and reusable lets. Reject with
  `Invalid check annotation-required`. Annotated reconstruction, ordinary
  variable inference and inference of an unmatched field remain accepted.
- A preceding field binder shadows a global type in subsequent annotations.
  The monomorphic catalog cannot resolve dependent field types, and must refuse
  them as `Unsupported check dependent-field-type` before checking or execution.
  A binder's own annotation precedes its scope. Renamed and later-binder
  controls remain accepted.
- Empty datatypes are valid. Accept unused Type/Data declarations, a declaration
  following the entry, and an unused field signature referencing an empty type.
  Constructors and inhabited domains are never invented for them.

Accepted entries return `On{}`, ordinal 1. Compare the seed's native and Bun
outputs, Knot's independent evaluator and actual Node Wasm execution. Both
emitter profiles remain subject to their existing capability boundaries:
fielded books are Unsupported in the enum emitter. A refused compilation
neither creates a fresh artifact nor replaces an existing artifact.

The seed checks and interprets each original source. Emitted seed builds need
Base, which reserves the name `Empty`: their four empty-datatype controls rename
only that datatype to `Vacant`. Record the complete build-control source beside
the original observation. These renamed builds do not establish native seed
acceptance of the original spelling; Knot's regressions use the original source.

These controls are concrete differential checks. Helper laws are checked
separately; neither constitutes a general parser/checker soundness proof.
Live semantic/style Perch review is reserved for the coordinator.
