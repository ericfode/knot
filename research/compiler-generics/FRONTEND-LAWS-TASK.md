# Frontend boundary contract

Lex bounded ASCII Bend source into tokens with byte spans. Preserve the LF,
indentation, comment and end-of-file conventions of the existing frontend.
Parsing either returns the bounded source tree, reports Invalid for malformed
supported syntax, reports Unsupported for an unmodeled form, or exhausts its
explicit depth budget. Unsupported is never language rejection (D4).

Generic headers and type applications are part of the accepted extension.
Template binders, additional scrutinees, imports and general type expressions
keep their documented boundaries until the owning increments land.
Type applications, quantities and type-parameter separators have a separate
law family. Do not weaken either family's statements (D21).

The seed treats -> and a constructor's term/pattern brace as glued tokens.
A source gap in those positions must not become an accepted glued term.
A constructor brace in a datatype declaration may have a gap. Glued supported
terms retain their seed behavior. Freeze source programs and seed observations
before each capability change (D7); preserve artifact bytes on compile refusal.

Proofs establish the exact boundary equations they state. General parser,
checker and compiler soundness remain separate obligations.
