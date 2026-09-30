# D26 reconciliation after closures

Generics merges after closures. This worktree does not merge that dependency;
its current Unsupported pins remain enforceable until the merged tree checks
the forms. The coordinator owns the separate D26 re-freezing commit, preserving
all original source hashes, seed observations and agreed values.

| Colliding pin | D26 verdict in the combined tree | Evidence and merge action |
| --- | --- | --- |
| `tests/subsets/classification/function-parameter.bend` | parse/check succeed; evaluator returns the unchanged seed value `On{}`. Compilation follows the selected profile's actual capability. | Seed kernel and native wrapper both return `On{}`; closures `a1d68911` checks it (last review). Generics owns supersession of the shared frontend phase pin and both parameter-type mutants. |
| `def-references/def-reference-monomorphic` | Checked; the closed entry returns `On{}` | Both seed lanes return `On{}`; closures checks the same source. Re-freeze this generics-owned Unsupported pin in the coordinator's dedicated D26 commit. |
| `def-references/def-reference-erased-monomorphic` | Checked; the closed entry returns `Off{}` | Both seed lanes return `Off{}`; closures checks it. Re-freeze this generics-owned Unsupported pin in the same dedicated D26 commit. |
| `def-reference-live`, `def-reference-erased`, `def-reference-forward-erased` | Unsupported while the generic checker cannot check first-class definition values | The unused generic family selects `generics.bend`; closures' monomorphic Variable rule alone does not qualify that path. Preserve these pins until the generic lane actually checks the form (D4). |
| `function-value-mismatch` | Unsupported in the unimplemented generic lane; Invalid type mismatch only once that lane types the function value | The seed rejects the function value against Flag. Do not promote a closure-capable monomorphic rule into a generic acceptance claim. |
| `fixtures/closure-apply` | Unsupported until generic function types/values are checked | Seed-valid higher-order generics remain a distinct dual-checker obligation. Retain the fixed seed calls. |

Fresh seed replay is recorded in ignored
`.local/generics/review-5/closure-seed/observations.json`: the three colliding
books are seed-checked unchanged, then kernel-run unchanged and native-run
through a wrapper importing Base and the unchanged book. Constructor results
agree in all three observations. Direct native builds of these import-free
fixtures fail the seed's host requirement `a build needs import Base`; wrappers
supply that build requirement without changing a fixture.

The scope review's closures observations are in
`docs/compiler-campaign/handoff/findings/generics-last.md` on main. Source
inspection of `a1d68911` confirms the function-type parser and named-definition
Variable path. These are stored review observations, distinct from the fresh
seed replay; no closures implementation is accepted or merged by this report.

At integration:

1. Preserve closures' function-type parsing, including `->`; apply the common
   adjacency guard to its arrow route. Keep generic type application parsing.
2. Resolve lexical bindings first. In the monomorphic Variable arm, resolve a
   checked definition through closures before `scope.term_name`'s Unsupported
   fallback. Preserve datatype/type-level and genuinely free-name handling.
3. Re-freeze the three losing pins above in their own D26 commit. Recheck each
   book in both seed lanes. Match the merged tree's phase/code for a profile
   refusal; do not guess an enum-compiler outcome from a checker observation.
4. Re-express `parameter-type-invalid` (frontend) and
   `parameter-application-invalid` (classification) as the same erroneous
   Invalid demotion of a remaining Unsupported type boundary. Their current
   `Flag -> Flag` witness must become an accepted control. Freeze a seed-valid
   pair/intersection parameter witness against the merged parser before changing
   the anchors; if no witness reaches that rule, a coordinator ruling must name
   their retirement and resulting kill counts. No witness or kill disappears
   silently. The generic `def-reference-free` mutant retains its generic-book
   witness and its Unsupported-versus-free-name distinction.

No losing pin is changed to an unenforceable Checked outcome on this branch.
The pending changes depend on closures and are explicitly coordinator-owned.
