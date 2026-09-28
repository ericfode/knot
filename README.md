# Knot

Design workspace for a Bend 2 compiler implemented in Bend 2.

[Current handoff](docs/HANDOFF.md): clean-main checkpoint, memetic starting point,
next comparison gate, verification limits and owner worktrees.

## Requested outcome

> create a whiteboard for us to design a bend compiler in bend.

The user confirmed Bend 2, direct self-hosting, retained GPU execution, and Wasm
as the compilation target on 2026-09-26, then selected **adaptive continuation
tasks** as the execution model. The working GPU path is WebGPU with WGSL compute
shaders and bounded task exchange between dispatches. The compiler itself may
bootstrap and self-host sequentially on CPU.

The first [compiler contract](src/SPEC.md) pins an enum slice to Bend 2.0.29.
Its Bend lexer, parser, resolver, checker, independent evaluator and direct binary
Wasm emitter run on native and Bun. The [executable milestone](research/compiler-wasm/README.md)
passes 25 source programs and 90 reference calls with byte-identical modules from
both builds, executed by Node 22.22.3. It checks affine/erased usage and exhaustive
matches; fields and recursion remain outside this profile. This is a seed-built
compiler that emits Wasm programs. Compiling itself and lowering source to the
GPU remain subsequent milestones.

The [module increment](tests/compiler-modules/README.md) adds explicit
`--bundle ROOT` commands for local/hash imports and the pinned Base's checked
reachable slice. A combined ordered book preserves file-local aliases and
checks every user definition. An audit lists unchecked Base declarations.
The original single-file command forms remain available; their few diagnostic
changes are listed in the [compiler specification](src/SPEC.md).

The approved [longer goal](docs/SELF-HOSTING-GOAL.md) ends with a reproducible
whole-compiler bootstrap and compiler-generated GPU execution. The first
[structural increment](research/compiler-fields/README.md) checks constructor
arguments, flat field patterns, quantities and parent reconstruction, and runs
them in the independent Bend evaluator. A [bounded owning store](research/owned-store/README.md)
now qualifies affine transfer, rejection and generation retirement on seed CPU
backends. A [Bend-emitted flat store](research/flat-store/README.md) executes the
word-payload transitions in actual Wasm, with complete logical-state comparison
against the independent Bend model. Compiler integration, general value lifetime
and Wasm field lowering remain pending.

The first [adaptive-task prototype](research/adaptive-tasks/README.md) is now
executable: 12 checked Bend laws, owned checkpoints and slots, and 38 actual
WebGPU runs on an Apple M5 Max. The device code is handwritten WGSL driven by a
native Node host. Connecting compiled Wasm to this device path, Bend-source GPU
lowering, and performance remain separate gates.

- [Subset stages and GPU acceptance gates](docs/BEND-SUBSET-STAGES.md)
- [Wasm and WebGPU backend plan](docs/WASM-WEBGPU-BACKEND.md)
- [Selected execution model and comparison](docs/EXECUTION-MODEL-CASE.md)
- [Execution-model laws and proof boundaries](docs/EXECUTION-MODEL-LAWS.md)
- [Runtime and compiler package requirements](docs/EXECUTION-MODEL-DEPENDENCIES.md)
- [Checked Bend binary-join contract](research/execution-models/README.md)
- [Adaptive task protocol and actual-device evidence](research/adaptive-tasks/README.md)
- [Live semantic review of research artifacts](research/PERCH_REPORT.md)
- [Compiler frontend corpus and executable gate](tests/subsets/README.md)
- [Frontend boundary laws and review](research/compiler-frontend/LAW_REVIEW.md)
- [Resolver/checker corpus and executable gate](tests/compiler-checker/README.md)
- [Checker laws, ownership semantics and limits](research/compiler-checker/LAW_REVIEW.md)
- [Source-to-Wasm commands, artifacts and execution gate](tests/compiler-wasm/README.md)
- [Compiler milestone audit, proof limits and trust inventory](research/compiler-wasm/README.md)

## Reference

- [Bend 2 upstream](https://github.com/bendlang/bend)
- [Bend guide](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md)
- [Standard-library inventory for a compiler in Bend](docs/bend-stdlib-inventory.md)
- [Compiler-support package campaign](docs/PACKAGE-CAMPAIGN.md)
- [Six published compiler-support packages and imports](docs/PACKAGE-RELEASES.md)
- [Law quality and publication gate](docs/LAW-QUALITY-GATE.md)

The separately installed local reference compiler reports Bend 2.0.16.
That observation does not select the compatibility or bootstrap pin.

## Development tooling

- [Compiler benchmark framework and hill-climbing workflow](bench/README.md): `npm run bench -- --suite=core`.
- [Offline compiler census](docs/compiler-campaign/inventory/README.md): `npm run census` and `npm run census:check`.

Perch 0.3.5 is installed as pinned local development tooling, with a local adapter
for Bend 2's actual parser. `npm ci` installs the adapter automatically. Bend
source rules review parsed declarations with explicit local helper context.
File targets check each declaration; `file.bend::name` checks a single unit.

- [Perch setup and commands](docs/perch.md)
- [Bend lint suggestions from bend-scrabble](docs/bend-lint-suggestions.md)
- [Existing Jev library and Bend parser integration](docs/bend-reuse.md)
- [Perch maintenance procedure](docs/perch-maintenance.md)
- [Perch review log and calibration decisions](docs/perch-review-log.md)
- [Performance checks and model repair experiments](docs/perch-performance-2026-09-26.md)
- [Perch whole-repository throughput and measured defaults](docs/perch-throughput-2026-09-26.md)
- [Ranked style review: conceptual compression and high-dopamine reading](docs/perch-style.md)
- [Owner-chat Perch pass, changes and code excerpts](docs/perch-thread-pass-2026-09-26.md)

```sh
npm ci
npm run lint:rules
# After privately setting a TypeSafe key:
npm run lint -- src/parse.bend::run --rules compiler-checker-trust,bend-fuel-completeness
```

Targeted checks retain local usage receipts; `npm run lint:history` summarizes
them. The weekly maintenance review uses those receipts and development
friction to refine rules. See root `AGENTS.md` for the normal workflow.

Finish coherent increments with explicit-path commits and report remaining
changes. See [Git checkpoint procedure](docs/GIT-WORKFLOW.md) for the shared
checkout rules.
