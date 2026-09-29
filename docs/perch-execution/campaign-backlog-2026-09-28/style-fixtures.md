# Fixture style review (rubric v8, Jev `jev-1.13.0`)

Live `npm run lint:style -- --live --incremental --context=interfaces-v1 [--task=…] <files>` per suite directory, run from the main checkout on 2026-09-28 (main `a6367eb9`). Each suite is one explicit source group. Cell counts are `meets / below / uncertain` per axis over that suite's declarations at their role-scaled targets. A suite composition is `unavailable` when its group exceeds the 48,000-byte composition cap or has unresolved references; it was not split to chase a score. Parse-rejected files and three oversized generated fixtures have zero style coverage and are listed, never counted as clean; datatype-only files without an executable declaration are style-rated on their datatypes. The full per-declaration data is in [style-fixtures-declarations.tsv.gz](style-fixtures-declarations.tsv.gz) (`gzip -dc`, tab separated, `status:percent` cells).

| suite | files reviewed | zero-coverage files | declarations | meet all five | brain | delight | memetic | anticipation | payoff | composition | potential | task |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `data-lifetime-fixtures` | 4 | 0 | 20 | 1 | 15/1/4 | 9/9/2 | 1/18/1 | 2/13/5 | 2/16/2 | below_target | low (25%) | `research/data-lifetime/SPEC.md` |
| `census-fixtures` | 3 | 0 | 16 | 0 | 15/1/0 | 5/5/6 | 0/15/1 | 8/7/1 | 5/9/2 | uncertain | low (17%) | `tools/census/SPEC.md` |
| `perch-context-signatures` | 1 | 0 | 11 | 0 | 8/1/2 | 1/7/3 | 0/10/1 | 2/4/5 | 3/6/2 | below_target | unavailable | `none` |
| `fields-wasm-fixtures` | 6 | 2 | 53 | 9 | 41/0/12 | 18/7/28 | 23/22/8 | 30/10/13 | 43/10/0 | below_target | low (6%) | `tests/compiler-fields-wasm/README.md` |
| `recursion` | 19 | 0 | 69 | 0 | 27/11/31 | 10/38/21 | 0/67/2 | 11/41/17 | 4/61/4 | below_target | low (4%) | `tests/compiler-recursion/SPEC.md` |
| `generics` | 40 | 0 | 226 | 42 | 225/0/1 | 180/11/35 | 43/153/30 | 93/95/38 | 100/90/36 | uncertain | low (5%) | `tests/compiler-generics/FIXTURES.md` |
| `literals` | 31 | 9 | 192 | 13 | 122/20/50 | 124/22/46 | 29/142/21 | 73/105/14 | 71/105/16 | uncertain | low (5%) | `tests/compiler-literals/FIXTURES.md` |
| `io` | 40 | 0 | 145 | 20 | 94/19/32 | 91/16/38 | 53/68/24 | 86/42/17 | 78/46/21 | meets_target | unavailable | `none` |
| `closures` | 40 | 2 | 288 | 77 | 263/8/17 | 238/19/31 | 115/128/45 | 132/106/50 | 153/108/27 | uncertain | unavailable | `none` |
| `sugar` | 35 | 5 | 236 | 69 | 221/1/14 | 184/10/42 | 93/114/29 | 108/100/28 | 127/96/13 | unavailable (unresolved_composition_context) | unavailable | `none` |
| `subsets-classification` | 11 | 19 | 29 | 0 | 27/2/0 | 6/13/10 | 0/28/1 | 13/10/6 | 12/15/2 | unavailable (unresolved_composition_context) | low (0%) | `tests/subsets/CLASSIFICATION.md` |
| `baseslice` | 40 | 0 | 409 | 78 | 257/68/84 | 344/16/49 | 144/212/53 | 198/149/62 | 199/178/32 | unavailable (composition_byte_limit) | unavailable | `none` |
| `poly` | 60 | 1 | 876 | 308 | 847/4/25 | 831/16/29 | 393/316/167 | 439/312/125 | 435/301/140 | unavailable (composition_byte_limit) | unavailable | `none` |
| `selfhost` | 90 | 9 | 1364 | 144 | 664/469/231 | 542/520/302 | 921/350/93 | 398/741/225 | 994/329/41 | unavailable (unresolved_composition_context, composition_byte_limit) | unavailable | `none` |
| **total** | 420 | 47 | 3934 | 761 | | | | | | | | |

Compositions that were available: `data-lifetime-fixtures` below_target, `census-fixtures` uncertain, `perch-context-signatures` below_target, `fields-wasm-fixtures` below_target, `recursion` below_target, `generics` uncertain, `literals` uncertain, `io` meets_target, `closures` uncertain.

## Zero-coverage fixtures

### Rejected by the pinned Bend 2.0.29 parser (44, both semantic and style review impossible)

These are deliberately invalid negative fixtures; the parser rejection is the fixture's purpose (the suite gates record the seed rejection). They are zero-coverage, not clean.

