# Nest review round 12

This round answers review round 3 of the second review cycle (the reviewer's `sem12`, `scope12` and `gates12`;
three confirmed findings). All three are **fixed**, none is disputed. The repairs converge on the class each finding
named: `fuzz12.py` draws the first-row marks and the term suffixes across every split, site and gap, and token mutation
of the frozen fixtures looked for the shapes it did not draw; each shape it found is frozen and repaired, or listed as open.

| Finding | Disposition |
|---|---|
| 1 (major, D4): seed-accepted body forms in a dead row of a two-scrutinee match are Invalid, where the merge base answered Unsupported | **Fixed as a class.** `Unsupported parse term-form` for an infix operator, a call, an index, an offload `!(`, a lambda after a name, `+name` and `+(name)` (also across the line break after the `+`), and a line that starts with an operator, `!(` or `=>`, at every site a term ends: a body, a let's value, an expression argument, a line's start. A let's value on the line after its `=` is `Unsupported line-break` whatever term it starts. REVIEW-11's "one program" is corrected |
| 2 (major): `nest-round11` and `nest-sweep11` race on the oracle's wrapper files | **Fixed.** Wrapper files are written by rename; a check in `nest-round12` fails a truncating writer |
| 3 (major): a seed-accepted `+` in the first row of a split is `Invalid check affine-reuse` | **Fixed.** The Decision's field binders are marked from the first row that starts the constructor, as in the seed's `match_flatten` |

| Commit | Change |
|---|---|
| `748bf0c6` | Finding 2: `regen.publish` writes wrappers by rename; the four oracle writers use it |
| `e6a61a30`, `c8a011b0`, `a613ce13`, `7b0f1285`, `216af7bf`, `c8ef78f3`, `5b264125`, `ad4f9902` | D7 freezes, from the pinned seed, before the repair each fixture tests; the set grew from 119 (216 seed calls) to 161 fixtures (229 seed calls) |
| `74700626` | Finding 3: `M.leading`, `M.marked`, the Decision's marked pattern, the lowering proof's mirror, two witness laws |
| `a2398b3b`, `9055abe8`, `31010fc3`, `b5c6a8a3`, `4d6447ac`, `6d287718` | Finding 1: `suffix`, `operator`, `continues`, `lambda`, `promoted_term` and their sites; the argument branch order that keeps round 9's anchor and law; `<=` and `>=` at a let's column; `+(a)` and a `+` that ends its line; a let's value on the next line; eight witness laws |
| `3281c22e` | Seed-derived amendments: one round-10 expectation and three mutant effects (below) |
| `1c4f48e4`, `3c0213a0`, `960f6347` | Census approval (summary in the first message) and inventory; the laws fitted to their groups |
| `21f4dc70` | The `nest-round12` gate, `fuzz12.py`, the runner registration, SPEC, CONTRACT and GATES |
| `abbd048f`, `6ba71564` and the commit of this report | The final SPEC, CONTRACT, GATES and ROUNDS statements and the REVIEW-11 correction; the round-12 receipts (`round12.json`, the preflight and falsification reports); this report, the Perch log entry and the campaign state |

Commit trailers read `Co-Authored-By: Claude Sonnet 5.5`, the running model according to the harness; the task text named
`Claude Opus 5.5`, as in rounds 9 to 11.

## Items for coordinator sign-off

- **One round-10 expectation amended (its own commit, `3281c22e`).** `argspace-operator-call` (`two(a + b)` in a
  live def body) was pinned `Invalid parse argument-separator` ("an operator after an argument is no term"). The seed
  rejects it only for its type (`a type for this operator`); it accepts the same text in a row the lowering discards (the
  `suffix-*-dead-arg` fixtures: nine when the commit was written, ten now, all seed-accepted) and in a live row whose
  operator target the program defines (`suffix-or-defined`, `suffix-amp-defined`). The parser can see neither, so
  `Invalid` was wrong under D4. The seed observation is unchanged; the reviewed Knot outcome is now `Unsupported parse
  term-form`, and `round10_seed.py` accepts an Unsupported fixture the seed rejects when its group states the seed's
  reason, as `round11_seed.py` does. `argspace-operator-fields` stays Invalid: a pattern is always validated. The commit
  message says 14 `suffix-*-dead-arg` fixtures; there were nine.
