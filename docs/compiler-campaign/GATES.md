# Compiler gate runner

Contract fixed before implementation (2026-09-27): export the invoking working
tree, run the existing assertions in scratch, classify normalized receipt drift,
and write tracked receipts only through an explicit refresh. Literal controls
are in `scripts/gates/fixtures/expectations.json`.

The runner owns only `scripts/gates/`, the npm gate commands, and this document.
It does not change compiler semantics, existing assertions, or package sources.

## Commands

```sh
npm run gates                         # run and compare; no tracked writes
npm run gates:check                   # same exit contract, suitable for CI
npm run gates:refresh                 # rerun, then explicitly refresh receipts
npm run gates:verify                  # offline wrapper controls and mutants
npm run gates -- --jobs 2 --keep-scratch
```

Harness wall-clock guards inside the gate scripts (the seed-build and CLI
`run()` timeouts) scale with `KNOT_GATE_TIMEOUT_SCALE`. The runner sets it to 4
unless the caller sets it. These guards only catch hangs; no passing receipt
records one firing. Under the campaign's parallel load (load average about 30
to 50 on 18 cores) the unscaled 30-second and 45-second guards made the frontend
and structural gates fail spuriously.

Both check commands exit 0 only when all registered gates finish successfully
and their required outputs are present and readable. The runner's self-test
requires the existing gates by name (including `perch-context` and `bootstrap`)
and unique names, so a new increment appends its gate and required name;
this branch retains the seventeen main gates and appends `nest` and
`nest-review`, for nineteen total. The latter checks the frozen reviewer repros,
enum whitelist, semantic repair mutants and fixed-seed 3,000-program comparison.
`bootstrap` runs the [E2E-2/E2E-3 harness](../../tests/compiler-bootstrap/README.md); `census` runs `tools/census/census.mjs
--check`, so a new source file, import or feature class needs a reviewed
`tools/census/approved.json` entry. Gate failures, missing executables,
timeouts, blocked dependencies, and malformed/missing completion records exit 1.
The Perch context increment adds gate 15, `perch-context`: 33 literal context
controls, eight semantic mutants, one complete seed signature check, and two
byte-identical offline compiler-manifest preflights. The literal command uses
the runner's frozen `BEND_LIB` by default. Package identities and request hashes
are independent of that store's location. It writes only its own
`tests/perch-context/receipts/context.json` in scratch. It makes no provider
requests and retains the pinned rubric and composition-byte cap.

Semantic receipt drift is reported but does **not** fail the check. It does not
make the current execution fail an unchanged assertion.

Each invocation writes one JSON summary to stdout and to an ignored, unique
`.local/gates/run-*/summary.json`. Use `npm run -s gates` for pure JSON stdout;
progress and the summary filename go to stderr. `run` contains measured total
and per-gate wall times, exit codes, and raw log filenames. `normalized` contains
the deterministic results, pass counts by category, exported-source and cached
dependency manifest hashes, and every receipt comparison. Categories overlap;
they are not added into a misleading single assertion count.

Full stdout/stderr logs, `snapshot.json`, `dependencies.json`, normalized
receipts, and unified semantic diffs remain alongside the summary. Scratch
sources, build products, and dependency caches are removed by default;
`--keep-scratch` retains them. `--timeout` sets a per-gate wall limit (default
900 seconds); timeout kills that process group and records `exhausted`.

To compare two runs of unchanged inputs, compare their entire `normalized`
objects, or byte-compare their `normalized/` receipt trees. Real timings and run
directories in `run` are deliberately outside that equivalence.

## Export and scheduling

The runner uses `git ls-files --cached --others --exclude-standard -z`. It
exports current working-copy bytes, including unstaged edits and non-ignored
new files; tracked deletions remain absent. `.env` and `.env.*` (including
`.env.example`), Git metadata, build directories, and ignored files are excluded
without reading their contents. The original tree is checked again after
copying. Internal source symlinks are relocated into scratch; external source
links and symlinked source parents are rejected.

