# Nest review round 10

This round answers review round 1 of the second review cycle (the reviewer's
`sem10`). All five findings are addressed: the blocking one and three of the
major ones are **fixed**, and the fourth major one (main-era whitespace gaps) is
fixed for all seven of its shapes, with the limits listed under Open.

| Finding | Disposition |
|---|---|
| 1 (blocking): a `+` detached from its binder between row columns is Checked | **Fixed.** `a + b`, `a+ b` and a line break before `+ b` end the row: `Invalid parse expected-:` |
| 2 (major): the nest gates ignore `KNOT_GATE_TIMEOUT_SCALE` | **Fixed** in `check.py`, `regen.py` and `typekind.py`, with a runner self-test |
| 3 (major): main-era whitespace gaps, newly Invalid in multi-scrutinee matches | **Fixed** for all seven shapes, flat and multi: `Unsupported` (46 fixtures, 13 mutants). Open: other layout variants of the same cause, of which the reviewer's edit grids still hold 71 that this branch introduced and 454 that main already had (see Open) |
| 4 (major): a `+`/`-` let marker apart from its name after another statement | **Fixed.** `Invalid parse detached-marker`; a marker first in a body stays spaced |
| 5 (major): a split return arrow `- >` is accepted | **Fixed.** `Invalid parse function-result` |

| Commit | Change |
|---|---|
| `8cd782a0` | Finding 2: the harness timeouts scale; `HarnessTimeoutTests` in the runner self-test |
| `c22f4759` | D7 freeze for findings 1, 4 and 5: 103 seed-derived fixtures and 343 seed calls (a replay without `--write` reports no differences) |
| `02bbbbc5` | Finding 1: `S.marks`, `promotes` at both row-continuation sites, `marks_witness` and `detached_plus`, census approval |
| `2dc95a63` | Finding 4: `BodyAt` gains `first`; `detached_marker` and `first_marker` |
| `6a2422f7` | Finding 5: the arrow needs `S.touches`; `split_arrow`, `return_type_application` restated |
| `05f286f6` | The `nest-round10` gate (registered, self-test name, GATES.md, counts) and the fuzz extension |
| `80655733` | D7 freeze for finding 3: 35 more fixtures (138 in all, 560 seed calls) |
| `6da0ad7f` | Finding 3, first form: the stopgaps at ListTail, `binder_failure`, `expect_line` and `term_failure` |
| `fea8f8c1` | Finding 3: the let's line-break test moves into one helper, `assign`; `term_failure` is unchanged; the round-6 `touch-past-one` mutant outcome; census refresh |
| `c06747cb` | D7 freeze for the last two repairs and three probes the first freeze missed: 152 fixtures, 624 seed calls |
| `987778f4` | Finding 3, seventh shape (`StartBody`); `-+u = x` stays Invalid (`binder_failure` gains `promoted`) |
| `b614b580` | The runner allows 1,800 s per gate |
| Final commit | This report, the round-10 receipt, falsification, preflight and law-review records, the final-tree gate run, the reviewer probe-root scan, the Perch log entry and the campaign state |

Commit trailers read `Co-Authored-By: Claude Sonnet 5.5`, which is the running
model according to the harness; the task text named `Claude Opus 5.5`, as it did in
round 9. History is left as committed.

## Items for coordinator sign-off

- **One mutant outcome of an earlier round changed.** `nest-round6`'s
  `touch-past-one` shifts `S.touches` by one offset. `touches` now also decides a
  return arrow's `->` (finding 5), so the shifted checker rejects every def header
  with `Invalid parse function-result` before it reaches the brace witness. It is
  still killed in both lanes; only the diagnostic it must produce changed (`round6.py`).
  Round 6 therefore no longer exercises an off-by-one in the brace rule on its own.
  No anchor, fixture or language assertion changed. Three round-9 mutants
  (`rebound-pattern-invalid`, `rebound-promotion-invalid`, `rebound-let-invalid`)
  name the new text of the `binder_failure` calls in `round9.py`; their `new` text
  and observed outcomes are unchanged.
