# Modules review round 2

The four confirmed findings are fixed. The twelve new probes preserve exact
seed observations frozen in `0474aa7` and `483f684`, before the corresponding
repairs. No existing source-language fixture or expected outcome changed.

| Finding | Disposition and evidence |
| --- | --- |
| Symlink and case aliases become Invalid | **Fixed.** Both seed programs return `Lit{}`. Native and Bun check/eval/compile return `Unsupported load path-identity`; rejected compilation preserves the existing artifact. The adapter checks exact directory-entry spelling and symlinks, including entry/bundle roots before normalization. |
| A module named Bool takes over Base names | **Fixed.** a1, a2 and a5 reject with `Invalid load duplicate-global` in both import orders. `fresh` checks bare and qualified names in the appropriate category; Base installation checks the existing symbol sets; dependency selection has no user shadow set. A no-Base control still agrees across seed/evaluator/Wasm. |
| Constructor names become pattern binders | **Fixed.** Module-local and full-Base constructor inventories reject ordinary and reusable binders with `Invalid check constructor-pattern-binder`. g2/g3 and both promoted variants match the seed. Checked laws retain the separate term/constructor categories and a legal term-name binder. |
| Column-zero foreign body becomes Invalid | **Fixed.** The seed returns `Lit{}` with its foreign warning. All three Knot commands report `Unsupported check foreign-definition`. Non-string imports after declarations still report Invalid. |

## Mechanism and law boundary

The loader still produces one completely checked user book. It uses a new
native/Bun metadata query only to establish canonical lexical path spelling.
Source parsing, name qualification, Base selection, checking, evaluation and
emission remain in Bend. Pinned Base retains its deliberate toolchain symlink
and its independent digest check.

There are 81 filled laws: loader/path 23, qualification 23, Base selection 20,
and pin helpers 15. All four complete proof entries print `All terms check.`.
Thirteen new laws cover qualified freshness, ordinary/reusable constructor
binders, Base category collisions, import classification, and host-query outcome
separation. These remain helper/transition laws, not proofs of the host adapter,
whole-graph confluence, SHA refinement or compiler correctness.

## Independent regressions and mutants

The review suite adds twelve seed fixtures: symlink-directory, case-alias,
canonical-control, base-first-collision, base-last-collision, base-body-shadow,
no-base-control, local-ctor-binder, base-ctor-binder, foreign-column-zero,
base-promoted-ctor-binder and local-promoted-ctor-binder.

The five original mutants remain. Nine additions attack path classification,
qualified freshness, late Base collisions, constructor-binder rejection,
column-based foreign-body classification, the JS symlink check, exact case
spelling, the full global constructor inventory, and reusable binders. Each
Bend mutant passes the pinned seed's complete typecheck before its wrong
observation is compared to the independent fixture. The two JS mutations also
pass `node --check`. No parse/build failure or timeout counts as a kill.

| New mutant | Frozen witness |
| --- | --- |
| `path-identity-ignored` | `symlink-directory` |
| `qualified-freshness-ignored` | `base-first-collision` |
| `base-collision-ignored` | `base-last-collision` |
| `pattern-constructor-ignored` | `local-ctor-binder` |
| `foreign-body-uses-column` | `foreign-column-zero` |
| `host-symlink-ignored` | `symlink-directory` |
| `host-case-ignored` | `case-alias` |
| `pattern-global-ctors-dropped` | `base-ctor-binder` |
| `promoted-constructor-ignored` | `local-promoted-ctor-binder` |

## Necessary integration changes

The coordinator-selected host query adds one foreign declaration. The seed now
reports five exact foreign-dependent definitions in each module-aware CLI.
`host-check-expectations.json` pins those outputs and the emitted compiler's
seven-effect requirement list. The assertion amendments are isolated in
`79ed2aa`, `f4c3224` and `48fe6ec`; ordinary proof/observer checks retain the exact
`All terms check.` requirement. Mutant scratch builds copy both the Bend files
and the new C/JS adapter directory.

The census keeps foreign code forbidden by default. A reviewed exception allows
only `foreign` in the exact SHA-256 of `src/path-host.bend`; changed bytes,
other files and other forbidden features still reject. Four literal controls
were committed before that policy extension. The printed `census:approve`
summary is retained in the repair commit. Inventory files were regenerated,
not merged by hand.

The manifest closes every local import and retains the current interface-context
policy. The six module groups select their mechanisms and proofs in full;
collaborators enter as checked interfaces. Every compiler declaration remains
covered by the full manifest.

## Complete deterministic gate run

`BEND_NO_TELEMETRY=1 npm run -s gates -- --jobs 2` exited 0. All 18 registered
gates passed. The [verification receipt](receipts/review-round2-verification.json)
retains the normalized runner summary, completion lines, exact counts and
earlier failed attempts. The [module receipt](receipts/modules.json) contains
the native/Bun observations, four complete proofs and all mutant kills.

