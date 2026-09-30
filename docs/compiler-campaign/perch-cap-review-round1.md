# perch-cap review round 1

All two major and four minor findings in the confirmed r0 review are fixed.
No finding is disputed. Work is confined to `campaign/perch-cap`; no branch was
pushed, merged or rebased. No Bend implementation, package, rubric or frozen
JSON expectation changed. The contract correction is a separate seed-witness
amendment (`9e91a4a7`). No provider/live Perch call or environment-file read ran.

## Repairs and evidence

- Canonicalize summary metadata only after both earlier fitting returns. The
  seed-accepted full-to-interface witness has identical complete states under
  `en_US.UTF-8` and `da_DK.UTF-8`: 59,829 bytes, SHA-256
  `a3713c8ccedd645eee88edd3620dc032ee1c7b5d3d616d7247c7df46a5dc9d7c`.
- Rank complete encoded savings, including byte/count digits and array commas,
  and recompute after each cut. An independent one-byte boundary now cuts only
  `b.bend`, retaining `a.bend`'s signature. A second witness changes rank after
  the first cut. Ties compare Unicode scalars: U+E000 precedes U+10000.
- Honor the original primary/task/names failure boundary. Compact metadata
  before omitting required contract source. The seed-accepted 400-datatype
  witness now fits at **56,427 bytes**, retaining every datatype and law source;
  its all-names minimum is 42,245 bytes. Required type/law omissions retain
  complete source in provenance, names/file hashes/reasons, and explicit
  truncation that withholds qualification. Optional notes cannot push the exact
  names minimum over the cap; that boundary fits and one byte below fails.
- Select Bun 1.3.14 explicitly. Bind scratch HEAD to the archived commit with
  read-only Git object alternates before the offline rule catalog. Both the
  worktree and scratch catalog runs list 57 rules with environment loading
  disabled. The initial guard rejected the CLI's loader entry before any read.

Seven additive controls and five new semantic mutants were frozen in
`2a3f4f82`; all original 40 controls and 13 mutants remain binding. Current
coverage is **47 controls, 18 assertion-killed mutants, 65 tests**, the complete
seed signature check and two byte-identical manifest preflights. Full details
and every affected unit are in
[the measurement artifact](perch-cap-review-round1-measurements.json).

## Byte identity on main's manifest

Source snapshot: `88f02bf1`, exported to permitted scratch without environment
files. Compare the baseline implementation against this increment on those
same sources: **957/957 declaration hashes and 17/17 composition hashes match**
(974 total; zero changed). The complete official preflight receipt is also
byte-identical: 722,704 uncompressed bytes, SHA-256
`044303f73a4743fd95f46fe30ba64bfe2f9a44fe218a8d402f9ead579f95ff06`.
The deterministic gzip is 42,490 bytes, SHA-256
`20f828fb6509eb060a25e007100ba5a66c5aee94692b2b90c701331bcdbc2e2d`.
Existing compiler preflight observations do not move.

## Motivating tree

These fresh measurements repeat the initial implementation's pinned motivating
snapshot, `campaign/literals-integ` at **6617f09b**, containing 8ea6faf. That
branch has since advanced; these numbers describe the named snapshot. Only its
scratch export was modified. Each variant has 2,713 declaration states and 36
compositions. The interface column stops when the legacy tier first fits or
is exhausted, just as production does.

| Variant | Raw run state | After interface tier | Fitted run state | Names cuts | Source bytes cut / encoded bytes cut |
| --- | ---: | ---: | ---: | ---: | ---: |
| (a) Snapshot as recorded | 68,192 | 59,941 | 59,941 | 0 | 0 / 0 |
| (b) Restore both `C.exhausted(C.Checked,token)` uses | 68,447 | 60,784 | 59,834 | 4 | 1,004 / 950 |
| (c) Also restore the three original task files | 73,295 | 65,632 | 59,881 | 27 | 4,984 / 5,751 |

In (a), zero units need names-only. In (b), only `src/check.bend::run` does.
In (c), **53 units** do: checking 1 (27 cuts), pattern-matrix-laws 40 (12–40),
pattern-matrix-proofs 11 (13–19), module-loading 1 (15). Every unit fits; the
largest is 59,979 bytes. The artifact records every target and its exact cuts.

The three largest compositions in (b) and (c) are `literal-source-machine`
47,639, `checking` 47,311 and `pattern-matrix-proofs` 46,848 against **48,000**
(margins 361, 689 and 1,152). All 36 remain available with the original tasks.
No further composition fix is required. The prior honest split of matrix laws
and proofs stays in place. Existing tasks larger than the separate 16,000-byte
task budget remain unavailable task evidence; this increment does not alter
that budget or promote missing profundity evidence.

## Deterministic verification

Final full execution: `BEND_NO_TELEMETRY=1 npm run -s gates -- --jobs 2`, Bun
1.3.14, Node 22.22.3. **20/20 passed, exit 0**, measured 450.800934 seconds.
The retained summary is `.local/gates/run-_a32vyij/summary.json`. This ran on
`8a265822`'s executable inputs; subsequent commits record evidence only.

