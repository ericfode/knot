# Supplied C1 conditions — parameter-tail repair

Starting head: `68fef116`. The inherited accepted implementation and receipts
are preserved. Nine controls were independently frozen in `3ed1df52` (D7),
before changing compiler code. Earlier frozen sources, expectations, values,
laws and required mutants remain unchanged.

## Executor dispositions

| Supplied fingerprints | Disposition | Evidence |
| --- | --- | --- |
| `a7aecbe6abd1b177f80b`, `7ba3d894773ad2817ea6` | Confirmed and fixed | Exact source hashes `4ce0f6cf470fb3922e9c7da0b96fd1731352503b0b1984f40ee891f6c0030ffc` and `4dc786a9c0d9bf308127a53d443fc548c0832f092e0be43ccb8bb6b403ed0a6b`. The seed's `parse_tele` rejects a non-leading `~` after skipping layout, at offsets 98 and 110. Knot's existing comma-tail guard now tests `S.skip_lines(t)` and reports Invalid parse parameter at `98:99:9:2` / `110:111:10:2` in both parse and check lanes. |
| `2479f63e20371fb1bd9e`, `3243ea49e491d4a71e20`, `e7e4004ce37fce303e1b` | Disputed | SHA prefixes `034f6b0a8ed661ef`, `299c7947c7d7a981`, `7b289f0aa74d83ea6`. The recognized prefix is `Name<`, before the diagnostic's `:` or `=` token. `src/SPEC.md` already lists this exact type-expression prefix-only rule. The first probe is also the separately authorized `application-return-after-prefix` pin and its required mutation witness. C1 equates the diagnostic span with the recognition span; source offsets alone do not establish that equivalence. All probes remain refused and preserve compilation artifacts. |
| `c98eec3a22494b9f0201`, `47be583c3da6e599c04c` | Disputed | SHA prefixes `3a57659eece1bf1d`, `66acbfe944f49488`. The adjacency rule reads a name before locating its detached brace. The seed instead finishes a bare variable and rejects the brace as a new declaration. Equal diagnostic offsets describe different completed productions. The SPEC prefix table, seven existing token-gap pins and the filled `spaced_term_token` law require the retained Unsupported refusal. The coordinator's modules detached-brace vocabulary amendment is a separate owner action. |
| `61d4c9784682a189d345`, `5ddb3eb23c17c9de47b6`, `0f32458d73d3e58df568`, `5fee6563bd061837ffcf`, visible trailing `00546995d6643017…` | Disputed | SHA prefixes `095b335753e43c94`, `6cdb9f1ec3bf7740`, `9bf0f314195f2a1f`. Every observed Invalid diagnostic has four TSV fields, exit 2, a nonempty code without control characters and a four-number span. A colon in `expected-:` is ordinary field content. C1's `[a-z0-9-]+` code regex is stronger than its stated TSV contract and rejects the existing frozen `expected-:` classification diagnostic. Both lanes retain the original spans `96:97:8:21`, `93:94:8:18`, `617:618:42:15`. |
| `48be3d3057909f734efb` | Disputed | Exact hash `8f78e510562ae976e93621cb8b8a268f72982db988324552b676ab6971b436f1`. Fresh `seed-value.ts` observation is `{constructor:"Nil",arity:0,display:"[]"}`. Knot prints `Evaluated\t1\t0\tNil{}`, the same constructor and the unchanged classification CLI pin. Comparing two renderers' text is not a value comparison. The boxed Wasm validates and is byte-identical between builds; a cell address is not counted as agreement with an enum ordinal. |

The final supplied condition is truncated. Its visible fingerprint, complete
source hash and diagnostic match the existing frozen split-pattern probe, which
is replayed in full. No unseen condition or fingerprint is invented. These
disputes retain original contract observations; they are not a clean C1 result
or a waiver of deterministic acceptance.

## Mechanism and verification

The change applies the existing layout primitive to one existing classification
guard and its error location. No new parser mode/helper or capability is added.
A bare erased quantity binder also ends the leading template region. Leading
templates still stop recognition, and expression-argument layout is unchanged.

`nonleading_template_layout` quantifies over fuel, the already parsed head,
comma/newline position, marker position and arbitrary suffix. Its complete proof
establishes the exact Invalid boundary after a newline; the original
`nonleading_template_binder` law remains unchanged. This is a boundary theorem,
not general parser soundness. All D21 obligations remain required.

Fresh focused verification passes all nine complete proof entries and all 60
precheck controls in both native and Bun builds. It records 60 seed parses,
60 seed checks, 27 seed runs, 480 compiler phase observations, 68 preserved
artifacts, 52 evaluator agreements, 48 actual enum Wasm agreements, 26
byte-identical module pairs, four boxed validations and one raw seed constructor
observation. The new type-correct `template-tail-layout-unguarded` mutant
restores the false Unsupported on five frozen witnesses in each lane.
Measured focused wall time: 70.167391 seconds. Baseline observations and the
full focused evidence remain in ignored `.local/generics/precheck-8/`.

The census approval adds only the new law and its fill, with no new syntax
classes, imports or frontend helper. Inventory: 51 files, 758 declarations,
41 classes and the unchanged 49 frontend definitions. Census controls pass
75/75. Offline manifest preflight has 29 complete groups, 1,269 units and
51 files, with all compositions available, zero truncated units/blockers and
zero provider requests/responses. The reading hypothesis is one consistent
layout boundary for the existing leading/non-leading distinction. Compression,
Delight, memetic identity, Anticipation and Payoff each remain unreviewed.

Full committed-head acceptance is recorded in [PRECHECK-8-GATES.md](PRECHECK-8-GATES.md):
`npm run -s gates` on `01ab7834` exits 0; all 21 gates pass. The owned gate
retains 148 main fixtures and now kills 37 type-correct mutants in both lanes,
with nine proof entries and all 60 prechecks passing. All 307 owned input
hashes match; the normalized owned receipt and census metadata are refreshed.
Fresh C1 covers 923 programs, removes both fixed fingerprints and retains
exactly the 26 earlier dispute/notice fingerprints. It remains partial, exit 3.
Closures reconciliation, assertion/pin rulings, shared receipt refresh, live
review and integration retain their existing coordinator owners.

## Existing mutation anchor

The first full-suite run on `b09e0a99` found a stale textual anchor in the
classification gate's existing `nonleading-template` mutant. The gate refused
to run that mutant; this was not a semantic kill or a passing classification
gate. Its anchor is updated to the same normalized guard and still replaced
by `False{}`. The original `template-nonleading` witness, fixed seed output,
expected Invalid diagnostic, wrong Unsupported diagnostic and all seven
required mutants remain unchanged. Focused classification verification passes
17 frozen seed outputs, 17 parse observations and seven type-correct mutants
on nine witnesses. Its receipt stays in ignored `.local/generics/precheck-8/`.
No shared receipt is refreshed by the focused invocation.
