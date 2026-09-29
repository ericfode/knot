# Pre-review checks (`prechecks`)

One command that runs before the expensive review and lists, in seconds, the findings a script can find:

```sh
npm run -s prechecks -- [--base <ref>] [--json]      # the current tree against its base
```

(If your shell aliases `npm` to a wrapper that prints a banner, use `command npm run -s prechecks`, or run
`python3 -B scripts/prechecks/run.py` directly. `--json` prints only JSON on stdout; progress goes to stderr.)

## Why

Each increment ran implementers, then three reviewers (scope, gates, semantics) that each re-exported the branch and
re-ran about ten minutes of gates, then verifiers, fix rounds and a re-review. Rounds took one to two hours, and most
increments needed three to nine. The mined history is 1,100 findings in 75 review rounds; 68 rounds carried at least one
unrefuted blocking or major finding, and many findings were cheap to detect by a script: stale documents, claims that
contradicted receipts, an upstream control that no consumer ran, a frozen expectation edited, a host path in a receipt.
The same fact was re-filed round after round (the missing `last.txt` 24 times, the runner's `fixtures: 2` count 12 times).
A defect class that a small generated grid would have listed before review (the D4 gaps) forced whole follow-up
increments. The design and its evidence are in the prechecks design record; this page is what was built.

Every check has one shape: **compare two views of one fact and report only where they disagree.**

| Check | Two views compared | Kind |
|---|---|---|
| C1 `probe-differential` | the seed's verdict on a program against Knot's parse, check and eval lanes, at head and at base | deterministic |
| C2 `merge-forecast` | the branch against main, its upstreams and its merge-order siblings | deterministic |
| C3 `frozen-and-owned` | base against head for frozen and owned artifacts, and the history between them | deterministic |
| C4 `receipt-integrity` | a committed receipt against the tree it describes | deterministic |
| C5 `preflight-delta` | the offline Perch style preflight at base against head | deterministic |
| C6 `claims-vs-facts` | prose, reports and commit messages against measured facts | deterministic |
| C7 `gate-adequacy` | a gate's claims against its witnesses and its verdict function | deterministic |
| C8 `perch-coherence` | a documented claim against the code or diff that decides it | Perch, advisory |

## Running it

```sh
npm run -s prechecks                       # everything, working copy against merge-base(main)
npm run -s prechecks -- --only C3,C4       # some checks
npm run -s prechecks -- --head <rev> --base <rev> --inc <id> --main-ref <rev> [--upstream vm-spec=<rev>]   # replay a committed revision
npm run -s prechecks -- --tier slow        # the same checks with their minute-scale extras
npm run -s prechecks -- --list
```

- **The tree.** By default the head is the *working copy*, including uncommitted and untracked files, read through a private
  git index (`.env*` is excluded by pathspec, never opened). `--head <rev>` judges a commit instead, from git objects only.
- **The base.** `--base <ref>`, else the merge-base with `main`. An increment stacked on another unmerged increment
  (vm-core on vm-spec) declares `upstream` in its manifest, or passes `--upstream id[=ref]`; its base is then the
  descendant-most of the main merge-base and the upstream merge-base, or, when neither contains the other, the tree of a
  trial merge of the two. Upstreams are declared, never inferred from topology: a branch created from X and X share history
  in both directions.
- **Exit status.** 0: no new or changed *executor-actionable* condition at or above `--fail-on` (default `major`). 3: at least
  one. 1: a check crashed (never silent). 2: usage error. Conditions that only the coordinator or an upstream can resolve
  never fail the run, and `unavailable` is never a pass. One consequence: the vm-core `a5e2ffa8` replay of C2 lists the
  unconsumed `run_controls` but exits 0, because its actor is `upstream`; no flag turns coordinator or upstream conditions
  into a failure, by design (an executor cannot merge or rebase).
- **Output.** A terminal summary (twelve conditions per rule; the rest are in JSON), and in `.local/prechecks/<head8>/`:
  `report.json`, `report.md`, `facts.json` (the measured facts), `known.txt` (lines for the review harness's `known`
  argument). `--emit-ledger` prints ledger entries that would acknowledge every new condition.
- **Time.** Measured on this host (Apple Silicon, four jobs, `python3 -B scripts/prechecks/run.py --no-write` on the prechecks
  branch, working copy against main): 26 s on the first run after a source change (C1 builds the head lanes and runs the
  corpus) and 10.9 s on the immediately repeated run (lanes, seed verdicts and base outcomes cached by tree and program
  hash). Main against main (`--head 43a394a4 --base 43a394a4`) took 28 s on a cold cache, with C2 and C3 skipping as an
  identity. The dominant check is C1; replays of historical increments took 4 to 32 s each.

### Conditions, fingerprints and the ledger

A condition names its check, rule, severity (`info`, `minor`, `major`, `blocking`) and **actor**: `executor` (fixable by a
commit on the branch), `coordinator` (a merge, sign-off, ledger or manifest entry, a shared-receipt refresh) or `upstream`.
Executors never merge or rebase, so coordinator conditions go to `known.txt` and the merge list, never to the implementer.

The fingerprint hashes the check, rule and a subject key without line numbers (a path and JSON pointer, a probe hash and
lane, a commit), so it survives unrelated edits. `docs/compiler-campaign/known-conditions.json` lists acknowledged fingerprints. The coordinator creates and owns it
(it does not exist yet, and the suite runs with an empty ledger); it is read **from main**, never from the branch, so a
branch cannot silence its own condition.
A matching fingerprint and value is `known`; a matching fingerprint with another value is `changed`; anything else is `new`.

### The increment manifest

`docs/compiler-campaign/increments/<id>.json`, written by the coordinator at launch and read from main (none exists yet;
`--manifest <file>` supplies one). Only `id` is required. Fields: `upstream`, `merge_before`, `owns`, `appends`, `frozen`, `receipts`, `impl`, `expectations`, `authorized`
(the only source of authority: a commit message never authorizes), `consumes`, `d4_targets`, `limits`, `coverage`,
`required_laws`, `charter`, `generators`, `executor`, `freeze_first`. A missing manifest yields defaults, and a rule that
needs a declaration (C3's write scope, C7's limits) reports that instead of guessing.

## What each check catches

Rules are listed with their severity and actor. "Motivated by" names findings from the mined history.

### C1 probe-differential

Replays every reviewer probe as a permanent control. The corpus is the registry harvested from dev-round probes
(`tests/prechecks/registry/lang.jsonl`, 117 programs with pinned-seed verdicts), tracked fixtures that carry seed
observations, and deterministically generated programs, at most 1,000 in the whole corpus per fast run (500 on a cold base
cache): grids (parameters, fields, tails after a
constructor head, return types, annotations, binder spellings, empty datatypes, let marks, literal forms) and operators (gaps
at token boundaries, literal substitutions, layout moves), weighted toward the families the changed sources are likely to
disturb. The pinned seed judges each program (its own `parse_book` in process, `--check-only`, a run), cached by program hash;
Knot's parse, check and eval CLIs are built from head and base with the seed's JS lane and run on the same programs.

`d4-invalid` (major: the seed accepts, a lane says Invalid), `unsound-accept` (blocking: the seed rejects, a lane says
Checked or yields a value), `crash`, `value-disagreement`, `premature-unsupported`, `diagnostic-shape`,
`incomplete-repair` (major: a violation that base already had, in a family the manifest lists in `d4_targets`).

**Ratchet.** Only a violation that head adds is a condition, and a verdict that was acceptable at base and is not now is
raised one severity step. A violation present at both is a known gap of the D4 ledger, reported as a fact (`d4_gaps`).
Programs the seed itself cannot judge (timeout, crash) are never flagged.

Motivated by: classify's eight verified majors and the follow-up increment they forced; classify-2's regressions from its own
fix; the detached constructor brace, found by nest, again by generics and again by modules; the empty datatype, found three
times; dotted binders; gapped Nat `+`. Replays (`--head <rev> --base <rev>`, main-side base as reconstructed by the design):

| Head (base) | Result |
|---|---|
| classify `5e5b2201` (`185b7d5f`) | exit 3, 58 failing: `Unsupported parse destructuring-binding` for `= \|x`, `= ~x`, `= x => x` and `template-binder` for `~~b:`, forms the seed's parser rejects later (the `==`/`=>` and `~` regressions) |
| classify-2 `7b85b8aa` (`fa31fec0`) | exit 3, 5 major: `Flag<Flag>>`, `Flag<>` and `Flag<x>=` read as `type-application` before the seed's error offset (the `Name<` regression) |
| nest `eb15da85` (`3c25d9be`) | exit 3, 4 blocking: a dotted binder accepted at parse and check lanes, an empty-typed binder turned Invalid, a moved type accepted |
| classify `5e5b2201`, with a hand-written manifest declaring every grid family in `d4_targets` | 184 `incomplete-repair` majors, for example `Flag<Flag, Flag>` and `@x: Flag -> Flag` as return types and `let x.y.z` |

Main against itself yields no condition; the 155 seed-accepted forms that Knot calls Invalid on main are reported as facts
(`d4_gaps`), not conditions.

### C2 merge-forecast

Trial merges (`git merge-tree`, no checkout touched) with main and each sibling in `merge_before`. Conflicts in the
generated-file registry (`inventory/*.json`, `run.py`, `test_runner.py`, `GATES.md`, the review log, `package.json`,
shared receipts) become known merge conditions with their mechanical resolution; any other conflict is `conflict` (major,
coordinator). Also: `base-fix-missing` (a main commit to the runner, host or owned paths that the branch lacks), `decision-drift`
(a decision row changed on main; its superseded literals found in the branch's normative docs), `upstream-contract-unconsumed`
(a control that the upstream's green tip newly exports and no consumer references; the green tip is the newest first-parent
commit whose committed receipt says passed with input hashes that still match), `brittle-upstream-coupling`, `oracle-behind`,
and `census-after-merge` (census `--check` on the trial merge, with inventory conflicts resolved to main's copy first).

Motivated by: vm-core `a5e2ffa8` exporting-but-never-running vm-spec's `run_controls` (replayed: found), the clang fix `90b4052`
missing from io-abi-2, 16 re-filed merge minors, the inventory conflict re-derived in 15 vm-spec rounds.

### C3 frozen-and-owned

`out-of-scope-edit` (needs a declared `owns`), `shared-file-shape` (run.py: only added Gate rows; test_runner.py: only added
names; GATES.md and the review log: only added paragraphs; approved.json and the manifest: additions), `frozen-edit`
(blocking for other gates' assertions and expectations; authorization is read from main), `assertion-weakened` (a removed
`require`/`assert`/`raise`, `x[k]` to `x.get(k)`, `==` to `in`/`>=`, a widened bound, a shrunken MUTANTS or controls list),
`coverage-dropped` (a receipt's mutants, fixtures or accepted counts shrank, with the removed names), `frozen-row-changed`
(a base row of a frozen data file changed; an `amend:` line makes it known), `freeze-order` and `provenance-mismatch`, history
lints (`commit-trailer` naming the executor family, `red-commit-wording`, `census-approval-summary`, `mixed-gate-commit`),
`normalized-comparison`, `generator-not-reproducible` (declared generators only) and `red-tip` (`census --check` fails; the slow
tier adds `census:test`, which takes about 25 s on this host and is not a registered gate).

Motivated by: generics deleting three classification mutants and shrinking coverage; nest's Wasm rejection pairs 64 to 62 and
fuzz count 426 to 242; a control comparator loosened from `observed[k]` to `observed.get(k)`; modules' `census:test` red at 78
of 79; expectations committed in the same commit as the implementation.

### C4 receipt-integrity

Scope is receipts changed between base and head, never the whole tree (52 tracked receipt and evidence files on main already
contain `/Users/` paths). `host-path` (major), `stale-receipt-hash` (a recorded input hash differs from the recomputed one, ratcheted:
a hash already stale at base is not re-reported), `decorative-hash`, `unowned-receipt-drift-predicted` (info, coordinator: a
receipt whose recorded input this branch changed), `corpus-glob-coupling` (added `.bend` files enter the bootstrap corpus),
volatility (measurements, README inputs, orphans, duplicates, more than three preflight receipts), `receipt-date-only`
(a receipt commit that changes nothing after normalization), and, from the implementer's own gate run (the newest
`.local/gates/run-*/summary.json` whose snapshot equals this tree): `gate-red`, `own-receipt-stale`, `unowned-receipt-drift`. If no
run matches, that rule is `unavailable`; the slow tier runs the gates itself.

Motivated by: opt-1's 12,276 host paths; perch-context sending a home path to the judge; generics' 12 stale hashes; gpu-2's
README in a receipt's source hash; the six unowned-drift and six sign-off majors that were merge conditions, not executor rework.

### C5 preflight-delta

`node scripts/perch-style.mjs --preflight --json` is offline (zero provider requests) and never loads a dotenv file. It runs on
exports of head and base (the base on the targets as they existed there; results cached by tree). `preflight-new-blocker` (a
unit newly truncated), `composition-budget` (each changed file preflighted alone against the 48,000-byte cap: a sole-member
file over it is major; manifest groups that lost their composition or fell under 2% headroom), `unit-cap` (the full manifest
run aborts at 5,000 units), `manifest-membership`, `task-provenance`, `bend-hygiene` (a non-ASCII byte or a divider comment
in an added `.bend` line) and `perch-identity-change` (a parser profile or rubric change with no review-log entry, or a
judge-facing sentence that disappeared). Absolute blocker counts are never findings: 25 to 137 exist at every base.

Replayed: recursion `624228e5` newly truncates `src/scope.bend::contains`; vm-model `e38afc32` composes 144,319 bytes in one
file and adds section dividers and `§` characters that put its files into Knot's non-ASCII lexer class.

### C6 claims-vs-facts

A facts table (`facts.json`: registered gates, required names, per-gate receipt list lengths, law counts, census counts) against
claims in the changed paragraphs of GATES.md, `tests/**/README|SPEC|REPORT.md`, the handoff report and commit messages. Only
added lines are judged. `stale-count` (a number paired with a counted noun, only when a backticked gate name attributes the
paragraph and the noun is not a breakdown), `retired-term` (a superseded literal such as D19's 2,048 pages, unless its context
says superseded), `missing-path` and `untracked-evidence`, `report-missing`/`report-stale`/`report-gates`, `hardcoded-count`,
`count-extraction-shape` (a generic receipt key that is not a list, which the runner would mis-count), `ground-law-general-name`
and `vestige`.

Motivated by: "All 18 gates passed" with 17 registered; the hard-coded `proof_laws: 37` behind 15 findings; vm-core's dict-valued
`fixtures` reported as 2; the D19 literal left in two documents, a memory declaration and three acceptance bars.

### C7 gate-adequacy

Static rules: `limit-unwitnessed` and `witness-missing` (from the manifest's declared `limits` and `coverage` cells; a control
is matched by a machine-readable `boundary: {limit, value}` field, else a numeric literal, and that is labelled heuristic),
`unscaled-timeout` (a fixed timeout in a changed gate script), `gate-wiring` (a new check script or gate row that the runner
registry and its self-test do not know) and `gate-headroom` (a gate over half the runner timeout in the matching run).
Adapters (`scripts/prechecks/adequacy/<gate>.py`, run only for a gate the branch touched) are the hook for the verifier-soundness
rules; no adapter ships in this build, so those rules report nothing rather than pretend.

Motivated by: fixed timeouts at four of six tips, judge-forgery findings that drove three of five fix rounds in harness-2 and
joint, the witness matrix with no False golden, key 0xFFFFFFFF and Char tags-mode cells unwitnessed.

### C8 perch-coherence (advisory)

Seven `each: file`, `gate: false` rules in `.perch/rules/prechecks.yaml`, one packet directory each:
`claim-holds-against-evidence`, `passages-agree`, `outcome-follows-d4`, `clause-vs-delta`, `expectation-independent`,
`kill-is-semantic`, `required-laws-met`. The deterministic builder writes self-contained Markdown packets (Claim, Evidence, Scope)
from git objects only, so rebuilding is byte-identical and a packet built anywhere can be checked anywhere:

```sh
npm run -s prechecks:packets -- --repo <path> --out <dir> [--head <rev>] [--base <ref>] [--inc <id>] [--rules a,b] [--limit 40]
# writes <dir>/<increment>/<head8>/<rule>/<n>.md
```

Claims are selected by mechanical triggers (absolute words, invariance verbs, identifiers, numeric budgets) and ranked by how
much of the claim the diff speaks about; evidence is ranked the same way, at hunk level for modified files and declaration
level for added ones, capped at 12 KB with a truncation marker and 48 KB per packet. A packet whose evidence does not resolve
is reported `unavailable`, never written. The check builds them into `.local/prechecks/packets/` and raises no condition: a packet
is a question, not a finding.

**Live use belongs to the coordinator, from the main checkout** (the credentials live only there; never copy or read an `.env`):

```sh
node scripts/prechecks-perch-run.mjs --controls                 # dry run (the default): what would be asked, zero requests
node scripts/prechecks-perch-run.mjs --controls --live          # calibration: one request per packet
node scripts/prechecks-perch-run.mjs --live --packets <dir>     # ask about a built increment
```

The runner uses the retained-receipt wrapper (`.perch/usage/`), refuses a linked worktree, and stops on the first
authentication or quota failure. It has never been run live in this build. Calibration follows `docs/perch-maintenance.md`:
run the [controls](../tests/prechecks/perch-controls/README.md), require every broken packet at or above the floor and every clean one
below it, freeze the rule text, then run the held-out packets; keep `gate: false` until adjudicated production findings
exist; a rule that does not separate is rewritten or narrowed, never floor-raised. The offline wiring test
(`scripts/check-prechecks-rule-wiring.mjs`, stubbed provider) proves selection and plumbing only. The built-in `docs`
category selects nothing on a packet, so it is not a baseline.

## How it is verified

`npm run -s prechecks:verify` (gate `prechecks`) runs offline, with no provider, network or credentials:

1. every unit test in `scripts/prechecks/tests/`, each rule against a synthetic clean and a synthetic broken repository (every
   test builds its own git repository, never the real one);
2. a fixed set of semantic mutants of the checks, each of which must be killed by the unit test that pins its rule;
3. the Perch rule wiring test.

`npm run -s prechecks:test` runs only the unit tests. Historical controls (classify, generics, vm-core, vm-model, recursion)
belong to the replay command above, not to the registered tests, because the gate's export has no history.

## Pipeline integration (for the coordinator)

These edits live in the campaign harness, outside the repository:

- **Implementer, before returning `complete`:** run `npm run -s prechecks -- --inc <id>`; fix every new or changed *executor*
  condition of major or higher severity (exit 3), or dispute each with evidence in `.local/<id>/HANDOFF.md`. Coordinator and
  upstream conditions are mentioned, never worked. Repeat after each fix session: the grid lists a regression in minutes.
- **Before review:** run it once more; pass `facts.json`, `report.md` and `known.txt` to the review workflow as
  `known: [...known, ...prechecks.known]`, and tell the lenses that an unchanged fingerprint is not a finding.
- **The gates lens** drops "compare with last.txt" and "run preflight and report blockers", and spot-checks one fact from
  `facts.json`. **The preamble** takes the executor trailer and the gate count from the tree, not from prose.
- **Ledger and manifests:** seed `known-conditions.json` (the Digest blocker, the six closure-golden rows in the bootstrap corpus,
  the dotted-binder and empty-datatype rulings) and write a manifest at each launch.

## Limits and what is not built

- **Family V** (VM image lanes: reference evaluator, `run-wasm-io`, the model binary, the laundering matrix) is not built;
  the tree on main has no `vm/`. C1 reports it unavailable when `vm/evaluate.py` exists. The harvested plans are stored in
  `tests/prechecks/registry/vm.jsonl` for it. Likewise R8 (helper lanes) needs declared helpers.
- **C2 R9** (forward-merge replay of upstream goldens through the downstream lanes), **C7 R3-R5** adapters and the C1 model lane
  are slow-tier work that needs those lanes.
- **The seed budget**: at most 200 uncached seed check runs per fast run; the rest are completed over later runs (the cache is
  shared across branches) or in the slow tier, and the shortfall is reported as `unavailable`.
- **Selection is lexical.** C8 packets and C1 samples are chosen by mechanical triggers, so recall is bounded: the calibration
  set records two defects (vm-spec's section 6 and section 9 passages; vm-model's `inspection_runs`) that selection does not reach.
- **Advisory Perch verdicts** are never findings until confirmed deterministically (AGENTS.md).
- **Held-out discipline.** Rules were derived from dev-round instances. The design's held-out rounds (review started at or after
  2026-09-28T12:00Z) were not used for tuning: their probes sit in `.local/prechecks/quarantine/` (untracked, copied unread) until
  replay has measured held-out recall, and the held-out calibration packets were built from the design's control table. Two
  exposures, both recorded in the [controls README](../tests/prechecks/perch-controls/README.md): vm-spec `5517f263` moved to dev
  when its passages were read to fix the P3 builder (DESIGN 1.4, rule 3), and one held-out literals finding was printed during
  orientation (nothing was derived from it).

## Adding a check or a rule

Write the rule as a small function over the run context (`lib/context.py`: two trees, the diff, the commits, the manifest),
return `Condition`s with a fingerprintable subject (no line numbers), an actor and a severity, ratchet against base so an
existing condition is not new, and add a synthetic clean and a synthetic broken control to `scripts/prechecks/tests/`. Register
a semantic mutant of the function in `tests/prechecks/check.py` so that a vacuous rule cannot pass. Calibrate against every
document on main first: a rule that fires on legacy files that the branch did not touch is scoped wrongly.
