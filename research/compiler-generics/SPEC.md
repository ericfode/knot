# Generics and quantity arguments contract

Profile `knot-generics-1`, seed Bend 2.0.29 at
`574b6d39a235b539eb19a5c532993a0abb3d11ad`. It extends the structural terms
profile with erased type and quantity parameters. Evidence is in
[`tests/compiler-generics/`](../../tests/compiler-generics/README.md).

## Types

`types.bend` is the type algebra: rigid binder indices, nominal families,
application, universes `Sort(q)`, the quantity type and quantity expressions.
Substitution is one sequential binding list; it instantiates later parameter
domains and results from earlier arguments. Quantities form a finite meet
algebra: literals reduce, `&2` is the identity and `&0` absorbs. Remaining
symbolic meets compare structurally, like the seed.

Supported families have erased type parameters (`-A: Type`, `-A: Data`,
`-A: Kind(a)`) and leading erased quantity parameters (`a`, `-a: Quant`).
Supported kinds are `Type`, `Data` and `Kind(q)`.

- `Name<..>` instantiates a family. A short application fills every omitted
  leading quantity with `&1`; prefix `+` fills all of them with `&2`, including
  written ones. Both need the family's declaration first.
- A bare `Name` is an instance only of a family without parameters. Any other
  bare family name is `Invalid check type-arity`.
- Type and quantity arguments are invariant, phantom parameters included.
  Distinct binders stay rigid.
- Kind fitting is directional. Data fits every kind; `Kind(&0)` and `Kind(&1)`
  impose the same single-use capability. A reusable binder needs a kind known
  to be Data. Every live field's kind fits its family's kind.

## Checking

`generic-catalog.bend` resolves parameter domains and family kinds before
fields and bodies. `generics.bend` checks every declaration, including unused
ones, before returning a runtime book. A call checks every argument, erased
ones included; an erased argument consumes no affine occurrence. A live
self-call must pass, as its first live argument, a strict field descendant of
the function's first live parameter.

`check-dispatch.bend` is the one checking entry. A book with generic syntax (a
generic datatype, a typed result, or a typed parameter) goes to the generic
checker; every other book keeps the monomorphic checker and its pinned
diagnostics. Acceptance is therefore decided per book: the generic checker's
first-live-parameter descent also applies to a monomorphic function in a book
that has generic syntax elsewhere. Both checkers classify an unbound term name
that names a datatype as `Unsupported check type-level-term`, and one that
names a definition, a first-class function value, as `Unsupported check
def-reference` (law `def_reference`). The type positions mirror this rule. A
type scope binds type variables over the book's definitions, so a type name
that resolves to a definition computes a type. It reports `Unsupported check
type-level-definition` wherever the definition is declared (law
`type_level_definition`). A name that resolves to nothing stays `Invalid
check unknown-type`.

## Erasure

`type-erasure.bend` projects the checked result into the existing core terms.
A generic family always uses a boxed `[tag][live fields...]` cell; one
synthetic erased field selects that representation without a memory word or
Wasm local. Closed monomorphic enums stay ordinals. An abstract value is an
opaque word whose checked instantiation fixes its representation. Each source
function has one emitted body with its erased arguments removed.

Compile generic books with the fields-profile driver. The default enum emitter
reports `Unsupported check constructor-fields` for a boxed family. Host calls
use closed monomorphic enum signatures only.

## Boundaries

Unsupported: type-returning definitions and aliases, local type or quantity
bindings, live type or quantity parameters and arguments, value-indexed
families, constructor-local type parameters, type-variable application, pair
type sugar, function types and templates.

- A type argument followed by anything but `,` or `>` is a term, as in the
  value-indexed application `Tag<On{}>`: `Unsupported parse term-argument`
  (law `term_argument`). Empty type-argument lists are Invalid, like the seed.
- A family without constructors, the domain of absurd elimination, is
  `Unsupported check empty-datatype` in both catalogs (laws `empty_family`
  and `empty_datatype`).

Laws in `types-LAWS.bend`, `type-erasure-LAWS.bend`, `catalog-LAWS.bend`,
`check-LAWS.bend` and `LAWS.bend` are proved; corpus agreement is finite differential evidence, not
a checker-soundness or compiler-correctness theorem.
