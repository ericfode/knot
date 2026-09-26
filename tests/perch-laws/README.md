# Common law-rule controls

`cases.json` contains one clean, one deliberately broken, and one held-out
specimen for each common law rule. Labels apply only to that named rule, not all
eight rules or a package's readiness. Specimens are synthetic, not actual proof
or mutation receipts. The held-out rows should not be used to rewrite a rule
after every observation; add fresh held-out examples after using one for tuning.

Live calibration ran on 2026-09-26 against `jev-1.13.0`: 19 of 24 controls
matched their labels at the current reporting floors. Five defective packets
were missed. See [the retained results](../../docs/perch-calibration/laws-2026-09-26.json).
Do not interpret the offline wiring check's stub responses as model quality.

```sh
node scripts/check-law-rule-wiring.mjs
# Explicit provider requests, separate from the offline gate:
node scripts/calibrate-law-rules.mjs --live
```

For manual live calibration, materialize a selected row's `packet` field as
`tests/perch-laws/<opaque-id>/LAW_REVIEW.md`. Do not include its expected label,
split, or rule name in the model's source packet. Run `perch check` with only the
row's named rule and `--json`. Keep packet/rule hashes, provider/model, complete
raw probabilities, exit code, coverage and expected label in a separate receipt.
The script automates this procedure with opaque case headings and temporary
packet paths; neither contains the expected label or split. It removes only its
own generated files and retains reconstructible input hashes and receipt links.
Every check must select exactly one relevant rule. Compare clean/broken readings
before evaluating held-out cases; no verdict is a formal adequacy proof.

The shared rules remain advisory. A broad rule that cannot distinguish these
cases needs narrower observations or separate packets, not a higher threshold.

`regressions/lossy-projection/LAW_REVIEW.md` is an expected violation of
`law-observable-essence`: a content observer that discards empty slots masks a
stale length. The Vec campaign exposed this case; its owner added a separate
length law. This is a regression control, not an unused held-out example.

`regressions/wrong-negative-phase/LAW_REVIEW.md` is an expected violation of
`law-proof-claim-integrity`: a parse failure is misreported as a type/ownership
rejection. Vec release review and TermStore's own negative-fixture check exposed
this recurring issue. The gate now requires the intended checker diagnostic.
