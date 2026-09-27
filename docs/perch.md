# Perch in Knot

Installed on 2026-09-26: `@lakeday/perch` **0.3.5**, pinned in `package.json`
and `package-lock.json`. Node 22.18 or newer is required. This npm package is
development tooling; it does not choose the compiler implementation language,
bootstrap version, or runtime. Knot remains a Bend 2 compiler design workspace.

The upstream Codex skill is installed at `.codex/skills/perch/SKILL.md`.
Use the npm scripts below to retain local check history. `npm exec -- perch`
still runs the native CLI directly, but bypasses this project's usage receipts.
No global package or shell configuration was changed.

An opt-in [Laya local trial](laya-local-2026-09-26.md) now runs native System One
questions offline through `npm run review:laya`. The pinned English checkpoint
failed the Bend performance controls, and the unchanged style rubric exceeds its
option-description limit. It is experimental evidence tooling, not an accepted
replacement for these reviews. The normal Perch endpoint remains unchanged.

The subsequent [Kev-4B local trial](kev-local-2026-09-26.md), available through
`npm run review:kev`, completed the same frozen requests on Apple Silicon via
MLX. It classified six of eight defect controls correctly and accepted the full
frozen style rubrics, but missed both growing-prefix defects. It remains an
opt-in experimental runner; it is not qualified as the default reviewer.

## Commands

```sh
npm ci                              # restore the pinned tools
npm run lint:rules                  # lists built-in and current custom rules
npm run lint:doctor                 # checks installation and credentials
npm run lint -- src/parse.bend      # current parsed declarations
npm run lint -- src/parse.bend --rules bend-fuel-completeness
npm run perch -- issues
npm run lint:history                # local usage and finding counts
npm run lint:style -- --live src/scope.bend
npm run lint:style -- --live --all  # explicitly requested project style review
npm run lint:verify                 # offline workflow and rule-wiring checks
```

`lint` and `lint:check` invoke `perch check` through `scripts/perch-workflow.mjs`.
They require a file argument, emit JSON, and retain ignored `.perch/usage/`
receipts. The wrapper rejects zero relevant checks and checks with no completed
provider response as failures, not clean results. It records actual model IDs,
raw noul probabilities (including below-floor answers), timing and token usage
when provided; it does not store source bodies, credentials, or provider errors.
The local adapter parses `.bend` before review and records parser identity,
declaration count and dependency diagnostics. All 13 shared source rules use
`each: method`: six Bend, three provisional compiler, and four performance
rules. A file target checks every applicable parsed `def` or law declaration;
`file.bend::function` selects one. Both custom and built-in method questions use
the current working-copy context. Law-review Markdown packets remain file rules.
Zero applicable checks fails visibly; a data-only or imports-only Bend file has
no executable declaration for these rules and must be reported as not applicable.

`lint:style` (`lint:rank` is an alias) assesses existing parsed definitions, laws
and datatypes against **Maximally big brain**, **Delightful to read — high dopamine**,
and **Highly memetic**. No alternative implementation is required. Each unit must
meet all three targets for a style pass; below-target and uncertain ratings are
reported separately from defect findings. The output retains distributions,
context limits and secondary ranks. Run it on materially changed Bend code beside
the relevant semantic checks. See [style targets, commands and evidence](perch-style.md).

Scan, check and style default to 16 workers. Use `--parallel N` for semantic
commands, `--jobs=N` for style, or `PERCH_JOBS` for either (explicit flags win).
The range is 1–256, but larger values overloaded the provider in measured
whole-repository trials. Bounded workers, command-local source/rule snapshots
and batched Git reads preserve review inputs. See the
[throughput measurements and limits](perch-throughput-2026-09-26.md).

The context includes exact local callees and referenced values, transitive
explicit relative imports within the workspace, direct same-file callers,
datatypes, and corresponding law statements. It does not discover arbitrary
repository files, fetch remote imports, or substitute stale committed helpers.
Every used file has a source hash. Context caps are 16 helpers, four callers,
12 files and 48 KB; unresolved references and truncation stay visible in each
unit receipt. The target declaration itself remains complete. A malformed local
helper fails preflight before a model request. A syntactically valid context is
not evidence of type checking or dependency completeness.

Named-declaration checks retain their unit and context identities in the same
`units` receipt array as file checks. Early named-check receipts omitted that
metadata; retain their raw output or supplemental context evidence when auditing
those historical runs. Do not infer missing identities from a newer source tree.

