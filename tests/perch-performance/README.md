# Bend performance repair benchmark

Three small, runnable repair tasks exercise compiler-support list patterns:

| Case | Required result | Baseline defect |
| --- | --- | --- |
| `growing-prefix-copy` | map `3*x+1`, preserve order | append to a growing prefix |
| `invariant-summary` | add the whole-list sum to each value | recompute a fixed sum per element |
| `indexed-linked-list` | multiply each value by its one-based position | repeatedly index from the list head |

All operations wrap modulo 2^32. Each case has its complete public contract in
`cases/<id>/CONTRACT.md`, a source of at most 19 lines in `baseline/main.bend`,
a checked linear control in `clean/main.bend`, and visible `smoke.json` examples.
The standard list type is `List<&2,U32>`. Imports and quantities are checked by
Bend 2.0.29, pinned revision `574b6d39a235b539eb19a5c532993a0abb3d11ad`.

For a repair trial, provide only the baseline source, contract, visible smoke
examples, and the selected Perch finding. Do not provide the clean controls,
held-out sources, mutants, runner, operation limits, or hidden probe values.
Models edit a separate candidate; they do not edit this directory or its gates.
Every model is evaluated by the same frozen gate.

```sh
python3 tests/perch-performance/evaluate.py \
  --case growing-prefix-copy \
  --candidate /absolute/path/to/candidate.bend \
  --output /absolute/path/to/result.json
```

Exit 0 means both behavioral and performance gates passed; exit 1 means a
rejection, compilation failure, gate failure, or harness error. Read `status`
and the individual gates, rather than treating every rejection as a semantic
kill. The receipt retains candidate/compiler/gate/generated-code hashes,
instrumentation coverage, per-size operation counts, and probe results.
A neighboring `.artifacts` directory retains the exact candidate, typed entry
wrapper, generated JavaScript, instrumented JavaScript, and tool output.
Credentials are not passed to subprocesses.

## What is measured

`compile.ts` uses the pinned compiler's checked `load()` library API. The typed
entry wrapper enforces `solve(List<&2,U32>) -> List<&2,U32>`. `instrument.mjs`
parses emitted JavaScript with the repository's installed tree-sitter package.
It instruments every function body, loop body, and object/array literal,
including Base helpers and the generated trampoline. The candidate supplies
no counters. `run.mjs` enables counters immediately before the public call and
disables them before observing the result. Host input construction and output
comparison are outside the measurement. JavaScript native U32 primitives have
constant cost; the task excludes arrays, strings, FFI, IO, unsafe definitions,
and other mechanisms that could hide bulk work in an uninstrumented host call.
This is a bounded benchmark restriction, not a general Bend security sandbox.

The independent JavaScript oracle computes the entire expected list. Nineteen
fixed probes cover empty/singleton inputs, order, duplicates, zero, U32 overflow,
and deterministic mixed values through length 1024. Six additional measured
probes have lengths 32, 64, 128, 256, 512, and 1024. Every measured result must
also match the oracle. Work must be nonzero, at most `64*n+128`, and grow by no
more than 2.65 per doubling from n=128. A hard operation cap and process timeout
bound pathological candidates; timeout is a failure, not positive evidence.

These are finite correctness and scaling checks. They are not universal proofs
of equivalence or asymptotic complexity, and they establish no native/GPU result.
Wall-clock durations describe harness execution only and are not acceptance
thresholds. Gate source and exact compiler files are frozen in `gate-lock.json`;
its SHA-256 is
`be943077833ee612b6f8ac9b56bc5fdb1af66971c04830b07976e8ca312a6fbb`.
The evaluator refuses changed locked files. The later calibration controls have
a separate hash manifest; adding them did not change the repair-trial gate.

## Reproduced control evidence

`evidence/controls.json` records 27/27 expected outcomes. Every control compiles.
All nine inefficient sources pass the behavioral probes and fail the work gate.
All nine linear sources pass both gates. Nine semantic mutant runs are killed
by output mismatches: constant-empty output, reversed output, and implementations
that work only for lists of at most 32 items.

| Case | Baseline work at n=1024 | Linear control work at n=1024 |
| --- | ---: | ---: |
| `growing-prefix-copy` | 1,051,656 | 4,108 |
| `invariant-summary` | 1,051,655 | 3,080 |
| `indexed-linked-list` | 534,024 | 2,055 |

The first held-out pair per case was written before live rule calibration.
The `fresh-held-out` pairs use different source formulations and were written
after threshold selection for a subsequent calibration holdout. No expected
labels are embedded in Bend source comments. These labels and the operation
oracle are deliberately outside the model's repair prompt.

Reproduce all original, held-out, and semantic controls with:

```sh
python3 tests/perch-performance/verify-controls.py \
  --output /absolute/path/to/controls.json
```

Prerequisites are the repository's existing `npm ci` installation, Node, Python 3,
Bun, and the pinned source referenced by `scripts/bend-reference`. This benchmark
installs nothing and contacts no model provider. Live Perch calibration and model
repair outcomes are separate evidence owned by the surrounding experiment.
