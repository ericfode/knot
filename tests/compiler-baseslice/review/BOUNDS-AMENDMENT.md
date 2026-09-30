# Seed-derived parameter-bound witness amendment

The repaired lexical checker sees the original parameter fixture's first binder
`N0`, then its later annotations `N0`. The pinned seed rejects the corresponding
two-parameter source with `expected : Type`, `observed : N0`. Treating that input
as a positive size-bound witness would reintroduce the confirmed shadowing defect.

Only the synthetic parameter **binder** names in
`tests/compiler-checker/bounds.bend` change from `N0`, `N1`, ... to `p0`, `p1`, ... .
Annotation names stay `N0`; quantities, list sizes, location tokens and every
boundary assertion in the immutable `tests/compiler-checker/check.py` stay
unchanged. The four expected `Done 256` / `Exhausted check budget` pairs retain
their meaning. The existing maximums stay 256 parameters, types, constructors
and functions. No test is weakened and no successful value moves.

Before the amendment, four seed witnesses were frozen in
`receipts/bounds-amendment.json`: the original shadowing pair is rejected, while
the renamed pair and the 256/257-parameter books check and run to `Yes{}` in
interpreted and native lanes. The 257 case demonstrates that Knot's limit is
resource exhaustion, not a seed-language rejection.

```sh
export BEND_NO_TELEMETRY=1
python3 -B tests/compiler-baseslice/review/bounds-oracle.py
```

The runtime bounds entry is then executed in both seed build lanes by the
unchanged checker gate. This amendment is committed separately from production
repairs, as required by D7 and the review-round instructions.
