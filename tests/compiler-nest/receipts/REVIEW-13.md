# Nest review round 13

This round answers review round 12 of the fix of round 11 (`nest-r12-findings`: four confirmed majors, and minors from
the finder, the scope, gates and semantics lenses). Findings 1 to 3 are **fixed**; finding 4 is **bounded** as the
coordinator ruled (the core representation does not change in this round). None is disputed. The repairs follow the
coordinator's code ruling (below), and every frozen pin that the ruling moves was amended in a commit of its own, from
the seed, before the repair.

| Finding | Disposition |
|---|---|
| 1 (major, D4): a spaced `+`, `-`, `++`, `->` (and `-+`) at the start of the line after a let's value, in a discarded row of `match x y:`, answers `Invalid parse detached-marker` | **Fixed as a class.** `Invalid detached-marker` only for the marker gap (a name, then `=` or `:`); every other operand, and every other infix token at that line start, on the let's line and after a header's scrutinee, is `Unsupported parse operator`. `src/LAWS.bend::detached_marker` restated and proved; the Unsupported outcome is its own law. The "main-era" label is dropped for the two-scrutinee shape |
| 2 (major, D4): a touching `+name`, a glued `x+y` or a `?` hole as the next call argument answers `Invalid argument-separator` | **Fixed.** `+name` and `?name` are `Unsupported parse term-form`, the glued `x+y` `Unsupported parse operator`, in expression argument lists only; `@`, a backslash, `-name`, a closer and a pattern's fields keep `Invalid argument-separator` (the seed rejects them: the SPEC and REVIEW-12 wording is corrected). `argspace-promoted-call` amended |
| 3 (major, D4): an arm body or a later statement that starts with `(`, `[`, a numeral or `?` at another column answers `Invalid body-indentation` | **Fixed.** `S.body_start` (the statement starts plus these) in `StartBody` and in `BodyAt`'s other-column branch; `)`, `,`, `:`, `=`, `case`, `def`, `type`, `!`, `@` and a backslash stay Invalid. The reviewer's grid is frozen from the seed (684 cells); SPEC line 198 and REVIEW-11 and REVIEW-12 are corrected |
| 4 (major, resource): a terminal default is copied into every remaining constructor arm, so the core and the module grow as ctors^columns and dd5x5 crashes the Bun lane, dd9x5 takes 45 s and 900 MB, dd10x5 never finishes | **Bounded.** A source match's core may not exceed 65,536 nodes, every copy counted: `Exhausted check budget` before any consumer reads it. dd5x5 (7,811 nodes) is Accepted; dd7x5, dd9x5 and dd10x5 are refused in milliseconds. The Bun lane's fault on a large module is `Exhausted (host)` in the nest gates. `tests/compiler-nest/SPEC.md`'s "shared" is corrected |

| Commit | Change |
|---|---|
| `a2b78f2b`, `6e88ea7a`, `110bd814`, `5fee2aa2` | The four amendments of frozen pins, each before the repair: `argspace-promoted-call` (Invalid to `term-form`), `argspace-operator-call` (`term-form` to `operator`), three round-11 header pins, 52 round-12 pins. Each cites the seed observation and the ruling |
| `b0e75fb4`, `43ae3d07`, `f53bfca8`, `11d7b987` | D7 freezes from the seed before the repairs: 210 fixtures, the 684-cell grid and the 64-form zoo (`round13_seed.py`) |
| `298184ea` | Findings 1 to 3: `P.form`, `P.gap`, `P.abuts`, `S.body_start` and their sites; ten laws; the eight re-anchored mutants; `fuzz12.py` draws the open families |
| `02cd3647` | Finding 4: `K.core_budget`, `K.weight`, `K.budgeted`; two laws |
| `33f17c10` | The Bun lane's fault as `Exhausted (host)` (`check.py`, `review.py`) |
| `f6a19c1b` | The `nest-round13` gate and its registration |
| `9645422d` | Resumed verification: remove the duplicate helper; add the brace-only mutant, syntax/type-checked falsification driver and corpus-budget scan; approve every census declaration; record preflight and budget receipts |
| the final report commit | Round-13 gate receipt, amended-pin audit, convergence and exact per-gate results; Perch log and nest state |

The existing commits retain their historical trailers. All commits from the resumed Codex session use
`Co-Authored-By: GPT-6.1 Sol <noreply@openai.com>`.

## The coordinator's code ruling, and the pins it moved

The two branches (nest and literals-integ) answered the same unmodeled shapes with different codes. The ruling settles one
vocabulary: an operator token that continues a term is `Unsupported parse operator`, the seed's operator sugar that Knot does
not model (a live row rejects it "for its type", which is no syntax claim Knot can make); any other unmodeled term form is
`Unsupported parse term-form`; `Invalid` stays only where the seed rejects for the syntactic reason the diagnostic names.
`P.form(ts)` is the whole rule: `operator` when `P.operator(ts)`, else `term-form`; each site that answered `term-form`
for a term suffix now calls it (a body, a let's value, an expression argument, a scrutinee, a line's start).

