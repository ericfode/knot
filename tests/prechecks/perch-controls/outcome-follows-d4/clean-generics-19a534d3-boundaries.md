<!-- prechecks packet v1; rule=outcome-follows-d4; increment=generics; head=19a534d33af4; base=481bb3188010; builder=scripts/prechecks/packets@3a2ef420dff1; sources: research/compiler-generics/SPEC.md@19a534d3 sha256=d36c8f20187a7a4cd58edbca0aaae383255c0393278d1e24e3226cb20b735cad -->
# Claim
Outcome claims this branch changed:

research/compiler-generics/SPEC.md:66-69 (section: Boundaries) - verbatim text:

> Unsupported: type-returning definitions and aliases, local type or quantity
> bindings, live type or quantity parameters and arguments, value-indexed
> families, constructor-local type parameters, type-variable application, pair
> type sugar, function types and templates.

research/compiler-generics/SPEC.md:71-73 (section: Boundaries) - verbatim text:

> - A type argument followed by anything but `,` or `>` is a term, as in the
>   value-indexed application `Tag<On{}>`: `Unsupported parse term-argument`
>   (law `term_argument`). Empty type-argument lists are Invalid, like the seed.

research/compiler-generics/SPEC.md:74-76 (section: Boundaries) - verbatim text:

> - A type argument followed by anything but `,` or `>` is a term, as in the
> - A family without constructors, the domain of absurd elimination, is
>   `Unsupported check empty-datatype` in both catalogs (laws `empty_family`
>   and `empty_datatype`).

# Evidence
Decision rows (verbatim, docs/COMPILER-CAMPAIGN.md):

| D4 | The compile path covers the full implementation language. The checker grows alongside, never silently accepting what it cannot check. A form it cannot check is reported `Unsupported`, never `Invalid`, and never passed through unchecked. | Keeps Knot's identity as a checked compiler while it grows. |
| D16 | VM fuel counts calls and invokes, independent of eval.bend's transition count. Exhausted kinds are 1 (fuel), 2 (heap) and 3 (frame region). | Keeps superinstructions and later optimization possible without changing observable budgets. |

research/compiler-generics/SPEC.md:64-81 (section: Boundaries):

> ## Boundaries
>
> Unsupported: type-returning definitions and aliases, local type or quantity
> bindings, live type or quantity parameters and arguments, value-indexed
> families, constructor-local type parameters, type-variable application, pair
> type sugar, function types and templates.
>
> - A type argument followed by anything but `,` or `>` is a term, as in the
>   value-indexed application `Tag<On{}>`: `Unsupported parse term-argument`
>   (law `term_argument`). Empty type-argument lists are Invalid, like the seed.
> - A family without constructors, the domain of absurd elimination, is
>   `Unsupported check empty-datatype` in both catalogs (laws `empty_family`
>   and `empty_datatype`).
>
> Laws in `types-LAWS.bend`, `type-erasure-LAWS.bend`, `catalog-LAWS.bend`,
> `check-LAWS.bend` and `LAWS.bend` are proved; corpus agreement is finite differential evidence, not
> a checker-soundness or compiler-correctness theorem.
>

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
