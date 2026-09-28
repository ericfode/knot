# Generics and quantity arguments

`knot-generics-1` checks erased type/quantity parameters, nested nominal
applications, invariant phantom parameters, `Kind(q)` meets, compact quantity
forms, generic fields and first-live-parameter descent. It projects checked
terms into the existing evaluator and fielded Wasm backend. The contract is
[research/compiler-generics/SPEC.md](../../research/compiler-generics/SPEC.md).
`src/check-dispatch.bend` sends a book with generic syntax to this checker;
the original monomorphic path and its fixed assertions remain in place for
every other book.

The frontend's generic-header pin was superseded under the coordinator's
review-round-1 authorization (`5eea108`), and classify-2's pins for `Name<...>`
in parameter, return and binding types under its later authorization
(`78c4942`). [Review round 2](#review-round-2) repairs three seed-accepted
forms the generic path had exposed as Invalid. [Review round 3](#review-round-3)
repairs one more such form, and three classes of seed-rejected books that the
generic path had checked.

The mechanism is a type-expression algebra with rigid binder indices. A single
sequential substitution list instantiates later parameter domains and results.
Literal quantity meets reduce; `&2` is identity and `&0` is an absorber for
symbolic expressions. Remaining symbolic syntax stays invariant. The checked
result crosses into runtime terms through one erasure module.

Every generic family uses a boxed `[tag][live fields...]` cell. An erased marker
selects the existing fielded representation even for nullary constructors,
without adding a live slot. Closed monomorphic enums remain ordinals. Abstract
values are opaque words; their checked instantiations determine whether the
word holds an ordinal or a cell address. Each source function has one emitted
body, with erased arguments absent from its live signature.

| Independent expectations | Fixtures | Seed calls | Origin |
| --- | ---: | ---: | --- |
| Original corpus | 40 | 122 | Unchanged source, outcomes and regeneration script from the integration base |
| Two-quantity short form | 1 | 4 | Frozen before implementation in `16d5d22` |
| Compact reusable binder | 1 | 4 | Frozen before implementation in `629c51f` |
| Kind and representation boundaries | 15 | 26 | Seed probes and literal Unsupported boundaries |
| Local type-value and dispatch boundaries | 9 | 9 | Fixed before their corresponding boundary repairs |
| [Bare family names](bare-families/README.md) | 7 | 3 | Frozen in `0c4eb10` before the arity repair |
| [Value arguments](value-arguments/README.md) | 5 | 5 | Frozen in `58afc10` before the term-argument repair |
| [Empty families](empty-families/README.md) | 7 | 7 | Frozen in `cfad5c4` before the empty-datatype repair |
| [Definition references](def-references/README.md) | 7 | 5 | Frozen in `efdca4a` before the def-reference repair |
| [Type-level definition names](type-level-names/README.md) | 11 | 8 | Frozen in `d8af22d` before the definition-scope repair |
| [Marked quantity binders](marked-binders/README.md) | 9 | 3 | Frozen in `8bac386` before the parser repair |
| [Constructor pattern order](pattern-order/README.md) | 8 | 7 | Frozen in `2345731` before the pattern-order repair; binding variant `d3fe024` |
| [Token spacing](spacing/README.md) | 18 | 14 | Frozen in `8b26748` before the spacing repair |
| Total | 138 | 217 | 83 seed-valid programs and 55 seed rejections |

The original `closure-apply` and `template-twice` pins remain. Optional
`match-erased-type` and `alias-type` remain Unsupported. Five independent literal
ABI controls inspect erased parameter counts without invoking generic exports.

| Type-correct mutant | Fixed witness | Observed violation |
| --- | --- | --- |
| Skipped substitution | `box-unbox` | Rejects the valid instantiated constructor/function path |
| Erased argument kept live | `unbox` ABI | Two live arguments instead of one |
| Wrong quantity meet | `meet-not-reusable` | Accepts an invalid reusable quantity |
| Missing arity check | `type-arity` | Accepts excess type arguments |
| Bare quantity default | `bare-family-parameter` | Accepts a bare all-quantity family name |
| Term argument demoted | `value-argument-parameter` | Reports Invalid for a seed-valid `Tag<On{}>` |
| Empty family demoted | `empty-generic-absurd` | Reports Invalid for a seed-valid generic empty family |
| Empty datatype demoted | `empty-type` | Reports Invalid for a seed-valid monomorphic empty type |
| Definition reference freed | `def-reference-live` | Reports a seed-valid `one` reference Invalid free-name |
| Definition scope dropped | `definition-field-later` | Reports a seed-valid type-level definition name Invalid unknown-type |
| Marked binder as quantity | `marked-reusable-binder` | Accepts the seed-rejected `+a,` binder |
| Pattern order dropped | `later-family-parameter` | Accepts a seed-rejected pattern above its datatype |
| Quantity gap glued | `quantity-gap-argument` | Accepts the seed-rejected `& 2` |
| Meet gap glued | `meet-gap` | Accepts the seed-rejected `< & >` |
| Closing gap glued | `close-gap-parameter` | Accepts the seed-rejected `Seq<&2,Flag >` |

Each mutant is seed-typechecked and exercised in native and Bun lanes. A parser
failure, host/internal error, exhausted budget or invalid Wasm cannot count as
a semantic kill. Seed regeneration never invokes Knot or derives expectations
from emitted code.

```sh
export BEND_NO_TELEMETRY=1
python3 tests/compiler-generics/regen.py
python3 tests/compiler-generics/check.py
npm run -s gates
npm run -s gates:verify
```

The gate uses `tests/compiler-fields-wasm/compile.bend` for the fielded profile.
The default enum emitter still rejects fielded books. Node calls use the
`--profile=knot-fields-wasm-1` host adapter and only closed monomorphic enum
signatures. Generic/cell-valued exports are for compiled callers. The existing
one-page arena and exhaustion policy apply; there is no reclamation or owned
storage guarantee.

`src/types-PROOF.bend` fills 12 laws, including universal substitution composition
and the quantity meet algebra. `src/type-erasure-PROOF.bend` fills 21 laws,
including erased evaluator transitions with their one-step fuel adjustment, the
empty-family boundary, `type_level_definition`, `pattern_order` and
`spaced_quantity`. `src/check-PROOF.bend` fills `def_reference`,
`src/catalog-PROOF.bend` fills `empty_datatype`, and the frontend proof fills
`term_argument` and `marked_binder`; the gate runs the frontend, types,
erasure and catalog proof entries (the last chains the check laws).
The complete frontend proof fills the restated generic-header acceptance law,
whose parameter type touches its closing `>`.
These proofs and finite differential observations are distinct from a universal
checker-soundness or compiler-correctness theorem. The bounded proof and review
obligations are in [LAW_REVIEW.md](LAW_REVIEW.md).

Local type/quantity normalization, type-returning definitions, value-indexed
families, constructor-local type binders, live static arguments, type-variable
application, pair sugar, function types, templates, general lexicographic
descent and gaps inside the seed's glued tokens remain Unsupported. This increment covers only the documented S2 subset.
The legacy structural catalog
observer remains monomorphic and reports Unsupported for generic declarations.

The next integration step must compose this checker with the parallel modules/pattern/descent work (which
extends `generics.bend`; see the dual checker path in
[COMPILER-CAMPAIGN.md](../../docs/COMPILER-CAMPAIGN.md)), and run live Perch
semantic and style review. No package, runtime IR, evaluator or Wasm emitter
implementation changes are part of this increment.

## Review round 3

The branch merges main `90b4052` (`90feb09`: gate runner `CC`/`SDKROOT`; census
regenerated). Each confirmed finding has a seed-derived fixture frozen in its
own commit before the repair (D7):

| Finding | Frozen | Repair | Disposition |
| --- | --- | --- | --- |
| [blocking] A type-level definition named in a family field (or an earlier signature) was Invalid `unknown-type` | `d8af22d`, 11 fixtures | `287a624`: the type scope binds the book's definitions, and such a name is `Unsupported check type-level-definition` wherever it is declared; law `type_level_definition`; mutant `type-level-definition-unknown` | fixed |
| A generic constructor pattern above its datatype was Checked | `2345731`, 6 fixtures; binding variant `d3fe024`, 2 fixtures | `2e9646f`: one `visible` order predicate; a later pattern is `Invalid check unknown-constructor`; law `pattern_order`; mutant `pattern-order-forward`. The binding variant is rejected earlier, as `Invalid check unmatchable-binder`: the seed never lets a match scrutinize a local binder | fixed |
| A constructor pattern above its type (f1, and f6 in a generic-routed book) was Checked | the same corpus (`later-family-unbox`, `later-enum-generic-book`) | `2e9646f` | fixed; the purely monomorphic f7 and late-mono stay with the monomorphic checker's owner (`src/SPEC.md`) |
| Marked bare binders (`+a,`, `-a,`) were checked, evaluated and compiled | `8bac386`, 9 fixtures | `d7fba74`: only an unmarked bare binder is a quantity; a marked one is `Invalid parse parameter` at the `,`; law `marked_binder`; mutant `marked-binder-quantity` | fixed |
| `census:test` failed 73/75 on stale literals | — | `6086dfa`: `frontend_definitions` 41→47 (six generics definitions in `parse.bend`) and the recursion Wasm evidence (the two recursive generics fixtures) | fixed; these are assertion changes and need the coordinator's confirmation |

Round 3 adds no definition to `lex.bend`, `parse.bend` or `syntax.bend`, so
`frontend_definitions` stays 47; `npm run -s census:test` passes 75 of 75.
Registering `census:test` in `scripts/gates/run.py` (runner-owned) would keep
these literals from going stale silently; it is recommended, not done here.

**Token spacing (found by this round's sweep, not a confirmed finding).** The
seed lexes `&2`, the meet `<&>` and, in most lists, a closing `>` as glued
tokens. Knot's lexer splits symbols and drops spaces, so the generic parser
checked books with `& 2`, `< & >` or `Seq<&2,Flag >` that the seed rejects;
main reported them Unsupported. [The spacing corpus](spacing/README.md) was
frozen in `8b26748` (18 fixtures). The repair `4e73b6c` reports every gap
inside a glued token as `Unsupported parse spacing`, with law
`spaced_quantity` and mutants `quantity-gap-glued`, `meet-gap-glued` and
`close-gap-glued`. The seed accepts a gap before the `>` of a single-argument
list. Knot does not reproduce that position-dependent rule, so four seed-valid
fixtures, and the sweep's `t3`, moved from `Checked` (end of round 2) to
Unsupported. Main also reported them Unsupported, so this is D4-legal, but it
is a visible demotion. The restated `generic_header` law now gives its
parameter type and closing `>` touching spans. The monomorphic forms of the
class, `On {}` and `- >`, are `Checked` on main as well and stay with the
frontend's owner.

`spaced_quantity` is a parser law, but it lives in `type-erasure-LAWS.bend`
beside the other generics boundary laws. In `LAWS.bend` it would push the
frontend-laws style composition to 48,420 bytes, over its 48,000-byte limit.
That composition is now at 47,760 bytes, so the next change to
`type-parse.bend` or `LAWS.bend` will create a structural blocker unless the
group is split.

Every repair keeps D4: no program that the seed accepts becomes Invalid.
Before each repair, the native `parse` and `check` CLIs ran over every tracked
Bend file and the review probes; after it, only the targeted probes and the
new fixtures changed outcome. On the final tree the round-3 sweep (214 probes)
finds no seed-accepted program reported Invalid. Six seed-rejected probes are
still `Checked`, and main reports every one of them `Checked` too. Four are
the monomorphic pattern order case (f7 twice, fw-p7 and late-mono), and two
are the monomorphic spacing forms (ws1 and ws2).

**Hang guards.** The generics gate's fixed 60- and 120-second hang guards now
scale with `KNOT_GATE_TIMEOUT_SCALE`, as in the other gates (`f07ce14`). At
load average ~70, a direct run had passed all 138 fixtures and then timed out
on its first mutant's seed build. That change moved the gate's program hash
in the census (`005887b`).

**Gates.** Every full run of this round is reported:

| Run | Tree | Result |
| --- | --- | --- |
| [run 1](receipts/review-3/gates-run1.json) | `f07ce14`, 4 jobs, 1,293 s, load average about 35 to 50 | exit 1: 19 passed. `census` reported `accepted.json` stale, because `f07ce14` had moved the generics gate's program hash (fixed in `005887b`). `bootstrap` failed on the host error `found no clang` while building `src/compile-cli.bend`. Generics passed in 832.71 s of its 900 s wall |
| [run 2](receipts/review-3/gates.json) | `005887b`, 4 jobs, 732 s, load average about 26 to 37 | exit 0: 21 of 21 passed |

Run 2 counts for generics are 138 fixtures, 217 seed calls, 324 evaluator and
324 Node agreements, 600 negative phase observations, 200 preserved
artifacts, 38 byte-identical module pairs, 10 ABI arity observations, 4 proof
entries and 15 mutants (30 lane kills). Classification has 17 fixtures and 7
mutants. `receipts/generics.json` is run 2's normalized receipt, and its 208
input hashes match the committed files. Of 89 regenerated receipts, 64 are
identical, 9 volatile-only and 16 semantic. The semantic ones are this gate's
receipt and shared receipts whose source hashes changed; the shared ones are
left for the coordinator. `npm run -s gates:verify` runs 18 tests OK.
`census --check` exits 0, and `census:test` passes 75 of 75.

The generics gate's wall time is the long pole under campaign load: 479.68 s
in run 2 and 832.71 s in run 1, against the runner's 900 s default. If the
load stays high, the coordinator should expect to need `--jobs 2` or a quieter
host.

**Style preflight (offline, 0 provider requests).** Manifest mode reports 24
groups, 0 truncated units, 24 of 24 compositions available and 0 structural
blockers. Changed groups (units / composition bytes): frontend-parsing
72 / 35,157, frontend-laws 114 / 47,760, generic-type-parsing 25 / 12,312 and
generic-erasure-laws 42 / 23,537. Targets mode over the four changed sources
(`type-parse.bend`, `LAWS.bend`, `type-erasure-LAWS.bend`,
`type-erasure-PROOF.bend`) reports 84 units and 13 truncated contexts. None of
those is a new declaration; the restated `generic_header` was already
truncated at round 0. That cross-group composition is unavailable. No style
rating is claimed.

The round-0 summaries `receipts/gates.json`,
`receipts/gates-resource-exhaustion.json` and
`receipts/preflight-before-dispatch.json` remain historical evidence.

## Review round 2

The branch merges main `481bb31` (`f7c98b9`; documentation only). Each
confirmed finding has a seed-derived fixture frozen in its own commit before
the repair (D7):

| Finding | Frozen | Repair | Disposition |
| --- | --- | --- | --- |
| [blocking] `Tag<On{}>` was Invalid `type-argument-separator` | `58afc10`, 5 fixtures | `447be7d`: a type argument followed by anything but `,` or `>` is `Unsupported parse term-argument`; law `term_argument`; mutant `term-argument-invalid` | fixed |
| Empty datatypes were Invalid `empty-datatype` | `cfad5c4`, 7 fixtures | `88e204b`: both catalogs report Unsupported; laws `empty_datatype` and `empty_family`; mutants `empty-family-invalid`, `empty-datatype-invalid` | fixed |
| A bare zero-arity definition was Invalid `free-name` | `efdca4a`, 7 fixtures | `c52929b`: shared `term_name` reports `Unsupported check def-reference`; law `def_reference`; mutant `def-reference-free` | fixed |
| Classification mutants deleted, not retargeted | existing witnesses | `d3cee9f`: `parameter-application-invalid` retargeted to `function-parameter`; `type-expression-invalid` on the three after-prefix twins; two route mutants on `application-return` and `application-binding`: 7 mutants (main had 6) | fixed |
| Stale `receipts/generics.json` | — | `6cc4bf0`: regenerated at the round-2 tree, normalized like round 0; `0d2b41f` regenerates the census the classification change staled | fixed |
| Host `found no clang` flakes under load | — | none in this increment | disputed as a generics defect, see below |

Every repair keeps D4 in the same direction: a seed-accepted program that the
generic path now reached is reported Unsupported, never Invalid. Before each
repair, the native `parse` and `check` CLIs ran over every tracked Bend file
and the review's probes; after it, only the targeted probes and the new
fixtures changed outcome.

**Gates.** `npm run -s gates` on `0d2b41f` (4 jobs, 445 s, load about 13 to 21):
exit 0, 21 of 21 passed ([summary](receipts/review-2/gates.json)). Generics:
92 fixtures, 185 seed calls, 284 evaluator and 284 Node agreements, 384
negative phase observations, 128 preserved artifacts, 28 byte-identical module
pairs, 10 ABI arity observations, 4 proof entries, 9 mutants (18 lane kills).
Classification: 17 fixtures, 7 mutants on 9 witnesses. `npm run -s
gates:verify`: 18 tests OK. Of 89 regenerated receipts, 64 are identical, 10
volatile-only (including this gate's committed receipt) and 15 semantic:
shared receipts whose source hashes changed, left for the coordinator.

**Host `found no clang`.** The failure is the seed's clang discovery returning
empty output under campaign load. `GATES.md` records the same class at the
campaign base, and no source in this increment touches it. The runner
(`scripts/gates/`) belongs to its own owner, and its documented contract is to
report such failures, never retry or relabel them. This round reports every
full run it made. The owner's options are the review's: a single retry on
that exact stderr, recorded in the summary, or capturing `spawnSync`'s errno
around `cc_find`.

**Style preflight (offline, 0 provider requests).** Manifest mode: 24 groups,
1,202 units, 0 truncated, 24 of 24 compositions available, 0 structural
blockers. Changed groups (units / composition bytes): frontend-laws 108 /
44,776, checker-laws 42 / 18,931, catalog-laws 44 / 26,089,
generic-erasure-laws 36 / 18,390, generic-type-parsing 21 / 10,812,
generic-catalog 76 / 31,119, generic-checking 65 / 39,414, checking 71 /
36,921, scope-patterns 101 / 30,982, catalog 65 / 18,845. Targets mode over the
14 changed sources reports 351 declarations, 55 truncated contexts (none of
them a new or changed declaration except the pre-existing `check.bend::run`
and `generics.bend::run`), and an unavailable cross-group composition. No
style rating is claimed.

**New observation (repaired in [round 3](#review-round-3)).** The seed
resolves a constructor pattern only against datatypes declared earlier in the
file: `case On{}:` above `type Flag` fails with `a declared constructor
(unknown: On)`. Knot accepted such books (`Checked`) in both checkers. Main
already accepts the monomorphic form; the generic form (`case Box{value}`
above a generic `Box`) was `Unsupported parse` on main and `Checked` at the
end of round 2.

## Review round 1

The branch merges main (`cac8dd2`) and fixes the confirmed findings:

- the authorized `generic` pin supersession (`5eea108`);
- bare family names (`0c4eb10` expectations, `feeea07` repair and mutant);
- the dispatch moved to `src/check-dispatch.bend`, shared `term_name`, the
  generics contract in its own task file and the manifest closures (`5f86882`);
- the dual checker path recorded with its convergence plan (`52c9e8a`).

**Blocker (resolved by the authorized supersession `78c4942`).** Main's classify-2 pins `Name<...>` in parameter, return and binding
types as Unsupported. The generic parser accepts them, so six classification
cases, three classification-gate mutants and the laws `return_type_application`
and `binding_type_application` conflict. Because every proof entry chains
through `src/PROOF.bend`, the committed tree's `npm run -s gates` stops nine
gates at their proof step:

| Run | Result |
| --- | --- |
| Committed tree `2fa6e2c`, 4 jobs (232 s) | exit 1: 9 passed (census, lint:verify, owned-store, flat-store, perch-context, io-host, io-abi-2, bootstrap, selfhost); frontend, checker, structural, fields, wasm, recursion, fields-wasm, classification and generics failed at their proof entry; 3 trust gates blocked |
| `2fa6e2c` plus the proposal, 4 jobs (328 s) | exit 0: 21 of 21 passed |
| `52c9e8a` plus the proposal, `--jobs 1` (854 s, load about 15) | exit 0: 21 of 21 passed |

Runner summaries: [committed tree](receipts/review-1/gates-tree.json),
[proposal, 4 jobs](receipts/review-1/gates-proposal.json) and
[proposal, 1 job](receipts/review-1/gates-proposal-jobs1.json).

The proposal (not committed; it changes classify-2 assertions and needs the
coordinator's authorization) gives the three seed-accepted application cases
phase expectations like `generic`, pins the after-prefix twins at
`Unsupported parse type-expression`, retires the three classification-gate
mutants with their anchors, restates `return_type_application` as the
typed-result transition and retires `binding_type_application`.
[CLASSIFICATION.md](../subsets/CLASSIFICATION.md) lists the derivations.

With the proposal applied, the generics gate reports 73 fixtures, 168 seed
calls, 284 evaluator and 284 Node agreements, 270 negative phase observations,
90 preserved artifacts, 28 byte-identical module pairs, 10 ABI arity
observations, 3 proof entries and 5 mutants killed in both lanes. The frontend
reports 30 classification fixtures in two lanes, 7 classification mutants and
180 downstream phase observations. `npm run -s gates:verify` passes 18 tests.

**Build cost.** Linking the second checker roughly doubles the generated code.
Sequential seed builds at load about 7 (main `cc9f2fd` → branch):

| CLI | Generated C (bytes) | Native build, real s |
| --- | ---: | ---: |
| parse | 1,240,306 → 1,838,731 | 2.8 → 3.8 |
| check | 2,497,614 → 4,824,594 | 5.5 → 11.2 |
| eval | 2,760,021 → 5,071,593 | 5.6 → 11.0 |
| compile | 3,413,614 → 5,733,438 | 7.2 → 11.9 |

Under main's default `KNOT_GATE_TIMEOUT_SCALE=4` the default four-job run
passes. The convergence plan (one checker) is the lever that removes the
duplicate code; no budget was changed.

**Style preflight (offline, 0 provider requests).** Full manifest: 24 groups,
1,196 units, 0 truncated units, 24 of 24 compositions available, 0 structural
blockers (main: 17 groups, 957 units, 0 blockers). The seven generic groups use
the 3,731-byte generics contract as their task. Per group, main `cc9f2fd` →
branch (units / composition bytes / structural blockers):

| Group | main units / composition bytes / blockers | branch units / composition bytes / blockers | branch composition |
| --- | --- | --- | --- |
| syntax-core | 33 / 5,156 / 0 | 33 / 5,698 / 0 | available |
| frontend-lexing | 27 / 7,112 / 0 | 27 / 7,654 / 0 | available |
| frontend-parsing | 41 / 20,432 / 0 | 68 / 33,502 / 0 | available |
| diagnostics | 45 / 11,027 / 0 | 45 / 12,813 / 0 | available |
| catalog | 65 / 17,844 / 0 | 65 / 18,698 / 0 | available |
| scope-patterns | 99 / 29,152 / 0 | 101 / 30,639 / 0 | available |
| checking | 134 / 47,903 / 0 | 71 / 36,665 / 0 | available |
| evaluation | 63 / 18,063 / 0 | 63 / 18,605 / 0 | available |
| wasm-codec | 30 / 6,317 / 0 | 30 / 6,859 / 0 | available |
| wasm-emission | 89 / 27,367 / 0 | 89 / 27,909 / 0 | available |
| driver-pipeline | 51 / 23,219 / 0 | 51 / 27,934 / 0 | available |
| frontend-laws | 81 / 29,806 / 0 | 108 / 43,224 / 0 | available |
| checker-laws | 38 / 15,598 / 0 | 40 / 17,455 / 0 | available |
| runtime-laws | 55 / 25,090 / 0 | 55 / 26,210 / 0 | available |
| catalog-laws | 42 / 24,051 / 0 | 42 / 25,587 / 0 | available |
| fields-laws | 32 / 19,604 / 0 | 32 / 20,724 / 0 | available |
| recursion-laws | 32 / 17,292 / 0 | 32 / 18,412 / 0 | available |
| generic-type-algebra | new | 35 / 10,322 / 0 | available |
| generic-type-parsing | new | 21 / 10,657 / 0 | available |
| generic-catalog | new | 76 / 31,035 / 0 | available |
| generic-checking | new | 65 / 39,301 / 0 | available |
| generic-erasure | new | 12 / 7,521 / 0 | available |
| generic-erasure-laws | new | 34 / 17,746 / 0 | available |
| check-dispatch | new | 1 / 9,277 / 0 | available |

Targets mode over this round's seven changed sources reports 227
declarations, 58 truncated contexts and an unavailable 158,052-byte
composition; `types.bend::Expr`, `syntax.bend::Token` and
`type-parse.bend::invalid` still truncate in a 20-file targets run. The
per-group manifest run is the qualifying form. No style rating is claimed.

On the committed tree, `src/types-PROOF.bend` and
`src/type-erasure-PROOF.bend` print `All terms check.` when run directly;
only `src/PROOF.bend` fails, on the two classify-2 laws. The selfhost need
`generics` is still `available: false`: all 30 cases that need it also need
`base`, so the flip is behavior-neutral and is owed when this increment lands.

## Round 0 verification (`f39ba7e`)

The [scratch-run summary](receipts/gates.json) records **14 of 15 gates passed**;
`npm run -s gates` exits 1 on the retained frontend pin. Before that failure,
the frontend completed 14 reference fixtures, 28 parser-lane observations,
24 boundaries and four mutants. Its classification loop stops on the first
generic case, so its remaining classification checks are not reported as passes.

| Gate | Exact completed coverage |
| --- | --- |
| Frontend — failed | 14 reference fixtures; 28 parser observations; 24 boundaries; 4 mutants; then obsolete generic pin |
| Checker | 49 fixtures; 98 observations; 10 depth probes; 16 catalog-bound observations; 7 mutants |
| Structural | 16 fixtures; 64 observations; 4 boundary pairs; 7 mutants |
| Fields | 40 fixtures; 240 observations; 36 budget probes; 6 host probes; 12 level/inspection observations; 9 mutants |
| Wasm | 25 fixtures; 90 reference calls in 2 lanes; 64 rejection pairs; 44 boundaries; 7 mutants |
| Wasm trust | 3 entries; 0 proof holes |
| Fields trust | 4 entries; 0 proof holes |
| Structural trust | 2 entries; 0 proof holes |
| Owned-store | 3,532 cases in 2 lanes; 15 literal witnesses; 6 mutants |
| Flat-store | Per lane: 13,621 observations, 3,534 instances, 2 installed boundary states, 7 lifecycle checks; 2 lanes; 9 mutants |
| Recursion | 19 fixtures; 114 phase observations; 4 fuel probes; 3 mutants |
| Fields Wasm | 8 fixtures; 32 seed calls; 64 evaluator and 64 Node observations; 50 frozen enum-byte checks; 30 boundaries; 4 mutants in both lanes |
| Census | 39 source files; 677 declarations; 41 feature classes |
| Lint verification | 127 tests; 8 law-rule wiring controls |
| Generics | 66 fixtures; 165 seed calls; 278 evaluator and 278 Node agreements; 234 negative-phase observations; 78 preserved artifacts; 27 byte-identical module pairs; 10 ABI arity observations; 3 proof entries; 4 mutants / 8 lane kills |

At round 0 the generic receipt had 27 agreed fixtures, 23 required
rejections and 16 Unsupported fixtures; round 2 refreshed it (see below). Across the two lanes, checking records
54 successes, 40 Invalid outcomes and 38 Unsupported outcomes. No exhaustion,
host failure or internal failure satisfies a fixture. All three complete proof
entries print `All terms check.` The gate wrapper's independent `gates:verify`
run passes 18 tests, including its six semantic mutants.

The scratch runner classified 81 artifacts: 63 identical, 8 volatile-only and
10 semantic. The semantic group contains changed compiler/source hashes and
the retained frontend failure. Existing gates' receipts
were left unchanged for coordinator refresh. The [census approval summary](receipts/census-approval.txt)
is also included verbatim in the implementation commit message.

A preceding parallel run exceeded existing build and harness timeouts. Its
[resource-exhaustion summary](receipts/gates-resource-exhaustion.json) remains
as failed-run evidence. The final run uses `npm run -s gates -- --jobs 1` with
the same assertions and time budgets.

The [classification transition](receipts/classification-transition.json) records
fresh Bun observations of the old generic fixture: parse/check/eval succeed and
eval returns `Box{On{}}`; the default enum compiler reports
`Unsupported check constructor-fields` and preserves the old output. Reconciling
the old harness requires phase-specific expectations, not one shared rejection
pin. The [legacy catalog controls](receipts/catalog-boundaries.json) retain two
Bun Unsupported observations at its monomorphic inspection boundary.

Final [offline preflight](receipts/preflight.json): 386 declarations in 16 files,
zero provider requests, 58 truncated contexts (6 caller/byte, 23 file, 29 helper
limits). These same 58 declarations cannot receive the supporting-role exemption.
The combined composition is unavailable: 195,340 bytes against 48,000, with
60 collaborators outside the group and 51 nonlocal imports. Its task is present
(4,152 bytes). Exit 3 records 59 structural blockers. Compression, Delight,
memetic identity, Anticipation and Payoff remain unreviewed; no style pass or
semantic Perch review is claimed. The earlier preflight remains as historical
evidence under `preflight-before-dispatch.json`.
