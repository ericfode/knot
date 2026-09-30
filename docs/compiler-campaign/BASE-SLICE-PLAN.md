# Base slice plan: VM-first, with an independent enum-source step

Snapshot: main `aef68c86` (2026-09-29), examined through Git objects; implementer
branch starts at `ff44b974`. Seed: Bend 2.0.29, `574b6d3`; Base is the unmodified
67,190-byte file, SHA-256
`22eea83911e2395f63594fea7c10ac0c1e5b548251681fc97cd7667e0eb7031b`.

This plan follows D2, D4, D7, D12, D14–D26 and the coordinator's standing rulings.
The session prohibits merges. The task file's main-into-baseslice merge therefore
remains a coordinator action unless the user explicitly resolves that conflict.
No production paths from another branch have been copied into this worktree.
Live Perch, merging to main and shared-receipt refresh are coordinator actions.

## What the selfhost judge means by `base`

`tests/compiler-selfhost/check.py` does not discover Base support. `judge` reads
`expectations.json.needs`, collects the names whose `available` is true, then
`derive` computes `case.needs - available`. A missing need makes a case blocked,
even if its current observations meet the requirement. `base` is false, owned by
`modules + baseslice`, and described as loading the pinned Base and lowering its
reachable slice. It is not a count of parsed declarations or a statement that
all 466 Base entries have checked. The coordinator controls that reviewed flag.

Main's recorded result is 2 pass / 63 blocked / 0 fail, out of 65. Forty-eight
blocked rows name `base`; those rows include rejected twins and have other
blockers. Forty-eight is neither the number of Base declarations nor the number
of programs this increment alone can make pass. The current judge runs check and
eval, not image emission. It invokes single-file CLI mode until modules supplies
its bundle lane. A missing need never excuses a crash, an accepted seed-rejected
twin, a wrong successful value, or an unreviewed false Invalid. The five reviewed
layout gaps remain owned by selfsource. This step changes neither needs nor pins.

Sources: `check.py::{judge,derive,observe,meets,faults,unreviewed}`, its
`D4_GAPS`, and `tests/compiler-selfhost/expectations.json.needs` on the snapshot.

## Exact reach and the different closures

[BASE-SLICE-INVENTORY.json](BASE-SLICE-INVENTORY.json) lists every reached Base
entry, exact source spans and hashes, shape/features, direct src users and
transitive dependency edges for each scope and lane. Its 30 src input hashes
identify the analyzed snapshot. It uses the pinned census parser and the
hash-checked seed OPERATIONS table; it is source analysis, not acceptance.

| Roots | Runtime Base, JS / native | Static checking Base | Unresolved |
|---|---:|---:|---:|
| `src/lex.tokenize`, `src/parse.parse` | 39 / 39 | 53 | 0 |
| complete compiler: `src/compile-cli.main` and imports | 72 / 72 | 110 | 0 |
| every declaration in every `src/*.bend`, including proofs and CLI variants | 76 / 76 | 114 | 0 |

Runtime reach includes signatures and body references, maps constructors to their
owning datatypes, retains both branches and supplied callbacks, and cuts intrinsic,
foreign and native word-representation bodies. It does not solve higher-order
flow or specialize generic instances. Static reach also descends into those
source implementations and proof bodies. The compiler's 72 are **43 source,
20 JS intrinsics, 6 foreigns, 2 word representations and 1 bodiless File**.
Native has 44 source / 19 intrinsics: String.append has a source implementation
there, while Bool.or is a seed intrinsic in both lanes.
The island qualification deliberately tests Bool.or's source body in both Knot
builds, rather than treating the seed's optimization as a required VM leaf.

All-src runtime adds Cmp.is_le, Nat.is_le, Nat.sub and String.length to the 72.
All-src static adds Equal.sym, Nat.is_le, Nat.sub and String.length to the 110.
Thus both static closures have 38 more entries than their runtime closures,
but those complements are not identical. The table below enumerates all 114,
not only the runtime 72 of the older suite.

Reproduction (read-only analysis of the named Git snapshot; output stays here):

