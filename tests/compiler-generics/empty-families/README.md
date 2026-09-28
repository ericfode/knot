# Empty families

These seven fixtures pin review round 2's empty-datatype finding. The pinned
seed accepts a datatype without constructors, the domain of absurd
elimination (`match n:` with no arms). Knot reported `Invalid check
empty-datatype` for all seven. Main's checker reported `Unsupported parse
generic-datatype` for the books with generic syntax, so the generics header
change had exposed the rule; the monomorphic books were already Invalid on
main.

Knot represents no empty family and checks no zero-arm match. By literal
review its requirement is `Unsupported check empty-datatype` in every phase,
with an existing artifact preserved, in both the generic and the monomorphic
catalog.

| Case | Declaration | Checker |
| --- | --- | --- |
| `empty-generic-absurd` | `Never<-A: Type>` and an absurd `match n:` | generic |
| `empty-generic-family` | `Void<-A: Type>` | generic |
| `empty-quantity-family` | `Void<a> is Kind(a)` | generic |
| `empty-kind-family` | `Void is Kind(&2)` | generic |
| `empty-type-generic-book` | monomorphic `Void is Type` beside a generic family | generic |
| `empty-type` | `Void is Type` | monomorphic |
| `empty-data-absurd` | `Void is Data` and an absurd `match e:` | monomorphic |

Before the repair (native check CLI of `f7c98b9`) every case printed
`Invalid check empty-datatype` at the declaration name (`40:45:5:5` for
`Never`, `40:44:5:5` for `Void`). `expectations.json` freezes seven seed-valid
programs and their seven `main` calls; none of its content comes from Knot.

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-generics/empty-families/regen.py
```
