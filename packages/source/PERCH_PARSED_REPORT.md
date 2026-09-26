# Source parsed Perch pass — 2026-09-26

**No package code needed changing.** Reviewed 14 parsed declarations and the current law packet: **149 relevant checks, 15 live provider requests and 15 completed responses**, actual model `jev-1.13.0` (requested `jev-latest`, Perch 0.3.5). No production findings were emitted. No rules, contracts, accepted laws or published source changed, and nothing was published.

## Exact scope and receipts

Each declaration received the six `bend-*` rules plus `perf-growing-prefix-copy`, `perf-loop-invariant-work`, `perf-linked-list-indexing` and `perf-amortized-growth` (10 checks). `LAW_REVIEW.md` received all eight `law-*` rules plus `source-checkpoint-observation` (9 checks). The root npm wrapper was used for every live request.

| Target | Checks | Provider receipt | CLI/context result |
| --- | ---: | --- | --- |
| `main.bend::Source.locate` | 10 | [9d21c5ad](receipts/perch-parsed-2026-09-26/9d21c5ad-8825-4970-9fb9-634d0ce06908.json) | [context](receipts/perch-parsed-2026-09-26/9d21c5ad-8825-4970-9fb9-634d0ce06908-context.json) |
| `main.bend::Source.bounded` | 10 | [c5cca861](receipts/perch-parsed-2026-09-26/c5cca861-47f6-4419-bc87-3ff02270ddaf.json) | [context](receipts/perch-parsed-2026-09-26/c5cca861-47f6-4419-bc87-3ff02270ddaf-context.json) |
| `main.bend::Source.text` | 10 | [d9add77e](receipts/perch-parsed-2026-09-26/d9add77e-2e67-481c-8086-726bc337f658.json) | [context](receipts/perch-parsed-2026-09-26/d9add77e-2e67-481c-8086-726bc337f658-context.json) |
| `main.bend::Source.get` | 10 | [1188f2e9](receipts/perch-parsed-2026-09-26/1188f2e9-9061-47b6-82c8-033cd9cb2f2c.json) | [context](receipts/perch-parsed-2026-09-26/1188f2e9-9061-47b6-82c8-033cd9cb2f2c-context.json) |
| `main.bend::Source.cursor` | 10 | [a0bf49b4](receipts/perch-parsed-2026-09-26/a0bf49b4-5937-445e-a4ba-966614b639a0.json) | [context](receipts/perch-parsed-2026-09-26/a0bf49b4-5937-445e-a4ba-966614b639a0-context.json) |
| `main.bend::Source.restore` | 10 | [e8cf0502](receipts/perch-parsed-2026-09-26/e8cf0502-abd5-4123-b55a-53b8994aa1d5.json) | [context](receipts/perch-parsed-2026-09-26/e8cf0502-abd5-4123-b55a-53b8994aa1d5-context.json) |
| `main.bend::Source.peek` | 10 | [405e684a](receipts/perch-parsed-2026-09-26/405e684a-1773-4e03-84d1-e13f4a5d4da9.json) | [context](receipts/perch-parsed-2026-09-26/405e684a-1773-4e03-84d1-e13f4a5d4da9-context.json) |
| `main.bend::Source.bump` | 10 | [c4311b00](receipts/perch-parsed-2026-09-26/c4311b00-cd8e-4b01-bd48-5aa4b17d6e69.json) | [context](receipts/perch-parsed-2026-09-26/c4311b00-cd8e-4b01-bd48-5aa4b17d6e69-context.json) |
| `main.bend::Source.span` | 10 | [0d8b55f2](receipts/perch-parsed-2026-09-26/0d8b55f2-a371-4617-8b39-ed0ee3d7d9b9.json) | [context](receipts/perch-parsed-2026-09-26/0d8b55f2-a371-4617-8b39-ed0ee3d7d9b9-context.json) |
| `main.bend::Source.extract` | 10 | [a6ac4dd0](receipts/perch-parsed-2026-09-26/a6ac4dd0-51ca-4bb3-ad16-20ea44f83e09.json) | [context](receipts/perch-parsed-2026-09-26/a6ac4dd0-51ca-4bb3-ad16-20ea44f83e09-context.json) |
| `main.bend::Source.offset` | 10 | [c6ad3b80](receipts/perch-parsed-2026-09-26/c6ad3b80-c115-49a7-a803-dca6b6cf5c66.json) | [context](receipts/perch-parsed-2026-09-26/c6ad3b80-c115-49a7-a803-dca6b6cf5c66-context.json) |
| `main.bend::build` | 10 | [78c81a85](receipts/perch-parsed-2026-09-26/78c81a85-dfcc-4e00-9ba6-070da56a948d.json) | [context](receipts/perch-parsed-2026-09-26/78c81a85-dfcc-4e00-9ba6-070da56a948d-context.json) |
| `main.bend::search` | 10 | [b2633655](receipts/perch-parsed-2026-09-26/b2633655-dc28-44d1-82ee-420b5dafe33b.json) | [context](receipts/perch-parsed-2026-09-26/b2633655-dc28-44d1-82ee-420b5dafe33b-context.json) |
| `main.bend::offset_line` | 10 | [0499dd30](receipts/perch-parsed-2026-09-26/0499dd30-9799-4626-ad31-d89c76737441.json) | [context](receipts/perch-parsed-2026-09-26/0499dd30-9799-4626-ad31-d89c76737441-context.json) |
| `LAW_REVIEW.md` | 9 | [d310851b](receipts/perch-parsed-2026-09-26/d310851b-459e-4a0a-a861-062f4db1626d.json) | [context](receipts/perch-parsed-2026-09-26/d310851b-459e-4a0a-a861-062f4db1626d-context.json) |

