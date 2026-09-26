# Source status — complete, 2026-09-26

Published and remotely verified: `0x88d5b48c03f82f217d3a2aa0656744f4`.

```bend
import 0x88d5b48c03f82f217d3a2aa0656744f4/main.bend as S
import 0x88d5b48c03f82f217d3a2aa0656744f4/types.bend as T
```

Pure indexed Source implements retained Unicode scalar content, caller-scoped
file identity, checked cursor/checkpoint/span operations, LF-only line starts,
binary location lookup and checked canonical reverse lookup. Vec is pinned to
verified release `0xd684886d10b431b9dce6c3b2d1ef1980`; only its public API is used.

Verified with Bend 2.0.29 / 574b6d39a235b539eb19a5c532993a0abb3d11ad:
- 32 zero-hole laws: five universal conditional public cursor/span/foreign-ID
  laws preserving the whole Source; five file-ID-parametric fixed-shape laws;
  one auxiliary helper law; 21 concrete normalizations. No all-string refinement
  theorem is claimed.
- Native CPU and JS conformance: nine text samples, all positions and valid spans,
  location grids/round trips, retained text/file/length/line-count observations,
  checkpoint/bump/restore, invalid positions/identity/ranges, EOF, Unicode and
  bounded exhaustion. Native malformed-Char rejection passes separately; JS's
  runtime rejects such values before the package receives them.
- Eleven parseable, type-correct semantic mutants killed by unchanged,
  baseline-passing Bend assertions. No syntax/type/harness failure counted.
- CPU/JS scaling through 131,072 codepoints, every indexed read and location
  checked. Native emitted code uses direct block access. No GPU execution claim.
- Release-time Perch evidence was offline because credentials were unavailable.
  The subsequent live audit is recorded in PERCH_REPORT.md: all 13 Bend files,
  the real law packet and four checkpoint controls received complete provider
  responses. No package findings; both broken controls reported at floor 70%.
- Reviewed MIT-0 upload: 13 intended files, 40,740 bytes; laws, proofs, independent
  model, runtime checks, example and benchmark are included. No sibling source,
  unrelated or private files were uploaded.
- Returned hash equals expected hash. Empty-cache remote consumer checks the
  proof closure and passes CPU and JS execution. All Source and pinned Vec file
  SHA-256 values match; recomputed Source content hash also matches.

There is no remaining release blocker. RELEASE.json contains the exact closure,
compiler/dependency pins, receipts, environment, license and limitations.

Reproduce:
  python3 packages/source/scripts/gates.py
  node packages/source/scripts/perch-wiring.mjs
  bun packages/source/scripts/closure.ts

The first command runs proof, native/JS conformance, native invalid-scalar checks,
eleven semantic mutants and scaling. tests/remote_consumer.bend imports the
published hash; run with a new BEND_LIB directory for an independent remote fetch.
SPEC.md, INTERFACE.md and LAW_REVIEW.md define the supported API and proof boundary.
No filesystem, lexer/parser, UTF-16 conversion, or global identity allocator is
included. Host allocation failure remains outside typed error recovery.
