# Structural declaration checkpoint

This increment extends the existing Bend parser and catalog. It does not yet
extend the executable enum profile. The complete goal is tracked in
`docs/SELF-HOSTING-GOAL.md`.

## Contract

A monomorphic constructor declaration has an ordered list of explicitly typed
fields: `Box{-ghost: Owned, value: Flag, +shared: Flag}`. Each field preserves its
name, source span, declared quantity (0, 1, 2), and resolved datatype index.
Indices follow declaration order. Forward, self and mutual datatype references
are allowed. Constructor names remain globally unique; field names must be
unique within one constructor, but may repeat across different constructors.

The catalog validates every declaration, including unused types. A reusable
field requires a `Data` type. Every live field of a datatype declared `Data`
requires `Data`; an erased field may have `Type`. No positivity or inhabitation
restriction is added. Unknown field types and these kind/quantity violations
are Invalid. More than 256 fields per constructor is Exhausted, never Invalid.
Other catalog limits and source/parser limits retain the enum contract.

Declaration scanning first establishes names, kinds and constructor order, then
resolves field signatures against all datatype headers. The temporary header
catalog is not a checked book. Only the completed catalog may pass to the body
checker. Before body checking, an explicit capability gate rejects all fielded
datatypes as Unsupported until field terms/patterns and their runtime exist.
The existing enum checker, evaluator and Wasm ABI remain regression oracles.
The observer reports `Catalogued`, never `Checked`, `Evaluated` or `Built`.

The declaration parser accepts single-line comma-separated field signatures,
including a trailing comma. Generic/dependent field types, bare quantity fields,
and other unsupported syntax do not acquire support through this checkpoint.

## Evidence and limits

The pinned upstream seed independently checks source fixtures. Literal expected
catalog observations establish field names, order, quantities and type identity
on both native and Bun builds. Negative fixtures have nearby valid controls and
exact diagnostic expectations. Boundary observations exercise 256/257 fields.
Semantic mutants must remain parseable and type-correct before an unchanged
observation can count as a kill. Laws about field-kind helpers are auxiliary;
runtime catalog tests establish the connection to public observations.

No field value is evaluated or emitted yet. Storage layout, transfer/drop,
field-pattern refinement, first-order structural descent and GPU reclamation
remain open. No whole-compiler soundness or performance theorem is claimed.
