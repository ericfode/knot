# Pattern-matrix law review, round 2

Contract: `tests/compiler-nest/SPEC.md`. Frozen expectations are
`expectations.json`, `control-expectations.json` and the separately committed
`review-expectations.json`. Live Perch review belongs to the coordinator.
This packet records no model rating or automatic style qualification.

## Mechanism and checked boundary

A constructor splits an ordered matrix into a positive specialization and a
negative remainder. `specialize` retains matching constructor rows and variable
rows in order. `without` removes only the selected constructor rows. The negative
scope retains a live reference and the remaining constructor set, including an
empty set. A variable default therefore reaches a checked leaf even after all
constructors have been removed. A body shadowed at the same leaf is still dead.

`Expansion{node, remaining}` threads one total counter through both children.
Each residual matrix, including leaves, spends one unit. A new source match
starts at 4,096; no branch divides that quota. Expansion scopes preserve field
levels and quantities. The checker independently checks both branches before
coalescing the binary spine into the existing exhaustive `Case` representation.
A terminal default is checked while unrefined, then shared across its remaining
runtime tags with their field layouts. The evaluator and emitter have no matrix
semantics. The 25 frozen enum modules retain their exact bytes.

A self-reference in `Binding.known` marks an unrefined residual binding; an empty
self-case additionally marks its emptied type. Both retain ordinary lexical
usage. A live emptied type can justify a later empty match, matching the seed's
`ctx_dead`; it cannot excuse a free name, type mismatch, affine reuse or erased
live use in a selected body. An erased emptied binding is no such evidence.
A later source match on a residual binding reports
`Unsupported check default-scrutinee` until arbitrary residual constructor sets are carried through
source-level nested matches.

`_` remains an anonymous internal field identity for reconstruction but cannot
be resolved by source name lookup. `_x` remains an ordinary source binder.
All-variable columns may alias the latest let binder without inspecting it.
Commas and spaces separate scrutinees and row patterns.

## Proof inventory

The complete `src/matrix-PROOF.bend` imports the earlier proof chain and fills
every matrix law (21 in round 2, 24 in round 3, 31 after round 4), with no added axiom, unsafe
declaration or proof hole.
`src/PROOF.bend` additionally fills the comma-scrutinee parser law.

| Family | Quantification and evidence | Limit |
|---|---|---|
| `specialization_preserves_first_match` | Induction over arbitrary rows, constructor, fields and level; independent `selected` projects row identities directly | Stable identity selection, not full compiler refinement |
| `selection_congruence` | Both Boolean cases, arbitrary tails | Auxiliary |
| `irrefutable_specialization`, `irrefutable_default`, `first_row_selected` | Arbitrary relevant inputs; preservation at one step and at a zero-column leaf | No induction over a complete lowering |
| `remainder_omits_split`, `remainder_keeps_other` | Arbitrary tag lists, given the split-constructor comparison; replaced the dead default-signature laws in round 4 | One step of the live remainder; coverage follows by induction but is not stated |
| `remainder_drops_split_rows`, `irrefutable_remainder` | Arbitrary rows, given the comparison; any variable-headed row | One step of the negative matrix |
| Alias erasure and identity | Arbitrary names and known terms, inhabited Flag scopes | Scope/quantity helpers |
| `anonymous_reference_is_free` | Every scope and source location | Source lookup only |
| `default_reference_stays_live`, `empty_reference_stays_live` | Every token, level, type, quantity and liveness | Residual markers preserve ordinary occurrence rules |
| `live_empty_is_dead`, `erased_empty_is_not_dead` | Arbitrary names, explicit live/erased empty bindings | Inhabited context witnesses |
| `let_alias_available` | Arbitrary names in an explicit latest-let scope | Variable-only alias helper |
| Work exhaustion, terminal budget, one-step leaf | Arbitrary matrix/scope at zero work; arbitrary terminal budget; explicit one-unit leaf | Counter boundary helpers, not an expansion-cost theorem |
| `irrefutable_lowering_witness` | One overlapping two-column Flag matrix | Ground complete-checker normalization |
| `exhaustive_matrix_witness` | All four cases of one two-column Flag matrix | Ground complete-checker normalization |

Two requested **general laws remain unmet**: arbitrary irrefutable-first-row
lowering and arbitrary exhaustive-matrix/no-missing-branch lowering. Both are
listed in `src/CONTRACT.json` and `docs/compiler-campaign/state.json`. Renaming
the two witnesses leaves their checked equations unchanged. Neither witnesses
nor fuzzing establish those general theorems.

