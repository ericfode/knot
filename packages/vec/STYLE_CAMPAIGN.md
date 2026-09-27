# Vec style campaign

## vec-growth-1 — accepted, unreleased

One candidate changed `plan_step` and `push_ready`. GPT-6 Astra high authored
the change. The first full proof/type/quantity check passed; no compiler retry
or subsequent source repair was used. Nothing was published. The released
package remains `0xd684886d10b431b9dce6c3b2d1ef1980`.

### Preregistered reading hypothesis and disposition

This is an author taste hypothesis, not a user-approved preference. Nested
matches hid the single continuation condition in growth planning and the
success-gated state transition after reserve. Joint matches expose those
conditions without new vocabulary. The preregistration preceded candidate
generation and judgment, with one candidate and one separately recorded
compiler-diagnostic retry available.

`plan_step` now has one recursive case: fuel remains and capacity is insufficient.
Every other combination returns the current plan. `push_ready` shows reserve
outcome beside the buffer transition; only its success arm duplicates the
length for increment and indexing. The failure arm returns the unchanged buffer.
This reduces decision nesting; it is not a performance claim.

Before:

```bend
  match fuel:
    case 0n:
      (cap,depth)
    case 1n+p:
      match enough:
        case True{}:
          (cap,depth)
        case False{}:
          +next = U32.add(cap,cap)
          plan_step(p,next,1n+depth,minimum,U32.is_le(minimum,next))
```

After:

```bend
  match fuel enough:
    case 1n+p False{}:
      +next = U32.add(cap,cap)
      plan_step(p,next,1n+depth,minimum,U32.is_le(minimum,next))
    case _ _:
      (cap,depth)
```

The push continuation now reads:

```bend
  match v r:
    case Buffer{n,c,d,m,a} Fail{e}:
      (Buffer{n,c,d,m,a},Fail{e})
    case Buffer{+n,c,d,m,a} Done{u}:
      (Buffer{U32.add(n,1),c,d,m,Array.set(Maybe<&2,T>,a,n,Some{value})},Done{Unit{}})
```

Acceptance is a manual reading judgment backed by preserved behavior. It is
**not an automatic style pass**: the judge lowered delight on both changed
definitions. The catch-all collapses the planner's two separately named stops;
the push joint match repeats the Buffer pattern. These are visible tradeoffs.
No score-chasing revision or repeated model judgment followed.

### Frozen contract and deterministic evidence

[Preregistration](campaigns/vec-growth-1/preregistration.json) freezes all 107
preexisting owned files except implementation, status and review packet.
This includes SPEC, INTERFACE, independent model, trace/assertions, generic and
boundary fixtures, LAWS, PROOF, gate script and all release-time evidence.
No frozen file changed; no mutation text locator needed repair.

- [Before snapshot](campaigns/vec-growth-1/before.snapshot):
  `baddf475d1fffb58749a6ab780dade30a10c8cf12b810320bc1903c5cdb28bb0`.
- [First candidate snapshot](campaigns/vec-growth-1/candidate-1.snapshot), also current source:
  `3e4d79031d5a1aede6b1d08c9859b4549d99f6628b3538ef399600280873e70a`.
- [First-shot check](campaigns/vec-growth-1/candidate-1-first-check.json): exit 0.
- [Gate receipts](campaigns/vec-growth-1/gates/gates.json): 25 zero-hole laws;
  12,288 bounded traces plus seven longer families on native/JS; generic
  records with Strings on both backends; exact ownership/kind rejections.
- [Mutation receipts](campaigns/vec-growth-1/gates/mutations.json): all nine
  type-correct mutants fail their original named runtime assertion and proof.
- [Scaling receipts](campaigns/vec-growth-1/gates/scaling.json): N=4096, 16384,
  65536, 262144; three samples each, every indexed value verified. Largest
  capacity 262144, 18 growth events, inferred 262143 copies and 524287
  initializations. Counts derive from transitions, not allocator instrumentation.
- [Integrity validation](campaigns/vec-growth-1/validation.json) records hashes,
  unchanged evidence, review counts, command completion and measured timings.

Pinned Bend 2.0.29 / `574b6d39a235b539eb19a5c532993a0abb3d11ad`. The proof
boundary remains 19 laws parametric in Data elements at fixed shapes, plus six
concrete boundary normalizations; no general all-state refinement or GPU claim.

The campaign runner imports the frozen gate and redirects only receipts:

```sh
python3 packages/vec/campaigns/vec-growth-1/run_gates.py
python3 packages/vec/campaigns/vec-growth-1/verify_evidence.py
```

