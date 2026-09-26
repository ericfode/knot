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
- For a bounded repair experiment, use **Luna 6 only**, never Luna 5.6. Retain
  the original contract and immutable independent tests. Record first-shot
  success separately from a single compiler-diagnostic retry; reject remaining
  failures instead of changing tests or silently hand-fixing the model's output.
  See docs/perch-performance-experiment-protocol.md and the experiment report.
