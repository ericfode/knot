# Getting out of the memetic valley

Reflection requested on 2026-09-26. This is a design judgment grounded in current
source and retained receipts, not a new style pass or an implementation result.
Compiler Planning owns this document. The existing scoped pilot and its owner,
fixed rubric, independent gates and wider-queue hold remain in force.

We have been improving individual pieces faster than we have been developing an
expressive identity. That produces competent, sometimes elegant declarations
which do not teach a reader how to anticipate the rest of Knot. My recent flat
store makes this particularly visible: its laws discuss owners, rejection and
retirement; its emitter mostly discusses numbered locals, offsets and opcodes.
The interesting ideas are present, but the reader must reconstruct them.

I have treated style too much as a review after the representation is settled.
By then the choices that determine the code's silhouette have already been made.
The next design should start with the few semantic distinctions we want the
reader to recognize, then make their consequences visible in actual Bend.

The receipts support a narrower observation than a diagnosis of their cause.
The historical whole-project scan rated 1,887 declarations: 1,246 met the
conceptual target, 779 the delight target, five the memetic target, and none all
three. The five memetic passes were the parser entry and dispatcher, checker
dispatcher, evaluator step and Wasm lowerer. Four had capped helper context.
These are historical source ratings, not current acceptance of those functions.

Their repeated transition clauses are a plausible source of recognition. The
small parser entry also qualified, so declaration size alone does not explain
the result. Conversely, all five missed the conceptual target: an impressive
case table can establish rhythm while still making the reader carry too many
independent facts. This is a clue to investigate, not evidence that long
dispatchers are the desired style.

Our [scope refactor](STYLE_CAMPAIGN.md) establishes another useful distinction.
One shared traversal now preserves binding metadata for both refine and replace;
all three declarations meet the first two targets. Their memetic target masses
are .34, .33 and .15. Removing duplicated procedure was worthwhile, but did not
create an expressive identity. The [flat store](../flat-store/PERCH_REPORT.md)
has zero memetic passes across 106 declarations and a concrete reading problem:
owner transitions disappear inside assembly construction. The
[derived receipt summary](memetic-reflection-2026-09-26.json) pins these sources
and preserves the selected distributions without making new provider requests.

The three desired experiences need different explanations. Conceptual compression
means one idea discharges several obligations. Delight means the written form
makes those consequences satisfying to recognize. Memetic identity means the
reader learns a characteristic way to express another problem. My proposed
practical question is: after reading two operations, can a fluent reader predict
the shape of a third, and want to write it that way? This is an author hypothesis,
not an established measurement or an attributed user preference.

Knot has unusually good material for that identity. A task owns unfinished work.
A continuation records precisely what remains to do. A rejected insertion must
return the incoming owner. A join remembers an ordered missing contribution.
A retired generation cannot silently become a fresh owner. These facts can
shape the program, its error paths, its laws and its generated code together.
We should make those relationships easy to see before inventing additional terms.

For example, the current owner-authored, unqualified
[runner candidate](../adaptive-tasks/task.bend) reads:

```bend
def run(fuel: Nat, state: Run) -> Run:
  match fuel state:
    case 1n+n Checkpoint{task}: run(n,step(task))
    case _ _: state
```

Its potential hook is that exactly one shape advances: fuel paired with pending
work. The complement preserves the entire affine owner. The short form earns
its meaning from the `Run` datatype and the absorbing-delivery and zero-fuel
contracts. Fewer cases alone would not establish an improvement; the catchall
also makes those two stopping reasons less explicit. That tradeoff needs review.
The coordinator records passing deterministic evidence and unavailable live
after-ratings. I have inspected that record, not rerun its gates here.

The existing [fuel law](../adaptive-tasks/LAWS.bend) states:

```text
run(m, run(n, r)) = run(n + m, r)
```

The [inductive proof](../adaptive-tasks/PROOF.bend) takes the same checkpoint
transition as the implementation. The program and proof have related shapes.
That is a substantive source of pleasure: understanding the operational rule
also unlocks its composition rule. It gives the reader a reusable idea about
scheduling. We should seek more of this fit, without merging implementation and
independent test machinery or claiming that every proof must normalize to `{==}`.

There is a related opportunity in the evaluator. `Evaluate` descends into a
subterm while recording a `Frame`; `Return` consumes that frame to recover the
pending computation. The two directions can make each other predictable. The
same reading discipline can appear in an owned task machine, while retaining the
different `Data`/`Type` lifetimes and different exhaustion contracts. Shared
visual grammar does not require one universal state type or runner.

