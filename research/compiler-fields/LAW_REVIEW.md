# Structural term review packet

Profile `knot-structural-terms-1`, pinned Bend 2.0.29 at
`574b6d39a235b539eb19a5c532993a0abb3d11ad`. This increment checks and independently
evaluates finite structural values. It does not implement an owning heap,
structural recursion or Wasm/GPU field lowering.

## Public observations and implementation

`check.check(depth,syntax) -> Result<Error,Book>` checks every body after complete
catalog resolution. Constructors carry resolved field signatures and checked
arguments in declaration order. `patterns.quantity(field,parent,mark)` produces
0 if either demand is erased, otherwise 2 if declaration, parent or explicit
promotion requires reuse, otherwise 1. Inputs come from validated quantities
0..2; a promoted live field must have Data type. Affine Data may move once into
a reusable field; the caller's use is not multiplied by the callee's demand.

`patterns.branch` consumes the match position and introduces stable lexical
identities for the fields. `Scope.open` is an ordered list, independent of ID
allocation. Matching drops earlier match eligibility, puts exposed fields before
later parameters, and does not drop values merely because they become
unmatchable. Field binders can shadow earlier names; a global constructor name
cannot be used as a bare binder. A local let closes the match frontier.

A matched parent has a reconstruction term whose references use field IDs.
`check.run(Rebuild)` looks up those IDs in the current scope and recursively
expands further refinements. It accounts for the live affine uses of the fields;
there is no extra owning parent alias. Sequential use sets must be disjoint;
alternative sets union. Branch-local field IDs are removed before returning
usage obligations to the outer scope. Nested source patterns and recursive calls
remain explicit Unsupported capabilities. Invalid bodies precede the emitter's
whole-book field capability rejection; no failed compiler invocation opens the
output artifact.

`eval.invoke(book,name,ordinals,fuel)` interprets checked terms using explicit
states and continuation frames. `Fields` evaluates live constructor arguments
left to right and skips erased arguments. Completed values reverse the local
accumulator once. `Unpack` walks declaration bindings while consuming only live
slots. The interpreter values are persistent Data trees. They model observations,
not physical ownership, memory reclamation or alias lifetime.

`eval.describe` returns a live-field projection. Full source-value printing can
differ from the seed: `Ghost{On{}}` with erased payload becomes `Ghost{}`. The
fixture records both explicit expectations. All other successful differential
value fixtures use enum results or non-erased structural trees. External ordinal
arguments only construct nullary values; fielded ordinals are HostFailure.

Inspection uses a worklist with at most 4096 transitions and 65,536 output
characters. Both limits fail explicitly as Exhausted inspect. This prevents
shared trees from expanding into unbounded successful output. A 24-level shared
binary tree is accepted by seed checking and Knot, then exhausts inspection;
no seed full-tree output or whole-value equivalence is claimed for that control.

## Domains, independent witnesses and coverage

The fixtures use inhabited Flag (Off/On), owned Box/Pair/Inner/Outer, Data trees
with Leaf, erased Ghost, and mixed-quantity Pack. No Empty parameter, unsafe
inhabitant, assumed axiom or contradictory precondition is introduced.

| Contract observation | Public witness | Additional evidence |
| --- | --- | --- |
| Construct, destructure and preserve values/order/types | open, reconstruct, multi-constructor, mixed-live-order | Seed interpreter; native/Bun evaluator; fixed checked-core slices |
| Quantity inheritance/promotion | data-parent, reusable-field, promote-field, constructor-promotion-once | Seed-positive controls; quantity helper laws |
| Affine ownership and reconstruction demand | affine-field-reuse, constructor-affine-reuse, parent-and-field, parent-twice | Intended seed consumed-more-than-once diagnostic; unchanged negative assertions |
| Erasure and type checking remain separate | erased-field-live/promote/typechecked, erased-forward versus live-forward | Exact error classes; 15/16 transition boundary; erasure laws |
| Stable identity under shadowing/refinement | duplicate-pattern-names, reconstruction-shadow, nested-reconstruction, field-then-parent-refinement | Seed values and canonical level/refinement slices |
| Ordered matching and branch use union | field-before-parameter versus parameter-before-field; sibling-order/reversed; branch-use-union | Frontier law; let-closes-frontier negative |
| Invalid shapes and incomplete coverage | constructor/pattern arity, constructor-type, field-missing-arm, constructor-name-binder | Intended seed phase diagnostics and Knot codes |
| Unsupported syntax/capabilities stay explicit | nested-pattern, nested-single-pattern, minus-pattern | First two accepted by seed; minus-pattern is a seed syntax error, not ownership evidence |
| Finite scopes and complete observation | level 4095/4096, inspection work zero, exact output capacity 0/1, shared-tree expansion | Explicit Exhausted; no partial success |
| Distinct host-domain failures | fielded ordinal, out-of-range tag, extra argument | Six native/Bun host observations |
| Field Wasm emission remains rejected | Every accepted structural book through actual compiler CLI with sentinel output | Output unchanged; enum regression still executes real Wasm |

The host harness only builds/invokes Bend, supplies fixed source inputs, compares
literal observations and records hashes. It implements no parser/checker/evaluator.
Seed results are independent language evidence. Checker acceptance alone is not
value equivalence. The independent evaluator shares the checked core with the
emitter but does not interpret Wasm instructions. There is no general refinement
relation between this model and an owning runtime yet.

## Laws and proof boundary

`src/fields-PROOF.bend` fills eleven new laws and imports the prior 23 filled laws.
Six properties quantify over substantive arbitrary inputs:

