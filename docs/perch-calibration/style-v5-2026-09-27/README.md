# Proportional helper requirements

Perch v5 separates expressive role from contract importance. Supporting helpers
need memetic identity 2 (Recognizable), Anticipation 2 (Guided), and Payoff 2
(Fitting). Leading or uncertain declarations retain level 3. Compression and
Delight stay at level 3, interpreted relative to the actual obligation. Every
probability threshold remains 60%.

The complete selected mechanism independently needs level 3 on identity,
Anticipation and Payoff. High potential profundity adds Galaxy 5; low, missing or
uncertain potential does not. Classifying everything as a helper cannot bypass
composition review. `--all` provides declaration inventory and needs bounded
composition reviews before a full qualification.

This policy implements the user's requested scope correction. Its model
judgments remain advisory: the small calibration below contains a held-out
Anticipation miss and one uncertain role classification. No full style pass is
claimed for these implementations.

## Frozen controls and results

[Expectations](../../../tests/perch-style-role/expectations.json) record source,
task, policy and engine hashes before any live review. Controls are assistant
judgments, not a human calibration panel. Development results were recorded in
[development.md](development.md) before opening the held-out results. No rule
wording, source, thresholds or expectations changed between those phases, and
no control was rerolled.

All live style responses resolved to **jev-1.13.0**. Four style file checks
covered 20 declarations and made 28 provider requests, including four separate
task and four composition judgments. All had complete selected context and no
provider errors. Each pair has identical behavior under the independent gates.

| Phase and helper | Role | Memetic 2+ | Anticipation 2+ | Payoff 2+ |
| --- | --- | ---: | ---: | ---: |
| D01: direct zero-default access | Supporting | 77% | 84% | 85% |
| D02: tagged, swapped access relays | Supporting | 12% | 26% | 52% |
| H01: direct index-to-bit conversion | Supporting | 87% | 98% | 96% |
| H02: redundant branch and cancelling XORs | Supporting | 56% | 67% | 60% |

The development pair separates on both prespecified axes. The held-out memetic
result is uncertain, below the 60% pass bar; its Anticipation result wrongly
passes the operator's negative expectation. The score still drops 31 points,
but relative separation does not establish an accurate absolute threshold.
Payoff was recorded without a prespecified negative expectation and must not
be promoted into a successful calibration claim.

H01's central traversal named `helper` is leading at 94%, as expected. Its thin
public `select` entry is uncertain at 45% leading probability, rather than the
expected supporting classification. It conservatively retains level 3. H02's
same entry is supporting at 37% leading probability: this is observed classifier
sensitivity to collaborating context, not a reason to relabel source or cherry
pick a receipt.

D01 is the unchanged final source from the Parallax trial at `2cab333`. Its
`sample` now meets the three role-scaled requirements, but Delight is uncertain
at 53%. Two of six declarations meet all five applicable targets. The complete
Life mechanism is below the three leading targets (30%, 7%, 22% respectively).
The held-out mask mechanisms are also below the complete-mechanism targets.
All four task judgments are low-potential, so none requires Galaxy brain.
The scope change does not turn these implementations into full style passes.

[D01](D01.json), [D02](D02.json), [H01](H01.json) and [H02](H02.json) retain all
distributions, exact request identities, source provenance and qualifications.
[summary.json](summary.json) extracts the helper and composition results without
changing their meaning. Historical v3/v4 receipts remain historical; the new
rubric and request hashes invalidate reuse across this policy change.

## Deterministic and semantic verification

- `npm run lint:verify`: **84/84 tests**, plus law-rule wiring. New coverage
  checks role scaling, missing/context-limited role evidence, names and public
  entry points, all-support composition bypass, high/low/unknown potential,
  project-inventory limits and exact receipt reuse. Frozen v3/v4 tests still run.
- `npm run lint:rules -- --json`: exit 0. No semantic rule was changed.
- All four controls typecheck and compile with pinned Bend **2.0.29**, commit
  `574b6d39a235b539eb19a5c532993a0abb3d11ad`. Generated modules are ignored build output.
- Each Life variant passes **1,537 behavior cases and 21 composition laws** in
  both Node and Bun, using the unchanged original experiment oracle.
- Each mask variant passes **1,890 cases** in both runtimes against an independent
  arithmetic oracle, including order, duplicates, boundaries and input preservation.
- Four targeted semantic file checks cover **80 applicable rule checks**, with
  zero reported findings. Rules: machine arithmetic, fuel completeness,
  growing-prefix copying and linked-list indexing. These checks are advisory,
  separate from compiler and behavior acceptance.

[verification.json](verification.json), [test log](lint-verify.log),
[Node receipt](controls-node.json), [Bun receipt](controls-bun.json) and
[semantic usage](semantic-usage.json) retain counts, identities and observations.
The four `*-semantic.json` files retain the corresponding detailed reports.
The eight-file review budget was respected; no whole-repository paid scan ran.

To reproduce deterministic controls with the pinned toolchain installed in the
checkout, compile each `tests/perch-style-role/{D01,D02,H01,H02}.bend` with
`bun tests/perch-performance/compile.ts ABS_SOURCE ABS_MODULE`, saving modules as
`ID.mjs` in an ignored directory. Run
`node tests/perch-style-role/check-controls.mjs MODULE_DIR OUTPUT.json`, then the
same command with Bun. The Life oracle's unchanged hash is in both receipts.

For a new paid review, use a fresh output path, e.g.
`npm run lint:style -- --live --json --jobs=2 --task=tests/perch-style-role/life.task.md --output=NEW.json tests/perch-style-role/D01.bend`.
H01/H02 use `mask.task.md`. These frozen controls are now seen evidence; future
rule changes need fresh held-out examples. Broad human taste calibration and
robust rejection of irrelevant anticipation cues remain unestablished.
