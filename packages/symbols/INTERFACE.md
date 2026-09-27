# Symbols interface

Owned append-only String interner; Bend 2.0.29. The interface below is unchanged.
The working character-trie revision is verified locally and unpublished; see
[STYLE_CAMPAIGN.md](STYLE_CAMPAIGN.md). The following import still identifies the
published, remotely verified Base Map implementation.
Import: `import 0xf5507d46d06a1a8043dcb1a582194615/main.bend as S`.
Proof-inclusive entry: `import 0xf5507d46d06a1a8043dcb1a582194615/release.bend as Verified`.
Pinned Vec: `0xd684886d10b431b9dce6c3b2d1ef1980/main.bend`.

```
Table : Type
Error : Data = InvalidId | Exhausted
Table.new() -> Table
Table.bounded(limit: U32) -> Table
Table.length(table: Table) -> Table & U32
Table.limit(table: Table) -> Table & U32
Table.find(table: Table, name: String) -> Table & Maybe<&2,U32>
Table.intern(table: Table, name: String) -> Table & Result<Error,U32>
Table.resolve(table: Table, id: U32) -> Table & Result<Error,String>
```

Names compare as exact Bend String code-point sequences, including empty and NUL;
no Unicode normalization or case folding. IDs start at zero, append without reuse,
and are valid only for the lifetime/lineage of their owning table. Moving the
returned table preserves that lifetime; dropping it ends it. A numeric ID carries
no table brand; callers must not transfer IDs between independent tables.

Bounded clamps to Vec's 16,777,216 maximum; zero is valid. Existing names succeed
even when full. New names at the limit fail with Exhausted and preserve the table.
Resolve rejects any id >= length, including 0xffffffff, without wrapping.
All operations thread ownership. Internal constructors/helpers are unsupported;
Bend has no module export hiding. No reset, deletion, clone, reuse or generation API.

Dependency: Vec.new/bounded/length/limit/get/push only, with String Data elements.
Requires Vec's unchanged-state failures and ordered append with stable old indices.


Reproducibility and namespaces: IDs follow first successful intern order. The
same ordered sequence of names and limit yields the same IDs; reordered first
insertions can yield different IDs across builds. Callers must control traversal
order and must not serialize incidental allocation order as canonical artifact
order. This release provides no canonical remapping or cross-build identity.
One table has one exact-string namespace. Callers manage distinct namespaces
using separate tables plus an external namespace identity, or an injective
namespace/name encoding. A bare U32 from another table is not a valid scoped
reference, even when its number happens to resolve locally.
