# Actual generated code walkthrough

These are saved outputs of the pinned upstream Bend 2.0.29 compiler for our
existing `conformance.bend`. They are not output from a Knot compiler. The
Whiteboard's **Generated code · follow the current executable path** section
links the source, generator, actual artifacts, and GPU record path.

## Generate and verify

From the repository root:

```sh
python3 research/adaptive-tasks/codegen/generate.py
```

The script verifies the existing protocol and seed core hashes, then runs:

```sh
scripts/bend-reference research/adaptive-tasks/conformance.bend -o research/adaptive-tasks/codegen/conformance.c
scripts/bend-reference research/adaptive-tasks/conformance.bend -o research/adaptive-tasks/codegen/conformance.js
```

It executes the retained JavaScript with Node and compiles the retained C with
Clang (`-std=c11 -O3 -lpthread -lm`), requiring both to reproduce the existing
eleven-line protocol transcript. It refuses those CPU-only build flags if the
generated program contains GPU bangs. No generated source is hand-edited.

## What to inspect

| Input / mechanism | Actual output |
|---|---|
| `task.run` tail recursion and Run constructor matches | [conformance.js](conformance.js): `$task$run$` is a loop with tagged objects. |
| `task.tick` modular U32 expression | JS uses `Math.imul` and unsigned shifts; [conformance.c](conformance.c) emits `spin_2` with `U32_BIN`. |
| `task.step_parts` owns a frame list and saved payload | C flattens fields into scalar/Term arguments and takes/releases consumed constructor storage. |
| `fixtures.cpu_frames` tree serialized by Bend | [cpu_frames.records.json](cpu_frames.records.json): postorder operation IDs and initial 64-byte task records. |

The TypeScript seed's `main.ts:cli_emit` chooses `compile_book` for `.c` or
`js_book` for `.js`, after `book_read` loads/checks imports and rejects holes.
`comp.ts:compile_book` emits reachable definitions and continuation segments,
iterates its representation facts, and includes an upstream runtime template.
`comp.ts:js_def` emits the loop used for recursive `run`. The local copies under
`.toolchain/bend-2.0.29-574b6d3/` are pinned by core-file hashes in the receipt.

For the GPU capture, [capture-gpu.mjs](capture-gpu.mjs) runs the independent Bend
fixture generator, then executes the exact `word`/`pack` function text from the
existing host. It checks the source boundaries/constants rather than maintaining
a second packer. It does not request a device or regenerate the device receipt.
The captured four nodes are: leaf 7; leaf 11 with three ticks; unary continuation
with factor 3/bias 5; root fork over nodes 0/2. Parent/slot fields preserve source
result order. The independently evaluated answer is 231817934.

## Generation boundary

The current GPU path generates **record data**. Its
[WGSL machine](../gpu/tasks.wgsl) is handwritten and consumes those records;
Dawn compiles that WGSL through WebGPU. The C/JS outputs are CPU references,
not inputs to a C/JS-to-WGSL translator. Knot's checked-source lowering, Wasm
emission, and device emitter are still future work.

[receipt.json](receipt.json) records exact commands, hashes, tools, and execution
results. [conformance.stdout](conformance.stdout) is the verified transcript.
The existing 38-run device receipt covers the unchanged shader/packer/fixtures;
this capture adds code visibility, not a new GPU execution claim. The new host
capture scripts and generated outputs are outside the earlier Bend-file Perch
audit. No Bend model, proof, or LAW_REVIEW packet changed for this walkthrough.
