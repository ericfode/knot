# Modules review round 6

Round 6 had three code findings and one coordinator decision. All three code
findings are fixed. Every seed observation was frozen in
[`review-round6.json`](review-round6.json) in `4d2e605`, before any repair.
Every earlier fixture, expectation and pinned host observation is unchanged.

| Finding | Freeze | Repair | Disposition and evidence |
| --- | --- | --- | --- |
| A sibling module's bare name equal to its own earlier qualified name is accepted (blocking) | `4d2e605` | `a9bc6da` | **Fixed.** In `m.bend`, `def f` then `def m.f` was Checked, evaluated and emitted as the exports `m.f` and `m.m.f`. The seed rejects it (`duplicate declaration: m.f`). It is now `Invalid load duplicate-global`, and so are the constructor and type forms. The reversed order is still accepted. |
| `import .//x.bend` and `import 0x<hash>//x.bend` are Invalid (D4) | `4d2e605` | `903a416` | **Fixed by acceptance.** Both spellings load with the seed's resolution. A diamond through `./x.bend` and `.//x.bend` loads `x.bend` once. The five seed-rejected empty-segment controls stay `Invalid load import-path`. |
| Dotted let, typed-let and field binders are accepted in both lanes (soundness) | `4d2e605` | `ee187a8`, `3424eb7` | **Fixed.** An unbound dotted binder is now `Invalid check dotted-binder` in the bundle and single-file lanes. The rule depends on scope, because the seed accepts a dotted binder that rebinds a bound name. See [Mechanism](#mechanism). |
| Single-file CLI behaviour beyond the charter (major, from round 5) | — | docs | **Decided: accepted by the coordinator on 2026-09-28.** The decision is recorded under "Single-file deltas (accepted by the coordinator, 2026-09-28)" in `src/SPEC.md` and `SPEC.md`, and as `legacy_commands_decision` in `src/CONTRACT.json`. Round 6 adds one row, below. |

## Mechanism

**Registration order.** The seed's `parse_fresh` tests a declaration's spelling
and its qualified name against every declaration registered so far, the
current file's included. Knot tested them only against earlier files.
`qualify.declarations` now adds each type and function to the term table, and
`constructors` adds each constructor to the constructor table, before the next
declaration is qualified. `fresh` itself is unchanged. The test is
order-sensitive, as in the seed: `def m.f` then `def f` registers `m.m.f`, then
`m.f`, and both are fresh. The same test catches exact duplicates within one
file one pass earlier. In the bundle lanes they are now `Invalid load
duplicate-global`; they used to be `Invalid check duplicate-global` or
`duplicate-constructor`. The single-file lanes, which do not qualify, are
unchanged.

**Rooted paths.** The seed strips one leading `./` (or the `0x<hash>/`
prefix). Its path grammar's leading `/` alternative then admits the remaining
slash, and `path.posix.normalize` collapses it. `imports.valid_parts` now
accepts exactly that shape (`rooted`): after `.` or a hash head, one empty
segment followed by plain names. It stays Invalid for `..` or a second empty
segment after it, as the seed. Identity needed no change, because `join`
already normalizes. The law `one_root_slash_has_one_identity` states it.

**Dotted binders.** The seed resolves a binder before binding it: `parse_var`
returns a `Var` only for a name on the binder stack, and an unbound dotted name
becomes a `Ref`, which neither `parse_patt` nor a typed let accepts. So the
rule depends on scope. The frozen controls show that the seed accepts
`a.b = a.b`, `a.b : Light = a.b` and `case Box{a.b}` inside `def f(a.b: Light)`.
It also accepts an erased let (`-a.b = x`), whose name `parse_name` reads
directly.

A parser rule on the spelling alone would report those seed-accepted programs
`Invalid`. The rule therefore lives in the checker, which both lanes share,
at the two places a binder enters the scope:

- `E.binder(bindings, token)`: a dotted binder must name a binding already in
  scope. `bound` moved from `check.bend` to `scope.bend` for it.
- The let case of `check.run` resolves its binder before checking the value.
  An erased let is exempt.
- `patterns.add` resolves each field binder before adding it.

A dotted top-level arm binder stays `Unsupported check variable-pattern`, the
conservative classification the review accepted.

The first form of the repair (`ee187a8`) resolved field binders in a separate
traversal. That pushed the offline `checking` composition to 48,595 bytes,
over the 48,000-byte bound. `3424eb7` moved the test into `add`. The scope
there includes the pattern's earlier fields, but each of those was bound only
after passing the same test, so the verdicts are unchanged.

## Single-file deltas

The coordinator accepted every row of the
[round-5 table](REVIEW-ROUND-5.md#single-file-deltas) on 2026-09-28. Round 6
adds one row under the same rule:

| Change | Before | After | Seed | Frozen evidence | Authorization |
| --- | --- | --- | --- | --- | --- |
| Unbound dotted let, typed-let or field binder | Checked | `Invalid check dotted-binder` | rejects | round 6 `dotted-let-binder`, `dotted-typed-let-binder`, `dotted-field-binder` (single-file lane too), mutants `dotted-let-binder-unresolved` (single-file lane), `dotted-field-binder-unresolved` | Round-6 finding 3: "in the shared parser or binder walk. It must never be accepted." |

A dotted binder that rebinds a bound name, an erased dotted let and a dotted
parameter stay accepted in both lanes (frozen `dotted-rebound-*`,
`dotted-erased-let`, `dotted-parameter`).

## Laws, fixtures and mutants

Four new filled laws. Each prints `All terms check.` unmutated and fails at
its own location under its matching mutation (`.local/modules/r6-law-*.txt`):

- `own_names_are_registered_in_order` (qualification). The pair `[f, m.f]`
  fails, `[m.f, f]` succeeds, and `[On, m.On]` in one type fails.
- `one_root_slash_is_plain` and `one_root_slash_has_one_identity`
  (loader/path). They state which empty segments are valid, and that
  `.//lib/flag.bend` and `0xab//flag.bend` resolve exactly as their
  single-slash spellings.
- `dotted_binder_rebinds_only_a_bound_name` (checker, `src/check-PROOF.bend`).
  An unbound dotted binder is Invalid; a bound one and an undotted one are not.

With these, the modules gate's four proof entries hold 99 laws: loader and
path 36, qualification 28, Base selection 20, pin helpers 15. `check-PROOF.bend`
adds the eighth checker law. These are helper and classification laws, not a
theorem of loader or checker correctness.

Round 6 freezes 28 seed fixtures, one seed call each, run from the repository
root with the frozen bundle. Before the repairs, 16 failed their frozen
obligation (`.local/modules/r6-before.txt`); after them, all pass
(`.local/modules/r6-after.txt`).

- **`own`, 8 fixtures.**
  - Rejected by the seed: the function, cross-type constructor, in-type
    constructor and type forms, and exact function and constructor duplicates
    in a module.
  - An exact duplicate in the entry, rejected in both lanes: `load` in the
    bundle lane and `check` in the single-file lane.
  - The reversed order, accepted with its audited files.
- **`hub`, 10 fixtures.**
  - Accepted, with their audited files and Wasm: local, nested, hash,
    transitive and diamond rooted imports.
  - Seed-rejected controls: `./lib//`, `..//`, `.//../`, `.///` and `lib//`.
- **`dotted`, 10 fixtures, 9 of them also through the single-file CLIs.**
  - Rejected by the seed: let, typed-let and field binders, and a let binder
    inside a module.
  - Accepted by the seed: a parameter; a rebound let, typed let and field
    binder; an erased let.
  - Unsupported in Knot: the arm binder.

Eight new type-correct semantic mutants, each killed by its frozen witness:

| Mutant | Mutation | Witness | Mutant's result |
| --- | --- | --- | --- |
| `own-terms-unregistered` | a function is not registered for its successors | `own-bare-after-qualified` | Checked |
| `own-constructors-unregistered` | a constructor is not registered for its successors | `own-constructor-in-type` | Checked |
| `rooted-local-invalid` | `.//` is Invalid again | `rooted-local-import` | Invalid import-path |
| `rooted-hash-invalid` | `0x<hash>//` is Invalid again | `rooted-hash-import` | Invalid import-path |
| `dotted-let-binder-unresolved` | the let binder is not resolved | `dotted-let-binder`, single-file lane | Checked |
| `dotted-field-binder-unresolved` | a field binder is not resolved | `dotted-field-binder` | Checked |
| `dotted-binder-scope-blind` | every dotted binder is rejected | `dotted-rebound-let` | Invalid dotted-binder |
| `erased-let-resolved` | an erased let's binder is resolved | `dotted-erased-let` | Invalid dotted-binder |

## Preflight

All preflight runs were offline and made no provider requests.

- **Manifest.** 23 groups and 1,425 declaration occurrences. There are no
  truncated or role-limited declarations and no structural blockers, and all 23
  compositions are available. `checking` is 47,988 bytes against the
  48,000-byte bound, and `module-loading` is 34,145.
- **Direct.** The eight changed implementation and law files hold 238
  declarations. Twenty-six contexts are truncated: 11 by the caller or byte
  limit, 11 by the helper limit and 4 by the file limit. None of them is a
  declaration this round added or changed. The combined composition is
  oversized, at 160,834 bytes.

No style rating or style pass is claimed. Live Perch review remains with the
coordinator.

## Gates

The full runner (`npm run -s gates -- --refresh --jobs 3`) passed all 22 gates
on the tree of `ba624dd`. Receipt drift was the same as in round 5: 64
identical, 16 semantic and 9 volatile-only. The modules gate checked:

- 158 fixtures and 166 seed calls;
- 316 checks, 332 evaluations and 316 compilations;
- 90 Wasm observations, 39 byte-identity pairs and 238 preserved outputs;
- 84 trust audits and 192 single-file observations;
- 22 pin, 6 tampered-Base and 22 output-guard observations;
- 47 semantic mutants.

The other gates have their round-5 counts, except for two inventories that
grew with this round's files. The census now counts 904 declarations (it was
893), and the bootstrap corpus holds 1,035 files (it was 996). The checker
gate, which runs `src/check-PROOF.bend`, passed with its 7 mutants.
`gates:verify` runs 19 tests. Only the modules receipt is committed; shared
receipts are left for the coordinator.

Two earlier runner passes on the same tree each failed one gate: recursion
first, then bootstrap. Both failures were the seed's host message `bend needs
clang 14 or newer ... (found no clang)`, under a load average of about 50.
Every other gate passed in both runs (`.local/modules/r6-gates-run{1,2}.stderr`).
main fixed this flake in `90b4052`, by passing `CC` and `SDKROOT` to every gate;
this branch predates that fix. For the passing run, the toolchain clang
(`xcrun --find clang`, the compiler that main passes) came first on `PATH`,
`SDKROOT` was set, and 3 jobs ran at once. No gate assertion or runner file
changed.

## For the coordinator

- **Nest conflict.** `campaign/nest` rejects dotted binders in the parser, by
  spelling: `S.binder` in `Term{pattern}` and `BindingStart`. Merged over this
  branch, that rule would make the seed-accepted `dotted-rebound-let` and
  `dotted-rebound-field` Invalid, which is a D4 violation, and this gate would
  fail on them. The two rules agree on every unbound dotted binder. Keep the
  scope-aware checker rule, and narrow nest's parser rule, or drop it.
- **Owner notices.** This round edits the checker files `scope.bend`
  (`bound`, `binder`), `check.bend` (the let case) and `patterns.bend` (`add`).
  The checker, fields, structural, recursion, classification and frontend gates
  pass unchanged.
- **Byte headroom.** The `checking` composition has 12 bytes of headroom. The
  next edit to its six files needs a manifest split, which is a coordinator
  decision.
- **Intermediate commit.** At `3424eb7`, the committed `selfhost.json`
  inventory already records the `accepted.json` hash of the next commit's
  gate script, so `census --check` reports it stale there. The next commit
  restores agreement, and every other round-6 commit passes `census --check`.
- **Carried over:** live Perch, the selfhost `modules` and `packages` needs,
  and refreshing shared receipts after the merge.