- **The runner's per-gate limit is 1,800 s** (`scripts/gates/run.py`, GATES.md),
  from 900. The final full run took 1,552.9 s under a load of 27 to 77 on 18 cores,
  and `nest-round10` alone took 723.8 s (about 4 minutes unloaded): it rebuilds the
  lanes and 22 mutants. The inner harness guards still scale with the variable.
- **No law covers the finding-3 stopgaps.** The frontend-laws group composes from
  its five files and stands at 47,916 of 48,000 bytes (43,781 before the round), so
  the five new laws and the restated one are ground witnesses, not position-quantified like
  `touching_brace`, and the five stopgap sites have fixtures and mutants only. The
  modules round must restate four dotted-binder laws in `src/LAWS.bend` and will not
  fit; a parser-law file with its own manifest group is the way out.
- **The Arms-site use of `promotes` cannot be killed by a mutant.** Arms and RowTail
  test the same predicate, and RowTail re-tests it, so a lax Arms reaches the same
  colon expectation. The finding asked for the rule at both sites, and both apply it;
  the gate kills the helper and the RowTail site.
- **Statement corrections.** `c22f4759`'s message says the 42 + 12 + 6 rejected
  programs are all Checked except `a ++b`; 57 of the 60 are Checked, and three
  report another code (`a ++b`: `pattern-binder`; the line-break marker:
  `binding-name`; the split arrow before a type application: `type-application`).
  `6da0ad7f` says no tracked file changes outcome over 794 files; that count is of the
  files that existed before the 35 finding-3 fixtures frozen in `80655733`, whose 25
  seed-accepted programs change from Invalid to Unsupported as frozen (of the 794
  earlier files, 0 change). `fea8f8c1` says the same eight mutants as before; ten
  mutants cover the stopgaps after it, five with their earlier anchors, four
  re-anchored and one new. `c06747cb` says its three gaps came from an "advisor-style
  review": they came from a consultation of the review tool during the round (the
  arm-body layout and `-+u` gaps) and from the reviewer's own finding 1 (the `+y +# c`
  row).

## Finding 1 (blocking): a detached `+` between row columns

**Fixed.**

### The seed's rule

The seed reads a `+` or `-` after a term as an infix operator unless the character
right after it starts a name (`parse_term_ops`, `bend2/bend.ts` around line 2033:
`(op === "-" || op === "+") && (nx === ">" || char_is_head(nx))` returns the term).
A row's patterns are terms: `a + b`, `a+ b` and `a` then a line break and `+ b` are
one operator term, so a two-scrutinee row has one pattern and is rejected ("2
patterns (one per scrutinee)"); `a +b` and `a+b` open the next column. A `+` that
starts a row or follows a comma is not after a term and is a promotion, spaced or
not, and so is one inside fields after a comma. Knot's `Arms` and `RowTail` continued
a row at any `+` token, whatever its spacing.

### The repair

One rule, stated once. `S.marks(t, next)` holds when `next` is a name touching `t`
(the offset comparison `touches` already uses for a constructor's brace, plus the
name test). `promotes(ts)` holds for a `+` that marks the next token, and replaces
`starts(...,"+")` at both continuation sites. A `+` that does not mark ends the row,
so the ordinary colon expectation reports `Invalid parse expected-:` at the `+`.

### Evidence

- **Frozen fixtures (D7), `c22f4759` and `c06747cb`.** 45 seed-rejected rows and 22
  seed-accepted controls. The rejected: the reviewer's row-token grid (three
  separators ` + `, `+ ` and a line break then `+ `; five left and two right
  patterns; 30), her plus grid (`a + b`, `a+ b`, a constructor, a wildcard, a line
  break, three columns with the detached `+` in the middle, last and both, `a ++b`;
  10), the two-column repro and its fielded variant `case Pr{l, r} + d`, and three
  rows with a `+` before a comment or a line break (`+y +# c` then `v`). The
  controls: a glued `+b`, `a+b`, `F0{}+b`, a promotion that starts a row (`+ a b`,
  `+ v _`, flat `+ v`), follows a comma (`a, + b`, `a,+ b`) or sits inside fields
  (`Pr{a, + b}`, `Pr{l, + r} d`), and a line break before a glued `+b`. Before the
  repair 44 of the 45 are Checked (`a ++b` reported `pattern-binder`); after it all 67
  hold in both lanes, the 22 accepted books agree with the seed, the evaluator and
  Wasm, and every rejected program is rejected in check, evaluation and both compile
  profiles with its artifact preserved.
