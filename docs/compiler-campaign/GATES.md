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

On macOS the runner resolves the toolchain clang once (`xcrun --find clang`) and
passes it to every gate as `CC`, unless the caller set `CC`. The seed probes
`$CC` before `clang`. The `/usr/bin/clang` shim intermittently printed nothing
under parallel load, which the seed reported as "found no clang". The resolved
binary is the same compiler the shim forwards to. Some gate programs rebuild
their own environment for seed and mutant builds, keeping `PATH` but dropping
`CC` and `SDKROOT`, so the runner also puts a `clang` wrapper first on `PATH`.
The wrapper runs the resolved compiler and supplies the SDK when it is missing,
which keeps those paths off the shim. `test_runner` pins it with a trimmed
environment.

The same message also appears under heavy host load with the real compiler on
PATH: the seed's `spawnSync` probe returns nothing. It is a host fault, not an
assertion, so the runner reruns a gate once when the gate failed and its output
contains `bend needs clang`. The result records the first attempt under
`retried` (its logs keep the `.retry` suffix on the second attempt), and the
normalized summary leaves `retried` out, so a retried pass normalizes like a
clean one. A gate that fails twice stays failed. Other failures are never retried.

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
The `io-abi-2` increment appends gate `io-abi-2` for the `knot-io-2` host
delta ([IO-ABI.md](IO-ABI.md#knot-io-2-delta)). Its counts record the foreign
reference, seed-witness, read, parity and mutant totals; it writes
`tests/compiler-io-abi-2/receipts/{host,reference}.json`.

The joint increment adds `selfhost`, the [self-hosting joint suite](../../tests/compiler-selfhost/README.md).

- It first reproduces 65 frozen cases on the seed's interpreter and native lanes.
- It then runs Knot's `check-cli` and `eval-cli` on each case.
- A case is blocked while a reviewed need is unavailable. A blocked case never
  counts as passing. It still fails the gate on a fault: crashing, timing out,
  a host or internal failure, accepting a seed-rejected twin, or a positive
  evaluating other than the seed. A seed-valid case reported Invalid must be
  one of the reviewed D4 gaps in `check.py`.
- The gate writes only `tests/compiler-selfhost/receipts/selfhost.json`.
- An increment that lands a need flips it in `expectations.json`, and the gate
  then holds that increment to its cases.

The vm-spec increment adds gate `vm-spec` (`python3 vm/check-spec.py`), which
freezes the `knot-image-1`/`knot-vm-1` contract of `vm/SPEC.md` before any VM
exists. It builds the pinned literals and closures heads' `eval-cli` and
`check-cli` from `vm/oracles/` with the seed's native lane, re-executes the seed
and eval-cli on 111 golden sources, and requires the frozen observations byte for
byte. It checks each committed image against its hand-written plan, the
reference codec and an independent reading of Knot's checked core display, save
three Book goldens whose lane's head (the literals one) answers Unsupported and
whose review declares the line. It also checks the frozen VM expectation table; 211 refused image controls (124 byte-level,
78 plan-level, and nine on either side of the resource limits that are `Exhausted` kind 2); 27
expectation, seven invocation, two seed-display, three display-lane and two bench
controls; two excused eval-bound controls; eight admitted plan controls (two of them names in every length of UTF-8),
one admitted limit control, seven admitted code-list controls and 138 run controls with their frozen
fuel, calls and outcomes (among them D23's requests: built by the Action's second application,
performed only by the Program's Top loop, dropped without effect and refused as
`Unsupported vm effect` wherever a read meets one, except a Case, whose Default takes it (D24; nest's lowering of a source
catch-all emits none, so its five compiled twins are refused, and two plans that test the slot again take the request as the native lane does), with the
bytes and host calls a Book makes, which are none; D20 on a Halt's message, the inspection points of section 6 and the UTF-8 of a scalar; and 27 atomic controls
(section 6.3): each stop reports the meters, output and effects that the run held before the step, and a stop that is not a fuel stop is reached with exactly
the fuel the run has spent); nine describe-domain controls; 13 argument controls;
the lowering of two hand-written displays; 15 seed witnesses (sources whose two seed lanes, and for
three the literals head, it re-executes and compares with frozen bytes and a literal review, with three
frozen refusals of that comparison); 137 codec, 4 source, 120 evaluator and twenty-three
rule mutants of `check-spec.py` itself (ten of them delete one clause of the canonicality clauses that the gate holds
against re-encoding on 5,797 images); the accounting of all 178 omissions of a refusal of the reference codec or of a clause of its test, each killed,
held by a raise or unreached; and the bench freeze: sources, guards, outputs and the seed-native
measurements pinned by digest in `vm/bench/workloads.json`. It asserts that its own peak
memory stays under 4 GiB (it holds about 430 MB): no mutant sizes an allocation from a raw word of an image. It writes only
`vm/receipts/spec.json`. `vm/SPEC.md` section 12 lists each control.

The vm-core increment adds gate `vm-core` (`python3 vm/check-core.py`). It
checks `vm/vm.wat`, the WAT `knot-vm-1`:
- The pinned `wat2wasm` reassembles `vm/vm.wasm` byte for byte. The module's
  imports, exports and 65,536-page memory are as the spec requires, and its call
  graph has no cycle.
- All 111 golden images run through `scripts/run-wasm-io.mjs` with their
  `vm-expected.json` outputs. So do its 44 frozen Book invocations. The test
  build confirms each exhaustion cause and audits the state after every
  transition. Every run that ends cleanly, in every row below too, ends in
  control `Halt` (mode 3).
- Atomic stops (SPEC section 6.3, D25): the harness plays every run that ends in a
  stop (a `HostFailure`, an `Unsupported` or an `Exhausted` of any kind) again to its
  last step, and that step may change no register, frame word or cell but the debit
  of an Enter. Its `witness` rows pin by hand the frames and `act` a stop leaves.
  Requests are values (D22 to D24): an Action's second application builds one, and
  only Top's loop performs it.
- `vm/core/fixtures.json` fixes literal-review runs, state-dump rows and
  lowered limits, including the 250,000-deep non-tail recursion, where a
  Nat Case makes its predecessor against its Scope push (vm-spec D17), a
  describe that needs exactly 132 bytes of frame region (12 bytes an open
  Object) and stops one byte short, an `append` block that ends exactly at a
  lowered heap and one 16 bytes past it, and the cell of an Action. Rows added
  for the survivors of the mutant study (round 7) pin the room of a Case's
  Scope, of a Call frame, of a tail loop below a Call frame and of `U32.show`'s
  digits at their exact fit and one byte short, a Closure that binds a slot after
  its captures and its live argument, a describe result whose second field is an
  arrow, an erased-arrow parameter, a name that is no function's and the class
  of the usage refusals.
- 24 seeded rows (`vm/core/seeded.json`) whose expected results the pinned seed's
  native lane fixed before any VM ran them: U32 and Char key Cases of 3 and 5
  keys queried below, at, between and above their keys (with keys and computed
  scrutinees at 2^30, 2^31 and 2^32-1), constructors of 3, 5 and 9 fields flat and
  nested in a wider one, tag Cases whose Default is reached by an immediate and by
  an Object, and, by literal review, the edges of SPEC section 6.1's inspection.
  The gate runs the seed again and requires its frozen bytes; the reference
  evaluation and the VM, on the real host and the test build, must give the
  same run.
- A differential lane (`vm/lane.py`; seed and sizes in `vm/core/lane.json`): 2,768
  rows (2,000 generated programs, every second one laundered through `none`
  types; 200 random key Cases; 76 prim sweeps; the print, Halt, digit and Nat
  writers' boundaries; two rows at the display bound; and 294 rows that put every
  kind of word at every place section 6 inspects one, which found a String cell
  and a Program's final word trapping on a scalar of about 2^25 or more instead of
  halting `ill-typed`, now fixed in `vm.wat`). Each runs through the test
  build and the production module and through `vm/evaluate.py`, which must
  agree on stdout, exit, stderr, outcome, cause and calls; an 84-row sample also
  runs through the seed's native lane with its bytes frozen. Every admitted
  golden, invocation, control and fuzz image (751) is compared with the reference
  evaluation too. `python3 vm/check-core.py --freeze` rewrites the two frozen
  files from the seed.
- Three Books on Chr's operand, one with a Big predecessor and one with a Closure
  that binds a slot after its capture and its live argument (`reference`
  rows) run as literal review froze them. vm-spec's reference evaluation (`vm/evaluate.py`) must give the same
  run and call count.
- Ten images (nine Books and a Program) whose bump pointer ends near or
  exactly at 4 GiB. Each row's bump pointer and outcome are first derived from
  SPEC section 5's cell sizes over its plan, independently of any VM. The first
  six pins were measured from the pre-fix VM (`c9869ef`), and the derivation
  agrees with them. Review round 4's four rows, three whose heap ends exactly
  at 4 GiB and a control 16 bytes above, took their fill counts from the
  derivation alone. A cell may end exactly at 4 GiB, where the pre-fix VM
  trapped.
- Three memory-end rows: Books whose last cell ends exactly at 48 MiB, where
  boot leaves the memory (CORE.md choice 15), so that the memory ends where
  the cell does. One is an Object whose four fields fill its cell, which a Case
  then binds; one is the Action of an `IO.print` that is never applied; the third
  is the full Activation of a Closure over four captures.
  A read or a write past a cell's end lands in padding or in free heap
  everywhere else, and faults only here. Section 5's model derives each fill
  count, bump pointer and line, and the reference evaluation at a fill of 3
  gives the line and the calls. The test build pins `bump` and `grows` (boot's
  grow, and one for the text that starts at the memory's end).
- The scope tables (CORE.md choice 16; `vm/scope.py`; `scope` in `fixtures.json`).
  The validator holds each slot's type and use mark at the sum of the depths of
  the Closures around it, in tables of W + 4200 indices at first, which the
  reviewer's images outgrew: valid images were refused or trapped, and a
  malformed one was accepted and run. Twenty-four rows, each frozen with its
  words, `need` (the indices validation holds, derived from the plan alone),
  SHA-256, the reference codec's verdict and the reference evaluation's run,
  before the VM changed: the reviewer's four saved images (two valid, two
  refused), rows one short of, at and one past the tables' size and after one,
  two and three doublings (K's fields typed, so a slot read after a doubling
  shows its type was carried over), a Closure whose capture sits where the
  tables must grow, two units of 65,535 slots, and a unit deeper than its
  `slots` with a defect after that depth (the reference codec reports the defect,
  not the slots: no early refusal). One row is valid but needs more scratch than
  4 GiB holds (`scope.scratch`): it stops `Exhausted` kind 2 (heap), not a trap.
  Then a seeded corpus of 300 such images, most with one small change, which the
  VM must judge as the reference codec does, in the test build and in `vm.wasm`.
  The rows bound the test build's `memory.grow` count, which tables that grow
  one index at a time would break.
- Three growth rows on one Book whose every entry allocates a 16-byte Activation,
  each stop derived from SPEC sections 5 and 7 in closed form: a heap lowered to
  256 MiB (`Exhausted` kind 2 in at most 24 `memory.grow` calls of the test
  build), the full 4 GiB through the real host within its 120 s guard, and a
  host that refuses growth beyond 4,700 pages (`HostFailure`, never
  `Exhausted`, at the cap). Growing memory one page at a time fails the first by
  its count and the second by its wall time (22 minutes on V8).
- A 200,000-deep nested expression runs on a 64 KiB host stack.
- The 211 refusal controls, a seeded fuzz corpus of 4,440 mutated goldens and
  9,810 goldens that each set one limit word (a record count, an arity or a
  `slots`) around its limit are refused with the reference codec's first
  defect, and none traps. A crash of the reference codec on any of those
  images fails the gate. Nine of the controls sit on either side of SPEC
  section 4's resource limits: past a limit the VM stops `Exhausted` kind 2
  with the limit as its cause, and the gate compares that with the reference's
  `Exhausted 2 <limit>`, in the VM's own outcome registers too.
- The 154 controls vm-spec admits load:
  - 16 (eight plan controls, `arity-at-limit` and seven code lists) run as literal
    review froze them, and as the reference evaluation runs them;
  - all 138 run controls, as many as SPEC section 12 states, run to the outcome,
    call count and host calls (`effects`) that `check-spec.py` freezes: the eleven
    fuel controls at their frozen fuel, the others also on exactly that much fuel.
    Eighteen of them are inspection points (SPEC section 6 and section 9's
    extents), and the rest include D22 to D24's requests and the atomic controls
    of section 6.3.
- `check-spec.py`'s 13 argument controls run through the real host to their
  frozen verdicts, or, where the words are admitted, as the reference
  evaluation runs them.
- One hundred and thirty-eight WAT mutants are each killed by a wrong observation. One restores the
  pre-fix trap at 4 GiB and is killed by that trap, only while every other
  ceiling row stays right; two restore the immediate tests that trapped
  (group `traps`), and four copy or bind past a cell's end (group
  `memory-end`), each killed by a trap on its memory-end row while every other
  row there stays right; one steps the key search to the middle, not past it, and is
  killed by the hang it makes (a row that outlives its deadline, in group
  `hang`). Twenty-four came with review round 6: the key search, tag
  Defaults and range, describe's separators, closing brace, visit and frame
  bounds, `append` at a lowered heap, an Action's cell, and a scalar read of an
  Action. Four read less than an inspection extent (`append`'s
  `b`, `is_empty` past its head, `eq` past a difference or an end, the moved
  word of a conversion); each survives every golden and dies by its own
  inspection controls. Fifteen move SPEC section 4's limits: checked in the
  wrong order, absent, reported as a malformed image, exclusive, given another
  limit's cause, or fitted to the wrong number of words. Each survives every
  golden and run control and dies by a limit control, except the two fits,
  which only the limit-word images kill. Two change the growth policy
  (CORE.md choice 15) and keep every outcome: memory grown one page at a time,
  killed by the test build's `memory.grow` count (a timeout never kills, SPEC
  section 11), and a refused step that traps, killed by the run whose host caps
  memory. Seven guard the scope tables: they never grow (W + 4200 restored),
  a write holds one index short, a doubling drops the types, carries a
  quarter of them, or drops the use marks, a table grows to the index that
  passed it and not to twice its size (killed by the memory.grow count), and a
  unit is refused as soon as its depth passes its `slots`, which names another
  first defect than the reference codec's. Fifty-one came with round 7: the
  eager rule, a dropped request that is performed, and a Case with a Default
  that refuses a request (D22 to D24); each half-done step of SPEC section
  6.3's atomic stops (a Gather popped before its node can refuse, `act`
  dropped before a check, an Activation made after a frame is popped); the
  describe domain (an arrow or a `none` field inside it, an Unsupported that
  is a HostFailure) and a visit charged before its word is inspected; and 19
  named for the survivors of the study that new rows now kill (a Closure whose
  depth leaves out its live argument, the room of a frame off by one byte, a
  describe walk that skips a field, a control left in Enter, a capture loop
  that runs one time too many).
