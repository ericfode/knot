# Literals executor handoff

Implemented the frozen U32/Nat/Char/String surface through bundle parsing, checked literal matrices, independent source evaluation and the new `knot-literals-wasm-1` profile. The ABI retains unary Nat cells and uses a 64 MiB arena with explicit frames/returns for the frozen 65536-depth case. Base source bodies and trusted intrinsic lowerings have separate audit categories.

The original 40 fixtures and observations are unchanged. Commit `d3c1e7b` fixed the 12 supplemental bootstrap-helper calls before implementation. See [README.md](README.md) for the exact contract and limits.

## Layout and binder order

Three seed-accepted layouts that Knot reported Invalid, recorded as inherited limits
in round 10, now agree with the seed. Branch `campaign/literals-layout`, from `a60c4e4`.
The freeze came first (D7); no earlier expectation changed, and the 103 earlier
entries of `regressions.json` are byte-identical.

| Commit | Content |
| --- | --- |
| `b27383d` | Freeze, before any fix: six books observed on the seed (`regressions.py --write`, two agreeing passes) |
| `8a95453` | The parser's layout rules, the nested-match floor, the checker's deference to registration order, four laws, six mutants, SPEC, README, LAW_REVIEW; census approved |
| `f52be51` | Restores the text the classification gate's nonleading-template mutant anchors on (below); census inventories follow |
| this commit | This section, the gate run and the literals receipt from the run on `f52be51` |

### What the seed does

From `bend2/bend.ts` and probes, each frozen or recorded below:

- `parse_term` begins with `parse_skip`, which skips spaces, newlines and comments, and
  `parse_term_args`, `parse_tele` and `parse_terms` skip again around every item and
  before `:`. A newline ends a term only before `(` or `[` (`parse_nl`) and where a body
  reads it. So a pattern may follow `case` on the next line, and a call's, constructor's,
  pattern's or parameter list's items may stand on any line.
- `parse_body(p, col)` checks no body column. A match's rows start at the first `case`
  column `ccol` and need `ccol > col`, where `col` is the enclosing `case`'s column for an
  arm body (`parse_block` passes the body column minus one for a function body). An arm
  body may therefore stand left of its `case`, even in column 0, and a let's next line
  in any column; but a match in a dedented body whose cases stand in the enclosing
  `case`'s column has no rows (`expected : cases for False, True`), and those cases
  become rows of the enclosing match.
- A constructor is registered when its declaration is parsed, and a registered
  constructor is no binder, even where a parameter of that name is in scope (probe t1):
  `a braced constructor pattern (Yes is a constructor ...)`. A constructor declared
  later is no obstacle.

### The fix

1. **Line breaks.** `parse.bend` skips line breaks where the seed reads a term or a list
   item: after `case`, `match` and a let's `=`, before the `:` of a case pattern or match
   scrutinee, and after `(` and `{`, around each item and after each `,` of an argument or
   parameter list (calls, constructor values and patterns, `def` headers, constructor
   fields). Thirteen new `S.skip_lines` calls at those continuation points; the lexer keeps
   its newline tokens (closures needs them inside lambda bodies, per SELF-HOSTING-PATH). The
   non-leading `~` test after a parameter's comma keeps its original text, which the
   classification gate's nonleading-template mutant anchors on, so a `~` binder on the
   line after the comma reaches `Parameters` and reports `Unsupported parse
   template-binder` instead of `Invalid parse parameter`; the seed rejects both.
