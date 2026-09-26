IntMap union_with: overlapping key 9 has Atom(2) on the left and Atom(7) on
the right. Combining constructs Join(left,right). The exact expected lookup
is Some(Join(Atom(2),Atom(7))); no nested Join is permitted. Left-only key 10
retains Atom(11); right-only key 12 retains Atom(13). This concrete observation
rejects swapped arguments, extra calls, or a call on a one-sided value. It is
not a universal theorem. Expected narrow rule result: satisfied.