- `tests/compiler-closures/fixtures/lambda-matches-binder.bend`
- `tests/compiler-closures/fixtures/lambda-matches-capture.bend`
- `tests/compiler-literals/fixtures/char-bad-escape.bend`
- `tests/compiler-literals/fixtures/char-empty.bend`
- `tests/compiler-literals/fixtures/char-unicode-escape-width.bend`
- `tests/compiler-literals/fixtures/nat-literal-overflow.bend`
- `tests/compiler-literals/fixtures/nat-pattern-offset-limit.bend`
- `tests/compiler-literals/fixtures/string-unclosed.bend`
- `tests/compiler-literals/fixtures/u32-hex.bend`
- `tests/compiler-literals/fixtures/u32-literal-overflow.bend`
- `tests/compiler-literals/fixtures/u32-operator-unannotated.bend`
- `tests/compiler-poly/fixtures/template-plain-param.bend`
- `tests/compiler-selfhost/fixtures/fuel-string-columns-arity/main.bend`
- `tests/compiler-selfhost/fixtures/layout-braces-comma/main.bend`
- `tests/compiler-selfhost/fixtures/layout-brackets-comma/main.bend`
- `tests/compiler-selfhost/fixtures/layout-call-args-comma/main.bend`
- `tests/compiler-selfhost/fixtures/layout-choose-ladder-comma/main.bend`
- `tests/compiler-selfhost/fixtures/layout-comments-swallowed/main.bend`
- `tests/compiler-selfhost/fixtures/layout-dedent-close-extra/main.bend`
- `tests/compiler-selfhost/fixtures/layout-def-header-comma/main.bend`
- `tests/compiler-sugar/fixtures/destructure-computed.bend`
- `tests/compiler-sugar/fixtures/destructure-order.bend`
- `tests/compiler-sugar/fixtures/destructure-typed.bend`
- `tests/compiler-sugar/fixtures/template-forward.bend`
- `tests/compiler-sugar/fixtures/template-late-binder.bend`
- `tests/subsets/classification/application-binding-after-prefix.bend`
- `tests/subsets/classification/application-parameter-after-prefix.bend`
- `tests/subsets/classification/application-return-after-prefix.bend`
- `tests/subsets/classification/destructure-after-prefix.bend`
- `tests/subsets/classification/destructure-arrow-malformed.bend`
- `tests/subsets/classification/destructure-arrow.bend`
- `tests/subsets/classification/destructure-equality-malformed.bend`
- `tests/subsets/classification/destructure-equality.bend`
- `tests/subsets/classification/destructure-malformed.bend`
- `tests/subsets/classification/generic-malformed.bend`
- `tests/subsets/classification/hash-import-malformed.bend`
- `tests/subsets/classification/local-import-malformed.bend`
- `tests/subsets/classification/match-malformed.bend`
- `tests/subsets/classification/template-after-prefix.bend`
- `tests/subsets/classification/template-malformed.bend`
- `tests/subsets/classification/template-nonleading-erased.bend`
- `tests/subsets/classification/template-nonleading-malformed.bend`
- `tests/subsets/classification/template-nonleading-reusable.bend`
- `tests/subsets/classification/template-nonleading.bend`

### No executable declaration (7; datatype-only, semantic rules not applicable; style-rated on their 13 datatypes)

- `tests/compiler-selfhost/fixtures/qualified-fields-unknown/flags.bend`
- `tests/compiler-selfhost/fixtures/qualified-fields/flags.bend`
- `tests/compiler-selfhost/fixtures/qualified-nested-ctors-foreign/core.bend`
- `tests/compiler-selfhost/fixtures/qualified-nested-ctors/core.bend`
- `tests/compiler-selfhost/fixtures/template-qualified-arg-type/core.bend`
- `tests/compiler-selfhost/fixtures/template-qualified-arg/core.bend`
- `tests/subsets/classification/module.bend`

### Too large for a style context (3, generated stress inputs)

`Style ranking failed: Style context too large after interface summaries`:

- `tests/compiler-selfhost/fixtures/scale-catalog/main.bend`
- `tests/compiler-fields-wasm/fixtures/deep-call.bend`
- `tests/compiler-fields-wasm/fixtures/deep-stack.bend`

## Per file

### `data-lifetime-fixtures`

| file | declarations | meet all five |
| --- | --- | --- |
| `research/data-lifetime/fixtures/list-tail.bend` | 5 | 0 |
| `research/data-lifetime/fixtures/owned-rebuild.bend` | 6 | 0 |
| `research/data-lifetime/fixtures/shared-open.bend` | 5 | 0 |
| `research/data-lifetime/fixtures/tree-share.bend` | 4 | 1 |

### `census-fixtures`

| file | declarations | meet all five |
| --- | --- | --- |
| `tools/census/fixtures/control.bend` | 2 | 0 |
| `tools/census/fixtures/features.bend` | 11 | 0 |
| `tools/census/fixtures/lambda.bend` | 3 | 0 |

### `perch-context-signatures`

| file | declarations | meet all five |
| --- | --- | --- |
| `tests/perch-context/fixtures/signatures.bend` | 11 | 0 |

### `fields-wasm-fixtures`

| file | declarations | meet all five |
| --- | --- | --- |
| `tests/compiler-fields-wasm/fixtures/aliasing.bend` | 5 | 0 |
| `tests/compiler-fields-wasm/fixtures/arena-overflow.bend` | 19 | 0 |
| `tests/compiler-fields-wasm/fixtures/erased.bend` | 8 | 5 |
| `tests/compiler-fields-wasm/fixtures/nested.bend` | 7 | 0 |
| `tests/compiler-fields-wasm/fixtures/pair.bend` | 7 | 0 |
| `tests/compiler-fields-wasm/fixtures/peano.bend` | 7 | 4 |

### `recursion`

| file | declarations | meet all five |
| --- | --- | --- |
| `tests/compiler-recursion/fixtures/add.bend` | 4 | 0 |
| `tests/compiler-recursion/fixtures/after-let.bend` | 3 | 0 |
| `tests/compiler-recursion/fixtures/computed.bend` | 4 | 0 |
| `tests/compiler-recursion/fixtures/deep-input.bend` | 4 | 0 |
| `tests/compiler-recursion/fixtures/deep.bend` | 4 | 0 |
| `tests/compiler-recursion/fixtures/direct.bend` | 3 | 0 |
| `tests/compiler-recursion/fixtures/even.bend` | 5 | 0 |
| `tests/compiler-recursion/fixtures/first-parameter.bend` | 3 | 0 |
| `tests/compiler-recursion/fixtures/length.bend` | 6 | 0 |
| `tests/compiler-recursion/fixtures/mirror.bend` | 4 | 0 |
| `tests/compiler-recursion/fixtures/mutual.bend` | 4 | 0 |
| `tests/compiler-recursion/fixtures/ordered-calls.bend` | 4 | 0 |
| `tests/compiler-recursion/fixtures/other-parameter.bend` | 3 | 0 |
| `tests/compiler-recursion/fixtures/rebuilt-constructor.bend` | 3 | 0 |
| `tests/compiler-recursion/fixtures/rebuilt-parent.bend` | 3 | 0 |
| `tests/compiler-recursion/fixtures/same-parameter.bend` | 3 | 0 |
| `tests/compiler-recursion/fixtures/second-descent.bend` | 3 | 0 |
| `tests/compiler-recursion/fixtures/shadow-field.bend` | 3 | 0 |
| `tests/compiler-recursion/fixtures/shadow-let.bend` | 3 | 0 |

