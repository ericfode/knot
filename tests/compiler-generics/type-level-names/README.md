# Type-level definition names

These eleven fixtures pin review round 3's type-level-definition finding. The
pinned seed accepts a zero-arity definition that computes a type, `def T() ->
Type: Flag`, named as a type in a family field or in a signature. Knot rejects
every type-level definition as `Unsupported check type-level-definition` when it
checks the definition's own signature. The catalog resolves family fields
before any signature, and signatures in declaration order. A field, or an
earlier signature, therefore met the name first and reported `Invalid check
unknown-type`.

By literal review, Knot must report `Unsupported check type-level-definition`
for every seed-valid case, in every phase, with an existing artifact
preserved. This holds wherever the definition is declared.

| Case | Name position | Declared | Seed |
| --- | --- | --- | --- |
| `definition-field-later` | generic field `Box{value: T}` | after | `On{}` |
| `definition-field-earlier` | generic field, value unboxed by `main` | before | `On{}` |
| `definition-monomorphic-field` | monomorphic field `W{value: T}` | before | `On{}` |
| `definition-monomorphic-field-generic` | the same, beside a generic family | before | `On{}` |
| `definition-monomorphic-field-later` | monomorphic field | after | `On{}` |
| `definition-parameter-forward` | parameter and result of `id(x: T) -> T` | after | `On{}` |
| `definition-argument-forward` | argument of `Box<T>` in a parameter | after | `On{}` |
| `definition-nested-field` | argument of `Box<T>` in a field | after | `On{}` |
| `definition-forward-mismatch` | `f(x: T) -> Flag` returns `x` | after | rejects: opaque `T` is not `Flag` |
| `value-definition-field` | field names `one() -> Flag` | before | rejects: `Flag` is not a type |
| `unknown-type-control` | field names `Missing` | none | rejects: not a defined name |

The monomorphic-field books have no generic syntax. Their typed-result
definition routes them to the generic checker.

The seed rejections bound the rule. Knot never accepts the two definition
names; it reports them Unsupported `type-level-definition`, because it does not
evaluate definitions named as types. The undeclared name stays `Invalid check
unknown-type`.

Before the repair, the native check CLI of `90feb09` printed `Invalid check
unknown-type` at the name for all eleven fixtures. `expectations.json` freezes
eight seed-valid programs, three seed rejections and eight `main` calls.
None of its content comes from Knot.

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-generics/type-level-names/regen.py
```
