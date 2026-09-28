# Pattern-matrix fixtures (campaign increment `nest`)

These fixtures freeze the expected behavior of campaign milestone 3, the pattern
matrix, **before** it is implemented (decisions D4 and D7 in
[the campaign charter](../../docs/COMPILER-CAMPAIGN.md)). The scope is
multi-scrutinee matches, wildcard and variable patterns, nested constructor
patterns, first-match order, exhaustiveness, unreachable rows, erased and
affine fields inside nested patterns, and structural recursion through nested
patterns.

Every expectation comes from one of two sources:

- the pinned seed, Bend 2.0.29 at `574b6d3`, run on the unmodified fixture; or
- literal review, marked `knot_expected` and justified in one line.

Nothing here was derived from Knot's output, and `regen.py` never runs Knot.

The fixtures use no Base, no literals and no imports; each one declares its own
datatypes. Every entry a host can call takes and returns nullary enums declared
in the fixture, because the host boundary is enum-only for now. Every fixture
also has a `main()` that the seed can run.

## Layout

| Path | Content |
|---|---|
| `fixtures/*.bend` | 40 programs, one feature or edge each. Line 1 is a `#` summary, which `regen.py` checks against `summary`. |
| `expectations.json` | Reviewed metadata, frozen seed observations and the Knot outcome for every fixture. |
| `regen.py` | Re-runs the seed over every fixture and entry call, then fails on any difference. |

Each fixture record has two kinds of field:

- **Hand-reviewed:** `feature`, `kind`, `requires`, `summary`, `types`, `entries`, `control`, `seed_rule` and `knot`.
- **Written by the script:** `sha256` and `observed`.

`observed.main` is the seed run on the fixture itself. `observed.calls` is every
entry called over its whole argument domain: 174 calls in total. Each call
records the following:

- the constructor arguments and their ordinals
- `result_type` and `type_id`
- the decoded `result` and `tag`
- the exact wrapper source and command
- the seed's `exit`, `stdout` and `stderr`

## Regenerating and checking

```sh
python3 tests/compiler-nest/regen.py          # check: must print "no differences"
python3 tests/compiler-nest/regen.py --write  # refreeze after a reviewed fixture change
```

The script runs every command from the repository root with
`BEND_NO_TELEMETRY=1`. The seed is
`bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts FILE`, the same program that
`scripts/bend-reference` launches.

**Wrappers.** An entry call goes through a generated wrapper. It lives at
`.local/compiler-nest/calls/<fixture>/<entry>-<args>.bend`, which is ignored.
The wrapper imports the unmodified fixture as `F` and its `main` calls
`F.entry(F.A{}, …)`. The seed prints the import path before the constructor,
for example `../../../../tests/compiler-nest/fixtures/multi-table.Green{}`.
The script records that exact output and decodes it to `Green`.

**Check mode fails** on any of the following:

- a changed `exit`, `stdout` or `stderr`
- a changed fixture hash
- a changed hash of the seed's `main.ts`, `bend.ts` or `comp.ts`
- a Bun version other than 1.3.14
- a fixture present on disk but not listed, or listed but missing
- a `types` or `entries` list that differs from the fixture's declared enum-only signatures
- a negative whose seed rejection lacks its `seed_rule` text, or whose `control` is not a seed-accepted fixture
- a seed-accepted fixture marked `Invalid` for Knot
- a `knot_expected` outcome without a justification

**`--write`** rewrites only `seed`, `tools`, `sha256` and `observed`. It never
creates, alters or drops a `knot` block. Review the resulting diff before
committing, as you would a new expectation.

## Coverage matrix

Negatives name their nearby valid control in `control`.

