# Knot

Design workspace for a Bend 2 compiler implemented in Bend 2.

## Requested outcome

> create a whiteboard for us to design a bend compiler in bend.

The user confirmed Bend 2, direct self-hosting, retained GPU execution, and Wasm
as the compilation target on 2026-09-26, then selected **adaptive continuation
tasks** as the execution model. The working GPU path is WebGPU with WGSL compute
shaders and bounded task exchange between dispatches. The compiler itself may
bootstrap and self-host sequentially on CPU.

The first [compiler contract](src/SPEC.md) pins an enum slice to Bend 2.0.29.
Its Bend lexer/parser runs on native and Bun, with four checked boundary laws,
14 reference fixtures and explicit resource diagnostics. Resolution, checking,
independent value evaluation and Wasm emission remain the active milestone.
The broader compatibility profile and runtime representation remain proposals.

The first [adaptive-task prototype](research/adaptive-tasks/README.md) is now
executable: 12 checked Bend laws, owned checkpoints and slots, and 38 actual
WebGPU runs on an Apple M5 Max. The device code is handwritten WGSL driven by a
native Node host. Wasm execution, Bend-source lowering, and performance remain
separate gates.

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
- [Ranked style review: conceptual compression and high-dopamine reading](docs/perch-style.md)

```sh
npm ci
npm run lint:rules
# After privately setting a TypeSafe key and adding compiler source:
npm run lint -- src/parser.bend
```

Targeted checks retain local usage receipts; `npm run lint:history` summarizes
them. The weekly maintenance review uses those receipts and development
friction to refine rules. See root `AGENTS.md` for the normal workflow.

Finish coherent increments with explicit-path commits and report remaining
changes. See [Git checkpoint procedure](docs/GIT-WORKFLOW.md) for the shared
checkout rules.
