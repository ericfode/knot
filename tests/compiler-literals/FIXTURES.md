# Literals fixture suite (frozen)

These are the frozen expectations for campaign increment 5, **Primitives and
literals** ([charter](../../docs/COMPILER-CAMPAIGN.md)). Under D7 they were fixed
before implementation. Seed-accepted and seed-rejected outcomes come from the
pinned seed, Bend 2.0.29 at `574b6d3`. Knot-specific outcomes come from literal
review. Nothing in this directory was derived from Knot's output. Under D4, a
form Knot cannot yet check is `Unsupported`, never `Invalid`, and never passed
through unchecked.

| File | Role |
|---|---|
| `fixtures/*.bend` | 40 programs, one feature or edge each. All but `literal-without-base` import Base. |
| `expectations.json` | Per fixture: its hash, the seed's `--check-only` record, every entry call with its exact command, stdout, stderr and exit, and the Knot outcome. |
| `regen.py` | Re-runs the seed and fails on any difference from `expectations.json`. |

## Host boundary

Every observed entry takes and returns nullary enums declared in its fixture.
`arguments` are constructor ordinals in declaration order, and `tag` is the
result's ordinal. This is the enum-only ABI of `scripts/run-wasm.mjs` and
`eval-cli`. Helpers that return `U32`, `Nat`, `Char` or `String` (`value`,
`char`, `text`, `result`, `nat` and the like) are exported by the current Wasm
contract, but no call observes them. Some enums are `Data`, only so that
`exact(+x)` can use its argument twice.

The seed prints a direct `main` run as `Yes{}`. It reaches every other entry
through a generated wrapper under the ignored `.local/compiler-literals/calls/`,
whose output carries the import path:
`../../../tests/compiler-literals/fixtures/<name>.Yes{}`. The recorded
`constructor` and `tag` strip that prefix.

## Coverage

Fixture names omit the directory and the `.bend` suffix. K marks a Knot-specific
`knot_expected` outcome.

| Feature | Positive | Edge | Negative |
|---|---|---|---|
| U32 | `u32-literals`, `u32-pattern` | `u32-wraparound`, `u32-unsigned-order`, `u32-division`, `u32-shifts`, `u32-pattern-first-match` | `u32-literal-overflow`, `u32-hex`, `u32-pattern-missing-default`, `u32-operator-unannotated` (K) |
| Nat | `nat-literals`, `nat-recursion` | `nat-pattern-offset`, `nat-arithmetic` | `nat-literal-overflow`, `nat-pattern-offset-limit`, `nat-u32-mismatch` |
| Char | `char-escapes`, `char-pattern` | `char-unicode-escapes`, `char-lexer-traps` | `char-empty`, `char-bad-escape`, `char-unicode-escape-width` |
| String | `string-equality`, `string-append`, `string-escapes`, `string-pattern` | `string-nul`, `string-unicode`, `string-lexer-traps` | `string-unclosed` |
| Conversions | `conversions` | | |
| Literal and constructor views | | `literal-views` | |
| Base import | | | `literal-without-base` |
| Outside the stage (K) | `u32-operators`, `string-concat-operator`, `string-raw-non-ascii`, `f32-literal` | | |

The seed accepts 28 books and rejects 12. The suite has 275 recorded seed
calls, 268 of them on the 24 fixtures where Knot must agree. The calls of each
such fixture yield at least two distinct constructors (`regen.py` asserts this),
so a constant answer cannot pass.

The Wasm-hostile edges are the most discriminating:

- **Unsigned comparison.** `U32.cmp(2147483648, 0)` is `GT`, and `is_gt`,
  `is_ge`, `is_le` and `is_lt` agree, where signed `i32` comparisons flip them.
- **Unsigned division.** `4294967295 / 2` is `2147483647` and `4294967295 % 10`
  is `5`.
- **Division by zero.** `7 / 0` is `0` and `7 % 0` is `7`, where Wasm
  `div_u`/`rem_u` trap.
- **Shift width.** `U32.shln(1, 32n)` is `0`, where Wasm masks the count and
  gives `1`. `shrn` is logical.
- **Surrogates.** `"\u{1F600}"` differs from `"\u{d83d}\u{de00}"`: escaped
  surrogates stay two Chars.

## Knot outcomes

- **`knot: agree`** (24 fixtures). The book checks. For every call, Knot's
  evaluator and the emitted Wasm both return the recorded `tag`.
- **`knot: Invalid`** (11 fixtures). The seed rejects the book. Knot exits 2
  with an `Invalid` diagnostic and emits no artifact. Phase and code are open to
  the implementer; the seed's exact message is recorded as evidence.
- **`knot_expected: Unsupported`** (5 fixtures). These are reviewed literals.
  Knot exits 3, the diagnostic starts with the recorded prefix, and no artifact
  is emitted. The seed's own result is kept alongside.

