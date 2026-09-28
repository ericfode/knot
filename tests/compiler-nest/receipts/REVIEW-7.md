# Nest review round 7

One blocking finding was confirmed, and it is **fixed**. A `+` row on an alias
of an affine let binder made the let reusable, a regression from main at
`eb15da8`. Knot now passes a `+` row's mark only to a lambda-case binder; a let
binder and its aliases keep the let's declared quantity. The same repair closes
a second defect of the same promotion: a `+` row on a let of a `Type`-kind
value reported a false `Invalid check reusable-type`.

| Commit | Change |
|---|---|
| `4fe5e6a` | D7 freeze before the repair: 35 seed-derived fixtures under `round7-fixtures/`, `round7-expectations.json` and `round7_seed.py` (134 seed calls; a replay without `--write` reports no differences) |
| `7281182` | The fix in `matrix.bend::alias_bound`, two laws in `matrix-LAWS.bend` with proofs in `matrix-PROOF.bend`, the `nest-round7` gate with three mutants, the let/alias generator `letalias.py`, runner registration, SPEC text and the census approval (summary in the commit message) |
| `b9f88e5` | Receipts (`round7.json`, `round7-letalias.json`, `round7-letalias-before.json`, `round7-all-gates.json.gz`), falsification, preflight, these dispositions, LAW_REVIEW round 7, the contract entry, the campaign state pointer and the Perch review log entry |
| `410205e` | Direct runs of the five earlier nest gates (counts unchanged) and the disposition of every probe class |
| Final commit | The final-tree gate run (`round7-final-gates.json.gz`) |

## Coordinator rulings on the round-6 open items

These are settled and are not reopened here.

1. **Ratified:** the main-era forms (w1, w5, w6, w7, z1, z3, z5, z6, and the
   argument, let and constructor-argument positions) close in this increment,
   as REVIEW-6.md argued. They report `Invalid parse detached-brace`.
2. **Ratified:** a tab before `{` (k3) stays `Unsupported lex whitespace`. It is
   non-accepting under D4.
3. **D21:** the two general lowering laws stay required open obligations,
   unchanged (`src/SPEC.md` trust inventory, `src/CONTRACT.json`
   `pattern_matrix.open_obligations` and `unmet`, campaign state `unmet_laws`).

## Finding

| Finding | Disposition and evidence |
|---|---|
| Unsound acceptance: a `+` row on an alias of an affine let binder makes the let reusable (`k = a; match k: case +y: both(y, y)` is `Checked` with core `let1 $2:0=$0:0 in call0($2:0;$2:0)`; the seed reports `k (consumed more than once)`) | **Fixed.** See below |

### The rule and its site

A binding's `param` flag marks a lambda-case binder: a parameter
(`scope.bend::parameters`) or a field opened on the frontier
(`patterns.bend::add`). A let binder (`scope.bend::extend`) has
`param = False`, and an alias copies the flag of the binding it aliases.

`alias_bound` is the quantity site. Both promotion paths reach it:

- the column promotion (`alias_column` -> `promote`, the column's own name at
  mark 2);
- the row binder (`default_rows` -> `bind_body(body, token, level, 2)` for a
  `+` row).

It now reads

```
+mark = S.choose(U32,param,u => row,u => 1)
+actual = P.quantity(q,1,mark)
```

so both the alias's quantity and `remarked` (every binding of the level) see a
mark of 1 for a let. `P.quantity(q,1,1)` is `q`, so a let keeps its declared
quantity: an affine let stays affine, a `+k` let stays reusable (m3) and a `-k`
let stays erased (t4, l8, x3). Parameters and fields, and their aliases, are
promoted as before (m6, m7, m8, m11, m12, z1, z4, z5).

`eb15da8` admitted the latest let as a variable-only column
(`variable_column`, `U32.is_eq(U32.add(level,1),next)`). The let then reached
a promotion rule written for parameters. Changing `promote` alone does not fix
it: the row binder path still passes mark 2 (see *Mutants*).

### Evidence

