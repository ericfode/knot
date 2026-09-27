# Targeted semantic and style review

2026-09-26 local date. Perch 0.3.5, model `jev-1.13.0`. The source review covers
85 changed executable declarations/laws/proofs and the bounded observer: 251
relevant checks and 85 completed provider responses. The law packet adds eight
checks and one response. Total: 259 checks, 86 responses, no threshold findings.
No confirmed Perch defect or model-directed repair occurred.

Commands used `npm run lint -- file.bend::name --rules
compiler-checker-trust,bend-fuel-completeness,bend-machine-arithmetic`, plus the
eight `law-*` rules on LAW_REVIEW.md. Source targets outside src receive only
the two applicable Bend rules. [Source receipts](receipts/perch-source.json.gz)
and [packet receipt](receipts/perch-laws.json) retain source/context hashes,
probabilities, counts, model identity and provider completion. Zero coverage is
not included as a pass.

Thirteen source targets have truncated helper/caller context: catalog.catalog;
check.run/functions/resolved; three evaluator-transition laws; parse.run;
patterns.fields/open_fields/branch; wasm.lower/emit. Targets themselves remain
complete. External Base and constructor identities remain unresolved by the
review parser. Data-only declarations are covered by deterministic type/proof
checks and the separate style pass, not falsely counted as semantic methods.

The quantity helper's subthreshold arithmetic score was inspected: its domain
is validated quantities, and it uses comparisons/Boolean composition without
arithmetic or narrowing. No wraparound path was found. The full checker/evaluator
fixtures separately establish its intended cases. No code or law was changed
to satisfy a score. The worklist inspection bound was added during local hostile
review before the frozen Perch run; it was not a model repair.

## Three independent style targets

`npm run lint:style -- --live --jobs=4` rated 96 changed declarations, with 96
completed responses and current source/context hashes. Exact targets, ordered
rubrics, distributions and context limits are retained in
[the style receipt](receipts/perch-style.json.gz).

| Axis | Meets target | Below target | Uncertain |
| --- | ---: | ---: | ---: |
| Maximally big brain | 48 | 20 | 28 |
| Delightful to read | 62 | 19 | 15 |
| Highly memetic | 4 | 87 | 5 |

No declaration meets all three bars: **style attention, not a style pass**.
The lower ratings prompted a concrete reading review. Scope now separates
identity, match order and use obligations; that representation removes the false
assumption that increasing lexical IDs imply match order. The inspection worklist
also makes complete versus exhausted output explicit. Those semantic improvements
preceded the review and are not claimed as measured before/after style gains.

Remaining opportunities are specific: function/field argument checking duplicates
quantity-sensitive traversal, and evaluator frames repeat environment/continuation
plumbing. A bounded family refactor could make those common transitions easier to
recognize without collapsing their different identity and slot rules. The catalog's
header placeholders remain a separate phase-typing opportunity.

Small proof fills, host guards and metadata records are retained despite low
memetic ratings. Their shape directly exposes the contract, and decorative names
or extra abstraction would not remove a case. This is an evidence-backed review
judgment, not a claim that the three targets were met. A future improvement
attempt must retain the frozen independent corpus, laws and runtime boundaries.