2. **Body column.** `StartBody` no longer checks an arm body's column; only a function
   body (parent 0) must leave column 0, which the frontend gate pins. `BodyAt` and the
   let modes carry the enclosing parent instead of their own column, so a let's next line
   is read in any column. A match's cases must stand right of `U32.max(column of match,
   parent)`: for a dedented body that is the enclosing `case`, the seed's floor, and for
   every layout Knot accepted before it is the match's own column, unchanged. Without
   the floor, the frozen layout-body-floor book (seed-invalid) compiles (`floorless-match`).
3. **Binder order.** The checker's catalog-wide test (`G.constructor_named` in
   `literal-matrix.bend`'s Variable and Promotion arms and in `patterns.bend`'s `fields`)
   is gone, with `constructor_named` and `has_tag` in `catalog.bend`. For a bundle book,
   `qualify.bend` already decides the ordered rule (`known` and `contains`), untouched
   here. For a single file, the parser's binder walker now judges each binder against
   the declarations in scope as nodes: parameters license a dotted name, and
   constructor nodes registered before the function forbid the name. `registered`
   walks a file's declarations in order and the driver runs it before checking. This
   matches campaign/modules, which also removed the checker's test.

### Evidence

Seed against Knot (`check --bundle`, native lane) on the task's probes: g1, g2, g3, o2,
c1 and c9 were Invalid and now check; the frozen books agree in the gate (below).
Single-file: the fields gate's `constructor-name-binder` keeps its exact diagnostic
(`121:123:8:13`); a later-constructor field binder now checks, as the seed accepts; and an
earlier-constructor let binder, which Knot accepted while the seed rejects it, is now
`Invalid check constructor-pattern-binder`, closing the single-file let limit of round 10.

`check` over the 1044 tracked books, old build against new, single-file and bundle:
2051 identical, 37 changed, every one from Invalid. None accepted before is rejected now.

| Change | Books |
| --- | --- |
| Invalid to Checked | layout-term-newline, layout-list-newline, layout-body-column, later-constructor-binder (bundle); selfhost layout-call-args, layout-comments, layout-dedent-close, layout-def-header (both modes); baseslice bool-gates (bundle) |
| Invalid to Unsupported | selfhost layout-braces (`nested-field-pattern`, both modes); nine baseslice fixtures, a perch-calibration control and perch-style-role H02 (`parameter-type`, bundle) |
| Invalid to another Invalid | layout-body-floor (`pattern-type`, as frozen); the five selfhost layout twins, now at their pinned codes and positions (`layout-call-args-comma` 18:14, `layout-braces-comma` 12:11, `layout-def-header-comma` 7:12, `layout-dedent-close-extra` 16:6, `layout-comments-swallowed` argument-separator) |

The floor control's code: the seed reads layout-body-floor's `case False{}` as a row of
the Answer match, so its Knot code follows from the existing vocabulary for a constructor
of another type (`pattern-type`, as pattern-u32-on-bool and dead-pattern-constructor pin
it). It was cross-checked, before the fix, by running the pre-fix build on the same
structure written with an indented match (`Invalid check pattern-type`); that run is the
one Knot observation behind a frozen expectation here, and it is disclosed rather than
hidden in `regressions.py`'s justification. The earlier Answer-only variant read as
`Unsupported check duplicate-arm` and was not frozen.

Laws (ground instances, outside the 37 literals entries): `src/PROOF.bend`
`list_across_lines`, `arm_across_lines` and `cases_right_of_parent`;
`src/check-PROOF.bend` `binders_meet_registered_constructors`. All 13 `src/*PROOF.bend`
print `All terms check.`. Nine negative controls (one mutation each in a scratch tree)
fail the named law ([LAW_REVIEW.md](LAW_REVIEW.md)).

Mutants (42 in the gate, six new, all killed by verdict, pre-checked individually):
case-line-kept, item-line-kept, parameter-line-kept, arm-column-checked, floorless-match
(seed-invalid book to `Built`) and binder-looked-up. The last looks every default binder up
among the constructors, so it also rejects ordinary default binders through the lookup's
own failure: broader than the removed catalog-wide test, and killed with the frozen verdict
because later-constructor-binder's first binder is a constructor's name.

### Known limits (each Invalid where the seed accepts)

Probed against the seed on the new build:

- a function body's first line in column 0 (`body-indentation`; the frontend gate pins it);
- a function body's cases in its `match` column (`top-level-indentation`);
- a line break inside a parameter (`parameter`), in a header outside its parentheses
  (`function-result`), after a promotion's `+` (`pattern-binder`), or before a let's
  `=` (`expected-=`) or `:` (`top-level-indentation`);
- a list item without its comma (`argument-separator`); the seed's commas are optional.

None is a resource limit or a regression: each was Invalid before, and none is reachable
through the frozen books.

### Merge notes for the coordinator

- **selfsource (SF-01, SF-02).** This increment implements the list continuation points
  that SELF-HOSTING-PATH assigns to selfsource, in the way it prescribes (in `parse.bend`,
  not the lexer). The selfhost gate passes with no blocked D4 gap; nine layout cases now
  meet their requirement while blocked (`blocked_meeting_requirement`: the four positives
  layout-call-args, layout-comments, layout-dedent-close, layout-def-header and their five
  twins at the pinned codes and positions), and only layout-braces still stops, at
  `Unsupported check nested-field-pattern`. The `layout` need is not flipped here. With no
  gap showing, the judge's four gap-dependent self-tests (`if gap:`) no longer run, so it
  reports 16 judge mutants where it reported 20; the selfhost owner may want a restated
  gap control to keep them. The committed selfhost receipt is left for its owner.
- **baseslice.** Ten baseslice fixtures change verdict in `--bundle` mode (bool-gates now
  checks; nine now stop at `Unsupported parse parameter-type`, all Invalid before).
  `tests/compiler-baseslice/expectations.json` pins no Knot parse diagnostic and the suite
  is not a registered gate on this branch; re-run it when baseslice merges.
- **Composition bytes.** frontend-laws is at 47959 of 48000. selfsource, closures and
  modules all edit `parse.bend`, so the next merge there will need bytes: the comments on
  `binder` and on `StartBody` are the first to reclaim.
- **modules.** Take modules' `rebinds` in `qualify.bend` and its driver call, and drop
  this branch's `registered` call in `driver.bend` (modules' pass also covers let
  binders and field binders, the same rule). `registered`, `constructor_named` in
  `parse.bend` and the law `binders_meet_registered_constructors` then go with it, or stay
  as the parser's file-local form if the coordinator prefers one walker. The checker-side
  removal matches modules. `binder-looked-up` anchors in `literal-matrix.bend`, which
  modules does not have.
- **closures.** `LambdaStatements` reads newline tokens inside an argument list. The skips
  here sit only at list continuation points (after an opener, around a finished item,
  after `,`), never inside an item, so a lambda body's statements keep their newlines;
  re-run layout-list-newline and the selfhost layout cases after the merge.
- **Trailers.** These commits carry `Co-Authored-By: Claude Sonnet 5.5`, as the run
  instruction asked; the model that made them was Opus 5.5.

### Gates on the fix head

`BEND_NO_TELEMETRY=1 npm run -s gates` on `f52be51` passed all 22 registered gates
(exit 0) in 909.7 seconds (`run-m26vl_zy`, four workers, load average about 48 to 61
from other sessions on the host), and `npm run -s gates:verify` passed 19 tests.
Counts are copied from the runner; categories overlap and are not summed.

| Gate | Seconds | Exact counts |
| --- | ---: | --- |
| frontend | 214.2 | boundaries=24; fixtures=14; lane observations=28; mutants=4 |
| checker | 118.6 | bound observations=16; bounds=2; budgets=10; fixtures=49; lane observations=98; mutants=7 |
| structural | 138.4 | bounds=4; fixtures=16; lane observations=64; mutants=7 |
| fields | 225.3 | bound observations=12; bounds=2; budgets=36; fixtures=40; host boundaries=6; lane observations=240; mutants=9 |
| wasm | 141.3 | boundaries=44; execution lanes=2; fixtures=25; mutants=7; reference calls=90; rejects=64 |
| wasm-trust | 2.8 | entries=3; proof holes=0 |
| fields-trust | 3.5 | entries=4; proof holes=0 |
| structural-trust | 0.6 | entries=2; proof holes=0 |
| owned-store | 9.2 | cases=3532; execution lanes=2; literal witnesses=15; mutants=6 |
| flat-store | 25.3 | bun=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621); mutants=9; native=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621) |
| recursion | 204.6 | fixtures=19; mutants=3 |
| fields-wasm | 316.7 | boundaries=30; fixtures=8; mutants=4 |
| modules | 409.0 | artifact preservation probes=80; byte identity pairs=23; check observations=126; compile observations=126; eval observations=142; execution lanes=2; fixtures=63; mutants=14; pin observations=22; proof entries=4; reference calls=71; tampered base observations=6; trust audits=46; wasm observations=58 |
| census | 15.5 | classes=42; declarations=1206; files=66 |
| perch-context | 95.5 | fixtures=33; mutants=8 |
| lint:verify | 8.1 | law rules=8; tests=168 |
| bootstrap | 116.2 | corpus=1044; mutants=54; reached=2; stages=8 |
| classification | 10.2 | fixtures=17; mutants=6 |
| io-host | 25.7 | cli runs=6; conformance runs=86; errno=[2, 9, 20, 21, 22, 92]; fixtures=20; host boundaries=22; mutants=6; review=(empty write=4; mutants=3; oracle controls=14; secret paths=21; seed runs=12); seed fixtures=40; seed runs=109; stress=(left binds=100000; right binds=100000) |
| io-abi-2 | 116.5 | case mode=insensitive; fixtures=43; host boundaries=25; mutants=5; mutants killed=5; parity=153; read observations=21; reference observations=64; seed exhausted=2; seed observations=61 |
| selfhost | 340.7 | blocked=63; cases=65; d4 gaps=0; judge mutants=16; mutants=3; passed=2 |
| literals | 364.0 | agree eval observations=970; agree fixtures=43; artifact preservation probes=214; boundary probes=16; byte identity pairs=43; check observations=300; compile observations=300; eval observations=1184; execution lanes=2; fixtures=150; invalid fixtures=62; mutant eval observations=9; mutant fault observations=1; mutant verdict observations=29; mutant wasm observations=8; no artifact probes=214; proof entries=3; proof laws=37; reference calls=523; result byte identity pairs=5; result calls=61; result display observations=122; result fixtures=5; semantic mutants=42; trust audits=86; unsupported fixtures=45; wasm observations=970 |

Receipt drift: identical=64; semantic=17; volatile-only=9, the same shape as round 10.
The 16 semantic drifts outside this gate are the shared receipts listed there, left for
the coordinator. This gate's receipt is the run's normalized output, copied after all
237 recorded input hashes were checked against the tree.

Earlier runs on this branch: a direct literals run on `8a95453` passed (14.6 min wall,
overlapping a direct selfhost run at load about 66; one earlier direct run failed only
its final input check, because `src/SPEC.md`, a gate input, was edited during it). A
first runner pass was stopped before any result when a scan showed that `8a95453` had
rewritten the text the classification gate's nonleading-template mutant anchors on;
`f52be51` restores it. `census:test` fails tests 28 and 60 on this head; both also fail,
with 29 and 65, on `a60c4e4`, so neither is new.

### Offline preflight

`npm run lint:style -- --preflight --manifest=docs/compiler-campaign/manifest.json`:
32 groups, 0 structural blockers, 0 provider requests. Changed groups, before and after,
of 48000 composition bytes: checking 47937 to 47689, literal-patterns 47995 to 47220,
frontend-parsing 33752 to 35275, frontend-laws 44795 to 47959, driver-pipeline 39639 to
39892, checker-laws 28408 to 29514. Live semantic and style Perch review need the
network, which this run forbids; no style pass is claimed.

### Remaining

- Live Perch semantic and style review of the changed files (network forbidden here).
- The known limits above, for selfsource or a later increment.
- Refresh of the shared receipts with semantic drift after the merge.

## Review round 10

The coordinator's review workflow (round 1 on `a122239`) confirmed three major
findings. Two are fixed in new commits; the third is disputed as runner-owned,
with a tested patch for the coordinator. No history was rewritten and no earlier
expectation changed: the 90 earlier regression books are byte-identical in
`regressions.json`, and every earlier frozen result still holds.

| Commit | Content |
| --- | --- |
| `6cb406d` | Freeze, before any fix: 13 books observed on the seed (`regressions.py --write`, two agreeing passes) |
| `b4b86fd` | Offset layout: `S.skip_lines` after an offset's `+` (one call in `parse.bend`); law `offset_tail_after_newline`; mutant offset-newline-kept |
| `abda387` | Names read whole (`names`, `malformed`, `name_text`); dotted binders scoped to parameters (`binders`, `binder`, `parameter_named`); let binders tested against constructors (`qualify.bend`); seven laws; seven more mutants; SPEC and CONTRACT; census approved, inventories regenerated |
| `ff8d4ef` | The gate's independent observations on four threads (not requested; see below) |
| `74ceb20` | Census inventories follow the gate script's hash |
| `c2e17a5` | README, LAW_REVIEW and this section: findings, evidence, merge notes |
| this commit | The gate lines below and the literals receipt, both from the full run on `c2e17a5` |

| Finding | Disposition | Evidence |
| --- | --- | --- |
| [major] "found no clang" flake recurs despite the runner's PATH wrapper (shared harness, not literals code) | **Disputed: runner-owned, so not changed here.** The finding's own fix field says "Coordinator/runner-owned, outside campaign/literals", the failing step (`src/parse-cli.bend` built by the seed in the bootstrap gate) does not depend on literals content, and `GATES.md` records that the runner does not retry. The seed's message is produced by any failure to obtain `clang --version` output, which a PATH wrapper cannot intercept (below). A tested patch is offered, not applied. | Mechanism reproduced (below); both full runner passes of this round passed `bootstrap` (46.9 s, 47.8 s); patch: `/Users/ericfode/src/knot/.claude/worktrees/campaign-literals/.local/literals/runner-retry.patch` |
| [major] Dotted, trailing-dot and constructor-named identifiers are accepted where the seed rejects them | **Fixed in `abda387`**, with the review's proposed fix corrected: a dotted binder is valid where a parameter binds that name, and a let binder may name a constructor declared later. | 13 frozen books; 176-book names matrix, 0 accept/reject differences (61 before); 1026 tracked books, 12 verdict changes, all frozen books |
| [major] A newline or a comment after an offset `+` is Invalid; the seed accepts the same spelling | **Fixed in `b4b86fd`.** | offset-layout: 7 calls agree seed, evaluator and Wasm in both lanes; r2a, r2b, r2c agree |

### Finding 1: the clang flake

The seed's native build picks its compiler in `cc_find` (`bend2/main.ts`, about
line 370): for `$CC`, `clang` and each `clang-NN` on PATH it runs
`spawnSync(cc, ["--version"], {encoding: "utf8"}).stdout ?? ""` and matches
`clang version N`. A spawn that fails to start has a null `stdout`, which reads as
empty output, and the message is "found no clang". So the message says that no
candidate printed a version, not that none is installed, and the runner's `clang`
wrapper cannot help when the process never starts. Reproduced: with process
creation failing in one process tree only (`.local/literals/rv1/flake/nproc.py`
sets `RLIMIT_NPROC` to 1 and `exec`s the seed), the seed's native build of
`src/parse-cli.bend` prints exactly `Error: bend needs clang 14 or newer to
build binaries (found no clang); on Debian/Ubuntu: curl -fsSL ...`, with clang and
the wrapper present. The natural cause of the one failure in eight bootstrap runs
is not established (fork failure under `kern.maxprocperuid` = 10666, memory
pressure and a killed child are all consistent with it) and remains untested.

The proposed patch (`scripts/gates/run.py`, its tests and one paragraph of
`GATES.md`; 139 lines, `git apply --check` clean on this tree, 20 of 20 runner
tests pass with it in a scratch copy) reruns a gate once when its stderr holds
that exact message, keeps both attempts' logs (`NAME.attempt1.*`), records
`host_flake` and the load average outside the normalized summary, and reports a
second identical failure as `host-failure`, never `failed`. It changes a
documented runner decision ("does not retry"), so it is left to the coordinator,
who should also confirm that a first bootstrap attempt leaves nothing in the
scratch tree that the second reuses. Until it lands, rerun and record both runs
rather than triaging a merge-time exit 1 whose only failure carries this message.

### Finding 3: offset layout

The seed reads an offset's tail with a free `parse_term`, whose first act is to
skip spaces, newlines, comments and blank lines. Knot's lexer already drops
comment text and emits one `"\n"` token per line, so the fix is one call in the
`LiteralTail` arm: `run(n,Term{pattern},S.skip_lines(tail))`. The reviewer's
r2a (`case 1n+` then `p:`), r2b (a comment after the `+`) and r2c (`1n+` then
`p` as an expression) now agree with the seed in check, evaluation and Wasm.
The frozen book `offset-layout` adds `+p` on the next line, a stacked `1n+` `1n+`
`p`, a blank and a comment line between `+` and tail, a tail in column 0 in an
expression, and a commented `2n+`: seven calls agree seed, evaluator and Wasm in
both lanes (byte-identical modules); before the fix the whole book was `Invalid
parse expected-term`. `offset-layout-keyword` pins the other side: a `def` line
after `1n+` is no tail, the seed rejects it, and Knot reports `Unsupported parse
term-form`, never Invalid.

Not fixed, and not part of this finding (inherited from `main`, in README and
SPEC): an arm body must start right of its `case` keyword, so an offset tail
dedented left of `case` with the body on the same line is `Invalid parse
body-indentation` where the seed accepts (a dedented body on its own line trips
the same rule without any offset); a newline after `case`, or inside call or
constructor arguments other than after an offset's `+`, is `Invalid parse
expected-term`. The frontend gate pins `body-indentation` for a `def` body in
column 0, so the rule is not loosened here.

### Finding 2: names and binders

What the seed does, from probes (frozen as books, each committed at `6cb406d`
before the fix):

- Every token that starts like a name is read by `parse_lexeme` and must match
  `^[A-Za-z_]\w*(\.[A-Za-z_]\w*)*$`: `x.`, `a..b`, `x.1`, `x.1a`, `A.1` fail in
  every position (function, parameter, type, constructor, field, binder, let).
  A dotted name that matches is a name: it may declare a function, type,
  constructor, field or parameter. Knot accepted all of them before; it now reads
  names whole in `parse` (`Invalid parse name`), and `parse` still returns
  `Exhausted` at budget 0 for every token list, so `no_parser_budget` holds.
- Where a let or a pattern binds, `parse_var` returns a Var for a name on the
  seed's scope stack and a Ref for any other dotted name, and a Ref is no
  pattern. A dotted parameter is the only way a dotted name reaches the stack.
  So `case x.y`, `1n+x.y`, `+x.y`, `case U32.add`, `case Bool.True` and `x.y :
  U32 = 3` are rejected, while a default, promoted, offset or field pattern, and a
  typed, promoted or plain let, that repeats a dotted parameter are accepted (the
  reviewer's "one unqualified identifier" would reject them: a new D4 violation).
  Knot checks this in the parser (`binders` over each function body against its
  parameters), so the single-file and bundle entries share it. Codes: `Invalid
  parse pattern-binder`, and `binding-name` for a let.
- A constructor is no binder once registered, and the seed registers in source
  order: a let binder naming a constructor of Base, of an import or of the book's
  own earlier declarations is rejected, one naming a constructor declared later
  is accepted, and a parameter, a function or a type may take any name.
  `qualify.bend` orders registration and already decided this for pattern
  binders; the Binding arm now asks it too (`Invalid check
  constructor-pattern-binder`). `--bundle` only.

Frozen books (13): offset-layout, offset-layout-keyword, name-parameter-trailing-dot,
name-function-double-dot, name-constructor-digit-word, name-binder-trailing-dot,
dotted-default-binder, dotted-offset-binder, dotted-shadows-intrinsic,
dotted-let-binder, let-constructor-binder, let-own-constructor-binder and the
agreeing control binder-scope (a dotted parameter rebound by default, promoted,
offset and field patterns and by typed, promoted and plain lets; a later
constructor, a parameter, a function and a type naming binders).

Differentials, seed against Knot (native lane; the frozen books and the
tracked-book comparison were also run in the Bun lane, with the same results and
byte-identical modules):

| Set | Result |
| --- | --- |
| Reviewer's r1a to r1e, r2a to r2c | all as the seed |
| 29 further probes: constructor order c1 to c9, dotted parameters e1 to e7, lets and promotions l1 to l13 | accept/reject equal in all but c1 and c9 (below) |
| Names matrix: 16 positions by 11 names (`x.`, `x..y`, `a.b.`, `X.`, `x.1`, `x.y`, `x.y.z`, `x.1a`, `True`, `_.`, `a1.b`), 176 generated books | 0 differences; the build before the fix differed on 61 of the 144 rows it was run on |
| `check` over the 1026 tracked books, old against new, both lanes | 1014 identical in each lane; the 12 changes are exactly the frozen books (10 Built to Invalid, offset-layout Invalid to Built, offset-layout-keyword Invalid to Unsupported) |

Laws (ground instances; eight, outside the 37 counted for the literals entries):
`src/PROOF.bend` malformed_name, name_shapes, dotted_binder_needs_a_parameter,
dotted_binder_repeats_a_parameter, dotted_reference_binds_nothing and
offset_tail_after_newline; `src/qualify-PROOF.bend` constructor_is_not_a_let_binder
and later_constructor_can_be_a_let_binder. All 13 `src/*PROOF.bend` print `All
terms check.`. Eleven negative controls (one mutation each in a scratch tree)
fail the named law ([LAW_REVIEW.md](LAW_REVIEW.md)).

Mutants (36 in the gate, eight new, all killed by verdict): offset-newline-kept,
names-unread, name-may-end-in-dot, name-word-may-be-empty,
name-word-may-start-with-digit, dotted-binder-anywhere (binder-scope: rejecting
every dotted binder is unsound), let-binder-unchecked and
constructor-binder-anywhere (binder-scope: a constructor test that ignores source
order rejects the later-constructor let).

### Merge notes for the coordinator

- **`qualify.bend` overlaps `campaign/modules`.** modules has independently put
  the let-binder test in its Binding arm (`then(pattern(...),binder => binders =>`)
  and added a single-file `rebinds` pass in source order. When `main` is re-merged
  after modules lands, take modules' form. Then: my mutant `let-binder-unchecked`
  anchors on my line (`S.bind(Qualified,Qualified,pattern(token,S.Variable{token},names,ctors),u =>`)
  and must be re-anchored to modules' text, or the gate fails on its anchor check;
  `constructor-binder-anywhere` anchors on `pattern`'s test, which modules keeps,
  but modules passes a different constructor list (`visible`), so re-confirm it
  is still killed; the laws `constructor_is_not_a_let_binder` and
  `later_constructor_can_be_a_let_binder` call `Q.walk_in` and need a re-run. The
  three frozen let books and binder-scope hold for either form. The single-file
  let-binder limit recorded here is closed by modules' `rebinds`; do not duplicate
  it. modules' `qualify.bend` does not typecheck against this branch alone (it
  has no `S.Literal`, `S.Offset` or `S.Intrinsic` arms), so the two were not
  tried together.
- **The gate now runs on four threads (`ff8d4ef`, not requested).** The round-10
  books and mutants add about 65 s, and the gate took 481.6 s sequentially in a
  full runner pass on identical content and 650 to 717 s under the review's load
  average, against the runner's 900 s limit per gate. Threaded it took 206 s in
  the runner (232 s directly), with a receipt equal observation for observation
  (only the date, three input hashes and the runner's path normalization
  differ). It reverts together with `74ceb20` (the census inventory hash of
  `check.py`). It raises the number of concurrent child processes while other
  gates run, which is the condition the flake reproduction above implicates;
  the gain is the margin against the wall limit.
- **Erratum.** The `ff8d4ef` commit message compares 232 s with "about 410 s
  sequentially on the same host at load 10". That 410 s was measured on
  `a122239`, before the 13 books and 8 mutants. The comparison on identical
  content is 481.6 s (run g1, sequential) against 206 s (run g2, threaded), in
  the runner.
- **Trailers.** These commits carry `Co-Authored-By: Claude Sonnet 5.5`, the
  model that made them, as the earlier round-9 implementer commits do; the run
  instruction named Opus 5.5.

### Known limits (all Invalid where the seed accepts, all inherited)

- A pattern binder named like a constructor declared later in the book (c1, c9)
  is `Invalid check constructor-pattern-binder` from the checker's catalog-wide
  test. Changing it in `literal-matrix.bend` is byte-blocked (literal-patterns is
  at 47995 of 48000 composition bytes), and the legacy fields gate pins the code.
- The single-file entry does not test let binders against constructors
  (closed by modules' `rebinds`, above).
- An arm body starting left of its `case` keyword; a newline after `case` or
  inside call or constructor arguments (Finding 3).
- None of these is a resource limit or a new regression: each was Invalid before
  this round, and none is reachable through the new books.

### Gates on the fix head

`BEND_NO_TELEMETRY=1 npm run -s gates` on `c2e17a5` passed all 22 registered
gates (exit 0) in 488.7 seconds (`run-8rmmrqg4`, four workers, load average about
10 to 14), and `npm run -s gates:verify` passed 19 tests. `bootstrap` passed
(65.8 s here; 46.9 s and 47.8 s in the two earlier passes). Counts are copied from
the runner; categories overlap and are not summed.

| Gate | Exact counts |
| --- | --- |
| frontend | boundaries=24; fixtures=14; lane observations=28; mutants=4 |
| checker | bound observations=16; bounds=2; budgets=10; fixtures=49; lane observations=98; mutants=7 |
| structural | bounds=4; fixtures=16; lane observations=64; mutants=7 |
| fields | bound observations=12; bounds=2; budgets=36; fixtures=40; host boundaries=6; lane observations=240; mutants=9 |
| wasm | boundaries=44; execution lanes=2; fixtures=25; mutants=7; reference calls=90; rejects=64 |
| wasm-trust | entries=3; proof holes=0 |
| fields-trust | entries=4; proof holes=0 |
| structural-trust | entries=2; proof holes=0 |
| owned-store | cases=3532; execution lanes=2; literal witnesses=15; mutants=6 |
| flat-store | bun=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621); mutants=9; native=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621) |
| recursion | fixtures=19; mutants=3 |
| fields-wasm | boundaries=30; fixtures=8; mutants=4 |
| modules | artifact preservation probes=80; byte identity pairs=23; check observations=126; compile observations=126; eval observations=142; execution lanes=2; fixtures=63; mutants=14; pin observations=22; proof entries=4; reference calls=71; tampered base observations=6; trust audits=46; wasm observations=58 |
| census | classes=42; declarations=1198; files=66 |
| perch-context | fixtures=33; mutants=8 |
| lint:verify | law rules=8; tests=168 |
| bootstrap | corpus=1038; mutants=54; reached=2; stages=8 |
| classification | fixtures=17; mutants=6 |
| io-host | cli runs=6; conformance runs=86; errno=[2, 9, 20, 21, 22, 92]; fixtures=20; host boundaries=22; mutants=6; review=(empty write=4; mutants=3; oracle controls=14; secret paths=21; seed runs=12); seed fixtures=40; seed runs=109; stress=(left binds=100000; right binds=100000) |
| io-abi-2 | case mode=insensitive; fixtures=43; host boundaries=25; mutants=5; mutants killed=5; parity=153; read observations=21; reference observations=64; seed exhausted=2; seed observations=61 |
| selfhost | blocked=63; cases=65; d4 gaps=5; judge mutants=20; mutants=3; passed=2 |
| literals | agree eval observations=946; agree fixtures=39; artifact preservation probes=210; boundary probes=16; byte identity pairs=39; check observations=288; compile observations=288; eval observations=1156; execution lanes=2; fixtures=144; invalid fixtures=60; mutant eval observations=9; mutant fault observations=1; mutant verdict observations=23; mutant wasm observations=8; no artifact probes=210; proof entries=3; proof laws=37; reference calls=511; result byte identity pairs=5; result calls=61; result display observations=122; result fixtures=5; semantic mutants=36; trust audits=78; unsupported fixtures=45; wasm observations=946 |

Receipt drift: identical=64; semantic=17; volatile-only=9. The 16 semantic drifts
outside this gate are source-hash and derived-code changes in shared receipts
(the three trust inventories, bootstrap progress and reference, checker,
classification, fields, fields-wasm, modules, recursion, selfhost, structural,
wasm, perch-context and frontend), left for the coordinator as before. This gate's
receipt is the run's normalized output, copied after all 231 recorded input
hashes were checked against the tree.

Two earlier full passes on the same sources failed only on `census`, and both were
stale approvals rather than code: the first ran before `census:approve` and the
regeneration of the inventories (21 of 22; literals 481.6 s in sequence), the
second after them but before the inventories followed the threaded gate script's
hash (21 of 22; literals 206 s threaded). `74ceb20` regenerated them; no
assertion was changed.

### Offline preflight

`npm run lint:style -- --preflight --manifest=docs/compiler-campaign/manifest.json`:
32 groups, 0 structural blockers, 0 provider requests (frontend-parsing 33752,
frontend-laws 44795, module-qualification 26279 of 48000 composition bytes;
`checking` 47937 and literal-patterns 47995 are unchanged). The six changed Bend
files (parse, qualify, LAWS, PROOF, qualify-LAWS, qualify-PROOF) report 32
truncated contexts (context-helper, context-file and caller limits, 7 + 3 + 22;
`parse` and the law `offset_tail_after_newline` are cut by the helper limit
because they call `run`) and the ad-hoc composition bound over the six together
(68893/48000); none of the seven new definitions in `parse.bend` is truncated. Live semantic and style Perch review remain the
coordinator's; no style pass is claimed.

### Remaining

- The runner patch for finding 1 (`.local/literals/runner-retry.patch`, not applied).
- Live Perch review of the changed files.
- The `modules` re-merge items above (take modules' Binding arm, re-anchor
  `let-binder-unchecked`, re-confirm `constructor-binder-anywhere`).
- Refresh of the shared receipts with semantic drift after the merge.
- The parser layout limits under Known limits, and c1/c9, for a separate
  increment.

## Review round 9

The coordinator's review of `943104f` confirmed one major finding: the law that
an expression offset spells `kn+t` as k Succ constructors around the shared
tail was stated and proved at k = 2 only (`natural_offset`, `offset_spelling`),
and SPEC recorded no open obligation for the general law (D21). It is fixed in
new commits after merging `main` (`43a394a`: the gate runner's clang PATH
wrapper, and D22); the merge had no conflicts. No history was rewritten and no
earlier expectation changed.

| Commit | Content |
| --- | --- |
| `60a68c3` | Merge `main` `43a394a` |
| `9263b15` | Freeze: offset-expression-width (5 seed calls) and three Invalid controls, before the fix |
| `e88b915` | `literal-offset.bend::successors`; the Offset arm checks the tail once and wraps it; laws `offset_cells`, `offset_lowering`, `offset_bound`, `single_argument_keeps_uses`; mutants offset-one-short, offset-extra-successor, offset-unchecked-type and the re-anchored offset-nat-add; offset limit probes in the gate; README, SPEC, CONTRACT, LAW_REVIEW; census approved, inventories regenerated |
| `d0296ce` | First report commit and literals receipt, on `e88b915` |
| `30e104e` | `offset_cells` quantified over the book (a tail may call functions); `offset_cells_call`; SPEC, CONTRACT and LAW_REVIEW state the checker law as proved (every tail that checks, against the installed Nat); census approved |
| `da78cca` | This section as run on `30e104e`, and the literals receipt from that run |
| addendum | The census approval output, one more limit, the proof loop on the head |

| Finding | Disposition | Evidence |
| --- | --- | --- |
| [major] The offset-construction law holds only at k = 2, and SPEC does not record the general law as an open obligation (D21) | Fixed in `e88b915` and `30e104e`. The general law is proved, so no D21 obligation is recorded for it. `literal-core-LAWS.bend::offset_cells` is an induction on a Nat k: in any book, k successors around any tail with a known value return k cells around that value in 4k+c transitions; `offset_cells_call` applies it to a tail that calls a function. To let the checker's own lowering meet it, the Offset arm no longer reaches the successors through a U32 count that no proof can decrement: it checks the tail once and wraps k = `U32.to_nat(count)` Succ constructors with `literal-offset.bend::successors`. `check-LAWS.bend::offset_lowering` states, for every count up to 4096 and every tail that checks to a term and its uses, against the installed Nat, that the checker returns that wrapper with those uses, and `offset_bound` that above 4096 it is `Exhausted check`. The k = 2 laws stay as witnesses. The known depth limit is recorded in SPEC and CONTRACT and is lifted from 1364 to 2047 successors end to end (table below). | All 13 `src/*PROOF.bend` print `All terms check.`; 15 negative controls fail; the frozen width book now agrees seed, evaluator and Wasm in both lanes (before: `Exhausted check budget`); 1011 of 1012 tracked books check byte-identically old and new in both lanes, the one difference being that book |

### Coordinator ruling: the selfhost pin

Recorded as ruled; no action this round. `c51f480` (round 7) changed a shared
selfhost gate assertion: the mutant typecheck must equal the modules host
verdict. modules made the same fix in a stricter form and merges to `main`
before literals, so modules' form is canonical. When literals re-merges `main`
after modules lands, take modules' version of that assertion and drop
`c51f480`'s variant.

### The proof attempt

The general law was tried first, over the existing lowering.

1. **Core law, existing core.** `offset_cells` needed no compiler change: a
   Nat-indexed builder and value, an induction on k generalized over the
   frames and the leftover fuel, one rewrite by the induction hypothesis. The
   tail is any term whose evaluation is a hypothesis, so the law covers every
   tail with a known value, not only a variable (in any book, after the
   review noted under Laws). The instance k = 2, c = 1 takes 9 transitions,
   the count `natural_offset` fixes.
2. **Checker law, existing lowering.** It does not go through. The offset
   reached its successors through `M.literal`, which decrements the U32 count
   with `U32.sub` and tests it against the literal 0. A symbolic count does not
   reduce there, and `U32.sub(U32.inc(c),1) == c` is not provable by
   reflexivity (probed: the checker prints the expected and observed terms).
   Base states no lemma that inverts its 32-bit adder (only `Word.add_comm`),
   so an induction over the count has nothing to stand on; proving it would
   mean a Word arithmetic library. This was the point at which the plan was
   put to an independent review, which recommended the route below.
3. **The change.** Convert the count once, `U32.to_nat`, and build the wrapper
   with a builder that is structural in a Nat. The checker laws then quantify
   over every count, the one trusted step being Base's `to_nat`. The change
   also removes the reason for the depth limit, one checker level per
   successor.

### Freeze and measured limits

`tests/compiler-literals/regressions/offset-expression-width.bend` (seed: all
five calls as frozen) holds `1364n+t`, `1365n+t` and `2000n+t` as single
expressions: `at_edge` and `past_edge` compare against 1366n and 1367n,
`wide_sum` against 2005n (Yes) and `wide_short` against 2004n (No); `main` is
`past_edge`. Three Invalid controls pin the diagnostics the fix must keep,
with the classes Knot reports today: offset-expression-mismatch (`2n+t` where
a U32 is expected: `Invalid check type-mismatch` at the offset),
offset-expression-unbound (`2n+zz`: `Invalid check free-name`) and
offset-expression-both (both errors, the tail first: `free-name`; the seed
names the type first, and both are Invalid). The three controls hold before and
after the fix; the width book fails before it and holds after. Before the fix
both lanes report
`Exhausted check budget` (exit 4) for check, eval and compile of the whole
width book; after it the book builds 97889 bytes, byte-identical across lanes,
and all five calls agree seed, evaluator and Wasm in both.

One expression, `kn+t` with the seed answering Yes throughout; native and Bun
lanes agree in every row (probe books `.local/literals/r9/p/k<k>.bend`:
`answer(Nat.is_eq(f(0n), kn))` with `f(t) = kn+t`):

| k | Before (`9263b15`) | After (`e88b915`) |
| --- | --- | --- |
| 1, 2, 3, 100, 1364 | Built (2718, 2738, 2758, 4700, 29982 bytes) | Built, identical bytes (sha256 equal) |
| 1365 | `Exhausted check budget` | Built, 30002 bytes; evaluator and Wasm answer Yes |
| 2000 | `Exhausted check budget` | Built, 42702 bytes; Yes |
| 2047 | `Exhausted check budget` | Built, 43642 bytes; Yes |
| 2048, 4096 | `Exhausted check budget` | checks and evaluates (Yes); compile `Exhausted emit budget`; the checker CLI's display is `Exhausted inspect budget` |
| 4097, 100000 | `Exhausted check budget` | `Exhausted check budget` at the offset (152:157:13:2), for check, eval and compile |

The gate now pins the four thresholds (16 budget/host probes, 8 new): 2047
builds and runs, 2048 and 4096 evaluate but are `Exhausted emit` with the
output preserved, 4097 is `Exhausted check`, in both lanes.

### Laws and mutants

- `literal-core-LAWS.bend::offset_cells` and `offset_cells_call` (37 literals
  laws in all; three proof entries): for every k, in any book, and every tail
  term with a known value (a hypothesis on its evaluation under any frames
  and fuel), k successors return k cells around it in `steps(k,c,m)` = 4k+c+m
  transitions. `cells` and `steps` are the specification, defined beside the
  law; the compiler uses neither. The builder is the compiler's own
  `successors`. `offset_cells` was first stated in the empty book, which
  excluded every tail with a call, the recursion that motivated rounds 7 and
  9; review of `e88b915` caught it. `offset_cells_call` is proved by applying
  the general law to a tail that calls a one-function book (3 transitions, so 2
  successors take 11), the hypothesis discharged by reflexivity: the
  hypothesis holds for a call, and the law is not vacuous there.
- `check-LAWS.bend::offset_lowering`, `offset_bound` and
  `single_argument_keeps_uses` (18 checker laws in all): the lowering and bound
  laws state, for every count and every tail that checks to a term and its
  uses (not every tail: one that fails to check has no law), the checker's
  exact result against the installed Nat; the last shows a
  constructor of one argument keeps its uses, why `offset` needs no
  sequencing. The k = 2 laws `natural_offset` and `offset_spelling` are
  unchanged and still pass.
- Negative controls (fifteen single mutations in a scratch tree, each failing
  its proof entry): `offset_cells` with three leading transitions per layer, an
  extra cell or extra successor at the base, a shifted tag; `offset_cells_call`
  with 10 transitions or a changed value; `offset_lowering`
  and `offset_bound` one successor short, wrong tag, the bound at 4095 or 4097,
  the tail's uses dropped, the tail unspelled or against no type, the
  below-bound branch not Exhausted; `single_argument_keeps_uses` with
  `sequential` dropping the head.
- Mutants (28 in the gate): offset-nat-add is re-anchored to the new arm and
  still gives `Exhausted eval budget` and `Exhausted wasm resource-limit` on
  `successor`; offset-one-short (`U32.sub(count,1)`) and offset-extra-successor
  (one more around every tail) are killed by a wrong enum result from the
  module (`wide_sum` and `successor`, both 0) and from the evaluator;
  offset-unchecked-type drops the expected-type check of the outermost Succ, so
  the seed-invalid mismatch book compiles.

### Known limits

- Compilation stops at 2047 successors: the emitter lowers a Construct in two
  of its 4096 levels (`machine-lower.bend::lower`, Term and Arguments), and the
  maximum override is 4096. The checker CLI's core display stops at the same
  size. Lifting it is an emitter change (an iterative chain), out of scope here.
- The count is bounded at 4096 (`Exhausted check`), where the seed answers Yes.
  It is a D4-safe resource bound: the count sizes the core, and the wrapper
  recurses to that depth in both lanes.
- An offset above 4096 or in 1365..4096 with an Invalid tail now reports the
  tail's Invalid (the tail is checked before the wrap), where the old descent
  reported `Exhausted` first. Only previously exhausted inputs change.
- The `checking` manifest group is at 47937/48000 composition bytes (46597
  before), so the next change to check.bend, scope.bend, patterns.bend,
  catalog.bend or a literal-* file in it needs a trim or a group split.
- `check-PROOF.bend`'s single-file composition is unavailable for the byte
  limit as well now (55602/48000; it was unavailable for unresolved context
  already): its motives import the checker's modules. Its manifest group,
  checker-laws, is available (28408/48000).
- SPEC calls the lowering the matrix's own spelling, but the checker now builds
  the chain with `successors`, not `M.literal`. Their equality is measured, not
  proved: identical `check` output on 1011 of 1012 books in both lanes and
  identical module bytes for k up to 1364. `M.literal` does not reduce on a
  symbolic U32 count, so no law can tie the two together.
- Trust that remains: `U32.to_nat` as Base's reading of the count, and the
  linear allocation of recursion through an offset, which the frozen depth
  books measure. The laws instantiate the installed Nat (`nat()`, one
  datatype); real catalogs are covered by the differential runs below.
- `check-LAWS.bend` and `literal-core-LAWS.bend` now define specification
  helpers (`nat`, `cells`, `steps`), which no other LAWS file does; the
  compiler uses none of them.

### Differential evidence

Old (`9263b15`'s sources, built native and Bun) against new (`e88b915`'s
compiler sources), both lanes, `check` on every tracked `.bend` under `tests/`,
`src/`, `packages/` and `research/` (1012 books, absolute bundle and entry
paths): 1011 identical in exit, stdout and stderr, and one difference, the
width book (`Exhausted check budget` to `Checked`). The five books whose core
changed in round 7 are not among the differences. `compile` on the 408
tracked books under `tests/compiler-literals`, `tests/compiler-modules`,
`tests/compiler-selfhost` and `src` (module bytes, exit and stdout): 407
identical, the same book.

### Gates on the round-9 fix head

`BEND_NO_TELEMETRY=1 npm run -s gates` on `30e104e` passed all 22 registered
gates (exit 0) in 619.8 seconds with 4 workers (run directory
`run-e4ke8dfe`). `npm run -s gates:verify` passed 19 tests. An earlier run on
`e88b915` passed the same 22 (648.7 s, `run-am8gue5z`); `30e104e` changes
only laws, proofs, prose, the census and the gate's law count. Counts are
copied from the runner; categories overlap and are not summed.

| Gate | Exact counts |
| --- | --- |
| frontend | boundaries=24; fixtures=14; lane observations=28; mutants=4 |
| checker | bound observations=16; bounds=2; budgets=10; fixtures=49; lane observations=98; mutants=7 |
| structural | bounds=4; fixtures=16; lane observations=64; mutants=7 |
| fields | bound observations=12; bounds=2; budgets=36; fixtures=40; host boundaries=6; lane observations=240; mutants=9 |
| wasm | boundaries=44; execution lanes=2; fixtures=25; mutants=7; reference calls=90; rejects=64 |
| wasm-trust | entries=3; proof holes=0 |
| fields-trust | entries=4; proof holes=0 |
| structural-trust | entries=2; proof holes=0 |
| owned-store | cases=3532; execution lanes=2; literal witnesses=15; mutants=6 |
| flat-store | bun=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621); mutants=9; native=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621) |
| recursion | fixtures=19; mutants=3 |
| fields-wasm | boundaries=30; fixtures=8; mutants=4 |
| modules | artifact preservation probes=80; byte identity pairs=23; check observations=126; compile observations=126; eval observations=142; execution lanes=2; fixtures=63; mutants=14; pin observations=22; proof entries=4; reference calls=71; tampered base observations=6; trust audits=46; wasm observations=58 |
| census | classes=42; declarations=1175; files=66 |
| perch-context | fixtures=33; mutants=8 |
| lint:verify | law rules=8; tests=168 |
| bootstrap | corpus=1025; mutants=54; reached=2; stages=8 |
| classification | fixtures=17; mutants=6 |
| io-host | cli runs=6; conformance runs=86; errno=[2, 9, 20, 21, 22, 92]; fixtures=20; host boundaries=22; mutants=6; review=(empty write=4; mutants=3; oracle controls=14; secret paths=21; seed runs=12); seed fixtures=40; seed runs=109; stress=(left binds=100000; right binds=100000) |
| io-abi-2 | case mode=insensitive; fixtures=43; host boundaries=25; mutants=5; mutants killed=5; parity=153; read observations=21; reference observations=64; seed exhausted=2; seed observations=61 |
| selfhost | blocked=63; cases=65; d4 gaps=5; judge mutants=20; mutants=3; passed=2 |
| literals | agree eval observations=922; agree fixtures=37; artifact preservation probes=188; boundary probes=16; byte identity pairs=37; check observations=262; compile observations=262; eval observations=1110; execution lanes=2; fixtures=131; invalid fixtures=50; mutant eval observations=9; mutant fault observations=1; mutant verdict observations=15; mutant wasm observations=8; no artifact probes=188; proof entries=3; proof laws=37; reference calls=499; result byte identity pairs=5; result calls=61; result display observations=122; result fixtures=5; semantic mutants=28; trust audits=74; unsupported fixtures=44; wasm observations=922 |

Receipt drift: identical=64; semantic=17; volatile-only=9. The 16 semantic
drifts in shared receipts (source hashes and derived code) are left for the
coordinator. The literals receipt was copied from the run's normalized output
after all 218 recorded input hashes were checked against the tree. The
selfhost pin ruling above was not acted on: `c51f480`'s assertion is unchanged.

### Offline preflight

- The compiler-manifest preflight reports 32 groups and 0 structural
  blockers. `literal-offset.bend` joins the nine groups that import it
  (checking, wasm-emission, driver-pipeline, checker-laws, runtime-laws,
  catalog-laws, fields-laws, recursion-laws, literal-source-machine).
  Composition bytes, before to after: checking 46597 to 47937/48000,
  checker-laws 23556 to 28408, literal-source-machine 43216 to 46085,
  wasm-emission 30680 to 30920, driver-pipeline 39397 to 39637, runtime-laws
  34881 to 35350, catalog-laws 28773 to 29242, fields-laws 24509 to 24978,
  recursion-laws 22014 to 22483. All are available.
- Per changed file (`--preflight --task=tests/compiler-literals/README.md`),
  truncated contexts, before to after: check.bend 7 to 7 (context-file-limit
  1 to 5), check-LAWS.bend 2 to 4 (the new `offset_lowering` and
  `offset_bound`, context-helper and context-file limits),
  literal-core-LAWS.bend 5 to 7 (`offset_cells` and `offset_cells_call`,
  context-helper limit; single-file composition 42655 to 44897/48000),
  literal-core-PROOF.bend 0 to 2 (their fills, context-helper limit),
  check-PROOF.bend 0 to 0 and literal-offset.bend 0 (composition available,
  6366/48000). The single-file
  compositions of check.bend (85201) and check-LAWS.bend (87615) were already
  over the limit (83903, 84146).
- Zero provider requests were made. Live Perch review remains the
  coordinator's.

### Census approval (addendum to `e88b915` and `30e104e`)

The commit messages keep the `new` lines of `npm run census:approve`; this is
its complete printed output, minus Node's experimental-feature warning.
`e88b915` (two runs: the first before `offset_bound` was added):

```
new src/check-LAWS.bend::single_argument_keeps_uses:law: calls,constructors,dependent,equality,fields,generics,laws,quantities.affine,quantities.arguments,quantities.reusable,types.base
new src/check-LAWS.bend::nat:definition: constructors,fields,literals.list,literals.string,literals.u32
new src/check-LAWS.bend::offset_lowering:law: calls,constructors,dependent,equality,fields,generics,laws,literals.list,literals.string,literals.u32,quantities.affine,quantities.arguments,quantities.reusable,types.base
import src/check-LAWS.bend: ./literal-offset.bend -> src/literal-offset.bend
new src/check-PROOF.bend::L.single_argument_keeps_uses:law_fill: calls,captures,constructors,dependent,equality,fields,generics,lambdas,matches,patterns.variable,proofs,quantities.affine,quantities.arguments,quantities.reusable,recursion,rewrites,types.base
new src/check-PROOF.bend::L.offset_lowering:law_fill: calls,captures,constructors,dependent,equality,fields,generics,lambdas,literals.list,literals.string,literals.u32,proofs,quantities.affine,quantities.arguments,quantities.reusable,rewrites,types.base
import src/check-PROOF.bend: ./syntax.bend -> src/syntax.bend
import src/check-PROOF.bend: ./core.bend -> src/core.bend
import src/check-PROOF.bend: ./scope.bend -> src/scope.bend
import src/check-PROOF.bend: ./check.bend -> src/check.bend
import src/check-PROOF.bend: ./catalog.bend -> src/catalog.bend
import src/check-PROOF.bend: ./literal-matrix.bend -> src/literal-matrix.bend
import src/check-PROOF.bend: ./literal-offset.bend -> src/literal-offset.bend
new src/check.bend::offset:definition: calls,captures,constructors,fields,generics,lambdas,literals.u32,matches,matches.multi,patterns.variable,quantities.affine,quantities.arguments,quantities.reusable,types.base
import src/check.bend: ./literal-offset.bend -> src/literal-offset.bend
new src/literal-core-LAWS.bend::cells:definition: calls,constructors,fields,literals.list,literals.nat,matches,patterns.variable,quantities.affine,quantities.reusable,recursion,types.base
new src/literal-core-LAWS.bend::steps:definition: calls,constructors,fields,literals.nat,matches,patterns.variable,quantities.affine,recursion,types.base
new src/literal-core-LAWS.bend::offset_cells:law: calls,constructors,dependent,equality,fields,generics,higher-order,laws,literals.list,literals.u32,quantities.affine,quantities.arguments,quantities.reusable,types.base
import src/literal-core-LAWS.bend: ./literal-offset.bend -> src/literal-offset.bend
new src/literal-core-PROOF.bend::L.offset_cells:law_fill: calls,calls.variable,captures,constructors,dependent,equality,fields,generics,higher-order,lambdas,literals.list,literals.nat,literals.u32,matches,patterns.variable,proofs,quantities.affine,quantities.arguments,quantities.reusable,recursion,rewrites,types.base
import src/literal-core-PROOF.bend: ./syntax.bend -> src/syntax.bend
import src/literal-core-PROOF.bend: ./core.bend -> src/core.bend
NEW FILE src/literal-offset.bend: 1 declarations
new src/check-LAWS.bend::offset_bound:law: calls,constructors,dependent,equality,fields,generics,laws,literals.string,literals.u32,quantities.affine,quantities.arguments,quantities.reusable,types.base
new src/check-PROOF.bend::L.offset_bound:law_fill: calls,captures,constructors,dependent,equality,fields,generics,lambdas,literals.list,literals.string,literals.u32,proofs,quantities.affine,quantities.arguments,quantities.reusable,rewrites,types.base
```

`30e104e`:

```
new src/literal-core-LAWS.bend::offset_cells_call:law: calls,constructors,dependent,equality,fields,generics,laws,literals.list,literals.nat,literals.u32,quantities.arguments,quantities.reusable,types.base
new src/literal-core-PROOF.bend::L.offset_cells_call:law_fill: calls,constructors,dependent,equality,fields,generics,lambdas,literals.list,literals.nat,literals.u32,proofs,quantities.affine,quantities.arguments,quantities.reusable,types.base
```

`census --check` exits 0 after each, and the inventories are regenerated.

Erratum: the merge commit `60a68c3` credits Claude Opus 5.5, the trailer the
task text prescribed, while `9263b15`, `e88b915`, `d0296ce`, `30e104e`,
`da78cca` and the addendum commit credit Claude Sonnet 5.5, the model that ran.
History is not rewritten. All 13 `src/*PROOF.bend` entries print
`All terms check.` on `da78cca`, the head the addendum follows; it differs from
the gated `30e104e` only in this file and the installed literals receipt.

## Review round 8

The coordinator's review of `27c1aa2` confirmed one major finding: the Bun
compile lane faulted (exit 1, `bend: memory fault (machine stack overflow?)`,
an unclassified outcome) on every `knot-literals-wasm-1` module above about
60.5 KB, while the native lane built the correct module. It is fixed in new
commits; no history was rewritten and no earlier expectation changed.

| Commit | Content |
| --- | --- |
| `788be82` | Freeze: module-width, 7 seed calls, before the fix, with the measured lane split |
| `8a2db01` | `machine-code.bend::runs`; `literal-wasm.bend::section` appends 4096-byte runs; laws `runs_are_bounded` and `seq_undoes_runs`; mutant unbounded-chunk and the `fault` kill kind; README, SPEC, CONTRACT, LAW_REVIEW; census approved |

| Finding | Disposition | Evidence |
| --- | --- | --- |
| [major] The Bun compile lane crashes (exit 1, unclassified) on any knot-literals-wasm-1 module above about 60.5 KB, while the native lane builds the correct module | Fixed in `8a2db01`. `section` handed each body to the published builder as one fragment, and the builder's `finish` copies a chunk with Base's `List.append`, which is not tail recursive, so a chunk's length was a host stack depth. `machine-code.bend::runs` splits a byte list into consecutive runs of at most `width` bytes, tail recursively (`seq` undoes it), and `appended` adds a body's 4096-byte runs to the builder in order. `B.append` scans each run against the room left, so the byte limit, the first failing byte and the error mapping are those of one fragment. The builder package is hash-pinned and published, so the bound sits at the call site; its `finish` is unchanged. | module-width builds 156918 bytes, byte-identical in both lanes, and all 7 calls agree seed, evaluator and Wasm in both; before the fix the Bun compile faulted. Native bytes are identical before and after on every probe. Laws `runs_are_bounded` and `seq_undoes_runs`. Mutant unbounded-chunk. |

### Freeze and measured lane split

`tests/compiler-literals/regressions/module-width.bend` (seed: all seven
calls as frozen) holds a 3000-Char String literal (`length`: 3000n Yes, 2999n
No), a `case 450n` (`depth`: 450n Yes, 449n No) and a 100-Char String pattern
(`spelled`: its spelling through `String.reverse` Yes, its 99-Char prefix No);
`main` is `length(Far)`. Gate CLIs, bundle mode, before (`27c1aa2`) and after
(`8a2db01`):

| Book | Native bytes | Bun compile before | Bun compile after |
| --- | --- | --- | --- |
| strexpr_1000 (1000-Char String) | 22728 | Built, identical | Built, identical |
| strexpr_3000 | 62728 | memory fault, exit 1 | Built, identical |
| natpat_450 (`case 450n`) | 65657 | memory fault, exit 1 | Built, identical |
| module-width | 156918 | memory fault, exit 1 (5 s), output untouched | Built, identical |
| many_13 (13 x 2000 Chars) | 524021 | not run | Built, identical |
| many_16 (16 x 2000 Chars) | 644304 | not run | Built, identical |
| big_32 (verifier's probe) | 644441 | not run | Built, identical |
| many_17, many_30 | Exhausted emit budget | not run | Exhausted emit budget, no output |

Check and evaluation agreed in both lanes before and after. The two lanes now
build identical modules up to the 32768-instruction bound and both report
`Exhausted emit` beyond it. The byte limit is unchanged: compiling
module-width with an output budget of 100000 (inside the data section) or
156917 bytes is `Exhausted emit budget`, exit 4, output untouched, in the
native lane before and after and in the Bun lane before and after; at 156918
the fixed lanes build it and the old Bun lane faulted. The largest module of any earlier frozen book was
39191 bytes (nat-pattern-offset), under the fault threshold.

### Laws and mutant

- `literal-LAWS.bend::runs_are_bounded`: `runs(2,[1,2,3,4,5])` is
  `[[1,2],[3,4],[5]]`, in order, each run at most the width.
- `literal-LAWS.bend::seq_undoes_runs`: `seq(runs(3,[1,...,7]))` is
  `[1,...,7]`.
- Negative controls: each law fails alone on a changed right-hand side and
  against a `split` that closes a run without reversing it. Both are concrete;
  that runs stay within the width and that `seq` undoes `runs` for every input
  is not claimed. All 13 `src/*PROOF.bend` entries print `All terms check.`
- Mutant unbounded-chunk restores `W.bytes(cap,data)`, one chunk per section.
  Its Bun compiler builds u32-literals to the gate's bytes (Built 3164) and
  faults on module-width with exactly `bend: memory fault (machine stack
  overflow?)`, exit 1, leaving the output file untouched. Since no existing
  kill accepts a build failure, `check.py` adds a `fault` kill: the pinned
  fault on a book both gate lanes built, plus the control book's bytes. The
  MUTANTS header states that exception; any other failure is still no kill.

### Known limits

- The builder's `finish` still recurses on each chunk. The bound holds
  because every Knot call site in this profile feeds runs of at most 4096
  bytes; a package revision with a tail-recursive `emit` would remove the
  bound for every user. That is the output_builder owner's decision.
- The older profiles (`knot-enum-1`, `knot-fields-wasm-1`) compose small
  fragments and were not changed or probed at this size.

Erratum: the `8a2db01` message credits the 473-second direct literals gate
to its tree. That run preceded two edits in the same commit, the law rename
`runs_invert_seq` to `seq_undoes_runs` and the direction of the `runs`
comment; no behavior changed, and the full run below is on `8a2db01`.

### Gates on the round-8 fix head

`BEND_NO_TELEMETRY=1 npm run -s gates` on `8a2db01` passed all 22 registered
gates (exit 0) in 663.0 seconds with 4 workers (run directory
`run-z5rdmlst`). `npm run -s gates:verify` passed 18 tests. The direct
literals gate had passed earlier on the same behavior (473 s). Counts are
copied from the runner; categories overlap and are not summed.

| Gate | Exact counts |
| --- | --- |
| frontend | boundaries=24; fixtures=14; lane observations=28; mutants=4 |
| checker | bound observations=16; bounds=2; budgets=10; fixtures=49; lane observations=98; mutants=7 |
| structural | bounds=4; fixtures=16; lane observations=64; mutants=7 |
| fields | bound observations=12; bounds=2; budgets=36; fixtures=40; host boundaries=6; lane observations=240; mutants=9 |
| wasm | boundaries=44; execution lanes=2; fixtures=25; mutants=7; reference calls=90; rejects=64 |
| wasm-trust | entries=3; proof holes=0 |
| fields-trust | entries=4; proof holes=0 |
| structural-trust | entries=2; proof holes=0 |
| owned-store | cases=3532; execution lanes=2; literal witnesses=15; mutants=6 |
| flat-store | bun=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621); mutants=9; native=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621) |
| recursion | fixtures=19; mutants=3 |
| fields-wasm | boundaries=30; fixtures=8; mutants=4 |
| modules | artifact preservation probes=80; byte identity pairs=23; check observations=126; compile observations=126; eval observations=142; execution lanes=2; fixtures=63; mutants=14; pin observations=22; proof entries=4; reference calls=71; tampered base observations=6; trust audits=46; wasm observations=58 |
| census | classes=42; declarations=1160; files=65 |
| perch-context | fixtures=33; mutants=8 |
| lint:verify | law rules=8; tests=168 |
| bootstrap | corpus=1020; mutants=54; reached=2; stages=8 |
| classification | fixtures=17; mutants=6 |
| io-host | cli runs=6; conformance runs=86; errno=[2, 9, 20, 21, 22, 92]; fixtures=20; host boundaries=22; mutants=6; review=(empty write=4; mutants=3; oracle controls=14; secret paths=21; seed runs=12); seed fixtures=40; seed runs=109; stress=(left binds=100000; right binds=100000) |
| io-abi-2 | case mode=insensitive; fixtures=43; host boundaries=25; mutants=5; mutants killed=5; parity=153; read observations=21; reference observations=64; seed exhausted=2; seed observations=61 |
| selfhost | blocked=63; cases=65; d4 gaps=5; judge mutants=20; mutants=3; passed=2 |
| literals | agree eval observations=912; agree fixtures=36; artifact preservation probes=182; boundary probes=8; byte identity pairs=36; check observations=254; compile observations=254; eval observations=1094; execution lanes=2; fixtures=127; invalid fixtures=47; mutant eval observations=7; mutant fault observations=1; mutant verdict observations=14; mutant wasm observations=6; no artifact probes=182; proof entries=3; proof laws=35; reference calls=494; result byte identity pairs=5; result calls=61; result display observations=122; result fixtures=5; semantic mutants=25; trust audits=72; unsupported fixtures=44; wasm observations=912 |

Receipt drift: identical=64; semantic=17; volatile-only=9. The 16 semantic
drifts in shared receipts (source hashes and derived code) are left for the
coordinator. The literals receipt was copied from the run's normalized output
after all 213 recorded input hashes were checked against the tree.

### Offline preflight

- The compiler-manifest preflight reports 32 groups and 0 structural
  blockers. literal-emission is 45280/48000 bytes (43967 before),
  literal-algebra-laws 26368/48000 (25400) and literal-machine-runtime
  23024/48000 (22304); literal-patterns is unchanged.
- Per changed file (`--preflight --task=tests/compiler-literals/README.md`),
  truncated contexts equal those at `27c1aa2`: literal-wasm.bend 4
  (context-helper limit on runtime, binary, module and emit), machine-code.bend
  2, literal-LAWS.bend 0 and literal-PROOF.bend 0.
- The module-width book has no preflight: Perch's parser adapter reports
  `resource-unavailable` (Maximum call stack size exceeded) on it. It is a
  test book, not compiler source.
- Zero provider requests were made. Live Perch review remains the
  coordinator's.

## Review round 7

The coordinator's review of `df0edb1` confirmed one major finding: an
expression offset `kn+t` lowered to the intrinsic `Nat.add(kn,t)`, which
counts both arguments and materializes a fresh Nat, so recursion that builds
a Nat through an offset allocated about n²/2 cells and reached Exhausted where
the seed succeeds. It is fixed in new commits after merging `main` (`c0bd08d`);
no history was rewritten and no earlier expectation changed.

| Commit | Content |
| --- | --- |
| `68787b7` | Merge `main` `c0bd08d` (CC/SDKROOT for every gate); registry and census conflicts resolved |
| `068539e` | Freeze: offset-expression-depth, 6 seed calls, before the fix, with the measured cost |
| `c22357e` | The Offset arm checks `M.literal(kn+t)`; laws `natural_offset` and `offset_spelling`; mutant offset-nat-add; README, SPEC, CONTRACT, LAW_REVIEW; census approved |
| `c51f480` | Merge resolution: selfhost mutants typecheck against the modules host verdict |

| Finding | Disposition | Evidence |
| --- | --- | --- |
| [major] `kn+t` lowers to an O(\|t\|) `Nat.add`, so offset recursion is quadratic and Exhausted where the seed succeeds | Fixed in `c22357e`. `check.bend`'s Offset arm checks `M.literal(S.Offset{token,count,tail})`, the pattern matrix's own expansion, instead of `S.Intrinsic{NAdd,[kn,t]}`: k `Succ` constructors around the tail, which is checked once and shared, as the seed builds it. `0n+t` never reaches it (the parser reads it as t), and inside the expansion `Offset{0,t}` spells t. `2n+n` now checks to exactly the core of `Succ{Succ{n}}` (`v0.1{v0.1{$0:0}}`). | The frozen book agrees seed ⇔ evaluator (both lanes) ⇔ Wasm (both lanes) at the gate's budgets; before the fix four of its six calls were Exhausted in both. Scaling table below. Laws `natural_offset` (literal-core) and `offset_spelling` (check). Mutant offset-nat-add. |

### Freeze and measured cost

`tests/compiler-literals/regressions/offset-expression-depth.bend` (seed:
all six calls as frozen): `successor` is `Nat.is_eq(up(4000n),4000n)` with
`up = 1n+up(p)`; `successor_short` compares with `3999n` (No, so the book is
not constant); `doubled` is Base's `Nat.double(3000n)` (`2n+double(p)`,
BaseChecked); `tripled` is `triple(3000n)` with `3n+triple(p)`; `zero` is
`kept(4000n)` with `Succ{0n+kept(p)}`, the `0n+t` control. Bun lane,
evaluator budget 1048576 transitions, Wasm heap 5505024 eight-byte cells
(the heap pointer read through an exported copy of the global):

| Call | Before: eval / Wasm | After: eval transitions / Wasm cells |
| --- | --- | --- |
| successor | Exhausted eval budget / Exhausted wasm resource-limit (heap full) | 56032 / 12000 |
| successor_short | Exhausted / Exhausted | 56031 / 11999 |
| doubled | Exhausted / Exhausted | 57032 / 15000 |
| tripled | Exhausted / Exhausted | 72032 / 21000 |
| zero | 56032 / 12000 | 56032 / 12000 |

Scaling of the same functions (eval transitions / Wasm cells, each call
including its argument and comparison literals):

| n | up(n) before | up(n) after | Nat.double(n) before | after | triple(n) before | after |
| --- | --- | --- | --- | --- | --- | --- |
| 250 | 36407 / 32125 | 3532 / 750 | 68282 / 64000 | 4782 / 1250 | 100157 / 95875 | 6032 / 1750 |
| 500 | 135282 / 126750 | 7032 / 1500 | 261532 / 253000 | 9532 / 2500 | 387782 / 379250 | 12032 / 3500 |
| 1000 | 520532 / 503500 | 14032 / 3000 | 1023032 / 1006000 | 19032 / 5000 | Exhausted / 1508500 | 24032 / 7000 |
| 2000 | Exhausted / 2007000 | 28032 / 6000 | Exhausted / 4012000 | 38032 / 10000 | Exhausted / trap at 5505024 | 48032 / 14000 |

Before, doubling n quadrupled both; after, it doubles both, and `up(n)`
allocates exactly the 3n cells of its argument, result and comparison
literal, as the `Succ{...}` control does.

### Laws and mutant

- `literal-core-LAWS.bend::natural_offset`: the core of `2n+t` (two Succ
  constructs around a reference to t) and a literal's `Natural` state with
  two successors around t's value both run to
  `Object{id,1,[Object{id,1,[value]}]}`, the former in exactly 9 transitions.
  So `kn` (`Natural` around Zero, `natural_literal`) and `kn+t` build the
  same cells.
- `check-LAWS.bend::offset_spelling`: against an installed Nat, the checker
  lowers `2n+Zero{}` to two Succ constructs around `Zero`'s value, with no
  uses, for any scope and current function. It lives beside the checker, as
  the round-5 and round-6 checker laws do; literal-core cannot import
  `check.bend` without closing the checker into literal-source-machine.
- Negative controls: `natural_offset` fails with three successors on the
  right and at 8 transitions; `offset_spelling` fails with `3n+` on the left
  and against the restored `Nat.add` lowering (expected
  `Intrinsic{NAdd,[Literal 2n, Zero]}`). All 13 `src/*PROOF.bend` entries
  print `All terms check.`
- Mutant offset-nat-add restores the `Nat.add` lowering (and the
  primitive-op import). It typechecks with the frozen host verdict; its
  compiled `successor` is `Exhausted wasm resource-limit` and its evaluator
  prints `Exhausted eval budget`, against the frozen Yes. The unmutated lanes
  answer Yes.

### Known limit

Each successor takes three levels of the 4096-deep bundle checker budget
(Offset, Succ constructor, its argument). `1364n+n` checks and agrees with
the seed in the evaluator and Wasm, native and Bun (a 29984-byte module,
byte-identical across lanes); `1365n+n`, `2000n+n` and `100000n+n` are
`Exhausted check budget` for check and eval in both lanes, where the
`Nat.add` lowering checked them (seed: Yes). No frozen book and no Knot
source uses an expression offset above 3; pattern offsets stop at 256 in
both. The expansion also costs code proportional to k, as the seed's does.

### Merge resolution: selfhost

`main` added the `selfhost` gate before `modules` was merged anywhere; this
branch already carries `modules`, whose host identity query makes the seed
list five foreign-dependent definitions in each CLI. The gate's three `src/`
mutants required `All terms check.` and copied only `src/*.bend`, so the first
full run on `c22357e` failed selfhost at reject-every-self-call. `c51f480`
applies the pattern the modules branch gave the other compiler gates in
`f4c3224`: the mutant typecheck must equal the frozen verdict of
`host-check-expectations.json` for its CLI, and each mutant copy carries
`src/host`. No case, expectation or mutant changed; the coordinator should
carry the same change when `modules` reaches `main`.

### Differential evidence

Checked-core verdicts, Bun `check.js` built from `068539e` against the fix,
over all 1007 tracked `tests/`, `src/`, `packages/` and `research/` books:
1002 identical byte for byte, 5 with the same exit and diagnostics whose
printed core changed only on lines that contained `Nat.add(` (literal-views,
nat-literals, let-annotated, offset-adjacent and offset-expression-depth),
and 0 verdict changes.

### Gates on the round-7 fix head

`BEND_NO_TELEMETRY=1 npm run -s gates` on `c51f480` passed all 22 registered
gates (exit 0) in 1306.5 seconds with 4 workers under heavy host load (run
directory `run-5_vq0t2_`). `npm run -s gates:verify` passed 18 tests. The
first full run, on `c22357e`, failed only selfhost, as described above; the
direct literals gate had passed on the same sources (126 fixtures, 24
mutants). Counts are copied from the runner; categories overlap and are not
summed.

| Gate | Exact counts |
| --- | --- |
| frontend | boundaries=24; fixtures=14; lane observations=28; mutants=4 |
| checker | bound observations=16; bounds=2; budgets=10; fixtures=49; lane observations=98; mutants=7 |
| structural | bounds=4; fixtures=16; lane observations=64; mutants=7 |
| fields | bound observations=12; bounds=2; budgets=36; fixtures=40; host boundaries=6; lane observations=240; mutants=9 |
| wasm | boundaries=44; execution lanes=2; fixtures=25; mutants=7; reference calls=90; rejects=64 |
| wasm-trust | entries=3; proof holes=0 |
| fields-trust | entries=4; proof holes=0 |
| structural-trust | entries=2; proof holes=0 |
| owned-store | cases=3532; execution lanes=2; literal witnesses=15; mutants=6 |
| flat-store | bun=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621); mutants=9; native=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621) |
| recursion | fixtures=19; mutants=3 |
| fields-wasm | boundaries=30; fixtures=8; mutants=4 |
| modules | artifact preservation probes=80; byte identity pairs=23; check observations=126; compile observations=126; eval observations=142; execution lanes=2; fixtures=63; mutants=14; pin observations=22; proof entries=4; reference calls=71; tampered base observations=6; trust audits=46; wasm observations=58 |
| census | classes=42; declarations=1153; files=65 |
| perch-context | fixtures=33; mutants=8 |
| lint:verify | law rules=8; tests=168 |
| bootstrap | corpus=1019; mutants=54; reached=2; stages=8 |
| classification | fixtures=17; mutants=6 |
| io-host | cli runs=6; conformance runs=86; errno=[2, 9, 20, 21, 22, 92]; fixtures=20; host boundaries=22; mutants=6; review=(empty write=4; mutants=3; oracle controls=14; secret paths=21; seed runs=12); seed fixtures=40; seed runs=109; stress=(left binds=100000; right binds=100000) |
| io-abi-2 | case mode=insensitive; fixtures=43; host boundaries=25; mutants=5; mutants killed=5; parity=153; read observations=21; reference observations=64; seed exhausted=2; seed observations=61 |
| selfhost | blocked=63; cases=65; d4 gaps=5; judge mutants=20; mutants=3; passed=2 |
| literals | agree eval observations=898; agree fixtures=35; artifact preservation probes=182; boundary probes=8; byte identity pairs=35; check observations=252; compile observations=252; eval observations=1080; execution lanes=2; fixtures=126; invalid fixtures=47; mutant eval observations=7; mutant verdict observations=14; mutant wasm observations=6; no artifact probes=182; proof entries=3; proof laws=33; reference calls=487; result byte identity pairs=5; result calls=61; result display observations=122; result fixtures=5; semantic mutants=24; trust audits=70; unsupported fixtures=44; wasm observations=898 |

Receipt drift: identical=64; semantic=17; volatile-only=9. The 16 semantic
drifts in shared receipts (source hashes and derived code, plus the
selfhost receipt's new inputs) are left for the coordinator. The literals
receipt was copied from the run's normalized output after all 212 recorded
input hashes were checked against the tree.

### Offline preflight

- The compiler-manifest preflight reports 32 groups and 0 structural
  blockers. literal-patterns stays at 47995/48000 bytes (`literal-matrix.bend`
  is unchanged); literal-source-machine is 43216/48000 (42591 before),
  checker-laws 23556/48000 (22435), checking 46597/48000 (46580).
- Per changed file (`--preflight FILE`), truncated contexts against
  `068539e`: check.bend 7 (7), check-LAWS.bend 2 (1; the new
  `offset_spelling`, context-helper and context-file limits),
  literal-core-LAWS.bend 5 (4; the new `natural_offset`, context-helper
  limit, as its neighbours), check-PROOF.bend and literal-core-PROOF.bend 0.
  The single-file composition of literal-core-LAWS.bend is available
  (42655/48000); check.bend (83903) and check-LAWS.bend (84146) were already
  over the limit (83886 and 76879). The new regression book has 2
  caller-or-byte-limit truncations and an available composition (901 bytes).
- Zero provider requests were made. Live Perch review remains the
  coordinator's.

## Review round 6

The coordinator's review of `c7f3487` confirmed one major D4 finding: without
Base, a seed-valid literal or Nat offset against a book's own Zero/Succ or
SNil/SCon datatype was Invalid. It is fixed in new commits; no history was
rewritten and no earlier expectation changed.

| Commit | Content |
| --- | --- |
| `e16fe06` | Freeze: 17 regression books from the seed (13 seed-valid, 4 seed-invalid controls) |
| `e1e6b55` | `primitive_type` keyed on the absent installed primitive and the spelled constructor; five checker laws; two mutants; docs; census |

| Finding | Disposition | Evidence |
| --- | --- | --- |
| [major] Without Base, a book's own Zero/Succ or SNil/SCon type: seed-valid literal/offset patterns and non-Nat-named expression literals are Invalid | Fixed in `e1e6b55`. `literal-check.bend::primitive_type` takes the literal's kind, its target (the expected type, or the scrutinee type for an arm) and its spelling (`M.literal`, the matrix's own expansion). The installed primitive wins. Without it, a target that declares the spelled constructor gives `Unsupported check literal-base-type`, whatever the type is called; a U32 or Char word (Base's `Word`) gives Unsupported for any target; a target that declares no spelled constructor, or no target, stays Invalid, as `unknown-type` at the literal. `check.bend` applies it to expression literals, expression offsets and, through `arm_pattern` in `patterns`, to literal and offset arms on a datatype scrutinee. With Base those arms stay Invalid pattern-type. | All 13 seed-valid round-6 books (own Nat, N, A.T, String and T; patterns `0n`, `2n`, `1n+p`, `""`; expressions `2n`, `2n+n`, `""`, `1n+n`) are `Unsupported check literal-base-type` in both lanes for check, eval and compile, with the output file preserved; 11 were Invalid before. Controls: own-u32-pattern is Unsupported, like the frozen own-u32-literal; own-unspelled-pattern (`N{Z, S}`), own-nat-pattern-module and own-n-expr-module (datatypes imported with qualified constructor names) stay Invalid unknown-type, as the seed rejects them; literal-without-base, pattern-u32-on-enum, pattern-offset-on-enum and pattern-string-on-enum stay Invalid; own-u32-literal stays Unsupported. Laws `installed_literal_type`, `spelled_own_literal`, `unspelled_literal`, `word_spells_any_target` and `untargeted_literal`. Mutants invalid-own-pattern and unspelled-own-target. |

The review named `literal-matrix.bend::normalize` as a site. No repro reaches
it, and `normalize` is unchanged:
- `M.enabled` admits only a scrutinee whose type is an installed primitive.
- Every nested matrix column is a primitive field (`Succ.pred`, `SCon`'s Char
  and String), so a matrix column is never a user datatype.
- An installed type exists only when Base is loaded, and Base then installs
  the primitive of every literal the book uses. The unchanged Invalid
  pattern-type of pattern-u32-on-enum, pattern-offset-on-enum and
  pattern-string-on-enum shows it: were U32, Nat or String missing there,
  the new rule would have changed their verdict.

The two conditions of the required rule therefore never hold together inside
`normalize`, and a guard there would be dead code that no book or mutant
reaches. A site probe on `c7f3487` gave each Invalid site its own code: all
nine review repros failed in `check.bend::pattern` (its Offset case for the
offset books). The matrix's pattern-type fired only for `dead-pattern-type`,
which has Base (`'a'` on U32).

Spelling, not the type name, separates the seed's verdicts: the seed rejects
`case 0n` on `N{Z, S}` ("unknown: Zero") and accepts it on `N{Zero, Succ}`.
Checking the target's spelled constructor keeps the first one Invalid; a rule
on the absent primitive alone would have made it Unsupported.

Erratum: the freeze message of `e16fe06` says twelve of its books are
seed-valid and that Knot printed Invalid for ten of them. The correct counts
are 13 and 11: regressions.json has 13 round-6 entries with seed check exit 0,
and all but own-nat-offset-expr and own-string-empty-expr were Invalid.

### Differential evidence

- Verdicts, base (`c7f3487` source) against fix, native lane, over 857
  tracked books (every `tests/`, `src/`, `packages/` and `research/` book):
  837 identical, byte for byte including the printed checked core. The 20
  changes are the 17 round-6 books and three location moves:
  literal-without-base (0:0:0:0 to its literal), own-nat-literal and
  own-u32-literal (their type token to their literal). No verdict class
  changed outside the round-6 books.
- Probes in other positions, seed `--check-only` and run against both check
  lanes and the native evaluator:
  - seed-valid, now Unsupported literal-base-type: a constructor field
    argument (`Succ{1n}` into own N), a call argument (`z(2n)`), annotated
    lets (`x: N = 2n` and `x: N = 1n+Zero{}`), and patterns on a Zero/Succ
    type named A.T and an SNil/SCon type named A.S;
  - seed-invalid, still Invalid: two types declaring Zero (duplicate
    constructor in both), an own `Nat` beside `import Base` (duplicate
    global), an unannotated `x = 2n` (unknown-type), `case 0n` and `z(0n)`
    against a type that declares none of the spelled constructors
    (unknown-type), and module-qualified datatypes;
  - seed-invalid, now Unsupported: a Char pattern on an own type, and
    `Succ{1n}` feeding a computed scrutinee, through spellings Knot does not
    interpret.
  No Invalid on a seed-valid book, no accepted seed-invalid book, no lane
  mismatch.

Scripts are in the executor scratchpad (`impl-literals/r6/probe.py`,
`diffverdict.py` and `mutants.py`).

### Gates on the round-6 fix head

`BEND_NO_TELEMETRY=1 npm run -s gates` on `e1e6b55` passed all 20
registered gates (exit 0) in 518.6 seconds with 4 workers (run directory
`run-a9rdezcy`). `npm run -s gates:verify` passed 18 tests. Before the
commit, the direct literals gate passed on the same sources (125 fixtures,
23 mutants). Counts are copied from the runner; categories overlap and are
not summed.

| Gate | Exact counts |
| --- | --- |
| frontend | boundaries=24; fixtures=14; lane observations=28; mutants=4 |
| checker | bound observations=16; bounds=2; budgets=10; fixtures=49; lane observations=98; mutants=7 |
| structural | bounds=4; fixtures=16; lane observations=64; mutants=7 |
| fields | bound observations=12; bounds=2; budgets=36; fixtures=40; host boundaries=6; lane observations=240; mutants=9 |
| wasm | boundaries=44; execution lanes=2; fixtures=25; mutants=7; reference calls=90; rejects=64 |
| wasm-trust | entries=3; proof holes=0 |
| fields-trust | entries=4; proof holes=0 |
| structural-trust | entries=2; proof holes=0 |
| owned-store | cases=3532; execution lanes=2; literal witnesses=15; mutants=6 |
| flat-store | bun=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621); mutants=9; native=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621) |
| recursion | fixtures=19; mutants=3 |
| fields-wasm | boundaries=30; fixtures=8; mutants=4 |
| modules | artifact preservation probes=80; byte identity pairs=23; check observations=126; compile observations=126; eval observations=142; execution lanes=2; fixtures=63; mutants=14; pin observations=22; proof entries=4; reference calls=71; tampered base observations=6; trust audits=46; wasm observations=58 |
| census | classes=42; declarations=1149; files=65 |
| perch-context | fixtures=33; mutants=8 |
| lint:verify | law rules=8; tests=168 |
| bootstrap | corpus=857; mutants=9; reached=2; stages=8 |
| classification | fixtures=17; mutants=6 |
| io-host | cli runs=6; conformance runs=86; errno=[2, 9, 20, 21, 22, 92]; fixtures=20; host boundaries=22; mutants=6; review=(empty write=4; mutants=3; oracle controls=14; secret paths=21; seed runs=12); seed fixtures=40; seed runs=109; stress=(left binds=100000; right binds=100000) |
| literals | agree eval observations=886; agree fixtures=34; artifact preservation probes=182; boundary probes=8; byte identity pairs=34; check observations=250; compile observations=250; eval observations=1068; execution lanes=2; fixtures=125; invalid fixtures=47; mutant eval observations=6; mutant verdict observations=14; mutant wasm observations=5; no artifact probes=182; proof entries=3; proof laws=32; reference calls=481; result byte identity pairs=5; result calls=61; result display observations=122; result fixtures=5; semantic mutants=23; trust audits=68; unsupported fixtures=44; wasm observations=886 |

Receipt drift: identical=64; semantic=16; volatile-only=7. The 15
semantic drifts in shared receipts are the same 15 as in rounds 2 to 5
(source hashes and derived code), left for the coordinator. The literals
receipt was copied from the run's normalized output after every recorded
input hash was checked against the tree.

All 13 `src/*PROOF.bend` entries print `All terms check.`; each of the five
new laws fails when its right-hand side is changed (`Done{1}` for
`installed_literal_type`, and Invalid and Unsupported swapped in the other
four).

### Offline preflight

- The compiler-manifest preflight reports 32 groups and 0 structural
  blockers. literal-patterns stays at 47995/48000 bytes (`literal-matrix.bend`
  is unchanged); checking is 46580/48000 (45288 before), checker-laws
  22435/48000 (20154) and literal-types 31762/48000 (31046).
- Per changed file (`--preflight FILE`), truncated contexts against
  `c7f3487`: check.bend 7 (6 before). The new one is `match_body`, whose
  transitive helpers now pass the 48-helper cap by three (`constructor_next`,
  `constructor_tag`, `fields_at`), because `patterns` reaches
  `L.primitive_type` through `arm_pattern`. check-LAWS.bend stays at 1,
  check-PROOF.bend and literal-check.bend at 0. The single-file compositions
  of check.bend (83886 bytes) and check-LAWS.bend (76879, now importing
  literal-check and literal-matrix) were already over the limit (82151 and
  52828); literal-check.bend's is available (31762/48000).
- Zero provider requests were made. Live Perch review remains the
  coordinator's.

### Known limits

- Without Base, Knot interprets no literal spelling: a seed-valid book that
  uses one is Unsupported, never Checked.
- Only the outermost spelled constructor is compared with the target: `2n`
  against a type that declares Succ but not Zero is Unsupported, where the
  seed rejects it ("unknown: Zero", probed). That is safe under D4.
- Without Base, a U32 or Char literal is Unsupported against any target,
  because Knot does not model Base's Word spelling. The seed rejected every
  such book probed: "unknown: U32" for own Char and U32 types, and "unknown:
  WCon" for one declaring its own `U32{data: Word}`. A book that declares
  Word's own constructors might be seed-valid; it would be Unsupported too.

## Review round 5

The coordinator's review of `3246fa3` confirmed one blocking and one major
finding (review round 1 of this fix cycle in the coordinator's numbering).
Both are fixed in new commits; no history was rewritten and no earlier
expectation changed.

| Commit | Content |
| --- | --- |
| `42a775b` | Freeze: 21 regression books from the seed (13 dead-arm, 6 controls, 2 own-type) |
| `f3a18ee` | Two-walk matrix check, own-type literals Unsupported, two checker laws, three mutants |
| `32331e4` | Regenerated census inventories (the first gate run failed census on a stale inventory) |

| Finding | Disposition | Evidence |
| --- | --- | --- |
| [blocking] A failing body in an unreachable match arm makes a seed-valid book Invalid | Fixed in `f3a18ee`. Each path's first leaf is live and the rest are dead there. `check.bend` walks the plan twice, all live leaves before any dead one; `dead_arm` turns a dead leaf's Invalid into `Unsupported check dead-arm` and keeps every other outcome. Every leaf is still checked. Reachability comes from the matrix, so subsumption and nested String columns are covered, and patterns stay checked in every row, as in the seed. | All 13 seed-valid dead-arm books (the review's two repros, the q5 and q9 shapes) now report `Unsupported check dead-arm` in both lanes for check, eval and compile, with the output file preserved; before the fix they were Invalid type-mismatch, affine-reuse or free-name. The six controls keep their codes: live-arm-nat-offset and live-arm-u32-default (a catch-all shadowed on the `5` path only) stay `Invalid check type-mismatch`, and the four q6 dead-pattern books stay pattern-arity, `parse` nat-offset-pattern and pattern-type (twice). Laws `dead_arm_invalid` and `dead_arm_exhausted`. Mutants all-leaf-invalid and dead-before-live. |
| [major] A literal typed by the book's own Nat is `Invalid check literal-base-type` | Fixed in `f3a18ee`: `literal-check.bend::type_id` reports `Unsupported check literal-base-type` for a type name that resolves to a user datatype. | own-nat-literal (seed `Yes{}`) and own-u32-literal (seed-invalid) are both `Unsupported check literal-base-type`. Mutant invalid-own-primitive. |

The walk order is the point of the design. A per-leaf downgrade would
report `case 5: 0 / case _: 'q'` as Unsupported: the catch-all is dead on
the `5` path, which is checked first, but live on the default path, where
the seed rejects it. Two walks report it Invalid, because every live leaf is
checked before any dead one; the `dead-before-live` mutant is killed on
exactly this book. The alternative of rejecting any match with an
unreachable arm would have turned the frozen agreeing books
`u32-pattern-first-match` and `promoted-column` (`unreached`) into
Unsupported.

### Differential evidence

- Verdicts, base (`3246fa3` source) against fix, native lane, over all 541
  tracked `tests/compiler-*` books plus the 36 earlier probe books in
  `.local/literals/r4`: 562 of 577 identical, byte for byte including the
  printed checked core. The 15 changes are the 13 dead-arm books and the 2
  own-type books, Invalid to Unsupported.
- Random primitive matches (U32, Char, Nat, String scrutinees; 2-5 arms from
  literals, offsets, constructors, nested String patterns, binders and `+`
  rows; bodies well-typed, ill-typed, affine-reusing or with a free name),
  seed `--check-only` against both check lanes, 480 books, on the final
  build: 0 Invalid on a seed-valid book (the base build had 98), 0 accepted
  seed-invalid books, 0 lane mismatches. Seed-valid books: 142 Checked, 98
  `Unsupported dead-arm`. Seed-invalid books: Invalid affine-reuse 74,
  type-mismatch 71, free-name 62, missing-arm 29, and 4
  `Unsupported dead-arm`, each a catch-all after rows that name every
  constructor (the first known limit below).

Scripts are in the executor scratchpad (`impl-literals/r5/probe.py`,
`diffverdict.py`, `sweep.py`).

### Gates on the round-5 fix head

`BEND_NO_TELEMETRY=1 npm run -s gates` on `32331e4` passed all 20
registered gates (exit 0) in 468.9 seconds with 4 workers. The one-minute load
average was 6.3 at the start and at the end (run directory
`run-uvvdyadb`). The first run, on `f3a18ee`, passed 19 gates and failed
census on a stale implementation inventory; `32331e4` regenerated the
inventories. `npm run -s gates:verify` passed 18 tests. Counts are copied
from the runner; categories overlap and are not summed.

| Gate | Exact counts |
| --- | --- |
| frontend | boundaries=24; fixtures=14; lane observations=28; mutants=4 |
| checker | bound observations=16; bounds=2; budgets=10; fixtures=49; lane observations=98; mutants=7 |
| structural | bounds=4; fixtures=16; lane observations=64; mutants=7 |
| fields | bound observations=12; bounds=2; budgets=36; fixtures=40; host boundaries=6; lane observations=240; mutants=9 |
| wasm | boundaries=44; execution lanes=2; fixtures=25; mutants=7; reference calls=90; rejects=64 |
| wasm-trust | entries=3; proof holes=0 |
| fields-trust | entries=4; proof holes=0 |
| structural-trust | entries=2; proof holes=0 |
| owned-store | cases=3532; execution lanes=2; literal witnesses=15; mutants=6 |
| flat-store | bun=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621); mutants=9; native=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621) |
| recursion | fixtures=19; mutants=3 |
| fields-wasm | boundaries=30; fixtures=8; mutants=4 |
| modules | artifact preservation probes=80; byte identity pairs=23; check observations=126; compile observations=126; eval observations=142; execution lanes=2; fixtures=63; mutants=14; pin observations=22; proof entries=4; reference calls=71; tampered base observations=6; trust audits=46; wasm observations=58 |
| census | classes=42; declarations=1137; files=65 |
| perch-context | fixtures=33; mutants=8 |
| lint:verify | law rules=8; tests=168 |
| bootstrap | corpus=840; mutants=9; reached=2; stages=8 |
| classification | fixtures=17; mutants=6 |
| io-host | cli runs=6; conformance runs=86; errno=[2, 9, 20, 21, 22, 92]; fixtures=20; host boundaries=22; mutants=6; review=(empty write=4; mutants=3; oracle controls=14; secret paths=21; seed runs=12); seed fixtures=40; seed runs=109; stress=(left binds=100000; right binds=100000) |
| literals | agree eval observations=886; agree fixtures=34; artifact preservation probes=148; boundary probes=8; byte identity pairs=34; check observations=216; compile observations=216; eval observations=1034; execution lanes=2; fixtures=108; invalid fixtures=44; mutant eval observations=6; mutant verdict observations=12; mutant wasm observations=5; no artifact probes=148; proof entries=3; proof laws=32; reference calls=468; result byte identity pairs=5; result calls=61; result display observations=122; result fixtures=5; semantic mutants=21; trust audits=68; unsupported fixtures=30; wasm observations=886 |

Receipt drift: identical=64; semantic=16; volatile-only=7. The 15
semantic drifts in shared receipts are the same 15 as in rounds 2 to 4
(source hashes and derived code), left for the coordinator. The literals
receipt was copied from the run's normalized output after every recorded
input hash was checked against the tree.

All 13 `src/*PROOF.bend` entries print `All terms check.`; the two new laws
fail when their right-hand side is changed.

### Offline preflight

- The compiler-manifest preflight reports 32 groups and 0 structural
  blockers. literal-patterns stays at 47995/48000 bytes, because
  `literal-matrix.bend` is unchanged; a first draft that put the helper and
  its laws there reached 48820 and was moved to `check.bend` and
  `check-LAWS.bend`. checking is 45288/48000 and checker-laws 20154/48000.
- Per changed file (`--preflight FILE`), truncated-context counts equal
  those at `3246fa3`: check.bend 6, check-LAWS.bend 1, check-PROOF.bend 0,
  literal-check.bend 0. The single-file compositions of check.bend
  (82151 bytes) and check-LAWS.bend (52828) were already over the limit
  before this round (81135 and 51605).
- Zero provider requests were made. Live Perch review remains the
  coordinator's.

### Known limits

- A catch-all after rows that name every constructor (`SNil{}` and
  `SCon{c, t}`, then `y: zzz`) is dead in Knot's plan. The seed checks it in
  a default continuation where the scrutinee is neither constructor, and
  rejects the book; Knot reports `Unsupported check dead-arm`. This is safe
  under D4 but less precise than before the fix, which said Invalid. No
  frozen book has this shape; the 480-book sweep found four.
- A dead leaf is checked in the scope of each path where it is dead. A live
  row is also checked, as a dead leaf, on paths that shadow it; a failure
  that appears only there is Unsupported. The seed does not check those
  occurrences, so no Invalid is lost.

## Review round 4

The coordinator's review of `f3a81fa` (literals review fix round 3 in the
coordinator's numbering) confirmed one major finding and settled two
questions: the modules-owner sign-off is granted, and merging with
`campaign/modules` and `main` stays deferred (nest, then modules, then
literals). No history was rewritten.

| Commit | Content |
| --- | --- |
| `60a4795` | Freeze: five result books, 61 seed calls, each with the display Knot must print |
| `d050416` | Sign-off on the literals amendment in `CONTRACT.json` and the modules SPEC |
| `16a35cd` | Primitive results display as the seed's literals; gate wiring, three mutants, four laws |

| Finding | Disposition | Evidence |
| --- | --- | --- |
| [major] U32 and Char results render as constructor tags: wrong output with exit 0, or InternalFailure on seed-valid books | Fixed in `16a35cd`. U32 and Char are scalar `Value{type_id,bits}` terms, and the display read the bits as a constructor index. `shape` in `eval.bend` now asks the value's datatype first. An installed primitive shows the seed's literal, which reads back as the value (`300`, `3n`, `'a'`, `"a\n"`), inside records too. Other data keeps the `Name{a,b}` frame that the fields and recursion suites pin. `quoted` in `primitive-eval.bend` inverts the reader's escape table and follows the seed's quote rule and raw/escaped ranges. | `results.json` (5 books, 61 calls) covers `main -> U32`, `main -> Char`, String, Nat and records with U32, Char, Nat, String, enum, Bool and nested fields. All 122 displays (both lanes) match exactly. The reviewer's `p13_render`/`p12_ret` calls now print `0`, `'\0'`, `'\u{1}'`, `""`, `"\0"`, `Box{0,'\0'}`, `Box{1,'a'}`, `300`, `"hi"`, `3n` and `'a'`. The law `primitive_fields_display_as_literals` fails on the pre-fix evaluator with `InternalFailure eval result-tag`. Mutants: constructor-tag-display, quote-blind-escape and raw-delete. |
| Modules-owner sign-off | Recorded in `d050416`, as decided by the coordinator. | `module_loading.literals_amendment` reads "approved by the coordinator, 2026-09-28". |

Before the fix, reproduced at `f3a81fa` (native and Bun lanes agree):
`u0` printed `Evaluated\t0\t0\t#U32{}`, `c0` `Chr{}`, `sn` `SCon{Chr{},SNil{}}`,
`b0` `Box{#U32{},Chr{}}`. `c1`, `b1`, `ru`, `rs`, `rc` and `main -> U32` gave
`InternalFailure\teval\tresult-tag` (exit 6).

The second `Evaluated` column is a U32 or Char value's bits and otherwise the
constructor tag; `src/SPEC.md` and `CONTRACT.json` (`literals.result_display`)
now say so. The law count is 32: the three proof entries hold 20, 7 and 5
laws. `CONTRACT.json` said 27 and the gate recorded 28 before this round.

### Differential sweeps

Seed display against both Knot evaluator lanes on generated books, at
`16a35cd`. A record's seed text is compared after replacing `, ` with `,`;
no generated leaf contains `, `.

| Sweep | Books | Lane observations | Mismatches |
| --- | ---: | ---: | ---: |
| 726 codes in Strings (0-299, both sides of 0x7f, 0x80, 0x9f, the surrogate edges, U+FFFD-U+10000, U+10FFFE-U+110001, U32 max, 300 random scalars, 100 random U32) | 12 | 24 | 0 |
| The same 726 codes as Char fields of 16-field records | 46 | 92 | 0 |
| 160 U32 values (edges and random) and 36 Nat values up to 3000n as record fields | 13 | 26 | 0 |

Scripts are in the executor scratchpad (`impl-literals/r4/sweep*.py`).

All 13 `src/*PROOF.bend` entries print `All terms check.`.

### Gates on the round-4 fix head

`BEND_NO_TELEMETRY=1 npm run -s gates` on `16a35cd` passed all 20
registered gates (exit 0) in 722.9 seconds with 4 workers. Load average was
14.6 at the start and 23.9 at the end (run directory `run-iiu07bcz`).
`npm run -s gates:verify` passed 18 tests. Counts are copied from the runner;
categories overlap and are not summed. This isolated run is the evidence for
`16a35cd`. The direct literals run cited in that commit's message overlapped
an interrupted earlier run in the same build directory and predates a
comment-only edit, so it is not cited here.

| Gate | Exact counts |
| --- | --- |
| frontend | boundaries=24; fixtures=14; lane observations=28; mutants=4 |
| checker | bound observations=16; bounds=2; budgets=10; fixtures=49; lane observations=98; mutants=7 |
| structural | bounds=4; fixtures=16; lane observations=64; mutants=7 |
| fields | bound observations=12; bounds=2; budgets=36; fixtures=40; host boundaries=6; lane observations=240; mutants=9 |
| wasm | boundaries=44; execution lanes=2; fixtures=25; mutants=7; reference calls=90; rejects=64 |
| wasm-trust | entries=3; proof holes=0 |
| fields-trust | entries=4; proof holes=0 |
| structural-trust | entries=2; proof holes=0 |
| owned-store | cases=3532; execution lanes=2; literal witnesses=15; mutants=6 |
| flat-store | bun=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621); mutants=9; native=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621) |
| recursion | fixtures=19; mutants=3 |
| fields-wasm | boundaries=30; fixtures=8; mutants=4 |
| modules | artifact preservation probes=80; byte identity pairs=23; check observations=126; compile observations=126; eval observations=142; execution lanes=2; fixtures=63; mutants=14; pin observations=22; proof entries=4; reference calls=71; tampered base observations=6; trust audits=46; wasm observations=58 |
| census | classes=42; declarations=1132; files=65 |
| perch-context | fixtures=33; mutants=8 |
| lint:verify | law rules=8; tests=168 |
| bootstrap | corpus=819; mutants=9; reached=2; stages=8 |
| classification | fixtures=17; mutants=6 |
| io-host | cli runs=6; conformance runs=86; errno=[2, 9, 20, 21, 22, 92]; fixtures=20; host boundaries=22; mutants=6; review=(empty write=4; mutants=3; oracle controls=14; secret paths=21; seed runs=12); seed fixtures=40; seed runs=109; stress=(left binds=100000; right binds=100000) |
| literals | agree eval observations=886; agree fixtures=34; artifact preservation probes=106; boundary probes=8; byte identity pairs=34; check observations=174; compile observations=174; eval observations=992; execution lanes=2; fixtures=87; invalid fixtures=38; mutant eval observations=6; mutant verdict observations=9; mutant wasm observations=5; no artifact probes=106; proof entries=3; proof laws=32; reference calls=454; result byte identity pairs=5; result calls=61; result display observations=122; result fixtures=5; semantic mutants=18; trust audits=68; unsupported fixtures=15; wasm observations=886 |

Receipt drift: identical=64; semantic=16; volatile-only=7. The 15 semantic
drifts in shared receipts are source-hash and derived-code changes, left for
the coordinator; they are the same 15 as in rounds 2 and 3. The literals
receipt was copied from the run's normalized output after every recorded
input hash was checked against the tree.

### Offline preflight

- The compiler-manifest preflight reports 32 groups and 0 structural
  blockers, with no truncated units. Group sizes grew in evaluation
  (39498/48000), literal-source-machine (41708), runtime-laws (34490),
  literal-primitives (17746) and literal-algebra-laws (25905).
  literal-types.bend, and so literal-patterns (47995/48000), is unchanged.
- Per changed file (`--preflight FILE`), the blocker counts equal those at
  `f3a81fa`: eval.bend 8 (the same truncated `Frame`, `State`, `Value`,
  `host`, `internal`, `invoke`, `run`, `step`), primitive-eval.bend 0,
  literal-LAWS.bend 0, literal-PROOF.bend 1, literal-core-LAWS.bend 4,
  literal-core-PROOF.bend 1. A first draft put `literal` in
  primitive-eval.bend, which gave `Datum` a fifth same-file user and
  truncated its unit (caller limit 4); `literal` moved to eval.bend.
- Zero provider requests were made. Live Perch review remains the
  coordinator's.

### Known limits

- Records keep Knot's `Name{a,b}` frame: the seed separates fields with
  `, `, qualifies an imported book's constructors and shows erased fields.
  Only primitive leaves are seed-exact. Generic data such as a
  `List<&2,U32>` result is still `Unsupported parse type-application`; once
  it is accepted, the seed's list and tuple sugar (`[1]`) will differ from
  the frame as well.
- The Node Wasm host observes enum results only. A Char-returning export
  would come back as an in-range ordinal (97 for `'a'`), so result books
  make no Wasm call.
- Host arguments stay enum ordinals. A U32 parameter accepts only ordinal 0
  (its one installed constructor) and reports `HostFailure invoke
  argument-range` otherwise (the reviewer's `p14_args` probe); a Nat or
  String parameter reports `structured-argument` for a nonzero ordinal.
- A String result longer than the 65,536-character display cap is
  `Exhausted inspect`; a longer build first exhausts the transition budget.

## Review round 3

The coordinator's review of `070a091` confirmed three findings: two blocking
D4 violations and the modules sign-off, which is coordinator action. Each
seed-derived freeze was committed before its fix, and every earlier
regression entry is unchanged (compared entry by entry after each `--write`).

| Commit | Content |
| --- | --- |
| `b6e0a15` | Freeze: escape-brace, escape-brace-unknown, promoted-split and three affine controls |
| `c5c7b25` | Escape fix (final). First promoted-binder fix, since superseded |
| `a88b14b` | Gate record for `c5c7b25` (superseded by this section) |
| `5ba2327` | Freeze: promoted-scrutinee, affine-scrutinee |
| `c7a1577` | Per-arm promotion (superseded) |
| `bd56a0d` | Freeze: promoted-column, affine-column |
| `905486e` | The seed's column-wide `+` promotion; `check.bend`, `check-LAWS.bend` and `check-PROOF.bend` byte-identical to `070a091` again |
| `530a5c1` | Freeze: affine-default-scrutinee, -binder, -string (seed-invalid books that `905486e` accepted) |
| `0da2aae` | Binder rows name their column's unrefined value, as the seed's default continuation does |

Two commit-message errata; history is not rewritten.
- The `0da2aae` message lost two `+` characters to shell substitution. It
  should read "that column's own `+` marks" and "a field-level `+`".
- The `982594f` message gives wrong sweep totals. The correct figures are
  2236 matrix books (848 replayed, 848 in the second draw, 240 and 300) and
  200 escape books; the table below is correct.

| Finding | Disposition | Evidence |
| --- | --- | --- |
| [blocking] an escape followed by `{` is `Invalid lex escape` | Fixed in `c5c7b25`. `glyph` opened a code point on any `\X{` and rejected X other than u or U. The seed's `parse_char` takes the code-point path only when `u{hex}` matches (case-insensitive); otherwise it reads X from its escape table. `glyph` now has its own `\u{` and `\U{` arms, and every other escape falls through to the table. The law `escape_before_brace` pins `"\n{"` as code 10 with `{` left over. | escape-brace (seed-valid, 23 calls) covers the seven escapes before `{` plus `"\n}"`, `"ab{"`, `"\u{41}{"` and `"\U{41}{"`. escape-brace-unknown pins `"\q{"` as `Invalid lex escape`. The broad-unicode-escape mutant restores the old arm and is killed. |
| [blocking] a promoted binder over a split Nat or String column is `Invalid affine-reuse` | Fixed in `905486e` and `0da2aae` by following the seed's `match_flatten`. A column's binder quantity joins the `+` marks of that column's binder rows, and it covers every row and every field opened from the column. A binder row is also checked in the default continuation, where the column is unrefined. `literal-matrix.bend` promotes a column's scope binding when any row binds it with `+`, then reads the column back from the scope, so its fields and aliases follow. Binder-row aliases, including the column's own name, bind the unrefined value. Constructor rows keep the rebuilt value. Erased columns never reach the matrix. | Seed-valid books: promoted-split (29 calls), promoted-scrutinee (29) and promoted-column (37). Seed-invalid controls, all `Invalid check affine-reuse`: affine-split-alias, -field, -tail, affine-scrutinee, affine-column and affine-default-scrutinee, -binder, -string. The unlifted-promoted-column mutant is killed by promoted-column; it also turns promoted-split and promoted-scrutinee Invalid. The refined-default-binder mutant is killed by affine-default-scrutinee, which it compiles to `Built`. |
| [major] modules-owned code, gate and `--bundle` defaults; sign-off and merge order | Disputed as an executor defect. The finding and its verifier both call it coordinator action, and the verifier confirmed that the `e088dea` audit change is not a weakening. This round changes no modules-owned file: `git diff 070a091..HEAD` is empty for `base-load`, `load`, `qualify`, the three CLIs, `driver`, `CONTRACT.json` and `tests/compiler-modules`. | Open for the coordinator: modules-owner sign-off on the [literals amendment](../compiler-modules/SPEC.md#literals-amendment) and the raised defaults. `campaign/modules` (`0111f13`, an ancestor of this branch) merges to main before this branch. |

Two intermediate fixes were wrong in ways the sweeps exposed, and neither
survives:
- `c5c7b25` promoted only the binder's own uses.
- `905486e` let a field's `+` make its parent's catch-all duplicable. That
  accepted 13 seed-invalid books in the scrutinee-reuse sweep.

### Differential sweeps

Each sweep compares the seed with Knot check, eval and compile (native lane)
and the Node run of the emitted Wasm. The "before" columns were measured at
`070a091`. Each "final" column was measured at `0da2aae`.

| Sweep | Books | Before: seed-valid, Knot Invalid | Final: seed-valid, Knot Invalid | Final: seed-invalid, Knot accepts | Final value or lane mismatch |
| --- | ---: | ---: | ---: | ---: | ---: |
| Escapes: 10 leads (seed escapes, u, U, q) by 10 followers, in String and Char literals | 200 | 21 | 0 | 0 | 0 |
| The reviewer's single-column matrix fuzz, the same 848 books replayed | 848 | 54 | 0 | 0 | 0 |
| A second draw from that generator | 848 | not run | 0 | 0 | 0 |
| Promoted String and Char rows (`+s`, `SCon{c, +t}`, `+c`) | 240 | 38 | 0 | 0 | 0 |
| Rows reusing the matched value `v` beside `+`, plain and `_` rows | 300 | 115 | 0 | 0 (13 at `905486e`) | 0 |

Scripts are in the executor scratchpad (`impl-literals/r3/{esc,fuzz}`).
Their books are single-column matrices. Four two-column probes are
`Unsupported parse match-scrutinees` in Knot, as before. The seed's
per-column rule for them was confirmed by hand: a `+` on `a` does not promote
`b`. Nested field patterns and syntax outside these generators are not
covered.

All 13 `src/*PROOF.bend` entries print `All terms check.`.

### Gates on the round-3 fix head

`BEND_NO_TELEMETRY=1 npm run -s gates` on `0da2aae` passed all
20 registered gates (exit 0) in 512.3 seconds with 4 workers. Load average was 23.9 at the start and
14.8 at the end (run directory `run-32yfjw8p`). `npm run -s gates:verify` passed 18
tests. Counts are copied from the runner; categories overlap and are not
summed.

| Gate | Exact counts |
| --- | --- |
| frontend | boundaries=24; fixtures=14; lane observations=28; mutants=4 |
| checker | bound observations=16; bounds=2; budgets=10; fixtures=49; lane observations=98; mutants=7 |
| structural | bounds=4; fixtures=16; lane observations=64; mutants=7 |
| fields | bound observations=12; bounds=2; budgets=36; fixtures=40; host boundaries=6; lane observations=240; mutants=9 |
| wasm | boundaries=44; execution lanes=2; fixtures=25; mutants=7; reference calls=90; rejects=64 |
| wasm-trust | entries=3; proof holes=0 |
| fields-trust | entries=4; proof holes=0 |
| structural-trust | entries=2; proof holes=0 |
| owned-store | cases=3532; execution lanes=2; literal witnesses=15; mutants=6 |
| flat-store | bun=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621); mutants=9; native=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621) |
| recursion | fixtures=19; mutants=3 |
| fields-wasm | boundaries=30; fixtures=8; mutants=4 |
| modules | artifact preservation probes=80; byte identity pairs=23; check observations=126; compile observations=126; eval observations=142; execution lanes=2; fixtures=63; mutants=14; pin observations=22; proof entries=4; reference calls=71; tampered base observations=6; trust audits=46; wasm observations=58 |
| census | classes=42; declarations=1114; files=65 |
| perch-context | fixtures=33; mutants=8 |
| lint:verify | law rules=8; tests=168 |
| bootstrap | corpus=814; mutants=9; reached=2; stages=8 |
| classification | fixtures=17; mutants=6 |
| io-host | cli runs=6; conformance runs=86; errno=[2, 9, 20, 21, 22, 92]; fixtures=20; host boundaries=22; mutants=6; review=(empty write=4; mutants=3; oracle controls=14; secret paths=21; seed runs=12); seed fixtures=40; seed runs=109; stress=(left binds=100000; right binds=100000) |
| literals | agree eval observations=886; agree fixtures=34; artifact preservation probes=106; boundary probes=8; byte identity pairs=34; check observations=174; compile observations=174; eval observations=992; execution lanes=2; fixtures=87; invalid fixtures=38; mutant eval observations=3; mutant verdict observations=9; mutant wasm observations=5; no artifact probes=106; proof entries=3; proof laws=28; reference calls=454; semantic mutants=15; trust audits=68; unsupported fixtures=15; wasm observations=886 |

Receipt drift: identical=64; semantic=16; volatile-only=7. The 15 semantic drifts in shared receipts are
source-hash and derived-code changes, left for the coordinator, and they are
the same 15 as in round 2. The literals receipt was copied from the run's
normalized output after every recorded input hash was checked against the
tree.

### Offline preflight

- The compiler-manifest preflight reports 32 groups and 0 structural
  blockers.
- literal-patterns is at 47995 of its 48000 composition bytes. To fit, a
  single-use helper was inlined, and the column promotion has no law; three
  frozen books and two mutants pin it instead. The next change to this group
  must free bytes first.
- The changed declarations were run with
  `--task=tests/compiler-literals/README.md`: `glyph`, `promoted`,
  `promote`, `capture`, `renamed`, `run` and `escape_before_brace`.
  - `run` is truncated (context-helper-limit).
  - Composition is unavailable: 56308 of 48000 bytes, with 11 collaborators
    outside one group.
- Zero provider requests were made. Live Perch review remains the
  coordinator's.

## Review round 2

The coordinator's review of `3cf9705` confirmed four findings. Reproducing
them exposed two more defects of the same class: the new `Literal` and
`Offset` syntax nodes were unhandled outside the primitive matrix. Commit
`020394e` froze 23 seed-derived books in
[regressions.json](regressions.json) before any code change; `585cf0a` fixes
them. The ten round-1 entries are byte-identical.

| Finding | Disposition | Evidence |
| --- | --- | --- |
| [blocking] unannotated let-bound literals and Nat offsets accepted | Fixed. `check.bend` resolves the literal, then requires a wanted type through `annotated` (the former `matrix_wanted`, shared by literals, offsets and literal matches), reporting `Invalid\tcheck\tannotation-required`. Resolving first keeps literal-without-base's `unknown-type` verdict. | Nine seed-rejected books (`n = 3`, `+n = 3`, `c = 'a'`, `n = 3n`, `+n = 3n`, `s = "ab"`, `+s = "ab"`, `n = 2n+m`, `n = 0n+3n`) pin that prefix; the seed-accepted let-annotated control (U32, Char, Nat offset, String) agrees in 9 calls. The `inferred-let-literal` mutant compiles `n = 3` to `Built` and is killed. |
| Found while reproducing: `0n+t` | Fixed. The seed reads `kn+t` as k successors around t, so `0n+t` is t. Knot rewrote it to `Nat.add(0n,t)`, making the seed-valid `U32.is_eq(0n+x,3)` and `case 0n+p` on U32 or String columns Invalid (D4); the review's proposed fix would also have rejected the seed-valid `n = 0n+m`. `parse.bend`'s `offset` returns t for a zero count, so every parsed offset spells a successor. | The offset-zero book agrees in 13 calls (inferred let, checked argument, scrutinee, Nat/U32/String binder arms); `case 0n+p: p` on a datatype is `Unsupported\tcheck\tvariable-pattern` like any binder. The `kept-zero-offset` mutant rejects offset-zero as `Invalid pattern-type` and is killed. |
| [major] modules-owned code, gate and `--bundle` defaults; sign-off pending | Not an executor action; disputed as a finding against this branch. Round 2 changes no modules-owned file (`base-load`, `load`, `qualify`, the CLI defaults or the modules gate). The amendment is recorded in [the modules contract](../compiler-modules/SPEC.md#literals-amendment) and `src/CONTRACT.json` `module_loading.literals_amendment`, both marked pending. | The modules gate passes unchanged on this head (63 fixtures, 71 calls, 46 audits, 14 mutants). Sign-off belongs to the coordinator and the modules owner before merge. |
| [major] literal or offset scrutinee is InternalFailure | Fixed. `scope.bend`'s `scrutinee` reports `Invalid\tcheck\tconstructor-scrutinee`, as for a constructor; the seed calls these values already constructed. | Five books (`match 3`, `'a'`, `3n`, `"ab"`, `1n+m`) pin the prefix. The `internal-literal-scrutinee` mutant restores the InternalFailure and is killed. |
| [major] literal or offset arm on a datatype is InternalFailure | Fixed. `check.bend`'s `pattern` reports `Invalid\tcheck\tpattern-type`: datatype scrutinees never enter the primitive matrix, so a literal spells no constructor of theirs. Found alongside: `patterns.bend`'s `binder` sent a literal field pattern (`Box{3}`, `Cell{1n+p}`) to InternalFailure; it now reports `Unsupported\tcheck\tnested-field-pattern`, as for a nested constructor. | Four books (`case 3`, `"a"`, `1n+p` on Answer; `case 0` on Bool) pin `pattern-type`; two single-arm field books pin `nested-field-pattern`. The `unsupported-literal-pattern` mutant reports Unsupported instead of the seed's Invalid and is killed. |

A differential sweep of the reviewers' 406 probe books (seed `--check-only`
against Knot check, before and after the fix) found no seed-valid book
reported Invalid, no seed-invalid book accepted and no InternalFailure after
the fix. The 18 changed verdicts are the nine let forms and nine
InternalFailures. All 13 `src/*PROOF.bend` entries print `All terms check.`.

### Gates on the round-2 fix head

`BEND_NO_TELEMETRY=1 npm run -s gates` on `585cf0a` passed all 20 registered
gates (exit 0) in 422.8 seconds with the default four workers, at load
average 9.9 rising to 14.6. `npm run -s gates:verify` passed 18 tests. Counts
are copied from the runner. Categories overlap and are not summed.

| Gate | Exact counts |
| --- | --- |
| frontend | boundaries=24; fixtures=14; lane observations=28; mutants=4 |
| checker | bound observations=16; bounds=2; budgets=10; fixtures=49; lane observations=98; mutants=7 |
| structural | bounds=4; fixtures=16; lane observations=64; mutants=7 |
| fields | bound observations=12; bounds=2; budgets=36; fixtures=40; host boundaries=6; lane observations=240; mutants=9 |
| wasm | boundaries=44; execution lanes=2; fixtures=25; mutants=7; reference calls=90; rejects=64 |
| wasm-trust | entries=3; proof holes=0 |
| fields-trust | entries=4; proof holes=0 |
| structural-trust | entries=2; proof holes=0 |
| owned-store | cases=3532; execution lanes=2; literal witnesses=15; mutants=6 |
| flat-store | bun=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621); mutants=9; native=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621) |
| recursion | fixtures=19; mutants=3 |
| fields-wasm | boundaries=30; fixtures=8; mutants=4 |
| modules | artifact preservation probes=80; byte identity pairs=23; check observations=126; compile observations=126; eval observations=142; execution lanes=2; fixtures=63; mutants=14; pin observations=22; proof entries=4; reference calls=71; tampered base observations=6; trust audits=46; wasm observations=58 |
| census | classes=42; declarations=1111; files=65 |
| perch-context | fixtures=33; mutants=8 |
| lint:verify | law rules=8; tests=168 |
| bootstrap | corpus=801; mutants=9; reached=2; stages=8 |
| classification | fixtures=17; mutants=6 |
| io-host | cli runs=6; conformance runs=86; errno=[2, 9, 20, 21, 22, 92]; fixtures=20; host boundaries=22; mutants=6; review=(empty write=4; mutants=3; oracle controls=14; secret paths=21; seed runs=12); seed fixtures=40; seed runs=109; stress=(left binds=100000; right binds=100000) |
| literals | agree eval observations=650; agree fixtures=30; artifact preservation probes=88; boundary probes=8; byte identity pairs=30; check observations=148; compile observations=148; eval observations=738; execution lanes=2; fixtures=74; invalid fixtures=29; mutant eval observations=3; mutant verdict observations=6; mutant wasm observations=5; no artifact probes=88; proof entries=3; proof laws=27; reference calls=336; semantic mutants=12; trust audits=60; unsupported fixtures=15; wasm observations=650 |

Receipt drift: identical=64; semantic=16; volatile-only=7. Fifteen semantic
drifts are source-hash and derived-code changes in shared receipts, left for
the coordinator. The literals receipt is copied from the run's normalized
output after every recorded input hash was checked against the tree.

### Offline preflight

With `--task`, the five changed declarations (`offset`, `annotated`,
`pattern`, `scrutinee`, `binder`) have complete context; composition is
unavailable (byte limit, collaborators outside one group). The four whole
files report the same 15 truncated units as at `020394e`. A zero-offset parser
law was tried and dropped: importing `parse.bend` into literal-matrix-LAWS
breaks the literal-patterns manifest closure and its 48000-byte bound. Zero
provider requests were made; live Perch review remains the coordinator's.

## Review round 1

The coordinator's review of `2ea222e` confirmed five findings. Each finding
has a seed-derived regression book, committed before its fix, in
[regressions.json](regressions.json). The fixes are new commits on
`campaign/literals` after merging `main` (`0798a27`) and `campaign/modules`
0111f13 (`9b3425e`).

| Finding | Disposition | Evidence |
| --- | --- | --- |
| [blocking] spaced Nat offset `+` accepted | Fixed. An Offset forms only when the literal's `At.end` equals the `+` token's `At.start`. Otherwise the parser reports `Unsupported\tparse\toperator\t`. | Four seed-rejected books expect that prefix; four seed-accepted controls (`1n+ p`, `1n+ +p`, `1n++p`, `3n+ x`) agree. The `spaced-offset` verdict mutant compiles `case 1n + p` to `Built` and is killed. |
| [major] modules audit rejects BaseIntrinsic | Adapter extended as authorized. The modules contract now has a literals amendment. Sign-off on the rewritten clauses and the raised `--bundle` defaults is **pending with the coordinator and the modules owner**. | The modules gate passes with unchanged counts. The audit requires a three-way partition of all 466 declarations in pinned order and declared intrinsic rows; the offline controls are recorded in `e088dea`. |
| [major] gate flakes under host load | Coordinator decision. `main`'s `KNOT_GATE_TIMEOUT_SCALE` (4 in the runner) now applies to every gate, including this one, and no budget was edited. The passing run below used the default four workers at load average 9.9 falling to 5.7. | The run is `run-hsj2ido2`, recorded in [campaign-gates.json](receipts/campaign-gates.json). Native CLI builds remain the dominant cost. |
| [major] seed-valid `U32{w}` reported Invalid | Fixed. `lookup` in literal-matrix.bend reports `Unsupported\tcheck\tu32-constructor` for the Base U32 constructor at all three constructor sites. `Chr{x}` expressions already agree with the seed. | The pattern and rebuild books expect the new prefix. A `U32{Word.zero(32n)}` book pins `Unsupported\tload\tbase-function-result`. The `invalid-u32-constructor` verdict mutant restores `Invalid` and is killed. |
| [major] Bun evaluator memory fault on long Strings | Fixed. `count`, `onto` (reverse-append) and a verdict-carrying `equal` are tail calls with accumulators. Three new laws cover append order, length count and length mismatch. | 40000-Char and 131072-Char books agree in both evaluator lanes and in Wasm; before the fix the Bun lane faulted on every call. Up to the 2^21-code bound, both lanes report identical Exhausted verdicts. The evaluator-only `append-reversed` mutant is killed. |

### Gates on the fix head

`BEND_NO_TELEMETRY=1 npm run -s gates` passed all 20 registered gates (exit 0)
in 311.7 seconds, and `npm run -s gates:verify` passed 18 tests. Counts are
copied from the runner. Categories overlap and are not summed.

| Gate | Exact counts |
| --- | --- |
| frontend | boundaries=24; fixtures=14; lane observations=28; mutants=4 |
| checker | bound observations=16; bounds=2; budgets=10; fixtures=49; lane observations=98; mutants=7 |
| structural | bounds=4; fixtures=16; lane observations=64; mutants=7 |
| fields | bound observations=12; bounds=2; budgets=36; fixtures=40; host boundaries=6; lane observations=240; mutants=9 |
| wasm | boundaries=44; execution lanes=2; fixtures=25; mutants=7; reference calls=90; rejects=64 |
| wasm-trust | entries=3; proof holes=0 |
| fields-trust | entries=4; proof holes=0 |
| structural-trust | entries=2; proof holes=0 |
| owned-store | cases=3532; execution lanes=2; literal witnesses=15; mutants=6 |
| flat-store | bun=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621); mutants=9; native=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621) |
| recursion | fixtures=19; mutants=3 |
| fields-wasm | boundaries=30; fixtures=8; mutants=4 |
| modules | artifact preservation probes=80; byte identity pairs=23; check observations=126; compile observations=126; eval observations=142; execution lanes=2; fixtures=63; mutants=14; pin observations=22; proof entries=4; reference calls=71; tampered base observations=6; trust audits=46; wasm observations=58 |
| census | classes=42; declarations=1110; files=65 |
| perch-context | fixtures=33; mutants=8 |
| lint:verify | law rules=8; tests=168 |
| bootstrap | corpus=778; mutants=9; reached=2; stages=8 |
| classification | fixtures=17; mutants=6 |
| io-host | cli runs=6; conformance runs=86; errno=[2, 9, 20, 21, 22, 92]; fixtures=20; host boundaries=22; mutants=6; review=(empty write=4; mutants=3; oracle controls=14; secret paths=21; seed runs=12); seed fixtures=40; seed runs=109; stress=(left binds=100000; right binds=100000) |
| literals | agree eval observations=606; agree fixtures=28; artifact preservation probes=46; boundary probes=8; byte identity pairs=28; check observations=102; compile observations=102; eval observations=652; execution lanes=2; fixtures=51; invalid fixtures=11; mutant eval observations=3; mutant verdict observations=2; mutant wasm observations=5; no artifact probes=46; proof entries=3; proof laws=27; reference calls=313; semantic mutants=8; trust audits=56; unsupported fixtures=12; wasm observations=606 |

Receipt drift: identical=64; semantic=16; volatile-only=7. The semantic drifts are source-hash
and derived-code changes in shared receipts, which are left for the coordinator
to refresh. Only this gate's receipt is copied from the run, after its input
hashes were checked against the working tree.

The first full run on `ff49ddb` failed two gates. perch-context failed because
the merged `checking` group, and three literal groups after the U32 helper
first imported the catalog, exceeded the 48000-byte composition bound. census
failed on a stale hosts inventory. `3292322` fixed both without changing an
assertion.

### Offline preflight

The eight changed source files report 25 structural blockers (24 truncated
units and the ad-hoc composition bound), identical to the same files at
`9b3425e`. Every new declaration has complete context. The compiler-manifest
preflight reports 32 groups and 0 structural blockers. Zero provider requests
were made; live semantic and style Perch review remain the coordinator's.

### Known limits

The raised bundle defaults and the rewritten modules clauses await sign-off.
Frozen shared receipts need the coordinator's refresh after merging. Native
CLI build time still dominates gate wall time under load. A literal
`U32{...}` construction is reachable only through Base Word functions, which
the loader reports as Unsupported first.

## Original implementation run (`2ea222e`): deterministic gates

All 16 registered gates completed with exit 0 in one serial runner invocation. The runner self-test also passed all 18 tests. Counts below are copied from the runner; categories overlap and are not summed.

| Gate | Exact counts |
| --- | --- |
| frontend | boundaries=24; fixtures=14; lane observations=28; mutants=4 |
| checker | bound observations=16; bounds=2; budgets=10; fixtures=49; lane observations=98; mutants=7 |
| structural | bounds=4; fixtures=16; lane observations=64; mutants=7 |
| fields | bound observations=12; bounds=2; budgets=36; fixtures=40; host boundaries=6; lane observations=240; mutants=9 |
| wasm | boundaries=44; execution lanes=2; fixtures=25; mutants=7; reference calls=90; rejects=64 |
| wasm-trust | entries=3; proof holes=0 |
| fields-trust | entries=4; proof holes=0 |
| structural-trust | entries=2; proof holes=0 |
| owned-store | cases=3532; execution lanes=2; literal witnesses=15; mutants=6 |
| flat-store | bun=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621); mutants=9; native=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621) |
| recursion | fixtures=19; mutants=3 |
| fields-wasm | boundaries=30; fixtures=8; mutants=4 |
| modules | artifact preservation probes=60; byte identity pairs=21; check observations=102; compile observations=102; eval observations=118; execution lanes=2; fixtures=51; mutants=5; pin observations=22; proof entries=4; reference calls=59; tampered base observations=6; trust audits=42; wasm observations=54 |
| census | classes=40; declarations=1047; files=64 |
| lint:verify | law rules=8; tests=127 |
| literals | agree eval observations=560; agree fixtures=25; artifact preservation probes=32; boundary probes=8; byte identity pairs=25; check observations=82; compile observations=82; eval observations=592; execution lanes=2; fixtures=41; invalid fixtures=11; mutant eval observations=2; mutant wasm observations=5; no artifact probes=32; proof entries=3; proof laws=24; reference calls=287; semantic mutants=5; trust audits=50; unsupported fixtures=5; wasm observations=560 |

Receipt drift: identical=63; semantic=12; volatile-only=7. Shared receipts were left for the coordinator. Only the literal receipt is copied from this run, after checking every recorded input hash against the final working tree.

The [campaign receipt](receipts/campaign-gates.json) retains counts, source/dependency identity, drift classification and measured execution metadata. [The literal receipt](receipts/literals.json) contains every new observation.

## Fixture and mutation coverage

The original freeze has 40 books and 275 seed calls; the supplemental book adds 12. The 25 accepted books contribute 280 calls, tested in both evaluator and compiler lanes. All 11 Invalid and five Unsupported books retain their frozen outcomes; the latter retain exact prefixes. Five type-correct mutants are killed: signed compare, trapping division by zero, masked shifts, merged surrogates and a Nat offset off by one. Compiler/typecheck failures do not count as kills.

Three complete new proof entries check 24 filled laws. These prove the named arithmetic guards, literal-reading cases, source transitions, matrix expansion and the legacy capability boundary. They are not a whole-compiler or all-input intrinsic refinement proof.

## Offline preflight

units=590; files=35; unranked files=0; empty files=0; truncated units=124; truncated by limit=(caller-or-byte-limit=20; context-file-limit=44; context-helper-limit=72); supporting role impossible=125; role gap units by reason=(context-file-limit=44; context-helper-limit=72; nonlocal-import=7; truncated-context=124); max state bytes=45570; composition available=False; composition reasons=['unresolved_composition_context', 'composition_byte_limit'].

All 35 changed Bend files parsed. Every new family closes local imports and is below 48000 source bytes. Eight family compositions have complete local context; emission retains the published ByteOutput context blocker. Declaration context truncation remains, so every family reports attention. Zero provider requests were made. Compression, Delight, memetic identity, Anticipation, Payoff and Galaxy-brain ratings remain unmeasured; no live style pass is claimed.

| Family | Source bytes | Truncated units | Structural blockers | Composition context available |
| --- | ---: | ---: | ---: | --- |
| literal-frontend | 18032 | 6 | 6 | True |
| literal-primitives | 14979 | 2 | 2 | True |
| literal-types | 30652 | 14 | 14 | True |
| literal-patterns | 46105 | 23 | 23 | True |
| literal-source-machine | 37938 | 24 | 24 | True |
| literal-instruction-graph | 23473 | 16 | 16 | True |
| literal-machine-runtime | 22304 | 5 | 5 | True |
| literal-emission | 42949 | 23 | 24 | False |
| literal-algebra-laws | 21490 | 7 | 7 | True |

[The compressed preflight receipt](receipts/preflight.json.gz) retains every declaration and family result.

## Prior failures and remaining work

The first full run exposed a legacy single-file literal misclassification and a non-tail token scan on the existing 50000-blank-line module. Both were fixed in implementation; existing assertions were not changed. Census approval also required regeneration of its inventory. Later native-build failures were timeouts and transient Clang lookup failure under high host load. A controlled native build took 51.023 seconds at high load and 15.624 seconds after load fell; this is scheduling evidence, not a compiler speedup claim. The final serial run retained every existing timeout and assertion.

Coordinator work: review/merge this branch, refresh shared receipts after integration, and run live semantic/style Perch. Other emitters must account for Literal, Intrinsic and Default core variants. The next language increment still needs generics/quantity arguments and broader pattern/recursion support. Primitive/structured host observations, reclamation (R3/R7), full intrinsic refinement and self-hosting remain outside this acceptance.
