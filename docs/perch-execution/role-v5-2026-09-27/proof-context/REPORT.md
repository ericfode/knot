# Paired-law prompt wiring repair

The working-copy built-in semantic request now receives the paired law text already selected for custom review. The installer forwards the optional law context through `checkTarget → methodSteps → methodStep`, inside the normal budgeted state builder. Local law lines are excluded from the secondary module-scope rendering; laws are not call-graph nodes. Selection, rules, models, caps, questions and Bend snapshots are unchanged.

[Before](reproduction.json), the actual installed CLI emitted two offline-captured requests for candidate 3 `PROOF.bend::L.put_empty`: the custom request contained its selected contract once; the built-in request omitted it. The nonzero request-level assertion failed. [After](reproduction-after.json), both contain it once and the assertion passes. Stub answers are not semantic evidence; neither capture contacted a provider. Historical candidate review findings remain historical.

Validation:

- [Focused integration](focused-integration.txt): 15/15 passed, including three new regressions. These exercise actual requests, imported/local laws, local deduplication, unchanged questions/graph edges, immutable per-command snapshots, exact byte boundaries, missing/malformed dependencies, token pressure and multiple chunks.
- [Full verification](lint-verify.txt): `npm run lint:verify` ran once; 94/94 tests and all eight law-rule wiring controls passed. No provider contacted.
- [Unchanged-input comparison](control-comparison.json): four complete custom/built-in requests for ordinary Bend and JavaScript are byte-identical before and after.
- A law-only working-copy edit changes the next request and the actual installed `askKey`; the old answer cannot match the new key. Working-copy `check` itself is stateless. The source body and questions stay fixed.
- [First focused attempt](focused-attempt-1.txt) retained: 2/3 passed. Its zero-byte fixture prevented the helper itself from entering context, so no helper law was attempted. The corrected fixture admits the helper while excluding its law; [attempt 2](focused-attempt-2.txt) passes 3/3. No production selection change was needed for this correction.

Installed adapter: `language-pack-1.20-v3+knot-bend-242a2b8f26068922`. Bundle SHA-256: `b5ead90af3e6f258cc50acfca2c2491878da6293c1f8278441be91004135acd1`. The installer hashes its source and the context adapter into this identity; full request state remains part of request/cache identity. See [manifest.json](manifest.json) for recorded artifact hashes.

Limits remain explicit. `context_notes` describes the shared Bend selection; upstream may further shorten helper/caller excerpts under its existing token budget. Selected paired laws specifically remain whole in every chunk/retry or preparation fails. A law omitted by the shared byte selection is not restored into the new `laws` field; its selection truncation remains visible. Existing module-scope behavior outside selected-law deduplication is unchanged. Committed `scan` has a separate context path and is unchanged. The adjacent imported-law file-admission bypass noted in [the proposal](PROPOSAL.md) remains outside scope. No datatype prompt redesign or broader completeness claim is made.

The implementation agent made no live review or source/rule change. The
coordinator then made one [live follow-up](live-result.json) on the unchanged
`L.put_empty` proof: two requests/responses, eleven reported checks, no broken
custom rule. Raw exit 3 remains: the documentation flag is absent in this sample,
but `does_not_do_what_it_claims` remains at .78. The complete original proof entry
checks; direct reduction of `put(Vacant,x)` gives the exact law RHS. The remaining
flag is an evidenced false positive, not an automatic pass. One sample does not
establish a calibration improvement. No unchanged rescore followed.

An [offline identity comparison](style-identity.json) confirms all eighteen
candidate-3 declaration states/source hashes and both composition states remain
identical to their retained style receipts. This semantic wiring repair neither
changes those style inputs nor resolves their recorded failure. Numeric limits,
review questions, thresholds and reviewer configuration remain unchanged.
