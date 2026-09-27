# IntMap edit-locality proof review

Scope: the shared edit recurrence and its lookup consequences. Runtime and all
original contracts, proofs, assertions and historical receipts are byte-identical
to main `7750e5b`. This packet describes an additive proof experiment, not a new
package release or a completeness theorem. Paths are relative to packages/int_map.

## Contract and actual observations

The public API is empty/get/set/remove/contains/size/fold/union_with over a pure
persistent U32 map with arbitrary copyable Data values. All 32 bits participate;
None differs from Some(0). Public maps are the closure of those operations;
manually forged constructor trees are outside the public contract. Internal
path laws below hold over arbitrary raw trees and arbitrary finite Bool paths.
Public get/set/remove all select exactly 32 low-bit-first bits. Set ends in
Entry(key,value) and rebuilds raw Branch; removal ends in Tip and uses branch,
which collapses only Branch(Tip,Tip). It never promotes children across depths.

For arbitrary Data T and children a,b, the rebuilding premise is:

```text
join : forall erased T:Data. IntMap<T> -> IntMap<T> -> IntMap<T>
left  : forall erased T, a,b. low(T,join(T,a,b))  = a
right : forall erased T, a,b. high(T,join(T,a,b)) = b
```

`join`, `left` and `right` are closed template parameters, checked with opaque
premises in the generic proof. They are not runtime mutable callbacks or axioms.
The exact new statements in locality/LAWS.bend are:

- edit_here: for every V,path,m,end and both projection proofs,
  get_path(V,path,edit_path(join,V,path,m,end)) = value(V,end).
- edit_away: for every V,p,q,m,end, both projection proofs and a constructive
  `distinct : LAWS.separated(p,q)`,
  get_path(V,q,edit_path(join,V,p,m,end)) = get_path(V,q,m).
- raw_low/raw_high: auxiliary constructor projections, each universally
  quantified over V and both children; neither is a headline behavioral claim.
- set_get/remove_get/set_preserves/remove_preserves: exact copies of the four
  corresponding original public propositions, independently filled by the two
  generic theorems. Same quantifiers, quantity annotations, domains and results.

The endpoint theorem inducts over path. Nil returns value(end); False/True use
the corresponding projection then recurse. The locality theorem inducts over p
and matches q: matching bits use that projection and induction; opposite bits
use the untouched sibling's projection. Equal/prefix branches eliminate Empty.
No step assumes that different numeric keys have separated paths universally.

## Inhabited premises and boundaries

Raw Branch discharges the premises by reduction in raw_low/raw_high. Pruning
branch discharges them with the existing checked LAWS.branch_low/branch_high
proofs, imported through the unchanged original PROOF.bend. Thus both actual
runtime policies instantiate the generic result, with Entry and Tip endpoints.
There are no unchecked projection inhabitants.

separated(p,q) is Unit at the first opposite bit, and Empty if one path ends
before a differing bit. Existing LAWS.distinct_witness constructs Unit for
bits(32,0) and bits(32,2147483648), traversing 31 shared bits. Opposite first
bits also provide Unit. Valid witnesses include V=U32, empty maps, and the
nonempty map {0->0, 2147483648->99}. Setting 0->17 preserves 2147483648->99;
removing 0 preserves that binding; the previous version retains 0->0.
The new public propositions accept that same explicit witness without adding
an assumption. Equal keys and proper-prefix paths are explicitly excluded from
edit_away. Empty path is included in edit_here. End may be Tip, Entry or Branch;
the result is value(end), not an unconditional Some.

Both projections are necessary premises. A join that always discards the right
child cannot satisfy right for b=Entry(1,99). A join that promotes a sole Entry
child changes a one-bit lookup to an empty child and cannot satisfy the relevant
projection. These are explanatory counterexamples to the assumptions, not new
machine-checked negative fixtures. Existing mutation evidence below is separate.

## Fixed independent observations and coverage

The independent model uses a unique-key association list, U32 equality, filtered
removal and front insertion. It imports Base only and performs no trie traversal
or bit extraction. The checked relation observes every selected key's lookup,
exact length, and once-per-binding fold entries in both directions. Universal
list-model refinement is not claimed.

