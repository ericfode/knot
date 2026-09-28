# classify-2 handoff

The three assigned classification boundaries are repaired. Non-leading `~`
binders report `Invalid parse parameter`; constructor `==` and `=>` report
`Invalid parse end-of-body`; generic return types and local annotations report
`Unsupported parse type-application` at `<`. Parameter type applications retain
their existing `Unsupported parse parameter-type` code. No syntax, checking,
evaluation or Wasm execution capability is added.

Parser edits are restricted to `ListTail`, `reply`, `FunctionTail` and
`AnnotatedBinding`. `MatchTail`, import parsing, existing test assertions and
the original twelve classification expectations are unchanged. No new
`src/*.bend` file requires a manifest group.

## Fresh deterministic verification

`BEND_NO_TELEMETRY=1 npm run -s gates` exited **0**. All original fourteen gates
and the appended `classification` gate passed. Counts overlap and are not summed.
The normalized counts and detailed completion evidence are retained in
`receipts/validation.json` and `receipts/gates.stderr.txt`.

| Gate | Exact passed coverage |
| --- | --- |
| frontend | 14 original seed fixtures; 28 parser observations; 24 boundaries; 4 original mutants; 29 classification fixtures; 58 classification parser observations; 7 classification mutants; 174 downstream rejections, including 58 preserved compiler outputs |
| checker | 49 seed fixtures; 98 checked observations; 10 depth probes; 16 catalog-bound observations in 2 records; 7 mutants |
| structural | 16 seed fixtures; 64 catalog/compiler observations; 4 boundary pairs; 7 mutants |
| fields | 40 seed fixtures; 240 phase observations; 36 budget probes; 6 host probes; 12 level/inspection observations in 2 records; 9 mutants |
| wasm | 25 programs; 90 seed calls in 2 execution lanes; 64 rejection pairs; 44 boundaries; 7 mutants |
| wasm-trust | 3 entries; 0 proof holes |
| fields-trust | 4 entries; 0 proof holes |
| structural-trust | 2 entries; 0 proof holes |
| owned-store | 3,532 cases in each of 2 lanes; 15 literal witnesses; 6 mutants |
| flat-store | 13,621 observations, 3,534 instances, 2 installed boundary states and 7 lifecycle checks per lane; 2 lanes; 9 mutants |
| recursion | 19 seed fixtures; 114 phase observations; 4 fuel probes; 3 mutants |
| fields-wasm | 8 fixtures; 32 seed calls; 64 evaluator and 64 Node observations; 50 frozen enum-byte checks; 30 boundary probes; 4 mutants killed in both lanes; 5 checked laws |
| census | 30 compiler source files; 437 declaration events; 41 feature classes |
| lint:verify | 127 tests; 8 law-rule wiring controls; 0 provider calls |
| classification | 17 exact frozen seed outputs; 17 parser observations; 6 type-correct semantic mutants; 16 filled frontend laws |

`npm run -s gates:verify` exited **0**: **18 tests**, including the wrapper's six
semantic mutants. The direct complete entry command
`bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts src/PROOF.bend` printed
`All terms check.` with telemetry disabled. The unchanged frontend runner's
printed six-classification-law label is historical; the complete entry contains
four boundary and twelve classification laws.

The runner classified **81 artifacts**: **63 identical**, **7 volatile-only**,
and **11 semantic**. Semantic differences include the new precision receipt, the
expanded frontend classification corpus and source/build hashes. No existing
assertion was changed. The direct frontend run's shared receipt was restored
with `git checkout -- tests/subsets/receipts/frontend.json`; all shared gate
receipts remain the coordinator's refresh responsibility.

## New controls and mutants

The 17 fixtures are appended to `tests/subsets/classification-cases.json`, with
source hashes and full pinned seed commands/outputs fixed before implementation.
`receipts/baseline.json` records **12 wrong baseline classifications** against
that unchanged expectation hash.

- Six template controls: ordinary, erased and reusable non-leading binders;
  malformed non-leading type; two leading binders; malformed type after a leading
  template prefix.
- Five constructor controls: equality and arrow, each with and without a right
  operand; malformed suffix after plain `=`.
- Six generic controls: parameter, return and local binding types before the
  generic datatype header, each paired with a malformed argument after `<`.

The new precision gate kills `nonleading-template`, `equality-as-binding`,
`arrow-as-binding`, `parameter-application-invalid`, `return-application-invalid`
and `binding-application-invalid`. Each mutant passes the complete parser CLI
typecheck and builds before the fixed diagnostic assertion kills it. Parser/type
errors, host failures and exhaustion cannot qualify as semantic kills.

Six filled laws cover the same distinctions. The existing destructuring law is
narrowed by an inhabited premise excluding both operator continuations. These
are quantified transition laws over locations and suffixes, not a whole-parser
soundness theorem.

## Offline review and limits

The source-only preflight (`receipts/preflight-bounded.json`) exits **3**:
**54 declarations / 3 files**, **4 truncated contexts**, **0 unranked files**,
**0 provider requests**. `Parsed` and `Mode` reach the context-file limit;
`invalid` and `unsupported` reach the caller/byte limit. Supporting-role context
is unavailable for those same four declarations. The composition is available
at **29,806 / 48,000 bytes**, without unresolved context. The bounded task is
available at 4,584 bytes. No compression, delight, memetic, anticipation or payoff
ratings were produced, and no automatic style pass is claimed.

The earlier preflight using `src/SPEC.md` also records `task_byte_limit`; the
bounded task resolves that task-context issue without changing source. A
preflight over all twenty changed/new Bend paths exits **1** at the intentionally
seed-rejected `template-nonleading.bend`; its exact command and failure are in
`receipts/preflight-all-paths.json`. Syntax-negative fixtures are not reviewable
implementation declarations.

`npm run census:approve` and `npm run -s census` succeeded. The approval adds six
law/fill pairs, widens the conditional destructuring law/proof classes, and adds
two proof imports. Its exact printed summary is in `receipts/census-approval.txt`
and the commit message. The runtime implementation feature classes do not widen.

The coordinator should review/merge this increment alongside nest and modules,
refresh shared receipts, and perform live semantic/style review. Templates,
destructuring and generic types remain Unsupported; their implementation belongs
to later capability increments. Prefix recognition still makes no validity claim
about the unconsumed suffix. Nest and modules retain ownership of multi-scrutinee
matching and import paths.
