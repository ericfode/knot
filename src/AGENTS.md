# Compiler ownership

This subtree is owned by Compiler Planning. Implement compiler semantics in
Bend. Host scripts may build, invoke the compiler, run Wasm, compare observations,
and record evidence; they may not implement the parser, checker, evaluator, or
emitter. Preserve the published support packages and adaptive-task prototype.

Read `SPEC.md` before changing the accepted profile. Keep invalid input,
unsupported features, exhaustion, and implementation failures distinct. A
resource limit cannot establish rejection or acceptance of the source language.
Commit each verified increment according to the root Git workflow.

The pinned seed's surface restrictions matter when writing the compiler itself:
match only parameters/fields, in their binder order. Give a computed scrutinee
its own helper. Use `syntax.choose` with thunks for lazy conditionals and
`syntax.bind` for computed results. Annotate local constructor values explicitly.
Keep structural fuel first in recursive dispatchers. These rules were recovered
from actual seed diagnostics while implementing the first lexer.
