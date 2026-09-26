# Three-axis style review — 2026-09-26

The user clarified that existing code must be assessed against a quality bar,
without requiring competing implementations. All three axes apply independently:
conceptual compression, high-dopamine reading, and memetic identity. The last means
a distinctive, felt visual/conceptual rhythm that gets into your head and creates
an appetite for more of that style. Its own ideas and vocabulary reward insider
fluency: knowing the words unlocks a shared grammar. Mere recall or teachability
was explicitly too weak a description.

## What changed

`npm run lint:style` now accepts a single declaration, file or explicit `--all`.
`lint:rank` remains an alias; alternatives and a shared task are optional. Actual
parsed definitions, law declarations/fills and datatypes receive three Score
questions in one request. The result includes each quality decision and a separate
rank order per axis. Agent instructions require style review of materially changed
Bend code instead of skipping it when no alternative exists.

The provisional target on each axis is level 3 or 4 with at least 60% normalized
probability mass. At most 40% is below target; the middle is uncertain. Every axis
must meet its target for a declaration to pass automatically. A completed review
can therefore return exit 3 for style attention. These thresholds are review
policy, not measured agreement with the user. The rubric was not retuned after
seeing this first project result.

## Complete project inventory

Git discovery found **232 project Bend files**: tracked files and nonignored new
files, including packages, compiler, research, tests and retained experiments.
**1,887 parsed units received all three ratings: 5,661 answers.** There were
1,872 new provider requests/responses and 15 explicitly reused units from the
first live example. All answers resolved to `jev-1.13.0`. No provider failed.
The final example reused 16 units without another provider call.

| Axis | Meets target | Below target | Uncertain |
| --- | ---: | ---: | ---: |
| Maximally big brain | 1,246 | 323 | 318 |
| Delightful to read — high dopamine | 779 | 622 | 486 |
| Highly memetic | 5 | 1,828 | 54 |

**Zero units meet all three automatic bars.** This is a visible review backlog,
not a claim that the code is incorrect or that every low rating deserves a rewrite.

The inventory includes 1,342 definitions, 182 law declarations, 182 proof fills and
181 datatypes. Ten files could not be parsed: three retained failed repair
specimens and seven negative compiler fixtures. One import-only file has no
declaration of its own. All are named in the receipt; none was silently assigned
a score or counted as passing. The project command therefore returned exit 1 for
incomplete coverage, while retaining ratings for all parseable units.

Context was truncated for 308 units. Definition/law helper context is bounded;
datatype context includes sibling types and at most four direct same-file users,
with imported/transitive dependencies explicitly unresolved. All recorded input
and helper hashes matched at completion and at consolidation. Concurrent compiler
work may subsequently change the working copy; the receipt identifies its exact
reviewed snapshot.

Evidence:

- [Every unit, all three decisions and ranks (CSV)](perch-calibration/style-project-2026-09-26.csv).
- [Complete distributions, input/context hashes and exclusions (compressed JSON)](perch-calibration/style-project-2026-09-26.json.gz).
- [First live example, 15 functions](perch-calibration/style-scope-2026-09-26.json).
- [Complete file example, 15 functions plus Scope datatype](perch-calibration/style-scope-complete-2026-09-26.json).
- [Tooling semantic review and adjudications](perch-calibration/style-tooling-2026-09-26.json).

The project evaluation/report phase measured 25.890 seconds, excluding discovery
and parsing. This is one run, not a sustained latency or productivity benchmark.
The 14.4 MB JSON was compressed losslessly to about 643 KB for the repository;
the original local usage receipt remains available. Source text and credentials
are absent from these style receipts.

## A real command and output

```sh
npm run lint:style -- --live src/scope.bend \
  --reuse=docs/perch-calibration/style-project-2026-09-26.json.gz
```

Recorded output, with the individual-unit lines and secondary ranks omitted here:

```text
0/16 declarations meet all 3 style targets.
Maximally big brain: 14 meet target; 0 below target; 2 uncertain.
Delightful to read — high dopamine: 9 meet target; 2 below target; 5 uncertain.
Highly memetic: 0 meet target; 15 below target; 1 uncertain.
```

This returned exit 3: complete coverage, current source hashes, style attention
needed. All 16 matching answers were reused, with zero new requests. Omit `--reuse`
to obtain a fresh review when needed; changed context invalidates reuse.

## Useful signals and calibration questions

The highest memetic ratings belong to `src/parse.bend::run`, `parse::parse`,
`wasm::lower`, `check::run`, and `eval::step`. All five meet that axis, while their
conceptual-compression ratings remain uncertain or below target. Four of those
five have truncated context. The model appears to recognize an expressive grammar
in the dispatchers while finding their decomposition harder to compress. This is
an interpretation of the ratings, not a model-supplied explanation or a human
preference result.

`packages/int_map/main.bend::set_path` receives 93% probability at the conceptual
target and 95% at the reading target, but 32% at the memetic target. The difference
between satisfying symmetry and a distinctive expressive identity is therefore
visible in this first result. It is a useful candidate for human calibration;
agreement with the user has not been established.

At the other extreme, mechanical proof fills and simple projections receive very
low ratings. A short canonical proof should not be inflated merely to impress a
style model. Keep these ratings in the evidence and examine whether the judge is
recognizing the role and vocabulary of such units. The memetic rubric's strong
selectivity and possible preference for large dispatchers need held-out checks,
not threshold changes designed to make this corpus pass.

No source implementation, accepted law or proof was changed to chase a score.
All three objectives are now explicit and observable; their quality as a proxy
for the user's aesthetic remains a calibration task.

## Verification

`npm run lint:verify` passes 25 offline tests and law-rule wiring. New cases cover
single-unit review without a cohort, all-axis targets, uncertain distributions,
Git inventory including new files/datatypes, explicit invalid/empty coverage,
ignored-file exclusion, concurrent response attribution, changing helper hashes,
compressed receipt reuse, provider/model failure, and secret-free evidence.

A separate live Perch review of the changed CLI completed two request groups.
It emitted destination, size and ignored-error advisories. Destination remains a
false positive for operator-controlled local CLI configuration. Size remains an
unresolved refactoring suggestion. No ignored error was reproduced: provider and
model failures return 1 with retained coverage, inventory failures are listed and
return 1, and source changes return attention status. That generic defect label
remains unresolved rather than being credited as a confirmed repair. The receipt
retains all three advisories and their evidence.
