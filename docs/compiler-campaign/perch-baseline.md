# Compiler Perch structural baseline

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
