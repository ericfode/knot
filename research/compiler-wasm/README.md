# First compiler milestone: source to actual Wasm

Implemented and verified on 2026-09-26: Knot is a Bend 2 compiler for the precise
no-Base `knot-enum-1` profile. It lexes, parses, resolves and checks source, then
emits a real Wasm module directly in Bend. A separate Bend evaluator interprets
checked terms. The compiler never uses evaluator output to replace function
bodies. [Reproduction commands](../../tests/compiler-wasm/README.md), the
[source contract](../../src/SPEC.md) and [machine-readable ABI/budgets](../../src/CONTRACT.json)
define the exact supported behavior.

The compiler itself is seed-built for native and Bun execution. It does not yet
compile its own source or emit GPU programs. This milestone is a nullary-enum
slice within S1; owned constructor fields and structural recursion remain open.

## Acceptance audit

| Requirement | Current evidence |
|---|---|
| Semantics and emission implemented in Bend | src/lex.bend, parse.bend, catalog.bend, scope.bend, check.bend, eval.bend, wasm.bend and wasm-bytes.bend; Python/Node only build, invoke, inspect and compare |
| Real source-to-Wasm execution | 25 source programs, 90 fixed calls; native/Bun compilers emit identical modules, all independently decoded, validated, instantiated and run on Node |
| Independent value oracle | Source-machine environments and frames in eval.bend; no emitter import. Literal expectations and separately invoked upstream interpreter constrain the shared frontend |
| Required negative controls | Affine reuse, erased live use and missing match arms rejected with exact diagnostics; 32 Invalid/Unsupported fixtures across both compiler/evaluator lanes, 64 rejection pairs |
| Distinct outcomes and bounds | Invalid=2, Unsupported=3, Exhausted=4, HostFailure=5, InternalFailure=6; 44 boundary observations include every stage's exhausted budget, exact output/evaluation limits and host failures |
| Seed and host contract | Bend 2.0.29 revision 574b6d39a235b539eb19a5c532993a0abb3d11ad; actual toolchain/dependency hashes in trust.json; Node 22.22.3 on macOS arm64; scalar Wasm v1, sections 1/3/7/10, no imports or memory |
| Deterministic laws and hostile checks | Complete runtime-PROOF entry fills all 18 frontend/checker/runtime laws; seven new type-correct semantic mutants killed by unchanged observations |
| Targeted semantic review | 344 checks, 104 completed provider responses; one fixture warning adjudicated false-positive, no confirmed defect; context limits retained in PERCH_REPORT.md |
| Preserve existing package/GPU work | Published ByteOutput consumed by exact package identity through its checked API; no package implementation or adaptive-task prototype files changed |
| Durable plan and generated code | Updated subset/backend plans; 25 actual .wasm files with independent .wat disassemblies under tests/compiler-wasm/generated; Whiteboard session ec417549-1568-412d-b7e2-43ccc36acbd5 receives the actual pipeline and artifact excerpts |

[Execution receipt](../../tests/compiler-wasm/receipts/wasm.json) records every
command, source/tool hash, reference call, evaluator result, Node result, boundary
and mutant. [Trust inventory](TRUST.md) names the actual loaded Base/ByteOutput
and native/unsafe dependencies. [Law review](LAW_REVIEW.md) gives the abstraction
relation, domain partitions and proof boundaries. [Perch report](PERCH_REPORT.md)
retains the full review attribution and adjudication.

The earlier parser gate was rerun: 14 fixtures, 24 boundary observations, four
laws and four semantic mutants passed. The checker gate was rerun: 49 fixtures,
98 observations, ten depth checks, 16 catalog bounds and seven mutants passed.
Their current Bend input hashes match. The checker receipt retains an earlier
SPEC.md hash: a later prose correction changed "enumerate those domains" to
"supply domain-valid arguments from literal observations". Its source and test
expectations did not change. The final Wasm receipt hashes the corrected SPEC.md.

## Flag: actual generated program

`tests/subsets/s1/flag.bend` defines Off/On, flip and main. The resulting
[68-byte module](../../tests/compiler-wasm/generated/flag.wasm) executes
flip(0)=1, flip(1)=0 and main()=1. Its actual
[disassembly](../../tests/compiler-wasm/generated/flag.wat) shows a local load,
equality, typed if/else and direct call. No source is evaluated during emission.

| Artifact | SHA-256 |
|---|---|
| src/eval.bend | ba318e44c13355cd9731514615b2fa0a68d9c4087bbf3dbc847dea12d62bc7cc |
| src/wasm.bend | e03d155aab051e37e699cad23c313837cc1fdb89bec70d02bff5c391712586a6 |
| src/wasm-bytes.bend | d828d6078ae84973ce2da7d3a5d47ccc7cceb6eeb3300319f142d25eec970aac |
| generated/flag.wasm | bec4dba4714d72ede6f34df093b4ba4fcda05c944c2b731686d1e53b64b0e609 |
| receipts/wasm.json | 83dd96a7e93dcc38731dec399c0faf13e5c478ae379749d2956a570efeea58f9 |

## Limits and next increment

This is finite differential and mutation evidence, not a universal checker
soundness or compiler refinement theorem. Four new laws are quantified machine
transitions; three are concrete LEB normalizations. The pinned seed checker,
primitive/native runtime, checked byte package and Wasm engine remain trusted.

Every raw Wasm argument must belong to its declared enum. The evaluator enforces
that domain; the Node adapter checks live arity and the profile-wide 0..255 range.
No general owning heap, closure runtime, field allocation, recursion or throughput
claim is made. Resource exhaustion is inconclusive. Semantic failure leaves an
existing output untouched, while host write failure can leave a partial file;
only successful exit plus a fresh Built record and verified bytes proves emission.

Next extend the checked core to owned fields and structural recursion, then
define the allocation/drop and continuation representation shared by Wasm and
WebGPU. Preserve these enum controls while widening the source profile. The
existing 38-run handwritten GPU probe is historical device evidence; it does not
establish compiler-generated GPU code. Full self-hosting remains the later S4
closure/bootstrap gate.
