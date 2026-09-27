# IntMap style campaign

## Batch int-map-paths-1 — pre-registered hypothesis

Recorded before candidate generation or judgment. Model: GPT-6 Astra, high
reasoning, as assigned. One substantive candidate, at most one separately
recorded compiler-diagnostic retry. Scope: branch pruning and the mirrored
get_path/set_path/remove_path family; no public API change or publication.

**Reading problem:** `branch` enumerates five constructor outcomes to express
one exception: two empty children collapse to empty. The remaining outcomes
manually unpack/reconstruct Entry and Branch values even though those children
should pass through unchanged. This makes the reader trace representation
cases before seeing the pruning law.

**Author's taste hypothesis, not a user-approved preference:** a joint match
with `Tip{} Tip{} -> Tip{}` and a single binding fallback `a b -> Branch{a,b}`
will express a small smart-constructor algebra directly. The felt rhythm is
“two tips vanish; otherwise branch.” Keep the established Tip/Entry/Branch and
low/high/path vocabulary; add no branding or new indirection. Do not dilute the
existing False/True symmetry of get_path, set_path, or remove_path.

**Fixed contract:** same empty/empty collapse and exact fallback for arbitrary
children; public reachable maps remain persistent, depth32 over every U32 bit,
with absence distinct from stored zero. Unrelated keys, exact size/fold contents,
low-bit-first fold order, and combine(left,right) on overlaps are preserved.
Removal prunes empty branches without promoting children across depths.
The package's SPEC.md and INTERFACE.md are frozen for this experiment.

Baseline source and immutable independent assertion identities are recorded
below and in [preregistration.json](campaigns/int-map-paths-1/preregistration.json).
Full snapshots are in `campaigns/int-map-paths-1/baseline/`. Model, laws, proof
bodies, fixtures, conformance and scaling assertions remain byte-identical.
Mutation text locators may change only if the refactor invalidates them; any
adaptation must retain the semantic violation and unchanged observing assertion.

| Frozen file | SHA-256 |
| --- | --- |
| `main.bend` | `e3e62df90a23f8f80ad6a0730f434b16035d1dda43fb93764fe03504d1c3f83a` |
| `SPEC.md` | `1f6232d5b627b2f7f4f89f02b8b7bc99424d4823da9ad5a147cca620f71cec06` |
| `INTERFACE.md` | `58fdd3b00a73fce48838fd9e2168df559ed1c948d9038fdfb562c0181f7dbedb` |
| `model.bend` | `62ede4569dd2d11dd8d23734afbaca21710f58bc73a14cee5fb82efe684109fa` |
| `LAWS.bend` | `95f0f9551cfcd8b5e0b16437405177f4e79f8305c4b9a503bfda68d2a9eea311` |
| `PROOF.bend` | `64a59a7d38a2daac8bdbf31006c27f6de88733edbca5176e953386881e7715e6` |
| `fixtures.bend` | `22374c110d4043af068e92d82c763022abebc10e292a5edd278f09f765a41b5e` |
| `conformance.bend` | `987b5f1fe814cefdc58ad39f95618bfcc58002983f021825c3c024b8c32b1de6` |
| `scaling.bend` | `cb6cb77a20a60026e7efd9a65e6d945f5dce923f299614e3899e4f59b57e283b` |
| `benchmark.bend` | `77a420bb48003b31e4f24862fffe3227d629fc81f809246386919f5c040549b2` |
| `example.bend` | `58bb16bafcdb56f6e488d49e9e5fabc40c4930e688a8d65fca48cc7af1a309f6` |
| `release.bend` | `71f59b2447b6c0e769ec6d73ce43d7e060d4f31226fb7367875f33d24d98992f` |
| `scripts/mutations.py` | `93841cefb561d6f23e693bdfaa56c485ba112c4c77cd85b5745561768c005c17` |
| `scripts/performance.py` | `3c705578b64452153838a2ba63ec53a68f7984026c5ec9e5c1380dbff901755d` |

Baseline ratings were read from the actual compressed project receipt, not
inferred from rankings. [Extracted rows](campaigns/int-map-paths-1/baseline-style.json)
preserve distributions, model, parser/context/rubric identities. Probability
mass at levels3–4 is the current target measure (pass >=0.60):

| Declaration | Compression | Delight | Memetic |
| --- | ---: | ---: | ---: |
| get_path | 0.85 | 0.94 | 0.18 |
| set_path | 0.93 | 0.95 | 0.32 |
| branch | 0.61 | 0.81 | 0.07 |
| remove_path | 0.93 | 0.92 | 0.26 |

Planned acceptance: complete proof checking; native/JS release conformance;
all11 type-correct semantic mutants; scaling/model equivalence at64..4096 for
dense and shared-prefix keys; targeted semantic Perch and all three style axes
for branch plus the three path declarations. Use the baseline receipt for exact
identity reuse; changed file/helper identities require fresh rows. Preserve
release-time receipts. Accept only a concrete reading payoff with deterministic
acceptance, recording unmet style axes rather than claiming a full style pass.

## Recorded outcome — accepted, unreleased

One candidate; first proof/type/quantity check passed. No compiler-diagnostic
retry and no later source repair. Main source SHA-256 is now
`53f771454f0e13b7128494a45e4ace529740eeb60c8eccb1f7724532359048d2`.
The first generated source and first compiler response remain in
[candidate-first.bend.snapshot](campaigns/int-map-paths-1/candidate-first.bend.snapshot)
and [first-result.json](campaigns/int-map-paths-1/first-result.json).