- **Fuzz (`fuzz.py`).** The atoms gain a spaced promotion `+ v`; multi-column rows
  draw ` + `, `+ ` and a line break then `+ ` as separators (1 in 40); the let terms
  gain a marker after a let (`- w =`, `-w =`, `+ w =`) and a spaced first marker.
  Against the pre-repair checker (`5ef36ae6`) the fixed-seed run reports **68 false
  acceptances**, 0 false Invalid; with the repairs **0 and 0**. The seed reports 221
  Accepted and 2,779 Invalid; Knot reports 221, 2,461 and 318 Unsupported (the dotted
  and repeated-promotion atoms); 221 values are evaluated (`nest-review`).
- **Reviewer's row grids**, on the final tree. `rowtokgrid` (840 programs): 30 seed-rejected
  Checked before, 0 after. `plusgrid`: nine flagged before, none after.
- **Edit grids** (`editgrid`, `editgrid2`, `editgrid3`, about 37,800 one-character
  variants of the reviewer's canonical programs; `layoutgrid` 575 and `letgrid` 483
  programs): 14 seed-rejected Checked programs on `5ef36ae6` (the three classes of
  this round), **0 on the repaired checker**, and no seed-accepted program becomes
  Invalid that was not before.
- **Reviewer probe roots** (`round10-probescan.json`). The seed, the `5ef36ae6` checker and the
  repaired one ran on every program without an import line under the reviewer's probe roots
  (`sem10-out` except the grids above, `sem10-probes`, `sem10-repro`): 40,642 programs. 426 change
  outcome. **Before the repairs 58 seed-rejected programs are Checked and 216 seed-accepted programs
  that change are Invalid; after them, 0 and 0.** The 58 become Invalid (`expected-:` 35,
  `function-result` 17, `detached-marker` 6); the 216 become Unsupported (`body-indentation` 189,
  `argument-separator` 14, `pattern-binder` 6, `binding-name` 3, `expected-term` 2, `expected-=` 2). The
  stopgaps also answer Unsupported for 123 seed-rejected programs (`body-indentation` 98,
  `argument-whitespace` 18, `repeated-promotion` 7), which the seed rejects for another reason as well:
  each stops at its first whitespace deviation before the parser sees the rest, so they lose precision, not
  soundness. The remaining changes are code changes among Invalid rejections (for example `a ++b` from
  `pattern-binder` to `expected-:`).
- **Laws.** `marks_witness` pins the predicate (a glued name, a space, a line break)
  and `detached_plus` states the row rule at RowTail; both have `{==}` proofs. See
  `LAW_REVIEW.md` (round 10) for the limits.
- **Mutants.** `nest-round10` kills, for this finding, `ignore-plus-gap` (the required
  one: `promotes` ignores the gap; witness `rowplus-second-spaced`),
  `ignore-plus-gap-later-column` (RowTail alone; `rowplus-three-cols-last`),
  `touch-leading-promotion` (a promotion that starts a row must stay spaced;
  `rowplus-first-spaced`) and, shared with finding 4, `mark-a-line-break`.

## Finding 4 (major, pre-existing): a let marker apart from its name

**Fixed.**

The same operator loop reads a let's value: after `v : F = x` the next line's
`+ u : F = ..` continues the value as `x + u`, and the statement would then start at
`:` or `=`. A marker first in a body follows no value and may be spaced; so may a
marker in a parameter list. Knot took `+` or `-` as a let at any line start.

`BodyAt` gains a `first` field: true from `StartBody` (the first statement of a def or
arm body), false from `BindingTail` (every later statement). Where a later statement
starts with `+` or `-`, the marker must satisfy `S.marks` (a name touching it) or
`BodyAt` reports `Invalid parse detached-marker` at the marker. This covers a marker
followed by a line break, which the seed reads as an operator too. A misaligned
statement still reports `body-indentation` first.

