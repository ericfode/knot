# Round 8: counter-rotating bit positions

The duplex operation emits immediately but builds its input word through one
deferred callback per bit. Replace that nesting with an incoming mask and a
one-hot input position. Each step shifts the output right and the input position
left, consumes one raw cell, and ORs its positioned bit into the incoming word.
The continuation runs only at the row boundary.

The reading gain should be direct symmetry between the two moving bit streams,
with all transfer in one recursive expression. This changes the actual
accumulation mechanism and removes per-column closure composition; it is not
a reroll of the 0.59 result. No speed claim is made.

Correctness risks: initialization and the last position at width 32. Start
place=1 and incoming=0. The final input is inserted before its unused position
shifts out of the U32; Nat width still controls exactly how many cells leave.
Input cells remain binary under the fixed contract.