| Public operation | Fixed law and executable observations |
| --- | --- |
| empty | empty_get universally gives None; empty size=0 and fold retains its seed. |
| get | set_get/remove_get; Some(0) versus None, every single-bit/complement key, max U32. |
| set | overwrite and separated-path set_preserves; distinct values, exact size, retained old versions. |
| remove | remove_get and separated-path remove_preserves; present/absent deletion and full erasure. |
| contains | set_contains; stored zero is present, missing one is false, model agreement. |
| size | Exact model length through overwrite/removal/union and scaling to 4096 entries. |
| fold | Exact entries, low-bit-first order 0,2^31,2,1, and retained nonempty accumulator seed. |
| union_with | Noncommutative overlaps, one-sided values, prior maps, trace shape and independent 96-entry model checks. |

Collision witness: left={0->2,max->3}, right={1->5,max->7},
combine(a,b)=100*a+b, expected={0->2,1->5,max->307}. Addition gives max->10 and
maximum gives max->7, so those controls alone would not suffice. A separate
Trace witness requires exactly Some(Join(Atom(2),Atom(7))) at the overlap and
unchanged Atom(11)/Atom(13) at one-sided keys. This rejects reversing operands,
combining twice and applying the combiner to a singleton. It constrains pure
expression structure, not physical callback counts under compiler optimization.

192 composed set/remove transitions compare old/updated/removed versions to the
list model at every step, all 64 query keys, exact size and fold membership.
Scaling checks 64,256,1024,4096 entries in dense and 16-shared-low-bit layouts,
every lookup, depth32, exact sum/size and zero retained nodes after full erasure.
Both native CPU and generated JavaScript executed the unchanged release suite.

## Proof and adversarial evidence

Pinned Bend 2.0.29 at 574b6d39a235b539eb19a5c532993a0abb3d11ad checks the complete
additive entry point and original entry point: 8 new plus 23 old filled laws,
zero holes. The first candidate failed parsing because a local binding preceded
a nested match. The one retained diagnostic retry moves only those bindings into
the leaf branches; statements and proof equations are unchanged. It passes.
No further source correction, unsafe proof, new axiom or weakened assertion.

All 11 unchanged semantic mutants first typechecked and then failed the intended
original runtime observation: discarded set value, erased sibling, ignored bit31,
stale removal, false membership, zero size, discarded fold entries, reverse fold,
reversed overlap operands, combined singleton, and duplicate combine. No parser,
type, build or timeout failure was counted as a kill. This rerun confirms the
existing contract controls; it is not a dedicated mutation study of the new proof.
The generic proof itself checks with opaque join/projection parameters.

gates.json records original/additive proof checks, native/JS builds and executions,
all mutations and scaling/model checks. preregistration.json freezes 70 inputs,
including all runtime sources, original law/proof files, scripts, contract and
release receipts. All match afterward. Runtime performance remains the previously
measured identical implementation: 3.1% native and 5.4% JS slower medians at 4096
under the user's 20% allowance. No new relative timing, speedup or nonregression
claim follows from this proof-only increment.

Trust remains the pinned checker, conversion/termination and Base definitions;
native/JS observations additionally trust primitive lowering, C, Bun and memory
management. Base contains foreign and unsafe operations, but unsafe Array
operations are unreachable from these pure proofs. IO occurs only in the runtime
test harness. GPU execution is unvalidated. No universal bit-injectivity, depth,
size/fold/union, allocation or complete model-refinement proof was added.

## Review boundary

The Perch observer parses the law file but lacks imported template-law context
for the proof fills: it rejects the recursive `~join` argument after treating
the imported law as having zero template parameters. The actual pinned compiler
accepts the complete source. parser-observations.json retains the exact failure.

review-copy.py mechanically combines the unchanged laws and proof bodies,
removes only their local G qualification, and relocates imports in a generated
review copy. The complete copy also passes the pinned compiler; its source and
hash mapping are retained. Supplementary semantic/style review can therefore
inspect all eight law/fill pairs without changing the maintained source. This
does not establish canonical per-file automatic style coverage. A separate
composition request includes the original proof, fixture and model collaborators
omitted from the first review's automatically assembled group. Original failed
attempts and all scores remain evidence; no unchanged declaration is rejudged
to seek a better score.
