# Generics precheck round 6

Base: `41447157`. Seed: Bend 2.0.29, `574b6d39a235b539eb19a5c532993a0abb3d11ad`.
The ten complete reported programs were recovered by their SHA-256 identities
from the frozen registry and fixed generator. Their exact bytes and seed
observations are in [prechecks/expectations.json](prechecks/expectations.json),
frozen before compiler edits in `412f649e`. No earlier expectation changed.

## Executor dispositions

| Condition fingerprint | Program SHA-256 prefix | Disposition and evidence |
| --- | --- | --- |
| `9d966b7865cffb5b0520` | `09ad0347501eff04` | Fixed. Parse observation is `Invalid parse unknown-constructor 102:105:7:9`; seed parse rejects Off at 102. Generic checking retains `Invalid check unknown-constructor` at the same name. |
| `6d5405cb9af62a120a6c` | `267a27fbe4d062a4` | Fixed. Parse observation is `Invalid parse unknown-constructor 56:59:3:9`; seed parse rejects Box at 56. Its declared-before-pattern twin parses, checks and runs to On{}. |
| `5476608ab985012e86fd` | `1d569d47256a77f9` | Fixed. The `~` token is `Invalid parse type-expression 103:104:9:11`, matching the seed's rejected term token. |
| `7f39d4e1585446c0d329` | `5605d9115aaf775e` | Fixed. The second initializer `=` is `Invalid parse expected-term 106:107:9:14`, matching the seed's rejected term token. |
| `d284cc476f5dc47540ae`, `547d92b6d8a356b8e11d` | `443aca1528c18111` | Fixed. The multiline header parses. Check/eval/compile reach the independent `Unsupported check def-reference 168:172:13:14` body boundary; they never report Invalid for layout. Three closed Flag controls also check, evaluate and execute in Wasm. |
| `61d4c9784682a189d345`, `5ddb3eb23c17c9de47b6` | `095b335753e43c94` | Disputed diagnostic-shape finding. `Invalid\tparse\texpected-:\t96:97:8:21` has exactly four TSV fields, an Invalid/exit-2 pair, no control character inside a field, and the rejected `>` span. The suite's `[a-z0-9-]+` restriction on the code is stronger than its stated four-field contract. The existing classification pin `Invalid\tparse\texpected-:\t81:82:6:10` must stay unchanged. |
| `2479f63e20371fb1bd9e`, `3243ea49e491d4a71e20` | `034f6b0a8ed661ef`, `299c7947c7d7a981` | Disputed premature-unsupported findings. `Name<` is already recognized before the diagnostic's `:` token. `034f...` is exactly the coordinator-authorized `application-return-after-prefix` pin (78c4942), with its restored classifier mutant (d3cee9f). The same type grammar covers `299c...`. Changing it to Invalid would violate that frozen expectation and its mutation control. The SPEC prefix-only table now names this existing policy. |
| `c98eec3a22494b9f0201`, `47be583c3da6e599c04c` | `3a57659eece1bf1d`, `66acbfe944f49488` | Disputed premature-unsupported findings. The adjacency recognizer has already read the name and detects its gap before `{`; its diagnostic locates the second token. The seed instead completes a bare variable and rejects the brace as a new declaration. Equal error offsets do not imply equal recognized prefixes. Seven existing D7 token-gap pins and the filled `spaced_term_token` law require Unsupported. Neither new probe can check, evaluate or emit. Their glued twins both check on the seed. |

The supplied message ends with an incomplete additional condition. Its visible
diagnostic is the same `Unsupported parse type-expression 91:92:8:16` as
`299c...`; the full matching program is included in the replay. No unseen
fingerprint or disposition is invented.

The two disputed refusal policies are documented as prefix-only, including
the distinction between a recognized prefix and the diagnostic token. This is
a preservation of existing authorized pins, not a claim that the seed accepts
the rejected complete programs. A future coordinator amendment may make the
detached-brace vocabulary more precise, following its separate modules ruling;
it requires a seed-citing pin amendment, outside this frozen-expectation fix.

## Mechanism and proof boundary

`parse-order.bend` records constructor declaration spans. A pattern name sees
only a matching declaration at an earlier source offset, independently of AST
list order. This preserves the frozen AST-sequence mutant's observation.
Forward term constructors remain
available. The parse CLI applies this check before rendering Parsed; the raw
AST builder and the checker's existing generic validation retain their separate
roles and diagnostics. The inherited monomorphic checker residual is unchanged.

Three filled laws cover the registered/unregistered pattern guard and zero
traversal budget. Their domains have registered and unregistered fixture
witnesses. They do not prove general parser soundness, traversal refinement,
constructor arity, or the monomorphic checker's declaration-order contract.
Five new type-correct semantic mutants restore the reported wrong outcomes;
both parse-order mutants have the two late-pattern witnesses. Earlier laws, proofs,
mutants and fixture requirements remain required.

The reading hypothesis is explicit declaration state and one bounded traversal,
with symmetric pattern guard laws. Compression, Delight, memetic identity,
Anticipation and Payoff remain unreviewed: no numeric score or automatic style
pass is claimed. Live semantic/style review remains coordinator-only.

## Verification

The focused native/Bun replay passes 13 frozen parser observations, 13 seed
checks and 3 seed executions. It checks 104 compiler phase observations,
preserves 20 refused artifacts, agrees on 6 evaluator and 6 Wasm calls, and
emits 3 byte-identical module pairs. The complete new proof entry and the
existing frontend proof entry both print `All terms check.`

The classification gate passes its unchanged 17 fixtures and 7 mutants on
9 witnesses. An initial direct frontend gate omitted the documented timeout
scale and exhausted its 30-second native-build guard under load; its failure
is retained in `.local/generics/precheck-6/frontend.log`. Scaled execution and
the full runner determine acceptance, not that exhausted attempt.

The final offline manifest preflight is recorded with the full gate run. The
syntax approval adds only the three order-check modules and the
parse CLI's explicit import/callback. The census remains at 48 definitions in
the three frozen frontend files; no census test expectation is amended.

Full gate counts and final measured evidence are recorded in
[PRECHECK-GATES.md](PRECHECK-GATES.md) after execution.
