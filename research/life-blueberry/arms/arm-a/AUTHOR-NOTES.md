# Arm-a author notes

## Reading hypothesis, declared before compiler feedback

Represent a board as a list of packed rows. A three-input bit tally composes
vertically and horizontally into the entire 3x3 census. Including the center
turns Conway's rule into two selections: total three, or total four with a live
center. This should make the mechanism visible through the recurring grammar
of row/rows, pack/unpack, tally/halo, and three/four.

The intended conceptual compression is a shared full-adder basis instead of
eight separate neighbor lookups. Reading pleasure should come from the dual
packing operations and the two balanced population selections. The proposed
memetic hook is the same tally applied along two axes: a local Life rule appears
as a short bit-plane census. These are author hypotheses, not review outcomes.

## Exposure and references

No additional inducer exposure was assigned or read. Exposure-read-in-full is
not applicable. No other arm, evaluator, oracle, prior experiment output, chat,
memory, network source, or bend-tests material was inspected.

References read:

- `research/life-blueberry/AUTHOR.md` and `CONTRACT.md`, complete.
- Root `AGENTS.md` and `README.md`, complete.
- `perch-style.json` and `docs/perch-style.md`, complete, with unchanged targets:
  each axis requires probability mass at level 3 or higher of at least 0.60.
- `.codex/skills/perch/SKILL.md` and `docs/perch.md`.
- `.toolchain/bend-2.0.29-574b6d3/guide/GUIDE.md`, including the full syntax
  reference, quantity rules, structural recursion, and Base conventions.
- `.toolchain/bend-2.0.29-574b6d3/bend2/base.bend`: type declarations at lines
  1–65, Bool operations at 425–495, List operations at 807–975, and U32
  operations at 1332–1445. A definition-name/tuple-binding search located these
  sections. After the first diagnostic, Pair at 110–151 and Array tuple
  destructuring at 2270–2291 confirmed the required helper-parameter form.
  No upstream compiler or test source was read.

The initial root `git status --short --branch` reported detached HEAD and no
changes. No Git mutation was performed. The parent owns review and commits.

## Compiler protocol

The source was copied to `first.bend.snapshot` before the first compiler
invocation. Both invocations used exactly:

```sh
scripts/bend-reference research/life-blueberry/arms/arm-a/life.bend --check-only
```

First check: exit **1**. It rejected destructuring the computed result of
`row.pack`, requiring a parameter or field scrutinee. Full stdout/stderr,
exit code, command, measured duration, and input hash are retained in
`compiler-first.*`.

The single diagnostic repair removes computed-pair destructuring throughout.
Row packing now returns its mask directly, while `List.drop` obtains the next
row. Census destructuring occurs in two helper parameters, following Base's
tuple pattern. The bit-plane census and Life selections are unchanged.

Repair check: exit **0**, stdout `All terms check.`, empty stderr. The exact
checked input is also retained in `repaired.bend.snapshot`; complete logs and
the command receipt are `compiler-repair.*`. **Repair count: 1. First-shot
acceptance: no. Repaired checker acceptance: yes.** No source change was made
after the successful check. No runtime or Perch command was run.

SHA-256:

- First source: `d0251e1e43f29085f5fb0349bc4cff9339eb5769c58fec6f8552f3297643944c`.
- Final source: `4aa35688d6970d1b2a7d03e5f69ace5a84467930feefd5a71d2dcd7969b2c107`.

## Remaining uncertainty

The author has reasoned about the Boolean population circuit, synchronous row
window, clipping, empty dimensions, and structural descent. No runtime behavior,
native-backend behavior, independent corpus, or style target has been observed.
The largest supported width uses all 32 mask bits; smaller widths are clipped
by unpacking before a subsequent public step repacks them. Invalid inputs have
no validation claim.
