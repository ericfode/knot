# Per-declaration style results, changed files (rubric v8, Jev `jev-1.13.0`)

Generated from the live style reports of 2026-09-28 (see [README.md](README.md)). Cell = target status and probability (percent) at the declaration's role-scaled target level: ✓ meets, ✗ below target, ? uncertain, – unavailable. `Δ` after a declaration marks a range that overlaps a change in `185b7d5..a6367eb9`; every declaration of a newly added file is Δ. Role: lead / supp / unc (uncertain roles are held to level 3). `all` = all five applicable targets are met. These are advisory taste statuses, not defects, and a file appears once per manifest group that selects it in full (its context in that group differs). Declarations of unchanged context files that the same groups also reviewed are counted in the README but not listed here.

## Group `recursion-laws`

Composition: below_target (highly_memetic ✓90, anticipation ✓92, payoff ✗8). Potential profundity: low (4% relevant).

### `src/recursion-LAWS.bend`: 16 declarations, 16 changed, 6 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `root_fields_are_smaller`:10 Δ | law | lead | ✓85 | ✓74 | ✗36 | ?51 | ✗38 | ✗ |
| `descendant_fields_are_smaller`:15 Δ | law | unc | ✓86 | ✓74 | ✗29 | ?55 | ?46 | ✗ |
| `unrelated_fields_stay_unmarked`:19 Δ | law | supp | ✓93 | ✓82 | ✓93 | ✓96 | ✓83 | ✓ |
| `marked_reference_descends`:23 Δ | law | unc | ✓94 | ✓76 | ✗21 | ?58 | ✓75 | ✗ |
| `root_reference_does_not_descend`:29 Δ | law | supp | ✓93 | ✓80 | ✓91 | ✓96 | ✓86 | ✓ |
| `rebuilt_argument_does_not_descend`:35 Δ | law | unc | ✓86 | ✓64 | ✗24 | ?50 | ?54 | ✗ |
| `computed_argument_does_not_descend`:44 Δ | law | supp | ✓89 | ✓74 | ✓91 | ✓94 | ✓76 | ✓ |
| `empty_call_does_not_descend`:52 Δ | law | supp | ✓93 | ✓80 | ✓88 | ✓99 | ✓90 | ✓ |
| `later_argument_cannot_establish_descent`:56 Δ | law | supp | ✓92 | ✓79 | ✓92 | ✓96 | ✓84 | ✓ |
| `local_binding_preserves_descent`:61 Δ | law | supp | ✓94 | ✓73 | ✓87 | ✓95 | ✓91 | ✓ |
| `opening_root_records_descent`:73 Δ | law | unc | ✓82 | ✓81 | ?53 | ?52 | ✓79 | ✗ |
| `opening_descendant_records_descent`:81 Δ | law | unc | ✓84 | ✓79 | ?50 | ?56 | ✓81 | ✗ |
| `descending_self_call_is_checked`:89 Δ | law | lead | ✓76 | ✓67 | ?52 | ?51 | ?51 | ✗ |
| `nondecreasing_self_call_is_unsupported`:97 Δ | law | lead | ✓81 | ✓69 | ?50 | ✓66 | ✓73 | ✗ |
| `earlier_call_needs_no_descent`:106 Δ | law | unc | ✓72 | ✓66 | ✗38 | ✗36 | ✗32 | ✗ |
| `recursive_evaluation_exhaustion`:115 Δ | law | unc | ?53 | ?49 | ✗22 | ?51 | ✗21 | ✗ |

### `src/recursion-PROOF.bend`: 16 declarations, 16 changed, 7 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `L.root_fields_are_smaller`:7 Δ | law_fill | supp | ✓76 | ✓72 | ✓92 | ✓76 | ✓62 | ✓ |
| `L.descendant_fields_are_smaller`:8 Δ | law_fill | supp | ✓73 | ✓62 | ✓90 | ✓72 | ?53 | ✗ |
| `L.unrelated_fields_stay_unmarked`:9 Δ | law_fill | supp | ✓72 | ✓72 | ✓86 | ✓73 | ✓62 | ✓ |
| `L.marked_reference_descends`:10 Δ | law_fill | supp | ✓86 | ✓69 | ✓86 | ✓86 | ✓60 | ✓ |
| `L.root_reference_does_not_descend`:11 Δ | law_fill | supp | ✓74 | ✓68 | ✓84 | ✓85 | ✓62 | ✓ |
| `L.rebuilt_argument_does_not_descend`:12 Δ | law_fill | supp | ✓72 | ✓66 | ✓90 | ✓84 | ?57 | ✗ |
| `L.computed_argument_does_not_descend`:13 Δ | law_fill | supp | ✓69 | ✓61 | ✓92 | ✓90 | ?53 | ✗ |
| `L.empty_call_does_not_descend`:14 Δ | law_fill | supp | ✓83 | ✓67 | ✓83 | ✓89 | ✓69 | ✓ |
| `L.later_argument_cannot_establish_descent`:15 Δ | law_fill | supp | ✓60 | ✓63 | ✓88 | ✓70 | ?50 | ✗ |
| `L.local_binding_preserves_descent`:16 Δ | law_fill | supp | ✓77 | ✓62 | ✓85 | ✓85 | ?55 | ✗ |
| `L.opening_root_records_descent`:17 Δ | law_fill | supp | ✓76 | ✓85 | ✓95 | ✓90 | ✓72 | ✓ |
| `L.opening_descendant_records_descent`:18 Δ | law_fill | supp | ✓75 | ✓83 | ✓93 | ✓88 | ✓70 | ✓ |
| `L.descending_self_call_is_checked`:19 Δ | law_fill | unc | ✓68 | ✓67 | ?50 | ?45 | ?42 | ✗ |
| `L.nondecreasing_self_call_is_unsupported`:20 Δ | law_fill | unc | ✓72 | ✓63 | ?42 | ?41 | ?41 | ✗ |
| `L.earlier_call_needs_no_descent`:21 Δ | law_fill | supp | ✗31 | ✗37 | ✓78 | ✓61 | ✗19 | ✗ |
| `L.recursive_evaluation_exhaustion`:24 Δ | law_fill | supp | ✗27 | ?46 | ✓77 | ✓64 | ✗23 | ✗ |

## Group `frontend-parsing`

Composition: below_target (highly_memetic ✓76, anticipation ✗39, payoff ?57). Potential profundity: unavailable (task_byte_limit).

### `src/parse.bend`: 22 declarations, 5 changed, 12 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Parsed`:4 | datatype | lead | ?50 | ✓68 | ✗13 | ✗36 | ✗12 | ✗ |
| `Mode`:7 | datatype | lead | ✗36 | ✓80 | ✗25 | ?46 | ✗22 | ✗ |
| `invalid`:27 | definition | supp | ✓92 | ?46 | ✗40 | ✓88 | ✓96 | ✗ |
| `unsupported`:30 | definition | supp | ✓94 | ?47 | ✓62 | ✓99 | ✓99 | ✗ |
| `starts`:33 Δ | definition | supp | ✓90 | ✓75 | ✓68 | ✓95 | ✓95 | ✓ |
| `scrutinee`:38 Δ | definition | supp | ✓83 | ✓71 | ✓63 | ✓88 | ✓91 | ✓ |
| `then`:43 | definition | supp | ✓92 | ✓82 | ✓92 | ✓95 | ✓98 | ✓ |
| `prepend`:49 | definition | supp | ✓94 | ✓77 | ✓69 | ✓95 | ✓98 | ✓ |
| `wrap_call`:54 | definition | supp | ✓95 | ✓89 | ✓94 | ✓94 | ✓100 | ✓ |
| `wrap_type`:63 | definition | supp | ✓88 | ✓79 | ✓80 | ✓97 | ✓98 | ✓ |
| `wrap_function`:69 | definition | supp | ✓91 | ✓83 | ✓85 | ✓99 | ✓100 | ✓ |
| `wrap_match`:75 | definition | supp | ✓91 | ✓80 | ✓89 | ✓99 | ✓99 | ✓ |
| `expect`:81 | definition | supp | ✓95 | ✓84 | ✓89 | ✓99 | ✓100 | ✓ |
| `parameter_end`:88 | definition | supp | ✓68 | ✓61 | ✓81 | ✓94 | ✓93 | ✓ |
| `parameter_parts`:95 | definition | unc | ✗25 | ?43 | ✗13 | ✗07 | ✗17 | ✗ |
| `parameter`:105 | definition | supp | ?43 | ✓75 | ✓89 | ✓92 | ✓95 | ✗ |
| `template_parameter`:113 Δ | definition | supp | ✓62 | ✓69 | ✓83 | ✓96 | ✓93 | ✓ |
| `body_end`:120 | definition | supp | ✓87 | ✓71 | ✓84 | ✓95 | ✓96 | ✓ |
| `reply`:127 Δ | definition | supp | ✗40 | ?48 | ✓76 | ?56 | ✓83 | ✗ |
| `term_failure`:138 | definition | supp | ✗35 | ✗40 | ✓81 | ✓94 | ✓97 | ✗ |
| `run`:148 Δ | definition | lead | ✗31 | ✓79 | ✓60 | ✓73 | ✓73 | ✗ |
| `parse`:320 | definition | supp | ✗40 | ✓84 | ✓98 | ✓94 | ✓90 | ✗ |

