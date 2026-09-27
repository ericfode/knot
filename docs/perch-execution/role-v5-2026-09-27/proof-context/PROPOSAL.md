# Paired-law context omitted from built-in review

The installed working-copy `check` path selects the proof's law, but drops it before building built-in questions. This is a prompt-wiring defect, not evidence that the proof or its accepted contract is wrong. Repair only the delivery of already-selected paired laws; preserve configuration, rule questions, models, source snapshots, context limits and historical receipts.

## Reproduction

[reproduction.json](reproduction.json) captures actual installed CLI requests for candidate 3 `PROOF.bend::L.put_empty`, with `fetch` replaced completely by an offline fixture. Both paths made nonzero requests: custom 1, built-in 1. The exact selected `law put_empty` source appears once in custom state and zero times in built-in state. The request-level regression assertion fails with exit 1. All recorded input hashes stayed unchanged; zero live provider requests. The stub CLI's exit 3 is arbitrary fixture-answer output, not a semantic result. An earlier harness attempt incorrectly required stub exit 0 and is recorded separately.

Current installed bundle SHA-256 is `9cae96b7fb9dc2f508389d523db3c2948bd6803e52af54fcd6654cf8507914ef`; its profile is `language-pack-1.20-v3+knot-bend-a91631dcc912aed6`.

## Exact loss point

- `scripts/perch-bend-context.mjs:164–185,206–221` selects paired laws from the immutable working-copy snapshot and charges their source bytes through the existing `add` function. `:278–286` returns them in `seen.laws`, but `builtin` only contains node/methods/imports/callees/callers.
- `scripts/install-perch-bend.mjs:85–100` routes custom requests through `bendReview.seen`, while built-in requests use `bendReview.builtin`.
- Installed `node_modules/@lakeday/perch/dist/cli.mjs:217199` forwards custom `seen`; `:217217` forwards only the built-in node/import/method/callee/caller fields into `methodSteps`. Merely adding `builtin.laws` would therefore not fix the prompt.
- Installed `:215919–215954` builds and budgets built-in state without laws. `:215984–216011` propagates optional method-step arguments across every source chunk/retry. The required fix belongs in this preparation chain, inside the budgeted `build` function.
- Existing `tests/perch-bend-integration.test.mjs:81–82` tests custom law visibility only; that test selects a custom rule and suppresses built-in review.

## Bounded repair

Patch the installed bundle through its maintained installer, adding an optional Bend-only paired-law/context-notes argument from the existing `seen` selection to `checkTarget → methodSteps → methodStep`. Supply exact selected entries as a dedicated `laws` state field inside `build`. No new law lookup, graph nodes, model instructions, thresholds, limits, or whole-file context. Ordinary requests without selected law context retain their existing state shape.

Reuse the already-charged source selection; do not charge a second helper/file admission. Deduplicate entries by source path/span. When a local law would also be rendered in `module_scope`, omit only those selected law lines from that secondary rendering, preserving unrelated scope. Never disguise laws as callees: that would invent call edges and misuse/follow questions. Never append them after the token check or place the only copy in droppable module scope. Every source chunk, question batch, and token retry keeps each selected contract whole or fails visibly as incomplete. Existing unresolved/truncated context notes remain explicit; this repair cannot make missing context complete.

The shared Bend limits remain 16 helpers, 12 files, 48,000 source bytes and 4 callers. Existing upstream state/single/request budgets remain 24,000/30,000/60,000 estimated tokens. One adjacent limitation is outside this wiring repair: the imported-law fallback at context `:216–218` directly calls `importedFile`, bypassing the `admitted` check used by `resolveReference(:137–149)`. The reproduced request uses only two files, below the cap. Do not claim this increment repairs all law-selection admission behavior or widen selection to compensate.

## Required regressions and identity

1. Capture real installed CLI requests with offline fetch: imported proof, nonzero custom and built-in review; exact selected law appears once in every relevant state. Assert before-fail/after-pass, keeping the original receipt.
2. Cover local paired laws with intervening declarations: no duplicate scope copy or unrelated law, unchanged graph/question set. Unpaired Bend and non-Bend controls keep unchanged request bytes.
3. Change only a paired law: proof body stays fixed, next invocation's law provenance and built-in request/cache identity change; within-invocation snapshots stay stable. Exercise the actual cache-key function, not merely a source hash.
4. Exercise byte omission and token pressure/chunking: selected laws stay whole on all outbound states, or preparation fails; unresolved/truncated status stays visible. No post-budget injection.
5. Run focused integration tests, then `npm run lint:verify` once after implementation.

`scripts/perch-throughput-patch.mjs:185–193` hashes full state, compiled questions and question/client identities (`knot-request-v2`). Correctly adding law text changes that key automatically. `scripts/install-perch-bend.mjs:135–142` hashes installer/context sources into the installed adapter profile, invalidating older adapter identities. Preserve old receipts; only fresh reviews can establish a new semantic outcome. Working-copy `check` is stateless; committed `scan` follows a separate preparation path (`cli.mjs:216926`) and remains outside this repair. Style preparation is separate and needs no change.

Proposal evidence only at creation: no source repair, live review, score change, or acceptance claim. Implementation was subsequently authorized by the parent as a separate bounded increment.
