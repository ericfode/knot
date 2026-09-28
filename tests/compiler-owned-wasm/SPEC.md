# Owned Wasm gate contract

`knot-owned-wasm-1` selects the existing checked structural source profile and
adds unique `Type` cells and counted immutable `Data` cells. The gate fixes
source results, classification controls, physical result reachability and
layout descriptors in `cases.json`; `expectations.json` binds their hashes.
The literal freeze precedes owned emission. `receipts/reference.json` is the
first seed replay of those expectations. Existing corpora and assertions remain
unchanged.

Every fielded runtime value points to `[tag][live slots]`. A slot contains either
an enum ordinal or a pointer, as specified by its datatype. Erased fields have
no slot. The metadata prefix outside the payload is three words: allocation
state at `p-12`, count at `p-8`, layout at `p-4`. State 1 is live, state 2 is
pending destruction, and state 0 is free. A live Type cell has one owner and
count one. A Data count includes every physical incoming field edge and root.
Opening a shared Data parent acquires its returned child edges before dropping
its parent reference. Returning an enum leaves no cells live.

The runtime owns two fixed 64-KiB pages. Free-list class heads occupy bytes
`[0,16384)`, release frames `[16384,49152)`, and cell storage `[65536,131072)`.
A release frame holds a pointer and scan cursor. Exhausting the step or stack
bound retains that cursor and its pending obligation; restoring capacity and
continuing completes the same release. No release cascade recurses on the Wasm
call stack. Free lists are indexed by live-slot count. Memory reservation does
not shrink when cells are freed.

The test export ABI is privileged. `__heap_memory` exports linear memory;
`__heap_live`, `__heap_allocations`, `__heap_peak`, `__heap_pending`,
`__heap_status`, and `__heap_bump` expose counters. Peak counts cells, including
pending destruction; bump is the byte high-water address. `__heap_enqueue`
queues one obligation, `__heap_clean(quantum)` returns 0 on completion or 3
with retained work, and `__heap_release` drains an ordinary release.
`__heap_share` permits direct count-overflow controls. `__heap_stack_limit`
and `__heap_rc_limit` set bounded test limits and return their old values.
The host never fabricates source values or implements source-language semantics.

`host.mjs` decodes payloads using literal descriptors and independently counts
unique reachable cells and their incoming edges. It compares those observations
with runtime counts after an entry returns. It then releases structured results
and requires zero remaining cells and work. A copied integer address is never
counted as a new owner. The decoder treats debug memory access as privileged;
this is not a production untrusted-pointer API.

The corpus includes all eight fields-Wasm programs and all nineteen recursion
programs. Eleven recursion programs run and eight preserve their existing
Invalid/Unsupported diagnostics. The fields `deep-call` evaluator remains
explicitly Exhausted at its existing parser budget. An additive test entry loads
that unchanged fixture at its already frozen compile limits, characters 65,536
and parser/checker depth 4,096, then invokes the unchanged evaluator with
1,048,576 transitions. Both lanes return the seed and owned Wasm value On. Four data-lifetime source controls retain their
original expectations. Five new programs isolate unused owned graphs, branch
cleanup, a shared value surviving intervening reuse, a structurally recursive
allocation workload, and a 65-cell release chain.

The recursive workload performs at least 32,768 cell allocations in one entry
call. The arena profile exhausts its fixed capacity; owned execution returns
On with zero live cells, and repeated calls keep the same memory/bump bound.
A second persistent test makes 20,000 ordinary fielded calls in one instance.
The stack control suspends at quanta zero and one, blocks at stack capacity one,
and resumes after raising the capacity. The count-ceiling control must fail
without changing the already returned graph or its ownership counts.

Compile both native and Bun seed-built compilers. Their 29 owned modules must
be byte identical. The legacy byte fence checks eight fields modules and twenty
five enum modules from both old profiles and both lanes. Rejections and compile
exhaustion preserve an existing output marker. Runtime Exhausted, internal
ownership violations, host failures and seed failures remain distinct.

Five type-correct semantic mutants must be killed: missing release, double
release, omitted sharing, reuse of a still-live shared cell, and a wrong release
stack bound. Compiler typecheck, Wasm validation, seed/evaluator differential,
physical accounting, concrete mutation witnesses and checked heap laws are
separate evidence. This gate does not establish a general compiler-correctness
or ownership-refinement theorem, GPU reader safety, arbitrary host roots,
closures, cycles, or recovery of a whole interrupted source invocation.