## Independent observations and mutants

The original 40 fixtures and 174 seed calls are unchanged. The original nest
gate retains 38 matched outcomes and two separately recorded recursion outcomes
that remain Unsupported rather than their frozen Invalid expectation. It runs
386 evaluator values, 386 Wasm values, 24 resource observations and 100 enum
hash checks. The six original semantic mutants remain; omitting the default now
removes the binary negative matrix instead of modifying the retired n-ary path.
Their intended wrong observation and rejecting assertion are unchanged.

The new gate replays 29 copied reviewer repros and 49 seed calls fixed in
`ebdad25` before repairs. Check/eval/compile observations run in native and Bun;
rejected inputs are checked through both Wasm profiles with preserved output
artifacts. Every enum-profile nest module passes the original eight-instruction
whitelist. The empty-match encoding is `i32.const 0`, not a contract extension.

Seven additional compiler mutants typecheck before execution: constant-refined
defaults, unchecked empty default bodies, referenceable anonymous binders,
partitioned work, rejected comma scrutinees, rejected let aliases, and forbidden
empty-case `unreachable`. The last emits a valid module whose `main` executes;
its forbidden instruction is what kills it. Type errors and host failures never
count as semantic kills.

The fuzzer commits its generator, seed 1313166164 and count 3,000. The seed is the
independent classifier; every accepted program also runs in Knot's evaluator.
The gate rejects false acceptance, false Invalid, timeout, and host/internal
failure separately. This is bounded testing, not a proof of soundness.

The old matrix-work fixture has 13 independent strict columns despite its first
wildcard row. Its literal binary expansion recurrence is `T(0)=1` and
`T(n+1)=2+2*T(n)`, so it needs 24,574 visits. Its unchanged Exhausted expectation
now follows total work. New linear-size self-shape, deep and wide fixtures must
succeed. The independent 65,536-byte arena and tree controls remain unchanged.

## Scope and review failure record

Round 1 wrongly refined defaults, dropped empty default leaves, exposed `_`,
rejected comma/let aliases, emitted an out-of-contract instruction, divided work
per path, and gave two ground witnesses general-law names. The new fixtures and
mutants directly cover those gaps; `REVIEW-2.md` records each disposition.

The next recursion increment owns `rec-swapped-args` and `rec-alias`. Arbitrary
source-level rematching of residual bindings, the two general laws, structured
host arguments, generics/closures, owned-memory reclamation and full self-hosting
remain unqualified. Existing Base/native trust gates retain their separate scope.
Current source hashes and execution evidence are in `nest.json`, `review.json`
and `review-verification.json`; old first-round receipts retain their historical
meaning. Offline preflight is not a live style assessment.

## Round 3

Round 3 adds binder grammar, the ordered dead-code rule and header layout; see
`REVIEW-3.md`. Every new law has a filled proof; `src/PROOF.bend` and
`src/matrix-PROOF.bend` print `All terms check.`, and falsifying each new law
makes its entry fail at that law.

| Law | Quantification and evidence | Limit |
|---|---|---|
| `pending_binder_witnesses_nothing` | Every binding, tail, catalog and pending suffix, given membership of the binding's level; proved by congruence | A binder still pending never witnesses dead code; says nothing of binders in context |
| `dotted_pattern_binder`, `dotted_let_binder` | Every source location and token suffix, for the fixed name `a.b` | One dotted spelling per position |
| `malformed_word_source` | Every fuel budget of at least two, for the fixed source `a.` | One malformed spelling at end of input |
| `header_joins_lines` | Every location and every token suffix after the colon | Line breaks before the colon of one fixed header |
| `erased_empty_is_not_dead`, `live_empty_is_dead` | Arbitrary names; the round-2 residual witnesses restated at a scrutinee level | Inhabited context witnesses |
| `name_words_witness` | Ground: `a.b_1.c` counts 3 words; `x.`, `a..b`, `a.1` count 0 | Ground normalization |
| `line_broken_scrutinees_witness` | Ground: `match` / `a` / `b:` across lines parses as two scrutinees | Ground parser normalization |
| `introduced_empty_witness`, `pending_empty_witness` | Ground: `f(x: V, y: Flag)` matching `y` is dead; `f(y: Flag, x: V)` is not | Ground scope normalization |

