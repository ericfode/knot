# Knot workflow

Read README.md for current project decisions and the closest local AGENTS.md
before editing. Preserve other chats' work and package ownership boundaries.
The deterministic proof and package gate is docs/LAW-QUALITY-GATE.md.

## Git checkpoints

- Start each increment with `git status --short --branch` and inspect existing
  changes. Keep package and chat ownership boundaries explicit.
- Commit a coherent, verified increment before handing it off. Stage explicit
  paths and inspect the staged diff; do not accumulate completed work as an
  untracked working tree. A checkpoint may contain incomplete research when its
  state and unrun gates are clearly recorded.
- Preserve concurrent edits. Never reset, stash, switch a shared checkout's
  branch, or commit another chat's new work without authorization. The user's
  2026-09-26 request to commit everything authorizes the initial repository-wide
  checkpoint; subsequent increments retain normal ownership boundaries.
- Keep credentials, dependency installs, build directories, and interpreter
  caches ignored. Preserve deliberate generated-code examples and evidence
  receipts referenced by the documentation.
- After committing, inspect `git status --short --branch` again. Report commit
  IDs and any remaining changes with their owner or reason. Do not claim a clean
  checkout while another chat is writing. Follow `docs/GIT-WORKFLOW.md`.

## Perch during development

- Use the installed .codex/skills/perch/SKILL.md and docs/perch.md. Run targeted
  checks on materially changed Bend files and bounded LAW_REVIEW.md packets
  before handing off an increment. Use `npm run lint -- <path> --rules <names>`;
  the wrapper records local usage for later review. Avoid repeated unchanged
  checks and whole-repository scans for a small change.
- Bend uses the pinned parser adapter installed by `npm ci`; syntax validation
  precedes review. Shared source rules use parsed `def` and law declarations.
  A file target fans out over its declarations; `file.bend::name` selects one.
  Explicit local helpers, callers, datatypes, and law context are included from
  the working copy, with hashes and truncation markers. Read those limits.
  Markdown law-review packets remain file rules. Require nonzero relevant checks.
  A missing key, provider error, incomplete request, or zero coverage is not a
  clean result. Record the blocker once and continue deterministic work; do not
  keep retrying the same unavailable credential in one increment.
- Read findings before changing code. Prove or test a suspected defect. Label
  findings confirmed, false-positive, duplicate, or unresolved with evidence.
  Never weaken an accepted law or change correct code to satisfy a model.
- After repeated failed attempts, substantial avoidable rework, a missed defect,
  or a noisy rule, append a concise evidence-linked entry to
  docs/perch-review-log.md. Record what would have prevented the waste. Report
  elapsed time only when measured; do not invent it from the number of attempts.
- The user authorized ongoing Perch configuration maintenance on 2026-09-26.
  Add, narrow, combine, or retire rules autonomously when evidence warrants it;
  this authorization supersedes the upstream skill's generic request to ask
  before adding a rule. Follow docs/perch-maintenance.md. Keep draft rules
  advisory, use clean/broken/held-out controls, and preserve package ownership.
  Do not introduce new approval loops for routine configuration maintenance.
- Perch is semantic review. Syntax/type/quantity/proof acceptance and supported
  backend behavior remain deterministic gates. Missing live calibration is
  unavailable evidence, not permission to claim a pass or a reason to abandon
  otherwise verified work.
- The user's later 2026-09-26 instruction authorizes stronger models for fixes,
  superseding the Luna-6-only restriction. Use **GPT-6 Astra at high reasoning**
  for confirmed Perch repairs; Luna 5.6 remains excluded. Retain the original
  contract and immutable independent tests. Record first-shot
  success separately from a single compiler-diagnostic retry; reject remaining
  failures instead of changing tests or silently hand-fixing the model's output.
  See docs/perch-performance-experiment-protocol.md and the experiment report.

## Style objective: high dopamine to read

- When writing or refactoring Bend, optimize for a rewarding reading experience
  for a technically fluent reader: high conceptual payoff per line, satisfying
  symmetry, rhythmic layout, exact names, and compact composition. Aim for
  repeated moments where the notation clicks and the structure feels inevitable.
- Keep two independent style rankings: **Maximally big brain** rewards a small
  expressive algebra or representation that absorbs cases and exposes invariants;
  **Delightful to read — high dopamine** rewards the pleasure of recognizing and
  tracing that structure. Each abstraction should explain more than it adds.
- Terse names, symbolic structure and learned idioms are welcome when their
  vocabulary is consistent and their relationships can be followed. Comments
  should explain conventions, invariants or surprising decisions. Verbosity,
  beginner familiarity, minimum line count and cleverness alone are not goals.
- For substantial implementation alternatives sharing a contract, use a bounded
  comparison with `npm run lint:rank -- --live --cohort='shared task or contract'
  file-a.bend::name file-b.bend::name`. Select actual parsed declarations and
  inspect their helper context. Follow [the style guide](docs/perch-style.md)
  and [the ordered rubrics](perch-style.json); avoid unchanged repeat reviews.
- Report the two rank orders separately, retaining distributions, near ties and
  context limits. A small score gap is a weak preference; ranking first does not
  establish a decisive winner. These judgments remain advisory. Preserve the
  accepted contract and deterministic type, quantity, proof, backend and
  performance gates when making a style improvement.
- Refine the rubrics from concrete reading experience and human preferences
  recorded before model review, with fresh held-out comparisons. Record noisy
  preferences or incentives toward obscurity in docs/perch-review-log.md and
  follow docs/perch-maintenance.md. Optimize the code's reading experience;
  do not chase scores through self-praise in comments or needless rewrites.
