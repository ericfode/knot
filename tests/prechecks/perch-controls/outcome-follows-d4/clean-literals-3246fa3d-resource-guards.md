<!-- prechecks packet v1; rule=outcome-follows-d4; increment=literals; head=3246fa3d7376; base=f84d83ef5fb2; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/SPEC.md@3246fa3d sha256=489bd678687f3c89de0a27ed86e6a229d91699796fb290e9f20de9dc82b91f72 -->
# Claim
Outcome claims this branch changed:

src/SPEC.md:463-465 (section: Primitives and literals: `knot-literals-wasm-1`) - verbatim text:

> It has no
> reclamation. Resource guards are Exhausted, not Invalid; other runtime traps
> are HostFailure.

src/SPEC.md:464-465 (section: Primitives and literals: `knot-literals-wasm-1`) - verbatim text:

> Resource guards are Exhausted, not Invalid; other runtime traps
> are HostFailure. The profile must be selected explicitly in the Node adapter.

# Evidence
Decision rows (verbatim, docs/COMPILER-CAMPAIGN.md):

| D4 | The compile path covers the full implementation language. The checker grows alongside, never silently accepting what it cannot check. A form it cannot check is reported `Unsupported`, never `Invalid`, and never passed through unchecked. | Keeps Knot's identity as a checked compiler while it grows. |
| D16 | VM fuel counts calls and invokes, independent of eval.bend's transition count. Exhausted kinds are 1 (fuel), 2 (heap) and 3 (frame region). | Keeps superinstructions and later optimization possible without changing observable budgets. |

src/SPEC.md:303-315 (section: Outcomes and budgets):

> ## Outcomes and budgets
>
> Return stable phase/code diagnostics with source offsets where available:
> `Invalid`, `Unsupported`, `Exhausted`, `HostFailure`, or `InternalFailure`.
> `Built` means a complete checked module has been emitted. The evaluator has a
> separate result and exhaustion outcome. A host timeout is exhaustion and cannot
> be relabeled as an invalid program. Stale output files cannot count as emission.
>
> The executable [contract manifest](CONTRACT.json) fixes source, parser, checker,
> emitter-depth, evaluator-transition and output-byte budgets. Exhaustion is
> inconclusive. The compiler and evaluator have separate commands and outcomes;
> emission never calls the evaluator.
>

src/SPEC.md:316-332 (section: Current checker bounds):

> ## Current checker bounds
>
> `check-cli.bend path [character-budget checker-depth]` defaults to 65,536 source
> characters and depth 512; parser depth is 512. Both frontend and checker depth
> are recursion-depth bounds, not total work counters. Overrides permit checker
> depth 0 through 4,096 and source budgets 0 through 65,536. The catalog allows
> 256 types, 256 functions, 256 constructors per type, 256 fields per constructor and 256 parameters per
> function; lexical levels are limited to 4,096 per branch scope. Exceeding any
> of these bounds is exhaustion. Catalog passes and environment/set scans are
> structural list traversals bounded by these limits and the source cap. Lookup
> and affine-set merging are deliberately simple linear/quadratic algorithms.
> No performance claim or general checker-soundness proof is made.
>
> The checker CLI prints a resolved-term observation and emits no executable.
> Its `Checked` result is not `Built`. The separate compiler/evaluator commands
> below execute the rest of this profile.
>

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
