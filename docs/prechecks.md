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
  git index (`.env*` is excluded by pathspec, never opened, and so are `.toolchain`, `node_modules`, `.local` and `build`, which
  worktrees share as links or generate). `--head <rev>` judges a commit instead, from git objects only, and takes the increment
  id from the one `campaign/<id>` ref that names that commit (never from the invoking checkout's branch: one commit gets one
  verdict from every checkout). A commit no campaign ref names runs without an increment and says so; `--inc <id>` names it and
  `--inc none` says there is none.
- **The base.** `--base <ref>`, else the merge-base with `main`. An increment stacked on another unmerged increment
  (vm-core on vm-spec) declares `upstream` in its manifest, or passes `--upstream id[=ref]`; its base is then the
  descendant-most of the main merge-base and the upstream merge-base, or, when neither contains the other, the tree of a
  trial merge of the two. Upstreams are declared, never inferred from topology: a branch created from X and X share history
  in both directions.
- **Outcomes.** `pass` means every rule of the check ran and found nothing. A check that found nothing but had a rule that did not
  run (no manifest, no gate run, no adapter, a target that does not parse) is `partial`, and one that could not run at all
  (the seed or bun missing, the lanes did not build, a timeout) is `unavailable`; `not-applicable` carries a declared reason
  (no `src/parse-cli.bend` in the tree). Neither `partial` nor `unavailable` is ever printed, filed or counted as a pass: the
  terminal summary lists every rule that did not run as `not run  <rule>: <reason>`, `report.md` lists them under "Checks
  and rules that did not run (never a pass)", and `facts.json` carries a `coverage` table (outcome, rules run, rules not run
  with reasons) for the reviewers.
- **Coverage.** Each check declares its rules (`Check.rules`, the names its docstring documents; a unit test compares the two), and
  every rule ends a run in exactly one of three states: it **ran**; it **could not** (`rules_unavailable`: a gap, with its reason);
  or it had **nothing to check** (`rules_not_applicable`: an absent input artifact such as `oracles/manifest.json` or `vm/`, an
  empty diff, a manifest that declares no siblings; not a gap, printed as "nothing to check" and listed with reasons in `report.md`
  and the `coverage` table). A rule that the check did not report at all is made unavailable with the reason "not reported by the check",
  so a forgotten or renamed rule is a loud gap; every check test asserts that none is silent. An undeclared input is unavailable
  (no `merge_before`, no `upstream`, no `owns`), a declared empty one is not applicable. A group alias (`family-l`, `preflight`)
  stands for its member rules. The gates lens keys on these names.
- **Exit status.** 0: no new or changed *executor-actionable* condition at or above `--fail-on` (default `major`). 3: at least
  one. 1: a check crashed (never silent). 2: usage error. 4: only with `--strict`, when nothing else failed but some check or
  rule did not run. The default lets an implementer proceed on the rules that could run (until a manifest, a gate run and the
  adapters exist, nearly every run is partly unavailable), and the harness that needs "everything ran" passes `--strict`.
  Conditions that only the coordinator or an upstream can resolve never fail the run. One consequence: the vm-core `a5e2ffa8`
  replay of C2 lists the unconsumed `run_controls` but exits 0, because its actor is `upstream`; no flag turns coordinator or
  upstream conditions into a failure, by design (an executor cannot merge or rebase).
- **Hang guards.** Each check has a budget that is multiplied by `KNOT_GATE_TIMEOUT_SCALE` (default 4): C1 180 s, C2 80 s, C3 100 s,
  C4 60 s, C5 120 s, C6 80 s, C7 80 s, C8 80 s. A check that overruns is reported `unavailable` with the reason `timeout after Ns`,
  never a pass, and it is stopped, not just relabelled: every tool it started runs in its own process group, which is killed,
  and its pools of queued tool runs stop starting new ones (forced with `KNOT_GATE_TIMEOUT_SCALE=0.05`, a check with twelve
  queued 30-second tools ends in under a second). The guards are hang detectors, not expected times. In the earlier loaded sweep (see Time),
  four replays reported `unavailable` (generics C2 and C5, harness-2 C2, literals C4; the reasons were not recorded, and C4's old
  guard of 20 s was the tightest); after the guards were raised each of the four produced a result. C4 alone on the 581-file
  literals increment (`3246fa3d`) took 9 to 15 s in four measurements at load averages of 20 to 46.
