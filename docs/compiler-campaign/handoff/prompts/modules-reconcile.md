# modules: reconciliation round after nest's merge

`campaign/modules` (7ac90164) is the module-loading increment, and it merges next after nest. Nest is merged into `main` (363ea67a).

1. **Merge `main` (363ea67a or later)** with a merge commit, never a rebase.
   - Take the union of both sides' gates in the registry.
   - Regenerate the census; do not hand-merge it.
   - Keep main's copy of shared receipts.
2. **Dotted binders.** modules' scope-aware checker rule (`Invalid check dotted-binder`, with rebound dotted binders accepted) is canonical. Remove nest's parser stopgap (`Unsupported parse dotted-binder`) and amend the nest-frozen dotted-binder pins in one seed-citing amendment commit, under **D26** (docs/COMPILER-CAMPAIGN.md): the most precise sound verdict wins, and the seed observations never move.
3. **Detached constructor brace.** Nest 43d6553 made it `Invalid parse detached-brace`. Freeze `spm-mod`, `spm-entry` and `spm-base` with that answer in both bundle lanes, plus an import-free single-file variant, and add a mutant.
4. **Empty datatypes are accepted**, as the seed and nest accept them. Freeze tc2, em-absurd, em-param, em-entry, em-hash and sf-empty/{main,mid,data} as matching the seed, and add a mutant that demotes the rule to Invalid. Align `base-empty-datatype`. A lane that cannot handle one reports `Unsupported check empty-datatype`, never Invalid.
5. **Coordinator ruling.** `Unsupported function-reference` and `type-as-term`, for a function or type used where a datatype is expected, stay. They are D4-compliant because they never accept.
6. **Watch** the nest/generics `catalog-LAWS` textual merge hazard noted in the modules round-8 record.
7. **Vocabulary.** Use the shared diagnostic vocabulary (docs/compiler-campaign/COORDINATOR-STATE.md): an operator continuing a term is `operator`; other unmodeled term forms are `term-form`.
8. **Probe** module-qualified names inside nest's new matrix forms (qualified constructors in nested patterns, qualified types in literal columns) with at least 30 new programs against the seed. Freeze every discrepancy you find and fix it.

Then run `npm run -s gates` and report every gate's exact counts.
