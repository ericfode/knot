# Nest review round 4

Both confirmed findings are fixed. Finding 2's seed-derived fixtures were
frozen in their own commit before the repair (D7). Finding 1 changes no
behavior, so it has no fixture; the old and new checker lanes produce
byte-identical check output and fields-profile Wasm on all 130 nest, review
and round-3 fixtures. Original nest conformance is unchanged at **38/40**. The
two explicitly unmet recursion cases and both general lowering theorems
remain open. This round does not establish self-hosting or a live
Perch/style pass.

| Commit | Change |
|---|---|
| `715599c` | Finding 1: retire `has_default`, `signature` and their three laws; `declared` replaces `defaults(ctors,seen)`; live remainder laws; proof-scope text corrected; census approved |
| `c3ff761` | Finding 2 freeze: 14 fixtures (8 accepted, 6 seed-rejected controls) and 32 seed calls |
| `3a35051` | Finding 2 repair: `E.rebuilt`; new laws; `nest-round4` gate registered; specs, contract, census |
| This commit | Receipts, preflight record, review-log entry, campaign state and these dispositions |

The original fixtures and expectations, the round-2 and round-3 fixtures and
expectations, and every existing gate assertion and mutant anchor are
unchanged. `round4_seed.py` replays all 14 fixtures and 32 seed calls with no
differences.

## Findings

| Finding | Disposition and evidence |
|---|---|
| Dead matrix helpers; laws over dead code cited as exhaustiveness evidence | **Fixed.** `has_default` and `signature` are deleted. `defaults(ctors,seen)`, whose only caller passed `Nil{}`, becomes `declared(ctors)`. `default_completes_missing_branch`, `default_does_not_repeat_explicit_branch` and `default_completion_witness` are deleted, not restated over `defaults`. Four quantified laws take their place and constrain the live split: `remainder_omits_split` and `remainder_keeps_other` for `remaining`, `remainder_drops_split_rows` and `irrefutable_remainder` for `without`. The reviewer's suggestion that "`without` keeps exactly the rows `specialize` drops" is not true of the live split, because variable rows go to both sides. The laws therefore state what does hold: `without` drops only rows headed by the split constructor. The matrix-LAWS comment, `tests/compiler-nest/SPEC.md` and `LAW_REVIEW.md` now say that these are one-step helpers, and that the general exhaustive-lowering law is unmet. The matrix laws are recounted: 24 before, 25 after finding 1, 31 after finding 2. Census approval is pasted in `715599c`. |
| Recursion on a default-row field binder Unsupported after an earlier row nests into that field | **Fixed, by the reviewer's second option.** The descent rule recognizes the reconstruction; see below. mData7 (verbatim), its `Type` variant and ls1 are frozen, and all three are accepted and executed. |

### Finding 2 in detail

The checker rebuilds a matched binder from its fields when it is referenced
again. This is an affine obligation: the scrutinee's own use is spent by the
case. In mData7 the third row's `l` reaches its body through the positive
branch of the split on `l`. It is therefore rebuilt as
`v1.1{$3:1;v0.1}`, and `E.descends` accepted only a `Reference`.

