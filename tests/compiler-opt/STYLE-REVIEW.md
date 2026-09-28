# Optimizer review packets

Review round 2 uses the compiler manifest's `interfaces-v1` context policy.
The five optimizer groups retain their complete local dependency inventories.
`selected_files` narrows only which implementations enter a composition in full:

| Group | Complete implementation |
| --- | --- |
| `opt-check` | Core verification, syntax and core datatypes |
| `opt-inline` | Level translation, capture checks and argument binding |
| `opt-fold` | Known cases, field fusion and reusable-let removal |
| `opt-pipeline` | All three passes, their traversal, laws and complete proof entry |
| `opt-wasm` | Optional tail-self-call lowering, syntax and core datatypes |

The existing source checker, emitter and earlier proof entries remain explicit
interfaces in downstream packets. Their full implementations are selected in
their own manifest groups. Each interface retains its full-file hash, imports,
datatypes and referenced signatures. The optimizer pipeline still includes its
complete pass implementations and checked local-law bodies. No compiler file,
declaration or local import is removed from the manifest's coverage obligation.

The source budget stays at 48,000 bytes and encoded declaration states stay
bounded by 60,000 bytes. Interface summaries are marked; they do not establish
the behavior of an omitted implementation. Main's context policy removes the
old file/helper truncation failures without changing these limits or rubric v8.

The files under `fixtures/observers/` are frozen test data, outside the compiler
composition targets. In particular, `deep-input.bend` expands a
literal 64-successor recognizer into a linear family of cases. Splitting that
fixture would change its frozen source and introduce module handling into its
source-language test. Keep its source and near-miss controls unchanged. Its
seed, evaluator and Wasm differentials remain mandatory. Every fixture and entry
wrapper, including this observer, still receives separate file-level preflight
with `--context=interfaces-v1`. The existing observer fits that policy without
splitting or excluding any declaration. The optimizer and its entire corpus
are not treated as one composition.

Reproduce a bounded group offline:

```sh
BEND_NO_TELEMETRY=1 node scripts/perch-style.mjs --preflight \
  --manifest=docs/compiler-campaign/manifest.json --group=opt-pipeline
```

Repeat for `opt-check`, `opt-inline`, `opt-fold` and `opt-wasm`. Each run supplies
`tests/compiler-opt/SPEC.md` as its fixed task through the manifest. The compact
[round-2 receipt](receipts/preflight-review2.json) records the command, selected
files, declaration counts, composition bytes, source hashes and blockers. The
older `preflight*.json` receipts retain their original context-policy meaning.

For a fixture or entry wrapper, use
`--context=interfaces-v1 --task=tests/compiler-opt/SPEC.md FILE.bend` instead of
the manifest options. Run each whole file separately.

The final round-2 preflight passes all five compiler groups and all 29 test
packets, including `review-controls.bend`. Every packet exits 0 with no
truncated declarations, supporting-role gaps, unresolved imports or structural
blockers. The five groups contain 315 declaration obligations, including 163
distinct declarations; repeated collaborators are counted in each group.
The 29 test packets cover 309 declarations. Their largest composition is
17,886 bytes and their largest encoded declaration state is 58,186 bytes.

| Compiler group | Declarations | Composition bytes / 48,000 | Maximum state bytes / 60,000 |
| --- | ---: | ---: | ---: |
| `opt-check` | 69 | 26,690 | 50,121 |
| `opt-inline` | 54 | 16,080 | 24,400 |
| `opt-fold` | 65 | 19,127 | 24,134 |
| `opt-pipeline` | 87 | 41,536 | 56,704 |
| `opt-wasm` | 40 | 17,200 | 50,356 |

The manifest and manifest-mutant controls pass 24 of 24 tests. Both compact
receipts pin 87 input identities, including 12 verified package members, with
no absolute host paths. No compiler or observer source was changed to obtain
these structural results.

The exact requested combined command was also run with an actual argument array:
`node scripts/perch-style.mjs --preflight` followed by every changed Bend file
against `main`, including the then-untracked `review-controls.bend`. This selects
37 files and 439 declarations. It uses the preserved legacy context policy,
because it supplies neither a manifest nor `--context=interfaces-v1`. It exits
3 with 80 truncated contexts, 83 declarations lacking complete role context,
and one unavailable composition: **81 structural blockers**. The composition
requires 186,307 bytes against 48,000. Its unresolved context contains six
collaborators outside the selected group and 86 nonlocal imports. Truncation
reasons overlap: 22 caller/byte-limit, 10 file-limit and 54 helper-limit cases.
The plain command also lacks task context.

Repeating that combined selection with
`--json --task=tests/compiler-opt/SPEC.md` supplies the task but retains the same
81 blockers and exits 3. The [combined receipt](receipts/preflight-combined-review2.json)
retains both command arrays, the plain output, task-qualified summaries and
every blocked or role-limited declaration. These residual aggregate failures
are distinct from the complete bounded packets above; neither result replaces
the other.

Structural availability is not a style rating or a D9 pass. Conceptual
compression, Delight, memetic identity, Anticipation, Payoff and potential
profundity remain unrated; the coordinator owns live review. No provider request
is part of this preflight.
