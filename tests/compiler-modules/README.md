# Modules and pinned Base

The module loader produces one ordered, qualified book. Every user definition is
checked by the existing checker; the evaluator and enum Wasm emitter operate on
ordinary names. Only the hash-verified Base receives reachable-slice treatment.

[Review round 2](REVIEW-ROUND-2.md) records the four fixed findings, seed freezes,
necessary host-verdict amendments, proof boundaries and the complete gate table.
[Review round 3](REVIEW-ROUND-3.md) records six more: byte-bounded sources,
pinned adapter bytes, the seed's header comment and separator rules, and binders
judged against the constructors declared before them.
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

Entry and bundle paths must have the same absolute/relative basis. Local `./`,
`../`, unprefixed and lowercase hash imports are supported. Files must exist
locally; no fetch or named-package resolution occurs. The legacy single-file
commands retain their import rejection.

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
controls.

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-modules/regen.py
BEND_NO_TELEMETRY=1 python3 tests/compiler-modules/check.py
BEND_NO_TELEMETRY=1 npm run -s gates
BEND_NO_TELEMETRY=1 npm run -s gates:verify
```

The module gate checks 89 fixtures and 97 seed calls, both native and Bun:
178 checks, 194 evaluations, 178 compilations, 66 Wasm observations, 27 identical
Wasm pairs, 124 preserved outputs, 58 trust audits, 30 single-file observations,
22 pin observations, six corrupted-Base observations and six adapter-pin controls.
All 24 semantic mutants are independently seed-typechecked and killed. The four
complete proof entries check 89 filled laws: loader/path 28, qualification 26,
Base selection 20 and pin helpers 15. These are helper/transition proofs, not a
general compiler-correctness theorem.

Offline preflight covers every compiler declaration through 23 bounded manifest
groups with zero structural blockers (1,375 declaration occurrences, all 23
compositions available). The direct eleven-file round-3 review (326 declarations)
has 55 truncated contexts and an oversized combined composition: 56 blockers. Deliberately invalid
binder fixtures fail parsing as expected. No live style ratings or style pass
are claimed; live Perch remains with the coordinator.

The default module emitter remains enum-only. This increment adds no broader
Base syntax, fielded/recursive module Wasm, IO ABI, whole-Base acceptance or
self-hosting. The next identity increment can replace conservative rejection
with canonical handles as part of the IO ABI. Shared receipts are refreshed by
the coordinator after merging.
