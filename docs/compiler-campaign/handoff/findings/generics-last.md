# generics: last review findings (2026-09-28)

Source: the coordinator review workflow wf_978eea6e-9a4. The status was needs-coordinator, with 4 confirmed majors: closures pin collisions, assertion rulings, a 900 s gate timeout (the runner now allows 1,800 s), and the generic path accepting a spaced `->` or `{` that the seed rejects. Also the forward-declared pattern residual.

## [major] (scope) New Unsupported pins collide with the closures increment, which the coordinator merges first: the function-parameter witness with both of its parameter-type mutants, and the monomorphic def-reference pins

**Evidence.** The coordinator's merge order (campaign-infra/COORD-NOTES.md) is "nest → modules → descent-2 → closures → literals → generics". campaign/closures (a1d6891) is not on main: `git log main --oneline | grep -i closure` shows only the frozen-suite commits.

I exported campaign/closures to scratch (review/generics/scope/closures) and built its checker with `bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts src/check-cli.bend -o .local/sc/check.js`. I built the generics branch's checker the same way, as a native binary at scope/copy/.local/sc/check. Results:

(1) tests/subsets/classification/function-parameter.bend (`def keep(f: Flag -> Flag)`), added by 5eea108 to the shared frontend manifest:
- closures prints `Checked` (keep(1:1)->0=apply1(...)), exit 0;
- generics prints `Unsupported\tparse\tparameter-type\t52:53:5:17`, exit 3, which is the pin in classification-cases.json.
- Both retargeted mutants use this file as their only witness: frontend `parameter-type-invalid` in check_frontend.py and classification `parameter-application-invalid` in tests/compiler-classification/check.py.
- The code conflicts at the same site. Main's parser.bend parameter_end treats `<`, `-` and `(` as Unsupported. Closures reduces that to `<` only and parses `->` as a function type. Generics widens it to `T.unsupported_suffix`, which includes `-`.

(2) The def-references corpus (c52929b), which pins Unsupported check def-reference:
- def-reference-monomorphic.bend: closures `Checked`; generics `Unsupported\tcheck\tdef-reference\t84:87:9:2`.
- def-reference-erased-monomorphic.bend: closures `Checked`; generics `Unsupported\tcheck\tdef-reference\t133:136:12:8`.
- `git diff fa31fec campaign/closures -- src/check.bend` rewrites the same `Expression{S.Variable{+token},...}` arm that generics wraps with `E.term_name(...)`. Closures falls back to `G.find_function` there, so it treats a bare definition as a function value.

After closures lands, the frontend and classification pins or mutant kills fail, and so do generics' two monomorphic def-reference pins and possibly the `def-reference-free` mutant. The only alternative is that the merge silently regresses closures' capability.

What the branch discloses:
- It mentions (1) only as closures' future burden. CLASSIFICATION.md:155 says "The closures increment will need to supersede this witness when it accepts function-typed parameters". That assumes the reverse merge order.
- It does not disclose (2).
- research/compiler-generics/SPEC.md still lists "function types" as Unsupported.

**Suggested fix.** This is decided at merge, before generics goes onto a main that contains closures.

(a) Generics carries the supersession, because it merges second.
- Replace the function-parameter pin with closures' accepted phases, or remove it.
- Retarget frontend `parameter-type-invalid` and classification `parameter-application-invalid` to a witness that stays Unsupported under closures' parser. That means a form still sent to `unsupported(rest,"parameter-type")`, such as a `(`, `&`, `|` or `[` suffix, with a seed-derived expectation frozen first. If no seed-valid witness exists, retire them under a recorded coordinator decision that keeps the kill count explicit.

(b) Reconcile the Variable arm of check.bend.
- Closures' function-value resolution must run before `term_name`'s def-reference fallback, or the coordinator records which rule wins.
- Supersede def-reference-monomorphic and def-reference-erased-monomorphic accordingly.
- Keep the generic-book def-reference pins until generics.bend gets the closures rule, per the dual-checker plan.