## Group `frontend-laws`

Composition: below_target (highly_memetic ✓86, anticipation ?59, payoff ✗20). Potential profundity: unavailable (task_byte_limit).

### `src/LAWS.bend`: 16 declarations, 12 changed, 0 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `empty_source`:7 | law | unc | ?54 | ✓72 | ✗31 | ✓77 | ✓64 | ✗ |
| `word_source`:11 | law | supp | ?56 | ✓67 | ✓77 | ✓78 | ✓67 | ✗ |
| `no_character_budget`:15 | law | lead | ✓72 | ✓72 | ✗26 | ✓62 | ✓82 | ✗ |
| `no_parser_budget`:20 | law | unc | ?49 | ✓73 | ✗34 | ?53 | ✓62 | ✗ |
| `generic_header`:25 Δ | law | unc | ?53 | ✓72 | ✗35 | ✗35 | ✗32 | ✗ |
| `multiple_scrutinees`:31 Δ | law | lead | ?47 | ✓62 | ✗39 | ✗25 | ✗29 | ✗ |
| `template_binder`:37 Δ | law | lead | ?51 | ✓62 | ✗36 | ✗26 | ✗21 | ✗ |
| `nonleading_template_binder`:43 Δ | law | unc | ✓63 | ✓63 | ✗23 | ✗22 | ✗24 | ✗ |
| `destructuring_binding`:50 Δ | law | lead | ?58 | ?49 | ✗16 | ✗38 | ✗37 | ✗ |
| `equality_is_not_binding`:58 Δ | law | lead | ✓63 | ?51 | ✗18 | ✗35 | ?41 | ✗ |
| `arrow_is_not_binding`:65 Δ | law | lead | ✓65 | ?59 | ✗18 | ?43 | ?44 | ✗ |
| `parameter_type_application`:72 Δ | law | lead | ✗32 | ?45 | ✗18 | ✗26 | ✗28 | ✗ |
| `return_type_application`:78 Δ | law | unc | ?52 | ✓65 | ✗38 | ✗32 | ?42 | ✗ |
| `binding_type_application`:85 Δ | law | unc | ?49 | ✓66 | ✗30 | ✗36 | ✗33 | ✗ |
| `local_import`:91 Δ | law | supp | ?50 | ✓71 | ✓90 | ✓77 | ✓69 | ✗ |
| `hash_import`:97 Δ | law | supp | ?53 | ✓65 | ✓83 | ✓66 | ✓64 | ✗ |

### `src/parse.bend`: 22 declarations, 5 changed, 12 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Parsed`:4 | datatype | lead | ?50 | ✓68 | ✗13 | ✗36 | ✗12 | ✗ |
| `Mode`:7 | datatype | lead | ✗36 | ✓80 | ✗25 | ?46 | ✗22 | ✗ |
| `invalid`:27 | definition | supp | ✓92 | ?46 | ✗40 | ✓88 | ✓96 | ✗ |
| `unsupported`:30 | definition | supp | ✓94 | ?47 | ✓62 | ✓99 | ✓99 | ✗ |
| `starts`:33 Δ | definition | supp | ✓90 | ✓75 | ✓68 | ✓95 | ✓95 | ✓ |
| `scrutinee`:38 Δ | definition | supp | ✓83 | ✓71 | ✓63 | ✓88 | ✓91 | ✓ |
| `then`:43 | definition | supp | ✓92 | ✓82 | ✓92 | ✓95 | ✓98 | ✓ |
| `prepend`:49 | definition | supp | ✓94 | ✓77 | ✓69 | ✓95 | ✓98 | ✓ |
| `wrap_call`:54 | definition | supp | ✓95 | ✓89 | ✓94 | ✓94 | ✓100 | ✓ |
| `wrap_type`:63 | definition | supp | ✓88 | ✓79 | ✓80 | ✓97 | ✓98 | ✓ |
| `wrap_function`:69 | definition | supp | ✓91 | ✓83 | ✓85 | ✓99 | ✓100 | ✓ |
| `wrap_match`:75 | definition | supp | ✓91 | ✓80 | ✓89 | ✓99 | ✓99 | ✓ |
| `expect`:81 | definition | supp | ✓95 | ✓84 | ✓89 | ✓99 | ✓100 | ✓ |
| `parameter_end`:88 | definition | supp | ✓68 | ✓61 | ✓81 | ✓94 | ✓93 | ✓ |
| `parameter_parts`:95 | definition | unc | ✗25 | ?43 | ✗13 | ✗07 | ✗17 | ✗ |
| `parameter`:105 | definition | supp | ?43 | ✓75 | ✓89 | ✓92 | ✓95 | ✗ |
| `template_parameter`:113 Δ | definition | supp | ✓62 | ✓69 | ✓83 | ✓96 | ✓93 | ✓ |
| `body_end`:120 | definition | supp | ✓87 | ✓71 | ✓84 | ✓95 | ✓96 | ✓ |
| `reply`:127 Δ | definition | supp | ✗40 | ?48 | ✓76 | ?56 | ✓83 | ✗ |
| `term_failure`:138 | definition | supp | ✗35 | ✗40 | ✓81 | ✓94 | ✓97 | ✗ |
| `run`:148 Δ | definition | lead | ✗31 | ✓79 | ✓60 | ✓73 | ✓73 | ✗ |
| `parse`:320 | definition | supp | ✗40 | ✓84 | ✓98 | ✓94 | ✓90 | ✗ |

### `src/PROOF.bend`: 16 declarations, 12 changed, 0 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `L.empty_source`:6 | law_fill | supp | ✗09 | ✗28 | ?49 | ✓78 | ✗06 | ✗ |
| `L.word_source`:11 | law_fill | unc | ✗09 | ✗24 | ✗15 | ✓61 | ✗04 | ✗ |
| `L.no_character_budget`:16 | law_fill | supp | ✗12 | ✗28 | ?55 | ✓79 | ✗13 | ✗ |
| `L.no_parser_budget`:19 | law_fill | supp | ✗19 | ✗35 | ?47 | ✓75 | ✗11 | ✗ |
| `L.generic_header`:22 Δ | law_fill | supp | ✗20 | ?48 | ✓63 | ?52 | ✗19 | ✗ |
| `L.multiple_scrutinees`:25 Δ | law_fill | unc | ✗14 | ✗36 | ✗29 | ?50 | ✗12 | ✗ |
| `L.template_binder`:28 Δ | law_fill | unc | ✗15 | ✗33 | ✗28 | ✗35 | ✗10 | ✗ |
| `L.nonleading_template_binder`:31 Δ | law_fill | unc | ✗18 | ✗36 | ✗18 | ?49 | ✗07 | ✗ |
| `L.destructuring_binding`:34 Δ | law_fill | unc | ✓63 | ✓61 | ✗17 | ?50 | ?51 | ✗ |
| `L.equality_is_not_binding`:42 Δ | law_fill | lead | ✗08 | ✗30 | ✗16 | ✓74 | ✗08 | ✗ |
| `L.arrow_is_not_binding`:45 Δ | law_fill | lead | ✗06 | ✗24 | ✗13 | ✓69 | ✗04 | ✗ |
| `L.parameter_type_application`:48 Δ | law_fill | lead | ✗14 | ✗37 | ✗24 | ?53 | ✗08 | ✗ |
| `L.return_type_application`:51 Δ | law_fill | unc | ✗15 | ✗37 | ✗31 | ?44 | ✗10 | ✗ |
| `L.binding_type_application`:54 Δ | law_fill | unc | ✗19 | ✗37 | ✗23 | ?49 | ✗14 | ✗ |
| `L.local_import`:57 Δ | law_fill | supp | ✗23 | ?42 | ?56 | ?55 | ✗18 | ✗ |
| `L.hash_import`:60 Δ | law_fill | supp | ✗21 | ?41 | ?54 | ?54 | ✗16 | ✗ |

## Group `scope-patterns`

Composition: uncertain (highly_memetic ✓92, anticipation ✓87, payoff ?46). Potential profundity: low (18% relevant).

