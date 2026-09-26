# Bidirectional preservation — clean control
Table contents initially ["a"], forward {"a":0}, limit 1. intern("b") returns
Exhausted without changing either structure. Then intern("a") returns 0,
find("b") is None, resolve(0) returns "a", and length remains 1. Non-full insertion
of "b" in limit 2 appends at ID 1 while retaining find("a")=0 and resolve(0)="a".
These are independent expected values. Both forward and reverse observations
are checked after transitions. IDs belong to one table lifetime.
