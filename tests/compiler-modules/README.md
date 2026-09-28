# Modules and pinned Base

The module loader produces one ordered, qualified book. Every user definition is
checked by the existing checker; the evaluator and enum Wasm emitter operate on
ordinary names. Only the hash-verified Base receives reachable-slice treatment.

[Review round 2](REVIEW-ROUND-2.md) records the four fixed findings, seed freezes,
necessary host-verdict amendments, proof boundaries and the complete gate table.
[Review round 3](REVIEW-ROUND-3.md) records six more: byte-bounded sources,
pinned adapter bytes, the seed's header comment and separator rules, and binders
judged against the constructors declared before them.
[Review round 4](REVIEW-ROUND-4.md) records six more: relative spellings that
climb above the working directory, import lines inside string literals, longer
result types, a guarded compile output and the corrected single-file claims.
[Review round 5](REVIEW-ROUND-5.md) records four more: the census tests, now a
registered gate; call heads read in their lexical scope; `&`, `|`, application
and arrow types reported Unsupported; and the single-file deltas, which the
coordinator accepted on 2026-09-28.
[Review round 6](REVIEW-ROUND-6.md) records three more: a file's own earlier
qualified names in the freshness test, the seed's `.//` and `0x<hash>//`
imports, and dotted binders resolved in scope.
The earlier [verification receipt](receipts/verification.json) and preflight
receipts without `review-round2` remain historical evidence for the first round.

## Commands

Build each `src/{check,eval,compile}-cli.bend` with the pinned seed. Run from the
repository root with `BEND_NO_TELEMETRY=1`:

```text
check-cli --bundle tests/compiler-modules/bundle/lib source.bend
check-cli --audit-bundle tests/compiler-modules/bundle/lib source.bend
eval-cli --bundle tests/compiler-modules/bundle/lib source.bend main 65536
compile-cli --bundle tests/compiler-modules/bundle/lib source.bend output.wasm
```

Entry and bundle paths must have the same absolute/relative basis. A relative
entry, bundle or import that still climbs above the working directory after
normalization is `Unsupported load path-identity`. Local `./`, `../`, unprefixed
and lowercase hash imports are supported, and so is one extra slash after a
leading `./` or hash head, as in the seed. Files must exist locally; no fetch or
named-package resolution occurs. The output of `compile-cli --bundle` may not
name the entry, a loaded module or the Base, and must be a canonical,
non-climbing path. The legacy single-file commands retain their import
rejection; their few diagnostic changes are listed in `src/SPEC.md`.

## Mechanism and trust boundary

`imports.bend` reads headers and normalizes lexical paths. `qualify.bend`
resolves file-local aliases and lexical binders with distinct term/constructor
inventories. `load.bend` keeps pending headers, active paths and completed paths
in one explicit machine. Completed dependencies are reused; back edges reject.

`path-host.bend` queries exact filesystem component spelling and symlink status
through small native/Bun adapters. Symlink and case aliases report
`Unsupported load path-identity`. Entry and bundle roots are checked before
normalization; user files are checked before reading. Host errors stay separate.
The query assumes stable files, and does not implement realpath module identity.

`base-pin.bend` verifies the pinned Base SHA-256 before `base-load.bend`
inventories its 466 declarations. Base names register at the import event.
Bare and qualified collisions reject in either load order, and user definitions
cannot shadow Base dependencies. The slice follows references from every user
definition. A pattern or let binder may not name a constructor registered
before it (all of Base once imported), even when that constructor is outside
the slice; a later constructor leaves it a variable.

The audit follows complete checking and emits `BasePin`, loaded `Module` paths,
and the exact ordered `BaseChecked` / `BaseUnchecked` partition. Unchecked Base
remains a trust boundary. The seed, arithmetic lowering, IO primitives and path
metadata query remain trusted. The Base toolchain symlink is intentional and is
protected by the content digest.

## Independent verification

The original 42 fixtures, four regressions and five boundary probes remain
unchanged. Twelve review fixtures were frozen from the pinned seed before their
repairs in `0474aa7` and `483f684`. Two controls preserve canonical duplicate
imports and a no-Base namespace. The case-alias probe explicitly requires a
case-insensitive filesystem. Round 3 adds 26 seed fixtures in `review-round3/`,
five of them also through the single-file CLIs, and six literal adapter-pin
controls. Round 4 adds 23 seed fixtures in `review-round4/`, ten of them also
through the single-file CLIs and ten run from their own directory with literal
entry and bundle spellings, and eleven literal output-guard cases. Round 5 adds
18 seed fixtures in `review-round5/`, seven of them also through the single-file
CLIs: shadowed call heads with their controls, and type continuations. Round 6
adds 28 seed fixtures in `review-round6/`, ten of them also through the
single-file CLIs: own-file name collisions, rooted imports with seed-rejected
controls, and dotted binders, free and rebound.

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-modules/regen.py
BEND_NO_TELEMETRY=1 python3 tests/compiler-modules/check.py
BEND_NO_TELEMETRY=1 npm run -s gates
BEND_NO_TELEMETRY=1 npm run -s gates:verify
BEND_NO_TELEMETRY=1 npm run -s census:test   # also a runner gate since round 5
```

The module gate checks 158 fixtures and 166 seed calls, both native and Bun:
316 checks, 332 evaluations, 316 compilations, 90 Wasm observations, 39 identical
Wasm pairs, 238 preserved outputs, 84 trust audits, 192 single-file observations,
22 pin observations, six corrupted-Base observations, 22 output-guard observations
and six adapter-pin controls. All 47 semantic mutants are independently
seed-typechecked and killed. The four complete proof entries check 99 filled
laws: loader/path 36, qualification 28, Base selection 20 and pin helpers 15.
These are helper/transition proofs, not a general compiler-correctness theorem.

Offline preflight covers every compiler declaration through 23 bounded manifest
groups with zero structural blockers (1,425 declaration occurrences, all 23
compositions available; `checking` is 47,988 of its 48,000 bytes). The direct
eight-file round-6 review (238 declarations) has 26 truncated contexts, none of
them a changed declaration, and an oversized combined composition: 27 blockers. Deliberately invalid
binder fixtures fail parsing as expected. No live style ratings or style pass
are claimed; live Perch remains with the coordinator.

The default module emitter remains enum-only. This increment adds no broader
Base syntax, fielded/recursive module Wasm, IO ABI, whole-Base acceptance or
self-hosting. The next identity increment can replace conservative rejection
with canonical handles as part of the IO ABI. Shared receipts are refreshed by
the coordinator after merging.
