# Round 2 hypothesis

Round 1's flat sweep made the former two-depth generic `front` unnecessary:
every surviving call supplies the same type U32 and the same outside value 0.
This is real reading overhead: three boundary observations in `pulse` repeat
invariants the mechanism could state once, while `halo` hides its one next-cell
observation among generic arguments.

Specialize `front` to the zero-extended cell stream. Retain the explicit
west/center/east scalar window and all other recurrences. The hypothesis is that
one exact boundary primitive makes the repeated stencil grammar easier to see.
This is a narrowed domain operation, not a rename or an unchanged reroll.

Correctness risk: a replacement must cover every former `front(U32, xs, 0)`
call without changing list ownership or the meaning of empty north/south halos.
The original Life contract and independent gates remain unchanged.
