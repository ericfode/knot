# Nest review round 3

All four confirmed findings are fixed. Each finding's seed-derived fixtures
were frozen in their own commit before its repair (D7). Original nest
conformance is unchanged at **38/40**: the two explicitly unmet recursion
cases and both general lowering theorems remain open. This increment does not
establish self-hosting or a live Perch/style pass.

| Commit | Change |
|---|---|
| `57d5a41` | Merge main `cc9f2fd`; keep both gate registrations; census regenerated, empty approval |
| `80702fb` | Freeze 20 dotted-binder and malformed-name fixtures |
| `2ae8dca` | Name grammar in the lexer; single-word pattern and live let binders |
| `6637ef0` | Freeze 25 empty-binder fixtures (14 accepted, 11 controls) |
| `8eb7914` | Ordered dead-code rule; fuzzer atoms for dotted names and empty binders |
| `fef55dd` | Freeze 16 line-broken header fixtures (13 accepted, 3 controls) |
| `ebf0b52` | Headers joined up to their colon; fuzzer line-broken separators |
| `0b6cfc0`, `f0ffea4` | Register `nest-round3`; specs, contract and census inventory |
| `d2d0b80` | Review-log entry and campaign state |
| This commit | Nest-owned receipts, preflight record and these dispositions |

The original fixtures and expectations, the round-2 review fixtures and
expectations, and every existing gate assertion are unchanged. The round-3
manifest was frozen three times; each freeze left all earlier entries
byte-identical, and `round3_seed.py` replays all 61 fixtures and 82 seed calls
with no differences.

## Findings

| Finding | Disposition and evidence |
|---|---|
| Dotted pattern binders accepted | **Fixed.** The seed parses every pattern term with `parse_patt`; a dotted name is a `Ref`, never a binder (`a pattern (a binder or a constructor)`). `S.words` counts the words of a name; `S.binder` requires exactly one. The parser rejects a dotted pattern variable or promotion (`Invalid parse pattern-binder`) and a dotted plain, reusable or typed let (`Invalid parse binding-name`). The check sits where the matrix variable rows, multi-column rows and both field paths (`P.fields` and nested matrix fields) get their binders, so a dotted binder never reaches `M.binder`, `M.validate` or `P.fields`. Seven pattern fixtures cover the variable row, multi-column row, flat and nested field, promotion, `_.x` and `On.x`. The seed keeps dotted names for parameters, scrutinees, fields, definitions and erased lets (it reads `-name` with `parse_name`); five accepted controls confirm these and agree in the evaluator and both Wasm profiles. |
| Malformed names accepted | **Fixed in the lexer**, as requested. The seed's `parse_lexeme` rejects any word that opens with a letter or `_` unless it matches `[A-Za-z_]\w*(\.[A-Za-z_]\w*)*`. `L.lexeme` reports `Invalid lex name` where such a word ends. Numbers and paths are unaffected: import paths with a dotted segment are already rejected by the seed (`an import path of plain names`). Five fixtures cover `x.` in a body, `a..b` as a parameter, type and field name, and `a.1` as a pattern; a comment containing `a.. b. c.1 _.x` stays accepted. |
| Missing arms under a live empty binder: multi-column Invalid | **Fixed by modelling the seed's rule exactly.** The seed's `check-efq` accepts a missing arm when `ctx_dead`: a live binder in the context has an empty constructor set. `match_flatten` introduces binders in match order: parameters before the scrutinee, and a split's fields ahead of the remaining parameters. Knot's `open` frontier is that order. `E.dead(scope,types,level)` therefore counts every live binder outside the pending suffix that starts at the scrutinee whose constructor set is empty: an emptied residual (as before) or a zero-constructor datatype. e11, e16, e19, e21, e22 are accepted. The requested rejecting controls stay `Invalid check missing-arm`: e4 and e15 (empty binder after the scrutinee), e27, e32 and an erased alias (erased), e5, e29 and a nested case (empty field after the matched one). |
| Flat and field matches still Invalid | **Fixed by the same rule** on the single-column path: `match_body` passes the scrutinee's level to `E.dead`, and fields join the frontier ahead of the remaining parameters. empty-flat, e30 (zero rows), e24, e28 and e31 are accepted; so are a parameter before a field or nested field, an empty field before a nested one and an empty `Data` type. A level-order rule would be unsound here: `f(p: P2, v: V)` with a missing arm on a field of `p` has `v` at a lower level, but the seed rejects it (`empty-param-after-field`, `empty-param-after-nested`). |
| Newline in a multi-column case header Invalid | **Fixed.** The seed's `parse_terms` skips all whitespace, newlines and comments up to the header's colon. `P.header` drops line breaks from a `match` or `case` header up to its colon and leaves the tokens after the colon untouched, so `MatchTail`, `RowTail`, `Arms` and pattern arguments keep their logic and depth budget. This fixes the reviewer's multi-column repros and also the pre-existing single-column, scrutinee (p20, p31, p41), in-brace (p30) and promotion breaks. A header without a colon before the next case and a trailing comma before the colon stay Invalid, as in the seed. |

