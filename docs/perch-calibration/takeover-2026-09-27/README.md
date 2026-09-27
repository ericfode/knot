# Perch takeover verification

Verified on 2026-09-27 UTC (2026-09-26 Pacific) in
`/Users/ericfode/.codex/worktrees/7e98/knot`, branch `codex/perch-takeover`.
**Configuration and live execution work.** The new worktree initially lacked
ignored dependencies and `.env`; pinned `npm ci` and the existing project
credential restored them. The credential is ignored, mode 0600, and absent from
these receipts. No endpoint, model, rule or threshold was changed.

| Check | Observed result |
| --- | --- |
| Installation | Perch 0.3.5; Node 22.22.3; checksum-guarded Bend 2.0.29 parser adapter |
| Doctor | Pass; root `rules: []` is deliberate split-rule configuration |
| Custom rules | 27 registered: 13 shared source, eight law, six package; all advisory |
| Offline verification | 28 tests pass, plus the eight-law selection/exit/coverage gate |
| Provider | Default TypeSafe endpoint resolves and returns `jev-1.13.0` |
| Candidate semantic checks | Four source and eight law checks, two live responses, no threshold findings |
| Style review | One successful inherited response, exact identities rechecked; no duplicate request |
| Finding exit behavior | Known bad validation packet produces exit 3 under mutation-sensitivity |

[Machine-readable configuration](configuration.json), [doctor](doctor.json),
[offline verification](offline-verification.json) and [registered rules](rules.json)
retain the evidence. Source/context identities and immutable pilot inputs are
verified separately in the [pilot takeover receipt](../../../research/adaptive-tasks/style-pilot/adaptive-run-1/takeover-verification.json).

## Detection limits observed live

The existing [wrong-checker-phase synthetic packet](../../../tests/perch-laws/regressions/wrong-negative-phase/LAW_REVIEW.md)
claims an ownership/type restriction was verified by a test that failed during
parsing. The intended proof-claim rule misses it: probability broken **0.19**,
below its unchanged 0.80 floor. The [raw receipt](known-broken.json) preserves
that false negative. The [offline request inspection](request-schema.json)
confirms the correct packet and rule were supplied, with no additional provider
call. This repeats the earlier [audit](../../perch-audit-2026-09-26.md) miss.

The same packet is detected by [mutation-sensitivity](known-broken-mutation.json)
at **0.89**, producing exit 3. That confirms finding delivery; it does not repair
the intended proof-claim rule's calibration. These are judgments of a synthetic
packet, not newly executed compiler-negative tests or semantic mutants. Keep
independent deterministic gates and the rules' advisory status.

## Recovered pilot

The [frozen adaptive-run candidate](../../../research/adaptive-tasks/style-pilot/adaptive-run-1/README.md)
has current style target masses **0.82 / 0.81 / 0.52** for compression, delight
and memetic identity. The last is uncertain; the unchanged target is at least
0.60 on every axis. The experiment is rejected as an all-three demonstration.
Its first-shot deterministic results remain valid by source/toolchain/receipt
identity, and no candidate or acceptance test was rewritten.

The old coordinator stood down. Its shared checkout and unrelated owner edits
remain intact. The existing heartbeat moved to this chat with the scoped-pilot
instructions; the wider component queue remains on hold.