- `python3 vm/check-core.py --study [--heavy]` runs the 993 systematic
  single-token mutants of `vm/study.py` against these rows instead, and writes
  `vm/receipts/study.json`; `vm/CORE.md` gives its result and why each survivor
  survives. The gate prints the time of each stage on stderr.

It writes only `vm/receipts/core.json`. [vm/CORE.md](../../vm/CORE.md) records
its conventions and open spec points.

The prechecks suite's own verification (`npm run -s prechecks:verify`: its unit tests against synthetic clean and broken repositories, its semantic mutants and the Perch wiring test for its seven advisory rules, receipt `tests/prechecks/receipts/prechecks.json`) is deliberately not a registered gate: it takes 150 to 390 seconds, and every increment's full gate run would pay for it while only a change to `scripts/prechecks/` or `tests/prechecks/` can affect it. Run it whenever either changes; the coordinator runs it before merging such a change. The suite itself is not a gate either: `npm run -s prechecks` reports conditions for the
implementer and the reviewers and is not part of `npm run gates`. Its historical controls (accepted tips as clean controls, confirmed
regressions as broken ones) run with `python3 scripts/prechecks/replay.py` in a checkout that has the campaign history, because the
gate's export has none.

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
1,800 seconds; 900 let the eight nest gates, each rebuilding its lanes, exhaust
under campaign load); timeout kills that process group and records `exhausted`.

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