- **A precision change across the whole class.** Live-row programs the seed rejects that end in a term suffix (`a <> a`,
  `h(a)(a)`, `a[0n]`, an operator with no target, ...) moved from `Invalid` to `Unsupported`, not only round 10's fixture.
  The justification is the seed's own acceptance of the same text: `live-or.bend` (`def Bool.or`, then `On{} || Off{}` in a
  live row prints `On{}`), `suffix-or-defined` and `suffix-amp-defined`, and every discarded row (the frozen dead fixtures).
  D4 asks for `Unsupported` where Knot cannot judge. `Invalid` stays where the seed rejects however a program is written:
  a closer, `==`, `=>` after a constructor, a marker touching a name, a lone `.` or `!`, a `(` or `[` that starts a line, an
  erased `-name`, a closer or colon after a let's `=` (17 controls in the frozen set).
- **Three mutant effects changed, each still killed on its own witness** (the round-10 ruling (3) covers the same
  situation): round 6 `touch-call-parenthesis` and round 11 `argument-ignores-paren` (a `(` after a term is now a
  suffix: Invalid end-of-body and argument-separator become Unsupported term-form), round 11 `colon-split-invalid` (`+u`,
  a line break, the colon split disabled: a promoted term, Invalid expected-= becomes Unsupported term-form).
  `mutcheck` (scratch) ran all 141 mutants of the nine older gates and `nest-round12` on the final sources (two are
  eval-phase and skipped): no other anchor moved and no other effect changed.
- **`pattern-matrix-laws` stands at 47,886 of 48,000 bytes.** The first draft's two helper unit laws
  (`leading_witness`, `marked_witness`) put it at 48,667, one structural blocker; they are dropped, and the fixtures, the
  mutants (`leading-takes-second-row`, `leading-takes-last-row`, `marked-promotes-every-field`,
  `marked-ignores-later-fields`) and the two whole-checker witnesses pin the helpers. The manifest preflight is 20 groups,
  0 structural blockers. The next law added to that group needs room first.
- **`tests/compiler-nest/SPEC.md`** moves two round-1 paragraphs (the control and mutant descriptions of `check.py`) to
  `ROUNDS.md` and gains the marks rule; `src/SPEC.md`, `src/CONTRACT.json` and `GATES.md` state both rules.
- **One gate, not two.** `nest-round12` runs the fixtures, the 26 mutants, the publish check and the 3,000-program
  generator; the sweep needs no oracle replay, so it shares no file with another gate.

## Finding 1 (major, D4): a term suffix in a discarded row

**Fixed as a class.**

### The seed's rule

`parse_term_ops` (`bend.ts`) reads, after a complete term, a call `(`, an index `[`, an offload `!(`, a lambda `=>` (a
binder is one name: `parse_bind`) and every infix operator of its `INFIX` table, and stops at a `(` or `[` that starts a
line (`parse_nl`); `parse_skip` skips newlines, so a line that starts with an operator, `!(` or `=>` continues the term.
`+` and `-` touching a name are markers, not operators. `parse_term_base` reads `+X` as a promoted variable when X is no
datatype, and skips whitespace, line breaks included, after the `+`. A body the lowering discards is parsed and never
checked, so each of these is accepted there; a live one needs a target the program defines (`def Bool.or`, `def Pair`,
`Array.get`), which is why the same text is rejected "for its type" in a live row and accepted in a dead one. The
reviewer's eight forms are the first eight; the whole `INFIX` table, the lambda, `!(` and the line-start continuations
are the rest of the class, and the merge base's single answer, `Unsupported match-scrutinees`, hid it. The
single-scrutinee twins were `Invalid` on `main` as well: main-era, but reachable only after the multi-scrutinee header, so
the branch widened their reach. A live row with a defined target is seed-accepted too (`live-or.bend`), which shows that
`Invalid` was wrong for the live form of these terms whether or not a row is discarded.

### The repair

`P.suffix(ts)` is a call `(`, an index `[`, an offload `!(` or `P.operator(ts)`: a token of the seed's table (`*`, `/`, `%`,
`<`, `>`, `&`, `|`), `.` before `|`, `^` or `&`, and `+` or `-` unless a name touches it (`P.marker`). All are read head first, so
a token that is none of them decides without the tokens after it (the frozen laws normalize over an abstract tail).
`P.lambda(node, ts)` is `=>` touching, after a name. The answer is `Unsupported parse term-form` at each site a term ends:

