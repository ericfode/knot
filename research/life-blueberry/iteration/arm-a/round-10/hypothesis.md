# Round 10: one full-adder grammar on both spatial axes

Base this final candidate on the selected round 7. Rounds 8–9 added explicit
mask/place state without meeting the remaining target; recovered round 9's
duplex memetic mass is 0.55, while round 7 retains the more compact state.

Make one concrete reading change to its census. The vertical sum uses parity
plus carry, but the two horizontal sums use a different majority expression.
Rewrite both horizontal sums with the same three-line identity as the vertical
sum: side parity, parity XOR center, side conjunction OR parity-and-center.
Names ns/we0/we1 identify the symmetric side pairs. One learned operation now
explains all three additions, replacing two equivalent but distinct idioms.

This is an algebraic reading improvement, not an unchanged retry or a change to
the rubric. The duplex recurrence, two-row delay, public functions and final
three/four selection remain those of round 7.

Correctness risk is Boolean transcription. For lane bits a,b,c, write p=a XOR b;
the sum bit is p XOR c and the carry is (a AND b) OR (p AND c). Carry and sum
still count the same 3x3 population. Preserve all fixed gates. This is the last
authorized round regardless of its result.
