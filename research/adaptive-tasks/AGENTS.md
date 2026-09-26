# Adaptive task prototype

Owned by Compiler Planning. Keep changes in this subtree unless updating its
project plan or shared review wiring. Do not change published package sources.

CPU semantic models, protocol code, witnesses, and proofs belong in Bend.
WGSL implements the device probe. JavaScript/Python only arrange inputs,
dispatch, build, read back, compare, and record evidence; neither is the semantic
oracle. Source-to-WGSL compilation and a general runtime heap are out of scope.

Use the root law/Perch workflow. Record exact source and toolchain hashes.
Reject a software/fallback adapter when claiming hardware GPU execution.
Distinguish quantified laws, finite cases, mutation checks, and device receipts.