```sh
export BEND_NO_TELEMETRY=1
node tests/compiler-baseslice/plan-inventory.mjs --ref=aef68c86abbf50f4acd71c3f2c503ead63c44306
```

The published package pins must still match the snapshot. Base constructors and
Word source types are not VM representations merely because their names match.
The hash-pinned registry and representation headers supply that authority.

## What is already provided, and by whom

- **baseslice at ff44b974:** 40 immutable seed fixtures (25 agree, 1 may be
  Unsupported, 4 host-effect refusals, 10 rejections), the 72-entry frozen runtime
  projection, seed regeneration and a fail-closed Wasm host adapter. There is no
  baseslice compiler implementation or registered baseslice gate at that tip.
- **main aef68c86:** the enum and monomorphic-field checker, first-parameter
  structural evaluator, native enum/field Wasm emitters, classification repairs,
  census, bootstrap/selfhost progress gates and knot-io-2 host. The production
  CLI still refuses imports. **Zero Base-loaded books are accepted on main.**
  Its existing grammar/checker/evaluator/emitter can process the seven enum
  declarations as ordinary source; BS1 independently qualifies that fact.
- **modules 7ac90164:** SHA-256, unmodified Base loading, all-466 name inventory,
  scoped dependency selection, source-order partition and checked/unchecked
  audit. Its ordinary-source route covers the seven enum declarations, once
  installed. It refuses unmodeled reachable syntax. Do not reimplement its
  loader in baseslice. Reconciliation after nest remains required.
- **literals-integ 7aa8427e:** four primitive representations plus 24 registry
  identities intersect the compiler's runtime slice: **28 declarations**.
  This is inspected source coverage on an unmerged branch, not integrated
  conformance or a VM pass. Its intrinsic set also replaces some seed-source
  routines (e.g. U32.show and String.eq), so its executable closure may be
  smaller than the seed's 72. U32.is_zero is a source wrapper of U32.is_eq;
  Bool.or is covered by ordinary source, not this registry intersection.
- **nest, descent-2, generics, closures:** own pattern matrices, broader descent,
  type/quantity erasure and higher-order core support. Their presence on branches
  does not establish a composed checker. Types-as-functions (Pair, IO), products
  and dependent Sigma normalization must be checked explicitly at integration.
- **image b200a6a9, vm-spec 819cbf9b, vm-core/model and later prims/io:** own the
  image codec and execution track. Their SPEC supplies the mapping below. None
  is installed on this main snapshot. An enum Wasm pass is not image execution.

The disjoint current-source coverage partition of the 72 is **7 enum + 28
literals identities + 37 remaining source/effect/opaque declarations**. Each
count describes an inspected mechanism or BS1 qualification; all 72 still wait
on modules for actual imported-book acceptance on main. Some of the remaining
37 helpers disappear if an already registered literal primitive cuts their
caller; keep their source inventory and the explicit unchecked complement.

## Check, evaluation, core and image requirements

The following codes make each row's obligations precise:

