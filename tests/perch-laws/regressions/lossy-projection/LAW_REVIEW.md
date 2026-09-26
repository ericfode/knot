# Regression: a content projection can hide stale metadata

This is a synthetic rule-control packet grounded in the Vec mutation experiment,
not a claim that the current Vec package retains the defect.

The public API exposes to_list, length and checked get. A faulty pop clears the
last storage slot but leaves logical length unchanged. Starting from [7,9], pop
returns 9 and leaves slots [Some(7),None] with logical length 2. The observation
function skips None slots, so to_list returns [7]. A law requiring only the
returned value 9 and observed contents [7] passes. The public length is wrong,
and index 1 is wrongly classified as logically present.

The claimed complete behavioral specification contains only the returned-value
and to_list equalities. It has no law for length after pop, logical bounds after
pop, or coherence between the contents observation and public metadata. This
specification therefore permits an implementation violating the stated API.