Before:

```bend
def branch(-V: Data, lo: IntMap<V>, hi: IntMap<V>) -> IntMap<V>:
  match lo:
    case Tip{}:
      match hi:
        case Tip{}: Tip{}
        case Entry{k,v}: Branch{Tip{},Entry{k,v}}
        case Branch{a,b}: Branch{Tip{},Branch{a,b}}
    case Entry{k,v}: Branch{Entry{k,v},hi}
    case Branch{a,b}: Branch{Branch{a,b},hi}
```

After:

```bend
def branch(-V: Data, lo: IntMap<V>, hi: IntMap<V>) -> IntMap<V>:
  match lo hi:
    case Tip{} Tip{}: Tip{}
    case a b: Branch{a,b}
```

This exposes the exceptional empty/empty case and the identity of every other
child pair directly. There is no extra helper, vocabulary or traversal. The
get/set/remove path bodies retain their False/True symmetry byte-for-byte.
Acceptance is the author's reading judgment supported by fixed deterministic
gates; the user has not specifically endorsed this taste hypothesis.

### Verification

- Complete pinned proof checking passed, including unchanged auxiliary projection
  laws that quantify over arbitrary children. The existing 23 filled declarations
  retain the published proof boundary; no stronger refinement claim is added.
- Native CPU and JavaScript release conformance and example passed: full32 keys,
  persistence, absence, exact fold order/seed, and noncommutative union observations.
- All11 mutants passed typechecking and failed their intended original assertion.
  No locator adaptation, assertion change or law weakening occurred.
- Existing scaling/list-model gates passed at64,256,1024,4096 for both backends
  and dense/shared-prefix layouts. A descriptive paired4096 comparison used one
  warmup then five alternating samples: native medians37.64ms ->37.42ms;
  JavaScript55.64ms ->55.48ms. No material regression was observed in this
  workload; concurrent process timings do not establish speedup or universal
  nonregression. The optional comparator initially omitted fixtures.bend from its
  copied closure; copying all frozen Bend inputs fixed that harness setup error.
  Candidate source did not change.
- Targeted semantic Perch completed29 checks in three provider responses:10 each
  on branch/remove_path and9 on a candidate-specific law packet. No finding
  reached its floor. Model jev-1.13.0; all reported source context was untruncated.
  Source contexts were bounded to16 helpers,12 files,48000bytes,4 callers; Bool
  was marked unresolved-or-builtin for remove_path. These are advisory judgments.
  The initial CLI invocation named two source targets but returned only branch;
  remove_path was therefore checked in its own invocation. Future semantic calls
  should use one named target each and verify the actual receipt coverage.
- Hash checks confirm the fixed contract, model, proof and assertion inputs are
  unchanged. RELEASE.json and every tracked release/historical receipt remain
  identical to the pre-candidate commit. No publish or dependency update occurred.

Evidence: [gates](campaigns/int-map-paths-1/gates.json),
[mutants](campaigns/int-map-paths-1/mutations.json),
[performance](campaigns/int-map-paths-1/performance.json),
[paired timings](campaigns/int-map-paths-1/performance-comparison.json),
[release preservation](campaigns/int-map-paths-1/release-preservation.json),
[branch review](campaigns/int-map-paths-1/semantic-branch.json),
[caller review](campaigns/int-map-paths-1/semantic-remove_path.json),
[law review](campaigns/int-map-paths-1/semantic-laws.json),
[machine-readable outcome](campaigns/int-map-paths-1/outcome.json).

### Three independent style axes

Each cell is baseline -> candidate probability mass at levels3–4; target >=0.60.

| Declaration | Compression | Delight | Memetic |
| --- | ---: | ---: | ---: |
| branch | 0.61 ->0.92 | 0.81 ->0.77 | 0.07 ->0.09 |
| get_path | 0.85 ->0.86 | 0.94 ->0.94 | 0.18 ->0.20 |
| set_path | 0.93 ->0.93 | 0.95 ->0.94 | 0.32 ->0.30 |
| remove_path | 0.93 ->0.91 | 0.92 ->0.91 | 0.26 ->0.29 |

Four fresh rows,12 axis ratings, zero reused units. File/helper hashes changed
so the baseline receipt could not be reused even for unchanged path bodies.
Model jev-1.13.0; parser bend-2.0.29-574b6d3-observer-v2; unchanged rubric hash
`a2e20d01461c2d0fb07aaa8cb577423693b73d07617318e9e30ed674186a01d3`.
All four style contexts were untruncated, with the same16/12/48000/4 bounds.
Full distributions and source/state/helper identities are preserved in
[baseline-style.json](campaigns/int-map-paths-1/baseline-style.json) and
[style-after.json](campaigns/int-map-paths-1/style-after.json).

Compression and delight meet target on all four declarations. All four remain
below the memetic target: zero declarations pass all three axes. The command
returned attention status3. Branch compression rose substantially in this
single judgment; delight fell slightly while staying above target. Small
fluctuations, including ratings of unchanged bodies, are not significant
evidence. There is no all-axis or whole-package style pass.

### Remaining work

The empty-pair rule is now concise enough that branding or another abstraction
would add ceremony. Leave it stable. A later bounded batch can examine the
shared low/high/observe path vocabulary as a family, requiring an actual reading
problem before proposing a change. The coordinator can use this tiny helper
and its unchanged callers as role/size calibration evidence alongside larger
families; low memetic scores alone establish neither a defective rubric nor
a reason to rename code. Remaining package declarations still need campaign
coverage. No second candidate was generated in this batch.