### `src/scope.bend`: 24 declarations, 10 changed, 14 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Scope`:5 Δ | datatype | lead | ✓68 | ✓76 | ✗23 | ?46 | ✗16 | ✗ |
| `contains`:8 | definition | supp | ✓92 | ✓75 | ✓73 | ✓98 | ✓94 | ✓ |
| `descendants`:14 Δ | definition | unc | ✓84 | ✓74 | ✗15 | ?45 | ✗27 | ✗ |
| `descends`:18 Δ | definition | supp | ✓91 | ✓75 | ✓67 | ✓94 | ✓89 | ✓ |
| `sequential`:25 | definition | lead | ✓78 | ✓80 | ?44 | ✓84 | ✗40 | ✗ |
| `alternatives`:32 | definition | lead | ✓71 | ?53 | ✗29 | ?52 | ✗19 | ✗ |
| `remove`:37 | definition | supp | ✓93 | ✓78 | ✓88 | ✓97 | ✓91 | ✓ |
| `find`:43 | definition | unc | ✓85 | ✓78 | ✗09 | ✗15 | ✗14 | ✗ |
| `lookup`:51 Δ | definition | supp | ✓60 | ✓68 | ✓92 | ✓96 | ✓90 | ✓ |
| `occurrence`:55 | definition | supp | ✓83 | ✓70 | ✓88 | ✓81 | ✓93 | ✓ |
| `reference`:63 Δ | definition | supp | ✓87 | ✓70 | ✓89 | ✓92 | ✓90 | ✓ |
| `live_scope`:68 Δ | definition | supp | ✓98 | ✓66 | ?55 | ✓88 | ✓78 | ✗ |
| `extend`:72 Δ | definition | supp | ✓92 | ?58 | ✓76 | ✓91 | ✓81 | ✗ |
| `set_known`:77 | definition | supp | ✓93 | ✓82 | ✓96 | ✓88 | ✓98 | ✓ |
| `refine`:85 | definition | supp | ✓92 | ✓87 | ✓96 | ✓91 | ✓98 | ✓ |
| `after`:89 | definition | supp | ✓88 | ✓87 | ✓87 | ✓92 | ✓95 | ✓ |
| `levels`:95 | definition | supp | ✓93 | ✓77 | ✓74 | ✓97 | ✓93 | ✓ |
| `find_level`:100 | definition | supp | ✓85 | ✓67 | ✓74 | ✓87 | ✓81 | ✓ |
| `replace`:108 | definition | supp | ✓92 | ✓81 | ✓94 | ✓92 | ✓93 | ✓ |
| `remove_fields`:111 | definition | supp | ✓84 | ✓65 | ✓83 | ✓93 | ✓84 | ✓ |
| `branch`:116 Δ | definition | lead | ✓78 | ✓88 | ?41 | ?44 | ?42 | ✗ |
| `parameters`:120 Δ | definition | lead | ✓87 | ✓74 | ✗12 | ?45 | ✗16 | ✗ |
| `matchable`:126 Δ | definition | supp | ✓77 | ✓66 | ✓91 | ✓92 | ✓92 | ✓ |
| `scrutinee`:134 | definition | supp | ?55 | ✓69 | ✓92 | ✓94 | ✓86 | ✗ |

### `src/patterns.bend`: 10 declarations, 3 changed, 6 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Fields`:7 | datatype | lead | ✓66 | ✓66 | ?45 | ✗38 | ✗26 | ✗ |
| `quantity`:10 | definition | supp | ✓71 | ✓69 | ✓92 | ✓77 | ✓96 | ✓ |
| `add`:14 Δ | definition | supp | ✓77 | ✓60 | ✓91 | ✓68 | ✓89 | ✓ |
| `binder`:21 | definition | supp | ✓71 | ✓66 | ✓94 | ✓93 | ✓83 | ✓ |
| `prepend`:29 | definition | supp | ✓89 | ✓69 | ✓90 | ✓96 | ✓95 | ✓ |
| `fields`:33 | definition | lead | ✓69 | ✓72 | ?58 | ?47 | ?52 | ✗ |
| `value`:47 | definition | supp | ✓82 | ✓73 | ✓90 | ✓92 | ✓90 | ✓ |
| `finish`:52 Δ | definition | supp | ✓66 | ✓76 | ✓96 | ✓84 | ✓90 | ✓ |
| `open_fields`:60 | definition | unc | ✓61 | ✓75 | ?46 | ✗40 | ?48 | ✗ |
| `branch`:65 Δ | definition | lead | ✓63 | ✓76 | ?48 | ✗39 | ?50 | ✗ |

## Group `checking`

Composition: uncertain (highly_memetic ✓88, anticipation ✓86, payoff ?49). Potential profundity: low (18% relevant).

### `src/scope.bend`: 24 declarations, 10 changed, 14 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Scope`:5 Δ | datatype | lead | ✓68 | ✓76 | ✗23 | ?46 | ✗16 | ✗ |
| `contains`:8 | definition | supp | ✓92 | ✓75 | ✓73 | ✓98 | ✓94 | ✓ |
| `descendants`:14 Δ | definition | unc | ✓84 | ✓74 | ✗15 | ?45 | ✗27 | ✗ |
| `descends`:18 Δ | definition | supp | ✓91 | ✓75 | ✓67 | ✓94 | ✓89 | ✓ |
| `sequential`:25 | definition | lead | ✓78 | ✓80 | ?44 | ✓84 | ✗40 | ✗ |
| `alternatives`:32 | definition | lead | ✓71 | ?53 | ✗29 | ?52 | ✗19 | ✗ |
| `remove`:37 | definition | supp | ✓93 | ✓78 | ✓88 | ✓97 | ✓91 | ✓ |
| `find`:43 | definition | unc | ✓85 | ✓78 | ✗09 | ✗15 | ✗14 | ✗ |
| `lookup`:51 Δ | definition | supp | ✓60 | ✓68 | ✓92 | ✓96 | ✓90 | ✓ |
| `occurrence`:55 | definition | supp | ✓83 | ✓70 | ✓88 | ✓81 | ✓93 | ✓ |
| `reference`:63 Δ | definition | supp | ✓87 | ✓70 | ✓89 | ✓92 | ✓90 | ✓ |
| `live_scope`:68 Δ | definition | supp | ✓98 | ✓66 | ?55 | ✓88 | ✓78 | ✗ |
| `extend`:72 Δ | definition | supp | ✓92 | ?58 | ✓76 | ✓91 | ✓81 | ✗ |
| `set_known`:77 | definition | supp | ✓93 | ✓82 | ✓96 | ✓88 | ✓98 | ✓ |
| `refine`:85 | definition | supp | ✓92 | ✓87 | ✓96 | ✓91 | ✓98 | ✓ |
| `after`:89 | definition | supp | ✓88 | ✓87 | ✓87 | ✓92 | ✓95 | ✓ |
| `levels`:95 | definition | supp | ✓93 | ✓77 | ✓74 | ✓97 | ✓93 | ✓ |
| `find_level`:100 | definition | supp | ✓85 | ✓67 | ✓74 | ✓87 | ✓81 | ✓ |
| `replace`:108 | definition | supp | ✓92 | ✓81 | ✓94 | ✓92 | ✓93 | ✓ |
| `remove_fields`:111 | definition | supp | ✓84 | ✓65 | ✓83 | ✓93 | ✓84 | ✓ |
| `branch`:116 Δ | definition | lead | ✓78 | ✓88 | ?41 | ?44 | ?42 | ✗ |
| `parameters`:120 Δ | definition | lead | ✓87 | ✓74 | ✗12 | ?45 | ✗16 | ✗ |
| `matchable`:126 Δ | definition | supp | ✓77 | ✓66 | ✓91 | ✓92 | ✓92 | ✓ |
| `scrutinee`:134 | definition | supp | ?55 | ✓69 | ✓92 | ✓94 | ✓86 | ✗ |

### `src/patterns.bend`: 10 declarations, 3 changed, 6 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Fields`:7 | datatype | lead | ✓66 | ✓66 | ?45 | ✗38 | ✗26 | ✗ |
| `quantity`:10 | definition | supp | ✓71 | ✓69 | ✓92 | ✓77 | ✓96 | ✓ |
| `add`:14 Δ | definition | supp | ✓77 | ✓60 | ✓91 | ✓68 | ✓89 | ✓ |
| `binder`:21 | definition | supp | ✓71 | ✓66 | ✓94 | ✓93 | ✓83 | ✓ |
| `prepend`:29 | definition | supp | ✓89 | ✓69 | ✓90 | ✓96 | ✓95 | ✓ |
| `fields`:33 | definition | lead | ✓69 | ✓72 | ?58 | ?47 | ?52 | ✗ |
| `value`:47 | definition | supp | ✓82 | ✓73 | ✓90 | ✓92 | ✓90 | ✓ |
| `finish`:52 Δ | definition | supp | ✓66 | ✓76 | ✓96 | ✓84 | ✓90 | ✓ |
| `open_fields`:60 | definition | unc | ✓61 | ✓75 | ?46 | ✗40 | ?48 | ✗ |
| `branch`:65 Δ | definition | lead | ✓63 | ✓76 | ?48 | ✗39 | ?50 | ✗ |

