# Modules review round 5

Round 5 had four confirmed findings. Three are fixed. The fourth is a coordinator
decision; this record gives its evidence and does not claim it closed. Each
code finding had its seed observations frozen in
[`review-round5.json`](review-round5.json) before its repair. Every earlier
fixture, expectation and pinned host observation is unchanged.

| Finding | Freeze | Repair | Disposition and evidence |
| --- | --- | --- | --- |
| `census:test` red at branch head (blocking) | — | `e05d1f8`, `f7b2239` | **Fixed.** a50bbb5 added `adjacent` and `result_type` to `src/parse.bend`, but the census fixture still pinned 41 frontend definitions. The literal is now 43 (lex 6, parse 22, syntax 15), and 44 after this round's `continues`. The gate runner now registers `census:test`, which passes only on a complete TAP record, so the next frontend edit cannot leave it red unnoticed. |
| A module-local binder shadowing a module function is called as that function (blocking) | `021453a` | `ed0e7d1` | **Fixed.** A parameter, field binder or let binder named `flip` in `lib/m` made `flip(b)` call `lib/m.flip`: Checked, Lit{} and, for two of them, Wasm returning 1. The seed rejects all three. Each now reports `Invalid check unknown-function`. The entry keeps `Invalid check not-callable`, and an unshadowed module call still runs to Lit. |
| Single-file behavior changed beyond the charter (major) | — | — | **Open: awaiting the coordinator's decision.** The table under [Single-file deltas](#single-file-deltas) lists each change with its seed evidence, frozen fixture, authorization and recommendation. Reverting any change marked as a repair would restore a confirmed unsound acceptance or D4 violation. |
| `&` and `|` types are Invalid where the seed accepts them (major) | `d1ea242` | `730d228` | **Fixed, with one part disputed.** Parameters, constructor fields and typed lets now report `Unsupported parse parameter-type` or `binding-type`. In a typed let, the `->` arrow and an application are reported the same way. The disputed part: seed-rejected programs without a `Pair` or `Or` declaration become `Unsupported`, not the finding's `Invalid`. See [Mechanism](#mechanism). |

## Mechanism

**Call heads.** `qualify.walk_in` read a variable through `local`, which consults
the lexical binders, but a call head through `reference`, which does not. A call
head is now read exactly as a variable. A bound head keeps its bare spelling.
The qualified book has no function of that name, so the unchanged checker
reports `unknown-function`. In the entry the namespace is empty, so the bare name
is the global function and the checker's own bound test gives `not-callable`,
as before. Both are Invalid; the diagnostic code differs because module
functions are qualified.

**Type operators.** The seed parses a parameter, field or let annotation as a
term. An application `(`, an arrow `->`, and the infix `&` (Pair) and `|` (Or)
continue that term. Knot reads one bare name. `parse.continues` names those four
continuations. `parameter_end`, shared by parameters and constructor fields,
reports them and `<` as `Unsupported parse parameter-type`. A typed let keeps
`type-application` at `<` and reports the four continuations as
`Unsupported parse binding-type`. Other continuations keep their Invalid codes.
The frozen controls `p: Light Light` (`argument-separator`) and
`x : Light Light` (`expected-=`) show this.

**Why seed-rejected operator types are Unsupported.** `&` names whatever `Pair`
is in scope when the seed checks the type. `local-pair-parameter` declares
`def Pair(A: Type, B: Type) -> Type` after its use, with no import, and the
seed prints Lit{}. `undeclared-pair-parameter` is the same file without that
declaration, and the seed rejects it (`expected : a defined name`). The parser
cannot tell the two apart without a later declaration, so both are Unsupported.
A resolution-aware Invalid would need the type term in the syntax tree and a
checker rule for it. This conservative choice matches round 4's
`-> Light & Light`, which is Unsupported whether or not Base is imported.

## Single-file deltas

These are the single-file CLI changes the branch makes relative to `main`. The
coordinator decides for each whether to accept it or to split it into its own
reviewed increment. No change here is claimed as accepted. "Before" is `main`
(90b4052, whose `src/` equals the merge base). The single-file rows were rerun
on both builds (`.local/modules/r5-single-file-deltas.txt`).

