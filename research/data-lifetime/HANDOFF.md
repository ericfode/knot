# r3r7 executor handoff

Branch: `campaign/r3r7`. Base:
`185b7d5ffad5a4e8d59ccc52b95a5b9c83c5330d`. Scope:
`research/data-lifetime/` and `docs/RUNTIME-SUPPORT-PLAN.md` only. No source,
package, existing assertion or other worktree was changed. No network or `.env`
access was needed.

Recommendation: **B, unique Type plus RC Data**, pending coordinator/user decision.
The packet is complete as a bounded policy experiment; actual Wasm/GPU owned
storage and lifetime acceptance remain open. See [README.md](README.md) for
record mapping, emitter costs, counter definitions and the next acceptance gate.

**Commits: none.** `git add` could not create
`/Users/ericfode/src/knot/.git/worktrees/campaign-r3r7/index.lock`:
`Operation not permitted`. The session cannot write the shared Git metadata,
and its approval policy does not permit escalation. No index/branch workaround
was attempted. Frozen expectation hashes preserve the pre-implementation
checkpoint; the final packet hash manifest identifies all delivered files.

Coordinator commit after review, from this worktree with Git metadata access:

```sh
git status --short --branch
git add docs/RUNTIME-SUPPORT-PLAN.md research/data-lifetime/
git diff --cached --check
git diff --cached --stat
git diff --cached
git commit -m 'Compare copied and counted Data lifetime policies' \
  -m 'Add independent trace models, filled proofs, semantic mutants, measured storage costs and the milestone-1 decision packet. Actual emitter/device integration and live Perch qualification remain open.' \
  -m 'Co-Authored-By: GPT-6 Astra <noreply@openai.com>'
git status --short --branch
```

Only the two scope paths above remain changed. All 15 regenerated existing
receipts were restored. `git checkout -- <explicit receipt paths>` hit the same
index-lock restriction, so restoration read the exact `HEAD:<path>` bytes with
`git show` and wrote only those test outputs after checking their fresh hashes.
Their fresh checks and hashes are recorded in `receipts/regression.json`; gzip
payloads were byte-identical. Older compiler receipt source-hash drift belongs
to the coordinator's main refresh, not this research increment.

| Existing gate | Fresh exact result |
| --- | --- |
| `tests/subsets/check_frontend.py` | 14 reference fixtures, 2 parser lanes, 24 boundaries, 4 laws, 4 semantic mutants |
| `tests/compiler-checker/check.py` | 49 reference fixtures, 98 checked observations, 10 depth + 16 catalog-bound observations, 7 mutants |
| `tests/compiler-structural/check.py` | 16 seed fixtures, 4 boundary pairs, 7 mutants |
| `tests/compiler-fields/check.py` | 40 seed fixtures, 240 phase observations, 36 budget + 6 host + 12 level/inspection observations, 9 mutants |
| `tests/compiler-wasm/check.py` | 25 programs, 90 reference calls compared in each of 2 lanes, 64 rejection pairs, 44 boundaries, 7 mutants |
| `tests/compiler-wasm/trust.ts` | 3 entries (15/13/18 loaded files), 0 holes, 42 foreign declarations and 2 seed unsafe primitives per entry |
| `tests/compiler-fields/trust.ts` | 4 entries (22/12/13/15 files), 0 holes, 42 foreign declarations and 2 seed unsafe primitives per entry |
| `tests/compiler-structural/trust.ts` | 2 entries (20/8 files), 0 holes, 42 foreign declarations and 2 seed unsafe primitives per entry |
| `research/owned-store/check.py` | 3,532 traces and 15 literals per lane × 2; 14 equations, 5 quantity controls, 4 generation observations, 6 mutants |
| `research/flat-store/check.py` | 3,534 instances and 13,621 observations per lane × 2; 7 lifecycle checks per lane, 24 literal probes, 15 equations, 9 mutants; unchanged 1,050-byte Wasm |
| `npm run -s lint:verify` | 103/103 tests; 8 law-rule wiring controls; 0 provider requests |

All invocations exported `BEND_NO_TELEMETRY=1`. Existing gate subprocesses used
a local Bun wrapper adding `--no-env-file`. The first lint run had 88 passes and
11 cache-permission failures; it passed unchanged after copying the already
installed parser manifest/libraries into `.local/data-lifetime/parser-cache`
and setting `TREE_SITTER_LANGUAGE_PACK_CACHE_DIR` to that directory.

New gate: **105 traces × 2 candidates × 2 lanes; 6,788 full-state observations;
20 literal checks; 1,691 cross-policy value/holder pairs; 20 filled laws; 5
quantity controls; 16/16 type-correct semantic mutants killed.** Four source
fixtures produce 4 seed + 8 evaluator agreements. Their current Wasm lane is
8 explicit Unsupported outcomes with old-artifact preservation. Both new trust
entries have zero holes; the generated model uses only `IO.print`.

Offline preflight: **137 declarations / 8 files; 15 truncated contexts**
(11 caller/byte, 4 helper); composition available at 25,109 / 48,000 bytes.
The 15 truncated declarations also lack supporting-role context. No live
semantic/style ratings, no automatic style pass. Coordinator review must retain
all five axes and these context limitations.

The new trace fixtures include zero/full capacity, rejected incoming owners,
partial-copy and shared-open rollback, RC ceiling, Type-copy rejection, ordered
fields, mixed ownership reconstruction, suspended/partial-join holders, duplicate
delivery, cancellation, two readers, and cleanup budgets 0/1/sufficient. Source
fixtures: `tree-share`, `list-tail`, `owned-rebuild`, `shared-open`.

Retained mutants: copy aliases original; copied fields reversed; missing retain;
count ceiling ignored; first release frees; never reclaim; cleanup loses tail;
zero budget loses work; reader barrier ignored; serial 7 disposed twice; failure
loses incoming owner; take retains parent; shared open forgets child acquires;
Type owner copied; suspended root omitted; partial-join root omitted. Each has
its exact typecheck/build command, changed source hash and first semantic witness
in `receipts/gate.json`.
