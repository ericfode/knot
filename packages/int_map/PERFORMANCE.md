# Performance receipt interpretation

Observed environment: Apple arm64, Apple clang 21.0.0, Bun 1.3.14.
Three process-level samples per size/backend; table shows medians in milliseconds.
Each sample includes startup, construction, self-union with addition, validation
of every key, exact fold sum/size, complete erasure, and structural counting,
for both dense and 16-common-low-bit layouts. Independent quadratic list-model
validation runs separately and is excluded from these timing samples.

| Entries per layout | Native ms | JS/Bun ms | Dense nodes | Shared-prefix nodes |
| --- | --- | --- | --- | --- |
| 64 | 5.241 | 20.939 | 1791 | 783 |
| 256 | 4.684 | 23.656 | 6655 | 2575 |
| 1024 | 10.727 | 34.871 | 24575 | 8207 |
| 4096 | 40.195 | 62.085 | 90111 | 24591 |

Every layout has maximum key depth 32. Full erasure returns zero nonempty
nodes. The retained node bound is 33*n; construction emits 33*n trie constructors
plus 32*n temporary path cons constructors at source level. These are structural
counts, not measured allocator calls or peak resident memory. Every union value,
size and checksum matches; independent list-model validation passes on both
backends for each size. Small-workload startup noise is visible. No timing ratio
is promoted to a complexity proof, speedup claim, or GPU result.

`receipts/performance.json` preserves all samples. `SPEC.md` derives work and
allocation bounds from the source, including payload/callback and reclamation
exclusions. Emitted C uses U32_BIN(key, >>, 1), and generated JS uses unsigned
right shift; neither converts keys to Strings. The generated files are temporary
build artifacts; reproduce with scripts/performance.py and the pinned compiler.
