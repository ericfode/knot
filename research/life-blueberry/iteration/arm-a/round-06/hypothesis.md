# Round 6: a duplex row with two rows of delay

Reading and emitting currently express opposite halves of the same bit stream.
Combine them: at each column, emit the low output bit and collect one input bit;
at row end, pass the packed input and untouched suffix to the continuation.

The row pipeline carries three old masks. It emits their stencil while reading
the following row, then rotates the window. Starting from three zero masks and
running height+2 rows handles both startup and drain. Drop the first two output
rows, which are pipeline latency. Empty input supplies zero bits during drain.

The reading hypothesis is an actual duplex grammar: low bits leave while binary
conses enter, and the same window rotation handles every row. This removes the
special startup/flush branches and the isolated codec roles.

Correctness risks: latency off by one, mixing old/new values, and insufficient
draining. The first real row is emitted on pass three. Exactly height+2 passes
therefore emit height real rows after the initial two are discarded. Width is
unchanged, including zero and 32; all discarded lengths use Nat arithmetic.
