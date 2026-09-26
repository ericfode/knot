# Structural declaration checkpoint

Knot now parses and resolves monomorphic constructor field declarations. It
retains field order, quantity, type identity and source spans, and checks
field kinds even for unused types. Forward and mutual datatype references work.
This is the first increment of the [active goal](../../docs/SELF-HOSTING-GOAL.md).

Field execution remains `Unsupported`. Pattern-bound fields, owned storage,
transfer/drop, recursive functions and generated GPU execution are outstanding.
The enum executable profile and all existing generated Wasm modules are preserved.

- [Contract](SPEC.md)
- [Laws, independent observations, mutants and proof limits](LAW_REVIEW.md)
- [Executable fixture gate](../../tests/compiler-structural/README.md)
- [Current trust inventory](receipts/trust.json)
- [Targeted Perch review](PERCH_REPORT.md)
- [Runtime support requirements](../../docs/RUNTIME-SUPPORT-PLAN.md)

The implementation remains seed-built Bend using recursive datatypes, generic
Base containers, affine/reusable/erased binders, captures and local imports.
Accepted executable programs remain the no-Base enum profile. The declaration
observer additionally accepts the monomorphic field profile. Host capabilities
remain byte/file IO and engine invocation; no host adapter implements Bend
source semantics. The full implementation language and dependency closure still
exceed the accepted language; closing that gap is a later goal gate.

Run `python3 tests/compiler-structural/check.py`, then
`bun tests/compiler-structural/trust.ts`. The gate checks 16 pinned-seed fixtures,
native/Bun catalog and compiler outcomes, 256/257-field bounds, five new filled
laws, and seven type-correct semantic mutants. The three existing frontend,
checker and source-to-Wasm gates were also rerun for this increment.
