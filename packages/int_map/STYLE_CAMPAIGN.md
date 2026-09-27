# IntMap style campaign

## Follow-up edit-locality-1 — retained additive proof

The user's 2026-09-27 follow-up authorizes proving the shared recurrence's lookup
consequences while preserving runtime and all prior proofs. The
[bounded report](campaigns/edit-locality-1/README.md) retains the preregistration,
first parser failure, single successful diagnostic retry and complete gates.
Two projection premises yield endpoint lookup and separated-path preservation;
raw Branch and pruning branch discharge those premises, giving four exact public
specializations. Eight additional laws and all 23 original laws check; runtime,
contracts, assertions and historical receipts remain byte-identical.

Keep the additive proof as a reusable explanation. Equality bookkeeping remains
visible: the generic declarations have uncertain compression and below-target
memetic/anticipation/payoff results. Perch's observer cannot parse imported
template-law fills; an exact combined review copy receives supplementary ratings.
All eight pairs are reviewed, with three meeting all five role-scaled targets.
The expanded complete composition remains below all three expressive targets.
Thirty-one targeted semantic checks report no findings. No complete style pass,
further candidate, publication, or new performance comparison is claimed.

Shared Perch v6, merged at `7750e5b`, incorporates the user's separate observation
that vacuity does not preclude memetic appeal. Historical v5 scores below retain
their original meaning; they are not reinterpreted as v6 judgments.

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

## Batch int-map-paths-2 — pre-registered hypothesis

Recorded before generation. Author model: GPT-6 Astra, max reasoning. The new
component dispatch asks for a small trial and permits retaining a concrete
reading improvement with honest below-target style status; it supersedes the
old all-target adaptive-task pilot prerequisite for this batch. One substantive
candidate, at most one separately recorded compiler-diagnostic retry.

**Reading problem:** set_path and remove_path repeat the same descent and sibling
retention, with only the terminal node and rebuilding operation differing. Lookup
already provides the three-case Nil/False/True traversal grammar.

**Author hypothesis, not a user-approved taste judgment:** put the shared edit
recurrence beside lookup, then define insertion and deletion by their endpoint
and rebuilding rule. The reader should learn descent once, then recognize how
edits rebuild exactly the traversed spine. Keep low/high/value and the accepted
branch(Tip,Tip) collapse. Avoid an abstraction for lookup itself: it has no
rebuilding obligation, and forcing it into an edit fold adds irrelevant policy.
The requested inducer was decoded and read before design; its repeated paired
forms suggest a shared structure with visible variation, not new terminology.

**Candidate shape:** one edit_path template parameterized by a closed polymorphic
branch constructor and a runtime terminal IntMap. set_path selects raw Branch
and Entry(key,value); remove_path selects existing branch and Tip. These are
compile-time policies, avoiding reusable affine closures and runtime callback
allocation. Verify the pinned compiler accepts specialization and unchanged
inductive proofs; reject if it does not after the single allowed retry.

**Fixed contract:** every U32 bit, persistent versions, None versus Some(0),
depth 32 and no child promotion, low-bit-first fold order, combine(left,right)
on overlaps, and existing work/allocation bounds. SPEC/INTERFACE and all
independent model, law, proof and assertion bodies remain fixed. Original
mutation semantic violations and observing assertions remain fixed; only text
locators invalidated by the shared recurrence may be adapted with evidence.

[Preregistration](campaigns/int-map-paths-2/preregistration.json) records all
baseline hashes; exact snapshots are in campaigns/int-map-paths-2/baseline.
The baseline includes the accepted int-map-paths-1 branch simplification.

Acceptance gates: complete proofs; native/JS release conformance; all 11
type-valid mutants; existing scaling/list-model checks; paired timings against
the exact baseline because the edit recurrence changes. Run targeted semantic
Perch and current role-aware live style for every changed/new declaration plus
the selected path family, with SPEC.md as fixed task evidence. Preserve full
distributions, role/composition results and context limits. No score retries,
whole-repository inventory, publication or compiler dependency changes.

