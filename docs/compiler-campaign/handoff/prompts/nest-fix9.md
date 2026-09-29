You are one executor in the Knot compiler campaign, working in a dedicated git worktree on branch `campaign/nest`, based on the campaign integration line (main plus the reviewed first wave). Another agent (the coordinator) reviews and merges; you own only this increment.

Read first, and follow: `AGENTS.md` (including the inducer instruction; keep any reflection private and never write it out), `README.md`, **`docs/COMPILER-CAMPAIGN.md`** (goal, definition of done, decisions D1–D26, protocol), `src/AGENTS.md`, `src/SPEC.md`, `src/CONTRACT.json` and the relevant parts of `docs/BEND-SUBSET-STAGES.md`.

Environment:
- Pinned seed: `bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts` (`.toolchain` is a symlink to the main checkout's ignored copy). Always export `BEND_NO_TELEMETRY=1`.
- Bun 1.3.14, Node 22.22.3, Python 3, wasm2wat 1.0.41.
- Build output goes to ignored `.local/` or `build/`.
- Never read or copy any `.env`. No network except what `npm ci` already did.

The existing deterministic gates must stay green, and their assertions must not change. Run them all with the gate runner (`docs/compiler-campaign/GATES.md`). It exports your working tree to scratch, runs every registered gate (14 today, including `recursion`, `fields-wasm` and `census`) and classifies receipt drift:
```
BEND_NO_TELEMETRY=1 npm run -s gates        # must exit 0; read the per-gate lines on stderr
npm run -s gates:verify
```
Run individual gates directly (`python3 tests/<gate>/check.py`) while iterating. Register your new gate by appending it to `GATES` in `scripts/gates/run.py`, so the next increment runs it too; the runner's self-test checks names, so no count needs editing. Add a `docs/compiler-campaign/manifest.json` group for any new `src/*.bend` file; `tests/perch-style-manifest.test.mjs` fails otherwise. The `census` gate (`tools/census/census.mjs --check`) fails on a new source file, import or feature class until you run `npm run census:approve`; paste its printed summary into your commit message so the reviewer sees what was approved.
- **Receipts.** Direct gate runs rewrite tracked receipts. Commit receipts for your own new gate. Leave shared receipts of existing gates to the coordinator, who refreshes them after merging: restore them with `git checkout -- <path>` before committing.
- **Expectations (D7).** Every new capability gets its expected results fixed first, from the pinned seed (the reference interpreter) or from literal review. Only then implement. Every new behavior needs an independent differential check: seed ⇔ Knot evaluator ⇔ Knot Wasm, where applicable.
- **Mutants.** Add type-correct semantic mutants that the new gate kills.

Knot's discipline (D4):
- A form Knot cannot handle is reported `Unsupported`, never `Invalid`, and is never passed through unchecked.
- Record `Invalid`, `Unsupported`, `Exhausted` and host/internal failures separately.
- Proofs: every law you add must be filled and pass the complete proof entry points. Run the relevant `bun .toolchain/.../main.ts src/*-PROOF.bend`, which must print `All terms check.`

Style (D9, rubric v8), for all new Bend code:
- One core idea that absorbs the cases.
- Laws as `law` declarations with checked proofs, not unchecked law comments.
- Terse, exact names.
- No costume vocabulary, narration or ornament. Comments state conventions, invariants or surprising decisions only.
- Run `node scripts/perch-style.mjs --preflight <changed .bend files>` (offline) and report its blockers. Live Perch review is done by the coordinator.

Git:
- Commit coherent increments on your branch with explicit paths; never `git add -A`.
- End each commit message with a blank line and `Co-Authored-By: GPT-6 Astra <noreply@openai.com>`.
- Do not push, merge or rebase onto other branches. Do not touch other worktrees.
- If `git commit` fails because Git metadata is read-only in your sandbox, do not work around it. Leave the tree as is, write `git bundle` plus the commit message under `.local/nest/`, and say so in your report.

Finish with a concise report:
- what changed;
- commits;
- every gate with its exact pass counts;
- the new fixtures and mutants;
- preflight results;
- known limits, and what the next increment needs.

----
YOUR INCREMENT:
ID: nest. REVIEW FIX ROUND 12, targeted. Campaign milestone 3 (pattern matrix). The branch is `campaign/nest` (8b5d2154). nest is the critical path: every other merge waits on it, and it merges to main next.

Merge `main` (b29b259d or later) first. main now records D25 and D26 in `docs/COMPILER-CAMPAIGN.md`; read D26.

Your round-11 review confirmed four majors: three are D4 (seed-accepted programs that the merge base answered Unsupported now answer Invalid), and one is an unbounded lowering blowup. Full evidence, the reviewer's probe programs and paths, and the verifiers' independent reproductions are in `docs/compiler-campaign/handoff/findings/nest-r12.md`. Read it completely. The minor findings there are yours to fix too if they are cheap; say which you took.

**The coordinator's code ruling (binding, and shared with campaign/literals-integ).** The two branches answer the same unmodeled shapes with different codes: nest's 3281c22e pins `argspace-operator-call` as `Unsupported parse term-form`, while literals-integ pins it `Unsupported parse operator`. literals-integ will re-merge your tip, so settle one vocabulary now:
- An operator token that continues a term (`+`, `-`, `++`, `->` after a value, spaced or on the next line; a glued `x+y`; a spaced `a + b` inside an argument list) is **`Unsupported parse operator`**. The seed parses these as operator sugar, which Knot does not model. In a live row the seed rejects them for a typing reason (an operator needs its annotation), and that is not a syntax claim Knot can make.
- Any other unmodeled term form, such as a touching `+name` promotion in an expression argument list or a `?` hole, is **`Unsupported parse term-form`**.
- `Invalid` stays only where the seed rejects for the syntactic reason the diagnostic names. Examples: the frozen round-10 `marker-gap` shape, where an operand is followed by a name and `=` or `:`; `@`, backslash and closers in an argument list; pattern fields, which the seed always validates.

**Fix, in new commits, freezing from the seed first (D7):**
1. **[major, D4]** A spaced `+`, `-`, `++` or `->` at the start of the line after a let's value, in a discarded row of `match x y:`, answers `Invalid parse detached-marker`.
   - Restate `src/LAWS.bend::detached_marker` so Invalid applies only to the marker-gap shape, with its proof filled. Add the Unsupported outcome as its own law. D21 applies: the law is restated to be true, never dropped.
   - In `parse.bend` BodyAt, answer `Unsupported parse operator` for the other cases, reusing round 12's `continues` rule.
   - Add a mutant that restores Invalid, and draw the form in fuzz12.py's suffix family.
   - Drop the "main-era" label for the two-scrutinee shape in SPEC, CONTRACT, state.json and REVIEW-12.
2. **[major, D4]** A touching `+name`, a glued `x+y` or a `?` hole as the next call argument, in a discarded row, answers `Invalid parse argument-separator`. In expression argument lists only:
   - a touching `+name` and a `?` hole answer `Unsupported parse term-form`;
   - a glued `x+y` answers `Unsupported parse operator`.

   Keep `argument-separator` for pattern fields, `@`, backslash and closers. Add a mutant per class that restores Invalid, draw the forms in fuzz12.py, and correct the SPEC and REVIEW wording (`@` and backslash are seed-rejected).

3. **[major, D4]** An arm body or a later statement that starts with `(`, a numeral, `[` or `?x` on its own line at another column answers `Invalid parse body-indentation`. The seed's `parse_body` takes any term as a body.
   - In StartBody, and in BodyAt's other-column branch, answer `Unsupported parse body-indentation` for every token that can start a seed term. That is `(`, `[`, numerals and `?`, besides the name, `match`, `+` and `-` it already takes; widen `S.statement` or add `S.term_start`.
   - Keep `)`, `,`, `:`, `=`, `case`, `def`, `type`, `!`, `@` and backslash Invalid, as precision controls.
   - Freeze the reviewer's 720-cell class grid from the seed first (`isem13/.local/p/ind4.py`), and add mutants that read `(` and `[` as Invalid again.
   - Correct src/SPEC.md:198 and the REVIEW-11/12 wording.
4. **[major, resource]** A terminal default is copied into every remaining constructor arm, so the checked core and the emitted module grow as ctors^columns, and the 4,096-visit quota never sees the copies. Measured: dd5x5 is 373 bytes of source and emits 34 KB, and crashes the Bun lane unclassified; dd9x5 takes 45 s and 900 MB; dd10x5 never finishes.

   **Coordinator ruling: bound it now; do not change the core representation in this round.** Core `Case` has no default arm, and adding one touches the evaluator, both Wasm emitters, the image encoder and the VM track. That is queued as its own increment.
   - Charge every copied default node to a core-size budget. When the budget is exceeded, answer `Exhausted check budget` before any blowup, so no program can grow the core or the module super-linearly unbounded.
   - Classify the seed's Bun-lane `memory fault (machine stack overflow?)` as Exhausted (host) in the nest gates' Bun lane.
   - Add controls for dd5x5, dd9x5 and dd10x5: each is either accepted within the budget or Exhausted, never a hang or a crash.
   - Correct the "shared" wording in tests/compiler-nest/SPEC.md:49.
   - Measure and report how many files in the bootstrap corpus, and which `src/*.bend` files, hit the new budget. Knot must still check its own sources, so if any of them is Exhausted, report it prominently and choose the smallest budget that admits them all.

**Frozen pins to amend.** This is the existing seed-derived amendment path, as 3281c22e used for its sibling. Each amendment goes in its own commit before the repair, and its message cites the seed observation and this ruling:
- `argspace-promoted-call` (round 10): `Invalid parse argument-separator` becomes `Unsupported parse term-form`. Its seed reason is non-syntactic (`expected : a bound variable`), and the seed accepts the same body in a discarded row.
- `argspace-operator-call` (round 10): `Unsupported parse term-form` (3281c22e) becomes `Unsupported parse operator`, under the code ruling above.
- Any other frozen pin that the code ruling moves. List every one in your report, with its seed observation.

Seed observations never move. round10_seed.py's REASON table gains the `argument-control` reason, so the reason is checked.

**Convergence.** Rerun the round-11 generator and fuzz12 with the new forms drawn. Require 0 false acceptances and 0 false Invalid, and record the class coverage. Before you finish, run the reviewer's zoo (`nest-scope-probes/zoo.py` in the scratchpad, 64 discarded-row body forms) against your final build: 0 seed-accepted programs may answer Invalid.

**Not yours; don't fix.** The dotted-binder stopgap (modules' rule replaces it). The two D21 general lowering laws (recorded open obligations). A let binder named after a declared constructor (literals-owned). The def-header and type-field line-break gap (literals-layout).

Finish with the report the preamble asks for, and update REVIEW-12 (or a REVIEW-13) with the dispositions.