### `generics`

| file | declarations | meet all five |
| --- | --- | --- |
| `tests/compiler-generics/fixtures/affine-dup-data.bend` | 4 | 0 |
| `tests/compiler-generics/fixtures/affine-dup-type.bend` | 4 | 0 |
| `tests/compiler-generics/fixtures/alias-misuse.bend` | 5 | 0 |
| `tests/compiler-generics/fixtures/alias-type.bend` | 6 | 0 |
| `tests/compiler-generics/fixtures/box-instances.bend` | 8 | 3 |
| `tests/compiler-generics/fixtures/box-unbox.bend` | 5 | 2 |
| `tests/compiler-generics/fixtures/closure-apply.bend` | 5 | 0 |
| `tests/compiler-generics/fixtures/data-cell.bend` | 7 | 2 |
| `tests/compiler-generics/fixtures/data-holds-type.bend` | 3 | 0 |
| `tests/compiler-generics/fixtures/erased-interleaved.bend` | 7 | 4 |
| `tests/compiler-generics/fixtures/erased-scrutinee.bend` | 4 | 0 |
| `tests/compiler-generics/fixtures/erased-type-live.bend` | 5 | 0 |
| `tests/compiler-generics/fixtures/erased-value-arg.bend` | 6 | 1 |
| `tests/compiler-generics/fixtures/erased-value-live.bend` | 3 | 0 |
| `tests/compiler-generics/fixtures/forward-generic-types.bend` | 7 | 1 |
| `tests/compiler-generics/fixtures/forward-short-form.bend` | 4 | 0 |
| `tests/compiler-generics/fixtures/generic-let.bend` | 5 | 1 |
| `tests/compiler-generics/fixtures/ghost-bad.bend` | 4 | 0 |
| `tests/compiler-generics/fixtures/kind-type-for-data.bend` | 6 | 0 |
| `tests/compiler-generics/fixtures/match-erased-type.bend` | 5 | 0 |
| `tests/compiler-generics/fixtures/meet-not-reusable.bend` | 6 | 2 |
| `tests/compiler-generics/fixtures/opt-default.bend` | 7 | 1 |
| `tests/compiler-generics/fixtures/pair-swap.bend` | 8 | 2 |
| `tests/compiler-generics/fixtures/phantom-mismatch.bend` | 7 | 1 |
| `tests/compiler-generics/fixtures/phantom-type.bend` | 7 | 3 |
| `tests/compiler-generics/fixtures/quantity-data-fits-type.bend` | 5 | 1 |
| `tests/compiler-generics/fixtures/quantity-invariant.bend` | 6 | 1 |
| `tests/compiler-generics/fixtures/quantity-meet.bend` | 9 | 3 |
| `tests/compiler-generics/fixtures/quantity-parity.bend` | 11 | 5 |
| `tests/compiler-generics/fixtures/quantity-short-form.bend` | 8 | 5 |
| `tests/compiler-generics/fixtures/quantity-zero.bend` | 5 | 1 |
| `tests/compiler-generics/fixtures/reusable-generic.bend` | 6 | 1 |
| `tests/compiler-generics/fixtures/reusable-kind-var.bend` | 3 | 0 |
| `tests/compiler-generics/fixtures/reusable-type-param.bend` | 4 | 0 |
| `tests/compiler-generics/fixtures/rigid-mismatch.bend` | 3 | 0 |
| `tests/compiler-generics/fixtures/seq-parity.bend` | 8 | 2 |
| `tests/compiler-generics/fixtures/shadow-type-name.bend` | 5 | 0 |
| `tests/compiler-generics/fixtures/template-twice.bend` | 5 | 0 |
| `tests/compiler-generics/fixtures/type-arity.bend` | 5 | 0 |
| `tests/compiler-generics/fixtures/wrong-type-arg.bend` | 5 | 0 |

### `literals`

| file | declarations | meet all five |
| --- | --- | --- |
| `tests/compiler-literals/fixtures/char-escapes.bend` | 8 | 2 |
| `tests/compiler-literals/fixtures/char-lexer-traps.bend` | 8 | 1 |
| `tests/compiler-literals/fixtures/char-pattern.bend` | 6 | 1 |
| `tests/compiler-literals/fixtures/char-unicode-escapes.bend` | 8 | 0 |
| `tests/compiler-literals/fixtures/conversions.bend` | 5 | 0 |
| `tests/compiler-literals/fixtures/f32-literal.bend` | 3 | 0 |
| `tests/compiler-literals/fixtures/literal-views.bend` | 5 | 0 |
| `tests/compiler-literals/fixtures/literal-without-base.bend` | 2 | 0 |
| `tests/compiler-literals/fixtures/nat-arithmetic.bend` | 6 | 1 |
| `tests/compiler-literals/fixtures/nat-literals.bend` | 10 | 0 |
| `tests/compiler-literals/fixtures/nat-pattern-offset.bend` | 9 | 0 |
| `tests/compiler-literals/fixtures/nat-recursion.bend` | 8 | 2 |
| `tests/compiler-literals/fixtures/nat-u32-mismatch.bend` | 3 | 0 |
| `tests/compiler-literals/fixtures/string-append.bend` | 6 | 0 |
| `tests/compiler-literals/fixtures/string-concat-operator.bend` | 3 | 0 |
| `tests/compiler-literals/fixtures/string-equality.bend` | 6 | 0 |
| `tests/compiler-literals/fixtures/string-escapes.bend` | 5 | 0 |
| `tests/compiler-literals/fixtures/string-lexer-traps.bend` | 5 | 0 |
| `tests/compiler-literals/fixtures/string-nul.bend` | 5 | 0 |
| `tests/compiler-literals/fixtures/string-pattern.bend` | 6 | 0 |
| `tests/compiler-literals/fixtures/string-raw-non-ascii.bend` | 3 | 0 |
| `tests/compiler-literals/fixtures/string-unicode.bend` | 5 | 0 |
| `tests/compiler-literals/fixtures/u32-division.bend` | 8 | 1 |
| `tests/compiler-literals/fixtures/u32-literals.bend` | 7 | 0 |
| `tests/compiler-literals/fixtures/u32-operators.bend` | 5 | 0 |
| `tests/compiler-literals/fixtures/u32-pattern-first-match.bend` | 8 | 0 |
| `tests/compiler-literals/fixtures/u32-pattern-missing-default.bend` | 3 | 0 |
| `tests/compiler-literals/fixtures/u32-pattern.bend` | 7 | 0 |
| `tests/compiler-literals/fixtures/u32-shifts.bend` | 8 | 2 |
| `tests/compiler-literals/fixtures/u32-unsigned-order.bend` | 13 | 2 |
| `tests/compiler-literals/fixtures/u32-wraparound.bend` | 8 | 1 |

