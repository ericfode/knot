# Refresh edge contract

Fixed before compiler probes, 2026-09-29. These are independent correctness
controls for bench-2, outside the timed hillclimb inventory.

- Peano parity at depths 0, 1, 2, 3, 31, 33 returns Off, On, Off, On, On, On.
- Last-cell traversal at lengths 0, 1, 2, 3, 31, 33 returns Off, On, Off, On, On, On.
  Cells alternate On/Off; the empty list returns its Off accumulator.
- A chain of 0, 1, 2, 3, 31, 33 flips starting at On returns On, Off, On, Off, Off, Off.
- Enum widths 1, 2, 3, 31, 33, 255 rotate the last constructor to T0.

The seed must check every source and both its native and Bun builds must return
the literal constructor before expectations are frozen. Knot must then compile
each source in both lanes, agree with the independent evaluator and execute
emitted Wasm with result guards and the profile's declared instance lifetime.
Seed builds use a wrapper that imports the unchanged fixture as F, adds the
seed-required Base import, and calls F.main. Its qualified output is frozen
verbatim. The original fixture is also checked without that wrapper.

No source-language law is added or weakened. These are concrete controls, not
universal proofs or a self-hosting or style qualification.
