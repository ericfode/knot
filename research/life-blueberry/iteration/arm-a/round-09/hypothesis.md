# Round 9: clock two shift registers

Round 8 tracks a changing output word, incoming word, and one-hot input place.
Replace the moving place with a constant top bit for the row width. Each step
shifts both words right: the output loses its low bit, while the input receives
the new cell at its high end. After exactly width clocks, the first input cell
has reached bit zero.

The reading hypothesis is a shared clock operation rather than a word plus
position tracker. The top bit is computed once by step and passed unchanged
through the row pipeline. Retain the explicit accumulator, zero extension,
two-row latency, and census from round 8.

Correctness risks: reversed order and width zero. For width w, cell i moves
from w-1 down to i by the end of the row. top=1<<(w-1), with saturating Nat
subtraction, is unused when w=0. The largest shift is 31 for the valid domain.
