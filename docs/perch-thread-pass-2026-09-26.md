# Knot owner-chat Perch pass — 2026-09-26

The user requested a Perch pass from every Knot chat, followed by interesting
changes and code excerpts. Eight owner chats received bounded review requests;
the Perch coordinator reviewed its own tooling. Unrelated projects were outside
scope. No publication, remote push or paused campaign restart was requested.

## Coverage and result

The six package reviews completed **1,178 rule checks in 130 provider requests**.
The compiler owner's new checker and selected earlier parser/task work added
**321 checks in 105 requests**. All 235 requests received responses, using
`jev-1.13.0`, with **no reported Bend/law findings**. These were parsed-declaration
reviews with bounded helper context plus file-level law packets, not exhaustive
whole-repository scans. Published package sources did not change.

The Perch tooling review completed two additional requests: one custom-rule
evaluation and one native review group. It emitted two advisories, adjudicated
below. Do not combine native groups with source-rule evaluations as if they
counted the same thing. The documentation-only support survey had no applicable
source/law target; its zero requests are an applicability decision, not a pass.

| Owner chat | Checks | Requests / responses | Report | Commit |
| --- | ---: | ---: | --- | --- |
| Build and publish Bend Vec | 359 | 36 / 36 | [Vec](../packages/vec/PERCH_PARSED_REPORT.md) | `2de47e8` |
| Build and publish Bend source buffers | 149 | 15 / 15 | [Source](../packages/source/PERCH_PARSED_REPORT.md) | `77ca8b8` |
| Build and publish Bend output builder | 109 | 21 / 21 | [OutputBuilder](../packages/output_builder/PERCH_PARSED_REPORT.md) | `0ce6585` |
| Build and publish Bend integer maps | 223 | 24 / 24 | [IntMap](../packages/int_map/PERCH_DECLARATION_REPORT.md) | `ee6707b` |
| Build and publish Bend symbol interning | 169 | 17 / 17 | [Symbols](../packages/symbols/PERCH_DECLARATION_REPORT.md) | `d7a411a` |
| Build and publish Bend term storage | 169 | 17 / 17 | [TermStore](../packages/term_store/PERCH_PARSED_REVIEW.md) | `df2c34b` |
| Compiler Planning | 321 | 105 / 105 | [Checker review](../research/compiler-checker/PERCH_REPORT.md) | `df82e1f` |
| Survey Bend compiler support | N/A | 0 / 0 | [Handoff review](PACKAGE-HANDOFF-REVIEW.md) | `a7595b2` |
| Configure Perch for Knot | 2 CLI groups | 2 / 2 | This report | This increment |

[The consolidated evidence](perch-thread-pass-2026-09-26.json) records the exact
root receipt identities, target hashes, provider coverage, owner evidence paths,
tooling output and adjudications. Owner reports preserve declaration identities,
helper limits and raw answers. Twenty compiler declaration contexts were marked
truncated; imported Base and some type/constructor identities remain unresolved
in static review. Earlier named-check receipts have incomplete unit
metadata; their owners retained raw CLI output or supplemental context. The fix
below preserves that attribution for future runs without rewriting old receipts.

## Changes caused by this review

**Confirmed receipt defect, fixed.** Symbols first reported that named Bend checks
put their unit at the top level, whereas file checks return a `units` array. The
usage wrapper recorded only the array. Model requests had the right source, but
named-check receipts lost declaration identity and helper hashes. Source, IntMap
and TermStore independently observed the same gap. Normalize once before writing
the receipt ([wrapper](../scripts/perch-workflow.mjs)):

```js
// File checks return an array; named checks put the same unit at the top level.
const units = result?.units ?? (result?.context ? [result] : []);
```

The regression failed before the fix with zero retained units instead of one.
After the fix, `npm run lint:verify` passed all 21 tests and law-rule wiring. The
regression verifies name, span, checked count, rule, working-copy helper hashes
and context retention, while ensuring helper source text is not copied into the
usage receipt. This defect was found by owner inspection during the review;
it was not a semantic model finding.

**Stale documentation claims, corrected.** The support-survey owner separated
the release-time credential blocker from later live calibration: 19 of 24 controls
were correctly classified, with five misses retained. The coordinator corrected
`docs/perch.md` to recognize the committed frontend as an applicable compiler
target. README now records the new resolver/checker checkpoint while keeping
evaluation and Wasm emission outstanding. These corrections do not upgrade proof,
backend or model-accuracy claims.

**Tooling advisories, no forced refactor.** `scripts/perch-style.mjs::runStyleRanking`
received `unvalidated_destination` at 79.68% and `too_big` at 79%:

