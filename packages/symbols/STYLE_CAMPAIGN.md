# Symbols style campaign

The user's subsequent instruction to keep iterating superseded the one-candidate
and one-diagnostic-retry limit below. The completed search tried 24 source variants spanning several
representations and compositions and installed a balanced character trie while
preserving the public contract and independent tests. See the
[iterative report](style-campaign/iterative-identity/README.md) for every candidate,
the selected source, all style axes, correctness gates and measured tradeoffs.

The selected `Trie.get` met all three frozen v2 targets: 69% conceptual,
74% Delight, 62% memetic. During integration the shared coordinator installed
rubric v3. A separate live v3 review gives it 62% memetic, 92% Delight,
64% Anticipation and 79% Payoff; Galaxy brain remains below target. The working
revision therefore contains an actual memetic pass, not a complete v3 style
pass. The original failed experiment remains evidence below.

## Initial intern-identity experiment

2026-09-26. **Rejected at compiler preflight. No new memetic pass.**
The working implementation and published release remain unchanged. This records
the user's requested attempt after the fresh [memetic review](MEMETIC_REVIEW.md).
It does not resolve the coordinator's adaptive-task pilot or dispatch its queue.

## Fixed scope and reading hypothesis

The selected family was `inserted`, `append_name`, `intern_found`, and
`Table.intern`. All other declarations, public types and seven operations,
dependency imports, contract, independent model, observations, assertions and
eight accepted laws were frozen before generation. The
[preregistration](style-campaign/intern-identity-1/preregistration.json) retains
18 input hashes and snapshots; [tool identities](style-campaign/intern-identity-1/toolchain.json)
pin the compiler and review machinery.

Author preference, recorded before generating or judging code: expose the
hit/miss and append/commit transitions as one ownership-preserving grammar.
The existing implementation returns an old ID on a hit, obtains the old reverse
length on a miss, appends the name, and extends the forward map only on successful
append. Three result handlers make the reader reconstruct that progression.
The hoped-for improvement was visible symmetry between retaining an old ID and
committing one new ID, with both stores preserved on exhaustion. This was an
author hypothesis; the user did not endorse any particular notation.

The current handoff is:

```bend
def append_name(m: Map<&2,Maybe<&2,U32>>, +name: String,
  pair: V.Vec<String> & U32) -> Table & Result<Error,U32>:
  (v,id) = pair
  inserted(m,name,id,V.Vec.push(String,v,name))
```

It looks like removable tuple plumbing. The experiment showed that its parameter
boundary does real work for the pinned Bend parser.

## Candidate and one diagnostic retry

A bounded candidate-authoring agent used the requested `gpt-6-astra` / `max`
settings. It received the original four definitions, unchanged signatures and
semantics, quantity conventions and reading hypothesis. It used no tools and
received no independent test source. Resolved provider model identity and actual
internal reasoning usage are not exposed by the collaboration tool.

The [first candidate](style-campaign/intern-identity-1/candidate-first.bend.snapshot)
inlined the transaction into `Table.intern`, including:

```bend
(ids,found) = Map.get(Maybe<&2,U32>,None{},ids0,name)
match found:
```

The [first compiler result](style-campaign/intern-identity-1/candidate-first-check.json)
rejected the computed pair as a match scrutinee. The exact diagnostic was sent
back without a parent repair hint. The permitted
[retry](style-campaign/intern-identity-1/candidate-retry.bend.snapshot) introduced
`intern_slot` and `intern_commit`, keeping the length operation in the miss arm:

```bend
case None{}:
  (before,+id) = V.Vec.length(String,names)
  intern_commit(ids,name,id,V.Vec.push(String,before,name))
```

The [retry compiler result](style-campaign/intern-identity-1/candidate-retry-check.json)
rejected the computed pair again, now at `Vec.length`. Tuple destructuring itself
introduces a match subject to the same restriction. Both compiler calls exited 1
with the diagnostic:

> a parameter or field scrutinee (a match cannot scrutinize a computed value: give it its own def)

No third generation, parent hand-fix, changed assertion or altered threshold was
used. Both exact candidate fragments, complete source snapshots, compiler outputs
and the [author rationale](style-campaign/intern-identity-1/candidate-rationale.md)
are retained.

## Acceptance and disposition

Both candidates fail syntax acceptance. They therefore did not run through
types/quantities, complete proofs, runtime conformance, mutation, performance,
semantic Perch or live style review. Those gates are **unrun**, not passed or
failed on behavior. No new provider style requests were made for invalid code.
The original source and every frozen independent input still match their hashes;
this does not claim a fresh rerun of the historical deterministic gates.

The matching baseline remains:

| Declaration | Conceptual target mass | Delight target mass | Memetic target mass |
| --- | ---: | ---: | ---: |
| `inserted` | 85% | 61% | 3% |
| `append_name` | 88% | 55% | 8% |
| `intern_found` | 76% | 59% | 11% |
| `Table.intern` | 55% | 66% | 16.2% |

Each unchanged target requires at least 60% on levels 3/4. Baseline function
contexts are untruncated, with external Vec/Base internals unresolved. Full
distributions remain in the [fresh baseline receipt](receipts/memetic-review-2026-09-26/style.json).
After-ratings on all three axes are unavailable. There is no measured style gain.

**Disposition: retain the existing implementation; reject both generated sources.**
The working `main.bend` still has SHA-256
`65dc5051a91257adee3eb660f186fb71f4fc40f85aa81bac4b100adb15a5f17b`.
The release at `0xf5507d46d06a1a8043dcb1a582194615` is unchanged.

## Workflow correction

Future Bend style prompts must state that `(a,b) = computed_call(...)` is itself
match syntax. A returned owning pair needs a parameter boundary or a separately
qualified elimination combinator; merely moving the following explicit match
does not fix it. Include an existing valid example such as `append_name` and
explain why its boundary exists before asking a model to remove that boundary.
The failed retry is evidence that the generic diagnostic alone did not communicate
this desugaring effectively.

A subsequent experiment should preserve those supported boundaries and seek a
representation or composition that earns its vocabulary across real operations.
The present result supplies no evidence that flattening the transaction would
meet the memetic standard even if the language accepted it. Its failure is a
language-boundary result, not a judgment against the intended reading experience.

The corresponding review-log entry belongs to the shared Perch coordinator;
this owner-local record preserves the evidence without absorbing concurrent
edits to `docs/perch-review-log.md` or the shared campaign state.