All source targets are in `main.bend`; SHA-256 `83029b603921ea8a978c3f9a424fb256e0737d8041836c2749f8bd1b5e0be12c`. The law packet SHA-256 is `6fcc66fcd55d34ee38b2624f7b8ad41969ceb8f64ceaa7dbb2a1af3a6636fd16`. [Index](receipts/perch-parsed-2026-09-26/index.json) retains exact targets, original `.perch/usage/` paths and working-copy identities. Raw probabilities and context limits are in the linked evidence.

The actual pinned Bend parser accepted each target: `bend-2.0.29-574b6d3-observer-v2`, integration profile `language-pack-1.20-v3+knot-bend-0cd9e831fc413760`. All 14 helper contexts reported `truncated: false`, within limits of 16 helpers, four callers, 12 files and 48 KB. Supplied helper/caller context is from the working copy, not committed substitutes.

Parsing is not type checking or a whole-program call graph. Remote Vec/Base implementations were not fetched by the review adapter. Unresolved records explicitly identify the remote Vec API, Base/builtin names, and local imported datatype references such as `T.Error`/`T.Location`. The parser therefore cannot independently establish Vec native costs or full dependency correctness. The pinned release and deterministic evidence remain the authority for those claims.

This pass deliberately skipped fresh paid checks of unchanged conformance fixtures, mutation copies, benchmarks and calibration controls. `Source.new` is a delegating alias; `Source.maximum` a literal; `file`, `length`, `line_count` metadata projections; `checkpoint` the exact cursor identity. They were not separate paid targets. Other materially relevant implementation helpers were supplied with the selected public operations, with `build`, `search` and `offset_line` also directly targeted. There is no claim that every declaration received a separate request.

## Findings and validation

**Package findings:** confirmed 0, false-positive 0, duplicate 0, unresolved 0. All selected checks completed with nonzero coverage. Broken-probability maxima on implementation units were 50–61%, below their relevant reporting floors; no concrete counterexample was emitted. This is advisory review evidence, not a claim of correctness from low scores.

**Confirmed tooling evidence gap, proposed to coordinator:** the wrapper stores `units` only from `result.units`. Single-declaration CLI results instead carry top-level `name`, line range and `context`; copied wrapper receipts have `units: []` and only the file-level `target`. See the `Source.bounded` provider receipt and its paired CLI/context result above. Preserve top-level single-unit metadata as one unit in the shared wrapper; test both single-unit and fan-out shapes. No shared tooling or log was edited here. During this pass, another owner added an unstaged shared-wrapper fallback `result?.units ?? (result?.context ? [result] : [])`; that concurrent patch was observed but not validated or committed by this chat. Source retains the original run context in its owned result files. The first `Source.locate` context was reconstructed with the same parser and identical source after the interactive live request; it is explicitly labeled reconstructed, not a captured request. The other 14 CLI results were retained directly.

Fresh deterministic check: `scripts/bend-reference packages/source/PROOF.bend --check-only` passed with all terms checked. All 13 uploaded files still match `RELEASE.json` for `0x88d5b48c03f82f217d3a2aa0656744f4`. Existing CPU/JS conformance, eleven semantic mutation kills and scaling receipts have source hashes matching current code. Those unchanged workloads were not rerun. [Verification receipt](receipts/perch-parsed-2026-09-26/verification.json). The audit driver passed `node --check`.

## What changed in this pass

Added this report, the bounded parsed-review driver, and retained provider/context/verification receipts. This is distinct from the earlier whole-file audit in `PERCH_REPORT.md`, which used the former adapter and included fresh controls. No Source implementation, model, proof, test, law packet or package rule changed now. No stronger repair model was invoked because there was no confirmed package defect. No style ranking was invented: this pass contains no competing implementations of one contract.

## Two existing mechanisms worth showing

These excerpts predate this pass; they are not new fixes. Their appeal is the small, explicit state vocabulary and visible symmetry.

`packages/source/main.bend:158–162` separates failure, EOF and consumption in one match. `Source.bump` obtains this result through `Source.peek`, which already checks file identity and bounds; only a real character advances the offset.

```bend
def bumped(c: T.Cursor, r: Result<T.Error,Maybe<Char>>) -> Result<T.Error,T.Cursor & Maybe<Char>>:
  match c r:
    case T.Cursor{id,i} Fail{e}: Fail{e}
    case T.Cursor{id,i} Done{None{}}: Done{(T.Cursor{id,i},None{})}
    case T.Cursor{id,i} Done{Some{ch}}: Done{(T.Cursor{id,(i + 1 : U32)},Some{ch})}
```

`packages/source/main.bend:207–210` expresses each binary-search branch as a replacement of exactly one interval endpoint. With `start[lo] <= position`, the midpoint remains the lower candidate when it is not after the position; otherwise it becomes the exclusive upper bound. `search_step` stops at interval width one, and exhausted search fuel is a separate `BadIndex`, never a successful line.

```bend
def split_search(lo: U32, hi: U32, mid: U32, before: Bool) -> Search:
  match before:
    case True{}: Searching{lo,mid}
    case False{}: Searching{mid,hi}
```

Remaining limits are unchanged: no all-string refinement theorem, no Source GPU execution claim, and no model ranking as correctness evidence. This pass does not resume the paused package campaign. The coherent audit increment is committed using only explicit paths under `packages/source/`; the final handoff supplies its commit ID.
