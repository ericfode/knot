<!-- prechecks packet v1; rule=claim-holds-against-evidence; increment=modules; head=bbff6371cf5a; base=92de61cea385; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/SPEC.md@bbff6371 sha256=c21ab5715e866e220483147bfa1a0ca5bd51d898d6efe017b13e17d59ce4a422; src/check-cli.bend@bbff6371 sha256=c9dba4cf5a76d64ecc8aea9ad1812382e5f50c9a4d943c2ac10d40fd3043acb2 -->
# Claim
src/SPEC.md:239-240 (section: Single-file deltas (accepted by the coordinator, 2026-09-28)) - verbatim text:

> - A let or arm binder named like an earlier constructor reports
> - The declaration-order binder walk is bounded at 65,536 work steps
>   (`Exhausted check`, not expected under the 65,536-byte source cap).

# Evidence
Evidence: the declarations that use the stated number, at head.

`src/check-cli.bend:49-55` (declaration using the budget 65536)
```
   49  def configure(+path: String, chars: Maybe<&2,U32>, depth: Maybe<&2,U32>) -> IO(Unit):
   50    match chars depth:
   51      case Some{+c} Some{+d}:
   52        S.choose(IO(Unit),Bool.and(U32.is_le(c,65536),U32.is_le(d,4096)),u =>
   53          open_source(path,U32.to_nat(c),U32.to_nat(d)),u =>
   54          IO.die(Unit,5,"HostFailure\targuments\tbudget-out-of-range"))
   55      case _ _: IO.die(Unit,5,"HostFailure\targuments\tinvalid-budget")
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
