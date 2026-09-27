# Structural declaration review packet

Historical declaration checkpoint `0479b66`. The current structural checker and
independent evaluator are described in [the next increment](../compiler-fields/README.md).
Statements below about the pre-body capability gate describe that earlier checkpoint.

Contract: `knot-structural-declarations-1`, pinned Bend 2.0.29,
`574b6d39a235b539eb19a5c532993a0abb3d11ad`. This checkpoint catalogs field
declarations. It does not execute field values or claim compiler soundness.

## Public observations and implementation

`parse.parse(depth,tokens)` returns a syntax tree or explicit error. Constructor
declarations contain ordered `Parameter{token,quantity,type_name}` nodes.
`catalog.catalog(root)` returns
`Catalog{types: List<Datatype>, signatures: List<Signature>}` or error.
Each datatype is `Datatype{token,reusable,constructors}`, each constructor is
`Constructor{token,fields}`, and each field is
`Parameter{token,quantity,type_id}`. Tokens retain spelling and source span.
Type IDs and constructor tags are declaration-order indices. No runtime layout
is inferred from the number or order of fields yet.

The first pass checks global names, nonempty types, constructor names and catalog
bounds. It records datatype headers and constructor order with empty placeholder
field lists. The second pass walks the original declarations and resolves every
field against the complete header list. Only its result is returned by `catalog`.
This separation permits forward, self and mutual type references without
recursively expanding their layouts.

`fields(nodes,types,data,seen,count)` checks, in order: capacity 256, duplicate
field name within the constructor, type lookup, quantity legality, and field
kind. It prepends the checked field to the recursively checked tail. The caller
starts `seen=[]` and `count=0` separately for every constructor. The helper is
internal and its count argument is not a public unbounded input contract.

`field_type(token,q,data,reference)` first checks q in 0..2 and requires a Data
child for q=2. Its remaining condition is:

```
(q != 2 OR child_is_Data) AND
(parent_is_Type OR q == 0 OR child_is_Data)
```

Thus a Type object may own a Type child; a Data object may not. Erased fields
may have Type. No inhabitation or positivity rule is added. An unused invalid
declaration is still invalid. Errors are not mapped to successful metadata.

`check.resolved` runs `enum_profile` before any body is checked. Any nonempty
field list gives `Unsupported check constructor-fields`. Compiler output is not
opened before complete checking and emission, so these failures preserve an
existing output file. The observer prints `Catalogued`, not `Checked` or `Built`;
it deliberately makes no statement about the function bodies in its input.

## Domains, witnesses and coverage

All success fixtures contain inhabited Flag with distinct Off/On constructors.
The recursive Tree has Leaf and Fork; mutual Tree/Forest has Tip and Empty bases.
No Empty parameter, axiom, unsafe inhabitant or impossible antecedent discharges
a claimed field property.

| Observation | Independent witness / gate | Law category |
| --- | --- | --- |
| Names, quantities, order, source spans, type identity survive parsing/resolution | Fixed complete catalog strings for plain-field, field-quantities and forward-field-type; native/Bun | Runtime observations; metadata helper law below |
| Forward, recursive and mutual type references | Forward-field-type, recursive-tree, mutual-types; independently accepted by pinned seed | Runtime fixtures, no general recursion theorem |
| Data cannot own live Type fields; + fields need Data | data-owns-type, many-owns-type, nested-type-kind, unused-invalid-fields; matching seed kind diagnostics | Kind helper laws plus public runtime negatives |
| Erased Type fields allowed | data-erased-type and field-quantities accepted by seed and catalog | Quantified helper law |
| Duplicate names local to constructor | duplicate-field rejected; duplicate-field-across-constructors accepted | Runtime controls |
| Unknown field type invalid | unknown-field-type; exact phase/code and seed missing-name diagnostic | Runtime negative |
| Out-of-profile field type syntax unsupported | Valid seed bare quantity, function and erased Type-field declarations | Runtime unsupported controls |
| 256 succeeds; 257 exhausts | Source-generated inputs accepted by seed; complete 256-field catalog and explicit check exhaustion at 257; native/Bun | Boundary observations |
| Field execution remains unsupported; rejected output preserved | All successful field declarations through actual compiler CLI with a preexisting sentinel output | Quantified guard helper law plus end-to-end observations |
| Existing enum semantics/ABI preserved | Original frontend, checker and actual Wasm gates; generated Wasm artifacts unchanged | Prior laws and new regression receipts |

The observer calls the real parser/catalog. The host harness supplies literal
sources and fixed expected strings; it does not parse, check or evaluate Bend.
The generated boundary oracle is an explicit vector of known field names and
positions, not a second general parser. The upstream seed supplies independent
acceptance/diagnostic evidence. No emitter or evaluator result is used to derive
the catalog expectations.

