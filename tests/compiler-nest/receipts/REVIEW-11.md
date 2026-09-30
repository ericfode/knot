# Nest review round 11

This round answers review round 2 of the second review cycle (the reviewer's `sem11`, `scope11`,
`gates11`; seven confirmed findings). Six are **fixed** and the seventh is owned by the literals branch.
The round's aim was to converge, so it adds a differential generator that draws each finding's shape
and its neighbours together, an exhaustive gap search over every pair of adjacent tokens, and a token-mutation fuzz
that found what the generator did not.

| Finding | Disposition |
|---|---|
| 1 (blocking): a nested match in a discarded row body is never pattern-validated | **Fixed.** `M.audit` reads every row of every match, through lets and nested matches, whether or not the lowering keeps the body |
| 2 (blocking): `+D` binder, `D` a datatype declared earlier | **Fixed.** `Invalid check datatype-pattern-binder`, at rows, fields, `+` lets and discarded bodies; the rule is source-ordered |
| 3 (blocking): a binder named after a datatype, then used as a type | **Fixed.** `Invalid check type-shadowed` for an annotation, a later parameter type, the result type and a later field type |
| 4 (major, D4): seed-accepted multi-scrutinee layouts are Invalid | **Fixed** for the four reviewed shapes and every further shape the token-mutation fuzz and the gap search found (ten sites in all): `Unsupported`. Open D4 families are listed below, none of them pattern-related |
| 5 (major, D4): a Nat literal in a later column is Invalid | **Fixed.** `Unsupported parse term-form`, as after a comma |
| 6 (major): the arity checks have no witness | **Fixed.** 21 seed-frozen rejected witnesses with three controls, and four mutants that delete each check |
| 7 (pre-existing): a let binder named after a constructor is accepted | **Owned by the literals branch** (`abda3875`, "test let binders against constructors"); recorded, not fixed. The generator never draws it |

## Coordinator rulings on round 10 (recorded)

- (3) The changed round-3 mutant outcomes (erased-let-as-pattern, header-past-colon) are accepted: both mutants are still killed.
- (5) The def-header and type-field line-break D4 gap is owned by the literals-layout increment (the list continuation points, `layout-def-header`). Nothing here duplicates it; the literals-integ merge reconciles it.
- (7) The frozen `matrix-work` control stays. Whether expansion should short-circuit an irrefutable first row is a speed-track question, recorded for later, with no change now. The `tests/compiler-recursion/SPEC.md` amendment happens with the descent-2 integration.
- (8) The destructuring let under a `+` row stays `Unsupported`, which is non-accepting.