Binding the alias to a reference (the reviewer's first option) would either
spend the scrutinee twice or change the emitted runtime term. It would also
leave the flat path unfixed: `match l: case Node{a, b}: len(l)` is
Unsupported for the same reason, and the seed accepts it (see
`rebuilt-refined-variable`).

`E.rebuilt(items,bindings,smaller)` instead checks whether a `Value` or
`Construct` first argument denotes a strict descendant of parameter 0:
- `layer` and `unfold` expose one layer of a level's refinement.
- `denotes` compares position-wise. A reference must be its own level. A
  value or constructor must have the same type and tag, and its fields are
  compared against the unfolded field references.
- The value passed is then that descendant's value, and the reference rule's
  argument applies unchanged.
- A reference head returns `False` (`reference_is_not_rebuilt`). This leaves
  `E.descends`, all 16 recursion laws, and the self-call mutants of the
  `recursion` and `selfhost` gates unchanged. The `call_result` condition
  keeps their anchored text inside a conjunction.
- The emitted argument, its uses, the evaluator and both emitters are
  unchanged.

The seed decides these calls by structural comparison with the refined
parameter. Probes fixed which conditions the recognizer needs:
- the constant's type: `Leaf{}` against a `Flag` refined to the same tag is
  rejected (`rebuilt-retyped-constant`);
- field order (`rebuilt-swapped-fields`);
- every field (`rebuilt-partial`);
- strict descent: the root rebuilt in a refined branch or in source is
  rejected (`rebuilt-root`, `rebuilt-root-source`);
- an unrefined constant is rejected (`rebuilt-unrefined-constant`).

Rebuilds the seed accepts, beyond the three finding repros:
- a flat-path refined variable;
- a source-written reconstruction;
- a source constant equal to a refined field;
- a nested rebuilt subterm;
- a tree with two rebuilt recursive fields.

All are frozen and pass in both lanes, the evaluator and fields Wasm.

The finding asked for "a mutant that re-enables the reconstruction". Under
this repair the reconstruction is never removed, so the equivalent mutant is
`ignore-rebuilt-descent`, which disables the recognizer. It restores the
reported `Unsupported check recursive-call` on mData7 and is killed. Three
further mutants each drop one condition of the recognizer:
- `any-rebuilt-level` (strict descent) is killed by `rebuilt-root`;
- `untyped-rebuilt-constant` (type) is killed by `rebuilt-retyped-constant`;
- `ignore-rebuilt-fields` (fields) is killed by `rebuilt-swapped-fields`.

Before the repair was committed, prototype and base checker lanes were run
on all 909 tracked `.bend` files. No first output line changed, so no
existing outcome flips. All 59 mutant anchors across the gates remain unique.

**Integration hazard.** `campaign/descent-2`, based on `57a0c01`, replaces the
descent rule with the complete seed comparison and removes `smaller`. Merging
it conflicts with this repair in `scope.bend` and `check.bend`. That branch
should keep the round-4 fixtures as regressions. Its complete rule may report
the six seed-rejected controls as Invalid rather than Unsupported, which
would need a reviewed amendment of `round4_seed.py`'s table. That table
records Unsupported because this branch lacks the complete rule.

## New checked laws

In `src/matrix-LAWS.bend`:
- quantified: `remainder_omits_split`, `remainder_keeps_other`,
  `remainder_drops_split_rows`, `irrefutable_remainder` and
  `reference_is_not_rebuilt`;
- ground witnesses over one explicit scope (len's third row after a nested
  second row): `rebuilt_descendant_witness`, `rebuilt_root_witness`,
  `changed_field_witness` and `retyped_constant_witness`;
- `rebuilt_descendant_call_witness`: `K.call_result` admits the rebuilt `l`
  for every token and use set.

Every `src/*-PROOF.bend` entry and `src/PROOF.bend` print `All terms check.`
Falsifying each new law makes the matrix entry fail at that law.

One obligation rests only on the 14 fixtures and is not proved: that
`E.rebuilt` admits only arguments the seed orders strictly below parameter 0.
The general exhaustive-lowering and irrefutable-first-row theorems remain
unmet.

## Gate `nest-round4`

`round4.py` does the following:
- replays the seed;
- checks `matrix-PROOF` and `recursion-PROOF`;
- builds both compiler lanes;
- runs all 14 fixtures. The 8 accepted books go through check, fields
  compilation, and evaluator and Wasm execution on every seed call (64
  evaluator and 64 Wasm values), with native and Bun module equality. The 6
  controls give `Unsupported check recursive-call` in check, eval and both
  compile profiles, with existing artifacts preserved (48 phase
  observations).

Four type-correct mutants are killed in both lanes, for 8 kills.

## Style preflight

`round4-preflight.txt` records three offline runs. None makes a provider
request.

- **The 19 changed declarations.** No truncated context and no impossible
  supporting role. Composition is unavailable: the group is 72,579 of 48,000
  bytes, with 78 collaborators outside the group.
- **The five changed files.** 25 contexts are truncated by helper, file and
  byte limits (as in round 3). Composition is over the byte limit.
- **The recognizer family plus `call_result`.** No truncated context.
  Composition is unavailable only because of collaborators outside the
  group (43,635 of 48,000 bytes).

Every run exits 3 (attention). No style rating or pass is claimed; live
review belongs to the coordinator.

## Gates

Fresh run: `BEND_NO_TELEMETRY=1 npm run -s gates` on `3a35051`, the commit
with every code, law, fixture, spec and gate change of this round. The
untracked round-4 receipt and preflight record were also present. The run is
scratch run `run-bzcnho8y`, started `2026-09-28T09:56:38Z`, and took 577.3
seconds with 4 jobs. It exited 0, with **24/24 gates passed**.

The counts below come from that run's summary, archived as
`round4-all-gates.json.gz`. They count different kinds of observation and
must not be summed. `npm run -s gates:verify` passes 18 tests.

| Gate | Result and exact coverage |
|---|---|
| `frontend` | PASS: 14 fixtures, 28 lane observations, 24 boundaries, 4 mutants |
| `checker` | PASS: 49 fixtures, 98 lane observations, 10 budgets, 2 bounds / 16 observations, 7 mutants |
| `structural` | PASS: 16 fixtures, 64 lane observations, 4 bounds, 7 mutants |
| `fields` | PASS: 40 fixtures, 240 lane observations, 36 budgets, 6 host boundaries, 2 bounds / 12 observations, 9 mutants |
| `wasm` | PASS: 25 fixtures, 90 reference calls in 2 execution lanes, 62 rejects, 44 boundaries, 7 mutants |
| `wasm-trust` | PASS: 3 entries, 0 proof holes |
| `fields-trust` | PASS: 4 entries, 0 proof holes |
| `structural-trust` | PASS: 2 entries, 0 proof holes |
| `owned-store` | PASS: 3,532 cases in 2 lanes, 15 literal witnesses, 6 mutants |
| `flat-store` | PASS in each of 2 lanes: 13,621 observations, 3,534 instances, 2 installed-boundary states, 7 lifecycle checks; 9 mutants |
| `recursion` | PASS: 19 fixtures, 3 mutants |
| `fields-wasm` | PASS: 8 fixtures, 30 boundaries, 4 mutants |
| `census` | PASS: 33 files, 599 declarations, 41 classes |
| `perch-context` | PASS: 33 fixtures, 8 mutants |
| `lint:verify` | PASS: 168 tests, 8 law rules |
| `bootstrap` | PASS: 935 corpus files, 8 stages, 2 reached, 54 mutants |
| `classification` | PASS: 17 fixtures, 6 mutants |
| `nest` | PASS within stated scope. 40 seed fixtures and 174 seed calls. 38/40 frozen outcomes, 2 unmet. 76 check observations, 25 accepted books, 386 evaluator and 386 Wasm values, 78 rejection observations, 24 boundaries, 100 enum hashes. 6 mutants / 12 kills |
| `nest-review` | PASS. 29 seed fixtures and 49 seed calls. 58 check observations, 15 accepted books, 98 evaluator and 98 Wasm values, 112 rejection observations. 7 mutants / 14 kills. Fuzz: 3,000 programs, 0 false acceptances, 0 false Invalid, 242 evaluator values |
| `io-host` | PASS: 40 seed fixtures, 109 seed runs, 86 conformance runs, 6 CLI runs, 22 host boundaries, 6 mutants |
| `io-abi-2` | PASS: 43 fixtures, 21 read, 64 reference and 61 seed observations, 153 parity checks, 5/5 mutants killed |
| `selfhost` | PASS: 65 cases, 2 passed, 63 blocked, 5 reviewed D4 gaps, 3 mutants, 20 judge mutants |
| `nest-round3` | PASS. 61 seed fixtures and 82 seed calls. 122 check observations, 32 accepted books, 164 evaluator and 164 Wasm values, 232 rejection observations. 11 mutants / 22 kills |
| `nest-round4` | PASS. 14 seed fixtures and 32 seed calls. 28 check observations, 8 accepted books, 64 evaluator and 64 Wasm values, 48 rejection observations. 4 mutants / 8 kills |

The recursion, selfhost, recursion-law and self-call-mutant results are
unchanged by the repair.

Receipt drift against the tracked tree: 64 identical, 9 volatile-only and 19
semantic. Compared with the round-3 final run (18 semantic), the only new
semantic receipt is `round4.json`, which is new. The other nest receipts
differ only in input hashes. The remaining semantic drift is the same shared
build-hash and earlier-round outcome drift as in round 3. Examples are the
checker's duplicate-arm fixture and the frontend's multi-scrutinee match, now
accepted, and a selfhost parse location moved by the round-3 header join.
Those shared receipts belong to the coordinator and are not modified here.
The nest-owned receipts `nest.json`, `review.json`, `round3.json` and
`round4.json` are refreshed from direct runs of their gates on this tree.

## Addendum (review round 8): the recursion contract this round supersedes

The repair above (`3a35051`) broadened the descent rule, but this report did not
say that it contradicts two sentences of
[`tests/compiler-recursion/SPEC.md`](../../compiler-recursion/SPEC.md). That
contract says that "reconstructed constructors" do not satisfy the rule, and
that "even reconstruction of a strict descendant does not qualify once its
checked term is no longer a Reference". Since `3a35051` a rebuilt
`Value`/`Construct` that denotes a strict descendant qualifies. Rebuilt parents
and rebuilt non-descendants still report `Unsupported check recursive-call`,
so the recursion gate's assertions hold. `src/CONTRACT.json`
`structural_recursion.rule` is authoritative, and its new `contract_note` and
`src/SPEC.md` now record the supersession. The recursion SPEC belongs to
another increment and is not amended here. Its amendment is left to the
coordinator and to the campaign/descent-2 integration
([REVIEW-8.md](REVIEW-8.md)).
