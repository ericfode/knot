# Symbols bidirectional-view experiments

Eight substantive candidates pass the unchanged proof and JS/native conformance.
None meets the complete style bar. Production source, independent inputs, rubric,
Git index and shared documentation were not edited by this sidecar.

| Variant | Mechanism | Declarations | Conceptual pass | Delight pass | Memetic pass | Highest memetic mass |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `mirrored` | One generic rejoin, two focused owned views | 8 | 8 | 3 | 0 | 30% (`Table.resolve`) |
| `persistent-forward` | Retain the Data Map and make intern consume find | 4 | 4 | 1 | 0 | 16% (`Table.intern`) |
| `typed-view` | Dependent answer type and one observation interpreter | 7 | 6 | 7 | 0 | 46% (`Table.view`, uncertain) |
| `bijection` | Name/Id involution and opposite-key crossing | 8 | 8 | 8 | 0 | 42% (`Table.cross`, uncertain) |
| `bijection-handlers` | Missing/present crossing shared by find, resolve and intern | 9 | 9 | 9 | 0 | 49% (`Table.cross`, uncertain) |
| `shared-binding` | Both indices store one immutable name/ID binding | 20 | 20 | 13 | 0 | 51% (`Table.cross`, uncertain) |
| `red-black` | Whole-string red-black tree with shared median promotion | 23 | 22 | 11 | 0 | 43% (`Table.intern`, uncertain) |
| `red-black-constructors` | Separate red/black constructors and inline rotations | 21 | 18 | 9 | 0 | 39% (`Table.intern`) |

Every axis still requires at least 60% normalized level-3/4 mass. All fresh
requests resolved to `jev-1.13.0`; full distributions, source hashes and context
limits are retained in each `style-first.json`. Function context is untruncated,
with Base and remote Vec details unresolved. The View datatype has same-file
context only. `summary.json` lists every target, command and disposition.

## Reading results

`mirrored` removes repetitive reconstruction through `rejoin`, `names`, and
`ids`. The two lifted public metadata reads are precise one-line compositions,
but the generic type arguments and rebuilding callbacks carry more visual weight
than the name/ID relation. The strongest conceptual scores do not imply memetic
acceptance.

`persistent-forward` uses a real ownership distinction: the Map is Data while
the Vec remains affine. `Table.find` retains the original Map and extracts the
lookup value from its round-tripped copy; `Table.intern` then consumes that public
observation. It is correct under the fixed gates. It has no style result that
would justify the unmeasured extra reference-count/path reconstruction cost.

`typed-view` has the strongest observed family: Length and Limit return U32,
ByName returns Maybe U32, ById returns Result Error String. `Answer(view)` gives
`Table.view` its exact dependent return type. The interpreter achieves 64%
conceptual, 90% delight and 46% memetic. Every changed declaration passes delight,
but the result function is conceptually uncertain and the support declarations
remain well below the memetic bar. The first hypothesis hoped to unpack Table
once in source; the pinned parser required parallel patterns, so that part of
the intended compression did not materialize.

`bijection` replaces the four unrelated query constructors with the actual two
sides of the association. `Key(Name{})` is String, `Key(Id{})` is U32, and
`Table.cross(side,t,key)` returns Maybe of `Key(opposite(side))`. This compiles
directly, and every changed declaration passes conceptual and delight targets.
The exact crossing masses are 74%, 82%, 42%. The optional internal result adds a
Result-to-Maybe-to-Result conversion for resolve, and its tiny type helpers remain
well below the memetic target.

`bijection-handlers` eliminates that conversion by giving the crossing two
continuations. Find chooses None/Some, resolve chooses InvalidId/Done, and intern
chooses append/old ID. This is the first form where the partial-bijection algebra
directly serves all three public operations. Every changed declaration passes
conceptual and delight; crossing is 71%, 89%, 49%, while find/resolve/intern have
memetic masses 43%, 41%, 44%. The four central operations remain uncertain on
memetic quality and the support declarations remain below target.

`shared-binding` changes the internal storage. Vec and Map store immutable
Binding{name,id} values, with a generic `Binding.key(side,binding)` projection.
On a new name, one reusable Binding is passed to Vec.push and retained for the
conditional Map commit. Existing IDs and all failure observations still pass the
fixed proof/runtime gates. Reviewing the entire 20-declaration file gives no
all-axis pass: crossing reaches 51% memetic, find 48%, intern 44%, resolve 41%.
Binding and Table datatype contexts hit the four-user bound. The representation
adds record/storage cost that has not been benchmarked, and the small style
movement supplies no acceptance case for it.

`red-black` is an original implementation of functional red-black insertion over
whole exact Strings. Four red/red shapes call one median promotion, and successful
Vec append alone permits insertion and root blackening. It passes the frozen
proof/runtime gates but has no style pass: balance is 24% memetic, Index.find 41%,
Index.insert 34%. A second representation, `red-black-constructors`, makes the
tree constructors directly E/R/B and balances only black parents. It also passes
the fixed gates, but the duplicated result expressions hurt conceptual ratings;
all memetic masses are below 40%. Neither balanced-tree experiment was integrated.

## Pinned compiler evidence

- Computed pair matches remain invalid. The generic `rejoin` uses a parameter
  boundary and compiles.
- After `(t,lookup) = pair`, trying to match `t` again is rejected as a consumed
  binder, even in `match lookup t`. A direct nested parameter pattern works:
  `(t,Some{id})` preserves the owner on hit; `(InternTable{v,m},None{})` exposes
  fields on miss. Both rejected attempts and accepted source are retained.
- Native GADT constructor result annotations are deliberately rejected in the
  pinned compiler tests. The ordinary dependent `Answer(view)` approach compiles
  without equality casts or runtime answer tagging.
- `InternTable{names,ids} = t` followed by `match view` is also rejected as a
  consumed binder. `match view t` with constructor patterns is supported.
- A shared constructor let needs an explicit type annotation: the compiler
  rejected `+binding = Bind{name,id}` and accepted
  `+binding = {Bind{name,id} : Binding}`. Both sources and diagnostics are saved.
- Mutually recursive named tree/comparison helpers were rejected as unfilled
  definitions. Passing an arbitrary subtree to a recursive callback hid the
  structural decrease. A typed comparison eliminator with constructor lambdas
  containing direct calls on the actual child fields passed the termination gate.

The frozen PROOF, model, cases and observation files are byte-identical to their
`intern-identity-1/inputs` snapshots in every variant. `gate.py` stores every
source attempt and complete command/stdout/stderr/exit/timing receipt. Each final
variant passes main and PROOF checking and produces `1` from unchanged JS and
native conformance. Full mutation, release-consumer, semantic Perch and paired
performance gates remain unrun; these rejected style candidates have not reached
integration acceptance.

Disposition: retain all eight as evidence, integrate none. A continuation should
build on a substantive representation or phase transition, rather than rescore
unchanged wrappers or rename generic helpers.

The later independent invariant review of the phase sidecar's balanced character
tries is separate from these rejected candidates. See `balanced-review/REPORT.md`:
both frozen layouts pass structural audits through 4,096 siblings on native and
JS, and 17 compiled mutation controls are rejected semantically.