### `io`

| file | declarations | meet all five |
| --- | --- | --- |
| `tests/compiler-io/fixtures/args-echo.bend` | 3 | 1 |
| `tests/compiler-io/fixtures/bind-deep.bend` | 4 | 0 |
| `tests/compiler-io/fixtures/bind-lazy.bend` | 3 | 0 |
| `tests/compiler-io/fixtures/bind-non-io-continuation.bend` | 1 | 0 |
| `tests/compiler-io/fixtures/bind-order.bend` | 6 | 0 |
| `tests/compiler-io/fixtures/die-after-write.bend` | 6 | 2 |
| `tests/compiler-io/fixtures/die-codes.bend` | 3 | 0 |
| `tests/compiler-io/fixtures/die-messages.bend` | 2 | 0 |
| `tests/compiler-io/fixtures/die-nat-code.bend` | 1 | 0 |
| `tests/compiler-io/fixtures/die-stops-effects.bend` | 1 | 0 |
| `tests/compiler-io/fixtures/do-bind-arrow.bend` | 1 | 0 |
| `tests/compiler-io/fixtures/do-bind-type-mismatch.bend` | 1 | 0 |
| `tests/compiler-io/fixtures/effect-file-write.bend` | 3 | 0 |
| `tests/compiler-io/fixtures/effect-get-env.bend` | 2 | 0 |
| `tests/compiler-io/fixtures/effect-print-err.bend` | 1 | 0 |
| `tests/compiler-io/fixtures/effect-write.bend` | 1 | 0 |
| `tests/compiler-io/fixtures/forge-file.bend` | 1 | 0 |
| `tests/compiler-io/fixtures/handle-dropped.bend` | 4 | 0 |
| `tests/compiler-io/fixtures/main-value.bend` | 1 | 0 |
| `tests/compiler-io/fixtures/mini-driver.bend` | 10 | 1 |
| `tests/compiler-io/fixtures/open-modes.bend` | 7 | 0 |
| `tests/compiler-io/fixtures/open-nul-path.bend` | 3 | 0 |
| `tests/compiler-io/fixtures/print-large.bend` | 1 | 0 |
| `tests/compiler-io/fixtures/print-lines.bend` | 1 | 0 |
| `tests/compiler-io/fixtures/print-many.bend` | 2 | 1 |
| `tests/compiler-io/fixtures/print-non-string.bend` | 1 | 0 |
| `tests/compiler-io/fixtures/read-decode.bend` | 8 | 1 |
| `tests/compiler-io/fixtures/read-limit.bend` | 9 | 1 |
| `tests/compiler-io/fixtures/read-result-without-handle.bend` | 3 | 0 |
| `tests/compiler-io/fixtures/read-text.bend` | 6 | 1 |
| `tests/compiler-io/fixtures/result-bind.bend` | 10 | 6 |
| `tests/compiler-io/fixtures/result-missing-fail.bend` | 2 | 0 |
| `tests/compiler-io/fixtures/result-try.bend` | 4 | 3 |
| `tests/compiler-io/fixtures/reuse-file.bend` | 3 | 1 |
| `tests/compiler-io/fixtures/reuse-io.bend` | 2 | 0 |
| `tests/compiler-io/fixtures/write-bytes-affine-list.bend` | 2 | 0 |
| `tests/compiler-io/fixtures/write-bytes-string.bend` | 2 | 0 |
| `tests/compiler-io/fixtures/write-bytes.bend` | 8 | 1 |
| `tests/compiler-io/fixtures/write-read-back.bend` | 8 | 0 |
| `tests/compiler-io/fixtures/write-values.bend` | 8 | 1 |

### `closures`