The recorded gate run passed. The runner refuses to overwrite its existing
receipt directory. For another run use a fresh output directory; the ordinary
package gate writes historical receipt paths. The verification script can be
rerun without inference or compilation. During receipt verification, two host
assertions initially assumed empty arrays where the wrapper uses nullable
`issue_count`/`issues`; inspection confirmed `findings=[]`, `broken=[]`,
`clean=true`. The verifier now checks those authoritative fields. This was
receipt-schema handling, not a Bend candidate retry or an assertion change.

### Semantic and style review

Targeted semantic Perch reviewed both changed definitions against six Bend and
four performance rules, plus the updated bounded law packet against nine law
rules: 29 checks, three requests/responses, no findings.
[Commands and receipts](campaigns/vec-growth-1/semantic-runs.json) retain model,
rule/source identities and supplied context. No Perch rule was changed.

Twelve preregistered units cover both changed definitions, copy/allocation, the
reserve/push family and Vec/Error datatypes. All twelve baseline source, state
and context identities matched the existing project receipt exactly. Baseline
rows were extracted without inference; the parent's unrelated incomplete
inventory is not treated as a project pass.

The candidate used `--reuse=docs/perch-calibration/style-project-2026-09-26.json.gz`.
All twelve contexts contain the changed source and therefore needed fresh review.
Twelve requests completed on `jev-1.13.0`, matching the baseline's resolved model.
The rubric and parser were unchanged. [Exact command/result](campaigns/vec-growth-1/style-run.json)
records exit 3: attention, not a provider failure.

| Level 3+ probability mass | Compression before → after | Delight before → after | Memetic before → after |
| --- | ---: | ---: | ---: |
| `plan_step` | 0.78 → 0.90 | 0.61 → 0.52 | 0.18 → 0.18 |
| `copy_slots` | 0.75 → 0.74 | 0.53 → 0.51 | 0.16 → 0.17 |
| `allocate` | 0.63 → 0.63 | 0.51 → 0.52 | 0.18 → 0.20 |
| `reserve_grow` | 0.75 → 0.79 | 0.64 → 0.63 | 0.24 → 0.25 |
| `reserve_limit` | 0.71 → 0.72 | 0.69 → 0.65 | 0.32 → 0.34 |
| `Vec.reserve` | 0.59 → 0.58 | 0.78 → 0.75 | 0.45 → 0.44 |
| `push_ready` | 0.82 → 0.82 | 0.77 → 0.69 | 0.07 → 0.18 |
| `push_reserved` | 0.84 → 0.87 | 0.50 → 0.50 | 0.04 → 0.04 |
| `push_if` | 0.74 → 0.77 | 0.71 → 0.70 | 0.23 → 0.28 |
| `Vec.push` | 0.56 → 0.55 | 0.80 → 0.80 | 0.53 → 0.52 |
| `Vec` | 0.49 → 0.53 | 0.38 → 0.39 | 0.11 → 0.12 |
| `Error` | 0.52 → 0.45 | 0.46 → 0.49 | 0.09 → 0.09 |

Full five-level distributions and confidence are retained in
[baseline rows](campaigns/vec-growth-1/baseline-style.json) and
[candidate ratings](campaigns/vec-growth-1/candidate-1-style.json). Values above
are normalized probability mass, not measured human response or significance.
Small deltas and unchanged neighbor movements should not be overread.

Candidate coverage: compression 8 meet / 4 uncertain; delight 6 meet /
5 uncertain / 1 below; memetic 0 meet / 2 uncertain / 10 below. Zero of twelve
meet all axes. All definition contexts were untruncated; Error hit the four-user
cap. Datatype context is same-file-only; builtins/imported Base definitions
remain unresolved as recorded. A flat Error rating cannot establish quality
for every error-producing path.

### Remaining debt and next bounded opportunity

The planner's delight fell 0.61 → 0.52 despite higher compression; push_ready's
delight fell 0.77 → 0.69 while memetic rose 0.07 → 0.18, still below target.
Vec itself remains below delight and uncertain on compression. This batch does
not establish the campaign's desired memetic identity.

The next concrete opportunity is the affine handoff through `unpack` in
`copy_slots` and through `push_reserved`: a reader must track an owner-returning
pair, callback binders and the operation across separate declarations. A future
preregistered batch could make that ownership-transfer rhythm more consistent
without renaming for branding, duplicating arrays, or changing the oracle.
This remains a proposal; no second candidate was generated here.
