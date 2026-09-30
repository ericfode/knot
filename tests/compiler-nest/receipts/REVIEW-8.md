# Nest review round 8

This round answers review round 1 of the Claude executor. All three confirmed
findings are **fixed**:

- **Blocking.** A `+` binder of a `Type`-kind type that is destructured before
  any variable use reported a false `Invalid check reusable-type`. The seed
  accepts such programs. Knot now judges the kind where the match frontier
  binds the binder, as the seed does.
- **Major (D21 record).** The record named only witnesses for the total
  irrefutable-first-row law. It now also names the frozen `matrix-work`
  control, which is a counterexample at the implemented quota. The law itself
  is unchanged.
- **Major (recursion contract).** `tests/compiler-recursion/SPEC.md` still says
  that reconstruction never qualifies, which the round-4 descent rule
  contradicts. The contract, `src/SPEC.md` and REVIEW-4.md now record the
  supersession.

| Commit | Change |
|---|---|
| `e0db57e` | D7 freeze before the repair: 37 seed-derived fixtures under `round8-fixtures/`, `round8-expectations.json` and `round8_seed.py` (150 seed calls; a replay without `--write` reports no differences) |
| `1f450e5` | The fix in `matrix.bend`, `patterns.bend`, `scope.bend` and `check.bend`; four frontier laws and two witnesses; the `nest-round8` gate with five mutants and the Type-kind generator `typekind.py`; runner registration, self-test, GATES.md, SPEC text and census approval (summary in the commit message) |
| `b87a971` | Three more whole-checker witnesses, so that every binding site has a law; falsification of every new law |
| `05d27e2` | The generator's evaluated set widened to every program with a `Type`-kind Wrap (the reviewer's a00196 has a `Data` Box) |
| `78f1758` | Receipts, falsification, preflight, the D21 and recursion-contract record corrections, LAW_REVIEW round 8, the contract and state entries and the Perch review-log entry |
| `8fc088c` | The witnesses build their programs from small named definitions, so no law calls `token` directly. This fixed a perch-context failure: the budget for `token`'s caller context was exceeded on `78f1758` |
| Final commit | This report, the refreshed round-8 receipts and the final-tree gate run (`round8-final-gates.json.gz`) |

Frozen expectations from earlier rounds are unchanged. No finding needed a
seed-derived amendment. A scan of all 1,007 tracked `.bend` files, comparing
the `99053a7` checker with the repaired one, changes a single first line: the
span of round-7 fixture t2, which is still `Invalid check reusable-type`.
Every other gate's assertions and every mutant anchor are unchanged.

## Finding 1 (blocking): false Invalid on a destructured `Type`-kind promotion

**Fixed.**

### The seed's rule

In the seed, `match_flatten` keeps lambda-case binders pending in `vars`. A `+`
row raises the pending binder's quantity: `patt_mark` joins the row's `Many`
into the binder. The binder becomes a lambda, and a `Many` lambda asks its type
to be `Data`, only at one of two points:

- a match on a later pending binder (the `else` branch), or
- a body that is not a match (the `body_flatten` default, which a `Local`/let
  also reaches).

When the binder is destructured first (the `v === x` branch), it never
becomes a lambda. Its fields take `quant_join(q, xq)`, so they inherit the
mark, and the same rule applies to each of them. An empty match on the binder
itself (`Efq`) binds nothing.

Knot judged the kind early, in two places. `matrix.bend::alias_bound` judged
it at the promotion, and `patterns.bend::fields` judged a promoted field's
quantity at its binding. This was so from the implementation commit `57a0c01`
onward. Round 7 froze the seed-rejected side (t2, `case +y: y`) without its
destructured twin.

### The repair

One idea covers both paths: a binder waiting on the match frontier may carry
a quantity above its kind, and **the kind is judged where the frontier binds
the binder**.

- `alias_bound` and `alias` no longer take the catalog or judge the kind. The
  round-7 rule, under which only a lambda-case binder takes a row's mark, is
  unchanged. `fields` no longer judges a field's promoted quantity.