| Feature | Positive | Edge | Negative (control) | Out of stage |
|---|---|---|---|---|
| Multi-scrutinee `match a b:` | `multi-table`, `multi-three` | `multi-var-column-reorder`, `multi-shadow-binder` | `multi-ctor-column-reorder` (var-column-reorder) | |
| Wildcard / variable patterns | `wildcard-default`, `variable-rebind`, `variable-reusable` | `forward-bare-binder` | `variable-affine-overuse` (variable-reusable), `bare-constructor-binder` (forward-bare-binder), `forward-constructor-pattern` (forward-bare-binder) | |
| Nested constructor patterns | `nested-pair`, `nested-sum` | `nested-alias-reconstruct` | `nested-missing` (nested-pair) | |
| First-match order | `first-match-multi` and `-swapped`, `first-match-nested` and `-swapped` | `first-match-duplicate-arm` | | |
| Unreachable rows | `unreachable-after-wildcard` | `unreachable-type-error`, `unreachable-free-name` | `unreachable-pattern-type` (after-wildcard) | |
| Exhaustiveness | (every accepted fixture) | `empty-type` | `multi-missing` (first-match-multi), `nested-missing`, `empty-match` (empty-type) | |
| Erased / affine nested fields | `erased-nested-ignore`, `affine-nested-promote` | | `erased-nested-inspect`, `erased-nested-live-use` (both: erased-nested-ignore), `affine-nested-reuse` (affine-nested-promote) | |
| Structural recursion + nesting | `rec-even-nested`, `rec-multi-descent`, `rec-list-nested` | | `rec-swapped-args` (multi-descent), `rec-alias` (even-nested) | |
| Knot-specific (seed-accepted, beyond this stage) | | | | `closure-parameter` (closure in an arm), `generic-box-pattern` (nested pattern through a generic) |

**Totals:**

| Kind | Count |
|---|---|
| Positive | 17 |
| Edge | 8 |
| Negative | 13 |
| Out-of-stage | 2 |

**Twin fixtures.** The swapped twins differ only in the order of their first two
rows. They discriminate on the results:

- `first-match-multi`: 1 of 4 calls differs.
- `first-match-nested`: 4 of 16 calls differ.

A "last row wins" or "most specific row wins" implementation fails at least one
of each pair. In `first-match-duplicate-arm`, a repeated `On{}` row returns
`R1`, not `R3`.

**Requirements.** `requires` marks the dependencies on other increments:

- `fields` (17 fixtures): executing these in Wasm needs increment 2 (the heap and fielded constructors).
- `recursion` (5 fixtures): these need increment 1 (structural recursion with a descent check).
- The seed reference lane is fully frozen today.

## Seed behavior these fixtures pin

The seed's `match_flatten` (bend2/bend.ts) compiles rows first-match: "first row
wins, uncovered cases become `\{}`". It shows the following behavior.

**Unreachable rows are dropped before checking.** A row shadowed by earlier rows
is never checked, resolved or run:

- `unreachable-type-error` returns a `Color` from a `Flag` def and is accepted.
- `unreachable-free-name` names an unbound variable and is accepted.

**A constructor row still makes its column strict, even under an earlier
catch-all.** An unreachable pattern of the wrong type is therefore rejected
(`unreachable-pattern-type`).

**Scrutinee order follows binder order.** A constructor column on a later
parameter closes the earlier ones (`multi-ctor-column-reorder`). A column that
holds only variables binds without closing anything, so `match b a:` is accepted
(`multi-var-column-reorder`). A variable row names the scrutinee, rebuilt from
the fields of any split:

- `nested-alias-reconstruct` depends on this rebuild.
- `rec-alias` shows that the rebuilt value is not smaller than the parameter, so recursion on it is rejected.

**Constructor patterns resolve when they are parsed.** `case On{}` before `Flag`
is declared is an unknown constructor (`forward-constructor-pattern`). In the
same position, a bare `On` is an ordinary binder, so `case On: On` is the
identity (`forward-bare-binder`). After the declaration, a bare `On` is rejected
(`bare-constructor-binder`).

**Other behavior:**

- A `+` mark on a variable row makes the matched parameter reusable (`variable-reusable`). Without the mark, the error names the parameter `x`, not the row binder (`variable-affine-overuse`).
- Binders are identities, not names. In `case v v: v`, the second binder wins (`multi-shadow-binder`).
- A zero-constructor datatype accepts a zero-row match (`empty-type`). A zero-row match on `Flag` reports `cases for Off, On` (`empty-match`).

## Knot outcomes

`knot.source = "seed"` means Knot must agree with the seed:

- **`Accepted`:** checking succeeds, and the independent evaluator and the Wasm lane both return `observed.main.tag` and every `observed.calls[].tag`.
- **`Invalid`:** exit 2 with the stated phase and code, and no artifact.

