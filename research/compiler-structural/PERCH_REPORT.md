# Targeted Perch review

2026-09-26. Perch 0.3.5 through `npm run lint -- <target> --rules <names>`;
model `jev-1.13.0`. The retained current-source review contains 130 relevant
checks and 59 completed provider responses. No finding crossed its configured
threshold; there was no confirmed defect or model-directed repair.

The [source receipt](receipts/perch-source.json) contains 122 checks across
the catalog, parser parameter/dispatch helpers, checker capability/entry helpers,
two adapted evaluator lookups, five law declarations, five proofs, the Bend
observer and checker-bound probe. The [packet receipt](receipts/perch-laws.json)
contains eight law-quality checks of the frozen review packet.

The parsed target declarations are complete. Helper/caller context was truncated
for catalog.catalog, parse.run, check.resolved, six observer IO/entry helpers,
and bounds.token/main. The receipts identify every included file/hash and the
omitted context. External Base/constructor identity resolution remains outside
the Perch parser. Data-only `core.bend` has no executable declaration to review;
the deterministic compile/proof gates cover its representation change.
Malformed/invalid source fixtures are test data, not implementation targets.

Perch is advisory. Its source scores establish neither type acceptance nor
catalog correctness. The five filled laws, 16 reference fixtures, catalog/output
preservation observations, bounds, semantic mutants and existing real Wasm
regression gate supply the separate deterministic evidence. No live calibration,
formal completeness result, whole-compiler proof or GPU execution is claimed.

## Style attention

The concurrent Perch maintenance update added mandatory three-axis style review
before this handoff. A bounded run rated 39 changed declarations with 39 completed
responses and current source/context hashes. The
[full distributions](receipts/perch-style.json) are retained separately from
semantic checks. Command: `npm run lint:style -- --live --jobs=4` followed by the
39 parsed targets recorded in the receipt.

| Axis | Meets target | Below target | Uncertain |
| --- | ---: | ---: | ---: |
| Maximally big brain | 18 | 8 | 13 |
| Delightful to read | 16 | 6 | 17 |
| Highly memetic | 1 | 36 | 2 |

No declaration met all three targets; this is **style attention, not a style
pass**. Context limits and unresolved imports are retained per row.

Review of the low/uncertain targets found two concrete opportunities: replace
the header pass's temporary Datatype representation with an explicit phase type
when the structural checker consumes it, and isolate parameter-shape decisions
from parser continuation plumbing. The nested result binds in `fields` and
`catalog` currently make the pass order harder to scan. The next field-pattern
increment should address this while introducing explicit binder order.

The constructor records, Boolean kind algebra and small proof witnesses were
retained despite low memetic ratings. Their fields and cases correspond directly
to the declared contract; adding notation or branding solely for a higher score
would add concepts without removing an existing distinction. This is a recorded
review judgment, not an assertion that those style targets were met. No semantic
law, fixed oracle or acceptance threshold was changed.
