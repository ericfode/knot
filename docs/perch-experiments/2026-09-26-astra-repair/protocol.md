# Performance review and fast-model repair pilot

Frozen before repair results, 2026-09-26.

Current repair policy: the user subsequently authorized stronger models. The
[stronger-model phase](#stronger-model-phase) below supersedes the Luna-only
restriction for future fixes; the original pilot and its scores remain frozen.

Question: can fast-tier coding models repair small Bend performance defects
reported by Perch while preserving the public behavior? This is a feasibility
pilot, not a model ranking or evidence that Perch improves an unaided model.
Model parameter counts and dollar costs are not available.

## Fixed protocol

- Three cases: growing prefix copy, repeated invariant summary, indexed linked
  list traversal. Existing package algorithms motivated these synthetic cases;
  the cases are not claims of unfixed production defects.
- Before repair, require live Perch findings on each original, passing semantic
  controls, failing original performance gates, and passing known-good controls.
- Try `gpt-6-luna` and `gpt-5.6-luna`, low reasoning, in fresh app agent contexts.
  The standalone CLI rejected `gpt-6-luna` for its ChatGPT authentication; that
  failed availability probe is separate from repair quality.
- One generation per model per case. Supply only its original source, public
  contract, smoke examples, and the applicable rule and live score. No clean
  solution, held-out source, evaluator internals, or other model's output.
- No tools or file inspection by repair agents. Return a complete source file.
  The parent saves it unchanged. Syntax failures count as failed repairs; no
  hand fixes or retries contribute to the one-shot score.
- Freeze hashes of prompts, sources, and evaluator before dispatch. Compile
  with pinned Bend 2.0.29, compare complete outputs with a deterministic host
  oracle, and instrument generated JavaScript to count executed work. Evaluator
  details live in `tests/perch-performance/README.md` and are withheld from
  repair prompts. Re-check Perch on parseable repairs, but never use its verdict
  as the acceptance oracle.
- Record model setting, source hashes, acceptance by gate, work counts, and
  observed turnaround. Agent service does not expose token usage or a separate
  response model ID; record those as unavailable, not guessed. Turnaround
  includes orchestration and concurrent workload, not isolated inference time.
- Keep candidate code out of packages and publication. No automatic deployment,
  acceptance of altered contracts, or weakened deterministic gates.

All four new performance rules remain advisory. Calibrate once on frozen
clean/broken/held-out examples, retaining misses and false positives. Any later
wording change needs new held-out controls. Inspect representative real files
for noise before recommending a workflow. A small successful sample establishes
only that these specific repairs worked under these gates.

## User correction during dispatch

The user restricted repair trials to **Luna 6 only**. Two Luna 5.6 generations
had already completed before the correction could stop them. Their outputs
are excluded from evaluation and no further Luna 5.6 work is authorized.
The active pilot is three one-shot Luna 6 repairs, not a model comparison.
The user also requested parsed Bend units for all source checks. Original
file-based calibration is retained as historical evidence; declaration-based
checks and recalibration supersede it for current configuration.

## Diagnostic retry phase

After recording the one-shot outcomes (one pass, two compiler rejections), allow
exactly one additional Luna 6 generation for each compiler-rejected candidate.
Supply the compiler diagnostic and retain the original contract and source in
that agent's context. No parent-authored repair hint, evaluator details, clean
solution, or gate changes. Report one-shot and after-one-retry results separately.
This phase tests whether cheap deterministic feedback rescues language mistakes;
it does not retrospectively change the one-shot protocol or score.

## Stronger-model phase

The user's later 2026-09-26 instruction, "Go ahead and use a smarter model for
the fixes," supersedes the Luna-6-only requirement. Use `gpt-6-astra` at high
reasoning for confirmed repairs. Luna 5.6 remains excluded.

The first escalation is limited to the rejected `indexed-linked-list` case.
Dispatch its byte-identical original repair prompt to a fresh model context,
without tools, prior candidate outputs, diagnostics, clean solutions or evaluator
internals. Freeze that prompt and the unchanged gate hash before dispatch.
Save the returned candidate unchanged, then run the same compilation, full-output
and operation-count gates. Allow at most one compiler-diagnostic retry, recorded
separately, and retain a failed result if it still does not pass.

Record this as a separate escalation result, not an additional Luna success or
a new three-case model comparison. Recheck accepted source with the relevant
parsed-unit Perch rule. Keep existing accepted candidates and historical receipts
intact. The source remains an experiment artifact, not a production package fix.
