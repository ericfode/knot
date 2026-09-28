# Boundary pin review: executor mapping, pending coordinator review

The [kind and representation boundaries](boundaries/README.md) (15 fixtures)
and the [dispatch boundaries](dispatch-boundaries/README.md) (9 fixtures) were
added in one commit, `f39ba7e`. That commit also added the generic checker
(`src/generics.bend`, `generic-catalog.bend`, `types.bend`, `type-parse.bend`
and `type-erasure.bend`), the `generics` section of `src/CONTRACT.json` and
the matching `src/SPEC.md` text. Git history therefore cannot show that these
24 expectations preceded the checker. Their Knot pins are phase/code strings
that the implementer chose, and the checker in the same commit produces them.
Every corpus added after `f39ba7e` was frozen in its own commit before its
repair (see the [README](README.md) table).

The seed side does not depend on Knot, and it reproduces:

```sh
$ BEND_NO_TELEMETRY=1 python3 tests/compiler-generics/boundaries/regen.py
regen: PASS 15 fixtures (12 seed-valid, 3 seed-invalid), 26 entry calls, identical to expectations.json
$ BEND_NO_TELEMETRY=1 python3 tests/compiler-generics/dispatch-boundaries/regen.py
regen: PASS 9 fixtures (7 seed-valid, 2 seed-invalid), 9 entry calls, identical to expectations.json
```

This file maps each Knot pin to its contract clause. The executor wrote it
(review round 4). It is not an independent review. The contract clauses cited
under "Contract" (`src/CONTRACT.json` `generics` and `src/SPEC.md`, as of
`f39ba7e` unless stated) were written in the same commit as the checker. For that
reason, each row also cites a source that predates `f39ba7e`, where one
exists:

- **[F]** `tests/compiler-generics/FIXTURES.md` at `629c51f`. It was written
  before implementation and independently of the implementer. It says that
  `type-level-definition` and `live-type-parameter` are "not on the increment 6
  ladder". For rules that belong to increment 6 but have no existing code, the
  implementer chooses the code ("class-only pins").
- **[L]** The milestone ladder in `docs/COMPILER-CAMPAIGN.md`, row 6:
  "Generics and quantity arguments: erasure and a uniform boxed
  representation".
- **[B]** The native checker built from `629c51f` (the integration base).
  Its outcome on the same fixture is shown for comparison.

**Mapping** grades each pin:

- *seed-derived*: Knot's pin follows from the seed's outcome and the
  requirement kind, not from a code the implementer chose.
- *exact*: a contract clause names the form, and an earlier source puts the
  form outside increment 6.
- *code-only*: the rule's status predates `f39ba7e`, but the code string does
  not.
- *loose*: no contract clause names the form exactly.

## Kind and representation boundaries (`boundaries/`)

| Fixture | Seed | Knot pin | [B] `629c51f` | Contract (`f39ba7e`) | Earlier source | Mapping |
| --- | --- | --- | --- | --- | --- | --- |
| `meet-right-identity`, `meet-left-identity`, `meet-right-zero`, `meet-left-zero` | valid | `agree` | Unsupported parse generic-datatype | `quantity_semantics.meet` | [L]; the increment task's `Kind(q)` meets | seed-derived |
| `prefix-overrides-quantity`, `prefix-overrides-undefined` | valid | `agree` | Unsupported parse generic-datatype | `quantity_semantics.plus_prefix` | the task's `+` binder over a compact family | seed-derived |
| `monomorphic-kind` | valid | `agree` | Unsupported parse kind | `accepted`: `Kind(q)` | [L] | seed-derived |
| `prefix-forward-explicit`, `prefix-forward-short` | rejects: "a quantified datatype after +" | exit 2, `Invalid check quantity-prefix` | Unsupported parse parameter-type | `quantity_semantics.short_form`: "after the family definition" | [F] `forward-short-form`, a class-only pin (exit 2) | code-only |
| `prefix-needs-quantifier` | rejects: same reason | exit 2, `Invalid check quantity-prefix` | Unsupported parse generic-datatype | `plus_prefix` | [F] class-only convention | code-only |
| `boxed-live-type`, `boxed-live-quant` | valid | `Unsupported check live-type-argument` | Unsupported parse generic-datatype | `unsupported`: "instantiated live type or quantity arguments" | [F] `live-type-parameter` is off the increment 6 ladder | exact |
| `type-valued-result` | valid | `Unsupported check type-level-definition` | **Invalid** parse function-result | `unsupported`: "type-returning definitions and aliases" | [F] `type-level-definition` is off the ladder | exact |
| `value-indexed-family` | valid | `Unsupported check generic-value-parameter` | Unsupported parse generic-datatype | `unsupported`: "value-indexed families" | [L]: generics and quantity arguments; S2's dependent fields are not on row 6 | exact |
| `constructor-local-type` | valid | `Unsupported parse parameter-type` | Unsupported parse generic-datatype | `unsupported`: "constructor-local type parameters" | [B]: the monomorphic form `Box{-B: Type, value: B}` is `Unsupported parse parameter-type` at `Type` on the base | exact |