- **Output.** A terminal summary (twelve conditions per rule; the rest are in JSON), and in `.local/prechecks/<head8>/`:
  `report.json`, `report.md`, `facts.json` (the measured facts and the coverage table), `known.txt` (lines for the review
  harness's `known` argument). `--emit-ledger` prints ledger entries that would acknowledge every new condition.
- **Time.** Measured on this host (Apple Silicon, four jobs, load average 10 to 20), from a fresh `git clone --shared` of this branch
  (no `.local`): the whole suite on the working copy against main took **9.4 s cold** and **6.0 s warm** (`python3 -B
  scripts/prechecks/run.py --no-write`; the branch does not touch `src/`, so head and base share their lanes). C1 alone on a head and a
  base whose `src` differ (classify-2 `7b85b8aa` against `fa31fec0`, both lane sets built and about a thousand programs run through three
  lanes each) took **17.2 s cold** and **0.35 s warm**, and a documentation-only child of that head is a warm run because lanes and outcomes
  are keyed by the `src` subtree. `python3 scripts/prechecks/replay.py` (ten historical contexts, each run twice, cold caches for the
  historical trees) took 88 s. The earlier robustness sweep of the whole suite on one historical dev head per increment (20 increments,
  host load average 40 to 90, before the corpus was fixed) took 2.9 to 153.6 s per replay (median 43 s). "Well under a minute" holds for the
  suite at moderate load; the hang guards above are what bound it on a loaded host.

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
(`tests/prechecks/registry/lang.jsonl`, 119 programs with pinned-seed verdicts), tracked fixtures that carry seed
observations, and a fixed sample of generated programs (`scripts/prechecks/lib/generate.py`): grids (parameters, fields, tails after
a constructor head, return types, annotations, binder spellings, empty datatypes, let marks, literal forms) and operators (gaps at
token boundaries, literal substitutions, layout moves) applied to the registry. Knot's parse, check and eval CLIs are built from
head and base with the seed's JS lane and run on the same programs.

**The fast corpus is deterministic.** The generated programs are a function of constants (`FIXED_SEED`, `GRID_TOTAL`,
`OPERATOR_TOTAL`) and of the tool's own registry: never of the head commit, the tree, the cache or the changed paths. The pinned
seed's verdicts on them are frozen in `tests/prechecks/registry/seed-verdicts.jsonl` (725 rows, keyed by sha256 and the seed
revision; `python3 scripts/prechecks/freeze.py` rewrites the file, and a unit test checks without the seed that it covers exactly
the generated programs), exactly as the registry rows carry the verdicts of the reviewers' probes. The fast tier never reads the local
seed cache and never runs the seed's CLI on a program: a program without a frozen verdict is counted, reported as an unavailable
rule (`seed-verdicts`) and judged by the slow tier, never silently dropped or judged when a cache happens to be warm. Lane builds and
outcome caches are keyed by the `src` subtree, which is all a lane exports, so a rerun, a documentation-only commit and a cold
cache give the same conditions (tested end to end; in a fresh clone: cold, warm and a documentation-only child of the classify-2
tip all give the same nine conditions). One limit, no cold-cache halving. The slow tier judges a larger sample that follows the
changed sources, with the same fixed seed, running the seed live in parallel.

`d4-invalid` (major: the seed accepts, a lane says Invalid), `unsound-accept` (blocking: the seed rejects, a lane says
Checked or yields a value), `crash`, `value-disagreement`, `premature-unsupported`, `diagnostic-shape`, `lane-build` (major: a
lane's `src/*-cli.bend` builds at base and not at head) and `incomplete-repair` (major: a violation that base already had, in
a family the manifest lists in `d4_targets`; unavailable when the manifest declares none).

**`premature-unsupported` (R5).** D4 says a form Knot cannot check is `Unsupported`, never `Invalid`, and a recognizer may stop at
a valid prefix and leave the rest unvalidated (`src/SPEC.md`: "Recognition stops at that prefix"). R5 therefore flags a
seed-rejected program whose Unsupported span begins *exactly at the seed's error offset*: the recognized token is the token the seed
rejects, so nothing valid was recognized (the classify reviewers' criterion: "the seed's error is at the recognized prefix token
itself"). A span that begins earlier, at a valid prefix that the seed rejects only later, is the documented policy: no condition
when the code is in the prefix-only table of the judged tree's own `src/SPEC.md` (head's for head, base's for base; counted as
the fact `prefix_policy`), a minor condition that the ratchet does not raise when the table does not list it. A span that
begins after the seed's error is not judged (the seed backtracks to the end of the last production it finished and reports there,
so its offset says nothing about a token further on), nor is a non-ASCII program (the seed counts UTF-16 units, Knot bytes).
A registry probe may also carry `expect: {lane: category}`, what a lane must still say about a program a reviewer froze as
malformed: the seed's verdict is binary, so this is the only rule that can tell Invalid from Unsupported where the offsets of the
two parsers do not separate the confirmed form from the suffix forms (`On{} => x` reads as a lambda to the seed, and its offsets
equal those of `On{} = |x`). The confirmed programs are frozen this way: a non-leading `~x` binder, `==` and `=>` after a
constructor, and `Name<` read as less-than. This is regression protection built from findings, not held-out recall.

