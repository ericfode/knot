# Version 6 figure reviews

Rubric version 6 judges identity at the figure against the pattern sheet
[KNOT-SHAPES.md](../../KNOT-SHAPES.md). This record holds the pre-registered
expectations for its first live use and, once run, the receipts beside them.

## Status

Live review: **pending**. The worktree used to prepare version 6 has no private
credential file, and the style tool loads `.env` from the Git root of the
checkout it runs in. Run the four commands below from a checkout that has it.
Each figure needs one run; do not rerun an unchanged figure for a different draw.

```sh
npm run lint:style -- --live --figure=docs/style-campaign/figures/owned-time-slicing.json --json --output=docs/perch-calibration/style-v6-2026-09-27/owned-time-slicing.json
npm run lint:style -- --live --figure=docs/style-campaign/figures/int-map-paths.json --json --output=docs/perch-calibration/style-v6-2026-09-27/int-map-paths.json
npm run lint:style -- --live --figure=docs/style-campaign/figures/symbols-trie.json --json --output=docs/perch-calibration/style-v6-2026-09-27/symbols-trie.json
npm run lint:style -- --live --figure=docs/style-campaign/figures/compiler-pipeline.json --json --output=docs/perch-calibration/style-v6-2026-09-27/compiler-pipeline.json
```

Each manifest carries its own fixed task, so the source-blind potential
judgment runs first. Expected request counts: 21, 23, 8 and 6 declaration
requests, plus one task and one composition request per figure.

## Pre-registered expectations

[expectations.json](expectations.json) records, before any provider response,
what the author expects for each lead, composition and member set, with the v5
or v3 prior it should be compared against. The hashes of the rubric, the sheet
and the four manifests are frozen there. A result that misses an expectation is
a calibration finding for the review log; it is not a reason to edit the sheet,
a manifest or a threshold.

## Offline verification

`npm run lint:verify` passes 94 tests plus law-rule wiring with no provider
contact. `tests/perch-style-figure.test.mjs` covers the sheet's presence in
every request and its part in each identity, manifest validation, declared-lead
monotonicity, advisory proof fills inside figures, opaque interface resolution,
stale sheet disclosure, figure-as-context for members and inventory scopes.
All four real manifests validate with zero truncated member contexts and zero
unresolved references; the compiler pipeline composition was unavailable under
version 5.

## Limits

No human preference has been recorded under any rubric version. A model
distribution is a reading prediction, not agreement with the user. Version 6 is
a change to the unit and context of judgment; its thresholds are the version 5
thresholds. Historical receipts keep their rubric identity and cannot be reused
under the new hash.
