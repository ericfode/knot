# literals-integ: fix round after nest's merge

`campaign/literals-integ` is `campaign/literals-layout` (literals plus layout) merged with an older nest tip (c9b073f). Nest has since been through rounds 11–13 and is merged into `main` (363ea67a). perch-cap (the names-only Perch tier) is also on main.

1. **Merge `main` (363ea67a or later)** with a merge commit, never a rebase. `git rerere` is enabled in this worktree, and earlier resolutions are recorded.
   - Take the union of both sides' gates in the registry.
   - Regenerate the census; do not hand-merge it.
   - Keep main's copy of shared receipts.
   - Where nest's newer frozen suites and this branch's pins disagree, apply **D26** (docs/COMPILER-CAMPAIGN.md): the most precise sound verdict wins, and the losing pins are re-frozen from the seed in a commit of their own.
   - Use the **shared diagnostic vocabulary** (docs/compiler-campaign/COORDINATOR-STATE.md): an operator continuing a term is `Unsupported parse operator`; other unmodeled term forms are `Unsupported parse term-form`.

   The earlier 39-pin ruling, the nest-oracle widening and the 19 re-expressed mutants are ratified (D26). Do not revert them.
2. **After perch-cap:**
   - Restore the two `C.exhausted(C.Checked,token)` uses that 8ea6faf spelled out to fit the old cap.
   - Restore the three original task files in the manifest wherever they now fit: `research/compiler-fields/SPEC.md` for `checking`, `tests/compiler-modules/SPEC.md` and `tests/compiler-nest/SPEC.md`.
   - Report each group's state and composition bytes, and the names-only cuts.
3. **Must fix.** Full evidence is in `/Users/ericfode/src/knot/docs/compiler-campaign/handoff/findings/literals-integ-r2.md`.
   - (a) The false Invalid `check unmatchable-binder` on a binder bound by a primitive (Nat or String) matrix, or by an alias or let of primitive type. The seed accepts these.
   - (b) Reproduce the reported acceptance of a constructor field named like a type that a later field of the same constructor reads (the seed rejects it). If it reproduces, answer Unsupported at minimum.
   - (c) Check the unannotated let of a matched parent that Knot accepts and the seed rejects (found by image's review). Fix it if it reproduces.
   - Freeze each expectation from the seed first (D7), and add a mutant for each rule.
4. **Laws (D21).** The review reported 8 parent laws removed and `offset_spelling` narrowed. Restore each removed law, or show where it moved. Undo the narrowing, or record it as a true open obligation in src/SPEC.md's trust inventory. D26 does not cover laws.
5. Run `npm run -s gates`, and report every gate's exact counts and the Perch manifest preflight.
