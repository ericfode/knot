<!-- prechecks packet v1; rule=passages-agree; increment=vm-spec; head=d2fe0f2048fb; base=none; builder=manual-excerpt@47dbd98ca1c7; sources: vm/SPEC.md@d2fe0f20 sha256=8766740dd99fadc82c5e393412a0b972bdffdcdb3de02162ce8dcbb2b86fa508; vm/SPEC.md@d2fe0f20 sha256=8766740dd99fadc82c5e393412a0b972bdffdcdb3de02162ce8dcbb2b86fa508 -->
# Claim
`vm/SPEC.md:333-336` (section 6, intrinsics)

>   its code word unchanged; any other constructor allocates an Object that takes the
>   operands. Return the result.
> - Intrinsic: compute the prim (§9), allocating its result, then drop the operands
>   in operand order. Return the result.

# Evidence
`vm/SPEC.md:470-476` (section 9, the append primitive)

```
  470    `reverse`, `length` and `is_empty` observe the list, and `U32.show`/`Nat.show`
  471    give unsigned decimal without leading zeros except `0`.
  472  
  473  **Allocation order.** A String result is allocated last cell first: `append(a,b)`
  474  copies `a`'s cells onto `b` (moved) from `a`'s last character to its first;
  475  `reverse(a)` allocates from `a`'s first character; `show` from its last digit. A
  476  Big result is allocated before the operands are dropped. Prims without a golden
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