### Trial outcome — kept under the user-authorized performance budget

The candidate has a concrete reading benefit: one edit recurrence explains the
shared spine reconstruction, and the wrappers expose insertion as (Entry, raw
Branch) and deletion as (Tip, pruning branch). Lookup keeps its matching
Nil/False/True grammar. The cost is a polymorphic template signature plus a
measured slowdown in the larger paired workload. The initial disposition rejected
that tradeoff and restored the prior source. The user then explicitly authorized
up to 20% performance degradation. The same candidate is now retained under that
budget, without regeneration or another style review. Its reading benefit remains
the author's judgment; the performance allowance is an explicit user instruction.
This acceptance does not establish nonregression.

Candidate source SHA-256:
`c4c6e55effd8507d21a184428d36c3711bd282493133139d88782476b0cf0a04`.
Current main.bend equals that first candidate byte-for-byte. The adapted mutation
harness is also reinstated exactly. The temporary restoration of the paths-1
source is preserved as historical evidence in restoration.json; it is no longer
the current source state. All release and paths-1 receipts remain unchanged.

**Before:** insertion and removal each contain the descent/rebuild recurrence.

```bend
def set_path(-V: Data, path: List<&2,Bool>, +m: IntMap<V>, key: U32, v: V) -> IntMap<V>:
  match path:
    case Nil{}:
      Entry{key,v}
    case Con{False{},tail}:
      Branch{set_path(V,tail,low(V,m),key,v),high(V,m)}
    case Con{True{},tail}:
      Branch{low(V,m),set_path(V,tail,high(V,m),key,v)}

def remove_path(-V: Data, path: List<&2,Bool>, +m: IntMap<V>) -> IntMap<V>:
  match path:
    case Nil{}:
      Tip{}
    case Con{False{},tail}:
      branch(V,remove_path(V,tail,low(V,m)),high(V,m))
    case Con{True{},tail}:
      branch(V,low(V,m),remove_path(V,tail,high(V,m)))
```

**Accepted candidate:** share the recurrence and choose its endpoint/rebuilder.

```bend
def edit_path(~join: @-T: Data -> IntMap<T> -> IntMap<T> -> IntMap<T>,
              -V: Data, path: List<&2,Bool>, +m: IntMap<V>, end: IntMap<V>) -> IntMap<V>:
  match path:
    case Nil{}:
      end
    case Con{False{},tail}:
      join(V,edit_path(~join,V,tail,low(V,m),end),high(V,m))
    case Con{True{},tail}:
      join(V,low(V,m),edit_path(~join,V,tail,high(V,m),end))

def set_path(-V: Data, path: List<&2,Bool>, +m: IntMap<V>, key: U32, v: V) -> IntMap<V>:
  edit_path(~(T => lo => hi => Branch{lo,hi}),V,path,m,Entry{key,v})

def remove_path(-V: Data, path: List<&2,Bool>, +m: IntMap<V>) -> IntMap<V>:
  edit_path(~branch,V,path,m,Tip{})
```

The original two-tip branch collapse is unchanged in both. The first generated
candidate passed the complete unchanged PROOF.bend entry; no diagnostic retry
or source repair occurred. Full frozen candidate and response are retained in
[candidate-first.bend.snapshot](campaigns/int-map-paths-2/candidate-first.bend.snapshot)
and [first-result.json](campaigns/int-map-paths-2/first-result.json).

#### Fixed gates and semantic review

All 23 filled laws checked on pinned Bend 2.0.29, including quantity/termination
and the same proof boundary. Native CPU and JavaScript passed all nine
conformance families and the example, including all 32 bits, persistence,
absence versus zero, fold order/seed and noncommutative union. The independent
model and scaling gates passed at 64,256,1024,4096 for dense and 16-shared-low-bit
keys. Every frozen contract, model, law, proof and assertion hash remained fixed.