(c) Record in CLASSIFICATION.md and the generics README that generics, not closures, owns these supersessions under the current merge order.

## [major] (scope) Unauthorized changes to existing assertions and implementer-chosen pins still need coordinator rulings (disclosed; no executor action possible)

**Evidence.** I diffed every file outside tests/compiler-generics against main, using `git -C <wt> diff main...campaign/generics`. Every change to an existing assertion matches a row of tests/compiler-generics/ASSERTION-CHANGES.md. I found no unlisted change. These rows have no coordinator authorization text, and the gates pass only with them:

- Row 7 (6086dfa): tools/census/fixtures/expected.json changes `"frontend_definitions": 41` to `47`.
- Row 8 (6086dfa): tools/census/tests/evidence.test.mjs changes `assert.deepEqual(recursion.wasm.evidence, [])` to the two generics fixtures, quantity-parity and seq-parity. This promotes the recursion increment's Wasm stage from generics evidence. The receipt shows both fixtures agreed in both lanes, so the evidence is real, but the claim is a campaign decision.
- Row 9 (cac8dd2): the census accepted.json promotes recursion.wasm to observed-in-successful-fixtures.
- Row 2 mechanics (5eea108): check_frontend.py adds `stdout_prefix` matching (`Parsed\t`, `Checked\n`) and requires artifact preservation only when `expected['exit'] != 0`.
- Row 5 (4e73b6c): the generic_header law statement in src/LAWS.bend is edited again, with touching spans `S.At{13,17,1,13}` / `S.At{17,18,1,17}`, after the spacing repair made the f39ba7e restatement false.
- Row 6 (d3cee9f): two new route mutants, `return-application-untyped` and `binding-application-untyped`, plus the per-witness mechanics.

Provenance of the Knot pins:
- The 24 boundary and dispatch-boundary pins first appear in f39ba7e, together with the checker and the contract text they cite (`git log -- tests/compiler-generics/boundaries/` shows 67a92b7 and f39ba7e). The implementer chose their codes. BOUNDARY-PINS.md is the executor's own map: 7 seed-derived, 9 exact, 5 code-only and 3 loose. It is not an independent review. The seed side does reproduce: `regen.py` PASS for 15/26 and 9/9.
- d3fe024 added two pattern-order cases after the repair (2e9646f). Its message says "The native CLIs of 6086dfa already satisfy both". One of them, `later-family-binding`, is pinned `Invalid check unmatchable-binder`. That rejection comes from the scrutinee rule and happens before any pattern resolution. The case therefore does not witness pattern order at all, and the README table counts it among the five pattern-order rejections.

The executor ledgered all of this in HANDOFF.md, ASSERTION-CHANGES.md and BOUNDARY-PINS.md, and lists it as "Open for the coordinator".

**Suggested fix.** No executor action is needed or possible. The coordinator must rule before merge:

- Confirm or reject ledger rows 7–9 and the unconfirmed parts of rows 2, 5 and 6. For each rejected row, revert that assertion and re-run the full runner.
- Do the literal review of the 24 boundary pins, recording each result in BOUNDARY-PINS.md. Look especially at the 3 loose type-level-term pins and the 5 code-only pins. The alternative is to relax the code-only pins to exit-class pins, per FIXTURES.md's convention.
- Decide whether `later-family-binding` stays as a scrutinee control or is removed from the pattern-order witness count.

## [minor] (scope) Ten gate-runner summaries (17,217 lines) with absolute worktree paths are committed as receipts, including failed and superseded runs

