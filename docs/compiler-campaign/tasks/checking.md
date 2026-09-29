Excerpt of research/compiler-fields/SPEC.md: the paragraph of the structural contract that the checker states and proves.

Extend the monomorphic catalog with constructor arguments and ordered pattern
matrices: multiple scrutinees, wildcard and variable rows, nested constructors
and plain or `+` field binders. Rows preserve source order; the first matching
row supplies the body. Shadowed bodies are discarded. Every constructor
combination must be covered, with zero rows valid for an empty datatype.
Source pattern names and arities are checked before selecting bodies;
constructor columns remain strict under earlier catch-all rows.
Every constructor argument is checked against its field type and demand;
erased arguments are checked but not executed. Constructor expressions require
an expected type. Structural recursion follows its separate descent contract.
