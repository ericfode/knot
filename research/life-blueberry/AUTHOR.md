# Identical author packet

Work only in your assigned arm directory in the current Knot worktree. Read
CONTRACT.md before designing. Your assignment gives any additional reading
condition; complete it before forming or writing your implementation.

Aim to meet all current Perch targets: conceptual compression, delight in
reading, and memetic identity. Read the complete perch-style.json and
docs/perch-style.md. Preserve their definitions and thresholds. The new general
ideas research is not the active rubric.

Allowed reference material:

- Root AGENTS.md and README.md; this packet and CONTRACT.md.
- perch-style.json, docs/perch-style.md, docs/perch.md and the Perch skill.
- .toolchain/bend-2.0.29-574b6d3/guide/GUIDE.md, bend2/base.bend and upstream
  compiler/typechecker source or upstream tests needed to learn Bend syntax.
- Your own arm directory and the exposure file explicitly assigned to you.

Do not inspect other arms, evaluator/oracle files, prior experiment outputs,
other chats, memory, network sources, or the bend-tests project. The parent
will provide the exposure material when applicable. Do not run Perch yourself;
the parent performs the required review on frozen submissions with neutral
paths. Do not modify shared rubrics, tests, dependencies, scripts or Git state.

Write life.bend and a short AUTHOR-NOTES.md in your assigned directory.
Before the first compiler invocation, copy life.bend to first.bend.snapshot.
Run scripts/bend-reference <your life.bend> --check-only and retain its complete
stdout/stderr and exit code. If it fails, one compiler-diagnostic repair and one
more check are allowed. Do not run exploratory candidate compilations before
the first snapshot, and do not change the candidate after a successful check.
No runtime test or style feedback is available before submission.

In AUTHOR-NOTES.md record the reading hypothesis and intended mechanism, all
references read, whether exposure was read in full, compiler commands/results,
repair count, remaining uncertainty, and source SHA-256. Then report completion
to the parent. The parent owns evaluation and commits; do not commit independently.
