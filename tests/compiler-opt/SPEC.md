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
growth. The shared manifests and benchmark generator are read on every run;
new cases run all applicable differentials without requiring a baseline edit.
`extensions.json` and `freeze.py` provide an explicit append-only freeze of new
off hashes. See the README for the extension procedure. The gate rebuilds the unoptimized modules in native and Bun, requires their exact byte
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
- Compare canonical function-body and signature observations after one and two pipeline applications. The original baseline retains its fixed-point assertions; later domains record convergence without requiring it. Datatypes, token spans and caches are outside this rendering.
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

Private scratch copies introduce seven type-correct compiler mutants: select the
wrong case arm, drop a used let, capture the wrong lexical level while inlining,
drop every core function, exhaust at the round limit, duplicate boxed literals,
and omit one non-entry Wasm export while retaining its function and working main. Each compiler is independently seed-checked and
built. A mutant is killed only by the fixed successful-call contract, checked
core preservation, or the host export contract. A mutant that fails seed
checking, fails to build, times out, or reports an unrelated host failure does
not count as killed. Wrong-value, core-preservation, ABI, optimization-availability
and resource-preservation kills have separate labels. A removed export also
produces a separately classified HostFailure; that failure does not supply the ABI kill.

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

## Review round 2: availability and representation

The separately frozen `regressions.json` adds 11 calls across `r_4_13`,
`r_20_13` and `arena-sharing`. The first two chains converge slowly; default and
maximum CLI budgets must compile them and preserve the seed/evaluator/Wasm
values. A successful optimization need not reach a fixed point: every completed
round has passed core rechecking, so the last verified book is returned after
eight rounds. The direct zero-round helper still has no completed result and
retains its original Exhausted law. Depth and byte-budget failures are unchanged.

Literal propagation is permitted only for enum-only datatypes. A nullary
constructor of a fielded datatype allocates a cell; replacing its let-bound
references with values would duplicate that allocation. Both the literal
recognizer and reference rewrite guard the type representation. The near-arena
fixture shares one Zero cell eight times per Row and must succeed under Fold
and the full pipeline whenever its fixed off observation succeeds. No DCE
assumption supplies this allocation guarantee.

Each pass checks ordered export names, parameter quantities/types and result
types against its input before verifying output bodies. Datatypes are retained
from the input by construction. Four added checked equations cover final-round
termination, enum propagation, boxed retention and missing-export rejection.
The original twelve laws and 43 core controls remain unchanged. Fourteen new
literal controls cover ordered ABI changes, body rechecking, reference
representation and round limits in both compiler hosts.

Direct receipts use the runner's normalizer before writing. The complete audit
texts are compared in memory; normalized text hashes and byte lengths are
retained instead of repeated successful IR dumps. Historical raw-root receipts
were replaced by the matching normalized runner output, without altering their
observations.
