# Round 4 disposition

First-shot compiler acceptance, no repair. Fixed behavior gates passed and all
28 Perch semantic checks completed cleanly, with no findings to classify.
All seven declarations meet big-brain, six meet delight, and three meet memetic
identity. `window` is below memetic (0.06) and uncertain on delight (0.47);
`peel`, `halo`, and `pulse` are uncertain on memetic identity (0.53, 0.52, 0.51).
Full distributions and uncertainty remain in style.json.gz.

The stream-view experiment did not yield the intended reading improvement.
Bend's parameter-only matching forced a helper whose interface obscures the
simple horizontal sum; the implementation is behavior-correct but reads less
directly than round 1. Preserve it as rejected design evidence.

The next hypothesis changes representation, rather than adding another adapter:
row words make each column a bit lane. A parity/carry circuit can then expose
the eight-neighbor ring without per-cell boundary observations. Packing and
unpacking keep the external row-major list contract explicit.
