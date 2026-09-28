# Modules review round 7

Round 7 had two major findings and one coordinator decision. Both findings are
fixed in both lanes. Every seed observation was frozen in
[`review-round7.json`](review-round7.json) in `c8ac3ef`, before any repair.
Every earlier fixture, expectation and pinned host observation is unchanged.
Main (`c0bd08d`) was merged first, in `a0c98c2`.

| Finding | Freeze | Repair | Disposition and evidence |
| --- | --- | --- | --- |
| Binders are ignored in type positions, so Knot accepts programs the seed rejects (major, soundness) | `c8ac3ef` | `fbc5d3b` | **Fixed.** A value binder named in a later type position of its scope is `Invalid check binder-as-type` in both lanes: a later parameter type, the result type, a typed-let annotation after a let (live or erased) or arm field binder, and a later field type. The seed-accepted controls stay accepted with agreeing values, and `-Light: Type` stays `Unsupported parse parameter-type`. |
| A declared type or function used as an unapplied term is `Invalid check free-name`, but the seed accepts it (major, D4) | `c8ac3ef` | `e53f4ce` | **Fixed.** It is `Unsupported check type-as-term` or `Unsupported check function-reference` in both lanes, for own, forward, module and Base declarations. A constructor without braces and an undeclared name stay `Invalid check free-name`. A Base declaration is never selected, parsed or checked through such a mention. |
| Dotted-binder conflict with `campaign/nest` (review finding 1) | — | docs | **Decided by the coordinator.** The scope-aware checker rule on this branch is canonical, because it matches the seed on both the rebound and the unbound controls. Nest merges to main first; the coordinator then runs a separate reconciliation round on this branch that merges main, removes nest's parser rule and amends any nest-frozen dotted-binder prefixes in one seed-citing amendment commit. That reconciliation is not done here, and no nest file is edited. |

## Mechanism

**Type positions (finding 1).** The seed reads a type as a term, so a binder
already in scope shadows a type name. `catalog.unshadowed` is the one rule: a
type position naming a binder in scope is `Invalid check binder-as-type`. It is
always Invalid, because every Knot binder holds a value; a Type binder
(`-T: Type`, `T : Type = …`) is Unsupported at parse and never reaches it.
Each type position applies the rule to its own scope:

- `signature_scope` reads a signature left to right. Each parameter's type sees
  the binders before it, and the result type sees all of them. It runs before
  `parameters`, which stays scope-free: the checker gate pins its 256-parameter
  bound on `N0: N0, N1: N0, …`, whose later types name the first binder.
- `fields` resolves a later field type against the earlier field binders it
  already tracks for duplicate fields (`scoped_type`).
- `check.annotation` resolves a typed-let annotation against the bindings in
  scope. They include parameters, live and erased lets, and arm fields, but not
  the let's own binder (`Light : Light = Lit{}` stays accepted).

Qualification must leave such a name bare, or the checker sees a qualified
type and accepts it. A type position now reads the scope, as a call head
already did: `local` replaces `reference` for parameter, result and annotation
types. Each item of a sequence sees the binders before it, and a declared
constructor's fields bind only within it (a constructor contributes binders
only as a pattern). Without that last rule, `Box{Flag: Flag}` would leave the
next constructor's `Other{v: Flag}` unqualified in a module
(`typebind-module-constructor`).

The Base slice still follows a type position that names a binder. That can
select a Base type the program never uses, but the program is rejected with
`binder-as-type` either way.

**Declared globals as terms (finding 2).** `scope.term` resolves a term name
lexically first. An unbound name goes to `catalog.unbound`, which names its
declaration: a type is `Unsupported check type-as-term`, a function
`Unsupported check function-reference`, and anything else, including a
constructor without braces, `Invalid check free-name`. A match scrutinee must
be a binder, so it keeps the binder-only `lookup`. The seed rejects a function
as a scrutinee, and so does Knot, with `free-name`
(`global-scrutinee`).

