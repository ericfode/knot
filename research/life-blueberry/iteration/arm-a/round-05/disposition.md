# Round 5 disposition

Retain the streaming dataflow. Checker and the full behavior gate passed;
28 semantic checks returned no findings. All seven declarations meet conceptual
compression and delight; five meet memetic identity, with row.emit below at
0.17 and row.read uncertain at 0.41. Full distributions are in `style.json.gz`.

The implementation now carries only an old-row window and the raw suffix,
without either intermediate row list. The next reading problem is the separate
one-way row codecs. They can be composed into one duplex operation: emit a
completed row while reading the next input row, with a fixed pipeline delay.
