# Constructor pattern order

These eight fixtures pin review round 3's two pattern-order findings. The
pinned seed resolves a constructor pattern only against the datatypes
declared above it. A `case Box{v}` above `type Box` is an error: "a declared
constructor (unknown: Box)". Type names and constructor expressions still
resolve in the whole book. The generic checker resolved patterns against the
whole book, and so checked, evaluated and compiled programs that the seed
rejects. This applied to a monomorphic enum pattern too, once a later generic
family routed the book to the generic checker.

By literal review, Knot must reject each such pattern as `Invalid check
unknown-constructor` at its name, and must agree with the seed when every
pattern follows its declaration.

| Case | Pattern | Declared later | Seed |
| --- | --- | --- | --- |
| `later-family-parameter` | `case Box{value}` on a generic parameter | `Box` | rejects: unknown `Box` |
| `later-family-unbox` | `case Box{v}` in the review's `unbox` | `Flag`, `Box` | rejects: unknown `Box` |
| `later-family-nested` | `case Box{v}` inside a `case On{}` arm | `Box` | rejects: unknown `Box` |
| `later-enum-generic-book` | `case Off{}` in `flip` | `Flag`, then a generic `Box` | rejects: unknown `Off` |
| `later-family-binding` | `case Box{v}` on a let-bound `Box` | `Flag`, `Box` | rejects: unknown `Box` |
| `earlier-family-forward-uses` | `case Box{v}` below the declarations | none (forward result type and `Box{x}` above) | `On{}`; `round` is the identity |
| `earlier-family-nested` | the nested patterns, below the declarations | none | `On{}` |
| `earlier-family-forward-binding` | `case Box{v}` below the declarations; a forward `b: Box<Flag> = Box{x}` above them | none | `On{}`; `round` is the identity |

The same order rule is missing from the monomorphic checker. A book with no
generic syntax and a `case On{}` above `type Flag` is `Checked` on main and on
this branch; the seed rejects it. The review's `f7` and `late-mono` probes
show this. That checker's owner holds that case. It is recorded here rather
than pinned, because the generics gate would fail on it.

The binding variant is rejected before its pattern is resolved. The seed
never lets a match scrutinize a local binder ("a match cannot scrutinize a
local binder"), whatever the order. Knot reports that scrutinee `Invalid check
unmatchable-binder`, so this variant does not depend on the order rule. The
binding variant and its control were added after the repair, at the review's
request. The pre-repair native check CLI of `d7fba74` printed `Checked` for
the first six fixtures. `expectations.json` freezes three seed-valid programs,
five seed rejections and seven entry calls. None of its content comes from
Knot.

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-generics/pattern-order/regen.py
```
