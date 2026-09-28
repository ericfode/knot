# Value arguments

These five fixtures pin review round 2's blocking finding: a seed-valid
application of a value-indexed family to a constructor value, `Tag<On{}>`, was
reported `Invalid parse type-argument-separator`. The type grammar read `On` as
a type variable and then found `{` where it expected `,` or `>`. Main's checker
reported `Unsupported parse generic-datatype` for the same books, so the
generics header change had exposed the separator rule (D4).

The pinned seed checks and runs every fixture. Value-indexed families are
outside `knot-generics-1`, so Knot's requirement, by literal review, is
`Unsupported parse term-argument` in every phase, with an existing artifact
preserved.

| Case | Position of the term-shaped argument | Knot before the repair |
| --- | --- | --- |
| `value-argument-parameter` | parameter type `Tag<On{}>` | `Invalid parse type-argument-separator 89:90:8:18` |
| `value-argument-binding` | local annotation `t: Tag<On{}>` | `Invalid parse type-argument-separator 102:103:9:11` |
| `value-argument-result` | result type of `Tag<-f: Flag>` | `Invalid parse type-argument-separator 92:93:8:20` |
| `value-argument-live-result` | result type of `Tag<f: Flag>` | `Invalid parse type-argument-separator 91:92:8:20` |
| `value-argument-second` | second argument, `Mark<Flag, Off{}>` | `Invalid parse type-argument-separator 110:111:8:26` |

`expectations.json` freezes five seed-valid programs and their five `main`
calls. The expectations come from the seed and literal review; none comes
from Knot output. An empty `Name<>`, which the seed rejects, stays
`Invalid parse type-arguments` (`dispatch-boundaries/empty-type-application`).

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-generics/value-arguments/regen.py
```