- **Frozen fixtures:** 12 seed-rejected (the reviewer's `+ u : F = ..`, `+ u = v`,
  `- u : F = ..`, `- u = v`, `+` then a line break, an arm body, a third statement, a
  call value and a constructor value; the erased marker before `+ u`) and 17
  seed-accepted controls (spaced first markers typed and untyped, `+  u`, in an arm, in
  a parameter list; glued markers after a let).
- **Laws:** `detached_marker`, `first_marker`.
- **Mutants:** `ignore-marker-gap`, `every-statement-first` (the flag at BindingTail),
  `touch-first-marker`.

## Finding 5 (major, pre-existing): a split return arrow

**Fixed.** `FunctionTail` matched `-` and `>` as separate tokens with no adjacency
check, so `def id(a: F) - > F:` was Checked, compiled and run; the seed rejects it. The
arrow now needs `S.touches(dash, arrow)`; a split arrow falls to the ordinary
malformed-result rule, `Invalid parse function-result`, before the type is read (`- >
List<F>` used to reach `type-application`).

- **Frozen fixtures:** 6 seed-rejected (`- >`, two and three spaces, in `main`, without
  parameters, before a type application) and 4 controls (`->` with a space before,
  after, or neither).
- **Laws:** `split_arrow`; `return_type_application` restated with the arrow's tokens
  at touching offsets.
- **Mutants:** `ignore-arrow-gap`, `touch-arrow-type` (`-> F` with a space stays
  accepted).

## Finding 2 (major): the nest gates ignored the timeout scale

**Fixed.** `check.py` reads `KNOT_GATE_TIMEOUT_SCALE` once (as its ten older siblings
do) and multiplies `run`'s 120 s default; `regen.py`'s 60 s and `typekind.py`'s two 240 s
guards follow. Every other nest script calls `gate.run`. The runner sets the variable to
4 unless the caller sets it. `HarnessTimeoutTests` in `scripts/gates/test_runner.py`
imports `check` and `regen` at scales 1 and 1000 and requires 120/60 and 120000/60000;
`npm run gates:verify` now runs 20 tests. The optional suggestion to share the lane builds
is not taken; the runner's per-gate limit is raised instead (see sign-off).

## Finding 3 (major): main-era whitespace gaps, newly Invalid in multi-scrutinee matches

**Fixed for all seven shapes, in the flat and the multi-scrutinee context.** The seed
reads whitespace where Knot ends a term, takes a comma, or lays a body out. Each site now
reports `Unsupported` when the seed reads what follows as a continuation, and keeps
`Invalid` where it cannot (the seed rejects those too). No tracked file outside the
round-10 fixtures changes outcome (see the scan).