- `reply` (a body's term): `suffix`;
- `line_end` (a let's value): `suffix`, after the existing statement check (`+` and `-` keep `same-line-statement`);
- an expression argument list (`ListTail`): `suffix` or `lambda`, tried before the line break so that round 9's anchor
  and law stay; a pattern's fields and a def header's parameters keep `argument-separator`;
- `BindingTail`: `lambda` after the let's value;
- `BindingStart`, the marker `+`: `promoted_term` (`+name` before a line's end or an operator, where no let follows), `+(`
  on the line or after a line break, and `+` after a line break (`Unsupported repeated-promotion`); an erased `-name`, `+name y`
  and `+h(a)` stay invalid, as the seed rejects them;
- a line that starts with an operator, `!(` or `=>` (`P.continues`): at a let's column or below it (`BodyAt`, and
  `BindingStart` when the operator is followed by `=`, as `<=` and `>=` are), left of the arms (`Declaration`) and at the
  margin (`Header`);
- a let's value on the line after its `=` (`assign`): any token that starts a term, not only a name, is `Unsupported line-break`
  (a closer, a colon or a keyword stays `Invalid expected-term`).

Eleven definitions are new in `src/parse.bend` (`touching`, `marker`, `operator`, `bang`, `suffix`, `arrow`, `variable`,
`lambda`, `continues`, `promoted_term`, `terminated`; `reply` and the sites above call them) and `src/syntax.bend` gains
`infix`. Eight witness laws in `src/LAWS.bend` (`suffix_witness`, `continues_witness`, `lambda_witness`,
`promoted_term_witness`, `suffix_ends_a_body`, `marker_ends_no_body`, `suffix_ends_a_let`,
`promoted_term_is_unsupported`) state the predicates and the outcomes; each is falsified by a mutant
(`receipts/round12-falsification.txt`).

### Evidence

- **Fixtures (D7), 129.** 109 are `Unsupported`: the reviewer's eight forms and 26 more (each entry of
  the seed's `INFIX` table, `+ x0`, `+(a)`, a call after a constructor, a lambda) in a dead row of a two-scrutinee match (34),
  the same forms at the own-line, single-scrutinee, let and argument sites (10 each), their live twins (nine the seed rejects for
  its type, and three it accepts: two rows whose operator target the program defines, and `h!(a)`), nine line-start
  continuations, six markers that end their line and eight lets whose value starts on the next line. 20 are controls that keep
  their outcome: 17 `Invalid` (a closer, a comma, `==`, `=>` after a constructor, a marker touching a name, a lone `.` or `!`, a
  `[` that starts a line, an erased `-name`, a closer or colon after a let's `=`) and three plain programs that stay Accepted.
  97 of the 129 failed on the round-11 checker.
- **Mutants, 21** (`round12.py`): `body-suffix-invalid`, `let-suffix-invalid`, `argument-suffix-invalid`,
  `argument-lambda-invalid`, `let-lambda-invalid`, `promoted-term-invalid`, `binding-paren-invalid`,
  `binding-paren-needs-no-break`, `binding-repeated-break-invalid`, `value-break-term-invalid` (each reads one site as invalid
  again), `erased-term-unsupported`, `every-token-a-suffix`, `marker-an-operator`, `dot-an-operator`, `bang-without-paren`,
  `value-break-any-token` (each widens a rule to what the seed rejects), `margin-operator-invalid`, `left-operator-invalid`,
  `let-operator-invalid`, `binding-operator-invalid` and `continuation-needs-no-bang` (the continuation sites).

## Finding 2 (major): the oracle's wrapper files

**Fixed.** `round11.py` and `round11.py --sweep` both run `round11_seed.py`, which rewrote
`.local/compiler-nest/calls/<fixture>/<call>.bend` with a truncating `write_text` before running the seed on it; the
runner has no `needs` edge between the gates, so a reader could find another writer's empty file (`All terms check.`
where a value was expected, `review_seed.py:39`). `regen.publish` writes a private temporary file and renames it over the
target. `regen.observe`, `review_seed.observe`, `letalias.compare` and `typekind.compare` use it.

- **Before and after.** Four to six concurrent copies of `round11_seed.py` on exported trees: the round-11 tip failed 2 of
  4 and 3 of 6; the repaired tree passed 18 of 18. The reviewer's paired trial (both gate modes started together, watched
  for 30 s, which covers the oracle): the round-11 tip failed 5 of 12 trials with the same traceback; the repaired tree
  passed 12 of 12.
- **A standing check.** `nest-round12` publishes a file, holds it open, publishes again and requires the held handle to keep
  its whole snapshot, the path to hold the new text and no temporary file to remain; the same check must reject a
  truncating writer (deterministic: an in-place write changes what the held handle reads).
- The reviewer's alternative (a `needs` edge) would also need `test_runner.py`'s exact map changed, and costs wall time.

## Finding 3 (major): a `+` in the first row of a split

**Fixed.**

### The seed's rule

`match_flatten` chooses `c`, the first row whose head is a constructor, and builds the split's field binders `xs` from
`c`'s own field variables, each joined with `xq = patt_mark(x, rows)` (the marks of the column's variable rows). Every row
below the split is matched against those binders, so a `+` on a field of `c` marks that field for all of them, and the
default matrix chooses its own first constructor row. A `+` in a later row marks only that row's binder (its alias); the
marks of a variable row reach every row of the column it closes. Knot opened fresh unmarked fields and let each row's
alias promote, so rows separated by an earlier constructor column never saw the mark: `case P{On{}, +v}: both(v, v)` then
`case P{Off{}, v}: both(v, v)` was `Invalid check affine-reuse`.

