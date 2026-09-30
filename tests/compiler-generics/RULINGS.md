# Proposed assertion rulings — review round 5

These proposals cover every row of ASSERTION-CHANGES.md and all 24 boundary
pins identified by the last review. They are not an independent coordinator
approval. Existing seed observations and agreed values are unchanged. D4 and
D7 decide sound source classifications; D21 preserves law obligations; D26
applies only after the combined tree actually checks a colliding form.

| Ledger row | Proposed ruling | Evidence / rule |
| --- | --- | --- |
| 1 — original generic fixture | keep | D4/D7: its unchanged seed accepts and returns Box{On{}}; the accepted generic extension supersedes the old Unsupported prefix. Preserve enum-profile refusal and its artifact. Already separately authorized. |
| 2 — phase/prefix mechanics | keep | D7: parse/check phase records are successful records; evaluator values remain exact seed values. Only failed compilation must preserve old bytes; a successful build must validate fresh Wasm. The harness enforces those distinct obligations. Mechanics remain a coordinator confirmation. |
| 3 — function-parameter witness | re-derive at closures integration | D26: seed accepts in both lanes and closures checks it. This later-merging increment owns its supersession and the two affected mutants; MERGE-WITH-CLOSURES.md gives the exact dependency. |
| 4 — six classify-2 application pins | keep pending D26 integration | Three seed-valid applications must not remain Invalid (D4). Three incomplete applications remain refusals; this parser does not validate the remainder beyond its Unsupported boundary. The prior separate authorization and original seed bytes stay. |
| 5 — law restatements and touching spans | keep; retain future acceptance obligations | D7: generic-header spans now describe the glued Type> source tokens that the seed accepts. The filled proof still quantifies over its declared domain. D21: relocating six law/proof blocks preserves their statements verbatim. The prior coordinator explicitly allowed restatement/retirement of the obsolete Unsupported application laws; it does not establish general parser soundness or a general application-acceptance theorem. Those remain open, never discharged by a boundary law. |
| 6 — classification mutants and witness mechanics | keep | D7: additive independent route mutants retain source hashes and unmutated outcomes; seed-valid forms cannot be demoted to Invalid. No existing positive value assertion is weakened. The current seven kills on nine frozen witnesses remain required. Confirm the two formerly unconfirmed route mutants at merge. |
| 7 — frontend definition census | keep historical 47/48; re-derived current count 49 (D7) | The original six added helpers explain 41→47. The shared adjacency guard added exactly parse.adjacent, giving 48. Review round 1 adds only parse.layout_head, giving 49. Both mechanical amendments are isolated commits citing D7; independent pinned-seed enumeration and the census agree. This counts implementation reachability, not capability. REVIEW-R1.md records the current enumeration. |
| 8 — recursion Wasm evidence test | keep as observed fixture evidence | Both frozen quantity-parity and seq-parity fixtures run in the evaluator and actual Node Wasm in both lanes. D7 keeps exact seed values. The evidence adapter calls the stage observed-in-successful-fixtures, not fully qualified; it excludes exhaustion and mere Built outcomes. Coordinator ratification remains required. |
| 9 — generated recursion.wasm inventory | keep the observation; do not promote qualification | Same independent observations as row 8. src/SPEC.md still says general recursion Wasm qualification is separate. The campaign-level interpretation remains a coordinator decision; refreshing inventory does not waive the recursion owner's obligations. |

## Boundary pins

The table proposes a disposition for each fixture, using its fixed seed
observation. A seed cannot supply Knot's diagnostic spelling. Code-only and
formerly loose spellings therefore remain literal coordinator-review items;
there is no reason to invent a seed-derived diagnostic or weaken a valid
agreement. The full gate replays every seed observation unchanged.

