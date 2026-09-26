# OutputBuilder parsed Perch pass — 2026-09-26

**No code needed changing.** This pass made 21 live requests with 21 completed
responses from `jev-1.13.0`: 100 source-rule answers over 20 parsed declarations,
plus nine checks of the current law packet. No findings were reported. Confirmed,
false-positive, duplicate and unresolved finding counts are all zero. A clean
model result is advisory, not a correctness claim.

New this pass: bounded parser-backed audit, helper-context inspection, current
proof check, release-identity verification, this report and receipts. The
implementation, laws, nine semantic mutant kills, runtime conformance, scaling,
and publication are earlier work; no new implementation success is claimed.
No stronger repair model was needed because no defect was confirmed. No publish,
paused-campaign continuation, shared-file edit or rule change occurred.

## Targets and exact coverage

Both implementation files were checked through `npm run lint -- <path> --rules
<names> --json`, which fans out over actual parsed definitions. Each listed
unit received exactly these five relevant rules:

- `bend-machine-arithmetic`, `bend-borrow-lifetime`, `bend-effect-boundary`;
- `perf-growing-prefix-copy`, `perf-loop-invariant-work`.

| Target | Actual parsed units (5 checks each) | Checks | Provider responses | Receipt |
| --- | --- | ---: | ---: | --- |
| `main.bend` | empty, fragment, compose, append, character, emit, finish | 35 | 7 | [main](evidence/perch-parsed/main.receipt.json) |
| `bytes.bend` | empty, length, limit, guard, scan, attach, append, fragment, byte, combine, compose, emit, finish | 65 | 13 | [bytes](evidence/perch-parsed/bytes.receipt.json) |
| `LAW_REVIEW.md` | All eight `law-*` rules plus `output-builder-linear-assembly` | 9 | 1 | [law packet](evidence/perch-parsed/law-review.receipt.json) |

[Summary and source identities](evidence/perch-parsed/summary.json) retain full
source hashes, exact rule names and original wrapper receipt paths. Each receipt
retains per-unit source locations, raw probabilities, model and parser identities.
All statuses are `completed`; no zero-coverage or incomplete provider result was
counted. No requests were retried.

Source scope intentionally omits unchanged tests, examples, benchmarks, proof
bodies and reference models from paid review. Their contracts are represented in
the current law packet and checked proof closure. The public code is only 120
lines across the two files, including all material implementation helpers. Fuel,
F32 and GPU rules were not selected because these operations have no fuel,
F32 arithmetic or device entry. Linked indexing and array growth rules were not
selected because the representation uses neither indexing nor reallocation.
Existing rule controls were not rerun unchanged: the previous 79% held-out miss
against the dedicated rule's 80% floor remains a limitation, not erased evidence.

## Actual helper context and limits

Parser profile: `language-pack-1.20-v3+knot-bend-0cd9e831fc413760`, using the
pinned Bend `574b6d39a235b539eb19a5c532993a0abb3d11ad` observer. All 20 units
parsed. Their context provenance says `working-tree`, **truncated=false**.
The configured bounds were 16 helpers, 4 callers, 12 files and 48 KB.

The [context manifest](evidence/perch-parsed/context-manifest.json) was regenerated
without provider calls and compared exactly to receipt provenance. In particular,
`bytes::append` included `attach`, `scan`, `guard`, and Tree/Builder/Error
datatypes; `bytes::compose` included `combine`; finish included emit. Self
recursion remains in the target body. No committed/stale helper was substituted.

Base primitives such as String.append, List.append, U32.add/sub/comparisons remain
marked `unresolved-or-builtin`; type references are also listed there even when
local datatype source is included separately. No missing local implementation
helper or truncation was observed. This partial graph is not type checking,
proof validation or a resolved Base dependency graph. The separate law packet
supplies the contract context; implementations do not directly import their law
files, so this pass does not claim the parser inferred those reverse imports.

## Adjudication and verification

No above-floor finding required repair. I inspected the arithmetic and cost
paths directly: bytes::scan increments only after count < room; append computes
room = cap-n under the documented checked-API invariant; compose compares the
right length with that room before addition. Raw Buffer forging remains outside
that invariant, as already documented. Tree emission copies disjoint fragments
into a suffix rather than repeatedly copying the growing prefix.

Some arithmetic scores were weak despite no visible arithmetic (up to 77%
broken in text units, below that rule's 80% floor). These probabilities supplied
no counterexample; correct code was left intact. No false-positive *finding*
was recorded from a below-floor score.

Fresh validation: `scripts/bend-reference packages/output_builder/PROOF.bend
--check-only` returned **All terms check.** The complete imported proof entry
contains all 27 filled law declarations. All 12 published closure SHA-256 values
still match RELEASE.json. [Proof output](evidence/perch-parsed/proof-check.txt)
and [closure comparison](evidence/perch-parsed/summary.json) retain the result.
Native/JS conformance, mutation and scaling evidence were not rerun because no
source changed. Their previously measured source identities remain unchanged.
The published hash stays `0xc409b77d3230ca33374caf6b0993f0cb`.

## Two existing mechanisms worth showing

These are excerpts of earlier implementation, **not changes made this pass**.
There are no genuine competing implementations here, so no ordinal style
comparison or invented ranking was requested.

`main.bend:24–31`:

```bend
def emit(builder: Builder, suffix: String) -> String:
  match builder:
    case Empty{}:
      suffix
    case Chunk{text}:
      String.append(text, suffix)
    case Join{left, right}:
      emit(left, emit(right, suffix))
```

The suffix absorbs the continuation. A join puts the right output into the
suffix before emitting the left, so the final order is left then right. Each
leaf copies its own fragment once; no growing prefix is revisited. The same
three-case algebra handles append, composition, empty nodes and skewed trees.
The compact payoff is structural, not a claim of bounded stack use on all targets.

`bytes.bend:36–42`:

```bend
def scan(values: List<&2,U32>, +room: U32, +count: U32) -> Result<Error,U32>:
  match values:
    case Nil{}:
      Done{count}
    case Con{+h,t}:
      guard(U32.is_le(h,255),InvalidByte{h},u =>
        guard(U32.is_lt(count,room),Limit{},v => scan(t,room,U32.add(count,1))))
```

The two guards encode the error order directly: validate the byte, then its
capacity. Each continuation is a closure; guard invokes it only on True. Thus
failure cannot evaluate the next recursive scan or increment count, and 256 is
reported as InvalidByte even when capacity is zero. The contract and control
flow can be read in the same order.

Shared follow-up proposal: none required by this pass. Keep the prior dedicated
rule's held-out miss visible and Base-context limitations explicit. No shared
review log was edited under this chat's ownership boundary.