**57 frozen pins moved, each with its seed observation unchanged** (`round10_seed.py`, `round11_seed.py` and
`round12_seed.py` without `--write` report no differences after every amendment):

- `argspace-promoted-call` (round 10): `Invalid parse argument-separator` becomes `Unsupported parse term-form`. The seed rejects
  the live body only for its scope ("expected : a bound variable", with a Context section) and accepts `two(a +b)` in a discarded
  row (`F0{}`, exit 0).
- `argspace-operator-call` (round 10): `term-form` becomes `operator`. "a type for this operator" in a live row; the same text is
  accepted in a discarded one.
- `header-plus-dead`, `header-minus-dead`, `header-two-plus-dead` (round 11): `term-form` becomes `operator` (`match a + b:`,
  `a - b`, `a b + a` in a discarded row: the seed prints `Off{}`).
- 52 round-12 fixtures whose suffix is a token of the infix table: 24 `suffix-*-dead`, four each for the own-line body, the single
  scrutinee, the let value and the argument (`or`, `amp`, `diamond`, `arrow`), four live rows and two defined-operator rows,
  and six line-start continuations (`|| a`, `<= a`, `>= a`). One of them, `suffix-arrow-dead-let`, was
  `same-line-statement`: `u : Flag = On{} -> Off{}` continues the value with an operator and starts no statement. The calls,
  indexes, offloads `!(`, lambdas `=>` and `+name` terms of the same round keep `term-form`.

Nothing else moved: the pre-repair tip (`8b5d2154`)'s 972 frozen fixtures run against the repaired checker give exactly these 57 differences and
no other (`.local/r13/movedpins.py`).

**Reading of the ruling for the reviewer to confirm.** The ruling's list names `+`, `-`, `++` and `->`; the vocabulary is
applied to every token of the seed's infix table (`*`, `<=`, `&&`, `.|.`, ...), because the parser sees no difference between
them and one code per site is the point of settling it. A narrower reading would keep `term-form` for the tokens the list does
not name: `P.form` and three literals (`BodyAt`, `MatchTail`, `line_end`) are all that would change, and the amended pins go
back with them.

## Finding 1 (major, D4): an operator that starts the line after a let's value

### The seed's rule

After a let's value the operator loop of `parse_term_ops` reads any operator of its infix table, spaced or on the next line, so
`v = x`, `+ y`, `v` is one value `x + y` and one statement `v`. `+` and `-` touching a name are markers. A statement cannot
start at the `=` or `:` that follows the operand, so `+ u : F = ..` is a syntax error: that pair, and only that, is what the
frozen round-10 `marker-gap` fixtures pin.

### The repair

