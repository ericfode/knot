# IO host review 2 contract

The coordinator's confirmed findings fix these expectations before host repair.
`review-expectations.json` extends host conformance; it does not alter the
compiler suite's frozen `../expectations.json` or its 40 source fixtures.
`review-seed.json` records the independent pre-repair seed witnesses.

- **Empty write.** `empty-write.bend` opens a path, writes `[]`, reads 64 bytes,
  closes, and reports both Results. For an `r` handle, writing `[]` returns
  `Done`, including directory handles. The following read still returns the
  original file bytes or directory errno 21. Four literal cases cover a file,
  an empty file, a named directory and `.`. All four agree in the pinned seed's
  interpreter, native build and emitted JS: 12 runs. Nonempty bytes on `r`
  still fail with 9; the invalid-element flag still takes precedence with 22.
- **Secret paths.** Every listed spelling of `.env` or `.env.*` is refused
  case-insensitively in each supported mode (`r`, `w`, `a`). The refusal is
  `HostFailure io sandbox`, exit 5, before open/truncate/append. Probes create
  only dummy `.env` and `sub/.env.local` files inside a fresh private sandbox;
  all their bytes and directory entries must remain unchanged.
- **Oracle faults.** Any seed stdout, stderr or merged stream containing
  `bend: memory fault` aborts freezing as `Exhausted seed memory-fault`, even
  with exit 0. An ordinary seed rejection remains distinct. Test both passes
  of `--write`: an exhausted pass must leave the previous expectation bytes
  unchanged. Synthetic fault streams test the refusal, not Bend semantics.

The host ABI stays independent of guest heap, continuation, image and native
Wasm lowering layouts. D14's VM owns those representations and calls `knot_io`.
These hand-assembled Wasm probes establish host behavior, not source lowering
or an IO evaluator capability. Live Perch review belongs to the coordinator.

Compiler-sized C1 inputs use the native seed lane under D14. The bounded IO
fixtures keep their JS oracle only while it completes without a lane fault.
Before increasing CLI budgets, the compile-cli owner must replace the
post-write `List.length(bytes)` and audit other output-sized non-tail traversals
with an accumulated/requested count or an explicit tail-recursive traversal.
No compiler budget is changed by this host increment.