### `src/check.bend`: 35 declarations, 4 changed, 16 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Mode`:8 | datatype | lead | ✗38 | ✓68 | ?45 | ✓65 | ✗08 | ✗ |
| `expected`:15 | definition | supp | ✓79 | ✓60 | ✓86 | ✓96 | ✓85 | ✓ |
| `enum_at`:21 | definition | supp | ✓84 | ✓62 | ✓85 | ✓97 | ✓93 | ✓ |
| `annotation_id`:27 | definition | supp | ✓93 | ?53 | ✓62 | ✓93 | ✓92 | ✗ |
| `annotation`:31 | definition | supp | ✓61 | ?57 | ✓91 | ✓91 | ✓64 | ✗ |
| `constant`:37 | definition | supp | ✓74 | ✓74 | ✓90 | ✓96 | ✓96 | ✓ |
| `constructor_result`:43 | definition | supp | ✓77 | ✓77 | ✓91 | ✓99 | ✓97 | ✓ |
| `constructor`:51 | definition | lead | ?47 | ✓65 | ✗36 | ?57 | ✗11 | ✗ |
| `variable`:58 | definition | supp | ✓70 | ?54 | ✓86 | ✓94 | ✓68 | ✗ |
| `bound`:64 | definition | supp | ✓91 | ✓62 | ?57 | ✓95 | ✓97 | ✗ |
| `callable`:70 Δ | definition | supp | ✓74 | ✓68 | ✓90 | ✓97 | ✓94 | ✓ |
| `call_result`:76 Δ | definition | supp | ✓79 | ✓64 | ✓85 | ✓74 | ✓88 | ✓ |
| `prepend_argument`:83 | definition | supp | ✓86 | ✓72 | ✓93 | ✓95 | ✓92 | ✓ |
| `let_result`:89 | definition | supp | ✓83 | ✓72 | ✓94 | ✓94 | ✓88 | ✓ |
| `pattern_arity`:95 | definition | supp | ✓95 | ✓70 | ✓72 | ✓99 | ✓98 | ✓ |
| `pattern`:98 | definition | unc | ?51 | ✓64 | ✗28 | ✗40 | ✗11 | ✗ |
| `pattern_id`:108 | definition | supp | ✓70 | ✓65 | ✓89 | ✓93 | ✓94 | ✓ |
| `complete_arms`:114 | definition | supp | ✓69 | ?56 | ✓86 | ✓96 | ✓92 | ✗ |
| `patterns`:119 | definition | lead | ✗39 | ✓66 | ✗31 | ✗32 | ✗10 | ✗ |
| `prepend_arm`:128 | definition | supp | ✓79 | ✓67 | ✓93 | ✓94 | ✓82 | ✓ |
| `case_result`:134 | definition | supp | ✓66 | ✓63 | ✓90 | ✓94 | ✓89 | ✓ |
| `call_body`:141 Δ | definition | supp | ?51 | ✓64 | ✓94 | ✓95 | ✓71 | ✗ |
| `binding_body`:147 | definition | supp | ✓69 | ✓65 | ✓95 | ✓95 | ✓64 | ✓ |
| `match_body`:153 | definition | lead | ✗39 | ✓63 | ?43 | ?47 | ✗16 | ✗ |
| `arm_body`:161 | definition | supp | ✓83 | ✓61 | ✓88 | ✓95 | ✓72 | ✓ |
| `arm_scope`:165 | definition | supp | ✓88 | ?59 | ✓84 | ✓95 | ✓76 | ✗ |
| `rebuilt`:169 | definition | supp | ✓87 | ✓72 | ✓91 | ✓94 | ✓90 | ✓ |
| `run`:174 Δ | definition | lead | ?47 | ✓74 | ✓72 | ✓70 | ✗19 | ✗ |
| `checked_function`:230 | definition | supp | ?42 | ✓65 | ✓93 | ✓98 | ✓82 | ✗ |
| `function_body`:234 | definition | supp | ✗39 | ✓71 | ✓97 | ✓96 | ?55 | ✗ |
| `functions`:239 | definition | unc | ✗37 | ✓72 | ✓60 | ?59 | ✗17 | ✗ |
| `enum_constructors`:253 | definition | supp | ✓84 | ✓69 | ✓67 | ✓95 | ✓71 | ✓ |
| `enum_profile`:260 | definition | unc | ✓81 | ✓71 | ✗15 | ?41 | ✗12 | ✗ |
| `resolved`:266 | definition | lead | ✗37 | ✓68 | ?54 | ?58 | ✗12 | ✗ |
| `check`:271 | definition | lead | ✗34 | ✓60 | ?57 | ✓70 | ✗07 | ✗ |

## Group `checker-laws`

Composition: below_target (highly_memetic ✓79, anticipation ✓75, payoff ✗27). Potential profundity: unavailable (task_byte_limit).

### `src/scope.bend`: 24 declarations, 10 changed, 5 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Scope`:5 Δ | datatype | lead | ?54 | ✓71 | ✗21 | ✗35 | ✗15 | ✗ |
| `contains`:8 | definition | supp | ✓99 | ✓84 | ✓66 | ✓100 | ✓100 | ✓ |
| `descendants`:14 Δ | definition | unc | ✓76 | ✓65 | ✗12 | ✗24 | ✗23 | ✗ |
| `descends`:18 Δ | definition | unc | ✓94 | ✓70 | ✗02 | ✗15 | ✗14 | ✗ |
| `sequential`:25 | definition | lead | ✓77 | ✓82 | ✗31 | ✓75 | ✓74 | ✗ |
| `alternatives`:32 | definition | lead | ✓86 | ✓62 | ✗24 | ✗33 | ✗30 | ✗ |
| `remove`:37 | definition | supp | ✓93 | ✓77 | ✓88 | ✓99 | ✓96 | ✓ |
| `find`:43 | definition | lead | ✓89 | ✓81 | ✗14 | ✗19 | ✗24 | ✗ |
| `lookup`:51 Δ | definition | unc | ✓87 | ?49 | ✗07 | ✗32 | ✗11 | ✗ |
| `occurrence`:55 | definition | lead | ✓78 | ✓73 | ✗12 | ✗10 | ✗24 | ✗ |
| `reference`:63 Δ | definition | unc | ✓86 | ✓70 | ✗21 | ✗23 | ✗21 | ✗ |
| `live_scope`:68 Δ | definition | supp | ✓94 | ?52 | ?53 | ✓63 | ✓64 | ✗ |
| `extend`:72 Δ | definition | unc | ✓84 | ?49 | ✗03 | ✗36 | ✗18 | ✗ |
| `set_known`:77 | definition | lead | ✓92 | ✓82 | ✗18 | ✗12 | ✗28 | ✗ |
| `refine`:85 | definition | supp | ✓95 | ✓85 | ✓92 | ✓81 | ✓98 | ✓ |
| `after`:89 | definition | supp | ✓87 | ✓84 | ✓87 | ✓88 | ✓81 | ✓ |
| `levels`:95 | definition | supp | ✓96 | ✓80 | ?55 | ✓98 | ✓98 | ✗ |
| `find_level`:100 | definition | unc | ✓88 | ✓69 | ✗05 | ✗14 | ✗17 | ✗ |
| `replace`:108 | definition | supp | ✓95 | ✓83 | ✓93 | ✓85 | ✓94 | ✓ |
| `remove_fields`:111 | definition | lead | ✓88 | ✓77 | ✗15 | ✗23 | ✗23 | ✗ |
| `branch`:116 Δ | definition | lead | ✓79 | ✓85 | ✗29 | ✗35 | ✗29 | ✗ |
| `parameters`:120 Δ | definition | lead | ✓84 | ✓76 | ✗08 | ✗32 | ✗23 | ✗ |
| `matchable`:126 Δ | definition | unc | ✓60 | ?57 | ✗11 | ✗13 | ✗22 | ✗ |
| `scrutinee`:134 | definition | lead | ✓71 | ✓84 | ✗14 | ?52 | ✗37 | ✗ |

## Group `fields-laws`

Composition: below_target (highly_memetic ✓94, anticipation ✓91, payoff ✗35). Potential profundity: low (18% relevant).

### `src/patterns.bend`: 10 declarations, 3 changed, 6 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Fields`:7 | datatype | lead | ✓66 | ✓66 | ?45 | ✗38 | ✗26 | ✗ |
| `quantity`:10 | definition | supp | ✓71 | ✓69 | ✓92 | ✓77 | ✓96 | ✓ |
| `add`:14 Δ | definition | supp | ✓77 | ✓60 | ✓91 | ✓68 | ✓89 | ✓ |
| `binder`:21 | definition | supp | ✓71 | ✓66 | ✓94 | ✓93 | ✓83 | ✓ |
| `prepend`:29 | definition | supp | ✓89 | ✓69 | ✓90 | ✓96 | ✓95 | ✓ |
| `fields`:33 | definition | lead | ✓69 | ✓72 | ?58 | ?47 | ?52 | ✗ |
| `value`:47 | definition | supp | ✓82 | ✓73 | ✓90 | ✓92 | ✓90 | ✓ |
| `finish`:52 Δ | definition | supp | ✓66 | ✓76 | ✓96 | ✓84 | ✓90 | ✓ |
| `open_fields`:60 | definition | unc | ✓61 | ✓75 | ?46 | ✗40 | ?48 | ✗ |
| `branch`:65 Δ | definition | lead | ✓63 | ✓76 | ?48 | ✗39 | ?50 | ✗ |

## Group `wasm-emission`

Composition: uncertain (highly_memetic ✓86, anticipation ✓63, payoff ?44). Potential profundity: unavailable (task_byte_limit).