| Commit | Change |
|---|---|
| `91923a16` | Merge of `main` (25b3a5b6); the only conflict was the append-only Perch review log |
| `b4a522d7` | D7 freeze for findings 1 to 6: 259 fixtures generated from templates in `round11_seed.py`, 282 seed calls; 159 fail on the round-10 checker |
| `f237a1a7` | Findings 1, 2, 3 and 6: `M.audit`, `G.binder`/`promotion`/`hidden`, the annotation, parameter, result and field checks; three mutants re-anchored |
| `3172853b` | Findings 4 and 5: `S.numeral`, `S.statement`, `opens`, the layout stopgaps; five round-10 mutants re-anchored |
| `480b50ff` | Second freeze, from the first 72,000 mutants of the token fuzz: 34 more fixtures (293 in all, 307 seed calls) |
| `56772770` | The stopgaps that fuzz found (`line_end`, plain-name `split`, declarations at another column or on a body's line, a case at the margin) and `+` lets in discarded bodies |
| `820fc622` | The gates `nest-round11` and `nest-sweep11`, `fuzz11.py`, room in two Perch groups (SPEC.md to ROUNDS.md, `frontend-laws` selection) |
| `4770901b`, `bb6e236d` | `G.parameters` keeps its public signature; a parameter's type is checked in its own pass (`telescope`), so the older gates' programs and mutant anchors stay |
| `79b46d59` | Fifteen witness laws with `{==}` fills (three more with the parenthesis repair) |
| `bebcf6b9` | `src/SPEC.md`, `src/CONTRACT.json`, `GATES.md` |
| `f92f7cfb`, `8d5108dc` | The names family draws a real call of `h`; the let line-break comments say where they belong |
| `a05658e7` | Third freeze, from the 100,000-mutant run: 13 header-term and numeral-argument fixtures (306 in all, 314 seed calls) |
| `f07920ad` | The stopgaps for them (`term_start`, `S.closes`, numeral arguments); four mutants |
| `a5df6f28` | Census approval and inventory (summary in the message) |
| `045725dd` | Fourth freeze, from the exhaustive gap search: 24 `paren-*` fixtures (330 in all, 328 seed calls); 19 fail on the checker before the repair |
| `89df7a98` | The repair (`S.same_line`, `opens`, the argument list), the `parens` family (COUNT 6,100), `gapsearch.py`, four mutants, three laws; four mutant anchors moved (two of them in round 6 and round 10) |
| `137f6cf4` | Census approval for it |
| Final commits | The round-11 receipts (`round11.json`, `round11-sweep.json`, `round11-gapsearch.json`, `round11-probescan.json`, the preflight and falsification reports), this report, the Perch log entry and the campaign state |

Commit trailers read `Co-Authored-By: Claude Sonnet 5.5`, the running model according to the harness;
the task text named `Claude Opus 5.5` (as it did in rounds 9 and 10). The merge commit was amended to match.

## Items for coordinator sign-off

- **Ten mutant anchors of earlier gates moved, with unchanged effects.** The audit replaced
  `prepare` and the field binder block calls `G.binder`, so `check.py` (`last-row-wins`,
  `most-specific-row-wins`: `prepare(fuel,rows,..` became `sequenced(rows)`), `round8.py`
  (`judge-field-kind-at-binding`: the block text) and `round10.py` (`ignore-plus-gap-later-column`:
  `opens(tokens)`; `equals-line-break-invalid`, `line-break-before-any-token`,
  `arm-body-layout-invalid`, `body-layout-any-token`: the widened conditions) name the new text; the header
  and argument stopgaps widened the condition `round10.py` `argument-whitespace-invalid` replaces, and the
  line-aware call (`S.same_line`) the one `round6.py` `touch-call-parenthesis` replaces. Each is
  still killed in both lanes on its own witness. No anchor, fixture or assertion of the checker, structural,
  fields, wasm or recursion gates changed: an earlier draft that threaded the earlier names through
  `G.parameters` broke `tests/compiler-checker/bounds.bend` (its parameters are `N0..` with the datatype
  `N0`) and the structural gate's `reverse-fields` anchor, so the rule moved out of those functions.
- **`tests/compiler-nest/SPEC.md` shrinks** from 14,727 to 9,120 bytes. The `flag` declaration of
  `src/matrix-LAWS.bend` had 50 bytes under its 60,000-byte Perch state bound; the round's helpers put it at
  61,691. The task text of the matrix groups kept a paragraph of evidence per round; those paragraphs moved
  verbatim to `ROUNDS.md`, and SPEC.md states the audit, binder and shadowing contract.
- **`frontend-laws` selects `LAWS.bend` and `PROOF.bend` in full** (`selected_files`); `syntax`, `lex` and
  `parse` enter as interfaces and are read in full by `syntax-core`, `frontend-lexing` and `frontend-parsing`.
  The group stood at 47,916 of 48,000 bytes; with the parser's growth it would be 49,868. The manifest
  preflight: 20 groups, 0 structural blockers, 0 truncated, 0 role-limited (`pattern-matrix-laws` stands at
  46,889 of 48,000, `frontend-laws` at 23,656 with the round's laws).
- **Two gates, not one.** `nest-round11` (fixtures and 23 audit, name-rule and shadowing mutants) and
  `nest-sweep11` (18 parser mutants and the 6,100-program generator) split the work so that each stays under
  the runner's per-gate limit under load. Both are registered in `scripts/gates/run.py` and its self-test.
- **`round11_seed.py` lets an `Unsupported` fixture be one the seed rejects** when its group states the seed's reason
  (six `paren-*` fixtures: a program Knot cannot read, where `Invalid` would need a parenthesized term it has no form
  for); every other `Unsupported` fixture must be seed-accepted, and an `Invalid` one seed-rejected, as before.
  `tests/compiler-nest/gapsearch.py` is an offline tool, not a gate; its receipt is `round11-gapsearch.json`.
- **The census approval** covers the round's new declarations and gate scripts (see its commit messages).
- **The `Unsupported` stopgaps are statements about the seed's layout freedom, not about parser
  soundness.** Each answers where the seed accepts, keeps `Invalid` where it cannot, and is killed by a mutant.

## Finding 1 (blocking): a nested match in a discarded row body

**Fixed.**

### The seed's rule

`parse_body` parses every row of every match and `parse_patt` validates each pattern (`bend.ts`
~1668): a declared constructor, its field count, no constructor as a bare binder, a term that is a binder
or a constructor; `parse_body` checks that a row has one pattern per scrutinee. A row's body is checked
only where `match_flatten` keeps it, so a type error, an unbound name, a computed or unbound scrutinee or an
unknown annotation type in a shadowed body is accepted. The branch validated a matrix's rows in `prepare`
when the checker reached the match; a match inside a body that no leaf selects was never reached.

### The repair

`M.audit` (src/matrix.bend) is one fuel-first dispatcher over the body tree: a `let` (its `+` through
`G.promotion`, then its body), a `match` (the width from its scrutinees, then its rows), and a row list (each
row's width, `validate` of its patterns, `audit` of its body, then the rest). `start` audits all rows of a
reached match before building the matrix; `sequenced` keeps the row-shape normalization `prepare` did. It
reads reachable bodies too (the same rule twice, idempotent) and checks no types, scopes or scrutinees, as the
seed does not. The lowering still discards an unreachable row's code.

### Evidence

- **Fixtures (D7), 108.** The reviewer's `r6` (unknown constructor), `r6b` (field count), `r6c` (pattern count),
  `r6d` (bare constructor), `p22 unreach-nonpat` (a call) and `d10` (a fresh field) are the `single` and `field`
  shapes; ten bad rows (unknown, arity up and down, bare, call, count, promoted datatype, promoted constructor,
  nested unknown, nested arity) in six shapes (wildcard first, duplicate row, two-column outer, two levels, a
  let ahead, a fresh field), a live twin of each, nested two-column matches with a short and a long row, the
  outer row's own pattern and a shadowed row of the reached nested match, and eight controls the seed accepts in
  a dead body (a type error, an unbound name, an unbound scrutinee, a computed scrutinee, an unknown annotation,
  an erased use, a shadowed annotation, a call of the wrong arity). On the round-10 checker 67 of the 108 fail
  (Checked where the seed rejects); all hold in both lanes now. `r6c` had been rejected correctly on `main` (`Invalid parse
  expected-:`); it is `Invalid check pattern-arity` now.
- **Mutants.** `audit-skips-bodies`, `audit-skips-nested-matches`, `audit-skips-let-bodies`,
  `audit-skips-let-promotion`, `audit-first-row-only`, `validate-accepts-calls`, `binder-accepts-constructors`.
- **Laws.** `discarded_unknown_constructor_witness`, `discarded_valid_row_witness`, `short_row_witness`,
  `extra_field_witness` (matrix-LAWS).

## Finding 2 (blocking): `+D` where D is a datatype declared earlier

**Fixed.**

`parse_term_base` reads `+X` with X a declared non-generic datatype as `+D<..>` and fails ("a quantified
datatype after +"; `bend.ts` ~1769); a name that is no datatype at that point of the file (declared later, a
function, undeclared, Base's `String`) is a promoted binder. The rule is source-ordered, like a
constructor's. A parameter reads `+` through `parse_quant`, a quantity, so `def f(+Tp: Flag)` with `Tp` a
datatype is accepted by the seed (probed), and the finding's suggestion to apply the rule to parameters
does not hold: the parameter forms that fail are finding 3's. `G.promotion(types, token, promoted)` reports `Invalid check datatype-pattern-binder`
when a datatype of that name was declared at or before the token (`prior_datatype`); `G.binder` runs the
constructor rule first and then `promotion`, so a name that is both keeps `constructor-pattern-binder`.
`validate` (rows, fields, nested), `P.fields` (flat fields), the `+` let and the audit's let all use them:
`G.binder` is the one place that names the binder rules (constructor and datatype), and the let site takes only
the datatype half, so the constructor half stays with the literals branch (finding 7).

- **Fixtures, 35.** `+Flag` at a row, a second and third column, a field, a second field, a nested field, a
  default row, an arm let, a typed let and a plain let; `+Color`, `+Opt`; the constructor and both-name cases;
  controls (a datatype declared after the def, before its own use and after it, a function, an undeclared
  name, Base's `String`, a plain name, `_x`, an erased `-Flag`, a bare `Flag`). `plusd-order-before` and
  `plusd-order-after` pin the source order in one file.
- **Mutants.** `promotion-ignores-datatypes`, `row-promotion-unmarked`, `field-promotion-unmarked`,
  `let-promotion-unchecked`, `datatype-order-ignored`, `bare-binder-promoted`.
- **Laws.** `promoted_datatype_is_rejected`, `bare_datatype_name_binds`, `later_datatype_is_no_datatype`.

## Finding 3 (blocking): a binder hides a datatype of its name

**Fixed.**

The seed has one namespace. `parse_var` searches the stack of open binders before a global name, so a
pattern, field, let or parameter binder named `Flag` makes a later `Flag` in a type position that binder, and
the check fails ("expected : Type, observed : Flag"). A parameter opens after its own type is parsed, so its
own type and a field's own type still name the datatype; a later parameter's type, the result (parsed with
every parameter open) and a later field's type see it. `G.hidden` is the rule, `G.visible` resolves a type
name through it. The typed-let annotation checks every binding in scope (`E.names`); `G.telescope` checks a
def's parameters once, each type against the names before it, and hands the names left to the result type;
`G.fields` uses `visible` for a field's type. `Invalid check type-shadowed`, after `unknown-type`. A row's binder
does not leak into the next row, and a discarded body's annotation is never checked, as in the seed.

- **Fixtures, 35.** The reviewer's `r3`, `r3b` and `p13` shapes (a row, either column of two, a nested field, a
  field, a let, a typed let, an erased let, a let in an arm, a parameter before and after another), the same with
  the both-name-free datatype `Color`, the signature forms (`def f(Flag: Flag) -> Flag`, `+` and `-` parameters,
  a later parameter type, the result after a second parameter, field types with an erased field) and a
  datatype declared after the binder; eleven controls (another type, a plain binder, a plain let, the annotation
  first, a binder's own type, a parameter's own type, another result, a field's own type, a row scope that ends,
  a dead body).
- **Mutants.** `annotation-ignores-binders`, `every-type-hidden`, `parameter-type-ignores-earlier`,
  `parameter-type-hides-itself`, `result-type-ignores-parameters`, `field-type-ignores-earlier`.
- **Laws.** `hidden_type_is_rejected`, `unrelated_binder_hides_nothing`.
- The reviewer's pre-existing forms (a field pattern then an annotation, parameters, type fields) are fixed by
  the same rule and frozen.

## Finding 4 (major, D4): seed-accepted layouts in multi-scrutinee matches

**Fixed for every shape found; the rest are open, main-era and named below.**

Main stopped every multi-scrutinee match at `Unsupported parse match-scrutinees`; the branch parses through it,
so each layout rule the parser has and the seed lacks (the seed reads a statement, a `case` or a let's colon
at any column and line) became a branch-introduced `Invalid`. The single-scrutinee outcomes were unchanged and
stay valid main-era gaps for the shapes not listed here; the sites below answer `Unsupported` in both.

| Shape (seed-accepted) | Site | Now |
|---|---|---|
| a case at, left of or at the margin of its match | `Declaration` (the case reaches the top level) | Unsupported `pattern-or-indentation` |
| a later statement at another column | `BodyAt` | Unsupported `body-indentation` (`S.statement`: a name, `match` or a marker) |
| a body of `+`, `-` or `match` at or left of its case | `StartBody` | Unsupported `body-indentation` (a name was round 10's) |
| a let split before its `:` or `=` (marker, or a plain name) | `assign`, and `BodyAt` for a plain name, through `split` | Unsupported `line-break` |
| a statement on the line of a let's value | `line_end` in `BindingTail` | Unsupported `same-line-statement` |
| a `def` or `type` at another column | `Declaration` | Unsupported `top-level-indentation` |
| a `def` or `type` on the line of a body's end | `body_end` | Unsupported `same-line-declaration` |
| a term after a header's scrutinee (`match a + b:`, `match a 10n:`, `match a 1n+m b:`) | `MatchTail` (`term_start`) | Unsupported `term-form` |
| a numeral as a call or field argument after whitespace (`h(On{} 10n)`, `Pr{On{} 10n}`) | the argument list | Unsupported `argument-whitespace` |
| a `(` that starts a line in a header (`match a`, break, `(b):`; `case x`, break, `(y):`; `h(a`, break, `(b))`) | `Term` (a call's parenthesis opens on its callee's line), `opens`, `ListTail` | Unsupported `term-form`, or `argument-whitespace` among arguments |

The reviewer's grid programs `p1` to `p4` are the first four rows; the rest, and the plain-name split and the
case at column 0, came from the token-mutation fuzz below. In a discarded body the seed reads any term as a
scrutinee and any argument after whitespace (a live match with the same header is rejected), so the header
continues at any token that is no closer, separator or keyword. The seed reads a `(` that starts a line as the next
term, never as the arguments of the term before it (`parse_term_ops` returns at `parse_nl` and `(`); a header joins
its lines, so the parser read `h`, break, `(a)` as the call `h(a)`: one column where the seed has two. That was a
false acceptance on the round-10 tip too (a dead nested match whose row has one pattern) and, with this round's
audit, a false Invalid where the row has two; exhaustive gap search found it (below). A token that can start no seed term (`case`, `def`, `)`) at another column stays `Invalid body-indentation`.
Round 13 corrects the other side of this boundary: `(`, `[`, numerals and `?` can start a term and are Unsupported, an empty arm stays Invalid, and a closer or a
keyword in a header stays `Invalid expected-:`; five fixtures pin that.

- **Fixtures, 95** (`layout-*`, `header-*`, `argument-*`, `paren-*`), in single and multi-scrutinee form, with the
  seed-accepted canonical layouts and the Invalid controls. The `paren-*` group is 24: eleven Unsupported where the
  seed accepts (a second column or row pattern in parentheses after a break of five kinds: an indent, the margin, a comment, a blank line, a deep indent), five
  Unsupported where the seed rejects (a dead nested match whose row has one pattern), two argument lists and
  five same-line controls. Nineteen of them failed on the round-10 checker.
- **Mutants (parser).** `declaration-case-invalid`, `declaration-indent-invalid`,
  `body-end-declaration-invalid`, `later-statement-invalid`, `marked-body-invalid`, `every-token-a-statement`
  (precision: a `case` after a let stays Invalid), `colon-split-invalid`, `plain-split-invalid`,
  `same-line-statement-invalid`, `header-ignores-terms`, `header-keyword-a-term` and `header-closer-a-term`
  (the header's two precision twins), `argument-ignores-numerals`, `call-ignores-line`, `call-needs-touch` (its
  precision twin: a spaced call is still a call), `opens-ignores-paren`, `argument-ignores-paren`.
- **Laws.** `statement_witness`, `same_line_statement`, `let_ends_at_line_break`, `split_before_colon_witness`,
  `same_line_witness`, `paren_on_a_later_line_is_no_call`, `parenthesis_opens_a_column`.

## Finding 5 (major, D4): a Nat literal in a later column

**Fixed.**

A row continued only at a name or a marking `+`, so `case _ 0n:` ended at the numeral and failed at the colon.
The seed's `parse_terms` reads any term as the next column and `parse_patt` reads a Nat literal through
`lit_step`; a U32, hex or fractional literal is rejected by the seed (unknown constructor `U32`), and a quote
literal is `Unsupported lex literal`. `opens` (a name, a numeral, a `(` or a marking `+`) is the continuation
predicate at both sites; the column then reports `Unsupported parse term-form`, as after a comma. Every
digit-leading token starts the same failure, so `1n+m` in a later column is the same shape.

- **Fixtures, 33.** Two left patterns and a variable and a promotion, three gaps (a space, a line break, a
  comment) and three literals (`0n`, `2n`, `1n+m`), three columns, a comma, controls the seed accepts (`Zero{}`,
  `m`, `Succ{m}`); a numeral in the first column and inside a field stay Unsupported.
- **Mutant.** `row-ignores-numerals`. **Laws.** `numeral_witness`, `numeral_column_is_unsupported`.

## Finding 6 (major): the arity checks had no witness

**Fixed.**

Both deletions the reviewer named survive the round-10 gates: the row-width comparison in the audit (was
`prepare`) and the constructor field count in `validate`. Twenty-one seed-frozen fixtures, each `Invalid check
pattern-arity`, plus three controls: a too-short and a too-long row in a multi-scrutinee match, live and
dead, three columns; a constructor pattern with one field too few or too many, live and dead, at the top, one
level down and as the outer pattern, flat and matrix. Mutants `audit-drops-row-width`,
`audit-drops-dead-row-width`, `validate-drops-constructor-arity` and `validate-drops-nested-arity` each make
their witnesses `Checked`. The generator draws row widths of one too few, one too many and two too many, and
field counts of one, two (correct) and three.

## Finding 7 (pre-existing): a let binder named after a constructor

**Not fixed here: literals-owned.** The literals branch fixes it (`abda3875`). The let site here takes only
the datatype half of the binder rule (`G.promotion`), so merging the constructor half is one call. The generator
never draws it (its let binders come from `LETTABLE`, which excludes constructors and the both-names), and its
token-mutation fuzz reports it and nothing else as a false acceptance (see below).

## Convergence

Each earlier round found new shapes one at a time. This round added three independent searches.

**`fuzz11.py`, 6,100 fixed-seed programs in six families, every one classed:** names (1,300), dead rows (1,300),
gaps (1,200), parenthesized columns (700), widths (700) and layout (900). Binder names come from a declared datatype,
a declared constructor, a name that is both, a datatype and a constructor declared after the def, a function, Base's
names (`String`, `List`, `T`, `Unit`) and plain names, as bare, `+` and erased binders and in lets, at rows,
later columns, fields, nested fields, parameters (also as scrutinee) and type fields, followed by an
annotation, a call or nothing. Dead rows hold nested matches one to three deep, flat and two-column, on a
parameter or a fresh field, after a let, with good and bad rows, and lets with `+` names. Gaps put a space,
line break, comment, comma or nothing between adjacent tokens of a header, row or body, at a random rate or at
exactly one random pair, with Nat, U32, Char and hex literals. Parenthesized columns draw header columns that are
a name, a call `h(a)` or `(a)` and row patterns that are a name, a wildcard, a constructor or `(x)`, live and in an
unreachable row, with the single gap aimed at a `(` half the time and then a line break half the time. Widths and
field counts are off by one both ways. Layout draws case, statement and body columns, marked, erased and split lets,
statements on a let's line and declarations at another column or on a body's line. The final tree on the fixed seed:

| Family | Programs | Seed accepts | Seed rejects | Knot accepts | Knot Invalid | Knot Unsupported |
|---|---|---|---|---|---|---|
| names | 1,300 | 722 | 578 | 722 | 578 | 0 |
| dead | 1,300 | 142 | 1,158 | 134 | 1,025 | 141 |
| gaps | 1,200 | 280 | 920 | 182 | 473 | 545 |
| parens | 700 | 96 | 604 | 37 | 222 | 441 |
| widths | 700 | 188 | 512 | 188 | 512 | 0 |
| layout | 900 | 703 | 197 | 67 | 0 | 833 |
| all | 6,100 | 2,131 | 3,969 | 1,330 | 2,810 | 1,960 |

**0 false acceptances and 0 false Invalid**, and the 1,330 programs both sides accept evaluate to the seed's value.
The full class table (all classes of every family) is in `receipts/round11-sweep.json`. Sensitivity, with the same
programs: the round-10 tip reports **908 false acceptances and 489 false Invalid**, the merge base (main-era code)
65 and 384, and this tree before the parenthesis repair 4 and 4 (all in the parens family). Four further fixed seeds (24,400 programs, offline) also report 0 and 0.

**Exhaustive gap search (`gapsearch.py`, offline).** Eight gaps (a line break, a break and an indent, a comment, a
blank line, a space, a comma, a spaced comma, nothing) between every pair of adjacent tokens of the match region of
43 bases (headers of names, commas, calls and parenthesized terms; row patterns of names, constructors, fields, `+`
marks, Nat literals and parentheses; nested matches in unreachable rows; lets; call and constructor arguments):
6,995 programs (the seed accepts 3,895 and Knot accepts 2,303 of them and answers Unsupported for 1,592; the seed rejects 3,100 and Knot answers Invalid for 2,215 and Unsupported for 885), **0 false acceptances, 0 false Invalid, 0 host failures** (`receipts/round11-gapsearch.json`). It found the parenthesis family before the repair (15 false acceptances and 20 false Invalid in 2,097
programs of eleven bases) and none after.

**Token-mutation fuzz (scratch, not a gate).** The fixtures and generated programs, mutated by a random token or gap
edit inside their match regions (rename to a pool name, insert or delete a gap, duplicate, swap, insert a marker,
shift indentation, insert a numeral), against the seed, the repaired checker and the merge-base checker (to separate
a main-era gap from a branch-introduced one). Nine runs of 6,000, 12,000, 12,000, 12,000, 30,000, 60,000, 100,000,
60,000 and 60,000 mutants (352,000 in all; the ninth on the final tree, the eighth on the tree before the
parenthesis repair) found: the layout shapes of finding 4 that were not in the reviewer's grid (the second frozen
batch); the header terms and numeral arguments (the third batch); two false acceptances of the parenthesis shape (in
the eighth run, and the reason for the gap search); false acceptances that were all a let binder named after a
constructor (finding 7); and the open families below. **The final run, 60,000 mutants on the final tree:** the seed
and Knot agree on 59,846 (4,270 both accept, 4,741 seed accepts and Knot answers Unsupported, 27,302 both reject,
23,533 seed rejects and Knot answers Unsupported); **12 false acceptances, all a let binder named after a
constructor** (finding 7, the literals branch's); 142 false Invalid, of which 128 are also Invalid on the merge base
and 14 are not (12 a def body at column 0, which the frontend gate pins Invalid; one an erased let of a global
function, `Invalid check free-name`; one a lone `+` marker line before `+ w : F = x`, `Invalid parse binding-name`,
Invalid on the round-10 tip too). None is pattern-related, and none is new.

## Open D4 families (seed-accepted, Knot Invalid; none is pattern-related)

Named so that the next reviewer's fuzz does not rediscover them. Each is main-era unless noted: the merge-base checker
reports the same `Invalid` for a program with one scrutinee.

- **A def header's parameters and a type's fields with a line break or extra whitespace** (the literals-layout
  increment's `layout-def-header`). 72 of the 115 programs below.
- **Term suffixes the term parser lacks (fixed in round 12; round 13 names operators `Unsupported parse operator`, other forms `term-form`).** An infix operator (`On{} || Off{}`, `On{} -> Off{}`, `a & b`,
  `a <> b`), a chained call `g(a)(a)`, an index `a[0n]` and `g!(a)` after a complete term. In a discarded body
  or let the seed parses and never checks them; a live one needs a target the program defines (`def Pair`,
  `def Bool.and`, a `Con` constructor). Knot answers `Invalid parse end-of-body` (`expected-` at a let's line
  end, `argument-separator` in an argument list); a lambda and a hole are already `Unsupported term-form`.
  Classification-2 pins `==` and `=>` after a constructor Invalid; nothing pins the infix set. 39 programs below.
- **A def body at column 0** (the frontend gate pins `Invalid parse body-indentation`).
- **A call with fewer arguments than parameters that the seed reads as an unused partial application**
  (`-x = h()`; `Invalid check call-arity`). The checker gate pins it Invalid where the result is used
  (`call-arity.bend`), so only an unused or unannotated let is open.
- **A global function used as a value** (`-v = main`; `Invalid check free-name`; the closures increment).
- **A Nat literal pattern as a let binder at another column** (`0n+v : Flag = ..`; `Invalid parse
  body-indentation`).
- **A `+x0` term in a discarded row** (`case _: +x0`; `Invalid parse expected-=`; fixed in round 12): the parser reads a
  statement. 2 programs below.
- **A constructor line of a type declaration at another column**, found by the last fuzz runs.
- **A lone `+` marker line before another marker** (`+`, break, `+ w : F = x`; `Invalid parse binding-name`): the seed
  reads a repeated promotion, which round 10 answered Unsupported on one line. One program in the final run.
- **Where a multi-scrutinee match is the difference.** The merge base stopped at `Unsupported
  match-scrutinees` before any of these, so a fuzz that labels a program by the merge base's answer calls a
  gap that follows a multi-scrutinee header branch-introduced: the def body at column 0 and the indented `def`
  (now `Unsupported`) were such artefacts, and an infix operator in a discarded row of a two-scrutinee match
  is the one seed-accepted program of the reviewers' probe roots that the merge base answered
  `Unsupported` and this branch answers `Invalid` (`mrun2/m19150`, `fl_Bx->(x0)`).
  **Correction (round 12, [REVIEW-12.md](REVIEW-12.md)): it is a class, not one program.** Every term suffix (an
  infix operator, a chained call, an index, an offload) and every `+name` term after a complete term was `Invalid`
  in a discarded row of a two-scrutinee match, where the merge base answered `Unsupported`; the probe roots held one
  program of the class. Round 12 answers `Unsupported parse term-form` at every site a term ends.

**The reviewers' probe roots, all 48,517 programs without an import line** (`receipts/round11-probescan.json`;
each program is classified by the seed and by three checkers: the round-10 tip, the merge base and this tree):

| | round-10 tip | merge base | this tree |
|---|---|---|---|
| seed rejects, Checked (false acceptance) | 157 | 104 | 57 |
| seed accepts, Invalid (false Invalid) | 254 | 951 | 115 |

All 57 remaining false acceptances are a let binder named after a constructor (finding 7). Of the 115 false
Invalid, 114 are also `Invalid` on the merge base: 72 def headers, 39 term suffixes, 2 `+x0` terms and 2 bodies
at another column (a `match` at another column); the one difference is the operator above.

## Gates

`BEND_NO_TELEMETRY=1 npm run -s gates` on the final code tree (HEAD `137f6cf4`; the runner exports the tree and runs
four gates at a time, on a machine loaded by other sessions, with `KNOT_GATE_TIMEOUT_SCALE=4` for the harness
timeouts): **31 of 31 gates passed** in 1,013 s, summary status `passed`. The runner's per-gate lines:

```
checker: passed (29.13s)
structural: passed (33.27s)
structural-trust: passed (0.35s)
owned-store: passed (7.54s)
flat-store: passed (23.66s)
fields: passed (70.32s)
fields-trust: passed (0.74s)
frontend: passed (77.16s)
census: passed (4.45s)
wasm: passed (69.32s)
wasm-trust: passed (0.74s)
lint:verify: passed (10.40s)
perch-context: passed (47.93s)
recursion: passed (67.10s)
classification: passed (3.46s)
bootstrap: passed (55.69s)
io-host: passed (15.92s)
fields-wasm: passed (125.32s)
io-abi-2: passed (55.92s)
nest: passed (172.02s)
nest-review: passed (189.56s)
selfhost: passed (142.98s)
nest-round4: passed (102.50s)
nest-round3: passed (192.56s)
nest-round6: passed (124.62s)
nest-round7: passed (157.14s)
nest-round8: passed (185.76s)
nest-round9: passed (314.83s)
nest-round10: passed (487.15s)
nest-sweep11: passed (400.02s)
nest-round11: passed (505.34s)
```

Every `src/*PROOF.bend` entry prints `All terms check.` (`PROOF`, `catalog-PROOF`, `check-PROOF`, `fields-PROOF`,
`lowering-PROOF`, `matrix-PROOF`, `recursion-PROOF`, `runtime-PROOF`). `npm run -s gates:verify` (the runner's 20
self-tests) and `npm run -s lint:verify` (168 tests) pass. The receipts of `nest-round11` and `nest-sweep11` were then
produced by direct runs in this worktree (`round11.json`, `round11-sweep.json`); the shared receipts of the older gates
are untouched (their input hashes moved with `parse.bend`, `syntax.bend` and the test scripts; the coordinator refreshes
them after the merge).

## Style preflight

`round11-preflight.txt` records the offline preflight (`node scripts/perch-style.mjs --preflight`, 0 provider
requests): each of the seven changed sources and of the six law and proof files alone, the seven sources together,
and the compiler manifest. **The manifest is the meaningful measure: 20 groups, every composition available, 0
truncated, 0 role-limited, 0 structural blockers** (the largest, `pattern-matrix-laws`, is 46,889 of 48,000 bytes;
`frontend-parsing` 30,339, `frontend-laws` 23,656). Alone, `catalog`, `parse`, `patterns`, `scope` and `syntax`
compose (23,220, 30,339, 41,586, 20,531 and 5,654 bytes); `check`, `matrix`, `LAWS`, `PROOF`, `catalog-LAWS`,
`matrix-LAWS` and `matrix-PROOF` exceed the 48,000-byte whole-file cap as whole files (84,239, 58,415, 48,975,
49,081, 51,470, 105,396 and 68,358; a proof file also names collaborators outside its file), and one to 33
declarations of a file are cut by a helper or file limit. Those are the whole-file limits of the earlier rounds'
selections (a declaration whose context is a large function such as `parse.run` or `check.run`), not manifest
blockers; the groups that read those files in the manifest compose within the cap.

## Remaining for the coordinator

- Live Perch review of the new declarations (`audit`, `sequenced`, `binder`, `promotion`, `hidden`, `visible`,
  `telescope`, `numeral`, `statement`, `closes`, `same_line`, `opens`, `term_start`, `split`, `line_end` and the eighteen
  laws), with
  `--task=tests/compiler-nest/SPEC.md` for the matrix groups and `src/SPEC.md` for the frontend groups.
- Refresh the receipts after merge (the earlier nest gates, whose input hashes moved, `selfhost` and the shared
  receipts). Sign off on the re-anchored mutants and the SPEC.md, manifest and gate changes above.
- Reconcile with the literals branch: its let-binder constructor rule joins `G.promotion` at the let site and
  in the audit's let case; its layout increment owns the def-header list continuation.
- The open D4 families above, and `gapsearch.py` as a standing tool (grow its bases when a review names a token class
  they lack).
- Both D21 laws are unchanged and remain required open obligations.
