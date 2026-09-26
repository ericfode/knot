# Perch maintenance procedure

Owner: the Knot Perch-maintenance chat and its weekly heartbeat. Scope:
`/Users/ericfode/src/knot`. The user authorized routine use, surveys of wasted
effort, and autonomous configuration refinement on 2026-09-26. No repeated
permission is needed for those changes. Preserve accepted contracts and local
package ownership. This procedure does not authorize publishing packages,
messaging other chats, changing their status, or modifying other repositories.

## During development

Use `npm run lint -- <file> --rules <relevant-names>` for changed Bend source or
a bounded law-review packet. The npm entry points retain JSON receipts under
ignored `.perch/usage/`. `npm run lint:history` summarizes them. Raw `npm exec
-- perch` bypasses this recording; if an existing package harness uses it,
retain its own receipt and link it from the review log.

Each receipt includes target, source/rule hashes, selected rule names where
explicit, elapsed time, Perch version, requested model, check count, findings,
and status. The wrapper also records actual provider request counts, resolved
model IDs, token usage when supplied, and raw noul probabilities including those
below the reporting floor. This reads a copy of the response without changing
the request or verdict. Receipts omit credentials, source text, and raw provider
errors. They are local operational data, not a public artifact.
Native `scan` results still live in Perch's own store; read those as well.

`lint:style` (`lint:rank` is an alias) uses `command: style-rank` receipts and
[perch-style.json](../perch-style.json). Review materially changed declarations
against all three absolute style targets: conceptual compression, high dopamine,
and memetic identity. No alternative implementation or comparison cohort is
required. Report below-target and uncertain units instead of hiding them behind
a clean defect-check count. Rankings remain a secondary view. Compare model,
rubric and context identities, distributions, and human preferences recorded
before model review. Existing matching receipts can be explicitly reused;
unchanged project-wide repeats are unnecessary. Retain fresh held-out examples
after rubric changes; do not promote the small historical two-axis pilot into
an accuracy claim for the current three-axis rubric. The [style guide](perch-style.md)
defines the desired taste and current evidence limits.

Record a concise entry in `docs/perch-review-log.md` after meaningful rework,
a discovered missed defect, a false positive, or repeated unhelpful findings.
Include the source or receipt, root cause, judgment, measured effort if known,
and the smallest prevention. Use `unknown` for unmeasured time. A finding that
did not lead to an edit may still have been useful; adjudicate it explicitly.

## Weekly review

Run Mondays at 09:00 America/Los_Angeles. Also apply the procedure after a
significant recurring failure while its context is available.
App heartbeat: `maintain-knot-perch-rules`, active in the Perch-maintenance chat.

1. Recover state. Read root/local instructions, this procedure, the review log,
   current rules, Git status, and `.perch/maintenance/state.json` if present.
   Do not restart completed work, stage the entire checkout, or overwrite
   concurrent edits. The separate completed package-campaign heartbeat stays
   paused; this job does not resume it.
2. Survey **new** evidence since the previous review: local usage receipts,
   native scan findings and explained dismissals, package `receipts/` and
   `evidence/`, STATUS/LAW_REVIEW documents, changed tests, failed gates and
   regressions. Where needed, read relevant Knot chat summaries (including
   package chats identified in `packages/threads.json`) to understand repeated
   failed approaches or user corrections. Read only; no coordination messages.
   Use cursors/checkpoints and bounded reads, not the entire history every week.
3. Separate causes: compiler defect, misunderstood Bend semantics, weak law or
   oracle, tooling/provider failure, missing context, duplicate requests, or
   noisy rule. Distinguish an observed failure from a hypothetical hazard.
   Count repeated attempts if visible; claim elapsed time only from timestamps
   that actually measure work. Provider failures are not false positives.
4. Review signal per rule **and rule hash/model**. Record confirmed findings,
   adjudicated false positives, duplicates, unresolved findings, and missed
   defects found by other means. Precision is confirmed/(confirmed + false
   positive) only for adjudicated findings; leave it unknown with no denominator.
   Zero findings or low usage alone cannot establish that a rule is useless.
   Compare utility with request count and measured duration where available.
   For Bend source rules, compare parsed declaration targets and context hashes,
   including truncation and unresolved references. File-era calibration is
   historical evidence, not interchangeable with declaration-era scores. Keep
   the performance clean/broken/held-out controls and immutable repair evaluator
   in the review. The user subsequently authorized stronger repair models;
   use GPT-6 Astra at high reasoning for confirmed repairs, with the same
   immutable gates and at most one compiler-diagnostic retry. Luna 5.6 remains
   excluded. Historical Luna results keep their original model attribution.
5. Make at most two focused rule/procedure changes in one routine review.
   Prefer deterministic fixes for deterministic mistakes. For repeated
   semantic mistakes, add a narrow rule with a concrete counterexample. Narrow
   context/selectors, remove overlap, or rewrite ambiguous rules. Consider
   retiring a rule after three adjudicated false positives of the same cause,
   or after clean/broken controls repeatedly fail to separate. These trigger
   review, not automatic deletion. Never raise a floor just to hide noise.
6. Validate selection locally with `npm run lint:rules -- --json` and
   `npm run lint:verify`; run the affected package's wiring/control harness if
   its rule is touched. Keep package-owned changes out of an active owner's
   work: record a concrete proposal and revisit when that work is available.
   Shared configuration and workflow fixes can proceed independently.
7. When credentials exist, run at most eight targeted file checks per routine
   review, using existing clean, specific broken, and held-out controls first.
   Capture model identity when available, exact input/rule hashes, probabilities,
   and expected-versus-observed outcomes. Never call fixed stub probabilities
   calibration. Stop on authentication/quota failure; do not repeat unchanged
   blocked calls. Never scan the whole repository merely to tune a single rule.
   Freeze the adapter installation and rule set before a paid corpus run; finish
   parser/context edits and offline gates first. If either changes during a run,
   retain the interrupted evidence separately and recheck the final version.
   Synthetic package law packets must select their intended owner rule with
   `--rules`; broader packet-completeness questions are not their test oracle.
8. Keep uncalibrated rules advisory. Promotion requires clean/broken/held-out
   separation and useful adjudicated production findings. Preserve deterministic
   proof/type/mutation gates regardless of model verdicts. Missing credentials
   leave calibration unavailable while local evidence review continues.
9. Record substantive decisions, evidence, before/after behavior, checks, and
   remaining uncertainty in the review log. Advance a local watermark in
   `.perch/maintenance/state.json`, retaining chat cursors if used. Leave
   no-op reviews out of the tracked log. Notify the user only for a meaningful
   change, completed improvement, new failure, or genuinely required action.
   Do not repeat the already-known missing-key notice while unchanged.

## Review entry format

```text
Date / scope / source revision or working-copy hashes:
Evidence links and usage receipt IDs:
Waste or missed behavior / measured effort (or unknown):
Rule + hash / requested and resolved model (or unknown):
Judgment: confirmed | false-positive | duplicate | unresolved | blocked
Change and why (or retain/no change):
Clean / broken / held-out evidence and deterministic checks:
Remaining uncertainty / next trigger:
```

The review log is the durable decision record. Raw run output and empty review
timestamps are not useful project memory. Add scripts or narrow procedures
when they prevent recurring waste more reliably than another model question.