All 11 mutants typechecked and were killed by their original named observations.
Two text locators changed: discard_set targets the Entry supplied by the new
wrapper; lose_sibling substitutes the original faulty set recurrence for that
wrapper, preserving specifically the False-branch high-sibling loss and leaving
its True branch and deletion intact. The nine other mutants and all observer
assertions were unchanged. Only formatting of unchanged mutation tuples was
restored after the run; AST equality confirmed no harness semantic change.
The exact adapted harness is retained as candidate-mutations.py.snapshot.

Targeted semantic Perch: 39 checks, four completed jev-1.13.0 provider responses,
zero findings: 10 each on edit_path/set_path/remove_path and nine on the bounded
law packet. No reported source context was truncated. Limits were 16 helpers,
12 files, 48,000 bytes and four callers; Bool/U32 builtins remained explicitly
marked unresolved-or-builtin where used. These judgments remain advisory.

Evidence: [gates](campaigns/int-map-paths-2/gates.json),
[mutations](campaigns/int-map-paths-2/mutations.json),
[locator adaptations](campaigns/int-map-paths-2/mutation-locators.json),
[semantic edit review](campaigns/int-map-paths-2/semantic-edit_path.json),
[set review](campaigns/int-map-paths-2/semantic-set_path.json),
[remove review](campaigns/int-map-paths-2/semantic-remove_path.json),
[law packet review](campaigns/int-map-paths-2/semantic-laws.json).
validate.py verifies the exact candidate and adapted harness before running.
Future replays should use an isolated checkout and new output paths; preserve
the original receipts. No unrelated gate was rerun when the exact candidate
was reinstated after the user changed the performance budget.

#### Performance disposition

The first five-pair comparison at 4096 entries showed medians
40.19 -> 41.78 ms native (+3.97%) and 60.48 -> 63.21 ms JavaScript (+4.52%).
That measured concern justified one longer comparison, with no candidate
regeneration or unrelated gate reruns: three warmups per version/backend and
21 alternating paired process samples at each size. Exact baseline and candidate
observations matched throughout.

| Entries | Backend | Baseline ms | Candidate ms | Median change | Slower candidate pairs |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1024 | native | 10.68 | 10.70 | +0.23% | 13/21 |
| 1024 | javascript | 28.57 | 28.89 | +1.12% | 10/21 |
| 4096 | native | 37.07 | 38.21 | +3.06% | 14/21 |
| 4096 | javascript | 55.98 | 59.03 | +5.44% | 19/21 |

The larger workload retained a slowdown on both backends. These process timings
include startup and the full dense/shared-prefix workload on a shared machine;
they do not prove a universal slowdown or identify its exact cause. The generated
JS contains separate template specializations with direct constructor/helper
calls, so no runtime join closure is introduced. However, the endpoint is now
constructed before descent and passed down the spine, and there is an extra
wrapper call. No stronger allocation or causal claim is made. Asymptotic bounds
and structural counts stayed intact, but established nonregression is not
supported. The initial rejection is retained in initial-disposition.json. The
user subsequently authorized a 20% degradation budget, explicitly changing the
acceptance policy after seeing this result. All four confirmation medians are
within that budget. performance-budget.json records the instruction and exact
ratios. This is an acknowledged tradeoff, not a reclassification as nonregression.

[Initial paired timings](campaigns/int-map-paths-2/performance-comparison.json),
[focused confirmation](campaigns/int-map-paths-2/performance-confirmation.json),
and [existing scaling/model gate](campaigns/int-map-paths-2/performance.json)
retain raw samples and observations. compare-performance.py materializes the
frozen versions, so it remains reproducible after source restoration; use a new
output location to preserve original receipts.

#### Role-aware style results

