# Perch manifest increment verification

2026-09-27, branch `campaign/perch-manifest`, compiler base `185b7d5`.
This increment changes style tooling, its tests and campaign documentation.
Compiler source, existing deterministic assertions and `perch-style.json` are
unchanged. No live provider requests were made and no environment file was read.

## Deterministic gates

All commands below were freshly executed with `BEND_NO_TELEMETRY=1`. Every listed
gate exited 0. The offline manifest preflight separately exits 3 for the
[recorded structural blockers](perch-baseline.md).

| Gate | Exact observed counts |
| --- | --- |
| `python3 tests/subsets/check_frontend.py` | 14 reference fixtures; 2 parser lanes; 24 boundary observations; 4 laws; 4 semantic mutants killed |
| `python3 tests/compiler-checker/check.py` | 49 reference fixtures; 98 checked observations; 10 depth observations; 16 catalog-bound observations; 7 semantic mutants killed |
| `python3 tests/compiler-structural/check.py` | 16 seed fixtures; 4 boundary pairs; 7 semantic mutants killed |
| `python3 tests/compiler-fields/check.py` | 40 seed fixtures; 240 native/Bun phase observations; 36 budget probes; 6 host probes; 12 level/inspection observations; 9 semantic mutants killed |
| `python3 tests/compiler-wasm/check.py` | 25 source programs; 90 independent reference calls across each of 2 lanes; 64 rejection pairs; 44 boundary observations; 7 semantic mutants killed |
| `bun tests/compiler-wasm/trust.ts` | 3 complete entries; closures of 15 / 13 / 18 files; 0 holes; 42 foreign declarations and 2 inventoried Base unsafe declarations per entry |
| `bun tests/compiler-fields/trust.ts` | 4 complete entries; closures of 22 / 12 / 13 / 15 files; 0 holes; 42 foreign declarations and 2 inventoried Base unsafe declarations per entry |
| `bun tests/compiler-structural/trust.ts` | 2 complete entries; closures of 20 / 8 files; 0 holes; 42 foreign declarations and 2 inventoried Base unsafe declarations per entry |
| `python3 research/owned-store/check.py` | 3,532 cases; 15 literal witnesses; native and Bun agreement; 6 semantic mutants killed |
| `python3 research/flat-store/check.py` | 13,621 observations / 3,534 Wasm instances / 2 installed boundary states / 7 lifecycle checks per seed-emission lane; 9 semantic mutants killed; 1,050-byte module identical across native/Bun emission |
| `npm run -s lint:verify` | 127 tests passed, 0 failed; all 8 law-rule wiring checks passed; provider responses were local fixtures |

The complete pinned-seed proof commands were also rerun:

```sh
export BEND_NO_TELEMETRY=1
bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts src/PROOF.bend
bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts src/check-PROOF.bend
bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts src/runtime-PROOF.bend
bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts src/catalog-PROOF.bend
bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts src/fields-PROOF.bend
```

All **5/5** printed `All terms check.` The final chain contains the existing
34 laws; this tooling increment adds no Bend laws or compiler capability.
Seed/evaluator/Wasm differential assertions remain exactly those of the existing
compiler gates. Manifest behavior is fixed by literal review and independent
tooling assertions in the [manifest contract](../../tests/perch-style/manifest-contract.md).

The first full lint attempt hit a host failure opening the parser cache lock
outside the sandbox: 111 tests passed and 11 failed during installed CLI loading.
The installed parser manifest, seven grammar libraries and cached bundle were
copied into ignored `.local/perch-manifest/parser-cache`. No download or package
change was needed. The complete unchanged suite then passed with:

```sh
export BEND_NO_TELEMETRY=1
export TREE_SITTER_LANGUAGE_PACK_CACHE_DIR="$PWD/.local/perch-manifest/parser-cache"
npm run -s lint:verify
```

## New fixtures and mutations

The 127-test total includes **20 manifest/compatibility tests and 4 mutation
tests**. Fixtures cover ordered groups, overlapping source, collaborators,
per-group tasks, absent/overlong task context, metadata isolation, malformed
schemas/options, workspace/symlink boundaries, parser failures, total unit caps,
truncation, unresolved imports, byte bounds, source/task/manifest freshness,
model drift, failed-group stopping, partial evidence, output collisions, reuse
and incremental cache invalidation. Compiler-manifest coverage and local import
closure are checked against the actual parsed source tree.

The three small Bend source fixtures (`z.bend`, `a.bend`, `m.bend`) are embedded
in [the fixture module](../../tests/perch-style/manifest-fixture.mjs). Independent
pinned-seed checks of all three printed `All terms check.` Expected manifest
ordering and outcomes were written before implementation. Legacy explicit-unit,
whole-file and `--all` request bytes, preflight JSON bytes and stable live report
bytes were frozen from unmodified `185b7d5` in
[manifest-legacy.json](../../tests/perch-style/manifest-legacy.json). Only timestamps
and measured durations are removed from live report comparisons.

| Semantic mutant | Unchanged rejecting observation |
| --- | --- |
| `lexical-order` | Composition must read `z.bend`, `m.bend`, then collaborator `a.bend`; explicit-target composition retains lexical order |
| `any-group-qualifies` | One failed composition keeps overall qualification false despite another passing group and passing declarations |
| `filtered-is-complete` | Passing `--group=primitive` cannot set whole-manifest qualification |
| `ignore-final-freshness` | A later group modifying an earlier group's source makes the aggregate stale and unqualified |

All **4/4** mutants preserve JavaScript value shapes, pass `node --check`, load
the real unchanged dependencies, and fail an `ERR_ASSERTION` in the fixed
behavioral test. JavaScript has no separate static type gate here; syntax/import
errors and harness failures are explicitly excluded as semantic kills.

## Evidence and ownership boundary

The new [preflight receipt](perch-preflight.json.gz) and
[baseline](perch-baseline.md) retain this increment's compiler source, task,
manifest and rubric identities. Existing regenerated compiler/store receipts
were restored rather than committed: timestamps, worktree paths, measurements
and gzip headers changed without a tooling-caused compiler result change.
Some old receipts also predate already-committed changes to `src/driver.bend`
and `src/check-LAWS.bend`, changing their recorded source/build hashes on this
rerun. Both sources are byte-identical to this branch's base; refreshing those
unrelated receipts belongs to the coordinator. Fresh gate logs and copies of
regenerated receipts remain under ignored `.local/perch-manifest/`.

No push, merge, rebase, other-worktree edit, provider call or rubric adjustment
is part of this increment. Live semantic review and all five style-axis ratings
remain the coordinator's next qualification work after the structural blockers.

The execution sandbox denies writes to the shared Git metadata at
`/Users/ericfode/src/knot/.git/worktrees/campaign-perch-manifest/index.lock`.
The attempted prescribed receipt checkout failed with `Operation not permitted`;
the 15 generated receipts were instead restored byte-for-byte from `git show
HEAD:<path>`. No shared index or branch ref was changed.

The verified increment is committed in the ignored task-local Git repository
`.local/perch-manifest/checkpoint.git` and exported as
`.local/perch-manifest/perch-manifest.bundle`, with `185b7d5` as its parent.
The coordinator must import that bundle from an environment allowed to write
the shared Git metadata. The original worktree branch remains at its base,
with this increment's files as working-tree changes; those files belong to this
executor and match the bundled commit.
