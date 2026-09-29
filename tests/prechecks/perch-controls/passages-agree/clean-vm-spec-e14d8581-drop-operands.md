<!-- prechecks packet v1; rule=passages-agree; increment=vm-spec; head=e14d8581dc12; base=none; builder=manual-excerpt@3a2ef420dff1; sources: vm/SPEC.md@e14d8581 sha256=775b305468384b9e8ec07490db7b51716e2d159635be1d9b3e3ab584923842ac; vm/SPEC.md@e14d8581 sha256=775b305468384b9e8ec07490db7b51716e2d159635be1d9b3e3ab584923842ac -->
# Claim
`vm/SPEC.md:358-362` (section 6, intrinsics)

>   its code word unchanged; any other constructor allocates an Object that takes the
>   operands. Return the result.
> - Intrinsic: compute the prim (§9), allocating its result, then drop the operands
>   in operand order, except an operand the prim moves into its result (§9), which
>   is neither dropped nor duplicated. Return the result.

# Evidence
`vm/SPEC.md:525-536` (section 9, prim ownership and the append primitive)

```
  525  **Ownership.** Every prim borrows its operands, and §6 drops them after the result
  526  is allocated, except for these moves, which consume the operand into the result:
  527  `String.append(a,b)` moves `b`, whose reference becomes the result's tail, and
  528  drops only `a`; `U32.to_nat`, `U32.from_nat`, `Char.from_u32` and `Char.to_u32`
  529  move their operand word, which is the result (a Big cell is reused, never copied
  530  or dropped). Golden `string-append-mortal` appends a freshly allocated `b`, so
  531  dropping it as well is a use after free.
  532  
  533  **Allocation order.** A String result is allocated last cell first: `append(a,b)`
  534  copies `a`'s cells onto the moved `b` from `a`'s last character to its first;
  535  `reverse(a)` allocates from `a`'s first character; `show` from its last digit. A
  536  Big result is allocated before the operands are dropped. Prims still without a
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
