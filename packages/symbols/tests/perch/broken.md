# Bidirectional preservation — broken control
Table contents initially ["a"], forward {"a":0}, limit 1. intern("b") returns
Exhausted, clears the forward map and keeps the vector ["a"]. The advertised law
checks only length=1 and resolve(0)="a"; it passes. There is no find or repeated
intern observation. The implementation claims all old symbol IDs remain usable
through both directions. Calling intern("a") now returns Exhausted.
