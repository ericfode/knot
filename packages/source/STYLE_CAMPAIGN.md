# Source style campaign

## source-search-1 — accepted, unreleased

Disposition: keep the first candidate as a narrow reading improvement. Each
terminal state now has one fuel-independent return; only `Searching` consumes
fuel. No helper, layer, API, dependency or vocabulary was added. The recursive
call and interval arithmetic are unchanged. This does **not** earn an automatic
three-axis style pass. Publication remains out of scope.

[Preregistration](campaigns/source-search-1/preregistration.json) froze the
reading problem, author taste hypothesis, contracts and independent assertions
before generation. The [author reading judgment](campaigns/source-search-1/author-reading-judgment.md)
was recorded before inspecting the after-score distributions. No user preference
for this particular candidate is claimed. Wildcard fuel trades explicit product
enumeration for one recognizable terminal-state rule; that is the concrete
reading benefit, not the two-line reduction by itself.

### Exact increment

At `main.bend::search`, the six fuel/state cases became four:

```bend
def search(fuel: Nat, +pos: U32, pair: V.Vec<U32> & Search) -> V.Vec<U32> & Search:
  match fuel pair:
    case _ Tuple{lines,Found{line}}: (lines,Found{line})
    case _ Tuple{lines,BadIndex{}}: (lines,BadIndex{})
    case 0n Tuple{lines,Searching{lo,hi}}: (lines,BadIndex{})
    case 1n+f Tuple{lines,Searching{+lo,+hi}}:
      search(f,pos,search_step(lines,lo,hi,pos,U32.is_le((hi - lo : U32),1)))
```

[Before](campaigns/source-search-1/before.snippet.snapshot) and
[after](campaigns/source-search-1/after-first.snippet.snapshot) are retained,
with full baseline and candidate source snapshots. Candidate authored with
GPT-6 Astra / high; one substantive attempt, **first compiler check passed,
zero diagnostic retries**. [First result](campaigns/source-search-1/evidence/first-result.json).

Baseline SHA-256: `83029b603921ea8a978c3f9a424fb256e0737d8041836c2749f8bd1b5e0be12c`.
Accepted SHA-256: `38f60094c1411632e50573b6aa18e92783d589340bd75b9ee6ea452074e66a17`.
The Vec pin remains `0xd684886d10b431b9dce6c3b2d1ef1980`.

### Deterministic acceptance

- Bend 2.0.29 / 574b6d39a235b539eb19a5c532993a0abb3d11ad: syntax,
  types/quantities and complete frozen PROOF check passed.
- Full native/JS conformance and native malformed-scalar checks passed.
- Supplemental exact terminal/pending/fuel/store assertions were frozen before
  generation and passed on both baseline and candidate, native and JS.
- All eleven unchanged mutants type-checked, then failed their intended
  baseline-passing semantic assertions. No locator re-anchoring or assertion
  change; no syntax/type failure counted as a kill.
- Full native/JS scaling through 131,072 scalars preserved all expected results.
  Initial largest JS medians were 123.02 → 155.57 ms. Because that apparent 26%
  slowdown was material, one alternating-order follow-up used eight pairs of
  the same built binaries: 123.34 → 123.61 ms, ratio 1.00224. This did not
  reproduce the slowdown. Initial largest native medians were 16.61 → 17.36 ms.
  Small process-level measurements include startup and have visible noise;
  no speedup or all-workload performance equivalence is claimed.

The [generated JS diff](campaigns/source-search-1/evidence/generated-js.diff)
changes only zero-fuel dispatch order; positive-fuel code is identical. Public
benchmark search starts at 25 fuel and needs at most 17 comparisons at the largest
size, so the changed dispatch is not reached there. This supports treating the
initial JS difference as measurement noise; raw timings remain visible.

[Gate receipt](campaigns/source-search-1/evidence/candidate/gates.json),
[mutation receipt](campaigns/source-search-1/evidence/candidate/mutations.json),
[baseline scaling](campaigns/source-search-1/evidence/baseline/scaling.json),
[candidate scaling](campaigns/source-search-1/evidence/candidate/scaling.json),
[interleaved timings](campaigns/source-search-1/evidence/interleaved-js.json).
Exact commands/stdout/status are in each phase's `commands.json`.
[Integrity receipt](campaigns/source-search-1/evidence/final-integrity.json)
confirms frozen files, first candidate and historical release evidence unchanged.

### Live review and remaining style deficits

