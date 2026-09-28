# Literals executor handoff

Implemented the frozen U32/Nat/Char/String surface through bundle parsing, checked literal matrices, independent source evaluation and the new `knot-literals-wasm-1` profile. The ABI retains unary Nat cells and uses a 64 MiB arena with explicit frames/returns for the frozen 65536-depth case. Base source bodies and trusted intrinsic lowerings have separate audit categories.

The original 40 fixtures and observations are unchanged. Commit `d3c1e7b` fixed the 12 supplemental bootstrap-helper calls before implementation. See [README.md](README.md) for the exact contract and limits.

## Review round 3

The coordinator's review of `070a091` confirmed three findings: two blocking
D4 violations and the modules sign-off, which is coordinator action. Commit
`b6e0a15` froze six seed-derived books in [regressions.json](regressions.json)
before any code change; `c5c7b25` fixes both D4 defects. The 33 earlier
regression entries are unchanged (compared entry by entry after `--write`).

| Finding | Disposition | Evidence |
| --- | --- | --- |
| [blocking] an escape followed by `{` is `Invalid lex escape` | Fixed. `glyph` opened a code point on any `\X{` and rejected X other than u/U. The seed's `parse_char` takes the code-point path only when `u{hex}` matches (case-insensitive) and otherwise reads X from its escape table. `glyph` now has its own `\u{` and `\U{` arms, and every other escape falls through to the table. The law `escape_before_brace` pins `"\n{"` as code 10 with `{` left over. | escape-brace (seed-valid, 23 calls) covers the seven escapes before `{` and the controls `"\n}"`, `"ab{"`, `"\u{41}{"` and `"\U{41}{"`; it agrees in both lanes and in Wasm. escape-brace-unknown pins `"\q{"` as `Invalid lex escape`. The `broad-unicode-escape` mutant restores the old arm and is killed (escape-brace becomes `Invalid lex escape`). |
| [blocking] a promoted binder over a split Nat or String column is `Invalid affine-reuse` | Fixed by propagating the promotion, not by reporting Unsupported. A matrix alias of a split column is rebuilt from that column's fields; a `+x` alias of an affine column counted those affine fields at every use. `check.bend`'s `variable` now passes the rebuild through `promoted`, which drops the field uses of a quantity-2 binding. Fields of a promoted parent already have quantity 2 (`patterns.bend` `quantity`), so only aliases of affine columns change. The evaluator and both emitters distinguish only erased from live quantities, so a copied rebuild needs no runtime change. Two checker laws state both sides: a promoted rebuild is fresh; an affine rebuild keeps its uses. | promoted-split (seed-valid, 29 calls): `1n+ +p` after literal and offset rows, `+x` after `0n`, before `0n` and after `Zero{}`, `+x` after `""`, and `SCon{c, +t}` after `"ab"`, each binder used twice; it agrees in both lanes and in Wasm. Three seed-invalid controls without `+` (`case x`, `case 1n+p`, `case SCon{c, t}`) stay `Invalid check affine-reuse`. The `affine-promoted-rebuild` mutant restores the plain rebuild and is killed (promoted-split becomes `Invalid check affine-reuse`). |
| [major] modules-owned code, gate and `--bundle` defaults; sign-off and merge order | Disputed as an executor defect. The finding and its verifier both call it coordinator action. The verifier also confirmed that the `e088dea` audit change is not a weakening. This round changes no modules-owned file: `git diff 070a091..c5c7b25` is empty for `base-load`, `load`, `qualify`, the three CLIs, `driver`, `CONTRACT.json` and `tests/compiler-modules`. | Open for the coordinator: modules-owner sign-off on the [literals amendment](../compiler-modules/SPEC.md#literals-amendment) and the raised defaults; merge `campaign/modules` (`0111f13`, an ancestor of this branch) to main before this branch. |

### Differential sweeps

Each sweep compares the seed with Knot check, eval and compile, and with the
Node run of the emitted Wasm. Scope is stated exactly; nothing outside it is
claimed. Round 2's sweep covered only the reviewers' probe books, which is
why it missed the escape defect.

- **Escapes, 200 books.** Leads: the seven seed escapes, `u`, `U` and `q`.
  Followers: none, `{`, `}`, `u`, `"`, `\`, `a`, a space, `{41}` and `{4g}`.
  Each pair appears once in a String-length book and once in a Char-code book.
  - At `070a091` (Bun lane): 21 seed-valid books were `Invalid lex escape`.
  - At `c5c7b25` (native lane): 67 books agree, with seed, evaluator and Wasm
    giving the same answer. 133 seed-invalid books are Invalid. No seed-valid
    book is Invalid, and no seed-invalid book is accepted.
- **Reviewer's single-column matrix fuzz, replayed.** The same 848 books
  (identical sources) through the reviewer's `fuzz.py`, retargeted to the fixed
  build.
  - The reviewer's run at `070a091` had 54 seed-valid books reported Invalid.
  - At `c5c7b25` there are none: those 54 moved from exit 2 to `Checked`, and
    the other 794 verdicts are unchanged (711 checked, 83 Invalid).
  - No evaluator, Wasm, check/compile or lane mismatch.
- **A second draw from the same generator,** 848 books (names 0–211 per kind):
  760 agree and 88 seed-invalid books are Invalid, with no mismatch.
- **Promoted String and Char binders,** 240 books from a variant generator
  that adds `+s`, `SCon{c, +t}` and `+c` rows. 106 contain a promoted binder,
  94 of them seed-valid.
  - At `070a091`: 38 seed-valid books were Invalid.
  - At `c5c7b25`: none. 215 agree, 25 seed-invalid books are Invalid, and there
    is no mismatch.

None of these sweeps covers two-column matrices, nested field patterns or
syntax outside the generators.

All 13 `src/*PROOF.bend` entries print `All terms check.`. A deliberately
false `promoted_rebuild_is_fresh` is rejected by `check-PROOF`.

### Gates on the round-3 fix head

`BEND_NO_TELEMETRY=1 npm run -s gates` on `c5c7b25` passed all 20 registered
gates (exit 0) in 400.3 seconds, with the default four workers. Load average
was 18.2 at the start and 8.4 at the end. `npm run -s gates:verify` passed 18
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
| census | classes=42; declarations=1118; files=65 |
| perch-context | fixtures=33; mutants=8 |
| lint:verify | law rules=8; tests=168 |
| bootstrap | corpus=807; mutants=9; reached=2; stages=8 |
| classification | fixtures=17; mutants=6 |
| io-host | cli runs=6; conformance runs=86; errno=[2, 9, 20, 21, 22, 92]; fixtures=20; host boundaries=22; mutants=6; review=(empty write=4; mutants=3; oracle controls=14; secret paths=21; seed runs=12); seed fixtures=40; seed runs=109; stress=(left binds=100000; right binds=100000) |
| literals | agree eval observations=754; agree fixtures=32; artifact preservation probes=96; boundary probes=8; byte identity pairs=32; check observations=160; compile observations=160; eval observations=850; execution lanes=2; fixtures=80; invalid fixtures=33; mutant eval observations=3; mutant verdict observations=8; mutant wasm observations=5; no artifact probes=96; proof entries=3; proof laws=28; reference calls=388; semantic mutants=14; trust audits=64; unsupported fixtures=15; wasm observations=754 |

Receipt drift: identical=64; semantic=16; volatile-only=7. The 15 semantic
drifts in shared receipts are source-hash and derived-code changes, left for
the coordinator; they are the same 15 as in round 2. The literals receipt was
copied from the run's normalized output after every recorded input hash was
checked against the tree.

### Offline preflight

- The six changed declarations were run with
  `--task=tests/compiler-literals/README.md`: `glyph`, `promoted`,
  `variable`, `escape_before_brace`, `promoted_rebuild_is_fresh` and
  `affine_rebuild_keeps_uses`.
  - All six have complete context: 0 truncated, 0 role-limited.
  - Composition is unavailable: 49255 of 48000 bytes, with 73 collaborators
    outside one group.
- The compiler-manifest preflight reports 32 groups and 0 structural blockers.
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
