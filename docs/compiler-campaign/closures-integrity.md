# Closures: scope and receipt integrity follow-up

This round starts at `35b979bf` on `campaign/closures`. The comparison base
reported by the unchanged precheck tool is `fa31fec0`; its main/tool reference
is `b92b1359`. Earlier implementation, freezes and observations remain in Git.
Only this worktree is written. No branch merge, rebase, push, `.env` access,
provider call or live Perch review is part of this executor round.

## Scope repair

The seven pre-existing compiler gate scripts and `scripts/gates/test_runner.py`
are restored byte for byte to the comparison base. `scripts/gates/run.py`
retains only the additive closure gate row and its count extraction. The prior
port of shared clang discovery, retry and timeout behavior is removed from
this branch; the coordinator owns the current shared runner at integration.
Host tool discovery for this executor can use an ignored local PATH wrapper,
and the runner's existing `--timeout` argument. Neither changes source budgets
or frozen assertions.

`census:approve` reports no new permissions. Nine previously approved feature
permissions are retained across three refactored declarations, making the
approval policy additive against the base. They are unused permissions, not
fabricated source observations. `npm run census` regenerates the inventories;
no generated inventory is hand-merged. `census:check` reports 42 compiler files,
598 declaration events and 40 classes.

Twelve selected shared-runner receipt, execution and semantic-mutant controls
pass. The workspace-fixture group is excluded because it reads `.env` files.
The full acceptance gate run follows the receipt repair.

## Frozen expectation dispute

`7932bed417c3f5b4c7d1` concerns the structural `function-field` row. It is an
intentional expectation-first amendment, committed in `61554f7c` before the
closure implementation `a1d68911`. The commit body cites the pinned seed and
its literal `On{}` result; [closures-amendments.md](closures-amendments.md)
records the exact command, retained field span and enum-profile refusal.
The checker now supports that seed-accepted affine function field.

C3 requires a literal `amend:` line in the historical commit body. That marker
is absent, although the seed observation and amendment are explicit. Rewriting
the old commit is outside the executor boundary. Restoring its old Unsupported
catalog expectation would contradict the seed, the capability and the frozen
closure-field controls. This finding is disputed on that evidence; the row,
source and seed observations remain unchanged. A fresh seed replay and full
structural gate are required below before handoff.

## Receipt repair

All eighteen earlier receipts are retained in `tests/compiler-closures/receipts/history/`.
Their dates, measured times, source hashes, seed observations, runtime results
and failures are unchanged. A structural comparison against `35b979bf` verifies
that only path spelling changed: checkout paths become `$ROOT`, toolchain and
package paths use `.toolchain`/`$BEND_LIB`, and transient gate directories use
`$GATE_RUN`. Historical report and review links now point to those receipts.
No historical hash is rewritten to describe the present source.

The closure harness stops hashing local Markdown that it does not execute.
It retains the accepted source contract, all Bend/proof sources, frozen JSON
and fixture sources, and every host/gate script. `receipt_evidence.py` records
a completed fifteen-gate run only after checking the current closure inputs
against the exported snapshot. Its verification mode rereads the current input
hashes, receipt identity and per-gate closure counts. It never refreshes shared
receipts or implements source-language behavior.

Both changed Python sources parse. The eighteen archival comparisons pass, and
their metadata contains no checkout-specific or transient gate path. This
checkpoint is an evidence-workflow change, not a fresh compiler acceptance.

## Remaining verification

Fresh source/input hashes, committed-head C1/C3/C4 replay and the full
fifteen-gate run are pending in this checkpoint. The old current `closures.json`
is intentionally awaiting regeneration; it is not used to claim acceptance.
The two previously documented HostFailure findings remain disputes
until their frozen function-result probe is freshly replayed. Live semantic,
law and five-axis/composition style qualification remains coordinator-owned.
