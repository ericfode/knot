# Fielded Wasm increment

`knot-fields-wasm-1` compiles completely checked, acyclic structural terms to a
one-page bump arena. The original `knot-enum-1` entry, capability law, assertions
and 25 module byte strings are retained. `src/check.bend` is unchanged.

The central representation is a cell containing its tag and live fields in
declaration order. Erasure removes a slot from both construction and matching.
All constructors of a fielded type use cells, including nullary and erased-only
constructors. Enum-only types stay ordinals. Arguments are saved in fresh locals
before allocation; an appended allocator checks remaining capacity before
advancing the bump or allowing stores. Checked exhaustive branch signatures
determine a match's representation; `Case.type_id` is its result type.

## Commands

```sh
export BEND_NO_TELEMETRY=1
bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts tests/compiler-fields-wasm/compile.bend -o .local/compile-fields
.local/compile-fields tests/compiler-fields-wasm/fixtures/pair.bend .local/pair.wasm
node scripts/run-wasm.mjs --profile=knot-fields-wasm-1 .local/pair.wasm swapped 0 1
python3 tests/compiler-fields-wasm/check.py
bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts tests/compiler-fields-wasm/PROOF.bend
```

The driver reuses the existing checked loader, budget parser and writer. A
separate explicit entry is necessary to keep the default compiler's existing
field-rejection assertions unchanged. The library entry is
`wasm.emit_profile(Fields{},book,depth,bytes)`; callers must supply a checked book.

The host profile flag asserts Knot compiler provenance. All original function
indices/exports are retained, but this adapter may invoke only functions with
enum-only live parameters and results. Structured parameters/results are for
compiled callers; their integer representation cannot be validated as an enum
ordinal from a bare Wasm signature. Erased parameters do not enter the ABI.

## Fixed expectations and executable evidence

`cases.json` contains literal result tags; `expectations.json` records the pinned
seed's independent observations and source hashes. The first 31 observations
and the enum hashes were fixed before emitter implementation. The additional
wide-stack fixture's `On{}` result and constrained-stack outcome were fixed
before exercising it. The seed is rerun by every gate invocation; expected
results are never derived from the emitter or evaluator.

| Fixture | Observation |
| --- | --- |
| `pair` | First field and swap/first, all four enum argument pairs |
| `peano` | Nonrecursive add-one; zero, one and two classification; nullary cell |
| `nested` | Build a nested constructor and read an inner field |
| `aliasing` | Two simultaneously live boxes retain distinct values |
| `erased` | Interleaved erased/live fields, erased forward call, erased-only and nullary constructors |
| `arena-overflow` | Acyclic call doubling allocates 16,384 boxes; seed/evaluator return On, bounded Wasm exhausts |
| `deep-call` | Narrow 250-call chain exceeds the evaluator's fixed parser budget; explicit compiler budget builds it, Node returns On |
| `deep-stack` | 160 acyclic frames with 48 parameters: seed/evaluator/default Node return On; constrained Node exhausts |

`--stack_size=80 --liftoff-only --no-wasm-tier-up` is the declared stack-test
configuration. The same flags successfully run the shallow `pair` control.
The initial 64 KiB probe failed during Node ESM startup, so it was not accepted
as a Wasm exhaustion observation. The narrow chain remains an explicit parser
budget control, not a three-way successful value comparison.

The gate passes 8 fixtures and 32 seed calls. Each compiler lane has 32 evaluator
observations (31 values, 1 parser exhaustion) and 32 Node observations (31
values, 1 arena exhaustion). Native/Bun modules agree byte for byte. Selecting
the Fields profile for each of the 25 enum fixtures preserves the frozen hashes
in both lanes: 50 checks, with sections `[1,3,7,10]`.

The 30 boundary probes comprise, per lane: 2 constrained-stack probes, 4
persistent-arena boundaries, 7 HostFailure classifications and 2 compiler
exhaustion/output-preservation checks. Persistent tests reach exactly 65,536
bytes with 8-byte boxes and 4-byte erased/nullary cells; 12-byte pairs leave 4
bytes unused. Each next allocation traps, and a repeated attempt traps too.
The independent `wasm2wat` whitelist permits one `unreachable` only in heap
modules; it also checks memory min=max=1, initial bump zero and export indices.