### The repair

`M.leading(rows)` reads the first constructor row's field patterns; `M.marked(fields, first)` turns each fresh field whose
counterpart there is a `+` into a `Promotion`. `M.split` puts the result in the Decision's pattern only: the sub-matrix keeps
its variable columns, `P.branch` opens the marked fields with quantity 2, and every split, one in a default matrix included,
reads its own rows. The kind of a promoted field is judged where the frontier binds it, as before, so a `+` on a `Type` field
of the first row is still `reusable-type`. The D21 proof mirrors the new pattern in `lowering-PROOF.bend::split_node`; every
`src/*PROOF.bend` prints `All terms check.` (dropping the marks makes `lowering-PROOF` itself fail at `splits`).
`first_row_marks_witness` and `unmarked_first_row_witness` state the whole-checker outcome with and without the mark.

### Evidence

- **Fixtures (D7), 32.** The reviewer's eight accepted programs, ten neighbours (each field position, both fields, two marked
  fields, constructors of two arities split in the default matrix, two columns, a Data parent) and the marks of a variable row
  are Checked (20 with the flat control); 12 controls keep what the seed does (the `+` in a later row, another constructor's
  first row, another column, another field, none: `affine-reuse`; a `+` on a `Type` field: `reusable-type`). 15 of the 19
  accepted programs failed on the round-11 checker (the other four reach the mark through variable columns). The 229 seed calls
  agree with the evaluator and Wasm in both lanes.
- **The reviewer's 15 repro files** (`r12-sem/.local/probe/repros`: eight seed-accepted programs and seven controls) and the
  fixtures that stand for them. Thirteen fixtures carry the same case rows as the reviewer's file (up to the name of one type), in the shared
  prelude of `round12_seed.py`: `plus-first-row-pair` is `plusfirst-pair`, `-second-uses-once` is `plusfirst-second-once`, `-var-row-after` is
  `plusfirst-var-row-after`, `-three-rows` is `plusfirst-three-rows`, `-two-levels` is `plusfirst-two-levels`,
  `plus-underscore-first-row` is `plusfirst-underscore`, `plus-underscore-x-first-row` is `plusfirst-underscore-name`,
  `plus-first-row-data-parent` is `plusfirst-data-parent` (a `Data` parent `D2`), `ctl-plus-in-later-row` is
  `plusfirst-ctl-later-row`, `ctl-other-constructor` is `plusfirst-ctl-other-constructor`, `ctl-type-kind-first` and
  `ctl-type-kind-later` are `plusfirst-ctl-type-first` and `plusfirst-ctl-type-later` (`reusable-type`), and `ctl-flat-single-row`
  is `plusfirst-ctl-flat`. The two controls with two flat `Flag` columns (`ctl-second-column`, `ctl-plus-underscore-flat`) are
  frozen in a `Pair`-then-`Flag` form, `plusfirst-ctl-second-column` and `plusfirst-ctl-underscore-flat`; their flat form is
  drawn by the plus family of `fuzz12.py` (a `Flag` column is one of its nine column types) but not frozen as a fixture. All 15
  files, verbatim, were also run through the seed and the final build outside the gate: the nine accepted ones (the eight
  programs and the flat control) are Accepted by both, evaluate to the seed's `On{}` in both lanes and compile through the
  `knot-fields-wasm-1` profile to a module whose `main` returns 1; the six rejecting controls are Invalid in both. The reviewer's
  three random programs (`sfz/s3/c548`, `c1429`, `c2111`) check and evaluate to `On{}`, and the verifier's own two corpora
  (`myfuzz-7`, 12,000 programs, and `myfuzz-20260929`, 3,000) show 0 discrepancies against the seed. The finding-1 probe programs
  of the reviewer and the verifier (48 files: the eight forms in a dead row, their single-scrutinee twins, controls, three
  scrutinees, a dead row after exhaustive rows, and the live-row controls) are never Invalid where the seed accepts: 12 Accepted,
  34 `Unsupported`, and the two live-row controls the seed rejects are `Unsupported`.
