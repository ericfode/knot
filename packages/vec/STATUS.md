# Vec status — complete, 2026-09-26

Published and verified: `0xd684886d10b431b9dce6c3b2d1ef1980`.

```bend
import 0xd684886d10b431b9dce6c3b2d1ef1980/main.bend as V
```

Base only; no external package dependencies. INTERFACE.md is stable. The reviewed
13-file / 32,241-byte MIT-0 upload includes implementation, independent list model,
LAWS/PROOF, constructive witnesses, conformance, generic-value checks and benchmark.
No sibling, private or unrelated files were uploaded.

Verified against Bend 2.0.29 / 574b6d39a235b539eb19a5c532993a0abb3d11ad:
- 25 zero-hole laws: 19 universal over Data elements at fixed shapes and six
  concrete boundary normalizations. General all-length refinement is not claimed.
- CPU and JavaScript: 12,288 bounded traces per backend and seven longer families.
- CPU/JS records containing Strings and a non-ASCII label survive growth/updates.
- Nine type-correct semantic mutants killed by unchanged assertions and checked
  laws. Receipts distinguish intended observations and first rejecting laws.
- Vec duplication rejects with the intended consumed-more-than-once diagnostic;
  closure-element rejection requires expected Data / observed Type. The original
  parser-failing closure fixture was disqualified and repaired after release;
  receipts/ownership_repair.json records the correction. Published source unchanged.
- Native scaling through 262,144 elements; every indexed value agrees, capacity
  doubles, inferred copies=262,143 and initializations=524,287 at that size.
- Empty-cache remote import, proof check, native and JS execution passed; all 13
  fetched file SHA-256 values and recomputed package hash match the reviewed upload.
- Perch: the original release recorded unavailable live inference. A subsequent
  live audit completed on jev-1.13.0; see PERCH_REPORT.md for full source coverage,
  advisory control calibration, misses and adjudication. A later parsed pass
  reviewed 35 implementation declarations (350 checks) and the law packet
  (9 checks), with 36 completed responses and no findings; see
  PERCH_PARSED_REPORT.md. Published Bend is unchanged.

Limits: Data elements only; Vec is affine. Allocation policy errors are explicit,
actual host OOM remains a runtime failure. No GPU execution or all-state universal
refinement proof claimed. Internal Buffer construction is outside the public API.

Reproduce local gates: `python3 packages/vec/scripts/gate.py`.
Repeat only the repaired negatives: `python3 packages/vec/scripts/gate.py ownership`.
Inspect exact upload closure: `bun packages/vec/scripts/closure.ts`.
Remote consumer source: tests/remote_consumer.bend. Run with a new BEND_LIB cache
through scripts/bend-reference for an independent fetch. RELEASE.json records
closure, compiler, outcomes and receipt identities; receipts/ holds raw results.
There is no remaining publication blocker.