**Evidence.** - `wc -l tests/compiler-generics/receipts/{gates.json,gates-resource-exhaustion.json,review-*/*.json}` totals 17217.
- Each file records `run.directory` = `/Users/ericfode/src/knot/.claude/worktrees/campaign-generics/.local/gates/run-*`. For example, review-4/gates.json:1377.
- They include failed or superseded runs: gates-resource-exhaustion.json, review-3/gates-run1.json, review-4/gates-run1.json and review-1/gates-proposal-jobs1.json.
- docs/compiler-campaign/GATES.md:69-70 says each summary goes to "an ignored, unique `.local/gates/run-*/summary.json`", and that "these ignored execution logs are not required inputs".
- `git grep -l '"directory": "/Users/' main` returns nothing, so main commits no runner summary.
- The increment's own regen.py forbids checkout-specific paths (`LEAKS`) in its observations.
- Review round 2 allowed the round-0 summaries to stay as historical. Rounds 1–4 each added more files: 2fa6e2c, 6e08e3d, 19a534d, d6e4d49, 542147a.

**Suggested fix.** Before merge, keep in git only what the README must cite. Record the final passing run's normalized summary SHA-256 and per-gate counts in README text, as GATES.md does. Move the other summaries to the ignored .local/. Otherwise the coordinator explicitly accepts them as historical evidence.

## [minor] (scope) D9 cohesion: type-erasure-LAWS.bend holds unrelated catalog and parser laws; `old_annotation` is named by history

**Evidence.** - src/type-erasure-LAWS.bend holds four laws that are not about erasure:
  - `empty_family` (G.header_kind), added in 88e204b;
  - `type_level_definition` (G.resolve), added in 287a624;
  - `pattern_order` (G.pattern_constructor), added in 2e9646f;
  - `spaced_quantity` (P.read_quantity in type-parse.bend), added in 4e73b6c.
- The other type-parse.bend laws, `term_argument` and `marked_binder`, live in src/LAWS.bend. A reader looking for the spacing law will not find it next to them.
- The erasure law module now imports eval, wasm and type-parse, and its PROOF imports all of them.
- src/generics.bend:188 `def old_annotation(node: Maybe<&2,S.Token>) -> S.Node` names the monomorphic S.Binding's token annotation by its age, not by its role.
- The other new-code checks passed: every law is a `law` declaration with a filled proof, and I found no unchecked law comments, narration or costume vocabulary. The comments state conventions or invariants.

**Suggested fix.** - Move the catalog laws into a generic-catalog-LAWS/PROOF pair, or into catalog-LAWS/PROOF.
- Move `spaced_quantity` into src/LAWS.bend next to `term_argument` and `marked_binder`.
- Update the generics gate's proof-entry list to match.
- Rename `old_annotation` to a role name, for example `named_annotation`.
- Do not reword any law statement.

## [minor] (scope) The shared gate runner gained a generics-only branch in counts() that execs the gate module, beyond appending to GATES

**Evidence.** The prompt said to register the gate by appending to `GATES` in scripts/gates/run.py. f39ba7e also adds this to `counts()`:

`if gate.name == 'generics': ... spec_from_file_location('generics_gate', root / 'tests/compiler-generics/check.py') ... module.coverage(record)`

The runner therefore executes the gate module's code to validate that gate's receipt. No other gate has such a branch. 542147a reports `gates:verify: 18 tests OK`, so the runner's self-test accepts it, and 67a92b7 labels the receipt normalization as unchanged.

**Suggested fix.** The coordinator either accepts this as a runner extension and records it in GATES.md, or it is replaced by a declarative count check like the other gates' `len(record[key])` counts.

## [major] (semantics) The generic path accepts books the seed rejects when `->` or a constructor's `{` contains a gap; main reported these books Unsupported

**Evidence.** Scratch root: R=/private/tmp/claude-501/-Users-ericfode-src-knot--claude-worktrees-perch-style-framework-c2cdfc/d7a4ddd4-7d29-4f63-803d-fca5b417c923/scratchpad/review/generics/sem5. Setup: tip edfad8b exported to $R/tip; merge-base main c0bd08d exported to $R/main; binaries built with `bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts src/{check,eval}-cli.bend -o $R/bin/...` and `tests/compiler-fields-wasm/compile.bend -o $R/bin/compile`; BEND_NO_TELEMETRY=1.