`BodyAt`, at the let's column, after a let (`first` is false): a spaced `+` or `-` that touches no name is `Invalid parse
detached-marker` when `P.gap` holds of the tokens after it (a name, then `=` or `:`, after any line breaks), else `Unsupported
parse operator`; any other infix token at that line start is `operator`. `line_end` (a let's value followed on its line by an
operator) tries `operator` before the statement test, so `u : Flag = x + y` is `operator` and `u : Flag = x +y` stays
`same-line-statement`. `MatchTail` answers `operator` for one after a scrutinee. The continuation test of `BindingStart` is
dropped: a let's column reaches `BodyAt` first, so the test could only fire for a body's first token, where the seed rejects
it, and `Invalid binding-name` is the more precise answer. A doubled sign (`-- y`, `+- y`) is rejected by the seed ("`-`
followed by a space starts no term") and is now `operator`: sound, and less precise than the `detached-marker` it was.

`src/LAWS.bend`: `detached_marker` states `Invalid` with a `:` after the operand; `spaced_operator_after_a_let` states
`Unsupported operator` with a line break after it; both normalize over an abstract tail. `suffix_ends_a_body` and
`suffix_ends_a_let` state `operator` for `|`, and `call_ends_a_body` and `call_ends_a_let` state `term-form` for `(`.

### Evidence

- **Fixtures (D7), 65** (`letop-*`): the five tokens of the finding and 18 more infix tokens (`*`, `/`, `%`, `<`, `>`, `<=`, `>=`,
  `<>`, `&`, `|`, `&&`, `||`, `<<`, `>>`, `.|.`, `.^.`, `.&.`, `<&>`) at the start of the line after a let in a discarded row, typed
  and untyped lets, two lets, three scrutinees, one scrutinee, a blank line and a comment between, operands that are a call or a
  constructor, an operator on the let's line and after a header, the live and flat twins the seed rejects for the operator's type
  (`expected : Type` for `->`), nine marker-gap programs that stay `Invalid detached-marker`, `==` and `!=` that stay `Invalid
  binding-name`, `=>` (`term-form`), and four programs the seed rejects that answer `operator` (a doubled sign, an operator with no
  operand). 47 of the fixtures fail on the pre-repair tip (`8b5d2154`).
- **Mutants:** `marker-gap-widened`, `marker-gap-dropped`, `marker-gap-ignores-line-breaks`, `operator-code-term-form`,
  `line-operator-term-form`, `same-line-operator-statement`, `header-operator-term-form`.

## Finding 2 (major, D4): `+name`, a glued `x+y` and a hole after an argument

### The seed's rule

After an expression argument `x +y` and the glued `x+y` are the same tokens to the seed: `x`, then the promoted term `+y` (the
operator loop returns at a `+` or `-` that a name follows). `?y` is a hole. The seed rejects them in a live row for their scope or
type ("expected : a bound variable", "expected : Flag") and accepts them in a discarded one. `@y`, `\y`, `-y` and `$y` are no term.

### The repair

`Arguments`, after an expression argument (never in a pattern): a touching `+name` is `Unsupported term-form`, or `operator` when
the `+` also touches the argument's last token (`P.abuts` walks the argument's tokens to the one before the `+`; it runs only when
this shape occurs, so the parse pays nothing otherwise). `ListTail` answers `term-form` for a hole. `@`, a backslash, `-name`, a
closer and a pattern's fields keep `Invalid argument-separator`: the seed rejects each, and a pattern is always validated.
Laws: `argument_promotion_is_unsupported`, `glued_argument_operator_is_unsupported`, `argument_hole_is_unsupported`,
`argument_at_is_invalid`.

### Evidence

- **Fixtures (D7), 40** (`argterm-*`): `h(x +y)`, `h(x +y, x)`, `h(x, k(x +y))`, `h(k(x) +y)`, `h(On{} +y)`, `h(x +y +x)`, the hole forms,
  the glued forms (`h(x+y)`, after a call, after a constructor, nested, before and after a comma, right-spaced), the exact body of
  `argspace-promoted-call` in a discarded row, single-scrutinee twins, the live twins, and seven controls the seed rejects for the
  syntax (`@`, backslash, `-y`, `$y`, a closer, `= y`). 22 fixtures fail on the pre-repair tip (`8b5d2154`).
- **Mutants:** `argument-promotion-invalid`, `argument-glue-lost`, `argument-glue-always`, `argument-hole-invalid`,
  `argument-at-unsupported`, `argument-erased-marker-unsupported`, `argument-pattern-promotion-unsupported`.

## Finding 3 (major, D4): a term at another column

### The repair

The seed's `parse_body` takes any term as a body with no first-token restriction. `S.body_start(t)` is `S.statement(t)` (a name,
`match`, `+`, `-`) or `(`, `[`, a numeral or `?`. `StartBody` (an arm body on the line after its `case`, at the case's column or
below) and the other-column branch of `BodyAt` (a later statement) answer `Unsupported body-indentation` for it. `S.statement` keeps
its other uses (a statement on a let's line). `)`, `,`, `:`, `=`, `case`, `def`, `type`, `!`, `@` and a backslash start no term and
stay `Invalid body-indentation`. Laws `body_start_witness`, `arm_body_may_start_with_a_term`, `closer_starts_no_body`.

### Evidence

- **The grid (D7), 684 cells.** The reviewer's `ind4.py` draws 57 terms at columns 4, 2 and 0, in one- and two-scrutinee
  matches, as an arm body and as a statement after a let (the finding says 720; the script's list has 57 terms). The pinned seed
  accepts 246 cells and rejects 438. Frozen by source hash with the seed's answer (`round13-grid.json`). Knot's reviewed
  outcome is fixed for the class (`Unsupported body-indentation`: 222 seed-accepted cells), for the precision controls (`Invalid
  body-indentation`), and for the lexer's answers (24 cells with `"x"` or `'c'`); the rest are constrained. The gate runs every
  cell in both lanes: 0 seed-accepted cells Invalid, 0 rejected cells Accepted. On the pre-repair tip (`8b5d2154`) 118 seed-accepted cells are
  Invalid.
- **Fixtures, 96:** the reviewer's repros (`paren-body-multi`, `paren-stmt-multi` and their single-scrutinee twins) and dead-row
  variants with `[a]`, `[]`, `0n`, `1n`, `0` and `?x`, and 40 controls.
- **Mutants:** `body-start-paren-invalid`, `body-start-bracket-invalid`, `body-start-numeral-invalid`, `body-start-hole-invalid`,
  `body-start-bang-unsupported`, `arm-body-start-statement-only`, `later-statement-statement-only`.

## Finding 4 (major, resource): the default copies

### The cause

`decision_arms` coalesces a binary spine into one core `Case`. A terminal default (a `Decision` whose negative branch is no `Case` of
the same level) is checked once and placed in every remaining constructor's `Branch`: core `Case` has no default arm, so the
copies are real to every consumer of the core (the display, the evaluator, both emitters, the image encoder), which read the tree.
Memory shares the copies; the readers do not. The 4,096-visit quota counts matrix visits: dd5x5 visits 32.

### The bound

`K.budgeted` measures the finished core of every source match with `K.weight`: a worklist that charges one unit per node and
pushes each node's children, so that a shared default is read once per copy, and stops when the budget is spent (it never visits
more than the budget plus one nodes). More than `K.core_budget()` = 65,536 is `Exhausted check budget`, before any consumer
reads the tree. A nested match counts inside the match that holds it, so a function's core is at most the budget for each source match
it holds plus linear structure. The count is exact: dd5x5's core is 781 cases, 3,905 branches and 3,125 leaves, 7,811, and a checker
built with the budget 7,810 refuses it while one built with 7,811 accepts it. Laws `weight_counts_every_node` and
`weight_stops_when_spent`.

**Why 65,536.** The fresh corpus comparison below checks all 1,771 pre-round-13 files against a 1,048,576-node control;
no outcome or accepted core observation changes. Earlier exploratory quota sweeps (`.local/r13/corpus-{b,c,d}.json`)
found no accepted-file difference at bounds of 128 or greater; their small-bound failures included
`wide-type-depth3.bend` and `self-shape.bend`. **0 pre-round-13 corpus files newly hit the budget.** **No `src/*.bend` file reaches a matrix**: 35 of 35 stop in the
lexer (a string literal: `Unsupported lex literal`) or in the parser (`Unsupported parse declaration-form`), so none is Exhausted; the
budget cannot be measured against them until literals and generics land. The largest match of Knot's own sources is
`parse.bend::run` (4,932 tokens, 21 arms), then `check.bend::run` (2,074) and `wasm.bend::lower` (1,620); these are token counts, not
checked core-size measurements. The 65,536 budget is 4,096 x 16, the visit quota with sixteen nodes per leaf. This round's new controls join
the corpus: the accepted `default-dd5x5` core (7,811) is now its largest.

### Evidence

- **Fixtures, 9** (`default-*`): the reviewer's dd5x5 and dd9x5 and dd10x5, dd4x5, dd7x5, dd10x3, a dd7x4 whose bodies are calls of
  three nodes, and dd4x5 and dd9x5 with the catch-all row first. The seed prints `On{}` for each in milliseconds. dd4x5, dd4x5-first and dd5x5
  are Accepted (dd5x5's module is 34,434 bytes: in the Bun lane the seed computes it and then faults, which the gates classify
  as `Exhausted (host)`); the other six are `Exhausted check budget`. On the pre-repair tip (`8b5d2154`) dd10x5 does not finish in 120 s; on the
  repaired checker it answers in 0.04 s (native) and 1 s (Bun).
- **The D21 obligation** (an irrefutable first row lowers to that row's body) is a second cost model of the same kind:
  `default-dd9x5-first`, the seed-accepted matrix with nine columns, five constructors per column and the catch-all row first, exhausts the core budget as `matrix-work`
  exhausts the visit quota. The contract records it beside the first one; the obligation stays required and open.
- **Mutants:** `budget-dropped`, `budget-counts-no-arms`, `budget-counts-no-bodies`.

Fresh corpus measurement (`round13-budget-corpus.json`, from the committed `budget_corpus.py` driver):
**1,981 files**, including **1,771 pre-round-13 files** compared under the production 65,536-node budget and
a 1,048,576-node control built from the same sources. **0 pre-round-13 outcomes or accepted core observations change.** The
six new stress fixtures answer `Exhausted check budget` (the seventh corpus exhaustion is the existing matrix-visit control); all other round-13 fixtures have their frozen outcomes.
Among the **35 top-level `src/*.bend` files**, **0 Exhausted, 0 Checked**: 28 stop at `Unsupported lex literal`,
7 at `Unsupported parse declaration-form`. Thus no compiler source is newly starved, but their core-size budget
fitness cannot yet be established. Literals, generics and modules must land before that compiler-wide measurement.

## Minor findings

Taken (cheap): a fresh corpus-budget comparison and the D9 duplicate `matrix.bend::named` (a copy of `catalog.bend::named`), `tests/perch-context/check.py`'s unscaled
120 s guard (now scaled by `KNOT_GATE_TIMEOUT_SCALE`, like the other gate scripts), the stale receipts README, and the REVIEW-12
misdescriptions (below).

Not taken, with the reason:

- The check-phase widening (`match c() y:`, `-v = k`, `-v = h()`): the flat forms are Invalid on main, and the answer belongs to
  closures and partial application; it needs the coordinator's ruling (Unsupported, or reviewed `D4_GAPS` rows with owners).
  Listed under "Remaining".
- 3281c22e moved a frozen expectation after the repair (D7 order inverted): the coordinator ratifies it, or has it replayed
  amendment-first. This round's four amendments each precede their repair.
- 6a2422f7's edit of `return_type_application` (a classify-owned law): ratify at merge; nothing to change.
- 1c4f48e4's census message: nothing to change on the branch; this round's census commit message lists one line per approved
  declaration.
- Eleven of nest's twelve receipts record stale input hashes: refresh after merge (`npm run gates:refresh`); the REVIEW-12 sentence
  ("semantic ones record build and input hashes and the argv path") is wrong: thirteen of the fourteen nest receipts differ in
  content since the round-3 commit (the reviewer's `drift.py` attributes each difference to a commit). The receipts of the
  earlier nest gates are not refreshed here.
- The full suite's cost and its thin headroom under the 1,800 s cap: `nest-round13` builds its mutants four at a time and
  does its grid and zoo in eight-way pools; sharing builds across the nest gates is a larger change and is not done.
- The previously untracked falsification driver is now committed as `tests/compiler-nest/falsify.py`, with both
  the ten round-12 mutants and fifteen round-13 mutants. It rejects syntax/type failures as semantic evidence.
- The original round-6 `touch-past-one` kill retains its historical arrow side effect. Round 13 adds
  `brace-gap-one-byte` at the brace call site alone: it admits the seed-rejected `On {}` in `w1-flat-space`
  while leaving return arrows and touching braces unchanged. The new gate kills it in both lanes.
- The total `catalog.datatype` wrapper is retained because the existing `empty_datatype` law observes it;
  removing that proof surface is unnecessary for this repair.

## Convergence

Both differential generators pass on the full runner snapshot. Exact class and family coverage,
including every outcome count, is preserved in [round13-gates.json](round13-gates.json).

| Generator | Programs | Families | Classes | Seed Accepted / Invalid | Knot Accepted / Invalid / Unsupported | False acceptances | False Invalid | Evaluator values |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| round 11 (`fuzz11.py`) | 6100 | 6 | 330 | 2131 / 3969 | 1330 / 2810 / 1960 | 0 | 0 | 1330 |
| round 12 (`fuzz12.py`, widened) | 3000 | 3 | 295 | 1265 / 1735 | 647 / 1211 / 1142 | 0 | 0 | 647 |

| Generator | Family | Programs |
| --- | --- | ---: |
| round 11 | `dead` | 1300 |
| round 11 | `gaps` | 1200 |
| round 11 | `layout` | 900 |
| round 11 | `names` | 1300 |
| round 11 | `parens` | 700 |
| round 11 | `widths` | 700 |
| round 12 | `plus` | 1500 |
| round 12 | `start` | 400 |
| round 12 | `suffix` | 1100 |

The widened round-12 draw includes operators after a let across a line break, touching `+name`,
glued `x+y` and holes after expression arguments, and term openers at another column, with seed-rejected
precision controls. These are tested as source programs against the pinned seed and both compiler lanes.

The frozen **684-cell grid** and **64-form zoo** also pass in both lanes: **0 seed-accepted Invalid**,
**0 seed-rejected Accepted**, no lane disagreement and no unclassified host failure. Their exact joint
outcome distributions follow; the gate enforces the grid's reviewed diagnostic pins separately.

| Control | Seed / Knot outcome | Cells |
| --- | --- | ---: |
| grid | `seed-Accepted knot-Unsupported lex literal` | 24 |
| grid | `seed-Accepted knot-Unsupported parse body-indentation` | 222 |
| grid | `seed-Rejected knot-Invalid parse body-indentation` | 306 |
| grid | `seed-Rejected knot-Unsupported lex non-ascii` | 12 |
| grid | `seed-Rejected knot-Unsupported parse body-indentation` | 78 |
| grid | `seed-Rejected knot-Unsupported parse operator` | 36 |
| grid | `seed-Rejected knot-Unsupported parse term-form` | 6 |
| zoo | `seed-Accepted knot-Accepted` | 11 |
| zoo | `seed-Accepted knot-Unsupported lex literal` | 2 |
| zoo | `seed-Accepted knot-Unsupported lex whitespace` | 1 |
| zoo | `seed-Accepted knot-Unsupported parse destructuring-binding` | 1 |
| zoo | `seed-Accepted knot-Unsupported parse line-break` | 1 |
| zoo | `seed-Accepted knot-Unsupported parse operator` | 9 |
| zoo | `seed-Accepted knot-Unsupported parse term-form` | 12 |
| zoo | `seed-Rejected knot-Invalid lex name` | 2 |
| zoo | `seed-Rejected knot-Invalid parse body-indentation` | 1 |
| zoo | `seed-Rejected knot-Invalid parse detached-brace` | 1 |
| zoo | `seed-Rejected knot-Invalid parse end-of-body` | 10 |
| zoo | `seed-Rejected knot-Unsupported lex non-ascii` | 2 |
| zoo | `seed-Rejected knot-Unsupported parse binding-type` | 1 |
| zoo | `seed-Rejected knot-Unsupported parse operator` | 1 |
| zoo | `seed-Rejected knot-Unsupported parse pattern-or-indentation` | 1 |
| zoo | `seed-Rejected knot-Unsupported parse term-form` | 8 |

## Gates

`BEND_NO_TELEMETRY=1 npm run -s gates` **exit 0, 33/33 registered gates passed**.
Measured runner wall time: **3178.59 s**. Source/gate code is checkpoint `9645422d`;
the final commit adds documentation corrections and this increment's receipts. [round13-gates.json](round13-gates.json)
preserves every runner count without abbreviation, including the finding histograms and errno cases.

| Gate | Result | Exact counts (finding histograms in the JSON audit) | Measured seconds |
| --- | --- | --- | ---: |
| `frontend` | passed, exit 0 | boundaries=24; fixtures=14; lane_observations=28; mutants=4 | 289.64 |
| `checker` | passed, exit 0 | bound_observations=16; bounds=2; budgets=10; fixtures=49; lane_observations=98; mutants=7 | 119.90 |
| `structural` | passed, exit 0 | bounds=4; fixtures=16; lane_observations=64; mutants=7 | 153.77 |
| `fields` | passed, exit 0 | bound_observations=12; bounds=2; budgets=36; fixtures=40; host_boundaries=6; lane_observations=240; mutants=9 | 268.81 |
| `wasm` | passed, exit 0 | boundaries=44; execution_lanes=2; fixtures=25; mutants=7; reference_calls=90; rejects=62 | 183.38 |
| `wasm-trust` | passed, exit 0 | entries=3; proof_holes=0 | 2.41 |
| `fields-trust` | passed, exit 0 | entries=4; proof_holes=0 | 2.47 |
| `structural-trust` | passed, exit 0 | entries=2; proof_holes=0 | 1.65 |
| `owned-store` | passed, exit 0 | cases=3532; execution_lanes=2; literal_witnesses=15; mutants=6 | 26.52 |
| `flat-store` | passed, exit 0 | bun={"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621}; mutants=9; native={"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621} | 58.08 |
| `recursion` | passed, exit 0 | fixtures=19; mutants=3 | 197.72 |
| `fields-wasm` | passed, exit 0 | boundaries=30; fixtures=8; mutants=4 | 389.01 |
| `census` | passed, exit 0 | classes=41; declarations=876; files=35 | 14.54 |
| `perch-context` | passed, exit 0 | fixtures=33; mutants=8 | 88.49 |
| `lint:verify` | passed, exit 0 | law_rules=8; tests=168 | 16.05 |
| `bootstrap` | passed, exit 0 | corpus=1981; mutants=54; reached=2; stages=8 | 118.02 |
| `classification` | passed, exit 0 | fixtures=17; mutants=6 | 8.53 |
| `nest` | passed, exit 0 | accepted_books=25; boundaries=24; boundary_observations=24; check_observations=76; enum_hash_checks=100; evaluation_values=386; fixtures=38; matched_frozen_outcomes=38; mutants=6; rejected_phase_observations=78; seed_entry_calls=174; seed_fixtures=40; semantic_kills=12; unmet_frozen_outcomes=2; unmet_phase_observations=12; wasm_values=386 | 600.03 |
| `nest-review` | passed, exit 0 | accepted_books=15; check_observations=58; evaluator_values=98; fixtures=29; fuzz_evaluator_values=221; fuzz_false_acceptances=0; fuzz_false_invalid=0; fuzz_programs=3000; mutants=7; rejected_phase_observations=112; seed_calls=49; seed_fixtures=29; semantic_kills=14; wasm_values=98 | 689.30 |
| `io-host` | passed, exit 0 | cli_runs=6; conformance_runs=86; errno controls=6; fixtures=20; host_boundaries=22; mutants=6; review={"empty_write":4,"mutants":3,"oracle_controls":14,"secret_paths":21,"seed_runs":12}; seed_fixtures=40; seed_runs=109; stress={"left_binds":100000,"right_binds":100000} | 19.27 |
| `io-abi-2` | passed, exit 0 | case_mode=insensitive; fixtures=43; host_boundaries=25; mutants=5; mutants_killed=5; parity=153; read_observations=21; reference_observations=64; seed_exhausted=2; seed_observations=61 | 112.84 |
| `selfhost` | passed, exit 0 | blocked=63; cases=65; d4_gaps=1; judge_mutants=20; mutants=3; passed=2 | 564.08 |
| `nest-round3` | passed, exit 0 | accepted_books=32; check_observations=122; evaluator_values=164; fixtures=61; mutants=11; rejected_phase_observations=232; seed_calls=82; seed_fixtures=61; semantic_kills=22; wasm_values=164 | 860.79 |
| `nest-round4` | passed, exit 0 | accepted_books=8; check_observations=28; evaluator_values=64; fixtures=14; mutants=4; rejected_phase_observations=48; seed_calls=32; seed_fixtures=14; semantic_kills=8; wasm_values=64 | 477.98 |
| `nest-round6` | passed, exit 0 | accepted_books=11; check_observations=70; evaluator_values=118; fixtures=35; mutants=5; rejected_phase_observations=192; seed_calls=59; seed_fixtures=35; semantic_kills=10; wasm_values=118 | 471.10 |
| `nest-round7` | passed, exit 0 | accepted_books=20; check_observations=70; evaluator_values=268; fixtures=35; generated_evaluator_values=1836; generated_false_acceptances=0; generated_false_invalid=0; generated_programs=1500; generated_seed_outcomes={"Accepted":780,"Invalid":720}; mutants=3; rejected_phase_observations=120; seed_calls=134; seed_fixtures=35; semantic_kills=6; wasm_values=268 | 425.80 |
| `nest-round8` | passed, exit 0 | accepted_books=21; check_observations=74; evaluator_values=292; fixtures=37; generated_evaluator_values=375; generated_false_acceptances=0; generated_false_invalid=0; generated_knot_outcomes={"Accepted":1148,"Invalid":1796,"Unsupported":56}; generated_programs=3000; generated_promotes_type=1334; generated_seed_outcomes={"Accepted":1161,"Invalid":1839}; mutants=5; rejected_phase_observations=128; seed_calls=150; seed_fixtures=37; semantic_kills=10; wasm_values=292 | 358.81 |
| `nest-round9` | passed, exit 0 | accepted_books=18; check_observations=160; evaluator_values=188; fixtures=80; mutants=12; rejected_phase_observations=496; seed_calls=111; seed_fixtures=80; semantic_kills=24; wasm_values=188 | 503.81 |
| `nest-round10` | passed, exit 0 | accepted_books=43; check_observations=304; evaluator_values=686; fixtures=152; mutants=22; rejected_phase_observations=872; seed_calls=624; seed_fixtures=152; semantic_kills=44; wasm_values=686 | 1046.02 |
| `nest-round11` | passed, exit 0 | accepted_books=62; check_observations=660; evaluator_values=656; fixtures=330; mutants=23; rejected_phase_observations=2144; seed_calls=328; seed_fixtures=330; semantic_kills=46; wasm_values=656 | 1203.54 |
| `nest-sweep11` | passed, exit 0 | evaluator_values=1330; false_acceptances=0; false_invalid=0; fixtures=0; knot_outcomes={"Accepted":1330,"Invalid":2810,"Unsupported":1960}; mutants=18; programs=6100; seed_outcomes={"Accepted":2131,"Invalid":3969}; semantic_kills=36 | 947.06 |
| `nest-round12` | passed, exit 0 | accepted_books=23; check_observations=322; evaluator_values=458; false_acceptances=0; false_invalid=0; fixtures=161; knot_outcomes={"Accepted":647,"Invalid":1211,"Unsupported":1142}; mutants=26; programs=3000; rejected_phase_observations=1104; seed_calls=229; seed_fixtures=161; seed_outcomes={"Accepted":1265,"Invalid":1735}; semantic_kills=52; sweep_evaluator_values=647; wasm_values=458 | 1121.57 |
| `nest-round13` | passed, exit 0 | accepted_books=3; check_observations=420; evaluator_values=6; fixtures=210; grid_cells=684; host_exhausted_modules=1; mutants=25; rejected_phase_observations=1656; seed_calls=13; seed_fixtures=210; semantic_kills=50; wasm_values=5; zoo_forms=64 | 422.27 |

The new gate checks **210 frozen fixtures**, **420 check observations**,
**1656 rejected-phase observations**, **3 accepted books**,
**6 evaluator values**, **5 Wasm values**, and **25 type-checked semantic mutants**
(**50 kills**, one per compiler lane). The frozen corpus records **13 seed calls**;
seed acceptance of an unmodeled form does not count as an accepted Knot book.
**1 Bun module compile** is classified `Exhausted (host)`; its native Wasm lane still passes.
All **eight** `src/*PROOF.bend` entry points print `All terms check.`. The law falsification driver separately
type-checks and falsifies **10/10 round-12** and **15/15 round-13** mutants; syntax/type failures count as neither.

`npm run -s gates:verify`: **21 tests, OK, exit 0**. `npm run -s census:check`: **current, exit 0**.
All changed Python modules parse; the staged diff has no whitespace errors.

Fresh runner receipt drift: **64 identical**, **30 semantic**, **9 volatile-only**.
Semantic drift includes changed observations, counts and mutant effects alongside source hashes.
Only `round13.json` is copied back from the runner; shared receipts retain their historical inputs for
the coordinator to refresh after merge. The corpus-budget, falsification and preflight receipts are new
increment-owned evidence, not refreshed shared receipts.

## Style preflight

`round13-preflight.txt` records all eight materially changed Bend files, each with
`--task=tests/compiler-nest/SPEC.md`, and the full manifest. No provider calls or `.env` reads occurred.

| Target | Truncated units | Structural blockers | Exit |
| --- | ---: | ---: | ---: |
| `src/parse.bend` | 8 | 8 | 3 |
| `src/syntax.bend` | 2 | 2 | 3 |
| `src/LAWS.bend` | 36 | 37 | 3 |
| `src/PROOF.bend` | 2 | 3 | 3 |
| `src/check.bend` | 11 | 12 | 3 |
| `src/check-LAWS.bend` | 1 | 2 | 3 |
| `src/check-PROOF.bend` | 0 | 1 | 3 |
| `src/matrix.bend` | 4 | 5 | 3 |

Manifest mode: **20/20 groups completed, 1,426 declaration contexts, 0 structural blockers**, all 20
compositions available, exit 0. `pattern-matrix-laws` remains at 47,886/48,000 bytes (114 bytes of headroom).
Per-file blockers require bounded manifest groups for live review; they do not establish a style pass.
Conceptual compression, Delight, memetic identity, Anticipation and Payoff are **unrated**. Live ratings and
semantic Perch review are coordinator-only and remain outstanding.

## Remaining for the coordinator

- Live Perch review of the new declarations (`form`, `abuts`, `gap` in `src/parse.bend`; `body_start` in `src/syntax.bend`;
  `children`, `weight`, `budgeted`, `core_budget` in `src/check.bend`) and the twelve laws, with `--task=tests/compiler-nest/SPEC.md`
  for the matrix groups and `src/SPEC.md` for the frontend groups.
- Refresh the receipts after merge (the earlier nest gates), and sign off on the amendments above and on the reading of the ruling.
- Reconcile with literals-integ: it will re-merge this tip, so `P.form` and its sites are the vocabulary; a let binder named after a
  constructor stays literals'; the def-header and type-field line breaks stay literals-layout's.
- The open D4 families: `match c():` and the check-phase widening above, the def body at column 0, partial application, a global
  function as a value, a Nat literal as a let binder at another column, a constructor line of a type declaration at another column.
  Both D21 laws stay open.
- The core representation (a default arm in core, the evaluator, both emitters, the image encoder and the VM track) is queued as
  its own increment; the budget stands until then.

## Every amended pin and its unchanged seed observation

| Round | Fixture | Amendment | Pinned seed observation |
| --- | --- | --- | --- |
| 10 | `argspace-operator-call` | Unsupported parse term-form → Unsupported parse operator | Rejected: a type for this operator (write (a + b : Nat)) |
| 10 | `argspace-promoted-call` | Invalid parse argument-separator → Unsupported parse term-form | Rejected: a bound variable |
| 11 | `header-minus-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: Off{} |
| 11 | `header-plus-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: Off{} |
| 11 | `header-two-plus-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: Off{} |
| 12 | `suffix-add-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-amp-dead-arg` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-amp-dead-let` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-amp-dead-own` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-amp-dead-single` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-amp-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-amp-defined` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-amp-live` | Unsupported parse term-form → Unsupported parse operator | Rejected: a defined name |
| 12 | `suffix-and-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-append-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-arrow-dead-arg` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-arrow-dead-let` | Unsupported parse same-line-statement → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-arrow-dead-own` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-arrow-dead-single` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-arrow-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-arrow-live` | Unsupported parse term-form → Unsupported parse operator | Rejected: Type |
| 12 | `suffix-bar-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-call-op-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-cont-left` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-cont-let-deeper` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-cont-let-ge` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-cont-let-le` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-cont-let-margin` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-cont-margin` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-dand-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-diamond-dead-arg` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-diamond-dead-let` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-diamond-dead-own` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-diamond-dead-single` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-diamond-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-diamond-live` | Unsupported parse term-form → Unsupported parse operator | Rejected: a declared constructor (Flag declares Off, On) |
| 12 | `suffix-div-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-dor-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-dxor-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-ge-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-gt-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-le-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-lt-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-lt-glue-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-min-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-mod-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-mul-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-or-dead-arg` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-or-dead-let` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-or-dead-own` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-or-dead-single` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-or-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-or-defined` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-or-live` | Unsupported parse term-form → Unsupported parse operator | Rejected: a defined name |
| 12 | `suffix-shl-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-shr-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
| 12 | `suffix-sub-dead` | Unsupported parse term-form → Unsupported parse operator | Accepted: On{} |
