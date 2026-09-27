# Vec growth: accepted with style debt

Commit `cd78dba` changes two definitions in the reserve/growth family. The
implementation remains unreleased. Contracts, independent assertions, proof
bodies, published identity and dependency pins are unchanged.

The planner now states its sole continuation condition directly:

```bend
  match fuel enough:
    case 1n+p False{}:
      +next = U32.add(cap,cap)
      plan_step(p,next,1n+depth,minimum,U32.is_le(minimum,next))
    case _ _:
      (cap,depth)
```

The push continuation also uses a joint match. Failure returns the original
buffer; only success duplicates the length for indexing and incrementing.
The benefit is a visible transition rule with less nesting. The tradeoff is
that the planner's two distinct stopping cases share a catch-all, and the push
arms repeat the buffer pattern. Acceptance is an explicit reading judgment,
not a universal preference or an automatic style pass.

The first candidate passed without a diagnostic retry. The owner ran the
complete proof/type/quantity gate, native and JavaScript conformance/generic
checks, exact ownership/kind negatives, nine semantic mutants and native
scaling through 262,144 elements. The 25 filled laws retain their existing
fixed-shape proof boundary. No GPU or general all-state refinement is claimed.

The coordinator verified the recorded outcomes, all 107 frozen files, the
evidence manifest, and current source/helper hashes. The 12 style request
states were regenerated with the actual parser and matched exactly, including
context, rubric and parser identities. This verification made no provider
requests and did not rerun the owner's compilation or execution.

| Target mass at level 3+ | Compression | Delight | Memetic |
| --- | --- | --- | --- |
| `plan_step`, before → after | 0.78 → 0.90 | 0.61 → 0.52 | 0.18 → 0.18 |
| `push_ready`, before → after | 0.82 → 0.82 | 0.77 → 0.69 | 0.07 → 0.18 |

Across 12 reviewed units, compression has eight meets/four uncertain; delight
has six meets/five uncertain/one below; memetic has zero meets/two uncertain/ten
below. None meets all three. In particular, planner delight moved from meeting
the provisional bar to uncertain. Single judgments and small differences are
not statistical estimates of human preference. Definition contexts were not
truncated; the Error datatype hit the cap of four direct users.

Semantic Perch returned 29 relevant checks over three complete responses with
no findings. Style produced 36 ratings over 12 complete responses. These are
review evidence; deterministic acceptance is separate.

[Full owner report and before/after evidence](../../packages/vec/STYLE_CAMPAIGN.md)
and [coordinator verification](vec-growth-1-verification.json) retain identities
and limitations. The Source search/location batch evaluated terminal-state
clarity separately; its [accepted result](growth-search-bindings.md) retains its
own tradeoffs. This Vec result does not support assuming that flattening improves
every reading axis.
