# Definition references

These seven fixtures pin review round 2's definition-reference finding. The
pinned seed accepts a bare reference to a zero-arity definition, `one`, as that
definition's value, in live and erased positions. Knot reported `Invalid
check free-name`: the shared rule `term_name` reclassified an unbound name as
Unsupported only when it named a datatype. Main reported `Unsupported parse
generic-datatype` for the books with generic syntax, so the generics header
change had exposed the rule; the monomorphic books were already Invalid on
main.

A definition used as a first-class value is outside Knot's first-order term
profile. By literal review Knot must report `Unsupported check def-reference`
for every seed-valid case, in every phase and in both checkers, with an
existing artifact preserved.

| Case | Reference | Checker | Seed |
| --- | --- | --- | --- |
| `def-reference-live` | `main` returns `one` | generic | `On{}` |
| `def-reference-erased` | `ghost(one, Off{})`, erased first argument | generic | `Off{}` |
| `def-reference-forward-erased` | `ghost(later(main), x)`, forward and erased | generic | `On{}` |
| `def-reference-monomorphic` | `main` returns `one` | monomorphic | `On{}` |
| `def-reference-erased-monomorphic` | `ghost(one, Off{})` | monomorphic | `Off{}` |
| `function-value-mismatch` | `main` returns the unary `id` | generic | rejects: `@x:Flag -> Flag` is not `Flag` |
| `free-name-control` | `main` returns the undefined `missing` | generic | rejects: not a defined name |

The two seed rejections bound the rule. Knot reports the function value
`Unsupported check def-reference` (never accepted; it does not type
definition references), and the undefined name stays `Invalid check
free-name`.

Before the repair (native check CLI of `f7c98b9`) all five seed-valid cases and
`function-value-mismatch` printed `Invalid check free-name` at the reference.
`def-reference-forward-erased` is the review's saved mutation-fuzz file
`fuzz-s7/m2277.bend`, unchanged. `expectations.json` freezes five seed-valid
programs, two seed rejections and five `main` calls; none of its content
comes from Knot.

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-generics/def-references/regen.py
```