| file | declarations | meet all five |
| --- | --- | --- |
| `tests/compiler-closures/fixtures/apply-non-function.bend` | 3 | 0 |
| `tests/compiler-closures/fixtures/bind-continuation.bend` | 10 | 3 |
| `tests/compiler-closures/fixtures/capture-affine-twice.bend` | 5 | 0 |
| `tests/compiler-closures/fixtures/capture-field-twice.bend` | 9 | 1 |
| `tests/compiler-closures/fixtures/capture-then-use.bend` | 4 | 0 |
| `tests/compiler-closures/fixtures/choose-promoted.bend` | 9 | 1 |
| `tests/compiler-closures/fixtures/choose-thunks.bend` | 10 | 7 |
| `tests/compiler-closures/fixtures/closure-call-twice.bend` | 4 | 1 |
| `tests/compiler-closures/fixtures/closure-domain-mismatch.bend` | 5 | 0 |
| `tests/compiler-closures/fixtures/closure-drop.bend` | 9 | 2 |
| `tests/compiler-closures/fixtures/closure-field.bend` | 9 | 4 |
| `tests/compiler-closures/fixtures/closure-in-arm.bend` | 10 | 3 |
| `tests/compiler-closures/fixtures/closure-list.bend` | 8 | 4 |
| `tests/compiler-closures/fixtures/closure-over-applied.bend` | 3 | 0 |
| `tests/compiler-closures/fixtures/closure-twice-data.bend` | 5 | 2 |
| `tests/compiler-closures/fixtures/compose.bend` | 7 | 2 |
| `tests/compiler-closures/fixtures/cps-fold.bend` | 10 | 2 |
| `tests/compiler-closures/fixtures/curried-arities.bend` | 7 | 3 |
| `tests/compiler-closures/fixtures/curried-continuation.bend` | 9 | 4 |
| `tests/compiler-closures/fixtures/defunc-sites.bend` | 9 | 5 |
| `tests/compiler-closures/fixtures/dependent-arrow.bend` | 5 | 0 |
| `tests/compiler-closures/fixtures/do-block.bend` | 9 | 3 |
| `tests/compiler-closures/fixtures/erased-capture-live.bend` | 3 | 0 |
| `tests/compiler-closures/fixtures/erased-closure-arg.bend` | 8 | 0 |
| `tests/compiler-closures/fixtures/function-field-data.bend` | 5 | 2 |
| `tests/compiler-closures/fixtures/generic-choose-bind.bend` | 15 | 6 |
| `tests/compiler-closures/fixtures/lambda-apply.bend` | 6 | 1 |
| `tests/compiler-closures/fixtures/lambda-forward-call.bend` | 5 | 0 |
| `tests/compiler-closures/fixtures/lambda-match.bend` | 4 | 1 |
| `tests/compiler-closures/fixtures/lambda-reusable-binder.bend` | 11 | 1 |
| `tests/compiler-closures/fixtures/map-reuses-function.bend` | 6 | 3 |
| `tests/compiler-closures/fixtures/nested-capture.bend` | 11 | 4 |
| `tests/compiler-closures/fixtures/partial-application.bend` | 13 | 3 |
| `tests/compiler-closures/fixtures/partial-self-call.bend` | 8 | 2 |
| `tests/compiler-closures/fixtures/partial-self-same.bend` | 7 | 1 |
| `tests/compiler-closures/fixtures/return-closure.bend` | 7 | 2 |
| `tests/compiler-closures/fixtures/reusable-closure-binder.bend` | 4 | 0 |
| `tests/compiler-closures/fixtures/reusable-function-param.bend` | 4 | 1 |
| `tests/compiler-closures/fixtures/template-map.bend` | 8 | 2 |
| `tests/compiler-closures/fixtures/unannotated-let-lambda.bend` | 4 | 1 |

### `sugar`

| file | declarations | meet all five |
| --- | --- | --- |
| `tests/compiler-sugar/fixtures/annotation-brace.bend` | 5 | 1 |
| `tests/compiler-sugar/fixtures/annotation-list-let.bend` | 7 | 2 |
| `tests/compiler-sugar/fixtures/annotation-reusable-quantity.bend` | 6 | 2 |
| `tests/compiler-sugar/fixtures/annotation-unannotated-list.bend` | 4 | 0 |
| `tests/compiler-sugar/fixtures/char-compare.bend` | 7 | 2 |
| `tests/compiler-sugar/fixtures/char-u32-mismatch.bend` | 4 | 0 |
| `tests/compiler-sugar/fixtures/cons-operator.bend` | 4 | 3 |
| `tests/compiler-sugar/fixtures/dependent-bind.bend` | 9 | 5 |
| `tests/compiler-sugar/fixtures/dependent-choose.bend` | 7 | 2 |
| `tests/compiler-sugar/fixtures/dependent-forward.bend` | 4 | 0 |
| `tests/compiler-sugar/fixtures/dependent-result.bend` | 9 | 5 |
| `tests/compiler-sugar/fixtures/destructure-constructor.bend` | 11 | 5 |
| `tests/compiler-sugar/fixtures/destructure-sum.bend` | 4 | 0 |
| `tests/compiler-sugar/fixtures/destructure-then-match.bend` | 8 | 2 |
| `tests/compiler-sugar/fixtures/function-value-arity.bend` | 6 | 1 |
| `tests/compiler-sugar/fixtures/function-value.bend` | 9 | 2 |
| `tests/compiler-sugar/fixtures/list-as-scalar.bend` | 3 | 0 |
| `tests/compiler-sugar/fixtures/list-element-mismatch.bend` | 5 | 0 |
| `tests/compiler-sugar/fixtures/list-literal-affine.bend` | 11 | 2 |
| `tests/compiler-sugar/fixtures/list-literal.bend` | 9 | 3 |
| `tests/compiler-sugar/fixtures/list-nested.bend` | 7 | 1 |
| `tests/compiler-sugar/fixtures/list-separators.bend` | 9 | 7 |
| `tests/compiler-sugar/fixtures/parallel-let.bend` | 5 | 1 |
| `tests/compiler-sugar/fixtures/partial-call-reuse.bend` | 6 | 1 |
| `tests/compiler-sugar/fixtures/partial-call.bend` | 9 | 2 |
| `tests/compiler-sugar/fixtures/template-bare-call.bend` | 5 | 3 |
| `tests/compiler-sugar/fixtures/template-function-arg.bend` | 7 | 1 |
| `tests/compiler-sugar/fixtures/template-open-argument.bend` | 5 | 2 |
| `tests/compiler-sugar/fixtures/template-set-known.bend` | 12 | 5 |
| `tests/compiler-sugar/fixtures/template-value-arg.bend` | 7 | 2 |
| `tests/compiler-sugar/fixtures/tuple-affine-reuse.bend` | 4 | 0 |
| `tests/compiler-sugar/fixtures/tuple-arity.bend` | 4 | 0 |
| `tests/compiler-sugar/fixtures/tuple-constructor-pattern.bend` | 9 | 2 |
| `tests/compiler-sugar/fixtures/tuple-read-pair.bend` | 8 | 4 |
| `tests/compiler-sugar/fixtures/tuple-right-nested.bend` | 7 | 1 |

### `subsets-classification`

| file | declarations | meet all five |
| --- | --- | --- |
| `tests/subsets/classification/application-binding.bend` | 3 | 0 |
| `tests/subsets/classification/application-parameter.bend` | 4 | 0 |
| `tests/subsets/classification/application-return.bend` | 3 | 0 |
| `tests/subsets/classification/destructure.bend` | 4 | 0 |
| `tests/subsets/classification/generic.bend` | 3 | 0 |
| `tests/subsets/classification/hash-import.bend` | 1 | 0 |
| `tests/subsets/classification/local-import.bend` | 1 | 0 |
| `tests/subsets/classification/match.bend` | 3 | 0 |
| `tests/subsets/classification/module.bend` | 1 | 0 |
| `tests/subsets/classification/template-leading-pair.bend` | 3 | 0 |
| `tests/subsets/classification/template.bend` | 3 | 0 |