## New law statements and proof boundary

`src/catalog-PROOF.bend` fills five laws and imports the previous 18 filled laws:

1. `field_kind(data,0,child) == True` for both Boolean kind arguments.
2. `field_kind(True,1,False) == False`, a closed normalization.
3. `field_kind(data,2,False) == False` for either parent kind.
4. `field_type(token,2,data,TypeRef{index,Datatype{name,True,ctors}})` returns
   exactly `Parameter{token,2,index}` for arbitrary tokens/index/constructors.
5. A constructor with any nonempty field list makes `enum_constructors` return
   Unsupported at that constructor's source span, regardless of its siblings.

Four are quantified helper properties; one is a concrete normalization. None
proves complete parser/catalog refinement, storage correctness, subject
reduction, recursive descent or generated-code equivalence. The proof entry
checks with zero holes. No new native declaration, axiom or unsafe call is added.

## Mutations and adversarial review

Seven altered implementations pass seed parsing/typechecking and are killed by
the unchanged independent gate: allow an owned Type field in Data; discard all
field metadata; reverse field order; substitute type index zero; allow duplicate
field names; accept field 257; and bypass the field capability guard. The last
mutant emits an executable enum main from a book containing unsupported fields,
which the unchanged rejection assertion catches. No syntax failure, timeout or
harness error counts as a semantic kill.

A header-only catalog could look correct on enums while discarding all new
fields; the nonempty catalog oracle rejects it. A kind check restricted to
reachable types would miss unused-invalid-fields. A global field-name set
would reject the valid Left{x}/Right{x} control. A one-pass lookup would reject
forward-field-type and mutual-types. These are tested observations, not an
exhaustive completeness argument. The mutation suite does not claim to cover
every possible quantity/lookup combination.

## Results, resource and trust limits

The structural gate passes 16 seed fixtures, 32 catalog observations and 32
compiler rejection/output-preservation observations, four native/Bun boundary
pairs, five new filled laws and seven semantic mutants. Existing gates pass
14 parser fixtures, 49 checker fixtures and 25 actual Wasm programs with 90
independent reference calls. Full commands and receipts are linked in README.

Catalog scans are finite lists under source, parser and catalog bounds. Repeated
name/type scans remain in the implementation; no asymptotic improvement or
runtime performance result is claimed. The probe allows parser depth 4096 so
256/257 fields reach the catalog gate; default compiler parser depth remains 512.

The new proof closure loads 19 files; the observer loads eight. Both load the
pinned Base's 42 foreign declarations and unsafe Array.fork/Array.join, without
introducing new assumptions. The observer's emitted JS host effects are exactly
IO.args, File.open/read/close and IO.print. Seed checking/normalization, primitive
lowering and the emitted runtime remain trusted. There is no self-hosting or
GPU execution evidence in this increment.

Exact implementation, fixture and gate hashes are recorded in
`tests/compiler-structural/receipts/catalog.json`. The trust inventory records
loaded dependency hashes; Perch records every supplied context hash and
truncation marker. Remaining work is field-pattern scope/refinement, sound
descent, owned storage, transfer/drop and device lifetime qualification.

## Frozen source hashes

| File | SHA-256 |
| --- | --- |
| `src/core.bend` | `3da0f83d79ef2c6ba239782cb9cdc85e268ea18963ea0ae748e58cba887b5a3c` |
| `src/parse.bend` | `60a1b54f53b26febbf1ecc4979162eb5eda1c3d204f040995bf453eff9af6ccb` |
| `src/catalog.bend` | `e7fef4e51b49e5978123980e52d382bc12ce03ec9b701dd3649c9fde6f288c45` |
| `src/check.bend` | `dbb83ba274078c9ce3ed903f4342889f0908687569fedd52bf522ea00e1195f5` |
| `src/eval.bend` | `c53c86485e0b55a97f1dfcb48c447355b7764ab3d65c5a8455faa58797f32883` |
| `src/catalog-LAWS.bend` | `3b4841bd9fb03d5404fb03c40128f7a495e674e31f7b0aceb40f8559186e8f6c` |
| `src/catalog-PROOF.bend` | `f7cfa9ad281b28bb2d2a96a6a60798916c6b8ba6a48f445d55b33213d155b7c9` |
| `tests/compiler-structural/observe.bend` | `cb80f7f2cb6d336265abfafc98cb0e043e5b3ffd501edae05e43c683b01aca5c` |
| `tests/compiler-structural/cases.json` | `9edb772692afc47cb7d5834a48fa6e79f7a8fc6ea892d93236e0ae19d62a25f3` |
| `tests/compiler-structural/check.py` | `3d0d052ed2c79f8a60b7546f707c0403f6e9b621f26104d81da73318b5f18d28` |