- **Frozen fixtures (D7).** At `384acc6` (the checker built with the pinned seed
  before the repair), Knot reported:
  - `Checked` on all 12 let-promotion fixtures: l7, m2, m4, m5, m9, m13, y1,
    y2, y3, z2, z3 and own1;
  - `Invalid check reusable-type` on t1, which the seed accepts.

  On HEAD, in both compiler lanes:
  - the 12 let-promotion fixtures report `Invalid check affine-reuse`, in
    check, evaluation and both compile profiles, with the artifact preserved;
  - p1 and p2 (an alias of an affine parameter without a `+` row, used twice)
    stay `Invalid check affine-reuse`;
  - t2 (a `+` row on a `Type`-kind parameter) stays `Invalid check
    reusable-type`;
  - t1 and the 19 controls are `Checked`. All 134 seed calls agree across the
    seed, the evaluator and Wasm in both lanes (268 evaluator values, 268 Wasm
    values, `round7.json`).

  Frozen outcome counts: 35 fixtures; 15 seed-rejected (12 let-promotion, 2
  parameter-alias, 1 parameter-kind) and 20 seed-accepted (1 let-kind, 19
  controls).
- **Generator.** `letalias.py` is the reviewer's `gen.py` verbatim; all 1,500
  programs (random seeds 0 to 1,499) are byte-identical to the reviewer's
  `lg/g` files.
  - Against the `384acc6` checker it reports 63 false acceptances, the
    reviewer's flagged set exactly, each with a `case +y` row
    (`round7-letalias-before.json`).
  - On HEAD it reports 0 false acceptances and 0 false Invalid; seed and Knot
    are both at 780 Accepted / 720 Invalid. Every call of `f` in the 459
    programs that both accept with an entry `f` agrees between the seed and
    the Knot evaluator: 1,836 values (`round7-letalias.json`).
  - Limit: the generator declares only `Data` types and matches only lets.
    The `Type`-kind cases (t1, t2) and parameter promotion are covered by the
    frozen fixtures and mutants, not by the generator.
- **Laws.** `let_alias_keeps_quantity` (every row mark and known term: a let
  and its alias stay affine) and `parameter_alias_promotes` (a `+` row raises
  a parameter and its alias to 2) are filled in `src/matrix-PROOF.bend`. All
  eight `src/*PROOF.bend` entries print `All terms check.` on HEAD, and the
  round-7 gate reruns `matrix-PROOF.bend`. No earlier law pinned a let's
  quantity; both existing alias laws state parameters, so the round adds laws
  rather than restating one (LAW_REVIEW.md, round 7).
- **Falsification** (`round7-falsification.txt`): reverting the gate and
  passing the row mark to lets falsify `let_alias_keeps_quantity`;
  withholding the mark from parameters falsifies `parameter_alias_promotes`.
- **Mutants.** `nest-round7` kills three type-correct mutants in both lanes (6
  semantic kills):
  - `promote-let-alias` (the quantity site; required): the finding restored.
    Killed on l7. Outside the harness it flips exactly the 12 let-promotion
    fixtures and t1, and the generator reports the reviewer's 63 programs.
  - `promote-every-variable-column` (the promote site; required): `promote`
    receives mark 2 for every variable column. It **cannot** re-enable let
    promotion: every let fixture and all 1,500 generated programs keep their
    outcome, because the quantity site withholds the mark from every let. It
    is a distinct unsoundness for parameters (an affine parameter aliased
    without a `+` row becomes reusable), so p1 and p2 were frozen for it;
    killed on p1. The variant that forces `promote` itself
    (`U32.is_eq(q,2)` -> `True{}`, also reaching constructor splits) behaves
    the same.
  - `never-promote` (the over-correction): eight parameter and field
    promotion controls report affine-reuse, and t2 is accepted. The
    generator cannot see it. Killed on z1.
- **Reviewer probes.** The `384acc6` and HEAD native checkers ran over all
  10,330 files under `sem-r7-probes/` and `refute-letalias-probes/`, beside the
  seed:
  - The only outcome changes are the let-promotion probes (12 in
    `refute-letalias-probes/`, the same 11 without own1 in
    `sem-r7-probes/lt/`), from Checked to Invalid affine-reuse, and the 63
    generated programs.
    One more generated program (l00354) stays `Invalid affine-reuse`; only its
    reported span moves, to the let's second use, which is also the seed's
    complaint.
  - Two slow `blow8` probes in `sweep/` changed from a 60-second harness
    timeout to `Checked`. Re-timed alone, both checkers report `Checked` on
    both files in 42 to 47 s, so under the eight-way sweep they straddle the
    timeout; the checker did not change.
  - The post-repair tally, keyed by seed exit and HEAD outcome, and each
    class's disposition:

    | Seed | HEAD | Files | Disposition |
    |---|---|---|---|
    | rejects | Invalid | 4,886 | agree |
    | rejects | Unsupported | 315 | non-accepting, allowed (D4) |
    | rejects | Exhausted | 4 | non-accepting, allowed (D4) |
    | rejects | timeout | 3 | harness timeout under load; a rerun of every probe with only HEAD's checker times out on 9 blow-up probes (`bl/L2W10`, `bl/L3W7`, and seven `sweep/*blow*`), all of which the seed accepts, so these 3 were seed runs that hit the 60-second limit |
    | accepts | Checked | 4,998 | agree |
    | accepts | Unsupported | 72 | allowed (D4) |
    | accepts | Exhausted | 41 | allowed resource limit (D4) |
    | accepts | timeout | 4 | the same blow-up probes: resource-bound, never a classification |
    | accepts | Invalid | 7 | the main-era `hd/` parse forms below |
    | rejects | Checked | 0 | no unsound acceptance |