| Shape (seed-accepted) | Before | Now | Site | Mutants |
|---|---|---|---|---|
| Arguments separated by whitespace, `two(a b)`, `Pr{a b}` | Invalid `argument-separator` | Unsupported `argument-whitespace` | `ListTail`: a name, or in a pattern a marking `+`, after an argument | `argument-whitespace-invalid`, `promoted-call-argument` (a promotion is no call argument) |
| Repeated promotion, `case ++y`, `+ +y`, `+++y`, `++u = x` | Invalid `pattern-binder`, `binding-name` | Unsupported `repeated-promotion` | `binder_failure`, with `promoted` (an erased marker wants a name: `-+u = x` stays Invalid) | `repeated-promotion-invalid`, `erased-repeated-promotion` |
| An arm body on the line after its `case`, at the case's column or below | Invalid `body-indentation` | Unsupported `body-indentation` | `StartBody`, for a body that starts with a name and a parent above 0 | `arm-body-layout-invalid`, `body-layout-any-token` (an empty arm stays Invalid) |
| A let split before its `=` (typed, or a marker's untyped) | Invalid `expected-=` | Unsupported `line-break` | `assign`, at `AnnotatedBinding` and `BindingStart` | `equals-line-break-invalid`, `typed-equals-line-break-invalid`, `marker-equals-line-break-invalid`, `line-break-before-any-token` |
| A let split after its `=` | Invalid `expected-term` | Unsupported `line-break` | `assign` | `value-line-break-invalid`, `line-break-before-any-name` |
| A marker split from its name, `+` then `w : F = x` | Invalid `binding-name` | Unsupported `line-break` | `binder_failure` | `marker-line-break-invalid`, `line-break-before-any-name` |

- **Frozen fixtures** (`80655733`, `c06747cb`): 46, from the reviewer's probes verbatim
  in both contexts plus variants: 8 whitespace arguments and 4 seed-rejected controls
  (`two(a = b)`, `two(a + b)`, `Pr{a + b}`, a promotion as a call argument); 7 repeated
  promotions and the `-+u` control; 10 split lets and 2 controls (nothing that continues
  the let after the break); 7 arm bodies and 2 controls (an empty arm, a `def` after the
  colon); 5 already-Unsupported forms in a multi-scrutinee row (destructuring let,
  generic parameter, `~` header, a nested match at the case column).
- **Laws:** none, for the reason under sign-off.
- **Main versus nest.** In the flat context all seven shapes were already Invalid on
  main. In a multi-scrutinee match main stopped at `Unsupported match-scrutinees`, and
  the branch's parse through it made them Invalid: a regression this branch introduced,
  like round 9's finding 2. They are Unsupported now in both.

### Open

All of these are seed-accepted programs that Knot still reports Invalid. The reviewer's edit
grids count 525 of them after the round (986 before it); the set after is contained in the
set before, so none is new. **454 are main-era gaps** (the checker of the merge base
`43a394a4` reports them Invalid too) and **71 were introduced by this branch**: main stopped
at `Unsupported parse match-scrutinees`, and the branch parses through the multi-scrutinee
match to a layout rule stricter than the seed's, the same regression as finding 3. The 71
are all layout, in the `lets` and `empty` programs:

| Family (seed-accepted, Knot Invalid) | Programs | Code |
|---|---|---|
| A later statement at a column other than the first statement's | 27 | `body-indentation` |
| A body that starts with `+` or `-` at or below the case column | 13 | `body-indentation` |
| A body's first token at another column (`match` after a def header) | 1 | `body-indentation` |
| A `case` at or left of its `match` column | 20 | `top-level-indentation` |
| A let split before its `:` (`+u` then ` : F = ..`, or `w` then ` : F = ..`) | 10 | `expected-=` 8, `top-level-indentation` 2 |

What would close them. The seed checks no column for a statement, so a later statement that
starts with a name, `+`, `-` or `match` at another column could report `Unsupported
body-indentation` in `BodyAt`'s column check (the 27), and `StartBody`'s name test could widen to
the same predicate (the 14). That predicate and its two uses cost about 240 bytes, and
`frontend-laws` has 84 left (see sign-off), so both wait for a parser-law file. A `case` at the
match column needs `Arms` to take the seed's rule (the first arm may sit at the match's column),
and a let split before its `:` needs one more line-break site in `BindingStart`; neither is a
stopgap that fits.

The 454 main-era gaps, unchanged by the round:

- **A def body at column 0** (`def main() -> Flag:` then `On{}` at the margin). The frontend
  gate pins `Invalid parse body-indentation` for it (`tests/subsets/check_frontend.py`, case
  `indent`), though the seed accepts it, so it cannot move without amending that assertion.
  `StartBody` leaves parent 0 alone.
- **Other layout**: nested-match arm bodies and statements at other columns (`body-indentation`
  69), a `case` at the match column or a top-level line at another column
  (`top-level-indentation` 94), a let split before its `:` (`expected-=` 8).
- **A def header's parameters and a type's fields with whitespace or line breaks** (the
  selfhost `layout` need; `argument-separator` 30, `parameter` 95, `declaration-name` 48,
  `expected-is` 16, `{` 14, `(` 12, `:` 8) and a function type as a def's result
  (`function-result` 60, the closures increment).

## The mutants