Both runs used rubric v5, SHA-256
`c7de14e38c3b57eec32ad822cfeb08bd1abc5c87ed2e5bdd649c44c1eed316ec`,
parser bend-2.0.29-574b6d3-observer-v2 and jev-1.13.0. SPEC.md was supplied
unchanged as task evidence. The source-blind potential assessment was reused
exactly for the candidate: relevant probability 0.31, low; Galaxy 5 was therefore
not required. Baseline used seven declaration rows plus task/composition reviews;
candidate used eight fresh declaration rows plus composition (nine fresh
responses each, task answer reused on the second run). No declaration rows
qualified for reuse. No model retries or score hunting occurred.

Candidate values below are probability mass at each applicable level; the bar
is 0.60. Supporting M/A/P targets are level 2; edit_path carries level 3.

| Declaration | Role | Compression | Delight | Memetic | Anticipation | Payoff |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| low | supporting | 0.96 / L3 | 0.77 / L3 | 0.87 / L2 | 0.97 / L2 | 0.98 / L2 |
| high | supporting | 0.96 / L3 | 0.72 / L3 | 0.87 / L2 | 0.95 / L2 | 0.97 / L2 |
| value | supporting | 0.97 / L3 | 0.68 / L3 | 0.73 / L2 | 0.98 / L2 | 0.99 / L2 |
| get_path | supporting | 0.84 / L3 | 0.92 / L3 | 0.88 / L2 | 1.00 / L2 | 1.00 / L2 |
| edit_path | leading | 0.94 / L3 | 0.93 / L3 | 0.09 / L3 | 0.08 / L3 | 0.03 / L3 |
| set_path | supporting | 0.91 / L3 | 0.90 / L3 | 0.90 / L2 | 0.99 / L2 | 0.99 / L2 |
| branch | supporting | 0.98 / L3 | 0.82 / L3 | 0.85 / L2 | 0.99 / L2 | 0.97 / L2 |
| remove_path | supporting | 0.88 / L3 | 0.89 / L3 | 0.87 / L2 | 0.99 / L2 | 0.97 / L2 |

Seven supporting declarations meet all their applicable targets. The organizing
edit_path recurrence meets Compression/Delight but fails Memetic/Anticipation/
Payoff. Baseline set_path was classified leading; its new supporting role reflects
the algorithm moving into edit_path. Changing the threshold is not evidence that
the same expression became more memetic. The small changes in unchanged helpers
are weak model preferences, not measured reading effects.

The mandatory composition review reads the full main.bend file, not only the
selected spans: 3295 bytes before, 3356 after, untruncated against a 48,000-byte
limit. At level 3, composition probabilities were Memetic 0.24 -> 0.30,
Anticipation 0.04 -> 0.04, Payoff 0.08 -> 0.11: all below target. Both commands
returned attention status 3. There is no automatic style pass. Declaration
contexts were also untruncated with the standard 16/12/48000/4 limits. Full
probability distributions, roles, task/composition inputs, source/helper hashes
and unresolved references remain in [style-before.json](campaigns/int-map-paths-2/style-before.json)
and [style-after.json](campaigns/int-map-paths-2/style-after.json). Current source
matches the candidate these ratings describe exactly; no ratings were repeated
when the candidate was reinstated.

#### Handoff

One candidate is retained; no second generation or compiler-diagnostic retry
occurred. The measured runtime regression is deferred debt under the explicit
20% allowance. The leading recurrence and full-file composition still fail their
Memetic/Anticipation/Payoff targets. Do not rerun unchanged style ratings or revisit
the accepted two-tip branch collapse to chase scores. The published package hash
is unchanged and no compiler dependency pin was edited. See
[outcome.json](campaigns/int-map-paths-2/outcome.json),
[performance-budget.json](campaigns/int-map-paths-2/performance-budget.json),
[source-verification.json](campaigns/int-map-paths-2/source-verification.json),
[initial disposition](campaigns/int-map-paths-2/initial-disposition.json),
[temporary restoration](campaigns/int-map-paths-2/restoration.json) and
[release-preservation.json](campaigns/int-map-paths-2/release-preservation.json).
