# Pattern-matrix law review

This is the offline review packet for the nest increment. The contract is
`tests/compiler-nest/SPEC.md`; the immutable independent oracle is
`tests/compiler-nest/expectations.json`. Live Perch review belongs to the
coordinator. This packet records no provider judgment or style qualification.

## Contract and abstraction

A source match is an ordered matrix of patterns and row bodies. Specializing a
constructor column retains matching constructor rows and irrefutable rows in
their original order. Irrefutable columns add aliases without inspecting the
scrutinee. At a leaf, the first remaining row supplies the body. Constructor
signatures plus default rows form flat source matches, which the existing
checker turns into core `Case` trees. The evaluator and emitters see no matrix.

The independent observation `identities(rows)` projects row tokens without
looking at fields, aliases, scopes or bodies. `selected(rows, ctor)` selects
these identities directly from the source patterns. The principal universal
law is:

```text
identities(M.specialize(rows, ctor, fields, level)) == selected(rows, ctor)
```

Its proof inducts over arbitrary row lists. A matching constructor row and an
irrefutable row retain their positions relative to every surviving later row.
The observation cannot establish that generated fields or bodies are correct;
those are separate laws and differential checks.

The internal entry points are:

```text
start(fuel, token, value, rows, types) -> Result<Error, Node>
step(token, columns, rows, work, types, scope) -> Result<Error, Node>
alias(scope, token, level, mark, types) -> Result<Error, Scope>
```

`start` validates source pattern names and arities before removing unreachable
bodies. `step` expands one column with a partitioned work budget. `alias` shares
the original lexical identity, quantity and descent relation. Checked aliases
are eliminated before core construction. A source match starts with 4096
steps; each branch receives a share of the remaining quota. Exhaustion is
inconclusive. Existing parser/checker depth, catalog, lexical-level, evaluator
and emitter bounds remain independent.

## Proof inventory and inhabited witnesses

All 13 matrix laws are filled in `src/matrix-PROOF.bend`, which imports the
complete earlier recursion/fields/catalog/runtime/checker/frontend proof chain.
The pinned seed prints `All terms check.` with exit 0. No new axiom, unsafe
declaration or proof hole is introduced. The earlier Base/native trust boundary
is retained; the existing three trust gates separately inventory their entry
closures. This is not a proof that the seed or native primitives are sound.

| Law family | Quantification and witnesses | Boundary |
|---|---|---|
| `specialization_preserves_first_match` | Arbitrary row lists, constructors, fields and levels; empty, retained and removed rows occur in the runtime corpus | Stable selection of row identities, not full term refinement |
| `selection_congruence` | Both Boolean cases and arbitrary tails | Auxiliary congruence, not a behavioral claim by itself |
| `irrefutable_specialization`, `irrefutable_default`, `first_row_selected` | Arbitrary token/body/tail inputs; a first variable row survives both eliminations and wins at a leaf | Compositional helper equations, not an induction over every complete lowering |
| `lowering_work_exhaustion` | Every matrix and scope with work 0 | Exact `Exhausted check` result |
| `erased_alias_stays_erased` | Arbitrary names and known terms; inhabited erased Flag binding at level 1 | Promotion preserves quantity 0 and scope identity |
| `alias_preserves_descent_and_identity` | Arbitrary names; inhabited affine Flag binding at level 1 | The smaller-level set and all scope metadata remain fixed |
| `default_completes_missing_branch`, `default_does_not_repeat_explicit_branch` | Arbitrary constructor tails with absent/present membership evidence; Off/On furnish both cases | One constructor step of default signature completion |
| `default_completion_witness` | Off explicit, On absent in a two-constructor datatype | Concrete inhabited normalization |
| `irrefutable_lowering_selects_first` | A first wildcard pair followed by a strict Off/Off row | Concrete normalization through the actual checker to a complete core tree |
| `exhaustive_matrix_has_no_missing_branch` | All four cases of a two-column Flag matrix | Concrete normalization to the exact branch tree, not a universal exhaustiveness theorem |

The empty-datatype catalog law is also filled. The restated parser
`multiple_scrutinees` law retains its proof. Both enter the checked proof chain.

## Operation and observation coverage