| Gate | Exact passing counts |
| --- | --- |
| frontend | 14 reference fixtures, 28 parser observations, 24 boundaries, 4 boundary laws, 6 classification laws, 4 semantic mutants; 29 classification fixtures in 2 lanes, 7 classification mutants, 174 downstream rejections |
| checker | 49 fixtures, 98 checks, 10 depth probes, 16 catalog-bound observations, 7 mutants |
| structural | 16 fixtures, 64 phase observations, 4 boundary pairs, 7 mutants |
| fields | 40 fixtures, 240 phase observations, 36 budget probes, 6 host probes, 12 level/inspection observations, 9 mutants |
| wasm | 25 programs, 90 reference calls, 2 execution lanes, 64 rejection pairs, 44 boundaries, 7 mutants |
| wasm-trust | 3 entries, 0 proof holes |
| fields-trust | 4 entries, 0 proof holes |
| structural-trust | 2 entries, 0 proof holes |
| owned-store | 3,532 cases in 2 lanes, 15 literal witnesses, 6 mutants |
| flat-store | Per lane: 13,621 observations, 3,534 instances, 2 installed boundary states, 7 lifecycle checks; 2 lanes, 9 mutants |
| recursion | 19 fixtures, 114 phase observations, 4 fuel probes, 3 mutants |
| fields-wasm | 8 fixtures, 32 seed calls, 64 evaluator and 64 Node observations, 50 enum-byte checks, 30 boundaries, 4 mutants killed in both lanes, 5 new checked laws |
| modules | 63 fixtures, 71 seed calls, 126 checks, 142 evaluations, 126 compilations, 58 Wasm observations, 23 identical-byte pairs, 80 preserved outputs, 46 audits, 22 pin observations, 6 tampered-Base observations, 14 mutants, 4 proof entries / 81 filled laws |
| census | 44 compiler files, 837 declarations, 42 feature classes |
| perch-context | 33 controls, 8 mutants, 23 compositions, 837 distinct declarations, 2 identical preflights, role-limited 475 to 0, 0 blockers, 0 provider requests |
| lint:verify | 168 tests, 8 law-rule wiring controls |
| bootstrap | 745 corpus files, 9 judge mutants, 4 controls; 8 stages: 2 reached, 2 blocked, 4 not run |
| classification | 17 frozen seed outputs, 17 parser observations, 6 mutants, 16 filled frontend laws |

The bootstrap **harness** passes: the reference stage agrees on 745/745 files and
the C1 stage on 57/57 enum cases. Building the next compiler/parser stages still
reports `Unsupported lex literal`. This is not self-hosting acceptance.

`npm run -s gates:verify` passed 18 controls. `npm run census:test` passed all
79 tests, including the four new literal host-policy controls. Runner receipt
drift was 63 identical, 7 volatile-only and 15 semantic; shared receipts were
left to the coordinator, as required.

Three earlier full runs remain failed evidence:

1. [Run 1](receipts/review-round2-run1.json.gz): exact seed CLI warnings, missing
   adapter scratch copies and merged manifest closure required integration fixes.
2. [Run 2](receipts/review-round2-run2.json.gz): only the two stale runtime trust
   inventories failed; `48fe6ec` records their exact seed-derived amendments.
3. [Run 3](receipts/review-round2-run3.json.gz): two native builds reported
   `found no clang`, blocking the dependent Wasm trust gate. Clang 21 was present
   on inspection; the same executable inputs passed with two workers. The
   earlier discovery failure's cause was not established.

After the passing run's export, one stale sentence in `src/SPEC.md` was corrected
to acknowledge the already documented host effect. The receipt preserves that
prose-only hash difference; compiler sources, contract JSON, fixtures and gates
match the executed inputs. The manifest preflight was refreshed after this
documentation correction. Original frozen language expectations are unchanged.

## Preflight

All preflights are offline; no environment file or provider was accessed.

- Changed implementation and law/proof files, direct invocation: 280 declarations
  in nine files; 32 truncated/role-limited contexts (nine caller/byte, eight file,
  fifteen helper limits); combined composition 99,492 / 48,000 bytes, unavailable.
  These total 33 structural blockers and produce exit 3.
- Full interface-context manifest: 23 groups, 1,357 declaration occurrences across
  44 files; zero truncated/role-limited contexts, zero unresolved references,
  all 23 compositions available, zero structural blockers.
- New fixtures: the parser rejects `g2-promoted/main.bend` as intended for a
  constructor-named binder. That negative fixture cannot receive a style score.

Compression, Delight, memetic identity, Anticipation, Payoff and potential
profundity have no live ratings. Structural preflight is not a style pass.
The full [direct receipt](receipts/review-round2-preflight.json.gz) and
[manifest receipt](receipts/review-round2-preflight-manifest.json.gz) retain the
per-declaration limits and source identities.

## Limits and next increment

The supported host is the pinned macOS/Bun/native environment. The case-alias
probe requires a case-insensitive filesystem and fails explicitly if unavailable.
The host query trusts filesystem metadata and assumes files remain stable during
loading; it does not provide race-resistant descriptor identity. Symlink/case
alias equivalence remains Unsupported, rather than realpath-based identity.
Mixed absolute/relative roots, absolute import spellings and named packages keep
their prior Unsupported classifications. Base still uses a repository-relative
path. No broader Base language, IO ABI, fielded/recursive module Wasm or
self-hosting capability is added.

The coordinator owns live Perch review, integration and refreshing shared
receipts. A later IO ABI increment can replace the conservative identity query
with canonical module handles.
