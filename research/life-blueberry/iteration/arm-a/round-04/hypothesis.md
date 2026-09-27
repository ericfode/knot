# Round 4: a row is a continuation over its suffix

The one-pass odometer fixes duplicated traversal but exposes three moving
coordinates: countdown, one-hot place, and accumulated mask. Replace it with
structural row reading. Each cons suspends one binary cons; at width zero, the
continuation receives the completed mask and untouched suffix. The board's
packing recursion supplies the next-row continuation.

This combines the original fold's local bit equation with the one-pass stream
property. Its reading hypothesis is that the two matching cons operations,
binary cons within a row and list cons between rows, form one traceable grammar.
The rest of round 3 stays fixed.

Correctness risks: closure quantity, structural recursion under the callback,
preserving the suffix, and bit orientation. The bit equation remains
cell OR shift-left(rest-of-row). Height bounds row construction, width bounds
the row reader, and zero width consumes no cells.
