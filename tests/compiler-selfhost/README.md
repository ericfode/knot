# Self-hosting joint suite

These fixtures pin the source shapes, combinations and scales that Knot's own
bundle S uses and that no other suite pins. They are the `joint` increment of
the [self-hosting path](../../docs/compiler-campaign/SELF-HOSTING-PATH.md#joint)
(D13, D14). Under D7 the expectations were fixed before any implementation:

- seed-accepted and seed-rejected outcomes come from the pinned seed, Bend 2.0.29 at `574b6d3`;
- Knot's codes for the rejected twins come from literal review of Knot's existing
  diagnostic vocabulary.

Nothing here was derived from Knot's output. Every case names the increment that
owns it, and the gate never passes a case whose needs have not landed.

| File | Role |
|---|---|
| `fixtures/<case>/main.bend` | The entry of each of 65 cases. Sibling `.bend` files are its local modules, and `inputs/` holds its IO inputs. |
| `expectations.json` | Reviewed: `needs`, `cases` and `lane_decisions`. Generated: `observations`, every seed record on both lanes. |
| `regen.py` | The seed lane. `verify` (the default) recomputes everything and fails on any difference; `--write` refreezes. |
| `check.py` | The gate (`selfhost`). It runs the seed lane, then Knot, with blocked cases reported separately. `--judge` re-verifies a receipt. |
| `receipts/selfhost.json` | The gate receipt: per-case status, Knot's observations, counts, mutants. No dates, timings or absolute paths. |

## Commands

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-selfhost/regen.py verify   # seed lanes only, about 1 minute
BEND_NO_TELEMETRY=1 python3 tests/compiler-selfhost/check.py          # the gate, about 2 minutes
python3 tests/compiler-selfhost/check.py --judge tests/compiler-selfhost/receipts/selfhost.json
BEND_NO_TELEMETRY=1 npm run -s gates                                  # includes `selfhost`
```

Builds, wrappers and IO sandboxes live under the ignored `.local/compiler-selfhost/`.
Timeouts are hang guards only; they scale with `KNOT_GATE_TIMEOUT_SCALE`.

## Seed lanes (DEC-7)

Every seed call is observed on both oracle lanes that DEC-7 recommends:

- `interpreter`: `bun main.ts <wrapper.bend>`, the reference interpreter;
- `native`: `bun main.ts <wrapper.bend> -o <bin>`, built through clang and then run. This is the lane C1 is built on.

The seed builds natively only a book that imports Base. Each call therefore goes
through one generated wrapper, used for both lanes:

```
import Base
import <fixture>/main.bend as F
def main() -> F.<Result>: F.<entry>(F.<Ctor>{},..)
```

The Base import has a consequence: even a Base-free fixture must avoid Base's
names. The seed rejects a module's `type Pair` next to Base as a duplicate
declaration.

IO cases run the whole program on each lane, with argv, empty stdin and a fresh
sandbox seeded with tracked inputs. Each run also carries reviewed literals
(exit, stdout, stderr), and the seed must agree with them.

A seed-rejected twin is observed three ways:

- the interpreter's direct `--check-only` report;
- its run report;
- the native build of a wrapper that imports the twin, which must fail and build nothing.

Both lanes must name the reviewed `seed_reason`. The native report's
module-path prefixes are normalized first. Today the two lanes' reports are
byte-identical after that normalization (`same_report`).

**Lane agreement today:** 194 calls and 7 IO runs, with 0 disagreements. A
disagreement fails `regen.py` unless a reviewed `lane_decisions` entry names it,
with the oracle lane it chose. The seed's Bun JS lane (`-o x.js`) is not an
oracle here; the lanes increment measures it.

## Knot requirements

- **`agree`** (34 positives).
  - Value cases: Knot's `check-cli` checks the entry, and `eval-cli <entry> <fn> <budget> <ordinals..>` returns the frozen constructor and tag for every call. The budget defaults to 65,536; the scale and Nat cases use 1,048,576. Exhausted within the budget does not meet the requirement.
  - IO cases: a Knot route must reproduce every run's exit, stdout, stderr and files. No Knot lane runs IO programs yet, so the need `io` (core-io) blocks them.
- **`reject`** (31 twins).
  - Every phase that runs (check and eval) must exit 2 with the pinned `Invalid<TAB>phase<TAB>code<TAB>` prefix.
  - Where `at` is pinned, the reported position must be the seed's caret, as `line:column` (1-based line, 0-based column). `regen.py` verifies that each pin is where the seed points.
  - Each code is an existing one: `type-mismatch`, `expected-term`, `parameter`, `end-of-body`, `argument-separator`, `missing-arm`, `affine-reuse`, `pattern-type`, `pattern-arity` (nest's matrix), `unknown-type`, `unknown-function` and `forward-live-call`.
  - A twin is the positive's own shape with one reviewed defect, so it needs what the positive needs. It keeps a D4-sound implementation from accepting the defect.

The runner invokes the CLIs in single-file mode. When `modules` lands, that
increment adds its bundle argument in `check.py` (`observe`), in the same change
that flips the need.

## Blocked cases

A case is **blocked** while any need it names is `available: false` in the
reviewed `needs` table of `expectations.json`. Blocking is never inferred from
Knot's output.

- The owning increment flips its need to `true` in the change that lands the
  capability. Every case with that need then must pass, or the gate fails.
- Knot still runs on a blocked case. The receipt records its first blocker as
  evidence, but the case never counts as passing.
- `blocked_meeting_requirement` lists a blocked case that Knot already meets. That flags a need that may be ready to flip.
- A blocked case may report Invalid, Unsupported or Exhausted. A host or
  internal failure, a signal, an unclassified exit or a timeout fails the gate.
- A seed-valid blocked case that Knot calls `Invalid` is a D4 gap. It is listed
  in `counts.d4_gaps`, so it stays visible, not silent.

Available on this tree: `fields`, `recursion`.

**Today:**

| Status | Count |
|---|---|
| Pass | 2 |
| Blocked | 63 |
| Fail | 0 |

The five D4 gaps are all owned by selfsource:

- `layout-call-args`, `layout-braces`, `layout-dedent-close` and `layout-comments`: `Invalid parse expected-term` at the first continuation newline;
- `layout-def-header`: `Invalid parse parameter` (SF-01, SF-02).

The other blocked cases stop at `Unsupported`:

- `parse declaration-form` at `import`;
- `lex literal`;
- `parse parameter-type` at a function type;
- `Exhausted parse budget` for `scale-catalog`.

## Cases

**Ids** are the requirement ids of the gap analysis. **Needs** omits the landed
`fields` and `recursion`. A twin's needs equal its positive's.

| Case | Owner | Ids | Needs | Twin (Knot code, pinned position) | Today |
|---|---|---|---|---|---|
| `nested-self-call` | descent-2 | SF-18 | - | `nested-self-call-mistyped` (type-mismatch, 19:48) | pass |
| `nested-self-call-list` | descent-2 | SF-18 | base, generics, literals | `nested-self-call-list-suffix` (type-mismatch) | blocked |
| `layout-call-args` | selfsource | SF-01 | layout | `layout-call-args-comma` (expected-term, 18:14) | blocked, D4 gap |
| `layout-def-header` | selfsource | SF-02 | layout | `layout-def-header-comma` (parameter, 7:12) | blocked, D4 gap |
| `layout-braces` | selfsource | SF-01 | layout | `layout-braces-comma` (expected-term, 12:11) | blocked, D4 gap |
| `layout-brackets` | selfsource | SF-01 | layout, base, generics, lists | `layout-brackets-comma` (expected-term, 36:12) | blocked |
| `layout-dedent-close` | selfsource | SF-01 | layout | `layout-dedent-close-extra` (end-of-body, 16:6) | blocked, D4 gap |
| `layout-comments` | selfsource | SF-01, SF-03 | layout | `layout-comments-swallowed` (argument-separator; position not pinned) | blocked, D4 gap |
| `layout-lambda-statements` | selfsource | SF-01 | layout, closures | `layout-lambda-statements-reuse` (affine-reuse) | blocked |
| `layout-choose-ladder` | selfsource | SF-04 | layout, closures | `layout-choose-ladder-comma` (expected-term, 24:11) | blocked |
| `fuel-rows` | literals | SF-05, SF-06 | base, literals, nat-columns, nest | `fuel-rows-missing-zero` (missing-arm) | blocked |
| `fuel-wildcard-first` | literals | SF-05 | base, literals, nat-columns, nest | `fuel-wildcard-first-reuse` (affine-reuse) | blocked |
| `fuel-string-columns` | literals | SF-05 | base, literals, nat-columns, nest | `fuel-string-columns-arity` (pattern-arity) | blocked |
| `fuel-continuation` | literals | SF-06 | base, literals, nat-columns, nest, closures | `fuel-continuation-capture` (affine-reuse) | blocked |
| `fuel-four-columns` | literals | SF-05 | base, literals, nat-columns, nest | `fuel-four-columns-column-type` (pattern-type) | blocked |
| `qualified-nested-ctors` | modules | SF-08 | base, modules, packages, nest, generics, literals | `qualified-nested-ctors-foreign` (pattern-type) | blocked |
| `qualified-fields` | generics | SF-09 | base, modules, packages, nest, generics, literals | `qualified-fields-unknown` (unknown-type) | blocked |
| `qualified-collision` | generics | INT-02 | base, modules, generics | `qualified-collision-bare` (unknown-function) | blocked |
| `cross-module-hof` | integrate-1 | SF-21 | base, modules, generics, closures, nest | `cross-module-hof-type-arg` (type-mismatch) | blocked |
| `rose-tree` | generics | SF-10 | base, generics, literals, nat-columns, nest | `rose-tree-kids` (type-mismatch) | blocked |
| `mutual-term-bind` | generics | SF-10 | base, generics, literals, nat-columns, nest | `mutual-term-bind-defs` (forward-live-call) | blocked |
| `io-load-continuation` | core-io | SF-13 | base, io, closures, generics, products, do, literals, nest, lists | `io-load-continuation-type` (type-mismatch) | blocked |
| `io-fuel-loader` | core-io | SF-13 | as above, plus nat-columns | `io-fuel-loader-missing-zero` (missing-arm) | blocked |
| `io-do-imported` | sugar | SF-14, SF-22 | base, io, modules, do, literals, closures | `io-do-imported-statement` (type-mismatch) | blocked |
| `list-literal-imported` | sugar | SF-22 | base, modules, lists, generics, nest | `list-literal-imported-element` (type-mismatch) | blocked |
| `list-generic-field` | sugar | SF-16 | base, lists, generics, nest | `list-generic-field-element` (type-mismatch) | blocked |
| `list-lambda-body` | sugar | SF-16 | base, lists, generics, closures, nest | `list-lambda-body-scalar` (type-mismatch) | blocked |
| `list-of-results` | sugar | SF-16 | base, lists, generics, nest | `list-of-results-element` (type-mismatch) | blocked |
| `template-qualified-arg` | sugar | SF-17 | base, modules, templates, generics, closures, lists, nest | `template-qualified-arg-type` (type-mismatch) | blocked |
| `scale-catalog` | selfsource | SCALE-01 | catalog, spine | none: the seed rejects no book for its size | blocked |
| `scale-bundle` | selfsource | SCALE-01 | base, modules, catalog, spine | none, as above | blocked |
| `nat-65536` | literals | SCALE-05 | base, literals | `nat-65536-as-word` (type-mismatch) | blocked |
| `u32-nat-roundtrip` | literals | SCALE-05 | base, literals, nat-word | none: `nat-65536-as-word` covers the Nat/U32 boundary | blocked |
| `u32-bitwise-edges` | literals | BS-05 | base, literals, u32-bits | `u32-bitwise-word-count` (type-mismatch) | blocked |

Each case's `shape` and `site` in `expectations.json` name the Knot source it
mirrors.

`layout-lambda-statements` separates two ways of implementing layout.
Continuation newlines inside delimiters are skippable. The newlines between a
lambda body's statements are not, even inside an argument list. So a lexer that
drops every newline inside delimiters fails that case, while a parser that skips
newlines at continuation points passes it, as SELF-HOSTING-PATH.md (selfsource)
requires. The generated scale fixtures are:

- `scale-catalog`: 723 functions in one Base-free book;
- `scale-bundle`: 782 functions across 20 modules plus Base, reached through one 720-link call chain.

`regen.py` regenerates both and verifies them byte for byte.

## What the gate checks

1. `regen.py`'s seed lane reproduces `observations` exactly. That covers the seed and package hashes, the fixture hashes, both lanes of every call, and the reviewed IO literals and twin positions.
2. The seed builds Knot's `check-cli` and `eval-cli` on the native lane.
3. Every case runs through Knot and is classified. An unblocked case must pass.
4. The judge recomputes every status from recorded fields only. It fails in these cases:
   - a recorded status differs;
   - a blocked case crashed;
   - the needs differ;
   - a seed call lacks a lane or disagrees without review;
   - no case passes.
5. Eleven mutated receipts or expectations must each be rejected by the judge:
   - a blocked case counted as a pass;
   - a failure relabelled as blocked;
   - a dropped call;
   - a flipped tag;
   - a crash while blocked;
   - a reworded diagnostic;
   - a shifted position;
   - stale needs;
   - an unreproduced seed;
   - an unreviewed lane disagreement;
   - a dropped native lane.
6. Three type-correct mutants of `src/` must be killed by an unblocked case, with a classified, non-crashing observation:
   - `reject-every-self-call` (check.bend): `nested-self-call` becomes `Unsupported check recursive-call`.
   - `admit-mistyped-constant` (check.bend): `nested-self-call-mistyped` checks.
   - `unreversed-fields` (eval.bend): `nested-self-call` evaluates wrong constructors.

## Limits

- The seed's interpreter and native lanes are the oracle. The seed's JS lane is not observed.
- Entries cross the host boundary as nullary enums only. Lists, strings and words are observed through the enum results they determine.
- Knot runs only through `check-cli` and `eval-cli`. The Wasm and image routes are compared with the evaluator by their own gates. The IO route has no Knot lane yet.
- A Knot code pin for a twin is a literal-review decision. An owner can change one before implementing, through a reviewed amendment that states why. An implementation result never justifies the change.
- Two shapes have no seed-rejected twin: scale and the Nat round trip. Their reasons are in the table above.