| Type-correct mutant | Frozen witness | Expected / mutant result |
| --- | --- | --- |
| Swapped store offsets | `pair.direct(0,1)` | 0 / 1 |
| Stored erased slot | `erased.observe(0,1)` | 1 / 0 |
| Wrong cell tag | `erased.ghost()` | 1 / 0 |
| No pointer bump | `aliasing.observe(0,1)` | 0 / 1 |

All four mutant compilers typecheck, emit decoder-valid modules, and yield the
wrong enum result in both compiler lanes: 8 semantic kills. Parse/type errors,
timeouts, host failures and invalid Wasm cannot satisfy these kill assertions.

## Proof and style boundary

Five new `law` declarations have filled proofs: enum capability preservation,
the structural profile's capability, erased-only constructor representation,
erased argument omission and erased pattern slot/local preservation. The
complete proof entry imports `src/fields-PROOF.bend` and its earlier proof chain
and prints `All terms check.` These are helper and erasure laws, not a general
heap-refinement or compiler-correctness theorem. Runtime differential and
mutation checks supply separate evidence.

The offline rubric-v8 preflight ran on all 12 changed/new Bend files, covering
526 declarations with zero provider requests. It returned attention (exit 3):
330 truncated contexts, 355 declarations lacking complete supporting-role
context, and unavailable composition (130,419 bytes against 48,000 plus unresolved
collaborators/imports). `src/SPEC.md` also exceeds the task input byte limit.
Of the emitter's 45 declarations, 8 have truncated contexts and 31 have incomplete
role context; the large stack fixtures account for 316 of the truncated units.

No conceptual-compression, delight, memetic-identity, anticipation or payoff
scores are available. No automatic style pass is claimed. The coordinator owns
bounded live review and the parser/context limits; correct code was not rewritten
to remove these preflight diagnostics. The complete report is
`receipts/style-preflight.json`.

## Regression gates and remaining work

`receipts/verification.json` records the final commands, outcomes, counts and
source identities. Every existing assertion is unchanged.

| Gate | Passed observations |
| --- | --- |
| Frontend | 14 seed fixtures, 2 parser lanes, 24 boundaries, 4 laws, 4 mutants |
| Checker | 49 seed fixtures, 98 checked observations, 10 depth and 16 catalog bounds, 7 mutants |
| Structural | 16 seed fixtures, 4 boundary pairs, 7 mutants |
| Fields | 40 seed fixtures, 240 phase observations, 36 budgets, 6 host probes, 12 level/inspection observations, 9 mutants |
| Enum Wasm | 25 programs, 90 seed calls in 2 lanes, 64 rejection pairs, 44 boundaries, 7 mutants |
| Wasm trust | 3 entries; zero holes; loaded closures 15/13/18 files |
| Fields trust | 4 entries; zero holes; loaded closures 22/12/13/15 files |
| Structural trust | 2 entries; zero holes; loaded closures 20/8 files |
| Owned store | 3,532 cases per lane, 15 literal witnesses, 5 quantity controls, 6 mutants |
| Flat store | 13,621 observations / 3,534 instances per lane, 7 lifecycle checks per lane, 9 mutants; unchanged 1,050-byte module |
| `lint:verify` | 103 tests, 0 failures; 8 law rules validated; no provider requests |

The lint run needed a workspace-local parser cache: the sandbox cannot lock the
user's global cache. The already installed manifest and grammar libraries were
copied into `.local/compiler-fields-wasm/parser-cache`; a Node preload used the
package's `configure({cacheDir})` API. This changes cache location only; no
assertions or installed dependency sources changed, and no downloads were made.

The arena is fixed at one page, persists across calls, and never reclaims dropped
values. Owned-storage reclamation R3/R7, structured host arguments, recursion,
tail calls, GPU lowering and self-hosting are unmet. Next: integrate the separate
recursion increment with this profile, expose profile selection in the public
CLI under driver ownership, and qualify allocation/reclamation separately.
Live Perch review remains the coordinator's gate before merge.