The `empty-binding` accepted programs lower to a partial core `Case`; the
missing branch is unreachable because no value of the empty type exists. Every
accepted round-3 book compiles in the enum or fields profile, and `main` agrees
between the seed, the evaluator and Wasm in both compiler lanes.

## New checked laws

In `src/LAWS.bend`: `malformed_word_source`, `dotted_pattern_binder`,
`dotted_let_binder` and `header_joins_lines`, each quantified over location
or token suffix, plus the ground `name_words_witness` and
`line_broken_scrutinees_witness`. In `src/matrix-LAWS.bend`:
`pending_binder_witnesses_nothing`, a general law: a binder in the pending
suffix never witnesses dead code, proved by congruence on the membership
hypothesis. Also the ground `introduced_empty_witness` and
`pending_empty_witness` (the e11 and e15 shapes), and the two residual laws
restated at a scrutinee. Following round 2's naming finding, every fully
ground new law carries the `_witness` suffix. `src/PROOF.bend` and every
`src/*-PROOF.bend` entry print `All terms check.` Falsifying each new law
makes its proof entry fail at that law. [LAW_REVIEW.md](LAW_REVIEW.md)
classifies them and names the two obligations that rest only on fixtures and
fuzzing: `E.dead` equals the seed's `ctx_dead`, and the name and binder
predicates equal the seed's lexeme and pattern rules.

## Deviations from the requested repairs

- **Finding 1 site.** The reviewer asked for validation in
  `M.binder`/`M.validate` and in `P.fields`. The check is in the parser
  instead, because the parser is the only producer of pattern `Variable` and
  `Promotion` nodes. Both matrix paths and both field paths receive their
  binders from it, so a dotted binder never reaches `M.binder`, `M.validate` or
  `P.fields`. The seven pattern fixtures cover each position, and the
  `dotted-pattern-binder` mutant is killed at that single site. The seed also
  rejects the form while parsing.
- **Findings 2 and 3** share one freeze (`6637ef0`) and one repair
  (`8eb7914`). The reviewer's finding-3 fix reads "apply the same repair as in
  the multi-column finding", and the ordered rule is a single definition used
  by both the flat and the matrix path.
- **The exact rule, not the fallback.** Both findings allowed Unsupported as a
  fallback. The repair implements the seed's order-sensitive rule instead. The
  rejecting controls therefore stay `Invalid check missing-arm`, matching the
  seed, rather than becoming Unsupported.

## Gate `nest-round3`

`round3.py` replays the seed, checks the matrix proof entry, builds both
compiler lanes, and runs all 61 fixtures:

- 32 accepted books: check, compile in their profile, evaluator and Wasm on
  every seed call, with native/Bun module equality;
- 29 rejections: the reviewed diagnostic in check, eval and both compile
  profiles, with existing artifacts preserved.

Eleven type-correct mutants each typecheck and are killed in both lanes
(22 kills): `dotted-pattern-binder`, `dotted-live-let`,
`erased-let-as-pattern`, `accept-malformed-name`, `unordered-empty-context`
(the "any empty binding" rule), `fields-after-parameters` (level order),
`ignore-empty-datatype`, `erased-empty-witness`, `case-header-layout`,
`match-header-layout` and `header-past-colon`.

## Fuzzer

`fuzz.py` keeps seed **1313166164** and **3,000** programs. It adds:

- dotted and malformed atoms (`a.b`, `+a.b`, `_.x`, `On.x`, `v.`, `a..b`,
  `a.1`) in 1 of 12 pattern slots, `a.b` bodies and a dotted parameter;
- in a quarter of the programs, a live, reusable or erased binder of an empty
  `Type` or `Data` datatype, as a parameter or field, before or after the
  scrutinee, with zero-row matches;
- line-broken header separators in 1 of 8 multi-column positions.

On this corpus the current compiler and the seed both report **242 Accepted
and 2,758 Invalid**. False acceptances, false Invalid, Unsupported, Exhausted
and host/internal failures are all **0**, and all **242** evaluator values
agree. The pre-fix compiler (`57d5a41`) on the same corpus gives
**76 false acceptances and 32 false Invalid** (19 missing-arm, 13 parse).
This randomized control uses the native lane; the frozen fixtures cover both
lanes and Wasm. It is bounded evidence, not a proof.

## Gates

Fresh run: `BEND_NO_TELEMETRY=1 npm run -s gates -- --keep-scratch` on
`d2d0b80` (every code, fixture, spec and gate change of this round), scratch run
`run-cqmhwjh8`, started `2026-09-28T08:07:53Z`, 398.4 seconds with 4 jobs,
**exit 0, 23/23 gates passed**. The counts come from that run's summary and
receipts; they count different observation kinds and must not be summed.

