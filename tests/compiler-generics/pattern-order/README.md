# Constructor pattern order

These six fixtures pin review round 3's two pattern-order findings. The
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
| `earlier-family-forward-uses` | `case Box{v}` below the declarations | none (forward result type and `Box{x}` above) | `On{}`; `round` is the identity |
| `earlier-family-nested` | the nested patterns, below the declarations | none | `On{}` |

The same order rule is missing from the monomorphic checker. A book with no
generic syntax and a `case On{}` above `type Flag` is `Checked` on main and on
this branch; the seed rejects it. The review's `f7` and `late-mono` probes
show this. That checker's owner holds that case. It is recorded here rather
than pinned, because the generics gate would fail on it.

Before the repair, the native check CLI of `d7fba74` printed `Checked` for all
six fixtures. `expectations.json` freezes two seed-valid programs, four seed
rejections and four entry calls. None of its content comes from Knot.

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-generics/pattern-order/regen.py
```
