# OutputBuilder style campaign

## output-builder-grammar-1 — preregistration

Recorded before generating or judging the candidate. Owner: packages/output_builder.
Implementation model: GPT-6 Astra, high reasoning, as selected for this batch.

Reading problem: `attach` accepts a checked byte count; `combine` accepts a
Boolean capacity decision. Both repeat failure/success handling and reconstruct
Buffer with `length + suffix length` and Join. The clean Empty/Chunk/Join grammar
is obscured by two separate completion protocols for the same tree operation.

**Author taste hypothesis, not a user-approved preference:** normalize admission
to `Result<Error,U32>` and give it one counted-join operation. Append's scanner
already yields exactly that result; compose can use the existing lazy guard to
yield its known right count. The recurring grammar becomes “admit count, join
suffix.” That is a shared mechanism, not new branding or an extra data wrapper.
Retain attach/combine as compatibility adapters because accepted tests use them.

One candidate: add internal `join(admitted,builder,suffix)`; route attach and
combine through it. Do not change scan, guard, byte/text emit, constructors,
public signatures or the byte-validation-before-capacity sequence. Candidate
body changes: attach, combine, new join. Style review includes the whole bytes
module (17 declarations including three datatypes, below the 24-unit limit)
because helper context changes propagate. Reuse baseline ratings only when the
style tool's complete identity check permits it.

Fixed contract: exact character/byte order, byte range 0..255, first examined
invalid-byte error before capacity at that element, no partial builder, left
capacity on compose, checked U32 length, retained snapshots, O(N+K) finishing.
Raw Buffer/helper callers must satisfy the existing documented invariant.
Source/native raw-Char versus JS scalar-text limitation is unchanged; no GPU,
Wasm or universal checked-byte history theorem is claimed.

Baseline source, contract, laws, proofs, independent models, immutable runtime
assertions, performance fixture and original mutation harness are frozen under
`campaigns/output-builder-grammar-1/baseline/` with full SHA-256 values in
`hashes.json`. The existing project receipt's 16 bytes declarations match the
baseline source identity; extracted distributions are in baseline/style.json.
For attach/combine, conceptual P(target) was 0.90/0.95, delight 0.83/0.79,
memetic 0.09/0.04. These are advisory baseline judgments, not evidence of a bug.

Acceptance: first candidate must pass the pinned complete proof/type/quantity
entry and unchanged native/JS assertions, all nine semantic mutants, and four
scaling sizes. At most one compiler-diagnostic retry; preserve failed source
and its diagnostic before using it. Assertions and laws remain byte-identical.
Only a mutation's literal text locator may move, retaining the same operation's
semantic defect and exact unchanged observing assertion. Keep release-time
receipts and published identity immutable; no publication or dependency update.

Candidate state at preregistration: not generated; the results below were added after the recorded experiment.


## Result — accepted unreleased, not a full style pass

One candidate was generated with GPT-6 Astra/high as assigned. The first pinned
compiler run accepted the complete proof closure; **zero diagnostic retries**.
Exact first source and stdout/stderr are retained as `candidate-first.bend.txt`
and `first-compile.*`. No second candidate or score-hunting rerun was made.

Kept change: `join` is the single transition from admitted byte count + prefix
builder + suffix tree to the resulting counted tree. `attach` supplies a Chunk;
`combine` admits its existing right count through guard. The public API and raw
compatibility helper signatures remain unchanged. Neither scanner nor either
emitter changed. The concrete benefit is one length/tree update and one error
propagation path, instead of parallel success implementations with different
input protocols. No new datatype, stored state or capacity invariant is added.
The tradeoff is an extra helper call and a constant-size admission closure on
compose; no speed improvement is claimed.

Before (`bytes.bend` baseline attach/combine success arms):

```bend
      Done{Buffer{cap,U32.add(n,k),Join{t,Chunk{values}}}}
```
```bend
      Done{Buffer{cap,U32.add(left_n,right_n),Join{left,right}}}
```

After (compatibility adapters share the same transition):

```bend
  join(result,b,Chunk{values})
```
```bend
  join(guard(ok,Limit{},u => Done{right_n}),Buffer{cap,left_n,left},right)
```

The shared success arm is now:

```bend
    case Done{k} Buffer{cap,n,prefix}:
      Done{Buffer{cap,U32.add(n,k),Join{prefix,suffix}}}
```

### Deterministic acceptance

- Pinned 2.0.29 type/quantity/proof check passed first attempt; direct book_valid
  inspection reports **zero holes**. All 27 accepted laws remain byte-identical.
- Native **14 checks**, JS scalar-text/bytes **13 checks** passed. The independent
  conformance source, both reference models, contract, proof terms and scaling
  assertion body match their frozen hashes exactly.
- All **nine mutants** first typechecked and compiled, then failed the intended
  unchanged runtime assertion. No survivor, parse/type error or harness failure
  counted as a kill. Only drop-right-bytes' literal locator changed: it now
  replaces combine's right-tree argument with Empty, preserving the original
  compose-only defect, old [0,97] witness, and assertion. See mutation-locator.json.
