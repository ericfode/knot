# Round 5: stream both sides of the stencil

Round 4's callback still builds a complete list of packed rows before a second
walk opens the stencil window. Use its untouched-suffix continuation directly
in the sweep. The state becomes the two previous old row masks and the raw
input suffix; reading the next row completes the window, emits one new row,
and advances it.

This makes the entire dataflow explicit: read old below, compute old window,
emit new here, continue. It removes an intermediate old-row list and the generic
packing traversal, complementing round 3's removal of the new-row list.

Correctness risks are initialization and flush: height zero emits nothing;
the first row is read with north zero; the terminal sweep supplies south zero.
Callbacks must duplicate below only as reusable U32 data, and newly emitted
cells must never enter the old-row window.
