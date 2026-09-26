# TermStore status — 2026-09-26

Complete: published and verified from a fresh remote cache.

API: `import 0xce7bfa94c40ded8493cdb39d330add0c/main.bend as S`
Proof/release: `import 0xce7bfa94c40ded8493cdb39d330add0c/release.bend as TermStoreRelease`
Dependency: Vec `0xd684886d10b431b9dce6c3b2d1ef1980/main.bend`.
Expected and returned content hashes match. Official hub: https://hub.bend-lang.com.

Verified with Bend 2.0.29 at 574b6d39a235b539eb19a5c532993a0abb3d11ad:
- Fourteen zero-hole laws: seven quantified theorems (including the independent
  model append theorem and a fixed three-cell generic payload theorem), seven
  concrete normalizations. Full arbitrary-store-history refinement is not claimed.
- CPU/JS conformance: ten named assertion families, 128 × 128 mixed store operations,
  all sixteen memo state/action pairs, exact results and unrelated-cell preservation.
- Generic runtime Store<Term> and Memo<Term,String> specializations pass.
- Review regressions cover zero-limit scope consumption and memo growth after
  Ready/Failed, plus allocation exhaustion while another cell remains Evaluating.
- Ten semantic mutants type-check and compile before failing their intended
  unchanged assertion. No syntax/type/harness failure counted as a semantic kill.
- Three intended checker-phase negatives: Store/Memo duplication and closure
  payload (expected Data, observed Type). Exact diagnostics and source hashes retained.
- CPU/JS scaling from 16,384 to 524,288 cells; every ID/value checked. Counts are
  explicitly source-derived; timings include process startup.
- Fourteen reviewed uploaded files, 42,634 bytes, explicit MIT-0. Laws, proofs,
  model, conformance and benchmark included; no sibling source or private files.
- Fresh BEND_LIB began empty. Downloaded proofs checked with zero holes; native
  and JS consumers each printed term=73 and passed all ten conformance families.
  Every fetched TermStore and Vec file matched the published closure hashes.
- Nine relevant Perch rules load/match. Live requests and calibration unavailable
  without PERCH_API_KEY; four controls retained. No model verdict claimed.

Core is pure first-order Data storage, with append-only slots and explicit owner
threading. One Scopes chain per identity realm; cancelled attempts must be discarded
before retry. Concurrent attempt fencing, affine handles, GPU/Wasm validation and
arbitrary-size/history store-refinement proofs are outside this release's claims.

Release identity/provenance: RELEASE.json. Reproducible gates: scripts/gate.py,
scripts/scaling.py, scripts/perch-check.ts, scripts/inspect-release.ts and
scripts/release.py. Evidence: evidence/. No remaining release blocker.
No git branch/commit/push or root/sibling source edits performed.
