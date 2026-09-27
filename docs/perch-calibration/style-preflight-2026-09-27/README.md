# Style scoring-tool repairs and structural baseline — 2026-09-27

Base: main `af3b202`, rubric v6. The whole increment is offline: zero provider
requests and no credentials.

## Repairs

1. **Imported template-law fills parse.** The observer gave an imported law
   fill a placeholder with template arity 0. The compiler-accepted
   `packages/int_map/locality/PROOF.bend` therefore failed with "Expected a
   term; observed '~'" at its recursive `G.edit_here(~join,…)` call. The
   placeholder now has unknown (`Infinity`) arity, as imported templates
   already did. The fill-head clause count and the foreign-template check are
   skipped only for non-finite arity; local laws keep the upstream checks.
   - Parser profile: `…-observer-v2+law-template-arity`.
   - `observer.patch` hunks from the changed region onward come from a fresh
     `diff -u`; earlier hunks keep their original alignment. Applied to pinned
     upstream `bend2/bend.ts` (sha256 `09d2cc5c…`), it reproduces `bend.mts`
     byte for byte with no offsets (`patch -F0` and `git apply`).
   - A full-analysis comparison over all 301 tracked `.bend` files changed
     exactly one file: this proof, from parse-error to 8 law fills
     ([before](parser-status-before.json.gz), [after](parser-status-after.json.gz)).
     All 16 intentional negative fixtures and retained failed specimens still
     fail to parse.
   - The new regression test fails on the previous parser with the original
     message.
2. **Offline structural preflight.** `lint:style --preflight` prepares the same
   candidate states, contexts and composition groups as a live run, without
   request bodies. It reports the units that cannot pass under any rating.
   Details are in [perch-style.md](../../perch-style.md#structural-preflight).
   - The role predicate is now one shared function (`roleContextLimits`), used
     by both scoring and preflight.
   - Option rules, task handling and the empty-inventory failure match the live
     run.
   - Project mode reports the same unavailable composition
     (`explicit_selected_group_required`) as a live `--all` run.
3. **Composition request: reverted to the calibrated form.** `1def9b9` briefly
   added each axis's own rubric instructions to the composition memetic,
   Anticipation and Payoff questions. It treated v6's phrase "under their own
   rubrics" as evidence of an omission. History shows otherwise: the
   generic-paragraph form was introduced deliberately in `3dc7774` (v5), and
   the v5 controls ran under it. The per-axis form is therefore a new,
   uncalibrated request contract, and it is reverted here.
   - It remains candidate **C1** for a paired comparison against the current
     form **C0**. No composition has met its level-3 targets: 0 of 27, best
     memetic .42, Anticipation .13 and Payoff .45, including the four
     reader-unit judgments in `7c13f9a`. Declaration Anticipation reaches .88.
   - Any composition answers produced under C1 between the two commits are
     not production evidence.

**Reuse cost.** The parser-profile bump changes the reuse identity, so every
earlier style receipt fails `--reuse` and every automatic cache entry misses.
This holds even for declarations whose analysis output did not change.
Declaration
reuse could be preserved only by deliberately not bumping the profile for
unchanged analysis output; that decision was not taken here.

**Tests.** `npm run lint:verify` at base `af3b202` ran 84 tests with 83 passing.
The existing corpus parse test already failed on `locality/PROOF.bend`, the gap
repaired here. It now runs 92 tests, all passing: +1 parser and +7 preflight.
Law-rule wiring also passes.

## Structural baseline (`project-preflight.json.gz`)

`--preflight --all`: 2,383 declarations in 284 files; 16 unranked files; 1 file
without declarations; 379 structural blockers. The blockers are:

- 362 truncated units;
- 16 unranked files;
- the project-mode composition, which needs explicit groups.

Exit 3.

| Truncated contexts: Anticipation and Payoff unavailable, so the unit cannot pass | Units |
| --- | ---: |
| Helper limit (16) | 309 |
| Caller limit (4) or 48 KB byte limit (not recorded separately) | 53 |

The 1,801 units that cannot take the supporting role form this **disjoint**
partition, assigned in the order shown:

| Role-context cause | Units |
| --- | ---: |
| Truncated context | 362 |
| Only capitalized type or constructor names unresolved, all local | 1,221 |
| Any hash-addressed package import (`V.*`, `B.*`), untruncated | 201 |
| Any missing local import, untruncated (one retained experiment, `research/compiler-style/family-1/behavior.bend`) | 16 |
| Other: an intentional free-name fixture | 1 |

About the 1,221:

- 235 are datatype declarations. They carry the constant note that datatype
  context is "same-file only".
- 896 are definitions, 76 laws and 14 law fills.
- Most frequent names, counted as units containing the name: `Flag` 414,
  `S.Error` 223, `Error` 145, `S.Token` 102, `Token` 98, `Box` 76, `At` 73,
  `Builder` 60.

Composition groups (preflight output files are in this directory):

- **Project-wide:** 194 of 284 single-file groups are composable. All of the
  other 90 have unresolved context, and 2 of them also exceed 48 KB.
- **`src/driver.bend`** ([driver-preflight.txt](driver-preflight.txt)): 7 of 13
  units truncated. Its composition needs 61,508 of 48,000 bytes and has 29
  collaborators outside the group.
- **int_map locality pair**
  ([int-map-locality-preflight.txt](int-map-locality-preflight.txt)): all 16
  declarations prepare with complete context. Its two-file composition lacks 6
  collaborators, as the edit-locality review recorded.

The largest structural lever is datatype-reference resolution (1,221 units).
Commit `55f1d50` addresses it; its measured effect is recorded in the follow-up
below once integrated. The context caps, the 48 KB composition bound,
negative-fixture scope and hash-import mapping remain threshold or scope
decisions for the user.
