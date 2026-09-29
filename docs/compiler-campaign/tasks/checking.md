# Checker contract

The checker maps a parsed book to a resolved core term or to one classified
failure, and the pinned seed decides each verdict: Invalid where the seed
rejects, Unsupported where Knot cannot check a form (never Invalid, never passed
through unchecked), Exhausted at a resource bound.

A datatype match is a flat match or a binary matrix of single-constructor
decisions; a match on an installed primitive, or with a literal arm, takes the
literal matrix. A body that is not a match closes the match frontier and judges
its `+` kinds. Literals, Nat offsets and refined lets check against a known
type. Checking is affine: a live occurrence is consumed once.

Frozen expectations: tests/compiler-checker, tests/compiler-fields,
tests/compiler-nest and tests/compiler-literals.