Each mutant is one replacement in a copy of `src/`; the gate kills it in both lanes. The table shows what it does
on the 152 frozen fixtures ("wrong" = fixtures whose reviewed outcome changes) and on the 3,000-program fuzz generator
(the unmutated checker: 0 wrong fixtures, 0 false acceptances, 0 false Invalid; Knot 221 Accepted, 2,461 Invalid, 318 Unsupported).

| Mutant | Witness | Wrong fixtures | Fuzz | Note |
|---|---|---|---|---|
| `ignore-plus-gap` | rowplus-second-spaced | 46 | 12 false acceptances | Restores the finding exactly (the required mutant) |
| `ignore-plus-gap-later-column` | rowplus-three-cols-last | 1 | no change | RowTail alone |
| `mark-a-line-break` | marker-plus-newline | 2 | no change | A marker before a line break; also the finding-4 line-break form |
| `touch-leading-promotion` | rowplus-first-spaced | 13 | 752 Unsupported (318 unmutated) | Over-rejects a promotion that starts a row |
| `ignore-marker-gap` | marker-repro | 12 | 52 false acceptances | Restores finding 4 |
| `every-statement-first` | marker-third-statement | 12 | 52 false acceptances | The `first` flag at BindingTail |
| `touch-first-marker` | marker-first-plus-spaced-typed | 15 | 21 false Invalid | Over-rejects a spaced first marker |
| `ignore-arrow-gap` | arrow-repro | 6 | no change | Restores finding 5 (the fuzz never splits an arrow) |
| `touch-arrow-type` | arrow-glued | 146 | 221 false Invalid | Over-rejects `-> F` (every def header) |
| `argument-whitespace-invalid` | argspace-call-flat | 8 | no change | Finding 3 |
| `repeated-promotion-invalid` | plusplus-flat | 7 | no change | Finding 3 |
| `marker-line-break-invalid` | letsplit-marker-flat | 4 | no change | Finding 3 |
| `value-line-break-invalid` | letsplit-after-eq-flat | 3 | no change | Finding 3 |
| `equals-line-break-invalid` | letsplit-before-eq-flat | 3 | no change | Finding 3 (the branch of `assign`) |
| `typed-equals-line-break-invalid` | letsplit-before-eq-flat | 4 | no change | Finding 3 (the typed call site) |
| `marker-equals-line-break-invalid` | letsplit-before-eq-marker | 2 | no change | Finding 3 (the marker call site) |
| `promoted-call-argument` | argspace-promoted-call | 1 | no change | Precision: a promotion is no call argument |
| `line-break-before-any-name` | letsplit-after-eq-junk | 1 | no change | Precision: a break with no name after it |
| `line-break-before-any-token` | letsplit-before-eq-junk | 1 | no change | Precision: a break with no `=` after it |
| `erased-repeated-promotion` | plusplus-erased-let | 1 | no change | Precision: `-+u = x` is no promotion of a promotion |
| `arm-body-layout-invalid` | bodycol-arm-flat | 7 | no change | Finding 3 |
| `body-layout-any-token` | bodycol-empty-arm | 2 | no change | Precision: an empty arm |

## Gates

`BEND_NO_TELEMETRY=1 npm run -s gates` exited 0 with **29/29 gates passed** on `b614b580`
(`run-wj36u5t9`, 1,552.9 s, 4 workers, load average 27 to 77 from other sessions;
`round10-final-gates.json.gz`). The tip differs from that tree only in files no gate reads:
this report, `round10.json` and its siblings, `round10-final-gates.json.gz`,
`round10-probescan.json`, `round10-falsification.txt`, `round10-preflight.txt`,
`LAW_REVIEW.md`, the Perch review log and the campaign `state.json`. `census --check`,
`perch-context` and `gates:verify` (20 tests) were rerun on the tip and passed. Receipts: 65
identical, 25 semantic and 9 volatile-only. All eight `src/*PROOF.bend` entries print `All
terms check.`