**Ratchet.** Only a violation that head adds is a condition, and a verdict that was acceptable at base is raised one severity step
(how a diagnostic code is spelled, R6, does not make a base verdict unacceptable). A violation present at both is a known gap
of the D4 ledger, reported as a fact (`d4_gaps`, and `known_by_rule` for every rule). Programs the seed itself cannot judge
(timeout, crash) are never flagged.

Motivated by: classify's eight verified majors and the follow-up increment they forced; classify-2's regressions from its own
fix; the detached constructor brace, found by nest, again by generics and again by modules; the empty datatype, found three
times; dotted binders; gapped Nat `+`. Replays (`--head <rev>`, with the reviewers' main-side bases):

| Head (base) | Result |
|---|---|
| classify `5e5b2201` (`185b7d5f`) | exit 3, six executor majors: a non-leading `~b:` binder (`a: Flag, ~b: List<Flag>`, seed error and Unsupported span both at the `~`), `Cell{v} ==`, and the frozen `~`, `==` and `=>` probes. The 58 suffix forms the previous rule reported (`= \|x`, `= 0`, `~~b:` after a leading binder) are the documented policy and are not conditions |
| classify-2 `7b85b8aa` (`fa31fec0`) | exit 3, nine executor majors, all `Name<` read as a type application where the seed reads less-than (`Flag<Flag`, `Flag < x`, `Flag<-A: Type>` in return types and annotations, and the frozen r1, r2 and r2b probes). `Flag<>`, `Flag<x>=` and `Flag<Flag>>` stay Unsupported after the prefix and are not reported |
| nest `eb15da85` (`3c25d9be`) | exit 3, 5 blocking: a dotted binder accepted at the parse and check lanes (two), an empty-typed binder turned Invalid (two: the `empty-multi` probe and one gap variant), a moved type accepted |
| classify `5e5b2201`, with a hand-written manifest declaring every grid family in `d4_targets` | 146 `incomplete-repair` majors beside the six above, for example `@x: Flag -> Flag` as a return type and a moved type declaration |

Main against itself yields no condition; the seed-accepted forms that Knot calls Invalid on main are reported as facts
(`d4_gaps`), not conditions.

**Family V (VM plans).** When a tree carries `vm/serializer.py` and `vm/registry.json`, C1 also exercises that tree's own
reference codec in a child process with a memory limit (`lib/codecprobe.py`), at head and at base, on every
`vm/golden/*.plan.json` and on the 13 harvested reviewer plans (`tests/prechecks/registry/vm.jsonl`).
`reference-crash` (major) is an exception the codec does not declare: its declared refusals are `Malformed`, `Exhausted`
and `ValueError`, and an `AttributeError`, `IndexError`, `MemoryError` or `RecursionError` is a defect of the oracle that
every VM lane is judged against. `roundtrip` (major) is `decode(encode(golden)) != golden`, or a decode that refuses the
encoder's own output. Roundtrip is strict for goldens only, since a reviewer's probe plan may be malformed on purpose. A verdict
that base already had is a known gap; a golden that the branch added or edited is judged as new.
Replay: vm-spec `d2fe0f20` against its merge base with main `454bf305` gives exit 3 with five `reference-crash` majors, all
`AttributeError: 'NoneType' object has no attribute 'to_bytes'` raised by the encoder on harvested reviewer plans
(`isempty-unchecked`, `chr-unchecked`, `append-tail-unchecked` and two more). The unit controls are the synthetic clean and
broken codecs of `FamilyVTests`.

**Unavailable is never converted to not-applicable.** A missing pinned seed or bun, or head lanes that do not build, leave family L
`unavailable`, named beside whatever family V finds, and a lane that builds at base and not at head is also a `lane-build` major for the
executor (its message is the build error; a `|` in it no longer splits a report row).

### C2 merge-forecast

Trial merges (`git merge-tree`, no checkout touched) with main and each sibling in `merge_before`. Conflicts in the
generated-file registry (`inventory/*.json`, `run.py`, `test_runner.py`, `GATES.md`, the review log, `package.json`,
shared receipts) become known merge conditions with their mechanical resolution; any other conflict is `conflict` (major,
coordinator). Also: `base-fix-missing` (a main commit to the runner, host or owned paths that the branch lacks; a merge commit on main counts by the
paths it resolved itself, those that differ from every parent), `decision-drift`
(a decision row changed on main; its superseded literals found in the branch's normative docs), `upstream-contract-unconsumed`
(a control that the upstream's green tip newly exports and no consumer references; the green tip is the newest first-parent
commit whose committed receipt says passed with input hashes that still match), `brittle-upstream-coupling`, `oracle-behind`,
and `census-after-merge` (census `--check` on the trial merge, with inventory conflicts resolved to main's copy first).

Motivated by: vm-core `a5e2ffa8` exporting-but-never-running vm-spec's `run_controls` (replayed: found), the clang fix `90b4052`
missing from io-abi-2, 16 re-filed merge minors, the inventory conflict re-derived in 15 vm-spec rounds.

### C3 frozen-and-owned

`out-of-scope-edit` (needs a declared `owns`), `shared-file-shape` (run.py: only added Gate rows, and in `counts()` only an added
`if gate.name == '<g>':` branch for a gate row this diff adds, as GATES.md tells every new gate to make; nothing else in the file,
no existing statement of `counts()` and no existing gate's branch may change, compared by AST; test_runner.py: only added names;
GATES.md and the review log: only added paragraphs; package.json: scripts may be added, none may change and no other key may;
approved.json and the manifest: additions), `frozen-edit`
(blocking for other gates' assertions and expectations; authorization is read from main), `assertion-weakened` (a removed
`require`/`assert`/`raise`, `x[k]` to `x.get(k)`, `==` to `in`/`>=`, a widened bound, a shrunken MUTANTS or controls list),
`coverage-dropped` (a receipt's mutants, fixtures or accepted counts shrank, with the removed names), `frozen-row-changed`
(a base row of a frozen data file changed; an `amend:` line makes it known), `freeze-order` and `provenance-mismatch`, history
lints (`commit-trailer` naming the executor family, `red-commit-wording`, `census-approval-summary`, `mixed-gate-commit`),
`normalized-comparison`, `generator-not-reproducible` (declared generators only) and `red-tip` (`census --check` fails; the slow
tier adds `census:test`, which takes about 25 s on this host and is not a registered gate).

The diffs of io-abi-2 `de221744`, joint `691b23b7` and bootstrap `dc76dac3`, which the earlier line-based `shared-file-shape` reported as
major on three accepted tips and three landing merges, are the clean controls of the counts() rule; editing or removing an existing
gate's branch, a branch for a gate the diff does not add, a loose statement and an `else` arm are its broken controls. A new gate's
branch that loads and runs the gate's own module (generics `f39ba7e8`: `module.coverage(record)` through importlib, which four reviewers
filed as minor) is a minor condition for the coordinator (`counts-runs-gate-code`), not a blocking one: it is the registration
GATES.md asks for, and the runner extension is the coordinator's to accept.

Motivated by: generics deleting three classification mutants and shrinking coverage; nest's Wasm rejection pairs 64 to 62 and
fuzz count 426 to 242; a control comparator loosened from `observed[k]` to `observed.get(k)`; modules' `census:test` red at 78
of 79; expectations committed in the same commit as the implementation.

### C4 receipt-integrity

Scope is receipts changed between base and head, never the whole tree (52 tracked receipt and evidence files on main already
contain `/Users/` paths). `host-path` (major), `stale-receipt-hash` (a recorded current-input hash differs from the recomputed one,
ratcheted: a hash already stale at base is not re-reported; a hash map under a section named for the past, such as
`baseline_implementation`, a freeze, a snapshot, an audit or a candidate, is history, never a condition and counted as the fact
`historical_hash_claims`, because no gate re-verifies it and regenerating it would break the freeze; major for a registered gate output or a receipt the
manifest lists, minor for any other receipt, which nothing regenerates: none of the 26 receipts on main whose hash maps
differ from main's files is a registered output), `decorative-hash`, `unowned-receipt-drift-predicted` (info, coordinator: a
receipt whose recorded input this branch changed), `corpus-glob-coupling` (added `.bend` files enter the bootstrap corpus),
volatility (measurements, README inputs, orphans, duplicates, more than three preflight receipts), `receipt-date-only`
(a receipt commit that changes nothing after normalization), and, from the implementer's own gate run (the newest
`.local/gates/run-*/summary.json` whose snapshot equals this tree): `gate-red`, `own-receipt-stale`, `unowned-receipt-drift`. If no
run matches, that rule is `unavailable`; the slow tier runs the gates itself. `host-path` on a receipt that the coordinator accepted
is not a defect of the rule: the accepted tips' own receipts carry worktree paths that the merge refreshes
(`npm run gates:refresh`); on main the base ratchet suppresses a path count the base already has, and the replay-only ledger below
lets the historical tips be replayed as clean controls.

Motivated by: opt-1's 12,276 host paths; perch-context sending a home path to the judge; generics' 12 stale hashes; gpu-2's
README in a receipt's source hash; the six unowned-drift and six sign-off majors that were merge conditions, not executor rework.

### C5 preflight-delta

`node scripts/perch-style.mjs --preflight --json` is offline (zero provider requests) and never loads a dotenv file. It runs
on exports of head and base (the base on the targets as they existed there; results cached by tree). `preflight-new-blocker` (a
unit newly truncated), `composition-budget` (a manifest group that lost its composition or fell under 2% headroom; and a changed
file that is in **no** group and composes over the 48,000-byte cap alone: major when the file itself is over the cap, minor
when its helper closure is what is large, with the closure named. A file that a group lists is judged by its group, never alone:
measured alone, a new law file of an existing group composed 52,838 bytes while its group composes 22,008),
`unit-cap` (the full manifest run aborts at 5,000 units), `manifest-membership`, `task-provenance`, `bend-hygiene` (a non-ASCII
byte or a divider comment in an added `.bend` line) and `perch-identity-change` (a parser profile or rubric change with no
review-log entry, or a judge-facing sentence that disappeared). A changed target that does not parse under the Perch parser aborts a
batch preflight; it is dropped, the rest are preflighted again and the dropped ones are named as the unavailable rule
`preflight-targets`. When the full-manifest run does not complete (`unit-cap`, an abort, or no manifest), the two rules that read it, the group
`composition-budget` and `manifest-membership`, are named as not run. Absolute blocker counts are never findings: 25 to 137 exist at every base.

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
is matched by a machine-readable `boundary: {limit, value}` field, else a numeric literal, and that is labelled heuristic; with no
declaration there is nothing to compare, so each is an unavailable rule, not a rule that ran), `unscaled-timeout` (a fixed timeout in a
changed gate script), `gate-wiring` (a new check script or gate row that the runner registry and its self-test do not know) and
`gate-headroom` (a gate over half the runner timeout in the matching run). Adapters (`scripts/prechecks/adequacy/<gate>.py`, run only
for a gate the branch touched) are the hook for the verifier-soundness rules; no adapter ships in this build, which is reported as the
unavailable rule `adequacy-adapters` rather than as a pass.

Motivated by: fixed timeouts at four of six tips, judge-forgery findings that drove three of five fix rounds in harness-2 and
joint, the witness matrix with no False golden, key 0xFFFFFFFF and Char tags-mode cells unwitnessed.

### C8 perch-coherence (advisory)

Seven `each: file`, `gate: false` rules in `.perch/rules/prechecks.yaml`, one packet directory each:
`claim-holds-against-evidence`, `passages-agree`, `outcome-follows-d4`, `clause-vs-delta`, `expectation-independent`,
`kill-is-semantic`, `required-laws-met`. The deterministic builder writes self-contained Markdown packets (Claim, Evidence, Scope)
from git objects only, so rebuilding is byte-identical and a packet built anywhere can be checked from the main checkout:

```sh
npm run -s prechecks:packets -- --repo <path> --out <dir> [--head <rev>] [--base <ref>] [--inc <id>] [--rules a,b] [--limit 40]
# writes <dir>/<increment>/<head8>/<rule>/<n>.md
```

Claims are selected by mechanical triggers (absolute words, invariance verbs, identifiers, numeric budgets) and ranked by how
much of the claim the diff speaks about; evidence is ranked the same way, at hunk level for modified files and declaration
level for added ones, capped at 12 KB with a truncation marker and 48 KB per packet. A packet whose evidence does not resolve
is reported `unavailable`, never written. The check builds them into `.local/prechecks/packets/` and raises no condition: a packet
is a question, not a finding. A build from a *dirty working copy* (the default) is labelled `<HEAD>+worktree.<tree>` in the
header, the sources and the directory name, since its text is not HEAD's; a build with `--head <rev>` (and a clean checkout) carries
the plain commit and is byte-identical on every rebuild.

**Live use belongs to the coordinator, from the main checkout** (the credentials live only there; never copy or read an `.env`):

```sh
node scripts/prechecks-perch-run.mjs --controls                 # dry run (the default): what would be asked, zero requests
node scripts/prechecks-perch-run.mjs --controls --live          # calibration: one request per packet
node scripts/prechecks-perch-run.mjs --packets <dir>            # dry run: which packets of a built increment would be asked
node scripts/prechecks-perch-run.mjs --live --packets <dir>     # ask about a built increment
```

The runner uses the retained-receipt wrapper (`.perch/usage/`), refuses a linked worktree, and stops on the first
authentication or quota failure. It has never been run live in this build. What it asks:

- The cap is **per rule and per (increment, head)**, as each packet's own header names them (never by directory depth), and it is
  the number the builder stops at: `scripts/prechecks/packets/limits.json` (`packets_per_rule_per_head`, 40) is read by the
  builder's `--limit` and the runner's `--cap`. A run that builds and asks with the defaults asks every packet; anything skipped is
  printed by rule. Measured with dry runs (zero requests): vm-spec `d2fe0f20` builds 130 packets in six rules, of which the previous runner
  planned 40, all `claim-holds-against-evidence`, and this one plans all 130 (40, 33, 14, 40, 2 and 1 by rule); over the replay's 7,949
  packets for 71 heads (previously 65% dropped, and only `claim-holds-against-evidence` asked on 63 heads) it plans all 7,949.
- The rules read only `.local/prechecks/packets/**/<rule>/*.md` of the checking checkout. A packet directory built anywhere else
  (`--out <dir>`, a worktree's) is copied into `.local/prechecks/packets/staged/` before it is asked (the dry run says how many, and
  copies nothing), and a packet that no rule can read is refused up front.
- Staged calibration controls and staged copies are asked only by the run that staged them; a production plan skips them, and a live
  calibration removes the controls when it ends.

Calibration follows `docs/perch-maintenance.md`:
run the [controls](../tests/prechecks/perch-controls/README.md), require every broken packet at or above the floor and every clean one
below it, freeze the rule text, then run the held-out packets; keep `gate: false` until adjudicated production findings
exist; a rule that does not separate is rewritten or narrowed, never floor-raised. The offline wiring test
(`scripts/check-prechecks-rule-wiring.mjs`, stubbed provider) proves selection and plumbing only, including the cap, the staging and the
controls' cleanup. The built-in `docs`
category selects nothing on a packet, so it is not a baseline.

## How it is verified

`npm run -s prechecks:verify` (gate `prechecks`) runs offline, with no provider, network or credentials:

1. every unit test in `scripts/prechecks/tests/`, each rule against a synthetic clean and a synthetic broken repository (every
   test builds its own git repository, never the real one), including end-to-end tests of C1 against the real lanes;
2. a fixed set of semantic mutants of the checks, each of which must be killed by the unit test that pins its rule (the gate
   does not re-run a pinning test unmutated: the whole suite has just run it);
3. the Perch rule wiring test.

The receipt's inputs include the calibration packets (`tests/prechecks/perch-controls/**/*.md`), which the wiring test reads and a
live calibration sends.

**Cost.** The gate is the slowest of the ones this increment adds: 223 tests and 32 mutants take 149 s standalone at load average about 35
(129.6 s for the 208 tests before the accounting tests, at about 40). Inside three full gates runs it took 138.6 s, 308.2 s and 393.3 s
as the host's load rose (27 to 45, from other sessions), and the wall time of those runs (251.7 s, 583.6 s, 638.9 s) followed the load, not
the gate. It cannot skip itself when its receipt inputs are unchanged: its end-to-end tests build the tree's own lanes from `src/` and run
the pinned seed, so `src/` would have to be an input and would change in almost every increment. Registering it first in the GATES table,
so that it overlaps the other long gates, was tried and reverted: the wall time over the mean slot load (the gate seconds over four
workers) was 1.22 in the run before the move (583.6 s) and 1.22 in the run after it (638.9 s), so the packing did not change, and
GATES.md has each increment append its gate.

`npm run -s prechecks:test` runs only the unit tests. **Historical controls** belong to a replay command, not to the registered tests,
because the gate's export has no history:

```sh
npm run -s prechecks:replay -- [--only classify,recursion]     # needs a checkout with the campaign branches' commits
```

`tests/prechecks/replay/contexts.json` is the table: each accepted tip is a **clean control**, each tip that carried a defect the
reviewers confirmed (or that main's own history repaired: io-host's stale census pin) is a **broken control**, and each context records the
executor conditions of major or higher that the suite must report with the default policy and with a replay-only ledger
(`tests/prechecks/replay/proposed-ledger.json`). A stacked increment names its `upstream` (passed as `--upstream`), and a context may carry a
manifest reconstructed from the diff, because the campaign wrote none then. Measured
on this tree (`python3 scripts/prechecks/replay.py`, all sixteen contexts ok):

| Context | Kind | Exit | With the ledger | What remains |
|---|---|---|---|---|
| bootstrap `dc76dac3` | clean | 0 | 0 | none: its `counts()` branch is the registration GATES.md asks for |
| io-abi-2 `de221744` | clean | 0 | 0 | none |
| poly `6ffb8884`, sugar `577d2b05` | clean | 0 | 0 | none |
| perch-context `ffab8be2` | clean | 0 | 0 | none |
| harness-2 `f53f937c` (manifest owns `tests/compiler-bootstrap/**`) | clean | 0 | 0 | none: without the manifest its own gate script is a C3 `frozen-edit` and an `assertion-weakened` (a selector widened from `==` to `in`) |
| vm-model `07e6db73` (upstream vm-spec `cea554ab`) | clean | 0 | 0 | none: without the declared upstream the run reports vm-spec's files as its own |
| main commit `25b3a5b6`, main `a6367eb9` against itself | clean | 0 | 0 | none |
| fields-wasm `3868b119` | clean | 3 | 0 | 2 `host-path`: its own receipts, as the gate run in the worktree wrote them (ledgered) |
| census-2 `0e8b2876` | clean | 3 | 0 | 1 `host-path`: the round receipt cites an ignored run summary (ledgered) |
| recursion `624228e5` | clean | 3 | 0 | 3 `host-path`: own receipts with worktree paths (ledgered); the `baseline_implementation` freeze is history, and the law file outside every manifest group is minor |
| classify `5e5b2201` | broken | 3 | 3 | six confirmed at-token regressions, and a C3 `frozen-edit`: the additive 112-line edit of the frontend gate script, which no manifest authorizes (it is not ledgered) |
| classify-2 `7b85b8aa` | broken | 3 | 3 | nine confirmed less-than readings; two `host-path` receipts are ledgered |
| joint `691b23b7` | broken | 3 | 3 | a real red gate: `census --check` fails on a plain export of the tip |
| io-host `963a7594` | broken | 3 | 3 | `red-tip`: the census inventory pins an older hash of `tests/compiler-io/host-check.py` than the file has (main repaired it in `f84d83ef`) |

The ledger file is **replay-only**: the suite never reads it by itself, `replay.py` passes it as `--ledger`, and it is not for adoption. It holds
eight C4 `host-path` entries, each pinned to the measured hit count, because the historical tips' base did not yet contain the receipts that the
merge accepted and refreshed; on main the base ratchet already suppresses a path count that the base has, so adopting an entry there would only
silence the same path later. It never holds a `frozen-edit`, an `assertion-weakened` or a `C1` entry: the fingerprint of the first two is the
path, so an entry would acknowledge every later edit of that gate script, and the third is a defect the reviewers confirmed (unit tests).
The ledger of record is `docs/compiler-campaign/known-conditions.json` on main, which the coordinator owns.

**Replayed, not controls.** Six more landed revisions were replayed with the same command and are left out of the table, each for a stated
reason. Four end with exit 3: the harness-2 landing `f8f50370` (the C3 pair above, without the manifest), the classify-2 landing `152fcd5d`
(the confirmed less-than defect, landed), the io-host landing `0b9498bb` (the stale inventory above, until `f84d83ef`) and the io-abi-2 landing
`2e93d582` (a receipt that records the previous hash of `scripts/run-wasm-io.mjs`). Two end with exit 0 only because `red-tip` did not run: the
perch-context landing `7c743980` and the joint landing `ef3081f6` fail `census --check` on a plain export (a stale inventory, which the
coordinator regenerates after a merge), but the diff of neither touches `src/`, `tools/census/` or the inventory, the rule's trigger. A trigger
that also fires on a changed gate program would run the census on 7 of the 76 distinct revisions replayed and report four landing merges and no
tip, so it is left as it is and the registered `census` gate covers the rest.

**Recall against the first delivery.** The fix round changed what C3, C4 and C5 report, so the change was measured. The 60 replay
contexts on which the first delivery (`e0ecc0c7`) reported an executor condition of major or higher in those checks were run again with
this tree's tool (at `3445f778`; the later commits add a minor coordinator note and name rules that did not run, and change no major
condition). Of those 817 conditions (154 C4 `host-path`, 140 C3 `frozen-edit`, 39 C3 `shared-file-shape`, 30 C3
`frozen-row-changed`, 94 C5 `composition-budget`, 353 C4 `stale-receipt-hash`, five `assertion-weakened`, two `unit-cap`), 365 are still major
or blocking, 78 are gone and 374 are minor, each for one stated reason. Gone: 37 `shared-file-shape` conditions were a new gate's `counts()`
branch, which GATES.md asks for; 3 `stale-receipt-hash` conditions were `baseline_implementation` freeze hashes, which are history; 38
file-level `composition-budget` conditions were on files that a manifest group lists, which the group check now judges (23 sit in groups that
all fit the cap, 9 reappear once as their group's own major condition, and 6 sit in two contexts where the full-manifest run aborts at the
unit cap, so the `unit-cap` major stays and the group rules are named as not run). Minor: 328 `stale-receipt-hash` conditions are on
receipts that are neither a registered gate output nor a manifest receipt (for example historic preflight, handoff and closed receipts), and
46 `composition-budget` conditions are on files in no group that exceed the cap only through their helper closure (all 46 name it; the files' own
bytes range from 123 to 33,676, all under the cap). No `host-path`, `frozen-edit`, `frozen-row-changed`, `assertion-weakened` or `unit-cap`
condition was lost or lowered, and the defects the reviewers labelled in C4 and C5 (generics `78c4942e`'s `generics.json`, vm-model
`e38afc32`'s `vm/model.bend`) are still major.

## Pipeline integration (for the coordinator)

These edits live in the campaign harness, outside the repository:

- **Implementer, before returning `complete`:** run `npm run -s prechecks -- --inc <id>`; fix every new or changed *executor*
  condition of major or higher severity (exit 3), or dispute each with evidence in `.local/<id>/HANDOFF.md`. Coordinator and
  upstream conditions are mentioned, never worked. Repeat after each fix session: the grid lists a regression in minutes, and the
  same conditions on the same tree (a rerun, a documentation-only commit and a cold cache change nothing). A `partial` check
  is not a pass: read what did not run, and pass `--strict` where "everything ran" is the requirement.
- **Before review:** run it once more; pass `facts.json` (with its `coverage` table), `report.md` and `known.txt` to the review
  workflow as `known: [...known, ...prechecks.known]`, and tell the lenses that an unchanged fingerprint is not a finding and that a
  rule listed under "did not run" is theirs to cover.
- **The gates lens** drops "compare with last.txt" and "run preflight and report blockers" only for a check whose `coverage` says its
  rule ran (C4's `gate-run` needs the implementer's own gate run; C5's `preflight-new-blocker` may be unavailable), and spot-checks one
  fact from `facts.json`. **The preamble** takes the executor trailer and the gate count from the tree, not from prose.
- **Ledger and manifests:** seed `known-conditions.json` (the Digest blocker, the six closure-golden rows in the bootstrap corpus,
  the dotted-binder and empty-datatype rulings; not `tests/prechecks/replay/proposed-ledger.json`, which is replay-only) and write a manifest
  at each launch; until a manifest declares `owns`, `d4_targets`, `limits` and `coverage`, the rules that need them are reported unavailable.

## Limits and what is not built

- **Family V is partly built**: R11 `reference-crash` and R12 `roundtrip` of the tree's own codec exist (above). R9 and R10
  (the reference evaluator against `run-wasm-io`, the model binary and the laundering matrix) need the VM binary and a
  machine-readable divergence table, and C1 reports them unavailable (`vm-lanes`) when `vm/evaluate.py` exists. The
  harvested plans in `tests/prechecks/registry/vm.jsonl` are their corpus. R8 (helper lanes) needs declared helpers. The tree
  on main has no `vm/`, so on main the family is not applicable.
- **C2 R9** (forward-merge replay of upstream goldens through the downstream lanes), **C7 R3-R5** adapters and the C1 model lane
  are slow-tier work that needs those lanes.
- **The fast corpus is frozen, so it is fixed**: the pinned seed judges a fixed sample of programs whose verdicts are committed
  (`seed-verdicts.jsonl`). A change to a generator, the registry or the seed pin needs `scripts/prechecks/freeze.py` (a unit test says
  so), and programs beyond the frozen sample (the slow tier's, a tree's own fixtures' variants) are judged live in the slow tier.
  Programs with imports are judged only when the `Base` library resolved at freeze time, and registry programs that need sibling files
  have no seed verdict: import lanes (modules, hash imports) are not built.
- **R5 and offsets.** Two parsers' error offsets are comparable only when both point at the offending token. The seed backtracks
  (`'def', 'type' or 'law'` at the end of the last production it finished) and reads `=>` after a constructor as a lambda, so a
  misclassification by *form* rather than by position (`On{} => x`) is found only by the frozen `expect` probes, not by the grid.
- **`partial` is the common state** until manifests, gate runs and adapters exist: nearly every run has a rule that could not run, and
  the report says which. It changes no exit code without `--strict`.
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