| Implementation family | Independent evidence | Important partitions |
|---|---|---|
| `items`, `flat_fields`, `flat_rows`, `flat` | 25 frozen enum hashes in two compiler lanes and two profiles; original gates | Flat unique matches retain their old path; overlapping/nested/multiple columns take the matrix path |
| `binder`, `validate`, `prepare`, `start` and catalog declaration-event lookup | Frozen forward-constructor, forward-binder, bare-constructor and unreachable-pattern fixtures | Unreachable bodies are ignored; invalid pattern names/arity are still checked |
| `bind_body`, `mark`, `promote` | Rebinding, shadowing, promotion and alias reconstruction calls | Alias order follows source binders; numeric levels survive simultaneous-column shadowing |
| `named`, `constructors`, `has_default`, `defaults`, `signature` | Default helper laws; wildcard/missing/duplicate-arm fixtures | Source constructor order, default completion and missing combinations |
| `fresh`, `specialize`, `default_rows`, `arms` | Stable-selection and irrefutable laws; nested sum/pair and row-order fixtures | Nested constructors, unused fields and wildcard survival |
| `variable_column`, `variable_step`, `alias_column`, `split`, `column_step`, `step`, `share` | Complete-lowering witnesses; column-reordering and matrix-work fixtures | Variable-only columns preserve the match frontier; constructor columns are strict; work exhaustion is explicit |
| `remarked`, `alias_bound`, `alias` | Alias identity/erasure laws; erased and affine nested fixtures plus the alias control | Erased inspection/use, Data promotion, reconstruction and affine reuse |
| Core evaluator and Wasm execution | 386 evaluator and 386 Node Wasm values from 25 accepted books | Both native/Bun compiler lanes; 3 recursive tree/list books; all accepted entry calls plus main |
| Empty datatypes and resource failure | Empty-type fixture and deep/shallow tree controls | No valid host ordinal for an empty type; arena exhaustion is distinct from a host failure |

## Hostile review and mutation evidence

The following six compilers all parse and typecheck, then violate their frozen
semantic witness in both native and Bun lanes. Type errors, timeouts and host
failures do not count as kills. Exact commands, hashes and observations are in
`nest.json`.

| Mutation | Witness | Actual wrong observation |
|---|---|---|
| Reverse rows before preparation | `first-match-multi`, `rank(1,1)` | Returns tag 2 (`R3`) instead of the frozen first-row result |
| Sort rows by constructor specificity | `first-match-nested`, `probe(1,1,0,1)` | Returns tag 2 (`R3`) instead of the frozen first-row result |
| Omit default completion | `wildcard-default` | Rejects accepted source with `Invalid check missing-arm` |
| Accept an incomplete branch set | `multi-missing` | Prints `Checked` for the frozen Invalid source |
| Turn erased nested aliases live | `erased-nested-live-use` | Prints `Checked` for the frozen Invalid source |
| Permit duplicate affine lexical uses | `nested-alias-affine` | Prints `Checked` although the seed rejects consumption more than once |

The first attempted erased-field mutation failed the compiler's own affine
check. It was rejected as an invalid mutant and contributes zero semantic
kills. The final mutation uses a type-correct quantity transformation; its
recorded wrong acceptance is the evidence. Total accepted kills: 6 mutants,
12 lane observations.

The wide total matrix is seed-accepted but exhausts the independent matrix
quota. The depth-12 recursive tree is seed/evaluator-accepted but exceeds the
65,536-byte arena (82,008 literal bytes including its depth value); Wasm reports
`Exhausted wasm arena-overflow`. A depth-4 tree needs 344 bytes and succeeds.
Rejected and exhausted compilation preserve an existing output artifact.

## Remaining scope

The receipt matches 38/40 frozen outcomes. `rec-swapped-args` and `rec-alias`
remain `Unsupported check recursive-call` instead of the frozen Invalid result.
Their expectations were not edited, and their 12 phase observations are
separate from passing conformance. The gate records
`qualification.complete=false`. Implementing the seed's full decreasing-call
rule is the next recursion obligation.

There is no universal end-to-end compiler refinement, exhaustiveness,
quantity-preservation or descent-preservation theorem here. Universal helper
laws, concrete complete-tree normalizations, and independent runtime checks
are distinct evidence. The 4096-step partition can conservatively exhaust on
otherwise valid matrices. Structured host arguments, generic/closure patterns,
owned-memory reclamation and broader recursion remain outside this increment.

This packet omits the full implementation and inherited proof source. It is a
coverage/claim review, not a substitute for complete source context during live
review. The implementation family is 43,223 bytes; the full proof family is
132,218 bytes and exceeds the 48,000-byte composition limit. The separate
preflight receipt records further context truncation and unresolved imports.

Source identities for this packet are recorded in `verification.json` and
`nest.json`; the latter hashes all compiler source, frozen fixtures, controls,
contracts and gate inputs. The frozen fixture tree and expectations are
unchanged from branch base `6f132ea`.
