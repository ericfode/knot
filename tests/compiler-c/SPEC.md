# `knot-c-1`: fixed contract before emission

The input is a completely checked `core.Book`. The separate compile entry uses
`driver.load`; it never parses, checks or evaluates in the host. The accepted
surface is the union of the current enum, field and first-parameter descent
profiles. Internal traversal containers are not source expressions. Future core
forms require explicit lowering or Unsupported; they cannot pass unchecked.

The emitter produces deterministic C99 in one translation unit. Enum values are
`uint32_t` ordinals. Every datatype with any declared fields uses pointers to
immutable cells `[tag][live fields in declaration order]`, including tag-only
constructors and erased-only constructors. A slot is a union of an ordinal and
a cell pointer, avoiding pointer truncation and aliasing violations. There are
16,384 slots, matching Wasm's 16,384 logical words; physical native bytes depend
on pointer size. Erased fields have no slot and erased expressions never run.
Arguments run left to right, before cell allocation or call parameter transfer.

Tail self-calls stage all live arguments, rebind every parameter simultaneously,
and jump to the function body. Other calls use the C stack with a depth guard
and conservative frame charging. Resource exhaustion exits 4 with
`Exhausted\tc\tarena-overflow` or `Exhausted\tc\tcall-stack`, before an arena
write or further recursive call. The default depth is 256. Guards are runtime
budgets, not source rejection. The host has the ordinary main-thread stack of
the recorded platform; reducing the OS stack is outside this host contract.

Each enum-signatured function has an index-named C wrapper and a dispatch entry
under its exact source name. The main shim accepts `export [live-ordinals...]`
and prints the run-wasm JSON fields. Names and numeric domains are checked.
Malformed host input exits 5; unreachable core/layout failures are Internal
(exit 6). Compiler Invalid/Unsupported/Exhausted remain distinct and leave a
pre-existing output untouched. Generated code imports only the C99 library.

`knot_reset()` starts a fresh execution arena; calling it invalidates all old
cells. Structured functions are private to compiled callers. `knot_invoke`
dispatches enum signatures. `KNOT_NO_MAIN` permits a host harness to include the
translation unit. `KNOT_SOURCE_BYTES` supplies source artifact size in the JSON
record; the host adapter sets it at compilation. No reclamation, threading,
structured host ABI, IO, or general compiler refinement proof is claimed.

Before implementation, expected results already exist in the unchanged three
suite manifests. New observers/probes must fix literal or seed expectations
before the emitter runs them. Independent execution compares seed, Knot eval,
Node Wasm and native C, with byte equality between native and Bun emitter lanes.
Sanitizers and type-correct offset/guard/tag/tail mutants qualify this corpus.
Proofs state bounded lowering invariants; runtime differential evidence remains
separate. Live Perch is the coordinator's gate, not an executor acceptance claim.
