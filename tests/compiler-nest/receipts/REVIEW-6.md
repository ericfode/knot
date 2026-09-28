# Nest review round 6

One blocking finding was confirmed, and it is **fixed**. Knot accepted a
space, comment or line break between a constructor name and its `{`, which the
seed rejects. Knot now reports `Invalid parse detached-brace` at the brace in
every position the reviewer reached and in every position main already
accepted. Coordinator decision D21 is recorded: both general lowering laws stay
required, as open proof obligations in the trust inventory.

| Commit | Change |
|---|---|
| `3898b86` | D7 freeze before the repair: 35 seed-derived fixtures under `round6-fixtures/`, `round6-expectations.json` and `round6_seed.py` (59 seed calls; a replay without `--write` reports no differences) |
| `43d6553` | The fix: `S.touches` in `syntax.bend`, the touching-brace rule in `parse.bend::run`, four laws in `LAWS.bend` with proofs in `PROOF.bend`, the `nest-round6` gate with five mutants, detached-brace fuzz atoms, and the census approval (summary in the commit message) |
| `7671dd1` | D21: `src/SPEC.md` *Trust inventory: open proof obligations*, `CONTRACT.json` `pattern_matrix.open_obligations`, and LAW_REVIEW.md round 6 |
| `7af274f` | D21 consistency: `CONTRACT.json` `unmet` and the campaign state list both laws as open; `irrefutable_first_row_selected` is recorded as a partial law |
| This commit | Receipts, falsification, preflight, these dispositions and the Perch review log entry |

`3898b86`'s message counts 22 seed-rejected gap fixtures. The correct count is
23: 5 joined-line, 7 new-row and 11 main-era. `43d6553`'s message records the
correction.

## Finding

| Finding | Disposition and evidence |
|---|---|
| Unsound acceptance: whitespace, a newline or a comment between a constructor name and its `{` in pattern position. The header join made this a regression, and nested and multi-scrutinee rows newly reached it | **Fixed.** See below |

### The rule

Token spans are half-open, so a brace touches its name exactly when the name's
end offset equals the brace's start offset (`S.touches`). `parse.bend::run`
opens a constructor's fields only at a touching brace. A detached brace reports
`Invalid parse detached-brace` at the brace, in pattern and body mode alike.
The match/case header join drops line-break tokens but keeps every offset, so a
brace on the next line never touches its name, and the join cannot bridge the
gap. The seed accepts these forms, and Knot still accepts them:

- a spaced call `f (x)`;
- a spaced promotion `+ v`;
- a spaced type declaration `Off {}`;
- spaces or line breaks inside the braces.

A tab before the brace stays `Unsupported lex whitespace`, as before.

### Evidence

- **Frozen fixtures (D7).** Before the fix, at `c500d7d`, Knot reported
  `Checked` on all 23 seed-rejected gap fixtures. On HEAD every one reports
  `Invalid parse detached-brace` at the brace in both compiler lanes:
  - joined-line (5): w2, k1, k2, gap-nested-newline, gap-multi-comment-nested;
  - new-row (7): w3, w4, y8, z2, z4, z7, z8;
  - main-era (11): w1, w5, w6, w7, z1, z3, z5, z6, gap-argument, gap-let,
    gap-constructor-argument.

  The tab fixture k3 stays `Unsupported lex whitespace`. The 11 seed-accepted
  controls are `Checked`, and all 59 seed calls agree across seed, evaluator
  and Wasm in both lanes (`round6.json`).
- **Laws.** `touches_witness`, `touching_brace`, `detached_brace` and
  `joined_brace_witness` are filled in `src/PROOF.bend`. All eight
  `src/*PROOF.bend` entries print `All terms check.` on HEAD, and the round-6
  gate reruns `PROOF.bend` and `matrix-PROOF.bend`.
  `round6-falsification.txt` applies six single mutations of the rule, and each
  fails at a named law:
  - ignoring the touch;
  - comparing lines;
  - shifting the offset by one;
  - confining the rule to patterns;
  - reporting a touching brace Invalid;
  - negating the predicate.
- **Mutants.** `nest-round6` kills five type-correct mutants in both lanes (10
  semantic kills): ignore-detached-brace (the finding), touch-by-line,
  touch-past-one, touch-patterns-only and touch-call-parenthesis.
- **Fuzz.** The fixed-seed fuzz draws a space, comment or line break before
  `{` as rare row atoms, `P`/`B` openers and bodies; 497 of the 3,000 programs
  carry one. The generator bites: against the `c500d7d` checker it reports 36
  false acceptances (`seed rejects, Knot accepts`). On HEAD it reports 0 false
  acceptances and 0 false Invalid, with seed and Knot both at 193 Accepted /
  2,807 Invalid and 193 evaluator values (`review.json`).
  - **Coverage cost.** Round 5 had 242 Accepted. The drop comes from the gap
    atoms: all 497 gapped programs are seed-rejected, and the accepted rate among
    the 2,503 gap-free programs (7.7%) is close to round 5's (8.1%). The gap
    draws also reshuffle the fixed random stream, so the two program sets
    differ. No assertion fixes the accepted count.
