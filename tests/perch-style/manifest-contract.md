# Manifest expectations (fixed before implementation)

Literal review, 2026-09-27, against campaign D7. This is tooling; no compiler
language capability, rubric, deterministic compiler assertion or Bend law changes.

- JSON schema 1 contains a nonempty `groups` array. Each group has a unique
  nonempty `name`, an ordered nonempty `files` array of distinct workspace Bend
  files, optional `task` (a workspace contract path) and optional string `notes`.
  Paths are workspace-relative, including when the manifest is under `docs/`.
- `--manifest=FILE` selects all groups in order. `--group=NAME` selects exactly
  that group. Reject unknown/duplicate/empty options, malformed groups, escaped
  paths, positional targets, `--all`, and run-wide task/cohort overrides.
- Each group uses the existing explicit-target declaration review and one
  composition. Shared declarations count once per group obligation. Notes are
  receipt metadata, never rating instructions. Missing/overlong tasks remain
  advisory, exactly as for explicit targets.
- Declaration states and requests equal explicit-target states and requests.
  Composition files start in manifest reading order; remaining known local
  collaborators follow in lexical order. The existing closure and 48,000-byte
  checks apply without weakening. Missing closure is reported, never excused.
- Every selected group is prepared before any provider call. Preflight never
  loads environment files, touches caches, writes usage receipts or calls a
  provider. It reports each group's truncations, role gaps, composition and an
  overall structural summary. Unavailable composition and truncated declarations
  cause exit 3; role gaps alone retain leading targets.
- Live run qualification is the conjunction of all selected group qualifications,
  source/task/manifest freshness and one resolved model identity. A filtered run
  qualifies only its selected group, never the entire manifest. Exit 1 denotes
  failed/incomplete review, 3 completed attention, 0 qualification.
- Reuse remains exact-request based, including composition order. Later groups
  cannot hide earlier source changes or provider failures. A provider failure
  stops new groups, retaining completed and failed-group evidence.
- Existing explicit-target and `--all` preflight JSON, stable live report JSON,
  and raw mock-provider request bytes are pinned from unmodified `185b7d5`.
  Only dates and measured durations are removed from live report comparisons.

Semantic mutant witnesses: reverse/lexically sort the manifest composition order;
accept one passing group despite another failing; grant whole-manifest success
to a filtered run; omit final aggregate freshness. Each must parse successfully
and fail an unchanged behavioral assertion, not fail during module loading.
