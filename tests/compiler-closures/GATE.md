# Closure execution gate

Run `BEND_NO_TELEMETRY=1 python3 tests/compiler-closures/check.py`.
The gate writes `receipts/closures.json`; build products and source mutants stay
under ignored `.local/compiler-closures/gate/`.

The original `FIXTURES.md`, `expectations.json`, `regen.py`, and 42 fixtures are
immutable inputs. The gate runs `regen.py` first: all 292 seed entry calls,
42 source checks, 18 seed rejections, fixture hashes, and seed hashes must still
match. Compiler output is never an expectation source.

The native and Bun lanes independently build the checker, evaluator, and the
existing Fields compile entry. Each fixture runs through all three phases.
Successful evaluator calls must return the frozen constructor and tag; Node
must return the same tag from actual Wasm. The two compilers must emit identical
bytes. Rejected compilation preserves an existing output marker. Every pinned
negative keeps its exact exit and diagnostic prefix. Unsupported, Invalid,
Exhausted, HostFailure, InternalFailure, process failures, and harness timeouts
remain distinct observations.

`generic-choose-bind` is blocked while its declared generics prerequisite is
unavailable. A blocking result must be exactly `Unsupported parse
generic-datatype` in all three phases. It retains its original `agree`
requirement, is listed under `blocked`, and contributes no agreement calls.
If it checks, every frozen call runs normally. The gate's successful execution
of available capabilities does not claim that a blocked fixture passes.

The three open boundary fixtures may agree or report Unsupported, as their
original requirements permit. Their compiler lanes must agree on classification.
The gate reports frozen fixtures, supplemental probes, seed calls, evaluator
calls, Node calls, rejection observations, blocked calls, boundaries, and mutant
kills separately; these overlapping counts are not summed into a test total.

## Supplemental expectations

`probes.json` was frozen from the pinned seed before closure implementation.
Its two sources add eight seed calls and two complete seed checks. Each gate
reruns every stored supplemental command and requires exact stdout/stderr,
exit status, and source hashes.

- `probes/erased-layout.bend` captures `x` live and uses `w` only as an erased
  argument. Both enum inputs return unchanged. The reviewed layout is the
  two-word cell `[site,x]`; the erased capture has no slot. In the unchanged
  65,536-byte arena, one instance completes 8,192 calls before call 8,193 reports
  arena exhaustion. A second overflow confirms that the failed allocation did
  not advance the bump pointer.
- `probes/deep-tail.bend` constructs 2,048 affine identity continuations through
  acyclic doubling helpers. It allocates less than one arena page. The shallow
  and deep entries both return their input under the existing fields gate's
  `node --stack_size=80 --liftoff-only --no-wasm-tier-up` host controls.
  Converting tail calls to ordinary calls must leave the shallow control working
  and make the deep call report `Exhausted wasm call-stack`.

`arena.mjs` only instantiates Wasm, invokes an export repeatedly, compares an enum
result, and observes the arena trap. It contains no compiler or source-language
semantics. WAT inspection rejects tables, function references, indirect calls,
imports, or memory exports. Any memory has the bounded arena profile. The deep
continuation control must contain `return_call`; a program without a tail call
does not need that instruction.

## Semantic mutants

Every source replacement in `mutants.json` has one unique anchor. Each modified
compiler must pass the pinned seed's complete `--check-only` entry point and
build in both native and Bun lanes before its observation counts as a kill.

| Mutant | Independent witness |
| --- | --- |
| Wrong dispatch arm | A frozen `defunc-sites` call returns the wrong enum tag. |
| Capture dropped | A frozen captured-value call returns the wrong enum tag. |
| Affine capture duplicated | The checker accepts the frozen `capture-affine-twice` rejection. |
| Erased capture stored live | The supplemental arena probe exhausts before its reviewed boundary. |
| Tail call not in tail position | The shallow control succeeds and the deep continuation exhausts the call stack. |

A crash, malformed module, provider failure, unrelated rejection, or timeout is
not a semantic kill. The gate additionally checks evaluator fuel, emission
depth, output capacity, and host entry lookup. All three complete proof entries
run: `src/closure-types-PROOF.bend`, `src/closure-check-PROOF.bend`, and
`src/closure-PROOF.bend`. The receipt lists their checked laws. Corpus agreement
is separate from those laws and does not claim a general compiler-correctness
theorem.

## Review regressions

`regressions.json` and `regressions/*.bend` were frozen from the seed before the
corresponding fixes. The gate reruns all 22 recorded seed observations for eleven
sources and requires exact source/seed hashes and process results.

- Postfix application or a literal lambda used as a match scrutinee is `Invalid check
  computed-scrutinee`, not an internal compiler failure.
- `_ => _` is `Invalid check free-name`: a discarded lambda binder does not
  introduce a usable name. `_ => On{}` is its accepted control.
- A discarded `_` binder leaves a valid global function `_()` visible.
- Six additional accepted controls cover erased-only captures, nested erased
  captures, reconstructed parents, partial application across erased or reusable
  parameters, and empty application `f()` preserving a function value.

All eleven sources run through both compiler lanes; the eight accepted `main`
calls also compare the evaluator and Wasm against their fixed seed result.
Regression counts are reported separately from the immutable 42 fixtures and
the two representation/continuation probes.
