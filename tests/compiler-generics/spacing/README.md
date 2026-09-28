# Token spacing

These eighteen fixtures pin one class of seed rejection that the round-3
sweep found. The pinned seed lexes three generic forms as glued tokens: the
quantity literal `&2`, the meet `<&>` and, in most lists, a closing `>`
that touches the type before it. Knot's lexer emits every symbol as its own
token and drops the spaces between them. The generic parser therefore read
`& 2` as `&2`, `< & >` as `<&>` and `Flag >` as `Flag>`, and checked,
evaluated and compiled books the seed rejects. Main reported all eighteen
books Unsupported (`parse generic-datatype`, `kind` or
`bare-quantity-field`).

By literal review, Knot reports a gap inside a glued token as `Unsupported
parse spacing`, and agrees with the seed when every gap lies outside one. The
seed's closing-`>` rule depends on position. It accepts a gap before the `>`
of a single-argument list, and rejects the same gap after a later argument or
a header type. Knot does not reproduce that rule: any gap before a `>` that
closes a type-argument list or a header parameter type is Unsupported (D4).
The four seed-valid single-argument forms are pinned Unsupported so that
the demotion is visible.

| Case | Form | Seed | Knot |
| --- | --- | --- | --- |
| `quantity-gap-argument` | `Seq<& 2,Flag>` | rejects: expected a name, `2` | Unsupported |
| `quantity-gap-kind` | `Kind(& 2)` | rejects: expected a name, `2` | Unsupported |
| `quantity-gap-term` | `pick(& 2, On{})` | rejects: expected a name, `2` | Unsupported |
| `meet-gap` | `Kind(a < & > b)` | rejects: expected a name, `>` | Unsupported |
| `meet-gap-close` | `Kind(a <& > b)` | rejects: expected a name, `>` | Unsupported |
| `meet-gap-open` | `Kind(a < &> b)` | rejects: expected a name, `>` | Unsupported |
| `close-gap-parameter` | parameter `Seq<&2,Flag >` | rejects: expected a term, `)` | Unsupported |
| `close-gap-result` | result `Seq<&2,Flag >` | rejects: expected a term, `:` | Unsupported |
| `close-gap-nested` | `Seq<&2,Seq<&2,Flag> >` | rejects: expected a term, `)` | Unsupported |
| `close-gap-header` | header `type Box<-A: Type >` | rejects: `is` cannot head a term | Unsupported |
| `single-close-parameter` | parameter `Box<Flag >` | `On{}` | Unsupported |
| `single-close-result` | result `Box<Flag >` | `On{}` | Unsupported |
| `single-close-binding` | binding `b: Box<Flag >` | `On{}` | Unsupported |
| `single-close-nested` | `Box<Box<Flag> >` | `On{}` | Unsupported |
| `gaps-around-arguments` | `Seq <&2,Flag>`, `Seq< &2, Flag>` | `On{}`; `both` is the identity | agrees |
| `gaps-around-quantities` | `Kind( &2 )`, `pick( &2 , x)` | `Off{}`; `swap` is the identity | agrees |
| `gaps-around-binders` | `type Seq<a >`, `Box< - A: Type>`, `open(- A: Type, ..)` | `On{}` | agrees |
| `glued-meets` | `Kind(a <&>b)`, `Kind(a<&>b)` | `On{}`; `keep` is the identity | agrees |

A bare header binder followed by a gap and `>` (`type Seq<a >`) is
seed-valid. It is not a type expression, so it is not a closing gap.

Two monomorphic forms of the same class stay with the frontend's owner:
`On {}` and `def main() - > Flag`. Main and this branch both report them
`Checked`, and the seed rejects them. They are recorded here, not pinned,
because the generics gate would fail on them.

Before the repair, the native check CLI of `6086dfa` printed `Checked` for
all eighteen fixtures. `expectations.json` freezes eight seed-valid programs,
ten seed rejections and fourteen entry calls. None of its content comes from
Knot.

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-generics/spacing/regen.py
```
