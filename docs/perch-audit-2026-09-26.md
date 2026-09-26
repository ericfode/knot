# Knot Perch audit — 2026-09-26

The six package owners and Compiler Planning completed live review of **88
maintained Bend sources and eight real law packets**. No Bend-source or real
law-packet finding crossed its reporting floor. This is not a correctness claim:
the controls exposed missed defects, and independent review found a benchmark
input bug. Shared JavaScript tooling was also scanned; that review led to a
reproduced zero-coverage bug in the Perch wrapper.

The user's follow-up request is implemented: **Perch now uses Bend's actual
parser**, pinned to Bend 2.0.29 / `574b6d39a235b539eb19a5c532993a0abb3d11ad`.
The local extension is installed automatically by `npm ci`, with a checksum
guard on Perch 0.3.5. [Setup and limitations](perch.md).

## Owner reports

Counts below are the checks retained in each owner's report, including its
controls and any documented rechecks. A rule evaluation is not an independent
proof. Actual provider model: **jev-1.13.0** throughout.

| Area | Bend files | Provider responses | Rule evaluations | Result |
| --- | ---: | ---: | ---: | --- |
| [Vec](../packages/vec/PERCH_REPORT.md) | 13 | 25 | 114 | No production findings; narrowed stale-length rule now catches three broken controls |
| [Source](../packages/source/PERCH_REPORT.md) | 13 | 19 | 100 | No production findings; both broken checkpoint controls caught at 70% floor |
| [OutputBuilder](../packages/output_builder/PERCH_REPORT.md) | 13 | 18 | 91 | No production findings; one held-out complexity defect missed at 79% versus 80% floor |
| [IntMap](../packages/int_map/PERCH_REPORT.md) | 11 | 18 | 94 | No reported production finding; manual review found and fixed benchmark input bounds |
| [Symbols](../packages/symbols/PERCH_REPORT.md) | 12 | 16 | 84 | No production findings; both broken controls caught |
| [TermStore](../packages/term_store/PERCH_REPORT.md) | 14 | 19 | 97 | No production findings; both broken controls caught |
| [Research](../research/PERCH_REPORT.md) | 12 | 14 | 88 | No findings; both execution-model and adaptive-task packets reviewed |

The six package reports account for 115 responses and 580 evaluations. Research
retains 14 selected receipts / 88 evaluations, including two of the later parser
smoke checks; do not add those same receipts twice. Every selected input has a
source hash and actual response evidence. The package owners verified published
upload closures remain unchanged. No package was republished by this audit.

## Confirmed defects and residual advisories

1. **IntMap benchmark input bounds:** size zero was accepted as a successful
   vacuous benchmark despite the documented range 1..4096. Both benchmark entry
   paths now enforce the range. Native and JS checks cover valid, excessive,
   zero and malformed inputs. This file was outside the published upload
   closure. Perch missed this defect; its independent reproduction is retained
   in the IntMap report.
2. **Perch wrapper coverage:** a scan restricted to an unrelated Markdown file
   returned exit 0 with zero methods and zero applicable file rules. The new
   regression failed before the fix and passes afterward. The wrapper now
   rejects empty coverage; partial parser/provider coverage also returns a
   failure. Native `scan --since HEAD` remains an explicit unchanged result.

The [shared-tooling scan](perch-calibration/tooling-2026-09-26.json) parsed five
JavaScript files and reviewed 24 methods in 24 live calls. The extensionless
`scripts/bend-reference` launcher was not selected by Perch; it has no new
semantic-review claim. Third-party vendor code was excluded.

Perch raised advisories on `runPerch`; investigation established the concrete
coverage defect above. Its original category/location was imprecise. A
[targeted post-fix check](perch-calibration/tooling-fix-2026-09-26.json) still
reports `type_confusion` (74%), `unvalidated_destination` (73%) and
`error_ignored` (67%). The destination advisory is a false positive within this
CLI's trust boundary: the operator explicitly configures the provider endpoint;
reviewed source cannot choose it. The other two residual labels are **unresolved
advisories without a reproduced counterexample**, not additional confirmed bugs.
Tests verify malformed provider answers, authentication failures and coverage
failures cannot become passes. Do not change correct behavior just to silence
the remaining scores.

