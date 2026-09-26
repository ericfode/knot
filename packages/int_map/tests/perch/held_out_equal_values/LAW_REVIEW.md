The only union collision test uses key 9 with value 7 on each input. The
combiner computes 100*left+right, and the expected collision lookup is Some(707).
Left-only key 10 must retain 11 and right-only key 12 must retain 13. The
collision test does not include any other values or invocation-tree observation.