- **Reviewer probes.** HEAD's native binaries ran the reviewer's differential
  harness over the 73 probes (`sem-r6-probes/ws` and `syn`). The copies were
  renamed from `x.0.bend` to `x-0.bend`, because the seed rejects a dotted file
  name in an import path. Results:
  - 0 unsound acceptances and 0 seed-accepted programs reported Invalid.
  - 41 probes report `Invalid parse detached-brace`. The other 12
    seed-rejected probes get other non-accepting classifications: pattern
    arity, constructor scrutinee, expected term, lex whitespace and term form.
  - 8 seed-accepted probes stay the allowed `Unsupported parse term-form`
    (annotations and a parenthesized pattern).
  - The 12 accepted probes (v1, v2, v3, y1, y5 and y6, two instances each)
    agree on all 96 calls across seed, evaluator, enum Wasm and fields Wasm.
- **No other expectation moved.** The `c500d7d` and HEAD checkers ran over all
  972 tracked `.bend` files. Their first output lines differ on exactly the 23
  seed-rejected round-6 gap fixtures, each going from `Checked` to
  `Invalid parse detached-brace`.

### Main-era forms: closed here, for the coordinator to ratify

The coordinator left open whether to close the main-era flat, body and
outer-pattern forms (w1/w5/w6/w7) here or split them out. They are closed here,
together with z1/z3/z5/z6 and the argument, let and constructor-argument
positions.

- **Reason.** The finding and these forms are one missing rule. Keeping the
  main-era positions open would need position-specific exceptions to one
  offset predicate. In a flat pattern it would also have to accept a space
  (w1, main-era) while rejecting a joined line break (w2, the regression),
  although after the header join both are the same token sequence and differ
  only in offsets.
- **Evidence that nothing else moved.** No tracked assertion depended on the
  defect: only the 23 frozen round-6 gap fixtures change outcome (see the scan
  above), and every registered gate passes with unchanged assertions.
- **To reverse.** If the coordinator prefers a split, a follow-up would restore
  acceptance only at those positions. That restores a known unsound
  acceptance, so this round does not recommend it.

## Coordinator decision D21

Both general lowering laws stay required. They are never weakened or dropped.
Each is recorded as an open proof obligation with its witnesses:

- `src/SPEC.md`, *Trust inventory: open proof obligations*;
- `src/CONTRACT.json`, `pattern_matrix.open_obligations` and `unmet`;
- the campaign state (`unmet_laws`);
- `tests/compiler-nest/receipts/LAW_REVIEW.md` round 6, which states each law
  as "unproved general law; witnessed by …".

The task names `tests/compiler-nest/LAW_REVIEW.md`. The nest law review has
always lived at `tests/compiler-nest/receipts/LAW_REVIEW.md`, so the entries are
there. The irrefutable-first-row entry says "in its total form". Round 5 proved
its partial-correctness part (`irrefutable_first_row_selected`), and that proof
is kept and labelled partial, not restated as the total law.

## Style preflight

`round6-preflight.txt` (offline, 0 provider requests, `--task=tests/compiler-nest/SPEC.md`) exits 3 (attention) in both runs:

- The seven changed or new declarations have no truncated contexts. Their
  composition is unavailable because of `collaborator-not-in-group: 4`: the
  selection names declarations from three files, not one manifest group.
- The four changed files (102 declarations) have an available composition
  (40,355 of 48,000 bytes). They have 5 truncated contexts, all on
  pre-existing shared declarations: `syntax.bend::Token`,
  `parse.bend::{Parsed, Mode, invalid, unsupported}`.

Live Perch review is the coordinator's.

## Gates

On `7af274f`, `npm run -s gates` exited 0 with 25 of 25 gates passed
(`run-4im_fokx`, 469.3 s; the summary is `round6-all-gates.json.gz`), and
`npm run -s gates:verify` passed its 18 tests. Every gate's counts equal
round 5's except these four:

| Gate | Round 6 | Round 5 |
|---|---|---|
| `census` | 35 files, 650 declarations, 41 classes (nine new: `touches` and four laws with their fills) | 35 files, 641 declarations, 41 classes |
| `bootstrap` | corpus 972 (adds the 35 round-6 fixtures) | corpus 937 |
| `nest-review` | fuzz 3,000 programs, 0 false acceptances, 0 false Invalid, 193 evaluator values | 242 evaluator values (see *Fuzz* above) |
| `nest-round6` (new) | 35 seed fixtures (control 11, joined-line 5, main-era 11, new-row 7, tab 1), 59 seed calls, 11 accepted books, 70 check observations, 118 evaluator and 118 Wasm values, 192 rejected phase observations, 5 mutants / 10 semantic kills | — |

All eight `src/*PROOF.bend` entries print `All terms check.` on HEAD, and
`census --check` reports current.

Only the nest-owned receipts (`nest.json`, `review.json`, `round3.json`,
`round4.json` and `round6.json`) are refreshed, by direct gate runs. All five
pass, and the first four change only input hashes, build hashes, dates and the
fuzz summary. Semantic drift in shared receipts is left to the coordinator.
