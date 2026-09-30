# Classification increment — 2026-09-27

Branch: `campaign/classify`; base: `185b7d5`. Scope: compiler campaign milestone
0, language track. The parser now reports the five recognized out-of-profile
forms as `Unsupported`, with exact phase/code/location diagnostics. It preserves
the six paired malformed controls as `Invalid`. No new source form is executed.

## Fixed expectations and change

The pinned seed accepted all six positive fixtures before parser edits. Local
and hash imports have separate fixtures. All six previously exited 2 in Knot.
The paired malformed fixtures also reached their intended seed syntax errors.
The manifest was fixed before implementation, SHA-256
`014d252d2e1e7cad36fba074213c3a9f0c9b67e593b11a501f92e5c7c37bf6fc`.

| Fixture stem | Original parser boundary at base | New phase/code |
| --- | --- | --- |
| `generic` | line 212, `expect(...,"is")` | `parse / generic-datatype` |
| `match` | line 236, `expect(...,":")` | `parse / match-scrutinees` |
| `template` | line 92, parameter shape | `parse / template-binder` |
| `destructure` | line 107, body terminator | `parse / destructuring-binding` |
| `local-import`, `hash-import` | line 217, declaration-name guard | `parse / import` |

Each stem has a `-malformed.bend` control. The manifest fixes seed results and
complete Knot diagnostics independently of the implementation. `module.bend`
is the shared import dependency. Its package manifest determines the local hash
fixture `0x77a1a37baca5d86f62241cab956a1fb1`; the gate stages it in an isolated
`BEND_LIB`. No hub request or package-publication claim is involved.

The reading hypothesis is one boundary distinction: recognize an out-of-profile
prefix before applying the supported grammar's next-token expectation. `reply`
limits destructuring recognition to constructor terms in function bodies; the
same `=` after a datatype constructor is not treated as a binding. Template
recognition applies to function parameters and still requires a name and colon.
The original `expect` and `invalid` behavior remains unchanged.

Six added laws quantify over diagnostic locations and arbitrary remaining token
lists (and constructor fields for destructuring). The complete
`src/PROOF.bend` entry prints `All terms check.` These are prefix-classification
laws, not general parser correctness or validity proofs for the remaining input.

## Gates

Every command below was run with `BEND_NO_TELEMETRY=1`. The seed is Bend 2.0.29,
revision `574b6d39a235b539eb19a5c532993a0abb3d11ad`, via `scripts/bend-reference`.
Existing test assertions and corpus manifests were not changed.

| Command | Exact passing coverage |
| --- | --- |
| `python3 tests/subsets/check_frontend.py` | 14 original fixtures in two lanes; 24 original boundary observations; 10 laws (4 retained, 6 added); 11 semantic mutants (4 retained, 7 added); 12 new classification fixtures in two lanes; 72 checker/evaluator/compiler rejection observations; 24 preserved output artifacts |
| `python3 tests/compiler-checker/check.py` | 49 reference fixtures; 98 checked observations; 10 depth and 16 catalog-bound observations; 7 mutants |
| `python3 tests/compiler-structural/check.py` | 16 reference fixtures; 4 boundary pairs; 7 mutants |
| `python3 tests/compiler-fields/check.py` | 40 reference fixtures; 240 phase observations; 36 budget probes; 6 host probes; 12 level/inspection observations; 9 mutants |
| `python3 tests/compiler-wasm/check.py` | 25 programs; 90 reference calls in each of two lanes; 64 rejection pairs; 44 boundary observations; 7 mutants |
| `bun tests/compiler-wasm/trust.ts` | 3 entries, 0 holes each; loaded-file counts 15 / 13 / 18 |
| `bun tests/compiler-fields/trust.ts` | 4 entries, 0 holes each; loaded-file counts 22 / 12 / 13 / 15 |
| `bun tests/compiler-structural/trust.ts` | 2 entries, 0 holes each; loaded-file counts 20 / 8; exact 5-effect observer allowlist |
| `python3 research/owned-store/check.py` | 3,532 cases in two lanes; 15 literal witnesses; 6 mutants |
| `python3 research/flat-store/check.py` | 13,621 observations and 3,534 instances per lane; 2 installed boundary states and 7 lifecycle checks per lane; 9 mutants; byte-identical 1,050-byte module |
| `npm run -s lint:verify` | 103 tests passed, 0 failed; all 8 law rules passed the offline wiring check |

All three trust inventories retain the same 42 loaded foreign definitions and
two Base unsafe definitions (`Array.fork`, `Array.join`) per entry. Complete
frontend, checker, catalog, fields and runtime proof entries passed. The 25
tracked emitted Wasm modules are byte-identical to the base commit, in addition
to byte identity between the two current lanes. All five original corpus
fixture-result records are unchanged after normalizing checkout paths.

The first flat-store invocation raced the owned-store receipt writer; it was
rerun after owned-store completed and passed. The first lint invocation was
blocked by the sandbox's cache-lock restriction. Copying the existing
`tree-sitter-language-pack/v1.20.0` cache to `.local/classify-probes/parser-cache/`
and setting `TREE_SITTER_LANGUAGE_PACK_CACHE_DIR` to that directory made the
unchanged command pass offline. No gate assertion was relaxed. Store receipts
were restored after confirming identical source hashes, logical results and
mutant outcomes; their changes were only paths, timing and gzip metadata.
The new-file whitespace check reports the final blank line in `module.bend`.
Those frozen reference bytes are retained because they determine the local
package hash; all other changed files pass the whitespace check.

## Mutants

Each new mutant type-checks through the seed's full CLI entry before building.
The fixed witness must produce the exact opposite Invalid/Unsupported class,
with the original phase/code/location and empty stdout. Host failures, parser
errors in the mutant, timeouts and unrelated diagnostics cannot count as kills.