- `scope.bend::ahead` lists the frontier ahead of a level.
- `patterns.bend` adds the binding sites. `kind` and `bound` judge the binders
  that a frontier step binds. `advance` binds the frontier ahead of a matched
  level; `branch` calls it, so it covers flat arms and matrix decisions.
  `close` binds the whole frontier and clears it.
- In `check.bend`, the four leaf forms (variable, constructor, call and let)
  close the frontier first, and `match_body` advances it, which covers
  zero-row matches.

The seed's variable-only columns and `Efq` bind nothing, so Knot's
`variable_step` and `empty_remainder` add no binding site. A remainder is
always at the head of the frontier.

### Evidence

- **Frozen fixtures (D7), `e0db57e`.** On `99053a7`, Knot reported `Invalid
  check reusable-type` on 32 of the 37 fixtures. The exceptions were the four
  `Data` controls (Checked) and y2 (Unsupported). After the repair, in both
  compiler lanes:
  - **destructured-promotion (17), the finding.** The reviewer's k1–k7, tk/t2,
    fu/Td5, tk/v1, tk/v6 and tk/u8; the pb generator hits a01432, a02809 and
    a02883; an inherited `Type`-kind field (k16); and x1, an empty `Type`-kind
    datatype matched with zero rows (on main, `Invalid empty-datatype`). All
    are Checked. A fielded parameter gets a host `probe` entry over Sel, so
    every call runs `f`.
  - **default-scrutinee (2).** y1 (`Type`, previously `Invalid`) and y2
    (`Data`) are `Unsupported check default-scrutinee`. This is the outcome
    the finding accepts for y1.
  - **kind-at-binding (14).** The reviewer's seed-rejected controls c1–c3,
    Td4, Td8, u2, v2 and x2, plus new negatives, all `Invalid check
    reusable-type`, with the seed reporting `expected : Data / observed :
    Type`. The new negatives are:
    - a let after the row (n1);
    - an inherited `Type`-kind field used directly (n2, n3);
    - a later flat match (n4), zero-row match (n5) and matrix split (n6)
      ahead of the promoted binder.
  - **data-control (4).** The `Data`-kind twins d1, d4, d7 and d8 are Checked.

  Frozen outcome counts: 37 fixtures. The seed accepts 23 (17 finding, 4
  controls, 2 default-scrutinee) and rejects 14. There are 150 seed calls.
  The seed, the evaluator and Wasm agree on all 146 calls of the 21 accepted
  books in both lanes (292 evaluator and 292 Wasm values). Wasm uses the
  fields profile for the 18 fielded books and the enum profile for k1, k8
  and x1 (x1 has no calls).
  A rejected fixture is rejected in check, evaluation and both compile
  profiles, and its artifact is preserved.
- **Generator.** `typekind.py` copies the reviewer's `sem-r8-probes/pb/gen.py`
  verbatim, from `def header` to `gen`. All 3,000 programs (random seeds 0 to
  2,999) are byte-identical to the reviewer's `pb/g` files.
  - Against `99053a7` it reports 5 false Invalid programs, the reviewer's set
    exactly: a00196, a01432, a02809, a02852 and a02883
    (`round8-typekind-before.json`).
  - On HEAD it reports 0 false acceptances and 0 false Invalid. The seed
    reports 1,161 Accepted and 1,839 Invalid. Knot reports 1,148 Accepted,
    1,796 Invalid and 56 Unsupported.
  - For each agreed acceptance that has a `+` binder and a `Type`-kind Wrap,
    one seeded `probe` call agrees between the seed and the Knot evaluator
    (375 values, `round8-typekind.json`).
  - Seventeen seed-rejected programs move from `Invalid reusable-type` to
    `Unsupported check default-scrutinee`. That outcome is non-accepting and
    allowed under D4. In each of them the seed rejects for another reason, for
    example a missing case, and Knot now stops at the default-region match
    before any binding site.