| Gate | Counts |
|---|---|
| `nest-round10` (new) | 152 fixtures, 624 seed calls, 43 accepted books, 304 check observations, 686 evaluator and 686 Wasm values, 872 rejection observations, 22 mutants / 44 kills |
| `nest-review` | fuzz 3,000 programs (now with spaced `+` and markers), 221 evaluated values, 0 false acceptances, 0 false Invalid |
| `nest-round3`, `nest-round6` | 61 and 35 fixtures, 11 and 5 mutants / 22 and 10 kills (`touch-past-one` reports the arrow diagnostic) |
| `nest` | 38/40 frozen outcomes, 2 unmet, 6 mutants / 12 kills, 100 enum hashes |
| `nest-round4`, `nest-round7`, `nest-round8`, `nest-round9` | unchanged: 14, 35, 37 and 80 fixtures |
| `selfhost` | 65 cases, 2 pass and 63 blocked, **1 D4 gap** (as at round 9), 20 judge mutants, 3 source mutants |
| `frontend`, `classification` | 14 fixtures, 28 lane observations, 24 boundaries, 4 mutants; 17 fixtures, 6 mutants (the `indent` pin is unchanged) |
| `census` | 35 files, 747 declarations, 41 classes |
| `bootstrap` | corpus 1,276, 8 stages, 2 reached, 54 mutants |
| `perch-context` | 33 controls, 8 mutants; 20 groups, 0 blockers |
| `lint:verify` | 168 tests, 8 law rules |

Every other gate's counts equal the earlier runs: `checker`, `structural`, `fields`, `wasm`,
the three trust inventories, `owned-store`, `flat-store`, `recursion`, `fields-wasm`,
`io-host` and `io-abi-2`.

The first full run of the round did not pass. It failed on `census` (the accepted inventory
records every registered gate script's hash, and `round10.py` had changed after the last
regeneration), on `nest-round3` (the first form of the let line-break stopgap sat in
`term_failure`, which every parse failure reaches, and moved the observed outcome of two
round-3 mutants; it now lives in `assign`) and on `nest-round6` (`touch-past-one`, above). No
other gate failed in any run.

The regenerated receipts of the earlier nest gates and the shared receipts of the existing
gates are **left for the coordinator's refresh**; `round10.json` is refreshed from a direct
run on `987778f4`, whose inputs match the tree (209 hashes).

## Style preflight

`round10-preflight.txt` records the offline preflight (0 provider requests). The new
mechanisms (`promotes`, `broken`, `assign`, `binder_failure`, `marks`) and the six laws have
complete contexts (0 truncated, 0 role-limited). The four changed Bend files together (131
declarations) exit 3 as in round 9: 7 contexts are truncated against 5 at `5ef36ae6`, the same
five types and helpers plus two laws that call `P.run`, which crossed the helper limit as `run`
grew. Those are limits of a whole-file selection: the `frontend-laws` group and the whole
compiler manifest exit 0 (20 groups, every composition available, 0 truncated, 0 role-limited,
0 structural blockers). Headroom is gone: `frontend-laws` composes to 47,916 of 48,000 bytes and
`tests/compiler-nest/SPEC.md` (14,727 bytes, the task of the matrix groups) has about 50 bytes
under its context bound. The manifest's task for the frontend groups, `src/SPEC.md`, is past the
16,000-byte style task limit, as it was before this round.

## Remaining for the coordinator

- Live Perch review of the new declarations (`promotes`, `broken`, `assign`, `marks`, the
  changed `binder_failure` and `run` arms and the six laws), with
  `--task=tests/compiler-nest/SPEC.md`.
- Refresh the receipts after merge (the earlier nest gates, whose input hashes moved,
  `selfhost` and the shared receipts). Sign off on the `touch-past-one` outcome and the
  runner limit.
- A parser-law file and manifest group, before the modules round restates the dotted laws,
  and laws for the finding-3 stopgaps.
- The open D4 families above: the 71 branch-introduced layout cases (a statement-column and
  marker-body stopgap once the parser-law file exists, `case` at the match column, a let
  split before its `:`), the def-body pin (an amendment to the frontend gate), and the
  def-header and type-field layout need.
- The modules round's scope-aware dotted-binder rule (`REVIEW-9.md`), unchanged.
- Both D21 laws are unchanged and remain required open obligations.