The checker sees only the Base slice, so an unselected Base declaration is not
in its catalog. The slice therefore classifies first. `base-load.mentions`
collects the names a user definition reads as values, with the scoping of
`references`. A mention of a Base declaration is Unsupported with the same
codes, before any Base declaration is selected. `-h = IO.write` and
`-T = Empty` show it: selecting them would report `Unsupported check
foreign-definition` and `Unsupported check base-empty-datatype`, which is
what the `base-values-selected` mutant produces.

In a bundle that mentions both a module function and a Base function, the
slice reports the Base mention first, because slicing precedes checking. Both
reports are the same Unsupported code.

**Seed-rejected contexts.** Only the value of an unannotated let has no
expected type. Everywhere else a datatype is expected, and the seed rejects a
function or type there with a type mismatch. Knot reports the same Unsupported
code (probes, not gate fixtures: `flip` as a function body, `flip(flip)`,
`y : Light = Light`). This is conservative under D4. Reporting
`Invalid check type-mismatch` there would need the same distinction in the Base
slice, which has no types.

## Single-file deltas

The coordinator accepted the round-5 and round-6 rows on 2026-09-28. Round 7
adds two rows, both authorized by this round's findings:

| Change | Before | After | Seed | Frozen evidence | Authorization |
| --- | --- | --- | --- | --- | --- |
| A binder named in a later type position of its scope | Checked | `Invalid check binder-as-type` | rejects | round 7 `typebind-result`, `-parameter`, `-result-only`, `-let`, `-erased-let`, `-field`, `-arm` (single-file lane too); mutants `type-positions-scope-blind` and `annotation-scope-blind` (single-file lane) | Round-7 finding 1: "Resolve every type position in its lexical scope" |
| A declared type or function as an unapplied term | `Invalid check free-name` | `Unsupported check type-as-term` or `function-reference` | accepts in an unannotated let; rejects where a datatype is expected | round 7 `global-erased-type`, `-type-let`, `-function`, `-live-function`, `-forward-function` (single-file lane too); mutant `declared-globals-free` (single-file lane) | Round-7 finding 2: "Report the declared case Unsupported … in both lanes" |

The controls stay unchanged in both lanes: `typebind-own-type`, `-sibling`,
`-other-arm`, `-next-constructor` and `-type-parameter`, and
`global-local-constructor`, `-undeclared` and `-scrutinee`.

## Laws, fixtures and mutants

Six new filled laws. Each prints `All terms check.` unmutated and fails at its
own location under its matching mutation
(`.local/modules/r7-law-typebind-mutants.txt`, `r7-law-globals-mutants.txt`):

- `type_positions_read_their_scope` (catalog, `src/catalog-PROOF.bend`). A
  field's own type precedes its binder; a later field type, a later parameter
  type and the result type see the earlier binders.
- `annotation_reads_the_scope` and `term_names_a_binder_or_a_declaration`
  (checker, `src/check-PROOF.bend`). A binder shadows a type in an annotation.
  A term name is a binder first; unbound, it is a type, a function or free.
- `type_positions_read_the_scope` (qualification). A bound name stays bare in
  a later parameter, result and let type, and a declared constructor's field
  binder does not reach the next constructor.
- `mentions_are_free_values` and `base_values_are_unsupported` (Base
  selection). A scrutinee, call head, type or binder is not a mention; a Base
  type or function mention is Unsupported with its kind, and a constructor name
  is not a declaration there.

With these, the modules gate's four proof entries hold 102 laws: loader and
path 36, qualification 29, Base selection 22, pin helpers 15.
`check-PROOF.bend` holds ten checker laws and `catalog-PROOF.bend` six. These
are helper and classification laws, not a theorem of checker correctness.

Round 7 freezes 33 seed fixtures, one seed call each, run from the repository
root with the frozen bundle. Before the repairs, 22 failed their frozen
obligation (`.local/modules/r7-before.txt`); after them, all pass
(`.local/modules/r7-after.txt`).