### `src/wasm.bend`: 45 declarations, 23 changed, 14 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Local`:8 | datatype | lead | ✓73 | ✓72 | ✗08 | ✗27 | ✗13 | ✗ |
| `Environment`:10 | datatype | lead | ✓60 | ✓83 | ✗24 | ✗36 | ✗25 | ✗ |
| `Code`:12 | datatype | lead | ✓73 | ✓69 | ✗14 | ✗40 | ✗17 | ✗ |
| `Profile`:14 Δ | datatype | lead | ✓64 | ?42 | ✗06 | ✗18 | ✗09 | ✗ |
| `Mode`:17 Δ | datatype | lead | ?44 | ✓87 | ✗24 | ?52 | ✗20 | ✗ |
| `fielded`:25 Δ | definition | supp | ✓75 | ✓64 | ✓72 | ✓73 | ✓92 | ✓ |
| `heap_types`:31 Δ | definition | lead | ✓91 | ✓83 | ✗12 | ✗21 | ✗17 | ✗ |
| `boxed`:37 Δ | definition | supp | ✓94 | ✓76 | ?56 | ✓91 | ✓99 | ✗ |
| `fielded_arms`:44 Δ | definition | supp | ✓80 | ✓87 | ✓74 | ✓87 | ✓93 | ✓ |
| `capability`:50 Δ | definition | supp | ✓77 | ✓65 | ?56 | ✓63 | ✓85 | ✗ |
| `internal`:55 | definition | supp | ✓91 | ?54 | ✗39 | ✓80 | ✓92 | ✗ |
| `lookup`:58 | definition | supp | ✓94 | ✓85 | ✓78 | ✓99 | ✓98 | ✓ |
| `signature`:64 | definition | supp | ✓72 | ✓72 | ✓79 | ✓97 | ✓92 | ✓ |
| `parameters`:70 | definition | lead | ✓84 | ✓88 | ✗19 | ✗25 | ✗29 | ✗ |
| `live_types`:77 | definition | unc | ✓90 | ✓80 | ✗18 | ✗23 | ✗24 | ✗ |
| `instruction`:83 | definition | supp | ✓86 | ✓83 | ✓91 | ✓91 | ✓96 | ✓ |
| `constant`:86 | definition | supp | ✓86 | ✓77 | ✓87 | ✓75 | ✓92 | ✓ |
| `code`:89 | definition | lead | ✓89 | ✓77 | ✗26 | ✗26 | ✗24 | ✗ |
| `append`:92 | definition | supp | ✓91 | ✓73 | ✓86 | ✓98 | ✓93 | ✓ |
| `called`:96 | definition | supp | ✓87 | ✓80 | ✓88 | ✓72 | ✓96 | ✓ |
| `call_body`:100 | definition | supp | ✓88 | ✓73 | ?56 | ✓94 | ✓96 | ✗ |
| `after_argument`:104 | definition | supp | ✓90 | ✓80 | ✓93 | ✓93 | ✓96 | ✓ |
| `after_initializer`:108 | definition | supp | ✓75 | ✓69 | ✓94 | ✓89 | ✓95 | ✓ |
| `branch_code`:115 | definition | unc | ?55 | ?58 | ✗15 | ✗11 | ✗14 | ✗ |
| `memory`:122 Δ | definition | supp | ✓82 | ✓88 | ✓87 | ✓80 | ✓86 | ✓ |
| `load`:125 Δ | definition | supp | ✓85 | ✓80 | ✓90 | ✓86 | ✓93 | ✓ |
| `stores`:128 Δ | definition | lead | ✓78 | ✓80 | ✗19 | ✗10 | ✗18 | ✗ |
| `allocate`:134 Δ | definition | supp | ?55 | ?49 | ✓89 | ✓67 | ✓87 | ✗ |
| `lower`:141 Δ | definition | lead | ?48 | ✓90 | ✓72 | ?52 | ?49 | ✗ |
| `local_declarations`:194 | definition | supp | ✓80 | ✓71 | ✓74 | ✓79 | ✓91 | ✓ |
| `function_code`:198 | definition | supp | ✓64 | ?59 | ✓89 | ✓85 | ✓87 | ✗ |
| `body`:204 Δ | definition | lead | ?48 | ✓88 | ?47 | ✗36 | ✗33 | ✗ |
| `function_type`:209 | definition | lead | ✓79 | ✓74 | ✗18 | ✗35 | ✗24 | ✗ |
| `Sections`:212 | datatype | lead | ✓70 | ✓81 | ✗17 | ?54 | ✗17 | ✗ |
| `extend_sections`:215 | definition | lead | ✓82 | ✓83 | ✗08 | ?44 | ✗26 | ✗ |
| `entry`:223 Δ | definition | lead | ?52 | ✓75 | ✗25 | ✗38 | ✗38 | ✗ |
| `entries`:231 Δ | definition | lead | ✓64 | ✓74 | ✗12 | ✗30 | ✗17 | ✗ |
| `allocator`:240 Δ | definition | lead | ✗33 | ?43 | ✗12 | ✗28 | ✗15 | ✗ |
| `heap_sections`:245 Δ | definition | supp | ✓74 | ✓78 | ✓86 | ✓92 | ✓93 | ✓ |
| `module_bytes`:253 Δ | definition | lead | ✓72 | ✓84 | ✗32 | ?51 | ✗31 | ✗ |
| `finish`:258 Δ | definition | lead | ?55 | ✓71 | ✗21 | ✗36 | ✗30 | ✗ |
| `present`:267 Δ | definition | supp | ✓83 | ✓69 | ✗37 | ✓87 | ✓93 | ✗ |
| `profiled`:272 Δ | definition | lead | ?52 | ?52 | ✗16 | ✗27 | ✗19 | ✗ |
| `emit_profile`:278 Δ | definition | lead | ✗39 | ✓74 | ✗24 | ✗40 | ✗28 | ✗ |
| `emit`:284 Δ | definition | supp | ✓74 | ?51 | ✓62 | ✓73 | ✓92 | ✗ |

## Group `adaptive-runtime`

Composition: uncertain (highly_memetic ✓91, anticipation ✓89, payoff ?43). Potential profundity: low (13% relevant).

### `research/adaptive-tasks/runtime/slot-model.bend`: 7 declarations, 7 changed, 1 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Command`:7 Δ | datatype | supp | ?59 | ?53 | ✓68 | ?55 | ✓65 | ✗ |
| `event`:10 Δ | definition | supp | ✓84 | ?59 | ✓76 | ✓91 | ✓82 | ✗ |
| `step`:14 Δ | definition | unc | ✓76 | ?56 | ✗14 | ✗26 | ✗23 | ✗ |
| `continue`:22 Δ | definition | supp | ✓83 | ✗28 | ✓60 | ✓76 | ✓79 | ✗ |
| `identity`:26 Δ | definition | supp | ?41 | ✗36 | ✓68 | ?50 | ?53 | ✗ |
| `run`:29 Δ | definition | lead | ✓71 | ✓62 | ✗25 | ✗28 | ✗19 | ✗ |
| `start`:35 Δ | definition | supp | ✓72 | ✓71 | ✓94 | ✓83 | ✓68 | ✓ |

### `research/adaptive-tasks/runtime/frontier.bend`: 34 declarations, 34 changed, 11 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Task`:4 Δ | datatype | lead | ?47 | ✓67 | ✗14 | ?51 | ✗02 | ✗ |
| `State`:6 Δ | datatype | lead | ?57 | ✓75 | ✗21 | ?54 | ✗02 | ✗ |
| `Command`:8 Δ | datatype | supp | ?47 | ✓80 | ✓88 | ✓60 | ✓65 | ✗ |
| `phase`:11 Δ | definition | supp | ✓85 | ✓68 | ✓82 | ✓82 | ✓67 | ✓ |
| `mark`:15 Δ | definition | supp | ✓92 | ✓80 | ✓88 | ✓73 | ✓79 | ✓ |
| `find`:23 Δ | definition | supp | ✓80 | ✓79 | ✓81 | ✓97 | ✓94 | ✓ |
| `append`:31 Δ | definition | supp | ✓95 | ✓76 | ?57 | ✓98 | ✓94 | ✗ |
| `length`:36 Δ | definition | supp | ✓91 | ✓73 | ?55 | ✓94 | ✓83 | ✗ |
| `result`:41 Δ | definition | supp | ✓78 | ✓69 | ✓81 | ✓87 | ?47 | ✗ |
| `offer_space`:45 Δ | definition | supp | ✓69 | ✓67 | ✓90 | ✓65 | ✗31 | ✗ |
| `offer_ready`:51 Δ | definition | supp | ✓75 | ✓80 | ✓95 | ✓83 | ✓82 | ✓ |
| `offer_task`:57 Δ | definition | supp | ✓61 | ✓81 | ✓95 | ✓87 | ✓72 | ✓ |
| `offer`:63 Δ | definition | supp | ?47 | ✓80 | ✓97 | ✓90 | ✓88 | ✗ |
| `wake_ready`:67 Δ | definition | supp | ✓79 | ✓66 | ✓92 | ✓75 | ✓68 | ✓ |
| `wake_task`:72 Δ | definition | supp | ✓74 | ✓73 | ✓93 | ✓83 | ✓77 | ✓ |
| `wake`:77 Δ | definition | supp | ?52 | ✓77 | ✓94 | ✓91 | ✓83 | ✗ |
| `running`:81 Δ | definition | supp | ✓93 | ✓78 | ✓88 | ✓92 | ✓82 | ✓ |
| `admit`:89 Δ | definition | supp | ✓68 | ✓66 | ✓88 | ?44 | ✓75 | ✗ |
| `prepare`:95 Δ | definition | supp | ?49 | ✓79 | ✓96 | ✓82 | ✓72 | ✗ |
| `instruction`:102 Δ | definition | supp | ✓83 | ✓68 | ✓84 | ✓80 | ✓63 | ✓ |
| `advance`:109 Δ | definition | supp | ?48 | ✓72 | ✓85 | ✓72 | ?58 | ✗ |
| `execute_task`:116 Δ | definition | unc | ✓65 | ✓81 | ✗24 | ?42 | ✗07 | ✗ |
| `execute_tasks`:123 Δ | definition | unc | ?59 | ✓80 | ✗20 | ✗27 | ✗05 | ✗ |
| `execute`:128 Δ | definition | lead | ✗35 | ✓81 | ✗33 | ?43 | ✗20 | ✗ |
| `fault`:134 Δ | definition | supp | ✓89 | ✓61 | ?57 | ✗40 | ✓64 | ✗ |
| `finish`:139 Δ | definition | supp | ✓79 | ?58 | ✓64 | ✓77 | ✓75 | ✗ |
| `publish`:144 Δ | definition | supp | ✗40 | ✓64 | ✓88 | ✓64 | ?49 | ✗ |
| `round`:150 Δ | definition | lead | ?47 | ✓85 | ?44 | ?57 | ✗40 | ✗ |
| `run`:153 Δ | definition | lead | ?49 | ✓85 | ?47 | ?53 | ✗33 | ✗ |
| `task_words`:158 Δ | definition | supp | ✓92 | ✓61 | ?54 | ✓93 | ✓61 | ✗ |
| `observation`:162 Δ | definition | supp | ✓61 | ✓75 | ✓80 | ✓90 | ✓72 | ✓ |
| `initial_at`:168 Δ | definition | supp | ✓88 | ✓63 | ✓62 | ✓81 | ✓74 | ✓ |
| `initial`:171 Δ | definition | supp | ✓86 | ✓61 | ?58 | ✓87 | ?54 | ✗ |
| `trace`:174 Δ | definition | unc | ✗34 | ✓79 | ✗34 | ✗33 | ✗12 | ✗ |