## Dispatch boundaries (`dispatch-boundaries/`)

| Fixture | Seed | Knot pin | [B] `629c51f` | Contract (`f39ba7e`) | Earlier source | Mapping |
| --- | --- | --- | --- | --- | --- | --- |
| `nested-erased-type` (`-Alias : Type = Flag` in a match arm) | valid | `Unsupported check type-level-binding` | Unsupported parse binding-type | `unsupported`: "local type or quantity bindings" | [F] `type-level-definition` is off the ladder; [B] already Unsupported | exact |
| `local-erased-quantity` (`-q : Quant = &2`) | valid | `Unsupported check type-level-binding` | Unsupported parse binding-type | same | [B] already Unsupported | exact |
| `generic-local-erased-type` | valid | `Unsupported check type-level-binding` | Unsupported parse generic-datatype | same | [F] | exact |
| `inferred-erased-type` (`-Alias = A`) | valid | `Unsupported check type-level-binding` | Unsupported parse parameter-type | same | [F] | exact |
| `unannotated-erased-quantity` (`-q = &2`) | valid | `Unsupported check type-level-term` | Unsupported parse term-form | SPEC: "Both checker paths recognize local type values without treating them as free variables"; no `unsupported` entry names a quantity term | [B] already Unsupported | loose |
| `unannotated-erased-type` (`-Alias = Flag`) | valid | `Unsupported check type-level-term` | **Invalid** check free-name | the same SPEC sentence; no `unsupported` entry names a datatype used as a term | none | loose |
| `generic-unannotated-erased-type` | valid | `Unsupported check type-level-term` | Unsupported parse generic-datatype | the same SPEC sentence | none | loose |
| `empty-type-application` (`Flag<>`) | rejects: "a term" | exit 2, `Invalid parse type-arguments` | Unsupported parse parameter-type | SPEC: "Empty type-argument lists are Invalid, matching the seed" | none | code-only |
| `monomorphic-type-application` (`Flag<Flag>` in a monomorphic field) | rejects: "Flag with 0 parameters" | exit 3, `Unsupported check type-expression` | Unsupported parse parameter-type | none at `f39ba7e`; `dispatch` (added in `5f86882`) keeps the monomorphic checker, which does not check type expressions, for a book without generic syntax | [B] already Unsupported | code-only |

## D4 consistency

- No seed-valid fixture is pinned Invalid.
- No seed-invalid fixture may be `Checked` or `Built`. Both the `reject` and
  the `unsupported` requirement enforce this.
- Two base outcomes violated D4. The base reported `type-valued-result`
  Invalid parse function-result and `unannotated-erased-type` Invalid check
  free-name, although the seed accepts both. The pins turn both into
  Unsupported.
- `monomorphic-type-application` is seed-invalid but pinned Unsupported, not
  Invalid. This is D4-legal but imprecise: the monomorphic checker recognizes
  the applied field type without checking it. Its base outcome was Unsupported
  too.
- The three `quantity-prefix` pins and `type-arguments` pin a code where
  [F]'s convention for implementer-chosen rules pins only the exit class. The
  coordinator may accept these codes or relax them to exit 2.

## Open for the coordinator

For each row, confirm that the pin is a contract boundary and not a
restatement of Knot's output. Pay particular attention to the three *loose*
`type-level-term` pins and the four *code-only* pins, and record the result
in this file. Relevant evidence for the dispatch corpus: an ignored local
snapshot (`.local/generics/dispatch-before-ninth.json`, file time
2026-09-27 19:25) holds the first eight dispatch cases byte-identical to the
committed ones, without `inferred-erased-type`. It is not in git. It neither
proves the ordering nor verifies any pin, and nothing here relies on it.
