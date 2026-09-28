# GPU emission contract — gpu-emit

Frozen before emission implementation. Input is a completely checked `core.Book`,
an entry name and enum-only host ordinals. Output is one invocation as a
`knot-device-records-2` JSON bundle. It never evaluates source to choose branches
or substitutes interpreter results for code. Every source body is checked by
`driver.load`; only the selected entry's live call closure is emitted.

The allocation unit is a static activation: 512 capture slots, disjoint from
all other activations. Each lexical binding names one owner. Affine occurrences move that owner; reusable Data occurrences share it and
retain the binding until scope exit. Each selected Case opens its scrutinee, binds live fields in declaration
order, and releases unused owners. Erased bindings/arguments/fields generate no
work. The device alone selects branches. Cleanup precedes function return and
tail self-jumps. The sole surviving root at halt is the result.

An acyclic call gets a fresh activation and two one-shot joins. The argument
join transfers ordered live arguments to the parameter range; the return join
saves the caller's complete activation interval and returns one result. Attempts
are the literal 1 issued by their sole start. Tail self-recursion evaluates new
arguments, releases the old scope, transfers them to the same parameter slots,
and jumps back to the entry. It allocates neither a join nor an activation on
the back edge. Non-tail self-calls are `Unsupported records recursive-activation`.
Any other live call in a recursive function is conservatively
`Unsupported records dynamic-attempt`, even when a more precise path analysis
could prove it one-shot. General recursive allocation is outside version 2.

Entry parameters and results must have enum-only datatypes. Structured results
and arguments are `Unsupported records entry-result` / `entry-parameters`.
Unknown entry, wrong arity and ordinal domain are HostFailure. Unsupported or
exhausted compilation writes no bundle and preserves a pre-existing output.

Limits: 64 static activations, 512 captures per activation, 512 joins, 16,384
instructions, emitter depth 4,096, JSON output 1,048,576 bytes. Device defaults
are 1,024 objects, 2,048 pending releases, maximum emitted live arity (at least
1), u32 identity/attempt limits, RC limit 65,535, storage limit 16 MiB. Resource
failure is Exhausted, never Invalid or Unsupported. Host and internal errors
retain separate categories. There is no cancellation or concurrency lowering.

`cases.json` fixes literal expected tags; `expectations.json` records pinned
seed executions before implementation. Source comparisons are seed ⇔ independent
Knot evaluator ⇔ actual Knot Wasm ⇔ records CPU simulation. A coordinator device
run adds the identical emitted bundles on Metal; CPU simulation is not a GPU
execution claim. Complete final ownership is checked as well as the result tag.
The source recursion fixtures are a new qualification of their bounded actual
Wasm execution, not a change to the existing Wasm profile's general claim.

Mutants preserve Bend types and bundle transport validity: wrong branch tag,
move in place of Data share, omitted release, swapped logical argument slots,
and stale delivery attempt. Neither a seed type error nor a validator refusal
counts as a semantic kill. Model laws cover the stated lowering helpers, not a
general compiler-correctness or WGSL-refinement theorem.
