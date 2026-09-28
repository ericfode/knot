# Bare family names

These seven fixtures pin review round 1's confirmed finding: a family whose
parameters are all leading quantities was silently instantiated at `&1` when
written without `<..>`. The pinned seed fills quantities only inside an explicit
`Name<..>` application; a bare name is not a family instance.

`expectations.json` freezes one seed-valid control and six seed rejections,
three entry calls and the seed's reason, `expected : a family instance (write
Name<..>)`. Every rejection must report `Invalid check type-arity` in all Knot
phases and preserve an existing artifact.

| Case | Position of the bare name |
| --- | --- |
| `bare-family-parameter` | parameter type |
| `bare-family-field` | constructor field type |
| `bare-family-annotation` | local binding annotation |
| `bare-family-result` | function result type |
| `bare-family-static` | erased static type argument |
| `bare-two-quantity-family` | parameter type of a two-quantity family |
| `explicit-quantity-family` | control: explicit `Bit<&1>` result and parameter |

Before the repair, Knot's checker printed `Checked` for all seven. The
expectations were written from the seed and literal review before the
repair; none comes from Knot output.

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-generics/bare-families/regen.py
```