- Destination: **false-positive for the current local CLI trust boundary**. The
  operator supplies output paths and provider configuration. Input source paths
  are constrained to the workspace by resolved paths; existing output is rejected
  before paid requests and writes use `wx`. No untrusted remote caller chooses
  the destination in this interface. A future hosted interface would need its own
  boundary review.
- Size: **unresolved advisory; no behavioral defect established**. The 58-line
  function validates arguments, dispatches review and records results. Existing
  tests cover preflight, failed review and receipt behavior. A size probability
  alone does not justify changing correct code.

The five offline style tests also passed. No defect threshold, aesthetic rubric,
accepted law or package contract changed. No model repair was needed.

## New compiler work reviewed at this checkpoint

The compiler owner was already implementing the enum-profile resolver/checker.
This pass reviewed that new work; it did not cause or discover all those changes.
The new implementation is Bend. The pinned bootstrap/reference compiler remains
the separate TypeScript toolchain.

**Ownership as set algebra.** Live affine references contribute lexical binder
levels. Sequential expressions require disjoint use sets; alternative branches
union their sets. Repeated spellings stay distinct because identity is lexical.
There is no usage counter to wrap. The branch operation is small
([scope](../src/scope.bend)):

```bend
def alternatives(xs: List<&2,U32>, +ys: List<&2,U32>) -> List<&2,U32>:
  match xs:
    case Nil{}: ys
    case Con{+h,t}: alternatives(t,S.choose(List<&2,U32>,contains(ys,h),u => ys,u => Con{h,ys}))
```

**Known constructors replace consumed binders.** Matching a nullary constructor
consumes the parameter, then refines its occurrences in that arm into fresh
constructor values. This avoids falsely rejecting repeated appearances of a
known constructor. The successful branch of `occurrence` states the transformation:

```bend
case Some{tag}: Done{C.Checked{C.Value{token,type_id,tag},type_id,Nil{}}}
```

Its empty use set is part of the meaning. Unrefined occurrences instead produce
references and, when live and affine, singleton use sets.

The independent [checker gate](../tests/compiler-checker/receipts/checker.json)
passed 49 reference fixtures and 98 exact observations across native and Bun;
seven type-correct semantic mutants failed unchanged expectations. The proof entry
checks seven additional helper/boundary laws. All 69 gate input hashes matched
when consolidated. This remains a bounded enum-profile checker: it does not emit
Wasm or evaluate source values. List-based lookups/set merging have linear or
quadratic costs, and no compiler performance claim follows from this review.

## Earlier package mechanisms worth reading

These implementations predate this pass and remained unchanged. They illustrate
the requested reading experience; no new style ranks were invented because the
owners had no genuine same-contract implementation alternatives to compare.

**OutputBuilder: make concatenation a suffix computation.** Each fragment extends
the suffix; a join composes the two operations
([implementation](../packages/output_builder/main.bend)):

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

The right subtree supplies the left subtree's suffix, so output remains left to
right without repeatedly copying an accumulated prefix. The shape exposes the
composition law directly; deterministic package evidence supplies the cost claim.

**TermStore: distinguish unfinished work from completed failure in the type.**
The outer Result describes readiness; the inner Result describes the completed
computation ([implementation](../packages/term_store/main.bend)):

```bend
def Cell.result(-T: Data,-E: Data,cell: Cell<T,E>) -> Result<Error,Result<E,T>>:
  match cell:
    case Pending{}:
      Fail{NotReady{}}
    case Evaluating{}:
      Fail{NotReady{}}
    case Ready{x}:
      Done{Done{x}}
    case Failed{e}:
      Done{Fail{e}}
```

The constructor symmetry makes three states readable without sentinels or
out-of-band flags. Its separate commit helper returns the original store on a
rejected transition and reaches the write only after acceptance.

## Value and limits

This round improved traceability, corrected stale guidance and provided an
independent advisory review of new compiler code. It produced **zero confirmed
semantic model discoveries**. The receipt defect came from inspection, and the
strongest correctness evidence came from independent expectations, mutation
tests and the actual compiler. No measured time saving, production precision or
model superiority is established. Retain the two tooling advisories and earlier
calibration misses; do not turn a large clean count into a reliability claim.

Future work should use targeted checks on changed declarations and concrete
controls for suspected misses/noise. Repeating this unchanged corpus would add
cost without resolving the current uncertainty. Package owners refreshed their
stated deterministic gates and checked publication hashes; historical runtime,
scaling and remote-consumer evidence remains historical unless their report
explicitly says it was rerun.
