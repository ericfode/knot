# opt-1 receipt portability repair

This executor round starts from `5854e614`. It addresses all seven reported
executor C4 `host-path` conditions, preserving the completed refresh corpus,
implementation, frozen expectations, laws and mutants.

The historical gate runner normalized checkout prefixes but retained its random
run directory. Those directories belong in ignored local evidence. Committed
receipts retain portable file identities and content hashes instead.

| Receipt | Repair |
| --- | --- |
| `receipts/gates-first.json` | Remove `/run/directory`. |
| `receipts/gates-first.txt` | Point `Summary:` to `$ROOT/tests/compiler-opt/receipts/gates-first.json`. |
| `receipts/gates-review2-first.json` | Remove `/run/directory`. |
| `receipts/gates-review2.json` | Remove `/run/directory` and `/optimizer_receipt/copied_from`; retain the receipt path, SHA-256 and equality evidence. |
| `receipts/gates.json` | Remove `/run/directory`. |
| `receipts/gates.txt` | Point `Summary:` to `$ROOT/tests/compiler-opt/receipts/gates.json`. |
| `receipts/manifest-failure.txt` | Replace the exported-worktree prefix with `$ROOT/` in both failure locations; retain file names and line/column numbers. |

`receipts/c4-portability.json` records every condition fingerprint, the before
and after hashes, and the exact permitted changes. Parsed JSON equality holds
after deleting only the five metadata fields. Text equality holds after only
the four path substitutions. Nine volatile paths are removed. Observations,
statuses (including historical failures), counts, commands, timings, assertion
messages and content hashes remain unchanged. Normalization with an unrelated
checkout root is idempotent.

The audit scans every opt-1 receipt for absolute home/temp paths and random
gate-run paths. It also verifies all 177 optimizer and 80 refresh input hashes
against the current files. The repair changes no frozen input, compiler source,
package source, gate implementation or shared receipt. The prior 32-program
seed refresh and its acceptance evidence remain in `REFRESH-2026-09-29.md`.

## Portable evidence procedure

Keep the gate runner's raw summary, logs and export paths under ignored
`.local/`. When retaining an opt-1 gate summary, omit `run.directory` and
copy-source directories. Retain the normalized gate results, source/dependency
hashes, receipt identities, durations and harness limits. For failure stacks,
map the exported-worktree root to `$ROOT`, preserving the relative file and
position. For a textual summary link, use the committed JSON receipt path.
Before committing, compare JSON/text with the raw evidence allowing only these
metadata changes; scan the retained receipt set for host and random-run paths.
No general path-erasing rewrite of observations is permitted.

## Verification and boundaries

The normalization checkpoint passes the preservation audit and
`git diff --check`. Its full-suite evidence before this repair is the unchanged
18/18 result in `receipts/refresh-gates.json`. A fresh complete gate run follows
the checkpoint; its result will be retained in `receipts/c4-gates.json`.

No provider/live Perch call is made. Style axes remain unrated. Current-main
integration, D26 shared-pin reconciliation, Default/empty-core support from
other increments, shared receipt refresh and live review remain coordinator
actions as recorded in the refresh report. The executor does not merge, rebase,
push, or change another worktree.
