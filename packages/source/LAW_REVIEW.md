# Source law review packet

Scope: owned immutable indexed Source; codepoint cursors/spans and LF line index.
This packet covers all supported operations; implementation helpers are private by
API convention. Pure Bend, pinned 2.0.29. Vec public API is the only package
dependency, pinned to 0xd684886d10b431b9dce6c3b2d1ef1980. Expected state relation: Vec chars = original scalar sequence,
cached n = its length, starts = [0] plus i+1 after each LF, file = caller ID.
The independent model uses linked String prefix scans and position enumeration;
it imports neither Source nor Vec and does not use a line index/binary search.

## Contract observations and matrix

All operations return the unchanged Source; checks observe text, file ID, length
and line count after each operation. Units are Unicode scalars, not UTF-16.
IDs are unique per caller session/revision; reuse for different text is a caller
violation. Scalar limit is 16,777,215. CR is content; LF starts the next line.
The empty text has one line; EOF is a valid position, but cannot be read by get.

| Public operation | Laws / observations | Independent runtime domain |
| --- | --- | --- |
| maximum | maximum_policy = 16,777,215; bounded construction | zero/exact/over-limit; maximum clamp follows Vec bound |
| new, bounded | content_identity, empty_content, scalar_units, invalid_scalar, exhausted_limit | original values/order; Unicode scalar edges; empty, exact, exhausted |
| file | file_identity: forall id, file(new(id,"a😀\nβ")) = Done(id) | metadata uses caller ID 7 |
| length, line_count, text | scalar_units = 4; empty_lines = 1; content_identity exact "a😀\nβ" | all nine corpus texts; preserved text after every observation |
| get | indexed_value compares to independent list model | every position plus EOF/after EOF/U32 max |
| cursor | accepted_cursor/rejected_cursor quantify arbitrary Source and i with <= bound true/false, preserve entire Source | every legal position, EOF, invalid offset |
| peek | peek_codepoint expects Some('😀') | nonempty, EOF, foreign, invalid |
| bump | bump_restore_content expects consumed scalar and next cursor; eof_fixed_point | positions 0/1, empty/nonempty EOF, invalid/foreign |
| checkpoint, restore | foreign_restore universal; bump_restore_content and foreign_cursor | original nonzero cursor, saved token, movement, restore and unchanged text |
| span | accepted_span/rejected_span_universal with start<=end<=n true/false; span_order, empty_eof_span | all valid ranges in each corpus, reversed and beyond EOF |
| extract | span_order expects "😀\n", foreign_span | every valid range against independent String take/drop; foreign/reversed/overrun |
| locate | newline_location, cr_is_content, crlf_location, trailing_line | every position including EOF vs linear prefix model |
| offset | canonical_location; newline_roundtrip | grid of lines/columns including noncanonical end; all offset/location round trips |

Source locations: main.bend contains public definitions; model.bend the oracle;
observations.bend contains named assertions and retained-content checks;
conformance.bend enumerates samples/positions/ranges/locations. PROOF.bend fills
LAWS.bend. tests/invalid_scalars.bend is the native malformed-input partition.

## Inhabited domains and exact claim categories

Universal conditional proofs cover arbitrary Source cursor bounds, span bounds,
and foreign restore; success/failure equality includes the complete unchanged
owned Source. Domains are inhabited by new(7,"ab"), cursor 1, span [0,2),
invalid cursor 3, reversed span [2,1), and foreign ID 8. inhabited_cursor_domain
and inhabited_span_domain normalize the successful public operations, including
construction. rejected_offset, rejected_span and foreign_cursor normalize the
invalid cases. No Empty parameter, unsafe witness or contradictory antecedent.

Five theorems quantify arbitrary file IDs over fixed empty/Unicode text shapes:
content preservation, file identity, empty content, empty line count, scalar
length. The remaining behavioral laws are **concrete normalization**, not general
all-string refinement. checked_cursor is auxiliary helper normalization only.
PROOF checks with zero holes and no package axiom, foreign declaration or unsafe
function. Base arithmetic/arrays/native lowering and Vec are trusted dependencies.
The complete loaded Base foreign/unsafe inventory is in receipts/closure.json;
loading an unused unsafe Base declaration does not make it a package proof step.

Runtime corpus: "", "x", "ab", LF, "a\n\nb", CRLF, "x\ry", "a😀\nβ",
and NUL+é+LF+LF. All valid spans and positions are enumerated; reverse locations
include invalid lines/columns. Invalid tests include surrogate endpoints and
U+110000 (native), maximum U32 offsets, foreign IDs, reversed ranges, EOF and
bounded exhaustion. JS's Char constructor rejects malformed scalars before Source;
JS package validation is therefore claimed only for representable Char inputs.

## Composition and mutation evidence