- **Mutants, 5:** `split-ignores-first-row-marks`, `leading-takes-second-row`, `leading-takes-last-row`,
  `marked-promotes-every-field`, `marked-ignores-later-fields`.

## Convergence

- **`fuzz12.py`, 3,000 fixed-seed programs in two families**, every one classed: *plus* (1,800: fielded matches of one or two
  columns over a pair, a triple, a box, constructors of two arities, an option, a list and Data twins, two to four rows whose
  slots are a wildcard, a name, a `+name` or a nested constructor, bodies that use one binder twice, once or never, and a
  catch-all row half of the time) and *suffix* (1,200: a term of five shapes followed by an operator, a call, an index, an offload,
  a lambda, a junk token or a `+name` term, after nothing, a space, a break at six columns, a comment or a blank line, at eight
  sites, a let's value on its `=` line or the next, in a kept or a discarded row). The gate requires 50 seed-accepted and 50
  seed-rejected programs per family. **0 false acceptances and 0 false Invalid**; the 748 programs both sides accept evaluate
  to the seed's value in both lanes. On the round-11 tip the same programs report 343 false Invalid (and 0 false acceptances).
- **Other seeds, offline, on the final tree.** 24,000 programs of four other seeds of `fuzz12.py` (11, 22, 33, 44): 0 false
  acceptances and 0 false Invalid, 5,984 evaluator values equal to the seed's. (The first three 6,000-program runs, on the tree
  before the `<=` repair, found `<=` and `>=`; 30,000, 18,000, 24,000 and 24,000 programs on the trees after each later repair
  found nothing.) The reviewers' own fuzzers, copied to scratch: `plusfuzz.py` (10,000 programs), `plusfuzz2.py` and `qfuzz.py`
  (2,500 each), `deadfuzz.py` and `reachfuzz.py` (2,000 each): 0 discrepancies. The 2,968 programs of two of the four sweeps that
  both sides accept compile through the `knot-fields-wasm-1` profile and run to the seed's value.
- **Token mutation of the frozen fixtures** (scratch, `mutfuzz.py`, the merge-base checker labelling main-era gaps): 340,000
  mutants in four batches: 120,000 after the `<=` repair, 80,000 after the `+(a)` repair, 80,000 after the marker-break repair and
  60,000 on the final tree. The false acceptances (3 to 10 per run of 30,000 or 40,000 mutants) are all the literals-owned let binder named after a
  constructor (finding 7 of round 10). The false Invalid that the merge-base checker does not report (9 in the last 60,000)
  answer the same on the round-11 tip: eight are a def body at column 0 (the frontend gate pins it) and one is an erased let of a
  global function (`-v = main`). The earlier batches found the shapes repaired above (`+(a)`, `+` at a line's end, a let's
  value on the next line, and `<=` and `>=` at a let's column; each frozen first) and one that stays open (`?` and `+a` as a next
  argument).
- **Sensitivity.** On the round-11 tip 112 of the 161 frozen fixtures fail (15 of the 32 first-row fixtures, 97 of the 129 suffix
  fixtures).

## Open D4 families (seed-accepted, Knot Invalid; not drawn by `fuzz12.py`)

Named so that the next reviewer's fuzz does not rediscover them; each is main-era.

- **A spaced `+` or `-` that starts the line after a let's value** (`u : Flag = a`, then `- a`): the seed continues the value with an
  operator; `Invalid parse detached-marker` is pinned by round 10's law `detached_marker`, which normalizes over an abstract tail.
  Refining it (Unsupported unless a let follows) would amend that law, so it is left for a coordinator ruling.