Each code comes with its `code_basis`. Most reuse a precedent frozen in
`tests/compiler-checker` or `tests/compiler-fields` for the same seed rule. Two
cases differ:

- `forward-constructor-pattern` proposes `unknown-constructor`.
- The two recursion negatives leave the code to increment 1's descent check.

The five `knot_expected` fixtures are reviewed decisions. The coordinator may
override them in the directions noted, but never to `Invalid`:

| Fixture | Knot outcome | Why | Allowed override |
|---|---|---|---|
| `unreachable-type-error` | Accepted, with the seed's results | The seed drops the row before checking | `Unsupported check unreachable-arm` |
| `unreachable-free-name` | Accepted, with the seed's results | The seed drops the row before resolving names | `Unsupported check unreachable-arm` |
| `empty-type` | Accepted | Base case of exhaustiveness; `src/catalog.bend` currently rejects it as `Invalid empty-datatype` | `Unsupported check empty-datatype` |
| `closure-parameter` | `Unsupported\tparse\tparameter-type\t` | Closures are milestone 7; the code is frozen for `function-field.bend` in `tests/compiler-structural` | none |
| `generic-box-pattern` | `Unsupported\tparse\ttype-parameters\t` | Generics are milestone 6; the code is new | reconcile if increment 0 names the form first |

## What the implementer wires

The gate runner belongs to the implementer. This suite provides only the oracle.

1. **Run the oracle first.** Run `python3 tests/compiler-nest/regen.py` at the start of the gate, and fail if it fails. Record `seed`, `tools` and the fixture hashes in the receipt.
2. **Check lane.** On the native and Bun lanes, run `check-cli` on every fixture and compare with `knot`: exit 0 for Accepted; for Invalid or Unsupported, the exact `Invalid|Unsupported\t<phase>\t<code>\t` prefix. A null `code` means the phase must match and the code comes from increment 1.
3. **Evaluator lane.** For each Accepted fixture, run `eval-cli <file> main <budget>` and, for every call, `eval-cli <file> <export> <budget> <ordinals…>`. Require `Evaluated\t<type_id>\t<tag>\t…`.
4. **Wasm lane.** Once fielded constructors emit (increment 2), compile each Accepted fixture. Run `scripts/run-wasm.mjs <module> <export> <ordinals…>` for `main` and every call, and require `tag`. `empty-type` exports `absurd`, which has no callable domain.
5. **Rejected compiles.** Every rejected compile must leave a pre-existing output file untouched.
6. **Staging.** Stage by `requires`. Before increment 1 lands, `recursion` fixtures may report `Unsupported check recursive-call`. Record them as pending, never as passes.
7. **Mutation.** Add the semantic mutants of `docs/LAW-QUALITY-GATE.md`, for example "last row wins" or "drop the strict column". They must be killed by these unchanged expectations.

**Assertions this increment supersedes.** D7 keeps existing assertions
unchanged, so the coordinator must decide how to retire or re-profile each of
these. None was edited here.

- `tests/compiler-checker/cases.json`, `duplicate-arm.bend`: `Unsupported check duplicate-arm`. See `first-match-duplicate-arm`.
- `tests/compiler-fields/cases.json`:
  - `nested-pattern`: `Unsupported check duplicate-arm`.
  - `nested-single-pattern`: `Unsupported check nested-field-pattern`.
- `src/SPEC.md`:
  - "every constructor … exactly once"
  - "Constructor patterns have no fields"
  - duplicate arms Unsupported
  - wildcard/multi-scrutinee and nested patterns unsupported
- `research/compiler-fields/SPEC.md`, and `src/CONTRACT.json` `structural_terms.patterns`: flat patterns only.
- `src/catalog.bend`, `empty-datatype`: Invalid. No frozen test asserts this.

## Omissions

These are left out deliberately and are not covered:

- Destructuring lets such as `K{x, y} = v`. The seed lowers them to one-row matches, but they are not in this increment's stated scope.
- Literal and `1n+p` patterns, which need Base.
- Lambda-match `\{…}`, except as the seed-side argument in `closure-parameter`.
- Parallel lets.
- Or-patterns and guards, which the seed does not have.
- Resource budgets for deep pattern trees. The implementer's gate owns its exhaustion probes.