| Fixture | Prefix | Justification |
|---|---|---|
| `u32-operators` | `Unsupported\tparse\toperator\t` | Operator sugar is outside this increment, which reaches primitives through literals and Base calls. |
| `string-concat-operator` | `Unsupported\tparse\toperator\t` | The same, for `++`. |
| `u32-operator-unannotated` | `Unsupported\tparse\toperator\t` | The seed rejects it, but Knot does not check operators in this increment, so D4 forbids an `Invalid` claim. |
| `string-raw-non-ascii` | `Unsupported\tlex\tnon-ascii\t` | Knot source stays ASCII (`src/SPEC.md`). `\u{e9}` expresses the same text. This is the lexer's existing code. |
| `f32-literal` | `Unsupported\tlex\tf32-literal\t` | F32 execution is outside the bootstrap profile (S3), and Base's F32 operations are native claims. The fixture only drops the value, because the seed's normalizer leaves `F32.is_lt(1.5, 2.5)` stuck. |

In these prefixes, `\t` stands for a tab character, as in the other compiler
suites; `expectations.json` holds the exact strings. The operator decision is the one scope call the seed cannot settle. It
**may be vetoed before implementation starts**. If it is, move the three
operator fixtures to `agree` (the first two) and `Invalid` (the third) in
`PLAN`, then re-freeze. After implementation starts, changing any expectation
requires a recorded review. Implementation results never justify one.

## Dependencies the implementer should see up front

- **Milestone 3 (pattern matrix).** Wildcard and binder defaults and the
  first-match duplicate arms in `u32-pattern-first-match` need it. Today's
  profile reports duplicate arms as `Unsupported`. Nested patterns need it
  too: in `string-pattern`, `case "ab"` is an `SCon` chain and `SCon{'a', t}`
  puts a Char literal inside a constructor; in `nat-pattern-offset`, `2n+p`
  is a double `Succ`.
- **Milestone 1 (structural recursion).** `nat-recursion` and
  `nat-pattern-offset` (a `2n+p` descent) need it, as does much of the
  reachable Base.
- **Milestone 6 (generics).** Base reaches pairs from `String.eq`, `String.cmp`
  and `Char.cmp`, and `U32.cmp` answers the Base enum `Cmp`. Under D2, only the
  reachable Base slice is lowered. `base_names` lists what each fixture spells
  directly, not its full closure.
- **Evaluator budget.** `nat-recursion.deep` recurses 65,536 times, and
  `nat-literals.agrees(S65536)` builds `U32.to_nat(65536)` and compares two
  unary Nats of that size. Both need more than the default 65,536 transitions.
  Nobody has measured whether they fit under the 1,048,576 maximum. If the
  evaluator reports `Exhausted`, that result is inconclusive under the contract:
  the gate must report it and must not count it as a pass, and it is no reason
  to edit the fixture. Nat values in this suite stay at 65536 or below, because
  the seed itself does not finish on `4294967295n`-scale unary work.

## Seed behaviour worth knowing

- **Number literals.**
  - There is no hex literal: `0xFF` is rejected at the `x`.
  - Leading zeros are decimal: `007` is `7`.
  - A U32 literal stops at `4294967295`, and a Nat literal at `4294967295n`.
  - Up to `256n`, `n+m` of literals folds and `256n+p` is a pattern. `257n+p` is
    `Nat.add` and is rejected as a pattern.
- **Char literals.**
  - `'''` is an apostrophe, and `''` is rejected.
  - The escape letter may be `\u` or `\U`, with 1 to 8 hex digits in either
    case. Nine digits are rejected even when the value is small.
  - Any 32-bit value is a Char: surrogates, values past U+10FFFF, and
    `\u{FFFFFFFF}`.
- **String literals.**
  - They may span a raw newline.
  - `#` and `'` inside them are plain characters.
- **Literal matches.** A U32 or Char literal match with no default arm is
  rejected with `cases for True`, because it lowers to a Bool test.

## Regenerating and verifying

From the repository root, with Bun 1.3.14 and the pinned toolchain at
`.toolchain/bend-2.0.29-574b6d3`:

```sh
python3 tests/compiler-literals/regen.py          # verify; exit 0 only on a byte-exact match
python3 tests/compiler-literals/regen.py --write  # re-freeze after a reviewed change
```

Every command runs from the repository root with `BEND_NO_TELEMETRY=1` and a
120-second timeout. A timeout aborts the script and is never recorded as a
result. Verification also fails in these cases:

- the hash of the seed's `main.ts`, `bend.ts` or `base.bend` changes;
- the Bun version changes;
- a fixture is edited, added or removed;
- a `PLAN` entry changes;
- any output leaks a local path;
- a local name reuses a Base name.

`--write` builds the document twice and writes only if both builds agree. A full
run takes about 20 seconds.

## What the implementer wires

The gate runner belongs to the implementer. It should:

1. Run `regen.py` in verify mode first. A mismatch means the frozen evidence
   moved, and the gate stops.
2. For each `knot: agree` fixture, in both native and Bun lanes:
   - `check-cli` reports `Checked`;
   - every call through `eval-cli <file> <export> <budget> <arguments…>` returns
     `tag`;
   - `compile-cli` builds the module;
   - `node scripts/run-wasm.mjs <module> <export> <arguments…>` validates and
     returns `tag`.
3. For each `knot: Invalid` fixture, compile and evaluate: exit 2, an `Invalid`
   diagnostic, and an existing output file left untouched.
4. For each `knot_expected` fixture: exit 3, the exact `diagnostic_prefix`, and
   no artifact.
5. Record receipts in the style of `tests/compiler-wasm/receipts/`. Never edit
   `expectations.json` to match Knot.