- **Reviewer probes.** Both lanes of both checkers ran over all probe roots,
  and the seed ran on every file whose Knot outcome changed.
  - `sem-r8-probes` and `refute-typekind-probes`: 7,639 files, including the
    pa (4,000) and pb (3,000) generators. 377 files change: 32 seed-accepted
    files go from Invalid to Checked and 1 to Unsupported; 323 seed-rejected
    files stay Invalid, with the diagnostic sometimes moving to the seed's own
    complaint (affine-reuse, missing-arm, already-matched); 21 seed-rejected
    files become Unsupported.
  - `sem-r7-probes`, `sem-r6-probes`, `sem-r5-probes`, `probes`,
    `refute-letalias-probes`, `scope-probes` and `empty-verify-probes`: 70,833
    files. 162 change: 160 seed-rejected files stay Invalid with a moved span
    or code, and two slow blow-up probes cross the harness timeout in opposite
    directions under load.
  - In every root, no seed-rejected program is Checked and no seed-accepted
    program is Invalid.
- **Laws** (`src/matrix-LAWS.bend`, filled in `src/matrix-PROOF.bend`).
  - Frontier laws:
    - `destructured_promotion_is_unbound`: a match on the promoted binder binds
      nothing ahead of it;
    - `later_match_binds_promotion`: a later match binds it, and is rejected;
    - `leaf_binds_promotion`: a leaf binds it, and is rejected;
    - `leaf_closes_frontier`: a leaf clears the frontier.
  - Whole-checker witnesses (`K.run`) at a `Type` kind:
    - a destructured promoted parameter and field check, with their literal
      core terms (the field bound at quantity 2);
    - returning the binder, a later matrix split and a later zero-row match
      are each rejected.

  All eight `src/*PROOF.bend` entries print `All terms check.`, and
  `nest-round8` reruns the matrix and lowering entries.
- **Falsification** (`round8-falsification.txt`). Each mutation of a binding
  site or of the frontier operations falsifies a named law. Judging the kind
  at `expand`'s alias stops earlier, at `lowering-PROOF`'s `expanded`. That is
  a proof-shape failure, because the proof mirrors the alias case. Its twin at
  `check.run`'s alias falsifies `destructured_promotion_witness`.
- **Mutants.** `nest-round8` kills five type-correct mutants in both lanes
  (10 semantic kills). Outside the harness, each mutant has these effects:

  | Mutant | Witness | Effect |
  |---|---|---|
  | `judge-kind-at-promotion` (the required mutant) | k1 | Restores the finding exactly: 17 fixtures (16 destructured, and y1) are Invalid again, and the generator reports the reviewer's 5 programs |
  | `judge-field-kind-at-binding` | k6 | The field half of the early judgement: k6, k16 and k7 are wrong, and the generator reports 1 false Invalid |
  | `skip-leaf-binding` | c2 | Over-accepts: 11 fixtures are wrong, and the generator reports 130 false acceptances |
  | `skip-split-binding` | n6 | Only n6 is wrong; the generator cannot see it |
  | `skip-empty-match-binding` | n5 | Only n5 is wrong; the generator cannot see it |

## Finding 2 (major): the D21 record omitted a known counterexample

**Fixed in the record.** The law is not weakened (D21).

`tests/compiler-nest/controls/matrix-work.bend` is a 13-column matrix whose
first row is 13 `_` with body `On{}`. The seed prints `On{}`. Knot reports
`Exhausted check budget` at the fixed 4,096-visit quota. The reason is that
`column_step` splits on a constructor head in any row, even when the first row
is irrefutable. By the recurrence `T(n+1)=2+2T(n)` that is 24,574 visits.

The trust inventory (`src/SPEC.md`), `CONTRACT.json` (`pattern_matrix.open_obligations`
and `unmet`), `LAW_REVIEW.md`'s D21 table and the campaign state's
`unmet_laws` now say three things:

- the total form is false at the implemented quota, with matrix-work as the
  counterexample;
- the control's `Exhausted` is Knot's cost model applied to a seed-accepted
  program, which is a resource limit under D4;
- the obligation holds only relative to sufficient work. As stated, it stays
  undischargeable until expansion selects an irrefutable first row without
  splitting.

That change would make matrix-work agree with the seed, but it changes a
frozen control, so it is **left for coordinator review** and not made here.
REVIEW-2 is historical and unedited.

## Finding 3 (major): the recursion contract contradicts the broadened descent rule

**Fixed in the record.**

