# Optional core optimization gate

This gate qualifies the optional `knot-core-opt-1` pipeline over already checked
`Book`, `Function` and `Term` values. The existing enum and fields entries remain
unchanged. The optimization entry is `compile.bend`; `eval.bend` evaluates its
checked output independently of Wasm. `audit.bend SOURCE ROUNDS` renders checked
core after zero, one, or two pipeline applications.

## Fixed expectations

`expectations.json` records six source fixtures and 24 literal, pinned-seed calls
before optimizer implementation:

| Fixture | Obligation | Calls |
| --- | --- | ---: |
| `known` | Reordered case arms select by constructor tag | 3 |
| `capture` | Inlining preserves parameters and a branch-local binding | 9 |
| `used-let` | A used reusable let survives while an unused reusable let can disappear | 3 |
| `known-fields` | Constructor/branch fusion preserves second-field projection | 5 |
| `tail` | First-parameter structural self-recursion retains its enum result | 1 |
| `non-tail` | A self-call used as another call's argument remains non-tail | 3 |

All 25 enum programs and their 90 calls, eight fields programs and their 32 calls,
and all 19 structural recursion programs retain their existing assertions.
Eleven recursion programs are accepted, seven are Unsupported, and the live
mutual-call fixture is Invalid. Nine deterministic `bench/generate.mjs` programs
cover enum widths, match widths, and acyclic call depths at 16, 64 and 128.
Four subsequent review regressions add 23 independently seeded calls without
changing the original observations: sibling argument relocation
(`hostile-multi-arg`), locals in a nullary callee (`hostile-nullary`),
constructor-field fusion scope (`hostile-fusion`), and erased forward references
(`hostile-erased-forward`). Their expectation-freeze timestamp is separate from
the original preimplementation freeze.

The generated formula is cross-checked against the pinned reference, never used
as a substitute for it.

The eleven accepted recursion mains return structured values. Literal observer
suffixes recognize each complete fixed result tree and return the enum
`OptObservation`; each has a seeded near-miss control returning `OptMismatch`.
The gate verifies that each observer fixture is precisely the original source
plus its frozen suffix. Its 22 calls run through seed, both evaluators, and actual
Wasm. No cell address is interpreted as an enum ordinal, and no memory export or
host implementation of the source semantics is introduced.

`baseline.json` fixes 63 unoptimized modules and eleven observer modules from the
existing fields entry. Every existing `src/*.bend` identity is recorded as baseline provenance.
Receipts audit those identities, while the gate enforces the fixed emitted bytes
and behavior. Source identity changes alone do not block later checked frontend
growth. The gate
rebuilds the unoptimized modules in native and Bun, requires their exact byte
hashes, and independently compares the default enum entry's 25 outputs. New
optimizer source files do not change this baseline.

## Assertions and outcomes

The 63 accepted corpus programs and eleven exact-tree observer programs run in
seed-built native and Bun lanes. The 211 reference calls cover their fixed
argument domains. Each of the three core passes also runs separately, using
Bend entry wrappers that replace only the pipeline call with `O.apply`.
For each lane:

- Compare the seed and evaluator observations against fixed literal expectations.
- Compare evaluation before and after optimization.
- Invoke every recorded enum host call on unoptimized and optimized real Wasm.
- Compare `wasm2wat`-decoded export names and function signatures.
- Compare canonical function-body and signature observations after one and two pipeline applications. Datatypes, token spans and caches are outside this rendering.
- Preserve the checked core function signatures and compare native/Bun bytes.

The existing `deep-call` evaluator parser limit remains an explicit Exhausted
observation; its enlarged compile/audit bounds permit Wasm and core inspection.
The arena-overflow control may become a successful value after allocation
elimination. Exhaustion is inconclusive about a value and is recorded separately.
The constrained-stack shallow control must run; deep programs may remain
Exhausted or finish with the fixed value after optimization. Neither outcome is
relabelled Invalid or Unsupported. Harness timeout, host failure, internal
failure, and compiler rejection are separate records.

Every optimized module must target only its current function with `return_call`.
The tail fixture must contain that instruction; the non-tail fixture must retain
an ordinary self `call` and contain no `return_call`. Its values and
constructor-building recursion also retain their fixed observations.
Zero optimizer depth and zero output capacity must report their exact Exhausted
codes. Both lanes must preserve a preexisting output on those failures and on a
missing-source HostFailure.
The new filled law entry must print `All terms check.` The 43 literal malformed
and valid core controls run in both lanes, checking the independent core
verifier's status distinctions, affine and erased use, declarations, lexical
levels, calls, cases, descent, and exhaustion.

## Mutants

Private scratch copies introduce four type-correct compiler mutants: select the
wrong case arm, drop a used let, capture the wrong lexical level while inlining,
and drop an exported function. Each compiler is independently seed-checked and
built. A mutant is killed only by the fixed successful-call contract, checked
core preservation, or the host export contract. A mutant that fails seed
checking, fails to build, times out, or reports an unrelated host failure does
not count as killed.

## Reproduction and limits

Run `BEND_NO_TELEMETRY=1 python3 tests/compiler-opt/check.py` or the registered
gate runner. The gate writes only its receipt and ignored `.local/compiler-opt/`
products. It uses the pinned seed with `bun --no-env-file`, performs no dependency
installation, and does not read `.env` files or use network services.

Corpus equality is a deterministic regression claim, not a universal refinement
proof. Pure source values remain the observational contract; bounded evaluator,
parser, stack and arena resources remain explicit. Every current top-level
function is exported, so the export-preserving function-DCE instance keeps every
function. Future private functions, primitive literals, modules, and new IR
constructors need fresh fixed domains and gates before broadening this claim.

## Development failure retained

An intermediate Bun build failed with `bend: memory fault (machine stack
overflow?)` on six larger programs: arena-overflow, deep-call, deep-stack, the
64-successor observer, and generated calls-64/calls-128. The fixed-point check
compared entire rendered books with recursive `String.eq`; the replacement
compares bounded core structure. The rebuilt full corpus and standalone pass
runs passed in both lanes. The failure was a compiler host-stack failure, never
source Invalid, Unsupported, or a successful optimization. The retained
`receipts/development-failure.json` names the observations and its provenance
limit: the intermediate executable was replaced and its hash was not retained.