Only `.toolchain` and `node_modules` are shared symlinks, as required by the
campaign. Already installed hash packages from `BEND_LIB` (default `~/.bend/lib`)
and the tree-sitter language-pack cache are copied and hashed. Tree-sitter's
cache must be private because even cached manifest reads acquire a writable
lock. No dependency installation runs. The child environment is an allowlist
for host-tool discovery, with `BEND_NO_TELEMETRY=1`, private temporary/cache
directories, UTC/C locale, npm offline mode, and disabled Bend hub/version and
tree-sitter manifest URLs. It does not inherit credentials or Node preload
options. Existing Perch tests use their unchanged mock provider.

Frontend, checker, structural, fields, Wasm, owned-store, and lint have separate
write sets and may overlap (four worker slots by default). Each of the three
trust inventories waits for its corresponding successful gate's generated JS.
Flat-store waits for owned-store's regenerated input corpus. A failed producer
blocks its consumer explicitly; independent gates still finish. Expected
receipts are removed **in scratch** before execution, so an old passing receipt
cannot stand in for missing fresh evidence. The five compiler checks, three
trust inventories, two store checks, and `npm run -s lint:verify` are invoked
without editing their scripts or assertions.

## Receipt identity and refresh

The comparison baseline is the invoking worktree's current **tracked receipt
bytes**, including an intentional uncommitted receipt edit. It is not another
branch or a hardcoded main checkout. New generated files compare against an
absent baseline. Retained Wasm/WAT and compressed observation files count as
receipt artifacts too; historical receipts not regenerated by the registered gates
are not included.

| Classification | Meaning |
| --- | --- |
| `identical` | Original and regenerated bytes match exactly. |
| `volatile-only` | Bytes differ but their normalized forms match. |
| `semantic` | A normalized observation, source/artifact hash, count, status, order, field, or artifact changed, appeared, or disappeared. |

Normalization sorts JSON object keys but preserves arrays. Root ISO `date`/`at`
metadata becomes `<normalized-date>`; measured `elapsed_seconds` becomes zero.
Budget limits remain meaningful. Known checkout, seed, and cached-package path
prefixes become `$ROOT`, `.toolchain`, and `$BEND_LIB`, including seed foreign
paths containing `/./`. Unrelated paths and filename changes remain meaningful.
Gzip payload bytes are preserved, with an empty filename, zero MTIME, and OS=255
in a deterministic header. These transformations are idempotent.

Flat-store records the digest of owned-store's **compressed** input. That one
digest edge is translated to the canonical gzip digest only if the recorded
hash matches the actual companion bytes. A stale/mismatched hash is preserved
and reported as semantic. No source hash, build hash, observation hash, exit
classification, array order, or count is blanket-ignored.

`gates:refresh` runs the same checks, then verifies that all exported worktree
files still match the snapshot and the normalized files still match their
reported hashes. It replaces only existing tracked receipts, one file at a
time via atomic rename. Failure or an intervening edit refuses the refresh.
New receipt paths need an explicit manifest/ownership review before refresh.
There is no multi-file crash transaction. Review and explicitly stage the
receipt diff for a separate refresh commit. Check commands never refresh.

## Verification on campaign base `185b7d5`

The first successful full scratch run took **37.522104 seconds**, with four
workers, Bun 1.3.14, Node 22.22.3 and the pinned Bend 2.0.29 seed on this host.
This is measured total wall time, including export and normalization. It is
not a cross-machine performance promise.

Two consecutive `gates` / `gates:check` runs took **38.948396** and
**36.111867 seconds**. Their entire `normalized` summary objects and all 78
normalized artifact files were identical. The summary SHA-256 was
`3254210320725945635be9836e370415171a4ce2c37464216a9db427d6f64e11`.
Comparing the exported manifest with the invoking worktree after each run found
no changed, added, or removed source files. The local raw summaries are
`.local/gates/run-9bpr0x75/summary.json` and
`.local/gates/run-mg0c405c/summary.json`; these ignored execution logs are not
required inputs. This paragraph was added after that comparison.

