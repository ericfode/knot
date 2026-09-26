# Vec pop/growth state observation
The vector has logical length 2, capacity 8, and live values [17,29]. Spare slots
are None. pop returns 29 and clears slot 1. The post-state observer traverses the
array prefix, drops None slots, and returns the remaining values. It produces
[17], matching the list model. The regression assertion compares this list and
the returned 29. A candidate implementation leaves logical length at 2, but the
observer still returns [17]; the regression passes. No assertion reads logical
length or checks the next get(1). We accept that candidate as fully preserving
the pop contract because the remaining values agree.