### `baseslice`

| file | declarations | meet all five |
| --- | --- | --- |
| `tests/compiler-baseslice/fixtures/bind-missing-types.bend` | 12 | 2 |
| `tests/compiler-baseslice/fixtures/bool-gates.bend` | 11 | 2 |
| `tests/compiler-baseslice/fixtures/bool-pick-values.bend` | 11 | 5 |
| `tests/compiler-baseslice/fixtures/char-as-u32.bend` | 12 | 2 |
| `tests/compiler-baseslice/fixtures/char-cmp-rebuild.bend` | 9 | 4 |
| `tests/compiler-baseslice/fixtures/char-lex-classes.bend` | 12 | 2 |
| `tests/compiler-baseslice/fixtures/char-word-bounds.bend` | 12 | 2 |
| `tests/compiler-baseslice/fixtures/cmp-string-reuse.bend` | 11 | 2 |
| `tests/compiler-baseslice/fixtures/concat-list-quantity.bend` | 12 | 2 |
| `tests/compiler-baseslice/fixtures/io-args-helper.bend` | 4 | 0 |
| `tests/compiler-baseslice/fixtures/io-do-sequence.bend` | 12 | 3 |
| `tests/compiler-baseslice/fixtures/io-file-read-helper.bend` | 6 | 0 |
| `tests/compiler-baseslice/fixtures/io-file-write-helper.bend` | 6 | 1 |
| `tests/compiler-baseslice/fixtures/io-print-helper.bend` | 3 | 0 |
| `tests/compiler-baseslice/fixtures/io-pure-bind.bend` | 12 | 4 |
| `tests/compiler-baseslice/fixtures/length-missing-quantity.bend` | 12 | 3 |
| `tests/compiler-baseslice/fixtures/list-append-levels.bend` | 10 | 3 |
| `tests/compiler-baseslice/fixtures/list-length-arity.bend` | 12 | 2 |
| `tests/compiler-baseslice/fixtures/list-quantity-instances.bend` | 7 | 1 |
| `tests/compiler-baseslice/fixtures/list-reverse-tokens.bend` | 11 | 3 |
| `tests/compiler-baseslice/fixtures/maybe-annotation.bend` | 12 | 2 |
| `tests/compiler-baseslice/fixtures/pick-missing-type.bend` | 11 | 3 |
| `tests/compiler-baseslice/fixtures/read-maybe-quantity.bend` | 12 | 4 |
| `tests/compiler-baseslice/fixtures/reserved-affine.bend` | 8 | 0 |
| `tests/compiler-baseslice/fixtures/result-bind-chain.bend` | 15 | 3 |
| `tests/compiler-baseslice/fixtures/result-host-failure.bend` | 9 | 1 |
| `tests/compiler-baseslice/fixtures/reverse-quantity.bend` | 11 | 0 |
| `tests/compiler-baseslice/fixtures/shrn-u32-count.bend` | 13 | 1 |
| `tests/compiler-baseslice/fixtures/string-append-order.bend` | 6 | 1 |
| `tests/compiler-baseslice/fixtures/string-compare.bend` | 11 | 2 |
| `tests/compiler-baseslice/fixtures/string-concat-diagnostic.bend` | 12 | 1 |
| `tests/compiler-baseslice/fixtures/string-reserved.bend` | 8 | 0 |
| `tests/compiler-baseslice/fixtures/string-reverse-word.bend` | 10 | 2 |
| `tests/compiler-baseslice/fixtures/string-starts-with.bend` | 9 | 0 |
| `tests/compiler-baseslice/fixtures/u32-index-walk.bend` | 13 | 6 |
| `tests/compiler-baseslice/fixtures/u32-leb128.bend` | 13 | 1 |
| `tests/compiler-baseslice/fixtures/u32-nat-bridge.bend` | 11 | 3 |
| `tests/compiler-baseslice/fixtures/u32-natural-budget.bend` | 12 | 3 |
| `tests/compiler-baseslice/fixtures/u32-read-edges.bend` | 7 | 2 |
| `tests/compiler-baseslice/fixtures/u32-show-digits.bend` | 9 | 0 |

### `poly`