For live checks, privately populate `.env` from `.env.example`, or export
`PERCH_API_KEY` / `TYPESAFE_API_KEY`. Perch loads `.env` from the Git root.
Keys are available from [TypeSafe](https://console.typesafe.ai).
Checks send selected source to the configured TypeSafe endpoint and use API
credits. The user supplied a project key on 2026-09-26; it is stored in ignored
`.env` with mode 0600. Doctor passed and bounded live control checks completed.
The original installation and package receipts predate this credential setup.

## Coverage limits

Upstream Perch 0.3.5 has no Bend registry entry. Knot installs a local extension
through `scripts/install-perch-bend.mjs`, called automatically by `npm ci`.
It verifies the exact upstream bundle version and SHA-256 before changing its
registry, analyzer dispatch, source parsing and explicit local-import resolution.
The extension is repeatable and refuses an unreviewed Perch bundle. Its identity
includes adapter contents so changed parser behavior invalidates scan caches.

The adapter uses the actual Bend 2.0.29 TypeScript parser from commit
`574b6d39a235b539eb19a5c532993a0abb3d11ad`, vendored with its Apache-2.0 license
and provenance under `vendor/bend-parser/`. Additive parser observers capture
declarations and references before lowering. This is a tooling pin, independent
of Knot's eventual language compatibility decision. Tree-sitter remains active
for other languages.

Bend-only committed repositories can now be scanned. Syntax errors are rejected
before a targeted model request. The wrapper also rejects a scan that reports
partial parser coverage. Source spans use UTF-8 byte offsets and columns.
Imported law, constructor and template context is explicitly unresolved during
standalone parsing: analysis never invokes `book_load`, downloads dependencies,
executes a program or checks its proofs. Complexity/risk metrics are unavailable
rather than invented. A static call graph is partial, not a resolution/type proof.

Compiler selectors cover `src/` and `compiler/`. The committed enum frontend
under `src/` supplies applicable parsed declarations; a successful source review
does not establish a completed compiler pipeline or Wasm backend. The shared law
rules cover bounded research packets too. Performance source rules cover growing
prefix copies, invariant recomputation, sequential linked-list indexing and
amortized storage growth. Their calibration and the bounded repair pilot are in
[the performance report](perch-performance-2026-09-26.md).

When supported source exists, `npm run lint:scan -- --since <base-ref>` scans
committed code at `HEAD`. It does not scan uncommitted edits; `lint` does.
Root and split rule files are read from the working copy. Both `check` and
`rules list` currently require a repository with a commit. This workspace
already had commit `3540128` when setup ran.

Perch's doctor reports only rules in root `perch.yaml` (zero here); use
`lint:rules` to confirm the rules in `.perch/rules/`. A successful command
with zero relevant files or rules is not coverage.

## Draft rules and gates

The rules are review suggestions, with an initial confidence floor of 80%.
`source-checkpoint-observation` now uses 70% based on a recorded clean/broken/
held-out comparison; this is preliminary tuning, not a production accuracy claim.
Performance floors are 70% for prefix copying, 60% for invariant work and linked
list indexing, and 80% for storage growth, selected from retained control
comparisons. All have `gate: false`; small control sets do not justify promotion.
Built-in defect/security findings still gate a supported-language `scan`.

Version 0.3.5 treats commands differently: `gate: false` affects **scan**;
**check still exits 3 for a broken custom rule**. Exit 1 means it could not run,
2 means usage error, and 3 means it reported a finding. Review the finding and
confirm it with deterministic checks before changing code. Keep compiler tests
and proof gates separate from Perch.

Before making a rule mandatory, check clean and deliberately broken examples
with `--rules <name> --json`. Keep input, expected label, model version, and
response separate. Require separation of the two cases, then test a held-out
case. Tighten an ambiguous question instead of hiding it behind a higher floor.

Scan exclusions cover generated output, local toolchains, secrets, and known
negative-fixture and performance-experiment directories. Dependencies/build directories are also excluded
by Perch. Explicit `check` targets should be selected deliberately; they can
read a path excluded from repository scans. Commit rules and explained
dismissals in `.perch/closed.jsonl`; generated results remain ignored.

## Installation verification

The package campaign adds eight advisory `law-*` rules in
`.perch/rules/laws.yaml`, plus package-specific rules as work progresses.
They check self-contained `LAW_REVIEW.md` packets for inhabited domains,
substantive observations, public-contract coverage, independent models,
composition, boundaries, valid semantic mutation evidence, and truthful proof
claims. Follow [the deterministic law gate](LAW-QUALITY-GATE.md); a model verdict
cannot replace it. These additions are distinct from the initial nine-rule
installation checks below. Live calibration now has retained evidence in
[the audit report](perch-audit-2026-09-26.md), including missed bad controls.

## Ongoing maintenance

Root [AGENTS.md](../AGENTS.md) makes targeted checks and evidence capture part
of the development workflow. The [maintenance procedure](perch-maintenance.md)
surveys wasted effort and Perch signal weekly, while the
[review log](perch-review-log.md) records decisions. Routine, evidence-backed
configuration changes are user-authorized. Existing deterministic gates and
package ownership continue to apply. Historical unavailable-calibration
receipts are preserved; new live evidence does not rewrite past observations.

### Original installation checks

The eight law rules have a separate offline CLI integration check:
`node scripts/check-law-rule-wiring.mjs`. It verifies all eight are selected for
package, nested-family and control packets in one request, named filtering
works, an advisory finding exits 3, and unrelated Markdown selects none.
No provider is contacted. Clean/broken/held-out specimens are recorded in
`tests/perch-laws/cases.json`. Their first live run classified 19/24 correctly;
five known violations were missed. The two regression packets also expose
misses in their intended rules. All shared rules remain advisory.

- Installed CLI reports 0.3.5; all nine custom rules parse and are listed.
- A temporary Git fixture with a `.bend` file under `src/` exercised the actual
  packaged CLI against a stubbed provider: all nine rules were sent in one
  request, rule filtering worked, and a reported violation produced exit 3.
- The original Bend-only fixture reproduced upstream `scan`'s unsupported-source
  failure. The later local adapter supersedes that installation limitation.
- Doctor passed Node, Git, repository, commit, output, and root-config checks.
  Its remaining failure was the absent API key.

These checks establish installation and rule wiring, not model quality or
compiler correctness. The setup introduced no compiler implementation and
made no changes to Bend Scrabble or the shared Bend libraries.

References: [Perch](https://github.com/lakeday-org/perch),
[rule documentation](https://docs.perchscan.com/rules/),
[command reference](https://docs.perchscan.com/cli/).