For the store, a real improvement would let the source expose an ordered
validation followed by an explicit ownership transition. The backend would
derive the corresponding loads, stores and branches. The representation must
still make error precedence, incoming-owner recovery, generation retirement,
free-list changes and payload clearing inspectable. A wrapper named `transfer`
around the same opaque instruction list has not achieved that. A tiny semantic
representation which removes duplicated invariants and explains several
operations might. That is a hypothesis requiring an implementation and fixed
independent evidence, not a decision to introduce a general DSL.

The next experiment I favor, after the existing pilot is resolved, is one bounded
store transition family. Develop the vocabulary against `put` and `take`, then
reserve `release` as a transfer test: does the vocabulary express its disposal
behavior without an ad hoc escape hatch? Keep its complete contract visible from
the outset; withhold its candidate rendering, not its requirements. If a new
abstraction only decorates `put`, or `release` needs to unpack all the machinery
again, the proposed basis has not earned adoption. Exact scope and preregistration
belong to that future owner assignment. Nothing is dispatched by this document.

This approach has several concrete constraints:

1. Record a reading claim before generating or judging a candidate: which
   relationships become visible, which distinctions remain, and what the next
   operation should make predictable. "More memetic" is not a sufficient claim.
2. Put the implementation, datatypes, relevant laws and two uses on one bounded
   reading surface. Give the vocabulary one clear explanation. Avoid a glossary
   whose cost exceeds the operations it explains. This surface presents actual
   source; it does not add marketing comments to score inputs.
3. Let each new abstraction earn its place through multiple real obligations.
   Preserve deliberate asymmetry, including error precedence and ordered joins.
   Consistent layout should reveal those distinctions, not smooth them away.
4. Compare the actual before and after before consulting scores. If the only
   reason to prefer the candidate is its rating, retain it as an experiment.
   A renaming-only example and an over-abstracted example are useful future
   calibration controls; they are not extra attempts in the current pilot.
5. Keep the independent model, laws, expected observations, negative tests,
   distinguishing mutants and applicable backend/cost gates fixed. A shared
   transition representation must not become its own independent oracle.
6. Review all changed and new declarations on all three unchanged axes. Record
   partial improvement or unavailable evidence as such. Propagation to another
   family needs a demonstrated reading benefit, not a numerical leaderboard.

There is also a real measurement problem to investigate. Our rubric asks for a
shared grammar, but the primary scoring unit is a declaration with bounded helper
context. The context builder resolves explicit local function references, caps
helpers and callers, and supplies datatypes from admitted source files. Some
imported types remain unresolved; `truncated: false` alone does not establish a
complete semantic context. A word can be necessary to a recognizable expression
without independently supplying that expression's entire effect.

That tension can encourage bad work: ornamenting ordinary helpers, accumulating
cases into one declaration, or adding terminology simply to appear distinctive.
It does not establish that any current low score is wrong. The current 60%
threshold is explicitly provisional and not calibrated human agreement. The
right response is a separate, bounded context experiment, not score retries or
a lower bar for the present pilot.

For that experiment, freeze the same actual source, rubric and model, and compare
the existing declaration context with a complete bounded family context. Select
a strong motif and a routine negative control before observing scores. Keep
per-declaration distributions and add a distinct family judgment; do not silently
substitute the latter for acceptance. Record the author's reading preference in
advance and seek a concrete user comparison before calling it human calibration.
If context consistently changes what the judge can recognize, repair the
measurement with held-out examples under the maintenance procedure. If the full
family still feels generic, improve the design. Neither outcome excuses the other.

We also need to distinguish syntax friction from a poor representation. Repeated
type arguments, explicit quantity annotations and long positional constructors
can obscure a strong idea. First isolate the particular pattern and ask whether
a well-chosen datatype or supported composition makes it clear. Propose language
sugar only for a repeated, demonstrated obstruction with a precise desugaring and
ownership law. Changing Bend to rescue one attractive sketch would create a new
compiler obligation before establishing the aesthetic benefit.

The immediate work remains small: finish the existing pilot honestly, preserve
its acceptance conditions, and use the next required compiler/runtime design to
develop one convincing family. Its best few expressions should become a concrete
style reference alongside the conventions that make them work. We will have a
stronger case for a Knot identity when a second, previously unwritten operation
inherits the form with less explanation and no extra semantic exceptions.