| Gate | Result / exit | Exact counts |
| --- | --- | --- |
| frontend | passed / 0 | `{"boundaries":24,"fixtures":14,"lane_observations":28,"mutants":4}` |
| checker | passed / 0 | `{"bound_observations":16,"bounds":2,"budgets":10,"fixtures":49,"lane_observations":98,"mutants":7}` |
| structural | passed / 0 | `{"bounds":4,"fixtures":16,"lane_observations":64,"mutants":7}` |
| fields | passed / 0 | `{"bound_observations":12,"bounds":2,"budgets":36,"fixtures":40,"host_boundaries":6,"lane_observations":240,"mutants":9}` |
| wasm | passed / 0 | `{"boundaries":44,"execution_lanes":2,"fixtures":25,"mutants":7,"reference_calls":90,"rejects":64}` |
| wasm-trust | passed / 0 | `{"entries":3,"proof_holes":0}` |
| fields-trust | passed / 0 | `{"entries":4,"proof_holes":0}` |
| structural-trust | passed / 0 | `{"entries":2,"proof_holes":0}` |
| owned-store | passed / 0 | `{"cases":3532,"execution_lanes":2,"literal_witnesses":15,"mutants":6}` |
| flat-store | passed / 0 | `{"bun":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621},"mutants":9,"native":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621}}` |
| recursion | passed / 0 | `{"fixtures":19,"mutants":3}` |
| fields-wasm | passed / 0 | `{"boundaries":30,"fixtures":8,"mutants":4}` |
| census | passed / 0 | `{"classes":41,"declarations":437,"files":30}` |
| perch-context | passed / 0 | `{"fixtures":47,"mutants":18}` |
| lint:verify | passed / 0 | `{"law_rules":8,"tests":192}` |
| bootstrap | passed / 0 | `{"corpus":789,"mutants":54,"reached":2,"stages":8}` |
| classification | passed / 0 | `{"fixtures":17,"mutants":6}` |
| io-host | passed / 0 | `{"cli_runs":6,"conformance_runs":86,"errno":[2,9,20,21,22,92],"fixtures":20,"host_boundaries":22,"mutants":6,"review":{"empty_write":4,"mutants":3,"oracle_controls":14,"secret_paths":21,"seed_runs":12},"seed_fixtures":40,"seed_runs":109,"stress":{"left_binds":100000,"right_binds":100000}}` |
| io-abi-2 | passed / 0 | `{"case_mode":"insensitive","fixtures":43,"host_boundaries":25,"mutants":5,"mutants_killed":5,"parity":153,"read_observations":21,"reference_observations":64,"seed_exhausted":2,"seed_observations":61}` |
| selfhost | passed / 0 | `{"blocked":63,"cases":65,"d4_gaps":5,"judge_mutants":20,"mutants":3,"passed":2}` |

`npm run -s gates:verify`: exit 0, 20 tests. `npm run -s lint:verify`: exit 0,
192 tests plus eight law-rule wiring controls; the full run independently
repeats this. `npm run -s lint:rules -- --json`: exit 0, 57 rules, with dotenv
loading disabled. The same catalog succeeds in a scratch archive bound to
HEAD 88f02bf1. `npm run -s census:check`: exit 0.

Receipt classes: 65 identical, 21 volatile-only, two semantic. The semantic
paths are bootstrap `progress.json` and `reference.json`; they remain for the
coordinator. Only the owned context receipt was refreshed, with every input
hash verified. Compiler group/preflight observations are unchanged.

The first full attempt finished 19/20: a stale generated census input hash
failed. Regeneration changed exactly two dependent hash rows; policy and
classifications stayed fixed. The runner retried one recognized clang-discovery
host failure and selfhost then passed. An intermediate receipt checkpoint used
an older local receipt after a failed scratch lookup; `8a265822` corrects it
from retained normalized evidence and verifies every hash. History is retained;
[the review log](../perch-review-log.md) records both corrections and prevention.

## Offline reproduction

Use the existing frozen controls and the pinned Bun before full gates:

```sh
export BEND_NO_TELEMETRY=1
export PATH="/Users/ericfode/.bun/bin:$PATH"
set -euo pipefail
test "$(bun --version)" = 1.3.14
python3 -B tests/perch-context/check.py
npm run -s census:check
npm run -s gates -- --jobs 2
npm run -s gates:verify
npm run -s lint:verify
```

For scratch catalog checks, archive without `.env` or `.env.*` members, link
only the required installed toolchain/dependencies, initialize Git, then bind
HEAD. These commands write only the permitted scratch export:

```sh
scratch=$(mktemp -d /private/tmp/knot-codex/perch-cap/scratch/catalog-XXXXXX)
git archive 88f02bf1 -- . ':(exclude,glob)**/.env*' ':(exclude,glob).env*' | tar -x -C "$scratch"
ln -s "$PWD/.toolchain" "$scratch/.toolchain"
ln -s "$PWD/node_modules" "$scratch/node_modules"
git -C "$scratch" init -q
archive_objects=$(git rev-parse --path-format=absolute --git-path objects)
printf '%s\n' "$archive_objects" > "$scratch/.git/objects/info/alternates"
git -C "$scratch" update-ref HEAD 88f02bf1
```

The CLI unconditionally enters `process.loadEnvFile` even for `rules list`.
Use a Node preload that makes that loader a no-op, rejects filesystem reads
whose basename is `.env` or starts `.env.`, and rejects network calls, then
run `npm run -s lint:rules -- --json`. The tested preload and raw probes are in
`.local/perch-cap/review-round1/`; their data are retained in the tracked artifact.
The measurement harness and a/b/c exports are under the same ignored evidence
directory and `/private/tmp/knot-codex/perch-cap/scratch/review-round1-*`.

## Remaining coordinator actions and limits

Merge/integrate the reviewed increment, reconcile the motivating branch's
call/task restores where still needed, refresh shared bootstrap receipts on
main, and perform live Perch calibration. These actions are outside implementer
ownership and do not block this increment. Ordinary helper/caller names-only
contexts remain advisory and uncalibrated; omitted type/law evidence is a
structural limit. This is a tooling completion, not whole-compiler self-hosting
or a style qualification. Selfhost still has 2 passing and 63 blocked cases.