- **A term that starts the next argument after whitespace and is no name, numeral or parenthesis** (a hole `? a`, `@`, `\`, or a `+`
  marker: `h(a +b)`, pinned `Invalid argument-separator` by round 10's `argspace-promoted-call`).
- **`match c():`** (a zero-argument call of a parameter reads as the parameter; `Invalid check computed-scrutinee`).
- The families of REVIEW-11 that are not term suffixes: the def-header and type-field layout (literals-layout), a def body at
  column 0, partial application, a global function as a value (`-v = main`), a Nat literal as a let binder at another column,
  a constructor line of a type declaration at another column and a lone marker line after a let's value.

## Gates

`BEND_NO_TELEMETRY=1 npm run -s gates` on the final code tree (code identical to `6ba71564`; the working tree differed only in this
report, the Perch log and the campaign state): exit 0 after 1,710 s, **32 of 32 gates passed** (the runner's stderr, unedited):

```
checker: passed (21.17s)
structural: passed (25.50s)
structural-trust: passed (0.37s)
owned-store: passed (6.40s)
flat-store: passed (13.57s)
fields: passed (50.44s)
fields-trust: passed (0.53s)
frontend: passed (53.64s)
census: passed (4.04s)
wasm: passed (48.71s)
wasm-trust: passed (0.53s)
lint:verify: passed (6.80s)
recursion: passed (45.83s)
perch-context: passed (34.40s)
classification: passed (3.46s)
bootstrap: passed (55.59s)
io-host: passed (13.46s)
fields-wasm: passed (100.29s)
io-abi-2: passed (47.49s)
nest: passed (182.29s)
nest-review: passed (203.41s)
selfhost: passed (176.26s)
nest-round4: passed (161.44s)
nest-round3: passed (290.07s)
nest-round6: passed (193.73s)
nest-round7: passed (206.74s)
nest-round8: passed (229.02s)
nest-round9: passed (322.21s)
nest-round10: passed (508.09s)
nest-sweep11: passed (414.35s)
nest-round11: passed (658.03s)
nest-round12: passed (826.06s)
```

The regenerated receipts: 64 identical, 9 volatile-only, 29 semantic. The semantic ones are the older gates' receipts, which record
build and input hashes and the worktree path of their `argv` (refresh them after the merge, as before); the regenerated
`round12.json` differs from the committed one only in those `argv` paths (its counts, the sweep's observation hash and all 225 input
hashes are equal). The message of `6ba71564` says the direct run was at `960f6347`; it started at 08:47 on `6d287718` plus
uncommitted documents, before `abbd048f` and `960f6347` existed, and the equal hashes are what make the receipt stand.
`BEND_NO_TELEMETRY=1 npm run -s gates:verify`: 20 tests, OK. `node tools/census/census.mjs --check`: exit 0.

Every `src/*PROOF.bend` entry prints `All terms check.` (`PROOF`, `catalog-PROOF`, `check-PROOF`, `fields-PROOF`,
`lowering-PROOF`, `matrix-PROOF`, `recursion-PROOF`, `runtime-PROOF`).

## Style preflight

`round12-preflight.txt` records the offline preflight (`node scripts/perch-style.mjs --preflight`, 0 provider requests): each of
the eight changed sources alone, the eight together and the compiler manifest. **The manifest is the meaningful measure: 20
groups, every composition available, 0 truncated, 0 role-limited, 0 structural blockers** (`pattern-matrix-laws` 47,886 of
48,000 bytes, `frontend-parsing` 34,626, `frontend-laws` 26,947). The whole-file numbers repeat the limits of the earlier rounds.

## Remaining for the coordinator

- Live Perch review of the new declarations (`leading`, `marked`, `suffix`, `operator`, `marker`, `bang`, `arrow`, `lambda`,
  `variable`, `touching`, `continues`, `promoted_term`, `terminated`, `infix` and the ten laws), with
  `--task=tests/compiler-nest/SPEC.md` for the matrix groups and `src/SPEC.md` for the frontend groups.
- Refresh the receipts after merge (the earlier nest gates, whose input hashes moved) and sign off on the amendments above.
- Reconcile with the literals branch: its let-binder constructor rule joins `G.promotion` at the let site and in the audit's let
  case; its layout increment owns the def-header list continuation.
- The open D4 families above. Both D21 laws are unchanged and remain required open obligations.