After adding the malformed-receipt evidence control, successful runs of the
final code took **52.277751 seconds** (four workers) and **68.794704 seconds**
(two workers). Both preserved the complete exported worktree manifest and
produced identical normalized summaries and all 78 normalized artifacts. Their
normalized summary SHA-256 is
`005cd718ab44c2517bc1dbeecfb3a2837c449ce5692b7576e2497a90b73322be`;
receipts are in `.local/gates/run-_m11kklh/` and
`.local/gates/run-vgxf0990/`. All 78 normalized artifacts are also idempotent
under a second normalization.

An intervening four-worker run, `.local/gates/run-2_63yvq0/`, failed when the
seed's clang discovery returned `found no clang`. It exited 1 and explicitly
blocked Wasm trust; the other gates completed. A subsequent direct clang
version probe succeeded, and the two-worker run above passed. The underlying
host failure is not diagnosed. The runner retains failures and does not retry
or relabel them as compiler rejection. No existing assertion was changed.

| Gate | Exact passed coverage |
| --- | --- |
| Frontend | 14 reference fixtures; 28 parser-lane observations; 24 boundaries; 4 mutants |
| Checker | 49 reference fixtures; 98 checked observations; 10 depth probes; 16 catalog-bound observations; 7 mutants |
| Structural | 16 seed fixtures; 64 catalog/compiler lane observations; 4 boundary pairs; 7 mutants |
| Fields | 40 seed fixtures; 240 phase observations; 36 budget probes; 6 host probes; 12 level/inspection observations; 9 mutants |
| Wasm | 25 programs; 90 independent reference calls in 2 execution lanes; 64 rejection pairs; 44 boundaries; 7 mutants |
| Wasm trust | 3 entries; 0 proof holes |
| Fields trust | 4 entries; 0 proof holes |
| Structural trust | 2 entries; 0 proof holes |
| Owned-store | 3,532 cases in 2 lanes; 15 literal witnesses; 6 mutants |
| Flat-store | 13,621 observations, 3,534 instances, 2 installed boundary states and 7 lifecycle checks **per lane**; 2 lanes; 9 mutants |
| Lint verification | 103 tests; 8 law-rule wiring controls; no provider calls |

All seven existing proof entry commands passed inside their gates (the five
compiler proof entries plus both store `PROOF.bend` entries). No Bend code or
law was added. Style preflight has **0 changed Bend targets**, so there is no
new declaration or composition review; live review remains the coordinator's
step.

Of **78** regenerated artifacts, **63** were identical, **7** volatile-only,
and **8** semantic. The eight are the five compiler check receipts and all
three compiler trust inventories. Their differences are the old `driver.bend`
and `check-LAWS.bend` hashes and derived generated-code hashes. No fixture
observation or count changed. This observes more stale inventories than the
initial estimate of six. No receipt refresh belongs to this implementation
commit; the coordinator can run `gates:refresh` after integration.

The wrapper's **18 passing tests** include 12 JSON comparison cases, gzip headers
and payloads, verified compressed-hash edges, path canonicalization, scratch
isolation, working-copy edits/deletions, secret-file exclusion, DAG ordering,
failure/timeout outcomes, missing fresh evidence, and guarded refresh. Six
executable Python semantic mutants are killed: erase source hashes, sort
observation arrays, erase observations, erase budgets, swallow a failing exit,
and drop dependency edges. Each mutant compiles and executes through the same
host API; the failure is the wrong contract observation. There are no new Bend
fixtures or seed/evaluator/Wasm capabilities in this wrapper increment.

## Limits and next increment

This isolates source and outputs; it is not a container or an OS network
sandbox. Host tool binaries, the required seed and `node_modules` symlinks are
shared and must remain stable during a run. Missing installed dependencies fail
locally; the runner does not repair or install them. The existing flat-store
gate still names `/opt/homebrew/bin/wasm2wat`; portability of that existing gate
is outside this change. Native executable hashes are meaningful within the
recorded host/toolchain, not promised equal across hosts.

Extend the gate/output inventory and dependency edges when a later increment
adds a gate or new receipt family. Extend count extraction with that gate's
independent completion record. Keep the compiler's Invalid, Unsupported,
Exhausted, host and internal observations intact inside the retained evidence;
wrapper process failures are a separate summary status, never a judgment of
the source language.
