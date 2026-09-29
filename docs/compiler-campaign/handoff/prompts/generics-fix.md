# generics: fix round after the 2026-09-28 review

Branch `campaign/generics` (edfad8b9). First merge `main` (5571625f or later) with a merge commit, never a rebase. For shared receipts, keep main's copy; the coordinator refreshes them. Regenerate the census as docs/compiler-campaign/GATES.md describes.

The last review's findings, with full evidence, are in `docs/compiler-campaign/handoff/findings/generics-last.md` on main (read it from `/Users/ericfode/src/knot/docs/...`). Handle every major, and every minor that is cheap:

1. **[major, unsound]** The generic path accepts books the seed rejects when `->` or a constructor's `{` contains a gap. Main answered them Unsupported. Freeze the seed's answers first (D7), then make the generic path follow the same token rule as the monomorphic path. Add a mutant that restores the acceptance.
2. **[major]** New Unsupported pins collide with the closures increment, which merges before generics.
   - Apply **D26** (docs/COMPILER-CAMPAIGN.md): the most precise sound verdict wins, and the losing pins are re-frozen in their own commit, seed observations unchanged.
   - You cannot merge closures here. Write down, for each colliding pin, the verdict D26 selects and the evidence, in `tests/compiler-generics/MERGE-WITH-CLOSURES.md`. The coordinator applies it at merge.
   - Change pins now only where your own pin is the imprecise side.
3. **[major]** Assertion edits and implementer-chosen pins that need rulings. For each one, give a proposed ruling in the report: keep, revert, or re-derive from the seed, with the seed evidence. Apply the ones that D4, D7, D21 or D26 already decide, each in a commit citing the rule. Leave the rest for the coordinator.
4. **[major]** The gate timeout. The runner now allows 1,800 s per gate. Measure the generics gate under load (KNOT_GATE_TIMEOUT_SCALE=4). If it is still near the limit, make it cheaper without dropping coverage: cache builds, and parallelize independent seed calls.
5. **Minors:**
   - Stop committing the ten gate-runner summaries with absolute paths.
   - Split `type-erasure-LAWS.bend` by subject, and rename `old_annotation` for what it is.
   - Move the generics-only branch in the shared runner's `counts()` into the gate itself.

Then run `npm run -s gates` and report every gate's exact counts.
