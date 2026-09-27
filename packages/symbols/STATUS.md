# Symbols status

2026-09-26: an unpublished working revision replaces the forward Base Map with
a balanced character trie. Public behavior, independent model, accepted laws,
Vec dependency and the published import are unchanged. The current implementation
and complete search evidence are in [STYLE_CAMPAIGN.md](STYLE_CAMPAIGN.md).

The original proofs, native/JS conformance and release consumers, eight semantic
mutants, additive exact-string observations and structural balancing checks pass.
Existing native common-prefix workloads take 0.244–0.568x baseline time; sorted
single-character workloads take up to 1.61x baseline time. This tradeoff is accepted
for the working compiler-support implementation; no universal speedup is claimed.

The selected lookup passed all three frozen v2 style axes. Current v3 review
still passes memetic identity, Delight, Anticipation and Payoff for that lookup,
but not the new Galaxy-brain requirement. No complete v3 declaration/package
style pass is claimed. Current commands write receipts/working/ so the published
release receipts below remain intact. GPU remains unvalidated.

## Published release evidence

2026-09-26: published and remotely verified.

`import 0xf5507d46d06a1a8043dcb1a582194615/main.bend as S`

Proof-inclusive entry: `0xf5507d46d06a1a8043dcb1a582194615/release.bend`.
Interface is stable in INTERFACE.md. Seven supported Table operations in main.bend.
Pure Bend core, exact String equality, Base Map forward index, Vec reverse storage,
append-only IDs and explicit owning-table lifetime. Original source licensed MIT-0.

Verified with pinned Bend 2.0.29 revision 574b6d39a235b539eb19a5c532993a0abb3d11ad:

- Complete PROOF.bend: zero holes. Three universal conversion laws for arbitrary
  String first insert/reverse, zero limit failure preservation, and empty find.
  Five additional concrete normalization laws. No universal arbitrary-history
  implementation-refinement claim.
- Native CPU and JS: conformance returns 1; 6,912 exhaustive three-command traces
  with full state snapshots plus Unicode/NUL/prefix, 65-name growth, repeat/full,
  invalid-ID and clamp/default cases. Release example returns 1 on both lanes.
- Eight semantic mutants parse/type-check before unchanged tests reject them.
- Nine native scaling workloads, all expected IDs/text verified. At 512 names,
  16 table lifetimes, 0/64/256 added common-prefix code points: median
  0.0415/0.2821/1.0167 seconds. Base Map's O(hL+L) cost is significant and disclosed.
- Perch: nine review rules and three dedicated controls have nonzero complete
  offline request coverage. No live provider verdict/calibration: PERCH_API_KEY
  is absent. Provider failure is not treated as a passed model review.
- GPU unvalidated. Host OOM and physical maximum-size allocation not exercised.

Receipts: receipts/gates.json, mutations.json, benchmark.json, perch-wiring.json,
closure.json. Coverage, trust boundary and source hashes are in LAW_REVIEW.md.
Commands: `python3 packages/symbols/scripts/gates.py` and
`python3 packages/symbols/scripts/benchmark.py`.

Vec is pinned to 0xd684886d10b431b9dce6c3b2d1ef1980. Its repaired gates.json
digest and all 13 uploaded source hashes matched RELEASE.json immediately before
publication. BendHub returned the expected Symbols hash 0xf5507d46d06a1a8043dcb1a582194615.
The 12-file MIT-0 upload contains only owned implementation/model/observations,
laws/proofs, conformance, benchmark and consumer sources plus LICENSE.

A fresh BEND_LIB cache fetched the release, checked the full proof-inclusive
consumer, and built/executed native CPU and JavaScript consumers: both returned 1.
All 12 Symbols files and all 13 Vec dependency files match reviewed SHA-256 values.
Durable consumer: tests/remote_consumer.bend. Raw commands: receipts/release-commands.json.
RELEASE.json records identities, compiler/dependency pins, gate/receipt hashes,
fresh verification, proof boundaries and backend limitations. No blocker remains.

IDs follow first-successful-intern order, so reordered insertions may change IDs
across builds. Namespaces are caller-managed (separate scoped tables or injective
name encoding). Canonical remapping is outside this release.
