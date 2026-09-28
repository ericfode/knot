# Marked quantity binders

These nine fixtures pin review round 3's marked-binder finding. An unmarked
bare binder in a parameter list, `def pick(a, x: Flag)`, is an erased quantity
parameter, and the pinned seed accepts it. A marked bare binder, `+a,` or
`-a,`, is a different matter: the seed reads the mark as the start of `name:
Type` and rejects the `,` where it expects `:`. Knot's type parser took the
bare-binder branch without looking at the mark. It turned `+a` and `-a` into
erased quantities, checked and compiled the book, and returned `On{}` from
both the evaluator and Wasm.

By literal review, Knot must reject each marked binder as `Invalid parse
parameter`, at the `,` the seed reports: a parameter missing its type. Each
unmarked twin agrees with the seed in the evaluator and in Node Wasm.

| Case | Binder | Position | Seed |
| --- | --- | --- | --- |
| `marked-reusable-binder` | `+a` | `def pick`, no generic family | rejects: expected `:` |
| `marked-erased-binder` | `-a` | `def pick`, no generic family | rejects: expected `:` |
| `unmarked-binder` | `a` | `def pick`, no generic family | `On{}` |
| `marked-reusable-function` | `+a` | `def head` over `Seq<a,A>` | rejects: expected `:` |
| `marked-erased-function` | `-a` | `def head` over `Seq<a,A>` | rejects: expected `:` |
| `unmarked-function` | `a` | `def head` over `Seq<a,A>` | `On{}` |
| `marked-reusable-header` | `+a` | `type Box<+a, -A: Kind(a)>` | rejects: expected `:` |
| `marked-erased-header` | `-a` | `type Box<-a, -A: Kind(a)>` | rejects: expected `:` |
| `unmarked-header` | `a` | `type Box<a, -A: Kind(a)>` | `On{}` |

Constructor fields keep their earlier rule, `Unsupported parse
bare-quantity-field`, for a bare field with or without a mark.

Before the repair, the native check CLI of `287a624` printed `Checked` for all
nine fixtures. `expectations.json` freezes three seed-valid programs, six
seed rejections and three `main` calls. None of its content comes from Knot.

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-generics/marked-binders/regen.py
```