Three minimal repros, each a copy of box-unbox with one space inserted:
- $R/probes/w1-arrow-gap-generic.bend: `def unbox(-A: Type, b: Box<A>) - > A:`. The seed exits 1 with `- expected : '->' (a def with no return type fills a law; no law named unbox is in scope)` / `- observed : '-'`.
- $R/probes/w2-ctor-gap-generic.bend: `unbox(Flag, Box {On{}})`. The seed exits 1 with `- expected : ':'` / `- observed : '}'`.
- $R/probes/w3-pattern-gap-generic.bend: `case Box {v}:`. The seed exits 1 with the same message.

Results on the tip, identical for all three:
- `$R/bin/check` prints `Checked`, and so does `bun $R/bin/check.js`.
- `$R/bin/eval F main 1048576` prints `Evaluated\t0\t1\tOn{}`.
- `$R/bin/compile F out.wasm` prints `Built\t152`.
- `node scripts/run-wasm.mjs --profile=knot-fields-wasm-1 out.wasm main` returns `{"validated":true,...,"result":1}`.

On main c0bd08d, `$R/bin/check-main` prints `Unsupported\tparse\tgeneric-datatype\t43:44:5:8` for all three. So these seed-invalid books went from Unsupported to accepted, evaluated and compiled.

Systematic sweep: $R/gen_space.py inserts or deletes one space in every generic-bearing line of 6 corpus fixtures. $R/sweep.py compares `seed --check-only` with Knot check; output is in $R/sweep-sp.jsonl.
- 47 of 1596 variants are UNSOUND (seed rejects, Knot Checked).
- Every one of the 47 is `- >` (26), `Ctor {` in an expression, or `case Ctor {` in a pattern.
- None involves `&2`, `<&>` or a closing `>`, so round 3's spacing repair holds for its own scope.

The README contradicts this behaviour. It states: "...general lexicographic descent and gaps inside the seed's glued tokens remain Unsupported."

The same lexer behaviour predates this increment on the monomorphic path. On main, `$R/bin/check-main` returns `Checked` for semantics/probes/ws1.bend (`On {}`) and ws2.bend (`def main() - > Flag`). Generics extends that defect to every generic book.

**Suggested fix.** Choose one of two routes. Either correct the README claim and send the lexer root cause (spaces dropped between `-`/`>` and between a constructor name and `{`) to its owner, classify-2 or the lexer owner. Or block the new reach in this increment.

To block it, first freeze a seed-derived fixture of w1, w2 and w3 in its own commit (D7). Then report `Unsupported parse spacing` in these cases:
- a gap inside `->`;
- a gap between a constructor name and `{` in term position;
- the same gap in pattern position.

The rule must depend on position. The seed accepts `Off {}` and `Box {value: A}` inside type declarations ($R/probes/gl/g7.bend and g8.bend: seed accepts, Knot Checked). A blanket `Name {` rule must therefore never report Invalid. Add a mutant that glues the new gap check, witnessed by the frozen fixture.

## [minor] (semantics) Host-boundary entries with abstract or boxed types return fabricated or address-valued results

**Evidence.** There are two repros; R is as in the previous finding.

(a) New with this increment. In `src/type-erasure.bend`, `type_id` has `case _: 0`, so every abstract type becomes datatype 0 in the runtime signature. For $R/probes/hb/h1-id-abstract.bend, which declares Color first, then Flag, then `def id(-A: Type, x: A) -> A`:
- `$R/bin/check` prints `id(0:0,1:0)->0`.
- `$R/bin/eval h1-id-abstract.bend id 1048576 1` prints `Evaluated\t0\t1\tGreen{}` with exit 0. The evaluator host accepted a generic entry and made up a Color constructor.
- By contrast, `eval r1-id-boxed.bend unbox 1048576 0` correctly reports `HostFailure\tinvoke\tstructured-argument`.

