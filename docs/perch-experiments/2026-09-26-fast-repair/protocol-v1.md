# Performance review and fast-model repair pilot

Frozen before repair results, 2026-09-26.

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