### `research/adaptive-tasks/runtime/LAWS.bend`: 8 declarations, 8 changed, 7 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `zero_slice`:6 Δ | law | supp | ✓83 | ✓78 | ✓91 | ✓81 | ✓92 | ✓ |
| `offer_full`:14 Δ | law | supp | ✓65 | ✓79 | ✓92 | ✓89 | ✓89 | ✓ |
| `offer_duplicate`:17 Δ | law | supp | ✓69 | ✓77 | ✓90 | ✓86 | ✓84 | ✓ |
| `prepare_reverse`:20 Δ | law | supp | ✓66 | ✓78 | ✓94 | ✓89 | ✓90 | ✓ |
| `round_suspend`:23 Δ | law | supp | ✓64 | ✓63 | ✓86 | ✓73 | ✓68 | ✓ |
| `round_wait`:26 Δ | law | supp | ✓62 | ✓65 | ✓84 | ✓72 | ✓77 | ✓ |
| `unsupported_slot`:30 Δ | law | supp | ✓85 | ✓69 | ✓73 | ✓94 | ✓91 | ✓ |
| `fault_retains`:34 Δ | law | supp | ?58 | ✓68 | ✓88 | ✓74 | ✓75 | ✗ |

### `research/adaptive-tasks/runtime/PROOF.bend`: 8 declarations, 8 changed, 0 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `L.zero_slice`:4 Δ | law_fill | supp | ?47 | ?50 | ✓80 | ✗30 | ✗33 | ✗ |
| `L.offer_full`:5 Δ | law_fill | supp | ?54 | ✓73 | ✓92 | ✓86 | ?51 | ✗ |
| `L.offer_duplicate`:6 Δ | law_fill | supp | ?55 | ✓71 | ✓88 | ✓84 | ?46 | ✗ |
| `L.prepare_reverse`:7 Δ | law_fill | supp | ?55 | ✓76 | ✓90 | ✓78 | ?56 | ✗ |
| `L.round_suspend`:8 Δ | law_fill | supp | ?47 | ✓61 | ✓85 | ✓73 | ✗39 | ✗ |
| `L.round_wait`:9 Δ | law_fill | supp | ✗35 | ?55 | ✓82 | ✓62 | ✗35 | ✗ |
| `L.unsupported_slot`:10 Δ | law_fill | supp | ?57 | ✓60 | ✓79 | ✓79 | ?49 | ✗ |
| `L.fault_retains`:11 Δ | law_fill | supp | ?57 | ✓72 | ✓89 | ✓69 | ?56 | ✗ |

## Group `data-lifetime`

Composition: uncertain (highly_memetic ✓95, anticipation ✓93, payoff ?46). Potential profundity: low (25% relevant).

### `research/data-lifetime/model.bend`: 70 declarations, 70 changed, 32 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Cell`:4 Δ | datatype | lead | ?52 | ✓64 | ✗15 | ✗28 | ✗02 | ✗ |
| `Holder`:7 Δ | datatype | supp | ✓82 | ✓67 | ✓77 | ✓93 | ?43 | ✗ |
| `Heap`:10 Δ | datatype | lead | ✗30 | ?58 | ✗31 | ?59 | ✗01 | ✗ |
| `Store`:16 Δ | datatype | lead | ?43 | ?59 | ?44 | ✗27 | ✗24 | ✗ |
| `Command`:19 Δ | datatype | lead | ?46 | ✓61 | ✓64 | ?51 | ✗26 | ✗ |
| `choose`:30 Δ | definition | supp | ✓97 | ✓66 | ?58 | ✓99 | ✓92 | ✗ |
| `bind`:35 Δ | definition | supp | ✓86 | ✓67 | ✓82 | ✓97 | ✓88 | ✓ |
| `length`:40 Δ | definition | supp | ✓64 | ✓69 | ✓68 | ✓92 | ✓82 | ✓ |
| `at`:45 Δ | definition | supp | ✓78 | ✓66 | ✓82 | ✓94 | ✓78 | ✓ |
| `set`:52 Δ | definition | supp | ✓66 | ✓71 | ✓87 | ✓89 | ✓68 | ✓ |
| `add`:59 Δ | definition | supp | ✓78 | ✓68 | ✓71 | ✓92 | ✓88 | ✓ |
| `maximum`:62 Δ | definition | supp | ✓98 | ✓72 | ?55 | ✓99 | ✓95 | ✗ |
| `member`:65 Δ | definition | supp | ✓88 | ✓66 | ✓65 | ✓97 | ✓88 | ✓ |
| `root`:70 Δ | definition | supp | ?46 | ✓74 | ✓94 | ✓93 | ✓62 | ✗ |
| `omit`:75 Δ | definition | supp | ✓89 | ✓76 | ✓87 | ✓94 | ✓96 | ✓ |
| `omit_all`:82 Δ | definition | supp | ✓86 | ✓70 | ✓80 | ✓94 | ✓93 | ✓ |
| `install`:87 Δ | definition | supp | ✓89 | ✓73 | ✓77 | ✓74 | ✓91 | ✓ |
| `vacant`:92 Δ | definition | supp | ✓87 | ✓75 | ✓88 | ✓98 | ✓98 | ✓ |
| `gather`:98 Δ | definition | supp | ✓71 | ✓66 | ✓89 | ✓64 | ✓89 | ✓ |
| `cell`:106 Δ | definition | supp | ?48 | ✓73 | ✓87 | ✓94 | ✓79 | ✗ |
| `erase`:113 Δ | definition | supp | ✓87 | ✓74 | ✓82 | ✓92 | ✓94 | ✓ |
| `count`:120 Δ | definition | supp | ✓83 | ✓75 | ✓82 | ✓88 | ✓95 | ✓ |
| `payload`:128 Δ | definition | supp | ✓94 | ✓71 | ✓60 | ✓96 | ✓95 | ✓ |
| `words`:132 Δ | definition | supp | ✓95 | ✓76 | ✓83 | ✓83 | ✓96 | ✓ |
| `initial`:137 Δ | definition | supp | ?45 | ✓61 | ✓82 | ✓78 | ✗23 | ✗ |
| `with_roots`:140 Δ | definition | supp | ✓78 | ?57 | ✓80 | ✓94 | ✓95 | ✗ |
| `with_readers`:144 Δ | definition | supp | ✓86 | ?58 | ✓81 | ✓94 | ✓95 | ✗ |
| `charged`:148 Δ | definition | supp | ✓87 | ✓66 | ✓78 | ?51 | ✓91 | ✗ |
| `queued`:152 Δ | definition | supp | ✓85 | ?59 | ✓77 | ✓86 | ✓92 | ✗ |
| `Allocation`:157 Δ | datatype | unc | ?52 | ✓70 | ✗19 | ✗20 | ✗19 | ✗ |
| `allocate`:160 Δ | definition | supp | ✓65 | ?58 | ✓91 | ✓86 | ✓89 | ✗ |
| `free`:171 Δ | definition | supp | ?54 | ?56 | ✓89 | ✓75 | ✓61 | ✗ |
| `retained`:176 Δ | definition | supp | ✓82 | ✓62 | ✓86 | ✓76 | ✓90 | ✓ |
| `acquire`:183 Δ | definition | supp | ?58 | ✓61 | ✓88 | ✓79 | ✓89 | ✗ |
| `acquire_all`:188 Δ | definition | supp | ✓65 | ?58 | ✓89 | ✓78 | ✓86 | ✗ |
| `decremented`:193 Δ | definition | supp | ✓93 | ✓64 | ✓77 | ✓91 | ✓94 | ✓ |
| `data_cell`:197 Δ | definition | supp | ✓94 | ✓64 | ✓65 | ✓80 | ✓83 | ✓ |
| `data_edges`:201 Δ | definition | supp | ✓64 | ✓63 | ✓89 | ✓84 | ✓84 | ✓ |
| `CopyFrame`:208 Δ | datatype | unc | ?56 | ✓62 | ✗21 | ✗15 | ✗13 | ✗ |
| `Copying`:212 Δ | datatype | lead | ?45 | ✓67 | ?47 | ✗26 | ✗11 | ✗ |
| `visits`:215 Δ | definition | supp | ✓93 | ✓83 | ✓79 | ✓91 | ✓91 | ✓ |
| `copying`:220 Δ | definition | supp | ✓73 | ?55 | ✓77 | ✓79 | ?51 | ✗ |
| `assemble`:226 Δ | definition | supp | ✗18 | ✓61 | ✓87 | ✓69 | ?57 | ✗ |
| `enter_copy`:236 Δ | definition | supp | ?49 | ✓66 | ✓92 | ✓79 | ✓68 | ✗ |
| `lookup`:241 Δ | definition | supp | ✓69 | ✓63 | ✓77 | ✓93 | ✓92 | ✓ |
| `copy_step`:245 Δ | definition | lead | ?42 | ✓68 | ✗28 | ✗12 | ✗13 | ✗ |
| `copy_run`:253 Δ | definition | lead | ✗37 | ✓72 | ?47 | ✗29 | ✗14 | ✗ |
| `copy`:259 Δ | definition | unc | ✗35 | ✓73 | ?50 | ✗34 | ✗31 | ✗ |
| `held`:262 Δ | definition | supp | ✓75 | ✓67 | ✓75 | ✓86 | ✓94 | ✓ |
| `constructed`:269 Δ | definition | supp | ✓70 | ✓67 | ✓86 | ✓86 | ✓94 | ✓ |
| `alloc`:277 Δ | definition | unc | ✗39 | ?59 | ✗37 | ?58 | ?45 | ✗ |
| `shared`:285 Δ | definition | supp | ?47 | ✓63 | ✓92 | ✓85 | ✓80 | ✗ |
| `share`:293 Δ | definition | unc | ?56 | ✓69 | ✗26 | ?55 | ?43 | ✗ |
| `transferred`:300 Δ | definition | supp | ✓79 | ✓67 | ✓82 | ✓80 | ✓92 | ✓ |
| `opened`:304 Δ | definition | supp | ?53 | ?58 | ✓92 | ✓62 | ✓79 | ✗ |
| `take_cell`:313 Δ | definition | supp | ?45 | ✓62 | ✓95 | ✓86 | ✓90 | ✗ |
| `take`:319 Δ | definition | unc | ?42 | ✓61 | ✗28 | ?49 | ?42 | ✗ |
| `move`:326 Δ | definition | supp | ✓90 | ✓72 | ✓89 | ✓98 | ✓96 | ✓ |
| `release`:333 Δ | definition | supp | ✓83 | ✓66 | ✓89 | ✓97 | ✓94 | ✓ |
| `dropped`:340 Δ | definition | supp | ✓83 | ✓63 | ✓85 | ✓75 | ✓87 | ✓ |
| `release_cell`:345 Δ | definition | supp | ✓72 | ✓68 | ✓93 | ✓88 | ✓88 | ✓ |
| `clean_step`:353 Δ | definition | supp | ✓60 | ✓62 | ✓95 | ✓81 | ✓90 | ✓ |
| `continue_clean`:359 Δ | definition | supp | ?58 | ✓63 | ✓86 | ✓95 | ✓91 | ✗ |
| `clean`:364 Δ | definition | lead | ✗38 | ?50 | ✗26 | ✗32 | ✗17 | ✗ |
| `pin`:372 Δ | definition | supp | ✓93 | ✓76 | ✓91 | ✓98 | ✓97 | ✓ |
| `ack`:379 Δ | definition | supp | ✓91 | ✓76 | ✓86 | ✓98 | ✓97 | ✓ |
| `commit`:384 Δ | definition | supp | ✓75 | ✓62 | ✓88 | ✓95 | ✓91 | ✓ |
| `step`:389 Δ | definition | lead | ?42 | ✓66 | ?56 | ?47 | ✗22 | ✗ |
| `wrapped`:401 Δ | definition | supp | ?56 | ?49 | ✓79 | ✓93 | ✓80 | ✗ |
| `transition`:405 Δ | definition | unc | ?44 | ?58 | ?57 | ?49 | ✗24 | ✗ |