(b) Pre-existing, but newly reachable through all-nullary generic families. $R/probes/mr/m4-entry-tag.bend defines `def f(x: Flag) -> Tag<Flag>` with `type Tag<-A: Type> is Type: TagA{} TagB{}`. The seed's `main` prints On{}.
- `$R/bin/eval m4 f 1048576 1` prints `Evaluated\t2\t1\tTagB{}`.
- `node scripts/run-wasm.mjs --profile=knot-fields-wasm-1 mr.wasm f 1` returns `"result":0`, which is the cell address reported as an ordinal.
- Main has the same behaviour for mono fielded results. In $R/probes/mr/n1-mono-fielded-result.bend, both main and the tip give eval `f 1` → `Some{On{}}` with tag 1, while Wasm returns `result:0`.

The gate never calls such entries: regen and check.py call enum signatures only. So this is a host-contract gap, not a corpus failure.

**Suggested fix.** Keep an explicit abstract marker in the erased runtime signature instead of datatype 0, or have eval-cli refuse any entry whose parameter or result type is not a closed monomorphic enum. Report `HostFailure` there, as `structured-argument` already does. The Wasm-side refusal of cell-valued exports belongs to the host adapter's owner (`scripts/run-wasm.mjs` is unchanged on this branch). Document it as a known limit in the meantime.

## [minor] (semantics) The SPEC promises descent on any strict field descendant, but a recursive call on a matched descendant is Unsupported

**Evidence.** $R/probes/md/g-matched-descendant.bend does `match xs: case Link{h,t}: match t: case Link{g,u}: last_or(A, t, d)`.
- The seed accepts it.
- The tip reports `Unsupported\tcheck\trecursive-call\t287:294:18:10`. A matched `t` occurs as a rebuilt constructor, not as a Reference.

The mono twin $R/probes/md/m-matched-descendant.bend gives `Unsupported\tcheck\trecursive-call\t389:393:29:10` on both main and the tip, so the limitation is inherited.

This complies with D4. The only problem is wording: research/compiler-generics/SPEC.md says "A live self-call must pass, as its first live argument, a strict field descendant". The same limit also blocks a self-hosting idiom ($R/probes/sh/s1-selfhost-idioms.bend: seed accepts, Knot Unsupported).

**Suggested fix.** Narrow the SPEC sentence to an unmatched strict field descendant, or accept a matched descendant by treating a known binding in `smaller` as descending. If the rule changes, freeze a seed fixture first.

## [major] (gates) The generics gate ran past the runner's 900 s limit, so one of two unmodified gate-suite runs exited 1

**Evidence.** Scratch export of campaign/generics at edfad8b: R=/private/tmp/claude-501/-Users-ericfode-src-knot--claude-worktrees-perch-style-framework-c2cdfc/d7a4ddd4-7d29-4f63-803d-fca5b417c923/scratchpad/review/generics/gates-lens-r5/copy. Its tree is 379b726, the same as the branch tree. The .toolchain and node_modules symlinks are in place, and BEND_NO_TELEMETRY=1 is set. I ran `python3 -B scripts/gates/run.py`, which is what `npm run -s gates` executes, bypassing the socket npm wrapper.

Run 1 (4 jobs, 10:19 to 10:37 PDT, load 26 to 44): exit 1 after 1077.7 s.
- 20 gates passed.
- The runner printed `generics: exhausted (900.01s)`.
- run-9mrz63ko/summary.json records generics as {status: exhausted, error: 'Gate timeout: 900 seconds', exit_code: null, counts: {}}. The receipt tests/compiler-generics/receipts/generics.json has after_sha256 null.
- Receipts: 64 identical, 16 semantic, 9 volatile-only.
- Timeline: the generics gate started at 10:22:48. Its native CLI builds finished at 10:25:38 and the mutant phase began at 10:26:49. At 10:28:55 it was on mutant 5 of 15, `bare-quantity-default`. It was killed at 10:37:48.
- Load stayed at about 38 after the run ended, so most of it came from other sessions. From 10:19 to 10:25 I also ran light offline checks: preflight, census:test and the eight PROOF checks of 1 s or less. After 10:26 I only read files.

Run 2 (same command plus `--keep-scratch`, 10:48 to 11:01, load 24 to 34): exit 0, 21 of 21 passed in 740.9 s, with generics taking 501.00 s.