| Code | Check | Independent evaluator | Core | VM image / executor |
|---|---|---|---|---|
| E | Existing nominal types, quantities, declaration order and exhaustive single-column cases | Existing enum tags, calls, lets and cases | Value, Reference, Application, Let, Case, Branch | Ordinary §3 nodes; slots and function indices; image + vm-core still required |
| P | literals' pinned signatures, representation identities and op arities; no user spelling installs an intrinsic | Literal/Intrinsic values; distinct U32, Nat, Char and String; declared bounds | Literal or Intrinsic with checked operands | §2 constants/representation headers and hash-pinned prim IDs; vm-prims; Nat > u32 is Exhausted (D15) |
| G | Generic datatype/function and quantity arguments, Kind meet and erased type applications; normalize type-level aliases | Erase types/quantities, retain every live argument and uniform boxed field | Ordinary records with erased binders; abstract field types retained for checking | No specialization: erased slots/arguments disappear, abstract positions use none (§2); generics |
| N | Ordered nested/multi-column/wildcard/variable rows and constructor refinement | Same first-match result, including parent reconstruction | Case/Branch/Default, including primitive matrix columns | §3 Case rows and Default; nest + literals; no duplicated-default size bypass |
| D | Base self-calls after erased/type parameters and mutual law fills; establish descent or return Unsupported | Fuel-bounded call transitions; no termination claim from exhaustion | Application with resolved function index; preserve declaration events | Existing Call/Enter semantics and fuel (D16); descent-2 |
| T | Products and Sigma/Pair dependency, tuple patterns/lets, type aliases; IO(A)'s arrow alias | Move/reconstruct live components; type computation erased | Algebraic Sigma fields plus ordinary cases/lets; IO arrow types | Sigma header Tuple{none,none}, ordinary cells; products/alias normalization, not an unchecked foreign shortcut |
| C | Arrow types, captures, reusable/affine closure rules and variable calls | Closure environment, Invoke and argument transfer | Closure / Invoke (no defunctionalization for D14) | §3 closures/capture slots and arrow tables; closures + vm-closures |
| H | Pinned opaque File/foreign signatures and IO.OP; D12 checks the pure consumer, never arbitrary user foreign | Independent inert requests and model effects; dropped requests never run | Foreign leaf / IO request and continuation; core-io | knot-io-2, exact foreign IDs; vm-io; D20–D25, including atomic stops and Book refusal |
| X | Source/signature/proof obligation behind a trusted primitive cut, retained unchecked under D2 | Not entered by this runtime slice | No executable node for the cut dependency | No encoded body; retain trust audit. Whole-Base checking stays S3 |

All installed declarations also need modules' hash/name/scope gates. Every
successful declaration must actually check; E/P/G/etc are requirements, not a
whitelist for skipping checks. Until the IO lowering exists, a checked book with
a host leaf compiles to Unsupported with no new artifact (D12). Until vm-io,
an image naming an unimplemented foreign is refused at load, not run.

For File, bodiless Type is a pinned opaque type, not a runtime function. For Pair
and IO, normalize their erased type-level definitions before assigning runtime
arrows/fields. For law + fill families, preserve the original declaration event
order. Do not label them Invalid merely because a narrow parser cannot handle a
forward declared filling body. When a proof cannot be completed, D21 leaves its
original proposition as an explicit obligation, never a weaker replacement.

## Every reached declaration

Scope C is compiler runtime; A adds an all-src runtime entry; S is static-only
for all-src. Shapes are the pinned declaration kinds and body/signature features;
full spans, hashes, direct users and dependencies are in the JSON inventory.
Requirements are cumulative unless X says the declaration is behind a runtime
cut. The branch column names outstanding integration, not an acceptance claim.

