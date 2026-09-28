# Bootstrap harness: E2E-2 self-parse and E2E-3 fixpoint

This harness measures how far the self-hosting pipeline gets, and records that in a
deterministic receipt. It builds with the pinned seed, invokes compilers and
modules, and compares bytes. It implements no parser, checker or emitter. See the
campaign's [definition of done](../../docs/COMPILER-CAMPAIGN.md), items 1 and 2
and milestones 9 and 10, and the [bootstrap protocol](../../docs/BEND-SUBSET-STAGES.md#bootstrap-protocol-and-first-self-compiling-stage).

Every compiler generation is produced from **one frozen bundle and one argv**
(increment harness-2, [gap analysis](../../docs/compiler-campaign/SELF-HOSTING-PATH.md#harness-2)).
Each generation step runs inside a staged sandbox of copied regular files. It runs
under a recorded generation contract, and the judge requires that contract to be
identical for C1 → A2 and A2 → A3. The contract does not depend on the route: the
Wasm path exists now, and the `knot-image-1` / `knot-vm-1` path plugs in later.

## Commands

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-bootstrap/check.py        # run all stages, write receipts
python3 tests/compiler-bootstrap/check.py --judge RECEIPT            # apply the gate verdict to a receipt
npm run -s gates                                                     # includes the registered `bootstrap` gate
```

The command takes about 20 to 35 seconds on an idle host. Corpus runs use two
workers, and the seed builds use three. It exits 0 only when the gate verdict
holds; a blocked stage alone is not a failure. Build products go to the ignored
`.local/compiler-bootstrap/`, which is cleared first so a stale artifact can
never count. Every wall-clock guard is multiplied by `KNOT_GATE_TIMEOUT_SCALE`
(default 1; the gate runner sets 4). The receipts do not depend on the scale.

## Stages

| Stage | What runs | Passes when |
| --- | --- | --- |
| `e2e2.reference` | The seed builds `src/parse-cli.bend` (native and Bun) from its sandbox. Both run on every corpus file. | Both lanes agree byte for byte on every file. |
| `e2e2.compile` | C1 compiles `src/parse-cli.bend` inside the parser sandbox, with the generation argv. | It prints `Built` with an artifact of that size. |
| `e2e2.self-parse` | The parser module runs on the same corpus through `host.mjs`. | Exit, stdout and stderr are byte-identical to the reference on every file. |
| `e2e3.c1` | The seed builds C1 from the S sandbox (native, twice). C1 compiles the conformance corpus. | Every program and reject matches. |
| `e2e3.a2` | C1 compiles S inside the S sandbox, with the generation argv. | It prints `Built` with an artifact within `output_bytes`. |
| `e2e3.a3` | A2 compiles the same S under `host.mjs`, inside a fresh copy of the sandbox, with the same argv. | It builds A3. Host exhaustion here is `divergent-exhausted`, which never passes. |
| `e2e3.fixpoint` | A2 and A3 are compared. | They are byte-identical. |
| `e2e3.conformance` | A2 and A3 each compile the conformance corpus. | Every call tag and rejection matches, every module is byte-identical to C1's, and every `(exit, stdout, stderr)` equals C1's byte for byte. |

The corpus is every `.bend` file that the gate runner exports: tracked files plus
unignored untracked ones. In a clean checkout that equals `git ls-files '*.bend'`.
Inside the runner's scratch copy, which has no `.git`, the harness walks the
exported tree and excludes `.local`, `.toolchain`, `node_modules` and `build`.
The seed is the oracle, so the reference corpus is a set of observations, not
expectations derived from Knot.

The conformance corpus reuses existing gate fixtures. It has the 25 programs of
`tests/compiler-wasm/cases.json`, with 90 seed-derived call tags run through
`scripts/run-wasm.mjs`, and the 32 fixed rejections of
`tests/compiler-checker/cases.json`. Every generation compiles a case with the
same argv, `<case> <output>`, from the repository root.

Only the seed step invokes `scripts/bend-reference`. A2 and A3 are produced
without any seed or upstream fallback. The compiler entry is one constant,
`COMPILER` in `check.py`. When a unified profile driver replaces
`src/compile-cli.bend`, change it there.

## One bundle, one argv, one contract

**Sandbox (FX-04, FX-05, A2H-07, A2H-08).** Before the seed step, the harness
copies each entry's closure into its own sandbox under `.local/compiler-bootstrap/`:

- `bundle/` for S (`src/compile-cli.bend`);
- `parser-bundle/` for `src/parse-cli.bend`;
- `checker-bundle/` for `src/check-cli.bend`, only when the audit applies.

A sandbox holds copied regular files and nothing else, at these paths:

- repository sources at their own paths, including any foreign host files that a
  definition body imports;
- Base at `.toolchain/bend-2.0.29-574b6d3/bend2/base.bend`;
- every hash package under the relative bundle ROOT, as
  `lib/0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend`.

Base is a pinned leaf. The seed serves Base's own effect files from its toolchain,
and Knot's loader reads only `base.bend`.

The receipt records every file's sha256, its kind and its link count. Base and every
package file must equal their pins in [`manifest.json`](manifest.json). Staging
refuses a mismatch, a symlink, a second hard link, an unpinned package or an
unresolved import, so the run fails before any seed invocation. The seed runs
inside the sandbox with `BEND_LIB` pointing at its `lib/`, so C1 is built from
the staged bytes. C1 is built twice under the same name, and the two binaries
must be identical (FX-11). Each step re-verifies its sandbox afterwards. Only
the declared output may appear. A2 runs in `bundle-a2/`, a fresh copy of the
same files.

**One argv (SCALE-02, SCALE-12, FX-02, FX-03, FX-10, A2H-06).** One builder
produces `[--bundle lib] <entry> generation.wasm <maximum_overrides>`. The
maxima are `65536 4096 4096 4096 1048576` from `src/CONTRACT.json`.
`--bundle lib` appears once `compiler.arguments` advertises
`[--bundle ROOT]`. Before harness-2, C1 → A2 received the maxima while
A2 → A3 received only `[source, output]`, and so ran with parser depth 512 and
a 65,536-byte output cap. Both steps now receive the same list, and the argv
builder refuses the seed-reserved flags `--`, `--bend-help`, `--gpu-build`,
`--threads` and `--gpu`. The native `main()` and the JS `cli()` in the seed's
`comp.ts` consume these before `IO.args`, so a seed-built C1 and a Knot-built A2
would otherwise see different argv.

**Generation contract (FX-09, FX-22, A2H-14, FX-27).** `generation_contract`
holds one object per step (`e2e3.a2`, `e2e3.a3`), and each is built the same
way from its own sandbox:

- the entry, the root, the dependency-first closure, and the sha256 of the
  sandbox's file record;
- the argv, the maxima, and whether module loading is in use;
- the target: route `wasm`, profile, output name and `output_bytes`;
- the runtime:
  - Node, asserted equal to `src/CONTRACT.json` (22.22.3);
  - no Node flags, and `NODE_OPTIONS` removed from every child;
  - V8's default stack size and the inherited native stack limit;
  - the D19 memory maximum, 65,536 pages;
- the build: the seed, the native lane, `clang --version` without its
  `InstalledDir` line, and `CC` removed;
- the host, which must be Darwin, the qualified host whose errno table the IO
  host freezes;
- the seed-reserved flags and the excluded metadata listed in the manifest.

The executor (seed-built C1 or Knot-built A2) is not part of the contract; each
stage records its own `args` and blocker or result. The a3 contract is recorded
even when A2 does not exist yet, because its sandbox and argv are prepared either
way.

**Loader audit (FX-20, FX-21).** Only `check-cli` has `--audit-bundle`.
`compile-cli` does not have it, so the harness cannot run the audit on C1
itself, as the gap analysis's wording has it. Where the contract advertises
`module_loading.audit_arguments`, the seed step also builds `src/check-cli.bend`
from its sandbox. The harness then runs `check-cli --audit-bundle lib
src/compile-cli.bend` inside the S sandbox. The recorded `Module` lines must equal the
staged `.bend` files minus Base, and `BasePin` must equal Base's pin. The
`BaseChecked` and `BaseUnchecked` lines are stored as the D2 trust inventory. An
audit that stops at `Unsupported` or `Exhausted` is recorded as blocked. Without
module loading, the audit is recorded as unavailable.

**Measurements (THIN-02, A2H-12).** Once `e2e3.a2` is reached, `measurements`
records C1's wall time on S (`elapsed_seconds`, which the gate runner normalizes)
and peak RSS from the child's own `wait4` rusage. It records the same for A2's
host run once `e2e3.a3` runs. These values are volatile and outside the
contract. Each reached step's `artifact` records its bytes, `output_bytes`, the
headroom, and the declared Wasm memory limits.

## Today (receipt `receipts/progress.json`)

| Stage | Status | Detail |
| --- | --- | --- |
| `e2e2.reference` | reached | 623/623 files; the native and Bun lanes agree |
| `e2e2.compile` | blocked | `Unsupported lex literal 291:292:10:44` (exit 3, no artifact) |
| `e2e2.self-parse` | not-run | its prerequisite `e2e2.compile` is blocked |
| `e2e3.c1` | reached | 57/57 (25 programs, 90 calls, 32 rejects); C1 builds reproducibly |
| `e2e3.a2` | blocked | `Unsupported lex literal 341:342:12:60` (exit 3, no artifact) |
| `e2e3.a3`, `e2e3.fixpoint`, `e2e3.conformance` | not-run | the prerequisite chain starts at `e2e3.a2` |

Both blockers are byte-identical to the pre-harness-2 receipt. On this tree the
compiler does not load modules, so the argv has no `--bundle` and the audit is
unavailable. S has 15 files: 13 sources, Base and ByteOutput.

**Scratch merge with `campaign/modules`.** The harness ran on a merge of this
branch and `campaign/modules` (`0111f13`), built with `git merge-tree` and
`git archive` without touching any branch, ref or worktree.
The two generated census inventory files conflict; the scratch tree takes
`campaign/modules`' copies, which the harness does not read.
[`evidence/modules-merge.json`](evidence/modules-merge.json) records the
commits, the merge tree, both argvs, the stages, the audit and the receipt's
sha256. The run passed its verdict. Both contracts carry
`--bundle lib src/compile-cli.bend generation.wasm 65536 4096 4096 4096 1048576`,
and S grows to 23 files, including `src/host/path-identity.c` and `.js`. The new
first blocker of both tiers, and of the audit, is `Unsupported lex literal
1947:1948:67:22`. That is the string literal `"type"` in `src/syntax.bend`, the
first module the loader lexes; before, the single-file command stopped at
`src/compile-cli.bend`'s own literal. The audit control records
`probe/side.bend` and `probe/main.bend` with no problems, so the Module-line
comparator runs on a real audit there.

The reference outcome histogram measures how much of the repository Knot's own
parser accepts today: 142 of 623 files parse. Most of the rest stop at
`Unsupported` literal, declaration-form or generic classifications. No
`src/*.bend` file reports `Invalid` or worse. The `Invalid` results are test
fixtures, and they are recorded, not judged.

## Receipts

- `receipts/progress.json` (schema 2) holds, per stage: the status (`reached`,
  `blocked`, `divergent-exhausted` or `not-run`), the corpus size, and the agree
  and disagree counts. A generation stage also holds its `args`. A blocked stage
  holds its raw blocker: source, argv, exit, stdout, stderr, the host flag, and
  for `Exhausted` its `resource` tag. A not-run stage holds its `prerequisite`.
  The receipt also records:
  - `tiers`: each tier's first blocking classification;
  - `bundles`: each staged sandbox, with its dependency-first order and per-file
    sha256, kind and link count;
  - `generation_contract`, `audit` and, once reached, `measurements`;
  - `e2e3.c1.observations`: C1's full `(exit, stdout, stderr)` for every
    conformance case;
  - `own_source`: the reference observations for `src/*.bend`;
  - the seed build hashes (C1 with `repeat_sha256`), the controls and mutants,
    and the verdict.
- `receipts/reference.json` holds one row per corpus file: its source hash, the
  exit status, and the stdout and stderr hashes.

The progress receipt holds no dates or absolute paths, and no timings until
`e2e3.a2` is reached. Two consecutive runs, at timeout scale 1 and 4, produced
byte-identical receipts.

## Gate verdict (`bootstrap`)

`judge()` reads only recorded fields and the fixed `manifest.json`. It derives each
classification from the exit status and the first stderr field, and the two must
agree. It also derives each exhaustion's source:

| Tag | Meaning |
| --- | --- |
| `knot-budget` | The compiler reported exit 4 itself. |
| `host-stack` | The host trapped a stack overflow (`host: true`, `Exhausted wasm call-stack`). |
| `host-memory` | The host failed to allocate memory (`host: true`, `Exhausted wasm memory`). |
| `host-time` | A wall-clock guard fired (`exit: null`). |

The verdict fails when:

- a reached stage lacks exact agreement;
- a blocked stage's blocker is anything but `Unsupported` or `Exhausted`
  (`Invalid`, `HostFailure`, `InternalFailure`, a signal, a stack trace, or a
  mismatched exit and word);
- a blocker's recorded `resource` tag differs from the tag derived from its fields;
- `e2e3.a3` is blocked by a host resource after `e2e3.a2` was reached (it must be
  `divergent-exhausted`), or any stage is `divergent-exhausted`;
- a not-run stage follows a reached prerequisite;
- any `src/*.bend` reference observation reports its own source as `Invalid` or
  worse (D4);
- a sandbox file is not a regular single-link file, escapes the sandbox, or
  differs from its pin; or a package file is unpinned;
- the two generation contracts differ, a contract's argv is not the one
  generation argv or uses a seed-reserved flag, its closure or bundle digest
  differs from the staged sandbox, its host is not Darwin, its Node is not the
  pinned version, or its memory maximum is not D19's;
- a generation stage's `args` differ from its contract's argv;
- a reached artifact exceeds `output_bytes` or declares memory without a maximum
  within the contract's;
- the loader audit contradicts the contract (see above);
- C1's per-case observations are missing, or a generation's observations differ
  from C1's (FX-18);
- the two C1 seed builds differ.

Every run also checks that the judge is not vacuous. It writes scratch copies of
the receipt under `.local/compiler-bootstrap/judge/`, with recorded fields
substituted, and runs `check.py --judge` on every copy. Each mutant must be
rejected **for its named reason**: some violation must contain its expected text.

The unmutated real receipt must pass. It has these mutants:

1. Blocker `Invalid` (exit and word).
2. Word only.
3. Exit only.
4. Host crash (exit 1 with a stack trace).
5. Signal exit.
6. An own-source row turned `Invalid`.
7. A reached stage with a disagreement.
8. A stage that is not run after a reached prerequisite.
9. `parser-argv-bare`: the parser compile's argv loses its maxima.

The generation rules only apply once generations are reached, and this tree does
not have any yet. So the harness also builds a **reached chain**: the real receipt
with a2, a3, fixpoint and conformance reached as a correct fixpoint records them,
with generation observations equal to C1's. The chain and its module-loading
variant must both pass. These mutants of the chain must each be rejected:

1. `argv-mismatch`: A2 → A3 gets the pre-harness-2 bare argv.
2. `argv-unrecorded`: a stage's args differ from its contract.
3. `argv-seed-reserved`: `--threads 1` appears in both argvs.
4. `sandbox-symlink`: a sandbox input is recorded as a symlink.
5. `sandbox-unpinned`: an input differs from its pin.
6. `a3-host-exhausted`: A3 is host-Exhausted after a reached A2.
7. `a3-divergent-exhausted`: A3's status is `divergent-exhausted`.
8. `a3-resource-forged`: a host stack trap is tagged `knot-budget`.
9. `diagnostic-tail`: one character near the end of an A3 diagnostic changes.
10. `artifact-over-budget`: an artifact is one byte over `output_bytes`.
11. `audit-closure-differs`: a staged module is missing from the audit.
12. `audit-missing`: no audit is recorded under module loading.

The runner's `counts()` rechecks the recorded verdict independently.

Fourteen controls exercise paths that have no Knot-built module to run today.
They use test doubles, not Knot evidence:

- A one-byte perturbation must produce exactly one disagreement.
- A hand-assembled replay module must agree on one file and disagree on
  another through `host.mjs`.
- A module that has an import must reach the IO seam and report
  `Unsupported host io-abi-pending`.
- An invalid module must report `HostFailure`, so it can never pass as
  Unsupported.
- A hand-assembled module that recurses without bound must trap as `host-stack`.
- `host.mjs`'s classification of V8's messages: two allocation failures give
  `host-memory`, a stack overflow gives `host-stack`, and an out-of-bounds access
  gives `HostFailure`.
- Staging with a tampered package in `BEND_LIB` must be refused for its pin.
- Damaged copies of the S sandbox must fail re-verification: a symlink, a second
  hard link, a changed package, and an extra file.
- The argv check must find `--threads`.
- A2's result on S must be routed correctly: a host timeout and a host stack trap
  become `divergent-exhausted`, a Knot `Unsupported` stays `blocked`, and exit 0
  proceeds to a reached row. The same pure function builds the live row.
- The audit control: where `--audit-bundle` is advertised, a real audit of a
  two-module entry (`probe/side.bend` importing Base, `probe/main.bend`) must
  return exactly those modules and satisfy the comparator. Otherwise it records
  unavailable.

## Host seam and the parser-as-Wasm ABI stub

`host.mjs REQUEST.json` is the only way the harness runs a Knot-built module. It
takes a request of the form
`{"abi": "auto", "module": path, "runs": [{"argv": [...], "inputs": [paths], "outputs": [paths]}]}`.
It returns
`{"abi", "blocked", "runs": [{"exit", "stdout", "stderr", "files", "host"}]}`,
with bytes in base64. Paths are relative to the host's working directory. For
A2 → A3 that directory is the `bundle-a2/` sandbox, the inputs are its staged
files, and the one output is `generation.wasm`. The host never writes files. The harness materializes
declared outputs itself. `host: true` marks an observation made by the host, such
as a trap, rather than the module's own record. The host classifies a Wasm stack
overflow as `Exhausted wasm call-stack` and a V8 allocation failure as
`Exhausted wasm memory`. The comparison treats both as inconclusive. It
classifies other traps and invalid modules as `HostFailure`, which is always a
gate violation. `host.mjs` exports `trap` and runs its request only when executed
directly.

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
ABI. It plugs in by adding `tests/compiler-bootstrap/io-abi.mjs`, which exports
`run(module, runs) -> [observation]` in the shape above. Until that file exists,
the host reports `Unsupported host io-abi-pending`, with source `harness`. A
parser module or compiler module (A2, A3) whose `main` performs IO needs this
seam. It receives the argv and the declared input and output paths, relative to
the sandbox. The adapter's hash joins the receipt's `inputs`.

## Limits

- The harness does not prove checker soundness or compiler correctness.
  Agreement is byte identity on the stated corpora.
- The conformance corpus uses the enum profile (`knot-enum-1`). It is fixed
  at 57 cases, and it runs from the repository root, not from a sandbox.
- C1 is built only in the native lane. The Bun lane's memory fault on large
  modules is a known open note in the campaign state.
- A seed build failure, a pin mismatch, a non-Darwin host or another Node is a
  harness failure (exit 1), not a stage result. A clang flake in the native lane
  is surfaced, not retried.
- `divergent-exhausted` applies only to host resources. A Knot-side
  `Unsupported`, or a knot-budget `Exhausted`, at `e2e3.a3` after a reached
  `e2e3.a2` remains an allowed blocker. On the VM route, the VM's declared
  heap budget (D19) is a knot budget.
- The host-memory tag rests on V8's error messages. This host allocates a
  4 GiB memory without failing, so no real allocation failure is exercised;
  the classification control feeds the messages to `trap` directly.
- The audit cannot cross-check S until S loads: on the modules merge it stops at
  the same lexer blocker. The audit control exercises the comparator meanwhile.
- The generation contract qualifies only Darwin. Other hosts fail before staging.
- The per-stage budgets are 600 seconds for each compile and 600 seconds for
  each host request, times `KNOT_GATE_TIMEOUT_SCALE`. Together they can exceed the
  gate runner's 900-second per-gate timeout. Once self-compiles become slow, raise
  `--timeout`, so that a stage's `Exhausted` is recorded rather than the runner
  killing the whole gate.
- A timeout is recorded as `exit: null, outcome: "Exhausted"`, tagged `host-time`,
  with its scaled `budget_seconds`. The judge and the runner's recheck both accept
  that as a blocker, except at `e2e3.a3` after a reached `e2e3.a2`, where the
  harness records it as `divergent-exhausted`.
- The receipts change whenever any `.bend` file changes, because the corpus is
  the repository. `npm run gates` reports this as drift. It does not fail on
  drift.
