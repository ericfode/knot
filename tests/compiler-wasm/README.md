# Executable enum compiler gate

Run from the repository root with the pinned seed, Bun 1.3.14, Node 22.22.3,
Python 3 and wasm2wat 1.0.41 available:

```sh
python3 tests/compiler-wasm/check.py
bun tests/compiler-wasm/trust.ts
```

The gate builds `src/compile-cli.bend` and `src/eval-cli.bend` for native and Bun
execution, then validates and runs emitted Wasm with Node. It records commands,
source/tool hashes, literal observations, proof checking, failures and semantic
mutants in [receipts/wasm.json](receipts/wasm.json). `trust.ts` independently
inspects the seed-loaded closure; see [TRUST.md](../../research/compiler-wasm/TRUST.md).
Builds and reference wrappers stay under ignored `.local/compiler-wasm/gate/`.
Retained [generated modules and disassemblies](generated/) are intentional
evidence, not build caches. No assembler generates these modules.

For the smallest example, after running the gate:

```sh
.local/compiler-wasm/gate/compile-cli tests/subsets/s1/flag.bend .local/flag.wasm
.local/compiler-wasm/gate/eval-cli tests/subsets/s1/flag.bend flip 65536 0
node scripts/run-wasm.mjs .local/flag.wasm flip 0
wasm2wat .local/flag.wasm
```

The compiler reports `Built\t68`; the evaluator reports
`Evaluated\t0\t1\tOn{}`; the Node execution record has `result: 1`.
`flip(1)` returns 0 and `main()` returns 1. The exact 68-byte artifact is
[generated/flag.wasm](generated/flag.wasm), with its actual decoded
[flag.wat](generated/flag.wat).

The current passing receipt covers:

- 25 programs and 90 fixed calls to the pinned reference interpreter; the
  independent Bend evaluator and real Wasm agree on both compiler build lanes.
- Byte-identical native/Bun modules, sections 1/3/7/10, and only the declared
  scalar instructions. All source functions are exported.
- 32 Invalid/Unsupported fixtures in both lanes: 64 compiler/evaluator rejection
  pairs, with exact phase/code checks and no emitted artifact.
- 44 resource/host observations, including exact evaluator budgets, 67/68-byte
  output bounds, stale-file preservation on failure, bad arguments and file errors.
- Seven type-correct semantic mutants killed by unchanged observations. Five
  emit valid Wasm with incorrect behavior; two break independent evaluation.
- Complete checking of 18 filled laws across the frontend, checker and runtime
  proof entries. Three codec laws are concrete normalizations, not universal proofs.

`make-manifest.py` records reviewed literal expectations in `cases.json`; it
does not derive an oracle from Knot. The host adapter reads/validates/executes
Wasm only. Source semantics and byte emission live in Bend.

The [contract](../../src/CONTRACT.json) fixes CLI limits, outcome codes and ABI
preconditions. Accepted values are nullary enums. Per-type external argument
domains are a caller precondition for raw Wasm and are enforced by the evaluator.
Fields, recursion, a general affine heap, GPU source lowering and self-hosting
are not claimed by this gate.