| Declaration | Scope / shape | Check → eval → core → image requirements | Waiting owner |
|---|---|---|---|
| `Bool` | C; ADT | E | modules; image / vm-core (BS1 body qualification) |
| `Bool.and` | C; Def | E | modules; image / vm-core (BS1 body qualification) |
| `Bool.cmp` | S; Def, matrix | X | D2 trust inventory; later S3 whole-Base check |
| `Bool.full_add` | S; Def, fields, matrix | X | D2 trust inventory; later S3 whole-Base check |
| `Bool.not` | C; Def | E | modules; image / vm-core (BS1 body qualification) |
| `Bool.or` | C; Def | E | modules; image / vm-core (BS1 body qualification) |
| `Bool.pick` | C; Def, generic, dependent | G | generics; nest / descent-2 for list bodies; modules; image |
| `Char` | C; ADT, fields | P | literals-integ; modules; image / vm-prims |
| `Char.cmp` | C; Def, fields, matrix | P G T | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `Char.is_eq` | C; Def, fields, matrix | P | literals-integ; modules; image / vm-prims |
| `Char.to_u32` | C; Def, fields | P | literals-integ; modules; image / vm-prims |
| `Cmp` | C; ADT | E | modules; image / vm-core (BS1 body qualification) |
| `Cmp.is_eq` | C; Def | E | modules; image / vm-core (BS1 body qualification) |
| `Cmp.is_ge` | S; Def | X | D2 trust inventory; later S3 whole-Base check |
| `Cmp.is_gt` | S; Def | X | D2 trust inventory; later S3 whole-Base check |
| `Cmp.is_le` | A; Def | E | modules; image / vm-core; later all-src qualification |
| `Cmp.is_lt` | S; Def | X | D2 trust inventory; later S3 whole-Base check |
| `Equal.sym` | S; Def, generic, dependent, closures, law, fill | X | D2 trust inventory; later S3 whole-Base check |
| `File` | C; Def, law, opaque/bodiless | G T C H | modules, generics, closures; products / core-io / vm-io |
| `File.close` | C; Def, foreign, IO | G T C H | modules, generics, closures; products / core-io / vm-io |
| `File.open` | C; Def, generic, foreign, IO | G T C H | modules, generics, closures; products / core-io / vm-io |
| `File.read` | C; Def, generic, foreign, IO | G T C H | modules, generics, closures; products / core-io / vm-io |
| `File.write_bytes` | C; Def, generic, foreign, IO | G T C H | modules, generics, closures; products / core-io / vm-io |
| `IO` | C; Def, generic, dependent, arrow, IO | G T C H | generics, closures; IO alias / core-io / vm-io |
| `IO.OP` | C; ADT, generic, dependent, fields, IO | G T C H | generics, closures; IO alias / core-io / vm-io |
| `IO.args` | C; Def, generic, foreign, IO | G T C H | modules, generics, closures; products / core-io / vm-io |
| `IO.bind` | C; Def, generic, dependent, arrow, closures, IO | G T C H | generics, closures; IO alias / core-io / vm-io |
| `IO.die` | C; Def, generic, dependent, fields, closures, IO | G T C H P | generics, closures; IO alias / core-io / vm-io |
| `IO.print` | C; Def, foreign, IO | G T C H | modules, generics, closures; products / core-io / vm-io |
| `List` | C; ADT, generic, dependent, fields, Kind/quantity | G | generics; nest / descent-2 for list bodies; modules; image |
| `List.append` | C; Def, generic, dependent, fields, Kind/quantity | G N D | generics; nest / descent-2 for list bodies; modules; image |
| `List.length` | C; Def, generic, dependent, fields, Kind/quantity | G N D | generics; nest / descent-2 for list bodies; modules; image |
| `List.reverse` | C; Def, generic, dependent, Kind/quantity | G N D | generics; nest / descent-2 for list bodies; modules; image |
| `List.reverse.go` | C; Def, generic, dependent, fields, Kind/quantity | G N D | generics; nest / descent-2 for list bodies; modules; image |
| `Maybe` | C; ADT, generic, dependent, fields, Kind/quantity | G | generics; nest / descent-2 for list bodies; modules; image |
| `Nat` | C; ADT, fields | P | literals-integ; modules; image / vm-prims |
| `Nat.cmp` | C; Def, fields, matrix | P | literals-integ; modules; image / vm-prims |
| `Nat.double` | S; Def, fields | X | D2 trust inventory; later S3 whole-Base check |
| `Nat.is_eq` | C; Def | P | literals-integ; modules; image / vm-prims |
| `Nat.is_le` | A; Def | P | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `Nat.sub` | A; Def, fields, matrix | P N D | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `Pair` | C; Def, generic, closures | G T | generics; products / aliases; modules; image |
| `Result` | C; ADT, generic, dependent, fields, Kind/quantity | G | generics; nest / descent-2 for list bodies; modules; image |
| `Sigma` | C; ADT, generic, dependent, fields, arrow, Kind/quantity | G T | generics; products / aliases; modules; image |
| `String` | C; ADT, fields | P | literals-integ; modules; image / vm-prims |
| `String.append` | C; Def, fields | P | literals-integ; modules; image / vm-prims |
| `String.cmp` | C; Def, fields, law, fill, matrix | P G T N D | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `String.cmp.fin` | C; Def, fields, nested | P G T N D | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `String.cmp.rec` | C; Def, fields, nested | P G T N D | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `String.concat` | C; Def, generic, fields | P N D | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `String.eq` | C; Def | P | literals-integ; modules; image / vm-prims |
| `String.eq.fin` | C; Def, fields, nested | P G T N D | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `String.length` | A; Def, fields | P N D | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `String.reverse` | C; Def | P | literals-integ; modules; image / vm-prims |
| `String.reverse.go` | C; Def, fields | P N D | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `String.starts_with` | C; Def, fields, law, fill, matrix | P N D | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `String.starts_with.if` | C; Def | P N D | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `U32` | C; ADT, fields | P | literals-integ; modules; image / vm-prims |
| `U32.add` | C; Def, fields, matrix | P | literals-integ; modules; image / vm-prims |
| `U32.and` | C; Def, fields, matrix | P | literals-integ; modules; image / vm-prims |
| `U32.cmp` | C; Def, fields, matrix | P | literals-integ; modules; image / vm-prims |
| `U32.div` | C; Def, fields | P | literals-integ; modules; image / vm-prims |
| `U32.div.fin` | S; Def, fields | X | D2 trust inventory; later S3 whole-Base check |
| `U32.div.if` | S; Def | X | D2 trust inventory; later S3 whole-Base check |
| `U32.divmod.go` | S; Def, dependent, fields, matrix | X | D2 trust inventory; later S3 whole-Base check |
| `U32.divmod.go.fin` | S; Def, dependent, fields | X | D2 trust inventory; later S3 whole-Base check |
| `U32.divmod.go.rec` | S; Def, dependent, fields | X | D2 trust inventory; later S3 whole-Base check |
| `U32.divmod.go.shl` | S; Def, dependent, fields | X | D2 trust inventory; later S3 whole-Base check |
| `U32.from_nat` | C; Def, fields | P | literals-integ; modules; image / vm-prims |
| `U32.inc` | S; Def, fields | X | D2 trust inventory; later S3 whole-Base check |
| `U32.is_eq` | C; Def | P | literals-integ; modules; image / vm-prims |
| `U32.is_ge` | C; Def | P | literals-integ; modules; image / vm-prims |
| `U32.is_gt` | C; Def | P | literals-integ; modules; image / vm-prims |
| `U32.is_le` | C; Def | P | literals-integ; modules; image / vm-prims |
| `U32.is_lt` | C; Def | P | literals-integ; modules; image / vm-prims |
| `U32.is_ne` | C; Def | P | literals-integ; modules; image / vm-prims |
| `U32.is_zero` | C; Def | P | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `U32.mod` | C; Def, fields | P | literals-integ; modules; image / vm-prims |
| `U32.mod.fin` | S; Def, fields | X | D2 trust inventory; later S3 whole-Base check |
| `U32.mod.if` | S; Def, fields | X | D2 trust inventory; later S3 whole-Base check |
| `U32.mul` | C; Def, fields, matrix | P | literals-integ; modules; image / vm-prims |
| `U32.read` | C; Def, generic, fields | P N D | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `U32.read.go` | C; Def, generic, fields, law, fill, nested | P N D | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `U32.read.if` | C; Def, generic | P N D | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `U32.show` | C; Def | P | literals-integ; modules; image / vm-prims |
| `U32.show.fin` | C; Def, fields | P N D | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `U32.show.go` | C; Def, fields, law, fill | P N D | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `U32.show.if` | C; Def, fields | P N D | literals-integ; nest / descent-2; products / generics where T/G; modules; image |
| `U32.shr` | S; Def, fields | X | D2 trust inventory; later S3 whole-Base check |
| `U32.shrn` | C; Def, fields | P | literals-integ; modules; image / vm-prims |
| `U32.sub` | C; Def, fields, matrix | P | literals-integ; modules; image / vm-prims |
| `U32.to_nat` | C; Def, fields | P | literals-integ; modules; image / vm-prims |
| `Unit` | C; ADT | E | modules; image / vm-core (BS1 body qualification) |
| `Word` | S; Def, generic, fields | X | D2 trust inventory; later S3 whole-Base check |
| `Word.Con` | S; ADT, generic, dependent, fields | X | D2 trust inventory; later S3 whole-Base check |
| `Word.Nil` | S; ADT | X | D2 trust inventory; later S3 whole-Base check |
| `Word.adc` | S; Def, dependent, fields, law, fill, matrix | X | D2 trust inventory; later S3 whole-Base check |
| `Word.adc.con` | S; Def, dependent, fields | X | D2 trust inventory; later S3 whole-Base check |
| `Word.add` | S; Def, dependent | X | D2 trust inventory; later S3 whole-Base check |
| `Word.and` | S; Def, dependent, fields, matrix | X | D2 trust inventory; later S3 whole-Base check |
| `Word.cmp` | S; Def, dependent, fields, matrix | X | D2 trust inventory; later S3 whole-Base check |
| `Word.cmp.fin` | S; Def | X | D2 trust inventory; later S3 whole-Base check |
| `Word.inc` | S; Def, dependent, fields, nested | X | D2 trust inventory; later S3 whole-Base check |
| `Word.mul` | S; Def, dependent | X | D2 trust inventory; later S3 whole-Base check |
| `Word.mul.go` | S; Def, dependent, fields, nested | X | D2 trust inventory; later S3 whole-Base check |
| `Word.shl` | S; Def, dependent, fields | X | D2 trust inventory; later S3 whole-Base check |
| `Word.shl.out` | S; Def, dependent, fields | X | D2 trust inventory; later S3 whole-Base check |
| `Word.shl.out.con` | S; Def, dependent, fields | X | D2 trust inventory; later S3 whole-Base check |
| `Word.shl.put` | S; Def, dependent, fields | X | D2 trust inventory; later S3 whole-Base check |
| `Word.shr` | S; Def, dependent, fields | X | D2 trust inventory; later S3 whole-Base check |
| `Word.shr.pad` | S; Def, dependent, fields | X | D2 trust inventory; later S3 whole-Base check |
| `Word.sub` | S; Def, dependent | X | D2 trust inventory; later S3 whole-Base check |
| `Word.to_nat` | S; Def, dependent, fields, nested | X | D2 trust inventory; later S3 whole-Base check |
| `Word.zero` | S; Def, dependent, fields | X | D2 trust inventory; later S3 whole-Base check |

