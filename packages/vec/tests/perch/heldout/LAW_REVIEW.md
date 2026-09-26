# Held-out clean control: range state observation
After constructing [11,23,37] and reserving 17, capacity is 32 and length is 3.
get(3) and slice(2,4) fail against logical length; slice(3,3) succeeds empty.
The live prefix has Some at precisely indices 0,1,2. to_list skips None, so its
three values are checked alongside length=3; filtered contents do not establish
representation validity. The stale pop mutant retaining length 3 after clearing
slot 2 is rejected by the unchanged length observation (expected 2).
