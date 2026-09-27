# Round 1: pack as a binary odometer

The baseline's two packing helpers separate row encoding from row consumption:
each row is traversed once to pack and again to drop. Their structural roles are
correct but the boundary movement is invisible in the packing operation itself.

Replace those helpers with one cell-stream transducer. A countdown advances
beside a one-hot place; at the last column the accumulated mask is emitted and
both return to their origins. This is a concrete carry operation, making the
word representation and row boundary visible together. Keep the census and
unpacking unchanged so the effect of this reading change remains inspectable.

Correctness risks: an off-by-one countdown, a premature 32-bit shift, and empty
widths. Use width minus one in saturating Nat arithmetic, emit before shifting
the final place, and terminate on the cell list. Valid empty inputs terminate
immediately. Height is implied by the contract's exact input length.