### `research/data-lifetime/observe.bend`: 7 declarations, 7 changed, 1 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `numbers`:4 Δ | definition | supp | ?58 | ✓65 | ✓72 | ✓90 | ✓70 | ✗ |
| `holders`:10 Δ | definition | supp | ?59 | ✓71 | ✓76 | ✓97 | ✓93 | ✗ |
| `cell`:16 Δ | definition | supp | ✓71 | ✓65 | ?57 | ✓96 | ✓84 | ✗ |
| `cells`:20 Δ | definition | supp | ?52 | ✓75 | ✓75 | ✓94 | ✓86 | ✗ |
| `wire`:26 Δ | definition | supp | ✓64 | ✓73 | ✓80 | ✓86 | ✓91 | ✓ |
| `report`:31 Δ | definition | supp | ?53 | ✓60 | ✓82 | ✓93 | ✓84 | ✗ |
| `run`:39 Δ | definition | unc | ?52 | ✓65 | ?43 | ✗40 | ✗19 | ✗ |

### `research/data-lifetime/LAWS.bend`: 20 declarations, 20 changed, 6 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `rejected_transaction_preserves_state`:4 Δ | law | supp | ✓97 | ✓79 | ✓75 | ✓97 | ✓92 | ✓ |
| `successful_transaction_publishes_state`:9 Δ | law | supp | ✓95 | ✓76 | ✓68 | ✓97 | ✓90 | ✓ |
| `type_is_not_shareable`:14 Δ | law | supp | ✓82 | ✓65 | ✓87 | ✓94 | ✓88 | ✓ |
| `count_ceiling_preserves_state`:19 Δ | law | supp | ✓71 | ?50 | ✓79 | ✓87 | ✓83 | ✗ |
| `copied_leaf_has_distinct_owner`:24 Δ | law | unc | ✓67 | ✓64 | ✗28 | ✓79 | ✓81 | ✗ |
| `counted_leaf_retains_one_record`:29 Δ | law | supp | ✓61 | ?58 | ✓88 | ✓88 | ✓84 | ✗ |
| `empty_capacity_rejects_allocation`:34 Δ | law | supp | ✓78 | ?58 | ✓86 | ✓95 | ✓83 | ✗ |
| `copied_allocation_installs_owner`:39 Δ | law | supp | ✓64 | ?57 | ✓84 | ✓86 | ✓74 | ✗ |
| `counted_allocation_starts_at_one`:44 Δ | law | supp | ✓74 | ✓61 | ✓84 | ✓91 | ✓87 | ✓ |
| `copied_release_keeps_other_value`:49 Δ | law | supp | ?49 | ?50 | ✓86 | ✓79 | ✓61 | ✗ |
| `shared_open_acquires_children`:54 Δ | law | supp | ?59 | ?59 | ✓90 | ✓83 | ✓80 | ✗ |
| `zero_budget_retains_obligation`:59 Δ | law | supp | ✓65 | ✓61 | ✓89 | ✓91 | ✓87 | ✓ |
| `reader_blocks_reuse`:65 Δ | law | supp | ?46 | ?55 | ✓88 | ✓62 | ?51 | ✗ |
| `type_last_release_drops_once`:71 Δ | law | supp | ✓65 | ✓61 | ✓92 | ✓91 | ✓83 | ✓ |
| `data_first_release_keeps_alias`:76 Δ | law | supp | ?51 | ?57 | ✓88 | ✓78 | ✓67 | ✗ |
| `data_last_release_reclaims`:81 Δ | law | supp | ?47 | ✓61 | ✓92 | ✓78 | ✓65 | ✗ |
| `consume_transfers_fields`:86 Δ | law | supp | ?48 | ?59 | ✓89 | ✓79 | ✓72 | ✗ |
| `release_queues_without_disposal`:90 Δ | law | supp | ✓68 | ?57 | ✓88 | ✓85 | ✓84 | ✗ |
| `suspension_moves_one_holder`:95 Δ | law | supp | ✓76 | ?56 | ✓84 | ✓94 | ✓91 | ✗ |
| `immutable_graph_rejects_backpatch`:100 Δ | law | supp | ✓83 | ?55 | ✓84 | ✓91 | ✓87 | ✗ |

