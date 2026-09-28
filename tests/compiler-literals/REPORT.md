# Literals executor handoff

Implemented the frozen U32/Nat/Char/String surface through bundle parsing, checked literal matrices, independent source evaluation and the new `knot-literals-wasm-1` profile. The ABI retains unary Nat cells and uses a 64 MiB arena with explicit frames/returns for the frozen 65536-depth case. Base source bodies and trusted intrinsic lowerings have separate audit categories.

The original 40 fixtures and observations are unchanged. Commit `d3c1e7b` fixed the 12 supplemental bootstrap-helper calls before implementation. See [README.md](README.md) for the exact contract and limits.

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
