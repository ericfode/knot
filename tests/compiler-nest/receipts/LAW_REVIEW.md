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
all 21 matrix laws, with no added axiom, unsafe declaration or proof hole.
`src/PROOF.bend` additionally fills the comma-scrutinee parser law.

| Family | Quantification and evidence | Limit |
|---|---|---|
| `specialization_preserves_first_match` | Induction over arbitrary rows, constructor, fields and level; independent `selected` projects row identities directly | Stable identity selection, not full compiler refinement |
| `selection_congruence` | Both Boolean cases, arbitrary tails | Auxiliary |
| `irrefutable_specialization`, `irrefutable_default`, `first_row_selected` | Arbitrary relevant inputs; preservation at one step and at a zero-column leaf | No induction over a complete lowering |
| Default-signature completion and exclusion | Arbitrary constructor tails with membership evidence | Tag-list helpers |
| Alias erasure and identity | Arbitrary names and known terms, inhabited Flag scopes | Scope/quantity helpers |
| `anonymous_reference_is_free` | Every scope and source location | Source lookup only |
| `default_reference_stays_live`, `empty_reference_stays_live` | Every token, level, type, quantity and liveness | Residual markers preserve ordinary occurrence rules |
| `live_empty_is_dead`, `erased_empty_is_not_dead` | Arbitrary names, explicit live/erased empty bindings | Inhabited context witnesses |
| `let_alias_available` | Arbitrary names in an explicit latest-let scope | Variable-only alias helper |
| Work exhaustion, terminal budget, one-step leaf | Arbitrary matrix/scope at zero work; arbitrary terminal budget; explicit one-unit leaf | Counter boundary helpers, not an expansion-cost theorem |
| `irrefutable_lowering_witness` | One overlapping two-column Flag matrix | Ground complete-checker normalization |
| `exhaustive_matrix_witness` | All four cases of one two-column Flag matrix | Ground complete-checker normalization |
| `default_completion_witness` | Off explicit and On remaining | Ground helper normalization |

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