- An erased declaration stays erased for any parent/mark word.
- Stepping an erased field skips its arbitrary term and preserves remaining
  arguments, values, environment and continuation frames.
- Stepping an erased pattern preserves the entire live-slot list.
- Unpacking one value preserves its lexical identity, tail and prior environment.
- Completing a two-field accumulator preserves the two arbitrary values in
  declaration order, its type/tag, and continuation frames.
- Any nonterminal inspection request at zero work reports Exhausted inspect.

The other five are bounded/concrete normalizations: affine promotion, reusable
parent inheritance, a nonmonotone-ID frontier, and output capacity 0/1. The last
two quantify over irrelevant type metadata but remain concrete capacity witnesses.
The order law is two-element, not an arbitrary-list reversal theorem.

All 34 laws are filled and the complete proof entry has zero holes. This does
not prove checker soundness, subject reduction, arbitrary program equivalence,
heap ownership, total resource safety or complete specification adequacy.
Helper laws reach the actual interpreter transitions; public fixtures separately
exercise composition and observations.

## Mutations and hostile review

Nine parseable/type-correct mutants fail unchanged assertions:

1. Let explicit promotion make an erased field live: erased-field-promote becomes accepted.
2. Remove reconstructed parent demands: parent-twice becomes accepted.
3. Rebuild by display spelling: reconstruction-shadow returns the wrong Pair.
4. Put exposed fields after later parameters: field-before-parameter becomes invalid.
5. Omit accumulator reversal: mixed-live-order returns Off instead of On.
6. Forget reusable declaration demand: reusable-field becomes invalid.
7. Execute an erased field: erased-forward exhausts its independently accounted
   16-transition boundary instead of returning On. The seed program itself is valid.
8. Ignore inspection capacity: a one-character write succeeds at capacity zero.
9. Allow lexical ID 4096: the unchanged boundary observer returns Next 4097.

Every mutant's seed typecheck and actual discrepancy are retained. No timeout,
syntax error, missing dependency or build failure is a semantic kill. The host
rejects unexpected failure classes. Mutation expectations are never regenerated.

Hostile review targeted retaining a hidden owning parent, name-based reconstruction,
reversed compact slots, erased evaluation and exponential display expansion.
The named fixtures/mutants reject the first four; a bounded inspection worklist
addresses the fifth. Removing earlier match eligibility is deliberately separate
from dropping its value. The current implementation still uses finite list scans
and repeated reconstruction; no performance or asymptotic improvement is claimed.

## Results, trust and omissions

The gate passes 40 seed controls (39 interpreter/diagnostic runs plus one seed
check-only expansion control), 240 native/Bun checker/evaluator/compiler phase
observations, 36 checker/evaluator budget probes, six host probes, twelve
level/inspection observations and nine semantic mutants. Compiler rejection
preserves existing artifacts in all 80 source/lane cases. Regressions pass:
14 frontend fixtures, 49 checker fixtures, 16 declaration fixtures, and 25 actual
Wasm programs with 90 independent reference calls. Enum Wasm artifacts are unchanged.

The proof closure loads 22 files; checker, evaluator and compiler closures load
12, 13 and 15. Each loads the pinned Base's 42 foreign declarations and unsafe
Array.fork/Array.join. No new foreign/unsafe declaration is added. Emitted JS uses
IO.args, File.open/read/close and IO.print; the compiler also uses File.write_bytes.
Seed checking/normalization, primitive lowering and emitted runtime remain trusted.
Exact closure and artifact hashes are in receipts/trust.json.

Owned allocation, transfer/drop, stale handles, reclamation, recursive descent,
generic/dependent/closure/module support, source-generated GPU dispatch and
whole-compiler A2/A3 remain unimplemented. The runtime support plan records their
required witnesses; its proposed storage probes remain unrun. This packet is an
adversarial review of the present contract, not a completeness theorem.

## Frozen implementation hashes

The full input inventory is `tests/compiler-fields/receipts/fields.json`.

| File | SHA-256 |
| --- | --- |
| `src/core.bend` | `eea976a956241715c1056fdbe4b3f3c6b4e4734a85fa3feb488629c203d7e973` |
| `src/parse.bend` | `046b79f2cbc4153a10493e44e0e7ec2136bbb68487680832b91689a6f28b1217` |
| `src/patterns.bend` | `3d0a5429adb3c3a095ec7ee28534152cb7274510e226f41691af5f1c99ea4e67` |
| `src/scope.bend` | `1457a6c70081f3c31d7eda4277ceb662399c7e8f3c40be2312001ccf287bd51e` |
| `src/check.bend` | `131bf0f567ce65ba69eb6eff597bb13595116811e3884a1ca18f182ad47b07d2` |
| `src/eval.bend` | `8383011adbad891f6afcd8fd90f9bea6cffdf174c691721d66288a99793c8091` |
| `src/fields-LAWS.bend` | `19638d07537ea7d166f3660bfa0c462474d29d9108ef1b9be961fddf3950054c` |
| `src/fields-PROOF.bend` | `fd8014bac6ff7edc97bacecd54a36274bb5f823966f575a2c2b3a7a8f31a84a6` |
| `tests/compiler-fields/cases.json` | `e01efe8b37004ff02e655586c2427484a798cc0b61ad5c3359135726be6612ac` |
| `tests/compiler-fields/check.py` | `86667e25daac9e9be73cf8693c1ed699db08d5f03a8028d7c4d55999bddca393` |
