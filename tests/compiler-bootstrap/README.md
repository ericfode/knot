# Bootstrap harness: E2E-2 self-parse and E2E-3 fixpoint

This harness measures how far the self-hosting pipeline gets, and records that in a
deterministic receipt. It builds with the pinned seed, invokes compilers and
modules, and compares bytes. It implements no parser, checker or emitter. See the
campaign's [definition of done](../../docs/COMPILER-CAMPAIGN.md), items 1 and 2
and milestones 9 and 10, and the [bootstrap protocol](../../docs/BEND-SUBSET-STAGES.md#bootstrap-protocol-and-first-self-compiling-stage).

## Commands

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-bootstrap/check.py        # run all stages, write receipts
python3 tests/compiler-bootstrap/check.py --judge RECEIPT            # apply the gate verdict to a receipt
npm run -s gates                                                     # includes the registered `bootstrap` gate
```

The command takes about 30 seconds on an idle host; corpus runs use two workers. It exits 0 only when the gate verdict holds;
a blocked stage alone is not a failure. Build products go to the ignored
`.local/compiler-bootstrap/`, which is cleared first so a stale artifact can
never count.

## Stages

| Stage | What runs | Passes when |
| --- | --- | --- |
| `e2e2.reference` | The seed builds `src/parse-cli.bend` (native and Bun). Both run on every corpus file. | Both lanes agree byte for byte on every file. |
| `e2e2.compile` | C1 compiles `src/parse-cli.bend` and its imports to a parser module. | It prints `Built` with an artifact of that size. |
| `e2e2.self-parse` | The parser module runs on the same corpus through `host.mjs`. | Exit, stdout and stderr are byte-identical to the reference on every file. |
| `e2e3.c1` | The seed builds C1 from `src/compile-cli.bend` (native). C1 compiles the conformance corpus. | Every program and reject matches. |
| `e2e3.a2` | C1 compiles S (`src/compile-cli.bend` and its imports) to A2. | It prints `Built` with an artifact. |
| `e2e3.a3` | A2 compiles the same S to A3 under `host.mjs`. | It builds A3. |
| `e2e3.fixpoint` | A2 and A3 are compared. | They are byte-identical. |
| `e2e3.conformance` | A2 and A3 each compile the conformance corpus. | Every call tag and rejection matches, and every module is byte-identical to C1's. |

The corpus is every `.bend` file that the gate runner exports: tracked files plus
unignored untracked ones. In a clean checkout that equals `git ls-files '*.bend'`.
Inside the runner's scratch copy, which has no `.git`, the harness walks the
exported tree and excludes `.local`, `.toolchain`, `node_modules` and `build`.
The seed is the oracle, so the reference corpus is a set of observations, not
expectations derived from Knot.

The conformance corpus reuses existing gate fixtures. It has the 25 programs of
`tests/compiler-wasm/cases.json`, with 90 seed-derived call tags run through
`scripts/run-wasm.mjs`, and the 32 fixed rejections of
`tests/compiler-checker/cases.json`.

Only the seed step invokes `scripts/bend-reference`. A2 and A3 are produced
without any seed or upstream fallback. The compiler entry is one constant,
`COMPILER` in `check.py`. When a unified profile driver replaces
`src/compile-cli.bend`, change it there.

## Today (receipt `receipts/progress.json`)

| Stage | Status | Detail |
| --- | --- | --- |
| `e2e2.reference` | reached | 525/525 files; the native and Bun lanes agree |
| `e2e2.compile` | blocked | `Unsupported lex literal 291:292:10:44` (exit 3, no artifact) |
| `e2e2.self-parse` | not-run | its prerequisite `e2e2.compile` is blocked |
| `e2e3.c1` | reached | 57/57 (25 programs, 90 calls, 32 rejects) |
| `e2e3.a2` | blocked | `Unsupported lex literal 341:342:12:60` (exit 3, no artifact) |
| `e2e3.a3`, `e2e3.fixpoint`, `e2e3.conformance` | not-run | the prerequisite chain starts at `e2e3.a2` |

The reference outcome histogram measures how much of the repository Knot's own
parser accepts today: 142 of 525 files parse. Most of the rest stop at
`Unsupported` literal, declaration-form or parameter-type classifications. All
30 `src/*.bend` files are `Unsupported`, never `Invalid`. The 17 `Invalid`
results are test fixtures, and they are recorded, not judged:

- Six are the intentionally malformed `tests/subsets/classification/*-malformed`
  fixtures.
- Eleven are `tests/compiler-closures` fixtures. Five of these are classed
  `positive` or `edge` in that suite, so Knot's parser calling them `Invalid` is
  a D4 gap for the closures increment to close.

## Receipts

- `receipts/progress.json` holds, per stage: the status (`reached`, `blocked` or
  `not-run`), the corpus size, and the agree and disagree counts. A blocked stage
  also holds its raw blocker (source `knot` or `harness`, argv, exit, stdout,
  stderr). A not-run stage holds its `prerequisite`. The receipt also records:
  - `tiers`: each tier's first blocking classification;
  - `bundles`: the frozen source bundle S, as the transitive imports of each
    entry, including Base and the ByteOutput package, with hashes;
  - `own_source`: the reference observations for `src/*.bend`;
  - the seed build hashes, the controls and mutants, and the verdict.
- `receipts/reference.json` holds one row per corpus file: its source hash, the
  exit status, and the stdout and stderr hashes.

Both receipts contain no dates, timings or absolute paths. Two consecutive runs
produce byte-identical receipts.

## Gate verdict (`bootstrap`)

`judge()` reads only recorded fields. It derives each classification from the exit
status and the first stderr field, and the two must agree. The verdict fails when:

- a reached stage lacks exact agreement;
- a blocked stage's blocker is anything but `Unsupported` or `Exhausted`
  (`Invalid`, `HostFailure`, `InternalFailure`, a signal, a stack trace, or a
  mismatched exit and word);
- a not-run stage follows a reached prerequisite;
- any `src/*.bend` reference observation reports its own source as `Invalid` or
  worse (D4).

Every run also checks that the judge is not vacuous. It writes scratch copies of
the receipt under `.local/compiler-bootstrap/judge/`, with one recorded
classification substituted in each, and runs `check.py --judge` on every copy.
The unmutated copy must pass. All eight mutants must be rejected:

1. Blocker `Invalid` (exit and word).
2. Word only.
3. Exit only.
4. Host crash (exit 1 with a stack trace).
5. Signal exit.
6. An own-source row turned `Invalid`.
7. A reached stage with a disagreement.
8. A stage that is not run after a reached prerequisite.

The runner's `counts()` rechecks the recorded verdict independently.

Four controls exercise the comparison paths, which have no Knot-built module to
run today. They use test doubles, not Knot evidence:

- A one-byte perturbation must produce exactly one disagreement.
- A hand-assembled replay module must agree on one file and disagree on
  another through `host.mjs`.
- A module that has an import must reach the IO seam and report
  `Unsupported host io-abi-pending`.
- An invalid module must report `HostFailure`, so it can never pass as
  Unsupported.

## Host seam and the parser-as-Wasm ABI stub

`host.mjs REQUEST.json` is the only way the harness runs a Knot-built module. It
takes a request of the form
`{"abi": "auto", "module": path, "runs": [{"argv": [...], "inputs": [paths], "outputs": [paths]}]}`.
It returns
`{"abi", "blocked", "runs": [{"exit", "stdout", "stderr", "files", "host"}]}`,
with bytes in base64. The host never writes files. The harness materializes
declared outputs itself. `host: true` marks an observation made by the host, such
as a trap, rather than the module's own record. The host classifies a Wasm stack
overflow as `Exhausted wasm call-stack`, which the comparison treats as
inconclusive. It classifies other traps and invalid modules as `HostFailure`,
which is always a gate violation.

**`knot-bytes-0` (stub).** This is a pure parser entry: bytes in, bytes out. It
applies when the module has no imports and has these exports:

- `memory`
- `knot_input(len: i32) -> i32`: the address of `len` writable bytes. The host
  copies the input file's bytes there.
- `knot_run(len: i32) -> i32`: the address of the result record.

The record is little-endian: `u32 exit`, `u32 stdout_len`, `u32 stderr_len`,
then the stdout bytes, then the stderr bytes. The observation must equal what
`parse-cli <path>` prints with default budgets, including the trailing newline.
Each run gets a fresh instance.

**`knot-io` (seam).** A module that imports anything is routed to the IO host
ABI. The IO fixture suite on `campaign/io` defines that ABI. It plugs in by adding
`tests/compiler-bootstrap/io-abi.mjs`, which exports
`run(module, runs) -> [observation]` in the shape above. Until that file exists,
the host reports `Unsupported host io-abi-pending`, with source `harness`. A
parser module or compiler module (A2, A3) whose `main` performs IO needs this
seam. It receives the argv and the declared input and output paths. For A3, the
inputs are the whole bundle S. Input paths are relative to the repository root,
except hash-package entries such as `0xc409…/bytes.bend`, which resolve under
`BEND_LIB` (default `~/.bend/lib`). Base resolves under `.toolchain`. The
adapter's hash joins the receipt's `inputs`.

## Limits

- The harness does not prove checker soundness or compiler correctness.
  Agreement is byte identity on the stated corpora.
- The conformance corpus uses the enum profile (`knot-enum-1`). It is fixed
  at 57 cases.
- C1 is built only in the native lane. The Bun lane's memory fault on large
  modules is a known open note in the campaign state.
- A seed build failure is a harness failure (exit 1), not a stage result. A
  clang flake in the native lane is surfaced, not retried.
- The per-stage budgets are 600 seconds for each compile and 600 seconds for
  each host request. Together they can exceed the gate runner's default
  900-second per-gate timeout. Today the gate takes about 30 seconds. Once
  self-compiles become slow, raise `--timeout`, so that a stage's `Exhausted`
  is recorded rather than the runner killing the whole gate.
- A timeout is recorded as `exit: null, outcome: "Exhausted"`. The judge and the
  runner's recheck both accept that as a blocker.
- The receipts change whenever any `.bend` file changes, because the corpus is
  the repository. `npm run gates` reports this as drift. It does not fail on
  drift.
