# Owned continuation run: deterministic pass, three-axis target not met

The user authorized this pilot in the current checkout after new-chat creation
was blocked. The scope is one parsed declaration; fifteen other task-file
declarations remain byte-identical. Requested effort is GPT-6 Astra / max.
Coordination transferred to `/Users/ericfode/.codex/worktrees/7e98/knot` on
branch `codex/perch-takeover`. This is a retained experiment, **rejected as an
all-three feasibility demonstration**. No second candidate was generated.

Before:

```bend
def run(fuel: Nat, state: Run) -> Run:
  match fuel state:
    case 0n _:
      state
    case 1n+n Checkpoint{task}:
      run(n,step(task))
    case 1n+n Delivered{dest,payload}:
      Delivered{dest,payload}
```

First candidate:

```bend
def run(fuel: Nat, state: Run) -> Run:
  match fuel state:
    case 1n+n Checkpoint{task}: run(n,step(task))
    case _ _: state
```

The recurrence is the sole progressing case; its complement is identity on the
complete owned state. The author prefers that explicit fixed point, while
recognizing that the named delivery arm disappears. The existing comment,
datatype and all proof bodies are unchanged. [Preregistration](preregistration.json)
precedes the edit; the [reading judgment](author-reading-judgment.md) precedes
the failed after-review. No human preference for this candidate is invented.

## Independent acceptance

- First candidate passes syntax/types/quantities and all twelve unchanged laws,
  including arbitrary full-state zero-fuel, absorbing delivery and fuel composition.
  No diagnostic retry or candidate correction occurred.
- Valid affine usage checks. Both reuse negatives fail specifically with
  `consumed more than once`.
- The independent Bend tree oracle produces the same ten fixture records.
  Baseline and candidate native/JS runs match all eleven conformance observations.
- All five mutants type-check, fail their original named proof obligations and
  reproduce the original differing runtime observations. The zero-budget locator
  inserts the same bad zero-fuel arm before the recurrence; it does not corrupt
  positive-fuel delivery. No assertion changed.
- All emitted JavaScript outside `run`, and its advancing path, are byte-identical.
  The only generated change removes two field reads and one Delivered wrapper
  construction in favour of returning the existing state. Forty-two bounded
  comparisons through 65,536 ticks retain exact full states and step counts.
  No wall-time speedup or native/GPU performance result is claimed.

Current reproducible receipts: [CPU gate](cpu-gates-reproduction.json),
[cost/full-state gate](cost-gate-reproduction.json), and
[actual parser/source verification](source-verification.json).
The first successful CPU/cost receipts remain historical. The final CPU driver
reconstructs its source closure from Git objects and immutable candidate/baseline
snapshots, so it does not require an earlier session's ignored inputs.

The old device receipt is retained. Its unchanged shader, runner and fresh
independent fixture output hashes match. That closure does not import task.run.
This is matching historical hardware evidence, not a new device run. The original
whole-check receipt remains historical because its task source hash differs.

## Style and semantic review

| Axis | Matching baseline target mass | Candidate target mass | Disposition |
| --- | --- | --- | --- |
| Conceptual compression | 0.84 | 0.82 | Meets target |
| Delight | 0.83 | 0.81 | Meets target |
| Memetic identity | 0.57 | 0.52 | Uncertain; target not met |

The unchanged target is at least 0.60 probability mass at levels 3/4 on **every**
axis. The [first successful candidate review](candidate-style-access-3.json)
returned all three distributions from `jev-1.13.0`, with complete, untruncated
bounded context. The differences from baseline are small; they do not establish
an improvement or a reliable preference. Full [baseline distributions](baseline-style.json)
and the author's preregistered reading hypothesis remain intact.

That review completed in the original chat while takeover was in flight. The
new coordinator [reconstructed its exact source/context/rubric identities](takeover-verification.json)
without another paid style request. The two earlier transport failures remain
historical evidence. They are superseded as the current access condition, not
erased or relabeled as successful requests.

Live [source review](semantic-source.json) checks fuel completeness, affine
lifetime, machine arithmetic and invariant work: four checks, one response,
no threshold findings. The [bounded packet review](semantic-laws.json) applies
all eight law rules: eight checks, one response, no threshold findings. These
are advisory observations. The [configuration controls](../../../../docs/perch-calibration/takeover-2026-09-27/README.md)
reproduce a known proof-claim false negative; zero findings is not a correctness
certificate.

## Disposition and takeover

The unchanged proofs, ownership negatives, independent native/JS observations,
mutations and cost comparisons passed in the original checkout. Takeover verified
all 19 frozen files, four tooling files, four pinned reference files and the
retained receipt hashes. Those deterministic gates were not rerun. The candidate
source remains `03d0139685cd66110a70101b6d74f5f903ab6cdc545f5735ed243314003ffb81`.
The accepted semantics, independent assertions and rubric are unchanged.

The pilot is rejected against its all-three acceptance criterion. The candidate
is retained in the isolated branch for inspection, with its semantic evidence
and remaining style uncertainty explicit. The broader queue stays on hold.
Do not repeat this unchanged score request or make a second candidate under the
same preregistration. A separately scoped next experiment must start from a new
concrete reading hypothesis rather than attempting to obtain a nicer score.

The [transfer manifest](takeover-transfer.json) records the copied owned paths.
The original chat stood down; its shared checkout, staged source and unrelated
runtime/Laya owner edits were preserved. The existing campaign heartbeat was
retargeted to the takeover chat; no duplicate automation was created. Current
checkpoint state is in [disposition.json](disposition.json) and the campaign
state file.

The old access failures remain in [access-2.json](access-2.json),
[disposition-access-1.json](disposition-access-1.json) and
[disposition-access-2.json](disposition-access-2.json). They do not describe the
current worktree's working provider, Git or app access.

## Reproduce without replacing evidence

From a checkout with the pinned reference toolchain installed, use new receipt
names:

```sh
python3 research/adaptive-tasks/style-pilot/adaptive-run-1/check-pilot.py --receipt=cpu-gates-fresh.json
bun research/adaptive-tasks/style-pilot/adaptive-run-1/check-cost.mjs cpu-gates-fresh.json cost-gate-fresh.json
```

The takeover worktree has the Perch parser installed but does not copy the ignored
reference compiler installation. Source/toolchain identities are checked before
execution. Candidate snapshots, first compiler results, original mutation
outcomes and historical receipts stay unchanged.