## Rule calibration

[Shared-law controls](perch-calibration/laws-2026-09-26.json): **19/24 classified
correctly**, no false alarms, five false negatives at current floors:

| Rule | Missed control | Probability broken |
| --- | --- | ---: |
| law-domain-inhabited | impossible positive allocation in a zero-capacity store | 76% |
| law-observable-essence | memo lookup always returns None | 75% |
| law-state-composition | map updates erase previous entries | 69% |
| law-proof-claim-integrity | finite examples / holes presented as universal proof | 46% |
| law-proof-claim-integrity | a model theorem promoted to optimized-API correctness | 54% |

The intended rules also missed both historical regression packets: lossy
projection scored 32%, wrong checker-phase evidence scored 20%. The additional
mutation rule flagged the latter at 88%; that does not rescue the intended
proof-claim rule's calibration. Proof-claim scores overlap valid production
packets, so merely lowering its floor is unjustified. Shared floors stay
unchanged and advisory. The calibration runner is reproducible via
`node scripts/calibrate-law-rules.mjs --live`; ordinary test gates stay offline.

Vec's owner narrowed its dedicated rule to one concrete stale-length observation:
broken controls moved from 53%/60% to 91%/93%, clean controls remained 9%, and a
fresh broken control scored 90%. Its 80% floor is unchanged. OutputBuilder's
79% held-out miss remains recorded. Source's earlier 70% floor was preserved.

The machine-arithmetic rule repeatedly scored arithmetic-free release wrappers
around 70–76%. These are weak below-floor signals, not counted reported false
positives. Maintenance should test narrow arithmetic-free and real-overflow
controls before changing that rule. No confidence score is proof evidence.

## Parser verification

- [Current corpus receipt](perch-calibration/parser-corpus-2026-09-26.json): all
  **96** nonignored package/research Bend files parse, including checker-negative
  syntax fixtures; **1,068** definitions/laws are extracted. Those additional
  negative fixtures are syntax coverage, not expected-clean semantic reviews.
- [Live parser checks](perch-calibration/parser-live-2026-09-26.json): six package
  implementations and two research models completed all six Bend rules with
  parser metadata and live provider responses. These checks used the same
  parser revision before the final conservative graph-resolution refinement.
- Actual CLI integration tests exercise a Bend-only committed scan, imported
  call edges, named-function checks, Unicode locations, malformed input,
  unresolved names, zero coverage, partial parsing, and JavaScript fallback.
  Unknown Bend imports never link to an unrelated same-named function.
- `npm run lint:verify`: **13 tests pass**, plus the eight-law wiring gate.
  [A fresh isolated `npm ci`](perch-calibration/install-2026-09-26.json) reinstalls
  the final adapter and parses Bend without the local compiler toolchain.

Original package receipts were collected with whole-file semantic checks before
the adapter was installed; their historical no-parser statements describe that
phase. Parser coverage is supplied separately here rather than rewriting old
evidence. Whole-file custom rules remain whole-file rules after parsing.

## Remaining boundaries

Standalone parsing does not validate imported law existence, arity, constructor
signatures or templates; diagnostics make that missing context explicit. It
does not fetch imports, execute code, type-check or prove laws. Metrics remain
unavailable and the static graph is partial. Scans read committed Git content;
file checks read the working copy. This audit did not commit other chats' work.

WGSL and the research/package host harnesses have no additional Perch coverage
in this report. Their deterministic device, quantity, proof, conformance and
mutation evidence remains separate. The published package sources are unchanged;
ongoing research may evolve after these recorded hashes. The existing weekly
maintenance heartbeat will review new friction and low-signal evidence.