Checkpoint witness: original c = Cursor{7,1} over "ab". Assert checkpoint(c) == c
independently. bump(c) returns Cursor{7,2}, Some('b'). restore(saved) returns the
original c, with text still "ab". This avoids deriving the expected checkpoint
from the implementation under test. A first draft omitted the independent
comparison; hostile review identified and repaired it before the mutation gate.
The dedicated Perch rule captures this exact oracle weakness.

Eleven mutants each compile/type-check as an implementation, then the unchanged
baseline-passing Bend witness returns 0 instead of 1: stored characters replaced
by 'x'; indexed read erases file identity; bump stays at the old position; checkpoint rewinds to zero; foreign cursor
accepted; extraction returns empty; CR treated as LF; binary-search < becomes <=;
EOF cursor rejected; column at next-line start accepted; surrogate accepted.
These attack defining values, identity, boundaries and state composition.
No syntax/type/harness failure counts as a kill. No survivor is reported.
Exact mutant changes, witnesses, type-check receipts and source hashes are in
receipts/mutations.json; scripts/gates.py reproduces them without changing originals.

## Scaling, trust and remaining limits

CPU and JS workload builds 2,048 / 8,192 / 32,768 / 131,072 scalars, then checks get
and locate at every position including EOF against arithmetic expectations for
alternating x/LF. All agree. Native median total times were approximately
2.8 / 3.6 / 6.4 / 16.2 ms; JS 19.9 / 27.8 / 45.0 / 130.0 ms in the initial run.
Receipts are authoritative for reruns. Timings include process startup, exclude
compilation, and are not proofs. Structural analysis: geometric Vec pushes yield
linear indexing, each line probe halves the interval, indexed reads use Vec's
native Array access, reverse location uses at most two reads. Probe bounds in the
receipt are analytic upper bounds, not measured allocation/instruction counts.
No GPU execution, all-length refinement, or host-OOM recovery is claimed.

Hostile candidates examined: constant content, stale bump, cross-file reuse,
checkpoint-to-zero, empty extraction, conflating CR/LF, boundary-line misassignment,
and aliasing next line via its predecessor. The eleven deterministic mutants reject
them. Unproved remaining scope: general refinement from every valid String to all
observations, backend code generation correctness, and caller ID uniqueness.

Perch: eight shared law rules plus source-checkpoint-observation cover this packet.
Clean/broken/held-out controls are in tests/perch. scripts/perch-wiring.mjs verifies
nonzero coverage and complete requests using an explicitly offline stub. That
release-time check did not calibrate probabilities. A subsequent live audit on
2026-09-26 used jev-1.13.0: the checkpoint rule reported both broken controls at
75% and left the clean controls at 23% and 18%, below its current 70% floor. The
original 80% floor would miss these broken controls; the rule remains advisory.
See PERCH_REPORT.md and receipts/perch-audit-2026-09-26/ for exact live coverage,
source identities and adjudication. Deterministic gates remain authoritative.

Source hashes are recorded alongside each actual run in receipts/gates.json,
receipts/mutations.json and receipts/scaling.json; final hashes and exact reviewed
upload closure are frozen in receipts/closure.json and RELEASE.json. Published as 0x88d5b48c03f82f217d3a2aa0656744f4. The fresh-cache consumer
checks the proof closure and passes CPU/JS execution. Every Source and pinned
Vec file hash matches. See receipts/publication.json and receipts/remote.json.

## Frozen source identities

```text
bbd74050a1a1fc5ae7af9f8fce892023de197f8e37dcfdf87ef000af718f0950  LAWS.bend
06e8c1044639d44fbfc6eeea3618b8dc8a4f75c25a2409918c97c86deda782af  PROOF.bend
d28dbdb645e5e132917653cf8434f59a37c4b0438944af28a430fbb1771793b8  benchmark.bend
93ede95e703f52c7efe436a98681d6003068b10819e423a1c3a3c0012f9e0c69  conformance.bend
d1e38d7f3f98a1db77eca3df5640fd1b67ad5b0a815162b2e1d6d12313a70800  example.bend
83029b603921ea8a978c3f9a424fb256e0737d8041836c2749f8bd1b5e0be12c  main.bend
2ba69937a36ee689bec25bcc2f99a83bdcf8373eb88e30813800388d7a8495ea  model.bend
c0d4d88f9e6324db3ec5698280d5ffa807b5b78304d02127fb6b75627ce39cb0  observations.bend
495a5d4767a750b176387d568489a556e23af935e8a05960c12839ce2ce4fc1f  proof_observations.bend
e5cd3a2902d6f871978777683442df9fe03f76221f37058a1b56212b7e469adb  release.bend
43e2cd88043f6f1b7c183e017931bc68dabae516b35a4eab9e319187442a9141  types.bend
```
