# Compiler Perch structural baseline

## Context enablement, 2026-09-27

Branch `campaign/perch-context`, compiler base `3a162ab`. The new
[`interfaces-v1` context rule](../perch-style.md#interface-context-rule-interfaces-v1)
leaves all `src/*.bend`, rubric v8, its targets and the 48,000-byte cap unchanged.
The [before receipt](perch-context-before.json.gz) and
[after receipt](perch-context-after.json.gz) use the same compiler source.
The original 317-blocker baseline is preserved below as history.

The current branch contains **30 files and 425 distinct declarations** in
**17 groups**. Before: **374 blockers** (366 truncated obligations, 74 distinct
truncated declarations, and 8 unavailable compositions), 475 role-limited
obligations, seven groups over the byte bound. After: **0 blockers, 0 truncated
contexts, 0 role-limited obligations, 0 unavailable compositions, 0 groups over
the bound and 0 unresolved published imports**. All 425 declarations are covered.

Group declaration obligations change from 2,425 to 945 because seven groups
now select their own full mechanism, keeping downstream collaborators as
interfaces. The original closed local file inventories are retained unchanged;
every compiler file remains selected in full in at least one group. Sources
are not shortened inside a selected mechanism. This is an explicit group
boundary change, not a reduction in whole-compiler declaration coverage.

There were **0 provider requests**. Conceptual compression, Delight, memetic
identity, Anticipation and Payoff remain **unrated**. These receipts qualify
context assembly only; they establish no style pass or semantic acceptance.

```sh
export BEND_NO_TELEMETRY=1
node scripts/perch-style.mjs --preflight \
  --manifest=docs/compiler-campaign/manifest.json \
  --package-store="$HOME/.bend/lib" --output=.local/compiler-context-next.json.gz
```

Choose a fresh output path. The explicit existing package store is necessary on
this checkout: `packages/output_builder/bytes.bend` has changed since publication
and correctly fails its release digest. Its installed immutable 12-file closure
verifies to `0xc409b77d3230ca33374caf6b0993f0cb`. No package was downloaded,
installed, copied into the repository, or substituted without verification.
Without a verified store, this dependency remains unresolved with
`package-member-hash-mismatch`; zero unresolved imports is conditional on the
explicit verified store in the command above. Gate `perch-context` supplies the
gate runner's private frozen copy of that same installed store.

### Before and after by group

Each arrow is the same compiler snapshot under the old versus new context and
selection policy. Composition bytes are actual UTF-8 source bytes, including
interface markers and hashes; the cap is 48,000 for both. All tasks fit 16,000
bytes. The selected-file lists and per-file representations are in the manifest
and raw receipt. Each group now has zero unresolved composition references.

| Group | Declaration obligations | Truncated | Role-limited | Composition bytes | Composition |
| --- | ---: | ---: | ---: | ---: | --- |
| `syntax-core` | 33 → 33 | 11 → 0 | 11 → 0 | 5,156 → 5,156 | Available → Available |
| `frontend-lexing` | 27 → 27 | 2 → 0 | 2 → 0 | 7,112 → 7,112 | Available → Available |
| `frontend-parsing` | 41 → 41 | 5 → 0 | 5 → 0 | 19,654 → 19,654 | Available → Available |
| `diagnostics` | 45 → 45 | 11 → 0 | 11 → 0 | 11,027 → 11,027 | Available → Available |
| `catalog` | 65 → 65 | 13 → 0 | 13 → 0 | 17,844 → 17,844 | Available → Available |
| `scope-patterns` | 99 → 99 | 16 → 0 | 16 → 0 | 29,152 → 29,152 | Available → Available |
| `checking` | 134 → 134 | 22 → 0 | 22 → 0 | 47,903 → 47,903 | Available → Available |
| `evaluation` | 63 → 63 | 16 → 0 | 16 → 0 | 18,063 → 18,063 | Available → Available |
| `wasm-codec` | 30 → 30 | 1 → 0 | 10 → 0 | 5,609 → 6,343 | Unavailable → Available |
| `wasm-emission` | 190 → 89 | 30 → 0 | 62 → 0 | 67,507 → 27,393 | Unavailable → Available |
| `driver-pipeline` | 313 → 51 | 73 → 0 | 105 → 0 | 119,433 → 23,245 | Unavailable → Available |
| `frontend-laws` | 69 → 69 | 6 → 0 | 6 → 0 | 26,496 → 26,496 | Available → Available |
| `checker-laws` | 198 → 38 | 28 → 0 | 28 → 0 | 73,388 → 15,547 | Unavailable → Available |
| `runtime-laws` | 253 → 55 | 33 → 0 | 42 → 0 | 90,852 → 25,065 | Unavailable → Available |
| `catalog-laws` | 263 → 42 | 33 → 0 | 42 → 0 | 92,594 → 24,026 | Unavailable → Available |
| `fields-laws` | 285 → 32 | 33 → 0 | 42 → 0 | 96,194 → 19,579 | Unavailable → Available |
| `recursion-laws` | 317 → 32 | 33 → 0 | 42 → 0 | 102,139 → 17,267 | Unavailable → Available |

### Context classification and limits

No unavoidable truncations remain on this snapshot, so the remaining-case list
is empty. Overflow bodies are explicitly classified as signatures, with their
type dependencies closed and their actual byte cost retained. The receipt has
per-declaration classifications; these counts include repeated group obligations:

- `context-caller-interface`: 162 summaries.
- `context-helper-interface`: 1147 summaries.
- `context-state-interface`: 4 summaries.

Interfaces contain full datatypes and referenced signatures, not implementations.
Earlier unselected proof-entry chains supply interfaces, not proof execution.
The unchanged deterministic gates and live reviews are still required. The
largest group (`checking`) is 47,903 bytes; an additional 98 bytes would exceed
the cap, so later changes may require another explicit group boundary.

The new [verification record](perch-context-verification.md) gives exact gate
counts, the four killed mutants and the fixed controls. The next increment can
run live semantic/style qualification with this context policy and verified
package store. A context change invalidates prior request identities; legacy
invocations deliberately keep their historical policy and controls.

### New receipt identities

- `docs/compiler-campaign/manifest.json` SHA-256: `cc311239670ce84e7111df80ff590a1aa6d74493d826021495479080ccb212db`.
- `perch-style.json` SHA-256: `b0747948ceadd3c10f48634adeccc2c880d944a9e63b1f6906d6121a68f4d693`.
- `scripts/perch-style.mjs` SHA-256: `de9559f86e80bae8844cf8fc81f62fa9e656fa1697dd1951a7a08894345ec61f`.
- `scripts/perch-bend-context.mjs` SHA-256: `d1968e24a167e2f818d7e28fe1eee296054dddeb19db98cb0c89e4fab8c9c935`.
- `scripts/perch-context-interfaces.mjs` SHA-256: `0b26b1cf178f78fd6cb5af96529f8d22fe91696de7cb32c2cd0e4332bd1de18e`.
- `docs/compiler-campaign/perch-context-before.json.gz` SHA-256: `3841bdffd6c8f37e3f5d132fe4d11f74597aa971b4ba516cb163e72e0964928f`.
- `docs/compiler-campaign/perch-context-after.json.gz` SHA-256: `76f210beae0f5dd92a9e9eaa5ce6ada3c72b47767c8313bc72178df4392ca633`.

## Historical baseline: campaign/perch-manifest

Recorded 2026-09-27 on `campaign/perch-manifest`, based on compiler commit `185b7d5`.

The manifest covers all **28 compiler source files and 359 distinct parsed declarations** in **16 mechanisms**. Local imports are closed in every group, including earlier proof-entry imports. Shared files produce **1,972 group/declaration obligations**. No Bend source, rubric text or target changed.

Offline preflight exits **3**: **317 structural blockers = 310 truncated declaration contexts + 7 unavailable required compositions**. There are **400 role-limited obligations** (95 distinct declarations); role gaps retain the leading targets and are not an additional blocker count. There are 68 distinct truncated declarations. All 16 groups contain at least one truncation, so none is structurally ready for a full style pass.

There were **0 provider requests**. Conceptual compression, Delight, memetic identity, Anticipation and Payoff are **unrated**; no probability distributions or style pass are claimed. Semantic acceptance remains separate.

## Reproduce

```sh
export BEND_NO_TELEMETRY=1
node scripts/perch-style.mjs --preflight \
  --manifest=docs/compiler-campaign/manifest.json \
  --output=.local/compiler-perch-preflight.json.gz
```

Choose a new output path: the tool refuses to overwrite evidence. The tracked [raw receipt](perch-preflight.json.gz) contains every declaration, role-context gap, composition diagnostic and source/task/manifest/rubric hash. Its source snapshot is the baseline identity; later compiler increments require a new preflight. The [verification record](perch-verification.md) gives deterministic gate counts and mutation witnesses.

## Per-group results

Truncation columns count file-cap / helper-cap / caller-or-byte-cap reasons. A declaration may contribute to multiple reason counts. All task contracts fit the 16,000-byte task bound. Composition bytes count complete selected and known collaborator sources, before request encoding.

| Group | Declarations | Truncated (file / helper / other) | Role-limited | Composition bytes / 48,000 | Composition |
| --- | ---: | ---: | ---: | ---: | --- |
| `syntax-core` | 33 | 11 (10 / 0 / 1) | 11 | 5,156 | Available |
| `frontend-lexing` | 27 | 2 (1 / 0 / 1) | 2 | 7,112 | Available |
| `frontend-parsing` | 37 | 4 (2 / 0 / 2) | 4 | 18,156 | Available |
| `diagnostics` | 45 | 11 (10 / 0 / 1) | 11 | 11,027 | Available |
| `catalog` | 65 | 13 (12 / 0 / 1) | 13 | 17,844 | Available |
| `scope-patterns` | 97 | 15 (14 / 0 / 1) | 15 | 28,479 | Available |
| `checking` | 132 | 21 (15 / 5 / 1) | 21 | 47,023 | Available |
| `evaluation` | 63 | 16 (12 / 0 / 4) | 16 | 18,063 | Available |
| `wasm-codec` | 30 | 1 (0 / 0 / 1) | 10 | 5,609 | published hash import |
| `wasm-emission` | 172 | 25 (18 / 6 / 1) | 52 | 59,330 | published hash import; over byte bound |
| `driver-pipeline` | 291 | 67 (24 / 37 / 6) | 94 | 109,758 | published hash import; over byte bound |
| `frontend-laws` | 53 | 5 (3 / 0 / 2) | 5 | 23,172 | Available |
| `checker-laws` | 180 | 26 (18 / 6 / 2) | 26 | 69,184 | over byte bound |
| `runtime-laws` | 235 | 31 (20 / 6 / 5) | 40 | 86,648 | published hash import; over byte bound |
| `catalog-laws` | 245 | 31 (20 / 6 / 5) | 40 | 88,390 | published hash import; over byte bound |
| `fields-laws` | 267 | 31 (20 / 6 / 5) | 40 | 91,990 | published hash import; over byte bound |

Nine compositions have complete available context. Six groups exceed the byte bound. Seven compositions are unavailable because the oversized groups overlap the six groups with unresolved published imports. Every listed local import is present; the unresolved composition reason is exclusively `nonlocal-import`, with 27 reference occurrences in codec/runtime-law families and 60 in emission/driver families.

## Structural causes and next increment

- **Datatype context:** the existing one-file datatype cap truncates required imported types. Examples include `src/core.bend::Constructor`, `Datatype`, `Parameter` and `Term`. Manifest membership does not expand declaration context.
- **Helper/caller context:** the existing 48-helper and four-caller bounds truncate declaration review. Examples include `src/check.bend::run`, `function_body`, `functions`, `resolved` and `check`; caller-or-byte limits affect `src/syntax.bend::Token` and `src/eval.bend::Value`. The receipt preserves the actual limit classification.
- **Published imports:** `src/wasm-bytes.bend` and `src/wasm.bend` use `0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend`. Style context currently follows relative local imports only. The next resolver increment needs a hash-verified local package closure; this run fetched nothing.
- **Whole-file composition size:** checking alone fits at 47,023 bytes. Emission reaches 59,330 bytes; the complete driver/CLI pipeline reaches 109,758 bytes. The checker, runtime, catalog and fields proof families include their earlier complete proof-entry chain and reach 69,184–91,990 bytes. These groups cannot fit under the existing whole-file closure rule. Source modularization or a separately specified composition-context mechanism is needed before qualification; the manifest retains these obligations and the 48,000-byte cap.

Resolve context limits and composition size while preserving the deterministic gates. Then the coordinator can run targeted semantic review and live manifest style review. A successful `--group=NAME` run qualifies that selection only; only an unfiltered run can set `manifest_fully_qualified`.

## Identities

- Manifest SHA-256: `222e720b6d15a5647e7892c12e3ccf3b254a746826c7281e838326ce2cb895db`.
- Rubric v8 SHA-256: `b0747948ceadd3c10f48634adeccc2c880d944a9e63b1f6906d6121a68f4d693`.
- Tool SHA-256: `7f5b13f26870a06e852131d8d4492cf4dc52f81288149be28522baba40820c87`.
- Compressed receipt SHA-256: `47e25b8def9e0d77ad03b30437997ced0ef2debb1b445b57e27527462596d9e3`.