- `generic-invalid`, `match-invalid`, `template-invalid`,
  `destructure-invalid`, `import-invalid`: demote the corresponding recognized
  prefix to Invalid; each is killed by its fixed accepted-reference witness.
- `malformed-unsupported`: promote the parser's ordinary invalid outcome;
  killed by `template-malformed`.
- `expected-unsupported`: promote a failed expected-token check;
  killed by `generic-malformed`.

## Offline preflight and remaining work

[`receipts/classification-preflight.json`](receipts/classification-preflight.json)
retains exact structural results and source hashes. Implementation preflight
covered 42 declarations in three files, with zero provider requests. Four
contexts are truncated: `parse::Parsed` and `parse::Mode` hit the context-file
limit; `parse::invalid` and `parse::unsupported` hit caller/byte limits. The
composition is available at 26,496 of 48,000 bytes, with no unresolved references.
An explicit 284-byte task supplied the fixed classification obligation.

The seven valid fixture files have 16 declarations and no truncated contexts.
Their combined composition is unavailable because the hash import remains a
nonlocal-import context gap. All six intentional malformed controls are rejected
by the tooling parser as expected. No conceptual-compression, Delight, memetic,
Anticipation or Payoff rating was requested; none is reported as a pass.

Recognition stops at the identified prefix. It does not validate the remainder,
load imports, implement generics/templates/pattern matching, or establish
self-hosting. The next increment needs those capabilities' independent seed,
evaluator and Wasm expectations before implementation. The coordinator owns
live Perch review, context-gap disposition, commit review and merging.

The executor could not stage a commit: the sandbox denied the worktree's index
lock under `/Users/ericfode/src/knot/.git/worktrees/campaign-classify/`.
The reviewed files remain in this dedicated worktree; an explicit-path patch and
commit message are provided under `.local/` for the coordinator.

## Generics supersession — 2026-09-28

The generics increment (`knot-generics-1`) parses generic datatype headers, so
the `generic` fixture no longer reports `Unsupported parse generic-datatype`.
The coordinator's review-round-1 authorization replaces that one pin with
phase-specific expectations. They were derived from the fixture's unchanged
seed reference (`bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts
tests/subsets/classification/generic.bend` exits 0 with `Box{On{}}`) and
literal review, not from Knot output:

| Phase | Expectation | Basis |
| --- | --- | --- |
| parse | exit 0, `Parsed<TAB>` record | seed accepts; generic headers are in profile |
| check | exit 0, `Checked` record | seed accepts |
| eval `main` | `Evaluated<TAB>0<TAB>0<TAB>Box{On{}}` | seed value; `CONTRACT.json` evaluator record; `Box` is type 0, constructor 0 |
| compile (enum profile) | exit 3, `Unsupported check constructor-fields 30:33:2:2`, prior artifact kept | `catalog-LAWS.bend::field_capability_is_not_acceptance` locates the first fielded constructor; `Box` spans bytes 30..33 at line 2, column 2 |

The retired pin is kept in the case record under `superseded`. The gate reads
a case's `phases` record when present and otherwise applies its shared record
to every phase, as before.

The `generic-invalid` mutant's anchor no longer exists. Its replacement,
`parameter-type-invalid`, demotes `unsupported(rest,"parameter-type")` in
`parse.bend`, the coordinator's suggested anchor. Its only witness among the
29 original cases, `application-parameter`, now parses as a type application.
A new seed-accepted witness therefore pins the anchor's remaining reachable
use, a function-typed parameter:

- `classification/function-parameter.bend`: the seed prints `On{}` (exit 0);
- Knot reports `Unsupported parse parameter-type 52:53:5:17` at the `-` of
  `->` (byte 52, line 5, column 17), derived from the source bytes.

The classification-mutant count stays at seven. The generics increment merges after closures and owns this witness
supersession at integration under D26. See
[the merge plan](../compiler-generics/MERGE-WITH-CLOSURES.md); neither mutant
may silently disappear when the function-typed parameter becomes accepted.

Six classify-2 cases (`application-parameter`, `-return`, `-binding` and their
`-after-prefix` twins), their three classification-gate mutants and the laws
`return_type_application` and `binding_type_application` also conflict with
generic type applications. The review-round-1 authorization did not cover
them, so `5eea108` left them unchanged.

### classify-2 supersession (authorized, `78c4942`)

`78c4942` applied the same reconciliation to the six application cases.
Its message cites "Coordinator authorization (2026-09-28)" for a patch that
the generics round-1 executor prepared. Git records only the shared author.
The review-round-2 task restates the authorization: the branch "now carries
the coordinator-authorized supersession of classify-2's type-application
pins". Each retired pin is kept
under `superseded`, whose `by` field names that authorization. The first
version of those six fields read "proposed ..., awaiting coordinator
authorization" (review round 4 corrected them). The
three seed-accepted cases get phase expectations (parse and check accept;
eval `Evaluated<TAB>0<TAB>1<TAB>On{}`, `Evaluated<TAB>1<TAB>0<TAB>Nil{}` and
`Evaluated<TAB>0<TAB>1<TAB>On{}` from the seed values, CONTRACT.json and
declaration order; enum compile `Unsupported check constructor-fields` at the
generic `List`'s first constructor `Nil`, which carries the boxed family's
synthetic erased field). The three after-prefix twins pin
`Unsupported parse type-expression` at the first token after `<`.
`return_type_application` is restated as the typed-result transition and
`binding_type_application` is retired. `78c4942` also retired the
classification gate's three application mutants. Review round 2 found that
one of their anchors still existed, and `d3cee9f` restored the gate to seven
mutants (see `tests/compiler-classification/README.md`).
