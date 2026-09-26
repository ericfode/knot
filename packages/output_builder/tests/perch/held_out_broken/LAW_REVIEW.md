Chunk composition constructs an immutable Join in constant work. Finishing
recursively visits both children and copies each fragment into a suffix. We
claim total finish cost O(N), where N is emitted bytes, independent of the
number of fragments. Empty fragments cost nothing under this bound because
they emit zero bytes. No shape restriction is placed on the tree.