| Gate | Result and exact coverage |
|---|---|
| `frontend` | PASS: 14 fixtures, 28 lane observations, 24 boundaries, 4 mutants |
| `checker` | PASS: 49 fixtures, 98 lane observations, 10 budgets, 2 bounds / 16 observations, 7 mutants |
| `structural` | PASS: 16 fixtures, 64 lane observations, 4 bounds, 7 mutants |
| `fields` | PASS: 40 fixtures, 240 lane observations, 36 budgets, 6 host boundaries, 2 bounds / 12 observations, 9 mutants |
| `wasm` | PASS: 25 fixtures, 90 reference calls in 2 execution lanes, 62 rejects, 44 boundaries, 7 mutants |
| `wasm-trust` | PASS: 3 entries, 0 proof holes |
| `fields-trust` | PASS: 4 entries, 0 proof holes |
| `structural-trust` | PASS: 2 entries, 0 proof holes |
| `owned-store` | PASS: 3,532 cases in 2 lanes, 15 literal witnesses, 6 mutants |
| `flat-store` | PASS in each of 2 lanes: 13,621 observations, 3,534 instances, 2 installed-boundary states, 7 lifecycle checks; 9 mutants |
| `recursion` | PASS: 19 fixtures, 3 mutants |
| `fields-wasm` | PASS: 8 fixtures, 30 boundaries, 4 mutants |
| `census` | PASS: 33 files, 576 declarations, 41 classes |
| `perch-context` | PASS: 33 fixtures, 8 mutants |
| `lint:verify` | PASS: 168 tests, 8 law rules |
| `bootstrap` | PASS: 921 corpus files, 8 stages, 2 reached, 54 mutants |
| `classification` | PASS: 17 fixtures, 6 mutants |
| `nest` | PASS within stated scope: 40 seed fixtures, 174 seed calls, 38/40 frozen outcomes, 2 unmet, 76 check observations, 25 accepted books, 386 evaluator and 386 Wasm values, 78 rejection observations, 24 boundaries, 100 enum hashes, 6 mutants / 12 kills |
| `nest-review` | PASS: 29 seed fixtures, 49 seed calls, 58 check observations, 15 accepted books, 98 evaluator and 98 Wasm values, 112 rejection observations, 7 mutants / 14 kills; fuzz 3,000 programs, 0 false acceptances, 0 false Invalid, 242 evaluator values |
| `io-host` | PASS: 40 seed fixtures, 109 seed runs, 86 conformance runs, 6 CLI runs, 22 host boundaries, 6 mutants |
| `io-abi-2` | PASS: 43 fixtures, 21 read, 64 reference and 61 seed observations, 153 parity checks, 5/5 mutants killed |
| `selfhost` | PASS: 65 cases, 2 passed, 63 blocked, 5 reviewed D4 gaps, 3 mutants, 20 judge mutants |
| `nest-round3` | PASS: 61 seed fixtures (20 dotted-binder, 25 empty-binding, 16 line-broken-header), 82 seed calls, 122 check observations, 32 accepted books, 164 evaluator and 164 Wasm values, 232 rejection observations, 11 mutants / 22 kills |

`npm run -s gates:verify` passes 18 tests. Receipt drift against the tracked
shared receipts is 64 identical, 9 volatile-only and 18 semantic. The semantic
drift is expected: rebuilt compiler hashes, earlier nest rounds' accepted
multi-column forms in the checker and frontend downstream observations, and one
selfhost twin. `layout-braces-comma` now meets its reject requirement at the
seed's location (12:11) because pattern headers join lines. Only the nest-owned
receipts are refreshed here (`nest.json`, `review.json`, `round3.json`, and the
normalized summary [round3-all-gates.json.gz](round3-all-gates.json.gz)); the
coordinator owns the shared ones.

## Perch preflight (offline, 0 provider requests)

- The 19 changed or added declarations, with `--task=tests/compiler-nest/SPEC.md`:
  0 truncated contexts, 0 supporting-role limits. Composition is unavailable:
  56,501 bytes against 48,000, with 24 collaborators outside the selection.
  Exit 3.
- The nine changed files: 233 declarations, 26 truncated contexts (6
  caller/byte, 5 file-limit, 15 helper-limit), 26 supporting-role limits.
  Composition is unavailable at 126,096 bytes. Exit 3.

Compression, Delight, Memetic identity, Anticipation and Payoff are
**unrated**. Live review belongs to the coordinator.

## Remaining limits

- A line break inside a call's or constructor's argument list in a body (not a
  header) is still `Invalid parse expected-term`. The seed accepts it. This is
  the selfhost suite's reviewed `layout` D4 gap; it predates nest and belongs to
  that need's owner.
- `rec-swapped-args` and `rec-alias` still report Unsupported against unchanged
  Invalid expectations; `descent-2` owns their decreasing-call rule.
- A new source match on a residual binding reports
  `Unsupported check default-scrutinee`.
- The two general lowering laws remain unmet.

Evidence: [round3.json](round3.json), [round3-preflight.txt](round3-preflight.txt).
