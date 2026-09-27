# Compiler family 1: known-binding updates

Disposition: **accepted implementation improvement; three-axis style target
still unmet**. The full [qualification record](family-1/QUALIFICATION.md) describes
the isolated first candidate. [Preregistration](family-1/preregistration.json)
precedes review and labels the reading hypothesis as the author's judgment.

The first Astra-high candidate was integrated byte-for-byte. No candidate retry
or later hand-fix was used. One new observer-only forward-call diagnostic was
retained and corrected separately. The family has three declarations, below
the campaign's 24-declaration bound.

Before, refine and replace repeated the complete binding traversal and metadata
reconstruction. Now one closed template owns that invariant; the wrappers state
the difference:

```bend
def refine(bindings: List<&2,C.Binding>, +level: U32, +tag: U32) -> List<&2,C.Binding>:
  set_known(~U32,~(tag => token => type_id => C.Value{token,type_id,tag}),bindings,level,tag)

def replace(bindings: List<&2,C.Binding>, +level: U32, +term: C.Term) -> List<&2,C.Binding>:
  set_known(~C.Term,~(term => token => type_id => term),bindings,level,term)
```

The [exact diff](family-1/candidate-first.diff) shows the shared traversal. Every
matching identity is updated, including duplicates. Order, tokens, quantities,
type IDs, parameter flags and nonmatching knowledge are preserved. The extra
template call is worthwhile here because it gives these two operations one
metadata-preservation rule. Template arguments are closed; runtime captures and
Knot's accepted-language profile do not expand. Closed templates remain part of
the compiler implementation's future bootstrap closure.

## Independent acceptance

The isolated baseline/candidate × native/Bun gate compared 54,720 complete
binding records across 28 runs at sizes 0,1,7,16,64,256,1024. It covered empty,
missing, first/middle/last and duplicate IDs. The independent oracle and all
existing contract/assertion hashes stayed fixed. Width scaling completed; the
timings include startup/formatting and establish no speedup or precise cost bound.

After live integration, all unchanged regression/mutation runners passed:

- Frontend: 14 fixtures, two lanes, 24 boundaries, four laws, four mutants.
- Checker: 49 fixtures, 98 observations, 10 depth/16 catalog bounds, seven mutants.
- Structural catalog: 16 fixtures, four boundary pairs, seven mutants.
- Fields: 40 fixtures, 240 phase observations, 36 budgets, six host probes,
  twelve level/inspection observations, nine mutants.
- Wasm: 25 programs, 90 independent calls in both lanes, 64 rejection pairs,
  44 boundaries and seven mutants. Existing generated modules stay unchanged.

The complete fields proof and refreshed fields/catalog/Wasm trust inventories
have zero holes and unchanged host-capability boundaries. No assertion or mutant
locator changed. Gate commands and links are in [acceptance.json](family-1/acceptance.json).

## Reading evidence

Targeted semantic review made nine checks in three complete responses, with no
findings. The before-style receipt reused two matching earlier ratings; the
after receipt made three fresh responses. All selected source identities match.

| Declaration | Conceptual before → after | Delight before → after | Memetic before → after |
| --- | ---: | ---: | ---: |
| refine | .95 → .95 | .75 → .76 | .17 → .34 |
| replace | .94 → .96 | .73 → .74 | .10 → .33 |
| set_known | new → .96 | new → .77 | new → .15 |

These are probability mass at levels 3/4, not measured reader outcomes. Small
differences give weak preference evidence. Every declaration meets the first two
targets and falls below the memetic threshold; none passes all three. Acceptance
rests on the concrete shared invariant and deterministic equivalence evidence.
The exact records retain full distributions, helpers and model identities.

No wider compiler rewrite or package publication is included. The coordinator
owns the shared campaign queue and can consolidate this checkpoint without
restarting completed package work.

The new 18-declaration observation fixture was reviewed separately in its fully
resolved isolated copy (21 changed/new declarations total). Its semantic review
completed 36 checks in 18 responses with no findings. Its style distributions
are 7/8/3 conceptual, 9/3/6 delight, and 0/16/2 memetic (meets/below/uncertain);
none meets all three. Explicit field projections make the oracle inspectable;
the repeated formatting remains a candidate for later bounded cleanup, not a
reason to compress away observed metadata.

Parent review found that the first host runner depended on a prior ignored
source copy. It now reconstructs and hashes the exact source closure from the
preregistered Git commit and immutable candidate snapshot. The corrected runner
passed all 28 observations again in attempt-003. This changes setup only; candidate,
fixture and expected observations remain byte-identical. Historical attempts
remain separate. Unified-diff context spaces are retained in the immutable
candidate-first.diff; the staged whitespace check excludes that artifact only.
