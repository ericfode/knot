# Round 3: emit the stencil directly

The sweep currently produces next-row words that a second traversal immediately
decodes. This separates the visible output from its Life calculation and leaves
the reader with a generic conversion pipeline.

Fuse row emission into the old-row sweep. Its two cases will each read as
emit(width, stencil(window), continuation), with the dead lower border as the
sole terminal variation. Rename the low-bit suffix recursion row.emit to match
this actual role. Packing and the bit-plane circuit remain unchanged.

Correctness risks are reversing row order through the continuation and using
new rows as old context. The suffix is the recursive sweep of the untouched old
tail; both north/here/below arguments remain old masks. Width still bounds the
emitted low bits, including width 32 and width zero.