- Tiny, uneven, empty and one-byte workloads passed at **1000/2000/4000/8000**
  chunks with exact independent outputs and unchanged linear node/unit census.
  Current warm process times were approximately 0.010/0.017/0.031/0.062 seconds;
  these include generation, finish, reference checks and process overhead.
  They preserve the existing scaling behavior, not an isolated latency claim.
- Release-time evidence and RELEASE.json remain unchanged. New gate output is
  `campaigns/output-builder-grammar-1/gates.json`; the root evidence/gates.json
  was not overwritten. The pinned remote package and all dependency hashes stay
  unchanged. Only working bytes.bend is an **unreleased revision**.

The gate was run by importing scripts/gate.py and setting its EVIDENCE variable
to this campaign directory before main(); BUILD remains the package's ignored
build directory so generated relative imports are unchanged. New proof.json
records direct book_valid rather than borrowing the release-time hole receipt.

### Semantic Perch

All 14 byte implementation definitions received five selected parsed rules:
machine arithmetic, borrow lifetime, effect boundary, growing-prefix copying,
and loop-invariant work (**70 answers, 14 completed provider responses**).
The new bounded LAW_REVIEW packet received all eight law rules and the dedicated
linear-assembly rule (**9 answers, one completed response**). No findings.
Original request IDs, source/context hashes and raw probabilities are retained
in semantic.receipt.json and law-semantic.receipt.json. These are advisory; no
rule threshold or shared configuration changed. Existing bad-control misses
remain historical limits, not erased by this result.

### All three style axes

The complete candidate bytes module — 14 definitions and three datatypes —
received **51 ratings across 17 completed requests** from `jev-1.13.0`. This
covers all changed units and their propagated helper/datatype context, below the
24-declaration batch cap. --reuse pointed at the initial project receipt;
**zero units qualified** because the source/context identities changed. No
unchanged text-module ratings were requested. Full distributions and identities
are in style.json; extracted matching baseline distributions are baseline/style.json.

Results: conceptual **16 meet, one uncertain**; delight **12 meet, three below,
two uncertain**; memetic **zero meet, 16 below, one uncertain**. Style exit 3 means
attention, not provider failure. No declaration meets all three; this batch is
not a full style pass. Builder and Error datatype context hit the four-user cap;
all definition context was untruncated. Base primitive resolution remains
explicitly unavailable. All rated source identities remained current.

P(level >= 3) by declaration (target threshold 0.60):

| Unit | Conceptual | Delight | Memetic |
| --- | ---: | ---: | ---: |
| Tree | 0.79 | 0.73 | 0.14 |
| Builder | 0.80 | 0.59 | 0.08 |
| Error | 0.81 | 0.84 | 0.33 |
| empty | 0.99 | 0.66 | 0.00 |
| length | 0.84 | 0.16 | 0.00 |
| limit | 0.66 | 0.12 | 0.00 |
| guard | 0.95 | 0.86 | 0.22 |
| scan | 0.92 | 0.82 | 0.36 |
| join | 0.92 | 0.62 | 0.09 |
| attach | 0.95 | 0.67 | 0.09 |
| append | 0.85 | 0.70 | 0.55 |
| fragment | 0.89 | 0.70 | 0.26 |
| byte | 0.86 | 0.57 | 0.27 |
| combine | 0.97 | 0.88 | 0.32 |
| compose | 0.92 | 0.67 | 0.39 |
| emit | 0.94 | 0.81 | 0.03 |
| finish | 0.54 | 0.19 | 0.04 |

Changed-unit comparisons:

| Unit | Conceptual before → after | Delight before → after | Memetic before → after |
| --- | --- | --- | --- |
| attach | 0.90 → 0.95 | 0.83 → 0.67 | 0.09 → 0.09 |
| combine | 0.95 → 0.97 | 0.79 → 0.88 | 0.04 → 0.32 |
| join | new → 0.92 | new → 0.62 | new → 0.09 |

The tradeoff is visible: attach's delight fell 0.83→0.67 while combine rose
0.79→0.88. Combine's memetic mass rose 0.04→0.32 but remains below target;
the new join's 0.09 does not support a memetic success claim. I retain the
change for the explicit shared transition and passing immutable gates, not
because every reading judgment improved. One-shot model differences do not
measure a psychological effect or establish statistical improvement.

Remaining work: all 17 memetic axes need attention or remain uncertain; length,
limit and finish are below delight, byte and Builder uncertain. No decorative
abstraction is proposed just to make these projections more unusual. A future
bounded batch should test a concrete admission vocabulary at append/compose
against actual reading experience, keeping the same immutable observations.
Datatype context caps must remain visible in any comparison. No additional
candidate is authorized by this batch's acceptance itself; the coordinator
selects the next increment. No shared campaign state or rubric was edited.