| Change | Before | After | Seed | Frozen evidence | Authorization | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| Let binder named like an earlier constructor | Checked | `Invalid check constructor-pattern-binder` | rejects | round 3 `let-single-ctor`, mutant `file-let-binder-unchecked` | Round-3 prompt: "Add the matching rule to check.bend so single-file mode agrees" | Accept. Reverting restores an unsound acceptance. |
| Arm binder named like an earlier constructor | `Unsupported check variable-pattern` | `Invalid check constructor-pattern-binder` | rejects | round 3 `arm-earlier-ctor`, mutant `file-arm-binders-unchecked` | Not requested. It follows from the ordered binder walk. | Accept for lane agreement: the module lanes give the same Invalid. Reverting is sound but less precise. |
| Field binder named like a later constructor | `Invalid check constructor-pattern-binder` | accepted | accepts (Lit) | round 3 `field-later-ctor`, `field-cross-module-ctor`, mutant `field-binder-book-wide` | Round-3 finding: "Make the check order-sensitive, as in the seed" | Accept. Reverting restores a D4 violation. |
| Field-binder test moved from `patterns.bend`/`catalog.bend` to `qualify.rebinds` (`c2722cf`) | book-wide test in the checker | ordered walk before checking | — | fields gate unchanged: 40 seed fixtures, 9 mutants, `constructor-name-binder` still Invalid at 121:123:8:13 | Mechanism of the previous row | Accept, and notify the fields owners. The removed test ignored declaration order. |
| Binder walk bound | — | `Exhausted check` after 65,536 steps | — | not reachable under the 65,536-byte source cap | Resource bound of the walk above | Accept. |
| Result type longer than one name | `Invalid parse function-result` | `Unsupported parse result-type` | accepts (Lit) | round 4 `result-parenthesized`, `result-arrow`, `result-equality`, mutant `result-type-invalid` | Round-4 finding 5, in the shared parser | Accept. Reverting restores a D4 violation. |
| Spaced `- >` arrow | Checked | `Invalid parse function-result` | rejects | round 4 `result-spaced-arrow`, mutant `spaced-arrow-accepted` | Not requested. Self-found in round 4, in the same function. | Accept. Reverting restores an unsound acceptance. |
| Parent-relative import | `Invalid parse declaration-name` | `Unsupported parse import` | accepts (Lit) with the file present | modules fixture `parent-relative-path`, in the bundle lanes only | Original modules prompt (D4) | Accept. Reverting restores a D4 violation. |
| `&` or `|` after a parameter or field type | `Invalid parse argument-separator` | `Unsupported parse parameter-type` | accepts with a `Pair` in scope | round 5 `local-pair-parameter`, `undeclared-pair-parameter`, mutant `type-operators-separate` | Round-5 finding 4 | Accept. Reverting restores a D4 violation. |
| `(`, `->`, `&` or `|` after a typed-let type | `Invalid parse expected-=` | `Unsupported parse binding-type` | accepts `f : Light -> Light` | round 5 `arrow-let`, `undeclared-pair-let`, mutant `binding-type-continuation-invalid` | Round-5 finding 4, same class | Accept. Reverting restores a D4 violation. |

`src/SPEC.md` and `src/CONTRACT.json` `legacy_commands` list the same changes.
When the coordinator has decided, the decision belongs next to them.

## Laws, fixtures and mutants

Three new filled laws. `call_head_has_local_scope` brings the modules gate's
four proof entries to 96: loader and path 34, qualification 27, Base selection 20,
pin helpers 15. `parameter_type_operator` and `binding_type_operator` bring
`src/PROOF.bend` to 20. Each was checked in a scratch copy: it prints
`All terms check.` unmutated, and fails at its own location under its matching
mutation (`.local/modules/r5-law-*.txt`). These are helper and classification
laws, not a theorem of parser or compiler correctness.

Round 5 freezes 18 seed fixtures, one seed call each, run from the repository
root with the frozen bundle:

- **Five call-head fixtures:** parameter, field and let shadowing; an unshadowed
  control that runs to Lit with its audited module files; and the entry-only
  program, which also runs the single-file CLIs.
- **Thirteen type-operator fixtures.** Six also run the single-file CLIs.

Three new type-correct semantic mutants are each killed by their frozen witness:

- `call-head-resolved-globally`, by `shadow-parameter-call`: Checked.
- `type-operators-separate`, by `pair-parameter`: Invalid argument-separator.
- `binding-type-continuation-invalid`, by `arrow-let` in the single-file lane:
  Invalid expected-=.

## Preflight

All preflight runs were offline and made no provider requests.

- **Manifest.** 23 groups, 1,410 declaration occurrences, all 23 compositions
  available. No truncated or role-limited declarations and no structural
  blockers. `frontend-parsing` is 21,648 bytes, `module-loading` 33,344 and
  `checking` 47,400, all under the 48,000-byte bound.
- **Direct.** The six changed implementation, law and proof files hold 170
  declarations. Twelve contexts are truncated: nine by the caller or byte
  limit, three by the file limit. The combined composition is oversized at
  61,533 bytes against the 48,000-byte bound, which gives 13 structural
  blockers.

No style rating or style pass is claimed. Live Perch review remains with the
coordinator.

## Gates

The full runner, run on the tree of `730d228`, passed all 22 gates, including
the newly registered `census:test` (79 tests). The modules gate checked:

- 130 fixtures and 138 seed calls;
- 260 checks, 276 evaluations and 260 compilations;
- 70 Wasm observations, 29 byte-identity pairs and 202 preserved outputs;
- 62 trust audits;
- 22 pin, 6 tampered-Base and 22 output-guard observations;
- 39 semantic mutants.

Of the other gates, frontend (14 fixtures, 4 mutants), classification (17, 6)
and selfhost (65 cases: 2 passed, 63 blocked, 5 reviewed D4 gaps) have the
same counts as in round 4. `gates:verify` runs 19 tests.

## Known limits

- **Diagnostic codes differ by namespace.** A shadowed call head is
  `unknown-function` in a module and `not-callable` in the entry. Both are
  Invalid, and the seed rejects both. Unifying them would reorder the shared
  checker's lookup and change single-file diagnostics, so it was not done.
- **Seed-rejected operator types are Unsupported**, as explained under
  [Mechanism](#mechanism).
- **Intermediate commits.** `f7b2239` and `021453a` leave the census inventory
  stale. `f7b2239` changed the runner, and the inventory hashes it. At those two
  commits `census --check` exits 1 and `census:test` passes 77 of 79 tests.
  `ed0e7d1` regenerates the inventory, and every later commit passes both
  (79/79).
- **Carried over from round 4:** climbing relative spellings, the coarse quote
  rule, the output guard's canonical-spelling limits and `def main?()` are
  unchanged. The selfhost `modules` and `packages` needs stay unflipped.