### `research/data-lifetime/PROOF.bend`: 20 declarations, 20 changed, 1 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `L.rejected_transaction_preserves_state`:4 Δ | law_fill | supp | ✓88 | ✓66 | ✓85 | ✓81 | ?54 | ✗ |
| `L.successful_transaction_publishes_state`:5 Δ | law_fill | supp | ✓84 | ✓62 | ✓82 | ✓86 | ?42 | ✗ |
| `L.type_is_not_shareable`:6 Δ | law_fill | supp | ?52 | ?43 | ✓86 | ✓84 | ✗37 | ✗ |
| `L.count_ceiling_preserves_state`:7 Δ | law_fill | supp | ✗39 | ?53 | ✓81 | ✓66 | ?43 | ✗ |
| `L.copied_leaf_has_distinct_owner`:8 Δ | law_fill | supp | ✗38 | ✓63 | ✓86 | ✓83 | ?48 | ✗ |
| `L.counted_leaf_retains_one_record`:9 Δ | law_fill | supp | ?49 | ✓65 | ✓86 | ✓76 | ?58 | ✗ |
| `L.empty_capacity_rejects_allocation`:10 Δ | law_fill | supp | ✓61 | ?54 | ✓89 | ✓84 | ?59 | ✗ |
| `L.copied_allocation_installs_owner`:11 Δ | law_fill | supp | ✓65 | ✓64 | ✓86 | ✓79 | ✓62 | ✓ |
| `L.counted_allocation_starts_at_one`:12 Δ | law_fill | supp | ✓62 | ✓61 | ✓86 | ✓87 | ?56 | ✗ |
| `L.copied_release_keeps_other_value`:13 Δ | law_fill | supp | ✗38 | ✓62 | ✓87 | ✓84 | ?46 | ✗ |
| `L.shared_open_acquires_children`:14 Δ | law_fill | supp | ✗34 | ?57 | ✓90 | ✓74 | ?42 | ✗ |
| `L.zero_budget_retains_obligation`:15 Δ | law_fill | supp | ?41 | ✓62 | ✓91 | ✓80 | ?52 | ✗ |
| `L.reader_blocks_reuse`:16 Δ | law_fill | supp | ✗26 | ?51 | ✓78 | ✓72 | ✗24 | ✗ |
| `L.type_last_release_drops_once`:17 Δ | law_fill | supp | ✗32 | ✓60 | ✓84 | ✓77 | ✗38 | ✗ |
| `L.data_first_release_keeps_alias`:18 Δ | law_fill | supp | ✗32 | ?59 | ✓86 | ✓64 | ✗34 | ✗ |
| `L.data_last_release_reclaims`:19 Δ | law_fill | supp | ✗30 | ?57 | ✓87 | ✓77 | ✗35 | ✗ |
| `L.consume_transfers_fields`:20 Δ | law_fill | supp | ✗37 | ?58 | ✓89 | ✓72 | ?53 | ✗ |
| `L.release_queues_without_disposal`:21 Δ | law_fill | supp | ?58 | ✓60 | ✓89 | ✓64 | ?52 | ✗ |
| `L.suspension_moves_one_holder`:22 Δ | law_fill | supp | ✓66 | ✓63 | ✓87 | ✓63 | ?47 | ✗ |
| `L.immutable_graph_rejects_backpatch`:23 Δ | law_fill | supp | ✓70 | ?57 | ✓86 | ✓77 | ✓61 | ✗ |

## Group `fields-wasm`

Composition: below_target (highly_memetic ✓75, anticipation ✓73, payoff ✗17). Potential profundity: low (6% relevant).

### `tests/compiler-fields-wasm/compile.bend`: 4 declarations, 4 changed, 1 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `compile`:8 Δ | definition | supp | ✓65 | ✓64 | ✓81 | ✓96 | ✓86 | ✓ |
| `configured`:13 Δ | definition | supp | ?52 | ?58 | ✓78 | ✓93 | ✓88 | ✗ |
| `arguments`:22 Δ | definition | supp | ?53 | ?57 | ✓82 | ✓96 | ✓88 | ✗ |
| `main`:30 Δ | definition | supp | ?48 | ?41 | ?58 | ✓84 | ✓77 | ✗ |

### `tests/compiler-fields-wasm/LAWS.bend`: 5 declarations, 5 changed, 4 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `enum_capability_preserved`:7 Δ | law | supp | ✓87 | ✓79 | ✓91 | ✓100 | ✓87 | ✓ |
| `fields_capability_follows_checking`:11 Δ | law | supp | ✓86 | ✓76 | ✓86 | ✓98 | ✓92 | ✓ |
| `erased_constructor_still_has_a_cell`:15 Δ | law | supp | ✓81 | ?54 | ✓83 | ✓79 | ✓77 | ✗ |
| `erased_argument_takes_no_slot`:22 Δ | law | supp | ✓88 | ✓78 | ✓97 | ✓98 | ✓94 | ✓ |
| `erased_pattern_keeps_offset_and_locals`:38 Δ | law | supp | ✓82 | ✓81 | ✓97 | ✓95 | ✓89 | ✓ |

### `tests/compiler-fields-wasm/PROOF.bend`: 5 declarations, 5 changed, 3 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `L.enum_capability_preserved`:5 Δ | law_fill | supp | ✓82 | ✓77 | ✓89 | ✓85 | ✓78 | ✓ |
| `L.fields_capability_follows_checking`:6 Δ | law_fill | supp | ✓86 | ✓70 | ✓80 | ✓85 | ✓86 | ✓ |
| `L.erased_constructor_still_has_a_cell`:7 Δ | law_fill | supp | ✓79 | ✓60 | ✓88 | ✓81 | ?47 | ✗ |
| `L.erased_argument_takes_no_slot`:8 Δ | law_fill | supp | ✓72 | ✓73 | ✓94 | ✓88 | ?58 | ✗ |
| `L.erased_pattern_keeps_offset_and_locals`:9 Δ | law_fill | supp | ✓67 | ✓77 | ✓97 | ✓86 | ✓61 | ✓ |

## Group `fields-bounds`

Composition: below_target (highly_memetic ?47, anticipation ✓68, payoff ✗2). Potential profundity: low (18% relevant).

### `tests/compiler-fields/bounds.bend`: 4 declarations, 2 changed, 0 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `show`:9 Δ | definition | supp | ?51 | ✓66 | ✓90 | ✓85 | ✓80 | ✗ |
| `add`:15 Δ | definition | supp | ?53 | ✓63 | ✓92 | ✓77 | ✓83 | ✗ |
| `text`:19 | definition | supp | ?47 | ✓72 | ✓93 | ✓92 | ✓85 | ✗ |
| `main`:24 | definition | supp | ?50 | ✓66 | ✓94 | ✓87 | ✓76 | ✗ |

## Group `io-read-bytes`

Composition: below_target (highly_memetic ✗30, anticipation ✓63, payoff ✗25). Potential profundity: low (7% relevant).

### `tests/compiler-io-abi-2/read-bytes.bend`: 12 declarations, 12 changed, 0 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `numbers`:6 Δ | definition | supp | ✓93 | ?54 | ?53 | ✓90 | ✓75 | ✗ |
| `scalars`:11 Δ | definition | supp | ✓96 | ✓68 | ?57 | ✓98 | ✓89 | ✗ |
| `decoded`:16 Δ | definition | supp | ✓90 | ?51 | ✓71 | ✓94 | ✓91 | ✗ |
| `shown`:21 Δ | definition | supp | ✓78 | ?49 | ✓66 | ✓92 | ✓84 | ✗ |
| `text`:26 Δ | definition | supp | ✓81 | ?44 | ✓74 | ✓91 | ✓87 | ✗ |
| `read`:30 Δ | definition | lead | ✓70 | ?52 | ✗08 | ✓62 | ✗17 | ✗ |
| `limit`:35 Δ | definition | supp | ?42 | ?52 | ✓80 | ✓91 | ✓77 | ✗ |
| `report`:40 Δ | definition | supp | ?44 | ?42 | ✓75 | ✓84 | ✓72 | ✗ |
| `reads`:46 Δ | definition | lead | ?51 | ?59 | ✗18 | ✗21 | ✗13 | ✗ |
| `opened`:52 Δ | definition | supp | ✗33 | ✓60 | ✓87 | ✓91 | ✓80 | ✗ |
| `arguments`:57 Δ | definition | unc | ✗36 | ✓63 | ✗18 | ✗25 | ✗09 | ✗ |
| `main`:62 Δ | definition | unc | ✗35 | ?48 | ✗12 | ✗22 | ✗07 | ✗ |

## Group `io-empty-write`

Composition: below_target (highly_memetic ✗19, anticipation ?42, payoff ?48). Potential profundity: unavailable (missing_task_context).

### `tests/compiler-io/host/empty-write.bend`: 7 declarations, 7 changed, 0 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `write_result`:3 Δ | definition | supp | ?56 | ?53 | ✓74 | ✓97 | ✓96 | ✗ |
| `read_result`:8 Δ | definition | supp | ✓66 | ?41 | ?43 | ✓97 | ✓94 | ✗ |
| `read_pair`:13 Δ | definition | supp | ✓70 | ?46 | ✓72 | ✓82 | ✓85 | ✗ |
| `write_pair`:19 Δ | definition | supp | ✗33 | ?56 | ✓89 | ✓81 | ✓83 | ✗ |
| `opened`:26 Δ | definition | unc | ✗30 | ✓76 | ✗17 | ?49 | ✗38 | ✗ |
| `arguments`:31 Δ | definition | lead | ✗29 | ✓79 | ✗22 | ✗34 | ✗35 | ✗ |
| `main`:36 Δ | definition | supp | ✗34 | ✓69 | ✓90 | ✓79 | ✓84 | ✗ |