| Pin | Seed evidence | Proposal | Basis |
| --- | --- | --- | --- |
| `boundaries/meet-right-identity` | accepted | keep | D7: preserve seed agreement. |
| `boundaries/meet-left-identity` | accepted | keep | D7: preserve seed agreement. |
| `boundaries/meet-right-zero` | accepted | keep | D7: preserve seed agreement. |
| `boundaries/meet-left-zero` | accepted | keep | D7: preserve seed agreement. |
| `boundaries/prefix-overrides-quantity` | accepted | keep | D7: preserve seed agreement. |
| `boundaries/prefix-overrides-undefined` | accepted | keep | D7: preserve seed agreement. |
| `boundaries/prefix-forward-explicit` | a quantified datatype after + | keep | D4/D7: seed rejects; preserve refusal and the reviewed reason. |
| `boundaries/prefix-forward-short` | a quantified datatype after + | keep | D4/D7: seed rejects; preserve refusal and the reviewed reason. |
| `boundaries/prefix-needs-quantifier` | a quantified datatype after + | keep | D4/D7: seed rejects; preserve refusal and the reviewed reason. |
| `boundaries/boxed-live-type` | accepted | keep | D4: accepted form must remain Unsupported until this lane checks it. |
| `boundaries/boxed-live-quant` | accepted | keep | D4: accepted form must remain Unsupported until this lane checks it. |
| `boundaries/type-valued-result` | accepted | keep | D4: accepted form must remain Unsupported until this lane checks it. |
| `boundaries/monomorphic-kind` | accepted | keep | D7: preserve seed agreement. |
| `boundaries/value-indexed-family` | accepted | keep | D4: accepted form must remain Unsupported until this lane checks it. |
| `boundaries/constructor-local-type` | accepted | keep | D4: accepted form must remain Unsupported until this lane checks it. |
| `dispatch-boundaries/nested-erased-type` | accepted | keep | D4: accepted form must remain Unsupported until this lane checks it. |
| `dispatch-boundaries/local-erased-quantity` | accepted | keep | D4: accepted form must remain Unsupported until this lane checks it. |
| `dispatch-boundaries/unannotated-erased-quantity` | accepted | keep | D4: accepted form must remain Unsupported until this lane checks it. |
| `dispatch-boundaries/unannotated-erased-type` | accepted | keep | D4: accepted form must remain Unsupported until this lane checks it. |
| `dispatch-boundaries/empty-type-application` | a term | keep | D4/D7: seed rejects; preserve refusal and the reviewed reason. |
| `dispatch-boundaries/monomorphic-type-application` | Flag with 0 parameters; Flag<Flag> | keep | D4/D7: seed rejects; preserve refusal and the reviewed reason. |
| `dispatch-boundaries/generic-local-erased-type` | accepted | keep | D4: accepted form must remain Unsupported until this lane checks it. |
| `dispatch-boundaries/generic-unannotated-erased-type` | accepted | keep | D4: accepted form must remain Unsupported until this lane checks it. |
| `dispatch-boundaries/inferred-erased-type` | accepted | keep | D4: accepted form must remain Unsupported until this lane checks it. |

`monomorphic-type-application` is seed-invalid but this monomorphic lane does
not check applied type expressions. Unsupported is therefore the precise
sound verdict this lane can establish (D4); Invalid type-arity would require
that missing check. For the three formerly loose type-level-term pins, the
seed accepts a type/quantity value and this profile cannot evaluate local static
computation: Unsupported is required, with spelling a literal review item.
The three quantity-prefix and one empty-argument codes name seed-rejected
forms; keep the codes provisionally, or have the coordinator adopt the original
class-only convention in a separate reviewed amendment.

`later-family-binding`: keep as a scrutinee control, and remove it from the
pattern-order rejection count. The actual seed's first diagnostic is unknown
Box; Knot refuses the local scrutinee before resolving the pattern. It therefore
proves no constructor-visibility property. Four other frozen negatives exercise
the order rule; the unchanged binding fixture still guards rejection.

## Applied versus pending

Applied: D4/D7 term-token refusal and abstract host-signature refusal, each after
its separate freeze; D9/D21 verbatim subject relocation; the mechanical current
census count; preservation of all original agreement values and source hashes.

Pending coordinator decisions: confirmation of rows 2, 5, 6, 7–9 and the literal
spellings described above; the separate D26 pin/mutant reconciliation after
closures; main integration and shared receipt refresh. The branch implements
no unavailable closure capability and makes no new recursion-qualification claim.