Two obligations are **not proved** and rest only on the frozen seed fixtures
and the fuzzer: that `E.dead` decides the seed's `ctx_dead` at every missing
arm (the match frontier as the seed's introduced context), and that
`S.malformed` and `S.binder` decide the seed's lexeme regex and `parse_patt`
binder rule. The round-3 fixtures fix both from the pinned seed, and the
3,000-program corpus reproduces all three defect classes on the pre-fix
compiler and none after the repair. This is bounded evidence, not a proof.

## Round 4

Round 4 retires the dead default-signature helpers and adds recursion through
rebuilt strict descendants; see `REVIEW-4.md`. `src/matrix-PROOF.bend`,
`src/recursion-PROOF.bend` and every other proof entry print
`All terms check.` Falsifying each new law makes the matrix entry fail at
that law.

| Law | Quantification and evidence | Limit |
|---|---|---|
| `remainder_omits_split`, `remainder_keeps_other` | Every tag list and constructor, given the head comparison; replace `default_completes_missing_branch` and `default_does_not_repeat_explicit_branch`, which constrained a `defaults(ctors,seen)` whose `seen` was always empty | One step of `remaining` |
| `remainder_drops_split_rows`, `irrefutable_remainder` | Every row list, given the head comparison; every variable-headed row | One step of `without`; with `irrefutable_specialization` and `irrefutable_default`, an irrefutable head survives every form of column elimination |
| `reference_is_not_rebuilt` | Every reference head, tail, scope and descendant set | References keep the reference rule; this keeps the recursion laws and the self-call mutants of the recursion and selfhost gates unchanged |
| `rebuilt_descendant_witness`, `rebuilt_root_witness`, `changed_field_witness`, `retyped_constant_witness` | Ground: len's third row after a nested second row. A rebuilt `l` descends. A rebuilt root, a rebuilt `l` with a changed field and a `T` constant against a `Flag` refined to the same tag do not | Ground normalizations of `E.rebuilt` |
| `rebuilt_descendant_call_witness` | Every call token and use set, in the ground scope above | `K.call_result` admits the rebuilt `l`; the emitted argument is unchanged |

`default_completion_witness` is deleted with `signature`. One obligation is
**not proved** and rests only on the 14 round-4 fixtures: that `E.rebuilt`
admits only arguments the seed's decreasing-call rule orders strictly below
parameter 0. No new general lowering or termination theorem is claimed.

## Round 5

The round-5 review confirmed that two of the three requested matrix laws were
only ground witnesses. The irrefutable-first-row law is now general. It lives in
`src/lowering-LAWS.bend` and is filled in `src/lowering-PROOF.bend`, which the
`src/matrix-PROOF.bend` entry imports, so the nest gate's proof run checks it;
the move keeps the `pattern-matrix-laws` Perch composition under its 48 KB
bound, with a new `lowering-laws` manifest group.

| Law | Quantification and evidence | Limit |
|---|---|---|
| `irrefutable_first_row_selected` | Every fuel, catalog, scope, work budget, column list, arm and trailing rows. Hypotheses: `Irrefutable(columns, patterns)` (one variable or promotion per column; indexed by the columns, so a short row, which a split would drop, cannot satisfy it) and `Leaf(body)` (not a matrix, decision or alias, which expansion would re-enter). Conclusion: if `M.expand` returns `Done{Expansion{tree, left}}`, `Leaves(tree, body)`: every leaf of both decision branches is the body, under the installed aliases | Partial correctness: exhausted fuel or work, catalog and scope failures, Invalid and Unsupported are other outcomes and are not claimed absent. Aliases are transparent; quantities and checking are other laws |
| `irrefutable_first_row_witness` (`matrix-LAWS`) | Ground: `M.expand` of the overlapping `_ _` / `Off Off` Flag matrix is a two-level decision with `On` at all three leaves | Inhabits the general law's antecedent |

The proof is an induction on expansion fuel over the invariant `Lowers`: a
matrix leads with an irrefutable row whose body lowers to the selected body,
an alias lowers when its body does, and a decision lowers on both sides. Each
lowering state preserves it: a split's positive matrix prepends fresh fields,
which are variables; its negative matrix keeps the variable-headed row; a
default drops the head; promotion adds a transparent alias; `bind_body` extends
the alias chain. A zero-column step returns the leading row's body. The
invariant is Data-kinded so one proof serves both branches of a split.

`round5-falsification.txt` runs the lowering entry on mutated copies of `src`.
The control checks; each of eight mutants fails at a named proof term:
`specialize` dropping variable rows or moving them last, `without` dropping
them, `default_rows` dropping variable or promotion rows, a zero-column step
returning another node, fresh fields built as constructors, and a conclusion
naming another body. Every proof entry prints `All terms check.`

The exhaustive-lowering law remains **unmet**. Its obstacle is typing, not
proof mechanics. A split reads a column's available constructors from the
scope-bound type (`M.available` over `G.type_at` of `M.column_binding`), and
field columns receive their types from `P.branch` as expansion proceeds. An
independent statement of exhaustiveness quantifies over typed value vectors,
so the proof must relate that scope to the column types: lookups of generated
`$matrix` names after `P.branch` (injectivity of `U32.show` levels), `E.residual`
and `M.alias`, and inhabitants for unconstrained positions, which empty types
deny (the dead-code rule). A type-free witness would be trivial: a vector of
unknown constructors refutes every row that has any constructor. A catch-all
corollary of the law above is not the general theorem and is not claimed.

## Round 6

The round-6 review confirmed an unsound acceptance: a space, comment or line
break between a constructor name and its `{`. The seed rejects each gap in
patterns and bodies; Knot accepted them, and the round-3 header join newly
carried a line-broken gap into nested and multi-scrutinee rows.

One predicate absorbs every position. Token spans are half-open, so a brace
touches its name when the name's end offset is the brace's start offset
(`S.touches`). The header join drops line-break tokens but keeps offsets, so
it can no longer bridge the gap.

| Law | Quantification and evidence | Limit |
|---|---|---|
| `touches_witness` | Ground: `On{`, `On {` and `On` / `{` on the next line give touching, detached, detached | Pins offsets, not lines or columns |
| `touching_brace` | Both term modes (pattern and body), every position of the name `On`, its brace and its closing brace, and every unconsumed suffix, under the hypothesis that the brace touches: `On{}` parses as the constructor | A classification law for one parser step, not parser soundness |
| `detached_brace` | The same quantification under the hypothesis that the brace does not touch: `Invalid parse detached-brace` at the brace | As above; lexing (a tab stays `Unsupported lex whitespace`) precedes it |
| `joined_brace_witness` | Ground: `header` joins `case On` / `{}:` and the term step still reports the detached brace at its own offset | Witnesses the regression path, not every header |

Falsification (`round6-falsification.txt`). The seed stops at the first
failing term:

- Comparing lines, shifting the offset by one and negating the predicate
  falsify `touches_witness`.
- Reporting a touching brace Invalid falsifies `touching_brace`.
- Ignoring the touch and confining the rule to patterns stop first at
  `touching_brace`, but only its proof breaks there. That proof mirrors the
  parser step, and the law still holds under both mutations. With
  `touching_brace` removed, each fails at `detached_brace`, whose statement
  it falsifies: the parser yields `Exhausted` instead of
  `Invalid parse detached-brace`.

The `nest-round6` gate kills five type-correct mutants of the same rule on
the 35 frozen fixtures, in both lanes. Among them, `ignore-detached-brace`
and `touch-patterns-only` are the behavioural forms of the last two
mutations, killed on w2 and w5.

### Open proof obligations (coordinator decision D21)

The two general lowering laws stay required and are never weakened or
dropped. Merge proceeds with them recorded as open obligations in the trust
inventory (`src/SPEC.md`, *Trust inventory: open proof obligations*, and
`src/CONTRACT.json` `pattern_matrix.open_obligations`).

| Law | Entry |
|---|---|
| Irrefutable first row: a matrix whose first row is irrefutable lowers to that row's body | Unproved general law in its total form, which includes that the lowering succeeds; witnessed by `irrefutable_lowering_witness`, `irrefutable_first_row_witness`, the helper laws `first_row_selected`, `irrefutable_specialization` and `irrefutable_default`, the `first-match-*`, `wildcard-default`, `unreachable-after-wildcard` and `variable-*` fixtures, and the 3,000-program seed fuzz. Its partial-correctness part is proved in round 5 (`irrefutable_first_row_selected`: every successful lowering selects the body at every leaf); this entry does not restate that proof as the total law |
| Exhaustive matrix: an exhaustive matrix lowers to a tree with no missing branch | Unproved general law; witnessed by `exhaustive_matrix_witness`, the remainder helper laws (`remainder_omits_split`, `remainder_keeps_other`, `remainder_drops_split_rows`, `irrefutable_remainder`), the `multi-*`, `nested-*`, `rec-*-nested` and `empty-*` fixtures, and the 3,000-program seed fuzz. Round 5 records the typing obstacle to its proof |