- `CONTRACT.json` `structural_recursion` gains a `contract_note`. It says that
  its rule, under which a rebuilt `Value`/`Construct` that denotes a strict
  descendant qualifies, supersedes the two sentences of
  `tests/compiler-recursion/SPEC.md` that exclude reconstruction.
- `src/SPEC.md` says the same where it links that contract.
- REVIEW-4.md gains a round-8 addendum.

No code reads those contract keys. The recursion gate's assertions hold,
because rebuilt parents and rebuilt non-descendants remain Unsupported.
`tests/compiler-recursion/SPEC.md` belongs to another increment and is **not
amended**. Its amendment is flagged for the coordinator and for the
campaign/descent-2 integration, which replaces the descent rule.

## Gates

On `8fc088c`, which is the tree this report describes apart from this
report, the refreshed round-8 receipts and one review-log paragraph,
`BEND_NO_TELEMETRY=1 npm run -s gates` exited 0 with 27/27 gates passed
(`run-8tejss50`, 532.0 s; summary in `round8-final-gates.json.gz`). Receipts:
66 identical, 22 semantic and 9 volatile-only. `npm run -s gates:verify`
passed its 18 tests.

Every gate's counts equal round 7's final run except these:

| Gate | Counts |
|---|---|
| `census` | 35 files, 695 declarations (41 new: the frontier functions, laws, witnesses, helpers and fills), 41 classes |
| `bootstrap` | corpus 1,044 (adding the 37 round-8 fixtures), 8 stages, 2 reached, 54 mutants |
| `nest-round8` (new) | 37 fixtures, 150 seed calls, 21 accepted books, 74 check observations, 292 evaluator and 292 Wasm values, 128 rejection observations, 5 mutants / 10 kills; 3,000 generated programs (seed 1,161 Accepted / 1,839 Invalid; Knot 1,148 / 1,796 / 56 Unsupported), 0 false acceptances, 0 false Invalid, 375 generated evaluator values |

Unchanged:

- `nest`: 38/40 frozen outcomes, 2 unmet;
- `nest-review`: fuzz 3,000 programs, 0 false acceptances, 0 false Invalid;
- `nest-round3`, `nest-round4`, `nest-round6` and `nest-round7`;
- `recursion`: 19 fixtures, 3 mutants;
- `checker` and `fields`: their `reusable-type` fixtures are unchanged;
- `selfhost`, `io-host`, `io-abi-2`, `perch-context` and the store gates.

Two earlier full runs did not pass. Neither failed on an assertion of the
fix:

- `run-zf87a17a` on `1f450e5`: 26/27. `nest-round6` stopped in a mutant
  build on the documented host clang-discovery failure (`bend needs clang 14
  or newer ... (found no clang)`) while other heavy work shared the host.
- `run-578cq9eo` on `78f1758`: 26/27. `perch-context` reported the witness
  laws' context overflow for `token`, which `8fc088c` repairs.

On both runs every other gate passed, including `nest-round8`. The shared
receipts of the existing gates are left for the coordinator to refresh.

## Remaining for the coordinator

- Live Perch review. The offline preflight (`round8-preflight.txt`) gives exit
  0 for the new frontier mechanism (`kind`, `bound`, `advance`, `close`,
  `ahead`): contexts are complete and the composition is available. Wider
  selections exceed the composition byte limit (exit 3), as in round 7.
  The whole seven changed files (287 declarations) also give exit 3: 52
  contexts are truncated (36 by the helper limit, 11 by the caller or byte
  limit, 5 by the file limit), and the composition is unavailable (134,878
  of 48,000 bytes).
- A destructuring let under a `+` row (`case +y: O{p} = y`) reports
  `Unsupported parse destructuring-binding`, which the seed accepts. The
  `99053a7` checker reports the same, so it predates this increment. It is a
  non-accepting outcome (D4), left for a parser follow-up.
- Amend `tests/compiler-recursion/SPEC.md` (finding 3), with the descent-2
  integration.
- Decide whether expansion should short-circuit an irrefutable first row. That
  would discharge the total D21 law and change the frozen matrix-work control
  (finding 2).
- Refresh shared receipts after merge.
- Still open from round 7: the seven main-era `Invalid parse` probes in
  `sem-r7-probes/hd`, and both D21 laws.