| file | declarations | meet all five |
| --- | --- | --- |
| `tests/compiler-poly/fixtures/bind-arrow-instance.bend` | 18 | 5 |
| `tests/compiler-poly/fixtures/bind-instance-chain.bend` | 16 | 6 |
| `tests/compiler-poly/fixtures/bind-promoted-instance.bend` | 21 | 7 |
| `tests/compiler-poly/fixtures/bind-rigid-caller.bend` | 15 | 5 |
| `tests/compiler-poly/fixtures/choose-branch-mismatch.bend` | 20 | 8 |
| `tests/compiler-poly/fixtures/choose-result-chain.bend` | 20 | 10 |
| `tests/compiler-poly/fixtures/choose-rigid.bend` | 14 | 6 |
| `tests/compiler-poly/fixtures/curried-generic-continuation.bend` | 23 | 9 |
| `tests/compiler-poly/fixtures/generic-arrow-instances.bend` | 10 | 5 |
| `tests/compiler-poly/fixtures/generic-capture.bend` | 10 | 3 |
| `tests/compiler-poly/fixtures/generic-compose.bend` | 12 | 4 |
| `tests/compiler-poly/fixtures/kind-closure-at-data.bend` | 14 | 1 |
| `tests/compiler-poly/fixtures/kind-closure-list.bend` | 14 | 2 |
| `tests/compiler-poly/fixtures/kind-closure-reuse.bend` | 14 | 2 |
| `tests/compiler-poly/fixtures/kind-forward.bend` | 14 | 5 |
| `tests/compiler-poly/fixtures/kind-higher-order.bend` | 15 | 6 |
| `tests/compiler-poly/fixtures/kind-meet-reuse.bend` | 17 | 7 |
| `tests/compiler-poly/fixtures/kind-quantity-mismatch.bend` | 15 | 3 |
| `tests/compiler-poly/fixtures/kind-result-list.bend` | 13 | 6 |
| `tests/compiler-poly/fixtures/kind-reuse-affine-result.bend` | 15 | 5 |
| `tests/compiler-poly/fixtures/kind-two-quantities.bend` | 17 | 9 |
| `tests/compiler-poly/fixtures/kind-zero-arrow.bend` | 9 | 2 |
| `tests/compiler-poly/fixtures/promoted-affine-instance.bend` | 21 | 9 |
| `tests/compiler-poly/fixtures/rank2-choose-action.bend` | 20 | 9 |
| `tests/compiler-poly/fixtures/rank2-choose-mismatch.bend` | 20 | 7 |
| `tests/compiler-poly/fixtures/rank2-continuation-twice.bend` | 17 | 9 |
| `tests/compiler-poly/fixtures/rank2-continuation.bend` | 17 | 8 |
| `tests/compiler-poly/fixtures/rank2-do-block.bend` | 15 | 7 |
| `tests/compiler-poly/fixtures/rank2-monomorphic-arg.bend` | 16 | 3 |
| `tests/compiler-poly/fixtures/rank2-param.bend` | 14 | 2 |
| `tests/compiler-poly/fixtures/rank2-partial-bind.bend` | 18 | 8 |
| `tests/compiler-poly/fixtures/rank2-pure-bind.bend` | 15 | 8 |
| `tests/compiler-poly/fixtures/rank2-rigid-answer.bend` | 15 | 8 |
| `tests/compiler-poly/fixtures/rank2-run-twice.bend` | 19 | 6 |
| `tests/compiler-poly/fixtures/rank2-try.bend` | 15 | 6 |
| `tests/compiler-poly/fixtures/rank2-two-answers.bend` | 17 | 5 |
| `tests/compiler-poly/fixtures/rigid-capture-twice.bend` | 14 | 4 |
| `tests/compiler-poly/fixtures/rigid-closure-twice.bend` | 13 | 3 |
| `tests/compiler-poly/fixtures/rigid-domain-mismatch.bend` | 12 | 1 |
| `tests/compiler-poly/fixtures/rigid-reusable-type.bend` | 14 | 5 |
| `tests/compiler-poly/fixtures/sigma-affine-twice.bend` | 13 | 6 |
| `tests/compiler-poly/fixtures/sigma-dependent.bend` | 9 | 2 |
| `tests/compiler-poly/fixtures/sigma-family-live-binder.bend` | 9 | 1 |
| `tests/compiler-poly/fixtures/sigma-in-result-action.bend` | 21 | 8 |
| `tests/compiler-poly/fixtures/sigma-pair.bend` | 13 | 6 |
| `tests/compiler-poly/fixtures/sigma-reusable.bend` | 11 | 4 |
| `tests/compiler-poly/fixtures/sigma-reuse-affine.bend` | 13 | 7 |
| `tests/compiler-poly/fixtures/sigma-snd-mismatch.bend` | 9 | 0 |
| `tests/compiler-poly/fixtures/sigma-unpack.bend` | 10 | 3 |
| `tests/compiler-poly/fixtures/sigma-unrefined.bend` | 10 | 0 |
| `tests/compiler-poly/fixtures/template-any-forward.bend` | 13 | 4 |
| `tests/compiler-poly/fixtures/template-filter-data.bend` | 11 | 7 |
| `tests/compiler-poly/fixtures/template-fold-quant.bend` | 10 | 5 |
| `tests/compiler-poly/fixtures/template-generic-arg.bend` | 9 | 3 |
| `tests/compiler-poly/fixtures/template-map-types.bend` | 11 | 3 |
| `tests/compiler-poly/fixtures/template-open-type.bend` | 13 | 3 |
| `tests/compiler-poly/fixtures/template-quant-kind.bend` | 10 | 4 |
| `tests/compiler-poly/fixtures/template-set-known-thunk.bend` | 21 | 10 |
| `tests/compiler-poly/fixtures/template-thunk-affine.bend` | 21 | 8 |
| `tests/compiler-poly/fixtures/template-type-mismatch.bend` | 11 | 0 |

### `selfhost`

