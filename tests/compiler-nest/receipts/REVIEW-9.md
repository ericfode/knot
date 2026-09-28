# Nest review round 9

This round answers review round 2 of the Claude executor. Both confirmed findings
and the optional third are **fixed**:

- **Blocking.** An unannotated let of a binder that a positive branch had refined
  to a constructor was Checked, flat and in a matrix. The seed rejects it ("an
  annotated term (cannot infer)"). The flat form was already on main. `expected`
  now rejects a checked constructor term when no annotation gives its type.
- **Major (D4 regression).** Commit `2ae8dca3` rejected every dotted binder as
  Invalid, but the seed accepts one that rebinds a name in scope. On the
  coordinator's stopgap decision, every dotted binder is now `Unsupported parse
  dotted-binder`, never Invalid. The ten round-3 dot-* expectations were amended
  in one commit.
- **Optional (main-era D4 gaps).** The seven `sem-r7-probes/hd` programs (b1 to
  b5, h15, h25) were Invalid parse; all seven are `Unsupported` now. The change
  is confined to a body's call and constructor arguments and a same-line arm.
  The same cause in a def header's parameters and a type's fields stays **open**
  (see the third finding).

| Commit | Change |
|---|---|
| `93579bb` | Merge of main `cd7ff10`; conflicts only in generated or state files |
| `afcb9f3` | D7 freeze before the first repair: 65 seed-derived fixtures under `round9-fixtures/`, `round9-expectations.json` and `round9_seed.py` (93 seed calls; a replay without `--write` reports no differences) |
| `7399ffd` | Finding 1: `expected`, eight laws with `{==}` proofs, SPEC text and census approval (summary in the commit message) |
| `dac1440` | D7 freeze for finding 2: eight rebound dotted-binder fixtures (the modules review's three verbatim), 73 fixtures and 101 seed calls in all |
| `07d8fd3` | The single amendment commit: the ten round-3 dot-* expectations from Invalid to `Unsupported parse dotted-binder`, with the seed outputs. It changes only the `knot` blocks of `round3-expectations.json` and the table in `round3_seed.py` |
| `635702a` | Finding 2: `binder_failure` in the parser, five laws, the erased-let mutant's observed outcome, census approval |
| `7901a46` | The `nest-round9` gate (registered, self-test, GATES.md, counts), nine mutants, `fuzz.py` lets of matched binders, SPEC and CONTRACT text |
| `d6fc90d` | D7 freeze for the optional finding: the seven probes verbatim and four declaration-list programs |
| `87c29c6` | Line-break classification, first form: every bracketed list |
| `e7a9d7e` | The same, confined to a body's arguments and a same-line arm (see the third finding for why) |
| `4378081` | Round-9 receipt, falsification record, preflight record, law review and Perch log entry |
| `d53c8e5` | Merge of main `43a394a` (a docs-only commit) |
| Final commit | This report, the probe-root scans (`round9-probescan.json`) and the final-tree gate run (`round9-final-gates.json.gz`) |

Commit trailers read `Co-Authored-By: Claude Sonnet 5.5`, which is the running
model according to the harness. The task text named `Claude Opus 5.5`, and the
round-8 commits carry that trailer. History is left as committed.

## Two items for coordinator sign-off

- **Two existing round-3 mutant outcomes changed.** Both mutants are still
  killed in both lanes, and no anchor, fixture, or language assertion changed.
  Only the wrong observation each mutant is required to produce follows its
  code path.
  - `erased-let-as-pattern`: `Invalid parse binding-name` became `Unsupported
    parse dotted-binder`. This follows from the stopgap you authorized.
  - `header-past-colon`: `Invalid parse end-of-body` became `Unsupported parse
    same-line-arm`. This follows from the optional third finding. Its mutated
    parser leaves a `case` after a body.
- **The line-break work is separable.** `d6fc90d`, `87c29c6` and `e7a9d7e` form
  a self-contained trio. Reverting them, newest first, drops the optional
  finding, and the round-9 receipt then needs `gates:refresh` (80 fixtures fall
  to 73, 12 mutants to 9).

## Finding 1 (blocking): a let of a refined binder was accepted

**Fixed.**

### The seed's rule

In a positive branch the seed substitutes a matched binder by its rebuilt
constructor term. A let infers its value's type, and `term_infer` has no rule for
a constructor: its `default` case (`infer-err`, `bend2/bend.ts` line 3358) throws
"an annotated term (cannot infer)". Knot already reported `annotation-required`
for a literal constructor. A refined binder reached `expected` as an ordinary
checked term: a `Value` from `occurrence` on the flat path, and the rebuilt
`Construct` on the matrix path.

### The repair

One idea covers every case: **a constructor term has no inferred type.**
`check.bend::expected` gains two rows. With no annotation, a checked `Value` or
`Construct` is `Invalid check annotation-required`. A residual or default-row
binder checks to a `Reference`. A field never split and a later parameter have
no refinement, a call is an `Application`, and an annotated let takes the
checked branch. Aliases share their level's refinement, so a variable row, a
nested field level and an enclosing match need no other rule. The let's quantity
check runs after the value, so `+v = z` now reports `annotation-required`, as the
seed does.

### Evidence

- **Frozen fixtures (D7), `afcb9f3`.** 65 programs and 93 seed calls:
  - 47 seed-rejected programs, all "cannot infer": the reviewer's 11 sites in
    three let forms (`v =`, `+v =`, `-v =`; 33), the multi-scrutinee, default,
    nested, flat, flat-field and unused-let programs (6), and the eight
    generated hits q1040 to q2495 (8);
  - one literal control, already `Invalid annotation-required`;
  - 17 seed-accepted controls: the 11 annotated sites, an annotated let, a
    default-only binder (`wildrow`, typed `C3<> - A{}` by the seed), and four
    twins (a call on a rebuilt binder, a field never split, a later parameter,
    a nested field binder).

  On the `93579bb` checker: 43 false acceptances (the flat path too), 4
  rejections with the wrong code (`+v =` reached `reusable-type` first at the four
  nested sites) and all 18 other outcomes as reviewed. After the repair all 65
  hold in both lanes, the 18 accepted books agree with the seed, the evaluator
  and Wasm, and every rejected program is rejected in check, evaluation and both
  compile profiles with its artifact preserved.
- **Scan.** All 1,109 tracked `.bend` files, `93579bb` checker against `7399ffd`:
  only the 47 rejected fixtures change (43 Checked to Invalid, 4 `reusable-type`
  to `annotation-required`).
- **Fuzz (`fuzz.py`).** `body_terms` now draw lets of a scrutinee, a parameter
  and pattern binders, in three forms (`u = b`, `u : Flag = b`, `-u = b`); 2,289
  of the 3,000 programs contain one. The fixed-seed run against `93579bb`
  reports **36 false acceptances**, 0 false Invalid. With the repairs: 0 and 0.
  The seed reports 240 Accepted and 2,760 Invalid; Knot reports 240 Accepted,
  2,411 Invalid and 349 Unsupported (the dotted atoms); 240 values are
  evaluated (`nest-review`).
- **Reviewer's generator (`rt4`).** 11,534 programs (random bases 0, 100000 and
  200000) against the `7399ffd` checker report 0 unsound accepts, 0 D4 Invalid
  and 0 evaluator or Wasm mismatches; base 0 reported 8 before.
- **Laws.** In `src/check-LAWS.bend`: `refined_value_needs_annotation`,
  `refined_construct_needs_annotation`, `unrefined_binder_is_inferable` and
  `annotation_admits_constructor`. In `src/matrix-LAWS.bend`, four whole-checker
  witnesses: `refined_flat_let_witness` and `refined_matrix_let_witness` (rejected),
  `residual_let_witness` and `annotated_let_witness` (accepted). All eight
  `src/*PROOF.bend` entries print `All terms check.`
- **Mutants.** `nest-round9` kills six in both lanes:

  | Mutant | Witness | Outside the harness |
  |---|---|---|
  | `ignore-refinement` (the required one) | letm-multi | Restores the finding exactly: 47 wrong fixtures, 36 false acceptances |
  | `ignore-refined-value` | letm-flat | 29 wrong fixtures, 28 false acceptances |
  | `ignore-refined-constructor` | letm-flatfield | 18 wrong fixtures, 8 false acceptances |
  | `infer-annotated-let` | letx-flat-param-annot | Over-rejects: 9 wrong fixtures, 30 false Invalid |
  | `refine-residual-binder` | letm-wildrow | 1 wrong fixture, 7 false acceptances and 3 false Invalid |
  | `refine-unsplit-field` | twin-field-unsplit | Over-rejects: 27 wrong fixtures, 38 false Invalid |

## Finding 2 (major): rebound dotted binders were Invalid

**Fixed as a stopgap.** The parser does not resolve scopes, so it cannot tell a
rebound dotted binder (accepted by the seed) from an unbound one (rejected).

### The repair

`parse.bend::binder_failure` reports a name that cannot bind. An identifier that
cannot bind is a dotted one, and it is `Unsupported parse dotted-binder`. Any
other token keeps `Invalid` with its code. It serves the three sites that
reported Invalid: a pattern variable, a `+` promotion, and a let or typed let. An
erased let's dotted name is still a name, as in the seed.

### Evidence

- **Frozen fixtures, `dac1440`.** Eight programs: the modules review's three
  probes verbatim (`rebound-let`, `rebound-typed-let`, `rebound-field`), a `+`
  promotion, a variable row, a multi-column row and a nested field (all
  seed-accepted), and the erased-let control. On `7399ffd` the seven binder
  programs were `Invalid parse pattern-binder` or `binding-name`. Now each is
  `Unsupported parse dotted-binder` (exit 3), and the control is Checked.
- **The amendment, `07d8fd3`.** The ten seed-rejected round-3 dot-* fixtures
  (`dot-multi-column`, `dot-variable-row`, `dot-nested-field`, `dot-flat-field`,
  `dot-promotion`, `dot-anonymous`, `dot-constructor-name`, `dot-let`,
  `dot-let-reusable`, `dot-let-typed`) moved from Invalid to Unsupported. The five
  `name-*` lex fixtures stay `Invalid lex name`, and the five accepted controls
  are unchanged.
- **Scan.** All 1,117 tracked files, `7399ffd` against `635702a`: only those 17
  programs change, all Invalid to Unsupported.
- **Laws (`src/LAWS.bend`).** `dotted_pattern_binder` and `dotted_let_binder`
  state the Unsupported outcome, with their proofs filled. Three more: 
  `dotted_promotion_binder`, `dotted_typed_let_binder`, and
  `unnamed_binder_is_invalid` (a token that is no name stays `Invalid parse
  binding-name`).
- **Mutants.** Three, each reporting a rebound dotted binder as Invalid at one
  site: `rebound-pattern-invalid` (rebound-field; 4 wrong fixtures),
  `rebound-promotion-invalid` (rebound-promotion; 1) and `rebound-let-invalid`
  (rebound-let; 2).

**For the modules round.** Its scope-aware rule (`Invalid check dotted-binder`
when unbound, accepted when rebound) must flip the seven `rebound-*` fixtures to
Accepted, the ten round-3 dot-* fixtures to that check-phase Invalid, and restate
the four dotted laws.

## Finding 3 (optional): the seven main-era probes

**Fixed for the seven; the same gap in declaration lists stays open.**

### The cause and the repair

The seed reads a line break inside call or constructor arguments as whitespace,
and a second arm on the line of an arm's body as the next arm. Knot ends a term at
a line break. The parser now reports `Unsupported parse line-break` in `Arguments`
and in `ListTail` (arguments only), and `Unsupported parse same-line-arm` when
`case` follows a body on its line. Each site was Invalid before (`expected-term`,
`argument-separator`, `end-of-body`), so the change refines rejections only and no
accepting path moves.

The seven programs were `Invalid parse expected-term` (b1 to b4, h15),
`argument-separator` (b5) and `end-of-body` (h25). Now b1 to b5 and h15 are
`Unsupported parse line-break`, and h25 is `Unsupported parse same-line-arm`.

### Why the rule is confined

The first form (`87c29c6`) also stopped at a line break in a def header's
parameters and in a type's fields, which the seed accepts too. Measured against
the selfhost suite, it closed all five of that gate's reviewed `layout` D4 gaps.
That left four of the gate's twenty judge controls (`recoded-d4-gap`,
`displaced-d4-gap`, `gap-outlives-need`, `erased-d4-gaps`) without a gap to run
on: a coverage loss in a gate that another increment owns. The coordinator asked
for the seven body probes, so `e7a9d7e` confines the rule to them. On that tree
`tests/compiler-selfhost/check.py` passes with 1 blocked D4 gap
(`layout-def-header`) and all 20 judge mutants and 3 source mutants killed.

- **Scan.** All 1,124 tracked files, `635702a` against `e7a9d7e`: 14 programs
  change, all Invalid to Unsupported. They are the 7 round-9 probes and 7
  selfhost fixtures (`layout-braces`, `layout-call-args`,
  `layout-call-args-comma`, `layout-comments`, `layout-comments-swallowed`,
  `layout-dedent-close`, `layout-dedent-close-extra`). The selfhost receipt will
  drift for the coordinator's refresh.
- **Laws (`src/LAWS.bend`).** `line_break_in_arguments`, `line_break_after_element`,
  `same_line_arm`, and `body_ends_at_line_break`, which keeps a line break after a
  complete body ending it.
- **Mutants.** Three, each reporting a site as Invalid again:
  `list-break-invalid-in-arguments` (hd-b2), `list-break-invalid-after-element`
  (hd-b5) and `same-line-arm-invalid` (hd-h25).

### Still open (D4)

A def header's parameters and a type's fields with a line break, which the seed
accepts and Knot reports `Invalid parse parameter` or `argument-separator`. This
is the selfhost suite's `layout` need (`layout-def-header`, owner selfsource). The
four probes I froze and then removed:

```
def f(a: Flag,
      b: Flag) -> Flag:          # Invalid parse parameter
def f(a: Flag, b: Flag
     ) -> Flag:                  # Invalid parse argument-separator
type Pair is Type:
  P{l: Flag,
    r: Flag}                     # Invalid parse parameter
type Pair is Type:
  P{
    l: Flag, r: Flag}            # Invalid parse parameter
```

The same rule at `Parameters` and the parameter form of `ListTail` closes it,
and the round-9 gate mutant for it is `list-break-invalid-in-parameters` (see
`87c29c6`); it costs the four selfhost controls unless that gate learns another
gap to run them on.

## Reviewer probe roots

`round9-probescan.json`. The seed, the `93579bb` checker and the `e7a9d7e` checker
ran on every program without an import line under the reviewer's probe roots:
`sem9-probes` (6,961 programs: 3,442 seed-accepted, 3,517 rejected, 2 other) and
`sem-r7-probes` (10,289 programs: 5,105, 5,181 and 3). After the repairs **no
seed-rejected program is Checked and no seed-accepted program is Invalid** in
either root. Before them there were 43 false acceptances in `sem9-probes` and 7
false Invalid in `sem-r7-probes` (the hd probes).

Sixty-seven outcomes change. In `sem9-probes`, 43 seed-rejected programs go from
Checked to Invalid, and 2 from Unsupported to Invalid. In `sem-r7-probes`, the 7
seed-accepted hd probes go from Invalid to Unsupported, and 14 seed-rejected
programs (dotted binders and body line breaks) go from Invalid to Unsupported.
One slow blow-up probe crosses the 90-second harness timeout under the 8-way
load, from Checked to Timeout. The two checkers run the slow probes in the same
time when run alone (`blow7` 7.4 to 11.5 s, `w2x8` 4.3 to 6.9 s), so this is
harness noise, as in round 8.

## Gates

`BEND_NO_TELEMETRY=1 npm run -s gates` exited 0 with **28/28 gates passed** on
`d53c8e5`, the committed tree this report describes apart from this report and
the run summary (`run-464w94pj`, 954.1 s; `round9-final-gates.json.gz`). Receipts:
66 identical, 23 semantic and 9 volatile-only. `npm run -s gates:verify` passed
its 19 tests. All eight `src/*PROOF.bend` entries print `All terms check.`

| Gate | Counts |
|---|---|
| `nest-round9` (new) | 80 fixtures, 111 seed calls, 18 accepted books, 160 check observations, 188 evaluator and 188 Wasm values, 496 rejection observations, 12 mutants / 24 kills; findings: 47 let-of-refined-binder, 17 inferable-control, 8 dotted-binder-stopgap, 7 layout-stopgap, 1 literal-control |
| `nest-review` | fuzz 3,000 programs (now with lets), 240 evaluated values, 0 false acceptances, 0 false Invalid |
| `nest-round3` | 61 fixtures (the ten amended), 11 mutants / 22 kills |
| `nest` | 38/40 frozen outcomes, 2 unmet, 6 mutants / 12 kills, 100 enum hashes |
| `nest-round4`, `nest-round6`, `nest-round7`, `nest-round8` | unchanged: 14, 35, 35 and 37 fixtures; round 7 1,500 and round 8 3,000 generated programs with 0 false acceptances and 0 false Invalid |
| `selfhost` | 65 cases, 2 pass and 63 blocked, **1 D4 gap** (was 5), 20 judge mutants, 3 source mutants |
| `census` | 35 files, 733 declarations, 41 classes |
| `bootstrap` | corpus 1,124, 8 stages, 2 reached, 54 mutants |
| `perch-context` | 33 controls, 8 mutants; 20 groups, 0 blockers |

Every other gate's counts equal the earlier runs: `frontend`, `checker`,
`structural`, `fields`, `wasm`, the three trust inventories, `owned-store`,
`flat-store`, `recursion`, `fields-wasm`, `classification`, `io-host`,
`io-abi-2` and `lint:verify`.

Two earlier full runs did not pass. Run A, on the working tree before the last
census regeneration and the SPEC trim, failed on `census` (the CONTRACT hash had
moved, so its manifests were stale) and on `perch-context` (a 2.6 KB round-9
paragraph in `tests/compiler-nest/SPEC.md`, the Perch task of the pattern-matrix
groups, pushed `src/matrix-LAWS.bend::flag` past the 60,000-byte context bound;
the paragraph is now 763 bytes). A scratch run of the first line-break form
failed on `census` (stale manifests) and `nest-round3` (the `header-past-colon`
outcome above). No other gate failed in any run.

The regenerated receipts of the earlier nest gates (`nest`, `nest-review`,
`nest-round3`, `nest-round4`, `nest-round6`, `nest-round7`, `nest-round8`) and the
shared receipts of the existing gates are **left for the coordinator's refresh**;
`round9.json` is refreshed from a direct run on `e7a9d7e`, whose inputs match the
tree.

## Style preflight

`round9-preflight.txt` records the offline preflight (0 provider requests). The
whole compiler manifest exits 0: 20 groups, every composition available, 0
truncated, 0 role-limited, 0 structural blockers. The new mechanisms and laws
(`expected`, `binder_failure`, `body_end`, the check and parser laws) have
complete contexts (0 truncated, 0 role-limited). Three whole-checker helper
functions (`flat_let`, `matrix_let`, `residual_let`) and the four witnesses of
`src/matrix-LAWS.bend` are truncated by the helper limit, as the round-8 witnesses
are, since each reaches `K.run`. Headroom is
thin: `pattern-matrix-laws` composes to 45,436 of 48,000 bytes, `frontend-laws`
to 43,781, and `tests/compiler-nest/SPEC.md` (14,479 bytes, the task of the
pattern-matrix groups) has about 300 bytes before the context bound.

## Remaining for the coordinator

- Live Perch review of the new declarations, with `--task=tests/compiler-nest/SPEC.md`.
- Refresh receipts after merge (the earlier nest gates, `selfhost` whose D4 gaps
  fell from 5 to 1, and the shared receipts). Sign off on the two round-3 mutant
  outcomes.
- The modules round's scope-aware dotted-binder rule (above).
- The declaration-list line-break gap, which belongs to the selfhost `layout` need.
- Both D21 laws are unchanged, and both remain required open obligations.
- The destructuring let under a `+` row (`case +y: O{p} = y`) is still
  `Unsupported parse destructuring-binding`, a non-accepting outcome the seed
  does not share; it predates this increment.