- **No other expectation moved.** The `384acc6` and HEAD checkers ran over all
  1,007 tracked `.bend` files. Their first output lines differ on exactly 13
  files, all round-7 fixtures: the 12 let-promotion fixtures go from `Checked`
  to `Invalid check affine-reuse`, and t1 goes from `Invalid check
  reusable-type` to `Checked`. The `nest-review` fuzz is unchanged from round
  6 (3,000 programs, 193 evaluator values, 0 false acceptances, 0 false
  Invalid).
- **All gates.** On `7281182`, `BEND_NO_TELEMETRY=1 npm run -s gates` exited 0
  with 26/26 gates passed (`run-hw659n1p`, 633.5 s; receipts: 64 identical,
  22 semantic, 9 volatile-only), and `npm run -s gates:verify` passed its 18
  tests. Counts equal round 6's except:
  - census: 654 declarations (4 new: the two laws and their fills);
  - bootstrap: corpus 1,007, adding the 35 round-7 fixtures;
  - nest-round7 (new): 35 fixtures, 134 seed calls, 268 evaluator and 268
    Wasm values, 3 mutants / 6 kills, 1,500 generated programs (seed and
    Knot 780 Accepted / 720 Invalid, 0 false acceptances, 0 false Invalid,
    1,836 generated evaluator values).
- **Final tree.** On `410205e` (the tree this report describes, apart from
  this report and the final summary), `npm run -s gates` exited 0 with 26/26
  gates passed (`run-67kw2nyk`, 561.8 s; summary in
  `round7-final-gates.json.gz`). Every gate's counts equal the `7281182` run.
  Two earlier runs on the same tree exited 1 on a host failure, not on a gate
  assertion: `run-vzchnrui` in `nest-round3` and `run-97mlt842` in
  `nest-round4`. In both, a mutant build stopped when the seed's clang
  discovery printed `bend needs clang 14 or newer ... (found no clang)`, and
  the other 25 gates passed. `docs/compiler-campaign/GATES.md` records this
  host failure as undiagnosed. `clang --version` works here, and 192
  concurrent probes under fresh `TMPDIR`s all succeeded. The host was shared
  with another worktree's gate run and ran at a load average of 20 to 28.
  The runner keeps such failures and does not retry them; no assertion
  changed.

### Mutation sites, answered

The task asked whether a mutant at the `promote` site is killed. Once the gate
sits at the quantity site, no mutation of `promote` or its call can re-enable
let promotion; the mutation that changes behaviour at that site is a distinct
parameter unsoundness, and the gate kills it. The table in
`round7-falsification.txt` records each mutation's fixture and generator
outcomes.

## Other observations (outside this finding)

The probe sweep also shows seven seed-accepted programs in `sem-r7-probes/hd`
reported `Invalid parse` (a line break inside a body constructor's braces or
a call's arguments, and two `case` rows on one line): b1, b2, b3, b4, b5, h15
and h25. Main `c0bd08d` reports the same `Invalid parse` diagnostics on all
seven, so they predate the nest increment and are unchanged by it.
Disposition: **unresolved, main-era**, outside this round's blocking finding.
Under D4 they should become `Unsupported` or be accepted; that belongs to a
parser follow-up for the coordinator to schedule.

## Remaining for the coordinator

- Live Perch review of the changed declarations. Offline preflight exits 3
  (attention): 0 truncated contexts for the changed declarations, but the
  composition is unavailable (`composition_byte_limit`, and
  `collaborator-not-in-group: 2` with the laws in the selection;
  `round7-preflight.txt`).
- Refresh shared receipts after merge.
- Schedule the seven main-era `Invalid parse` probes above.
- The two D21 laws stay open obligations.