| file | declarations | meet all five |
| --- | --- | --- |
| `tests/compiler-selfhost/fixtures/cross-module-hof-type-arg/main.bend` | 9 | 0 |
| `tests/compiler-selfhost/fixtures/cross-module-hof-type-arg/syntax.bend` | 3 | 0 |
| `tests/compiler-selfhost/fixtures/cross-module-hof/main.bend` | 9 | 1 |
| `tests/compiler-selfhost/fixtures/cross-module-hof/syntax.bend` | 3 | 0 |
| `tests/compiler-selfhost/fixtures/fuel-continuation-capture/main.bend` | 16 | 6 |
| `tests/compiler-selfhost/fixtures/fuel-continuation/main.bend` | 16 | 7 |
| `tests/compiler-selfhost/fixtures/fuel-four-columns-column-type/main.bend` | 14 | 3 |
| `tests/compiler-selfhost/fixtures/fuel-four-columns/main.bend` | 14 | 4 |
| `tests/compiler-selfhost/fixtures/fuel-rows-missing-zero/main.bend` | 10 | 4 |
| `tests/compiler-selfhost/fixtures/fuel-rows/main.bend` | 10 | 4 |
| `tests/compiler-selfhost/fixtures/fuel-string-columns/main.bend` | 11 | 6 |
| `tests/compiler-selfhost/fixtures/fuel-wildcard-first-reuse/main.bend` | 11 | 6 |
| `tests/compiler-selfhost/fixtures/fuel-wildcard-first/main.bend` | 10 | 4 |
| `tests/compiler-selfhost/fixtures/io-do-imported-statement/lib.bend` | 2 | 0 |
| `tests/compiler-selfhost/fixtures/io-do-imported-statement/main.bend` | 2 | 0 |
| `tests/compiler-selfhost/fixtures/io-do-imported/lib.bend` | 2 | 0 |
| `tests/compiler-selfhost/fixtures/io-do-imported/main.bend` | 2 | 0 |
| `tests/compiler-selfhost/fixtures/io-fuel-loader-missing-zero/main.bend` | 14 | 3 |
| `tests/compiler-selfhost/fixtures/io-fuel-loader/main.bend` | 14 | 4 |
| `tests/compiler-selfhost/fixtures/io-load-continuation-type/main.bend` | 9 | 2 |
| `tests/compiler-selfhost/fixtures/io-load-continuation/main.bend` | 9 | 1 |
| `tests/compiler-selfhost/fixtures/layout-braces/main.bend` | 8 | 1 |
| `tests/compiler-selfhost/fixtures/layout-brackets/main.bend` | 7 | 3 |
| `tests/compiler-selfhost/fixtures/layout-call-args/main.bend` | 6 | 3 |
| `tests/compiler-selfhost/fixtures/layout-choose-ladder/main.bend` | 6 | 1 |
| `tests/compiler-selfhost/fixtures/layout-comments/main.bend` | 8 | 2 |
| `tests/compiler-selfhost/fixtures/layout-dedent-close/main.bend` | 7 | 3 |
| `tests/compiler-selfhost/fixtures/layout-def-header/main.bend` | 6 | 2 |
| `tests/compiler-selfhost/fixtures/layout-lambda-statements-reuse/main.bend` | 11 | 4 |
| `tests/compiler-selfhost/fixtures/layout-lambda-statements/main.bend` | 11 | 4 |
| `tests/compiler-selfhost/fixtures/list-generic-field-element/main.bend` | 12 | 3 |
| `tests/compiler-selfhost/fixtures/list-generic-field/main.bend` | 12 | 1 |
| `tests/compiler-selfhost/fixtures/list-lambda-body-scalar/main.bend` | 9 | 2 |
| `tests/compiler-selfhost/fixtures/list-lambda-body/main.bend` | 9 | 1 |
| `tests/compiler-selfhost/fixtures/list-literal-imported-element/flags.bend` | 4 | 0 |
| `tests/compiler-selfhost/fixtures/list-literal-imported-element/main.bend` | 9 | 3 |
| `tests/compiler-selfhost/fixtures/list-literal-imported/flags.bend` | 4 | 0 |
| `tests/compiler-selfhost/fixtures/list-literal-imported/main.bend` | 9 | 4 |
| `tests/compiler-selfhost/fixtures/list-of-results-element/main.bend` | 8 | 3 |
| `tests/compiler-selfhost/fixtures/list-of-results/main.bend` | 8 | 4 |
| `tests/compiler-selfhost/fixtures/mutual-term-bind-defs/main.bend` | 12 | 2 |
| `tests/compiler-selfhost/fixtures/mutual-term-bind/main.bend` | 12 | 1 |
| `tests/compiler-selfhost/fixtures/nat-65536-as-word/main.bend` | 3 | 0 |
| `tests/compiler-selfhost/fixtures/nat-65536/main.bend` | 6 | 1 |
| `tests/compiler-selfhost/fixtures/nested-self-call-list-suffix/main.bend` | 10 | 2 |
| `tests/compiler-selfhost/fixtures/nested-self-call-list/main.bend` | 10 | 3 |
| `tests/compiler-selfhost/fixtures/nested-self-call-mistyped/main.bend` | 5 | 1 |
| `tests/compiler-selfhost/fixtures/nested-self-call/main.bend` | 11 | 3 |
| `tests/compiler-selfhost/fixtures/qualified-collision-bare/lib.bend` | 4 | 2 |
| `tests/compiler-selfhost/fixtures/qualified-collision-bare/main.bend` | 6 | 0 |
| `tests/compiler-selfhost/fixtures/qualified-collision/lib.bend` | 4 | 2 |
| `tests/compiler-selfhost/fixtures/qualified-collision/main.bend` | 6 | 2 |
| `tests/compiler-selfhost/fixtures/qualified-fields-unknown/flags.bend` | 2 | 0 |
| `tests/compiler-selfhost/fixtures/qualified-fields-unknown/main.bend` | 13 | 0 |
| `tests/compiler-selfhost/fixtures/qualified-fields/flags.bend` | 2 | 0 |
| `tests/compiler-selfhost/fixtures/qualified-fields/main.bend` | 13 | 4 |
| `tests/compiler-selfhost/fixtures/qualified-nested-ctors-foreign/core.bend` | 3 | 0 |
| `tests/compiler-selfhost/fixtures/qualified-nested-ctors-foreign/main.bend` | 12 | 3 |
| `tests/compiler-selfhost/fixtures/qualified-nested-ctors/core.bend` | 3 | 0 |
| `tests/compiler-selfhost/fixtures/qualified-nested-ctors/main.bend` | 12 | 4 |
| `tests/compiler-selfhost/fixtures/rose-tree-kids/main.bend` | 12 | 2 |
| `tests/compiler-selfhost/fixtures/rose-tree/main.bend` | 12 | 4 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m00.bend` | 38 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m01.bend` | 40 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m02.bend` | 40 | 1 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m03.bend` | 40 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m04.bend` | 40 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m05.bend` | 40 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m06.bend` | 40 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m07.bend` | 40 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m08.bend` | 40 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m09.bend` | 40 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m10.bend` | 40 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m11.bend` | 40 | 1 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m12.bend` | 40 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m13.bend` | 40 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m14.bend` | 40 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m15.bend` | 40 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m16.bend` | 40 | 1 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m17.bend` | 40 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m18.bend` | 40 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/m19.bend` | 40 | 0 |
| `tests/compiler-selfhost/fixtures/scale-bundle/main.bend` | 6 | 0 |
| `tests/compiler-selfhost/fixtures/template-qualified-arg-type/core.bend` | 1 | 0 |
| `tests/compiler-selfhost/fixtures/template-qualified-arg-type/main.bend` | 10 | 3 |
| `tests/compiler-selfhost/fixtures/template-qualified-arg/core.bend` | 1 | 0 |
| `tests/compiler-selfhost/fixtures/template-qualified-arg/main.bend` | 10 | 3 |
| `tests/compiler-selfhost/fixtures/u32-bitwise-edges/main.bend` | 12 | 0 |
| `tests/compiler-selfhost/fixtures/u32-bitwise-word-count/main.bend` | 3 | 0 |
| `tests/compiler-selfhost/fixtures/u32-nat-roundtrip/main.bend` | 6 | 0 |
