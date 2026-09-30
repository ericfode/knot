# vm-model deterministic pre-review repairs

Baseline: `6e978f19`. The two executor conditions are confirmed.

| Condition | Repair |
| --- | --- |
| C3 `shared-file-shape`, `bc7e4c3c95f3ebca7c07` | Removed the runtime helper and invocation from `scripts/gates/run.py`. Its increment diff again contains only the additive `vm-model` gate row. Restored the shared runner tests to their pre-guard bytes. The guard and controls now belong to `vm/run-gates.py` and `vm/test-runtime.py`. |
| C4 `host-path`, `1ef25c2f374414a817db` | Removed local run-directory and summary pointers from `vm/receipts/review-r1.json`; consecutive runs are identified by ordinal. Historical observations, hashes, timings and comparison results are preserved. |

`python3 -B vm/run-gates.py` checks the Bun version selected by PATH against
io-host's frozen pin before invoking `npm run -s gates`, forwarding runner
arguments and the exit status. A failed probe or mismatched runtime starts no
gate and changes no workspace or receipt. Its three offline controls pass.
The shared runner's 20 original tests pass. No frozen expectation, accepted law
or Bend source changes in this repair.

Direct commands must select Bun 1.3.14 on PATH and export
`BEND_NO_TELEMETRY=1`. The required full gate rerun and proof verification are
pending at this implementation checkpoint. Live Perch and integration remain
coordinator-owned; no provider call is made.