## Ordered increments

Sizes are planning bounds, not measured elapsed times. The serial merge order
from COORDINATOR-STATE remains nest → modules → descent-2 → closures → literals-
integ → generics → VM track; this plan does not move those branches ahead.

| Step / size | Dependencies | Acceptance and D7 expectations | Semantic mutants |
|---|---|---|---|
| **BS1: enum-source qualification, 0.5–1 day** | Existing main/branch E support only; no unmerged branch | Seven verbatim pinned Base declarations; two positive books with 31 calls; four rejected books; one seed-valid import book still Unsupported. Both seed lanes freeze 32 calls before the runner. Native/Bun-built Knot check/eval and emitted Node Wasm agree on all 31 unblocked calls, with equal Wasm bytes. Eight source-algebra laws check with zero holes. Register `base-enum` in gates. | Wrong tags, reversed case selection, aliased argument slots, constant evaluator and disabled type boundary. Kills must be classified disagreements or acceptance of the pinned bad type, never parser/build failures. |
| BS2: module/island integration, 0.5–1 day | modules after nest reconciliation | Install exactly these seven from hash-verified Base, source order retained, correct unchecked complement. Run imported equivalents through bundle check/eval and every available emitter. Freeze both seed lanes before fixtures are added. Preserve single-file pins or amend conflicts separately under D26. | Wrong Base digest accepted; dropped helper dependency; discovery-order output; duplicate/colliding names; silently unchecked selected body. |
| BS3: scalar leaves and wrappers, 1 day | literals-integ + modules; image/VM when merged | Qualify the 28 identities, plus ordinary U32.is_zero and enum Bool.or wrappers; signatures and quantities match Base. Frozen edges 0, 1, 2^31, 2^32−1, overflow/divide/shift boundaries and Char/Nat distinctions. Image records use registry IDs, not inferred names. | Op-ID swap; Nat/U32 conflation; wrong shifted operand; alias a familiar user name to a primitive; weaken declared bounds. |
| BS4: generic containers and selection, 1–2 days | generics, nest, descent-2, modules, literals | Bool.pick, Maybe, Result, List and append/length/reverse.go/reverse; all quantity instances, erased/live argument order, affine negatives and accumulator order. Reuse the immutable first suite's corresponding observations; add any new observations from both seed lanes first. Generic/type-level checking failures remain Unsupported. | Erased argument executed or dropped live argument; Kind meet widened; swapped Con fields; reversed append; input-discarding length/reverse. |
| BS5: products and recursive comparisons, 1–2 days | BS4; products/aliases; nest + descent-2 | Sigma/Pair, Char.cmp and the String.cmp/eq/starts_with families; retained parent values, prefix/length/first-difference cases and LT/EQ/GT tags. Quantities and law/fill order checked. Every original Base law required by the implementation stays required under D21. | Drop/reorder a preserved component; wrong first-difference/prefix result; copied affine parent; accept an unproved/unsupported mutual call. |
| BS6: formatting and scans, 1–2 days | BS3–BS5; registry-cut audit | String.concat/reverse, U32.read/show helper families, and extra all-src Nat.is_le/sub/String.length. Freeze leading zeros, empty strings, non-digit tails, maximum decimal, LEB128 edges and formatting/diagnostic composition. If a registry cut removes helper execution, record that helper unchecked rather than claim it checked. | Digit order, stale accumulator, accept trailing junk, discard list tail, overflow before guard; falsely include a cut helper in the checked audit. |
| BS7: pure IO and host leaves, 1–2 days | generics, closures, products/IO aliases, core-io, VM prims/closures/io | IO/IO.OP/bind/die, opaque File and six effects. Preserve the original suite's host observation and D12's main amendment; do not change old pins in this step. Freeze request dropping/default/Book refusal, ABI failure, bad-handle and atomic-stop traces against the applicable seed/contract oracle. | Eager/dropped request performed; Book effect; wrong foreign ID; bad handle accepted; mutate halted state or output before refusal. |
| BS8: complete slice and image conformance, 1–2 days | All preceding source increments + image/VM track | Frozen complete src/compile-cli import bundle and bytes package; every selected declaration checked, exact unselected/unchecked audit. Evaluator ⇔ seed ⇔ VM values; encoded image uses one node per core form, contiguous live slots and canonical tables. Cover all 40 original baseslice books and all relevant selfhost rows. Only coordinator updates needs, merges and refreshes shared receipts. C1→I2→I3 fixpoint remains vm-e2e3, not this slice gate. | Missing closure edge; noncanonical table/slot; wrong erasure; trust a user-created representation; stale output or receipt; constant compiler; losing a checked declaration. |

BS1 is the first independent increment because its entire language mechanism is
already present. It implements a new qualification/gate, not a competing loader
or a synthesized Base. No new source-language capability is claimed. Installing
Base requires BS2 and the existing modules branch. Native Wasm is supporting
conformance here; VM images remain the self-hosting route (D14).

## Evidence and unrun gates

The BS1 oracle, cases and consumer bodies live in
`tests/compiler-baseslice/enum/expectations.json` and `fixtures/`. Seed source
uses `import Base` plus the same consumer body; the Knot qualification book
contains the seven byte-for-byte Base excerpts. The native seed mandates Base
and reserves its names, so those two representations are deliberate and frozen.
They do not establish import scope, hashing, file loading or a runtime trust audit.

The original 40-book suite and its expectations remain untouched. Its full
ladder gate is deferred to BS2–BS8. No selfhost capability is flipped by BS1.
BS1 source proofs establish five finite-domain universal algebra laws and three
Cmp ground equations, not a compiler correctness theorem. Main's merge, twenty-
gate reconciliation, full imported slice, images, VM execution, fixpoint, and
live Perch remain explicit follow-on actions. The implementation report records
fresh gate results and exact counts separately from this design snapshot.