P(level 3 or 4), independently on each axis; meets ≥60%, below ≤40%, otherwise
uncertain. These are model judgments, not measured human preferences.

| Declaration | Conceptual compression | Delight | Memetic identity |
| --- | --- | --- | --- |
| `Search` | 72% → 71% (meets) | 77% → 77% (meets) | 9% → 9% (below) |
| `search_step` | 61% → 63% (meets) | 70% → 71% (meets) | 17% → 16% (below) |
| `search` | 38% → 56% (uncertain) | 57% → 65% (meets) | 31% → 33% (below) |
| `location_finish` | 48% → 52% (uncertain) | 52% → 54% (uncertain) | 8% → 7% (below) |
| `Source.locate` | 39% → 34% (below) | 74% → 70% (meets) | 45% → 35% (below) |

All five declarations still need review: six axis results meet, six are below,
three uncertain, **zero declarations meet all three**. Changed `search` improves
compression/delight, but compression remains uncertain and memetic identity
below target. Neighbour decreases are retained, including `Source.locate`
compression 39 → 34% and memetic 45 → 35%. They do not establish a family-wide
improvement. The retained source-level benefit is the terminal-state grammar;
there is insufficient evidence for a strong memetic gain.

[Full baseline distributions](campaigns/source-search-1/baseline/style.json)
and [full after distributions](campaigns/source-search-1/evidence/style-after.json)
retain source/context/rubric identities. Baseline is the five matching rows from
`docs/perch-calibration/style-project-2026-09-26.json.gz`, not a new paid run.
After review: five requests and five responses, `jev-1.13.0`, requested
`jev-latest`, parser `bend-2.0.29-574b6d3-observer-v2`, rubric SHA-256
`a2e20d01461c2d0fb07aaa8cb577423693b73d07617318e9e30ed674186a01d3`.
Reuse was offered but zero rows matched after source/context identity changed.
Exit 3 means style attention. No score retries or rubric changes were made.

`Search` datatype context is truncated at four direct callers and same-file
context in both runs. Other four contexts are untruncated within helper/file/byte
limits. Remote Vec and Base details remain unresolved. Model scores cannot
validate those dependencies or establish backend cost.

Targeted semantic Perch: ten Bend/performance checks on changed `search`, eight
shared law checks on the new bounded [law packet](campaigns/source-search-1/LAW_REVIEW.md).
Final coverage: two requests/responses, actual `jev-1.13.0`,
**18 relevant checks, no findings**
(confirmed 0, false-positive 0, duplicate 0, unresolved 0).
Search context was untruncated. The unchanged checkpoint-specific rule remains
attached to the historical full packet and was not relevant to this change.
[Semantic index and exact commands](campaigns/source-search-1/evidence/semantic-index.json).
No repeated unchanged whole-package audit.

Local source review caught one overclaim in the first new law packet: locate
was said to reject a foreign ID, but takes a plain position, not a cursor. The
first eight-rule review had not flagged it. The packet now states the actual
parameter boundary; the original packet/receipt are retained in
`evidence/law-packet-first.snapshot` and `semantic-laws.json`. One corrected
packet-only review completed all eight rules without findings. Total semantic
usage is therefore three requests/responses and 26 checks, of which 18 cover
the final source/packet. No implementation or frozen assertion changed. This is
a concrete review limitation: confirm each matrix row against its signature;
a clean model judgment does not establish packet accuracy.

### Open work and reproduction boundary

Potential next bounded opportunity: inspect duplicated failure arms in
`location_finish` and whether the relation between Searching/Found/BadIndex and
public result conversion can be traced more directly. It needs a separate
preregistration and gates; no second candidate was attempted here. No new
abstraction or jargon is justified merely by low memetic scores. Neighbour
regressions and all listed unmet axes remain in the campaign queue.

Historical `RELEASE.json`, receipts, full law packet and interface were retained.
Published `0x88d5b48c03f82f217d3a2aa0656744f4` still names the prior source.
This working revision is **unreleased**; no publication or dependency-hash update.
No all-string refinement theorem, GPU execution or host-OOM recovery claim.

The batch validation script redirects the unchanged package harness to fresh
phase directories. Its recorded baseline run used the baseline source on disk;
its candidate run used the exact first candidate. It is a one-shot experiment
runner (fresh output directories required), not a command to replay baseline
against the current source. Use an isolated checkout with the intended snapshot
when reproducing, and retain new outputs separately. Historical receipts must
not be overwritten. The style and semantic commands are recorded in their
receipts/driver; no unchanged paid repeat is needed for this handoff.