Direct run (`KNOT_GATE_TIMEOUT_SCALE=4 python3 -B tests/compiler-generics/check.py`, load 25 to 37): exit 0 in 592.4 s real. After the CLI builds, each of the 15 mutants took 17 to 45 s. Each one runs a full seed `--check-only` of a CLI plus a native build and a Bun build (check.py:355-373).

The executor's own generics wall times grow with the gate:
- 159 to 188 s with 5 mutants;
- 284 s with 9 mutants;
- 428, 480, 524 and 833 s with 15 mutants.

The 900 s cap is scripts/gates/run.py:412. HANDOFF.md discloses the risk ('428-833 s vs 900 s under load'), and the prompt requires `npm run -s gates` to exit 0. The failure has now occurred, so one passing run is not a reliable merge signal at the campaign's usual load. The flake is in the increment's own gate, not in the known bootstrap failure 'found no clang': bootstrap passed in both of my runs.

**Suggested fix.** Cut the generics gate's wall time well below 900 s at load 40, and report every full run.

Options:
- Build the native and Bun mutant lanes concurrently, or run mutants in a bounded worker pool.
- Skip the separate whole-CLI `--check-only` step where the seed build already typechecks. Verify that first.
- Group mutants that share an entry.

If that is not done, the runner owner (a coordinator decision) could give generics a recorded per-gate timeout, or GATES.md could make `--jobs 2` the documented merge-signal mode. Until one of these lands, the coordinator should rerun on a quieter host, or with `--jobs 2`, before merging.

## [minor] (gates) Offline style preflight in targets mode over the 24 changed src files exits 3 with 83 structural blockers (manifest mode is clean)

**Evidence.** From R/copy I ran `node scripts/perch-style.mjs --preflight [--json] <24 files>`, where the file list is `git diff --name-only main...campaign/generics -- 'src/*.bend'`. Output: exit 3, 0 provider requests, 493 declarations in 24 files, and 82 truncated contexts (caller-or-byte-limit 8, context-file-limit 33, context-helper-limit 50). The composition is unavailable (223,416/48,000 bytes; 60 collaborators outside the group, 51 nonlocal imports). The task is missing, and structural_blockers is 83.

The same command on the 14 files that also exist on main, run in an export of main c0bd08d: main has 218 units, 32 truncated and 33 blockers; the branch has 232 units, 42 truncated and 43 blockers.

50 truncations are new. Eight are existing LAWS.bend laws that are now at context-helper-limit: no_parser_budget, generic_header, multiple_scrutinees, template_binder, nonleading_template_binder, return_type_application, local_import and hash_import. Two more are parse.bend::run and ::parse. The other 40 are new declarations in generic-catalog.bend, generics.bend, type-parse.bend, types.bend::Expr, check-dispatch.bend::check and type_level_definition in type-erasure-LAWS.bend and type-erasure-PROOF.bend.

Manifest mode (`--manifest=docs/compiler-campaign/manifest.json`) exits 0: 24 groups, 1,227 units, 0 truncated, 24 of 24 compositions available, 0 blockers, 0 requests. Every one of the 493 changed declarations is ranked in some group. frontend-laws is at 47,760 of 48,000 composition bytes, leaving 240 bytes of headroom. Twelve groups use src/SPEC.md as their task; at 22,505 bytes it is over the 16,000-byte limit (task_byte_limit), against 20,417 bytes on main, where it was already over. The executor's round-3 manifest figures reproduce exactly. Round 4 changed no Bend source, so it correctly ran no new preflight. No targets-mode preflight over the whole increment was reported after round 0, whose receipt covers 16 files and 59 blockers.

**Suggested fix.** Record the whole-increment targets-mode result, 83 blockers, next to the manifest result in the handoff, so the coordinator's live review goes through manifest groups. Before any further change to LAWS.bend or type-parse.bend, split frontend-laws or give it its own concise task. The generic groups already have one.

