# Round 7: one recurrence over a zero-extended stream

Round 6 duplicates the duplex recurrence for source exhaustion and a present
cell. The two paths differ only by substituting zero for the input bit. Treat
the source as a zero-extended stream: default its missing head to zero and let
the tail of Nil remain Nil. The single remaining recursive expression sends
one bit out while the continuation collects one bit in.

This is a normalization of the actual dead-border semantics, not a renamed
helper. Base's Maybe.default and List.head/List.tail provide the exact bounded
operations; each advances or observes only the current head. No source prefix
is retraversed.

Correctness risk is changing the exhaustion behavior. Base definitions confirm
that absent heads use the supplied zero and the tail of Nil is Nil. Retain the
same Nat width, two-row latency, drain count, and stencil circuit. Additional
reference read: Base lines 710–738 for Maybe.default.
