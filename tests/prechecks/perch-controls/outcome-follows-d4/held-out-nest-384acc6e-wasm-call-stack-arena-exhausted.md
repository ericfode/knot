<!-- prechecks packet v1; rule=outcome-follows-d4; increment=nest; head=384acc6e83c5; base=cc9f2fd23d59; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/SPEC.md@384acc6e sha256=a11dba1814b3c8e7464576926218853acbe7b4f83159aeddfab086429bb487d8 -->
# Claim
Outcome claims this branch changed:

src/SPEC.md:259-261 (section: Fielded Wasm profile: `knot-fields-wasm-1`) - verbatim text:

> During export invocation, a call-stack `RangeError` reports
> `Exhausted<TAB>wasm<TAB>call-stack` (exit 4). For domain-valid calls in the fields profile, the arena's
> `unreachable` reports `Exhausted<TAB>wasm<TAB>arena-overflow` (exit 4).

# Evidence
Decision rows (verbatim, docs/COMPILER-CAMPAIGN.md):

| D4 | The compile path covers the full implementation language. The checker grows alongside, never silently accepting what it cannot check. A form it cannot check is reported `Unsupported`, never `Invalid`, and never passed through unchecked. | Keeps Knot's identity as a checked compiler while it grows. |
| D16 | VM fuel counts calls and invokes, independent of eval.bend's transition count. Exhausted kinds are 1 (fuel), 2 (heap) and 3 (frame region). | Keeps superinstructions and later optimization possible without changing observable budgets. |

src/SPEC.md:273-285 (section: Outcomes and budgets):

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

src/SPEC.md:286-306 (section: Current checker bounds):

> ## Current checker bounds
>
> `check-cli.bend path [character-budget checker-depth]` defaults to 65,536 source
> characters and depth 512; parser depth is 512. Both frontend and checker depth
> are recursion-depth bounds, not total work counters. Overrides permit checker
> depth 0 through 4,096 and source budgets 0 through 65,536. The catalog allows
> 256 types, 256 functions, 256 constructors per type, 256 fields per constructor and 256 parameters per
> function; lexical levels are limited to 4,096 per branch scope. Exceeding any
> of these bounds is exhaustion. Each expanded source match has 4096 matrix
> visits, including leaves and empty remainders. `Expansion` returns the unused
> counter from each positive branch to its negative branch. The counter is never
> divided; the bound covers total expansion separately from recursion depth. Catalog passes and
> environment/set scans are structural list traversals bounded by the catalog
> limits and source cap. Lookup
> and affine-set merging are deliberately simple linear/quadratic algorithms.
> No performance claim or general checker-soundness proof is made.
>
> The checker CLI prints a resolved-term observation and emits no executable.
> Its `Checked` result is not `Built`. The separate compiler/evaluator commands
> below execute the rest of this profile.
>

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
