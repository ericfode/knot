IntMap union_with: overlapping key 4294967295 has 3 on the left and 7 on
the right. Combining computes 100*left+right. Expected lookup: Some(307).
Key 0 exists only on the left with 2; its expected lookup is Some(2).
Key 1 exists only on the right with 5; its expected lookup is Some(5).
These are concrete observations, not a universal proof. Expected narrow rule
result: satisfied, independently phrased arithmetic control.
