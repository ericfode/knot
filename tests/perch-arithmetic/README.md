# Machine-arithmetic controls

Clean, broken and held-out controls for the advisory Perch rule
`bend-machine-arithmetic`. They exist so the rule's question and floor can be
compared before and after an edit; they are not compiler code, are excluded from
repository scans in `perch.yaml`, and are not a gate. Every file passes the pinned
seed (`--check-only`; the proof entry prints `All terms check.`).

| file | role | declarations |
| --- | --- | --- |
| `cases/dev.bend` | fitting set | broken: `free_slots`, `reserve`, `slot`, `bytes_needed`, `fits_page`; clean with arithmetic: `next_random`, `free_slots_guarded`, `next_id`; clean without arithmetic: `on`, `flip`, `main` |
| `cases/heldout.bend` | held out; written before the edited question was scored, scored once | broken: `valid_span`, `row_offset`, `in_grid`, `align_up`; clean with arithmetic: `hash_word`, `distance`, `clamp_page`; clean without arithmetic: `swap`, `head_or`, `main` |
| `cases/proof-laws.bend`, `cases/proof-fills.bend` | law fill, the applicability failure class | `L.flip_twice_on`, `L.flip_once_off` (`{==}` fills, no arithmetic) |

[expectations.json](expectations.json) fixes the labels; [results-2026-09-28.json](results-2026-09-28.json)
holds the scores. Run one file with

```sh
node --env-file=<path to the private Perch .env> scripts/perch-workflow.mjs check tests/perch-arithmetic/cases/dev.bend --rules bend-machine-arithmetic
```

and read `units[].asked[].broken` for the rule (raw probability, below and above the
floor). A live run sends the source to the configured endpoint and uses credits.

## 2026-09-28 comparison (Jev 1.13.0)

| set | old question, floor 0.80 | edited question |
| --- | --- | --- |
| 9 broken declarations | 0.31 to 0.48; none flagged | 0.61 to 0.81; 6 of 9 flagged at the new floor 0.70 |
| 14 clean declarations (6 with arithmetic, 8 without) | 0.43 to 0.76; arithmetic-free ones scored highest | 0.05 to 0.17; none flagged |
| 46 production false positives of the 2026-09-28 review | 0.81 to 0.85 | 0.05 to 0.12 |
| 218 declarations of 7 compiler and research files | not measured | at most 0.57; none at or above 0.60 |

The old question scored arithmetic-free declarations as more likely broken than real
overflow; it lacked the applicability sentence that every other Bend rule has. The
edited question adds that sentence, three concrete violation shapes (unordered
subtraction, sum or product compared against a limit, masked index) and the guard
exemption. The floor moved from 0.80 to 0.70 because the broken controls now
separate from the clean ones by at least 0.44 and no production declaration reaches
0.60. Three broken controls (`slot` 0.65, `row_offset` 0.63, `align_up` 0.63) remain
below the floor; the rule stays advisory (`gate: false`) and this small set is not an
accuracy claim.