- **`typebind`, 17 fixtures, 12 of them also through the single-file CLIs.**
  - Rejected by the seed: a later parameter type, the result type (twice), a
    typed let after a live and after an erased let, a later field type and an
    annotation after an arm field binder. Also a module function, a module
    typed let, a dotted parameter binder and a Base type.
  - Accepted by the seed: the parameter's own type, a sibling function, another
    arm, and the next constructor in the entry and in a module.
  - Unsupported in Knot: `-Light: Type`, which the seed accepts.
- **`globals`, 16 fixtures, 8 of them also through the single-file CLIs.**
  - Accepted by the seed, Unsupported in Knot: an erased and a live type or
    function value, a forward function, a module function and type, and a Base
    function, type, foreign function and empty type.
  - Rejected by the seed, `Invalid check free-name` in Knot: a constructor
    without braces in the entry, a module and Base; an undeclared name; and a
    function as a match scrutinee.

Six new type-correct semantic mutants, each killed by its frozen witness:

| Mutant | Mutation | Witness | Mutant's result |
| --- | --- | --- | --- |
| `type-positions-scope-blind` | `unshadowed` never fails | `typebind-result`, single-file lane | Checked |
| `qualified-parameter-types-global` | a parameter type is resolved globally | `typebind-dotted` | Checked |
| `declared-fields-leak` | a declared constructor's fields scope over the next | `typebind-module-constructor` | Invalid unknown-type |
| `annotation-scope-blind` | an annotation ignores the scope | `typebind-arm`, single-file lane | Checked |
| `declared-globals-free` | a declared type or function is free again | `global-function`, single-file lane | Invalid free-name |
| `base-values-selected` | a Base value mention selects Base | `global-base-foreign` | Unsupported foreign-definition |

## Preflight

All preflight runs were offline and made no provider requests.

- **Manifest.** The `checking` composition grew to 50,259 bytes, over its
  48,000-byte bound. It now composes check, scope and patterns in full and takes
  the declaration catalog as an interface, like the checker collaborators in
  `wasm-emission`. `catalog.bend` stays composed in full in `catalog` (19,302
  bytes). All 23 groups and 1,428 declaration occurrences check, with no
  truncated or role-limited declarations and no structural blockers. All
  compositions are available; `checking` is 37,484 bytes.
- **Direct.** The thirteen changed implementation and law files hold 335
  declarations. Thirty-two contexts are truncated: 11 by the caller or byte
  limit, 14 by the helper limit and 7 by the file limit. Two of them are
  changed declarations, both at the helper limit: `check.run`, which was
  already truncated in round 6, and `base-load.slice`. The combined composition
  is oversized, at 137,259 bytes.

No style rating or style pass is claimed. Live Perch review remains with the
coordinator.

## Gates

The modules gate, run directly on the tree of `e53f4ce` with the scaled
timeouts, passed:

- 191 fixtures and 199 seed calls;
- 382 checks, 398 evaluations and 382 compilations;
- 96 Wasm observations, 42 byte-identity pairs and 298 preserved outputs;
- 94 trust audits and 312 single-file observations;
- 22 pin, 6 tampered-Base and 22 output-guard observations;
- 53 semantic mutants.

The checker, structural, fields and recursion gates passed directly after the
finding-1 repair. Every proof entry, including `check-PROOF.bend` and
`catalog-PROOF.bend`, prints `All terms check.`

## For the coordinator

- **Owner notices.** This round edits the checker files `catalog.bend`
  (`unshadowed`, `scoped_type`, `signature_scope`, `found`, `unbound`,
  `collect_signatures`, `fields`), `scope.bend` (`term`, and a new import of
  `catalog.bend`) and `check.bend` (`annotation`, the variable and let cases),
  with laws in `catalog-LAWS.bend` and `check-LAWS.bend`.
- **Manifest.** `checking` takes the catalog as an interface, as described
  under Preflight.
- **Seed-rejected contexts** are reported Unsupported, as described under
  Mechanism. Refining them to `Invalid check type-mismatch` is a later option.
- **Carried over:** the nest reconciliation round, live Perch, the selfhost
  `modules` and `packages` needs, and refreshing shared receipts after the
  merge.
